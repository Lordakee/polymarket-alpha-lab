from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_SLA_CONFIG_VERSION",
    "MarketOutcomeFreshnessRecheckSlaConfig",
    "MarketOutcomeFreshnessRecheckSlaItem",
    "MarketOutcomeFreshnessRecheckSlaReport",
    "MarketOutcomeFreshnessRecheckSlaRow",
    "build_market_outcome_freshness_recheck_sla_report",
    "market_outcome_freshness_recheck_sla_report_payload",
)


DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_SLA_CONFIG_VERSION = (
    "market-outcome-freshness-recheck-sla-v1"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SLA_STATUSES = ("blocked", "watch", "pass")
SLA_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
CLEAR_REASON_CODE = "outcome_freshness_recheck_clear"
NO_RECHECKS_REASON_CODE = "no_outcome_freshness_rechecks"
READY_REASON_CODE = "outcome_freshness_recheck_sla_ready"
REASON_CODE_WEIGHT = {
    "missing_recheck_owner": 0,
    "proxy_contradicts_official_source": 1,
    "recheck_sla_overdue": 2,
    "official_source_stale": 3,
    "team_acknowledgement_lag": 4,
    CLEAR_REASON_CODE: 5,
    READY_REASON_CODE: 6,
    NO_RECHECKS_REASON_CODE: 7,
}


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckSlaConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_SLA_CONFIG_VERSION
    stale_official_source_after_seconds: Decimal = Decimal("86400.000000")
    team_ack_lag_after_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_official_source_after_seconds",
            _normalize_nonnegative_decimal(
                "stale_official_source_after_seconds",
                self.stale_official_source_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "team_ack_lag_after_seconds",
            _normalize_nonnegative_decimal(
                "team_ack_lag_after_seconds",
                self.team_ack_lag_after_seconds,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckSlaItem:
    condition_id: str
    outcome_key: str
    queued_at: datetime
    recheck_due_at: datetime
    owner_team_id: str | None
    official_source_checked_at: datetime
    proxy_contradicts_official: bool
    team_acknowledged_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("outcome_key", self.outcome_key)
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "recheck_due_at",
            _as_utc("recheck_due_at", self.recheck_due_at),
        )
        object.__setattr__(
            self,
            "official_source_checked_at",
            _as_utc("official_source_checked_at", self.official_source_checked_at),
        )
        if self.owner_team_id is not None:
            _require_canonical_string("owner_team_id", self.owner_team_id)
        if type(self.proxy_contradicts_official) is not bool:
            raise ValueError("proxy_contradicts_official must be a bool")
        if self.team_acknowledged_at is not None:
            object.__setattr__(
                self,
                "team_acknowledged_at",
                _as_utc("team_acknowledged_at", self.team_acknowledged_at),
            )
        if self.recheck_due_at < self.queued_at:
            raise ValueError("recheck_due_at must not precede queued_at")
        if (
            self.team_acknowledged_at is not None
            and self.team_acknowledged_at < self.queued_at
        ):
            raise ValueError("team_acknowledged_at must not precede queued_at")
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckSlaRow:
    condition_id: str
    outcome_key: str
    queued_at: datetime
    recheck_due_at: datetime
    owner_team_id: str | None
    official_source_checked_at: datetime
    proxy_contradicts_official: bool
    team_acknowledged_at: datetime | None
    queue_age_seconds: Decimal
    overdue_by_seconds: Decimal
    official_source_age_seconds: Decimal
    team_ack_lag_seconds: Decimal
    sla_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("outcome_key", self.outcome_key)
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "recheck_due_at",
            _as_utc("recheck_due_at", self.recheck_due_at),
        )
        object.__setattr__(
            self,
            "official_source_checked_at",
            _as_utc("official_source_checked_at", self.official_source_checked_at),
        )
        if self.owner_team_id is not None:
            _require_canonical_string("owner_team_id", self.owner_team_id)
        if type(self.proxy_contradicts_official) is not bool:
            raise ValueError("proxy_contradicts_official must be a bool")
        if self.team_acknowledged_at is not None:
            object.__setattr__(
                self,
                "team_acknowledged_at",
                _as_utc("team_acknowledged_at", self.team_acknowledged_at),
            )
        for field_name in (
            "queue_age_seconds",
            "overdue_by_seconds",
            "official_source_age_seconds",
            "team_ack_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_sla_status("sla_status", self.sla_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckSlaReport:
    generated_at: datetime
    config_version: str
    stale_official_source_after_seconds: Decimal
    team_ack_lag_after_seconds: Decimal
    total_recheck_count: Decimal
    pass_recheck_count: Decimal
    watch_recheck_count: Decimal
    blocked_recheck_count: Decimal
    overdue_recheck_count: Decimal
    missing_owner_count: Decimal
    stale_official_source_count: Decimal
    proxy_contradiction_count: Decimal
    team_ack_lag_count: Decimal
    clear_recheck_ratio: Decimal
    sla_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketOutcomeFreshnessRecheckSlaRow, ...]
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
            "stale_official_source_after_seconds",
            "team_ack_lag_after_seconds",
            "total_recheck_count",
            "pass_recheck_count",
            "watch_recheck_count",
            "blocked_recheck_count",
            "overdue_recheck_count",
            "missing_owner_count",
            "stale_official_source_count",
            "proxy_contradiction_count",
            "team_ack_lag_count",
            "clear_recheck_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("clear_recheck_ratio", self.clear_recheck_ratio)
        _require_sla_status("sla_status", self.sla_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_market_outcome_freshness_recheck_sla_report(
    items: tuple[MarketOutcomeFreshnessRecheckSlaItem, ...]
    | list[MarketOutcomeFreshnessRecheckSlaItem],
    *,
    config: MarketOutcomeFreshnessRecheckSlaConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckSlaReport:
    if type(config) is not MarketOutcomeFreshnessRecheckSlaConfig:
        raise ValueError("config must be a MarketOutcomeFreshnessRecheckSlaConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(
        sorted(
            (
                _row_from_item(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_items
            ),
            key=_row_sort_key,
        ),
    )
    return MarketOutcomeFreshnessRecheckSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        stale_official_source_after_seconds=config.stale_official_source_after_seconds,
        team_ack_lag_after_seconds=config.team_ack_lag_after_seconds,
        total_recheck_count=_decimal_count(len(rows)),
        pass_recheck_count=_decimal_count(
            sum(1 for row in rows if row.sla_status == "pass"),
        ),
        watch_recheck_count=_decimal_count(
            sum(1 for row in rows if row.sla_status == "watch"),
        ),
        blocked_recheck_count=_decimal_count(
            sum(1 for row in rows if row.sla_status == "blocked"),
        ),
        overdue_recheck_count=_decimal_count(
            sum(1 for row in rows if "recheck_sla_overdue" in row.reason_codes),
        ),
        missing_owner_count=_decimal_count(
            sum(1 for row in rows if "missing_recheck_owner" in row.reason_codes),
        ),
        stale_official_source_count=_decimal_count(
            sum(1 for row in rows if "official_source_stale" in row.reason_codes),
        ),
        proxy_contradiction_count=_decimal_count(
            sum(
                1
                for row in rows
                if "proxy_contradicts_official_source" in row.reason_codes
            ),
        ),
        team_ack_lag_count=_decimal_count(
            sum(1 for row in rows if "team_acknowledgement_lag" in row.reason_codes),
        ),
        clear_recheck_ratio=_ratio(
            sum(1 for row in rows if row.sla_status == "pass"),
            len(rows),
        ),
        sla_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_outcome_freshness_recheck_sla_report_payload(
    report: MarketOutcomeFreshnessRecheckSlaReport,
) -> dict[str, object]:
    if type(report) is not MarketOutcomeFreshnessRecheckSlaReport:
        raise ValueError("report must be a MarketOutcomeFreshnessRecheckSlaReport")
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    return value


def _row_from_item(
    item: MarketOutcomeFreshnessRecheckSlaItem,
    *,
    config: MarketOutcomeFreshnessRecheckSlaConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckSlaRow:
    _require_not_future("queued_at", item.queued_at, generated_at)
    _require_not_future(
        "official_source_checked_at",
        item.official_source_checked_at,
        generated_at,
    )
    if item.team_acknowledged_at is not None:
        _require_not_future(
            "team_acknowledged_at",
            item.team_acknowledged_at,
            generated_at,
        )
    queue_age_seconds = _elapsed_seconds(item.queued_at, generated_at)
    overdue_by_seconds = (
        _elapsed_seconds(item.recheck_due_at, generated_at)
        if item.recheck_due_at < generated_at
        else ZERO
    )
    official_source_age_seconds = _elapsed_seconds(
        item.official_source_checked_at,
        generated_at,
    )
    team_ack_lag_seconds = _elapsed_seconds(
        item.queued_at,
        item.team_acknowledged_at if item.team_acknowledged_at is not None else generated_at,
    )
    reason_codes = _row_reason_codes(
        item=item,
        overdue_by_seconds=overdue_by_seconds,
        official_source_age_seconds=official_source_age_seconds,
        team_ack_lag_seconds=team_ack_lag_seconds,
        config=config,
    )
    return MarketOutcomeFreshnessRecheckSlaRow(
        condition_id=item.condition_id,
        outcome_key=item.outcome_key,
        queued_at=item.queued_at,
        recheck_due_at=item.recheck_due_at,
        owner_team_id=item.owner_team_id,
        official_source_checked_at=item.official_source_checked_at,
        proxy_contradicts_official=item.proxy_contradicts_official,
        team_acknowledged_at=item.team_acknowledged_at,
        queue_age_seconds=queue_age_seconds,
        overdue_by_seconds=overdue_by_seconds,
        official_source_age_seconds=official_source_age_seconds,
        team_ack_lag_seconds=team_ack_lag_seconds,
        sla_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: MarketOutcomeFreshnessRecheckSlaItem,
    overdue_by_seconds: Decimal,
    official_source_age_seconds: Decimal,
    team_ack_lag_seconds: Decimal,
    config: MarketOutcomeFreshnessRecheckSlaConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.owner_team_id is None:
        reason_codes.append("missing_recheck_owner")
    if item.proxy_contradicts_official:
        reason_codes.append("proxy_contradicts_official_source")
    if overdue_by_seconds > ZERO:
        reason_codes.append("recheck_sla_overdue")
    if official_source_age_seconds > config.stale_official_source_after_seconds:
        reason_codes.append("official_source_stale")
    if team_ack_lag_seconds > config.team_ack_lag_after_seconds:
        reason_codes.append("team_acknowledgement_lag")
    if not reason_codes:
        return (CLEAR_REASON_CODE,)
    return tuple(sorted(reason_codes, key=_reason_code_key))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "missing_recheck_owner" in reason_codes
        or "proxy_contradicts_official_source" in reason_codes
    ):
        return "blocked"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[MarketOutcomeFreshnessRecheckSlaRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.sla_status == "blocked" for row in rows):
        return "blocked"
    if any(row.sla_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketOutcomeFreshnessRecheckSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_RECHECKS_REASON_CODE,)
    issue_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    }
    if not issue_codes:
        return (READY_REASON_CODE,)
    return tuple(sorted(issue_codes, key=_reason_code_key))


def _row_sort_key(
    row: MarketOutcomeFreshnessRecheckSlaRow,
) -> tuple[int, str, str]:
    return (
        SLA_STATUS_WEIGHT[row.sla_status],
        row.condition_id,
        row.outcome_key,
    )


def _reason_code_key(reason_code: str) -> int:
    return REASON_CODE_WEIGHT[reason_code]


def _normalize_items(
    items: tuple[MarketOutcomeFreshnessRecheckSlaItem, ...]
    | list[MarketOutcomeFreshnessRecheckSlaItem],
) -> tuple[MarketOutcomeFreshnessRecheckSlaItem, ...]:
    if type(items) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    normalized = tuple(items)
    for item in normalized:
        if type(item) is not MarketOutcomeFreshnessRecheckSlaItem:
            raise ValueError(
                "items must contain MarketOutcomeFreshnessRecheckSlaItem values",
            )
    return normalized


def _normalize_rows(
    rows: tuple[MarketOutcomeFreshnessRecheckSlaRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckSlaRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in normalized:
        if type(row) is not MarketOutcomeFreshnessRecheckSlaRow:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckSlaRow values",
            )
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sla sort")
    return normalized


def _validate_report_consistency(
    report: MarketOutcomeFreshnessRecheckSlaReport,
) -> None:
    if report.total_recheck_count != _decimal_count(len(report.rows)):
        raise ValueError("total_recheck_count must match rows")
    if report.pass_recheck_count != _decimal_count(
        sum(1 for row in report.rows if row.sla_status == "pass"),
    ):
        raise ValueError("pass_recheck_count must match rows")
    if report.watch_recheck_count != _decimal_count(
        sum(1 for row in report.rows if row.sla_status == "watch"),
    ):
        raise ValueError("watch_recheck_count must match rows")
    if report.blocked_recheck_count != _decimal_count(
        sum(1 for row in report.rows if row.sla_status == "blocked"),
    ):
        raise ValueError("blocked_recheck_count must match rows")
    if report.overdue_recheck_count != _decimal_count(
        sum(1 for row in report.rows if "recheck_sla_overdue" in row.reason_codes),
    ):
        raise ValueError("overdue_recheck_count must match rows")
    if report.missing_owner_count != _decimal_count(
        sum(1 for row in report.rows if "missing_recheck_owner" in row.reason_codes),
    ):
        raise ValueError("missing_owner_count must match rows")
    if report.stale_official_source_count != _decimal_count(
        sum(1 for row in report.rows if "official_source_stale" in row.reason_codes),
    ):
        raise ValueError("stale_official_source_count must match rows")
    if report.proxy_contradiction_count != _decimal_count(
        sum(
            1
            for row in report.rows
            if "proxy_contradicts_official_source" in row.reason_codes
        ),
    ):
        raise ValueError("proxy_contradiction_count must match rows")
    if report.team_ack_lag_count != _decimal_count(
        sum(1 for row in report.rows if "team_acknowledgement_lag" in row.reason_codes),
    ):
        raise ValueError("team_ack_lag_count must match rows")
    if report.clear_recheck_ratio != _ratio(
        sum(1 for row in report.rows if row.sla_status == "pass"),
        len(report.rows),
    ):
        raise ValueError("clear_recheck_ratio must match rows")
    if report.sla_status != _report_status(report.rows):
        raise ValueError("sla_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
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


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be a tuple")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple") from exc
    if not reason_codes:
        raise ValueError("reason_codes must include at least one code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODE_WEIGHT:
            raise ValueError("reason_codes include an unknown code")
    return tuple(sorted(reason_codes, key=_reason_code_key))


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    return (Decimal(numerator) / Decimal(denominator)).quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a non-negative int")
    return Decimal(value).quantize(QUANTUM)


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end must not precede start")
    delta = end - start
    microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    return (Decimal(microseconds) / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return value.quantize(QUANTUM)


def _require_ratio(field_name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_sla_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in SLA_STATUSES:
        raise ValueError(f"{field_name} must be one of {SLA_STATUSES!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty stripped string")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
