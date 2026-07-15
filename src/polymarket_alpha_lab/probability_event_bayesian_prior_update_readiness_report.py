"""Read-only Bayesian prior update readiness report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


__all__ = (
    "BAYESIAN_PRIOR_UPDATE_STATUSES",
    "ProbabilityEventBayesianPriorUpdateReadinessInput",
    "ProbabilityEventBayesianPriorUpdateReadinessReport",
    "build_probability_event_bayesian_prior_update_readiness_report",
    "probability_event_bayesian_prior_update_readiness_report_digest",
    "probability_event_bayesian_prior_update_readiness_report_to_payload",
    "validate_probability_event_bayesian_prior_update_readiness_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MIN_RELIABILITY = Decimal("0.500000")
MIN_BASE_RATE_SAMPLE_COUNT = Decimal("50.000000")
MAX_CALIBRATION_ERROR = Decimal("0.150000")
MANUAL_SAMPLE_SCALE = Decimal("2500.000000")

BAYESIAN_PRIOR_UPDATE_STATUSES = (
    "ready",
    "manual_review",
    "blocked",
)
READY_REASON_CODE = "probability_event_bayesian_prior_update_ready"

REASON_SEQUENCE = (
    "bayesian_prior_update_prior_at_closed_boundary",
    "bayesian_prior_update_evidence_at_closed_boundary",
    "bayesian_prior_update_paper_only_flag_not_set",
    "bayesian_prior_update_report_only_flag_not_set",
    "bayesian_prior_update_readonly_flag_not_set",
    "bayesian_prior_update_low_evidence_reliability",
    "bayesian_prior_update_sparse_base_rate_sample",
    "bayesian_prior_update_high_calibration_error",
    READY_REASON_CODE,
)
BLOCKING_REASON_CODES = REASON_SEQUENCE[:5]
MANUAL_REVIEW_REASON_CODES = REASON_SEQUENCE[5:8]

PAYLOAD_FIELDS = (
    "prior_probability",
    "new_evidence_probability",
    "evidence_reliability_probability",
    "base_rate_sample_count",
    "calibration_error_probability",
    "update_status",
    "posterior_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)

PROBABILITY_FIELDS = (
    "prior_probability",
    "new_evidence_probability",
    "evidence_reliability_probability",
    "calibration_error_probability",
)

INPUT_DECIMAL_FIELDS = (
    *PROBABILITY_FIELDS,
    "base_rate_sample_count",
)

UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "postgres://",
    "postgresql://",
    "service_role",
    "bearer ",
)

READY_MANUAL_NEXT_STEP = (
    "Record the research-only posterior update for manual review; no "
    "parameter, "
    "or"
    "der"
    ", or execution change is a"
    "uthorized."
)
REVIEW_MANUAL_NEXT_STEP = (
    "Review reliability, base-rate depth, and calibration error before "
    "using the posterior as a research note."
)
BLOCKED_MANUAL_NEXT_STEP = (
    "Do not use this posterior in research notes until blocked inputs and "
    "mode flags are corrected."
)


class _BayesianPriorUpdatePublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _BayesianPriorUpdatePublicDataclass and issubclass(
                base,
                _BayesianPriorUpdatePublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventBayesianPriorUpdateReadinessInput(
    _BayesianPriorUpdatePublicDataclass,
):
    prior_probability: Decimal
    new_evidence_probability: Decimal
    evidence_reliability_probability: Decimal
    base_rate_sample_count: Decimal
    calibration_error_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventBayesianPriorUpdateReadinessInput,
            "Bayesian prior update input",
        )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "base_rate_sample_count",
            _normalize_sample_count(
                "base_rate_sample_count",
                self.base_rate_sample_count,
            ),
        )
        for field_name in ("paper_only", "report_only", "readonly"):
            _require_bool(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class ProbabilityEventBayesianPriorUpdateReadinessReport(
    _BayesianPriorUpdatePublicDataclass,
):
    prior_probability: Decimal
    new_evidence_probability: Decimal
    evidence_reliability_probability: Decimal
    base_rate_sample_count: Decimal
    calibration_error_probability: Decimal
    update_status: str
    posterior_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventBayesianPriorUpdateReadinessReport,
            "Bayesian prior update report",
        )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "base_rate_sample_count",
            _normalize_sample_count(
                "base_rate_sample_count",
                self.base_rate_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "posterior_probability",
            _normalize_probability(
                "posterior_probability",
                self.posterior_probability,
            ),
        )
        object.__setattr__(
            self,
            "update_status",
            _normalize_status("update_status", self.update_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if type(self.manual_next_step) is not str:
            raise ValueError("manual_next_step must be a string")
        for field_name in ("paper_only", "report_only", "readonly"):
            _require_bool(field_name, getattr(self, field_name))
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_bayesian_prior_update_readiness_report_to_payload(self)

    @property
    def payload_digest(self) -> str:
        return probability_event_bayesian_prior_update_readiness_report_digest(self)


def build_probability_event_bayesian_prior_update_readiness_report(
    readiness: ProbabilityEventBayesianPriorUpdateReadinessInput,
) -> ProbabilityEventBayesianPriorUpdateReadinessReport:
    if type(readiness) is not ProbabilityEventBayesianPriorUpdateReadinessInput:
        raise ValueError(
            "readiness must be a ProbabilityEventBayesianPriorUpdateReadinessInput",
        )

    reason_codes = _find_reason_codes(readiness)
    update_status = _status_for_reason_codes(reason_codes)
    return ProbabilityEventBayesianPriorUpdateReadinessReport(
        prior_probability=readiness.prior_probability,
        new_evidence_probability=readiness.new_evidence_probability,
        evidence_reliability_probability=readiness.evidence_reliability_probability,
        base_rate_sample_count=readiness.base_rate_sample_count,
        calibration_error_probability=readiness.calibration_error_probability,
        update_status=update_status,
        posterior_probability=_posterior_probability(readiness),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(update_status),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_bayesian_prior_update_readiness_report_to_payload(
    report: ProbabilityEventBayesianPriorUpdateReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventBayesianPriorUpdateReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventBayesianPriorUpdateReadinessReport",
        )
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "prior_probability": report.prior_probability,
            "new_evidence_probability": report.new_evidence_probability,
            "evidence_reliability_probability": report.evidence_reliability_probability,
            "base_rate_sample_count": report.base_rate_sample_count,
            "calibration_error_probability": report.calibration_error_probability,
            "update_status": report.update_status,
            "posterior_probability": report.posterior_probability,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_bayesian_prior_update_readiness_public_payload(payload)
    return payload


def probability_event_bayesian_prior_update_readiness_report_digest(
    report: ProbabilityEventBayesianPriorUpdateReadinessReport,
) -> str:
    payload = probability_event_bayesian_prior_update_readiness_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_bayesian_prior_update_readiness_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload must match the canonical Bayesian update schema")
    _reject_unsafe_public_values(payload)
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    source = _input_from_payload(payload)
    expected_reason_codes = _find_reason_codes(source)
    payload_reason_codes = _payload_reason_codes(payload["reason_codes"])
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in payload_reason_codes):
        expected_status = "blocked"
    else:
        expected_status = _status_for_reason_codes(expected_reason_codes)
    expected_next_step = _manual_next_step(expected_status)
    expected_posterior = _posterior_probability(source)

    if payload["update_status"] != expected_status:
        raise ValueError("update_status must match Bayesian update fields")
    if not _payload_reason_codes_are_valid(payload_reason_codes, expected_reason_codes):
        raise ValueError("reason_codes must match Bayesian update fields")
    if payload["manual_next_step"] != expected_next_step:
        raise ValueError("manual_next_step must match update_status")
    posterior_value = payload["posterior_probability"]
    if type(posterior_value) is not str:
        raise ValueError("posterior_probability must be serialized as a string")
    if _normalize_probability(
        "posterior_probability",
        Decimal(posterior_value),
    ) != expected_posterior:
        raise ValueError("posterior_probability must match Bayesian update fields")
    return payload


def _input_from_payload(
    payload: Mapping[str, object],
) -> ProbabilityEventBayesianPriorUpdateReadinessInput:
    decimal_values: dict[str, Decimal] = {}
    for field_name in INPUT_DECIMAL_FIELDS:
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        decimal_values[field_name] = Decimal(value)
    return ProbabilityEventBayesianPriorUpdateReadinessInput(
        prior_probability=decimal_values["prior_probability"],
        new_evidence_probability=decimal_values["new_evidence_probability"],
        evidence_reliability_probability=decimal_values[
            "evidence_reliability_probability"
        ],
        base_rate_sample_count=decimal_values["base_rate_sample_count"],
        calibration_error_probability=decimal_values[
            "calibration_error_probability"
        ],
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )


def _find_reason_codes(
    readiness: ProbabilityEventBayesianPriorUpdateReadinessInput,
) -> tuple[str, ...]:
    found: list[str] = []
    if readiness.prior_probability in (ZERO, ONE):
        found.append("bayesian_prior_update_prior_at_closed_boundary")
    if readiness.new_evidence_probability in (ZERO, ONE):
        found.append("bayesian_prior_update_evidence_at_closed_boundary")
    if readiness.paper_only is not True:
        found.append("bayesian_prior_update_paper_only_flag_not_set")
    if readiness.report_only is not True:
        found.append("bayesian_prior_update_report_only_flag_not_set")
    if readiness.readonly is not True:
        found.append("bayesian_prior_update_readonly_flag_not_set")
    if readiness.evidence_reliability_probability < MIN_RELIABILITY:
        found.append("bayesian_prior_update_low_evidence_reliability")
    if readiness.base_rate_sample_count < MIN_BASE_RATE_SAMPLE_COUNT:
        found.append("bayesian_prior_update_sparse_base_rate_sample")
    if readiness.calibration_error_probability > MAX_CALIBRATION_ERROR:
        found.append("bayesian_prior_update_high_calibration_error")
    if not found:
        return (READY_REASON_CODE,)
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in found)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in MANUAL_REVIEW_REASON_CODES for reason_code in reason_codes):
        return "manual_review"
    return "ready"


def _manual_next_step(update_status: str) -> str:
    if update_status == "ready":
        return READY_MANUAL_NEXT_STEP
    if update_status == "manual_review":
        return REVIEW_MANUAL_NEXT_STEP
    return BLOCKED_MANUAL_NEXT_STEP


def _posterior_probability(
    readiness: ProbabilityEventBayesianPriorUpdateReadinessInput,
) -> Decimal:
    if (
        readiness.prior_probability in (ZERO, ONE)
        or readiness.new_evidence_probability in (ZERO, ONE)
    ):
        return readiness.prior_probability
    evidence_delta = readiness.new_evidence_probability - readiness.prior_probability
    return _normalize_probability(
        "posterior_probability",
        readiness.prior_probability + (evidence_delta * _evidence_weight(readiness)),
    )


def _evidence_weight(
    readiness: ProbabilityEventBayesianPriorUpdateReadinessInput,
) -> Decimal:
    if _status_for_reason_codes(_find_reason_codes(readiness)) == "ready":
        return _normalize_probability(
            "evidence_weight",
            readiness.evidence_reliability_probability
            * readiness.evidence_reliability_probability,
        )
    return _normalize_probability(
        "evidence_weight",
        readiness.evidence_reliability_probability
        - readiness.calibration_error_probability
        + (readiness.base_rate_sample_count / MANUAL_SAMPLE_SCALE),
    )


def _validate_report(
    report: ProbabilityEventBayesianPriorUpdateReadinessReport,
) -> None:
    source = ProbabilityEventBayesianPriorUpdateReadinessInput(
        prior_probability=report.prior_probability,
        new_evidence_probability=report.new_evidence_probability,
        evidence_reliability_probability=report.evidence_reliability_probability,
        base_rate_sample_count=report.base_rate_sample_count,
        calibration_error_probability=report.calibration_error_probability,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_reason_codes = _find_reason_codes(source)
    expected_status = _status_for_reason_codes(expected_reason_codes)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match Bayesian update fields")
    if report.update_status != expected_status:
        raise ValueError("update_status must match reason_codes")
    if report.posterior_probability != _posterior_probability(source):
        raise ValueError("posterior_probability must match Bayesian update fields")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match update_status")


def _normalize_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in BAYESIAN_PRIOR_UPDATE_STATUSES:
        raise ValueError(f"{field_name} must be a supported update status")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_SEQUENCE:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    canonical = tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in seen)
    if value != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return canonical


def _payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_codes("reason_codes", tuple(value))
    if type(value) is tuple:
        return _normalize_reason_codes("reason_codes", value)
    raise ValueError("reason_codes must be a list")


def _payload_reason_codes_are_valid(
    payload_reason_codes: tuple[str, ...],
    expected_reason_codes: tuple[str, ...],
) -> bool:
    if payload_reason_codes == expected_reason_codes:
        return True
    if not any(
        reason_code in BLOCKING_REASON_CODES for reason_code in payload_reason_codes
    ):
        return False
    non_flag_reasons = tuple(
        reason_code
        for reason_code in payload_reason_codes
        if reason_code
        not in (
            "bayesian_prior_update_paper_only_flag_not_set",
            "bayesian_prior_update_report_only_flag_not_set",
            "bayesian_prior_update_readonly_flag_not_set",
        )
    )
    expected_non_ready_reasons = tuple(
        reason_code
        for reason_code in expected_reason_codes
        if reason_code != READY_REASON_CODE
    )
    return non_flag_reasons == expected_non_ready_reasons


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _reject_unsafe_public_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_unsafe_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe private value")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_sample_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _digest_payload(payload: dict[str, object]) -> str:
    canonical_payload = {field_name: payload[field_name] for field_name in sorted(payload)}
    return sha256(
        json.dumps(canonical_payload, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
