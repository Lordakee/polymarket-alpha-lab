"""Pure report-only source-class assignment balance reducer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_SOURCE_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION = (
    "research-team-source-assignment-balance-report-v1"
)
ASSIGNMENT_BALANCE_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_DIGEST_LENGTH = 64
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_token",
    "bearer ",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "live",
    "exec" + "ution",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "reco" + "mmend",
    "siz" + "ing",
)


@dataclass(frozen=True)
class ResearchTeamSourceAssignmentBalanceConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_SOURCE_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION
    watch_utilization_ratio: Decimal = Decimal("0.750000")
    block_utilization_ratio: Decimal = Decimal("1.000000")
    watch_assignment_pressure: Decimal = Decimal("0.550000")
    block_assignment_pressure: Decimal = Decimal("0.850000")
    watch_coverage_strength: Decimal = Decimal("0.250000")
    block_coverage_strength: Decimal = Decimal("0.100000")
    low_source_reliability: Decimal = Decimal("0.600000")
    high_freshness_decay: Decimal = Decimal("0.700000")
    high_catalyst_pressure: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSourceAssignmentBalanceConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "watch_utilization_ratio",
            "block_utilization_ratio",
            "watch_assignment_pressure",
            "block_assignment_pressure",
            "watch_coverage_strength",
            "block_coverage_strength",
            "low_source_reliability",
            "high_freshness_decay",
            "high_catalyst_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_utilization_ratio > self.block_utilization_ratio:
            raise ValueError("watch_utilization_ratio must not exceed block_utilization_ratio")
        if self.watch_assignment_pressure > self.block_assignment_pressure:
            raise ValueError("watch_assignment_pressure must not exceed block_assignment_pressure")
        if self.block_coverage_strength > self.watch_coverage_strength:
            raise ValueError("block_coverage_strength must not exceed watch_coverage_strength")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSourceClassAssignment:
    team_id: str
    source_class_id: str
    assigned_load_units: Decimal
    aggregate_capacity_units: Decimal
    expertise_score: Decimal
    source_reliability: Decimal
    freshness_decay: Decimal
    catalyst_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSourceClassAssignment, "assignment")
        _require_public_code("team_id", self.team_id)
        _require_public_code("source_class_id", self.source_class_id)
        object.__setattr__(
            self,
            "assigned_load_units",
            _normalize_nonnegative_decimal("assigned_load_units", self.assigned_load_units),
        )
        object.__setattr__(
            self,
            "aggregate_capacity_units",
            _normalize_positive_decimal(
                "aggregate_capacity_units",
                self.aggregate_capacity_units,
            ),
        )
        for field_name in (
            "expertise_score",
            "source_reliability",
            "freshness_decay",
            "catalyst_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("assignment", self)


@dataclass(frozen=True)
class ResearchTeamSourceAssignmentBalanceRow:
    team_id: str
    source_class_id: str
    assigned_load_units: Decimal
    aggregate_capacity_units: Decimal
    utilization_ratio: Decimal
    expertise_score: Decimal
    source_reliability: Decimal
    freshness_decay: Decimal
    catalyst_pressure: Decimal
    coverage_strength: Decimal
    assignment_pressure: Decimal
    monitoring_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSourceAssignmentBalanceRow, "row")
        _require_public_code("team_id", self.team_id)
        _require_public_code("source_class_id", self.source_class_id)
        for field_name in (
            "assigned_load_units",
            "aggregate_capacity_units",
            "utilization_ratio",
            "expertise_score",
            "source_reliability",
            "freshness_decay",
            "catalyst_pressure",
            "coverage_strength",
            "assignment_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.aggregate_capacity_units <= ZERO:
            raise ValueError("aggregate_capacity_units must be greater than zero")
        for field_name in (
            "expertise_score",
            "source_reliability",
            "freshness_decay",
            "catalyst_pressure",
            "coverage_strength",
            "assignment_pressure",
        ):
            _require_unit_decimal(field_name, getattr(self, field_name))
        _require_status("monitoring_status", self.monitoring_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSourceAssignmentBalanceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSourceAssignmentBalanceReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSourceAssignmentBalanceReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    team_count: Decimal
    source_class_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_assigned_load_units: Decimal
    total_capacity_units: Decimal
    aggregate_utilization_ratio: Decimal
    max_assignment_pressure: Decimal
    min_coverage_strength: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSourceAssignmentBalanceReasonCodeCount, ...]
    rows: tuple[ResearchTeamSourceAssignmentBalanceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSourceAssignmentBalanceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "row_count",
            "team_count",
            "source_class_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_assigned_load_units",
            "total_capacity_units",
            "aggregate_utilization_ratio",
            "max_assignment_pressure",
            "min_coverage_strength",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
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
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_source_assignment_balance_report_payload(self)


def build_research_team_source_assignment_balance_report(
    assignments: object,
    *,
    config: ResearchTeamSourceAssignmentBalanceConfig,
    generated_at: datetime,
) -> ResearchTeamSourceAssignmentBalanceReport:
    if type(config) is not ResearchTeamSourceAssignmentBalanceConfig:
        raise ValueError("config must be a ResearchTeamSourceAssignmentBalanceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_assignments = _normalize_assignments(assignments)
    _validate_unique_assignments(normalized_assignments)
    rows = tuple(
        sorted(
            (
                _row_for_assignment(assignment, config=config)
                for assignment in normalized_assignments
            ),
            key=_row_key,
        ),
    )
    report_reason_codes = _report_reason_codes(rows)
    total_assigned = _sum_decimal(tuple(row.assigned_load_units for row in rows))
    total_capacity = _sum_decimal(tuple(row.aggregate_capacity_units for row in rows))
    return ResearchTeamSourceAssignmentBalanceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_count(len(rows)),
        team_count=_count(len({row.team_id for row in rows})),
        source_class_count=_count(len({row.source_class_id for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_assigned_load_units=total_assigned,
        total_capacity_units=total_capacity,
        aggregate_utilization_ratio=_ratio_or_zero(total_assigned, total_capacity),
        max_assignment_pressure=max(
            (row.assignment_pressure for row in rows),
            default=ZERO,
        ),
        min_coverage_strength=min((row.coverage_strength for row in rows), default=ZERO),
        report_status=_report_status(rows),
        reason_codes=report_reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_source_assignment_balance_report_payload(
    report: ResearchTeamSourceAssignmentBalanceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSourceAssignmentBalanceReport:
        raise ValueError("report must be a ResearchTeamSourceAssignmentBalanceReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_team_source_assignment_balance_report_payload(payload)
    return payload


def validate_research_team_source_assignment_balance_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload")
    return True


def _row_for_assignment(
    assignment: ResearchTeamSourceClassAssignment,
    *,
    config: ResearchTeamSourceAssignmentBalanceConfig,
) -> ResearchTeamSourceAssignmentBalanceRow:
    utilization_ratio = _ratio_or_zero(
        assignment.assigned_load_units,
        assignment.aggregate_capacity_units,
    )
    coverage_strength = _coverage_strength(assignment)
    assignment_pressure = _assignment_pressure(
        utilization_ratio=utilization_ratio,
        freshness_decay=assignment.freshness_decay,
        catalyst_pressure=assignment.catalyst_pressure,
    )
    monitoring_status = _monitoring_status(
        utilization_ratio=utilization_ratio,
        coverage_strength=coverage_strength,
        assignment_pressure=assignment_pressure,
        config=config,
    )
    return ResearchTeamSourceAssignmentBalanceRow(
        team_id=assignment.team_id,
        source_class_id=assignment.source_class_id,
        assigned_load_units=assignment.assigned_load_units,
        aggregate_capacity_units=assignment.aggregate_capacity_units,
        utilization_ratio=utilization_ratio,
        expertise_score=assignment.expertise_score,
        source_reliability=assignment.source_reliability,
        freshness_decay=assignment.freshness_decay,
        catalyst_pressure=assignment.catalyst_pressure,
        coverage_strength=coverage_strength,
        assignment_pressure=assignment_pressure,
        monitoring_status=monitoring_status,
        reason_codes=_row_reason_codes(
            utilization_ratio=utilization_ratio,
            coverage_strength=coverage_strength,
            assignment_pressure=assignment_pressure,
            source_reliability=assignment.source_reliability,
            freshness_decay=assignment.freshness_decay,
            catalyst_pressure=assignment.catalyst_pressure,
            monitoring_status=monitoring_status,
            config=config,
        ),
    )


def _coverage_strength(assignment: ResearchTeamSourceClassAssignment) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            assignment.expertise_score
            * assignment.source_reliability
            * (ONE - assignment.freshness_decay)
        )
    return _clamp_unit(_quantize(value))


def _assignment_pressure(
    *,
    utilization_ratio: Decimal,
    freshness_decay: Decimal,
    catalyst_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        capacity_component = min(utilization_ratio, ONE) * Decimal("0.550000")
        pressure_component = catalyst_pressure * Decimal("0.750000")
        freshness_component = freshness_decay * Decimal("0.215000")
        over_capacity_component = max(utilization_ratio - ONE, ZERO) * Decimal("0.390000")
    return _clamp_unit(
        _quantize(
            max(
                capacity_component,
                pressure_component + freshness_component + over_capacity_component,
            ),
        ),
    )


def _monitoring_status(
    *,
    utilization_ratio: Decimal,
    coverage_strength: Decimal,
    assignment_pressure: Decimal,
    config: ResearchTeamSourceAssignmentBalanceConfig,
) -> str:
    if (
        utilization_ratio >= config.block_utilization_ratio
        or assignment_pressure >= config.block_assignment_pressure
        or coverage_strength <= config.block_coverage_strength
    ):
        return "block"
    if (
        utilization_ratio >= config.watch_utilization_ratio
        or assignment_pressure >= config.watch_assignment_pressure
        or coverage_strength <= config.watch_coverage_strength
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    utilization_ratio: Decimal,
    coverage_strength: Decimal,
    assignment_pressure: Decimal,
    source_reliability: Decimal,
    freshness_decay: Decimal,
    catalyst_pressure: Decimal,
    monitoring_status: str,
    config: ResearchTeamSourceAssignmentBalanceConfig,
) -> tuple[str, ...]:
    reason_codes = [f"assignment_balance_{monitoring_status}"]
    if utilization_ratio >= config.block_utilization_ratio:
        reason_codes.append("aggregate_capacity_exceeded")
    elif utilization_ratio >= config.watch_utilization_ratio:
        reason_codes.append("aggregate_capacity_watch")
    if coverage_strength <= config.block_coverage_strength:
        reason_codes.append("coverage_strength_block")
    elif coverage_strength <= config.watch_coverage_strength:
        reason_codes.append("coverage_strength_watch")
    if assignment_pressure >= config.block_assignment_pressure:
        reason_codes.append("assignment_pressure_block")
    elif assignment_pressure >= config.watch_assignment_pressure:
        reason_codes.append("assignment_pressure_watch")
    if source_reliability <= config.low_source_reliability:
        reason_codes.append("source_reliability_low")
    if freshness_decay >= config.high_freshness_decay:
        reason_codes.append("freshness_decay_high")
    if catalyst_pressure >= config.high_catalyst_pressure:
        reason_codes.append("catalyst_pressure_high")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchTeamSourceAssignmentBalanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("assignment_balance_empty",)
    reason_codes = [_report_status(rows)]
    if reason_codes[0] == "pass":
        reason_codes[0] = "assignment_balance_report_pass"
    elif reason_codes[0] == "watch":
        reason_codes[0] = "assignment_balance_report_watch"
    else:
        reason_codes[0] = "assignment_balance_report_block"
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchTeamSourceAssignmentBalanceRow, ...]) -> str:
    if any(row.monitoring_status == "block" for row in rows):
        return "block"
    if any(row.monitoring_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamSourceAssignmentBalanceRow, ...],
) -> tuple[ResearchTeamSourceAssignmentBalanceReasonCodeCount, ...]:
    reason_codes = sorted({reason_code for row in rows for reason_code in row.reason_codes})
    return tuple(
        ResearchTeamSourceAssignmentBalanceReasonCodeCount(
            reason_code=reason_code,
            count=_count(
                sum(
                    1
                    for row in rows
                    if reason_code in row.reason_codes
                ),
            ),
        )
        for reason_code in reason_codes
    )


def _normalize_assignments(value: object) -> tuple[ResearchTeamSourceClassAssignment, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("assignments must be an iterable")
    try:
        assignments = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("assignments must be an iterable") from exc
    for item in assignments:
        if type(item) is not ResearchTeamSourceClassAssignment:
            raise ValueError(
                "assignments must contain ResearchTeamSourceClassAssignment values",
            )
        _require_hard_flags("assignment", item)
    return assignments


def _normalize_rows(value: object) -> tuple[ResearchTeamSourceAssignmentBalanceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSourceAssignmentBalanceRow:
            raise ValueError("rows must contain ResearchTeamSourceAssignmentBalanceRow values")
        _require_hard_flags("row", row)
    normalized = tuple(sorted(rows, key=_row_key))
    if rows != normalized:
        raise ValueError("rows must use deterministic sequence")
    _validate_unique_rows(rows)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSourceAssignmentBalanceReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchTeamSourceAssignmentBalanceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSourceAssignmentBalanceReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(count.reason_code)
    normalized = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != normalized:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _validate_unique_assignments(
    assignments: tuple[ResearchTeamSourceClassAssignment, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for assignment in assignments:
        key = (assignment.source_class_id, assignment.team_id)
        if key in seen:
            raise ValueError("assignments must be unique by team and source class")
        seen.add(key)


def _validate_unique_rows(rows: tuple[ResearchTeamSourceAssignmentBalanceRow, ...]) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = _row_key(row)
        if key in seen:
            raise ValueError("rows must be unique by team and source class")
        seen.add(key)


def _validate_report(report: ResearchTeamSourceAssignmentBalanceReport) -> None:
    _require_hard_flags("report", report)
    _validate_unique_rows(report.rows)
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.source_class_count != _count(
        len({row.source_class_id for row in report.rows}),
    ):
        raise ValueError("source_class_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.total_assigned_load_units != _sum_decimal(
        tuple(row.assigned_load_units for row in report.rows),
    ):
        raise ValueError("total_assigned_load_units must match rows")
    if report.total_capacity_units != _sum_decimal(
        tuple(row.aggregate_capacity_units for row in report.rows),
    ):
        raise ValueError("total_capacity_units must match rows")
    if report.aggregate_utilization_ratio != _ratio_or_zero(
        report.total_assigned_load_units,
        report.total_capacity_units,
    ):
        raise ValueError("aggregate_utilization_ratio must match totals")
    expected_max_pressure = max(
        (row.assignment_pressure for row in report.rows),
        default=ZERO,
    )
    if report.max_assignment_pressure != expected_max_pressure:
        raise ValueError("max_assignment_pressure must match rows")
    expected_min_coverage = min((row.coverage_strength for row in report.rows), default=ZERO)
    if report.min_coverage_strength != expected_min_coverage:
        raise ValueError("min_coverage_strength must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report")


def _row_key(row: ResearchTeamSourceAssignmentBalanceRow) -> tuple[str, str]:
    return (row.source_class_id, row.team_id)


def _status_count(
    rows: tuple[ResearchTeamSourceAssignmentBalanceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.monitoring_status == status))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    _require_unit_decimal(field_name, decimal_value)
    return decimal_value


def _require_unit_decimal(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_SOURCE_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    if not value:
        raise ValueError(f"{field_name} must be a public code")
    if any(fragment in value.lower() for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ASSIGNMENT_BALANCE_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload must be paper_only")
    if payload.get("report_only") is not True:
        raise ValueError("payload must be report_only")
    if payload.get("readonly") is not True:
        raise ValueError("payload must be readonly")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _report_public_payload_for_digest(
    report: ResearchTeamSourceAssignmentBalanceReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_derived_validation_digest(
    report: ResearchTeamSourceAssignmentBalanceReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public payload field")
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


__all__ = (
    "ASSIGNMENT_BALANCE_STATUSES",
    "DEFAULT_RESEARCH_TEAM_SOURCE_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION",
    "ResearchTeamSourceAssignmentBalanceConfig",
    "ResearchTeamSourceAssignmentBalanceReasonCodeCount",
    "ResearchTeamSourceAssignmentBalanceReport",
    "ResearchTeamSourceAssignmentBalanceRow",
    "ResearchTeamSourceClassAssignment",
    "build_research_team_source_assignment_balance_report",
    "research_team_source_assignment_balance_report_payload",
    "validate_research_team_source_assignment_balance_report_payload",
)
