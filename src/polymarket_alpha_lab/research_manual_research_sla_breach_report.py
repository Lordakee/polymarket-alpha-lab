"""Deterministic manual research SLA breach reporting.

Callers provide already-collected manual follow-up observations. This module
groups them into public, report-only SLA status rows without external I/O.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchManualResearchSlaBreachConfig",
    "ResearchManualResearchSlaBreachObservation",
    "ResearchManualResearchSlaBreachReasonCodeCount",
    "ResearchManualResearchSlaBreachReport",
    "ResearchManualResearchSlaBreachRow",
    "build_research_manual_research_sla_breach_report",
    "research_manual_research_sla_breach_report_digest",
    "research_manual_research_sla_breach_report_payload",
)


DEFAULT_CONFIG_VERSION = "manual-research-sla-breach-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")

_SENSITIVE_FIELD_NAMES = (
    "raw_" "candidate_id",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_ref",
    "source_reference",
    "source_url",
    "source_text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "wal" "let",
    "au" "th",
    "or" "der",
    "tra" "de",
    "pos" "ition",
    "b" "uy",
    "se" "ll",
    "rec" "ommend",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchManualResearchSlaBreachConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_source_age_seconds: Decimal = Decimal("3600")
    stale_source_age_seconds: Decimal = Decimal("21600")
    watch_window_seconds: Decimal = Decimal("1800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualResearchSlaBreachConfig:
            raise TypeError(
                "ResearchManualResearchSlaBreachConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualResearchSlaBreachConfig, "config")
        _require_canonical_identifier("config_version", self.config_version)
        for field_name in (
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
            "watch_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_age_seconds <= self.fresh_source_age_seconds:
            raise ValueError(
                "stale_source_age_seconds must be greater than "
                "fresh_source_age_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchManualResearchSlaBreachObservation:
    team: str
    event_category: str
    assigned_at: datetime
    due_at: datetime
    source_age_seconds: Decimal
    completed_at: datetime | None = None
    missing_owner_flag: bool = False
    evidence_gap_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualResearchSlaBreachObservation:
            raise TypeError(
                "ResearchManualResearchSlaBreachObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualResearchSlaBreachObservation, "item")
        _require_public_label("team", self.team)
        _require_public_label("event_category", self.event_category)
        object.__setattr__(self, "assigned_at", _as_utc("assigned_at", self.assigned_at))
        object.__setattr__(self, "due_at", _as_utc("due_at", self.due_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "completed_at",
            _optional_as_utc("completed_at", self.completed_at),
        )
        _require_bool("missing_owner_flag", self.missing_owner_flag)
        _require_bool("evidence_gap_flag", self.evidence_gap_flag)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        if self.assigned_at > self.due_at:
            raise ValueError("assigned_at must not be after due_at")
        if self.completed_at is not None and self.completed_at < self.assigned_at:
            raise ValueError("completed_at must not be before assigned_at")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchManualResearchSlaBreachRow:
    team: str
    event_category: str
    source_freshness_status: str
    assignment_count: Decimal
    open_count: Decimal
    completed_count: Decimal
    due_soon_count: Decimal
    active_breach_count: Decimal
    completed_late_count: Decimal
    missing_owner_count: Decimal
    evidence_gap_count: Decimal
    latest_assigned_at: datetime
    earliest_due_at: datetime
    latest_completed_at: datetime | None
    max_source_age_seconds: Decimal
    max_overdue_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualResearchSlaBreachRow:
            raise TypeError(
                "ResearchManualResearchSlaBreachRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualResearchSlaBreachRow, "row")
        _require_public_label("team", self.team)
        _require_public_label("event_category", self.event_category)
        _require_status("source_freshness_status", self.source_freshness_status)
        for field_name in (
            "assignment_count",
            "open_count",
            "completed_count",
            "due_soon_count",
            "active_breach_count",
            "completed_late_count",
            "missing_owner_count",
            "evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_assigned_at",
            _as_utc("latest_assigned_at", self.latest_assigned_at),
        )
        object.__setattr__(
            self,
            "earliest_due_at",
            _as_utc("earliest_due_at", self.earliest_due_at),
        )
        object.__setattr__(
            self,
            "latest_completed_at",
            _optional_as_utc("latest_completed_at", self.latest_completed_at),
        )
        for field_name in ("max_source_age_seconds", "max_overdue_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchManualResearchSlaBreachReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualResearchSlaBreachReasonCodeCount:
            raise TypeError(
                "ResearchManualResearchSlaBreachReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchManualResearchSlaBreachReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchManualResearchSlaBreachReport:
    generated_at: datetime
    config_version: str
    group_count: Decimal
    assignment_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchManualResearchSlaBreachRow, ...]
    reason_code_counts: tuple[ResearchManualResearchSlaBreachReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualResearchSlaBreachReport:
            raise TypeError(
                "ResearchManualResearchSlaBreachReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualResearchSlaBreachReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_identifier("config_version", self.config_version)
        for field_name in (
            "group_count",
            "assignment_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_manual_research_sla_breach_report(
    observations: object,
    *,
    config: ResearchManualResearchSlaBreachConfig,
    generated_at: datetime,
) -> ResearchManualResearchSlaBreachReport:
    if type(config) is not ResearchManualResearchSlaBreachConfig:
        raise ValueError("config must be a ResearchManualResearchSlaBreachConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        _reject_future_item_times(item, generated_at_utc)

    groups: dict[tuple[str, str, str], list[ResearchManualResearchSlaBreachObservation]] = {}
    for item in items:
        source_status = _source_freshness_status(item.source_age_seconds, config=config)
        groups.setdefault((item.team, item.event_category, source_status), []).append(item)

    rows = tuple(
        _row_from_group(
            group_items=tuple(groups[key]),
            source_freshness_status=key[2],
            config=config,
            generated_at=generated_at_utc,
        )
        for key in sorted(groups)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchManualResearchSlaBreachReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        group_count=_decimal_count(len(rows)),
        assignment_count=sum((row.assignment_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_manual_research_sla_breach_report_payload(
    report: ResearchManualResearchSlaBreachReport,
) -> dict[str, Any]:
    if type(report) is not ResearchManualResearchSlaBreachReport:
        raise ValueError("report must be a ResearchManualResearchSlaBreachReport")
    _require_hard_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "group_count": str(report.group_count),
        "assignment_count": str(report.assignment_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            {"reason_code": count.reason_code, "count": str(count.count)}
            for count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
    }


def research_manual_research_sla_breach_report_digest(
    report: ResearchManualResearchSlaBreachReport,
) -> dict[str, Any]:
    if type(report) is not ResearchManualResearchSlaBreachReport:
        raise ValueError("report must be a ResearchManualResearchSlaBreachReport")
    _require_hard_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "group_count": str(report.group_count),
        "assignment_count": str(report.assignment_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "status": report.status,
        "team_statuses": _team_statuses(report.rows),
        "reason_codes": list(report.reason_codes),
    }


def _row_from_group(
    *,
    group_items: tuple[ResearchManualResearchSlaBreachObservation, ...],
    source_freshness_status: str,
    config: ResearchManualResearchSlaBreachConfig,
    generated_at: datetime,
) -> ResearchManualResearchSlaBreachRow:
    if not group_items:
        raise ValueError("group_items must be nonempty")
    sorted_items = tuple(
        sorted(
            group_items,
            key=lambda item: (
                item.assigned_at,
                item.due_at,
                item.completed_at or datetime.max.replace(tzinfo=UTC),
                item.team,
                item.event_category,
            ),
        ),
    )
    team = sorted_items[0].team
    event_category = sorted_items[0].event_category
    assignment_count = len(sorted_items)
    open_items = tuple(item for item in sorted_items if item.completed_at is None)
    completed_items = tuple(item for item in sorted_items if item.completed_at is not None)
    due_soon_count = sum(
        1
        for item in open_items
        if ZERO <= _age_seconds(item.due_at, generated_at) <= config.watch_window_seconds
    )
    active_breach_count = sum(1 for item in open_items if item.due_at < generated_at)
    completed_late_count = sum(
        1
        for item in completed_items
        if item.completed_at is not None and item.completed_at > item.due_at
    )
    missing_owner_count = sum(1 for item in sorted_items if item.missing_owner_flag)
    evidence_gap_count = sum(1 for item in sorted_items if item.evidence_gap_flag)
    max_source_age_seconds = max(item.source_age_seconds for item in sorted_items)
    max_overdue_seconds = max(
        (
            _item_overdue_seconds(item, generated_at)
            for item in sorted_items
        ),
        default=ZERO,
    )
    status = _row_status(
        source_freshness_status=source_freshness_status,
        due_soon_count=due_soon_count,
        active_breach_count=active_breach_count,
        completed_late_count=completed_late_count,
        missing_owner_count=missing_owner_count,
        evidence_gap_count=evidence_gap_count,
    )
    reason_codes = _row_reason_codes(
        status=status,
        source_freshness_status=source_freshness_status,
        due_soon_count=due_soon_count,
        active_breach_count=active_breach_count,
        completed_late_count=completed_late_count,
        missing_owner_count=missing_owner_count,
        evidence_gap_count=evidence_gap_count,
        input_reason_codes=tuple(
            reason_code for item in sorted_items for reason_code in item.reason_codes
        ),
    )

    return ResearchManualResearchSlaBreachRow(
        team=team,
        event_category=event_category,
        source_freshness_status=source_freshness_status,
        assignment_count=_decimal_count(assignment_count),
        open_count=_decimal_count(len(open_items)),
        completed_count=_decimal_count(len(completed_items)),
        due_soon_count=_decimal_count(due_soon_count),
        active_breach_count=_decimal_count(active_breach_count),
        completed_late_count=_decimal_count(completed_late_count),
        missing_owner_count=_decimal_count(missing_owner_count),
        evidence_gap_count=_decimal_count(evidence_gap_count),
        latest_assigned_at=max(item.assigned_at for item in sorted_items),
        earliest_due_at=min(item.due_at for item in sorted_items),
        latest_completed_at=(
            max(item.completed_at for item in completed_items if item.completed_at is not None)
            if completed_items
            else None
        ),
        max_source_age_seconds=max_source_age_seconds,
        max_overdue_seconds=max_overdue_seconds,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_observations(
    observations: object,
) -> tuple[ResearchManualResearchSlaBreachObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(value: object) -> ResearchManualResearchSlaBreachObservation:
    _reject_sensitive_surface(value)
    if type(value) is ResearchManualResearchSlaBreachObservation:
        _require_hard_flags("item", value)
        return value
    _require_hard_flags("item", value)
    return ResearchManualResearchSlaBreachObservation(
        team=_field_value(value, "team"),
        event_category=_field_value(value, "event_category"),
        assigned_at=_field_value(value, "assigned_at"),
        due_at=_field_value(value, "due_at"),
        source_age_seconds=_field_value(value, "source_age_seconds"),
        completed_at=_field_value(value, "completed_at", default=None),
        missing_owner_flag=_field_value(value, "missing_owner_flag", default=False),
        evidence_gap_flag=_field_value(value, "evidence_gap_flag", default=False),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _source_freshness_status(
    source_age_seconds: Decimal,
    *,
    config: ResearchManualResearchSlaBreachConfig,
) -> str:
    if source_age_seconds > config.stale_source_age_seconds:
        return "block"
    if source_age_seconds > config.fresh_source_age_seconds:
        return "watch"
    return "pass"


def _row_status(
    *,
    source_freshness_status: str,
    due_soon_count: int,
    active_breach_count: int,
    completed_late_count: int,
    missing_owner_count: int,
    evidence_gap_count: int,
) -> str:
    if (
        source_freshness_status == "block"
        or active_breach_count
        or completed_late_count
        or missing_owner_count
        or evidence_gap_count
    ):
        return "block"
    if source_freshness_status == "watch" or due_soon_count:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_freshness_status: str,
    due_soon_count: int,
    active_breach_count: int,
    completed_late_count: int,
    missing_owner_count: int,
    evidence_gap_count: int,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"manual_research_sla_{status}"}
    if source_freshness_status == "pass":
        reason_codes.add("fresh_sources")
    elif source_freshness_status == "watch":
        reason_codes.add("aging_sources")
    else:
        reason_codes.add("stale_sources")
    if due_soon_count:
        reason_codes.add("manual_research_due_soon")
    if active_breach_count or completed_late_count:
        reason_codes.add("manual_research_sla_overdue")
    if missing_owner_count:
        reason_codes.add("missing_owner_present")
    if evidence_gap_count:
        reason_codes.add("evidence_gap_present")
    if status == "pass":
        reason_codes.add("no_manual_research_sla_breach")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchManualResearchSlaBreachRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_manual_research_assignments",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.status == "watch" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("manual_research_sla_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_manual_research_assignments",):
        return "block"
    if "manual_research_sla_block" in reason_codes:
        return "block"
    if "manual_research_sla_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchManualResearchSlaBreachRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchManualResearchSlaBreachReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchManualResearchSlaBreachReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _team_statuses(
    rows: tuple[ResearchManualResearchSlaBreachRow, ...],
) -> list[dict[str, str]]:
    team_names = tuple(sorted({row.team for row in rows}))
    statuses: list[dict[str, str]] = []
    for team in team_names:
        team_rows = tuple(row for row in rows if row.team == team)
        reason_codes = tuple(sorted({code for row in team_rows for code in row.reason_codes}))
        statuses.append(
            {
                "assignment_count": str(
                    sum((row.assignment_count for row in team_rows), ZERO),
                ),
                "status": _summary_status(reason_codes),
                "team": team,
            },
        )
    return statuses


def _row_payload(row: ResearchManualResearchSlaBreachRow) -> dict[str, Any]:
    _require_hard_flags("row", row)
    return {
        "team": row.team,
        "event_category": row.event_category,
        "source_freshness_status": row.source_freshness_status,
        "assignment_count": str(row.assignment_count),
        "open_count": str(row.open_count),
        "completed_count": str(row.completed_count),
        "due_soon_count": str(row.due_soon_count),
        "active_breach_count": str(row.active_breach_count),
        "completed_late_count": str(row.completed_late_count),
        "missing_owner_count": str(row.missing_owner_count),
        "evidence_gap_count": str(row.evidence_gap_count),
        "latest_assigned_at": row.latest_assigned_at.isoformat(),
        "earliest_due_at": row.earliest_due_at.isoformat(),
        "latest_completed_at": (
            row.latest_completed_at.isoformat()
            if row.latest_completed_at is not None
            else None
        ),
        "max_source_age_seconds": str(row.max_source_age_seconds),
        "max_overdue_seconds": str(row.max_overdue_seconds),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
    }


def _item_overdue_seconds(
    item: ResearchManualResearchSlaBreachObservation,
    generated_at: datetime,
) -> Decimal:
    if item.completed_at is None:
        if item.due_at >= generated_at:
            return ZERO
        return _age_seconds(generated_at, item.due_at)
    if item.completed_at <= item.due_at:
        return ZERO
    return _age_seconds(item.completed_at, item.due_at)


def _reject_future_item_times(
    item: ResearchManualResearchSlaBreachObservation,
    generated_at: datetime,
) -> None:
    if item.assigned_at > generated_at:
        raise ValueError("assigned_at must not be after generated_at")
    if item.completed_at is not None and item.completed_at > generated_at:
        raise ValueError("completed_at must not be after generated_at")


def _status_count(rows: tuple[ResearchManualResearchSlaBreachRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchManualResearchSlaBreachRow, ...],
) -> tuple[ResearchManualResearchSlaBreachRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchManualResearchSlaBreachRow:
            raise ValueError(
                "rows must contain ResearchManualResearchSlaBreachRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.team,
                row.event_category,
                row.source_freshness_status,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public grouping fields")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchManualResearchSlaBreachReasonCodeCount, ...],
) -> tuple[ResearchManualResearchSlaBreachReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchManualResearchSlaBreachReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchManualResearchSlaBreachReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchManualResearchSlaBreachRow) -> None:
    if row.assignment_count <= ZERO:
        raise ValueError("assignment_count must be positive")
    if row.assignment_count != row.open_count + row.completed_count:
        raise ValueError("assignment_count must equal open_count plus completed_count")
    for field_name in (
        "due_soon_count",
        "active_breach_count",
        "completed_late_count",
        "missing_owner_count",
        "evidence_gap_count",
    ):
        if getattr(row, field_name) > row.assignment_count:
            raise ValueError(f"{field_name} must not exceed assignment_count")
    expected_status = _row_status(
        source_freshness_status=row.source_freshness_status,
        due_soon_count=int(row.due_soon_count),
        active_breach_count=int(row.active_breach_count),
        completed_late_count=int(row.completed_late_count),
        missing_owner_count=int(row.missing_owner_count),
        evidence_gap_count=int(row.evidence_gap_count),
    )
    if row.status != expected_status:
        raise ValueError("status must match row SLA state")


def _validate_report_consistency(
    report: ResearchManualResearchSlaBreachReport,
) -> None:
    if report.group_count != _decimal_count(len(report.rows)):
        raise ValueError("group_count must match rows")
    if report.assignment_count != sum((row.assignment_count for row in report.rows), ZERO):
        raise ValueError("assignment_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _reject_sensitive_surface(value: object) -> None:
    names: set[str] = set()
    if is_dataclass(value):
        names.update(field.name for field in fields(value))
    try:
        names.update(vars(value))
    except TypeError:
        pass
    lowered_to_original = {name.lower(): name for name in names}
    for sensitive_name in _SENSITIVE_FIELD_NAMES:
        if sensitive_name in lowered_to_original:
            original_name = lowered_to_original[sensitive_name]
            raise ValueError(
                f"{original_name} must not be present in manual research SLA inputs",
            )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_canonical_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_identifier(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public identifier")
    if not value[0].islower():
        raise ValueError(f"{field_name} must be a public identifier")
    if "http" in value or "://" in value or "?" in value or "#" in value:
        raise ValueError(f"{field_name} must not contain external references")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must contain public reason codes")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
