"""Deterministic report-only cost and liquidity break-even bands."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_BREAK_EVEN_BANDS_REPORT_CONFIG_VERSION = (
    "research-market-cost-liquidity-break-even-bands-report-v1"
)
DEFAULT_CONFIG_VERSION = (
    DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_BREAK_EVEN_BANDS_REPORT_CONFIG_VERSION
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
BPS_PER_PROBABILITY = Decimal("10000.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
STATUS_WEIGHT = {
    STATUS_PASS: Decimal("1.000000"),
    STATUS_WATCH: Decimal("2.000000"),
    STATUS_BLOCK: Decimal("3.000000"),
}

COST_BAND_LOW = "low"
COST_BAND_MEDIUM = "medium"
COST_BAND_HIGH = "high"
COST_BANDS = frozenset((COST_BAND_LOW, COST_BAND_MEDIUM, COST_BAND_HIGH))

LIQUIDITY_BAND_DEEP = "deep"
LIQUIDITY_BAND_MODERATE = "moderate"
LIQUIDITY_BAND_THIN = "thin"
LIQUIDITY_BANDS = frozenset(
    (LIQUIDITY_BAND_DEEP, LIQUIDITY_BAND_MODERATE, LIQUIDITY_BAND_THIN),
)

REASON_NO_INPUTS = "research_market_cost_liquidity_break_even_bands_no_inputs"
REASON_REPORT_PASS = "research_market_cost_liquidity_break_even_bands_pass"
REASON_REPORT_WATCH = "research_market_cost_liquidity_break_even_bands_watch"
REASON_REPORT_BLOCK = "research_market_cost_liquidity_break_even_bands_block"
REASON_COST_LOW = "cost_band_low"
REASON_COST_MEDIUM = "cost_band_medium"
REASON_COST_HIGH = "cost_band_high"
REASON_LIQUIDITY_DEEP = "liquidity_band_deep"
REASON_LIQUIDITY_MODERATE = "liquidity_band_moderate"
REASON_LIQUIDITY_THIN = "liquidity_band_thin"
REASON_EDGE_ABOVE = "probability_edge_above_break_even"
REASON_EDGE_NEAR = "probability_edge_near_break_even"
REASON_EDGE_BELOW = "probability_edge_below_break_even"
REASON_BANDS_PASS = "break_even_bands_pass"
REASON_BANDS_WATCH = "break_even_bands_watch"
REASON_BANDS_BLOCK = "break_even_bands_block"

ROW_REASON_CODE_SEQUENCE = (
    REASON_COST_LOW,
    REASON_COST_MEDIUM,
    REASON_COST_HIGH,
    REASON_LIQUIDITY_DEEP,
    REASON_LIQUIDITY_MODERATE,
    REASON_LIQUIDITY_THIN,
    REASON_EDGE_ABOVE,
    REASON_EDGE_NEAR,
    REASON_EDGE_BELOW,
    REASON_BANDS_PASS,
    REASON_BANDS_WATCH,
    REASON_BANDS_BLOCK,
)
REPORT_REASON_CODE_SEQUENCE = (
    REASON_NO_INPUTS,
    REASON_REPORT_BLOCK,
    REASON_REPORT_WATCH,
    REASON_REPORT_PASS,
    *ROW_REASON_CODE_SEQUENCE,
)
REASON_CODES = frozenset(REPORT_REASON_CODE_SEQUENCE)

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_STRING_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")

CONFIG_THRESHOLD_FIELDS = (
    "pass_break_even_margin_bps",
    "watch_break_even_margin_bps",
    "pass_depth",
    "watch_depth",
    "low_cost_max_bps",
    "medium_cost_max_bps",
)

REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        *CONFIG_THRESHOLD_FIELDS,
        "status",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_total_cost_bps",
        "max_total_cost_bps",
        "min_break_even_margin_bps",
        "rows",
        "reason_codes",
        "reason_code_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "research_digest",
        "rank",
        "spread_bps",
        "taker_fee_bps",
        "slippage_bps",
        "spread_cost_bps",
        "total_cost_bps",
        "depth",
        "probability_edge",
        "probability_edge_bps",
        "break_even_probability_edge",
        "break_even_margin_bps",
        "cost_band",
        "liquidity_band",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    ("reason_code", "count", "paper_only", "report_only", "readonly"),
)

_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "execute",
    "recommendation",
    "sizing",
    "credential",
    "private_key",
    "api_key",
    "auth",
)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityBreakEvenBandsConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_BREAK_EVEN_BANDS_REPORT_CONFIG_VERSION
    )
    pass_break_even_margin_bps: Decimal = Decimal("10.000000")
    watch_break_even_margin_bps: Decimal = Decimal("0.000000")
    pass_depth: Decimal = Decimal("1000.000000")
    watch_depth: Decimal = Decimal("250.000000")
    low_cost_max_bps: Decimal = Decimal("20.000000")
    medium_cost_max_bps: Decimal = Decimal("50.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostLiquidityBreakEvenBandsConfig:
            raise TypeError(
                "ResearchMarketCostLiquidityBreakEvenBandsConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchMarketCostLiquidityBreakEvenBandsConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in CONFIG_THRESHOLD_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_thresholds(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityBreakEvenBandsInput:
    research_reference: str
    spread_bps: Decimal
    taker_fee_bps: Decimal
    slippage_bps: Decimal
    depth: Decimal
    probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostLiquidityBreakEvenBandsInput:
            raise TypeError(
                "ResearchMarketCostLiquidityBreakEvenBandsInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchMarketCostLiquidityBreakEvenBandsInput,
        )
        _require_private_reference("research_reference", self.research_reference)
        for field_name in ("spread_bps", "taker_fee_bps", "slippage_bps", "depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_edge",
            _require_probability_decimal("probability_edge", self.probability_edge),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityBreakEvenBandsRow:
    research_digest: str
    rank: Decimal
    spread_bps: Decimal
    taker_fee_bps: Decimal
    slippage_bps: Decimal
    spread_cost_bps: Decimal
    total_cost_bps: Decimal
    depth: Decimal
    probability_edge: Decimal
    probability_edge_bps: Decimal
    break_even_probability_edge: Decimal
    break_even_margin_bps: Decimal
    cost_band: str
    liquidity_band: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostLiquidityBreakEvenBandsRow:
            raise TypeError(
                "ResearchMarketCostLiquidityBreakEvenBandsRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchMarketCostLiquidityBreakEvenBandsRow,
        )
        _require_sha256_digest("research_digest", self.research_digest)
        object.__setattr__(self, "rank", _require_positive_count("rank", self.rank))
        for field_name in (
            "spread_bps",
            "taker_fee_bps",
            "slippage_bps",
            "spread_cost_bps",
            "total_cost_bps",
            "depth",
            "probability_edge_bps",
            "break_even_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_edge",
            _require_probability_decimal("probability_edge", self.probability_edge),
        )
        object.__setattr__(
            self,
            "break_even_margin_bps",
            _require_decimal("break_even_margin_bps", self.break_even_margin_bps),
        )
        _require_member("cost_band", self.cost_band, COST_BANDS)
        _require_member("liquidity_band", self.liquidity_band, LIQUIDITY_BANDS)
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row_math(self)
        _require_hard_flags("row", self)


ResearchMarketCostLiquidityBreakEvenBandsReportRow = (
    ResearchMarketCostLiquidityBreakEvenBandsRow
)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount:
            raise TypeError(
                "ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityBreakEvenBandsReport:
    generated_at: datetime
    config_version: str
    pass_break_even_margin_bps: Decimal
    watch_break_even_margin_bps: Decimal
    pass_depth: Decimal
    watch_depth: Decimal
    low_cost_max_bps: Decimal
    medium_cost_max_bps: Decimal
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_total_cost_bps: Decimal
    max_total_cost_bps: Decimal
    min_break_even_margin_bps: Decimal
    rows: tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostLiquidityBreakEvenBandsReport:
            raise TypeError(
                "ResearchMarketCostLiquidityBreakEvenBandsReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchMarketCostLiquidityBreakEvenBandsReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in CONFIG_THRESHOLD_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_thresholds(self)
        _require_member("status", self.status, STATUSES)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_total_cost_bps",
            "max_total_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_break_even_margin_bps",
            _require_decimal(
                "min_break_even_margin_bps",
                self.min_break_even_margin_bps,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest does not match report payload",
                )

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_liquidity_break_even_bands_report_payload(self)

    @property
    def digest(self) -> str:
        return self.derived_validation_digest


def build_research_market_cost_liquidity_break_even_bands_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketCostLiquidityBreakEvenBandsConfig,
    generated_at: datetime,
) -> ResearchMarketCostLiquidityBreakEvenBandsReport:
    """Reduce local observations into deterministic diagnostic bands."""

    if type(config) is not ResearchMarketCostLiquidityBreakEvenBandsConfig:
        raise ValueError(
            "config must be a ResearchMarketCostLiquidityBreakEvenBandsConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(
        sorted(
            (_unranked_row(item, config) for item in normalized_inputs),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketCostLiquidityBreakEvenBandsRow(
            rank=_count(index),
            **values,
        )
        for index, values in enumerate(unranked_rows, start=1)
    )
    return ResearchMarketCostLiquidityBreakEvenBandsReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        pass_break_even_margin_bps=config.pass_break_even_margin_bps,
        watch_break_even_margin_bps=config.watch_break_even_margin_bps,
        pass_depth=config.pass_depth,
        watch_depth=config.watch_depth,
        low_cost_max_bps=config.low_cost_max_bps,
        medium_cost_max_bps=config.medium_cost_max_bps,
        status=_report_status(rows),
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_total_cost_bps=_mean(
            tuple(row.total_cost_bps for row in rows),
        ),
        max_total_cost_bps=_maximum(
            tuple(row.total_cost_bps for row in rows),
        ),
        min_break_even_margin_bps=_minimum(
            tuple(row.break_even_margin_bps for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
    )


def research_market_cost_liquidity_break_even_bands_report_payload(
    report: ResearchMarketCostLiquidityBreakEvenBandsReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketCostLiquidityBreakEvenBandsReport:
        _validate_report_consistency(report)
        if report.derived_validation_digest != _report_digest(report):
            raise ValueError(
                "derived_validation_digest does not match report payload",
            )
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        return validate_research_market_cost_liquidity_break_even_bands_report_payload(
            payload,
        )
    if type(report) is dict:
        return validate_research_market_cost_liquidity_break_even_bands_report_payload(
            report,
        )
    raise ValueError(
        "report must be a ResearchMarketCostLiquidityBreakEvenBandsReport",
    )


def validate_research_market_cost_liquidity_break_even_bands_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Validate and return the canonical public JSON payload."""

    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_json_payload_value("payload", payload)
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_FIELDS)
    _validate_public_payload_digest(payload)
    report = _report_from_payload(payload)
    canonical = _json_ready(report)
    if type(canonical) is not dict or canonical != payload:
        raise ValueError("payload must match canonical public schema")
    return canonical


def _unranked_row(
    item: ResearchMarketCostLiquidityBreakEvenBandsInput,
    config: ResearchMarketCostLiquidityBreakEvenBandsConfig,
) -> dict[str, object]:
    spread_cost_bps = _quantize(item.spread_bps / TWO)
    total_cost_bps = _quantize(
        spread_cost_bps + item.taker_fee_bps + item.slippage_bps,
    )
    probability_edge_bps = _quantize(
        item.probability_edge * BPS_PER_PROBABILITY,
    )
    break_even_probability_edge = _quantize(
        total_cost_bps / BPS_PER_PROBABILITY,
    )
    break_even_margin_bps = _quantize(probability_edge_bps - total_cost_bps)
    cost_band = _cost_band(total_cost_bps, config)
    liquidity_band = _liquidity_band(item.depth, config)
    status = _row_status(
        break_even_margin_bps=break_even_margin_bps,
        liquidity_band=liquidity_band,
        config=config,
    )
    return {
        "research_digest": _sha256_text(item.research_reference),
        "spread_bps": item.spread_bps,
        "taker_fee_bps": item.taker_fee_bps,
        "slippage_bps": item.slippage_bps,
        "spread_cost_bps": spread_cost_bps,
        "total_cost_bps": total_cost_bps,
        "depth": item.depth,
        "probability_edge": item.probability_edge,
        "probability_edge_bps": probability_edge_bps,
        "break_even_probability_edge": break_even_probability_edge,
        "break_even_margin_bps": break_even_margin_bps,
        "cost_band": cost_band,
        "liquidity_band": liquidity_band,
        "status": status,
        "reason_codes": _row_reason_codes(
            cost_band=cost_band,
            liquidity_band=liquidity_band,
            break_even_margin_bps=break_even_margin_bps,
            status=status,
            config=config,
        ),
    }


def _cost_band(
    total_cost_bps: Decimal,
    config: ResearchMarketCostLiquidityBreakEvenBandsConfig
    | ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> str:
    if total_cost_bps <= config.low_cost_max_bps:
        return COST_BAND_LOW
    if total_cost_bps <= config.medium_cost_max_bps:
        return COST_BAND_MEDIUM
    return COST_BAND_HIGH


def _liquidity_band(
    depth: Decimal,
    config: ResearchMarketCostLiquidityBreakEvenBandsConfig
    | ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> str:
    if depth >= config.pass_depth:
        return LIQUIDITY_BAND_DEEP
    if depth >= config.watch_depth:
        return LIQUIDITY_BAND_MODERATE
    return LIQUIDITY_BAND_THIN


def _row_status(
    *,
    break_even_margin_bps: Decimal,
    liquidity_band: str,
    config: ResearchMarketCostLiquidityBreakEvenBandsConfig
    | ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> str:
    if (
        break_even_margin_bps < config.watch_break_even_margin_bps
        or liquidity_band == LIQUIDITY_BAND_THIN
    ):
        return STATUS_BLOCK
    if (
        break_even_margin_bps >= config.pass_break_even_margin_bps
        and liquidity_band == LIQUIDITY_BAND_DEEP
    ):
        return STATUS_PASS
    return STATUS_WATCH


def _row_reason_codes(
    *,
    cost_band: str,
    liquidity_band: str,
    break_even_margin_bps: Decimal,
    status: str,
    config: ResearchMarketCostLiquidityBreakEvenBandsConfig
    | ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> tuple[str, ...]:
    cost_reason = {
        COST_BAND_LOW: REASON_COST_LOW,
        COST_BAND_MEDIUM: REASON_COST_MEDIUM,
        COST_BAND_HIGH: REASON_COST_HIGH,
    }[cost_band]
    liquidity_reason = {
        LIQUIDITY_BAND_DEEP: REASON_LIQUIDITY_DEEP,
        LIQUIDITY_BAND_MODERATE: REASON_LIQUIDITY_MODERATE,
        LIQUIDITY_BAND_THIN: REASON_LIQUIDITY_THIN,
    }[liquidity_band]
    if break_even_margin_bps < config.watch_break_even_margin_bps:
        edge_reason = REASON_EDGE_BELOW
    elif break_even_margin_bps < config.pass_break_even_margin_bps:
        edge_reason = REASON_EDGE_NEAR
    else:
        edge_reason = REASON_EDGE_ABOVE
    status_reason = {
        STATUS_PASS: REASON_BANDS_PASS,
        STATUS_WATCH: REASON_BANDS_WATCH,
        STATUS_BLOCK: REASON_BANDS_BLOCK,
    }[status]
    return _normalize_row_reason_codes(
        (cost_reason, liquidity_reason, edge_reason, status_reason),
    )


def _report_status(
    rows: tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_NO_INPUTS,)
    report_reason = {
        STATUS_PASS: REASON_REPORT_PASS,
        STATUS_WATCH: REASON_REPORT_WATCH,
        STATUS_BLOCK: REASON_REPORT_BLOCK,
    }[_report_status(rows)]
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    return (
        report_reason,
        *(
            reason_code
            for reason_code in ROW_REASON_CODE_SEQUENCE
            if reason_code in observed
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...],
) -> tuple[ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=_count(1),
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_thresholds(
    value: ResearchMarketCostLiquidityBreakEvenBandsConfig
    | ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> None:
    if value.pass_break_even_margin_bps < value.watch_break_even_margin_bps:
        raise ValueError(
            "pass_break_even_margin_bps must be at least "
            "watch_break_even_margin_bps",
        )
    if value.pass_depth < value.watch_depth:
        raise ValueError("pass_depth must be at least watch_depth")
    if value.medium_cost_max_bps < value.low_cost_max_bps:
        raise ValueError("medium_cost_max_bps must be at least low_cost_max_bps")


def _validate_row_math(
    row: ResearchMarketCostLiquidityBreakEvenBandsRow,
) -> None:
    if row.spread_cost_bps != _quantize(row.spread_bps / TWO):
        raise ValueError("spread_cost_bps must match half spread_bps")
    expected_total_cost = _quantize(
        row.spread_cost_bps + row.taker_fee_bps + row.slippage_bps,
    )
    if row.total_cost_bps != expected_total_cost:
        raise ValueError("total_cost_bps must match cost components")
    expected_probability_edge_bps = _quantize(
        row.probability_edge * BPS_PER_PROBABILITY,
    )
    if row.probability_edge_bps != expected_probability_edge_bps:
        raise ValueError("probability_edge_bps must match probability_edge")
    expected_break_even_edge = _quantize(
        row.total_cost_bps / BPS_PER_PROBABILITY,
    )
    if row.break_even_probability_edge != expected_break_even_edge:
        raise ValueError(
            "break_even_probability_edge must match total_cost_bps",
        )
    expected_margin = _quantize(row.probability_edge_bps - row.total_cost_bps)
    if row.break_even_margin_bps != expected_margin:
        raise ValueError("break_even_margin_bps must match edge minus costs")
    expected_cost_reason = f"cost_band_{row.cost_band}"
    expected_liquidity_reason = f"liquidity_band_{row.liquidity_band}"
    expected_status_reason = f"break_even_bands_{row.status}"
    for reason_code in (
        expected_cost_reason,
        expected_liquidity_reason,
        expected_status_reason,
    ):
        if reason_code not in row.reason_codes:
            raise ValueError("reason_codes must match row bands and status")


def _validate_row_against_report(
    row: ResearchMarketCostLiquidityBreakEvenBandsRow,
    report: ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> None:
    expected_cost_band = _cost_band(row.total_cost_bps, report)
    if row.cost_band != expected_cost_band:
        raise ValueError("cost_band must match derived total cost band")
    expected_liquidity_band = _liquidity_band(row.depth, report)
    if row.liquidity_band != expected_liquidity_band:
        raise ValueError("liquidity_band must match derived depth band")
    expected_status = _row_status(
        break_even_margin_bps=row.break_even_margin_bps,
        liquidity_band=expected_liquidity_band,
        config=report,
    )
    if row.status != expected_status:
        raise ValueError("status must match derived break-even bands")
    expected_reasons = _row_reason_codes(
        cost_band=expected_cost_band,
        liquidity_band=expected_liquidity_band,
        break_even_margin_bps=row.break_even_margin_bps,
        status=expected_status,
        config=report,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match derived break-even bands")


def _validate_report_consistency(
    report: ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> None:
    for expected_rank, row in enumerate(report.rows, start=1):
        if row.rank != _count(expected_rank):
            raise ValueError("rank must match canonical row order")
        _validate_row_against_report(row, report)
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical order")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_total_cost_bps != _mean(
        tuple(row.total_cost_bps for row in report.rows),
    ):
        raise ValueError("average_total_cost_bps must match rows")
    if report.max_total_cost_bps != _maximum(
        tuple(row.total_cost_bps for row in report.rows),
    ):
        raise ValueError("max_total_cost_bps must match rows")
    if report.min_break_even_margin_bps != _minimum(
        tuple(row.break_even_margin_bps for row in report.rows),
    ):
        raise ValueError("min_break_even_margin_bps must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketCostLiquidityBreakEvenBandsInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_references: set[str] = set()
    normalized: list[ResearchMarketCostLiquidityBreakEvenBandsInput] = []
    for item in values:
        if type(item) is not ResearchMarketCostLiquidityBreakEvenBandsInput:
            raise ValueError(
                "inputs must contain ResearchMarketCostLiquidityBreakEvenBandsInput "
                "values",
            )
        _require_hard_flags("input", item)
        if item.research_reference in seen_references:
            raise ValueError(
                "inputs must not contain duplicate research_reference values",
            )
        seen_references.add(item.research_reference)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketCostLiquidityBreakEvenBandsRow],
) -> tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    values = tuple(rows)
    seen_digests: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketCostLiquidityBreakEvenBandsRow:
            raise ValueError(
                "rows must contain ResearchMarketCostLiquidityBreakEvenBandsRow "
                "values",
            )
        if row.research_digest in seen_digests:
            raise ValueError("rows must not contain duplicate research_digest values")
        seen_digests.add(row.research_digest)
    return values


def _normalize_row_reason_codes(
    reason_codes: Iterable[str],
) -> tuple[str, ...]:
    values = _reason_code_values("reason_codes", reason_codes)
    if len(values) != 4:
        raise ValueError("reason_codes must contain exactly four row reasons")
    canonical = tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in values
    )
    if values != canonical:
        raise ValueError("reason_codes must use canonical row sequence")
    category_counts = (
        sum(reason.startswith("cost_band_") for reason in values),
        sum(reason.startswith("liquidity_band_") for reason in values),
        sum(reason.startswith("probability_edge_") for reason in values),
        sum(reason.startswith("break_even_bands_") for reason in values),
    )
    if category_counts != (1, 1, 1, 1):
        raise ValueError("reason_codes must contain one reason per diagnostic band")
    return values


def _normalize_report_reason_codes(
    reason_codes: Iterable[str],
) -> tuple[str, ...]:
    values = _reason_code_values("reason_codes", reason_codes)
    canonical = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in values
    )
    if values != canonical:
        raise ValueError("reason_codes must use canonical report sequence")
    return values


def _reason_code_values(
    field_name: str,
    reason_codes: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
    return values


def _normalize_reason_code_counts(
    values: Sequence[ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount],
) -> tuple[ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized = tuple(values)
    seen_codes: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount values",
            )
        if item.reason_code in seen_codes:
            raise ValueError(
                "reason_code_counts must not contain duplicate reason_code values",
            )
        seen_codes.add(item.reason_code)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError(
            "reason_code_counts must be sorted by count then reason_code",
        )
    return normalized


def _unranked_row_sort_key(
    row: Mapping[str, object],
) -> tuple[Decimal, Decimal, Decimal, str]:
    status = row["status"]
    margin = row["break_even_margin_bps"]
    total_cost = row["total_cost_bps"]
    digest = row["research_digest"]
    if type(status) is not str or status not in STATUSES:
        raise ValueError("status must be valid")
    if type(margin) is not Decimal:
        raise ValueError("break_even_margin_bps must be a Decimal")
    if type(total_cost) is not Decimal:
        raise ValueError("total_cost_bps must be a Decimal")
    if type(digest) is not str:
        raise ValueError("research_digest must be a string")
    return (-STATUS_WEIGHT[status], margin, -total_cost, digest)


def _row_sort_key(
    row: ResearchMarketCostLiquidityBreakEvenBandsRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        row.break_even_margin_bps,
        -row.total_cost_bps,
        row.research_digest,
    )


def _status_count(
    rows: tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext() as context:
        context.prec = 40
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO)


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    return min(values, default=ZERO)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(
            f"{field_name} must be exactly {expected_type.__name__}",
        )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical and non-empty")
    if len(value) > 4096:
        raise ValueError(f"{field_name} is too long")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains an unsafe public fragment")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed: frozenset[str],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must use supported vocabulary")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("Decimal value must be finite")
    normalized = value.quantize(QUANT, rounding=ROUND_HALF_UP)
    if normalized == ZERO:
        return ZERO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest(
    report: ResearchMarketCostLiquidityBreakEvenBandsReport,
) -> str:
    return _digest_values(_report_values_without_digest(report))


def _digest_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected = _digest_values(unsigned)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        normalized = _require_decimal("payload Decimal", value)
        return format(normalized, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not public JSON serializable")


def _require_json_payload_value(label: str, value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _require_json_payload_value(f"{label}.{key}", item)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_json_payload_value(f"{label}[{index}]", item)
        return
    raise ValueError(f"{label} must contain exact public JSON types")


def _report_from_payload(
    payload: Mapping[str, object],
) -> ResearchMarketCostLiquidityBreakEvenBandsReport:
    return ResearchMarketCostLiquidityBreakEvenBandsReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        pass_break_even_margin_bps=_payload_decimal(
            "pass_break_even_margin_bps",
            payload["pass_break_even_margin_bps"],
        ),
        watch_break_even_margin_bps=_payload_decimal(
            "watch_break_even_margin_bps",
            payload["watch_break_even_margin_bps"],
        ),
        pass_depth=_payload_decimal("pass_depth", payload["pass_depth"]),
        watch_depth=_payload_decimal("watch_depth", payload["watch_depth"]),
        low_cost_max_bps=_payload_decimal(
            "low_cost_max_bps",
            payload["low_cost_max_bps"],
        ),
        medium_cost_max_bps=_payload_decimal(
            "medium_cost_max_bps",
            payload["medium_cost_max_bps"],
        ),
        status=_payload_string("status", payload["status"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_total_cost_bps=_payload_decimal(
            "average_total_cost_bps",
            payload["average_total_cost_bps"],
        ),
        max_total_cost_bps=_payload_decimal(
            "max_total_cost_bps",
            payload["max_total_cost_bps"],
        ),
        min_break_even_margin_bps=_payload_decimal(
            "min_break_even_margin_bps",
            payload["min_break_even_margin_bps"],
        ),
        rows=_payload_rows(payload["rows"]),
        reason_codes=_payload_strings("reason_codes", payload["reason_codes"]),
        reason_code_counts=_payload_reason_code_counts(
            payload["reason_code_counts"],
        ),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _payload_rows(
    value: object,
) -> tuple[ResearchMarketCostLiquidityBreakEvenBandsRow, ...]:
    return tuple(
        _payload_row(f"rows[{index}]", item)
        for index, item in enumerate(_payload_sequence("rows", value))
    )


def _payload_row(
    label: str,
    value: object,
) -> ResearchMarketCostLiquidityBreakEvenBandsRow:
    row = _payload_mapping(label, value)
    _require_payload_keys(label, row, ROW_PAYLOAD_FIELDS)
    return ResearchMarketCostLiquidityBreakEvenBandsRow(
        research_digest=_payload_string(
            f"{label}.research_digest",
            row["research_digest"],
        ),
        rank=_payload_decimal(f"{label}.rank", row["rank"]),
        spread_bps=_payload_decimal(f"{label}.spread_bps", row["spread_bps"]),
        taker_fee_bps=_payload_decimal(
            f"{label}.taker_fee_bps",
            row["taker_fee_bps"],
        ),
        slippage_bps=_payload_decimal(
            f"{label}.slippage_bps",
            row["slippage_bps"],
        ),
        spread_cost_bps=_payload_decimal(
            f"{label}.spread_cost_bps",
            row["spread_cost_bps"],
        ),
        total_cost_bps=_payload_decimal(
            f"{label}.total_cost_bps",
            row["total_cost_bps"],
        ),
        depth=_payload_decimal(f"{label}.depth", row["depth"]),
        probability_edge=_payload_decimal(
            f"{label}.probability_edge",
            row["probability_edge"],
        ),
        probability_edge_bps=_payload_decimal(
            f"{label}.probability_edge_bps",
            row["probability_edge_bps"],
        ),
        break_even_probability_edge=_payload_decimal(
            f"{label}.break_even_probability_edge",
            row["break_even_probability_edge"],
        ),
        break_even_margin_bps=_payload_decimal(
            f"{label}.break_even_margin_bps",
            row["break_even_margin_bps"],
        ),
        cost_band=_payload_string(f"{label}.cost_band", row["cost_band"]),
        liquidity_band=_payload_string(
            f"{label}.liquidity_band",
            row["liquidity_band"],
        ),
        status=_payload_string(f"{label}.status", row["status"]),
        reason_codes=_payload_strings(
            f"{label}.reason_codes",
            row["reason_codes"],
        ),
        paper_only=_payload_true(f"{label}.paper_only", row["paper_only"]),
        report_only=_payload_true(f"{label}.report_only", row["report_only"]),
        readonly=_payload_true(f"{label}.readonly", row["readonly"]),
    )


def _payload_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount, ...]:
    return tuple(
        _payload_reason_code_count(f"reason_code_counts[{index}]", item)
        for index, item in enumerate(
            _payload_sequence("reason_code_counts", value),
        )
    )


def _payload_reason_code_count(
    label: str,
    value: object,
) -> ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount:
    row = _payload_mapping(label, value)
    _require_payload_keys(label, row, REASON_COUNT_PAYLOAD_FIELDS)
    return ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
        reason_code=_payload_string(
            f"{label}.reason_code",
            row["reason_code"],
        ),
        count=_payload_decimal(f"{label}.count", row["count"]),
        paper_only=_payload_true(f"{label}.paper_only", row["paper_only"]),
        report_only=_payload_true(f"{label}.report_only", row["report_only"]),
        readonly=_payload_true(f"{label}.readonly", row["readonly"]),
    )


def _require_payload_keys(
    label: str,
    value: Mapping[str, object],
    expected: frozenset[str],
) -> None:
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} keys must be strings")
    actual = frozenset(value)
    if actual != expected:
        raise ValueError(f"{label} must match exact public schema")


def _payload_mapping(label: str, value: object) -> Mapping[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must match public schema")
    return value


def _payload_sequence(label: str, value: object) -> tuple[object, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must match public schema")
    return tuple(value)


def _payload_strings(label: str, value: object) -> tuple[str, ...]:
    return tuple(
        _payload_string(f"{label}[{index}]", item)
        for index, item in enumerate(_payload_sequence(label, value))
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not DECIMAL_STRING_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a six decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a six decimal string") from exc
    normalized = _require_decimal(field_name, decimal_value)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical six decimal string")
    return normalized


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_BREAK_EVEN_BANDS_REPORT_CONFIG_VERSION",
    "STATUSES",
    "COST_BANDS",
    "LIQUIDITY_BANDS",
    "REASON_CODES",
    "ResearchMarketCostLiquidityBreakEvenBandsConfig",
    "ResearchMarketCostLiquidityBreakEvenBandsInput",
    "ResearchMarketCostLiquidityBreakEvenBandsRow",
    "ResearchMarketCostLiquidityBreakEvenBandsReportRow",
    "ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount",
    "ResearchMarketCostLiquidityBreakEvenBandsReport",
    "build_research_market_cost_liquidity_break_even_bands_report",
    "research_market_cost_liquidity_break_even_bands_report_payload",
    "validate_research_market_cost_liquidity_break_even_bands_report_payload",
)
