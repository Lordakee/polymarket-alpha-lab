"""Pure report-only early signal noise scoring."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_EARLY_SIGNAL_NOISE_SCORE_CONFIG_VERSION = (
    "candidate-decision-early-signal-noise-score-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

EARLY_SIGNAL_NOISE_STATUSES = ("pass", "watch", "block")

_BASE_REASON_CODE = "candidate_decision_early_signal_noise_score"
_SCORE_FIELDS = (
    "signal_count",
    "independent_signal_ratio",
    "contradiction_ratio",
    "volatility_score",
    "rumor_risk_score",
    "source_quality_score",
    "recency_score",
    "weighted_noise_score",
)
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
    ("to", "ken"),
    ("sec", "ret"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("tr", "ade"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmend"),
    ("position", "_size"),
    ("pos", "ition", "-sizing"),
    ("pos", "ition", "_sizing"),
)
_UNSAFE_PUBLIC_VALUE_PARTS = (
    ("candidate", "_id"),
    ("market", "_id"),
    ("market", "_sl", "ug"),
    ("market", "_ques", "tion"),
    ("source", "_re", "f"),
    ("source", "_ur", "l"),
    ("source", "_te", "xt"),
    ("private", "_key"),
    ("to", "ken"),
    ("sec", "ret"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tr", "ade"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmend"),
    ("ht", "tp"),
    (":", "/", "/"),
    ("d", "sn"),
    ("table", "_name"),
    ("position", "_size"),
    ("pos", "ition", "-sizing"),
    ("pos", "ition", " sizing"),
)
_SENSITIVE_REFERENCE_PARTS = _UNSAFE_PUBLIC_VALUE_PARTS + (
    ("raw", "_candidate"),
)


@dataclass(frozen=True)
class CandidateDecisionEarlySignalNoiseScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_EARLY_SIGNAL_NOISE_SCORE_CONFIG_VERSION
    )
    min_pass_signal_count: Decimal = Decimal("3.000000")
    min_watch_signal_count: Decimal = Decimal("1.000000")
    min_pass_independent_signal_ratio: Decimal = Decimal("0.750000")
    min_watch_independent_signal_ratio: Decimal = Decimal("0.500000")
    max_pass_contradiction_ratio: Decimal = Decimal("0.200000")
    max_watch_contradiction_ratio: Decimal = Decimal("0.500000")
    max_pass_volatility_score: Decimal = Decimal("0.250000")
    max_watch_volatility_score: Decimal = Decimal("0.600000")
    max_pass_rumor_risk_score: Decimal = Decimal("0.200000")
    max_watch_rumor_risk_score: Decimal = Decimal("0.500000")
    min_pass_source_quality_score: Decimal = Decimal("0.700000")
    min_watch_source_quality_score: Decimal = Decimal("0.400000")
    min_pass_recency_score: Decimal = Decimal("0.600000")
    min_watch_recency_score: Decimal = Decimal("0.300000")
    max_pass_noise_score: Decimal = Decimal("0.250000")
    max_watch_noise_score: Decimal = Decimal("0.500000")
    independent_signal_weight: Decimal = Decimal("1.000000")
    contradiction_weight: Decimal = Decimal("1.000000")
    volatility_weight: Decimal = Decimal("1.000000")
    rumor_risk_weight: Decimal = Decimal("1.000000")
    source_quality_weight: Decimal = Decimal("1.000000")
    recency_weight: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEarlySignalNoiseScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionEarlySignalNoiseScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("min_pass_signal_count", "min_watch_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_independent_signal_ratio",
            "min_watch_independent_signal_ratio",
            "max_pass_contradiction_ratio",
            "max_watch_contradiction_ratio",
            "max_pass_volatility_score",
            "max_watch_volatility_score",
            "max_pass_rumor_risk_score",
            "max_watch_rumor_risk_score",
            "min_pass_source_quality_score",
            "min_watch_source_quality_score",
            "min_pass_recency_score",
            "min_watch_recency_score",
            "max_pass_noise_score",
            "max_watch_noise_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_signal_weight",
            "contradiction_weight",
            "volatility_weight",
            "rumor_risk_weight",
            "source_quality_weight",
            "recency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config_thresholds(self)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionEarlySignalNoiseScoreInput:
    redacted_candidate_ref: str
    signal_count: Decimal
    independent_signal_ratio: Decimal
    contradiction_ratio: Decimal
    volatility_score: Decimal
    rumor_risk_score: Decimal
    source_quality_score: Decimal
    recency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEarlySignalNoiseScoreInput:
            raise ValueError(
                "input_value must be a CandidateDecisionEarlySignalNoiseScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        object.__setattr__(
            self,
            "signal_count",
            _normalize_count_decimal("signal_count", self.signal_count),
        )
        for field_name in (
            "independent_signal_ratio",
            "contradiction_ratio",
            "volatility_score",
            "rumor_risk_score",
            "source_quality_score",
            "recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_safety_flags("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionEarlySignalNoiseScoreReport:
    config_version: str
    redacted_candidate_ref: str
    signal_count: Decimal
    independent_signal_ratio: Decimal
    contradiction_ratio: Decimal
    volatility_score: Decimal
    rumor_risk_score: Decimal
    source_quality_score: Decimal
    recency_score: Decimal
    independence_noise_score: Decimal
    source_quality_noise_score: Decimal
    recency_noise_score: Decimal
    weighted_noise_score: Decimal
    status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    independent_signal_weight: Decimal = Decimal("1.000000")
    contradiction_weight: Decimal = Decimal("1.000000")
    volatility_weight: Decimal = Decimal("1.000000")
    rumor_risk_weight: Decimal = Decimal("1.000000")
    source_quality_weight: Decimal = Decimal("1.000000")
    recency_weight: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionEarlySignalNoiseScoreReport:
            raise ValueError(
                "report must be a CandidateDecisionEarlySignalNoiseScoreReport",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        object.__setattr__(
            self,
            "signal_count",
            _normalize_count_decimal("signal_count", self.signal_count),
        )
        for field_name in (
            "independent_signal_ratio",
            "contradiction_ratio",
            "volatility_score",
            "rumor_risk_score",
            "source_quality_score",
            "recency_score",
            "independence_noise_score",
            "source_quality_noise_score",
            "recency_noise_score",
            "weighted_noise_score",
            "independent_signal_weight",
            "contradiction_weight",
            "volatility_weight",
            "rumor_risk_weight",
            "source_quality_weight",
            "recency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_report_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, EARLY_SIGNAL_NOISE_STATUSES)
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
        _require_validation_digest(self.derived_validation_digest)
        _require_safety_flags("report", self)
        _validate_report_metrics(self)
        _validate_report_reasons(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_early_signal_noise_score_payload(self)


def score_candidate_decision_early_signal_noise(
    input_value: CandidateDecisionEarlySignalNoiseScoreInput,
    *,
    config: CandidateDecisionEarlySignalNoiseScoreConfig,
) -> CandidateDecisionEarlySignalNoiseScoreReport:
    if type(input_value) is not CandidateDecisionEarlySignalNoiseScoreInput:
        raise ValueError(
            "input_value must be a CandidateDecisionEarlySignalNoiseScoreInput",
        )
    if type(config) is not CandidateDecisionEarlySignalNoiseScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionEarlySignalNoiseScoreConfig",
        )
    _require_safety_flags("input_value", input_value)
    _require_safety_flags("config", config)

    metrics = _score_metrics(input_value, config)
    levels = _status_levels(input_value, metrics["weighted_noise_score"], config)
    status = _status_from_levels(levels)
    hard_flags = _hard_flag_codes(levels)
    report_values: dict[str, object] = {
        "config_version": config.config_version,
        "redacted_candidate_ref": input_value.redacted_candidate_ref,
        "signal_count": input_value.signal_count,
        "independent_signal_ratio": input_value.independent_signal_ratio,
        "contradiction_ratio": input_value.contradiction_ratio,
        "volatility_score": input_value.volatility_score,
        "rumor_risk_score": input_value.rumor_risk_score,
        "source_quality_score": input_value.source_quality_score,
        "recency_score": input_value.recency_score,
        "independence_noise_score": metrics["independence_noise_score"],
        "source_quality_noise_score": metrics["source_quality_noise_score"],
        "recency_noise_score": metrics["recency_noise_score"],
        "weighted_noise_score": metrics["weighted_noise_score"],
        "status": status,
        "hard_flag_codes": hard_flags,
        "reason_codes": _reason_codes(status, levels),
        "independent_signal_weight": config.independent_signal_weight,
        "contradiction_weight": config.contradiction_weight,
        "volatility_weight": config.volatility_weight,
        "rumor_risk_weight": config.rumor_risk_weight,
        "source_quality_weight": config.source_quality_weight,
        "recency_weight": config.recency_weight,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionEarlySignalNoiseScoreReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def candidate_decision_early_signal_noise_score_payload(
    report: CandidateDecisionEarlySignalNoiseScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionEarlySignalNoiseScoreReport:
        raise ValueError("report must be a CandidateDecisionEarlySignalNoiseScoreReport")
    _require_safety_flags("report", report)
    _validate_report_metrics(report)
    _validate_report_reasons(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_early_signal_noise_score_public_payload(payload)
    return payload


def validate_candidate_decision_early_signal_noise_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_live_surface_fields(
        "candidate decision early signal noise payload",
        payload,
    )
    _reject_unsafe_public_entries(payload)
    _reject_numeric_public_values(payload)
    _require_public_payload_flags(payload)
    return True


def _score_metrics(
    input_value: CandidateDecisionEarlySignalNoiseScoreInput,
    config: CandidateDecisionEarlySignalNoiseScoreConfig,
) -> dict[str, Decimal]:
    independence_noise_score = _normalize_probability(
        "independence_noise_score",
        ONE - input_value.independent_signal_ratio,
    )
    source_quality_noise_score = _normalize_probability(
        "source_quality_noise_score",
        ONE - input_value.source_quality_score,
    )
    recency_noise_score = _normalize_probability(
        "recency_noise_score",
        ONE - input_value.recency_score,
    )
    weighted_noise_score = _weighted_average(
        (
            (independence_noise_score, config.independent_signal_weight),
            (input_value.contradiction_ratio, config.contradiction_weight),
            (input_value.volatility_score, config.volatility_weight),
            (input_value.rumor_risk_score, config.rumor_risk_weight),
            (source_quality_noise_score, config.source_quality_weight),
            (recency_noise_score, config.recency_weight),
        ),
    )
    return {
        "independence_noise_score": independence_noise_score,
        "source_quality_noise_score": source_quality_noise_score,
        "recency_noise_score": recency_noise_score,
        "weighted_noise_score": weighted_noise_score,
    }


def _status_levels(
    input_value: CandidateDecisionEarlySignalNoiseScoreInput,
    weighted_noise_score: Decimal,
    config: CandidateDecisionEarlySignalNoiseScoreConfig,
) -> dict[str, str]:
    return {
        "signal_count": _min_threshold_level(
            input_value.signal_count,
            config.min_pass_signal_count,
            config.min_watch_signal_count,
        ),
        "independent_signal_ratio": _min_threshold_level(
            input_value.independent_signal_ratio,
            config.min_pass_independent_signal_ratio,
            config.min_watch_independent_signal_ratio,
        ),
        "contradiction_ratio": _max_threshold_level(
            input_value.contradiction_ratio,
            config.max_pass_contradiction_ratio,
            config.max_watch_contradiction_ratio,
        ),
        "volatility_score": _max_threshold_level(
            input_value.volatility_score,
            config.max_pass_volatility_score,
            config.max_watch_volatility_score,
        ),
        "rumor_risk_score": _max_threshold_level(
            input_value.rumor_risk_score,
            config.max_pass_rumor_risk_score,
            config.max_watch_rumor_risk_score,
        ),
        "source_quality_score": _min_threshold_level(
            input_value.source_quality_score,
            config.min_pass_source_quality_score,
            config.min_watch_source_quality_score,
        ),
        "recency_score": _min_threshold_level(
            input_value.recency_score,
            config.min_pass_recency_score,
            config.min_watch_recency_score,
        ),
        "weighted_noise_score": _max_threshold_level(
            weighted_noise_score,
            config.max_pass_noise_score,
            config.max_watch_noise_score,
        ),
    }


def _status_from_levels(levels: Mapping[str, str]) -> str:
    if any(level == "block" for level in levels.values()):
        return "block"
    if all(level == "pass" for level in levels.values()):
        return "pass"
    return "watch"


def _hard_flag_codes(levels: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(
        f"{field_name}_block"
        for field_name in _SCORE_FIELDS
        if levels[field_name] == "block"
    )


def _reason_codes(status: str, levels: Mapping[str, str]) -> tuple[str, ...]:
    return (
        _BASE_REASON_CODE,
        f"status_{status}",
        *(f"{field_name}_{levels[field_name]}" for field_name in _SCORE_FIELDS),
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


def _weighted_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    numerator = ZERO
    denominator = ZERO
    for score, weight in values:
        numerator += score * weight
        denominator += weight
    if denominator <= ZERO:
        raise ValueError("weights must include at least one positive value")
    return _normalize_probability("weighted_noise_score", numerator / denominator)


def _validate_config_thresholds(
    config: CandidateDecisionEarlySignalNoiseScoreConfig,
) -> None:
    if config.min_watch_signal_count > config.min_pass_signal_count:
        raise ValueError("min_watch_signal_count must not exceed pass threshold")
    if (
        config.min_watch_independent_signal_ratio
        > config.min_pass_independent_signal_ratio
    ):
        raise ValueError(
            "min_watch_independent_signal_ratio must not exceed pass threshold",
        )
    if config.max_pass_contradiction_ratio > config.max_watch_contradiction_ratio:
        raise ValueError(
            "max_pass_contradiction_ratio must not exceed watch threshold",
        )
    if config.max_pass_volatility_score > config.max_watch_volatility_score:
        raise ValueError("max_pass_volatility_score must not exceed watch threshold")
    if config.max_pass_rumor_risk_score > config.max_watch_rumor_risk_score:
        raise ValueError("max_pass_rumor_risk_score must not exceed watch threshold")
    if config.min_watch_source_quality_score > config.min_pass_source_quality_score:
        raise ValueError(
            "min_watch_source_quality_score must not exceed pass threshold",
        )
    if config.min_watch_recency_score > config.min_pass_recency_score:
        raise ValueError("min_watch_recency_score must not exceed pass threshold")
    if config.max_pass_noise_score > config.max_watch_noise_score:
        raise ValueError("max_pass_noise_score must not exceed watch threshold")
    _weighted_average(
        (
            (ONE, config.independent_signal_weight),
            (ONE, config.contradiction_weight),
            (ONE, config.volatility_weight),
            (ONE, config.rumor_risk_weight),
            (ONE, config.source_quality_weight),
            (ONE, config.recency_weight),
        ),
    )


def _validate_report_metrics(
    report: CandidateDecisionEarlySignalNoiseScoreReport,
) -> None:
    expected_independence_noise = _normalize_probability(
        "independence_noise_score",
        ONE - report.independent_signal_ratio,
    )
    expected_source_quality_noise = _normalize_probability(
        "source_quality_noise_score",
        ONE - report.source_quality_score,
    )
    expected_recency_noise = _normalize_probability(
        "recency_noise_score",
        ONE - report.recency_score,
    )
    if report.independence_noise_score != expected_independence_noise:
        raise ValueError("independence_noise_score must match score inputs")
    if report.source_quality_noise_score != expected_source_quality_noise:
        raise ValueError("source_quality_noise_score must match score inputs")
    if report.recency_noise_score != expected_recency_noise:
        raise ValueError("recency_noise_score must match score inputs")
    if report.weighted_noise_score != _reported_weighted_noise_score(report):
        raise ValueError("weighted_noise_score must match score inputs")


def _reported_weighted_noise_score(
    report: CandidateDecisionEarlySignalNoiseScoreReport,
) -> Decimal:
    return _weighted_average(
        (
            (report.independence_noise_score, report.independent_signal_weight),
            (report.contradiction_ratio, report.contradiction_weight),
            (report.volatility_score, report.volatility_weight),
            (report.rumor_risk_score, report.rumor_risk_weight),
            (report.source_quality_noise_score, report.source_quality_weight),
            (report.recency_noise_score, report.recency_weight),
        ),
    )


def _validate_report_reasons(
    report: CandidateDecisionEarlySignalNoiseScoreReport,
) -> None:
    if len(report.reason_codes) != 10:
        raise ValueError("reason_codes must include all score classification reasons")
    if report.reason_codes[0] != _BASE_REASON_CODE:
        raise ValueError("reason_codes must start with score reason")
    if report.reason_codes[1] != f"status_{report.status}":
        raise ValueError("reason_codes must include status reason")
    levels: dict[str, str] = {}
    for reason_code, field_name in zip(report.reason_codes[2:], _SCORE_FIELDS):
        prefix = f"{field_name}_"
        if not reason_code.startswith(prefix):
            raise ValueError("reason_codes must include score classification reasons")
        level = reason_code.removeprefix(prefix)
        if level not in EARLY_SIGNAL_NOISE_STATUSES:
            raise ValueError("reason_codes must include known classification levels")
        levels[field_name] = level
    if _status_from_levels(levels) != report.status:
        raise ValueError("reason_codes must match status")
    if report.hard_flag_codes != _hard_flag_codes(levels):
        raise ValueError("hard_flag_codes must match blocking reasons")


def _report_values_without_digest(
    report: CandidateDecisionEarlySignalNoiseScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    _reject_unsafe_live_surface_fields(
        "candidate decision early signal noise digest",
        payload,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_redacted_candidate_ref(value: object) -> str:
    _require_canonical_string("redacted_candidate_ref", value)
    if type(value) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    lowered = value.lower()
    if lowered.startswith(("candidate-", "market-", "raw-")):
        raise ValueError("redacted_candidate_ref must not expose sensitive material")
    if _contains_part(lowered, _SENSITIVE_REFERENCE_PARTS):
        raise ValueError("redacted_candidate_ref must not expose sensitive material")
    return value


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative count Decimal")
    return normalized


def _normalize_report_decimal(field_name: str, value: object) -> Decimal:
    if field_name.endswith("_weight"):
        return _normalize_nonnegative_decimal(field_name, value)
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
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


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_validation_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")


def _require_safety_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    _reject_unsafe_live_surface_fields(label, value)


def _reject_unsafe_live_surface_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in _unsafe_live_fragments()):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _unsafe_live_fragments() -> tuple[str, ...]:
    return (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "exchange_mutation",
        "token",
        "secret",
    )


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _reject_unsafe_public_entries(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if _contains_part(lowered_key, _UNSAFE_PUBLIC_KEY_PARTS):
                raise ValueError(f"unsafe public payload field: {key}")
            _reject_unsafe_public_entries(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_entries(item)
        return
    if type(value) is str and _contains_part(value.lower(), _UNSAFE_PUBLIC_VALUE_PARTS):
        raise ValueError("unsafe public payload value")


def _reject_numeric_public_values(value: object) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (Decimal, float, int)):
        raise ValueError("numeric public payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_numeric_public_values(item)


def _require_public_payload_flags(payload: Mapping[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _contains_part(value: str, parts: tuple[tuple[str, ...], ...]) -> bool:
    return any("".join(part) in value for part in parts)


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_EARLY_SIGNAL_NOISE_SCORE_CONFIG_VERSION",
    "EARLY_SIGNAL_NOISE_STATUSES",
    "CandidateDecisionEarlySignalNoiseScoreConfig",
    "CandidateDecisionEarlySignalNoiseScoreInput",
    "CandidateDecisionEarlySignalNoiseScoreReport",
    "score_candidate_decision_early_signal_noise",
    "candidate_decision_early_signal_noise_score_payload",
    "validate_candidate_decision_early_signal_noise_score_public_payload",
)
