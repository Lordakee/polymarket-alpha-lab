"""Pure history reducer for candidate decision score reports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.candidate_decision_score import (
    ACTION_STATES,
    CandidateDecisionScoreReport,
)


__all__ = (
    "CandidateDecisionScoreHistoryActionCount",
    "CandidateDecisionScoreHistoryReasonCodeCount",
    "CandidateDecisionScoreHistoryRow",
    "CandidateDecisionScoreHistoryReport",
    "CandidateDecisionScoreHistoryTeamCount",
    "build_candidate_decision_score_history_report",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HISTORY_STATUSES = ("empty", "observed")


@dataclass(frozen=True)
class CandidateDecisionScoreHistoryActionCount:
    action: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_action("action", self.action)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        _require_hard_flags("action_count", self)


@dataclass(frozen=True)
class CandidateDecisionScoreHistoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class CandidateDecisionScoreHistoryTeamCount:
    team_id: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        _require_hard_flags("team_count", self)


@dataclass(frozen=True)
class CandidateDecisionScoreHistoryRow:
    source_generated_at: datetime
    config_version: str
    candidate_id: str
    market_id: str
    primary_team_id: str
    action: str
    decision_score: Decimal
    hard_blocker_count: Decimal
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        for field_name in (
            "config_version",
            "candidate_id",
            "market_id",
            "primary_team_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_action("action", self.action)
        object.__setattr__(
            self,
            "decision_score",
            _normalize_unit_decimal("decision_score", self.decision_score),
        )
        object.__setattr__(
            self,
            "hard_blocker_count",
            _normalize_count_decimal("hard_blocker_count", self.hard_blocker_count),
        )
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(
                "hard_blocker_codes",
                self.hard_blocker_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_history_row(self)
        _require_hard_flags("history_row", self)


@dataclass(frozen=True)
class CandidateDecisionScoreHistoryReport:
    generated_at: datetime
    status: str
    source_report_count: Decimal
    report_count: Decimal
    first_source_generated_at: datetime | None
    latest_generated_at: datetime | None
    candidate_count: Decimal
    action_reject_count: Decimal
    action_watch_count: Decimal
    action_research_more_count: Decimal
    action_paper_recommend_count: Decimal
    hard_blocked_count: Decimal
    blocked_total: Decimal
    watch_total: Decimal
    paper_recommend_total: Decimal
    rows: tuple[CandidateDecisionScoreHistoryRow, ...]
    action_counts: tuple[CandidateDecisionScoreHistoryActionCount, ...]
    hard_blocker_code_counts: tuple[CandidateDecisionScoreHistoryReasonCodeCount, ...]
    reason_code_counts: tuple[CandidateDecisionScoreHistoryReasonCodeCount, ...]
    reason_counts: tuple[CandidateDecisionScoreHistoryReasonCodeCount, ...]
    primary_team_counts: tuple[CandidateDecisionScoreHistoryTeamCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_member("status", self.status, HISTORY_STATUSES)
        object.__setattr__(
            self,
            "first_source_generated_at",
            _as_optional_utc("first_source_generated_at", self.first_source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        for field_name in (
            "source_report_count",
            "report_count",
            "candidate_count",
            "action_reject_count",
            "action_watch_count",
            "action_research_more_count",
            "action_paper_recommend_count",
            "hard_blocked_count",
            "blocked_total",
            "watch_total",
            "paper_recommend_total",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "action_counts",
            _normalize_action_counts("action_counts", self.action_counts),
        )
        object.__setattr__(
            self,
            "hard_blocker_code_counts",
            _normalize_reason_code_counts(
                "hard_blocker_code_counts",
                self.hard_blocker_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_counts",
            _normalize_reason_code_counts("reason_counts", self.reason_counts),
        )
        object.__setattr__(
            self,
            "primary_team_counts",
            _normalize_team_counts("primary_team_counts", self.primary_team_counts),
        )
        _validate_history_report(self)
        _require_hard_flags("history_report", self)


def build_candidate_decision_score_history_report(
    reports: CandidateDecisionScoreReport | Iterable[CandidateDecisionScoreReport],
    *,
    generated_at: datetime,
) -> CandidateDecisionScoreHistoryReport:
    """Reduce candidate decision score reports into deterministic history metrics."""

    generated_at_utc = _as_utc("generated_at", generated_at)
    source_reports = _normalize_source_reports(reports)
    rows = tuple(_row_from_report(report) for report in source_reports)
    first_row = rows[0] if rows else None
    latest_row = rows[-1] if rows else None

    return CandidateDecisionScoreHistoryReport(
        generated_at=generated_at_utc,
        status="observed" if rows else "empty",
        source_report_count=_count_decimal(len(source_reports)),
        report_count=_count_decimal(len(source_reports)),
        first_source_generated_at=(
            first_row.source_generated_at if first_row is not None else None
        ),
        latest_generated_at=latest_row.source_generated_at if latest_row is not None else None,
        candidate_count=_count_decimal(len({report.candidate_id for report in source_reports})),
        action_reject_count=_action_count(source_reports, "reject"),
        action_watch_count=_action_count(source_reports, "watch"),
        action_research_more_count=_action_count(source_reports, "research_more"),
        action_paper_recommend_count=_action_count(source_reports, "paper_recommend"),
        hard_blocked_count=_hard_blocked_count(source_reports),
        blocked_total=_hard_blocked_count(source_reports),
        watch_total=_action_count(source_reports, "watch"),
        paper_recommend_total=_action_count(source_reports, "paper_recommend"),
        rows=rows,
        action_counts=_action_counts_from_rows(rows),
        hard_blocker_code_counts=_reason_code_counts_from_rows(
            rows,
            "hard_blocker_codes",
        ),
        reason_code_counts=_reason_code_counts_from_rows(rows, "reason_codes"),
        reason_counts=_reason_code_counts_from_rows(rows, "reason_codes"),
        primary_team_counts=_team_counts_from_rows(rows),
    )


def _row_from_report(report: CandidateDecisionScoreReport) -> CandidateDecisionScoreHistoryRow:
    return CandidateDecisionScoreHistoryRow(
        source_generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_id=report.candidate_id,
        market_id=report.market_id,
        primary_team_id=report.primary_team_id,
        action=report.action,
        decision_score=report.decision_score,
        hard_blocker_count=_count_decimal(len(report.hard_blocker_codes)),
        hard_blocker_codes=report.hard_blocker_codes,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _normalize_source_reports(
    value: CandidateDecisionScoreReport | Iterable[CandidateDecisionScoreReport],
) -> tuple[CandidateDecisionScoreReport, ...]:
    if type(value) is CandidateDecisionScoreReport:
        reports = (value,)
    else:
        if isinstance(value, (str, bytes)):
            raise ValueError(
                "reports must be a CandidateDecisionScoreReport or an iterable",
            )
        try:
            reports = tuple(value)
        except TypeError as exc:
            raise ValueError(
                "reports must be a CandidateDecisionScoreReport or an iterable",
            ) from exc

    seen_keys: set[tuple[datetime, str, str, str]] = set()
    for report in reports:
        if type(report) is not CandidateDecisionScoreReport:
            raise ValueError("reports must contain CandidateDecisionScoreReport values")
        _require_hard_flags("reports", report)
        key = _history_sort_key(report)
        if key in seen_keys:
            raise ValueError(
                "duplicate generated_at/config/candidate/market source history key",
            )
        seen_keys.add(key)
    return tuple(sorted(reports, key=_history_sort_key))


def _history_sort_key(report: CandidateDecisionScoreReport) -> tuple[datetime, str, str, str]:
    return (
        _as_utc("generated_at", report.generated_at),
        report.config_version,
        report.candidate_id,
        report.market_id,
    )


def _row_sort_key(row: CandidateDecisionScoreHistoryRow) -> tuple[datetime, str, str, str]:
    return (
        row.source_generated_at,
        row.config_version,
        row.candidate_id,
        row.market_id,
    )


def _action_count(
    reports: tuple[CandidateDecisionScoreReport, ...],
    action: str,
) -> Decimal:
    return _count_decimal(sum(1 for report in reports if report.action == action))


def _hard_blocked_count(reports: tuple[CandidateDecisionScoreReport, ...]) -> Decimal:
    return _count_decimal(sum(1 for report in reports if report.hard_blocker_codes))


def _reason_code_counts_from_rows(
    rows: tuple[CandidateDecisionScoreHistoryRow, ...],
    field_name: str,
) -> tuple[CandidateDecisionScoreHistoryReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(getattr(row, field_name))
    return tuple(
        CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _action_counts_from_rows(
    rows: tuple[CandidateDecisionScoreHistoryRow, ...],
) -> tuple[CandidateDecisionScoreHistoryActionCount, ...]:
    counter: Counter[str] = Counter(row.action for row in rows)
    return tuple(
        CandidateDecisionScoreHistoryActionCount(
            action=action,
            count=_count_decimal(count),
        )
        for action, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _team_counts_from_rows(
    rows: tuple[CandidateDecisionScoreHistoryRow, ...],
) -> tuple[CandidateDecisionScoreHistoryTeamCount, ...]:
    counter: Counter[str] = Counter(row.primary_team_id for row in rows)
    return tuple(
        CandidateDecisionScoreHistoryTeamCount(
            team_id=team_id,
            count=_count_decimal(count),
        )
        for team_id, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_rows(
    value: Iterable[CandidateDecisionScoreHistoryRow],
) -> tuple[CandidateDecisionScoreHistoryRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not CandidateDecisionScoreHistoryRow:
            raise ValueError("rows must contain CandidateDecisionScoreHistoryRow values")
        _require_hard_flags("rows", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_action_counts(
    field_name: str,
    value: Iterable[CandidateDecisionScoreHistoryActionCount],
) -> tuple[CandidateDecisionScoreHistoryActionCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen_actions: set[str] = set()
    for row in rows:
        if type(row) is not CandidateDecisionScoreHistoryActionCount:
            raise ValueError(
                f"{field_name} must contain CandidateDecisionScoreHistoryActionCount values",
            )
        _require_hard_flags(field_name, row)
        if row.action in seen_actions:
            raise ValueError(f"duplicate {field_name} action")
        seen_actions.add(row.action)
    return tuple(sorted(rows, key=lambda row: row.action))


def _normalize_reason_code_counts(
    field_name: str,
    value: Iterable[CandidateDecisionScoreHistoryReasonCodeCount],
) -> tuple[CandidateDecisionScoreHistoryReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not CandidateDecisionScoreHistoryReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain CandidateDecisionScoreHistoryReasonCodeCount values",
            )
        _require_hard_flags(field_name, row)
        if row.reason_code in seen_codes:
            raise ValueError(f"duplicate {field_name} reason_code")
        seen_codes.add(row.reason_code)
    return tuple(sorted(rows, key=lambda row: (-row.count, row.reason_code)))


def _normalize_team_counts(
    field_name: str,
    value: Iterable[CandidateDecisionScoreHistoryTeamCount],
) -> tuple[CandidateDecisionScoreHistoryTeamCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen_team_ids: set[str] = set()
    for row in rows:
        if type(row) is not CandidateDecisionScoreHistoryTeamCount:
            raise ValueError(
                f"{field_name} must contain CandidateDecisionScoreHistoryTeamCount values",
            )
        _require_hard_flags(field_name, row)
        if row.team_id in seen_team_ids:
            raise ValueError(f"duplicate {field_name} team_id")
        seen_team_ids.add(row.team_id)
    return tuple(sorted(rows, key=lambda row: (-row.count, row.team_id)))


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for code in codes:
        _require_canonical_string(f"{field_name} item", code)
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def _validate_history_row(row: CandidateDecisionScoreHistoryRow) -> None:
    if row.hard_blocker_count != _count_decimal(len(row.hard_blocker_codes)):
        raise ValueError("hard_blocker_count must match hard_blocker_codes")
    if row.reason_codes[0] != f"candidate_decision_{row.action}":
        raise ValueError("reason_codes must start with action reason")
    if row.hard_blocker_codes and row.action != "reject":
        raise ValueError("hard_blocker_codes require reject action")
    for code in row.hard_blocker_codes:
        if code not in row.reason_codes:
            raise ValueError("reason_codes must include hard blocker codes")


def _validate_history_report(report: CandidateDecisionScoreHistoryReport) -> None:
    if report.report_count != report.source_report_count:
        raise ValueError("report_count must match source_report_count")
    if report.source_report_count != _count_decimal(len(report.rows)):
        raise ValueError("source_report_count must match rows")
    if report.status != ("observed" if report.rows else "empty"):
        raise ValueError("status must match rows")
    if report.candidate_count != _count_decimal(
        len({row.candidate_id for row in report.rows}),
    ):
        raise ValueError("candidate_count must match rows")
    action_total = (
        report.action_reject_count
        + report.action_watch_count
        + report.action_research_more_count
        + report.action_paper_recommend_count
    )
    if action_total != report.source_report_count:
        raise ValueError("action counts must match source_report_count")
    if report.hard_blocked_count != _count_decimal(
        sum(1 for row in report.rows if row.hard_blocker_codes),
    ):
        raise ValueError("hard_blocked_count must match rows")
    if report.blocked_total != report.hard_blocked_count:
        raise ValueError("blocked_total must match hard_blocked_count")
    if report.watch_total != report.action_watch_count:
        raise ValueError("watch_total must match action_watch_count")
    if report.paper_recommend_total != report.action_paper_recommend_count:
        raise ValueError(
            "paper_recommend_total must match action_paper_recommend_count",
        )
    if report.action_counts != _action_counts_from_rows(report.rows):
        raise ValueError("action_counts must match rows")
    if report.reason_counts != report.reason_code_counts:
        raise ValueError("reason_counts must match reason_code_counts")
    if report.primary_team_counts != _team_counts_from_rows(report.rows):
        raise ValueError("primary_team_counts must match rows")
    if not report.rows:
        _validate_empty_history_report(report)
        return
    _validate_nonempty_history_report(report)


def _validate_empty_history_report(report: CandidateDecisionScoreHistoryReport) -> None:
    if report.first_source_generated_at is not None:
        raise ValueError("first_source_generated_at must be None for empty history")
    if report.latest_generated_at is not None:
        raise ValueError("latest_generated_at must be None for empty history")
    if report.hard_blocker_code_counts:
        raise ValueError("hard_blocker_code_counts must be empty for empty history")
    if report.reason_code_counts:
        raise ValueError("reason_code_counts must be empty for empty history")


def _validate_nonempty_history_report(report: CandidateDecisionScoreHistoryReport) -> None:
    if report.first_source_generated_at is None:
        raise ValueError("first_source_generated_at is required")
    if report.latest_generated_at is None:
        raise ValueError("latest_generated_at is required")
    if report.latest_generated_at < report.first_source_generated_at:
        raise ValueError("latest_generated_at must not precede first_source_generated_at")
    if report.first_source_generated_at != report.rows[0].source_generated_at:
        raise ValueError("first_source_generated_at must match first row")
    if report.latest_generated_at != report.rows[-1].source_generated_at:
        raise ValueError("latest_generated_at must match latest row")
    expected_hard_counts = _reason_code_counts_from_rows(
        report.rows,
        "hard_blocker_codes",
    )
    if report.hard_blocker_code_counts != expected_hard_counts:
        raise ValueError("hard_blocker_code_counts must match rows")
    expected_reason_counts = _reason_code_counts_from_rows(report.rows, "reason_codes")
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATES:
        raise ValueError(f"{field_name} must be a known candidate decision action")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
