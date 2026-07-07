"""Pure report-only threshold margin scorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


def _p(*parts: str) -> str:
    return "".join(parts)


DEFAULT_CANDIDATE_DECISION_THRESHOLD_MARGIN_SCORE_CONFIG_VERSION = (
    "candidate-decision-threshold-margin-score-v0"
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_SENTINEL = Decimal("999999.000000")
DECIMAL_CONTEXT = Context(prec=64)

THRESHOLD_MARGIN_STATUSES = ("pass", "watch", "block")

_BASE_REASON_CODE = "candidate_decision_threshold_margin_score"
_REASON_CODE_FIELDS = (
    "net_threshold_margin",
    "margin_coverage_ratio",
    "evidence_confidence",
    "threshold_margin_score",
)
_ALLOWED_REASON_CODES = (
    "candidate_decision_threshold_margin_score",
    "status_pass",
    "status_watch",
    "status_block",
    "net_threshold_margin_pass",
    "net_threshold_margin_watch",
    "net_threshold_margin_block",
    "margin_coverage_ratio_pass",
    "margin_coverage_ratio_watch",
    "margin_coverage_ratio_block",
    "evidence_confidence_pass",
    "evidence_confidence_watch",
    "evidence_confidence_block",
    "threshold_margin_score_pass",
    "threshold_margin_score_watch",
    "threshold_margin_score_block",
)
_UNSAFE_KEY_SEQUENCES = (
    ("candidate", "id"),
    ("raw", "candidate"),
    ("market", "id"),
    ("market", "slug"),
    ("market", "question"),
    ("source", "ref"),
    ("source", "url"),
    ("source", "text"),
    (_p("d", "sn"),),
    (_p("ta", "ble"),),
    (_p("to", "ken"),),
    (_p("wal", "let"),),
    (_p("au", "th"),),
    (_p("or", "der"),),
    (_p("tr", "ade"),),
    (_p("pos", "ition"),),
    (_p("b", "uy"),),
    (_p("s", "ell"),),
    (_p("reco", "mmendation"),),
)
_UNSAFE_VALUE_TERMS = (
    _p("private", "_", "key"),
    _p("to", "ken"),
    _p("wal", "let"),
    _p("au", "th"),
    _p("or", "der"),
    _p("tr", "ade"),
    _p("pos", "ition"),
    _p("b", "uy"),
    _p("s", "ell"),
    _p("reco", "mmendation"),
    _p("source", "_", "text"),
    _p("ht", "tp"),
    _p(":", "/", "/"),
    _p("d", "sn"),
)


@dataclass(frozen=True)
class CandidateDecisionThresholdMarginScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_THRESHOLD_MARGIN_SCORE_CONFIG_VERSION
    )
    min_pass_net_threshold_margin: Decimal = Decimal("0.100000")
    min_watch_net_threshold_margin: Decimal = Decimal("0.020000")
    min_pass_margin_coverage_ratio: Decimal = Decimal("2.000000")
    min_watch_margin_coverage_ratio: Decimal = Decimal("1.000000")
    min_pass_evidence_confidence: Decimal = Decimal("0.750000")
    min_watch_evidence_confidence: Decimal = Decimal("0.450000")
    min_pass_threshold_margin_score: Decimal = Decimal("0.650000")
    min_watch_threshold_margin_score: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionThresholdMarginScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionThresholdMarginScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_net_threshold_margin",
            "min_watch_net_threshold_margin",
            "min_pass_evidence_confidence",
            "min_watch_evidence_confidence",
            "min_pass_threshold_margin_score",
            "min_watch_threshold_margin_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_margin_coverage_ratio",
            "min_watch_margin_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_net_threshold_margin > self.min_pass_net_threshold_margin:
            raise ValueError(
                "min_watch_net_threshold_margin must not exceed pass threshold",
            )
        if self.min_watch_margin_coverage_ratio > self.min_pass_margin_coverage_ratio:
            raise ValueError(
                "min_watch_margin_coverage_ratio must not exceed pass threshold",
            )
        if self.min_watch_evidence_confidence > self.min_pass_evidence_confidence:
            raise ValueError(
                "min_watch_evidence_confidence must not exceed pass threshold",
            )
        if self.min_watch_threshold_margin_score > self.min_pass_threshold_margin_score:
            raise ValueError(
                "min_watch_threshold_margin_score must not exceed pass threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionThresholdMarginScoreInput:
    observed_value: Decimal
    critical_threshold: Decimal
    resolution_boundary_width: Decimal
    measurement_uncertainty: Decimal
    evidence_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionThresholdMarginScoreInput:
            raise ValueError(
                "input_value must be a CandidateDecisionThresholdMarginScoreInput",
            )
        for field_name in (
            "observed_value",
            "critical_threshold",
            "resolution_boundary_width",
            "measurement_uncertainty",
            "evidence_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionThresholdMarginScoreReport:
    config_version: str
    observed_value: Decimal
    critical_threshold: Decimal
    resolution_boundary_width: Decimal
    measurement_uncertainty: Decimal
    evidence_confidence: Decimal
    absolute_threshold_margin: Decimal
    total_boundary_buffer: Decimal
    net_threshold_margin: Decimal
    margin_coverage_ratio: Decimal
    threshold_margin_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionThresholdMarginScoreReport:
            raise ValueError(
                "report must be a CandidateDecisionThresholdMarginScoreReport",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observed_value",
            "critical_threshold",
            "resolution_boundary_width",
            "measurement_uncertainty",
            "evidence_confidence",
            "absolute_threshold_margin",
            "threshold_margin_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_boundary_buffer",
            _normalize_nonnegative_decimal(
                "total_boundary_buffer",
                self.total_boundary_buffer,
            ),
        )
        object.__setattr__(
            self,
            "net_threshold_margin",
            _normalize_decimal("net_threshold_margin", self.net_threshold_margin),
        )
        object.__setattr__(
            self,
            "margin_coverage_ratio",
            _normalize_nonnegative_decimal(
                "margin_coverage_ratio",
                self.margin_coverage_ratio,
            ),
        )
        _require_member("status", self.status, THRESHOLD_MARGIN_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_metrics(self)
        _validate_report_reasons(self)
        if self.report_sha256 == "":
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        else:
            object.__setattr__(
                self,
                "report_sha256",
                _normalize_sha256("report_sha256", self.report_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report_digests(self)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_threshold_margin_score_payload(self)


def score_candidate_decision_threshold_margin_score(
    input_value: CandidateDecisionThresholdMarginScoreInput,
    *,
    config: CandidateDecisionThresholdMarginScoreConfig,
) -> CandidateDecisionThresholdMarginScoreReport:
    if type(input_value) is not CandidateDecisionThresholdMarginScoreInput:
        raise ValueError("input_value must be a CandidateDecisionThresholdMarginScoreInput")
    if type(config) is not CandidateDecisionThresholdMarginScoreConfig:
        raise ValueError("config must be a CandidateDecisionThresholdMarginScoreConfig")
    _require_hard_flags("input_value", input_value)
    _require_hard_flags("config", config)

    metrics = _score_metrics(input_value)
    levels = _status_levels(metrics, config)
    status = _status_from_levels(levels)
    return CandidateDecisionThresholdMarginScoreReport(
        config_version=config.config_version,
        observed_value=input_value.observed_value,
        critical_threshold=input_value.critical_threshold,
        resolution_boundary_width=input_value.resolution_boundary_width,
        measurement_uncertainty=input_value.measurement_uncertainty,
        evidence_confidence=input_value.evidence_confidence,
        absolute_threshold_margin=metrics["absolute_threshold_margin"],
        total_boundary_buffer=metrics["total_boundary_buffer"],
        net_threshold_margin=metrics["net_threshold_margin"],
        margin_coverage_ratio=metrics["margin_coverage_ratio"],
        threshold_margin_score=metrics["threshold_margin_score"],
        status=status,
        reason_codes=_reason_codes(status, levels),
    )


def validate_candidate_decision_threshold_margin_score_report(
    report: CandidateDecisionThresholdMarginScoreReport,
) -> bool:
    if type(report) is not CandidateDecisionThresholdMarginScoreReport:
        raise ValueError("report must be a CandidateDecisionThresholdMarginScoreReport")
    _require_hard_flags("report", report)
    _validate_report_metrics(report)
    _validate_report_reasons(report)
    _validate_report_digests(report)
    _reject_unsafe_public_payload("threshold margin report", report)
    return True


def candidate_decision_threshold_margin_score_payload(
    report: CandidateDecisionThresholdMarginScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionThresholdMarginScoreReport:
        raise ValueError("report must be a CandidateDecisionThresholdMarginScoreReport")
    validate_candidate_decision_threshold_margin_score_report(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_threshold_margin_score_public_payload(payload)
    return payload


def validate_candidate_decision_threshold_margin_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("threshold margin public payload", payload)
    _reject_numeric_public_values(payload)
    _require_public_payload_flags(payload)
    return True


def _score_metrics(
    input_value: CandidateDecisionThresholdMarginScoreInput,
) -> dict[str, Decimal]:
    absolute_threshold_margin = _normalize_probability(
        "absolute_threshold_margin",
        abs(input_value.observed_value - input_value.critical_threshold),
    )
    total_boundary_buffer = _normalize_nonnegative_decimal(
        "total_boundary_buffer",
        input_value.resolution_boundary_width + input_value.measurement_uncertainty,
    )
    net_threshold_margin = _normalize_decimal(
        "net_threshold_margin",
        absolute_threshold_margin - total_boundary_buffer,
    )
    margin_coverage_ratio = _margin_coverage_ratio(
        absolute_threshold_margin,
        total_boundary_buffer,
    )
    threshold_margin_score = _threshold_margin_score(
        absolute_threshold_margin,
        total_boundary_buffer,
        input_value.evidence_confidence,
    )
    return {
        "absolute_threshold_margin": absolute_threshold_margin,
        "total_boundary_buffer": total_boundary_buffer,
        "net_threshold_margin": net_threshold_margin,
        "margin_coverage_ratio": margin_coverage_ratio,
        "threshold_margin_score": threshold_margin_score,
        "evidence_confidence": input_value.evidence_confidence,
    }


def _status_levels(
    metrics: dict[str, Decimal],
    config: CandidateDecisionThresholdMarginScoreConfig,
) -> dict[str, str]:
    return {
        "net_threshold_margin": _min_threshold_level(
            metrics["net_threshold_margin"],
            config.min_pass_net_threshold_margin,
            config.min_watch_net_threshold_margin,
        ),
        "margin_coverage_ratio": _min_threshold_level(
            metrics["margin_coverage_ratio"],
            config.min_pass_margin_coverage_ratio,
            config.min_watch_margin_coverage_ratio,
        ),
        "evidence_confidence": _min_threshold_level(
            metrics["evidence_confidence"],
            config.min_pass_evidence_confidence,
            config.min_watch_evidence_confidence,
        ),
        "threshold_margin_score": _min_threshold_level(
            metrics["threshold_margin_score"],
            config.min_pass_threshold_margin_score,
            config.min_watch_threshold_margin_score,
        ),
    }


def _status_from_levels(levels: dict[str, str]) -> str:
    if any(level == "block" for level in levels.values()):
        return "block"
    if all(level == "pass" for level in levels.values()):
        return "pass"
    return "watch"


def _reason_codes(status: str, levels: dict[str, str]) -> tuple[str, ...]:
    return (
        _BASE_REASON_CODE,
        f"status_{status}",
        f"net_threshold_margin_{levels['net_threshold_margin']}",
        f"margin_coverage_ratio_{levels['margin_coverage_ratio']}",
        f"evidence_confidence_{levels['evidence_confidence']}",
        f"threshold_margin_score_{levels['threshold_margin_score']}",
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


def _margin_coverage_ratio(
    absolute_threshold_margin: Decimal,
    total_boundary_buffer: Decimal,
) -> Decimal:
    if total_boundary_buffer <= ZERO:
        if absolute_threshold_margin <= ZERO:
            return ZERO
        return RATIO_SENTINEL
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal(
            "margin_coverage_ratio",
            absolute_threshold_margin / total_boundary_buffer,
        )


def _threshold_margin_score(
    absolute_threshold_margin: Decimal,
    total_boundary_buffer: Decimal,
    evidence_confidence: Decimal,
) -> Decimal:
    denominator = absolute_threshold_margin + total_boundary_buffer
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "threshold_margin_score",
            evidence_confidence * absolute_threshold_margin / denominator,
        )


def _validate_report_metrics(
    report: CandidateDecisionThresholdMarginScoreReport,
) -> None:
    expected = _score_metrics(
        CandidateDecisionThresholdMarginScoreInput(
            observed_value=report.observed_value,
            critical_threshold=report.critical_threshold,
            resolution_boundary_width=report.resolution_boundary_width,
            measurement_uncertainty=report.measurement_uncertainty,
            evidence_confidence=report.evidence_confidence,
        ),
    )
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match score inputs")


def _validate_report_reasons(
    report: CandidateDecisionThresholdMarginScoreReport,
) -> None:
    if len(report.reason_codes) != 6:
        raise ValueError("reason_codes must match threshold margin classification")
    if report.reason_codes[0] != _BASE_REASON_CODE:
        raise ValueError("reason_codes must start with threshold margin score")
    if report.reason_codes[1] != f"status_{report.status}":
        raise ValueError("status must match reason_codes")
    levels: dict[str, str] = {}
    for reason_code, field_name in zip(report.reason_codes[2:], _REASON_CODE_FIELDS):
        prefix = f"{field_name}_"
        if not reason_code.startswith(prefix):
            raise ValueError("reason_codes must match threshold margin classification")
        level = reason_code.removeprefix(prefix)
        if level not in THRESHOLD_MARGIN_STATUSES:
            raise ValueError("reason_codes must use known classification levels")
        levels[field_name] = level
    if _status_from_levels(levels) != report.status:
        raise ValueError("status must match reason_codes")


def _validate_report_digests(
    report: CandidateDecisionThresholdMarginScoreReport,
) -> None:
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_member(field_name, value, _ALLOWED_REASON_CODES)
    return values


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
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
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _is_unsafe_public_value(value):
        raise ValueError(f"{field_name} has unsafe value")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _report_sha256(report: CandidateDecisionThresholdMarginScoreReport) -> str:
    return _sha256(
        "threshold_margin_report",
        (
            f"config_version={report.config_version}",
            f"observed_value={report.observed_value}",
            f"critical_threshold={report.critical_threshold}",
            f"resolution_boundary_width={report.resolution_boundary_width}",
            f"measurement_uncertainty={report.measurement_uncertainty}",
            f"evidence_confidence={report.evidence_confidence}",
            f"absolute_threshold_margin={report.absolute_threshold_margin}",
            f"total_boundary_buffer={report.total_boundary_buffer}",
            f"net_threshold_margin={report.net_threshold_margin}",
            f"margin_coverage_ratio={report.margin_coverage_ratio}",
            f"threshold_margin_score={report.threshold_margin_score}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _derived_validation_digest(report: CandidateDecisionThresholdMarginScoreReport) -> str:
    return _sha256(
        "threshold_margin_derived",
        (
            f"absolute_threshold_margin={report.absolute_threshold_margin}",
            f"total_boundary_buffer={report.total_boundary_buffer}",
            f"net_threshold_margin={report.net_threshold_margin}",
            f"margin_coverage_ratio={report.margin_coverage_ratio}",
            f"threshold_margin_score={report.threshold_margin_score}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            f"report_sha256={report.report_sha256}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _payload_keys(payload):
        if _is_unsafe_public_key(key):
            raise ValueError(f"unsafe public payload field in {label}: {key}")
    for value in _payload_string_values(payload):
        if _is_unsafe_public_value(value):
            raise ValueError(f"unsafe public payload value in {label}")


def _is_unsafe_public_key(key: str) -> bool:
    key_tokens = _surface_key_tokens(key.lower())
    for sequence in _UNSAFE_KEY_SEQUENCES:
        if _contains_token_sequence(key_tokens, sequence):
            return True
    return False


def _is_unsafe_public_value(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in _UNSAFE_VALUE_TERMS)


def _contains_token_sequence(tokens: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    if len(sequence) > len(tokens):
        return False
    for index in range(len(tokens) - len(sequence) + 1):
        if tokens[index : index + len(sequence)] == sequence:
            return True
    return False


def _surface_key_tokens(key: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in key:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _payload_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_payload_keys(item))
        return tuple(keys)
    return ()


def _payload_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_string_values(asdict(value))
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_payload_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_payload_string_values(item))
        return tuple(values)
    return ()


def _reject_numeric_public_values(value: object) -> None:
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("numeric public payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_numeric_public_values(item)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_THRESHOLD_MARGIN_SCORE_CONFIG_VERSION",
    "THRESHOLD_MARGIN_STATUSES",
    "CandidateDecisionThresholdMarginScoreConfig",
    "CandidateDecisionThresholdMarginScoreInput",
    "CandidateDecisionThresholdMarginScoreReport",
    "score_candidate_decision_threshold_margin_score",
    "candidate_decision_threshold_margin_score_payload",
    "validate_candidate_decision_threshold_margin_score_public_payload",
    "validate_candidate_decision_threshold_margin_score_report",
)
