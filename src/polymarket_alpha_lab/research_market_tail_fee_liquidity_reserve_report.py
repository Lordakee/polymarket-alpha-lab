"""Report-only tail fee/liquidity reserve monitor."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_TAIL_FEE_LIQUIDITY_RESERVE_CONFIG_VERSION",
    "ResearchMarketTailFeeLiquidityReserveConfig",
    "ResearchMarketTailFeeLiquidityReserveInput",
    "ResearchMarketTailFeeLiquidityReserveReasonCodeCount",
    "ResearchMarketTailFeeLiquidityReserveReport",
    "ResearchMarketTailFeeLiquidityReserveReportRow",
    "build_research_market_tail_fee_liquidity_reserve_report",
    "research_market_tail_fee_liquidity_reserve_report_payload",
    "validate_research_market_tail_fee_liquidity_reserve_public_payload",
)


DEFAULT_RESEARCH_MARKET_TAIL_FEE_LIQUIDITY_RESERVE_CONFIG_VERSION = (
    "research-market-tail-fee-liquidity-reserve-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_tail_fee_liquidity_reserve_inputs"
REASON_PASS = "tail_fee_liquidity_reserve_pass"
REASON_WATCH = "tail_fee_liquidity_reserve_watch"
REASON_BLOCK = "tail_fee_liquidity_reserve_block"
REASON_REQUIRED_WATCH = "required_reserve_rate_watch"
REASON_REQUIRED_BLOCK = "required_reserve_rate_block"
REASON_COVERAGE_WATCH = "reserve_coverage_ratio_watch"
REASON_COVERAGE_BLOCK = "reserve_coverage_ratio_block"
REASON_TAIL = "tail_loss_component_applied"
REASON_FEE = "fee_reserve_applied"
REASON_LIQUIDITY = "liquidity_reserve_applied"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_BLOCK,
    REASON_WATCH,
    REASON_PASS,
    REASON_REQUIRED_BLOCK,
    REASON_REQUIRED_WATCH,
    REASON_COVERAGE_BLOCK,
    REASON_COVERAGE_WATCH,
    REASON_TAIL,
    REASON_FEE,
    REASON_LIQUIDITY,
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
    _join_parts("candi", "date", "_", "id"),
    _join_parts("creden", "tial"),
    _join_parts("d", "s", "n"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "sl", "ug"),
    _join_parts("pri", "vate"),
    _join_parts("raw", "_", "candi", "date"),
    _join_parts("raw", "_", "mar", "ket"),
    _join_parts("que", "stion"),
    _join_parts("sec", "ret"),
    _join_parts("source", "_", "te", "xt"),
    _join_parts("source", "_", "u", "r", "l"),
    _join_parts("table", "_", "na", "me"),
    _join_parts("to", "ken"),
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
class ResearchMarketTailFeeLiquidityReserveConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_TAIL_FEE_LIQUIDITY_RESERVE_CONFIG_VERSION
    watch_required_reserve_rate: Decimal = Decimal("0.050000")
    block_required_reserve_rate: Decimal = Decimal("0.120000")
    watch_min_reserve_coverage_ratio: Decimal = Decimal("1.500000")
    block_min_reserve_coverage_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketTailFeeLiquidityReserveConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketTailFeeLiquidityReserveConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_TAIL_FEE_LIQUIDITY_RESERVE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_required_reserve_rate",
            "block_required_reserve_rate",
            "watch_min_reserve_coverage_ratio",
            "block_min_reserve_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending(
            "required_reserve_rate",
            self.watch_required_reserve_rate,
            self.block_required_reserve_rate,
        )
        _require_descending(
            "reserve_coverage_ratio",
            self.watch_min_reserve_coverage_ratio,
            self.block_min_reserve_coverage_ratio,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketTailFeeLiquidityReserveInput:
    private_signal_reference: str
    observed_at: datetime
    tail_probability: Decimal
    tail_loss_rate: Decimal
    taker_fee_rate: Decimal
    liquidity_shortfall_rate: Decimal
    liquidity_haircut_rate: Decimal
    available_reserve_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketTailFeeLiquidityReserveInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketTailFeeLiquidityReserveInput, "input")
        _require_private_reference("private_signal_reference", self.private_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("tail_probability", "liquidity_haircut_rate"):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "tail_loss_rate",
            "taker_fee_rate",
            "liquidity_shortfall_rate",
            "available_reserve_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketTailFeeLiquidityReserveReportRow:
    signal_digest: str
    rank: Decimal
    observed_at: datetime
    tail_probability: Decimal
    tail_loss_rate: Decimal
    tail_loss_component_rate: Decimal
    fee_reserve_rate: Decimal
    liquidity_shortfall_rate: Decimal
    liquidity_haircut_rate: Decimal
    liquidity_reserve_rate: Decimal
    required_reserve_rate: Decimal
    available_reserve_rate: Decimal
    reserve_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketTailFeeLiquidityReserveReportRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketTailFeeLiquidityReserveReportRow, "row")
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "rank", _positive_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("tail_probability", "liquidity_haircut_rate"):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "tail_loss_rate",
            "tail_loss_component_rate",
            "fee_reserve_rate",
            "liquidity_shortfall_rate",
            "liquidity_reserve_rate",
            "required_reserve_rate",
            "available_reserve_rate",
            "reserve_coverage_ratio",
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
class ResearchMarketTailFeeLiquidityReserveReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketTailFeeLiquidityReserveReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketTailFeeLiquidityReserveReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketTailFeeLiquidityReserveReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_required_reserve_rate: Decimal | None
    max_required_reserve_rate: Decimal
    min_reserve_coverage_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketTailFeeLiquidityReserveReasonCodeCount, ...]
    rows: tuple[ResearchMarketTailFeeLiquidityReserveReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketTailFeeLiquidityReserveReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketTailFeeLiquidityReserveReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_TAIL_FEE_LIQUIDITY_RESERVE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_required_reserve_rate",
            _optional_nonnegative_decimal(
                "average_required_reserve_rate",
                self.average_required_reserve_rate,
            ),
        )
        object.__setattr__(
            self,
            "max_required_reserve_rate",
            _nonnegative_decimal("max_required_reserve_rate", self.max_required_reserve_rate),
        )
        object.__setattr__(
            self,
            "min_reserve_coverage_ratio",
            _optional_nonnegative_decimal(
                "min_reserve_coverage_ratio",
                self.min_reserve_coverage_ratio,
            ),
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
        return research_market_tail_fee_liquidity_reserve_report_payload(self)


def build_research_market_tail_fee_liquidity_reserve_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketTailFeeLiquidityReserveConfig,
    generated_at: datetime,
) -> ResearchMarketTailFeeLiquidityReserveReport:
    if type(config) is not ResearchMarketTailFeeLiquidityReserveConfig:
        raise ValueError("config must be a ResearchMarketTailFeeLiquidityReserveConfig")
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(
        sorted(
            (_unranked_row(item, config=config) for item in normalized_inputs),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketTailFeeLiquidityReserveReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(unranked_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketTailFeeLiquidityReserveReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_required_reserve_rate=_average(
            tuple(row.required_reserve_rate for row in rows),
        ),
        max_required_reserve_rate=_maximum(
            tuple(row.required_reserve_rate for row in rows),
            ZERO,
        ),
        min_reserve_coverage_ratio=_minimum(
            tuple(row.reserve_coverage_ratio for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_tail_fee_liquidity_reserve_report_payload(
    report: ResearchMarketTailFeeLiquidityReserveReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketTailFeeLiquidityReserveReport:
        _require_hard_flags("report", report)
        _verify_digest(report, "report")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketTailFeeLiquidityReserveReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_statuses(payload)
    _verify_payload_digest(payload)
    return _freeze_json_object(payload)


def validate_research_market_tail_fee_liquidity_reserve_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        research_market_tail_fee_liquidity_reserve_report_payload(payload)
    except ValueError:
        return False
    return True


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketTailFeeLiquidityReserveInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of reserve inputs")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketTailFeeLiquidityReserveInput:
            raise ValueError(
                "inputs must contain ResearchMarketTailFeeLiquidityReserveInput values",
            )
        _require_hard_flags("input", item)
        if item.private_signal_reference in seen:
            raise ValueError("inputs must be unique by private signal reference")
        seen.add(item.private_signal_reference)
    return normalized


def _unranked_row(
    item: ResearchMarketTailFeeLiquidityReserveInput,
    *,
    config: ResearchMarketTailFeeLiquidityReserveConfig,
) -> dict[str, object]:
    tail_loss_component_rate = _product(
        item.tail_probability,
        item.tail_loss_rate,
    )
    fee_reserve_rate = item.taker_fee_rate
    liquidity_reserve_rate = _product(
        item.liquidity_shortfall_rate,
        (ONE + item.liquidity_haircut_rate).quantize(QUANTUM),
    )
    required_reserve_rate = _sum_decimal(
        tail_loss_component_rate,
        fee_reserve_rate,
        liquidity_reserve_rate,
    )
    reserve_coverage_ratio = _coverage_ratio(
        item.available_reserve_rate,
        required_reserve_rate,
    )
    status = _row_status(
        required_reserve_rate=required_reserve_rate,
        reserve_coverage_ratio=reserve_coverage_ratio,
        config=config,
    )
    return {
        "signal_digest": _private_signal_digest(item.private_signal_reference),
        "observed_at": item.observed_at,
        "tail_probability": item.tail_probability,
        "tail_loss_rate": item.tail_loss_rate,
        "tail_loss_component_rate": tail_loss_component_rate,
        "fee_reserve_rate": fee_reserve_rate,
        "liquidity_shortfall_rate": item.liquidity_shortfall_rate,
        "liquidity_haircut_rate": item.liquidity_haircut_rate,
        "liquidity_reserve_rate": liquidity_reserve_rate,
        "required_reserve_rate": required_reserve_rate,
        "available_reserve_rate": item.available_reserve_rate,
        "reserve_coverage_ratio": reserve_coverage_ratio,
        "status": status,
        "reason_codes": _row_reason_codes(
            status=status,
            tail_loss_component_rate=tail_loss_component_rate,
            fee_reserve_rate=fee_reserve_rate,
            liquidity_reserve_rate=liquidity_reserve_rate,
            required_reserve_rate=required_reserve_rate,
            reserve_coverage_ratio=reserve_coverage_ratio,
            config=config,
        ),
    }


def _row_status(
    *,
    required_reserve_rate: Decimal,
    reserve_coverage_ratio: Decimal,
    config: ResearchMarketTailFeeLiquidityReserveConfig,
) -> str:
    if (
        required_reserve_rate >= config.block_required_reserve_rate
        or reserve_coverage_ratio <= config.block_min_reserve_coverage_ratio
    ):
        return STATUS_BLOCK
    if (
        required_reserve_rate >= config.watch_required_reserve_rate
        or reserve_coverage_ratio <= config.watch_min_reserve_coverage_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    tail_loss_component_rate: Decimal,
    fee_reserve_rate: Decimal,
    liquidity_reserve_rate: Decimal,
    required_reserve_rate: Decimal,
    reserve_coverage_ratio: Decimal,
    config: ResearchMarketTailFeeLiquidityReserveConfig,
) -> tuple[str, ...]:
    reasons = {f"tail_fee_liquidity_reserve_{status}"}
    if required_reserve_rate >= config.block_required_reserve_rate:
        reasons.add(REASON_REQUIRED_BLOCK)
    elif required_reserve_rate >= config.watch_required_reserve_rate:
        reasons.add(REASON_REQUIRED_WATCH)
    if reserve_coverage_ratio <= config.block_min_reserve_coverage_ratio:
        reasons.add(REASON_COVERAGE_BLOCK)
    elif reserve_coverage_ratio <= config.watch_min_reserve_coverage_ratio:
        reasons.add(REASON_COVERAGE_WATCH)
    if tail_loss_component_rate > ZERO:
        reasons.add(REASON_TAIL)
    if fee_reserve_rate > ZERO:
        reasons.add(REASON_FEE)
    if liquidity_reserve_rate > ZERO:
        reasons.add(REASON_LIQUIDITY)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _unranked_row_sort_key(row: dict[str, object]) -> tuple[Decimal, Decimal, Decimal, str]:
    status = row["status"]
    required_reserve_rate = row["required_reserve_rate"]
    reserve_coverage_ratio = row["reserve_coverage_ratio"]
    signal_digest = row["signal_digest"]
    if type(status) is not str or status not in STATUS_SORT_RANK:
        raise ValueError("status must be pass, watch, or block")
    if type(required_reserve_rate) is not Decimal:
        raise ValueError("required_reserve_rate must be a Decimal")
    if type(reserve_coverage_ratio) is not Decimal:
        raise ValueError("reserve_coverage_ratio must be a Decimal")
    if type(signal_digest) is not str:
        raise ValueError("signal_digest must be a string")
    return (
        STATUS_SORT_RANK[status],
        -required_reserve_rate,
        reserve_coverage_ratio,
        signal_digest,
    )


def _report_status(
    rows: tuple[ResearchMarketTailFeeLiquidityReserveReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketTailFeeLiquidityReserveReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketTailFeeLiquidityReserveReportRow, ...],
) -> tuple[ResearchMarketTailFeeLiquidityReserveReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketTailFeeLiquidityReserveReasonCodeCount(
                reason_code=REASON_MISSING_INPUTS,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketTailFeeLiquidityReserveReasonCodeCount(
            reason_code=reason,
            count=_decimal_count(counts[reason]),
            row_ratio=_ratio(_decimal_count(counts[reason]), row_count),
        )
        for reason in reason_codes
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketTailFeeLiquidityReserveReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    previous_key: tuple[Decimal, Decimal, Decimal, str] | None = None
    for index, row in enumerate(rows, start=1):
        if type(row) is not ResearchMarketTailFeeLiquidityReserveReportRow:
            raise ValueError(
                "rows must contain ResearchMarketTailFeeLiquidityReserveReportRow values",
            )
        _require_hard_flags("row", row)
        if row.rank != _decimal_count(index):
            raise ValueError("row ranks must follow deterministic sequence")
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchMarketTailFeeLiquidityReserveReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_index = -1
    for count in counts:
        if type(count) is not ResearchMarketTailFeeLiquidityReserveReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketTailFeeLiquidityReserveReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
        index = REASON_CODES.index(count.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must follow deterministic sequence")
        previous_index = index
    return counts


def _row_sort_key(
    row: ResearchMarketTailFeeLiquidityReserveReportRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.required_reserve_rate,
        row.reserve_coverage_ratio,
        row.signal_digest,
    )


def _validate_row(row: ResearchMarketTailFeeLiquidityReserveReportRow) -> None:
    if row.tail_loss_component_rate != _product(row.tail_probability, row.tail_loss_rate):
        raise ValueError("tail_loss_component_rate must match inputs")
    expected_liquidity_reserve_rate = _product(
        row.liquidity_shortfall_rate,
        (ONE + row.liquidity_haircut_rate).quantize(QUANTUM),
    )
    if row.liquidity_reserve_rate != expected_liquidity_reserve_rate:
        raise ValueError("liquidity_reserve_rate must match inputs")
    expected_required = _sum_decimal(
        row.tail_loss_component_rate,
        row.fee_reserve_rate,
        row.liquidity_reserve_rate,
    )
    if row.required_reserve_rate != expected_required:
        raise ValueError("required_reserve_rate must match components")
    if row.reserve_coverage_ratio != _coverage_ratio(
        row.available_reserve_rate,
        row.required_reserve_rate,
    ):
        raise ValueError("reserve_coverage_ratio must match available reserve")
    if f"tail_fee_liquidity_reserve_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketTailFeeLiquidityReserveReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_required_reserve_rate != _average(
        tuple(row.required_reserve_rate for row in report.rows),
    ):
        raise ValueError("average_required_reserve_rate must match rows")
    if report.max_required_reserve_rate != _maximum(
        tuple(row.required_reserve_rate for row in report.rows),
        ZERO,
    ):
        raise ValueError("max_required_reserve_rate must match rows")
    if report.min_reserve_coverage_ratio != _minimum(
        tuple(row.reserve_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_reserve_coverage_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchMarketTailFeeLiquidityReserveReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(row.status == status for row in rows))


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _ratio(sum(values, ZERO), _decimal_count(len(values)))


def _maximum(values: tuple[Decimal, ...], default: Decimal) -> Decimal:
    if not values:
        return default
    return max(values).quantize(QUANTUM)


def _minimum(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return min(values).quantize(QUANTUM)


def _product(left: Decimal, right: Decimal) -> Decimal:
    left_value = _nonnegative_decimal("left", left)
    right_value = _nonnegative_decimal("right", right)
    with localcontext(DECIMAL_CONTEXT):
        return (left_value * right_value).quantize(QUANTUM)


def _sum_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum((_nonnegative_decimal("value", value) for value in values), ZERO).quantize(
            QUANTUM,
        )


def _coverage_ratio(available_reserve_rate: Decimal, required_reserve_rate: Decimal) -> Decimal:
    if required_reserve_rate == ZERO:
        return ONE
    return _ratio(available_reserve_rate, required_reserve_rate)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_decimal(field_name, value)


def _ratio_decimal(field_name: str, value: object) -> Decimal:
    ratio = _nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_ascending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value < watch_value:
        raise ValueError(f"{field_name} block threshold must not be below watch threshold")


def _require_descending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value > watch_value:
        raise ValueError(f"{field_name} block threshold must not exceed watch threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or PUBLIC_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a deterministic public identifier")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        index = REASON_CODES.index(reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if index <= previous_index:
            raise ValueError(f"{field_name} must follow deterministic sequence")
        seen.add(reason_code)
        previous_index = index
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _private_signal_digest(value: str) -> str:
    _require_private_reference("private_signal_reference", value)
    return sha256(value.encode("utf-8")).hexdigest()


def _set_or_verify_digest(value: object, label: str) -> None:
    digest = _field_value(value, "derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest_for_value(value)
    if digest == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if digest != expected:
        raise ValueError(f"{label} derived_validation_digest does not match public payload")


def _verify_digest(value: object, label: str) -> None:
    digest = _field_value(value, "derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest_for_value(value)
    if digest != expected:
        raise ValueError(f"{label} derived_validation_digest does not match public payload")


def _digest_for_value(value: object) -> str:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_payload_digest(value: object) -> None:
    if isinstance(value, dict):
        if "derived_validation_digest" in value:
            digest = value["derived_validation_digest"]
            if type(digest) is not str:
                raise ValueError("derived_validation_digest must be a string")
            comparable = dict(value)
            comparable.pop("derived_validation_digest", None)
            if digest != _canonical_digest(comparable):
                raise ValueError("derived_validation_digest does not match public payload")
        for item in value.values():
            _verify_payload_digest(item)
    elif isinstance(value, list):
        for item in value:
            _verify_payload_digest(item)


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        if "status" in value and value["status"] not in STATUSES:
            raise ValueError("status must be pass, watch, or block")
        for item in value.values():
            _validate_payload_statuses(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public value")


class _DictFlags:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

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


class FrozenJsonArray(list[Any]):
    def __setitem__(self, key: int | slice, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: int | slice) -> None:
        raise TypeError("payload is immutable")

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Iterable[Any]) -> None:
        raise TypeError("payload is immutable")

    def insert(self, index: int, value: Any) -> None:
        raise TypeError("payload is immutable")

    def pop(self, index: int = -1) -> Any:
        raise TypeError("payload is immutable")

    def remove(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def reverse(self) -> None:
        raise TypeError("payload is immutable")

    def sort(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_array(value: list[Any]) -> FrozenJsonArray:
    return FrozenJsonArray(_freeze_json_value(item) for item in value)


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return _freeze_json_array(value)
    return value
