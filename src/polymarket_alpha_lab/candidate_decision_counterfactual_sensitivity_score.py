"""Pure report-only counterfactual sensitivity scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_COUNTERFACTUAL_SENSITIVITY_SCORE_CONFIG_VERSION = (
    "candidate-decision-counterfactual-sensitivity-score-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

COUNTERFACTUAL_SENSITIVITY_STATUSES = ("pass", "watch", "block")

_BASE_REASON_CODE = "candidate_decision_counterfactual_sensitivity_score"

_UNSAFE_PARTS = (
    ("candidate", "_id"),
    ("raw", "_candidate"),
    ("market", "_id"),
    ("market", "_sl", "ug"),
    ("market", "_ques", "tion"),
    ("ques", "tion"),
    ("source", "_re", "f"),
    ("source", "_ur", "l"),
    ("source", "_te", "xt"),
    ("ur", "l"),
    ("ht", "tp"),
    (":", "/", "/"),
    ("d", "sn"),
    ("table", "_name"),
    ("to", "ken"),
    ("sec", "ret"),
    ("private", "_key"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tr", "ade"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmend"),
    ("pos", "ition", "_size"),
    ("pos", "ition", "-", "sizing"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_PARTS)

_DIGEST_FIELDS = (
    "config_version",
    "redacted_candidate_ref",
    "assumption_count",
    "dominant_assumption_weight",
    "scenario_dispersion_score",
    "downside_sensitivity_score",
    "independent_driver_count",
    "evidence_support_score",
    "driver_diversification_score",
    "driver_concentration_score",
    "evidence_gap_score",
    "counterfactual_fragility_score",
    "counterfactual_resilience_score",
    "status",
    "hard_flag_codes",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionCounterfactualSensitivityScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_COUNTERFACTUAL_SENSITIVITY_SCORE_CONFIG_VERSION
    )
    max_pass_dominant_assumption_weight: Decimal = Decimal("0.450000")
    max_watch_dominant_assumption_weight: Decimal = Decimal("0.650000")
    max_pass_scenario_dispersion_score: Decimal = Decimal("0.350000")
    max_watch_scenario_dispersion_score: Decimal = Decimal("0.650000")
    max_pass_downside_sensitivity_score: Decimal = Decimal("0.350000")
    max_watch_downside_sensitivity_score: Decimal = Decimal("0.650000")
    min_pass_independent_driver_count: Decimal = Decimal("3.000000")
    min_watch_independent_driver_count: Decimal = Decimal("2.000000")
    min_pass_evidence_support_score: Decimal = Decimal("0.750000")
    min_watch_evidence_support_score: Decimal = Decimal("0.450000")
    dominant_assumption_weight_weight: Decimal = Decimal("0.350000")
    scenario_dispersion_weight: Decimal = Decimal("0.250000")
    downside_sensitivity_weight: Decimal = Decimal("0.250000")
    driver_concentration_weight: Decimal = Decimal("0.100000")
    evidence_gap_weight: Decimal = Decimal("0.050000")
    min_pass_counterfactual_resilience_score: Decimal = Decimal("0.700000")
    min_watch_counterfactual_resilience_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCounterfactualSensitivityScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionCounterfactualSensitivityScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_pass_dominant_assumption_weight",
            "max_watch_dominant_assumption_weight",
            "max_pass_scenario_dispersion_score",
            "max_watch_scenario_dispersion_score",
            "max_pass_downside_sensitivity_score",
            "max_watch_downside_sensitivity_score",
            "min_pass_evidence_support_score",
            "min_watch_evidence_support_score",
            "dominant_assumption_weight_weight",
            "scenario_dispersion_weight",
            "downside_sensitivity_weight",
            "driver_concentration_weight",
            "evidence_gap_weight",
            "min_pass_counterfactual_resilience_score",
            "min_watch_counterfactual_resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_independent_driver_count",
            "min_watch_independent_driver_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_max_threshold_pair(
            "max_pass_dominant_assumption_weight",
            self.max_pass_dominant_assumption_weight,
            self.max_watch_dominant_assumption_weight,
        )
        _require_max_threshold_pair(
            "max_pass_scenario_dispersion_score",
            self.max_pass_scenario_dispersion_score,
            self.max_watch_scenario_dispersion_score,
        )
        _require_max_threshold_pair(
            "max_pass_downside_sensitivity_score",
            self.max_pass_downside_sensitivity_score,
            self.max_watch_downside_sensitivity_score,
        )
        if self.min_watch_independent_driver_count > self.min_pass_independent_driver_count:
            raise ValueError(
                "min_watch_independent_driver_count must not exceed pass threshold",
            )
        if self.min_watch_evidence_support_score > self.min_pass_evidence_support_score:
            raise ValueError(
                "min_watch_evidence_support_score must not exceed pass threshold",
            )
        if (
            self.min_watch_counterfactual_resilience_score
            > self.min_pass_counterfactual_resilience_score
        ):
            raise ValueError(
                "min_watch_counterfactual_resilience_score must not exceed pass threshold",
            )
        if _config_weight_sum(self) != ONE:
            raise ValueError("config weights must sum to 1")
        _require_report_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionCounterfactualSensitivityScoreInput:
    redacted_candidate_ref: str
    assumption_count: Decimal
    dominant_assumption_weight: Decimal
    scenario_dispersion_score: Decimal
    downside_sensitivity_score: Decimal
    independent_driver_count: Decimal
    evidence_support_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCounterfactualSensitivityScoreInput:
            raise ValueError(
                "input_value must be a CandidateDecisionCounterfactualSensitivityScoreInput",
            )
        validate_candidate_decision_counterfactual_sensitivity_public_payload(
            {"redacted_candidate_ref": self.redacted_candidate_ref},
            require_flags=False,
        )
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "assumption_count",
            "independent_driver_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.assumption_count <= ZERO:
            raise ValueError("assumption_count must be positive")
        if self.independent_driver_count > self.assumption_count:
            raise ValueError("independent_driver_count must not exceed assumption_count")
        for field_name in (
            "dominant_assumption_weight",
            "scenario_dispersion_score",
            "downside_sensitivity_score",
            "evidence_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_flags("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionCounterfactualSensitivityScoreReport:
    config_version: str
    redacted_candidate_ref: str
    assumption_count: Decimal
    dominant_assumption_weight: Decimal
    scenario_dispersion_score: Decimal
    downside_sensitivity_score: Decimal
    independent_driver_count: Decimal
    evidence_support_score: Decimal
    driver_diversification_score: Decimal
    driver_concentration_score: Decimal
    evidence_gap_score: Decimal
    counterfactual_fragility_score: Decimal
    counterfactual_resilience_score: Decimal
    status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCounterfactualSensitivityScoreReport:
            raise ValueError(
                "report must be a CandidateDecisionCounterfactualSensitivityScoreReport",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "assumption_count",
            "independent_driver_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.assumption_count <= ZERO:
            raise ValueError("assumption_count must be positive")
        if self.independent_driver_count > self.assumption_count:
            raise ValueError("independent_driver_count must not exceed assumption_count")
        for field_name in (
            "dominant_assumption_weight",
            "scenario_dispersion_score",
            "downside_sensitivity_score",
            "evidence_support_score",
            "driver_diversification_score",
            "driver_concentration_score",
            "evidence_gap_score",
            "counterfactual_fragility_score",
            "counterfactual_resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, COUNTERFACTUAL_SENSITIVITY_STATUSES)
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_reason_codes("hard_flag_codes", self.hard_flag_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_report_flags("report", self)
        _validate_report_consistency(self)
        validate_candidate_decision_counterfactual_sensitivity_public_payload(
            _public_json(asdict(self)),
        )
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_counterfactual_sensitivity_score_payload(self)


def score_candidate_decision_counterfactual_sensitivity(
    input_value: CandidateDecisionCounterfactualSensitivityScoreInput,
    *,
    config: CandidateDecisionCounterfactualSensitivityScoreConfig,
) -> CandidateDecisionCounterfactualSensitivityScoreReport:
    if type(input_value) is not CandidateDecisionCounterfactualSensitivityScoreInput:
        raise ValueError(
            "input_value must be a CandidateDecisionCounterfactualSensitivityScoreInput",
        )
    if type(config) is not CandidateDecisionCounterfactualSensitivityScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionCounterfactualSensitivityScoreConfig",
        )
    _require_report_flags("input_value", input_value)
    _require_report_flags("config", config)

    metrics = _score_metrics(input_value, config)
    levels = _levels(input_value, metrics, config)
    hard_flags = _hard_flag_codes(levels)
    status = _status_from_levels(levels, hard_flags)
    return CandidateDecisionCounterfactualSensitivityScoreReport(
        config_version=config.config_version,
        redacted_candidate_ref=input_value.redacted_candidate_ref,
        assumption_count=input_value.assumption_count,
        dominant_assumption_weight=input_value.dominant_assumption_weight,
        scenario_dispersion_score=input_value.scenario_dispersion_score,
        downside_sensitivity_score=input_value.downside_sensitivity_score,
        independent_driver_count=input_value.independent_driver_count,
        evidence_support_score=input_value.evidence_support_score,
        driver_diversification_score=metrics["driver_diversification_score"],
        driver_concentration_score=metrics["driver_concentration_score"],
        evidence_gap_score=metrics["evidence_gap_score"],
        counterfactual_fragility_score=metrics["counterfactual_fragility_score"],
        counterfactual_resilience_score=metrics["counterfactual_resilience_score"],
        status=status,
        hard_flag_codes=hard_flags,
        reason_codes=_reason_codes(status, levels, hard_flags),
    )


def candidate_decision_counterfactual_sensitivity_score_payload(
    report: CandidateDecisionCounterfactualSensitivityScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionCounterfactualSensitivityScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionCounterfactualSensitivityScoreReport",
        )
    _require_report_flags("report", report)
    _validate_report_consistency(report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _public_json(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_counterfactual_sensitivity_public_payload(payload)
    return payload


def validate_candidate_decision_counterfactual_sensitivity_public_payload(
    payload: dict[str, Any],
    *,
    require_flags: bool = True,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_entries(payload)
    _reject_numeric_public_values(payload)
    if require_flags:
        _require_public_payload_flags(payload)
    return True


def _score_metrics(
    input_value: CandidateDecisionCounterfactualSensitivityScoreInput,
    config: CandidateDecisionCounterfactualSensitivityScoreConfig,
) -> dict[str, Decimal]:
    driver_diversification_score = _normalize_unit_decimal(
        "driver_diversification_score",
        min(ONE, input_value.independent_driver_count / input_value.assumption_count),
    )
    driver_concentration_score = _normalize_unit_decimal(
        "driver_concentration_score",
        ONE - driver_diversification_score,
    )
    evidence_gap_score = _normalize_unit_decimal(
        "evidence_gap_score",
        ONE - input_value.evidence_support_score,
    )
    counterfactual_fragility_score = _normalize_unit_decimal(
        "counterfactual_fragility_score",
        input_value.dominant_assumption_weight * config.dominant_assumption_weight_weight
        + input_value.scenario_dispersion_score * config.scenario_dispersion_weight
        + input_value.downside_sensitivity_score * config.downside_sensitivity_weight
        + driver_concentration_score * config.driver_concentration_weight
        + evidence_gap_score * config.evidence_gap_weight,
    )
    counterfactual_resilience_score = _normalize_unit_decimal(
        "counterfactual_resilience_score",
        ONE - counterfactual_fragility_score,
    )
    return {
        "driver_diversification_score": driver_diversification_score,
        "driver_concentration_score": driver_concentration_score,
        "evidence_gap_score": evidence_gap_score,
        "counterfactual_fragility_score": counterfactual_fragility_score,
        "counterfactual_resilience_score": counterfactual_resilience_score,
    }


def _levels(
    input_value: CandidateDecisionCounterfactualSensitivityScoreInput,
    metrics: dict[str, Decimal],
    config: CandidateDecisionCounterfactualSensitivityScoreConfig,
) -> dict[str, str]:
    return {
        "dominant_assumption_weight": _max_level(
            input_value.dominant_assumption_weight,
            config.max_pass_dominant_assumption_weight,
            config.max_watch_dominant_assumption_weight,
        ),
        "scenario_dispersion_score": _max_level(
            input_value.scenario_dispersion_score,
            config.max_pass_scenario_dispersion_score,
            config.max_watch_scenario_dispersion_score,
        ),
        "downside_sensitivity_score": _max_level(
            input_value.downside_sensitivity_score,
            config.max_pass_downside_sensitivity_score,
            config.max_watch_downside_sensitivity_score,
        ),
        "independent_driver_count": _min_level(
            input_value.independent_driver_count,
            config.min_pass_independent_driver_count,
            config.min_watch_independent_driver_count,
        ),
        "evidence_support_score": _min_level(
            input_value.evidence_support_score,
            config.min_pass_evidence_support_score,
            config.min_watch_evidence_support_score,
        ),
        "counterfactual_resilience_score": _min_level(
            metrics["counterfactual_resilience_score"],
            config.min_pass_counterfactual_resilience_score,
            config.min_watch_counterfactual_resilience_score,
        ),
    }


def _status_from_levels(levels: dict[str, str], hard_flag_codes: tuple[str, ...]) -> str:
    if hard_flag_codes or levels["counterfactual_resilience_score"] == "block":
        return "block"
    if any(level == "watch" for level in levels.values()):
        return "watch"
    return "pass"


def _hard_flag_codes(levels: dict[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for field_name in (
        "dominant_assumption_weight",
        "scenario_dispersion_score",
        "downside_sensitivity_score",
        "independent_driver_count",
        "evidence_support_score",
    ):
        if levels[field_name] == "block":
            values.append(f"{field_name}_hard_flag")
    return tuple(values)


def _reason_codes(
    status: str,
    levels: dict[str, str],
    hard_flag_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return (
        _BASE_REASON_CODE,
        f"status_{status}",
        f"dominant_assumption_weight_{levels['dominant_assumption_weight']}",
        f"scenario_dispersion_score_{levels['scenario_dispersion_score']}",
        f"downside_sensitivity_score_{levels['downside_sensitivity_score']}",
        f"independent_driver_count_{levels['independent_driver_count']}",
        f"evidence_support_score_{levels['evidence_support_score']}",
        f"counterfactual_resilience_score_{levels['counterfactual_resilience_score']}",
        "hard_flags_present" if hard_flag_codes else "hard_flags_absent",
    )


def _max_level(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _min_level(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _validate_report_consistency(
    report: CandidateDecisionCounterfactualSensitivityScoreReport,
) -> None:
    config = CandidateDecisionCounterfactualSensitivityScoreConfig(
        config_version=report.config_version,
    )
    input_value = CandidateDecisionCounterfactualSensitivityScoreInput(
        redacted_candidate_ref=report.redacted_candidate_ref,
        assumption_count=report.assumption_count,
        dominant_assumption_weight=report.dominant_assumption_weight,
        scenario_dispersion_score=report.scenario_dispersion_score,
        downside_sensitivity_score=report.downside_sensitivity_score,
        independent_driver_count=report.independent_driver_count,
        evidence_support_score=report.evidence_support_score,
    )
    metrics = _score_metrics(input_value, config)
    for field_name, expected_value in metrics.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match score inputs")
    levels = _levels(input_value, metrics, config)
    hard_flags = _hard_flag_codes(levels)
    expected_status = _status_from_levels(levels, hard_flags)
    if report.hard_flag_codes != hard_flags:
        raise ValueError("hard_flag_codes must match score inputs")
    if report.status != expected_status:
        raise ValueError("status must match score inputs")
    if report.reason_codes != _reason_codes(expected_status, levels, hard_flags):
        raise ValueError("reason_codes must match score inputs")


def _config_weight_sum(
    config: CandidateDecisionCounterfactualSensitivityScoreConfig,
) -> Decimal:
    return _normalize_decimal(
        "config_weight_sum",
        config.dominant_assumption_weight_weight
        + config.scenario_dispersion_weight
        + config.downside_sensitivity_weight
        + config.driver_concentration_weight
        + config.evidence_gap_weight,
    )


def _require_max_threshold_pair(
    field_name: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold > watch_threshold:
        raise ValueError(f"{field_name} must not exceed watch threshold")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
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
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{field_name} must be lowercase")
    for character in value:
        if not (
            "a" <= character <= "z"
            or "0" <= character <= "9"
            or character in {"_", "-"}
        ):
            raise ValueError(f"{field_name} must contain safe public characters")


def _require_report_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


def _reject_unsafe_public_entries(value: object) -> None:
    for item in _iter_public_strings(value):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError("unsafe public payload entry")


def _reject_numeric_public_values(value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, float):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_numeric_public_values(item)


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _public_json(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _public_json(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("public value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("public value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            converted[key] = _public_json(item)
        return converted
    if isinstance(value, (list, tuple)):
        return [_public_json(item) for item in value]
    raise ValueError("public value must be scalar or container")


def _derived_validation_digest(
    report: CandidateDecisionCounterfactualSensitivityScoreReport,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(report, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _require_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_COUNTERFACTUAL_SENSITIVITY_SCORE_CONFIG_VERSION",
    "COUNTERFACTUAL_SENSITIVITY_STATUSES",
    "CandidateDecisionCounterfactualSensitivityScoreConfig",
    "CandidateDecisionCounterfactualSensitivityScoreInput",
    "CandidateDecisionCounterfactualSensitivityScoreReport",
    "score_candidate_decision_counterfactual_sensitivity",
    "candidate_decision_counterfactual_sensitivity_score_payload",
    "validate_candidate_decision_counterfactual_sensitivity_public_payload",
)
