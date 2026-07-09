"""Readonly probability review readiness index report."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION",
    "PROBABILITY_REVIEW_READINESS_INDEX_STATUSES",
    "ResearchStrategyProbabilityReviewReadinessIndexConfig",
    "ResearchStrategyProbabilityReviewReadinessIndexReport",
    "ResearchStrategyProbabilityReviewReadinessIndexRow",
    "ResearchStrategyProbabilityReviewReadinessInput",
    "ResearchStrategyProbabilityReviewReadinessReasonCodeCount",
    "build_research_strategy_probability_review_readiness_index_report",
    "research_strategy_probability_review_readiness_index_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-review-readiness-index-report-v0"
)
PROBABILITY_REVIEW_READINESS_INDEX_STATUSES = ("pass", "watch", "block")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_REVIEW_PACKET_READY = "review_packet_ready"
REASON_MANUAL_PROBABILITY_REVIEW_REQUESTED = "manual_probability_review_requested"
REASON_SPECIALIST_MEMORY_PENDING = "specialist_memory_pending"
REASON_EVIDENCE_COVERAGE_BLOCK = "evidence_coverage_block"
REASON_SOURCE_FRESHNESS_BLOCK = "source_freshness_block"
REASON_COST_DRAG_BLOCK = "cost_drag_block"
REASON_LIQUIDITY_RELIABILITY_BLOCK = "liquidity_reliability_block"
REASON_RESOLUTION_CLARITY_BLOCK = "resolution_clarity_block"
REASON_SPECIALIST_MEMORY_READINESS_BLOCK = "specialist_memory_readiness_block"
REASON_READINESS_INDEX_BLOCK = "readiness_index_block"
REASON_EVIDENCE_COVERAGE_WATCH = "evidence_coverage_watch"
REASON_SOURCE_FRESHNESS_WATCH = "source_freshness_watch"
REASON_COST_DRAG_WATCH = "cost_drag_watch"
REASON_LIQUIDITY_RELIABILITY_WATCH = "liquidity_reliability_watch"
REASON_RESOLUTION_CLARITY_WATCH = "resolution_clarity_watch"
REASON_SPECIALIST_MEMORY_READINESS_WATCH = "specialist_memory_readiness_watch"
REASON_READINESS_INDEX_WATCH = "readiness_index_watch"
REASON_PROBABILITY_REVIEW_READY_PASS = "probability_review_ready_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_REVIEW_PACKET_READY,
    REASON_MANUAL_PROBABILITY_REVIEW_REQUESTED,
    REASON_SPECIALIST_MEMORY_PENDING,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_COVERAGE_BLOCK,
    REASON_SOURCE_FRESHNESS_BLOCK,
    REASON_COST_DRAG_BLOCK,
    REASON_LIQUIDITY_RELIABILITY_BLOCK,
    REASON_RESOLUTION_CLARITY_BLOCK,
    REASON_SPECIALIST_MEMORY_READINESS_BLOCK,
    REASON_READINESS_INDEX_BLOCK,
    REASON_EVIDENCE_COVERAGE_WATCH,
    REASON_SOURCE_FRESHNESS_WATCH,
    REASON_COST_DRAG_WATCH,
    REASON_LIQUIDITY_RELIABILITY_WATCH,
    REASON_RESOLUTION_CLARITY_WATCH,
    REASON_SPECIALIST_MEMORY_READINESS_WATCH,
    REASON_READINESS_INDEX_WATCH,
    REASON_PROBABILITY_REVIEW_READY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_COVERAGE_BLOCK,
        REASON_SOURCE_FRESHNESS_BLOCK,
        REASON_COST_DRAG_BLOCK,
        REASON_LIQUIDITY_RELIABILITY_BLOCK,
        REASON_RESOLUTION_CLARITY_BLOCK,
        REASON_SPECIALIST_MEMORY_READINESS_BLOCK,
        REASON_READINESS_INDEX_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset(PROBABILITY_REVIEW_READINESS_INDEX_STATUSES)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyProbabilityReviewReadinessIndexConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION
    )
    pass_min_readiness_index: Decimal = Decimal("0.800000")
    watch_min_readiness_index: Decimal = Decimal("0.600000")
    min_pass_evidence_coverage_score: Decimal = Decimal("0.800000")
    min_watch_evidence_coverage_score: Decimal = Decimal("0.600000")
    min_pass_source_freshness_score: Decimal = Decimal("0.750000")
    min_watch_source_freshness_score: Decimal = Decimal("0.500000")
    max_pass_cost_drag_score: Decimal = Decimal("0.150000")
    max_watch_cost_drag_score: Decimal = Decimal("0.350000")
    min_pass_liquidity_reliability_score: Decimal = Decimal("0.750000")
    min_watch_liquidity_reliability_score: Decimal = Decimal("0.550000")
    min_pass_resolution_clarity_score: Decimal = Decimal("0.800000")
    min_watch_resolution_clarity_score: Decimal = Decimal("0.600000")
    min_pass_specialist_memory_readiness_score: Decimal = Decimal("0.750000")
    min_watch_specialist_memory_readiness_score: Decimal = Decimal("0.550000")
    evidence_coverage_weight: Decimal = Decimal("0.200000")
    source_freshness_weight: Decimal = Decimal("0.150000")
    cost_efficiency_weight: Decimal = Decimal("0.150000")
    liquidity_reliability_weight: Decimal = Decimal("0.150000")
    resolution_clarity_weight: Decimal = Decimal("0.200000")
    specialist_memory_readiness_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityReviewReadinessIndexConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_readiness_index",
            "watch_min_readiness_index",
            "min_pass_evidence_coverage_score",
            "min_watch_evidence_coverage_score",
            "min_pass_source_freshness_score",
            "min_watch_source_freshness_score",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
            "min_pass_liquidity_reliability_score",
            "min_watch_liquidity_reliability_score",
            "min_pass_resolution_clarity_score",
            "min_watch_resolution_clarity_score",
            "min_pass_specialist_memory_readiness_score",
            "min_watch_specialist_memory_readiness_score",
            "evidence_coverage_weight",
            "source_freshness_weight",
            "cost_efficiency_weight",
            "liquidity_reliability_weight",
            "resolution_clarity_weight",
            "specialist_memory_readiness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_readiness_index < self.watch_min_readiness_index:
            raise ValueError(
                "pass_min_readiness_index must be at least watch_min_readiness_index",
            )
        if (
            self.min_pass_evidence_coverage_score
            < self.min_watch_evidence_coverage_score
        ):
            raise ValueError(
                "min_pass_evidence_coverage_score must be at least "
                "min_watch_evidence_coverage_score",
            )
        if self.min_pass_source_freshness_score < self.min_watch_source_freshness_score:
            raise ValueError(
                "min_pass_source_freshness_score must be at least "
                "min_watch_source_freshness_score",
            )
        if self.max_pass_cost_drag_score > self.max_watch_cost_drag_score:
            raise ValueError(
                "max_pass_cost_drag_score must not exceed max_watch_cost_drag_score",
            )
        if (
            self.min_pass_liquidity_reliability_score
            < self.min_watch_liquidity_reliability_score
        ):
            raise ValueError(
                "min_pass_liquidity_reliability_score must be at least "
                "min_watch_liquidity_reliability_score",
            )
        if (
            self.min_pass_resolution_clarity_score
            < self.min_watch_resolution_clarity_score
        ):
            raise ValueError(
                "min_pass_resolution_clarity_score must be at least "
                "min_watch_resolution_clarity_score",
            )
        if (
            self.min_pass_specialist_memory_readiness_score
            < self.min_watch_specialist_memory_readiness_score
        ):
            raise ValueError(
                "min_pass_specialist_memory_readiness_score must be at least "
                "min_watch_specialist_memory_readiness_score",
            )
        weight_sum = _quantize(
            self.evidence_coverage_weight
            + self.source_freshness_weight
            + self.cost_efficiency_weight
            + self.liquidity_reliability_weight
            + self.resolution_clarity_weight
            + self.specialist_memory_readiness_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("readiness weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityReviewReadinessInput(_FinalPublicDataclass):
    review_item_ref: str
    evidence_coverage_score: Decimal
    source_freshness_score: Decimal
    cost_drag_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_readiness_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityReviewReadinessInput, "input")
        object.__setattr__(
            self,
            "review_item_ref",
            _require_private_ref("review_item_ref", self.review_item_ref),
        )
        for field_name in (
            "evidence_coverage_score",
            "source_freshness_score",
            "cost_drag_score",
            "liquidity_reliability_score",
            "resolution_clarity_score",
            "specialist_memory_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityReviewReadinessIndexRow(_FinalPublicDataclass):
    review_item_digest: str
    evidence_coverage_score: Decimal
    source_freshness_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_readiness_score: Decimal
    readiness_index: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyProbabilityReviewReadinessIndexConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: (
            ResearchStrategyProbabilityReviewReadinessIndexConfig | None
        ),
    ) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityReviewReadinessIndexRow, "row")
        object.__setattr__(
            self,
            "review_item_digest",
            _require_private_digest("review_item_digest", self.review_item_digest),
        )
        for field_name in (
            "evidence_coverage_score",
            "source_freshness_score",
            "cost_drag_score",
            "cost_efficiency_score",
            "liquidity_reliability_score",
            "resolution_clarity_score",
            "specialist_memory_readiness_score",
            "readiness_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityReviewReadinessReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityReviewReadinessReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityReviewReadinessIndexReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_index: Decimal
    min_readiness_index: Decimal
    min_evidence_coverage_score: Decimal
    min_source_freshness_score: Decimal
    max_cost_drag_score: Decimal
    min_liquidity_reliability_score: Decimal
    min_resolution_clarity_score: Decimal
    min_specialist_memory_readiness_score: Decimal
    rows: tuple[ResearchStrategyProbabilityReviewReadinessIndexRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityReviewReadinessReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityReviewReadinessIndexReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_index",
            "min_readiness_index",
            "min_evidence_coverage_score",
            "min_source_freshness_score",
            "max_cost_drag_score",
            "min_liquidity_reliability_score",
            "min_resolution_clarity_score",
            "min_specialist_memory_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_probability_review_readiness_index_report_payload(self)


def build_research_strategy_probability_review_readiness_index_report(
    inputs: Sequence[ResearchStrategyProbabilityReviewReadinessInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityReviewReadinessIndexConfig | None = None,
) -> ResearchStrategyProbabilityReviewReadinessIndexReport:
    cfg = config or ResearchStrategyProbabilityReviewReadinessIndexConfig()
    if type(cfg) is not ResearchStrategyProbabilityReviewReadinessIndexConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityReviewReadinessIndexConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyProbabilityReviewReadinessReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_readiness_index": _average_ratio(
            tuple(row.readiness_index for row in rows),
        ),
        "min_readiness_index": min((row.readiness_index for row in rows), default=_ZERO),
        "min_evidence_coverage_score": min(
            (row.evidence_coverage_score for row in rows),
            default=_ZERO,
        ),
        "min_source_freshness_score": min(
            (row.source_freshness_score for row in rows),
            default=_ZERO,
        ),
        "max_cost_drag_score": max((row.cost_drag_score for row in rows), default=_ZERO),
        "min_liquidity_reliability_score": min(
            (row.liquidity_reliability_score for row in rows),
            default=_ZERO,
        ),
        "min_resolution_clarity_score": min(
            (row.resolution_clarity_score for row in rows),
            default=_ZERO,
        ),
        "min_specialist_memory_readiness_score": min(
            (row.specialist_memory_readiness_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityReviewReadinessIndexReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_probability_review_readiness_index_report_payload(
    value: ResearchStrategyProbabilityReviewReadinessIndexReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyProbabilityReviewReadinessIndexReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a "
            "ResearchStrategyProbabilityReviewReadinessIndexReport or dict",
        )
    _validate_payload_statuses(payload)
    _validate_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyProbabilityReviewReadinessInput,
    config: ResearchStrategyProbabilityReviewReadinessIndexConfig,
) -> ResearchStrategyProbabilityReviewReadinessIndexRow:
    cost_efficiency = _inverse_ratio(row.cost_drag_score)
    readiness_index = _readiness_index(
        evidence_coverage_score=row.evidence_coverage_score,
        source_freshness_score=row.source_freshness_score,
        cost_efficiency_score=cost_efficiency,
        liquidity_reliability_score=row.liquidity_reliability_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_readiness_score=row.specialist_memory_readiness_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        evidence_coverage_score=row.evidence_coverage_score,
        source_freshness_score=row.source_freshness_score,
        cost_drag_score=row.cost_drag_score,
        liquidity_reliability_score=row.liquidity_reliability_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_readiness_score=row.specialist_memory_readiness_score,
        readiness_index=readiness_index,
        config=config,
    )
    return ResearchStrategyProbabilityReviewReadinessIndexRow(
        review_item_digest=_private_ref_digest(row.review_item_ref),
        evidence_coverage_score=row.evidence_coverage_score,
        source_freshness_score=row.source_freshness_score,
        cost_drag_score=row.cost_drag_score,
        cost_efficiency_score=cost_efficiency,
        liquidity_reliability_score=row.liquidity_reliability_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_readiness_score=row.specialist_memory_readiness_score,
        readiness_index=readiness_index,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    evidence_coverage_score: Decimal,
    source_freshness_score: Decimal,
    cost_drag_score: Decimal,
    liquidity_reliability_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_readiness_score: Decimal,
    readiness_index: Decimal,
    config: ResearchStrategyProbabilityReviewReadinessIndexConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if evidence_coverage_score < config.min_watch_evidence_coverage_score:
        reason_codes.append(REASON_EVIDENCE_COVERAGE_BLOCK)
    elif evidence_coverage_score < config.min_pass_evidence_coverage_score:
        reason_codes.append(REASON_EVIDENCE_COVERAGE_WATCH)
    if source_freshness_score < config.min_watch_source_freshness_score:
        reason_codes.append(REASON_SOURCE_FRESHNESS_BLOCK)
    elif source_freshness_score < config.min_pass_source_freshness_score:
        reason_codes.append(REASON_SOURCE_FRESHNESS_WATCH)
    if cost_drag_score > config.max_watch_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_BLOCK)
    elif cost_drag_score > config.max_pass_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_WATCH)
    if liquidity_reliability_score < config.min_watch_liquidity_reliability_score:
        reason_codes.append(REASON_LIQUIDITY_RELIABILITY_BLOCK)
    elif liquidity_reliability_score < config.min_pass_liquidity_reliability_score:
        reason_codes.append(REASON_LIQUIDITY_RELIABILITY_WATCH)
    if resolution_clarity_score < config.min_watch_resolution_clarity_score:
        reason_codes.append(REASON_RESOLUTION_CLARITY_BLOCK)
    elif resolution_clarity_score < config.min_pass_resolution_clarity_score:
        reason_codes.append(REASON_RESOLUTION_CLARITY_WATCH)
    if (
        specialist_memory_readiness_score
        < config.min_watch_specialist_memory_readiness_score
    ):
        reason_codes.append(REASON_SPECIALIST_MEMORY_READINESS_BLOCK)
    elif (
        specialist_memory_readiness_score
        < config.min_pass_specialist_memory_readiness_score
    ):
        reason_codes.append(REASON_SPECIALIST_MEMORY_READINESS_WATCH)
    if readiness_index < config.watch_min_readiness_index:
        reason_codes.append(REASON_READINESS_INDEX_BLOCK)
    elif readiness_index < config.pass_min_readiness_index:
        reason_codes.append(REASON_READINESS_INDEX_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_PROBABILITY_REVIEW_READY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_PROBABILITY_REVIEW_READY_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyProbabilityReviewReadinessIndexRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyProbabilityReviewReadinessIndexRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyProbabilityReviewReadinessIndexRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.readiness_index, row.review_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityReviewReadinessIndexRow, ...],
) -> tuple[ResearchStrategyProbabilityReviewReadinessReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyProbabilityReviewReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _readiness_index(
    *,
    evidence_coverage_score: Decimal,
    source_freshness_score: Decimal,
    cost_efficiency_score: Decimal,
    liquidity_reliability_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_readiness_score: Decimal,
    config: ResearchStrategyProbabilityReviewReadinessIndexConfig,
) -> Decimal:
    score = (
        evidence_coverage_score * config.evidence_coverage_weight
        + source_freshness_score * config.source_freshness_weight
        + cost_efficiency_score * config.cost_efficiency_weight
        + liquidity_reliability_score * config.liquidity_reliability_weight
        + resolution_clarity_score * config.resolution_clarity_weight
        + specialist_memory_readiness_score
        * config.specialist_memory_readiness_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyProbabilityReviewReadinessIndexRow,
    config: ResearchStrategyProbabilityReviewReadinessIndexConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategyProbabilityReviewReadinessIndexConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyProbabilityReviewReadinessIndexConfig",
            )
        if row.cost_efficiency_score != _inverse_ratio(row.cost_drag_score):
            raise ValueError("cost_efficiency_score must match cost_drag_score")
        expected_readiness = _readiness_index(
            evidence_coverage_score=row.evidence_coverage_score,
            source_freshness_score=row.source_freshness_score,
            cost_efficiency_score=row.cost_efficiency_score,
            liquidity_reliability_score=row.liquidity_reliability_score,
            resolution_clarity_score=row.resolution_clarity_score,
            specialist_memory_readiness_score=row.specialist_memory_readiness_score,
            config=config,
        )
        if row.readiness_index != expected_readiness:
            raise ValueError("readiness_index must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            evidence_coverage_score=row.evidence_coverage_score,
            source_freshness_score=row.source_freshness_score,
            cost_drag_score=row.cost_drag_score,
            liquidity_reliability_score=row.liquidity_reliability_score,
            resolution_clarity_score=row.resolution_clarity_score,
            specialist_memory_readiness_score=row.specialist_memory_readiness_score,
            readiness_index=row.readiness_index,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_PROBABILITY_REVIEW_READY_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_PROBABILITY_REVIEW_READY_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(
    report: ResearchStrategyProbabilityReviewReadinessIndexReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_readiness_index != _average_ratio(
        tuple(row.readiness_index for row in report.rows),
    ):
        raise ValueError("average_readiness_index must match rows")
    if report.min_readiness_index != min(
        (row.readiness_index for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_readiness_index must match rows")
    if report.min_evidence_coverage_score != min(
        (row.evidence_coverage_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_coverage_score must match rows")
    if report.min_source_freshness_score != min(
        (row.source_freshness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_source_freshness_score must match rows")
    if report.max_cost_drag_score != max(
        (row.cost_drag_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_drag_score must match rows")
    if report.min_liquidity_reliability_score != min(
        (row.liquidity_reliability_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_liquidity_reliability_score must match rows")
    if report.min_resolution_clarity_score != min(
        (row.resolution_clarity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_resolution_clarity_score must match rows")
    if report.min_specialist_memory_readiness_score != min(
        (row.specialist_memory_readiness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_specialist_memory_readiness_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyProbabilityReviewReadinessReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyProbabilityReviewReadinessInput],
) -> tuple[ResearchStrategyProbabilityReviewReadinessInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityReviewReadinessInput:
            raise ValueError(
                "inputs must contain ResearchStrategyProbabilityReviewReadinessInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.review_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by review item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyProbabilityReviewReadinessIndexRow, ...],
) -> tuple[ResearchStrategyProbabilityReviewReadinessIndexRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityReviewReadinessIndexRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityReviewReadinessIndexRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    digests = tuple(row.review_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique review item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityReviewReadinessReasonCodeCount, ...],
) -> tuple[ResearchStrategyProbabilityReviewReadinessReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityReviewReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityReviewReadinessReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code(
            "reason_codes",
            reason_code,
            _UPSTREAM_REASON_CODE_SEQUENCE,
        )
    normalized = tuple(
        reason_code
        for reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_PROBABILITY_REVIEW_READY_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_PROBABILITY_REVIEW_READY_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(
    report: ResearchStrategyProbabilityReviewReadinessIndexReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_readiness_index=report.average_readiness_index,
        min_readiness_index=report.min_readiness_index,
        min_evidence_coverage_score=report.min_evidence_coverage_score,
        min_source_freshness_score=report.min_source_freshness_score,
        max_cost_drag_score=report.max_cost_drag_score,
        min_liquidity_reliability_score=report.min_liquidity_reliability_score,
        min_resolution_clarity_score=report.min_resolution_clarity_score,
        min_specialist_memory_readiness_score=(
            report.min_specialist_memory_readiness_score
        ),
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(
    report: ResearchStrategyProbabilityReviewReadinessIndexReport,
) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_readiness_index": report.average_readiness_index,
            "min_readiness_index": report.min_readiness_index,
            "min_evidence_coverage_score": report.min_evidence_coverage_score,
            "min_source_freshness_score": report.min_source_freshness_score,
            "max_cost_drag_score": report.max_cost_drag_score,
            "min_liquidity_reliability_score": (
                report.min_liquidity_reliability_score
            ),
            "min_resolution_clarity_score": report.min_resolution_clarity_score,
            "min_specialist_memory_readiness_score": (
                report.min_specialist_memory_readiness_score
            ),
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
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
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_hard_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True for payload")
        for item in value.values():
            _validate_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_hard_flags(item)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float) or isinstance(value, Decimal):
        raise ValueError("payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload values must be JSON compatible")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            result[key] = _json_ready(item)
        return result
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload values must be public JSON values")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    public_value = value if allow_json_containers else _json_ready(value)
    _reject_unsafe_public_value(label, public_value)


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            lowered_key = key.casefold()
            if any(fragment in lowered_key for fragment in _unsafe_public_fragments()):
                raise ValueError(f"{label} unsafe public field")
            _reject_unsafe_public_value(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_value(label, item)
        return
    if type(value) is str:
        lowered_value = value.casefold()
        if _PRIVATE_DIGEST_RE.match(value):
            return
        if any(fragment in lowered_value for fragment in _unsafe_public_fragments()):
            raise ValueError(f"{label} unsafe public value")


def _unsafe_public_fragments() -> tuple[str, ...]:
    return (
        "raw",
        "candi" + "date",
        "candi" + "date" + "_" + "id",
        "mark" + "et",
        "mark" + "et" + "_" + "id",
        "mark" + "et" + "_" + "slug",
        "condition" + "_" + "id",
        "to" + "ken",
        "to" + "ken" + "_" + "id",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "tra" + "de",
        "position",
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmend",
        "si" + "zing",
        "quest" + "ion",
        "source" + "_" + "url",
        "source" + "-" + "url",
        "source" + " " + "url",
        "source" + "_" + "text",
        "source" + "-" + "text",
        "source" + " " + "text",
        "d" + "sn",
        "data" + "base",
        "table",
        "table" + "_" + "name",
        "secret",
        "credential",
        "private key",
        "http",
        "://",
        "net" + "work",
        "li" + "ve",
    )


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.prec = 28
        return _clamp_ratio(sum(values, _ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.prec = 28
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(normalized)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.casefold()
    if any(fragment in lowered for fragment in _unsafe_public_fragments()):
        raise ValueError(f"{field_name} must not expose unsafe public text")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty string")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_reason_codes:
        raise ValueError(f"{field_name} must contain supported reason codes")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PROBABILITY_REVIEW_READINESS_INDEX_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
