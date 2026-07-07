"""Pure report-only candidate timing-window uncertainty scoring."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any


DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION = (
    "candidate-decision-time-to-resolution-uncertainty-score-v0"
)

TIME_TO_RESOLUTION_UNCERTAINTY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

BASE_REASON_CODE = "time_to_resolution_uncertainty_score"
HEX_CHARS = frozenset("0123456789abcdef")

_UNSAFE_KEY_PARTS = (
    ("candidate", "_id", "raw candidate"),
    ("raw", "_candidate", "raw candidate"),
    ("candidate", "_slug", "raw candidate"),
    ("market", "_id", "raw market"),
    ("market", "_slug", "raw market"),
    ("question", "", "raw market"),
    ("source", "_ref", "source"),
    ("source", "_url", "source"),
    ("source", "_text", "source"),
    ("url", "", "source"),
    ("dsn", "", "storage"),
    ("table", "_name", "storage"),
    ("to", "ken", "unsafe"),
    ("se", "cret", "unsafe"),
    ("au", "th", "unsafe"),
    ("wal", "let", "unsafe"),
    ("or", "der", "unsafe"),
    ("tr", "ade", "unsafe"),
    ("b", "uy", "unsafe"),
    ("s", "ell", "unsafe"),
    ("reco", "mmend", "unsafe"),
    ("pos", "ition", "_size", "unsafe"),
)
_UNSAFE_VALUE_PARTS = (
    ("candidate", ":", "raw candidate"),
    ("candidate", "_id", "raw candidate"),
    ("market", ":", "raw market"),
    ("market", "_slug", "raw market"),
    ("0", "x", "raw market"),
    ("will ", "", "raw market"),
    ("?", "", "raw market"),
    ("source", ":", "source"),
    ("source", "_text", "source"),
    ("http", "://", "source"),
    ("https", "://", "source"),
    (":", "//", "source"),
    (".com", "", "source"),
    (".org", "", "source"),
    (".net", "", "source"),
    (".test", "", "source"),
    ("dsn", "", "storage"),
    ("postgres", "://", "storage"),
    ("table", "", "storage"),
    ("to", "ken", "unsafe"),
    ("se", "cret", "unsafe"),
    ("au", "th", "unsafe"),
    ("wal", "let", "unsafe"),
    ("or", "der", "unsafe"),
    ("tr", "ade", "unsafe"),
    ("b", "uy", "unsafe"),
    ("s", "ell", "unsafe"),
    ("reco", "mmend", "unsafe"),
    ("pos", "ition sizing", "unsafe"),
    ("pos", "ition-size", "unsafe"),
    ("pos", "ition_size", "unsafe"),
)
_UNSAFE_STATUS_VALUES = frozenset(("ready", "blocked", "matched", "supported"))


@dataclass(frozen=True)
class CandidateDecisionTimeToResolutionUncertaintyScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION
    )
    max_pass_expected_resolution_days: Decimal = Decimal("14.000000")
    max_watch_expected_resolution_days: Decimal = Decimal("45.000000")
    max_pass_resolution_window_width_days: Decimal = Decimal("2.000000")
    max_watch_resolution_window_width_days: Decimal = Decimal("10.000000")
    min_pass_timing_confidence_score: Decimal = Decimal("0.800000")
    min_watch_timing_confidence_score: Decimal = Decimal("0.500000")
    min_pass_catalyst_specificity_score: Decimal = Decimal("0.750000")
    min_watch_catalyst_specificity_score: Decimal = Decimal("0.450000")
    min_pass_evidence_freshness_score: Decimal = Decimal("0.750000")
    min_watch_evidence_freshness_score: Decimal = Decimal("0.450000")
    min_pass_settlement_rule_clarity_score: Decimal = Decimal("0.800000")
    min_watch_settlement_rule_clarity_score: Decimal = Decimal("0.500000")
    expected_resolution_days_weight: Decimal = Decimal("0.150000")
    resolution_window_width_days_weight: Decimal = Decimal("0.350000")
    timing_confidence_score_weight: Decimal = Decimal("0.200000")
    catalyst_specificity_score_weight: Decimal = Decimal("0.100000")
    evidence_freshness_score_weight: Decimal = Decimal("0.100000")
    settlement_rule_clarity_score_weight: Decimal = Decimal("0.100000")
    min_pass_uncertainty_score: Decimal = Decimal("0.750000")
    min_watch_uncertainty_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionTimeToResolutionUncertaintyScoreConfig:
            raise ValueError(
                "config must be a "
                "CandidateDecisionTimeToResolutionUncertaintyScoreConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported version")
        for field_name in (
            "max_pass_expected_resolution_days",
            "max_watch_expected_resolution_days",
            "max_pass_resolution_window_width_days",
            "max_watch_resolution_window_width_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_timing_confidence_score",
            "min_watch_timing_confidence_score",
            "min_pass_catalyst_specificity_score",
            "min_watch_catalyst_specificity_score",
            "min_pass_evidence_freshness_score",
            "min_watch_evidence_freshness_score",
            "min_pass_settlement_rule_clarity_score",
            "min_watch_settlement_rule_clarity_score",
            "expected_resolution_days_weight",
            "resolution_window_width_days_weight",
            "timing_confidence_score_weight",
            "catalyst_specificity_score_weight",
            "evidence_freshness_score_weight",
            "settlement_rule_clarity_score_weight",
            "min_pass_uncertainty_score",
            "min_watch_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateDecisionTimeToResolutionUncertaintyScoreInput:
    redacted_candidate_ref: str
    expected_resolution_days: Decimal
    resolution_window_width_days: Decimal
    timing_confidence_score: Decimal
    catalyst_specificity_score: Decimal
    evidence_freshness_score: Decimal
    settlement_rule_clarity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionTimeToResolutionUncertaintyScoreInput:
            raise ValueError(
                "input_value must be a "
                "CandidateDecisionTimeToResolutionUncertaintyScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "expected_resolution_days",
            "resolution_window_width_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "timing_confidence_score",
            "catalyst_specificity_score",
            "evidence_freshness_score",
            "settlement_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateDecisionTimeToResolutionUncertaintyScoreResult:
    config_version: str
    redacted_candidate_ref: str
    expected_resolution_days: Decimal
    resolution_window_width_days: Decimal
    timing_confidence_score: Decimal
    catalyst_specificity_score: Decimal
    evidence_freshness_score: Decimal
    settlement_rule_clarity_score: Decimal
    expected_resolution_days_component_score: Decimal
    resolution_window_width_days_component_score: Decimal
    timing_confidence_component_score: Decimal
    catalyst_specificity_component_score: Decimal
    evidence_freshness_component_score: Decimal
    settlement_rule_clarity_component_score: Decimal
    uncertainty_score: Decimal
    status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionTimeToResolutionUncertaintyScoreResult:
            raise ValueError(
                "result must be a "
                "CandidateDecisionTimeToResolutionUncertaintyScoreResult",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "expected_resolution_days",
            "resolution_window_width_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "timing_confidence_score",
            "catalyst_specificity_score",
            "evidence_freshness_score",
            "settlement_rule_clarity_score",
            "expected_resolution_days_component_score",
            "resolution_window_width_days_component_score",
            "timing_confidence_component_score",
            "catalyst_specificity_component_score",
            "evidence_freshness_component_score",
            "settlement_rule_clarity_component_score",
            "uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, TIME_TO_RESOLUTION_UNCERTAINTY_STATUSES)
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_reason_codes("hard_flag_codes", self.hard_flag_codes, True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, False),
        )
        _require_digest(self.derived_validation_digest)
        _require_hard_flags(self)
        _validate_result_consistency(self)
        if self.derived_validation_digest != _result_digest_from_values(
            _result_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match result payload")

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_time_to_resolution_uncertainty_score_payload(self)


def score_candidate_decision_time_to_resolution_uncertainty_score(
    input_value: CandidateDecisionTimeToResolutionUncertaintyScoreInput,
    *,
    config: CandidateDecisionTimeToResolutionUncertaintyScoreConfig,
) -> CandidateDecisionTimeToResolutionUncertaintyScoreResult:
    if type(input_value) is not CandidateDecisionTimeToResolutionUncertaintyScoreInput:
        raise ValueError(
            "input_value must be a "
            "CandidateDecisionTimeToResolutionUncertaintyScoreInput",
        )
    if type(config) is not CandidateDecisionTimeToResolutionUncertaintyScoreConfig:
        raise ValueError(
            "config must be a "
            "CandidateDecisionTimeToResolutionUncertaintyScoreConfig",
        )
    _require_hard_flags(input_value)
    _require_hard_flags(config)
    metrics = _score_metrics(input_value, config)
    levels = metrics["levels"]
    if type(levels) is not dict:
        raise ValueError("levels must be a dict")
    status = _status_from_levels(levels)
    hard_flag_codes = _hard_flag_codes(levels)
    result_values: dict[str, object] = {
        "config_version": config.config_version,
        "redacted_candidate_ref": input_value.redacted_candidate_ref,
        "expected_resolution_days": input_value.expected_resolution_days,
        "resolution_window_width_days": input_value.resolution_window_width_days,
        "timing_confidence_score": input_value.timing_confidence_score,
        "catalyst_specificity_score": input_value.catalyst_specificity_score,
        "evidence_freshness_score": input_value.evidence_freshness_score,
        "settlement_rule_clarity_score": input_value.settlement_rule_clarity_score,
        "expected_resolution_days_component_score": metrics[
            "expected_resolution_days_component_score"
        ],
        "resolution_window_width_days_component_score": metrics[
            "resolution_window_width_days_component_score"
        ],
        "timing_confidence_component_score": metrics[
            "timing_confidence_component_score"
        ],
        "catalyst_specificity_component_score": metrics[
            "catalyst_specificity_component_score"
        ],
        "evidence_freshness_component_score": metrics[
            "evidence_freshness_component_score"
        ],
        "settlement_rule_clarity_component_score": metrics[
            "settlement_rule_clarity_component_score"
        ],
        "uncertainty_score": metrics["uncertainty_score"],
        "status": status,
        "hard_flag_codes": hard_flag_codes,
        "reason_codes": _reason_codes(status, levels),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionTimeToResolutionUncertaintyScoreResult(
        **result_values,
        derived_validation_digest=_result_digest_from_values(result_values),
    )


def candidate_decision_time_to_resolution_uncertainty_score_payload(
    result: CandidateDecisionTimeToResolutionUncertaintyScoreResult,
) -> dict[str, Any]:
    if type(result) is not CandidateDecisionTimeToResolutionUncertaintyScoreResult:
        raise ValueError(
            "result must be a "
            "CandidateDecisionTimeToResolutionUncertaintyScoreResult",
        )
    _require_hard_flags(result)
    _validate_result_consistency(result)
    payload = _json_ready(asdict(result))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    validate_candidate_decision_time_to_resolution_uncertainty_score_public_payload(
        payload,
    )
    return payload


def validate_candidate_decision_time_to_resolution_uncertainty_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _walk_public_payload(payload)
    _require_payload_flags(payload)
    return True


def _score_metrics(
    input_value: CandidateDecisionTimeToResolutionUncertaintyScoreInput,
    config: CandidateDecisionTimeToResolutionUncertaintyScoreConfig,
) -> dict[str, object]:
    expected_component, expected_level = _max_component_level(
        input_value.expected_resolution_days,
        config.max_pass_expected_resolution_days,
        config.max_watch_expected_resolution_days,
    )
    width_component, width_level = _max_component_level(
        input_value.resolution_window_width_days,
        config.max_pass_resolution_window_width_days,
        config.max_watch_resolution_window_width_days,
    )
    timing_component, timing_level = _min_component_level(
        input_value.timing_confidence_score,
        config.min_pass_timing_confidence_score,
        config.min_watch_timing_confidence_score,
    )
    catalyst_component, catalyst_level = _min_component_level(
        input_value.catalyst_specificity_score,
        config.min_pass_catalyst_specificity_score,
        config.min_watch_catalyst_specificity_score,
    )
    freshness_component, freshness_level = _min_component_level(
        input_value.evidence_freshness_score,
        config.min_pass_evidence_freshness_score,
        config.min_watch_evidence_freshness_score,
    )
    rule_component, rule_level = _min_component_level(
        input_value.settlement_rule_clarity_score,
        config.min_pass_settlement_rule_clarity_score,
        config.min_watch_settlement_rule_clarity_score,
    )
    uncertainty_score = _normalize_unit_decimal(
        "uncertainty_score",
        expected_component * config.expected_resolution_days_weight
        + width_component * config.resolution_window_width_days_weight
        + timing_component * config.timing_confidence_score_weight
        + catalyst_component * config.catalyst_specificity_score_weight
        + freshness_component * config.evidence_freshness_score_weight
        + rule_component * config.settlement_rule_clarity_score_weight,
    )
    score_level = _min_threshold_level(
        uncertainty_score,
        config.min_pass_uncertainty_score,
        config.min_watch_uncertainty_score,
    )
    return {
        "expected_resolution_days_component_score": expected_component,
        "resolution_window_width_days_component_score": width_component,
        "timing_confidence_component_score": timing_component,
        "catalyst_specificity_component_score": catalyst_component,
        "evidence_freshness_component_score": freshness_component,
        "settlement_rule_clarity_component_score": rule_component,
        "uncertainty_score": uncertainty_score,
        "levels": {
            "expected_resolution_days": expected_level,
            "resolution_window_width_days": width_level,
            "timing_confidence_score": timing_level,
            "catalyst_specificity_score": catalyst_level,
            "evidence_freshness_score": freshness_level,
            "settlement_rule_clarity_score": rule_level,
            "uncertainty_score": score_level,
        },
    }


def _max_component_level(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> tuple[Decimal, str]:
    if value <= pass_threshold:
        return ONE, "pass"
    if value > watch_threshold:
        return ZERO, "block"
    return (
        _normalize_unit_decimal(
            "component_score",
            (watch_threshold - value) / (watch_threshold - pass_threshold),
        ),
        "watch",
    )


def _min_component_level(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> tuple[Decimal, str]:
    if value >= pass_threshold:
        return ONE, "pass"
    if value < watch_threshold:
        return ZERO, "block"
    return (
        _normalize_unit_decimal(
            "component_score",
            (value - watch_threshold) / (pass_threshold - watch_threshold),
        ),
        "watch",
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


def _status_from_levels(levels: dict[str, str]) -> str:
    component_fields = (
        "expected_resolution_days",
        "resolution_window_width_days",
        "timing_confidence_score",
        "catalyst_specificity_score",
        "evidence_freshness_score",
        "settlement_rule_clarity_score",
    )
    if any(levels[field_name] == "block" for field_name in component_fields):
        return "block"
    if levels["uncertainty_score"] == "block":
        return "block"
    if all(level == "pass" for level in levels.values()):
        return "pass"
    return "watch"


def _hard_flag_codes(levels: dict[str, str]) -> tuple[str, ...]:
    hard_flags: list[str] = []
    for field_name in (
        "expected_resolution_days",
        "resolution_window_width_days",
        "timing_confidence_score",
        "catalyst_specificity_score",
        "evidence_freshness_score",
        "settlement_rule_clarity_score",
        "uncertainty_score",
    ):
        if levels[field_name] == "block":
            hard_flags.append(f"{field_name}_block")
    return tuple(hard_flags)


def _reason_codes(status: str, levels: dict[str, str]) -> tuple[str, ...]:
    return (
        BASE_REASON_CODE,
        f"status_{status}",
        f"expected_resolution_days_{levels['expected_resolution_days']}",
        f"resolution_window_width_days_{levels['resolution_window_width_days']}",
        f"timing_confidence_score_{levels['timing_confidence_score']}",
        f"catalyst_specificity_score_{levels['catalyst_specificity_score']}",
        f"evidence_freshness_score_{levels['evidence_freshness_score']}",
        f"settlement_rule_clarity_score_{levels['settlement_rule_clarity_score']}",
        f"uncertainty_score_{levels['uncertainty_score']}",
    )


def _validate_result_consistency(
    result: CandidateDecisionTimeToResolutionUncertaintyScoreResult,
) -> None:
    if (
        result.config_version
        != DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION
    ):
        raise ValueError("config_version must match supported version")
    default_config = CandidateDecisionTimeToResolutionUncertaintyScoreConfig()
    input_value = CandidateDecisionTimeToResolutionUncertaintyScoreInput(
        redacted_candidate_ref=result.redacted_candidate_ref,
        expected_resolution_days=result.expected_resolution_days,
        resolution_window_width_days=result.resolution_window_width_days,
        timing_confidence_score=result.timing_confidence_score,
        catalyst_specificity_score=result.catalyst_specificity_score,
        evidence_freshness_score=result.evidence_freshness_score,
        settlement_rule_clarity_score=result.settlement_rule_clarity_score,
    )
    metrics = _score_metrics(input_value, default_config)
    for field_name in (
        "expected_resolution_days_component_score",
        "resolution_window_width_days_component_score",
        "timing_confidence_component_score",
        "catalyst_specificity_component_score",
        "evidence_freshness_component_score",
        "settlement_rule_clarity_component_score",
        "uncertainty_score",
    ):
        if getattr(result, field_name) != metrics[field_name]:
            raise ValueError(f"{field_name} must match score inputs")
    levels = metrics["levels"]
    if type(levels) is not dict:
        raise ValueError("levels must be a dict")
    if result.status != _status_from_levels(levels):
        raise ValueError("status must match score inputs")
    if result.hard_flag_codes != _hard_flag_codes(levels):
        raise ValueError("hard_flag_codes must match score inputs")
    if result.reason_codes != _reason_codes(result.status, levels):
        raise ValueError("reason_codes must match score inputs")


def _validate_config(
    config: CandidateDecisionTimeToResolutionUncertaintyScoreConfig,
) -> None:
    if config.max_pass_expected_resolution_days > config.max_watch_expected_resolution_days:
        raise ValueError(
            "max_pass_expected_resolution_days must not exceed watch threshold",
        )
    if (
        config.max_pass_resolution_window_width_days
        > config.max_watch_resolution_window_width_days
    ):
        raise ValueError(
            "max_pass_resolution_window_width_days must not exceed watch threshold",
        )
    for pass_field, watch_field in (
        ("min_pass_timing_confidence_score", "min_watch_timing_confidence_score"),
        ("min_pass_catalyst_specificity_score", "min_watch_catalyst_specificity_score"),
        ("min_pass_evidence_freshness_score", "min_watch_evidence_freshness_score"),
        (
            "min_pass_settlement_rule_clarity_score",
            "min_watch_settlement_rule_clarity_score",
        ),
        ("min_pass_uncertainty_score", "min_watch_uncertainty_score"),
    ):
        if getattr(config, watch_field) > getattr(config, pass_field):
            raise ValueError(f"{watch_field} must not exceed pass threshold")
    weights_sum = _normalize_decimal(
        "weights_sum",
        config.expected_resolution_days_weight
        + config.resolution_window_width_days_weight
        + config.timing_confidence_score_weight
        + config.catalyst_specificity_score_weight
        + config.evidence_freshness_score_weight
        + config.settlement_rule_clarity_score_weight,
    )
    if weights_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
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


def _require_redacted_candidate_ref(value: object) -> str:
    _require_public_string("redacted_candidate_ref", value)
    if type(value) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if not value.startswith(prefix) or len(digest) != 64:
        raise ValueError("redacted_candidate_ref must use candidate_ref_ plus digest")
    if any(char not in HEX_CHARS for char in digest):
        raise ValueError("redacted_candidate_ref must use lowercase hex digest")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_digest(value: object) -> str:
    _require_public_string("derived_validation_digest", value)
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError("derived_validation_digest must be lowercase sha256 hex")
    return value


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _result_values_without_digest(
    result: CandidateDecisionTimeToResolutionUncertaintyScoreResult,
) -> dict[str, object]:
    values = asdict(result)
    values.pop("derived_validation_digest")
    return values


def _result_digest_from_values(values: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(values),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _require_payload_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")


def _walk_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_public_key(key)
            _walk_public_payload(child)
        return
    if type(value) is list:
        for child in value:
            _walk_public_payload(child)
        return
    if type(value) in (int, float, Decimal) and type(value) is not bool:
        raise ValueError("numeric public payload values must be decimal strings")
    if type(value) is str:
        _reject_public_string_value(value)


def _reject_public_key(key: str) -> None:
    lowered = key.lower()
    if lowered == "redacted_candidate_ref":
        return
    for item in _UNSAFE_KEY_PARTS:
        term = "".join(item[:-1])
        message = item[-1]
        if term in lowered:
            raise ValueError(f"{message} public payload field is not allowed")


def _reject_public_string_value(value: str) -> None:
    lowered = value.lower()
    if lowered in _UNSAFE_STATUS_VALUES:
        raise ValueError("status value must use pass, watch, or block")
    if lowered.startswith("candidate_ref_"):
        _require_redacted_candidate_ref(value)
        return
    for item in _UNSAFE_VALUE_PARTS:
        term = "".join(item[:-1])
        message = item[-1]
        if term and term in lowered:
            raise ValueError(f"{message} public payload value is not allowed")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION",
    "TIME_TO_RESOLUTION_UNCERTAINTY_STATUSES",
    "CandidateDecisionTimeToResolutionUncertaintyScoreConfig",
    "CandidateDecisionTimeToResolutionUncertaintyScoreInput",
    "CandidateDecisionTimeToResolutionUncertaintyScoreResult",
    "score_candidate_decision_time_to_resolution_uncertainty_score",
    "candidate_decision_time_to_resolution_uncertainty_score_payload",
    "validate_candidate_decision_time_to_resolution_uncertainty_score_public_payload",
)
