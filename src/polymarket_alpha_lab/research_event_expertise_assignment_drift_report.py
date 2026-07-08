"""Public-safe aggregate drift report for specialist assignment fit."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchEventExpertiseAssignmentDriftConfig",
    "ResearchEventExpertiseAssignmentDriftReasonCodeCount",
    "ResearchEventExpertiseAssignmentDriftReport",
    "ResearchEventExpertiseAssignmentDriftRow",
    "ResearchEventExpertiseAssignmentDriftSignal",
    "build_research_event_expertise_assignment_drift_report",
    "research_event_expertise_assignment_drift_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-expertise-assignment-drift-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
LOW_ASSIGNMENT_COVERAGE_SCORE = Decimal("0.500000")
WATCH_ASSIGNMENT_COVERAGE_SCORE = Decimal("0.800000")
LOW_EXPERTISE_FIT_SCORE = Decimal("0.500000")
LOW_CAPACITY_BUFFER_SCORE = Decimal("0.150000")
LOW_MEMORY_FRESHNESS_SCORE = Decimal("0.500000")
LOW_CALIBRATION_SCORE = Decimal("0.550000")
WATCH_CATALYST_PRESSURE_SCORE = Decimal("0.600000")
BLOCK_CATALYST_PRESSURE_SCORE = Decimal("0.850000")
RAW_BUCKET_MARKERS = (
    "market-",
    "event-",
    "source-",
    "condition-",
    "token-",
    "0x",
)
SENSITIVE_TEXT_MARKERS = (
    "wal" "let",
    "au" "th",
    "or" "der",
    "tra" "de",
    "recom" "mend",
    "siz" "ing",
    "b" "uy",
    "se" "ll",
)


@dataclass(frozen=True)
class ResearchEventExpertiseAssignmentDriftConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_drift_score: Decimal = Decimal("0.750000")
    watch_drift_score: Decimal = Decimal("0.500000")
    min_expertise_fit_score: Decimal = Decimal("0.700000")
    min_capacity_buffer_score: Decimal = Decimal("0.250000")
    min_memory_freshness_score: Decimal = Decimal("0.600000")
    min_calibration_score: Decimal = Decimal("0.650000")
    max_catalyst_pressure_score: Decimal = Decimal("0.700000")
    expertise_weight: Decimal = Decimal("0.300000")
    capacity_weight: Decimal = Decimal("0.200000")
    memory_weight: Decimal = Decimal("0.200000")
    calibration_weight: Decimal = Decimal("0.200000")
    catalyst_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpertiseAssignmentDriftConfig:
            raise ValueError(
                "config must be exactly ResearchEventExpertiseAssignmentDriftConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_drift_score",
            "watch_drift_score",
            "min_expertise_fit_score",
            "min_capacity_buffer_score",
            "min_memory_freshness_score",
            "min_calibration_score",
            "max_catalyst_pressure_score",
            "expertise_weight",
            "capacity_weight",
            "memory_weight",
            "calibration_weight",
            "catalyst_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_drift_score <= self.watch_drift_score:
            raise ValueError("pass_drift_score must be greater than watch_drift_score")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventExpertiseAssignmentDriftSignal:
    domain_bucket: str
    team_bucket: str
    need_count: Decimal
    assigned_count: Decimal
    expertise_fit_score: Decimal
    capacity_buffer_score: Decimal
    memory_freshness_score: Decimal
    calibration_score: Decimal
    catalyst_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpertiseAssignmentDriftSignal:
            raise ValueError(
                "signal must be exactly ResearchEventExpertiseAssignmentDriftSignal",
            )
        _require_public_bucket_string("domain_bucket", self.domain_bucket)
        _require_public_bucket_string("team_bucket", self.team_bucket)
        object.__setattr__(
            self,
            "need_count",
            _require_positive_whole_decimal("need_count", self.need_count),
        )
        object.__setattr__(
            self,
            "assigned_count",
            _require_nonnegative_whole_decimal("assigned_count", self.assigned_count),
        )
        if self.assigned_count > self.need_count:
            raise ValueError("assigned_count must not exceed need_count")
        for field_name in (
            "expertise_fit_score",
            "capacity_buffer_score",
            "memory_freshness_score",
            "calibration_score",
            "catalyst_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchEventExpertiseAssignmentDriftRow:
    domain_bucket: str
    team_bucket: str
    need_count: Decimal
    assigned_count: Decimal
    assignment_coverage_score: Decimal
    expertise_fit_score: Decimal
    capacity_buffer_score: Decimal
    memory_freshness_score: Decimal
    calibration_score: Decimal
    catalyst_pressure_score: Decimal
    drift_score: Decimal
    expertise_weight: Decimal
    capacity_weight: Decimal
    memory_weight: Decimal
    calibration_weight: Decimal
    catalyst_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpertiseAssignmentDriftRow:
            raise ValueError("row must be exactly ResearchEventExpertiseAssignmentDriftRow")
        _require_public_bucket_string("domain_bucket", self.domain_bucket)
        _require_public_bucket_string("team_bucket", self.team_bucket)
        object.__setattr__(
            self,
            "need_count",
            _require_positive_whole_decimal("need_count", self.need_count),
        )
        object.__setattr__(
            self,
            "assigned_count",
            _require_nonnegative_whole_decimal("assigned_count", self.assigned_count),
        )
        if self.assigned_count > self.need_count:
            raise ValueError("assigned_count must not exceed need_count")
        for field_name in (
            "assignment_coverage_score",
            "expertise_fit_score",
            "capacity_buffer_score",
            "memory_freshness_score",
            "calibration_score",
            "catalyst_pressure_score",
            "drift_score",
            "expertise_weight",
            "capacity_weight",
            "memory_weight",
            "calibration_weight",
            "catalyst_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if _row_weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1")
        expected_coverage = _assignment_coverage_score(
            need_count=self.need_count,
            assigned_count=self.assigned_count,
        )
        if self.assignment_coverage_score != expected_coverage:
            raise ValueError("assignment_coverage_score must match counts")
        expected_drift_score = _drift_score(
            expertise_fit_score=self.expertise_fit_score,
            capacity_buffer_score=self.capacity_buffer_score,
            memory_freshness_score=self.memory_freshness_score,
            calibration_score=self.calibration_score,
            catalyst_pressure_score=self.catalyst_pressure_score,
            expertise_weight=self.expertise_weight,
            capacity_weight=self.capacity_weight,
            memory_weight=self.memory_weight,
            calibration_weight=self.calibration_weight,
            catalyst_weight=self.catalyst_weight,
        )
        if self.drift_score != expected_drift_score:
            raise ValueError("drift_score must match component scores")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventExpertiseAssignmentDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpertiseAssignmentDriftReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventExpertiseAssignmentDriftReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventExpertiseAssignmentDriftReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    team_count: Decimal
    total_need_count: Decimal
    total_assigned_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_drift_score: Decimal | None
    status: str
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...]
    reason_code_counts: tuple[
        ResearchEventExpertiseAssignmentDriftReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpertiseAssignmentDriftReport:
            raise ValueError(
                "report must be exactly ResearchEventExpertiseAssignmentDriftReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "team_count",
            "total_need_count",
            "total_assigned_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_drift_score",
            _require_optional_probability_decimal(
                "average_drift_score",
                self.average_drift_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_event_expertise_assignment_drift_report(
    assignment_signals: Iterable[object],
    *,
    config: ResearchEventExpertiseAssignmentDriftConfig,
    generated_at: datetime,
) -> ResearchEventExpertiseAssignmentDriftReport:
    if type(config) is not ResearchEventExpertiseAssignmentDriftConfig:
        raise ValueError(
            "config must be a ResearchEventExpertiseAssignmentDriftConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    signals = _normalize_signals(assignment_signals)
    rows = tuple(
        _row_from_signal(item, config=config)
        for item in sorted(signals, key=_signal_sort_key)
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    core_payload = _report_core_payload(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_decimal_count(len({row.domain_bucket for row in rows})),
        team_count=_decimal_count(len({row.team_bucket for row in rows})),
        total_need_count=sum((row.need_count for row in rows), ZERO),
        total_assigned_count=sum((row.assigned_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_drift_score=_average_drift_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )

    return ResearchEventExpertiseAssignmentDriftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_decimal_count(len({row.domain_bucket for row in rows})),
        team_count=_decimal_count(len({row.team_bucket for row in rows})),
        total_need_count=sum((row.need_count for row in rows), ZERO),
        total_assigned_count=sum((row.assigned_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_drift_score=_average_drift_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        payload_digest=_payload_digest(core_payload),
    )


def research_event_expertise_assignment_drift_report_payload(
    report: ResearchEventExpertiseAssignmentDriftReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventExpertiseAssignmentDriftReport:
        raise ValueError(
            "report must be a ResearchEventExpertiseAssignmentDriftReport",
        )
    _require_hard_flags("report", report)
    core_payload = _report_payload(report)
    digest = _payload_digest(core_payload)
    if digest != report.payload_digest:
        raise ValueError("payload_digest must match report payload")
    payload = dict(core_payload)
    payload["payload_digest"] = report.payload_digest
    return payload


def _row_from_signal(
    signal: ResearchEventExpertiseAssignmentDriftSignal,
    *,
    config: ResearchEventExpertiseAssignmentDriftConfig,
) -> ResearchEventExpertiseAssignmentDriftRow:
    coverage_score = _assignment_coverage_score(
        need_count=signal.need_count,
        assigned_count=signal.assigned_count,
    )
    drift_score = _drift_score(
        expertise_fit_score=signal.expertise_fit_score,
        capacity_buffer_score=signal.capacity_buffer_score,
        memory_freshness_score=signal.memory_freshness_score,
        calibration_score=signal.calibration_score,
        catalyst_pressure_score=signal.catalyst_pressure_score,
        expertise_weight=config.expertise_weight,
        capacity_weight=config.capacity_weight,
        memory_weight=config.memory_weight,
        calibration_weight=config.calibration_weight,
        catalyst_weight=config.catalyst_weight,
    )
    status = _row_status(
        assignment_coverage_score=coverage_score,
        expertise_fit_score=signal.expertise_fit_score,
        capacity_buffer_score=signal.capacity_buffer_score,
        memory_freshness_score=signal.memory_freshness_score,
        calibration_score=signal.calibration_score,
        catalyst_pressure_score=signal.catalyst_pressure_score,
        drift_score=drift_score,
        config=config,
    )
    return ResearchEventExpertiseAssignmentDriftRow(
        domain_bucket=signal.domain_bucket,
        team_bucket=signal.team_bucket,
        need_count=signal.need_count,
        assigned_count=signal.assigned_count,
        assignment_coverage_score=coverage_score,
        expertise_fit_score=signal.expertise_fit_score,
        capacity_buffer_score=signal.capacity_buffer_score,
        memory_freshness_score=signal.memory_freshness_score,
        calibration_score=signal.calibration_score,
        catalyst_pressure_score=signal.catalyst_pressure_score,
        drift_score=drift_score,
        expertise_weight=config.expertise_weight,
        capacity_weight=config.capacity_weight,
        memory_weight=config.memory_weight,
        calibration_weight=config.calibration_weight,
        catalyst_weight=config.catalyst_weight,
        status=status,
        reason_codes=_row_reason_codes(
            assignment_coverage_score=coverage_score,
            expertise_fit_score=signal.expertise_fit_score,
            capacity_buffer_score=signal.capacity_buffer_score,
            memory_freshness_score=signal.memory_freshness_score,
            calibration_score=signal.calibration_score,
            catalyst_pressure_score=signal.catalyst_pressure_score,
            drift_score=drift_score,
            status=status,
            config=config,
        ),
    )


def _normalize_signals(
    assignment_signals: Iterable[object],
) -> tuple[ResearchEventExpertiseAssignmentDriftSignal, ...]:
    if isinstance(assignment_signals, (str, bytes)):
        raise ValueError("assignment_signals must be an iterable")
    try:
        values = tuple(assignment_signals)
    except TypeError as exc:
        raise ValueError("assignment_signals must be an iterable") from exc
    return tuple(_coerce_signal(value) for value in values)


def _coerce_signal(value: object) -> ResearchEventExpertiseAssignmentDriftSignal:
    if type(value) is ResearchEventExpertiseAssignmentDriftSignal:
        _require_hard_flags("signal", value)
        return value
    try:
        return ResearchEventExpertiseAssignmentDriftSignal(
            domain_bucket=getattr(value, "domain_bucket"),
            team_bucket=getattr(value, "team_bucket"),
            need_count=getattr(value, "need_count"),
            assigned_count=getattr(value, "assigned_count"),
            expertise_fit_score=getattr(value, "expertise_fit_score"),
            capacity_buffer_score=getattr(value, "capacity_buffer_score"),
            memory_freshness_score=getattr(value, "memory_freshness_score"),
            calibration_score=getattr(value, "calibration_score"),
            catalyst_pressure_score=getattr(value, "catalyst_pressure_score"),
            paper_only=getattr(value, "paper_only"),
            report_only=getattr(value, "report_only"),
            readonly=getattr(value, "readonly"),
        )
    except AttributeError as exc:
        raise ValueError("assignment signal must expose required fields") from exc


def _assignment_coverage_score(*, need_count: Decimal, assigned_count: Decimal) -> Decimal:
    with _decimal_context():
        return _quantize(assigned_count / need_count)


def _drift_score(
    *,
    expertise_fit_score: Decimal,
    capacity_buffer_score: Decimal,
    memory_freshness_score: Decimal,
    calibration_score: Decimal,
    catalyst_pressure_score: Decimal,
    expertise_weight: Decimal,
    capacity_weight: Decimal,
    memory_weight: Decimal,
    calibration_weight: Decimal,
    catalyst_weight: Decimal,
) -> Decimal:
    with _decimal_context():
        return _quantize(
            (expertise_fit_score * expertise_weight)
            + (capacity_buffer_score * capacity_weight)
            + (memory_freshness_score * memory_weight)
            + (calibration_score * calibration_weight)
            + ((ONE - catalyst_pressure_score) * catalyst_weight),
        )


def _row_status(
    *,
    assignment_coverage_score: Decimal,
    expertise_fit_score: Decimal,
    capacity_buffer_score: Decimal,
    memory_freshness_score: Decimal,
    calibration_score: Decimal,
    catalyst_pressure_score: Decimal,
    drift_score: Decimal,
    config: ResearchEventExpertiseAssignmentDriftConfig,
) -> str:
    if (
        drift_score < config.watch_drift_score
        or assignment_coverage_score < LOW_ASSIGNMENT_COVERAGE_SCORE
        or expertise_fit_score < LOW_EXPERTISE_FIT_SCORE
        or capacity_buffer_score < LOW_CAPACITY_BUFFER_SCORE
        or memory_freshness_score < LOW_MEMORY_FRESHNESS_SCORE
        or calibration_score < LOW_CALIBRATION_SCORE
        or catalyst_pressure_score > BLOCK_CATALYST_PRESSURE_SCORE
    ):
        return "block"
    if (
        drift_score < config.pass_drift_score
        or assignment_coverage_score < WATCH_ASSIGNMENT_COVERAGE_SCORE
        or expertise_fit_score < config.min_expertise_fit_score
        or capacity_buffer_score < config.min_capacity_buffer_score
        or memory_freshness_score < config.min_memory_freshness_score
        or calibration_score < config.min_calibration_score
        or catalyst_pressure_score >= WATCH_CATALYST_PRESSURE_SCORE
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    assignment_coverage_score: Decimal,
    expertise_fit_score: Decimal,
    capacity_buffer_score: Decimal,
    memory_freshness_score: Decimal,
    calibration_score: Decimal,
    catalyst_pressure_score: Decimal,
    drift_score: Decimal,
    status: str,
    config: ResearchEventExpertiseAssignmentDriftConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if assignment_coverage_score < LOW_ASSIGNMENT_COVERAGE_SCORE:
        reason_codes.append("assignment_coverage_low")
    elif assignment_coverage_score < WATCH_ASSIGNMENT_COVERAGE_SCORE:
        reason_codes.append("assignment_coverage_watch")

    if expertise_fit_score < LOW_EXPERTISE_FIT_SCORE:
        reason_codes.append("expertise_fit_low")
    elif expertise_fit_score < config.min_expertise_fit_score:
        reason_codes.append("expertise_fit_watch")

    if capacity_buffer_score < LOW_CAPACITY_BUFFER_SCORE:
        reason_codes.append("capacity_buffer_low")
    elif capacity_buffer_score < config.min_capacity_buffer_score:
        reason_codes.append("capacity_buffer_watch")

    if memory_freshness_score < LOW_MEMORY_FRESHNESS_SCORE:
        reason_codes.append("memory_freshness_low")
    elif memory_freshness_score < config.min_memory_freshness_score:
        reason_codes.append("memory_freshness_watch")

    if calibration_score < LOW_CALIBRATION_SCORE:
        reason_codes.append("calibration_drift")
    elif calibration_score < config.min_calibration_score:
        reason_codes.append("calibration_watch")

    if catalyst_pressure_score > BLOCK_CATALYST_PRESSURE_SCORE:
        reason_codes.append("catalyst_pressure_high")
    elif catalyst_pressure_score >= WATCH_CATALYST_PRESSURE_SCORE:
        reason_codes.append("catalyst_pressure_watch")

    if not reason_codes:
        if status == "pass":
            reason_codes.append("assignment_fit_aligned")
        elif drift_score < config.watch_drift_score:
            reason_codes.append("drift_score_low")
        else:
            reason_codes.append("drift_score_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_assignment_signals",)
    return tuple(sorted({reason for row in rows for reason in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventExpertiseAssignmentDriftReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventExpertiseAssignmentDriftReasonCodeCount(
                reason_code="no_assignment_signals",
                count=ONE,
            ),
        )
    counter = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchEventExpertiseAssignmentDriftReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _average_drift_score(
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with _decimal_context():
        return _quantize(sum((row.drift_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_report_consistency(
    report: ResearchEventExpertiseAssignmentDriftReport,
) -> None:
    rows = report.rows
    if report.domain_count != _decimal_count(len({row.domain_bucket for row in rows})):
        raise ValueError("domain_count must match rows")
    if report.team_count != _decimal_count(len({row.team_bucket for row in rows})):
        raise ValueError("team_count must match rows")
    if report.total_need_count != sum((row.need_count for row in rows), ZERO):
        raise ValueError("total_need_count must match rows")
    if report.total_assigned_count != sum((row.assigned_count for row in rows), ZERO):
        raise ValueError("total_assigned_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_drift_score != _average_drift_score(rows):
        raise ValueError("average_drift_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.payload_digest != _payload_digest(_report_payload(report)):
        raise ValueError("payload_digest must match report payload")


def _report_payload(
    report: ResearchEventExpertiseAssignmentDriftReport,
) -> dict[str, Any]:
    return _report_core_payload(
        generated_at=report.generated_at,
        config_version=report.config_version,
        domain_count=report.domain_count,
        team_count=report.team_count,
        total_need_count=report.total_need_count,
        total_assigned_count=report.total_assigned_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_drift_score=report.average_drift_score,
        status=report.status,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
    )


def _report_core_payload(
    *,
    generated_at: datetime,
    config_version: str,
    domain_count: Decimal,
    team_count: Decimal,
    total_need_count: Decimal,
    total_assigned_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_drift_score: Decimal | None,
    status: str,
    rows: tuple[ResearchEventExpertiseAssignmentDriftRow, ...],
    reason_code_counts: tuple[
        ResearchEventExpertiseAssignmentDriftReasonCodeCount,
        ...,
    ],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at.isoformat(),
        "config_version": config_version,
        "domain_count": _decimal_payload(domain_count),
        "team_count": _decimal_payload(team_count),
        "total_need_count": _decimal_payload(total_need_count),
        "total_assigned_count": _decimal_payload(total_assigned_count),
        "pass_count": _decimal_payload(pass_count),
        "watch_count": _decimal_payload(watch_count),
        "block_count": _decimal_payload(block_count),
        "average_drift_score": (
            None if average_drift_score is None else _decimal_payload(average_drift_score)
        ),
        "status": status,
        "rows": [_row_payload(row) for row in rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in reason_code_counts
        ],
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchEventExpertiseAssignmentDriftRow) -> dict[str, Any]:
    return {
        "domain_bucket": row.domain_bucket,
        "team_bucket": row.team_bucket,
        "need_count": _decimal_payload(row.need_count),
        "assigned_count": _decimal_payload(row.assigned_count),
        "assignment_coverage_score": _decimal_payload(row.assignment_coverage_score),
        "expertise_fit_score": _decimal_payload(row.expertise_fit_score),
        "capacity_buffer_score": _decimal_payload(row.capacity_buffer_score),
        "memory_freshness_score": _decimal_payload(row.memory_freshness_score),
        "calibration_score": _decimal_payload(row.calibration_score),
        "catalyst_pressure_score": _decimal_payload(row.catalyst_pressure_score),
        "drift_score": _decimal_payload(row.drift_score),
        "expertise_weight": _decimal_payload(row.expertise_weight),
        "capacity_weight": _decimal_payload(row.capacity_weight),
        "memory_weight": _decimal_payload(row.memory_weight),
        "calibration_weight": _decimal_payload(row.calibration_weight),
        "catalyst_weight": _decimal_payload(row.catalyst_weight),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: ResearchEventExpertiseAssignmentDriftReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventExpertiseAssignmentDriftRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchEventExpertiseAssignmentDriftRow] = []
    for row in rows:
        if type(row) is not ResearchEventExpertiseAssignmentDriftRow:
            raise ValueError("rows must contain ResearchEventExpertiseAssignmentDriftRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchEventExpertiseAssignmentDriftReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchEventExpertiseAssignmentDriftReasonCodeCount] = []
    for value in values:
        if type(value) is not ResearchEventExpertiseAssignmentDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventExpertiseAssignmentDriftReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _signal_sort_key(
    item: ResearchEventExpertiseAssignmentDriftSignal,
) -> tuple[str, str]:
    return (item.domain_bucket, item.team_bucket)


def _row_sort_key(
    item: ResearchEventExpertiseAssignmentDriftRow,
) -> tuple[str, str]:
    return (item.domain_bucket, item.team_bucket)


def _weight_sum(config: ResearchEventExpertiseAssignmentDriftConfig) -> Decimal:
    return _quantize(
        config.expertise_weight
        + config.capacity_weight
        + config.memory_weight
        + config.calibration_weight
        + config.catalyst_weight,
    )


def _row_weight_sum(row: ResearchEventExpertiseAssignmentDriftRow) -> Decimal:
    return _quantize(
        row.expertise_weight
        + row.capacity_weight
        + row.memory_weight
        + row.calibration_weight
        + row.catalyst_weight,
    )


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
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return str(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_bucket_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert isinstance(value, str)
    lowered = value.lower()
    if any(marker in lowered for marker in RAW_BUCKET_MARKERS):
        raise ValueError(f"{field_name} must be aggregate-only")
    if any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert isinstance(value, str)
    if value.lower() != value or " " in value:
        raise ValueError(f"{field_name} must be snake_case")


def _normalize_reason_codes(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


class _decimal_context:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_exc: object) -> bool:
        return False
