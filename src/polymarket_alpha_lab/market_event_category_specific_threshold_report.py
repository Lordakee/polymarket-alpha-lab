"""Readonly category-specific threshold readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_CONFIG_VERSION = (
    "market-event-category-specific-threshold-report-v0"
)
MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
MIN_EDGE_PROBABILITY_FLOOR = Decimal("0.010000")
MIN_SOURCE_QUALITY_PROBABILITY_FLOOR = Decimal("0.500000")
MAX_COST_PROBABILITY_CEILING = Decimal("0.050000")
MAX_LATENCY_HOURS_CEILING = Decimal("24.000000")
HEX_CHARS = frozenset("0123456789abcdef")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_CODES = (
    "category_specific_thresholds_ready",
    "manual_override_required",
    "max_cost_probability_above_category_ceiling",
    "max_latency_hours_above_category_ceiling",
    "min_edge_probability_below_category_floor",
    "min_source_quality_probability_below_category_floor",
)


@dataclass(frozen=True)
class MarketEventCategorySpecificThresholdReport:
    category_id: str
    min_edge_probability: Decimal
    min_source_quality_probability: Decimal
    max_cost_probability: Decimal
    max_latency_hours: Decimal
    manual_override_required: bool
    threshold_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category_id",
            _require_public_identifier("category_id", self.category_id),
        )
        for field_name in (
            "min_edge_probability",
            "min_source_quality_probability",
            "max_cost_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latency_hours",
            _normalize_positive_decimal("max_latency_hours", self.max_latency_hours),
        )
        if type(self.manual_override_required) is not bool:
            raise ValueError("manual_override_required must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_status("threshold_status", self.threshold_status)
        _require_public_text("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _apply_or_verify_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_event_category_specific_threshold_report_payload(self)


def build_market_event_category_specific_threshold_report(
    *,
    category_id: str,
    min_edge_probability: Decimal,
    min_source_quality_probability: Decimal,
    max_cost_probability: Decimal,
    max_latency_hours: Decimal,
    manual_override_required: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEventCategorySpecificThresholdReport:
    normalized_min_edge = _normalize_probability(
        "min_edge_probability",
        min_edge_probability,
    )
    normalized_source_quality = _normalize_probability(
        "min_source_quality_probability",
        min_source_quality_probability,
    )
    normalized_max_cost = _normalize_probability(
        "max_cost_probability",
        max_cost_probability,
    )
    normalized_latency = _normalize_positive_decimal(
        "max_latency_hours",
        max_latency_hours,
    )
    if type(manual_override_required) is not bool:
        raise ValueError("manual_override_required must be a bool")
    reason_codes = _reason_codes(
        min_edge_probability=normalized_min_edge,
        min_source_quality_probability=normalized_source_quality,
        max_cost_probability=normalized_max_cost,
        max_latency_hours=normalized_latency,
        manual_override_required=manual_override_required,
    )
    status = _threshold_status(reason_codes)
    return MarketEventCategorySpecificThresholdReport(
        category_id=category_id,
        min_edge_probability=normalized_min_edge,
        min_source_quality_probability=normalized_source_quality,
        max_cost_probability=normalized_max_cost,
        max_latency_hours=normalized_latency,
        manual_override_required=manual_override_required,
        threshold_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status, reason_codes),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def market_event_category_specific_threshold_report_payload(
    value: MarketEventCategorySpecificThresholdReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is MarketEventCategorySpecificThresholdReport:
        _require_hard_flags("report", value)
        _validate_report_consistency(value)
        payload = _json_ready(asdict(value))
    elif type(value) is dict:
        _require_hard_flags("payload", _DictFlags(value))
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a MarketEventCategorySpecificThresholdReport or public payload",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_public_payload(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _reason_codes(
    *,
    min_edge_probability: Decimal,
    min_source_quality_probability: Decimal,
    max_cost_probability: Decimal,
    max_latency_hours: Decimal,
    manual_override_required: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if min_edge_probability < MIN_EDGE_PROBABILITY_FLOOR:
        codes.append("min_edge_probability_below_category_floor")
    if min_source_quality_probability < MIN_SOURCE_QUALITY_PROBABILITY_FLOOR:
        codes.append("min_source_quality_probability_below_category_floor")
    if max_cost_probability > MAX_COST_PROBABILITY_CEILING:
        codes.append("max_cost_probability_above_category_ceiling")
    if max_latency_hours > MAX_LATENCY_HOURS_CEILING:
        codes.append("max_latency_hours_above_category_ceiling")
    if manual_override_required:
        codes.append("manual_override_required")
    if not codes:
        codes.append("category_specific_thresholds_ready")
    return tuple(codes)


def _threshold_status(reason_codes: tuple[str, ...]) -> str:
    blocking_codes = {
        "max_cost_probability_above_category_ceiling",
        "max_latency_hours_above_category_ceiling",
        "min_edge_probability_below_category_floor",
        "min_source_quality_probability_below_category_floor",
    }
    if any(code in blocking_codes for code in reason_codes):
        return "block"
    if "manual_override_required" in reason_codes:
        return "watch"
    return "pass"


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if status == "pass":
        return "Use the category-specific thresholds for paper-only screening review."
    if status == "watch" and reason_codes == ("manual_override_required",):
        return "Complete manual override review before marking thresholds ready."
    return "Revise category-specific thresholds before paper-only screening review."


def _validate_report_consistency(
    report: MarketEventCategorySpecificThresholdReport,
) -> None:
    expected_reason_codes = _reason_codes(
        min_edge_probability=report.min_edge_probability,
        min_source_quality_probability=report.min_source_quality_probability,
        max_cost_probability=report.max_cost_probability,
        max_latency_hours=report.max_latency_hours,
        manual_override_required=report.manual_override_required,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match threshold inputs")
    expected_status = _threshold_status(expected_reason_codes)
    if report.threshold_status != expected_status:
        raise ValueError("threshold_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status, expected_reason_codes):
        raise ValueError("manual_next_step must match threshold_status")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    for field_name in (
        "category_id",
        "min_edge_probability",
        "min_source_quality_probability",
        "max_cost_probability",
        "max_latency_hours",
        "manual_override_required",
        "threshold_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    _require_digest("payload_digest", payload["payload_digest"])
    if payload["payload_digest"] != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    _require_public_identifier("category_id", payload["category_id"])
    _normalize_probability(
        "min_edge_probability",
        _decimal_from_payload("min_edge_probability", payload["min_edge_probability"]),
    )
    _normalize_probability(
        "min_source_quality_probability",
        _decimal_from_payload(
            "min_source_quality_probability",
            payload["min_source_quality_probability"],
        ),
    )
    _normalize_probability(
        "max_cost_probability",
        _decimal_from_payload("max_cost_probability", payload["max_cost_probability"]),
    )
    _normalize_positive_decimal(
        "max_latency_hours",
        _decimal_from_payload("max_latency_hours", payload["max_latency_hours"]),
    )
    if type(payload["manual_override_required"]) is not bool:
        raise ValueError("manual_override_required must be a bool")
    _require_status("threshold_status", payload["threshold_status"])
    reason_codes = _normalize_reason_codes(tuple(payload["reason_codes"]))
    _require_public_text("manual_next_step", payload["manual_next_step"])
    expected_reason_codes = _reason_codes(
        min_edge_probability=_decimal_from_payload(
            "min_edge_probability",
            payload["min_edge_probability"],
        ),
        min_source_quality_probability=_decimal_from_payload(
            "min_source_quality_probability",
            payload["min_source_quality_probability"],
        ),
        max_cost_probability=_decimal_from_payload(
            "max_cost_probability",
            payload["max_cost_probability"],
        ),
        max_latency_hours=_decimal_from_payload(
            "max_latency_hours",
            payload["max_latency_hours"],
        ),
        manual_override_required=payload["manual_override_required"],
    )
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match threshold inputs")
    expected_status = _threshold_status(expected_reason_codes)
    if payload["threshold_status"] != expected_status:
        raise ValueError("threshold_status must match reason_codes")
    if payload["manual_next_step"] != _manual_next_step(expected_status, reason_codes):
        raise ValueError("manual_next_step must match threshold_status")

def _apply_or_verify_digest(report: MarketEventCategorySpecificThresholdReport) -> None:
    expected_digest = _payload_digest(_public_payload_without_digest(report))
    if report.payload_digest == "":
        object.__setattr__(report, "payload_digest", expected_digest)
        return
    _require_digest("payload_digest", report.payload_digest)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")


def _public_payload_without_digest(
    report: MarketEventCategorySpecificThresholdReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("payload_digest", None)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    values = dict(payload)
    values.pop("payload_digest", None)
    encoded = dumps(
        _json_ready(values),
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value.quantize(DECIMAL_QUANTUM), "f")
    if isinstance(value, dict):
        return {str(name): _json_ready(item) for name, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than 0")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value.quantize(DECIMAL_QUANTUM)


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in REASON_CODES:
            raise ValueError(f"unknown reason_code: {reason_code}")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    return tuple(normalized)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{field_name} must not be empty")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be empty")


def _require_status(field_name: str, value: object) -> None:
    if value not in MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{context}.{field_name} must be True")


__all__ = (
    "DEFAULT_MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_CONFIG_VERSION",
    "MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_STATUSES",
    "MarketEventCategorySpecificThresholdReport",
    "build_market_event_category_specific_threshold_report",
    "market_event_category_specific_threshold_report_payload",
)
