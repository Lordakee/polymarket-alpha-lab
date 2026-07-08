"""Pure report-only research lane assignment balance reducer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION = (
    "research-team-domain-assignment-balance-report-v1"
)
DOMAIN_ASSIGNMENT_BALANCE_STATUSES = ("pass", "watch", "block")
RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES = (
    "politics",
    "macro",
    "crypto",
    "equity_index",
    "precious_metals",
    "soccer",
    "basketball",
    "baseball",
    "tennis",
)

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
    "data" + "base",
    "net" + "work",
    "requ" + "ests",
    "url" + "lib",
    "sock" + "et",
    "sql" + "ite",
    "market_" + "slug",
    "market_" + "question",
    "event_" + "id",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "reco" + "mmend",
    "siz" + "ing",
)


@dataclass(frozen=True)
class ResearchTeamDomainAssignmentBalanceConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_DOMAIN_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION
    watch_review_load_ratio: Decimal = Decimal("0.750000")
    block_review_load_ratio: Decimal = Decimal("1.000000")
    watch_stale_memory_ratio: Decimal = Decimal("0.500000")
    block_stale_memory_ratio: Decimal = Decimal("0.800000")
    watch_coverage_gap_ratio: Decimal = Decimal("0.150000")
    block_coverage_gap_ratio: Decimal = Decimal("0.400000")
    watch_escalation_pressure: Decimal = Decimal("0.550000")
    block_escalation_pressure: Decimal = Decimal("0.850000")
    review_load_weight: Decimal = Decimal("0.400000")
    stale_memory_weight: Decimal = Decimal("0.300000")
    coverage_gap_weight: Decimal = Decimal("0.200000")
    escalation_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainAssignmentBalanceConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "watch_review_load_ratio",
            "block_review_load_ratio",
            "watch_stale_memory_ratio",
            "block_stale_memory_ratio",
            "watch_coverage_gap_ratio",
            "block_coverage_gap_ratio",
            "watch_escalation_pressure",
            "block_escalation_pressure",
            "review_load_weight",
            "stale_memory_weight",
            "coverage_gap_weight",
            "escalation_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_review_load_ratio > self.block_review_load_ratio:
            raise ValueError("watch_review_load_ratio must not exceed block_review_load_ratio")
        if self.watch_stale_memory_ratio > self.block_stale_memory_ratio:
            raise ValueError("watch_stale_memory_ratio must not exceed block_stale_memory_ratio")
        if self.watch_coverage_gap_ratio > self.block_coverage_gap_ratio:
            raise ValueError("watch_coverage_gap_ratio must not exceed block_coverage_gap_ratio")
        if self.watch_escalation_pressure > self.block_escalation_pressure:
            raise ValueError(
                "watch_escalation_pressure must not exceed block_escalation_pressure",
            )
        weight_sum = _sum_decimal(
            (
                self.review_load_weight,
                self.stale_memory_weight,
                self.coverage_gap_weight,
                self.escalation_pressure_weight,
            ),
        )
        if weight_sum != ONE:
            raise ValueError("assignment pressure weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainAssignment:
    team_id: str
    research_lane: str
    assigned_researchers: Decimal
    active_review_load: Decimal
    review_capacity: Decimal
    fresh_memory_items: Decimal
    stale_memory_items: Decimal
    covered_topic_count: Decimal
    required_topic_count: Decimal
    escalation_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainAssignment, "assignment")
        _require_public_code("team_id", self.team_id)
        _require_research_lane(self.research_lane)
        for field_name in (
            "assigned_researchers",
            "active_review_load",
            "fresh_memory_items",
            "stale_memory_items",
            "covered_topic_count",
            "required_topic_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_capacity",
            _normalize_positive_decimal("review_capacity", self.review_capacity),
        )
        object.__setattr__(
            self,
            "escalation_pressure",
            _normalize_unit_decimal("escalation_pressure", self.escalation_pressure),
        )
        _require_hard_flags("assignment", self)


@dataclass(frozen=True)
class ResearchTeamDomainAssignmentBalanceRow:
    research_lane: str
    team_count: Decimal
    assigned_researchers: Decimal
    active_review_load: Decimal
    review_capacity: Decimal
    review_load_ratio: Decimal
    fresh_memory_items: Decimal
    stale_memory_items: Decimal
    stale_memory_ratio: Decimal
    covered_topic_count: Decimal
    required_topic_count: Decimal
    coverage_gap_count: Decimal
    coverage_gap_ratio: Decimal
    escalation_pressure: Decimal
    assignment_pressure: Decimal
    balance_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainAssignmentBalanceRow, "row")
        _require_research_lane(self.research_lane)
        for field_name in (
            "team_count",
            "assigned_researchers",
            "active_review_load",
            "review_capacity",
            "review_load_ratio",
            "fresh_memory_items",
            "stale_memory_items",
            "stale_memory_ratio",
            "covered_topic_count",
            "required_topic_count",
            "coverage_gap_count",
            "coverage_gap_ratio",
            "escalation_pressure",
            "assignment_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.review_capacity <= ZERO:
            raise ValueError("review_capacity must be greater than zero")
        for field_name in (
            "stale_memory_ratio",
            "coverage_gap_ratio",
            "escalation_pressure",
            "assignment_pressure",
        ):
            _require_unit_decimal(field_name, getattr(self, field_name))
        _require_status("balance_status", self.balance_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainAssignmentBalanceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainAssignmentBalanceReasonCodeCount,
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
class ResearchTeamDomainAssignmentBalanceReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    team_count: Decimal
    research_lane_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_assigned_researchers: Decimal
    total_active_review_load: Decimal
    total_review_capacity: Decimal
    aggregate_review_load_ratio: Decimal
    max_stale_memory_ratio: Decimal
    max_coverage_gap_ratio: Decimal
    max_escalation_pressure: Decimal
    max_assignment_pressure: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainAssignmentBalanceReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainAssignmentBalanceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainAssignmentBalanceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "row_count",
            "team_count",
            "research_lane_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_assigned_researchers",
            "total_active_review_load",
            "total_review_capacity",
            "aggregate_review_load_ratio",
            "max_stale_memory_ratio",
            "max_coverage_gap_ratio",
            "max_escalation_pressure",
            "max_assignment_pressure",
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
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report")
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_assignment_balance_report_payload(self)


def build_research_team_domain_assignment_balance_report(
    assignments: object,
    *,
    generated_at: datetime,
    config: ResearchTeamDomainAssignmentBalanceConfig,
) -> ResearchTeamDomainAssignmentBalanceReport:
    if type(config) is not ResearchTeamDomainAssignmentBalanceConfig:
        raise ValueError("config must be a ResearchTeamDomainAssignmentBalanceConfig")
    _require_hard_flags("config", config)
    rows = _rows_for_assignments(_normalize_assignments(assignments), config=config)
    total_load = _sum_decimal(tuple(row.active_review_load for row in rows))
    total_capacity = _sum_decimal(tuple(row.review_capacity for row in rows))
    report_reason_codes = _report_reason_codes(rows)
    return ResearchTeamDomainAssignmentBalanceReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        row_count=_count(len(rows)),
        team_count=_sum_decimal(tuple(row.team_count for row in rows)),
        research_lane_count=_count(len({row.research_lane for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_assigned_researchers=_sum_decimal(
            tuple(row.assigned_researchers for row in rows),
        ),
        total_active_review_load=total_load,
        total_review_capacity=total_capacity,
        aggregate_review_load_ratio=_ratio_or_zero(total_load, total_capacity),
        max_stale_memory_ratio=max((row.stale_memory_ratio for row in rows), default=ZERO),
        max_coverage_gap_ratio=max((row.coverage_gap_ratio for row in rows), default=ZERO),
        max_escalation_pressure=max((row.escalation_pressure for row in rows), default=ZERO),
        max_assignment_pressure=max((row.assignment_pressure for row in rows), default=ZERO),
        report_status=_report_status(rows),
        reason_codes=report_reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_assignment_balance_report_payload(
    report: ResearchTeamDomainAssignmentBalanceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamDomainAssignmentBalanceReport:
        raise ValueError("report must be a ResearchTeamDomainAssignmentBalanceReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_team_domain_assignment_balance_report_payload(payload)
    return payload


def validate_research_team_domain_assignment_balance_report_payload(
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


def _rows_for_assignments(
    assignments: tuple[ResearchTeamDomainAssignment, ...],
    *,
    config: ResearchTeamDomainAssignmentBalanceConfig,
) -> tuple[ResearchTeamDomainAssignmentBalanceRow, ...]:
    grouped: dict[str, list[ResearchTeamDomainAssignment]] = {
        research_lane: [] for research_lane in RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES
    }
    for assignment in assignments:
        grouped[assignment.research_lane].append(assignment)
    rows = tuple(
        _row_for_research_lane(research_lane, tuple(grouped[research_lane]), config=config)
        for research_lane in RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES
        if grouped[research_lane]
    )
    return rows


def _row_for_research_lane(
    research_lane: str,
    assignments: tuple[ResearchTeamDomainAssignment, ...],
    *,
    config: ResearchTeamDomainAssignmentBalanceConfig,
) -> ResearchTeamDomainAssignmentBalanceRow:
    assigned = _sum_decimal(tuple(item.assigned_researchers for item in assignments))
    active_load = _sum_decimal(tuple(item.active_review_load for item in assignments))
    capacity = _sum_decimal(tuple(item.review_capacity for item in assignments))
    fresh_memory = _sum_decimal(tuple(item.fresh_memory_items for item in assignments))
    stale_memory = _sum_decimal(tuple(item.stale_memory_items for item in assignments))
    covered_topics = _sum_decimal(tuple(item.covered_topic_count for item in assignments))
    required_topics = _sum_decimal(tuple(item.required_topic_count for item in assignments))
    review_load_ratio = _ratio_or_zero(active_load, capacity)
    stale_memory_ratio = _ratio_or_zero(stale_memory, fresh_memory + stale_memory)
    coverage_gap_count = _quantize(max(required_topics - covered_topics, ZERO))
    coverage_gap_ratio = _ratio_or_zero(coverage_gap_count, required_topics)
    escalation_pressure = max(
        (item.escalation_pressure for item in assignments),
        default=ZERO,
    )
    assignment_pressure = _assignment_pressure(
        review_load_ratio=review_load_ratio,
        stale_memory_ratio=stale_memory_ratio,
        coverage_gap_ratio=coverage_gap_ratio,
        escalation_pressure=escalation_pressure,
        config=config,
    )
    balance_status = _balance_status(
        review_load_ratio=review_load_ratio,
        stale_memory_ratio=stale_memory_ratio,
        coverage_gap_ratio=coverage_gap_ratio,
        escalation_pressure=escalation_pressure,
        assignment_pressure=assignment_pressure,
        config=config,
    )
    return ResearchTeamDomainAssignmentBalanceRow(
        research_lane=research_lane,
        team_count=_count(len({item.team_id for item in assignments})),
        assigned_researchers=assigned,
        active_review_load=active_load,
        review_capacity=capacity,
        review_load_ratio=review_load_ratio,
        fresh_memory_items=fresh_memory,
        stale_memory_items=stale_memory,
        stale_memory_ratio=stale_memory_ratio,
        covered_topic_count=covered_topics,
        required_topic_count=required_topics,
        coverage_gap_count=coverage_gap_count,
        coverage_gap_ratio=coverage_gap_ratio,
        escalation_pressure=escalation_pressure,
        assignment_pressure=assignment_pressure,
        balance_status=balance_status,
        reason_codes=_row_reason_codes(
            review_load_ratio=review_load_ratio,
            stale_memory_ratio=stale_memory_ratio,
            coverage_gap_ratio=coverage_gap_ratio,
            escalation_pressure=escalation_pressure,
            assignment_pressure=assignment_pressure,
            balance_status=balance_status,
            config=config,
        ),
    )


def _assignment_pressure(
    *,
    review_load_ratio: Decimal,
    stale_memory_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    escalation_pressure: Decimal,
    config: ResearchTeamDomainAssignmentBalanceConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        composite = (
            min(review_load_ratio, ONE) * config.review_load_weight
            + stale_memory_ratio * config.stale_memory_weight
            + coverage_gap_ratio * config.coverage_gap_weight
            + escalation_pressure * config.escalation_pressure_weight
        )
        review_memory_floor = (
            min(review_load_ratio, ONE) * Decimal("0.500000")
            + stale_memory_ratio * Decimal("0.200000")
        )
    return _clamp_unit(_quantize(max(composite, review_memory_floor)))


def _balance_status(
    *,
    review_load_ratio: Decimal,
    stale_memory_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    escalation_pressure: Decimal,
    assignment_pressure: Decimal,
    config: ResearchTeamDomainAssignmentBalanceConfig,
) -> str:
    if (
        review_load_ratio >= config.block_review_load_ratio
        or stale_memory_ratio >= config.block_stale_memory_ratio
        or coverage_gap_ratio >= config.block_coverage_gap_ratio
        or escalation_pressure >= config.block_escalation_pressure
        or assignment_pressure >= config.block_escalation_pressure
    ):
        return "block"
    if (
        review_load_ratio >= config.watch_review_load_ratio
        or stale_memory_ratio >= config.watch_stale_memory_ratio
        or coverage_gap_ratio >= config.watch_coverage_gap_ratio
        or escalation_pressure >= config.watch_escalation_pressure
        or assignment_pressure >= config.watch_escalation_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    review_load_ratio: Decimal,
    stale_memory_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    escalation_pressure: Decimal,
    assignment_pressure: Decimal,
    balance_status: str,
    config: ResearchTeamDomainAssignmentBalanceConfig,
) -> tuple[str, ...]:
    reason_codes = [f"domain_assignment_balance_{balance_status}"]
    if review_load_ratio >= config.block_review_load_ratio:
        reason_codes.append("review_load_block")
    elif review_load_ratio >= config.watch_review_load_ratio:
        reason_codes.append("review_load_watch")
    if stale_memory_ratio >= config.block_stale_memory_ratio:
        reason_codes.append("stale_memory_block")
    elif stale_memory_ratio >= config.watch_stale_memory_ratio:
        reason_codes.append("stale_memory_watch")
    if coverage_gap_ratio >= config.block_coverage_gap_ratio:
        reason_codes.append("coverage_gap_block")
    elif coverage_gap_ratio >= config.watch_coverage_gap_ratio:
        reason_codes.append("coverage_gap_watch")
    if escalation_pressure >= config.block_escalation_pressure:
        reason_codes.append("escalation_pressure_block")
    elif escalation_pressure >= config.watch_escalation_pressure:
        reason_codes.append("escalation_pressure_watch")
    if assignment_pressure >= config.block_escalation_pressure:
        reason_codes.append("assignment_pressure_block")
    elif (
        assignment_pressure >= config.watch_escalation_pressure
        and "escalation_pressure_watch" not in reason_codes
    ):
        reason_codes.append("assignment_pressure_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainAssignmentBalanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("domain_assignment_balance_empty",)
    report_status = _report_status(rows)
    reason_codes = [f"domain_assignment_balance_report_{report_status}"]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchTeamDomainAssignmentBalanceRow, ...]) -> str:
    if any(row.balance_status == "block" for row in rows):
        return "block"
    if any(row.balance_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainAssignmentBalanceRow, ...],
) -> tuple[ResearchTeamDomainAssignmentBalanceReasonCodeCount, ...]:
    reason_codes = sorted({reason_code for row in rows for reason_code in row.reason_codes})
    return tuple(
        ResearchTeamDomainAssignmentBalanceReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _normalize_assignments(value: object) -> tuple[ResearchTeamDomainAssignment, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("assignments must be an iterable")
    try:
        assignments = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("assignments must be an iterable") from exc
    for item in assignments:
        if type(item) is not ResearchTeamDomainAssignment:
            raise ValueError("assignments must contain ResearchTeamDomainAssignment values")
        _require_hard_flags("assignment", item)
    _validate_unique_assignments(assignments)
    return assignments


def _normalize_rows(value: object) -> tuple[ResearchTeamDomainAssignmentBalanceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamDomainAssignmentBalanceRow:
            raise ValueError("rows must contain ResearchTeamDomainAssignmentBalanceRow values")
        _require_hard_flags("row", row)
    normalized = tuple(sorted(rows, key=_row_key))
    if rows != normalized:
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainAssignmentBalanceReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchTeamDomainAssignmentBalanceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainAssignmentBalanceReasonCodeCount values",
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
    assignments: tuple[ResearchTeamDomainAssignment, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for assignment in assignments:
        key = (assignment.team_id, assignment.research_lane)
        if key in seen:
            raise ValueError("assignments must be unique by team_id and research_lane")
        seen.add(key)


def _validate_report(report: ResearchTeamDomainAssignmentBalanceReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _sum_decimal(tuple(row.team_count for row in report.rows)):
        raise ValueError("team_count must match rows")
    if report.research_lane_count != _count(len({row.research_lane for row in report.rows})):
        raise ValueError("research_lane_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchTeamDomainAssignmentBalanceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.balance_status == status))


def _row_key(row: ResearchTeamDomainAssignmentBalanceRow) -> tuple[int, str]:
    return (
        RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES.index(row.research_lane),
        row.research_lane,
    )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _reject_unsafe_public_text("config_version", value)


def _require_research_lane(value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES:
        raise ValueError("research_lane must be supported")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_ASSIGNMENT_BALANCE_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must be {field_name}")


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    _require_unit_decimal(field_name, normalized)
    return normalized


def _require_unit_decimal(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _clamp_unit(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_derived_validation_digest(
    report: ResearchTeamDomainAssignmentBalanceReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_public_payload_for_digest(
    report: ResearchTeamDomainAssignmentBalanceReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    return payload


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime value", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON compatible")


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public text")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_ASSIGNMENT_BALANCE_REPORT_CONFIG_VERSION",
    "DOMAIN_ASSIGNMENT_BALANCE_STATUSES",
    "RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES",
    "ResearchTeamDomainAssignment",
    "ResearchTeamDomainAssignmentBalanceConfig",
    "ResearchTeamDomainAssignmentBalanceReasonCodeCount",
    "ResearchTeamDomainAssignmentBalanceReport",
    "ResearchTeamDomainAssignmentBalanceRow",
    "build_research_team_domain_assignment_balance_report",
    "research_team_domain_assignment_balance_report_payload",
    "validate_research_team_domain_assignment_balance_report_payload",
)
