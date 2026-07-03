from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    TEAM_ID_TO_PRIMARY_CATEGORY,
    TEAM_IDS,
    require_category_id,
    require_team_category_pair,
)


DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_COVERAGE_CONFIG_VERSION = (
    "team-memory-outcome-source-recheck-coverage-v0"
)
DEFAULT_TEAM_CATEGORY_IDS = tuple(
    (team_id, TEAM_ID_TO_PRIMARY_CATEGORY[team_id]) for team_id in TEAM_IDS
)

RATIO_QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

OUTCOME_STATUSES = ("resolved", "unresolved")
COVERAGE_STATUSES = ("pass", "watch", "blocked")
PASS_REASON = "outcome_source_rechecks_covered"
EMPTY_REASON = "outcome_source_rechecks_empty"
MISSING_REASON = "missing_source_rechecks_present"
STALE_REASON = "stale_source_rechecks_present"
UNRESOLVED_REASON = "unresolved_outcomes_missing_current_rechecks"
REASON_CODES = (
    EMPTY_REASON,
    MISSING_REASON,
    PASS_REASON,
    STALE_REASON,
    UNRESOLVED_REASON,
)
REASON_PRIORITY = (
    EMPTY_REASON,
    MISSING_REASON,
    STALE_REASON,
    UNRESOLVED_REASON,
    PASS_REASON,
)


__all__ = (
    "DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_COVERAGE_CONFIG_VERSION",
    "DEFAULT_TEAM_CATEGORY_IDS",
    "TeamMemoryOutcomeSourceRecheckCoverageConfig",
    "TeamMemoryOutcomeSourceRecheckRecord",
    "TeamMemoryOutcomeSourceRecheckTeamRow",
    "TeamMemoryOutcomeSourceRecheckCategoryRow",
    "TeamMemoryOutcomeSourceRecheckCoverageReport",
    "build_team_memory_outcome_source_recheck_coverage_report",
    "team_memory_outcome_source_recheck_coverage_report_to_jsonable",
)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckCoverageConfig:
    config_version: str = (
        DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_COVERAGE_CONFIG_VERSION
    )
    max_recheck_age_seconds: Decimal = Decimal("86400.000000")
    expected_team_categories: tuple[tuple[str, str], ...] = DEFAULT_TEAM_CATEGORY_IDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_recheck_age_seconds",
            _normalize_positive_decimal(
                "max_recheck_age_seconds",
                self.max_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "expected_team_categories",
            _normalize_team_categories(self.expected_team_categories),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckRecord:
    outcome_id: str
    source_id: str
    team_id: str
    category_id: str
    outcome_status: str
    outcome_observed_at: datetime
    rechecked_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("outcome_id", self.outcome_id)
        _require_canonical_string("source_id", self.source_id)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_outcome_status("outcome_status", self.outcome_status)
        object.__setattr__(
            self,
            "outcome_observed_at",
            _as_utc("outcome_observed_at", self.outcome_observed_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_optional_utc("rechecked_at", self.rechecked_at),
        )
        if self.rechecked_at is not None and self.rechecked_at < self.outcome_observed_at:
            raise ValueError("rechecked_at must not be before outcome_observed_at")
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckTeamRow:
    team_id: str
    category_id: str
    source_count: Decimal
    current_source_count: Decimal
    stale_source_count: Decimal
    missing_source_count: Decimal
    unresolved_outcome_count: Decimal
    unresolved_outcome_with_current_recheck_count: Decimal
    stale_unresolved_outcome_count: Decimal
    source_coverage_ratio: Decimal | None
    unresolved_outcome_coverage_ratio: Decimal | None
    stale_recheck_ratio: Decimal | None
    coverage_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _validate_coverage_counts(self)
        _validate_coverage_ratios(self)
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_coverage_shape(self)
        _require_hard_flags("team_row", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckCategoryRow:
    category_id: str
    source_count: Decimal
    current_source_count: Decimal
    stale_source_count: Decimal
    missing_source_count: Decimal
    unresolved_outcome_count: Decimal
    unresolved_outcome_with_current_recheck_count: Decimal
    stale_unresolved_outcome_count: Decimal
    source_coverage_ratio: Decimal | None
    unresolved_outcome_coverage_ratio: Decimal | None
    stale_recheck_ratio: Decimal | None
    coverage_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        _validate_coverage_counts(self)
        _validate_coverage_ratios(self)
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_coverage_shape(self)
        _require_hard_flags("category_row", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckCoverageReport:
    generated_at: datetime
    config_version: str
    coverage_status: str
    source_count: Decimal
    current_source_count: Decimal
    stale_source_count: Decimal
    missing_source_count: Decimal
    unresolved_outcome_count: Decimal
    unresolved_outcome_with_current_recheck_count: Decimal
    stale_unresolved_outcome_count: Decimal
    source_coverage_ratio: Decimal | None
    unresolved_outcome_coverage_ratio: Decimal | None
    stale_recheck_ratio: Decimal | None
    team_count: Decimal
    category_count: Decimal
    latest_rechecked_at: datetime | None
    team_rows: tuple[TeamMemoryOutcomeSourceRecheckTeamRow, ...]
    category_rows: tuple[TeamMemoryOutcomeSourceRecheckCategoryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_coverage_status("coverage_status", self.coverage_status)
        _validate_coverage_counts(self)
        _validate_coverage_ratios(self)
        object.__setattr__(
            self,
            "team_count",
            _normalize_nonnegative_whole_decimal("team_count", self.team_count),
        )
        object.__setattr__(
            self,
            "category_count",
            _normalize_nonnegative_whole_decimal("category_count", self.category_count),
        )
        object.__setattr__(
            self,
            "latest_rechecked_at",
            _as_optional_utc("latest_rechecked_at", self.latest_rechecked_at),
        )
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        object.__setattr__(
            self,
            "category_rows",
            _normalize_category_rows(self.category_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_memory_outcome_source_recheck_coverage_report(
    records: list[TeamMemoryOutcomeSourceRecheckRecord]
    | tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    *,
    config: TeamMemoryOutcomeSourceRecheckCoverageConfig,
    generated_at: datetime,
) -> TeamMemoryOutcomeSourceRecheckCoverageReport:
    if type(config) is not TeamMemoryOutcomeSourceRecheckCoverageConfig:
        raise ValueError(
            "config must be a TeamMemoryOutcomeSourceRecheckCoverageConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_records = _normalize_records(records)
    _validate_record_scope(
        normalized_records,
        expected_team_categories=config.expected_team_categories,
    )
    _validate_record_timing(normalized_records, generated_at=generated_at_utc)

    team_rows = _team_rows(
        normalized_records,
        expected_team_categories=config.expected_team_categories,
        generated_at=generated_at_utc,
        max_recheck_age_seconds=config.max_recheck_age_seconds,
    )
    category_rows = _category_rows(team_rows)
    reason_codes = _reason_codes(
        source_count=sum((row.source_count for row in team_rows), ZERO_COUNT),
        missing_source_count=sum(
            (row.missing_source_count for row in team_rows),
            ZERO_COUNT,
        ),
        stale_source_count=sum(
            (row.stale_source_count for row in team_rows),
            ZERO_COUNT,
        ),
        unresolved_outcome_count=sum(
            (row.unresolved_outcome_count for row in team_rows),
            ZERO_COUNT,
        ),
        unresolved_outcome_with_current_recheck_count=sum(
            (
                row.unresolved_outcome_with_current_recheck_count
                for row in team_rows
            ),
            ZERO_COUNT,
        ),
    )
    source_count = sum((row.source_count for row in team_rows), ZERO_COUNT)
    current_source_count = sum(
        (row.current_source_count for row in team_rows),
        ZERO_COUNT,
    )
    stale_source_count = sum((row.stale_source_count for row in team_rows), ZERO_COUNT)
    missing_source_count = sum(
        (row.missing_source_count for row in team_rows),
        ZERO_COUNT,
    )
    unresolved_outcome_count = sum(
        (row.unresolved_outcome_count for row in team_rows),
        ZERO_COUNT,
    )
    unresolved_outcome_with_current_recheck_count = sum(
        (row.unresolved_outcome_with_current_recheck_count for row in team_rows),
        ZERO_COUNT,
    )
    stale_unresolved_outcome_count = sum(
        (row.stale_unresolved_outcome_count for row in team_rows),
        ZERO_COUNT,
    )

    return TeamMemoryOutcomeSourceRecheckCoverageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        coverage_status=_coverage_status(reason_codes),
        source_count=source_count,
        current_source_count=current_source_count,
        stale_source_count=stale_source_count,
        missing_source_count=missing_source_count,
        unresolved_outcome_count=unresolved_outcome_count,
        unresolved_outcome_with_current_recheck_count=(
            unresolved_outcome_with_current_recheck_count
        ),
        stale_unresolved_outcome_count=stale_unresolved_outcome_count,
        source_coverage_ratio=_ratio_or_none(current_source_count, source_count),
        unresolved_outcome_coverage_ratio=_ratio_or_none(
            unresolved_outcome_with_current_recheck_count,
            unresolved_outcome_count,
        ),
        stale_recheck_ratio=_ratio_or_none(stale_source_count, source_count),
        team_count=_whole_decimal(len(team_rows)),
        category_count=_whole_decimal(len(category_rows)),
        latest_rechecked_at=_latest_rechecked_at(normalized_records),
        team_rows=team_rows,
        category_rows=category_rows,
        reason_codes=reason_codes,
    )


def team_memory_outcome_source_recheck_coverage_report_to_jsonable(
    report: TeamMemoryOutcomeSourceRecheckCoverageReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryOutcomeSourceRecheckCoverageReport:
        raise ValueError(
            "report must be a TeamMemoryOutcomeSourceRecheckCoverageReport",
        )
    require_paper_only_flags("TeamMemoryOutcomeSourceRecheckCoverageReport", report)
    _require_report_surface_flags(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    reject_unsafe_surface_fields(
        "team memory outcome source recheck coverage payload",
        payload,
    )
    _reject_runtime_surface_fields(
        "team memory outcome source recheck coverage payload",
        payload,
    )
    return payload


def _require_report_surface_flags(
    report: TeamMemoryOutcomeSourceRecheckCoverageReport,
) -> None:
    for row in report.team_rows:
        require_paper_only_flags("TeamMemoryOutcomeSourceRecheckTeamRow", row)
    for row in report.category_rows:
        require_paper_only_flags("TeamMemoryOutcomeSourceRecheckCategoryRow", row)


def _reject_runtime_surface_fields(label: str, payload: object) -> None:
    unsafe_fragments = ("li" "ve", "execution")
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in unsafe_fragments):
            surface = "li" "ve"
            raise ValueError(f"unsafe {surface} surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _team_rows(
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    *,
    expected_team_categories: tuple[tuple[str, str], ...],
    generated_at: datetime,
    max_recheck_age_seconds: Decimal,
) -> tuple[TeamMemoryOutcomeSourceRecheckTeamRow, ...]:
    pairs = {
        (record.team_id, record.category_id)
        for record in records
    }
    return tuple(
        _team_row(
            team_id=team_id,
            category_id=category_id,
            records=tuple(
                record
                for record in records
                if record.team_id == team_id and record.category_id == category_id
            ),
            generated_at=generated_at,
            max_recheck_age_seconds=max_recheck_age_seconds,
        )
        for team_id, category_id in sorted(pairs, key=lambda pair: (pair[1], pair[0]))
    )


def _validate_record_scope(
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    *,
    expected_team_categories: tuple[tuple[str, str], ...],
) -> None:
    expected = frozenset(expected_team_categories)
    if not expected:
        return
    for record in records:
        if (record.team_id, record.category_id) not in expected:
            raise ValueError("record team_id and category_id must be configured")


def _team_row(
    *,
    team_id: str,
    category_id: str,
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    generated_at: datetime,
    max_recheck_age_seconds: Decimal,
) -> TeamMemoryOutcomeSourceRecheckTeamRow:
    statuses = tuple(
        _recheck_status(
            record,
            generated_at=generated_at,
            max_recheck_age_seconds=max_recheck_age_seconds,
        )
        for record in records
    )
    current_source_count = sum(1 for status in statuses if status == "current")
    stale_source_count = sum(1 for status in statuses if status == "stale")
    missing_source_count = sum(1 for status in statuses if status == "missing")
    unresolved_outcome_ids = _outcome_ids(records, status="unresolved")
    current_unresolved_outcome_ids = _outcome_ids_with_recheck_status(
        records,
        recheck_statuses=statuses,
        outcome_status="unresolved",
        recheck_status="current",
    )
    stale_unresolved_outcome_ids = _outcome_ids_with_recheck_status(
        records,
        recheck_statuses=statuses,
        outcome_status="unresolved",
        recheck_status="stale",
    ) - current_unresolved_outcome_ids
    reason_codes = _reason_codes(
        source_count=_whole_decimal(len(records)),
        missing_source_count=_whole_decimal(missing_source_count),
        stale_source_count=_whole_decimal(stale_source_count),
        unresolved_outcome_count=_whole_decimal(len(unresolved_outcome_ids)),
        unresolved_outcome_with_current_recheck_count=_whole_decimal(
            len(current_unresolved_outcome_ids),
        ),
    )
    return TeamMemoryOutcomeSourceRecheckTeamRow(
        team_id=team_id,
        category_id=category_id,
        source_count=_whole_decimal(len(records)),
        current_source_count=_whole_decimal(current_source_count),
        stale_source_count=_whole_decimal(stale_source_count),
        missing_source_count=_whole_decimal(missing_source_count),
        unresolved_outcome_count=_whole_decimal(len(unresolved_outcome_ids)),
        unresolved_outcome_with_current_recheck_count=_whole_decimal(
            len(current_unresolved_outcome_ids),
        ),
        stale_unresolved_outcome_count=_whole_decimal(
            len(stale_unresolved_outcome_ids),
        ),
        source_coverage_ratio=_ratio_or_none(
            _whole_decimal(current_source_count),
            _whole_decimal(len(records)),
        ),
        unresolved_outcome_coverage_ratio=_ratio_or_none(
            _whole_decimal(len(current_unresolved_outcome_ids)),
            _whole_decimal(len(unresolved_outcome_ids)),
        ),
        stale_recheck_ratio=_ratio_or_none(
            _whole_decimal(stale_source_count),
            _whole_decimal(len(records)),
        ),
        coverage_status=_coverage_status(reason_codes),
        reason_codes=reason_codes,
    )


def _category_rows(
    team_rows: tuple[TeamMemoryOutcomeSourceRecheckTeamRow, ...],
) -> tuple[TeamMemoryOutcomeSourceRecheckCategoryRow, ...]:
    category_ids = tuple(sorted({row.category_id for row in team_rows}))
    rows = []
    for category_id in category_ids:
        rows_for_category = tuple(row for row in team_rows if row.category_id == category_id)
        source_count = sum(
            (row.source_count for row in rows_for_category),
            ZERO_COUNT,
        )
        current_source_count = sum(
            (row.current_source_count for row in rows_for_category),
            ZERO_COUNT,
        )
        stale_source_count = sum(
            (row.stale_source_count for row in rows_for_category),
            ZERO_COUNT,
        )
        missing_source_count = sum(
            (row.missing_source_count for row in rows_for_category),
            ZERO_COUNT,
        )
        unresolved_outcome_count = sum(
            (row.unresolved_outcome_count for row in rows_for_category),
            ZERO_COUNT,
        )
        unresolved_outcome_with_current_recheck_count = sum(
            (
                row.unresolved_outcome_with_current_recheck_count
                for row in rows_for_category
            ),
            ZERO_COUNT,
        )
        stale_unresolved_outcome_count = sum(
            (row.stale_unresolved_outcome_count for row in rows_for_category),
            ZERO_COUNT,
        )
        reason_codes = _reason_codes(
            source_count=source_count,
            missing_source_count=missing_source_count,
            stale_source_count=stale_source_count,
            unresolved_outcome_count=unresolved_outcome_count,
            unresolved_outcome_with_current_recheck_count=(
                unresolved_outcome_with_current_recheck_count
            ),
        )
        rows.append(
            TeamMemoryOutcomeSourceRecheckCategoryRow(
                category_id=category_id,
                source_count=source_count,
                current_source_count=current_source_count,
                stale_source_count=stale_source_count,
                missing_source_count=missing_source_count,
                unresolved_outcome_count=unresolved_outcome_count,
                unresolved_outcome_with_current_recheck_count=(
                    unresolved_outcome_with_current_recheck_count
                ),
                stale_unresolved_outcome_count=stale_unresolved_outcome_count,
                source_coverage_ratio=_ratio_or_none(current_source_count, source_count),
                unresolved_outcome_coverage_ratio=_ratio_or_none(
                    unresolved_outcome_with_current_recheck_count,
                    unresolved_outcome_count,
                ),
                stale_recheck_ratio=_ratio_or_none(stale_source_count, source_count),
                coverage_status=_coverage_status(reason_codes),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _recheck_status(
    record: TeamMemoryOutcomeSourceRecheckRecord,
    *,
    generated_at: datetime,
    max_recheck_age_seconds: Decimal,
) -> str:
    if record.rechecked_at is None:
        return "missing"
    age_seconds = _age_seconds(generated_at, record.rechecked_at)
    if age_seconds > max_recheck_age_seconds:
        return "stale"
    return "current"


def _outcome_ids(
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    *,
    status: str,
) -> frozenset[str]:
    return frozenset(record.outcome_id for record in records if record.outcome_status == status)


def _outcome_ids_with_recheck_status(
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    *,
    recheck_statuses: tuple[str, ...],
    outcome_status: str,
    recheck_status: str,
) -> frozenset[str]:
    return frozenset(
        record.outcome_id
        for record, status in zip(records, recheck_statuses, strict=True)
        if record.outcome_status == outcome_status and status == recheck_status
    )


def _reason_codes(
    *,
    source_count: Decimal,
    missing_source_count: Decimal,
    stale_source_count: Decimal,
    unresolved_outcome_count: Decimal,
    unresolved_outcome_with_current_recheck_count: Decimal,
) -> tuple[str, ...]:
    if source_count == ZERO_COUNT:
        return (EMPTY_REASON,)
    codes = []
    if missing_source_count > ZERO_COUNT:
        codes.append(MISSING_REASON)
    if stale_source_count > ZERO_COUNT:
        codes.append(STALE_REASON)
    if unresolved_outcome_with_current_recheck_count < unresolved_outcome_count:
        codes.append(UNRESOLVED_REASON)
    if not codes:
        codes.append(PASS_REASON)
    return tuple(code for code in REASON_PRIORITY if code in codes)


def _coverage_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in (EMPTY_REASON, MISSING_REASON, UNRESOLVED_REASON)
        for reason_code in reason_codes
    ):
        return "blocked"
    if STALE_REASON in reason_codes:
        return "watch"
    if reason_codes == (PASS_REASON,):
        return "pass"
    raise ValueError("reason_codes must contain known coverage reasons")


def _normalize_records(
    records: list[TeamMemoryOutcomeSourceRecheckRecord]
    | tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
) -> tuple[TeamMemoryOutcomeSourceRecheckRecord, ...]:
    if type(records) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    normalized = tuple(records)
    seen_source_keys: set[tuple[str, str]] = set()
    outcome_shapes: dict[str, tuple[str, str, str, datetime]] = {}
    for record in normalized:
        if type(record) is not TeamMemoryOutcomeSourceRecheckRecord:
            raise ValueError(
                "records must contain TeamMemoryOutcomeSourceRecheckRecord values",
            )
        _require_hard_flags("record", record)
        source_key = (record.outcome_id, record.source_id)
        if source_key in seen_source_keys:
            raise ValueError("outcome_id and source_id pairs must be unique")
        seen_source_keys.add(source_key)
        outcome_shape = (
            record.team_id,
            record.category_id,
            record.outcome_status,
            record.outcome_observed_at,
        )
        existing = outcome_shapes.get(record.outcome_id)
        if existing is None:
            outcome_shapes[record.outcome_id] = outcome_shape
        elif existing != outcome_shape:
            raise ValueError("outcome_id values must keep one outcome shape")
    return tuple(
        sorted(
            normalized,
            key=lambda record: (
                record.category_id,
                record.team_id,
                record.outcome_id,
                record.source_id,
            ),
        ),
    )


def _validate_record_timing(
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
    *,
    generated_at: datetime,
) -> None:
    for record in records:
        if record.outcome_observed_at > generated_at:
            raise ValueError("outcome_observed_at must not be in the future")
        if record.rechecked_at is not None and record.rechecked_at > generated_at:
            raise ValueError("rechecked_at must not be in the future")


def _normalize_team_categories(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("expected_team_categories must contain team/category pairs")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "expected_team_categories must contain team/category pairs",
        ) from exc
    normalized = []
    seen_team_ids: set[str] = set()
    seen_category_ids: set[str] = set()
    for item in items:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError(
                "expected_team_categories entries must be team/category pairs",
            )
        team_id, category_id = require_team_category_pair(
            "team_id",
            item[0],
            "category_id",
            item[1],
        )
        if team_id in seen_team_ids:
            raise ValueError("expected_team_categories team_id values must be unique")
        if category_id in seen_category_ids:
            raise ValueError("expected_team_categories category_id values must be unique")
        seen_team_ids.add(team_id)
        seen_category_ids.add(category_id)
        normalized.append((team_id, category_id))
    return tuple(sorted(normalized, key=lambda pair: (pair[1], pair[0])))


def _normalize_team_rows(
    value: tuple[TeamMemoryOutcomeSourceRecheckTeamRow, ...],
) -> tuple[TeamMemoryOutcomeSourceRecheckTeamRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_rows must be a list or tuple")
    rows = tuple(value)
    seen_team_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamMemoryOutcomeSourceRecheckTeamRow:
            raise ValueError(
                "team_rows must contain TeamMemoryOutcomeSourceRecheckTeamRow values",
            )
        _require_hard_flags("team_row", row)
        if row.team_id in seen_team_ids:
            raise ValueError("team_rows team_id values must be unique")
        seen_team_ids.add(row.team_id)
    if rows != tuple(sorted(rows, key=lambda row: (row.category_id, row.team_id))):
        raise ValueError("team_rows must be sorted by category_id and team_id")
    return rows


def _normalize_category_rows(
    value: tuple[TeamMemoryOutcomeSourceRecheckCategoryRow, ...],
) -> tuple[TeamMemoryOutcomeSourceRecheckCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("category_rows must be a list or tuple")
    rows = tuple(value)
    seen_category_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamMemoryOutcomeSourceRecheckCategoryRow:
            raise ValueError(
                "category_rows must contain TeamMemoryOutcomeSourceRecheckCategoryRow values",
            )
        _require_hard_flags("category_row", row)
        if row.category_id in seen_category_ids:
            raise ValueError("category_rows category_id values must be unique")
        seen_category_ids.add(row.category_id)
    if rows != tuple(sorted(rows, key=lambda row: row.category_id)):
        raise ValueError("category_rows must be sorted by category_id")
    return rows


def _validate_coverage_counts(value: object) -> None:
    for field_name in (
        "source_count",
        "current_source_count",
        "stale_source_count",
        "missing_source_count",
        "unresolved_outcome_count",
        "unresolved_outcome_with_current_recheck_count",
        "stale_unresolved_outcome_count",
    ):
        object.__setattr__(
            value,
            field_name,
            _normalize_nonnegative_whole_decimal(field_name, getattr(value, field_name)),
        )
    if (
        value.current_source_count
        + value.stale_source_count
        + value.missing_source_count
        != value.source_count
    ):
        raise ValueError("current_source_count, stale_source_count, and missing_source_count must match source_count")
    if (
        value.unresolved_outcome_with_current_recheck_count
        > value.unresolved_outcome_count
    ):
        raise ValueError(
            "unresolved_outcome_with_current_recheck_count must not exceed unresolved_outcome_count",
        )
    if value.stale_unresolved_outcome_count > value.unresolved_outcome_count:
        raise ValueError(
            "stale_unresolved_outcome_count must not exceed unresolved_outcome_count",
        )


def _validate_coverage_ratios(value: object) -> None:
    _require_optional_ratio("source_coverage_ratio", value.source_coverage_ratio)
    _require_optional_ratio(
        "unresolved_outcome_coverage_ratio",
        value.unresolved_outcome_coverage_ratio,
    )
    _require_optional_ratio("stale_recheck_ratio", value.stale_recheck_ratio)
    if value.source_coverage_ratio != _ratio_or_none(
        value.current_source_count,
        value.source_count,
    ):
        raise ValueError("source_coverage_ratio must match source counts")
    if value.unresolved_outcome_coverage_ratio != _ratio_or_none(
        value.unresolved_outcome_with_current_recheck_count,
        value.unresolved_outcome_count,
    ):
        raise ValueError(
            "unresolved_outcome_coverage_ratio must match unresolved outcome counts",
        )
    if value.stale_recheck_ratio != _ratio_or_none(
        value.stale_source_count,
        value.source_count,
    ):
        raise ValueError("stale_recheck_ratio must match stale and source counts")


def _validate_coverage_shape(value: object) -> None:
    expected_reason_codes = _reason_codes(
        source_count=value.source_count,
        missing_source_count=value.missing_source_count,
        stale_source_count=value.stale_source_count,
        unresolved_outcome_count=value.unresolved_outcome_count,
        unresolved_outcome_with_current_recheck_count=(
            value.unresolved_outcome_with_current_recheck_count
        ),
    )
    if value.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match coverage inputs")
    if value.coverage_status != _coverage_status(value.reason_codes):
        raise ValueError("coverage_status must match reason_codes")


def _validate_report_consistency(
    report: TeamMemoryOutcomeSourceRecheckCoverageReport,
) -> None:
    if report.team_count != _whole_decimal(len(report.team_rows)):
        raise ValueError("team_count must match team_rows")
    if report.category_count != _whole_decimal(len(report.category_rows)):
        raise ValueError("category_count must match category_rows")
    if report.category_count != _whole_decimal(
        len({row.category_id for row in report.team_rows}),
    ):
        raise ValueError("category_count must match team_rows")
    for field_name in (
        "source_count",
        "current_source_count",
        "stale_source_count",
        "missing_source_count",
        "unresolved_outcome_count",
        "unresolved_outcome_with_current_recheck_count",
        "stale_unresolved_outcome_count",
    ):
        if getattr(report, field_name) != sum(
            (getattr(row, field_name) for row in report.team_rows),
            ZERO_COUNT,
        ):
            raise ValueError(f"{field_name} must match team_rows")
    expected_category_rows = _category_rows(report.team_rows)
    if report.category_rows != expected_category_rows:
        raise ValueError("category_rows must match team_rows")
    _validate_coverage_shape(report)


def _latest_rechecked_at(
    records: tuple[TeamMemoryOutcomeSourceRecheckRecord, ...],
) -> datetime | None:
    values = tuple(record.rechecked_at for record in records if record.rechecked_at is not None)
    if not values:
        return None
    return max(values)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("observed_at", observed_at)
    seconds = (Decimal(delta.days) * SECONDS_PER_DAY) + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return (seconds + microseconds).quantize(SECOND_QUANTUM)


def _ratio_or_none(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO_COUNT:
        return None
    return (numerator / denominator).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_outcome_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in OUTCOME_STATUSES:
        raise ValueError(f"{field_name} must be resolved or unresolved")


def _require_coverage_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in COVERAGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must contain at least one value")
    for code in codes:
        _require_canonical_string("reason_codes", code)
        if code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if codes != tuple(code for code in REASON_PRIORITY if code in codes):
        raise ValueError("reason_codes must use canonical sequence")
    return codes


def _require_optional_ratio(field_name: str, value: Any) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    if value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be quantized to six decimal places")


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _whole_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
