"""Pure in-memory priority report for source ack rechecks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_PRIORITY_CONFIG_VERSION = (
    "research-packet-source-ack-recheck-priority-v0"
)

ROW_STATUSES = ("critical", "watch", "clear")
REPORT_STATUSES = ("empty", "critical", "watch", "clear")
ROW_REASON_CODES = (
    "source_ack_priority_missing_ack_pressure_critical",
    "source_ack_priority_missing_ack_pressure_watch",
    "source_ack_priority_stale_recheck_age_critical",
    "source_ack_priority_stale_recheck_age_watch",
    "source_ack_priority_reliability_gap_critical",
    "source_ack_priority_reliability_gap_watch",
    "source_ack_priority_never_rechecked",
    "source_ack_priority_clear",
)
REPORT_REASON_CODES = ("source_ack_priority_empty", *ROW_REASON_CODES)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UTC_OFFSET = timedelta(0)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cre", "den", "tial"),
        _join_parts("pri", "vate", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("au", "th"),
        _join_parts("li", "ve"),
        _join_parts("fa", "st"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckPriorityConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_PRIORITY_CONFIG_VERSION
    missing_ack_watch_ratio: Decimal = Decimal("0.250000")
    missing_ack_critical_ratio: Decimal = Decimal("0.500000")
    stale_recheck_watch_seconds: Decimal = Decimal("86400.000000")
    stale_recheck_critical_seconds: Decimal = Decimal("172800.000000")
    reliability_gap_watch: Decimal = Decimal("0.100000")
    reliability_gap_critical: Decimal = Decimal("0.250000")
    min_source_reliability_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in ("missing_ack_watch_ratio", "missing_ack_critical_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_recheck_watch_seconds", "stale_recheck_critical_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("reliability_gap_watch", "reliability_gap_critical"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_reliability_score",
            _normalize_ratio(
                "min_source_reliability_score",
                self.min_source_reliability_score,
            ),
        )
        _validate_config(self)
        reject_unsafe_surface_fields("source ack priority config", self)
        require_paper_only_flags("priority config", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckPriorityInput:
    packet_id: str
    team_id: str
    category_id: str
    source_family: str
    requested_at: datetime
    last_rechecked_at: datetime | None
    required_ack_count: Decimal
    acknowledged_ack_count: Decimal
    source_reliability_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("packet_id", self.packet_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_family", self.source_family)
        object.__setattr__(self, "requested_at", _as_utc("requested_at", self.requested_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "required_ack_count",
            _normalize_positive_count("required_ack_count", self.required_ack_count),
        )
        object.__setattr__(
            self,
            "acknowledged_ack_count",
            _normalize_nonnegative_count(
                "acknowledged_ack_count",
                self.acknowledged_ack_count,
            ),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_ratio("source_reliability_score", self.source_reliability_score),
        )
        _validate_input(self)
        reject_unsafe_surface_fields("source ack priority input", self)
        require_paper_only_flags("priority input", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckPriorityRow:
    priority_rank: Decimal
    packet_id: str
    team_id: str
    category_id: str
    source_family: str
    priority_status: str
    requested_at: datetime
    last_rechecked_at: datetime | None
    required_ack_count: Decimal
    acknowledged_ack_count: Decimal
    missing_ack_count: Decimal
    missing_ack_pressure_ratio: Decimal
    stale_recheck_age_seconds: Decimal
    source_reliability_score: Decimal
    source_reliability_gap: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        _require_public_string("packet_id", self.packet_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_family", self.source_family)
        _require_member("priority_status", self.priority_status, ROW_STATUSES)
        object.__setattr__(self, "requested_at", _as_utc("requested_at", self.requested_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "required_ack_count",
            _normalize_positive_count("required_ack_count", self.required_ack_count),
        )
        for field_name in ("acknowledged_ack_count", "missing_ack_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_ack_pressure_ratio",
            _normalize_ratio(
                "missing_ack_pressure_ratio",
                self.missing_ack_pressure_ratio,
            ),
        )
        object.__setattr__(
            self,
            "stale_recheck_age_seconds",
            _normalize_nonnegative_seconds(
                "stale_recheck_age_seconds",
                self.stale_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_ratio("source_reliability_score", self.source_reliability_score),
        )
        object.__setattr__(
            self,
            "source_reliability_gap",
            _normalize_ratio("source_reliability_gap", self.source_reliability_gap),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("source ack priority row", self)
        require_paper_only_flags("priority row", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckPriorityReport:
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    critical_packet_count: Decimal
    watch_packet_count: Decimal
    clear_packet_count: Decimal
    missing_ack_packet_count: Decimal
    stale_recheck_packet_count: Decimal
    reliability_gap_packet_count: Decimal
    max_missing_ack_pressure_ratio: Decimal
    max_stale_recheck_age_seconds: Decimal
    max_source_reliability_gap: Decimal
    rows: tuple[ResearchPacketSourceAckRecheckPriorityRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "critical_packet_count",
            "watch_packet_count",
            "clear_packet_count",
            "missing_ack_packet_count",
            "stale_recheck_packet_count",
            "reliability_gap_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_missing_ack_pressure_ratio",
            _normalize_ratio(
                "max_missing_ack_pressure_ratio",
                self.max_missing_ack_pressure_ratio,
            ),
        )
        object.__setattr__(
            self,
            "max_stale_recheck_age_seconds",
            _normalize_nonnegative_seconds(
                "max_stale_recheck_age_seconds",
                self.max_stale_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_source_reliability_gap",
            _normalize_ratio(
                "max_source_reliability_gap",
                self.max_source_reliability_gap,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("source ack priority report", self)
        require_paper_only_flags("priority report", self)


def build_research_packet_source_ack_recheck_priority_report(
    packets: Iterable[ResearchPacketSourceAckRecheckPriorityInput],
    *,
    config: ResearchPacketSourceAckRecheckPriorityConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckPriorityReport:
    if type(config) is not ResearchPacketSourceAckRecheckPriorityConfig:
        raise ValueError("config must be a ResearchPacketSourceAckRecheckPriorityConfig")
    require_paper_only_flags("priority config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(packets)
    _validate_input_times(inputs, generated_at_utc)
    base_rows = tuple(
        _priority_row(row, config=config, generated_at=generated_at_utc)
        for row in inputs
    )
    rows = tuple(
        _with_priority_rank(row, index)
        for index, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )

    return ResearchPacketSourceAckRecheckPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        packet_count=_count(len(rows)),
        critical_packet_count=_status_count(rows, "critical"),
        watch_packet_count=_status_count(rows, "watch"),
        clear_packet_count=_status_count(rows, "clear"),
        missing_ack_packet_count=_count(
            sum(1 for row in rows if row.missing_ack_count > ZERO_COUNT),
        ),
        stale_recheck_packet_count=_count(
            sum(1 for row in rows if _has_stale_reason(row)),
        ),
        reliability_gap_packet_count=_count(
            sum(1 for row in rows if row.source_reliability_gap > ZERO_RATIO),
        ),
        max_missing_ack_pressure_ratio=_max_ratio(
            tuple(row.missing_ack_pressure_ratio for row in rows),
        ),
        max_stale_recheck_age_seconds=_max_seconds(
            tuple(row.stale_recheck_age_seconds for row in rows),
        ),
        max_source_reliability_gap=_max_ratio(
            tuple(row.source_reliability_gap for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_source_ack_recheck_priority_report_to_payload(
    report: ResearchPacketSourceAckRecheckPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketSourceAckRecheckPriorityReport:
        raise ValueError("report must be a ResearchPacketSourceAckRecheckPriorityReport")
    reject_unsafe_surface_fields("source ack priority report", report)
    require_paper_only_flags("priority report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("source ack priority payload", payload)
    return payload


def _priority_row(
    row: ResearchPacketSourceAckRecheckPriorityInput,
    *,
    config: ResearchPacketSourceAckRecheckPriorityConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckPriorityRow:
    missing_ack_count = row.required_ack_count - row.acknowledged_ack_count
    missing_ack_pressure_ratio = _ratio(missing_ack_count, row.required_ack_count)
    stale_recheck_age_seconds = _duration_seconds(
        row.requested_at if row.last_rechecked_at is None else row.last_rechecked_at,
        generated_at,
    )
    source_reliability_gap = _source_reliability_gap(
        score=row.source_reliability_score,
        minimum=config.min_source_reliability_score,
    )
    reason_codes = _row_reason_codes(
        missing_ack_pressure_ratio=missing_ack_pressure_ratio,
        stale_recheck_age_seconds=stale_recheck_age_seconds,
        source_reliability_gap=source_reliability_gap,
        never_rechecked=row.last_rechecked_at is None,
        config=config,
    )
    return ResearchPacketSourceAckRecheckPriorityRow(
        priority_rank=_count(1),
        packet_id=row.packet_id,
        team_id=row.team_id,
        category_id=row.category_id,
        source_family=row.source_family,
        priority_status=_priority_status(reason_codes),
        requested_at=row.requested_at,
        last_rechecked_at=row.last_rechecked_at,
        required_ack_count=row.required_ack_count,
        acknowledged_ack_count=row.acknowledged_ack_count,
        missing_ack_count=missing_ack_count,
        missing_ack_pressure_ratio=missing_ack_pressure_ratio,
        stale_recheck_age_seconds=stale_recheck_age_seconds,
        source_reliability_score=row.source_reliability_score,
        source_reliability_gap=source_reliability_gap,
        reason_codes=reason_codes,
    )


def _with_priority_rank(
    row: ResearchPacketSourceAckRecheckPriorityRow,
    index: int,
) -> ResearchPacketSourceAckRecheckPriorityRow:
    return ResearchPacketSourceAckRecheckPriorityRow(
        priority_rank=_count(index),
        packet_id=row.packet_id,
        team_id=row.team_id,
        category_id=row.category_id,
        source_family=row.source_family,
        priority_status=row.priority_status,
        requested_at=row.requested_at,
        last_rechecked_at=row.last_rechecked_at,
        required_ack_count=row.required_ack_count,
        acknowledged_ack_count=row.acknowledged_ack_count,
        missing_ack_count=row.missing_ack_count,
        missing_ack_pressure_ratio=row.missing_ack_pressure_ratio,
        stale_recheck_age_seconds=row.stale_recheck_age_seconds,
        source_reliability_score=row.source_reliability_score,
        source_reliability_gap=row.source_reliability_gap,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    missing_ack_pressure_ratio: Decimal,
    stale_recheck_age_seconds: Decimal,
    source_reliability_gap: Decimal,
    never_rechecked: bool,
    config: ResearchPacketSourceAckRecheckPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_ack_pressure_ratio >= config.missing_ack_critical_ratio:
        reason_codes.append("source_ack_priority_missing_ack_pressure_critical")
    elif missing_ack_pressure_ratio >= config.missing_ack_watch_ratio:
        reason_codes.append("source_ack_priority_missing_ack_pressure_watch")
    if stale_recheck_age_seconds >= config.stale_recheck_critical_seconds:
        reason_codes.append("source_ack_priority_stale_recheck_age_critical")
    elif stale_recheck_age_seconds >= config.stale_recheck_watch_seconds:
        reason_codes.append("source_ack_priority_stale_recheck_age_watch")
    if source_reliability_gap >= config.reliability_gap_critical:
        reason_codes.append("source_ack_priority_reliability_gap_critical")
    elif source_reliability_gap >= config.reliability_gap_watch:
        reason_codes.append("source_ack_priority_reliability_gap_watch")
    if never_rechecked:
        reason_codes.append("source_ack_priority_never_rechecked")
    if not reason_codes:
        reason_codes.append("source_ack_priority_clear")
    return tuple(reason_codes)


def _priority_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_critical") for reason_code in reason_codes):
        return "critical"
    if reason_codes == ("source_ack_priority_clear",):
        return "clear"
    return "watch"


def _report_status(rows: tuple[ResearchPacketSourceAckRecheckPriorityRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.priority_status == "critical" for row in rows):
        return "critical"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceAckRecheckPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_ack_priority_empty",)
    reason_codes = tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code != "source_ack_priority_clear"
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reason_codes:
        return reason_codes
    return ("source_ack_priority_clear",)


def _normalize_inputs(
    value: Iterable[ResearchPacketSourceAckRecheckPriorityInput],
) -> tuple[ResearchPacketSourceAckRecheckPriorityInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("packets must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("packets must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckPriorityInput:
            raise ValueError(
                "packets must contain ResearchPacketSourceAckRecheckPriorityInput values",
            )
        require_paper_only_flags("priority input", row)
        if row.packet_id in seen:
            raise ValueError("packet_id values must be unique")
        seen.add(row.packet_id)
    return rows


def _normalize_rows(
    value: Iterable[ResearchPacketSourceAckRecheckPriorityRow],
) -> tuple[ResearchPacketSourceAckRecheckPriorityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckPriorityRow:
            raise ValueError("rows must contain priority row values")
        require_paper_only_flags("priority row", row)
        if row.packet_id in seen:
            raise ValueError("rows packet_id values must be unique")
        seen.add(row.packet_id)
    return rows


def _validate_config(config: ResearchPacketSourceAckRecheckPriorityConfig) -> None:
    if config.missing_ack_watch_ratio <= ZERO_RATIO:
        raise ValueError("missing_ack_watch_ratio must be positive")
    if config.missing_ack_critical_ratio < config.missing_ack_watch_ratio:
        raise ValueError("missing_ack_critical_ratio must be >= missing_ack_watch_ratio")
    if config.stale_recheck_critical_seconds < config.stale_recheck_watch_seconds:
        raise ValueError(
            "stale_recheck_critical_seconds must be >= stale_recheck_watch_seconds",
        )
    if config.reliability_gap_watch <= ZERO_RATIO:
        raise ValueError("reliability_gap_watch must be positive")
    if config.reliability_gap_critical < config.reliability_gap_watch:
        raise ValueError("reliability_gap_critical must be >= reliability_gap_watch")


def _validate_input(row: ResearchPacketSourceAckRecheckPriorityInput) -> None:
    if row.acknowledged_ack_count > row.required_ack_count:
        raise ValueError("acknowledged_ack_count must not exceed required_ack_count")
    if row.last_rechecked_at is not None and row.last_rechecked_at < row.requested_at:
        raise ValueError("last_rechecked_at must be >= requested_at")


def _validate_row(row: ResearchPacketSourceAckRecheckPriorityRow) -> None:
    if row.acknowledged_ack_count > row.required_ack_count:
        raise ValueError("acknowledged_ack_count must not exceed required_ack_count")
    if row.missing_ack_count != row.required_ack_count - row.acknowledged_ack_count:
        raise ValueError("missing_ack_count must match ack counts")
    if row.missing_ack_pressure_ratio != _ratio(
        row.missing_ack_count,
        row.required_ack_count,
    ):
        raise ValueError("missing_ack_pressure_ratio must match ack counts")
    if row.last_rechecked_at is not None and row.last_rechecked_at < row.requested_at:
        raise ValueError("last_rechecked_at must be >= requested_at")
    if row.priority_status != _priority_status(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")


def _validate_report(report: ResearchPacketSourceAckRecheckPriorityReport) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.critical_packet_count != _status_count(report.rows, "critical"):
        raise ValueError("critical_packet_count must match rows")
    if report.watch_packet_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_packet_count must match rows")
    if report.clear_packet_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_packet_count must match rows")
    if report.missing_ack_packet_count != _count(
        sum(1 for row in report.rows if row.missing_ack_count > ZERO_COUNT),
    ):
        raise ValueError("missing_ack_packet_count must match rows")
    if report.stale_recheck_packet_count != _count(
        sum(1 for row in report.rows if _has_stale_reason(row)),
    ):
        raise ValueError("stale_recheck_packet_count must match rows")
    if report.reliability_gap_packet_count != _count(
        sum(1 for row in report.rows if row.source_reliability_gap > ZERO_RATIO),
    ):
        raise ValueError("reliability_gap_packet_count must match rows")
    if report.max_missing_ack_pressure_ratio != _max_ratio(
        tuple(row.missing_ack_pressure_ratio for row in report.rows),
    ):
        raise ValueError("max_missing_ack_pressure_ratio must match rows")
    if report.max_stale_recheck_age_seconds != _max_seconds(
        tuple(row.stale_recheck_age_seconds for row in report.rows),
    ):
        raise ValueError("max_stale_recheck_age_seconds must match rows")
    if report.max_source_reliability_gap != _max_ratio(
        tuple(row.source_reliability_gap for row in report.rows),
    ):
        raise ValueError("max_source_reliability_gap must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for index, row in enumerate(report.rows, start=1):
        if row.priority_rank != _count(index):
            raise ValueError("priority_rank values must be sequential")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sorting")


def _validate_input_times(
    rows: tuple[ResearchPacketSourceAckRecheckPriorityInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.requested_at > generated_at:
            raise ValueError("requested_at must be <= generated_at")
        if row.last_rechecked_at is not None and row.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must be <= generated_at")


def _row_sort_key(
    row: ResearchPacketSourceAckRecheckPriorityRow,
) -> tuple[Decimal, Decimal, Decimal, tuple[str, ...], str, str, str, str]:
    return (
        -row.missing_ack_pressure_ratio,
        -row.stale_recheck_age_seconds,
        -row.source_reliability_gap,
        row.reason_codes,
        row.team_id,
        row.category_id,
        row.source_family,
        row.packet_id,
    )


def _status_count(
    rows: tuple[ResearchPacketSourceAckRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.priority_status == status))


def _has_stale_reason(row: ResearchPacketSourceAckRecheckPriorityRow) -> bool:
    return (
        "source_ack_priority_stale_recheck_age_critical" in row.reason_codes
        or "source_ack_priority_stale_recheck_age_watch" in row.reason_codes
    )


def _source_reliability_gap(*, score: Decimal, minimum: Decimal) -> Decimal:
    if score >= minimum:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (minimum - score).quantize(RATIO_QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end time must be >= start time")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return seconds.quantize(SECONDS_QUANTUM)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO_RATIO)


def _max_seconds(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO_SECONDS)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(COUNT_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a whole-number Decimal") from exc


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(RATIO_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a ratio Decimal") from exc


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_seconds(field_name, value)
    if decimal_value <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(SECONDS_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a seconds Decimal") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != UTC_OFFSET:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical string")


def _reject_unsafe_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain a canonical string")
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains an unsafe surface fragment")


def _normalize_row_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    codes = _reason_code_tuple(field_name, value)
    _require_reason_codes_known(field_name, codes, ROW_REASON_CODES, "known row reason codes")
    _require_reason_codes_unique(codes)
    if "source_ack_priority_clear" in codes and codes != ("source_ack_priority_clear",):
        raise ValueError("source_ack_priority_clear must be exclusive")
    _require_reason_codes_deterministic(codes, ROW_REASON_CODES)
    return codes


def _normalize_report_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    codes = _reason_code_tuple(field_name, value)
    _require_reason_codes_known(field_name, codes, REPORT_REASON_CODES, "known reason codes")
    _require_reason_codes_unique(codes)
    if "source_ack_priority_empty" in codes and codes != ("source_ack_priority_empty",):
        raise ValueError("source_ack_priority_empty must be exclusive")
    if "source_ack_priority_clear" in codes and codes != ("source_ack_priority_clear",):
        raise ValueError("source_ack_priority_clear must be exclusive")
    _require_reason_codes_deterministic(codes, REPORT_REASON_CODES)
    return codes


def _reason_code_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    return codes


def _require_reason_codes_known(
    field_name: str,
    codes: tuple[str, ...],
    allowed: tuple[str, ...],
    label: str,
) -> None:
    for code in codes:
        if type(code) is not str or code not in allowed:
            raise ValueError(f"{field_name} must contain {label}")


def _require_reason_codes_unique(codes: tuple[str, ...]) -> None:
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")


def _require_reason_codes_deterministic(
    codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> None:
    expected = tuple(code for code in allowed if code in codes)
    if codes != expected:
        raise ValueError("reason_codes must be deterministic")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_PRIORITY_CONFIG_VERSION",
    "ResearchPacketSourceAckRecheckPriorityConfig",
    "ResearchPacketSourceAckRecheckPriorityInput",
    "ResearchPacketSourceAckRecheckPriorityReport",
    "ResearchPacketSourceAckRecheckPriorityRow",
    "build_research_packet_source_ack_recheck_priority_report",
    "research_packet_source_ack_recheck_priority_report_to_payload",
)
