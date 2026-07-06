"""Pure report reducer for market candidate triage v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_MARKET_CANDIDATE_TRIAGE_V10_CONFIG_VERSION = (
    "strategy-market-candidate-triage-v10"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
TRIAGE_STATUSES = ("pass", "watch", "blocked")
TRIAGE_RANK_BANDS = ("A", "B", "C", "D")
NEXT_STEP_BY_STATUS = {
    "pass": "advance_to_readonly_research_packet",
    "watch": "refresh_scores_before_specialist_review",
    "blocked": "do_not_advance_until_blockers_clear",
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV10Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_CANDIDATE_TRIAGE_V10_CONFIG_VERSION
    minimum_information_edge_score: Decimal = Decimal("0.550000")
    minimum_expected_value_score: Decimal = Decimal("0.550000")
    minimum_liquidity_score: Decimal = Decimal("0.400000")
    maximum_resolution_risk_score: Decimal = Decimal("0.650000")
    minimum_team_fit_score: Decimal = Decimal("0.500000")
    maximum_cost_drag_score: Decimal = Decimal("0.550000")
    minimum_time_to_resolution_minutes: Decimal = Decimal("60.000000")
    minimum_pass_composite_score: Decimal = Decimal("0.650000")
    rank_band_a_minimum_score: Decimal = Decimal("0.800000")
    rank_band_b_minimum_score: Decimal = Decimal("0.650000")
    rank_band_c_minimum_score: Decimal = Decimal("0.500000")
    information_edge_weight: Decimal = Decimal("0.250000")
    expected_value_weight: Decimal = Decimal("0.250000")
    liquidity_weight: Decimal = Decimal("0.200000")
    team_fit_weight: Decimal = Decimal("0.150000")
    resolution_quality_weight: Decimal = Decimal("0.100000")
    cost_quality_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "minimum_information_edge_score",
            "minimum_expected_value_score",
            "minimum_liquidity_score",
            "maximum_resolution_risk_score",
            "minimum_team_fit_score",
            "maximum_cost_drag_score",
            "minimum_pass_composite_score",
            "rank_band_a_minimum_score",
            "rank_band_b_minimum_score",
            "rank_band_c_minimum_score",
            "information_edge_weight",
            "expected_value_weight",
            "liquidity_weight",
            "team_fit_weight",
            "resolution_quality_weight",
            "cost_quality_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "minimum_time_to_resolution_minutes",
                self.minimum_time_to_resolution_minutes,
            ),
        )
        if not (
            self.rank_band_a_minimum_score
            >= self.rank_band_b_minimum_score
            >= self.rank_band_c_minimum_score
        ):
            raise ValueError("rank band score thresholds must descend")
        if self.rank_band_b_minimum_score != self.minimum_pass_composite_score:
            raise ValueError("rank_band_b_minimum_score must match pass threshold")
        weight_sum = _quantize(
            self.information_edge_weight
            + self.expected_value_weight
            + self.liquidity_weight
            + self.team_fit_weight
            + self.resolution_quality_weight
            + self.cost_quality_weight,
        )
        if weight_sum != ONE:
            raise ValueError("score weights must sum to one")
        require_paper_only_flags("StrategyMarketCandidateTriageV10Config", self)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV10Input:
    market_id: str
    category: str
    information_edge_score: Decimal
    expected_value_score: Decimal
    liquidity_score: Decimal
    resolution_risk_score: Decimal
    team_fit_score: Decimal
    cost_drag_score: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_public_text("category", self.category)
        for field_name in (
            "information_edge_score",
            "expected_value_score",
            "liquidity_score",
            "resolution_risk_score",
            "team_fit_score",
            "cost_drag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        require_paper_only_flags("StrategyMarketCandidateTriageV10Input", self)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV10Payload:
    config_version: str
    market_id: str
    category: str
    information_edge_score: Decimal
    expected_value_score: Decimal
    liquidity_score: Decimal
    resolution_risk_score: Decimal
    team_fit_score: Decimal
    cost_drag_score: Decimal
    time_to_resolution_minutes: Decimal
    resolution_quality_score: Decimal
    cost_quality_score: Decimal
    composite_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        _require_identifier("market_id", self.market_id)
        _require_public_text("category", self.category)
        for field_name in (
            "information_edge_score",
            "expected_value_score",
            "liquidity_score",
            "resolution_risk_score",
            "team_fit_score",
            "cost_drag_score",
            "resolution_quality_score",
            "cost_quality_score",
            "composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        if self.resolution_quality_score != _quantize(ONE - self.resolution_risk_score):
            raise ValueError("resolution_quality_score must match resolution_risk_score")
        if self.cost_quality_score != _quantize(ONE - self.cost_drag_score):
            raise ValueError("cost_quality_score must match cost_drag_score")
        require_paper_only_flags("StrategyMarketCandidateTriageV10Payload", self)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV10Result:
    triage_status: str
    triage_rank_band: str
    recommended_next_step: str
    blocking_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: StrategyMarketCandidateTriageV10Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_status("triage_status", self.triage_status)
        _require_rank_band("triage_rank_band", self.triage_rank_band)
        _require_next_step("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.triage_status]:
            raise ValueError("recommended_next_step must match triage_status")
        object.__setattr__(
            self,
            "blocking_reasons",
            _normalize_reasons("blocking_reasons", self.blocking_reasons, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.payload) is not StrategyMarketCandidateTriageV10Payload:
            raise ValueError("payload must be a StrategyMarketCandidateTriageV10Payload")
        require_paper_only_flags("payload", self.payload)
        if self.triage_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("triage_status must match reason_codes")
        if bool(self.blocking_reasons) != (self.triage_status == "blocked"):
            raise ValueError("blocking_reasons must match triage_status")
        if self.triage_status == "blocked" and self.triage_rank_band != "D":
            raise ValueError("blocked candidates must use rank band D")
        require_paper_only_flags("StrategyMarketCandidateTriageV10Result", self)


def build_strategy_market_candidate_triage_v10_result(
    candidate: StrategyMarketCandidateTriageV10Input,
    *,
    config: StrategyMarketCandidateTriageV10Config,
) -> StrategyMarketCandidateTriageV10Result:
    """Score one market candidate without side effects."""

    if type(candidate) is not StrategyMarketCandidateTriageV10Input:
        raise ValueError("candidate must be a StrategyMarketCandidateTriageV10Input")
    if type(config) is not StrategyMarketCandidateTriageV10Config:
        raise ValueError("config must be a StrategyMarketCandidateTriageV10Config")
    require_paper_only_flags("candidate", candidate)
    require_paper_only_flags("config", config)

    resolution_quality_score = _quantize(ONE - candidate.resolution_risk_score)
    cost_quality_score = _quantize(ONE - candidate.cost_drag_score)
    composite_score = _quantize(
        candidate.information_edge_score * config.information_edge_weight
        + candidate.expected_value_score * config.expected_value_weight
        + candidate.liquidity_score * config.liquidity_weight
        + candidate.team_fit_score * config.team_fit_weight
        + resolution_quality_score * config.resolution_quality_weight
        + cost_quality_score * config.cost_quality_weight,
    )
    payload = StrategyMarketCandidateTriageV10Payload(
        config_version=config.config_version,
        market_id=candidate.market_id,
        category=candidate.category,
        information_edge_score=candidate.information_edge_score,
        expected_value_score=candidate.expected_value_score,
        liquidity_score=candidate.liquidity_score,
        resolution_risk_score=candidate.resolution_risk_score,
        team_fit_score=candidate.team_fit_score,
        cost_drag_score=candidate.cost_drag_score,
        time_to_resolution_minutes=candidate.time_to_resolution_minutes,
        resolution_quality_score=resolution_quality_score,
        cost_quality_score=cost_quality_score,
        composite_score=composite_score,
    )
    blocking_reasons = _blocking_reasons(candidate, config=config)
    reason_codes = _reason_codes(
        candidate,
        config=config,
        composite_score=composite_score,
        blocking_reasons=blocking_reasons,
    )
    status = _status_from_reason_codes(reason_codes)

    return StrategyMarketCandidateTriageV10Result(
        triage_status=status,
        triage_rank_band="D" if status == "blocked" else _rank_band(composite_score, config),
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        blocking_reasons=blocking_reasons,
        reason_codes=reason_codes,
        payload=payload,
    )


def triage_strategy_market_candidate_v10(
    *,
    market_id: str,
    category: str,
    information_edge_score: Decimal,
    expected_value_score: Decimal,
    liquidity_score: Decimal,
    resolution_risk_score: Decimal,
    team_fit_score: Decimal,
    cost_drag_score: Decimal,
    time_to_resolution_minutes: Decimal,
    config: StrategyMarketCandidateTriageV10Config | None = None,
) -> StrategyMarketCandidateTriageV10Result:
    candidate = StrategyMarketCandidateTriageV10Input(
        market_id=market_id,
        category=category,
        information_edge_score=information_edge_score,
        expected_value_score=expected_value_score,
        liquidity_score=liquidity_score,
        resolution_risk_score=resolution_risk_score,
        team_fit_score=team_fit_score,
        cost_drag_score=cost_drag_score,
        time_to_resolution_minutes=time_to_resolution_minutes,
    )
    return build_strategy_market_candidate_triage_v10_result(
        candidate,
        config=config or StrategyMarketCandidateTriageV10Config(),
    )


def strategy_market_candidate_triage_v10_payload(
    result: StrategyMarketCandidateTriageV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is StrategyMarketCandidateTriageV10Result:
        require_paper_only_flags("result", result)
        reject_unsafe_surface_fields("market candidate triage result", result)
        _reject_payload_values("result", result)
        ready = _json_ready(result)
    elif type(result) is dict:
        reject_unsafe_surface_fields("market candidate triage payload", result)
        _reject_payload_values("payload", result)
        ready = _json_ready(result)
    else:
        raise ValueError("result must be a StrategyMarketCandidateTriageV10Result")
    if type(ready) is not dict:
        raise ValueError("result payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(ready))
    return ready


@dataclass(frozen=True)
class _DictFlags:
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


def _blocking_reasons(
    candidate: StrategyMarketCandidateTriageV10Input,
    *,
    config: StrategyMarketCandidateTriageV10Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.liquidity_score < config.minimum_liquidity_score:
        reasons.append("liquidity_score_below_floor")
    if candidate.resolution_risk_score > config.maximum_resolution_risk_score:
        reasons.append("resolution_risk_score_above_limit")
    if candidate.team_fit_score < config.minimum_team_fit_score:
        reasons.append("team_fit_score_below_floor")
    if candidate.cost_drag_score > config.maximum_cost_drag_score:
        reasons.append("cost_drag_score_above_limit")
    if candidate.time_to_resolution_minutes < config.minimum_time_to_resolution_minutes:
        reasons.append("time_to_resolution_below_floor")
    return tuple(reasons)


def _reason_codes(
    candidate: StrategyMarketCandidateTriageV10Input,
    *,
    config: StrategyMarketCandidateTriageV10Config,
    composite_score: Decimal,
    blocking_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if blocking_reasons:
        return _normalize_reasons(
            "reason_codes",
            tuple(f"candidate_{reason}_blocked" for reason in blocking_reasons),
            allow_empty=False,
        )

    reason_codes: list[str] = []
    if candidate.information_edge_score < config.minimum_information_edge_score:
        reason_codes.append("candidate_information_edge_watch")
    if candidate.expected_value_score < config.minimum_expected_value_score:
        reason_codes.append("candidate_expected_value_watch")
    if composite_score < config.minimum_pass_composite_score:
        reason_codes.append("candidate_composite_score_watch")
    if not reason_codes:
        reason_codes.append("candidate_triage_clear")
    return _normalize_reasons("reason_codes", tuple(reason_codes), allow_empty=False)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rank_band(
    composite_score: Decimal,
    config: StrategyMarketCandidateTriageV10Config,
) -> str:
    if composite_score >= config.rank_band_a_minimum_score:
        return "A"
    if composite_score >= config.rank_band_b_minimum_score:
        return "B"
    if composite_score >= config.rank_band_c_minimum_score:
        return "C"
    return "D"


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TRIAGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_rank_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TRIAGE_RANK_BANDS:
        raise ValueError(f"{field_name} must be A, B, C, or D")


def _require_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEP_BY_STATUS.values():
        raise ValueError(f"{field_name} is not supported")


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe surface text")


def _normalize_reasons(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reasons = tuple(value)
    if not allow_empty and not reasons:
        raise ValueError(f"{field_name} must not be empty")
    for reason in reasons:
        _require_identifier(field_name, reason)
    if len(reasons) != len(set(reasons)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return reasons


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
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
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_payload_values(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must use Decimal values")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is bool or value is None:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_STRATEGY_MARKET_CANDIDATE_TRIAGE_V10_CONFIG_VERSION",
    "StrategyMarketCandidateTriageV10Config",
    "StrategyMarketCandidateTriageV10Input",
    "StrategyMarketCandidateTriageV10Payload",
    "StrategyMarketCandidateTriageV10Result",
    "build_strategy_market_candidate_triage_v10_result",
    "strategy_market_candidate_triage_v10_payload",
    "triage_strategy_market_candidate_v10",
)
