"""Pure report for source-backed thesis and liquidity-cost alignment."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_STATUSES",
    "ResearchStrategySourceLiquidityThesisAlignmentConfig",
    "ResearchStrategySourceLiquidityThesisAlignmentInput",
    "ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount",
    "ResearchStrategySourceLiquidityThesisAlignmentReport",
    "ResearchStrategySourceLiquidityThesisAlignmentRow",
    "build_research_strategy_source_liquidity_thesis_alignment_report",
    "research_strategy_source_liquidity_thesis_alignment_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "research-strategy-source-liquidity-thesis-alignment-report-v0"
)

RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_STATUSES = (
    "pass",
    "watch",
    "block",
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
TWO_RATIO = Decimal("2")
FOUR_RATIO = Decimal("4")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

EMPTY_REPORT_REASON_CODE = "empty_source_liquidity_thesis_alignment_inputs"
REPORT_PASS_REASON_CODE = "source_liquidity_thesis_alignment_pass"
REPORT_WATCH_REASON_CODE = "source_liquidity_thesis_alignment_watch"
REPORT_BLOCK_REASON_CODE = "source_liquidity_thesis_alignment_block"
ROW_PASS_REASON_CODE = "source_liquidity_thesis_alignment_gap_pass"
ROW_REASON_CODES = (
    "source_liquidity_thesis_alignment_gap_block",
    "source_liquidity_thesis_alignment_gap_watch",
    ROW_PASS_REASON_CODE,
    "source_freshness_block",
    "source_freshness_watch",
    "evidence_strength_block",
    "evidence_strength_watch",
    "market_divergence_block",
    "market_divergence_watch",
    "spread_depth_quality_block",
    "spread_depth_quality_watch",
    "fee_drag_block",
    "fee_drag_watch",
    "resolution_clarity_block",
    "resolution_clarity_watch",
    "specialist_memory_confidence_block",
    "specialist_memory_confidence_watch",
    "alignment_pressure_block",
    "alignment_pressure_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REPORT_REASON_CODE,
)
ROW_REASON_SEQUENCE = (
    (
        "source_liquidity_thesis_alignment_gap_block",
        "source_liquidity_thesis_alignment_gap_watch",
        ROW_PASS_REASON_CODE,
    ),
    ("source_freshness_block", "source_freshness_watch"),
    ("evidence_strength_block", "evidence_strength_watch"),
    ("market_divergence_block", "market_divergence_watch"),
    ("spread_depth_quality_block", "spread_depth_quality_watch"),
    ("fee_drag_block", "fee_drag_watch"),
    ("resolution_clarity_block", "resolution_clarity_watch"),
    (
        "specialist_memory_confidence_block",
        "specialist_memory_confidence_watch",
    ),
    ("alignment_pressure_block", "alignment_pressure_watch"),
)
UNSAFE_KEY_FRAGMENTS = (
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "dsn",
    "tab" + "le_name",
    "tok" + "en",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
    "li" + "ve",
)
UNSAFE_VALUE_FRAGMENTS = (
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "ques" + "tion:",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "://",
    "ht" + "tp:",
    "ht" + "tps:",
    "www.",
    "dsn=",
    "tab" + "le_name",
    "tok" + "en=",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
    "li" + "ve",
)
HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ResearchStrategySourceLiquidityThesisAlignmentConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    watch_alignment_gap: Decimal = Decimal("0.150000")
    block_alignment_gap: Decimal = Decimal("0.300000")
    watch_source_age_seconds: Decimal = Decimal("7200.000000")
    block_source_age_seconds: Decimal = Decimal("21600.000000")
    watch_evidence_strength_score: Decimal = Decimal("0.700000")
    block_evidence_strength_score: Decimal = Decimal("0.450000")
    watch_market_divergence_score: Decimal = Decimal("0.300000")
    block_market_divergence_score: Decimal = Decimal("0.600000")
    watch_spread_depth_quality_score: Decimal = Decimal("0.700000")
    block_spread_depth_quality_score: Decimal = Decimal("0.450000")
    watch_fee_drag_score: Decimal = Decimal("0.030000")
    block_fee_drag_score: Decimal = Decimal("0.060000")
    watch_resolution_clarity_score: Decimal = Decimal("0.700000")
    block_resolution_clarity_score: Decimal = Decimal("0.450000")
    watch_specialist_memory_confidence_score: Decimal = Decimal("0.700000")
    block_specialist_memory_confidence_score: Decimal = Decimal("0.450000")
    watch_alignment_pressure: Decimal = Decimal("0.350000")
    block_alignment_pressure: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceLiquidityThesisAlignmentConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_alignment_gap",
            "block_alignment_gap",
            "watch_evidence_strength_score",
            "block_evidence_strength_score",
            "watch_market_divergence_score",
            "block_market_divergence_score",
            "watch_spread_depth_quality_score",
            "block_spread_depth_quality_score",
            "watch_fee_drag_score",
            "block_fee_drag_score",
            "watch_resolution_clarity_score",
            "block_resolution_clarity_score",
            "watch_specialist_memory_confidence_score",
            "block_specialist_memory_confidence_score",
            "watch_alignment_pressure",
            "block_alignment_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_source_age_seconds", "block_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        _require_rising_threshold(
            "alignment_gap",
            self.watch_alignment_gap,
            self.block_alignment_gap,
        )
        _require_rising_threshold(
            "source_age_seconds",
            self.watch_source_age_seconds,
            self.block_source_age_seconds,
        )
        _require_falling_threshold(
            "evidence_strength_score",
            self.watch_evidence_strength_score,
            self.block_evidence_strength_score,
        )
        _require_rising_threshold(
            "market_divergence_score",
            self.watch_market_divergence_score,
            self.block_market_divergence_score,
        )
        _require_falling_threshold(
            "spread_depth_quality_score",
            self.watch_spread_depth_quality_score,
            self.block_spread_depth_quality_score,
        )
        _require_rising_threshold(
            "fee_drag_score",
            self.watch_fee_drag_score,
            self.block_fee_drag_score,
        )
        _require_falling_threshold(
            "resolution_clarity_score",
            self.watch_resolution_clarity_score,
            self.block_resolution_clarity_score,
        )
        _require_falling_threshold(
            "specialist_memory_confidence_score",
            self.watch_specialist_memory_confidence_score,
            self.block_specialist_memory_confidence_score,
        )
        _require_rising_threshold(
            "alignment_pressure",
            self.watch_alignment_pressure,
            self.block_alignment_pressure,
        )
        require_paper_only_flags(
            "ResearchStrategySourceLiquidityThesisAlignmentConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceLiquidityThesisAlignmentInput:
    public_thesis_key: str
    source_observed_at: datetime
    evidence_strength_score: Decimal
    market_divergence_score: Decimal
    spread_quality_score: Decimal
    depth_quality_score: Decimal
    fee_drag_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceLiquidityThesisAlignmentInput)
        object.__setattr__(
            self,
            "public_thesis_key",
            _require_safe_label("public_thesis_key", self.public_thesis_key),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "evidence_strength_score",
            "market_divergence_score",
            "spread_quality_score",
            "depth_quality_score",
            "fee_drag_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "ResearchStrategySourceLiquidityThesisAlignmentInput",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceLiquidityThesisAlignmentRow:
    rank: Decimal
    public_thesis_key: str
    status: str
    source_observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_score: Decimal
    evidence_strength_score: Decimal
    market_divergence_score: Decimal
    spread_quality_score: Decimal
    depth_quality_score: Decimal
    spread_depth_quality_score: Decimal
    fee_drag_score: Decimal
    liquidity_cost_quality_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    source_backed_thesis_quality_score: Decimal
    source_liquidity_alignment_gap: Decimal
    alignment_pressure: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceLiquidityThesisAlignmentRow)
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "public_thesis_key",
            _require_safe_label("public_thesis_key", self.public_thesis_key),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_STATUSES,
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_measure("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "source_freshness_score",
            "evidence_strength_score",
            "market_divergence_score",
            "spread_quality_score",
            "depth_quality_score",
            "spread_depth_quality_score",
            "fee_drag_score",
            "liquidity_cost_quality_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
            "source_backed_thesis_quality_score",
            "source_liquidity_alignment_gap",
            "alignment_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        _validate_row(self)
        require_paper_only_flags(
            "ResearchStrategySourceLiquidityThesisAlignmentRow",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount,
        )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        require_paper_only_flags(
            "ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategySourceLiquidityThesisAlignmentReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_backed_thesis_quality_score: Decimal
    average_liquidity_cost_quality_score: Decimal
    average_source_liquidity_alignment_gap: Decimal
    average_alignment_pressure: Decimal
    max_alignment_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceLiquidityThesisAlignmentReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_backed_thesis_quality_score",
            "average_liquidity_cost_quality_score",
            "average_source_liquidity_alignment_gap",
            "average_alignment_pressure",
            "max_alignment_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_SOURCE_LIQUIDITY_THESIS_ALIGNMENT_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_report_reason_code_sequence(self.reason_codes)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags(
            "ResearchStrategySourceLiquidityThesisAlignmentReport",
            self,
        )
        expected_digest = _report_public_payload_digest(self)
        if self.public_payload_digest:
            object.__setattr__(
                self,
                "public_payload_digest",
                _normalize_sha256("public_payload_digest", self.public_payload_digest),
            )
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report fields")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)


def build_research_strategy_source_liquidity_thesis_alignment_report(
    observations: tuple[ResearchStrategySourceLiquidityThesisAlignmentInput, ...]
    | list[ResearchStrategySourceLiquidityThesisAlignmentInput],
    *,
    config: ResearchStrategySourceLiquidityThesisAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySourceLiquidityThesisAlignmentReport:
    if type(config) is not ResearchStrategySourceLiquidityThesisAlignmentConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceLiquidityThesisAlignmentConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(row, config=config, generated_at=generated_at_utc) for row in inputs),
    )
    return ResearchStrategySourceLiquidityThesisAlignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_source_backed_thesis_quality_score=_average_field(
            rows,
            "source_backed_thesis_quality_score",
        ),
        average_liquidity_cost_quality_score=_average_field(
            rows,
            "liquidity_cost_quality_score",
        ),
        average_source_liquidity_alignment_gap=_average_field(
            rows,
            "source_liquidity_alignment_gap",
        ),
        average_alignment_pressure=_average_field(rows, "alignment_pressure"),
        max_alignment_pressure=_max_field(rows, "alignment_pressure"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_source_liquidity_thesis_alignment_report_payload(
    report: ResearchStrategySourceLiquidityThesisAlignmentReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySourceLiquidityThesisAlignmentReport:
        raise ValueError(
            "report must be a ResearchStrategySourceLiquidityThesisAlignmentReport",
        )
    require_paper_only_flags("report", report)
    _validate_report_public_payload_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
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


def _build_row(
    row: ResearchStrategySourceLiquidityThesisAlignmentInput,
    *,
    config: ResearchStrategySourceLiquidityThesisAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySourceLiquidityThesisAlignmentRow:
    source_age_seconds = _age_seconds(row.source_observed_at, generated_at)
    source_freshness_score = _remaining_ratio(
        source_age_seconds,
        config.block_source_age_seconds,
    )
    spread_depth_quality_score = _average_pair(
        row.spread_quality_score,
        row.depth_quality_score,
    )
    liquidity_cost_quality_score = _average_pair(
        spread_depth_quality_score,
        ONE_RATIO - row.fee_drag_score,
    )
    source_backed_thesis_quality_score = _source_backed_thesis_quality_score(
        source_freshness_score=source_freshness_score,
        evidence_strength_score=row.evidence_strength_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
    )
    source_liquidity_alignment_gap = _abs_decimal(
        source_backed_thesis_quality_score - liquidity_cost_quality_score,
    )
    source_liquidity_alignment_gap = _normalize_probability(
        "source_liquidity_alignment_gap",
        source_liquidity_alignment_gap,
    )
    alignment_pressure = _alignment_pressure(
        source_freshness_score=source_freshness_score,
        evidence_strength_score=row.evidence_strength_score,
        market_divergence_score=row.market_divergence_score,
        spread_depth_quality_score=spread_depth_quality_score,
        fee_drag_score=row.fee_drag_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        source_liquidity_alignment_gap=source_liquidity_alignment_gap,
    )
    reason_codes = _row_reason_codes(
        source_liquidity_alignment_gap=source_liquidity_alignment_gap,
        source_age_seconds=source_age_seconds,
        evidence_strength_score=row.evidence_strength_score,
        market_divergence_score=row.market_divergence_score,
        spread_depth_quality_score=spread_depth_quality_score,
        fee_drag_score=row.fee_drag_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        alignment_pressure=alignment_pressure,
        config=config,
    )
    return ResearchStrategySourceLiquidityThesisAlignmentRow(
        rank=COUNT_QUANTUM,
        public_thesis_key=row.public_thesis_key,
        status=_status_from_reason_codes(reason_codes),
        source_observed_at=row.source_observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_score=source_freshness_score,
        evidence_strength_score=row.evidence_strength_score,
        market_divergence_score=row.market_divergence_score,
        spread_quality_score=row.spread_quality_score,
        depth_quality_score=row.depth_quality_score,
        spread_depth_quality_score=spread_depth_quality_score,
        fee_drag_score=row.fee_drag_score,
        liquidity_cost_quality_score=liquidity_cost_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        source_backed_thesis_quality_score=source_backed_thesis_quality_score,
        source_liquidity_alignment_gap=source_liquidity_alignment_gap,
        alignment_pressure=alignment_pressure,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
) -> tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...]:
    return tuple(
        ResearchStrategySourceLiquidityThesisAlignmentRow(
            rank=_count(index),
            public_thesis_key=row.public_thesis_key,
            status=row.status,
            source_observed_at=row.source_observed_at,
            source_age_seconds=row.source_age_seconds,
            source_freshness_score=row.source_freshness_score,
            evidence_strength_score=row.evidence_strength_score,
            market_divergence_score=row.market_divergence_score,
            spread_quality_score=row.spread_quality_score,
            depth_quality_score=row.depth_quality_score,
            spread_depth_quality_score=row.spread_depth_quality_score,
            fee_drag_score=row.fee_drag_score,
            liquidity_cost_quality_score=row.liquidity_cost_quality_score,
            resolution_clarity_score=row.resolution_clarity_score,
            specialist_memory_confidence_score=row.specialist_memory_confidence_score,
            source_backed_thesis_quality_score=row.source_backed_thesis_quality_score,
            source_liquidity_alignment_gap=row.source_liquidity_alignment_gap,
            alignment_pressure=row.alignment_pressure,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    source_liquidity_alignment_gap: Decimal,
    source_age_seconds: Decimal,
    evidence_strength_score: Decimal,
    market_divergence_score: Decimal,
    spread_depth_quality_score: Decimal,
    fee_drag_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
    alignment_pressure: Decimal,
    config: ResearchStrategySourceLiquidityThesisAlignmentConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_liquidity_alignment_gap >= config.block_alignment_gap:
        reason_codes.append("source_liquidity_thesis_alignment_gap_block")
    elif source_liquidity_alignment_gap >= config.watch_alignment_gap:
        reason_codes.append("source_liquidity_thesis_alignment_gap_watch")
    else:
        reason_codes.append(ROW_PASS_REASON_CODE)
    if source_age_seconds >= config.block_source_age_seconds:
        reason_codes.append("source_freshness_block")
    elif source_age_seconds >= config.watch_source_age_seconds:
        reason_codes.append("source_freshness_watch")
    if evidence_strength_score <= config.block_evidence_strength_score:
        reason_codes.append("evidence_strength_block")
    elif evidence_strength_score <= config.watch_evidence_strength_score:
        reason_codes.append("evidence_strength_watch")
    if market_divergence_score >= config.block_market_divergence_score:
        reason_codes.append("market_divergence_block")
    elif market_divergence_score >= config.watch_market_divergence_score:
        reason_codes.append("market_divergence_watch")
    if spread_depth_quality_score <= config.block_spread_depth_quality_score:
        reason_codes.append("spread_depth_quality_block")
    elif spread_depth_quality_score <= config.watch_spread_depth_quality_score:
        reason_codes.append("spread_depth_quality_watch")
    if fee_drag_score >= config.block_fee_drag_score:
        reason_codes.append("fee_drag_block")
    elif fee_drag_score >= config.watch_fee_drag_score:
        reason_codes.append("fee_drag_watch")
    if resolution_clarity_score <= config.block_resolution_clarity_score:
        reason_codes.append("resolution_clarity_block")
    elif resolution_clarity_score <= config.watch_resolution_clarity_score:
        reason_codes.append("resolution_clarity_watch")
    if specialist_memory_confidence_score <= config.block_specialist_memory_confidence_score:
        reason_codes.append("specialist_memory_confidence_block")
    elif specialist_memory_confidence_score <= config.watch_specialist_memory_confidence_score:
        reason_codes.append("specialist_memory_confidence_watch")
    if alignment_pressure >= config.block_alignment_pressure:
        reason_codes.append("alignment_pressure_block")
    elif alignment_pressure >= config.watch_alignment_pressure:
        reason_codes.append("alignment_pressure_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _normalize_inputs(
    value: tuple[ResearchStrategySourceLiquidityThesisAlignmentInput, ...]
    | list[ResearchStrategySourceLiquidityThesisAlignmentInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategySourceLiquidityThesisAlignmentInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategySourceLiquidityThesisAlignmentInput:
            raise ValueError(
                "observations must contain ResearchStrategySourceLiquidityThesisAlignmentInput values",
            )
        require_paper_only_flags("observation", row)
        if row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
    return rows


def _normalize_rows(
    value: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
) -> tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategySourceLiquidityThesisAlignmentRow:
            raise ValueError("rows must contain alignment row values")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: tuple[ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount, ...],
) -> tuple[ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        require_paper_only_flags("reason_code_count", row)
    expected = tuple(sorted(rows, key=lambda row: _row_reason_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for row in rows:
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
) -> tuple[ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategySourceLiquidityThesisAlignmentReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counter
    )


def _validate_row(row: ResearchStrategySourceLiquidityThesisAlignmentRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.spread_depth_quality_score != _average_pair(
        row.spread_quality_score,
        row.depth_quality_score,
    ):
        raise ValueError("spread_depth_quality_score must match row fields")
    if row.liquidity_cost_quality_score != _average_pair(
        row.spread_depth_quality_score,
        ONE_RATIO - row.fee_drag_score,
    ):
        raise ValueError("liquidity_cost_quality_score must match row fields")
    expected_thesis_quality = _source_backed_thesis_quality_score(
        source_freshness_score=row.source_freshness_score,
        evidence_strength_score=row.evidence_strength_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
    )
    if row.source_backed_thesis_quality_score != expected_thesis_quality:
        raise ValueError("source_backed_thesis_quality_score must match row fields")
    expected_gap = _normalize_probability(
        "source_liquidity_alignment_gap",
        _abs_decimal(
            row.source_backed_thesis_quality_score - row.liquidity_cost_quality_score,
        ),
    )
    if row.source_liquidity_alignment_gap != expected_gap:
        raise ValueError("source_liquidity_alignment_gap must match row fields")
    expected_pressure = _alignment_pressure(
        source_freshness_score=row.source_freshness_score,
        evidence_strength_score=row.evidence_strength_score,
        market_divergence_score=row.market_divergence_score,
        spread_depth_quality_score=row.spread_depth_quality_score,
        fee_drag_score=row.fee_drag_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        source_liquidity_alignment_gap=row.source_liquidity_alignment_gap,
    )
    if row.alignment_pressure != expected_pressure:
        raise ValueError("alignment_pressure must match row fields")


def _validate_report(report: ResearchStrategySourceLiquidityThesisAlignmentReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    field_pairs = (
        (
            "average_source_backed_thesis_quality_score",
            "source_backed_thesis_quality_score",
        ),
        ("average_liquidity_cost_quality_score", "liquidity_cost_quality_score"),
        (
            "average_source_liquidity_alignment_gap",
            "source_liquidity_alignment_gap",
        ),
        ("average_alignment_pressure", "alignment_pressure"),
    )
    for report_field_name, row_field_name in field_pairs:
        if getattr(report, report_field_name) != _average_field(rows, row_field_name):
            raise ValueError(f"{report_field_name} must match rows")
    if report.max_alignment_pressure != _max_field(rows, "alignment_pressure"):
        raise ValueError("max_alignment_pressure must match rows")
    if report.status != _status_rollup(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_public_payload_digest(
    report: ResearchStrategySourceLiquidityThesisAlignmentReport,
) -> None:
    _normalize_sha256("public_payload_digest", report.public_payload_digest)
    if report.public_payload_digest != _report_public_payload_digest(report):
        raise ValueError("public_payload_digest must match report fields")


def _report_public_payload_digest(
    report: ResearchStrategySourceLiquidityThesisAlignmentReport,
) -> str:
    payload = asdict(report)
    payload.pop("public_payload_digest", None)
    ready = _json_ready(payload)
    _reject_unsafe_public_payload("digest_payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_backed_thesis_quality_score(
    *,
    source_freshness_score: Decimal,
    evidence_strength_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "source_backed_thesis_quality_score",
            (
                source_freshness_score
                + evidence_strength_score
                + resolution_clarity_score
                + specialist_memory_confidence_score
            )
            / FOUR_RATIO,
        )


def _alignment_pressure(
    *,
    source_freshness_score: Decimal,
    evidence_strength_score: Decimal,
    market_divergence_score: Decimal,
    spread_depth_quality_score: Decimal,
    fee_drag_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
    source_liquidity_alignment_gap: Decimal,
) -> Decimal:
    return _normalize_probability(
        "alignment_pressure",
        max(
            source_liquidity_alignment_gap,
            ONE_RATIO - source_freshness_score,
            ONE_RATIO - evidence_strength_score,
            market_divergence_score,
            ONE_RATIO - spread_depth_quality_score,
            fee_drag_score,
            ONE_RATIO - resolution_clarity_score,
            ONE_RATIO - specialist_memory_confidence_score,
        ),
    )


def _average_pair(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("average_pair", (left + right) / TWO_RATIO)


def _status_count(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            field_name,
            sum((getattr(row, field_name) for row in rows), ZERO_RATIO)
            / Decimal(len(rows)),
        )


def _max_field(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(getattr(row, field_name) for row in rows)


def _status_rollup(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceLiquidityThesisAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _status_rollup(rows)
    codes = [_report_status_reason_code(status)]
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status_reason_code(status: str) -> str:
    if status == BLOCK_STATUS:
        return REPORT_BLOCK_REASON_CODE
    if status == WATCH_STATUS:
        return REPORT_WATCH_REASON_CODE
    return REPORT_PASS_REASON_CODE


def _row_sort_key(
    row: ResearchStrategySourceLiquidityThesisAlignmentRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.alignment_pressure,
        -row.source_liquidity_alignment_gap,
        row.source_backed_thesis_quality_score,
        row.liquidity_cost_quality_score,
        row.public_thesis_key,
    )


def _row_reason_rank(reason_code: str) -> int:
    return ROW_REASON_CODES.index(reason_code)


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    expected = tuple(
        reason_code
        for group in ROW_REASON_SEQUENCE
        for reason_code in group
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    gap_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code
        in (
            "source_liquidity_thesis_alignment_gap_block",
            "source_liquidity_thesis_alignment_gap_watch",
            ROW_PASS_REASON_CODE,
        )
    )
    if len(gap_reasons) != 1:
        raise ValueError("reason_codes must include exactly one alignment reason")


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(value)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    for code in codes:
        _require_member(name, code, allowed)
    return codes


def _age_seconds(
    older_at: datetime,
    newer_at: datetime,
) -> Decimal:
    older = _as_utc("source_observed_at", older_at)
    newer = _as_utc("generated_at", newer_at)
    if older > newer:
        raise ValueError("source_observed_at must not be after generated_at")
    delta = newer - older
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _normalize_nonnegative_measure("source_age_seconds", seconds)


def _remaining_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO_RATIO:
        raise ValueError("ratio limit must be positive")
    if value >= limit:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("remaining_ratio", ONE_RATIO - (value / limit))


def _require_rising_threshold(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"watch_{name} must not exceed block_{name}")


def _require_falling_threshold(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value < block_value:
        raise ValueError(f"watch_{name} must not be below block_{name}")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{expected_type.__name__} subclasses are not supported")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonblank trimmed string")


def _require_safe_label(name: str, value: object) -> str:
    _require_public_string(name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{name} must not expose restricted references")
    return value


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO or decimal > ONE_RATIO:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_measure(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal.quantize(COUNT_QUANTUM)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(name, value)
    if count <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return count


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO_RATIO else value


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 string")
    return value


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_KEY_FRAGMENTS):
                raise ValueError(f"{context} contains restricted key")
            _reject_unsafe_public_payload(f"{context}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(context, item)
    elif type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"{context} contains restricted value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
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
