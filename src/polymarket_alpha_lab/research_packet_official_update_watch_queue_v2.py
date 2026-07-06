"""Phase 1 readonly official-update watch queue report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_PACKET_OFFICIAL_UPDATE_WATCH_QUEUE_V2_CONFIG_VERSION = (
    "research-packet-official-update-watch-queue-v2"
)
SOURCE_KINDS = ("official", "resolution_critical", "proxy", "context")
WATCH_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "official_update_current",
    "official_update_overdue",
    "official_source_missing",
    "resolution_critical_source_due",
    "resolution_critical_source_missing",
    "proxy_only_official_gap",
)
REPORT_REASON_CODES = (
    "official_update_watch_queue_clear",
    "official_update_watch_items_present",
    "official_update_blocked_items_present",
    "overdue_official_sources_present",
    "resolution_critical_sources_present",
    "missing_official_sources_present",
)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ONE_COUNT = Decimal("1").quantize(COUNT_QUANTUM)
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_OFFICIAL_UPDATE_WATCH_QUEUE_V2_CONFIG_VERSION",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "SOURCE_KINDS",
    "WATCH_STATUSES",
    "ResearchPacketOfficialUpdateWatchQueueV2Config",
    "ResearchPacketOfficialUpdateWatchQueueV2Input",
    "ResearchPacketOfficialUpdateWatchQueueV2Report",
    "ResearchPacketOfficialUpdateWatchQueueV2Row",
    "build_research_packet_official_update_watch_queue_v2",
    "research_packet_official_update_watch_queue_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketOfficialUpdateWatchQueueV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_OFFICIAL_UPDATE_WATCH_QUEUE_V2_CONFIG_VERSION
    official_overdue_seconds: Decimal = Decimal("3600.000000")
    resolution_critical_due_seconds: Decimal = Decimal("900.000000")
    overdue_official_penalty: Decimal = Decimal("20.000000")
    missing_official_penalty: Decimal = Decimal("30.000000")
    resolution_critical_boost: Decimal = Decimal("25.000000")
    proxy_only_penalty: Decimal = Decimal("10.000000")
    watch_priority_floor: Decimal = Decimal("20.000000")
    blocked_priority_floor: Decimal = Decimal("45.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "official_overdue_seconds",
            "resolution_critical_due_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overdue_official_penalty",
            "missing_official_penalty",
            "resolution_critical_boost",
            "proxy_only_penalty",
            "watch_priority_floor",
            "blocked_priority_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_score(field_name, getattr(self, field_name)),
            )
        if self.blocked_priority_floor < self.watch_priority_floor:
            raise ValueError("blocked_priority_floor must be >= watch_priority_floor")
        _reject_unsafe_public_payload(
            "ResearchPacketOfficialUpdateWatchQueueV2Config",
            self,
        )
        require_paper_only_flags("ResearchPacketOfficialUpdateWatchQueueV2Config", self)


@dataclass(frozen=True)
class ResearchPacketOfficialUpdateWatchQueueV2Input:
    packet_id: str
    source_id: str
    source_kind: str
    last_checked_at: datetime | None
    expected_update_at: datetime | None
    source_priority_score: Decimal
    resolution_critical: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("source_id", self.source_id)
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "last_checked_at",
            _as_optional_utc("last_checked_at", self.last_checked_at),
        )
        object.__setattr__(
            self,
            "expected_update_at",
            _as_optional_utc("expected_update_at", self.expected_update_at),
        )
        object.__setattr__(
            self,
            "source_priority_score",
            _normalize_nonnegative_score(
                "source_priority_score",
                self.source_priority_score,
            ),
        )
        _require_bool("resolution_critical", self.resolution_critical)
        _reject_unsafe_public_payload(
            "ResearchPacketOfficialUpdateWatchQueueV2Input",
            self,
        )
        require_paper_only_flags("ResearchPacketOfficialUpdateWatchQueueV2Input", self)


@dataclass(frozen=True)
class ResearchPacketOfficialUpdateWatchQueueV2Row:
    priority_rank: Decimal
    packet_id: str
    source_id: str
    source_kind: str
    watch_status: str
    last_checked_at: datetime | None
    expected_update_at: datetime | None
    official_update_age_seconds: Decimal | None
    overdue_seconds: Decimal
    source_priority_score: Decimal
    official_update_priority_score: Decimal
    official_source_missing: bool
    official_update_overdue: bool
    resolution_critical: bool
    resolution_critical_due: bool
    proxy_only_official_gap: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("source_id", self.source_id)
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        _require_member("watch_status", self.watch_status, WATCH_STATUSES)
        object.__setattr__(
            self,
            "last_checked_at",
            _as_optional_utc("last_checked_at", self.last_checked_at),
        )
        object.__setattr__(
            self,
            "expected_update_at",
            _as_optional_utc("expected_update_at", self.expected_update_at),
        )
        object.__setattr__(
            self,
            "official_update_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "official_update_age_seconds",
                self.official_update_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "overdue_seconds",
            _normalize_nonnegative_seconds("overdue_seconds", self.overdue_seconds),
        )
        for field_name in (
            "source_priority_score",
            "official_update_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_missing",
            "official_update_overdue",
            "resolution_critical",
            "resolution_critical_due",
            "proxy_only_official_gap",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload(
            "ResearchPacketOfficialUpdateWatchQueueV2Row",
            self,
        )
        require_paper_only_flags("ResearchPacketOfficialUpdateWatchQueueV2Row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketOfficialUpdateWatchQueueV2Report:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    official_source_count: Decimal
    overdue_official_source_count: Decimal
    missing_official_source_count: Decimal
    resolution_critical_source_count: Decimal
    max_official_update_priority_score: Decimal
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, WATCH_STATUSES)
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
            "source_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "official_source_count",
            "overdue_official_source_count",
            "missing_official_source_count",
            "resolution_critical_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_official_update_priority_score",
            _normalize_nonnegative_score(
                "max_official_update_priority_score",
                self.max_official_update_priority_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload(
            "ResearchPacketOfficialUpdateWatchQueueV2Report",
            self,
        )
        require_paper_only_flags("ResearchPacketOfficialUpdateWatchQueueV2Report", self)
        _validate_report(self)


@dataclass(frozen=True)
class _OfficialUpdateDraft:
    packet_id: str
    source_id: str
    source_kind: str
    last_checked_at: datetime | None
    expected_update_at: datetime | None
    official_update_age_seconds: Decimal | None
    overdue_seconds: Decimal
    source_priority_score: Decimal
    official_update_priority_score: Decimal
    official_source_missing: bool
    official_update_overdue: bool
    resolution_critical: bool
    resolution_critical_due: bool
    proxy_only_official_gap: bool
    watch_status: str
    reason_codes: tuple[str, ...]


def build_research_packet_official_update_watch_queue_v2(
    inputs: list[ResearchPacketOfficialUpdateWatchQueueV2Input]
    | tuple[ResearchPacketOfficialUpdateWatchQueueV2Input, ...],
    *,
    config: ResearchPacketOfficialUpdateWatchQueueV2Config,
    generated_at: datetime,
) -> ResearchPacketOfficialUpdateWatchQueueV2Report:
    if type(config) is not ResearchPacketOfficialUpdateWatchQueueV2Config:
        raise ValueError("config must be a ResearchPacketOfficialUpdateWatchQueueV2Config")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    drafts = tuple(
        _draft_for_input(row, config=config, generated_at=generated_at_utc)
        for row in input_rows
    )
    rows = tuple(
        _row_from_draft(draft, _count(index))
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    digest = _report_digest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchPacketOfficialUpdateWatchQueueV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        source_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        official_source_count=_source_kind_count(rows, "official"),
        overdue_official_source_count=_flag_count(rows, "official_update_overdue"),
        missing_official_source_count=_flag_count(rows, "official_source_missing"),
        resolution_critical_source_count=_flag_count(rows, "resolution_critical"),
        max_official_update_priority_score=_max_score(
            tuple(row.official_update_priority_score for row in rows),
        ),
        rows=rows,
        derived_validation_digest=digest,
    )


def research_packet_official_update_watch_queue_v2_payload(
    report: ResearchPacketOfficialUpdateWatchQueueV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketOfficialUpdateWatchQueueV2Report:
        _reject_unsafe_public_payload(
            "research packet official update watch queue v2 payload",
            report,
        )
        raise ValueError("report must be a ResearchPacketOfficialUpdateWatchQueueV2Report")
    require_paper_only_flags("report", report)
    _validate_report(report)
    _reject_unsafe_public_payload(
        "research packet official update watch queue v2 payload",
        report,
    )
    ready = _json_ready(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "research packet official update watch queue v2 payload",
        ready,
    )
    return ready


def _draft_for_input(
    row: ResearchPacketOfficialUpdateWatchQueueV2Input,
    *,
    config: ResearchPacketOfficialUpdateWatchQueueV2Config,
    generated_at: datetime,
) -> _OfficialUpdateDraft:
    if row.last_checked_at is not None and row.last_checked_at > generated_at:
        raise ValueError("last_checked_at must not be after generated_at")
    if row.expected_update_at is not None and row.expected_update_at > generated_at:
        raise ValueError("expected_update_at must not be after generated_at")

    official_like = row.source_kind in ("official", "resolution_critical")
    official_source_missing = official_like and row.last_checked_at is None
    age_seconds = (
        None if row.last_checked_at is None else _seconds_between(row.last_checked_at, generated_at)
    )
    overdue_by_age = (
        age_seconds is not None
        and official_like
        and age_seconds >= config.official_overdue_seconds
    )
    overdue_by_expected_update = (
        row.expected_update_at is not None
        and official_like
        and row.expected_update_at <= generated_at
        and (row.last_checked_at is None or row.last_checked_at < row.expected_update_at)
    )
    official_update_overdue = overdue_by_age or overdue_by_expected_update
    overdue_seconds = _overdue_seconds(
        row,
        config=config,
        generated_at=generated_at,
        age_seconds=age_seconds,
        official_like=official_like,
    )
    resolution_critical = row.resolution_critical or row.source_kind == "resolution_critical"
    resolution_critical_due = resolution_critical and (
        row.last_checked_at is None
        or (age_seconds is not None and age_seconds >= config.resolution_critical_due_seconds)
        or overdue_by_expected_update
    )
    proxy_only_official_gap = row.source_kind == "proxy" and row.expected_update_at is not None
    priority_score = row.source_priority_score
    if official_update_overdue:
        priority_score += config.overdue_official_penalty
    if official_source_missing:
        priority_score += config.missing_official_penalty
    if resolution_critical_due:
        priority_score += config.resolution_critical_boost
    if proxy_only_official_gap:
        priority_score += config.proxy_only_penalty
    priority_score = _normalize_nonnegative_score(
        "official_update_priority_score",
        priority_score,
    )
    watch_status = _watch_status(priority_score, config=config)
    return _OfficialUpdateDraft(
        packet_id=row.packet_id,
        source_id=row.source_id,
        source_kind=row.source_kind,
        last_checked_at=row.last_checked_at,
        expected_update_at=row.expected_update_at,
        official_update_age_seconds=age_seconds,
        overdue_seconds=overdue_seconds,
        source_priority_score=row.source_priority_score,
        official_update_priority_score=priority_score,
        official_source_missing=official_source_missing,
        official_update_overdue=official_update_overdue,
        resolution_critical=resolution_critical,
        resolution_critical_due=resolution_critical_due,
        proxy_only_official_gap=proxy_only_official_gap,
        watch_status=watch_status,
        reason_codes=_row_reason_codes(
            official_source_missing=official_source_missing,
            official_update_overdue=official_update_overdue,
            resolution_critical=resolution_critical,
            resolution_critical_due=resolution_critical_due,
            proxy_only_official_gap=proxy_only_official_gap,
        ),
    )


def _row_from_draft(
    draft: _OfficialUpdateDraft,
    priority_rank: Decimal,
) -> ResearchPacketOfficialUpdateWatchQueueV2Row:
    digest = _row_digest(draft=draft, priority_rank=priority_rank)
    return ResearchPacketOfficialUpdateWatchQueueV2Row(
        priority_rank=priority_rank,
        packet_id=draft.packet_id,
        source_id=draft.source_id,
        source_kind=draft.source_kind,
        watch_status=draft.watch_status,
        last_checked_at=draft.last_checked_at,
        expected_update_at=draft.expected_update_at,
        official_update_age_seconds=draft.official_update_age_seconds,
        overdue_seconds=draft.overdue_seconds,
        source_priority_score=draft.source_priority_score,
        official_update_priority_score=draft.official_update_priority_score,
        official_source_missing=draft.official_source_missing,
        official_update_overdue=draft.official_update_overdue,
        resolution_critical=draft.resolution_critical,
        resolution_critical_due=draft.resolution_critical_due,
        proxy_only_official_gap=draft.proxy_only_official_gap,
        reason_codes=draft.reason_codes,
        derived_validation_digest=digest,
    )


def _normalize_inputs(
    inputs: list[ResearchPacketOfficialUpdateWatchQueueV2Input]
    | tuple[ResearchPacketOfficialUpdateWatchQueueV2Input, ...],
) -> tuple[ResearchPacketOfficialUpdateWatchQueueV2Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketOfficialUpdateWatchQueueV2Input:
            raise ValueError(
                "inputs must contain ResearchPacketOfficialUpdateWatchQueueV2Input values",
            )
        require_paper_only_flags("input", row)
        key = (row.packet_id, row.source_id)
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate packet_id/source_id values")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a list or tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a list or tuple") from exc
    seen_keys: set[tuple[str, str]] = set()
    seen_ranks: set[Decimal] = set()
    for row in rows:
        if type(row) is not ResearchPacketOfficialUpdateWatchQueueV2Row:
            raise ValueError(
                "rows must contain ResearchPacketOfficialUpdateWatchQueueV2Row values",
            )
        require_paper_only_flags("row", row)
        _validate_row(row)
        key = (row.packet_id, row.source_id)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate packet_id/source_id values")
        seen_keys.add(key)
        if row.priority_rank in seen_ranks:
            raise ValueError("rows must not contain duplicate priority_rank values")
        seen_ranks.add(row.priority_rank)
    return rows


def _validate_row(row: ResearchPacketOfficialUpdateWatchQueueV2Row) -> None:
    if row.source_kind == "official" and row.official_source_missing != (
        row.last_checked_at is None
    ):
        raise ValueError("official_source_missing must match last_checked_at")
    if row.source_kind not in ("official", "resolution_critical"):
        if row.official_source_missing or row.official_update_overdue:
            raise ValueError("non-official rows must not be marked as official gaps")
    if row.official_source_missing and not row.official_update_overdue:
        raise ValueError("official_source_missing must also be official_update_overdue")
    if row.official_update_age_seconds is None and row.last_checked_at is not None:
        raise ValueError("official_update_age_seconds must be present when last_checked_at is present")
    if row.official_update_age_seconds is not None and row.last_checked_at is None:
        raise ValueError("official_update_age_seconds must be None when last_checked_at is None")
    if row.official_update_overdue is False and row.overdue_seconds != ZERO_SECONDS:
        raise ValueError("overdue_seconds must be zero when official_update_overdue is False")
    if row.resolution_critical_due and not row.resolution_critical:
        raise ValueError("resolution_critical_due requires resolution_critical")
    if row.reason_codes != _row_reason_codes(
        official_source_missing=row.official_source_missing,
        official_update_overdue=row.official_update_overdue,
        resolution_critical=row.resolution_critical,
        resolution_critical_due=row.resolution_critical_due,
        proxy_only_official_gap=row.proxy_only_official_gap,
    ):
        raise ValueError("reason_codes must match official update flags")
    if row.derived_validation_digest != _row_digest(row=row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchPacketOfficialUpdateWatchQueueV2Report) -> None:
    if report.source_count != _count(len(report.rows)):
        raise ValueError("source_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.official_source_count != _source_kind_count(report.rows, "official"):
        raise ValueError("official_source_count must match rows")
    if report.overdue_official_source_count != _flag_count(
        report.rows,
        "official_update_overdue",
    ):
        raise ValueError("overdue_official_source_count must match rows")
    if report.missing_official_source_count != _flag_count(
        report.rows,
        "official_source_missing",
    ):
        raise ValueError("missing_official_source_count must match rows")
    if report.resolution_critical_source_count != _flag_count(
        report.rows,
        "resolution_critical",
    ):
        raise ValueError("resolution_critical_source_count must match rows")
    if report.max_official_update_priority_score != _max_score(
        tuple(row.official_update_priority_score for row in report.rows),
    ):
        raise ValueError("max_official_update_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.priority_rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must have contiguous priority_rank values")
    if tuple(report.rows) != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by official update priority")
    if report.derived_validation_digest != _report_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=report.rows,
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _watch_status(
    priority_score: Decimal,
    *,
    config: ResearchPacketOfficialUpdateWatchQueueV2Config,
) -> str:
    if priority_score >= config.blocked_priority_floor:
        return "blocked"
    if priority_score >= config.watch_priority_floor:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    official_source_missing: bool,
    official_update_overdue: bool,
    resolution_critical: bool,
    resolution_critical_due: bool,
    proxy_only_official_gap: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if official_source_missing:
        codes.append("official_source_missing")
    elif official_update_overdue:
        codes.append("official_update_overdue")
    if resolution_critical and resolution_critical_due:
        if official_source_missing:
            codes.append("resolution_critical_source_missing")
        else:
            codes.append("resolution_critical_source_due")
    if proxy_only_official_gap:
        codes.append("proxy_only_official_gap")
    if not codes:
        codes.append("official_update_current")
    return tuple(codes)


def _report_status(
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...],
) -> str:
    if any(row.watch_status == "blocked" for row in rows):
        return "blocked"
    if any(row.watch_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    if any(row.watch_status == "blocked" for row in rows):
        codes.append("official_update_blocked_items_present")
    elif any(row.watch_status == "watch" for row in rows):
        codes.append("official_update_watch_items_present")
    else:
        codes.append("official_update_watch_queue_clear")
    if any(row.official_update_overdue for row in rows):
        codes.append("overdue_official_sources_present")
    if any(row.resolution_critical for row in rows):
        codes.append("resolution_critical_sources_present")
    if any(row.official_source_missing for row in rows):
        codes.append("missing_official_sources_present")
    return tuple(codes)


def _draft_sort_key(draft: _OfficialUpdateDraft) -> tuple[Decimal, Decimal, str, str]:
    return (
        -draft.official_update_priority_score,
        -draft.overdue_seconds,
        draft.packet_id,
        draft.source_id,
    )


def _row_sort_key(
    row: ResearchPacketOfficialUpdateWatchQueueV2Row,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        row.priority_rank,
        -row.official_update_priority_score,
        row.packet_id,
        row.source_id,
    )


def _overdue_seconds(
    row: ResearchPacketOfficialUpdateWatchQueueV2Input,
    *,
    config: ResearchPacketOfficialUpdateWatchQueueV2Config,
    generated_at: datetime,
    age_seconds: Decimal | None,
    official_like: bool,
) -> Decimal:
    if not official_like:
        return ZERO_SECONDS
    values: list[Decimal] = []
    if age_seconds is not None:
        values.append(_nonnegative_seconds_delta(age_seconds, config.official_overdue_seconds))
    if row.expected_update_at is not None:
        if row.last_checked_at is None or row.last_checked_at < row.expected_update_at:
            values.append(_seconds_between(row.expected_update_at, generated_at))
    if row.last_checked_at is None:
        values.append(config.official_overdue_seconds)
    return _max_seconds(tuple(values))


def _nonnegative_seconds_delta(value: Decimal, threshold: Decimal) -> Decimal:
    if value <= threshold:
        return ZERO_SECONDS
    return _normalize_nonnegative_seconds("seconds_delta", value - threshold)


def _status_count(
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.watch_status == status))


def _source_kind_count(
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...],
    source_kind: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.source_kind == source_kind))


def _flag_count(
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...],
    flag_name: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, flag_name) is True))


def _max_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SECONDS
    return _normalize_nonnegative_seconds("max_seconds", max(values))


def _max_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    return _normalize_nonnegative_score("max_score", max(values))


def _row_digest(
    *,
    draft: _OfficialUpdateDraft | None = None,
    priority_rank: Decimal | None = None,
    row: ResearchPacketOfficialUpdateWatchQueueV2Row | None = None,
) -> str:
    if row is not None:
        payload = {
            "priority_rank": row.priority_rank,
            "packet_id": row.packet_id,
            "source_id": row.source_id,
            "source_kind": row.source_kind,
            "watch_status": row.watch_status,
            "last_checked_at": row.last_checked_at,
            "expected_update_at": row.expected_update_at,
            "official_update_age_seconds": row.official_update_age_seconds,
            "overdue_seconds": row.overdue_seconds,
            "source_priority_score": row.source_priority_score,
            "official_update_priority_score": row.official_update_priority_score,
            "official_source_missing": row.official_source_missing,
            "official_update_overdue": row.official_update_overdue,
            "resolution_critical": row.resolution_critical,
            "resolution_critical_due": row.resolution_critical_due,
            "proxy_only_official_gap": row.proxy_only_official_gap,
            "reason_codes": row.reason_codes,
        }
    elif draft is not None and priority_rank is not None:
        payload = {
            "priority_rank": priority_rank,
            "packet_id": draft.packet_id,
            "source_id": draft.source_id,
            "source_kind": draft.source_kind,
            "watch_status": draft.watch_status,
            "last_checked_at": draft.last_checked_at,
            "expected_update_at": draft.expected_update_at,
            "official_update_age_seconds": draft.official_update_age_seconds,
            "overdue_seconds": draft.overdue_seconds,
            "source_priority_score": draft.source_priority_score,
            "official_update_priority_score": draft.official_update_priority_score,
            "official_source_missing": draft.official_source_missing,
            "official_update_overdue": draft.official_update_overdue,
            "resolution_critical": draft.resolution_critical,
            "resolution_critical_due": draft.resolution_critical_due,
            "proxy_only_official_gap": draft.proxy_only_official_gap,
            "reason_codes": draft.reason_codes,
        }
    else:
        raise ValueError("row digest requires row or draft with priority_rank")
    return _digest_payload(payload)


def _report_digest(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchPacketOfficialUpdateWatchQueueV2Row, ...],
) -> str:
    payload = {
        "generated_at": generated_at,
        "config_version": config_version,
        "row_digests": tuple(row.derived_validation_digest for row in rows),
    }
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, object]) -> str:
    return "sha256:" + sha256(
        json.dumps(
            _json_ready(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key, item in _iter_public_items(value):
        lowered_key = key.lower()
        if any(term in lowered_key for term in UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public key in {label}: {key}")
        if isinstance(item, str):
            lowered_value = item.lower()
            if any(term in lowered_value for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"unsafe public value in {label}: {key}")


def _iter_public_items(value: object) -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[tuple[str, object]] = []
        for field in fields(value):
            items.append((field.name, getattr(value, field.name)))
            items.extend(_iter_public_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append((key, item))
            items.extend(_iter_public_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_items(item))
        return tuple(items)
    return ()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_seconds(
        "seconds_between",
        total_microseconds / MICROSECONDS_PER_SECOND,
    )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized <= ZERO_COUNT or normalized != value:
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT or normalized != value:
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return normalized


def _normalize_positive_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_nonnegative_score(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = decimal_value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if value != value.lower():
        raise ValueError(f"{field_name} must be lowercase")
    if any(term in value.lower() for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for code in value:
        _require_member(field_name, code, allowed)
        if code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(code)
    return value


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{field_name} must be a sha256 digest")
    suffix = value.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
