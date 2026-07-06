"""Pure paper-only market research packet prioritization."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_PACKET_PRIORITY_V10_CONFIG_VERSION = (
    "market-research-packet-priority-v10"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SOURCE_GAP_PENALTY_CAP = Decimal("0.200000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PACKET_STATUSES = ("ready", "researching", "draft", "archived", "blocked")
BLOCKED_PACKET_STATUSES = ("archived", "blocked")
PRIORITY_STATUSES = ("urgent", "high", "review", "low", "blocked")
QUEUE_RECOMMENDATIONS = (
    "front_of_queue",
    "research_queue",
    "human_review_queue",
    "backlog",
    "do_not_queue",
)
REASON_CODES = (
    "capacity_available",
    "capacity_constrained",
    "completeness_high",
    "completeness_watch",
    "completeness_low",
    "human_review_required",
    "information_edge_high",
    "information_edge_medium",
    "information_edge_low",
    "packet_ready",
    "packet_in_progress",
    "packet_blocked_status",
    "priority_urgent",
    "priority_high",
    "priority_review",
    "priority_low",
    "priority_blocked",
    "resolution_window_immediate",
    "resolution_window_near",
    "resolution_window_normal",
    "source_gaps_none",
    "source_gaps_present",
)


@dataclass(frozen=True)
class MarketResearchPacketPriorityV10Config:
    config_version: str = DEFAULT_MARKET_RESEARCH_PACKET_PRIORITY_V10_CONFIG_VERSION
    immediate_resolution_minutes: Decimal = Decimal("60")
    near_resolution_minutes: Decimal = Decimal("600")
    minimum_ready_completeness: Decimal = Decimal("0.600000")
    high_completeness_score: Decimal = Decimal("0.800000")
    high_information_edge_score: Decimal = Decimal("0.800000")
    medium_information_edge_score: Decimal = Decimal("0.500000")
    minimum_capacity_score: Decimal = Decimal("0.500000")
    high_priority_threshold: Decimal = Decimal("0.750000")
    review_priority_threshold: Decimal = Decimal("0.300000")
    completeness_weight: Decimal = Decimal("0.391729")
    information_edge_weight: Decimal = Decimal("0.234716")
    urgency_weight: Decimal = Decimal("0.093389")
    capacity_weight: Decimal = Decimal("0.280166")
    source_gap_penalty_weight: Decimal = Decimal("0.075000")
    human_review_penalty_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, MarketResearchPacketPriorityV10Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "immediate_resolution_minutes",
            "near_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_ready_completeness",
            "high_completeness_score",
            "high_information_edge_score",
            "medium_information_edge_score",
            "minimum_capacity_score",
            "high_priority_threshold",
            "review_priority_threshold",
            "completeness_weight",
            "information_edge_weight",
            "urgency_weight",
            "capacity_weight",
            "source_gap_penalty_weight",
            "human_review_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.immediate_resolution_minutes >= self.near_resolution_minutes:
            raise ValueError(
                "immediate_resolution_minutes must be below near_resolution_minutes",
            )
        if self.minimum_ready_completeness > self.high_completeness_score:
            raise ValueError(
                "minimum_ready_completeness must be <= high_completeness_score",
            )
        if self.medium_information_edge_score > self.high_information_edge_score:
            raise ValueError(
                "medium_information_edge_score must be <= high_information_edge_score",
            )
        if self.review_priority_threshold > self.high_priority_threshold:
            raise ValueError("review_priority_threshold must be <= high_priority_threshold")
        _validate_score_weights(self)
        require_paper_only_flags("MarketResearchPacketPriorityV10Config", self)


@dataclass(frozen=True)
class MarketResearchPacketPriorityV10Input:
    market_id: str
    packet_status: str
    completeness_score: Decimal
    information_edge_score: Decimal
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    human_review_required: bool
    source_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("packet", self, MarketResearchPacketPriorityV10Input)
        _require_canonical_string("market_id", self.market_id)
        _require_choice("packet_status", self.packet_status, PACKET_STATUSES)
        for field_name in (
            "completeness_score",
            "information_edge_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_count(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_count("source_gap_count", self.source_gap_count),
        )
        _require_bool("human_review_required", self.human_review_required)
        require_paper_only_flags("MarketResearchPacketPriorityV10Input", self)


@dataclass(frozen=True)
class MarketResearchPacketPriorityV10Report:
    config_version: str
    market_id: str
    packet_status: str
    completeness_score: Decimal
    information_edge_score: Decimal
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    human_review_required: bool
    source_gap_count: Decimal
    urgency_score: Decimal
    readiness_score: Decimal
    gap_penalty: Decimal
    review_penalty: Decimal
    priority_score: Decimal
    priority_status: str
    queue_recommendation: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, MarketResearchPacketPriorityV10Report)
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_id", self.market_id)
        _require_choice("packet_status", self.packet_status, PACKET_STATUSES)
        for field_name in (
            "completeness_score",
            "information_edge_score",
            "team_capacity_score",
            "urgency_score",
            "readiness_score",
            "gap_penalty",
            "review_penalty",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("time_to_resolution_minutes", "source_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_bool("human_review_required", self.human_review_required)
        _require_choice("priority_status", self.priority_status, PRIORITY_STATUSES)
        _require_choice(
            "queue_recommendation",
            self.queue_recommendation,
            QUEUE_RECOMMENDATIONS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("market research packet priority v10", self)
        require_paper_only_flags("MarketResearchPacketPriorityV10Report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return market_research_packet_priority_v10_payload(self)


def prioritize_market_research_packet_v10(
    packet: MarketResearchPacketPriorityV10Input,
    *,
    config: MarketResearchPacketPriorityV10Config | None = None,
) -> MarketResearchPacketPriorityV10Report:
    if type(packet) is not MarketResearchPacketPriorityV10Input:
        raise ValueError("packet must be a MarketResearchPacketPriorityV10Input")
    require_paper_only_flags("packet", packet)
    active_config = config or MarketResearchPacketPriorityV10Config()
    if type(active_config) is not MarketResearchPacketPriorityV10Config:
        raise ValueError("config must be a MarketResearchPacketPriorityV10Config")
    require_paper_only_flags("config", active_config)

    urgency_score = _urgency_score(packet.time_to_resolution_minutes, active_config)
    readiness_score = _readiness_score(packet.packet_status, packet.completeness_score)
    gap_penalty = _gap_penalty(packet.source_gap_count, active_config)
    review_penalty = _review_penalty(packet.human_review_required, active_config)
    priority_score = _priority_score(
        completeness_score=packet.completeness_score,
        information_edge_score=packet.information_edge_score,
        urgency_score=urgency_score,
        team_capacity_score=packet.team_capacity_score,
        gap_penalty=gap_penalty,
        review_penalty=review_penalty,
        config=active_config,
    )
    priority_status = _priority_status(
        packet_status=packet.packet_status,
        completeness_score=packet.completeness_score,
        information_edge_score=packet.information_edge_score,
        team_capacity_score=packet.team_capacity_score,
        human_review_required=packet.human_review_required,
        priority_score=priority_score,
        config=active_config,
    )

    return MarketResearchPacketPriorityV10Report(
        config_version=active_config.config_version,
        market_id=packet.market_id,
        packet_status=packet.packet_status,
        completeness_score=packet.completeness_score,
        information_edge_score=packet.information_edge_score,
        time_to_resolution_minutes=packet.time_to_resolution_minutes,
        team_capacity_score=packet.team_capacity_score,
        human_review_required=packet.human_review_required,
        source_gap_count=packet.source_gap_count,
        urgency_score=urgency_score,
        readiness_score=readiness_score,
        gap_penalty=gap_penalty,
        review_penalty=review_penalty,
        priority_score=priority_score,
        priority_status=priority_status,
        queue_recommendation=_queue_recommendation(priority_status),
        reason_codes=_reason_codes(
            packet_status=packet.packet_status,
            completeness_score=packet.completeness_score,
            information_edge_score=packet.information_edge_score,
            time_to_resolution_minutes=packet.time_to_resolution_minutes,
            team_capacity_score=packet.team_capacity_score,
            human_review_required=packet.human_review_required,
            source_gap_count=packet.source_gap_count,
            priority_status=priority_status,
            config=active_config,
        ),
    )


def market_research_packet_priority_v10_payload(
    report: MarketResearchPacketPriorityV10Report,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPacketPriorityV10Report:
        raise ValueError("report must be a MarketResearchPacketPriorityV10Report")
    require_paper_only_flags("report", report)
    payload = {
        "config_version": report.config_version,
        "market_id": report.market_id,
        "packet_status": report.packet_status,
        "completeness_score": report.completeness_score,
        "information_edge_score": report.information_edge_score,
        "time_to_resolution_minutes": report.time_to_resolution_minutes,
        "team_capacity_score": report.team_capacity_score,
        "human_review_required": report.human_review_required,
        "source_gap_count": report.source_gap_count,
        "urgency_score": report.urgency_score,
        "readiness_score": report.readiness_score,
        "gap_penalty": report.gap_penalty,
        "review_penalty": report.review_penalty,
        "priority_score": report.priority_score,
        "priority_status": report.priority_status,
        "queue_recommendation": report.queue_recommendation,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields("market research packet priority v10 payload", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _urgency_score(
    time_to_resolution_minutes: Decimal,
    config: MarketResearchPacketPriorityV10Config,
) -> Decimal:
    if time_to_resolution_minutes <= config.immediate_resolution_minutes:
        return ONE_RATIO
    if time_to_resolution_minutes >= config.near_resolution_minutes:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        resolution_range = (
            config.near_resolution_minutes - config.immediate_resolution_minutes
        )
        minutes_remaining = (
            config.near_resolution_minutes - time_to_resolution_minutes
        )
        return _clamp_ratio(minutes_remaining / resolution_range)


def _readiness_score(packet_status: str, completeness_score: Decimal) -> Decimal:
    if packet_status == "ready":
        return ONE_RATIO
    if packet_status in BLOCKED_PACKET_STATUSES:
        return ZERO_RATIO
    return completeness_score


def _gap_penalty(
    source_gap_count: Decimal,
    config: MarketResearchPacketPriorityV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        penalty = source_gap_count * config.source_gap_penalty_weight
    if penalty > SOURCE_GAP_PENALTY_CAP:
        return SOURCE_GAP_PENALTY_CAP
    return _clamp_ratio(penalty)


def _review_penalty(
    human_review_required: bool,
    config: MarketResearchPacketPriorityV10Config,
) -> Decimal:
    if human_review_required:
        return config.human_review_penalty_weight
    return ZERO_RATIO


def _priority_score(
    *,
    completeness_score: Decimal,
    information_edge_score: Decimal,
    urgency_score: Decimal,
    team_capacity_score: Decimal,
    gap_penalty: Decimal,
    review_penalty: Decimal,
    config: MarketResearchPacketPriorityV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            completeness_score * config.completeness_weight
            + information_edge_score * config.information_edge_weight
            + urgency_score * config.urgency_weight
            + team_capacity_score * config.capacity_weight
            - gap_penalty
            - review_penalty
        )
    return _clamp_ratio(raw_score)


def _priority_status(
    *,
    packet_status: str,
    completeness_score: Decimal,
    information_edge_score: Decimal,
    team_capacity_score: Decimal,
    human_review_required: bool,
    priority_score: Decimal,
    config: MarketResearchPacketPriorityV10Config,
) -> str:
    if (
        packet_status in BLOCKED_PACKET_STATUSES
        or completeness_score < config.minimum_ready_completeness
    ):
        return "blocked"
    if human_review_required:
        return "review"
    if (
        priority_score >= config.high_priority_threshold
        and packet_status == "ready"
        and completeness_score >= config.high_completeness_score
        and information_edge_score >= config.high_information_edge_score
        and team_capacity_score >= config.minimum_capacity_score
    ):
        return "urgent"
    if priority_score >= config.high_priority_threshold:
        return "high"
    if priority_score >= config.review_priority_threshold:
        return "review"
    return "low"


def _queue_recommendation(priority_status: str) -> str:
    if priority_status == "urgent":
        return "front_of_queue"
    if priority_status == "high":
        return "research_queue"
    if priority_status == "review":
        return "human_review_queue"
    if priority_status == "low":
        return "backlog"
    if priority_status == "blocked":
        return "do_not_queue"
    raise ValueError("priority_status must be supported")


def _reason_codes(
    *,
    packet_status: str,
    completeness_score: Decimal,
    information_edge_score: Decimal,
    time_to_resolution_minutes: Decimal,
    team_capacity_score: Decimal,
    human_review_required: bool,
    source_gap_count: Decimal,
    priority_status: str,
    config: MarketResearchPacketPriorityV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if team_capacity_score >= config.minimum_capacity_score:
        codes.append("capacity_available")
    else:
        codes.append("capacity_constrained")
    if completeness_score >= config.high_completeness_score:
        codes.append("completeness_high")
    elif completeness_score >= config.minimum_ready_completeness:
        codes.append("completeness_watch")
    else:
        codes.append("completeness_low")
    if human_review_required:
        codes.append("human_review_required")
    if information_edge_score >= config.high_information_edge_score:
        codes.append("information_edge_high")
    elif information_edge_score >= config.medium_information_edge_score:
        codes.append("information_edge_medium")
    else:
        codes.append("information_edge_low")
    if packet_status == "ready":
        codes.append("packet_ready")
    elif packet_status in BLOCKED_PACKET_STATUSES:
        codes.append("packet_blocked_status")
    else:
        codes.append("packet_in_progress")
    codes.append(f"priority_{priority_status}")
    if time_to_resolution_minutes <= config.immediate_resolution_minutes:
        codes.append("resolution_window_immediate")
    elif time_to_resolution_minutes <= config.near_resolution_minutes:
        codes.append("resolution_window_near")
    else:
        codes.append("resolution_window_normal")
    if source_gap_count == ZERO_COUNT:
        codes.append("source_gaps_none")
    else:
        codes.append("source_gaps_present")
    return _normalize_reason_codes(tuple(codes))


def _validate_report(report: MarketResearchPacketPriorityV10Report) -> None:
    config = MarketResearchPacketPriorityV10Config(config_version=report.config_version)
    expected_urgency_score = _urgency_score(
        report.time_to_resolution_minutes,
        config,
    )
    expected_readiness_score = _readiness_score(
        report.packet_status,
        report.completeness_score,
    )
    expected_gap_penalty = _gap_penalty(report.source_gap_count, config)
    expected_review_penalty = _review_penalty(report.human_review_required, config)
    expected_priority_score = _priority_score(
        completeness_score=report.completeness_score,
        information_edge_score=report.information_edge_score,
        urgency_score=expected_urgency_score,
        team_capacity_score=report.team_capacity_score,
        gap_penalty=expected_gap_penalty,
        review_penalty=expected_review_penalty,
        config=config,
    )
    if report.urgency_score != expected_urgency_score:
        raise ValueError("urgency_score must match packet timing")
    if report.readiness_score != expected_readiness_score:
        raise ValueError("readiness_score must match packet_status")
    if report.gap_penalty != expected_gap_penalty:
        raise ValueError("gap_penalty must match source_gap_count")
    if report.review_penalty != expected_review_penalty:
        raise ValueError("review_penalty must match human_review_required")
    if report.priority_score != expected_priority_score:
        raise ValueError("priority_score must match score components")
    expected_priority_status = _priority_status(
        packet_status=report.packet_status,
        completeness_score=report.completeness_score,
        information_edge_score=report.information_edge_score,
        team_capacity_score=report.team_capacity_score,
        human_review_required=report.human_review_required,
        priority_score=report.priority_score,
        config=config,
    )
    if report.priority_status != expected_priority_status:
        raise ValueError("priority_status must match priority_score")
    if report.queue_recommendation != _queue_recommendation(report.priority_status):
        raise ValueError("queue_recommendation must match priority_status")
    expected_reason_codes = _reason_codes(
        packet_status=report.packet_status,
        completeness_score=report.completeness_score,
        information_edge_score=report.information_edge_score,
        time_to_resolution_minutes=report.time_to_resolution_minutes,
        team_capacity_score=report.team_capacity_score,
        human_review_required=report.human_review_required,
        source_gap_count=report.source_gap_count,
        priority_status=report.priority_status,
        config=config,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("report reason_codes must match")


def _validate_score_weights(config: MarketResearchPacketPriorityV10Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            config.completeness_weight
            + config.information_edge_weight
            + config.urgency_weight
            + config.capacity_weight
        ).quantize(RATIO_QUANTUM)
    if total != ONE_RATIO:
        raise ValueError("score component weights must sum to 1.000000")


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _require_choice(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_PACKET_PRIORITY_V10_CONFIG_VERSION",
    "PACKET_STATUSES",
    "PRIORITY_STATUSES",
    "QUEUE_RECOMMENDATIONS",
    "REASON_CODES",
    "MarketResearchPacketPriorityV10Config",
    "MarketResearchPacketPriorityV10Input",
    "MarketResearchPacketPriorityV10Report",
    "prioritize_market_research_packet_v10",
    "market_research_packet_priority_v10_payload",
)
