"""Report-only liquidity/probability/resolution guard for research rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_CONFIG_VERSION",
    "LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_STATUSES",
    "ResearchMarketLiquidityProbabilityResolutionGuardConfig",
    "ResearchMarketLiquidityProbabilityResolutionGuardInput",
    "ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount",
    "ResearchMarketLiquidityProbabilityResolutionGuardReport",
    "ResearchMarketLiquidityProbabilityResolutionGuardReportRow",
    "build_research_market_liquidity_probability_resolution_guard_report",
    "research_market_liquidity_probability_resolution_guard_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_CONFIG_VERSION = (
    "research-market-liquidity-probability-resolution-guard-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SIX = Decimal("6.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_liquidity_probability_resolution_guard_inputs"
REASON_PASS = "liquidity_probability_resolution_guard_pass"
REASON_WATCH = "liquidity_probability_resolution_guard_watch"
REASON_BLOCK = "liquidity_probability_resolution_guard_block"
REASON_LIQUIDITY_DEPTH_BLOCK = "liquidity_depth_block"
REASON_LIQUIDITY_DEPTH_WATCH = "liquidity_depth_watch"
REASON_SPREAD_BLOCK = "spread_block"
REASON_SPREAD_WATCH = "spread_watch"
REASON_PROBABILITY_BLOCK = "probability_dislocation_block"
REASON_PROBABILITY_WATCH = "probability_dislocation_watch"
REASON_TIME_BLOCK = "resolution_time_block"
REASON_TIME_WATCH = "resolution_time_watch"
REASON_CONFIDENCE_BLOCK = "resolution_evidence_confidence_block"
REASON_CONFIDENCE_WATCH = "resolution_evidence_confidence_watch"
REASON_AMBIGUITY_BLOCK = "resolution_rule_ambiguity_block"
REASON_AMBIGUITY_WATCH = "resolution_rule_ambiguity_watch"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_BLOCK,
    REASON_WATCH,
    REASON_PASS,
    REASON_LIQUIDITY_DEPTH_BLOCK,
    REASON_LIQUIDITY_DEPTH_WATCH,
    REASON_SPREAD_BLOCK,
    REASON_SPREAD_WATCH,
    REASON_PROBABILITY_BLOCK,
    REASON_PROBABILITY_WATCH,
    REASON_TIME_BLOCK,
    REASON_TIME_WATCH,
    REASON_CONFIDENCE_BLOCK,
    REASON_CONFIDENCE_WATCH,
    REASON_AMBIGUITY_BLOCK,
    REASON_AMBIGUITY_WATCH,
)
REASON_CODE_SET = frozenset(REASON_CODES)
PUBLIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
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
    _join_parts("live", "_", "trad", "ing"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityResolutionGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_CONFIG_VERSION
    )
    watch_min_liquidity_depth_ratio: Decimal = Decimal("1.000000")
    block_min_liquidity_depth_ratio: Decimal = Decimal("0.400000")
    watch_max_quoted_spread_rate: Decimal = Decimal("0.040000")
    block_max_quoted_spread_rate: Decimal = Decimal("0.100000")
    watch_max_probability_dislocation_rate: Decimal = Decimal("0.080000")
    block_max_probability_dislocation_rate: Decimal = Decimal("0.200000")
    watch_max_resolution_rule_ambiguity_rate: Decimal = Decimal("0.300000")
    block_max_resolution_rule_ambiguity_rate: Decimal = Decimal("0.700000")
    watch_min_resolution_evidence_confidence: Decimal = Decimal("0.700000")
    block_min_resolution_evidence_confidence: Decimal = Decimal("0.400000")
    watch_resolution_hours_remaining: Decimal = Decimal("24.000000")
    block_resolution_hours_remaining: Decimal = Decimal("6.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityResolutionGuardConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityResolutionGuardConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_min_liquidity_depth_ratio",
            "watch_resolution_hours_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "block_min_liquidity_depth_ratio",
            "block_resolution_hours_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_max_quoted_spread_rate",
            "block_max_quoted_spread_rate",
            "watch_max_probability_dislocation_rate",
            "block_max_probability_dislocation_rate",
            "watch_max_resolution_rule_ambiguity_rate",
            "block_max_resolution_rule_ambiguity_rate",
            "watch_min_resolution_evidence_confidence",
            "block_min_resolution_evidence_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_descending(
            "liquidity_depth_ratio",
            self.watch_min_liquidity_depth_ratio,
            self.block_min_liquidity_depth_ratio,
        )
        _require_ascending(
            "quoted_spread_rate",
            self.watch_max_quoted_spread_rate,
            self.block_max_quoted_spread_rate,
        )
        _require_ascending(
            "probability_dislocation_rate",
            self.watch_max_probability_dislocation_rate,
            self.block_max_probability_dislocation_rate,
        )
        _require_ascending(
            "resolution_rule_ambiguity_rate",
            self.watch_max_resolution_rule_ambiguity_rate,
            self.block_max_resolution_rule_ambiguity_rate,
        )
        _require_descending(
            "resolution_evidence_confidence",
            self.watch_min_resolution_evidence_confidence,
            self.block_min_resolution_evidence_confidence,
        )
        _require_descending(
            "resolution_hours_remaining",
            self.watch_resolution_hours_remaining,
            self.block_resolution_hours_remaining,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityResolutionGuardInput:
    private_research_reference: str
    observed_at: datetime
    liquidity_depth_ratio: Decimal
    quoted_spread_rate: Decimal
    anchor_probability: Decimal
    market_probability: Decimal
    resolution_hours_remaining: Decimal
    resolution_evidence_confidence: Decimal
    resolution_rule_ambiguity_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityResolutionGuardInput does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityResolutionGuardInput,
            "input",
        )
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "liquidity_depth_ratio",
            _nonnegative_decimal("liquidity_depth_ratio", self.liquidity_depth_ratio),
        )
        object.__setattr__(
            self,
            "resolution_hours_remaining",
            _nonnegative_decimal(
                "resolution_hours_remaining",
                self.resolution_hours_remaining,
            ),
        )
        for field_name in (
            "quoted_spread_rate",
            "anchor_probability",
            "market_probability",
            "resolution_evidence_confidence",
            "resolution_rule_ambiguity_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityResolutionGuardReportRow:
    signal_digest: str
    rank: Decimal
    observed_at: datetime
    liquidity_depth_ratio: Decimal
    quoted_spread_rate: Decimal
    anchor_probability: Decimal
    market_probability: Decimal
    probability_dislocation_rate: Decimal
    resolution_hours_remaining: Decimal
    resolution_evidence_confidence: Decimal
    resolution_rule_ambiguity_rate: Decimal
    liquidity_stress_score: Decimal
    probability_resolution_guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityResolutionGuardReportRow does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityResolutionGuardReportRow,
            "row",
        )
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "rank", _positive_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "liquidity_depth_ratio",
            _nonnegative_decimal("liquidity_depth_ratio", self.liquidity_depth_ratio),
        )
        object.__setattr__(
            self,
            "resolution_hours_remaining",
            _nonnegative_decimal(
                "resolution_hours_remaining",
                self.resolution_hours_remaining,
            ),
        )
        for field_name in (
            "quoted_spread_rate",
            "anchor_probability",
            "market_probability",
            "probability_dislocation_rate",
            "resolution_evidence_confidence",
            "resolution_rule_ambiguity_rate",
            "liquidity_stress_score",
            "probability_resolution_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
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
class ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityResolutionGuardReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_dislocation_rate: Decimal | None
    max_probability_dislocation_rate: Decimal
    min_liquidity_depth_ratio: Decimal | None
    min_resolution_evidence_confidence: Decimal | None
    max_resolution_rule_ambiguity_rate: Decimal
    max_probability_resolution_guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketLiquidityProbabilityResolutionGuardReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityResolutionGuardReport does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityResolutionGuardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_probability_dislocation_rate",
            _optional_ratio_decimal(
                "average_probability_dislocation_rate",
                self.average_probability_dislocation_rate,
            ),
        )
        object.__setattr__(
            self,
            "min_liquidity_depth_ratio",
            _optional_nonnegative_decimal(
                "min_liquidity_depth_ratio",
                self.min_liquidity_depth_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_resolution_evidence_confidence",
            _optional_ratio_decimal(
                "min_resolution_evidence_confidence",
                self.min_resolution_evidence_confidence,
            ),
        )
        for field_name in (
            "max_probability_dislocation_rate",
            "max_resolution_rule_ambiguity_rate",
            "max_probability_resolution_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
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
        return research_market_liquidity_probability_resolution_guard_report_payload(
            self,
        )


def build_research_market_liquidity_probability_resolution_guard_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketLiquidityProbabilityResolutionGuardConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityProbabilityResolutionGuardReport:
    if type(config) is not ResearchMarketLiquidityProbabilityResolutionGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityProbabilityResolutionGuardConfig",
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
        ResearchMarketLiquidityProbabilityResolutionGuardReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(unranked_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketLiquidityProbabilityResolutionGuardReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_probability_dislocation_rate=_average(
            tuple(row.probability_dislocation_rate for row in rows),
        ),
        max_probability_dislocation_rate=_maximum(
            tuple(row.probability_dislocation_rate for row in rows),
            ZERO,
        ),
        min_liquidity_depth_ratio=_minimum(
            tuple(row.liquidity_depth_ratio for row in rows),
        ),
        min_resolution_evidence_confidence=_minimum(
            tuple(row.resolution_evidence_confidence for row in rows),
        ),
        max_resolution_rule_ambiguity_rate=_maximum(
            tuple(row.resolution_rule_ambiguity_rate for row in rows),
            ZERO,
        ),
        max_probability_resolution_guard_score=_maximum(
            tuple(row.probability_resolution_guard_score for row in rows),
            ZERO,
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_liquidity_probability_resolution_guard_report_payload(
    report: ResearchMarketLiquidityProbabilityResolutionGuardReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketLiquidityProbabilityResolutionGuardReport:
        _require_hard_flags("report", report)
        _verify_digest(report, "report")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketLiquidityProbabilityResolutionGuardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _verify_payload_digest(payload)
    return _freeze_json_object(payload)


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
    item: ResearchMarketLiquidityProbabilityResolutionGuardInput,
    *,
    config: ResearchMarketLiquidityProbabilityResolutionGuardConfig,
) -> dict[str, object]:
    probability_dislocation_rate = _ratio_decimal(
        "probability_dislocation_rate",
        abs(item.anchor_probability - item.market_probability),
    )
    liquidity_shortfall_rate = _liquidity_shortfall_rate(item, config)
    spread_pressure_rate = _threshold_pressure(
        item.quoted_spread_rate,
        config.block_max_quoted_spread_rate,
    )
    probability_pressure_rate = _threshold_pressure(
        probability_dislocation_rate,
        config.block_max_probability_dislocation_rate,
    )
    resolution_time_pressure_rate = _resolution_time_pressure_rate(item, config)
    evidence_gap_rate = _ratio_decimal(
        "resolution_evidence_gap_rate",
        ONE - item.resolution_evidence_confidence,
    )
    ambiguity_pressure_rate = item.resolution_rule_ambiguity_rate
    liquidity_stress_score = _average_nonempty(
        (liquidity_shortfall_rate, spread_pressure_rate),
    )
    probability_resolution_guard_score = _average_nonempty(
        (
            liquidity_shortfall_rate,
            spread_pressure_rate,
            probability_pressure_rate,
            resolution_time_pressure_rate,
            evidence_gap_rate,
            ambiguity_pressure_rate,
        ),
    )
    status = _row_status(
        liquidity_depth_ratio=item.liquidity_depth_ratio,
        quoted_spread_rate=item.quoted_spread_rate,
        probability_dislocation_rate=probability_dislocation_rate,
        resolution_hours_remaining=item.resolution_hours_remaining,
        resolution_evidence_confidence=item.resolution_evidence_confidence,
        resolution_rule_ambiguity_rate=item.resolution_rule_ambiguity_rate,
        config=config,
    )
    return {
        "signal_digest": _private_reference_digest(item.private_research_reference),
        "observed_at": item.observed_at,
        "liquidity_depth_ratio": item.liquidity_depth_ratio,
        "quoted_spread_rate": item.quoted_spread_rate,
        "anchor_probability": item.anchor_probability,
        "market_probability": item.market_probability,
        "probability_dislocation_rate": probability_dislocation_rate,
        "resolution_hours_remaining": item.resolution_hours_remaining,
        "resolution_evidence_confidence": item.resolution_evidence_confidence,
        "resolution_rule_ambiguity_rate": item.resolution_rule_ambiguity_rate,
        "liquidity_stress_score": liquidity_stress_score,
        "probability_resolution_guard_score": probability_resolution_guard_score,
        "status": status,
        "reason_codes": _row_reason_codes(
            liquidity_depth_ratio=item.liquidity_depth_ratio,
            quoted_spread_rate=item.quoted_spread_rate,
            probability_dislocation_rate=probability_dislocation_rate,
            resolution_hours_remaining=item.resolution_hours_remaining,
            resolution_evidence_confidence=item.resolution_evidence_confidence,
            resolution_rule_ambiguity_rate=item.resolution_rule_ambiguity_rate,
            status=status,
            config=config,
        ),
    }


def _liquidity_shortfall_rate(
    item: ResearchMarketLiquidityProbabilityResolutionGuardInput,
    config: ResearchMarketLiquidityProbabilityResolutionGuardConfig,
) -> Decimal:
    if item.liquidity_depth_ratio >= config.watch_min_liquidity_depth_ratio:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = (
            config.watch_min_liquidity_depth_ratio - item.liquidity_depth_ratio
        ) / config.watch_min_liquidity_depth_ratio
    return _ratio_decimal("liquidity_shortfall_rate", value)


def _threshold_pressure(value: Decimal, block_value: Decimal) -> Decimal:
    if block_value <= ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        pressure = value / block_value
    return _clamped_ratio("threshold_pressure", pressure)


def _resolution_time_pressure_rate(
    item: ResearchMarketLiquidityProbabilityResolutionGuardInput,
    config: ResearchMarketLiquidityProbabilityResolutionGuardConfig,
) -> Decimal:
    if item.resolution_hours_remaining >= config.watch_resolution_hours_remaining:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        pressure = (
            config.watch_resolution_hours_remaining - item.resolution_hours_remaining
        ) / config.watch_resolution_hours_remaining
    return _clamped_ratio("resolution_time_pressure_rate", pressure)


def _row_status(
    *,
    liquidity_depth_ratio: Decimal,
    quoted_spread_rate: Decimal,
    probability_dislocation_rate: Decimal,
    resolution_hours_remaining: Decimal,
    resolution_evidence_confidence: Decimal,
    resolution_rule_ambiguity_rate: Decimal,
    config: ResearchMarketLiquidityProbabilityResolutionGuardConfig,
) -> str:
    if (
        liquidity_depth_ratio <= config.block_min_liquidity_depth_ratio
        or quoted_spread_rate >= config.block_max_quoted_spread_rate
        or probability_dislocation_rate >= config.block_max_probability_dislocation_rate
        or resolution_hours_remaining <= config.block_resolution_hours_remaining
        or resolution_evidence_confidence
        <= config.block_min_resolution_evidence_confidence
        or resolution_rule_ambiguity_rate
        >= config.block_max_resolution_rule_ambiguity_rate
    ):
        return STATUS_BLOCK
    if (
        liquidity_depth_ratio < config.watch_min_liquidity_depth_ratio
        or quoted_spread_rate >= config.watch_max_quoted_spread_rate
        or probability_dislocation_rate >= config.watch_max_probability_dislocation_rate
        or resolution_hours_remaining <= config.watch_resolution_hours_remaining
        or resolution_evidence_confidence
        <= config.watch_min_resolution_evidence_confidence
        or resolution_rule_ambiguity_rate
        >= config.watch_max_resolution_rule_ambiguity_rate
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    liquidity_depth_ratio: Decimal,
    quoted_spread_rate: Decimal,
    probability_dislocation_rate: Decimal,
    resolution_hours_remaining: Decimal,
    resolution_evidence_confidence: Decimal,
    resolution_rule_ambiguity_rate: Decimal,
    status: str,
    config: ResearchMarketLiquidityProbabilityResolutionGuardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if status == STATUS_BLOCK:
        reasons.append(REASON_BLOCK)
    elif status == STATUS_WATCH:
        reasons.append(REASON_WATCH)
    else:
        reasons.append(REASON_PASS)
    if liquidity_depth_ratio <= config.block_min_liquidity_depth_ratio:
        reasons.append(REASON_LIQUIDITY_DEPTH_BLOCK)
    elif liquidity_depth_ratio < config.watch_min_liquidity_depth_ratio:
        reasons.append(REASON_LIQUIDITY_DEPTH_WATCH)
    if quoted_spread_rate >= config.block_max_quoted_spread_rate:
        reasons.append(REASON_SPREAD_BLOCK)
    elif quoted_spread_rate >= config.watch_max_quoted_spread_rate:
        reasons.append(REASON_SPREAD_WATCH)
    if probability_dislocation_rate >= config.block_max_probability_dislocation_rate:
        reasons.append(REASON_PROBABILITY_BLOCK)
    elif probability_dislocation_rate >= config.watch_max_probability_dislocation_rate:
        reasons.append(REASON_PROBABILITY_WATCH)
    if resolution_hours_remaining <= config.block_resolution_hours_remaining:
        reasons.append(REASON_TIME_BLOCK)
    elif resolution_hours_remaining <= config.watch_resolution_hours_remaining:
        reasons.append(REASON_TIME_WATCH)
    if resolution_evidence_confidence <= config.block_min_resolution_evidence_confidence:
        reasons.append(REASON_CONFIDENCE_BLOCK)
    elif resolution_evidence_confidence <= config.watch_min_resolution_evidence_confidence:
        reasons.append(REASON_CONFIDENCE_WATCH)
    if resolution_rule_ambiguity_rate >= config.block_max_resolution_rule_ambiguity_rate:
        reasons.append(REASON_AMBIGUITY_BLOCK)
    elif resolution_rule_ambiguity_rate >= config.watch_max_resolution_rule_ambiguity_rate:
        reasons.append(REASON_AMBIGUITY_WATCH)
    return tuple(reasons)


def _unranked_row_sort_key(row: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    status = row["status"]
    score = row["probability_resolution_guard_score"]
    signal_digest = row["signal_digest"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(score) is not Decimal:
        raise ValueError("probability_resolution_guard_score must be a Decimal")
    if type(signal_digest) is not str:
        raise ValueError("signal_digest must be a string")
    return (
        STATUS_SORT_RANK[status],
        -score,
        signal_digest,
    )


def _report_status(
    rows: tuple[ResearchMarketLiquidityProbabilityResolutionGuardReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityProbabilityResolutionGuardReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketLiquidityProbabilityResolutionGuardReportRow, ...],
) -> tuple[ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount, ...]:
    if reason_codes == (REASON_MISSING_INPUTS,):
        return (
            ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount(
                reason_code=REASON_MISSING_INPUTS,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in set(row.reason_codes))
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_ratio(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in reason_codes
    )


def _validate_row(
    row: ResearchMarketLiquidityProbabilityResolutionGuardReportRow,
) -> None:
    if row.probability_dislocation_rate != _ratio_decimal(
        "probability_dislocation_rate",
        abs(row.anchor_probability - row.market_probability),
    ):
        raise ValueError("probability_dislocation_rate must match probabilities")
    if row.probability_resolution_guard_score < ZERO:
        raise ValueError("probability_resolution_guard_score must be nonnegative")


def _validate_report(
    report: ResearchMarketLiquidityProbabilityResolutionGuardReport,
) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_probability_dislocation_rate != _average(
        tuple(row.probability_dislocation_rate for row in rows),
    ):
        raise ValueError("average_probability_dislocation_rate must match rows")
    if report.max_probability_dislocation_rate != _maximum(
        tuple(row.probability_dislocation_rate for row in rows),
        ZERO,
    ):
        raise ValueError("max_probability_dislocation_rate must match rows")
    if report.min_liquidity_depth_ratio != _minimum(
        tuple(row.liquidity_depth_ratio for row in rows),
    ):
        raise ValueError("min_liquidity_depth_ratio must match rows")
    if report.min_resolution_evidence_confidence != _minimum(
        tuple(row.resolution_evidence_confidence for row in rows),
    ):
        raise ValueError("min_resolution_evidence_confidence must match rows")
    if report.max_resolution_rule_ambiguity_rate != _maximum(
        tuple(row.resolution_rule_ambiguity_rate for row in rows),
        ZERO,
    ):
        raise ValueError("max_resolution_rule_ambiguity_rate must match rows")
    if report.max_probability_resolution_guard_score != _maximum(
        tuple(row.probability_resolution_guard_score for row in rows),
        ZERO,
    ):
        raise ValueError("max_probability_resolution_guard_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match reason_codes")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")


def _row_sort_key(
    row: ResearchMarketLiquidityProbabilityResolutionGuardReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.probability_resolution_guard_score,
        row.signal_digest,
    )


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketLiquidityProbabilityResolutionGuardInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen_digests: set[str] = set()
    for item in rows:
        if type(item) is not ResearchMarketLiquidityProbabilityResolutionGuardInput:
            raise ValueError(
                "inputs must contain "
                "ResearchMarketLiquidityProbabilityResolutionGuardInput values",
            )
        _require_hard_flags("input", item)
        signal_digest = _private_reference_digest(item.private_research_reference)
        if signal_digest in seen_digests:
            raise ValueError("inputs signal digests must be unique")
        seen_digests.add(signal_digest)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketLiquidityProbabilityResolutionGuardReportRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketLiquidityProbabilityResolutionGuardReportRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketLiquidityProbabilityResolutionGuardReportRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row, "row")
        if row.signal_digest in seen_digests:
            raise ValueError("rows signal digests must be unique")
        seen_digests.add(row.signal_digest)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    for count in counts:
        if (
            type(count)
            is not ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount "
                "values",
            )
        _require_hard_flags("reason code count", count)
    return counts


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _average_nonempty(values)


def _average_nonempty(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _maximum(values: tuple[Decimal, ...], default: Decimal) -> Decimal:
    if not values:
        return default
    return max(values)


def _minimum(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return min(values)


def _status_count(
    rows: tuple[ResearchMarketLiquidityProbabilityResolutionGuardReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _ratio_decimal("ratio", numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_public_identifier(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    return value


def _require_private_reference(name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    if len(value) > 4096:
        raise ValueError(f"{name} is too long")
    return value


def _require_sha256_digest(name: str, value: object) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a supported reason code")
    return value


def _require_status(name: str, value: object) -> str:
    if (
        type(value) is not str
        or value not in LIQUIDITY_PROBABILITY_RESOLUTION_GUARD_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _normalize_reason_codes(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must not be empty")
    return tuple(_require_reason_code(name, value) for value in values)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be at most one")
    return decimal_value


def _optional_ratio_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _ratio_decimal(name, value)


def _optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_decimal(name, value)


def _clamped_ratio(name: str, value: Decimal) -> Decimal:
    decimal_value = _nonnegative_decimal(name, value)
    if decimal_value > ONE:
        return ONE
    return decimal_value


def _require_ascending(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value >= block_value:
        raise ValueError(f"{name} watch threshold must be below block")


def _require_descending(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value <= block_value:
        raise ValueError(f"{name} watch threshold must exceed block")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _set_or_verify_digest(value: object, label: str) -> None:
    digest = _digest_for_value(value)
    current = getattr(value, "derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", digest)
        return
    if current != digest:
        raise ValueError(f"{label} derived_validation_digest does not match payload")


def _verify_digest(value: object, label: str) -> None:
    current = getattr(value, "derived_validation_digest", None)
    if type(current) is not str or SHA256_RE.fullmatch(current) is None:
        raise ValueError(f"{label} derived_validation_digest must be a sha256 digest")
    expected = _digest_for_value(value)
    if current != expected:
        raise ValueError(f"{label} derived_validation_digest does not match payload")


def _digest_for_value(value: object) -> str:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_mapping(payload)


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    _verify_nested_payload_digest(payload)


def _verify_nested_payload_digest(value: Any) -> None:
    if isinstance(value, dict):
        if "derived_validation_digest" in value:
            current = value["derived_validation_digest"]
            if type(current) is not str or SHA256_RE.fullmatch(current) is None:
                raise ValueError("derived_validation_digest must be a sha256 digest")
            expected = _digest_mapping(value)
            if current != expected:
                raise ValueError("derived_validation_digest does not match payload")
        for item in value.values():
            _verify_nested_payload_digest(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _verify_nested_payload_digest(item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is float or type(value) is int:
        raise ValueError("payload value must not be a raw number")
    if type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    payload = _json_ready(value)
    _reject_unsafe_public_payload_value(label, payload)


def _reject_unsafe_public_payload_value(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload_value(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload_value(label, item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")


def _freeze_json_object(value: dict[str, Any]) -> "FrozenJsonObject":
    frozen = {key: _freeze_json_value(item) for key, item in value.items()}
    return FrozenJsonObject(frozen)


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value
