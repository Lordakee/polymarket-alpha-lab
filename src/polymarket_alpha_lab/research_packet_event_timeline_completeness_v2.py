"""Phase 1 pure report for research packet event timeline completeness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_PACKET_EVENT_TIMELINE_COMPLETENESS_V2_CONFIG_VERSION = (
    "research-packet-event-timeline-completeness-v2"
)

ROW_STATUSES = ("complete", "watch", "blocked")
REPORT_STATUSES = ROW_STATUSES

COMPLETE_REASON = "event_timeline_completeness_complete"
WATCH_REASON = "event_timeline_completeness_watch"
BLOCKED_REASON = "event_timeline_completeness_blocked"
MISSING_STEPS_REASON = "event_timeline_missing_steps"
LATE_STEPS_REASON = "event_timeline_late_steps"

TIMELINE_STEP_FIELDS = (
    "initial_catalyst_at",
    "primary_source_timestamp_at",
    "probability_move_timestamp_at",
    "follow_up_source_timestamp_at",
    "resolution_update_timestamp_at",
)
MISSING_STEP_CODE_BY_FIELD = {
    "initial_catalyst_at": "missing_initial_catalyst",
    "primary_source_timestamp_at": "missing_primary_source_timestamp",
    "probability_move_timestamp_at": "missing_probability_move_timestamp",
    "follow_up_source_timestamp_at": "missing_follow_up_source_timestamp",
    "resolution_update_timestamp_at": "missing_resolution_update_timestamp",
}
LATE_STEP_CODE_BY_FIELD = {
    "initial_catalyst_at": "late_initial_catalyst",
    "primary_source_timestamp_at": "late_primary_source_timestamp",
    "probability_move_timestamp_at": "late_probability_move_timestamp",
    "follow_up_source_timestamp_at": "late_follow_up_source_timestamp",
    "resolution_update_timestamp_at": "late_resolution_update_timestamp",
}
MISSING_STEP_CODES = tuple(
    MISSING_STEP_CODE_BY_FIELD[field_name] for field_name in TIMELINE_STEP_FIELDS
)
LATE_STEP_CODES = tuple(
    LATE_STEP_CODE_BY_FIELD[field_name] for field_name in TIMELINE_STEP_FIELDS
)
REASON_CODES = (
    COMPLETE_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
    MISSING_STEPS_REASON,
    LATE_STEPS_REASON,
    *MISSING_STEP_CODES,
    *LATE_STEP_CODES,
)

COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANT)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANT)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANT)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANT)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
REQUIRED_STEP_COUNT = Decimal(len(TIMELINE_STEP_FIELDS)).quantize(COUNT_QUANT)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "complete": 2}


@dataclass(frozen=True)
class ResearchPacketEventTimelineCompletenessV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_EVENT_TIMELINE_COMPLETENESS_V2_CONFIG_VERSION
    late_after_packet_grace_seconds: Decimal = ZERO_SECONDS
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
            "late_after_packet_grace_seconds",
            _require_nonnegative_seconds(
                "late_after_packet_grace_seconds",
                self.late_after_packet_grace_seconds,
            ),
        )
        reject_unsafe_surface_fields(
            "research packet event timeline completeness v2 config",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketEventTimelineCompletenessV2Config",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketEventTimelineCompletenessV2Input:
    packet_ref: str
    team_id: str
    category_id: str
    packet_generated_at: datetime
    initial_catalyst_at: datetime | None
    primary_source_timestamp_at: datetime | None
    probability_move_timestamp_at: datetime | None
    follow_up_source_timestamp_at: datetime | None
    resolution_update_timestamp_at: datetime | None
    packet_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "packet_ref",
            _require_canonical_string("packet_ref", self.packet_ref),
        )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            require_team_category_pair(
                "team_id",
                self.team_id,
                "category_id",
                self.category_id,
            )[1],
        )
        object.__setattr__(
            self,
            "packet_generated_at",
            _as_utc("packet_generated_at", self.packet_generated_at),
        )
        for field_name in TIMELINE_STEP_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "packet_config_version",
            _require_canonical_string(
                "packet_config_version",
                self.packet_config_version,
            ),
        )
        reject_unsafe_surface_fields(
            "research packet event timeline completeness v2 input",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketEventTimelineCompletenessV2Input",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketEventTimelineCompletenessV2Row:
    packet_ref: str
    team_id: str
    category_id: str
    packet_generated_at: datetime
    initial_catalyst_at: datetime | None
    primary_source_timestamp_at: datetime | None
    probability_move_timestamp_at: datetime | None
    follow_up_source_timestamp_at: datetime | None
    resolution_update_timestamp_at: datetime | None
    packet_config_version: str
    late_after_packet_grace_seconds: Decimal
    row_status: str
    present_step_count: Decimal
    complete_step_count: Decimal
    missing_step_count: Decimal
    late_step_count: Decimal
    completeness_ratio: Decimal
    missing_step_codes: tuple[str, ...]
    late_step_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    timeline_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "packet_ref",
            _require_canonical_string("packet_ref", self.packet_ref),
        )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            require_team_category_pair(
                "team_id",
                self.team_id,
                "category_id",
                self.category_id,
            )[1],
        )
        object.__setattr__(
            self,
            "packet_generated_at",
            _as_utc("packet_generated_at", self.packet_generated_at),
        )
        for field_name in TIMELINE_STEP_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "packet_config_version",
            _require_canonical_string(
                "packet_config_version",
                self.packet_config_version,
            ),
        )
        object.__setattr__(
            self,
            "late_after_packet_grace_seconds",
            _require_nonnegative_seconds(
                "late_after_packet_grace_seconds",
                self.late_after_packet_grace_seconds,
            ),
        )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        for field_name in (
            "present_step_count",
            "complete_step_count",
            "missing_step_count",
            "late_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completeness_ratio",
            _require_ratio("completeness_ratio", self.completeness_ratio),
        )
        object.__setattr__(
            self,
            "missing_step_codes",
            _normalize_step_codes(
                "missing_step_codes",
                self.missing_step_codes,
                MISSING_STEP_CODES,
            ),
        )
        object.__setattr__(
            self,
            "late_step_codes",
            _normalize_step_codes(
                "late_step_codes",
                self.late_step_codes,
                LATE_STEP_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "timeline_digest",
            _require_digest("timeline_digest", self.timeline_digest),
        )
        _validate_row(self)
        reject_unsafe_surface_fields(
            "research packet event timeline completeness v2 row",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketEventTimelineCompletenessV2Row",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketEventTimelineCompletenessV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    source_packet_count: Decimal
    complete_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    required_step_count: Decimal
    complete_step_count: Decimal
    missing_step_count: Decimal
    late_step_count: Decimal
    completeness_ratio: Decimal
    report_digest: str
    rows: tuple[ResearchPacketEventTimelineCompletenessV2Row, ...]
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
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "source_packet_count",
            "complete_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "required_step_count",
            "complete_step_count",
            "missing_step_count",
            "late_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completeness_ratio",
            _require_ratio("completeness_ratio", self.completeness_ratio),
        )
        object.__setattr__(
            self,
            "report_digest",
            _require_digest("report_digest", self.report_digest),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "research packet event timeline completeness v2 report",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketEventTimelineCompletenessV2Report",
            self,
        )


def build_research_packet_event_timeline_completeness_v2_report(
    packets: object,
    *,
    config: ResearchPacketEventTimelineCompletenessV2Config,
    generated_at: datetime,
) -> ResearchPacketEventTimelineCompletenessV2Report:
    if type(config) is not ResearchPacketEventTimelineCompletenessV2Config:
        raise ValueError(
            "config must be a ResearchPacketEventTimelineCompletenessV2Config",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(packets, generated_at=generated_at_utc)
    rows = _normalize_rows(
        tuple(_row(row, config=config) for row in input_rows),
    )
    source_packet_count = _decimal_count(len(rows))
    complete_step_count = _sum_decimals(row.complete_step_count for row in rows)
    required_step_count = _decimal_count(len(rows) * len(TIMELINE_STEP_FIELDS))
    report_status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchPacketEventTimelineCompletenessV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        reason_codes=reason_codes,
        source_packet_count=source_packet_count,
        complete_packet_count=_status_count(rows, "complete"),
        watch_packet_count=_status_count(rows, "watch"),
        blocked_packet_count=_status_count(rows, "blocked"),
        required_step_count=required_step_count,
        complete_step_count=complete_step_count,
        missing_step_count=_sum_decimals(row.missing_step_count for row in rows),
        late_step_count=_sum_decimals(row.late_step_count for row in rows),
        completeness_ratio=_ratio(complete_step_count, required_step_count),
        report_digest=_report_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            report_status=report_status,
            reason_codes=reason_codes,
            rows=rows,
        ),
        rows=rows,
    )


def research_packet_event_timeline_completeness_v2_report_to_payload(
    report: ResearchPacketEventTimelineCompletenessV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketEventTimelineCompletenessV2Report:
        raise ValueError(
            "report must be a ResearchPacketEventTimelineCompletenessV2Report",
        )
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report must convert to a JSON object")
    reject_unsafe_surface_fields(
        "research packet event timeline completeness v2 payload",
        payload,
    )
    return payload


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketEventTimelineCompletenessV2Input, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    rows = tuple(value)
    seen_packet_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketEventTimelineCompletenessV2Input:
            raise ValueError(
                "packets must contain ResearchPacketEventTimelineCompletenessV2Input values",
            )
        require_paper_only_flags("input", row)
        for field_name in ("packet_generated_at", *TIMELINE_STEP_FIELDS):
            timestamp = getattr(row, field_name)
            if timestamp is not None and timestamp > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")
        if row.packet_ref in seen_packet_refs:
            raise ValueError("packet_ref values must be unique")
        seen_packet_refs.add(row.packet_ref)
    return tuple(
        sorted(
            rows,
            key=lambda row: (row.team_id, row.category_id, row.packet_ref),
        ),
    )


def _row(
    value: ResearchPacketEventTimelineCompletenessV2Input,
    *,
    config: ResearchPacketEventTimelineCompletenessV2Config,
) -> ResearchPacketEventTimelineCompletenessV2Row:
    missing_step_codes = _missing_step_codes(value)
    late_step_codes = _late_step_codes(
        value,
        late_after_packet_grace_seconds=config.late_after_packet_grace_seconds,
    )
    present_step_count = _decimal_count(len(TIMELINE_STEP_FIELDS) - len(missing_step_codes))
    missing_step_count = _decimal_count(len(missing_step_codes))
    late_step_count = _decimal_count(len(late_step_codes))
    complete_step_count = _decimal_count(
        len(TIMELINE_STEP_FIELDS) - len(missing_step_codes) - len(late_step_codes),
    )
    reason_codes = _row_reason_codes(
        missing_step_codes=missing_step_codes,
        late_step_codes=late_step_codes,
    )
    row_status = _row_status(
        missing_step_codes=missing_step_codes,
        late_step_codes=late_step_codes,
    )
    return ResearchPacketEventTimelineCompletenessV2Row(
        packet_ref=value.packet_ref,
        team_id=value.team_id,
        category_id=value.category_id,
        packet_generated_at=value.packet_generated_at,
        initial_catalyst_at=value.initial_catalyst_at,
        primary_source_timestamp_at=value.primary_source_timestamp_at,
        probability_move_timestamp_at=value.probability_move_timestamp_at,
        follow_up_source_timestamp_at=value.follow_up_source_timestamp_at,
        resolution_update_timestamp_at=value.resolution_update_timestamp_at,
        packet_config_version=value.packet_config_version,
        late_after_packet_grace_seconds=config.late_after_packet_grace_seconds,
        row_status=row_status,
        present_step_count=present_step_count,
        complete_step_count=complete_step_count,
        missing_step_count=missing_step_count,
        late_step_count=late_step_count,
        completeness_ratio=_ratio(complete_step_count, REQUIRED_STEP_COUNT),
        missing_step_codes=missing_step_codes,
        late_step_codes=late_step_codes,
        reason_codes=reason_codes,
        timeline_digest=_timeline_digest(
            value,
            late_after_packet_grace_seconds=config.late_after_packet_grace_seconds,
            row_status=row_status,
            missing_step_codes=missing_step_codes,
            late_step_codes=late_step_codes,
            reason_codes=reason_codes,
        ),
    )


def _missing_step_codes(
    row: ResearchPacketEventTimelineCompletenessV2Input
    | ResearchPacketEventTimelineCompletenessV2Row,
) -> tuple[str, ...]:
    return tuple(
        MISSING_STEP_CODE_BY_FIELD[field_name]
        for field_name in TIMELINE_STEP_FIELDS
        if getattr(row, field_name) is None
    )


def _late_step_codes(
    row: ResearchPacketEventTimelineCompletenessV2Input
    | ResearchPacketEventTimelineCompletenessV2Row,
    *,
    late_after_packet_grace_seconds: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    for field_name in TIMELINE_STEP_FIELDS:
        timestamp = getattr(row, field_name)
        if timestamp is not None and _is_late_after_packet(
            timestamp=timestamp,
            packet_generated_at=row.packet_generated_at,
            late_after_packet_grace_seconds=late_after_packet_grace_seconds,
        ):
            codes.append(LATE_STEP_CODE_BY_FIELD[field_name])
    return tuple(codes)


def _is_late_after_packet(
    *,
    timestamp: datetime,
    packet_generated_at: datetime,
    late_after_packet_grace_seconds: Decimal,
) -> bool:
    if timestamp <= packet_generated_at:
        return False
    return (
        _duration_seconds(later=timestamp, earlier=packet_generated_at)
        > late_after_packet_grace_seconds
    )


def _row_reason_codes(
    *,
    missing_step_codes: tuple[str, ...],
    late_step_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not missing_step_codes and not late_step_codes:
        return (COMPLETE_REASON,)
    reasons: list[str] = []
    if missing_step_codes:
        reasons.append(MISSING_STEPS_REASON)
    if late_step_codes:
        reasons.append(LATE_STEPS_REASON)
    reasons.extend(missing_step_codes)
    reasons.extend(late_step_codes)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _row_status(
    *,
    missing_step_codes: tuple[str, ...],
    late_step_codes: tuple[str, ...],
) -> str:
    if missing_step_codes:
        return "blocked"
    if late_step_codes:
        return "watch"
    return "complete"


def _report_status(rows: tuple[ResearchPacketEventTimelineCompletenessV2Row, ...]) -> str:
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "complete"


def _report_reason_codes(
    rows: tuple[ResearchPacketEventTimelineCompletenessV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "complete":
        return (COMPLETE_REASON,)
    reasons = [BLOCKED_REASON if status == "blocked" else WATCH_REASON]
    if any(MISSING_STEPS_REASON in row.reason_codes for row in rows):
        reasons.append(MISSING_STEPS_REASON)
    if any(LATE_STEPS_REASON in row.reason_codes for row in rows):
        reasons.append(LATE_STEPS_REASON)
    for code in (*MISSING_STEP_CODES, *LATE_STEP_CODES):
        if any(code in row.reason_codes for row in rows):
            reasons.append(code)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketEventTimelineCompletenessV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_packet_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketEventTimelineCompletenessV2Row:
            raise ValueError(
                "rows must contain ResearchPacketEventTimelineCompletenessV2Row values",
            )
        require_paper_only_flags("row", row)
        if row.packet_ref in seen_packet_refs:
            raise ValueError("row packet_ref values must be unique")
        seen_packet_refs.add(row.packet_ref)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchPacketEventTimelineCompletenessV2Row,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_WEIGHT[row.row_status],
        -row.missing_step_count,
        -row.late_step_count,
        row.team_id,
        row.category_id,
        row.packet_ref,
    )


def _status_count(
    rows: tuple[ResearchPacketEventTimelineCompletenessV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _validate_row(row: ResearchPacketEventTimelineCompletenessV2Row) -> None:
    missing_step_codes = _missing_step_codes(row)
    late_step_codes = _late_step_codes(
        row,
        late_after_packet_grace_seconds=row.late_after_packet_grace_seconds,
    )
    if row.missing_step_codes != missing_step_codes:
        raise ValueError("missing_step_codes must match timeline fields")
    if row.late_step_codes != late_step_codes:
        raise ValueError("late_step_codes must match timeline fields")
    if row.present_step_count != _decimal_count(len(TIMELINE_STEP_FIELDS) - len(missing_step_codes)):
        raise ValueError("present_step_count must match timeline fields")
    if row.missing_step_count != _decimal_count(len(missing_step_codes)):
        raise ValueError("missing_step_count must match missing_step_codes")
    if row.late_step_count != _decimal_count(len(late_step_codes)):
        raise ValueError("late_step_count must match late_step_codes")
    complete_step_count = _decimal_count(
        len(TIMELINE_STEP_FIELDS) - len(missing_step_codes) - len(late_step_codes),
    )
    if row.complete_step_count != complete_step_count:
        raise ValueError("complete_step_count must match timeline fields")
    if row.completeness_ratio != _ratio(row.complete_step_count, REQUIRED_STEP_COUNT):
        raise ValueError("completeness_ratio must match complete_step_count")
    if row.row_status != _row_status(
        missing_step_codes=missing_step_codes,
        late_step_codes=late_step_codes,
    ):
        raise ValueError("row_status must match timeline fields")
    if row.reason_codes != _row_reason_codes(
        missing_step_codes=missing_step_codes,
        late_step_codes=late_step_codes,
    ):
        raise ValueError("reason_codes must match timeline fields")
    if row.timeline_digest != _timeline_digest(
        row,
        late_after_packet_grace_seconds=row.late_after_packet_grace_seconds,
        row_status=row.row_status,
        missing_step_codes=row.missing_step_codes,
        late_step_codes=row.late_step_codes,
        reason_codes=row.reason_codes,
    ):
        raise ValueError("timeline_digest must match timeline fields")


def _validate_report(report: ResearchPacketEventTimelineCompletenessV2Report) -> None:
    if report.source_packet_count != _decimal_count(len(report.rows)):
        raise ValueError("source_packet_count must match rows")
    for field_name, status in (
        ("complete_packet_count", "complete"),
        ("watch_packet_count", "watch"),
        ("blocked_packet_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if (
        report.complete_packet_count
        + report.watch_packet_count
        + report.blocked_packet_count
        != report.source_packet_count
    ):
        raise ValueError("packet status counts must match source_packet_count")
    if report.required_step_count != _decimal_count(
        len(report.rows) * len(TIMELINE_STEP_FIELDS),
    ):
        raise ValueError("required_step_count must match rows")
    for field_name in ("complete_step_count", "missing_step_count", "late_step_count"):
        if getattr(report, field_name) != _sum_decimals(
            getattr(row, field_name) for row in report.rows
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.completeness_ratio != _ratio(
        report.complete_step_count,
        report.required_step_count,
    ):
        raise ValueError("completeness_ratio must match complete_step_count")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_digest != _report_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_status=report.report_status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    ):
        raise ValueError("report_digest must match rows")


def _timeline_digest(
    row: ResearchPacketEventTimelineCompletenessV2Input
    | ResearchPacketEventTimelineCompletenessV2Row,
    *,
    late_after_packet_grace_seconds: Decimal,
    row_status: str,
    missing_step_codes: tuple[str, ...],
    late_step_codes: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> str:
    return _stable_digest(
        (
            "research_packet_event_timeline_completeness_v2_row",
            row.packet_ref,
            row.team_id,
            row.category_id,
            _datetime_token(row.packet_generated_at),
            *(_datetime_token(getattr(row, field_name)) for field_name in TIMELINE_STEP_FIELDS),
            row.packet_config_version,
            str(late_after_packet_grace_seconds),
            row_status,
            ",".join(missing_step_codes),
            ",".join(late_step_codes),
            ",".join(reason_codes),
        ),
    )


def _report_digest(
    *,
    generated_at: datetime,
    config_version: str,
    report_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchPacketEventTimelineCompletenessV2Row, ...],
) -> str:
    return _stable_digest(
        (
            "research_packet_event_timeline_completeness_v2_report",
            _datetime_token(generated_at),
            config_version,
            report_status,
            ",".join(reason_codes),
            *(row.timeline_digest for row in rows),
        ),
    )


def _stable_digest(parts: tuple[str, ...]) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _datetime_token(value: datetime | None) -> str:
    if value is None:
        return ""
    return _as_utc("timestamp", value).isoformat()


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


def _duration_seconds(*, later: datetime, earlier: datetime) -> Decimal:
    delta = _as_utc("later", later) - _as_utc("earlier", earlier)
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize_seconds(seconds)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANT)


def _sum_decimals(values: object) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must contain Decimal")
        total += value
    return total.quantize(COUNT_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANT)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    seconds = _quantize_seconds(_require_decimal(field_name, value))
    if seconds < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return seconds


def _quantize_seconds(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(SECONDS_QUANT)
    except InvalidOperation as exc:
        raise ValueError("seconds value must be quantizable") from exc


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    count = _require_decimal(field_name, value).quantize(COUNT_QUANT)
    if count < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if count != value:
        raise ValueError(f"{field_name} must be integral")
    return count


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_decimal(field_name, value).quantize(RATIO_QUANT)
    if ratio < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if ratio > ONE_RATIO:
        raise ValueError(f"{field_name} must be <= 1")
    return ratio


def _normalize_step_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(code for code in allowed if code in codes)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must contain at least one value")
    for code in codes:
        _require_member("reason_code", code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(code for code in REASON_CODES if code in codes)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    lowered = value.lower()
    if lowered != value or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


__all__ = (
    "BLOCKED_REASON",
    "COMPLETE_REASON",
    "DEFAULT_RESEARCH_PACKET_EVENT_TIMELINE_COMPLETENESS_V2_CONFIG_VERSION",
    "LATE_STEP_CODES",
    "LATE_STEP_CODE_BY_FIELD",
    "LATE_STEPS_REASON",
    "MISSING_STEP_CODES",
    "MISSING_STEP_CODE_BY_FIELD",
    "MISSING_STEPS_REASON",
    "REASON_CODES",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "ResearchPacketEventTimelineCompletenessV2Config",
    "ResearchPacketEventTimelineCompletenessV2Input",
    "ResearchPacketEventTimelineCompletenessV2Report",
    "ResearchPacketEventTimelineCompletenessV2Row",
    "TIMELINE_STEP_FIELDS",
    "WATCH_REASON",
    "build_research_packet_event_timeline_completeness_v2_report",
    "research_packet_event_timeline_completeness_v2_report_to_payload",
)
