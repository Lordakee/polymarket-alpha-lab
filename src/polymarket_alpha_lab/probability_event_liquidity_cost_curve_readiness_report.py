"""Read-only Phase 1 liquidity cost curve readiness report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


PROBABILITY_EVENT_LIQUIDITY_COST_CURVE_READINESS_REPORT_VERSION = (
    "probability-event-liquidity-cost-curve-readiness-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEPTH_DECAY_WATCH_THRESHOLD = Decimal("0.250000")
DEPTH_DECAY_BLOCK_THRESHOLD = Decimal("0.400000")

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

PROBABILITY_FIELDS = (
    "small_size_cost_probability",
    "medium_size_cost_probability",
    "large_size_cost_probability",
    "depth_decay_probability",
    "max_acceptable_cost_probability",
)
PAYLOAD_KEYS = (
    "config_version",
    "small_size_cost_probability",
    "medium_size_cost_probability",
    "large_size_cost_probability",
    "depth_decay_probability",
    "max_acceptable_cost_probability",
    "curve_status",
    "recommended_manual_size_band",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUS_VALUES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

LARGE_BAND = "large"
MEDIUM_BAND = "medium"
SMALL_BAND = "small"
NONE_BAND = "none"
SIZE_BANDS = (LARGE_BAND, MEDIUM_BAND, SMALL_BAND, NONE_BAND)

PASS_REASON = "liquidity_cost_curve_pass"
WATCH_REASON = "liquidity_cost_curve_watch"
BLOCKED_REASON = "liquidity_cost_curve_blocked"
SMALL_COST_REASON = "small_size_cost_above_limit"
MEDIUM_COST_REASON = "medium_size_cost_above_limit"
LARGE_COST_REASON = "large_size_cost_above_limit"
DEPTH_DECAY_WATCH_REASON = "depth_decay_probability_watch"
DEPTH_DECAY_BLOCK_REASON = "depth_decay_probability_blocked"
REASON_VALUES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
    SMALL_COST_REASON,
    MEDIUM_COST_REASON,
    LARGE_COST_REASON,
    DEPTH_DECAY_WATCH_REASON,
    DEPTH_DECAY_BLOCK_REASON,
)

NEXT_STEP_BY_STATUS_AND_BAND = {
    (PASS_STATUS, LARGE_BAND): "document_large_band_for_manual_phase1_review",
    (WATCH_STATUS, MEDIUM_BAND): "manually_review_medium_band_cost_curve",
    (WATCH_STATUS, SMALL_BAND): "manually_review_small_band_cost_curve",
    (BLOCKED_STATUS, NONE_BAND): (
        "do_not_use_curve_until_manual_liquidity_cost_review"
    ),
}
PUBLIC_STRING_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")

__all__ = (
    "PROBABILITY_EVENT_LIQUIDITY_COST_CURVE_READINESS_REPORT_VERSION",
    "ProbabilityEventLiquidityCostCurveReadinessInput",
    "ProbabilityEventLiquidityCostCurveReadinessPublicPayload",
    "ProbabilityEventLiquidityCostCurveReadinessReport",
    "build_probability_event_liquidity_cost_curve_readiness_report",
    "probability_event_liquidity_cost_curve_readiness_report_digest",
    "probability_event_liquidity_cost_curve_readiness_report_payload",
)


class ProbabilityEventLiquidityCostCurveReadinessPublicPayload(dict[str, object]):
    """Immutable public payload for this read-only readiness report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ProbabilityEventLiquidityCostCurveReadinessInput:
    small_size_cost_probability: Decimal
    medium_size_cost_probability: Decimal
    large_size_cost_probability: Decimal
    depth_decay_probability: Decimal
    max_acceptable_cost_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventLiquidityCostCurveReadinessInput:
            raise TypeError(
                "ProbabilityEventLiquidityCostCurveReadinessInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventLiquidityCostCurveReadinessInput:
            raise ValueError(
                "input must be exactly ProbabilityEventLiquidityCostCurveReadinessInput",
            )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventLiquidityCostCurveReadinessReport:
    config_version: str
    small_size_cost_probability: Decimal
    medium_size_cost_probability: Decimal
    large_size_cost_probability: Decimal
    depth_decay_probability: Decimal
    max_acceptable_cost_probability: Decimal
    curve_status: str
    recommended_manual_size_band: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventLiquidityCostCurveReadinessReport:
            raise TypeError(
                "ProbabilityEventLiquidityCostCurveReadinessReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventLiquidityCostCurveReadinessReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventLiquidityCostCurveReadinessReport",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != PROBABILITY_EVENT_LIQUIDITY_COST_CURVE_READINESS_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported report version")
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status(self.curve_status)
        _require_size_band(self.recommended_manual_size_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(
        self,
    ) -> ProbabilityEventLiquidityCostCurveReadinessPublicPayload:
        payload = ProbabilityEventLiquidityCostCurveReadinessPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_liquidity_cost_curve_readiness_report(
    inputs: ProbabilityEventLiquidityCostCurveReadinessInput,
) -> ProbabilityEventLiquidityCostCurveReadinessReport:
    """Build a deterministic report-only Phase 1 liquidity cost curve review."""

    if type(inputs) is not ProbabilityEventLiquidityCostCurveReadinessInput:
        raise ValueError(
            "inputs must be a ProbabilityEventLiquidityCostCurveReadinessInput",
        )
    _require_hard_flags("input", inputs)
    values: dict[str, object] = {
        "config_version": (
            PROBABILITY_EVENT_LIQUIDITY_COST_CURVE_READINESS_REPORT_VERSION
        ),
        "small_size_cost_probability": inputs.small_size_cost_probability,
        "medium_size_cost_probability": inputs.medium_size_cost_probability,
        "large_size_cost_probability": inputs.large_size_cost_probability,
        "depth_decay_probability": inputs.depth_decay_probability,
        "max_acceptable_cost_probability": inputs.max_acceptable_cost_probability,
        "curve_status": _curve_status(inputs),
        "recommended_manual_size_band": _recommended_manual_size_band(inputs),
        "reason_codes": _reason_codes(inputs),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["manual_next_step"] = _manual_next_step(
        values["curve_status"],
        values["recommended_manual_size_band"],
    )
    return ProbabilityEventLiquidityCostCurveReadinessReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_liquidity_cost_curve_readiness_report_payload(
    report: ProbabilityEventLiquidityCostCurveReadinessReport | Mapping[str, object],
) -> ProbabilityEventLiquidityCostCurveReadinessPublicPayload:
    if type(report) is ProbabilityEventLiquidityCostCurveReadinessReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        expected_digest = _payload_digest(_payload_items(report, payload_digest=""))
        if report.payload_digest != expected_digest:
            raise ValueError("payload_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return ProbabilityEventLiquidityCostCurveReadinessPublicPayload(report)
    raise ValueError(
        "report must be a ProbabilityEventLiquidityCostCurveReadinessReport "
        "or public payload",
    )


def probability_event_liquidity_cost_curve_readiness_report_digest(
    report: ProbabilityEventLiquidityCostCurveReadinessReport,
) -> str:
    if type(report) is not ProbabilityEventLiquidityCostCurveReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventLiquidityCostCurveReadinessReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    return (
        "ProbabilityEventLiquidityCostCurveReadinessReport("
        f"curve_status={report.curve_status}, "
        f"recommended_manual_size_band={report.recommended_manual_size_band}, "
        f"reasons={','.join(report.reason_codes)}, "
        f"payload_digest={report.payload_digest})"
    )


def _curve_status(inputs: ProbabilityEventLiquidityCostCurveReadinessInput) -> str:
    if (
        inputs.small_size_cost_probability
        > inputs.max_acceptable_cost_probability
        or inputs.depth_decay_probability >= DEPTH_DECAY_BLOCK_THRESHOLD
    ):
        return BLOCKED_STATUS
    if (
        inputs.medium_size_cost_probability
        > inputs.max_acceptable_cost_probability
        or inputs.large_size_cost_probability
        > inputs.max_acceptable_cost_probability
        or inputs.depth_decay_probability >= DEPTH_DECAY_WATCH_THRESHOLD
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _recommended_manual_size_band(
    inputs: ProbabilityEventLiquidityCostCurveReadinessInput,
) -> str:
    if _curve_status(inputs) == BLOCKED_STATUS:
        return NONE_BAND
    if (
        inputs.large_size_cost_probability
        <= inputs.max_acceptable_cost_probability
        and inputs.depth_decay_probability < DEPTH_DECAY_WATCH_THRESHOLD
    ):
        return LARGE_BAND
    if inputs.medium_size_cost_probability <= inputs.max_acceptable_cost_probability:
        return MEDIUM_BAND
    return SMALL_BAND


def _reason_codes(
    inputs: ProbabilityEventLiquidityCostCurveReadinessInput,
) -> tuple[str, ...]:
    status = _curve_status(inputs)
    reasons: list[str] = [
        {
            PASS_STATUS: PASS_REASON,
            WATCH_STATUS: WATCH_REASON,
            BLOCKED_STATUS: BLOCKED_REASON,
        }[status],
    ]
    if inputs.small_size_cost_probability > inputs.max_acceptable_cost_probability:
        reasons.append(SMALL_COST_REASON)
    if inputs.medium_size_cost_probability > inputs.max_acceptable_cost_probability:
        reasons.append(MEDIUM_COST_REASON)
    if inputs.large_size_cost_probability > inputs.max_acceptable_cost_probability:
        reasons.append(LARGE_COST_REASON)
    if inputs.depth_decay_probability >= DEPTH_DECAY_BLOCK_THRESHOLD:
        reasons.append(DEPTH_DECAY_BLOCK_REASON)
    elif inputs.depth_decay_probability >= DEPTH_DECAY_WATCH_THRESHOLD:
        reasons.append(DEPTH_DECAY_WATCH_REASON)
    return tuple(reasons)


def _manual_next_step(status: object, recommended_band: object) -> str:
    if type(status) is not str or type(recommended_band) is not str:
        raise ValueError("manual_next_step inputs must be public strings")
    try:
        return NEXT_STEP_BY_STATUS_AND_BAND[(status, recommended_band)]
    except KeyError as exc:
        raise ValueError("manual_next_step must match curve_status") from exc


def _validate_report(report: ProbabilityEventLiquidityCostCurveReadinessReport) -> None:
    inputs = ProbabilityEventLiquidityCostCurveReadinessInput(
        small_size_cost_probability=report.small_size_cost_probability,
        medium_size_cost_probability=report.medium_size_cost_probability,
        large_size_cost_probability=report.large_size_cost_probability,
        depth_decay_probability=report.depth_decay_probability,
        max_acceptable_cost_probability=report.max_acceptable_cost_probability,
    )
    if report.curve_status != _curve_status(inputs):
        raise ValueError("curve_status must match inputs")
    if report.recommended_manual_size_band != _recommended_manual_size_band(inputs):
        raise ValueError("recommended_manual_size_band must match inputs")
    if report.reason_codes != _reason_codes(inputs):
        raise ValueError("reason_codes must match inputs")
    if report.manual_next_step != _manual_next_step(
        report.curve_status,
        report.recommended_manual_size_band,
    ):
        raise ValueError("manual_next_step must match curve_status")


def _payload_items(
    report: ProbabilityEventLiquidityCostCurveReadinessReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "small_size_cost_probability": _decimal_string(
            report.small_size_cost_probability,
        ),
        "medium_size_cost_probability": _decimal_string(
            report.medium_size_cost_probability,
        ),
        "large_size_cost_probability": _decimal_string(
            report.large_size_cost_probability,
        ),
        "depth_decay_probability": _decimal_string(report.depth_decay_probability),
        "max_acceptable_cost_probability": _decimal_string(
            report.max_acceptable_cost_probability,
        ),
        "curve_status": report.curve_status,
        "recommended_manual_size_band": report.recommended_manual_size_band,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": payload_digest,
    }


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "small_size_cost_probability": _decimal_string(
            values["small_size_cost_probability"],
        ),
        "medium_size_cost_probability": _decimal_string(
            values["medium_size_cost_probability"],
        ),
        "large_size_cost_probability": _decimal_string(
            values["large_size_cost_probability"],
        ),
        "depth_decay_probability": _decimal_string(values["depth_decay_probability"]),
        "max_acceptable_cost_probability": _decimal_string(
            values["max_acceptable_cost_probability"],
        ),
        "curve_status": values["curve_status"],
        "recommended_manual_size_band": values["recommended_manual_size_band"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("public payload keys must match report contract")
    for field_name in PROBABILITY_FIELDS:
        _parse_decimal_string(field_name, payload[field_name])
    _require_public_label("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != PROBABILITY_EVENT_LIQUIDITY_COST_CURVE_READINESS_REPORT_VERSION
    ):
        raise ValueError("config_version must be the supported report version")
    _require_status(payload["curve_status"])
    _require_size_band(payload["recommended_manual_size_band"])
    _normalize_reason_codes(_tuple_from_payload("reason_codes", payload["reason_codes"]))
    _require_manual_next_step(payload["manual_next_step"])
    _validate_public_payload_derived(payload)
    _require_hard_flags("public payload", payload)
    _require_digest("payload_digest", payload["payload_digest"])
    payload_without_digest = dict(payload)
    payload_without_digest["payload_digest"] = ""
    if payload["payload_digest"] != _payload_digest(payload_without_digest):
        raise ValueError("payload_digest must match public payload")


def _require_probability_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    quantized = decimal_value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if decimal_value != quantized:
        raise ValueError(f"{name} precision is too granular")
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return quantized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_string(value: object) -> str:
    return str(_require_decimal("payload decimal", value).quantize(QUANTUM))


def _parse_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if str(parsed.quantize(QUANTUM)) != value:
        raise ValueError(f"{name} must use six decimal places")
    if parsed < ZERO or parsed > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return parsed


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase sha256 hex")
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError("curve_status must be pass, watch, or blocked")
    return value


def _require_size_band(value: object) -> str:
    if type(value) is not str or value not in SIZE_BANDS:
        raise ValueError("recommended_manual_size_band must be supported")
    return value


def _require_manual_next_step(value: object) -> str:
    if type(value) is not str or not PUBLIC_STRING_RE.fullmatch(value):
        raise ValueError("manual_next_step must be a public string")
    return value


def _validate_public_payload_derived(payload: Mapping[str, object]) -> None:
    inputs = ProbabilityEventLiquidityCostCurveReadinessInput(
        small_size_cost_probability=_parse_decimal_string(
            "small_size_cost_probability",
            payload["small_size_cost_probability"],
        ),
        medium_size_cost_probability=_parse_decimal_string(
            "medium_size_cost_probability",
            payload["medium_size_cost_probability"],
        ),
        large_size_cost_probability=_parse_decimal_string(
            "large_size_cost_probability",
            payload["large_size_cost_probability"],
        ),
        depth_decay_probability=_parse_decimal_string(
            "depth_decay_probability",
            payload["depth_decay_probability"],
        ),
        max_acceptable_cost_probability=_parse_decimal_string(
            "max_acceptable_cost_probability",
            payload["max_acceptable_cost_probability"],
        ),
    )
    if payload["curve_status"] != _curve_status(inputs):
        raise ValueError("curve_status must match public payload inputs")
    if payload["recommended_manual_size_band"] != _recommended_manual_size_band(inputs):
        raise ValueError(
            "recommended_manual_size_band must match public payload inputs",
        )
    if _tuple_from_payload("reason_codes", payload["reason_codes"]) != _reason_codes(
        inputs,
    ):
        raise ValueError("reason_codes must match public payload inputs")
    if payload["manual_next_step"] != _manual_next_step(
        payload["curve_status"],
        payload["recommended_manual_size_band"],
    ):
        raise ValueError("manual_next_step must match public payload status")


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_VALUES:
            raise ValueError("reason_codes contains unsupported reason code")
    return reason_codes


def _tuple_from_payload(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list in public payload")
    if not all(type(item) is str for item in value):
        raise ValueError(f"{name} must contain strings")
    return tuple(value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
