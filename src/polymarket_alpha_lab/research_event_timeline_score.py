"""Pure research event timeline quality score for research queueing."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from types import MappingProxyType
from typing import Any


DEFAULT_CONFIG_VERSION = "research-event-timeline-score-v1"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_SCORE = Decimal("0.500000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
SECONDS_PER_HOUR = Decimal("3600.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "event_timeline_quality_empty"
PASS_REASON = "event_timeline_quality_pass"
CATALYST_WATCH_REASON = "catalyst_timing_watch"
CATALYST_BLOCK_REASON = "catalyst_timing_block"
SOURCE_LAG_WATCH_REASON = "source_lag_watch"
SOURCE_LAG_BLOCK_REASON = "source_lag_block"
EVIDENCE_STALENESS_WATCH_REASON = "evidence_staleness_watch"
EVIDENCE_STALENESS_BLOCK_REASON = "evidence_staleness_block"
RESOLUTION_TIMING_WATCH_REASON = "resolution_timing_watch"
RESOLUTION_TIMING_BLOCK_REASON = "resolution_timing_block"
RESOLUTION_TIME_CLARITY_WATCH_REASON = "resolution_time_clarity_watch"
RESOLUTION_TIME_CLARITY_BLOCK_REASON = "resolution_time_clarity_block"

REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    CATALYST_BLOCK_REASON,
    SOURCE_LAG_BLOCK_REASON,
    EVIDENCE_STALENESS_BLOCK_REASON,
    RESOLUTION_TIMING_BLOCK_REASON,
    RESOLUTION_TIME_CLARITY_BLOCK_REASON,
    CATALYST_WATCH_REASON,
    SOURCE_LAG_WATCH_REASON,
    EVIDENCE_STALENESS_WATCH_REASON,
    RESOLUTION_TIMING_WATCH_REASON,
    RESOLUTION_TIME_CLARITY_WATCH_REASON,
    PASS_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        EMPTY_REASON,
        CATALYST_BLOCK_REASON,
        SOURCE_LAG_BLOCK_REASON,
        EVIDENCE_STALENESS_BLOCK_REASON,
        RESOLUTION_TIMING_BLOCK_REASON,
        RESOLUTION_TIME_CLARITY_BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        CATALYST_WATCH_REASON,
        SOURCE_LAG_WATCH_REASON,
        EVIDENCE_STALENESS_WATCH_REASON,
        RESOLUTION_TIMING_WATCH_REASON,
        RESOLUTION_TIME_CLARITY_WATCH_REASON,
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate_reference",
    "raw_candidate",
    "market_id",
    "market_slug",
    "market_question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
)


@dataclass(frozen=True)
class ResearchEventTimelineScoreConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_catalyst_lead_hours: Decimal = Decimal("24.000000")
    min_watch_catalyst_lead_hours: Decimal = Decimal("6.000000")
    max_pass_source_capture_lag_hours: Decimal = Decimal("2.000000")
    max_watch_source_capture_lag_hours: Decimal = Decimal("12.000000")
    max_pass_evidence_age_hours: Decimal = Decimal("4.000000")
    max_watch_evidence_age_hours: Decimal = Decimal("24.000000")
    min_pass_resolution_lead_hours: Decimal = Decimal("24.000000")
    min_watch_resolution_lead_hours: Decimal = Decimal("6.000000")
    min_pass_resolution_time_clarity_score: Decimal = Decimal("0.800000")
    min_watch_resolution_time_clarity_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineScoreConfig:
            raise ValueError("config must be a ResearchEventTimelineScoreConfig")
        _require_text("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_pass_catalyst_lead_hours",
            "min_watch_catalyst_lead_hours",
            "max_pass_source_capture_lag_hours",
            "max_watch_source_capture_lag_hours",
            "max_pass_evidence_age_hours",
            "max_watch_evidence_age_hours",
            "min_pass_resolution_lead_hours",
            "min_watch_resolution_lead_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_resolution_time_clarity_score",
            "min_watch_resolution_time_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_interval_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventTimelineScoreInput:
    research_reference: str
    observed_at: datetime
    catalyst_at: datetime
    source_first_available_at: datetime
    source_captured_at: datetime
    evidence_observed_at: datetime
    expected_resolution_at: datetime
    resolution_time_clarity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineScoreInput:
            raise ValueError("input must be a ResearchEventTimelineScoreInput")
        _require_text("research_reference", self.research_reference)
        for field_name in (
            "observed_at",
            "catalyst_at",
            "source_first_available_at",
            "source_captured_at",
            "evidence_observed_at",
            "expected_resolution_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_time_clarity_score",
            _normalize_unit_interval_decimal(
                "resolution_time_clarity_score",
                self.resolution_time_clarity_score,
            ),
        )
        if self.source_captured_at < self.source_first_available_at:
            raise ValueError("source_captured_at must not be before source_first_available_at")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventTimelineScoreRow:
    generated_at: datetime
    redacted_research_reference: str
    observed_at: datetime
    catalyst_at: datetime
    source_first_available_at: datetime
    source_captured_at: datetime
    evidence_observed_at: datetime
    expected_resolution_at: datetime
    hours_until_catalyst: Decimal
    source_capture_lag_hours: Decimal
    evidence_age_hours: Decimal
    hours_until_resolution: Decimal
    resolution_time_clarity_score: Decimal
    catalyst_timing_score: Decimal
    source_lag_score: Decimal
    evidence_freshness_score: Decimal
    resolution_timing_score: Decimal
    resolution_time_clarity_component_score: Decimal
    timeline_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineScoreRow:
            raise ValueError("row must be a ResearchEventTimelineScoreRow")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_redacted_reference(self.redacted_research_reference)
        for field_name in (
            "observed_at",
            "catalyst_at",
            "source_first_available_at",
            "source_captured_at",
            "evidence_observed_at",
            "expected_resolution_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "hours_until_catalyst",
            "source_capture_lag_hours",
            "evidence_age_hours",
            "hours_until_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_time_clarity_score",
            "catalyst_timing_score",
            "source_lag_score",
            "evidence_freshness_score",
            "resolution_timing_score",
            "resolution_time_clarity_component_score",
            "timeline_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_interval_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventTimelineScoreReport:
    generated_at: datetime
    config_version: str
    research_event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_timeline_quality_score: Decimal
    top_timeline_quality_score: Decimal
    min_hours_until_catalyst: Decimal | None
    max_source_capture_lag_hours: Decimal
    max_evidence_age_hours: Decimal
    min_hours_until_resolution: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: Mapping[str, Decimal]
    rows: tuple[ResearchEventTimelineScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineScoreReport:
            raise ValueError("report must be a ResearchEventTimelineScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "research_event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_timeline_quality_score",
            "top_timeline_quality_score",
            "max_source_capture_lag_hours",
            "max_evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_hours_until_catalyst",
            "min_hours_until_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_timeline_score_public_payload(self)


def build_research_event_timeline_score(
    events: Iterable[ResearchEventTimelineScoreInput],
    *,
    generated_at: datetime,
    config: ResearchEventTimelineScoreConfig,
) -> ResearchEventTimelineScoreReport:
    if type(config) is not ResearchEventTimelineScoreConfig:
        raise ValueError("config must be a ResearchEventTimelineScoreConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(event, generated_at=generated_at_utc, config=config)
                for event in _normalize_inputs(events, generated_at=generated_at_utc)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _status_from_reason_codes(reason_codes)
    return ResearchEventTimelineScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_event_count=_count(len(rows)),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        average_timeline_quality_score=_average_decimal(
            row.timeline_quality_score for row in rows
        ),
        top_timeline_quality_score=_max_decimal(row.timeline_quality_score for row in rows),
        min_hours_until_catalyst=_min_optional_decimal(
            row.hours_until_catalyst for row in rows
        ),
        max_source_capture_lag_hours=_max_decimal(
            row.source_capture_lag_hours for row in rows
        ),
        max_evidence_age_hours=_max_decimal(row.evidence_age_hours for row in rows),
        min_hours_until_resolution=_min_optional_decimal(
            row.hours_until_resolution for row in rows
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_event_timeline_score_public_payload(
    value: ResearchEventTimelineScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventTimelineScoreReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError("value must be a ResearchEventTimelineScoreReport or dict")
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_event_timeline_score_public_payload(payload)
    return dict(payload)


def validate_research_event_timeline_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    event: ResearchEventTimelineScoreInput,
    *,
    generated_at: datetime,
    config: ResearchEventTimelineScoreConfig,
) -> ResearchEventTimelineScoreRow:
    _validate_input_timestamps(event, generated_at)
    hours_until_catalyst = max(_hours_between(generated_at, event.catalyst_at), ZERO)
    source_capture_lag_hours = _hours_between(
        event.source_first_available_at,
        event.source_captured_at,
    )
    evidence_age_hours = _hours_between(event.evidence_observed_at, generated_at)
    hours_until_resolution = max(
        _hours_between(generated_at, event.expected_resolution_at),
        ZERO,
    )
    catalyst_timing_score = _minimum_threshold_score(
        hours_until_catalyst,
        pass_threshold=config.min_pass_catalyst_lead_hours,
        watch_threshold=config.min_watch_catalyst_lead_hours,
    )
    source_lag_score = _maximum_threshold_score(
        source_capture_lag_hours,
        pass_threshold=config.max_pass_source_capture_lag_hours,
        watch_threshold=config.max_watch_source_capture_lag_hours,
    )
    evidence_freshness_score = _maximum_threshold_score(
        evidence_age_hours,
        pass_threshold=config.max_pass_evidence_age_hours,
        watch_threshold=config.max_watch_evidence_age_hours,
    )
    resolution_timing_score = _minimum_threshold_score(
        hours_until_resolution,
        pass_threshold=config.min_pass_resolution_lead_hours,
        watch_threshold=config.min_watch_resolution_lead_hours,
    )
    resolution_time_clarity_component_score = _minimum_threshold_score(
        event.resolution_time_clarity_score,
        pass_threshold=config.min_pass_resolution_time_clarity_score,
        watch_threshold=config.min_watch_resolution_time_clarity_score,
    )
    reason_codes = _row_reason_codes(
        catalyst_timing_score=catalyst_timing_score,
        source_lag_score=source_lag_score,
        evidence_freshness_score=evidence_freshness_score,
        resolution_timing_score=resolution_timing_score,
        resolution_time_clarity_component_score=resolution_time_clarity_component_score,
    )
    return ResearchEventTimelineScoreRow(
        generated_at=generated_at,
        redacted_research_reference=_redacted_reference(event.research_reference),
        observed_at=event.observed_at,
        catalyst_at=event.catalyst_at,
        source_first_available_at=event.source_first_available_at,
        source_captured_at=event.source_captured_at,
        evidence_observed_at=event.evidence_observed_at,
        expected_resolution_at=event.expected_resolution_at,
        hours_until_catalyst=hours_until_catalyst,
        source_capture_lag_hours=source_capture_lag_hours,
        evidence_age_hours=evidence_age_hours,
        hours_until_resolution=hours_until_resolution,
        resolution_time_clarity_score=event.resolution_time_clarity_score,
        catalyst_timing_score=catalyst_timing_score,
        source_lag_score=source_lag_score,
        evidence_freshness_score=evidence_freshness_score,
        resolution_timing_score=resolution_timing_score,
        resolution_time_clarity_component_score=resolution_time_clarity_component_score,
        timeline_quality_score=_average_decimal(
            (
                catalyst_timing_score,
                source_lag_score,
                evidence_freshness_score,
                resolution_timing_score,
                resolution_time_clarity_component_score,
            ),
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    catalyst_timing_score: Decimal,
    source_lag_score: Decimal,
    evidence_freshness_score: Decimal,
    resolution_timing_score: Decimal,
    resolution_time_clarity_component_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_component_reason(
        reason_codes,
        catalyst_timing_score,
        watch_reason=CATALYST_WATCH_REASON,
        block_reason=CATALYST_BLOCK_REASON,
    )
    _append_component_reason(
        reason_codes,
        source_lag_score,
        watch_reason=SOURCE_LAG_WATCH_REASON,
        block_reason=SOURCE_LAG_BLOCK_REASON,
    )
    _append_component_reason(
        reason_codes,
        evidence_freshness_score,
        watch_reason=EVIDENCE_STALENESS_WATCH_REASON,
        block_reason=EVIDENCE_STALENESS_BLOCK_REASON,
    )
    _append_component_reason(
        reason_codes,
        resolution_timing_score,
        watch_reason=RESOLUTION_TIMING_WATCH_REASON,
        block_reason=RESOLUTION_TIMING_BLOCK_REASON,
    )
    _append_component_reason(
        reason_codes,
        resolution_time_clarity_component_score,
        watch_reason=RESOLUTION_TIME_CLARITY_WATCH_REASON,
        block_reason=RESOLUTION_TIME_CLARITY_BLOCK_REASON,
    )
    if not reason_codes:
        return (PASS_REASON,)
    return _stable_reason_codes(reason_codes)


def _append_component_reason(
    reason_codes: list[str],
    score: Decimal,
    *,
    watch_reason: str,
    block_reason: str,
) -> None:
    if score == ZERO:
        reason_codes.append(block_reason)
    elif score == WATCH_SCORE:
        reason_codes.append(watch_reason)


def _minimum_threshold_score(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value < watch_threshold:
        return ZERO
    if value < pass_threshold:
        return WATCH_SCORE
    return ONE


def _maximum_threshold_score(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value > watch_threshold:
        return ZERO
    if value > pass_threshold:
        return WATCH_SCORE
    return ONE


def _normalize_inputs(
    events: Iterable[ResearchEventTimelineScoreInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchEventTimelineScoreInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be iterable")
    try:
        normalized = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be iterable") from exc
    seen: set[str] = set()
    for event in normalized:
        if type(event) is not ResearchEventTimelineScoreInput:
            raise ValueError("events must contain ResearchEventTimelineScoreInput values")
        _require_hard_flags("event", event)
        if event.research_reference in seen:
            raise ValueError("research_reference values must be unique")
        seen.add(event.research_reference)
        _validate_input_timestamps(event, generated_at)
    return normalized


def _validate_input_timestamps(
    event: ResearchEventTimelineScoreInput,
    generated_at: datetime,
) -> None:
    if event.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    if event.source_first_available_at > generated_at:
        raise ValueError("source_first_available_at must not be after generated_at")
    if event.source_captured_at > generated_at:
        raise ValueError("source_captured_at must not be after generated_at")
    if event.evidence_observed_at > generated_at:
        raise ValueError("evidence_observed_at must not be after generated_at")
    if event.source_captured_at < event.source_first_available_at:
        raise ValueError("source_captured_at must not be before source_first_available_at")


def _normalize_rows(
    rows: Iterable[ResearchEventTimelineScoreRow],
) -> tuple[ResearchEventTimelineScoreRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventTimelineScoreRow:
            raise ValueError("rows must contain ResearchEventTimelineScoreRow values")
        _require_hard_flags("row", row)
        if row.redacted_research_reference in seen:
            raise ValueError("rows must not contain duplicate research references")
        seen.add(row.redacted_research_reference)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_config(config: ResearchEventTimelineScoreConfig) -> None:
    if config.min_pass_catalyst_lead_hours < config.min_watch_catalyst_lead_hours:
        raise ValueError(
            "min_pass_catalyst_lead_hours must be at least "
            "min_watch_catalyst_lead_hours",
        )
    if (
        config.max_pass_source_capture_lag_hours
        > config.max_watch_source_capture_lag_hours
    ):
        raise ValueError(
            "max_pass_source_capture_lag_hours must be at most "
            "max_watch_source_capture_lag_hours",
        )
    if config.max_pass_evidence_age_hours > config.max_watch_evidence_age_hours:
        raise ValueError(
            "max_pass_evidence_age_hours must be at most max_watch_evidence_age_hours",
        )
    if config.min_pass_resolution_lead_hours < config.min_watch_resolution_lead_hours:
        raise ValueError(
            "min_pass_resolution_lead_hours must be at least "
            "min_watch_resolution_lead_hours",
        )
    if (
        config.min_pass_resolution_time_clarity_score
        <= config.min_watch_resolution_time_clarity_score
    ):
        raise ValueError(
            "min_pass_resolution_time_clarity_score must exceed "
            "min_watch_resolution_time_clarity_score",
        )


def _validate_row(row: ResearchEventTimelineScoreRow) -> None:
    if row.source_captured_at < row.source_first_available_at:
        raise ValueError("source_captured_at must not be before source_first_available_at")
    if row.hours_until_catalyst != max(_hours_between(row.generated_at, row.catalyst_at), ZERO):
        raise ValueError("hours_until_catalyst must match timestamps")
    if row.source_capture_lag_hours != _hours_between(
        row.source_first_available_at,
        row.source_captured_at,
    ):
        raise ValueError("source_capture_lag_hours must match timestamps")
    if row.evidence_age_hours != _hours_between(row.evidence_observed_at, row.generated_at):
        raise ValueError("evidence_age_hours must match timestamps")
    if row.hours_until_resolution != max(
        _hours_between(row.generated_at, row.expected_resolution_at),
        ZERO,
    ):
        raise ValueError("hours_until_resolution must match timestamps")
    expected_score = _average_decimal(
        (
            row.catalyst_timing_score,
            row.source_lag_score,
            row.evidence_freshness_score,
            row.resolution_timing_score,
            row.resolution_time_clarity_component_score,
        ),
    )
    if row.timeline_quality_score != expected_score:
        raise ValueError("timeline_quality_score must match component scores")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only include pass reason")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason")


def _validate_report(report: ResearchEventTimelineScoreReport) -> None:
    rows = report.rows
    if report.research_event_count != _count(len(rows)):
        raise ValueError("research_event_count must match rows")
    if report.pass_count != _count(sum(row.status == "pass" for row in rows)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(row.status == "watch" for row in rows)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(row.status == "block" for row in rows)):
        raise ValueError("block_count must match rows")
    if report.average_timeline_quality_score != _average_decimal(
        row.timeline_quality_score for row in rows
    ):
        raise ValueError("average_timeline_quality_score must match rows")
    if report.top_timeline_quality_score != _max_decimal(
        row.timeline_quality_score for row in rows
    ):
        raise ValueError("top_timeline_quality_score must match rows")
    if report.min_hours_until_catalyst != _min_optional_decimal(
        row.hours_until_catalyst for row in rows
    ):
        raise ValueError("min_hours_until_catalyst must match rows")
    if report.max_source_capture_lag_hours != _max_decimal(
        row.source_capture_lag_hours for row in rows
    ):
        raise ValueError("max_source_capture_lag_hours must match rows")
    if report.max_evidence_age_hours != _max_decimal(row.evidence_age_hours for row in rows):
        raise ValueError("max_evidence_age_hours must match rows")
    if report.min_hours_until_resolution != _min_optional_decimal(
        row.hours_until_resolution for row in rows
    ):
        raise ValueError("min_hours_until_resolution must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_counts = dict(_reason_code_counts(rows))
    if dict(report.reason_code_counts) != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _set_or_validate_derived_validation_digest(
    report: ResearchEventTimelineScoreReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(report: ResearchEventTimelineScoreReport) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if isinstance(value, Mapping):
        return {
            key: _payload_value(value[key])
            for key in sorted(value, key=_mapping_sort_key(value))
        }
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_unit_interval_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must contain at least one reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _require_reason_code(field_name, item)
    stable = _stable_reason_codes(value)
    if stable != value:
        raise ValueError(f"{field_name} must follow canonical order")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if EMPTY_REASON in value and len(value) != 1:
        raise ValueError(f"{field_name} empty reason must stand alone")
    return value


def _normalize_reason_code_counts(value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
    if not isinstance(value, Mapping):
        raise ValueError("reason_code_counts must be a mapping")
    normalized: dict[str, Decimal] = {}
    for reason_code, count in value.items():
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code_counts contains an unknown reason code")
        normalized[reason_code] = _normalize_count(f"reason_code_counts.{reason_code}", count)
    return MappingProxyType(
        {
            reason_code: normalized[reason_code]
            for reason_code in sorted(normalized, key=_reason_code_sort_index)
        },
    )


def _reason_code_counts(
    rows: tuple[ResearchEventTimelineScoreRow, ...],
) -> Mapping[str, Decimal]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return _normalize_reason_code_counts(
        {reason_code: _count(count) for reason_code, count in counts.items()},
    )


def _report_reason_codes(
    rows: tuple[ResearchEventTimelineScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    unique = {reason_code for row in rows for reason_code in row.reason_codes}
    if unique == {PASS_REASON}:
        return (PASS_REASON,)
    unique.discard(PASS_REASON)
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in unique)


def _stable_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    unique = set(reason_codes)
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in unique)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_sort_key(row: ResearchEventTimelineScoreRow) -> tuple[str, str]:
    status_order = {"block": "0", "watch": "1", "pass": "2"}
    return (status_order[row.status], row.redacted_research_reference)


def _reason_code_sort_index(reason_code: str) -> int:
    if reason_code not in REASON_CODES:
        raise ValueError("unknown reason code")
    return REASON_CODE_PRIORITY.index(reason_code)


def _mapping_sort_key(value: Mapping[str, object]) -> Any:
    if all(type(key) is str and key in REASON_CODES for key in value):
        return _reason_code_sort_index
    return str


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(normalized, ZERO) / _count(len(normalized)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _min_optional_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return min(normalized)


def _hours_between(start: datetime, end: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(str((end - start).total_seconds()))
        return _quantize(seconds / SECONDS_PER_HOUR)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redacted_reference(research_reference: str) -> str:
    digest = hashlib.sha256(research_reference.encode("utf-8")).hexdigest()[:16]
    return f"research:{digest}"


def _require_redacted_reference(value: str) -> None:
    if type(value) is not str:
        raise ValueError("redacted_research_reference must be a string")
    prefix = "research:"
    digest = value.removeprefix(prefix)
    if (
        not value.startswith(prefix)
        or len(digest) != 16
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("redacted_research_reference must be redacted")


def _require_text(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES!r}")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} has unknown reason code")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "ResearchEventTimelineScoreConfig",
    "ResearchEventTimelineScoreInput",
    "ResearchEventTimelineScoreReport",
    "ResearchEventTimelineScoreRow",
    "build_research_event_timeline_score",
    "research_event_timeline_score_public_payload",
    "validate_research_event_timeline_score_public_payload",
)
