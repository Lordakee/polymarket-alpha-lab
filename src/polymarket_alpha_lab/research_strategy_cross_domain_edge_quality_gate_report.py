"""Report-only cross-domain edge quality gate."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-cross-domain-edge-quality-gate-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_CROSS_DOMAIN_REVIEW_READY = "cross_domain_review_ready"
REASON_DOMAIN_DISAGREEMENT_OBSERVED = "domain_disagreement_observed"
REASON_SOURCE_INDEPENDENCE_REVIEW_REQUESTED = (
    "source_independence_review_requested"
)
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_EDGE_QUALITY_REVIEW_REQUESTED = "edge_quality_review_requested"
REASON_DOMAIN_SIGNAL_QUALITY_BLOCK = "domain_signal_quality_block"
REASON_DOMAIN_SIGNAL_QUALITY_WATCH = "domain_signal_quality_watch"
REASON_EVIDENCE_QUALITY_BLOCK = "evidence_quality_block"
REASON_EVIDENCE_QUALITY_WATCH = "evidence_quality_watch"
REASON_SOURCE_INDEPENDENCE_BLOCK = "source_independence_block"
REASON_SOURCE_INDEPENDENCE_WATCH = "source_independence_watch"
REASON_PROBABILITY_EDGE_BLOCK = "probability_edge_block"
REASON_PROBABILITY_EDGE_WATCH = "probability_edge_watch"
REASON_LIQUIDITY_QUALITY_BLOCK = "liquidity_quality_block"
REASON_LIQUIDITY_QUALITY_WATCH = "liquidity_quality_watch"
REASON_RESOLUTION_CLARITY_BLOCK = "resolution_clarity_block"
REASON_RESOLUTION_CLARITY_WATCH = "resolution_clarity_watch"
REASON_COST_DRAG_BLOCK = "cost_drag_block"
REASON_COST_DRAG_WATCH = "cost_drag_watch"
REASON_QUALITY_SCORE_BLOCK = "quality_score_block"
REASON_QUALITY_SCORE_WATCH = "quality_score_watch"
REASON_CROSS_DOMAIN_EDGE_QUALITY_GATE_PASS = (
    "cross_domain_edge_quality_gate_pass"
)

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_CROSS_DOMAIN_REVIEW_READY,
    REASON_DOMAIN_DISAGREEMENT_OBSERVED,
    REASON_SOURCE_INDEPENDENCE_REVIEW_REQUESTED,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_EDGE_QUALITY_REVIEW_REQUESTED,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_DOMAIN_SIGNAL_QUALITY_BLOCK,
    REASON_DOMAIN_SIGNAL_QUALITY_WATCH,
    REASON_EVIDENCE_QUALITY_BLOCK,
    REASON_EVIDENCE_QUALITY_WATCH,
    REASON_SOURCE_INDEPENDENCE_BLOCK,
    REASON_SOURCE_INDEPENDENCE_WATCH,
    REASON_PROBABILITY_EDGE_BLOCK,
    REASON_PROBABILITY_EDGE_WATCH,
    REASON_LIQUIDITY_QUALITY_BLOCK,
    REASON_LIQUIDITY_QUALITY_WATCH,
    REASON_RESOLUTION_CLARITY_BLOCK,
    REASON_RESOLUTION_CLARITY_WATCH,
    REASON_COST_DRAG_BLOCK,
    REASON_COST_DRAG_WATCH,
    REASON_QUALITY_SCORE_BLOCK,
    REASON_QUALITY_SCORE_WATCH,
    REASON_CROSS_DOMAIN_EDGE_QUALITY_GATE_PASS,
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
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
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
    "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategyCrossDomainEdgeQualityGateConfig",
    "ResearchStrategyCrossDomainEdgeQualityGateInput",
    "ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount",
    "ResearchStrategyCrossDomainEdgeQualityGateReport",
    "ResearchStrategyCrossDomainEdgeQualityGateRow",
    "build_research_strategy_cross_domain_edge_quality_gate_report",
    "research_strategy_cross_domain_edge_quality_gate_report_digest",
    "research_strategy_cross_domain_edge_quality_gate_report_payload",
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
class ResearchStrategyCrossDomainEdgeQualityGateConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION
    )
    pass_min_quality_score: Decimal = Decimal("0.800000")
    watch_min_quality_score: Decimal = Decimal("0.600000")
    min_pass_dimension_score: Decimal = Decimal("0.750000")
    min_watch_dimension_score: Decimal = Decimal("0.500000")
    max_pass_cost_drag_score: Decimal = Decimal("0.200000")
    max_watch_cost_drag_score: Decimal = Decimal("0.450000")
    domain_signal_weight: Decimal = Decimal("0.170000")
    evidence_quality_weight: Decimal = Decimal("0.180000")
    source_independence_weight: Decimal = Decimal("0.150000")
    probability_edge_weight: Decimal = Decimal("0.170000")
    liquidity_quality_weight: Decimal = Decimal("0.130000")
    resolution_clarity_weight: Decimal = Decimal("0.110000")
    cost_efficiency_weight: Decimal = Decimal("0.090000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossDomainEdgeQualityGateConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_quality_score",
            "watch_min_quality_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
            "domain_signal_weight",
            "evidence_quality_weight",
            "source_independence_weight",
            "probability_edge_weight",
            "liquidity_quality_weight",
            "resolution_clarity_weight",
            "cost_efficiency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_quality_score < self.watch_min_quality_score:
            raise ValueError(
                "pass_min_quality_score must be at least watch_min_quality_score",
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
            raise ValueError("cross-domain edge quality weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossDomainEdgeQualityGateInput(_FinalPublicDataclass):
    edge_item_ref: str
    domain_signal_score: Decimal
    evidence_quality_score: Decimal
    source_independence_score: Decimal
    probability_edge_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    cost_drag_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossDomainEdgeQualityGateInput,
            "input",
        )
        object.__setattr__(
            self,
            "edge_item_ref",
            _require_private_ref("edge_item_ref", self.edge_item_ref),
        )
        for field_name in (
            "domain_signal_score",
            "evidence_quality_score",
            "source_independence_score",
            "probability_edge_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "cost_drag_score",
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
class ResearchStrategyCrossDomainEdgeQualityGateRow(_FinalPublicDataclass):
    edge_item_digest: str
    domain_signal_score: Decimal
    evidence_quality_score: Decimal
    source_independence_score: Decimal
    probability_edge_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    quality_score: Decimal
    lowest_dimension_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyCrossDomainEdgeQualityGateConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyCrossDomainEdgeQualityGateConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainEdgeQualityGateRow, "row")
        object.__setattr__(
            self,
            "edge_item_digest",
            _require_private_digest("edge_item_digest", self.edge_item_digest),
        )
        for field_name in (
            "domain_signal_score",
            "evidence_quality_score",
            "source_independence_score",
            "probability_edge_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "cost_drag_score",
            "cost_efficiency_score",
            "quality_score",
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
class ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount,
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
class ResearchStrategyCrossDomainEdgeQualityGateReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quality_score: Decimal
    min_quality_score: Decimal
    min_domain_signal_score: Decimal
    min_evidence_quality_score: Decimal
    min_source_independence_score: Decimal
    min_probability_edge_score: Decimal
    min_liquidity_quality_score: Decimal
    min_resolution_clarity_score: Decimal
    max_cost_drag_score: Decimal
    rows: tuple[ResearchStrategyCrossDomainEdgeQualityGateRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainEdgeQualityGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION
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
            "average_quality_score",
            "min_quality_score",
            "min_domain_signal_score",
            "min_evidence_quality_score",
            "min_source_independence_score",
            "min_probability_edge_score",
            "min_liquidity_quality_score",
            "min_resolution_clarity_score",
            "max_cost_drag_score",
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
        return research_strategy_cross_domain_edge_quality_gate_report_payload(self)


def build_research_strategy_cross_domain_edge_quality_gate_report(
    inputs: Sequence[ResearchStrategyCrossDomainEdgeQualityGateInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig | None = None,
) -> ResearchStrategyCrossDomainEdgeQualityGateReport:
    """Build a deterministic, readonly cross-domain edge quality gate report."""

    cfg = config or ResearchStrategyCrossDomainEdgeQualityGateConfig()
    if type(cfg) is not ResearchStrategyCrossDomainEdgeQualityGateConfig:
        raise ValueError(
            "config must be a ResearchStrategyCrossDomainEdgeQualityGateConfig",
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
            ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    return ResearchStrategyCrossDomainEdgeQualityGateReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        average_quality_score=_average_ratio(tuple(row.quality_score for row in rows)),
        min_quality_score=min((row.quality_score for row in rows), default=_ZERO),
        min_domain_signal_score=min(
            (row.domain_signal_score for row in rows),
            default=_ZERO,
        ),
        min_evidence_quality_score=min(
            (row.evidence_quality_score for row in rows),
            default=_ZERO,
        ),
        min_source_independence_score=min(
            (row.source_independence_score for row in rows),
            default=_ZERO,
        ),
        min_probability_edge_score=min(
            (row.probability_edge_score for row in rows),
            default=_ZERO,
        ),
        min_liquidity_quality_score=min(
            (row.liquidity_quality_score for row in rows),
            default=_ZERO,
        ),
        min_resolution_clarity_score=min(
            (row.resolution_clarity_score for row in rows),
            default=_ZERO,
        ),
        max_cost_drag_score=max((row.cost_drag_score for row in rows), default=_ZERO),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_strategy_cross_domain_edge_quality_gate_report_payload(
    value: ResearchStrategyCrossDomainEdgeQualityGateReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyCrossDomainEdgeQualityGateReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyCrossDomainEdgeQualityGateReport or dict",
        )
    _validate_payload_statuses(payload)
    _validate_payload_phase_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def research_strategy_cross_domain_edge_quality_gate_report_digest(
    report: ResearchStrategyCrossDomainEdgeQualityGateReport,
) -> str:
    if type(report) is not ResearchStrategyCrossDomainEdgeQualityGateReport:
        raise ValueError(
            "report must be a ResearchStrategyCrossDomainEdgeQualityGateReport",
        )
    return _report_digest(report)


def _row_for_input(
    row: ResearchStrategyCrossDomainEdgeQualityGateInput,
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig,
) -> ResearchStrategyCrossDomainEdgeQualityGateRow:
    cost_efficiency_score = _inverse_ratio(row.cost_drag_score)
    quality_score = _quality_score(
        domain_signal_score=row.domain_signal_score,
        evidence_quality_score=row.evidence_quality_score,
        source_independence_score=row.source_independence_score,
        probability_edge_score=row.probability_edge_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        cost_efficiency_score=cost_efficiency_score,
        config=config,
    )
    lowest_dimension_score = min(
        row.domain_signal_score,
        row.evidence_quality_score,
        row.source_independence_score,
        row.probability_edge_score,
        row.liquidity_quality_score,
        row.resolution_clarity_score,
        cost_efficiency_score,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        domain_signal_score=row.domain_signal_score,
        evidence_quality_score=row.evidence_quality_score,
        source_independence_score=row.source_independence_score,
        probability_edge_score=row.probability_edge_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        cost_drag_score=row.cost_drag_score,
        quality_score=quality_score,
        config=config,
    )
    return ResearchStrategyCrossDomainEdgeQualityGateRow(
        edge_item_digest=_private_ref_digest(row.edge_item_ref),
        domain_signal_score=row.domain_signal_score,
        evidence_quality_score=row.evidence_quality_score,
        source_independence_score=row.source_independence_score,
        probability_edge_score=row.probability_edge_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        cost_drag_score=row.cost_drag_score,
        cost_efficiency_score=cost_efficiency_score,
        quality_score=quality_score,
        lowest_dimension_score=lowest_dimension_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    domain_signal_score: Decimal,
    evidence_quality_score: Decimal,
    source_independence_score: Decimal,
    probability_edge_score: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    cost_drag_score: Decimal,
    quality_score: Decimal,
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_DOMAIN_SIGNAL_QUALITY_BLOCK,
        watch_code=REASON_DOMAIN_SIGNAL_QUALITY_WATCH,
        value=domain_signal_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_EVIDENCE_QUALITY_BLOCK,
        watch_code=REASON_EVIDENCE_QUALITY_WATCH,
        value=evidence_quality_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_SOURCE_INDEPENDENCE_BLOCK,
        watch_code=REASON_SOURCE_INDEPENDENCE_WATCH,
        value=source_independence_score,
        config=config,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_PROBABILITY_EDGE_BLOCK,
        watch_code=REASON_PROBABILITY_EDGE_WATCH,
        value=probability_edge_score,
        config=config,
    )
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
    if cost_drag_score > config.max_watch_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_BLOCK)
    elif cost_drag_score > config.max_pass_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_WATCH)
    if quality_score < config.watch_min_quality_score:
        reason_codes.append(REASON_QUALITY_SCORE_BLOCK)
    elif quality_score < config.pass_min_quality_score:
        reason_codes.append(REASON_QUALITY_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_CROSS_DOMAIN_EDGE_QUALITY_GATE_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _append_dimension_reason(
    reason_codes: list[str],
    *,
    block_code: str,
    watch_code: str,
    value: Decimal,
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig,
) -> None:
    if value < config.min_watch_dimension_score:
        reason_codes.append(block_code)
    elif value < config.min_pass_dimension_score:
        reason_codes.append(watch_code)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_CROSS_DOMAIN_EDGE_QUALITY_GATE_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyCrossDomainEdgeQualityGateRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyCrossDomainEdgeQualityGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchStrategyCrossDomainEdgeQualityGateRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.quality_score, row.edge_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyCrossDomainEdgeQualityGateRow, ...],
) -> tuple[ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _quality_score(
    *,
    domain_signal_score: Decimal,
    evidence_quality_score: Decimal,
    source_independence_score: Decimal,
    probability_edge_score: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    cost_efficiency_score: Decimal,
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig,
) -> Decimal:
    score = (
        domain_signal_score * config.domain_signal_weight
        + evidence_quality_score * config.evidence_quality_weight
        + source_independence_score * config.source_independence_weight
        + probability_edge_score * config.probability_edge_weight
        + liquidity_quality_score * config.liquidity_quality_weight
        + resolution_clarity_score * config.resolution_clarity_weight
        + cost_efficiency_score * config.cost_efficiency_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyCrossDomainEdgeQualityGateRow,
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig | None,
) -> None:
    expected_lowest = min(
        row.domain_signal_score,
        row.evidence_quality_score,
        row.source_independence_score,
        row.probability_edge_score,
        row.liquidity_quality_score,
        row.resolution_clarity_score,
        row.cost_efficiency_score,
    )
    if row.cost_efficiency_score != _inverse_ratio(row.cost_drag_score):
        raise ValueError("cost_efficiency_score must match cost_drag_score")
    if row.lowest_dimension_score != expected_lowest:
        raise ValueError("lowest_dimension_score must match dimensions")
    if config is not None:
        if type(config) is not ResearchStrategyCrossDomainEdgeQualityGateConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyCrossDomainEdgeQualityGateConfig",
            )
        expected_quality = _quality_score(
            domain_signal_score=row.domain_signal_score,
            evidence_quality_score=row.evidence_quality_score,
            source_independence_score=row.source_independence_score,
            probability_edge_score=row.probability_edge_score,
            liquidity_quality_score=row.liquidity_quality_score,
            resolution_clarity_score=row.resolution_clarity_score,
            cost_efficiency_score=row.cost_efficiency_score,
            config=config,
        )
        if row.quality_score != expected_quality:
            raise ValueError("quality_score must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            domain_signal_score=row.domain_signal_score,
            evidence_quality_score=row.evidence_quality_score,
            source_independence_score=row.source_independence_score,
            probability_edge_score=row.probability_edge_score,
            liquidity_quality_score=row.liquidity_quality_score,
            resolution_clarity_score=row.resolution_clarity_score,
            cost_drag_score=row.cost_drag_score,
            quality_score=row.quality_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_CROSS_DOMAIN_EDGE_QUALITY_GATE_PASS in row.reason_codes
        and any(
            reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
            and reason_code != REASON_CROSS_DOMAIN_EDGE_QUALITY_GATE_PASS
            for reason_code in row.reason_codes
        )
    ):
        raise ValueError("reason_codes must not mix pass with risk reasons")


def _validate_report(report: ResearchStrategyCrossDomainEdgeQualityGateReport) -> None:
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
    if report.average_quality_score != _average_ratio(
        tuple(row.quality_score for row in report.rows),
    ):
        raise ValueError("average_quality_score must match rows")
    if report.min_quality_score != min(
        (row.quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_quality_score must match rows")
    if report.min_domain_signal_score != min(
        (row.domain_signal_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_domain_signal_score must match rows")
    if report.min_evidence_quality_score != min(
        (row.evidence_quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_quality_score must match rows")
    if report.min_source_independence_score != min(
        (row.source_independence_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_source_independence_score must match rows")
    if report.min_probability_edge_score != min(
        (row.probability_edge_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_probability_edge_score must match rows")
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
    if report.max_cost_drag_score != max(
        (row.cost_drag_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_drag_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = _normalize_report_reason_codes(
        tuple(row.reason_code for row in expected_counts),
    )
    if not report.rows:
        expected_counts = (
            ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount(
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
    inputs: Sequence[ResearchStrategyCrossDomainEdgeQualityGateInput],
) -> tuple[ResearchStrategyCrossDomainEdgeQualityGateInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainEdgeQualityGateInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCrossDomainEdgeQualityGateInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.edge_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by edge item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyCrossDomainEdgeQualityGateRow, ...],
) -> tuple[ResearchStrategyCrossDomainEdgeQualityGateRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainEdgeQualityGateRow:
            raise ValueError(
                "rows must contain ResearchStrategyCrossDomainEdgeQualityGateRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.edge_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique edge item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount, ...],
) -> tuple[ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    return normalized


def _normalize_upstream_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        allowed=_UPSTREAM_REASON_CODE_SEQUENCE,
        field_name="reason_codes",
    )


def _normalize_row_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        allowed=_ROW_REASON_CODE_SEQUENCE,
        field_name="reason_codes",
    )


def _normalize_report_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        allowed=_REPORT_REASON_CODE_SEQUENCE,
        field_name="reason_codes",
    )


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allowed: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, allowed)
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=allowed.index))


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public payload")
    return value


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                if item not in _STATUS_VALUES:
                    raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_phase_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in ("paper_only", "readonly", "report_only"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True")
        for item in value.values():
            _validate_payload_phase_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_phase_flags(item)


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    unsigned = dict(payload)
    unsigned[_DIGEST_FIELD] = ""
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), allow_nan=False)
    expected = sha256(encoded.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _report_payload(report: ResearchStrategyCrossDomainEdgeQualityGateReport) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchStrategyCrossDomainEdgeQualityGateReport) -> str:
    payload = _report_payload(report)
    payload[_DIGEST_FIELD] = ""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must use exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must use exact datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON value contains numeric value")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


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
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        if type(value) is not dict and not allow_json_containers:
            raise ValueError(f"{label} must use a plain dict")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public payload")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a private SHA-256 digest")
    return value


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(sum(values, _ZERO) / Decimal(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _config_weight_sum(
    config: ResearchStrategyCrossDomainEdgeQualityGateConfig,
) -> Decimal:
    return _quantize(
        sum(
            (getattr(config, field.name) for field in fields(config) if field.name.endswith("_weight")),
            _ZERO,
        ),
    )


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
