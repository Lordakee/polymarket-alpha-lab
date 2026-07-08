"""Report-only expected-value priority snapshot for review queues."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION = (
    "research-strategy-review-queue-ev-priority-report"
)

REVIEW_QUEUE_EV_PRIORITY_DIMENSIONS = (
    "cost_adjusted_expected_value",
    "evidence_quality",
    "liquidity_reliability",
    "resolution_clarity",
    "signal_freshness",
    "specialist_memory_confidence",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_STATUS_SORT_WEIGHT = {"pass": 0, "watch": 1, "block": 2}
_DIMENSION_FIELDS = (
    (
        "cost_adjusted_expected_value_score",
        "review_queue_ev_priority_cost_adjusted_ev_block",
        "review_queue_ev_priority_cost_adjusted_ev_watch",
        "cost_adjusted_expected_value_weight",
    ),
    (
        "evidence_quality_score",
        "review_queue_ev_priority_evidence_quality_block",
        "review_queue_ev_priority_evidence_quality_watch",
        "evidence_quality_weight",
    ),
    (
        "liquidity_reliability_score",
        "review_queue_ev_priority_liquidity_reliability_block",
        "review_queue_ev_priority_liquidity_reliability_watch",
        "liquidity_reliability_weight",
    ),
    (
        "resolution_clarity_score",
        "review_queue_ev_priority_resolution_clarity_block",
        "review_queue_ev_priority_resolution_clarity_watch",
        "resolution_clarity_weight",
    ),
    (
        "signal_freshness_score",
        "review_queue_ev_priority_signal_freshness_block",
        "review_queue_ev_priority_signal_freshness_watch",
        "signal_freshness_weight",
    ),
    (
        "specialist_memory_confidence_score",
        "review_queue_ev_priority_memory_confidence_block",
        "review_queue_ev_priority_memory_confidence_watch",
        "specialist_memory_confidence_weight",
    ),
)
_SCORE_FIELDS = tuple(field_name for field_name, _, _, _ in _DIMENSION_FIELDS)
_WEIGHT_FIELDS = tuple(weight_name for _, _, _, weight_name in _DIMENSION_FIELDS)
_ROW_REASON_CODES = (
    "review_queue_ev_priority_passed",
    "review_queue_ev_priority_cost_adjusted_ev_block",
    "review_queue_ev_priority_cost_adjusted_ev_watch",
    "review_queue_ev_priority_evidence_quality_block",
    "review_queue_ev_priority_evidence_quality_watch",
    "review_queue_ev_priority_liquidity_reliability_block",
    "review_queue_ev_priority_liquidity_reliability_watch",
    "review_queue_ev_priority_resolution_clarity_block",
    "review_queue_ev_priority_resolution_clarity_watch",
    "review_queue_ev_priority_signal_freshness_block",
    "review_queue_ev_priority_signal_freshness_watch",
    "review_queue_ev_priority_memory_confidence_block",
    "review_queue_ev_priority_memory_confidence_watch",
    "review_queue_ev_priority_score_below_watch",
    "review_queue_ev_priority_score_below_pass",
)
_REPORT_REASON_CODES = (
    "review_queue_ev_priority_report_passed",
    "review_queue_ev_priority_report_empty",
    "review_queue_ev_priority_report_block_rows",
    "review_queue_ev_priority_report_watch_rows",
    "review_queue_ev_priority_report_average_below_watch",
    "review_queue_ev_priority_report_average_below_pass",
    "review_queue_ev_priority_report_low_dimension_floor",
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
    "DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION",
    "REVIEW_QUEUE_EV_PRIORITY_DIMENSIONS",
    "ResearchStrategyReviewQueueEvPriorityConfig",
    "ResearchStrategyReviewQueueEvPriorityItem",
    "ResearchStrategyReviewQueueEvPriorityReport",
    "ResearchStrategyReviewQueueEvPriorityRow",
    "build_research_strategy_review_queue_ev_priority_report",
    "research_strategy_review_queue_ev_priority_report_digest",
    "research_strategy_review_queue_ev_priority_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyReviewQueueEvPriorityConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION
    min_pass_priority_score: Decimal = Decimal("0.750000")
    min_watch_priority_score: Decimal = Decimal("0.500000")
    min_pass_dimension_score: Decimal = Decimal("0.700000")
    min_watch_dimension_score: Decimal = Decimal("0.400000")
    cost_adjusted_expected_value_weight: Decimal = Decimal("0.300000")
    evidence_quality_weight: Decimal = Decimal("0.175000")
    liquidity_reliability_weight: Decimal = Decimal("0.150000")
    resolution_clarity_weight: Decimal = Decimal("0.125000")
    signal_freshness_weight: Decimal = Decimal("0.125000")
    specialist_memory_confidence_weight: Decimal = Decimal("0.125000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewQueueEvPriorityConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_priority_score",
            "min_watch_priority_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            *_WEIGHT_FIELDS,
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
class ResearchStrategyReviewQueueEvPriorityItem:
    review_key: str
    cost_adjusted_expected_value_score: Decimal
    evidence_quality_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_clarity_score: Decimal
    signal_freshness_score: Decimal
    specialist_memory_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewQueueEvPriorityItem, "item")
        object.__setattr__(
            self,
            "review_key",
            _require_public_identifier("review_key", self.review_key),
        )
        for field_name in _SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("item", self)
        _reject_unsafe_public_payload("item", self)


@dataclass(frozen=True)
class ResearchStrategyReviewQueueEvPriorityRow:
    rank: Decimal
    review_key: str
    cost_adjusted_expected_value_score: Decimal
    evidence_quality_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_clarity_score: Decimal
    signal_freshness_score: Decimal
    specialist_memory_confidence_score: Decimal
    priority_score: Decimal
    lowest_dimension_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_config: InitVar[ResearchStrategyReviewQueueEvPriorityConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: ResearchStrategyReviewQueueEvPriorityConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyReviewQueueEvPriorityRow, "row")
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
        for field_name in (*_SCORE_FIELDS, "priority_score", "lowest_dimension_score"):
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
        if validation_config is None:
            validation_config = ResearchStrategyReviewQueueEvPriorityConfig()
        if type(validation_config) is not ResearchStrategyReviewQueueEvPriorityConfig:
            raise ValueError(
                "validation_config must be a ResearchStrategyReviewQueueEvPriorityConfig",
            )
        _require_hard_flags("validation_config", validation_config)
        _validate_row_consistency(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyReviewQueueEvPriorityReport:
    generated_at: datetime
    config_version: str
    status: str
    review_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_priority_score: Decimal
    max_priority_score: Decimal
    min_priority_score: Decimal
    min_evidence_quality_score: Decimal
    min_liquidity_reliability_score: Decimal
    min_resolution_clarity_score: Decimal
    min_signal_freshness_score: Decimal
    min_specialist_memory_confidence_score: Decimal
    min_pass_priority_score: Decimal
    min_watch_priority_score: Decimal
    min_pass_dimension_score: Decimal
    min_watch_dimension_score: Decimal
    rows: tuple[ResearchStrategyReviewQueueEvPriorityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewQueueEvPriorityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
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
            "average_priority_score",
            "max_priority_score",
            "min_priority_score",
            "min_evidence_quality_score",
            "min_liquidity_reliability_score",
            "min_resolution_clarity_score",
            "min_signal_freshness_score",
            "min_specialist_memory_confidence_score",
            "min_pass_priority_score",
            "min_watch_priority_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
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
            "ResearchStrategyReviewQueueEvPriorityReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_review_queue_ev_priority_report(
    review_items: Iterable[ResearchStrategyReviewQueueEvPriorityItem],
    *,
    generated_at: datetime,
    config: ResearchStrategyReviewQueueEvPriorityConfig | None = None,
) -> ResearchStrategyReviewQueueEvPriorityReport:
    """Build a deterministic review-queue priority report without action guidance."""

    if config is None:
        config = ResearchStrategyReviewQueueEvPriorityConfig()
    if type(config) is not ResearchStrategyReviewQueueEvPriorityConfig:
        raise ValueError("config must be a ResearchStrategyReviewQueueEvPriorityConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_items(review_items)
    rows = _build_rows(items, config)
    item_count = _decimal_count(len(rows))
    pass_count = _decimal_count(_status_count(rows, "pass"))
    watch_count = _decimal_count(_status_count(rows, "watch"))
    block_count = _decimal_count(_status_count(rows, "block"))
    priority_scores = tuple(row.priority_score for row in rows)
    average_priority_score = _average(priority_scores)
    min_priority_score = min(priority_scores, default=_ZERO)
    max_priority_score = max(priority_scores, default=_ZERO)
    min_dimension_score = min((row.lowest_dimension_score for row in rows), default=_ZERO)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(
            rows=rows,
            item_count=item_count,
            average_priority_score=average_priority_score,
            config=config,
        ),
        "review_item_count": item_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_priority_score": average_priority_score,
        "max_priority_score": max_priority_score,
        "min_priority_score": min_priority_score,
        "min_evidence_quality_score": _min_row_score(rows, "evidence_quality_score"),
        "min_liquidity_reliability_score": _min_row_score(
            rows,
            "liquidity_reliability_score",
        ),
        "min_resolution_clarity_score": _min_row_score(rows, "resolution_clarity_score"),
        "min_signal_freshness_score": _min_row_score(rows, "signal_freshness_score"),
        "min_specialist_memory_confidence_score": _min_row_score(
            rows,
            "specialist_memory_confidence_score",
        ),
        "min_pass_priority_score": config.min_pass_priority_score,
        "min_watch_priority_score": config.min_watch_priority_score,
        "min_pass_dimension_score": config.min_pass_dimension_score,
        "min_watch_dimension_score": config.min_watch_dimension_score,
        "rows": rows,
        "reason_codes": _report_reason_codes(
            item_count=item_count,
            block_count=block_count,
            watch_count=watch_count,
            average_priority_score=average_priority_score,
            min_dimension_score=min_dimension_score,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _digest_from_values(values)
    return ResearchStrategyReviewQueueEvPriorityReport(**values)


def research_strategy_review_queue_ev_priority_report_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchStrategyReviewQueueEvPriorityReport:
        return value.payload
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload(
        "research_strategy_review_queue_ev_priority_report_payload",
        payload,
        allow_json_containers=True,
    )
    _require_sha256_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    if payload["derived_validation_digest"] != _digest_from_values(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    return payload


def research_strategy_review_queue_ev_priority_report_digest(value: object) -> str:
    return str(
        research_strategy_review_queue_ev_priority_report_payload(value)[
            "derived_validation_digest"
        ],
    )


def _build_rows(
    items: tuple[ResearchStrategyReviewQueueEvPriorityItem, ...],
    config: ResearchStrategyReviewQueueEvPriorityConfig,
) -> tuple[ResearchStrategyReviewQueueEvPriorityRow, ...]:
    row_values = tuple(_row_values_for_item(item, config) for item in items)
    sorted_values = tuple(
        sorted(
            row_values,
            key=lambda item: (
                -_object_decimal(item["priority_score"]),
                _STATUS_SORT_WEIGHT[str(item["status"])],
                str(item["review_key"]),
            ),
        ),
    )
    return tuple(
        ResearchStrategyReviewQueueEvPriorityRow(
            **dict(values, rank=_decimal_count(index)),
            validation_config=config,
        )
        for index, values in enumerate(sorted_values, start=1)
    )


def _row_values_for_item(
    item: ResearchStrategyReviewQueueEvPriorityItem,
    config: ResearchStrategyReviewQueueEvPriorityConfig,
) -> dict[str, object]:
    priority_score = _priority_score(item, config)
    lowest_dimension_score = min(getattr(item, field_name) for field_name in _SCORE_FIELDS)
    status = _row_status(item, priority_score, config)
    return {
        "review_key": item.review_key,
        "cost_adjusted_expected_value_score": item.cost_adjusted_expected_value_score,
        "evidence_quality_score": item.evidence_quality_score,
        "liquidity_reliability_score": item.liquidity_reliability_score,
        "resolution_clarity_score": item.resolution_clarity_score,
        "signal_freshness_score": item.signal_freshness_score,
        "specialist_memory_confidence_score": item.specialist_memory_confidence_score,
        "priority_score": priority_score,
        "lowest_dimension_score": lowest_dimension_score,
        "status": status,
        "reason_codes": _row_reason_codes(item, priority_score, status, config),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _priority_score(
    value: ResearchStrategyReviewQueueEvPriorityItem
    | ResearchStrategyReviewQueueEvPriorityRow,
    config: ResearchStrategyReviewQueueEvPriorityConfig,
) -> Decimal:
    total = _ZERO
    for field_name, _, _, weight_name in _DIMENSION_FIELDS:
        total += getattr(value, field_name) * getattr(config, weight_name)
    return _clamp_ratio(total)


def _row_status(
    value: ResearchStrategyReviewQueueEvPriorityItem
    | ResearchStrategyReviewQueueEvPriorityRow,
    priority_score: Decimal,
    config: ResearchStrategyReviewQueueEvPriorityConfig
    | ResearchStrategyReviewQueueEvPriorityReport,
) -> str:
    dimension_scores = tuple(getattr(value, field_name) for field_name in _SCORE_FIELDS)
    if (
        priority_score < config.min_watch_priority_score
        or any(score < config.min_watch_dimension_score for score in dimension_scores)
    ):
        return "block"
    if (
        priority_score < config.min_pass_priority_score
        or any(score < config.min_pass_dimension_score for score in dimension_scores)
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    value: ResearchStrategyReviewQueueEvPriorityItem
    | ResearchStrategyReviewQueueEvPriorityRow,
    priority_score: Decimal,
    status: str,
    config: ResearchStrategyReviewQueueEvPriorityConfig
    | ResearchStrategyReviewQueueEvPriorityReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "block":
        for field_name, block_reason, _, _ in _DIMENSION_FIELDS:
            if getattr(value, field_name) < config.min_watch_dimension_score:
                reason_codes.append(block_reason)
        if priority_score < config.min_watch_priority_score:
            reason_codes.append("review_queue_ev_priority_score_below_watch")
    elif status == "watch":
        for field_name, _, watch_reason, _ in _DIMENSION_FIELDS:
            if getattr(value, field_name) < config.min_pass_dimension_score:
                reason_codes.append(watch_reason)
        if priority_score < config.min_pass_priority_score:
            reason_codes.append("review_queue_ev_priority_score_below_pass")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes or ("review_queue_ev_priority_passed",)),
        _ROW_REASON_CODES,
    )


def _report_status(
    *,
    rows: tuple[ResearchStrategyReviewQueueEvPriorityRow, ...],
    item_count: Decimal,
    average_priority_score: Decimal,
    config: ResearchStrategyReviewQueueEvPriorityConfig
    | ResearchStrategyReviewQueueEvPriorityReport,
) -> str:
    if (
        item_count == _ZERO
        or any(row.status == "block" for row in rows)
        or average_priority_score < config.min_watch_priority_score
    ):
        return "block"
    if (
        any(row.status == "watch" for row in rows)
        or average_priority_score < config.min_pass_priority_score
    ):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    item_count: Decimal,
    block_count: Decimal,
    watch_count: Decimal,
    average_priority_score: Decimal,
    min_dimension_score: Decimal,
    config: ResearchStrategyReviewQueueEvPriorityConfig
    | ResearchStrategyReviewQueueEvPriorityReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item_count == _ZERO:
        reason_codes.append("review_queue_ev_priority_report_empty")
    if block_count > _ZERO:
        reason_codes.append("review_queue_ev_priority_report_block_rows")
    if watch_count > _ZERO:
        reason_codes.append("review_queue_ev_priority_report_watch_rows")
    if average_priority_score < config.min_watch_priority_score:
        reason_codes.append("review_queue_ev_priority_report_average_below_watch")
    elif average_priority_score < config.min_pass_priority_score:
        reason_codes.append("review_queue_ev_priority_report_average_below_pass")
    if item_count > _ZERO and min_dimension_score < config.min_pass_dimension_score:
        reason_codes.append("review_queue_ev_priority_report_low_dimension_floor")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes or ("review_queue_ev_priority_report_passed",)),
        _REPORT_REASON_CODES,
    )


def _status_count(
    rows: tuple[ResearchStrategyReviewQueueEvPriorityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _min_row_score(
    rows: tuple[ResearchStrategyReviewQueueEvPriorityRow, ...],
    field_name: str,
) -> Decimal:
    return min((getattr(row, field_name) for row in rows), default=_ZERO)


def _validate_config(config: ResearchStrategyReviewQueueEvPriorityConfig) -> None:
    if config.min_watch_priority_score > config.min_pass_priority_score:
        raise ValueError("min_watch_priority_score must not exceed min_pass_priority_score")
    if config.min_watch_dimension_score > config.min_pass_dimension_score:
        raise ValueError("min_watch_dimension_score must not exceed min_pass_dimension_score")
    if sum((getattr(config, field_name) for field_name in _WEIGHT_FIELDS), _ZERO) != _ONE:
        raise ValueError("review queue priority weights must sum to 1")


def _validate_row_consistency(
    row: ResearchStrategyReviewQueueEvPriorityRow,
    config: ResearchStrategyReviewQueueEvPriorityConfig,
) -> None:
    expected_lowest = min(getattr(row, field_name) for field_name in _SCORE_FIELDS)
    if row.lowest_dimension_score != expected_lowest:
        raise ValueError("lowest_dimension_score must match row scores")
    expected_priority_score = _priority_score(row, config)
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match weighted row scores")
    expected_status = _row_status(row, row.priority_score, config)
    if row.status != expected_status:
        raise ValueError("status must match row scores")
    expected_reasons = _row_reason_codes(row, row.priority_score, row.status, config)
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row status")


def _validate_report_consistency(report: ResearchStrategyReviewQueueEvPriorityReport) -> None:
    rows = report.rows
    if report.review_item_count != _decimal_count(len(rows)):
        raise ValueError("review_item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    priority_scores = tuple(row.priority_score for row in rows)
    if report.average_priority_score != _average(priority_scores):
        raise ValueError("average_priority_score must match rows")
    if report.max_priority_score != max(priority_scores, default=_ZERO):
        raise ValueError("max_priority_score must match rows")
    if report.min_priority_score != min(priority_scores, default=_ZERO):
        raise ValueError("min_priority_score must match rows")
    expected_minimums = {
        "min_evidence_quality_score": _min_row_score(rows, "evidence_quality_score"),
        "min_liquidity_reliability_score": _min_row_score(
            rows,
            "liquidity_reliability_score",
        ),
        "min_resolution_clarity_score": _min_row_score(rows, "resolution_clarity_score"),
        "min_signal_freshness_score": _min_row_score(rows, "signal_freshness_score"),
        "min_specialist_memory_confidence_score": _min_row_score(
            rows,
            "specialist_memory_confidence_score",
        ),
    }
    for field_name, expected_value in expected_minimums.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _report_status(
        rows=rows,
        item_count=report.review_item_count,
        average_priority_score=report.average_priority_score,
        config=report,
    )
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    min_dimension_score = min((row.lowest_dimension_score for row in rows), default=_ZERO)
    expected_reasons = _report_reason_codes(
        item_count=report.review_item_count,
        block_count=report.block_count,
        watch_count=report.watch_count,
        average_priority_score=report.average_priority_score,
        min_dimension_score=min_dimension_score,
        config=report,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report status")


def _normalize_items(
    values: Iterable[ResearchStrategyReviewQueueEvPriorityItem],
) -> tuple[ResearchStrategyReviewQueueEvPriorityItem, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("review_items must be an iterable of review priority items")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("review_items must be an iterable of review priority items") from exc
    for item in items:
        if type(item) is not ResearchStrategyReviewQueueEvPriorityItem:
            raise ValueError(
                "review_items must contain ResearchStrategyReviewQueueEvPriorityItem",
            )
        _require_hard_flags("item", item)
    return tuple(sorted(items, key=lambda item: item.review_key))


def _normalize_rows(
    values: tuple[ResearchStrategyReviewQueueEvPriorityRow, ...],
) -> tuple[ResearchStrategyReviewQueueEvPriorityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be a tuple of priority rows")
    rows = tuple(values)
    for row in rows:
        if type(row) is not ResearchStrategyReviewQueueEvPriorityRow:
            raise ValueError("rows must contain ResearchStrategyReviewQueueEvPriorityRow")
        _require_hard_flags("row", row)
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be contiguous")
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.priority_score,
                _STATUS_SORT_WEIGHT[row.status],
                row.review_key,
            ),
        ),
    ):
        raise ValueError("rows must be sorted by priority")
    return rows


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _contains_unsafe_public_term(value):
        raise ValueError(f"{field_name} contains unsafe public identifier content")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_payload_hard_flags(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of reason codes")
    raw_values = tuple(values)
    if not raw_values:
        raise ValueError(f"{field_name} must not be empty")
    for value in raw_values:
        if type(value) is not str or value not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported reason code")
    return tuple(value for value in allowed_values if value in raw_values)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _object_decimal(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(_quantize(value))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _digest_from_values(values: object) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload = dict(payload)
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must not expose non-dict mapping payloads")
        for key, item in value.items():
            if _contains_unsafe_public_term(str(key)):
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is str and _contains_unsafe_public_term(value):
        raise ValueError(f"{label} contains unsafe public value")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)
