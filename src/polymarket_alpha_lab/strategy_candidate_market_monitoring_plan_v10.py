"""Candidate market monitoring plan."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

DEFAULT_STRATEGY_CANDIDATE_MARKET_MONITORING_PLAN_V10_CONFIG_VERSION = (
    "strategy-candidate-market-monitoring-plan-v10"
)

CANDIDATE_STATUSES = ("accepted", "researching", "paused", "blocked", "rejected")
WATCHLIST_TIERS = ("tier_1", "tier_2", "tier_3", "none")
EDGE_STATUSES = ("positive", "flat", "weakening", "negative")
SOURCE_REFRESH_STATUSES = ("fresh", "stale", "blocked")
MONITORING_STATUSES = ("monitor", "watch", "blocked")

MONITOR_ACTION = "continue_readonly_monitoring"
BLOCKED_SUFFIX = "_blocked"
WATCH_SUFFIX = "_watch"

BAD_TEXT_FRAGMENTS = (
    "li" "ve",
    "trad" "ing",
    "au" "th",
    "wal" "let",
    "or" "der",
    "si" "gn",
    "private" "_" "key",
    "bro" "ker",
    "data" "base",
    "per" "sist",
    "net" "work",
)


@dataclass(frozen=True)
class StrategyCandidateMarketMonitoringPlanV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_MARKET_MONITORING_PLAN_V10_CONFIG_VERSION
    )
    tier_1_review_minutes: Decimal = Decimal("240.000000")
    tier_2_review_minutes: Decimal = Decimal("720.000000")
    tier_3_review_minutes: Decimal = Decimal("1440.000000")
    watch_review_minutes: Decimal = Decimal("60.000000")
    urgent_review_minutes: Decimal = Decimal("30.000000")
    blocked_review_minutes: Decimal = Decimal("1440.000000")
    near_resolution_minutes: Decimal = Decimal("180.000000")
    minimum_resolution_minutes: Decimal = Decimal("30.000000")
    watch_team_capacity_score: Decimal = Decimal("0.500000")
    minimum_team_capacity_score: Decimal = Decimal("0.250000")
    watch_market_move_bps: Decimal = Decimal("75.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "tier_1_review_minutes",
            "tier_2_review_minutes",
            "tier_3_review_minutes",
            "watch_review_minutes",
            "urgent_review_minutes",
            "blocked_review_minutes",
            "near_resolution_minutes",
            "minimum_resolution_minutes",
            "watch_market_move_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_team_capacity_score",
            "minimum_team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if not (
            self.urgent_review_minutes
            <= self.watch_review_minutes
            <= self.tier_1_review_minutes
            <= self.tier_2_review_minutes
            <= self.tier_3_review_minutes
            <= self.blocked_review_minutes
        ):
            raise ValueError("review cadence thresholds must ascend through base tiers")
        if not self.minimum_resolution_minutes <= self.near_resolution_minutes:
            raise ValueError("resolution thresholds must ascend")
        if not self.minimum_team_capacity_score <= self.watch_team_capacity_score:
            raise ValueError("team capacity thresholds must ascend")
        reject_unsafe_surface_fields("candidate market monitoring config", self)
        require_paper_only_flags("candidate market monitoring config", self)


@dataclass(frozen=True)
class StrategyCandidateMarketMonitoringPlanV10Input:
    market_id: str
    candidate_status: str
    watchlist_tier: str
    edge_status: str
    source_refresh_status: str
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    market_move_bps: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("market_id", self.market_id)
        _require_member("candidate_status", self.candidate_status, CANDIDATE_STATUSES)
        _require_member("watchlist_tier", self.watchlist_tier, WATCHLIST_TIERS)
        _require_member("edge_status", self.edge_status, EDGE_STATUSES)
        _require_member(
            "source_refresh_status",
            self.source_refresh_status,
            SOURCE_REFRESH_STATUSES,
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_ratio("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_decimal("market_move_bps", self.market_move_bps),
        )
        reject_unsafe_surface_fields("candidate market monitoring input", self)
        require_paper_only_flags("candidate market monitoring input", self)


@dataclass(frozen=True)
class StrategyCandidateMarketMonitoringPlanV10Payload:
    config_version: str
    market_id: str
    candidate_status: str
    watchlist_tier: str
    edge_status: str
    source_refresh_status: str
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    market_move_bps: Decimal
    absolute_market_move_bps: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        _require_public_text("market_id", self.market_id)
        _require_member("candidate_status", self.candidate_status, CANDIDATE_STATUSES)
        _require_member("watchlist_tier", self.watchlist_tier, WATCHLIST_TIERS)
        _require_member("edge_status", self.edge_status, EDGE_STATUSES)
        _require_member(
            "source_refresh_status",
            self.source_refresh_status,
            SOURCE_REFRESH_STATUSES,
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_ratio("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_decimal("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "absolute_market_move_bps",
            _normalize_nonnegative_decimal(
                "absolute_market_move_bps",
                self.absolute_market_move_bps,
            ),
        )
        if self.absolute_market_move_bps != abs(self.market_move_bps):
            raise ValueError("absolute_market_move_bps must match market_move_bps")
        reject_unsafe_surface_fields("candidate market monitoring payload", self)
        require_paper_only_flags("candidate market monitoring payload", self)


@dataclass(frozen=True)
class StrategyCandidateMarketMonitoringPlanV10Result:
    monitoring_status: str
    monitoring_actions: tuple[str, ...]
    next_review_minutes: Decimal
    reason_codes: tuple[str, ...]
    payload: StrategyCandidateMarketMonitoringPlanV10Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("monitoring_status", self.monitoring_status, MONITORING_STATUSES)
        object.__setattr__(
            self,
            "monitoring_actions",
            _normalize_string_tuple("monitoring_actions", self.monitoring_actions),
        )
        object.__setattr__(
            self,
            "next_review_minutes",
            _normalize_nonnegative_decimal(
                "next_review_minutes",
                self.next_review_minutes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        if type(self.payload) is not StrategyCandidateMarketMonitoringPlanV10Payload:
            raise ValueError(
                "payload must be a StrategyCandidateMarketMonitoringPlanV10Payload",
            )
        require_paper_only_flags("candidate market monitoring payload", self.payload)
        if self.monitoring_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("monitoring_status must match reason_codes")
        if self.monitoring_status == "monitor" and self.monitoring_actions != (
            MONITOR_ACTION,
        ):
            raise ValueError("monitoring_actions must match monitoring_status")
        reject_unsafe_surface_fields("candidate market monitoring result", self)
        require_paper_only_flags("candidate market monitoring result", self)

    @property
    def payload_json(self) -> dict[str, Any]:
        return strategy_candidate_market_monitoring_plan_v10_payload(self)


def build_strategy_candidate_market_monitoring_plan_v10_result(
    candidate: StrategyCandidateMarketMonitoringPlanV10Input,
    *,
    config: StrategyCandidateMarketMonitoringPlanV10Config,
) -> StrategyCandidateMarketMonitoringPlanV10Result:
    if type(candidate) is not StrategyCandidateMarketMonitoringPlanV10Input:
        raise ValueError(
            "candidate must be a StrategyCandidateMarketMonitoringPlanV10Input",
        )
    if type(config) is not StrategyCandidateMarketMonitoringPlanV10Config:
        raise ValueError(
            "config must be a StrategyCandidateMarketMonitoringPlanV10Config",
        )
    reject_unsafe_surface_fields("candidate market monitoring input", candidate)
    require_paper_only_flags("candidate market monitoring input", candidate)
    reject_unsafe_surface_fields("candidate market monitoring config", config)
    require_paper_only_flags("candidate market monitoring config", config)

    payload = StrategyCandidateMarketMonitoringPlanV10Payload(
        config_version=config.config_version,
        market_id=candidate.market_id,
        candidate_status=candidate.candidate_status,
        watchlist_tier=candidate.watchlist_tier,
        edge_status=candidate.edge_status,
        source_refresh_status=candidate.source_refresh_status,
        time_to_resolution_minutes=candidate.time_to_resolution_minutes,
        team_capacity_score=candidate.team_capacity_score,
        market_move_bps=candidate.market_move_bps,
        absolute_market_move_bps=abs(candidate.market_move_bps),
    )
    reason_codes = _reason_codes(candidate, config=config)
    monitoring_status = _status_from_reason_codes(reason_codes)

    return StrategyCandidateMarketMonitoringPlanV10Result(
        monitoring_status=monitoring_status,
        monitoring_actions=_monitoring_actions(candidate, status=monitoring_status),
        next_review_minutes=_next_review_minutes(
            candidate,
            config=config,
            status=monitoring_status,
        ),
        reason_codes=reason_codes,
        payload=payload,
    )


def plan_strategy_candidate_market_monitoring_v10(
    *,
    market_id: str,
    candidate_status: str,
    watchlist_tier: str,
    edge_status: str,
    source_refresh_status: str,
    time_to_resolution_minutes: Decimal,
    team_capacity_score: Decimal,
    market_move_bps: Decimal,
    config: StrategyCandidateMarketMonitoringPlanV10Config | None = None,
) -> StrategyCandidateMarketMonitoringPlanV10Result:
    candidate = StrategyCandidateMarketMonitoringPlanV10Input(
        market_id=market_id,
        candidate_status=candidate_status,
        watchlist_tier=watchlist_tier,
        edge_status=edge_status,
        source_refresh_status=source_refresh_status,
        time_to_resolution_minutes=time_to_resolution_minutes,
        team_capacity_score=team_capacity_score,
        market_move_bps=market_move_bps,
    )
    return build_strategy_candidate_market_monitoring_plan_v10_result(
        candidate,
        config=config or StrategyCandidateMarketMonitoringPlanV10Config(),
    )


def strategy_candidate_market_monitoring_plan_v10_payload(
    report: StrategyCandidateMarketMonitoringPlanV10Result | dict[str, Any],
) -> dict[str, Any]:
    _require_readonly_flags("candidate market monitoring plan", report)
    _check_public_text_values("candidate market monitoring plan", report)
    reject_unsafe_surface_fields("candidate market monitoring plan", report)

    if isinstance(report, dict):
        return json_ready_no_floats(report)
    if type(report) is not StrategyCandidateMarketMonitoringPlanV10Result:
        raise ValueError(
            "report must be a StrategyCandidateMarketMonitoringPlanV10Result",
        )
    return json_ready_no_floats(
        {
            "monitoring_status": report.monitoring_status,
            "monitoring_actions": report.monitoring_actions,
            "next_review_minutes": report.next_review_minutes,
            "reason_codes": report.reason_codes,
            "payload": report.payload,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _reason_codes(
    candidate: StrategyCandidateMarketMonitoringPlanV10Input,
    *,
    config: StrategyCandidateMarketMonitoringPlanV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []

    if candidate.candidate_status in ("blocked", "rejected"):
        codes.append(f"candidate_status_{candidate.candidate_status}_blocked")
    if candidate.watchlist_tier == "none":
        codes.append("candidate_not_watchlisted_blocked")
    if candidate.edge_status == "negative":
        codes.append("candidate_edge_negative_blocked")
    if candidate.source_refresh_status == "blocked":
        codes.append("candidate_source_refresh_blocked")
    if candidate.time_to_resolution_minutes < config.minimum_resolution_minutes:
        codes.append("candidate_resolution_window_too_short_blocked")
    if candidate.team_capacity_score < config.minimum_team_capacity_score:
        codes.append("candidate_team_capacity_below_floor_blocked")

    if codes:
        return tuple(codes)

    if candidate.source_refresh_status == "stale":
        codes.append("candidate_source_refresh_stale_watch")
    if candidate.edge_status in ("flat", "weakening"):
        codes.append(f"candidate_edge_status_{candidate.edge_status}_watch")
    if abs(candidate.market_move_bps) >= config.watch_market_move_bps:
        codes.append("candidate_market_move_watch")
    if candidate.time_to_resolution_minutes <= config.near_resolution_minutes:
        codes.append("candidate_near_resolution_watch")
    if candidate.team_capacity_score < config.watch_team_capacity_score:
        codes.append("candidate_team_capacity_watch")
    if candidate.candidate_status in ("researching", "paused"):
        codes.append(f"candidate_status_{candidate.candidate_status}_watch")

    if codes:
        return tuple(codes)
    return ("candidate_market_monitoring_clear",)


def _monitoring_actions(
    candidate: StrategyCandidateMarketMonitoringPlanV10Input,
    *,
    status: str,
) -> tuple[str, ...]:
    if status == "monitor":
        return (MONITOR_ACTION,)

    actions: list[str] = []
    if candidate.candidate_status in ("blocked", "rejected"):
        actions.append("hold_readonly_monitoring_until_candidate_reopens")
    if candidate.watchlist_tier == "none":
        actions.append("remove_from_active_readonly_watchlist")
    if candidate.edge_status == "negative":
        actions.append("defer_until_edge_recovers")
    if candidate.source_refresh_status == "blocked":
        actions.append("repair_source_refresh_before_review")
    if candidate.time_to_resolution_minutes < ZERO:
        actions.append("archive_resolution_too_close")
    if candidate.team_capacity_score < ZERO:
        actions.append("defer_until_capacity_recovers")

    if status == "blocked":
        if candidate.time_to_resolution_minutes >= ZERO:
            if candidate.time_to_resolution_minutes < Decimal("30.000000"):
                actions.append("archive_resolution_too_close")
        if candidate.team_capacity_score >= ZERO:
            if candidate.team_capacity_score < Decimal("0.250000"):
                actions.append("defer_until_capacity_recovers")
        return tuple(actions)

    if candidate.source_refresh_status == "stale":
        actions.append("refresh_sources_before_review")
    if candidate.edge_status in ("flat", "weakening"):
        actions.append("review_edge_decay")
    if abs(candidate.market_move_bps) >= Decimal("75.000000"):
        actions.append("review_market_move")
    if candidate.time_to_resolution_minutes <= Decimal("180.000000"):
        actions.append("increase_cadence_near_resolution")
    if candidate.team_capacity_score < Decimal("0.500000"):
        actions.append("rebalance_team_capacity")
    if candidate.candidate_status in ("researching", "paused"):
        actions.append("complete_candidate_research_check")
    return tuple(actions)


def _next_review_minutes(
    candidate: StrategyCandidateMarketMonitoringPlanV10Input,
    *,
    config: StrategyCandidateMarketMonitoringPlanV10Config,
    status: str,
) -> Decimal:
    if status == "blocked":
        return config.blocked_review_minutes
    if status == "watch":
        if candidate.time_to_resolution_minutes <= config.near_resolution_minutes:
            return config.urgent_review_minutes
        return config.watch_review_minutes
    return _base_review_minutes(candidate.watchlist_tier, config)


def _base_review_minutes(
    watchlist_tier: str,
    config: StrategyCandidateMarketMonitoringPlanV10Config,
) -> Decimal:
    if watchlist_tier == "tier_1":
        return config.tier_1_review_minutes
    if watchlist_tier == "tier_2":
        return config.tier_2_review_minutes
    if watchlist_tier == "tier_3":
        return config.tier_3_review_minutes
    return config.blocked_review_minutes


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith(BLOCKED_SUFFIX) for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith(WATCH_SUFFIX) for reason_code in reason_codes):
        return "watch"
    return "monitor"


def _require_readonly_flags(label: str, value: object) -> None:
    if isinstance(value, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        return
    require_paper_only_flags(label, value)


def _normalize_string_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    for item in value:
        _require_public_text(field_name, item)
    return value


def _require_member(field_name: str, value: Any, allowed_values: tuple[str, ...]) -> None:
    _require_public_text(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_public_text(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _check_public_text_values(field_name, value)


def _check_public_text_values(label: str, value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in BAD_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public text in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _check_public_text_values(label, key)
            _check_public_text_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _check_public_text_values(label, item)


__all__ = (
    "StrategyCandidateMarketMonitoringPlanV10Config",
    "StrategyCandidateMarketMonitoringPlanV10Input",
    "StrategyCandidateMarketMonitoringPlanV10Payload",
    "StrategyCandidateMarketMonitoringPlanV10Result",
    "build_strategy_candidate_market_monitoring_plan_v10_result",
    "plan_strategy_candidate_market_monitoring_v10",
    "strategy_candidate_market_monitoring_plan_v10_payload",
)
