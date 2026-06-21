"""Paper-only rank stability reducer for recommendation queue summaries.

Recommendation scores inherit the queue module's 0..1 probability-like score
invariant; this reducer observes rank churn without changing queue decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.strategy_recommendation_queue import (
    PaperStrategyRecommendationQueueRow,
    PaperStrategyRecommendationQueueSummaryReport,
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
STABILITY_STATUSES = ("stable", "watch", "blocked")
QUEUE_STATUSES = ("ready", "watch", "blocked")
SIDES = ("yes", "no", "none")
# Stable candidates remain first; blocked rows follow so repair work is visible
# before ordinary watch rows.
STABILITY_STATUS_RANK = {"stable": 0, "blocked": 1, "watch": 2}
QUEUE_STATUS_RANK = {"ready": 0, "watch": 1, "blocked": 2}


@dataclass(frozen=True)
class PaperStrategyRecommendationRankStabilityConfig:
    config_version: str
    min_snapshot_count: int
    max_rank_movement: int
    max_score_delta: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_snapshot_count", self.min_snapshot_count)
        _require_nonnegative_int("max_rank_movement", self.max_rank_movement)
        object.__setattr__(
            self,
            "max_score_delta",
            _normalize_probability_decimal("max_score_delta", self.max_score_delta),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationRankStabilityRow:
    market_slug: str
    stability_status: str
    latest_selected_side: str
    latest_queue_status: str
    present_snapshot_count: int
    ready_snapshot_count: int
    first_rank: int
    latest_rank: int
    rank_delta: int
    max_rank_movement: int
    first_score: Decimal
    latest_score: Decimal
    score_delta: Decimal
    max_score_delta: Decimal
    first_notional: Decimal
    latest_notional: Decimal
    notional_delta: Decimal
    selected_side_changed: bool
    queue_status_changed: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_stability_status("stability_status", self.stability_status)
        _require_side("latest_selected_side", self.latest_selected_side)
        _require_queue_status("latest_queue_status", self.latest_queue_status)
        for field_name in (
            "present_snapshot_count",
            "ready_snapshot_count",
            "max_rank_movement",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_positive_int("first_rank", self.first_rank)
        _require_positive_int("latest_rank", self.latest_rank)
        _require_int("rank_delta", self.rank_delta)
        for field_name in (
            "first_score",
            "latest_score",
            "max_score_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "score_delta",
            _normalize_signed_decimal("score_delta", self.score_delta),
        )
        for field_name in ("first_notional", "latest_notional"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "notional_delta",
            _normalize_signed_decimal("notional_delta", self.notional_delta),
        )
        _require_bool("selected_side_changed", self.selected_side_changed)
        _require_bool("queue_status_changed", self.queue_status_changed)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("rank_stability_row", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationRankStabilityReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    candidate_count: int
    stability_status: str
    stable_count: int
    watch_count: int
    blocked_count: int
    stable_ready_count: int
    unstable_ready_count: int
    selected_side_changed_count: int
    queue_status_changed_count: int
    latest_generated_at: datetime | None
    top_stable_market_slug: str | None
    reason_codes: tuple[str, ...]
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_report_count",
            "candidate_count",
            "stable_count",
            "watch_count",
            "blocked_count",
            "stable_ready_count",
            "unstable_ready_count",
            "selected_side_changed_count",
            "queue_status_changed_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_stability_status("stability_status", self.stability_status)
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        if self.top_stable_market_slug is not None:
            _require_canonical_string("top_stable_market_slug", self.top_stable_market_slug)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_stability_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("rank_stability_report", self)


def build_paper_strategy_recommendation_rank_stability_report(
    queue_summary_reports: object,
    *,
    config: PaperStrategyRecommendationRankStabilityConfig,
    generated_at: datetime,
) -> PaperStrategyRecommendationRankStabilityReport:
    """Measure whether latest paper queue candidates stayed stable over history."""

    if type(config) is not PaperStrategyRecommendationRankStabilityConfig:
        raise ValueError(
            "config must be a PaperStrategyRecommendationRankStabilityConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    reports = _normalize_queue_summary_reports(queue_summary_reports)
    chronological_reports = _chronological_reports(reports)
    latest_report = chronological_reports[-1] if chronological_reports else None
    rows = (
        _stability_rows_for_latest_report(
            latest_report,
            chronological_reports,
            config=config,
        )
        if latest_report is not None
        else ()
    )
    ordered_rows = _order_rows(rows)

    return PaperStrategyRecommendationRankStabilityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=len(chronological_reports),
        candidate_count=len(ordered_rows),
        stability_status=_report_status(ordered_rows),
        stable_count=_stability_count(ordered_rows, "stable"),
        watch_count=_stability_count(ordered_rows, "watch"),
        blocked_count=_stability_count(ordered_rows, "blocked"),
        stable_ready_count=_stable_ready_count(ordered_rows),
        unstable_ready_count=_unstable_ready_count(ordered_rows),
        selected_side_changed_count=sum(
            1 for row in ordered_rows if row.selected_side_changed
        ),
        queue_status_changed_count=sum(
            1 for row in ordered_rows if row.queue_status_changed
        ),
        latest_generated_at=latest_report.generated_at if latest_report is not None else None,
        top_stable_market_slug=_top_stable_market_slug(ordered_rows),
        reason_codes=_report_reason_codes(ordered_rows),
        rows=ordered_rows,
    )


def _normalize_queue_summary_reports(
    value: object,
) -> tuple[PaperStrategyRecommendationQueueSummaryReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(
            "queue_summary_reports must be a list or tuple of "
            "PaperStrategyRecommendationQueueSummaryReport values",
        )
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperStrategyRecommendationQueueSummaryReport:
            raise ValueError(
                "queue_summary_reports must contain "
                "PaperStrategyRecommendationQueueSummaryReport values",
            )
        _require_hard_flags("queue_summary_report", report)
        _require_unique_market_slugs(report.queue_rows)
    return reports


def _chronological_reports(
    reports: tuple[PaperStrategyRecommendationQueueSummaryReport, ...],
) -> tuple[PaperStrategyRecommendationQueueSummaryReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (item[1].generated_at, item[0]),
        )
    )


def _stability_rows_for_latest_report(
    latest_report: PaperStrategyRecommendationQueueSummaryReport,
    reports: tuple[PaperStrategyRecommendationQueueSummaryReport, ...],
    *,
    config: PaperStrategyRecommendationRankStabilityConfig,
) -> tuple[PaperStrategyRecommendationRankStabilityRow, ...]:
    history_by_slug = _history_by_market_slug(reports)
    return tuple(
        _stability_row_from_observations(
            latest_row.market_slug,
            history_by_slug[latest_row.market_slug],
            config=config,
        )
        for latest_row in latest_report.queue_rows
    )


def _history_by_market_slug(
    reports: tuple[PaperStrategyRecommendationQueueSummaryReport, ...],
) -> dict[str, tuple[PaperStrategyRecommendationQueueRow, ...]]:
    values: dict[str, list[PaperStrategyRecommendationQueueRow]] = {}
    for report in reports:
        for row in report.queue_rows:
            values.setdefault(row.market_slug, []).append(row)
    return {market_slug: tuple(rows) for market_slug, rows in values.items()}


def _stability_row_from_observations(
    market_slug: str,
    observations: tuple[PaperStrategyRecommendationQueueRow, ...],
    *,
    config: PaperStrategyRecommendationRankStabilityConfig,
) -> PaperStrategyRecommendationRankStabilityRow:
    first = observations[0]
    latest = observations[-1]
    selected_side_changed = _selected_side_changed(observations)
    queue_status_changed = _queue_status_changed(observations)
    max_rank_movement = _max_rank_movement(observations)
    max_score_delta = _max_score_delta(observations)
    score_delta = _quantize_signed(latest.recommendation_score - first.recommendation_score)
    notional_delta = _quantize_signed(latest.suggested_notional - first.suggested_notional)
    reason_codes = _row_reason_codes(
        observations,
        selected_side_changed=selected_side_changed,
        queue_status_changed=queue_status_changed,
        max_rank_movement=max_rank_movement,
        max_score_delta=max_score_delta,
        config=config,
    )
    stability_status = _row_status(reason_codes)

    return PaperStrategyRecommendationRankStabilityRow(
        market_slug=market_slug,
        stability_status=stability_status,
        latest_selected_side=latest.selected_side,
        latest_queue_status=latest.queue_status,
        present_snapshot_count=len(observations),
        ready_snapshot_count=sum(1 for row in observations if row.queue_status == "ready"),
        first_rank=first.rank,
        latest_rank=latest.rank,
        rank_delta=latest.rank - first.rank,
        max_rank_movement=max_rank_movement,
        first_score=first.recommendation_score,
        latest_score=latest.recommendation_score,
        score_delta=score_delta,
        max_score_delta=max_score_delta,
        first_notional=first.suggested_notional,
        latest_notional=latest.suggested_notional,
        notional_delta=notional_delta,
        selected_side_changed=selected_side_changed,
        queue_status_changed=queue_status_changed,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observations: tuple[PaperStrategyRecommendationQueueRow, ...],
    *,
    selected_side_changed: bool,
    queue_status_changed: bool,
    max_rank_movement: int,
    max_score_delta: Decimal,
    config: PaperStrategyRecommendationRankStabilityConfig,
) -> tuple[str, ...]:
    latest = observations[-1]
    if latest.queue_status == "blocked":
        reason_codes = ["latest_candidate_blocked"]
        if any(row.queue_status == "ready" for row in observations[:-1]):
            reason_codes.append("ready_to_blocked_transition")
        return tuple(reason_codes)

    if selected_side_changed:
        return ("selected_side_changed",)

    if len(observations) < config.min_snapshot_count:
        return ("insufficient_history",)

    if latest.queue_status != "ready":
        return (f"latest_candidate_{latest.queue_status}",)

    blocking_reasons = []
    if max_rank_movement > config.max_rank_movement:
        blocking_reasons.append("rank_movement_exceeds_threshold")
    if max_score_delta > config.max_score_delta:
        blocking_reasons.append("score_delta_exceeds_threshold")
    if blocking_reasons:
        return tuple(blocking_reasons)

    if queue_status_changed:
        return ("queue_status_changed",)

    return ("stable_ready",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            "latest_candidate_blocked",
            "rank_movement_exceeds_threshold",
            "score_delta_exceeds_threshold",
            "selected_side_changed",
        )
    ):
        return "blocked"
    if reason_codes == ("stable_ready",):
        return "stable"
    return "watch"


def _selected_side_changed(
    observations: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> bool:
    tradeable_sides = {
        row.selected_side for row in observations if row.selected_side in ("yes", "no")
    }
    return len(tradeable_sides) > 1


def _queue_status_changed(
    observations: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> bool:
    return len({row.queue_status for row in observations}) > 1


def _max_rank_movement(
    observations: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> int:
    ranks = tuple(row.rank for row in observations)
    return _max_int_spread(ranks)


def _max_score_delta(
    observations: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> Decimal:
    scores = tuple(row.recommendation_score for row in observations)
    if not scores:
        return ZERO.quantize(QUANTUM)
    return _quantize_nonnegative(max(scores) - min(scores))


def _max_int_spread(values: tuple[int, ...]) -> int:
    if not values:
        return 0
    return max(values) - min(values)


def _order_rows(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
) -> tuple[PaperStrategyRecommendationRankStabilityRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STABILITY_STATUS_RANK[row.stability_status],
                QUEUE_STATUS_RANK[row.latest_queue_status],
                -row.latest_score,
                row.latest_rank,
                row.market_slug,
            ),
        ),
    )


def _report_status(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
) -> str:
    if any(row.stability_status == "blocked" for row in rows):
        return "blocked"
    if not rows:
        return "watch"
    if _stable_ready_count(rows) > 0 and _unstable_ready_count(rows) == 0:
        return "stable"
    return "watch"


def _report_reason_codes(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_latest_candidates",)
    if any(row.stability_status == "blocked" for row in rows):
        return ("blocked_stability_candidates_present",)
    if _unstable_ready_count(rows) > 0:
        return ("unstable_ready_candidates_present",)
    if _stable_ready_count(rows) > 0:
        return ("stable_ready_candidates_present",)
    return ("no_stable_ready_candidates",)


def _stability_count(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
    stability_status: str,
) -> int:
    return sum(1 for row in rows if row.stability_status == stability_status)


def _stable_ready_count(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
) -> int:
    return sum(
        1
        for row in rows
        if row.stability_status == "stable" and row.latest_queue_status == "ready"
    )


def _unstable_ready_count(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
) -> int:
    return sum(
        1
        for row in rows
        if row.stability_status != "stable" and row.latest_queue_status == "ready"
    )


def _top_stable_market_slug(
    rows: tuple[PaperStrategyRecommendationRankStabilityRow, ...],
) -> str | None:
    for row in rows:
        if row.stability_status == "stable" and row.latest_queue_status == "ready":
            return row.market_slug
    return None


def _validate_row_consistency(
    row: PaperStrategyRecommendationRankStabilityRow,
) -> None:
    if row.ready_snapshot_count > row.present_snapshot_count:
        raise ValueError("ready_snapshot_count must not exceed present_snapshot_count")
    if row.rank_delta != row.latest_rank - row.first_rank:
        raise ValueError("rank_delta must equal latest_rank minus first_rank")
    if row.max_rank_movement < abs(row.rank_delta):
        raise ValueError("max_rank_movement must cover rank_delta")
    if row.score_delta != _quantize_signed(row.latest_score - row.first_score):
        raise ValueError("score_delta must equal latest_score minus first_score")
    if row.max_score_delta < abs(row.score_delta):
        raise ValueError("max_score_delta must cover score_delta")
    if row.notional_delta != _quantize_signed(row.latest_notional - row.first_notional):
        raise ValueError("notional_delta must equal latest_notional minus first_notional")
    if row.stability_status == "stable":
        if row.latest_queue_status != "ready":
            raise ValueError("stable rows must have latest_queue_status ready")
        if row.reason_codes != ("stable_ready",):
            raise ValueError("stable rows must have stable_ready reason")


def _validate_report_consistency(
    report: PaperStrategyRecommendationRankStabilityReport,
) -> None:
    if report.candidate_count != len(report.rows):
        raise ValueError("candidate_count must match rows")
    if report.stable_count != _stability_count(report.rows, "stable"):
        raise ValueError("stable_count must match rows")
    if report.watch_count != _stability_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _stability_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.stable_count + report.watch_count + report.blocked_count != report.candidate_count:
        raise ValueError("stability counts must sum to candidate_count")
    if report.stable_ready_count != _stable_ready_count(report.rows):
        raise ValueError("stable_ready_count must match rows")
    if report.unstable_ready_count != _unstable_ready_count(report.rows):
        raise ValueError("unstable_ready_count must match rows")
    if report.selected_side_changed_count != sum(
        1 for row in report.rows if row.selected_side_changed
    ):
        raise ValueError("selected_side_changed_count must match rows")
    if report.queue_status_changed_count != sum(
        1 for row in report.rows if row.queue_status_changed
    ):
        raise ValueError("queue_status_changed_count must match rows")
    if report.rows != _order_rows(report.rows):
        raise ValueError("rows must use deterministic ordering")
    if report.stability_status != _report_status(report.rows):
        raise ValueError("stability_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.top_stable_market_slug != _top_stable_market_slug(report.rows):
        raise ValueError("top_stable_market_slug must match rows")
    if report.source_report_count == 0:
        if report.latest_generated_at is not None:
            raise ValueError("latest_generated_at must be absent without sources")
        if report.candidate_count != 0:
            raise ValueError("candidate_count must be zero without sources")
    elif report.latest_generated_at is None:
        raise ValueError("latest_generated_at is required with sources")


def _normalize_stability_rows(
    value: object,
) -> tuple[PaperStrategyRecommendationRankStabilityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperStrategyRecommendationRankStabilityRow:
            raise ValueError(
                "rows must contain PaperStrategyRecommendationRankStabilityRow values",
            )
        _require_hard_flags("rank_stability_row", row)
        _validate_row_consistency(row)
    return rows


def _require_unique_market_slugs(
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> None:
    market_slugs = tuple(row.market_slug for row in rows)
    if len(set(market_slugs)) != len(market_slugs):
        raise ValueError("queue_rows must have unique market_slug values")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_signed_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.quantize(QUANTUM):
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return value.quantize(QUANTUM)


def _quantize_nonnegative(value: Decimal) -> Decimal:
    quantized = _quantize_signed(value)
    if quantized < ZERO:
        raise ValueError("value must be nonnegative")
    return quantized


def _quantize_signed(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_queue_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperStrategyRecommendationRankStabilityConfig",
    "PaperStrategyRecommendationRankStabilityReport",
    "PaperStrategyRecommendationRankStabilityRow",
    "build_paper_strategy_recommendation_rank_stability_report",
)
