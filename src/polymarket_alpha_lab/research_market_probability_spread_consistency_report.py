"""Readonly probability and spread consistency report for research triage."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_CONSISTENCY_CONFIG_VERSION = (
    "research-market-probability-spread-consistency-v0"
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
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "probability_spread_consistency_pass"
WATCH_REASON = "probability_spread_consistency_watch"
BLOCK_REASON = "probability_spread_consistency_block"
BOOK_MIDPOINT_GAP_WATCH_REASON = "book_midpoint_gap_watch"
BOOK_MIDPOINT_GAP_BLOCK_REASON = "book_midpoint_gap_block"
SPREAD_WIDTH_WATCH_REASON = "spread_width_watch"
SPREAD_WIDTH_BLOCK_REASON = "spread_width_block"
MODEL_MIDPOINT_GAP_WATCH_REASON = "model_midpoint_gap_watch"
MODEL_MIDPOINT_GAP_BLOCK_REASON = "model_midpoint_gap_block"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    BOOK_MIDPOINT_GAP_WATCH_REASON,
    BOOK_MIDPOINT_GAP_BLOCK_REASON,
    SPREAD_WIDTH_WATCH_REASON,
    SPREAD_WIDTH_BLOCK_REASON,
    MODEL_MIDPOINT_GAP_WATCH_REASON,
    MODEL_MIDPOINT_GAP_BLOCK_REASON,
)
REASON_CODE_SET = frozenset(ROW_REASON_CODES)

PASS_CONSISTENCY_SCORE = Decimal("0.833333")
WATCH_CONSISTENCY_SCORE = Decimal("0.500000")
BLOCK_CONSISTENCY_SCORE = Decimal("0.000000")

__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_CONSISTENCY_CONFIG_VERSION",
    "MarketProbabilitySpreadConsistencyConfig",
    "MarketProbabilitySpreadConsistencySignal",
    "MarketProbabilitySpreadConsistencyRow",
    "MarketProbabilitySpreadConsistencyReasonCodeCount",
    "MarketProbabilitySpreadConsistencyReport",
    "build_research_market_probability_spread_consistency_report",
    "research_market_probability_spread_consistency_report_payload",
)


@dataclass(frozen=True)
class MarketProbabilitySpreadConsistencyConfig:
    watch_book_midpoint_gap: Decimal = Decimal("0.010000")
    block_book_midpoint_gap: Decimal = Decimal("0.050000")
    watch_spread_width: Decimal = Decimal("0.040000")
    block_spread_width: Decimal = Decimal("0.080000")
    watch_model_midpoint_gap: Decimal = Decimal("0.030000")
    block_model_midpoint_gap: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilitySpreadConsistencyConfig, "config")
        for field_name in (
            "watch_book_midpoint_gap",
            "block_book_midpoint_gap",
            "watch_spread_width",
            "block_spread_width",
            "watch_model_midpoint_gap",
            "block_model_midpoint_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_book_midpoint_gap <= self.watch_book_midpoint_gap:
            raise ValueError("block_book_midpoint_gap must exceed watch")
        if self.block_spread_width <= self.watch_spread_width:
            raise ValueError("block_spread_width must exceed watch")
        if self.block_model_midpoint_gap <= self.watch_model_midpoint_gap:
            raise ValueError("block_model_midpoint_gap must exceed watch")
        require_paper_only_flags("config", self)
        _reject_private_reference_fields("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class MarketProbabilitySpreadConsistencySignal:
    case_digest: str
    model_probability: Decimal
    book_probability: Decimal
    bid_probability: Decimal
    ask_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilitySpreadConsistencySignal, "signal")
        _require_digest("case_digest", self.case_digest)
        for field_name in (
            "model_probability",
            "book_probability",
            "bid_probability",
            "ask_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.ask_probability < self.bid_probability:
            raise ValueError("ask_probability must be at least bid_probability")
        require_paper_only_flags("signal", self)
        _reject_private_reference_fields("signal", self)
        reject_unsafe_surface_fields("signal", self)


@dataclass(frozen=True)
class MarketProbabilitySpreadConsistencyRow:
    case_digest: str
    model_probability: Decimal
    book_probability: Decimal
    bid_probability: Decimal
    ask_probability: Decimal
    midpoint_probability: Decimal
    spread_width: Decimal
    book_midpoint_gap: Decimal
    model_midpoint_gap: Decimal
    consistency_score: Decimal
    consistency_status: str
    manual_research_ready: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    validation_config: InitVar[MarketProbabilitySpreadConsistencyConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: MarketProbabilitySpreadConsistencyConfig | None,
    ) -> None:
        _require_exact_type(self, MarketProbabilitySpreadConsistencyRow, "row")
        _require_digest("case_digest", self.case_digest)
        for field_name in (
            "model_probability",
            "book_probability",
            "bid_probability",
            "ask_probability",
            "midpoint_probability",
            "spread_width",
            "book_midpoint_gap",
            "model_midpoint_gap",
            "consistency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "model_probability",
            "book_probability",
            "bid_probability",
            "ask_probability",
            "midpoint_probability",
            "spread_width",
            "book_midpoint_gap",
            "model_midpoint_gap",
            "consistency_score",
        ):
            _require_unit_range(field_name, getattr(self, field_name))
        if self.ask_probability < self.bid_probability:
            raise ValueError("ask_probability must be at least bid_probability")
        _require_choice("consistency_status", self.consistency_status, STATUSES)
        if type(self.manual_research_ready) is not bool:
            raise ValueError("manual_research_ready must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self, validation_config)
        require_paper_only_flags("row", self)
        _reject_private_reference_fields("row", self)
        reject_unsafe_surface_fields("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class MarketProbabilitySpreadConsistencyReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketProbabilitySpreadConsistencyReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        require_paper_only_flags("reason code count", self)
        _reject_private_reference_fields("reason code count", self)
        reject_unsafe_surface_fields("reason code count", self)


@dataclass(frozen=True)
class MarketProbabilitySpreadConsistencyReport:
    generated_at: datetime
    config_version: str
    report_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_consistency_score: Decimal
    min_consistency_score: Decimal
    max_book_midpoint_gap: Decimal
    max_spread_width: Decimal
    rows: tuple[MarketProbabilitySpreadConsistencyRow, ...]
    reason_code_counts: tuple[MarketProbabilitySpreadConsistencyReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilitySpreadConsistencyReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_CONSISTENCY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, STATUSES)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_consistency_score",
            "min_consistency_score",
            "max_book_midpoint_gap",
            "max_spread_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_consistency_score",
            "min_consistency_score",
            "max_book_midpoint_gap",
            "max_spread_width",
        ):
            _require_unit_range(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        _reject_private_reference_fields("report", self)
        reject_unsafe_surface_fields("report", self)
        _set_or_validate_digest(self, "report")


def build_research_market_probability_spread_consistency_report(
    signals: Iterable[MarketProbabilitySpreadConsistencySignal],
    *,
    generated_at: datetime,
    config: MarketProbabilitySpreadConsistencyConfig | None = None,
) -> MarketProbabilitySpreadConsistencyReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = (
        MarketProbabilitySpreadConsistencyConfig() if config is None else config
    )
    if type(active_config) is not MarketProbabilitySpreadConsistencyConfig:
        raise ValueError("config must be MarketProbabilitySpreadConsistencyConfig")
    require_paper_only_flags("config", active_config)
    normalized_signals = _normalize_signals(signals)
    report_rows = tuple(
        sorted(
            (
                _row_from_signal(signal, config=active_config)
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    case_count = _decimal_from_int(len(report_rows))
    return MarketProbabilitySpreadConsistencyReport(
        generated_at=generated_at_utc,
        config_version=(
            DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_CONSISTENCY_CONFIG_VERSION
        ),
        report_status=_report_status(report_rows),
        case_count=case_count,
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        mean_consistency_score=_mean_decimal(
            row.consistency_score for row in report_rows
        ),
        min_consistency_score=min(
            (row.consistency_score for row in report_rows),
            default=ZERO,
        ),
        max_book_midpoint_gap=max(
            (row.book_midpoint_gap for row in report_rows),
            default=ZERO,
        ),
        max_spread_width=max((row.spread_width for row in report_rows), default=ZERO),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows),
    )


def research_market_probability_spread_consistency_report_payload(
    report: MarketProbabilitySpreadConsistencyReport,
) -> "FrozenJsonObject":
    if type(report) is not MarketProbabilitySpreadConsistencyReport:
        raise ValueError("report must be exactly MarketProbabilitySpreadConsistencyReport")
    require_paper_only_flags("report", report)
    _reject_private_reference_fields("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_private_reference_fields("payload", payload)
    reject_unsafe_surface_fields("payload", payload)
    _require_payload_digest(payload)
    return _freeze_json_object(payload)


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


def _row_from_signal(
    signal: MarketProbabilitySpreadConsistencySignal,
    *,
    config: MarketProbabilitySpreadConsistencyConfig,
) -> MarketProbabilitySpreadConsistencyRow:
    midpoint_probability = _quantize((signal.bid_probability + signal.ask_probability) / TWO)
    spread_width = _quantize(signal.ask_probability - signal.bid_probability)
    book_midpoint_gap = _quantize(abs(signal.book_probability - midpoint_probability))
    model_midpoint_gap = _quantize(abs(signal.model_probability - midpoint_probability))
    reason_codes = _reason_codes_for_values(
        book_midpoint_gap=book_midpoint_gap,
        spread_width=spread_width,
        model_midpoint_gap=model_midpoint_gap,
        config=config,
    )
    consistency_status = _status_from_reason_codes(reason_codes)
    return MarketProbabilitySpreadConsistencyRow(
        case_digest=signal.case_digest,
        model_probability=signal.model_probability,
        book_probability=signal.book_probability,
        bid_probability=signal.bid_probability,
        ask_probability=signal.ask_probability,
        midpoint_probability=midpoint_probability,
        spread_width=spread_width,
        book_midpoint_gap=book_midpoint_gap,
        model_midpoint_gap=model_midpoint_gap,
        consistency_score=_consistency_score(consistency_status),
        consistency_status=consistency_status,
        manual_research_ready=consistency_status == STATUS_PASS,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _reason_codes_for_values(
    *,
    book_midpoint_gap: Decimal,
    spread_width: Decimal,
    model_midpoint_gap: Decimal,
    config: MarketProbabilitySpreadConsistencyConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    has_block_reason = False

    for reason in (
        _high_value_reason(
            value=book_midpoint_gap,
            watch_value=config.watch_book_midpoint_gap,
            block_value=config.block_book_midpoint_gap,
            watch_reason=BOOK_MIDPOINT_GAP_WATCH_REASON,
            block_reason=BOOK_MIDPOINT_GAP_BLOCK_REASON,
        ),
        _high_value_reason(
            value=spread_width,
            watch_value=config.watch_spread_width,
            block_value=config.block_spread_width,
            watch_reason=SPREAD_WIDTH_WATCH_REASON,
            block_reason=SPREAD_WIDTH_BLOCK_REASON,
        ),
        _high_value_reason(
            value=model_midpoint_gap,
            watch_value=config.watch_model_midpoint_gap,
            block_value=config.block_model_midpoint_gap,
            watch_reason=MODEL_MIDPOINT_GAP_WATCH_REASON,
            block_reason=MODEL_MIDPOINT_GAP_BLOCK_REASON,
        ),
    ):
        if reason is None:
            continue
        detail_reasons.append(reason)
        has_block_reason = has_block_reason or reason.endswith("_block")

    if has_block_reason:
        return (BLOCK_REASON, *detail_reasons)
    if detail_reasons:
        return (WATCH_REASON, *detail_reasons)
    return (PASS_REASON,)


def _high_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str | None:
    if value >= block_value:
        return block_reason
    if value >= watch_value:
        return watch_reason
    return None


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _consistency_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return BLOCK_CONSISTENCY_SCORE
    if status == STATUS_WATCH:
        return WATCH_CONSISTENCY_SCORE
    return PASS_CONSISTENCY_SCORE


def _report_status(rows: tuple[MarketProbabilitySpreadConsistencyRow, ...]) -> str:
    if any(row.consistency_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.consistency_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_signals(
    signals: Iterable[MarketProbabilitySpreadConsistencySignal],
) -> tuple[MarketProbabilitySpreadConsistencySignal, ...]:
    if isinstance(signals, (str, bytes, dict)):
        raise ValueError("signals must be an iterable of signal rows")
    normalized = tuple(signals)
    seen_case_digests: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketProbabilitySpreadConsistencySignal:
            raise ValueError(
                "signals must contain MarketProbabilitySpreadConsistencySignal",
            )
        require_paper_only_flags("signal", signal)
        if signal.case_digest in seen_case_digests:
            raise ValueError("case_digest values must be unique")
        seen_case_digests.add(signal.case_digest)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketProbabilitySpreadConsistencyRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_case_digests: set[str] = set()
    for row in normalized:
        if type(row) is not MarketProbabilitySpreadConsistencyRow:
            raise ValueError("rows must contain MarketProbabilitySpreadConsistencyRow")
        require_paper_only_flags("row", row)
        if row.case_digest in seen_case_digests:
            raise ValueError("rows case_digest values must be unique")
        seen_case_digests.add(row.case_digest)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[MarketProbabilitySpreadConsistencyReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not MarketProbabilitySpreadConsistencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketProbabilitySpreadConsistencyReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: MarketProbabilitySpreadConsistencyRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.consistency_status],
        row.consistency_score,
        row.book_midpoint_gap,
        row.spread_width,
        row.case_digest,
    )


def _reason_code_counts(
    rows: tuple[MarketProbabilitySpreadConsistencyRow, ...],
) -> tuple[MarketProbabilitySpreadConsistencyReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketProbabilitySpreadConsistencyReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[MarketProbabilitySpreadConsistencyRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.consistency_status == status))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _validate_row_consistency(
    row: MarketProbabilitySpreadConsistencyRow,
    validation_config: MarketProbabilitySpreadConsistencyConfig | None,
) -> None:
    if row.midpoint_probability != _quantize(
        (row.bid_probability + row.ask_probability) / TWO,
    ):
        raise ValueError("midpoint_probability must match bid and ask probabilities")
    if row.spread_width != _quantize(row.ask_probability - row.bid_probability):
        raise ValueError("spread_width must match bid and ask probabilities")
    if row.book_midpoint_gap != _quantize(
        abs(row.book_probability - row.midpoint_probability),
    ):
        raise ValueError("book_midpoint_gap must match book and midpoint probabilities")
    if row.model_midpoint_gap != _quantize(
        abs(row.model_probability - row.midpoint_probability),
    ):
        raise ValueError("model_midpoint_gap must match model and midpoint probabilities")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.consistency_status != expected_status:
        raise ValueError("consistency_status must match reason_codes")
    if row.manual_research_ready != (row.consistency_status == STATUS_PASS):
        raise ValueError("manual_research_ready must match consistency_status")
    if row.consistency_score != _consistency_score(row.consistency_status):
        raise ValueError("consistency_score must match consistency_status")
    active_config = (
        MarketProbabilitySpreadConsistencyConfig()
        if validation_config is None
        else validation_config
    )
    if type(active_config) is not MarketProbabilitySpreadConsistencyConfig:
        raise ValueError("validation_config must be MarketProbabilitySpreadConsistencyConfig")
    require_paper_only_flags("validation config", active_config)
    expected_reason_codes = _reason_codes_for_values(
        book_midpoint_gap=row.book_midpoint_gap,
        spread_width=row.spread_width,
        model_midpoint_gap=row.model_midpoint_gap,
        config=active_config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row consistency fields")


def _validate_report_consistency(report: MarketProbabilitySpreadConsistencyReport) -> None:
    expected_values = {
        "case_count": _decimal_from_int(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "mean_consistency_score": _mean_decimal(
            row.consistency_score for row in report.rows
        ),
        "min_consistency_score": min(
            (row.consistency_score for row in report.rows),
            default=ZERO,
        ),
        "max_book_midpoint_gap": max(
            (row.book_midpoint_gap for row in report.rows),
            default=ZERO,
        ),
        "max_spread_width": max((row.spread_width for row in report.rows), default=ZERO),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and len(reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    if reason_codes[0] == WATCH_REASON and any(
        reason.endswith("_block") for reason in reason_codes[1:]
    ):
        raise ValueError("watch reason_codes must not contain block reasons")
    if reason_codes[0] == BLOCK_REASON and not any(
        reason.endswith("_block") for reason in reason_codes[1:]
    ):
        raise ValueError("block reason_codes must include a block detail")
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    _reject_private_reference_fields(f"{label} digest payload", ready_value)
    reject_unsafe_surface_fields(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _require_payload_digest(payload: dict[str, Any]) -> None:
    supplied_digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", supplied_digest)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected_digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _unit_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    _require_unit_range(name, normalized)
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_unit_range(name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")


def _reject_private_reference_fields(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_private_reference_fields(label, asdict(value))
        return
    if type(value) is str:
        if _has_private_reference_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_private_reference_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_private_reference_fields(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_private_reference_fields(label, item)


def _has_private_reference_fragment(value: str) -> bool:
    normalized = value.lower()
    unsafe_fragments = (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "://",
    )
    return any(fragment in normalized for fragment in unsafe_fragments)
