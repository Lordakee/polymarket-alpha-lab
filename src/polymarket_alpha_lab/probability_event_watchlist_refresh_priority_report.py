"""Pure in-memory probability event watchlist refresh priority report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Sequence

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_PROBABILITY_EVENT_WATCHLIST_REFRESH_PRIORITY_CONFIG_VERSION = (
    "probability-event-watchlist-refresh-priority-report-v0"
)

WATCH_STATUSES = ("active", "paused", "candidate")
LIQUIDITY_STATUSES = ("healthy", "thin", "blocked")
MEMORY_POLICY_STATUSES = ("current", "refresh_due", "blocked")
REFRESH_PRIORITIES = ("low", "medium", "high", "critical")
REPORT_STATUSES = ("pass", "watch", "block")
MANUAL_NEXT_STEPS = (
    "paper_review_continue_watchlist_monitoring",
    "paper_review_schedule_watchlist_refresh",
    "paper_review_refresh_sources_today",
    "paper_review_resolve_refresh_blockers",
)
REASON_CODES = (
    "watchlist_refresh_current",
    "watch_status_paused",
    "watch_status_candidate",
    "liquidity_blocked",
    "memory_policy_blocked",
    "source_refresh_overdue",
    "source_refresh_stale",
    "market_close_imminent",
    "market_close_near",
    "edge_threshold_imminent",
    "edge_threshold_near",
    "liquidity_thin",
    "memory_policy_refresh_due",
)

QUANT = Decimal("0.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PRIORITY_RANK = {
    "low": Decimal("0.000000"),
    "medium": Decimal("1.000000"),
    "high": Decimal("2.000000"),
    "critical": Decimal("3.000000"),
}
LOCAL_UNSAFE_TEXT_FRAGMENTS = (
    "auth",
    "credential",
    "private",
    "secret",
    "token",
    "wallet",
    "order",
    "broker",
    "buy",
    "sell",
    "trade",
    "persist",
    "database",
    "network",
    "live",
)


@dataclass(frozen=True)
class ProbabilityEventWatchlistRefreshPriorityConfig:
    config_version: str = DEFAULT_PROBABILITY_EVENT_WATCHLIST_REFRESH_PRIORITY_CONFIG_VERSION
    source_stale_hours: Decimal = Decimal("6.000000")
    source_overdue_hours: Decimal = Decimal("24.000000")
    market_close_near_hours: Decimal = Decimal("48.000000")
    market_close_imminent_hours: Decimal = Decimal("6.000000")
    edge_watch_probability: Decimal = Decimal("0.100000")
    edge_urgent_probability: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "source_stale_hours",
            "source_overdue_hours",
            "market_close_near_hours",
            "market_close_imminent_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("edge_watch_probability", "edge_urgent_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        reject_unsafe_surface_fields("probability event watchlist refresh priority config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventWatchlistRefreshPriorityInput:
    event_id: str
    watch_status: str
    source_age_hours: Decimal
    market_close_hours: Decimal
    edge_to_threshold_probability: Decimal
    liquidity_status: str
    memory_policy_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_member("watch_status", self.watch_status, WATCH_STATUSES)
        _require_member("liquidity_status", self.liquidity_status, LIQUIDITY_STATUSES)
        _require_member(
            "memory_policy_status",
            self.memory_policy_status,
            MEMORY_POLICY_STATUSES,
        )
        for field_name in (
            "source_age_hours",
            "market_close_hours",
            "edge_to_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_to_threshold_probability",
            _require_ratio(
                "edge_to_threshold_probability",
                self.edge_to_threshold_probability,
            ),
        )
        reject_unsafe_surface_fields("probability event watchlist refresh priority input", self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventWatchlistRefreshPriorityRow:
    event_id: str
    watch_status: str
    source_age_hours: Decimal
    market_close_hours: Decimal
    edge_to_threshold_probability: Decimal
    liquidity_status: str
    memory_policy_status: str
    refresh_priority: str
    status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_member("watch_status", self.watch_status, WATCH_STATUSES)
        _require_member("liquidity_status", self.liquidity_status, LIQUIDITY_STATUSES)
        _require_member(
            "memory_policy_status",
            self.memory_policy_status,
            MEMORY_POLICY_STATUSES,
        )
        for field_name in (
            "source_age_hours",
            "market_close_hours",
            "edge_to_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_to_threshold_probability",
            _require_ratio(
                "edge_to_threshold_probability",
                self.edge_to_threshold_probability,
            ),
        )
        _require_member("refresh_priority", self.refresh_priority, REFRESH_PRIORITIES)
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        _validate_row(self)
        reject_unsafe_surface_fields("probability event watchlist refresh priority row", self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ProbabilityEventWatchlistRefreshPriorityReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    critical_count: Decimal
    high_count: Decimal
    medium_count: Decimal
    low_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ProbabilityEventWatchlistRefreshPriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "event_count",
            "critical_count",
            "high_count",
            "medium_count",
            "low_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("probability event watchlist refresh priority report", self)
        require_paper_only_flags("report", self)


def build_probability_event_watchlist_refresh_priority_report(
    inputs: Sequence[ProbabilityEventWatchlistRefreshPriorityInput],
    *,
    generated_at: datetime,
    config: ProbabilityEventWatchlistRefreshPriorityConfig | None = None,
) -> ProbabilityEventWatchlistRefreshPriorityReport:
    cfg = config or ProbabilityEventWatchlistRefreshPriorityConfig()
    if type(cfg) is not ProbabilityEventWatchlistRefreshPriorityConfig:
        raise ValueError("config must be a ProbabilityEventWatchlistRefreshPriorityConfig")
    require_paper_only_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=cfg) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return ProbabilityEventWatchlistRefreshPriorityReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_report_status(rows),
        event_count=_count(len(rows)),
        critical_count=_priority_count(rows, "critical"),
        high_count=_priority_count(rows, "high"),
        medium_count=_priority_count(rows, "medium"),
        low_count=_priority_count(rows, "low"),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def probability_event_watchlist_refresh_priority_report_payload(
    report: ProbabilityEventWatchlistRefreshPriorityReport | dict[str, Any],
) -> dict[str, Any]:
    label = "probability event watchlist refresh priority report"
    if type(report) is ProbabilityEventWatchlistRefreshPriorityReport:
        reject_unsafe_surface_fields(label, report)
        require_paper_only_flags("report", report)
        ready = json_ready_no_floats(report)
        if not isinstance(ready, dict):
            raise ValueError("report payload must be a JSON object")
        reject_unsafe_surface_fields(label, ready)
        return ready
    if isinstance(report, dict):
        _require_payload_flags(label, report)
        reject_unsafe_surface_fields(label, report)
        ready = json_ready_no_floats(report)
        if not isinstance(ready, dict):
            raise ValueError("report payload must be a JSON object")
        _require_payload_flags(label, ready)
        reject_unsafe_surface_fields(label, ready)
        return ready
    raise ValueError("report must be a ProbabilityEventWatchlistRefreshPriorityReport")


def _row_from_input(
    item: ProbabilityEventWatchlistRefreshPriorityInput,
    *,
    config: ProbabilityEventWatchlistRefreshPriorityConfig,
) -> ProbabilityEventWatchlistRefreshPriorityRow:
    reason_codes = _row_reason_codes(item, config=config)
    priority = _refresh_priority(reason_codes)
    return ProbabilityEventWatchlistRefreshPriorityRow(
        event_id=item.event_id,
        watch_status=item.watch_status,
        source_age_hours=item.source_age_hours,
        market_close_hours=item.market_close_hours,
        edge_to_threshold_probability=item.edge_to_threshold_probability,
        liquidity_status=item.liquidity_status,
        memory_policy_status=item.memory_policy_status,
        refresh_priority=priority,
        status=_status_from_priority(priority),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(priority),
    )


def _row_reason_codes(
    item: ProbabilityEventWatchlistRefreshPriorityInput,
    *,
    config: ProbabilityEventWatchlistRefreshPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.watch_status == "paused":
        reasons.append("watch_status_paused")
    elif item.watch_status == "candidate":
        reasons.append("watch_status_candidate")
    if item.liquidity_status == "blocked":
        reasons.append("liquidity_blocked")
    if item.memory_policy_status == "blocked":
        reasons.append("memory_policy_blocked")
    if item.source_age_hours >= config.source_overdue_hours:
        reasons.append("source_refresh_overdue")
    elif item.source_age_hours > config.source_stale_hours:
        reasons.append("source_refresh_stale")
    if item.market_close_hours <= config.market_close_imminent_hours:
        reasons.append("market_close_imminent")
    elif item.market_close_hours <= config.market_close_near_hours:
        reasons.append("market_close_near")
    if item.edge_to_threshold_probability <= config.edge_urgent_probability:
        reasons.append("edge_threshold_imminent")
    elif item.edge_to_threshold_probability <= config.edge_watch_probability:
        reasons.append("edge_threshold_near")
    if item.liquidity_status == "thin":
        reasons.append("liquidity_thin")
    if item.memory_policy_status == "refresh_due":
        reasons.append("memory_policy_refresh_due")
    if not reasons:
        reasons.append("watchlist_refresh_current")
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _refresh_priority(reason_codes: tuple[str, ...]) -> str:
    if "liquidity_blocked" in reason_codes or "memory_policy_blocked" in reason_codes:
        return "critical"
    if "market_close_imminent" in reason_codes and "edge_threshold_imminent" in reason_codes:
        return "critical"
    if "source_refresh_overdue" in reason_codes:
        return "high"
    if "liquidity_thin" in reason_codes and "edge_threshold_near" in reason_codes:
        return "high"
    if "watchlist_refresh_current" in reason_codes:
        return "low"
    return "medium"


def _manual_next_step(priority: str) -> str:
    if priority == "critical":
        return "paper_review_resolve_refresh_blockers"
    if priority == "high":
        return "paper_review_refresh_sources_today"
    if priority == "medium":
        return "paper_review_schedule_watchlist_refresh"
    return "paper_review_continue_watchlist_monitoring"


def _status_from_priority(priority: str) -> str:
    if priority == "critical":
        return "block"
    if priority in ("high", "medium"):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ProbabilityEventWatchlistRefreshPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ProbabilityEventWatchlistRefreshPriorityRow, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if not seen:
        seen.add("watchlist_refresh_current")
    if len(seen) > 1:
        seen.discard("watchlist_refresh_current")
    return tuple(reason for reason in REASON_CODES if reason in seen)


def _row_sort_key(row: ProbabilityEventWatchlistRefreshPriorityRow) -> tuple[Decimal, str]:
    return (-PRIORITY_RANK[row.refresh_priority], row.event_id)


def _priority_count(
    rows: tuple[ProbabilityEventWatchlistRefreshPriorityRow, ...],
    priority: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.refresh_priority == priority))


def _normalize_inputs(
    inputs: Sequence[ProbabilityEventWatchlistRefreshPriorityInput],
) -> tuple[ProbabilityEventWatchlistRefreshPriorityInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ProbabilityEventWatchlistRefreshPriorityInput] = []
    seen: set[str] = set()
    for item in inputs:
        if type(item) is not ProbabilityEventWatchlistRefreshPriorityInput:
            raise ValueError("inputs must contain ProbabilityEventWatchlistRefreshPriorityInput values")
        require_paper_only_flags("input", item)
        if item.event_id in seen:
            raise ValueError("duplicate event_id")
        seen.add(item.event_id)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.event_id))


def _normalize_rows(
    rows: object,
) -> tuple[ProbabilityEventWatchlistRefreshPriorityRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ProbabilityEventWatchlistRefreshPriorityRow:
            raise ValueError("rows must contain ProbabilityEventWatchlistRefreshPriorityRow values")
        require_paper_only_flags("row", row)
        if row.event_id in seen:
            raise ValueError("duplicate event_id")
        seen.add(row.event_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_config(config: ProbabilityEventWatchlistRefreshPriorityConfig) -> None:
    if config.source_stale_hours >= config.source_overdue_hours:
        raise ValueError("source_stale_hours must be less than source_overdue_hours")
    if config.market_close_imminent_hours > config.market_close_near_hours:
        raise ValueError("market_close_imminent_hours must not exceed market_close_near_hours")
    if config.edge_urgent_probability > config.edge_watch_probability:
        raise ValueError("edge_urgent_probability must not exceed edge_watch_probability")


def _validate_row(row: ProbabilityEventWatchlistRefreshPriorityRow) -> None:
    expected_priority = _refresh_priority(row.reason_codes)
    if row.refresh_priority != expected_priority:
        raise ValueError("refresh_priority must match reason_codes")
    if row.status != _status_from_priority(row.refresh_priority):
        raise ValueError("status must match refresh_priority")
    if row.manual_next_step != _manual_next_step(row.refresh_priority):
        raise ValueError("manual_next_step must match refresh_priority")
    if row.reason_codes == ("watchlist_refresh_current",) and row.refresh_priority != "low":
        raise ValueError("current rows must be low priority")


def _validate_report(report: ProbabilityEventWatchlistRefreshPriorityReport) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    for priority, field_name in (
        ("critical", "critical_count"),
        ("high", "high_count"),
        ("medium", "medium_count"),
        ("low", "low_count"),
    ):
        if getattr(report, field_name) != _priority_count(rows, priority):
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason in reason_codes:
        _require_member(field_name, reason, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in REASON_CODES if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    if "watchlist_refresh_current" in reason_codes and len(reason_codes) != 1:
        raise ValueError("watchlist_refresh_current must be alone")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in LOCAL_UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe live surface text")


__all__ = (
    "DEFAULT_PROBABILITY_EVENT_WATCHLIST_REFRESH_PRIORITY_CONFIG_VERSION",
    "LIQUIDITY_STATUSES",
    "MANUAL_NEXT_STEPS",
    "MEMORY_POLICY_STATUSES",
    "REASON_CODES",
    "REFRESH_PRIORITIES",
    "REPORT_STATUSES",
    "WATCH_STATUSES",
    "ProbabilityEventWatchlistRefreshPriorityConfig",
    "ProbabilityEventWatchlistRefreshPriorityInput",
    "ProbabilityEventWatchlistRefreshPriorityReport",
    "ProbabilityEventWatchlistRefreshPriorityRow",
    "build_probability_event_watchlist_refresh_priority_report",
    "probability_event_watchlist_refresh_priority_report_payload",
)
