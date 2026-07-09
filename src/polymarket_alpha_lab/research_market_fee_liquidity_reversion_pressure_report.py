"""Report-only fee/liquidity reversion pressure monitor."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_REVERSION_PRESSURE_CONFIG_VERSION",
    "ResearchMarketFeeLiquidityReversionPressureConfig",
    "ResearchMarketFeeLiquidityReversionPressureInput",
    "ResearchMarketFeeLiquidityReversionPressureReasonCodeCount",
    "ResearchMarketFeeLiquidityReversionPressureReport",
    "ResearchMarketFeeLiquidityReversionPressureReportRow",
    "build_research_market_fee_liquidity_reversion_pressure_report",
    "research_market_fee_liquidity_reversion_pressure_report_digest",
    "research_market_fee_liquidity_reversion_pressure_report_payload",
    "validate_research_market_fee_liquidity_reversion_pressure_public_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_REVERSION_PRESSURE_CONFIG_VERSION = (
    "research-market-fee-liquidity-reversion-pressure-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_fee_liquidity_reversion_pressure_inputs"
REASON_PASS = "fee_liquidity_reversion_pressure_pass"
REASON_WATCH = "fee_liquidity_reversion_pressure_watch"
REASON_BLOCK = "fee_liquidity_reversion_pressure_block"
REASON_RAW_WATCH = "raw_reversion_pressure_watch"
REASON_RAW_BLOCK = "raw_reversion_pressure_block"
REASON_NET_WATCH = "net_reversion_pressure_watch"
REASON_NET_BLOCK = "net_reversion_pressure_block"
REASON_DRAG_WATCH = "fee_liquidity_drag_watch"
REASON_DRAG_BLOCK = "fee_liquidity_drag_block"
REASON_DEPTH_WATCH = "depth_coverage_watch"
REASON_DEPTH_BLOCK = "depth_coverage_block"
REASON_FEE = "fee_drag_applied"
REASON_SPREAD = "spread_drag_applied"
REASON_LIQUIDITY = "liquidity_shortfall_applied"
REASON_SLIPPAGE = "slippage_buffer_applied"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_BLOCK,
    REASON_WATCH,
    REASON_PASS,
    REASON_RAW_BLOCK,
    REASON_RAW_WATCH,
    REASON_NET_BLOCK,
    REASON_NET_WATCH,
    REASON_DRAG_BLOCK,
    REASON_DRAG_WATCH,
    REASON_DEPTH_BLOCK,
    REASON_DEPTH_WATCH,
    REASON_FEE,
    REASON_SPREAD,
    REASON_LIQUIDITY,
    REASON_SLIPPAGE,
)
REASON_CODE_SET = frozenset(REASON_CODES)
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "=",
    _join_parts("api", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("candidate", "_", "id"),
    _join_parts("creden", "tial"),
    _join_parts("d", "s", "n"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "sl", "ug"),
    _join_parts("private", "_", "key"),
    _join_parts("private", "_", "research", "_", "reference"),
    _join_parts("que", "stion"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "mar", "ket"),
    _join_parts("sec", "ret"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("pos", "ition"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityReversionPressureConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_REVERSION_PRESSURE_CONFIG_VERSION
    )
    watch_raw_reversion_pressure_rate: Decimal = Decimal("0.100000")
    block_raw_reversion_pressure_rate: Decimal = Decimal("0.250000")
    watch_net_reversion_pressure_rate: Decimal = Decimal("0.050000")
    block_net_reversion_pressure_rate: Decimal = Decimal("0.120000")
    watch_fee_liquidity_drag_rate: Decimal = Decimal("0.030000")
    block_fee_liquidity_drag_rate: Decimal = Decimal("0.080000")
    watch_min_depth_coverage_ratio: Decimal = Decimal("1.000000")
    block_min_depth_coverage_ratio: Decimal = Decimal("0.500000")
    depth_shortfall_penalty_rate: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeLiquidityReversionPressureConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeLiquidityReversionPressureConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_REVERSION_PRESSURE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_raw_reversion_pressure_rate",
            "block_raw_reversion_pressure_rate",
            "watch_net_reversion_pressure_rate",
            "block_net_reversion_pressure_rate",
            "watch_fee_liquidity_drag_rate",
            "block_fee_liquidity_drag_rate",
            "watch_min_depth_coverage_ratio",
            "block_min_depth_coverage_ratio",
            "depth_shortfall_penalty_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending(
            "raw_reversion_pressure_rate",
            self.watch_raw_reversion_pressure_rate,
            self.block_raw_reversion_pressure_rate,
        )
        _require_ascending(
            "net_reversion_pressure_rate",
            self.watch_net_reversion_pressure_rate,
            self.block_net_reversion_pressure_rate,
        )
        _require_ascending(
            "fee_liquidity_drag_rate",
            self.watch_fee_liquidity_drag_rate,
            self.block_fee_liquidity_drag_rate,
        )
        _require_descending(
            "depth_coverage_ratio",
            self.watch_min_depth_coverage_ratio,
            self.block_min_depth_coverage_ratio,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityReversionPressureInput:
    private_research_reference: str
    observed_at: datetime
    anchor_probability: Decimal
    market_probability: Decimal
    taker_fee_rate: Decimal
    quoted_spread_rate: Decimal
    depth_coverage_ratio: Decimal
    slippage_buffer_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeLiquidityReversionPressureInput does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeLiquidityReversionPressureInput,
            "input",
        )
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("anchor_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_rate",
            "quoted_spread_rate",
            "depth_coverage_ratio",
            "slippage_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityReversionPressureReportRow:
    signal_digest: str
    rank: Decimal
    observed_at: datetime
    anchor_probability: Decimal
    market_probability: Decimal
    raw_reversion_pressure_rate: Decimal
    fee_cost_rate: Decimal
    spread_cost_rate: Decimal
    liquidity_shortfall_cost_rate: Decimal
    slippage_buffer_cost_rate: Decimal
    fee_liquidity_drag_rate: Decimal
    net_reversion_pressure_rate: Decimal
    depth_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeLiquidityReversionPressureReportRow does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeLiquidityReversionPressureReportRow,
            "row",
        )
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "rank", _positive_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("anchor_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "raw_reversion_pressure_rate",
            "fee_cost_rate",
            "spread_cost_rate",
            "liquidity_shortfall_cost_rate",
            "slippage_buffer_cost_rate",
            "fee_liquidity_drag_rate",
            "net_reversion_pressure_rate",
            "depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _set_or_verify_digest(self, "row")
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityReversionPressureReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeLiquidityReversionPressureReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeLiquidityReversionPressureReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityReversionPressureReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_raw_reversion_pressure_rate: Decimal | None
    average_net_reversion_pressure_rate: Decimal | None
    max_net_reversion_pressure_rate: Decimal
    max_fee_liquidity_drag_rate: Decimal
    min_depth_coverage_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeLiquidityReversionPressureReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeLiquidityReversionPressureReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeLiquidityReversionPressureReport does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeLiquidityReversionPressureReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_REVERSION_PRESSURE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_raw_reversion_pressure_rate",
            "average_net_reversion_pressure_rate",
            "min_depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_net_reversion_pressure_rate",
            "max_fee_liquidity_drag_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
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
        _require_hard_flags("report", self)
        if self.derived_validation_digest != "":
            _verify_digest(self, "report")
        _validate_report(self)
        if self.derived_validation_digest == "":
            _set_or_verify_digest(self, "report")
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> "FrozenJsonObject":
        return research_market_fee_liquidity_reversion_pressure_report_payload(self)


def build_research_market_fee_liquidity_reversion_pressure_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketFeeLiquidityReversionPressureConfig,
    generated_at: datetime,
) -> ResearchMarketFeeLiquidityReversionPressureReport:
    if type(config) is not ResearchMarketFeeLiquidityReversionPressureConfig:
        raise ValueError(
            "config must be a ResearchMarketFeeLiquidityReversionPressureConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(
        sorted(
            (_unranked_row(item, config=config) for item in normalized_inputs),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketFeeLiquidityReversionPressureReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(unranked_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketFeeLiquidityReversionPressureReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_raw_reversion_pressure_rate=_average(
            tuple(row.raw_reversion_pressure_rate for row in rows),
        ),
        average_net_reversion_pressure_rate=_average(
            tuple(row.net_reversion_pressure_rate for row in rows),
        ),
        max_net_reversion_pressure_rate=_maximum(
            tuple(row.net_reversion_pressure_rate for row in rows),
            ZERO,
        ),
        max_fee_liquidity_drag_rate=_maximum(
            tuple(row.fee_liquidity_drag_rate for row in rows),
            ZERO,
        ),
        min_depth_coverage_ratio=_minimum(
            tuple(row.depth_coverage_ratio for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_fee_liquidity_reversion_pressure_report_payload(
    report: ResearchMarketFeeLiquidityReversionPressureReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketFeeLiquidityReversionPressureReport:
        _require_hard_flags("report", report)
        _verify_digest(report, "report")
        payload = _json_ready(report)
    elif type(report) is dict:
        try:
            payload = _thaw_public_payload("payload", report)
        except (TypeError, ValueError) as exc:
            raise ValueError("report payload does not match public schema") from exc
    else:
        raise ValueError(
            "report must be a ResearchMarketFeeLiquidityReversionPressureReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _verify_payload_digest(payload)
    try:
        _report_from_public_payload(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("report payload does not match public schema") from exc
    return _freeze_json_object(payload)


def research_market_fee_liquidity_reversion_pressure_report_digest(
    report: ResearchMarketFeeLiquidityReversionPressureReport,
) -> str:
    if type(report) is not ResearchMarketFeeLiquidityReversionPressureReport:
        raise ValueError(
            "report must be a ResearchMarketFeeLiquidityReversionPressureReport",
        )
    _require_hard_flags("report", report)
    _verify_digest(report, "report")
    return report.derived_validation_digest


def validate_research_market_fee_liquidity_reversion_pressure_public_payload(
    payload: object,
) -> bool:
    try:
        ready = _thaw_public_payload("payload", payload)
        if type(ready) is not dict:
            return False
        _require_hard_flags("payload", _DictFlags(ready))
        _reject_unsafe_public_payload("payload", ready)
        _verify_payload_digest(ready)
        _report_from_public_payload(ready)
        return True
    except (TypeError, ValueError):
        return False


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


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: Mapping[str, Any]) -> None:
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


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchMarketFeeLiquidityReversionPressureReport:
    values = _exact_payload_object(
        "report payload",
        payload,
        ResearchMarketFeeLiquidityReversionPressureReport,
    )
    reason_code_counts_value = values["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in reason_code_counts_value
    )
    rows_value = values["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON array")
    rows = tuple(_row_from_public_payload(item) for item in rows_value)
    report = ResearchMarketFeeLiquidityReversionPressureReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            values["generated_at"],
        ),
        config_version=values["config_version"],
        input_count=_decimal_from_public_payload("input_count", values["input_count"]),
        pass_count=_decimal_from_public_payload("pass_count", values["pass_count"]),
        watch_count=_decimal_from_public_payload("watch_count", values["watch_count"]),
        block_count=_decimal_from_public_payload("block_count", values["block_count"]),
        average_raw_reversion_pressure_rate=_optional_decimal_from_public_payload(
            "average_raw_reversion_pressure_rate",
            values["average_raw_reversion_pressure_rate"],
        ),
        average_net_reversion_pressure_rate=_optional_decimal_from_public_payload(
            "average_net_reversion_pressure_rate",
            values["average_net_reversion_pressure_rate"],
        ),
        max_net_reversion_pressure_rate=_decimal_from_public_payload(
            "max_net_reversion_pressure_rate",
            values["max_net_reversion_pressure_rate"],
        ),
        max_fee_liquidity_drag_rate=_decimal_from_public_payload(
            "max_fee_liquidity_drag_rate",
            values["max_fee_liquidity_drag_rate"],
        ),
        min_depth_coverage_ratio=_optional_decimal_from_public_payload(
            "min_depth_coverage_ratio",
            values["min_depth_coverage_ratio"],
        ),
        status=values["status"],
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            values["reason_codes"],
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=values["derived_validation_digest"],
        paper_only=values["paper_only"],
        report_only=values["report_only"],
        readonly=values["readonly"],
    )
    if _json_ready(report) != payload:
        raise ValueError("report payload must use canonical public values")
    return report


def _row_from_public_payload(
    value: object,
) -> ResearchMarketFeeLiquidityReversionPressureReportRow:
    values = _exact_payload_object(
        "row payload",
        value,
        ResearchMarketFeeLiquidityReversionPressureReportRow,
    )
    return ResearchMarketFeeLiquidityReversionPressureReportRow(
        signal_digest=values["signal_digest"],
        rank=_decimal_from_public_payload("rank", values["rank"]),
        observed_at=_datetime_from_public_payload(
            "observed_at",
            values["observed_at"],
        ),
        anchor_probability=_decimal_from_public_payload(
            "anchor_probability",
            values["anchor_probability"],
        ),
        market_probability=_decimal_from_public_payload(
            "market_probability",
            values["market_probability"],
        ),
        raw_reversion_pressure_rate=_decimal_from_public_payload(
            "raw_reversion_pressure_rate",
            values["raw_reversion_pressure_rate"],
        ),
        fee_cost_rate=_decimal_from_public_payload(
            "fee_cost_rate",
            values["fee_cost_rate"],
        ),
        spread_cost_rate=_decimal_from_public_payload(
            "spread_cost_rate",
            values["spread_cost_rate"],
        ),
        liquidity_shortfall_cost_rate=_decimal_from_public_payload(
            "liquidity_shortfall_cost_rate",
            values["liquidity_shortfall_cost_rate"],
        ),
        slippage_buffer_cost_rate=_decimal_from_public_payload(
            "slippage_buffer_cost_rate",
            values["slippage_buffer_cost_rate"],
        ),
        fee_liquidity_drag_rate=_decimal_from_public_payload(
            "fee_liquidity_drag_rate",
            values["fee_liquidity_drag_rate"],
        ),
        net_reversion_pressure_rate=_decimal_from_public_payload(
            "net_reversion_pressure_rate",
            values["net_reversion_pressure_rate"],
        ),
        depth_coverage_ratio=_decimal_from_public_payload(
            "depth_coverage_ratio",
            values["depth_coverage_ratio"],
        ),
        status=values["status"],
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            values["reason_codes"],
        ),
        derived_validation_digest=values["derived_validation_digest"],
        paper_only=values["paper_only"],
        report_only=values["report_only"],
        readonly=values["readonly"],
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchMarketFeeLiquidityReversionPressureReasonCodeCount:
    values = _exact_payload_object(
        "reason code count payload",
        value,
        ResearchMarketFeeLiquidityReversionPressureReasonCodeCount,
    )
    return ResearchMarketFeeLiquidityReversionPressureReasonCodeCount(
        reason_code=values["reason_code"],
        count=_decimal_from_public_payload("count", values["count"]),
        row_ratio=_decimal_from_public_payload("row_ratio", values["row_ratio"]),
        paper_only=values["paper_only"],
        report_only=values["report_only"],
        readonly=values["readonly"],
    )


def _exact_payload_object(
    label: str,
    value: object,
    expected_type: type[object],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    expected_fields = tuple(field.name for field in fields(expected_type))
    if len(value) != len(expected_fields) or set(value) != set(expected_fields):
        raise ValueError(f"{label} must contain exactly the public schema fields")
    return value


def _reason_codes_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _decimal(field_name, decimal_value)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _optional_decimal_from_public_payload(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_public_payload(field_name, value)


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _thaw_public_payload(label: str, value: object) -> Any:
    if type(value) in (dict, FrozenJsonObject):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} object keys must be strings")
            ready[key] = _thaw_public_payload(f"{label}.{key}", item)
        return ready
    if type(value) in (list, FrozenJsonArray):
        return [
            _thaw_public_payload(f"{label}[{index}]", item)
            for index, item in enumerate(value)
        ]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"{label} must contain only canonical JSON values")


def _unranked_row(
    item: ResearchMarketFeeLiquidityReversionPressureInput,
    *,
    config: ResearchMarketFeeLiquidityReversionPressureConfig,
) -> dict[str, object]:
    raw_reversion_pressure_rate = _nonnegative_decimal(
        "raw_reversion_pressure_rate",
        abs(item.anchor_probability - item.market_probability),
    )
    fee_cost_rate = item.taker_fee_rate
    spread_cost_rate = _nonnegative_decimal(
        "spread_cost_rate",
        item.quoted_spread_rate / TWO,
    )
    liquidity_shortfall_cost_rate = _liquidity_shortfall_cost_rate(item, config)
    slippage_buffer_cost_rate = item.slippage_buffer_rate
    fee_liquidity_drag_rate = _nonnegative_decimal(
        "fee_liquidity_drag_rate",
        fee_cost_rate
        + spread_cost_rate
        + liquidity_shortfall_cost_rate
        + slippage_buffer_cost_rate,
    )
    net_reversion_pressure_rate = _nonnegative_decimal(
        "net_reversion_pressure_rate",
        max(ZERO, raw_reversion_pressure_rate - fee_liquidity_drag_rate),
    )
    status = _row_status(
        raw_reversion_pressure_rate=raw_reversion_pressure_rate,
        net_reversion_pressure_rate=net_reversion_pressure_rate,
        fee_liquidity_drag_rate=fee_liquidity_drag_rate,
        depth_coverage_ratio=item.depth_coverage_ratio,
        config=config,
    )
    return {
        "signal_digest": _private_reference_digest(item.private_research_reference),
        "observed_at": item.observed_at,
        "anchor_probability": item.anchor_probability,
        "market_probability": item.market_probability,
        "raw_reversion_pressure_rate": raw_reversion_pressure_rate,
        "fee_cost_rate": fee_cost_rate,
        "spread_cost_rate": spread_cost_rate,
        "liquidity_shortfall_cost_rate": liquidity_shortfall_cost_rate,
        "slippage_buffer_cost_rate": slippage_buffer_cost_rate,
        "fee_liquidity_drag_rate": fee_liquidity_drag_rate,
        "net_reversion_pressure_rate": net_reversion_pressure_rate,
        "depth_coverage_ratio": item.depth_coverage_ratio,
        "status": status,
        "reason_codes": _row_reason_codes(
            raw_reversion_pressure_rate=raw_reversion_pressure_rate,
            net_reversion_pressure_rate=net_reversion_pressure_rate,
            fee_liquidity_drag_rate=fee_liquidity_drag_rate,
            depth_coverage_ratio=item.depth_coverage_ratio,
            fee_cost_rate=fee_cost_rate,
            spread_cost_rate=spread_cost_rate,
            liquidity_shortfall_cost_rate=liquidity_shortfall_cost_rate,
            slippage_buffer_cost_rate=slippage_buffer_cost_rate,
            status=status,
            config=config,
        ),
    }


def _liquidity_shortfall_cost_rate(
    item: ResearchMarketFeeLiquidityReversionPressureInput,
    config: ResearchMarketFeeLiquidityReversionPressureConfig,
) -> Decimal:
    if item.depth_coverage_ratio >= config.watch_min_depth_coverage_ratio:
        return ZERO
    if config.watch_min_depth_coverage_ratio == ZERO:
        return ZERO
    shortfall_ratio = _nonnegative_decimal(
        "depth_shortfall_ratio",
        (config.watch_min_depth_coverage_ratio - item.depth_coverage_ratio)
        / config.watch_min_depth_coverage_ratio,
    )
    return _nonnegative_decimal(
        "liquidity_shortfall_cost_rate",
        shortfall_ratio * config.depth_shortfall_penalty_rate,
    )


def _row_status(
    *,
    raw_reversion_pressure_rate: Decimal,
    net_reversion_pressure_rate: Decimal,
    fee_liquidity_drag_rate: Decimal,
    depth_coverage_ratio: Decimal,
    config: ResearchMarketFeeLiquidityReversionPressureConfig,
) -> str:
    if (
        raw_reversion_pressure_rate >= config.block_raw_reversion_pressure_rate
        or net_reversion_pressure_rate >= config.block_net_reversion_pressure_rate
        or fee_liquidity_drag_rate >= config.block_fee_liquidity_drag_rate
        or depth_coverage_ratio <= config.block_min_depth_coverage_ratio
    ):
        return STATUS_BLOCK
    if (
        raw_reversion_pressure_rate >= config.watch_raw_reversion_pressure_rate
        or net_reversion_pressure_rate >= config.watch_net_reversion_pressure_rate
        or fee_liquidity_drag_rate >= config.watch_fee_liquidity_drag_rate
        or depth_coverage_ratio < config.watch_min_depth_coverage_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    raw_reversion_pressure_rate: Decimal,
    net_reversion_pressure_rate: Decimal,
    fee_liquidity_drag_rate: Decimal,
    depth_coverage_ratio: Decimal,
    fee_cost_rate: Decimal,
    spread_cost_rate: Decimal,
    liquidity_shortfall_cost_rate: Decimal,
    slippage_buffer_cost_rate: Decimal,
    status: str,
    config: ResearchMarketFeeLiquidityReversionPressureConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if status == STATUS_BLOCK:
        reasons.append(REASON_BLOCK)
    elif status == STATUS_WATCH:
        reasons.append(REASON_WATCH)
    else:
        reasons.append(REASON_PASS)
    if raw_reversion_pressure_rate >= config.block_raw_reversion_pressure_rate:
        reasons.append(REASON_RAW_BLOCK)
    elif raw_reversion_pressure_rate >= config.watch_raw_reversion_pressure_rate:
        reasons.append(REASON_RAW_WATCH)
    if net_reversion_pressure_rate >= config.block_net_reversion_pressure_rate:
        reasons.append(REASON_NET_BLOCK)
    elif net_reversion_pressure_rate >= config.watch_net_reversion_pressure_rate:
        reasons.append(REASON_NET_WATCH)
    if fee_liquidity_drag_rate >= config.block_fee_liquidity_drag_rate:
        reasons.append(REASON_DRAG_BLOCK)
    elif fee_liquidity_drag_rate >= config.watch_fee_liquidity_drag_rate:
        reasons.append(REASON_DRAG_WATCH)
    if depth_coverage_ratio <= config.block_min_depth_coverage_ratio:
        reasons.append(REASON_DEPTH_BLOCK)
    elif depth_coverage_ratio < config.watch_min_depth_coverage_ratio:
        reasons.append(REASON_DEPTH_WATCH)
    if fee_cost_rate > ZERO:
        reasons.append(REASON_FEE)
    if spread_cost_rate > ZERO:
        reasons.append(REASON_SPREAD)
    if liquidity_shortfall_cost_rate > ZERO:
        reasons.append(REASON_LIQUIDITY)
    if slippage_buffer_cost_rate > ZERO:
        reasons.append(REASON_SLIPPAGE)
    return tuple(reasons)


def _unranked_row_sort_key(row: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    status = row["status"]
    net_reversion_pressure_rate = row["net_reversion_pressure_rate"]
    signal_digest = row["signal_digest"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(net_reversion_pressure_rate) is not Decimal:
        raise ValueError("net_reversion_pressure_rate must be a Decimal")
    if type(signal_digest) is not str:
        raise ValueError("signal_digest must be a string")
    return (
        STATUS_SORT_RANK[status],
        -net_reversion_pressure_rate,
        signal_digest,
    )


def _report_status(
    rows: tuple[ResearchMarketFeeLiquidityReversionPressureReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeLiquidityReversionPressureReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketFeeLiquidityReversionPressureReportRow, ...],
) -> tuple[ResearchMarketFeeLiquidityReversionPressureReasonCodeCount, ...]:
    if reason_codes == (REASON_MISSING_INPUTS,):
        return (
            ResearchMarketFeeLiquidityReversionPressureReasonCodeCount(
                reason_code=REASON_MISSING_INPUTS,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(
        reason_code for row in rows for reason_code in set(row.reason_codes)
    )
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchMarketFeeLiquidityReversionPressureReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_ratio(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in reason_codes
    )


def _validate_row(row: ResearchMarketFeeLiquidityReversionPressureReportRow) -> None:
    if row.fee_liquidity_drag_rate != _nonnegative_decimal(
        "fee_liquidity_drag_rate",
        row.fee_cost_rate
        + row.spread_cost_rate
        + row.liquidity_shortfall_cost_rate
        + row.slippage_buffer_cost_rate,
    ):
        raise ValueError("fee_liquidity_drag_rate must match cost components")
    if row.net_reversion_pressure_rate != _nonnegative_decimal(
        "net_reversion_pressure_rate",
        max(ZERO, row.raw_reversion_pressure_rate - row.fee_liquidity_drag_rate),
    ):
        raise ValueError("net_reversion_pressure_rate must match raw pressure less drag")


def _validate_report(report: ResearchMarketFeeLiquidityReversionPressureReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_raw_reversion_pressure_rate != _average(
        tuple(row.raw_reversion_pressure_rate for row in rows),
    ):
        raise ValueError("average_raw_reversion_pressure_rate must match rows")
    if report.average_net_reversion_pressure_rate != _average(
        tuple(row.net_reversion_pressure_rate for row in rows),
    ):
        raise ValueError("average_net_reversion_pressure_rate must match rows")
    if report.max_net_reversion_pressure_rate != _maximum(
        tuple(row.net_reversion_pressure_rate for row in rows),
        ZERO,
    ):
        raise ValueError("max_net_reversion_pressure_rate must match rows")
    if report.max_fee_liquidity_drag_rate != _maximum(
        tuple(row.fee_liquidity_drag_rate for row in rows),
        ZERO,
    ):
        raise ValueError("max_fee_liquidity_drag_rate must match rows")
    if report.min_depth_coverage_ratio != _minimum(
        tuple(row.depth_coverage_ratio for row in rows),
    ):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match reason_codes")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")


def _row_sort_key(
    row: ResearchMarketFeeLiquidityReversionPressureReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.net_reversion_pressure_rate,
        row.signal_digest,
    )


def _normalize_inputs(inputs: Iterable[object]) -> tuple[
    ResearchMarketFeeLiquidityReversionPressureInput,
    ...,
]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen_digests: set[str] = set()
    for item in rows:
        if type(item) is not ResearchMarketFeeLiquidityReversionPressureInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeLiquidityReversionPressureInput "
                "values",
            )
        _require_hard_flags("input", item)
        signal_digest = _private_reference_digest(item.private_research_reference)
        if signal_digest in seen_digests:
            raise ValueError("inputs signal digests must be unique")
        seen_digests.add(signal_digest)
    return rows


def _normalize_rows(value: object) -> tuple[
    ResearchMarketFeeLiquidityReversionPressureReportRow,
    ...,
]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketFeeLiquidityReversionPressureReportRow:
            raise ValueError(
                "rows must contain ResearchMarketFeeLiquidityReversionPressureReportRow "
                "values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row, "row")
        if row.signal_digest in seen_digests:
            raise ValueError("rows signal digests must be unique")
        seen_digests.add(row.signal_digest)
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[
    ResearchMarketFeeLiquidityReversionPressureReasonCodeCount,
    ...,
]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchMarketFeeLiquidityReversionPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeLiquidityReversionPressureReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected_order = tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)
    if tuple(item.reason_code for item in counts) != expected_order:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return reason_codes


def _status_count(
    rows: tuple[ResearchMarketFeeLiquidityReversionPressureReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _nonnegative_decimal("average", sum(values, ZERO) / _decimal_count(len(values)))


def _maximum(values: tuple[Decimal, ...], default: Decimal) -> Decimal:
    if not values:
        return default
    return _nonnegative_decimal("maximum", max(values))


def _minimum(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _nonnegative_decimal("minimum", min(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _ratio_decimal("ratio", numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_decimal(field_name, value)


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ascending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"{field_name} watch threshold must not exceed block threshold")


def _require_descending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value < block_value:
        raise ValueError(f"{field_name} watch threshold must be at least block threshold")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or value == "":
        raise ValueError(f"{field_name} must be a nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in PHASE_FLAG_FIELDS:
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _set_or_verify_digest(value: object, label: str) -> None:
    current = getattr(value, "derived_validation_digest")
    expected = _dataclass_digest(value, label)
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        current = expected
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _verify_digest(value: object, label: str) -> None:
    current = getattr(value, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", current)
    if current != _dataclass_digest(value, label):
        raise ValueError("derived_validation_digest does not match report payload")


def _dataclass_digest(value: object, label: str) -> str:
    payload = _json_ready_without_digest(value)
    _reject_unsafe_public_payload(f"{label} digest payload", payload)
    return _payload_digest(payload)


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("digest value must be a dataclass")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", current)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    expected = _payload_digest(payload_without_digest)
    if current != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _payload_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


def _freeze_json_object(value: Mapping[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({str(key): _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    ready = _json_ready(value)
    _walk_public_payload(label, ready)


def _walk_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_text(f"{label}.{key}", str(key))
            _walk_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)
        return
    if type(value) in (bool,) or value is None:
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{label} contains unsafe public field")
