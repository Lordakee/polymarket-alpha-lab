"""Pure in-memory portfolio-fit digest reducer for strategy recommendations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_PORTFOLIO_FIT_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationPortfolioFitDigestConfig",
    "StrategyRecommendationPortfolioFitDigestInput",
    "StrategyRecommendationPortfolioFitDigestReasonCodeCount",
    "StrategyRecommendationPortfolioFitDigestReport",
    "StrategyRecommendationPortfolioFitDigestRow",
    "build_strategy_recommendation_portfolio_fit_digest_report",
    "strategy_recommendation_portfolio_fit_digest_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_PORTFOLIO_FIT_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-portfolio-fit-digest-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}


@dataclass(frozen=True)
class StrategyRecommendationPortfolioFitDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_PORTFOLIO_FIT_DIGEST_CONFIG_VERSION
    )
    category_watch_share: Decimal = Decimal("0.500000")
    category_block_share: Decimal = Decimal("0.700000")
    event_overlap_watch_share: Decimal = Decimal("0.400000")
    event_overlap_block_share: Decimal = Decimal("0.600000")
    cash_watch_remaining: Decimal = Decimal("100.000000")
    cash_block_remaining: Decimal = Decimal("0.000000")
    capacity_watch_ratio: Decimal = Decimal("1.500000")
    capacity_block_ratio: Decimal = Decimal("1.000000")
    tail_cluster_watch_share: Decimal = Decimal("0.300000")
    tail_cluster_block_share: Decimal = Decimal("0.500000")
    settlement_watch_share: Decimal = Decimal("0.300000")
    settlement_block_share: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_watch_share",
            "category_block_share",
            "event_overlap_watch_share",
            "event_overlap_block_share",
            "tail_cluster_watch_share",
            "tail_cluster_block_share",
            "settlement_watch_share",
            "settlement_block_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cash_watch_remaining",
            "cash_block_remaining",
            "capacity_watch_ratio",
            "capacity_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most("category_watch_share", self.category_watch_share, self.category_block_share)
        _require_at_most(
            "event_overlap_watch_share",
            self.event_overlap_watch_share,
            self.event_overlap_block_share,
        )
        _require_at_most(
            "tail_cluster_watch_share",
            self.tail_cluster_watch_share,
            self.tail_cluster_block_share,
        )
        _require_at_most(
            "settlement_watch_share",
            self.settlement_watch_share,
            self.settlement_block_share,
        )
        _require_at_most("cash_block_remaining", self.cash_block_remaining, self.cash_watch_remaining)
        _require_at_most("capacity_block_ratio", self.capacity_block_ratio, self.capacity_watch_ratio)
        require_paper_only_flags("StrategyRecommendationPortfolioFitDigestConfig", self)


@dataclass(frozen=True)
class StrategyRecommendationPortfolioFitDigestInput:
    recommendation_id: str
    market_slug: str
    category_id: str
    event_id: str
    tail_cluster_id: str
    candidate_notional: Decimal
    available_cash: Decimal
    liquidity_capacity: Decimal
    existing_category_notional: Decimal
    existing_event_notional: Decimal
    existing_tail_cluster_notional: Decimal
    settlement_lockup_notional: Decimal
    unresolved_settlement_notional: Decimal
    portfolio_notional: Decimal
    expected_settlement_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "market_slug",
            "category_id",
            "event_id",
            "tail_cluster_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "candidate_notional",
            "available_cash",
            "liquidity_capacity",
            "existing_category_notional",
            "existing_event_notional",
            "existing_tail_cluster_notional",
            "settlement_lockup_notional",
            "unresolved_settlement_notional",
            "portfolio_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_settlement_at",
            _as_utc("expected_settlement_at", self.expected_settlement_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("StrategyRecommendationPortfolioFitDigestInput", self)


@dataclass(frozen=True)
class StrategyRecommendationPortfolioFitDigestRow:
    recommendation_id: str
    market_slug: str
    category_id: str
    event_id: str
    tail_cluster_id: str
    fit_status: str
    candidate_notional: Decimal
    available_cash: Decimal
    liquidity_capacity: Decimal
    existing_category_notional: Decimal
    category_exposure_after_candidate: Decimal
    category_exposure_share: Decimal
    existing_event_notional: Decimal
    event_overlap_after_candidate: Decimal
    event_overlap_share: Decimal
    cash_remaining_after_candidate: Decimal
    capacity_ratio: Decimal
    existing_tail_cluster_notional: Decimal
    tail_cluster_after_candidate: Decimal
    tail_cluster_share: Decimal
    settlement_lockup_notional: Decimal
    unresolved_settlement_notional: Decimal
    settlement_notional_after_candidate: Decimal
    settlement_share: Decimal
    portfolio_notional: Decimal
    expected_settlement_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "market_slug",
            "category_id",
            "event_id",
            "tail_cluster_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("fit_status", self.fit_status)
        for field_name in (
            "candidate_notional",
            "available_cash",
            "liquidity_capacity",
            "existing_category_notional",
            "category_exposure_after_candidate",
            "category_exposure_share",
            "existing_event_notional",
            "event_overlap_after_candidate",
            "event_overlap_share",
            "cash_remaining_after_candidate",
            "capacity_ratio",
            "existing_tail_cluster_notional",
            "tail_cluster_after_candidate",
            "tail_cluster_share",
            "settlement_lockup_notional",
            "unresolved_settlement_notional",
            "settlement_notional_after_candidate",
            "settlement_share",
            "portfolio_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_settlement_at",
            _as_utc("expected_settlement_at", self.expected_settlement_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.fit_status != _row_status(self.reason_codes):
            raise ValueError("fit_status must match reason_codes")
        require_paper_only_flags("StrategyRecommendationPortfolioFitDigestRow", self)


@dataclass(frozen=True)
class StrategyRecommendationPortfolioFitDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags(
            "StrategyRecommendationPortfolioFitDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationPortfolioFitDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_category_exposure_share: Decimal
    max_event_overlap_share: Decimal
    min_cash_remaining_after_candidate: Decimal
    min_capacity_ratio: Decimal
    max_tail_cluster_share: Decimal
    max_settlement_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyRecommendationPortfolioFitDigestReasonCodeCount, ...]
    recommendation_rows: tuple[StrategyRecommendationPortfolioFitDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_category_exposure_share",
            "max_event_overlap_share",
            "min_cash_remaining_after_candidate",
            "min_capacity_ratio",
            "max_tail_cluster_share",
            "max_settlement_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_ordered_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "recommendation_rows", _normalize_rows(self.recommendation_rows))
        _validate_report(self)
        reject_unsafe_surface_fields("portfolio fit digest report", self)
        require_paper_only_flags("StrategyRecommendationPortfolioFitDigestReport", self)


def build_strategy_recommendation_portfolio_fit_digest_report(
    recommendations: Iterable[StrategyRecommendationPortfolioFitDigestInput],
    *,
    config: StrategyRecommendationPortfolioFitDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationPortfolioFitDigestReport:
    if type(config) is not StrategyRecommendationPortfolioFitDigestConfig:
        raise ValueError("config must be a StrategyRecommendationPortfolioFitDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(recommendations)
    rows = tuple(
        sorted(
            (_digest_row(row, config=config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationPortfolioFitDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_category_exposure_share=_max_decimal(
            tuple(row.category_exposure_share for row in rows),
        ),
        max_event_overlap_share=_max_decimal(tuple(row.event_overlap_share for row in rows)),
        min_cash_remaining_after_candidate=_min_decimal(
            tuple(row.cash_remaining_after_candidate for row in rows),
        ),
        min_capacity_ratio=_min_decimal(tuple(row.capacity_ratio for row in rows)),
        max_tail_cluster_share=_max_decimal(tuple(row.tail_cluster_share for row in rows)),
        max_settlement_share=_max_decimal(tuple(row.settlement_share for row in rows)),
        status=_rollup_status(tuple(row.fit_status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        recommendation_rows=rows,
    )


def strategy_recommendation_portfolio_fit_digest_payload(
    report: StrategyRecommendationPortfolioFitDigestReport | dict[str, Any],
) -> dict[str, Any]:
    reject_unsafe_surface_fields("portfolio fit digest payload", report)
    if type(report) is dict:
        _reject_unsafe_payload_values("portfolio fit digest payload", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    reject_unsafe_surface_fields("portfolio fit digest payload", payload)
    _reject_unsafe_payload_values("portfolio fit digest payload", payload)
    return payload


def _digest_row(
    recommendation: StrategyRecommendationPortfolioFitDigestInput,
    *,
    config: StrategyRecommendationPortfolioFitDigestConfig,
) -> StrategyRecommendationPortfolioFitDigestRow:
    total_after_candidate = _add_decimal(
        recommendation.portfolio_notional,
        recommendation.candidate_notional,
    )
    category_after_candidate = _add_decimal(
        recommendation.existing_category_notional,
        recommendation.candidate_notional,
    )
    event_after_candidate = _add_decimal(
        recommendation.existing_event_notional,
        recommendation.candidate_notional,
    )
    cash_remaining = _remaining(
        recommendation.available_cash,
        recommendation.candidate_notional,
    )
    capacity_ratio = _ratio(
        recommendation.liquidity_capacity,
        recommendation.candidate_notional,
    )
    tail_after_candidate = _add_decimal(
        recommendation.existing_tail_cluster_notional,
        recommendation.candidate_notional,
    )
    settlement_after_candidate = _add_decimal(
        recommendation.unresolved_settlement_notional,
        recommendation.settlement_lockup_notional,
    )
    reason_codes = _row_reason_codes(
        recommendation=recommendation,
        config=config,
        category_exposure_share=_ratio(category_after_candidate, total_after_candidate),
        event_overlap_share=_ratio(event_after_candidate, total_after_candidate),
        cash_remaining_after_candidate=cash_remaining,
        capacity_ratio=capacity_ratio,
        tail_cluster_share=_ratio(tail_after_candidate, total_after_candidate),
        settlement_share=_ratio(settlement_after_candidate, total_after_candidate),
    )
    return StrategyRecommendationPortfolioFitDigestRow(
        recommendation_id=recommendation.recommendation_id,
        market_slug=recommendation.market_slug,
        category_id=recommendation.category_id,
        event_id=recommendation.event_id,
        tail_cluster_id=recommendation.tail_cluster_id,
        fit_status=_row_status(reason_codes),
        candidate_notional=recommendation.candidate_notional,
        available_cash=recommendation.available_cash,
        liquidity_capacity=recommendation.liquidity_capacity,
        existing_category_notional=recommendation.existing_category_notional,
        category_exposure_after_candidate=category_after_candidate,
        category_exposure_share=_ratio(category_after_candidate, total_after_candidate),
        existing_event_notional=recommendation.existing_event_notional,
        event_overlap_after_candidate=event_after_candidate,
        event_overlap_share=_ratio(event_after_candidate, total_after_candidate),
        cash_remaining_after_candidate=cash_remaining,
        capacity_ratio=capacity_ratio,
        existing_tail_cluster_notional=recommendation.existing_tail_cluster_notional,
        tail_cluster_after_candidate=tail_after_candidate,
        tail_cluster_share=_ratio(tail_after_candidate, total_after_candidate),
        settlement_lockup_notional=recommendation.settlement_lockup_notional,
        unresolved_settlement_notional=recommendation.unresolved_settlement_notional,
        settlement_notional_after_candidate=settlement_after_candidate,
        settlement_share=_ratio(settlement_after_candidate, total_after_candidate),
        portfolio_notional=recommendation.portfolio_notional,
        expected_settlement_at=recommendation.expected_settlement_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    recommendation: StrategyRecommendationPortfolioFitDigestInput,
    config: StrategyRecommendationPortfolioFitDigestConfig,
    category_exposure_share: Decimal,
    event_overlap_share: Decimal,
    cash_remaining_after_candidate: Decimal,
    capacity_ratio: Decimal,
    tail_cluster_share: Decimal,
    settlement_share: Decimal,
) -> tuple[str, ...]:
    reasons = [*recommendation.reason_codes]
    _append_upper_threshold_reason(
        reasons,
        category_exposure_share,
        watch_threshold=config.category_watch_share,
        block_threshold=config.category_block_share,
        watch_reason="portfolio_fit_category_exposure_watch",
        block_reason="portfolio_fit_category_exposure_blocked",
    )
    _append_upper_threshold_reason(
        reasons,
        event_overlap_share,
        watch_threshold=config.event_overlap_watch_share,
        block_threshold=config.event_overlap_block_share,
        watch_reason="portfolio_fit_event_overlap_watch",
        block_reason="portfolio_fit_event_overlap_blocked",
    )
    if (
        recommendation.candidate_notional > recommendation.available_cash
        or cash_remaining_after_candidate < config.cash_block_remaining
    ):
        reasons.append("portfolio_fit_cash_blocked")
    elif cash_remaining_after_candidate < config.cash_watch_remaining:
        reasons.append("portfolio_fit_cash_watch")
    if capacity_ratio < config.capacity_block_ratio:
        reasons.append("portfolio_fit_capacity_ratio_blocked")
    elif capacity_ratio < config.capacity_watch_ratio:
        reasons.append("portfolio_fit_capacity_ratio_watch")
    _append_upper_threshold_reason(
        reasons,
        tail_cluster_share,
        watch_threshold=config.tail_cluster_watch_share,
        block_threshold=config.tail_cluster_block_share,
        watch_reason="portfolio_fit_tail_cluster_watch",
        block_reason="portfolio_fit_tail_cluster_blocked",
    )
    _append_upper_threshold_reason(
        reasons,
        settlement_share,
        watch_threshold=config.settlement_watch_share,
        block_threshold=config.settlement_block_share,
        watch_reason="portfolio_fit_settlement_timing_watch",
        block_reason="portfolio_fit_settlement_timing_blocked",
    )
    if len(reasons) == len(recommendation.reason_codes):
        reasons.append("portfolio_fit_clear")
    return _normalize_reason_codes(tuple(reasons))


def _append_upper_threshold_reason(
    reason_codes: list[str],
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reason_codes.append(block_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _normalize_inputs(
    recommendations: Iterable[StrategyRecommendationPortfolioFitDigestInput],
) -> tuple[StrategyRecommendationPortfolioFitDigestInput, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        normalized = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    for recommendation in normalized:
        if type(recommendation) is not StrategyRecommendationPortfolioFitDigestInput:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationPortfolioFitDigestInput values",
            )
        require_paper_only_flags("recommendation", recommendation)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyRecommendationPortfolioFitDigestRow],
) -> tuple[StrategyRecommendationPortfolioFitDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("recommendation_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("recommendation_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyRecommendationPortfolioFitDigestRow:
            raise ValueError(
                "recommendation_rows must contain "
                "StrategyRecommendationPortfolioFitDigestRow values",
            )
        require_paper_only_flags("recommendation row", row)
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[StrategyRecommendationPortfolioFitDigestReasonCodeCount],
) -> tuple[StrategyRecommendationPortfolioFitDigestReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not StrategyRecommendationPortfolioFitDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyRecommendationPortfolioFitDigestReasonCodeCount values",
            )
        require_paper_only_flags("reason code count", count)
    return tuple(sorted(normalized, key=_reason_code_count_sort_key))


def _validate_report(report: StrategyRecommendationPortfolioFitDigestReport) -> None:
    rows = report.recommendation_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match recommendation_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match recommendation_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match recommendation_rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match recommendation_rows")
    if report.max_category_exposure_share != _max_decimal(
        tuple(row.category_exposure_share for row in rows),
    ):
        raise ValueError("max_category_exposure_share must match recommendation_rows")
    if report.max_event_overlap_share != _max_decimal(
        tuple(row.event_overlap_share for row in rows),
    ):
        raise ValueError("max_event_overlap_share must match recommendation_rows")
    if report.min_cash_remaining_after_candidate != _min_decimal(
        tuple(row.cash_remaining_after_candidate for row in rows),
    ):
        raise ValueError("min_cash_remaining_after_candidate must match recommendation_rows")
    if report.min_capacity_ratio != _min_decimal(tuple(row.capacity_ratio for row in rows)):
        raise ValueError("min_capacity_ratio must match recommendation_rows")
    if report.max_tail_cluster_share != _max_decimal(
        tuple(row.tail_cluster_share for row in rows),
    ):
        raise ValueError("max_tail_cluster_share must match recommendation_rows")
    if report.max_settlement_share != _max_decimal(tuple(row.settlement_share for row in rows)):
        raise ValueError("max_settlement_share must match recommendation_rows")
    if report.status != _rollup_status(tuple(row.fit_status for row in rows)):
        raise ValueError("status must match recommendation_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match recommendation_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match recommendation_rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("recommendation_rows must be sorted")


def _row_sort_key(
    row: StrategyRecommendationPortfolioFitDigestRow,
) -> tuple[Any, ...]:
    return (
        -STATUS_WEIGHT[row.fit_status],
        -row.candidate_notional,
        -row.category_exposure_share,
        row.recommendation_id,
        row.market_slug,
        row.category_id,
        row.event_id,
        row.tail_cluster_id,
        row.expected_settlement_at,
        row.available_cash,
        row.liquidity_capacity,
        row.existing_event_notional,
        row.existing_tail_cluster_notional,
        row.settlement_lockup_notional,
        row.unresolved_settlement_notional,
        row.portfolio_notional,
        row.reason_codes,
    )


def _reason_code_count_sort_key(
    count: StrategyRecommendationPortfolioFitDigestReasonCodeCount,
) -> tuple[Decimal, str]:
    return (-count.count, count.reason_code)


def _status_count(
    rows: tuple[StrategyRecommendationPortfolioFitDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.fit_status == status))


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_blocked") for reason in reason_codes):
        return "blocked"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[StrategyRecommendationPortfolioFitDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("portfolio_fit_digest_empty",)
    row_reasons = _aggregate_reason_codes(
        tuple(reason for row in rows for reason in row.reason_codes),
    )
    status = _rollup_status(tuple(row.fit_status for row in rows))
    if status == "pass":
        return ("portfolio_fit_digest_clear",)
    return (f"portfolio_fit_digest_{status}", *_fit_guard_reasons(row_reasons))


def _fit_guard_reasons(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    excluded = {
        "portfolio_fit_clear",
        "portfolio_fit_input_available",
    }
    return tuple(
        reason
        for reason in reason_codes
        if reason.startswith("portfolio_fit_") and reason not in excluded
    )


def _reject_unsafe_payload_values(label: str, value: object, path: str = "") -> None:
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_payload_values(label, item, item_path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload_values(label, item, item_path)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationPortfolioFitDigestRow, ...],
) -> tuple[StrategyRecommendationPortfolioFitDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    counter = Counter(reason for row in rows for reason in row.reason_codes)
    counts = tuple(
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in counter.items()
    )
    return tuple(sorted(counts, key=_reason_code_count_sort_key))


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_canonical_string("reason_code", reason_code)
    return _aggregate_reason_codes(normalized)


def _normalize_ordered_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_canonical_string("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _aggregate_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(reason_codes)))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_at_most(field_name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{field_name} must not exceed comparison threshold")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _remaining(limit: Decimal, used: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        remaining = _quantize(limit - used)
    if remaining < ZERO:
        return ZERO
    return remaining


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)
