"""Acquisition boundary: fetch, persist raw first, then normalized rows.

The acquisition functions run inside the caller's transaction: they accept
an already-bound ``CentralDataStore`` and never commit or roll back.
Retries and backoff are bounded; ``retry-after`` is integer-seconds-only
with a hard clamp. ``FailureStatus.PAGINATION_BUDGET_EXHAUSTED`` is an
acquisition-level outcome only and is never bound to a persisted row.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .central_data_contracts import (
    CentralDataRequest,
    FailureStatus,
    SourceDefinition,
)
from .central_data_db_row import NormalizedObservationRow, RawEventRow
from .central_data_persistence_policy import CentralDataPolicyError
from .central_data_registry import DEFAULT_PAGINATION_POLICIES
from .central_data_request_params import (
    PaginationPolicy,
    build_request_query,
    request_query_identity,
)
from .central_data_source_adapters import SOURCE_PARSERS
from .central_data_store import CentralDataInsertResult, CentralDataStore
from .central_data_transport import SafeGETTransport


RETRYABLE_STATUSES = frozenset(
    {
        FailureStatus.TIMEOUT,
        FailureStatus.NETWORK_ERROR,
        FailureStatus.STREAM_ERROR,
    }
)
RETRY_AFTER_CAP_SECONDS = 300
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 1.0

Sleep = Callable[[float], None]


@dataclass(frozen=True)
class AcquisitionOutcome:
    source_id: str
    request_identity: str
    raw_result: CentralDataInsertResult | None
    normalized_rows: tuple[NormalizedObservationRow, ...]
    failure_status: FailureStatus
    reason_codes: tuple[str, ...]
    attempts: int
    retry_after_seconds: int | None
    pages_fetched: int


def _parse_retry_after(value: str | None) -> int | None:
    if type(value) is not str:
        return None
    stripped = value.strip()
    if not stripped.isdigit():
        return None
    return int(stripped)


def _request(source_def: SourceDefinition, query: Mapping[str, str], transport: SafeGETTransport) -> CentralDataRequest:
    return CentralDataRequest(
        source_id=source_def.source_id,
        url=source_def.url_template,
        headers={"accept": source_def.content_type, "user-agent": transport.user_agent},
        query=dict(query),
    )


def acquire_once(
    source_def: SourceDefinition,
    *,
    transport: SafeGETTransport,
    store: CentralDataStore,
    params: Mapping[str, Any] | None = None,
    parser=None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Sleep | None = None,
) -> AcquisitionOutcome:
    if type(source_def) is not SourceDefinition:
        raise ValueError("source_def must be a SourceDefinition")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
        raise ValueError("max_attempts must be between 1 and 3")
    parse = parser or SOURCE_PARSERS.get(source_def.source_id)
    if parse is None:
        raise ValueError("no parser is registered for this source")
    query = build_request_query(source_def, params)
    identity = request_query_identity(source_def.source_id, query)
    request = _request(source_def, query, transport)

    failure: FailureStatus | None = None
    reasons: list[str] = []
    retry_after: int | None = None
    attempts = 0
    raw_row: RawEventRow | None = None
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        failure = None
        try:
            response = transport.fetch(source_def, request)
        except Exception as exc:
            status = getattr(exc, "status", None)
            if isinstance(status, FailureStatus):
                failure = status
            else:
                failure = FailureStatus.UNKNOWN
            if (
                failure in RETRYABLE_STATUSES
                and attempt < max_attempts
                and sleep is not None
            ):
                sleep(DEFAULT_BACKOFF_SECONDS * attempt)
                continue
            reasons.append("transport_error")
            break
        if response.failure_status is not FailureStatus.NONE:
            failure = response.failure_status
            if response.status_code == 429:
                retry_after = _parse_retry_after(response.headers.get("retry-after"))
                if retry_after is None or retry_after > RETRY_AFTER_CAP_SECONDS:
                    reasons.append("rate_limit_exceeded")
                    retry_after = (
                        RETRY_AFTER_CAP_SECONDS if retry_after is not None else None
                    )
                    break
                if attempt < max_attempts and sleep is not None:
                    sleep(float(retry_after))
                    continue
                reasons.append("rate_limit_exceeded")
                break
            reasons.append(f"http_error_{response.status_code}")
            break
        try:
            raw_row = RawEventRow.from_contracts(source_def, response)
        except (CentralDataPolicyError, ValueError):
            failure = FailureStatus.INVALID_REQUEST
            reasons.append("policy_refused")
            break
        break

    if raw_row is None or failure is not None:
        return AcquisitionOutcome(
            source_id=source_def.source_id,
            request_identity=identity,
            raw_result=None,
            normalized_rows=(),
            failure_status=failure or FailureStatus.UNKNOWN,
            reason_codes=tuple(dict.fromkeys(reasons)),
            attempts=attempts,
            retry_after_seconds=retry_after,
            pages_fetched=0,
        )

    raw_result = store.insert_raw_event(raw_row)
    normalized_rows = parse(source_def, raw_row)
    for row in normalized_rows:
        store.insert_normalized_observation(row)
    return AcquisitionOutcome(
        source_id=source_def.source_id,
        request_identity=identity,
        raw_result=raw_result,
        normalized_rows=normalized_rows,
        failure_status=FailureStatus.NONE,
        reason_codes=(),
        attempts=attempts,
        retry_after_seconds=None,
        pages_fetched=1,
    )


def acquire_paginated(
    source_def: SourceDefinition,
    *,
    transport: SafeGETTransport,
    store: CentralDataStore,
    base_params: Mapping[str, Any] | None = None,
    policy: PaginationPolicy | None = None,
    items_per_page: int | None = None,
    parser=None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Sleep | None = None,
) -> AcquisitionOutcome:
    pagination = policy or DEFAULT_PAGINATION_POLICIES.get(source_def.source_id)
    if pagination is None:
        return acquire_once(
            source_def,
            transport=transport,
            store=store,
            params=base_params,
            parser=parser,
            max_attempts=max_attempts,
            sleep=sleep,
        )
    spec_names = {spec.name for spec in source_def.query_params}
    if not {"limit", "offset"} <= spec_names:
        raise ValueError("paginated sources must register limit and offset parameters")
    if items_per_page is None:
        items = pagination.max_items_per_page
    else:
        if type(items_per_page) is not int or not (
            pagination.min_items_per_page
            <= items_per_page
            <= pagination.max_items_per_page
        ):
            raise ValueError("items_per_page is outside the pagination policy")
        items = items_per_page

    accumulated: list[NormalizedObservationRow] = []
    attempts = 0
    retry_after: int | None = None
    last_raw_result: CentralDataInsertResult | None = None
    pages = 0
    exhausted_budget = False
    failure: FailureStatus | None = None
    reasons: list[str] = []
    base = dict(base_params or {})
    query_probe = build_request_query(source_def, base)
    identity = request_query_identity(source_def.source_id, query_probe)

    for page in range(1, pagination.max_pages + 1):
        params = dict(base)
        params["limit"] = items
        params["offset"] = (page - 1) * items
        outcome = acquire_once(
            source_def,
            transport=transport,
            store=store,
            params=params,
            parser=parser,
            max_attempts=max_attempts,
            sleep=sleep,
        )
        attempts += outcome.attempts
        pages += 1
        last_raw_result = outcome.raw_result or last_raw_result
        retry_after = retry_after or outcome.retry_after_seconds
        if outcome.failure_status is not FailureStatus.NONE:
            failure = outcome.failure_status
            reasons.extend(outcome.reason_codes)
            break
        accumulated.extend(outcome.normalized_rows)
        if len(outcome.normalized_rows) < items:
            break
        if page == pagination.max_pages:
            exhausted_budget = True

    return AcquisitionOutcome(
        source_id=source_def.source_id,
        request_identity=identity,
        raw_result=last_raw_result,
        normalized_rows=tuple(accumulated),
        failure_status=(
            FailureStatus.PAGINATION_BUDGET_EXHAUSTED
            if exhausted_budget and failure is None
            else (failure or FailureStatus.NONE)
        ),
        reason_codes=tuple(dict.fromkeys(reasons)) if reasons else (),
        attempts=attempts,
        retry_after_seconds=retry_after,
        pages_fetched=pages,
    )


__all__ = (
    "AcquisitionOutcome",
    "DEFAULT_BACKOFF_SECONDS",
    "DEFAULT_MAX_ATTEMPTS",
    "RETRY_AFTER_CAP_SECONDS",
    "RETRYABLE_STATUSES",
    "acquire_once",
    "acquire_paginated",
)
