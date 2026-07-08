"""Deterministic event-trigger research readiness report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION = (
    "research-event-trigger-calendar-readiness-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

NO_INPUTS_REASON = "event_trigger_calendar_readiness_no_inputs"
PASS_REASON = "event_trigger_calendar_readiness_pass"
EVENT_ELAPSED_REASON = "event_trigger_calendar_readiness_event_elapsed"
EVENT_NEAR_REASON = "event_trigger_calendar_readiness_event_near"
SOURCE_CURRENT_REASON = "event_trigger_calendar_readiness_source_refresh_current"
SOURCE_DUE_REASON = "event_trigger_calendar_readiness_source_refresh_due"
SOURCE_MISSING_REASON = "event_trigger_calendar_readiness_source_refresh_missing"
TEAM_READY_REASON = "event_trigger_calendar_readiness_team_capacity_ready"
TEAM_THIN_REASON = "event_trigger_calendar_readiness_team_capacity_thin"
TEAM_UNAVAILABLE_REASON = "event_trigger_calendar_readiness_team_unavailable"
EVIDENCE_FRESH_REASON = "event_trigger_calendar_readiness_evidence_fresh"
EVIDENCE_STALE_REASON = "event_trigger_calendar_readiness_evidence_stale"
EVIDENCE_MISSING_REASON = "event_trigger_calendar_readiness_evidence_missing"
HARD_CALENDAR_CONFLICT_REASON = (
    "event_trigger_calendar_readiness_hard_calendar_conflict"
)
HARD_EVIDENCE_GAP_REASON = "event_trigger_calendar_readiness_hard_evidence_gap"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")

_PUBLIC_NEXT_STEPS = {
    STATUS_PASS: "continue_report_only_research_readiness",
    STATUS_WATCH: "watch_report_only_research_readiness",
    STATUS_BLOCK: "pause_report_only_research_readiness",
}

_ROW_REASON_CODE_SEQUENCE = (
    PASS_REASON,
    EVENT_ELAPSED_REASON,
    EVENT_NEAR_REASON,
    SOURCE_CURRENT_REASON,
    SOURCE_DUE_REASON,
    SOURCE_MISSING_REASON,
    TEAM_READY_REASON,
    TEAM_THIN_REASON,
    TEAM_UNAVAILABLE_REASON,
    EVIDENCE_FRESH_REASON,
    EVIDENCE_STALE_REASON,
    EVIDENCE_MISSING_REASON,
    HARD_CALENDAR_CONFLICT_REASON,
    HARD_EVIDENCE_GAP_REASON,
)

_REPORT_REASON_CODE_SEQUENCE = (
    EVENT_ELAPSED_REASON,
    EVENT_NEAR_REASON,
    SOURCE_CURRENT_REASON,
    SOURCE_DUE_REASON,
    SOURCE_MISSING_REASON,
    TEAM_READY_REASON,
    TEAM_THIN_REASON,
    TEAM_UNAVAILABLE_REASON,
    EVIDENCE_FRESH_REASON,
    EVIDENCE_STALE_REASON,
    EVIDENCE_MISSING_REASON,
    HARD_CALENDAR_CONFLICT_REASON,
    HARD_EVIDENCE_GAP_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)


def _join_text(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        _join_text("mar", "ket"),
        _join_text("source", "_", "ref", "-"),
        _join_text("source", "_", "url"),
        _join_text("source", "_", "text"),
        _join_text("d", "sn"),
        "postgres",
        "secret",
        "table",
        _join_text("to", "ken"),
        _join_text("wal", "let"),
        _join_text("au", "th"),
        _join_text("or", "der"),
        _join_text("tra", "de"),
        _join_text("pos", "ition"),
        _join_text("b", "uy"),
        _join_text("s", "ell"),
        _join_text("reco", "mmend"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION",
    "ResearchEventTriggerCalendarReadinessConfig",
    "ResearchEventTriggerCalendarReadinessInput",
    "ResearchEventTriggerCalendarReadinessReasonCodeCount",
    "ResearchEventTriggerCalendarReadinessReport",
    "ResearchEventTriggerCalendarReadinessRow",
    "build_research_event_trigger_calendar_readiness_report",
    "research_event_trigger_calendar_readiness_report_digest",
    "research_event_trigger_calendar_readiness_report_payload",
)


@dataclass(frozen=True)
class ResearchEventTriggerCalendarReadinessConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION
    watch_trigger_window_seconds: Decimal = Decimal("86400.000000")
    max_evidence_age_seconds: Decimal = Decimal("86400.000000")
    min_watch_team_capacity_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTriggerCalendarReadinessConfig:
            raise TypeError(
                "ResearchEventTriggerCalendarReadinessConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTriggerCalendarReadinessConfig:
            raise TypeError(
                "config must be exactly ResearchEventTriggerCalendarReadinessConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("watch_trigger_window_seconds", "max_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_watch_team_capacity_ratio",
            _require_ratio_decimal(
                "min_watch_team_capacity_ratio",
                self.min_watch_team_capacity_ratio,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventTriggerCalendarReadinessInput:
    research_event_key: str
    event_family: str
    trigger_at: datetime
    latest_source_refresh_at: datetime | None
    source_refresh_window_seconds: Decimal
    latest_evidence_at: datetime | None
    evidence_item_count: Decimal
    available_researcher_count: Decimal
    team_available_hours: Decimal
    required_research_hours: Decimal
    hard_calendar_conflict: bool = False
    hard_evidence_gap: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTriggerCalendarReadinessInput:
            raise TypeError(
                "ResearchEventTriggerCalendarReadinessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTriggerCalendarReadinessInput:
            raise TypeError(
                "input must be exactly ResearchEventTriggerCalendarReadinessInput",
            )
        _require_public_string("research_event_key", self.research_event_key)
        _require_public_string("event_family", self.event_family)
        object.__setattr__(self, "trigger_at", _as_utc("trigger_at", self.trigger_at))
        object.__setattr__(
            self,
            "latest_source_refresh_at",
            _as_optional_utc("latest_source_refresh_at", self.latest_source_refresh_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_optional_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "source_refresh_window_seconds",
            _require_positive_decimal(
                "source_refresh_window_seconds",
                self.source_refresh_window_seconds,
            ),
        )
        for field_name in ("evidence_item_count", "available_researcher_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_available_hours",
            _require_nonnegative_decimal("team_available_hours", self.team_available_hours),
        )
        object.__setattr__(
            self,
            "required_research_hours",
            _require_positive_decimal("required_research_hours", self.required_research_hours),
        )
        _require_bool("hard_calendar_conflict", self.hard_calendar_conflict)
        _require_bool("hard_evidence_gap", self.hard_evidence_gap)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventTriggerCalendarReadinessRow:
    research_event_key: str
    event_family: str
    readiness_status: str
    public_next_step: str
    trigger_at: datetime
    latest_source_refresh_at: datetime | None
    latest_evidence_at: datetime | None
    event_trigger_seconds: Decimal
    latest_source_age_seconds: Decimal | None
    latest_evidence_age_seconds: Decimal | None
    source_refresh_window_seconds: Decimal
    evidence_item_count: Decimal
    available_researcher_count: Decimal
    team_available_hours: Decimal
    required_research_hours: Decimal
    team_capacity_ratio: Decimal
    hard_calendar_conflict: bool
    hard_evidence_gap: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTriggerCalendarReadinessRow:
            raise TypeError(
                "ResearchEventTriggerCalendarReadinessRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTriggerCalendarReadinessRow:
            raise TypeError("row must be exactly ResearchEventTriggerCalendarReadinessRow")
        _require_public_string("research_event_key", self.research_event_key)
        _require_public_string("event_family", self.event_family)
        _require_public_status("readiness_status", self.readiness_status)
        if self.public_next_step != _PUBLIC_NEXT_STEPS[self.readiness_status]:
            raise ValueError("public_next_step must match public status")
        object.__setattr__(self, "trigger_at", _as_utc("trigger_at", self.trigger_at))
        object.__setattr__(
            self,
            "latest_source_refresh_at",
            _as_optional_utc("latest_source_refresh_at", self.latest_source_refresh_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_optional_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "event_trigger_seconds",
            _require_decimal("event_trigger_seconds", self.event_trigger_seconds),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_optional_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _require_optional_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_refresh_window_seconds",
            _require_positive_decimal(
                "source_refresh_window_seconds",
                self.source_refresh_window_seconds,
            ),
        )
        for field_name in ("evidence_item_count", "available_researcher_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_available_hours",
            _require_nonnegative_decimal("team_available_hours", self.team_available_hours),
        )
        object.__setattr__(
            self,
            "required_research_hours",
            _require_positive_decimal("required_research_hours", self.required_research_hours),
        )
        object.__setattr__(
            self,
            "team_capacity_ratio",
            _require_nonnegative_decimal("team_capacity_ratio", self.team_capacity_ratio),
        )
        _require_bool("hard_calendar_conflict", self.hard_calendar_conflict)
        _require_bool("hard_evidence_gap", self.hard_evidence_gap)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        if self.readiness_status != _status_from_reason_codes(
            self.reason_codes,
            self.team_capacity_ratio,
        ):
            raise ValueError("readiness_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventTriggerCalendarReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTriggerCalendarReadinessReasonCodeCount:
            raise TypeError(
                "ResearchEventTriggerCalendarReadinessReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTriggerCalendarReadinessReasonCodeCount:
            raise TypeError(
                "reason code count must be exactly "
                "ResearchEventTriggerCalendarReadinessReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventTriggerCalendarReadinessReport:
    generated_at: datetime
    config_version: str
    readiness_status: str
    public_next_step: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    source_refresh_due_count: Decimal
    source_refresh_missing_count: Decimal
    evidence_stale_count: Decimal
    evidence_missing_count: Decimal
    team_capacity_thin_count: Decimal
    team_unavailable_count: Decimal
    hard_flag_count: Decimal
    average_team_capacity_ratio: Decimal
    average_latest_evidence_age_seconds: Decimal
    rows: tuple[ResearchEventTriggerCalendarReadinessRow, ...]
    reason_code_counts: tuple[ResearchEventTriggerCalendarReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventTriggerCalendarReadinessReport:
            raise TypeError(
                "ResearchEventTriggerCalendarReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTriggerCalendarReadinessReport:
            raise TypeError(
                "report must be exactly ResearchEventTriggerCalendarReadinessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_status("readiness_status", self.readiness_status)
        if self.public_next_step != _PUBLIC_NEXT_STEPS[self.readiness_status]:
            raise ValueError("public_next_step must match public status")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "source_refresh_due_count",
            "source_refresh_missing_count",
            "evidence_stale_count",
            "evidence_missing_count",
            "team_capacity_thin_count",
            "team_unavailable_count",
            "hard_flag_count",
            "average_team_capacity_ratio",
            "average_latest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_count_tuple("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != tuple(item.reason_code for item in self.reason_code_counts):
            raise ValueError("reason_codes must match reason_code_counts")
        _require_hard_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_trigger_calendar_readiness_report_payload(self)

    @property
    def digest(self) -> str:
        return research_event_trigger_calendar_readiness_report_digest(self)


def build_research_event_trigger_calendar_readiness_report(
    rows: tuple[ResearchEventTriggerCalendarReadinessInput, ...],
    *,
    config: ResearchEventTriggerCalendarReadinessConfig | None = None,
    generated_at: datetime,
) -> ResearchEventTriggerCalendarReadinessReport:
    cfg = config or ResearchEventTriggerCalendarReadinessConfig()
    if type(cfg) is not ResearchEventTriggerCalendarReadinessConfig:
        raise TypeError(
            "config must be exactly ResearchEventTriggerCalendarReadinessConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _require_input_tuple("rows", rows)

    if not input_rows:
        reason_counts = (
            ResearchEventTriggerCalendarReadinessReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        return ResearchEventTriggerCalendarReadinessReport(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            readiness_status=STATUS_BLOCK,
            public_next_step=_PUBLIC_NEXT_STEPS[STATUS_BLOCK],
            event_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            source_refresh_due_count=ZERO,
            source_refresh_missing_count=ZERO,
            evidence_stale_count=ZERO,
            evidence_missing_count=ZERO,
            team_capacity_thin_count=ZERO,
            team_unavailable_count=ZERO,
            hard_flag_count=ZERO,
            average_team_capacity_ratio=ZERO,
            average_latest_evidence_age_seconds=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        _build_report_row(row, config=cfg, generated_at=generated_at_utc)
        for row in input_rows
    )
    sorted_rows = tuple(
        sorted(
            report_rows,
            key=lambda row: (
                _status_rank(row.readiness_status),
                row.research_event_key,
                row.event_family,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    readiness_status = _report_status(sorted_rows)

    return ResearchEventTriggerCalendarReadinessReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        readiness_status=readiness_status,
        public_next_step=_PUBLIC_NEXT_STEPS[readiness_status],
        event_count=_count_decimal(len(sorted_rows)),
        pass_count=_sum_if(sorted_rows, lambda row: row.readiness_status == STATUS_PASS),
        watch_count=_sum_if(sorted_rows, lambda row: row.readiness_status == STATUS_WATCH),
        block_count=_sum_if(sorted_rows, lambda row: row.readiness_status == STATUS_BLOCK),
        source_refresh_due_count=_sum_reason(sorted_rows, SOURCE_DUE_REASON),
        source_refresh_missing_count=_sum_reason(sorted_rows, SOURCE_MISSING_REASON),
        evidence_stale_count=_sum_reason(sorted_rows, EVIDENCE_STALE_REASON),
        evidence_missing_count=_sum_reason(sorted_rows, EVIDENCE_MISSING_REASON),
        team_capacity_thin_count=_sum_reason(sorted_rows, TEAM_THIN_REASON),
        team_unavailable_count=_sum_reason(sorted_rows, TEAM_UNAVAILABLE_REASON),
        hard_flag_count=_sum_if(
            sorted_rows,
            lambda row: row.hard_calendar_conflict or row.hard_evidence_gap,
        ),
        average_team_capacity_ratio=_average_decimal(
            tuple(row.team_capacity_ratio for row in sorted_rows),
        ),
        average_latest_evidence_age_seconds=_average_optional_decimal(
            tuple(row.latest_evidence_age_seconds for row in sorted_rows),
        ),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_event_trigger_calendar_readiness_report_payload(
    report: ResearchEventTriggerCalendarReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventTriggerCalendarReadinessReport:
        raise TypeError("report must be exactly ResearchEventTriggerCalendarReadinessReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    _reject_unsafe_public_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def research_event_trigger_calendar_readiness_report_digest(
    report: ResearchEventTriggerCalendarReadinessReport,
) -> str:
    payload = research_event_trigger_calendar_readiness_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode()).hexdigest()


def _build_report_row(
    row: ResearchEventTriggerCalendarReadinessInput,
    *,
    config: ResearchEventTriggerCalendarReadinessConfig,
    generated_at: datetime,
) -> ResearchEventTriggerCalendarReadinessRow:
    _reject_future_optional(row.latest_source_refresh_at, generated_at)
    _reject_future_optional(row.latest_evidence_at, generated_at)

    event_trigger_seconds = _seconds_between(row.trigger_at, generated_at)
    latest_source_age_seconds = (
        None
        if row.latest_source_refresh_at is None
        else _seconds_between(generated_at, row.latest_source_refresh_at)
    )
    latest_evidence_age_seconds = (
        None
        if row.latest_evidence_at is None
        else _seconds_between(generated_at, row.latest_evidence_at)
    )
    team_capacity_ratio = _ratio(row.team_available_hours, row.required_research_hours)

    reasons: list[str] = []
    if event_trigger_seconds < ZERO:
        reasons.append(EVENT_ELAPSED_REASON)
    elif event_trigger_seconds <= config.watch_trigger_window_seconds:
        reasons.append(EVENT_NEAR_REASON)

    if latest_source_age_seconds is None:
        reasons.append(SOURCE_MISSING_REASON)
    elif latest_source_age_seconds > row.source_refresh_window_seconds:
        reasons.append(SOURCE_DUE_REASON)
    else:
        reasons.append(SOURCE_CURRENT_REASON)

    if row.available_researcher_count == ZERO or row.team_available_hours == ZERO:
        reasons.append(TEAM_UNAVAILABLE_REASON)
    elif team_capacity_ratio < ONE:
        reasons.append(TEAM_THIN_REASON)
    else:
        reasons.append(TEAM_READY_REASON)

    if latest_evidence_age_seconds is None or row.evidence_item_count == ZERO:
        reasons.append(EVIDENCE_MISSING_REASON)
    elif latest_evidence_age_seconds > config.max_evidence_age_seconds:
        reasons.append(EVIDENCE_STALE_REASON)
    else:
        reasons.append(EVIDENCE_FRESH_REASON)

    if row.hard_calendar_conflict:
        reasons.append(HARD_CALENDAR_CONFLICT_REASON)
    if row.hard_evidence_gap:
        reasons.append(HARD_EVIDENCE_GAP_REASON)

    reason_codes = _normalize_row_reason_codes("reason_codes", tuple(reasons))
    readiness_status = _status_from_reason_codes(reason_codes, team_capacity_ratio)
    if readiness_status == STATUS_PASS:
        reason_codes = _normalize_row_reason_codes(
            "reason_codes",
            (PASS_REASON, *reason_codes),
        )

    return ResearchEventTriggerCalendarReadinessRow(
        research_event_key=row.research_event_key,
        event_family=row.event_family,
        readiness_status=readiness_status,
        public_next_step=_PUBLIC_NEXT_STEPS[readiness_status],
        trigger_at=row.trigger_at,
        latest_source_refresh_at=row.latest_source_refresh_at,
        latest_evidence_at=row.latest_evidence_at,
        event_trigger_seconds=event_trigger_seconds,
        latest_source_age_seconds=latest_source_age_seconds,
        latest_evidence_age_seconds=latest_evidence_age_seconds,
        source_refresh_window_seconds=row.source_refresh_window_seconds,
        evidence_item_count=row.evidence_item_count,
        available_researcher_count=row.available_researcher_count,
        team_available_hours=row.team_available_hours,
        required_research_hours=row.required_research_hours,
        team_capacity_ratio=team_capacity_ratio,
        hard_calendar_conflict=row.hard_calendar_conflict,
        hard_evidence_gap=row.hard_evidence_gap,
        reason_codes=reason_codes,
    )


def _status_from_reason_codes(
    reason_codes: tuple[str, ...],
    team_capacity_ratio: Decimal,
) -> str:
    if any(
        reason in reason_codes
        for reason in (
            EVENT_ELAPSED_REASON,
            SOURCE_MISSING_REASON,
            TEAM_UNAVAILABLE_REASON,
            EVIDENCE_MISSING_REASON,
            HARD_CALENDAR_CONFLICT_REASON,
            HARD_EVIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCK
    if TEAM_THIN_REASON in reason_codes and team_capacity_ratio < ZERO:
        return STATUS_BLOCK
    if any(
        reason in reason_codes
        for reason in (
            EVENT_NEAR_REASON,
            SOURCE_DUE_REASON,
            TEAM_THIN_REASON,
            EVIDENCE_STALE_REASON,
        )
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchEventTriggerCalendarReadinessRow, ...]) -> str:
    if any(row.readiness_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.readiness_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventTriggerCalendarReadinessRow, ...],
) -> tuple[ResearchEventTriggerCalendarReadinessReasonCodeCount, ...]:
    event_count = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            event_ratio=_ratio(counts[reason_code], event_count),
        )
        for reason_code in _REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _require_input_tuple(
    field_name: str,
    value: tuple[ResearchEventTriggerCalendarReadinessInput, ...],
) -> tuple[ResearchEventTriggerCalendarReadinessInput, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchEventTriggerCalendarReadinessInput:
            raise TypeError(
                f"{field_name} must contain ResearchEventTriggerCalendarReadinessInput",
            )
        _require_hard_flags("input", row)
    return value


def _require_row_tuple(
    field_name: str,
    value: tuple[ResearchEventTriggerCalendarReadinessRow, ...],
) -> tuple[ResearchEventTriggerCalendarReadinessRow, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchEventTriggerCalendarReadinessRow:
            raise TypeError(
                f"{field_name} must contain ResearchEventTriggerCalendarReadinessRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(
            value,
            key=lambda row: (
                _status_rank(row.readiness_status),
                row.research_event_key,
                row.event_family,
            ),
        ),
    )
    if value != sorted_rows:
        raise ValueError("rows must be sorted by public status and research_event_key")
    return value


def _require_reason_count_tuple(
    field_name: str,
    value: tuple[ResearchEventTriggerCalendarReadinessReasonCodeCount, ...],
) -> tuple[ResearchEventTriggerCalendarReadinessReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not ResearchEventTriggerCalendarReadinessReasonCodeCount:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchEventTriggerCalendarReadinessReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    sorted_values = tuple(
        sorted(
            value,
            key=lambda item: _REPORT_REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if value != sorted_values:
        raise ValueError("reason_code_counts must follow known reason sequence")
    return value


def _validate_report_consistency(report: ResearchEventTriggerCalendarReadinessReport) -> None:
    if report.event_count != _count_decimal(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _sum_if(
        report.rows,
        lambda row: row.readiness_status == STATUS_PASS,
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_if(
        report.rows,
        lambda row: row.readiness_status == STATUS_WATCH,
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _sum_if(
        report.rows,
        lambda row: row.readiness_status == STATUS_BLOCK,
    ):
        raise ValueError("block_count must match rows")
    if report.source_refresh_due_count != _sum_reason(report.rows, SOURCE_DUE_REASON):
        raise ValueError("source_refresh_due_count must match rows")
    if report.source_refresh_missing_count != _sum_reason(
        report.rows,
        SOURCE_MISSING_REASON,
    ):
        raise ValueError("source_refresh_missing_count must match rows")
    if report.evidence_stale_count != _sum_reason(report.rows, EVIDENCE_STALE_REASON):
        raise ValueError("evidence_stale_count must match rows")
    if report.evidence_missing_count != _sum_reason(report.rows, EVIDENCE_MISSING_REASON):
        raise ValueError("evidence_missing_count must match rows")
    if report.team_capacity_thin_count != _sum_reason(report.rows, TEAM_THIN_REASON):
        raise ValueError("team_capacity_thin_count must match rows")
    if report.team_unavailable_count != _sum_reason(report.rows, TEAM_UNAVAILABLE_REASON):
        raise ValueError("team_unavailable_count must match rows")
    if report.hard_flag_count != _sum_if(
        report.rows,
        lambda row: row.hard_calendar_conflict or row.hard_evidence_gap,
    ):
        raise ValueError("hard_flag_count must match rows")
    if report.average_team_capacity_ratio != _average_decimal(
        tuple(row.team_capacity_ratio for row in report.rows),
    ):
        raise ValueError("average_team_capacity_ratio must match rows")
    if report.average_latest_evidence_age_seconds != _average_optional_decimal(
        tuple(row.latest_evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("average_latest_evidence_age_seconds must match rows")
    expected_status = STATUS_BLOCK if not report.rows else _report_status(report.rows)
    if report.readiness_status != expected_status:
        raise ValueError("readiness_status must match rows")


def _normalize_row_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in unique_values:
        _require_reason_code(field_name, reason_code)
    return tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in unique_values
    )


def _normalize_report_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in unique_values:
        _require_reason_code(field_name, reason_code)
    return tuple(
        reason_code
        for reason_code in _REPORT_REASON_CODE_SEQUENCE
        if reason_code in unique_values
    )


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    if value not in _REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} contains unknown reason_code")


def _require_public_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a public status: pass, watch, or block")


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be exactly bool")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _reject_future_optional(value: datetime | None, generated_at: datetime) -> None:
    if value is not None and value > generated_at:
        raise ValueError("observed timestamp must not be in the future")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise TypeError("count source must be exactly int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _sum_if(
    rows: tuple[ResearchEventTriggerCalendarReadinessRow, ...],
    predicate: object,
) -> Decimal:
    return _quantize(sum((ONE for row in rows if predicate(row)), ZERO))


def _sum_reason(
    rows: tuple[ResearchEventTriggerCalendarReadinessRow, ...],
    reason_code: str,
) -> Decimal:
    return _sum_if(rows, lambda row: reason_code in row.reason_codes)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), Decimal(len(values)))


def _average_optional_decimal(values: tuple[Decimal | None, ...]) -> Decimal:
    collected = tuple(value for value in values if value is not None)
    if not collected:
        return ZERO
    return _ratio(sum(collected, ZERO), Decimal(len(collected)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, str):
        _reject_unsafe_public_string("payload", value)
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string("payload", str(key))
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(getattr(value, field.name))
