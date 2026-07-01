"""Paper-only team forecast packets and side-edge adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeInput,
)
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = frozenset(("yes", "no"))
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class TeamForecastEvidencePacket:
    evidence_id: str
    team_id: str
    market_slug: str
    source_id: str
    source_type: str
    data_timestamp: datetime
    data_freshness_seconds: int
    evidence_type: str
    evidence_text: str
    weight: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "evidence_id",
            "market_slug",
            "source_id",
            "source_type",
            "evidence_type",
            "evidence_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_nonnegative_int(
            "data_freshness_seconds",
            self.data_freshness_seconds,
        )
        object.__setattr__(
            self,
            "weight",
            _normalize_probability("weight", self.weight),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("team forecast evidence packet", self)


@dataclass(frozen=True)
class TeamForecastPacket:
    forecast_id: str
    team_id: str
    condition_id: str
    market_slug: str
    question: str
    category_id: str
    event_template: str
    selected_side: str
    forecast_probability: Decimal
    confidence: Decimal
    evidence_quality: Decimal
    data_freshness_score: Decimal
    resolution_risk: Decimal
    base_rate: Decimal
    market_implied_probability_observed: Decimal
    reason_codes: tuple[str, ...]
    memory_references: tuple[str, ...]
    source_references: tuple[str, ...]
    known_failure_modes: tuple[str, ...]
    config_version: str
    prompt_version: str
    generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_id",
            "condition_id",
            "market_slug",
            "question",
            "event_template",
            "config_version",
            "prompt_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        if self.selected_side not in SIDES:
            raise ValueError("selected_side must be yes or no")
        for field_name in (
            "forecast_probability",
            "confidence",
            "evidence_quality",
            "data_freshness_score",
            "resolution_risk",
            "base_rate",
            "market_implied_probability_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "memory_references",
            "source_references",
            "known_failure_modes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        require_paper_only_flags("team forecast packet", self)


@dataclass(frozen=True)
class TeamForecastCostInterfaceInput:
    side_price: Decimal
    fee_cost_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal
    capital_cost_per_share: Decimal
    requested_paper_shares: Decimal
    max_executable_shares: Decimal
    market_context_fresh: bool
    settlement_context_fresh: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "side_price",
            _normalize_probability("side_price", self.side_price),
        )
        for field_name in (
            "fee_cost_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "funding_cost_per_share",
            "finalization_cost_per_share",
            "time_cost_per_share",
            "risk_cost_per_share",
            "capital_cost_per_share",
            "requested_paper_shares",
            "max_executable_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("market_context_fresh", self.market_context_fresh)
        _require_bool("settlement_context_fresh", self.settlement_context_fresh)
        require_paper_only_flags("team forecast cost interface input", self)


def team_forecast_to_side_edge_input(
    forecast: TeamForecastPacket,
    *,
    cost_input: TeamForecastCostInterfaceInput,
) -> PaperProbabilitySideEdgeInput:
    if type(forecast) is not TeamForecastPacket:
        raise ValueError("forecast must be a TeamForecastPacket")
    if type(cost_input) is not TeamForecastCostInterfaceInput:
        raise ValueError("cost_input must be a TeamForecastCostInterfaceInput")
    require_paper_only_flags("team forecast packet", forecast)
    require_paper_only_flags("team forecast cost interface input", cost_input)

    return PaperProbabilitySideEdgeInput(
        market_slug=forecast.market_slug,
        question=forecast.question,
        side=forecast.selected_side,
        forecast_probability=forecast.forecast_probability,
        side_price=cost_input.side_price,
        fee_cost_per_share=cost_input.fee_cost_per_share,
        spread_cost_per_share=cost_input.spread_cost_per_share,
        slippage_cost_per_share=cost_input.slippage_cost_per_share,
        funding_cost_per_share=cost_input.funding_cost_per_share,
        finalization_cost_per_share=cost_input.finalization_cost_per_share,
        time_cost_per_share=cost_input.time_cost_per_share,
        risk_cost_per_share=cost_input.risk_cost_per_share,
        capital_cost_per_share=cost_input.capital_cost_per_share,
        requested_paper_shares=cost_input.requested_paper_shares,
        max_executable_shares=cost_input.max_executable_shares,
        market_context_fresh=cost_input.market_context_fresh,
        settlement_context_fresh=cost_input.settlement_context_fresh,
        reason_codes=(
            *forecast.reason_codes,
            f"team_{forecast.team_id}",
        ),
    )


def team_forecast_packet_payload(value: object) -> dict[str, Any]:
    if isinstance(value, (TeamForecastPacket, TeamForecastEvidencePacket)):
        require_paper_only_flags("team forecast packet payload", value)
    elif not isinstance(value, dict):
        raise ValueError(
            "value must be a TeamForecastPacket, TeamForecastEvidencePacket, or JSON object",
        )

    reject_unsafe_surface_fields("team forecast packet payload", value)
    payload = json_ready_no_floats(value)
    if not isinstance(payload, dict):
        raise ValueError("team forecast packet payload must be a JSON object")
    _validate_payload_safety_flags(payload, "payload")
    reject_unsafe_surface_fields("team forecast packet payload", payload)
    return payload


def _validate_payload_safety_flags(value: object, field_path: str) -> None:
    if isinstance(value, dict):
        for flag_name in SAFETY_FLAG_NAMES:
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{field_path} {flag_name} must be True")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _validate_payload_safety_flags(item, f"{field_path} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_safety_flags(item, f"{field_path} {index}")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    items = _normalize_string_tuple("reason_codes", value)
    return tuple(sorted(set(items)))


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "TeamForecastCostInterfaceInput",
    "TeamForecastEvidencePacket",
    "TeamForecastPacket",
    "team_forecast_packet_payload",
    "team_forecast_to_side_edge_input",
)
