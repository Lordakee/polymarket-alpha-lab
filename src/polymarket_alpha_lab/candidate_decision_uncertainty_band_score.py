"""Pure Phase 1 candidate decision uncertainty band scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_UNCERTAINTY_BAND_SCORE_CONFIG_VERSION = (
    "candidate-decision-uncertainty-band-score-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_SENTINEL = Decimal("999999.000000")

UNCERTAINTY_BAND_STATUSES = ("pass", "watch", "block")

_BASE_REASON_CODE = "candidate_decision_uncertainty_band_score"

_UNSAFE_PUBLIC_KEY_PARTS = (
    ("candidate", "_id"),
    ("raw", "_candidate"),
    ("market", "_id"),
    ("market", "_sl", "ug"),
    ("market", "_ques", "tion"),
    ("source", "_re", "f"),
    ("source", "_ur", "l"),
    ("source", "_te", "xt"),
    ("ur", "l"),
    ("d", "sn"),
    ("table", "_name"),
    ("pos", "ition", "_size"),
    ("paper", "_impact", "_notional"),
    ("private", "_key"),
    ("to", "ken"),
)
_UNSAFE_PUBLIC_VALUE_PARTS = (
    ("private", "_key"),
    ("to", "ken"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tr", "ade"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmend"),
    ("source", "_te", "xt"),
    ("ht", "tp"),
    (":", "/", "/"),
    ("d", "sn"),
)
_REASON_CODE_LEVELS = (
    ("midpoint_net_edge", ("pass", "watch", "block")),
    ("lower_bound_net_edge", ("pass", "watch", "nonpositive")),
    ("uncertainty_band_width", ("pass", "watch", "block")),
    ("uncertainty_to_edge_ratio", ("pass", "watch", "block")),
    ("evidence_quality", ("pass", "watch", "block")),
    ("uncertainty_band_score", ("pass", "watch", "block")),
)


@dataclass(frozen=True)
class CandidateDecisionUncertaintyBandScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_UNCERTAINTY_BAND_SCORE_CONFIG_VERSION
    )
    min_pass_midpoint_net_edge: Decimal = Decimal("0.030000")
    min_watch_midpoint_net_edge: Decimal = Decimal("0.010000")
    min_pass_lower_bound_net_edge: Decimal = Decimal("0.005000")
    max_pass_band_width: Decimal = Decimal("0.080000")
    max_watch_band_width: Decimal = Decimal("0.180000")
    max_pass_uncertainty_to_edge_ratio: Decimal = Decimal("1.000000")
    max_watch_uncertainty_to_edge_ratio: Decimal = Decimal("3.000000")
    min_pass_evidence_quality: Decimal = Decimal("0.750000")
    min_watch_evidence_quality: Decimal = Decimal("0.400000")
    min_pass_band_score: Decimal = Decimal("0.750000")
    min_watch_band_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionUncertaintyBandScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionUncertaintyBandScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_midpoint_net_edge",
            "min_watch_midpoint_net_edge",
            "min_pass_lower_bound_net_edge",
            "max_pass_band_width",
            "max_watch_band_width",
            "min_pass_evidence_quality",
            "min_watch_evidence_quality",
            "min_pass_band_score",
            "min_watch_band_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_uncertainty_to_edge_ratio",
            "max_watch_uncertainty_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_midpoint_net_edge > self.min_pass_midpoint_net_edge:
            raise ValueError(
                "min_watch_midpoint_net_edge must not exceed pass threshold",
            )
        if self.max_pass_band_width > self.max_watch_band_width:
            raise ValueError("max_pass_band_width must not exceed watch threshold")
        if (
            self.max_pass_uncertainty_to_edge_ratio
            > self.max_watch_uncertainty_to_edge_ratio
        ):
            raise ValueError(
                "max_pass_uncertainty_to_edge_ratio must not exceed watch threshold",
            )
        if self.min_watch_evidence_quality > self.min_pass_evidence_quality:
            raise ValueError(
                "min_watch_evidence_quality must not exceed pass threshold",
            )
        if self.min_watch_band_score > self.min_pass_band_score:
            raise ValueError("min_watch_band_score must not exceed pass threshold")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionUncertaintyBandScoreInput:
    forecast_midpoint: Decimal
    forecast_lower_bound: Decimal
    forecast_upper_bound: Decimal
    market_probability: Decimal
    estimated_cost_drag: Decimal
    evidence_quality: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionUncertaintyBandScoreInput:
            raise ValueError(
                "input_value must be a CandidateDecisionUncertaintyBandScoreInput",
            )
        for field_name in (
            "forecast_midpoint",
            "forecast_lower_bound",
            "forecast_upper_bound",
            "market_probability",
            "estimated_cost_drag",
            "evidence_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.forecast_lower_bound > self.forecast_midpoint:
            raise ValueError("forecast_lower_bound must not exceed midpoint")
        if self.forecast_upper_bound < self.forecast_midpoint:
            raise ValueError("forecast_upper_bound must be at least midpoint")
        _require_safety_flags("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionUncertaintyBandScoreResult:
    config_version: str
    forecast_midpoint: Decimal
    forecast_lower_bound: Decimal
    forecast_upper_bound: Decimal
    market_probability: Decimal
    estimated_cost_drag: Decimal
    evidence_quality: Decimal
    gross_midpoint_edge: Decimal
    net_midpoint_edge: Decimal
    lower_bound_net_edge: Decimal
    upper_bound_net_edge: Decimal
    uncertainty_band_width: Decimal
    uncertainty_to_edge_ratio: Decimal
    uncertainty_band_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionUncertaintyBandScoreResult:
            raise ValueError(
                "result must be a CandidateDecisionUncertaintyBandScoreResult",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_midpoint",
            "forecast_lower_bound",
            "forecast_upper_bound",
            "market_probability",
            "estimated_cost_drag",
            "evidence_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.forecast_lower_bound > self.forecast_midpoint:
            raise ValueError("forecast_lower_bound must not exceed midpoint")
        if self.forecast_upper_bound < self.forecast_midpoint:
            raise ValueError("forecast_upper_bound must be at least midpoint")
        for field_name in (
            "gross_midpoint_edge",
            "net_midpoint_edge",
            "lower_bound_net_edge",
            "upper_bound_net_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "uncertainty_band_width",
            _normalize_probability(
                "uncertainty_band_width",
                self.uncertainty_band_width,
            ),
        )
        object.__setattr__(
            self,
            "uncertainty_to_edge_ratio",
            _normalize_nonnegative_decimal(
                "uncertainty_to_edge_ratio",
                self.uncertainty_to_edge_ratio,
            ),
        )
        object.__setattr__(
            self,
            "uncertainty_band_score",
            _normalize_probability(
                "uncertainty_band_score",
                self.uncertainty_band_score,
            ),
        )
        _require_member("status", self.status, UNCERTAINTY_BAND_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_safety_flags("result", self)
        _validate_result_metrics(self)
        _validate_result_reasons(self)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_uncertainty_band_score_payload(self)


def score_candidate_decision_uncertainty_band(
    input_value: CandidateDecisionUncertaintyBandScoreInput,
    *,
    config: CandidateDecisionUncertaintyBandScoreConfig,
) -> CandidateDecisionUncertaintyBandScoreResult:
    if type(input_value) is not CandidateDecisionUncertaintyBandScoreInput:
        raise ValueError("input_value must be a CandidateDecisionUncertaintyBandScoreInput")
    if type(config) is not CandidateDecisionUncertaintyBandScoreConfig:
        raise ValueError("config must be a CandidateDecisionUncertaintyBandScoreConfig")
    _require_safety_flags("input_value", input_value)
    _require_safety_flags("config", config)

    metrics = _score_metrics(input_value)
    levels = _status_levels(metrics, config)
    status = _status_from_levels(levels)
    return CandidateDecisionUncertaintyBandScoreResult(
        config_version=config.config_version,
        forecast_midpoint=input_value.forecast_midpoint,
        forecast_lower_bound=input_value.forecast_lower_bound,
        forecast_upper_bound=input_value.forecast_upper_bound,
        market_probability=input_value.market_probability,
        estimated_cost_drag=input_value.estimated_cost_drag,
        evidence_quality=input_value.evidence_quality,
        gross_midpoint_edge=metrics["gross_midpoint_edge"],
        net_midpoint_edge=metrics["net_midpoint_edge"],
        lower_bound_net_edge=metrics["lower_bound_net_edge"],
        upper_bound_net_edge=metrics["upper_bound_net_edge"],
        uncertainty_band_width=metrics["uncertainty_band_width"],
        uncertainty_to_edge_ratio=metrics["uncertainty_to_edge_ratio"],
        uncertainty_band_score=metrics["uncertainty_band_score"],
        status=status,
        reason_codes=_reason_codes(status, levels),
    )


def candidate_decision_uncertainty_band_score_payload(
    result: CandidateDecisionUncertaintyBandScoreResult,
) -> dict[str, Any]:
    if type(result) is not CandidateDecisionUncertaintyBandScoreResult:
        raise ValueError("result must be a CandidateDecisionUncertaintyBandScoreResult")
    _require_safety_flags("result", result)
    _validate_result_metrics(result)
    _validate_result_reasons(result)
    payload = json_ready_no_floats(asdict(result))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_uncertainty_band_score_public_payload(payload)
    return payload


def validate_candidate_decision_uncertainty_band_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    reject_unsafe_surface_fields("candidate decision uncertainty band payload", payload)
    _reject_unsafe_public_entries(payload)
    _reject_numeric_public_values(payload)
    _require_public_payload_flags(payload)
    return True


def _score_metrics(
    input_value: CandidateDecisionUncertaintyBandScoreInput,
) -> dict[str, Decimal]:
    gross_midpoint_edge = _normalize_decimal(
        "gross_midpoint_edge",
        input_value.forecast_midpoint - input_value.market_probability,
    )
    net_midpoint_edge = _net_edge(
        "net_midpoint_edge",
        input_value.forecast_midpoint,
        input_value.market_probability,
        input_value.estimated_cost_drag,
    )
    lower_bound_net_edge = _net_edge(
        "lower_bound_net_edge",
        input_value.forecast_lower_bound,
        input_value.market_probability,
        input_value.estimated_cost_drag,
    )
    upper_bound_net_edge = _net_edge(
        "upper_bound_net_edge",
        input_value.forecast_upper_bound,
        input_value.market_probability,
        input_value.estimated_cost_drag,
    )
    uncertainty_band_width = _normalize_probability(
        "uncertainty_band_width",
        input_value.forecast_upper_bound - input_value.forecast_lower_bound,
    )
    uncertainty_to_edge_ratio = _uncertainty_to_edge_ratio(
        uncertainty_band_width,
        net_midpoint_edge,
    )
    uncertainty_band_score = _uncertainty_band_score(
        input_value.evidence_quality,
        uncertainty_band_width,
        net_midpoint_edge,
    )
    return {
        "gross_midpoint_edge": gross_midpoint_edge,
        "net_midpoint_edge": net_midpoint_edge,
        "lower_bound_net_edge": lower_bound_net_edge,
        "upper_bound_net_edge": upper_bound_net_edge,
        "uncertainty_band_width": uncertainty_band_width,
        "uncertainty_to_edge_ratio": uncertainty_to_edge_ratio,
        "uncertainty_band_score": uncertainty_band_score,
        "evidence_quality": input_value.evidence_quality,
    }


def _status_levels(
    metrics: dict[str, Decimal],
    config: CandidateDecisionUncertaintyBandScoreConfig,
) -> dict[str, str]:
    return {
        "midpoint_net_edge": _min_threshold_level(
            metrics["net_midpoint_edge"],
            config.min_pass_midpoint_net_edge,
            config.min_watch_midpoint_net_edge,
        ),
        "lower_bound_net_edge": _lower_bound_level(
            metrics["lower_bound_net_edge"],
            config.min_pass_lower_bound_net_edge,
        ),
        "uncertainty_band_width": _max_threshold_level(
            metrics["uncertainty_band_width"],
            config.max_pass_band_width,
            config.max_watch_band_width,
        ),
        "uncertainty_to_edge_ratio": _max_threshold_level(
            metrics["uncertainty_to_edge_ratio"],
            config.max_pass_uncertainty_to_edge_ratio,
            config.max_watch_uncertainty_to_edge_ratio,
        ),
        "evidence_quality": _min_threshold_level(
            metrics["evidence_quality"],
            config.min_pass_evidence_quality,
            config.min_watch_evidence_quality,
        ),
        "uncertainty_band_score": _min_threshold_level(
            metrics["uncertainty_band_score"],
            config.min_pass_band_score,
            config.min_watch_band_score,
        ),
    }


def _status_from_levels(levels: dict[str, str]) -> str:
    block_fields = (
        "midpoint_net_edge",
        "uncertainty_band_width",
        "uncertainty_to_edge_ratio",
        "evidence_quality",
        "uncertainty_band_score",
    )
    if any(levels[field_name] == "block" for field_name in block_fields):
        return "block"
    if all(level == "pass" for level in levels.values()):
        return "pass"
    return "watch"


def _reason_codes(status: str, levels: dict[str, str]) -> tuple[str, ...]:
    return (
        _BASE_REASON_CODE,
        f"status_{status}",
        f"midpoint_net_edge_{levels['midpoint_net_edge']}",
        f"lower_bound_net_edge_{levels['lower_bound_net_edge']}",
        f"uncertainty_band_width_{levels['uncertainty_band_width']}",
        f"uncertainty_to_edge_ratio_{levels['uncertainty_to_edge_ratio']}",
        f"evidence_quality_{levels['evidence_quality']}",
        f"uncertainty_band_score_{levels['uncertainty_band_score']}",
    )


def _min_threshold_level(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _max_threshold_level(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _lower_bound_level(value: Decimal, pass_threshold: Decimal) -> str:
    if value <= ZERO:
        return "nonpositive"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _net_edge(
    field_name: str,
    forecast_probability: Decimal,
    observed_probability: Decimal,
    estimated_cost_drag: Decimal,
) -> Decimal:
    return _normalize_decimal(
        field_name,
        forecast_probability - observed_probability - estimated_cost_drag,
    )


def _uncertainty_to_edge_ratio(
    uncertainty_band_width: Decimal,
    net_midpoint_edge: Decimal,
) -> Decimal:
    if net_midpoint_edge <= ZERO:
        if uncertainty_band_width <= ZERO:
            return ZERO
        return RATIO_SENTINEL
    return _normalize_nonnegative_decimal(
        "uncertainty_to_edge_ratio",
        uncertainty_band_width / net_midpoint_edge,
    )


def _uncertainty_band_score(
    evidence_quality: Decimal,
    uncertainty_band_width: Decimal,
    net_midpoint_edge: Decimal,
) -> Decimal:
    if net_midpoint_edge <= ZERO:
        return ZERO
    if uncertainty_band_width <= ZERO:
        containment_score = ONE
    else:
        containment_score = min(
            ONE,
            _normalize_nonnegative_decimal(
                "edge_to_band_ratio",
                net_midpoint_edge / uncertainty_band_width,
            ),
        )
    return _normalize_probability(
        "uncertainty_band_score",
        evidence_quality * containment_score,
    )


def _validate_result_metrics(
    result: CandidateDecisionUncertaintyBandScoreResult,
) -> None:
    expected = _score_metrics(
        CandidateDecisionUncertaintyBandScoreInput(
            forecast_midpoint=result.forecast_midpoint,
            forecast_lower_bound=result.forecast_lower_bound,
            forecast_upper_bound=result.forecast_upper_bound,
            market_probability=result.market_probability,
            estimated_cost_drag=result.estimated_cost_drag,
            evidence_quality=result.evidence_quality,
        ),
    )
    for field_name, expected_value in expected.items():
        if getattr(result, field_name) != expected_value:
            raise ValueError(f"{field_name} must match score inputs")


def _validate_result_reasons(
    result: CandidateDecisionUncertaintyBandScoreResult,
) -> None:
    if len(result.reason_codes) != 8:
        raise ValueError("reason_codes must include score classification reasons")
    if result.reason_codes[0] != _BASE_REASON_CODE:
        raise ValueError("reason_codes must start with score reason")
    if result.reason_codes[1] != f"status_{result.status}":
        raise ValueError("reason_codes must include status reason")
    levels: dict[str, str] = {}
    for reason_code, (field_name, allowed_levels) in zip(
        result.reason_codes[2:],
        _REASON_CODE_LEVELS,
    ):
        prefix = f"{field_name}_"
        if not reason_code.startswith(prefix):
            raise ValueError("reason_codes must include score classification reasons")
        level = reason_code.removeprefix(prefix)
        if level not in allowed_levels:
            raise ValueError("reason_codes must include known classification levels")
        levels[field_name] = level
    if _status_from_levels(levels) != result.status:
        raise ValueError("reason_codes must match status")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_safety_flags(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    require_paper_only_flags(label, value)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _reject_unsafe_public_entries(payload: object) -> None:
    bad_keys = tuple("".join(parts) for parts in _UNSAFE_PUBLIC_KEY_PARTS)
    bad_values = tuple("".join(parts) for parts in _UNSAFE_PUBLIC_VALUE_PARTS)
    for key, item in _iter_entries(payload):
        lowered_key = key.lower()
        if any(term in lowered_key for term in bad_keys):
            raise ValueError("unsafe public payload field")
        if type(item) is str:
            lowered_value = item.lower()
            if any(term in lowered_value for term in bad_values):
                raise ValueError("unsafe public payload value")


def _reject_numeric_public_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if isinstance(value, (Decimal, float, int)):
        raise ValueError("numeric public payload values must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_numeric_public_values(item)


def _iter_entries(value: object) -> tuple[tuple[str, object], ...]:
    if isinstance(value, dict):
        entries: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            entries.append((key, item))
            entries.extend(_iter_entries(item))
        return tuple(entries)
    if isinstance(value, (list, tuple)):
        entries = []
        for item in value:
            entries.extend(_iter_entries(item))
        return tuple(entries)
    return ()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_UNCERTAINTY_BAND_SCORE_CONFIG_VERSION",
    "UNCERTAINTY_BAND_STATUSES",
    "CandidateDecisionUncertaintyBandScoreConfig",
    "CandidateDecisionUncertaintyBandScoreInput",
    "CandidateDecisionUncertaintyBandScoreResult",
    "score_candidate_decision_uncertainty_band",
    "candidate_decision_uncertainty_band_score_payload",
    "validate_candidate_decision_uncertainty_band_score_public_payload",
)
