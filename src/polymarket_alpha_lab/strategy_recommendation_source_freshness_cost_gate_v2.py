"""Pure paper-only readiness reducer for supplied recommendation candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_VALUE = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE_VALUE = Decimal("1.000000")
STATUS_VALUES = ("ready", "watch", "blocked")
SIDE_VALUES = ("yes", "no")
STATUS_RANK = {
    "ready": Decimal("0"),
    "watch": Decimal("1"),
    "blocked": Decimal("2"),
}


@dataclass(frozen=True)
class PaperStrategyRecommendationSourceFreshnessCostGateV2Config:
    config_version: str
    max_source_age_seconds: Decimal
    min_evidence_source_count: Decimal
    min_fresh_source_count: Decimal
    max_taker_fee_per_share: Decimal
    max_spread_cost_per_share: Decimal
    max_slippage_cost_per_share: Decimal
    max_total_cost_per_share: Decimal
    max_settlement_lag_seconds: Decimal
    min_liquidity_depth: Decimal
    watch_band_ratio: Decimal = Decimal("0.900000")
    liquidity_watch_multiplier: Decimal = Decimal("1.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperStrategyRecommendationSourceFreshnessCostGateV2Config:
            raise TypeError(
                "PaperStrategyRecommendationSourceFreshnessCostGateV2Config "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Config:
            raise ValueError("config must be exactly the v2 config")
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _positive_seconds("max_source_age_seconds", self.max_source_age_seconds),
        )
        for name in ("min_evidence_source_count", "min_fresh_source_count"):
            object.__setattr__(self, name, _positive_count(name, getattr(self, name)))
        if self.min_fresh_source_count > self.min_evidence_source_count:
            raise ValueError("min_fresh_source_count must not exceed min_evidence_source_count")
        for name in (
            "max_taker_fee_per_share",
            "max_spread_cost_per_share",
            "max_slippage_cost_per_share",
            "max_total_cost_per_share",
            "min_liquidity_depth",
        ):
            object.__setattr__(self, name, _positive_value(name, getattr(self, name)))
        object.__setattr__(
            self,
            "max_settlement_lag_seconds",
            _positive_seconds("max_settlement_lag_seconds", self.max_settlement_lag_seconds),
        )
        object.__setattr__(
            self,
            "watch_band_ratio",
            _watch_band_ratio("watch_band_ratio", self.watch_band_ratio),
        )
        object.__setattr__(
            self,
            "liquidity_watch_multiplier",
            _liquidity_watch_multiplier(
                "liquidity_watch_multiplier",
                self.liquidity_watch_multiplier,
            ),
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationSourceFreshnessCostGateV2Input:
    recommendation_id: str
    market_slug: str
    side: str
    source_count: Decimal
    fresh_source_count: Decimal
    source_age_seconds: Decimal
    taker_fee_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    settlement_lag_seconds: Decimal
    liquidity_depth: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperStrategyRecommendationSourceFreshnessCostGateV2Input:
            raise TypeError(
                "PaperStrategyRecommendationSourceFreshnessCostGateV2Input "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Input:
            raise ValueError("input must be exactly the v2 input")
        for name in ("recommendation_id", "market_slug"):
            _require_text(name, getattr(self, name))
        _require_side(self.side)
        for name in ("source_count", "fresh_source_count"):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        if self.fresh_source_count > self.source_count:
            raise ValueError("fresh_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "source_age_seconds",
            _seconds("source_age_seconds", self.source_age_seconds),
        )
        for name in (
            "taker_fee_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "liquidity_depth",
        ):
            object.__setattr__(self, name, _nonnegative_value(name, getattr(self, name)))
        object.__setattr__(
            self,
            "settlement_lag_seconds",
            _seconds("settlement_lag_seconds", self.settlement_lag_seconds),
        )
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _require_flags("input", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationSourceFreshnessCostGateV2Row:
    recommendation_id: str
    market_slug: str
    side: str
    source_count: Decimal
    fresh_source_count: Decimal
    fresh_source_ratio: Decimal
    source_age_seconds: Decimal
    taker_fee_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    total_cost_per_share: Decimal
    settlement_lag_seconds: Decimal
    liquidity_depth: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperStrategyRecommendationSourceFreshnessCostGateV2Row:
            raise TypeError(
                "PaperStrategyRecommendationSourceFreshnessCostGateV2Row "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Row:
            raise ValueError("row must be exactly the v2 row")
        for name in ("recommendation_id", "market_slug"):
            _require_text(name, getattr(self, name))
        _require_side(self.side)
        for name in ("source_count", "fresh_source_count"):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        if self.fresh_source_count > self.source_count:
            raise ValueError("fresh_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "fresh_source_ratio",
            _nonnegative_value("fresh_source_ratio", self.fresh_source_ratio),
        )
        if self.fresh_source_ratio != _ratio(self.fresh_source_count, self.source_count):
            raise ValueError("fresh_source_ratio must match source counts")
        object.__setattr__(
            self,
            "source_age_seconds",
            _seconds("source_age_seconds", self.source_age_seconds),
        )
        for name in (
            "taker_fee_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "total_cost_per_share",
            "liquidity_depth",
        ):
            object.__setattr__(self, name, _nonnegative_value(name, getattr(self, name)))
        expected_total = _sum_values(
            (
                self.taker_fee_per_share,
                self.spread_cost_per_share,
                self.slippage_cost_per_share,
            ),
        )
        if self.total_cost_per_share != expected_total:
            raise ValueError("total_cost_per_share must match cost components")
        object.__setattr__(
            self,
            "settlement_lag_seconds",
            _seconds("settlement_lag_seconds", self.settlement_lag_seconds),
        )
        _require_status(self.readiness_status)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _require_flags("row", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    recommendation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount:
            raise TypeError(
                "PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount:
            raise ValueError("reason count must be exactly the v2 reason count")
        _require_reason_code(self.reason_code)
        object.__setattr__(self, "count", _positive_count("count", self.count))
        object.__setattr__(
            self,
            "recommendation_ratio",
            _nonnegative_value("recommendation_ratio", self.recommendation_ratio),
        )
        if self.recommendation_ratio > ONE_VALUE:
            raise ValueError("recommendation_ratio must be at most 1.000000")
        _require_flags("reason count", self)


@dataclass(frozen=True)
class PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    observed_average_total_cost_per_share: Decimal
    observed_max_total_cost_per_share: Decimal
    observed_max_settlement_lag_seconds: Decimal
    observed_min_liquidity_depth: Decimal
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...]
    reason_code_counts: tuple[
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
        ...,
    ]
    report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
            raise TypeError(
                "PaperStrategyRecommendationSourceFreshnessCostGateV2Report "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
            raise ValueError("report must be exactly the v2 report")
        object.__setattr__(self, "generated_at", _utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for name in ("recommendation_count", "ready_count", "watch_count", "blocked_count"):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in (
            "observed_average_total_cost_per_share",
            "observed_max_total_cost_per_share",
            "observed_min_liquidity_depth",
        ):
            object.__setattr__(self, name, _nonnegative_value(name, getattr(self, name)))
        object.__setattr__(
            self,
            "observed_max_settlement_lag_seconds",
            _seconds(
                "observed_max_settlement_lag_seconds",
                self.observed_max_settlement_lag_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_digest(self.report_digest)
        if self.report_digest != _report_digest(self):
            raise ValueError("report_digest must match report contents")
        _require_flags("report", self)


def build_paper_strategy_recommendation_source_freshness_cost_gate_v2_report(
    candidates: Iterable[PaperStrategyRecommendationSourceFreshnessCostGateV2Input],
    *,
    config: PaperStrategyRecommendationSourceFreshnessCostGateV2Config,
    generated_at: datetime,
) -> PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
    if type(config) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Config:
        raise ValueError("config must be exactly the v2 config")
    _require_flags("config", config)
    generated = _utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    rows = tuple(sorted((_build_row(item, config) for item in inputs), key=_row_sort_key))
    reason_code_counts = _reason_code_counts(rows)
    return _report_from_parts(
        generated_at=generated,
        config_version=config.config_version,
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def strategy_recommendation_source_freshness_cost_gate_v2_payload(
    report: PaperStrategyRecommendationSourceFreshnessCostGateV2Report,
) -> dict[str, object]:
    if type(report) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
        raise ValueError("report must be exactly the v2 report")
    _require_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "recommendation_count": _count_payload(report.recommendation_count),
        "ready_count": _count_payload(report.ready_count),
        "watch_count": _count_payload(report.watch_count),
        "blocked_count": _count_payload(report.blocked_count),
        "observed_average_total_cost_per_share": _value_payload(
            report.observed_average_total_cost_per_share,
        ),
        "observed_max_total_cost_per_share": _value_payload(
            report.observed_max_total_cost_per_share,
        ),
        "observed_max_settlement_lag_seconds": _count_payload(
            report.observed_max_settlement_lag_seconds,
        ),
        "observed_min_liquidity_depth": _value_payload(report.observed_min_liquidity_depth),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "report_digest": report.report_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...],
    reason_code_counts: tuple[
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
        ...,
    ],
    report_digest: str | None = None,
) -> PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
    recommendation_count = _count("recommendation_count", Decimal(len(rows)))
    ready_count = _status_count(rows, "ready")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    observed_average_total_cost_per_share = _average_total_cost(rows)
    observed_max_total_cost_per_share = max(
        (row.total_cost_per_share for row in rows),
        default=ZERO_VALUE,
    )
    observed_max_settlement_lag_seconds = max(
        (row.settlement_lag_seconds for row in rows),
        default=ZERO_COUNT,
    )
    observed_min_liquidity_depth = min(
        (row.liquidity_depth for row in rows),
        default=ZERO_VALUE,
    )
    digest = report_digest or _report_digest_from_parts(
        generated_at=generated_at,
        config_version=config_version,
        recommendation_count=recommendation_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        observed_average_total_cost_per_share=observed_average_total_cost_per_share,
        observed_max_total_cost_per_share=observed_max_total_cost_per_share,
        observed_max_settlement_lag_seconds=observed_max_settlement_lag_seconds,
        observed_min_liquidity_depth=observed_min_liquidity_depth,
        rows=rows,
        reason_code_counts=reason_code_counts,
    )
    return PaperStrategyRecommendationSourceFreshnessCostGateV2Report(
        generated_at=generated_at,
        config_version=config_version,
        recommendation_count=recommendation_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        observed_average_total_cost_per_share=observed_average_total_cost_per_share,
        observed_max_total_cost_per_share=observed_max_total_cost_per_share,
        observed_max_settlement_lag_seconds=observed_max_settlement_lag_seconds,
        observed_min_liquidity_depth=observed_min_liquidity_depth,
        rows=rows,
        reason_code_counts=reason_code_counts,
        report_digest=digest,
    )


def _build_row(
    candidate: PaperStrategyRecommendationSourceFreshnessCostGateV2Input,
    config: PaperStrategyRecommendationSourceFreshnessCostGateV2Config,
) -> PaperStrategyRecommendationSourceFreshnessCostGateV2Row:
    total_cost = _sum_values(
        (
            candidate.taker_fee_per_share,
            candidate.spread_cost_per_share,
            candidate.slippage_cost_per_share,
        ),
    )
    reasons = list(candidate.reason_codes)
    blocked = False
    watch = False

    if candidate.source_count < config.min_evidence_source_count:
        blocked = True
        reasons.append("evidence_quorum_below_minimum")
    else:
        reasons.append("evidence_quorum_passed")

    if candidate.fresh_source_count < config.min_fresh_source_count:
        blocked = True
        reasons.append("source_freshness_below_minimum")
    if candidate.source_age_seconds > config.max_source_age_seconds:
        blocked = True
        reasons.append("source_age_above_limit")
    elif candidate.fresh_source_count >= config.min_fresh_source_count:
        if _near_upper_limit(
            candidate.source_age_seconds,
            config.max_source_age_seconds,
            config.watch_band_ratio,
        ):
            watch = True
            reasons.append("source_freshness_near_limit")
        else:
            reasons.append("source_freshness_passed")

    blocked, watch = _append_upper_limit_reason(
        reasons,
        blocked=blocked,
        watch=watch,
        value=candidate.taker_fee_per_share,
        limit=config.max_taker_fee_per_share,
        watch_band_ratio=config.watch_band_ratio,
        reason_base="taker_fee_cost",
    )
    blocked, watch = _append_upper_limit_reason(
        reasons,
        blocked=blocked,
        watch=watch,
        value=candidate.spread_cost_per_share,
        limit=config.max_spread_cost_per_share,
        watch_band_ratio=config.watch_band_ratio,
        reason_base="spread_cost",
    )
    blocked, watch = _append_upper_limit_reason(
        reasons,
        blocked=blocked,
        watch=watch,
        value=candidate.slippage_cost_per_share,
        limit=config.max_slippage_cost_per_share,
        watch_band_ratio=config.watch_band_ratio,
        reason_base="slippage_cost",
    )
    blocked, watch = _append_upper_limit_reason(
        reasons,
        blocked=blocked,
        watch=watch,
        value=total_cost,
        limit=config.max_total_cost_per_share,
        watch_band_ratio=config.watch_band_ratio,
        reason_base="total_cost",
    )
    blocked, watch = _append_upper_limit_reason(
        reasons,
        blocked=blocked,
        watch=watch,
        value=candidate.settlement_lag_seconds,
        limit=config.max_settlement_lag_seconds,
        watch_band_ratio=config.watch_band_ratio,
        reason_base="settlement_lag",
    )
    if candidate.liquidity_depth < config.min_liquidity_depth:
        blocked = True
        reasons.append("liquidity_depth_below_minimum")
    elif candidate.liquidity_depth <= _nonnegative_value(
        "liquidity watch floor",
        config.min_liquidity_depth * config.liquidity_watch_multiplier,
    ):
        watch = True
        reasons.append("liquidity_depth_near_minimum")
    else:
        reasons.append("liquidity_depth_passed")

    return PaperStrategyRecommendationSourceFreshnessCostGateV2Row(
        recommendation_id=candidate.recommendation_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        source_count=candidate.source_count,
        fresh_source_count=candidate.fresh_source_count,
        fresh_source_ratio=_ratio(candidate.fresh_source_count, candidate.source_count),
        source_age_seconds=candidate.source_age_seconds,
        taker_fee_per_share=candidate.taker_fee_per_share,
        spread_cost_per_share=candidate.spread_cost_per_share,
        slippage_cost_per_share=candidate.slippage_cost_per_share,
        total_cost_per_share=total_cost,
        settlement_lag_seconds=candidate.settlement_lag_seconds,
        liquidity_depth=candidate.liquidity_depth,
        readiness_status=_readiness_status(blocked=blocked, watch=watch),
        reason_codes=_reason_codes(tuple(reasons)),
    )


def _append_upper_limit_reason(
    reasons: list[str],
    *,
    blocked: bool,
    watch: bool,
    value: Decimal,
    limit: Decimal,
    watch_band_ratio: Decimal,
    reason_base: str,
) -> tuple[bool, bool]:
    if value > limit:
        reasons.append(f"{reason_base}_above_limit")
        return True, watch
    if _near_upper_limit(value, limit, watch_band_ratio):
        reasons.append(f"{reason_base}_near_limit")
        return blocked, True
    reasons.append(f"{reason_base}_within_limit")
    return blocked, watch


def _near_upper_limit(value: Decimal, limit: Decimal, watch_band_ratio: Decimal) -> bool:
    return value >= _nonnegative_value("near upper limit", limit * watch_band_ratio)


def _readiness_status(*, blocked: bool, watch: bool) -> str:
    if blocked:
        return "blocked"
    if watch:
        return "watch"
    return "ready"


def _normalize_inputs(
    candidates: Iterable[PaperStrategyRecommendationSourceFreshnessCostGateV2Input],
) -> tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Input, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be iterable")
    items = tuple(candidates)
    for item in items:
        if type(item) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Input:
            raise ValueError("candidates must contain only v2 inputs")
        _require_flags("input", item)
    return items


def _normalize_rows(
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...],
) -> tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be tuple")
    for row in rows:
        if type(row) is not PaperStrategyRecommendationSourceFreshnessCostGateV2Row:
            raise ValueError("rows must contain only v2 rows")
        _require_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
        ...,
    ],
) -> tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be tuple")
    for item in counts:
        if type(item) is not PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount:
            raise ValueError("reason_code_counts must contain only v2 reason counts")
        _require_flags("reason count", item)
    if counts != tuple(sorted(counts, key=_reason_code_count_sort_key)):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return counts


def _reason_code_counts(
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...],
) -> tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO_COUNT) + COUNT_QUANTUM
    recommendation_count = _count("recommendation_count", Decimal(len(rows)))
    return tuple(
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=count,
            recommendation_ratio=_ratio(count, recommendation_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _row_sort_key(
    row: PaperStrategyRecommendationSourceFreshnessCostGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        -STATUS_RANK[row.readiness_status],
        -row.total_cost_per_share,
        -row.settlement_lag_seconds,
        row.recommendation_id,
        row.market_slug,
        row.side,
    )


def _reason_code_count_sort_key(
    item: PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
) -> tuple[Decimal, str]:
    return (-item.count, item.reason_code)


def _status_count(
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...],
    readiness_status: str,
) -> Decimal:
    _require_status(readiness_status)
    return _count(
        f"{readiness_status}_count",
        sum(
            (COUNT_QUANTUM for row in rows if row.readiness_status == readiness_status),
            ZERO_COUNT,
        ),
    )


def _average_total_cost(
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_VALUE
    return _nonnegative_value(
        "observed_average_total_cost_per_share",
        _sum_values(tuple(row.total_cost_per_share for row in rows)) / Decimal(len(rows)),
    )


def _validate_report(
    report: PaperStrategyRecommendationSourceFreshnessCostGateV2Report,
) -> None:
    rows = report.rows
    if report.recommendation_count != _count("recommendation_count", Decimal(len(rows))):
        raise ValueError("recommendation_count must match rows")
    if report.ready_count != _status_count(rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.recommendation_count != report.ready_count + report.watch_count + report.blocked_count:
        raise ValueError("recommendation_count must reconcile with status counts")
    if report.observed_average_total_cost_per_share != _average_total_cost(rows):
        raise ValueError("observed_average_total_cost_per_share must match rows")
    if report.observed_max_total_cost_per_share != max(
        (row.total_cost_per_share for row in rows),
        default=ZERO_VALUE,
    ):
        raise ValueError("observed_max_total_cost_per_share must match rows")
    if report.observed_max_settlement_lag_seconds != max(
        (row.settlement_lag_seconds for row in rows),
        default=ZERO_COUNT,
    ):
        raise ValueError("observed_max_settlement_lag_seconds must match rows")
    if report.observed_min_liquidity_depth != min(
        (row.liquidity_depth for row in rows),
        default=ZERO_VALUE,
    ):
        raise ValueError("observed_min_liquidity_depth must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _report_digest(report: PaperStrategyRecommendationSourceFreshnessCostGateV2Report) -> str:
    return _report_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        recommendation_count=report.recommendation_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        observed_average_total_cost_per_share=report.observed_average_total_cost_per_share,
        observed_max_total_cost_per_share=report.observed_max_total_cost_per_share,
        observed_max_settlement_lag_seconds=report.observed_max_settlement_lag_seconds,
        observed_min_liquidity_depth=report.observed_min_liquidity_depth,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
    )


def _report_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    recommendation_count: Decimal,
    ready_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    observed_average_total_cost_per_share: Decimal,
    observed_max_total_cost_per_share: Decimal,
    observed_max_settlement_lag_seconds: Decimal,
    observed_min_liquidity_depth: Decimal,
    rows: tuple[PaperStrategyRecommendationSourceFreshnessCostGateV2Row, ...],
    reason_code_counts: tuple[
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
        ...,
    ],
) -> str:
    pieces = [
        generated_at.isoformat(),
        config_version,
        _count_payload(recommendation_count),
        _count_payload(ready_count),
        _count_payload(watch_count),
        _count_payload(blocked_count),
        _value_payload(observed_average_total_cost_per_share),
        _value_payload(observed_max_total_cost_per_share),
        _count_payload(observed_max_settlement_lag_seconds),
        _value_payload(observed_min_liquidity_depth),
    ]
    for row in rows:
        pieces.extend(_row_digest_parts(row))
    for item in reason_code_counts:
        pieces.extend(
            (
                item.reason_code,
                _count_payload(item.count),
                _value_payload(item.recommendation_ratio),
            ),
        )
    return hashlib.sha256("\x1f".join(pieces).encode("utf-8")).hexdigest()


def _row_digest_parts(
    row: PaperStrategyRecommendationSourceFreshnessCostGateV2Row,
) -> tuple[str, ...]:
    return (
        row.recommendation_id,
        row.market_slug,
        row.side,
        _count_payload(row.source_count),
        _count_payload(row.fresh_source_count),
        _value_payload(row.fresh_source_ratio),
        _count_payload(row.source_age_seconds),
        _value_payload(row.taker_fee_per_share),
        _value_payload(row.spread_cost_per_share),
        _value_payload(row.slippage_cost_per_share),
        _value_payload(row.total_cost_per_share),
        _count_payload(row.settlement_lag_seconds),
        _value_payload(row.liquidity_depth),
        row.readiness_status,
        ",".join(row.reason_codes),
    )


def _row_payload(row: PaperStrategyRecommendationSourceFreshnessCostGateV2Row) -> dict[str, object]:
    _require_flags("row", row)
    return {
        "recommendation_id": row.recommendation_id,
        "market_slug": row.market_slug,
        "side": row.side,
        "source_count": _count_payload(row.source_count),
        "fresh_source_count": _count_payload(row.fresh_source_count),
        "fresh_source_ratio": _value_payload(row.fresh_source_ratio),
        "source_age_seconds": _count_payload(row.source_age_seconds),
        "taker_fee_per_share": _value_payload(row.taker_fee_per_share),
        "spread_cost_per_share": _value_payload(row.spread_cost_per_share),
        "slippage_cost_per_share": _value_payload(row.slippage_cost_per_share),
        "total_cost_per_share": _value_payload(row.total_cost_per_share),
        "settlement_lag_seconds": _count_payload(row.settlement_lag_seconds),
        "liquidity_depth": _value_payload(row.liquidity_depth),
        "readiness_status": row.readiness_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
) -> dict[str, object]:
    _require_flags("reason count", item)
    return {
        "reason_code": item.reason_code,
        "count": _count_payload(item.count),
        "recommendation_ratio": _value_payload(item.recommendation_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _sum_values(values: tuple[Decimal, ...]) -> Decimal:
    return _nonnegative_value("value sum", sum(values, ZERO_VALUE))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _count("ratio numerator", numerator)
    denominator = _count("ratio denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_VALUE
    return _nonnegative_value("ratio", numerator / denominator)


def _utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be canonical text")
    lowered = value.lower()
    if "://" in lowered and "@" in lowered:
        raise ValueError(f"{name} must not contain sensitive text")


def _require_side(value: object) -> None:
    if type(value) is not str or value not in SIDE_VALUES:
        raise ValueError("side must be yes or no")


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError("readiness_status must be ready, watch, or blocked")


def _require_reason_code(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("reason_codes must contain text")
    if value.strip() != value or value.lower() != value:
        raise ValueError("reason_codes must contain canonical values")


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_reason_code(value)
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    return tuple(normalized)


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _nonnegative_value(name: str, value: object) -> Decimal:
    decimal_value = _decimal(name, value)
    if decimal_value < ZERO_VALUE:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value.quantize(VALUE_QUANTUM)


def _positive_value(name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_value(name, value)
    if decimal_value <= ZERO_VALUE:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _count(name: str, value: object) -> Decimal:
    decimal_value = _decimal(name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be whole Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _positive_count(name: str, value: object) -> Decimal:
    count = _count(name, value)
    if count <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return count


def _seconds(name: str, value: object) -> Decimal:
    return _count(name, value)


def _positive_seconds(name: str, value: object) -> Decimal:
    return _positive_count(name, value)


def _watch_band_ratio(name: str, value: object) -> Decimal:
    ratio = _nonnegative_value(name, value)
    if ratio <= ZERO_VALUE or ratio >= ONE_VALUE:
        raise ValueError(f"{name} must be greater than 0 and less than 1")
    return ratio


def _liquidity_watch_multiplier(name: str, value: object) -> Decimal:
    multiplier = _nonnegative_value(name, value)
    if multiplier < ONE_VALUE:
        raise ValueError(f"{name} must be at least 1.000000")
    return multiplier


def _require_digest(value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("report_digest must be a 64 character hexadecimal string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("report_digest must be a 64 character hexadecimal string") from exc


def _require_flags(name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _value_payload(value: Decimal) -> str:
    return format(_nonnegative_value("payload value", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_count("payload count", value)))


__all__ = (
    "PaperStrategyRecommendationSourceFreshnessCostGateV2Config",
    "PaperStrategyRecommendationSourceFreshnessCostGateV2Input",
    "PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount",
    "PaperStrategyRecommendationSourceFreshnessCostGateV2Report",
    "PaperStrategyRecommendationSourceFreshnessCostGateV2Row",
    "build_paper_strategy_recommendation_source_freshness_cost_gate_v2_report",
    "strategy_recommendation_source_freshness_cost_gate_v2_payload",
)
