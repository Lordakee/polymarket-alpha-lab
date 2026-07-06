"""Pure read-only market narrative shift v10 report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-market-narrative-shift-v10"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SHIFT_STATUSES = ("stable", "emerging_shift", "confirmed_shift")
UPDATE_URGENCIES = ("none", "elevated", "immediate")
RESEARCH_ACTIONS = (
    "no_action",
    "refresh_narrative_research",
    "escalate_primary_source_review",
)
STATUS_URGENCY = {
    "stable": "none",
    "emerging_shift": "elevated",
    "confirmed_shift": "immediate",
}
STATUS_ACTION = {
    "stable": "no_action",
    "emerging_shift": "refresh_narrative_research",
    "confirmed_shift": "escalate_primary_source_review",
}

STABLE_REASON_CODE = "market_narrative_shift_v10_stable"
CONSENSUS_URGENT_REASON = "consensus_probability_move_urgent"
SOURCE_COUNT_URGENT_REASON = "source_count_change_urgent"
FRESH_PRIMARY_URGENT_REASON = "fresh_primary_sources_urgent"
PRICE_MOVE_URGENT_REASON = "market_price_move_urgent"
CONFLICT_URGENT_REASON = "conflict_delta_urgent"
IMMEDIATE_WINDOW_URGENT_REASON = "immediate_time_window_urgent"
CONSENSUS_WATCH_REASON = "consensus_probability_move_watch"
SOURCE_COUNT_WATCH_REASON = "source_count_change_watch"
FRESH_PRIMARY_WATCH_REASON = "fresh_primary_sources_watch"
PRICE_MOVE_WATCH_REASON = "market_price_move_watch"
CONFLICT_WATCH_REASON = "conflict_delta_watch"
RAPID_WINDOW_WATCH_REASON = "rapid_time_window_watch"

URGENT_REASON_CODES = frozenset(
    (
        CONSENSUS_URGENT_REASON,
        SOURCE_COUNT_URGENT_REASON,
        FRESH_PRIMARY_URGENT_REASON,
        PRICE_MOVE_URGENT_REASON,
        CONFLICT_URGENT_REASON,
        IMMEDIATE_WINDOW_URGENT_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        CONSENSUS_WATCH_REASON,
        SOURCE_COUNT_WATCH_REASON,
        FRESH_PRIMARY_WATCH_REASON,
        PRICE_MOVE_WATCH_REASON,
        CONFLICT_WATCH_REASON,
        RAPID_WINDOW_WATCH_REASON,
    ),
)
REASON_PRIORITY = (
    CONSENSUS_URGENT_REASON,
    SOURCE_COUNT_URGENT_REASON,
    FRESH_PRIMARY_URGENT_REASON,
    PRICE_MOVE_URGENT_REASON,
    CONFLICT_URGENT_REASON,
    IMMEDIATE_WINDOW_URGENT_REASON,
    CONSENSUS_WATCH_REASON,
    SOURCE_COUNT_WATCH_REASON,
    FRESH_PRIMARY_WATCH_REASON,
    PRICE_MOVE_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    RAPID_WINDOW_WATCH_REASON,
    STABLE_REASON_CODE,
)


@dataclass(frozen=True)
class StrategyMarketNarrativeShiftV10Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_consensus_probability_move: Decimal = Decimal("0.030000")
    urgent_consensus_probability_move: Decimal = Decimal("0.080000")
    watch_source_count_change: Decimal = Decimal("2.000000")
    urgent_source_count_change: Decimal = Decimal("5.000000")
    watch_fresh_primary_source_count: Decimal = Decimal("1.000000")
    urgent_fresh_primary_source_count: Decimal = Decimal("3.000000")
    watch_market_price_move: Decimal = Decimal("0.020000")
    urgent_market_price_move: Decimal = Decimal("0.060000")
    watch_conflict_delta: Decimal = Decimal("0.150000")
    urgent_conflict_delta: Decimal = Decimal("0.400000")
    rapid_time_window_minutes: Decimal = Decimal("60.000000")
    immediate_time_window_minutes: Decimal = Decimal("15.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_consensus_probability_move",
            "urgent_consensus_probability_move",
            "watch_market_price_move",
            "urgent_market_price_move",
            "watch_conflict_delta",
            "urgent_conflict_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_count_change",
            "urgent_source_count_change",
            "watch_fresh_primary_source_count",
            "urgent_fresh_primary_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("rapid_time_window_minutes", "immediate_time_window_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending_threshold(
            "urgent_consensus_probability_move",
            self.watch_consensus_probability_move,
            self.urgent_consensus_probability_move,
        )
        _require_ascending_threshold(
            "urgent_source_count_change",
            self.watch_source_count_change,
            self.urgent_source_count_change,
        )
        _require_ascending_threshold(
            "urgent_fresh_primary_source_count",
            self.watch_fresh_primary_source_count,
            self.urgent_fresh_primary_source_count,
        )
        _require_ascending_threshold(
            "urgent_market_price_move",
            self.watch_market_price_move,
            self.urgent_market_price_move,
        )
        _require_ascending_threshold(
            "urgent_conflict_delta",
            self.watch_conflict_delta,
            self.urgent_conflict_delta,
        )
        _require_descending_threshold(
            "immediate_time_window_minutes",
            self.rapid_time_window_minutes,
            self.immediate_time_window_minutes,
        )
        reject_unsafe_surface_fields("strategy market narrative shift v10 config", self)
        require_paper_only_flags("strategy market narrative shift v10 config", self)


@dataclass(frozen=True)
class StrategyMarketNarrativeShiftV10Input:
    previous_consensus_probability: Decimal
    current_consensus_probability: Decimal
    source_count_change: Decimal
    fresh_primary_source_count: Decimal
    market_price_move: Decimal
    time_window_minutes: Decimal
    conflict_delta: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "previous_consensus_probability",
            "current_consensus_probability",
            "conflict_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count_change",
            _normalize_signed_whole_decimal("source_count_change", self.source_count_change),
        )
        object.__setattr__(
            self,
            "fresh_primary_source_count",
            _normalize_nonnegative_whole_decimal(
                "fresh_primary_source_count",
                self.fresh_primary_source_count,
            ),
        )
        object.__setattr__(
            self,
            "market_price_move",
            _normalize_signed_probability_move("market_price_move", self.market_price_move),
        )
        object.__setattr__(
            self,
            "time_window_minutes",
            _normalize_positive_decimal("time_window_minutes", self.time_window_minutes),
        )
        reject_unsafe_surface_fields("strategy market narrative shift v10 input", self)
        require_paper_only_flags("strategy market narrative shift v10 input", self)


@dataclass(frozen=True)
class StrategyMarketNarrativeShiftV10Report:
    generated_at: datetime
    config_version: str
    previous_consensus_probability: Decimal
    current_consensus_probability: Decimal
    consensus_probability_move: Decimal
    source_count_change: Decimal
    source_count_change_magnitude: Decimal
    fresh_primary_source_count: Decimal
    market_price_move: Decimal
    market_price_move_magnitude: Decimal
    time_window_minutes: Decimal
    conflict_delta: Decimal
    shift_status: str
    update_urgency: str
    research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "previous_consensus_probability",
            "current_consensus_probability",
            "consensus_probability_move",
            "conflict_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count_change",
            _normalize_signed_whole_decimal("source_count_change", self.source_count_change),
        )
        object.__setattr__(
            self,
            "source_count_change_magnitude",
            _normalize_nonnegative_whole_decimal(
                "source_count_change_magnitude",
                self.source_count_change_magnitude,
            ),
        )
        object.__setattr__(
            self,
            "fresh_primary_source_count",
            _normalize_nonnegative_whole_decimal(
                "fresh_primary_source_count",
                self.fresh_primary_source_count,
            ),
        )
        object.__setattr__(
            self,
            "market_price_move",
            _normalize_signed_probability_move("market_price_move", self.market_price_move),
        )
        object.__setattr__(
            self,
            "market_price_move_magnitude",
            _normalize_probability("market_price_move_magnitude", self.market_price_move_magnitude),
        )
        object.__setattr__(
            self,
            "time_window_minutes",
            _normalize_positive_decimal("time_window_minutes", self.time_window_minutes),
        )
        _require_member("shift_status", self.shift_status, SHIFT_STATUSES)
        _require_member("update_urgency", self.update_urgency, UPDATE_URGENCIES)
        _require_member("research_action", self.research_action, RESEARCH_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("strategy market narrative shift v10 report", self)
        require_paper_only_flags("strategy market narrative shift v10 report", self)


def build_strategy_market_narrative_shift_v10_report(
    input_value: StrategyMarketNarrativeShiftV10Input,
    *,
    config: StrategyMarketNarrativeShiftV10Config,
    generated_at: datetime,
) -> StrategyMarketNarrativeShiftV10Report:
    if type(input_value) is not StrategyMarketNarrativeShiftV10Input:
        raise ValueError("input_value must be a StrategyMarketNarrativeShiftV10Input")
    if type(config) is not StrategyMarketNarrativeShiftV10Config:
        raise ValueError("config must be a StrategyMarketNarrativeShiftV10Config")
    require_paper_only_flags("strategy market narrative shift v10 input", input_value)
    require_paper_only_flags("strategy market narrative shift v10 config", config)

    consensus_probability_move = _absolute_difference(
        input_value.current_consensus_probability,
        input_value.previous_consensus_probability,
    )
    source_count_change_magnitude = _absolute_value(input_value.source_count_change)
    market_price_move_magnitude = _absolute_value(input_value.market_price_move)
    reason_codes = _reason_codes(
        input_value,
        config,
        consensus_probability_move=consensus_probability_move,
        source_count_change_magnitude=source_count_change_magnitude,
        market_price_move_magnitude=market_price_move_magnitude,
    )
    shift_status = _shift_status(reason_codes)
    return StrategyMarketNarrativeShiftV10Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        previous_consensus_probability=input_value.previous_consensus_probability,
        current_consensus_probability=input_value.current_consensus_probability,
        consensus_probability_move=consensus_probability_move,
        source_count_change=input_value.source_count_change,
        source_count_change_magnitude=source_count_change_magnitude,
        fresh_primary_source_count=input_value.fresh_primary_source_count,
        market_price_move=input_value.market_price_move,
        market_price_move_magnitude=market_price_move_magnitude,
        time_window_minutes=input_value.time_window_minutes,
        conflict_delta=input_value.conflict_delta,
        shift_status=shift_status,
        update_urgency=STATUS_URGENCY[shift_status],
        research_action=STATUS_ACTION[shift_status],
        reason_codes=reason_codes,
    )


def strategy_market_narrative_shift_v10_payload(
    report: StrategyMarketNarrativeShiftV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketNarrativeShiftV10Report:
        raise ValueError("report must be a StrategyMarketNarrativeShiftV10Report")
    require_paper_only_flags("strategy market narrative shift v10 report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("strategy market narrative shift v10 payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _reason_codes(
    input_value: StrategyMarketNarrativeShiftV10Input,
    config: StrategyMarketNarrativeShiftV10Config,
    *,
    consensus_probability_move: Decimal,
    source_count_change_magnitude: Decimal,
    market_price_move_magnitude: Decimal,
) -> tuple[str, ...]:
    urgent_codes: list[str] = []
    _append_threshold_reason(
        urgent_codes,
        consensus_probability_move,
        config.urgent_consensus_probability_move,
        CONSENSUS_URGENT_REASON,
    )
    _append_threshold_reason(
        urgent_codes,
        source_count_change_magnitude,
        config.urgent_source_count_change,
        SOURCE_COUNT_URGENT_REASON,
    )
    _append_threshold_reason(
        urgent_codes,
        input_value.fresh_primary_source_count,
        config.urgent_fresh_primary_source_count,
        FRESH_PRIMARY_URGENT_REASON,
    )
    _append_threshold_reason(
        urgent_codes,
        market_price_move_magnitude,
        config.urgent_market_price_move,
        PRICE_MOVE_URGENT_REASON,
    )
    _append_threshold_reason(
        urgent_codes,
        input_value.conflict_delta,
        config.urgent_conflict_delta,
        CONFLICT_URGENT_REASON,
    )
    if urgent_codes:
        if input_value.time_window_minutes <= config.immediate_time_window_minutes:
            urgent_codes.append(IMMEDIATE_WINDOW_URGENT_REASON)
        return _normalize_reason_codes("reason_codes", tuple(urgent_codes))

    watch_codes: list[str] = []
    _append_threshold_reason(
        watch_codes,
        consensus_probability_move,
        config.watch_consensus_probability_move,
        CONSENSUS_WATCH_REASON,
    )
    _append_threshold_reason(
        watch_codes,
        source_count_change_magnitude,
        config.watch_source_count_change,
        SOURCE_COUNT_WATCH_REASON,
    )
    _append_threshold_reason(
        watch_codes,
        input_value.fresh_primary_source_count,
        config.watch_fresh_primary_source_count,
        FRESH_PRIMARY_WATCH_REASON,
    )
    _append_threshold_reason(
        watch_codes,
        market_price_move_magnitude,
        config.watch_market_price_move,
        PRICE_MOVE_WATCH_REASON,
    )
    _append_threshold_reason(
        watch_codes,
        input_value.conflict_delta,
        config.watch_conflict_delta,
        CONFLICT_WATCH_REASON,
    )
    if watch_codes:
        if input_value.time_window_minutes <= config.rapid_time_window_minutes:
            watch_codes.append(RAPID_WINDOW_WATCH_REASON)
        return _normalize_reason_codes("reason_codes", tuple(watch_codes))
    return (STABLE_REASON_CODE,)


def _append_threshold_reason(
    codes: list[str],
    value: Decimal,
    threshold: Decimal,
    reason_code: str,
) -> None:
    if value >= threshold:
        codes.append(reason_code)


def _shift_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in URGENT_REASON_CODES for reason_code in reason_codes):
        return "confirmed_shift"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "emerging_shift"
    return "stable"


def _validate_report(report: StrategyMarketNarrativeShiftV10Report) -> None:
    if report.consensus_probability_move != _absolute_difference(
        report.current_consensus_probability,
        report.previous_consensus_probability,
    ):
        raise ValueError(
            "consensus_probability_move must match current_consensus_probability "
            "and previous_consensus_probability",
        )
    if report.source_count_change_magnitude != _absolute_value(report.source_count_change):
        raise ValueError("source_count_change_magnitude must match source_count_change")
    if report.market_price_move_magnitude != _absolute_value(report.market_price_move):
        raise ValueError("market_price_move_magnitude must match market_price_move")
    expected_shift_status = _shift_status(report.reason_codes)
    if report.shift_status != expected_shift_status:
        raise ValueError("shift_status must match reason_codes")
    if report.update_urgency != STATUS_URGENCY[report.shift_status]:
        raise ValueError("update_urgency must match shift_status")
    if report.research_action != STATUS_ACTION[report.shift_status]:
        raise ValueError("research_action must match shift_status")
    if report.shift_status == "stable" and report.reason_codes != (STABLE_REASON_CODE,):
        raise ValueError("stable report must include only the stable reason")
    if report.shift_status != "stable" and STABLE_REASON_CODE in report.reason_codes:
        raise ValueError("non-stable report must not include stable reason")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code not in REASON_PRIORITY:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in REASON_PRIORITY if reason_code in seen)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part.lower() != part:
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _absolute_difference(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return _quantize(left - right)
    return _quantize(right - left)


def _absolute_value(value: Decimal) -> Decimal:
    if value >= ZERO:
        return _quantize(value)
    return _quantize(-value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_signed_probability_move(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _normalize_signed_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_signed_whole_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_ascending_threshold(
    field_name: str,
    watch_value: Decimal,
    urgent_value: Decimal,
) -> None:
    if urgent_value < watch_value:
        raise ValueError(f"{field_name} must be at least watch threshold")


def _require_descending_threshold(
    field_name: str,
    watch_value: Decimal,
    urgent_value: Decimal,
) -> None:
    if urgent_value > watch_value:
        raise ValueError(f"{field_name} must not exceed watch threshold")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyMarketNarrativeShiftV10Config",
    "StrategyMarketNarrativeShiftV10Input",
    "StrategyMarketNarrativeShiftV10Report",
    "build_strategy_market_narrative_shift_v10_report",
    "strategy_market_narrative_shift_v10_payload",
)
