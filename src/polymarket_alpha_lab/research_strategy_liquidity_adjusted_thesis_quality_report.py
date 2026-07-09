"""Report-only liquidity-adjusted thesis quality scoring."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_CONFIG_VERSION = (
    "research-strategy-liquidity-adjusted-thesis-quality-report-v0"
)

RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_STATUSES = (
    "pass",
    "watch",
    "block",
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUS_SORT_RANK = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EMPTY_REASON_CODE = "no_liquidity_adjusted_thesis_quality_inputs"
REPORT_PASS_REASON_CODE = "liquidity_adjusted_thesis_quality_report_pass"
REPORT_WATCH_REASON_CODE = "liquidity_adjusted_thesis_quality_report_watch"
REPORT_BLOCK_REASON_CODE = "liquidity_adjusted_thesis_quality_report_block"
QUALITY_PASS_REASON_CODE = "liquidity_adjusted_thesis_quality_pass"
QUALITY_WATCH_REASON_CODE = "liquidity_adjusted_thesis_quality_watch"
QUALITY_BLOCK_REASON_CODE = "liquidity_adjusted_thesis_quality_block"

STATUS_REASON_CODES = (
    QUALITY_BLOCK_REASON_CODE,
    QUALITY_WATCH_REASON_CODE,
    QUALITY_PASS_REASON_CODE,
)
ROW_REASON_CODES = (
    QUALITY_BLOCK_REASON_CODE,
    QUALITY_WATCH_REASON_CODE,
    QUALITY_PASS_REASON_CODE,
    "source_freshness_block",
    "source_freshness_watch",
    "evidence_strength_block",
    "evidence_strength_watch",
    "model_market_divergence_block",
    "model_market_divergence_watch",
    "spread_depth_quality_block",
    "spread_depth_quality_watch",
    "fee_drag_block",
    "fee_drag_watch",
    "resolution_clarity_block",
    "resolution_clarity_watch",
    "specialist_memory_confidence_block",
    "specialist_memory_confidence_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    EMPTY_REASON_CODE,
    *ROW_REASON_CODES,
)
ROW_REASON_SEQUENCE = (
    (
        QUALITY_BLOCK_REASON_CODE,
        QUALITY_WATCH_REASON_CODE,
        QUALITY_PASS_REASON_CODE,
    ),
    ("source_freshness_block", "source_freshness_watch"),
    ("evidence_strength_block", "evidence_strength_watch"),
    ("model_market_divergence_block", "model_market_divergence_watch"),
    ("spread_depth_quality_block", "spread_depth_quality_watch"),
    ("fee_drag_block", "fee_drag_watch"),
    ("resolution_clarity_block", "resolution_clarity_watch"),
    (
        "specialist_memory_confidence_block",
        "specialist_memory_confidence_watch",
    ),
)
REASON_CODE_SET = frozenset(REPORT_REASON_CODES)
HEX_CHARS = frozenset("0123456789abcdef")
PUBLIC_THESIS_KEY_RE = re.compile(r"thesis-[a-z][a-z0-9_]{0,63}")
RAW_THESIS_IDENTIFIER_RE = re.compile(
    r"thesis-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
)

UNSAFE_REFERENCE_FRAGMENTS = (
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
    "dsn",
    "tab" + "le_name",
    "tok" + "en",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
    "li" + "ve",
    "buy",
    "sell",
    "reco" + "mmend",
    "pos" + "ition",
    "siz" + "ing",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_CONFIG_VERSION",
    "RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_STATUSES",
    "ResearchStrategyLiquidityAdjustedThesisQualityConfig",
    "ResearchStrategyLiquidityAdjustedThesisQualityInput",
    "ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount",
    "ResearchStrategyLiquidityAdjustedThesisQualityReport",
    "ResearchStrategyLiquidityAdjustedThesisQualityRow",
    "build_research_strategy_liquidity_adjusted_thesis_quality_report",
    "research_strategy_liquidity_adjusted_thesis_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyLiquidityAdjustedThesisQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_CONFIG_VERSION
    )
    watch_quality_score: Decimal = Decimal("0.650000")
    block_quality_score: Decimal = Decimal("0.300000")
    watch_source_age_seconds: Decimal = Decimal("7200.000000")
    block_source_age_seconds: Decimal = Decimal("21600.000000")
    watch_evidence_strength_score: Decimal = Decimal("0.700000")
    block_evidence_strength_score: Decimal = Decimal("0.450000")
    watch_model_market_divergence_score: Decimal = Decimal("0.300000")
    block_model_market_divergence_score: Decimal = Decimal("0.600000")
    watch_spread_depth_quality_score: Decimal = Decimal("0.700000")
    block_spread_depth_quality_score: Decimal = Decimal("0.450000")
    watch_fee_drag_score: Decimal = Decimal("0.030000")
    block_fee_drag_score: Decimal = Decimal("0.060000")
    watch_resolution_clarity_score: Decimal = Decimal("0.700000")
    block_resolution_clarity_score: Decimal = Decimal("0.450000")
    watch_specialist_memory_confidence_score: Decimal = Decimal("0.700000")
    block_specialist_memory_confidence_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyLiquidityAdjustedThesisQualityConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_quality_score",
            "block_quality_score",
            "watch_evidence_strength_score",
            "block_evidence_strength_score",
            "watch_model_market_divergence_score",
            "block_model_market_divergence_score",
            "watch_spread_depth_quality_score",
            "block_spread_depth_quality_score",
            "watch_fee_drag_score",
            "block_fee_drag_score",
            "watch_resolution_clarity_score",
            "block_resolution_clarity_score",
            "watch_specialist_memory_confidence_score",
            "block_specialist_memory_confidence_score",
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
        _require_falling_threshold(
            "watch_quality_score",
            self.watch_quality_score,
            "block_quality_score",
            self.block_quality_score,
        )
        _require_rising_threshold(
            "watch_source_age_seconds",
            self.watch_source_age_seconds,
            "block_source_age_seconds",
            self.block_source_age_seconds,
        )
        _require_falling_threshold(
            "watch_evidence_strength_score",
            self.watch_evidence_strength_score,
            "block_evidence_strength_score",
            self.block_evidence_strength_score,
        )
        _require_rising_threshold(
            "watch_model_market_divergence_score",
            self.watch_model_market_divergence_score,
            "block_model_market_divergence_score",
            self.block_model_market_divergence_score,
        )
        _require_falling_threshold(
            "watch_spread_depth_quality_score",
            self.watch_spread_depth_quality_score,
            "block_spread_depth_quality_score",
            self.block_spread_depth_quality_score,
        )
        _require_rising_threshold(
            "watch_fee_drag_score",
            self.watch_fee_drag_score,
            "block_fee_drag_score",
            self.block_fee_drag_score,
        )
        _require_falling_threshold(
            "watch_resolution_clarity_score",
            self.watch_resolution_clarity_score,
            "block_resolution_clarity_score",
            self.block_resolution_clarity_score,
        )
        _require_falling_threshold(
            "watch_specialist_memory_confidence_score",
            self.watch_specialist_memory_confidence_score,
            "block_specialist_memory_confidence_score",
            self.block_specialist_memory_confidence_score,
        )
        require_paper_only_flags(
            "ResearchStrategyLiquidityAdjustedThesisQualityConfig",
            self,
        )
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyLiquidityAdjustedThesisQualityInput:
    public_thesis_key: str
    source_observed_at: datetime
    evidence_strength_score: Decimal
    model_market_divergence_score: Decimal
    spread_quality_score: Decimal
    depth_quality_score: Decimal
    fee_drag_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyLiquidityAdjustedThesisQualityInput)
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
            "model_market_divergence_score",
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
            "ResearchStrategyLiquidityAdjustedThesisQualityInput",
            self,
        )
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyLiquidityAdjustedThesisQualityRow:
    rank: Decimal
    public_thesis_key: str
    status: str
    source_observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_score: Decimal
    evidence_strength_score: Decimal
    model_market_divergence_score: Decimal
    model_market_convergence_score: Decimal
    spread_quality_score: Decimal
    depth_quality_score: Decimal
    spread_depth_quality_score: Decimal
    fee_drag_score: Decimal
    liquidity_cost_quality_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    source_backed_thesis_quality_score: Decimal
    liquidity_adjusted_thesis_quality_score: Decimal
    liquidity_adjustment_drag: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyLiquidityAdjustedThesisQualityRow)
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "public_thesis_key",
            _require_safe_label("public_thesis_key", self.public_thesis_key),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_STATUSES,
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
            "model_market_divergence_score",
            "model_market_convergence_score",
            "spread_quality_score",
            "depth_quality_score",
            "spread_depth_quality_score",
            "fee_drag_score",
            "liquidity_cost_quality_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
            "source_backed_thesis_quality_score",
            "liquidity_adjusted_thesis_quality_score",
            "liquidity_adjustment_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        _validate_row(self)
        require_paper_only_flags(
            "ResearchStrategyLiquidityAdjustedThesisQualityRow",
            self,
        )
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount,
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        require_paper_only_flags(
            "ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount",
            self,
        )
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyLiquidityAdjustedThesisQualityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_backed_thesis_quality_score: Decimal
    average_liquidity_cost_quality_score: Decimal
    average_liquidity_adjusted_thesis_quality_score: Decimal
    average_liquidity_adjustment_drag: Decimal
    max_liquidity_adjustment_drag: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyLiquidityAdjustedThesisQualityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_CONFIG_VERSION
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
            "average_liquidity_adjusted_thesis_quality_score",
            "average_liquidity_adjustment_drag",
            "max_liquidity_adjustment_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_LIQUIDITY_ADJUSTED_THESIS_QUALITY_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags(
            "ResearchStrategyLiquidityAdjustedThesisQualityReport",
            self,
        )
        _reject_unsafe_public_payload("report", self)
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


def build_research_strategy_liquidity_adjusted_thesis_quality_report(
    observations: Iterable[ResearchStrategyLiquidityAdjustedThesisQualityInput],
    *,
    config: ResearchStrategyLiquidityAdjustedThesisQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyLiquidityAdjustedThesisQualityReport:
    if type(config) is not ResearchStrategyLiquidityAdjustedThesisQualityConfig:
        raise ValueError(
            "config must be a ResearchStrategyLiquidityAdjustedThesisQualityConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(row, config=config, generated_at=generated_at_utc) for row in inputs),
    )
    return ResearchStrategyLiquidityAdjustedThesisQualityReport(
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
        average_liquidity_adjusted_thesis_quality_score=_average_field(
            rows,
            "liquidity_adjusted_thesis_quality_score",
        ),
        average_liquidity_adjustment_drag=_average_field(
            rows,
            "liquidity_adjustment_drag",
        ),
        max_liquidity_adjustment_drag=_max_field(rows, "liquidity_adjustment_drag"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_liquidity_adjusted_thesis_quality_report_payload(
    report: ResearchStrategyLiquidityAdjustedThesisQualityReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchStrategyLiquidityAdjustedThesisQualityReport:
        raise ValueError(
            "report must be a ResearchStrategyLiquidityAdjustedThesisQualityReport",
        )
    require_paper_only_flags("report", report)
    _validate_report_public_payload_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


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
    row: ResearchStrategyLiquidityAdjustedThesisQualityInput,
    *,
    config: ResearchStrategyLiquidityAdjustedThesisQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyLiquidityAdjustedThesisQualityRow:
    source_age_seconds = _age_seconds(row.source_observed_at, generated_at)
    source_freshness_score = _remaining_ratio(
        source_age_seconds,
        config.block_source_age_seconds,
    )
    model_market_convergence_score = ONE_RATIO - row.model_market_divergence_score
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
        model_market_convergence_score=model_market_convergence_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
    )
    liquidity_adjusted_thesis_quality_score = _normalize_probability(
        "liquidity_adjusted_thesis_quality_score",
        source_backed_thesis_quality_score * liquidity_cost_quality_score,
    )
    liquidity_adjustment_drag = _normalize_probability(
        "liquidity_adjustment_drag",
        source_backed_thesis_quality_score - liquidity_adjusted_thesis_quality_score,
    )
    reason_codes = _row_reason_codes(
        config=config,
        source_age_seconds=source_age_seconds,
        evidence_strength_score=row.evidence_strength_score,
        model_market_divergence_score=row.model_market_divergence_score,
        spread_depth_quality_score=spread_depth_quality_score,
        fee_drag_score=row.fee_drag_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        liquidity_adjusted_thesis_quality_score=liquidity_adjusted_thesis_quality_score,
    )
    return ResearchStrategyLiquidityAdjustedThesisQualityRow(
        rank=_count(1),
        public_thesis_key=row.public_thesis_key,
        status=_status_from_reason_codes(reason_codes),
        source_observed_at=row.source_observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_score=source_freshness_score,
        evidence_strength_score=row.evidence_strength_score,
        model_market_divergence_score=row.model_market_divergence_score,
        model_market_convergence_score=model_market_convergence_score,
        spread_quality_score=row.spread_quality_score,
        depth_quality_score=row.depth_quality_score,
        spread_depth_quality_score=spread_depth_quality_score,
        fee_drag_score=row.fee_drag_score,
        liquidity_cost_quality_score=liquidity_cost_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        source_backed_thesis_quality_score=source_backed_thesis_quality_score,
        liquidity_adjusted_thesis_quality_score=liquidity_adjusted_thesis_quality_score,
        liquidity_adjustment_drag=liquidity_adjustment_drag,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    config: ResearchStrategyLiquidityAdjustedThesisQualityConfig,
    source_age_seconds: Decimal,
    evidence_strength_score: Decimal,
    model_market_divergence_score: Decimal,
    spread_depth_quality_score: Decimal,
    fee_drag_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
    liquidity_adjusted_thesis_quality_score: Decimal,
) -> tuple[str, ...]:
    details: list[str] = []
    severity = PASS_STATUS
    severity = _combine_severity(
        severity,
        _falling_threshold_status(
            liquidity_adjusted_thesis_quality_score,
            config.watch_quality_score,
            config.block_quality_score,
        ),
    )
    freshness_status = _rising_threshold_status(
        source_age_seconds,
        config.watch_source_age_seconds,
        config.block_source_age_seconds,
    )
    severity = _combine_severity(severity, freshness_status)
    if freshness_status == BLOCK_STATUS:
        details.append("source_freshness_block")
    elif freshness_status == WATCH_STATUS:
        details.append("source_freshness_watch")

    evidence_status = _falling_threshold_status(
        evidence_strength_score,
        config.watch_evidence_strength_score,
        config.block_evidence_strength_score,
    )
    severity = _combine_severity(severity, evidence_status)
    if evidence_status == BLOCK_STATUS:
        details.append("evidence_strength_block")
    elif evidence_status == WATCH_STATUS:
        details.append("evidence_strength_watch")

    divergence_status = _rising_threshold_status(
        model_market_divergence_score,
        config.watch_model_market_divergence_score,
        config.block_model_market_divergence_score,
    )
    severity = _combine_severity(severity, divergence_status)
    if divergence_status == BLOCK_STATUS:
        details.append("model_market_divergence_block")
    elif divergence_status == WATCH_STATUS:
        details.append("model_market_divergence_watch")

    spread_depth_status = _falling_threshold_status(
        spread_depth_quality_score,
        config.watch_spread_depth_quality_score,
        config.block_spread_depth_quality_score,
    )
    severity = _combine_severity(severity, spread_depth_status)
    if spread_depth_status == BLOCK_STATUS:
        details.append("spread_depth_quality_block")
    elif spread_depth_status == WATCH_STATUS:
        details.append("spread_depth_quality_watch")

    fee_status = _rising_threshold_status(
        fee_drag_score,
        config.watch_fee_drag_score,
        config.block_fee_drag_score,
    )
    severity = _combine_severity(severity, fee_status)
    if fee_status == BLOCK_STATUS:
        details.append("fee_drag_block")
    elif fee_status == WATCH_STATUS:
        details.append("fee_drag_watch")

    resolution_status = _falling_threshold_status(
        resolution_clarity_score,
        config.watch_resolution_clarity_score,
        config.block_resolution_clarity_score,
    )
    severity = _combine_severity(severity, resolution_status)
    if resolution_status == BLOCK_STATUS:
        details.append("resolution_clarity_block")
    elif resolution_status == WATCH_STATUS:
        details.append("resolution_clarity_watch")

    specialist_status = _falling_threshold_status(
        specialist_memory_confidence_score,
        config.watch_specialist_memory_confidence_score,
        config.block_specialist_memory_confidence_score,
    )
    severity = _combine_severity(severity, specialist_status)
    if specialist_status == BLOCK_STATUS:
        details.append("specialist_memory_confidence_block")
    elif specialist_status == WATCH_STATUS:
        details.append("specialist_memory_confidence_watch")

    if severity == BLOCK_STATUS:
        return (QUALITY_BLOCK_REASON_CODE, *details)
    if severity == WATCH_STATUS:
        return (QUALITY_WATCH_REASON_CODE, *details)
    return (QUALITY_PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == QUALITY_BLOCK_REASON_CODE:
        return BLOCK_STATUS
    if reason_codes[0] == QUALITY_WATCH_REASON_CODE:
        return WATCH_STATUS
    return PASS_STATUS


def _status_rollup(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
) -> str:
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    if rows:
        return PASS_STATUS
    return BLOCK_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    status = _status_rollup(rows)
    if status == BLOCK_STATUS:
        return (REPORT_BLOCK_REASON_CODE,)
    if status == WATCH_STATUS:
        return (REPORT_WATCH_REASON_CODE,)
    return (REPORT_PASS_REASON_CODE,)


def _normalize_inputs(
    rows: Iterable[ResearchStrategyLiquidityAdjustedThesisQualityInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyLiquidityAdjustedThesisQualityInput, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("observations must be an iterable of inputs")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyLiquidityAdjustedThesisQualityInput:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyLiquidityAdjustedThesisQualityInput",
            )
        require_paper_only_flags("input", row)
        if row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        if row.public_thesis_key in seen_keys:
            raise ValueError("public_thesis_key values must be unique")
        seen_keys.add(row.public_thesis_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyLiquidityAdjustedThesisQualityRow:
            raise ValueError(
                "rows must contain ResearchStrategyLiquidityAdjustedThesisQualityRow",
            )
        require_paper_only_flags("row", row)
        if row.public_thesis_key in seen_keys:
            raise ValueError("rows public_thesis_key values must be unique")
        seen_keys.add(row.public_thesis_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    for index, row in enumerate(normalized, start=1):
        if row.rank != _count(index):
            raise ValueError("rows rank values must be sequential")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount",
            )
        require_paper_only_flags("reason_code_count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _rank_rows(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
) -> tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...]:
    ranked_rows = []
    for rank, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked_rows.append(
            ResearchStrategyLiquidityAdjustedThesisQualityRow(
                rank=_count(rank),
                public_thesis_key=row.public_thesis_key,
                status=row.status,
                source_observed_at=row.source_observed_at,
                source_age_seconds=row.source_age_seconds,
                source_freshness_score=row.source_freshness_score,
                evidence_strength_score=row.evidence_strength_score,
                model_market_divergence_score=row.model_market_divergence_score,
                model_market_convergence_score=row.model_market_convergence_score,
                spread_quality_score=row.spread_quality_score,
                depth_quality_score=row.depth_quality_score,
                spread_depth_quality_score=row.spread_depth_quality_score,
                fee_drag_score=row.fee_drag_score,
                liquidity_cost_quality_score=row.liquidity_cost_quality_score,
                resolution_clarity_score=row.resolution_clarity_score,
                specialist_memory_confidence_score=(
                    row.specialist_memory_confidence_score
                ),
                source_backed_thesis_quality_score=(
                    row.source_backed_thesis_quality_score
                ),
                liquidity_adjusted_thesis_quality_score=(
                    row.liquidity_adjusted_thesis_quality_score
                ),
                liquidity_adjustment_drag=row.liquidity_adjustment_drag,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _row_sort_key(
    row: ResearchStrategyLiquidityAdjustedThesisQualityRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.liquidity_adjustment_drag,
        row.public_thesis_key,
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
) -> tuple[ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ZERO_COUNT,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_probability(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_RATIO) / _count(len(rows)),
    )


def _max_field(
    rows: tuple[ResearchStrategyLiquidityAdjustedThesisQualityRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO_RATIO)


def _validate_row(row: ResearchStrategyLiquidityAdjustedThesisQualityRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    _require_close(
        "model_market_convergence_score",
        row.model_market_convergence_score,
        ONE_RATIO - row.model_market_divergence_score,
    )
    _require_close(
        "spread_depth_quality_score",
        row.spread_depth_quality_score,
        _average_pair(row.spread_quality_score, row.depth_quality_score),
    )
    _require_close(
        "liquidity_cost_quality_score",
        row.liquidity_cost_quality_score,
        _average_pair(row.spread_depth_quality_score, ONE_RATIO - row.fee_drag_score),
    )
    _require_close(
        "source_backed_thesis_quality_score",
        row.source_backed_thesis_quality_score,
        _source_backed_thesis_quality_score(
            source_freshness_score=row.source_freshness_score,
            evidence_strength_score=row.evidence_strength_score,
            model_market_convergence_score=row.model_market_convergence_score,
            resolution_clarity_score=row.resolution_clarity_score,
            specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        ),
    )
    _require_close(
        "liquidity_adjusted_thesis_quality_score",
        row.liquidity_adjusted_thesis_quality_score,
        _normalize_probability(
            "liquidity_adjusted_thesis_quality_score",
            row.source_backed_thesis_quality_score * row.liquidity_cost_quality_score,
        ),
    )
    _require_close(
        "liquidity_adjustment_drag",
        row.liquidity_adjustment_drag,
        _normalize_probability(
            "liquidity_adjustment_drag",
            row.source_backed_thesis_quality_score
            - row.liquidity_adjusted_thesis_quality_score,
        ),
    )


def _validate_report(report: ResearchStrategyLiquidityAdjustedThesisQualityReport) -> None:
    expected_input_count = _count(len(report.rows))
    if report.input_count != expected_input_count:
        raise ValueError("input_count must match rows")
    expected_values = {
        "pass_count": _status_count(report.rows, PASS_STATUS),
        "watch_count": _status_count(report.rows, WATCH_STATUS),
        "block_count": _status_count(report.rows, BLOCK_STATUS),
        "average_source_backed_thesis_quality_score": _average_field(
            report.rows,
            "source_backed_thesis_quality_score",
        ),
        "average_liquidity_cost_quality_score": _average_field(
            report.rows,
            "liquidity_cost_quality_score",
        ),
        "average_liquidity_adjusted_thesis_quality_score": _average_field(
            report.rows,
            "liquidity_adjusted_thesis_quality_score",
        ),
        "average_liquidity_adjustment_drag": _average_field(
            report.rows,
            "liquidity_adjustment_drag",
        ),
        "max_liquidity_adjustment_drag": _max_field(
            report.rows,
            "liquidity_adjustment_drag",
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _status_rollup(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REPORT_REASON_CODES)
        if reason_code in seen:
            raise ValueError(f"{name} must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must use deterministic sequence")
    if reason_codes[0] == QUALITY_PASS_REASON_CODE and len(reason_codes) != 1:
        raise ValueError("reason_codes must use deterministic sequence")
    expected_detail_order = [
        reason_code
        for reason_group in ROW_REASON_SEQUENCE[1:]
        for reason_code in reason_group
        if reason_code in reason_codes
    ]
    if tuple(reason_codes[1:]) != tuple(expected_detail_order):
        raise ValueError("reason_codes must use deterministic sequence")


def _report_public_payload_digest(
    report: ResearchStrategyLiquidityAdjustedThesisQualityReport,
) -> str:
    ready = _json_ready_without_digest(report)
    _reject_unsafe_public_payload("report digest payload", ready)
    canonical_payload = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_report_public_payload_digest(
    report: ResearchStrategyLiquidityAdjustedThesisQualityReport,
) -> None:
    expected_digest = _report_public_payload_digest(report)
    if report.public_payload_digest != expected_digest:
        raise ValueError("public_payload_digest must match report fields")


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("public_payload_digest", None)
    return ready


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        _reject_unsafe_string_value("JSON string", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_string_value("JSON key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _source_backed_thesis_quality_score(
    *,
    source_freshness_score: Decimal,
    evidence_strength_score: Decimal,
    model_market_convergence_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
) -> Decimal:
    return _normalize_probability(
        "source_backed_thesis_quality_score",
        (
            source_freshness_score
            + evidence_strength_score
            + model_market_convergence_score
            + resolution_clarity_score
            + specialist_memory_confidence_score
        )
        / Decimal("5"),
    )


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    observed_at_utc = _as_utc("source_observed_at", observed_at)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if observed_at_utc > generated_at_utc:
        raise ValueError("source_observed_at must not be after generated_at")
    delta = generated_at_utc - observed_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _normalize_nonnegative_measure("source_age_seconds", seconds)


def _remaining_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO_RATIO:
        raise ValueError("limit must be positive")
    remaining = ONE_RATIO - (value / limit)
    if remaining < ZERO_RATIO:
        return ZERO_RATIO
    if remaining > ONE_RATIO:
        return ONE_RATIO
    return _normalize_probability("remaining_ratio", remaining)


def _average_pair(left: Decimal, right: Decimal) -> Decimal:
    return _normalize_probability("average_pair", (left + right) / Decimal("2"))


def _combine_severity(left: str, right: str) -> str:
    if left == BLOCK_STATUS or right == BLOCK_STATUS:
        return BLOCK_STATUS
    if left == WATCH_STATUS or right == WATCH_STATUS:
        return WATCH_STATUS
    return PASS_STATUS


def _falling_threshold_status(value: Decimal, watch: Decimal, block: Decimal) -> str:
    if value <= block:
        return BLOCK_STATUS
    if value <= watch:
        return WATCH_STATUS
    return PASS_STATUS


def _rising_threshold_status(value: Decimal, watch: Decimal, block: Decimal) -> str:
    if value >= block:
        return BLOCK_STATUS
    if value >= watch:
        return WATCH_STATUS
    return PASS_STATUS


def _require_close(name: str, observed: Decimal, expected: Decimal) -> None:
    if observed != expected:
        raise ValueError(f"{name} must match derived fields")


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be lowercase hex")
    return value


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_measure(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_decimal(name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    _reject_unsafe_string_value(name, value)
    return value


def _require_safe_label(name: str, value: object) -> str:
    normalized = _require_public_string(name, value)
    if any(fragment in normalized.lower() for fragment in UNSAFE_REFERENCE_FRAGMENTS):
        raise ValueError(f"{name} contains restricted references")
    if name == "public_thesis_key":
        if RAW_THESIS_IDENTIFIER_RE.fullmatch(normalized.lower()):
            raise ValueError(f"{name} must not expose raw identifiers")
        if not PUBLIC_THESIS_KEY_RE.fullmatch(normalized):
            raise ValueError(f"{name} must be a sanitized public thesis key")
        tail = normalized.removeprefix("thesis-")
        if sum(character.isdigit() for character in tail) > len(tail) // 2:
            raise ValueError(f"{name} must not expose raw identifiers")
    return normalized


def _require_member(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{name} must be one of: {', '.join(choices)}")


def _require_falling_threshold(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value <= block_value:
        raise ValueError(f"{watch_name} must be above {block_name}")


def _require_rising_threshold(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value >= block_value:
        raise ValueError(f"{watch_name} must be below {block_name}")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_string_value(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(payload, str):
        _reject_unsafe_string_value(label, payload)


def _reject_unsafe_string_value(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_REFERENCE_FRAGMENTS):
        raise ValueError(f"{label} contains restricted references")
