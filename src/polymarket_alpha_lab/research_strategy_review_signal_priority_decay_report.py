"""Report-only review signal priority decay scoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-review-signal-priority-decay-report"
)

REVIEW_SIGNAL_PRIORITY_DECAY_DIMENSIONS = (
    "signal_freshness",
    "evidence_strength",
    "authority",
    "movement",
    "cost_drag",
    "liquidity_quality",
    "resolution_clarity",
    "specialist_memory_confidence",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_EIGHT = Decimal("8.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_POSITIVE_DIMENSION_FIELDS = (
    (
        "signal_freshness_score",
        "review_signal_priority_decay_signal_freshness_block",
        "review_signal_priority_decay_signal_freshness_watch",
    ),
    (
        "evidence_strength_score",
        "review_signal_priority_decay_evidence_strength_block",
        "review_signal_priority_decay_evidence_strength_watch",
    ),
    (
        "authority_score",
        "review_signal_priority_decay_authority_block",
        "review_signal_priority_decay_authority_watch",
    ),
    (
        "liquidity_quality_score",
        "review_signal_priority_decay_liquidity_quality_block",
        "review_signal_priority_decay_liquidity_quality_watch",
    ),
    (
        "resolution_clarity_score",
        "review_signal_priority_decay_resolution_clarity_block",
        "review_signal_priority_decay_resolution_clarity_watch",
    ),
    (
        "specialist_memory_confidence_score",
        "review_signal_priority_decay_specialist_memory_confidence_block",
        "review_signal_priority_decay_specialist_memory_confidence_watch",
    ),
)
_ALL_INPUT_SCORE_FIELDS = tuple(
    field_name for field_name, _, _ in _POSITIVE_DIMENSION_FIELDS
) + ("movement_score", "cost_drag_score")
_ROW_REASON_CODES = (
    "review_signal_priority_decay_passed",
    "review_signal_priority_decay_signal_freshness_block",
    "review_signal_priority_decay_signal_freshness_watch",
    "review_signal_priority_decay_evidence_strength_block",
    "review_signal_priority_decay_evidence_strength_watch",
    "review_signal_priority_decay_authority_block",
    "review_signal_priority_decay_authority_watch",
    "review_signal_priority_decay_movement_block",
    "review_signal_priority_decay_movement_watch",
    "review_signal_priority_decay_cost_drag_block",
    "review_signal_priority_decay_cost_drag_watch",
    "review_signal_priority_decay_liquidity_quality_block",
    "review_signal_priority_decay_liquidity_quality_watch",
    "review_signal_priority_decay_resolution_clarity_block",
    "review_signal_priority_decay_resolution_clarity_watch",
    "review_signal_priority_decay_specialist_memory_confidence_block",
    "review_signal_priority_decay_specialist_memory_confidence_watch",
    "review_signal_priority_decay_priority_retention_below_watch",
    "review_signal_priority_decay_priority_retention_below_pass",
)
_REPORT_REASON_CODES = (
    "review_signal_priority_decay_report_passed",
    "review_signal_priority_decay_report_empty",
    "review_signal_priority_decay_report_block_rows",
    "review_signal_priority_decay_report_watch_rows",
    "review_signal_priority_decay_report_average_below_watch",
    "review_signal_priority_decay_report_average_below_pass",
    "review_signal_priority_decay_report_movement_elevated",
    "review_signal_priority_decay_report_cost_drag_elevated",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "report_status",
    "review_item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_priority_retention_score",
    "max_priority_decay_score",
    "max_movement_score",
    "max_cost_drag_score",
    "min_signal_freshness_score",
    "min_pass_priority_score",
    "min_watch_priority_score",
    "min_pass_dimension_score",
    "min_watch_dimension_score",
    "max_pass_movement_score",
    "max_watch_movement_score",
    "max_pass_cost_drag_score",
    "max_watch_cost_drag_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "rank",
    "review_key",
    "signal_freshness_score",
    "evidence_strength_score",
    "authority_score",
    "movement_score",
    "movement_stability_score",
    "cost_drag_score",
    "cost_efficiency_score",
    "liquidity_quality_score",
    "resolution_clarity_score",
    "specialist_memory_confidence_score",
    "priority_retention_score",
    "priority_decay_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_COUNT_PAYLOAD_FIELDS = (
    "review_item_count",
    "pass_count",
    "watch_count",
    "block_count",
)
_REPORT_RATIO_PAYLOAD_FIELDS = (
    "average_priority_retention_score",
    "max_priority_decay_score",
    "max_movement_score",
    "max_cost_drag_score",
    "min_signal_freshness_score",
    "min_pass_priority_score",
    "min_watch_priority_score",
    "min_pass_dimension_score",
    "min_watch_dimension_score",
    "max_pass_movement_score",
    "max_watch_movement_score",
    "max_pass_cost_drag_score",
    "max_watch_cost_drag_score",
)
_ROW_RATIO_PAYLOAD_FIELDS = (
    "signal_freshness_score",
    "evidence_strength_score",
    "authority_score",
    "movement_score",
    "movement_stability_score",
    "cost_drag_score",
    "cost_efficiency_score",
    "liquidity_quality_score",
    "resolution_clarity_score",
    "specialist_memory_confidence_score",
    "priority_retention_score",
    "priority_decay_score",
)
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "position",
    "sizing",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION",
    "REVIEW_SIGNAL_PRIORITY_DECAY_DIMENSIONS",
    "ResearchStrategyReviewSignalPriorityDecayConfig",
    "ResearchStrategyReviewSignalPriorityDecayReport",
    "ResearchStrategyReviewSignalPriorityDecayRow",
    "ResearchStrategyReviewSignalPriorityDecaySignal",
    "build_research_strategy_review_signal_priority_decay_report",
    "research_strategy_review_signal_priority_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyReviewSignalPriorityDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION
    )
    min_pass_priority_score: Decimal = Decimal("0.800000")
    min_watch_priority_score: Decimal = Decimal("0.550000")
    min_pass_dimension_score: Decimal = Decimal("0.700000")
    min_watch_dimension_score: Decimal = Decimal("0.500000")
    max_pass_movement_score: Decimal = Decimal("0.300000")
    max_watch_movement_score: Decimal = Decimal("0.600000")
    max_pass_cost_drag_score: Decimal = Decimal("0.250000")
    max_watch_cost_drag_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyReviewSignalPriorityDecayConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyReviewSignalPriorityDecayConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_priority_score",
            "min_watch_priority_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            "max_pass_movement_score",
            "max_watch_movement_score",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyReviewSignalPriorityDecaySignal:
    review_key: str
    signal_freshness_score: Decimal
    evidence_strength_score: Decimal
    authority_score: Decimal
    movement_score: Decimal
    cost_drag_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyReviewSignalPriorityDecaySignal:
            raise ValueError(
                "signal must be exactly ResearchStrategyReviewSignalPriorityDecaySignal",
            )
        object.__setattr__(
            self,
            "review_key",
            _require_public_identifier("review_key", self.review_key),
        )
        for field_name in _ALL_INPUT_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class ResearchStrategyReviewSignalPriorityDecayRow:
    rank: Decimal
    review_key: str
    signal_freshness_score: Decimal
    evidence_strength_score: Decimal
    authority_score: Decimal
    movement_score: Decimal
    movement_stability_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    priority_retention_score: Decimal
    priority_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyReviewSignalPriorityDecayRow:
            raise ValueError("row must be exactly ResearchStrategyReviewSignalPriorityDecayRow")
        object.__setattr__(
            self,
            "rank",
            _require_positive_count_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "review_key",
            _require_public_identifier("review_key", self.review_key),
        )
        for field_name in _ALL_INPUT_SCORE_FIELDS + (
            "movement_stability_score",
            "cost_efficiency_score",
            "priority_retention_score",
            "priority_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyReviewSignalPriorityDecayReport:
    generated_at: datetime
    config_version: str
    report_status: str
    review_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_priority_retention_score: Decimal
    max_priority_decay_score: Decimal
    max_movement_score: Decimal
    max_cost_drag_score: Decimal
    min_signal_freshness_score: Decimal
    min_pass_priority_score: Decimal
    min_watch_priority_score: Decimal
    min_pass_dimension_score: Decimal
    min_watch_dimension_score: Decimal
    max_pass_movement_score: Decimal
    max_watch_movement_score: Decimal
    max_pass_cost_drag_score: Decimal
    max_watch_cost_drag_score: Decimal
    rows: tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyReviewSignalPriorityDecayReport:
            raise ValueError(
                "report must be exactly ResearchStrategyReviewSignalPriorityDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in (
            "review_item_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_priority_retention_score",
            "max_priority_decay_score",
            "max_movement_score",
            "max_cost_drag_score",
            "min_signal_freshness_score",
            "min_pass_priority_score",
            "min_watch_priority_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            "max_pass_movement_score",
            "max_watch_movement_score",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _digest_from_values(asdict(self)):
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchStrategyReviewSignalPriorityDecayReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_review_signal_priority_decay_report(
    review_signals: Sequence[ResearchStrategyReviewSignalPriorityDecaySignal],
    *,
    generated_at: datetime,
    config: ResearchStrategyReviewSignalPriorityDecayConfig | None = None,
) -> ResearchStrategyReviewSignalPriorityDecayReport:
    """Build a deterministic report-only review priority decay snapshot."""

    if config is None:
        config = ResearchStrategyReviewSignalPriorityDecayConfig()
    if type(config) is not ResearchStrategyReviewSignalPriorityDecayConfig:
        raise ValueError("config must be a ResearchStrategyReviewSignalPriorityDecayConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    signals = _normalize_signals(review_signals)
    rows = _build_rows(signals, config)
    item_count = _decimal_count(len(rows))
    pass_count = _decimal_count(_status_count(rows, "pass"))
    watch_count = _decimal_count(_status_count(rows, "watch"))
    block_count = _decimal_count(_status_count(rows, "block"))
    average_retention = _average(tuple(row.priority_retention_score for row in rows))
    max_decay = max((row.priority_decay_score for row in rows), default=_ZERO)
    max_movement = max((row.movement_score for row in rows), default=_ZERO)
    max_cost_drag = max((row.cost_drag_score for row in rows), default=_ZERO)
    min_freshness = min((row.signal_freshness_score for row in rows), default=_ZERO)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(
            rows=rows,
            item_count=item_count,
            average_priority_retention_score=average_retention,
            config=config,
        ),
        "review_item_count": item_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_priority_retention_score": average_retention,
        "max_priority_decay_score": max_decay,
        "max_movement_score": max_movement,
        "max_cost_drag_score": max_cost_drag,
        "min_signal_freshness_score": min_freshness,
        "min_pass_priority_score": config.min_pass_priority_score,
        "min_watch_priority_score": config.min_watch_priority_score,
        "min_pass_dimension_score": config.min_pass_dimension_score,
        "min_watch_dimension_score": config.min_watch_dimension_score,
        "max_pass_movement_score": config.max_pass_movement_score,
        "max_watch_movement_score": config.max_watch_movement_score,
        "max_pass_cost_drag_score": config.max_pass_cost_drag_score,
        "max_watch_cost_drag_score": config.max_watch_cost_drag_score,
        "rows": rows,
        "reason_codes": _report_reason_codes(
            item_count=item_count,
            block_count=block_count,
            watch_count=watch_count,
            average_priority_retention_score=average_retention,
            max_movement_score=max_movement,
            max_cost_drag_score=max_cost_drag,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _digest_from_values(values)
    return ResearchStrategyReviewSignalPriorityDecayReport(**values)


def research_strategy_review_signal_priority_decay_report_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchStrategyReviewSignalPriorityDecayReport:
        return value.payload
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload(
        "research_strategy_review_signal_priority_decay_report_payload",
        payload,
        allow_json_containers=True,
    )
    _require_sha256_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    if payload["derived_validation_digest"] != _digest_from_values(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    _validate_report_payload(payload)
    return payload


def _build_rows(
    signals: tuple[ResearchStrategyReviewSignalPriorityDecaySignal, ...],
    config: ResearchStrategyReviewSignalPriorityDecayConfig,
) -> tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...]:
    row_values = tuple(_row_values_for_signal(item, config) for item in signals)
    sorted_values = tuple(
        sorted(
            row_values,
            key=lambda item: (
                _STATUS_SORT_WEIGHT[str(item["status"])],
                item["priority_retention_score"],
                item["review_key"],
            ),
        ),
    )
    return tuple(
        ResearchStrategyReviewSignalPriorityDecayRow(
            **dict(values, rank=_decimal_count(index)),
        )
        for index, values in enumerate(sorted_values, start=1)
    )


def _row_values_for_signal(
    signal: ResearchStrategyReviewSignalPriorityDecaySignal,
    config: ResearchStrategyReviewSignalPriorityDecayConfig,
) -> dict[str, object]:
    movement_stability = _clamp_ratio(_ONE - signal.movement_score)
    cost_efficiency = _clamp_ratio(_ONE - signal.cost_drag_score)
    retention_score = _priority_retention_score(
        (
            signal.signal_freshness_score,
            signal.evidence_strength_score,
            signal.authority_score,
            movement_stability,
            cost_efficiency,
            signal.liquidity_quality_score,
            signal.resolution_clarity_score,
            signal.specialist_memory_confidence_score,
        ),
    )
    return {
        "review_key": signal.review_key,
        "signal_freshness_score": signal.signal_freshness_score,
        "evidence_strength_score": signal.evidence_strength_score,
        "authority_score": signal.authority_score,
        "movement_score": signal.movement_score,
        "movement_stability_score": movement_stability,
        "cost_drag_score": signal.cost_drag_score,
        "cost_efficiency_score": cost_efficiency,
        "liquidity_quality_score": signal.liquidity_quality_score,
        "resolution_clarity_score": signal.resolution_clarity_score,
        "specialist_memory_confidence_score": signal.specialist_memory_confidence_score,
        "priority_retention_score": retention_score,
        "priority_decay_score": _clamp_ratio(_ONE - retention_score),
        "status": _row_status(signal, retention_score, config),
        "reason_codes": _row_reason_codes(signal, retention_score, config),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _priority_retention_score(values: tuple[Decimal, ...]) -> Decimal:
    if len(values) != 8:
        raise ValueError("priority retention score requires eight dimensions")
    return _clamp_ratio(sum(values, _ZERO) / _EIGHT)


def _row_status(
    value: ResearchStrategyReviewSignalPriorityDecaySignal
    | ResearchStrategyReviewSignalPriorityDecayRow,
    retention_score: Decimal,
    config: ResearchStrategyReviewSignalPriorityDecayConfig
    | ResearchStrategyReviewSignalPriorityDecayReport,
) -> str:
    positive_scores = tuple(
        getattr(value, field_name) for field_name, _, _ in _POSITIVE_DIMENSION_FIELDS
    )
    if (
        retention_score < config.min_watch_priority_score
        or any(score < config.min_watch_dimension_score for score in positive_scores)
        or value.movement_score > config.max_watch_movement_score
        or value.cost_drag_score > config.max_watch_cost_drag_score
    ):
        return "block"
    if (
        retention_score < config.min_pass_priority_score
        or any(score < config.min_pass_dimension_score for score in positive_scores)
        or value.movement_score > config.max_pass_movement_score
        or value.cost_drag_score > config.max_pass_cost_drag_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    value: ResearchStrategyReviewSignalPriorityDecaySignal
    | ResearchStrategyReviewSignalPriorityDecayRow,
    retention_score: Decimal,
    config: ResearchStrategyReviewSignalPriorityDecayConfig
    | ResearchStrategyReviewSignalPriorityDecayReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for field_name, block_reason, watch_reason in _POSITIVE_DIMENSION_FIELDS:
        score = getattr(value, field_name)
        if score < config.min_watch_dimension_score:
            reason_codes.append(block_reason)
        elif score < config.min_pass_dimension_score:
            reason_codes.append(watch_reason)
    if value.movement_score > config.max_watch_movement_score:
        reason_codes.append("review_signal_priority_decay_movement_block")
    elif value.movement_score > config.max_pass_movement_score:
        reason_codes.append("review_signal_priority_decay_movement_watch")
    if value.cost_drag_score > config.max_watch_cost_drag_score:
        reason_codes.append("review_signal_priority_decay_cost_drag_block")
    elif value.cost_drag_score > config.max_pass_cost_drag_score:
        reason_codes.append("review_signal_priority_decay_cost_drag_watch")
    if retention_score < config.min_watch_priority_score:
        reason_codes.append("review_signal_priority_decay_priority_retention_below_watch")
    elif retention_score < config.min_pass_priority_score:
        reason_codes.append("review_signal_priority_decay_priority_retention_below_pass")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes or ("review_signal_priority_decay_passed",)),
        _ROW_REASON_CODES,
    )


def _report_status(
    *,
    rows: tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...],
    item_count: Decimal,
    average_priority_retention_score: Decimal,
    config: ResearchStrategyReviewSignalPriorityDecayConfig
    | ResearchStrategyReviewSignalPriorityDecayReport,
) -> str:
    if (
        item_count == _ZERO
        or any(row.status == "block" for row in rows)
        or average_priority_retention_score < config.min_watch_priority_score
    ):
        return "block"
    if (
        any(row.status == "watch" for row in rows)
        or average_priority_retention_score < config.min_pass_priority_score
    ):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    item_count: Decimal,
    block_count: Decimal,
    watch_count: Decimal,
    average_priority_retention_score: Decimal,
    max_movement_score: Decimal,
    max_cost_drag_score: Decimal,
    config: ResearchStrategyReviewSignalPriorityDecayConfig
    | ResearchStrategyReviewSignalPriorityDecayReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item_count == _ZERO:
        reason_codes.append("review_signal_priority_decay_report_empty")
    if block_count > _ZERO:
        reason_codes.append("review_signal_priority_decay_report_block_rows")
    if watch_count > _ZERO:
        reason_codes.append("review_signal_priority_decay_report_watch_rows")
    if average_priority_retention_score < config.min_watch_priority_score:
        reason_codes.append("review_signal_priority_decay_report_average_below_watch")
    elif average_priority_retention_score < config.min_pass_priority_score:
        reason_codes.append("review_signal_priority_decay_report_average_below_pass")
    if item_count > _ZERO and max_movement_score > config.max_pass_movement_score:
        reason_codes.append("review_signal_priority_decay_report_movement_elevated")
    if item_count > _ZERO and max_cost_drag_score > config.max_pass_cost_drag_score:
        reason_codes.append("review_signal_priority_decay_report_cost_drag_elevated")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes or ("review_signal_priority_decay_report_passed",)),
        _REPORT_REASON_CODES,
    )


def _status_count(
    rows: tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _validate_config(config: ResearchStrategyReviewSignalPriorityDecayConfig) -> None:
    if config.min_watch_priority_score > config.min_pass_priority_score:
        raise ValueError("min_watch_priority_score must not exceed min_pass_priority_score")
    if config.min_watch_dimension_score > config.min_pass_dimension_score:
        raise ValueError("min_watch_dimension_score must not exceed min_pass_dimension_score")
    if config.max_pass_movement_score > config.max_watch_movement_score:
        raise ValueError("max_pass_movement_score must not exceed max_watch_movement_score")
    if config.max_pass_cost_drag_score > config.max_watch_cost_drag_score:
        raise ValueError("max_pass_cost_drag_score must not exceed max_watch_cost_drag_score")


def _validate_row_consistency(row: ResearchStrategyReviewSignalPriorityDecayRow) -> None:
    expected_movement_stability = _clamp_ratio(_ONE - row.movement_score)
    if row.movement_stability_score != expected_movement_stability:
        raise ValueError("movement_stability_score must match movement_score")
    expected_cost_efficiency = _clamp_ratio(_ONE - row.cost_drag_score)
    if row.cost_efficiency_score != expected_cost_efficiency:
        raise ValueError("cost_efficiency_score must match cost_drag_score")
    expected_retention = _priority_retention_score(
        (
            row.signal_freshness_score,
            row.evidence_strength_score,
            row.authority_score,
            row.movement_stability_score,
            row.cost_efficiency_score,
            row.liquidity_quality_score,
            row.resolution_clarity_score,
            row.specialist_memory_confidence_score,
        ),
    )
    if row.priority_retention_score != expected_retention:
        raise ValueError("priority_retention_score must match dimension scores")
    if row.priority_decay_score != _clamp_ratio(_ONE - row.priority_retention_score):
        raise ValueError("priority_decay_score must match priority_retention_score")


def _validate_report_consistency(
    report: ResearchStrategyReviewSignalPriorityDecayReport,
) -> None:
    rows = report.rows
    if report.review_item_count != _decimal_count(len(rows)):
        raise ValueError("review_item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_priority_retention_score != _average(
        tuple(row.priority_retention_score for row in rows),
    ):
        raise ValueError("average_priority_retention_score must match rows")
    if report.max_priority_decay_score != max(
        (row.priority_decay_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_priority_decay_score must match rows")
    if report.max_movement_score != max((row.movement_score for row in rows), default=_ZERO):
        raise ValueError("max_movement_score must match rows")
    if report.max_cost_drag_score != max((row.cost_drag_score for row in rows), default=_ZERO):
        raise ValueError("max_cost_drag_score must match rows")
    if report.min_signal_freshness_score != min(
        (row.signal_freshness_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_signal_freshness_score must match rows")
    _validate_rows_sorted(rows)
    _validate_rows_against_report(rows, report)
    if report.report_status != _report_status(
        rows=rows,
        item_count=report.review_item_count,
        average_priority_retention_score=report.average_priority_retention_score,
        config=report,
    ):
        raise ValueError("report_status must match report fields")
    if report.reason_codes != _report_reason_codes(
        item_count=report.review_item_count,
        block_count=report.block_count,
        watch_count=report.watch_count,
        average_priority_retention_score=report.average_priority_retention_score,
        max_movement_score=report.max_movement_score,
        max_cost_drag_score=report.max_cost_drag_score,
        config=report,
    ):
        raise ValueError("reason_codes must match report fields")


def _validate_rows_sorted(
    rows: tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...],
) -> None:
    expected_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_SORT_WEIGHT[row.status],
                row.priority_retention_score,
                row.review_key,
            ),
        ),
    )
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected_rows or tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use deterministic sorting and rank")


def _validate_rows_against_report(
    rows: tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...],
    report: ResearchStrategyReviewSignalPriorityDecayReport,
) -> None:
    for row in rows:
        if row.status != _row_status(row, row.priority_retention_score, report):
            raise ValueError("row status must match report thresholds")
        if row.reason_codes != _row_reason_codes(row, row.priority_retention_score, report):
            raise ValueError("row reason_codes must match report thresholds")


def _normalize_signals(
    value: Sequence[ResearchStrategyReviewSignalPriorityDecaySignal],
) -> tuple[ResearchStrategyReviewSignalPriorityDecaySignal, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("review_signals must be a sequence")
    signals = tuple(value)
    seen: set[str] = set()
    for item in signals:
        if type(item) is not ResearchStrategyReviewSignalPriorityDecaySignal:
            raise ValueError(
                "review_signals must contain ResearchStrategyReviewSignalPriorityDecaySignal",
            )
        _require_hard_flags("signal", item)
        if item.review_key in seen:
            raise ValueError("review_signals must not contain duplicate review_key values")
        seen.add(item.review_key)
    return tuple(sorted(signals, key=lambda item: item.review_key))


def _normalize_rows(value: object) -> tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchStrategyReviewSignalPriorityDecayRow:
            raise ValueError("rows must contain ResearchStrategyReviewSignalPriorityDecayRow")
    return value


def _validate_report_payload(payload: dict[str, object]) -> None:
    _require_payload_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    rows = _require_row_payloads(payload.get("rows"))
    values: dict[str, object] = {
        "generated_at": _datetime_from_payload(payload.get("generated_at")),
        "config_version": payload.get("config_version"),
        "report_status": _require_status("report_status", payload.get("report_status")),
        "rows": rows,
        "reason_codes": _reason_codes_from_payload(
            "reason_codes",
            payload.get("reason_codes"),
            _REPORT_REASON_CODES,
        ),
        "derived_validation_digest": payload.get("derived_validation_digest"),
        "paper_only": payload.get("paper_only"),
        "report_only": payload.get("report_only"),
        "readonly": payload.get("readonly"),
    }
    for field_name in _COUNT_PAYLOAD_FIELDS:
        values[field_name] = _decimal_from_payload_count(field_name, payload.get(field_name))
    for field_name in _REPORT_RATIO_PAYLOAD_FIELDS:
        values[field_name] = _decimal_from_payload_ratio(field_name, payload.get(field_name))

    report = ResearchStrategyReviewSignalPriorityDecayReport(**values)
    if report.payload != payload:
        raise ValueError("payload must use canonical report schema")


def _require_row_payloads(
    value: object,
) -> tuple[ResearchStrategyReviewSignalPriorityDecayRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[ResearchStrategyReviewSignalPriorityDecayRow] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain dict payloads")
        _require_payload_keys("row", item, _ROW_PAYLOAD_KEYS)
        row_values: dict[str, object] = {
            "rank": _decimal_from_payload_positive_count("rank", item.get("rank")),
            "review_key": _require_public_identifier("review_key", item.get("review_key")),
            "status": _require_status("status", item.get("status")),
            "reason_codes": _reason_codes_from_payload(
                "reason_codes",
                item.get("reason_codes"),
                _ROW_REASON_CODES,
            ),
            "paper_only": item.get("paper_only"),
            "report_only": item.get("report_only"),
            "readonly": item.get("readonly"),
        }
        for field_name in _ROW_RATIO_PAYLOAD_FIELDS:
            row_values[field_name] = _decimal_from_payload_ratio(
                field_name,
                item.get(field_name),
            )
        rows.append(ResearchStrategyReviewSignalPriorityDecayRow(**row_values))
    return tuple(rows)


def _require_payload_keys(
    label: str,
    value: dict[str, object],
    expected_keys: tuple[str, ...],
) -> None:
    if set(value) != set(expected_keys):
        raise ValueError(f"{label} keys must match report schema")


def _datetime_from_payload(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("generated_at must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at must be an ISO datetime string") from exc
    parsed = _as_utc("generated_at", parsed)
    if parsed.isoformat() != value:
        raise ValueError("generated_at must be a canonical UTC ISO datetime string")
    return parsed


def _decimal_from_payload_ratio(field_name: str, value: object) -> Decimal:
    return _require_canonical_decimal_payload(
        field_name,
        value,
        _require_ratio_decimal(field_name, _decimal_from_payload(field_name, value)),
    )


def _decimal_from_payload_count(field_name: str, value: object) -> Decimal:
    return _require_canonical_decimal_payload(
        field_name,
        value,
        _require_nonnegative_count_decimal(
            field_name,
            _decimal_from_payload(field_name, value),
        ),
    )


def _decimal_from_payload_positive_count(field_name: str, value: object) -> Decimal:
    return _require_canonical_decimal_payload(
        field_name,
        value,
        _require_positive_count_decimal(
            field_name,
            _decimal_from_payload(field_name, value),
        ),
    )


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _require_canonical_decimal_payload(
    field_name: str,
    raw_value: object,
    decimal_value: Decimal,
) -> Decimal:
    if str(decimal_value) != raw_value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return decimal_value


def _reason_codes_from_payload(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(field_name, tuple(value), allowed)
    if list(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    for item in value:
        _require_public_identifier(field_name, item)
        if item not in allowed:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if item not in normalized:
            normalized.append(item)
    return tuple(reason_code for reason_code in allowed if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True for payload")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True for payload")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True for payload")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{field_name} must be integral")
    return value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = {
        key: _json_ready(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
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
    if isinstance(value, Decimal):
        raise ValueError("Decimal payload value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string(current_path, field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(current_path, key)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) in (int, float) and type(value) is not bool:
        raise ValueError(f"unsafe public payload in {current_path}")
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
