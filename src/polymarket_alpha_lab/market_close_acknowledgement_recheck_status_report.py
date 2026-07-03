"""Market close acknowledgement recheck status report."""

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


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_STATUS_CONFIG_VERSION = (
    "market-close-acknowledgement-recheck-status-v0"
)

EMPTY_REASON = "market_close_acknowledgement_recheck_status_empty"
BLOCKED_REASON = "market_close_acknowledgement_recheck_status_blocked"
OVERDUE_REASON = "market_close_acknowledgement_recheck_status_overdue"
WATCH_REASON = "market_close_acknowledgement_recheck_status_watch"
STALE_SOURCE_REASON = "market_close_acknowledgement_recheck_status_stale_source"
CONTRADICTION_REASON = "market_close_acknowledgement_recheck_status_contradiction"
CLEARED_REASON = "market_close_acknowledgement_recheck_status_cleared"

ROW_STATUSES = ("blocked", "overdue", "watch", "cleared")
REPORT_STATUSES = ("empty", *ROW_STATUSES)
REASON_CODES = (
    BLOCKED_REASON,
    OVERDUE_REASON,
    WATCH_REASON,
    STALE_SOURCE_REASON,
    CONTRADICTION_REASON,
    CLEARED_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON, *REASON_CODES)
STATUS_RANK = {"blocked": 0, "overdue": 1, "watch": 2, "cleared": 3}
REASON_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckStatusConfig:
    config_version: str = DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_STATUS_CONFIG_VERSION
    overdue_recheck_seconds: Decimal = Decimal("3600.000000")
    source_stale_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "overdue_recheck_seconds",
            _require_positive_decimal(
                "overdue_recheck_seconds",
                self.overdue_recheck_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_stale_seconds",
            _require_positive_decimal(
                "source_stale_seconds",
                self.source_stale_seconds,
            ),
        )
        require_paper_only_flags("market close acknowledgement recheck status config", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckStatusInputRow:
    market_id: str
    team_id: str
    category_id: str
    market_closed_at: datetime
    recheck_requested_at: datetime
    source_observed_at: datetime
    acknowledgement_at: datetime | None = None
    rechecked_at: datetime | None = None
    recheck_blocked: bool = False
    source_contradicts_acknowledgement: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(self, "team_id", _require_canonical_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "acknowledgement_at",
            _as_optional_utc("acknowledgement_at", self.acknowledgement_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_optional_utc("rechecked_at", self.rechecked_at),
        )
        _require_bool("recheck_blocked", self.recheck_blocked)
        _require_bool(
            "source_contradicts_acknowledgement",
            self.source_contradicts_acknowledgement,
        )
        _validate_input_time_shape(self)
        require_paper_only_flags("market close acknowledgement recheck status input row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckStatusRow:
    market_id: str
    team_id: str
    category_id: str
    market_closed_at: datetime
    recheck_requested_at: datetime
    source_observed_at: datetime
    acknowledgement_at: datetime | None
    rechecked_at: datetime | None
    recheck_blocked: bool
    source_contradicts_acknowledgement: bool
    overdue_recheck_seconds: Decimal
    source_stale_seconds: Decimal
    recheck_age_seconds: Decimal
    source_age_seconds: Decimal
    acknowledgement_age_seconds: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(self, "team_id", _require_canonical_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "acknowledgement_at",
            _as_optional_utc("acknowledgement_at", self.acknowledgement_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_optional_utc("rechecked_at", self.rechecked_at),
        )
        _require_bool("recheck_blocked", self.recheck_blocked)
        _require_bool(
            "source_contradicts_acknowledgement",
            self.source_contradicts_acknowledgement,
        )
        object.__setattr__(
            self,
            "overdue_recheck_seconds",
            _require_positive_decimal(
                "overdue_recheck_seconds",
                self.overdue_recheck_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_stale_seconds",
            _require_positive_decimal("source_stale_seconds", self.source_stale_seconds),
        )
        object.__setattr__(
            self,
            "recheck_age_seconds",
            _require_age_decimal("recheck_age_seconds", self.recheck_age_seconds),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_age_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "acknowledgement_age_seconds",
            _normalize_optional_age_decimal(
                "acknowledgement_age_seconds",
                self.acknowledgement_age_seconds,
            ),
        )
        _require_status("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        require_paper_only_flags("market close acknowledgement recheck status row", self)
        _validate_status_row(self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckStatusTeamCategoryRow:
    team_id: str
    category_id: str
    status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    blocked_count: Decimal
    overdue_count: Decimal
    watch_count: Decimal
    cleared_count: Decimal
    stale_source_count: Decimal
    contradiction_count: Decimal
    issue_count: Decimal
    issue_ratio: Decimal
    max_recheck_age_seconds: Decimal
    max_source_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_canonical_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        _require_status("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        for field_name in (
            "market_count",
            "blocked_count",
            "overdue_count",
            "watch_count",
            "cleared_count",
            "stale_source_count",
            "contradiction_count",
            "issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_ratio_decimal("issue_ratio", self.issue_ratio),
        )
        for field_name in ("max_recheck_age_seconds", "max_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_age_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "market close acknowledgement recheck status team category row",
            self,
        )
        _validate_team_category_row(self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckStatusReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    blocked_count: Decimal
    overdue_count: Decimal
    watch_count: Decimal
    cleared_count: Decimal
    stale_source_count: Decimal
    contradiction_count: Decimal
    issue_count: Decimal
    issue_ratio: Decimal
    max_recheck_age_seconds: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...]
    team_category_rows: tuple[MarketCloseAcknowledgementRecheckStatusTeamCategoryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        _require_status("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        for field_name in (
            "market_count",
            "blocked_count",
            "overdue_count",
            "watch_count",
            "cleared_count",
            "stale_source_count",
            "contradiction_count",
            "issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_ratio_decimal("issue_ratio", self.issue_ratio),
        )
        for field_name in ("max_recheck_age_seconds", "max_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_age_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "team_category_rows",
            _normalize_team_category_rows(self.team_category_rows),
        )
        reject_unsafe_surface_fields(
            "market close acknowledgement recheck status report",
            self,
        )
        require_paper_only_flags("market close acknowledgement recheck status report", self)
        _validate_report(self)


def build_market_close_acknowledgement_recheck_status_report(
    input_rows: list[MarketCloseAcknowledgementRecheckStatusInputRow]
    | tuple[MarketCloseAcknowledgementRecheckStatusInputRow, ...],
    *,
    config: MarketCloseAcknowledgementRecheckStatusConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckStatusReport:
    if type(config) is not MarketCloseAcknowledgementRecheckStatusConfig:
        raise ValueError(
            "config must be a MarketCloseAcknowledgementRecheckStatusConfig",
        )
    require_paper_only_flags("market close acknowledgement recheck status config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    team_category_rows = _team_category_rows(rows)
    reason_codes = _report_reason_codes(rows)

    return MarketCloseAcknowledgementRecheckStatusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(reason_codes),
        reason_codes=reason_codes,
        market_count=_count(len(rows)),
        blocked_count=_status_count(rows, "blocked"),
        overdue_count=_status_count(rows, "overdue"),
        watch_count=_status_count(rows, "watch"),
        cleared_count=_status_count(rows, "cleared"),
        stale_source_count=_reason_count(rows, STALE_SOURCE_REASON),
        contradiction_count=_reason_count(rows, CONTRADICTION_REASON),
        issue_count=_count(sum(1 for row in rows if row.status != "cleared")),
        issue_ratio=_ratio(
            _count(sum(1 for row in rows if row.status != "cleared")),
            _count(len(rows)),
        ),
        max_recheck_age_seconds=_max_decimal(tuple(row.recheck_age_seconds for row in rows)),
        max_source_age_seconds=_max_decimal(tuple(row.source_age_seconds for row in rows)),
        rows=rows,
        team_category_rows=team_category_rows,
    )


def market_close_acknowledgement_recheck_status_report_to_payload(
    report: MarketCloseAcknowledgementRecheckStatusReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckStatusReport:
        raise ValueError(
            "report must be a MarketCloseAcknowledgementRecheckStatusReport",
        )
    require_paper_only_flags("market close acknowledgement recheck status report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields(
        "market close acknowledgement recheck status report",
        payload,
    )
    return payload


def _normalize_input_rows(
    input_rows: object,
    *,
    generated_at: datetime,
) -> tuple[MarketCloseAcknowledgementRecheckStatusInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckStatusInputRow:
            raise ValueError(
                "input_rows must contain MarketCloseAcknowledgementRecheckStatusInputRow",
            )
        require_paper_only_flags("market close acknowledgement recheck status input row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("market_id values must be unique")
        seen_market_ids.add(row.market_id)
        _validate_input_times_against_generated_at(row, generated_at=generated_at)
    return tuple(sorted(rows, key=lambda row: (row.team_id, row.category_id, row.market_id)))


def _row_from_input(
    row: MarketCloseAcknowledgementRecheckStatusInputRow,
    *,
    config: MarketCloseAcknowledgementRecheckStatusConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckStatusRow:
    recheck_age_seconds = _age_seconds(
        generated_at,
        row.recheck_requested_at,
        earlier_field_name="recheck_requested_at",
    )
    source_age_seconds = _age_seconds(
        generated_at,
        row.source_observed_at,
        earlier_field_name="source_observed_at",
    )
    acknowledgement_age_seconds = (
        None
        if row.acknowledgement_at is None
        else _age_seconds(
            generated_at,
            row.acknowledgement_at,
            earlier_field_name="acknowledgement_at",
        )
    )
    reason_codes = _row_reason_codes(
        recheck_blocked=row.recheck_blocked,
        source_contradicts_acknowledgement=row.source_contradicts_acknowledgement,
        acknowledgement_at=row.acknowledgement_at,
        rechecked_at=row.rechecked_at,
        overdue_recheck_seconds=config.overdue_recheck_seconds,
        source_stale_seconds=config.source_stale_seconds,
        recheck_age_seconds=recheck_age_seconds,
        source_age_seconds=source_age_seconds,
    )
    return MarketCloseAcknowledgementRecheckStatusRow(
        market_id=row.market_id,
        team_id=row.team_id,
        category_id=row.category_id,
        market_closed_at=row.market_closed_at,
        recheck_requested_at=row.recheck_requested_at,
        source_observed_at=row.source_observed_at,
        acknowledgement_at=row.acknowledgement_at,
        rechecked_at=row.rechecked_at,
        recheck_blocked=row.recheck_blocked,
        source_contradicts_acknowledgement=row.source_contradicts_acknowledgement,
        overdue_recheck_seconds=config.overdue_recheck_seconds,
        source_stale_seconds=config.source_stale_seconds,
        recheck_age_seconds=recheck_age_seconds,
        source_age_seconds=source_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    recheck_blocked: bool,
    source_contradicts_acknowledgement: bool,
    acknowledgement_at: datetime | None,
    rechecked_at: datetime | None,
    overdue_recheck_seconds: Decimal,
    source_stale_seconds: Decimal,
    recheck_age_seconds: Decimal,
    source_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if recheck_blocked:
        reasons.add(BLOCKED_REASON)
    if source_contradicts_acknowledgement:
        reasons.add(CONTRADICTION_REASON)
    if source_age_seconds > source_stale_seconds:
        reasons.add(STALE_SOURCE_REASON)
    if rechecked_at is None and recheck_age_seconds >= overdue_recheck_seconds:
        reasons.add(OVERDUE_REASON)
    if not reasons:
        if acknowledgement_at is not None and rechecked_at is not None:
            reasons.add(CLEARED_REASON)
        else:
            reasons.add(WATCH_REASON)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _team_category_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckStatusTeamCategoryRow, ...]:
    grouped: dict[tuple[str, str], list[MarketCloseAcknowledgementRecheckStatusRow]] = {}
    for row in rows:
        grouped.setdefault((row.team_id, row.category_id), []).append(row)
    summaries = tuple(
        _team_category_row(team_id, category_id, tuple(group_rows))
        for (team_id, category_id), group_rows in sorted(grouped.items())
    )
    return tuple(sorted(summaries, key=_team_category_sort_key))


def _team_category_row(
    team_id: str,
    category_id: str,
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...],
) -> MarketCloseAcknowledgementRecheckStatusTeamCategoryRow:
    issue_count = _count(sum(1 for row in rows if row.status != "cleared"))
    reason_codes = _group_reason_codes(rows)
    return MarketCloseAcknowledgementRecheckStatusTeamCategoryRow(
        team_id=team_id,
        category_id=category_id,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        market_count=_count(len(rows)),
        blocked_count=_status_count(rows, "blocked"),
        overdue_count=_status_count(rows, "overdue"),
        watch_count=_status_count(rows, "watch"),
        cleared_count=_status_count(rows, "cleared"),
        stale_source_count=_reason_count(rows, STALE_SOURCE_REASON),
        contradiction_count=_reason_count(rows, CONTRADICTION_REASON),
        issue_count=issue_count,
        issue_ratio=_ratio(issue_count, _count(len(rows))),
        max_recheck_age_seconds=_max_decimal(tuple(row.recheck_age_seconds for row in rows)),
        max_source_age_seconds=_max_decimal(tuple(row.source_age_seconds for row in rows)),
    )


def _group_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (CLEARED_REASON,)
    reasons: set[str] = set()
    if any(row.status == "blocked" for row in rows):
        reasons.add(BLOCKED_REASON)
    if any(row.status == "overdue" for row in rows):
        reasons.add(OVERDUE_REASON)
    if any(row.status == "watch" for row in rows):
        reasons.add(WATCH_REASON)
    if any(STALE_SOURCE_REASON in row.reason_codes for row in rows):
        reasons.add(STALE_SOURCE_REASON)
    if any(CONTRADICTION_REASON in row.reason_codes for row in rows):
        reasons.add(CONTRADICTION_REASON)
    if not reasons:
        reasons.add(CLEARED_REASON)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = set(_group_reason_codes(rows))
    if reasons == {CLEARED_REASON}:
        return (CLEARED_REASON,)
    reasons.discard(CLEARED_REASON)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (EMPTY_REASON,):
        return "empty"
    return _row_status(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCKED_REASON in reason_codes or CONTRADICTION_REASON in reason_codes:
        return "blocked"
    if OVERDUE_REASON in reason_codes:
        return "overdue"
    if reason_codes == (CLEARED_REASON,):
        return "cleared"
    return "watch"


def _status_count(
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[MarketCloseAcknowledgementRecheckStatusRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketCloseAcknowledgementRecheckStatusRow,
) -> tuple[int, Decimal, int, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -_row_issue_age_seconds(row),
        REASON_RANK[row.reason_codes[0]],
        row.team_id,
        row.category_id,
        row.market_id,
    )


def _row_issue_age_seconds(row: MarketCloseAcknowledgementRecheckStatusRow) -> Decimal:
    values = (row.recheck_age_seconds, row.source_age_seconds)
    if row.acknowledgement_age_seconds is not None:
        values = (*values, row.acknowledgement_age_seconds)
    return max(values, default=ZERO)


def _team_category_sort_key(
    row: MarketCloseAcknowledgementRecheckStatusTeamCategoryRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.issue_ratio,
        -row.max_recheck_age_seconds,
        row.team_id,
        row.category_id,
    )


def _validate_input_time_shape(
    row: MarketCloseAcknowledgementRecheckStatusInputRow,
) -> None:
    if row.recheck_requested_at < row.market_closed_at:
        raise ValueError("recheck_requested_at must not be before market_closed_at")
    if row.source_observed_at < row.market_closed_at:
        raise ValueError("source_observed_at must not be before market_closed_at")
    if row.acknowledgement_at is not None and row.acknowledgement_at < row.market_closed_at:
        raise ValueError("acknowledgement_at must not be before market_closed_at")
    if row.rechecked_at is not None and row.rechecked_at < row.recheck_requested_at:
        raise ValueError("rechecked_at must not be before recheck_requested_at")


def _validate_input_times_against_generated_at(
    row: MarketCloseAcknowledgementRecheckStatusInputRow,
    *,
    generated_at: datetime,
) -> None:
    _age_seconds(
        generated_at,
        row.market_closed_at,
        earlier_field_name="market_closed_at",
    )
    _age_seconds(
        generated_at,
        row.recheck_requested_at,
        earlier_field_name="recheck_requested_at",
    )
    _age_seconds(
        generated_at,
        row.source_observed_at,
        earlier_field_name="source_observed_at",
    )
    if row.acknowledgement_at is not None:
        _age_seconds(
            generated_at,
            row.acknowledgement_at,
            earlier_field_name="acknowledgement_at",
        )
    if row.rechecked_at is not None:
        _age_seconds(
            generated_at,
            row.rechecked_at,
            earlier_field_name="rechecked_at",
        )


def _validate_status_row(row: MarketCloseAcknowledgementRecheckStatusRow) -> None:
    _validate_input_time_shape(
        MarketCloseAcknowledgementRecheckStatusInputRow(
            market_id=row.market_id,
            team_id=row.team_id,
            category_id=row.category_id,
            market_closed_at=row.market_closed_at,
            recheck_requested_at=row.recheck_requested_at,
            source_observed_at=row.source_observed_at,
            acknowledgement_at=row.acknowledgement_at,
            rechecked_at=row.rechecked_at,
            recheck_blocked=row.recheck_blocked,
            source_contradicts_acknowledgement=row.source_contradicts_acknowledgement,
        ),
    )
    if row.acknowledgement_at is None and row.acknowledgement_age_seconds is not None:
        raise ValueError("acknowledgement_age_seconds requires acknowledgement_at")
    if row.acknowledgement_at is not None and row.acknowledgement_age_seconds is None:
        raise ValueError("acknowledgement_age_seconds is required after acknowledgement")
    expected_reasons = _row_reason_codes(
        recheck_blocked=row.recheck_blocked,
        source_contradicts_acknowledgement=row.source_contradicts_acknowledgement,
        acknowledgement_at=row.acknowledgement_at,
        rechecked_at=row.rechecked_at,
        overdue_recheck_seconds=row.overdue_recheck_seconds,
        source_stale_seconds=row.source_stale_seconds,
        recheck_age_seconds=row.recheck_age_seconds,
        source_age_seconds=row.source_age_seconds,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row state")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_team_category_row(
    row: MarketCloseAcknowledgementRecheckStatusTeamCategoryRow,
) -> None:
    if row.market_count != (
        row.blocked_count + row.overdue_count + row.watch_count + row.cleared_count
    ):
        raise ValueError("market_count must match status counts")
    if row.issue_count != row.blocked_count + row.overdue_count + row.watch_count:
        raise ValueError("issue_count must match status counts")
    if row.stale_source_count > row.market_count:
        raise ValueError("stale_source_count must not exceed market_count")
    if row.contradiction_count > row.market_count:
        raise ValueError("contradiction_count must not exceed market_count")
    if row.issue_ratio != _ratio(row.issue_count, row.market_count):
        raise ValueError("issue_ratio must match counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.cleared_count == row.market_count and row.reason_codes != (CLEARED_REASON,):
        raise ValueError("cleared team category rows require cleared reason")


def _validate_report(report: MarketCloseAcknowledgementRecheckStatusReport) -> None:
    rows = report.rows
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.overdue_count != _status_count(rows, "overdue"):
        raise ValueError("overdue_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.cleared_count != _status_count(rows, "cleared"):
        raise ValueError("cleared_count must match rows")
    if report.market_count != (
        report.blocked_count
        + report.overdue_count
        + report.watch_count
        + report.cleared_count
    ):
        raise ValueError("status counts must match market_count")
    if report.stale_source_count != _reason_count(rows, STALE_SOURCE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.contradiction_count != _reason_count(rows, CONTRADICTION_REASON):
        raise ValueError("contradiction_count must match rows")
    expected_issue_count = _count(sum(1 for row in rows if row.status != "cleared"))
    if report.issue_count != expected_issue_count:
        raise ValueError("issue_count must match rows")
    if report.issue_ratio != _ratio(report.issue_count, report.market_count):
        raise ValueError("issue_ratio must match rows")
    if report.max_recheck_age_seconds != _max_decimal(
        tuple(row.recheck_age_seconds for row in rows),
    ):
        raise ValueError("max_recheck_age_seconds must match rows")
    if report.max_source_age_seconds != _max_decimal(
        tuple(row.source_age_seconds for row in rows),
    ):
        raise ValueError("max_source_age_seconds must match rows")
    expected_team_category_rows = _team_category_rows(rows)
    if report.team_category_rows != expected_team_category_rows:
        raise ValueError("team_category_rows must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    _validate_report_row_times(report)


def _validate_report_row_times(
    report: MarketCloseAcknowledgementRecheckStatusReport,
) -> None:
    for row in report.rows:
        if row.recheck_age_seconds != _age_seconds(
            report.generated_at,
            row.recheck_requested_at,
            earlier_field_name="recheck_requested_at",
        ):
            raise ValueError("recheck_age_seconds must match generated_at")
        if row.source_age_seconds != _age_seconds(
            report.generated_at,
            row.source_observed_at,
            earlier_field_name="source_observed_at",
        ):
            raise ValueError("source_age_seconds must match generated_at")
        if row.acknowledgement_at is not None:
            expected_age = _age_seconds(
                report.generated_at,
                row.acknowledgement_at,
                earlier_field_name="acknowledgement_at",
            )
            if row.acknowledgement_age_seconds != expected_age:
                raise ValueError("acknowledgement_age_seconds must match generated_at")


def _normalize_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckStatusRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckStatusRow:
            raise ValueError("rows must contain MarketCloseAcknowledgementRecheckStatusRow")
        require_paper_only_flags("market close acknowledgement recheck status row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("rows market_id values must be unique")
        seen_market_ids.add(row.market_id)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_team_category_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckStatusTeamCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_category_rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckStatusTeamCategoryRow:
            raise ValueError(
                "team_category_rows must contain MarketCloseAcknowledgementRecheckStatusTeamCategoryRow",
            )
        require_paper_only_flags(
            "market close acknowledgement recheck status team category row",
            row,
        )
        key = (row.team_id, row.category_id)
        if key in seen_keys:
            raise ValueError("team_category_rows team/category values must be unique")
        seen_keys.add(key)
    expected = tuple(sorted(rows, key=_team_category_sort_key))
    if rows != expected:
        raise ValueError("team_category_rows must be deterministic")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_status(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(reason for reason in allowed if reason in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _age_seconds(
    later: datetime,
    earlier: datetime,
    *,
    earlier_field_name: str,
) -> Decimal:
    later_utc = _as_utc("generated_at", later)
    earlier_utc = _as_utc(earlier_field_name, earlier)
    if earlier_utc > later_utc:
        raise ValueError(f"{earlier_field_name} must not be after generated_at")
    return _elapsed_seconds(earlier_utc, later_utc)


def _elapsed_seconds(earlier: datetime, later: datetime) -> Decimal:
    earlier_utc = _as_utc("earlier", earlier)
    later_utc = _as_utc("later", later)
    if later_utc < earlier_utc:
        raise ValueError("elapsed seconds must be nonnegative")
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_optional_age_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_age_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _require_age_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_status(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be known")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if any(character < " " for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


__all__ = (
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_STATUS_CONFIG_VERSION",
    "MarketCloseAcknowledgementRecheckStatusConfig",
    "MarketCloseAcknowledgementRecheckStatusInputRow",
    "MarketCloseAcknowledgementRecheckStatusReport",
    "MarketCloseAcknowledgementRecheckStatusRow",
    "MarketCloseAcknowledgementRecheckStatusTeamCategoryRow",
    "build_market_close_acknowledgement_recheck_status_report",
    "market_close_acknowledgement_recheck_status_report_to_payload",
)
