import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.analytics_history import PaperAnalyticsHistoryReport
from polymarket_alpha_lab.domain import MarketScore
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceReport


__all__ = (
    "PaperManualReviewCandidate",
    "PaperManualReviewConfig",
    "PaperManualReviewLog",
    "PaperManualReviewQueue",
    "PaperManualReviewQueueItem",
    "build_paper_manual_review_queue",
)


DEFAULT_BOUNDARY_STATEMENT = (
    "This is a paper-only manual-review artifact for human inspection, "
    "not a trade instruction or order instruction."
)
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
NEGATIVE_ONE = Decimal("-1")
EVIDENCE_SCOPE = "portfolio_and_forecast_aggregate"
QUEUE_STATUSES = (
    "incomplete_data",
    "insufficient_evidence",
    "blocked_by_risk",
    "blocked_by_quality",
    "paper_review_ready",
)
STATUS_RANK = {
    "paper_review_ready": 0,
    "insufficient_evidence": 1,
    "blocked_by_quality": 2,
    "blocked_by_risk": 3,
    "incomplete_data": 4,
}
PRIMARY_REASON_CODES = frozenset(
    {
        "paper_evidence_ready",
        "needs_more_sample",
        "blocked_risk_drawdown",
        "blocked_forecast_quality",
        "incomplete_data",
        "below_source_score",
    }
)


@dataclass(frozen=True)
class PaperManualReviewConfig:
    config_version: str
    min_source_score: Decimal = Decimal("0.0000")
    min_ready_items: int = 1
    include_blocked_items: bool = True
    boundary_statement: str = DEFAULT_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("min_source_score", self.min_source_score)
        _require_nonnegative_int("min_ready_items", self.min_ready_items)
        if not isinstance(self.include_blocked_items, bool):
            raise ValueError("include_blocked_items must be a bool")
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class PaperManualReviewCandidate:
    queued_at: datetime
    packet_id: str
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    source_score: Decimal
    raw_archive_path: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    model_probability: Decimal | None
    expected_entry_price: Decimal | None
    fair_value_estimate: Decimal | None
    theoretical_edge: Decimal | None
    cost_adjusted_edge: Decimal | None
    confidence: Decimal | None
    max_executable_size: Decimal | None
    risk_gate_passed: bool
    risk_reason_codes: tuple[str, ...] = ()
    risk_reason_summary: str | None = None
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "queued_at", _as_utc(self.queued_at))
        for field_name in (
            "packet_id",
            "condition_id",
            "token_id",
            "market_slug",
            "question",
            "outcome_name",
            "raw_archive_path",
            "strategy_type",
            "thesis",
            "invalidating_conditions",
            "rule_text_hash",
            "resolution_source",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_optional_canonical_string("market_url", self.market_url, allow_empty=True)
        _require_nonnegative_decimal("source_score", self.source_score)
        for field_name in (
            "model_probability",
            "expected_entry_price",
            "fair_value_estimate",
            "theoretical_edge",
            "cost_adjusted_edge",
            "confidence",
            "max_executable_size",
        ):
            _require_optional_finite_decimal(field_name, getattr(self, field_name))
        if self.max_executable_size is not None and self.max_executable_size < ZERO:
            raise ValueError("max_executable_size must be nonnegative")
        object.__setattr__(self, "risk_tags", _normalize_string_tuple("risk_tags", self.risk_tags))
        object.__setattr__(
            self,
            "risk_reason_codes",
            _normalize_string_tuple("risk_reason_codes", self.risk_reason_codes),
        )
        if not isinstance(self.risk_gate_passed, bool):
            raise ValueError("risk_gate_passed must be a bool")
        if self.risk_gate_passed and self.risk_reason_codes != ():
            raise ValueError("risk_reason_codes must be empty when risk gate passes")
        if not self.risk_gate_passed and not self.risk_reason_codes:
            raise ValueError("risk_reason_codes are required when risk gate fails")
        if self.risk_reason_summary is not None:
            _require_canonical_string("risk_reason_summary", self.risk_reason_summary)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")


@dataclass(frozen=True)
class PaperManualReviewQueueItem:
    queue_item_id: str
    rank: int
    status: str
    status_rank: int
    hard_block_count: int
    evidence_pass_count: int
    source_score: Decimal
    market_score_total: Decimal | None
    queued_at: datetime
    packet_id: str
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    model_probability: Decimal | None
    expected_entry_price: Decimal | None
    fair_value_estimate: Decimal | None
    theoretical_edge: Decimal | None
    cost_adjusted_edge: Decimal | None
    confidence: Decimal | None
    max_executable_size: Decimal | None
    risk_gate_passed: bool
    risk_reason_codes: tuple[str, ...]
    history_status: str
    forecast_status: str
    history_gate_pass_count: int
    forecast_gate_pass_count: int
    history_gate_fail_count: int
    forecast_gate_fail_count: int
    readiness_summary: str
    risk_summary: str
    evidence_summary: str
    why_in_queue: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...]
    blocking_reason_codes: tuple[str, ...]
    review_focus: tuple[str, ...]
    evidence_scope: str
    boundary_statement: str
    paper_only: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("queue_item_id", self.queue_item_id)
        _require_positive_int("rank", self.rank)
        if self.status not in QUEUE_STATUSES:
            raise ValueError("status must be a known manual review status")
        if self.status_rank != STATUS_RANK[self.status]:
            raise ValueError("status_rank must match status")
        for field_name in (
            "hard_block_count",
            "evidence_pass_count",
            "history_gate_pass_count",
            "forecast_gate_pass_count",
            "history_gate_fail_count",
            "forecast_gate_fail_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_nonnegative_decimal("source_score", self.source_score)
        _require_optional_finite_decimal("market_score_total", self.market_score_total)
        object.__setattr__(self, "queued_at", _as_utc(self.queued_at))
        for field_name in (
            "packet_id",
            "condition_id",
            "token_id",
            "market_slug",
            "question",
            "outcome_name",
            "strategy_type",
            "thesis",
            "invalidating_conditions",
            "rule_text_hash",
            "resolution_source",
            "history_status",
            "forecast_status",
            "readiness_summary",
            "risk_summary",
            "evidence_summary",
            "why_in_queue",
            "evidence_scope",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_optional_canonical_string("market_url", self.market_url, allow_empty=True)
        if self.evidence_scope != EVIDENCE_SCOPE:
            raise ValueError("evidence_scope must be portfolio_and_forecast_aggregate")
        for field_name in (
            "model_probability",
            "expected_entry_price",
            "fair_value_estimate",
            "theoretical_edge",
            "cost_adjusted_edge",
            "confidence",
            "max_executable_size",
        ):
            _require_optional_finite_decimal(field_name, getattr(self, field_name))
        if self.max_executable_size is not None and self.max_executable_size < ZERO:
            raise ValueError("max_executable_size must be nonnegative")
        if not isinstance(self.risk_gate_passed, bool):
            raise ValueError("risk_gate_passed must be a bool")
        object.__setattr__(self, "risk_tags", _normalize_string_tuple("risk_tags", self.risk_tags))
        object.__setattr__(
            self,
            "risk_reason_codes",
            _normalize_string_tuple("risk_reason_codes", self.risk_reason_codes),
        )
        object.__setattr__(
            self,
            "supporting_reason_codes",
            _normalize_string_tuple(
                "supporting_reason_codes",
                self.supporting_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "blocking_reason_codes",
            _normalize_string_tuple("blocking_reason_codes", self.blocking_reason_codes),
        )
        object.__setattr__(
            self,
            "review_focus",
            _normalize_string_tuple("review_focus", self.review_focus),
        )
        if self.primary_reason_code not in PRIMARY_REASON_CODES:
            raise ValueError("primary_reason_code must be a known reason code")
        if self.queue_item_id != f"{self.condition_id}:{self.token_id}:{self.packet_id}":
            raise ValueError("queue_item_id must match condition_id:token_id:packet_id")
        _require_boundary_statement(self.boundary_statement)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")


@dataclass(frozen=True)
class PaperManualReviewQueue:
    generated_at: datetime
    config_version: str
    first_queued_at: datetime | None
    last_queued_at: datetime | None
    candidate_count: int
    item_count: int
    ready_item_count: int
    insufficient_item_count: int
    blocked_risk_item_count: int
    blocked_quality_item_count: int
    incomplete_item_count: int
    unique_market_count: int
    unique_strategy_count: int
    unique_risk_tag_count: int
    top_queue_item_id: str | None
    status: str
    items: tuple[PaperManualReviewQueueItem, ...]
    boundary_statement: str
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.first_queued_at is not None:
            object.__setattr__(self, "first_queued_at", _as_utc(self.first_queued_at))
        if self.last_queued_at is not None:
            object.__setattr__(self, "last_queued_at", _as_utc(self.last_queued_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "item_count",
            "ready_item_count",
            "insufficient_item_count",
            "blocked_risk_item_count",
            "blocked_quality_item_count",
            "incomplete_item_count",
            "unique_market_count",
            "unique_strategy_count",
            "unique_risk_tag_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.status not in QUEUE_STATUSES:
            raise ValueError("status must be a known manual review status")
        object.__setattr__(
            self,
            "items",
            _normalize_typed_tuple("items", self.items, PaperManualReviewQueueItem),
        )
        if self.item_count != len(self.items):
            raise ValueError("item_count must equal items length")
        actual_counts = _status_counts(self.items)
        if self.ready_item_count != actual_counts["paper_review_ready"]:
            raise ValueError("ready_item_count must match items")
        if self.insufficient_item_count != actual_counts["insufficient_evidence"]:
            raise ValueError("insufficient_item_count must match items")
        if self.blocked_risk_item_count != actual_counts["blocked_by_risk"]:
            raise ValueError("blocked_risk_item_count must match items")
        if self.blocked_quality_item_count != actual_counts["blocked_by_quality"]:
            raise ValueError("blocked_quality_item_count must match items")
        if self.incomplete_item_count != actual_counts["incomplete_data"]:
            raise ValueError("incomplete_item_count must match items")
        if self.unique_market_count != len({item.market_slug for item in self.items}):
            raise ValueError("unique_market_count must match items")
        if self.unique_strategy_count != len({item.strategy_type for item in self.items}):
            raise ValueError("unique_strategy_count must match items")
        if self.unique_risk_tag_count != len(
            {risk_tag for item in self.items for risk_tag in item.risk_tags}
        ):
            raise ValueError("unique_risk_tag_count must match items")
        if self.items:
            if self.top_queue_item_id != self.items[0].queue_item_id:
                raise ValueError("top_queue_item_id must match first item")
            if self.first_queued_at is None or self.last_queued_at is None:
                raise ValueError("queued_at bounds are required with items")
            if tuple(item.rank for item in self.items) != tuple(range(1, len(self.items) + 1)):
                raise ValueError("item ranks must be consecutive")
        else:
            if self.first_queued_at is not None or self.last_queued_at is not None:
                raise ValueError("queued_at bounds must be absent without items")
            if self.top_queue_item_id is not None:
                raise ValueError("top_queue_item_id must be absent without items")
            if self.status != "incomplete_data":
                raise ValueError("empty queues must be incomplete_data")
        _require_boundary_statement(self.boundary_statement)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")


@dataclass(frozen=True)
class PaperManualReviewLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, queue: PaperManualReviewQueue) -> None:
        if not isinstance(queue, PaperManualReviewQueue):
            raise ValueError("queue must be a PaperManualReviewQueue")
        _validate_queue_tree(queue)
        line = json.dumps(_json_ready(asdict(queue)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_manual_review_queue(
    candidates: Iterable[PaperManualReviewCandidate],
    *,
    market_scores: Iterable[MarketScore],
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
    config: PaperManualReviewConfig,
    generated_at: datetime,
) -> PaperManualReviewQueue:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of PaperManualReviewCandidate values")
    if isinstance(market_scores, (str, bytes)):
        raise ValueError("market_scores must be an iterable of MarketScore values")
    if not isinstance(config, PaperManualReviewConfig):
        raise ValueError("config must be a PaperManualReviewConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    _validate_report_inputs(analytics_history, forecast_evidence)
    try:
        candidate_items = tuple(candidates)
    except TypeError as exc:
        raise ValueError(
            "candidates must be an iterable of PaperManualReviewCandidate values"
        ) from exc
    try:
        score_items = tuple(market_scores)
    except TypeError as exc:
        raise ValueError("market_scores must be an iterable of MarketScore values") from exc

    normalized_candidates: list[PaperManualReviewCandidate] = []
    seen_candidate_keys: set[tuple[datetime, str, str]] = set()
    seen_queue_ids: set[str] = set()
    for candidate in candidate_items:
        if not isinstance(candidate, PaperManualReviewCandidate):
            raise ValueError("candidates must contain PaperManualReviewCandidate values")
        normalized = _clone_candidate(candidate)
        candidate_key = (normalized.queued_at, normalized.token_id, normalized.packet_id)
        if candidate_key in seen_candidate_keys:
            raise ValueError("duplicate candidate keys are not allowed")
        seen_candidate_keys.add(candidate_key)
        queue_item_id = _queue_item_id(normalized)
        if queue_item_id in seen_queue_ids:
            raise ValueError("duplicate queue_item_id values are not allowed")
        seen_queue_ids.add(queue_item_id)
        normalized_candidates.append(normalized)

    score_by_key: dict[tuple[str, str], MarketScore] = {}
    for score in score_items:
        if not isinstance(score, MarketScore):
            raise ValueError("market_scores must contain MarketScore values")
        score_key = (score.condition_id, score.token_id)
        if score_key in score_by_key:
            raise ValueError("duplicate market score keys are not allowed")
        score_by_key[score_key] = score

    draft_items = tuple(
        _build_queue_item(
            candidate,
            market_score_total=(
                score_by_key[(candidate.condition_id, candidate.token_id)].total
                if (candidate.condition_id, candidate.token_id) in score_by_key
                else None
            ),
            analytics_history=analytics_history,
            forecast_evidence=forecast_evidence,
            config=config,
        )
        for candidate in normalized_candidates
    )
    retained_items = (
        draft_items
        if config.include_blocked_items
        else tuple(
            item
            for item in draft_items
            if item.status in {"paper_review_ready", "insufficient_evidence"}
        )
    )
    sorted_items = tuple(
        _copy_item_with_rank(item, rank=index)
        for index, item in enumerate(
            sorted(
                retained_items,
                key=lambda item: _item_sort_key(
                    item,
                    analytics_history=analytics_history,
                    forecast_evidence=forecast_evidence,
                ),
            ),
            start=1,
        )
    )
    return _build_queue(
        generated_at=generated_at,
        config=config,
        candidate_count=len(normalized_candidates),
        items=sorted_items,
    )


def _build_queue_item(
    candidate: PaperManualReviewCandidate,
    *,
    market_score_total: Decimal | None,
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
    config: PaperManualReviewConfig,
) -> PaperManualReviewQueueItem:
    history_counts = _gate_counts(analytics_history.gate_results)
    forecast_counts = _gate_counts(forecast_evidence.gate_results)
    hard_block_count = (
        (0 if candidate.risk_gate_passed else 1)
        + history_counts["fail"]
        + forecast_counts["fail"]
    )
    evidence_pass_count = history_counts["pass"] + forecast_counts["pass"]
    status, primary_reason_code = _derive_item_status(
        candidate,
        analytics_history=analytics_history,
        forecast_evidence=forecast_evidence,
        config=config,
    )
    return PaperManualReviewQueueItem(
        queue_item_id=_queue_item_id(candidate),
        rank=1,
        status=status,
        status_rank=STATUS_RANK[status],
        hard_block_count=hard_block_count,
        evidence_pass_count=evidence_pass_count,
        source_score=candidate.source_score,
        market_score_total=market_score_total,
        queued_at=candidate.queued_at,
        packet_id=candidate.packet_id,
        condition_id=candidate.condition_id,
        token_id=candidate.token_id,
        market_slug=candidate.market_slug,
        market_url=candidate.market_url,
        question=candidate.question,
        outcome_name=candidate.outcome_name,
        strategy_type=candidate.strategy_type,
        risk_tags=candidate.risk_tags,
        thesis=candidate.thesis,
        invalidating_conditions=candidate.invalidating_conditions,
        rule_text_hash=candidate.rule_text_hash,
        resolution_source=candidate.resolution_source,
        model_probability=candidate.model_probability,
        expected_entry_price=candidate.expected_entry_price,
        fair_value_estimate=candidate.fair_value_estimate,
        theoretical_edge=candidate.theoretical_edge,
        cost_adjusted_edge=candidate.cost_adjusted_edge,
        confidence=candidate.confidence,
        max_executable_size=candidate.max_executable_size,
        risk_gate_passed=candidate.risk_gate_passed,
        risk_reason_codes=candidate.risk_reason_codes,
        history_status=analytics_history.status,
        forecast_status=forecast_evidence.status,
        history_gate_pass_count=history_counts["pass"],
        forecast_gate_pass_count=forecast_counts["pass"],
        history_gate_fail_count=history_counts["fail"],
        forecast_gate_fail_count=forecast_counts["fail"],
        readiness_summary=_readiness_summary(status),
        risk_summary=_risk_summary(candidate, analytics_history),
        evidence_summary=_evidence_summary(analytics_history, forecast_evidence),
        why_in_queue=_why_in_queue(status),
        primary_reason_code=primary_reason_code,
        supporting_reason_codes=_supporting_reason_codes(
            candidate,
            analytics_history,
            forecast_evidence,
            config,
        ),
        blocking_reason_codes=_blocking_reason_codes(
            candidate,
            analytics_history,
            forecast_evidence,
        ),
        review_focus=_review_focus(candidate, analytics_history, forecast_evidence),
        evidence_scope=EVIDENCE_SCOPE,
        boundary_statement=config.boundary_statement,
    )


def _build_queue(
    *,
    generated_at: datetime,
    config: PaperManualReviewConfig,
    candidate_count: int,
    items: tuple[PaperManualReviewQueueItem, ...],
) -> PaperManualReviewQueue:
    counts = _status_counts(items)
    first_queued_at = min((item.queued_at for item in items), default=None)
    last_queued_at = max((item.queued_at for item in items), default=None)
    return PaperManualReviewQueue(
        generated_at=generated_at,
        config_version=config.config_version,
        first_queued_at=first_queued_at,
        last_queued_at=last_queued_at,
        candidate_count=candidate_count,
        item_count=len(items),
        ready_item_count=counts["paper_review_ready"],
        insufficient_item_count=counts["insufficient_evidence"],
        blocked_risk_item_count=counts["blocked_by_risk"],
        blocked_quality_item_count=counts["blocked_by_quality"],
        incomplete_item_count=counts["incomplete_data"],
        unique_market_count=len({item.market_slug for item in items}),
        unique_strategy_count=len({item.strategy_type for item in items}),
        unique_risk_tag_count=len({risk_tag for item in items for risk_tag in item.risk_tags}),
        top_queue_item_id=items[0].queue_item_id if items else None,
        status=_queue_status(counts, config.min_ready_items),
        items=items,
        boundary_statement=config.boundary_statement,
    )


def _derive_item_status(
    candidate: PaperManualReviewCandidate,
    *,
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
    config: PaperManualReviewConfig,
) -> tuple[str, str]:
    if _candidate_is_incomplete(candidate) or _reports_are_incomplete(
        analytics_history,
        forecast_evidence,
    ):
        return "incomplete_data", "incomplete_data"
    if not candidate.risk_gate_passed or analytics_history.status == "blocked_by_risk":
        return "blocked_by_risk", "blocked_risk_drawdown"
    if forecast_evidence.status == "blocked_by_quality":
        return "blocked_by_quality", "blocked_forecast_quality"
    if (
        analytics_history.status == "insufficient_evidence"
        or forecast_evidence.status == "insufficient_evidence"
    ):
        return "insufficient_evidence", "needs_more_sample"
    if candidate.source_score < config.min_source_score:
        return "insufficient_evidence", "below_source_score"
    if (
        analytics_history.status == "paper_review_ready"
        and forecast_evidence.status == "paper_review_ready"
    ):
        return "paper_review_ready", "paper_evidence_ready"
    return "insufficient_evidence", "needs_more_sample"


def _candidate_is_incomplete(candidate: PaperManualReviewCandidate) -> bool:
    return candidate.market_url == ""


def _reports_are_incomplete(
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
) -> bool:
    return (
        analytics_history.status == "incomplete_data"
        or forecast_evidence.status == "incomplete_data"
    )


def _queue_status(counts: dict[str, int], min_ready_items: int) -> str:
    if sum(counts.values()) == 0:
        return "incomplete_data"
    if counts["paper_review_ready"] >= min_ready_items:
        return "paper_review_ready"
    if counts["blocked_by_quality"]:
        return "blocked_by_quality"
    if counts["blocked_by_risk"]:
        return "blocked_by_risk"
    if counts["insufficient_evidence"]:
        return "insufficient_evidence"
    return "incomplete_data"


def _item_sort_key(
    item: PaperManualReviewQueueItem,
    *,
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
) -> tuple[Any, ...]:
    return (
        item.status_rank,
        item.hard_block_count,
        -item.evidence_pass_count,
        item.source_score * NEGATIVE_ONE,
        _decimal_or_zero(item.cost_adjusted_edge) * NEGATIVE_ONE,
        _decimal_or_zero(item.confidence) * NEGATIVE_ONE,
        _decimal_or_zero(item.max_executable_size) * NEGATIVE_ONE,
        _risk_drag_ratio(item),
        -_freshness_timestamp(
            max(item.queued_at, analytics_history.generated_at, forecast_evidence.generated_at)
        ),
        item.market_slug,
        item.token_id,
        item.packet_id,
    )


def _risk_drag_ratio(item: PaperManualReviewQueueItem) -> Decimal:
    return (
        Decimal(item.hard_block_count)
        + Decimal(item.history_gate_fail_count) / Decimal("10")
        + Decimal(item.forecast_gate_fail_count) / Decimal("10")
    ).quantize(RATIO_QUANTUM)


def _freshness_timestamp(value: datetime) -> int:
    value = _as_utc(value)
    return (
        value.toordinal() * 86400000000
        + value.hour * 3600000000
        + value.minute * 60000000
        + value.second * 1000000
        + value.microsecond
    )


def _supporting_reason_codes(
    candidate: PaperManualReviewCandidate,
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
    config: PaperManualReviewConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if candidate.source_score >= config.min_source_score:
        codes.append("high_source_score")
    if candidate.risk_gate_passed:
        codes.append("risk_gate_passed")
    if analytics_history.status == "paper_review_ready":
        codes.append("history_ready")
    if forecast_evidence.status == "paper_review_ready":
        codes.append("forecast_ready")
    history_gates = _gate_by_name(analytics_history.gate_results)
    forecast_gates = _gate_by_name(forecast_evidence.gate_results)
    if (
        history_gates.get("sample_size") == "pass"
        and forecast_gates.get("sample_size") == "pass"
    ):
        codes.append("sample_size_passed")
    if forecast_gates.get("executable_edge_quality") == "pass":
        codes.append("edge_quality_passed")
    return tuple(codes)


def _blocking_reason_codes(
    candidate: PaperManualReviewCandidate,
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
) -> tuple[str, ...]:
    codes = [f"risk_gate:{code}" for code in candidate.risk_reason_codes]
    codes.extend(
        f"analytics_history:{gate.gate_name}:{gate.status}"
        for gate in analytics_history.gate_results
        if gate.status != "pass"
    )
    codes.extend(
        f"forecast_evidence:{gate.gate_name}:{gate.status}"
        for gate in forecast_evidence.gate_results
        if gate.status != "pass"
    )
    return tuple(codes)


def _review_focus(
    candidate: PaperManualReviewCandidate,
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
) -> tuple[str, ...]:
    focus = ["resolution_rule_ambiguity"]
    history_gates = _gate_by_name(analytics_history.gate_results)
    forecast_gates = _gate_by_name(forecast_evidence.gate_results)
    latest_trend = max(analytics_history.trends, key=lambda item: item.marked_at, default=None)
    if (
        "liquidity" in candidate.risk_tags
        or history_gates.get("execution_cost_reality") != "pass"
        or _is_positive(analytics_history.worst_exit_depth_shortfall_ratio)
        or (
            latest_trend is not None
            and _is_positive(latest_trend.exit_depth_shortfall_ratio)
        )
    ):
        focus.append("liquidity_exit_risk")
    if (
        forecast_gates.get("probability_quality") in {"pass", "fail", "incomplete"}
        or forecast_evidence.probability_observation_count > 0
        or forecast_evidence.mean_probability_loss is not None
        or forecast_evidence.worst_bucket_error is not None
    ):
        focus.append("probability_quality")
    if (
        forecast_gates.get("executable_edge_quality") in {"pass", "fail", "incomplete"}
        or forecast_evidence.edge_observation_count > 0
        or forecast_evidence.mean_edge_gap_ratio is not None
        or forecast_evidence.positive_edge_hit_rate is not None
    ):
        focus.append("edge_quality")
    if (
        forecast_gates.get("residual_exposure") in {"pass", "fail"}
        or forecast_evidence.worst_residual_exposure_ratio is not None
    ):
        focus.append("residual_exposure")
    if _is_positive(analytics_history.largest_market_cost_basis_ratio) or _is_positive(
        analytics_history.largest_risk_tag_cost_basis_ratio
    ):
        focus.append("theme_concentration")
    return tuple(focus)


def _readiness_summary(status: str) -> str:
    if status == "paper_review_ready":
        return "Paper evidence is ready for manual inspection."
    if status == "incomplete_data":
        return "Required paper evidence is incomplete."
    return "Paper evidence needs manual review before any later stage."


def _risk_summary(
    candidate: PaperManualReviewCandidate,
    analytics_history: PaperAnalyticsHistoryReport,
) -> str:
    if not candidate.risk_gate_passed:
        return candidate.risk_reason_summary or "Candidate risk gate failed."
    if analytics_history.status == "blocked_by_risk":
        return "Paper analytics history is blocked by risk."
    return "No hard paper risk block is present."


def _evidence_summary(
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
) -> str:
    return (
        f"History status is {analytics_history.status}; "
        f"forecast evidence status is {forecast_evidence.status}."
    )


def _why_in_queue(status: str) -> str:
    if status == "paper_review_ready":
        return "Candidate has enough paper evidence for human inspection."
    if status == "incomplete_data":
        return "Candidate is retained to show incomplete paper evidence."
    return "Candidate is retained to show paper review blockers or gaps."


def _gate_counts(gate_results: tuple[Any, ...]) -> dict[str, int]:
    return {
        "pass": sum(1 for gate in gate_results if gate.status == "pass"),
        "fail": sum(1 for gate in gate_results if gate.status == "fail"),
        "incomplete": sum(1 for gate in gate_results if gate.status == "incomplete"),
    }


def _gate_by_name(gate_results: tuple[Any, ...]) -> dict[str, str]:
    return {gate.gate_name: gate.status for gate in gate_results}


def _status_counts(items: tuple[PaperManualReviewQueueItem, ...]) -> dict[str, int]:
    return {status: sum(1 for item in items if item.status == status) for status in QUEUE_STATUSES}


def _queue_item_id(candidate: PaperManualReviewCandidate) -> str:
    return f"{candidate.condition_id}:{candidate.token_id}:{candidate.packet_id}"


def _copy_item_with_rank(
    item: PaperManualReviewQueueItem,
    *,
    rank: int,
) -> PaperManualReviewQueueItem:
    return PaperManualReviewQueueItem(
        queue_item_id=item.queue_item_id,
        rank=rank,
        status=item.status,
        status_rank=item.status_rank,
        hard_block_count=item.hard_block_count,
        evidence_pass_count=item.evidence_pass_count,
        source_score=item.source_score,
        market_score_total=item.market_score_total,
        queued_at=item.queued_at,
        packet_id=item.packet_id,
        condition_id=item.condition_id,
        token_id=item.token_id,
        market_slug=item.market_slug,
        market_url=item.market_url,
        question=item.question,
        outcome_name=item.outcome_name,
        strategy_type=item.strategy_type,
        risk_tags=item.risk_tags,
        thesis=item.thesis,
        invalidating_conditions=item.invalidating_conditions,
        rule_text_hash=item.rule_text_hash,
        resolution_source=item.resolution_source,
        model_probability=item.model_probability,
        expected_entry_price=item.expected_entry_price,
        fair_value_estimate=item.fair_value_estimate,
        theoretical_edge=item.theoretical_edge,
        cost_adjusted_edge=item.cost_adjusted_edge,
        confidence=item.confidence,
        max_executable_size=item.max_executable_size,
        risk_gate_passed=item.risk_gate_passed,
        risk_reason_codes=item.risk_reason_codes,
        history_status=item.history_status,
        forecast_status=item.forecast_status,
        history_gate_pass_count=item.history_gate_pass_count,
        forecast_gate_pass_count=item.forecast_gate_pass_count,
        history_gate_fail_count=item.history_gate_fail_count,
        forecast_gate_fail_count=item.forecast_gate_fail_count,
        readiness_summary=item.readiness_summary,
        risk_summary=item.risk_summary,
        evidence_summary=item.evidence_summary,
        why_in_queue=item.why_in_queue,
        primary_reason_code=item.primary_reason_code,
        supporting_reason_codes=item.supporting_reason_codes,
        blocking_reason_codes=item.blocking_reason_codes,
        review_focus=item.review_focus,
        evidence_scope=item.evidence_scope,
        boundary_statement=item.boundary_statement,
        paper_only=item.paper_only,
    )


def _clone_candidate(candidate: PaperManualReviewCandidate) -> PaperManualReviewCandidate:
    return PaperManualReviewCandidate(
        queued_at=candidate.queued_at,
        packet_id=candidate.packet_id,
        condition_id=candidate.condition_id,
        token_id=candidate.token_id,
        market_slug=candidate.market_slug,
        market_url=candidate.market_url,
        question=candidate.question,
        outcome_name=candidate.outcome_name,
        source_score=candidate.source_score,
        raw_archive_path=candidate.raw_archive_path,
        strategy_type=candidate.strategy_type,
        risk_tags=candidate.risk_tags,
        thesis=candidate.thesis,
        invalidating_conditions=candidate.invalidating_conditions,
        rule_text_hash=candidate.rule_text_hash,
        resolution_source=candidate.resolution_source,
        model_probability=candidate.model_probability,
        expected_entry_price=candidate.expected_entry_price,
        fair_value_estimate=candidate.fair_value_estimate,
        theoretical_edge=candidate.theoretical_edge,
        cost_adjusted_edge=candidate.cost_adjusted_edge,
        confidence=candidate.confidence,
        max_executable_size=candidate.max_executable_size,
        risk_gate_passed=candidate.risk_gate_passed,
        risk_reason_codes=candidate.risk_reason_codes,
        risk_reason_summary=candidate.risk_reason_summary,
        paper_only=candidate.paper_only,
    )


def _validate_report_inputs(
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
) -> None:
    if type(analytics_history) is not PaperAnalyticsHistoryReport:
        raise ValueError("analytics_history must be a PaperAnalyticsHistoryReport")
    if type(forecast_evidence) is not PaperForecastEvidenceReport:
        raise ValueError("forecast_evidence must be a PaperForecastEvidenceReport")
    if analytics_history.paper_only is not True:
        raise ValueError("analytics_history must be paper-only")
    if forecast_evidence.paper_only is not True:
        raise ValueError("forecast_evidence must be paper-only")
    PaperAnalyticsHistoryReport(
        generated_at=analytics_history.generated_at,
        config_version=analytics_history.config_version,
        first_marked_at=analytics_history.first_marked_at,
        last_marked_at=analytics_history.last_marked_at,
        report_count=analytics_history.report_count,
        candidate_observation_count=analytics_history.candidate_observation_count,
        simulated_trade_count=analytics_history.simulated_trade_count,
        exited_trade_count=analytics_history.exited_trade_count,
        forward_window_days=analytics_history.forward_window_days,
        unique_market_count=analytics_history.unique_market_count,
        unique_strategy_count=analytics_history.unique_strategy_count,
        unique_risk_tag_count=analytics_history.unique_risk_tag_count,
        latest_exit_nav=analytics_history.latest_exit_nav,
        latest_total_exit_pnl=analytics_history.latest_total_exit_pnl,
        max_drawdown=analytics_history.max_drawdown,
        max_drawdown_ratio=analytics_history.max_drawdown_ratio,
        worst_exit_depth_shortfall_ratio=analytics_history.worst_exit_depth_shortfall_ratio,
        worst_no_exit_depth_cost_basis_ratio=analytics_history.worst_no_exit_depth_cost_basis_ratio,
        worst_midpoint_nav_gap_ratio=analytics_history.worst_midpoint_nav_gap_ratio,
        largest_market_cost_basis_ratio=analytics_history.largest_market_cost_basis_ratio,
        largest_risk_tag_cost_basis_ratio=analytics_history.largest_risk_tag_cost_basis_ratio,
        max_breach_count=analytics_history.max_breach_count,
        status=analytics_history.status,
        gate_results=analytics_history.gate_results,
        trends=analytics_history.trends,
        paper_only=analytics_history.paper_only,
    )
    PaperForecastEvidenceReport(
        generated_at=forecast_evidence.generated_at,
        config_version=forecast_evidence.config_version,
        first_observed_at=forecast_evidence.first_observed_at,
        last_observed_at=forecast_evidence.last_observed_at,
        observation_count=forecast_evidence.observation_count,
        probability_observation_count=forecast_evidence.probability_observation_count,
        edge_observation_count=forecast_evidence.edge_observation_count,
        unique_market_count=forecast_evidence.unique_market_count,
        unique_strategy_count=forecast_evidence.unique_strategy_count,
        unique_risk_tag_count=forecast_evidence.unique_risk_tag_count,
        mean_probability_loss=forecast_evidence.mean_probability_loss,
        worst_bucket_error=forecast_evidence.worst_bucket_error,
        mean_edge_gap_ratio=forecast_evidence.mean_edge_gap_ratio,
        positive_edge_hit_rate=forecast_evidence.positive_edge_hit_rate,
        worst_residual_exposure_ratio=forecast_evidence.worst_residual_exposure_ratio,
        status=forecast_evidence.status,
        gate_results=forecast_evidence.gate_results,
        buckets=forecast_evidence.buckets,
        paper_only=forecast_evidence.paper_only,
    )


def _validate_queue_tree(queue: PaperManualReviewQueue) -> None:
    items = tuple(
        PaperManualReviewQueueItem(
            queue_item_id=item.queue_item_id,
            rank=item.rank,
            status=item.status,
            status_rank=item.status_rank,
            hard_block_count=item.hard_block_count,
            evidence_pass_count=item.evidence_pass_count,
            source_score=item.source_score,
            market_score_total=item.market_score_total,
            queued_at=item.queued_at,
            packet_id=item.packet_id,
            condition_id=item.condition_id,
            token_id=item.token_id,
            market_slug=item.market_slug,
            market_url=item.market_url,
            question=item.question,
            outcome_name=item.outcome_name,
            strategy_type=item.strategy_type,
            risk_tags=item.risk_tags,
            thesis=item.thesis,
            invalidating_conditions=item.invalidating_conditions,
            rule_text_hash=item.rule_text_hash,
            resolution_source=item.resolution_source,
            model_probability=item.model_probability,
            expected_entry_price=item.expected_entry_price,
            fair_value_estimate=item.fair_value_estimate,
            theoretical_edge=item.theoretical_edge,
            cost_adjusted_edge=item.cost_adjusted_edge,
            confidence=item.confidence,
            max_executable_size=item.max_executable_size,
            risk_gate_passed=item.risk_gate_passed,
            risk_reason_codes=item.risk_reason_codes,
            history_status=item.history_status,
            forecast_status=item.forecast_status,
            history_gate_pass_count=item.history_gate_pass_count,
            forecast_gate_pass_count=item.forecast_gate_pass_count,
            history_gate_fail_count=item.history_gate_fail_count,
            forecast_gate_fail_count=item.forecast_gate_fail_count,
            readiness_summary=item.readiness_summary,
            risk_summary=item.risk_summary,
            evidence_summary=item.evidence_summary,
            why_in_queue=item.why_in_queue,
            primary_reason_code=item.primary_reason_code,
            supporting_reason_codes=item.supporting_reason_codes,
            blocking_reason_codes=item.blocking_reason_codes,
            review_focus=item.review_focus,
            evidence_scope=item.evidence_scope,
            boundary_statement=item.boundary_statement,
            paper_only=item.paper_only,
        )
        for item in queue.items
    )
    PaperManualReviewQueue(
        generated_at=queue.generated_at,
        config_version=queue.config_version,
        first_queued_at=queue.first_queued_at,
        last_queued_at=queue.last_queued_at,
        candidate_count=queue.candidate_count,
        item_count=queue.item_count,
        ready_item_count=queue.ready_item_count,
        insufficient_item_count=queue.insufficient_item_count,
        blocked_risk_item_count=queue.blocked_risk_item_count,
        blocked_quality_item_count=queue.blocked_quality_item_count,
        incomplete_item_count=queue.incomplete_item_count,
        unique_market_count=queue.unique_market_count,
        unique_strategy_count=queue.unique_strategy_count,
        unique_risk_tag_count=queue.unique_risk_tag_count,
        top_queue_item_id=queue.top_queue_item_id,
        status=queue.status,
        items=items,
        boundary_statement=queue.boundary_statement,
        paper_only=queue.paper_only,
    )


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_canonical_string(
    field_name: str,
    value: str,
    *,
    allow_empty: bool,
) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if allow_empty and value == "":
        return
    _require_canonical_string(field_name, value)


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    required_parts = (
        "paper-only",
        "manual-review artifact",
        "not a trade instruction",
        "order instruction",
    )
    lowered = value.lower()
    if any(part not in lowered for part in required_parts):
        raise ValueError("boundary_statement must describe paper-only manual review")


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_typed_tuple(
    field_name: str,
    value: Iterable[Any],
    expected_type: type,
) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not all(isinstance(item, expected_type) for item in items):
        raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _decimal_or_zero(value: Decimal | None) -> Decimal:
    return ZERO if value is None else value


def _is_positive(value: Decimal | None) -> bool:
    return value is not None and value > ZERO
