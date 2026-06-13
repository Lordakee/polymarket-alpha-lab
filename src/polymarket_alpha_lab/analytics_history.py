"""Paper-only history validation for paper analytics reports."""

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.analytics import PaperAnalyticsReport

__all__ = [
    "PaperAnalyticsHistoryConfig",
    "PaperAnalyticsHistoryGateResult",
    "PaperAnalyticsHistoryLog",
    "PaperAnalyticsHistoryReport",
    "PaperAnalyticsHistoryTrend",
    "build_paper_analytics_history_report",
]


RATIO_QUANTUM = Decimal("0.0001")
GATE_NAMES = (
    "data_integrity",
    "sample_size",
    "execution_cost_reality",
    "forecast_edge_quality",
    "risk_drawdown",
)
GATE_STATUSES = frozenset({"pass", "fail", "incomplete"})
HISTORY_STATUSES = frozenset(
    {
        "incomplete_data",
        "insufficient_evidence",
        "blocked_by_risk",
        "paper_review_ready",
    }
)


@dataclass(frozen=True)
class PaperAnalyticsHistoryConfig:
    config_version: str
    min_candidate_observations: int = 200
    min_simulated_trades: int = 50
    min_exited_trades: int = 30
    min_forward_days: int = 28
    max_drawdown_ratio: Decimal = Decimal("0.2000")
    max_market_cost_basis_ratio: Decimal = Decimal("0.5000")
    max_risk_tag_cost_basis_ratio: Decimal = Decimal("0.5000")
    max_no_exit_depth_cost_basis_ratio: Decimal = Decimal("0.1000")
    max_exit_depth_shortfall_ratio: Decimal = Decimal("0.2500")
    max_midpoint_nav_gap_ratio: Decimal = Decimal("0.0500")
    max_breach_count: int = 0

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_candidate_observations",
            "min_simulated_trades",
            "min_exited_trades",
            "min_forward_days",
            "max_breach_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "max_drawdown_ratio",
            "max_market_cost_basis_ratio",
            "max_risk_tag_cost_basis_ratio",
            "max_no_exit_depth_cost_basis_ratio",
            "max_exit_depth_shortfall_ratio",
            "max_midpoint_nav_gap_ratio",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class PaperAnalyticsHistoryGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known analytics history gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known analytics history gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class PaperAnalyticsHistoryTrend:
    marked_at: datetime
    exit_nav: Decimal
    total_exit_pnl: Decimal
    drawdown: Decimal
    drawdown_ratio: Decimal | None
    exit_depth_shortfall_ratio: Decimal | None
    no_exit_depth_cost_basis_ratio: Decimal | None
    midpoint_nav_gap_ratio: Decimal | None
    breach_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "marked_at", _as_utc(self.marked_at))
        _require_nonnegative_decimal("exit_nav", self.exit_nav)
        _require_finite_decimal("total_exit_pnl", self.total_exit_pnl)
        _require_nonnegative_decimal("drawdown", self.drawdown)
        _require_optional_nonnegative_decimal("drawdown_ratio", self.drawdown_ratio)
        _require_optional_nonnegative_decimal(
            "exit_depth_shortfall_ratio",
            self.exit_depth_shortfall_ratio,
        )
        _require_optional_nonnegative_decimal(
            "no_exit_depth_cost_basis_ratio",
            self.no_exit_depth_cost_basis_ratio,
        )
        _require_optional_nonnegative_decimal(
            "midpoint_nav_gap_ratio",
            self.midpoint_nav_gap_ratio,
        )
        _require_nonnegative_int("breach_count", self.breach_count)


@dataclass(frozen=True)
class PaperAnalyticsHistoryReport:
    generated_at: datetime
    config_version: str
    first_marked_at: datetime | None
    last_marked_at: datetime | None
    report_count: int
    candidate_observation_count: int
    simulated_trade_count: int
    exited_trade_count: int
    forward_window_days: int
    unique_market_count: int
    unique_strategy_count: int
    unique_risk_tag_count: int
    latest_exit_nav: Decimal | None
    latest_total_exit_pnl: Decimal | None
    max_drawdown: Decimal | None
    max_drawdown_ratio: Decimal | None
    worst_exit_depth_shortfall_ratio: Decimal | None
    worst_no_exit_depth_cost_basis_ratio: Decimal | None
    worst_midpoint_nav_gap_ratio: Decimal | None
    largest_market_cost_basis_ratio: Decimal | None
    largest_risk_tag_cost_basis_ratio: Decimal | None
    max_breach_count: int
    status: str
    gate_results: tuple[PaperAnalyticsHistoryGateResult, ...]
    trends: tuple[PaperAnalyticsHistoryTrend, ...]
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.first_marked_at is not None:
            object.__setattr__(self, "first_marked_at", _as_utc(self.first_marked_at))
        if self.last_marked_at is not None:
            object.__setattr__(self, "last_marked_at", _as_utc(self.last_marked_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "report_count",
            "candidate_observation_count",
            "simulated_trade_count",
            "exited_trade_count",
            "forward_window_days",
            "unique_market_count",
            "unique_strategy_count",
            "unique_risk_tag_count",
            "max_breach_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_nonnegative_decimal("latest_exit_nav", self.latest_exit_nav)
        _require_optional_finite_decimal("latest_total_exit_pnl", self.latest_total_exit_pnl)
        _require_optional_nonnegative_decimal("max_drawdown", self.max_drawdown)
        _require_optional_nonnegative_decimal("max_drawdown_ratio", self.max_drawdown_ratio)
        _require_optional_nonnegative_decimal(
            "worst_exit_depth_shortfall_ratio",
            self.worst_exit_depth_shortfall_ratio,
        )
        _require_optional_nonnegative_decimal(
            "worst_no_exit_depth_cost_basis_ratio",
            self.worst_no_exit_depth_cost_basis_ratio,
        )
        _require_optional_nonnegative_decimal(
            "worst_midpoint_nav_gap_ratio",
            self.worst_midpoint_nav_gap_ratio,
        )
        _require_optional_nonnegative_decimal(
            "largest_market_cost_basis_ratio",
            self.largest_market_cost_basis_ratio,
        )
        _require_optional_nonnegative_decimal(
            "largest_risk_tag_cost_basis_ratio",
            self.largest_risk_tag_cost_basis_ratio,
        )
        if self.status not in HISTORY_STATUSES:
            raise ValueError("status must be a known analytics history report status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                PaperAnalyticsHistoryGateResult,
            ),
        )
        object.__setattr__(
            self,
            "trends",
            _normalize_typed_tuple("trends", self.trends, PaperAnalyticsHistoryTrend),
        )
        if tuple(gate.gate_name for gate in self.gate_results) != GATE_NAMES:
            raise ValueError("gate_results must contain the five analytics history gates")
        if self.report_count != len(self.trends):
            raise ValueError("report_count must equal trends length")
        if self.report_count == 0:
            if self.first_marked_at is not None or self.last_marked_at is not None:
                raise ValueError("marked_at bounds must be absent without reports")
            if self.latest_exit_nav is not None or self.latest_total_exit_pnl is not None:
                raise ValueError("latest values must be absent without reports")
        else:
            if self.first_marked_at is None or self.last_marked_at is None:
                raise ValueError("marked_at bounds are required with reports")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")


@dataclass(frozen=True)
class PaperAnalyticsHistoryLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperAnalyticsHistoryReport) -> None:
        if not isinstance(report, PaperAnalyticsHistoryReport):
            raise ValueError("report must be a PaperAnalyticsHistoryReport")
        _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_analytics_history_report(
    reports: Iterable[PaperAnalyticsReport],
    *,
    config: PaperAnalyticsHistoryConfig,
    generated_at: datetime,
    candidate_observation_count: int = 0,
    simulated_trade_count: int = 0,
    exited_trade_count: int = 0,
) -> PaperAnalyticsHistoryReport:
    if isinstance(reports, (str, bytes)):
        raise ValueError("reports must be an iterable of PaperAnalyticsReport values")
    if not isinstance(config, PaperAnalyticsHistoryConfig):
        raise ValueError("config must be a PaperAnalyticsHistoryConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    _require_nonnegative_int("candidate_observation_count", candidate_observation_count)
    _require_nonnegative_int("simulated_trade_count", simulated_trade_count)
    _require_nonnegative_int("exited_trade_count", exited_trade_count)
    try:
        report_items = tuple(reports)
    except TypeError as exc:
        raise ValueError("reports must be an iterable of PaperAnalyticsReport values") from exc
    for report in report_items:
        if not isinstance(report, PaperAnalyticsReport):
            raise ValueError("reports must contain PaperAnalyticsReport values")
        if report.paper_only is not True:
            raise ValueError("reports must be paper-only")

    sorted_reports = tuple(sorted(report_items, key=lambda item: _as_utc(item.marked_at)))
    seen_marked_at: set[datetime] = set()
    for report in sorted_reports:
        marked_at = _as_utc(report.marked_at)
        if marked_at in seen_marked_at:
            raise ValueError("duplicate marked_at values are not allowed")
        seen_marked_at.add(marked_at)

    report_count = len(sorted_reports)
    first_marked_at = _as_utc(sorted_reports[0].marked_at) if sorted_reports else None
    last_marked_at = _as_utc(sorted_reports[-1].marked_at) if sorted_reports else None
    forward_window_days = (
        (last_marked_at.date() - first_marked_at.date()).days
        if first_marked_at is not None and last_marked_at is not None
        else 0
    )

    trends = _build_trends(sorted_reports)
    max_drawdown = _max_optional((trend.drawdown for trend in trends))
    max_drawdown_ratio = _max_optional((trend.drawdown_ratio for trend in trends))
    worst_exit_depth_shortfall_ratio = _max_optional(
        report.exit_depth_shortfall_ratio for report in sorted_reports
    )
    worst_no_exit_depth_cost_basis_ratio = _max_optional(
        report.no_exit_depth_cost_basis_ratio for report in sorted_reports
    )
    worst_midpoint_nav_gap_ratio = _max_optional(
        (report.performance.midpoint_nav_gap_ratio for report in sorted_reports),
        absolute=True,
    )
    largest_market_cost_basis_ratio = _max_bucket_ratio(sorted_reports, "market_slug")
    largest_risk_tag_cost_basis_ratio = _max_bucket_ratio(sorted_reports, "risk_tag")
    max_breach_count = max((len(report.breaches) for report in sorted_reports), default=0)

    gate_results = _build_gate_results(
        report_count=report_count,
        config=config,
        candidate_observation_count=candidate_observation_count,
        simulated_trade_count=simulated_trade_count,
        exited_trade_count=exited_trade_count,
        forward_window_days=forward_window_days,
        worst_exit_depth_shortfall_ratio=worst_exit_depth_shortfall_ratio,
        worst_no_exit_depth_cost_basis_ratio=worst_no_exit_depth_cost_basis_ratio,
        max_drawdown_ratio=max_drawdown_ratio,
        largest_market_cost_basis_ratio=largest_market_cost_basis_ratio,
        largest_risk_tag_cost_basis_ratio=largest_risk_tag_cost_basis_ratio,
        worst_midpoint_nav_gap_ratio=worst_midpoint_nav_gap_ratio,
        max_breach_count=max_breach_count,
    )
    status = _history_status(report_count, gate_results)

    return PaperAnalyticsHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        first_marked_at=first_marked_at,
        last_marked_at=last_marked_at,
        report_count=report_count,
        candidate_observation_count=candidate_observation_count,
        simulated_trade_count=simulated_trade_count,
        exited_trade_count=exited_trade_count,
        forward_window_days=forward_window_days,
        unique_market_count=len(_unique_markets(sorted_reports)),
        unique_strategy_count=len(_unique_strategies(sorted_reports)),
        unique_risk_tag_count=len(_unique_risk_tags(sorted_reports)),
        latest_exit_nav=sorted_reports[-1].performance.exit_nav if sorted_reports else None,
        latest_total_exit_pnl=(
            sorted_reports[-1].performance.total_exit_pnl if sorted_reports else None
        ),
        max_drawdown=max_drawdown,
        max_drawdown_ratio=max_drawdown_ratio,
        worst_exit_depth_shortfall_ratio=worst_exit_depth_shortfall_ratio,
        worst_no_exit_depth_cost_basis_ratio=worst_no_exit_depth_cost_basis_ratio,
        worst_midpoint_nav_gap_ratio=worst_midpoint_nav_gap_ratio,
        largest_market_cost_basis_ratio=largest_market_cost_basis_ratio,
        largest_risk_tag_cost_basis_ratio=largest_risk_tag_cost_basis_ratio,
        max_breach_count=max_breach_count,
        status=status,
        gate_results=gate_results,
        trends=trends,
    )


def _build_trends(
    reports: tuple[PaperAnalyticsReport, ...],
) -> tuple[PaperAnalyticsHistoryTrend, ...]:
    high_watermark_nav: Decimal | None = None
    trends: list[PaperAnalyticsHistoryTrend] = []
    for report in reports:
        exit_nav = report.performance.exit_nav
        if high_watermark_nav is None or exit_nav >= high_watermark_nav:
            high_watermark_nav = exit_nav
        drawdown = high_watermark_nav - exit_nav
        trends.append(
            PaperAnalyticsHistoryTrend(
                marked_at=report.marked_at,
                exit_nav=exit_nav,
                total_exit_pnl=report.performance.total_exit_pnl,
                drawdown=drawdown,
                drawdown_ratio=_ratio_or_none(drawdown, high_watermark_nav),
                exit_depth_shortfall_ratio=report.exit_depth_shortfall_ratio,
                no_exit_depth_cost_basis_ratio=report.no_exit_depth_cost_basis_ratio,
                midpoint_nav_gap_ratio=(
                    abs(report.performance.midpoint_nav_gap_ratio)
                    if report.performance.midpoint_nav_gap_ratio is not None
                    else None
                ),
                breach_count=len(report.breaches),
            )
        )
    return tuple(trends)


def _build_gate_results(
    *,
    report_count: int,
    config: PaperAnalyticsHistoryConfig,
    candidate_observation_count: int,
    simulated_trade_count: int,
    exited_trade_count: int,
    forward_window_days: int,
    worst_exit_depth_shortfall_ratio: Decimal | None,
    worst_no_exit_depth_cost_basis_ratio: Decimal | None,
    max_drawdown_ratio: Decimal | None,
    largest_market_cost_basis_ratio: Decimal | None,
    largest_risk_tag_cost_basis_ratio: Decimal | None,
    worst_midpoint_nav_gap_ratio: Decimal | None,
    max_breach_count: int,
) -> tuple[PaperAnalyticsHistoryGateResult, ...]:
    if report_count == 0:
        return tuple(
            PaperAnalyticsHistoryGateResult(
                gate_name=gate_name,
                status="incomplete",
                message="No paper analytics reports are available.",
            )
            for gate_name in GATE_NAMES
        )

    sample_passes = (
        candidate_observation_count >= config.min_candidate_observations
        and simulated_trade_count >= config.min_simulated_trades
        and exited_trade_count >= config.min_exited_trades
        and forward_window_days >= config.min_forward_days
    )
    execution_fails = _breaches_threshold(
        worst_exit_depth_shortfall_ratio,
        config.max_exit_depth_shortfall_ratio,
    ) or _breaches_threshold(
        worst_no_exit_depth_cost_basis_ratio,
        config.max_no_exit_depth_cost_basis_ratio,
    )
    risk_fails = (
        _breaches_threshold(max_drawdown_ratio, config.max_drawdown_ratio)
        or _breaches_threshold(
            largest_market_cost_basis_ratio,
            config.max_market_cost_basis_ratio,
        )
        or _breaches_threshold(
            largest_risk_tag_cost_basis_ratio,
            config.max_risk_tag_cost_basis_ratio,
        )
        or _breaches_threshold(
            worst_midpoint_nav_gap_ratio,
            config.max_midpoint_nav_gap_ratio,
        )
        or max_breach_count > config.max_breach_count
    )

    return (
        PaperAnalyticsHistoryGateResult(
            gate_name="data_integrity",
            status="pass",
            message="Input paper analytics reports are sorted and duplicate-free.",
            observed_value=f"report_count={report_count}",
            threshold="report_count>0",
        ),
        PaperAnalyticsHistoryGateResult(
            gate_name="sample_size",
            status="pass" if sample_passes else "fail",
            message=(
                "Paper sample-size thresholds are met."
                if sample_passes
                else "Paper sample-size thresholds are not met."
            ),
            observed_value=(
                "candidate_observation_count="
                f"{candidate_observation_count}; simulated_trade_count={simulated_trade_count}; "
                f"exited_trade_count={exited_trade_count}; forward_window_days={forward_window_days}"
            ),
            threshold=(
                "min_candidate_observations="
                f"{config.min_candidate_observations}; min_simulated_trades="
                f"{config.min_simulated_trades}; min_exited_trades="
                f"{config.min_exited_trades}; min_forward_days={config.min_forward_days}"
            ),
        ),
        PaperAnalyticsHistoryGateResult(
            gate_name="execution_cost_reality",
            status="fail" if execution_fails else "pass",
            message=(
                "Paper exit-liquidity thresholds are breached."
                if execution_fails
                else "Paper exit-liquidity thresholds are within limits."
            ),
            observed_value=(
                "exit_depth_shortfall_ratio="
                f"{_display_optional_decimal(worst_exit_depth_shortfall_ratio)}; "
                "no_exit_depth_cost_basis_ratio="
                f"{_display_optional_decimal(worst_no_exit_depth_cost_basis_ratio)}"
            ),
            threshold=(
                "max_exit_depth_shortfall_ratio="
                f"{config.max_exit_depth_shortfall_ratio}; "
                "max_no_exit_depth_cost_basis_ratio="
                f"{config.max_no_exit_depth_cost_basis_ratio}"
            ),
        ),
        PaperAnalyticsHistoryGateResult(
            gate_name="forecast_edge_quality",
            status="incomplete",
            message="Resolved-outcome forecast quality evidence is deferred beyond Node 4.",
        ),
        PaperAnalyticsHistoryGateResult(
            gate_name="risk_drawdown",
            status="fail" if risk_fails else "pass",
            message=(
                "Paper risk or drawdown thresholds are breached."
                if risk_fails
                else "Paper risk and drawdown thresholds are within limits."
            ),
            observed_value=(
                f"max_drawdown_ratio={_display_optional_decimal(max_drawdown_ratio)}; "
                "market_cost_basis_ratio="
                f"{_display_optional_decimal(largest_market_cost_basis_ratio)}; "
                "risk_tag_cost_basis_ratio="
                f"{_display_optional_decimal(largest_risk_tag_cost_basis_ratio)}; "
                "midpoint_nav_gap_ratio="
                f"{_display_optional_decimal(worst_midpoint_nav_gap_ratio)}; "
                f"max_breach_count={max_breach_count}"
            ),
            threshold=(
                f"max_drawdown_ratio={config.max_drawdown_ratio}; "
                f"max_market_cost_basis_ratio={config.max_market_cost_basis_ratio}; "
                f"max_risk_tag_cost_basis_ratio={config.max_risk_tag_cost_basis_ratio}; "
                f"max_midpoint_nav_gap_ratio={config.max_midpoint_nav_gap_ratio}; "
                f"max_breach_count={config.max_breach_count}"
            ),
        ),
    )


def _history_status(
    report_count: int,
    gate_results: tuple[PaperAnalyticsHistoryGateResult, ...],
) -> str:
    gates = {gate.gate_name: gate for gate in gate_results}
    if report_count == 0 or gates["data_integrity"].status == "incomplete":
        return "incomplete_data"
    if (
        gates["execution_cost_reality"].status == "fail"
        or gates["risk_drawdown"].status == "fail"
    ):
        return "blocked_by_risk"
    if gates["sample_size"].status == "fail":
        return "insufficient_evidence"
    return "paper_review_ready"


def _unique_markets(reports: tuple[PaperAnalyticsReport, ...]) -> frozenset[str]:
    return frozenset(
        exposure.market_slug for report in reports for exposure in report.position_exposures
    )


def _unique_strategies(reports: tuple[PaperAnalyticsReport, ...]) -> frozenset[str]:
    return frozenset(
        exposure.strategy_type for report in reports for exposure in report.position_exposures
    )


def _unique_risk_tags(reports: tuple[PaperAnalyticsReport, ...]) -> frozenset[str]:
    return frozenset(
        risk_tag
        for report in reports
        for exposure in report.position_exposures
        for risk_tag in exposure.risk_tags
    )


def _max_bucket_ratio(
    reports: tuple[PaperAnalyticsReport, ...],
    bucket_type: str,
) -> Decimal | None:
    return _max_optional(
        bucket.cost_basis_ratio_to_starting_cash
        for report in reports
        for bucket in report.buckets
        if bucket.bucket_type == bucket_type
    )


def _max_optional(
    values: Iterable[Decimal | None],
    *,
    absolute: bool = False,
) -> Decimal | None:
    sampled: list[Decimal] = []
    for value in values:
        if value is None:
            continue
        _require_finite_decimal("value", value)
        sampled.append(abs(value) if absolute else value)
    return max(sampled) if sampled else None


def _breaches_threshold(value: Decimal | None, threshold: Decimal) -> bool:
    return value is not None and value > threshold


def _display_optional_decimal(value: Decimal | None) -> str:
    return "None" if value is None else str(value)


def _ratio_or_none(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    _require_finite_decimal("numerator", numerator)
    _require_finite_decimal("denominator", denominator)
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(RATIO_QUANTUM)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} is required")


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
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_gate_value(field_name: str, value: Decimal | int | str | None) -> None:
    if value is None:
        return
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
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


def _normalize_typed_tuple(
    field_name: str,
    values: Iterable[Any],
    expected_type: type[Any],
) -> tuple[Any, ...]:
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if not isinstance(item, expected_type):
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


def _validate_report_tree(report: PaperAnalyticsHistoryReport) -> None:
    gate_results = tuple(
        PaperAnalyticsHistoryGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    trends = tuple(
        PaperAnalyticsHistoryTrend(
            marked_at=trend.marked_at,
            exit_nav=trend.exit_nav,
            total_exit_pnl=trend.total_exit_pnl,
            drawdown=trend.drawdown,
            drawdown_ratio=trend.drawdown_ratio,
            exit_depth_shortfall_ratio=trend.exit_depth_shortfall_ratio,
            no_exit_depth_cost_basis_ratio=trend.no_exit_depth_cost_basis_ratio,
            midpoint_nav_gap_ratio=trend.midpoint_nav_gap_ratio,
            breach_count=trend.breach_count,
        )
        for trend in report.trends
    )
    PaperAnalyticsHistoryReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        first_marked_at=report.first_marked_at,
        last_marked_at=report.last_marked_at,
        report_count=report.report_count,
        candidate_observation_count=report.candidate_observation_count,
        simulated_trade_count=report.simulated_trade_count,
        exited_trade_count=report.exited_trade_count,
        forward_window_days=report.forward_window_days,
        unique_market_count=report.unique_market_count,
        unique_strategy_count=report.unique_strategy_count,
        unique_risk_tag_count=report.unique_risk_tag_count,
        latest_exit_nav=report.latest_exit_nav,
        latest_total_exit_pnl=report.latest_total_exit_pnl,
        max_drawdown=report.max_drawdown,
        max_drawdown_ratio=report.max_drawdown_ratio,
        worst_exit_depth_shortfall_ratio=report.worst_exit_depth_shortfall_ratio,
        worst_no_exit_depth_cost_basis_ratio=report.worst_no_exit_depth_cost_basis_ratio,
        worst_midpoint_nav_gap_ratio=report.worst_midpoint_nav_gap_ratio,
        largest_market_cost_basis_ratio=report.largest_market_cost_basis_ratio,
        largest_risk_tag_cost_basis_ratio=report.largest_risk_tag_cost_basis_ratio,
        max_breach_count=report.max_breach_count,
        status=report.status,
        gate_results=gate_results,
        trends=trends,
        paper_only=report.paper_only,
    )


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("analytics history log Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("analytics history log float values must be finite Decimal values")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("analytics history log object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("analytics history log values must be JSON serializable")


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
