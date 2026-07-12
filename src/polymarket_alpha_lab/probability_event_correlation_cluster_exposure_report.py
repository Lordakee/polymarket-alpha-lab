from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Any


DEFAULT_CONFIG_VERSION = "probability-event-correlation-cluster-exposure-report-v0"

CLEAR_STATUS = "clear"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
EXPOSURE_STATUSES = (CLEAR_STATUS, WATCH_STATUS, BLOCK_STATUS)

SAME_FAMILY_REASON = "correlation_cluster_same_outcome_family_watch"
OPEN_REASON = "correlation_cluster_open_candidate_watch"
LIMIT_REASON = "correlation_cluster_risk_adjusted_edge_block"
CLEAR_REASON = "correlation_cluster_exposure_clear"
REASON_CODES = (SAME_FAMILY_REASON, OPEN_REASON, LIMIT_REASON, CLEAR_REASON)

MANUAL_BLOCK_STEP = "manual_block_cluster_exposure_limit"
MANUAL_WATCH_STEP = "manual_review_cluster_correlation"
MANUAL_CLEAR_STEP = "no_manual_action_required"
MANUAL_STEPS = (MANUAL_BLOCK_STEP, MANUAL_WATCH_STEP, MANUAL_CLEAR_STEP)

COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
SHA256_CHARS = frozenset("0123456789abcdef")

DECIMAL_PUBLIC_NAMES = frozenset(
    (
        "open_candidate_count",
        "same_outcome_family_count",
        "aggregate_edge_probability",
        "correlation_risk_probability",
        "manual_exposure_limit_probability",
        "adjusted_edge_probability",
    ),
)
PUBLIC_NAMES = frozenset(
    (
        "config_version",
        "cluster_id",
        "open_candidate_count",
        "same_outcome_family_count",
        "aggregate_edge_probability",
        "correlation_risk_probability",
        "manual_exposure_limit_probability",
        "exposure_status",
        "adjusted_edge_probability",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
CANON_NAMES = (
    "adjusted_edge_probability",
    "aggregate_edge_probability",
    "cluster_id",
    "config_version",
    "correlation_risk_probability",
    "exposure_status",
    "manual_exposure_limit_probability",
    "manual_next_step",
    "open_candidate_count",
    "paper_only",
    "readonly",
    "reason_codes",
    "report_only",
    "same_outcome_family_count",
)


def _make(*parts: str) -> str:
    return "".join(parts)


UNSAFE_FRAGMENTS = frozenset(
    (
        _make("l", "ive"),
        _make("au", "th"),
        _make("wal", "let"),
        _make("or", "der"),
        _make("k", "ey"),
        _make("sig", "na", "ture"),
        _make("exe", "cute"),
        _make("tra", "de"),
        _make("pri", "vate"),
        _make("per", "sist"),
        _make("js", "onl"),
    ),
)
UNSAFE_NAMES = frozenset(
    (
        "candidate_id",
        "market_id",
        _make("private_", "k", "ey"),
        _make("au", "th_", "to", "ken"),
        _make("wal", "let_", "address"),
        _make("or", "der_", "id"),
        _make("sig", "na", "ture"),
        _make("exe", "cute_", "route"),
        _make("exe", "cute_", "p", "ath"),
        _make("per", "sist_", "js", "onl"),
    ),
)

__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "EXPOSURE_STATUSES",
    "ProbabilityEventCorrelationClusterExposureInput",
    "ProbabilityEventCorrelationClusterExposureReport",
    "build_probability_event_correlation_cluster_exposure_report",
    "probability_event_correlation_cluster_exposure_report_digest",
    "probability_event_correlation_cluster_exposure_report_payload",
    "validate_probability_event_correlation_cluster_exposure_public_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ProbabilityEventCorrelationClusterExposureInput(_FinalDataclass):
    cluster_id: str
    open_candidate_count: Decimal
    same_outcome_family_count: Decimal
    aggregate_edge_probability: Decimal
    correlation_risk_probability: Decimal
    manual_exposure_limit_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventCorrelationClusterExposureInput,
            "input",
        )
        _require_public_label("cluster_id", self.cluster_id)
        _reject_unsafe_public_payload_text(self.cluster_id)
        for name in ("open_candidate_count", "same_outcome_family_count"):
            object.__setattr__(
                self,
                name,
                _require_count_decimal(name, getattr(self, name)),
            )
        for name in (
            "aggregate_edge_probability",
            "correlation_risk_probability",
            "manual_exposure_limit_probability",
        ):
            object.__setattr__(
                self,
                name,
                _require_probability_decimal(name, getattr(self, name)),
            )
        if self.same_outcome_family_count > self.open_candidate_count:
            raise ValueError(
                "same_outcome_family_count must not exceed open_candidate_count",
            )
        if self.manual_exposure_limit_probability <= ZERO_RATIO:
            raise ValueError("manual_exposure_limit_probability must be positive")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ProbabilityEventCorrelationClusterExposureReport(_FinalDataclass):
    config_version: str
    cluster_id: str
    open_candidate_count: Decimal
    same_outcome_family_count: Decimal
    aggregate_edge_probability: Decimal
    correlation_risk_probability: Decimal
    manual_exposure_limit_probability: Decimal
    exposure_status: str
    adjusted_edge_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventCorrelationClusterExposureReport,
            "report",
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_public_label("cluster_id", self.cluster_id)
        _reject_unsafe_public_payload_text(self.cluster_id)
        for name in ("open_candidate_count", "same_outcome_family_count"):
            object.__setattr__(
                self,
                name,
                _require_count_decimal(name, getattr(self, name)),
            )
        for name in (
            "aggregate_edge_probability",
            "correlation_risk_probability",
            "manual_exposure_limit_probability",
            "adjusted_edge_probability",
        ):
            object.__setattr__(
                self,
                name,
                _require_probability_decimal(name, getattr(self, name)),
            )
        if self.same_outcome_family_count > self.open_candidate_count:
            raise ValueError(
                "same_outcome_family_count must not exceed open_candidate_count",
            )
        if self.manual_exposure_limit_probability <= ZERO_RATIO:
            raise ValueError("manual_exposure_limit_probability must be positive")
        _require_status("exposure_status", self.exposure_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        _require_manual_step("manual_next_step", self.manual_next_step)
        _require_sha256("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload(self)
        if self.payload_digest != _digest_from_report(self):
            raise ValueError("payload_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        _validate_report(self)
        _reject_unsafe_public_payload(self)
        payload = _public_payload_from_report(self)
        validate_probability_event_correlation_cluster_exposure_public_payload(payload)
        return payload


def build_probability_event_correlation_cluster_exposure_report(
    item: ProbabilityEventCorrelationClusterExposureInput,
) -> ProbabilityEventCorrelationClusterExposureReport:
    _require_exact_type(item, ProbabilityEventCorrelationClusterExposureInput, "input")
    _require_hard_flags("input", item)
    adjusted = _adjusted_edge_probability(
        item.aggregate_edge_probability,
        item.correlation_risk_probability,
    )
    status = _exposure_status(
        open_candidate_count=item.open_candidate_count,
        same_outcome_family_count=item.same_outcome_family_count,
        aggregate_edge_probability=item.aggregate_edge_probability,
        manual_exposure_limit_probability=item.manual_exposure_limit_probability,
    )
    values: dict[str, object] = {
        "config_version": DEFAULT_CONFIG_VERSION,
        "cluster_id": item.cluster_id,
        "open_candidate_count": item.open_candidate_count,
        "same_outcome_family_count": item.same_outcome_family_count,
        "aggregate_edge_probability": item.aggregate_edge_probability,
        "correlation_risk_probability": item.correlation_risk_probability,
        "manual_exposure_limit_probability": item.manual_exposure_limit_probability,
        "exposure_status": status,
        "adjusted_edge_probability": adjusted,
        "reason_codes": _reason_codes(
            exposure_status=status,
            open_candidate_count=item.open_candidate_count,
            same_outcome_family_count=item.same_outcome_family_count,
        ),
        "manual_next_step": _manual_next_step(status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventCorrelationClusterExposureReport(
        **values,
        payload_digest=_digest_from_values(values),
    )


def probability_event_correlation_cluster_exposure_report_payload(
    item: ProbabilityEventCorrelationClusterExposureReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(item) is ProbabilityEventCorrelationClusterExposureReport:
        return item.public_payload
    if isinstance(item, Mapping):
        payload = dict(item.items())
        validate_probability_event_correlation_cluster_exposure_public_payload(payload)
        return payload
    raise ValueError("report must be a correlation cluster exposure report")


def probability_event_correlation_cluster_exposure_report_digest(
    item: ProbabilityEventCorrelationClusterExposureReport | Mapping[str, object],
) -> str:
    if type(item) is ProbabilityEventCorrelationClusterExposureReport:
        return item.payload_digest
    if isinstance(item, Mapping):
        payload = dict(item.items())
        validate_probability_event_correlation_cluster_exposure_public_payload(payload)
        digest = payload.get("payload_digest")
        if type(digest) is not str:
            raise ValueError("payload_digest must be a string")
        return digest
    raise ValueError("report must be a correlation cluster exposure report")


def validate_probability_event_correlation_cluster_exposure_public_payload(
    payload: Mapping[str, object],
) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    _reject_unsafe_public_payload(payload)
    names = frozenset(str(name) for name in payload)
    if names != PUBLIC_NAMES:
        raise ValueError("public payload fields must match report fields")
    for name in DECIMAL_PUBLIC_NAMES:
        value = payload[name]
        if type(value) is not str or not PUBLIC_DECIMAL_RE.fullmatch(value):
            raise ValueError(f"{name} must be Decimal-derived public text")
    _require_public_string("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _require_public_label("cluster_id", payload["cluster_id"])
    _reject_unsafe_public_payload_text(payload["cluster_id"])
    _require_status("exposure_status", payload["exposure_status"])
    _require_public_reason_codes(payload["reason_codes"])
    _require_manual_step("manual_next_step", payload["manual_next_step"])
    for name in ("paper_only", "report_only", "readonly"):
        if payload[name] is not True:
            raise ValueError(f"{name} must be True")
    digest = payload["payload_digest"]
    _require_sha256("payload_digest", digest)
    if digest != _digest_from_public_payload(payload):
        raise ValueError("payload_digest does not match public payload")


def _require_exact_type(item: object, expected_type: type[object], name: str) -> None:
    if type(item) is not expected_type:
        raise ValueError(f"{name} must be {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str or value == "":
        raise ValueError(f"{name} must be a non-empty public string")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public aggregate label")
    return value


def _require_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if value < ZERO_COUNT or value != value.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_probability_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in EXPOSURE_STATUSES:
        raise ValueError(f"{name} must be a supported exposure status")
    return value


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or len(value) == 0:
        raise ValueError("reason_codes must be a non-empty tuple")
    for code in value:
        if type(code) is not str or code not in REASON_CODES:
            raise ValueError("reason_codes must be supported reason codes")
    if len(frozenset(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return value


def _require_public_reason_codes(value: object) -> None:
    if type(value) not in (list, tuple) or len(value) == 0:
        raise ValueError("reason_codes must be public reason code text")
    for code in value:
        if type(code) is not str or code not in REASON_CODES:
            raise ValueError("reason_codes must be supported reason codes")
    if len(frozenset(value)) != len(value):
        raise ValueError("reason_codes must be unique")


def _require_manual_step(name: str, value: object) -> str:
    if type(value) is not str or value not in MANUAL_STEPS:
        raise ValueError(f"{name} must be a supported manual next step")
    return value


def _require_sha256(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in SHA256_CHARS for char in value)
    ):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_hard_flags(label: str, item: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(item, name, None) is not True:
            raise ValueError(f"{label} {name} must be True")


def _reject_unsafe_public_payload_text(value: object) -> None:
    if type(value) is not str:
        return
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_FRAGMENTS):
        raise ValueError("unsafe public payload value")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for name, nested in value.items():
            lowered = str(name).lower()
            if lowered in UNSAFE_NAMES:
                raise ValueError("unsafe public payload")
            if any(fragment in lowered for fragment in UNSAFE_FRAGMENTS):
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(nested)
        return
    if dataclass_is_public(value):
        for name in value.__dataclass_fields__:
            lowered = str(name).lower()
            if lowered in UNSAFE_NAMES:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(getattr(value, name))
        return
    if type(value) in (tuple, list):
        for nested in value:
            _reject_unsafe_public_payload(nested)
        return
    _reject_unsafe_public_payload_text(value)


def dataclass_is_public(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__")


def _adjusted_edge_probability(
    aggregate_edge_probability: Decimal,
    correlation_risk_probability: Decimal,
) -> Decimal:
    adjusted = aggregate_edge_probability - correlation_risk_probability
    if adjusted < ZERO_RATIO:
        return ZERO_RATIO
    return adjusted.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _exposure_status(
    *,
    open_candidate_count: Decimal,
    same_outcome_family_count: Decimal,
    aggregate_edge_probability: Decimal,
    manual_exposure_limit_probability: Decimal,
) -> str:
    if aggregate_edge_probability > manual_exposure_limit_probability:
        return BLOCK_STATUS
    if open_candidate_count > Decimal("1") or same_outcome_family_count > ZERO_COUNT:
        return WATCH_STATUS
    return CLEAR_STATUS


def _reason_codes(
    *,
    exposure_status: str,
    open_candidate_count: Decimal,
    same_outcome_family_count: Decimal,
) -> tuple[str, ...]:
    if exposure_status == BLOCK_STATUS:
        reasons: list[str] = []
        if same_outcome_family_count > ZERO_COUNT:
            reasons.append(SAME_FAMILY_REASON)
        reasons.append(LIMIT_REASON)
        return tuple(reasons)
    if exposure_status == WATCH_STATUS:
        reasons = []
        if open_candidate_count > Decimal("1"):
            reasons.append(OPEN_REASON)
        if same_outcome_family_count > ZERO_COUNT:
            reasons.append(SAME_FAMILY_REASON)
        return tuple(reasons)
    return (CLEAR_REASON,)


def _manual_next_step(status: str) -> str:
    if status == BLOCK_STATUS:
        return MANUAL_BLOCK_STEP
    if status == WATCH_STATUS:
        return MANUAL_WATCH_STEP
    return MANUAL_CLEAR_STEP


def _validate_report(report: ProbabilityEventCorrelationClusterExposureReport) -> None:
    expected_adjusted = _adjusted_edge_probability(
        report.aggregate_edge_probability,
        report.correlation_risk_probability,
    )
    if report.adjusted_edge_probability != expected_adjusted:
        raise ValueError("adjusted_edge_probability must match inputs")
    expected_status = _exposure_status(
        open_candidate_count=report.open_candidate_count,
        same_outcome_family_count=report.same_outcome_family_count,
        aggregate_edge_probability=report.aggregate_edge_probability,
        manual_exposure_limit_probability=report.manual_exposure_limit_probability,
    )
    if report.exposure_status != expected_status:
        raise ValueError("exposure_status must match inputs")
    expected_reasons = _reason_codes(
        exposure_status=expected_status,
        open_candidate_count=report.open_candidate_count,
        same_outcome_family_count=report.same_outcome_family_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match exposure_status")


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _public_payload_from_report(
    report: ProbabilityEventCorrelationClusterExposureReport,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "cluster_id": report.cluster_id,
        "open_candidate_count": _decimal_text(report.open_candidate_count),
        "same_outcome_family_count": _decimal_text(report.same_outcome_family_count),
        "aggregate_edge_probability": _decimal_text(report.aggregate_edge_probability),
        "correlation_risk_probability": _decimal_text(
            report.correlation_risk_probability,
        ),
        "manual_exposure_limit_probability": _decimal_text(
            report.manual_exposure_limit_probability,
        ),
        "exposure_status": report.exposure_status,
        "adjusted_edge_probability": _decimal_text(report.adjusted_edge_probability),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "payload_digest": report.payload_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _public_values_from_report(
    report: ProbabilityEventCorrelationClusterExposureReport,
) -> dict[str, object]:
    payload = _public_payload_from_report(report)
    return {name: payload[name] for name in CANON_NAMES}


def _public_values_from_mapping(payload: Mapping[str, object]) -> dict[str, object]:
    return {name: payload[name] for name in CANON_NAMES}


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = {
        "config_version": values["config_version"],
        "cluster_id": values["cluster_id"],
        "open_candidate_count": _decimal_text(values["open_candidate_count"]),
        "same_outcome_family_count": _decimal_text(values["same_outcome_family_count"]),
        "aggregate_edge_probability": _decimal_text(
            values["aggregate_edge_probability"],
        ),
        "correlation_risk_probability": _decimal_text(
            values["correlation_risk_probability"],
        ),
        "manual_exposure_limit_probability": _decimal_text(
            values["manual_exposure_limit_probability"],
        ),
        "exposure_status": values["exposure_status"],
        "adjusted_edge_probability": _decimal_text(values["adjusted_edge_probability"]),
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return _digest_from_public_values({name: payload[name] for name in CANON_NAMES})


def _digest_from_report(report: ProbabilityEventCorrelationClusterExposureReport) -> str:
    return _digest_from_public_values(_public_values_from_report(report))


def _digest_from_public_payload(payload: Mapping[str, object]) -> str:
    return _digest_from_public_values(_public_values_from_mapping(payload))


def _digest_from_public_values(values: Mapping[str, object]) -> str:
    body = {name: values[name] for name in CANON_NAMES}
    data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
