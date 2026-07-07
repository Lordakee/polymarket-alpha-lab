"""Pure Phase 1 report-only reducer for official source monitoring queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION = (
    "research-packet-official-source-monitoring-queue-v2"
)

CLEAR_REASON = "official_source_monitoring_queue_clear"
MARKET_CLOSE_URGENCY_REASON = "market_close_urgent"
MISSING_OFFICIAL_SOURCE_REASON = "official_source_missing"
STALE_OFFICIAL_SOURCE_REASON = "official_source_stale"
CONTRADICTION_COUNT_REASON = "official_source_contradiction_count"
PROBABILITY_MOVE_REASON = "market_probability_move"
RESOLUTION_CRITERIA_SENSITIVE_REASON = "resolution_criteria_sensitive"
FOLLOW_UP_PRIORITY_REASON = "follow_up_priority"

REASON_CODES = (
    CLEAR_REASON,
    MARKET_CLOSE_URGENCY_REASON,
    MISSING_OFFICIAL_SOURCE_REASON,
    STALE_OFFICIAL_SOURCE_REASON,
    CONTRADICTION_COUNT_REASON,
    PROBABILITY_MOVE_REASON,
    RESOLUTION_CRITERIA_SENSITIVE_REASON,
    FOLLOW_UP_PRIORITY_REASON,
)
REPORT_STATUSES = ("clear", "watch", "urgent")
QUEUE_STATUSES = ("watch", "urgent")
STATUS_WEIGHT = {"urgent": 0, "watch": 1}
REASON_WEIGHT = {
    MARKET_CLOSE_URGENCY_REASON: 0,
    MISSING_OFFICIAL_SOURCE_REASON: 1,
    STALE_OFFICIAL_SOURCE_REASON: 2,
    CONTRADICTION_COUNT_REASON: 3,
    PROBABILITY_MOVE_REASON: 4,
    RESOLUTION_CRITERIA_SENSITIVE_REASON: 5,
    FOLLOW_UP_PRIORITY_REASON: 6,
}
URGENT_REASONS = frozenset(
    (
        MARKET_CLOSE_URGENCY_REASON,
        MISSING_OFFICIAL_SOURCE_REASON,
        STALE_OFFICIAL_SOURCE_REASON,
        CONTRADICTION_COUNT_REASON,
        RESOLUTION_CRITERIA_SENSITIVE_REASON,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceMonitoringQueueV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION
    )
    close_urgency_window_seconds: Decimal = Decimal("7200.000000")
    stale_official_source_age_seconds: Decimal = Decimal("86400.000000")
    contradiction_count_threshold: Decimal = Decimal("1.000000")
    probability_move_threshold: Decimal = Decimal("0.050000")
    resolution_criteria_sensitivity_threshold: Decimal = Decimal("0.700000")
    follow_up_priority_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "close_urgency_window_seconds",
            "stale_official_source_age_seconds",
            "contradiction_count_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_move_threshold",
            "resolution_criteria_sensitivity_threshold",
            "follow_up_priority_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceMonitoringQueueV2InputRow:
    packet_id: str
    market_id: str
    team_id: str
    category_id: str
    market_close_at: datetime
    latest_official_source_checked_at: datetime | None
    official_source_count: Decimal
    official_contradiction_count: Decimal
    previous_probability: Decimal
    current_probability: Decimal
    resolution_criteria_sensitivity: Decimal
    follow_up_priority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    monitoring_digest: str = ""

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "market_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "latest_official_source_checked_at",
            _as_optional_utc(
                "latest_official_source_checked_at",
                self.latest_official_source_checked_at,
            ),
        )
        for field_name in (
            "official_source_count",
            "official_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "previous_probability",
            "current_probability",
            "resolution_criteria_sensitivity",
            "follow_up_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input row", self)
        reject_unsafe_surface_fields("input row", self)
        _set_or_validate_monitoring_digest("input row", self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceMonitoringQueueV2Item:
    packet_id: str
    market_id: str
    team_id: str
    category_id: str
    queue_status: str
    priority_rank: Decimal
    market_close_at: datetime
    time_to_market_close_seconds: Decimal
    latest_official_source_checked_at: datetime | None
    official_source_age_seconds: Decimal | None
    official_source_count: Decimal
    official_contradiction_count: Decimal
    previous_probability: Decimal
    current_probability: Decimal
    probability_move: Decimal
    resolution_criteria_sensitivity: Decimal
    follow_up_priority_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    monitoring_digest: str = ""

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "market_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_member("queue_status", self.queue_status, QUEUE_STATUSES)
        object.__setattr__(
            self,
            "priority_rank",
            _require_nonnegative_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "time_to_market_close_seconds",
            _require_nonnegative_decimal(
                "time_to_market_close_seconds",
                self.time_to_market_close_seconds,
            ),
        )
        object.__setattr__(
            self,
            "latest_official_source_checked_at",
            _as_optional_utc(
                "latest_official_source_checked_at",
                self.latest_official_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_source_age_seconds",
            _normalize_optional_decimal(
                "official_source_age_seconds",
                self.official_source_age_seconds,
            ),
        )
        for field_name in (
            "official_source_count",
            "official_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "previous_probability",
            "current_probability",
            "probability_move",
            "resolution_criteria_sensitivity",
            "follow_up_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("queue item", self)
        reject_unsafe_surface_fields("queue item", self)
        _validate_queue_item(self)
        _set_or_validate_monitoring_digest("queue item", self)


@dataclass(frozen=True)
class ResearchPacketOfficialSourceMonitoringQueueV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    queue_item_count: Decimal
    urgent_item_count: Decimal
    market_close_urgency_count: Decimal
    missing_official_source_count: Decimal
    stale_official_source_count: Decimal
    contradiction_count: Decimal
    probability_move_count: Decimal
    resolution_criteria_sensitivity_count: Decimal
    follow_up_priority_count: Decimal
    min_time_to_market_close_seconds: Decimal
    max_official_source_age_seconds: Decimal
    max_probability_move: Decimal
    queue_pressure_ratio: Decimal
    reason_codes: tuple[str, ...]
    queue_items: tuple[ResearchPacketOfficialSourceMonitoringQueueV2Item, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    monitoring_digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "queue_item_count",
            "urgent_item_count",
            "market_close_urgency_count",
            "missing_official_source_count",
            "stale_official_source_count",
            "contradiction_count",
            "probability_move_count",
            "resolution_criteria_sensitivity_count",
            "follow_up_priority_count",
            "min_time_to_market_close_seconds",
            "max_official_source_age_seconds",
            "max_probability_move",
            "queue_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "queue_items",
            _normalize_queue_items(self.queue_items),
        )
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)
        _validate_report(self)
        _set_or_validate_monitoring_digest("report", self)


@dataclass(frozen=True)
class _ScoredRow:
    input_row: ResearchPacketOfficialSourceMonitoringQueueV2InputRow
    time_to_market_close_seconds: Decimal
    official_source_age_seconds: Decimal | None
    probability_move: Decimal
    market_close_urgent: bool
    official_source_missing: bool
    official_source_stale: bool
    contradiction_count_hit: bool
    probability_move_hit: bool
    resolution_criteria_sensitive: bool
    follow_up_priority: bool


def build_research_packet_official_source_monitoring_queue_v2(
    monitoring_rows: object,
    *,
    config: ResearchPacketOfficialSourceMonitoringQueueV2Config,
    generated_at: datetime,
) -> ResearchPacketOfficialSourceMonitoringQueueV2Report:
    if type(config) is not ResearchPacketOfficialSourceMonitoringQueueV2Config:
        raise ValueError(
            "config must be a ResearchPacketOfficialSourceMonitoringQueueV2Config",
        )
    require_paper_only_flags("config", config)
    reject_unsafe_surface_fields("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(monitoring_rows, generated_at=generated_at_utc)
    scored_rows = tuple(
        _scored_row(row, config=config, generated_at=generated_at_utc) for row in rows
    )
    queue_items = _queue_items(scored_rows)
    reason_codes = _report_reason_codes(queue_items)

    return ResearchPacketOfficialSourceMonitoringQueueV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(queue_items),
        packet_count=_decimal_count(len(scored_rows)),
        queue_item_count=_decimal_count(len(queue_items)),
        urgent_item_count=_decimal_count(
            sum(1 for item in queue_items if item.queue_status == "urgent"),
        ),
        market_close_urgency_count=_reason_count(
            queue_items,
            MARKET_CLOSE_URGENCY_REASON,
        ),
        missing_official_source_count=_reason_count(
            queue_items,
            MISSING_OFFICIAL_SOURCE_REASON,
        ),
        stale_official_source_count=_reason_count(
            queue_items,
            STALE_OFFICIAL_SOURCE_REASON,
        ),
        contradiction_count=_reason_count(
            queue_items,
            CONTRADICTION_COUNT_REASON,
        ),
        probability_move_count=_reason_count(
            queue_items,
            PROBABILITY_MOVE_REASON,
        ),
        resolution_criteria_sensitivity_count=_reason_count(
            queue_items,
            RESOLUTION_CRITERIA_SENSITIVE_REASON,
        ),
        follow_up_priority_count=_reason_count(queue_items, FOLLOW_UP_PRIORITY_REASON),
        min_time_to_market_close_seconds=min(
            (item.time_to_market_close_seconds for item in queue_items),
            default=ZERO,
        ),
        max_official_source_age_seconds=max(
            (
                item.official_source_age_seconds
                for item in queue_items
                if item.official_source_age_seconds is not None
            ),
            default=ZERO,
        ),
        max_probability_move=max(
            (item.probability_move for item in queue_items),
            default=ZERO,
        ),
        queue_pressure_ratio=_ratio(
            _decimal_count(len(queue_items)),
            _decimal_count(len(scored_rows)),
        ),
        reason_codes=reason_codes,
        queue_items=queue_items,
    )


def research_packet_official_source_monitoring_queue_v2_to_payload(
    report: ResearchPacketOfficialSourceMonitoringQueueV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketOfficialSourceMonitoringQueueV2Report:
        raise ValueError(
            "report must be a ResearchPacketOfficialSourceMonitoringQueueV2Report",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("report payload", payload)
    return payload


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketOfficialSourceMonitoringQueueV2InputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("monitoring_rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketOfficialSourceMonitoringQueueV2InputRow:
            raise ValueError(
                "monitoring_rows must contain "
                "ResearchPacketOfficialSourceMonitoringQueueV2InputRow",
            )
        require_paper_only_flags("input row", row)
        reject_unsafe_surface_fields("input row", row)
        key = (row.packet_id, row.market_id)
        if key in seen_keys:
            raise ValueError(
                "monitoring_rows must not contain duplicate packet_id and market_id",
            )
        seen_keys.add(key)
        if (
            row.latest_official_source_checked_at is not None
            and row.latest_official_source_checked_at > generated_at
        ):
            raise ValueError("latest_official_source_checked_at must not be in the future")
    return tuple(
        sorted(
            rows,
            key=lambda row: (row.team_id, row.category_id, row.packet_id, row.market_id),
        ),
    )


def _scored_row(
    row: ResearchPacketOfficialSourceMonitoringQueueV2InputRow,
    *,
    config: ResearchPacketOfficialSourceMonitoringQueueV2Config,
    generated_at: datetime,
) -> _ScoredRow:
    time_to_market_close_seconds = _time_to_market_close_seconds(
        row.market_close_at,
        generated_at,
    )
    official_source_age_seconds = (
        None
        if row.latest_official_source_checked_at is None
        else _age_seconds(generated_at, row.latest_official_source_checked_at)
    )
    probability_move = _absolute_probability_move(
        row.previous_probability,
        row.current_probability,
    )
    market_close_urgent = (
        time_to_market_close_seconds <= config.close_urgency_window_seconds
    )
    official_source_missing = (
        row.latest_official_source_checked_at is None or row.official_source_count == ZERO
    )
    official_source_stale = (
        official_source_age_seconds is not None
        and official_source_age_seconds > config.stale_official_source_age_seconds
    )
    contradiction_count_hit = (
        row.official_contradiction_count >= config.contradiction_count_threshold
    )
    probability_move_hit = probability_move >= config.probability_move_threshold
    resolution_criteria_sensitive = (
        row.resolution_criteria_sensitivity
        >= config.resolution_criteria_sensitivity_threshold
    )
    follow_up_priority = row.follow_up_priority_score >= config.follow_up_priority_threshold
    return _ScoredRow(
        input_row=row,
        time_to_market_close_seconds=time_to_market_close_seconds,
        official_source_age_seconds=official_source_age_seconds,
        probability_move=probability_move,
        market_close_urgent=market_close_urgent,
        official_source_missing=official_source_missing,
        official_source_stale=official_source_stale,
        contradiction_count_hit=contradiction_count_hit,
        probability_move_hit=probability_move_hit,
        resolution_criteria_sensitive=resolution_criteria_sensitive,
        follow_up_priority=follow_up_priority,
    )


def _queue_items(
    scored_rows: tuple[_ScoredRow, ...],
) -> tuple[ResearchPacketOfficialSourceMonitoringQueueV2Item, ...]:
    unranked_items = tuple(
        item
        for item in (_queue_item(scored_row) for scored_row in scored_rows)
        if item is not None
    )
    ranked_items = tuple(
        sorted(
            unranked_items,
            key=lambda item: (
                STATUS_WEIGHT[item.queue_status],
                min(REASON_WEIGHT[reason] for reason in item.reason_codes),
                item.time_to_market_close_seconds,
                item.team_id,
                item.category_id,
                item.packet_id,
                item.market_id,
            ),
        ),
    )
    return tuple(
        ResearchPacketOfficialSourceMonitoringQueueV2Item(
            packet_id=item.packet_id,
            market_id=item.market_id,
            team_id=item.team_id,
            category_id=item.category_id,
            queue_status=item.queue_status,
            priority_rank=_decimal_count(index),
            market_close_at=item.market_close_at,
            time_to_market_close_seconds=item.time_to_market_close_seconds,
            latest_official_source_checked_at=item.latest_official_source_checked_at,
            official_source_age_seconds=item.official_source_age_seconds,
            official_source_count=item.official_source_count,
            official_contradiction_count=item.official_contradiction_count,
            previous_probability=item.previous_probability,
            current_probability=item.current_probability,
            probability_move=item.probability_move,
            resolution_criteria_sensitivity=item.resolution_criteria_sensitivity,
            follow_up_priority_score=item.follow_up_priority_score,
            reason_codes=item.reason_codes,
        )
        for index, item in enumerate(ranked_items, start=1)
    )


def _queue_item(
    scored_row: _ScoredRow,
) -> ResearchPacketOfficialSourceMonitoringQueueV2Item | None:
    reason_codes = _item_reason_codes(scored_row)
    if reason_codes == (CLEAR_REASON,):
        return None
    row = scored_row.input_row
    return ResearchPacketOfficialSourceMonitoringQueueV2Item(
        packet_id=row.packet_id,
        market_id=row.market_id,
        team_id=row.team_id,
        category_id=row.category_id,
        queue_status=_queue_status(reason_codes),
        priority_rank=ZERO,
        market_close_at=row.market_close_at,
        time_to_market_close_seconds=scored_row.time_to_market_close_seconds,
        latest_official_source_checked_at=row.latest_official_source_checked_at,
        official_source_age_seconds=scored_row.official_source_age_seconds,
        official_source_count=row.official_source_count,
        official_contradiction_count=row.official_contradiction_count,
        previous_probability=row.previous_probability,
        current_probability=row.current_probability,
        probability_move=scored_row.probability_move,
        resolution_criteria_sensitivity=row.resolution_criteria_sensitivity,
        follow_up_priority_score=row.follow_up_priority_score,
        reason_codes=reason_codes,
    )


def _item_reason_codes(scored_row: _ScoredRow) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if scored_row.market_close_urgent:
        reason_codes.append(MARKET_CLOSE_URGENCY_REASON)
    if scored_row.official_source_missing:
        reason_codes.append(MISSING_OFFICIAL_SOURCE_REASON)
    if scored_row.official_source_stale:
        reason_codes.append(STALE_OFFICIAL_SOURCE_REASON)
    if scored_row.contradiction_count_hit:
        reason_codes.append(CONTRADICTION_COUNT_REASON)
    if scored_row.probability_move_hit:
        reason_codes.append(PROBABILITY_MOVE_REASON)
    if scored_row.resolution_criteria_sensitive:
        reason_codes.append(RESOLUTION_CRITERIA_SENSITIVE_REASON)
    if scored_row.follow_up_priority:
        reason_codes.append(FOLLOW_UP_PRIORITY_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _queue_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in URGENT_REASONS for reason_code in reason_codes):
        return "urgent"
    return "watch"


def _report_status(
    queue_items: tuple[ResearchPacketOfficialSourceMonitoringQueueV2Item, ...],
) -> str:
    if not queue_items:
        return "clear"
    if any(item.queue_status == "urgent" for item in queue_items):
        return "urgent"
    return "watch"


def _report_reason_codes(
    queue_items: tuple[ResearchPacketOfficialSourceMonitoringQueueV2Item, ...],
) -> tuple[str, ...]:
    if not queue_items:
        return (CLEAR_REASON,)
    reason_codes: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in item.reason_codes for item in queue_items):
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _normalize_queue_items(
    value: object,
) -> tuple[ResearchPacketOfficialSourceMonitoringQueueV2Item, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("queue_items must be a list or tuple")
    items = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchPacketOfficialSourceMonitoringQueueV2Item:
            raise ValueError(
                "queue_items must contain "
                "ResearchPacketOfficialSourceMonitoringQueueV2Item",
            )
        require_paper_only_flags("queue item", item)
        reject_unsafe_surface_fields("queue item", item)
        key = (item.packet_id, item.market_id)
        if key in seen_keys:
            raise ValueError("queue_items must not contain duplicate packet_id and market_id")
        seen_keys.add(key)
    expected = tuple(
        sorted(
            items,
            key=lambda item: (
                item.priority_rank,
                STATUS_WEIGHT[item.queue_status],
                min(REASON_WEIGHT[reason] for reason in item.reason_codes),
                item.time_to_market_close_seconds,
                item.team_id,
                item.category_id,
                item.packet_id,
                item.market_id,
            ),
        ),
    )
    if items != expected:
        raise ValueError("queue_items must be sorted deterministically")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(items) + 1))
    if tuple(item.priority_rank for item in items) != expected_ranks:
        raise ValueError("queue_items must have contiguous priority_rank values")
    return items


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if (CLEAR_REASON in reason_codes) and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason cannot be mixed with monitoring reasons")
    if tuple(reason for reason in REASON_CODES if reason in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_queue_item(
    item: ResearchPacketOfficialSourceMonitoringQueueV2Item,
) -> None:
    if (item.latest_official_source_checked_at is None) != (
        item.official_source_age_seconds is None
    ):
        raise ValueError("official source age presence must match source check time")
    if item.reason_codes == (CLEAR_REASON,):
        raise ValueError("queue items cannot use clear reason")
    if item.queue_status != _queue_status(item.reason_codes):
        raise ValueError("queue_status must match reason_codes")
    if item.probability_move != _absolute_probability_move(
        item.previous_probability,
        item.current_probability,
    ):
        raise ValueError("probability_move must match probabilities")


def _validate_report(report: ResearchPacketOfficialSourceMonitoringQueueV2Report) -> None:
    if report.queue_item_count != _decimal_count(len(report.queue_items)):
        raise ValueError("queue_item_count must match queue_items")
    if report.queue_item_count > report.packet_count:
        raise ValueError("queue_item_count must not exceed packet_count")
    if report.urgent_item_count != _decimal_count(
        sum(1 for item in report.queue_items if item.queue_status == "urgent"),
    ):
        raise ValueError("urgent_item_count must match queue_items")
    expected_reason_counts = (
        ("market_close_urgency_count", MARKET_CLOSE_URGENCY_REASON),
        ("missing_official_source_count", MISSING_OFFICIAL_SOURCE_REASON),
        ("stale_official_source_count", STALE_OFFICIAL_SOURCE_REASON),
        ("contradiction_count", CONTRADICTION_COUNT_REASON),
        ("probability_move_count", PROBABILITY_MOVE_REASON),
        (
            "resolution_criteria_sensitivity_count",
            RESOLUTION_CRITERIA_SENSITIVE_REASON,
        ),
        ("follow_up_priority_count", FOLLOW_UP_PRIORITY_REASON),
    )
    for field_name, reason_code in expected_reason_counts:
        if getattr(report, field_name) != _reason_count(report.queue_items, reason_code):
            raise ValueError(f"{field_name} must match queue_items")
    min_item_close_seconds = min(
        (item.time_to_market_close_seconds for item in report.queue_items),
        default=ZERO,
    )
    if report.min_time_to_market_close_seconds != min_item_close_seconds:
        raise ValueError("min_time_to_market_close_seconds must match queue_items")
    max_item_source_age = max(
        (
            item.official_source_age_seconds
            for item in report.queue_items
            if item.official_source_age_seconds is not None
        ),
        default=ZERO,
    )
    if report.max_official_source_age_seconds != max_item_source_age:
        raise ValueError("max_official_source_age_seconds must match queue_items")
    if report.max_probability_move != max(
        (item.probability_move for item in report.queue_items),
        default=ZERO,
    ):
        raise ValueError("max_probability_move must match queue_items")
    if report.queue_pressure_ratio != _ratio(report.queue_item_count, report.packet_count):
        raise ValueError("queue_pressure_ratio must match queue_item_count and packet_count")
    if report.reason_codes != _report_reason_codes(report.queue_items):
        raise ValueError("reason_codes must match queue_items")
    if report.report_status != _report_status(report.queue_items):
        raise ValueError("report_status must match queue_items")
    if report.report_status == "clear" and report.queue_items:
        raise ValueError("clear report cannot contain queue_items")


def _reason_count(
    queue_items: tuple[ResearchPacketOfficialSourceMonitoringQueueV2Item, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for item in queue_items if reason_code in item.reason_codes))


def _time_to_market_close_seconds(market_close_at: datetime, generated_at: datetime) -> Decimal:
    if market_close_at <= generated_at:
        return ZERO
    return _age_seconds(market_close_at, generated_at)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    if earlier_utc > later_utc:
        raise ValueError("earlier datetime must not be in the future")
    delta = later_utc - earlier_utc
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _absolute_probability_move(previous_probability: Decimal, current_probability: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(current_probability - previous_probability))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or isinstance(value, bool):
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return decimal_value


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
    decimal_value = _quantize(value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe report detail")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if "." in value:
        raise ValueError(f"{field_name} must be an opaque public identifier")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _set_or_validate_monitoring_digest(label: str, value: object) -> None:
    current = getattr(value, "monitoring_digest")
    if type(current) is not str:
        raise ValueError(f"monitoring_digest must be a string for {label}")
    expected = _monitoring_digest(value)
    if current == "":
        object.__setattr__(value, "monitoring_digest", expected)
        return
    if current != expected:
        raise ValueError(f"monitoring_digest must match {label}")


def _monitoring_digest(value: object) -> str:
    payload = asdict(value)
    payload.pop("monitoring_digest", None)
    canonical_payload = json_ready_no_floats(payload)
    canonical_json = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION",
    "ResearchPacketOfficialSourceMonitoringQueueV2Config",
    "ResearchPacketOfficialSourceMonitoringQueueV2InputRow",
    "ResearchPacketOfficialSourceMonitoringQueueV2Item",
    "ResearchPacketOfficialSourceMonitoringQueueV2Report",
    "build_research_packet_official_source_monitoring_queue_v2",
    "research_packet_official_source_monitoring_queue_v2_to_payload",
)
