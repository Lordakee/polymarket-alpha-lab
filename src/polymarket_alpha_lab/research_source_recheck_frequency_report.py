"""Pure public aggregate source recheck frequency report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_SOURCE_RECHECK_FREQUENCY_CONFIG_VERSION = (
    "research-source-recheck-frequency-v0"
)

STATUSES = ("pass", "watch", "block")
NO_INPUTS_REASON = "research_source_recheck_frequency_no_public_aggregate_inputs"
CLEAR_REASON = "research_source_recheck_frequency_clear"
STALE_AGE_REASON = "research_source_recheck_frequency_stale_source_age"
LOW_RELIABILITY_REASON = "research_source_recheck_frequency_reliability_memory_low"
CATALYST_PRESSURE_REASON = "research_source_recheck_frequency_catalyst_pressure"
CONTRADICTION_COUNT_REASON = "research_source_recheck_frequency_contradiction_count"
CAPACITY_LIMITED_REASON = "research_source_recheck_frequency_capacity_limited"
REASON_CODES = (
    NO_INPUTS_REASON,
    STALE_AGE_REASON,
    LOW_RELIABILITY_REASON,
    CATALYST_PRESSURE_REASON,
    CONTRADICTION_COUNT_REASON,
    CAPACITY_LIMITED_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

PASS_RECHECK_FREQUENCY_BAND = "pass_24h"
WATCH_RECHECK_FREQUENCY_BAND = "watch_6h"
BLOCK_RECHECK_FREQUENCY_BAND = "block_1h"
RECHECK_FREQUENCY_BANDS = (
    PASS_RECHECK_FREQUENCY_BAND,
    WATCH_RECHECK_FREQUENCY_BAND,
    BLOCK_RECHECK_FREQUENCY_BAND,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
AGE_WEIGHT = Decimal("0.250000")
RELIABILITY_WEIGHT = Decimal("0.200000")
CATALYST_WEIGHT = Decimal("0.200000")
CONTRADICTION_WEIGHT = Decimal("0.150000")
CAPACITY_WEIGHT = Decimal("0.200000")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_source",
    "source_id",
    "source_name",
    "source_text",
    "source_url",
    "source_ref",
    "source_reference",
    "url",
)


@dataclass(frozen=True)
class ResearchSourceRecheckFrequencyConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_RECHECK_FREQUENCY_CONFIG_VERSION
    source_age_watch_seconds: Decimal = Decimal("3600.000000")
    source_age_block_seconds: Decimal = Decimal("10800.000000")
    reliability_memory_watch_floor: Decimal = Decimal("0.800000")
    reliability_memory_block_floor: Decimal = Decimal("0.600000")
    catalyst_pressure_watch_ratio: Decimal = Decimal("0.500000")
    catalyst_pressure_block_ratio: Decimal = Decimal("0.850000")
    contradiction_watch_count: Decimal = Decimal("2.000000")
    contradiction_block_count: Decimal = Decimal("5.000000")
    capacity_watch_ratio: Decimal = Decimal("0.750000")
    capacity_block_ratio: Decimal = Decimal("0.400000")
    pass_recheck_frequency_seconds: Decimal = Decimal("86400.000000")
    watch_recheck_frequency_seconds: Decimal = Decimal("21600.000000")
    block_recheck_frequency_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_age_watch_seconds",
            "source_age_block_seconds",
            "pass_recheck_frequency_seconds",
            "watch_recheck_frequency_seconds",
            "block_recheck_frequency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_memory_watch_floor",
            "reliability_memory_block_floor",
            "catalyst_pressure_watch_ratio",
            "catalyst_pressure_block_ratio",
            "capacity_watch_ratio",
            "capacity_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("contradiction_watch_count", "contradiction_block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.source_age_block_seconds <= self.source_age_watch_seconds:
            raise ValueError("source_age_block_seconds must exceed source_age_watch_seconds")
        if self.reliability_memory_block_floor >= self.reliability_memory_watch_floor:
            raise ValueError(
                "reliability_memory_block_floor must be below "
                "reliability_memory_watch_floor",
            )
        if self.catalyst_pressure_block_ratio <= self.catalyst_pressure_watch_ratio:
            raise ValueError(
                "catalyst_pressure_block_ratio must exceed catalyst_pressure_watch_ratio",
            )
        if self.contradiction_block_count <= self.contradiction_watch_count:
            raise ValueError(
                "contradiction_block_count must exceed contradiction_watch_count",
            )
        if self.capacity_block_ratio >= self.capacity_watch_ratio:
            raise ValueError("capacity_block_ratio must be below capacity_watch_ratio")
        if self.watch_recheck_frequency_seconds >= self.pass_recheck_frequency_seconds:
            raise ValueError(
                "watch_recheck_frequency_seconds must be below "
                "pass_recheck_frequency_seconds",
            )
        if self.block_recheck_frequency_seconds >= self.watch_recheck_frequency_seconds:
            raise ValueError(
                "block_recheck_frequency_seconds must be below "
                "watch_recheck_frequency_seconds",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceRecheckFrequencyInput:
    team_id: str
    category_id: str
    aggregate_source_age_seconds: Decimal
    reliability_memory_score: Decimal
    catalyst_pressure_ratio: Decimal
    contradiction_count: Decimal
    available_team_capacity_units: Decimal
    required_team_capacity_units: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        for field_name in (
            "aggregate_source_age_seconds",
            "available_team_capacity_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("reliability_memory_score", "catalyst_pressure_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_whole_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "required_team_capacity_units",
            _require_positive_decimal(
                "required_team_capacity_units",
                self.required_team_capacity_units,
            ),
        )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceRecheckFrequencyRow:
    team_id: str
    category_id: str
    aggregate_source_age_seconds: Decimal
    reliability_memory_score: Decimal
    catalyst_pressure_ratio: Decimal
    contradiction_count: Decimal
    team_capacity_ratio: Decimal
    recheck_pressure_score: Decimal
    status: str
    recheck_frequency_band: str
    recheck_frequency_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        for field_name in (
            "aggregate_source_age_seconds",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name))
                if field_name == "contradiction_count"
                else _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_memory_score",
            "catalyst_pressure_ratio",
            "team_capacity_ratio",
            "recheck_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_frequency_band("recheck_frequency_band", self.recheck_frequency_band)
        object.__setattr__(
            self,
            "recheck_frequency_seconds",
            _require_positive_decimal(
                "recheck_frequency_seconds",
                self.recheck_frequency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceRecheckFrequencyReport:
    generated_at: datetime
    config_version: str
    team_category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_aggregate_source_age_seconds: Decimal
    min_reliability_memory_score: Decimal
    max_catalyst_pressure_ratio: Decimal
    max_contradiction_count: Decimal
    min_team_capacity_ratio: Decimal
    average_recheck_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceRecheckFrequencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_category_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_aggregate_source_age_seconds",
            "max_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_reliability_memory_score",
            "max_catalyst_pressure_ratio",
            "min_team_capacity_ratio",
            "average_recheck_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("report", self)
        _validate_report(self)
        _require_or_set_digest(self)


def build_research_source_recheck_frequency_report(
    input_rows: list[ResearchSourceRecheckFrequencyInput]
    | tuple[ResearchSourceRecheckFrequencyInput, ...],
    *,
    config: ResearchSourceRecheckFrequencyConfig,
    generated_at: datetime,
) -> ResearchSourceRecheckFrequencyReport:
    if type(config) is not ResearchSourceRecheckFrequencyConfig:
        raise ValueError("config must be a ResearchSourceRecheckFrequencyConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _build_rows(_normalize_input_rows(input_rows), config=config)
    return ResearchSourceRecheckFrequencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_category_count=_count(len(rows)),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        max_aggregate_source_age_seconds=_max_rows(
            rows,
            "aggregate_source_age_seconds",
        ),
        min_reliability_memory_score=_min_rows(rows, "reliability_memory_score"),
        max_catalyst_pressure_ratio=_max_rows(rows, "catalyst_pressure_ratio"),
        max_contradiction_count=_max_rows(rows, "contradiction_count"),
        min_team_capacity_ratio=_min_rows(rows, "team_capacity_ratio"),
        average_recheck_pressure_score=_ratio(
            _sum_rows(rows, "recheck_pressure_score"),
            _count(len(rows)),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_recheck_frequency_report_payload(
    report: ResearchSourceRecheckFrequencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceRecheckFrequencyReport:
        raise ValueError("report must be a ResearchSourceRecheckFrequencyReport")
    require_paper_only_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def _normalize_input_rows(
    value: object,
) -> tuple[ResearchSourceRecheckFrequencyInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceRecheckFrequencyInput:
            raise ValueError("input rows must contain ResearchSourceRecheckFrequencyInput")
        require_paper_only_flags("input row", row)
        key = (row.category_id, row.team_id)
        if key in seen:
            raise ValueError("input rows must be unique by team and category")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.category_id, row.team_id)))


def _build_rows(
    rows: tuple[ResearchSourceRecheckFrequencyInput, ...],
    *,
    config: ResearchSourceRecheckFrequencyConfig,
) -> tuple[ResearchSourceRecheckFrequencyRow, ...]:
    return tuple(sorted((_build_row(row, config=config) for row in rows), key=_row_sort_key))


def _build_row(
    row: ResearchSourceRecheckFrequencyInput,
    *,
    config: ResearchSourceRecheckFrequencyConfig,
) -> ResearchSourceRecheckFrequencyRow:
    team_capacity_ratio = _capacity_ratio(row)
    reason_codes = _row_reason_codes(
        row,
        team_capacity_ratio=team_capacity_ratio,
        config=config,
    )
    status = _row_status(
        row,
        team_capacity_ratio=team_capacity_ratio,
        reason_codes=reason_codes,
        config=config,
    )
    return ResearchSourceRecheckFrequencyRow(
        team_id=row.team_id,
        category_id=row.category_id,
        aggregate_source_age_seconds=row.aggregate_source_age_seconds,
        reliability_memory_score=row.reliability_memory_score,
        catalyst_pressure_ratio=row.catalyst_pressure_ratio,
        contradiction_count=row.contradiction_count,
        team_capacity_ratio=team_capacity_ratio,
        recheck_pressure_score=_recheck_pressure_score(
            row,
            team_capacity_ratio=team_capacity_ratio,
            config=config,
        ),
        status=status,
        recheck_frequency_band=_frequency_band(status),
        recheck_frequency_seconds=_frequency_seconds(status, config),
        reason_codes=reason_codes,
    )


def _capacity_ratio(row: ResearchSourceRecheckFrequencyInput) -> Decimal:
    return min(
        _ratio(row.available_team_capacity_units, row.required_team_capacity_units),
        ONE,
    )


def _recheck_pressure_score(
    row: ResearchSourceRecheckFrequencyInput,
    *,
    team_capacity_ratio: Decimal,
    config: ResearchSourceRecheckFrequencyConfig,
) -> Decimal:
    age_pressure = min(
        _ratio(row.aggregate_source_age_seconds, config.source_age_block_seconds),
        ONE,
    )
    reliability_gap = (ONE - row.reliability_memory_score).quantize(QUANT)
    contradiction_pressure = min(
        _ratio(row.contradiction_count, config.contradiction_block_count),
        ONE,
    )
    capacity_gap = (ONE - team_capacity_ratio).quantize(QUANT)
    with localcontext(DECIMAL_CONTEXT):
        return (
            age_pressure * AGE_WEIGHT
            + reliability_gap * RELIABILITY_WEIGHT
            + row.catalyst_pressure_ratio * CATALYST_WEIGHT
            + contradiction_pressure * CONTRADICTION_WEIGHT
            + capacity_gap * CAPACITY_WEIGHT
        ).quantize(QUANT)


def _row_reason_codes(
    row: ResearchSourceRecheckFrequencyInput,
    *,
    team_capacity_ratio: Decimal,
    config: ResearchSourceRecheckFrequencyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.aggregate_source_age_seconds >= config.source_age_watch_seconds:
        reasons.append(STALE_AGE_REASON)
    if row.reliability_memory_score <= config.reliability_memory_watch_floor:
        reasons.append(LOW_RELIABILITY_REASON)
    if row.catalyst_pressure_ratio >= config.catalyst_pressure_watch_ratio:
        reasons.append(CATALYST_PRESSURE_REASON)
    if row.contradiction_count >= config.contradiction_watch_count:
        reasons.append(CONTRADICTION_COUNT_REASON)
    if team_capacity_ratio <= config.capacity_watch_ratio:
        reasons.append(CAPACITY_LIMITED_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(
    row: ResearchSourceRecheckFrequencyInput,
    *,
    team_capacity_ratio: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchSourceRecheckFrequencyConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        row.aggregate_source_age_seconds >= config.source_age_block_seconds
        or row.reliability_memory_score <= config.reliability_memory_block_floor
        or row.catalyst_pressure_ratio >= config.catalyst_pressure_block_ratio
        or row.contradiction_count >= config.contradiction_block_count
        or team_capacity_ratio <= config.capacity_block_ratio
    ):
        return "block"
    return "watch"


def _frequency_band(status: str) -> str:
    if status == "block":
        return BLOCK_RECHECK_FREQUENCY_BAND
    if status == "watch":
        return WATCH_RECHECK_FREQUENCY_BAND
    if status == "pass":
        return PASS_RECHECK_FREQUENCY_BAND
    raise ValueError("status must be pass, watch, or block")


def _frequency_seconds(
    status: str,
    config: ResearchSourceRecheckFrequencyConfig,
) -> Decimal:
    if status == "block":
        return config.block_recheck_frequency_seconds
    if status == "watch":
        return config.watch_recheck_frequency_seconds
    if status == "pass":
        return config.pass_recheck_frequency_seconds
    raise ValueError("status must be pass, watch, or block")


def _row_sort_key(
    row: ResearchSourceRecheckFrequencyRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.recheck_pressure_score,
        row.category_id,
        row.team_id,
    )


def _report_status(rows: tuple[ResearchSourceRecheckFrequencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceRecheckFrequencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_INPUTS_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceRecheckFrequencyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str, str] | None = None
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceRecheckFrequencyRow:
            raise ValueError("rows must contain ResearchSourceRecheckFrequencyRow")
        require_paper_only_flags("row", row)
        key = (row.category_id, row.team_id)
        if key in seen:
            raise ValueError("rows must contain unique team and category pairs")
        seen.add(key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_row(row: ResearchSourceRecheckFrequencyRow) -> None:
    if row.reason_codes == (CLEAR_REASON,):
        if row.status != "pass":
            raise ValueError("status must match reason_codes")
    elif row.status == "pass":
        raise ValueError("status must match reason_codes")
    if row.recheck_frequency_band != _frequency_band(row.status):
        raise ValueError("recheck_frequency_band must match status")


def _validate_report(report: ResearchSourceRecheckFrequencyReport) -> None:
    if report.team_category_count != _count(len(report.rows)):
        raise ValueError("team_category_count must match rows")
    if report.pass_count != _count(sum(row.status == "pass" for row in report.rows)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(row.status == "watch" for row in report.rows)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(row.status == "block" for row in report.rows)):
        raise ValueError("block_count must match rows")
    if report.max_aggregate_source_age_seconds != _max_rows(
        report.rows,
        "aggregate_source_age_seconds",
    ):
        raise ValueError("max_aggregate_source_age_seconds must match rows")
    if report.min_reliability_memory_score != _min_rows(
        report.rows,
        "reliability_memory_score",
    ):
        raise ValueError("min_reliability_memory_score must match rows")
    if report.max_catalyst_pressure_ratio != _max_rows(
        report.rows,
        "catalyst_pressure_ratio",
    ):
        raise ValueError("max_catalyst_pressure_ratio must match rows")
    if report.max_contradiction_count != _max_rows(report.rows, "contradiction_count"):
        raise ValueError("max_contradiction_count must match rows")
    if report.min_team_capacity_ratio != _min_rows(report.rows, "team_capacity_ratio"):
        raise ValueError("min_team_capacity_ratio must match rows")
    if report.average_recheck_pressure_score != _ratio(
        _sum_rows(report.rows, "recheck_pressure_score"),
        _count(len(report.rows)),
    ):
        raise ValueError("average_recheck_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return _require_nonnegative_decimal(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _max_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_frequency_band(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RECHECK_FREQUENCY_BANDS:
        raise ValueError(f"{field_name} must be a known recheck frequency band")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        index = REASON_CODES.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        previous_index = index
        seen.add(reason_code)
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_or_set_digest(report: ResearchSourceRecheckFrequencyReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchSourceRecheckFrequencyReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
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


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str) and value.lower().startswith(("http://", "https://")):
        raise ValueError("public payload contains unsafe value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RECHECK_FREQUENCY_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceRecheckFrequencyConfig",
    "ResearchSourceRecheckFrequencyInput",
    "ResearchSourceRecheckFrequencyReport",
    "ResearchSourceRecheckFrequencyRow",
    "build_research_source_recheck_frequency_report",
    "research_source_recheck_frequency_report_payload",
)
