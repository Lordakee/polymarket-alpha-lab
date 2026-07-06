"""Pure report-only reasoner for probability forecast revision explanations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_PROBABILITY_FORECAST_REVISION_REASONER_V10_CONFIG_VERSION = (
    "strategy-probability-forecast-revision-reasoner-v10"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_BPS_PER_PROBABILITY_POINT = Decimal("10000.000000")

_SOURCE_FRESHNESS_STATUSES = ("fresh", "stale", "missing")
_RESOLUTION_RISK_TIERS = ("low", "medium", "high", "blocked")
_REVISION_STATUSES = (
    "revision_required",
    "revision_watch",
    "revision_blocked",
    "no_revision_needed",
)
_ALLOWED_REASON_CODES = frozenset(
    (
        "probability_delta_material",
        "probability_delta_immaterial",
        "source_updates_available",
        "no_source_updates",
        "market_move_material",
        "market_move_immaterial",
        "model_disagreement_high",
        "model_disagreement_low",
        "fresh_sources",
        "source_stale",
        "source_missing",
        "resolution_risk_low",
        "resolution_risk_medium",
        "resolution_risk_high",
        "resolution_risk_blocked",
        *_REVISION_STATUSES,
    )
)


@dataclass(frozen=True)
class StrategyProbabilityForecastRevisionReasonerV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_FORECAST_REVISION_REASONER_V10_CONFIG_VERSION
    )
    material_revision_delta_bps: Decimal = Decimal("100.000000")
    material_market_move_bps: Decimal = Decimal("100.000000")
    high_model_disagreement_score: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityForecastRevisionReasonerV10Config:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_FORECAST_REVISION_REASONER_V10_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "material_revision_delta_bps",
            _require_positive_decimal(
                "material_revision_delta_bps",
                self.material_revision_delta_bps,
            ),
        )
        object.__setattr__(
            self,
            "material_market_move_bps",
            _require_positive_decimal(
                "material_market_move_bps",
                self.material_market_move_bps,
            ),
        )
        object.__setattr__(
            self,
            "high_model_disagreement_score",
            _normalize_probability(
                "high_model_disagreement_score",
                self.high_model_disagreement_score,
            ),
        )
        reject_unsafe_surface_fields(
            "strategy probability forecast revision reasoner v10 config",
            self,
        )
        require_paper_only_flags(
            "StrategyProbabilityForecastRevisionReasonerV10Config",
            self,
        )


@dataclass(frozen=True)
class StrategyProbabilityForecastRevisionReasonerV10Input:
    market_id: str
    previous_probability: Decimal
    new_probability: Decimal
    source_update_count: Decimal
    market_move_bps: Decimal
    model_disagreement_score: Decimal
    source_freshness_status: str
    resolution_risk_tier: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityForecastRevisionReasonerV10Input:
            raise ValueError("revision input must be exact")
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "previous_probability",
            _normalize_probability("previous_probability", self.previous_probability),
        )
        object.__setattr__(
            self,
            "new_probability",
            _normalize_probability("new_probability", self.new_probability),
        )
        object.__setattr__(
            self,
            "source_update_count",
            _normalize_nonnegative_count(
                "source_update_count",
                self.source_update_count,
            ),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_signed_decimal("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "model_disagreement_score",
            _normalize_probability(
                "model_disagreement_score",
                self.model_disagreement_score,
            ),
        )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            _SOURCE_FRESHNESS_STATUSES,
        )
        _require_member(
            "resolution_risk_tier",
            self.resolution_risk_tier,
            _RESOLUTION_RISK_TIERS,
        )
        reject_unsafe_surface_fields(
            "strategy probability forecast revision reasoner v10 input",
            self,
        )
        require_paper_only_flags(
            "StrategyProbabilityForecastRevisionReasonerV10Input",
            self,
        )


@dataclass(frozen=True)
class StrategyProbabilityForecastRevisionReasonerV10Report:
    market_id: str
    previous_probability: Decimal
    new_probability: Decimal
    source_update_count: Decimal
    market_move_bps: Decimal
    model_disagreement_score: Decimal
    source_freshness_status: str
    resolution_risk_tier: str
    revision_status: str
    revision_delta_bps: Decimal
    revision_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityForecastRevisionReasonerV10Report:
            raise ValueError("revision report must be exact")
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("previous_probability", "new_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_update_count",
            _normalize_nonnegative_count(
                "source_update_count",
                self.source_update_count,
            ),
        )
        for field_name in ("market_move_bps", "revision_delta_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "model_disagreement_score",
            _normalize_probability(
                "model_disagreement_score",
                self.model_disagreement_score,
            ),
        )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            _SOURCE_FRESHNESS_STATUSES,
        )
        _require_member(
            "resolution_risk_tier",
            self.resolution_risk_tier,
            _RESOLUTION_RISK_TIERS,
        )
        _require_member("revision_status", self.revision_status, _REVISION_STATUSES)
        object.__setattr__(
            self,
            "revision_reasons",
            _normalize_string_tuple("revision_reasons", self.revision_reasons),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload(self.payload))
        reject_unsafe_surface_fields(
            "strategy probability forecast revision reasoner v10 report",
            self,
        )
        require_paper_only_flags(
            "StrategyProbabilityForecastRevisionReasonerV10Report",
            self,
        )
        _validate_report_consistency(self)


def build_strategy_probability_forecast_revision_reasoner_v10(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
    *,
    config: StrategyProbabilityForecastRevisionReasonerV10Config | None = None,
) -> StrategyProbabilityForecastRevisionReasonerV10Report:
    if type(revision_input) is not StrategyProbabilityForecastRevisionReasonerV10Input:
        raise ValueError(
            "revision_input must be a StrategyProbabilityForecastRevisionReasonerV10Input",
        )
    require_paper_only_flags(
        "StrategyProbabilityForecastRevisionReasonerV10Input",
        revision_input,
    )
    cfg = config or StrategyProbabilityForecastRevisionReasonerV10Config()
    if type(cfg) is not StrategyProbabilityForecastRevisionReasonerV10Config:
        raise ValueError(
            "config must be a StrategyProbabilityForecastRevisionReasonerV10Config",
        )
    require_paper_only_flags("StrategyProbabilityForecastRevisionReasonerV10Config", cfg)

    revision_delta_bps = _revision_delta_bps(
        revision_input.previous_probability,
        revision_input.new_probability,
    )
    reason_codes = _reason_codes(
        revision_input,
        revision_delta_bps=revision_delta_bps,
        config=cfg,
    )
    revision_status = _revision_status(revision_input, reason_codes)
    reason_codes = (*reason_codes, revision_status)
    revision_reasons = _revision_reasons(
        revision_input,
        revision_delta_bps=revision_delta_bps,
        revision_status=revision_status,
        config=cfg,
    )

    payload = _build_payload(
        revision_input,
        revision_status=revision_status,
        revision_delta_bps=revision_delta_bps,
        revision_reasons=revision_reasons,
        reason_codes=reason_codes,
    )

    return StrategyProbabilityForecastRevisionReasonerV10Report(
        market_id=revision_input.market_id,
        previous_probability=revision_input.previous_probability,
        new_probability=revision_input.new_probability,
        source_update_count=revision_input.source_update_count,
        market_move_bps=revision_input.market_move_bps,
        model_disagreement_score=revision_input.model_disagreement_score,
        source_freshness_status=revision_input.source_freshness_status,
        resolution_risk_tier=revision_input.resolution_risk_tier,
        revision_status=revision_status,
        revision_delta_bps=revision_delta_bps,
        revision_reasons=revision_reasons,
        reason_codes=reason_codes,
        payload=payload,
    )


def strategy_probability_forecast_revision_reasoner_v10_payload(
    report: StrategyProbabilityForecastRevisionReasonerV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyProbabilityForecastRevisionReasonerV10Report:
        raise ValueError(
            "report must be a StrategyProbabilityForecastRevisionReasonerV10Report",
        )
    require_paper_only_flags(
        "StrategyProbabilityForecastRevisionReasonerV10Report",
        report,
    )
    return _normalize_payload(report.payload)


def _revision_delta_bps(previous_probability: Decimal, new_probability: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_signed_decimal(
            "revision_delta_bps",
            (new_probability - previous_probability) * _BPS_PER_PROBABILITY_POINT,
        )


def _reason_codes(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
    *,
    revision_delta_bps: Decimal,
    config: StrategyProbabilityForecastRevisionReasonerV10Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs(revision_delta_bps) >= config.material_revision_delta_bps:
        reason_codes.append("probability_delta_material")
    else:
        reason_codes.append("probability_delta_immaterial")

    if revision_input.source_update_count > _ZERO:
        reason_codes.append("source_updates_available")
    else:
        reason_codes.append("no_source_updates")

    if abs(revision_input.market_move_bps) >= config.material_market_move_bps:
        reason_codes.append("market_move_material")
    else:
        reason_codes.append("market_move_immaterial")

    if revision_input.model_disagreement_score >= config.high_model_disagreement_score:
        reason_codes.append("model_disagreement_high")
    else:
        reason_codes.append("model_disagreement_low")

    reason_codes.append(_source_freshness_reason_code(revision_input))
    reason_codes.append(f"resolution_risk_{revision_input.resolution_risk_tier}")
    return tuple(reason_codes)


def _revision_status(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
    reason_codes: tuple[str, ...],
) -> str:
    if revision_input.resolution_risk_tier == "blocked":
        return "revision_blocked"
    if (
        "probability_delta_material" in reason_codes
        and "source_updates_available" in reason_codes
        and revision_input.source_freshness_status == "fresh"
        and revision_input.resolution_risk_tier in ("low", "medium")
    ):
        return "revision_required"
    if (
        "probability_delta_material" in reason_codes
        or "source_updates_available" in reason_codes
        or "market_move_material" in reason_codes
        or "model_disagreement_high" in reason_codes
        or revision_input.source_freshness_status != "fresh"
        or revision_input.resolution_risk_tier == "high"
    ):
        return "revision_watch"
    return "no_revision_needed"


def _revision_reasons(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
    *,
    revision_delta_bps: Decimal,
    revision_status: str,
    config: StrategyProbabilityForecastRevisionReasonerV10Config,
) -> tuple[str, ...]:
    reasons = [
        _probability_delta_reason(
            revision_delta_bps,
            material=abs(revision_delta_bps) >= config.material_revision_delta_bps,
        ),
        _source_update_reason(revision_input.source_update_count),
        _market_move_reason(
            revision_input.market_move_bps,
            material=abs(revision_input.market_move_bps)
            >= config.material_market_move_bps,
        ),
        _model_disagreement_reason(
            revision_input.model_disagreement_score,
            high=revision_input.model_disagreement_score
            >= config.high_model_disagreement_score,
        ),
        _source_freshness_reason(revision_input, revision_status),
        _resolution_risk_reason(revision_input.resolution_risk_tier),
    ]
    return tuple(reasons)


def _probability_delta_reason(revision_delta_bps: Decimal, *, material: bool) -> str:
    formatted = _format_signed_decimal(revision_delta_bps)
    if material:
        return f"Probability forecast changed by {formatted} bps."
    return f"Probability forecast changed by {formatted} bps, below material threshold."


def _source_update_reason(source_update_count: Decimal) -> str:
    if source_update_count > _ZERO:
        return f"{source_update_count} source updates support reassessment."
    return "No source updates supplied."


def _market_move_reason(market_move_bps: Decimal, *, material: bool) -> str:
    if material:
        return f"Market price moved {market_move_bps} bps."
    return "Market price move is below material threshold."


def _model_disagreement_reason(
    model_disagreement_score: Decimal,
    *,
    high: bool,
) -> str:
    if high:
        return (
            f"Model disagreement score {model_disagreement_score} "
            "exceeds review threshold."
        )
    return "Model disagreement score is below review threshold."


def _source_freshness_reason(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
    revision_status: str,
) -> str:
    if revision_input.source_freshness_status == "fresh":
        if revision_status == "no_revision_needed":
            return "Fresh source context supports no revision."
        return "Fresh source context supports revision."
    if revision_input.source_freshness_status == "stale":
        return "Source context is stale; refresh evidence before a required revision."
    return "Source context is missing; refresh evidence before a required revision."


def _resolution_risk_reason(resolution_risk_tier: str) -> str:
    if resolution_risk_tier == "low":
        return "Resolution risk is low."
    if resolution_risk_tier == "medium":
        return "Resolution risk is medium; revise with caution."
    if resolution_risk_tier == "high":
        return "Resolution risk is high; keep the revision on watch."
    return "Resolution risk is blocked; do not treat the forecast change as actionable."


def _source_freshness_reason_code(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
) -> str:
    if revision_input.source_freshness_status == "fresh":
        return "fresh_sources"
    if revision_input.source_freshness_status == "stale":
        return "source_stale"
    return "source_missing"


def _build_payload(
    revision_input: StrategyProbabilityForecastRevisionReasonerV10Input,
    *,
    revision_status: str,
    revision_delta_bps: Decimal,
    revision_reasons: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    payload = {
        "market_id": revision_input.market_id,
        "previous_probability": revision_input.previous_probability,
        "new_probability": revision_input.new_probability,
        "source_update_count": revision_input.source_update_count,
        "market_move_bps": revision_input.market_move_bps,
        "model_disagreement_score": revision_input.model_disagreement_score,
        "source_freshness_status": revision_input.source_freshness_status,
        "resolution_risk_tier": revision_input.resolution_risk_tier,
        "revision_status": revision_status,
        "revision_delta_bps": revision_delta_bps,
        "revision_reasons": revision_reasons,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return _normalize_payload(payload)


def _validate_report_consistency(
    report: StrategyProbabilityForecastRevisionReasonerV10Report,
) -> None:
    expected_delta = _revision_delta_bps(
        report.previous_probability,
        report.new_probability,
    )
    if report.revision_delta_bps != expected_delta:
        raise ValueError("revision_delta_bps must match probability difference")
    if not report.revision_reasons:
        raise ValueError("revision_reasons must not be empty")
    if report.reason_codes[-1] != report.revision_status:
        raise ValueError("reason_codes must end with revision_status")
    if report.revision_status == "revision_blocked" and (
        "resolution_risk_blocked" not in report.reason_codes
    ):
        raise ValueError("revision_blocked requires blocked resolution risk")
    expected_payload = _build_payload(
        StrategyProbabilityForecastRevisionReasonerV10Input(
            market_id=report.market_id,
            previous_probability=report.previous_probability,
            new_probability=report.new_probability,
            source_update_count=report.source_update_count,
            market_move_bps=report.market_move_bps,
            model_disagreement_score=report.model_disagreement_score,
            source_freshness_status=report.source_freshness_status,
            resolution_risk_tier=report.resolution_risk_tier,
        ),
        revision_status=report.revision_status,
        revision_delta_bps=report.revision_delta_bps,
        revision_reasons=report.revision_reasons,
        reason_codes=report.reason_codes,
    )
    if report.payload != expected_payload:
        raise ValueError("payload must match report fields")


def _normalize_payload(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    normalized = json_ready_no_floats(value)
    if type(normalized) is not dict:
        raise ValueError("payload must be a dict")
    reject_unsafe_surface_fields(
        "strategy probability forecast revision reasoner v10 payload",
        normalized,
    )
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    items = _normalize_string_tuple("reason_codes", value)
    if not items:
        raise ValueError("reason_codes must not be empty")
    for item in items:
        if item not in _ALLOWED_REASON_CODES:
            raise ValueError("reason_codes must be recognized")
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    return items


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


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_signed_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_signed_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_COUNT_QUANTUM)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _format_signed_decimal(value: Decimal) -> str:
    if value >= _ZERO:
        return f"+{value}"
    return str(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_FORECAST_REVISION_REASONER_V10_CONFIG_VERSION",
    "StrategyProbabilityForecastRevisionReasonerV10Config",
    "StrategyProbabilityForecastRevisionReasonerV10Input",
    "StrategyProbabilityForecastRevisionReasonerV10Report",
    "build_strategy_probability_forecast_revision_reasoner_v10",
    "strategy_probability_forecast_revision_reasoner_v10_payload",
)
