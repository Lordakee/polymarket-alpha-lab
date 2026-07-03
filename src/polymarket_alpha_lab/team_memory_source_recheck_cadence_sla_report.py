"""Pure in-memory SLA report for team memory source recheck cadence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_SLA_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-sla-v0"
)

EMPTY_REASON = "team_memory_source_recheck_cadence_sla_empty_sources"
CLEAR_REASON = "team_memory_source_recheck_cadence_sla_clear"
OVERDUE_REASON = "team_memory_source_recheck_cadence_sla_overdue_cadence"
MISSING_OWNER_REASON = "team_memory_source_recheck_cadence_sla_missing_owner"
CONCENTRATION_REASON = (
    "team_memory_source_recheck_cadence_sla_source_family_concentration"
)
MISSING_REVIEWER_ACKNOWLEDGEMENT_REASON = (
    "team_memory_source_recheck_cadence_sla_missing_reviewer_acknowledgement"
)
REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    OVERDUE_REASON,
    MISSING_OWNER_REASON,
    CONCENTRATION_REASON,
    MISSING_REVIEWER_ACKNOWLEDGEMENT_REASON,
    CLEAR_REASON,
)
BLOCKING_REASONS = frozenset(
    (
        EMPTY_REASON,
        OVERDUE_REASON,
        MISSING_OWNER_REASON,
        MISSING_REVIEWER_ACKNOWLEDGEMENT_REASON,
    ),
)
SLA_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cre", "den", "tial"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSlaConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_SLA_CONFIG_VERSION
    source_family_concentration_threshold_ratio: Decimal = Decimal("0.666667")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "source_family_concentration_threshold_ratio",
            _require_ratio(
                "source_family_concentration_threshold_ratio",
                self.source_family_concentration_threshold_ratio,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSlaInputRow:
    team_id: str
    category_id: str
    source_id: str
    source_family: str
    owner_id: str | None
    last_rechecked_at: datetime
    next_recheck_due_at: datetime
    reviewer_acknowledged_at: datetime | None = None
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
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "owner_id",
            _normalize_optional_public_string("owner_id", self.owner_id),
        )
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
        if self.next_recheck_due_at < self.last_rechecked_at:
            raise ValueError("next_recheck_due_at must not precede last_rechecked_at")
        object.__setattr__(
            self,
            "reviewer_acknowledged_at",
            _as_optional_utc(
                "reviewer_acknowledged_at",
                self.reviewer_acknowledged_at,
            ),
        )
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSlaTeamCategoryRow:
    category_id: str
    team_id: str
    sla_status: str
    source_count: Decimal
    source_family_count: Decimal
    dominant_source_family: str | None
    dominant_source_family_count: Decimal
    source_family_concentration_ratio: Decimal
    overdue_source_count: Decimal
    missing_owner_count: Decimal
    missing_reviewer_acknowledgement_count: Decimal
    max_recheck_overdue_age_seconds: Decimal
    max_last_recheck_age_seconds: Decimal
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
        _require_sla_status("sla_status", self.sla_status)
        for field_name in (
            "source_count",
            "source_family_count",
            "dominant_source_family_count",
            "source_family_concentration_ratio",
            "overdue_source_count",
            "missing_owner_count",
            "missing_reviewer_acknowledgement_count",
            "max_recheck_overdue_age_seconds",
            "max_last_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.source_family_concentration_ratio > Decimal("1.000000"):
            raise ValueError("source_family_concentration_ratio must not exceed one")
        object.__setattr__(
            self,
            "dominant_source_family",
            _normalize_optional_public_string(
                "dominant_source_family",
                self.dominant_source_family,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_team_category_row(self)
        require_paper_only_flags("team category row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSlaReport:
    generated_at: datetime
    config_version: str
    sla_status: str
    team_category_count: Decimal
    source_count: Decimal
    overdue_source_count: Decimal
    missing_owner_count: Decimal
    source_family_concentration_count: Decimal
    missing_reviewer_acknowledgement_count: Decimal
    max_recheck_overdue_age_seconds: Decimal
    max_last_recheck_age_seconds: Decimal
    max_source_family_concentration_ratio: Decimal
    team_category_rows: tuple[TeamMemorySourceRecheckCadenceSlaTeamCategoryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_sla_status("sla_status", self.sla_status)
        for field_name in (
            "team_category_count",
            "source_count",
            "overdue_source_count",
            "missing_owner_count",
            "source_family_concentration_count",
            "missing_reviewer_acknowledgement_count",
            "max_recheck_overdue_age_seconds",
            "max_last_recheck_age_seconds",
            "max_source_family_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_source_family_concentration_ratio > Decimal("1.000000"):
            raise ValueError("max_source_family_concentration_ratio must not exceed one")
        object.__setattr__(
            self,
            "team_category_rows",
            _normalize_team_category_rows(self.team_category_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_team_memory_source_recheck_cadence_sla_report(
    input_rows: list[TeamMemorySourceRecheckCadenceSlaInputRow]
    | tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...],
    *,
    config: TeamMemorySourceRecheckCadenceSlaConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceSlaReport:
    if type(config) is not TeamMemorySourceRecheckCadenceSlaConfig:
        raise ValueError("config must be a TeamMemorySourceRecheckCadenceSlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    team_category_rows = _team_category_rows(
        rows,
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(team_category_rows)
    return TeamMemorySourceRecheckCadenceSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        sla_status=_status_from_reason_codes(reason_codes),
        team_category_count=_decimal_count(len(team_category_rows)),
        source_count=_sum_decimal(team_category_rows, "source_count"),
        overdue_source_count=_sum_decimal(team_category_rows, "overdue_source_count"),
        missing_owner_count=_sum_decimal(team_category_rows, "missing_owner_count"),
        source_family_concentration_count=_decimal_count(
            sum(
                CONCENTRATION_REASON in row.reason_codes
                for row in team_category_rows
            ),
        ),
        missing_reviewer_acknowledgement_count=_sum_decimal(
            team_category_rows,
            "missing_reviewer_acknowledgement_count",
        ),
        max_recheck_overdue_age_seconds=_max_decimal(
            team_category_rows,
            "max_recheck_overdue_age_seconds",
        ),
        max_last_recheck_age_seconds=_max_decimal(
            team_category_rows,
            "max_last_recheck_age_seconds",
        ),
        max_source_family_concentration_ratio=_max_decimal(
            team_category_rows,
            "source_family_concentration_ratio",
        ),
        team_category_rows=team_category_rows,
        reason_codes=reason_codes,
    )


def team_memory_source_recheck_cadence_sla_report_payload(
    report: TeamMemorySourceRecheckCadenceSlaReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceSlaReport:
        raise ValueError("report must be a TeamMemorySourceRecheckCadenceSlaReport")
    require_paper_only_flags("report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report must reduce to a JSON object")
    reject_unsafe_surface_fields(
        "team_memory_source_recheck_cadence_sla_report",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceSlaInputRow:
            raise ValueError(
                "input rows must contain TeamMemorySourceRecheckCadenceSlaInputRow",
            )
        require_paper_only_flags("input row", row)
        if row.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must not be in the future")
        if (
            row.reviewer_acknowledged_at is not None
            and row.reviewer_acknowledged_at > generated_at
        ):
            raise ValueError("reviewer_acknowledged_at must not be in the future")
        key = (row.category_id, row.team_id, row.source_id)
        if key in seen:
            raise ValueError("source_id values must be unique per team and category")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.category_id,
                row.team_id,
                row.source_family,
                row.source_id,
            ),
        ),
    )


def _team_category_rows(
    rows: tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...],
    *,
    config: TeamMemorySourceRecheckCadenceSlaConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceSlaTeamCategoryRow, ...]:
    groups: dict[tuple[str, str], list[TeamMemorySourceRecheckCadenceSlaInputRow]] = {}
    for row in rows:
        groups.setdefault((row.category_id, row.team_id), []).append(row)
    return tuple(
        sorted(
            (
                _team_category_row(
                    category_id=category_id,
                    team_id=team_id,
                    rows=tuple(group_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for (category_id, team_id), group_rows in groups.items()
            ),
            key=lambda row: (
                STATUS_RANK[row.sla_status],
                row.category_id,
                row.team_id,
            ),
        ),
    )


def _team_category_row(
    *,
    category_id: str,
    team_id: str,
    rows: tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...],
    config: TeamMemorySourceRecheckCadenceSlaConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceSlaTeamCategoryRow:
    family_counts = _family_counts(rows)
    dominant_source_family, dominant_source_family_count = _dominant_family(family_counts)
    source_count = _decimal_count(len(rows))
    source_family_count = _decimal_count(len(family_counts))
    concentration_ratio = _ratio(dominant_source_family_count, source_count)
    overdue_rows = tuple(row for row in rows if row.next_recheck_due_at < generated_at)
    reason_codes = _team_reason_codes(
        overdue_source_count=_decimal_count(len(overdue_rows)),
        missing_owner_count=_decimal_count(sum(row.owner_id is None for row in rows)),
        concentration_ratio=concentration_ratio,
        source_family_concentration_threshold_ratio=(
            config.source_family_concentration_threshold_ratio
        ),
        missing_reviewer_acknowledgement_count=_decimal_count(
            sum(row.reviewer_acknowledged_at is None for row in rows),
        ),
    )
    return TeamMemorySourceRecheckCadenceSlaTeamCategoryRow(
        category_id=category_id,
        team_id=team_id,
        sla_status=_status_from_reason_codes(reason_codes),
        source_count=source_count,
        source_family_count=source_family_count,
        dominant_source_family=dominant_source_family,
        dominant_source_family_count=dominant_source_family_count,
        source_family_concentration_ratio=concentration_ratio,
        overdue_source_count=_decimal_count(len(overdue_rows)),
        missing_owner_count=_decimal_count(sum(row.owner_id is None for row in rows)),
        missing_reviewer_acknowledgement_count=_decimal_count(
            sum(row.reviewer_acknowledged_at is None for row in rows),
        ),
        max_recheck_overdue_age_seconds=_max_recheck_overdue_age_seconds(
            overdue_rows,
            generated_at=generated_at,
        ),
        max_last_recheck_age_seconds=_max_last_recheck_age_seconds(
            rows,
            generated_at=generated_at,
        ),
        reason_codes=reason_codes,
    )


def _family_counts(
    rows: tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...],
) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        counts[row.source_family] = (counts.get(row.source_family, ZERO) + Decimal("1")).quantize(
            QUANTUM,
        )
    return counts


def _dominant_family(family_counts: dict[str, Decimal]) -> tuple[str | None, Decimal]:
    if not family_counts:
        return None, ZERO
    family_name, count = sorted(
        family_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]
    return family_name, count


def _team_reason_codes(
    *,
    overdue_source_count: Decimal,
    missing_owner_count: Decimal,
    concentration_ratio: Decimal,
    source_family_concentration_threshold_ratio: Decimal,
    missing_reviewer_acknowledgement_count: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if overdue_source_count > ZERO:
        reasons.append(OVERDUE_REASON)
    if missing_owner_count > ZERO:
        reasons.append(MISSING_OWNER_REASON)
    if concentration_ratio > source_family_concentration_threshold_ratio:
        reasons.append(CONCENTRATION_REASON)
    if missing_reviewer_acknowledgement_count > ZERO:
        reasons.append(MISSING_REVIEWER_ACKNOWLEDGEMENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _report_reason_codes(
    rows: tuple[TeamMemorySourceRecheckCadenceSlaTeamCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code not in (EMPTY_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _max_recheck_overdue_age_seconds(
    rows: tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...],
    *,
    generated_at: datetime,
) -> Decimal:
    if not rows:
        return ZERO
    return max(
        _age_seconds(generated_at, row.next_recheck_due_at)
        for row in rows
    ).quantize(QUANTUM)


def _max_last_recheck_age_seconds(
    rows: tuple[TeamMemorySourceRecheckCadenceSlaInputRow, ...],
    *,
    generated_at: datetime,
) -> Decimal:
    if not rows:
        return ZERO
    return max(_age_seconds(generated_at, row.last_rechecked_at) for row in rows).quantize(
        QUANTUM,
    )


def _age_seconds(generated_at: datetime, value: datetime) -> Decimal:
    delta = generated_at - value
    if delta.days < 0:
        raise ValueError("age seconds must not be negative")
    total_microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANTUM)


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


def _normalize_team_category_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceSlaTeamCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_category_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[int, str, str] | None = None
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceSlaTeamCategoryRow:
            raise ValueError(
                "team_category_rows must contain TeamMemorySourceRecheckCadenceSlaTeamCategoryRow",
            )
        require_paper_only_flags("team category row", row)
        key = (row.category_id, row.team_id)
        if key in seen:
            raise ValueError("team_category_rows must contain unique team and category pairs")
        seen.add(key)
        sort_key = (STATUS_RANK[row.sla_status], row.category_id, row.team_id)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("team_category_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        index = REASON_CODE_SEQUENCE.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        seen.add(reason_code)
        previous_index = index
    return reason_codes


def _validate_team_category_row(
    row: TeamMemorySourceRecheckCadenceSlaTeamCategoryRow,
) -> None:
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if row.dominant_source_family is None:
        if row.dominant_source_family_count != ZERO:
            raise ValueError("dominant_source_family_count must be zero without a family")
    elif row.dominant_source_family_count <= ZERO:
        raise ValueError("dominant_source_family_count must be positive with a family")
    if row.dominant_source_family_count > row.source_count:
        raise ValueError("dominant_source_family_count must not exceed source_count")
    if row.source_family_concentration_ratio != _ratio(
        row.dominant_source_family_count,
        row.source_count,
    ):
        raise ValueError("source_family_concentration_ratio must match source counts")
    if row.overdue_source_count > row.source_count:
        raise ValueError("overdue_source_count must not exceed source_count")
    if row.missing_owner_count > row.source_count:
        raise ValueError("missing_owner_count must not exceed source_count")
    if row.missing_reviewer_acknowledgement_count > row.source_count:
        raise ValueError(
            "missing_reviewer_acknowledgement_count must not exceed source_count",
        )
    if row.sla_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("sla_status must match reason_codes")


def _validate_report(report: TeamMemorySourceRecheckCadenceSlaReport) -> None:
    if report.team_category_count != _decimal_count(len(report.team_category_rows)):
        raise ValueError("team_category_count must match team_category_rows")
    if report.source_count != _sum_decimal(report.team_category_rows, "source_count"):
        raise ValueError("source_count must match team_category_rows")
    if report.overdue_source_count != _sum_decimal(
        report.team_category_rows,
        "overdue_source_count",
    ):
        raise ValueError("overdue_source_count must match team_category_rows")
    if report.missing_owner_count != _sum_decimal(
        report.team_category_rows,
        "missing_owner_count",
    ):
        raise ValueError("missing_owner_count must match team_category_rows")
    expected_concentration_count = _decimal_count(
        sum(CONCENTRATION_REASON in row.reason_codes for row in report.team_category_rows),
    )
    if report.source_family_concentration_count != expected_concentration_count:
        raise ValueError(
            "source_family_concentration_count must match team_category_rows",
        )
    if report.missing_reviewer_acknowledgement_count != _sum_decimal(
        report.team_category_rows,
        "missing_reviewer_acknowledgement_count",
    ):
        raise ValueError(
            "missing_reviewer_acknowledgement_count must match team_category_rows",
        )
    if report.max_recheck_overdue_age_seconds != _max_decimal(
        report.team_category_rows,
        "max_recheck_overdue_age_seconds",
    ):
        raise ValueError("max_recheck_overdue_age_seconds must match team_category_rows")
    if report.max_last_recheck_age_seconds != _max_decimal(
        report.team_category_rows,
        "max_last_recheck_age_seconds",
    ):
        raise ValueError("max_last_recheck_age_seconds must match team_category_rows")
    if report.max_source_family_concentration_ratio != _max_decimal(
        report.team_category_rows,
        "source_family_concentration_ratio",
    ):
        raise ValueError(
            "max_source_family_concentration_ratio must match team_category_rows",
        )
    if report.reason_codes != _report_reason_codes(report.team_category_rows):
        raise ValueError("reason_codes must match team_category_rows")
    if report.sla_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("sla_status must match reason_codes")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_sla_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SLA_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_string(field_name, value)


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
    if ratio > Decimal("1.000000"):
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


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
        raise ValueError(f"{field_name} must fit the decimal context") from exc


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


__all__ = (
    "CLEAR_REASON",
    "CONCENTRATION_REASON",
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_SLA_CONFIG_VERSION",
    "EMPTY_REASON",
    "MISSING_OWNER_REASON",
    "MISSING_REVIEWER_ACKNOWLEDGEMENT_REASON",
    "OVERDUE_REASON",
    "REASON_CODE_SEQUENCE",
    "TeamMemorySourceRecheckCadenceSlaConfig",
    "TeamMemorySourceRecheckCadenceSlaInputRow",
    "TeamMemorySourceRecheckCadenceSlaReport",
    "TeamMemorySourceRecheckCadenceSlaTeamCategoryRow",
    "build_team_memory_source_recheck_cadence_sla_report",
    "team_memory_source_recheck_cadence_sla_report_payload",
)
