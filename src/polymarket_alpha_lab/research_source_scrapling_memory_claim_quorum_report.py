"""Deterministic report-only Scrapling memory claim quorum research source."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "scrapling-memory-claim-quorum-report-v1"
STATUSES = ("pass", "watch", "block")

PASS_REASON = "claim_quorum_pass"
EMPTY_REASON = "empty_memory_claim_quorum"
INSUFFICIENT_MEMO_REASON = "insufficient_memory_quorum"
INSUFFICIENT_FAMILY_REASON = "insufficient_family_quorum"
LOW_CORROBORATION_REASON = "corroboration_ratio_below_floor"
LOW_CONFIDENCE_REASON = "confidence_below_floor"
CONFLICT_REASON = "memory_conflict_present"
STALE_REASON = "stale_memory_snapshot"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    EMPTY_REASON,
    INSUFFICIENT_MEMO_REASON,
    INSUFFICIENT_FAMILY_REASON,
    LOW_CORROBORATION_REASON,
    LOW_CONFIDENCE_REASON,
    CONFLICT_REASON,
    STALE_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASON_CODES = frozenset(
    (
        EMPTY_REASON,
        INSUFFICIENT_MEMO_REASON,
        INSUFFICIENT_FAMILY_REASON,
        CONFLICT_REASON,
        STALE_REASON,
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "source-text",
    "sourcetext",
    "url",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "database",
    "network",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "trading",
    "execute",
    "execution",
    "sizing",
    "recommendation",
)

PUBLIC_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "claim_count",
        "memo_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_confidence_score",
        "oldest_memory_age_seconds",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    (
        "claim_fingerprint_digest",
        "memo_count",
        "family_count",
        "corroborating_count",
        "conflict_count",
        "corroboration_ratio",
        "conflict_ratio",
        "average_confidence_score",
        "oldest_memory_age_seconds",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class _ValidatedPublicRow:
    claim_fingerprint_digest: str
    memo_count: Decimal
    family_count: Decimal
    corroborating_count: Decimal
    conflict_count: Decimal
    corroboration_ratio: Decimal
    conflict_ratio: Decimal
    average_confidence_score: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ResearchSourceScraplingMemoryClaimQuorumConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_memo_count: Decimal = Decimal("2")
    min_family_count: Decimal = Decimal("2")
    min_corroboration_ratio: Decimal = Decimal("0.750000")
    min_average_confidence_score: Decimal = Decimal("0.600000")
    max_conflict_ratio: Decimal = Decimal("0.000000")
    max_memory_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchSourceScraplingMemoryClaimQuorumConfig is final")

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in ("min_memo_count", "min_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_corroboration_ratio",
            "min_average_confidence_score",
            "max_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _normalize_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingMemoryClaimSnapshot:
    memo_id: str
    claim_id: str
    family_id: str
    observed_at: datetime
    confidence_score: Decimal
    corroborates_claim: bool
    conflict_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchSourceScraplingMemoryClaimSnapshot is final")

    def __post_init__(self) -> None:
        for field_name in ("memo_id", "claim_id", "family_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _normalize_probability("confidence_score", self.confidence_score),
        )
        for field_name in ("corroborates_claim", "conflict_flag"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload("snapshot", self)


@dataclass(frozen=True)
class ResearchSourceScraplingMemoryClaimQuorumRow:
    claim_id: str
    memo_count: Decimal
    family_count: Decimal
    corroborating_count: Decimal
    conflict_count: Decimal
    corroboration_ratio: Decimal
    conflict_ratio: Decimal
    average_confidence_score: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    memo_ids: tuple[str, ...]
    family_ids: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchSourceScraplingMemoryClaimQuorumRow is final")

    def __post_init__(self) -> None:
        _require_public_string("claim_id", self.claim_id)
        for field_name in (
            "memo_count",
            "family_count",
            "corroborating_count",
            "conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroboration_ratio",
            "conflict_ratio",
            "average_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _normalize_nonnegative_decimal(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "memo_ids",
            _normalize_string_tuple("memo_ids", self.memo_ids),
        )
        object.__setattr__(
            self,
            "family_ids",
            _normalize_string_tuple("family_ids", self.family_ids),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingMemoryClaimQuorumReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    memo_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_score: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceScraplingMemoryClaimQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchSourceScraplingMemoryClaimQuorumReport is final")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "memo_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_confidence_score",
            _normalize_probability(
                "average_confidence_score",
                self.average_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _normalize_nonnegative_decimal(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_memory_claim_quorum_public_payload(self)


def build_research_source_scrapling_memory_claim_quorum_report(
    snapshots: Iterable[ResearchSourceScraplingMemoryClaimSnapshot],
    *,
    generated_at: datetime,
    config: ResearchSourceScraplingMemoryClaimQuorumConfig | None = None,
) -> ResearchSourceScraplingMemoryClaimQuorumReport:
    if config is None:
        config = ResearchSourceScraplingMemoryClaimQuorumConfig()
    if type(config) is not ResearchSourceScraplingMemoryClaimQuorumConfig:
        raise ValueError(
            "config must be a ResearchSourceScraplingMemoryClaimQuorumConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(
        snapshots,
        generated_at=generated_at_utc,
    )

    grouped: dict[str, list[ResearchSourceScraplingMemoryClaimSnapshot]] = {}
    for snapshot in normalized_snapshots:
        grouped.setdefault(snapshot.claim_id, []).append(snapshot)

    rows = tuple(
        _row_for_claim(
            claim_id=claim_id,
            snapshots=tuple(grouped[claim_id]),
            config=config,
            generated_at=generated_at_utc,
        )
        for claim_id in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceScraplingMemoryClaimQuorumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_count(len(rows)),
        memo_count=_sum_counts(row.memo_count for row in rows),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        average_confidence_score=_weighted_average_confidence(rows),
        oldest_memory_age_seconds=_max_decimal(
            row.oldest_memory_age_seconds for row in rows
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
    )


def research_source_scrapling_memory_claim_quorum_public_payload(
    value: ResearchSourceScraplingMemoryClaimQuorumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchSourceScraplingMemoryClaimQuorumReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchSourceScraplingMemoryClaimQuorumReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_source_scrapling_memory_claim_quorum_public_payload(payload)
    return dict(payload)


def validate_research_source_scrapling_memory_claim_quorum_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_exact_public_payload_keys(
        "public payload",
        payload,
        PUBLIC_REPORT_PAYLOAD_KEYS,
    )
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")

    _payload_required_datetime(payload, "generated_at")
    _require_public_string(
        "config_version",
        _payload_required_string(payload, "config_version"),
    )
    claim_count = _payload_required_decimal(
        payload,
        "claim_count",
        _normalize_count,
    )
    memo_count = _payload_required_decimal(
        payload,
        "memo_count",
        _normalize_count,
    )
    pass_count = _payload_required_decimal(
        payload,
        "pass_count",
        _normalize_count,
    )
    watch_count = _payload_required_decimal(
        payload,
        "watch_count",
        _normalize_count,
    )
    block_count = _payload_required_decimal(
        payload,
        "block_count",
        _normalize_count,
    )
    average_confidence_score = _payload_required_decimal(
        payload,
        "average_confidence_score",
        _normalize_probability,
    )
    oldest_memory_age_seconds = _payload_required_decimal(
        payload,
        "oldest_memory_age_seconds",
        _normalize_nonnegative_decimal,
    )
    status = _payload_required_string(payload, "status")
    _require_member("status", status, STATUSES)
    reason_codes = _payload_required_reason_codes(payload, "reason_codes")
    rows_value = payload.get("rows")
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(
        _validated_public_row(row, index=index)
        for index, row in enumerate(rows_value)
    )
    claim_fingerprints = tuple(row.claim_fingerprint_digest for row in rows)
    if len(claim_fingerprints) != len(set(claim_fingerprints)):
        raise ValueError("claim_fingerprint_digest values must be unique")
    if claim_fingerprints != tuple(sorted(claim_fingerprints)):
        raise ValueError("rows must be in canonical order")

    if claim_count != _count(len(rows)):
        raise ValueError("claim_count must match rows")
    if memo_count != _sum_counts(row.memo_count for row in rows):
        raise ValueError("memo_count must match rows")
    if pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if average_confidence_score != _weighted_average_confidence(rows):
        raise ValueError("average_confidence_score must match rows")
    if oldest_memory_age_seconds != _max_decimal(
        row.oldest_memory_age_seconds for row in rows
    ):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if status != _report_status(rows):
        raise ValueError("status must match rows")
    if reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    return True


def _validated_public_row(value: object, *, index: int) -> _ValidatedPublicRow:
    label = f"rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    _require_exact_public_payload_keys(label, value, PUBLIC_ROW_PAYLOAD_KEYS)
    _require_public_payload_flags(value)
    claim_fingerprint_digest = _payload_required_string(
        value,
        "claim_fingerprint_digest",
    )
    _require_sha256_digest(
        "claim_fingerprint_digest",
        claim_fingerprint_digest,
    )
    memo_count = _payload_required_decimal(value, "memo_count", _normalize_count)
    family_count = _payload_required_decimal(value, "family_count", _normalize_count)
    corroborating_count = _payload_required_decimal(
        value,
        "corroborating_count",
        _normalize_count,
    )
    conflict_count = _payload_required_decimal(
        value,
        "conflict_count",
        _normalize_count,
    )
    corroboration_ratio = _payload_required_decimal(
        value,
        "corroboration_ratio",
        _normalize_probability,
    )
    conflict_ratio = _payload_required_decimal(
        value,
        "conflict_ratio",
        _normalize_probability,
    )
    average_confidence_score = _payload_required_decimal(
        value,
        "average_confidence_score",
        _normalize_probability,
    )
    oldest_memory_age_seconds = _payload_required_decimal(
        value,
        "oldest_memory_age_seconds",
        _normalize_nonnegative_decimal,
    )
    status = _payload_required_string(value, "status")
    _require_member("status", status, STATUSES)
    reason_codes = _payload_required_reason_codes(value, "reason_codes")

    if EMPTY_REASON in reason_codes:
        raise ValueError(f"{label} empty reason is report-only")
    if memo_count <= ZERO:
        raise ValueError(f"{label} memo_count must be positive")
    if family_count <= ZERO:
        raise ValueError(f"{label} family_count must be positive")
    if family_count > memo_count:
        raise ValueError(f"{label} family_count must not exceed memo_count")
    if corroborating_count > memo_count:
        raise ValueError(f"{label} corroborating_count must not exceed memo_count")
    if conflict_count > memo_count:
        raise ValueError(f"{label} conflict_count must not exceed memo_count")
    if corroboration_ratio != _ratio(corroborating_count, memo_count):
        raise ValueError(f"{label} corroboration_ratio must match counts")
    if conflict_ratio != _ratio(conflict_count, memo_count):
        raise ValueError(f"{label} conflict_ratio must match counts")
    if status != _status_from_reason_codes(reason_codes):
        raise ValueError(f"{label} status must match reason_codes")

    return _ValidatedPublicRow(
        claim_fingerprint_digest=claim_fingerprint_digest,
        memo_count=memo_count,
        family_count=family_count,
        corroborating_count=corroborating_count,
        conflict_count=conflict_count,
        corroboration_ratio=corroboration_ratio,
        conflict_ratio=conflict_ratio,
        average_confidence_score=average_confidence_score,
        oldest_memory_age_seconds=oldest_memory_age_seconds,
        status=status,
        reason_codes=reason_codes,
    )


def _row_for_claim(
    *,
    claim_id: str,
    snapshots: tuple[ResearchSourceScraplingMemoryClaimSnapshot, ...],
    config: ResearchSourceScraplingMemoryClaimQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingMemoryClaimQuorumRow:
    sorted_snapshots = tuple(sorted(snapshots, key=_snapshot_sort_key))
    memo_count = _count(len(sorted_snapshots))
    family_ids = tuple(sorted({snapshot.family_id for snapshot in sorted_snapshots}))
    family_count = _count(len(family_ids))
    corroborating_count = _count(
        sum(1 for snapshot in sorted_snapshots if snapshot.corroborates_claim),
    )
    conflict_count = _count(
        sum(1 for snapshot in sorted_snapshots if snapshot.conflict_flag),
    )
    confidence = _average(
        tuple(snapshot.confidence_score for snapshot in sorted_snapshots),
    )
    oldest_age = _max_decimal(
        _seconds_between(snapshot.observed_at, generated_at)
        for snapshot in sorted_snapshots
    )
    corroboration_ratio = _ratio(corroborating_count, memo_count)
    conflict_ratio = _ratio(conflict_count, memo_count)
    reason_codes = _row_reason_codes(
        memo_count=memo_count,
        family_count=family_count,
        corroboration_ratio=corroboration_ratio,
        conflict_ratio=conflict_ratio,
        average_confidence_score=confidence,
        oldest_memory_age_seconds=oldest_age,
        config=config,
    )
    return ResearchSourceScraplingMemoryClaimQuorumRow(
        claim_id=claim_id,
        memo_count=memo_count,
        family_count=family_count,
        corroborating_count=corroborating_count,
        conflict_count=conflict_count,
        corroboration_ratio=corroboration_ratio,
        conflict_ratio=conflict_ratio,
        average_confidence_score=confidence,
        oldest_memory_age_seconds=oldest_age,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        memo_ids=tuple(snapshot.memo_id for snapshot in sorted_snapshots),
        family_ids=family_ids,
    )


def _row_reason_codes(
    *,
    memo_count: Decimal,
    family_count: Decimal,
    corroboration_ratio: Decimal,
    conflict_ratio: Decimal,
    average_confidence_score: Decimal,
    oldest_memory_age_seconds: Decimal,
    config: ResearchSourceScraplingMemoryClaimQuorumConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if memo_count < config.min_memo_count:
        reasons.append(INSUFFICIENT_MEMO_REASON)
    if family_count < config.min_family_count:
        reasons.append(INSUFFICIENT_FAMILY_REASON)
    if corroboration_ratio < config.min_corroboration_ratio:
        reasons.append(LOW_CORROBORATION_REASON)
    if average_confidence_score < config.min_average_confidence_score:
        reasons.append(LOW_CONFIDENCE_REASON)
    if conflict_ratio > config.max_conflict_ratio:
        reasons.append(CONFLICT_REASON)
    if oldest_memory_age_seconds > config.max_memory_age_seconds:
        reasons.append(STALE_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _normalize_snapshots(
    value: Iterable[ResearchSourceScraplingMemoryClaimSnapshot],
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceScraplingMemoryClaimSnapshot, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        snapshots = tuple(value)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    seen_ids: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not ResearchSourceScraplingMemoryClaimSnapshot:
            raise ValueError(
                "snapshots must contain ResearchSourceScraplingMemoryClaimSnapshot values",
            )
        _require_hard_flags("snapshot", snapshot)
        if snapshot.memo_id in seen_ids:
            raise ValueError("memo_id values must be unique")
        seen_ids.add(snapshot.memo_id)
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(sorted(snapshots, key=_snapshot_sort_key))


def _normalize_rows(
    value: Iterable[ResearchSourceScraplingMemoryClaimQuorumRow],
) -> tuple[ResearchSourceScraplingMemoryClaimQuorumRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_claim_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceScraplingMemoryClaimQuorumRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingMemoryClaimQuorumRow values",
            )
        _require_hard_flags("row", row)
        if row.claim_id in seen_claim_ids:
            raise ValueError("row claim_id values must be unique")
        seen_claim_ids.add(row.claim_id)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _validate_row(row: ResearchSourceScraplingMemoryClaimQuorumRow) -> None:
    if row.memo_count <= ZERO:
        raise ValueError("memo_count must be positive")
    if row.family_count <= ZERO:
        raise ValueError("family_count must be positive")
    if row.family_count > row.memo_count:
        raise ValueError("family_count must not exceed memo_count")
    if row.corroborating_count > row.memo_count:
        raise ValueError("corroborating_count must not exceed memo_count")
    if row.conflict_count > row.memo_count:
        raise ValueError("conflict_count must not exceed memo_count")
    if row.corroboration_ratio != _ratio(row.corroborating_count, row.memo_count):
        raise ValueError("corroboration_ratio must match counts")
    if row.conflict_ratio != _ratio(row.conflict_count, row.memo_count):
        raise ValueError("conflict_ratio must match counts")
    if EMPTY_REASON in row.reason_codes:
        raise ValueError("empty reason is report-only")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if len(row.memo_ids) != int(row.memo_count):
        raise ValueError("memo_ids must match memo_count")
    if len(row.family_ids) != int(row.family_count):
        raise ValueError("family_ids must match family_count")


def _validate_report(report: ResearchSourceScraplingMemoryClaimQuorumReport) -> None:
    rows = report.rows
    if report.claim_count != _count(len(rows)):
        raise ValueError("claim_count must match rows")
    if report.memo_count != _sum_counts(row.memo_count for row in rows):
        raise ValueError("memo_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.average_confidence_score != _weighted_average_confidence(rows):
        raise ValueError("average_confidence_score must match rows")
    if report.oldest_memory_age_seconds != _max_decimal(
        row.oldest_memory_age_seconds for row in rows
    ):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _set_or_validate_derived_validation_digest(
    report: ResearchSourceScraplingMemoryClaimQuorumReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchSourceScraplingMemoryClaimQuorumReport,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is ResearchSourceScraplingMemoryClaimQuorumReport:
        return {
            "generated_at": _payload_value(value.generated_at),
            "config_version": value.config_version,
            "claim_count": _payload_value(value.claim_count),
            "memo_count": _payload_value(value.memo_count),
            "pass_count": _payload_value(value.pass_count),
            "watch_count": _payload_value(value.watch_count),
            "block_count": _payload_value(value.block_count),
            "average_confidence_score": _payload_value(value.average_confidence_score),
            "oldest_memory_age_seconds": _payload_value(
                value.oldest_memory_age_seconds,
            ),
            "status": value.status,
            "reason_codes": _payload_value(value.reason_codes),
            "rows": sorted(
                _payload_value(value.rows),
                key=lambda row: row["claim_fingerprint_digest"],
            ),
            "derived_validation_digest": value.derived_validation_digest,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchSourceScraplingMemoryClaimQuorumRow:
        return {
            "claim_fingerprint_digest": _stable_public_digest(value.claim_id),
            "memo_count": _payload_value(value.memo_count),
            "family_count": _payload_value(value.family_count),
            "corroborating_count": _payload_value(value.corroborating_count),
            "conflict_count": _payload_value(value.conflict_count),
            "corroboration_ratio": _payload_value(value.corroboration_ratio),
            "conflict_ratio": _payload_value(value.conflict_ratio),
            "average_confidence_score": _payload_value(
                value.average_confidence_score,
            ),
            "oldest_memory_age_seconds": _payload_value(
                value.oldest_memory_age_seconds,
            ),
            "status": value.status,
            "reason_codes": _payload_value(value.reason_codes),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if value is None or type(value) is bool or type(value) is str:
        return value
    raise ValueError("payload value is not public JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is tuple or type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} must use Decimal values")
    raise ValueError(f"{current_path} is not a supported public payload value")


def _stable_public_digest(value: str) -> str:
    _require_public_string("public_fingerprint_value", value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {path}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_required_datetime(
    payload: dict[str, Any],
    field_name: str,
) -> datetime:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _payload_required_decimal(
    payload: dict[str, Any],
    field_name: str,
    normalizer: Callable[[str, object], Decimal],
) -> Decimal:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = Decimal(value)
        normalized = normalizer(field_name, parsed)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_required_reason_codes(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(value)
    normalized = _normalize_reason_codes(field_name, reason_codes)
    if normalized != reason_codes:
        raise ValueError(f"{field_name} must be in canonical order")
    return normalized


def _require_exact_public_payload_keys(
    label: str,
    value: object,
    expected_keys: frozenset[str],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} keys must match expected public schema")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "memory_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_counts(values: Iterable[Decimal]) -> Decimal:
    return sum(values, Decimal("0")).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("ratio", numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("average", sum(values, ZERO) / Decimal(len(values)))


def _weighted_average_confidence(
    rows: tuple[
        ResearchSourceScraplingMemoryClaimQuorumRow | _ValidatedPublicRow,
        ...,
    ],
) -> Decimal:
    memo_count = _sum_counts(row.memo_count for row in rows)
    if memo_count <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        weighted_total = sum(
            (row.average_confidence_score * row.memo_count for row in rows),
            ZERO,
        )
        return _normalize_probability("average_confidence_score", weighted_total / memo_count)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if EMPTY_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} empty reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for item in items:
        _require_public_string(field_name, item)
    sorted_items = tuple(sorted(items))
    if items != sorted_items:
        raise ValueError(f"{field_name} must be sorted deterministically")
    if len(items) != len(set(items)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _report_reason_codes(
    rows: tuple[
        ResearchSourceScraplingMemoryClaimQuorumRow | _ValidatedPublicRow,
        ...,
    ],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    active_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != PASS_REASON and reason_code not in active_codes:
                active_codes.append(reason_code)
    if not active_codes:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(active_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _report_status(
    rows: tuple[
        ResearchSourceScraplingMemoryClaimQuorumRow | _ValidatedPublicRow,
        ...,
    ],
) -> str:
    if not rows:
        return "block"
    statuses = {row.status for row in rows}
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_string(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _snapshot_sort_key(
    snapshot: ResearchSourceScraplingMemoryClaimSnapshot,
) -> tuple[str, str, str]:
    return (snapshot.claim_id, snapshot.family_id, snapshot.memo_id)


def _row_sort_key(row: ResearchSourceScraplingMemoryClaimQuorumRow) -> str:
    return row.claim_id


__all__ = (
    "ResearchSourceScraplingMemoryClaimQuorumConfig",
    "ResearchSourceScraplingMemoryClaimQuorumReport",
    "ResearchSourceScraplingMemoryClaimQuorumRow",
    "ResearchSourceScraplingMemoryClaimSnapshot",
    "build_research_source_scrapling_memory_claim_quorum_report",
    "research_source_scrapling_memory_claim_quorum_public_payload",
    "validate_research_source_scrapling_memory_claim_quorum_public_payload",
)
