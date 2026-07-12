"""Report-only probability event resolution timeline compression snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUSES = frozenset(("open", "compressed", "closed"))
_NEXT_STEPS = frozenset(
    (
        "archive_report_only_resolution_timeline",
        "escalate_manual_review_before_market_close",
        "prepare_manual_resolution_decision_packet",
        "refresh_public_sources_before_next_review",
    ),
)
_REASON_SEQUENCE = (
    "market_close_elapsed",
    "catalyst_before_close",
    "close_before_catalyst",
    "market_close_path",
    "review_path",
    "source_refresh_path",
    "manual_decision_path",
)


@dataclass(frozen=True)
class ProbabilityEventResolutionTimelineCompressionInput:
    market_close_hours: Decimal
    next_catalyst_hours: Decimal
    review_sla_hours: Decimal
    source_refresh_sla_hours: Decimal
    manual_decision_sla_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventResolutionTimelineCompressionInput:
            raise TypeError(
                "ProbabilityEventResolutionTimelineCompressionInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventResolutionTimelineCompressionInput:
            raise ValueError(
                "input must be exactly ProbabilityEventResolutionTimelineCompressionInput",
            )
        for field_name in (
            "market_close_hours",
            "next_catalyst_hours",
            "review_sla_hours",
            "source_refresh_sla_hours",
            "manual_decision_sla_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventResolutionTimelineCompressionReport:
    market_close_hours: Decimal
    next_catalyst_hours: Decimal
    review_sla_hours: Decimal
    source_refresh_sla_hours: Decimal
    manual_decision_sla_hours: Decimal
    compression_status: str
    critical_path_hours: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventResolutionTimelineCompressionReport:
            raise TypeError(
                "ProbabilityEventResolutionTimelineCompressionReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventResolutionTimelineCompressionReport:
            raise ValueError(
                "report must be exactly ProbabilityEventResolutionTimelineCompressionReport",
            )
        for field_name in (
            "market_close_hours",
            "next_catalyst_hours",
            "review_sla_hours",
            "source_refresh_sla_hours",
            "manual_decision_sla_hours",
            "critical_path_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("compression_status", self.compression_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_next_step("manual_next_step", self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        return payload


def build_probability_event_resolution_timeline_compression_report(
    item: ProbabilityEventResolutionTimelineCompressionInput,
) -> ProbabilityEventResolutionTimelineCompressionReport:
    """Build a local report-only timeline compression snapshot."""

    if type(item) is not ProbabilityEventResolutionTimelineCompressionInput:
        raise ValueError(
            "item must be a ProbabilityEventResolutionTimelineCompressionInput",
        )
    values: dict[str, object] = {
        "market_close_hours": item.market_close_hours,
        "next_catalyst_hours": item.next_catalyst_hours,
        "review_sla_hours": item.review_sla_hours,
        "source_refresh_sla_hours": item.source_refresh_sla_hours,
        "manual_decision_sla_hours": item.manual_decision_sla_hours,
        "compression_status": _compression_status(item),
        "critical_path_hours": _critical_path_hours(item),
        "reason_codes": _reason_codes(item),
        "manual_next_step": _manual_next_step(item),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventResolutionTimelineCompressionReport(
        **values,
        payload_digest=_digest_from_values(values),
    )


def _compression_status(
    item: ProbabilityEventResolutionTimelineCompressionInput,
) -> str:
    if item.market_close_hours == _ZERO:
        return "closed"
    reason_codes = _reason_codes(item)
    if "market_close_path" in reason_codes or "manual_decision_path" in reason_codes:
        return "compressed"
    return "open"


def _critical_path_hours(
    item: ProbabilityEventResolutionTimelineCompressionInput,
) -> Decimal:
    if item.market_close_hours == _ZERO:
        return _ZERO
    return min(
        item.market_close_hours,
        item.next_catalyst_hours,
        item.review_sla_hours,
        item.source_refresh_sla_hours,
        item.manual_decision_sla_hours,
    )


def _reason_codes(
    item: ProbabilityEventResolutionTimelineCompressionInput,
) -> tuple[str, ...]:
    if item.market_close_hours == _ZERO:
        return ("market_close_elapsed",)

    reason_codes: list[str] = []
    if item.next_catalyst_hours < item.market_close_hours:
        reason_codes.append("catalyst_before_close")
    else:
        reason_codes.append("close_before_catalyst")

    critical_path_hours = _critical_path_hours(item)
    if critical_path_hours == item.market_close_hours:
        reason_codes.append("market_close_path")
    elif critical_path_hours == item.source_refresh_sla_hours:
        reason_codes.append("source_refresh_path")
    elif critical_path_hours == item.manual_decision_sla_hours:
        reason_codes.append("manual_decision_path")
    else:
        reason_codes.append("review_path")
    return _normalize_reason_codes(tuple(reason_codes))


def _manual_next_step(
    item: ProbabilityEventResolutionTimelineCompressionInput,
) -> str:
    reason_codes = _reason_codes(item)
    if reason_codes == ("market_close_elapsed",):
        return "archive_report_only_resolution_timeline"
    if "market_close_path" in reason_codes:
        return "escalate_manual_review_before_market_close"
    if "manual_decision_path" in reason_codes:
        return "prepare_manual_resolution_decision_packet"
    return "refresh_public_sources_before_next_review"


def _validate_report_consistency(
    report: ProbabilityEventResolutionTimelineCompressionReport,
) -> None:
    item = ProbabilityEventResolutionTimelineCompressionInput(
        market_close_hours=report.market_close_hours,
        next_catalyst_hours=report.next_catalyst_hours,
        review_sla_hours=report.review_sla_hours,
        source_refresh_sla_hours=report.source_refresh_sla_hours,
        manual_decision_sla_hours=report.manual_decision_sla_hours,
    )
    if report.compression_status != _compression_status(item):
        raise ValueError("compression_status must match report inputs")
    if report.critical_path_hours != _critical_path_hours(item):
        raise ValueError("critical_path_hours must match report inputs")
    if report.reason_codes != _reason_codes(item):
        raise ValueError("reason_codes must match report inputs")
    if report.manual_next_step != _manual_next_step(item):
        raise ValueError("manual_next_step must match report inputs")


def _require_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be open, compressed, or closed")
    return value


def _require_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in normalized)


def _report_values_without_digest(
    report: ProbabilityEventResolutionTimelineCompressionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("payload_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item_value)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item_value) for item_value in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "ProbabilityEventResolutionTimelineCompressionInput",
    "ProbabilityEventResolutionTimelineCompressionReport",
    "build_probability_event_resolution_timeline_compression_report",
)
