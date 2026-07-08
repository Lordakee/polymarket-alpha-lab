"""Pure aggregate report for sports injury signal freshness research."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION = (
    "research-sports-injury-signal-freshness-report-v0"
)
RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_SCOPE = (
    "aggregate sports injury news signal freshness report only"
)

SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

STATUSES = ("pass", "watch", "block")
STATUS_RANKS = {"block": 0, "watch": 1, "pass": 2}

STALE_SOURCE_WATCH_REASON = "sports_injury_signal_freshness_stale_source_watch"
STALE_SOURCE_BLOCK_REASON = "sports_injury_signal_freshness_stale_source_block"
CONTRADICTION_WATCH_REASON = "sports_injury_signal_freshness_contradiction_watch"
CONTRADICTION_BLOCK_REASON = "sports_injury_signal_freshness_contradiction_block"
RECHECK_WATCH_REASON = "sports_injury_signal_freshness_recheck_watch"
RECHECK_BLOCK_REASON = "sports_injury_signal_freshness_recheck_block"
SIGNAL_AGE_WATCH_REASON = "sports_injury_signal_freshness_signal_age_watch"
PASS_REASON = "sports_injury_signal_freshness_pass"
NO_LANES_REASON = "sports_injury_signal_freshness_no_lanes"
NO_SIGNALS_REASON = "sports_injury_signal_freshness_no_signals"

REASON_CODES = (
    STALE_SOURCE_WATCH_REASON,
    STALE_SOURCE_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    RECHECK_WATCH_REASON,
    RECHECK_BLOCK_REASON,
    SIGNAL_AGE_WATCH_REASON,
    PASS_REASON,
    NO_SIGNALS_REASON,
    NO_LANES_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
AGGREGATE_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("or", "der"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "-", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("api", "key"),
        _join_parts("ke", "y="),
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION",
    "RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_SCOPE",
    "ResearchSportsInjurySignalFreshnessConfig",
    "ResearchSportsInjurySignalFreshnessLane",
    "ResearchSportsInjurySignalFreshnessReasonCodeCount",
    "ResearchSportsInjurySignalFreshnessReport",
    "ResearchSportsInjurySignalFreshnessRow",
    "build_research_sports_injury_signal_freshness_report",
    "research_sports_injury_signal_freshness_report_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchSportsInjurySignalFreshnessConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("1800.000000")
    stale_source_watch_pressure: Decimal = Decimal("0.250000")
    stale_source_block_pressure: Decimal = Decimal("0.600000")
    contradiction_watch_pressure: Decimal = Decimal("0.200000")
    contradiction_block_pressure: Decimal = Decimal("0.500000")
    recheck_watch_urgency: Decimal = Decimal("0.300000")
    recheck_block_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsInjurySignalFreshnessConfig:
            raise ValueError(
                "config must be exactly ResearchSportsInjurySignalFreshnessConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_nonnegative_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        if self.max_signal_age_seconds <= ZERO:
            raise ValueError("max_signal_age_seconds must be positive")
        for field_name in (
            "stale_source_watch_pressure",
            "stale_source_block_pressure",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "recheck_watch_urgency",
            "recheck_block_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_watch_pressure >= self.stale_source_block_pressure:
            raise ValueError(
                "stale_source_watch_pressure must be below stale_source_block_pressure",
            )
        if self.contradiction_watch_pressure >= self.contradiction_block_pressure:
            raise ValueError(
                "contradiction_watch_pressure must be below contradiction_block_pressure",
            )
        if self.recheck_watch_urgency >= self.recheck_block_urgency:
            raise ValueError("recheck_watch_urgency must be below recheck_block_urgency")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSportsInjurySignalFreshnessLane(_NoSubclass):
    lane_id: str
    sport_lane: str
    aggregate_label: str
    latest_signal_observed_at: datetime
    signal_count: Decimal
    stale_source_count: Decimal
    contradiction_count: Decimal
    recheck_due_count: Decimal
    lane_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsInjurySignalFreshnessLane:
            raise ValueError(
                "lane must be exactly ResearchSportsInjurySignalFreshnessLane",
            )
        _require_public_identifier("lane_id", self.lane_id)
        _require_public_identifier("sport_lane", self.sport_lane)
        _require_aggregate_label(
            "aggregate_label",
            self.aggregate_label,
            sport_lane=self.sport_lane,
        )
        object.__setattr__(
            self,
            "latest_signal_observed_at",
            _as_utc("latest_signal_observed_at", self.latest_signal_observed_at),
        )
        for field_name in (
            "signal_count",
            "stale_source_count",
            "contradiction_count",
            "recheck_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_count > self.signal_count:
            raise ValueError("stale_source_count must not exceed signal_count")
        if self.contradiction_count > self.signal_count:
            raise ValueError("contradiction_count must not exceed signal_count")
        if self.recheck_due_count > self.signal_count:
            raise ValueError("recheck_due_count must not exceed signal_count")
        _require_canonical_string("lane_config_version", self.lane_config_version)
        _require_hard_flags("lane", self)


@dataclass(frozen=True)
class ResearchSportsInjurySignalFreshnessReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    lane_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsInjurySignalFreshnessReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSportsInjurySignalFreshnessReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "lane_ratio",
            _require_ratio_decimal("lane_ratio", self.lane_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSportsInjurySignalFreshnessRow(_NoSubclass):
    lane_id: str
    sport_lane: str
    aggregate_label: str
    latest_signal_observed_at: datetime
    signal_age_seconds: Decimal
    signal_count: Decimal
    stale_source_count: Decimal
    contradiction_count: Decimal
    recheck_due_count: Decimal
    stale_source_pressure: Decimal
    contradiction_pressure: Decimal
    recheck_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsInjurySignalFreshnessRow:
            raise ValueError("row must be exactly ResearchSportsInjurySignalFreshnessRow")
        _require_public_identifier("lane_id", self.lane_id)
        _require_public_identifier("sport_lane", self.sport_lane)
        _require_aggregate_label(
            "aggregate_label",
            self.aggregate_label,
            sport_lane=self.sport_lane,
        )
        object.__setattr__(
            self,
            "latest_signal_observed_at",
            _as_utc("latest_signal_observed_at", self.latest_signal_observed_at),
        )
        for field_name in (
            "signal_age_seconds",
            "signal_count",
            "stale_source_count",
            "contradiction_count",
            "recheck_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_pressure",
            "contradiction_pressure",
            "recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSportsInjurySignalFreshnessReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    research_scope: str
    status: str
    lane_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_source_pressure_lane_count: Decimal
    contradiction_pressure_lane_count: Decimal
    recheck_urgency_lane_count: Decimal
    max_signal_age_seconds: Decimal
    stale_source_watch_pressure: Decimal
    stale_source_block_pressure: Decimal
    contradiction_watch_pressure: Decimal
    contradiction_block_pressure: Decimal
    recheck_watch_urgency: Decimal
    recheck_block_urgency: Decimal
    recheck_urgency: Decimal
    max_signal_age_seconds_observed: Decimal
    average_stale_source_pressure: Decimal
    average_contradiction_pressure: Decimal
    rows: tuple[ResearchSportsInjurySignalFreshnessRow, ...]
    lane_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[ResearchSportsInjurySignalFreshnessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsInjurySignalFreshnessReport:
            raise ValueError(
                "report must be exactly ResearchSportsInjurySignalFreshnessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_SCOPE:
            raise ValueError("research_scope must match sports injury signal scope")
        _require_status("status", self.status)
        for field_name in (
            "lane_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_source_pressure_lane_count",
            "contradiction_pressure_lane_count",
            "recheck_urgency_lane_count",
            "max_signal_age_seconds",
            "max_signal_age_seconds_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_watch_pressure",
            "stale_source_block_pressure",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "recheck_watch_urgency",
            "recheck_block_urgency",
            "recheck_urgency",
            "average_stale_source_pressure",
            "average_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "lane_config_versions",
            _normalize_lane_config_versions(self.lane_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            _validate_report_derived_validation_digest(self)
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _validate_report_consistency(self)


def build_research_sports_injury_signal_freshness_report(
    lanes: Iterable[ResearchSportsInjurySignalFreshnessLane],
    *,
    config: ResearchSportsInjurySignalFreshnessConfig,
    generated_at: datetime,
) -> ResearchSportsInjurySignalFreshnessReport:
    if type(config) is not ResearchSportsInjurySignalFreshnessConfig:
        raise ValueError(
            "config must be exactly ResearchSportsInjurySignalFreshnessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_lanes = _normalize_lanes(lanes)
    rows = _rows_from_lanes(normalized_lanes, config=config, generated_at=generated_at_utc)
    lane_count = _decimal_count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchSportsInjurySignalFreshnessReasonCodeCount(
                reason_code=NO_LANES_REASON,
                count=ONE,
                lane_ratio=ZERO,
            ),
        )
        reason_codes = (NO_LANES_REASON,)

    return ResearchSportsInjurySignalFreshnessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_SCOPE,
        status=_report_status(rows),
        lane_count=lane_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        stale_source_pressure_lane_count=_threshold_count(
            rows,
            "stale_source_pressure",
            config.stale_source_watch_pressure,
        ),
        contradiction_pressure_lane_count=_threshold_count(
            rows,
            "contradiction_pressure",
            config.contradiction_watch_pressure,
        ),
        recheck_urgency_lane_count=_threshold_count(
            rows,
            "recheck_urgency",
            config.recheck_watch_urgency,
        ),
        max_signal_age_seconds=_six(config.max_signal_age_seconds),
        stale_source_watch_pressure=_six(config.stale_source_watch_pressure),
        stale_source_block_pressure=_six(config.stale_source_block_pressure),
        contradiction_watch_pressure=_six(config.contradiction_watch_pressure),
        contradiction_block_pressure=_six(config.contradiction_block_pressure),
        recheck_watch_urgency=_six(config.recheck_watch_urgency),
        recheck_block_urgency=_six(config.recheck_block_urgency),
        recheck_urgency=_max_decimal(row.recheck_urgency for row in rows),
        max_signal_age_seconds_observed=_max_decimal(
            row.signal_age_seconds for row in rows
        ),
        average_stale_source_pressure=_average_decimal(
            tuple(row.stale_source_pressure for row in rows),
        ),
        average_contradiction_pressure=_average_decimal(
            tuple(row.contradiction_pressure for row in rows),
        ),
        rows=rows,
        lane_config_versions=tuple(
            sorted((lane.lane_id, lane.lane_config_version) for lane in normalized_lanes),
        ),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_sports_injury_signal_freshness_report_payload(
    report: ResearchSportsInjurySignalFreshnessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSportsInjurySignalFreshnessReport:
        raise ValueError(
            "report must be a ResearchSportsInjurySignalFreshnessReport",
        )
    _require_hard_flags("report", report)
    _validate_report_derived_validation_digest(report)
    payload = _report_payload_values(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _rows_from_lanes(
    lanes: tuple[ResearchSportsInjurySignalFreshnessLane, ...],
    *,
    config: ResearchSportsInjurySignalFreshnessConfig,
    generated_at: datetime,
) -> tuple[ResearchSportsInjurySignalFreshnessRow, ...]:
    rows = tuple(_row_from_lane(lane, config=config, generated_at=generated_at) for lane in lanes)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANKS[row.status],
                -row.recheck_urgency,
                row.lane_id,
            ),
        ),
    )


def _row_from_lane(
    lane: ResearchSportsInjurySignalFreshnessLane,
    *,
    config: ResearchSportsInjurySignalFreshnessConfig,
    generated_at: datetime,
) -> ResearchSportsInjurySignalFreshnessRow:
    if lane.latest_signal_observed_at > generated_at:
        raise ValueError("latest_signal_observed_at must not be future dated")
    signal_age_seconds = _datetime_delta_seconds(generated_at, lane.latest_signal_observed_at)
    stale_source_pressure = _safe_ratio(lane.stale_source_count, lane.signal_count)
    contradiction_pressure = _safe_ratio(lane.contradiction_count, lane.signal_count)
    recheck_urgency = _safe_ratio(lane.recheck_due_count, lane.signal_count)
    reason_codes = _row_reason_codes(
        signal_count=lane.signal_count,
        signal_age_seconds=signal_age_seconds,
        stale_source_pressure=stale_source_pressure,
        contradiction_pressure=contradiction_pressure,
        recheck_urgency=recheck_urgency,
        config=config,
    )
    return ResearchSportsInjurySignalFreshnessRow(
        lane_id=lane.lane_id,
        sport_lane=lane.sport_lane,
        aggregate_label=lane.aggregate_label,
        latest_signal_observed_at=lane.latest_signal_observed_at,
        signal_age_seconds=signal_age_seconds,
        signal_count=lane.signal_count,
        stale_source_count=lane.stale_source_count,
        contradiction_count=lane.contradiction_count,
        recheck_due_count=lane.recheck_due_count,
        stale_source_pressure=stale_source_pressure,
        contradiction_pressure=contradiction_pressure,
        recheck_urgency=recheck_urgency,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_count: Decimal,
    signal_age_seconds: Decimal,
    stale_source_pressure: Decimal,
    contradiction_pressure: Decimal,
    recheck_urgency: Decimal,
    config: ResearchSportsInjurySignalFreshnessConfig,
) -> tuple[str, ...]:
    if signal_count == ZERO:
        return (NO_SIGNALS_REASON,)

    reason_codes: list[str] = []
    if stale_source_pressure >= config.stale_source_block_pressure:
        reason_codes.append(STALE_SOURCE_BLOCK_REASON)
    elif stale_source_pressure >= config.stale_source_watch_pressure:
        reason_codes.append(STALE_SOURCE_WATCH_REASON)

    if contradiction_pressure >= config.contradiction_block_pressure:
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_pressure >= config.contradiction_watch_pressure:
        reason_codes.append(CONTRADICTION_WATCH_REASON)

    if recheck_urgency >= config.recheck_block_urgency:
        reason_codes.append(RECHECK_BLOCK_REASON)
    elif recheck_urgency >= config.recheck_watch_urgency:
        reason_codes.append(RECHECK_WATCH_REASON)

    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(SIGNAL_AGE_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") or reason_code == NO_SIGNALS_REASON for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSportsInjurySignalFreshnessRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSportsInjurySignalFreshnessRow, ...],
) -> tuple[ResearchSportsInjurySignalFreshnessReasonCodeCount, ...]:
    lane_count = _decimal_count(len(rows))
    counts: list[ResearchSportsInjurySignalFreshnessReasonCodeCount] = []
    for reason_code in REASON_CODES:
        count = _decimal_count(
            sum(1 for row in rows if reason_code in row.reason_codes),
        )
        if count == ZERO:
            continue
        counts.append(
            ResearchSportsInjurySignalFreshnessReasonCodeCount(
                reason_code=reason_code,
                count=count,
                lane_ratio=_safe_ratio(count, lane_count),
            ),
        )
    return tuple(counts)


def _status_count(
    rows: tuple[ResearchSportsInjurySignalFreshnessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _threshold_count(
    rows: tuple[ResearchSportsInjurySignalFreshnessRow, ...],
    field_name: str,
    threshold: Decimal,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) >= threshold))


def _validate_row_consistency(row: ResearchSportsInjurySignalFreshnessRow) -> None:
    if row.stale_source_count > row.signal_count:
        raise ValueError("stale_source_count must not exceed signal_count")
    if row.contradiction_count > row.signal_count:
        raise ValueError("contradiction_count must not exceed signal_count")
    if row.recheck_due_count > row.signal_count:
        raise ValueError("recheck_due_count must not exceed signal_count")
    if row.stale_source_pressure != _safe_ratio(row.stale_source_count, row.signal_count):
        raise ValueError("stale_source_pressure must match lane counts")
    if row.contradiction_pressure != _safe_ratio(row.contradiction_count, row.signal_count):
        raise ValueError("contradiction_pressure must match lane counts")
    if row.recheck_urgency != _safe_ratio(row.recheck_due_count, row.signal_count):
        raise ValueError("recheck_urgency must match lane counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchSportsInjurySignalFreshnessReport) -> None:
    if report.lane_count != _decimal_count(len(report.rows)):
        raise ValueError("lane_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.recheck_urgency != _max_decimal(row.recheck_urgency for row in report.rows):
        raise ValueError("recheck_urgency must match rows")
    if report.max_signal_age_seconds_observed != _max_decimal(
        row.signal_age_seconds for row in report.rows
    ):
        raise ValueError("max_signal_age_seconds_observed must match rows")
    if report.average_stale_source_pressure != _average_decimal(
        tuple(row.stale_source_pressure for row in report.rows),
    ):
        raise ValueError("average_stale_source_pressure must match rows")
    if report.average_contradiction_pressure != _average_decimal(
        tuple(row.contradiction_pressure for row in report.rows),
    ):
        raise ValueError("average_contradiction_pressure must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_lanes(
    lanes: Iterable[ResearchSportsInjurySignalFreshnessLane],
) -> tuple[ResearchSportsInjurySignalFreshnessLane, ...]:
    if isinstance(lanes, (str, bytes)) or not isinstance(lanes, Iterable):
        raise ValueError("lanes must be an iterable")
    normalized: list[ResearchSportsInjurySignalFreshnessLane] = []
    lane_ids: set[str] = set()
    aggregate_labels: set[str] = set()
    for lane in lanes:
        if type(lane) is not ResearchSportsInjurySignalFreshnessLane:
            raise ValueError("lanes must contain ResearchSportsInjurySignalFreshnessLane")
        if lane.lane_id in lane_ids:
            raise ValueError("lane_id values must be unique")
        if lane.aggregate_label in aggregate_labels:
            raise ValueError("aggregate_label values must be unique")
        lane_ids.add(lane.lane_id)
        aggregate_labels.add(lane.aggregate_label)
        normalized.append(lane)
    return tuple(sorted(normalized, key=lambda lane: lane.lane_id))


def _normalize_rows(
    rows: tuple[ResearchSportsInjurySignalFreshnessRow, ...],
) -> tuple[ResearchSportsInjurySignalFreshnessRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSportsInjurySignalFreshnessRow:
            raise ValueError("rows must contain ResearchSportsInjurySignalFreshnessRow")
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANKS[row.status],
                -row.recheck_urgency,
                row.lane_id,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must use deterministic sort")
    return rows


def _normalize_lane_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if not isinstance(values, tuple):
        raise ValueError("lane_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("lane_config_versions entries must be pairs")
        lane_id, lane_config_version = item
        _require_public_identifier("lane_id", lane_id)
        _require_canonical_string("lane_config_version", lane_config_version)
        normalized.append((lane_id, lane_config_version))
    sorted_values = tuple(sorted(normalized))
    if values != sorted_values:
        raise ValueError("lane_config_versions must use deterministic sort")
    return values


def _normalize_reason_code_counts(
    counts: tuple[ResearchSportsInjurySignalFreshnessReasonCodeCount, ...],
) -> tuple[ResearchSportsInjurySignalFreshnessReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSportsInjurySignalFreshnessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSportsInjurySignalFreshnessReasonCodeCount",
            )
    sorted_counts = tuple(
        sorted(counts, key=lambda item: REASON_CODES.index(item.reason_code)),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must use deterministic sort")
    return counts


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if len(value) > 128:
        raise ValueError(f"{field_name} must not exceed 128 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_aggregate_label(field_name: str, value: object, *, sport_lane: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not AGGREGATE_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an aggregate-safe label")
    expected_prefix = f"{sport_lane}-injury-news"
    if value != expected_prefix and not value.startswith(expected_prefix + "-"):
        raise ValueError(f"{field_name} must be an aggregate-safe label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _six(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _six(numerator / denominator)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _six(sum(values, ZERO) / _decimal_count(len(values)))


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        (Decimal(delta.days) * SECONDS_PER_DAY)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _six(seconds)


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _report_derived_validation_digest(
    report: ResearchSportsInjurySignalFreshnessReport,
) -> str:
    payload = _report_payload_values(report)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_report_derived_validation_digest(
    report: ResearchSportsInjurySignalFreshnessReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_payload_values(
    report: ResearchSportsInjurySignalFreshnessReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(_six(value))
    if type(value) is datetime:
        return _format_utc(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _format_utc(value: datetime) -> str:
    return _as_utc("payload datetime", value).isoformat().replace("+00:00", "Z")
