"""Pure report-only exogenous shock sensitivity scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_CANDIDATE_DECISION_EXOGENOUS_SHOCK_SENSITIVITY_SCORE_CONFIG_VERSION = (
    "candidate-decision-exogenous-shock-sensitivity-score-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

EXOGENOUS_SHOCK_SENSITIVITY_STATUSES = ("pass", "watch", "block")

_BASE_REASON_CODE = "candidate_decision_exogenous_shock_sensitivity_score"

_UNSAFE_PARTS = (
    ("candidate", "_", "id"),
    ("raw", "_", "candidate"),
    ("market", "_", "id"),
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
    "baseline_probability_move_bps",
    "historical_shock_frequency_score",
    "shock_driver_correlation_score",
    "external_dependency_score",
    "mitigation_coverage_score",
    "monitoring_latency_score",
    "normalized_probability_move_score",
    "mitigation_gap_score",
    "exogenous_shock_sensitivity_score",
    "exogenous_shock_resilience_score",
    "status",
    "hard_flag_codes",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionExogenousShockSensitivityScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_EXOGENOUS_SHOCK_SENSITIVITY_SCORE_CONFIG_VERSION
    )
    normalization_probability_move_bps: Decimal = Decimal("500.000000")
    max_pass_probability_move_bps: Decimal = Decimal("150.000000")
    max_watch_probability_move_bps: Decimal = Decimal("350.000000")
    max_pass_historical_shock_frequency_score: Decimal = Decimal("0.350000")
    max_watch_historical_shock_frequency_score: Decimal = Decimal("0.650000")
    max_pass_shock_driver_correlation_score: Decimal = Decimal("0.350000")
    max_watch_shock_driver_correlation_score: Decimal = Decimal("0.650000")
    max_pass_external_dependency_score: Decimal = Decimal("0.400000")
    max_watch_external_dependency_score: Decimal = Decimal("0.700000")
    min_pass_mitigation_coverage_score: Decimal = Decimal("0.700000")
    min_watch_mitigation_coverage_score: Decimal = Decimal("0.450000")
    max_pass_monitoring_latency_score: Decimal = Decimal("0.350000")
    max_watch_monitoring_latency_score: Decimal = Decimal("0.650000")
    max_pass_exogenous_shock_sensitivity_score: Decimal = Decimal("0.350000")
    max_watch_exogenous_shock_sensitivity_score: Decimal = Decimal("0.650000")
    probability_move_weight: Decimal = Decimal("0.300000")
    historical_shock_frequency_weight: Decimal = Decimal("0.200000")
    shock_driver_correlation_weight: Decimal = Decimal("0.200000")
    external_dependency_weight: Decimal = Decimal("0.150000")
    mitigation_gap_weight: Decimal = Decimal("0.100000")
    monitoring_latency_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionExogenousShockSensitivityScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionExogenousShockSensitivityScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "normalization_probability_move_bps",
            _normalize_positive_decimal(
                "normalization_probability_move_bps",
                self.normalization_probability_move_bps,
            ),
        )
        for field_name in (
            "max_pass_probability_move_bps",
            "max_watch_probability_move_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_historical_shock_frequency_score",
            "max_watch_historical_shock_frequency_score",
            "max_pass_shock_driver_correlation_score",
            "max_watch_shock_driver_correlation_score",
            "max_pass_external_dependency_score",
            "max_watch_external_dependency_score",
            "min_pass_mitigation_coverage_score",
            "min_watch_mitigation_coverage_score",
            "max_pass_monitoring_latency_score",
            "max_watch_monitoring_latency_score",
            "max_pass_exogenous_shock_sensitivity_score",
            "max_watch_exogenous_shock_sensitivity_score",
            "probability_move_weight",
            "historical_shock_frequency_weight",
            "shock_driver_correlation_weight",
            "external_dependency_weight",
            "mitigation_gap_weight",
            "monitoring_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_max_threshold_pair(
            "max_pass_probability_move_bps",
            self.max_pass_probability_move_bps,
            self.max_watch_probability_move_bps,
        )
        _require_max_threshold_pair(
            "max_pass_historical_shock_frequency_score",
            self.max_pass_historical_shock_frequency_score,
            self.max_watch_historical_shock_frequency_score,
        )
        _require_max_threshold_pair(
            "max_pass_shock_driver_correlation_score",
            self.max_pass_shock_driver_correlation_score,
            self.max_watch_shock_driver_correlation_score,
        )
        _require_max_threshold_pair(
            "max_pass_external_dependency_score",
            self.max_pass_external_dependency_score,
            self.max_watch_external_dependency_score,
        )
        _require_max_threshold_pair(
            "max_pass_monitoring_latency_score",
            self.max_pass_monitoring_latency_score,
            self.max_watch_monitoring_latency_score,
        )
        _require_max_threshold_pair(
            "max_pass_exogenous_shock_sensitivity_score",
            self.max_pass_exogenous_shock_sensitivity_score,
            self.max_watch_exogenous_shock_sensitivity_score,
        )
        if self.min_watch_mitigation_coverage_score > self.min_pass_mitigation_coverage_score:
            raise ValueError(
                "min_watch_mitigation_coverage_score must not exceed pass threshold",
            )
        if _config_weight_sum(self) != ONE:
            raise ValueError("config weights must sum to 1")
        _require_report_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionExogenousShockSensitivityScoreInput:
    baseline_probability_move_bps: Decimal
    historical_shock_frequency_score: Decimal
    shock_driver_correlation_score: Decimal
    external_dependency_score: Decimal
    mitigation_coverage_score: Decimal
    monitoring_latency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionExogenousShockSensitivityScoreInput:
            raise ValueError(
                "input_value must be a CandidateDecisionExogenousShockSensitivityScoreInput",
            )
        object.__setattr__(
            self,
            "baseline_probability_move_bps",
            _normalize_nonnegative_decimal(
                "baseline_probability_move_bps",
                self.baseline_probability_move_bps,
            ),
        )
        for field_name in (
            "historical_shock_frequency_score",
            "shock_driver_correlation_score",
            "external_dependency_score",
            "mitigation_coverage_score",
            "monitoring_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_flags("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionExogenousShockSensitivityScoreReport:
    config_version: str
    baseline_probability_move_bps: Decimal
    historical_shock_frequency_score: Decimal
    shock_driver_correlation_score: Decimal
    external_dependency_score: Decimal
    mitigation_coverage_score: Decimal
    monitoring_latency_score: Decimal
    normalized_probability_move_score: Decimal
    mitigation_gap_score: Decimal
    exogenous_shock_sensitivity_score: Decimal
    exogenous_shock_resilience_score: Decimal
    status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionExogenousShockSensitivityScoreReport:
            raise ValueError(
                "report must be a CandidateDecisionExogenousShockSensitivityScoreReport",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "baseline_probability_move_bps",
            _normalize_nonnegative_decimal(
                "baseline_probability_move_bps",
                self.baseline_probability_move_bps,
            ),
        )
        for field_name in (
            "historical_shock_frequency_score",
            "shock_driver_correlation_score",
            "external_dependency_score",
            "mitigation_coverage_score",
            "monitoring_latency_score",
            "normalized_probability_move_score",
            "mitigation_gap_score",
            "exogenous_shock_sensitivity_score",
            "exogenous_shock_resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, EXOGENOUS_SHOCK_SENSITIVITY_STATUSES)
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
        validate_candidate_decision_exogenous_shock_sensitivity_public_payload(
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
        return candidate_decision_exogenous_shock_sensitivity_score_payload(self)


def score_candidate_decision_exogenous_shock_sensitivity(
    input_value: CandidateDecisionExogenousShockSensitivityScoreInput,
    *,
    config: CandidateDecisionExogenousShockSensitivityScoreConfig,
) -> CandidateDecisionExogenousShockSensitivityScoreReport:
    if type(input_value) is not CandidateDecisionExogenousShockSensitivityScoreInput:
        raise ValueError(
            "input_value must be a CandidateDecisionExogenousShockSensitivityScoreInput",
        )
    if type(config) is not CandidateDecisionExogenousShockSensitivityScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionExogenousShockSensitivityScoreConfig",
        )
    _require_report_flags("input_value", input_value)
    _require_report_flags("config", config)

    metrics = _score_metrics(input_value, config)
    levels = _levels(input_value, metrics, config)
    hard_flags = _hard_flag_codes(levels)
    status = _status_from_levels(levels, hard_flags)
    return CandidateDecisionExogenousShockSensitivityScoreReport(
        config_version=config.config_version,
        baseline_probability_move_bps=input_value.baseline_probability_move_bps,
        historical_shock_frequency_score=input_value.historical_shock_frequency_score,
        shock_driver_correlation_score=input_value.shock_driver_correlation_score,
        external_dependency_score=input_value.external_dependency_score,
        mitigation_coverage_score=input_value.mitigation_coverage_score,
        monitoring_latency_score=input_value.monitoring_latency_score,
        normalized_probability_move_score=metrics["normalized_probability_move_score"],
        mitigation_gap_score=metrics["mitigation_gap_score"],
        exogenous_shock_sensitivity_score=metrics["exogenous_shock_sensitivity_score"],
        exogenous_shock_resilience_score=metrics["exogenous_shock_resilience_score"],
        status=status,
        hard_flag_codes=hard_flags,
        reason_codes=_reason_codes(status, levels, hard_flags),
    )


def candidate_decision_exogenous_shock_sensitivity_score_payload(
    report: CandidateDecisionExogenousShockSensitivityScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionExogenousShockSensitivityScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionExogenousShockSensitivityScoreReport",
        )
    _require_report_flags("report", report)
    _validate_report_consistency(report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _public_json(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_exogenous_shock_sensitivity_public_payload(payload)
    return payload


def validate_candidate_decision_exogenous_shock_sensitivity_public_payload(
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
    input_value: CandidateDecisionExogenousShockSensitivityScoreInput,
    config: CandidateDecisionExogenousShockSensitivityScoreConfig,
) -> dict[str, Decimal]:
    normalized_probability_move_score = _normalize_unit_decimal(
        "normalized_probability_move_score",
        min(ONE, input_value.baseline_probability_move_bps / config.normalization_probability_move_bps),
    )
    mitigation_gap_score = _normalize_unit_decimal(
        "mitigation_gap_score",
        ONE - input_value.mitigation_coverage_score,
    )
    exogenous_shock_sensitivity_score = _normalize_unit_decimal(
        "exogenous_shock_sensitivity_score",
        normalized_probability_move_score * config.probability_move_weight
        + input_value.historical_shock_frequency_score
        * config.historical_shock_frequency_weight
        + input_value.shock_driver_correlation_score
        * config.shock_driver_correlation_weight
        + input_value.external_dependency_score * config.external_dependency_weight
        + mitigation_gap_score * config.mitigation_gap_weight
        + input_value.monitoring_latency_score * config.monitoring_latency_weight,
    )
    exogenous_shock_resilience_score = _normalize_unit_decimal(
        "exogenous_shock_resilience_score",
        ONE - exogenous_shock_sensitivity_score,
    )
    return {
        "normalized_probability_move_score": normalized_probability_move_score,
        "mitigation_gap_score": mitigation_gap_score,
        "exogenous_shock_sensitivity_score": exogenous_shock_sensitivity_score,
        "exogenous_shock_resilience_score": exogenous_shock_resilience_score,
    }


def _levels(
    input_value: CandidateDecisionExogenousShockSensitivityScoreInput,
    metrics: dict[str, Decimal],
    config: CandidateDecisionExogenousShockSensitivityScoreConfig,
) -> dict[str, str]:
    return {
        "baseline_probability_move_bps": _max_level(
            input_value.baseline_probability_move_bps,
            config.max_pass_probability_move_bps,
            config.max_watch_probability_move_bps,
        ),
        "historical_shock_frequency_score": _max_level(
            input_value.historical_shock_frequency_score,
            config.max_pass_historical_shock_frequency_score,
            config.max_watch_historical_shock_frequency_score,
        ),
        "shock_driver_correlation_score": _max_level(
            input_value.shock_driver_correlation_score,
            config.max_pass_shock_driver_correlation_score,
            config.max_watch_shock_driver_correlation_score,
        ),
        "external_dependency_score": _max_level(
            input_value.external_dependency_score,
            config.max_pass_external_dependency_score,
            config.max_watch_external_dependency_score,
        ),
        "mitigation_coverage_score": _min_level(
            input_value.mitigation_coverage_score,
            config.min_pass_mitigation_coverage_score,
            config.min_watch_mitigation_coverage_score,
        ),
        "monitoring_latency_score": _max_level(
            input_value.monitoring_latency_score,
            config.max_pass_monitoring_latency_score,
            config.max_watch_monitoring_latency_score,
        ),
        "exogenous_shock_sensitivity_score": _max_level(
            metrics["exogenous_shock_sensitivity_score"],
            config.max_pass_exogenous_shock_sensitivity_score,
            config.max_watch_exogenous_shock_sensitivity_score,
        ),
    }


def _status_from_levels(levels: dict[str, str], hard_flag_codes: tuple[str, ...]) -> str:
    if hard_flag_codes or levels["exogenous_shock_sensitivity_score"] == "block":
        return "block"
    if any(level == "watch" for level in levels.values()):
        return "watch"
    return "pass"


def _hard_flag_codes(levels: dict[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for field_name in (
        "baseline_probability_move_bps",
        "historical_shock_frequency_score",
        "shock_driver_correlation_score",
        "external_dependency_score",
        "mitigation_coverage_score",
        "monitoring_latency_score",
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
        f"baseline_probability_move_bps_{levels['baseline_probability_move_bps']}",
        f"historical_shock_frequency_score_{levels['historical_shock_frequency_score']}",
        f"shock_driver_correlation_score_{levels['shock_driver_correlation_score']}",
        f"external_dependency_score_{levels['external_dependency_score']}",
        f"mitigation_coverage_score_{levels['mitigation_coverage_score']}",
        f"monitoring_latency_score_{levels['monitoring_latency_score']}",
        f"exogenous_shock_sensitivity_score_{levels['exogenous_shock_sensitivity_score']}",
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
    report: CandidateDecisionExogenousShockSensitivityScoreReport,
) -> None:
    config = CandidateDecisionExogenousShockSensitivityScoreConfig(
        config_version=report.config_version,
    )
    input_value = CandidateDecisionExogenousShockSensitivityScoreInput(
        baseline_probability_move_bps=report.baseline_probability_move_bps,
        historical_shock_frequency_score=report.historical_shock_frequency_score,
        shock_driver_correlation_score=report.shock_driver_correlation_score,
        external_dependency_score=report.external_dependency_score,
        mitigation_coverage_score=report.mitigation_coverage_score,
        monitoring_latency_score=report.monitoring_latency_score,
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
    config: CandidateDecisionExogenousShockSensitivityScoreConfig,
) -> Decimal:
    return _normalize_decimal(
        "config_weight_sum",
        config.probability_move_weight
        + config.historical_shock_frequency_weight
        + config.shock_driver_correlation_weight
        + config.external_dependency_weight
        + config.mitigation_gap_weight
        + config.monitoring_latency_weight,
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


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
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
    report: CandidateDecisionExogenousShockSensitivityScoreReport,
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
    "DEFAULT_CANDIDATE_DECISION_EXOGENOUS_SHOCK_SENSITIVITY_SCORE_CONFIG_VERSION",
    "EXOGENOUS_SHOCK_SENSITIVITY_STATUSES",
    "CandidateDecisionExogenousShockSensitivityScoreConfig",
    "CandidateDecisionExogenousShockSensitivityScoreInput",
    "CandidateDecisionExogenousShockSensitivityScoreReport",
    "score_candidate_decision_exogenous_shock_sensitivity",
    "candidate_decision_exogenous_shock_sensitivity_score_payload",
    "validate_candidate_decision_exogenous_shock_sensitivity_public_payload",
)
