"""Paper-only operator queue summary for strategy recommendation bundles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable

from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)


__all__ = (
    "PaperStrategyRecommendationQueueRow",
    "PaperStrategyRecommendationQueueSummaryReport",
    "build_paper_strategy_recommendation_queue_summary_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
ACTIONS = ("recommend", "watch", "reject")
DECISIONS = ("selected", "skipped", "not_selected")
QUEUE_STATUSES = ("ready", "watch", "blocked")
SIDES = ("yes", "no", "none")
QUEUE_STATUS_RANK = {"ready": 0, "watch": 1, "blocked": 2}
NO_REASON_CODE = "no_reason_code"


@dataclass(frozen=True)
class PaperStrategyRecommendationQueueRow:
    rank: int
    market_slug: str
    selected_side: str
    action: str
    decision: str
    recommendation_score: Decimal
    suggested_notional: Decimal
    primary_reason_code: str
    queue_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("rank", self.rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("selected_side", self.selected_side)
        _require_action("action", self.action)
        _require_decision("decision", self.decision)
        object.__setattr__(
            self,
            "recommendation_score",
            _quantize_score("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(
            self,
            "suggested_notional",
            _quantize_decimal("suggested_notional", self.suggested_notional),
        )
        _require_canonical_string("primary_reason_code", self.primary_reason_code)
        _require_queue_status("queue_status", self.queue_status)
        _validate_row_status(self)
        _validate_hard_flags("queue_row", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationQueueSummaryReport:
    generated_at: datetime
    source_config_version: str
    queue_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    top_score: Decimal
    average_ready_score: Decimal
    primary_reason_code_counts: tuple[tuple[str, int], ...]
    queue_rows: tuple[PaperStrategyRecommendationQueueRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("source_config_version", self.source_config_version)
        for field_name in (
            "queue_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        queue_rows = _normalize_queue_rows(self.queue_rows)
        object.__setattr__(self, "queue_rows", queue_rows)
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_decimal("total_ready_notional", self.total_ready_notional),
        )
        object.__setattr__(
            self,
            "top_score",
            _quantize_score("top_score", self.top_score),
        )
        object.__setattr__(
            self,
            "average_ready_score",
            _quantize_score("average_ready_score", self.average_ready_score),
        )
        primary_reason_code_counts = _normalize_reason_code_counts(
            self.primary_reason_code_counts,
        )
        object.__setattr__(
            self,
            "primary_reason_code_counts",
            primary_reason_code_counts,
        )
        _validate_summary(self)
        _validate_hard_flags("queue_summary", self)


def build_paper_strategy_recommendation_queue_summary_report(
    bundle_report: object,
) -> PaperStrategyRecommendationQueueSummaryReport:
    """Reduce a paper strategy bundle into an operator-facing queue summary."""

    _validate_bundle_report(bundle_report)
    rows_without_rank = _queue_row_values(bundle_report)
    queue_rows = tuple(
        PaperStrategyRecommendationQueueRow(
            rank=index,
            market_slug=values["market_slug"],
            selected_side=values["selected_side"],
            action=values["action"],
            decision=values["decision"],
            recommendation_score=values["recommendation_score"],
            suggested_notional=values["suggested_notional"],
            primary_reason_code=values["primary_reason_code"],
            queue_status=values["queue_status"],
        )
        for index, values in enumerate(_order_row_values(rows_without_rank), start=1)
    )
    ready_rows = tuple(row for row in queue_rows if row.queue_status == "ready")
    return PaperStrategyRecommendationQueueSummaryReport(
        generated_at=bundle_report.generated_at,
        source_config_version=bundle_report.config_version,
        queue_count=len(queue_rows),
        ready_count=len(ready_rows),
        watch_count=_queue_status_count(queue_rows, "watch"),
        blocked_count=_queue_status_count(queue_rows, "blocked"),
        total_ready_notional=_total_notional(ready_rows),
        top_score=_top_score(queue_rows),
        average_ready_score=_average_score(ready_rows),
        primary_reason_code_counts=_primary_reason_code_counts(queue_rows),
        queue_rows=queue_rows,
    )


def _queue_row_values(
    bundle_report: PaperStrategyRecommendationBundleReport,
) -> tuple[dict[str, Any], ...]:
    explanation_by_slug = _explanation_rows_by_slug(
        bundle_report.explanation_report.explanation_rows,
    )
    values: list[dict[str, Any]] = []
    for selection_row in bundle_report.selection_policy_report.selection_rows:
        explanation_row = explanation_by_slug.get(selection_row.market_slug)
        if explanation_row is None:
            raise ValueError("explanation_report rows must match selection rows")
        if explanation_row.action != selection_row.source_action:
            raise ValueError("explanation_report rows must match selection rows")
        if explanation_row.selected_side != selection_row.selected_side:
            raise ValueError("explanation_report rows must match selection rows")
        if explanation_row.recommendation_score != selection_row.recommendation_score:
            raise ValueError("explanation_report rows must match selection rows")
        values.append(
            {
                "market_slug": selection_row.market_slug,
                "selected_side": selection_row.selected_side,
                "action": selection_row.source_action,
                "decision": selection_row.decision,
                "recommendation_score": _quantize_score(
                    "recommendation_score",
                    selection_row.recommendation_score,
                ),
                "suggested_notional": _quantize_decimal(
                    "suggested_notional",
                    selection_row.suggested_position_notional,
                ),
                "primary_reason_code": explanation_row.primary_reason_code,
                "queue_status": _queue_status(selection_row),
            },
        )
    if len(values) != len(explanation_by_slug):
        raise ValueError("explanation_report rows must match selection rows")
    return tuple(values)


def _order_row_values(values: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        sorted(
            values,
            key=lambda row: (
                QUEUE_STATUS_RANK[row["queue_status"]],
                -row["recommendation_score"],
                -row["suggested_notional"],
                row["market_slug"],
            ),
        ),
    )


def _queue_status(selection_row: object) -> str:
    if selection_row.decision == "selected":
        return "ready"
    if selection_row.source_action == "reject":
        return "blocked"
    return "watch"


def _validate_bundle_report(bundle_report: object) -> None:
    if type(bundle_report) is not PaperStrategyRecommendationBundleReport:
        raise ValueError(
            "bundle_report must be a PaperStrategyRecommendationBundleReport",
        )
    _validate_hard_flags("bundle_report", bundle_report)
    _validate_hard_flags("recommendation_report", bundle_report.recommendation_report)
    _validate_hard_flags("selection_policy_report", bundle_report.selection_policy_report)
    _validate_hard_flags("explanation_report", bundle_report.explanation_report)


def _explanation_rows_by_slug(rows: Iterable[object]) -> dict[str, object]:
    by_slug: dict[str, object] = {}
    for row in rows:
        _require_canonical_string("market_slug", getattr(row, "market_slug", None))
        if row.market_slug in by_slug:
            raise ValueError("explanation_report rows must have unique market_slug values")
        by_slug[row.market_slug] = row
    return by_slug


def _normalize_queue_rows(
    value: Iterable[PaperStrategyRecommendationQueueRow],
) -> tuple[PaperStrategyRecommendationQueueRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("queue_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("queue_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperStrategyRecommendationQueueRow:
            raise ValueError(
                "queue_rows must contain PaperStrategyRecommendationQueueRow values",
            )
    return rows


def _validate_summary(
    report: PaperStrategyRecommendationQueueSummaryReport,
) -> None:
    if report.queue_count != len(report.queue_rows):
        raise ValueError("queue_count must match queue_rows")
    if report.ready_count != _queue_status_count(report.queue_rows, "ready"):
        raise ValueError("ready_count must match queue_rows")
    if report.watch_count != _queue_status_count(report.queue_rows, "watch"):
        raise ValueError("watch_count must match queue_rows")
    if report.blocked_count != _queue_status_count(report.queue_rows, "blocked"):
        raise ValueError("blocked_count must match queue_rows")
    if (
        report.ready_count + report.watch_count + report.blocked_count
        != report.queue_count
    ):
        raise ValueError("queue status counts must match queue_count")
    if tuple(row.rank for row in report.queue_rows) != tuple(
        range(1, len(report.queue_rows) + 1),
    ):
        raise ValueError("rank values must be contiguous")
    if report.queue_rows != _order_queue_rows(report.queue_rows):
        raise ValueError("queue_rows must use deterministic ordering")
    if report.total_ready_notional != _total_notional(
        row for row in report.queue_rows if row.queue_status == "ready"
    ):
        raise ValueError("total_ready_notional must match ready queue_rows")
    if report.top_score != _top_score(report.queue_rows):
        raise ValueError("top_score must match queue_rows")
    if report.average_ready_score != _average_score(
        row for row in report.queue_rows if row.queue_status == "ready"
    ):
        raise ValueError("average_ready_score must match ready queue_rows")
    if report.primary_reason_code_counts != _primary_reason_code_counts(
        report.queue_rows,
    ):
        raise ValueError("primary_reason_code_counts must match queue_rows")


def _order_queue_rows(
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> tuple[PaperStrategyRecommendationQueueRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                QUEUE_STATUS_RANK[row.queue_status],
                -row.recommendation_score,
                -row.suggested_notional,
                row.market_slug,
                row.rank,
            ),
        ),
    )


def _validate_row_status(row: PaperStrategyRecommendationQueueRow) -> None:
    if row.queue_status != _expected_queue_status(row.action, row.decision):
        raise ValueError("queue_status must match action and decision")
    if row.queue_status == "ready":
        if row.selected_side == "none":
            raise ValueError("ready rows must have a selected side")
        if row.suggested_notional <= ZERO:
            raise ValueError("ready rows must have positive suggested_notional")


def _expected_queue_status(action: str, decision: str) -> str:
    if decision == "selected":
        return "ready"
    if action == "reject":
        return "blocked"
    return "watch"


def _queue_status_count(
    rows: Iterable[PaperStrategyRecommendationQueueRow],
    queue_status: str,
) -> int:
    return sum(1 for row in rows if row.queue_status == queue_status)


def _total_notional(rows: Iterable[PaperStrategyRecommendationQueueRow]) -> Decimal:
    return _quantize_decimal(
        "total_ready_notional",
        sum((row.suggested_notional for row in rows), ZERO),
    )


def _top_score(rows: tuple[PaperStrategyRecommendationQueueRow, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return _quantize_score("top_score", rows[0].recommendation_score)


def _average_score(rows: Iterable[PaperStrategyRecommendationQueueRow]) -> Decimal:
    items = tuple(rows)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize_score(
        "average_ready_score",
        sum((row.recommendation_score for row in items), ZERO) / Decimal(len(items)),
    )


def _primary_reason_code_counts(
    rows: Iterable[PaperStrategyRecommendationQueueRow],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _normalize_reason_code_counts(
    value: Iterable[tuple[str, int]],
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("primary_reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("primary_reason_code_counts must be an iterable") from exc
    for item in counts:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("primary_reason_code_counts must contain tuple rows")
        reason_code, count = item
        _require_canonical_string("primary_reason_code_counts reason_code", reason_code)
        _require_nonnegative_int("primary_reason_code_counts count", count)
    return counts


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANTUM)


def _quantize_score(field_name: str, value: object) -> Decimal:
    score = _quantize_decimal(field_name, value)
    if score > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return score


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_decision(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DECISIONS:
        raise ValueError(f"{field_name} must be selected, skipped, or not_selected")


def _require_queue_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _validate_hard_flags(field_name: str, report: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(report, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
