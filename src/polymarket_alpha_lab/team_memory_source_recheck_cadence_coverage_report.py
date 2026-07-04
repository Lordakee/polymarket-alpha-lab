"""Pure in-memory coverage reducer for team memory source cadence."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_COVERAGE_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-coverage-v0"
)

NO_TEAM_CATEGORIES_REASON = (
    "team_memory_source_recheck_cadence_coverage_no_team_categories"
)
SOURCE_GAP_REASON = "team_memory_source_recheck_cadence_coverage_source_gap"
OVERDUE_GAP_REASON = "team_memory_source_recheck_cadence_coverage_overdue_gap"
ACKNOWLEDGEMENT_GAP_REASON = (
    "team_memory_source_recheck_cadence_coverage_acknowledgement_gap"
)
CLEAR_REASON = "team_memory_source_recheck_cadence_coverage_clear"

REASON_CODE_SEQUENCE = (
    NO_TEAM_CATEGORIES_REASON,
    SOURCE_GAP_REASON,
    OVERDUE_GAP_REASON,
    ACKNOWLEDGEMENT_GAP_REASON,
    CLEAR_REASON,
)
ROW_REASON_CODE_SEQUENCE = REASON_CODE_SEQUENCE[1:]
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("or", "der"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceCoverageTarget:
    team_id: str
    category_id: str
    expected_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "expected_source_count",
            _require_positive_decimal(
                "expected_source_count",
                self.expected_source_count,
            ),
        )
        require_paper_only_flags("coverage target", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceCoverageConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_COVERAGE_CONFIG_VERSION
    team_category_targets: tuple[TeamMemorySourceRecheckCadenceCoverageTarget, ...] = ()
    min_source_coverage_ratio: Decimal = Decimal("1.000000")
    min_overdue_cadence_coverage_ratio: Decimal = Decimal("1.000000")
    min_acknowledged_source_coverage_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "team_category_targets",
            _normalize_targets(self.team_category_targets),
        )
        for field_name in (
            "min_source_coverage_ratio",
            "min_overdue_cadence_coverage_ratio",
            "min_acknowledged_source_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("coverage config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceCoverageSource:
    team_id: str
    category_id: str
    source_id: str
    source_family: str
    last_rechecked_at: datetime
    next_recheck_due_at: datetime
    acknowledged_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if self.next_recheck_due_at < self.last_rechecked_at:
            raise ValueError("next_recheck_due_at must not precede last_rechecked_at")
        require_paper_only_flags("coverage source", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow:
    team_id: str
    category_id: str
    row_status: str
    expected_source_count: Decimal
    source_count: Decimal
    missing_source_count: Decimal
    current_cadence_source_count: Decimal
    overdue_source_count: Decimal
    acknowledged_source_count: Decimal
    unacknowledged_source_count: Decimal
    source_coverage_ratio: Decimal
    overdue_cadence_coverage_ratio: Decimal
    acknowledged_source_coverage_ratio: Decimal
    max_overdue_age_seconds: Decimal
    latest_rechecked_at: datetime | None
    latest_acknowledged_at: datetime | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_row_status("row_status", self.row_status)
        for field_name in (
            "expected_source_count",
            "source_count",
            "missing_source_count",
            "current_cadence_source_count",
            "overdue_source_count",
            "acknowledged_source_count",
            "unacknowledged_source_count",
            "max_overdue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_coverage_ratio",
            "overdue_cadence_coverage_ratio",
            "acknowledged_source_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_rechecked_at",
            _as_optional_utc("latest_rechecked_at", self.latest_rechecked_at),
        )
        object.__setattr__(
            self,
            "latest_acknowledged_at",
            _as_optional_utc("latest_acknowledged_at", self.latest_acknowledged_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, row_scope=True),
        )
        _validate_team_category_row(self)
        require_paper_only_flags("coverage team category row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceCoverageReport:
    generated_at: datetime
    config_version: str
    report_status: str
    team_category_count: Decimal
    expected_source_count: Decimal
    source_count: Decimal
    missing_source_count: Decimal
    current_cadence_source_count: Decimal
    overdue_source_count: Decimal
    acknowledged_source_count: Decimal
    unacknowledged_source_count: Decimal
    source_coverage_ratio: Decimal
    overdue_cadence_coverage_ratio: Decimal
    acknowledged_source_coverage_ratio: Decimal
    max_overdue_age_seconds: Decimal
    team_category_rows: tuple[TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "team_category_count",
            "expected_source_count",
            "source_count",
            "missing_source_count",
            "current_cadence_source_count",
            "overdue_source_count",
            "acknowledged_source_count",
            "unacknowledged_source_count",
            "max_overdue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_coverage_ratio",
            "overdue_cadence_coverage_ratio",
            "acknowledged_source_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_category_rows",
            _normalize_team_category_rows(self.team_category_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, row_scope=False),
        )
        _validate_report(self)
        require_paper_only_flags("coverage report", self)


def build_team_memory_source_recheck_cadence_coverage_report(
    sources: list[TeamMemorySourceRecheckCadenceCoverageSource]
    | tuple[TeamMemorySourceRecheckCadenceCoverageSource, ...],
    *,
    config: TeamMemorySourceRecheckCadenceCoverageConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceCoverageReport:
    if type(config) is not TeamMemorySourceRecheckCadenceCoverageConfig:
        raise ValueError(
            "config must be a TeamMemorySourceRecheckCadenceCoverageConfig",
        )
    require_paper_only_flags("coverage config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources, generated_at=generated_at_utc)
    rows = _team_category_rows(
        normalized_sources,
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(rows)
    return TeamMemorySourceRecheckCadenceCoverageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(reason_codes),
        team_category_count=_decimal_count(len(rows)),
        expected_source_count=_sum_decimal(rows, "expected_source_count"),
        source_count=_sum_decimal(rows, "source_count"),
        missing_source_count=_sum_decimal(rows, "missing_source_count"),
        current_cadence_source_count=_sum_decimal(
            rows,
            "current_cadence_source_count",
        ),
        overdue_source_count=_sum_decimal(rows, "overdue_source_count"),
        acknowledged_source_count=_sum_decimal(rows, "acknowledged_source_count"),
        unacknowledged_source_count=_sum_decimal(rows, "unacknowledged_source_count"),
        source_coverage_ratio=_coverage_ratio(
            _sum_decimal(rows, "source_count"),
            _sum_decimal(rows, "expected_source_count"),
        ),
        overdue_cadence_coverage_ratio=_coverage_ratio(
            _sum_decimal(rows, "current_cadence_source_count"),
            _sum_decimal(rows, "source_count"),
        ),
        acknowledged_source_coverage_ratio=_coverage_ratio(
            _sum_decimal(rows, "acknowledged_source_count"),
            _sum_decimal(rows, "source_count"),
        ),
        max_overdue_age_seconds=_max_decimal(rows, "max_overdue_age_seconds"),
        team_category_rows=rows,
        reason_codes=reason_codes,
    )


def team_memory_source_recheck_cadence_coverage_report_payload(
    report: TeamMemorySourceRecheckCadenceCoverageReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceCoverageReport:
        raise ValueError(
            "report must be a TeamMemorySourceRecheckCadenceCoverageReport",
        )
    require_paper_only_flags("coverage report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report must become a JSON object")
    reject_unsafe_surface_fields(
        "team memory source recheck cadence coverage report",
        ready,
    )
    return ready


def _team_category_rows(
    sources: tuple[TeamMemorySourceRecheckCadenceCoverageSource, ...],
    *,
    config: TeamMemorySourceRecheckCadenceCoverageConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow, ...]:
    grouped_sources: dict[
        tuple[str, str],
        list[TeamMemorySourceRecheckCadenceCoverageSource],
    ] = {}
    for source in sources:
        grouped_sources.setdefault((source.team_id, source.category_id), []).append(source)
    expected_counts = {
        (target.team_id, target.category_id): target.expected_source_count
        for target in config.team_category_targets
    }
    pairs = tuple(
        sorted(
            set(grouped_sources) | set(expected_counts),
            key=lambda item: (item[1], item[0]),
        ),
    )
    rows = tuple(
        _team_category_row(
            team_id=team_id,
            category_id=category_id,
            sources=tuple(grouped_sources.get((team_id, category_id), ())),
            expected_source_count=expected_counts.get(
                (team_id, category_id),
                _decimal_count(len(grouped_sources.get((team_id, category_id), ()))),
            ),
            config=config,
            generated_at=generated_at,
        )
        for team_id, category_id in pairs
    )
    return tuple(sorted(rows, key=_team_category_row_sort_key))


def _team_category_row(
    *,
    team_id: str,
    category_id: str,
    sources: tuple[TeamMemorySourceRecheckCadenceCoverageSource, ...],
    expected_source_count: Decimal,
    config: TeamMemorySourceRecheckCadenceCoverageConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow:
    source_count = _decimal_count(len(sources))
    overdue_sources = tuple(
        source for source in sources if source.next_recheck_due_at < generated_at
    )
    acknowledged_sources = tuple(
        source for source in sources if source.acknowledged_at is not None
    )
    current_cadence_source_count = _decimal_count(len(sources) - len(overdue_sources))
    overdue_source_count = _decimal_count(len(overdue_sources))
    acknowledged_source_count = _decimal_count(len(acknowledged_sources))
    unacknowledged_source_count = _decimal_count(len(sources) - len(acknowledged_sources))
    missing_source_count = _nonnegative_decimal_difference(
        expected_source_count,
        source_count,
    )
    source_coverage_ratio = _coverage_ratio(source_count, expected_source_count)
    overdue_cadence_coverage_ratio = _coverage_ratio(
        current_cadence_source_count,
        source_count,
    )
    acknowledged_source_coverage_ratio = _coverage_ratio(
        acknowledged_source_count,
        source_count,
    )
    reason_codes = _row_reason_codes(
        source_coverage_ratio=source_coverage_ratio,
        overdue_cadence_coverage_ratio=overdue_cadence_coverage_ratio,
        acknowledged_source_coverage_ratio=acknowledged_source_coverage_ratio,
        config=config,
    )
    return TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow(
        team_id=team_id,
        category_id=category_id,
        row_status=_row_status(reason_codes),
        expected_source_count=expected_source_count,
        source_count=source_count,
        missing_source_count=missing_source_count,
        current_cadence_source_count=current_cadence_source_count,
        overdue_source_count=overdue_source_count,
        acknowledged_source_count=acknowledged_source_count,
        unacknowledged_source_count=unacknowledged_source_count,
        source_coverage_ratio=source_coverage_ratio,
        overdue_cadence_coverage_ratio=overdue_cadence_coverage_ratio,
        acknowledged_source_coverage_ratio=acknowledged_source_coverage_ratio,
        max_overdue_age_seconds=_max_overdue_age_seconds(
            overdue_sources,
            generated_at=generated_at,
        ),
        latest_rechecked_at=_latest_datetime(
            tuple(source.last_rechecked_at for source in sources),
        ),
        latest_acknowledged_at=_latest_datetime(
            tuple(
                source.acknowledged_at
                for source in sources
                if source.acknowledged_at is not None
            ),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_coverage_ratio: Decimal,
    overdue_cadence_coverage_ratio: Decimal,
    acknowledged_source_coverage_ratio: Decimal,
    config: TeamMemorySourceRecheckCadenceCoverageConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_coverage_ratio < config.min_source_coverage_ratio:
        reasons.append(SOURCE_GAP_REASON)
    if overdue_cadence_coverage_ratio < config.min_overdue_cadence_coverage_ratio:
        reasons.append(OVERDUE_GAP_REASON)
    if acknowledged_source_coverage_ratio < config.min_acknowledged_source_coverage_ratio:
        reasons.append(ACKNOWLEDGEMENT_GAP_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if SOURCE_GAP_REASON in reason_codes:
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_TEAM_CATEGORIES_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code != CLEAR_REASON
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (NO_TEAM_CATEGORIES_REASON,):
        return "blocked"
    if SOURCE_GAP_REASON in reason_codes:
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _team_category_row_sort_key(
    row: TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow,
) -> tuple[int, str, str]:
    return (STATUS_RANK[row.row_status], row.category_id, row.team_id)


def _normalize_targets(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceCoverageTarget, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_category_targets must be a list or tuple")
    targets = tuple(value)
    seen: set[tuple[str, str]] = set()
    for target in targets:
        if type(target) is not TeamMemorySourceRecheckCadenceCoverageTarget:
            raise ValueError(
                "team_category_targets must contain coverage target values",
            )
        require_paper_only_flags("coverage target", target)
        key = (target.team_id, target.category_id)
        if key in seen:
            raise ValueError("team_category_targets must contain unique pairs")
        seen.add(key)
    return tuple(sorted(targets, key=lambda target: (target.category_id, target.team_id)))


def _normalize_sources(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceCoverageSource, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    sources = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for source in sources:
        if type(source) is not TeamMemorySourceRecheckCadenceCoverageSource:
            raise ValueError(
                "sources must contain TeamMemorySourceRecheckCadenceCoverageSource",
            )
        require_paper_only_flags("coverage source", source)
        if source.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must not be in the future")
        if source.acknowledged_at is not None and source.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at must not be in the future")
        key = (source.team_id, source.category_id, source.source_id)
        if key in seen:
            raise ValueError("source_id values must be unique per team and category")
        seen.add(key)
    return sources


def _normalize_team_category_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_category_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow:
            raise ValueError(
                "team_category_rows must contain coverage team category rows",
            )
        require_paper_only_flags("coverage team category row", row)
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("team_category_rows must contain unique pairs")
        seen.add(key)
    return tuple(sorted(rows, key=_team_category_row_sort_key))


def _normalize_reason_codes(
    value: object,
    *,
    row_scope: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    allowed = ROW_REASON_CODE_SEQUENCE if row_scope else REASON_CODE_SEQUENCE
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in allowed:
            raise ValueError("reason_codes must contain known values")
        index = allowed.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        seen.add(reason_code)
        previous_index = index
    if row_scope and NO_TEAM_CATEGORIES_REASON in reason_codes:
        raise ValueError("row reason_codes cannot use empty group reason")
    if not row_scope and NO_TEAM_CATEGORIES_REASON in reason_codes and reason_codes != (
        NO_TEAM_CATEGORIES_REASON,
    ):
        raise ValueError("empty group reason cannot be combined")
    return reason_codes


def _validate_team_category_row(
    row: TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow,
) -> None:
    if row.source_count > row.expected_source_count:
        expected_missing_source_count = ZERO
    else:
        expected_missing_source_count = row.expected_source_count - row.source_count
    if row.missing_source_count != expected_missing_source_count.quantize(QUANTUM):
        raise ValueError("missing_source_count must match expected and source counts")
    if row.current_cadence_source_count + row.overdue_source_count != row.source_count:
        raise ValueError("cadence source counts must match source_count")
    if row.acknowledged_source_count + row.unacknowledged_source_count != row.source_count:
        raise ValueError("acknowledged source counts must match source_count")
    if row.source_coverage_ratio != _coverage_ratio(
        row.source_count,
        row.expected_source_count,
    ):
        raise ValueError("source_coverage_ratio must match source counts")
    if row.overdue_cadence_coverage_ratio != _coverage_ratio(
        row.current_cadence_source_count,
        row.source_count,
    ):
        raise ValueError("overdue_cadence_coverage_ratio must match source counts")
    if row.acknowledged_source_coverage_ratio != _coverage_ratio(
        row.acknowledged_source_count,
        row.source_count,
    ):
        raise ValueError("acknowledged_source_coverage_ratio must match source counts")
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    if row.source_count == ZERO:
        if row.latest_rechecked_at is not None:
            raise ValueError("latest_rechecked_at requires sources")
        if row.latest_acknowledged_at is not None:
            raise ValueError("latest_acknowledged_at requires sources")


def _validate_report(report: TeamMemorySourceRecheckCadenceCoverageReport) -> None:
    rows = report.team_category_rows
    if report.team_category_count != _decimal_count(len(rows)):
        raise ValueError("team_category_count must match team_category_rows")
    for field_name in (
        "expected_source_count",
        "source_count",
        "missing_source_count",
        "current_cadence_source_count",
        "overdue_source_count",
        "acknowledged_source_count",
        "unacknowledged_source_count",
    ):
        if getattr(report, field_name) != _sum_decimal(rows, field_name):
            raise ValueError(f"{field_name} must match team_category_rows")
    if report.source_coverage_ratio != _coverage_ratio(
        report.source_count,
        report.expected_source_count,
    ):
        raise ValueError("source_coverage_ratio must match counts")
    if report.overdue_cadence_coverage_ratio != _coverage_ratio(
        report.current_cadence_source_count,
        report.source_count,
    ):
        raise ValueError("overdue_cadence_coverage_ratio must match counts")
    if report.acknowledged_source_coverage_ratio != _coverage_ratio(
        report.acknowledged_source_count,
        report.source_count,
    ):
        raise ValueError("acknowledged_source_coverage_ratio must match counts")
    if report.max_overdue_age_seconds != _max_decimal(rows, "max_overdue_age_seconds"):
        raise ValueError("max_overdue_age_seconds must match team_category_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match team_category_rows")
    if report.report_status != _report_status(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _require_row_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains an unsafe fragment")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain surrounding whitespace")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit decimal precision") from exc


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = (numerator_value / denominator_value).quantize(QUANTUM)
    return ONE if ratio > ONE else ratio


def _nonnegative_decimal_difference(left: Decimal, right: Decimal) -> Decimal:
    left_value = _require_nonnegative_decimal("left count", left)
    right_value = _require_nonnegative_decimal("right count", right)
    if right_value >= left_value:
        return ZERO
    return (left_value - right_value).quantize(QUANTUM)


def _sum_decimal(values: tuple[object, ...], field_name: str) -> Decimal:
    total = sum((getattr(value, field_name) for value in values), ZERO)
    return _require_nonnegative_decimal(field_name, total)


def _max_decimal(values: tuple[object, ...], field_name: str) -> Decimal:
    if not values:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(value, field_name))
        for value in values
    ).quantize(QUANTUM)


def _max_overdue_age_seconds(
    sources: tuple[TeamMemorySourceRecheckCadenceCoverageSource, ...],
    *,
    generated_at: datetime,
) -> Decimal:
    if not sources:
        return ZERO
    return max(
        _elapsed_seconds(generated_at, source.next_recheck_due_at)
        for source in sources
    ).quantize(QUANTUM)


def _elapsed_seconds(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    delta = later_utc - earlier_utc
    if delta.days < 0:
        raise ValueError("elapsed seconds must be nonnegative")
    total_microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _latest_datetime(values: tuple[datetime, ...]) -> datetime | None:
    if not values:
        return None
    return max(_as_utc("latest datetime", value) for value in values)


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


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_COVERAGE_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadenceCoverageConfig",
    "TeamMemorySourceRecheckCadenceCoverageReport",
    "TeamMemorySourceRecheckCadenceCoverageSource",
    "TeamMemorySourceRecheckCadenceCoverageTarget",
    "TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow",
    "build_team_memory_source_recheck_cadence_coverage_report",
    "team_memory_source_recheck_cadence_coverage_report_payload",
)
