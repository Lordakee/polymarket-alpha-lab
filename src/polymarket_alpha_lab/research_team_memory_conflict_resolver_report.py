"""Pure report-only resolver for research-team memory conflict cases.

Callers pass already-loaded conflict cases. This module performs no database,
network, or trading side effects; it only classifies resolver status and emits
redacted public payloads.
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
    "DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_RESOLVER_CONFIG_VERSION",
    "ResearchTeamMemoryConflictCase",
    "ResearchTeamMemoryConflictResolverConfig",
    "ResearchTeamMemoryConflictResolverReport",
    "ResearchTeamMemoryConflictResolverRow",
    "build_research_team_memory_conflict_resolver_report",
    "research_team_memory_conflict_resolver_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_RESOLVER_CONFIG_VERSION = (
    "research-team-memory-conflict-resolver-v0"
)

CONFLICT_TYPES = (
    "source_disagreement",
    "resolution_rule",
    "model_assumption",
    "evidence_quality",
    "outcome_label",
    "timeline",
)
POSTMORTEM_CONCLUSIONS = ("resolved", "needs_recheck", "unresolved", "superseded")
STATUSES = ("pass", "watch", "block")
DOMAIN_PRIORITY_TIERS = ("low", "watch", "block")
EVIDENCE_AGE_ORDERS = ("same_timestamp", "newer_after_older")

PASS_REASON = "memory_conflict_resolver_pass"
EMPTY_REASON = "memory_conflict_resolver_empty"
ESCALATION_BLOCK_REASON = "escalation_required_block"
POSTMORTEM_UNRESOLVED_BLOCK_REASON = "postmortem_unresolved_block"
DOMAIN_PRIORITY_BLOCK_REASON = "domain_priority_block"
NEWER_EVIDENCE_STALE_BLOCK_REASON = "newer_evidence_stale_block"
NEWER_EVIDENCE_STALE_WATCH_REASON = "newer_evidence_stale_watch"
DOMAIN_PRIORITY_WATCH_REASON = "domain_priority_watch"
POSTMORTEM_RECHECK_WATCH_REASON = "postmortem_recheck_watch"

ROW_REASON_PRIORITY = (
    ESCALATION_BLOCK_REASON,
    POSTMORTEM_UNRESOLVED_BLOCK_REASON,
    DOMAIN_PRIORITY_BLOCK_REASON,
    NEWER_EVIDENCE_STALE_BLOCK_REASON,
    NEWER_EVIDENCE_STALE_WATCH_REASON,
    DOMAIN_PRIORITY_WATCH_REASON,
    POSTMORTEM_RECHECK_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_PRIORITY = (
    ESCALATION_BLOCK_REASON,
    POSTMORTEM_UNRESOLVED_BLOCK_REASON,
    DOMAIN_PRIORITY_BLOCK_REASON,
    NEWER_EVIDENCE_STALE_BLOCK_REASON,
    NEWER_EVIDENCE_STALE_WATCH_REASON,
    DOMAIN_PRIORITY_WATCH_REASON,
    POSTMORTEM_RECHECK_WATCH_REASON,
    EMPTY_REASON,
)
BLOCK_REASONS = frozenset(
    (
        ESCALATION_BLOCK_REASON,
        POSTMORTEM_UNRESOLVED_BLOCK_REASON,
        DOMAIN_PRIORITY_BLOCK_REASON,
        NEWER_EVIDENCE_STALE_BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        NEWER_EVIDENCE_STALE_WATCH_REASON,
        DOMAIN_PRIORITY_WATCH_REASON,
        POSTMORTEM_RECHECK_WATCH_REASON,
    ),
)
RESOLVED_ACTION = "record_resolved_postmortem"
ESCALATE_ACTION = "escalate_to_memory_owner"
FREEZE_ACTION = "freeze_conflicting_memory_until_reviewed"
PREFER_NEWER_ACTION = "prefer_newer_evidence_after_review"
RECHECK_ACTION = "queue_memory_recheck"

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
    "source_url",
    "source_text",
    "source_id",
    "market_reference",
    "market_id",
    "market_slug",
    "market_question",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "postgres:",
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
    "market-id",
    "market_id",
    "slug",
    "question",
    "polymarket-market",
)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictResolverConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_RESOLVER_CONFIG_VERSION
    stale_evidence_watch_seconds: Decimal = Decimal("604800.000000")
    stale_evidence_block_seconds: Decimal = Decimal("2592000.000000")
    domain_priority_watch_score: Decimal = Decimal("0.700000")
    domain_priority_block_score: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_RESOLVER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_evidence_watch_seconds",
            "stale_evidence_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_evidence_block_seconds <= self.stale_evidence_watch_seconds:
            raise ValueError(
                "stale_evidence_block_seconds must be greater than "
                "stale_evidence_watch_seconds",
            )
        for field_name in (
            "domain_priority_watch_score",
            "domain_priority_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.domain_priority_block_score <= self.domain_priority_watch_score:
            raise ValueError(
                "domain_priority_block_score must be greater than "
                "domain_priority_watch_score",
            )
        require_paper_only_flags("memory conflict resolver config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictCase:
    case_reference: str
    raw_source_reference: str
    market_reference: str
    team_domain: str
    memory_topic: str
    conflict_type: str
    older_evidence_observed_at: datetime
    newer_evidence_observed_at: datetime
    domain_priority_score: Decimal
    postmortem_conclusion: str
    escalation_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_private_reference("case_reference", self.case_reference)
        _require_private_reference("raw_source_reference", self.raw_source_reference)
        _require_private_reference("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "case_reference",
            _redacted_marker("case_marker_", self.case_reference),
        )
        object.__setattr__(
            self,
            "raw_source_reference",
            _redacted_marker("evidence_marker_", self.raw_source_reference),
        )
        object.__setattr__(
            self,
            "market_reference",
            _redacted_marker("scope_marker_", self.market_reference),
        )
        _require_public_text("team_domain", self.team_domain)
        _require_public_text("memory_topic", self.memory_topic)
        _require_choice("conflict_type", self.conflict_type, CONFLICT_TYPES)
        object.__setattr__(
            self,
            "older_evidence_observed_at",
            _as_utc("older_evidence_observed_at", self.older_evidence_observed_at),
        )
        object.__setattr__(
            self,
            "newer_evidence_observed_at",
            _as_utc("newer_evidence_observed_at", self.newer_evidence_observed_at),
        )
        if self.newer_evidence_observed_at < self.older_evidence_observed_at:
            raise ValueError(
                "newer_evidence_observed_at must be >= older_evidence_observed_at",
            )
        object.__setattr__(
            self,
            "domain_priority_score",
            _require_ratio("domain_priority_score", self.domain_priority_score),
        )
        _require_choice(
            "postmortem_conclusion",
            self.postmortem_conclusion,
            POSTMORTEM_CONCLUSIONS,
        )
        _require_bool("escalation_required", self.escalation_required)
        require_paper_only_flags("memory conflict case", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictResolverRow:
    case_marker: str
    evidence_bundle_marker: str
    case_scope_marker: str
    team_domain: str
    memory_topic: str
    conflict_type: str
    older_evidence_observed_at: datetime
    newer_evidence_observed_at: datetime
    evidence_age_order: str
    newer_evidence_age_seconds: Decimal
    evidence_revision_gap_seconds: Decimal
    domain_priority_score: Decimal
    domain_priority_tier: str
    postmortem_conclusion: str
    escalation_required: bool
    status: str
    reason_codes: tuple[str, ...]
    resolver_actions: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "case_marker",
            "evidence_bundle_marker",
            "case_scope_marker",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        _require_public_text("team_domain", self.team_domain)
        _require_public_text("memory_topic", self.memory_topic)
        _require_choice("conflict_type", self.conflict_type, CONFLICT_TYPES)
        object.__setattr__(
            self,
            "older_evidence_observed_at",
            _as_utc("older_evidence_observed_at", self.older_evidence_observed_at),
        )
        object.__setattr__(
            self,
            "newer_evidence_observed_at",
            _as_utc("newer_evidence_observed_at", self.newer_evidence_observed_at),
        )
        _require_choice("evidence_age_order", self.evidence_age_order, EVIDENCE_AGE_ORDERS)
        for field_name in (
            "newer_evidence_age_seconds",
            "evidence_revision_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_priority_score",
            _require_ratio("domain_priority_score", self.domain_priority_score),
        )
        _require_choice("domain_priority_tier", self.domain_priority_tier, DOMAIN_PRIORITY_TIERS)
        _require_choice(
            "postmortem_conclusion",
            self.postmortem_conclusion,
            POSTMORTEM_CONCLUSIONS,
        )
        _require_bool("escalation_required", self.escalation_required)
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
        object.__setattr__(
            self,
            "resolver_actions",
            _normalize_public_text_tuple(
                "resolver_actions",
                self.resolver_actions,
            ),
        )
        require_paper_only_flags("memory conflict resolver row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictResolverReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    escalation_required_count: Decimal
    stale_newer_evidence_count: Decimal
    high_domain_priority_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamMemoryConflictResolverRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_RESOLVER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "escalation_required_count",
            "stale_newer_evidence_count",
            "high_domain_priority_count",
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
        require_paper_only_flags("memory conflict resolver report", self)
        _reject_unsafe_public_payload("memory conflict resolver report", self)
        _validate_report(self)


def build_research_team_memory_conflict_resolver_report(
    cases: Iterable[ResearchTeamMemoryConflictCase],
    *,
    config: ResearchTeamMemoryConflictResolverConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryConflictResolverReport:
    if type(config) is not ResearchTeamMemoryConflictResolverConfig:
        raise ValueError("config must be a ResearchTeamMemoryConflictResolverConfig")
    require_paper_only_flags("memory conflict resolver config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_cases = _normalize_cases(cases)
    for item in normalized_cases:
        if item.older_evidence_observed_at > generated_at_utc:
            raise ValueError("older_evidence_observed_at must be <= generated_at")
        if item.newer_evidence_observed_at > generated_at_utc:
            raise ValueError("newer_evidence_observed_at must be <= generated_at")

    rows = _sort_rows(
        tuple(_row_from_case(item, config=config, generated_at=generated_at_utc) for item in normalized_cases),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamMemoryConflictResolverReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        case_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        escalation_required_count=_count(
            sum(1 for row in rows if row.escalation_required),
        ),
        stale_newer_evidence_count=_count(
            sum(1 for row in rows if _has_stale_newer_evidence(row)),
        ),
        high_domain_priority_count=_count(
            sum(1 for row in rows if row.domain_priority_tier in ("watch", "block")),
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
    )


def research_team_memory_conflict_resolver_report_payload(
    report: ResearchTeamMemoryConflictResolverReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryConflictResolverReport:
        raise ValueError("report must be a ResearchTeamMemoryConflictResolverReport")
    require_paper_only_flags("memory conflict resolver report", report)
    _reject_unsafe_public_payload("memory conflict resolver report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("memory conflict resolver report payload", payload)
    return payload


def _row_from_case(
    item: ResearchTeamMemoryConflictCase,
    *,
    config: ResearchTeamMemoryConflictResolverConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryConflictResolverRow:
    newer_evidence_age_seconds = _duration_seconds(
        item.newer_evidence_observed_at,
        generated_at,
    )
    evidence_revision_gap_seconds = _duration_seconds(
        item.older_evidence_observed_at,
        item.newer_evidence_observed_at,
    )
    domain_priority_tier = _domain_priority_tier(item.domain_priority_score, config)
    reason_codes = _row_reason_codes(
        newer_evidence_age_seconds=newer_evidence_age_seconds,
        domain_priority_tier=domain_priority_tier,
        postmortem_conclusion=item.postmortem_conclusion,
        escalation_required=item.escalation_required,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchTeamMemoryConflictResolverRow(
        case_marker=item.case_reference,
        evidence_bundle_marker=item.raw_source_reference,
        case_scope_marker=item.market_reference,
        team_domain=item.team_domain,
        memory_topic=item.memory_topic,
        conflict_type=item.conflict_type,
        older_evidence_observed_at=item.older_evidence_observed_at,
        newer_evidence_observed_at=item.newer_evidence_observed_at,
        evidence_age_order=_evidence_age_order(
            item.older_evidence_observed_at,
            item.newer_evidence_observed_at,
        ),
        newer_evidence_age_seconds=newer_evidence_age_seconds,
        evidence_revision_gap_seconds=evidence_revision_gap_seconds,
        domain_priority_score=item.domain_priority_score,
        domain_priority_tier=domain_priority_tier,
        postmortem_conclusion=item.postmortem_conclusion,
        escalation_required=item.escalation_required,
        status=status,
        reason_codes=reason_codes,
        resolver_actions=_resolver_actions(
            status=status,
            escalation_required=item.escalation_required,
        ),
    )


def _row_reason_codes(
    *,
    newer_evidence_age_seconds: Decimal,
    domain_priority_tier: str,
    postmortem_conclusion: str,
    escalation_required: bool,
    config: ResearchTeamMemoryConflictResolverConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if escalation_required:
        reasons.append(ESCALATION_BLOCK_REASON)
    if postmortem_conclusion == "unresolved":
        reasons.append(POSTMORTEM_UNRESOLVED_BLOCK_REASON)
    if domain_priority_tier == "block":
        reasons.append(DOMAIN_PRIORITY_BLOCK_REASON)
    if newer_evidence_age_seconds >= config.stale_evidence_block_seconds:
        reasons.append(NEWER_EVIDENCE_STALE_BLOCK_REASON)
    elif newer_evidence_age_seconds >= config.stale_evidence_watch_seconds:
        reasons.append(NEWER_EVIDENCE_STALE_WATCH_REASON)
    if domain_priority_tier == "watch":
        reasons.append(DOMAIN_PRIORITY_WATCH_REASON)
    if postmortem_conclusion == "needs_recheck":
        reasons.append(POSTMORTEM_RECHECK_WATCH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in ROW_REASON_PRIORITY if reason in reasons)


def _resolver_actions(*, status: str, escalation_required: bool) -> tuple[str, ...]:
    if status == "pass":
        return (RESOLVED_ACTION,)
    actions: list[str] = []
    if escalation_required or status == "block":
        actions.append(ESCALATE_ACTION)
    if status == "block":
        actions.append(FREEZE_ACTION)
    actions.append(PREFER_NEWER_ACTION)
    if status == "watch":
        actions.append(RECHECK_ACTION)
    return tuple(actions)


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryConflictResolverRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    row_reasons = {
        reason for row in rows for reason in row.reason_codes if reason != PASS_REASON
    }
    if not row_reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in REPORT_REASON_PRIORITY if reason in row_reasons)


def _report_status(rows: tuple[ResearchTeamMemoryConflictResolverRow, ...]) -> str:
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


def _domain_priority_tier(
    value: Decimal,
    config: ResearchTeamMemoryConflictResolverConfig,
) -> str:
    if value >= config.domain_priority_block_score:
        return "block"
    if value >= config.domain_priority_watch_score:
        return "watch"
    return "low"


def _evidence_age_order(older: datetime, newer: datetime) -> str:
    if older == newer:
        return "same_timestamp"
    return "newer_after_older"


def _has_stale_newer_evidence(row: ResearchTeamMemoryConflictResolverRow) -> bool:
    return (
        NEWER_EVIDENCE_STALE_BLOCK_REASON in row.reason_codes
        or NEWER_EVIDENCE_STALE_WATCH_REASON in row.reason_codes
    )


def _normalize_cases(
    cases: Iterable[ResearchTeamMemoryConflictCase],
) -> tuple[ResearchTeamMemoryConflictCase, ...]:
    if isinstance(cases, str | bytes):
        raise ValueError("cases must be an iterable")
    try:
        normalized = tuple(cases)
    except TypeError as exc:
        raise ValueError("cases must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamMemoryConflictCase:
            raise ValueError("cases must contain ResearchTeamMemoryConflictCase values")
        require_paper_only_flags("memory conflict case", item)
        if item.case_reference in seen:
            raise ValueError("case_reference values must be unique")
        seen.add(item.case_reference)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_domain,
                item.memory_topic,
                item.conflict_type,
                item.case_reference,
            ),
        ),
    )


def _normalize_rows(
    rows: Iterable[ResearchTeamMemoryConflictResolverRow],
) -> tuple[ResearchTeamMemoryConflictResolverRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamMemoryConflictResolverRow:
            raise ValueError("rows must contain ResearchTeamMemoryConflictResolverRow values")
        require_paper_only_flags("memory conflict resolver row", row)
        if row.case_marker in seen:
            raise ValueError("rows case_marker values must be unique")
        seen.add(row.case_marker)
    expected = _sort_rows(normalized)
    if normalized != expected:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _sort_rows(
    rows: tuple[ResearchTeamMemoryConflictResolverRow, ...],
) -> tuple[ResearchTeamMemoryConflictResolverRow, ...]:
    return tuple(sorted(rows, key=_row_rank))


def _row_rank(
    row: ResearchTeamMemoryConflictResolverRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -_count(len(row.reason_codes)),
        row.team_domain,
        row.memory_topic,
        row.case_marker,
    )


def _validate_row(row: ResearchTeamMemoryConflictResolverRow) -> None:
    if row.newer_evidence_observed_at < row.older_evidence_observed_at:
        raise ValueError("newer_evidence_observed_at must be >= older_evidence_observed_at")
    if row.evidence_age_order != _evidence_age_order(
        row.older_evidence_observed_at,
        row.newer_evidence_observed_at,
    ):
        raise ValueError("evidence_age_order must match evidence timestamps")
    if row.evidence_revision_gap_seconds != _duration_seconds(
        row.older_evidence_observed_at,
        row.newer_evidence_observed_at,
    ):
        raise ValueError("evidence_revision_gap_seconds must match evidence timestamps")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows require pass reason only")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason")
    if row.escalation_required and ESCALATION_BLOCK_REASON not in row.reason_codes:
        raise ValueError("escalation_required rows require escalation reason")
    if row.status == "pass" and row.resolver_actions != (RESOLVED_ACTION,):
        raise ValueError("pass rows require resolved action only")
    if row.status == "block" and FREEZE_ACTION not in row.resolver_actions:
        raise ValueError("block rows require freeze action")


def _validate_report(report: ResearchTeamMemoryConflictResolverReport) -> None:
    if report.case_count != _count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.escalation_required_count != _count(
        sum(1 for row in report.rows if row.escalation_required),
    ):
        raise ValueError("escalation_required_count must match rows")
    if report.stale_newer_evidence_count != _count(
        sum(1 for row in report.rows if _has_stale_newer_evidence(row)),
    ):
        raise ValueError("stale_newer_evidence_count must match rows")
    if report.high_domain_priority_count != _count(
        sum(1 for row in report.rows if row.domain_priority_tier in ("watch", "block")),
    ):
        raise ValueError("high_domain_priority_count must match rows")
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


def _normalize_public_text_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must contain public strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain public strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain public strings")
    for item in items:
        _require_public_text(field_name, item)
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
