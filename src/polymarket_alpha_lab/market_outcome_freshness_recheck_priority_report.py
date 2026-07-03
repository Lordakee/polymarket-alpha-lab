"""Pure in-memory market outcome freshness recheck priority report.

This Phase 1 reducer ranks already-supplied market freshness candidates for
read-only outcome rechecks. It performs no IO, network access, auth, wallet
access, broker access, order submission, cancellation, signing, or advice.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from numbers import Number
from typing import Any


__all__ = (
    "MarketOutcomeFreshnessRecheckCandidate",
    "MarketOutcomeFreshnessRecheckPriorityConfig",
    "MarketOutcomeFreshnessRecheckPriorityReport",
    "MarketOutcomeFreshnessRecheckPriorityRow",
    "build_market_outcome_freshness_recheck_priority_report",
    "market_outcome_freshness_recheck_priority_report_to_json",
)


ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
CHECKED_SORT_WEIGHT = Decimal("1")
NEVER_CHECKED_SORT_WEIGHT = Decimal("0")

ROW_STATUSES = ("fresh", "watch", "urgent")
REPORT_STATUSES = ("empty", "fresh", "watch", "urgent")
ROW_STATUS_SORT_WEIGHT = {
    "urgent": Decimal("0"),
    "watch": Decimal("1"),
    "fresh": Decimal("2"),
}
REASON_CODE_ORDER = (
    "outcome_never_checked",
    "outcome_freshness_urgent",
    "outcome_freshness_stale",
    "outcome_freshness_fresh",
    "unresolved_outcome_gap",
    "market_close_time_passed",
    "market_close_time_soon",
)
URGENT_REASON_CODES = frozenset(
    (
        "outcome_never_checked",
        "outcome_freshness_urgent",
        "market_close_time_passed",
    ),
)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckPriorityConfig:
    config_version: str
    stale_after_seconds: Decimal
    urgent_after_seconds: Decimal
    close_pressure_window_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("stale_after_seconds", self.stale_after_seconds)
        _require_nonnegative_decimal("urgent_after_seconds", self.urgent_after_seconds)
        _require_nonnegative_decimal(
            "close_pressure_window_seconds",
            self.close_pressure_window_seconds,
        )
        if self.urgent_after_seconds < self.stale_after_seconds:
            raise ValueError("urgent_after_seconds must be at least stale_after_seconds")
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckCandidate:
    market_slug: str
    condition_id: str
    question: str
    expected_outcome_count: Decimal
    resolved_outcome_count: Decimal
    last_outcome_checked_at: datetime | None
    market_close_time: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("question", self.question)
        _require_positive_whole_decimal(
            "expected_outcome_count",
            self.expected_outcome_count,
        )
        _require_nonnegative_whole_decimal(
            "resolved_outcome_count",
            self.resolved_outcome_count,
        )
        if self.resolved_outcome_count > self.expected_outcome_count:
            raise ValueError(
                "resolved_outcome_count must not exceed expected_outcome_count",
            )
        object.__setattr__(
            self,
            "last_outcome_checked_at",
            _require_optional_utc_datetime(
                "last_outcome_checked_at",
                self.last_outcome_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "market_close_time",
            _require_optional_utc_datetime(
                "market_close_time",
                self.market_close_time,
            ),
        )
        _validate_hard_flags("candidate", self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckPriorityRow:
    priority_rank: Decimal
    market_slug: str
    condition_id: str
    question: str
    priority_status: str
    expected_outcome_count: Decimal
    resolved_outcome_count: Decimal
    unresolved_outcome_gap: Decimal
    last_outcome_checked_at: datetime | None
    market_close_time: datetime | None
    outcome_freshness_age_seconds: Decimal | None
    staleness_priority_seconds: Decimal
    close_time_delta_seconds: Decimal | None
    close_time_pressure_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_whole_decimal("priority_rank", self.priority_rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("question", self.question)
        if self.priority_status not in ROW_STATUSES:
            raise ValueError("priority_status must be a known row status")
        _require_positive_whole_decimal(
            "expected_outcome_count",
            self.expected_outcome_count,
        )
        _require_nonnegative_whole_decimal(
            "resolved_outcome_count",
            self.resolved_outcome_count,
        )
        if self.resolved_outcome_count > self.expected_outcome_count:
            raise ValueError(
                "resolved_outcome_count must not exceed expected_outcome_count",
            )
        _require_nonnegative_whole_decimal(
            "unresolved_outcome_gap",
            self.unresolved_outcome_gap,
        )
        if (
            self.unresolved_outcome_gap
            != self.expected_outcome_count - self.resolved_outcome_count
        ):
            raise ValueError(
                "unresolved_outcome_gap must equal expected minus resolved outcomes",
            )
        object.__setattr__(
            self,
            "last_outcome_checked_at",
            _require_optional_utc_datetime(
                "last_outcome_checked_at",
                self.last_outcome_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "market_close_time",
            _require_optional_utc_datetime(
                "market_close_time",
                self.market_close_time,
            ),
        )
        _require_optional_nonnegative_decimal(
            "outcome_freshness_age_seconds",
            self.outcome_freshness_age_seconds,
        )
        _require_nonnegative_decimal(
            "staleness_priority_seconds",
            self.staleness_priority_seconds,
        )
        _require_optional_decimal(
            "close_time_delta_seconds",
            self.close_time_delta_seconds,
        )
        _require_nonnegative_decimal(
            "close_time_pressure_seconds",
            self.close_time_pressure_seconds,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_status_matches_reason_codes(self)
        _validate_hard_flags("row", self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckPriorityReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    fresh_count: Decimal
    watch_count: Decimal
    urgent_count: Decimal
    recheck_count: Decimal
    total_unresolved_outcome_gap: Decimal
    max_outcome_freshness_age_seconds: Decimal | None
    min_close_time_delta_seconds: Decimal | None
    status: str
    rows: tuple[MarketOutcomeFreshnessRecheckPriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _require_utc_datetime("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "fresh_count",
            "watch_count",
            "urgent_count",
            "recheck_count",
        ):
            _require_nonnegative_whole_decimal(field_name, getattr(self, field_name))
        _require_nonnegative_whole_decimal(
            "total_unresolved_outcome_gap",
            self.total_unresolved_outcome_gap,
        )
        _require_optional_nonnegative_decimal(
            "max_outcome_freshness_age_seconds",
            self.max_outcome_freshness_age_seconds,
        )
        _require_optional_decimal(
            "min_close_time_delta_seconds",
            self.min_close_time_delta_seconds,
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known report status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _validate_hard_flags("report", self)


def build_market_outcome_freshness_recheck_priority_report(
    candidates: Iterable[MarketOutcomeFreshnessRecheckCandidate],
    *,
    config: MarketOutcomeFreshnessRecheckPriorityConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckPriorityReport:
    """Rank local market outcome freshness candidates for read-only rechecks."""

    if type(config) is not MarketOutcomeFreshnessRecheckPriorityConfig:
        raise ValueError(
            "config must be a MarketOutcomeFreshnessRecheckPriorityConfig",
        )
    generated_at_utc = _require_utc_datetime("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    row_values = tuple(
        _row_values_for_candidate(
            candidate,
            config=config,
            generated_at=generated_at_utc,
        )
        for candidate in normalized_candidates
    )
    ranked_values = sorted(row_values, key=_priority_sort_key)
    rows = tuple(
        MarketOutcomeFreshnessRecheckPriorityRow(
            priority_rank=Decimal(index),
            **values,
        )
        for index, values in enumerate(ranked_values, start=1)
    )
    return MarketOutcomeFreshnessRecheckPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=Decimal(len(normalized_candidates)),
        row_count=Decimal(len(rows)),
        fresh_count=_row_status_count(rows, "fresh"),
        watch_count=_row_status_count(rows, "watch"),
        urgent_count=_row_status_count(rows, "urgent"),
        recheck_count=_row_status_count(rows, "watch")
        + _row_status_count(rows, "urgent"),
        total_unresolved_outcome_gap=sum(
            (row.unresolved_outcome_gap for row in rows),
            ZERO,
        ),
        max_outcome_freshness_age_seconds=_max_optional_decimal(
            row.outcome_freshness_age_seconds for row in rows
        ),
        min_close_time_delta_seconds=_min_optional_decimal(
            row.close_time_delta_seconds for row in rows
        ),
        status=_report_status(rows),
        rows=rows,
    )


def market_outcome_freshness_recheck_priority_report_to_json(
    report: MarketOutcomeFreshnessRecheckPriorityReport,
) -> dict[str, Any]:
    """Return a JSON-ready payload with Decimal values encoded as strings."""

    if type(report) is not MarketOutcomeFreshnessRecheckPriorityReport:
        raise ValueError(
            "report must be a MarketOutcomeFreshnessRecheckPriorityReport",
        )
    return _json_ready(report)


def _normalize_candidates(
    candidates: Iterable[MarketOutcomeFreshnessRecheckCandidate],
) -> tuple[MarketOutcomeFreshnessRecheckCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of recheck candidates")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of recheck candidates") from exc
    for candidate in items:
        if type(candidate) is not MarketOutcomeFreshnessRecheckCandidate:
            raise ValueError(
                "candidates must contain MarketOutcomeFreshnessRecheckCandidate values",
            )
        _validate_hard_flags("candidate", candidate)
    return items


def _row_values_for_candidate(
    candidate: MarketOutcomeFreshnessRecheckCandidate,
    *,
    config: MarketOutcomeFreshnessRecheckPriorityConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    if (
        candidate.last_outcome_checked_at is not None
        and candidate.last_outcome_checked_at > generated_at
    ):
        raise ValueError("last_outcome_checked_at must not be after generated_at")

    freshness_age = (
        None
        if candidate.last_outcome_checked_at is None
        else _timedelta_seconds(generated_at - candidate.last_outcome_checked_at)
    )
    staleness_priority = (
        config.urgent_after_seconds * TWO
        if freshness_age is None
        else freshness_age
    )
    close_time_delta = (
        None
        if candidate.market_close_time is None
        else _timedelta_seconds(candidate.market_close_time - generated_at)
    )
    close_pressure = _close_time_pressure_seconds(
        close_time_delta,
        config.close_pressure_window_seconds,
    )
    unresolved_gap = (
        candidate.expected_outcome_count - candidate.resolved_outcome_count
    )
    reason_codes = _candidate_reason_codes(
        freshness_age=freshness_age,
        unresolved_gap=unresolved_gap,
        close_time_delta=close_time_delta,
        config=config,
    )
    return {
        "market_slug": candidate.market_slug,
        "condition_id": candidate.condition_id,
        "question": candidate.question,
        "priority_status": _priority_status(reason_codes),
        "expected_outcome_count": candidate.expected_outcome_count,
        "resolved_outcome_count": candidate.resolved_outcome_count,
        "unresolved_outcome_gap": unresolved_gap,
        "last_outcome_checked_at": candidate.last_outcome_checked_at,
        "market_close_time": candidate.market_close_time,
        "outcome_freshness_age_seconds": freshness_age,
        "staleness_priority_seconds": staleness_priority,
        "close_time_delta_seconds": close_time_delta,
        "close_time_pressure_seconds": close_pressure,
        "reason_codes": reason_codes,
    }


def _candidate_reason_codes(
    *,
    freshness_age: Decimal | None,
    unresolved_gap: Decimal,
    close_time_delta: Decimal | None,
    config: MarketOutcomeFreshnessRecheckPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if freshness_age is None:
        reason_codes.append("outcome_never_checked")
    elif freshness_age >= config.urgent_after_seconds:
        reason_codes.append("outcome_freshness_urgent")
    elif freshness_age >= config.stale_after_seconds:
        reason_codes.append("outcome_freshness_stale")

    if unresolved_gap > ZERO:
        reason_codes.append("unresolved_outcome_gap")

    if close_time_delta is not None:
        if close_time_delta <= ZERO:
            reason_codes.append("market_close_time_passed")
        elif close_time_delta <= config.close_pressure_window_seconds:
            reason_codes.append("market_close_time_soon")

    if not reason_codes:
        reason_codes.append("outcome_freshness_fresh")
    return _normalize_reason_codes(tuple(reason_codes))


def _priority_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in URGENT_REASON_CODES for reason_code in reason_codes):
        return "urgent"
    if reason_codes == ("outcome_freshness_fresh",):
        return "fresh"
    return "watch"


def _priority_sort_key(values: dict[str, Any]) -> tuple[Any, ...]:
    return (
        ROW_STATUS_SORT_WEIGHT[values["priority_status"]],
        _never_checked_sort_weight(values["outcome_freshness_age_seconds"]),
        -values["staleness_priority_seconds"],
        -values["unresolved_outcome_gap"],
        -values["close_time_pressure_seconds"],
        values["market_slug"],
        values["condition_id"],
        values["question"],
        _datetime_sort_value(values["last_outcome_checked_at"]),
        _datetime_sort_value(values["market_close_time"]),
    )


def _row_priority_sort_key(
    row: MarketOutcomeFreshnessRecheckPriorityRow,
) -> tuple[Any, ...]:
    return (
        ROW_STATUS_SORT_WEIGHT[row.priority_status],
        _never_checked_sort_weight(row.outcome_freshness_age_seconds),
        -row.staleness_priority_seconds,
        -row.unresolved_outcome_gap,
        -row.close_time_pressure_seconds,
        row.market_slug,
        row.condition_id,
        row.question,
        _datetime_sort_value(row.last_outcome_checked_at),
        _datetime_sort_value(row.market_close_time),
    )


def _never_checked_sort_weight(freshness_age: Decimal | None) -> Decimal:
    if freshness_age is None:
        return NEVER_CHECKED_SORT_WEIGHT
    return CHECKED_SORT_WEIGHT


def _datetime_sort_value(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _close_time_pressure_seconds(
    close_time_delta: Decimal | None,
    close_pressure_window_seconds: Decimal,
) -> Decimal:
    if close_time_delta is None:
        return ZERO
    if close_time_delta <= ZERO:
        return close_pressure_window_seconds + abs(close_time_delta)
    if close_time_delta <= close_pressure_window_seconds:
        return close_pressure_window_seconds - close_time_delta
    return ZERO


def _row_status_count(
    rows: tuple[MarketOutcomeFreshnessRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.priority_status == status))


def _report_status(
    rows: tuple[MarketOutcomeFreshnessRecheckPriorityRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.priority_status == "urgent" for row in rows):
        return "urgent"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "fresh"


def _max_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(value for value in values if value is not None)
    if not items:
        return None
    return max(items)


def _min_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(value for value in values if value is not None)
    if not items:
        return None
    return min(items)


def _normalize_rows(
    rows: Iterable[MarketOutcomeFreshnessRecheckPriorityRow],
) -> tuple[MarketOutcomeFreshnessRecheckPriorityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for index, row in enumerate(items, start=1):
        if type(row) is not MarketOutcomeFreshnessRecheckPriorityRow:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckPriorityRow values",
            )
        if row.priority_rank != Decimal(index):
            raise ValueError("rows must be sorted by contiguous priority_rank")
    return items


def _validate_row_status_matches_reason_codes(
    row: MarketOutcomeFreshnessRecheckPriorityRow,
) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must not be empty")
    if (
        "outcome_freshness_fresh" in row.reason_codes
        and row.reason_codes != ("outcome_freshness_fresh",)
    ):
        raise ValueError("outcome_freshness_fresh must be the only fresh row reason")
    if row.priority_status != _priority_status(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")


def _validate_report_consistency(
    report: MarketOutcomeFreshnessRecheckPriorityReport,
) -> None:
    row_count = Decimal(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must equal rows length")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must equal row_count")
    fresh_count = _row_status_count(report.rows, "fresh")
    watch_count = _row_status_count(report.rows, "watch")
    urgent_count = _row_status_count(report.rows, "urgent")
    if report.fresh_count != fresh_count:
        raise ValueError("fresh_count must equal fresh row count")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must equal watch row count")
    if report.urgent_count != urgent_count:
        raise ValueError("urgent_count must equal urgent row count")
    if report.recheck_count != watch_count + urgent_count:
        raise ValueError("recheck_count must equal watch plus urgent row counts")
    total_gap = sum((row.unresolved_outcome_gap for row in report.rows), ZERO)
    if report.total_unresolved_outcome_gap != total_gap:
        raise ValueError("total_unresolved_outcome_gap must equal summed row gaps")
    if report.max_outcome_freshness_age_seconds != _max_optional_decimal(
        row.outcome_freshness_age_seconds for row in report.rows
    ):
        raise ValueError(
            "max_outcome_freshness_age_seconds must equal max row freshness age",
        )
    if report.min_close_time_delta_seconds != _min_optional_decimal(
        row.close_time_delta_seconds for row in report.rows
    ):
        raise ValueError(
            "min_close_time_delta_seconds must equal min row close time delta",
        )
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.rows != tuple(sorted(report.rows, key=_row_priority_sort_key)):
        raise ValueError("rows must use deterministic priority sort")
    for row in report.rows:
        _validate_row_datetimes_against_report(row, report.generated_at)


def _validate_row_datetimes_against_report(
    row: MarketOutcomeFreshnessRecheckPriorityRow,
    generated_at: datetime,
) -> None:
    if row.last_outcome_checked_at is None:
        if row.outcome_freshness_age_seconds is not None:
            raise ValueError(
                "outcome_freshness_age_seconds must be None when never checked",
            )
    else:
        if row.last_outcome_checked_at > generated_at:
            raise ValueError("last_outcome_checked_at must not be after generated_at")
        expected_age = _timedelta_seconds(generated_at - row.last_outcome_checked_at)
        if row.outcome_freshness_age_seconds != expected_age:
            raise ValueError(
                "outcome_freshness_age_seconds must match generated_at delta",
            )
    if row.market_close_time is None:
        if row.close_time_delta_seconds is not None:
            raise ValueError(
                "close_time_delta_seconds must be None when close time is absent",
            )
    else:
        expected_delta = _timedelta_seconds(row.market_close_time - generated_at)
        if row.close_time_delta_seconds != expected_delta:
            raise ValueError("close_time_delta_seconds must match generated_at delta")


def _timedelta_seconds(value: timedelta) -> Decimal:
    return (
        Decimal(value.days) * SECONDS_PER_DAY
        + Decimal(value.seconds)
        + (Decimal(value.microseconds) / MICROSECONDS_PER_SECOND)
    )


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    order = {reason_code: index for index, reason_code in enumerate(REASON_CODE_ORDER)}
    for item in items:
        _require_canonical_string("reason_codes", item)
        if item not in order:
            raise ValueError("reason_codes must contain known reason codes")
    return tuple(sorted(set(items), key=lambda item: order[item]))


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, Number):
        raise ValueError("JSON payload contains a non-Decimal numeric value")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None or offset != timedelta(0):
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_optional_utc_datetime(
    field_name: str,
    value: object,
) -> datetime | None:
    if value is None:
        return None
    return _require_utc_datetime(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")


def _require_positive_whole_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _validate_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{field_name} readonly must be True")
