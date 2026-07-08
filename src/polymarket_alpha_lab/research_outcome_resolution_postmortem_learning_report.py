from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_CONFIG_VERSION = (
    "research-outcome-resolution-postmortem-learning-v1"
)
OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_STATUSES = ("pass", "watch", "block")
_DIGEST_PREFIX = "rorplr-v1:"
_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_UNSAFE_PUBLIC_KEYS = frozenset(
    (
        "market_id",
        "market_slug",
        "outcome_id",
        "outcome_ref",
        "source_id",
        "source_ref",
        "source_url",
        "raw_market",
        "raw_source",
    ),
)
_UNSAFE_TEXT_FRAGMENTS = (
    "".join(("ht", "tp")),
    "://",
    "raw-market",
    "raw_source",
    "private-source",
)


@dataclass(frozen=True)
class ResearchOutcomeResolutionPostmortemLearningConfig:
    config_version: str = (
        DEFAULT_RESEARCH_OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_CONFIG_VERSION
    )
    forecast_error_watch_threshold: Decimal = Decimal("0.100000")
    forecast_error_block_threshold: Decimal = Decimal("0.300000")
    evidence_miss_watch_threshold: Decimal = Decimal("0.100000")
    evidence_miss_block_threshold: Decimal = Decimal("0.250000")
    resolution_ambiguity_watch_threshold: Decimal = Decimal("0.150000")
    resolution_ambiguity_block_threshold: Decimal = Decimal("0.350000")
    cost_friction_miss_watch_threshold: Decimal = Decimal("0.080000")
    cost_friction_miss_block_threshold: Decimal = Decimal("0.200000")
    source_reliability_loss_watch_threshold: Decimal = Decimal("0.050000")
    source_reliability_loss_block_threshold: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for name in (
            "forecast_error_watch_threshold",
            "forecast_error_block_threshold",
            "evidence_miss_watch_threshold",
            "evidence_miss_block_threshold",
            "resolution_ambiguity_watch_threshold",
            "resolution_ambiguity_block_threshold",
            "cost_friction_miss_watch_threshold",
            "cost_friction_miss_block_threshold",
            "source_reliability_loss_watch_threshold",
            "source_reliability_loss_block_threshold",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_ratio(name, getattr(self, name)),
            )
        _require_threshold_pair(
            "forecast_error",
            self.forecast_error_watch_threshold,
            self.forecast_error_block_threshold,
        )
        _require_threshold_pair(
            "evidence_miss",
            self.evidence_miss_watch_threshold,
            self.evidence_miss_block_threshold,
        )
        _require_threshold_pair(
            "resolution_ambiguity",
            self.resolution_ambiguity_watch_threshold,
            self.resolution_ambiguity_block_threshold,
        )
        _require_threshold_pair(
            "cost_friction_miss",
            self.cost_friction_miss_watch_threshold,
            self.cost_friction_miss_block_threshold,
        )
        _require_threshold_pair(
            "source_reliability_loss",
            self.source_reliability_loss_watch_threshold,
            self.source_reliability_loss_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchOutcomeResolutionPostmortemLearningSignal:
    specialist_team_ref: str
    outcome_ref: str
    source_ref: str
    resolved_at: datetime
    aggregate_forecast_error: Decimal
    evidence_miss_rate: Decimal
    resolution_ambiguity_score: Decimal
    cost_friction_miss: Decimal
    source_reliability_delta: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("specialist_team_ref", self.specialist_team_ref)
        _require_text("outcome_ref", self.outcome_ref)
        _require_text("source_ref", self.source_ref)
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for name in (
            "aggregate_forecast_error",
            "evidence_miss_rate",
            "resolution_ambiguity_score",
            "cost_friction_miss",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_ratio(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "source_reliability_delta",
            _normalize_signed_ratio(
                "source_reliability_delta",
                self.source_reliability_delta,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchOutcomeResolutionPostmortemLearningRow:
    redacted_team_ref: str
    redacted_outcome_ref: str
    redacted_source_ref: str
    resolved_at: datetime
    aggregate_forecast_error: Decimal
    evidence_miss_rate: Decimal
    resolution_ambiguity_score: Decimal
    cost_friction_miss: Decimal
    source_reliability_delta: Decimal
    source_reliability_loss_score: Decimal
    learning_pressure_score: Decimal
    learning_status: str
    learning_rank: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("redacted_team_ref", self.redacted_team_ref, "team")
        _require_redacted_ref("redacted_outcome_ref", self.redacted_outcome_ref, "outcome")
        _require_redacted_ref("redacted_source_ref", self.redacted_source_ref, "source")
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for name in (
            "aggregate_forecast_error",
            "evidence_miss_rate",
            "resolution_ambiguity_score",
            "cost_friction_miss",
            "source_reliability_loss_score",
            "learning_pressure_score",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_ratio(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "source_reliability_delta",
            _normalize_signed_ratio(
                "source_reliability_delta",
                self.source_reliability_delta,
            ),
        )
        object.__setattr__(
            self,
            "learning_rank",
            _normalize_nonnegative_count("learning_rank", self.learning_rank),
        )
        _require_member("learning_status", self.learning_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_row_digest(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchOutcomeResolutionPostmortemLearningReport:
    generated_at: datetime
    config_version: str
    source_signal_count: Decimal
    learning_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_forecast_error: Decimal
    average_evidence_miss_rate: Decimal
    average_resolution_ambiguity_score: Decimal
    average_cost_friction_miss: Decimal
    average_source_reliability_delta: Decimal
    max_learning_pressure_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    learning_rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for name in (
            "source_signal_count",
            "learning_row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_count(name, getattr(self, name)),
            )
        for name in (
            "average_forecast_error",
            "average_evidence_miss_rate",
            "average_resolution_ambiguity_score",
            "average_cost_friction_miss",
            "max_learning_pressure_score",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_ratio(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "average_source_reliability_delta",
            _normalize_signed_ratio(
                "average_source_reliability_delta",
                self.average_source_reliability_delta,
            ),
        )
        _require_member("report_status", self.report_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "learning_rows", _normalize_rows(self.learning_rows))
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_outcome_resolution_postmortem_learning_report(
    signals: (
        list[ResearchOutcomeResolutionPostmortemLearningSignal]
        | tuple[ResearchOutcomeResolutionPostmortemLearningSignal, ...]
    ),
    *,
    config: ResearchOutcomeResolutionPostmortemLearningConfig,
    generated_at: datetime,
) -> ResearchOutcomeResolutionPostmortemLearningReport:
    if type(config) is not ResearchOutcomeResolutionPostmortemLearningConfig:
        raise ValueError(
            "config must be a ResearchOutcomeResolutionPostmortemLearningConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_signals = _normalize_signals(signals, generated_at_utc)
    team_refs = _redaction_map(
        tuple(signal.specialist_team_ref for signal in source_signals),
        "team",
    )
    outcome_refs = _redaction_map(
        tuple(signal.outcome_ref for signal in source_signals),
        "outcome",
    )
    source_refs = _redaction_map(
        tuple(signal.source_ref for signal in source_signals),
        "source",
    )
    unranked_rows = tuple(
        _row_from_signal(
            signal,
            config=config,
            redacted_team_ref=team_refs[signal.specialist_team_ref],
            redacted_outcome_ref=outcome_refs[signal.outcome_ref],
            redacted_source_ref=source_refs[signal.source_ref],
            learning_rank=_ZERO_COUNT,
        )
        for signal in source_signals
    )
    ranked_rows = tuple(
        _row_with_rank(row, _count(index))
        for index, row in enumerate(sorted(unranked_rows, key=_row_sort_key), start=1)
    )
    source_signal_count = _count(len(source_signals))
    learning_row_count = _count(len(ranked_rows))
    pass_count = _count(_status_count(ranked_rows, "pass"))
    watch_count = _count(_status_count(ranked_rows, "watch"))
    block_count = _count(_status_count(ranked_rows, "block"))
    reason_codes = (
        ("outcome_resolution_postmortem_empty",)
        if not ranked_rows
        else _report_reason_codes(ranked_rows)
    )
    report_status = _report_status(ranked_rows)

    return ResearchOutcomeResolutionPostmortemLearningReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_signal_count=source_signal_count,
        learning_row_count=learning_row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_forecast_error=_mean(
            tuple(row.aggregate_forecast_error for row in ranked_rows),
        ),
        average_evidence_miss_rate=_mean(
            tuple(row.evidence_miss_rate for row in ranked_rows),
        ),
        average_resolution_ambiguity_score=_mean(
            tuple(row.resolution_ambiguity_score for row in ranked_rows),
        ),
        average_cost_friction_miss=_mean(
            tuple(row.cost_friction_miss for row in ranked_rows),
        ),
        average_source_reliability_delta=_mean(
            tuple(row.source_reliability_delta for row in ranked_rows),
        ),
        max_learning_pressure_score=_max_pressure(ranked_rows),
        report_status=report_status,
        reason_codes=reason_codes,
        learning_rows=ranked_rows,
        validation_digest=_report_validation_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            source_signal_count=source_signal_count,
            learning_row_count=learning_row_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            average_forecast_error=_mean(
                tuple(row.aggregate_forecast_error for row in ranked_rows),
            ),
            average_evidence_miss_rate=_mean(
                tuple(row.evidence_miss_rate for row in ranked_rows),
            ),
            average_resolution_ambiguity_score=_mean(
                tuple(row.resolution_ambiguity_score for row in ranked_rows),
            ),
            average_cost_friction_miss=_mean(
                tuple(row.cost_friction_miss for row in ranked_rows),
            ),
            average_source_reliability_delta=_mean(
                tuple(row.source_reliability_delta for row in ranked_rows),
            ),
            max_learning_pressure_score=_max_pressure(ranked_rows),
            report_status=report_status,
            reason_codes=reason_codes,
            learning_rows=ranked_rows,
        ),
    )


def research_outcome_resolution_postmortem_learning_report_payload(
    report: ResearchOutcomeResolutionPostmortemLearningReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchOutcomeResolutionPostmortemLearningReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _require_recursive_hard_flags("payload", report)
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchOutcomeResolutionPostmortemLearningReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _require_recursive_hard_flags("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
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


def _normalize_signals(
    signals: (
        list[ResearchOutcomeResolutionPostmortemLearningSignal]
        | tuple[ResearchOutcomeResolutionPostmortemLearningSignal, ...]
    ),
    generated_at: datetime,
) -> tuple[ResearchOutcomeResolutionPostmortemLearningSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not ResearchOutcomeResolutionPostmortemLearningSignal:
            raise ValueError(
                "signals must contain ResearchOutcomeResolutionPostmortemLearningSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.resolved_at > generated_at:
            raise ValueError("resolved_at must not be after generated_at")
        key = (signal.specialist_team_ref, signal.outcome_ref)
        if key in seen:
            raise ValueError("signals must contain unique team outcome pairs")
        seen.add(key)
    return normalized


def _row_from_signal(
    signal: ResearchOutcomeResolutionPostmortemLearningSignal,
    *,
    config: ResearchOutcomeResolutionPostmortemLearningConfig,
    redacted_team_ref: str,
    redacted_outcome_ref: str,
    redacted_source_ref: str,
    learning_rank: Decimal,
) -> ResearchOutcomeResolutionPostmortemLearningRow:
    source_reliability_loss_score = _source_reliability_loss(
        signal.source_reliability_delta,
    )
    learning_pressure_score = _mean(
        (
            signal.aggregate_forecast_error,
            signal.evidence_miss_rate,
            signal.resolution_ambiguity_score,
            signal.cost_friction_miss,
            source_reliability_loss_score,
        ),
    )
    reason_codes = _row_reason_codes(
        signal,
        config,
        source_reliability_loss_score=source_reliability_loss_score,
    )
    learning_status = _status_from_reason_codes(reason_codes)
    return ResearchOutcomeResolutionPostmortemLearningRow(
        redacted_team_ref=redacted_team_ref,
        redacted_outcome_ref=redacted_outcome_ref,
        redacted_source_ref=redacted_source_ref,
        resolved_at=signal.resolved_at,
        aggregate_forecast_error=signal.aggregate_forecast_error,
        evidence_miss_rate=signal.evidence_miss_rate,
        resolution_ambiguity_score=signal.resolution_ambiguity_score,
        cost_friction_miss=signal.cost_friction_miss,
        source_reliability_delta=signal.source_reliability_delta,
        source_reliability_loss_score=source_reliability_loss_score,
        learning_pressure_score=learning_pressure_score,
        learning_status=learning_status,
        learning_rank=learning_rank,
        reason_codes=reason_codes,
        validation_digest=_row_validation_digest(
            redacted_team_ref=redacted_team_ref,
            redacted_outcome_ref=redacted_outcome_ref,
            redacted_source_ref=redacted_source_ref,
            resolved_at=signal.resolved_at,
            aggregate_forecast_error=signal.aggregate_forecast_error,
            evidence_miss_rate=signal.evidence_miss_rate,
            resolution_ambiguity_score=signal.resolution_ambiguity_score,
            cost_friction_miss=signal.cost_friction_miss,
            source_reliability_delta=signal.source_reliability_delta,
            source_reliability_loss_score=source_reliability_loss_score,
            learning_pressure_score=learning_pressure_score,
            learning_status=learning_status,
            learning_rank=learning_rank,
            reason_codes=reason_codes,
        ),
    )


def _row_with_rank(
    row: ResearchOutcomeResolutionPostmortemLearningRow,
    learning_rank: Decimal,
) -> ResearchOutcomeResolutionPostmortemLearningRow:
    return ResearchOutcomeResolutionPostmortemLearningRow(
        redacted_team_ref=row.redacted_team_ref,
        redacted_outcome_ref=row.redacted_outcome_ref,
        redacted_source_ref=row.redacted_source_ref,
        resolved_at=row.resolved_at,
        aggregate_forecast_error=row.aggregate_forecast_error,
        evidence_miss_rate=row.evidence_miss_rate,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        cost_friction_miss=row.cost_friction_miss,
        source_reliability_delta=row.source_reliability_delta,
        source_reliability_loss_score=row.source_reliability_loss_score,
        learning_pressure_score=row.learning_pressure_score,
        learning_status=row.learning_status,
        learning_rank=learning_rank,
        reason_codes=row.reason_codes,
        validation_digest=_row_validation_digest(
            redacted_team_ref=row.redacted_team_ref,
            redacted_outcome_ref=row.redacted_outcome_ref,
            redacted_source_ref=row.redacted_source_ref,
            resolved_at=row.resolved_at,
            aggregate_forecast_error=row.aggregate_forecast_error,
            evidence_miss_rate=row.evidence_miss_rate,
            resolution_ambiguity_score=row.resolution_ambiguity_score,
            cost_friction_miss=row.cost_friction_miss,
            source_reliability_delta=row.source_reliability_delta,
            source_reliability_loss_score=row.source_reliability_loss_score,
            learning_pressure_score=row.learning_pressure_score,
            learning_status=row.learning_status,
            learning_rank=learning_rank,
            reason_codes=row.reason_codes,
        ),
    )


def _row_reason_codes(
    signal: ResearchOutcomeResolutionPostmortemLearningSignal,
    config: ResearchOutcomeResolutionPostmortemLearningConfig,
    *,
    source_reliability_loss_score: Decimal,
) -> tuple[str, ...]:
    block_reasons = _metric_reason_codes(
        signal,
        config,
        source_reliability_loss_score=source_reliability_loss_score,
        severity="block",
    )
    if block_reasons:
        return block_reasons
    watch_reasons = _metric_reason_codes(
        signal,
        config,
        source_reliability_loss_score=source_reliability_loss_score,
        severity="watch",
    )
    if watch_reasons:
        return watch_reasons
    return ("outcome_resolution_postmortem_passed",)


def _metric_reason_codes(
    signal: ResearchOutcomeResolutionPostmortemLearningSignal,
    config: ResearchOutcomeResolutionPostmortemLearningConfig,
    *,
    source_reliability_loss_score: Decimal,
    severity: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    checks = (
        (
            signal.aggregate_forecast_error,
            config.forecast_error_watch_threshold,
            config.forecast_error_block_threshold,
            "outcome_resolution_postmortem_forecast_error",
        ),
        (
            signal.evidence_miss_rate,
            config.evidence_miss_watch_threshold,
            config.evidence_miss_block_threshold,
            "outcome_resolution_postmortem_evidence_miss",
        ),
        (
            signal.resolution_ambiguity_score,
            config.resolution_ambiguity_watch_threshold,
            config.resolution_ambiguity_block_threshold,
            "outcome_resolution_postmortem_resolution_ambiguity",
        ),
        (
            signal.cost_friction_miss,
            config.cost_friction_miss_watch_threshold,
            config.cost_friction_miss_block_threshold,
            "outcome_resolution_postmortem_cost_friction_miss",
        ),
        (
            source_reliability_loss_score,
            config.source_reliability_loss_watch_threshold,
            config.source_reliability_loss_block_threshold,
            "outcome_resolution_postmortem_source_reliability_delta",
        ),
    )
    for value, watch_threshold, block_threshold, prefix in checks:
        threshold = block_threshold if severity == "block" else watch_threshold
        if value >= threshold:
            reasons.append(f"{prefix}_{severity}")
    return tuple(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...],
) -> str:
    if any(row.learning_status == "block" for row in rows):
        return "block"
    if not rows or any(row.learning_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    reasons: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code == "outcome_resolution_postmortem_passed":
                continue
            if reason_code not in seen:
                reasons.append(reason_code)
                seen.add(reason_code)
    if not reasons and rows:
        return ("outcome_resolution_postmortem_passed",)
    return tuple(reasons)


def _redaction_map(values: tuple[str, ...], label: str) -> dict[str, str]:
    return {
        value: f"<redacted-{label}-{index:03d}>"
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _row_sort_key(row: ResearchOutcomeResolutionPostmortemLearningRow) -> tuple[int, str, str]:
    return (
        _STATUS_WEIGHT[row.learning_status],
        _negative_decimal_key(row.learning_pressure_score),
        row.redacted_team_ref,
    )


def _negative_decimal_key(value: Decimal) -> str:
    return f"{_ONE_RATIO - value:>12}"


def _normalize_rows(
    rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...],
) -> tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("learning_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchOutcomeResolutionPostmortemLearningRow:
            raise ValueError(
                "learning_rows must contain ResearchOutcomeResolutionPostmortemLearningRow",
            )
        _require_hard_flags("row", row)
    return normalized


def _status_count(
    rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.learning_status == status)


def _max_pressure(
    rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO_RATIO
    return max(row.learning_pressure_score for row in rows)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    with localcontext(_DECIMAL_CONTEXT):
        return (sum(values, _ZERO_RATIO) / Decimal(len(values))).quantize(_RATIO_QUANTUM)


def _source_reliability_loss(value: Decimal) -> Decimal:
    if value >= _ZERO_RATIO:
        return _ZERO_RATIO
    with localcontext(_DECIMAL_CONTEXT):
        return (-value).quantize(_RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_count(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < _ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be a whole number")
    return value.quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_ratio(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < _ZERO_RATIO or value > _ONE_RATIO:
        raise ValueError(f"{name} must be between 0 and 1")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_RATIO_QUANTUM)


def _normalize_signed_ratio(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < -_ONE_RATIO or value > _ONE_RATIO:
        raise ValueError(f"{name} must be between -1 and 1")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_RATIO_QUANTUM)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _require_threshold_pair(name: str, watch: Decimal, block: Decimal) -> None:
    if block <= watch:
        raise ValueError(f"{name} block threshold must exceed watch threshold")


def _require_text(name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_redacted_ref(name: str, value: str, label: str) -> None:
    _require_text(name, value)
    prefix = f"<redacted-{label}-"
    if not value.startswith(prefix) or not value.endswith(">"):
        raise ValueError(f"{name} must be a redacted {label} ref")


def _require_member(name: str, value: object) -> None:
    if value not in OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_STATUSES:
        raise ValueError(
            f"{name} must be one of {OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_STATUSES}",
        )


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_text("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return normalized


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{name}.{flag} must be True")


def _require_recursive_hard_flags(name: str, value: Any) -> None:
    if is_dataclass(value):
        if all(hasattr(value, flag) for flag in ("paper_only", "report_only", "readonly")):
            _require_hard_flags(name, value)
        for field in fields(value):
            _require_recursive_hard_flags(field.name, getattr(value, field.name))
    elif type(value) is dict:
        if any(flag in value for flag in ("paper_only", "report_only", "readonly")):
            _require_hard_flags(name, _DictFlags(value))
        for nested in value.values():
            _require_recursive_hard_flags(name, nested)
    elif type(value) in (list, tuple):
        for nested in value:
            _require_recursive_hard_flags(name, nested)


def _require_validation_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.startswith(_DIGEST_PREFIX):
        raise ValueError(f"{name} must start with {_DIGEST_PREFIX}")
    digest = value.removeprefix(_DIGEST_PREFIX)
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError(f"{name} must include a sha256 hex digest")
    return value


def _validate_row_digest(row: ResearchOutcomeResolutionPostmortemLearningRow) -> None:
    expected = _row_validation_digest(
        redacted_team_ref=row.redacted_team_ref,
        redacted_outcome_ref=row.redacted_outcome_ref,
        redacted_source_ref=row.redacted_source_ref,
        resolved_at=row.resolved_at,
        aggregate_forecast_error=row.aggregate_forecast_error,
        evidence_miss_rate=row.evidence_miss_rate,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        cost_friction_miss=row.cost_friction_miss,
        source_reliability_delta=row.source_reliability_delta,
        source_reliability_loss_score=row.source_reliability_loss_score,
        learning_pressure_score=row.learning_pressure_score,
        learning_status=row.learning_status,
        learning_rank=row.learning_rank,
        reason_codes=row.reason_codes,
    )
    if row.validation_digest != expected:
        raise ValueError("validation_digest does not match row")


def _validate_report(report: ResearchOutcomeResolutionPostmortemLearningReport) -> None:
    rows = report.learning_rows
    if report.source_signal_count != _count(len(rows)):
        raise ValueError("source_signal_count does not match learning_rows")
    if report.learning_row_count != _count(len(rows)):
        raise ValueError("learning_row_count does not match learning_rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count does not match learning_rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count does not match learning_rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count does not match learning_rows")
    if report.average_forecast_error != _mean(
        tuple(row.aggregate_forecast_error for row in rows),
    ):
        raise ValueError("average_forecast_error does not match learning_rows")
    if report.average_evidence_miss_rate != _mean(
        tuple(row.evidence_miss_rate for row in rows),
    ):
        raise ValueError("average_evidence_miss_rate does not match learning_rows")
    if report.average_resolution_ambiguity_score != _mean(
        tuple(row.resolution_ambiguity_score for row in rows),
    ):
        raise ValueError("average_resolution_ambiguity_score does not match learning_rows")
    if report.average_cost_friction_miss != _mean(
        tuple(row.cost_friction_miss for row in rows),
    ):
        raise ValueError("average_cost_friction_miss does not match learning_rows")
    if report.average_source_reliability_delta != _mean(
        tuple(row.source_reliability_delta for row in rows),
    ):
        raise ValueError("average_source_reliability_delta does not match learning_rows")
    if report.max_learning_pressure_score != _max_pressure(rows):
        raise ValueError("max_learning_pressure_score does not match learning_rows")
    expected_reason_codes = (
        ("outcome_resolution_postmortem_empty",)
        if not rows
        else _report_reason_codes(rows)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match learning_rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status does not match learning_rows")
    expected = _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_signal_count=report.source_signal_count,
        learning_row_count=report.learning_row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_forecast_error=report.average_forecast_error,
        average_evidence_miss_rate=report.average_evidence_miss_rate,
        average_resolution_ambiguity_score=report.average_resolution_ambiguity_score,
        average_cost_friction_miss=report.average_cost_friction_miss,
        average_source_reliability_delta=report.average_source_reliability_delta,
        max_learning_pressure_score=report.max_learning_pressure_score,
        report_status=report.report_status,
        reason_codes=report.reason_codes,
        learning_rows=report.learning_rows,
    )
    if report.validation_digest != expected:
        raise ValueError("validation_digest does not match report")


def _row_validation_digest(
    *,
    redacted_team_ref: str,
    redacted_outcome_ref: str,
    redacted_source_ref: str,
    resolved_at: datetime,
    aggregate_forecast_error: Decimal,
    evidence_miss_rate: Decimal,
    resolution_ambiguity_score: Decimal,
    cost_friction_miss: Decimal,
    source_reliability_delta: Decimal,
    source_reliability_loss_score: Decimal,
    learning_pressure_score: Decimal,
    learning_status: str,
    learning_rank: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    return _validation_digest(
        {
            "redacted_team_ref": redacted_team_ref,
            "redacted_outcome_ref": redacted_outcome_ref,
            "redacted_source_ref": redacted_source_ref,
            "resolved_at": resolved_at,
            "aggregate_forecast_error": aggregate_forecast_error,
            "evidence_miss_rate": evidence_miss_rate,
            "resolution_ambiguity_score": resolution_ambiguity_score,
            "cost_friction_miss": cost_friction_miss,
            "source_reliability_delta": source_reliability_delta,
            "source_reliability_loss_score": source_reliability_loss_score,
            "learning_pressure_score": learning_pressure_score,
            "learning_status": learning_status,
            "learning_rank": learning_rank,
            "reason_codes": reason_codes,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    source_signal_count: Decimal,
    learning_row_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_forecast_error: Decimal,
    average_evidence_miss_rate: Decimal,
    average_resolution_ambiguity_score: Decimal,
    average_cost_friction_miss: Decimal,
    average_source_reliability_delta: Decimal,
    max_learning_pressure_score: Decimal,
    report_status: str,
    reason_codes: tuple[str, ...],
    learning_rows: tuple[ResearchOutcomeResolutionPostmortemLearningRow, ...],
) -> str:
    return _validation_digest(
        {
            "generated_at": generated_at,
            "config_version": config_version,
            "source_signal_count": source_signal_count,
            "learning_row_count": learning_row_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "block_count": block_count,
            "average_forecast_error": average_forecast_error,
            "average_evidence_miss_rate": average_evidence_miss_rate,
            "average_resolution_ambiguity_score": average_resolution_ambiguity_score,
            "average_cost_friction_miss": average_cost_friction_miss,
            "average_source_reliability_delta": average_source_reliability_delta,
            "max_learning_pressure_score": max_learning_pressure_score,
            "report_status": report_status,
            "reason_codes": reason_codes,
            "learning_rows": learning_rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _validation_digest(value: Any) -> str:
    ready = _json_ready(value)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return _DIGEST_PREFIX + sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(nested) for nested in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    return value


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    if is_dataclass(value):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
    elif type(value) is dict:
        for key, nested in value.items():
            if type(key) is str and key in _UNSAFE_PUBLIC_KEYS:
                raise ValueError(f"{name} contains unsafe public payload")
            _reject_unsafe_public_payload(str(key), nested)
    elif type(value) in (list, tuple):
        for nested in value:
            _reject_unsafe_public_payload(name, nested)
    elif type(value) is str and not value.startswith("<redacted-"):
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{name} contains unsafe public payload")


__all__ = (
    "DEFAULT_RESEARCH_OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_CONFIG_VERSION",
    "OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_STATUSES",
    "ResearchOutcomeResolutionPostmortemLearningConfig",
    "ResearchOutcomeResolutionPostmortemLearningReport",
    "ResearchOutcomeResolutionPostmortemLearningRow",
    "ResearchOutcomeResolutionPostmortemLearningSignal",
    "build_research_outcome_resolution_postmortem_learning_report",
    "research_outcome_resolution_postmortem_learning_report_payload",
)
