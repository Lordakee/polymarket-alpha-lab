"""Pure report-only reducer for market fee probability memory ladders."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_MEMORY_LADDER_REPORT_CONFIG_VERSION = (
    "research-market-fee-probability-memory-ladder-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
MARKET_FEE_PROBABILITY_MEMORY_LADDER_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
NO_INPUTS_REASON = "ladder_no_inputs"


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("r", "aw"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "s", "n"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("exec", "ution"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("ap", "i", "_", "key"),
    _join_parts("priv", "ate", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
    "://",
    "?",
    "@",
    "=",
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_MEMORY_LADDER_REPORT_CONFIG_VERSION",
    "MARKET_FEE_PROBABILITY_MEMORY_LADDER_STATUSES",
    "ResearchMarketFeeProbabilityMemoryLadderConfig",
    "ResearchMarketFeeProbabilityMemoryLadderInput",
    "ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount",
    "ResearchMarketFeeProbabilityMemoryLadderReport",
    "ResearchMarketFeeProbabilityMemoryLadderRow",
    "build_research_market_fee_probability_memory_ladder_report",
    "research_market_fee_probability_memory_ladder_report_payload",
    "validate_research_market_fee_probability_memory_ladder_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityMemoryLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
    )
    minimum_pass_probability_gap: Decimal = Decimal("0.080000")
    minimum_watch_probability_gap: Decimal = Decimal("0.030000")
    maximum_pass_fee_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_ratio: Decimal = Decimal("0.030000")
    minimum_pass_memory_confidence: Decimal = Decimal("0.800000")
    minimum_watch_memory_confidence: Decimal = Decimal("0.500000")
    probability_gap_weight: Decimal = Decimal("0.400000")
    fee_efficiency_weight: Decimal = Decimal("0.300000")
    memory_confidence_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityMemoryLadderConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_probability_gap",
            "minimum_watch_probability_gap",
            "maximum_pass_fee_ratio",
            "maximum_watch_fee_ratio",
            "minimum_pass_memory_confidence",
            "minimum_watch_memory_confidence",
            "probability_gap_weight",
            "fee_efficiency_weight",
            "memory_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_probability_gap < self.minimum_watch_probability_gap:
            raise ValueError("minimum_pass_probability_gap must be at least watch")
        if self.maximum_pass_fee_ratio > self.maximum_watch_fee_ratio:
            raise ValueError("maximum_pass_fee_ratio must not exceed watch")
        if self.minimum_pass_memory_confidence < self.minimum_watch_memory_confidence:
            raise ValueError("minimum_pass_memory_confidence must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityMemoryLadderInput(_FinalPublicDataclass):
    private_ref: str
    observed_at: datetime
    research_probability: Decimal
    venue_probability: Decimal
    fee_ratio: Decimal
    memory_confidence: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityMemoryLadderInput, "input")
        _require_private_ref("private_ref", self.private_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "research_probability",
            "venue_probability",
            "fee_ratio",
            "memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityMemoryLadderRow(_FinalPublicDataclass):
    public_row_ref: str
    observed_at: datetime
    research_probability: Decimal
    venue_probability: Decimal
    probability_gap: Decimal
    probability_gap_score: Decimal
    fee_ratio: Decimal
    fee_efficiency_score: Decimal
    memory_confidence: Decimal
    memory_confidence_score: Decimal
    ladder_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityMemoryLadderRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "research_probability",
            "venue_probability",
            "probability_gap_score",
            "fee_ratio",
            "fee_efficiency_score",
            "memory_confidence",
            "memory_confidence_score",
            "ladder_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_gap",
            _require_edge_decimal("probability_gap", self.probability_gap),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount,
            "reason_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_count", self)
        _reject_unsafe_public_payload("reason_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeProbabilityMemoryLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_probability_gap_count: Decimal
    high_fee_count: Decimal
    low_memory_confidence_count: Decimal
    average_ladder_score: Decimal
    min_probability_gap: Decimal
    max_fee_ratio: Decimal
    min_memory_confidence: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeProbabilityMemoryLadderReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_probability_gap_count",
            "high_fee_count",
            "low_memory_confidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_ladder_score",
            "max_fee_ratio",
            "min_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_probability_gap",
            _require_edge_decimal("min_probability_gap", self.min_probability_gap),
        )
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_market_fee_probability_memory_ladder_report_payload(self)


def build_research_market_fee_probability_memory_ladder_report(
    inputs: Iterable[ResearchMarketFeeProbabilityMemoryLadderInput],
    *,
    config: ResearchMarketFeeProbabilityMemoryLadderConfig,
    generated_at: datetime,
) -> ResearchMarketFeeProbabilityMemoryLadderReport:
    if type(config) is not ResearchMarketFeeProbabilityMemoryLadderConfig:
        raise ValueError("config must be a ResearchMarketFeeProbabilityMemoryLadderConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            ((_private_digest(value.private_ref), value) for value in normalized),
            key=lambda item: item[0],
        ),
    )
    if len({key for key, _ in keyed_inputs}) != len(keyed_inputs):
        raise ValueError("private_ref values must be unique")
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    public_row_ref=_public_row_ref(index),
                )
                for index, (_, value) in enumerate(keyed_inputs, start=1)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketFeeProbabilityMemoryLadderReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        low_probability_gap_count=_non_pass_reason_count(rows, "ladder_probability_gap"),
        high_fee_count=_non_pass_reason_count(rows, "ladder_fee_ratio"),
        low_memory_confidence_count=_non_pass_reason_count(
            rows,
            "ladder_memory_confidence",
        ),
        average_ladder_score=_average_row_decimal(rows, "ladder_score"),
        min_probability_gap=_min_row_decimal(rows, "probability_gap"),
        max_fee_ratio=_max_row_decimal(rows, "fee_ratio"),
        min_memory_confidence=_min_row_decimal(rows, "memory_confidence"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_probability_memory_ladder_report_payload(
    report: ResearchMarketFeeProbabilityMemoryLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeProbabilityMemoryLadderReport:
        raise ValueError("report must be a ResearchMarketFeeProbabilityMemoryLadderReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_probability_memory_ladder_report_payload(payload)
    return payload


def validate_research_market_fee_probability_memory_ladder_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    value: ResearchMarketFeeProbabilityMemoryLadderInput,
    *,
    config: ResearchMarketFeeProbabilityMemoryLadderConfig,
    public_row_ref: str,
) -> ResearchMarketFeeProbabilityMemoryLadderRow:
    probability_gap = _quantize_decimal(value.research_probability - value.venue_probability)
    probability_gap_score = _score_for_minimum(
        probability_gap,
        config.minimum_pass_probability_gap,
        config.minimum_watch_probability_gap,
    )
    fee_efficiency_score = _score_for_maximum(
        value.fee_ratio,
        config.maximum_pass_fee_ratio,
        config.maximum_watch_fee_ratio,
    )
    memory_confidence_score = _score_for_minimum(
        value.memory_confidence,
        config.minimum_pass_memory_confidence,
        config.minimum_watch_memory_confidence,
    )
    ladder_score = _ladder_score(
        probability_gap_score=probability_gap_score,
        fee_efficiency_score=fee_efficiency_score,
        memory_confidence_score=memory_confidence_score,
        config=config,
    )
    probability_gap_status = _status_for_minimum(
        probability_gap,
        config.minimum_pass_probability_gap,
        config.minimum_watch_probability_gap,
    )
    fee_ratio_status = _status_for_maximum(
        value.fee_ratio,
        config.maximum_pass_fee_ratio,
        config.maximum_watch_fee_ratio,
    )
    memory_confidence_status = _status_for_minimum(
        value.memory_confidence,
        config.minimum_pass_memory_confidence,
        config.minimum_watch_memory_confidence,
    )
    status = _row_status(
        component_statuses=(
            probability_gap_status,
            fee_ratio_status,
            memory_confidence_status,
        ),
    )
    return ResearchMarketFeeProbabilityMemoryLadderRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        research_probability=value.research_probability,
        venue_probability=value.venue_probability,
        probability_gap=probability_gap,
        probability_gap_score=probability_gap_score,
        fee_ratio=value.fee_ratio,
        fee_efficiency_score=fee_efficiency_score,
        memory_confidence=value.memory_confidence,
        memory_confidence_score=memory_confidence_score,
        ladder_score=ladder_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            probability_gap_status=probability_gap_status,
            fee_ratio_status=fee_ratio_status,
            memory_confidence_status=memory_confidence_status,
        ),
    )


def _ladder_score(
    *,
    probability_gap_score: Decimal,
    fee_efficiency_score: Decimal,
    memory_confidence_score: Decimal,
    config: ResearchMarketFeeProbabilityMemoryLadderConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            probability_gap_score * config.probability_gap_weight
            + fee_efficiency_score * config.fee_efficiency_weight
            + memory_confidence_score * config.memory_confidence_weight,
        )


def _row_status(*, component_statuses: tuple[str, ...]) -> str:
    if BLOCK_STATUS in component_statuses:
        return BLOCK_STATUS
    if WATCH_STATUS in component_statuses:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    probability_gap_status: str,
    fee_ratio_status: str,
    memory_confidence_status: str,
) -> tuple[str, ...]:
    reason_codes = [
        _component_reason("probability_gap", probability_gap_status),
        _component_reason("fee_ratio", fee_ratio_status),
        _component_reason("memory_confidence", memory_confidence_status),
        f"ladder_status_{status}",
    ]
    reason_codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _component_reason(component: str, status: str) -> str:
    return f"ladder_{component}_{status}"


def _score_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value <= pass_value:
        return ONE
    if value >= watch_value:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((watch_value - value) / (watch_value - pass_value))


def _score_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value >= pass_value:
        return ONE
    if value <= watch_value:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((value - watch_value) / (pass_value - watch_value))


def _status_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value <= pass_value:
        return PASS_STATUS
    if value <= watch_value:
        return WATCH_STATUS
    return BLOCK_STATUS


def _status_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value >= pass_value:
        return PASS_STATUS
    if value >= watch_value:
        return WATCH_STATUS
    return BLOCK_STATUS


def _report_status(rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes})),
    )


def _report_reason_code_counts(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
) -> tuple[ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketFeeProbabilityMemoryLadderInput],
) -> tuple[ResearchMarketFeeProbabilityMemoryLadderInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    rows: list[ResearchMarketFeeProbabilityMemoryLadderInput] = []
    try:
        iterator = iter(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    for value in iterator:
        if type(value) is not ResearchMarketFeeProbabilityMemoryLadderInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeProbabilityMemoryLadderInput",
            )
        _require_hard_flags("input", value)
        rows.append(value)
    return tuple(rows)


def _normalize_rows(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
) -> tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketFeeProbabilityMemoryLadderRow:
            raise ValueError("rows must contain ResearchMarketFeeProbabilityMemoryLadderRow")
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount, ...],
) -> tuple[ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount",
            )
        _require_hard_flags("reason_count", value)
    return tuple(sorted(values, key=lambda value: value.reason_code))


def _row_sort_key(row: ResearchMarketFeeProbabilityMemoryLadderRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.ladder_score,
        row.public_row_ref,
    )


def _status_count(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
    reason_prefix: str,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if any(
                reason_code.startswith(reason_prefix)
                and not reason_code.endswith(f"_{PASS_STATUS}")
                for reason_code in row.reason_codes
            )
        ),
    )


def _average_row_decimal(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((getattr(row, field_name) for row in rows), ZERO) / _count_decimal(len(rows)),
        )


def _min_row_decimal(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_decimal(min(getattr(row, field_name) for row in rows))


def _max_row_decimal(
    rows: tuple[ResearchMarketFeeProbabilityMemoryLadderRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_decimal(max(getattr(row, field_name) for row in rows))


def _validate_row_consistency(row: ResearchMarketFeeProbabilityMemoryLadderRow) -> None:
    expected_probability_gap = _quantize_decimal(
        row.research_probability - row.venue_probability,
    )
    if row.probability_gap != expected_probability_gap:
        raise ValueError("probability_gap must match research and venue probabilities")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.ladder_score != _expected_score_from_reason_codes(row):
        raise ValueError("ladder_score must match component scores")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith(f"_{BLOCK_STATUS}") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith(f"_{WATCH_STATUS}") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _expected_score_from_reason_codes(
    row: ResearchMarketFeeProbabilityMemoryLadderRow,
) -> Decimal:
    if _component_reason("probability_gap", _status_for_score(row.probability_gap_score)) not in row.reason_codes:
        raise ValueError("probability_gap_score must match reason_codes")
    if _component_reason("fee_ratio", _reverse_status_for_score(row.fee_efficiency_score)) not in row.reason_codes:
        raise ValueError("fee_efficiency_score must match reason_codes")
    if _component_reason("memory_confidence", _status_for_score(row.memory_confidence_score)) not in row.reason_codes:
        raise ValueError("memory_confidence_score must match reason_codes")
    if f"ladder_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            row.probability_gap_score * Decimal("0.400000")
            + row.fee_efficiency_score * Decimal("0.300000")
            + row.memory_confidence_score * Decimal("0.300000"),
        )


def _status_for_score(score: Decimal) -> str:
    if score <= ZERO:
        return BLOCK_STATUS
    if score < ONE:
        return WATCH_STATUS
    return PASS_STATUS


def _reverse_status_for_score(score: Decimal) -> str:
    return _status_for_score(score)


def _validate_report_consistency(
    report: ResearchMarketFeeProbabilityMemoryLadderReport,
) -> None:
    rows = report.rows
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.input_count < report.row_count:
        raise ValueError("input_count must be at least row_count")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    expected_counts = {
        PASS_STATUS: report.pass_count,
        WATCH_STATUS: report.watch_count,
        BLOCK_STATUS: report.block_count,
    }
    for status, count in expected_counts.items():
        if count != _status_count(rows, status):
            raise ValueError(f"{status}_count must match rows")
    if report.low_probability_gap_count != _non_pass_reason_count(
        rows,
        "ladder_probability_gap",
    ):
        raise ValueError("low_probability_gap_count must match rows")
    if report.high_fee_count != _non_pass_reason_count(rows, "ladder_fee_ratio"):
        raise ValueError("high_fee_count must match rows")
    if report.low_memory_confidence_count != _non_pass_reason_count(
        rows,
        "ladder_memory_confidence",
    ):
        raise ValueError("low_memory_confidence_count must match rows")
    if report.average_ladder_score != _average_row_decimal(rows, "ladder_score"):
        raise ValueError("average_ladder_score must match rows")
    if report.min_probability_gap != _min_row_decimal(rows, "probability_gap"):
        raise ValueError("min_probability_gap must match rows")
    if report.max_fee_ratio != _max_row_decimal(rows, "fee_ratio"):
        raise ValueError("max_fee_ratio must match rows")
    if report.min_memory_confidence != _min_row_decimal(rows, "memory_confidence"):
        raise ValueError("min_memory_confidence must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _weight_sum(config: ResearchMarketFeeProbabilityMemoryLadderConfig) -> Decimal:
    return _quantize_decimal(
        config.probability_gap_weight
        + config.fee_efficiency_weight
        + config.memory_confidence_weight,
    )


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _private_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _public_row_ref(index: int) -> str:
    return f"ladder-row-{index:06d}"


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_ref(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_label(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_payload(field_name, value)


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_label(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: str) -> None:
    if value not in MARKET_FEE_PROBABILITY_MEMORY_LADDER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_edge_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _json_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal value must use exact Decimal type")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime value must use exact datetime type")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    raise ValueError("value is not public JSON")


def _report_derived_validation_digest(
    report: ResearchMarketFeeProbabilityMemoryLadderReport,
) -> str:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    payload.pop("derived_validation_digest", None)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {label}")
