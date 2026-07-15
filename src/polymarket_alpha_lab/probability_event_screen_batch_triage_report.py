"""Pure paper-only probability event screen batch triage reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_EDGE_READY_MIN = Decimal("0.050000")
_QUALITY_READY_MIN = Decimal("0.600000")
_TRIAGE_BANDS = frozenset(("ready", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "operator_output_safety_not_ready",
    "screen_batch_contains_blocked_candidates",
    "edge_to_threshold_probability_low",
    "manual_review_queue_available",
    "manual_review_queue_empty",
    "memory_context_score_low",
    "screen_batch_contains_watch_candidates",
    "screen_batch_empty",
    "source_reliability_score_low",
)


@dataclass(frozen=True)
class ProbabilityEventScreenBatchTriageReport:
    total_candidate_count: Decimal
    ready_for_manual_review_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    highest_edge_to_threshold_probability: Decimal
    average_source_reliability_score: Decimal
    average_memory_context_score: Decimal
    operator_output_safety_ready: bool
    batch_triage_ready: bool
    triage_band: str
    next_manual_review_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "total_candidate_count",
            "ready_for_manual_review_count",
            "watch_count",
            "blocked_count",
            "next_manual_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_edge_to_threshold_probability",
            "average_source_reliability_score",
            "average_memory_context_score",
            "ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("operator_output_safety_ready", self.operator_output_safety_ready)
        _require_bool("batch_triage_ready", self.batch_triage_ready)
        _require_triage_band("triage_band", self.triage_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(self.attention_reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _payload_without_digest(self)
        payload["digest"] = self.digest
        return payload

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_probability_event_screen_batch_triage_report(
    *,
    total_candidate_count: Decimal,
    ready_for_manual_review_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    highest_edge_to_threshold_probability: Decimal,
    average_source_reliability_score: Decimal,
    average_memory_context_score: Decimal,
    operator_output_safety_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenBatchTriageReport:
    total = _require_count_decimal("total_candidate_count", total_candidate_count)
    ready_count = _require_count_decimal(
        "ready_for_manual_review_count",
        ready_for_manual_review_count,
    )
    watch = _require_count_decimal("watch_count", watch_count)
    blocked = _require_count_decimal("blocked_count", blocked_count)
    edge = _require_ratio_decimal(
        "highest_edge_to_threshold_probability",
        highest_edge_to_threshold_probability,
    )
    source_score = _require_ratio_decimal(
        "average_source_reliability_score",
        average_source_reliability_score,
    )
    memory_score = _require_ratio_decimal(
        "average_memory_context_score",
        average_memory_context_score,
    )
    _require_bool("operator_output_safety_ready", operator_output_safety_ready)
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)
    _require_candidate_counts(total, ready_count, watch, blocked)

    blocked_reasons = _blocked_reason_codes(
        operator_output_safety_ready=operator_output_safety_ready,
        blocked_count=blocked,
    )
    attention_reasons = _attention_reason_codes(
        total_candidate_count=total,
        ready_for_manual_review_count=ready_count,
        watch_count=watch,
        highest_edge_to_threshold_probability=edge,
        average_source_reliability_score=source_score,
        average_memory_context_score=memory_score,
        blocked_reason_codes=blocked_reasons,
    )
    triage_band = _triage_band(blocked_reasons, attention_reasons)
    return ProbabilityEventScreenBatchTriageReport(
        total_candidate_count=total,
        ready_for_manual_review_count=ready_count,
        watch_count=watch,
        blocked_count=blocked,
        highest_edge_to_threshold_probability=edge,
        average_source_reliability_score=source_score,
        average_memory_context_score=memory_score,
        operator_output_safety_ready=operator_output_safety_ready,
        batch_triage_ready=triage_band == "ready" and ready_count > _ZERO,
        triage_band=triage_band,
        next_manual_review_count=_next_manual_review_count(
            triage_band=triage_band,
            ready_for_manual_review_count=ready_count,
        ),
        blocked_reason_codes=blocked_reasons,
        attention_reason_codes=attention_reasons,
        ready_ratio=_ready_ratio(ready_count, total),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_screen_batch_triage_report_payload(
    report: ProbabilityEventScreenBatchTriageReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenBatchTriageReport:
        raise ValueError("report must be a ProbabilityEventScreenBatchTriageReport")
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _blocked_reason_codes(
    *,
    operator_output_safety_ready: bool,
    blocked_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not operator_output_safety_ready:
        reason_codes.append("operator_output_safety_not_ready")
    if blocked_count > _ZERO:
        reason_codes.append("screen_batch_contains_blocked_candidates")
    return _normalize_reason_codes(reason_codes)


def _attention_reason_codes(
    *,
    total_candidate_count: Decimal,
    ready_for_manual_review_count: Decimal,
    watch_count: Decimal,
    highest_edge_to_threshold_probability: Decimal,
    average_source_reliability_score: Decimal,
    average_memory_context_score: Decimal,
    blocked_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if total_candidate_count == _ZERO:
        reason_codes.append("screen_batch_empty")
    elif ready_for_manual_review_count == _ZERO:
        reason_codes.append("manual_review_queue_empty")
    elif blocked_reason_codes or watch_count > _ZERO:
        reason_codes.append("manual_review_queue_available")
    if watch_count > _ZERO:
        reason_codes.append("screen_batch_contains_watch_candidates")
    if highest_edge_to_threshold_probability < _EDGE_READY_MIN:
        reason_codes.append("edge_to_threshold_probability_low")
    if average_source_reliability_score < _QUALITY_READY_MIN:
        reason_codes.append("source_reliability_score_low")
    if average_memory_context_score < _QUALITY_READY_MIN:
        reason_codes.append("memory_context_score_low")
    return _normalize_reason_codes(reason_codes)


def _triage_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "watch"
    return "ready"


def _next_manual_review_count(
    *,
    triage_band: str,
    ready_for_manual_review_count: Decimal,
) -> Decimal:
    if triage_band == "blocked":
        return _ZERO
    return ready_for_manual_review_count


def _ready_ratio(ready_for_manual_review_count: Decimal, total_candidate_count: Decimal) -> Decimal:
    if total_candidate_count == _ZERO:
        return _ZERO
    return _quantize(ready_for_manual_review_count / total_candidate_count)


def _validate_report_consistency(report: ProbabilityEventScreenBatchTriageReport) -> None:
    _require_candidate_counts(
        report.total_candidate_count,
        report.ready_for_manual_review_count,
        report.watch_count,
        report.blocked_count,
    )
    expected_blocked_reasons = _blocked_reason_codes(
        operator_output_safety_ready=report.operator_output_safety_ready,
        blocked_count=report.blocked_count,
    )
    if report.blocked_reason_codes != expected_blocked_reasons:
        raise ValueError("blocked_reason_codes must match report inputs")
    expected_attention_reasons = _attention_reason_codes(
        total_candidate_count=report.total_candidate_count,
        ready_for_manual_review_count=report.ready_for_manual_review_count,
        watch_count=report.watch_count,
        highest_edge_to_threshold_probability=report.highest_edge_to_threshold_probability,
        average_source_reliability_score=report.average_source_reliability_score,
        average_memory_context_score=report.average_memory_context_score,
        blocked_reason_codes=expected_blocked_reasons,
    )
    if report.attention_reason_codes != expected_attention_reasons:
        raise ValueError("attention_reason_codes must match report inputs")
    expected_band = _triage_band(expected_blocked_reasons, expected_attention_reasons)
    if report.triage_band != expected_band:
        raise ValueError("triage_band must match report inputs")
    expected_ready = expected_band == "ready" and report.ready_for_manual_review_count > _ZERO
    if report.batch_triage_ready is not expected_ready:
        raise ValueError("batch_triage_ready must match report inputs")
    expected_next_count = _next_manual_review_count(
        triage_band=expected_band,
        ready_for_manual_review_count=report.ready_for_manual_review_count,
    )
    if report.next_manual_review_count != expected_next_count:
        raise ValueError("next_manual_review_count must match report inputs")
    expected_ready_ratio = _ready_ratio(
        report.ready_for_manual_review_count,
        report.total_candidate_count,
    )
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match report inputs")


def _require_candidate_counts(
    total_candidate_count: Decimal,
    ready_for_manual_review_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> None:
    if total_candidate_count != ready_for_manual_review_count + watch_count + blocked_count:
        raise ValueError("candidate counts must sum to total_candidate_count")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_triage_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _TRIAGE_BANDS:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _payload_without_digest(report: ProbabilityEventScreenBatchTriageReport) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return payload


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
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "ProbabilityEventScreenBatchTriageReport",
    "build_probability_event_screen_batch_triage_report",
    "probability_event_screen_batch_triage_report_payload",
)
