"""Pure aggregate event timeline evidence freshness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-event-timeline-evidence-freshness-report-v0"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_URGENCY_SCORE = Decimal("0.500000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
SECONDS_PER_HOUR = Decimal("3600.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "timeline_evidence_freshness_empty"
PASS_REASON = "timeline_evidence_freshness_pass"
WATCH_REASON = "timeline_evidence_freshness_watch"
BLOCK_REASON = "timeline_evidence_freshness_block"
CATALYST_WATCH_REASON = "catalyst_timing_watch"
CATALYST_BLOCK_REASON = "catalyst_timing_block"
STALE_EVIDENCE_WATCH_REASON = "stale_evidence_window_watch"
STALE_EVIDENCE_BLOCK_REASON = "stale_evidence_window_block"
MISSING_UPDATE_WATCH_REASON = "missing_update_pressure_watch"
MISSING_UPDATE_BLOCK_REASON = "missing_update_pressure_block"
SOURCE_RECENCY_WATCH_REASON = "source_recency_watch"
SOURCE_RECENCY_BLOCK_REASON = "source_recency_block"
COVERAGE_WATCH_REASON = "coverage_watch"
COVERAGE_BLOCK_REASON = "coverage_block"
HARD_RECHECK_REASON = "hard_recheck_flag"

REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    CATALYST_BLOCK_REASON,
    STALE_EVIDENCE_BLOCK_REASON,
    MISSING_UPDATE_BLOCK_REASON,
    SOURCE_RECENCY_BLOCK_REASON,
    COVERAGE_BLOCK_REASON,
    HARD_RECHECK_REASON,
    BLOCK_REASON,
    CATALYST_WATCH_REASON,
    STALE_EVIDENCE_WATCH_REASON,
    MISSING_UPDATE_WATCH_REASON,
    SOURCE_RECENCY_WATCH_REASON,
    COVERAGE_WATCH_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        CATALYST_BLOCK_REASON,
        STALE_EVIDENCE_BLOCK_REASON,
        MISSING_UPDATE_BLOCK_REASON,
        SOURCE_RECENCY_BLOCK_REASON,
        COVERAGE_BLOCK_REASON,
        HARD_RECHECK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        CATALYST_WATCH_REASON,
        STALE_EVIDENCE_WATCH_REASON,
        MISSING_UPDATE_WATCH_REASON,
        SOURCE_RECENCY_WATCH_REASON,
        COVERAGE_WATCH_REASON,
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate_reference",
    "raw_candidate",
    "raw_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_ref",
    "source_url",
    "source_text",
    "source_reference",
    "http://",
    "https://",
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
class ResearchEventTimelineEvidenceFreshnessReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_catalyst_lead_hours: Decimal = Decimal("24.000000")
    min_watch_catalyst_lead_hours: Decimal = Decimal("6.000000")
    max_pass_evidence_age_hours: Decimal = Decimal("6.000000")
    max_watch_evidence_age_hours: Decimal = Decimal("24.000000")
    max_pass_missing_update_pressure_hours: Decimal = Decimal("0.000000")
    max_watch_missing_update_pressure_hours: Decimal = Decimal("24.000000")
    max_pass_source_recency_hours: Decimal = Decimal("6.000000")
    max_watch_source_recency_hours: Decimal = Decimal("24.000000")
    min_pass_source_family_count: Decimal = Decimal("3")
    min_watch_source_family_count: Decimal = Decimal("2")
    min_pass_timeline_evidence_count: Decimal = Decimal("3")
    min_watch_timeline_evidence_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineEvidenceFreshnessReportConfig:
            raise ValueError(
                "config must be a ResearchEventTimelineEvidenceFreshnessReportConfig",
            )
        _require_text("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_pass_catalyst_lead_hours",
            "min_watch_catalyst_lead_hours",
            "max_pass_evidence_age_hours",
            "max_watch_evidence_age_hours",
            "max_pass_missing_update_pressure_hours",
            "max_watch_missing_update_pressure_hours",
            "max_pass_source_recency_hours",
            "max_watch_source_recency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_source_family_count",
            "min_watch_source_family_count",
            "min_pass_timeline_evidence_count",
            "min_watch_timeline_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventTimelineEvidenceFreshnessReportInput:
    aggregate_label: str
    catalyst_at: datetime
    latest_evidence_at: datetime
    latest_source_update_at: datetime
    expected_update_at: datetime
    source_family_count: Decimal
    timeline_evidence_count: Decimal
    hard_recheck_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineEvidenceFreshnessReportInput:
            raise ValueError(
                "input must be a ResearchEventTimelineEvidenceFreshnessReportInput",
            )
        _require_aggregate_label("aggregate_label", self.aggregate_label)
        for field_name in (
            "catalyst_at",
            "latest_evidence_at",
            "latest_source_update_at",
            "expected_update_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_nonnegative_count(
                "source_family_count",
                self.source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "timeline_evidence_count",
            _normalize_nonnegative_count(
                "timeline_evidence_count",
                self.timeline_evidence_count,
            ),
        )
        if self.latest_evidence_at > self.latest_source_update_at:
            raise ValueError(
                "latest_evidence_at must not be after latest_source_update_at",
            )
        if type(self.hard_recheck_flag) is not bool:
            raise ValueError("hard_recheck_flag must be a bool")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventTimelineEvidenceFreshnessReportRow:
    aggregate_public_label: str
    hours_until_catalyst: Decimal
    stale_evidence_window_hours: Decimal
    missing_update_pressure_hours: Decimal
    source_recency_hours: Decimal
    source_family_count: Decimal
    timeline_evidence_count: Decimal
    recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    hard_recheck_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineEvidenceFreshnessReportRow:
            raise ValueError("row must be a ResearchEventTimelineEvidenceFreshnessReportRow")
        _require_public_label("aggregate_public_label", self.aggregate_public_label)
        for field_name in (
            "hours_until_catalyst",
            "stale_evidence_window_hours",
            "missing_update_pressure_hours",
            "source_recency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_family_count", "timeline_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recheck_urgency_score",
            _normalize_probability(
                "recheck_urgency_score",
                self.recheck_urgency_score,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if type(self.hard_recheck_flag) is not bool:
            raise ValueError("hard_recheck_flag must be a bool")
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODE_PRIORITY)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventTimelineEvidenceFreshnessReport:
    generated_at: datetime
    config_version: str
    aggregate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_hours_until_catalyst: Decimal | None
    max_stale_evidence_window_hours: Decimal | None
    max_missing_update_pressure_hours: Decimal | None
    max_source_recency_hours: Decimal | None
    average_recheck_urgency_score: Decimal | None
    status: str
    rows: tuple[ResearchEventTimelineEvidenceFreshnessReportRow, ...]
    reason_code_counts: tuple[
        ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventTimelineEvidenceFreshnessReport:
            raise ValueError("report must be a ResearchEventTimelineEvidenceFreshnessReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("aggregate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_hours_until_catalyst",
            "max_stale_evidence_window_hours",
            "max_missing_update_pressure_hours",
            "max_source_recency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_recheck_urgency_score",
            _normalize_optional_probability(
                "average_recheck_urgency_score",
                self.average_recheck_urgency_score,
            ),
        )
        _require_member("status", self.status, STATUSES)
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
        _set_or_validate_public_digest(self)
        _reject_unsafe_public_payload("report", _payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_timeline_evidence_freshness_report_public_payload(self)


def build_research_event_timeline_evidence_freshness_report(
    inputs: Iterable[ResearchEventTimelineEvidenceFreshnessReportInput],
    *,
    generated_at: datetime,
    config: ResearchEventTimelineEvidenceFreshnessReportConfig,
) -> ResearchEventTimelineEvidenceFreshnessReport:
    if type(config) is not ResearchEventTimelineEvidenceFreshnessReportConfig:
        raise ValueError(
            "config must be a ResearchEventTimelineEvidenceFreshnessReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs, generated_at=generated_at_utc)
    public_labels = {
        item.aggregate_label: f"aggregate-{index:03d}"
        for index, item in enumerate(
            sorted(normalized_inputs, key=lambda item: item.aggregate_label),
            start=1,
        )
    }
    rows = tuple(
        sorted(
            (
                _row_for_input(
                    item,
                    aggregate_public_label=public_labels[item.aggregate_label],
                    generated_at=generated_at_utc,
                    config=config,
                )
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchEventTimelineEvidenceFreshnessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        aggregate_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        min_hours_until_catalyst=_min_decimal(row.hours_until_catalyst for row in rows),
        max_stale_evidence_window_hours=_max_decimal(
            row.stale_evidence_window_hours for row in rows
        ),
        max_missing_update_pressure_hours=_max_decimal(
            row.missing_update_pressure_hours for row in rows
        ),
        max_source_recency_hours=_max_decimal(row.source_recency_hours for row in rows),
        average_recheck_urgency_score=_average_decimal(
            row.recheck_urgency_score for row in rows
        ),
        status=_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_timeline_evidence_freshness_report_public_payload(
    value: ResearchEventTimelineEvidenceFreshnessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventTimelineEvidenceFreshnessReport:
        _validate_report(value)
        _validate_public_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEventTimelineEvidenceFreshnessReport or dict",
        )
    validate_research_event_timeline_evidence_freshness_report_public_payload(payload)
    return dict(payload)


def validate_research_event_timeline_evidence_freshness_report_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_scalars(payload)
    _validate_payload_public_digest(payload)


def research_event_timeline_evidence_freshness_report_public_digest(
    value: ResearchEventTimelineEvidenceFreshnessReport | dict[str, Any],
) -> str:
    payload = research_event_timeline_evidence_freshness_report_public_payload(value)
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    return public_digest


def _row_for_input(
    item: ResearchEventTimelineEvidenceFreshnessReportInput,
    *,
    aggregate_public_label: str,
    generated_at: datetime,
    config: ResearchEventTimelineEvidenceFreshnessReportConfig,
) -> ResearchEventTimelineEvidenceFreshnessReportRow:
    hours_until_catalyst = _positive_hours_between(generated_at, item.catalyst_at)
    stale_evidence_window_hours = _positive_hours_between(
        item.latest_evidence_at,
        generated_at,
    )
    missing_update_pressure_hours = _positive_hours_between(
        item.expected_update_at,
        generated_at,
    )
    source_recency_hours = _positive_hours_between(
        item.latest_source_update_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        hours_until_catalyst=hours_until_catalyst,
        stale_evidence_window_hours=stale_evidence_window_hours,
        missing_update_pressure_hours=missing_update_pressure_hours,
        source_recency_hours=source_recency_hours,
        source_family_count=item.source_family_count,
        timeline_evidence_count=item.timeline_evidence_count,
        hard_recheck_flag=item.hard_recheck_flag,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchEventTimelineEvidenceFreshnessReportRow(
        aggregate_public_label=aggregate_public_label,
        hours_until_catalyst=hours_until_catalyst,
        stale_evidence_window_hours=stale_evidence_window_hours,
        missing_update_pressure_hours=missing_update_pressure_hours,
        source_recency_hours=source_recency_hours,
        source_family_count=item.source_family_count,
        timeline_evidence_count=item.timeline_evidence_count,
        recheck_urgency_score=_urgency_score(status),
        status=status,
        reason_codes=reason_codes,
        hard_recheck_flag=item.hard_recheck_flag,
    )


def _row_reason_codes(
    *,
    hours_until_catalyst: Decimal,
    stale_evidence_window_hours: Decimal,
    missing_update_pressure_hours: Decimal,
    source_recency_hours: Decimal,
    source_family_count: Decimal,
    timeline_evidence_count: Decimal,
    hard_recheck_flag: bool,
    config: ResearchEventTimelineEvidenceFreshnessReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if hours_until_catalyst < config.min_watch_catalyst_lead_hours:
        reasons.append(CATALYST_BLOCK_REASON)
    elif hours_until_catalyst < config.min_pass_catalyst_lead_hours:
        reasons.append(CATALYST_WATCH_REASON)

    if stale_evidence_window_hours > config.max_watch_evidence_age_hours:
        reasons.append(STALE_EVIDENCE_BLOCK_REASON)
    elif stale_evidence_window_hours > config.max_pass_evidence_age_hours:
        reasons.append(STALE_EVIDENCE_WATCH_REASON)

    if missing_update_pressure_hours > config.max_watch_missing_update_pressure_hours:
        reasons.append(MISSING_UPDATE_BLOCK_REASON)
    elif missing_update_pressure_hours > config.max_pass_missing_update_pressure_hours:
        reasons.append(MISSING_UPDATE_WATCH_REASON)

    if source_recency_hours > config.max_watch_source_recency_hours:
        reasons.append(SOURCE_RECENCY_BLOCK_REASON)
    elif source_recency_hours > config.max_pass_source_recency_hours:
        reasons.append(SOURCE_RECENCY_WATCH_REASON)

    if (
        source_family_count < config.min_watch_source_family_count
        or timeline_evidence_count < config.min_watch_timeline_evidence_count
    ):
        reasons.append(COVERAGE_BLOCK_REASON)
    elif (
        source_family_count < config.min_pass_source_family_count
        or timeline_evidence_count < config.min_pass_timeline_evidence_count
    ):
        reasons.append(COVERAGE_WATCH_REASON)

    if hard_recheck_flag:
        reasons.append(HARD_RECHECK_REASON)

    if any(reason in BLOCK_REASONS for reason in reasons):
        reasons.append(BLOCK_REASON)
    elif any(reason in WATCH_REASONS for reason in reasons):
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchEventTimelineEvidenceFreshnessReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if all(row.status == "pass" for row in rows):
        return (PASS_REASON,)
    reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    )
    return _normalize_reason_codes("reason_codes", reasons)


def _reason_code_counts(
    rows: tuple[ResearchEventTimelineEvidenceFreshnessReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_inputs(
    value: Iterable[ResearchEventTimelineEvidenceFreshnessReportInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchEventTimelineEvidenceFreshnessReportInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventTimelineEvidenceFreshnessReportInput:
            raise ValueError(
                "inputs must contain "
                "ResearchEventTimelineEvidenceFreshnessReportInput values",
            )
        _require_hard_flags("input", row)
        if row.aggregate_label in seen:
            raise ValueError("aggregate_label values must be unique")
        seen.add(row.aggregate_label)
        if row.latest_evidence_at > generated_at:
            raise ValueError("latest_evidence_at must not be after generated_at")
        if row.latest_source_update_at > generated_at:
            raise ValueError("latest_source_update_at must not be after generated_at")
    return tuple(sorted(rows, key=lambda row: row.aggregate_label))


def _normalize_rows(
    value: Iterable[ResearchEventTimelineEvidenceFreshnessReportRow],
) -> tuple[ResearchEventTimelineEvidenceFreshnessReportRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventTimelineEvidenceFreshnessReportRow:
            raise ValueError(
                "rows must contain ResearchEventTimelineEvidenceFreshnessReportRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and aggregate_public_label")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount],
) -> tuple[ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventTimelineEvidenceFreshnessReportReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda row: REASON_CODE_PRIORITY.index(row.reason_code))):
        raise ValueError("reason_code_counts must be sorted by reason_code priority")
    return counts


def _validate_config(
    config: ResearchEventTimelineEvidenceFreshnessReportConfig,
) -> None:
    if config.min_pass_catalyst_lead_hours <= config.min_watch_catalyst_lead_hours:
        raise ValueError(
            "min_pass_catalyst_lead_hours must be greater than "
            "min_watch_catalyst_lead_hours",
        )
    if config.max_pass_evidence_age_hours >= config.max_watch_evidence_age_hours:
        raise ValueError(
            "max_pass_evidence_age_hours must be less than "
            "max_watch_evidence_age_hours",
        )
    if (
        config.max_pass_missing_update_pressure_hours
        >= config.max_watch_missing_update_pressure_hours
    ):
        raise ValueError(
            "max_pass_missing_update_pressure_hours must be less than "
            "max_watch_missing_update_pressure_hours",
        )
    if config.max_pass_source_recency_hours >= config.max_watch_source_recency_hours:
        raise ValueError(
            "max_pass_source_recency_hours must be less than "
            "max_watch_source_recency_hours",
        )
    if config.min_pass_source_family_count <= config.min_watch_source_family_count:
        raise ValueError(
            "min_pass_source_family_count must be greater than "
            "min_watch_source_family_count",
        )
    if (
        config.min_pass_timeline_evidence_count
        <= config.min_watch_timeline_evidence_count
    ):
        raise ValueError(
            "min_pass_timeline_evidence_count must be greater than "
            "min_watch_timeline_evidence_count",
        )


def _validate_row(row: ResearchEventTimelineEvidenceFreshnessReportRow) -> None:
    status = _status_from_reason_codes(row.reason_codes)
    if row.status != status:
        raise ValueError("row status must match reason_codes")
    expected_urgency = _urgency_score(row.status)
    if row.recheck_urgency_score != expected_urgency:
        raise ValueError("recheck_urgency_score must match status")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only carry pass reason")
    if row.hard_recheck_flag and HARD_RECHECK_REASON not in row.reason_codes:
        raise ValueError("hard_recheck_flag rows must include hard_recheck_flag reason")


def _validate_report(report: ResearchEventTimelineEvidenceFreshnessReport) -> None:
    _require_hard_flags("report", report)
    row_count = len(report.rows)
    if report.aggregate_count != _count(row_count):
        raise ValueError("aggregate_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("report reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report status must match reason_codes")
    expected_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.min_hours_until_catalyst != _min_decimal(
        row.hours_until_catalyst for row in report.rows
    ):
        raise ValueError("min_hours_until_catalyst must match rows")
    if report.max_stale_evidence_window_hours != _max_decimal(
        row.stale_evidence_window_hours for row in report.rows
    ):
        raise ValueError("max_stale_evidence_window_hours must match rows")
    if report.max_missing_update_pressure_hours != _max_decimal(
        row.missing_update_pressure_hours for row in report.rows
    ):
        raise ValueError("max_missing_update_pressure_hours must match rows")
    if report.max_source_recency_hours != _max_decimal(
        row.source_recency_hours for row in report.rows
    ):
        raise ValueError("max_source_recency_hours must match rows")
    if report.average_recheck_urgency_score != _average_decimal(
        row.recheck_urgency_score for row in report.rows
    ):
        raise ValueError("average_recheck_urgency_score must match rows")


def _row_sort_key(
    row: ResearchEventTimelineEvidenceFreshnessReportRow,
) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.recheck_urgency_score,
        row.aggregate_public_label,
    )


def _status_count(
    rows: tuple[ResearchEventTimelineEvidenceFreshnessReportRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if any(reason in BLOCK_REASONS or reason == EMPTY_REASON for reason in reason_codes):
        return "block"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _urgency_score(status: str) -> Decimal:
    if status == "block":
        return ONE
    if status == "watch":
        return WATCH_URGENCY_SCORE
    if status == "pass":
        return ZERO
    raise ValueError("status must be pass, watch, or block")


def _positive_hours_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    if seconds <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (seconds / SECONDS_PER_HOUR).quantize(VALUE_QUANTUM)


def _average_decimal(values: Iterable[Decimal]) -> Decimal | None:
    rows = tuple(values)
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (sum(rows, ZERO) / Decimal(len(rows))).quantize(VALUE_QUANTUM)


def _min_decimal(values: Iterable[Decimal]) -> Decimal | None:
    rows = tuple(values)
    return min(rows) if rows else None


def _max_decimal(values: Iterable[Decimal]) -> Decimal | None:
    rows = tuple(values)
    return max(rows) if rows else None


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_optional_probability(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _require_aggregate_label(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    lowered = value.lower()
    if not all(character.isalnum() or character == "-" for character in value):
        raise ValueError(f"{field_name} must be aggregate-safe")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe fragments")


def _require_public_label(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    if not value.startswith("aggregate-"):
        raise ValueError(f"{field_name} must be redacted aggregate label")
    suffix = value.removeprefix("aggregate-")
    if len(suffix) != 3 or not suffix.isdecimal():
        raise ValueError(f"{field_name} must be redacted aggregate label")


def _require_member(field_name: str, value: str, allowed_values: Iterable[str]) -> None:
    allowed = tuple(allowed_values)
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REASON_CODES)
    deduped = tuple(
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in set(reason_codes)
    )
    if len(deduped) != len(set(reason_codes)):
        raise ValueError(f"{field_name} contains unsupported reason codes")
    return deduped


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, flag_name)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _set_or_validate_public_digest(
    report: ResearchEventTimelineEvidenceFreshnessReport,
) -> None:
    payload = _payload_value(report)
    expected = _digest_payload(payload)
    if report.public_digest == "":
        object.__setattr__(report, "public_digest", expected)
        return
    _require_sha256_digest("public_digest", report.public_digest)
    if report.public_digest != expected:
        raise ValueError("public_digest must match report fields")


def _validate_public_digest(
    report: ResearchEventTimelineEvidenceFreshnessReport,
) -> None:
    _require_sha256_digest("public_digest", report.public_digest)
    expected = _digest_payload(_payload_value(report))
    if report.public_digest != expected:
        raise ValueError("public_digest must match report fields")


def _validate_payload_public_digest(payload: dict[str, Any]) -> None:
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    expected = _digest_payload(payload)
    if public_digest != expected:
        raise ValueError("public_digest must match public payload")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _digest_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["public_digest"] = ""
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in sorted(value.items())}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {value!r}")


def _reject_unsafe_public_payload(context: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_text(context, str(key))
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(context, value)
        return
    if type(value) in (bool, int, float, Decimal) or value is None:
        return
    raise ValueError(f"{context} contains unsupported public payload value")


def _reject_unsafe_public_text(context: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {context}")


def _reject_public_numeric_scalars(value: Any) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_scalars(item)
        return
    if isinstance(value, (Decimal, int, float)) and type(value) is not bool:
        raise ValueError("public payload must use Decimal strings")
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError("public payload contains unsupported value")
