"""Pure public settlement cost pressure report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import reject_unsafe_surface_fields


DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_PRESSURE_CONFIG_VERSION = (
    "research-market-settlement-cost-pressure-report-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "settlement_cost_pressure_clear",
    "aggregate_spread_watch",
    "aggregate_spread_blocking",
    "fee_friction_watch",
    "fee_friction_blocking",
    "settlement_delay_risk_watch",
    "settlement_delay_risk_blocking",
    "depth_fade_watch",
    "depth_fade_blocking",
    "quote_staleness_watch",
    "quote_staleness_blocking",
    "composite_settlement_cost_pressure_watch",
    "composite_settlement_cost_pressure_blocking",
)
REPORT_REASON_CODES = (
    "no_settlement_cost_pressure_observations",
    "settlement_cost_pressure_report_clear",
    "aggregate_spread_pressure_detected",
    "fee_friction_detected",
    "settlement_delay_risk_detected",
    "depth_fade_detected",
    "quote_staleness_detected",
    "composite_settlement_cost_pressure_detected",
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_VALUE = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE_VALUE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "condition_id",
    "market_id",
    "market-slug",
    "market_slug",
    "raw-market",
    "raw_market",
    "raw-source",
    "raw_source",
    "source_id",
    "source_url",
    "source-ref",
    "source_ref",
    "question",
    "secret",
    "private",
    "tok" + "en",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "buy",
    "sell",
    "recommend",
    "size",
)


@dataclass(frozen=True)
class ResearchMarketSettlementCostPressureConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_PRESSURE_CONFIG_VERSION
    aggregate_spread_watch_ratio: Decimal = Decimal("0.020000")
    aggregate_spread_block_ratio: Decimal = Decimal("0.050000")
    fee_friction_watch_ratio: Decimal = Decimal("0.015000")
    fee_friction_block_ratio: Decimal = Decimal("0.040000")
    settlement_delay_watch_score: Decimal = Decimal("0.300000")
    settlement_delay_block_score: Decimal = Decimal("0.700000")
    depth_fade_watch_ratio: Decimal = Decimal("0.250000")
    depth_fade_block_ratio: Decimal = Decimal("0.600000")
    quote_staleness_watch_seconds: Decimal = Decimal("120.000000")
    quote_staleness_block_seconds: Decimal = Decimal("300.000000")
    watch_pressure_score: Decimal = Decimal("0.300000")
    block_pressure_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostPressureConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "aggregate_spread_watch_ratio",
            "aggregate_spread_block_ratio",
            "fee_friction_watch_ratio",
            "fee_friction_block_ratio",
            "settlement_delay_watch_score",
            "settlement_delay_block_score",
            "depth_fade_watch_ratio",
            "depth_fade_block_ratio",
            "quote_staleness_watch_seconds",
            "quote_staleness_block_seconds",
            "watch_pressure_score",
            "block_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "aggregate_spread_watch_ratio",
            self.aggregate_spread_watch_ratio,
            "aggregate_spread_block_ratio",
            self.aggregate_spread_block_ratio,
        )
        _require_threshold_pair(
            "fee_friction_watch_ratio",
            self.fee_friction_watch_ratio,
            "fee_friction_block_ratio",
            self.fee_friction_block_ratio,
        )
        _require_threshold_pair(
            "settlement_delay_watch_score",
            self.settlement_delay_watch_score,
            "settlement_delay_block_score",
            self.settlement_delay_block_score,
        )
        _require_threshold_pair(
            "depth_fade_watch_ratio",
            self.depth_fade_watch_ratio,
            "depth_fade_block_ratio",
            self.depth_fade_block_ratio,
        )
        _require_threshold_pair(
            "quote_staleness_watch_seconds",
            self.quote_staleness_watch_seconds,
            "quote_staleness_block_seconds",
            self.quote_staleness_block_seconds,
        )
        _require_threshold_pair(
            "watch_pressure_score",
            self.watch_pressure_score,
            "block_pressure_score",
            self.block_pressure_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostPressureObservation:
    public_pressure_key: str
    observed_at: datetime
    aggregate_spread_ratio: Decimal
    fee_friction_ratio: Decimal
    settlement_delay_risk_score: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostPressureObservation, "observation")
        _require_public_key("public_pressure_key", self.public_pressure_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_spread_ratio",
            "fee_friction_ratio",
            "settlement_delay_risk_score",
            "depth_fade_ratio",
            "quote_staleness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostPressureRow:
    public_pressure_key: str
    observed_at: datetime
    aggregate_spread_ratio: Decimal
    fee_friction_ratio: Decimal
    settlement_delay_risk_score: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    aggregate_spread_pressure: Decimal
    fee_friction_pressure: Decimal
    settlement_delay_pressure: Decimal
    depth_fade_pressure: Decimal
    quote_staleness_pressure: Decimal
    pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostPressureRow, "row")
        _require_public_key("public_pressure_key", self.public_pressure_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_spread_ratio",
            "fee_friction_ratio",
            "settlement_delay_risk_score",
            "depth_fade_ratio",
            "quote_staleness_seconds",
            "aggregate_spread_pressure",
            "fee_friction_pressure",
            "settlement_delay_pressure",
            "depth_fade_pressure",
            "quote_staleness_pressure",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostPressureReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    spread_pressure_count: Decimal
    fee_friction_count: Decimal
    settlement_delay_risk_count: Decimal
    depth_fade_count: Decimal
    quote_staleness_count: Decimal
    mean_aggregate_spread_ratio: Decimal
    mean_fee_friction_ratio: Decimal
    mean_settlement_delay_risk_score: Decimal
    mean_depth_fade_ratio: Decimal
    mean_quote_staleness_seconds: Decimal
    mean_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchMarketSettlementCostPressureRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostPressureReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "spread_pressure_count",
            "fee_friction_count",
            "settlement_delay_risk_count",
            "depth_fade_count",
            "quote_staleness_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_aggregate_spread_ratio",
            "mean_fee_friction_ratio",
            "mean_settlement_delay_risk_score",
            "mean_depth_fade_ratio",
            "mean_quote_staleness_seconds",
            "mean_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_market_settlement_cost_pressure_report(
    observations: list[ResearchMarketSettlementCostPressureObservation]
    | tuple[ResearchMarketSettlementCostPressureObservation, ...],
    *,
    config: ResearchMarketSettlementCostPressureConfig,
    generated_at: datetime,
) -> ResearchMarketSettlementCostPressureReport:
    if type(config) is not ResearchMarketSettlementCostPressureConfig:
        raise ValueError("config must be a ResearchMarketSettlementCostPressureConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_observations(observations, generated_at_utc)
    rows = tuple(sorted((_row_from_observation(row, config) for row in source_rows), key=_row_key))
    return ResearchMarketSettlementCostPressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(source_rows)),
        row_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        spread_pressure_count=_reason_count(
            rows,
            ("aggregate_spread_watch", "aggregate_spread_blocking"),
        ),
        fee_friction_count=_reason_count(
            rows,
            ("fee_friction_watch", "fee_friction_blocking"),
        ),
        settlement_delay_risk_count=_reason_count(
            rows,
            ("settlement_delay_risk_watch", "settlement_delay_risk_blocking"),
        ),
        depth_fade_count=_reason_count(rows, ("depth_fade_watch", "depth_fade_blocking")),
        quote_staleness_count=_reason_count(
            rows,
            ("quote_staleness_watch", "quote_staleness_blocking"),
        ),
        mean_aggregate_spread_ratio=_mean(tuple(row.aggregate_spread_ratio for row in rows)),
        mean_fee_friction_ratio=_mean(tuple(row.fee_friction_ratio for row in rows)),
        mean_settlement_delay_risk_score=_mean(
            tuple(row.settlement_delay_risk_score for row in rows),
        ),
        mean_depth_fade_ratio=_mean(tuple(row.depth_fade_ratio for row in rows)),
        mean_quote_staleness_seconds=_mean(tuple(row.quote_staleness_seconds for row in rows)),
        mean_pressure_score=_mean(tuple(row.pressure_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_market_settlement_cost_pressure_report_payload(
    report: ResearchMarketSettlementCostPressureReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketSettlementCostPressureReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketSettlementCostPressureReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    reject_unsafe_surface_fields("settlement cost pressure payload", payload)
    _reject_unsafe_public_strings("settlement cost pressure payload", payload)
    return payload


def research_market_settlement_cost_pressure_report_digest(
    report: ResearchMarketSettlementCostPressureReport | dict[str, Any],
) -> str:
    payload = research_market_settlement_cost_pressure_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


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


def _row_from_observation(
    row: ResearchMarketSettlementCostPressureObservation,
    config: ResearchMarketSettlementCostPressureConfig,
) -> ResearchMarketSettlementCostPressureRow:
    aggregate_spread_pressure = _pressure(
        row.aggregate_spread_ratio,
        config.aggregate_spread_block_ratio,
    )
    fee_friction_pressure = _pressure(row.fee_friction_ratio, config.fee_friction_block_ratio)
    settlement_delay_pressure = _pressure(
        row.settlement_delay_risk_score,
        config.settlement_delay_block_score,
    )
    depth_fade_pressure = _pressure(row.depth_fade_ratio, config.depth_fade_block_ratio)
    quote_staleness_pressure = _pressure(
        row.quote_staleness_seconds,
        config.quote_staleness_block_seconds,
    )
    pressure_score = _mean(
        (
            aggregate_spread_pressure,
            fee_friction_pressure,
            settlement_delay_pressure,
            depth_fade_pressure,
            quote_staleness_pressure,
        ),
    )
    return ResearchMarketSettlementCostPressureRow(
        public_pressure_key=row.public_pressure_key,
        observed_at=row.observed_at,
        aggregate_spread_ratio=row.aggregate_spread_ratio,
        fee_friction_ratio=row.fee_friction_ratio,
        settlement_delay_risk_score=row.settlement_delay_risk_score,
        depth_fade_ratio=row.depth_fade_ratio,
        quote_staleness_seconds=row.quote_staleness_seconds,
        aggregate_spread_pressure=aggregate_spread_pressure,
        fee_friction_pressure=fee_friction_pressure,
        settlement_delay_pressure=settlement_delay_pressure,
        depth_fade_pressure=depth_fade_pressure,
        quote_staleness_pressure=quote_staleness_pressure,
        pressure_score=pressure_score,
        status=_row_status(row, pressure_score, config),
        reason_codes=_row_reason_codes(row, pressure_score, config),
    )


def _row_status(
    row: ResearchMarketSettlementCostPressureObservation,
    pressure_score: Decimal,
    config: ResearchMarketSettlementCostPressureConfig,
) -> str:
    if (
        row.aggregate_spread_ratio >= config.aggregate_spread_block_ratio
        or row.fee_friction_ratio >= config.fee_friction_block_ratio
        or row.settlement_delay_risk_score >= config.settlement_delay_block_score
        or row.depth_fade_ratio >= config.depth_fade_block_ratio
        or row.quote_staleness_seconds >= config.quote_staleness_block_seconds
        or pressure_score >= config.block_pressure_score
    ):
        return "block"
    if (
        row.aggregate_spread_ratio >= config.aggregate_spread_watch_ratio
        or row.fee_friction_ratio >= config.fee_friction_watch_ratio
        or row.settlement_delay_risk_score >= config.settlement_delay_watch_score
        or row.depth_fade_ratio >= config.depth_fade_watch_ratio
        or row.quote_staleness_seconds >= config.quote_staleness_watch_seconds
        or pressure_score >= config.watch_pressure_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ResearchMarketSettlementCostPressureObservation,
    pressure_score: Decimal,
    config: ResearchMarketSettlementCostPressureConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_code(
        codes,
        row.aggregate_spread_ratio,
        config.aggregate_spread_watch_ratio,
        config.aggregate_spread_block_ratio,
        "aggregate_spread_watch",
        "aggregate_spread_blocking",
    )
    _append_threshold_code(
        codes,
        row.fee_friction_ratio,
        config.fee_friction_watch_ratio,
        config.fee_friction_block_ratio,
        "fee_friction_watch",
        "fee_friction_blocking",
    )
    _append_threshold_code(
        codes,
        row.settlement_delay_risk_score,
        config.settlement_delay_watch_score,
        config.settlement_delay_block_score,
        "settlement_delay_risk_watch",
        "settlement_delay_risk_blocking",
    )
    _append_threshold_code(
        codes,
        row.depth_fade_ratio,
        config.depth_fade_watch_ratio,
        config.depth_fade_block_ratio,
        "depth_fade_watch",
        "depth_fade_blocking",
    )
    _append_threshold_code(
        codes,
        row.quote_staleness_seconds,
        config.quote_staleness_watch_seconds,
        config.quote_staleness_block_seconds,
        "quote_staleness_watch",
        "quote_staleness_blocking",
    )
    _append_threshold_code(
        codes,
        pressure_score,
        config.watch_pressure_score,
        config.block_pressure_score,
        "composite_settlement_cost_pressure_watch",
        "composite_settlement_cost_pressure_blocking",
    )
    if not codes:
        return ("settlement_cost_pressure_clear",)
    return tuple(codes)


def _append_threshold_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block_threshold:
        codes.append(block_code)
    elif value >= watch_threshold:
        codes.append(watch_code)


def _report_status(rows: tuple[ResearchMarketSettlementCostPressureRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementCostPressureRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_settlement_cost_pressure_observations",)
    if all(row.status == "pass" for row in rows):
        return ("settlement_cost_pressure_report_clear",)
    codes: list[str] = []
    if _has_any_row_reason(rows, ("aggregate_spread_watch", "aggregate_spread_blocking")):
        codes.append("aggregate_spread_pressure_detected")
    if _has_any_row_reason(rows, ("fee_friction_watch", "fee_friction_blocking")):
        codes.append("fee_friction_detected")
    if _has_any_row_reason(
        rows,
        ("settlement_delay_risk_watch", "settlement_delay_risk_blocking"),
    ):
        codes.append("settlement_delay_risk_detected")
    if _has_any_row_reason(rows, ("depth_fade_watch", "depth_fade_blocking")):
        codes.append("depth_fade_detected")
    if _has_any_row_reason(rows, ("quote_staleness_watch", "quote_staleness_blocking")):
        codes.append("quote_staleness_detected")
    if _has_any_row_reason(
        rows,
        (
            "composite_settlement_cost_pressure_watch",
            "composite_settlement_cost_pressure_blocking",
        ),
    ):
        codes.append("composite_settlement_cost_pressure_detected")
    return tuple(codes)


def _has_any_row_reason(
    rows: tuple[ResearchMarketSettlementCostPressureRow, ...],
    reason_codes: tuple[str, ...],
) -> bool:
    return any(any(code in row.reason_codes for code in reason_codes) for row in rows)


def _reason_count(
    rows: tuple[ResearchMarketSettlementCostPressureRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)))


def _row_key(row: ResearchMarketSettlementCostPressureRow) -> tuple[Decimal, Decimal, str]:
    rank = {"block": Decimal("2"), "watch": Decimal("1"), "pass": Decimal("0")}[
        row.status
    ]
    return (-rank, -row.pressure_score, row.public_pressure_key)


def _validate_row(row: ResearchMarketSettlementCostPressureRow) -> None:
    if row.status == "pass" and row.reason_codes != ("settlement_cost_pressure_clear",):
        raise ValueError("pass row reason_codes must be clear")
    if row.status in ("watch", "block") and row.reason_codes == (
        "settlement_cost_pressure_clear",
    ):
        raise ValueError("pressure row reason_codes must not be clear")
    if row.status == "block" and not any(code.endswith("_blocking") for code in row.reason_codes):
        raise ValueError("block row reason_codes must contain blocking checks")
    if row.status == "watch" and any(code.endswith("_blocking") for code in row.reason_codes):
        raise ValueError("watch row reason_codes must not contain blocking checks")


def _validate_report(report: ResearchMarketSettlementCostPressureReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.spread_pressure_count != _reason_count(
        report.rows,
        ("aggregate_spread_watch", "aggregate_spread_blocking"),
    ):
        raise ValueError("spread_pressure_count must match rows")
    if report.fee_friction_count != _reason_count(
        report.rows,
        ("fee_friction_watch", "fee_friction_blocking"),
    ):
        raise ValueError("fee_friction_count must match rows")
    if report.settlement_delay_risk_count != _reason_count(
        report.rows,
        ("settlement_delay_risk_watch", "settlement_delay_risk_blocking"),
    ):
        raise ValueError("settlement_delay_risk_count must match rows")
    if report.depth_fade_count != _reason_count(
        report.rows,
        ("depth_fade_watch", "depth_fade_blocking"),
    ):
        raise ValueError("depth_fade_count must match rows")
    if report.quote_staleness_count != _reason_count(
        report.rows,
        ("quote_staleness_watch", "quote_staleness_blocking"),
    ):
        raise ValueError("quote_staleness_count must match rows")
    if report.mean_aggregate_spread_ratio != _mean(
        tuple(row.aggregate_spread_ratio for row in report.rows),
    ):
        raise ValueError("mean_aggregate_spread_ratio must match rows")
    if report.mean_fee_friction_ratio != _mean(tuple(row.fee_friction_ratio for row in report.rows)):
        raise ValueError("mean_fee_friction_ratio must match rows")
    if report.mean_settlement_delay_risk_score != _mean(
        tuple(row.settlement_delay_risk_score for row in report.rows),
    ):
        raise ValueError("mean_settlement_delay_risk_score must match rows")
    if report.mean_depth_fade_ratio != _mean(tuple(row.depth_fade_ratio for row in report.rows)):
        raise ValueError("mean_depth_fade_ratio must match rows")
    if report.mean_quote_staleness_seconds != _mean(
        tuple(row.quote_staleness_seconds for row in report.rows),
    ):
        raise ValueError("mean_quote_staleness_seconds must match rows")
    if report.mean_pressure_score != _mean(tuple(row.pressure_score for row in report.rows)):
        raise ValueError("mean_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must be deterministic")
    keys = tuple(row.public_pressure_key for row in report.rows)
    if len(set(keys)) != len(keys):
        raise ValueError("rows must contain unique public_pressure_key values")


def _normalize_observations(
    observations: list[ResearchMarketSettlementCostPressureObservation]
    | tuple[ResearchMarketSettlementCostPressureObservation, ...],
    generated_at: datetime,
) -> tuple[ResearchMarketSettlementCostPressureObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketSettlementCostPressureObservation:
            raise ValueError(
                "observations must contain ResearchMarketSettlementCostPressureObservation values",
            )
        _require_hard_flags("observation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if row.public_pressure_key in seen:
            raise ValueError("observations must contain unique public_pressure_key values")
        seen.add(row.public_pressure_key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketSettlementCostPressureRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not ResearchMarketSettlementCostPressureRow:
            raise ValueError(
                "rows must contain ResearchMarketSettlementCostPressureRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _reason_code_counts_from_rows(
    rows: tuple[ResearchMarketSettlementCostPressureRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for code in row.reason_codes:
            counts[code] = counts.get(code, 0) + 1
    return tuple((code, _count(count)) for code, count in sorted(counts.items()))


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    normalized: list[tuple[str, Decimal]] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason code count tuples")
        code, count = row
        _require_member("reason_code_counts reason_code", code, ROW_REASON_CODES)
        normalized.append(
            (code, _normalize_nonnegative_count("reason_code_counts count", count)),
        )
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _pressure(value: Decimal, block_threshold: Decimal) -> Decimal:
    if block_threshold <= ZERO_VALUE:
        raise ValueError("block threshold must be positive")
    with localcontext(DECIMAL_CONTEXT):
        pressure = value / block_threshold
    if pressure > ONE_VALUE:
        pressure = ONE_VALUE
    return _normalize_nonnegative_value("pressure", pressure)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_VALUE
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_VALUE)
        return _normalize_nonnegative_value("mean", total / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    checked = _require_decimal(field_name, value)
    if checked < ZERO_VALUE:
        raise ValueError(f"{field_name} must be nonnegative")
    return checked.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    checked = _require_decimal(field_name, value)
    if checked < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    integral = checked.quantize(COUNT_QUANTUM)
    if checked != integral:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return integral


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} must be public-safe")


def _require_public_key(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _contains_sensitive_text(value):
        raise ValueError(f"{field_name} must be public-safe")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_strings(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_surface_fragment(value) or _contains_sensitive_text(value):
            raise ValueError(f"unsafe surface value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_strings(label, item)


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _contains_sensitive_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in ("secret", "private", "raw-"))


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_PRESSURE_CONFIG_VERSION",
    "ResearchMarketSettlementCostPressureConfig",
    "ResearchMarketSettlementCostPressureObservation",
    "ResearchMarketSettlementCostPressureReport",
    "ResearchMarketSettlementCostPressureRow",
    "STATUSES",
    "build_research_market_settlement_cost_pressure_report",
    "research_market_settlement_cost_pressure_report_digest",
    "research_market_settlement_cost_pressure_report_payload",
)
