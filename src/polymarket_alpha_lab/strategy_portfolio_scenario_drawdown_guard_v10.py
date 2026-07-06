"""Pure portfolio scenario drawdown guard scoring for paper reports."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

LOW_SCENARIO_LOSS = Decimal("0.080000")
WATCH_SCENARIO_LOSS = Decimal("0.200000")
LOW_CATEGORY_CONCENTRATION = Decimal("0.250000")
WATCH_CATEGORY_CONCENTRATION = Decimal("0.400000")
LOW_CORRELATED_EVENT_EXPOSURE = Decimal("0.200000")
WATCH_CORRELATED_EVENT_EXPOSURE = Decimal("0.350000")
LOW_LIQUIDITY_EXIT_STRESS = Decimal("0.200000")
WATCH_LIQUIDITY_EXIT_STRESS = Decimal("0.400000")
STRONG_CALIBRATION_CONFIDENCE = Decimal("0.850000")
WATCH_CALIBRATION_CONFIDENCE = Decimal("0.650000")

GUARD_STATUSES = ("pass", "watch", "blocked")
RECOMMENDED_ACTIONS = (
    "allow_paper_exposure",
    "reduce_paper_exposure",
    "block_paper_exposure",
)


@dataclass(frozen=True)
class PortfolioScenarioDrawdownGuardV10Config:
    scenario_loss_weight: Decimal = Decimal("0.350000")
    category_concentration_weight: Decimal = Decimal("0.200000")
    correlated_event_exposure_weight: Decimal = Decimal("0.200000")
    liquidity_exit_stress_weight: Decimal = Decimal("0.150000")
    calibration_confidence_gap_weight: Decimal = Decimal("0.100000")
    watch_guard_score: Decimal = Decimal("0.150000")
    block_guard_score: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "scenario_loss_weight",
            "category_concentration_weight",
            "correlated_event_exposure_weight",
            "liquidity_exit_stress_weight",
            "calibration_confidence_gap_weight",
            "watch_guard_score",
            "block_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("PortfolioScenarioDrawdownGuardV10Config", self)


@dataclass(frozen=True)
class PortfolioScenarioDrawdownGuardV10Input:
    portfolio_id: str
    scenario_id: str
    scenario_loss_ratio: Decimal
    category_concentration_ratio: Decimal
    correlated_event_exposure_ratio: Decimal
    liquidity_exit_stress_ratio: Decimal
    calibration_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "portfolio_id",
            _require_non_empty_string("portfolio_id", self.portfolio_id),
        )
        object.__setattr__(
            self,
            "scenario_id",
            _require_non_empty_string("scenario_id", self.scenario_id),
        )
        for field_name in (
            "scenario_loss_ratio",
            "category_concentration_ratio",
            "correlated_event_exposure_ratio",
            "liquidity_exit_stress_ratio",
            "calibration_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("PortfolioScenarioDrawdownGuardV10Input", self)


@dataclass(frozen=True)
class PortfolioScenarioDrawdownGuardV10Result:
    portfolio_id: str
    scenario_id: str
    drawdown_guard_score: Decimal
    guard_status: str
    recommended_action: str
    scenario_loss_component: Decimal
    category_concentration_component: Decimal
    correlated_event_exposure_component: Decimal
    liquidity_exit_stress_component: Decimal
    calibration_confidence_gap_component: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "portfolio_id",
            _require_non_empty_string("portfolio_id", self.portfolio_id),
        )
        object.__setattr__(
            self,
            "scenario_id",
            _require_non_empty_string("scenario_id", self.scenario_id),
        )
        for field_name in (
            "drawdown_guard_score",
            "scenario_loss_component",
            "category_concentration_component",
            "correlated_event_exposure_component",
            "liquidity_exit_stress_component",
            "calibration_confidence_gap_component",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.guard_status not in GUARD_STATUSES:
            raise ValueError("guard_status must be pass, watch, or blocked")
        if self.recommended_action not in RECOMMENDED_ACTIONS:
            raise ValueError(
                "recommended_action must be allow, reduce, or block paper exposure",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _result_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_result_components(self)
        require_paper_only_flags("PortfolioScenarioDrawdownGuardV10Result", self)
        _validate_result_derived_fields(self)

    @property
    def payload(self) -> dict[str, Any]:
        return portfolio_scenario_drawdown_guard_v10_payload(self)


def evaluate_portfolio_scenario_drawdown_guard_v10(
    exposure: PortfolioScenarioDrawdownGuardV10Input,
    config: PortfolioScenarioDrawdownGuardV10Config | None = None,
) -> PortfolioScenarioDrawdownGuardV10Result:
    if type(exposure) is not PortfolioScenarioDrawdownGuardV10Input:
        raise ValueError("exposure must be a PortfolioScenarioDrawdownGuardV10Input")
    if config is None:
        config = PortfolioScenarioDrawdownGuardV10Config()
    if type(config) is not PortfolioScenarioDrawdownGuardV10Config:
        raise ValueError("config must be a PortfolioScenarioDrawdownGuardV10Config")
    require_paper_only_flags("PortfolioScenarioDrawdownGuardV10Input", exposure)
    require_paper_only_flags("PortfolioScenarioDrawdownGuardV10Config", config)

    scenario_loss_component = _weighted_component(
        exposure.scenario_loss_ratio,
        config.scenario_loss_weight,
    )
    category_concentration_component = _weighted_component(
        exposure.category_concentration_ratio,
        config.category_concentration_weight,
    )
    correlated_event_exposure_component = _weighted_component(
        exposure.correlated_event_exposure_ratio,
        config.correlated_event_exposure_weight,
    )
    liquidity_exit_stress_component = _weighted_component(
        exposure.liquidity_exit_stress_ratio,
        config.liquidity_exit_stress_weight,
    )
    calibration_confidence_gap_component = _weighted_component(
        ONE - exposure.calibration_confidence,
        config.calibration_confidence_gap_weight,
    )
    drawdown_guard_score = _clamp_ratio(
        scenario_loss_component
        + category_concentration_component
        + correlated_event_exposure_component
        + liquidity_exit_stress_component
        + calibration_confidence_gap_component,
    )
    guard_status = _guard_status(drawdown_guard_score, config)
    recommended_action = _recommended_action(guard_status)

    return PortfolioScenarioDrawdownGuardV10Result(
        portfolio_id=exposure.portfolio_id,
        scenario_id=exposure.scenario_id,
        drawdown_guard_score=drawdown_guard_score,
        guard_status=guard_status,
        recommended_action=recommended_action,
        scenario_loss_component=scenario_loss_component,
        category_concentration_component=category_concentration_component,
        correlated_event_exposure_component=correlated_event_exposure_component,
        liquidity_exit_stress_component=liquidity_exit_stress_component,
        calibration_confidence_gap_component=calibration_confidence_gap_component,
        reason_codes=(
            f"portfolio_scenario_drawdown_guard_{guard_status}",
            _scenario_loss_reason(exposure.scenario_loss_ratio),
            _category_concentration_reason(exposure.category_concentration_ratio),
            _correlated_event_exposure_reason(
                exposure.correlated_event_exposure_ratio,
            ),
            _liquidity_exit_stress_reason(exposure.liquidity_exit_stress_ratio),
            _calibration_confidence_reason(exposure.calibration_confidence),
            _action_reason(recommended_action),
        ),
    )


def portfolio_scenario_drawdown_guard_v10_payload(
    result: PortfolioScenarioDrawdownGuardV10Result,
) -> dict[str, Any]:
    if type(result) is not PortfolioScenarioDrawdownGuardV10Result:
        raise ValueError("result must be a PortfolioScenarioDrawdownGuardV10Result")
    require_paper_only_flags("PortfolioScenarioDrawdownGuardV10Result", result)
    _validate_result_components(result)
    _validate_result_derived_fields(result)
    payload = {
        "portfolio_id": result.portfolio_id,
        "scenario_id": result.scenario_id,
        "drawdown_guard_score": _decimal_payload(result.drawdown_guard_score),
        "guard_status": result.guard_status,
        "recommended_action": result.recommended_action,
        "scenario_loss_component": _decimal_payload(
            result.scenario_loss_component,
        ),
        "category_concentration_component": _decimal_payload(
            result.category_concentration_component,
        ),
        "correlated_event_exposure_component": _decimal_payload(
            result.correlated_event_exposure_component,
        ),
        "liquidity_exit_stress_component": _decimal_payload(
            result.liquidity_exit_stress_component,
        ),
        "calibration_confidence_gap_component": _decimal_payload(
            result.calibration_confidence_gap_component,
        ),
        "reason_codes": list(result.reason_codes),
        "derived_validation_digest": result.derived_validation_digest,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    validate_portfolio_scenario_drawdown_guard_v10_public_payload(payload)
    return payload


def validate_portfolio_scenario_drawdown_guard_v10_public_payload(
    payload: object,
) -> None:
    reject_unsafe_surface_fields(
        "portfolio scenario drawdown guard public payload",
        payload,
    )
    _require_safe_payload(payload)


def _weighted_component(value: Decimal, weight: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value * weight)


def _guard_status(
    drawdown_guard_score: Decimal,
    config: PortfolioScenarioDrawdownGuardV10Config,
) -> str:
    if drawdown_guard_score >= config.block_guard_score:
        return "blocked"
    if drawdown_guard_score >= config.watch_guard_score:
        return "watch"
    return "pass"


def _recommended_action(guard_status: str) -> str:
    if guard_status == "blocked":
        return "block_paper_exposure"
    if guard_status == "watch":
        return "reduce_paper_exposure"
    return "allow_paper_exposure"


def _action_reason(recommended_action: str) -> str:
    if recommended_action == "block_paper_exposure":
        return "paper_exposure_action_block"
    if recommended_action == "reduce_paper_exposure":
        return "paper_exposure_action_reduce"
    return "paper_exposure_action_allow"


def _scenario_loss_reason(scenario_loss_ratio: Decimal) -> str:
    if scenario_loss_ratio <= LOW_SCENARIO_LOSS:
        return "scenario_loss_low"
    if scenario_loss_ratio <= WATCH_SCENARIO_LOSS:
        return "scenario_loss_watch"
    return "scenario_loss_high"


def _category_concentration_reason(category_concentration_ratio: Decimal) -> str:
    if category_concentration_ratio <= LOW_CATEGORY_CONCENTRATION:
        return "category_concentration_low"
    if category_concentration_ratio <= WATCH_CATEGORY_CONCENTRATION:
        return "category_concentration_watch"
    return "category_concentration_high"


def _correlated_event_exposure_reason(
    correlated_event_exposure_ratio: Decimal,
) -> str:
    if correlated_event_exposure_ratio <= LOW_CORRELATED_EVENT_EXPOSURE:
        return "correlated_event_exposure_low"
    if correlated_event_exposure_ratio <= WATCH_CORRELATED_EVENT_EXPOSURE:
        return "correlated_event_exposure_watch"
    return "correlated_event_exposure_high"


def _liquidity_exit_stress_reason(liquidity_exit_stress_ratio: Decimal) -> str:
    if liquidity_exit_stress_ratio <= LOW_LIQUIDITY_EXIT_STRESS:
        return "liquidity_exit_stress_low"
    if liquidity_exit_stress_ratio <= WATCH_LIQUIDITY_EXIT_STRESS:
        return "liquidity_exit_stress_watch"
    return "liquidity_exit_stress_high"


def _calibration_confidence_reason(calibration_confidence: Decimal) -> str:
    if calibration_confidence >= STRONG_CALIBRATION_CONFIDENCE:
        return "calibration_confidence_strong"
    if calibration_confidence >= WATCH_CALIBRATION_CONFIDENCE:
        return "calibration_confidence_watch"
    return "calibration_confidence_low"


def _validate_config(config: PortfolioScenarioDrawdownGuardV10Config) -> None:
    weights_total = (
        config.scenario_loss_weight
        + config.category_concentration_weight
        + config.correlated_event_exposure_weight
        + config.liquidity_exit_stress_weight
        + config.calibration_confidence_gap_weight
    ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("drawdown guard weights must sum to 1.000000")
    if config.watch_guard_score > config.block_guard_score:
        raise ValueError("watch_guard_score must not exceed block_guard_score")


def _validate_result_components(
    result: PortfolioScenarioDrawdownGuardV10Result,
) -> None:
    component_total = _clamp_ratio(
        result.scenario_loss_component
        + result.category_concentration_component
        + result.correlated_event_exposure_component
        + result.liquidity_exit_stress_component
        + result.calibration_confidence_gap_component,
    )
    if result.drawdown_guard_score != component_total:
        raise ValueError("drawdown_guard_score must match component total")


def _validate_result_derived_fields(
    result: PortfolioScenarioDrawdownGuardV10Result,
) -> None:
    if result.recommended_action != _recommended_action(result.guard_status):
        raise ValueError("recommended_action must match guard_status")
    expected_status_reason = f"portfolio_scenario_drawdown_guard_{result.guard_status}"
    if result.reason_codes[0] != expected_status_reason:
        raise ValueError("reason_codes must match guard status")
    if result.reason_codes[-1] != _action_reason(result.recommended_action):
        raise ValueError("reason_codes must match recommended action")
    if result.derived_validation_digest != _result_derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _result_derived_validation_digest(
    result: PortfolioScenarioDrawdownGuardV10Result,
) -> str:
    return _sha256(
        (
            "portfolio_scenario_drawdown_guard_v10_result",
            f"portfolio_id={result.portfolio_id}",
            f"scenario_id={result.scenario_id}",
            f"drawdown_guard_score={_decimal_payload(result.drawdown_guard_score)}",
            f"guard_status={result.guard_status}",
            f"recommended_action={result.recommended_action}",
            f"scenario_loss_component={_decimal_payload(result.scenario_loss_component)}",
            "category_concentration_component="
            f"{_decimal_payload(result.category_concentration_component)}",
            "correlated_event_exposure_component="
            f"{_decimal_payload(result.correlated_event_exposure_component)}",
            "liquidity_exit_stress_component="
            f"{_decimal_payload(result.liquidity_exit_stress_component)}",
            "calibration_confidence_gap_component="
            f"{_decimal_payload(result.calibration_confidence_gap_component)}",
            f"reason_codes={','.join(result.reason_codes)}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return value.quantize(SCORE_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    normalized = value.strip()
    if normalized != value or len(normalized) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if normalized.lower() != normalized:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return normalized


def _sha256(values: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def _decimal_payload(value: Decimal) -> str:
    return str(value)


def _require_safe_payload(value: Any) -> None:
    if type(value) in (str, bool):
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_safe_payload(item)
        return
    if type(value) is list:
        for item in value:
            _require_safe_payload(item)
        return
    if type(value) is Decimal:
        raise ValueError("payload Decimal values must be rendered as strings")
    if type(value) is float:
        raise ValueError("payload float values are not supported")
    raise ValueError("payload contains unsupported value")


__all__ = (
    "PortfolioScenarioDrawdownGuardV10Config",
    "PortfolioScenarioDrawdownGuardV10Input",
    "PortfolioScenarioDrawdownGuardV10Result",
    "evaluate_portfolio_scenario_drawdown_guard_v10",
    "portfolio_scenario_drawdown_guard_v10_payload",
    "validate_portfolio_scenario_drawdown_guard_v10_public_payload",
)
