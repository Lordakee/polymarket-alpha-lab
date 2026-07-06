"""Pure paper-only research quality trend snapshot builder v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_RESEARCH_QUALITY_TREND_SNAPSHOT_V10_CONFIG_VERSION = (
    "strategy-research-quality-trend-snapshot-v10"
)

SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MIN_RECENT_PACKET_COUNT = Decimal("3")
STRONG_SCORE_THRESHOLD = Decimal("0.700000")
HIGH_STALENESS_THRESHOLD = Decimal("0.500000")
HIGH_CALIBRATION_ERROR_BPS = Decimal("100.000000")
HEALTHY_QUALITY_SCORE = Decimal("0.750000")
WATCH_QUALITY_SCORE = Decimal("0.600000")
COMPLETENESS_WEIGHT = Decimal("0.050000")
SOURCE_CONFIDENCE_WEIGHT = Decimal("0.550000")
FRESHNESS_WEIGHT = Decimal("0.400000")
CALIBRATION_ERROR_PENALTY = Decimal("0.000300")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

TREND_STATUSES = (
    "healthy",
    "watch",
    "degrading",
    "insufficient_data",
)
IMPROVEMENT_ACTIONS = (
    "maintain_current_research_process",
    "increase_recent_research_packet_sample",
    "complete_missing_research_sections",
    "raise_source_confidence_quorum",
    "refresh_stale_research_packets",
    "review_calibration_error_drivers",
    "monitor_quality_trend",
    "schedule_quality_recovery_review",
)
REASON_CODES = (
    "sample_sufficient",
    "sample_insufficient",
    "completeness_strong",
    "completeness_weak",
    "source_confidence_strong",
    "source_confidence_weak",
    "staleness_low",
    "staleness_high",
    "calibration_error_controlled",
    "calibration_error_high",
    "quality_trend_healthy",
    "quality_trend_watch",
    "quality_trend_degrading",
    "quality_trend_insufficient_data",
)
PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "category",
        "team_id",
        "recent_packet_count",
        "average_completeness_score",
        "average_source_confidence_score",
        "average_staleness_score",
        "calibration_error_bps",
        "days_window",
        "trend_status",
        "quality_score",
        "improvement_actions",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class StrategyResearchQualityTrendSnapshotV10Input:
    category: str
    team_id: str
    recent_packet_count: Decimal
    average_completeness_score: Decimal
    average_source_confidence_score: Decimal
    average_staleness_score: Decimal
    calibration_error_bps: Decimal
    days_window: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "recent_packet_count",
            _normalize_nonnegative_count(
                "recent_packet_count",
                self.recent_packet_count,
            ),
        )
        for field_name in (
            "average_completeness_score",
            "average_source_confidence_score",
            "average_staleness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_bps",
            _normalize_nonnegative_decimal(
                "calibration_error_bps",
                self.calibration_error_bps,
            ),
        )
        object.__setattr__(
            self,
            "days_window",
            _normalize_positive_count("days_window", self.days_window),
        )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyResearchQualityTrendSnapshotV10Report:
    config_version: str
    category: str
    team_id: str
    recent_packet_count: Decimal
    average_completeness_score: Decimal
    average_source_confidence_score: Decimal
    average_staleness_score: Decimal
    calibration_error_bps: Decimal
    days_window: Decimal
    trend_status: str
    quality_score: Decimal
    improvement_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("category", self.category)
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "recent_packet_count",
            _normalize_nonnegative_count(
                "recent_packet_count",
                self.recent_packet_count,
            ),
        )
        for field_name in (
            "average_completeness_score",
            "average_source_confidence_score",
            "average_staleness_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_bps",
            _normalize_nonnegative_decimal(
                "calibration_error_bps",
                self.calibration_error_bps,
            ),
        )
        object.__setattr__(
            self,
            "days_window",
            _normalize_positive_count("days_window", self.days_window),
        )
        object.__setattr__(
            self,
            "trend_status",
            _normalize_choice("trend_status", self.trend_status, TREND_STATUSES),
        )
        object.__setattr__(
            self,
            "improvement_actions",
            _normalize_string_choices(
                "improvement_actions",
                self.improvement_actions,
                IMPROVEMENT_ACTIONS,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_choices("reason_codes", self.reason_codes, REASON_CODES),
        )
        _validate_report(self)
        _require_paper_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_quality_trend_snapshot_v10_payload(self)


StrategyResearchQualityTrendSnapshotV10Result = (
    StrategyResearchQualityTrendSnapshotV10Report
)


def build_strategy_research_quality_trend_snapshot_v10(
    input_row: StrategyResearchQualityTrendSnapshotV10Input,
) -> StrategyResearchQualityTrendSnapshotV10Report:
    if type(input_row) is not StrategyResearchQualityTrendSnapshotV10Input:
        raise ValueError(
            "input_row must be a StrategyResearchQualityTrendSnapshotV10Input",
        )
    _require_paper_flags("input", input_row)
    quality_score = _quality_score(input_row)
    trend_status = _trend_status(input_row, quality_score)
    return StrategyResearchQualityTrendSnapshotV10Report(
        config_version=DEFAULT_STRATEGY_RESEARCH_QUALITY_TREND_SNAPSHOT_V10_CONFIG_VERSION,
        category=input_row.category,
        team_id=input_row.team_id,
        recent_packet_count=input_row.recent_packet_count,
        average_completeness_score=input_row.average_completeness_score,
        average_source_confidence_score=input_row.average_source_confidence_score,
        average_staleness_score=input_row.average_staleness_score,
        calibration_error_bps=input_row.calibration_error_bps,
        days_window=input_row.days_window,
        trend_status=trend_status,
        quality_score=quality_score,
        improvement_actions=_improvement_actions(input_row, trend_status),
        reason_codes=_reason_codes(input_row, trend_status),
    )


def strategy_research_quality_trend_snapshot_v10(
    value: StrategyResearchQualityTrendSnapshotV10Input | dict[str, Any],
) -> StrategyResearchQualityTrendSnapshotV10Report | dict[str, Any]:
    if type(value) is StrategyResearchQualityTrendSnapshotV10Input:
        return build_strategy_research_quality_trend_snapshot_v10(value)
    if type(value) is dict:
        return strategy_research_quality_trend_snapshot_v10_payload(value)
    raise ValueError(
        "value must be a StrategyResearchQualityTrendSnapshotV10Input",
    )


def strategy_research_quality_trend_snapshot_v10_payload(
    report: StrategyResearchQualityTrendSnapshotV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyResearchQualityTrendSnapshotV10Report:
        _require_paper_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _validate_payload_fields(report)
        _require_payload_flags(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyResearchQualityTrendSnapshotV10Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload_fields(payload)
    _require_payload_flags(payload)
    return payload


def _quality_score(input_row: StrategyResearchQualityTrendSnapshotV10Input) -> Decimal:
    freshness_score = _q(ONE - input_row.average_staleness_score)
    score = _q(
        (input_row.average_completeness_score * COMPLETENESS_WEIGHT)
        + (input_row.average_source_confidence_score * SOURCE_CONFIDENCE_WEIGHT)
        + (freshness_score * FRESHNESS_WEIGHT)
        - (input_row.calibration_error_bps * CALIBRATION_ERROR_PENALTY),
    )
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return score


def _trend_status(
    input_row: StrategyResearchQualityTrendSnapshotV10Input,
    quality_score: Decimal,
) -> str:
    if input_row.recent_packet_count < MIN_RECENT_PACKET_COUNT:
        return "insufficient_data"
    if quality_score >= HEALTHY_QUALITY_SCORE and _all_quality_inputs_strong(input_row):
        return "healthy"
    if quality_score >= WATCH_QUALITY_SCORE:
        return "watch"
    return "degrading"


def _all_quality_inputs_strong(
    input_row: StrategyResearchQualityTrendSnapshotV10Input,
) -> bool:
    return (
        input_row.average_completeness_score >= STRONG_SCORE_THRESHOLD
        and input_row.average_source_confidence_score >= STRONG_SCORE_THRESHOLD
        and input_row.average_staleness_score <= HIGH_STALENESS_THRESHOLD
        and input_row.calibration_error_bps <= HIGH_CALIBRATION_ERROR_BPS
    )


def _improvement_actions(
    input_row: StrategyResearchQualityTrendSnapshotV10Input,
    trend_status: str,
) -> tuple[str, ...]:
    if trend_status == "insufficient_data":
        return ("increase_recent_research_packet_sample",)
    actions: list[str] = []
    if input_row.average_completeness_score < STRONG_SCORE_THRESHOLD:
        actions.append("complete_missing_research_sections")
    if input_row.average_source_confidence_score < STRONG_SCORE_THRESHOLD:
        actions.append("raise_source_confidence_quorum")
    if input_row.average_staleness_score > HIGH_STALENESS_THRESHOLD:
        actions.append("refresh_stale_research_packets")
    if input_row.calibration_error_bps > HIGH_CALIBRATION_ERROR_BPS:
        actions.append("review_calibration_error_drivers")
    if trend_status == "degrading":
        actions.append("schedule_quality_recovery_review")
    elif trend_status == "watch":
        actions.append("monitor_quality_trend")
    if not actions:
        actions.append("maintain_current_research_process")
    return tuple(actions)


def _reason_codes(
    input_row: StrategyResearchQualityTrendSnapshotV10Input,
    trend_status: str,
) -> tuple[str, ...]:
    return (
        (
            "sample_sufficient"
            if input_row.recent_packet_count >= MIN_RECENT_PACKET_COUNT
            else "sample_insufficient"
        ),
        (
            "completeness_strong"
            if input_row.average_completeness_score >= STRONG_SCORE_THRESHOLD
            else "completeness_weak"
        ),
        (
            "source_confidence_strong"
            if input_row.average_source_confidence_score >= STRONG_SCORE_THRESHOLD
            else "source_confidence_weak"
        ),
        (
            "staleness_low"
            if input_row.average_staleness_score <= HIGH_STALENESS_THRESHOLD
            else "staleness_high"
        ),
        (
            "calibration_error_controlled"
            if input_row.calibration_error_bps <= HIGH_CALIBRATION_ERROR_BPS
            else "calibration_error_high"
        ),
        f"quality_trend_{trend_status}",
    )


def _validate_report(report: StrategyResearchQualityTrendSnapshotV10Report) -> None:
    input_row = StrategyResearchQualityTrendSnapshotV10Input(
        category=report.category,
        team_id=report.team_id,
        recent_packet_count=report.recent_packet_count,
        average_completeness_score=report.average_completeness_score,
        average_source_confidence_score=report.average_source_confidence_score,
        average_staleness_score=report.average_staleness_score,
        calibration_error_bps=report.calibration_error_bps,
        days_window=report.days_window,
    )
    expected_quality_score = _quality_score(input_row)
    expected_trend_status = _trend_status(input_row, expected_quality_score)
    if report.config_version != DEFAULT_STRATEGY_RESEARCH_QUALITY_TREND_SNAPSHOT_V10_CONFIG_VERSION:
        raise ValueError("report config_version must match")
    if report.quality_score != expected_quality_score:
        raise ValueError("report quality_score must match")
    if report.trend_status != expected_trend_status:
        raise ValueError("report trend_status must match")
    if report.improvement_actions != _improvement_actions(input_row, expected_trend_status):
        raise ValueError("report improvement_actions must match")
    if report.reason_codes != _reason_codes(input_row, expected_trend_status):
        raise ValueError("report reason_codes must match")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_choice(field_name: str, value: object, choices: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return value


def _normalize_string_choices(
    field_name: str,
    values: object,
    choices: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_normalize_choice(field_name, value, choices))
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_QUALITY_TREND_SNAPSHOT_V10_CONFIG_VERSION",
    "IMPROVEMENT_ACTIONS",
    "REASON_CODES",
    "TREND_STATUSES",
    "StrategyResearchQualityTrendSnapshotV10Input",
    "StrategyResearchQualityTrendSnapshotV10Report",
    "StrategyResearchQualityTrendSnapshotV10Result",
    "build_strategy_research_quality_trend_snapshot_v10",
    "strategy_research_quality_trend_snapshot_v10",
    "strategy_research_quality_trend_snapshot_v10_payload",
)
