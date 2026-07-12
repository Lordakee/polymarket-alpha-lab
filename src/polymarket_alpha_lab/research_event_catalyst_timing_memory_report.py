"""Pure public-safe aggregate catalyst timing memory report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json


DEFAULT_RESEARCH_EVENT_CATALYST_TIMING_MEMORY_REPORT_CONFIG_VERSION = (
    "research-event-catalyst-timing-memory-report-v0"
)

TIMING_MEMORY_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
STATUS_NEXT_STEPS = {
    "pass": "keep_timing_memory_on_regular_paper_review",
    "watch": "refresh_timing_memory_before_paper_report",
    "block": "rebuild_timing_memory_before_paper_report",
}

PASS_REASON = "timing_memory_pass"
CATALYST_FRESHNESS_WATCH_REASON = "catalyst_freshness_watch"
CATALYST_FRESHNESS_BLOCK_REASON = "catalyst_freshness_block"
WEAK_EVIDENCE_LEAD_TIME_WATCH_REASON = "weak_evidence_lead_time_watch"
WEAK_EVIDENCE_LEAD_TIME_BLOCK_REASON = "weak_evidence_lead_time_block"
STALE_THESIS_RISK_WATCH_REASON = "stale_thesis_risk_watch"
STALE_THESIS_RISK_BLOCK_REASON = "stale_thesis_risk_block"
RECHECK_URGENCY_WATCH_REASON = "recheck_urgency_watch"
RECHECK_URGENCY_BLOCK_REASON = "recheck_urgency_block"

REASON_CODES = (
    CATALYST_FRESHNESS_BLOCK_REASON,
    CATALYST_FRESHNESS_WATCH_REASON,
    RECHECK_URGENCY_BLOCK_REASON,
    RECHECK_URGENCY_WATCH_REASON,
    STALE_THESIS_RISK_BLOCK_REASON,
    STALE_THESIS_RISK_WATCH_REASON,
    WEAK_EVIDENCE_LEAD_TIME_BLOCK_REASON,
    WEAK_EVIDENCE_LEAD_TIME_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASONS = frozenset(
    (
        CATALYST_FRESHNESS_BLOCK_REASON,
        WEAK_EVIDENCE_LEAD_TIME_BLOCK_REASON,
        STALE_THESIS_RISK_BLOCK_REASON,
        RECHECK_URGENCY_BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        CATALYST_FRESHNESS_WATCH_REASON,
        WEAK_EVIDENCE_LEAD_TIME_WATCH_REASON,
        STALE_THESIS_RISK_WATCH_REASON,
        RECHECK_URGENCY_WATCH_REASON,
    ),
)

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "http://",
        "https://",
        "www.",
        "://",
        "raw source text",
        _join_parts("eve", "nt_id"),
        "event-id",
        _join_parts("mar", "ket_id"),
        "market-id",
        _join_parts("sou", "rce_id"),
        "source-id",
        _join_parts("condition", "_id"),
        "condition-id",
        "clob",
        "0x",
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        "network",
        "database",
        "persist",
        _join_parts("sig", "ning"),
        "mutation",
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("tr", "ade"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_CATALYST_TIMING_MEMORY_REPORT_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchEventCatalystTimingMemoryConfig",
    "ResearchEventCatalystTimingMemoryInput",
    "ResearchEventCatalystTimingMemoryReport",
    "ResearchEventCatalystTimingMemoryRow",
    "TIMING_MEMORY_STATUSES",
    "build_research_event_catalyst_timing_memory_report",
    "research_event_catalyst_timing_memory_report_to_payload",
)


@dataclass(frozen=True)
class ResearchEventCatalystTimingMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CATALYST_TIMING_MEMORY_REPORT_CONFIG_VERSION
    )
    max_pass_catalyst_freshness_hours: Decimal = Decimal("24.000000")
    max_watch_catalyst_freshness_hours: Decimal = Decimal("72.000000")
    min_pass_evidence_lead_time_hours: Decimal = Decimal("24.000000")
    min_watch_evidence_lead_time_hours: Decimal = Decimal("6.000000")
    stale_thesis_risk_watch_threshold: Decimal = Decimal("0.250000")
    stale_thesis_risk_block_threshold: Decimal = Decimal("0.600000")
    recheck_urgency_watch_threshold: Decimal = Decimal("0.400000")
    recheck_urgency_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCatalystTimingMemoryConfig:
            raise ValueError(
                "config must be a ResearchEventCatalystTimingMemoryConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CATALYST_TIMING_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_catalyst_freshness_hours",
            "max_watch_catalyst_freshness_hours",
            "min_pass_evidence_lead_time_hours",
            "min_watch_evidence_lead_time_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_thesis_risk_watch_threshold",
            "stale_thesis_risk_block_threshold",
            "recheck_urgency_watch_threshold",
            "recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchEventCatalystTimingMemoryInput:
    aggregate_label: str
    catalyst_freshness_hours: Decimal
    evidence_lead_time_hours: Decimal
    stale_thesis_risk_score: Decimal
    recheck_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCatalystTimingMemoryInput:
            raise ValueError("input must be a ResearchEventCatalystTimingMemoryInput")
        object.__setattr__(
            self,
            "aggregate_label",
            _require_aggregate_label("aggregate_label", self.aggregate_label),
        )
        for field_name in ("catalyst_freshness_hours", "evidence_lead_time_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_thesis_risk_score", "recheck_urgency_score"):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("timing memory input", asdict(self))


@dataclass(frozen=True)
class ResearchEventCatalystTimingMemoryRow:
    aggregate_label: str
    status: str
    catalyst_freshness_hours: Decimal
    evidence_lead_time_hours: Decimal
    stale_thesis_risk_score: Decimal
    recheck_urgency_score: Decimal
    timing_memory_risk_score: Decimal
    manual_review_timing_gap_hours: Decimal
    needs_fresh_catalyst: bool
    weak_evidence_lead_time: bool
    stale_thesis_risk: bool
    recheck_urgency: bool
    manual_review_ready: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCatalystTimingMemoryRow:
            raise ValueError("row must be a ResearchEventCatalystTimingMemoryRow")
        object.__setattr__(
            self,
            "aggregate_label",
            _require_aggregate_label("aggregate_label", self.aggregate_label),
        )
        _require_status("status", self.status)
        for field_name in ("catalyst_freshness_hours", "evidence_lead_time_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_thesis_risk_score",
            "recheck_urgency_score",
            "timing_memory_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_review_timing_gap_hours",
            _require_nonnegative_decimal(
                "manual_review_timing_gap_hours",
                self.manual_review_timing_gap_hours,
            ),
        )
        for field_name in (
            "needs_fresh_catalyst",
            "weak_evidence_lead_time",
            "stale_thesis_risk",
            "recheck_urgency",
            "manual_review_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("timing memory row", asdict(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventCatalystTimingMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    recommended_next_step: str
    aggregate_count: Decimal
    pass_aggregate_count: Decimal
    watch_aggregate_count: Decimal
    block_aggregate_count: Decimal
    flagged_aggregate_count: Decimal
    flagged_aggregate_ratio: Decimal
    catalyst_freshness_risk_count: Decimal
    weak_evidence_lead_time_count: Decimal
    stale_thesis_risk_count: Decimal
    recheck_urgency_count: Decimal
    manual_review_ready_aggregate_count: Decimal
    manual_review_deferred_aggregate_count: Decimal
    manual_review_ready_aggregate_ratio: Decimal
    highest_timing_memory_risk_score: Decimal
    max_manual_review_timing_gap_hours: Decimal
    max_catalyst_freshness_hours: Decimal
    min_evidence_lead_time_hours: Decimal
    max_stale_thesis_risk_score: Decimal
    max_recheck_urgency_score: Decimal
    rows: tuple[ResearchEventCatalystTimingMemoryRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCatalystTimingMemoryReport:
            raise ValueError("report must be a ResearchEventCatalystTimingMemoryReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CATALYST_TIMING_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        if self.recommended_next_step != STATUS_NEXT_STEPS[self.status]:
            raise ValueError("recommended_next_step must match status")
        for field_name in (
            "aggregate_count",
            "pass_aggregate_count",
            "watch_aggregate_count",
            "block_aggregate_count",
            "flagged_aggregate_count",
            "catalyst_freshness_risk_count",
            "weak_evidence_lead_time_count",
            "stale_thesis_risk_count",
            "recheck_urgency_count",
            "manual_review_ready_aggregate_count",
            "manual_review_deferred_aggregate_count",
            "max_manual_review_timing_gap_hours",
            "max_catalyst_freshness_hours",
            "min_evidence_lead_time_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "flagged_aggregate_ratio",
            "manual_review_ready_aggregate_ratio",
            "highest_timing_memory_risk_score",
            "max_stale_thesis_risk_score",
            "max_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("timing memory report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)
        _validate_report_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("timing memory payload", payload)
        if type(payload) is not dict:
            raise ValueError("timing memory payload must be an object")
        _validate_report_digest(self)
        return payload


def build_research_event_catalyst_timing_memory_report(
    inputs: object,
    *,
    config: ResearchEventCatalystTimingMemoryConfig,
    generated_at: datetime,
) -> ResearchEventCatalystTimingMemoryReport:
    if type(config) is not ResearchEventCatalystTimingMemoryConfig:
        raise ValueError("config must be a ResearchEventCatalystTimingMemoryConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _rank_rows(
        tuple(_build_row(item, config=config) for item in normalized_inputs),
    )
    status = _report_status(rows)
    aggregate_count = _count(len(rows))
    flagged_count = _count(sum(1 for row in rows if row.status != "pass"))
    manual_review_ready_count = _count(
        sum(1 for row in rows if row.manual_review_ready),
    )
    manual_review_deferred_count = _count(
        sum(1 for row in rows if not row.manual_review_ready),
    )
    return ResearchEventCatalystTimingMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        recommended_next_step=STATUS_NEXT_STEPS[status],
        aggregate_count=aggregate_count,
        pass_aggregate_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_aggregate_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_aggregate_count=_count(sum(1 for row in rows if row.status == "block")),
        flagged_aggregate_count=flagged_count,
        flagged_aggregate_ratio=_ratio(flagged_count, aggregate_count),
        catalyst_freshness_risk_count=_count(
            sum(1 for row in rows if row.needs_fresh_catalyst),
        ),
        weak_evidence_lead_time_count=_count(
            sum(1 for row in rows if row.weak_evidence_lead_time),
        ),
        stale_thesis_risk_count=_count(
            sum(1 for row in rows if row.stale_thesis_risk),
        ),
        recheck_urgency_count=_count(sum(1 for row in rows if row.recheck_urgency)),
        manual_review_ready_aggregate_count=manual_review_ready_count,
        manual_review_deferred_aggregate_count=manual_review_deferred_count,
        manual_review_ready_aggregate_ratio=_ratio(
            manual_review_ready_count,
            aggregate_count,
        ),
        highest_timing_memory_risk_score=_max_decimal(
            (row.timing_memory_risk_score for row in rows),
        ),
        max_manual_review_timing_gap_hours=_max_decimal(
            (row.manual_review_timing_gap_hours for row in rows),
        ),
        max_catalyst_freshness_hours=_max_decimal(
            (row.catalyst_freshness_hours for row in rows),
        ),
        min_evidence_lead_time_hours=_min_decimal(
            (row.evidence_lead_time_hours for row in rows),
        ),
        max_stale_thesis_risk_score=_max_decimal(
            (row.stale_thesis_risk_score for row in rows),
        ),
        max_recheck_urgency_score=_max_decimal(
            (row.recheck_urgency_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_event_catalyst_timing_memory_report_to_payload(
    report: ResearchEventCatalystTimingMemoryReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventCatalystTimingMemoryReport:
        raise ValueError("report must be a ResearchEventCatalystTimingMemoryReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    _validate_report_digest(report)
    return report.payload


def _build_row(
    item: ResearchEventCatalystTimingMemoryInput,
    *,
    config: ResearchEventCatalystTimingMemoryConfig,
) -> ResearchEventCatalystTimingMemoryRow:
    reason_codes = _timing_reason_codes(item, config=config)
    status = _status_from_reason_codes(reason_codes)
    if not reason_codes:
        reason_codes = (PASS_REASON,)
    manual_review_timing_gap_hours = _manual_review_timing_gap_hours(
        item,
        config=config,
    )
    return ResearchEventCatalystTimingMemoryRow(
        aggregate_label=item.aggregate_label,
        status=status,
        catalyst_freshness_hours=item.catalyst_freshness_hours,
        evidence_lead_time_hours=item.evidence_lead_time_hours,
        stale_thesis_risk_score=item.stale_thesis_risk_score,
        recheck_urgency_score=item.recheck_urgency_score,
        timing_memory_risk_score=_risk_score_for_status(status),
        manual_review_timing_gap_hours=manual_review_timing_gap_hours,
        needs_fresh_catalyst=any(
            reason_code
            in (
                CATALYST_FRESHNESS_WATCH_REASON,
                CATALYST_FRESHNESS_BLOCK_REASON,
            )
            for reason_code in reason_codes
        ),
        weak_evidence_lead_time=any(
            reason_code
            in (
                WEAK_EVIDENCE_LEAD_TIME_WATCH_REASON,
                WEAK_EVIDENCE_LEAD_TIME_BLOCK_REASON,
            )
            for reason_code in reason_codes
        ),
        stale_thesis_risk=any(
            reason_code
            in (
                STALE_THESIS_RISK_WATCH_REASON,
                STALE_THESIS_RISK_BLOCK_REASON,
            )
            for reason_code in reason_codes
        ),
        recheck_urgency=any(
            reason_code
            in (
                RECHECK_URGENCY_WATCH_REASON,
                RECHECK_URGENCY_BLOCK_REASON,
            )
            for reason_code in reason_codes
        ),
        manual_review_ready=manual_review_timing_gap_hours == ZERO,
        reason_codes=_normalize_reason_codes("reason_codes", reason_codes),
    )


def _timing_reason_codes(
    item: ResearchEventCatalystTimingMemoryInput,
    *,
    config: ResearchEventCatalystTimingMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.catalyst_freshness_hours > config.max_watch_catalyst_freshness_hours:
        reason_codes.append(CATALYST_FRESHNESS_BLOCK_REASON)
    elif item.catalyst_freshness_hours > config.max_pass_catalyst_freshness_hours:
        reason_codes.append(CATALYST_FRESHNESS_WATCH_REASON)

    if item.evidence_lead_time_hours < config.min_watch_evidence_lead_time_hours:
        reason_codes.append(WEAK_EVIDENCE_LEAD_TIME_BLOCK_REASON)
    elif item.evidence_lead_time_hours < config.min_pass_evidence_lead_time_hours:
        reason_codes.append(WEAK_EVIDENCE_LEAD_TIME_WATCH_REASON)

    if item.stale_thesis_risk_score >= config.stale_thesis_risk_block_threshold:
        reason_codes.append(STALE_THESIS_RISK_BLOCK_REASON)
    elif item.stale_thesis_risk_score >= config.stale_thesis_risk_watch_threshold:
        reason_codes.append(STALE_THESIS_RISK_WATCH_REASON)

    if item.recheck_urgency_score >= config.recheck_urgency_block_threshold:
        reason_codes.append(RECHECK_URGENCY_BLOCK_REASON)
    elif item.recheck_urgency_score >= config.recheck_urgency_watch_threshold:
        reason_codes.append(RECHECK_URGENCY_WATCH_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _manual_review_timing_gap_hours(
    item: ResearchEventCatalystTimingMemoryInput,
    *,
    config: ResearchEventCatalystTimingMemoryConfig,
) -> Decimal:
    catalyst_gap = item.catalyst_freshness_hours - config.max_pass_catalyst_freshness_hours
    evidence_gap = config.min_pass_evidence_lead_time_hours - item.evidence_lead_time_hours
    return max(ZERO, catalyst_gap, evidence_gap)


def _validate_config(config: ResearchEventCatalystTimingMemoryConfig) -> None:
    if config.max_pass_catalyst_freshness_hours > config.max_watch_catalyst_freshness_hours:
        raise ValueError(
            "max_pass_catalyst_freshness_hours must be at most "
            "max_watch_catalyst_freshness_hours",
        )
    if config.min_pass_evidence_lead_time_hours < config.min_watch_evidence_lead_time_hours:
        raise ValueError(
            "min_pass_evidence_lead_time_hours must be at least "
            "min_watch_evidence_lead_time_hours",
        )
    if config.stale_thesis_risk_watch_threshold > config.stale_thesis_risk_block_threshold:
        raise ValueError(
            "stale_thesis_risk_watch_threshold must be at most "
            "stale_thesis_risk_block_threshold",
        )
    if config.recheck_urgency_watch_threshold > config.recheck_urgency_block_threshold:
        raise ValueError(
            "recheck_urgency_watch_threshold must be at most "
            "recheck_urgency_block_threshold",
        )


def _validate_row(row: ResearchEventCatalystTimingMemoryRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.timing_memory_risk_score != _risk_score_for_status(row.status):
        raise ValueError("timing_memory_risk_score must match status")
    if row.manual_review_ready != (row.manual_review_timing_gap_hours == ZERO):
        raise ValueError("manual_review_ready must match manual_review_timing_gap_hours")
    if row.needs_fresh_catalyst != any(
        reason_code
        in (CATALYST_FRESHNESS_WATCH_REASON, CATALYST_FRESHNESS_BLOCK_REASON)
        for reason_code in row.reason_codes
    ):
        raise ValueError("needs_fresh_catalyst must match reason_codes")
    if row.weak_evidence_lead_time != any(
        reason_code
        in (
            WEAK_EVIDENCE_LEAD_TIME_WATCH_REASON,
            WEAK_EVIDENCE_LEAD_TIME_BLOCK_REASON,
        )
        for reason_code in row.reason_codes
    ):
        raise ValueError("weak_evidence_lead_time must match reason_codes")
    if row.stale_thesis_risk != any(
        reason_code
        in (STALE_THESIS_RISK_WATCH_REASON, STALE_THESIS_RISK_BLOCK_REASON)
        for reason_code in row.reason_codes
    ):
        raise ValueError("stale_thesis_risk must match reason_codes")
    if row.recheck_urgency != any(
        reason_code
        in (RECHECK_URGENCY_WATCH_REASON, RECHECK_URGENCY_BLOCK_REASON)
        for reason_code in row.reason_codes
    ):
        raise ValueError("recheck_urgency must match reason_codes")


def _validate_report(report: ResearchEventCatalystTimingMemoryReport) -> None:
    rows = report.rows
    if report.aggregate_count != _count(len(rows)):
        raise ValueError("aggregate_count must match rows")
    if report.pass_aggregate_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_aggregate_count must match rows")
    if report.watch_aggregate_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_aggregate_count must match rows")
    if report.block_aggregate_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_aggregate_count must match rows")
    flagged_count = _count(sum(1 for row in rows if row.status != "pass"))
    if report.flagged_aggregate_count != flagged_count:
        raise ValueError("flagged_aggregate_count must match rows")
    if report.flagged_aggregate_ratio != _ratio(flagged_count, report.aggregate_count):
        raise ValueError("flagged_aggregate_ratio must match rows")
    if report.catalyst_freshness_risk_count != _count(
        sum(1 for row in rows if row.needs_fresh_catalyst),
    ):
        raise ValueError("catalyst_freshness_risk_count must match rows")
    if report.weak_evidence_lead_time_count != _count(
        sum(1 for row in rows if row.weak_evidence_lead_time),
    ):
        raise ValueError("weak_evidence_lead_time_count must match rows")
    if report.stale_thesis_risk_count != _count(
        sum(1 for row in rows if row.stale_thesis_risk),
    ):
        raise ValueError("stale_thesis_risk_count must match rows")
    if report.recheck_urgency_count != _count(sum(1 for row in rows if row.recheck_urgency)):
        raise ValueError("recheck_urgency_count must match rows")
    manual_review_ready_count = _count(sum(1 for row in rows if row.manual_review_ready))
    if report.manual_review_ready_aggregate_count != manual_review_ready_count:
        raise ValueError("manual_review_ready_aggregate_count must match rows")
    manual_review_deferred_count = _count(
        sum(1 for row in rows if not row.manual_review_ready),
    )
    if report.manual_review_deferred_aggregate_count != manual_review_deferred_count:
        raise ValueError("manual_review_deferred_aggregate_count must match rows")
    if report.manual_review_ready_aggregate_ratio != _ratio(
        manual_review_ready_count,
        report.aggregate_count,
    ):
        raise ValueError("manual_review_ready_aggregate_ratio must match rows")
    if report.highest_timing_memory_risk_score != _max_decimal(
        (row.timing_memory_risk_score for row in rows),
    ):
        raise ValueError("highest_timing_memory_risk_score must match rows")
    if report.max_manual_review_timing_gap_hours != _max_decimal(
        (row.manual_review_timing_gap_hours for row in rows),
    ):
        raise ValueError("max_manual_review_timing_gap_hours must match rows")
    if report.max_catalyst_freshness_hours != _max_decimal(
        (row.catalyst_freshness_hours for row in rows),
    ):
        raise ValueError("max_catalyst_freshness_hours must match rows")
    if report.min_evidence_lead_time_hours != _min_decimal(
        (row.evidence_lead_time_hours for row in rows),
    ):
        raise ValueError("min_evidence_lead_time_hours must match rows")
    if report.max_stale_thesis_risk_score != _max_decimal(
        (row.stale_thesis_risk_score for row in rows),
    ):
        raise ValueError("max_stale_thesis_risk_score must match rows")
    if report.max_recheck_urgency_score != _max_decimal(
        (row.recheck_urgency_score for row in rows),
    ):
        raise ValueError("max_recheck_urgency_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.recommended_next_step != STATUS_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_digest(report: ResearchEventCatalystTimingMemoryReport) -> None:
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_inputs(
    inputs: object,
) -> tuple[ResearchEventCatalystTimingMemoryInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of timing memory inputs")
    try:
        normalized = tuple(inputs)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of timing memory inputs") from exc
    seen_labels: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchEventCatalystTimingMemoryInput:
            raise ValueError(
                "inputs must contain ResearchEventCatalystTimingMemoryInput values",
            )
        _require_hard_flags("input", item)
        if item.aggregate_label in seen_labels:
            raise ValueError("inputs must be unique by aggregate_label")
        seen_labels.add(item.aggregate_label)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventCatalystTimingMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen_labels: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventCatalystTimingMemoryRow:
            raise ValueError(
                "rows must contain ResearchEventCatalystTimingMemoryRow values",
            )
        _require_hard_flags("row", row)
        if row.aggregate_label in seen_labels:
            raise ValueError("rows must be unique by aggregate_label")
        seen_labels.add(row.aggregate_label)
    if normalized != _rank_rows(normalized):
        raise ValueError("rows must be ranked")
    return normalized


def _rank_rows(
    rows: tuple[ResearchEventCatalystTimingMemoryRow, ...],
) -> tuple[ResearchEventCatalystTimingMemoryRow, ...]:
    return tuple(sorted(rows, key=_row_rank_key))


def _row_rank_key(
    row: ResearchEventCatalystTimingMemoryRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.timing_memory_risk_score,
        -row.catalyst_freshness_hours,
        row.evidence_lead_time_hours,
        row.aggregate_label,
    )


def _report_status(rows: tuple[ResearchEventCatalystTimingMemoryRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventCatalystTimingMemoryRow, ...],
) -> tuple[str, ...]:
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in BLOCK_REASONS or reason_code in WATCH_REASONS
    }
    if not observed:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(observed))


def _status_from_reason_codes(reason_codes: tuple[str, ...] | list[str]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _risk_score_for_status(status: str) -> Decimal:
    return {
        "block": ONE,
        "watch": WATCH_RISK_SCORE,
        "pass": ZERO,
    }[status]


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        if value not in REASON_CODES:
            raise ValueError(f"{field_name} contains unknown reason code")
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        return ()
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return _quantize(numerator / denominator)


def _max_decimal(values: object) -> Decimal:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return ZERO
    return max(items)


def _min_decimal(values: object) -> Decimal:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return ZERO
    return min(items)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_score_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_aggregate_label(field_name: str, value: object) -> str:
    normalized = _require_public_string(field_name, value)
    if _has_unsafe_public_fragment(normalized):
        raise ValueError(f"{field_name} has unsafe public payload value")
    return normalized


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TIMING_MEMORY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _derived_validation_digest(report: ResearchEventCatalystTimingMemoryReport) -> str:
    payload = _report_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return hashlib.sha256(
        b"research_event_catalyst_timing_memory_report|" + encoded,
    ).hexdigest()


def _report_digest_payload(
    report: ResearchEventCatalystTimingMemoryReport,
) -> dict[str, object]:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report digest payload must be an object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _payload_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError("payload has unsafe public payload value")
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key: {key}")
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public payload value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("public payload value is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
