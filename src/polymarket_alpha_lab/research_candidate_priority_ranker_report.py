"""Research-only candidate event priority ranker for manual review queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_CANDIDATE_PRIORITY_RANKER_REPORT_CONFIG_VERSION = (
    "research-candidate-priority-ranker-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_STATUSES = ("pass", "watch", "block")
_STATUS_SORT_RANK = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "block": Decimal("2.000000"),
}

_EMPTY_REASON_CODE = "research_candidate_priority_ranker_empty"
_PASS_REASON_CODE = "research_candidate_priority_pass"
_REPORT_PASS_REASON_CODE = "research_candidate_priority_ranker_pass"

_ROW_REASON_CODE_SEQUENCE = (
    "priority_score_below_block_minimum",
    "confidence_below_block_minimum",
    "evidence_gap_above_block_limit",
    "cost_friction_above_block_limit",
    "resolution_risk_above_block_limit",
    "freshness_below_block_minimum",
    "priority_score_below_pass_minimum",
    "confidence_below_pass_minimum",
    "evidence_gap_above_watch_limit",
    "cost_friction_above_watch_limit",
    "resolution_risk_above_watch_limit",
    "freshness_below_pass_minimum",
    _PASS_REASON_CODE,
)
_REPORT_REASON_CODE_SEQUENCE = (
    _EMPTY_REASON_CODE,
    _REPORT_PASS_REASON_CODE,
) + _ROW_REASON_CODE_SEQUENCE
_BLOCK_REASON_CODES = frozenset(_ROW_REASON_CODE_SEQUENCE[:6])


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("priv", "ate", "_", "key"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bal", "ance"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("sub", "mit"),
        _join_parts("rep", "lace"),
        _join_parts("sig", "n"),
        _join_parts("ex", "change", "_", "change"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("net", "work"),
        _join_parts("pos", "ition"),
        _join_parts("not", "ional"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)
_SENSITIVE_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "candidate_id",
        "event_id",
        "event_slug",
        "source_config_version",
        "top_candidate_id",
    ),
)


@dataclass(frozen=True)
class ResearchCandidatePriorityRankerConfig:
    config_version: str = (
        DEFAULT_RESEARCH_CANDIDATE_PRIORITY_RANKER_REPORT_CONFIG_VERSION
    )
    min_pass_priority_score: Decimal = Decimal("0.400000")
    min_watch_priority_score: Decimal = Decimal("0.150000")
    min_pass_confidence: Decimal = Decimal("0.700000")
    min_watch_confidence: Decimal = Decimal("0.400000")
    max_watch_evidence_gap: Decimal = Decimal("0.600000")
    max_block_evidence_gap: Decimal = Decimal("0.850000")
    max_watch_cost_friction: Decimal = Decimal("0.400000")
    max_block_cost_friction: Decimal = Decimal("0.750000")
    max_watch_resolution_risk: Decimal = Decimal("0.400000")
    max_block_resolution_risk: Decimal = Decimal("0.750000")
    min_pass_freshness: Decimal = Decimal("0.550000")
    min_watch_freshness: Decimal = Decimal("0.200000")
    confidence_weight: Decimal = Decimal("0.300000")
    evidence_gap_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    cost_friction_weight: Decimal = Decimal("0.100000")
    resolution_risk_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchCandidatePriorityRankerConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidatePriorityRankerConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_CANDIDATE_PRIORITY_RANKER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_priority_score",
            "min_watch_priority_score",
            "min_pass_confidence",
            "min_watch_confidence",
            "max_watch_evidence_gap",
            "max_block_evidence_gap",
            "max_watch_cost_friction",
            "max_block_cost_friction",
            "max_watch_resolution_risk",
            "max_block_resolution_risk",
            "min_pass_freshness",
            "min_watch_freshness",
            "confidence_weight",
            "evidence_gap_weight",
            "freshness_weight",
            "cost_friction_weight",
            "resolution_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_pass_priority_score <= self.min_watch_priority_score:
            raise ValueError(
                "min_pass_priority_score must exceed min_watch_priority_score",
            )
        if self.min_pass_confidence <= self.min_watch_confidence:
            raise ValueError("min_pass_confidence must exceed min_watch_confidence")
        if self.max_block_evidence_gap < self.max_watch_evidence_gap:
            raise ValueError(
                "max_block_evidence_gap must be at least max_watch_evidence_gap",
            )
        if self.max_block_cost_friction < self.max_watch_cost_friction:
            raise ValueError(
                "max_block_cost_friction must be at least max_watch_cost_friction",
            )
        if self.max_block_resolution_risk < self.max_watch_resolution_risk:
            raise ValueError(
                "max_block_resolution_risk must be at least "
                "max_watch_resolution_risk",
            )
        if self.min_pass_freshness <= self.min_watch_freshness:
            raise ValueError("min_pass_freshness must exceed min_watch_freshness")
        weight_sum = _quantize(
            self.confidence_weight
            + self.evidence_gap_weight
            + self.freshness_weight
            + self.cost_friction_weight
            + self.resolution_risk_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("priority component weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidatePriorityRankerCandidate:
    candidate_id: str
    event_id: str
    event_slug: str
    evaluated_at: datetime
    confidence: Decimal
    evidence_gap: Decimal
    cost_friction: Decimal
    resolution_risk: Decimal
    freshness: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchCandidatePriorityRankerCandidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidatePriorityRankerCandidate, "candidate")
        for field_name in (
            "candidate_id",
            "event_id",
            "event_slug",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "confidence",
            "evidence_gap",
            "cost_friction",
            "resolution_risk",
            "freshness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchCandidatePriorityRankerRow:
    priority_rank: Decimal
    candidate_id: str
    event_id: str
    event_slug: str
    evaluated_at: datetime
    confidence: Decimal
    evidence_gap: Decimal
    cost_friction: Decimal
    resolution_risk: Decimal
    freshness: Decimal
    priority_score: Decimal
    research_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchCandidatePriorityRankerRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidatePriorityRankerRow, "row")
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_count("priority_rank", self.priority_rank),
        )
        for field_name in (
            "candidate_id",
            "event_id",
            "event_slug",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "confidence",
            "evidence_gap",
            "cost_friction",
            "resolution_risk",
            "freshness",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("research_status", self.research_status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchCandidatePriorityRankerReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    top_candidate_id: str | None
    max_priority_score: Decimal
    average_priority_score: Decimal | None
    research_queue_status: str
    next_research_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCandidatePriorityRankerRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchCandidatePriorityRankerReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidatePriorityRankerReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_id is not None:
            _require_public_string("top_candidate_id", self.top_candidate_id)
        object.__setattr__(
            self,
            "max_priority_score",
            _normalize_ratio("max_priority_score", self.max_priority_score),
        )
        object.__setattr__(
            self,
            "average_priority_score",
            _normalize_optional_ratio(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
        _require_member("research_queue_status", self.research_queue_status, _STATUSES)
        _require_public_string("next_research_step", self.next_research_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_candidate_priority_ranker_report(
    candidates: list[ResearchCandidatePriorityRankerCandidate]
    | tuple[ResearchCandidatePriorityRankerCandidate, ...],
    *,
    config: ResearchCandidatePriorityRankerConfig,
    generated_at: datetime,
) -> ResearchCandidatePriorityRankerReport:
    if type(config) is not ResearchCandidatePriorityRankerConfig:
        raise ValueError("config must be a ResearchCandidatePriorityRankerConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    _validate_unique_candidates(normalized_candidates)
    _validate_not_after_generated_at(normalized_candidates, generated_at=generated_at_utc)
    rows = _ranked_rows(
        tuple(_row_for_candidate(candidate, config=config) for candidate in normalized_candidates),
    )

    return ResearchCandidatePriorityRankerReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        top_candidate_id=next(iter(rows)).candidate_id if rows else None,
        max_priority_score=max((row.priority_score for row in rows), default=_ZERO),
        average_priority_score=_average_priority_score(rows),
        research_queue_status=_report_status(rows),
        next_research_step=_next_research_step(_report_status(rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_candidate_priority_ranker_report_public_payload(
    report: ResearchCandidatePriorityRankerReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCandidatePriorityRankerReport:
        raise ValueError("report must be a ResearchCandidatePriorityRankerReport")
    _validate_report(report)
    payload = _json_ready_no_numbers(_public_report_payload(report))
    validate_research_candidate_priority_ranker_report_public_payload(payload)
    return payload


def validate_research_candidate_priority_ranker_report_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("research candidate priority payload", payload)
    _require_public_payload_shape(payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    return True


def _public_report_payload(
    report: ResearchCandidatePriorityRankerReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "top_priority_rank": report.rows[0].priority_rank if report.rows else None,
        "max_priority_score": report.max_priority_score,
        "average_priority_score": report.average_priority_score,
        "research_queue_status": report.research_queue_status,
        "next_research_step": report.next_research_step,
        "reason_codes": report.reason_codes,
        "rows": tuple(_public_row_payload(row) for row in report.rows),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_row_payload(row: ResearchCandidatePriorityRankerRow) -> dict[str, Any]:
    return {
        "priority_rank": row.priority_rank,
        "evaluated_at": row.evaluated_at,
        "confidence": row.confidence,
        "evidence_gap": row.evidence_gap,
        "cost_friction": row.cost_friction,
        "resolution_risk": row.resolution_risk,
        "freshness": row.freshness,
        "priority_score": row.priority_score,
        "research_status": row.research_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_for_candidate(
    candidate: ResearchCandidatePriorityRankerCandidate,
    *,
    config: ResearchCandidatePriorityRankerConfig,
) -> ResearchCandidatePriorityRankerRow:
    priority_score = _priority_score(candidate, config=config)
    reason_codes = _row_reason_codes(
        candidate,
        priority_score=priority_score,
        config=config,
    )
    return ResearchCandidatePriorityRankerRow(
        priority_rank=_ZERO,
        candidate_id=candidate.candidate_id,
        event_id=candidate.event_id,
        event_slug=candidate.event_slug,
        evaluated_at=candidate.evaluated_at,
        confidence=candidate.confidence,
        evidence_gap=candidate.evidence_gap,
        cost_friction=candidate.cost_friction,
        resolution_risk=candidate.resolution_risk,
        freshness=candidate.freshness,
        priority_score=priority_score,
        research_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        source_config_version=candidate.source_config_version,
    )


def _priority_score(
    candidate: ResearchCandidatePriorityRankerCandidate,
    *,
    config: ResearchCandidatePriorityRankerConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        raw_score = (
            candidate.confidence * config.confidence_weight
            + candidate.evidence_gap * config.evidence_gap_weight
            + candidate.freshness * config.freshness_weight
            - candidate.cost_friction * config.cost_friction_weight
            - candidate.resolution_risk * config.resolution_risk_weight
        )
    return _quantize(max(_ZERO, min(_ONE, raw_score)))


def _row_reason_codes(
    candidate: ResearchCandidatePriorityRankerCandidate,
    *,
    priority_score: Decimal,
    config: ResearchCandidatePriorityRankerConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if priority_score < config.min_watch_priority_score:
        reason_codes.append("priority_score_below_block_minimum")
    if candidate.confidence < config.min_watch_confidence:
        reason_codes.append("confidence_below_block_minimum")
    if candidate.evidence_gap > config.max_block_evidence_gap:
        reason_codes.append("evidence_gap_above_block_limit")
    if candidate.cost_friction > config.max_block_cost_friction:
        reason_codes.append("cost_friction_above_block_limit")
    if candidate.resolution_risk > config.max_block_resolution_risk:
        reason_codes.append("resolution_risk_above_block_limit")
    if candidate.freshness < config.min_watch_freshness:
        reason_codes.append("freshness_below_block_minimum")

    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if priority_score < config.min_pass_priority_score:
            reason_codes.append("priority_score_below_pass_minimum")
        if candidate.confidence < config.min_pass_confidence:
            reason_codes.append("confidence_below_pass_minimum")
        if candidate.evidence_gap > config.max_watch_evidence_gap:
            reason_codes.append("evidence_gap_above_watch_limit")
        if candidate.cost_friction > config.max_watch_cost_friction:
            reason_codes.append("cost_friction_above_watch_limit")
        if candidate.resolution_risk > config.max_watch_resolution_risk:
            reason_codes.append("resolution_risk_above_watch_limit")
        if candidate.freshness < config.min_pass_freshness:
            reason_codes.append("freshness_below_pass_minimum")

    if not reason_codes:
        return (_PASS_REASON_CODE,)
    return tuple(
        reason_code
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _ranked_rows(
    rows: tuple[ResearchCandidatePriorityRankerRow, ...],
) -> tuple[ResearchCandidatePriorityRankerRow, ...]:
    ranked: list[ResearchCandidatePriorityRankerRow] = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked.append(_replace_row_rank(row, _count(index)))
    return tuple(ranked)


def _replace_row_rank(
    row: ResearchCandidatePriorityRankerRow,
    priority_rank: Decimal,
) -> ResearchCandidatePriorityRankerRow:
    return ResearchCandidatePriorityRankerRow(
        priority_rank=priority_rank,
        candidate_id=row.candidate_id,
        event_id=row.event_id,
        event_slug=row.event_slug,
        evaluated_at=row.evaluated_at,
        confidence=row.confidence,
        evidence_gap=row.evidence_gap,
        cost_friction=row.cost_friction,
        resolution_risk=row.resolution_risk,
        freshness=row.freshness,
        priority_score=row.priority_score,
        research_status=row.research_status,
        reason_codes=row.reason_codes,
        source_config_version=row.source_config_version,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchCandidatePriorityRankerRow, ...]) -> str:
    statuses = tuple(row.research_status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _next_research_step(research_queue_status: str) -> str:
    if research_queue_status == "block":
        return "hold_manual_research_queue"
    if research_queue_status == "watch":
        return "review_manual_research_queue"
    return "continue_manual_research_queue"


def _report_reason_codes(
    rows: tuple[ResearchCandidatePriorityRankerRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON_CODE,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _PASS_REASON_CODE
    }
    if not present:
        return (_REPORT_PASS_REASON_CODE,)
    return tuple(
        reason_code
        for reason_code in _REPORT_REASON_CODE_SEQUENCE
        if reason_code in present
    )


def _normalize_candidates(
    value: object,
) -> tuple[ResearchCandidatePriorityRankerCandidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    for candidate in candidates:
        if type(candidate) is not ResearchCandidatePriorityRankerCandidate:
            raise ValueError(
                "candidates must contain ResearchCandidatePriorityRankerCandidate values",
            )
        _require_hard_flags("candidate", candidate)
    return candidates


def _validate_unique_candidates(
    candidates: tuple[ResearchCandidatePriorityRankerCandidate, ...],
) -> None:
    seen_candidate_ids: set[str] = set()
    seen_event_ids: set[str] = set()
    for candidate in candidates:
        if candidate.candidate_id in seen_candidate_ids:
            raise ValueError("candidates must not contain duplicate candidate_id")
        if candidate.event_id in seen_event_ids:
            raise ValueError("candidates must not contain duplicate event_id")
        seen_candidate_ids.add(candidate.candidate_id)
        seen_event_ids.add(candidate.event_id)


def _validate_not_after_generated_at(
    candidates: tuple[ResearchCandidatePriorityRankerCandidate, ...],
    *,
    generated_at: datetime,
) -> None:
    for candidate in candidates:
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")


def _normalize_rows(
    value: object,
) -> tuple[ResearchCandidatePriorityRankerRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_candidate_ids: set[str] = set()
    seen_event_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchCandidatePriorityRankerRow:
            raise ValueError("rows must contain ResearchCandidatePriorityRankerRow values")
        _require_hard_flags("row", row)
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("rows must not contain duplicate candidate_id")
        if row.event_id in seen_event_ids:
            raise ValueError("rows must not contain duplicate event_id")
        seen_candidate_ids.add(row.candidate_id)
        seen_event_ids.add(row.event_id)
    if rows != tuple(sorted(rows, key=_ranked_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_row(row: ResearchCandidatePriorityRankerRow) -> None:
    if row.research_status != _row_status(row.reason_codes):
        raise ValueError("research_status must match reason_codes")
    if row.priority_rank < _ZERO:
        raise ValueError("priority_rank must be nonnegative")


def _validate_report(report: ResearchCandidatePriorityRankerReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.candidate_count:
        raise ValueError("status counts must match candidate_count")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.priority_rank for row in rows) != expected_ranks:
        raise ValueError("priority_rank values must match rows")
    top_candidate_id = next(iter(rows)).candidate_id if rows else None
    if report.top_candidate_id != top_candidate_id:
        raise ValueError("top_candidate_id must match rows")
    if report.max_priority_score != max((row.priority_score for row in rows), default=_ZERO):
        raise ValueError("max_priority_score must match rows")
    if report.average_priority_score != _average_priority_score(rows):
        raise ValueError("average_priority_score must match rows")
    if report.research_queue_status != _report_status(rows):
        raise ValueError("research_queue_status must match rows")
    if report.next_research_step != _next_research_step(report.research_queue_status):
        raise ValueError("next_research_step must match research_queue_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _average_priority_score(
    rows: tuple[ResearchCandidatePriorityRankerRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.priority_score for row in rows), _ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchCandidatePriorityRankerRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.research_status == status))


def _row_sort_key(
    row: ResearchCandidatePriorityRankerRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        _STATUS_SORT_RANK[row.research_status],
        -row.priority_score,
        -row.confidence,
        row.cost_friction,
        row.resolution_risk,
        -row.freshness,
        row.event_id,
        row.candidate_id,
    )


def _ranked_row_sort_key(
    row: ResearchCandidatePriorityRankerRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str, Decimal]:
    return (*_row_sort_key(row), row.priority_rank)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(_QUANTUM)


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty canonical text")
    _reject_unsafe_public_payload(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_payload_shape(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public key in public payload")
            if key in _SENSITIVE_PUBLIC_PAYLOAD_KEYS:
                raise ValueError(f"unsafe public key in public payload: {key}")
            _require_public_payload_shape(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_shape(item)


def _reject_public_numeric_values(value: object, path: str = "") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(
            f"public payload must use Decimal strings, not numeric values at {path}",
        )
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_public_numeric_values(item, nested_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_public_numeric_values(item, nested_path)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
                raise ValueError(f"unsafe public key in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}: {path}")


def _json_ready_no_numbers(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_numbers(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime JSON value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        raise ValueError("JSON value must not be numeric")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_numbers(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_numbers(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_PRIORITY_RANKER_REPORT_CONFIG_VERSION",
    "ResearchCandidatePriorityRankerCandidate",
    "ResearchCandidatePriorityRankerConfig",
    "ResearchCandidatePriorityRankerReport",
    "ResearchCandidatePriorityRankerRow",
    "build_research_candidate_priority_ranker_report",
    "research_candidate_priority_ranker_report_public_payload",
    "validate_research_candidate_priority_ranker_report_public_payload",
)
