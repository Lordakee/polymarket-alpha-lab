"""Pure read-only research packet completeness v10 evaluator."""

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


DEFAULT_CONFIG_VERSION = "strategy-research-packet-completeness-v10"
COUNT_QUANT = Decimal("1")
SCORE_QUANT = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

HUMAN_REVIEW_STATUSES = ("approved", "pending_review", "rejected")
PACKET_STATUSES = ("complete", "watch", "blocked", "rejected")
SECTION_ORDER = (
    "resolution_contract",
    "source_quorum",
    "forecast_rationale",
    "cost_model",
    "risk_sizing",
    "exit_readiness",
    "human_review_status",
)
BLOCKING_SECTIONS = (
    "resolution_contract",
    "source_quorum",
    "forecast_rationale",
    "cost_model",
    "risk_sizing",
    "exit_readiness",
)
REASON_CODES = (
    "complete",
    "resolution_contract_missing",
    "source_quorum_missing",
    "forecast_rationale_missing",
    "cost_model_missing",
    "risk_sizing_missing",
    "exit_readiness_missing",
    "human_review_not_approved",
    "human_review_rejected",
)


@dataclass(frozen=True)
class StrategyResearchPacketCompletenessV10Packet:
    packet_id: str
    market_slug: str
    research_generated_at: datetime
    source_count: Decimal
    required_source_count: Decimal
    resolution_contract_present: bool
    forecast_rationale_present: bool
    cost_model_present: bool
    risk_sizing_present: bool
    exit_readiness_present: bool
    human_review_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "research_generated_at",
            _as_utc("research_generated_at", self.research_generated_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_count("required_source_count", self.required_source_count),
        )
        for field_name in (
            "resolution_contract_present",
            "forecast_rationale_present",
            "cost_model_present",
            "risk_sizing_present",
            "exit_readiness_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_member(
            "human_review_status",
            self.human_review_status,
            HUMAN_REVIEW_STATUSES,
        )
        reject_unsafe_surface_fields("strategy research packet completeness v10 packet", self)
        require_paper_only_flags("packet", self)


@dataclass(frozen=True)
class StrategyResearchPacketCompletenessV10Result:
    generated_at: datetime
    config_version: str
    packet_id: str
    market_slug: str
    research_generated_at: datetime
    source_count: Decimal
    required_source_count: Decimal
    source_quorum_met: bool
    resolution_contract_present: bool
    forecast_rationale_present: bool
    cost_model_present: bool
    risk_sizing_present: bool
    exit_readiness_present: bool
    human_review_status: str
    completeness_score: Decimal
    missing_sections: tuple[str, ...]
    packet_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "research_generated_at",
            _as_utc("research_generated_at", self.research_generated_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_count("required_source_count", self.required_source_count),
        )
        for field_name in (
            "source_quorum_met",
            "resolution_contract_present",
            "forecast_rationale_present",
            "cost_model_present",
            "risk_sizing_present",
            "exit_readiness_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_member(
            "human_review_status",
            self.human_review_status,
            HUMAN_REVIEW_STATUSES,
        )
        object.__setattr__(
            self,
            "completeness_score",
            _normalize_score("completeness_score", self.completeness_score),
        )
        object.__setattr__(
            self,
            "missing_sections",
            _normalize_missing_sections(self.missing_sections),
        )
        _require_member("packet_status", self.packet_status, PACKET_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        reject_unsafe_surface_fields("strategy research packet completeness v10 result", self)
        require_paper_only_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_packet_completeness_v10_payload(self)


def evaluate_strategy_research_packet_completeness_v10(
    packet: StrategyResearchPacketCompletenessV10Packet,
    *,
    generated_at: datetime,
    config_version: str = DEFAULT_CONFIG_VERSION,
) -> StrategyResearchPacketCompletenessV10Result:
    if type(packet) is not StrategyResearchPacketCompletenessV10Packet:
        raise ValueError("packet must be a StrategyResearchPacketCompletenessV10Packet")
    reject_unsafe_surface_fields("strategy research packet completeness v10 packet", packet)
    require_paper_only_flags("packet", packet)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if packet.research_generated_at > generated_at_utc:
        raise ValueError("research_generated_at must not be after generated_at")
    _require_canonical_string("config_version", config_version)

    source_quorum_met = packet.source_count >= packet.required_source_count
    missing_sections = _missing_sections(
        source_quorum_met=source_quorum_met,
        resolution_contract_present=packet.resolution_contract_present,
        forecast_rationale_present=packet.forecast_rationale_present,
        cost_model_present=packet.cost_model_present,
        risk_sizing_present=packet.risk_sizing_present,
        exit_readiness_present=packet.exit_readiness_present,
        human_review_status=packet.human_review_status,
    )
    reason_codes = _reason_codes(missing_sections, packet.human_review_status)
    return StrategyResearchPacketCompletenessV10Result(
        generated_at=generated_at_utc,
        config_version=config_version,
        packet_id=packet.packet_id,
        market_slug=packet.market_slug,
        research_generated_at=packet.research_generated_at,
        source_count=packet.source_count,
        required_source_count=packet.required_source_count,
        source_quorum_met=source_quorum_met,
        resolution_contract_present=packet.resolution_contract_present,
        forecast_rationale_present=packet.forecast_rationale_present,
        cost_model_present=packet.cost_model_present,
        risk_sizing_present=packet.risk_sizing_present,
        exit_readiness_present=packet.exit_readiness_present,
        human_review_status=packet.human_review_status,
        completeness_score=_completeness_score(missing_sections),
        missing_sections=missing_sections,
        packet_status=_packet_status(missing_sections, packet.human_review_status),
        reason_codes=reason_codes,
    )


def strategy_research_packet_completeness_v10_payload(
    result: StrategyResearchPacketCompletenessV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyResearchPacketCompletenessV10Result:
        raise ValueError("result must be a StrategyResearchPacketCompletenessV10Result")
    reject_unsafe_surface_fields("strategy research packet completeness v10 result", result)
    require_paper_only_flags("result", result)
    payload = json_ready_no_floats(result)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _missing_sections(
    *,
    source_quorum_met: bool,
    resolution_contract_present: bool,
    forecast_rationale_present: bool,
    cost_model_present: bool,
    risk_sizing_present: bool,
    exit_readiness_present: bool,
    human_review_status: str,
) -> tuple[str, ...]:
    missing: list[str] = []
    if not resolution_contract_present:
        missing.append("resolution_contract")
    if not source_quorum_met:
        missing.append("source_quorum")
    if not forecast_rationale_present:
        missing.append("forecast_rationale")
    if not cost_model_present:
        missing.append("cost_model")
    if not risk_sizing_present:
        missing.append("risk_sizing")
    if not exit_readiness_present:
        missing.append("exit_readiness")
    if human_review_status != "approved":
        missing.append("human_review_status")
    return _normalize_missing_sections(tuple(missing))


def _reason_codes(
    missing_sections: tuple[str, ...],
    human_review_status: str,
) -> tuple[str, ...]:
    if not missing_sections:
        return ("complete",)
    codes: list[str] = []
    for section in missing_sections:
        if section == "human_review_status":
            if human_review_status == "rejected":
                codes.append("human_review_rejected")
            else:
                codes.append("human_review_not_approved")
        else:
            codes.append(f"{section}_missing")
    return _normalize_reason_codes(tuple(codes))


def _packet_status(
    missing_sections: tuple[str, ...],
    human_review_status: str,
) -> str:
    if human_review_status == "rejected":
        return "rejected"
    if not missing_sections:
        return "complete"
    if any(section in BLOCKING_SECTIONS for section in missing_sections):
        return "blocked"
    return "watch"


def _completeness_score(missing_sections: tuple[str, ...]) -> Decimal:
    completed_count = Decimal(len(SECTION_ORDER) - len(missing_sections))
    total_count = Decimal(len(SECTION_ORDER))
    with localcontext(DECIMAL_CONTEXT):
        return (completed_count / total_count).quantize(SCORE_QUANT)


def _validate_result(result: StrategyResearchPacketCompletenessV10Result) -> None:
    if result.source_quorum_met != (result.source_count >= result.required_source_count):
        raise ValueError("source_quorum_met must match source counts")
    expected_missing_sections = _missing_sections(
        source_quorum_met=result.source_quorum_met,
        resolution_contract_present=result.resolution_contract_present,
        forecast_rationale_present=result.forecast_rationale_present,
        cost_model_present=result.cost_model_present,
        risk_sizing_present=result.risk_sizing_present,
        exit_readiness_present=result.exit_readiness_present,
        human_review_status=result.human_review_status,
    )
    if result.missing_sections != expected_missing_sections:
        raise ValueError("missing_sections must match packet fields")
    if result.reason_codes != _reason_codes(result.missing_sections, result.human_review_status):
        raise ValueError("reason_codes must match missing_sections")
    if result.packet_status != _packet_status(result.missing_sections, result.human_review_status):
        raise ValueError("packet_status must match missing_sections")
    if result.completeness_score != _completeness_score(result.missing_sections):
        raise ValueError("completeness_score must match missing_sections")


def _normalize_missing_sections(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("missing_sections must be a tuple")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("missing_sections", value)
        if value not in SECTION_ORDER:
            raise ValueError("missing_sections contains unsupported value")
        if value in seen:
            raise ValueError("missing_sections contains duplicate value")
        seen.add(value)
    return tuple(value for value in SECTION_ORDER if value in seen)


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


def _normalize_score(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(SCORE_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < Decimal("0.000000") or normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANT)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "HUMAN_REVIEW_STATUSES",
    "PACKET_STATUSES",
    "REASON_CODES",
    "SECTION_ORDER",
    "StrategyResearchPacketCompletenessV10Packet",
    "StrategyResearchPacketCompletenessV10Result",
    "evaluate_strategy_research_packet_completeness_v10",
    "strategy_research_packet_completeness_v10_payload",
)
