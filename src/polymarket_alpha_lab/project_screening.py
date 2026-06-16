"""Paper-only project screening reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyReport,
)


__all__ = (
    "PaperProjectScreeningConfig",
    "PaperProjectScreeningCandidate",
    "PaperProjectScreeningGateResult",
    "PaperProjectScreeningQueueItem",
    "PaperProjectScreeningReport",
    "PaperProjectScreeningLog",
    "build_paper_project_screening_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")

GATE_NAMES = (
    "input_count",
    "candidate_types",
    "unique_slugs",
    "screenable_candidates",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
RESEARCH_BUCKETS = ("research_ready", "watch", "defer", "blocked")
SCREENING_STATUSES = (
    "screening_ready",
    "screening_watch",
    "screening_defer",
    "screening_blocked",
)
SIDES = ("yes", "no", "none")
BUCKET_INDEX = {
    "research_ready": 0,
    "watch": 1,
    "defer": 2,
    "blocked": 3,
}
BUCKET_SCREENING_STATUS = {
    "research_ready": "screening_ready",
    "watch": "screening_watch",
    "defer": "screening_defer",
    "blocked": "screening_blocked",
}
BLOCKED_SOURCE_STATUSES = ("blocked_by_inputs", "blocked_by_risk")
DEFER_SOURCE_STATUSES = ("blocked_by_cost", "no_paper_edge")


@dataclass(frozen=True)
class PaperProjectScreeningConfig:
    config_version: str
    min_screening_score: Decimal = Decimal("0.010000")
    reference_ask_size: Decimal = Decimal("100.0000")
    net_edge_weight: Decimal = Decimal("1.0000")
    confidence_weight: Decimal = Decimal("0.3000")
    depth_weight: Decimal = Decimal("0.1000")
    spread_penalty_weight: Decimal = Decimal("0.5000")
    resolution_risk_penalty_weight: Decimal = Decimal("0.5000")
    cost_penalty_weight: Decimal = Decimal("0.3000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("min_screening_score", self.min_screening_score)
        _require_positive_decimal("reference_ask_size", self.reference_ask_size)
        for field_name in (
            "net_edge_weight",
            "confidence_weight",
            "depth_weight",
            "spread_penalty_weight",
            "resolution_risk_penalty_weight",
            "cost_penalty_weight",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class PaperProjectScreeningGateResult:
    gate_name: str
    status: str
    reason_code: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known project screening gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known project screening gate status")
        _require_canonical_string("reason_code", self.reason_code)
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class PaperProjectScreeningCandidate:
    market_slug: str
    question: str
    source_status: str
    scoring_side: str
    valid_depth: bool
    net_edge_per_share: Decimal | None
    total_cost_per_share: Decimal | None
    ask_size: Decimal | None
    edge_component: Decimal
    confidence_component: Decimal
    depth_component: Decimal
    spread_penalty: Decimal
    resolution_risk_penalty: Decimal
    cost_penalty: Decimal
    screening_score: Decimal
    screening_status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("source_status", self.source_status)
        if self.scoring_side not in SIDES:
            raise ValueError("scoring_side must be yes, no, or none")
        if not isinstance(self.valid_depth, bool):
            raise ValueError("valid_depth must be a bool")
        _require_optional_finite_decimal("net_edge_per_share", self.net_edge_per_share)
        _require_optional_nonnegative_decimal(
            "total_cost_per_share",
            self.total_cost_per_share,
        )
        _require_optional_nonnegative_decimal("ask_size", self.ask_size)
        for field_name in (
            "edge_component",
            "confidence_component",
            "depth_component",
            "spread_penalty",
            "resolution_risk_penalty",
            "cost_penalty",
            "screening_score",
        ):
            _require_finite_decimal(field_name, getattr(self, field_name))
        if self.screening_status not in SCREENING_STATUSES:
            raise ValueError("screening_status must be a known screening status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperProjectScreeningQueueItem:
    queue_position: int
    market_slug: str
    question: str
    research_bucket: str
    screening_score: Decimal
    source_status: str
    scoring_side: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_positive_int("queue_position", self.queue_position)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.research_bucket not in RESEARCH_BUCKETS:
            raise ValueError("research_bucket must be a known project screening bucket")
        _require_finite_decimal("screening_score", self.screening_score)
        _require_canonical_string("source_status", self.source_status)
        if self.scoring_side not in SIDES:
            raise ValueError("scoring_side must be yes, no, or none")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperProjectScreeningReport:
    generated_at: datetime
    config_version: str
    candidate_count: int
    ready_count: int
    watch_count: int
    defer_count: int
    blocked_count: int
    gate_results: tuple[PaperProjectScreeningGateResult, ...]
    candidates: tuple[PaperProjectScreeningCandidate, ...]
    queue_items: tuple[PaperProjectScreeningQueueItem, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "defer_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "gate_results",
            _normalize_gate_tuple(self.gate_results),
        )
        object.__setattr__(
            self,
            "candidates",
            _normalize_candidate_tuple(self.candidates),
        )
        object.__setattr__(
            self,
            "queue_items",
            _normalize_queue_item_tuple(self.queue_items),
        )
        if self.candidate_count != len(self.candidates):
            raise ValueError("candidate_count must match candidates")
        if self.candidate_count != len(self.queue_items):
            raise ValueError("candidate_count must match queue_items")
        if self.ready_count != _bucket_count(self.queue_items, "research_ready"):
            raise ValueError("ready_count must match queue_items")
        if self.watch_count != _bucket_count(self.queue_items, "watch"):
            raise ValueError("watch_count must match queue_items")
        if self.defer_count != _bucket_count(self.queue_items, "defer"):
            raise ValueError("defer_count must match queue_items")
        if self.blocked_count != _bucket_count(self.queue_items, "blocked"):
            raise ValueError("blocked_count must match queue_items")
        if tuple(item.queue_position for item in self.queue_items) != tuple(
            range(1, len(self.queue_items) + 1),
        ):
            raise ValueError("queue positions must be contiguous")
        _validate_queue_items_match_candidates(self.candidates, self.queue_items)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


@dataclass(frozen=True)
class PaperProjectScreeningLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperProjectScreeningReport) -> None:
        if not isinstance(report, PaperProjectScreeningReport):
            raise ValueError("report must be a PaperProjectScreeningReport")
        _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_project_screening_report(
    reports: tuple[PaperCostAwareEventStrategyReport, ...],
    *,
    config: PaperProjectScreeningConfig,
    generated_at: datetime,
) -> PaperProjectScreeningReport:
    if not isinstance(config, PaperProjectScreeningConfig):
        raise ValueError("config must be a PaperProjectScreeningConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    source_reports = _collect_source_reports(reports)
    gate_results = _gate_results(source_reports)
    candidates = tuple(_candidate_from_report(report, config) for report in source_reports)
    queue_items = _queue_items(candidates, config)

    return PaperProjectScreeningReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=len(candidates),
        ready_count=_bucket_count(queue_items, "research_ready"),
        watch_count=_bucket_count(queue_items, "watch"),
        defer_count=_bucket_count(queue_items, "defer"),
        blocked_count=_bucket_count(queue_items, "blocked"),
        gate_results=gate_results,
        candidates=candidates,
        queue_items=queue_items,
    )


def _collect_source_reports(
    reports: tuple[PaperCostAwareEventStrategyReport, ...],
) -> tuple[PaperCostAwareEventStrategyReport, ...]:
    if isinstance(reports, (str, bytes)):
        raise ValueError("reports must be an iterable of PaperCostAwareEventStrategyReport")
    try:
        items = tuple(reports)
    except TypeError as exc:
        raise ValueError(
            "reports must be an iterable of PaperCostAwareEventStrategyReport",
        ) from exc
    if not items:
        raise ValueError("reports must contain at least one value")
    for item in items:
        if not isinstance(item, PaperCostAwareEventStrategyReport):
            raise ValueError("reports must contain PaperCostAwareEventStrategyReport values")
        _validate_source_report(item)
    slugs = tuple(item.market_slug for item in items)
    if len(set(slugs)) != len(slugs):
        raise ValueError("market_slug values must be unique")
    return items


def _validate_source_report(report: PaperCostAwareEventStrategyReport) -> None:
    PaperCostAwareEventStrategyReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        market_slug=report.market_slug,
        question=report.question,
        fair_probability_yes=report.fair_probability_yes,
        confidence=report.confidence,
        yes_bid=report.yes_bid,
        no_bid=report.no_bid,
        spread=report.spread,
        resolution_risk=report.resolution_risk,
        selected_side=report.selected_side,
        status=report.status,
        yes_result=report.yes_result,
        no_result=report.no_result,
        gate_results=report.gate_results,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _gate_results(
    source_reports: tuple[PaperCostAwareEventStrategyReport, ...],
) -> tuple[PaperProjectScreeningGateResult, ...]:
    unique_slug_count = len({report.market_slug for report in source_reports})
    return (
        _gate(
            "input_count",
            "pass" if source_reports else "fail",
            "source_reports_supplied" if source_reports else "missing_source_reports",
            "At least one source report is supplied.",
            len(source_reports),
            1,
        ),
        _gate(
            "candidate_types",
            "pass",
            "source_report_types_ready",
            "Every candidate source is a cost-aware event strategy report.",
            len(source_reports),
            len(source_reports),
        ),
        _gate(
            "unique_slugs",
            "pass" if unique_slug_count == len(source_reports) else "fail",
            "unique_market_slugs"
            if unique_slug_count == len(source_reports)
            else "duplicate_market_slugs",
            "Every source report has a unique market slug.",
            unique_slug_count,
            len(source_reports),
        ),
        _gate(
            "screenable_candidates",
            "pass" if source_reports else "fail",
            "screenable_candidates_ready" if source_reports else "no_screenable_candidates",
            "At least one candidate can be screened.",
            len(source_reports),
            1,
        ),
    )


def _gate(
    gate_name: str,
    status: str,
    reason_code: str,
    message: str,
    observed_value: Decimal | int | str | None,
    threshold: Decimal | int | str | None,
) -> PaperProjectScreeningGateResult:
    return PaperProjectScreeningGateResult(
        gate_name=gate_name,
        status=status,
        reason_code=reason_code,
        message=message,
        observed_value=observed_value,
        threshold=threshold,
    )


def _candidate_from_report(
    report: PaperCostAwareEventStrategyReport,
    config: PaperProjectScreeningConfig,
) -> PaperProjectScreeningCandidate:
    side = _scoring_result(report)
    valid_depth = _valid_depth(side)
    scoring_side = side.side if side is not None else "none"
    net_edge = side.net_edge_per_share if side is not None else None
    total_cost = side.total_cost_per_share if side is not None else None
    ask_size = side.ask_size if side is not None else None
    reason_codes: list[str] = [f"source_{report.status}"]
    if side is None:
        reason_codes.append("missing_scoring_side")
    elif valid_depth:
        reason_codes.append(f"{side.side}_depth_ready")
    else:
        reason_codes.append(f"{side.side}_depth_incomplete")

    edge_component = _quantize_score(
        (net_edge if net_edge is not None else ZERO) * config.net_edge_weight,
    )
    confidence_component = _quantize_score(report.confidence * config.confidence_weight)
    depth_component = _quantize_score(
        _depth_ratio(ask_size, config.reference_ask_size) * config.depth_weight,
    )
    spread_penalty = _quantize_score(report.spread * config.spread_penalty_weight)
    resolution_risk_penalty = _quantize_score(
        report.resolution_risk * config.resolution_risk_penalty_weight,
    )
    cost_penalty = _quantize_score(
        (total_cost if total_cost is not None else ZERO) * config.cost_penalty_weight,
    )
    screening_score = _quantize_score(
        edge_component
        + confidence_component
        + depth_component
        - spread_penalty
        - resolution_risk_penalty
        - cost_penalty,
    )
    screening_status = _screening_status(report, valid_depth, net_edge, screening_score, config)

    return PaperProjectScreeningCandidate(
        market_slug=report.market_slug,
        question=report.question,
        source_status=report.status,
        scoring_side=scoring_side,
        valid_depth=valid_depth,
        net_edge_per_share=net_edge,
        total_cost_per_share=total_cost,
        ask_size=ask_size,
        edge_component=edge_component,
        confidence_component=confidence_component,
        depth_component=depth_component,
        spread_penalty=spread_penalty,
        resolution_risk_penalty=resolution_risk_penalty,
        cost_penalty=cost_penalty,
        screening_score=screening_score,
        screening_status=screening_status,
        reason_codes=tuple(reason_codes),
    )


def _scoring_result(
    report: PaperCostAwareEventStrategyReport,
) -> PaperCostAwareEventSideResult | None:
    selected_result = _selected_side_result(report)
    if selected_result is not None and _scoring_side_is_ready(report, selected_result):
        return selected_result
    choices = tuple(
        result
        for result in (report.yes_result, report.no_result)
        if _scoring_side_is_ready(report, result)
    )
    if not choices:
        return None
    return max(choices, key=lambda result: result.net_edge_per_share)


def _selected_side_result(
    report: PaperCostAwareEventStrategyReport,
) -> PaperCostAwareEventSideResult | None:
    if report.selected_side == "yes":
        return report.yes_result
    if report.selected_side == "no":
        return report.no_result
    return None


def _scoring_side_is_ready(
    report: PaperCostAwareEventStrategyReport,
    result: PaperCostAwareEventSideResult,
) -> bool:
    return _source_depth_passes(report, result.side) and _valid_depth(result)


def _source_depth_passes(report: PaperCostAwareEventStrategyReport, side: str) -> bool:
    gates = {gate.gate_name: gate for gate in report.gate_results}
    return gates[f"{side}_depth"].status == "pass"


def _valid_depth(result: PaperCostAwareEventSideResult | None) -> bool:
    return (
        result is not None
        and result.executable_price is not None
        and result.ask_size is not None
        and result.ask_size > ZERO
        and result.net_edge_per_share is not None
    )


def _depth_ratio(ask_size: Decimal | None, reference_ask_size: Decimal) -> Decimal:
    if ask_size is None or ask_size <= ZERO:
        return ZERO
    ratio = ask_size / reference_ask_size
    return ONE if ratio > ONE else ratio


def _screening_status(
    report: PaperCostAwareEventStrategyReport,
    valid_depth: bool,
    net_edge: Decimal | None,
    screening_score: Decimal,
    config: PaperProjectScreeningConfig,
) -> str:
    if report.status in BLOCKED_SOURCE_STATUSES:
        return "screening_blocked"
    if (
        report.status == "paper_review_ready"
        and valid_depth
        and screening_score >= config.min_screening_score
    ):
        return "screening_ready"
    if report.status == "watch" or (
        valid_depth
        and net_edge is not None
        and net_edge > ZERO
        and screening_score < config.min_screening_score
    ):
        return "screening_watch"
    return "screening_defer"


def _research_bucket(
    candidate: PaperProjectScreeningCandidate,
    config: PaperProjectScreeningConfig,
) -> str:
    if candidate.source_status in BLOCKED_SOURCE_STATUSES:
        return "blocked"
    if (
        candidate.source_status == "paper_review_ready"
        and candidate.valid_depth
        and candidate.screening_score >= config.min_screening_score
    ):
        return "research_ready"
    if candidate.source_status == "watch" or (
        candidate.valid_depth
        and candidate.net_edge_per_share is not None
        and candidate.net_edge_per_share > ZERO
        and candidate.screening_score < config.min_screening_score
    ):
        return "watch"
    if candidate.source_status in DEFER_SOURCE_STATUSES:
        return "defer"
    return "defer"


def _queue_items(
    candidates: tuple[PaperProjectScreeningCandidate, ...],
    config: PaperProjectScreeningConfig,
) -> tuple[PaperProjectScreeningQueueItem, ...]:
    bucketed = tuple(
        (
            _research_bucket(candidate, config),
            candidate,
        )
        for candidate in candidates
    )
    sorted_items = sorted(
        bucketed,
        key=lambda item: (
            BUCKET_INDEX[item[0]],
            -item[1].screening_score,
            item[1].market_slug,
        ),
    )
    return tuple(
        PaperProjectScreeningQueueItem(
            queue_position=index,
            market_slug=candidate.market_slug,
            question=candidate.question,
            research_bucket=bucket,
            screening_score=candidate.screening_score,
            source_status=candidate.source_status,
            scoring_side=candidate.scoring_side,
            reason_codes=candidate.reason_codes,
        )
        for index, (bucket, candidate) in enumerate(sorted_items, start=1)
    )


def _bucket_count(
    queue_items: tuple[PaperProjectScreeningQueueItem, ...],
    bucket: str,
) -> int:
    return sum(1 for item in queue_items if item.research_bucket == bucket)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


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


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_nonnegative_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


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


def _require_gate_value(field_name: str, value: Decimal | int | str | None) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, Decimal):
        _require_finite_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_gate_tuple(
    value: tuple[PaperProjectScreeningGateResult, ...],
) -> tuple[PaperProjectScreeningGateResult, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("gate_results must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("gate_results must be an iterable") from exc
    if not all(isinstance(item, PaperProjectScreeningGateResult) for item in items):
        raise ValueError("gate_results must contain PaperProjectScreeningGateResult values")
    if tuple(item.gate_name for item in items) != GATE_NAMES:
        raise ValueError("gate_results must contain the project screening gates")
    return items


def _normalize_candidate_tuple(
    value: tuple[PaperProjectScreeningCandidate, ...],
) -> tuple[PaperProjectScreeningCandidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    if not all(isinstance(item, PaperProjectScreeningCandidate) for item in items):
        raise ValueError("candidates must contain PaperProjectScreeningCandidate values")
    return items


def _normalize_queue_item_tuple(
    value: tuple[PaperProjectScreeningQueueItem, ...],
) -> tuple[PaperProjectScreeningQueueItem, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("queue_items must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("queue_items must be an iterable") from exc
    if not all(isinstance(item, PaperProjectScreeningQueueItem) for item in items):
        raise ValueError("queue_items must contain PaperProjectScreeningQueueItem values")
    return items


def _validate_queue_items_match_candidates(
    candidates: tuple[PaperProjectScreeningCandidate, ...],
    queue_items: tuple[PaperProjectScreeningQueueItem, ...],
) -> None:
    candidate_slugs = tuple(candidate.market_slug for candidate in candidates)
    item_slugs = tuple(item.market_slug for item in queue_items)
    if len(set(candidate_slugs)) != len(candidate_slugs):
        raise ValueError("queue_items must match candidates")
    if len(set(item_slugs)) != len(item_slugs):
        raise ValueError("queue_items must match candidates")
    if set(candidate_slugs) != set(item_slugs):
        raise ValueError("queue_items must match candidates")

    candidates_by_slug = {candidate.market_slug: candidate for candidate in candidates}
    for item in queue_items:
        candidate = candidates_by_slug[item.market_slug]
        if (
            item.question != candidate.question
            or item.screening_score != candidate.screening_score
            or item.source_status != candidate.source_status
            or item.scoring_side != candidate.scoring_side
            or item.reason_codes != candidate.reason_codes
            or BUCKET_SCREENING_STATUS[item.research_bucket]
            != candidate.screening_status
        ):
            raise ValueError("queue_items must match candidates")


def _quantize_score(value: Decimal) -> Decimal:
    _require_finite_decimal("score", value)
    return value.quantize(SCORE_QUANTUM)


def _validate_report_tree(report: PaperProjectScreeningReport) -> None:
    gate_results = tuple(
        PaperProjectScreeningGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            reason_code=gate.reason_code,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    candidates = tuple(
        PaperProjectScreeningCandidate(
            market_slug=candidate.market_slug,
            question=candidate.question,
            source_status=candidate.source_status,
            scoring_side=candidate.scoring_side,
            valid_depth=candidate.valid_depth,
            net_edge_per_share=candidate.net_edge_per_share,
            total_cost_per_share=candidate.total_cost_per_share,
            ask_size=candidate.ask_size,
            edge_component=candidate.edge_component,
            confidence_component=candidate.confidence_component,
            depth_component=candidate.depth_component,
            spread_penalty=candidate.spread_penalty,
            resolution_risk_penalty=candidate.resolution_risk_penalty,
            cost_penalty=candidate.cost_penalty,
            screening_score=candidate.screening_score,
            screening_status=candidate.screening_status,
            reason_codes=candidate.reason_codes,
        )
        for candidate in report.candidates
    )
    queue_items = tuple(
        PaperProjectScreeningQueueItem(
            queue_position=item.queue_position,
            market_slug=item.market_slug,
            question=item.question,
            research_bucket=item.research_bucket,
            screening_score=item.screening_score,
            source_status=item.source_status,
            scoring_side=item.scoring_side,
            reason_codes=item.reason_codes,
        )
        for item in report.queue_items
    )
    PaperProjectScreeningReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        defer_count=report.defer_count,
        blocked_count=report.blocked_count,
        gate_results=gate_results,
        candidates=candidates,
        queue_items=queue_items,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
