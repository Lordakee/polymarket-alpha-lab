"""Pure paper-only candidate decision research priority reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_CANDIDATE_DECISION_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION = (
    "candidate-decision-research-priority-queue-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
QUANTUM = Decimal("0.000001")

BUCKETS = ("research_next", "watch", "block")
QUEUE_STATUSES = BUCKETS
NEXT_RESEARCH_ACTIONS = (
    "collect_missing_evidence",
    "refresh_sources",
    "repair_team_memory_before_research",
    "resolve_urgent_research",
    "review_blocking_flags",
    "stop_research_until_edge_recovers",
    "wait_for_cost_readiness",
    "watch_for_new_signal",
)
REPORT_REASON_CODE_PRIORITY = (
    "research_next_ready",
    "watch_research_later",
    "research_block",
    "missing_evidence_high",
    "resolution_urgent",
    "source_refresh_needed",
    "cost_drag_elevated",
    "liquidity_thin",
    "liquidity_cost_ready",
    "liquidity_cost_not_ready",
    "team_memory_not_ready",
    "team_memory_ready",
    "candidate_hard_flagged",
    "net_edge_nonpositive",
    "candidate_decision_research_priority_queue_empty",
)
EMPTY_REASON_CODE = "candidate_decision_research_priority_queue_empty"
PUBLIC_PAYLOAD_KEYS = (
    "config_version",
    "queue_status",
    "input_count",
    "research_next_count",
    "watch_count",
    "block_count",
    "highest_priority_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_TEXT_PARTS = (
    ("can", "didate", "_", "ref"),
    ("mar", "ket"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("source", "-", "ref", "://"),
    ("source", "_", "references"),
    ("u", "rl"),
    ("d", "sn"),
    ("ta", "ble"),
    ("wall", "et"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("pos", "ition"),
    ("si", "ze"),
    ("b", "uy"),
    ("se", "ll"),
    ("to", "ken"),
    ("pri", "vate"),
    ("sec", "ret"),
)


@dataclass(frozen=True)
class CandidateDecisionResearchPriorityQueueConfig:
    config_version: str
    research_next_score_floor: Decimal = Decimal("0.600000")
    expected_net_edge_score_ceiling: Decimal = Decimal("0.150000")
    minimum_net_edge_for_research: Decimal = Decimal("0.010000")
    urgent_resolution_seconds: Decimal = Decimal("86400.000000")
    stale_source_seconds: Decimal = Decimal("7200.000000")
    min_research_liquidity: Decimal = Decimal("100.000000")
    max_cost_drag_share: Decimal = Decimal("0.300000")
    block_cost_drag_share: Decimal = Decimal("0.750000")
    high_missing_evidence_score: Decimal = Decimal("0.600000")
    high_resolution_urgency_score: Decimal = Decimal("0.900000")
    liquidity_cost_ready_floor: Decimal = Decimal("0.750000")
    team_memory_ready_floor: Decimal = Decimal("0.700000")
    team_memory_block_floor: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "research_next_score_floor",
            "high_missing_evidence_score",
            "high_resolution_urgency_score",
            "liquidity_cost_ready_floor",
            "team_memory_ready_floor",
            "team_memory_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_net_edge_score_ceiling",
            "urgent_resolution_seconds",
            "stale_source_seconds",
            "min_research_liquidity",
            "max_cost_drag_share",
            "block_cost_drag_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_net_edge_for_research",
            _normalize_decimal(
                "minimum_net_edge_for_research",
                self.minimum_net_edge_for_research,
            ),
        )
        if self.team_memory_block_floor >= self.team_memory_ready_floor:
            raise ValueError("team_memory_block_floor must be below team_memory_ready_floor")
        if self.max_cost_drag_share >= self.block_cost_drag_share:
            raise ValueError("max_cost_drag_share must be below block_cost_drag_share")
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateDecisionResearchCandidateAggregate:
    candidate_reference: str
    market_id: str
    question: str
    source_references: tuple[str, ...]
    expected_gross_edge: Decimal
    expected_cost_drag: Decimal
    missing_evidence_score: Decimal
    resolution_seconds: Decimal
    source_age_seconds: Decimal
    available_liquidity: Decimal
    team_memory_readiness_score: Decimal
    missing_evidence_codes: tuple[str, ...]
    hard_block_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_id", self.market_id)
        _require_text("question", self.question)
        object.__setattr__(
            self,
            "source_references",
            _normalize_texts("source_references", self.source_references),
        )
        object.__setattr__(
            self,
            "expected_gross_edge",
            _normalize_decimal("expected_gross_edge", self.expected_gross_edge),
        )
        for field_name in (
            "expected_cost_drag",
            "resolution_seconds",
            "source_age_seconds",
            "available_liquidity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_evidence_score",
            _normalize_ratio("missing_evidence_score", self.missing_evidence_score),
        )
        object.__setattr__(
            self,
            "team_memory_readiness_score",
            _normalize_ratio(
                "team_memory_readiness_score",
                self.team_memory_readiness_score,
            ),
        )
        object.__setattr__(
            self,
            "missing_evidence_codes",
            _normalize_reason_codes(
                "missing_evidence_codes",
                self.missing_evidence_codes,
            ),
        )
        object.__setattr__(
            self,
            "hard_block_reason_codes",
            _normalize_reason_codes(
                "hard_block_reason_codes",
                self.hard_block_reason_codes,
                require_sorted=True,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateDecisionResearchPriorityQueueRow:
    research_rank: Decimal
    redacted_candidate_reference: str
    bucket: str
    priority_score: Decimal
    missing_evidence_score: Decimal
    expected_net_edge: Decimal
    resolution_urgency_score: Decimal
    source_refresh_priority_score: Decimal
    liquidity_cost_readiness_score: Decimal
    team_memory_readiness_score: Decimal
    cost_drag_share: Decimal
    available_liquidity: Decimal
    next_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "research_rank",
            _normalize_positive_count("research_rank", self.research_rank),
        )
        _require_canonical_string(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_bucket("bucket", self.bucket)
        for field_name in (
            "priority_score",
            "missing_evidence_score",
            "resolution_urgency_score",
            "source_refresh_priority_score",
            "liquidity_cost_readiness_score",
            "team_memory_readiness_score",
            "cost_drag_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_net_edge",
            _normalize_decimal("expected_net_edge", self.expected_net_edge),
        )
        object.__setattr__(
            self,
            "available_liquidity",
            _normalize_nonnegative_decimal(
                "available_liquidity",
                self.available_liquidity,
            ),
        )
        _require_next_research_action(
            "next_research_action",
            self.next_research_action,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                require_nonempty=True,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateDecisionResearchPriorityQueueReport:
    config_version: str
    queue_status: str
    input_count: Decimal
    research_next_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[CandidateDecisionResearchPriorityQueueRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_queue_status("queue_status", self.queue_status)
        for field_name in (
            "input_count",
            "research_next_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_ratio("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class _UnrankedPriorityRow:
    redacted_candidate_reference: str
    bucket: str
    priority_score: Decimal
    missing_evidence_score: Decimal
    expected_net_edge: Decimal
    resolution_seconds: Decimal
    resolution_urgency_score: Decimal
    source_age_seconds: Decimal
    source_refresh_priority_score: Decimal
    liquidity_cost_readiness_score: Decimal
    team_memory_readiness_score: Decimal
    cost_drag_share: Decimal
    available_liquidity: Decimal
    next_research_action: str
    reason_codes: tuple[str, ...]


def build_candidate_decision_research_priority_queue(
    candidates: Iterable[CandidateDecisionResearchCandidateAggregate],
    *,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> CandidateDecisionResearchPriorityQueueReport:
    """Rank supplied paper candidate aggregates for human research triage."""

    if type(config) is not CandidateDecisionResearchPriorityQueueConfig:
        raise ValueError(
            "config must be a CandidateDecisionResearchPriorityQueueConfig",
        )
    _require_hard_flags(config)
    source_candidates = _normalize_candidates(candidates)
    unranked_rows = tuple(_unranked_row(candidate, config) for candidate in source_candidates)
    rows = tuple(
        CandidateDecisionResearchPriorityQueueRow(
            research_rank=_count_decimal(index),
            redacted_candidate_reference=row.redacted_candidate_reference,
            bucket=row.bucket,
            priority_score=row.priority_score,
            missing_evidence_score=row.missing_evidence_score,
            expected_net_edge=row.expected_net_edge,
            resolution_urgency_score=row.resolution_urgency_score,
            source_refresh_priority_score=row.source_refresh_priority_score,
            liquidity_cost_readiness_score=row.liquidity_cost_readiness_score,
            team_memory_readiness_score=row.team_memory_readiness_score,
            cost_drag_share=row.cost_drag_share,
            available_liquidity=row.available_liquidity,
            next_research_action=row.next_research_action,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(unranked_rows, key=_unranked_sort_key), start=1)
    )
    return CandidateDecisionResearchPriorityQueueReport(
        config_version=config.config_version,
        queue_status=_queue_status(rows),
        input_count=_count_decimal(len(source_candidates)),
        research_next_count=_bucket_count(rows, "research_next"),
        watch_count=_bucket_count(rows, "watch"),
        block_count=_bucket_count(rows, "block"),
        highest_priority_score=rows[0].priority_score if rows else ZERO.quantize(QUANTUM),
        rows=rows,
        reason_codes=_combined_report_reason_codes(rows),
    )


def candidate_decision_research_priority_queue_payload(
    report: CandidateDecisionResearchPriorityQueueReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionResearchPriorityQueueReport:
        raise ValueError(
            "report must be a CandidateDecisionResearchPriorityQueueReport",
        )
    _require_hard_flags(report)
    payload = {
        "config_version": report.config_version,
        "queue_status": report.queue_status,
        "input_count": _decimal_string(report.input_count),
        "research_next_count": _decimal_string(report.research_next_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "highest_priority_score": _decimal_string(report.highest_priority_score),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    _require_safe_public_payload(payload)
    return payload


def _unranked_row(
    candidate: CandidateDecisionResearchCandidateAggregate,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> _UnrankedPriorityRow:
    expected_net_edge = _normalize_decimal(
        "expected_net_edge",
        candidate.expected_gross_edge - candidate.expected_cost_drag,
    )
    cost_drag_share = _cost_drag_share(candidate)
    resolution_urgency_score = _resolution_urgency_score(candidate, config)
    source_refresh_priority_score = _source_refresh_priority_score(candidate, config)
    liquidity_cost_readiness_score = _liquidity_cost_readiness_score(candidate, config)
    priority_score = _priority_score(
        missing_evidence_score=candidate.missing_evidence_score,
        expected_net_edge=expected_net_edge,
        resolution_urgency_score=resolution_urgency_score,
        source_refresh_priority_score=source_refresh_priority_score,
        liquidity_cost_readiness_score=liquidity_cost_readiness_score,
        team_memory_readiness_score=candidate.team_memory_readiness_score,
        config=config,
    )
    bucket = _bucket(
        candidate=candidate,
        expected_net_edge=expected_net_edge,
        cost_drag_share=cost_drag_share,
        liquidity_cost_readiness_score=liquidity_cost_readiness_score,
        priority_score=priority_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        candidate=candidate,
        expected_net_edge=expected_net_edge,
        cost_drag_share=cost_drag_share,
        resolution_urgency_score=resolution_urgency_score,
        source_refresh_priority_score=source_refresh_priority_score,
        liquidity_cost_readiness_score=liquidity_cost_readiness_score,
        config=config,
    )
    return _UnrankedPriorityRow(
        redacted_candidate_reference=_redacted_candidate_reference(
            candidate.candidate_reference,
        ),
        bucket=bucket,
        priority_score=priority_score,
        missing_evidence_score=candidate.missing_evidence_score,
        expected_net_edge=expected_net_edge,
        resolution_seconds=candidate.resolution_seconds,
        resolution_urgency_score=resolution_urgency_score,
        source_age_seconds=candidate.source_age_seconds,
        source_refresh_priority_score=source_refresh_priority_score,
        liquidity_cost_readiness_score=liquidity_cost_readiness_score,
        team_memory_readiness_score=candidate.team_memory_readiness_score,
        cost_drag_share=cost_drag_share,
        available_liquidity=candidate.available_liquidity,
        next_research_action=_next_research_action(
            candidate=candidate,
            expected_net_edge=expected_net_edge,
            cost_drag_share=cost_drag_share,
            liquidity_cost_readiness_score=liquidity_cost_readiness_score,
            reason_codes=reason_codes,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _priority_score(
    *,
    missing_evidence_score: Decimal,
    expected_net_edge: Decimal,
    resolution_urgency_score: Decimal,
    source_refresh_priority_score: Decimal,
    liquidity_cost_readiness_score: Decimal,
    team_memory_readiness_score: Decimal,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> Decimal:
    net_edge_score = _clamp_ratio(
        expected_net_edge / config.expected_net_edge_score_ceiling,
    )
    return _normalize_ratio(
        "priority_score",
        (missing_evidence_score * Decimal("0.300000"))
        + (net_edge_score * Decimal("0.250000"))
        + (resolution_urgency_score * Decimal("0.150000"))
        + (source_refresh_priority_score * Decimal("0.100000"))
        + (liquidity_cost_readiness_score * Decimal("0.100000"))
        + (team_memory_readiness_score * Decimal("0.100000")),
    )


def _bucket(
    *,
    candidate: CandidateDecisionResearchCandidateAggregate,
    expected_net_edge: Decimal,
    cost_drag_share: Decimal,
    liquidity_cost_readiness_score: Decimal,
    priority_score: Decimal,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> str:
    if candidate.hard_block_reason_codes:
        return "block"
    if candidate.team_memory_readiness_score < config.team_memory_block_floor:
        return "block"
    if expected_net_edge <= ZERO:
        return "block"
    if cost_drag_share >= config.block_cost_drag_share:
        return "block"
    if expected_net_edge < config.minimum_net_edge_for_research:
        return "watch"
    if candidate.available_liquidity < config.min_research_liquidity:
        return "watch"
    if cost_drag_share > config.max_cost_drag_share:
        return "watch"
    if liquidity_cost_readiness_score < config.liquidity_cost_ready_floor:
        return "watch"
    if priority_score >= config.research_next_score_floor:
        return "research_next"
    return "watch"


def _row_reason_codes(
    *,
    candidate: CandidateDecisionResearchCandidateAggregate,
    expected_net_edge: Decimal,
    cost_drag_share: Decimal,
    resolution_urgency_score: Decimal,
    source_refresh_priority_score: Decimal,
    liquidity_cost_readiness_score: Decimal,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(candidate.missing_evidence_codes)
    reason_codes.extend(candidate.hard_block_reason_codes)
    if candidate.hard_block_reason_codes:
        reason_codes.append("candidate_hard_flagged")
    if candidate.missing_evidence_score >= config.high_missing_evidence_score:
        reason_codes.append("missing_evidence_high")
    elif candidate.missing_evidence_score > ZERO:
        reason_codes.append("missing_evidence_present")
    if expected_net_edge > ZERO:
        reason_codes.append("net_edge_positive")
    else:
        reason_codes.append("net_edge_nonpositive")
    if resolution_urgency_score >= config.high_resolution_urgency_score:
        reason_codes.append("resolution_urgent")
    if source_refresh_priority_score >= ONE:
        reason_codes.append("source_refresh_needed")
    if candidate.available_liquidity < config.min_research_liquidity:
        reason_codes.append("liquidity_thin")
    if cost_drag_share > config.max_cost_drag_share:
        reason_codes.append("cost_drag_elevated")
    if liquidity_cost_readiness_score >= config.liquidity_cost_ready_floor:
        reason_codes.append("liquidity_cost_ready")
    else:
        reason_codes.append("liquidity_cost_not_ready")
    if candidate.team_memory_readiness_score < config.team_memory_block_floor:
        reason_codes.append("team_memory_not_ready")
    elif candidate.team_memory_readiness_score >= config.team_memory_ready_floor:
        reason_codes.append("team_memory_ready")
    else:
        reason_codes.append("team_memory_partial")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), require_nonempty=True)


def _next_research_action(
    *,
    candidate: CandidateDecisionResearchCandidateAggregate,
    expected_net_edge: Decimal,
    cost_drag_share: Decimal,
    liquidity_cost_readiness_score: Decimal,
    reason_codes: tuple[str, ...],
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> str:
    if candidate.team_memory_readiness_score < config.team_memory_block_floor:
        return "repair_team_memory_before_research"
    if candidate.hard_block_reason_codes:
        return "review_blocking_flags"
    if expected_net_edge <= ZERO:
        return "stop_research_until_edge_recovers"
    if (
        candidate.available_liquidity < config.min_research_liquidity
        or cost_drag_share > config.max_cost_drag_share
        or liquidity_cost_readiness_score < config.liquidity_cost_ready_floor
    ):
        return "wait_for_cost_readiness"
    if "missing_evidence_high" in reason_codes:
        return "collect_missing_evidence"
    if "source_refresh_needed" in reason_codes:
        return "refresh_sources"
    if "resolution_urgent" in reason_codes:
        return "resolve_urgent_research"
    return "watch_for_new_signal"


def _cost_drag_share(candidate: CandidateDecisionResearchCandidateAggregate) -> Decimal:
    if candidate.expected_gross_edge > ZERO:
        return _normalize_ratio(
            "cost_drag_share",
            _clamp_ratio(candidate.expected_cost_drag / candidate.expected_gross_edge),
        )
    if candidate.expected_cost_drag > ZERO:
        return ONE.quantize(QUANTUM)
    return ZERO.quantize(QUANTUM)


def _resolution_urgency_score(
    candidate: CandidateDecisionResearchCandidateAggregate,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> Decimal:
    return _normalize_ratio(
        "resolution_urgency_score",
        ONE - _clamp_ratio(candidate.resolution_seconds / config.urgent_resolution_seconds),
    )


def _source_refresh_priority_score(
    candidate: CandidateDecisionResearchCandidateAggregate,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> Decimal:
    return _normalize_ratio(
        "source_refresh_priority_score",
        _clamp_ratio(candidate.source_age_seconds / config.stale_source_seconds),
    )


def _liquidity_cost_readiness_score(
    candidate: CandidateDecisionResearchCandidateAggregate,
    config: CandidateDecisionResearchPriorityQueueConfig,
) -> Decimal:
    liquidity_score = _clamp_ratio(
        candidate.available_liquidity / config.min_research_liquidity,
    )
    cost_score = ONE - _clamp_ratio(_cost_drag_share(candidate) / config.max_cost_drag_share)
    return _normalize_ratio(
        "liquidity_cost_readiness_score",
        (liquidity_score + cost_score) / TWO,
    )


def _unranked_sort_key(row: _UnrankedPriorityRow) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        _bucket_sort_rank(row.bucket),
        -row.priority_score,
        -row.missing_evidence_score,
        -row.expected_net_edge,
        row.resolution_seconds,
        -row.source_age_seconds,
        row.redacted_candidate_reference,
    )


def _queue_item_sort_key(
    row: CandidateDecisionResearchPriorityQueueRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        _bucket_sort_rank(row.bucket),
        -row.priority_score,
        -row.missing_evidence_score,
        -row.expected_net_edge,
        row.redacted_candidate_reference,
    )


def _bucket_sort_rank(bucket: str) -> int:
    if bucket == "research_next":
        return 0
    if bucket == "watch":
        return 1
    return 2


def _queue_status(
    rows: tuple[CandidateDecisionResearchPriorityQueueRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.bucket == "block" for row in rows):
        return "block"
    if any(row.bucket == "research_next" for row in rows):
        return "research_next"
    return "watch"


def _combined_report_reason_codes(
    rows: tuple[CandidateDecisionResearchPriorityQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    if any(row.bucket == "research_next" for row in rows):
        found.add("research_next_ready")
    if any(row.bucket == "watch" for row in rows):
        found.add("watch_research_later")
    if any(row.bucket == "block" for row in rows):
        found.add("research_block")
    return tuple(reason_code for reason_code in REPORT_REASON_CODE_PRIORITY if reason_code in found)


def _require_safe_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("unsafe public payload must be a dict")
    if tuple(payload.keys()) != PUBLIC_PAYLOAD_KEYS:
        raise ValueError("unsafe public payload fields")
    for key, value in payload.items():
        if key == "reason_codes":
            _require_safe_public_payload_reason_codes(value)
            continue
        if isinstance(value, str):
            _require_safe_public_payload_text(value)
        elif type(value) is bool:
            continue
        elif type(value) is not str:
            raise ValueError("unsafe public payload value")


def _require_safe_public_payload_reason_codes(value: object) -> None:
    if type(value) is not list:
        raise ValueError("unsafe public payload reason_codes")
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("unsafe public payload reason_codes")
        if reason_code not in REPORT_REASON_CODE_PRIORITY:
            raise ValueError("unsafe public payload reason_codes")
        _require_safe_public_payload_text(reason_code)


def _require_safe_public_payload_text(value: str) -> None:
    lowered = value.lower()
    for parts in UNSAFE_PUBLIC_TEXT_PARTS:
        if "".join(parts) in lowered:
            raise ValueError("unsafe public payload text")


def _normalize_candidates(
    candidates: Iterable[CandidateDecisionResearchCandidateAggregate],
) -> tuple[CandidateDecisionResearchCandidateAggregate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_references: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not CandidateDecisionResearchCandidateAggregate:
            raise ValueError(
                "candidates must contain CandidateDecisionResearchCandidateAggregate",
            )
        _require_hard_flags(candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("candidates must not contain duplicate candidate_reference")
        seen_references.add(candidate.candidate_reference)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionResearchPriorityQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_references: set[str] = set()
    for row in normalized:
        if type(row) is not CandidateDecisionResearchPriorityQueueRow:
            raise ValueError(
                "rows must contain CandidateDecisionResearchPriorityQueueRow values",
            )
        _require_hard_flags(row)
        if row.redacted_candidate_reference in seen_references:
            raise ValueError("rows must not contain duplicate redacted_candidate_reference")
        seen_references.add(row.redacted_candidate_reference)
    return normalized


def _validate_report(report: CandidateDecisionResearchPriorityQueueReport) -> None:
    if report.input_count < _count_decimal(len(report.rows)):
        raise ValueError("input_count must be >= rows")
    if report.research_next_count != _bucket_count(report.rows, "research_next"):
        raise ValueError("research_next_count must match rows")
    if report.watch_count != _bucket_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _bucket_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if (
        report.research_next_count + report.watch_count + report.block_count
        != _count_decimal(len(report.rows))
    ):
        raise ValueError("bucket counts must match rows")
    if tuple(row.research_rank for row in report.rows) != tuple(
        _count_decimal(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("research_rank values must be contiguous")
    if tuple(sorted(report.rows, key=_queue_item_sort_key)) != report.rows:
        raise ValueError("rows must follow deterministic sequence")
    if report.queue_status != _queue_status(report.rows):
        raise ValueError("queue_status must match rows")
    expected_highest = report.rows[0].priority_score if report.rows else ZERO.quantize(QUANTUM)
    if report.highest_priority_score != expected_highest:
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _combined_report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _bucket_count(
    rows: tuple[CandidateDecisionResearchPriorityQueueRow, ...],
    bucket: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.bucket == bucket))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _redacted_candidate_reference(candidate_reference: str) -> str:
    digest = sha256(candidate_reference.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    require_nonempty: bool = False,
    require_sorted: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if require_sorted and tuple(normalized) != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    sorted_codes = tuple(sorted(normalized))
    if require_nonempty and not sorted_codes:
        raise ValueError(f"{field_name} must not be empty")
    return sorted_codes


def _normalize_texts(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        texts = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for text in texts:
        _require_text(field_name, text)
    return texts


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty text without edge whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain only canonical characters")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if "-" in value:
        raise ValueError(f"{field_name} must use underscores")


def _require_bucket(field_name: str, value: object) -> None:
    if value not in BUCKETS:
        raise ValueError(f"{field_name} must be one of {BUCKETS}")


def _require_queue_status(field_name: str, value: object) -> None:
    if value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be one of {QUEUE_STATUSES}")


def _require_next_research_action(field_name: str, value: object) -> None:
    if value not in NEXT_RESEARCH_ACTIONS:
        raise ValueError(f"{field_name} must be one of {NEXT_RESEARCH_ACTIONS}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO.quantize(QUANTUM)
    if value >= ONE:
        return ONE.quantize(QUANTUM)
    return value.quantize(QUANTUM)


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION",
    "CandidateDecisionResearchCandidateAggregate",
    "CandidateDecisionResearchPriorityQueueConfig",
    "CandidateDecisionResearchPriorityQueueReport",
    "CandidateDecisionResearchPriorityQueueRow",
    "build_candidate_decision_research_priority_queue",
    "candidate_decision_research_priority_queue_payload",
)
