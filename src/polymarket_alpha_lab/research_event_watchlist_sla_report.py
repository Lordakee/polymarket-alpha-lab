"""Pure in-memory SLA report for research event watchlist coverage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Sequence

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_WATCHLIST_SLA_CONFIG_VERSION = (
    "research-event-watchlist-sla-v0"
)

RESEARCH_EVENT_WATCHLIST_SLA_STATUSES = ("pass", "watch", "block")
RESEARCH_EVENT_WATCHLIST_SLA_REASON_CODES = (
    "watchlist_sla_clear",
    "refresh_frequency_breach",
    "evidence_stale",
    "team_owner_missing",
    "near_settlement_check_missing",
    "review_overdue",
    "watchlist_sla_watch",
    "watchlist_sla_block",
)
LOCAL_FIELD_NAMES = (
    "watchlist_id",
    "event_id",
    "market_slug",
    "team_owner_id",
    "last_refreshed_at",
    "evidence_checked_at",
    "settlement_at",
    "settlement_checked_at",
    "review_requested_at",
    "reviewed_at",
    "generated_at",
    "row_status",
    "reason_codes",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000000")
ONE = Decimal("1.000000")
ZERO = Decimal("0.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("cre", "den", "tial"),
        _join_parts("ds", "n"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "n"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class ResearchEventWatchlistSlaConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_WATCHLIST_SLA_CONFIG_VERSION
    refresh_max_age_seconds: Decimal = Decimal("1800.000000")
    evidence_max_age_seconds: Decimal = Decimal("7200.000000")
    near_settlement_window_seconds: Decimal = Decimal("86400.000000")
    settlement_check_max_age_seconds: Decimal = Decimal("3600.000000")
    review_due_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventWatchlistSlaConfig:
            raise TypeError("ResearchEventWatchlistSlaConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventWatchlistSlaConfig:
            raise ValueError("config must be exactly ResearchEventWatchlistSlaConfig")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "refresh_max_age_seconds",
            "evidence_max_age_seconds",
            "near_settlement_window_seconds",
            "settlement_check_max_age_seconds",
            "review_due_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchEventWatchlistSlaItem:
    watchlist_id: str
    event_id: str
    market_slug: str
    team_owner_id: str | None
    last_refreshed_at: datetime
    evidence_checked_at: datetime
    settlement_at: datetime
    settlement_checked_at: datetime | None
    review_requested_at: datetime | None
    reviewed_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventWatchlistSlaItem:
            raise TypeError("ResearchEventWatchlistSlaItem does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventWatchlistSlaItem:
            raise ValueError("item must be exactly ResearchEventWatchlistSlaItem")
        for field_name in ("watchlist_id", "event_id", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "team_owner_id",
            _normalize_optional_public_string("team_owner_id", self.team_owner_id),
        )
        for field_name in (
            "last_refreshed_at",
            "evidence_checked_at",
            "settlement_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "settlement_checked_at",
            _as_optional_utc("settlement_checked_at", self.settlement_checked_at),
        )
        object.__setattr__(
            self,
            "review_requested_at",
            _as_optional_utc("review_requested_at", self.review_requested_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _as_optional_utc("reviewed_at", self.reviewed_at),
        )
        if (
            self.reviewed_at is not None
            and self.review_requested_at is not None
            and self.reviewed_at < self.review_requested_at
        ):
            raise ValueError("reviewed_at must be on or after review_requested_at")
        if self.reviewed_at is not None and self.review_requested_at is None:
            raise ValueError("review_requested_at is required when reviewed_at is set")
        reject_unsafe_surface_fields("research event watchlist sla item", self)
        require_paper_only_flags("item", self)


@dataclass(frozen=True)
class ResearchEventWatchlistSlaRow:
    watchlist_id: str
    event_id: str
    market_slug: str
    team_owner_id: str | None
    row_status: str
    last_refreshed_at: datetime
    evidence_checked_at: datetime
    settlement_at: datetime
    settlement_checked_at: datetime | None
    review_requested_at: datetime | None
    reviewed_at: datetime | None
    refresh_age_seconds: Decimal
    evidence_age_seconds: Decimal
    seconds_to_settlement: Decimal
    settlement_check_age_seconds: Decimal
    review_age_seconds: Decimal
    refresh_frequency_breach: bool
    evidence_stale: bool
    team_owner_missing: bool
    near_settlement_check_required: bool
    near_settlement_check_missing: bool
    review_overdue: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventWatchlistSlaRow:
            raise TypeError("ResearchEventWatchlistSlaRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventWatchlistSlaRow:
            raise ValueError("row must be exactly ResearchEventWatchlistSlaRow")
        for field_name in ("watchlist_id", "event_id", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "team_owner_id",
            _normalize_optional_public_string("team_owner_id", self.team_owner_id),
        )
        _require_status("row_status", self.row_status)
        for field_name in (
            "last_refreshed_at",
            "evidence_checked_at",
            "settlement_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "settlement_checked_at",
            _as_optional_utc("settlement_checked_at", self.settlement_checked_at),
        )
        object.__setattr__(
            self,
            "review_requested_at",
            _as_optional_utc("review_requested_at", self.review_requested_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _as_optional_utc("reviewed_at", self.reviewed_at),
        )
        for field_name in (
            "refresh_age_seconds",
            "evidence_age_seconds",
            "seconds_to_settlement",
            "settlement_check_age_seconds",
            "review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "refresh_frequency_breach",
            "evidence_stale",
            "team_owner_missing",
            "near_settlement_check_required",
            "near_settlement_check_missing",
            "review_overdue",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields("research event watchlist sla row", self)
        require_paper_only_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventWatchlistSlaReport:
    generated_at: datetime
    config_version: str
    report_status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    refresh_frequency_breach_count: Decimal
    evidence_stale_count: Decimal
    missing_team_owner_count: Decimal
    near_settlement_check_due_count: Decimal
    review_overdue_count: Decimal
    oldest_refresh_age_seconds: Decimal
    oldest_evidence_age_seconds: Decimal
    nearest_seconds_to_settlement: Decimal
    local_field_names: tuple[str, ...]
    rows: tuple[ResearchEventWatchlistSlaRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventWatchlistSlaReport:
            raise TypeError("ResearchEventWatchlistSlaReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventWatchlistSlaReport:
            raise ValueError("report must be exactly ResearchEventWatchlistSlaReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "refresh_frequency_breach_count",
            "evidence_stale_count",
            "missing_team_owner_count",
            "near_settlement_check_due_count",
            "review_overdue_count",
            "oldest_refresh_age_seconds",
            "oldest_evidence_age_seconds",
            "nearest_seconds_to_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "local_field_names",
            _normalize_local_field_names(self.local_field_names),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields("research event watchlist sla report", self)
        require_paper_only_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_watchlist_sla_report_to_payload(self)


def build_research_event_watchlist_sla_report(
    items: Sequence[ResearchEventWatchlistSlaItem],
    *,
    generated_at: datetime,
    config: ResearchEventWatchlistSlaConfig | None = None,
) -> ResearchEventWatchlistSlaReport:
    cfg = config or ResearchEventWatchlistSlaConfig()
    if type(cfg) is not ResearchEventWatchlistSlaConfig:
        raise ValueError("config must be a ResearchEventWatchlistSlaConfig")
    require_paper_only_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    _validate_item_times(normalized_items, generated_at_utc)
    rows = _normalize_rows(
        tuple(_build_row(item_value, config=cfg, generated_at=generated_at_utc) for item_value in normalized_items),
    )

    return ResearchEventWatchlistSlaReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=_report_status(rows),
        event_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        refresh_frequency_breach_count=_decimal_count(
            _true_count(tuple(row.refresh_frequency_breach for row in rows)),
        ),
        evidence_stale_count=_decimal_count(
            _true_count(tuple(row.evidence_stale for row in rows)),
        ),
        missing_team_owner_count=_decimal_count(
            _true_count(tuple(row.team_owner_missing for row in rows)),
        ),
        near_settlement_check_due_count=_decimal_count(
            _true_count(tuple(row.near_settlement_check_required for row in rows)),
        ),
        review_overdue_count=_decimal_count(
            _true_count(tuple(row.review_overdue for row in rows)),
        ),
        oldest_refresh_age_seconds=_max_decimal(
            tuple(row.refresh_age_seconds for row in rows),
        ),
        oldest_evidence_age_seconds=_max_decimal(
            tuple(row.evidence_age_seconds for row in rows),
        ),
        nearest_seconds_to_settlement=_min_decimal(
            tuple(row.seconds_to_settlement for row in rows),
        ),
        local_field_names=LOCAL_FIELD_NAMES,
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_event_watchlist_sla_report_to_payload(
    report: ResearchEventWatchlistSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventWatchlistSlaReport:
        raise ValueError("report must be a ResearchEventWatchlistSlaReport")
    reject_unsafe_surface_fields("research event watchlist sla report", report)
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_row(
    item_value: ResearchEventWatchlistSlaItem,
    *,
    config: ResearchEventWatchlistSlaConfig,
    generated_at: datetime,
) -> ResearchEventWatchlistSlaRow:
    refresh_age_seconds = _duration_seconds(item_value.last_refreshed_at, generated_at)
    evidence_age_seconds = _duration_seconds(item_value.evidence_checked_at, generated_at)
    seconds_to_settlement = _duration_seconds(generated_at, item_value.settlement_at)
    settlement_check_age_seconds = (
        ZERO
        if item_value.settlement_checked_at is None
        else _duration_seconds(item_value.settlement_checked_at, generated_at)
    )
    review_age_seconds = _review_age_seconds(item_value, generated_at)

    refresh_frequency_breach = refresh_age_seconds > config.refresh_max_age_seconds
    evidence_stale = evidence_age_seconds > config.evidence_max_age_seconds
    team_owner_missing = item_value.team_owner_id is None
    near_settlement_check_required = (
        seconds_to_settlement <= config.near_settlement_window_seconds
    )
    near_settlement_check_missing = near_settlement_check_required and (
        item_value.settlement_checked_at is None
        or settlement_check_age_seconds > config.settlement_check_max_age_seconds
    )
    review_overdue = (
        item_value.review_requested_at is not None
        and item_value.reviewed_at is None
        and review_age_seconds > config.review_due_seconds
    )
    reason_codes = _row_reason_codes(
        refresh_frequency_breach=refresh_frequency_breach,
        evidence_stale=evidence_stale,
        team_owner_missing=team_owner_missing,
        near_settlement_check_missing=near_settlement_check_missing,
        review_overdue=review_overdue,
    )

    return ResearchEventWatchlistSlaRow(
        watchlist_id=item_value.watchlist_id,
        event_id=item_value.event_id,
        market_slug=item_value.market_slug,
        team_owner_id=item_value.team_owner_id,
        row_status=_row_status(reason_codes),
        last_refreshed_at=item_value.last_refreshed_at,
        evidence_checked_at=item_value.evidence_checked_at,
        settlement_at=item_value.settlement_at,
        settlement_checked_at=item_value.settlement_checked_at,
        review_requested_at=item_value.review_requested_at,
        reviewed_at=item_value.reviewed_at,
        refresh_age_seconds=refresh_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        seconds_to_settlement=seconds_to_settlement,
        settlement_check_age_seconds=settlement_check_age_seconds,
        review_age_seconds=review_age_seconds,
        refresh_frequency_breach=refresh_frequency_breach,
        evidence_stale=evidence_stale,
        team_owner_missing=team_owner_missing,
        near_settlement_check_required=near_settlement_check_required,
        near_settlement_check_missing=near_settlement_check_missing,
        review_overdue=review_overdue,
        reason_codes=reason_codes,
    )


def _review_age_seconds(
    item_value: ResearchEventWatchlistSlaItem,
    generated_at: datetime,
) -> Decimal:
    if item_value.review_requested_at is None:
        return ZERO
    if item_value.reviewed_at is None:
        return _duration_seconds(item_value.review_requested_at, generated_at)
    return _duration_seconds(item_value.review_requested_at, item_value.reviewed_at)


def _row_reason_codes(
    *,
    refresh_frequency_breach: bool,
    evidence_stale: bool,
    team_owner_missing: bool,
    near_settlement_check_missing: bool,
    review_overdue: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if refresh_frequency_breach:
        codes.append("refresh_frequency_breach")
    if evidence_stale:
        codes.append("evidence_stale")
    if team_owner_missing:
        codes.append("team_owner_missing")
    if near_settlement_check_missing:
        codes.append("near_settlement_check_missing")
    if review_overdue:
        codes.append("review_overdue")
    if not codes:
        codes.append("watchlist_sla_clear")
    if any(code in codes for code in _block_reason_codes()):
        codes.append("watchlist_sla_block")
    elif codes != ["watchlist_sla_clear"]:
        codes.append("watchlist_sla_watch")
    return _normalize_reason_codes(tuple(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "watchlist_sla_block" in reason_codes:
        return "block"
    if "watchlist_sla_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventWatchlistSlaRow, ...]) -> str:
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchEventWatchlistSlaRow, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if not seen:
        seen.add("watchlist_sla_clear")
    return tuple(code for code in RESEARCH_EVENT_WATCHLIST_SLA_REASON_CODES if code in seen)


def _block_reason_codes() -> tuple[str, ...]:
    return (
        "evidence_stale",
        "team_owner_missing",
        "near_settlement_check_missing",
        "review_overdue",
    )


def _status_count(rows: tuple[ResearchEventWatchlistSlaRow, ...], status: str) -> Decimal:
    _require_status("status", status)
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _true_count(values: tuple[bool, ...]) -> int:
    return sum(1 for value in values if value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return min(values, default=ZERO)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end must be on or after start")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return _quantize(seconds)


def _normalize_items(
    items: Sequence[ResearchEventWatchlistSlaItem],
) -> tuple[ResearchEventWatchlistSlaItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence")
    normalized: list[ResearchEventWatchlistSlaItem] = []
    for item_value in items:
        if type(item_value) is not ResearchEventWatchlistSlaItem:
            raise ValueError("items must contain ResearchEventWatchlistSlaItem values")
        reject_unsafe_surface_fields("research event watchlist sla item", item_value)
        require_paper_only_flags("item", item_value)
        normalized.append(item_value)
    return tuple(sorted(normalized, key=lambda value: (value.event_id, value.watchlist_id)))


def _normalize_rows(
    rows: tuple[ResearchEventWatchlistSlaRow, ...],
) -> tuple[ResearchEventWatchlistSlaRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchEventWatchlistSlaRow] = []
    for row in rows:
        if type(row) is not ResearchEventWatchlistSlaRow:
            raise ValueError("rows must contain ResearchEventWatchlistSlaRow values")
        reject_unsafe_surface_fields("research event watchlist sla row", row)
        require_paper_only_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda value: (value.event_id, value.watchlist_id)))


def _normalize_local_field_names(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("local_field_names must be a tuple")
    for value in values:
        _require_public_string("local_field_names", value)
    if values != LOCAL_FIELD_NAMES:
        raise ValueError("local_field_names must match the local field plan")
    return values


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_public_string("reason_codes", value)
        if value not in RESEARCH_EVENT_WATCHLIST_SLA_REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(code for code in RESEARCH_EVENT_WATCHLIST_SLA_REASON_CODES if code in seen)


def _validate_item_times(
    items: tuple[ResearchEventWatchlistSlaItem, ...],
    generated_at: datetime,
) -> None:
    for item_value in items:
        if item_value.last_refreshed_at > generated_at:
            raise ValueError("last_refreshed_at must not be after generated_at")
        if item_value.evidence_checked_at > generated_at:
            raise ValueError("evidence_checked_at must not be after generated_at")
        if (
            item_value.settlement_checked_at is not None
            and item_value.settlement_checked_at > generated_at
        ):
            raise ValueError("settlement_checked_at must not be after generated_at")
        if (
            item_value.review_requested_at is not None
            and item_value.review_requested_at > generated_at
        ):
            raise ValueError("review_requested_at must not be after generated_at")
        if item_value.reviewed_at is not None and item_value.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not be after generated_at")


def _validate_row(row: ResearchEventWatchlistSlaRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")
    _require_reason_pair(
        row.refresh_frequency_breach,
        "refresh_frequency_breach",
        row.reason_codes,
        "refresh_frequency_breach",
    )
    _require_reason_pair(row.evidence_stale, "evidence_stale", row.reason_codes, "evidence_stale")
    _require_reason_pair(
        row.team_owner_missing,
        "team_owner_missing",
        row.reason_codes,
        "team_owner_missing",
    )
    _require_reason_pair(
        row.near_settlement_check_missing,
        "near_settlement_check_missing",
        row.reason_codes,
        "near_settlement_check_missing",
    )
    _require_reason_pair(row.review_overdue, "review_overdue", row.reason_codes, "review_overdue")
    if row.team_owner_missing != (row.team_owner_id is None):
        raise ValueError("team_owner_missing must match team_owner_id")
    if row.near_settlement_check_missing and not row.near_settlement_check_required:
        raise ValueError("near_settlement_check_missing requires a near settlement check")


def _validate_report(report: ResearchEventWatchlistSlaReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.refresh_frequency_breach_count != _decimal_count(
        _true_count(tuple(row.refresh_frequency_breach for row in report.rows)),
    ):
        raise ValueError("refresh_frequency_breach_count must match rows")
    if report.evidence_stale_count != _decimal_count(
        _true_count(tuple(row.evidence_stale for row in report.rows)),
    ):
        raise ValueError("evidence_stale_count must match rows")
    if report.missing_team_owner_count != _decimal_count(
        _true_count(tuple(row.team_owner_missing for row in report.rows)),
    ):
        raise ValueError("missing_team_owner_count must match rows")
    if report.near_settlement_check_due_count != _decimal_count(
        _true_count(tuple(row.near_settlement_check_required for row in report.rows)),
    ):
        raise ValueError("near_settlement_check_due_count must match rows")
    if report.review_overdue_count != _decimal_count(
        _true_count(tuple(row.review_overdue for row in report.rows)),
    ):
        raise ValueError("review_overdue_count must match rows")
    if report.oldest_refresh_age_seconds != _max_decimal(
        tuple(row.refresh_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_refresh_age_seconds must match rows")
    if report.oldest_evidence_age_seconds != _max_decimal(
        tuple(row.evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_evidence_age_seconds must match rows")
    if report.nearest_seconds_to_settlement != _min_decimal(
        tuple(row.seconds_to_settlement for row in report.rows),
    ):
        raise ValueError("nearest_seconds_to_settlement must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_reason_pair(
    flag: bool,
    reason_code: str,
    reason_codes: tuple[str, ...],
    field_name: str,
) -> None:
    if flag and reason_code not in reason_codes:
        raise ValueError(f"{field_name} must include {reason_code}")
    if not flag and reason_code in reason_codes:
        raise ValueError(f"{field_name} must not include {reason_code}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_EVENT_WATCHLIST_SLA_STATUSES:
        raise ValueError(f"{field_name} must be one of {RESEARCH_EVENT_WATCHLIST_SLA_STATUSES}")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_string(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_WATCHLIST_SLA_CONFIG_VERSION",
    "LOCAL_FIELD_NAMES",
    "RESEARCH_EVENT_WATCHLIST_SLA_REASON_CODES",
    "RESEARCH_EVENT_WATCHLIST_SLA_STATUSES",
    "ResearchEventWatchlistSlaConfig",
    "ResearchEventWatchlistSlaItem",
    "ResearchEventWatchlistSlaReport",
    "ResearchEventWatchlistSlaRow",
    "build_research_event_watchlist_sla_report",
    "research_event_watchlist_sla_report_to_payload",
)
