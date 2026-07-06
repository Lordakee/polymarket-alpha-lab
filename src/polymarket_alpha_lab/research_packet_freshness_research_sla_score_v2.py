"""Pure Phase 1 research packet freshness SLA score report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_FRESHNESS_RESEARCH_SLA_SCORE_V2_CONFIG_VERSION = (
    "research-packet-freshness-research-sla-score-v2"
)
RESEARCH_PACKET_FRESHNESS_RESEARCH_SLA_SCORE_V2_STATUSES = (
    "pass",
    "watch",
    "blocked",
)
SOURCE_PRIORITIES = ("standard", "high", "critical")

FRESH_SOURCE_REASON = "fresh_source"
OVERDUE_SOURCE_REASON = "source_overdue"
FRESHNESS_PENALTY_REASON = "freshness_penalty_applied"
PRIORITY_ESCALATED_REASON = "priority_overdue_escalation"
REPORT_PASS_REASON = "freshness_sla_clear"
REPORT_WATCH_REASON = "freshness_sla_watch"
REPORT_BLOCKED_REASON = "freshness_sla_blocked"
NO_RESEARCH_SOURCES_REASON = "no_research_sources"

ROW_REASON_CODES = (
    OVERDUE_SOURCE_REASON,
    FRESHNESS_PENALTY_REASON,
    PRIORITY_ESCALATED_REASON,
    FRESH_SOURCE_REASON,
)
REPORT_REASON_CODES = (
    REPORT_BLOCKED_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
    NO_RESEARCH_SOURCES_REASON,
    OVERDUE_SOURCE_REASON,
    FRESHNESS_PENALTY_REASON,
    PRIORITY_ESCALATED_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_SECONDS = Decimal("0.000000")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STANDARD_RESEARCH_SLA_SECONDS = Decimal("86400.000000")
HIGH_RESEARCH_SLA_SECONDS = Decimal("43200.000000")
CRITICAL_RESEARCH_SLA_SECONDS = Decimal("21600.000000")
OVERDUE_BASE_PENALTY_SCORE = Decimal("0.350000")
HIGH_PRIORITY_ESCALATION_SCORE = Decimal("0.075000")
CRITICAL_PRIORITY_ESCALATION_SCORE = Decimal("0.150000")

UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class ResearchPacketFreshnessResearchSlaScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_FRESHNESS_RESEARCH_SLA_SCORE_V2_CONFIG_VERSION
    )
    standard_research_sla_seconds: Decimal = STANDARD_RESEARCH_SLA_SECONDS
    high_research_sla_seconds: Decimal = HIGH_RESEARCH_SLA_SECONDS
    critical_research_sla_seconds: Decimal = CRITICAL_RESEARCH_SLA_SECONDS
    watch_score_threshold: Decimal = Decimal("0.250000")
    block_score_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "standard_research_sla_seconds",
            "high_research_sla_seconds",
            "critical_research_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_score_threshold", "block_score_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold > self.block_score_threshold:
            raise ValueError(
                "watch_score_threshold must be less than or equal to "
                "block_score_threshold",
            )
        if self.critical_research_sla_seconds > self.high_research_sla_seconds:
            raise ValueError(
                "critical_research_sla_seconds must be less than or equal to "
                "high_research_sla_seconds",
            )
        if self.high_research_sla_seconds > self.standard_research_sla_seconds:
            raise ValueError(
                "high_research_sla_seconds must be less than or equal to "
                "standard_research_sla_seconds",
            )
        require_paper_only_flags("freshness research SLA score config", self)


@dataclass(frozen=True)
class ResearchPacketFreshnessResearchSlaScoreV2Source:
    packet_id: str
    source_id: str
    research_topic_id: str
    source_priority: str
    source_label: str
    last_researched_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "source_id",
            "research_topic_id",
            "source_label",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_priority",
            _require_source_priority("source_priority", self.source_priority),
        )
        object.__setattr__(
            self,
            "last_researched_at",
            _as_utc("last_researched_at", self.last_researched_at),
        )
        require_paper_only_flags("freshness research SLA score source", self)


@dataclass(frozen=True)
class ResearchPacketFreshnessResearchSlaScoreV2Row:
    packet_id: str
    source_id: str
    research_topic_id: str
    source_priority: str
    source_label: str
    last_researched_at: datetime
    source_age_seconds: Decimal
    research_sla_seconds: Decimal
    seconds_over_sla: Decimal
    overdue_ratio: Decimal
    freshness_penalty_score: Decimal
    priority_escalation_score: Decimal
    freshness_sla_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "source_id",
            "research_topic_id",
            "source_label",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_priority",
            _require_source_priority("source_priority", self.source_priority),
        )
        object.__setattr__(
            self,
            "last_researched_at",
            _as_utc("last_researched_at", self.last_researched_at),
        )
        for field_name in (
            "source_age_seconds",
            "research_sla_seconds",
            "seconds_over_sla",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overdue_ratio",
            "freshness_penalty_score",
            "priority_escalation_score",
            "freshness_sla_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _row_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match row fields")
        _reject_unsafe_public_payload("freshness research SLA score row", _json_payload(self))
        require_paper_only_flags("freshness research SLA score row", self)


@dataclass(frozen=True)
class ResearchPacketFreshnessResearchSlaScoreV2Report:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    overdue_source_count: Decimal
    priority_escalated_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    average_freshness_sla_score: Decimal
    highest_freshness_sla_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "source_count",
            "overdue_source_count",
            "priority_escalated_count",
            "blocked_count",
            "watch_count",
            "pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_freshness_sla_score",
            "highest_freshness_sla_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "source_rows",
            _normalize_source_rows(self.source_rows),
        )
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report fields")
        _reject_unsafe_public_payload(
            "freshness research SLA score report",
            _json_payload(self),
        )
        require_paper_only_flags("freshness research SLA score report", self)


def build_research_packet_freshness_research_sla_score_v2_report(
    sources: list[ResearchPacketFreshnessResearchSlaScoreV2Source]
    | tuple[ResearchPacketFreshnessResearchSlaScoreV2Source, ...],
    *,
    config: ResearchPacketFreshnessResearchSlaScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketFreshnessResearchSlaScoreV2Report:
    if type(config) is not ResearchPacketFreshnessResearchSlaScoreV2Config:
        raise ValueError(
            "config must be a ResearchPacketFreshnessResearchSlaScoreV2Config",
        )
    require_paper_only_flags("freshness research SLA score config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_for_source(source, config, generated_at_utc) for source in _normalize_sources(sources)),
            key=_row_sort_key,
        ),
    )
    return ResearchPacketFreshnessResearchSlaScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_count(len(rows)),
        overdue_source_count=_overdue_source_count(rows),
        priority_escalated_count=_priority_escalated_count(rows),
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        average_freshness_sla_score=_average_freshness_sla_score(rows),
        highest_freshness_sla_score=_highest_freshness_sla_score(rows),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        source_rows=rows,
    )


def research_packet_freshness_research_sla_score_v2_payload(
    value: ResearchPacketFreshnessResearchSlaScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchPacketFreshnessResearchSlaScoreV2Report:
        require_paper_only_flags("freshness research SLA score report", value)
        _validate_report(value)
        payload = _json_payload(value)
    elif type(value) is dict:
        payload = _json_payload(value)
    else:
        raise ValueError(
            "value must be a ResearchPacketFreshnessResearchSlaScoreV2Report "
            "or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("freshness research SLA score payload must be a JSON object")
    validate_research_packet_freshness_research_sla_score_v2_public_payload(payload)
    return payload


def validate_research_packet_freshness_research_sla_score_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_values("public payload", payload)
    _require_public_payload_flags(payload, "public payload")
    source_rows = payload.get("source_rows")
    if type(source_rows) is not list:
        raise ValueError("source_rows must be a list in public payload")
    for index, row in enumerate(source_rows):
        if type(row) is not dict:
            raise ValueError("source_rows must contain JSON objects")
        _require_public_payload_flags(row, f"public payload source row {index}")
        _validate_row_public_payload_digest(row)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_report_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_source(
    source: ResearchPacketFreshnessResearchSlaScoreV2Source,
    config: ResearchPacketFreshnessResearchSlaScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketFreshnessResearchSlaScoreV2Row:
    source_age_seconds = _seconds_between(source.last_researched_at, generated_at)
    research_sla_seconds = _sla_seconds_for_priority(source.source_priority, config)
    seconds_over_sla = _seconds_over_sla(source_age_seconds, research_sla_seconds)
    overdue_ratio = _overdue_ratio(seconds_over_sla, research_sla_seconds)
    freshness_penalty_score = _freshness_penalty_score(overdue_ratio)
    priority_escalation_score = _priority_escalation_score(
        source.source_priority,
        seconds_over_sla,
    )
    freshness_sla_score = _freshness_sla_score(
        freshness_penalty_score,
        priority_escalation_score,
    )
    reason_codes = _row_reason_codes(
        seconds_over_sla,
        priority_escalation_score,
    )
    return ResearchPacketFreshnessResearchSlaScoreV2Row(
        packet_id=source.packet_id,
        source_id=source.source_id,
        research_topic_id=source.research_topic_id,
        source_priority=source.source_priority,
        source_label=source.source_label,
        last_researched_at=source.last_researched_at,
        source_age_seconds=source_age_seconds,
        research_sla_seconds=research_sla_seconds,
        seconds_over_sla=seconds_over_sla,
        overdue_ratio=overdue_ratio,
        freshness_penalty_score=freshness_penalty_score,
        priority_escalation_score=priority_escalation_score,
        freshness_sla_score=freshness_sla_score,
        row_status=_row_status(
            source.source_priority,
            freshness_sla_score,
            seconds_over_sla,
            config,
        ),
        reason_codes=reason_codes,
    )


def _sla_seconds_for_priority(
    source_priority: str,
    config: ResearchPacketFreshnessResearchSlaScoreV2Config,
) -> Decimal:
    if source_priority == "critical":
        return config.critical_research_sla_seconds
    if source_priority == "high":
        return config.high_research_sla_seconds
    return config.standard_research_sla_seconds


def _seconds_over_sla(source_age_seconds: Decimal, research_sla_seconds: Decimal) -> Decimal:
    if source_age_seconds <= research_sla_seconds:
        return ZERO_SECONDS
    return (source_age_seconds - research_sla_seconds).quantize(SECONDS_QUANTUM)


def _overdue_ratio(seconds_over_sla: Decimal, research_sla_seconds: Decimal) -> Decimal:
    if seconds_over_sla == ZERO_SECONDS:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        ratio = seconds_over_sla / research_sla_seconds
        if ratio > ONE_RATIO:
            ratio = ONE_RATIO
        return ratio.quantize(RATIO_QUANTUM)


def _freshness_penalty_score(overdue_ratio: Decimal) -> Decimal:
    if overdue_ratio == ZERO_RATIO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        score = OVERDUE_BASE_PENALTY_SCORE + (
            overdue_ratio * (ONE_RATIO - OVERDUE_BASE_PENALTY_SCORE)
        )
        if score > ONE_RATIO:
            score = ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _priority_escalation_score(
    source_priority: str,
    seconds_over_sla: Decimal,
) -> Decimal:
    if seconds_over_sla == ZERO_SECONDS:
        return ZERO_RATIO
    if source_priority == "critical":
        return CRITICAL_PRIORITY_ESCALATION_SCORE
    if source_priority == "high":
        return HIGH_PRIORITY_ESCALATION_SCORE
    return ZERO_RATIO


def _freshness_sla_score(
    freshness_penalty_score: Decimal,
    priority_escalation_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = freshness_penalty_score + priority_escalation_score
        if score > ONE_RATIO:
            score = ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _row_reason_codes(
    seconds_over_sla: Decimal,
    priority_escalation_score: Decimal,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if seconds_over_sla == ZERO_SECONDS:
        codes.add(FRESH_SOURCE_REASON)
    else:
        codes.add(OVERDUE_SOURCE_REASON)
        codes.add(FRESHNESS_PENALTY_REASON)
    if priority_escalation_score > ZERO_RATIO:
        codes.add(PRIORITY_ESCALATED_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _row_status(
    source_priority: str,
    freshness_sla_score: Decimal,
    seconds_over_sla: Decimal,
    config: ResearchPacketFreshnessResearchSlaScoreV2Config,
) -> str:
    if source_priority == "critical" and seconds_over_sla > ZERO_SECONDS:
        return "blocked"
    if freshness_sla_score >= config.block_score_threshold:
        return "blocked"
    if freshness_sla_score >= config.watch_score_threshold:
        return "watch"
    if seconds_over_sla > ZERO_SECONDS:
        return "watch"
    return "pass"


def _validate_row(row: ResearchPacketFreshnessResearchSlaScoreV2Row) -> None:
    expected_seconds_over_sla = _seconds_over_sla(
        row.source_age_seconds,
        row.research_sla_seconds,
    )
    expected_overdue_ratio = _overdue_ratio(
        expected_seconds_over_sla,
        row.research_sla_seconds,
    )
    expected_penalty_score = _freshness_penalty_score(expected_overdue_ratio)
    expected_priority_escalation_score = _priority_escalation_score(
        row.source_priority,
        expected_seconds_over_sla,
    )
    expected_freshness_sla_score = _freshness_sla_score(
        expected_penalty_score,
        expected_priority_escalation_score,
    )
    expected_reason_codes = _row_reason_codes(
        expected_seconds_over_sla,
        expected_priority_escalation_score,
    )
    if row.seconds_over_sla != expected_seconds_over_sla:
        raise ValueError("seconds_over_sla must match source age and SLA")
    if row.overdue_ratio != expected_overdue_ratio:
        raise ValueError("overdue_ratio must match overdue seconds and SLA")
    if row.freshness_penalty_score != expected_penalty_score:
        raise ValueError("freshness_penalty_score must match overdue ratio")
    if row.priority_escalation_score != expected_priority_escalation_score:
        raise ValueError("priority_escalation_score must match source priority")
    if row.freshness_sla_score != expected_freshness_sla_score:
        raise ValueError("freshness_sla_score must match row score components")
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row freshness state")
    if row.row_status == "pass" and row.seconds_over_sla > ZERO_SECONDS:
        raise ValueError("row_status cannot pass with overdue seconds")
    if row.row_status == "blocked" and row.freshness_sla_score < ZERO_RATIO:
        raise ValueError("row_status must match freshness SLA score")


def _validate_report(report: ResearchPacketFreshnessResearchSlaScoreV2Report) -> None:
    if report.source_count != _count(len(report.source_rows)):
        raise ValueError("source_count must match source_rows")
    if report.overdue_source_count != _overdue_source_count(report.source_rows):
        raise ValueError("overdue_source_count must match source_rows")
    if report.priority_escalated_count != _priority_escalated_count(report.source_rows):
        raise ValueError("priority_escalated_count must match source_rows")
    if report.blocked_count != _status_count(report.source_rows, "blocked"):
        raise ValueError("blocked_count must match source_rows")
    if report.watch_count != _status_count(report.source_rows, "watch"):
        raise ValueError("watch_count must match source_rows")
    if report.pass_count != _status_count(report.source_rows, "pass"):
        raise ValueError("pass_count must match source_rows")
    if report.average_freshness_sla_score != _average_freshness_sla_score(
        report.source_rows,
    ):
        raise ValueError("average_freshness_sla_score must match source_rows")
    if report.highest_freshness_sla_score != _highest_freshness_sla_score(
        report.source_rows,
    ):
        raise ValueError("highest_freshness_sla_score must match source_rows")
    if report.report_status != _report_status(report.source_rows):
        raise ValueError("report_status must match source_rows")
    if report.reason_codes != _report_reason_codes(report.source_rows):
        raise ValueError("reason_codes must match source_rows")
    if report.source_rows != tuple(sorted(report.source_rows, key=_row_sort_key)):
        raise ValueError("source_rows must use deterministic sequence")


def _row_sort_key(
    row: ResearchPacketFreshnessResearchSlaScoreV2Row,
) -> tuple[int, Decimal, datetime, str, str]:
    return (
        -_status_rank(row.row_status),
        -row.freshness_sla_score,
        row.last_researched_at,
        row.packet_id,
        row.source_id,
    )


def _status_rank(status: str) -> int:
    if status == "blocked":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count(len(tuple(row for row in source_rows if row.row_status == status)))


def _overdue_source_count(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
) -> Decimal:
    return _count(
        len(tuple(row for row in source_rows if row.seconds_over_sla > ZERO_SECONDS)),
    )


def _priority_escalated_count(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
) -> Decimal:
    return _count(
        len(
            tuple(
                row
                for row in source_rows
                if row.priority_escalation_score > ZERO_RATIO
            ),
        ),
    )


def _average_freshness_sla_score(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
) -> Decimal:
    if not source_rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.freshness_sla_score for row in source_rows), ZERO_RATIO)
            / Decimal(len(source_rows))
        ).quantize(RATIO_QUANTUM)


def _highest_freshness_sla_score(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
) -> Decimal:
    if not source_rows:
        return ZERO_RATIO
    return max(row.freshness_sla_score for row in source_rows).quantize(RATIO_QUANTUM)


def _report_status(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
) -> str:
    if not source_rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in source_rows):
        return "blocked"
    if any(row.row_status == "watch" for row in source_rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    source_rows: tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...],
) -> tuple[str, ...]:
    if not source_rows:
        return (NO_RESEARCH_SOURCES_REASON,)
    codes = {
        code
        for row in source_rows
        for code in row.reason_codes
        if code != FRESH_SOURCE_REASON
    }
    report_status = _report_status(source_rows)
    if report_status == "blocked":
        codes.add(REPORT_BLOCKED_REASON)
    elif report_status == "watch":
        codes.add(REPORT_WATCH_REASON)
    if not codes:
        codes.add(REPORT_PASS_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _normalize_sources(
    value: object,
) -> tuple[ResearchPacketFreshnessResearchSlaScoreV2Source, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketFreshnessResearchSlaScoreV2Source:
            raise ValueError(
                "sources must contain "
                "ResearchPacketFreshnessResearchSlaScoreV2Source values",
            )
        require_paper_only_flags("freshness research SLA score source", row)
        key = (row.packet_id, row.source_id)
        if key in seen:
            raise ValueError("sources must not contain duplicate packet/source pairs")
        seen.add(key)
    return rows


def _normalize_source_rows(
    value: object,
) -> tuple[ResearchPacketFreshnessResearchSlaScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("source_rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPacketFreshnessResearchSlaScoreV2Row:
            raise ValueError(
                "source_rows must contain "
                "ResearchPacketFreshnessResearchSlaScoreV2Row values",
            )
        _validate_row(row)
        require_paper_only_flags("freshness research SLA score row", row)
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    expected = tuple(code for code in allowed_reason_codes if code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return value.quantize(SECONDS_QUANTUM)


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(SECONDS_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _seconds_between(started_at: datetime, ended_at: datetime) -> Decimal:
    delta = ended_at - started_at
    if delta.days < 0:
        raise ValueError("generated_at must be greater than or equal to last_researched_at")
    with localcontext(DECIMAL_CONTEXT):
        total = Decimal(delta.days * 86400 + delta.seconds) + (
            Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        )
        return total.quantize(SECONDS_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_source_priority(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in SOURCE_PRIORITIES:
        raise ValueError(f"{field_name} must be standard, high, or critical")
    return value


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_PACKET_FRESHNESS_RESEARCH_SLA_SCORE_V2_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            if any(term in key.lower() for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_public_numeric_values(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must serialize numeric values as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(label, item)


def _require_public_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in {label}")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _row_derived_validation_digest(
    row: ResearchPacketFreshnessResearchSlaScoreV2Row,
) -> str:
    return _public_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: ResearchPacketFreshnessResearchSlaScoreV2Report,
) -> str:
    return _public_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(
    row: ResearchPacketFreshnessResearchSlaScoreV2Row,
) -> dict[str, Any]:
    payload = _json_payload(row)
    if type(payload) is not dict:
        raise ValueError("row digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: ResearchPacketFreshnessResearchSlaScoreV2Report,
) -> dict[str, Any]:
    payload = _json_payload(report)
    if type(payload) is not dict:
        raise ValueError("report digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _validate_row_public_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    if digest_value != _public_digest(digest_payload):
        raise ValueError("derived_validation_digest must match row public payload")


def _public_report_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _public_digest(digest_payload)


def _public_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_public_numeric_values("digest payload", payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_payload(value: Any) -> Any:
    return json_ready_no_floats(value)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_FRESHNESS_RESEARCH_SLA_SCORE_V2_CONFIG_VERSION",
    "RESEARCH_PACKET_FRESHNESS_RESEARCH_SLA_SCORE_V2_STATUSES",
    "SOURCE_PRIORITIES",
    "FRESH_SOURCE_REASON",
    "OVERDUE_SOURCE_REASON",
    "FRESHNESS_PENALTY_REASON",
    "PRIORITY_ESCALATED_REASON",
    "REPORT_PASS_REASON",
    "REPORT_WATCH_REASON",
    "REPORT_BLOCKED_REASON",
    "NO_RESEARCH_SOURCES_REASON",
    "ResearchPacketFreshnessResearchSlaScoreV2Config",
    "ResearchPacketFreshnessResearchSlaScoreV2Source",
    "ResearchPacketFreshnessResearchSlaScoreV2Row",
    "ResearchPacketFreshnessResearchSlaScoreV2Report",
    "build_research_packet_freshness_research_sla_score_v2_report",
    "research_packet_freshness_research_sla_score_v2_payload",
    "validate_research_packet_freshness_research_sla_score_v2_public_payload",
)
