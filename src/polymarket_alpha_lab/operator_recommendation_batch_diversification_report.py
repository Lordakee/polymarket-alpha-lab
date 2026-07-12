"""Read-only operator recommendation batch diversification report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping


OPERATOR_RECOMMENDATION_BATCH_DIVERSIFICATION_REPORT_VERSION = (
    "operator_recommendation_batch_diversification_report.v1"
)

READY_REASON = "operator_recommendation_batch_diversified"
EMPTY_REASON = "recommendation_batch_empty"
SINGLE_CATEGORY_REASON = "single_category_recommendation_batch"
MINIMUM_CATEGORY_REASON = "minimum_category_count_not_met"
DOMINANT_CATEGORY_WATCH_REASON = "dominant_category_concentration_watch"
DOMINANT_CATEGORY_BLOCKER_REASON = "dominant_category_concentration_blocker"
CORRELATED_CLUSTER_REASON = "correlated_cluster_concentration_watch"

STATUS_VALUES = frozenset(("diversified", "attention", "blocked"))
REASON_VALUES = frozenset(
    (
        READY_REASON,
        EMPTY_REASON,
        SINGLE_CATEGORY_REASON,
        MINIMUM_CATEGORY_REASON,
        DOMINANT_CATEGORY_WATCH_REASON,
        DOMINANT_CATEGORY_BLOCKER_REASON,
        CORRELATED_CLUSTER_REASON,
    ),
)
NEXT_STEP_VALUES = frozenset(
    (
        "manual_review_batch_diversification",
        "manual_add_recommendations_before_review",
        "manual_add_independent_category_review",
        "manual_split_batch_or_add_uncorrelated_categories",
    ),
)
PAYLOAD_KEYS = (
    "config_version",
    "diversification_status",
    "reason_codes",
    "manual_next_step",
    "recommendation_count",
    "category_count",
    "dominant_category_count",
    "correlated_cluster_count",
    "minimum_category_count",
    "category_ratio",
    "dominant_category_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
UNSAFE_PUBLIC_TOKENS = (
    "live",
    "auth",
    "wallet",
    "key",
    "signature",
    "signing",
    "signed",
    "execute",
    "execution",
    "order",
    "trade",
    "jsonl",
    "file",
    "persistence",
    "persist",
    "path",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SIX_PLACES = Decimal("0.000001")
SHA256_HEX_LENGTH = 64


class OperatorRecommendationBatchDiversificationPublicPayload(dict[str, object]):
    """Immutable public payload for the read-only diversification report."""

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
class OperatorRecommendationBatchDiversificationInput:
    recommendation_count: Decimal
    category_count: Decimal
    dominant_category_count: Decimal
    correlated_cluster_count: Decimal
    minimum_category_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorRecommendationBatchDiversificationInput:
            raise TypeError(
                "OperatorRecommendationBatchDiversificationInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorRecommendationBatchDiversificationInput:
            raise ValueError(
                "input must be exactly OperatorRecommendationBatchDiversificationInput",
            )
        for field_name in (
            "recommendation_count",
            "category_count",
            "dominant_category_count",
            "correlated_cluster_count",
            "minimum_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _validate_input_counts(self)


@dataclass(frozen=True)
class OperatorRecommendationBatchDiversificationReport:
    config_version: str
    diversification_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    recommendation_count: Decimal
    category_count: Decimal
    dominant_category_count: Decimal
    correlated_cluster_count: Decimal
    minimum_category_count: Decimal
    category_ratio: Decimal
    dominant_category_ratio: Decimal
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorRecommendationBatchDiversificationReport:
            raise TypeError(
                "OperatorRecommendationBatchDiversificationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorRecommendationBatchDiversificationReport:
            raise ValueError(
                "report must be exactly OperatorRecommendationBatchDiversificationReport",
            )
        if type(self.config_version) is not str or not self.config_version:
            raise ValueError("config_version must be a non-empty public string")
        if self.config_version != OPERATOR_RECOMMENDATION_BATCH_DIVERSIFICATION_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        if self.diversification_status not in STATUS_VALUES:
            raise ValueError("diversification_status must be a supported status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.manual_next_step not in NEXT_STEP_VALUES:
            raise ValueError("manual_next_step must be a supported manual action")
        for field_name in (
            "recommendation_count",
            "category_count",
            "dominant_category_count",
            "correlated_cluster_count",
            "minimum_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("category_ratio", "dominant_category_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        if self.payload_digest != _payload_digest(_payload_items(self, payload_digest="")):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> OperatorRecommendationBatchDiversificationPublicPayload:
        payload = OperatorRecommendationBatchDiversificationPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_operator_recommendation_batch_diversification_report(
    inputs: OperatorRecommendationBatchDiversificationInput,
) -> OperatorRecommendationBatchDiversificationReport:
    """Build a deterministic read-only diversification report for manual review."""

    if type(inputs) is not OperatorRecommendationBatchDiversificationInput:
        raise ValueError(
            "inputs must be an OperatorRecommendationBatchDiversificationInput",
        )
    _require_hard_flags(inputs)
    _validate_input_counts(inputs)
    category_ratio = _safe_ratio(inputs.category_count, inputs.recommendation_count)
    dominant_category_ratio = _safe_ratio(
        inputs.dominant_category_count,
        inputs.recommendation_count,
    )
    reason_codes = _reason_codes(
        recommendation_count=inputs.recommendation_count,
        category_count=inputs.category_count,
        dominant_category_ratio=dominant_category_ratio,
        correlated_cluster_count=inputs.correlated_cluster_count,
        minimum_category_count=inputs.minimum_category_count,
    )
    status = _status_from_reason_codes(reason_codes)
    values: dict[str, object] = {
        "config_version": OPERATOR_RECOMMENDATION_BATCH_DIVERSIFICATION_REPORT_VERSION,
        "diversification_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(status, reason_codes),
        "recommendation_count": inputs.recommendation_count,
        "category_count": inputs.category_count,
        "dominant_category_count": inputs.dominant_category_count,
        "correlated_cluster_count": inputs.correlated_cluster_count,
        "minimum_category_count": inputs.minimum_category_count,
        "category_ratio": category_ratio,
        "dominant_category_ratio": dominant_category_ratio,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return OperatorRecommendationBatchDiversificationReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def operator_recommendation_batch_diversification_report_payload(
    report: OperatorRecommendationBatchDiversificationReport | Mapping[str, object],
) -> OperatorRecommendationBatchDiversificationPublicPayload:
    if type(report) is OperatorRecommendationBatchDiversificationReport:
        _require_hard_flags(report)
        _validate_report(report)
        if report.payload_digest != _payload_digest(
            _payload_items(report, payload_digest=""),
        ):
            raise ValueError("payload_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return OperatorRecommendationBatchDiversificationPublicPayload(report)
    raise ValueError(
        "report must be an OperatorRecommendationBatchDiversificationReport or public payload",
    )


def operator_recommendation_batch_diversification_report_digest(
    report: OperatorRecommendationBatchDiversificationReport | Mapping[str, object],
) -> str:
    payload = operator_recommendation_batch_diversification_report_payload(report)
    return str(payload["payload_digest"])


def _validate_input_counts(
    inputs: OperatorRecommendationBatchDiversificationInput,
) -> None:
    if inputs.category_count > inputs.recommendation_count:
        raise ValueError("category_count must not exceed recommendation_count")
    if inputs.dominant_category_count > inputs.recommendation_count:
        raise ValueError(
            "dominant_category_count must not exceed recommendation_count",
        )
    if (
        inputs.recommendation_count > ZERO
        and inputs.category_count > ZERO
        and inputs.dominant_category_count < ONE
    ):
        raise ValueError("dominant_category_count must be positive for non-empty batches")
    if inputs.correlated_cluster_count > inputs.category_count:
        raise ValueError("correlated_cluster_count must not exceed category_count")


def _reason_codes(
    *,
    recommendation_count: Decimal,
    category_count: Decimal,
    dominant_category_ratio: Decimal,
    correlated_cluster_count: Decimal,
    minimum_category_count: Decimal,
) -> tuple[str, ...]:
    if recommendation_count == ZERO:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    if category_count <= ONE:
        reasons.append(SINGLE_CATEGORY_REASON)
    if category_count < minimum_category_count:
        reasons.append(MINIMUM_CATEGORY_REASON)
    if dominant_category_ratio > Decimal("0.500000"):
        reasons.append(DOMINANT_CATEGORY_BLOCKER_REASON)
    elif dominant_category_ratio >= Decimal("0.500000"):
        reasons.append(DOMINANT_CATEGORY_WATCH_REASON)
    if category_count > TWO and correlated_cluster_count >= category_count:
        reasons.append(CORRELATED_CLUSTER_REASON)
    if not reasons:
        return (READY_REASON,)
    return tuple(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "diversified"
    if (
        EMPTY_REASON in reason_codes
        or SINGLE_CATEGORY_REASON in reason_codes
        or DOMINANT_CATEGORY_BLOCKER_REASON in reason_codes
    ):
        return "blocked"
    return "attention"


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if status == "diversified":
        return "manual_review_batch_diversification"
    if EMPTY_REASON in reason_codes:
        return "manual_add_recommendations_before_review"
    if status == "blocked":
        return "manual_split_batch_or_add_uncorrelated_categories"
    return "manual_add_independent_category_review"


def _validate_report(report: OperatorRecommendationBatchDiversificationReport) -> None:
    _validate_input_counts(report)
    expected_category_ratio = _safe_ratio(report.category_count, report.recommendation_count)
    expected_dominant_ratio = _safe_ratio(
        report.dominant_category_count,
        report.recommendation_count,
    )
    if report.category_ratio != expected_category_ratio:
        raise ValueError("category_ratio must match counts")
    if report.dominant_category_ratio != expected_dominant_ratio:
        raise ValueError("dominant_category_ratio must match counts")
    expected_reasons = _reason_codes(
        recommendation_count=report.recommendation_count,
        category_count=report.category_count,
        dominant_category_ratio=report.dominant_category_ratio,
        correlated_cluster_count=report.correlated_cluster_count,
        minimum_category_count=report.minimum_category_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match diversification inputs")
    expected_status = _status_from_reason_codes(report.reason_codes)
    if report.diversification_status != expected_status:
        raise ValueError("diversification_status must match reason_codes")
    expected_next_step = _manual_next_step(report.diversification_status, report.reason_codes)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match diversification status")


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    _reject_unsafe_public_payload(payload)
    if set(payload) != set(PAYLOAD_KEYS):
        raise ValueError("public payload fields must match report schema exactly")
    if (
        payload["config_version"]
        != OPERATOR_RECOMMENDATION_BATCH_DIVERSIFICATION_REPORT_VERSION
    ):
        raise ValueError("config_version must be the supported report version")
    if payload["diversification_status"] not in STATUS_VALUES:
        raise ValueError("diversification_status must be a supported status")
    _normalize_reason_codes(_require_string_tuple(payload["reason_codes"]))
    if payload["manual_next_step"] not in NEXT_STEP_VALUES:
        raise ValueError("manual_next_step must be a supported manual action")
    for field_name in (
        "recommendation_count",
        "category_count",
        "dominant_category_count",
        "correlated_cluster_count",
        "minimum_category_count",
        "category_ratio",
        "dominant_category_ratio",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _require_hard_flags(_MappingFlags(payload))
    _require_digest("payload_digest", payload["payload_digest"])
    if payload["payload_digest"] != _payload_digest(dict(payload) | {"payload_digest": ""}):
        raise ValueError("payload_digest must match public payload")


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _payload_items(
    report: OperatorRecommendationBatchDiversificationReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(
        {
            "config_version": report.config_version,
            "diversification_status": report.diversification_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "recommendation_count": report.recommendation_count,
            "category_count": report.category_count,
            "dominant_category_count": report.dominant_category_count,
            "correlated_cluster_count": report.correlated_cluster_count,
            "minimum_category_count": report.minimum_category_count,
            "category_ratio": report.category_ratio,
            "dominant_category_ratio": report.dominant_category_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
        payload_digest=payload_digest,
    )


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    payload = {
        key: _coerce_payload_value(values[key])
        for key in PAYLOAD_KEYS
        if key != "payload_digest"
    }
    payload["payload_digest"] = payload_digest
    return payload


def _coerce_payload_value(value: object) -> object:
    if type(value) is Decimal:
        return _format_decimal(value)
    if type(value) is tuple:
        return value
    if type(value) in (str, bool):
        return value
    raise ValueError("public payload contains unsupported value type")


def _payload_digest(payload: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if decimal_value.is_nan() or decimal_value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if _format_decimal(decimal_value) != value:
        raise ValueError(f"{field_name} must use six decimal places")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_VALUES:
            raise ValueError("reason_codes must contain supported reason codes")
        if reason_code in normalized:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(reason_code)
    if READY_REASON in normalized and len(normalized) != 1:
        raise ValueError("ready reason_code must be the only reason_code")
    return tuple(normalized)


def _require_string_tuple(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not all(type(item) is str for item in value):
        raise ValueError("reason_codes must contain strings")
    return value


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(value: object) -> None:
    if value.paper_only is not True:
        raise ValueError("paper_only must be True")
    if value.report_only is not True:
        raise ValueError("report_only must be True")
    if value.readonly is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(payload: Mapping[str, object]) -> None:
    for key, value in payload.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in UNSAFE_PUBLIC_TOKENS):
            raise ValueError("unsafe public payload field")
        if type(value) is str:
            value_lower = value.lower()
            if any(token in value_lower for token in UNSAFE_PUBLIC_TOKENS):
                raise ValueError("unsafe public payload value")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _format_decimal(value: Decimal) -> str:
    return format(_quantize(value), "f")
