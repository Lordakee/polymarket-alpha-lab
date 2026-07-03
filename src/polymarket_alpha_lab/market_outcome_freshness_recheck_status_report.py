from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext


DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_STATUS_CONFIG_VERSION = (
    "market-outcome-freshness-recheck-status-v0"
)
ZERO = Decimal("0")
ZERO_SECONDS = Decimal("0.000000")
ZERO_RATIO = Decimal("0.000000")
ONE = Decimal("1")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECOND_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)

ROW_STATUSES = ("blocked", "overdue", "watch", "cleared")
REPORT_STATUSES = ("empty", "blocked", "overdue", "watch", "cleared")
STATUS_WEIGHT = {"blocked": 0, "overdue": 1, "watch": 2, "cleared": 3}
REPORT_STATUS_WEIGHT = {"blocked": 0, "overdue": 1, "watch": 2, "cleared": 3}
REASON_CODES = (
    "outcome_freshness_recheck_blocked",
    "outcome_freshness_recheck_proxy_contradiction",
    "outcome_freshness_recheck_overdue",
    "outcome_freshness_recheck_stale_source",
    "outcome_freshness_recheck_acknowledgement_lag",
    "outcome_freshness_recheck_cleared",
    "outcome_freshness_recheck_empty",
)
REASON_WEIGHT = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckStatusConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_STATUS_CONFIG_VERSION
    stale_source_after_seconds: Decimal = Decimal("3600")
    acknowledgement_lag_after_seconds: Decimal = Decimal("900")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_source_after_seconds",
            _normalize_positive_integral_decimal(
                "stale_source_after_seconds",
                self.stale_source_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_after_seconds",
            _normalize_positive_integral_decimal(
                "acknowledgement_lag_after_seconds",
                self.acknowledgement_lag_after_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckStatusInput:
    recheck_id: str
    market_id: str
    outcome_id: str
    team_id: str
    requested_at: datetime
    due_at: datetime
    source_checked_at: datetime | None
    official_outcome: str | None
    proxy_outcome: str | None
    acknowledged_at: datetime | None = None
    cleared_at: datetime | None = None
    blocked_at: datetime | None = None
    blocked_reason_code: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("recheck_id", "market_id", "outcome_id", "team_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "requested_at",
            _as_utc("requested_at", self.requested_at),
        )
        object.__setattr__(self, "due_at", _as_utc("due_at", self.due_at))
        object.__setattr__(
            self,
            "source_checked_at",
            _as_optional_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "cleared_at",
            _as_optional_utc("cleared_at", self.cleared_at),
        )
        object.__setattr__(
            self,
            "blocked_at",
            _as_optional_utc("blocked_at", self.blocked_at),
        )
        _require_optional_canonical_string("official_outcome", self.official_outcome)
        _require_optional_canonical_string("proxy_outcome", self.proxy_outcome)
        _require_optional_canonical_string(
            "blocked_reason_code",
            self.blocked_reason_code,
        )
        _validate_input_shape(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckStatusRow:
    recheck_id: str
    market_id: str
    outcome_id: str
    team_id: str
    requested_at: datetime
    due_at: datetime
    source_checked_at: datetime | None
    official_outcome: str | None
    proxy_outcome: str | None
    acknowledged_at: datetime | None
    cleared_at: datetime | None
    blocked_at: datetime | None
    blocked_reason_code: str | None
    recheck_age_seconds: Decimal
    overdue_age_seconds: Decimal
    source_age_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("recheck_id", "market_id", "outcome_id", "team_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "requested_at",
            _as_utc("requested_at", self.requested_at),
        )
        object.__setattr__(self, "due_at", _as_utc("due_at", self.due_at))
        object.__setattr__(
            self,
            "source_checked_at",
            _as_optional_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "cleared_at",
            _as_optional_utc("cleared_at", self.cleared_at),
        )
        object.__setattr__(
            self,
            "blocked_at",
            _as_optional_utc("blocked_at", self.blocked_at),
        )
        _require_optional_canonical_string("official_outcome", self.official_outcome)
        _require_optional_canonical_string("proxy_outcome", self.proxy_outcome)
        _require_optional_canonical_string(
            "blocked_reason_code",
            self.blocked_reason_code,
        )
        for field_name in (
            "recheck_age_seconds",
            "overdue_age_seconds",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _require_known_value("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_shape(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckStatusReport:
    generated_at: datetime
    config_version: str
    recheck_count: Decimal
    blocked_count: Decimal
    overdue_count: Decimal
    watch_count: Decimal
    cleared_count: Decimal
    stale_source_count: Decimal
    proxy_contradiction_count: Decimal
    acknowledgement_lag_count: Decimal
    cleared_ratio: Decimal
    max_recheck_age_seconds: Decimal
    max_overdue_age_seconds: Decimal
    max_source_age_seconds: Decimal
    max_acknowledgement_lag_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "recheck_count",
            "blocked_count",
            "overdue_count",
            "watch_count",
            "cleared_count",
            "stale_source_count",
            "proxy_contradiction_count",
            "acknowledgement_lag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "cleared_ratio",
            _normalize_ratio("cleared_ratio", self.cleared_ratio),
        )
        for field_name in (
            "max_recheck_age_seconds",
            "max_overdue_age_seconds",
            "max_source_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_known_value("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_outcome_freshness_recheck_status_report(
    rechecks: Iterable[MarketOutcomeFreshnessRecheckStatusInput],
    *,
    config: MarketOutcomeFreshnessRecheckStatusConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckStatusReport:
    if type(config) is not MarketOutcomeFreshnessRecheckStatusConfig:
        raise ValueError(
            "config must be a MarketOutcomeFreshnessRecheckStatusConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized_rechecks = _normalize_rechecks(rechecks)
    rows = tuple(
        sorted(
            (
                _row_from_recheck(
                    recheck,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for recheck in normalized_rechecks
            ),
            key=_row_sort_key,
        ),
    )

    return MarketOutcomeFreshnessRecheckStatusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        recheck_count=_decimal_count(rows),
        blocked_count=_status_count(rows, "blocked"),
        overdue_count=_status_count(rows, "overdue"),
        watch_count=_status_count(rows, "watch"),
        cleared_count=_status_count(rows, "cleared"),
        stale_source_count=_reason_count(
            rows,
            "outcome_freshness_recheck_stale_source",
        ),
        proxy_contradiction_count=_reason_count(
            rows,
            "outcome_freshness_recheck_proxy_contradiction",
        ),
        acknowledgement_lag_count=_reason_count(
            rows,
            "outcome_freshness_recheck_acknowledgement_lag",
        ),
        cleared_ratio=_cleared_ratio(rows),
        max_recheck_age_seconds=_max_recheck_age_seconds(rows),
        max_overdue_age_seconds=_max_overdue_age_seconds(rows),
        max_source_age_seconds=_max_source_age_seconds(rows),
        max_acknowledgement_lag_seconds=_max_acknowledgement_lag_seconds(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_outcome_freshness_recheck_status_report_payload(
    report: MarketOutcomeFreshnessRecheckStatusReport,
) -> dict[str, object]:
    if type(report) is not MarketOutcomeFreshnessRecheckStatusReport:
        raise ValueError(
            "report must be a MarketOutcomeFreshnessRecheckStatusReport",
        )
    ready = _payload_value(report)
    if type(ready) is not dict:
        raise ValueError("report payload must be a dict")
    return ready


def _row_from_recheck(
    recheck: MarketOutcomeFreshnessRecheckStatusInput,
    *,
    config: MarketOutcomeFreshnessRecheckStatusConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckStatusRow:
    _require_recheck_times_not_after_generated(recheck, generated_at)
    recheck_age_seconds = _seconds_between(recheck.requested_at, generated_at)
    overdue_age_seconds = (
        _seconds_between(recheck.due_at, generated_at)
        if recheck.due_at < generated_at
        else ZERO_SECONDS
    )
    source_age_seconds = (
        None
        if recheck.source_checked_at is None
        else _seconds_between(recheck.source_checked_at, generated_at)
    )
    acknowledgement_lag_seconds = _seconds_between(
        recheck.requested_at,
        recheck.acknowledged_at
        if recheck.acknowledged_at is not None
        else generated_at,
    )
    reason_codes = _row_reason_codes(
        recheck=recheck,
        overdue_age_seconds=overdue_age_seconds,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )

    return MarketOutcomeFreshnessRecheckStatusRow(
        recheck_id=recheck.recheck_id,
        market_id=recheck.market_id,
        outcome_id=recheck.outcome_id,
        team_id=recheck.team_id,
        requested_at=recheck.requested_at,
        due_at=recheck.due_at,
        source_checked_at=recheck.source_checked_at,
        official_outcome=recheck.official_outcome,
        proxy_outcome=recheck.proxy_outcome,
        acknowledged_at=recheck.acknowledged_at,
        cleared_at=recheck.cleared_at,
        blocked_at=recheck.blocked_at,
        blocked_reason_code=recheck.blocked_reason_code,
        recheck_age_seconds=recheck_age_seconds,
        overdue_age_seconds=overdue_age_seconds,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    recheck: MarketOutcomeFreshnessRecheckStatusInput,
    overdue_age_seconds: Decimal,
    source_age_seconds: Decimal | None,
    acknowledgement_lag_seconds: Decimal,
    config: MarketOutcomeFreshnessRecheckStatusConfig,
) -> tuple[str, ...]:
    # cleared_at is audit evidence; active freshness failures still drive status.
    requested_codes: list[str] = []
    if recheck.blocked_at is not None:
        requested_codes.append("outcome_freshness_recheck_blocked")
    if _has_proxy_contradiction(recheck):
        requested_codes.append("outcome_freshness_recheck_proxy_contradiction")
    if (
        "outcome_freshness_recheck_blocked" not in requested_codes
        and "outcome_freshness_recheck_proxy_contradiction" not in requested_codes
        and overdue_age_seconds > ZERO
    ):
        requested_codes.append("outcome_freshness_recheck_overdue")
    if source_age_seconds is None or source_age_seconds > config.stale_source_after_seconds:
        requested_codes.append("outcome_freshness_recheck_stale_source")
    if acknowledgement_lag_seconds > config.acknowledgement_lag_after_seconds:
        requested_codes.append("outcome_freshness_recheck_acknowledgement_lag")
    if not requested_codes:
        requested_codes.append("outcome_freshness_recheck_cleared")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in requested_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "outcome_freshness_recheck_blocked" in reason_codes
        or "outcome_freshness_recheck_proxy_contradiction" in reason_codes
    ):
        return "blocked"
    if "outcome_freshness_recheck_overdue" in reason_codes:
        return "overdue"
    if reason_codes == ("outcome_freshness_recheck_cleared",):
        return "cleared"
    return "watch"


def _report_status(rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...]) -> str:
    if not rows:
        return "empty"
    return min(
        (row.status for row in rows),
        key=lambda status: REPORT_STATUS_WEIGHT[status],
    )


def _report_reason_codes(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("outcome_freshness_recheck_empty",)
    requested_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "outcome_freshness_recheck_cleared"
    )
    if not requested_codes:
        return ("outcome_freshness_recheck_cleared",)
    unique_codes = frozenset(requested_codes)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in unique_codes)


def _has_proxy_contradiction(
    recheck: MarketOutcomeFreshnessRecheckStatusInput,
) -> bool:
    return (
        recheck.official_outcome is not None
        and recheck.proxy_outcome is not None
        and recheck.official_outcome != recheck.proxy_outcome
    )


def _normalize_rechecks(
    values: Iterable[MarketOutcomeFreshnessRecheckStatusInput],
) -> tuple[MarketOutcomeFreshnessRecheckStatusInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rechecks must be an iterable")
    try:
        rechecks = tuple(values)
    except TypeError as exc:
        raise ValueError("rechecks must be an iterable") from exc
    recheck_ids: set[str] = set()
    for recheck in rechecks:
        if type(recheck) is not MarketOutcomeFreshnessRecheckStatusInput:
            raise ValueError(
                "rechecks must contain MarketOutcomeFreshnessRecheckStatusInput values",
            )
        _require_hard_flags(recheck)
        if recheck.recheck_id in recheck_ids:
            raise ValueError("recheck_id values must be unique")
        recheck_ids.add(recheck.recheck_id)
    return rechecks


def _normalize_rows(
    values: Iterable[MarketOutcomeFreshnessRecheckStatusRow],
) -> tuple[MarketOutcomeFreshnessRecheckStatusRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketOutcomeFreshnessRecheckStatusRow:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckStatusRow values",
            )
        _require_hard_flags(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    return rows


def _validate_input_shape(recheck: MarketOutcomeFreshnessRecheckStatusInput) -> None:
    if recheck.requested_at > recheck.due_at:
        raise ValueError("requested_at must be <= due_at")
    if recheck.acknowledged_at is not None and recheck.acknowledged_at < recheck.requested_at:
        raise ValueError("acknowledged_at must be >= requested_at")
    if recheck.cleared_at is not None and recheck.cleared_at < recheck.requested_at:
        raise ValueError("cleared_at must be >= requested_at")
    if recheck.blocked_at is not None and recheck.blocked_at < recheck.requested_at:
        raise ValueError("blocked_at must be >= requested_at")
    if recheck.cleared_at is not None and recheck.blocked_at is not None:
        raise ValueError("cleared_at and blocked_at cannot both be present")
    if recheck.blocked_at is not None and recheck.blocked_reason_code is None:
        raise ValueError("blocked_reason_code is required when blocked_at is present")
    if recheck.blocked_at is None and recheck.blocked_reason_code is not None:
        raise ValueError("blocked_reason_code requires blocked_at")


def _validate_row_shape(row: MarketOutcomeFreshnessRecheckStatusRow) -> None:
    if row.requested_at > row.due_at:
        raise ValueError("requested_at must be <= due_at")
    if row.source_checked_at is None and row.source_age_seconds is not None:
        raise ValueError("source_age_seconds requires source_checked_at")
    if row.source_checked_at is not None and row.source_age_seconds is None:
        raise ValueError("source_age_seconds is required with source_checked_at")
    if row.acknowledged_at is not None and row.acknowledged_at < row.requested_at:
        raise ValueError("acknowledged_at must be >= requested_at")
    if row.cleared_at is not None and row.cleared_at < row.requested_at:
        raise ValueError("cleared_at must be >= requested_at")
    if row.blocked_at is not None and row.blocked_at < row.requested_at:
        raise ValueError("blocked_at must be >= requested_at")
    if row.cleared_at is not None and row.blocked_at is not None:
        raise ValueError("cleared_at and blocked_at cannot both be present")
    if row.blocked_at is not None and row.blocked_reason_code is None:
        raise ValueError("blocked_reason_code is required when blocked_at is present")
    if row.blocked_at is None and row.blocked_reason_code is not None:
        raise ValueError("blocked_reason_code requires blocked_at")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: MarketOutcomeFreshnessRecheckStatusReport,
) -> None:
    rows = report.rows
    if report.recheck_count != _decimal_count(rows):
        raise ValueError("recheck_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.overdue_count != _status_count(rows, "overdue"):
        raise ValueError("overdue_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.cleared_count != _status_count(rows, "cleared"):
        raise ValueError("cleared_count must match rows")
    if report.stale_source_count != _reason_count(
        rows,
        "outcome_freshness_recheck_stale_source",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.proxy_contradiction_count != _reason_count(
        rows,
        "outcome_freshness_recheck_proxy_contradiction",
    ):
        raise ValueError("proxy_contradiction_count must match rows")
    if report.acknowledgement_lag_count != _reason_count(
        rows,
        "outcome_freshness_recheck_acknowledgement_lag",
    ):
        raise ValueError("acknowledgement_lag_count must match rows")
    if report.cleared_ratio != _cleared_ratio(rows):
        raise ValueError("cleared_ratio must match rows")
    if report.max_recheck_age_seconds != _max_recheck_age_seconds(rows):
        raise ValueError("max_recheck_age_seconds must match rows")
    if report.max_overdue_age_seconds != _max_overdue_age_seconds(rows):
        raise ValueError("max_overdue_age_seconds must match rows")
    if report.max_source_age_seconds != _max_source_age_seconds(rows):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_acknowledgement_lag_seconds != _max_acknowledgement_lag_seconds(rows):
        raise ValueError("max_acknowledgement_lag_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_recheck_times_not_after_generated(
    recheck: MarketOutcomeFreshnessRecheckStatusInput,
    generated_at: datetime,
) -> None:
    _require_not_after_generated("requested_at", recheck.requested_at, generated_at)
    _require_not_after_generated(
        "source_checked_at",
        recheck.source_checked_at,
        generated_at,
    )
    _require_not_after_generated(
        "acknowledged_at",
        recheck.acknowledged_at,
        generated_at,
    )
    _require_not_after_generated("cleared_at", recheck.cleared_at, generated_at)
    _require_not_after_generated("blocked_at", recheck.blocked_at, generated_at)


def _require_not_after_generated(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must be <= generated_at")


def _row_sort_key(
    row: MarketOutcomeFreshnessRecheckStatusRow,
) -> tuple[int, int, str, str, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        _primary_reason_weight(row.reason_codes),
        row.team_id,
        row.market_id,
        row.outcome_id,
        row.recheck_id,
    )


def _primary_reason_weight(reason_codes: tuple[str, ...]) -> int:
    return min(REASON_WEIGHT[reason_code] for reason_code in reason_codes)


def _status_count(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(tuple(row for row in rows if row.status == status))


def _reason_count(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(tuple(row for row in rows if reason_code in row.reason_codes))


def _cleared_ratio(rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (_status_count(rows, "cleared") / _decimal_count(rows)).quantize(
            RATIO_QUANTUM,
        )


def _max_recheck_age_seconds(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SECONDS
    return max(row.recheck_age_seconds for row in rows)


def _max_overdue_age_seconds(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
) -> Decimal:
    overdue_rows = tuple(
        row
        for row in rows
        if "outcome_freshness_recheck_overdue" in row.reason_codes
    )
    if not overdue_rows:
        return ZERO_SECONDS
    return max(row.overdue_age_seconds for row in overdue_rows)


def _max_source_age_seconds(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
) -> Decimal:
    source_ages = tuple(
        row.source_age_seconds for row in rows if row.source_age_seconds is not None
    )
    if not source_ages:
        return ZERO_SECONDS
    return max(source_ages)


def _max_acknowledgement_lag_seconds(
    rows: tuple[MarketOutcomeFreshnessRecheckStatusRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SECONDS
    return max(row.acknowledgement_lag_seconds for row in rows)


def _decimal_count(values: tuple[object, ...]) -> Decimal:
    return Decimal(len(values))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta < timedelta(0):
        raise ValueError("datetime range must be nonnegative")
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize_seconds(seconds)


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_canonical_string(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_canonical_string(field_name, value)


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be known")


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_integral_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_seconds(decimal_value)


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_WEIGHT:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected_codes = tuple(
        reason_code for reason_code in REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _quantize_seconds(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("seconds value must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECOND_QUANTUM)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_STATUS_CONFIG_VERSION",
    "MarketOutcomeFreshnessRecheckStatusConfig",
    "MarketOutcomeFreshnessRecheckStatusInput",
    "MarketOutcomeFreshnessRecheckStatusReport",
    "MarketOutcomeFreshnessRecheckStatusRow",
    "build_market_outcome_freshness_recheck_status_report",
    "market_outcome_freshness_recheck_status_report_payload",
)
