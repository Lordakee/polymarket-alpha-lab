"""Pure public aggregate SLA priority report for research collection teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_SOURCE_COLLECTION_SLA_PRIORITY_CONFIG_VERSION = (
    "research-source-collection-sla-priority-v0"
)

STATUSES = ("pass", "watch", "block")
NO_TASKS_REASON = "research_source_collection_sla_priority_no_collection_tasks"
CLEAR_REASON = "research_source_collection_sla_priority_clear"
STALE_AGE_REASON = "research_source_collection_sla_priority_stale_source_age"
LOW_RELIABILITY_REASON = "research_source_collection_sla_priority_low_reliability"
COVERAGE_GAP_REASON = "research_source_collection_sla_priority_coverage_gap"
CATALYST_PRESSURE_REASON = "research_source_collection_sla_priority_catalyst_pressure"
CAPACITY_LIMITED_REASON = "research_source_collection_sla_priority_capacity_limited"
REASON_CODES = (
    NO_TASKS_REASON,
    STALE_AGE_REASON,
    LOW_RELIABILITY_REASON,
    COVERAGE_GAP_REASON,
    CATALYST_PRESSURE_REASON,
    CAPACITY_LIMITED_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {"block": Decimal("0.000000"), "watch": Decimal("1.000000"), "pass": Decimal("2.000000")}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
AGE_WEIGHT = Decimal("0.250000")
RELIABILITY_WEIGHT = Decimal("0.100000")
COVERAGE_WEIGHT = Decimal("0.250000")
CATALYST_WEIGHT = Decimal("0.200000")
CAPACITY_WEIGHT = Decimal("0.200000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    _join_parts("u", "r", "l"),
    _join_parts("te", "xt"),
    _join_parts("na", "me"),
    _join_parts("re", "f"),
    _join_parts("re", "fer", "ence"),
    _join_parts("source", "_", "id"),
)


@dataclass(frozen=True)
class ResearchSourceCollectionSlaPriorityConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_COLLECTION_SLA_PRIORITY_CONFIG_VERSION
    source_age_watch_seconds: Decimal = Decimal("3600.000000")
    source_age_block_seconds: Decimal = Decimal("7200.000000")
    reliability_watch_floor: Decimal = Decimal("0.800000")
    reliability_block_floor: Decimal = Decimal("0.600000")
    coverage_gap_watch_ratio: Decimal = Decimal("0.250000")
    coverage_gap_block_ratio: Decimal = Decimal("0.500000")
    catalyst_pressure_watch_ratio: Decimal = Decimal("0.500000")
    catalyst_pressure_block_ratio: Decimal = Decimal("0.850000")
    capacity_watch_ratio: Decimal = Decimal("0.750000")
    capacity_block_ratio: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_age_watch_seconds",
            "source_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_watch_floor",
            "reliability_block_floor",
            "coverage_gap_watch_ratio",
            "coverage_gap_block_ratio",
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
        if self.source_age_block_seconds < self.source_age_watch_seconds:
            raise ValueError("source_age_block_seconds must not be below watch seconds")
        if self.reliability_block_floor > self.reliability_watch_floor:
            raise ValueError("reliability_block_floor must not exceed watch floor")
        if self.coverage_gap_block_ratio < self.coverage_gap_watch_ratio:
            raise ValueError("coverage_gap_block_ratio must not be below watch ratio")
        if self.catalyst_pressure_block_ratio < self.catalyst_pressure_watch_ratio:
            raise ValueError("catalyst_pressure_block_ratio must not be below watch ratio")
        if self.capacity_block_ratio > self.capacity_watch_ratio:
            raise ValueError("capacity_block_ratio must not exceed watch ratio")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceCollectionSlaPriorityInput:
    team_id: str
    category_id: str
    collection_task_count: Decimal
    aggregate_source_age_seconds: Decimal
    reliability_score: Decimal
    expected_source_count: Decimal
    collected_source_count: Decimal
    catalyst_pressure_ratio: Decimal
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
        object.__setattr__(
            self,
            "collection_task_count",
            _require_positive_count("collection_task_count", self.collection_task_count),
        )
        for field_name in (
            "aggregate_source_age_seconds",
            "collected_source_count",
            "available_team_capacity_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_source_count",
            _require_positive_decimal("expected_source_count", self.expected_source_count),
        )
        object.__setattr__(
            self,
            "required_team_capacity_units",
            _require_positive_decimal(
                "required_team_capacity_units",
                self.required_team_capacity_units,
            ),
        )
        for field_name in ("reliability_score", "catalyst_pressure_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.collected_source_count > self.expected_source_count:
            raise ValueError("collected_source_count must not exceed expected_source_count")
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceCollectionSlaPriorityRow:
    team_id: str
    category_id: str
    collection_task_count: Decimal
    aggregate_source_age_seconds: Decimal
    reliability_score: Decimal
    expected_source_count: Decimal
    collected_source_count: Decimal
    coverage_gap_ratio: Decimal
    catalyst_pressure_ratio: Decimal
    team_capacity_ratio: Decimal
    priority_score: Decimal
    status: str
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
            "collection_task_count",
            "aggregate_source_age_seconds",
            "expected_source_count",
            "collected_source_count",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_score",
            "coverage_gap_ratio",
            "catalyst_pressure_ratio",
            "team_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("priority row", self)


@dataclass(frozen=True)
class ResearchSourceCollectionSlaPriorityReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    collection_task_count: Decimal
    block_team_count: Decimal
    watch_team_count: Decimal
    max_aggregate_source_age_seconds: Decimal
    min_reliability_score: Decimal
    max_coverage_gap_ratio: Decimal
    max_catalyst_pressure_ratio: Decimal
    min_team_capacity_ratio: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[ResearchSourceCollectionSlaPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "collection_task_count",
            "block_team_count",
            "watch_team_count",
            "max_aggregate_source_age_seconds",
            "average_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_reliability_score",
            "max_coverage_gap_ratio",
            "max_catalyst_pressure_ratio",
            "min_team_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "priority_rows", _normalize_priority_rows(self.priority_rows))
        _validate_report(self)
        _require_or_set_digest(self)
        require_paper_only_flags("report", self)


def build_research_source_collection_sla_priority_report(
    inputs: list[ResearchSourceCollectionSlaPriorityInput]
    | tuple[ResearchSourceCollectionSlaPriorityInput, ...],
    *,
    config: ResearchSourceCollectionSlaPriorityConfig,
    generated_at: datetime,
) -> ResearchSourceCollectionSlaPriorityReport:
    if type(config) is not ResearchSourceCollectionSlaPriorityConfig:
        raise ValueError("config must be a ResearchSourceCollectionSlaPriorityConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _priority_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceCollectionSlaPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len(rows)),
        collection_task_count=_sum_rows(rows, "collection_task_count"),
        block_team_count=_count(sum(row.status == "block" for row in rows)),
        watch_team_count=_count(sum(row.status == "watch" for row in rows)),
        max_aggregate_source_age_seconds=max(
            (row.aggregate_source_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        min_reliability_score=min(
            (row.reliability_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        max_coverage_gap_ratio=max(
            (row.coverage_gap_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        max_catalyst_pressure_ratio=max(
            (row.catalyst_pressure_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        min_team_capacity_ratio=min(
            (row.team_capacity_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        average_priority_score=_ratio(_sum_rows(rows, "priority_score"), _count(len(rows))),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        priority_rows=rows,
    )


def research_source_collection_sla_priority_report_payload(
    report: ResearchSourceCollectionSlaPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceCollectionSlaPriorityReport:
        raise ValueError("report must be a ResearchSourceCollectionSlaPriorityReport")
    require_paper_only_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceCollectionSlaPriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceCollectionSlaPriorityInput:
            raise ValueError(
                "inputs must contain ResearchSourceCollectionSlaPriorityInput",
            )
        require_paper_only_flags("input", row)
        key = (row.category_id, row.team_id)
        if key in seen:
            raise ValueError("inputs must be unique by team and category")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.category_id, row.team_id)))


def _priority_rows(
    rows: tuple[ResearchSourceCollectionSlaPriorityInput, ...],
    *,
    config: ResearchSourceCollectionSlaPriorityConfig,
) -> tuple[ResearchSourceCollectionSlaPriorityRow, ...]:
    return tuple(
        sorted(
            (_priority_row(row, config=config) for row in rows),
            key=_row_sort_key,
        ),
    )


def _priority_row(
    row: ResearchSourceCollectionSlaPriorityInput,
    *,
    config: ResearchSourceCollectionSlaPriorityConfig,
) -> ResearchSourceCollectionSlaPriorityRow:
    coverage_gap_ratio = _coverage_gap_ratio(row)
    team_capacity_ratio = _capacity_ratio(row)
    reason_codes = _row_reason_codes(
        row,
        coverage_gap_ratio=coverage_gap_ratio,
        team_capacity_ratio=team_capacity_ratio,
        config=config,
    )
    return ResearchSourceCollectionSlaPriorityRow(
        team_id=row.team_id,
        category_id=row.category_id,
        collection_task_count=row.collection_task_count,
        aggregate_source_age_seconds=row.aggregate_source_age_seconds,
        reliability_score=row.reliability_score,
        expected_source_count=row.expected_source_count,
        collected_source_count=row.collected_source_count,
        coverage_gap_ratio=coverage_gap_ratio,
        catalyst_pressure_ratio=row.catalyst_pressure_ratio,
        team_capacity_ratio=team_capacity_ratio,
        priority_score=_priority_score(
            aggregate_source_age_seconds=row.aggregate_source_age_seconds,
            source_age_block_seconds=config.source_age_block_seconds,
            reliability_score=row.reliability_score,
            coverage_gap_ratio=coverage_gap_ratio,
            catalyst_pressure_ratio=row.catalyst_pressure_ratio,
            team_capacity_ratio=team_capacity_ratio,
        ),
        status=_row_status(
            row,
            coverage_gap_ratio=coverage_gap_ratio,
            team_capacity_ratio=team_capacity_ratio,
            reason_codes=reason_codes,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _coverage_gap_ratio(row: ResearchSourceCollectionSlaPriorityInput) -> Decimal:
    return _ratio(row.expected_source_count - row.collected_source_count, row.expected_source_count)


def _capacity_ratio(row: ResearchSourceCollectionSlaPriorityInput) -> Decimal:
    return min(_ratio(row.available_team_capacity_units, row.required_team_capacity_units), ONE)


def _priority_score(
    *,
    aggregate_source_age_seconds: Decimal,
    source_age_block_seconds: Decimal,
    reliability_score: Decimal,
    coverage_gap_ratio: Decimal,
    catalyst_pressure_ratio: Decimal,
    team_capacity_ratio: Decimal,
) -> Decimal:
    age_pressure = min(_ratio(aggregate_source_age_seconds, source_age_block_seconds), ONE)
    reliability_gap = (ONE - reliability_score).quantize(QUANT)
    capacity_gap = (ONE - team_capacity_ratio).quantize(QUANT)
    with localcontext(DECIMAL_CONTEXT):
        return (
            age_pressure * AGE_WEIGHT
            + reliability_gap * RELIABILITY_WEIGHT
            + coverage_gap_ratio * COVERAGE_WEIGHT
            + catalyst_pressure_ratio * CATALYST_WEIGHT
            + capacity_gap * CAPACITY_WEIGHT
        ).quantize(QUANT)


def _row_reason_codes(
    row: ResearchSourceCollectionSlaPriorityInput,
    *,
    coverage_gap_ratio: Decimal,
    team_capacity_ratio: Decimal,
    config: ResearchSourceCollectionSlaPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.aggregate_source_age_seconds >= config.source_age_watch_seconds:
        reasons.append(STALE_AGE_REASON)
    if row.reliability_score <= config.reliability_watch_floor:
        reasons.append(LOW_RELIABILITY_REASON)
    if coverage_gap_ratio >= config.coverage_gap_watch_ratio:
        reasons.append(COVERAGE_GAP_REASON)
    if row.catalyst_pressure_ratio >= config.catalyst_pressure_watch_ratio:
        reasons.append(CATALYST_PRESSURE_REASON)
    if team_capacity_ratio <= config.capacity_watch_ratio:
        reasons.append(CAPACITY_LIMITED_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(
    row: ResearchSourceCollectionSlaPriorityInput,
    *,
    coverage_gap_ratio: Decimal,
    team_capacity_ratio: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchSourceCollectionSlaPriorityConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        row.aggregate_source_age_seconds >= config.source_age_block_seconds
        or row.reliability_score <= config.reliability_block_floor
        or coverage_gap_ratio >= config.coverage_gap_block_ratio
        or row.catalyst_pressure_ratio >= config.catalyst_pressure_block_ratio
        or team_capacity_ratio <= config.capacity_block_ratio
    ):
        return "block"
    return "watch"


def _row_status_is_consistent(row: ResearchSourceCollectionSlaPriorityRow) -> bool:
    if row.reason_codes == (CLEAR_REASON,):
        return row.status == "pass"
    return row.status in ("watch", "block")


def _row_sort_key(row: ResearchSourceCollectionSlaPriorityRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.priority_score,
        row.category_id,
        row.team_id,
    )


def _report_status(rows: tuple[ResearchSourceCollectionSlaPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceCollectionSlaPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_TASKS_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_TASKS_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _normalize_priority_rows(
    value: object,
) -> tuple[ResearchSourceCollectionSlaPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("priority_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str, str] | None = None
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceCollectionSlaPriorityRow:
            raise ValueError(
                "priority_rows must contain ResearchSourceCollectionSlaPriorityRow",
            )
        require_paper_only_flags("priority row", row)
        key = (row.category_id, row.team_id)
        if key in seen:
            raise ValueError("priority_rows must contain unique team and category pairs")
        seen.add(key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("priority_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_row(row: ResearchSourceCollectionSlaPriorityRow) -> None:
    if row.collected_source_count > row.expected_source_count:
        raise ValueError("collected_source_count must not exceed expected_source_count")
    if row.coverage_gap_ratio != _ratio(
        row.expected_source_count - row.collected_source_count,
        row.expected_source_count,
    ):
        raise ValueError("coverage_gap_ratio must match source counts")
    if not _row_status_is_consistent(row):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceCollectionSlaPriorityReport) -> None:
    if report.team_count != _count(len(report.priority_rows)):
        raise ValueError("team_count must match priority_rows")
    if report.collection_task_count != _sum_rows(report.priority_rows, "collection_task_count"):
        raise ValueError("collection_task_count must match priority_rows")
    if report.block_team_count != _count(sum(row.status == "block" for row in report.priority_rows)):
        raise ValueError("block_team_count must match priority_rows")
    if report.watch_team_count != _count(sum(row.status == "watch" for row in report.priority_rows)):
        raise ValueError("watch_team_count must match priority_rows")
    if report.max_aggregate_source_age_seconds != _max_rows(
        report.priority_rows,
        "aggregate_source_age_seconds",
    ):
        raise ValueError("max_aggregate_source_age_seconds must match priority_rows")
    if report.min_reliability_score != _min_rows(report.priority_rows, "reliability_score"):
        raise ValueError("min_reliability_score must match priority_rows")
    if report.max_coverage_gap_ratio != _max_rows(report.priority_rows, "coverage_gap_ratio"):
        raise ValueError("max_coverage_gap_ratio must match priority_rows")
    if report.max_catalyst_pressure_ratio != _max_rows(
        report.priority_rows,
        "catalyst_pressure_ratio",
    ):
        raise ValueError("max_catalyst_pressure_ratio must match priority_rows")
    if report.min_team_capacity_ratio != _min_rows(report.priority_rows, "team_capacity_ratio"):
        raise ValueError("min_team_capacity_ratio must match priority_rows")
    if report.average_priority_score != _ratio(
        _sum_rows(report.priority_rows, "priority_score"),
        _count(len(report.priority_rows)),
    ):
        raise ValueError("average_priority_score must match priority_rows")
    if report.reason_codes != _report_reason_codes(report.priority_rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.status != _report_status(report.priority_rows):
        raise ValueError("status must match priority_rows")


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


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
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


def _require_or_set_digest(report: ResearchSourceCollectionSlaPriorityReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchSourceCollectionSlaPriorityReport) -> str:
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
    "DEFAULT_RESEARCH_SOURCE_COLLECTION_SLA_PRIORITY_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceCollectionSlaPriorityConfig",
    "ResearchSourceCollectionSlaPriorityInput",
    "ResearchSourceCollectionSlaPriorityReport",
    "ResearchSourceCollectionSlaPriorityRow",
    "build_research_source_collection_sla_priority_report",
    "research_source_collection_sla_priority_report_payload",
)
