"""Pure in-memory conflict resolution SLA report for Phase 1 research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_MARKET_SOURCE_CONFLICT_RESOLUTION_SLA_REPORT_CONFIG_VERSION = (
    "market-source-conflict-resolution-sla-report-v0"
)

REPORT_STATUSES = ("clear", "watch", "breached")
SLA_STATUSES = ("resolved", "pending", "breached")

CLEAR_REASON = "market_source_conflict_resolution_sla_clear"
BREACHED_REASON = "market_source_conflict_resolution_sla_breached"
PENDING_REASON = "market_source_conflict_resolution_sla_pending"
MISSING_OFFICIAL_CHECK_REASON = (
    "market_source_conflict_resolution_missing_official_check"
)
MISSING_PROXY_CHECK_REASON = "market_source_conflict_resolution_missing_proxy_check"
MISSING_SOURCE_FAMILY_CHECK_REASON = (
    "market_source_conflict_resolution_missing_source_family_check"
)
MISSING_TEAM_ACKNOWLEDGEMENT_REASON = (
    "market_source_conflict_resolution_missing_team_acknowledgement"
)
MISSING_ADJUDICATION_EVIDENCE_REASON = (
    "market_source_conflict_resolution_missing_adjudication_evidence"
)
LATE_COMPLETION_REASON = "market_source_conflict_resolution_late_completion"
OPEN_BEYOND_SLA_REASON = "market_source_conflict_resolution_open_beyond_sla"
REASON_CODES = (
    CLEAR_REASON,
    BREACHED_REASON,
    PENDING_REASON,
    MISSING_OFFICIAL_CHECK_REASON,
    MISSING_PROXY_CHECK_REASON,
    MISSING_SOURCE_FAMILY_CHECK_REASON,
    MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
    MISSING_ADJUDICATION_EVIDENCE_REASON,
    LATE_COMPLETION_REASON,
    OPEN_BEYOND_SLA_REASON,
)

STATUS_RANK = {"breached": 0, "pending": 1, "resolved": 2}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
REQUIRED_EVIDENCE_COUNT = Decimal("5.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("que", "stion"),
        _join_parts("pay", "load"),
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketSourceConflictResolutionSlaConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_CONFLICT_RESOLUTION_SLA_REPORT_CONFIG_VERSION
    )
    default_resolution_sla_seconds: Decimal = Decimal("86400.000000")
    source_family_sla_seconds: tuple[tuple[str, Decimal], ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "default_resolution_sla_seconds",
            _require_positive_decimal(
                "default_resolution_sla_seconds",
                self.default_resolution_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_family_sla_seconds",
            _normalize_source_family_sla_seconds(self.source_family_sla_seconds),
        )
        require_paper_only_flags("market source conflict resolution SLA config", self)


@dataclass(frozen=True)
class MarketSourceConflictResolutionSlaInputRow:
    team_id: str
    category_id: str
    conflict_id: str
    source_family: str
    detected_at: datetime
    official_checked_at: datetime | None
    proxy_checked_at: datetime | None
    source_family_checked_at: datetime | None
    team_acknowledged_at: datetime | None
    adjudication_evidence_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("category_id", self.category_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("conflict_id", self.conflict_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        for field_name in _OPTIONAL_TIME_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        require_paper_only_flags("market source conflict resolution SLA input row", self)


@dataclass(frozen=True)
class MarketSourceConflictResolutionSlaConflictRow:
    team_id: str
    category_id: str
    conflict_id: str
    source_family: str
    detected_at: datetime
    official_checked_at: datetime | None
    proxy_checked_at: datetime | None
    source_family_checked_at: datetime | None
    team_acknowledged_at: datetime | None
    adjudication_evidence_at: datetime | None
    sla_seconds: Decimal
    required_evidence_count: Decimal
    completed_evidence_count: Decimal
    missing_evidence_count: Decimal
    evidence_completion_ratio: Decimal
    age_seconds: Decimal
    resolution_age_seconds: Decimal | None
    seconds_over_sla: Decimal
    sla_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("category_id", self.category_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("conflict_id", self.conflict_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        for field_name in _OPTIONAL_TIME_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        for field_name in (
            "sla_seconds",
            "required_evidence_count",
            "completed_evidence_count",
            "missing_evidence_count",
            "evidence_completion_ratio",
            "age_seconds",
            "seconds_over_sla",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.sla_seconds <= ZERO:
            raise ValueError("sla_seconds must be positive")
        object.__setattr__(
            self,
            "resolution_age_seconds",
            _normalize_optional_decimal(
                "resolution_age_seconds",
                self.resolution_age_seconds,
            ),
        )
        _require_sla_status("sla_status", self.sla_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_conflict_row(self)
        require_paper_only_flags("market source conflict resolution SLA conflict row", self)


@dataclass(frozen=True)
class MarketSourceConflictResolutionSlaReport:
    generated_at: datetime
    config_version: str
    report_status: str
    conflict_count: Decimal
    breached_conflict_count: Decimal
    pending_conflict_count: Decimal
    resolved_conflict_count: Decimal
    missing_official_check_count: Decimal
    missing_proxy_check_count: Decimal
    missing_source_family_check_count: Decimal
    missing_team_acknowledgement_count: Decimal
    missing_adjudication_evidence_count: Decimal
    breach_ratio: Decimal
    oldest_conflict_age_seconds: Decimal | None
    rows: tuple[MarketSourceConflictResolutionSlaConflictRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "conflict_count",
            "breached_conflict_count",
            "pending_conflict_count",
            "resolved_conflict_count",
            "missing_official_check_count",
            "missing_proxy_check_count",
            "missing_source_family_check_count",
            "missing_team_acknowledgement_count",
            "missing_adjudication_evidence_count",
            "breach_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_conflict_age_seconds",
            _normalize_optional_decimal(
                "oldest_conflict_age_seconds",
                self.oldest_conflict_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_conflict_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        require_paper_only_flags("market source conflict resolution SLA report", self)


_OPTIONAL_TIME_FIELDS = (
    "official_checked_at",
    "proxy_checked_at",
    "source_family_checked_at",
    "team_acknowledged_at",
    "adjudication_evidence_at",
)


def build_market_source_conflict_resolution_sla_report(
    input_rows: list[MarketSourceConflictResolutionSlaInputRow]
    | tuple[MarketSourceConflictResolutionSlaInputRow, ...],
    *,
    config: MarketSourceConflictResolutionSlaConfig,
    generated_at: datetime,
) -> MarketSourceConflictResolutionSlaReport:
    if type(config) is not MarketSourceConflictResolutionSlaConfig:
        raise ValueError("config must be a MarketSourceConflictResolutionSlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_row_values = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    conflict_rows = _sort_conflict_rows(
        tuple(
            _conflict_row(
                row,
                config=config,
                generated_at=generated_at_utc,
            )
            for row in input_row_values
        )
    )
    reason_codes = _report_reason_codes(conflict_rows)
    return MarketSourceConflictResolutionSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(reason_codes),
        conflict_count=_decimal_count(len(conflict_rows)),
        breached_conflict_count=_decimal_count(
            sum(1 for row in conflict_rows if row.sla_status == "breached"),
        ),
        pending_conflict_count=_decimal_count(
            sum(1 for row in conflict_rows if row.sla_status == "pending"),
        ),
        resolved_conflict_count=_decimal_count(
            sum(1 for row in conflict_rows if row.sla_status == "resolved"),
        ),
        missing_official_check_count=_missing_time_count(
            conflict_rows,
            "official_checked_at",
        ),
        missing_proxy_check_count=_missing_time_count(conflict_rows, "proxy_checked_at"),
        missing_source_family_check_count=_missing_time_count(
            conflict_rows,
            "source_family_checked_at",
        ),
        missing_team_acknowledgement_count=_missing_time_count(
            conflict_rows,
            "team_acknowledged_at",
        ),
        missing_adjudication_evidence_count=_missing_time_count(
            conflict_rows,
            "adjudication_evidence_at",
        ),
        breach_ratio=_ratio(
            _decimal_count(sum(1 for row in conflict_rows if row.sla_status == "breached")),
            _decimal_count(len(conflict_rows)),
        ),
        oldest_conflict_age_seconds=_oldest_age_seconds(conflict_rows),
        rows=conflict_rows,
        reason_codes=reason_codes,
    )


def market_source_conflict_resolution_sla_report_to_payload(
    report: MarketSourceConflictResolutionSlaReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceConflictResolutionSlaReport:
        raise ValueError("report must be a MarketSourceConflictResolutionSlaReport")
    require_paper_only_flags("market source conflict resolution SLA report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields(
        "market source conflict resolution SLA report payload",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceConflictResolutionSlaInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketSourceConflictResolutionSlaInputRow:
            raise ValueError("input rows must contain SLA input rows")
        require_paper_only_flags("market source conflict resolution SLA input row", row)
        if row.detected_at > generated_at:
            raise ValueError("detected_at must not be in the future")
        for field_name in _OPTIONAL_TIME_FIELDS:
            time_value = getattr(row, field_name)
            if time_value is None:
                continue
            if time_value > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
            if time_value < row.detected_at:
                raise ValueError(f"{field_name} must not be before detected_at")
        key = (row.team_id, row.conflict_id)
        if key in seen:
            raise ValueError("conflict_id values must be unique per team")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.team_id,
                row.category_id,
                row.source_family,
                row.conflict_id,
            ),
        )
    )


def _conflict_row(
    row: MarketSourceConflictResolutionSlaInputRow,
    *,
    config: MarketSourceConflictResolutionSlaConfig,
    generated_at: datetime,
) -> MarketSourceConflictResolutionSlaConflictRow:
    evidence_times = _evidence_times(row)
    completed_count = _decimal_count(sum(1 for value in evidence_times if value is not None))
    missing_count = REQUIRED_EVIDENCE_COUNT - completed_count
    age_seconds = _age_seconds(generated_at, row.detected_at)
    sla_seconds = _sla_seconds(row.source_family, config)
    resolution_age_seconds = _resolution_age_seconds(row)
    duration_seconds = resolution_age_seconds if resolution_age_seconds is not None else age_seconds
    seconds_over_sla = _seconds_over_sla(duration_seconds, sla_seconds)
    if seconds_over_sla > ZERO:
        sla_status = "breached"
    elif missing_count > ZERO:
        sla_status = "pending"
    else:
        sla_status = "resolved"

    return MarketSourceConflictResolutionSlaConflictRow(
        team_id=row.team_id,
        category_id=row.category_id,
        conflict_id=row.conflict_id,
        source_family=row.source_family,
        detected_at=row.detected_at,
        official_checked_at=row.official_checked_at,
        proxy_checked_at=row.proxy_checked_at,
        source_family_checked_at=row.source_family_checked_at,
        team_acknowledged_at=row.team_acknowledged_at,
        adjudication_evidence_at=row.adjudication_evidence_at,
        sla_seconds=sla_seconds,
        required_evidence_count=REQUIRED_EVIDENCE_COUNT,
        completed_evidence_count=completed_count,
        missing_evidence_count=missing_count,
        evidence_completion_ratio=_ratio(completed_count, REQUIRED_EVIDENCE_COUNT),
        age_seconds=age_seconds,
        resolution_age_seconds=resolution_age_seconds,
        seconds_over_sla=seconds_over_sla,
        sla_status=sla_status,
        reason_codes=_row_reason_codes(
            row,
            sla_status=sla_status,
            resolution_age_seconds=resolution_age_seconds,
        ),
    )


def _row_reason_codes(
    row: MarketSourceConflictResolutionSlaInputRow,
    *,
    sla_status: str,
    resolution_age_seconds: Decimal | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if sla_status == "resolved":
        return (CLEAR_REASON,)
    if sla_status == "breached":
        reasons.append(BREACHED_REASON)
    if sla_status == "pending":
        reasons.append(PENDING_REASON)
    if row.official_checked_at is None:
        reasons.append(MISSING_OFFICIAL_CHECK_REASON)
    if row.proxy_checked_at is None:
        reasons.append(MISSING_PROXY_CHECK_REASON)
    if row.source_family_checked_at is None:
        reasons.append(MISSING_SOURCE_FAMILY_CHECK_REASON)
    if row.team_acknowledged_at is None:
        reasons.append(MISSING_TEAM_ACKNOWLEDGEMENT_REASON)
    if row.adjudication_evidence_at is None:
        reasons.append(MISSING_ADJUDICATION_EVIDENCE_REASON)
    if sla_status == "breached":
        if resolution_age_seconds is None:
            reasons.append(OPEN_BEYOND_SLA_REASON)
        else:
            reasons.append(LATE_COMPLETION_REASON)
    return tuple(code for code in REASON_CODES if code in reasons)


def _report_reason_codes(
    rows: tuple[MarketSourceConflictResolutionSlaConflictRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if BREACHED_REASON in reason_codes:
        return "breached"
    if PENDING_REASON in reason_codes:
        return "watch"
    return "clear"


def _validate_conflict_row(row: MarketSourceConflictResolutionSlaConflictRow) -> None:
    if row.required_evidence_count != REQUIRED_EVIDENCE_COUNT:
        raise ValueError("required_evidence_count must match required evidence")
    if row.completed_evidence_count + row.missing_evidence_count != row.required_evidence_count:
        raise ValueError("evidence counts must sum to required_evidence_count")
    if row.evidence_completion_ratio != _ratio(
        row.completed_evidence_count,
        row.required_evidence_count,
    ):
        raise ValueError("evidence_completion_ratio must match evidence counts")
    expected_missing = _decimal_count(
        sum(1 for field_name in _OPTIONAL_TIME_FIELDS if getattr(row, field_name) is None)
    )
    if row.missing_evidence_count != expected_missing:
        raise ValueError("missing_evidence_count must match missing evidence")
    if row.completed_evidence_count != row.required_evidence_count - expected_missing:
        raise ValueError("completed_evidence_count must match evidence timestamps")
    for field_name in _OPTIONAL_TIME_FIELDS:
        time_value = getattr(row, field_name)
        if time_value is not None and time_value < row.detected_at:
            raise ValueError(f"{field_name} must not be before detected_at")
    if row.resolution_age_seconds is None and row.missing_evidence_count == ZERO:
        raise ValueError("resolution_age_seconds is required when evidence is complete")
    if row.resolution_age_seconds is not None and row.missing_evidence_count > ZERO:
        raise ValueError("resolution_age_seconds requires complete evidence")
    duration_seconds = (
        row.resolution_age_seconds
        if row.resolution_age_seconds is not None
        else row.age_seconds
    )
    if row.seconds_over_sla != _seconds_over_sla(duration_seconds, row.sla_seconds):
        raise ValueError("seconds_over_sla must match SLA duration")
    if row.sla_status == "resolved":
        if row.reason_codes != (CLEAR_REASON,):
            raise ValueError("resolved rows require clear reason")
        if row.missing_evidence_count != ZERO:
            raise ValueError("resolved rows require complete evidence")
        if row.seconds_over_sla != ZERO:
            raise ValueError("resolved rows cannot exceed SLA")
    if row.sla_status == "pending":
        if PENDING_REASON not in row.reason_codes:
            raise ValueError("pending rows require pending reason")
        if row.missing_evidence_count <= ZERO:
            raise ValueError("pending rows require missing evidence")
        if row.seconds_over_sla != ZERO:
            raise ValueError("pending rows cannot exceed SLA")
    if row.sla_status == "breached":
        if BREACHED_REASON not in row.reason_codes:
            raise ValueError("breached rows require breach reason")
        if row.seconds_over_sla <= ZERO:
            raise ValueError("breached rows require seconds_over_sla")


def _validate_report(report: MarketSourceConflictResolutionSlaReport) -> None:
    if report.conflict_count != _decimal_count(len(report.rows)):
        raise ValueError("conflict_count must match rows")
    expected_breached = _decimal_count(
        sum(1 for row in report.rows if row.sla_status == "breached")
    )
    expected_pending = _decimal_count(
        sum(1 for row in report.rows if row.sla_status == "pending")
    )
    expected_resolved = _decimal_count(
        sum(1 for row in report.rows if row.sla_status == "resolved")
    )
    if report.breached_conflict_count != expected_breached:
        raise ValueError("breached_conflict_count must match rows")
    if report.pending_conflict_count != expected_pending:
        raise ValueError("pending_conflict_count must match rows")
    if report.resolved_conflict_count != expected_resolved:
        raise ValueError("resolved_conflict_count must match rows")
    if (
        report.breached_conflict_count
        + report.pending_conflict_count
        + report.resolved_conflict_count
        != report.conflict_count
    ):
        raise ValueError("status counts must sum to conflict_count")
    for field_name, time_field_name in (
        ("missing_official_check_count", "official_checked_at"),
        ("missing_proxy_check_count", "proxy_checked_at"),
        ("missing_source_family_check_count", "source_family_checked_at"),
        ("missing_team_acknowledgement_count", "team_acknowledged_at"),
        ("missing_adjudication_evidence_count", "adjudication_evidence_at"),
    ):
        if getattr(report, field_name) != _missing_time_count(report.rows, time_field_name):
            raise ValueError(f"{field_name} must match rows")
    if report.breach_ratio != _ratio(report.breached_conflict_count, report.conflict_count):
        raise ValueError("breach_ratio must match breached_conflict_count")
    if report.oldest_conflict_age_seconds != _oldest_age_seconds(report.rows):
        raise ValueError("oldest_conflict_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _normalize_source_family_sla_seconds(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_family_sla_seconds must be a list or tuple")
    rows = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError("source_family_sla_seconds rows must contain family and SLA")
        source_family, sla_seconds = row
        _require_public_string("source_family", source_family)
        if source_family in seen:
            raise ValueError("source_family_sla_seconds must be unique by family")
        seen.add(source_family)
        normalized.append(
            (
                source_family,
                _require_positive_decimal("source_family_sla_seconds", sla_seconds),
            )
        )
    return tuple(sorted(normalized, key=lambda row: row[0]))


def _normalize_conflict_rows(
    value: object,
) -> tuple[MarketSourceConflictResolutionSlaConflictRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketSourceConflictResolutionSlaConflictRow:
            raise ValueError("rows must contain conflict rows")
        require_paper_only_flags("market source conflict resolution SLA conflict row", row)
        key = (row.team_id, row.conflict_id)
        if key in seen:
            raise ValueError("rows must be unique per team and conflict_id")
        seen.add(key)
    expected = _sort_conflict_rows(rows)
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _sort_conflict_rows(
    rows: tuple[MarketSourceConflictResolutionSlaConflictRow, ...],
) -> tuple[MarketSourceConflictResolutionSlaConflictRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.sla_status],
                row.team_id,
                row.category_id,
                row.source_family,
                row.conflict_id,
            ),
        )
    )


def _sla_seconds(
    source_family: str,
    config: MarketSourceConflictResolutionSlaConfig,
) -> Decimal:
    family_slas = dict(config.source_family_sla_seconds)
    return family_slas.get(source_family, config.default_resolution_sla_seconds)


def _evidence_times(
    row: MarketSourceConflictResolutionSlaInputRow,
) -> tuple[datetime | None, ...]:
    return tuple(getattr(row, field_name) for field_name in _OPTIONAL_TIME_FIELDS)


def _resolution_age_seconds(
    row: MarketSourceConflictResolutionSlaInputRow,
) -> Decimal | None:
    evidence_times = _evidence_times(row)
    if any(value is None for value in evidence_times):
        return None
    return _age_seconds(max(value for value in evidence_times if value is not None), row.detected_at)


def _seconds_over_sla(duration_seconds: Decimal, sla_seconds: Decimal) -> Decimal:
    if duration_seconds <= sla_seconds:
        return ZERO
    return (duration_seconds - sla_seconds).quantize(QUANT)


def _missing_time_count(
    rows: tuple[MarketSourceConflictResolutionSlaConflictRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) is None))


def _oldest_age_seconds(
    rows: tuple[MarketSourceConflictResolutionSlaConflictRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.age_seconds for row in rows)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


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
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or breached")


def _require_sla_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SLA_STATUSES:
        raise ValueError(f"{field_name} must be resolved, pending, or breached")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_SOURCE_CONFLICT_RESOLUTION_SLA_REPORT_CONFIG_VERSION",
    "MarketSourceConflictResolutionSlaConfig",
    "MarketSourceConflictResolutionSlaConflictRow",
    "MarketSourceConflictResolutionSlaInputRow",
    "MarketSourceConflictResolutionSlaReport",
    "build_market_source_conflict_resolution_sla_report",
    "market_source_conflict_resolution_sla_report_to_payload",
)
