"""Pure paper-only watchlist recheck cadence v10 decision module."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-watchlist-recheck-cadence-v10"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

WATCHLIST_TIERS = ("tier_1", "tier_2", "tier_3")
EDGE_STATUSES = ("actionable_edge", "monitoring_edge", "no_edge")
DATA_GAP_STATUSES = ("none", "minor_gap", "major_gap", "blocking_gap")
SOURCE_FRESHNESS_STATUSES = ("fresh", "aging", "stale")
CADENCE_STATUSES = (
    "recheck_now",
    "accelerated_recheck",
    "standard_recheck",
    "deferred_recheck",
)
REASON_CODES = (
    "actionable_edge",
    "blocking_data_gap",
    "cadence_standard",
    "capacity_constrained",
    "data_gap_major",
    "data_gap_minor",
    "large_market_move",
    "moderate_market_move",
    "monitoring_edge",
    "no_edge",
    "resolution_imminent",
    "resolution_near",
    "source_aging",
    "source_stale",
    "tier_1_watchlist",
    "tier_2_watchlist",
    "tier_3_watchlist",
)


@dataclass(frozen=True)
class StrategyWatchlistRecheckCadenceV10Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    tier_1_recheck_minutes: Decimal = Decimal("30.000000")
    tier_2_recheck_minutes: Decimal = Decimal("120.000000")
    tier_3_recheck_minutes: Decimal = Decimal("360.000000")
    moderate_market_move_bps: Decimal = Decimal("50.000000")
    large_market_move_bps: Decimal = Decimal("100.000000")
    near_resolution_minutes: Decimal = Decimal("360.000000")
    imminent_resolution_minutes: Decimal = Decimal("60.000000")
    low_capacity_score: Decimal = Decimal("0.250000")
    accelerated_multiplier: Decimal = Decimal("0.500000")
    deferred_multiplier: Decimal = Decimal("2.000000")
    min_recheck_minutes: Decimal = Decimal("5.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "tier_1_recheck_minutes",
            "tier_2_recheck_minutes",
            "tier_3_recheck_minutes",
            "moderate_market_move_bps",
            "large_market_move_bps",
            "near_resolution_minutes",
            "imminent_resolution_minutes",
            "low_capacity_score",
            "accelerated_multiplier",
            "deferred_multiplier",
            "min_recheck_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.moderate_market_move_bps >= self.large_market_move_bps:
            raise ValueError("large_market_move_bps must exceed moderate_market_move_bps")
        if self.imminent_resolution_minutes >= self.near_resolution_minutes:
            raise ValueError("near_resolution_minutes must exceed imminent_resolution_minutes")
        if self.low_capacity_score > ONE:
            raise ValueError("low_capacity_score must be between 0.000000 and 1.000000")
        if self.accelerated_multiplier >= ONE:
            raise ValueError("accelerated_multiplier must be below 1.000000")
        if self.deferred_multiplier <= ONE:
            raise ValueError("deferred_multiplier must exceed 1.000000")
        reject_unsafe_surface_fields("watchlist recheck cadence v10 config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyWatchlistRecheckCadenceV10Input:
    market_id: str
    watchlist_tier: str
    edge_status: str
    data_gap_status: str
    market_move_bps: Decimal
    source_freshness_status: str
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_member("watchlist_tier", self.watchlist_tier, WATCHLIST_TIERS)
        _require_member("edge_status", self.edge_status, EDGE_STATUSES)
        _require_member("data_gap_status", self.data_gap_status, DATA_GAP_STATUSES)
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_FRESHNESS_STATUSES,
        )
        for field_name in (
            "market_move_bps",
            "time_to_resolution_minutes",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.team_capacity_score > ONE:
            raise ValueError("team_capacity_score must be between 0.000000 and 1.000000")
        reject_unsafe_surface_fields("watchlist recheck cadence v10 input", self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class StrategyWatchlistRecheckCadenceV10Decision:
    config_version: str
    market_id: str
    watchlist_tier: str
    edge_status: str
    data_gap_status: str
    market_move_bps: Decimal
    source_freshness_status: str
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    base_recheck_minutes: Decimal
    cadence_status: str
    next_recheck_minutes: Decimal
    recheck_reason: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_id", self.market_id)
        _require_member("watchlist_tier", self.watchlist_tier, WATCHLIST_TIERS)
        _require_member("edge_status", self.edge_status, EDGE_STATUSES)
        _require_member("data_gap_status", self.data_gap_status, DATA_GAP_STATUSES)
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_FRESHNESS_STATUSES,
        )
        _require_member("cadence_status", self.cadence_status, CADENCE_STATUSES)
        _require_canonical_string("recheck_reason", self.recheck_reason)
        for field_name in (
            "market_move_bps",
            "time_to_resolution_minutes",
            "team_capacity_score",
            "base_recheck_minutes",
            "next_recheck_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.team_capacity_score > ONE:
            raise ValueError("team_capacity_score must be between 0.000000 and 1.000000")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields("watchlist recheck cadence v10 decision", self)
        require_paper_only_flags("decision", self)
        _validate_decision(self)


def build_strategy_watchlist_recheck_cadence_v10_decision(
    watchlist_market: StrategyWatchlistRecheckCadenceV10Input,
    *,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> StrategyWatchlistRecheckCadenceV10Decision:
    if type(watchlist_market) is not StrategyWatchlistRecheckCadenceV10Input:
        raise ValueError("watchlist_market must be a StrategyWatchlistRecheckCadenceV10Input")
    if type(config) is not StrategyWatchlistRecheckCadenceV10Config:
        raise ValueError("config must be a StrategyWatchlistRecheckCadenceV10Config")
    require_paper_only_flags("input", watchlist_market)
    require_paper_only_flags("config", config)
    base_recheck_minutes = _base_recheck_minutes(watchlist_market.watchlist_tier, config)
    cadence_status = _cadence_status(watchlist_market, config)
    reason_codes = _decision_reason_codes(watchlist_market, cadence_status, config)
    next_recheck_minutes = _next_recheck_minutes(
        cadence_status=cadence_status,
        base_recheck_minutes=base_recheck_minutes,
        config=config,
    )

    return StrategyWatchlistRecheckCadenceV10Decision(
        config_version=config.config_version,
        market_id=watchlist_market.market_id,
        watchlist_tier=watchlist_market.watchlist_tier,
        edge_status=watchlist_market.edge_status,
        data_gap_status=watchlist_market.data_gap_status,
        market_move_bps=watchlist_market.market_move_bps,
        source_freshness_status=watchlist_market.source_freshness_status,
        time_to_resolution_minutes=watchlist_market.time_to_resolution_minutes,
        team_capacity_score=watchlist_market.team_capacity_score,
        base_recheck_minutes=base_recheck_minutes,
        cadence_status=cadence_status,
        next_recheck_minutes=next_recheck_minutes,
        recheck_reason=_recheck_reason(cadence_status, reason_codes),
        reason_codes=reason_codes,
    )


def strategy_watchlist_recheck_cadence_v10_payload(
    decision: StrategyWatchlistRecheckCadenceV10Decision,
) -> dict[str, Any]:
    if type(decision) is not StrategyWatchlistRecheckCadenceV10Decision:
        raise ValueError("decision must be a StrategyWatchlistRecheckCadenceV10Decision")
    require_paper_only_flags("decision", decision)
    reject_unsafe_surface_fields("watchlist recheck cadence v10 decision", decision)
    payload = json_ready_no_floats(decision)
    if not isinstance(payload, dict):
        raise ValueError("decision payload must be a JSON object")
    reject_unsafe_surface_fields("watchlist recheck cadence v10 payload", payload)
    return payload


def _base_recheck_minutes(
    watchlist_tier: str,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> Decimal:
    if watchlist_tier == "tier_1":
        return config.tier_1_recheck_minutes
    if watchlist_tier == "tier_2":
        return config.tier_2_recheck_minutes
    return config.tier_3_recheck_minutes


def _cadence_status(
    row: StrategyWatchlistRecheckCadenceV10Input,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> str:
    if _immediate_reason_codes(row, config):
        return "recheck_now"
    if _accelerated_reason_codes(row, config):
        return "accelerated_recheck"
    if row.team_capacity_score <= config.low_capacity_score:
        return "deferred_recheck"
    return "standard_recheck"


def _decision_reason_codes(
    row: StrategyWatchlistRecheckCadenceV10Input,
    cadence_status: str,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> tuple[str, ...]:
    codes = {
        _tier_reason_code(row.watchlist_tier),
        row.edge_status,
    }
    codes.update(_immediate_reason_codes(row, config))
    if cadence_status == "accelerated_recheck":
        codes.update(_accelerated_reason_codes(row, config))
    elif cadence_status == "deferred_recheck":
        codes.add("capacity_constrained")
    elif cadence_status == "standard_recheck":
        codes.add("cadence_standard")
    if row.data_gap_status == "minor_gap":
        codes.add("data_gap_minor")
    return tuple(sorted(codes))


def _immediate_reason_codes(
    row: StrategyWatchlistRecheckCadenceV10Input,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if row.data_gap_status == "blocking_gap":
        codes.append("blocking_data_gap")
    if row.market_move_bps >= config.large_market_move_bps:
        codes.append("large_market_move")
    if row.source_freshness_status == "stale":
        codes.append("source_stale")
    if row.time_to_resolution_minutes <= config.imminent_resolution_minutes:
        codes.append("resolution_imminent")
    return tuple(codes)


def _accelerated_reason_codes(
    row: StrategyWatchlistRecheckCadenceV10Input,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if row.data_gap_status == "major_gap":
        codes.append("data_gap_major")
    if row.market_move_bps >= config.moderate_market_move_bps:
        codes.append("moderate_market_move")
    if row.source_freshness_status == "aging":
        codes.append("source_aging")
    if row.time_to_resolution_minutes <= config.near_resolution_minutes:
        codes.append("resolution_near")
    return tuple(codes)


def _tier_reason_code(watchlist_tier: str) -> str:
    return f"{watchlist_tier}_watchlist"


def _next_recheck_minutes(
    *,
    cadence_status: str,
    base_recheck_minutes: Decimal,
    config: StrategyWatchlistRecheckCadenceV10Config,
) -> Decimal:
    if cadence_status == "recheck_now":
        return ZERO
    if cadence_status == "accelerated_recheck":
        return max(
            config.min_recheck_minutes,
            _multiply_decimal(base_recheck_minutes, config.accelerated_multiplier),
        )
    if cadence_status == "deferred_recheck":
        return _multiply_decimal(base_recheck_minutes, config.deferred_multiplier)
    return base_recheck_minutes


def _recheck_reason(cadence_status: str, reason_codes: tuple[str, ...]) -> str:
    if cadence_status == "recheck_now":
        labels = _trigger_labels(
            reason_codes,
            (
                "blocking_data_gap",
                "large_market_move",
                "source_stale",
                "resolution_imminent",
            ),
        )
        return f"Immediate recheck required: {_join_labels(labels)}."
    if cadence_status == "accelerated_recheck":
        labels = _trigger_labels(
            reason_codes,
            (
                "data_gap_major",
                "moderate_market_move",
                "source_aging",
                "resolution_near",
                "actionable_edge",
            ),
        )
        return f"Accelerated recheck scheduled: {_join_labels(labels)}."
    if cadence_status == "deferred_recheck":
        return "Recheck deferred because team capacity is constrained."
    return "Standard recheck cadence applies."


def _trigger_labels(
    reason_codes: tuple[str, ...],
    ordered_codes: tuple[str, ...],
) -> tuple[str, ...]:
    labels = tuple(_reason_label(code) for code in ordered_codes if code in reason_codes)
    if not labels:
        raise ValueError("reason_codes must contain a cadence trigger")
    return labels


def _reason_label(reason_code: str) -> str:
    labels = {
        "actionable_edge": "actionable edge",
        "blocking_data_gap": "blocking data gap",
        "data_gap_major": "major data gap",
        "large_market_move": "large market move",
        "moderate_market_move": "moderate market move",
        "resolution_imminent": "imminent resolution",
        "resolution_near": "near resolution",
        "source_aging": "aging source",
        "source_stale": "stale source",
    }
    return labels[reason_code]


def _join_labels(labels: tuple[str, ...]) -> str:
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return f"{', '.join(labels[:-1])}, and {labels[-1]}"


def _validate_decision(decision: StrategyWatchlistRecheckCadenceV10Decision) -> None:
    if decision.next_recheck_minutes == ZERO and decision.cadence_status != "recheck_now":
        raise ValueError("next_recheck_minutes must be positive unless recheck_now")
    if decision.cadence_status == "recheck_now" and decision.next_recheck_minutes != ZERO:
        raise ValueError("next_recheck_minutes must be zero for recheck_now")
    if decision.cadence_status == "standard_recheck":
        if decision.next_recheck_minutes != decision.base_recheck_minutes:
            raise ValueError("next_recheck_minutes must match base cadence")
    if decision.cadence_status == "accelerated_recheck":
        if decision.next_recheck_minutes >= decision.base_recheck_minutes:
            raise ValueError("next_recheck_minutes must be below base cadence")
        _require_any_reason_code(
            decision.reason_codes,
            (
                "actionable_edge",
                "data_gap_major",
                "moderate_market_move",
                "source_aging",
                "resolution_near",
            ),
        )
    if decision.cadence_status == "deferred_recheck":
        if decision.next_recheck_minutes <= decision.base_recheck_minutes:
            raise ValueError("next_recheck_minutes must exceed base cadence")
        if "capacity_constrained" not in decision.reason_codes:
            raise ValueError("reason_codes must include capacity_constrained")
    if _tier_reason_code(decision.watchlist_tier) not in decision.reason_codes:
        raise ValueError("reason_codes must include watchlist tier")
    if decision.edge_status not in decision.reason_codes:
        raise ValueError("reason_codes must include edge status")
    if decision.cadence_status == "standard_recheck" and "cadence_standard" not in decision.reason_codes:
        raise ValueError("reason_codes must include cadence_standard")
    if decision.recheck_reason != _recheck_reason(decision.cadence_status, decision.reason_codes):
        raise ValueError("recheck_reason must match cadence diagnostics")


def _require_any_reason_code(
    reason_codes: tuple[str, ...],
    expected_codes: tuple[str, ...],
) -> None:
    if not any(reason_code in reason_codes for reason_code in expected_codes):
        raise ValueError("reason_codes must include an accelerated trigger")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be sorted")
    return reason_codes


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANT)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyWatchlistRecheckCadenceV10Config",
    "StrategyWatchlistRecheckCadenceV10Decision",
    "StrategyWatchlistRecheckCadenceV10Input",
    "build_strategy_watchlist_recheck_cadence_v10_decision",
    "strategy_watchlist_recheck_cadence_v10_payload",
)
