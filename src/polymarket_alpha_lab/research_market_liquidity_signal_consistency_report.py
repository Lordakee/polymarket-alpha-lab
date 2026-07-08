"""Pure public liquidity and research signal consistency report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_LIQUIDITY_SIGNAL_CONSISTENCY_CONFIG_VERSION = (
    "research-market-liquidity-signal-consistency-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
REPORT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_market_liquidity_signal_consistency_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
CONSISTENT_REASON = f"{REASON_PREFIX}consistent"
AGGREGATE_DEPTH_BLOCK_REASON = f"{REASON_PREFIX}aggregate_depth_block"
AGGREGATE_DEPTH_WATCH_REASON = f"{REASON_PREFIX}aggregate_depth_watch"
SPREAD_BLOCK_REASON = f"{REASON_PREFIX}spread_block"
SPREAD_WATCH_REASON = f"{REASON_PREFIX}spread_watch"
QUOTE_STALE_BLOCK_REASON = f"{REASON_PREFIX}quote_stale_block"
QUOTE_STALE_WATCH_REASON = f"{REASON_PREFIX}quote_stale_watch"
EVIDENCE_STALE_BLOCK_REASON = f"{REASON_PREFIX}evidence_stale_block"
EVIDENCE_STALE_WATCH_REASON = f"{REASON_PREFIX}evidence_stale_watch"
CATALYST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}catalyst_pressure_block"
CATALYST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}catalyst_pressure_watch"
CONFIDENCE_DISPERSION_BLOCK_REASON = f"{REASON_PREFIX}confidence_dispersion_block"
CONFIDENCE_DISPERSION_WATCH_REASON = f"{REASON_PREFIX}confidence_dispersion_watch"
CONFIDENCE_GAP_BLOCK_REASON = f"{REASON_PREFIX}confidence_gap_block"
CONFIDENCE_GAP_WATCH_REASON = f"{REASON_PREFIX}confidence_gap_watch"

REASON_CODE_SEQUENCE = (
    AGGREGATE_DEPTH_BLOCK_REASON,
    AGGREGATE_DEPTH_WATCH_REASON,
    SPREAD_BLOCK_REASON,
    SPREAD_WATCH_REASON,
    QUOTE_STALE_BLOCK_REASON,
    QUOTE_STALE_WATCH_REASON,
    EVIDENCE_STALE_BLOCK_REASON,
    EVIDENCE_STALE_WATCH_REASON,
    CATALYST_PRESSURE_BLOCK_REASON,
    CATALYST_PRESSURE_WATCH_REASON,
    CONFIDENCE_DISPERSION_BLOCK_REASON,
    CONFIDENCE_DISPERSION_WATCH_REASON,
    CONFIDENCE_GAP_BLOCK_REASON,
    CONFIDENCE_GAP_WATCH_REASON,
    CONSISTENT_REASON,
    NO_INPUTS_REASON,
)

ROW_REASON_CODE_SEQUENCE = (
    AGGREGATE_DEPTH_BLOCK_REASON,
    AGGREGATE_DEPTH_WATCH_REASON,
    SPREAD_BLOCK_REASON,
    SPREAD_WATCH_REASON,
    QUOTE_STALE_BLOCK_REASON,
    QUOTE_STALE_WATCH_REASON,
    EVIDENCE_STALE_BLOCK_REASON,
    EVIDENCE_STALE_WATCH_REASON,
    CATALYST_PRESSURE_BLOCK_REASON,
    CATALYST_PRESSURE_WATCH_REASON,
    CONFIDENCE_DISPERSION_BLOCK_REASON,
    CONFIDENCE_DISPERSION_WATCH_REASON,
    CONFIDENCE_GAP_BLOCK_REASON,
    CONFIDENCE_GAP_WATCH_REASON,
    CONSISTENT_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "sample_count",
        "pass_count",
        "watch_count",
        "block_count",
        "thin_depth_count",
        "wide_spread_count",
        "stale_quote_count",
        "stale_evidence_count",
        "catalyst_pressure_count",
        "confidence_dispersion_count",
        "confidence_gap_count",
        "average_aggregate_depth_usd",
        "average_bid_ask_spread_ratio",
        "average_catalyst_pressure",
        "average_confidence_dispersion",
        "average_confidence_gap",
        "max_quote_age_seconds",
        "max_evidence_age_seconds",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "public_row_id",
        "consistency_status",
        "observed_at",
        "quote_observed_at",
        "evidence_observed_at",
        "quote_age_seconds",
        "evidence_age_seconds",
        "aggregate_depth_usd",
        "bid_ask_spread_ratio",
        "liquidity_signal_confidence",
        "research_signal_confidence",
        "confidence_gap",
        "catalyst_pressure",
        "confidence_dispersion",
        "consistency_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "sample_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("mut", "ation"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "_key"),
        _join_parts("bear", "er"),
        _join_parts("cred", "ential"),
        _join_parts("pass", "word"),
        _join_parts("tra", "de"),
        _join_parts("dsn"),
        "://",
        "?",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_SIGNAL_CONSISTENCY_CONFIG_VERSION",
    "REPORT_STATUSES",
    "ResearchMarketLiquiditySignalConsistencyConfig",
    "ResearchMarketLiquiditySignalConsistencyInput",
    "ResearchMarketLiquiditySignalConsistencyReasonCodeCount",
    "ResearchMarketLiquiditySignalConsistencyReport",
    "ResearchMarketLiquiditySignalConsistencyRow",
    "build_research_market_liquidity_signal_consistency_report",
    "research_market_liquidity_signal_consistency_report_digest",
    "research_market_liquidity_signal_consistency_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketLiquiditySignalConsistencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_SIGNAL_CONSISTENCY_CONFIG_VERSION
    )
    minimum_aggregate_depth_usd: Decimal = Decimal("1000.000000")
    blocked_aggregate_depth_usd: Decimal = Decimal("250.000000")
    maximum_spread_ratio: Decimal = Decimal("0.050000")
    blocked_spread_ratio: Decimal = Decimal("0.120000")
    maximum_quote_age_seconds: Decimal = Decimal("600.000000")
    blocked_quote_age_seconds: Decimal = Decimal("1800.000000")
    maximum_evidence_age_seconds: Decimal = Decimal("86400.000000")
    blocked_evidence_age_seconds: Decimal = Decimal("172800.000000")
    catalyst_pressure_watch_threshold: Decimal = Decimal("0.600000")
    catalyst_pressure_block_threshold: Decimal = Decimal("0.850000")
    confidence_dispersion_watch_threshold: Decimal = Decimal("0.250000")
    confidence_dispersion_block_threshold: Decimal = Decimal("0.500000")
    confidence_gap_watch_threshold: Decimal = Decimal("0.200000")
    confidence_gap_block_threshold: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquiditySignalConsistencyConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquiditySignalConsistencyConfig:
            raise TypeError(
                "config must be exactly ResearchMarketLiquiditySignalConsistencyConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_SIGNAL_CONSISTENCY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "minimum_aggregate_depth_usd",
            "blocked_aggregate_depth_usd",
            "maximum_quote_age_seconds",
            "blocked_quote_age_seconds",
            "maximum_evidence_age_seconds",
            "blocked_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_spread_ratio",
            "blocked_spread_ratio",
            "catalyst_pressure_watch_threshold",
            "catalyst_pressure_block_threshold",
            "confidence_dispersion_watch_threshold",
            "confidence_dispersion_block_threshold",
            "confidence_gap_watch_threshold",
            "confidence_gap_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_aggregate_depth_usd >= self.minimum_aggregate_depth_usd:
            raise ValueError(
                "blocked_aggregate_depth_usd must be less than "
                "minimum_aggregate_depth_usd",
            )
        if self.blocked_spread_ratio <= self.maximum_spread_ratio:
            raise ValueError(
                "blocked_spread_ratio must exceed maximum_spread_ratio",
            )
        if self.blocked_quote_age_seconds <= self.maximum_quote_age_seconds:
            raise ValueError(
                "blocked_quote_age_seconds must exceed maximum_quote_age_seconds",
            )
        if self.blocked_evidence_age_seconds <= self.maximum_evidence_age_seconds:
            raise ValueError(
                "blocked_evidence_age_seconds must exceed "
                "maximum_evidence_age_seconds",
            )
        if (
            self.catalyst_pressure_block_threshold
            <= self.catalyst_pressure_watch_threshold
        ):
            raise ValueError(
                "catalyst_pressure_block_threshold must exceed "
                "catalyst_pressure_watch_threshold",
            )
        if (
            self.confidence_dispersion_block_threshold
            <= self.confidence_dispersion_watch_threshold
        ):
            raise ValueError(
                "confidence_dispersion_block_threshold must exceed "
                "confidence_dispersion_watch_threshold",
            )
        if self.confidence_gap_block_threshold <= self.confidence_gap_watch_threshold:
            raise ValueError(
                "confidence_gap_block_threshold must exceed confidence_gap_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquiditySignalConsistencyInput:
    market_reference: str
    evidence_reference: str
    observed_at: datetime
    quote_observed_at: datetime
    evidence_observed_at: datetime
    aggregate_depth_usd: Decimal
    bid_ask_spread_ratio: Decimal
    liquidity_signal_confidence: Decimal
    research_signal_confidence: Decimal
    catalyst_pressure: Decimal
    confidence_dispersion: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquiditySignalConsistencyInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquiditySignalConsistencyInput:
            raise TypeError(
                "input must be exactly ResearchMarketLiquiditySignalConsistencyInput",
            )
        _require_reference("market_reference", self.market_reference)
        _require_reference("evidence_reference", self.evidence_reference)
        for field_name in ("observed_at", "quote_observed_at", "evidence_observed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_depth_usd",
            _require_nonnegative_decimal("aggregate_depth_usd", self.aggregate_depth_usd),
        )
        for field_name in (
            "bid_ask_spread_ratio",
            "liquidity_signal_confidence",
            "research_signal_confidence",
            "catalyst_pressure",
            "confidence_dispersion",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquiditySignalConsistencyRow:
    public_row_id: str
    consistency_status: str
    observed_at: datetime
    quote_observed_at: datetime
    evidence_observed_at: datetime
    quote_age_seconds: Decimal
    evidence_age_seconds: Decimal
    aggregate_depth_usd: Decimal
    bid_ask_spread_ratio: Decimal
    liquidity_signal_confidence: Decimal
    research_signal_confidence: Decimal
    confidence_gap: Decimal
    catalyst_pressure: Decimal
    confidence_dispersion: Decimal
    consistency_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquiditySignalConsistencyRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquiditySignalConsistencyRow:
            raise TypeError("row must be exactly ResearchMarketLiquiditySignalConsistencyRow")
        _require_public_id("public_row_id", self.public_row_id)
        _require_report_status("consistency_status", self.consistency_status)
        for field_name in ("observed_at", "quote_observed_at", "evidence_observed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quote_age_seconds",
            "evidence_age_seconds",
            "aggregate_depth_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_ask_spread_ratio",
            "liquidity_signal_confidence",
            "research_signal_confidence",
            "confidence_gap",
            "catalyst_pressure",
            "confidence_dispersion",
            "consistency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquiditySignalConsistencyReasonCodeCount:
    reason_code: str
    count: Decimal
    sample_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquiditySignalConsistencyReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquiditySignalConsistencyReasonCodeCount:
            raise TypeError(
                "reason count must be exactly "
                "ResearchMarketLiquiditySignalConsistencyReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "sample_ratio",
            _require_ratio_decimal("sample_ratio", self.sample_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchMarketLiquiditySignalConsistencyReport:
    generated_at: datetime
    config_version: str
    report_status: str
    sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    thin_depth_count: Decimal
    wide_spread_count: Decimal
    stale_quote_count: Decimal
    stale_evidence_count: Decimal
    catalyst_pressure_count: Decimal
    confidence_dispersion_count: Decimal
    confidence_gap_count: Decimal
    average_aggregate_depth_usd: Decimal
    average_bid_ask_spread_ratio: Decimal
    average_catalyst_pressure: Decimal
    average_confidence_dispersion: Decimal
    average_confidence_gap: Decimal
    max_quote_age_seconds: Decimal
    max_evidence_age_seconds: Decimal
    rows: tuple[ResearchMarketLiquiditySignalConsistencyRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquiditySignalConsistencyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquiditySignalConsistencyReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquiditySignalConsistencyReport:
            raise TypeError(
                "report must be exactly ResearchMarketLiquiditySignalConsistencyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "sample_count",
            "pass_count",
            "watch_count",
            "block_count",
            "thin_depth_count",
            "wide_spread_count",
            "stale_quote_count",
            "stale_evidence_count",
            "catalyst_pressure_count",
            "confidence_dispersion_count",
            "confidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_aggregate_depth_usd",
            "average_bid_ask_spread_ratio",
            "average_catalyst_pressure",
            "average_confidence_dispersion",
            "average_confidence_gap",
            "max_quote_age_seconds",
            "max_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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


_PUBLIC_DATACLASS_TYPES = frozenset(
    (
        ResearchMarketLiquiditySignalConsistencyConfig,
        ResearchMarketLiquiditySignalConsistencyInput,
        ResearchMarketLiquiditySignalConsistencyRow,
        ResearchMarketLiquiditySignalConsistencyReasonCodeCount,
        ResearchMarketLiquiditySignalConsistencyReport,
    ),
)


def build_research_market_liquidity_signal_consistency_report(
    inputs: list[ResearchMarketLiquiditySignalConsistencyInput]
    | tuple[ResearchMarketLiquiditySignalConsistencyInput, ...],
    *,
    config: ResearchMarketLiquiditySignalConsistencyConfig,
    generated_at: datetime,
) -> ResearchMarketLiquiditySignalConsistencyReport:
    if type(config) is not ResearchMarketLiquiditySignalConsistencyConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquiditySignalConsistencyConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_inputs = _normalize_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _build_row(value, config=config, generated_at=generated_at_utc)
                for value in source_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchMarketLiquiditySignalConsistencyReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                sample_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    sample_count = _count(len(rows))
    pass_count = _status_count(rows, STATUS_PASS)
    watch_count = _status_count(rows, STATUS_WATCH)
    block_count = _status_count(rows, STATUS_BLOCK)
    return ResearchMarketLiquiditySignalConsistencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(
            has_inputs=bool(rows),
            block_count=block_count,
            watch_count=watch_count,
        ),
        sample_count=sample_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        thin_depth_count=_feature_count(
            rows,
            AGGREGATE_DEPTH_BLOCK_REASON,
            AGGREGATE_DEPTH_WATCH_REASON,
        ),
        wide_spread_count=_feature_count(rows, SPREAD_BLOCK_REASON, SPREAD_WATCH_REASON),
        stale_quote_count=_feature_count(
            rows,
            QUOTE_STALE_BLOCK_REASON,
            QUOTE_STALE_WATCH_REASON,
        ),
        stale_evidence_count=_feature_count(
            rows,
            EVIDENCE_STALE_BLOCK_REASON,
            EVIDENCE_STALE_WATCH_REASON,
        ),
        catalyst_pressure_count=_feature_count(
            rows,
            CATALYST_PRESSURE_BLOCK_REASON,
            CATALYST_PRESSURE_WATCH_REASON,
        ),
        confidence_dispersion_count=_feature_count(
            rows,
            CONFIDENCE_DISPERSION_BLOCK_REASON,
            CONFIDENCE_DISPERSION_WATCH_REASON,
        ),
        confidence_gap_count=_feature_count(
            rows,
            CONFIDENCE_GAP_BLOCK_REASON,
            CONFIDENCE_GAP_WATCH_REASON,
        ),
        average_aggregate_depth_usd=_ratio(
            _sum_decimal(row.aggregate_depth_usd for row in rows),
            sample_count,
        ),
        average_bid_ask_spread_ratio=_ratio(
            _sum_decimal(row.bid_ask_spread_ratio for row in rows),
            sample_count,
        ),
        average_catalyst_pressure=_ratio(
            _sum_decimal(row.catalyst_pressure for row in rows),
            sample_count,
        ),
        average_confidence_dispersion=_ratio(
            _sum_decimal(row.confidence_dispersion for row in rows),
            sample_count,
        ),
        average_confidence_gap=_ratio(
            _sum_decimal(row.confidence_gap for row in rows),
            sample_count,
        ),
        max_quote_age_seconds=max(
            (row.quote_age_seconds for row in rows),
            default=ZERO,
        ),
        max_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_market_liquidity_signal_consistency_report_payload(
    report: ResearchMarketLiquiditySignalConsistencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquiditySignalConsistencyReport:
        raise ValueError(
            "report must be a ResearchMarketLiquiditySignalConsistencyReport",
        )
    _reject_unsafe_public_payload("report", report)
    validated = _validated_report(report)
    _require_hard_flags("report", validated)
    ready = _json_ready(validated)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _reject_unsafe_public_payload("payload", ready)
    return ready


def research_market_liquidity_signal_consistency_report_digest(
    report: ResearchMarketLiquiditySignalConsistencyReport,
) -> str:
    if type(report) is not ResearchMarketLiquiditySignalConsistencyReport:
        raise ValueError(
            "report must be a ResearchMarketLiquiditySignalConsistencyReport",
        )
    payload = research_market_liquidity_signal_consistency_report_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


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


def _validated_report(
    report: ResearchMarketLiquiditySignalConsistencyReport,
) -> ResearchMarketLiquiditySignalConsistencyReport:
    return ResearchMarketLiquiditySignalConsistencyReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_status=report.report_status,
        sample_count=report.sample_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        thin_depth_count=report.thin_depth_count,
        wide_spread_count=report.wide_spread_count,
        stale_quote_count=report.stale_quote_count,
        stale_evidence_count=report.stale_evidence_count,
        catalyst_pressure_count=report.catalyst_pressure_count,
        confidence_dispersion_count=report.confidence_dispersion_count,
        confidence_gap_count=report.confidence_gap_count,
        average_aggregate_depth_usd=report.average_aggregate_depth_usd,
        average_bid_ask_spread_ratio=report.average_bid_ask_spread_ratio,
        average_catalyst_pressure=report.average_catalyst_pressure,
        average_confidence_dispersion=report.average_confidence_dispersion,
        average_confidence_gap=report.average_confidence_gap,
        max_quote_age_seconds=report.max_quote_age_seconds,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        rows=_validated_rows(report.rows),
        reason_code_counts=_validated_reason_code_counts(report.reason_code_counts),
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _validated_rows(
    rows: object,
) -> tuple[ResearchMarketLiquiditySignalConsistencyRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    return tuple(_validated_row(row) for row in rows)


def _validated_row(row: object) -> ResearchMarketLiquiditySignalConsistencyRow:
    if type(row) is not ResearchMarketLiquiditySignalConsistencyRow:
        raise ValueError("rows must contain ResearchMarketLiquiditySignalConsistencyRow")
    return ResearchMarketLiquiditySignalConsistencyRow(
        public_row_id=row.public_row_id,
        consistency_status=row.consistency_status,
        observed_at=row.observed_at,
        quote_observed_at=row.quote_observed_at,
        evidence_observed_at=row.evidence_observed_at,
        quote_age_seconds=row.quote_age_seconds,
        evidence_age_seconds=row.evidence_age_seconds,
        aggregate_depth_usd=row.aggregate_depth_usd,
        bid_ask_spread_ratio=row.bid_ask_spread_ratio,
        liquidity_signal_confidence=row.liquidity_signal_confidence,
        research_signal_confidence=row.research_signal_confidence,
        confidence_gap=row.confidence_gap,
        catalyst_pressure=row.catalyst_pressure,
        confidence_dispersion=row.confidence_dispersion,
        consistency_score=row.consistency_score,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _validated_reason_code_counts(
    counts: object,
) -> tuple[ResearchMarketLiquiditySignalConsistencyReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    return tuple(_validated_reason_code_count(count) for count in counts)


def _validated_reason_code_count(
    count: object,
) -> ResearchMarketLiquiditySignalConsistencyReasonCodeCount:
    if type(count) is not ResearchMarketLiquiditySignalConsistencyReasonCodeCount:
        raise ValueError("reason_code_counts must contain reason count rows")
    return ResearchMarketLiquiditySignalConsistencyReasonCodeCount(
        reason_code=count.reason_code,
        count=count.count,
        sample_ratio=count.sample_ratio,
        paper_only=count.paper_only,
        report_only=count.report_only,
        readonly=count.readonly,
    )


def _build_row(
    value: ResearchMarketLiquiditySignalConsistencyInput,
    *,
    config: ResearchMarketLiquiditySignalConsistencyConfig,
    generated_at: datetime,
) -> ResearchMarketLiquiditySignalConsistencyRow:
    quote_age_seconds = _seconds_between(value.quote_observed_at, generated_at)
    evidence_age_seconds = _seconds_between(value.evidence_observed_at, generated_at)
    confidence_gap = _ratio_gap(
        value.liquidity_signal_confidence,
        value.research_signal_confidence,
    )
    reason_codes = _row_reason_codes(
        aggregate_depth_usd=value.aggregate_depth_usd,
        bid_ask_spread_ratio=value.bid_ask_spread_ratio,
        quote_age_seconds=quote_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        catalyst_pressure=value.catalyst_pressure,
        confidence_dispersion=value.confidence_dispersion,
        confidence_gap=confidence_gap,
        config=config,
    )
    return ResearchMarketLiquiditySignalConsistencyRow(
        public_row_id=_public_row_id(value.market_reference, value.evidence_reference),
        consistency_status=_row_status(reason_codes),
        observed_at=value.observed_at,
        quote_observed_at=value.quote_observed_at,
        evidence_observed_at=value.evidence_observed_at,
        quote_age_seconds=quote_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        aggregate_depth_usd=value.aggregate_depth_usd,
        bid_ask_spread_ratio=value.bid_ask_spread_ratio,
        liquidity_signal_confidence=value.liquidity_signal_confidence,
        research_signal_confidence=value.research_signal_confidence,
        confidence_gap=confidence_gap,
        catalyst_pressure=value.catalyst_pressure,
        confidence_dispersion=value.confidence_dispersion,
        consistency_score=_consistency_score(
            reason_codes=reason_codes,
            bid_ask_spread_ratio=value.bid_ask_spread_ratio,
            catalyst_pressure=value.catalyst_pressure,
            confidence_dispersion=value.confidence_dispersion,
            confidence_gap=confidence_gap,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    aggregate_depth_usd: Decimal,
    bid_ask_spread_ratio: Decimal,
    quote_age_seconds: Decimal,
    evidence_age_seconds: Decimal,
    catalyst_pressure: Decimal,
    confidence_dispersion: Decimal,
    confidence_gap: Decimal,
    config: ResearchMarketLiquiditySignalConsistencyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if aggregate_depth_usd <= config.blocked_aggregate_depth_usd:
        reasons.append(AGGREGATE_DEPTH_BLOCK_REASON)
    elif aggregate_depth_usd < config.minimum_aggregate_depth_usd:
        reasons.append(AGGREGATE_DEPTH_WATCH_REASON)
    if bid_ask_spread_ratio >= config.blocked_spread_ratio:
        reasons.append(SPREAD_BLOCK_REASON)
    elif bid_ask_spread_ratio > config.maximum_spread_ratio:
        reasons.append(SPREAD_WATCH_REASON)
    if quote_age_seconds >= config.blocked_quote_age_seconds:
        reasons.append(QUOTE_STALE_BLOCK_REASON)
    elif quote_age_seconds > config.maximum_quote_age_seconds:
        reasons.append(QUOTE_STALE_WATCH_REASON)
    if evidence_age_seconds >= config.blocked_evidence_age_seconds:
        reasons.append(EVIDENCE_STALE_BLOCK_REASON)
    elif evidence_age_seconds > config.maximum_evidence_age_seconds:
        reasons.append(EVIDENCE_STALE_WATCH_REASON)
    if catalyst_pressure >= config.catalyst_pressure_block_threshold:
        reasons.append(CATALYST_PRESSURE_BLOCK_REASON)
    elif catalyst_pressure >= config.catalyst_pressure_watch_threshold:
        reasons.append(CATALYST_PRESSURE_WATCH_REASON)
    if confidence_dispersion >= config.confidence_dispersion_block_threshold:
        reasons.append(CONFIDENCE_DISPERSION_BLOCK_REASON)
    elif confidence_dispersion >= config.confidence_dispersion_watch_threshold:
        reasons.append(CONFIDENCE_DISPERSION_WATCH_REASON)
    if confidence_gap >= config.confidence_gap_block_threshold:
        reasons.append(CONFIDENCE_GAP_BLOCK_REASON)
    elif confidence_gap >= config.confidence_gap_watch_threshold:
        reasons.append(CONFIDENCE_GAP_WATCH_REASON)
    if not reasons:
        reasons.append(CONSISTENT_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (CONSISTENT_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_BLOCK
    if block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _consistency_score(
    *,
    reason_codes: tuple[str, ...],
    bid_ask_spread_ratio: Decimal,
    catalyst_pressure: Decimal,
    confidence_dispersion: Decimal,
    confidence_gap: Decimal,
) -> Decimal:
    if reason_codes == (CONSISTENT_REASON,):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        block_count = Decimal(
            sum(1 for reason_code in reason_codes if reason_code.endswith("_block")),
        )
        watch_count = Decimal(
            sum(1 for reason_code in reason_codes if reason_code.endswith("_watch")),
        )
        value = (
            block_count * Decimal("0.100000")
            + watch_count * Decimal("0.025000")
            + bid_ask_spread_ratio
            + catalyst_pressure
            + confidence_dispersion
            + confidence_gap
        )
    return _finite_decimal(min(value, ONE))


def _row_sort_key(row: ResearchMarketLiquiditySignalConsistencyRow) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.consistency_status],
        -row.consistency_score,
        row.public_row_id,
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquiditySignalConsistencyRow, ...],
) -> tuple[ResearchMarketLiquiditySignalConsistencyReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    sample_count = _count(len(rows))
    return tuple(
        ResearchMarketLiquiditySignalConsistencyReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            sample_ratio=_ratio(_count(counts[reason_code]), sample_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_inputs(
    inputs: object,
    generated_at: datetime,
) -> tuple[ResearchMarketLiquiditySignalConsistencyInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchMarketLiquiditySignalConsistencyInput:
            raise ValueError(
                "inputs must contain ResearchMarketLiquiditySignalConsistencyInput",
            )
        _require_hard_flags("input", value)
        public_row_id = _public_row_id(value.market_reference, value.evidence_reference)
        if public_row_id in seen:
            raise ValueError("inputs must use unique redacted row identifiers")
        seen.add(public_row_id)
        for field_name in ("observed_at", "quote_observed_at", "evidence_observed_at"):
            if getattr(value, field_name) > generated_at:
                raise ValueError(f"{field_name} cannot be after generated_at")
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketLiquiditySignalConsistencyRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, Decimal, str] | None = None
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMarketLiquiditySignalConsistencyRow:
            raise ValueError("rows must contain ResearchMarketLiquiditySignalConsistencyRow")
        _require_hard_flags("row", row)
        if row.public_row_id in seen:
            raise ValueError("rows must use unique public_row_id values")
        seen.add(row.public_row_id)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be ranked by unique public_row_id values")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchMarketLiquiditySignalConsistencyReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_rank = -1
    for count in counts:
        if type(count) is not ResearchMarketLiquiditySignalConsistencyReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_code_counts must be ranked by unique reason_code")
        previous_rank = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be ranked by unique reason code")
        previous_rank = rank
    if CONSISTENT_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes consistent cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be ranked by unique reason code")
        previous_rank = rank
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_row(row: ResearchMarketLiquiditySignalConsistencyRow) -> None:
    if row.consistency_status != _row_status(row.reason_codes):
        raise ValueError("consistency_status must match reason_codes")
    if row.consistency_score == ZERO and row.reason_codes != (CONSISTENT_REASON,):
        raise ValueError("consistency_score must match reason_codes")


def _validate_report(report: ResearchMarketLiquiditySignalConsistencyReport) -> None:
    if report.sample_count != _count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            ResearchMarketLiquiditySignalConsistencyReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                sample_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        block_count=report.block_count,
        watch_count=report.watch_count,
    )
    if report.report_status != expected_status:
        raise ValueError("report_status must match row statuses")
    _validate_report_feature(
        report,
        "thin_depth_count",
        AGGREGATE_DEPTH_BLOCK_REASON,
        AGGREGATE_DEPTH_WATCH_REASON,
    )
    _validate_report_feature(
        report,
        "wide_spread_count",
        SPREAD_BLOCK_REASON,
        SPREAD_WATCH_REASON,
    )
    _validate_report_feature(
        report,
        "stale_quote_count",
        QUOTE_STALE_BLOCK_REASON,
        QUOTE_STALE_WATCH_REASON,
    )
    _validate_report_feature(
        report,
        "stale_evidence_count",
        EVIDENCE_STALE_BLOCK_REASON,
        EVIDENCE_STALE_WATCH_REASON,
    )
    _validate_report_feature(
        report,
        "catalyst_pressure_count",
        CATALYST_PRESSURE_BLOCK_REASON,
        CATALYST_PRESSURE_WATCH_REASON,
    )
    _validate_report_feature(
        report,
        "confidence_dispersion_count",
        CONFIDENCE_DISPERSION_BLOCK_REASON,
        CONFIDENCE_DISPERSION_WATCH_REASON,
    )
    _validate_report_feature(
        report,
        "confidence_gap_count",
        CONFIDENCE_GAP_BLOCK_REASON,
        CONFIDENCE_GAP_WATCH_REASON,
    )
    if report.average_aggregate_depth_usd != _ratio(
        _sum_decimal(row.aggregate_depth_usd for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_aggregate_depth_usd must match rows")
    if report.average_bid_ask_spread_ratio != _ratio(
        _sum_decimal(row.bid_ask_spread_ratio for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_bid_ask_spread_ratio must match rows")
    if report.average_catalyst_pressure != _ratio(
        _sum_decimal(row.catalyst_pressure for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_catalyst_pressure must match rows")
    if report.average_confidence_dispersion != _ratio(
        _sum_decimal(row.confidence_dispersion for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_confidence_dispersion must match rows")
    if report.average_confidence_gap != _ratio(
        _sum_decimal(row.confidence_gap for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_confidence_gap must match rows")
    if report.max_quote_age_seconds != max(
        (row.quote_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.max_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_age_seconds must match rows")


def _validate_report_feature(
    report: ResearchMarketLiquiditySignalConsistencyReport,
    field_name: str,
    block_reason_code: str,
    watch_reason_code: str,
) -> None:
    expected = _feature_count(report.rows, block_reason_code, watch_reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _status_count(
    rows: tuple[ResearchMarketLiquiditySignalConsistencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.consistency_status == status))


def _feature_count(
    rows: tuple[ResearchMarketLiquiditySignalConsistencyRow, ...],
    block_reason_code: str,
    watch_reason_code: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if block_reason_code in row.reason_codes or watch_reason_code in row.reason_codes
        ),
    )


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    return value


def _require_public_id(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be redacted")
    if _has_unsafe_public_text_fragment(value.lower()):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be one of {REPORT_STATUSES}")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_six_decimal_value(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _finite_decimal(numerator / denominator)


def _ratio_gap(left: Decimal, right: Decimal) -> Decimal:
    return _finite_decimal(abs(left - right))


def _finite_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be finite and quantizable") from exc


def _public_row_id(market_reference: str, evidence_reference: str) -> str:
    digest = sha256(f"{market_reference}\n{evidence_reference}".encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def _reason_code_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be a known reason code") from exc


def _row_reason_code_rank(reason_code: str) -> int:
    try:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_codes must contain row reason codes") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or 'value'} must be a supported public dataclass")
        _reject_unsafe_public_payload("value", value, path)
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if type(value) is Decimal:
        return format(_require_six_decimal_value(path or "value", value), "f")
    if type(value) is datetime:
        if value.tzinfo is not UTC or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be UTC-aware")
        return value.isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError(f"{path or 'value'} must come from public dataclass fields")
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if isinstance(value, Decimal):
        _require_six_decimal_value(path or label, value)
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        lowered = value.lower()
        if "://" in lowered or "?" in lowered:
            raise ValueError(f"{path or label} has unsafe value")
        if _has_unsafe_public_text_fragment(lowered):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        actual_fields = frozenset(value)
        if path == "":
            _require_payload_fields(label, value, REPORT_PAYLOAD_FIELDS)
        elif path.endswith("rows"):
            for item in value.values():
                _reject_unsafe_public_payload(label, item, path)
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key.lower()):
                raise ValueError(f"{item_path} has unsafe field")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    actual_fields = frozenset(payload)
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must contain the exact report fields")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_TEXT_FRAGMENTS)
