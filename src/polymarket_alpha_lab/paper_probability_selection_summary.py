"""Pure paper-only selection summary for probability queue rows under cost stress."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.paper_cost_stress import (
    PaperCostStressReport,
    PaperCostStressScenarioRow,
)
from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueReport,
    PaperProbabilityRecommendationQueueRow,
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
SIDES = ("yes", "no")
ACTIONS = ("recommend", "watch", "reject")
RECOMMENDED_NEXT_STEPS = ("research_review", "await_fresh_context", "skip")
SELECTION_STATUSES = ("ready", "watch", "blocked")
SURVIVAL_STATUSES = ("pass", "watch", "fail")


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryConfig:
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryRow:
    queue_rank: int
    market_slug: str
    question: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    executable_paper_shares: Decimal
    recommended_next_step: str
    selection_status: str
    stress_scenario_count: int
    stress_pass_count: int
    stress_watch_count: int
    stress_fail_count: int
    worst_stressed_net_probability_edge: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("queue_rank", self.queue_rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("side", self.side)
        _require_action("action", self.action)
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_nonnegative_decimal(
                "recommendation_score",
                self.recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "executable_paper_shares",
            _normalize_nonnegative_decimal(
                "executable_paper_shares",
                self.executable_paper_shares,
            ),
        )
        _require_recommended_next_step(
            "recommended_next_step",
            self.recommended_next_step,
        )
        _require_selection_status("selection_status", self.selection_status)
        for field_name in (
            "stress_scenario_count",
            "stress_pass_count",
            "stress_watch_count",
            "stress_fail_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "worst_stressed_net_probability_edge",
            _normalize_optional_decimal(
                "worst_stressed_net_probability_edge",
                self.worst_stressed_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("selection_row", self)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryReport:
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_cost_stress_config_version: str
    queue_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    missing_stress_count: int
    rows: tuple[PaperProbabilitySelectionSummaryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "source_queue_config_version",
            self.source_queue_config_version,
        )
        _require_canonical_string(
            "source_cost_stress_config_version",
            self.source_cost_stress_config_version,
        )
        for field_name in (
            "queue_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "missing_stress_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_selection_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("selection_report", self)


def build_paper_probability_selection_summary_report(
    queue_report: object,
    cost_stress_report: object,
    *,
    config: PaperProbabilitySelectionSummaryConfig,
    generated_at: datetime,
) -> PaperProbabilitySelectionSummaryReport:
    """Join probability queue rows to cost-stress outcomes without changing queue decisions."""

    if type(queue_report) is not PaperProbabilityRecommendationQueueReport:
        raise ValueError("queue_report must be a PaperProbabilityRecommendationQueueReport")
    if type(cost_stress_report) is not PaperCostStressReport:
        raise ValueError("cost_stress_report must be a PaperCostStressReport")
    if type(config) is not PaperProbabilitySelectionSummaryConfig:
        raise ValueError("config must be a PaperProbabilitySelectionSummaryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_queue_report(queue_report)
    _validate_cost_stress_report(cost_stress_report)
    _require_hard_flags("config", config)

    stress_rows_by_key = _stress_rows_by_key(cost_stress_report.rows)
    rows = tuple(
        _selection_row_from_queue_row(
            row,
            stress_rows_by_key.get((row.market_slug, row.side), ()),
        )
        for row in queue_report.queue_rows
    )

    return PaperProbabilitySelectionSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_queue_config_version=queue_report.source_config_version,
        source_cost_stress_config_version=cost_stress_report.config_version,
        queue_count=len(rows),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        missing_stress_count=sum(1 for row in rows if row.stress_scenario_count == 0),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def _selection_row_from_queue_row(
    queue_row: PaperProbabilityRecommendationQueueRow,
    stress_rows: tuple[PaperCostStressScenarioRow, ...],
) -> PaperProbabilitySelectionSummaryRow:
    _validate_stress_rows_match_queue_row(queue_row, stress_rows)
    stress_pass_count = _survival_status_count(stress_rows, "pass")
    stress_watch_count = _survival_status_count(stress_rows, "watch")
    stress_fail_count = _survival_status_count(stress_rows, "fail")
    selection_status = _selection_status(
        queue_row,
        stress_scenario_count=len(stress_rows),
        stress_watch_count=stress_watch_count,
        stress_fail_count=stress_fail_count,
    )
    reason_codes = _row_reason_codes(
        queue_row,
        stress_rows,
        selection_status=selection_status,
    )

    return PaperProbabilitySelectionSummaryRow(
        queue_rank=queue_row.queue_rank,
        market_slug=queue_row.market_slug,
        question=queue_row.question,
        side=queue_row.side,
        action=queue_row.action,
        recommendation_score=queue_row.recommendation_score,
        net_probability_edge=queue_row.net_probability_edge,
        executable_paper_shares=queue_row.executable_paper_shares,
        recommended_next_step=queue_row.recommended_next_step,
        selection_status=selection_status,
        stress_scenario_count=len(stress_rows),
        stress_pass_count=stress_pass_count,
        stress_watch_count=stress_watch_count,
        stress_fail_count=stress_fail_count,
        worst_stressed_net_probability_edge=_worst_stressed_edge(stress_rows),
        reason_codes=reason_codes,
    )


def _selection_status(
    queue_row: PaperProbabilityRecommendationQueueRow,
    *,
    stress_scenario_count: int,
    stress_watch_count: int,
    stress_fail_count: int,
) -> str:
    if stress_scenario_count == 0:
        return "blocked"
    if queue_row.recommended_next_step == "skip":
        return "blocked"
    if queue_row.recommended_next_step == "await_fresh_context":
        return "watch"
    if stress_fail_count > 0:
        return "blocked"
    if stress_watch_count > 0:
        return "watch"
    return "ready"


def _row_reason_codes(
    queue_row: PaperProbabilityRecommendationQueueRow,
    stress_rows: tuple[PaperCostStressScenarioRow, ...],
    *,
    selection_status: str,
) -> tuple[str, ...]:
    reason_codes = list(queue_row.reason_codes)
    if not stress_rows:
        reason_codes.append("missing_cost_stress")
    elif queue_row.recommended_next_step == "skip":
        reason_codes.append("source_next_step_skip")
    elif queue_row.recommended_next_step == "await_fresh_context":
        reason_codes.append("source_next_step_await_fresh_context")
    elif selection_status == "blocked":
        reason_codes.extend(_stress_reason_codes(stress_rows, include_pass=False))
        reason_codes.append("cost_stress_failed")
    elif selection_status == "watch":
        reason_codes.extend(_stress_reason_codes(stress_rows, include_pass=False))
        reason_codes.append("cost_stress_watch")
    else:
        reason_codes.append("cost_stress_passed")
    return _normalize_reason_codes("reason_codes", reason_codes)


def _stress_reason_codes(
    stress_rows: tuple[PaperCostStressScenarioRow, ...],
    *,
    include_pass: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in stress_rows:
        if include_pass is False and row.survival_status == "pass":
            continue
        reason_codes.extend(row.reason_codes)
    return tuple(reason_codes)


def _stress_rows_by_key(
    rows: tuple[PaperCostStressScenarioRow, ...],
) -> dict[tuple[str, str], tuple[PaperCostStressScenarioRow, ...]]:
    grouped: dict[tuple[str, str], list[PaperCostStressScenarioRow]] = {}
    scenario_names_by_key: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        key = (row.market_slug, row.side)
        scenario_names = scenario_names_by_key.setdefault(key, set())
        if row.scenario_name in scenario_names:
            raise ValueError("cost_stress_report rows must have unique scenarios")
        scenario_names.add(row.scenario_name)
        grouped.setdefault(key, []).append(row)
    return {key: tuple(values) for key, values in grouped.items()}


def _validate_stress_rows_match_queue_row(
    queue_row: PaperProbabilityRecommendationQueueRow,
    stress_rows: tuple[PaperCostStressScenarioRow, ...],
) -> None:
    for stress_row in stress_rows:
        if stress_row.market_slug != queue_row.market_slug or stress_row.side != queue_row.side:
            raise ValueError("stress rows must match queue row")
        if stress_row.net_probability_edge != queue_row.net_probability_edge:
            raise ValueError("stress rows must match queue row")
        if stress_row.total_cost_per_share != queue_row.total_cost_per_share:
            raise ValueError("stress rows must match queue row")
        if stress_row.recommendation_score != queue_row.recommendation_score:
            raise ValueError("stress rows must match queue row")


def _validate_queue_report(report: PaperProbabilityRecommendationQueueReport) -> None:
    _require_hard_flags("queue_report", report)
    for row in report.queue_rows:
        if type(row) is not PaperProbabilityRecommendationQueueRow:
            raise ValueError("queue_report rows must be queue row values")
        _require_hard_flags("queue_row", row)


def _validate_cost_stress_report(report: PaperCostStressReport) -> None:
    _require_hard_flags("cost_stress_report", report)
    for row in report.rows:
        if type(row) is not PaperCostStressScenarioRow:
            raise ValueError("cost_stress_report rows must be stress row values")
        _require_hard_flags("cost_stress_row", row)


def _validate_row_consistency(row: PaperProbabilitySelectionSummaryRow) -> None:
    if (
        row.stress_pass_count + row.stress_watch_count + row.stress_fail_count
        != row.stress_scenario_count
    ):
        raise ValueError("stress counts must sum to stress_scenario_count")
    if row.stress_scenario_count == 0:
        if row.worst_stressed_net_probability_edge is not None:
            raise ValueError("worst_stressed_net_probability_edge must be absent")
        if row.selection_status != "blocked":
            raise ValueError("missing stress rows must be blocked")
    elif row.worst_stressed_net_probability_edge is None:
        raise ValueError("worst_stressed_net_probability_edge is required")
    if row.selection_status == "ready":
        if row.recommended_next_step != "research_review":
            raise ValueError("ready rows must come from research_review")
        if row.stress_fail_count != 0 or row.stress_watch_count != 0:
            raise ValueError("ready rows must have only passing stress scenarios")
    if row.selection_status == "blocked" and row.recommended_next_step == "research_review":
        if row.stress_scenario_count > 0 and row.stress_fail_count == 0:
            raise ValueError("blocked research rows must have failed stress")


def _validate_report_consistency(report: PaperProbabilitySelectionSummaryReport) -> None:
    if report.queue_count != len(report.rows):
        raise ValueError("queue_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.ready_count + report.watch_count + report.blocked_count != report.queue_count:
        raise ValueError("selection counts must sum to queue_count")
    if report.missing_stress_count != sum(
        1 for row in report.rows if row.stress_scenario_count == 0
    ):
        raise ValueError("missing_stress_count must match rows")
    if tuple(row.queue_rank for row in report.rows) != tuple(
        range(1, len(report.rows) + 1),
    ):
        raise ValueError("rows must preserve contiguous queue_rank values")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_reason_codes(
    rows: tuple[PaperProbabilitySelectionSummaryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_probability_queue_rows",)
    if any(row.stress_scenario_count == 0 for row in rows):
        return ("missing_cost_stress",)
    if any(row.selection_status == "blocked" for row in rows):
        return ("blocked_selection_rows_present",)
    if any(row.selection_status == "watch" for row in rows):
        return ("watch_selection_rows_present",)
    return ("ready_selection_rows_present",)


def _status_count(
    rows: tuple[PaperProbabilitySelectionSummaryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.selection_status == status)


def _survival_status_count(
    rows: tuple[PaperCostStressScenarioRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.survival_status == status)


def _worst_stressed_edge(
    rows: tuple[PaperCostStressScenarioRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return min(row.stressed_net_probability_edge for row in rows)


def _normalize_selection_rows(
    value: object,
) -> tuple[PaperProbabilitySelectionSummaryRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperProbabilitySelectionSummaryRow:
            raise ValueError("rows must contain PaperProbabilitySelectionSummaryRow values")
        _require_hard_flags("selection_row", row)
        _validate_row_consistency(row)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    normalized = []
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _normalize_optional_decimal(field_name: str, value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
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


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_recommended_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECOMMENDED_NEXT_STEPS:
        raise ValueError(
            f"{field_name} must be research_review, await_fresh_context, or skip",
        )


def _require_selection_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SELECTION_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperProbabilitySelectionSummaryConfig",
    "PaperProbabilitySelectionSummaryReport",
    "PaperProbabilitySelectionSummaryRow",
    "build_paper_probability_selection_summary_report",
)
