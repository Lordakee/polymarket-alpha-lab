"""Readonly expert review queue report for research domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_DOMAIN_EXPERT_REVIEW_QUEUE_CONFIG_VERSION = (
    "research-domain-expert-review-queue"
)
DOMAINS = ("politics", "btc", "stock_index", "gold", "soccer", "basketball")
REVIEW_STATUSES = ("pass", "watch", "block")
RECENCY_STATUSES = ("current", "stale", "missing")
CONFLICT_STATUSES = ("low", "medium", "high")
ROW_REASON_CODES = (
    "expert_review_clear",
    "evidence_gap_present",
    "evidence_missing",
    "evidence_stale",
    "source_conflict_watch",
    "source_conflict_block",
)
REPORT_REASON_CODES = (
    "expert_review_queue_clear",
    "expert_review_watch_items_present",
    "expert_review_block_items_present",
    "evidence_gaps_present",
    "stale_evidence_present",
    "source_conflicts_present",
)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
UNSAFE_PUBLIC_TERMS = (
    "auth",
    "wallet",
    "order",
    "database",
    "network",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_EXPERT_REVIEW_QUEUE_CONFIG_VERSION",
    "CONFLICT_STATUSES",
    "DOMAINS",
    "RECENCY_STATUSES",
    "REPORT_REASON_CODES",
    "REVIEW_STATUSES",
    "ROW_REASON_CODES",
    "ResearchDomainExpertReviewQueueConfig",
    "ResearchDomainExpertReviewQueueInput",
    "ResearchDomainExpertReviewQueueReport",
    "ResearchDomainExpertReviewQueueRow",
    "build_research_domain_expert_review_queue",
    "research_domain_expert_review_queue_payload",
)


@dataclass(frozen=True)
class ResearchDomainExpertReviewQueueConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_EXPERT_REVIEW_QUEUE_CONFIG_VERSION
    stale_evidence_seconds: Decimal = Decimal("3600.000000")
    evidence_gap_penalty: Decimal = Decimal("20.000000")
    stale_evidence_penalty: Decimal = Decimal("15.000000")
    missing_evidence_penalty: Decimal = Decimal("30.000000")
    conflict_score_multiplier: Decimal = Decimal("50.000000")
    conflict_watch_threshold: Decimal = Decimal("0.300000")
    conflict_block_threshold: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("20.000000")
    block_score_floor: Decimal = Decimal("70.000000")
    block_evidence_gap_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_evidence_seconds",
            _normalize_positive_seconds(
                "stale_evidence_seconds",
                self.stale_evidence_seconds,
            ),
        )
        for field_name in (
            "evidence_gap_penalty",
            "stale_evidence_penalty",
            "missing_evidence_penalty",
            "conflict_score_multiplier",
            "watch_score_floor",
            "block_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_score(field_name, getattr(self, field_name)),
            )
        for field_name in ("conflict_watch_threshold", "conflict_block_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "block_evidence_gap_count",
            _normalize_positive_count(
                "block_evidence_gap_count",
                self.block_evidence_gap_count,
            ),
        )
        if self.conflict_block_threshold < self.conflict_watch_threshold:
            raise ValueError("conflict_block_threshold must be >= conflict_watch_threshold")
        if self.block_score_floor < self.watch_score_floor:
            raise ValueError("block_score_floor must be >= watch_score_floor")
        _reject_unsafe_public_payload("ResearchDomainExpertReviewQueueConfig", self)
        require_paper_only_flags("ResearchDomainExpertReviewQueueConfig", self)


@dataclass(frozen=True)
class ResearchDomainExpertReviewQueueInput:
    packet_id: str
    market_id: str
    domain: str
    question: str
    evidence_gap_codes: tuple[str, ...]
    latest_evidence_at: datetime | None
    conflict_strength: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_id", self.market_id)
        _require_member("domain", self.domain, DOMAINS, "known domain")
        _require_public_text("question", self.question)
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_public_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_optional_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "conflict_strength",
            _normalize_unit_score("conflict_strength", self.conflict_strength),
        )
        _reject_unsafe_public_payload("ResearchDomainExpertReviewQueueInput", self)
        require_paper_only_flags("ResearchDomainExpertReviewQueueInput", self)


@dataclass(frozen=True)
class ResearchDomainExpertReviewQueueRow:
    priority_rank: Decimal
    packet_id: str
    market_id: str
    domain: str
    question: str
    review_status: str
    review_reason_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...]
    evidence_gap_count: Decimal
    latest_evidence_at: datetime | None
    evidence_age_seconds: Decimal | None
    recency_status: str
    conflict_strength: Decimal
    conflict_status: str
    expert_review_priority_score: Decimal
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_id", self.market_id)
        _require_member("domain", self.domain, DOMAINS, "known domain")
        _require_public_text("question", self.question)
        _require_member("review_status", self.review_status, REVIEW_STATUSES, "review status")
        object.__setattr__(
            self,
            "review_reason_codes",
            _normalize_reason_codes(
                "review_reason_codes",
                self.review_reason_codes,
                ROW_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_public_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        object.__setattr__(
            self,
            "evidence_gap_count",
            _normalize_nonnegative_count("evidence_gap_count", self.evidence_gap_count),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_optional_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        _require_member("recency_status", self.recency_status, RECENCY_STATUSES, "recency status")
        object.__setattr__(
            self,
            "conflict_strength",
            _normalize_unit_score("conflict_strength", self.conflict_strength),
        )
        _require_member(
            "conflict_status",
            self.conflict_status,
            CONFLICT_STATUSES,
            "conflict status",
        )
        object.__setattr__(
            self,
            "expert_review_priority_score",
            _normalize_nonnegative_score(
                "expert_review_priority_score",
                self.expert_review_priority_score,
            ),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload("ResearchDomainExpertReviewQueueRow", self)
        require_paper_only_flags("ResearchDomainExpertReviewQueueRow", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchDomainExpertReviewQueueReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    domain_count: Decimal
    evidence_gap_candidate_count: Decimal
    stale_evidence_candidate_count: Decimal
    conflict_candidate_count: Decimal
    max_expert_review_priority_score: Decimal
    rows: tuple[ResearchDomainExpertReviewQueueRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REVIEW_STATUSES, "review status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "domain_count",
            "evidence_gap_candidate_count",
            "stale_evidence_candidate_count",
            "conflict_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_expert_review_priority_score",
            _normalize_nonnegative_score(
                "max_expert_review_priority_score",
                self.max_expert_review_priority_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload("ResearchDomainExpertReviewQueueReport", self)
        require_paper_only_flags("ResearchDomainExpertReviewQueueReport", self)
        _validate_report(self)


@dataclass(frozen=True)
class _DomainReviewDraft:
    input_rank: Decimal
    packet_id: str
    market_id: str
    domain: str
    question: str
    review_status: str
    review_reason_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...]
    evidence_gap_count: Decimal
    latest_evidence_at: datetime | None
    evidence_age_seconds: Decimal | None
    recency_status: str
    conflict_strength: Decimal
    conflict_status: str
    expert_review_priority_score: Decimal


def build_research_domain_expert_review_queue(
    inputs: list[ResearchDomainExpertReviewQueueInput]
    | tuple[ResearchDomainExpertReviewQueueInput, ...],
    *,
    config: ResearchDomainExpertReviewQueueConfig,
    generated_at: datetime,
) -> ResearchDomainExpertReviewQueueReport:
    if type(config) is not ResearchDomainExpertReviewQueueConfig:
        raise ValueError("config must be a ResearchDomainExpertReviewQueueConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    drafts = tuple(
        _draft_for_input(row, config=config, generated_at=generated_at_utc, input_rank=_count(index))
        for index, row in enumerate(input_rows, start=1)
    )
    rows = tuple(
        _row_from_draft(draft, priority_rank=_count(index))
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    digest = _report_digest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchDomainExpertReviewQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        domain_count=_count(len({row.domain for row in rows})),
        evidence_gap_candidate_count=_flag_count(rows, "has_evidence_gap"),
        stale_evidence_candidate_count=_flag_count(rows, "has_stale_evidence"),
        conflict_candidate_count=_flag_count(rows, "has_conflict"),
        max_expert_review_priority_score=_max_score(
            tuple(row.expert_review_priority_score for row in rows),
        ),
        rows=rows,
        derived_validation_digest=digest,
    )


def research_domain_expert_review_queue_payload(report: ResearchDomainExpertReviewQueueReport) -> dict[str, Any]:
    if type(report) is not ResearchDomainExpertReviewQueueReport:
        _reject_unsafe_public_payload("research domain expert review queue payload", report)
        raise ValueError("report must be a ResearchDomainExpertReviewQueueReport")
    require_paper_only_flags("report", report)
    _validate_report(report)
    _reject_unsafe_public_payload("research domain expert review queue payload", report)
    ready = _json_ready(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("research domain expert review queue payload", ready)
    return ready


def _draft_for_input(
    row: ResearchDomainExpertReviewQueueInput,
    *,
    config: ResearchDomainExpertReviewQueueConfig,
    generated_at: datetime,
    input_rank: Decimal,
) -> _DomainReviewDraft:
    if row.latest_evidence_at is not None and row.latest_evidence_at > generated_at:
        raise ValueError("latest_evidence_at must not be after generated_at")
    evidence_age_seconds = (
        None
        if row.latest_evidence_at is None
        else _seconds_between(row.latest_evidence_at, generated_at)
    )
    evidence_gap_count = _count(len(row.evidence_gap_codes))
    recency_status = _recency_status(evidence_age_seconds, config=config)
    conflict_status = _conflict_status(row.conflict_strength, config=config)
    priority_score = (
        evidence_gap_count * config.evidence_gap_penalty
        + row.conflict_strength * config.conflict_score_multiplier
    )
    if recency_status == "missing":
        priority_score += config.missing_evidence_penalty
    elif recency_status == "stale":
        priority_score += config.stale_evidence_penalty
    priority_score = _normalize_nonnegative_score("expert_review_priority_score", priority_score)
    review_status = _review_status(
        evidence_gap_count=evidence_gap_count,
        recency_status=recency_status,
        conflict_strength=row.conflict_strength,
        expert_review_priority_score=priority_score,
        config=config,
    )
    return _DomainReviewDraft(
        input_rank=input_rank,
        packet_id=row.packet_id,
        market_id=row.market_id,
        domain=row.domain,
        question=row.question,
        review_status=review_status,
        review_reason_codes=_row_reason_codes(
            evidence_gap_count=evidence_gap_count,
            recency_status=recency_status,
            conflict_status=conflict_status,
        ),
        evidence_gap_codes=row.evidence_gap_codes,
        evidence_gap_count=evidence_gap_count,
        latest_evidence_at=row.latest_evidence_at,
        evidence_age_seconds=evidence_age_seconds,
        recency_status=recency_status,
        conflict_strength=row.conflict_strength,
        conflict_status=conflict_status,
        expert_review_priority_score=priority_score,
    )


def _row_from_draft(
    draft: _DomainReviewDraft,
    *,
    priority_rank: Decimal,
) -> ResearchDomainExpertReviewQueueRow:
    return ResearchDomainExpertReviewQueueRow(
        priority_rank=priority_rank,
        packet_id=draft.packet_id,
        market_id=draft.market_id,
        domain=draft.domain,
        question=draft.question,
        review_status=draft.review_status,
        review_reason_codes=draft.review_reason_codes,
        evidence_gap_codes=draft.evidence_gap_codes,
        evidence_gap_count=draft.evidence_gap_count,
        latest_evidence_at=draft.latest_evidence_at,
        evidence_age_seconds=draft.evidence_age_seconds,
        recency_status=draft.recency_status,
        conflict_strength=draft.conflict_strength,
        conflict_status=draft.conflict_status,
        expert_review_priority_score=draft.expert_review_priority_score,
        derived_validation_digest=_row_digest(draft=draft, priority_rank=priority_rank),
    )


def _normalize_inputs(
    inputs: list[ResearchDomainExpertReviewQueueInput]
    | tuple[ResearchDomainExpertReviewQueueInput, ...],
) -> tuple[ResearchDomainExpertReviewQueueInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchDomainExpertReviewQueueInput:
            raise ValueError("inputs must contain ResearchDomainExpertReviewQueueInput values")
        require_paper_only_flags("input", row)
        key = (row.packet_id, row.market_id)
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate packet_id/market_id values")
        seen_keys.add(key)
    return rows


def _normalize_rows(value: object) -> tuple[ResearchDomainExpertReviewQueueRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a list or tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a list or tuple") from exc
    seen_keys: set[tuple[str, str]] = set()
    seen_ranks: set[Decimal] = set()
    for row in rows:
        if type(row) is not ResearchDomainExpertReviewQueueRow:
            raise ValueError("rows must contain ResearchDomainExpertReviewQueueRow values")
        require_paper_only_flags("row", row)
        _validate_row(row)
        key = (row.packet_id, row.market_id)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate packet_id/market_id values")
        seen_keys.add(key)
        if row.priority_rank in seen_ranks:
            raise ValueError("rows must not contain duplicate priority_rank values")
        seen_ranks.add(row.priority_rank)
    return rows


def _validate_row(row: ResearchDomainExpertReviewQueueRow) -> None:
    if row.evidence_gap_count != _count(len(row.evidence_gap_codes)):
        raise ValueError("evidence_gap_count must match evidence_gap_codes")
    if row.latest_evidence_at is None:
        if row.evidence_age_seconds is not None:
            raise ValueError("evidence_age_seconds must be absent without latest_evidence_at")
        if row.recency_status != "missing":
            raise ValueError("recency_status must be missing without latest_evidence_at")
    elif row.evidence_age_seconds is None:
        raise ValueError("evidence_age_seconds must be present with latest_evidence_at")
    if row.review_reason_codes != _row_reason_codes(
        evidence_gap_count=row.evidence_gap_count,
        recency_status=row.recency_status,
        conflict_status=row.conflict_status,
    ):
        raise ValueError("review_reason_codes must match row review signals")
    if row.derived_validation_digest != _row_digest(row=row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchDomainExpertReviewQueueReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.domain_count != _count(len({row.domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.evidence_gap_candidate_count != _flag_count(report.rows, "has_evidence_gap"):
        raise ValueError("evidence_gap_candidate_count must match rows")
    if report.stale_evidence_candidate_count != _flag_count(report.rows, "has_stale_evidence"):
        raise ValueError("stale_evidence_candidate_count must match rows")
    if report.conflict_candidate_count != _flag_count(report.rows, "has_conflict"):
        raise ValueError("conflict_candidate_count must match rows")
    if report.max_expert_review_priority_score != _max_score(
        tuple(row.expert_review_priority_score for row in report.rows),
    ):
        raise ValueError("max_expert_review_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.priority_rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must have contiguous priority_rank values")
    if tuple(report.rows) != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by expert review priority")
    if report.derived_validation_digest != _report_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=report.rows,
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _recency_status(
    evidence_age_seconds: Decimal | None,
    *,
    config: ResearchDomainExpertReviewQueueConfig,
) -> str:
    if evidence_age_seconds is None:
        return "missing"
    if evidence_age_seconds >= config.stale_evidence_seconds:
        return "stale"
    return "current"


def _conflict_status(
    conflict_strength: Decimal,
    *,
    config: ResearchDomainExpertReviewQueueConfig,
) -> str:
    if conflict_strength >= config.conflict_block_threshold:
        return "high"
    if conflict_strength >= config.conflict_watch_threshold:
        return "medium"
    return "low"


def _review_status(
    *,
    evidence_gap_count: Decimal,
    recency_status: str,
    conflict_strength: Decimal,
    expert_review_priority_score: Decimal,
    config: ResearchDomainExpertReviewQueueConfig,
) -> str:
    if (
        recency_status == "missing"
        or evidence_gap_count >= config.block_evidence_gap_count
        or conflict_strength >= config.conflict_block_threshold
        or expert_review_priority_score >= config.block_score_floor
    ):
        return "block"
    if (
        recency_status == "stale"
        or evidence_gap_count > ZERO_COUNT
        or conflict_strength >= config.conflict_watch_threshold
        or expert_review_priority_score >= config.watch_score_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    evidence_gap_count: Decimal,
    recency_status: str,
    conflict_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if evidence_gap_count >= Decimal("3"):
        codes.append("evidence_missing")
    elif evidence_gap_count > ZERO_COUNT:
        codes.append("evidence_gap_present")
    if recency_status == "missing":
        if "evidence_missing" not in codes:
            codes.append("evidence_missing")
    elif recency_status == "stale":
        codes.append("evidence_stale")
    if conflict_status == "high":
        codes.append("source_conflict_block")
    elif conflict_status == "medium":
        codes.append("source_conflict_watch")
    if not codes:
        codes.append("expert_review_clear")
    return tuple(codes)


def _report_status(rows: tuple[ResearchDomainExpertReviewQueueRow, ...]) -> str:
    if any(row.review_status == "block" for row in rows):
        return "block"
    if any(row.review_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchDomainExpertReviewQueueRow, ...]) -> tuple[str, ...]:
    codes: list[str] = []
    if any(row.review_status == "block" for row in rows):
        codes.append("expert_review_block_items_present")
    elif any(row.review_status == "watch" for row in rows):
        codes.append("expert_review_watch_items_present")
    else:
        codes.append("expert_review_queue_clear")
    if any(row.evidence_gap_count > ZERO_COUNT for row in rows):
        codes.append("evidence_gaps_present")
    if any(row.recency_status != "current" for row in rows):
        codes.append("stale_evidence_present")
    if any(row.conflict_status != "low" for row in rows):
        codes.append("source_conflicts_present")
    return tuple(codes)


def _draft_sort_key(draft: _DomainReviewDraft) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return (
        -draft.expert_review_priority_score,
        -draft.conflict_strength,
        -draft.evidence_gap_count,
        draft.input_rank,
    )


def _row_sort_key(row: ResearchDomainExpertReviewQueueRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        row.priority_rank,
        -row.expert_review_priority_score,
        row.packet_id,
        row.market_id,
    )


def _status_count(rows: tuple[ResearchDomainExpertReviewQueueRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.review_status == status))


def _flag_count(rows: tuple[ResearchDomainExpertReviewQueueRow, ...], flag_name: str) -> Decimal:
    if flag_name == "has_evidence_gap":
        return _count(sum(1 for row in rows if row.evidence_gap_count > ZERO_COUNT))
    if flag_name == "has_stale_evidence":
        return _count(sum(1 for row in rows if row.recency_status != "current"))
    if flag_name == "has_conflict":
        return _count(sum(1 for row in rows if row.conflict_status != "low"))
    raise ValueError("unknown row flag")


def _max_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    return _normalize_nonnegative_score("max_score", max(values))


def _row_digest(
    *,
    draft: _DomainReviewDraft | None = None,
    priority_rank: Decimal | None = None,
    row: ResearchDomainExpertReviewQueueRow | None = None,
) -> str:
    if row is not None:
        payload = {
            "priority_rank": row.priority_rank,
            "packet_id": row.packet_id,
            "market_id": row.market_id,
            "domain": row.domain,
            "question": row.question,
            "review_status": row.review_status,
            "review_reason_codes": row.review_reason_codes,
            "evidence_gap_codes": row.evidence_gap_codes,
            "evidence_gap_count": row.evidence_gap_count,
            "latest_evidence_at": row.latest_evidence_at,
            "evidence_age_seconds": row.evidence_age_seconds,
            "recency_status": row.recency_status,
            "conflict_strength": row.conflict_strength,
            "conflict_status": row.conflict_status,
            "expert_review_priority_score": row.expert_review_priority_score,
        }
    elif draft is not None and priority_rank is not None:
        payload = {
            "priority_rank": priority_rank,
            "packet_id": draft.packet_id,
            "market_id": draft.market_id,
            "domain": draft.domain,
            "question": draft.question,
            "review_status": draft.review_status,
            "review_reason_codes": draft.review_reason_codes,
            "evidence_gap_codes": draft.evidence_gap_codes,
            "evidence_gap_count": draft.evidence_gap_count,
            "latest_evidence_at": draft.latest_evidence_at,
            "evidence_age_seconds": draft.evidence_age_seconds,
            "recency_status": draft.recency_status,
            "conflict_strength": draft.conflict_strength,
            "conflict_status": draft.conflict_status,
            "expert_review_priority_score": draft.expert_review_priority_score,
        }
    else:
        raise ValueError("row digest requires row or draft with priority_rank")
    return _digest_payload(payload)


def _report_digest(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchDomainExpertReviewQueueRow, ...],
) -> str:
    return _digest_payload(
        {
            "generated_at": generated_at,
            "config_version": config_version,
            "row_digests": tuple(row.derived_validation_digest for row in rows),
        },
    )


def _digest_payload(payload: dict[str, object]) -> str:
    return "sha256:" + sha256(
        json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key, item in _iter_public_items(value):
        lowered_key = key.lower()
        if any(term in lowered_key for term in UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public key in {label}: {key}")
        if isinstance(item, str):
            lowered_value = item.lower()
            if any(term in lowered_value for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"unsafe public value in {label}: {key}")


def _iter_public_items(value: object) -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[tuple[str, object]] = []
        for field in fields(value):
            item = getattr(value, field.name)
            items.append((field.name, item))
            items.extend(_iter_public_items(item))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append((key, item))
            items.extend(_iter_public_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_items(item))
        return tuple(items)
    return ()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_seconds(
        "seconds_between",
        total_microseconds / MICROSECONDS_PER_SECOND,
    )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized <= ZERO_COUNT or normalized != value:
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT or normalized != value:
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return normalized


def _normalize_positive_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_nonnegative_score(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_score(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_score(field_name, value)
    if normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


def _quantize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = decimal_value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if value != value.lower():
        raise ValueError(f"{field_name} must be lowercase")
    _reject_unsafe_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_member(
    field_name: str,
    value: str,
    allowed: tuple[str, ...],
    label: str,
) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be a {label}")


def _normalize_public_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for code in value:
        _require_canonical_string(field_name, code)
        if code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(code)
    return value


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for code in value:
        _require_member(field_name, code, allowed, "known reason code")
        if code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(code)
    return value


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{field_name} must be a sha256 digest")
    suffix = value.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
