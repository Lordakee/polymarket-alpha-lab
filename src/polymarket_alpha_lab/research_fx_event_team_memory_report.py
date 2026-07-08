"""Pure report-only FX event team memory readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchFxEventTeamMemoryConfig",
    "ResearchFxEventTeamMemoryObservation",
    "ResearchFxEventTeamMemoryReasonCodeCount",
    "ResearchFxEventTeamMemoryReport",
    "ResearchFxEventTeamMemoryRow",
    "build_research_fx_event_team_memory_report",
    "research_fx_event_team_memory_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-fx-event-team-memory-report-v0"

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

NO_OBSERVATIONS_REASON = "fx_event_memory_no_observations"
REPORT_PASS_REASON = "fx_event_memory_report_pass"
REPORT_WATCH_REASON = "fx_event_memory_report_watch"
REPORT_BLOCK_REASON = "fx_event_memory_report_block"
SOURCE_FRESH_REASON = "fx_event_memory_source_fresh"
SOURCE_WATCH_REASON = "fx_event_memory_source_watch"
SOURCE_STALE_REASON = "fx_event_memory_source_stale"
EVIDENCE_REUSE_READY_REASON = "fx_event_memory_evidence_reuse_ready"
EVIDENCE_REUSE_LOW_REASON = "fx_event_memory_evidence_reuse_low"
MACRO_LINKAGE_READY_REASON = "fx_event_memory_macro_linkage_ready"
MACRO_LINKAGE_WEAK_REASON = "fx_event_memory_macro_linkage_weak"
CALIBRATION_READY_REASON = "fx_event_memory_calibration_ready"
CALIBRATION_UNDERPOWERED_REASON = "fx_event_memory_calibration_underpowered"

REPORT_REASON_BY_STATUS = {
    STATUS_PASS: REPORT_PASS_REASON,
    STATUS_WATCH: REPORT_WATCH_REASON,
    STATUS_BLOCK: REPORT_BLOCK_REASON,
}
REASON_CODES = (
    NO_OBSERVATIONS_REASON,
    CALIBRATION_READY_REASON,
    CALIBRATION_UNDERPOWERED_REASON,
    EVIDENCE_REUSE_LOW_REASON,
    EVIDENCE_REUSE_READY_REASON,
    MACRO_LINKAGE_READY_REASON,
    MACRO_LINKAGE_WEAK_REASON,
    REPORT_BLOCK_REASON,
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    SOURCE_FRESH_REASON,
    SOURCE_STALE_REASON,
    SOURCE_WATCH_REASON,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")

AGGREGATE_LABEL_ALLOWED_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789-_",
)
UNSAFE_LABEL_FRAGMENTS = (
    "http",
    "www.",
    "url",
    "source-text",
    "source_text",
    "source text",
    "raw",
    "quote",
    "excerpt",
    "transcript",
    "candidate",
    "market",
    "slug",
    "question",
    "dsn",
    "table",
    "token",
    "private",
    "auth",
    "wal" "let",
    "or" "der",
    "li" "ve",
    "tra" "de",
    "sizing",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchFxEventTeamMemoryConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    source_fresh_seconds: Decimal = Decimal("7200")
    source_stale_seconds: Decimal = Decimal("86400")
    min_calibration_sample_count: Decimal = Decimal("20")
    pass_readiness_score: Decimal = Decimal("0.750000")
    watch_readiness_score: Decimal = Decimal("0.500000")
    source_freshness_weight: Decimal = Decimal("0.250000")
    evidence_reuse_weight: Decimal = Decimal("0.250000")
    macro_linkage_weight: Decimal = Decimal("0.250000")
    calibration_readiness_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchFxEventTeamMemoryConfig:
            raise ValueError("config must be exact")
        _require_config_version(self.config_version)
        for field_name in ("source_fresh_seconds", "source_stale_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.source_fresh_seconds >= self.source_stale_seconds:
            raise ValueError("source_fresh_seconds must be less than source_stale_seconds")
        object.__setattr__(
            self,
            "min_calibration_sample_count",
            _require_positive_whole_decimal(
                "min_calibration_sample_count",
                self.min_calibration_sample_count,
            ),
        )
        for field_name in ("pass_readiness_score", "watch_readiness_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must exceed watch_readiness_score")
        for field_name in (
            "source_freshness_weight",
            "evidence_reuse_weight",
            "macro_linkage_weight",
            "calibration_readiness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if _quantize(
            self.source_freshness_weight
            + self.evidence_reuse_weight
            + self.macro_linkage_weight
            + self.calibration_readiness_weight,
        ) != ONE:
            raise ValueError("component weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchFxEventTeamMemoryObservation:
    specialist_label: str
    event_bucket: str
    source_family_label: str
    source_observed_at: datetime
    evidence_reuse_ratio: Decimal
    macro_linkage_score: Decimal
    calibration_sample_count: Decimal
    calibration_error: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchFxEventTeamMemoryObservation:
            raise ValueError("observation must be exact")
        for field_name in ("specialist_label", "event_bucket", "source_family_label"):
            object.__setattr__(
                self,
                field_name,
                _require_aggregate_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in ("evidence_reuse_ratio", "macro_linkage_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_whole_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "calibration_error",
            _require_probability_decimal("calibration_error", self.calibration_error),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchFxEventTeamMemoryRow:
    specialist_label: str
    event_bucket: str
    source_family_label: str
    source_observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_score: Decimal
    evidence_reuse_ratio: Decimal
    macro_linkage_score: Decimal
    calibration_sample_count: Decimal
    calibration_error: Decimal
    calibration_readiness_score: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchFxEventTeamMemoryRow:
            raise ValueError("row must be exact")
        for field_name in ("specialist_label", "event_bucket", "source_family_label"):
            object.__setattr__(
                self,
                field_name,
                _require_aggregate_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "source_freshness_score",
            "evidence_reuse_ratio",
            "macro_linkage_score",
            "calibration_error",
            "calibration_readiness_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_whole_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchFxEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchFxEventTeamMemoryReasonCodeCount:
            raise ValueError("reason_code_count must be exact")
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchFxEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    specialist_count: Decimal
    event_bucket_count: Decimal
    source_family_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal | None
    rows: tuple[ResearchFxEventTeamMemoryRow, ...]
    reason_code_counts: tuple[ResearchFxEventTeamMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchFxEventTeamMemoryReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "specialist_count",
            "event_bucket_count",
            "source_family_count",
            "observation_count",
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
            "average_readiness_score",
            _require_optional_probability_decimal(
                "average_readiness_score",
                self.average_readiness_score,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        digest = _digest_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match report")


def build_research_fx_event_team_memory_report(
    observations: Iterable[object],
    *,
    config: ResearchFxEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchFxEventTeamMemoryReport:
    if type(config) is not ResearchFxEventTeamMemoryConfig:
        raise ValueError("config must be a ResearchFxEventTeamMemoryConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.source_observed_at > generated_at_utc:
            raise ValueError("source_observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation=item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in items
            ),
            key=lambda row: (
                STATUS_RANK[row.status],
                row.event_bucket,
                row.specialist_label,
                row.source_family_label,
            ),
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchFxEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_summary_status(reason_codes),
        specialist_count=_decimal_count(len({row.specialist_label for row in rows})),
        event_bucket_count=_decimal_count(len({row.event_bucket for row in rows})),
        source_family_count=_decimal_count(len({row.source_family_label for row in rows})),
        observation_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_readiness_score=_average_readiness_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_fx_event_team_memory_report_payload(
    report: ResearchFxEventTeamMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchFxEventTeamMemoryReport:
        raise ValueError("report must be a ResearchFxEventTeamMemoryReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_unsafe_public_payload("report payload", payload)
    _verify_payload_digest(payload)
    return payload


def _row_from_observation(
    *,
    observation: ResearchFxEventTeamMemoryObservation,
    config: ResearchFxEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchFxEventTeamMemoryRow:
    source_age_seconds = _age_seconds(generated_at, observation.source_observed_at)
    source_freshness_score = _source_freshness_score(
        source_age_seconds,
        config=config,
    )
    calibration_readiness_score = _calibration_readiness_score(
        sample_count=observation.calibration_sample_count,
        calibration_error=observation.calibration_error,
        config=config,
    )
    readiness_score = _quantize(
        source_freshness_score * config.source_freshness_weight
        + observation.evidence_reuse_ratio * config.evidence_reuse_weight
        + observation.macro_linkage_score * config.macro_linkage_weight
        + calibration_readiness_score * config.calibration_readiness_weight,
    )
    status = _status_from_score(readiness_score, config=config)
    return ResearchFxEventTeamMemoryRow(
        specialist_label=observation.specialist_label,
        event_bucket=observation.event_bucket,
        source_family_label=observation.source_family_label,
        source_observed_at=observation.source_observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_score=source_freshness_score,
        evidence_reuse_ratio=observation.evidence_reuse_ratio,
        macro_linkage_score=observation.macro_linkage_score,
        calibration_sample_count=observation.calibration_sample_count,
        calibration_error=observation.calibration_error,
        calibration_readiness_score=calibration_readiness_score,
        readiness_score=readiness_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            config=config,
            source_age_seconds=source_age_seconds,
        ),
    )


def _source_freshness_score(
    source_age_seconds: Decimal,
    *,
    config: ResearchFxEventTeamMemoryConfig,
) -> Decimal:
    if source_age_seconds <= config.source_fresh_seconds:
        return ONE
    if source_age_seconds >= config.source_stale_seconds:
        return ZERO
    return _quantize(ONE - source_age_seconds / config.source_stale_seconds)


def _calibration_readiness_score(
    *,
    sample_count: Decimal,
    calibration_error: Decimal,
    config: ResearchFxEventTeamMemoryConfig,
) -> Decimal:
    sample_coverage = min(ONE, sample_count / config.min_calibration_sample_count)
    return _quantize(sample_coverage * (ONE - calibration_error))


def _status_from_score(
    readiness_score: Decimal,
    *,
    config: ResearchFxEventTeamMemoryConfig,
) -> str:
    if readiness_score >= config.pass_readiness_score:
        return STATUS_PASS
    if readiness_score >= config.watch_readiness_score:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_reason_codes(
    *,
    observation: ResearchFxEventTeamMemoryObservation,
    config: ResearchFxEventTeamMemoryConfig,
    source_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if source_age_seconds <= config.source_fresh_seconds:
        reason_codes.add(SOURCE_FRESH_REASON)
    elif source_age_seconds >= config.source_stale_seconds:
        reason_codes.add(SOURCE_STALE_REASON)
    else:
        reason_codes.add(SOURCE_WATCH_REASON)
    if observation.evidence_reuse_ratio >= config.pass_readiness_score:
        reason_codes.add(EVIDENCE_REUSE_READY_REASON)
    elif observation.evidence_reuse_ratio < config.watch_readiness_score:
        reason_codes.add(EVIDENCE_REUSE_LOW_REASON)
    if observation.macro_linkage_score >= config.pass_readiness_score:
        reason_codes.add(MACRO_LINKAGE_READY_REASON)
    elif observation.macro_linkage_score < config.watch_readiness_score:
        reason_codes.add(MACRO_LINKAGE_WEAK_REASON)
    if observation.calibration_sample_count >= config.min_calibration_sample_count:
        reason_codes.add(CALIBRATION_READY_REASON)
    else:
        reason_codes.add(CALIBRATION_UNDERPOWERED_REASON)
    return tuple(sorted(reason_codes))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchFxEventTeamMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchFxEventTeamMemoryObservation:
            raise ValueError("observations must contain ResearchFxEventTeamMemoryObservation")
        _require_hard_flags("observation", value)
    return tuple(
        sorted(
            values,
            key=lambda item: (
                item.event_bucket,
                item.specialist_label,
                item.source_family_label,
            ),
        ),
    )


def _summary_reason_codes(rows: tuple[ResearchFxEventTeamMemoryRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(REPORT_REASON_BY_STATUS[_status_from_rows(rows)])
    return tuple(sorted(reason_codes))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (NO_OBSERVATIONS_REASON,):
        return STATUS_BLOCK
    if REPORT_BLOCK_REASON in reason_codes:
        return STATUS_BLOCK
    if REPORT_WATCH_REASON in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_rows(rows: tuple[ResearchFxEventTeamMemoryRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchFxEventTeamMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchFxEventTeamMemoryReasonCodeCount, ...]:
    if reason_codes == (NO_OBSERVATIONS_REASON,):
        return (
            ResearchFxEventTeamMemoryReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    counts.update({REPORT_REASON_BY_STATUS[_status_from_rows(rows)]: 1})
    return tuple(
        ResearchFxEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_count(rows: tuple[ResearchFxEventTeamMemoryRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(row.status == status for row in rows))


def _average_readiness_score(
    rows: tuple[ResearchFxEventTeamMemoryRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.readiness_score for row in rows), ZERO) / Decimal(len(rows)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchFxEventTeamMemoryRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchFxEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchFxEventTeamMemoryRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                row.event_bucket,
                row.specialist_label,
                row.source_family_label,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchFxEventTeamMemoryReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    for count in counts:
        if type(count) is not ResearchFxEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchFxEventTeamMemoryReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_report(report: ResearchFxEventTeamMemoryReport) -> None:
    rows = report.rows
    if report.specialist_count != _decimal_count(len({row.specialist_label for row in rows})):
        raise ValueError("specialist_count must match rows")
    if report.event_bucket_count != _decimal_count(len({row.event_bucket for row in rows})):
        raise ValueError("event_bucket_count must match rows")
    if report.source_family_count != _decimal_count(
        len({row.source_family_label for row in rows}),
    ):
        raise ValueError("source_family_count must match rows")
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average_readiness_score(rows):
        raise ValueError("average_readiness_score must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_counts = _reason_code_counts(rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
    )


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("value must be quantizable") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_config_version(value: object) -> None:
    if type(value) is not str or value != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_aggregate_label(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be an aggregate-safe label")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in AGGREGATE_LABEL_ALLOWED_CHARS for character in value):
        raise ValueError(f"{field_name} must be aggregate-safe")
    if any(fragment in value for fragment in UNSAFE_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be aggregate-safe")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(sorted(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _unsigned_payload(report: ResearchFxEventTeamMemoryReport) -> dict[str, Any]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return unsigned


def _digest_report(report: ResearchFxEventTeamMemoryReport) -> str:
    return _digest_payload(_unsigned_payload(report))


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned):
        raise ValueError("derived_validation_digest does not match payload")


def _reject_public_numbers(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numbers(item)
    elif type(value) is list:
        for item in value:
            _reject_public_numbers(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_payload(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")
