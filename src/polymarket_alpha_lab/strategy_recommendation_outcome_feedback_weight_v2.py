"""Readonly Decimal report for paper outcome feedback recommendation weights."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_STRATEGY_RECOMMENDATION_OUTCOME_FEEDBACK_WEIGHT_V2_CONFIG_VERSION = (
    "strategy-recommendation-outcome-feedback-weight-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

WEIGHT_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "future_weight_pass",
    "future_weight_watch",
    "future_weight_blocked",
    "prior_outcome_strong",
    "prior_outcome_watch",
    "prior_outcome_weak",
    "calibration_accuracy_strong",
    "calibration_accuracy_watch",
    "calibration_accuracy_weak",
    "source_reliability_strong",
    "source_reliability_watch",
    "source_reliability_weak",
    "resolution_lag_fast",
    "resolution_lag_watch",
    "resolution_lag_slow",
    "liquidity_exit_slippage_low",
    "liquidity_exit_slippage_watch",
    "liquidity_exit_slippage_high",
    "specialist_team_performance_strong",
    "specialist_team_performance_watch",
    "specialist_team_performance_weak",
)
REPORT_REASON_CODES = (
    "future_weight_report_passed",
    "future_weight_report_watch_rows",
    "future_weight_report_blocked_rows",
    "future_weight_report_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_OUTCOME_FEEDBACK_WEIGHT_V2_CONFIG_VERSION",
    "StrategyRecommendationOutcomeFeedbackWeightV2Config",
    "StrategyRecommendationOutcomeFeedbackV2Input",
    "StrategyRecommendationOutcomeFeedbackWeightV2Row",
    "StrategyRecommendationOutcomeFeedbackWeightV2Report",
    "build_strategy_recommendation_outcome_feedback_weight_v2_report",
)


@dataclass(frozen=True)
class StrategyRecommendationOutcomeFeedbackWeightV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_OUTCOME_FEEDBACK_WEIGHT_V2_CONFIG_VERSION
    )
    prior_paper_outcome_weight: Decimal = Decimal("0.300000")
    calibration_accuracy_weight: Decimal = Decimal("0.200000")
    source_reliability_weight: Decimal = Decimal("0.200000")
    resolution_lag_weight: Decimal = Decimal("0.100000")
    liquidity_exit_weight: Decimal = Decimal("0.100000")
    specialist_team_performance_weight: Decimal = Decimal("0.100000")
    max_resolution_lag_hours: Decimal = Decimal("72.000000")
    max_liquidity_exit_slippage: Decimal = Decimal("0.250000")
    pass_weight_floor: Decimal = Decimal("0.850000")
    watch_weight_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "prior_paper_outcome_weight",
            "calibration_accuracy_weight",
            "source_reliability_weight",
            "resolution_lag_weight",
            "liquidity_exit_weight",
            "specialist_team_performance_weight",
            "pass_weight_floor",
            "watch_weight_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_resolution_lag_hours",
            _normalize_positive_decimal(
                "max_resolution_lag_hours",
                self.max_resolution_lag_hours,
            ),
        )
        object.__setattr__(
            self,
            "max_liquidity_exit_slippage",
            _normalize_positive_decimal(
                "max_liquidity_exit_slippage",
                self.max_liquidity_exit_slippage,
            ),
        )
        _validate_config(self)
        _require_hard_flags("StrategyRecommendationOutcomeFeedbackWeightV2Config", self)
        _reject_unsafe_public_payload(
            "StrategyRecommendationOutcomeFeedbackWeightV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyRecommendationOutcomeFeedbackV2Input:
    recommendation_id: str
    market_slug: str
    specialist_team_id: str
    prior_paper_outcome_score: Decimal
    calibration_error: Decimal
    source_reliability_score: Decimal
    resolution_lag_hours: Decimal
    liquidity_exit_slippage: Decimal
    specialist_team_performance_score: Decimal
    base_recommendation_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("recommendation_id", "market_slug", "specialist_team_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "prior_paper_outcome_score",
            "calibration_error",
            "source_reliability_score",
            "liquidity_exit_slippage",
            "specialist_team_performance_score",
            "base_recommendation_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_lag_hours",
            _normalize_nonnegative_decimal(
                "resolution_lag_hours",
                self.resolution_lag_hours,
            ),
        )
        _require_hard_flags("StrategyRecommendationOutcomeFeedbackV2Input", self)
        _reject_unsafe_public_payload(
            "StrategyRecommendationOutcomeFeedbackV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyRecommendationOutcomeFeedbackWeightV2Row:
    rank: Decimal
    recommendation_id: str
    market_slug: str
    specialist_team_id: str
    prior_paper_outcome_score: Decimal
    calibration_error: Decimal
    calibration_accuracy_score: Decimal
    source_reliability_score: Decimal
    resolution_lag_hours: Decimal
    resolution_lag_score: Decimal
    liquidity_exit_slippage: Decimal
    liquidity_exit_score: Decimal
    specialist_team_performance_score: Decimal
    base_recommendation_weight: Decimal
    feedback_weight_score: Decimal
    future_recommendation_weight: Decimal
    weight_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("recommendation_id", "market_slug", "specialist_team_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "prior_paper_outcome_score",
            "calibration_error",
            "calibration_accuracy_score",
            "source_reliability_score",
            "resolution_lag_score",
            "liquidity_exit_slippage",
            "liquidity_exit_score",
            "specialist_team_performance_score",
            "base_recommendation_weight",
            "feedback_weight_score",
            "future_recommendation_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_lag_hours",
            _normalize_nonnegative_decimal(
                "resolution_lag_hours",
                self.resolution_lag_hours,
            ),
        )
        _require_weight_status("weight_status", self.weight_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("StrategyRecommendationOutcomeFeedbackWeightV2Row", self)
        _reject_unsafe_public_payload(
            "StrategyRecommendationOutcomeFeedbackWeightV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyRecommendationOutcomeFeedbackWeightV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    recommendation_count: Decimal
    pass_recommendation_count: Decimal
    watch_recommendation_count: Decimal
    blocked_recommendation_count: Decimal
    average_future_recommendation_weight: Decimal
    top_future_recommendation_weight: Decimal
    bottom_future_recommendation_weight: Decimal
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "recommendation_count",
            "pass_recommendation_count",
            "watch_recommendation_count",
            "blocked_recommendation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_future_recommendation_weight",
            "top_future_recommendation_weight",
            "bottom_future_recommendation_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("StrategyRecommendationOutcomeFeedbackWeightV2Report", self)
        _reject_unsafe_public_payload(
            "StrategyRecommendationOutcomeFeedbackWeightV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyRecommendationOutcomeFeedbackWeightV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_recommendation_outcome_feedback_weight_v2_report(
    feedback_items: object,
    *,
    config: StrategyRecommendationOutcomeFeedbackWeightV2Config | None = None,
    generated_at: datetime,
) -> StrategyRecommendationOutcomeFeedbackWeightV2Report:
    if config is None:
        config = StrategyRecommendationOutcomeFeedbackWeightV2Config()
    if type(config) is not StrategyRecommendationOutcomeFeedbackWeightV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationOutcomeFeedbackWeightV2Config",
        )
    _require_hard_flags("StrategyRecommendationOutcomeFeedbackWeightV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_feedback_items(feedback_items)
    rows = tuple(
        _row_for_feedback_item(rank=index, item=item, config=config)
        for index, item in enumerate(_sorted_feedback_items(items, config), start=1)
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "recommendation_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_recommendation_count": _status_count(rows, "pass"),
        "watch_recommendation_count": _status_count(rows, "watch"),
        "blocked_recommendation_count": _status_count(rows, "blocked"),
        "average_future_recommendation_weight": _average_future_weight(rows),
        "top_future_recommendation_weight": _top_future_weight(rows),
        "bottom_future_recommendation_weight": _bottom_future_weight(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyRecommendationOutcomeFeedbackWeightV2Report(**values)


def _sorted_feedback_items(
    items: tuple[StrategyRecommendationOutcomeFeedbackV2Input, ...],
    config: StrategyRecommendationOutcomeFeedbackWeightV2Config,
) -> tuple[StrategyRecommendationOutcomeFeedbackV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_future_recommendation_weight(item, config),
                item.recommendation_id,
                item.market_slug,
                item.specialist_team_id,
            ),
        ),
    )


def _row_for_feedback_item(
    *,
    rank: int,
    item: StrategyRecommendationOutcomeFeedbackV2Input,
    config: StrategyRecommendationOutcomeFeedbackWeightV2Config,
) -> StrategyRecommendationOutcomeFeedbackWeightV2Row:
    calibration_accuracy_score = _calibration_accuracy_score(item.calibration_error)
    resolution_lag_score = _resolution_lag_score(
        item.resolution_lag_hours,
        config.max_resolution_lag_hours,
    )
    liquidity_exit_score = _liquidity_exit_score(
        item.liquidity_exit_slippage,
        config.max_liquidity_exit_slippage,
    )
    feedback_weight_score = _feedback_weight_score(item, config)
    future_recommendation_weight = _future_recommendation_weight(item, config)
    status = _weight_status(feedback_weight_score, config)
    return StrategyRecommendationOutcomeFeedbackWeightV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        recommendation_id=item.recommendation_id,
        market_slug=item.market_slug,
        specialist_team_id=item.specialist_team_id,
        prior_paper_outcome_score=item.prior_paper_outcome_score,
        calibration_error=item.calibration_error,
        calibration_accuracy_score=calibration_accuracy_score,
        source_reliability_score=item.source_reliability_score,
        resolution_lag_hours=item.resolution_lag_hours,
        resolution_lag_score=resolution_lag_score,
        liquidity_exit_slippage=item.liquidity_exit_slippage,
        liquidity_exit_score=liquidity_exit_score,
        specialist_team_performance_score=item.specialist_team_performance_score,
        base_recommendation_weight=item.base_recommendation_weight,
        feedback_weight_score=feedback_weight_score,
        future_recommendation_weight=future_recommendation_weight,
        weight_status=status,
        reason_codes=_row_reason_codes(
            item,
            calibration_accuracy_score,
            resolution_lag_score,
            liquidity_exit_score,
            status,
        ),
    )


def _feedback_weight_score(
    item: StrategyRecommendationOutcomeFeedbackV2Input,
    config: StrategyRecommendationOutcomeFeedbackWeightV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.prior_paper_outcome_score * config.prior_paper_outcome_weight
            + _calibration_accuracy_score(item.calibration_error)
            * config.calibration_accuracy_weight
            + item.source_reliability_score * config.source_reliability_weight
            + _resolution_lag_score(
                item.resolution_lag_hours,
                config.max_resolution_lag_hours,
            )
            * config.resolution_lag_weight
            + _liquidity_exit_score(
                item.liquidity_exit_slippage,
                config.max_liquidity_exit_slippage,
            )
            * config.liquidity_exit_weight
            + item.specialist_team_performance_score
            * config.specialist_team_performance_weight
        )
        return _clamp_ratio(score)


def _future_recommendation_weight(
    item: StrategyRecommendationOutcomeFeedbackV2Input,
    config: StrategyRecommendationOutcomeFeedbackWeightV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            item.base_recommendation_weight * _feedback_weight_score(item, config),
        )


def _calibration_accuracy_score(calibration_error: Decimal) -> Decimal:
    return _clamp_ratio(ONE - calibration_error)


def _resolution_lag_score(lag_hours: Decimal, max_lag_hours: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - lag_hours / max_lag_hours)


def _liquidity_exit_score(slippage: Decimal, max_slippage: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - slippage / max_slippage)


def _weight_status(
    feedback_weight_score: Decimal,
    config: StrategyRecommendationOutcomeFeedbackWeightV2Config,
) -> str:
    if feedback_weight_score >= config.pass_weight_floor:
        return "pass"
    if feedback_weight_score >= config.watch_weight_floor:
        return "watch"
    return "blocked"


def _report_status(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.weight_status == "blocked" for row in rows):
        return "blocked"
    if any(row.weight_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: StrategyRecommendationOutcomeFeedbackV2Input,
    calibration_accuracy_score: Decimal,
    resolution_lag_score: Decimal,
    liquidity_exit_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    return (
        f"future_weight_{status}",
        _tier_reason(
            item.prior_paper_outcome_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="prior_outcome_strong",
            watch_reason="prior_outcome_watch",
            weak_reason="prior_outcome_weak",
        ),
        _tier_reason(
            calibration_accuracy_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="calibration_accuracy_strong",
            watch_reason="calibration_accuracy_watch",
            weak_reason="calibration_accuracy_weak",
        ),
        _tier_reason(
            item.source_reliability_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="source_reliability_strong",
            watch_reason="source_reliability_watch",
            weak_reason="source_reliability_weak",
        ),
        _tier_reason(
            resolution_lag_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="resolution_lag_fast",
            watch_reason="resolution_lag_watch",
            weak_reason="resolution_lag_slow",
        ),
        _tier_reason(
            liquidity_exit_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="liquidity_exit_slippage_low",
            watch_reason="liquidity_exit_slippage_watch",
            weak_reason="liquidity_exit_slippage_high",
        ),
        _tier_reason(
            item.specialist_team_performance_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="specialist_team_performance_strong",
            watch_reason="specialist_team_performance_watch",
            weak_reason="specialist_team_performance_weak",
        ),
    )


def _report_reason_codes(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("future_weight_report_empty",)
    reasons: list[str] = []
    if any(row.weight_status == "blocked" for row in rows):
        reasons.append("future_weight_report_blocked_rows")
    if any(row.weight_status == "watch" for row in rows):
        reasons.append("future_weight_report_watch_rows")
    if not reasons and status == "pass":
        reasons.append("future_weight_report_passed")
    return tuple(reasons)


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _status_count(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.weight_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_future_weight(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.future_recommendation_weight for row in rows) / Decimal(len(rows)),
        )


def _top_future_weight(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.future_recommendation_weight for row in rows)


def _bottom_future_weight(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.future_recommendation_weight for row in rows)


def _normalize_feedback_items(
    value: object,
) -> tuple[StrategyRecommendationOutcomeFeedbackV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("feedback_items must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not StrategyRecommendationOutcomeFeedbackV2Input:
            raise ValueError(
                "feedback items must be StrategyRecommendationOutcomeFeedbackV2Input",
            )
        _require_hard_flags("StrategyRecommendationOutcomeFeedbackV2Input", item)
    keys = tuple(item.recommendation_id for item in items)
    if len(set(keys)) != len(keys):
        raise ValueError("feedback items must not contain duplicate recommendation ids")
    return items


def _normalize_rows(
    value: object,
) -> tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategyRecommendationOutcomeFeedbackWeightV2Row:
            raise ValueError(
                "rows must contain StrategyRecommendationOutcomeFeedbackWeightV2Row",
            )
    return value


def _validate_config(config: StrategyRecommendationOutcomeFeedbackWeightV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.prior_paper_outcome_weight
            + config.calibration_accuracy_weight
            + config.source_reliability_weight
            + config.resolution_lag_weight
            + config.liquidity_exit_weight
            + config.specialist_team_performance_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("feedback weights must sum to 1.000000")
    if config.watch_weight_floor > config.pass_weight_floor:
        raise ValueError("watch_weight_floor must not exceed pass_weight_floor")


def _validate_row_consistency(
    row: StrategyRecommendationOutcomeFeedbackWeightV2Row,
) -> None:
    if row.calibration_accuracy_score != _calibration_accuracy_score(row.calibration_error):
        raise ValueError("calibration_accuracy_score must match calibration_error")
    with localcontext(DECIMAL_CONTEXT):
        expected_future_weight = _clamp_ratio(
            row.base_recommendation_weight * row.feedback_weight_score,
        )
    if row.future_recommendation_weight != expected_future_weight:
        raise ValueError("future_recommendation_weight must match feedback_weight_score")


def _validate_report_consistency(
    report: StrategyRecommendationOutcomeFeedbackWeightV2Report,
) -> None:
    rows = report.rows
    if report.recommendation_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("recommendation_count must match rows")
    if (
        report.pass_recommendation_count != _status_count(rows, "pass")
        or report.watch_recommendation_count != _status_count(rows, "watch")
        or report.blocked_recommendation_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_recommendation_count
        + report.watch_recommendation_count
        + report.blocked_recommendation_count
        != report.recommendation_count
    ):
        raise ValueError("status counts must sum to recommendation_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match report_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_future_recommendation_weight != _average_future_weight(rows):
        raise ValueError("average_future_recommendation_weight must match rows")
    if report.top_future_recommendation_weight != _top_future_weight(rows):
        raise ValueError("top_future_recommendation_weight must match rows")
    if report.bottom_future_recommendation_weight != _bottom_future_weight(rows):
        raise ValueError("bottom_future_recommendation_weight must match rows")


def _validate_rows_sorted(
    rows: tuple[StrategyRecommendationOutcomeFeedbackWeightV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.future_recommendation_weight,
                row.recommendation_id,
                row.market_slug,
                row.specialist_team_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by future weight and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_weight_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in WEIGHT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return _quantize_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field must be a string")
            _require_non_empty_string("payload field", key)
            payload[key] = _payload_value(item)
        return payload
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is bool:
        return value
    if type(value) is str:
        _require_non_empty_string("payload string", value)
        return value
    if value is None:
        return None
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
