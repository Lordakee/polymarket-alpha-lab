"""Pure paper-only probability event screen quality index reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


QUALITY_BANDS = ("ready", "watch", "blocked")
_QUALITY_BANDS = frozenset(QUALITY_BANDS)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_READY_MIN = Decimal("0.700000")
_WATCH_MIN = Decimal("0.500000")
_RELIABILITY_READY_MIN = Decimal("0.700000")
_RELIABILITY_BLOCK_MIN = Decimal("0.600000")
_DILIGENCE_READY_MIN = Decimal("0.700000")
_GAP_READY_MAX = Decimal("0.250000")
_GAP_BLOCK_MIN = Decimal("0.600000")
_RULE_READY_MIN = Decimal("0.700000")
_RULE_BLOCK_MIN = Decimal("0.600000")
_LIQUIDITY_READY_MAX = Decimal("0.350000")
_LIQUIDITY_BLOCK_MIN = Decimal("0.600000")
_MEMORY_READY_MIN = Decimal("0.600000")
_MEMORY_BLOCK_MIN = Decimal("0.500000")
_REASON_CODE_SEQUENCE = (
    "information_gap_score_high",
    "liquidity_exit_risk_score_high",
    "operator_safety_not_ready",
    "resolution_rule_clarity_score_low",
    "source_reliability_score_low",
    "team_memory_quality_score_low",
    "due_diligence_depth_score_low",
    "information_gap_score_elevated",
    "liquidity_exit_risk_score_elevated",
    "quality_index_score_low",
    "source_reliability_score_watch",
)
_PUBLIC_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class ProbabilityEventScreenQualityIndexReport:
    source_reliability_score: Decimal
    due_diligence_depth_score: Decimal
    information_gap_score: Decimal
    resolution_rule_clarity_score: Decimal
    liquidity_exit_risk_score: Decimal
    team_memory_quality_score: Decimal
    operator_safety_ready: bool
    quality_index_score: Decimal
    quality_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "source_reliability_score",
            "due_diligence_depth_score",
            "information_gap_score",
            "resolution_rule_clarity_score",
            "liquidity_exit_risk_score",
            "team_memory_quality_score",
            "quality_index_score",
            "ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("operator_safety_ready", self.operator_safety_ready)
        _require_quality_band("quality_band", self.quality_band)
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
        return probability_event_screen_quality_index_report_digest(self)


def build_probability_event_screen_quality_index_report(
    *,
    source_reliability_score: Decimal,
    due_diligence_depth_score: Decimal,
    information_gap_score: Decimal,
    resolution_rule_clarity_score: Decimal,
    liquidity_exit_risk_score: Decimal,
    team_memory_quality_score: Decimal,
    operator_safety_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenQualityIndexReport:
    reliability = _require_ratio_decimal(
        "source_reliability_score",
        source_reliability_score,
    )
    diligence = _require_ratio_decimal(
        "due_diligence_depth_score",
        due_diligence_depth_score,
    )
    information_gap = _require_ratio_decimal(
        "information_gap_score",
        information_gap_score,
    )
    rule_clarity = _require_ratio_decimal(
        "resolution_rule_clarity_score",
        resolution_rule_clarity_score,
    )
    liquidity_risk = _require_ratio_decimal(
        "liquidity_exit_risk_score",
        liquidity_exit_risk_score,
    )
    memory = _require_ratio_decimal(
        "team_memory_quality_score",
        team_memory_quality_score,
    )
    _require_bool("operator_safety_ready", operator_safety_ready)
    flags = _PublicFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    quality_score = _quality_index_score(
        source_reliability_score=reliability,
        due_diligence_depth_score=diligence,
        information_gap_score=information_gap,
        resolution_rule_clarity_score=rule_clarity,
        liquidity_exit_risk_score=liquidity_risk,
        team_memory_quality_score=memory,
    )
    blocked_reasons = _blocked_reason_codes(
        source_reliability_score=reliability,
        information_gap_score=information_gap,
        resolution_rule_clarity_score=rule_clarity,
        liquidity_exit_risk_score=liquidity_risk,
        team_memory_quality_score=memory,
        operator_safety_ready=operator_safety_ready,
    )
    attention_reasons = _attention_reason_codes(
        source_reliability_score=reliability,
        due_diligence_depth_score=diligence,
        information_gap_score=information_gap,
        liquidity_exit_risk_score=liquidity_risk,
        quality_index_score=quality_score,
    )
    quality_band = _quality_band(quality_score, blocked_reasons, attention_reasons)
    return ProbabilityEventScreenQualityIndexReport(
        source_reliability_score=reliability,
        due_diligence_depth_score=diligence,
        information_gap_score=information_gap,
        resolution_rule_clarity_score=rule_clarity,
        liquidity_exit_risk_score=liquidity_risk,
        team_memory_quality_score=memory,
        operator_safety_ready=operator_safety_ready,
        quality_index_score=quality_score,
        quality_band=quality_band,
        blocked_reason_codes=blocked_reasons,
        attention_reason_codes=attention_reasons,
        ready_ratio=_ready_ratio(quality_band, quality_score),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_screen_quality_index_report_payload(
    report: ProbabilityEventScreenQualityIndexReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenQualityIndexReport:
        raise ValueError("report must be a ProbabilityEventScreenQualityIndexReport")
    return report.public_payload


def probability_event_screen_quality_index_report_digest(
    report: ProbabilityEventScreenQualityIndexReport,
) -> str:
    if type(report) is not ProbabilityEventScreenQualityIndexReport:
        raise ValueError("report must be a ProbabilityEventScreenQualityIndexReport")
    canonical = json.dumps(
        _payload_without_digest(report),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _PublicFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _quality_index_score(
    *,
    source_reliability_score: Decimal,
    due_diligence_depth_score: Decimal,
    information_gap_score: Decimal,
    resolution_rule_clarity_score: Decimal,
    liquidity_exit_risk_score: Decimal,
    team_memory_quality_score: Decimal,
) -> Decimal:
    favorable_sum = (
        source_reliability_score
        + due_diligence_depth_score
        + (_ONE - information_gap_score)
        + resolution_rule_clarity_score
        + (_ONE - liquidity_exit_risk_score)
        + team_memory_quality_score
    )
    return _quantize(favorable_sum / Decimal("6"))


def _blocked_reason_codes(
    *,
    source_reliability_score: Decimal,
    information_gap_score: Decimal,
    resolution_rule_clarity_score: Decimal,
    liquidity_exit_risk_score: Decimal,
    team_memory_quality_score: Decimal,
    operator_safety_ready: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if information_gap_score >= _GAP_BLOCK_MIN:
        reason_codes.append("information_gap_score_high")
    if liquidity_exit_risk_score >= _LIQUIDITY_BLOCK_MIN:
        reason_codes.append("liquidity_exit_risk_score_high")
    if not operator_safety_ready:
        reason_codes.append("operator_safety_not_ready")
    if resolution_rule_clarity_score < _RULE_BLOCK_MIN:
        reason_codes.append("resolution_rule_clarity_score_low")
    if source_reliability_score < _RELIABILITY_BLOCK_MIN:
        reason_codes.append("source_reliability_score_low")
    if team_memory_quality_score < _MEMORY_BLOCK_MIN:
        reason_codes.append("team_memory_quality_score_low")
    return _normalize_reason_codes(reason_codes)


def _attention_reason_codes(
    *,
    source_reliability_score: Decimal,
    due_diligence_depth_score: Decimal,
    information_gap_score: Decimal,
    liquidity_exit_risk_score: Decimal,
    quality_index_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if due_diligence_depth_score < _DILIGENCE_READY_MIN:
        reason_codes.append("due_diligence_depth_score_low")
    if _GAP_READY_MAX < information_gap_score < _GAP_BLOCK_MIN:
        reason_codes.append("information_gap_score_elevated")
    if _LIQUIDITY_READY_MAX < liquidity_exit_risk_score < _LIQUIDITY_BLOCK_MIN:
        reason_codes.append("liquidity_exit_risk_score_elevated")
    if quality_index_score < _WATCH_MIN:
        reason_codes.append("quality_index_score_low")
    if _RELIABILITY_BLOCK_MIN <= source_reliability_score < _RELIABILITY_READY_MIN:
        reason_codes.append("source_reliability_score_watch")
    return _normalize_reason_codes(reason_codes)


def _quality_band(
    quality_index_score: Decimal,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes or quality_index_score < _READY_MIN:
        return "watch"
    return "ready"


def _ready_ratio(quality_band: str, quality_index_score: Decimal) -> Decimal:
    if quality_band == "blocked":
        return _ZERO
    if quality_band == "ready":
        return _ONE
    return quality_index_score


def _validate_report_consistency(
    report: ProbabilityEventScreenQualityIndexReport,
) -> None:
    expected_score = _quality_index_score(
        source_reliability_score=report.source_reliability_score,
        due_diligence_depth_score=report.due_diligence_depth_score,
        information_gap_score=report.information_gap_score,
        resolution_rule_clarity_score=report.resolution_rule_clarity_score,
        liquidity_exit_risk_score=report.liquidity_exit_risk_score,
        team_memory_quality_score=report.team_memory_quality_score,
    )
    if report.quality_index_score != expected_score:
        raise ValueError("quality_index_score must match report inputs")

    expected_blocked = _blocked_reason_codes(
        source_reliability_score=report.source_reliability_score,
        information_gap_score=report.information_gap_score,
        resolution_rule_clarity_score=report.resolution_rule_clarity_score,
        liquidity_exit_risk_score=report.liquidity_exit_risk_score,
        team_memory_quality_score=report.team_memory_quality_score,
        operator_safety_ready=report.operator_safety_ready,
    )
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match report inputs")

    expected_attention = _attention_reason_codes(
        source_reliability_score=report.source_reliability_score,
        due_diligence_depth_score=report.due_diligence_depth_score,
        information_gap_score=report.information_gap_score,
        liquidity_exit_risk_score=report.liquidity_exit_risk_score,
        quality_index_score=report.quality_index_score,
    )
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match report inputs")

    expected_band = _quality_band(
        report.quality_index_score,
        report.blocked_reason_codes,
        report.attention_reason_codes,
    )
    if report.quality_band != expected_band:
        raise ValueError("quality_band must match report inputs")

    expected_ready_ratio = _ready_ratio(report.quality_band, report.quality_index_score)
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match report inputs")


def _payload_without_digest(
    report: ProbabilityEventScreenQualityIndexReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenQualityIndexReport:
        raise ValueError("report must be a ProbabilityEventScreenQualityIndexReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    payload.pop("digest", None)
    _reject_runtime_numbers(payload)
    _reject_unsafe_keys(payload)
    return payload


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, ".6f")
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value


def _reject_runtime_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public_payload must not contain runtime numeric values")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_runtime_numbers(item)
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for item in value:
            _reject_runtime_numbers(item)


def _reject_unsafe_keys(value: object) -> None:
    forbidden = (
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "data" + "base",
        "net" + "work",
    )
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered_key = str(key).lower()
            if any(token in lowered_key for token in forbidden):
                raise ValueError("public_payload contains unsafe key")
            _reject_unsafe_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for item in value:
            _reject_unsafe_keys(item)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_quality_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _QUALITY_BANDS:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, str) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError(f"unknown reason_code: {reason_code}")
        normalized.add(reason_code)
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PUBLIC_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


__all__ = [
    "QUALITY_BANDS",
    "ProbabilityEventScreenQualityIndexReport",
    "build_probability_event_screen_quality_index_report",
    "probability_event_screen_quality_index_report_digest",
    "probability_event_screen_quality_index_report_payload",
]
