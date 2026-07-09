"""Report-only blocker reducer for analyst review decisions.

The report identifies evidence, source conflict, cost, liquidity, resolution,
and team readiness blockers that prevent analyst review from moving forward.
It exposes only deterministic, readonly report payloads.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION = (
    "research-strategy-review-decision-blocker-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_ANALYST_REVIEW_INPUTS_PRESENT = "analyst_review_inputs_present"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_DECISION_MEMORY_MISSING = "decision_memory_missing"
REASON_EVIDENCE_GAP_BLOCK = "evidence_gap_block"
REASON_SOURCE_CONFLICT_BLOCK = "source_conflict_block"
REASON_COST_DRAG_BLOCK = "cost_drag_block"
REASON_LIQUIDITY_RISK_BLOCK = "liquidity_risk_block"
REASON_RESOLUTION_AMBIGUITY_BLOCK = "resolution_ambiguity_block"
REASON_MEMORY_CAPACITY_BLOCK = "memory_capacity_block"
REASON_BLOCKER_PRESSURE_BLOCK = "blocker_pressure_block"
REASON_EVIDENCE_GAP_WATCH = "evidence_gap_watch"
REASON_SOURCE_CONFLICT_WATCH = "source_conflict_watch"
REASON_COST_DRAG_WATCH = "cost_drag_watch"
REASON_LIQUIDITY_RISK_WATCH = "liquidity_risk_watch"
REASON_RESOLUTION_AMBIGUITY_WATCH = "resolution_ambiguity_watch"
REASON_MEMORY_CAPACITY_WATCH = "memory_capacity_watch"
REASON_BLOCKER_PRESSURE_WATCH = "blocker_pressure_watch"
REASON_ANALYST_REVIEW_READY_PASS = "analyst_review_ready_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_ANALYST_REVIEW_INPUTS_PRESENT,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_DECISION_MEMORY_MISSING,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_GAP_BLOCK,
    REASON_SOURCE_CONFLICT_BLOCK,
    REASON_COST_DRAG_BLOCK,
    REASON_LIQUIDITY_RISK_BLOCK,
    REASON_RESOLUTION_AMBIGUITY_BLOCK,
    REASON_MEMORY_CAPACITY_BLOCK,
    REASON_BLOCKER_PRESSURE_BLOCK,
    REASON_EVIDENCE_GAP_WATCH,
    REASON_SOURCE_CONFLICT_WATCH,
    REASON_COST_DRAG_WATCH,
    REASON_LIQUIDITY_RISK_WATCH,
    REASON_RESOLUTION_AMBIGUITY_WATCH,
    REASON_MEMORY_CAPACITY_WATCH,
    REASON_BLOCKER_PRESSURE_WATCH,
    REASON_ANALYST_REVIEW_READY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_GAP_BLOCK,
        REASON_SOURCE_CONFLICT_BLOCK,
        REASON_COST_DRAG_BLOCK,
        REASON_LIQUIDITY_RISK_BLOCK,
        REASON_RESOLUTION_AMBIGUITY_BLOCK,
        REASON_MEMORY_CAPACITY_BLOCK,
        REASON_BLOCKER_PRESSURE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "sizing",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "raw-candidate",
    "market-slug",
    "market id",
    "market_id",
    "market slug",
    "market_slug",
    "question=",
    "source_url",
    "source text",
    "source_text",
    "dsn",
    "database table",
    "token",
    "wallet",
    "auth",
    "order=",
    "trade=",
    "sizing",
    "private key",
    "http://",
    "https://",
    "://",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION",
    "ResearchStrategyReviewDecisionBlockerConfig",
    "ResearchStrategyReviewDecisionBlockerInput",
    "ResearchStrategyReviewDecisionBlockerReasonCodeCount",
    "ResearchStrategyReviewDecisionBlockerReport",
    "ResearchStrategyReviewDecisionBlockerRow",
    "build_research_strategy_review_decision_blocker_report",
    "research_strategy_review_decision_blocker_report_payload",
)


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
class ResearchStrategyReviewDecisionBlockerConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION
    )
    watch_blocker_pressure: Decimal = Decimal("0.250000")
    block_blocker_pressure: Decimal = Decimal("0.550000")
    watch_evidence_gap_score: Decimal = Decimal("0.250000")
    block_evidence_gap_score: Decimal = Decimal("0.600000")
    watch_source_conflict_score: Decimal = Decimal("0.250000")
    block_source_conflict_score: Decimal = Decimal("0.600000")
    watch_cost_drag_score: Decimal = Decimal("0.250000")
    block_cost_drag_score: Decimal = Decimal("0.600000")
    watch_liquidity_risk_score: Decimal = Decimal("0.250000")
    block_liquidity_risk_score: Decimal = Decimal("0.600000")
    watch_resolution_ambiguity_score: Decimal = Decimal("0.250000")
    block_resolution_ambiguity_score: Decimal = Decimal("0.600000")
    watch_memory_capacity_gap_score: Decimal = Decimal("0.250000")
    block_memory_capacity_gap_score: Decimal = Decimal("0.600000")
    evidence_gap_weight: Decimal = Decimal("0.200000")
    source_conflict_weight: Decimal = Decimal("0.200000")
    cost_drag_weight: Decimal = Decimal("0.150000")
    liquidity_risk_weight: Decimal = Decimal("0.150000")
    resolution_ambiguity_weight: Decimal = Decimal("0.150000")
    memory_capacity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewDecisionBlockerConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_blocker_pressure",
            "block_blocker_pressure",
            "watch_evidence_gap_score",
            "block_evidence_gap_score",
            "watch_source_conflict_score",
            "block_source_conflict_score",
            "watch_cost_drag_score",
            "block_cost_drag_score",
            "watch_liquidity_risk_score",
            "block_liquidity_risk_score",
            "watch_resolution_ambiguity_score",
            "block_resolution_ambiguity_score",
            "watch_memory_capacity_gap_score",
            "block_memory_capacity_gap_score",
            "evidence_gap_weight",
            "source_conflict_weight",
            "cost_drag_weight",
            "liquidity_risk_weight",
            "resolution_ambiguity_weight",
            "memory_capacity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "block_blocker_pressure",
            self.block_blocker_pressure,
            "watch_blocker_pressure",
            self.watch_blocker_pressure,
        )
        _require_threshold_order(
            "block_evidence_gap_score",
            self.block_evidence_gap_score,
            "watch_evidence_gap_score",
            self.watch_evidence_gap_score,
        )
        _require_threshold_order(
            "block_source_conflict_score",
            self.block_source_conflict_score,
            "watch_source_conflict_score",
            self.watch_source_conflict_score,
        )
        _require_threshold_order(
            "block_cost_drag_score",
            self.block_cost_drag_score,
            "watch_cost_drag_score",
            self.watch_cost_drag_score,
        )
        _require_threshold_order(
            "block_liquidity_risk_score",
            self.block_liquidity_risk_score,
            "watch_liquidity_risk_score",
            self.watch_liquidity_risk_score,
        )
        _require_threshold_order(
            "block_resolution_ambiguity_score",
            self.block_resolution_ambiguity_score,
            "watch_resolution_ambiguity_score",
            self.watch_resolution_ambiguity_score,
        )
        _require_threshold_order(
            "block_memory_capacity_gap_score",
            self.block_memory_capacity_gap_score,
            "watch_memory_capacity_gap_score",
            self.watch_memory_capacity_gap_score,
        )
        weight_sum = _quantize(
            self.evidence_gap_weight
            + self.source_conflict_weight
            + self.cost_drag_weight
            + self.liquidity_risk_weight
            + self.resolution_ambiguity_weight
            + self.memory_capacity_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("blocker weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyReviewDecisionBlockerInput(_FinalPublicDataclass):
    review_item_ref: str
    evidence_gap_score: Decimal
    source_conflict_score: Decimal
    cost_drag_score: Decimal
    liquidity_risk_score: Decimal
    resolution_ambiguity_score: Decimal
    memory_capacity_gap_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewDecisionBlockerInput, "input")
        object.__setattr__(
            self,
            "review_item_ref",
            _require_private_ref("review_item_ref", self.review_item_ref),
        )
        for field_name in (
            "evidence_gap_score",
            "source_conflict_score",
            "cost_drag_score",
            "liquidity_risk_score",
            "resolution_ambiguity_score",
            "memory_capacity_gap_score",
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
class ResearchStrategyReviewDecisionBlockerRow(_FinalPublicDataclass):
    review_item_digest: str
    evidence_gap_score: Decimal
    source_conflict_score: Decimal
    cost_drag_score: Decimal
    liquidity_risk_score: Decimal
    resolution_ambiguity_score: Decimal
    memory_capacity_gap_score: Decimal
    blocker_pressure: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyReviewDecisionBlockerConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyReviewDecisionBlockerConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyReviewDecisionBlockerRow, "row")
        object.__setattr__(
            self,
            "review_item_digest",
            _require_private_digest("review_item_digest", self.review_item_digest),
        )
        for field_name in (
            "evidence_gap_score",
            "source_conflict_score",
            "cost_drag_score",
            "liquidity_risk_score",
            "resolution_ambiguity_score",
            "memory_capacity_gap_score",
            "blocker_pressure",
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
class ResearchStrategyReviewDecisionBlockerReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReviewDecisionBlockerReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyReviewDecisionBlockerReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_blocker_pressure: Decimal
    max_blocker_pressure: Decimal
    max_evidence_gap_score: Decimal
    max_source_conflict_score: Decimal
    max_cost_drag_score: Decimal
    max_liquidity_risk_score: Decimal
    max_resolution_ambiguity_score: Decimal
    max_memory_capacity_gap_score: Decimal
    rows: tuple[ResearchStrategyReviewDecisionBlockerRow, ...]
    reason_code_counts: tuple[ResearchStrategyReviewDecisionBlockerReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewDecisionBlockerReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_blocker_pressure",
            "max_blocker_pressure",
            "max_evidence_gap_score",
            "max_source_conflict_score",
            "max_cost_drag_score",
            "max_liquidity_risk_score",
            "max_resolution_ambiguity_score",
            "max_memory_capacity_gap_score",
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
        return research_strategy_review_decision_blocker_report_payload(self)


def build_research_strategy_review_decision_blocker_report(
    inputs: Sequence[ResearchStrategyReviewDecisionBlockerInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyReviewDecisionBlockerConfig | None = None,
) -> ResearchStrategyReviewDecisionBlockerReport:
    """Build a deterministic report of blockers to analyst review progress."""

    cfg = config or ResearchStrategyReviewDecisionBlockerConfig()
    if type(cfg) is not ResearchStrategyReviewDecisionBlockerConfig:
        raise ValueError("config must be a ResearchStrategyReviewDecisionBlockerConfig")
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
            ResearchStrategyReviewDecisionBlockerReasonCodeCount(
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
        "average_blocker_pressure": _average_ratio(
            tuple(row.blocker_pressure for row in rows),
        ),
        "max_blocker_pressure": max(
            (row.blocker_pressure for row in rows),
            default=_ZERO,
        ),
        "max_evidence_gap_score": max(
            (row.evidence_gap_score for row in rows),
            default=_ZERO,
        ),
        "max_source_conflict_score": max(
            (row.source_conflict_score for row in rows),
            default=_ZERO,
        ),
        "max_cost_drag_score": max(
            (row.cost_drag_score for row in rows),
            default=_ZERO,
        ),
        "max_liquidity_risk_score": max(
            (row.liquidity_risk_score for row in rows),
            default=_ZERO,
        ),
        "max_resolution_ambiguity_score": max(
            (row.resolution_ambiguity_score for row in rows),
            default=_ZERO,
        ),
        "max_memory_capacity_gap_score": max(
            (row.memory_capacity_gap_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyReviewDecisionBlockerReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_review_decision_blocker_report_payload(
    value: ResearchStrategyReviewDecisionBlockerReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyReviewDecisionBlockerReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyReviewDecisionBlockerReport or dict",
        )
    _validate_payload_statuses(payload)
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyReviewDecisionBlockerInput,
    config: ResearchStrategyReviewDecisionBlockerConfig,
) -> ResearchStrategyReviewDecisionBlockerRow:
    blocker_pressure = _blocker_pressure(row, config)
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        evidence_gap_score=row.evidence_gap_score,
        source_conflict_score=row.source_conflict_score,
        cost_drag_score=row.cost_drag_score,
        liquidity_risk_score=row.liquidity_risk_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        memory_capacity_gap_score=row.memory_capacity_gap_score,
        blocker_pressure=blocker_pressure,
        config=config,
    )
    return ResearchStrategyReviewDecisionBlockerRow(
        review_item_digest=_private_ref_digest(row.review_item_ref),
        evidence_gap_score=row.evidence_gap_score,
        source_conflict_score=row.source_conflict_score,
        cost_drag_score=row.cost_drag_score,
        liquidity_risk_score=row.liquidity_risk_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        memory_capacity_gap_score=row.memory_capacity_gap_score,
        blocker_pressure=blocker_pressure,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _blocker_pressure(
    row: ResearchStrategyReviewDecisionBlockerInput | ResearchStrategyReviewDecisionBlockerRow,
    config: ResearchStrategyReviewDecisionBlockerConfig,
) -> Decimal:
    return _clamp_ratio(
        row.evidence_gap_score * config.evidence_gap_weight
        + row.source_conflict_score * config.source_conflict_weight
        + row.cost_drag_score * config.cost_drag_weight
        + row.liquidity_risk_score * config.liquidity_risk_weight
        + row.resolution_ambiguity_score * config.resolution_ambiguity_weight
        + row.memory_capacity_gap_score * config.memory_capacity_weight,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    evidence_gap_score: Decimal,
    source_conflict_score: Decimal,
    cost_drag_score: Decimal,
    liquidity_risk_score: Decimal,
    resolution_ambiguity_score: Decimal,
    memory_capacity_gap_score: Decimal,
    blocker_pressure: Decimal,
    config: ResearchStrategyReviewDecisionBlockerConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    _append_component_reason(
        reason_codes,
        value=evidence_gap_score,
        watch_threshold=config.watch_evidence_gap_score,
        block_threshold=config.block_evidence_gap_score,
        watch_reason=REASON_EVIDENCE_GAP_WATCH,
        block_reason=REASON_EVIDENCE_GAP_BLOCK,
    )
    _append_component_reason(
        reason_codes,
        value=source_conflict_score,
        watch_threshold=config.watch_source_conflict_score,
        block_threshold=config.block_source_conflict_score,
        watch_reason=REASON_SOURCE_CONFLICT_WATCH,
        block_reason=REASON_SOURCE_CONFLICT_BLOCK,
    )
    _append_component_reason(
        reason_codes,
        value=cost_drag_score,
        watch_threshold=config.watch_cost_drag_score,
        block_threshold=config.block_cost_drag_score,
        watch_reason=REASON_COST_DRAG_WATCH,
        block_reason=REASON_COST_DRAG_BLOCK,
    )
    _append_component_reason(
        reason_codes,
        value=liquidity_risk_score,
        watch_threshold=config.watch_liquidity_risk_score,
        block_threshold=config.block_liquidity_risk_score,
        watch_reason=REASON_LIQUIDITY_RISK_WATCH,
        block_reason=REASON_LIQUIDITY_RISK_BLOCK,
    )
    _append_component_reason(
        reason_codes,
        value=resolution_ambiguity_score,
        watch_threshold=config.watch_resolution_ambiguity_score,
        block_threshold=config.block_resolution_ambiguity_score,
        watch_reason=REASON_RESOLUTION_AMBIGUITY_WATCH,
        block_reason=REASON_RESOLUTION_AMBIGUITY_BLOCK,
    )
    _append_component_reason(
        reason_codes,
        value=memory_capacity_gap_score,
        watch_threshold=config.watch_memory_capacity_gap_score,
        block_threshold=config.block_memory_capacity_gap_score,
        watch_reason=REASON_MEMORY_CAPACITY_WATCH,
        block_reason=REASON_MEMORY_CAPACITY_BLOCK,
    )
    _append_component_reason(
        reason_codes,
        value=blocker_pressure,
        watch_threshold=config.watch_blocker_pressure,
        block_threshold=config.block_blocker_pressure,
        watch_reason=REASON_BLOCKER_PRESSURE_WATCH,
        block_reason=REASON_BLOCKER_PRESSURE_BLOCK,
    )
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_ANALYST_REVIEW_READY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _append_component_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reason_codes.append(block_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_ANALYST_REVIEW_READY_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyReviewDecisionBlockerRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(row: ResearchStrategyReviewDecisionBlockerRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), -row.blocker_pressure, row.review_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _status_count(
    rows: tuple[ResearchStrategyReviewDecisionBlockerRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_code_counts(
    rows: tuple[ResearchStrategyReviewDecisionBlockerRow, ...],
) -> tuple[ResearchStrategyReviewDecisionBlockerReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyReviewDecisionBlockerReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_row(
    row: ResearchStrategyReviewDecisionBlockerRow,
    config: ResearchStrategyReviewDecisionBlockerConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategyReviewDecisionBlockerConfig:
            raise ValueError(
                "validation_config must be a ResearchStrategyReviewDecisionBlockerConfig",
            )
        expected_pressure = _blocker_pressure(row, config)
        if row.blocker_pressure != expected_pressure:
            raise ValueError("blocker_pressure must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            evidence_gap_score=row.evidence_gap_score,
            source_conflict_score=row.source_conflict_score,
            cost_drag_score=row.cost_drag_score,
            liquidity_risk_score=row.liquidity_risk_score,
            resolution_ambiguity_score=row.resolution_ambiguity_score,
            memory_capacity_gap_score=row.memory_capacity_gap_score,
            blocker_pressure=row.blocker_pressure,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_ANALYST_REVIEW_READY_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_ANALYST_REVIEW_READY_PASS
    ):
        raise ValueError("reason_codes cannot mix pass with risk reasons")


def _validate_report(report: ResearchStrategyReviewDecisionBlockerReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_blocker_pressure != _average_ratio(
        tuple(row.blocker_pressure for row in report.rows),
    ):
        raise ValueError("average_blocker_pressure must match rows")
    if report.max_blocker_pressure != max(
        (row.blocker_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_blocker_pressure must match rows")
    _validate_report_max(
        report.max_evidence_gap_score,
        "max_evidence_gap_score",
        tuple(row.evidence_gap_score for row in report.rows),
    )
    _validate_report_max(
        report.max_source_conflict_score,
        "max_source_conflict_score",
        tuple(row.source_conflict_score for row in report.rows),
    )
    _validate_report_max(
        report.max_cost_drag_score,
        "max_cost_drag_score",
        tuple(row.cost_drag_score for row in report.rows),
    )
    _validate_report_max(
        report.max_liquidity_risk_score,
        "max_liquidity_risk_score",
        tuple(row.liquidity_risk_score for row in report.rows),
    )
    _validate_report_max(
        report.max_resolution_ambiguity_score,
        "max_resolution_ambiguity_score",
        tuple(row.resolution_ambiguity_score for row in report.rows),
    )
    _validate_report_max(
        report.max_memory_capacity_gap_score,
        "max_memory_capacity_gap_score",
        tuple(row.memory_capacity_gap_score for row in report.rows),
    )
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyReviewDecisionBlockerReasonCodeCount(
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


def _validate_report_max(
    actual: Decimal,
    field_name: str,
    values: tuple[Decimal, ...],
) -> None:
    if actual != max(values, default=_ZERO):
        raise ValueError(f"{field_name} must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyReviewDecisionBlockerInput],
) -> tuple[ResearchStrategyReviewDecisionBlockerInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyReviewDecisionBlockerInput:
            raise ValueError(
                "inputs must contain ResearchStrategyReviewDecisionBlockerInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.review_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by review item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyReviewDecisionBlockerRow, ...],
) -> tuple[ResearchStrategyReviewDecisionBlockerRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyReviewDecisionBlockerRow:
            raise ValueError("rows must contain ResearchStrategyReviewDecisionBlockerRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.review_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique review item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyReviewDecisionBlockerReasonCodeCount, ...],
) -> tuple[ResearchStrategyReviewDecisionBlockerReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyReviewDecisionBlockerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyReviewDecisionBlockerReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _UPSTREAM_REASON_CODE_SEQUENCE)
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
    if REASON_ANALYST_REVIEW_READY_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_ANALYST_REVIEW_READY_PASS,):
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


def _report_payload(report: ResearchStrategyReviewDecisionBlockerReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_blocker_pressure=report.average_blocker_pressure,
        max_blocker_pressure=report.max_blocker_pressure,
        max_evidence_gap_score=report.max_evidence_gap_score,
        max_source_conflict_score=report.max_source_conflict_score,
        max_cost_drag_score=report.max_cost_drag_score,
        max_liquidity_risk_score=report.max_liquidity_risk_score,
        max_resolution_ambiguity_score=report.max_resolution_ambiguity_score,
        max_memory_capacity_gap_score=report.max_memory_capacity_gap_score,
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


def _report_digest(report: ResearchStrategyReviewDecisionBlockerReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_blocker_pressure": report.average_blocker_pressure,
            "max_blocker_pressure": report.max_blocker_pressure,
            "max_evidence_gap_score": report.max_evidence_gap_score,
            "max_source_conflict_score": report.max_source_conflict_score,
            "max_cost_drag_score": report.max_cost_drag_score,
            "max_liquidity_risk_score": report.max_liquidity_risk_score,
            "max_resolution_ambiguity_score": report.max_resolution_ambiguity_score,
            "max_memory_capacity_gap_score": report.max_memory_capacity_gap_score,
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


def _require_payload_hard_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _require_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_hard_flags(item)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
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
    raise ValueError("payload contains unsupported JSON value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _json_ready(getattr(value, field.name))
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
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
            _reject_unsafe_public_key(field.name, current_path)
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
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_value(value, current_path)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    normalized = key.casefold()
    for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(f"unsafe public field at {path}.{key}")


def _reject_unsafe_public_value(value: str, path: str) -> None:
    if _PRIVATE_DIGEST_RE.fullmatch(value) or _DIGEST_RE.fullmatch(value):
        return
    normalized = value.casefold()
    for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(f"unsafe public value at {path}")


def _require_threshold_order(
    block_name: str,
    block_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{block_name} must meet or exceed {watch_name}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_value(value, field_name)
    return value


def _require_private_ref(field_name: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a private reference string")
    if len(value) > 2048:
        raise ValueError(f"{field_name} is too long")
    return value


def _require_private_digest(field_name: str, value: str) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 private digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_reason_code(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} contains unsupported reason code")
    return value


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)
