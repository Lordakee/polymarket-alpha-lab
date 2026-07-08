"""Pure report-only reducer for research team memory retention health."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_RESEARCH_TEAM_MEMORY_RETENTION_HEALTH_REPORT_CONFIG_VERSION = (
    "research-team-memory-retention-health-report-v0"
)

OBSERVED_REASON = "research_team_memory_retention_health_observed"
NO_MEMORY_REASON = "research_team_memory_retention_health_no_team_memory"
SNAPSHOT_STALE_REASON = "research_team_memory_retention_health_snapshot_stale"
LOW_FRESHNESS_REASON = "research_team_memory_retention_health_low_freshness"
LOW_REUSE_REASON = "research_team_memory_retention_health_low_reuse"
MISSING_CALIBRATION_REASON = (
    "research_team_memory_retention_health_missing_calibration_feedback"
)
COVERAGE_GAP_REASON = "research_team_memory_retention_health_coverage_gap"
BACKLOG_PRESSURE_REASON = (
    "research_team_memory_retention_health_review_backlog_pressure"
)
PASS_REASON = "research_team_memory_retention_health_passed"

SNAPSHOT_REASON_CODES = (OBSERVED_REASON,)
REASON_CODES = (
    NO_MEMORY_REASON,
    SNAPSHOT_STALE_REASON,
    LOW_FRESHNESS_REASON,
    LOW_REUSE_REASON,
    MISSING_CALIBRATION_REASON,
    COVERAGE_GAP_REASON,
    BACKLOG_PRESSURE_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (NO_MEMORY_REASON, SNAPSHOT_STALE_REASON)
WATCH_REASONS = (
    LOW_FRESHNESS_REASON,
    LOW_REUSE_REASON,
    MISSING_CALIBRATION_REASON,
    COVERAGE_GAP_REASON,
    BACKLOG_PRESSURE_REASON,
)
STATUSES = ("pass", "watch", "block")
NEXT_REVIEW_STEPS = {
    "pass": "reuse_memory_for_specialist_research",
    "watch": "review_memory_retention_before_reuse",
    "block": "block_memory_reuse_until_retention_review",
}

DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
HEALTH_COMPONENT_COUNT = Decimal("5.000000")

UNSAFE_PUBLIC_FRAGMENTS = (
    "li" + "ve",
    "wall" + "et",
    "ord" + "er",
    "au" + "th",
    "priv" + "ate" + "_" + "key",
    "acc" + "ount",
    "sig" + "ning",
    "sec" + "ret",
    "net" + "work",
    "tra" + "de_exe" + "cution",
    "source_id",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_RETENTION_HEALTH_REPORT_CONFIG_VERSION",
    "ResearchTeamMemoryRetentionHealthConfig",
    "ResearchTeamMemoryRetentionHealthReasonCodeCount",
    "ResearchTeamMemoryRetentionHealthReport",
    "ResearchTeamMemoryRetentionHealthRow",
    "ResearchTeamMemoryRetentionHealthSnapshot",
    "build_research_team_memory_retention_health_report",
    "research_team_memory_retention_health_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamMemoryRetentionHealthConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_MEMORY_RETENTION_HEALTH_REPORT_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("604800.000000")
    min_memory_freshness_ratio: Decimal = Decimal("0.600000")
    min_memory_reuse_ratio: Decimal = Decimal("0.200000")
    min_calibration_feedback_ratio: Decimal = Decimal("0.200000")
    max_coverage_gap_ratio: Decimal = Decimal("0.150000")
    max_review_backlog_pressure: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_snapshot_age_seconds",
            _normalize_positive_decimal(
                "max_snapshot_age_seconds",
                self.max_snapshot_age_seconds,
            ),
        )
        for field_name in (
            "min_memory_freshness_ratio",
            "min_memory_reuse_ratio",
            "min_calibration_feedback_ratio",
            "max_coverage_gap_ratio",
            "max_review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("research team memory retention health config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetentionHealthSnapshot:
    team_id: str
    category_id: str
    observed_at: datetime
    memory_item_count: Decimal
    fresh_memory_item_count: Decimal
    reused_memory_item_count: Decimal
    calibration_feedback_count: Decimal
    coverage_gap_count: Decimal
    open_review_backlog_count: Decimal
    high_priority_review_backlog_count: Decimal
    reason_codes: tuple[str, ...] = (OBSERVED_REASON,)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "memory_item_count",
            "fresh_memory_item_count",
            "reused_memory_item_count",
            "calibration_feedback_count",
            "coverage_gap_count",
            "open_review_backlog_count",
            "high_priority_review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, SNAPSHOT_REASON_CODES),
        )
        _validate_snapshot(self)
        require_paper_only_flags("research team memory retention health snapshot", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetentionHealthRow:
    team_id: str
    category_id: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    memory_item_count: Decimal
    fresh_memory_item_count: Decimal
    reused_memory_item_count: Decimal
    calibration_feedback_count: Decimal
    coverage_gap_count: Decimal
    open_review_backlog_count: Decimal
    high_priority_review_backlog_count: Decimal
    memory_freshness_ratio: Decimal
    memory_reuse_ratio: Decimal
    calibration_feedback_ratio: Decimal
    coverage_gap_ratio: Decimal
    review_backlog_pressure: Decimal
    retention_health_score: Decimal
    health_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "memory_item_count",
            "fresh_memory_item_count",
            "reused_memory_item_count",
            "calibration_feedback_count",
            "coverage_gap_count",
            "open_review_backlog_count",
            "high_priority_review_backlog_count",
            "retention_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_freshness_ratio",
            "memory_reuse_ratio",
            "calibration_feedback_ratio",
            "coverage_gap_ratio",
            "review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("health_status", self.health_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("research team memory retention health row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetentionHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        require_paper_only_flags(
            "research team memory retention health reason count",
            self,
        )


@dataclass(frozen=True)
class ResearchTeamMemoryRetentionHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    snapshot_count: Decimal
    team_category_count: Decimal
    memory_item_count: Decimal
    fresh_memory_item_count: Decimal
    reused_memory_item_count: Decimal
    calibration_feedback_count: Decimal
    coverage_gap_count: Decimal
    open_review_backlog_count: Decimal
    high_priority_review_backlog_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_freshness_ratio: Decimal
    memory_reuse_ratio: Decimal
    calibration_feedback_ratio: Decimal
    coverage_gap_ratio: Decimal
    review_backlog_pressure: Decimal
    retention_health_score: Decimal
    rows: tuple[ResearchTeamMemoryRetentionHealthRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryRetentionHealthReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_canonical_string("next_review_step", self.next_review_step)
        for field_name in (
            "snapshot_count",
            "team_category_count",
            "memory_item_count",
            "fresh_memory_item_count",
            "reused_memory_item_count",
            "calibration_feedback_count",
            "coverage_gap_count",
            "open_review_backlog_count",
            "high_priority_review_backlog_count",
            "pass_count",
            "watch_count",
            "block_count",
            "retention_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_freshness_ratio",
            "memory_reuse_ratio",
            "calibration_feedback_ratio",
            "coverage_gap_ratio",
            "review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODES),
        )
        _validate_report(self)
        require_paper_only_flags("research team memory retention health report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_team_memory_retention_health_report(
    snapshots: list[ResearchTeamMemoryRetentionHealthSnapshot]
    | tuple[ResearchTeamMemoryRetentionHealthSnapshot, ...],
    *,
    config: ResearchTeamMemoryRetentionHealthConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryRetentionHealthReport:
    if type(config) is not ResearchTeamMemoryRetentionHealthConfig:
        raise ValueError("config must be a ResearchTeamMemoryRetentionHealthConfig")
    require_paper_only_flags("research team memory retention health config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots, generated_at=generated_at_utc)
    rows = tuple(
        _row_from_snapshot(snapshot, config=config, generated_at=generated_at_utc)
        for snapshot in normalized_snapshots
    )
    reason_codes = _report_reason_codes(rows)
    status = _status_for_reason_codes(reason_codes)

    return ResearchTeamMemoryRetentionHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        snapshot_count=_decimal_count(len(normalized_snapshots)),
        team_category_count=_decimal_count(len(rows)),
        memory_item_count=sum((row.memory_item_count for row in rows), ZERO),
        fresh_memory_item_count=sum((row.fresh_memory_item_count for row in rows), ZERO),
        reused_memory_item_count=sum((row.reused_memory_item_count for row in rows), ZERO),
        calibration_feedback_count=sum(
            (row.calibration_feedback_count for row in rows),
            ZERO,
        ),
        coverage_gap_count=sum((row.coverage_gap_count for row in rows), ZERO),
        open_review_backlog_count=sum(
            (row.open_review_backlog_count for row in rows),
            ZERO,
        ),
        high_priority_review_backlog_count=sum(
            (row.high_priority_review_backlog_count for row in rows),
            ZERO,
        ),
        pass_count=_decimal_count(sum(1 for row in rows if row.health_status == "pass")),
        watch_count=_decimal_count(sum(1 for row in rows if row.health_status == "watch")),
        block_count=_decimal_count(sum(1 for row in rows if row.health_status == "block")),
        memory_freshness_ratio=_aggregate_ratio(rows, "fresh_memory_item_count"),
        memory_reuse_ratio=_aggregate_ratio(rows, "reused_memory_item_count"),
        calibration_feedback_ratio=_aggregate_ratio(rows, "calibration_feedback_count"),
        coverage_gap_ratio=_aggregate_ratio(rows, "coverage_gap_count"),
        review_backlog_pressure=_aggregate_ratio(rows, "open_review_backlog_count"),
        retention_health_score=_aggregate_health_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_memory_retention_health_report_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchTeamMemoryRetentionHealthConfig,
            ResearchTeamMemoryRetentionHealthSnapshot,
            ResearchTeamMemoryRetentionHealthRow,
            ResearchTeamMemoryRetentionHealthReasonCodeCount,
            ResearchTeamMemoryRetentionHealthReport,
        ),
    ):
        require_paper_only_flags("research team memory retention health payload", value)
    elif type(value) is not dict:
        raise ValueError(
            "value must be a research team memory retention health dataclass "
            "or JSON object",
        )
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("research team memory retention health payload must be an object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    return payload


def _normalize_snapshots(
    snapshots: list[ResearchTeamMemoryRetentionHealthSnapshot]
    | tuple[ResearchTeamMemoryRetentionHealthSnapshot, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamMemoryRetentionHealthSnapshot, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    normalized_snapshots = tuple(snapshots)
    seen_keys: set[tuple[str, str]] = set()
    for snapshot in normalized_snapshots:
        if type(snapshot) is not ResearchTeamMemoryRetentionHealthSnapshot:
            raise ValueError(
                "snapshots must contain ResearchTeamMemoryRetentionHealthSnapshot",
            )
        require_paper_only_flags("research team memory retention health snapshot", snapshot)
        key = (snapshot.team_id, snapshot.category_id)
        if key in seen_keys:
            raise ValueError("team/category values must be unique")
        seen_keys.add(key)
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(
        sorted(
            normalized_snapshots,
            key=lambda snapshot: (snapshot.team_id, snapshot.category_id),
        )
    )


def _row_from_snapshot(
    snapshot: ResearchTeamMemoryRetentionHealthSnapshot,
    *,
    config: ResearchTeamMemoryRetentionHealthConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryRetentionHealthRow:
    memory_count = snapshot.memory_item_count
    freshness_ratio = _safe_ratio(snapshot.fresh_memory_item_count, memory_count)
    reuse_ratio = _safe_ratio(snapshot.reused_memory_item_count, memory_count)
    feedback_ratio = _safe_ratio(snapshot.calibration_feedback_count, memory_count)
    gap_ratio = _safe_ratio(snapshot.coverage_gap_count, memory_count)
    backlog_pressure = _safe_ratio(snapshot.open_review_backlog_count, memory_count)
    age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    health_score = _health_score(
        memory_freshness_ratio=freshness_ratio,
        memory_reuse_ratio=reuse_ratio,
        calibration_feedback_ratio=feedback_ratio,
        coverage_gap_ratio=gap_ratio,
        review_backlog_pressure=backlog_pressure,
    )
    reason_codes = _row_reason_codes(
        snapshot_age_seconds=age_seconds,
        memory_freshness_ratio=freshness_ratio,
        memory_reuse_ratio=reuse_ratio,
        calibration_feedback_ratio=feedback_ratio,
        coverage_gap_ratio=gap_ratio,
        review_backlog_pressure=backlog_pressure,
        config=config,
    )

    return ResearchTeamMemoryRetentionHealthRow(
        team_id=snapshot.team_id,
        category_id=snapshot.category_id,
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=age_seconds,
        memory_item_count=memory_count,
        fresh_memory_item_count=snapshot.fresh_memory_item_count,
        reused_memory_item_count=snapshot.reused_memory_item_count,
        calibration_feedback_count=snapshot.calibration_feedback_count,
        coverage_gap_count=snapshot.coverage_gap_count,
        open_review_backlog_count=snapshot.open_review_backlog_count,
        high_priority_review_backlog_count=snapshot.high_priority_review_backlog_count,
        memory_freshness_ratio=freshness_ratio,
        memory_reuse_ratio=reuse_ratio,
        calibration_feedback_ratio=feedback_ratio,
        coverage_gap_ratio=gap_ratio,
        review_backlog_pressure=backlog_pressure,
        retention_health_score=health_score,
        health_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot_age_seconds: Decimal,
    memory_freshness_ratio: Decimal,
    memory_reuse_ratio: Decimal,
    calibration_feedback_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    review_backlog_pressure: Decimal,
    config: ResearchTeamMemoryRetentionHealthConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reason_codes.append(SNAPSHOT_STALE_REASON)
    if memory_freshness_ratio < config.min_memory_freshness_ratio:
        reason_codes.append(LOW_FRESHNESS_REASON)
    if memory_reuse_ratio < config.min_memory_reuse_ratio:
        reason_codes.append(LOW_REUSE_REASON)
    if calibration_feedback_ratio < config.min_calibration_feedback_ratio:
        reason_codes.append(MISSING_CALIBRATION_REASON)
    if coverage_gap_ratio > config.max_coverage_gap_ratio:
        reason_codes.append(COVERAGE_GAP_REASON)
    if review_backlog_pressure > config.max_review_backlog_pressure:
        reason_codes.append(BACKLOG_PRESSURE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _report_reason_codes(rows: tuple[ResearchTeamMemoryRetentionHealthRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_MEMORY_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        )
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryRetentionHealthRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemoryRetentionHealthReasonCodeCount, ...]:
    if reason_codes == (NO_MEMORY_REASON,):
        return (
            ResearchTeamMemoryRetentionHealthReasonCodeCount(
                reason_code=NO_MEMORY_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchTeamMemoryRetentionHealthReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _health_score(
    *,
    memory_freshness_ratio: Decimal,
    memory_reuse_ratio: Decimal,
    calibration_feedback_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    review_backlog_pressure: Decimal,
) -> Decimal:
    return _quantize_decimal(
        (
            memory_freshness_ratio
            + memory_reuse_ratio
            + calibration_feedback_ratio
            + (ONE - coverage_gap_ratio)
            + (ONE - review_backlog_pressure)
        )
        / HEALTH_COMPONENT_COUNT
    )


def _aggregate_ratio(
    rows: tuple[ResearchTeamMemoryRetentionHealthRow, ...],
    field_name: str,
) -> Decimal:
    total_memory = sum((row.memory_item_count for row in rows), ZERO)
    if total_memory == ZERO:
        return ZERO
    return _safe_ratio(sum((getattr(row, field_name) for row in rows), ZERO), total_memory)


def _aggregate_health_score(rows: tuple[ResearchTeamMemoryRetentionHealthRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _health_score(
        memory_freshness_ratio=_aggregate_ratio(rows, "fresh_memory_item_count"),
        memory_reuse_ratio=_aggregate_ratio(rows, "reused_memory_item_count"),
        calibration_feedback_ratio=_aggregate_ratio(rows, "calibration_feedback_count"),
        coverage_gap_ratio=_aggregate_ratio(rows, "coverage_gap_count"),
        review_backlog_pressure=_aggregate_ratio(rows, "open_review_backlog_count"),
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _validate_snapshot(snapshot: ResearchTeamMemoryRetentionHealthSnapshot) -> None:
    if snapshot.memory_item_count <= ZERO:
        raise ValueError("memory_item_count must be positive")
    for field_name in (
        "fresh_memory_item_count",
        "reused_memory_item_count",
        "calibration_feedback_count",
        "coverage_gap_count",
        "open_review_backlog_count",
    ):
        if getattr(snapshot, field_name) > snapshot.memory_item_count:
            raise ValueError(f"{field_name} cannot exceed memory_item_count")
    if snapshot.high_priority_review_backlog_count > snapshot.open_review_backlog_count:
        raise ValueError(
            "high_priority_review_backlog_count cannot exceed open_review_backlog_count",
        )


def _validate_row(row: ResearchTeamMemoryRetentionHealthRow) -> None:
    if row.memory_item_count <= ZERO:
        raise ValueError("memory_item_count must be positive")
    expected_ratios = {
        "memory_freshness_ratio": _safe_ratio(
            row.fresh_memory_item_count,
            row.memory_item_count,
        ),
        "memory_reuse_ratio": _safe_ratio(
            row.reused_memory_item_count,
            row.memory_item_count,
        ),
        "calibration_feedback_ratio": _safe_ratio(
            row.calibration_feedback_count,
            row.memory_item_count,
        ),
        "coverage_gap_ratio": _safe_ratio(row.coverage_gap_count, row.memory_item_count),
        "review_backlog_pressure": _safe_ratio(
            row.open_review_backlog_count,
            row.memory_item_count,
        ),
    }
    for field_name, expected_value in expected_ratios.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match row counts")
    expected_score = _health_score(
        memory_freshness_ratio=row.memory_freshness_ratio,
        memory_reuse_ratio=row.memory_reuse_ratio,
        calibration_feedback_ratio=row.calibration_feedback_ratio,
        coverage_gap_ratio=row.coverage_gap_ratio,
        review_backlog_pressure=row.review_backlog_pressure,
    )
    if row.retention_health_score != expected_score:
        raise ValueError("retention_health_score must match row ratios")
    if row.health_status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("health_status must match reason_codes")


def _validate_report(report: ResearchTeamMemoryRetentionHealthReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count must match rows")
    if report.team_category_count != _decimal_count(len(report.rows)):
        raise ValueError("team_category_count must match rows")
    for field_name in (
        "memory_item_count",
        "fresh_memory_item_count",
        "reused_memory_item_count",
        "calibration_feedback_count",
        "coverage_gap_count",
        "open_review_backlog_count",
        "high_priority_review_backlog_count",
    ):
        if getattr(report, field_name) != sum(
            (getattr(row, field_name) for row in report.rows),
            ZERO,
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count != _decimal_count(
        sum(1 for row in report.rows if row.health_status == "pass")
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.health_status == "watch")
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.health_status == "block")
    ):
        raise ValueError("block_count must match rows")
    expected_ratios = {
        "memory_freshness_ratio": _aggregate_ratio(report.rows, "fresh_memory_item_count"),
        "memory_reuse_ratio": _aggregate_ratio(report.rows, "reused_memory_item_count"),
        "calibration_feedback_ratio": _aggregate_ratio(
            report.rows,
            "calibration_feedback_count",
        ),
        "coverage_gap_ratio": _aggregate_ratio(report.rows, "coverage_gap_count"),
        "review_backlog_pressure": _aggregate_ratio(
            report.rows,
            "open_review_backlog_count",
        ),
        "retention_health_score": _aggregate_health_score(report.rows),
    }
    for field_name, expected_value in expected_ratios.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchTeamMemoryRetentionHealthRow, ...],
) -> tuple[ResearchTeamMemoryRetentionHealthRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized_rows:
        if type(row) is not ResearchTeamMemoryRetentionHealthRow:
            raise ValueError("rows must contain ResearchTeamMemoryRetentionHealthRow")
        require_paper_only_flags("research team memory retention health row", row)
        key = (row.team_id, row.category_id)
        if key in seen_keys:
            raise ValueError("rows team/category values must be unique")
        seen_keys.add(key)
    if normalized_rows != tuple(
        sorted(normalized_rows, key=lambda row: (row.team_id, row.category_id))
    ):
        raise ValueError("rows must be deterministically sorted")
    return normalized_rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamMemoryRetentionHealthReasonCodeCount, ...],
) -> tuple[ResearchTeamMemoryRetentionHealthReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not ResearchTeamMemoryRetentionHealthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemoryRetentionHealthReasonCodeCount",
            )
        require_paper_only_flags(
            "research team memory retention health reason count",
            count,
        )
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized_counts != tuple(
        sorted(normalized_counts, key=lambda count: REASON_CODE_RANK[count.reason_code])
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized_counts


def _normalize_reason_codes(value: object, allowed: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    stable_codes = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if stable_codes != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _payload_value(getattr(value, item.name))
            for item in fields(value)
        }
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _validate_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, nested_item in enumerate(item):
                    if type(nested_item) is dict:
                        _validate_payload_flags(nested_item, f"{field_path}.{key}.{index}")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        return
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if digest != _digest_payload(payload):
        raise ValueError("derived_validation_digest must match payload")


def _derived_validation_digest(report: ResearchTeamMemoryRetentionHealthReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload field or value")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANT)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_decimal(
        "snapshot_age_seconds",
        (micros / MICROSECONDS_PER_SECOND).quantize(
            DECIMAL_QUANT,
            rounding=ROUND_HALF_EVEN,
        ),
    )


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_decimal(value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
