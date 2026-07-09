"""Report-only market memory confidence guard snapshot.

The reducer accepts caller-supplied private memory references and confidence
surfaces, then emits only deterministic redacted aggregate rows. It is
paper-only, report-only, readonly, and performs no external actions.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION = (
    "research-strategy-market-memory-confidence-guard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_MEMORY_REVIEW_READY = "memory_review_ready"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_STALENESS_REVIEW_REQUESTED = "staleness_review_requested"
REASON_CONFLICT_REVIEW_REQUESTED = "conflict_review_requested"
REASON_MEMORY_CONFIDENCE_BLOCK = "memory_confidence_block"
REASON_MEMORY_CONFIDENCE_WATCH = "memory_confidence_watch"
REASON_EVIDENCE_RECHECK_CONFIDENCE_BLOCK = "evidence_recheck_confidence_block"
REASON_EVIDENCE_RECHECK_CONFIDENCE_WATCH = "evidence_recheck_confidence_watch"
REASON_CROSS_EVIDENCE_CONSISTENCY_BLOCK = "cross_evidence_consistency_block"
REASON_CROSS_EVIDENCE_CONSISTENCY_WATCH = "cross_evidence_consistency_watch"
REASON_OUTCOME_FEEDBACK_CONFIDENCE_BLOCK = "outcome_feedback_confidence_block"
REASON_OUTCOME_FEEDBACK_CONFIDENCE_WATCH = "outcome_feedback_confidence_watch"
REASON_FRESHNESS_SUPPORT_BLOCK = "freshness_support_block"
REASON_FRESHNESS_SUPPORT_WATCH = "freshness_support_watch"
REASON_CONFLICT_SAFETY_BLOCK = "conflict_safety_block"
REASON_CONFLICT_SAFETY_WATCH = "conflict_safety_watch"
REASON_STALENESS_RISK_BLOCK = "staleness_risk_block"
REASON_STALENESS_RISK_WATCH = "staleness_risk_watch"
REASON_CONFLICT_RISK_BLOCK = "conflict_risk_block"
REASON_CONFLICT_RISK_WATCH = "conflict_risk_watch"
REASON_GUARD_SCORE_BLOCK = "guard_score_block"
REASON_GUARD_SCORE_WATCH = "guard_score_watch"
REASON_MEMORY_CONFIDENCE_GUARD_PASS = "memory_confidence_guard_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_MEMORY_REVIEW_READY,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_STALENESS_REVIEW_REQUESTED,
    REASON_CONFLICT_REVIEW_REQUESTED,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_MEMORY_CONFIDENCE_BLOCK,
    REASON_MEMORY_CONFIDENCE_WATCH,
    REASON_EVIDENCE_RECHECK_CONFIDENCE_BLOCK,
    REASON_EVIDENCE_RECHECK_CONFIDENCE_WATCH,
    REASON_CROSS_EVIDENCE_CONSISTENCY_BLOCK,
    REASON_CROSS_EVIDENCE_CONSISTENCY_WATCH,
    REASON_OUTCOME_FEEDBACK_CONFIDENCE_BLOCK,
    REASON_OUTCOME_FEEDBACK_CONFIDENCE_WATCH,
    REASON_FRESHNESS_SUPPORT_BLOCK,
    REASON_FRESHNESS_SUPPORT_WATCH,
    REASON_CONFLICT_SAFETY_BLOCK,
    REASON_CONFLICT_SAFETY_WATCH,
    REASON_STALENESS_RISK_BLOCK,
    REASON_STALENESS_RISK_WATCH,
    REASON_CONFLICT_RISK_BLOCK,
    REASON_CONFLICT_RISK_WATCH,
    REASON_GUARD_SCORE_BLOCK,
    REASON_GUARD_SCORE_WATCH,
    REASON_MEMORY_CONFIDENCE_GUARD_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REPORT_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    if reason_code.endswith("_block")
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_HEX_DIGITS = frozenset("0123456789abcdef")
_UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "api_key",
    "auth",
    "candidate",
    "database",
    "dsn",
    "market_id",
    "market_slug",
    "market_question",
    "market_url",
    "order",
    "position",
    "private_key",
    "question",
    "raw",
    "recommend",
    "secret",
    "sizing",
    "source_text",
    "source_url",
    "table",
    "text",
    "token",
    "trade",
    "url",
    "wallet",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    *_UNSAFE_PUBLIC_FIELD_FRAGMENTS,
    "://",
    "buy",
    "sell",
    "source text",
    "source-url",
    "source url",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION",
    "ResearchStrategyMarketMemoryConfidenceGuardConfig",
    "ResearchStrategyMarketMemoryConfidenceGuardInput",
    "ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount",
    "ResearchStrategyMarketMemoryConfidenceGuardReport",
    "ResearchStrategyMarketMemoryConfidenceGuardRow",
    "build_research_strategy_market_memory_confidence_guard_report",
    "research_strategy_market_memory_confidence_guard_report_digest",
    "research_strategy_market_memory_confidence_guard_report_payload",
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
class ResearchStrategyMarketMemoryConfidenceGuardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION
    )
    pass_min_guard_score: Decimal = Decimal("0.800000")
    watch_min_guard_score: Decimal = Decimal("0.600000")
    min_pass_support_score: Decimal = Decimal("0.700000")
    min_watch_support_score: Decimal = Decimal("0.500000")
    max_pass_risk_score: Decimal = Decimal("0.200000")
    max_watch_risk_score: Decimal = Decimal("0.450000")
    memory_confidence_weight: Decimal = Decimal("0.250000")
    evidence_recheck_weight: Decimal = Decimal("0.200000")
    cross_evidence_consistency_weight: Decimal = Decimal("0.200000")
    outcome_feedback_weight: Decimal = Decimal("0.150000")
    freshness_support_weight: Decimal = Decimal("0.100000")
    conflict_safety_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketMemoryConfidenceGuardConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_guard_score",
            "watch_min_guard_score",
            "min_pass_support_score",
            "min_watch_support_score",
            "max_pass_risk_score",
            "max_watch_risk_score",
            "memory_confidence_weight",
            "evidence_recheck_weight",
            "cross_evidence_consistency_weight",
            "outcome_feedback_weight",
            "freshness_support_weight",
            "conflict_safety_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_guard_score < self.watch_min_guard_score:
            raise ValueError("pass_min_guard_score must be at least watch_min_guard_score")
        if self.min_pass_support_score < self.min_watch_support_score:
            raise ValueError(
                "min_pass_support_score must be at least min_watch_support_score",
            )
        if self.max_pass_risk_score > self.max_watch_risk_score:
            raise ValueError(
                "max_pass_risk_score must not exceed max_watch_risk_score",
            )
        if _config_weight_sum(self) != _ONE:
            raise ValueError("market memory confidence guard weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyMarketMemoryConfidenceGuardInput(_FinalPublicDataclass):
    private_memory_ref: str
    memory_confidence_score: Decimal
    evidence_recheck_confidence_score: Decimal
    cross_evidence_consistency_score: Decimal
    outcome_feedback_confidence_score: Decimal
    staleness_risk_score: Decimal
    conflict_risk_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketMemoryConfidenceGuardInput, "input")
        object.__setattr__(
            self,
            "private_memory_ref",
            _require_private_ref("private_memory_ref", self.private_memory_ref),
        )
        for field_name in (
            "memory_confidence_score",
            "evidence_recheck_confidence_score",
            "cross_evidence_consistency_score",
            "outcome_feedback_confidence_score",
            "staleness_risk_score",
            "conflict_risk_score",
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
class ResearchStrategyMarketMemoryConfidenceGuardRow(_FinalPublicDataclass):
    memory_item_digest: str
    memory_confidence_score: Decimal
    evidence_recheck_confidence_score: Decimal
    cross_evidence_consistency_score: Decimal
    outcome_feedback_confidence_score: Decimal
    staleness_risk_score: Decimal
    freshness_support_score: Decimal
    conflict_risk_score: Decimal
    conflict_safety_score: Decimal
    guard_score: Decimal
    lowest_support_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyMarketMemoryConfidenceGuardConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyMarketMemoryConfidenceGuardConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyMarketMemoryConfidenceGuardRow, "row")
        object.__setattr__(
            self,
            "memory_item_digest",
            _require_private_digest("memory_item_digest", self.memory_item_digest),
        )
        for field_name in (
            "memory_confidence_score",
            "evidence_recheck_confidence_score",
            "cross_evidence_consistency_score",
            "outcome_feedback_confidence_score",
            "staleness_risk_score",
            "freshness_support_score",
            "conflict_risk_score",
            "conflict_safety_score",
            "guard_score",
            "lowest_support_score",
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
class ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
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
class ResearchStrategyMarketMemoryConfidenceGuardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_guard_score: Decimal
    min_guard_score: Decimal
    min_memory_confidence_score: Decimal
    min_evidence_recheck_confidence_score: Decimal
    min_cross_evidence_consistency_score: Decimal
    min_outcome_feedback_confidence_score: Decimal
    max_staleness_risk_score: Decimal
    max_conflict_risk_score: Decimal
    rows: tuple[ResearchStrategyMarketMemoryConfidenceGuardRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketMemoryConfidenceGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION
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
            "average_guard_score",
            "min_guard_score",
            "min_memory_confidence_score",
            "min_evidence_recheck_confidence_score",
            "min_cross_evidence_consistency_score",
            "min_outcome_feedback_confidence_score",
            "max_staleness_risk_score",
            "max_conflict_risk_score",
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
        return research_strategy_market_memory_confidence_guard_report_payload(self)


def build_research_strategy_market_memory_confidence_guard_report(
    inputs: Sequence[ResearchStrategyMarketMemoryConfidenceGuardInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig | None = None,
) -> ResearchStrategyMarketMemoryConfidenceGuardReport:
    """Build a deterministic, readonly market memory confidence guard report."""

    cfg = config or ResearchStrategyMarketMemoryConfidenceGuardConfig()
    if type(cfg) is not ResearchStrategyMarketMemoryConfidenceGuardConfig:
        raise ValueError(
            "config must be a ResearchStrategyMarketMemoryConfidenceGuardConfig",
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
    reason_codes = _normalize_report_reason_codes(
        tuple(row.reason_code for row in reason_code_counts),
    )
    if not rows:
        reason_code_counts = (
            ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount(
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
        "average_guard_score": _average_ratio(tuple(row.guard_score for row in rows)),
        "min_guard_score": min((row.guard_score for row in rows), default=_ZERO),
        "min_memory_confidence_score": min(
            (row.memory_confidence_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_recheck_confidence_score": min(
            (row.evidence_recheck_confidence_score for row in rows),
            default=_ZERO,
        ),
        "min_cross_evidence_consistency_score": min(
            (row.cross_evidence_consistency_score for row in rows),
            default=_ZERO,
        ),
        "min_outcome_feedback_confidence_score": min(
            (row.outcome_feedback_confidence_score for row in rows),
            default=_ZERO,
        ),
        "max_staleness_risk_score": max(
            (row.staleness_risk_score for row in rows),
            default=_ZERO,
        ),
        "max_conflict_risk_score": max(
            (row.conflict_risk_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyMarketMemoryConfidenceGuardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_market_memory_confidence_guard_report_payload(
    value: ResearchStrategyMarketMemoryConfidenceGuardReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyMarketMemoryConfidenceGuardReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyMarketMemoryConfidenceGuardReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_numbers(payload)
    _require_hard_flags("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_strategy_market_memory_confidence_guard_report_digest(
    report: ResearchStrategyMarketMemoryConfidenceGuardReport,
) -> str:
    if type(report) is not ResearchStrategyMarketMemoryConfidenceGuardReport:
        raise ValueError(
            "report must be a ResearchStrategyMarketMemoryConfidenceGuardReport",
        )
    return _report_digest(report)


def _row_for_input(
    row: ResearchStrategyMarketMemoryConfidenceGuardInput,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig,
) -> ResearchStrategyMarketMemoryConfidenceGuardRow:
    freshness_support_score = _inverse_ratio(row.staleness_risk_score)
    conflict_safety_score = _inverse_ratio(row.conflict_risk_score)
    guard_score = _guard_score(
        memory_confidence_score=row.memory_confidence_score,
        evidence_recheck_confidence_score=row.evidence_recheck_confidence_score,
        cross_evidence_consistency_score=row.cross_evidence_consistency_score,
        outcome_feedback_confidence_score=row.outcome_feedback_confidence_score,
        freshness_support_score=freshness_support_score,
        conflict_safety_score=conflict_safety_score,
        config=config,
    )
    lowest_support_score = min(
        row.memory_confidence_score,
        row.evidence_recheck_confidence_score,
        row.cross_evidence_consistency_score,
        row.outcome_feedback_confidence_score,
        freshness_support_score,
        conflict_safety_score,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        memory_confidence_score=row.memory_confidence_score,
        evidence_recheck_confidence_score=row.evidence_recheck_confidence_score,
        cross_evidence_consistency_score=row.cross_evidence_consistency_score,
        outcome_feedback_confidence_score=row.outcome_feedback_confidence_score,
        freshness_support_score=freshness_support_score,
        conflict_safety_score=conflict_safety_score,
        staleness_risk_score=row.staleness_risk_score,
        conflict_risk_score=row.conflict_risk_score,
        guard_score=guard_score,
        config=config,
    )
    return ResearchStrategyMarketMemoryConfidenceGuardRow(
        memory_item_digest=_private_ref_digest(row.private_memory_ref),
        memory_confidence_score=row.memory_confidence_score,
        evidence_recheck_confidence_score=row.evidence_recheck_confidence_score,
        cross_evidence_consistency_score=row.cross_evidence_consistency_score,
        outcome_feedback_confidence_score=row.outcome_feedback_confidence_score,
        staleness_risk_score=row.staleness_risk_score,
        freshness_support_score=freshness_support_score,
        conflict_risk_score=row.conflict_risk_score,
        conflict_safety_score=conflict_safety_score,
        guard_score=guard_score,
        lowest_support_score=lowest_support_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _guard_score(
    *,
    memory_confidence_score: Decimal,
    evidence_recheck_confidence_score: Decimal,
    cross_evidence_consistency_score: Decimal,
    outcome_feedback_confidence_score: Decimal,
    freshness_support_score: Decimal,
    conflict_safety_score: Decimal,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig,
) -> Decimal:
    return _quantize(
        (memory_confidence_score * config.memory_confidence_weight)
        + (evidence_recheck_confidence_score * config.evidence_recheck_weight)
        + (
            cross_evidence_consistency_score
            * config.cross_evidence_consistency_weight
        )
        + (outcome_feedback_confidence_score * config.outcome_feedback_weight)
        + (freshness_support_score * config.freshness_support_weight)
        + (conflict_safety_score * config.conflict_safety_weight),
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    memory_confidence_score: Decimal,
    evidence_recheck_confidence_score: Decimal,
    cross_evidence_consistency_score: Decimal,
    outcome_feedback_confidence_score: Decimal,
    freshness_support_score: Decimal,
    conflict_safety_score: Decimal,
    staleness_risk_score: Decimal,
    conflict_risk_score: Decimal,
    guard_score: Decimal,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    _append_support_reason(
        reason_codes,
        block_code=REASON_MEMORY_CONFIDENCE_BLOCK,
        watch_code=REASON_MEMORY_CONFIDENCE_WATCH,
        value=memory_confidence_score,
        config=config,
    )
    _append_support_reason(
        reason_codes,
        block_code=REASON_EVIDENCE_RECHECK_CONFIDENCE_BLOCK,
        watch_code=REASON_EVIDENCE_RECHECK_CONFIDENCE_WATCH,
        value=evidence_recheck_confidence_score,
        config=config,
    )
    _append_support_reason(
        reason_codes,
        block_code=REASON_CROSS_EVIDENCE_CONSISTENCY_BLOCK,
        watch_code=REASON_CROSS_EVIDENCE_CONSISTENCY_WATCH,
        value=cross_evidence_consistency_score,
        config=config,
    )
    _append_support_reason(
        reason_codes,
        block_code=REASON_OUTCOME_FEEDBACK_CONFIDENCE_BLOCK,
        watch_code=REASON_OUTCOME_FEEDBACK_CONFIDENCE_WATCH,
        value=outcome_feedback_confidence_score,
        config=config,
    )
    _append_support_reason(
        reason_codes,
        block_code=REASON_FRESHNESS_SUPPORT_BLOCK,
        watch_code=REASON_FRESHNESS_SUPPORT_WATCH,
        value=freshness_support_score,
        config=config,
    )
    _append_support_reason(
        reason_codes,
        block_code=REASON_CONFLICT_SAFETY_BLOCK,
        watch_code=REASON_CONFLICT_SAFETY_WATCH,
        value=conflict_safety_score,
        config=config,
    )
    _append_risk_reason(
        reason_codes,
        block_code=REASON_STALENESS_RISK_BLOCK,
        watch_code=REASON_STALENESS_RISK_WATCH,
        value=staleness_risk_score,
        config=config,
    )
    _append_risk_reason(
        reason_codes,
        block_code=REASON_CONFLICT_RISK_BLOCK,
        watch_code=REASON_CONFLICT_RISK_WATCH,
        value=conflict_risk_score,
        config=config,
    )
    if guard_score < config.watch_min_guard_score:
        reason_codes.append(REASON_GUARD_SCORE_BLOCK)
    elif guard_score < config.pass_min_guard_score:
        reason_codes.append(REASON_GUARD_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_MEMORY_CONFIDENCE_GUARD_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _append_support_reason(
    reason_codes: list[str],
    *,
    block_code: str,
    watch_code: str,
    value: Decimal,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig,
) -> None:
    if value < config.min_watch_support_score:
        reason_codes.append(block_code)
    elif value < config.min_pass_support_score:
        reason_codes.append(watch_code)


def _append_risk_reason(
    reason_codes: list[str],
    *,
    block_code: str,
    watch_code: str,
    value: Decimal,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig,
) -> None:
    if value > config.max_watch_risk_score:
        reason_codes.append(block_code)
    elif value > config.max_pass_risk_score:
        reason_codes.append(watch_code)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_MEMORY_CONFIDENCE_GUARD_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyMarketMemoryConfidenceGuardRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyMarketMemoryConfidenceGuardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchStrategyMarketMemoryConfidenceGuardRow) -> tuple[
    int,
    Decimal,
    str,
]:
    return (_status_rank(row.status), row.guard_score, row.memory_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyMarketMemoryConfidenceGuardRow, ...],
) -> tuple[ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyMarketMemoryConfidenceGuardInput],
) -> tuple[ResearchStrategyMarketMemoryConfidenceGuardInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be a sequence") from exc
    for value in values:
        if type(value) is not ResearchStrategyMarketMemoryConfidenceGuardInput:
            raise ValueError(
                "inputs must contain ResearchStrategyMarketMemoryConfidenceGuardInput "
                "values",
            )
        _require_hard_flags("input", value)
    return values


def _normalize_rows(
    rows: tuple[ResearchStrategyMarketMemoryConfidenceGuardRow, ...],
) -> tuple[ResearchStrategyMarketMemoryConfidenceGuardRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyMarketMemoryConfidenceGuardRow:
            raise ValueError(
                "rows must contain ResearchStrategyMarketMemoryConfidenceGuardRow "
                "values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount, ...],
) -> tuple[ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount values",
            )
        _require_hard_flags("reason count", value)
    return values


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _UPSTREAM_REASON_CODE_SEQUENCE)


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _ROW_REASON_CODE_SEQUENCE)


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _REPORT_REASON_CODE_SEQUENCE)


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code, allowed_sequence)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in allowed_sequence if reason_code in seen)


def _require_reason_code(
    field_name: str,
    value: str,
    allowed_sequence: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_sequence:
        raise ValueError(f"{field_name} contains an unsupported reason code")
    return value


def _validate_row(
    row: ResearchStrategyMarketMemoryConfidenceGuardRow,
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig | None,
) -> None:
    generated = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if (
        REASON_MEMORY_CONFIDENCE_GUARD_PASS in row.reason_codes
        and generated != (REASON_MEMORY_CONFIDENCE_GUARD_PASS,)
    ):
        raise ValueError("reason_codes cannot mix pass and watch/block reasons")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if config is None:
        return
    expected_freshness = _inverse_ratio(row.staleness_risk_score)
    expected_conflict_safety = _inverse_ratio(row.conflict_risk_score)
    if row.freshness_support_score != expected_freshness:
        raise ValueError("freshness_support_score mismatch")
    if row.conflict_safety_score != expected_conflict_safety:
        raise ValueError("conflict_safety_score mismatch")
    expected_guard_score = _guard_score(
        memory_confidence_score=row.memory_confidence_score,
        evidence_recheck_confidence_score=row.evidence_recheck_confidence_score,
        cross_evidence_consistency_score=row.cross_evidence_consistency_score,
        outcome_feedback_confidence_score=row.outcome_feedback_confidence_score,
        freshness_support_score=row.freshness_support_score,
        conflict_safety_score=row.conflict_safety_score,
        config=config,
    )
    if row.guard_score != expected_guard_score:
        raise ValueError("guard_score mismatch")
    expected_lowest_support_score = min(
        row.memory_confidence_score,
        row.evidence_recheck_confidence_score,
        row.cross_evidence_consistency_score,
        row.outcome_feedback_confidence_score,
        row.freshness_support_score,
        row.conflict_safety_score,
    )
    if row.lowest_support_score != expected_lowest_support_score:
        raise ValueError("lowest_support_score mismatch")
    expected_reasons = _row_reason_codes(
        upstream_reason_codes=tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        ),
        memory_confidence_score=row.memory_confidence_score,
        evidence_recheck_confidence_score=row.evidence_recheck_confidence_score,
        cross_evidence_consistency_score=row.cross_evidence_consistency_score,
        outcome_feedback_confidence_score=row.outcome_feedback_confidence_score,
        freshness_support_score=row.freshness_support_score,
        conflict_safety_score=row.conflict_safety_score,
        staleness_risk_score=row.staleness_risk_score,
        conflict_risk_score=row.conflict_risk_score,
        guard_score=row.guard_score,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes mismatch")


def _validate_report(report: ResearchStrategyMarketMemoryConfidenceGuardReport) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count mismatch")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count mismatch")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count mismatch")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count mismatch")
    if report.status != _report_status(rows):
        raise ValueError("status mismatch")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    if report.average_guard_score != _average_ratio(tuple(row.guard_score for row in rows)):
        raise ValueError("average_guard_score mismatch")
    if report.min_guard_score != min((row.guard_score for row in rows), default=_ZERO):
        raise ValueError("min_guard_score mismatch")
    if report.min_memory_confidence_score != min(
        (row.memory_confidence_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_memory_confidence_score mismatch")
    if report.min_evidence_recheck_confidence_score != min(
        (row.evidence_recheck_confidence_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_recheck_confidence_score mismatch")
    if report.min_cross_evidence_consistency_score != min(
        (row.cross_evidence_consistency_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_cross_evidence_consistency_score mismatch")
    if report.min_outcome_feedback_confidence_score != min(
        (row.outcome_feedback_confidence_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_outcome_feedback_confidence_score mismatch")
    if report.max_staleness_risk_score != max(
        (row.staleness_risk_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_staleness_risk_score mismatch")
    if report.max_conflict_risk_score != max(
        (row.conflict_risk_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_conflict_risk_score mismatch")
    expected_counts = _reason_code_counts(rows)
    expected_reasons = _normalize_report_reason_codes(
        tuple(row.reason_code for row in expected_counts),
    )
    if not rows:
        expected_counts = (
            ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_reasons = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts mismatch")
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes mismatch")


def _config_weight_sum(
    config: ResearchStrategyMarketMemoryConfidenceGuardConfig,
) -> Decimal:
    return _quantize(
        config.memory_confidence_weight
        + config.evidence_recheck_weight
        + config.cross_evidence_consistency_weight
        + config.outcome_feedback_weight
        + config.freshness_support_weight
        + config.conflict_safety_weight,
    )


def _inverse_ratio(value: Decimal) -> Decimal:
    return _quantize(_ONE - value)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must fit the six-place quantum") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    for character in value:
        if not (
            character.isalnum()
            or character in {"-", "_", "."}
        ):
            raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest")
    digest = value.removeprefix("sha256:")
    _require_digest(field_name, digest)
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in _HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if isinstance(value, dict):
            flag_value = value.get(field_name)
        else:
            flag_value = getattr(value, field_name, None)
        if flag_value is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _report_digest(
    report: ResearchStrategyMarketMemoryConfidenceGuardReport,
) -> str:
    return _report_digest_from_values(asdict(report))


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, object]) -> str:
    copied = dict(payload)
    copied.pop(_DIGEST_FIELD, None)
    encoded = json.dumps(copied, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchStrategyMarketMemoryConfidenceGuardReport,
) -> dict[str, object]:
    payload = _payload_value(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        return format(value.quantize(_QUANT), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item)
            for key, item in value.items()
        }
    return value


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if not isinstance(copied, dict):
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return {str(key): _copy_json_value(item) for key, item in value.items()}
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if type(value) in {str, bool} or value is None:
        return value
    if type(value) in {int, float, Decimal}:
        raise ValueError("public numeric values must be Decimal strings")
    raise ValueError("payload must contain JSON-compatible public values")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_payload_statuses(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_public_payload_numbers(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_public_payload_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _validate_public_payload_numbers(item)
    elif type(value) in {int, float, Decimal}:
        raise ValueError("public numeric values must be Decimal strings")


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    if digest != _payload_digest(payload):
        raise ValueError("derived_validation_digest mismatch")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    payload = value if allow_json_containers else _payload_value(value)
    _reject_unsafe_public_value(label, payload)


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).casefold()
            if any(fragment in key_text for fragment in _UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_value(f"{label}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_value(label, item)
    elif type(value) is str:
        value_text = value.casefold()
        if any(fragment in value_text for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
