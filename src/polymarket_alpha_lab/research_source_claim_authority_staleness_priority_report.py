from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Any


REPORT_NAME = "research_source_claim_authority_staleness_priority_report"
REPORT_VERSION = "research_source_claim_authority_staleness_priority_report.v1"
ALLOWED_STATUSES = ("pass", "watch", "block")

_DECIMAL_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "ALLOWED_STATUSES",
    "REPORT_NAME",
    "REPORT_VERSION",
    "FrozenJsonArray",
    "FrozenJsonObject",
    "ResearchSourceClaimAuthorityStalenessPriorityConfig",
    "ResearchSourceClaimAuthorityStalenessPriorityReport",
    "ResearchSourceClaimAuthorityStalenessPriorityRow",
    "ResearchSourceClaimAuthorityStalenessPrioritySignal",
    "ResearchSourceClaimAuthorityStalenessPriorityStatusCount",
    "build_research_source_claim_authority_staleness_priority_report",
    "research_source_claim_authority_staleness_priority_payload_json",
    "research_source_claim_authority_staleness_priority_public_payload",
    "validate_research_source_claim_authority_staleness_priority_payload",
)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityStalenessPriorityConfig:
    config_version: str = REPORT_VERSION
    watch_source_age_seconds: Decimal = Decimal("86400.000000")
    block_source_age_seconds: Decimal = Decimal("604800.000000")
    watch_authority_score_threshold: Decimal = Decimal("0.600000")
    block_authority_score_threshold: Decimal = Decimal("0.300000")
    watch_claim_priority_score_threshold: Decimal = Decimal("0.800000")
    block_claim_priority_score_threshold: Decimal = Decimal("0.900000")
    block_contradiction_count_threshold: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimAuthorityStalenessPriorityConfig, "config")
        _require_nonempty_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_source_age_seconds",
            _require_decimal(
                "watch_source_age_seconds",
                self.watch_source_age_seconds,
                minimum=_ZERO,
            ),
        )
        object.__setattr__(
            self,
            "block_source_age_seconds",
            _require_decimal(
                "block_source_age_seconds",
                self.block_source_age_seconds,
                minimum=_ZERO,
            ),
        )
        for field_name in (
            "watch_authority_score_threshold",
            "block_authority_score_threshold",
            "watch_claim_priority_score_threshold",
            "block_claim_priority_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name), minimum=_ZERO, maximum=_ONE),
            )
        object.__setattr__(
            self,
            "block_contradiction_count_threshold",
            _require_decimal(
                "block_contradiction_count_threshold",
                self.block_contradiction_count_threshold,
                minimum=_ZERO,
            ),
        )
        if self.block_source_age_seconds <= self.watch_source_age_seconds:
            raise ValueError("block_source_age_seconds must exceed watch_source_age_seconds")
        if self.block_authority_score_threshold >= self.watch_authority_score_threshold:
            raise ValueError(
                "block_authority_score_threshold must be below "
                "watch_authority_score_threshold",
            )
        if self.block_claim_priority_score_threshold < self.watch_claim_priority_score_threshold:
            raise ValueError(
                "block_claim_priority_score_threshold must be at least "
                "watch_claim_priority_score_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityStalenessPrioritySignal:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    source_observed_at: datetime
    authority_score: Decimal
    claim_priority_score: Decimal
    corroborating_source_count: Decimal
    contradiction_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimAuthorityStalenessPrioritySignal, "signal")
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_nonempty_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in ("authority_score", "claim_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name), minimum=_ZERO, maximum=_ONE),
            )
        for field_name in ("corroborating_source_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name), minimum=_ZERO),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityStalenessPriorityRow:
    claim_key: str
    source_observed_at: datetime
    source_age_seconds: Decimal
    authority_score: Decimal
    claim_priority_score: Decimal
    corroborating_source_count: Decimal
    contradiction_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimAuthorityStalenessPriorityRow, "row")
        _require_digest("claim_key", self.claim_key)
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_decimal("source_age_seconds", self.source_age_seconds, minimum=_ZERO),
        )
        for field_name in ("authority_score", "claim_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name), minimum=_ZERO, maximum=_ONE),
            )
        for field_name in ("corroborating_source_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name), minimum=_ZERO),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityStalenessPriorityStatusCount:
    status: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimAuthorityStalenessPriorityStatusCount,
            "status_count",
        )
        _require_status("status", self.status)
        object.__setattr__(self, "count", _require_decimal("count", self.count, minimum=_ZERO))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityStalenessPriorityReport:
    report_name: str
    report_version: str
    as_of: datetime
    status: str
    source_count: Decimal
    rows: tuple[ResearchSourceClaimAuthorityStalenessPriorityRow, ...]
    status_counts: tuple[ResearchSourceClaimAuthorityStalenessPriorityStatusCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimAuthorityStalenessPriorityReport, "report")
        _require_nonempty_string("report_name", self.report_name)
        _require_nonempty_string("report_version", self.report_version)
        object.__setattr__(self, "as_of", _as_utc("as_of", self.as_of))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "source_count",
            _require_decimal("source_count", self.source_count, minimum=_ZERO),
        )
        rows = _normalize_exact_tuple(
            "rows",
            self.rows,
            ResearchSourceClaimAuthorityStalenessPriorityRow,
        )
        status_counts = _normalize_exact_tuple(
            "status_counts",
            self.status_counts,
            ResearchSourceClaimAuthorityStalenessPriorityStatusCount,
        )
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "status_counts", status_counts)
        if self.source_count != _decimal_from_count(len(rows)):
            raise ValueError("source_count must match rows")
        if self.status != _overall_status(rows):
            raise ValueError("status must match rows")
        _require_hard_flags(self)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: Mapping[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def build_research_source_claim_authority_staleness_priority_report(
    signals: Sequence[ResearchSourceClaimAuthorityStalenessPrioritySignal],
    *,
    as_of: datetime,
    config: ResearchSourceClaimAuthorityStalenessPriorityConfig | None = None,
) -> ResearchSourceClaimAuthorityStalenessPriorityReport:
    active_config = config or ResearchSourceClaimAuthorityStalenessPriorityConfig()
    _require_exact_type(
        active_config,
        ResearchSourceClaimAuthorityStalenessPriorityConfig,
        "config",
    )
    as_of_utc = _as_utc("as_of", as_of)
    normalized_signals = _normalize_exact_tuple(
        "signals",
        signals,
        ResearchSourceClaimAuthorityStalenessPrioritySignal,
    )
    rows = tuple(
        sorted(
            (_row_from_signal(signal, as_of=as_of_utc, config=active_config) for signal in normalized_signals),
            key=_row_sort_key,
        ),
    )
    status_counts = tuple(
        ResearchSourceClaimAuthorityStalenessPriorityStatusCount(
            status=status,
            count=_decimal_from_count(sum(Decimal("1") for row in rows if row.status == status)),
        )
        for status in ALLOWED_STATUSES
    )
    return ResearchSourceClaimAuthorityStalenessPriorityReport(
        report_name=REPORT_NAME,
        report_version=REPORT_VERSION,
        as_of=as_of_utc,
        status=_overall_status(rows),
        source_count=_decimal_from_count(len(rows)),
        rows=rows,
        status_counts=status_counts,
    )


def research_source_claim_authority_staleness_priority_public_payload(
    report: ResearchSourceClaimAuthorityStalenessPriorityReport,
) -> FrozenJsonObject:
    _require_exact_type(report, ResearchSourceClaimAuthorityStalenessPriorityReport, "report")
    payload = _report_public_dict(report)
    digest = _digest_json_object(payload)
    payload_with_digest = dict(payload)
    payload_with_digest["validation_digest"] = digest
    return _freeze_json_object(payload_with_digest)


def research_source_claim_authority_staleness_priority_payload_json(
    report: ResearchSourceClaimAuthorityStalenessPriorityReport,
) -> str:
    payload = research_source_claim_authority_staleness_priority_public_payload(report)
    return _canonical_json_dumps(_thaw_json_value(payload))


def validate_research_source_claim_authority_staleness_priority_payload(
    payload: Mapping[str, Any],
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    digest = payload.get("validation_digest")
    if type(digest) is not str:
        return False
    payload_without_digest = {
        key: _thaw_json_value(value)
        for key, value in payload.items()
        if key != "validation_digest"
    }
    return digest == _digest_json_object(payload_without_digest)


def _row_from_signal(
    signal: ResearchSourceClaimAuthorityStalenessPrioritySignal,
    *,
    as_of: datetime,
    config: ResearchSourceClaimAuthorityStalenessPriorityConfig,
) -> ResearchSourceClaimAuthorityStalenessPriorityRow:
    source_age_seconds = _duration_seconds(signal.source_observed_at, as_of)
    status, reason_codes = _classify_signal(
        signal,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return ResearchSourceClaimAuthorityStalenessPriorityRow(
        claim_key=_claim_key(signal),
        source_observed_at=signal.source_observed_at,
        source_age_seconds=source_age_seconds,
        authority_score=signal.authority_score,
        claim_priority_score=signal.claim_priority_score,
        corroborating_source_count=signal.corroborating_source_count,
        contradiction_count=signal.contradiction_count,
        status=status,
        reason_codes=reason_codes,
    )


def _classify_signal(
    signal: ResearchSourceClaimAuthorityStalenessPrioritySignal,
    *,
    source_age_seconds: Decimal,
    config: ResearchSourceClaimAuthorityStalenessPriorityConfig,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    status = "pass"
    if source_age_seconds >= config.block_source_age_seconds:
        status = "block"
        reasons.append("source_age_block")
    elif source_age_seconds >= config.watch_source_age_seconds:
        status = "watch"
        reasons.append("source_age_watch")
    if signal.authority_score <= config.block_authority_score_threshold:
        status = "block"
        reasons.append("authority_score_block")
    elif signal.authority_score <= config.watch_authority_score_threshold and status != "block":
        status = "watch"
        reasons.append("authority_score_watch")
    high_priority = signal.claim_priority_score >= config.block_claim_priority_score_threshold
    degraded_freshness = source_age_seconds >= config.watch_source_age_seconds
    degraded_authority = signal.authority_score <= config.watch_authority_score_threshold
    if high_priority and (degraded_freshness or degraded_authority):
        status = "block"
        reasons.append("high_priority_claim_block")
    elif (
        signal.claim_priority_score >= config.watch_claim_priority_score_threshold
        and status == "pass"
    ):
        status = "watch"
        reasons.append("high_priority_claim_watch")
    if signal.contradiction_count >= config.block_contradiction_count_threshold:
        status = "block"
        reasons.append("contradiction_count_block")
    if not reasons:
        reasons.append("within_thresholds")
    return status, tuple(reasons)


def _report_public_dict(report: ResearchSourceClaimAuthorityStalenessPriorityReport) -> dict[str, Any]:
    return {
        "report_name": report.report_name,
        "report_version": report.report_version,
        "as_of": _datetime_to_json(report.as_of),
        "status": report.status,
        "source_count": _decimal_to_json(report.source_count),
        "hard_flags": _hard_flags_dict(report),
        "status_counts": [
            {
                "status": item.status,
                "count": _decimal_to_json(item.count),
                "hard_flags": _hard_flags_dict(item),
            }
            for item in report.status_counts
        ],
        "rows": [
            {
                "claim_key": row.claim_key,
                "source_observed_at": _datetime_to_json(row.source_observed_at),
                "source_age_seconds": _decimal_to_json(row.source_age_seconds),
                "authority_score": _decimal_to_json(row.authority_score),
                "claim_priority_score": _decimal_to_json(row.claim_priority_score),
                "corroborating_source_count": _decimal_to_json(row.corroborating_source_count),
                "contradiction_count": _decimal_to_json(row.contradiction_count),
                "status": row.status,
                "reason_codes": list(row.reason_codes),
                "hard_flags": _hard_flags_dict(row),
            }
            for row in report.rows
        ],
    }


def _claim_key(signal: ResearchSourceClaimAuthorityStalenessPrioritySignal) -> str:
    digest_input = {
        "candidate_id": signal.candidate_id,
        "market_id": signal.market_id,
        "market_slug": signal.market_slug,
        "market_question": signal.market_question,
        "source_url": signal.source_url,
        "source_text": signal.source_text,
        "source_observed_at": _datetime_to_json(signal.source_observed_at),
    }
    return _digest_json_object(digest_input)


def _digest_json_object(value: Mapping[str, Any]) -> str:
    return "sha256:" + sha256(_canonical_json_dumps(value).encode("utf-8")).hexdigest()


def _canonical_json_dumps(value: Any) -> str:
    _reject_json_numbers(value)
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _reject_json_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise ValueError("JSON payload numerics must be encoded as strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_json_numbers(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_numbers(item)


def _freeze_json_object(value: Mapping[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_json_object(value)
    if isinstance(value, (list, tuple)):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _thaw_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


def _overall_status(rows: tuple[ResearchSourceClaimAuthorityStalenessPriorityRow, ...]) -> str:
    statuses = {row.status for row in rows}
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _row_sort_key(row: ResearchSourceClaimAuthorityStalenessPriorityRow) -> tuple[str, str]:
    return (row.status, row.claim_key)


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    if delta.days < 0:
        raise ValueError("source_observed_at must not be after as_of")
    value = (
        (Decimal(delta.days) * _SECONDS_PER_DAY)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return _require_decimal("source_age_seconds", value, minimum=_ZERO)


def _decimal_from_count(value: int | Decimal) -> Decimal:
    return _require_decimal("count", Decimal(value), minimum=_ZERO)


def _require_exact_type(value: Any, expected_type: type[Any], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_nonempty_string(name: str, value: Any) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_digest(name: str, value: Any) -> str:
    _require_nonempty_string(name, value)
    if not value.startswith("sha256:") or len(value) != len("sha256:") + 64:
        raise ValueError(f"{name} must be a sha256 digest")
    suffix = value[len("sha256:") :]
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_status(name: str, value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_STATUSES:
        raise ValueError(f"{name} must be one of {ALLOWED_STATUSES}")
    return value


def _require_decimal(
    name: str,
    value: Any,
    *,
    minimum: Decimal | None = None,
    maximum: Decimal | None = None,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = value.quantize(_DECIMAL_QUANTUM)
    if minimum is not None and normalized < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and normalized > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return normalized


def _as_utc(name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _normalize_reason_codes(value: Any) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for item in value:
        _require_nonempty_string("reason_code", item)
        if item != item.lower() or not all(
            character.isalnum() or character == "_" for character in item
        ):
            raise ValueError("reason_code must be lower snake case")
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _normalize_exact_tuple(name: str, values: Any, expected_type: type[Any]) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    normalized = tuple(values)
    for value in normalized:
        _require_exact_type(value, expected_type, name)
    return normalized


def _require_hard_flags(value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _hard_flags_dict(value: Any) -> dict[str, bool]:
    _require_hard_flags(value)
    return {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _decimal_to_json(value: Decimal) -> str:
    return format(_require_decimal("decimal", value), "f")


def _datetime_to_json(value: datetime) -> str:
    utc_value = _as_utc("datetime", value)
    return utc_value.isoformat(timespec="microseconds").replace("+00:00", "Z")
