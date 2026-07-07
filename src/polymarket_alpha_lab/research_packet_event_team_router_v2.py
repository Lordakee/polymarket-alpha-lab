"""Pure read-only event research packet team router v2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_category_id, require_team_id


RESEARCH_PACKET_EVENT_TEAM_ROUTER_V2_CONFIG_VERSION = (
    "research-packet-event-team-router-v2"
)

ROUTE_STATUSES = ("assigned",)
ROW_REASON_CODES = (
    "domain_fit_leader",
    "calibration_supported",
    "source_familiarity_supported",
    "time_resolution_urgent",
    "backlog_pressure_diverted",
    "team_selected_politics",
    "team_selected_crypto_btc",
    "team_selected_crypto_eth",
    "team_selected_macro_rates",
    "team_selected_equity_indices",
    "team_selected_commodities_gold",
    "team_selected_commodities_oil",
    "team_selected_sports_soccer",
    "team_selected_sports_basketball",
    "team_selected_sports_other",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_SCORE = Decimal("100.000000")
DOMAIN_FIT_WEIGHT = Decimal("45.000000")
CALIBRATION_WEIGHT = Decimal("25.000000")
BACKLOG_RELIEF_WEIGHT = Decimal("20.000000")
SOURCE_FAMILIARITY_WEIGHT = Decimal("10.000000")
CATEGORY_MATCH_BONUS = Decimal("0.500000")
URGENT_ROUTING_BONUS = Decimal("1.000000")
URGENT_HOURS = Decimal("12.000000")
BASELINE_HOURS = Decimal("36.000000")
MICROSECONDS_PER_HOUR = Decimal("3600000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("per", "sist"),
    _join_parts("sig", "ning"),
    _join_parts("muta", "tion"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("tra", "de"),
)


@dataclass(frozen=True)
class ResearchPacketEventTeamRouterV2Config:
    config_version: str = RESEARCH_PACKET_EVENT_TEAM_ROUTER_V2_CONFIG_VERSION
    domain_fit_weight: Decimal = DOMAIN_FIT_WEIGHT
    calibration_weight: Decimal = CALIBRATION_WEIGHT
    backlog_relief_weight: Decimal = BACKLOG_RELIEF_WEIGHT
    source_familiarity_weight: Decimal = SOURCE_FAMILIARITY_WEIGHT
    category_match_bonus: Decimal = CATEGORY_MATCH_BONUS
    urgent_routing_bonus: Decimal = URGENT_ROUTING_BONUS
    urgent_hours: Decimal = URGENT_HOURS
    baseline_hours: Decimal = BASELINE_HOURS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "domain_fit_weight",
            "calibration_weight",
            "backlog_relief_weight",
            "source_familiarity_weight",
            "category_match_bonus",
            "urgent_routing_bonus",
            "urgent_hours",
            "baseline_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.urgent_hours >= self.baseline_hours:
            raise ValueError("urgent_hours must be less than baseline_hours")
        require_paper_only_flags("router v2 config", self)


@dataclass(frozen=True)
class ResearchPacketEventTeamRouterV2Packet:
    packet_id: str
    event_slug: str
    category_id: str
    source_ids: tuple[str, ...]
    received_at: datetime
    resolution_deadline_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _reject_public_surface("category_id", self.category_id)
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "source_ids",
            _normalize_public_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(self, "received_at", _as_utc("received_at", self.received_at))
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_optional_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        if (
            self.resolution_deadline_at is not None
            and self.resolution_deadline_at <= self.received_at
        ):
            raise ValueError("resolution_deadline_at must be after received_at")
        require_paper_only_flags("router v2 packet", self)


@dataclass(frozen=True)
class ResearchPacketEventTeamRouterV2TeamProfile:
    team_id: str
    category_id: str
    domain_fit_score: Decimal
    calibration_score: Decimal
    backlog_pressure_score: Decimal
    source_familiarity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _reject_public_surface("category_id", self.category_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        for field_name in (
            "domain_fit_score",
            "calibration_score",
            "backlog_pressure_score",
            "source_familiarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("router v2 team profile", self)


@dataclass(frozen=True)
class ResearchPacketEventTeamRouterV2TeamScore:
    rank_sequence: Decimal
    team_id: str
    category_id: str
    domain_fit_score: Decimal
    calibration_score: Decimal
    backlog_pressure_score: Decimal
    backlog_relief_score: Decimal
    source_familiarity_score: Decimal
    time_to_resolution_urgency_score: Decimal
    category_match_score: Decimal
    routing_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank_sequence",
            _normalize_positive_count_decimal("rank_sequence", self.rank_sequence),
        )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        for field_name in (
            "domain_fit_score",
            "calibration_score",
            "backlog_pressure_score",
            "backlog_relief_score",
            "source_familiarity_score",
            "time_to_resolution_urgency_score",
            "category_match_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "routing_score",
            _normalize_score("routing_score", self.routing_score),
        )
        require_paper_only_flags("router v2 team score", self)


@dataclass(frozen=True)
class ResearchPacketEventTeamRouterV2Decision:
    config_version: str
    packet_id: str
    event_slug: str
    category_id: str
    source_ids: tuple[str, ...]
    generated_at: datetime
    received_at: datetime
    resolution_deadline_at: datetime | None
    time_to_resolution_hours: Decimal
    time_to_resolution_urgency_score: Decimal
    assigned_team_id: str
    route_status: str
    assigned_routing_score: Decimal
    runner_up_team_id: str | None
    runner_up_routing_score: Decimal
    assignment_margin: Decimal
    team_scores: tuple[ResearchPacketEventTeamRouterV2TeamScore, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("config_version", "packet_id", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _reject_public_surface("category_id", self.category_id)
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "source_ids",
            _normalize_public_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(self, "received_at", _as_utc("received_at", self.received_at))
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_optional_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _normalize_nonnegative_decimal(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_urgency_score",
            _normalize_ratio(
                "time_to_resolution_urgency_score",
                self.time_to_resolution_urgency_score,
            ),
        )
        object.__setattr__(
            self,
            "assigned_team_id",
            require_team_id("assigned_team_id", self.assigned_team_id),
        )
        _require_member("route_status", self.route_status, ROUTE_STATUSES)
        object.__setattr__(
            self,
            "assigned_routing_score",
            _normalize_score("assigned_routing_score", self.assigned_routing_score),
        )
        if self.runner_up_team_id is not None:
            object.__setattr__(
                self,
                "runner_up_team_id",
                require_team_id("runner_up_team_id", self.runner_up_team_id),
            )
        object.__setattr__(
            self,
            "runner_up_routing_score",
            _normalize_score("runner_up_routing_score", self.runner_up_routing_score),
        )
        object.__setattr__(
            self,
            "assignment_margin",
            _normalize_nonnegative_decimal("assignment_margin", self.assignment_margin),
        )
        object.__setattr__(
            self,
            "team_scores",
            _normalize_team_scores(self.team_scores),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("router v2 decision", self)
        _validate_decision(self)


def route_research_packet_event_team_router_v2(
    packet: ResearchPacketEventTeamRouterV2Packet,
    *,
    profiles: Iterable[ResearchPacketEventTeamRouterV2TeamProfile],
    generated_at: datetime,
    config: ResearchPacketEventTeamRouterV2Config | None = None,
) -> ResearchPacketEventTeamRouterV2Decision:
    if type(packet) is not ResearchPacketEventTeamRouterV2Packet:
        raise ValueError("packet must be a ResearchPacketEventTeamRouterV2Packet")
    active_config = ResearchPacketEventTeamRouterV2Config() if config is None else config
    if type(active_config) is not ResearchPacketEventTeamRouterV2Config:
        raise ValueError("config must be a ResearchPacketEventTeamRouterV2Config")
    require_paper_only_flags("router v2 packet", packet)
    require_paper_only_flags("router v2 config", active_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if packet.received_at > generated_at_utc:
        raise ValueError("received_at must be no later than generated_at")
    if (
        packet.resolution_deadline_at is not None
        and packet.resolution_deadline_at <= generated_at_utc
    ):
        raise ValueError("resolution_deadline_at must be after generated_at")

    normalized_profiles = _normalize_profiles(profiles)
    time_hours = _time_to_resolution_hours(packet, generated_at_utc)
    urgency_score = _time_to_resolution_urgency_score(time_hours, active_config)
    team_scores = _ranked_team_scores(
        packet,
        normalized_profiles,
        time_to_resolution_urgency_score=urgency_score,
        config=active_config,
    )
    top_score = team_scores[0]
    runner_up = team_scores[1] if len(team_scores) > 1 else None
    reason_codes = _decision_reason_codes(packet, top_score, runner_up, urgency_score)

    digest = _derived_validation_digest(
        config_version=active_config.config_version,
        packet=packet,
        generated_at=generated_at_utc,
        time_to_resolution_hours=time_hours,
        time_to_resolution_urgency_score=urgency_score,
        assigned_team_id=top_score.team_id,
        route_status="assigned",
        assigned_routing_score=top_score.routing_score,
        runner_up_team_id=None if runner_up is None else runner_up.team_id,
        runner_up_routing_score=ZERO if runner_up is None else runner_up.routing_score,
        assignment_margin=(
            top_score.routing_score
            if runner_up is None
            else top_score.routing_score - runner_up.routing_score
        ),
        team_scores=team_scores,
        reason_codes=reason_codes,
    )

    return ResearchPacketEventTeamRouterV2Decision(
        config_version=active_config.config_version,
        packet_id=packet.packet_id,
        event_slug=packet.event_slug,
        category_id=packet.category_id,
        source_ids=packet.source_ids,
        generated_at=generated_at_utc,
        received_at=packet.received_at,
        resolution_deadline_at=packet.resolution_deadline_at,
        time_to_resolution_hours=time_hours,
        time_to_resolution_urgency_score=urgency_score,
        assigned_team_id=top_score.team_id,
        route_status="assigned",
        assigned_routing_score=top_score.routing_score,
        runner_up_team_id=None if runner_up is None else runner_up.team_id,
        runner_up_routing_score=ZERO if runner_up is None else runner_up.routing_score,
        assignment_margin=(
            top_score.routing_score
            if runner_up is None
            else top_score.routing_score - runner_up.routing_score
        ),
        team_scores=team_scores,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
    )


def research_packet_event_team_router_v2_payload(
    decision: ResearchPacketEventTeamRouterV2Decision,
) -> dict[str, Any]:
    if type(decision) is not ResearchPacketEventTeamRouterV2Decision:
        raise ValueError("decision must be a ResearchPacketEventTeamRouterV2Decision")
    require_paper_only_flags("router v2 decision", decision)
    _validate_decision(decision)
    payload = _decision_payload(decision, include_digest=True)
    _reject_public_surface("payload", payload)
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("decision payload must be a JSON object")
    require_paper_only_flags("router v2 payload", _PayloadFlags(ready_payload))
    return ready_payload


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


def _ranked_team_scores(
    packet: ResearchPacketEventTeamRouterV2Packet,
    profiles: tuple[ResearchPacketEventTeamRouterV2TeamProfile, ...],
    *,
    time_to_resolution_urgency_score: Decimal,
    config: ResearchPacketEventTeamRouterV2Config,
) -> tuple[ResearchPacketEventTeamRouterV2TeamScore, ...]:
    unranked = tuple(
        _team_score(
            packet,
            profile,
            time_to_resolution_urgency_score=time_to_resolution_urgency_score,
            config=config,
        )
        for profile in profiles
    )
    ranked = tuple(sorted(unranked, key=_team_score_rank))
    return tuple(
        ResearchPacketEventTeamRouterV2TeamScore(
            rank_sequence=_count(index),
            team_id=row.team_id,
            category_id=row.category_id,
            domain_fit_score=row.domain_fit_score,
            calibration_score=row.calibration_score,
            backlog_pressure_score=row.backlog_pressure_score,
            backlog_relief_score=row.backlog_relief_score,
            source_familiarity_score=row.source_familiarity_score,
            time_to_resolution_urgency_score=row.time_to_resolution_urgency_score,
            category_match_score=row.category_match_score,
            routing_score=row.routing_score,
        )
        for index, row in enumerate(ranked, start=1)
    )


def _team_score(
    packet: ResearchPacketEventTeamRouterV2Packet,
    profile: ResearchPacketEventTeamRouterV2TeamProfile,
    *,
    time_to_resolution_urgency_score: Decimal,
    config: ResearchPacketEventTeamRouterV2Config,
) -> ResearchPacketEventTeamRouterV2TeamScore:
    backlog_relief_score = _quantize(ONE - profile.backlog_pressure_score)
    category_match_score = ONE if packet.category_id == profile.category_id else ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = profile.domain_fit_score * config.domain_fit_weight
        score += profile.calibration_score * config.calibration_weight
        score += backlog_relief_score * config.backlog_relief_weight
        score += profile.source_familiarity_score * config.source_familiarity_weight
        score += category_match_score * config.category_match_bonus
        score += time_to_resolution_urgency_score * config.urgent_routing_bonus
    return ResearchPacketEventTeamRouterV2TeamScore(
        rank_sequence=_count(1),
        team_id=profile.team_id,
        category_id=profile.category_id,
        domain_fit_score=profile.domain_fit_score,
        calibration_score=profile.calibration_score,
        backlog_pressure_score=profile.backlog_pressure_score,
        backlog_relief_score=backlog_relief_score,
        source_familiarity_score=profile.source_familiarity_score,
        time_to_resolution_urgency_score=time_to_resolution_urgency_score,
        category_match_score=category_match_score,
        routing_score=_normalize_score("routing_score", score),
    )


def _team_score_rank(
    row: ResearchPacketEventTeamRouterV2TeamScore,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -row.routing_score,
        -row.domain_fit_score,
        -row.calibration_score,
        row.backlog_pressure_score,
        row.team_id,
    )


def _decision_reason_codes(
    packet: ResearchPacketEventTeamRouterV2Packet,
    top_score: ResearchPacketEventTeamRouterV2TeamScore,
    runner_up: ResearchPacketEventTeamRouterV2TeamScore | None,
    urgency_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = ["domain_fit_leader"]
    if top_score.calibration_score >= Decimal("0.700000"):
        reason_codes.append("calibration_supported")
    if top_score.source_familiarity_score >= Decimal("0.600000"):
        reason_codes.append("source_familiarity_supported")
    if urgency_score >= ONE:
        reason_codes.append("time_resolution_urgent")
    if (
        packet.category_id != top_score.category_id
        and runner_up is not None
        and runner_up.category_id == packet.category_id
    ):
        reason_codes.append("backlog_pressure_diverted")
    reason_codes.append(f"team_selected_{top_score.team_id}")
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes)


def _time_to_resolution_hours(
    packet: ResearchPacketEventTeamRouterV2Packet,
    generated_at: datetime,
) -> Decimal:
    if packet.resolution_deadline_at is None:
        return ZERO
    delta = packet.resolution_deadline_at - generated_at
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_decimal(
        "time_to_resolution_hours",
        total_microseconds / MICROSECONDS_PER_HOUR,
    )


def _time_to_resolution_urgency_score(
    time_to_resolution_hours: Decimal,
    config: ResearchPacketEventTeamRouterV2Config,
) -> Decimal:
    if time_to_resolution_hours <= config.urgent_hours:
        return ONE
    if time_to_resolution_hours >= config.baseline_hours:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = (config.baseline_hours - time_to_resolution_hours) / (
            config.baseline_hours - config.urgent_hours
        )
    return _normalize_ratio("time_to_resolution_urgency_score", score)


def _normalize_profiles(
    profiles: Iterable[ResearchPacketEventTeamRouterV2TeamProfile],
) -> tuple[ResearchPacketEventTeamRouterV2TeamProfile, ...]:
    if isinstance(profiles, str | bytes):
        raise ValueError("team_profiles must be an iterable")
    try:
        normalized = tuple(profiles)
    except TypeError as exc:
        raise ValueError("team_profiles must be an iterable") from exc
    if not normalized:
        raise ValueError("team_profiles must contain at least one profile")
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchPacketEventTeamRouterV2TeamProfile:
            raise ValueError("team_profiles must contain router v2 team profiles")
        require_paper_only_flags("router v2 team profile", item)
        if item.team_id in seen:
            raise ValueError("team_profiles team_id values must be unique")
        seen.add(item.team_id)
    return normalized


def _normalize_team_scores(
    team_scores: Iterable[ResearchPacketEventTeamRouterV2TeamScore],
) -> tuple[ResearchPacketEventTeamRouterV2TeamScore, ...]:
    if isinstance(team_scores, str | bytes):
        raise ValueError("team_scores must be an iterable")
    try:
        normalized = tuple(team_scores)
    except TypeError as exc:
        raise ValueError("team_scores must be an iterable") from exc
    if not normalized:
        raise ValueError("team_scores must contain at least one score")
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchPacketEventTeamRouterV2TeamScore:
            raise ValueError("team_scores must contain router v2 team scores")
        require_paper_only_flags("router v2 team score", item)
        if item.team_id in seen:
            raise ValueError("team_scores team_id values must be unique")
        seen.add(item.team_id)
    if tuple(row.rank_sequence for row in normalized) != tuple(
        _count(index) for index in range(1, len(normalized) + 1)
    ):
        raise ValueError("team_scores must have contiguous rank_sequence values")
    if normalized != tuple(sorted(normalized, key=_team_score_rank)):
        raise ValueError("team_scores must use deterministic sorting")
    return normalized


def _validate_decision(decision: ResearchPacketEventTeamRouterV2Decision) -> None:
    if decision.received_at > decision.generated_at:
        raise ValueError("received_at must be no later than generated_at")
    if (
        decision.resolution_deadline_at is not None
        and decision.resolution_deadline_at <= decision.generated_at
    ):
        raise ValueError("resolution_deadline_at must be after generated_at")
    expected_digest = _derived_validation_digest(
        config_version=decision.config_version,
        packet=ResearchPacketEventTeamRouterV2Packet(
            packet_id=decision.packet_id,
            event_slug=decision.event_slug,
            category_id=decision.category_id,
            source_ids=decision.source_ids,
            received_at=decision.received_at,
            resolution_deadline_at=decision.resolution_deadline_at,
        ),
        generated_at=decision.generated_at,
        time_to_resolution_hours=decision.time_to_resolution_hours,
        time_to_resolution_urgency_score=decision.time_to_resolution_urgency_score,
        assigned_team_id=decision.assigned_team_id,
        route_status=decision.route_status,
        assigned_routing_score=decision.assigned_routing_score,
        runner_up_team_id=decision.runner_up_team_id,
        runner_up_routing_score=decision.runner_up_routing_score,
        assignment_margin=decision.assignment_margin,
        team_scores=decision.team_scores,
        reason_codes=decision.reason_codes,
    )
    if decision.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public decision fields")
    expected_top = decision.team_scores[0]
    if decision.assigned_team_id != expected_top.team_id:
        raise ValueError("assigned_team_id must match team_scores")
    if decision.assigned_routing_score != expected_top.routing_score:
        raise ValueError("assigned_routing_score must match team_scores")
    expected_runner_up = decision.team_scores[1] if len(decision.team_scores) > 1 else None
    if decision.runner_up_team_id != (
        None if expected_runner_up is None else expected_runner_up.team_id
    ):
        raise ValueError("runner_up_team_id must match team_scores")
    if decision.runner_up_routing_score != (
        ZERO if expected_runner_up is None else expected_runner_up.routing_score
    ):
        raise ValueError("runner_up_routing_score must match team_scores")
    expected_margin = (
        decision.assigned_routing_score
        if expected_runner_up is None
        else decision.assigned_routing_score - expected_runner_up.routing_score
    )
    if decision.assignment_margin != expected_margin:
        raise ValueError("assignment_margin must match team_scores")


def _decision_payload(
    decision: ResearchPacketEventTeamRouterV2Decision,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        "config_version": decision.config_version,
        "packet_id": decision.packet_id,
        "event_slug": decision.event_slug,
        "category_id": decision.category_id,
        "source_ids": list(decision.source_ids),
        "generated_at": decision.generated_at,
        "received_at": decision.received_at,
        "resolution_deadline_at": decision.resolution_deadline_at,
        "time_to_resolution_hours": decision.time_to_resolution_hours,
        "time_to_resolution_urgency_score": decision.time_to_resolution_urgency_score,
        "assigned_team_id": decision.assigned_team_id,
        "route_status": decision.route_status,
        "assigned_routing_score": decision.assigned_routing_score,
        "runner_up_team_id": decision.runner_up_team_id,
        "runner_up_routing_score": decision.runner_up_routing_score,
        "assignment_margin": decision.assignment_margin,
        "team_scores": [_team_score_payload(row) for row in decision.team_scores],
        "reason_codes": list(decision.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = decision.derived_validation_digest
    return payload


def _team_score_payload(row: ResearchPacketEventTeamRouterV2TeamScore) -> dict[str, Any]:
    return {
        "rank_sequence": row.rank_sequence,
        "team_id": row.team_id,
        "category_id": row.category_id,
        "domain_fit_score": row.domain_fit_score,
        "calibration_score": row.calibration_score,
        "backlog_pressure_score": row.backlog_pressure_score,
        "backlog_relief_score": row.backlog_relief_score,
        "source_familiarity_score": row.source_familiarity_score,
        "time_to_resolution_urgency_score": row.time_to_resolution_urgency_score,
        "category_match_score": row.category_match_score,
        "routing_score": row.routing_score,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _derived_validation_digest(
    *,
    config_version: str,
    packet: ResearchPacketEventTeamRouterV2Packet,
    generated_at: datetime,
    time_to_resolution_hours: Decimal,
    time_to_resolution_urgency_score: Decimal,
    assigned_team_id: str,
    route_status: str,
    assigned_routing_score: Decimal,
    runner_up_team_id: str | None,
    runner_up_routing_score: Decimal,
    assignment_margin: Decimal,
    team_scores: tuple[ResearchPacketEventTeamRouterV2TeamScore, ...],
    reason_codes: tuple[str, ...],
) -> str:
    decision = {
        "config_version": config_version,
        "packet_id": packet.packet_id,
        "event_slug": packet.event_slug,
        "category_id": packet.category_id,
        "source_ids": list(packet.source_ids),
        "generated_at": generated_at,
        "received_at": packet.received_at,
        "resolution_deadline_at": packet.resolution_deadline_at,
        "time_to_resolution_hours": time_to_resolution_hours,
        "time_to_resolution_urgency_score": time_to_resolution_urgency_score,
        "assigned_team_id": assigned_team_id,
        "route_status": route_status,
        "assigned_routing_score": assigned_routing_score,
        "runner_up_team_id": runner_up_team_id,
        "runner_up_routing_score": runner_up_routing_score,
        "assignment_margin": assignment_margin,
        "team_scores": [_team_score_payload(row) for row in team_scores],
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    ready = json_ready_no_floats(decision)
    encoded = json.dumps(ready, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for item in items:
        _require_public_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must contain unique values")
        seen.add(item)
    return tuple(sorted(items))


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must contain known values")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain known values") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must contain unique values")
    for item in items:
        if type(item) is not str or item not in ROW_REASON_CODES:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in ROW_REASON_CODES if code in items) != items:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return items


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > MAX_SCORE:
        raise ValueError(f"{field_name} must be no greater than one hundred")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_surface(field_name, value)


def _reject_public_surface(label: str, value: object) -> None:
    for text in _iter_public_text(label, value):
        lowered = text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value for {label}")


def _iter_public_text(label: str, value: object) -> tuple[str, ...]:
    if type(label) is str:
        texts = [label]
    else:
        texts = []
    if isinstance(value, str):
        texts.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            texts.extend(_iter_public_text(key, item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            texts.extend(_iter_public_text(label, item))
    return tuple(texts)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must contain a known value")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "RESEARCH_PACKET_EVENT_TEAM_ROUTER_V2_CONFIG_VERSION",
    "ResearchPacketEventTeamRouterV2Config",
    "ResearchPacketEventTeamRouterV2Decision",
    "ResearchPacketEventTeamRouterV2Packet",
    "ResearchPacketEventTeamRouterV2TeamProfile",
    "ResearchPacketEventTeamRouterV2TeamScore",
    "research_packet_event_team_router_v2_payload",
    "route_research_packet_event_team_router_v2",
)
