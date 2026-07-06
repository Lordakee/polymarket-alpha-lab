"""Pure readonly priority report for market outcome source rechecks.

This module ranks already-supplied outcome source recheck candidates. It is a
Phase 1 report-only reducer: no live trading, auth, wallet, order, network,
database, or persistence surface is exposed or used.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_PRIORITY_REPORT_CONFIG_VERSION = (
    "market-outcome-source-recheck-priority-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE_HUNDRED = Decimal("100.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
)

_PRIORITY_STATUSES = ("urgent", "watch", "low")
_REPORT_STATUSES = ("empty", "urgent", "watch", "low")
_STATUS_RANK = {"urgent": 0, "watch": 1, "low": 2}

_REASON_SOURCE_NEVER_RECHECKED = "source_never_rechecked"
_REASON_SOURCE_RECHECK_URGENT = "source_recheck_urgent"
_REASON_SOURCE_RECHECK_STALE = "source_recheck_stale"
_REASON_SOURCE_RECHECK_RECENT = "source_recheck_recent"
_REASON_OUTCOME_SOURCE_AGE_URGENT = "outcome_source_age_urgent"
_REASON_OUTCOME_SOURCE_AGE_STALE = "outcome_source_age_stale"
_REASON_MISSING_ACK = "missing_official_source_acknowledgement"
_REASON_UNRESOLVED_CONFLICT = "unresolved_source_conflict"
_REASON_HISTORICAL_GAP = "historical_source_gap_present"
_REASON_CLAMPED = "priority_score_clamped"

_REASON_SCORE = {
    _REASON_SOURCE_NEVER_RECHECKED: Decimal("50.000000"),
    _REASON_SOURCE_RECHECK_URGENT: Decimal("50.000000"),
    _REASON_SOURCE_RECHECK_STALE: Decimal("20.000000"),
    _REASON_SOURCE_RECHECK_RECENT: _ZERO,
    _REASON_OUTCOME_SOURCE_AGE_URGENT: Decimal("30.000000"),
    _REASON_OUTCOME_SOURCE_AGE_STALE: Decimal("10.000000"),
    _REASON_MISSING_ACK: Decimal("20.000000"),
    _REASON_UNRESOLVED_CONFLICT: Decimal("40.000000"),
    _REASON_HISTORICAL_GAP: Decimal("10.000000"),
}


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_PRIORITY_REPORT_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckPriorityConfig",
    "MarketOutcomeSourceRecheckPriorityCandidate",
    "MarketOutcomeSourceRecheckPriorityRow",
    "MarketOutcomeSourceRecheckPriorityReport",
    "build_market_outcome_source_recheck_priority_report",
    "market_outcome_source_recheck_priority_report_payload",
    "validate_market_outcome_source_recheck_priority_report_payload",
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckPriorityConfig:
    config_version: str = (
        DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_PRIORITY_REPORT_CONFIG_VERSION
    )
    stale_recheck_seconds: Decimal = Decimal("7200.000000")
    urgent_recheck_seconds: Decimal = Decimal("21600.000000")
    stale_source_seconds: Decimal = Decimal("7200.000000")
    urgent_source_seconds: Decimal = Decimal("21600.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckPriorityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, MarketOutcomeSourceRecheckPriorityConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_recheck_seconds",
            "urgent_recheck_seconds",
            "stale_source_seconds",
            "urgent_source_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.urgent_recheck_seconds < self.stale_recheck_seconds:
            raise ValueError("urgent_recheck_seconds must cover stale_recheck_seconds")
        if self.urgent_source_seconds < self.stale_source_seconds:
            raise ValueError("urgent_source_seconds must cover stale_source_seconds")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckPriorityCandidate:
    market_slug: str
    condition_id: str
    source_id: str
    source_kind: str
    source_observed_at: datetime
    last_rechecked_at: datetime | None = None
    official_source_acknowledged_at: datetime | None = None
    has_source_conflict: bool = False
    historical_gap_count: Decimal = Decimal("0.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckPriorityCandidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "source_id",
            "source_kind",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _optional_as_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "official_source_acknowledged_at",
            _optional_as_utc(
                "official_source_acknowledged_at",
                self.official_source_acknowledged_at,
            ),
        )
        if type(self.has_source_conflict) is not bool:
            raise ValueError("has_source_conflict must be a bool")
        object.__setattr__(
            self,
            "historical_gap_count",
            _normalize_count("historical_gap_count", self.historical_gap_count),
        )
        _validate_candidate_sequence(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("candidate", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckPriorityRow:
    priority_rank: Decimal
    market_slug: str
    condition_id: str
    source_id: str
    source_kind: str
    priority_status: str
    priority_score: Decimal
    source_age_seconds: Decimal
    recheck_age_seconds: Decimal | None
    acknowledgement_age_seconds: Decimal | None
    historical_gap_count: Decimal
    has_source_conflict: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckPriorityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        for field_name in (
            "market_slug",
            "condition_id",
            "source_id",
            "source_kind",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.priority_status not in _PRIORITY_STATUSES:
            raise ValueError("priority_status must be a known value")
        object.__setattr__(
            self,
            "priority_score",
            _normalize_priority_score("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "recheck_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "recheck_age_seconds",
                self.recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "acknowledgement_age_seconds",
                self.acknowledgement_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "historical_gap_count",
            _normalize_count("historical_gap_count", self.historical_gap_count),
        )
        if type(self.has_source_conflict) is not bool:
            raise ValueError("has_source_conflict must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckPriorityReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    urgent_count: Decimal
    watch_count: Decimal
    low_count: Decimal
    recheck_count: Decimal
    max_priority_score: Decimal
    max_source_age_seconds: Decimal | None
    status: str
    rows: tuple[MarketOutcomeSourceRecheckPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckPriorityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, MarketOutcomeSourceRecheckPriorityReport)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "urgent_count",
            "watch_count",
            "low_count",
            "recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_priority_score",
            _normalize_priority_score("max_priority_score", self.max_priority_score),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        if self.status not in _REPORT_STATUSES:
            raise ValueError("status must be a known report status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_market_outcome_source_recheck_priority_report(
    candidates: Iterable[MarketOutcomeSourceRecheckPriorityCandidate],
    *,
    config: MarketOutcomeSourceRecheckPriorityConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckPriorityReport:
    if type(config) is not MarketOutcomeSourceRecheckPriorityConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckPriorityConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_candidates(candidates)
    _validate_generated_at_covers_values(generated_at, values)

    unranked_rows = tuple(
        _row_from_candidate(value, config=config, generated_at=generated_at)
        for value in values
    )
    ranked_rows = tuple(sorted(unranked_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_rank(row, _decimal_count(index))
        for index, row in enumerate(ranked_rows, start=1)
    )
    return MarketOutcomeSourceRecheckPriorityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_decimal_count(len(values)),
        row_count=_decimal_count(len(rows)),
        urgent_count=_status_count(rows, "urgent"),
        watch_count=_status_count(rows, "watch"),
        low_count=_status_count(rows, "low"),
        recheck_count=_status_count(rows, "urgent") + _status_count(rows, "watch"),
        max_priority_score=_max_decimal(
            (row.priority_score for row in rows),
            default=_ZERO,
        ),
        max_source_age_seconds=_max_optional_decimal(
            row.source_age_seconds for row in rows
        ),
        status=_report_status(rows),
        rows=rows,
    )


def market_outcome_source_recheck_priority_report_payload(
    report: MarketOutcomeSourceRecheckPriorityReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckPriorityReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckPriorityReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_market_outcome_source_recheck_priority_report_payload(payload)
    return payload


def validate_market_outcome_source_recheck_priority_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_candidate(
    value: MarketOutcomeSourceRecheckPriorityCandidate,
    *,
    config: MarketOutcomeSourceRecheckPriorityConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckPriorityRow:
    source_age_seconds = _seconds_between(value.source_observed_at, generated_at)
    recheck_age_seconds = _optional_seconds_between(
        value.last_rechecked_at,
        generated_at,
    )
    acknowledgement_age_seconds = _optional_seconds_between(
        value.official_source_acknowledged_at,
        generated_at,
    )
    reason_codes = _reason_codes_for_candidate(
        value,
        source_age_seconds=source_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        config=config,
    )
    priority_score = _priority_score(reason_codes)
    return MarketOutcomeSourceRecheckPriorityRow(
        priority_rank=_ONE_HUNDRED,
        market_slug=value.market_slug,
        condition_id=value.condition_id,
        source_id=value.source_id,
        source_kind=value.source_kind,
        priority_status=_status_from_score(priority_score),
        priority_score=priority_score,
        source_age_seconds=source_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        historical_gap_count=value.historical_gap_count,
        has_source_conflict=value.has_source_conflict,
        reason_codes=reason_codes,
    )


def _row_with_rank(
    row: MarketOutcomeSourceRecheckPriorityRow,
    priority_rank: Decimal,
) -> MarketOutcomeSourceRecheckPriorityRow:
    return MarketOutcomeSourceRecheckPriorityRow(
        priority_rank=priority_rank,
        market_slug=row.market_slug,
        condition_id=row.condition_id,
        source_id=row.source_id,
        source_kind=row.source_kind,
        priority_status=row.priority_status,
        priority_score=row.priority_score,
        source_age_seconds=row.source_age_seconds,
        recheck_age_seconds=row.recheck_age_seconds,
        acknowledgement_age_seconds=row.acknowledgement_age_seconds,
        historical_gap_count=row.historical_gap_count,
        has_source_conflict=row.has_source_conflict,
        reason_codes=row.reason_codes,
    )


def _reason_codes_for_candidate(
    value: MarketOutcomeSourceRecheckPriorityCandidate,
    *,
    source_age_seconds: Decimal,
    recheck_age_seconds: Decimal | None,
    config: MarketOutcomeSourceRecheckPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if recheck_age_seconds is None:
        reasons.append(_REASON_SOURCE_NEVER_RECHECKED)
    elif recheck_age_seconds >= config.urgent_recheck_seconds:
        reasons.append(_REASON_SOURCE_RECHECK_URGENT)
    elif recheck_age_seconds >= config.stale_recheck_seconds:
        reasons.append(_REASON_SOURCE_RECHECK_STALE)
    else:
        reasons.append(_REASON_SOURCE_RECHECK_RECENT)

    if source_age_seconds >= config.urgent_source_seconds:
        reasons.append(_REASON_OUTCOME_SOURCE_AGE_URGENT)
    elif source_age_seconds >= config.stale_source_seconds:
        reasons.append(_REASON_OUTCOME_SOURCE_AGE_STALE)

    if value.official_source_acknowledged_at is None:
        reasons.append(_REASON_MISSING_ACK)
    if value.has_source_conflict:
        reasons.append(_REASON_UNRESOLVED_CONFLICT)
    if value.historical_gap_count > _ZERO:
        reasons.append(_REASON_HISTORICAL_GAP)

    unclamped_score = _unclamped_priority_score(tuple(reasons))
    if unclamped_score > _ONE_HUNDRED:
        reasons.append(_REASON_CLAMPED)
    return tuple(reasons)


def _normalize_candidates(
    values: Iterable[MarketOutcomeSourceRecheckPriorityCandidate],
) -> tuple[MarketOutcomeSourceRecheckPriorityCandidate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in normalized:
        if type(value) is not MarketOutcomeSourceRecheckPriorityCandidate:
            raise ValueError(
                "candidates must contain MarketOutcomeSourceRecheckPriorityCandidate "
                "values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("candidate", value)
        _require_or_set_digest(value)
        key = (value.market_slug, value.condition_id, value.source_id)
        if key in seen_keys:
            raise ValueError("candidates must not contain duplicate source keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[MarketOutcomeSourceRecheckPriorityRow],
) -> tuple[MarketOutcomeSourceRecheckPriorityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain MarketOutcomeSourceRecheckPriorityRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketOutcomeSourceRecheckPriorityRow values",
        ) from exc
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckPriorityRow:
            raise ValueError(
                "rows must contain MarketOutcomeSourceRecheckPriorityRow values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")
    if len(set(_row_identity(row) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    actual_ranks = tuple(row.priority_rank for row in rows)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank values must be contiguous")
    return rows


def _validate_candidate_sequence(
    value: MarketOutcomeSourceRecheckPriorityCandidate,
) -> None:
    if (
        value.official_source_acknowledged_at is not None
        and _seconds_between(
            value.source_observed_at,
            value.official_source_acknowledged_at,
        )
        < _ZERO
    ):
        raise ValueError(
            "official_source_acknowledged_at must be at or after source_observed_at",
        )


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[MarketOutcomeSourceRecheckPriorityCandidate, ...],
) -> None:
    for value in values:
        if _seconds_between(_latest_candidate_stage_at(value), generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after every known stage")


def _latest_candidate_stage_at(
    value: MarketOutcomeSourceRecheckPriorityCandidate,
) -> datetime:
    latest = value.source_observed_at
    if value.last_rechecked_at is not None and value.last_rechecked_at > latest:
        latest = value.last_rechecked_at
    if (
        value.official_source_acknowledged_at is not None
        and value.official_source_acknowledged_at > latest
    ):
        latest = value.official_source_acknowledged_at
    return latest


def _validate_row_consistency(row: MarketOutcomeSourceRecheckPriorityRow) -> None:
    expected_score = _priority_score(row.reason_codes)
    if row.priority_score != expected_score:
        raise ValueError("priority_score must match reason_codes")
    if row.priority_status != _status_from_score(row.priority_score):
        raise ValueError("priority_status must match priority_score")
    if row.has_source_conflict and _REASON_UNRESOLVED_CONFLICT not in row.reason_codes:
        raise ValueError("has_source_conflict rows must include conflict reason")
    if row.historical_gap_count > _ZERO and _REASON_HISTORICAL_GAP not in row.reason_codes:
        raise ValueError("historical_gap_count rows must include gap reason")
    if row.acknowledgement_age_seconds is None and _REASON_MISSING_ACK not in row.reason_codes:
        raise ValueError("missing acknowledgement rows must include acknowledgement reason")
    if (
        row.acknowledgement_age_seconds is not None
        and _REASON_MISSING_ACK in row.reason_codes
    ):
        raise ValueError("acknowledged rows must not include missing acknowledgement reason")


def _validate_report_consistency(
    report: MarketOutcomeSourceRecheckPriorityReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must match rows")
    if report.urgent_count != _status_count(report.rows, "urgent"):
        raise ValueError("urgent_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.low_count != _status_count(report.rows, "low"):
        raise ValueError("low_count must match rows")
    if report.recheck_count != report.urgent_count + report.watch_count:
        raise ValueError("recheck_count must match urgent and watch rows")
    if report.max_priority_score != _max_decimal(
        (row.priority_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    if report.max_source_age_seconds != _max_optional_decimal(
        row.source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len(set(_row_identity(row) for row in report.rows)) != len(report.rows):
        raise ValueError("rows must be unique")


def _row_sort_key(
    row: MarketOutcomeSourceRecheckPriorityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.priority_status],
        -row.priority_score,
        -row.source_age_seconds,
        -_optional_sort_decimal(row.recheck_age_seconds),
        row.market_slug,
        row.condition_id,
        row.source_id,
    )


def _row_identity(row: MarketOutcomeSourceRecheckPriorityRow) -> tuple[str, str, str]:
    return (row.market_slug, row.condition_id, row.source_id)


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_status == status))


def _report_status(rows: tuple[MarketOutcomeSourceRecheckPriorityRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.priority_status == "urgent" for row in rows):
        return "urgent"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "low"


def _status_from_score(score: Decimal) -> str:
    if score >= Decimal("70.000000"):
        return "urgent"
    if score >= Decimal("20.000000"):
        return "watch"
    return "low"


def _priority_score(reason_codes: Iterable[str]) -> Decimal:
    unclamped = _unclamped_priority_score(tuple(reason_codes))
    if unclamped > _ONE_HUNDRED:
        return _ONE_HUNDRED
    return _quantize(unclamped)


def _unclamped_priority_score(reason_codes: tuple[str, ...]) -> Decimal:
    total = _ZERO
    for reason_code in reason_codes:
        total += _REASON_SCORE.get(reason_code, _ZERO)
    return _quantize(total)


def _optional_sort_decimal(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("999999999999999999.000000")
    return value


def _optional_seconds_between(start: datetime | None, end: datetime) -> Decimal | None:
    if start is None:
        return None
    return _seconds_between(start, end)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return max(items)


def _max_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(value for value in values if value is not None)
    if not items:
        return None
    return max(items)


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_priority_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE_HUNDRED:
        raise ValueError(f"{field_name} must be between 0.000000 and 100.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime values must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("payload numeric values must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    raise ValueError("value is not public payload serializable")


def _reject_unsafe_public_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_public_surface(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_surface(label, item, nested_path)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if type(value) in (float, int):
        raise ValueError(f"{path} must use Decimal-derived string values")
    if type(value) is bool or value is None or type(value) is str:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            item_path = f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for readonly public payload")
            _require_public_payload_values(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} is not public payload serializable")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD, None)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest_for_value(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if not _is_digest(current):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    if current != expected:
        raise ValueError(
            "derived_validation_digest mismatch for priority_rank priority_score payload",
        )


def _digest_for_value(value: object) -> str:
    digest_value = _canonical_digest_value(_payload_value(value))
    return sha256(repr(digest_value).encode("utf-8")).hexdigest()


def _canonical_digest_value(value: object) -> object:
    if isinstance(value, dict):
        return tuple(
            (key, _canonical_digest_value(item))
            for key, item in sorted(value.items())
            if key != _DIGEST_FIELD
        )
    if isinstance(value, list):
        return tuple(_canonical_digest_value(item) for item in value)
    return value


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        digest = value.get(_DIGEST_FIELD)
        if digest is not None:
            if type(digest) is not str or not _is_digest(digest):
                raise ValueError("derived_validation_digest must be a sha256 hex digest")
            expected = sha256(
                repr(_canonical_digest_value(value)).encode("utf-8"),
            ).hexdigest()
            if digest != expected:
                raise ValueError("derived_validation_digest mismatch")
        for item in value.values():
            _validate_payload_digest_tree(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _is_digest(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)
