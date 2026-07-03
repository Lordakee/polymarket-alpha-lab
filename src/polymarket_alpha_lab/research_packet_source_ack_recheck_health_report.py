"""Pure in-memory source ack recheck health report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
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


DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_HEALTH_CONFIG_VERSION = (
    "research-packet-source-ack-recheck-health-v0"
)

ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("empty", "pass", "watch", "blocked")
EMPTY_REASON_CODE = "source_ack_recheck_health_empty"
CLEAR_REASON_CODE = "source_ack_recheck_health_clear"
LATENCY_WATCH_REASON_CODE = "source_ack_latency_watch"
LATENCY_BLOCKED_REASON_CODE = "source_ack_latency_blocked"
MISSING_ACK_REASON_CODE = "source_ack_missing_acknowledgement"
MISSING_PRESSURE_WATCH_REASON_CODE = "source_ack_missing_pressure_watch"
MISSING_PRESSURE_BLOCKED_REASON_CODE = "source_ack_missing_pressure_blocked"
FRESHNESS_WATCH_REASON_CODE = "source_ack_recheck_freshness_watch"
FRESHNESS_BLOCKED_REASON_CODE = "source_ack_recheck_freshness_blocked"
ROW_REASON_CODES = (
    CLEAR_REASON_CODE,
    LATENCY_WATCH_REASON_CODE,
    LATENCY_BLOCKED_REASON_CODE,
    MISSING_ACK_REASON_CODE,
    MISSING_PRESSURE_WATCH_REASON_CODE,
    MISSING_PRESSURE_BLOCKED_REASON_CODE,
    FRESHNESS_WATCH_REASON_CODE,
    FRESHNESS_BLOCKED_REASON_CODE,
)
REPORT_REASON_CODES = (EMPTY_REASON_CODE, *ROW_REASON_CODES)
TRIGGER_REASON_CODES = tuple(
    code for code in ROW_REASON_CODES if code != CLEAR_REASON_CODE
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}


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
    ),
)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckHealthConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_HEALTH_CONFIG_VERSION
    ack_latency_watch_seconds: Decimal = Decimal("900.000000")
    ack_latency_block_seconds: Decimal = Decimal("1800.000000")
    missing_acknowledgement_watch_count: Decimal = Decimal("1")
    missing_acknowledgement_block_count: Decimal = Decimal("2")
    recheck_freshness_watch_seconds: Decimal = Decimal("3600.000000")
    recheck_freshness_block_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "ack_latency_watch_seconds",
            "ack_latency_block_seconds",
            "recheck_freshness_watch_seconds",
            "recheck_freshness_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "missing_acknowledgement_watch_count",
            "missing_acknowledgement_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.ack_latency_watch_seconds > self.ack_latency_block_seconds:
            raise ValueError(
                "ack_latency_watch_seconds must be <= ack_latency_block_seconds",
            )
        if (
            self.missing_acknowledgement_watch_count
            > self.missing_acknowledgement_block_count
        ):
            raise ValueError(
                "missing_acknowledgement_watch_count must be <= block count",
            )
        if self.recheck_freshness_watch_seconds > self.recheck_freshness_block_seconds:
            raise ValueError(
                "recheck_freshness_watch_seconds must be <= block seconds",
            )
        require_paper_only_flags("health config", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckHealthObservation:
    observation_id: str
    packet_id: str
    source_id: str
    source_family: str
    team_id: str
    category_id: str
    source_observed_at: datetime
    acknowledged_at: datetime | None
    rechecked_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "observation_id",
            "packet_id",
            "source_id",
            "source_family",
        ):
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
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_optional_utc("rechecked_at", self.rechecked_at),
        )
        reject_unsafe_surface_fields("source ack recheck health observation", self)
        require_paper_only_flags("health observation", self)
        _validate_observation(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckHealthRow:
    observation_id: str
    packet_id: str
    source_id: str
    source_family: str
    team_id: str
    category_id: str
    status: str
    ack_latency_status: str
    missing_acknowledgement_pressure_status: str
    recheck_freshness_status: str
    source_observed_at: datetime
    acknowledged_at: datetime | None
    rechecked_at: datetime | None
    source_age_seconds: Decimal
    ack_latency_seconds: Decimal
    missing_acknowledgement_age_seconds: Decimal
    recheck_age_seconds: Decimal
    group_missing_acknowledgement_count: Decimal
    group_observation_count: Decimal
    group_missing_acknowledgement_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "observation_id",
            "packet_id",
            "source_id",
            "source_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        for field_name in (
            "status",
            "ack_latency_status",
            "missing_acknowledgement_pressure_status",
            "recheck_freshness_status",
        ):
            _require_member(field_name, getattr(self, field_name), ROW_STATUSES)
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_optional_utc("rechecked_at", self.rechecked_at),
        )
        for field_name in (
            "source_age_seconds",
            "ack_latency_seconds",
            "missing_acknowledgement_age_seconds",
            "recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "group_missing_acknowledgement_count",
            "group_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "group_missing_acknowledgement_ratio",
            _require_ratio(
                "group_missing_acknowledgement_ratio",
                self.group_missing_acknowledgement_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        reject_unsafe_surface_fields("source ack recheck health row", self)
        require_paper_only_flags("health row", self)
        _validate_health_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckHealthSummaryRow:
    team_id: str
    category_id: str
    source_family: str
    status: str
    observation_count: Decimal
    missing_acknowledgement_count: Decimal
    missing_acknowledgement_ratio: Decimal
    max_ack_latency_seconds: Decimal
    max_recheck_age_seconds: Decimal
    reason_codes: tuple[str, ...]
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
        _require_public_string("source_family", self.source_family)
        _require_member("status", self.status, ROW_STATUSES)
        for field_name in ("observation_count", "missing_acknowledgement_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_acknowledgement_ratio",
            _require_ratio(
                "missing_acknowledgement_ratio",
                self.missing_acknowledgement_ratio,
            ),
        )
        for field_name in ("max_ack_latency_seconds", "max_recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        reject_unsafe_surface_fields("source ack recheck health summary row", self)
        require_paper_only_flags("health summary row", self)
        _validate_summary_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    summary_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_acknowledgement_count: Decimal
    ack_latency_watch_count: Decimal
    ack_latency_blocked_count: Decimal
    missing_acknowledgement_pressure_count: Decimal
    recheck_freshness_watch_count: Decimal
    recheck_freshness_blocked_count: Decimal
    issue_ratio: Decimal
    max_ack_latency_seconds: Decimal
    max_missing_acknowledgement_age_seconds: Decimal
    max_recheck_age_seconds: Decimal
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...]
    summary_rows: tuple[ResearchPacketSourceAckRecheckHealthSummaryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "observation_count",
            "summary_row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "missing_acknowledgement_count",
            "ack_latency_watch_count",
            "ack_latency_blocked_count",
            "missing_acknowledgement_pressure_count",
            "recheck_freshness_watch_count",
            "recheck_freshness_blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_ratio("issue_ratio", self.issue_ratio),
        )
        for field_name in (
            "max_ack_latency_seconds",
            "max_missing_acknowledgement_age_seconds",
            "max_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_health_rows(self.rows))
        object.__setattr__(
            self,
            "summary_rows",
            _normalize_summary_rows(self.summary_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        reject_unsafe_surface_fields("source ack recheck health report", self)
        require_paper_only_flags("health report", self)
        _validate_report(self)


def build_research_packet_source_ack_recheck_health_report(
    observations: Iterable[ResearchPacketSourceAckRecheckHealthObservation],
    *,
    config: ResearchPacketSourceAckRecheckHealthConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckHealthReport:
    if type(config) is not ResearchPacketSourceAckRecheckHealthConfig:
        raise ValueError(
            "config must be a ResearchPacketSourceAckRecheckHealthConfig",
        )
    require_paper_only_flags("health config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _validate_input_times(normalized_observations, generated_at_utc)
    group_metrics = _group_missing_acknowledgement_metrics(
        normalized_observations,
        config=config,
    )
    rows = _sort_health_rows(
        tuple(
            _health_row(
                observation,
                group_metrics=group_metrics[
                    (
                        observation.team_id,
                        observation.category_id,
                        observation.source_family,
                    )
                ],
                config=config,
                generated_at=generated_at_utc,
            )
            for observation in normalized_observations
        ),
    )
    summary_rows = _summary_rows(rows)

    return ResearchPacketSourceAckRecheckHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_count(len(rows)),
        summary_row_count=_count(len(summary_rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        missing_acknowledgement_count=_count(
            sum(1 for row in rows if row.acknowledged_at is None),
        ),
        ack_latency_watch_count=_dimension_status_count(
            rows,
            "ack_latency_status",
            "watch",
        ),
        ack_latency_blocked_count=_dimension_status_count(
            rows,
            "ack_latency_status",
            "blocked",
        ),
        missing_acknowledgement_pressure_count=_count(
            sum(
                1
                for row in rows
                if row.missing_acknowledgement_pressure_status != "pass"
            ),
        ),
        recheck_freshness_watch_count=_dimension_status_count(
            rows,
            "recheck_freshness_status",
            "watch",
        ),
        recheck_freshness_blocked_count=_dimension_status_count(
            rows,
            "recheck_freshness_status",
            "blocked",
        ),
        issue_ratio=_ratio(
            _count(sum(1 for row in rows if row.status != "pass")),
            _count(len(rows)),
        ),
        max_ack_latency_seconds=_max_decimal(
            tuple(row.ack_latency_seconds for row in rows),
        ),
        max_missing_acknowledgement_age_seconds=_max_decimal(
            tuple(row.missing_acknowledgement_age_seconds for row in rows),
        ),
        max_recheck_age_seconds=_max_decimal(
            tuple(row.recheck_age_seconds for row in rows),
        ),
        rows=rows,
        summary_rows=summary_rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_source_ack_recheck_health_report_to_payload(
    report: ResearchPacketSourceAckRecheckHealthReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketSourceAckRecheckHealthReport:
        raise ValueError("report must be a ResearchPacketSourceAckRecheckHealthReport")
    reject_unsafe_surface_fields("source ack recheck health report", report)
    require_paper_only_flags("health report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("source ack recheck health payload", payload)
    return payload


def _health_row(
    observation: ResearchPacketSourceAckRecheckHealthObservation,
    *,
    group_metrics: tuple[Decimal, Decimal, Decimal, str],
    config: ResearchPacketSourceAckRecheckHealthConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckHealthRow:
    group_missing_count, group_count, group_ratio, pressure_status = group_metrics
    source_age_seconds = _duration_seconds(observation.source_observed_at, generated_at)
    ack_latency_seconds = _duration_seconds(
        observation.source_observed_at,
        observation.acknowledged_at or generated_at,
    )
    missing_age_seconds = (
        source_age_seconds if observation.acknowledged_at is None else ZERO_SECONDS
    )
    recheck_age_seconds = _duration_seconds(
        _latest_recheck_anchor(observation),
        generated_at,
    )
    ack_latency_status = _seconds_status(
        ack_latency_seconds,
        watch_seconds=config.ack_latency_watch_seconds,
        block_seconds=config.ack_latency_block_seconds,
    )
    recheck_freshness_status = _seconds_status(
        recheck_age_seconds,
        watch_seconds=config.recheck_freshness_watch_seconds,
        block_seconds=config.recheck_freshness_block_seconds,
    )
    reason_codes = _row_reason_codes(
        ack_latency_status=ack_latency_status,
        missing_acknowledgement=observation.acknowledged_at is None,
        missing_acknowledgement_pressure_status=pressure_status,
        recheck_freshness_status=recheck_freshness_status,
        include_recheck_freshness=observation.acknowledged_at is not None,
    )
    return ResearchPacketSourceAckRecheckHealthRow(
        observation_id=observation.observation_id,
        packet_id=observation.packet_id,
        source_id=observation.source_id,
        source_family=observation.source_family,
        team_id=observation.team_id,
        category_id=observation.category_id,
        status=_status_from_dimension_statuses(
            (
                ack_latency_status,
                pressure_status,
                recheck_freshness_status,
            ),
        ),
        ack_latency_status=ack_latency_status,
        missing_acknowledgement_pressure_status=pressure_status,
        recheck_freshness_status=recheck_freshness_status,
        source_observed_at=observation.source_observed_at,
        acknowledged_at=observation.acknowledged_at,
        rechecked_at=observation.rechecked_at,
        source_age_seconds=source_age_seconds,
        ack_latency_seconds=ack_latency_seconds,
        missing_acknowledgement_age_seconds=missing_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        group_missing_acknowledgement_count=group_missing_count,
        group_observation_count=group_count,
        group_missing_acknowledgement_ratio=group_ratio,
        reason_codes=reason_codes,
    )


def _latest_recheck_anchor(
    observation: ResearchPacketSourceAckRecheckHealthObservation,
) -> datetime:
    if observation.rechecked_at is not None:
        return observation.rechecked_at
    if observation.acknowledged_at is not None:
        return observation.acknowledged_at
    return observation.source_observed_at


def _group_missing_acknowledgement_metrics(
    observations: tuple[ResearchPacketSourceAckRecheckHealthObservation, ...],
    *,
    config: ResearchPacketSourceAckRecheckHealthConfig,
) -> dict[tuple[str, str, str], tuple[Decimal, Decimal, Decimal, str]]:
    totals: dict[tuple[str, str, str], int] = {}
    missing: dict[tuple[str, str, str], int] = {}
    for observation in observations:
        key = (
            observation.team_id,
            observation.category_id,
            observation.source_family,
        )
        totals[key] = totals.get(key, 0) + 1
        if observation.acknowledged_at is None:
            missing[key] = missing.get(key, 0) + 1

    metrics: dict[tuple[str, str, str], tuple[Decimal, Decimal, Decimal, str]] = {}
    for key in sorted(totals):
        missing_count = _count(missing.get(key, 0))
        total_count = _count(totals[key])
        metrics[key] = (
            missing_count,
            total_count,
            _ratio(missing_count, total_count),
            _count_status(
                missing_count,
                watch_count=config.missing_acknowledgement_watch_count,
                block_count=config.missing_acknowledgement_block_count,
            ),
        )
    return metrics


def _summary_rows(
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckHealthSummaryRow, ...]:
    grouped: dict[tuple[str, str, str], list[ResearchPacketSourceAckRecheckHealthRow]] = {}
    for row in rows:
        key = (row.team_id, row.category_id, row.source_family)
        grouped.setdefault(key, []).append(row)
    return _sort_summary_rows(
        tuple(_summary_row(key, tuple(value)) for key, value in grouped.items()),
    )


def _summary_row(
    key: tuple[str, str, str],
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
) -> ResearchPacketSourceAckRecheckHealthSummaryRow:
    observation_count = _count(len(rows))
    missing_count = _count(sum(1 for row in rows if row.acknowledged_at is None))
    return ResearchPacketSourceAckRecheckHealthSummaryRow(
        team_id=key[0],
        category_id=key[1],
        source_family=key[2],
        status=_rollup_status(rows),
        observation_count=observation_count,
        missing_acknowledgement_count=missing_count,
        missing_acknowledgement_ratio=_ratio(missing_count, observation_count),
        max_ack_latency_seconds=_max_decimal(
            tuple(row.ack_latency_seconds for row in rows),
        ),
        max_recheck_age_seconds=_max_decimal(
            tuple(row.recheck_age_seconds for row in rows),
        ),
        reason_codes=_summary_reason_codes(rows),
    )


def _row_reason_codes(
    *,
    ack_latency_status: str,
    missing_acknowledgement: bool,
    missing_acknowledgement_pressure_status: str,
    recheck_freshness_status: str,
    include_recheck_freshness: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if ack_latency_status == "watch":
        reason_codes.append(LATENCY_WATCH_REASON_CODE)
    if ack_latency_status == "blocked":
        reason_codes.append(LATENCY_BLOCKED_REASON_CODE)
    if missing_acknowledgement:
        reason_codes.append(MISSING_ACK_REASON_CODE)
    if missing_acknowledgement_pressure_status == "watch":
        reason_codes.append(MISSING_PRESSURE_WATCH_REASON_CODE)
    if missing_acknowledgement_pressure_status == "blocked":
        reason_codes.append(MISSING_PRESSURE_BLOCKED_REASON_CODE)
    if include_recheck_freshness and recheck_freshness_status == "watch":
        reason_codes.append(FRESHNESS_WATCH_REASON_CODE)
    if include_recheck_freshness and recheck_freshness_status == "blocked":
        reason_codes.append(FRESHNESS_BLOCKED_REASON_CODE)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON_CODE)
    return tuple(reason_codes)


def _summary_reason_codes(
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
) -> tuple[str, ...]:
    reason_codes = tuple(
        reason_code
        for reason_code in TRIGGER_REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )
    if reason_codes:
        return reason_codes
    return (CLEAR_REASON_CODE,)


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return _summary_reason_codes(rows)


def _status_from_dimension_statuses(statuses: tuple[str, ...]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON_CODE,):
        return "pass"
    if any(
        reason_code
        in (
            LATENCY_BLOCKED_REASON_CODE,
            MISSING_PRESSURE_BLOCKED_REASON_CODE,
            FRESHNESS_BLOCKED_REASON_CODE,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    return "watch"


def _rollup_status(rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...]) -> str:
    if not rows:
        return "empty"
    return _rollup_status(rows)


def _seconds_status(
    value: Decimal,
    *,
    watch_seconds: Decimal,
    block_seconds: Decimal,
) -> str:
    _require_nonnegative_seconds_decimal("value", value)
    _require_positive_seconds_decimal("watch_seconds", watch_seconds)
    _require_positive_seconds_decimal("block_seconds", block_seconds)
    if value >= block_seconds:
        return "blocked"
    if value > watch_seconds:
        return "watch"
    return "pass"


def _count_status(
    value: Decimal,
    *,
    watch_count: Decimal,
    block_count: Decimal,
) -> str:
    _require_nonnegative_count_decimal("value", value)
    _require_positive_count_decimal("watch_count", watch_count)
    _require_positive_count_decimal("block_count", block_count)
    if value >= block_count:
        return "blocked"
    if value >= watch_count:
        return "watch"
    return "pass"


def _normalize_observations(
    observations: Iterable[ResearchPacketSourceAckRecheckHealthObservation],
) -> tuple[ResearchPacketSourceAckRecheckHealthObservation, ...]:
    if isinstance(observations, str | bytes):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchPacketSourceAckRecheckHealthObservation:
            raise ValueError("observations must contain exact health observations")
        require_paper_only_flags("health observation", observation)
        if observation.observation_id in seen:
            raise ValueError("observation_id values must be unique")
        seen.add(observation.observation_id)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.team_id,
                observation.category_id,
                observation.source_family,
                observation.source_observed_at,
                observation.observation_id,
            ),
        ),
    )


def _sort_health_rows(
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckHealthRow, ...]:
    return tuple(sorted(rows, key=_health_row_sort_key))


def _health_row_sort_key(
    row: ResearchPacketSourceAckRecheckHealthRow,
) -> tuple[int, int, int, int, int, str, str, str, datetime, str]:
    missing_rank = 0 if row.acknowledged_at is None else 1
    return (
        STATUS_RANK[row.status],
        STATUS_RANK[row.recheck_freshness_status],
        missing_rank,
        STATUS_RANK[row.ack_latency_status],
        STATUS_RANK[row.missing_acknowledgement_pressure_status],
        row.team_id,
        row.category_id,
        row.source_family,
        row.source_observed_at,
        row.observation_id,
    )


def _sort_summary_rows(
    rows: tuple[ResearchPacketSourceAckRecheckHealthSummaryRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckHealthSummaryRow, ...]:
    return tuple(sorted(rows, key=_summary_row_sort_key))


def _summary_row_sort_key(
    row: ResearchPacketSourceAckRecheckHealthSummaryRow,
) -> tuple[int, str, str, str]:
    return (
        STATUS_RANK[row.status],
        row.team_id,
        row.category_id,
        row.source_family,
    )


def _normalize_health_rows(
    value: Iterable[ResearchPacketSourceAckRecheckHealthRow],
) -> tuple[ResearchPacketSourceAckRecheckHealthRow, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckHealthRow:
            raise ValueError("rows must contain exact health rows")
        require_paper_only_flags("health row", row)
        if row.observation_id in seen:
            raise ValueError("row observation_id values must be unique")
        seen.add(row.observation_id)
    return _sort_health_rows(rows)


def _normalize_summary_rows(
    value: Iterable[ResearchPacketSourceAckRecheckHealthSummaryRow],
) -> tuple[ResearchPacketSourceAckRecheckHealthSummaryRow, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("summary_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("summary_rows must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckHealthSummaryRow:
            raise ValueError("summary_rows must contain exact health summary rows")
        require_paper_only_flags("health summary row", row)
        key = (row.team_id, row.category_id, row.source_family)
        if key in seen:
            raise ValueError("summary_rows must be unique by team, category, and family")
        seen.add(key)
    return _sort_summary_rows(rows)


def _validate_observation(
    observation: ResearchPacketSourceAckRecheckHealthObservation,
) -> None:
    if (
        observation.acknowledged_at is not None
        and observation.acknowledged_at < observation.source_observed_at
    ):
        raise ValueError("acknowledged_at must be >= source_observed_at")
    if observation.acknowledged_at is None and observation.rechecked_at is not None:
        raise ValueError("rechecked_at requires acknowledged_at")
    if (
        observation.rechecked_at is not None
        and observation.acknowledged_at is not None
        and observation.rechecked_at < observation.acknowledged_at
    ):
        raise ValueError("rechecked_at must be >= acknowledged_at")


def _validate_input_times(
    observations: tuple[ResearchPacketSourceAckRecheckHealthObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.source_observed_at > generated_at:
            raise ValueError("source_observed_at must be <= generated_at")
        if (
            observation.acknowledged_at is not None
            and observation.acknowledged_at > generated_at
        ):
            raise ValueError("acknowledged_at must be <= generated_at")
        if observation.rechecked_at is not None and observation.rechecked_at > generated_at:
            raise ValueError("rechecked_at must be <= generated_at")


def _validate_health_row(row: ResearchPacketSourceAckRecheckHealthRow) -> None:
    if row.acknowledged_at is None:
        if row.missing_acknowledgement_age_seconds != row.source_age_seconds:
            raise ValueError("missing rows must use source age as missing age")
    else:
        if row.acknowledged_at < row.source_observed_at:
            raise ValueError("acknowledged_at must be >= source_observed_at")
        if row.missing_acknowledgement_age_seconds != ZERO_SECONDS:
            raise ValueError("acknowledged rows require zero missing age")
    if row.rechecked_at is not None:
        if row.acknowledged_at is None:
            raise ValueError("rechecked_at requires acknowledged_at")
        if row.rechecked_at < row.acknowledged_at:
            raise ValueError("rechecked_at must be >= acknowledged_at")
    if row.ack_latency_seconds > row.source_age_seconds:
        raise ValueError("ack_latency_seconds must be <= source_age_seconds")
    if row.recheck_age_seconds > row.source_age_seconds:
        raise ValueError("recheck_age_seconds must be <= source_age_seconds")
    if row.group_missing_acknowledgement_count > row.group_observation_count:
        raise ValueError("group missing count must not exceed group count")
    if row.group_missing_acknowledgement_ratio != _ratio(
        row.group_missing_acknowledgement_count,
        row.group_observation_count,
    ):
        raise ValueError("group missing ratio must match group counts")
    expected_status = _status_from_dimension_statuses(
        (
            row.ack_latency_status,
            row.missing_acknowledgement_pressure_status,
            row.recheck_freshness_status,
        ),
    )
    if row.status != expected_status:
        raise ValueError("status must match dimension statuses")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_summary_row(
    row: ResearchPacketSourceAckRecheckHealthSummaryRow,
) -> None:
    if row.missing_acknowledgement_count > row.observation_count:
        raise ValueError("missing_acknowledgement_count must not exceed observation_count")
    if row.missing_acknowledgement_ratio != _ratio(
        row.missing_acknowledgement_count,
        row.observation_count,
    ):
        raise ValueError("missing_acknowledgement_ratio must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchPacketSourceAckRecheckHealthReport) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.summary_row_count != _count(len(report.summary_rows)):
        raise ValueError("summary_row_count must match summary_rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.missing_acknowledgement_count != _count(
        sum(1 for row in report.rows if row.acknowledged_at is None),
    ):
        raise ValueError("missing_acknowledgement_count must match rows")
    if report.ack_latency_watch_count != _dimension_status_count(
        report.rows,
        "ack_latency_status",
        "watch",
    ):
        raise ValueError("ack_latency_watch_count must match rows")
    if report.ack_latency_blocked_count != _dimension_status_count(
        report.rows,
        "ack_latency_status",
        "blocked",
    ):
        raise ValueError("ack_latency_blocked_count must match rows")
    if report.missing_acknowledgement_pressure_count != _count(
        sum(
            1
            for row in report.rows
            if row.missing_acknowledgement_pressure_status != "pass"
        ),
    ):
        raise ValueError("missing_acknowledgement_pressure_count must match rows")
    if report.recheck_freshness_watch_count != _dimension_status_count(
        report.rows,
        "recheck_freshness_status",
        "watch",
    ):
        raise ValueError("recheck_freshness_watch_count must match rows")
    if report.recheck_freshness_blocked_count != _dimension_status_count(
        report.rows,
        "recheck_freshness_status",
        "blocked",
    ):
        raise ValueError("recheck_freshness_blocked_count must match rows")
    if report.issue_ratio != _ratio(
        _count(sum(1 for row in report.rows if row.status != "pass")),
        report.observation_count,
    ):
        raise ValueError("issue_ratio must match rows")
    if report.max_ack_latency_seconds != _max_decimal(
        tuple(row.ack_latency_seconds for row in report.rows),
    ):
        raise ValueError("max_ack_latency_seconds must match rows")
    if report.max_missing_acknowledgement_age_seconds != _max_decimal(
        tuple(row.missing_acknowledgement_age_seconds for row in report.rows),
    ):
        raise ValueError("max_missing_acknowledgement_age_seconds must match rows")
    if report.max_recheck_age_seconds != _max_decimal(
        tuple(row.recheck_age_seconds for row in report.rows),
    ):
        raise ValueError("max_recheck_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.summary_rows != _summary_rows(report.rows):
        raise ValueError("summary_rows must match rows")


def _status_count(
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _dimension_status_count(
    rows: tuple[ResearchPacketSourceAckRecheckHealthRow, ...],
    field_name: str,
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name) == status))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SECONDS
    return max(values).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    _require_nonnegative_count_decimal("numerator", numerator)
    _require_nonnegative_count_decimal("denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        if seconds < ZERO_SECONDS:
            raise ValueError("duration seconds must be nonnegative")
        return seconds.quantize(SECONDS_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public string")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {allowed_values}")


def _require_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_seconds_decimal(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(SECONDS_QUANTUM)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _require_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between zero and one")
    return value.quantize(RATIO_QUANTUM)


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


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_HEALTH_CONFIG_VERSION",
    "ResearchPacketSourceAckRecheckHealthConfig",
    "ResearchPacketSourceAckRecheckHealthObservation",
    "ResearchPacketSourceAckRecheckHealthReport",
    "ResearchPacketSourceAckRecheckHealthRow",
    "ResearchPacketSourceAckRecheckHealthSummaryRow",
    "build_research_packet_source_ack_recheck_health_report",
    "research_packet_source_ack_recheck_health_report_to_payload",
)
