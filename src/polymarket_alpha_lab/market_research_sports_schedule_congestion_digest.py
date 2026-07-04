"""Pure Phase 1 reducer for sports schedule congestion research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_SPORTS_SCHEDULE_CONGESTION_DIGEST_CONFIG_VERSION = (
    "market-research-sports-schedule-congestion-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")

PASS_STATUS = "pass"
READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS)

CONFLICTING_SOURCES_REASON = "sports_schedule_congestion_conflicting_sources"
REST_GAP_REASON = "sports_schedule_congestion_rest_gap_short"
EVENT_DENSITY_REASON = "sports_schedule_congestion_event_density_high"
TRAVEL_LOAD_REASON = "sports_schedule_congestion_travel_load_high"
SOURCE_COVERAGE_GAP_REASON = "sports_schedule_congestion_source_coverage_gap"
READY_REASON = "sports_schedule_congestion_ready"
PASSED_REASON = "sports_schedule_congestion_passed"
EMPTY_REASON = "sports_schedule_congestion_empty"

ROW_REASON_CODES = (
    CONFLICTING_SOURCES_REASON,
    REST_GAP_REASON,
    EVENT_DENSITY_REASON,
    TRAVEL_LOAD_REASON,
    SOURCE_COVERAGE_GAP_REASON,
    READY_REASON,
)
DIGEST_REASON_CODES = (
    CONFLICTING_SOURCES_REASON,
    REST_GAP_REASON,
    EVENT_DENSITY_REASON,
    TRAVEL_LOAD_REASON,
    SOURCE_COVERAGE_GAP_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_sports_schedule_congestion_monitoring",
    WATCH_STATUS: "review_report_only_sports_schedule_congestion_review",
    BLOCKED_STATUS: "block_report_only_sports_schedule_congestion_review",
}

_BLOCKED_WORDS = (
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "sign" "ing",
    "sub" "mit",
    "can" "cel",
    "repl" "ace",
    "ex" "change",
    "data" "base",
    "per" "sist",
    "pay" "load_" "json",
    "sec" "ret",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SPORTS_SCHEDULE_CONGESTION_DIGEST_CONFIG_VERSION",
    "MarketResearchSportsScheduleCongestionDigestConfig",
    "MarketResearchSportsScheduleCongestionDigestEvent",
    "MarketResearchSportsScheduleCongestionDigestReasonCodeCount",
    "MarketResearchSportsScheduleCongestionDigestRow",
    "MarketResearchSportsScheduleCongestionDigestReport",
    "build_market_research_sports_schedule_congestion_digest",
    "market_research_sports_schedule_congestion_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSportsScheduleCongestionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SPORTS_SCHEDULE_CONGESTION_DIGEST_CONFIG_VERSION
    )
    min_rest_hours: Decimal = Decimal("48.000000")
    min_schedule_gap_hours: Decimal = Decimal("36.000000")
    max_event_count_window: Decimal = Decimal("3.000000")
    high_travel_distance_km: Decimal = Decimal("1000.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_conflicting_source_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSportsScheduleCongestionDigestConfig:
            raise TypeError(
                "MarketResearchSportsScheduleCongestionDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSportsScheduleCongestionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchSportsScheduleCongestionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_rest_hours",
            "min_schedule_gap_hours",
            "high_travel_distance_km",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_event_count_window",
            "min_source_count",
            "max_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSportsScheduleCongestionDigestEvent:
    condition_id: str
    sport_category: str
    league_key: str
    team_key: str
    event_ref: str
    scheduled_at: datetime
    is_target_event: bool
    travel_distance_km: Decimal
    source_count: Decimal
    conflicting_source_count: Decimal
    event_config_version: str = (
        DEFAULT_MARKET_RESEARCH_SPORTS_SCHEDULE_CONGESTION_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSportsScheduleCongestionDigestEvent:
            raise TypeError(
                "MarketResearchSportsScheduleCongestionDigestEvent "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSportsScheduleCongestionDigestEvent:
            raise ValueError(
                "event must be exactly "
                "MarketResearchSportsScheduleCongestionDigestEvent",
            )
        for field_name in (
            "condition_id",
            "sport_category",
            "league_key",
            "team_key",
            "event_ref",
            "event_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "scheduled_at", _as_utc("scheduled_at", self.scheduled_at))
        if type(self.is_target_event) is not bool:
            raise ValueError("is_target_event must be a bool")
        object.__setattr__(
            self,
            "travel_distance_km",
            _normalize_nonnegative_decimal("travel_distance_km", self.travel_distance_km),
        )
        for field_name in ("source_count", "conflicting_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_flags("event", self)


@dataclass(frozen=True)
class MarketResearchSportsScheduleCongestionDigestReasonCodeCount:
    reason_code: str
    condition_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSportsScheduleCongestionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSportsScheduleCongestionDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSportsScheduleCongestionDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSportsScheduleCongestionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "condition_count",
            _normalize_nonnegative_whole_decimal(
                "condition_count",
                self.condition_count,
            ),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSportsScheduleCongestionDigestRow:
    condition_id: str
    sport_category: str
    league_key: str
    team_key: str
    target_event_ref: str
    target_scheduled_at: datetime
    event_count_window: Decimal
    rest_hours_before_target: Decimal
    min_schedule_gap_hours_observed: Decimal
    travel_distance_km_latest: Decimal
    source_count_latest: Decimal
    conflicting_source_count_latest: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSportsScheduleCongestionDigestRow:
            raise TypeError(
                "MarketResearchSportsScheduleCongestionDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSportsScheduleCongestionDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchSportsScheduleCongestionDigestRow",
            )
        for field_name in (
            "condition_id",
            "sport_category",
            "league_key",
            "team_key",
            "target_event_ref",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "target_scheduled_at",
            _as_utc("target_scheduled_at", self.target_scheduled_at),
        )
        for field_name in (
            "event_count_window",
            "source_count_latest",
            "conflicting_source_count_latest",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hours_before_target",
            "min_schedule_gap_hours_observed",
            "travel_distance_km_latest",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSportsScheduleCongestionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    condition_count: Decimal
    ready_condition_count: Decimal
    watch_condition_count: Decimal
    blocked_condition_count: Decimal
    event_count: Decimal
    rest_gap_condition_count: Decimal
    schedule_density_condition_count: Decimal
    travel_load_condition_count: Decimal
    source_gap_condition_count: Decimal
    conflict_condition_count: Decimal
    min_rest_hours: Decimal
    min_schedule_gap_hours: Decimal
    max_event_count_window: Decimal
    high_travel_distance_km: Decimal
    min_source_count: Decimal
    max_conflicting_source_count: Decimal
    min_rest_hours_observed: Decimal | None
    max_event_count_window_observed: Decimal | None
    max_travel_distance_km_observed: Decimal | None
    rows: tuple[MarketResearchSportsScheduleCongestionDigestRow, ...]
    event_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSportsScheduleCongestionDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSportsScheduleCongestionDigestReport:
            raise TypeError(
                "MarketResearchSportsScheduleCongestionDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSportsScheduleCongestionDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchSportsScheduleCongestionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "condition_count",
            "ready_condition_count",
            "watch_condition_count",
            "blocked_condition_count",
            "event_count",
            "rest_gap_condition_count",
            "schedule_density_condition_count",
            "travel_load_condition_count",
            "source_gap_condition_count",
            "conflict_condition_count",
            "min_rest_hours",
            "min_schedule_gap_hours",
            "max_event_count_window",
            "high_travel_distance_km",
            "min_source_count",
            "max_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_rest_hours_observed",
            "max_event_count_window_observed",
            "max_travel_distance_km_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "event_config_versions",
            _normalize_event_config_versions(self.event_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_sports_schedule_congestion_digest(
    events: Iterable[MarketResearchSportsScheduleCongestionDigestEvent],
    *,
    config: MarketResearchSportsScheduleCongestionDigestConfig,
    generated_at: datetime,
) -> MarketResearchSportsScheduleCongestionDigestReport:
    if type(config) is not MarketResearchSportsScheduleCongestionDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchSportsScheduleCongestionDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    event_items = _normalize_events(events)
    rows = _build_rows(event_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    )
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        digest_status = BLOCKED_STATUS
    elif row_reason_codes:
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchSportsScheduleCongestionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        condition_count=_whole(len(rows)),
        ready_condition_count=_whole(
            sum(1 for row in rows if row.digest_status == READY_STATUS),
        ),
        watch_condition_count=_whole(
            sum(1 for row in rows if row.digest_status == WATCH_STATUS),
        ),
        blocked_condition_count=_whole(
            sum(1 for row in rows if row.digest_status == BLOCKED_STATUS),
        ),
        event_count=_whole(len(event_items)),
        rest_gap_condition_count=_whole(
            sum(1 for row in rows if REST_GAP_REASON in row.reason_codes),
        ),
        schedule_density_condition_count=_whole(
            sum(1 for row in rows if EVENT_DENSITY_REASON in row.reason_codes),
        ),
        travel_load_condition_count=_whole(
            sum(1 for row in rows if TRAVEL_LOAD_REASON in row.reason_codes),
        ),
        source_gap_condition_count=_whole(
            sum(1 for row in rows if SOURCE_COVERAGE_GAP_REASON in row.reason_codes),
        ),
        conflict_condition_count=_whole(
            sum(1 for row in rows if CONFLICTING_SOURCES_REASON in row.reason_codes),
        ),
        min_rest_hours=config.min_rest_hours,
        min_schedule_gap_hours=config.min_schedule_gap_hours,
        max_event_count_window=config.max_event_count_window,
        high_travel_distance_km=config.high_travel_distance_km,
        min_source_count=config.min_source_count,
        max_conflicting_source_count=config.max_conflicting_source_count,
        min_rest_hours_observed=_min_or_none(row.rest_hours_before_target for row in rows),
        max_event_count_window_observed=_max_or_none(
            row.event_count_window for row in rows
        ),
        max_travel_distance_km_observed=_max_or_none(
            row.travel_distance_km_latest for row in rows
        ),
        rows=rows,
        event_config_versions=tuple(
            sorted(
                {
                    (event.event_ref, event.event_config_version)
                    for event in event_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_sports_schedule_congestion_digest_payload(
    report: MarketResearchSportsScheduleCongestionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSportsScheduleCongestionDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchSportsScheduleCongestionDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _build_rows(
    events: tuple[MarketResearchSportsScheduleCongestionDigestEvent, ...],
    *,
    config: MarketResearchSportsScheduleCongestionDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchSportsScheduleCongestionDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str],
        list[MarketResearchSportsScheduleCongestionDigestEvent],
    ] = {}
    for event in events:
        grouped.setdefault(
            (event.condition_id, event.sport_category, event.league_key, event.team_key),
            [],
        ).append(event)

    rows: list[MarketResearchSportsScheduleCongestionDigestRow] = []
    for (condition_id, sport_category, league_key, team_key), group_events in grouped.items():
        timeline = sorted(group_events, key=lambda item: (item.scheduled_at, item.event_ref))
        target_events = tuple(item for item in timeline if item.is_target_event)
        if len(target_events) != 1:
            raise ValueError("each condition/team group must contain exactly one target event")
        target = target_events[0]
        if target.scheduled_at < generated_at:
            raise ValueError("target event must not be in the past")
        prior_events = tuple(item for item in timeline if item.scheduled_at < target.scheduled_at)
        window_start = target.scheduled_at - _hours_to_timedelta(config.min_rest_hours)
        window_events = tuple(
            item
            for item in prior_events
            if item.scheduled_at >= window_start
        )
        if prior_events:
            rest_hours_before_target = _hours_between(
                target.scheduled_at,
                prior_events[-1].scheduled_at,
            )
        else:
            rest_hours_before_target = config.min_rest_hours
        schedule_gaps = tuple(
            _hours_between(later.scheduled_at, earlier.scheduled_at)
            for earlier, later in zip(timeline, timeline[1:])
            if later.scheduled_at <= target.scheduled_at
        )
        min_schedule_gap_hours_observed = (
            _quantize(min(schedule_gaps)) if schedule_gaps else rest_hours_before_target
        )
        event_count_window = _whole(len(window_events) + 1)

        reason_codes = []
        if target.conflicting_source_count > config.max_conflicting_source_count:
            reason_codes.append(CONFLICTING_SOURCES_REASON)
        if rest_hours_before_target < config.min_rest_hours:
            reason_codes.append(REST_GAP_REASON)
        if (
            event_count_window >= config.max_event_count_window
            or min_schedule_gap_hours_observed < config.min_schedule_gap_hours
        ):
            reason_codes.append(EVENT_DENSITY_REASON)
        if target.travel_distance_km >= config.high_travel_distance_km:
            reason_codes.append(TRAVEL_LOAD_REASON)
        if target.source_count < config.min_source_count:
            reason_codes.append(SOURCE_COVERAGE_GAP_REASON)
        if not reason_codes:
            reason_codes.append(READY_REASON)
        row_reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

        rows.append(
            MarketResearchSportsScheduleCongestionDigestRow(
                condition_id=condition_id,
                sport_category=sport_category,
                league_key=league_key,
                team_key=team_key,
                target_event_ref=target.event_ref,
                target_scheduled_at=target.scheduled_at,
                event_count_window=event_count_window,
                rest_hours_before_target=rest_hours_before_target,
                min_schedule_gap_hours_observed=min_schedule_gap_hours_observed,
                travel_distance_km_latest=target.travel_distance_km,
                source_count_latest=target.source_count,
                conflicting_source_count_latest=target.conflicting_source_count,
                digest_status=_row_status(row_reason_codes),
                reason_codes=row_reason_codes,
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSportsScheduleCongestionDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSportsScheduleCongestionDigestReasonCodeCount(
            reason_code=reason_code,
            condition_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_events(
    events: Iterable[MarketResearchSportsScheduleCongestionDigestEvent],
) -> tuple[MarketResearchSportsScheduleCongestionDigestEvent, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must contain sports schedule records")
    try:
        event_items = tuple(events)
    except TypeError as exc:
        raise ValueError("events must contain sports schedule records") from exc
    seen: set[str] = set()
    for event in event_items:
        if type(event) is not MarketResearchSportsScheduleCongestionDigestEvent:
            raise ValueError(
                "events must contain "
                "MarketResearchSportsScheduleCongestionDigestEvent records",
            )
        _require_flags("event", event)
        if event.event_ref in seen:
            raise ValueError("events must not contain duplicate event_ref values")
        seen.add(event.event_ref)
    return event_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSportsScheduleCongestionDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSportsScheduleCongestionDigestRow:
            raise ValueError(
                "rows must contain MarketResearchSportsScheduleCongestionDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    keys = tuple(
        (row.condition_id, row.sport_category, row.league_key, row.team_key)
        for row in normalized
    )
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate condition/team keys")
    return normalized


def _normalize_event_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("event_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError(
                "event_config_versions entries must be event/version pairs",
            )
        event_ref, config_version = item
        _require_canonical_string("event_config_versions event_ref", event_ref)
        _require_canonical_string(
            "event_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("event_config_versions event_ref", event_ref)
        _reject_sensitive_text(
            "event_config_versions config_version",
            config_version,
        )
        if event_ref in seen_refs:
            raise ValueError("event_config_versions event_ref values must be unique")
        seen_refs.add(event_ref)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("event_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSportsScheduleCongestionDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchSportsScheduleCongestionDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSportsScheduleCongestionDigestReasonCodeCount records",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: DIGEST_REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _validate_row(row: MarketResearchSportsScheduleCongestionDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == READY_STATUS and row.reason_codes != (READY_REASON,):
        raise ValueError("ready rows must use the ready reason")
    if row.conflicting_source_count_latest > row.source_count_latest:
        raise ValueError("conflicting_source_count_latest must not exceed source_count_latest")


def _validate_report(report: MarketResearchSportsScheduleCongestionDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.condition_count != _whole(len(report.rows)):
        raise ValueError("condition_count must match rows")
    if report.ready_condition_count != _whole(
        sum(1 for row in report.rows if row.digest_status == READY_STATUS),
    ):
        raise ValueError("ready_condition_count must match rows")
    if report.watch_condition_count != _whole(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_condition_count must match rows")
    if report.blocked_condition_count != _whole(
        sum(1 for row in report.rows if row.digest_status == BLOCKED_STATUS),
    ):
        raise ValueError("blocked_condition_count must match rows")
    if (
        report.condition_count
        != report.ready_condition_count
        + report.watch_condition_count
        + report.blocked_condition_count
    ):
        raise ValueError("condition counts must reconcile")
    if report.rest_gap_condition_count != _whole(
        sum(1 for row in report.rows if REST_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("rest_gap_condition_count must match rows")
    if report.schedule_density_condition_count != _whole(
        sum(1 for row in report.rows if EVENT_DENSITY_REASON in row.reason_codes),
    ):
        raise ValueError("schedule_density_condition_count must match rows")
    if report.travel_load_condition_count != _whole(
        sum(1 for row in report.rows if TRAVEL_LOAD_REASON in row.reason_codes),
    ):
        raise ValueError("travel_load_condition_count must match rows")
    if report.source_gap_condition_count != _whole(
        sum(1 for row in report.rows if SOURCE_COVERAGE_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("source_gap_condition_count must match rows")
    if report.conflict_condition_count != _whole(
        sum(1 for row in report.rows if CONFLICTING_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("conflict_condition_count must match rows")
    if report.min_rest_hours_observed != _min_or_none(
        row.rest_hours_before_target for row in report.rows
    ):
        raise ValueError("min_rest_hours_observed must match rows")
    if report.max_event_count_window_observed != _max_or_none(
        row.event_count_window for row in report.rows
    ):
        raise ValueError("max_event_count_window_observed must match rows")
    if report.max_travel_distance_km_observed != _max_or_none(
        row.travel_distance_km_latest for row in report.rows
    ):
        raise ValueError("max_travel_distance_km_observed must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = (
        BLOCKED_STATUS
        if any(row.digest_status == BLOCKED_STATUS for row in report.rows)
        else WATCH_STATUS
        if row_reason_codes
        else PASS_STATUS
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{name} contains invalid reason code for this field")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must not contain duplicates")
    sorted_codes = _sort_reason_codes(reason_codes, allowed)
    if reason_codes != sorted_codes:
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CONFLICTING_SOURCES_REASON in reason_codes:
        return BLOCKED_STATUS
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    return WATCH_STATUS


def _row_sort_key(row: MarketResearchSportsScheduleCongestionDigestRow) -> tuple[object, ...]:
    status_rank = {
        BLOCKED_STATUS: 0,
        WATCH_STATUS: 1,
        READY_STATUS: 2,
    }[row.digest_status]
    return (
        status_rank,
        row.rest_hours_before_target,
        -row.event_count_window,
        row.min_schedule_gap_hours_observed,
        -row.travel_distance_km_latest,
        row.condition_id,
        row.sport_category,
        row.league_key,
        row.team_key,
    )


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400) + (
        Decimal(delta.seconds * 1000000 + delta.microseconds) / Decimal("1000000")
    )
    return _quantize(seconds / Decimal("3600"))


def _hours_to_timedelta(hours: Decimal) -> timedelta:
    return timedelta(microseconds=int(hours * Decimal("3600000000")))


def _normalize_optional_nonnegative_decimal(
    name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _whole(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _min_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(min(items))


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(max(items))


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(word in lowered for word in _BLOCKED_WORDS):
        raise ValueError(f"{name} contains unsafe source detail")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
