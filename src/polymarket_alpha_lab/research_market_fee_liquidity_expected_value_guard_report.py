"""Report-only fee/liquidity expected value guard."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_CONFIG_VERSION = (
    "research-market-fee-liquidity-expected-value-guard-report-v1"
)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
DEFAULT_OBSERVED_AT = datetime(1970, 1, 1, tzinfo=UTC)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))

REASON_MISSING_INPUTS = "missing_expected_value_guard_inputs"
REASON_POSITIVE_EDGE = "positive_model_market_edge"
REASON_NON_POSITIVE_EDGE = "model_edge_not_positive"
REASON_FEE = "fee_drag_applied"
REASON_SPREAD = "spread_drag_applied"
REASON_LIQUIDITY = "liquidity_shortfall_applied"
REASON_SLIPPAGE = "slippage_buffer_applied"
REASON_SETTLEMENT = "settlement_friction_applied"
REASON_CONFIDENCE = "confidence_haircut_applied"
REASON_COST_BLOCK = "total_cost_drag_blocks_edge"
REASON_COST_EXCEEDS_EDGE = "cost_drag_exceeds_edge"
REASON_BELOW_WATCH = "expected_value_below_watch_threshold"
REASON_PASS = "expected_value_guard_pass"
REASON_WATCH = "expected_value_guard_watch"
REASON_BLOCK = "expected_value_guard_block"
REASON_CODES = frozenset(
    (
        REASON_MISSING_INPUTS,
        REASON_POSITIVE_EDGE,
        REASON_NON_POSITIVE_EDGE,
        REASON_FEE,
        REASON_SPREAD,
        REASON_LIQUIDITY,
        REASON_SLIPPAGE,
        REASON_SETTLEMENT,
        REASON_CONFIDENCE,
        REASON_COST_BLOCK,
        REASON_COST_EXCEEDS_EDGE,
        REASON_BELOW_WATCH,
        REASON_PASS,
        REASON_WATCH,
        REASON_BLOCK,
    ),
)

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_TERMS = (
    "candidate" "_id",
    "candi" "date",
    "market" "_id",
    "market" "_slug",
    "sl" "ug",
    "ques" "tion",
    "u" "rl",
    "te" "xt",
    "d" "sn",
    "ta" "ble",
    "tok" "en",
    "wall" "et",
    "ord" "er",
    "tra" "de",
    "li" "ve",
    "exec" "ute",
    "recommend" "ation",
    "siz" "ing",
    "sec" "ret",
    "creden" "tial",
    "private" "_key",
    "api" "_key",
    "au" "th",
)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityExpectedValueGuardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_adjusted_expected_value_threshold: Decimal = Decimal("0.030000")
    watch_adjusted_expected_value_threshold: Decimal = Decimal("0.005000")
    minimum_depth_coverage_ratio: Decimal = Decimal("1.000000")
    depth_shortfall_penalty_rate: Decimal = Decimal("0.020000")
    block_total_cost_drag_threshold: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityExpectedValueGuardConfig:
            raise TypeError(
                "ResearchMarketFeeLiquidityExpectedValueGuardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchMarketFeeLiquidityExpectedValueGuardConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_adjusted_expected_value_threshold",
            "watch_adjusted_expected_value_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_adjusted_expected_value_threshold
            < self.watch_adjusted_expected_value_threshold
        ):
            raise ValueError(
                "pass_adjusted_expected_value_threshold must be at least "
                "watch_adjusted_expected_value_threshold",
            )
        object.__setattr__(
            self,
            "minimum_depth_coverage_ratio",
            _require_positive_decimal(
                "minimum_depth_coverage_ratio",
                self.minimum_depth_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "depth_shortfall_penalty_rate",
            _require_nonnegative_decimal(
                "depth_shortfall_penalty_rate",
                self.depth_shortfall_penalty_rate,
            ),
        )
        object.__setattr__(
            self,
            "block_total_cost_drag_threshold",
            _require_positive_decimal(
                "block_total_cost_drag_threshold",
                self.block_total_cost_drag_threshold,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(
            "config",
            self,
            allow_constructor_containers=True,
        )


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityExpectedValueGuardInput:
    research_reference: str
    model_probability: Decimal
    market_probability: Decimal
    taker_fee_rate: Decimal
    quoted_spread: Decimal
    depth_coverage_ratio: Decimal
    slippage_buffer_rate: Decimal
    settlement_friction_rate: Decimal
    confidence_haircut_rate: Decimal
    observed_at: datetime = DEFAULT_OBSERVED_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityExpectedValueGuardInput:
            raise TypeError(
                "ResearchMarketFeeLiquidityExpectedValueGuardInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchMarketFeeLiquidityExpectedValueGuardInput,
        )
        _require_private_reference("research_reference", self.research_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_rate",
            "quoted_spread",
            "depth_coverage_ratio",
            "slippage_buffer_rate",
            "settlement_friction_rate",
            "confidence_haircut_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityExpectedValueGuardReportRow:
    research_digest: str
    rank: Decimal
    model_probability: Decimal
    market_probability: Decimal
    gross_expected_value_edge: Decimal
    fee_cost: Decimal
    spread_cost: Decimal
    liquidity_shortfall_cost: Decimal
    slippage_buffer_cost: Decimal
    settlement_friction_cost: Decimal
    confidence_haircut_cost: Decimal
    total_fee_liquidity_drag: Decimal
    total_cost_drag: Decimal
    adjusted_expected_value_edge: Decimal
    guard_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityExpectedValueGuardReportRow:
            raise TypeError(
                "ResearchMarketFeeLiquidityExpectedValueGuardReportRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchMarketFeeLiquidityExpectedValueGuardReportRow,
        )
        _require_sha256_digest("research_digest", self.research_digest)
        object.__setattr__(
            self,
            "rank",
            _require_positive_decimal("rank", self.rank),
        )
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_cost",
            "spread_cost",
            "liquidity_shortfall_cost",
            "slippage_buffer_cost",
            "settlement_friction_cost",
            "confidence_haircut_cost",
            "total_fee_liquidity_drag",
            "total_cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_expected_value_edge",
            "adjusted_expected_value_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("guard_status", self.guard_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload(
            "row",
            self,
            allow_constructor_containers=True,
        )


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityExpectedValueGuardReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_adjusted_expected_value_edge: Decimal | None
    top_adjusted_expected_value_edge: Decimal | None
    max_total_cost_drag: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketFeeLiquidityExpectedValueGuardReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityExpectedValueGuardReport:
            raise TypeError(
                "ResearchMarketFeeLiquidityExpectedValueGuardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchMarketFeeLiquidityExpectedValueGuardReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_adjusted_expected_value_edge",
            "top_adjusted_expected_value_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_total_cost_drag",
            _require_nonnegative_decimal("max_total_cost_drag", self.max_total_cost_drag),
        )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            _validate_report(self)
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
            _validate_report(self)
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _reject_unsafe_public_payload(
            "report",
            _json_ready(self),
            allow_json_containers=True,
        )

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_fee_liquidity_expected_value_guard_report_payload(self)


def build_research_market_fee_liquidity_expected_value_guard_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketFeeLiquidityExpectedValueGuardConfig,
    generated_at: datetime,
) -> ResearchMarketFeeLiquidityExpectedValueGuardReport:
    if type(config) is not ResearchMarketFeeLiquidityExpectedValueGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketFeeLiquidityExpectedValueGuardConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    scored_rows = tuple(
        sorted(
            (_unranked_row(item, config=config) for item in normalized_inputs),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketFeeLiquidityExpectedValueGuardReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(scored_rows, start=1)
    )
    return ResearchMarketFeeLiquidityExpectedValueGuardReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_adjusted_expected_value_edge=_average(
            tuple(row.adjusted_expected_value_edge for row in rows),
        ),
        top_adjusted_expected_value_edge=(
            rows[0].adjusted_expected_value_edge if rows else None
        ),
        max_total_cost_drag=_maximum((row.total_cost_drag for row in rows), ZERO),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_market_fee_liquidity_expected_value_guard_report_payload(
    report: ResearchMarketFeeLiquidityExpectedValueGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketFeeLiquidityExpectedValueGuardReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _report_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketFeeLiquidityExpectedValueGuardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "payload",
        payload,
        allow_json_containers=True,
    )
    _require_payload_digest(payload)
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


def _unranked_row(
    item: ResearchMarketFeeLiquidityExpectedValueGuardInput,
    *,
    config: ResearchMarketFeeLiquidityExpectedValueGuardConfig,
) -> dict[str, object]:
    gross_expected_value_edge = _quantize(
        item.model_probability - item.market_probability,
    )
    fee_cost = item.taker_fee_rate
    spread_cost = _quantize(item.quoted_spread / TWO)
    liquidity_shortfall_cost = _liquidity_shortfall_cost(item, config)
    slippage_buffer_cost = item.slippage_buffer_rate
    settlement_friction_cost = item.settlement_friction_rate
    confidence_haircut_cost = item.confidence_haircut_rate
    total_fee_liquidity_drag = _quantize(
        fee_cost
        + spread_cost
        + liquidity_shortfall_cost
        + slippage_buffer_cost
        + settlement_friction_cost,
    )
    total_cost_drag = _quantize(total_fee_liquidity_drag + confidence_haircut_cost)
    adjusted_expected_value_edge = _quantize(
        gross_expected_value_edge - total_cost_drag,
    )
    guard_status = _guard_status(
        gross_expected_value_edge=gross_expected_value_edge,
        adjusted_expected_value_edge=adjusted_expected_value_edge,
        total_cost_drag=total_cost_drag,
        config=config,
    )
    return {
        "research_digest": _research_digest(item.research_reference),
        "model_probability": item.model_probability,
        "market_probability": item.market_probability,
        "gross_expected_value_edge": gross_expected_value_edge,
        "fee_cost": fee_cost,
        "spread_cost": spread_cost,
        "liquidity_shortfall_cost": liquidity_shortfall_cost,
        "slippage_buffer_cost": slippage_buffer_cost,
        "settlement_friction_cost": settlement_friction_cost,
        "confidence_haircut_cost": confidence_haircut_cost,
        "total_fee_liquidity_drag": total_fee_liquidity_drag,
        "total_cost_drag": total_cost_drag,
        "adjusted_expected_value_edge": adjusted_expected_value_edge,
        "guard_status": guard_status,
        "reason_codes": _row_reason_codes(
            gross_expected_value_edge=gross_expected_value_edge,
            fee_cost=fee_cost,
            spread_cost=spread_cost,
            liquidity_shortfall_cost=liquidity_shortfall_cost,
            slippage_buffer_cost=slippage_buffer_cost,
            settlement_friction_cost=settlement_friction_cost,
            confidence_haircut_cost=confidence_haircut_cost,
            total_cost_drag=total_cost_drag,
            adjusted_expected_value_edge=adjusted_expected_value_edge,
            guard_status=guard_status,
            config=config,
        ),
    }


def _liquidity_shortfall_cost(
    item: ResearchMarketFeeLiquidityExpectedValueGuardInput,
    config: ResearchMarketFeeLiquidityExpectedValueGuardConfig,
) -> Decimal:
    if item.depth_coverage_ratio >= config.minimum_depth_coverage_ratio:
        return ZERO
    shortfall_ratio = _quantize(
        (config.minimum_depth_coverage_ratio - item.depth_coverage_ratio)
        / config.minimum_depth_coverage_ratio,
    )
    return _quantize(shortfall_ratio * config.depth_shortfall_penalty_rate)


def _guard_status(
    *,
    gross_expected_value_edge: Decimal,
    adjusted_expected_value_edge: Decimal,
    total_cost_drag: Decimal,
    config: ResearchMarketFeeLiquidityExpectedValueGuardConfig,
) -> str:
    if total_cost_drag >= config.block_total_cost_drag_threshold:
        return STATUS_BLOCK
    if gross_expected_value_edge <= ZERO:
        return STATUS_BLOCK
    if adjusted_expected_value_edge >= config.pass_adjusted_expected_value_threshold:
        return STATUS_PASS
    if adjusted_expected_value_edge >= config.watch_adjusted_expected_value_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_reason_codes(
    *,
    gross_expected_value_edge: Decimal,
    fee_cost: Decimal,
    spread_cost: Decimal,
    liquidity_shortfall_cost: Decimal,
    slippage_buffer_cost: Decimal,
    settlement_friction_cost: Decimal,
    confidence_haircut_cost: Decimal,
    total_cost_drag: Decimal,
    adjusted_expected_value_edge: Decimal,
    guard_status: str,
    config: ResearchMarketFeeLiquidityExpectedValueGuardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gross_expected_value_edge > ZERO:
        reasons.append(REASON_POSITIVE_EDGE)
    else:
        reasons.append(REASON_NON_POSITIVE_EDGE)
    if fee_cost > ZERO:
        reasons.append(REASON_FEE)
    if spread_cost > ZERO:
        reasons.append(REASON_SPREAD)
    if liquidity_shortfall_cost > ZERO:
        reasons.append(REASON_LIQUIDITY)
    if slippage_buffer_cost > ZERO:
        reasons.append(REASON_SLIPPAGE)
    if settlement_friction_cost > ZERO:
        reasons.append(REASON_SETTLEMENT)
    if confidence_haircut_cost > ZERO:
        reasons.append(REASON_CONFIDENCE)
    if total_cost_drag >= config.block_total_cost_drag_threshold:
        reasons.append(REASON_COST_BLOCK)
    if total_cost_drag > gross_expected_value_edge:
        reasons.append(REASON_COST_EXCEEDS_EDGE)
    if adjusted_expected_value_edge < config.watch_adjusted_expected_value_threshold:
        reasons.append(REASON_BELOW_WATCH)
    if guard_status == STATUS_PASS:
        reasons.append(REASON_PASS)
    elif guard_status == STATUS_WATCH:
        reasons.append(REASON_WATCH)
    else:
        reasons.append(REASON_BLOCK)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _unranked_row_sort_key(row: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    adjusted_edge = row["adjusted_expected_value_edge"]
    total_drag = row["total_cost_drag"]
    digest = row["research_digest"]
    if type(adjusted_edge) is not Decimal:
        raise ValueError("adjusted_expected_value_edge must be a Decimal")
    if type(total_drag) is not Decimal:
        raise ValueError("total_cost_drag must be a Decimal")
    if type(digest) is not str:
        raise ValueError("research_digest must be a string")
    return (-adjusted_edge, total_drag, digest)


def _row_sort_key(
    row: ResearchMarketFeeLiquidityExpectedValueGuardReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (-row.adjusted_expected_value_edge, row.total_cost_drag, row.research_digest)


def _report_status(
    rows: tuple[ResearchMarketFeeLiquidityExpectedValueGuardReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.guard_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.guard_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeLiquidityExpectedValueGuardReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _status_count(
    rows: tuple[ResearchMarketFeeLiquidityExpectedValueGuardReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.guard_status == status))


def _validate_row(row: ResearchMarketFeeLiquidityExpectedValueGuardReportRow) -> None:
    if row.gross_expected_value_edge != _quantize(
        row.model_probability - row.market_probability,
    ):
        raise ValueError("gross_expected_value_edge must match probabilities")
    expected_fee_liquidity_drag = _quantize(
        row.fee_cost
        + row.spread_cost
        + row.liquidity_shortfall_cost
        + row.slippage_buffer_cost
        + row.settlement_friction_cost,
    )
    if row.total_fee_liquidity_drag != expected_fee_liquidity_drag:
        raise ValueError("total_fee_liquidity_drag must match cost components")
    if row.total_cost_drag != _quantize(
        row.total_fee_liquidity_drag + row.confidence_haircut_cost,
    ):
        raise ValueError("total_cost_drag must match cost components")
    if row.adjusted_expected_value_edge != _quantize(
        row.gross_expected_value_edge - row.total_cost_drag,
    ):
        raise ValueError("adjusted_expected_value_edge must match edge minus costs")
    expected_status_reason = f"expected_value_guard_{row.guard_status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include guard status")


def _validate_report(report: ResearchMarketFeeLiquidityExpectedValueGuardReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    adjusted_edges = tuple(row.adjusted_expected_value_edge for row in report.rows)
    if report.average_adjusted_expected_value_edge != _average(adjusted_edges):
        raise ValueError("average_adjusted_expected_value_edge must match rows")
    expected_top = report.rows[0].adjusted_expected_value_edge if report.rows else None
    if report.top_adjusted_expected_value_edge != expected_top:
        raise ValueError("top_adjusted_expected_value_edge must match rows")
    expected_max_drag = _maximum((row.total_cost_drag for row in report.rows), ZERO)
    if report.max_total_cost_drag != expected_max_drag:
        raise ValueError("max_total_cost_drag must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketFeeLiquidityExpectedValueGuardInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be iterable")
    normalized: list[ResearchMarketFeeLiquidityExpectedValueGuardInput] = []
    for item in inputs:
        if type(item) is not ResearchMarketFeeLiquidityExpectedValueGuardInput:
            raise ValueError(
                "inputs must contain "
                "ResearchMarketFeeLiquidityExpectedValueGuardInput",
            )
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketFeeLiquidityExpectedValueGuardReportRow],
) -> tuple[ResearchMarketFeeLiquidityExpectedValueGuardReportRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketFeeLiquidityExpectedValueGuardReportRow] = []
    for row in rows:
        if type(row) is not ResearchMarketFeeLiquidityExpectedValueGuardReportRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketFeeLiquidityExpectedValueGuardReportRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 4096:
        raise ValueError(f"{field_name} is too long")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
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


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _require_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must be non-empty")
    return tuple(sorted(normalized))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _maximum(values: Iterable[Decimal], default: Decimal) -> Decimal:
    maximum = default
    for value in values:
        if value > maximum:
            maximum = value
    return _quantize(maximum)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _research_digest(value: str) -> str:
    canonical = json.dumps(
        {"ref": value},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchMarketFeeLiquidityExpectedValueGuardReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_validation_digest(
    report: ResearchMarketFeeLiquidityExpectedValueGuardReport,
) -> str:
    payload = _json_ready(_report_values_without_digest(report))
    _reject_unsafe_public_payload(
        "digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_payload_digest(payload: Mapping[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
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
    allow_constructor_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_constructor_containers=allow_constructor_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and not allow_constructor_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
                allow_constructor_containers=allow_constructor_containers,
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
                allow_constructor_containers=allow_constructor_containers,
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
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ResearchMarketFeeLiquidityExpectedValueGuardConfig",
    "ResearchMarketFeeLiquidityExpectedValueGuardInput",
    "ResearchMarketFeeLiquidityExpectedValueGuardReport",
    "ResearchMarketFeeLiquidityExpectedValueGuardReportRow",
    "build_research_market_fee_liquidity_expected_value_guard_report",
    "research_market_fee_liquidity_expected_value_guard_report_payload",
)
