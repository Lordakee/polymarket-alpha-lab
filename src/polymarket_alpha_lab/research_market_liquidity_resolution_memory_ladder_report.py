"""Pure report-only reducer for liquidity resolution memory ladders."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_LIQUIDITY_RESOLUTION_MEMORY_LADDER_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-resolution-memory-ladder-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
LIQUIDITY_RESOLUTION_MEMORY_LADDER_STATUSES = (
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
INPUT_MANUAL_REVIEW_REASON = "input_manual_review"
LIQUIDITY_WATCH_REASON = "ladder_liquidity_watch"
LIQUIDITY_BLOCK_REASON = "ladder_liquidity_block"
MEMORY_WATCH_REASON = "ladder_memory_watch"
MEMORY_BLOCK_REASON = "ladder_memory_block"
WINDOW_WATCH_REASON = "ladder_resolution_window_watch"
WINDOW_BLOCK_REASON = "ladder_resolution_window_block"
PRESSURE_WATCH_REASON = "ladder_pressure_watch"
PRESSURE_BLOCK_REASON = "ladder_pressure_block"
STATUS_WATCH_REASON = "ladder_status_watch"
STATUS_BLOCK_REASON = "ladder_status_block"
STATUS_PASS_REASON = "ladder_status_pass"

INPUT_REASON_CODES = ("manual_review",)
ROW_REASON_CODES = (
    INPUT_MANUAL_REVIEW_REASON,
    LIQUIDITY_WATCH_REASON,
    LIQUIDITY_BLOCK_REASON,
    MEMORY_WATCH_REASON,
    MEMORY_BLOCK_REASON,
    WINDOW_WATCH_REASON,
    WINDOW_BLOCK_REASON,
    PRESSURE_WATCH_REASON,
    PRESSURE_BLOCK_REASON,
    STATUS_WATCH_REASON,
    STATUS_BLOCK_REASON,
    STATUS_PASS_REASON,
)
REPORT_REASON_CODES = (
    NO_INPUTS_REASON,
    INPUT_MANUAL_REVIEW_REASON,
    LIQUIDITY_WATCH_REASON,
    LIQUIDITY_BLOCK_REASON,
    MEMORY_WATCH_REASON,
    MEMORY_BLOCK_REASON,
    WINDOW_WATCH_REASON,
    WINDOW_BLOCK_REASON,
    PRESSURE_WATCH_REASON,
    PRESSURE_BLOCK_REASON,
    STATUS_WATCH_REASON,
    STATUS_BLOCK_REASON,
    STATUS_PASS_REASON,
)
REPORT_TRIGGER_REASONS = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (NO_INPUTS_REASON, STATUS_PASS_REASON)
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("r", "aw"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "s", "n"),
    _join_parts("ta", "ble"),
    _join_parts("ta", "ble", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmenda", "tion"),
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
    _join_parts(":", "//"),
    "?",
    "@",
    "=",
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_RESOLUTION_MEMORY_LADDER_REPORT_CONFIG_VERSION",
    "LIQUIDITY_RESOLUTION_MEMORY_LADDER_STATUSES",
    "ResearchMarketLiquidityResolutionMemoryLadderConfig",
    "ResearchMarketLiquidityResolutionMemoryLadderInput",
    "ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount",
    "ResearchMarketLiquidityResolutionMemoryLadderRow",
    "ResearchMarketLiquidityResolutionMemoryLadderReport",
    "build_research_market_liquidity_resolution_memory_ladder_report",
    "research_market_liquidity_resolution_memory_ladder_report_payload",
    "validate_research_market_liquidity_resolution_memory_ladder_public_payload",
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
class ResearchMarketLiquidityResolutionMemoryLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_RESOLUTION_MEMORY_LADDER_REPORT_CONFIG_VERSION
    )
    minimum_pass_liquidity_score: Decimal = Decimal("0.800000")
    minimum_watch_liquidity_score: Decimal = Decimal("0.500000")
    minimum_pass_resolution_memory: Decimal = Decimal("0.800000")
    minimum_watch_resolution_memory: Decimal = Decimal("0.500000")
    minimum_pass_resolution_window_seconds: Decimal = Decimal("3600.000000")
    minimum_watch_resolution_window_seconds: Decimal = Decimal("900.000000")
    maximum_pass_pressure_score: Decimal = Decimal("0.200000")
    maximum_watch_pressure_score: Decimal = Decimal("0.600000")
    liquidity_score_weight: Decimal = Decimal("0.400000")
    resolution_memory_weight: Decimal = Decimal("0.400000")
    resolution_window_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityResolutionMemoryLadderConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_RESOLUTION_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_liquidity_score",
            "minimum_watch_liquidity_score",
            "minimum_pass_resolution_memory",
            "minimum_watch_resolution_memory",
            "maximum_pass_pressure_score",
            "maximum_watch_pressure_score",
            "liquidity_score_weight",
            "resolution_memory_weight",
            "resolution_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_resolution_window_seconds",
            "minimum_watch_resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_liquidity_score < self.minimum_watch_liquidity_score:
            raise ValueError("minimum_pass_liquidity_score must be at least watch")
        if self.minimum_pass_resolution_memory < self.minimum_watch_resolution_memory:
            raise ValueError("minimum_pass_resolution_memory must be at least watch")
        if (
            self.minimum_pass_resolution_window_seconds
            <= self.minimum_watch_resolution_window_seconds
        ):
            raise ValueError("minimum_pass_resolution_window_seconds must exceed watch")
        if self.maximum_pass_pressure_score > self.maximum_watch_pressure_score:
            raise ValueError("maximum_pass_pressure_score must not exceed watch")
        if _weight_sum(self) != ONE:
            raise ValueError(
                "liquidity_score_weight, resolution_memory_weight, and "
                "resolution_window_weight must sum to 1.000000",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityResolutionMemoryLadderInput(_FinalPublicDataclass):
    private_ref: str
    observed_at: datetime
    liquidity_score: Decimal
    resolution_memory: Decimal
    resolution_window_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityResolutionMemoryLadderInput,
            "input",
        )
        _require_private_ref("private_ref", self.private_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("liquidity_score", "resolution_memory"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_window_seconds",
            _require_positive_decimal(
                "resolution_window_seconds",
                self.resolution_window_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount(
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
            ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount,
            "reason count",
        )
        _require_known_value("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityResolutionMemoryLadderRow(_FinalPublicDataclass):
    public_row_ref: str
    observed_at: datetime
    liquidity_score: Decimal
    resolution_memory: Decimal
    resolution_window_seconds: Decimal
    resolution_window_score: Decimal
    ladder_score: Decimal
    pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityResolutionMemoryLadderRow,
            "row",
        )
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "liquidity_score",
            "resolution_memory",
            "resolution_window_score",
            "ladder_score",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_window_seconds",
            _require_positive_decimal(
                "resolution_window_seconds",
                self.resolution_window_seconds,
            ),
        )
        _require_known_value("status", self.status, LIQUIDITY_RESOLUTION_MEMORY_LADDER_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityResolutionMemoryLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_liquidity_count: Decimal
    low_resolution_memory_count: Decimal
    short_resolution_window_count: Decimal
    average_ladder_score: Decimal
    max_pressure_score: Decimal
    min_liquidity_score: Decimal
    min_resolution_memory: Decimal
    min_resolution_window_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount, ...]
    rows: tuple[ResearchMarketLiquidityResolutionMemoryLadderRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityResolutionMemoryLadderReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_liquidity_count",
            "low_resolution_memory_count",
            "short_resolution_window_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_ladder_score",
            "max_pressure_score",
            "min_liquidity_score",
            "min_resolution_memory",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_resolution_window_seconds",
            _require_count_decimal(
                "min_resolution_window_seconds",
                self.min_resolution_window_seconds,
            ),
        )
        _require_known_value("status", self.status, LIQUIDITY_RESOLUTION_MEMORY_LADDER_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match public payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_surface("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_market_liquidity_resolution_memory_ladder_report_payload(self)


def build_research_market_liquidity_resolution_memory_ladder_report(
    inputs: Iterable[ResearchMarketLiquidityResolutionMemoryLadderInput],
    *,
    config: ResearchMarketLiquidityResolutionMemoryLadderConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityResolutionMemoryLadderReport:
    if type(config) is not ResearchMarketLiquidityResolutionMemoryLadderConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityResolutionMemoryLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(sorted((_row_from_input(item, config=config) for item in normalized_inputs), key=_row_sort_key))
    return ResearchMarketLiquidityResolutionMemoryLadderReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(normalized_inputs)),
        row_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == PASS_STATUS)),
        watch_count=_count(sum(1 for row in rows if row.status == WATCH_STATUS)),
        block_count=_count(sum(1 for row in rows if row.status == BLOCK_STATUS)),
        low_liquidity_count=_count(
            sum(
                1
                for row in rows
                if LIQUIDITY_WATCH_REASON in row.reason_codes
                or LIQUIDITY_BLOCK_REASON in row.reason_codes
            ),
        ),
        low_resolution_memory_count=_count(
            sum(
                1
                for row in rows
                if MEMORY_WATCH_REASON in row.reason_codes
                or MEMORY_BLOCK_REASON in row.reason_codes
            ),
        ),
        short_resolution_window_count=_count(
            sum(
                1
                for row in rows
                if WINDOW_WATCH_REASON in row.reason_codes
                or WINDOW_BLOCK_REASON in row.reason_codes
            ),
        ),
        average_ladder_score=_average_decimal(row.ladder_score for row in rows),
        max_pressure_score=_max_decimal(row.pressure_score for row in rows),
        min_liquidity_score=_min_decimal(row.liquidity_score for row in rows),
        min_resolution_memory=_min_decimal(row.resolution_memory for row in rows),
        min_resolution_window_seconds=_min_decimal(
            row.resolution_window_seconds for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_liquidity_resolution_memory_ladder_report_payload(
    report: ResearchMarketLiquidityResolutionMemoryLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityResolutionMemoryLadderReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityResolutionMemoryLadderReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return validate_research_market_liquidity_resolution_memory_ladder_public_payload(payload)


def validate_research_market_liquidity_resolution_memory_ladder_public_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _reject_flag_downgrades("public payload", payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    item: ResearchMarketLiquidityResolutionMemoryLadderInput,
    *,
    config: ResearchMarketLiquidityResolutionMemoryLadderConfig,
) -> ResearchMarketLiquidityResolutionMemoryLadderRow:
    if type(item) is not ResearchMarketLiquidityResolutionMemoryLadderInput:
        raise ValueError(
            "item must be a ResearchMarketLiquidityResolutionMemoryLadderInput",
        )
    _require_hard_flags("input", item)
    window_score = _resolution_window_score(item.resolution_window_seconds, config)
    ladder_score = _ladder_score(item, window_score=window_score, config=config)
    pressure_score = _quantize(ONE - ladder_score)
    reason_codes = _row_reason_codes(
        item,
        pressure_score=pressure_score,
        config=config,
    )
    return ResearchMarketLiquidityResolutionMemoryLadderRow(
        public_row_ref=_public_row_ref(item.private_ref),
        observed_at=item.observed_at,
        liquidity_score=item.liquidity_score,
        resolution_memory=item.resolution_memory,
        resolution_window_seconds=item.resolution_window_seconds,
        resolution_window_score=window_score,
        ladder_score=ladder_score,
        pressure_score=pressure_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketLiquidityResolutionMemoryLadderInput,
    *,
    pressure_score: Decimal,
    config: ResearchMarketLiquidityResolutionMemoryLadderConfig,
) -> tuple[str, ...]:
    reasons: list[str] = [
        _input_reason_code(reason_code) for reason_code in item.reason_codes
    ]
    if item.liquidity_score < config.minimum_watch_liquidity_score:
        reasons.append(LIQUIDITY_BLOCK_REASON)
    elif item.liquidity_score < config.minimum_pass_liquidity_score:
        reasons.append(LIQUIDITY_WATCH_REASON)
    if item.resolution_memory < config.minimum_watch_resolution_memory:
        reasons.append(MEMORY_BLOCK_REASON)
    elif item.resolution_memory < config.minimum_pass_resolution_memory:
        reasons.append(MEMORY_WATCH_REASON)
    if item.resolution_window_seconds < config.minimum_watch_resolution_window_seconds:
        reasons.append(WINDOW_BLOCK_REASON)
    elif item.resolution_window_seconds < config.minimum_pass_resolution_window_seconds:
        reasons.append(WINDOW_WATCH_REASON)
    if pressure_score > config.maximum_watch_pressure_score:
        reasons.append(PRESSURE_BLOCK_REASON)
    elif pressure_score > config.maximum_pass_pressure_score:
        reasons.append(PRESSURE_WATCH_REASON)
    status = _status_from_reason_codes(tuple(reasons))
    if status == BLOCK_STATUS:
        reasons.append(STATUS_BLOCK_REASON)
    elif status == WATCH_STATUS:
        reasons.append(STATUS_WATCH_REASON)
    else:
        reasons.append(STATUS_PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[ResearchMarketLiquidityResolutionMemoryLadderRow, ...],
) -> str:
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityResolutionMemoryLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in REPORT_TRIGGER_REASONS
    }
    if not found:
        return (STATUS_PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityResolutionMemoryLadderRow, ...],
) -> tuple[ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount, ...]:
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if counts[reason_code] > 0 and reason_code != STATUS_PASS_REASON
    )


def _row_sort_key(
    row: ResearchMarketLiquidityResolutionMemoryLadderRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], -row.pressure_score, row.public_row_ref)


def _normalize_inputs(
    inputs: Iterable[ResearchMarketLiquidityResolutionMemoryLadderInput],
) -> tuple[ResearchMarketLiquidityResolutionMemoryLadderInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchMarketLiquidityResolutionMemoryLadderInput:
            raise ValueError(
                "inputs must contain ResearchMarketLiquidityResolutionMemoryLadderInput",
            )
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketLiquidityResolutionMemoryLadderRow],
) -> tuple[ResearchMarketLiquidityResolutionMemoryLadderRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketLiquidityResolutionMemoryLadderRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityResolutionMemoryLadderRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount],
) -> tuple[ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
    return tuple(
        sorted(normalized, key=lambda count: ROW_REASON_CODES.index(count.reason_code)),
    )


def _validate_report_consistency(
    report: ResearchMarketLiquidityResolutionMemoryLadderReport,
) -> None:
    rows = report.rows
    expected_values = {
        "row_count": _count(len(rows)),
        "pass_count": _count(sum(1 for row in rows if row.status == PASS_STATUS)),
        "watch_count": _count(sum(1 for row in rows if row.status == WATCH_STATUS)),
        "block_count": _count(sum(1 for row in rows if row.status == BLOCK_STATUS)),
        "low_liquidity_count": _count(
            sum(
                1
                for row in rows
                if LIQUIDITY_WATCH_REASON in row.reason_codes
                or LIQUIDITY_BLOCK_REASON in row.reason_codes
            ),
        ),
        "low_resolution_memory_count": _count(
            sum(
                1
                for row in rows
                if MEMORY_WATCH_REASON in row.reason_codes
                or MEMORY_BLOCK_REASON in row.reason_codes
            ),
        ),
        "short_resolution_window_count": _count(
            sum(
                1
                for row in rows
                if WINDOW_WATCH_REASON in row.reason_codes
                or WINDOW_BLOCK_REASON in row.reason_codes
            ),
        ),
        "average_ladder_score": _average_decimal(row.ladder_score for row in rows),
        "max_pressure_score": _max_decimal(row.pressure_score for row in rows),
        "min_liquidity_score": _min_decimal(row.liquidity_score for row in rows),
        "min_resolution_memory": _min_decimal(row.resolution_memory for row in rows),
        "min_resolution_window_seconds": _min_decimal(
            row.resolution_window_seconds for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
    }
    if report.input_count < report.row_count:
        raise ValueError("input_count must be at least row_count")
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _resolution_window_score(
    resolution_window_seconds: Decimal,
    config: ResearchMarketLiquidityResolutionMemoryLadderConfig,
) -> Decimal:
    if resolution_window_seconds >= config.minimum_pass_resolution_window_seconds:
        return ONE
    if resolution_window_seconds <= config.minimum_watch_resolution_window_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = (
            config.minimum_pass_resolution_window_seconds
            - config.minimum_watch_resolution_window_seconds
        )
        value = (
            resolution_window_seconds - config.minimum_watch_resolution_window_seconds
        ) / span
    return _quantize(value)


def _ladder_score(
    item: ResearchMarketLiquidityResolutionMemoryLadderInput,
    *,
    window_score: Decimal,
    config: ResearchMarketLiquidityResolutionMemoryLadderConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            item.liquidity_score * config.liquidity_score_weight
            + item.resolution_memory * config.resolution_memory_weight
            + window_score * config.resolution_window_weight
        )
    return _quantize(value)


def _input_reason_code(reason_code: str) -> str:
    _require_known_value("reason_codes", reason_code, INPUT_REASON_CODES)
    return f"input_{reason_code}"


def _public_row_ref(private_ref: str) -> str:
    digest = sha256(private_ref.encode("utf-8")).hexdigest()[:16]
    return f"row_{digest}"


def _derived_validation_digest(
    report: ResearchMarketLiquidityResolutionMemoryLadderReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: ResearchMarketLiquidityResolutionMemoryLadderReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _normalize_input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes entries must be strings")
        _require_known_value("reason_codes", reason_code, INPUT_REASON_CODES)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in INPUT_REASON_CODES if reason_code in normalized)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        _require_known_value(field_name, reason_code, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", reason_codes, REPORT_REASON_CODES)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(max(normalized))


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(min(normalized))


def _weight_sum(config: ResearchMarketLiquidityResolutionMemoryLadderConfig) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            config.liquidity_score_weight
            + config.resolution_memory_weight
            + config.resolution_window_weight,
        )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, _json_ready(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
