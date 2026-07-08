"""Pure aggregate liquidity-cost anomaly backlog report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_ANOMALY_BACKLOG_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-cost-anomaly-backlog-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
BACKLOG_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

SPREAD_SHOCK_BLOCK_REASON = "liquidity_cost_spread_shock_block"
SPREAD_SHOCK_WATCH_REASON = "liquidity_cost_spread_shock_watch"
DEPTH_FADE_BLOCK_REASON = "liquidity_cost_depth_fade_block"
DEPTH_FADE_WATCH_REASON = "liquidity_cost_depth_fade_watch"
QUOTE_STALENESS_BLOCK_REASON = "liquidity_cost_quote_staleness_block"
QUOTE_STALENESS_WATCH_REASON = "liquidity_cost_quote_staleness_watch"
FEE_FRICTION_BLOCK_REASON = "liquidity_cost_fee_friction_block"
FEE_FRICTION_WATCH_REASON = "liquidity_cost_fee_friction_watch"
VOLUME_BURST_BLOCK_REASON = "liquidity_cost_volume_burst_block"
VOLUME_BURST_WATCH_REASON = "liquidity_cost_volume_burst_watch"
PASS_REASON = "liquidity_cost_anomaly_pass"
WATCH_PRESENT_REASON = "liquidity_cost_anomaly_watch_present"
CLEAR_REASON = "liquidity_cost_anomaly_backlog_clear"
EMPTY_REASON = "liquidity_cost_anomaly_backlog_empty"

ROW_REASON_CODE_SEQUENCE = (
    SPREAD_SHOCK_BLOCK_REASON,
    SPREAD_SHOCK_WATCH_REASON,
    DEPTH_FADE_BLOCK_REASON,
    DEPTH_FADE_WATCH_REASON,
    QUOTE_STALENESS_BLOCK_REASON,
    QUOTE_STALENESS_WATCH_REASON,
    FEE_FRICTION_BLOCK_REASON,
    FEE_FRICTION_WATCH_REASON,
    VOLUME_BURST_BLOCK_REASON,
    VOLUME_BURST_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    SPREAD_SHOCK_BLOCK_REASON,
    SPREAD_SHOCK_WATCH_REASON,
    DEPTH_FADE_BLOCK_REASON,
    DEPTH_FADE_WATCH_REASON,
    QUOTE_STALENESS_BLOCK_REASON,
    QUOTE_STALENESS_WATCH_REASON,
    FEE_FRICTION_BLOCK_REASON,
    FEE_FRICTION_WATCH_REASON,
    VOLUME_BURST_BLOCK_REASON,
    VOLUME_BURST_WATCH_REASON,
    WATCH_PRESENT_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BLOCK_REASON_CODES = (
    SPREAD_SHOCK_BLOCK_REASON,
    DEPTH_FADE_BLOCK_REASON,
    QUOTE_STALENESS_BLOCK_REASON,
    FEE_FRICTION_BLOCK_REASON,
    VOLUME_BURST_BLOCK_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_SHA256_PUBLIC_KEY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_ANOMALY_BACKLOG_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityCostAnomalyBacklogReportConfig",
    "ResearchMarketLiquidityCostAnomalyBacklogReportInput",
    "ResearchMarketLiquidityCostAnomalyBacklogRow",
    "ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount",
    "ResearchMarketLiquidityCostAnomalyBacklogReport",
    "build_research_market_liquidity_cost_anomaly_backlog_report",
    "research_market_liquidity_cost_anomaly_backlog_report_digest",
    "research_market_liquidity_cost_anomaly_backlog_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostAnomalyBacklogReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_ANOMALY_BACKLOG_REPORT_CONFIG_VERSION
    )
    watch_spread_shock_bps: Decimal = Decimal("10.000000")
    block_spread_shock_bps: Decimal = Decimal("35.000000")
    watch_depth_fade_ratio: Decimal = Decimal("0.250000")
    block_depth_fade_ratio: Decimal = Decimal("0.650000")
    watch_quote_staleness_seconds: Decimal = Decimal("120.000000")
    block_quote_staleness_seconds: Decimal = Decimal("300.000000")
    watch_fee_friction_bps: Decimal = Decimal("20.000000")
    block_fee_friction_bps: Decimal = Decimal("60.000000")
    watch_volume_burst_ratio: Decimal = Decimal("2.000000")
    block_volume_burst_ratio: Decimal = Decimal("5.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostAnomalyBacklogReportConfig:
            raise TypeError(
                "ResearchMarketLiquidityCostAnomalyBacklogReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostAnomalyBacklogReportConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_ANOMALY_BACKLOG_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_spread_shock_bps",
            "block_spread_shock_bps",
            "watch_quote_staleness_seconds",
            "block_quote_staleness_seconds",
            "watch_fee_friction_bps",
            "block_fee_friction_bps",
            "watch_volume_burst_ratio",
            "block_volume_burst_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_depth_fade_ratio",
            "block_depth_fade_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_block(
            "watch_spread_shock_bps",
            self.watch_spread_shock_bps,
            "block_spread_shock_bps",
            self.block_spread_shock_bps,
        )
        _require_watch_not_above_block(
            "watch_depth_fade_ratio",
            self.watch_depth_fade_ratio,
            "block_depth_fade_ratio",
            self.block_depth_fade_ratio,
        )
        _require_watch_not_above_block(
            "watch_quote_staleness_seconds",
            self.watch_quote_staleness_seconds,
            "block_quote_staleness_seconds",
            self.block_quote_staleness_seconds,
        )
        _require_watch_not_above_block(
            "watch_fee_friction_bps",
            self.watch_fee_friction_bps,
            "block_fee_friction_bps",
            self.block_fee_friction_bps,
        )
        _require_watch_not_above_block(
            "watch_volume_burst_ratio",
            self.watch_volume_burst_ratio,
            "block_volume_burst_ratio",
            self.block_volume_burst_ratio,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostAnomalyBacklogReportInput:
    public_backlog_key: str
    observed_at: datetime
    spread_shock_bps: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    fee_friction_bps: Decimal
    volume_burst_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostAnomalyBacklogReportInput:
            raise TypeError(
                "ResearchMarketLiquidityCostAnomalyBacklogReportInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostAnomalyBacklogReportInput,
            "input",
        )
        _require_public_backlog_key(self.public_backlog_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_shock_bps",
            "quote_staleness_seconds",
            "fee_friction_bps",
            "volume_burst_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "depth_fade_ratio",
            _require_ratio_decimal("depth_fade_ratio", self.depth_fade_ratio),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostAnomalyBacklogRow:
    public_backlog_key: str
    observed_at: datetime
    spread_shock_bps: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    fee_friction_bps: Decimal
    volume_burst_ratio: Decimal
    backlog_status: str
    risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostAnomalyBacklogRow:
            raise TypeError(
                "ResearchMarketLiquidityCostAnomalyBacklogRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostAnomalyBacklogRow, "row")
        _require_public_backlog_key(self.public_backlog_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_shock_bps",
            "quote_staleness_seconds",
            "fee_friction_bps",
            "volume_burst_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "depth_fade_ratio",
            _require_ratio_decimal("depth_fade_ratio", self.depth_fade_ratio),
        )
        _require_member("backlog_status", self.backlog_status, BACKLOG_STATUSES)
        object.__setattr__(
            self,
            "risk_score",
            _require_ratio_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount:
            raise TypeError(
                "ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostAnomalyBacklogReport:
    generated_at: datetime
    config_version: str
    backlog_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    spread_shock_count: Decimal
    depth_fade_count: Decimal
    quote_staleness_count: Decimal
    fee_friction_count: Decimal
    volume_burst_count: Decimal
    max_spread_shock_bps: Decimal
    max_depth_fade_ratio: Decimal
    max_quote_staleness_seconds: Decimal
    max_fee_friction_bps: Decimal
    max_volume_burst_ratio: Decimal
    liquidity_cost_anomaly_score: Decimal
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount,
        ...,
    ]
    report_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostAnomalyBacklogReport:
            raise TypeError(
                "ResearchMarketLiquidityCostAnomalyBacklogReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostAnomalyBacklogReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_ANOMALY_BACKLOG_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("backlog_status", self.backlog_status, BACKLOG_STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "spread_shock_count",
            "depth_fade_count",
            "quote_staleness_count",
            "fee_friction_count",
            "volume_burst_count",
            "max_spread_shock_bps",
            "max_depth_fade_ratio",
            "max_quote_staleness_seconds",
            "max_fee_friction_bps",
            "max_volume_burst_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_cost_anomaly_score",
            _require_ratio_decimal(
                "liquidity_cost_anomaly_score",
                self.liquidity_cost_anomaly_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.report_digest == "":
            object.__setattr__(self, "report_digest", expected_digest)
        elif self.report_digest != expected_digest:
            raise ValueError("report_digest must match report payload")
        _require_prefixed_sha256_digest("report_digest", self.report_digest)
        _require_hard_flags("report", self)


def build_research_market_liquidity_cost_anomaly_backlog_report(
    inputs: tuple[object, ...],
    *,
    config: ResearchMarketLiquidityCostAnomalyBacklogReportConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketLiquidityCostAnomalyBacklogReport:
    cfg = config or ResearchMarketLiquidityCostAnomalyBacklogReportConfig()
    if type(cfg) is not ResearchMarketLiquidityCostAnomalyBacklogReportConfig:
        raise ValueError(
            "config must be exactly ResearchMarketLiquidityCostAnomalyBacklogReportConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at cannot be after generated_at")
    rows = tuple(
        sorted(
            (_build_row(row, config=cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    backlog_status = _report_status(rows)
    return ResearchMarketLiquidityCostAnomalyBacklogReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        backlog_status=backlog_status,
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        spread_shock_count=(
            _reason_count(SPREAD_SHOCK_BLOCK_REASON, rows)
            + _reason_count(SPREAD_SHOCK_WATCH_REASON, rows)
        ),
        depth_fade_count=(
            _reason_count(DEPTH_FADE_BLOCK_REASON, rows)
            + _reason_count(DEPTH_FADE_WATCH_REASON, rows)
        ),
        quote_staleness_count=(
            _reason_count(QUOTE_STALENESS_BLOCK_REASON, rows)
            + _reason_count(QUOTE_STALENESS_WATCH_REASON, rows)
        ),
        fee_friction_count=(
            _reason_count(FEE_FRICTION_BLOCK_REASON, rows)
            + _reason_count(FEE_FRICTION_WATCH_REASON, rows)
        ),
        volume_burst_count=(
            _reason_count(VOLUME_BURST_BLOCK_REASON, rows)
            + _reason_count(VOLUME_BURST_WATCH_REASON, rows)
        ),
        max_spread_shock_bps=_max_decimal(
            (row.spread_shock_bps for row in rows),
            default=ZERO,
        ),
        max_depth_fade_ratio=_max_decimal(
            (row.depth_fade_ratio for row in rows),
            default=ZERO,
        ),
        max_quote_staleness_seconds=_max_decimal(
            (row.quote_staleness_seconds for row in rows),
            default=ZERO,
        ),
        max_fee_friction_bps=_max_decimal(
            (row.fee_friction_bps for row in rows),
            default=ZERO,
        ),
        max_volume_burst_ratio=_max_decimal(
            (row.volume_burst_ratio for row in rows),
            default=ZERO,
        ),
        liquidity_cost_anomaly_score=_report_risk_score(rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def research_market_liquidity_cost_anomaly_backlog_report_payload(
    report: ResearchMarketLiquidityCostAnomalyBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityCostAnomalyBacklogReport:
        raise ValueError(
            "report must be exactly ResearchMarketLiquidityCostAnomalyBacklogReport",
        )
    _validate_report_consistency(report)
    if report.report_digest != _report_digest(report):
        raise ValueError("report_digest must match report payload")
    return _payload_value(report)


def research_market_liquidity_cost_anomaly_backlog_report_digest(
    report: ResearchMarketLiquidityCostAnomalyBacklogReport,
) -> str:
    if type(report) is not ResearchMarketLiquidityCostAnomalyBacklogReport:
        raise ValueError(
            "report must be exactly ResearchMarketLiquidityCostAnomalyBacklogReport",
        )
    _validate_report_consistency(report)
    return _report_digest(report)


def _build_row(
    row: ResearchMarketLiquidityCostAnomalyBacklogReportInput,
    *,
    config: ResearchMarketLiquidityCostAnomalyBacklogReportConfig,
) -> ResearchMarketLiquidityCostAnomalyBacklogRow:
    reason_codes = _row_reason_codes(row, config=config)
    backlog_status = _row_status(reason_codes)
    return ResearchMarketLiquidityCostAnomalyBacklogRow(
        public_backlog_key=row.public_backlog_key,
        observed_at=row.observed_at,
        spread_shock_bps=row.spread_shock_bps,
        depth_fade_ratio=row.depth_fade_ratio,
        quote_staleness_seconds=row.quote_staleness_seconds,
        fee_friction_bps=row.fee_friction_bps,
        volume_burst_ratio=row.volume_burst_ratio,
        backlog_status=backlog_status,
        risk_score=_status_risk_score(backlog_status),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchMarketLiquidityCostAnomalyBacklogReportInput,
    *,
    config: ResearchMarketLiquidityCostAnomalyBacklogReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.spread_shock_bps >= config.block_spread_shock_bps:
        reasons.append(SPREAD_SHOCK_BLOCK_REASON)
    elif row.spread_shock_bps >= config.watch_spread_shock_bps:
        reasons.append(SPREAD_SHOCK_WATCH_REASON)
    if row.depth_fade_ratio >= config.block_depth_fade_ratio:
        reasons.append(DEPTH_FADE_BLOCK_REASON)
    elif row.depth_fade_ratio >= config.watch_depth_fade_ratio:
        reasons.append(DEPTH_FADE_WATCH_REASON)
    if row.quote_staleness_seconds >= config.block_quote_staleness_seconds:
        reasons.append(QUOTE_STALENESS_BLOCK_REASON)
    elif row.quote_staleness_seconds >= config.watch_quote_staleness_seconds:
        reasons.append(QUOTE_STALENESS_WATCH_REASON)
    if row.fee_friction_bps >= config.block_fee_friction_bps:
        reasons.append(FEE_FRICTION_BLOCK_REASON)
    elif row.fee_friction_bps >= config.watch_fee_friction_bps:
        reasons.append(FEE_FRICTION_WATCH_REASON)
    if row.volume_burst_ratio >= config.block_volume_burst_ratio:
        reasons.append(VOLUME_BURST_BLOCK_REASON)
    elif row.volume_burst_ratio >= config.watch_volume_burst_ratio:
        reasons.append(VOLUME_BURST_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASON_CODES for reason in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _status_risk_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ONE
    if status == STATUS_WATCH:
        return WATCH_RISK_SCORE
    return ZERO


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes if reason != PASS_REASON}
    reasons = [reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in present]
    if any(row.backlog_status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_PRESENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _report_status(
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.backlog_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.backlog_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> tuple[ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount, ...]:
    row_count = _decimal_count(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> Decimal:
    if reason_code == WATCH_PRESENT_REASON:
        return _status_count(rows, STATUS_WATCH)
    if reason_code == CLEAR_REASON:
        return _status_count(rows, STATUS_PASS)
    return _reason_count(reason_code, rows)


def _reason_count(
    reason_code: str,
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.backlog_status == status))


def _report_risk_score(
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    weighted = _status_count(rows, STATUS_BLOCK) + (
        _status_count(rows, STATUS_WATCH) * WATCH_RISK_SCORE
    )
    return _ratio(weighted, _decimal_count(len(rows)))


def _validate_row_consistency(row: ResearchMarketLiquidityCostAnomalyBacklogRow) -> None:
    if row.backlog_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match backlog_status")
    if row.risk_score != _status_risk_score(row.backlog_status):
        raise ValueError("risk_score must match backlog_status")
    if row.backlog_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must match backlog_status")
    if row.backlog_status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must match backlog_status")


def _validate_report_consistency(report: ResearchMarketLiquidityCostAnomalyBacklogReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.spread_shock_count != (
        _reason_count(SPREAD_SHOCK_BLOCK_REASON, report.rows)
        + _reason_count(SPREAD_SHOCK_WATCH_REASON, report.rows)
    ):
        raise ValueError("spread_shock_count must match rows")
    if report.depth_fade_count != (
        _reason_count(DEPTH_FADE_BLOCK_REASON, report.rows)
        + _reason_count(DEPTH_FADE_WATCH_REASON, report.rows)
    ):
        raise ValueError("depth_fade_count must match rows")
    if report.quote_staleness_count != (
        _reason_count(QUOTE_STALENESS_BLOCK_REASON, report.rows)
        + _reason_count(QUOTE_STALENESS_WATCH_REASON, report.rows)
    ):
        raise ValueError("quote_staleness_count must match rows")
    if report.fee_friction_count != (
        _reason_count(FEE_FRICTION_BLOCK_REASON, report.rows)
        + _reason_count(FEE_FRICTION_WATCH_REASON, report.rows)
    ):
        raise ValueError("fee_friction_count must match rows")
    if report.volume_burst_count != (
        _reason_count(VOLUME_BURST_BLOCK_REASON, report.rows)
        + _reason_count(VOLUME_BURST_WATCH_REASON, report.rows)
    ):
        raise ValueError("volume_burst_count must match rows")
    if report.max_spread_shock_bps != _max_decimal(
        (row.spread_shock_bps for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_shock_bps must match rows")
    if report.max_depth_fade_ratio != _max_decimal(
        (row.depth_fade_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_depth_fade_ratio must match rows")
    if report.max_quote_staleness_seconds != _max_decimal(
        (row.quote_staleness_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_quote_staleness_seconds must match rows")
    if report.max_fee_friction_bps != _max_decimal(
        (row.fee_friction_bps for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_fee_friction_bps must match rows")
    if report.max_volume_burst_ratio != _max_decimal(
        (row.volume_burst_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_volume_burst_ratio must match rows")
    if report.liquidity_cost_anomaly_score != _report_risk_score(report.rows):
        raise ValueError("liquidity_cost_anomaly_score must match rows")
    if report.backlog_status != _report_status(report.rows):
        raise ValueError("backlog_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: tuple[object, ...],
) -> tuple[ResearchMarketLiquidityCostAnomalyBacklogReportInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    seen_public_keys: set[str] = set()
    normalized: list[ResearchMarketLiquidityCostAnomalyBacklogReportInput] = []
    for row in inputs:
        if type(row) is not ResearchMarketLiquidityCostAnomalyBacklogReportInput:
            raise ValueError(
                "inputs must contain ResearchMarketLiquidityCostAnomalyBacklogReportInput",
            )
        _require_hard_flags("input", row)
        if row.public_backlog_key in seen_public_keys:
            raise ValueError(
                "inputs must not contain duplicate public_backlog_key values",
            )
        seen_public_keys.add(row.public_backlog_key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...],
) -> tuple[ResearchMarketLiquidityCostAnomalyBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_public_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketLiquidityCostAnomalyBacklogRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityCostAnomalyBacklogRow",
            )
        _require_hard_flags("row", row)
        if row.public_backlog_key in seen_public_keys:
            raise ValueError("rows must not contain duplicate public_backlog_key values")
        seen_public_keys.add(row.public_backlog_key)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: tuple[ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return tuple(
        sorted(rows, key=lambda row: REPORT_REASON_CODE_SEQUENCE.index(row.reason_code)),
    )


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(reason_codes)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_member("reason_code", reason_code, sequence)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in sequence if reason_code in seen)


def _row_sort_key(
    row: ResearchMarketLiquidityCostAnomalyBacklogRow,
) -> tuple[int, Decimal, str]:
    status_rank = {
        STATUS_BLOCK: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }
    return (
        status_rank[row.backlog_status],
        -row.risk_score,
        row.public_backlog_key,
    )


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    for value in normalized:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize(max(normalized))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_watch_not_above_block(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_field_name} must not exceed {block_field_name}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_backlog_key(value: object) -> None:
    if type(value) is not str:
        raise ValueError("public_backlog_key must be a plain str")
    if _SHA256_PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError("public_backlog_key must be a prefixed lowercase sha256 digest")


def _require_prefixed_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if _SHA256_PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a prefixed lowercase sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _report_digest(report: ResearchMarketLiquidityCostAnomalyBacklogReport) -> str:
    payload = _payload_value(report)
    payload.pop("report_digest", None)
    encoded_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
