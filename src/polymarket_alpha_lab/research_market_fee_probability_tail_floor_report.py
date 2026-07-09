"""Report-only fee-adjusted probability tail-floor monitor."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_TAIL_FLOOR_CONFIG_VERSION",
    "ResearchMarketFeeProbabilityTailFloorConfig",
    "ResearchMarketFeeProbabilityTailFloorInput",
    "ResearchMarketFeeProbabilityTailFloorReasonCodeCount",
    "ResearchMarketFeeProbabilityTailFloorReport",
    "ResearchMarketFeeProbabilityTailFloorReportRow",
    "build_research_market_fee_probability_tail_floor_report",
    "research_market_fee_probability_tail_floor_report_digest",
    "research_market_fee_probability_tail_floor_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_TAIL_FLOOR_CONFIG_VERSION = (
    "research-market-fee-probability-tail-floor-report-v1"
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

REASON_MISSING_INPUTS = "missing_fee_probability_tail_floor_inputs"
REASON_PASS = "fee_probability_tail_floor_pass"
REASON_WATCH = "fee_probability_tail_floor_watch"
REASON_BLOCK = "fee_probability_tail_floor_block"
REASON_TAIL_WATCH = "probability_tail_floor_watch"
REASON_TAIL_BLOCK = "probability_tail_floor_block"
REASON_ADJUSTED_WATCH = "fee_adjusted_tail_floor_watch"
REASON_ADJUSTED_BLOCK = "fee_adjusted_tail_floor_block"
REASON_DRAG_WATCH = "fee_probability_drag_watch"
REASON_DRAG_BLOCK = "fee_probability_drag_block"
REASON_FEE = "fee_drag_applied"
REASON_SPREAD = "spread_drag_applied"
REASON_SLIPPAGE = "slippage_buffer_applied"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_BLOCK,
    REASON_WATCH,
    REASON_PASS,
    REASON_TAIL_BLOCK,
    REASON_TAIL_WATCH,
    REASON_ADJUSTED_BLOCK,
    REASON_ADJUSTED_WATCH,
    REASON_DRAG_BLOCK,
    REASON_DRAG_WATCH,
    REASON_FEE,
    REASON_SPREAD,
    REASON_SLIPPAGE,
)
REASON_CODE_SET = frozenset(REASON_CODES)

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "=",
    _join_parts("api", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("candidate", "_", "id"),
    _join_parts("credential"),
    _join_parts("d", "s", "n"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("private", "_", "key"),
    _join_parts("private", "_", "research", "_", "reference"),
    _join_parts("question"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "market"),
    _join_parts("secret"),
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
class ResearchMarketFeeProbabilityTailFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_TAIL_FLOOR_CONFIG_VERSION
    )
    watch_tail_distance_floor: Decimal = Decimal("0.050000")
    block_tail_distance_floor: Decimal = Decimal("0.010000")
    watch_fee_adjusted_tail_floor: Decimal = Decimal("0.025000")
    block_fee_adjusted_tail_floor: Decimal = Decimal("0.005000")
    watch_fee_probability_drag_rate: Decimal = Decimal("0.020000")
    block_fee_probability_drag_rate: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeProbabilityTailFloorConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityTailFloorConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_TAIL_FLOOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_tail_distance_floor",
            "block_tail_distance_floor",
            "watch_fee_adjusted_tail_floor",
            "block_fee_adjusted_tail_floor",
            "watch_fee_probability_drag_rate",
            "block_fee_probability_drag_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_descending_floor(
            "tail_distance_floor",
            self.watch_tail_distance_floor,
            self.block_tail_distance_floor,
        )
        _require_descending_floor(
            "fee_adjusted_tail_floor",
            self.watch_fee_adjusted_tail_floor,
            self.block_fee_adjusted_tail_floor,
        )
        _require_ascending_threshold(
            "fee_probability_drag_rate",
            self.watch_fee_probability_drag_rate,
            self.block_fee_probability_drag_rate,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityTailFloorInput:
    private_research_reference: str
    observed_at: datetime
    market_probability: Decimal
    taker_fee_rate: Decimal
    quoted_spread_rate: Decimal
    slippage_buffer_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeProbabilityTailFloorInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityTailFloorInput, "input")
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "market_probability",
            _probability_decimal("market_probability", self.market_probability),
        )
        for field_name in (
            "taker_fee_rate",
            "quoted_spread_rate",
            "slippage_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityTailFloorReportRow:
    signal_digest: str
    rank: Decimal
    observed_at: datetime
    market_probability: Decimal
    probability_tail_distance: Decimal
    fee_cost_rate: Decimal
    spread_cost_rate: Decimal
    slippage_buffer_cost_rate: Decimal
    fee_probability_drag_rate: Decimal
    fee_adjusted_tail_floor: Decimal
    tail_floor_gap_rate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeProbabilityTailFloorReportRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityTailFloorReportRow, "row")
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "rank", _positive_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "market_probability",
            _probability_decimal("market_probability", self.market_probability),
        )
        for field_name in (
            "probability_tail_distance",
            "fee_cost_rate",
            "spread_cost_rate",
            "slippage_buffer_cost_rate",
            "fee_probability_drag_rate",
            "fee_adjusted_tail_floor",
            "tail_floor_gap_rate",
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
class ResearchMarketFeeProbabilityTailFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeProbabilityTailFloorReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeProbabilityTailFloorReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityTailFloorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_tail_distance: Decimal | None
    average_fee_adjusted_tail_floor: Decimal | None
    min_fee_adjusted_tail_floor: Decimal | None
    max_fee_probability_drag_rate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeProbabilityTailFloorReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeProbabilityTailFloorReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeProbabilityTailFloorReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityTailFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_TAIL_FLOOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_probability_tail_distance",
            "average_fee_adjusted_tail_floor",
            "min_fee_adjusted_tail_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_fee_probability_drag_rate",
            _nonnegative_decimal(
                "max_fee_probability_drag_rate",
                self.max_fee_probability_drag_rate,
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
        return research_market_fee_probability_tail_floor_report_payload(self)


def build_research_market_fee_probability_tail_floor_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketFeeProbabilityTailFloorConfig,
    generated_at: datetime,
) -> ResearchMarketFeeProbabilityTailFloorReport:
    if type(config) is not ResearchMarketFeeProbabilityTailFloorConfig:
        raise ValueError("config must be a ResearchMarketFeeProbabilityTailFloorConfig")
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(
        sorted(
            (_unranked_row(item, config=config) for item in normalized_inputs),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketFeeProbabilityTailFloorReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(unranked_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketFeeProbabilityTailFloorReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_probability_tail_distance=_average(
            tuple(row.probability_tail_distance for row in rows),
        ),
        average_fee_adjusted_tail_floor=_average(
            tuple(row.fee_adjusted_tail_floor for row in rows),
        ),
        min_fee_adjusted_tail_floor=_minimum(
            tuple(row.fee_adjusted_tail_floor for row in rows),
        ),
        max_fee_probability_drag_rate=_maximum(
            tuple(row.fee_probability_drag_rate for row in rows),
            ZERO,
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_fee_probability_tail_floor_report_payload(
    report: ResearchMarketFeeProbabilityTailFloorReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketFeeProbabilityTailFloorReport:
        _require_hard_flags("report", report)
        _verify_digest(report, "report")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketFeeProbabilityTailFloorReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _require_public_payload_hard_flags("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    _verify_payload_digest(payload)
    return _freeze_json_object(payload)


def research_market_fee_probability_tail_floor_report_digest(
    report: ResearchMarketFeeProbabilityTailFloorReport,
) -> str:
    if type(report) is not ResearchMarketFeeProbabilityTailFloorReport:
        raise ValueError("report must be a ResearchMarketFeeProbabilityTailFloorReport")
    _require_hard_flags("report", report)
    _verify_digest(report, "report")
    return report.derived_validation_digest


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


def _unranked_row(
    item: ResearchMarketFeeProbabilityTailFloorInput,
    *,
    config: ResearchMarketFeeProbabilityTailFloorConfig,
) -> dict[str, object]:
    probability_tail_distance = _probability_tail_distance(item.market_probability)
    fee_cost_rate = item.taker_fee_rate
    spread_cost_rate = _nonnegative_decimal(
        "spread_cost_rate",
        item.quoted_spread_rate / TWO,
    )
    slippage_buffer_cost_rate = item.slippage_buffer_rate
    fee_probability_drag_rate = _nonnegative_decimal(
        "fee_probability_drag_rate",
        fee_cost_rate + spread_cost_rate + slippage_buffer_cost_rate,
    )
    fee_adjusted_tail_floor = _nonnegative_decimal(
        "fee_adjusted_tail_floor",
        max(ZERO, probability_tail_distance - fee_probability_drag_rate),
    )
    tail_floor_gap_rate = _nonnegative_decimal(
        "tail_floor_gap_rate",
        max(ZERO, config.watch_tail_distance_floor - probability_tail_distance),
    )
    status = _row_status(
        probability_tail_distance=probability_tail_distance,
        fee_probability_drag_rate=fee_probability_drag_rate,
        fee_adjusted_tail_floor=fee_adjusted_tail_floor,
        config=config,
    )
    return {
        "signal_digest": _private_reference_digest(item.private_research_reference),
        "observed_at": item.observed_at,
        "market_probability": item.market_probability,
        "probability_tail_distance": probability_tail_distance,
        "fee_cost_rate": fee_cost_rate,
        "spread_cost_rate": spread_cost_rate,
        "slippage_buffer_cost_rate": slippage_buffer_cost_rate,
        "fee_probability_drag_rate": fee_probability_drag_rate,
        "fee_adjusted_tail_floor": fee_adjusted_tail_floor,
        "tail_floor_gap_rate": tail_floor_gap_rate,
        "status": status,
        "reason_codes": _row_reason_codes(
            probability_tail_distance=probability_tail_distance,
            fee_probability_drag_rate=fee_probability_drag_rate,
            fee_adjusted_tail_floor=fee_adjusted_tail_floor,
            fee_cost_rate=fee_cost_rate,
            spread_cost_rate=spread_cost_rate,
            slippage_buffer_cost_rate=slippage_buffer_cost_rate,
            status=status,
            config=config,
        ),
    }


def _probability_tail_distance(value: Decimal) -> Decimal:
    return _nonnegative_decimal("probability_tail_distance", min(value, ONE - value))


def _row_status(
    *,
    probability_tail_distance: Decimal,
    fee_probability_drag_rate: Decimal,
    fee_adjusted_tail_floor: Decimal,
    config: ResearchMarketFeeProbabilityTailFloorConfig,
) -> str:
    if (
        probability_tail_distance <= config.block_tail_distance_floor
        or fee_adjusted_tail_floor <= config.block_fee_adjusted_tail_floor
        or fee_probability_drag_rate >= config.block_fee_probability_drag_rate
    ):
        return STATUS_BLOCK
    if (
        probability_tail_distance <= config.watch_tail_distance_floor
        or fee_adjusted_tail_floor <= config.watch_fee_adjusted_tail_floor
        or fee_probability_drag_rate >= config.watch_fee_probability_drag_rate
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    probability_tail_distance: Decimal,
    fee_probability_drag_rate: Decimal,
    fee_adjusted_tail_floor: Decimal,
    fee_cost_rate: Decimal,
    spread_cost_rate: Decimal,
    slippage_buffer_cost_rate: Decimal,
    status: str,
    config: ResearchMarketFeeProbabilityTailFloorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if status == STATUS_BLOCK:
        reasons.append(REASON_BLOCK)
    elif status == STATUS_WATCH:
        reasons.append(REASON_WATCH)
    else:
        reasons.append(REASON_PASS)
    if probability_tail_distance <= config.block_tail_distance_floor:
        reasons.append(REASON_TAIL_BLOCK)
    elif probability_tail_distance <= config.watch_tail_distance_floor:
        reasons.append(REASON_TAIL_WATCH)
    if fee_adjusted_tail_floor <= config.block_fee_adjusted_tail_floor:
        reasons.append(REASON_ADJUSTED_BLOCK)
    elif fee_adjusted_tail_floor <= config.watch_fee_adjusted_tail_floor:
        reasons.append(REASON_ADJUSTED_WATCH)
    if fee_probability_drag_rate >= config.block_fee_probability_drag_rate:
        reasons.append(REASON_DRAG_BLOCK)
    elif fee_probability_drag_rate >= config.watch_fee_probability_drag_rate:
        reasons.append(REASON_DRAG_WATCH)
    if fee_cost_rate > ZERO:
        reasons.append(REASON_FEE)
    if spread_cost_rate > ZERO:
        reasons.append(REASON_SPREAD)
    if slippage_buffer_cost_rate > ZERO:
        reasons.append(REASON_SLIPPAGE)
    return tuple(reasons)


def _unranked_row_sort_key(row: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    status = row["status"]
    probability_tail_distance = row["probability_tail_distance"]
    fee_probability_drag_rate = row["fee_probability_drag_rate"]
    signal_digest = row["signal_digest"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(probability_tail_distance) is not Decimal:
        raise ValueError("probability_tail_distance must be a Decimal")
    if type(fee_probability_drag_rate) is not Decimal:
        raise ValueError("fee_probability_drag_rate must be a Decimal")
    if type(signal_digest) is not str:
        raise ValueError("signal_digest must be a string")
    return (
        STATUS_SORT_RANK[status],
        probability_tail_distance,
        -fee_probability_drag_rate,
        signal_digest,
    )


def _row_sort_key(
    row: ResearchMarketFeeProbabilityTailFloorReportRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        row.probability_tail_distance,
        -row.fee_probability_drag_rate,
        row.signal_digest,
    )


def _report_status(
    rows: tuple[ResearchMarketFeeProbabilityTailFloorReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeProbabilityTailFloorReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketFeeProbabilityTailFloorReportRow, ...],
) -> tuple[ResearchMarketFeeProbabilityTailFloorReasonCodeCount, ...]:
    if reason_codes == (REASON_MISSING_INPUTS,):
        return (
            ResearchMarketFeeProbabilityTailFloorReasonCodeCount(
                reason_code=REASON_MISSING_INPUTS,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in set(row.reason_codes))
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchMarketFeeProbabilityTailFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_ratio(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in reason_codes
    )


def _validate_row(row: ResearchMarketFeeProbabilityTailFloorReportRow) -> None:
    if row.probability_tail_distance != _probability_tail_distance(row.market_probability):
        raise ValueError("probability_tail_distance must match market_probability")
    if row.fee_probability_drag_rate != _nonnegative_decimal(
        "fee_probability_drag_rate",
        row.fee_cost_rate + row.spread_cost_rate + row.slippage_buffer_cost_rate,
    ):
        raise ValueError("fee_probability_drag_rate must match cost components")
    if row.fee_adjusted_tail_floor != _nonnegative_decimal(
        "fee_adjusted_tail_floor",
        max(ZERO, row.probability_tail_distance - row.fee_probability_drag_rate),
    ):
        raise ValueError(
            "fee_adjusted_tail_floor must match tail distance less fee drag",
        )
    expected_status_reason = f"fee_probability_tail_floor_{row.status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include status")


def _validate_report(report: ResearchMarketFeeProbabilityTailFloorReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_probability_tail_distance != _average(
        tuple(row.probability_tail_distance for row in rows),
    ):
        raise ValueError("average_probability_tail_distance must match rows")
    if report.average_fee_adjusted_tail_floor != _average(
        tuple(row.fee_adjusted_tail_floor for row in rows),
    ):
        raise ValueError("average_fee_adjusted_tail_floor must match rows")
    if report.min_fee_adjusted_tail_floor != _minimum(
        tuple(row.fee_adjusted_tail_floor for row in rows),
    ):
        raise ValueError("min_fee_adjusted_tail_floor must match rows")
    if report.max_fee_probability_drag_rate != _maximum(
        tuple(row.fee_probability_drag_rate for row in rows),
        ZERO,
    ):
        raise ValueError("max_fee_probability_drag_rate must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match reason_codes")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketFeeProbabilityTailFloorInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen_digests: set[str] = set()
    for item in rows:
        if type(item) is not ResearchMarketFeeProbabilityTailFloorInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeProbabilityTailFloorInput values",
            )
        _require_hard_flags("input", item)
        signal_digest = _private_reference_digest(item.private_research_reference)
        if signal_digest in seen_digests:
            raise ValueError("inputs signal digests must be unique")
        seen_digests.add(signal_digest)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketFeeProbabilityTailFloorReportRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketFeeProbabilityTailFloorReportRow:
            raise ValueError(
                "rows must contain ResearchMarketFeeProbabilityTailFloorReportRow "
                "values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row, "row")
        if row.signal_digest in seen_digests:
            raise ValueError("rows signal digests must be unique")
        seen_digests.add(row.signal_digest)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketFeeProbabilityTailFloorReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchMarketFeeProbabilityTailFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeProbabilityTailFloorReasonCodeCount values",
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
    rows: tuple[ResearchMarketFeeProbabilityTailFloorReportRow, ...],
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
            return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_descending_floor(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if watch_value < block_value:
        raise ValueError(f"{field_name} watch floor must be at least block floor")


def _require_ascending_threshold(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{field_name} watch threshold must not exceed block threshold")


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


def _require_public_payload_hard_flags(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        has_phase_flag = any(flag in value for flag in PHASE_FLAG_FIELDS)
        if has_phase_flag:
            for flag in PHASE_FLAG_FIELDS:
                if value.get(flag) is not True:
                    raise ValueError(f"{label} {flag} must be True")
        for key, item in value.items():
            _require_public_payload_hard_flags(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_hard_flags(f"{label}[{index}]", item)


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
        raise ValueError("derived_validation_digest does not match public payload")


def _verify_digest(value: object, label: str) -> None:
    current = getattr(value, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", current)
    if current != _dataclass_digest(value, label):
        raise ValueError("derived_validation_digest does not match public payload")


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
        raise ValueError("derived_validation_digest does not match public payload")


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
