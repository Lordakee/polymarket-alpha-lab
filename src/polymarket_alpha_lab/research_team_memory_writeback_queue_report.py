"""Pure planning report for research-team memory writeback queues.

Callers pass already-loaded writeback candidates. This module does not connect
to any store, perform network requests, or submit trading actions; it only
classifies local writeback readiness and emits deidentified planning payloads.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_WRITEBACK_QUEUE_CONFIG_VERSION",
    "ResearchTeamMemoryWritebackCandidate",
    "ResearchTeamMemoryWritebackQueueConfig",
    "ResearchTeamMemoryWritebackQueueReport",
    "ResearchTeamMemoryWritebackQueueRow",
    "build_research_team_memory_writeback_queue_report",
    "research_team_memory_writeback_queue_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_WRITEBACK_QUEUE_CONFIG_VERSION = (
    "research-team-memory-writeback-queue-v0"
)

STATUSES = ("pass", "watch", "block")
CONFLICT_RESOLUTION_STATES = ("not_needed", "resolved", "needs_review", "blocked")
LOCAL_STORE_PLAN_STATES = ("ready", "needs_review", "blocked")

PASS_REASON = "memory_writeback_queue_pass"
EMPTY_REASON = "memory_writeback_queue_empty"
POSTMORTEM_SUMMARY_WATCH_REASON = "postmortem_summary_watch"
STALE_POSTMORTEM_WATCH_REASON = "stale_postmortem_watch"
STALE_POSTMORTEM_BLOCK_REASON = "stale_postmortem_block"
DEIDENTIFICATION_WATCH_REASON = "deidentification_watch"
DEIDENTIFICATION_BLOCK_REASON = "deidentification_block"
CONFLICT_RESOLUTION_WATCH_REASON = "conflict_resolution_watch"
CONFLICT_RESOLUTION_BLOCK_REASON = "conflict_resolution_block"
CALIBRATION_UPDATE_WATCH_REASON = "calibration_update_watch"
LOCAL_STORE_PLAN_WATCH_REASON = "local_store_plan_watch"
LOCAL_STORE_PLAN_BLOCK_REASON = "local_store_plan_block"
OWNER_REVIEW_WATCH_REASON = "owner_review_watch"

ROW_REASON_PRIORITY = (
    DEIDENTIFICATION_BLOCK_REASON,
    CONFLICT_RESOLUTION_BLOCK_REASON,
    STALE_POSTMORTEM_BLOCK_REASON,
    LOCAL_STORE_PLAN_BLOCK_REASON,
    POSTMORTEM_SUMMARY_WATCH_REASON,
    STALE_POSTMORTEM_WATCH_REASON,
    DEIDENTIFICATION_WATCH_REASON,
    CONFLICT_RESOLUTION_WATCH_REASON,
    CALIBRATION_UPDATE_WATCH_REASON,
    LOCAL_STORE_PLAN_WATCH_REASON,
    OWNER_REVIEW_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_PRIORITY = (
    DEIDENTIFICATION_BLOCK_REASON,
    CONFLICT_RESOLUTION_BLOCK_REASON,
    STALE_POSTMORTEM_BLOCK_REASON,
    LOCAL_STORE_PLAN_BLOCK_REASON,
    POSTMORTEM_SUMMARY_WATCH_REASON,
    STALE_POSTMORTEM_WATCH_REASON,
    DEIDENTIFICATION_WATCH_REASON,
    CONFLICT_RESOLUTION_WATCH_REASON,
    CALIBRATION_UPDATE_WATCH_REASON,
    LOCAL_STORE_PLAN_WATCH_REASON,
    OWNER_REVIEW_WATCH_REASON,
    PASS_REASON,
    EMPTY_REASON,
)
BLOCK_REASONS = frozenset(
    (
        DEIDENTIFICATION_BLOCK_REASON,
        CONFLICT_RESOLUTION_BLOCK_REASON,
        STALE_POSTMORTEM_BLOCK_REASON,
        LOCAL_STORE_PLAN_BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        POSTMORTEM_SUMMARY_WATCH_REASON,
        STALE_POSTMORTEM_WATCH_REASON,
        DEIDENTIFICATION_WATCH_REASON,
        CONFLICT_RESOLUTION_WATCH_REASON,
        CALIBRATION_UPDATE_WATCH_REASON,
        LOCAL_STORE_PLAN_WATCH_REASON,
        OWNER_REVIEW_WATCH_REASON,
    ),
)

SUMMARY_INCLUDE_PLAN = "include_deidentified_postmortem_summary"
SUMMARY_REVISE_PLAN = "revise_postmortem_summary"
SUMMARY_BLOCK_PLAN = "block_until_postmortem_summary_refreshed"
DEID_PASS_PLAN = "use_redacted_markers_only"
DEID_WATCH_PLAN = "strengthen_deidentification"
DEID_BLOCK_PLAN = "block_until_redaction_passes"
CONFLICT_APPLY_PLAN = "apply_resolved_memory"
CONFLICT_NONE_PLAN = "no_conflict_resolution_needed"
CONFLICT_REVIEW_PLAN = "queue_conflict_owner_review"
CONFLICT_BLOCK_PLAN = "hold_until_conflict_owner_resolution"
CALIBRATION_APPLY_PLAN = "apply_calibration_update"
CALIBRATION_REVIEW_PLAN = "queue_calibration_review"
LOCAL_STORE_READY_PLAN = "prepare_local_supabase_postgres_write_plan"
LOCAL_STORE_REVIEW_PLAN = "hold_local_supabase_postgres_plan_for_review"
LOCAL_STORE_BLOCK_PLAN = "do_not_prepare_local_store_plan"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "dsn",
    "table",
    "token",
    "private_key",
    "raw_source",
    "source_reference",
    "source_bundle_reference",
    "source_url",
    "source_text",
    "market_reference",
    "market_id",
    "market_slug",
    "market_question",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "postgres:",
    "postgresql:",
    "dsn",
    "table",
    "token",
    "private_key",
    "wallet",
    "auth",
    "raw source",
    "raw/source",
    "raw_source",
    "source_reference",
    "source_bundle_reference",
    "market-id",
    "market id",
    "market_reference",
    "market_id",
    "slug",
    "question",
    "polymarket-market",
)


@dataclass(frozen=True)
class ResearchTeamMemoryWritebackQueueConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_WRITEBACK_QUEUE_CONFIG_VERSION
    min_postmortem_summary_score: Decimal = Decimal("0.750000")
    min_deidentification_pass_score: Decimal = Decimal("0.900000")
    min_deidentification_block_score: Decimal = Decimal("0.500000")
    min_calibration_update_score: Decimal = Decimal("0.700000")
    stale_postmortem_watch_seconds: Decimal = Decimal("2592000.000000")
    stale_postmortem_block_seconds: Decimal = Decimal("7776000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_WRITEBACK_QUEUE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_postmortem_summary_score",
            "min_deidentification_pass_score",
            "min_deidentification_block_score",
            "min_calibration_update_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_deidentification_block_score >= self.min_deidentification_pass_score:
            raise ValueError(
                "min_deidentification_block_score must be less than "
                "min_deidentification_pass_score",
            )
        for field_name in (
            "stale_postmortem_watch_seconds",
            "stale_postmortem_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_postmortem_block_seconds <= self.stale_postmortem_watch_seconds:
            raise ValueError(
                "stale_postmortem_block_seconds must be greater than "
                "stale_postmortem_watch_seconds",
            )
        require_paper_only_flags("memory writeback queue config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryWritebackCandidate:
    writeback_reference: str
    source_bundle_reference: str
    scope_reference: str
    team_domain: str
    memory_topic: str
    postmortem_summary: str
    postmortem_completed_at: datetime
    postmortem_summary_score: Decimal
    deidentification_score: Decimal
    conflict_resolution_state: str
    calibration_update_score: Decimal
    local_store_plan_state: str
    owner_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_private_reference("writeback_reference", self.writeback_reference)
        _require_private_reference(
            "source_bundle_reference",
            self.source_bundle_reference,
        )
        _require_private_reference("scope_reference", self.scope_reference)
        object.__setattr__(
            self,
            "writeback_reference",
            _redacted_marker("writeback_marker_", self.writeback_reference),
        )
        object.__setattr__(
            self,
            "source_bundle_reference",
            _redacted_marker("evidence_marker_", self.source_bundle_reference),
        )
        object.__setattr__(
            self,
            "scope_reference",
            _redacted_marker("scope_marker_", self.scope_reference),
        )
        _require_public_text("team_domain", self.team_domain)
        _require_public_text("memory_topic", self.memory_topic)
        _require_public_text("postmortem_summary", self.postmortem_summary)
        object.__setattr__(
            self,
            "postmortem_completed_at",
            _as_utc("postmortem_completed_at", self.postmortem_completed_at),
        )
        for field_name in (
            "postmortem_summary_score",
            "deidentification_score",
            "calibration_update_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "conflict_resolution_state",
            self.conflict_resolution_state,
            CONFLICT_RESOLUTION_STATES,
        )
        _require_choice(
            "local_store_plan_state",
            self.local_store_plan_state,
            LOCAL_STORE_PLAN_STATES,
        )
        _require_bool("owner_review_required", self.owner_review_required)
        require_paper_only_flags("memory writeback candidate", self)


@dataclass(frozen=True)
class ResearchTeamMemoryWritebackQueueRow:
    writeback_marker: str
    evidence_bundle_marker: str
    scope_marker: str
    team_domain: str
    memory_topic: str
    postmortem_summary: str
    postmortem_completed_at: datetime
    postmortem_age_seconds: Decimal
    postmortem_summary_score: Decimal
    postmortem_summary_plan: str
    deidentification_score: Decimal
    deidentification_plan: str
    conflict_resolution_state: str
    conflict_resolution_plan: str
    calibration_update_score: Decimal
    calibration_update_plan: str
    local_store_plan_state: str
    local_store_write_plan: str
    owner_review_required: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "writeback_marker",
            "evidence_bundle_marker",
            "scope_marker",
            "team_domain",
            "memory_topic",
            "postmortem_summary",
            "postmortem_summary_plan",
            "deidentification_plan",
            "conflict_resolution_plan",
            "calibration_update_plan",
            "local_store_write_plan",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "postmortem_completed_at",
            _as_utc("postmortem_completed_at", self.postmortem_completed_at),
        )
        object.__setattr__(
            self,
            "postmortem_age_seconds",
            _require_nonnegative_decimal(
                "postmortem_age_seconds",
                self.postmortem_age_seconds,
            ),
        )
        for field_name in (
            "postmortem_summary_score",
            "deidentification_score",
            "calibration_update_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "conflict_resolution_state",
            self.conflict_resolution_state,
            CONFLICT_RESOLUTION_STATES,
        )
        _require_choice(
            "local_store_plan_state",
            self.local_store_plan_state,
            LOCAL_STORE_PLAN_STATES,
        )
        _require_bool("owner_review_required", self.owner_review_required)
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_PRIORITY,
            ),
        )
        require_paper_only_flags("memory writeback queue row", self)
        _reject_unsafe_public_payload("memory writeback queue row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamMemoryWritebackQueueReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    owner_review_required_count: Decimal
    deidentification_watch_count: Decimal
    deidentification_block_count: Decimal
    local_store_ready_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamMemoryWritebackQueueRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_WRITEBACK_QUEUE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "owner_review_required_count",
            "deidentification_watch_count",
            "deidentification_block_count",
            "local_store_ready_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_PRIORITY,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("memory writeback queue report", self)
        _reject_unsafe_public_payload("memory writeback queue report", self)
        _validate_report(self)


def build_research_team_memory_writeback_queue_report(
    candidates: Iterable[ResearchTeamMemoryWritebackCandidate],
    *,
    config: ResearchTeamMemoryWritebackQueueConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryWritebackQueueReport:
    if type(config) is not ResearchTeamMemoryWritebackQueueConfig:
        raise ValueError("config must be a ResearchTeamMemoryWritebackQueueConfig")
    require_paper_only_flags("memory writeback queue config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for item in normalized_candidates:
        if item.postmortem_completed_at > generated_at_utc:
            raise ValueError("postmortem_completed_at must be <= generated_at")

    rows = _sort_rows(
        tuple(
            _row_from_candidate(item, config=config, generated_at=generated_at_utc)
            for item in normalized_candidates
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamMemoryWritebackQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        owner_review_required_count=_count(
            sum(1 for row in rows if row.owner_review_required),
        ),
        deidentification_watch_count=_count(
            _reason_count(rows, DEIDENTIFICATION_WATCH_REASON),
        ),
        deidentification_block_count=_count(
            _reason_count(rows, DEIDENTIFICATION_BLOCK_REASON),
        ),
        local_store_ready_count=_count(
            sum(1 for row in rows if row.local_store_plan_state == "ready"),
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
    )


def research_team_memory_writeback_queue_report_payload(
    report: ResearchTeamMemoryWritebackQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryWritebackQueueReport:
        raise ValueError("report must be a ResearchTeamMemoryWritebackQueueReport")
    require_paper_only_flags("memory writeback queue report", report)
    _reject_unsafe_public_payload("memory writeback queue report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("memory writeback queue report payload", payload)
    return payload


def _row_from_candidate(
    item: ResearchTeamMemoryWritebackCandidate,
    *,
    config: ResearchTeamMemoryWritebackQueueConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryWritebackQueueRow:
    postmortem_age_seconds = _duration_seconds(item.postmortem_completed_at, generated_at)
    reason_codes = _row_reason_codes(
        postmortem_age_seconds=postmortem_age_seconds,
        postmortem_summary_score=item.postmortem_summary_score,
        deidentification_score=item.deidentification_score,
        conflict_resolution_state=item.conflict_resolution_state,
        calibration_update_score=item.calibration_update_score,
        local_store_plan_state=item.local_store_plan_state,
        owner_review_required=item.owner_review_required,
        config=config,
    )
    return ResearchTeamMemoryWritebackQueueRow(
        writeback_marker=item.writeback_reference,
        evidence_bundle_marker=item.source_bundle_reference,
        scope_marker=item.scope_reference,
        team_domain=item.team_domain,
        memory_topic=item.memory_topic,
        postmortem_summary=item.postmortem_summary,
        postmortem_completed_at=item.postmortem_completed_at,
        postmortem_age_seconds=postmortem_age_seconds,
        postmortem_summary_score=item.postmortem_summary_score,
        postmortem_summary_plan=_postmortem_summary_plan(
            postmortem_age_seconds=postmortem_age_seconds,
            postmortem_summary_score=item.postmortem_summary_score,
            config=config,
        ),
        deidentification_score=item.deidentification_score,
        deidentification_plan=_deidentification_plan(
            item.deidentification_score,
            config,
        ),
        conflict_resolution_state=item.conflict_resolution_state,
        conflict_resolution_plan=_conflict_resolution_plan(
            item.conflict_resolution_state,
        ),
        calibration_update_score=item.calibration_update_score,
        calibration_update_plan=_calibration_update_plan(
            item.calibration_update_score,
            config,
        ),
        local_store_plan_state=item.local_store_plan_state,
        local_store_write_plan=_local_store_write_plan(item.local_store_plan_state),
        owner_review_required=item.owner_review_required,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    postmortem_age_seconds: Decimal,
    postmortem_summary_score: Decimal,
    deidentification_score: Decimal,
    conflict_resolution_state: str,
    calibration_update_score: Decimal,
    local_store_plan_state: str,
    owner_review_required: bool,
    config: ResearchTeamMemoryWritebackQueueConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if deidentification_score < config.min_deidentification_block_score:
        reasons.append(DEIDENTIFICATION_BLOCK_REASON)
    elif deidentification_score < config.min_deidentification_pass_score:
        reasons.append(DEIDENTIFICATION_WATCH_REASON)
    if conflict_resolution_state == "blocked":
        reasons.append(CONFLICT_RESOLUTION_BLOCK_REASON)
    elif conflict_resolution_state == "needs_review":
        reasons.append(CONFLICT_RESOLUTION_WATCH_REASON)
    if postmortem_age_seconds >= config.stale_postmortem_block_seconds:
        reasons.append(STALE_POSTMORTEM_BLOCK_REASON)
    elif postmortem_age_seconds >= config.stale_postmortem_watch_seconds:
        reasons.append(STALE_POSTMORTEM_WATCH_REASON)
    if postmortem_summary_score < config.min_postmortem_summary_score:
        reasons.append(POSTMORTEM_SUMMARY_WATCH_REASON)
    if calibration_update_score < config.min_calibration_update_score:
        reasons.append(CALIBRATION_UPDATE_WATCH_REASON)
    if local_store_plan_state == "blocked":
        reasons.append(LOCAL_STORE_PLAN_BLOCK_REASON)
    elif local_store_plan_state == "needs_review":
        reasons.append(LOCAL_STORE_PLAN_WATCH_REASON)
    if owner_review_required:
        reasons.append(OWNER_REVIEW_WATCH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in ROW_REASON_PRIORITY if reason in reasons)


def _postmortem_summary_plan(
    *,
    postmortem_age_seconds: Decimal,
    postmortem_summary_score: Decimal,
    config: ResearchTeamMemoryWritebackQueueConfig,
) -> str:
    if postmortem_age_seconds >= config.stale_postmortem_block_seconds:
        return SUMMARY_BLOCK_PLAN
    if (
        postmortem_age_seconds >= config.stale_postmortem_watch_seconds
        or postmortem_summary_score < config.min_postmortem_summary_score
    ):
        return SUMMARY_REVISE_PLAN
    return SUMMARY_INCLUDE_PLAN


def _deidentification_plan(
    score: Decimal,
    config: ResearchTeamMemoryWritebackQueueConfig,
) -> str:
    if score < config.min_deidentification_block_score:
        return DEID_BLOCK_PLAN
    if score < config.min_deidentification_pass_score:
        return DEID_WATCH_PLAN
    return DEID_PASS_PLAN


def _conflict_resolution_plan(state: str) -> str:
    if state == "not_needed":
        return CONFLICT_NONE_PLAN
    if state == "resolved":
        return CONFLICT_APPLY_PLAN
    if state == "needs_review":
        return CONFLICT_REVIEW_PLAN
    return CONFLICT_BLOCK_PLAN


def _calibration_update_plan(
    score: Decimal,
    config: ResearchTeamMemoryWritebackQueueConfig,
) -> str:
    if score < config.min_calibration_update_score:
        return CALIBRATION_REVIEW_PLAN
    return CALIBRATION_APPLY_PLAN


def _local_store_write_plan(state: str) -> str:
    if state == "ready":
        return LOCAL_STORE_READY_PLAN
    if state == "needs_review":
        return LOCAL_STORE_REVIEW_PLAN
    return LOCAL_STORE_BLOCK_PLAN


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryWritebackQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    row_reasons = {
        reason for row in rows for reason in row.reason_codes if reason != PASS_REASON
    }
    if not row_reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in REPORT_REASON_PRIORITY if reason in row_reasons)


def _report_status(rows: tuple[ResearchTeamMemoryWritebackQueueRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return "block"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _reason_count(
    rows: tuple[ResearchTeamMemoryWritebackQueueRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _normalize_candidates(
    candidates: Iterable[ResearchTeamMemoryWritebackCandidate],
) -> tuple[ResearchTeamMemoryWritebackCandidate, ...]:
    if isinstance(candidates, str | bytes):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamMemoryWritebackCandidate:
            raise ValueError(
                "candidates must contain ResearchTeamMemoryWritebackCandidate values",
            )
        require_paper_only_flags("memory writeback candidate", item)
        if item.writeback_reference in seen:
            raise ValueError("writeback_reference values must be unique")
        seen.add(item.writeback_reference)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_domain,
                item.memory_topic,
                item.writeback_reference,
            ),
        ),
    )


def _normalize_rows(
    rows: Iterable[ResearchTeamMemoryWritebackQueueRow],
) -> tuple[ResearchTeamMemoryWritebackQueueRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamMemoryWritebackQueueRow:
            raise ValueError(
                "rows must contain ResearchTeamMemoryWritebackQueueRow values",
            )
        require_paper_only_flags("memory writeback queue row", row)
        if row.writeback_marker in seen:
            raise ValueError("rows writeback_marker values must be unique")
        seen.add(row.writeback_marker)
    expected = _sort_rows(normalized)
    if normalized != expected:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _sort_rows(
    rows: tuple[ResearchTeamMemoryWritebackQueueRow, ...],
) -> tuple[ResearchTeamMemoryWritebackQueueRow, ...]:
    return tuple(sorted(rows, key=_row_rank))


def _row_rank(
    row: ResearchTeamMemoryWritebackQueueRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -_count(len(row.reason_codes)),
        row.team_domain,
        row.memory_topic,
        row.writeback_marker,
    )


def _validate_row(row: ResearchTeamMemoryWritebackQueueRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows require pass reason only")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason")
    if row.deidentification_plan != _expected_deidentification_plan(row):
        raise ValueError("deidentification_plan must match deidentification_score")
    if row.conflict_resolution_plan != _conflict_resolution_plan(
        row.conflict_resolution_state,
    ):
        raise ValueError(
            "conflict_resolution_plan must match conflict_resolution_state",
        )
    if row.local_store_write_plan != _local_store_write_plan(row.local_store_plan_state):
        raise ValueError("local_store_write_plan must match local_store_plan_state")


def _expected_deidentification_plan(
    row: ResearchTeamMemoryWritebackQueueRow,
) -> str:
    if DEIDENTIFICATION_BLOCK_REASON in row.reason_codes:
        return DEID_BLOCK_PLAN
    if DEIDENTIFICATION_WATCH_REASON in row.reason_codes:
        return DEID_WATCH_PLAN
    return DEID_PASS_PLAN


def _validate_report(report: ResearchTeamMemoryWritebackQueueReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.owner_review_required_count != _count(
        sum(1 for row in report.rows if row.owner_review_required),
    ):
        raise ValueError("owner_review_required_count must match rows")
    if report.deidentification_watch_count != _count(
        _reason_count(report.rows, DEIDENTIFICATION_WATCH_REASON),
    ):
        raise ValueError("deidentification_watch_count must match rows")
    if report.deidentification_block_count != _count(
        _reason_count(report.rows, DEIDENTIFICATION_BLOCK_REASON),
    ):
        raise ValueError("deidentification_block_count must match rows")
    if report.local_store_ready_count != _count(
        sum(1 for row in report.rows if row.local_store_plan_state == "ready"),
    ):
        raise ValueError("local_store_ready_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must contain reason codes")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason codes") from exc
    if not items:
        raise ValueError(f"{field_name} must contain reason codes")
    seen: set[str] = set()
    for item in items:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    expected = tuple(reason for reason in allowed if reason in seen)
    if items != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return items


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end must be >= start")
    delta = end - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO or normalized != value:
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_choice(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose unsafe public text")


def _redacted_marker(prefix: str, value: str) -> str:
    return f"{prefix}{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key, value in _iter_public_items(payload):
        lowered_key = key.lower()
        if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"unsafe public payload in {label}: {key}")
        if type(value) is str:
            lowered_value = value.lower()
            if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
                raise ValueError(f"unsafe public payload in {label}: {key}")


def _iter_public_items(value: object) -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_items(asdict(value))
    if isinstance(value, dict):
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key must be a string")
            items.append((key, item))
            items.extend(_iter_public_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_items(item))
        return tuple(items)
    return ()
