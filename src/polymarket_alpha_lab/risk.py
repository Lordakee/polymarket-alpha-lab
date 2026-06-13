"""Paper-only research-packet risk gates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from polymarket_alpha_lab.research import ResearchPacket

ALLOWED_REASON_CODES = {
    "incomplete_packet",
    "low_confidence",
    "low_cost_adjusted_edge",
    "wide_spread",
    "high_slippage",
    "insufficient_executable_size",
    "strategy_not_allowed",
    "blocked_risk_tag",
}

RISK_NUMERIC_FIELDS = (
    "confidence",
    "cost_adjusted_edge",
    "spread",
    "slippage_estimate",
    "max_executable_size",
)


@dataclass(frozen=True)
class RiskGateConfig:
    config_version: str
    min_confidence: Decimal = Decimal("0.50")
    min_cost_adjusted_edge: Decimal = Decimal("0.00")
    max_spread: Decimal = Decimal("0.10")
    max_slippage_estimate: Decimal = Decimal("0.02")
    min_max_executable_size: Decimal = Decimal("1")
    allowed_strategy_types: tuple[str, ...] = ()
    blocked_risk_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "allowed_strategy_types",
            _normalize_string_sequence(
                "allowed_strategy_types",
                self.allowed_strategy_types,
            ),
        )
        object.__setattr__(
            self,
            "blocked_risk_tags",
            _normalize_string_sequence("blocked_risk_tags", self.blocked_risk_tags),
        )
        _validate_config(self)


@dataclass(frozen=True)
class RiskGateReason:
    code: str
    message: str
    field_name: str
    observed_value: Decimal | str | None = None
    threshold: Decimal | str | None = None

    def __post_init__(self) -> None:
        _validate_reason(self)


@dataclass(frozen=True)
class RiskGateDecision:
    accepted: bool
    config_version: str
    reasons: tuple[RiskGateReason, ...]

    def __post_init__(self) -> None:
        try:
            normalized_reasons = tuple(self.reasons)
        except TypeError as exc:
            raise ValueError("reasons must be a sequence of RiskGateReason values") from exc
        object.__setattr__(self, "reasons", normalized_reasons)
        if not isinstance(self.accepted, bool):
            raise ValueError("accepted must be a bool")
        if not isinstance(self.config_version, str) or not self.config_version.strip():
            raise ValueError("config_version is required")
        for reason in self.reasons:
            if not isinstance(reason, RiskGateReason):
                raise ValueError("reasons must contain RiskGateReason values")
        if self.accepted and self.reasons:
            raise ValueError("accepted decisions must not include reasons")
        if not self.accepted and not self.reasons:
            raise ValueError("rejected decisions must include at least one reason")


def evaluate_research_packet_risk(
    packet: ResearchPacket,
    config: RiskGateConfig,
) -> RiskGateDecision:
    if not isinstance(packet, ResearchPacket):
        raise ValueError("packet must be a ResearchPacket")
    if not isinstance(config, RiskGateConfig):
        raise ValueError("config must be a RiskGateConfig")

    missing = _missing_fields_for_risk(packet)
    if missing:
        return RiskGateDecision(
            accepted=False,
            config_version=config.config_version,
            reasons=(
                RiskGateReason(
                    code="incomplete_packet",
                    message="research packet is incomplete",
                    field_name="missing_required_fields",
                    observed_value=",".join(missing),
                ),
            ),
        )

    reasons: list[RiskGateReason] = []

    if config.allowed_strategy_types and packet.strategy_type not in config.allowed_strategy_types:
        reasons.append(
            RiskGateReason(
                code="strategy_not_allowed",
                message="strategy type is not allowed by this gate config",
                field_name="strategy_type",
                observed_value=packet.strategy_type,
                threshold=",".join(config.allowed_strategy_types),
            )
        )

    blocked_tags = set(config.blocked_risk_tags)
    for tag in packet.risk_tags:
        if tag in blocked_tags:
            reasons.append(
                RiskGateReason(
                    code="blocked_risk_tag",
                    message="risk tag is blocked by this gate config",
                    field_name="risk_tags",
                    observed_value=tag,
                    threshold=",".join(config.blocked_risk_tags),
                )
            )

    if packet.confidence < config.min_confidence:
        reasons.append(
            RiskGateReason(
                code="low_confidence",
                message="confidence is below minimum",
                field_name="confidence",
                observed_value=packet.confidence,
                threshold=config.min_confidence,
            )
        )
    if packet.cost_adjusted_edge < config.min_cost_adjusted_edge:
        reasons.append(
            RiskGateReason(
                code="low_cost_adjusted_edge",
                message="cost-adjusted edge is below minimum",
                field_name="cost_adjusted_edge",
                observed_value=packet.cost_adjusted_edge,
                threshold=config.min_cost_adjusted_edge,
            )
        )
    if packet.spread > config.max_spread:
        reasons.append(
            RiskGateReason(
                code="wide_spread",
                message="spread is above maximum",
                field_name="spread",
                observed_value=packet.spread,
                threshold=config.max_spread,
            )
        )
    if packet.slippage_estimate > config.max_slippage_estimate:
        reasons.append(
            RiskGateReason(
                code="high_slippage",
                message="slippage estimate is above maximum",
                field_name="slippage_estimate",
                observed_value=packet.slippage_estimate,
                threshold=config.max_slippage_estimate,
            )
        )
    if packet.max_executable_size < config.min_max_executable_size:
        reasons.append(
            RiskGateReason(
                code="insufficient_executable_size",
                message="maximum executable size is below minimum",
                field_name="max_executable_size",
                observed_value=packet.max_executable_size,
                threshold=config.min_max_executable_size,
            )
        )

    return RiskGateDecision(
        accepted=not reasons,
        config_version=config.config_version,
        reasons=tuple(reasons),
    )


def _validate_config(config: RiskGateConfig) -> None:
    if not isinstance(config.config_version, str) or not config.config_version.strip():
        raise ValueError("config_version is required")
    for field_name, value in (
        ("min_confidence", config.min_confidence),
        ("min_cost_adjusted_edge", config.min_cost_adjusted_edge),
        ("max_spread", config.max_spread),
        ("max_slippage_estimate", config.max_slippage_estimate),
        ("min_max_executable_size", config.min_max_executable_size),
    ):
        if not isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
    if config.min_confidence < 0 or config.min_confidence > 1:
        raise ValueError("min_confidence must be in [0, 1]")
    if config.max_spread <= 0:
        raise ValueError("max_spread must be positive")
    if config.max_slippage_estimate < 0:
        raise ValueError("max_slippage_estimate must be nonnegative")
    if config.min_max_executable_size <= 0:
        raise ValueError("min_max_executable_size must be positive")


def _validate_reason(reason: RiskGateReason) -> None:
    if not isinstance(reason.code, str):
        raise ValueError("risk gate reason code must be a string")
    if reason.code not in ALLOWED_REASON_CODES:
        raise ValueError("risk gate reason code is not recognized")
    if not isinstance(reason.message, str) or not reason.message.strip():
        raise ValueError("risk gate reason message is required")
    if not isinstance(reason.field_name, str) or not reason.field_name.strip():
        raise ValueError("risk gate reason field_name is required")
    for field_name, value in (
        ("observed_value", reason.observed_value),
        ("threshold", reason.threshold),
    ):
        if value is not None and not isinstance(value, (Decimal, str)):
            raise ValueError(f"risk gate reason {field_name} must be a Decimal or string")


def _missing_fields_for_risk(packet: ResearchPacket) -> tuple[str, ...]:
    numeric_missing = _risk_numeric_missing_fields(packet)
    try:
        level_1a_missing = tuple(packet.missing_required_fields())
    except (AttributeError, TypeError) as exc:
        if numeric_missing:
            return _ordered_unique(numeric_missing)
        raise ValueError("research packet completeness could not be evaluated") from exc
    if "max_executable_size" in numeric_missing:
        level_1a_missing = tuple(
            field_name
            for field_name in level_1a_missing
            if field_name != "positive_max_executable_size"
        )
    return _ordered_unique((*level_1a_missing, *numeric_missing))


def _risk_numeric_missing_fields(packet: ResearchPacket) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in RISK_NUMERIC_FIELDS:
        value = getattr(packet, field_name)
        if not isinstance(value, Decimal) or not value.is_finite():
            missing.append(field_name)
    return tuple(missing)


def _normalize_string_sequence(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    for item in normalized:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain nonblank strings")
    return normalized


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
