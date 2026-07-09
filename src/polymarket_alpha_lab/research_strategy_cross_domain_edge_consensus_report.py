"""Report-only cross-domain edge consensus scorecard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION = (
    "research-strategy-cross-domain-edge-consensus-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_CROSS_DOMAIN_REVIEW_READY = "cross_domain_review_ready"
REASON_DOMAIN_DISAGREEMENT_OBSERVED = "domain_disagreement_observed"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_SOURCE_FRESHNESS_GAP_OBSERVED = "source_freshness_gap_observed"
REASON_SPECIALIST_MEMORY_REVIEW_REQUESTED = (
    "specialist_memory_review_requested"
)
REASON_DOMAIN_SIGNAL_AGREEMENT_BLOCK = "domain_signal_agreement_block"
REASON_DOMAIN_SIGNAL_AGREEMENT_WATCH = "domain_signal_agreement_watch"
REASON_EVIDENCE_STRENGTH_BLOCK = "evidence_strength_block"
REASON_EVIDENCE_STRENGTH_WATCH = "evidence_strength_watch"
REASON_SOURCE_FRESHNESS_BLOCK = "source_freshness_block"
REASON_SOURCE_FRESHNESS_WATCH = "source_freshness_watch"
REASON_COST_DRAG_BLOCK = "cost_drag_block"
REASON_COST_DRAG_WATCH = "cost_drag_watch"
REASON_LIQUIDITY_QUALITY_BLOCK = "liquidity_quality_block"
REASON_LIQUIDITY_QUALITY_WATCH = "liquidity_quality_watch"
REASON_RESOLUTION_CLARITY_BLOCK = "resolution_clarity_block"
REASON_RESOLUTION_CLARITY_WATCH = "resolution_clarity_watch"
REASON_SPECIALIST_MEMORY_CONFIDENCE_BLOCK = (
    "specialist_memory_confidence_block"
)
REASON_SPECIALIST_MEMORY_CONFIDENCE_WATCH = (
    "specialist_memory_confidence_watch"
)
REASON_CONSENSUS_SCORE_BLOCK = "consensus_score_block"
REASON_CONSENSUS_SCORE_WATCH = "consensus_score_watch"
REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS = "cross_domain_edge_consensus_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_CROSS_DOMAIN_REVIEW_READY,
    REASON_DOMAIN_DISAGREEMENT_OBSERVED,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_SOURCE_FRESHNESS_GAP_OBSERVED,
    REASON_SPECIALIST_MEMORY_REVIEW_REQUESTED,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_DOMAIN_SIGNAL_AGREEMENT_BLOCK,
    REASON_DOMAIN_SIGNAL_AGREEMENT_WATCH,
    REASON_EVIDENCE_STRENGTH_BLOCK,
    REASON_EVIDENCE_STRENGTH_WATCH,
    REASON_SOURCE_FRESHNESS_BLOCK,
    REASON_SOURCE_FRESHNESS_WATCH,
    REASON_COST_DRAG_BLOCK,
    REASON_COST_DRAG_WATCH,
    REASON_LIQUIDITY_QUALITY_BLOCK,
    REASON_LIQUIDITY_QUALITY_WATCH,
    REASON_RESOLUTION_CLARITY_BLOCK,
    REASON_RESOLUTION_CLARITY_WATCH,
    REASON_SPECIALIST_MEMORY_CONFIDENCE_BLOCK,
    REASON_SPECIALIST_MEMORY_CONFIDENCE_WATCH,
    REASON_CONSENSUS_SCORE_BLOCK,
    REASON_CONSENSUS_SCORE_WATCH,
    REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS,
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
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "live",
    "raw",
    "private key",
    "http://",
    "https://",
    "://",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION",
    "ResearchStrategyCrossDomainEdgeConsensusConfig",
    "ResearchStrategyCrossDomainEdgeConsensusInput",
    "ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount",
    "ResearchStrategyCrossDomainEdgeConsensusReport",
    "ResearchStrategyCrossDomainEdgeConsensusRow",
    "build_research_strategy_cross_domain_edge_consensus_report",
    "research_strategy_cross_domain_edge_consensus_report_digest",
    "research_strategy_cross_domain_edge_consensus_report_payload",
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
class ResearchStrategyCrossDomainEdgeConsensusConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION
    )
    pass_min_consensus_score: Decimal = Decimal("0.800000")
    watch_min_consensus_score: Decimal = Decimal("0.600000")
    min_pass_dimension_score: Decimal = Decimal("0.750000")
    min_watch_dimension_score: Decimal = Decimal("0.500000")
    max_pass_cost_drag_score: Decimal = Decimal("0.200000")
    max_watch_cost_drag_score: Decimal = Decimal("0.450000")
    domain_signal_agreement_weight: Decimal = Decimal("0.180000")
    evidence_strength_weight: Decimal = Decimal("0.170000")
    source_freshness_weight: Decimal = Decimal("0.130000")
    cost_efficiency_weight: Decimal = Decimal("0.130000")
    liquidity_quality_weight: Decimal = Decimal("0.140000")
    resolution_clarity_weight: Decimal = Decimal("0.130000")
    specialist_memory_confidence_weight: Decimal = Decimal("0.120000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainEdgeConsensusConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_consensus_score",
            "watch_min_consensus_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
            "domain_signal_agreement_weight",
            "evidence_strength_weight",
            "source_freshness_weight",
            "cost_efficiency_weight",
            "liquidity_quality_weight",
            "resolution_clarity_weight",
            "specialist_memory_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_consensus_score < self.watch_min_consensus_score:
            raise ValueError(
                "pass_min_consensus_score must be at least watch_min_consensus_score",
            )
        if self.min_pass_dimension_score < self.min_watch_dimension_score:
            raise ValueError(
                "min_pass_dimension_score must be at least min_watch_dimension_score",
            )
        if self.max_pass_cost_drag_score > self.max_watch_cost_drag_score:
            raise ValueError(
                "max_pass_cost_drag_score must not exceed max_watch_cost_drag_score",
            )
        if _config_weight_sum(self) != _ONE:
            raise ValueError("cross-domain edge consensus weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossDomainEdgeConsensusInput(_FinalPublicDataclass):
    consensus_item_ref: str
    domain_signal_agreement_score: Decimal
    evidence_strength_score: Decimal
    source_freshness_score: Decimal
    cost_drag_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainEdgeConsensusInput, "input")
        object.__setattr__(
            self,
            "consensus_item_ref",
            _require_private_ref("consensus_item_ref", self.consensus_item_ref),
        )
        for field_name in (
            "domain_signal_agreement_score",
            "evidence_strength_score",
            "source_freshness_score",
            "cost_drag_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
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
class ResearchStrategyCrossDomainEdgeConsensusRow(_FinalPublicDataclass):
    consensus_item_digest: str
    domain_signal_agreement_score: Decimal
    evidence_strength_score: Decimal
    source_freshness_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    consensus_score: Decimal
    lowest_dimension_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyCrossDomainEdgeConsensusConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyCrossDomainEdgeConsensusConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainEdgeConsensusRow, "row")
        object.__setattr__(
            self,
            "consensus_item_digest",
            _require_private_digest("consensus_item_digest", self.consensus_item_digest),
        )
        for field_name in (
            "domain_signal_agreement_score",
            "evidence_strength_score",
            "source_freshness_score",
            "cost_drag_score",
            "cost_efficiency_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
            "consensus_score",
            "lowest_dimension_score",
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
class ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount,
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
class ResearchStrategyCrossDomainEdgeConsensusReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_consensus_score: Decimal
    min_consensus_score: Decimal
    min_domain_signal_agreement_score: Decimal
    min_evidence_strength_score: Decimal
    min_source_freshness_score: Decimal
    max_cost_drag_score: Decimal
    min_liquidity_quality_score: Decimal
    min_resolution_clarity_score: Decimal
    min_specialist_memory_confidence_score: Decimal
    rows: tuple[ResearchStrategyCrossDomainEdgeConsensusRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainEdgeConsensusReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION
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
            "average_consensus_score",
            "min_consensus_score",
            "min_domain_signal_agreement_score",
            "min_evidence_strength_score",
            "min_source_freshness_score",
            "max_cost_drag_score",
            "min_liquidity_quality_score",
            "min_resolution_clarity_score",
            "min_specialist_memory_confidence_score",
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
        return research_strategy_cross_domain_edge_consensus_report_payload(self)


def build_research_strategy_cross_domain_edge_consensus_report(
    inputs: Sequence[ResearchStrategyCrossDomainEdgeConsensusInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyCrossDomainEdgeConsensusConfig | None = None,
) -> ResearchStrategyCrossDomainEdgeConsensusReport:
    """Build a deterministic, readonly cross-domain edge consensus report."""

    cfg = config or ResearchStrategyCrossDomainEdgeConsensusConfig()
    if type(cfg) is not ResearchStrategyCrossDomainEdgeConsensusConfig:
        raise ValueError("config must be a ResearchStrategyCrossDomainEdgeConsensusConfig")
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
            ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(
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
        "average_consensus_score": _average_ratio(
            tuple(row.consensus_score for row in rows),
        ),
        "min_consensus_score": min(
            (row.consensus_score for row in rows),
            default=_ZERO,
        ),
        "min_domain_signal_agreement_score": min(
            (row.domain_signal_agreement_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_strength_score": min(
            (row.evidence_strength_score for row in rows),
            default=_ZERO,
        ),
        "min_source_freshness_score": min(
            (row.source_freshness_score for row in rows),
            default=_ZERO,
        ),
        "max_cost_drag_score": max((row.cost_drag_score for row in rows), default=_ZERO),
        "min_liquidity_quality_score": min(
            (row.liquidity_quality_score for row in rows),
            default=_ZERO,
        ),
        "min_resolution_clarity_score": min(
            (row.resolution_clarity_score for row in rows),
            default=_ZERO,
        ),
        "min_specialist_memory_confidence_score": min(
            (row.specialist_memory_confidence_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCrossDomainEdgeConsensusReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_cross_domain_edge_consensus_report_payload(
    value: ResearchStrategyCrossDomainEdgeConsensusReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyCrossDomainEdgeConsensusReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyCrossDomainEdgeConsensusReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    _validate_payload_schema(payload)
    return payload


def research_strategy_cross_domain_edge_consensus_report_digest(
    report: ResearchStrategyCrossDomainEdgeConsensusReport,
) -> str:
    if type(report) is not ResearchStrategyCrossDomainEdgeConsensusReport:
        raise ValueError("report must be a ResearchStrategyCrossDomainEdgeConsensusReport")
    return _report_digest(report)


def _row_for_input(
    row: ResearchStrategyCrossDomainEdgeConsensusInput,
    config: ResearchStrategyCrossDomainEdgeConsensusConfig,
) -> ResearchStrategyCrossDomainEdgeConsensusRow:
    cost_efficiency_score = _inverse_ratio(row.cost_drag_score)
    consensus_score = _consensus_score(
        domain_signal_agreement_score=row.domain_signal_agreement_score,
        evidence_strength_score=row.evidence_strength_score,
        source_freshness_score=row.source_freshness_score,
        cost_efficiency_score=cost_efficiency_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        config=config,
    )
    lowest_dimension_score = min(
        row.domain_signal_agreement_score,
        row.evidence_strength_score,
        row.source_freshness_score,
        cost_efficiency_score,
        row.liquidity_quality_score,
        row.resolution_clarity_score,
        row.specialist_memory_confidence_score,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        domain_signal_agreement_score=row.domain_signal_agreement_score,
        evidence_strength_score=row.evidence_strength_score,
        source_freshness_score=row.source_freshness_score,
        cost_drag_score=row.cost_drag_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        consensus_score=consensus_score,
        config=config,
    )
    return ResearchStrategyCrossDomainEdgeConsensusRow(
        consensus_item_digest=_private_ref_digest(row.consensus_item_ref),
        domain_signal_agreement_score=row.domain_signal_agreement_score,
        evidence_strength_score=row.evidence_strength_score,
        source_freshness_score=row.source_freshness_score,
        cost_drag_score=row.cost_drag_score,
        cost_efficiency_score=cost_efficiency_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        consensus_score=consensus_score,
        lowest_dimension_score=lowest_dimension_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    domain_signal_agreement_score: Decimal,
    evidence_strength_score: Decimal,
    source_freshness_score: Decimal,
    cost_drag_score: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
    consensus_score: Decimal,
    config: ResearchStrategyCrossDomainEdgeConsensusConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_DOMAIN_SIGNAL_AGREEMENT_BLOCK,
        watch_code=REASON_DOMAIN_SIGNAL_AGREEMENT_WATCH,
        value=domain_signal_agreement_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_EVIDENCE_STRENGTH_BLOCK,
        watch_code=REASON_EVIDENCE_STRENGTH_WATCH,
        value=evidence_strength_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_SOURCE_FRESHNESS_BLOCK,
        watch_code=REASON_SOURCE_FRESHNESS_WATCH,
        value=source_freshness_score,
        config=config,
    )
    if cost_drag_score > config.max_watch_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_BLOCK)
    elif cost_drag_score > config.max_pass_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_WATCH)
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_LIQUIDITY_QUALITY_BLOCK,
        watch_code=REASON_LIQUIDITY_QUALITY_WATCH,
        value=liquidity_quality_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_RESOLUTION_CLARITY_BLOCK,
        watch_code=REASON_RESOLUTION_CLARITY_WATCH,
        value=resolution_clarity_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_SPECIALIST_MEMORY_CONFIDENCE_BLOCK,
        watch_code=REASON_SPECIALIST_MEMORY_CONFIDENCE_WATCH,
        value=specialist_memory_confidence_score,
        config=config,
    )
    if consensus_score < config.watch_min_consensus_score:
        reason_codes.append(REASON_CONSENSUS_SCORE_BLOCK)
    elif consensus_score < config.pass_min_consensus_score:
        reason_codes.append(REASON_CONSENSUS_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _append_dimension_reason(
    reason_codes: list[str],
    *,
    block_code: str,
    watch_code: str,
    value: Decimal,
    config: ResearchStrategyCrossDomainEdgeConsensusConfig,
) -> None:
    if value < config.min_watch_dimension_score:
        reason_codes.append(block_code)
    elif value < config.min_pass_dimension_score:
        reason_codes.append(watch_code)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyCrossDomainEdgeConsensusRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyCrossDomainEdgeConsensusRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchStrategyCrossDomainEdgeConsensusRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.consensus_score, row.consensus_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyCrossDomainEdgeConsensusRow, ...],
) -> tuple[ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _consensus_score(
    *,
    domain_signal_agreement_score: Decimal,
    evidence_strength_score: Decimal,
    source_freshness_score: Decimal,
    cost_efficiency_score: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
    config: ResearchStrategyCrossDomainEdgeConsensusConfig,
) -> Decimal:
    score = (
        domain_signal_agreement_score * config.domain_signal_agreement_weight
        + evidence_strength_score * config.evidence_strength_weight
        + source_freshness_score * config.source_freshness_weight
        + cost_efficiency_score * config.cost_efficiency_weight
        + liquidity_quality_score * config.liquidity_quality_weight
        + resolution_clarity_score * config.resolution_clarity_weight
        + specialist_memory_confidence_score
        * config.specialist_memory_confidence_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyCrossDomainEdgeConsensusRow,
    config: ResearchStrategyCrossDomainEdgeConsensusConfig | None,
) -> None:
    expected_lowest = min(
        row.domain_signal_agreement_score,
        row.evidence_strength_score,
        row.source_freshness_score,
        row.cost_efficiency_score,
        row.liquidity_quality_score,
        row.resolution_clarity_score,
        row.specialist_memory_confidence_score,
    )
    if row.cost_efficiency_score != _inverse_ratio(row.cost_drag_score):
        raise ValueError("cost_efficiency_score must match cost_drag_score")
    if row.lowest_dimension_score != expected_lowest:
        raise ValueError("lowest_dimension_score must match dimensions")
    if config is not None:
        if type(config) is not ResearchStrategyCrossDomainEdgeConsensusConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyCrossDomainEdgeConsensusConfig",
            )
        expected_consensus = _consensus_score(
            domain_signal_agreement_score=row.domain_signal_agreement_score,
            evidence_strength_score=row.evidence_strength_score,
            source_freshness_score=row.source_freshness_score,
            cost_efficiency_score=row.cost_efficiency_score,
            liquidity_quality_score=row.liquidity_quality_score,
            resolution_clarity_score=row.resolution_clarity_score,
            specialist_memory_confidence_score=row.specialist_memory_confidence_score,
            config=config,
        )
        if row.consensus_score != expected_consensus:
            raise ValueError("consensus_score must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            domain_signal_agreement_score=row.domain_signal_agreement_score,
            evidence_strength_score=row.evidence_strength_score,
            source_freshness_score=row.source_freshness_score,
            cost_drag_score=row.cost_drag_score,
            liquidity_quality_score=row.liquidity_quality_score,
            resolution_clarity_score=row.resolution_clarity_score,
            specialist_memory_confidence_score=row.specialist_memory_confidence_score,
            consensus_score=row.consensus_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(report: ResearchStrategyCrossDomainEdgeConsensusReport) -> None:
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
    if report.average_consensus_score != _average_ratio(
        tuple(row.consensus_score for row in report.rows),
    ):
        raise ValueError("average_consensus_score must match rows")
    if report.min_consensus_score != min(
        (row.consensus_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_consensus_score must match rows")
    if report.min_domain_signal_agreement_score != min(
        (row.domain_signal_agreement_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_domain_signal_agreement_score must match rows")
    if report.min_evidence_strength_score != min(
        (row.evidence_strength_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_strength_score must match rows")
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
    if report.min_liquidity_quality_score != min(
        (row.liquidity_quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_liquidity_quality_score must match rows")
    if report.min_resolution_clarity_score != min(
        (row.resolution_clarity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_resolution_clarity_score must match rows")
    if report.min_specialist_memory_confidence_score != min(
        (row.specialist_memory_confidence_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_specialist_memory_confidence_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(
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
    inputs: Sequence[ResearchStrategyCrossDomainEdgeConsensusInput],
) -> tuple[ResearchStrategyCrossDomainEdgeConsensusInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainEdgeConsensusInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCrossDomainEdgeConsensusInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.consensus_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by consensus item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyCrossDomainEdgeConsensusRow, ...],
) -> tuple[ResearchStrategyCrossDomainEdgeConsensusRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainEdgeConsensusRow:
            raise ValueError(
                "rows must contain ResearchStrategyCrossDomainEdgeConsensusRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.consensus_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique consensus item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount, ...],
) -> tuple[ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount",
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
    if REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_CROSS_DOMAIN_EDGE_CONSENSUS_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REPORT_REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(report: ResearchStrategyCrossDomainEdgeConsensusReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_consensus_score=report.average_consensus_score,
        min_consensus_score=report.min_consensus_score,
        min_domain_signal_agreement_score=report.min_domain_signal_agreement_score,
        min_evidence_strength_score=report.min_evidence_strength_score,
        min_source_freshness_score=report.min_source_freshness_score,
        max_cost_drag_score=report.max_cost_drag_score,
        min_liquidity_quality_score=report.min_liquidity_quality_score,
        min_resolution_clarity_score=report.min_resolution_clarity_score,
        min_specialist_memory_confidence_score=(
            report.min_specialist_memory_confidence_score
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


def _report_digest(report: ResearchStrategyCrossDomainEdgeConsensusReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_consensus_score": report.average_consensus_score,
            "min_consensus_score": report.min_consensus_score,
            "min_domain_signal_agreement_score": (
                report.min_domain_signal_agreement_score
            ),
            "min_evidence_strength_score": report.min_evidence_strength_score,
            "min_source_freshness_score": report.min_source_freshness_score,
            "max_cost_drag_score": report.max_cost_drag_score,
            "min_liquidity_quality_score": report.min_liquidity_quality_score,
            "min_resolution_clarity_score": report.min_resolution_clarity_score,
            "min_specialist_memory_confidence_score": (
                report.min_specialist_memory_confidence_score
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


def _validate_payload_schema(payload: dict[str, object]) -> None:
    _require_payload_keys(
        "report payload",
        payload,
        (
            "generated_at",
            "config_version",
            "status",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_consensus_score",
            "min_consensus_score",
            "min_domain_signal_agreement_score",
            "min_evidence_strength_score",
            "min_source_freshness_score",
            "max_cost_drag_score",
            "min_liquidity_quality_score",
            "min_resolution_clarity_score",
            "min_specialist_memory_confidence_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
            _DIGEST_FIELD,
        ),
    )
    rows = tuple(
        _payload_row(row_payload)
        for row_payload in _payload_object_list("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _payload_reason_code_count(row_payload)
        for row_payload in _payload_object_list(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    report = ResearchStrategyCrossDomainEdgeConsensusReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        status=_payload_status("status", payload["status"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_consensus_score=_payload_decimal(
            "average_consensus_score",
            payload["average_consensus_score"],
        ),
        min_consensus_score=_payload_decimal(
            "min_consensus_score",
            payload["min_consensus_score"],
        ),
        min_domain_signal_agreement_score=_payload_decimal(
            "min_domain_signal_agreement_score",
            payload["min_domain_signal_agreement_score"],
        ),
        min_evidence_strength_score=_payload_decimal(
            "min_evidence_strength_score",
            payload["min_evidence_strength_score"],
        ),
        min_source_freshness_score=_payload_decimal(
            "min_source_freshness_score",
            payload["min_source_freshness_score"],
        ),
        max_cost_drag_score=_payload_decimal(
            "max_cost_drag_score",
            payload["max_cost_drag_score"],
        ),
        min_liquidity_quality_score=_payload_decimal(
            "min_liquidity_quality_score",
            payload["min_liquidity_quality_score"],
        ),
        min_resolution_clarity_score=_payload_decimal(
            "min_resolution_clarity_score",
            payload["min_resolution_clarity_score"],
        ),
        min_specialist_memory_confidence_score=_payload_decimal(
            "min_specialist_memory_confidence_score",
            payload["min_specialist_memory_confidence_score"],
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            _REPORT_REASON_CODE_SEQUENCE,
        ),
        derived_validation_digest=_payload_string(
            _DIGEST_FIELD,
            payload[_DIGEST_FIELD],
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    if _report_payload(report) != payload:
        raise ValueError("report payload must use canonical report payload schema")


def _payload_row(
    payload: dict[str, object],
) -> ResearchStrategyCrossDomainEdgeConsensusRow:
    _require_payload_keys(
        "row payload",
        payload,
        (
            "consensus_item_digest",
            "domain_signal_agreement_score",
            "evidence_strength_score",
            "source_freshness_score",
            "cost_drag_score",
            "cost_efficiency_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
            "consensus_score",
            "lowest_dimension_score",
            "observed_at",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchStrategyCrossDomainEdgeConsensusRow(
        consensus_item_digest=_payload_string(
            "consensus_item_digest",
            payload["consensus_item_digest"],
        ),
        domain_signal_agreement_score=_payload_decimal(
            "domain_signal_agreement_score",
            payload["domain_signal_agreement_score"],
        ),
        evidence_strength_score=_payload_decimal(
            "evidence_strength_score",
            payload["evidence_strength_score"],
        ),
        source_freshness_score=_payload_decimal(
            "source_freshness_score",
            payload["source_freshness_score"],
        ),
        cost_drag_score=_payload_decimal("cost_drag_score", payload["cost_drag_score"]),
        cost_efficiency_score=_payload_decimal(
            "cost_efficiency_score",
            payload["cost_efficiency_score"],
        ),
        liquidity_quality_score=_payload_decimal(
            "liquidity_quality_score",
            payload["liquidity_quality_score"],
        ),
        resolution_clarity_score=_payload_decimal(
            "resolution_clarity_score",
            payload["resolution_clarity_score"],
        ),
        specialist_memory_confidence_score=_payload_decimal(
            "specialist_memory_confidence_score",
            payload["specialist_memory_confidence_score"],
        ),
        consensus_score=_payload_decimal(
            "consensus_score",
            payload["consensus_score"],
        ),
        lowest_dimension_score=_payload_decimal(
            "lowest_dimension_score",
            payload["lowest_dimension_score"],
        ),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        status=_payload_status("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            _ROW_REASON_CODE_SEQUENCE,
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _payload_reason_code_count(
    payload: dict[str, object],
) -> ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount:
    _require_payload_keys(
        "reason_code_count payload",
        payload,
        (
            "reason_code",
            "count",
            "row_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(
        reason_code=_payload_reason_code(
            "reason_code",
            payload["reason_code"],
            _REPORT_REASON_CODE_SEQUENCE,
        ),
        count=_payload_decimal("count", payload["count"]),
        row_ratio=_payload_decimal("row_ratio", payload["row_ratio"]),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _require_payload_keys(
    label: str,
    payload: dict[str, object],
    expected_keys: tuple[str, ...],
) -> None:
    if set(payload) != set(expected_keys):
        raise ValueError(f"{label} must use canonical report payload schema")


def _payload_object_list(
    field_name: str,
    value: object,
) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    rows: list[dict[str, object]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must use canonical report payload schema")
        rows.append(item)
    return tuple(rows)


def _payload_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return tuple(
        _payload_reason_code(field_name, reason_code, allowed_values)
        for reason_code in value
    )


def _payload_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    return _require_reason_code(field_name, _payload_string(field_name, value), allowed_values)


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return value


def _payload_status(field_name: str, value: object) -> str:
    return _require_status(field_name, _payload_string(field_name, value))


def _payload_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(field_name, parsed)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return normalized


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc
    parsed = _require_decimal(field_name, parsed)
    normalized = _quantize(parsed)
    if value != str(normalized):
        raise ValueError(f"{field_name} must use canonical report payload schema")
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    if (
        field_name.endswith("_score")
        or field_name.endswith("_ratio")
    ) and normalized > _ONE:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    if (
        field_name == "count"
        or field_name.endswith("_count")
    ) and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return normalized


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
                raise ValueError("payload object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    raise ValueError("payload value is not JSON serializable")


def _as_utc(field_name: str, value: object) -> datetime:
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
        raise ValueError(f"{field_name} must be between 0 and 1")
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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _inverse_ratio(value: Decimal) -> Decimal:
    return _quantize(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _config_weight_sum(config: ResearchStrategyCrossDomainEdgeConsensusConfig) -> Decimal:
    return _quantize(
        config.domain_signal_agreement_weight
        + config.evidence_strength_weight
        + config.source_freshness_weight
        + config.cost_efficiency_weight
        + config.liquidity_quality_weight
        + config.resolution_clarity_weight
        + config.specialist_memory_confidence_weight,
    )


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be empty")
    return value


def _private_ref_digest(value: str) -> str:
    _require_private_ref("private reference", value)
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be an allowed reason code")
    _require_public_identifier(field_name, value)
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


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
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
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
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")
