"""Pure paper-only probability event screen rank reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TOP_FRACTION = Decimal("0.250000")
_EDGE_READY_MIN = Decimal("0.050000")
_QUALITY_READY_MIN = Decimal("0.600000")
_SOURCE_READY_MIN = Decimal("0.600000")
_URGENCY_WATCH_MIN = Decimal("0.800000")
_RANKING_BANDS = frozenset(("top", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_BLOCKED_REASON_SEQUENCE = (
    "liquidity_exit_not_ready",
    "manual_decision_gate_not_ready",
    "operator_safety_not_ready",
)
_ATTENTION_REASON_SEQUENCE = (
    "candidate_batch_empty",
    "edge_to_threshold_probability_low",
    "quality_index_score_low",
    "source_reliability_score_low",
    "time_decay_urgency_high",
)
_REASON_CODE_SEQUENCE = _BLOCKED_REASON_SEQUENCE + _ATTENTION_REASON_SEQUENCE


@dataclass(frozen=True)
class ProbabilityEventScreenRankOrderReport:
    candidate_count: Decimal
    quality_index_score: Decimal
    edge_to_threshold_probability: Decimal
    time_decay_urgency_score: Decimal
    source_reliability_score: Decimal
    liquidity_exit_ready: bool
    manual_decision_gate_ready: bool
    operator_safety_ready: bool
    rank_order_ready: bool
    ranking_band: str
    top_candidate_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_count", "top_candidate_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quality_index_score",
            "edge_to_threshold_probability",
            "time_decay_urgency_score",
            "source_reliability_score",
            "ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_exit_ready",
            "manual_decision_gate_ready",
            "operator_safety_ready",
            "rank_order_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_ranking_band("ranking_band", self.ranking_band)
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


def build_probability_event_screen_rank_order_report(
    *,
    candidate_count: Decimal,
    quality_index_score: Decimal,
    edge_to_threshold_probability: Decimal,
    time_decay_urgency_score: Decimal,
    source_reliability_score: Decimal,
    liquidity_exit_ready: bool,
    manual_decision_gate_ready: bool,
    operator_safety_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenRankOrderReport:
    count = _require_count_decimal("candidate_count", candidate_count)
    quality = _require_ratio_decimal("quality_index_score", quality_index_score)
    edge = _require_ratio_decimal(
        "edge_to_threshold_probability",
        edge_to_threshold_probability,
    )
    urgency = _require_ratio_decimal(
        "time_decay_urgency_score",
        time_decay_urgency_score,
    )
    source = _require_ratio_decimal(
        "source_reliability_score",
        source_reliability_score,
    )
    for field_name, value in (
        ("liquidity_exit_ready", liquidity_exit_ready),
        ("manual_decision_gate_ready", manual_decision_gate_ready),
        ("operator_safety_ready", operator_safety_ready),
    ):
        _require_bool(field_name, value)
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    blocked_reasons = _blocked_reason_codes(
        liquidity_exit_ready=liquidity_exit_ready,
        manual_decision_gate_ready=manual_decision_gate_ready,
        operator_safety_ready=operator_safety_ready,
    )
    attention_reasons = ()
    if not blocked_reasons:
        attention_reasons = _attention_reason_codes(
            candidate_count=count,
            quality_index_score=quality,
            edge_to_threshold_probability=edge,
            time_decay_urgency_score=urgency,
            source_reliability_score=source,
        )
    ranking_band = _ranking_band(blocked_reasons, attention_reasons, count)
    top_count = _top_candidate_count(
        candidate_count=count,
        blocked_reason_codes=blocked_reasons,
    )
    return ProbabilityEventScreenRankOrderReport(
        candidate_count=count,
        quality_index_score=quality,
        edge_to_threshold_probability=edge,
        time_decay_urgency_score=urgency,
        source_reliability_score=source,
        liquidity_exit_ready=liquidity_exit_ready,
        manual_decision_gate_ready=manual_decision_gate_ready,
        operator_safety_ready=operator_safety_ready,
        rank_order_ready=ranking_band == "top" and count > _ZERO,
        ranking_band=ranking_band,
        top_candidate_count=top_count,
        blocked_reason_codes=blocked_reasons,
        attention_reason_codes=attention_reasons,
        ready_ratio=_ready_ratio(
            ranking_band=ranking_band,
            candidate_count=count,
            top_candidate_count=top_count,
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_screen_rank_order_report_payload(
    report: ProbabilityEventScreenRankOrderReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenRankOrderReport:
        raise ValueError("report must be a ProbabilityEventScreenRankOrderReport")
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _blocked_reason_codes(
    *,
    liquidity_exit_ready: bool,
    manual_decision_gate_ready: bool,
    operator_safety_ready: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not liquidity_exit_ready:
        reason_codes.append("liquidity_exit_not_ready")
    if not manual_decision_gate_ready:
        reason_codes.append("manual_decision_gate_not_ready")
    if not operator_safety_ready:
        reason_codes.append("operator_safety_not_ready")
    return _normalize_reason_codes(reason_codes)


def _attention_reason_codes(
    *,
    candidate_count: Decimal,
    quality_index_score: Decimal,
    edge_to_threshold_probability: Decimal,
    time_decay_urgency_score: Decimal,
    source_reliability_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate_count == _ZERO:
        reason_codes.append("candidate_batch_empty")
    if edge_to_threshold_probability < _EDGE_READY_MIN:
        reason_codes.append("edge_to_threshold_probability_low")
    if quality_index_score < _QUALITY_READY_MIN:
        reason_codes.append("quality_index_score_low")
    if source_reliability_score < _SOURCE_READY_MIN:
        reason_codes.append("source_reliability_score_low")
    if time_decay_urgency_score >= _URGENCY_WATCH_MIN:
        reason_codes.append("time_decay_urgency_high")
    return _normalize_reason_codes(reason_codes)


def _ranking_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
    candidate_count: Decimal,
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes or candidate_count == _ZERO:
        return "watch"
    return "top"


def _top_candidate_count(
    *,
    candidate_count: Decimal,
    blocked_reason_codes: tuple[str, ...],
) -> Decimal:
    if blocked_reason_codes or candidate_count == _ZERO:
        return _ZERO
    top_count = (candidate_count * _TOP_FRACTION).to_integral_value(
        rounding=ROUND_FLOOR,
    )
    if top_count < Decimal("1"):
        top_count = Decimal("1")
    return _quantize(top_count)


def _ready_ratio(
    *,
    ranking_band: str,
    candidate_count: Decimal,
    top_candidate_count: Decimal,
) -> Decimal:
    if ranking_band == "blocked" or candidate_count == _ZERO:
        return _ZERO
    if ranking_band == "top":
        return _ONE
    return _quantize(top_candidate_count / candidate_count)


def _validate_report_consistency(report: ProbabilityEventScreenRankOrderReport) -> None:
    expected_blocked_reasons = _blocked_reason_codes(
        liquidity_exit_ready=report.liquidity_exit_ready,
        manual_decision_gate_ready=report.manual_decision_gate_ready,
        operator_safety_ready=report.operator_safety_ready,
    )
    if report.blocked_reason_codes != expected_blocked_reasons:
        raise ValueError("blocked_reason_codes must match report inputs")
    expected_attention_reasons = ()
    if not expected_blocked_reasons:
        expected_attention_reasons = _attention_reason_codes(
            candidate_count=report.candidate_count,
            quality_index_score=report.quality_index_score,
            edge_to_threshold_probability=report.edge_to_threshold_probability,
            time_decay_urgency_score=report.time_decay_urgency_score,
            source_reliability_score=report.source_reliability_score,
        )
    if report.attention_reason_codes != expected_attention_reasons:
        raise ValueError("attention_reason_codes must match report inputs")
    expected_band = _ranking_band(
        expected_blocked_reasons,
        expected_attention_reasons,
        report.candidate_count,
    )
    if report.ranking_band != expected_band:
        raise ValueError("ranking_band must match report inputs")
    expected_top_count = _top_candidate_count(
        candidate_count=report.candidate_count,
        blocked_reason_codes=expected_blocked_reasons,
    )
    if report.top_candidate_count != expected_top_count:
        raise ValueError("top_candidate_count must match report inputs")
    expected_ready = expected_band == "top" and report.candidate_count > _ZERO
    if report.rank_order_ready is not expected_ready:
        raise ValueError("rank_order_ready must match report inputs")
    expected_ready_ratio = _ready_ratio(
        ranking_band=expected_band,
        candidate_count=report.candidate_count,
        top_candidate_count=expected_top_count,
    )
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match report inputs")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_ranking_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _RANKING_BANDS:
        raise ValueError(f"{field_name} must be top, watch, or blocked")


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


def _payload_without_digest(report: ProbabilityEventScreenRankOrderReport) -> dict[str, Any]:
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
    "ProbabilityEventScreenRankOrderReport",
    "build_probability_event_screen_rank_order_report",
    "probability_event_screen_rank_order_report_payload",
)
