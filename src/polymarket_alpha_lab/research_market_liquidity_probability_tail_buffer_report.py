"""Report-only liquidity probability tail-buffer monitor."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_TAIL_BUFFER_CONFIG_VERSION",
    "REASON_CODES",
    "STATUSES",
    "ResearchMarketLiquidityProbabilityTailBufferInput",
    "ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount",
    "ResearchMarketLiquidityProbabilityTailBufferReport",
    "ResearchMarketLiquidityProbabilityTailBufferReportConfig",
    "ResearchMarketLiquidityProbabilityTailBufferReportRow",
    "build_research_market_liquidity_probability_tail_buffer_report",
    "research_market_liquidity_probability_tail_buffer_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_TAIL_BUFFER_CONFIG_VERSION = (
    "research-market-liquidity-probability-tail-buffer-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
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

REASON_MISSING_INPUTS = "missing_liquidity_probability_tail_buffer_inputs"
REASON_PASS = "liquidity_probability_tail_buffer_pass"
REASON_WATCH = "liquidity_probability_tail_buffer_watch"
REASON_BLOCK = "liquidity_probability_tail_buffer_block"
REASON_TAIL_WATCH = "tail_pressure_watch"
REASON_TAIL_BLOCK = "tail_pressure_block"
REASON_BUFFER_WATCH = "buffer_shortfall_watch"
REASON_BUFFER_BLOCK = "buffer_shortfall_block"
REASON_STRESS_WATCH = "stress_probability_watch"
REASON_STRESS_BLOCK = "stress_probability_block"
REASON_DEPTH_WATCH = "depth_support_watch"
REASON_DEPTH_BLOCK = "depth_support_block"
REASON_GAP = "probability_gap_observed"
REASON_SPREAD = "spread_cost_applied"
REASON_SLIPPAGE = "slippage_buffer_applied"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_BLOCK,
    REASON_WATCH,
    REASON_PASS,
    REASON_TAIL_BLOCK,
    REASON_TAIL_WATCH,
    REASON_BUFFER_BLOCK,
    REASON_BUFFER_WATCH,
    REASON_STRESS_BLOCK,
    REASON_STRESS_WATCH,
    REASON_DEPTH_BLOCK,
    REASON_DEPTH_WATCH,
    REASON_GAP,
    REASON_SPREAD,
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
    _join_parts("reco", "mmendation"),
    _join_parts("siz", "ing"),
    _join_parts("b", "u", "y"),
    _join_parts("s", "e", "l", "l"),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityTailBufferReportConfig(
    _FinalPublicDataclass,
):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_TAIL_BUFFER_CONFIG_VERSION
    )
    watch_tail_pressure_probability: Decimal = Decimal("0.080000")
    block_tail_pressure_probability: Decimal = Decimal("0.180000")
    watch_buffer_shortfall_probability: Decimal = Decimal("0.030000")
    block_buffer_shortfall_probability: Decimal = Decimal("0.080000")
    watch_stress_probability: Decimal = Decimal("0.120000")
    block_stress_probability: Decimal = Decimal("0.300000")
    watch_min_depth_support_score: Decimal = Decimal("0.650000")
    block_min_depth_support_score: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityTailBufferReportConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_TAIL_BUFFER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_tail_pressure_probability",
            "block_tail_pressure_probability",
            "watch_buffer_shortfall_probability",
            "block_buffer_shortfall_probability",
            "watch_stress_probability",
            "block_stress_probability",
            "watch_min_depth_support_score",
            "block_min_depth_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending(
            "tail_pressure_probability",
            self.watch_tail_pressure_probability,
            self.block_tail_pressure_probability,
        )
        _require_ascending(
            "buffer_shortfall_probability",
            self.watch_buffer_shortfall_probability,
            self.block_buffer_shortfall_probability,
        )
        _require_ascending(
            "stress_probability",
            self.watch_stress_probability,
            self.block_stress_probability,
        )
        _require_descending(
            "depth_support_score",
            self.watch_min_depth_support_score,
            self.block_min_depth_support_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityTailBufferInput(_FinalPublicDataclass):
    private_research_reference: str
    observed_at: datetime
    model_probability: Decimal
    quoted_probability: Decimal
    downside_tail_probability: Decimal
    upside_tail_probability: Decimal
    liquidity_buffer_probability: Decimal
    depth_support_score: Decimal
    spread_cost_probability: Decimal
    slippage_buffer_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityProbabilityTailBufferInput, "input")
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "quoted_probability",
            "downside_tail_probability",
            "upside_tail_probability",
            "liquidity_buffer_probability",
            "depth_support_score",
            "spread_cost_probability",
            "slippage_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityTailBufferReportRow(_FinalPublicDataclass):
    signal_digest: str
    rank: Decimal
    observed_at: datetime
    model_probability: Decimal
    quoted_probability: Decimal
    absolute_probability_gap: Decimal
    downside_tail_probability: Decimal
    upside_tail_probability: Decimal
    tail_pressure_probability: Decimal
    liquidity_buffer_probability: Decimal
    buffer_shortfall_probability: Decimal
    depth_support_score: Decimal
    spread_cost_probability: Decimal
    slippage_buffer_probability: Decimal
    friction_buffer_probability: Decimal
    stress_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityProbabilityTailBufferReportRow, "row")
        _require_sha256("signal_digest", self.signal_digest)
        object.__setattr__(self, "rank", _count_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "quoted_probability",
            "absolute_probability_gap",
            "downside_tail_probability",
            "upside_tail_probability",
            "tail_pressure_probability",
            "liquidity_buffer_probability",
            "buffer_shortfall_probability",
            "depth_support_score",
            "spread_cost_probability",
            "slippage_buffer_probability",
            "friction_buffer_probability",
            "stress_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _row_validation_digest(self):
                raise ValueError("derived_validation_digest must match row payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_validation_digest(self),
            )
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityTailBufferReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_tail_pressure_probability: Decimal | None
    max_buffer_shortfall_probability: Decimal
    max_stress_probability: Decimal
    min_depth_support_score: Decimal | None
    rows: tuple[ResearchMarketLiquidityProbabilityTailBufferReportRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityProbabilityTailBufferReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_TAIL_BUFFER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_tail_pressure_probability",
            _optional_probability_decimal(
                "average_tail_pressure_probability",
                self.average_tail_pressure_probability,
            ),
        )
        for field_name in ("max_buffer_shortfall_probability", "max_stress_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_depth_support_score",
            _optional_probability_decimal(
                "min_depth_support_score",
                self.min_depth_support_score,
            ),
        )
        object.__setattr__(self, "rows", _rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_validation_digest(self):
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> FrozenJsonObject:
        return research_market_liquidity_probability_tail_buffer_report_payload(self)


def build_research_market_liquidity_probability_tail_buffer_report(
    inputs: Iterable[ResearchMarketLiquidityProbabilityTailBufferInput],
    *,
    config: ResearchMarketLiquidityProbabilityTailBufferReportConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityProbabilityTailBufferReport:
    if type(config) is not ResearchMarketLiquidityProbabilityTailBufferReportConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityProbabilityTailBufferReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    unranked_rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                )
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        replace(row, rank=_count(index), derived_validation_digest="")
        for index, row in enumerate(unranked_rows, start=1)
    )
    return ResearchMarketLiquidityProbabilityTailBufferReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_rollup_status(tuple(row.status for row in rows)),
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_tail_pressure_probability=_average(
            tuple(row.tail_pressure_probability for row in rows),
        ),
        max_buffer_shortfall_probability=_max_decimal(
            tuple(row.buffer_shortfall_probability for row in rows),
        ),
        max_stress_probability=_max_decimal(tuple(row.stress_probability for row in rows)),
        min_depth_support_score=_min_optional(
            tuple(row.depth_support_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
    )


def research_market_liquidity_probability_tail_buffer_report_payload(
    report: ResearchMarketLiquidityProbabilityTailBufferReport | dict[str, Any],
) -> FrozenJsonObject:
    if type(report) is ResearchMarketLiquidityProbabilityTailBufferReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.derived_validation_digest != _report_validation_digest(report):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        _reject_public_status_values(payload)
        return _freeze_json_object(payload)
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        _reject_public_status_values(payload)
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest must match report payload")
        return _freeze_json_object(payload)
    raise ValueError(
        "report must be a ResearchMarketLiquidityProbabilityTailBufferReport",
    )


@dataclass(frozen=True)
class _PayloadFlags:
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

    def __ior__(self, other: object) -> FrozenJsonObject:
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


def _normalize_inputs(
    inputs: Iterable[ResearchMarketLiquidityProbabilityTailBufferInput],
) -> tuple[ResearchMarketLiquidityProbabilityTailBufferInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchMarketLiquidityProbabilityTailBufferInput:
            raise ValueError(
                "inputs must contain ResearchMarketLiquidityProbabilityTailBufferInput",
            )
        _require_hard_flags("input", item)
    return normalized


def _row_from_input(
    item: ResearchMarketLiquidityProbabilityTailBufferInput,
    *,
    config: ResearchMarketLiquidityProbabilityTailBufferReportConfig,
) -> ResearchMarketLiquidityProbabilityTailBufferReportRow:
    absolute_probability_gap = _abs_decimal(
        item.model_probability - item.quoted_probability,
    )
    tail_pressure_probability = max(
        item.downside_tail_probability,
        item.upside_tail_probability,
    )
    buffer_shortfall_probability = max(
        tail_pressure_probability - item.liquidity_buffer_probability,
        ZERO,
    )
    friction_buffer_probability = item.spread_cost_probability + (
        item.slippage_buffer_probability
    )
    stress_probability = min(
        absolute_probability_gap
        + tail_pressure_probability
        + buffer_shortfall_probability
        + friction_buffer_probability,
        ONE,
    )
    status = _row_status(
        tail_pressure_probability=tail_pressure_probability,
        buffer_shortfall_probability=buffer_shortfall_probability,
        stress_probability=stress_probability,
        depth_support_score=item.depth_support_score,
        config=config,
    )
    return ResearchMarketLiquidityProbabilityTailBufferReportRow(
        signal_digest=_signal_digest(item),
        rank=ZERO,
        observed_at=item.observed_at,
        model_probability=item.model_probability,
        quoted_probability=item.quoted_probability,
        absolute_probability_gap=absolute_probability_gap,
        downside_tail_probability=item.downside_tail_probability,
        upside_tail_probability=item.upside_tail_probability,
        tail_pressure_probability=tail_pressure_probability,
        liquidity_buffer_probability=item.liquidity_buffer_probability,
        buffer_shortfall_probability=buffer_shortfall_probability,
        depth_support_score=item.depth_support_score,
        spread_cost_probability=item.spread_cost_probability,
        slippage_buffer_probability=item.slippage_buffer_probability,
        friction_buffer_probability=friction_buffer_probability,
        stress_probability=stress_probability,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            absolute_probability_gap=absolute_probability_gap,
            tail_pressure_probability=tail_pressure_probability,
            buffer_shortfall_probability=buffer_shortfall_probability,
            stress_probability=stress_probability,
            depth_support_score=item.depth_support_score,
            spread_cost_probability=item.spread_cost_probability,
            slippage_buffer_probability=item.slippage_buffer_probability,
            config=config,
        ),
    )


def _row_status(
    *,
    tail_pressure_probability: Decimal,
    buffer_shortfall_probability: Decimal,
    stress_probability: Decimal,
    depth_support_score: Decimal,
    config: ResearchMarketLiquidityProbabilityTailBufferReportConfig,
) -> str:
    if (
        tail_pressure_probability >= config.block_tail_pressure_probability
        or buffer_shortfall_probability >= config.block_buffer_shortfall_probability
        or stress_probability >= config.block_stress_probability
        or depth_support_score <= config.block_min_depth_support_score
    ):
        return STATUS_BLOCK
    if (
        tail_pressure_probability >= config.watch_tail_pressure_probability
        or buffer_shortfall_probability >= config.watch_buffer_shortfall_probability
        or stress_probability >= config.watch_stress_probability
        or depth_support_score <= config.watch_min_depth_support_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    absolute_probability_gap: Decimal,
    tail_pressure_probability: Decimal,
    buffer_shortfall_probability: Decimal,
    stress_probability: Decimal,
    depth_support_score: Decimal,
    spread_cost_probability: Decimal,
    slippage_buffer_probability: Decimal,
    config: ResearchMarketLiquidityProbabilityTailBufferReportConfig,
) -> tuple[str, ...]:
    codes: list[str] = [
        {
            STATUS_BLOCK: REASON_BLOCK,
            STATUS_WATCH: REASON_WATCH,
            STATUS_PASS: REASON_PASS,
        }[status],
    ]
    if tail_pressure_probability >= config.block_tail_pressure_probability:
        codes.append(REASON_TAIL_BLOCK)
    elif tail_pressure_probability >= config.watch_tail_pressure_probability:
        codes.append(REASON_TAIL_WATCH)
    if buffer_shortfall_probability >= config.block_buffer_shortfall_probability:
        codes.append(REASON_BUFFER_BLOCK)
    elif buffer_shortfall_probability >= config.watch_buffer_shortfall_probability:
        codes.append(REASON_BUFFER_WATCH)
    if stress_probability >= config.block_stress_probability:
        codes.append(REASON_STRESS_BLOCK)
    elif stress_probability >= config.watch_stress_probability:
        codes.append(REASON_STRESS_WATCH)
    if depth_support_score <= config.block_min_depth_support_score:
        codes.append(REASON_DEPTH_BLOCK)
    elif depth_support_score <= config.watch_min_depth_support_score:
        codes.append(REASON_DEPTH_WATCH)
    if absolute_probability_gap > ZERO:
        codes.append(REASON_GAP)
    if spread_cost_probability > ZERO:
        codes.append(REASON_SPREAD)
    if slippage_buffer_probability > ZERO:
        codes.append(REASON_SLIPPAGE)
    return tuple(codes)


def _row_sort_key(
    row: ResearchMarketLiquidityProbabilityTailBufferReportRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.stress_probability,
        -row.tail_pressure_probability,
        row.signal_digest,
    )


def _validate_row(row: ResearchMarketLiquidityProbabilityTailBufferReportRow) -> None:
    if row.absolute_probability_gap != _abs_decimal(
        row.model_probability - row.quoted_probability,
    ):
        raise ValueError("absolute_probability_gap must match probabilities")
    if row.tail_pressure_probability != max(
        row.downside_tail_probability,
        row.upside_tail_probability,
    ):
        raise ValueError("tail_pressure_probability must match tail probabilities")
    if row.buffer_shortfall_probability != max(
        row.tail_pressure_probability - row.liquidity_buffer_probability,
        ZERO,
    ):
        raise ValueError("buffer_shortfall_probability must match tail and buffer")
    if row.friction_buffer_probability != _quantize(
        row.spread_cost_probability + row.slippage_buffer_probability,
    ):
        raise ValueError("friction_buffer_probability must match cost probabilities")
    expected_stress = min(
        row.absolute_probability_gap
        + row.tail_pressure_probability
        + row.buffer_shortfall_probability
        + row.friction_buffer_probability,
        ONE,
    )
    if row.stress_probability != _quantize(expected_stress):
        raise ValueError("stress_probability must match row components")


def _validate_report(
    report: ResearchMarketLiquidityProbabilityTailBufferReport,
) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.average_tail_pressure_probability != _average(
        tuple(row.tail_pressure_probability for row in rows),
    ):
        raise ValueError("average_tail_pressure_probability must match rows")
    if report.max_buffer_shortfall_probability != _max_decimal(
        tuple(row.buffer_shortfall_probability for row in rows),
    ):
        raise ValueError("max_buffer_shortfall_probability must match rows")
    if report.max_stress_probability != _max_decimal(
        tuple(row.stress_probability for row in rows),
    ):
        raise ValueError("max_stress_probability must match rows")
    if report.min_depth_support_score != _min_optional(
        tuple(row.depth_support_score for row in rows),
    ):
        raise ValueError("min_depth_support_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityProbabilityTailBufferReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    codes: list[str] = []
    for row in rows:
        for code in row.reason_codes:
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def _report_reason_code_counts(
    rows: tuple[ResearchMarketLiquidityProbabilityTailBufferReportRow, ...],
) -> tuple[ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount(
                reason_code=REASON_MISSING_INPUTS,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount(
            reason_code=code,
            count=_count(counter[code]),
        )
        for code in _report_reason_codes(rows)
    )


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return STATUS_BLOCK
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketLiquidityProbabilityTailBufferReportRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _ratio(sum(values, ZERO), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return min(values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _signal_digest(item: ResearchMarketLiquidityProbabilityTailBufferInput) -> str:
    payload = {
        "private_research_reference": item.private_research_reference,
        "observed_at": item.observed_at.isoformat(),
        "model_probability": str(item.model_probability),
        "quoted_probability": str(item.quoted_probability),
        "downside_tail_probability": str(item.downside_tail_probability),
        "upside_tail_probability": str(item.upside_tail_probability),
        "liquidity_buffer_probability": str(item.liquidity_buffer_probability),
        "depth_support_score": str(item.depth_support_score),
        "spread_cost_probability": str(item.spread_cost_probability),
        "slippage_buffer_probability": str(item.slippage_buffer_probability),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _row_validation_digest(
    row: ResearchMarketLiquidityProbabilityTailBufferReportRow,
) -> str:
    payload = _json_ready_without_digest(row)
    return _payload_validation_digest(payload)


def _report_validation_digest(
    report: ResearchMarketLiquidityProbabilityTailBufferReport,
) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, (list, tuple)):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_public_status_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _reject_public_status_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_status_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public field")


def _rows(
    rows: tuple[ResearchMarketLiquidityProbabilityTailBufferReportRow, ...],
) -> tuple[ResearchMarketLiquidityProbabilityTailBufferReportRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketLiquidityProbabilityTailBufferReportRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityProbabilityTailBufferReportRow",
            )
        _require_hard_flags("row", row)
    return normalized


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    for reason_code in normalized:
        _reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must contain unique values")
    return normalized


def _reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_text(field_name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize(normalized)


def _probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _probability_decimal(field_name, value)


def _count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_ascending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"{field_name} watch threshold must not exceed block threshold")


def _require_descending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value < block_value:
        raise ValueError(f"{field_name} watch threshold must not be below block threshold")
