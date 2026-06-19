"""Pure paper-only health reducer for supplied recommendation rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperRecommendationHealthConfig",
    "PaperRecommendationHealthInputRow",
    "PaperRecommendationHealthReasonCodeCount",
    "PaperRecommendationHealthReport",
    "build_paper_recommendation_health_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no")
HEALTH_STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class PaperRecommendationHealthConfig:
    config_version: str
    max_average_cost_per_share: Decimal
    min_recommend_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_average_cost_per_share",
            _normalize_nonnegative_decimal(
                "max_average_cost_per_share",
                self.max_average_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "min_recommend_share",
            _normalize_probability("min_recommend_share", self.min_recommend_share),
        )
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationHealthInputRow:
    market_slug: str
    side: str
    action: str
    net_probability_edge: Decimal
    total_cost_per_share: Decimal
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_action("action", self.action)
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
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
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags("input row", self)


@dataclass(frozen=True)
class PaperRecommendationHealthReasonCodeCount:
    reason_code: str
    count: int

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)


@dataclass(frozen=True)
class PaperRecommendationHealthReport:
    generated_at: datetime
    config_version: str
    row_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    average_net_probability_edge: Decimal
    average_total_cost_per_share: Decimal
    top_recommendation_score: Decimal
    reason_code_counts: tuple[PaperRecommendationHealthReasonCodeCount, ...]
    health_status: str
    max_average_cost_per_share: Decimal
    min_recommend_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "recommend_count",
            "watch_count",
            "reject_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "average_net_probability_edge",
            _normalize_decimal(
                "average_net_probability_edge",
                self.average_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "average_total_cost_per_share",
            _normalize_nonnegative_decimal(
                "average_total_cost_per_share",
                self.average_total_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "top_recommendation_score",
            _normalize_nonnegative_decimal(
                "top_recommendation_score",
                self.top_recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_health_status("health_status", self.health_status)
        object.__setattr__(
            self,
            "max_average_cost_per_share",
            _normalize_nonnegative_decimal(
                "max_average_cost_per_share",
                self.max_average_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "min_recommend_share",
            _normalize_probability("min_recommend_share", self.min_recommend_share),
        )
        _validate_report_consistency(self)
        _require_safety_flags("health report", self)


def build_paper_recommendation_health_report(
    rows: Iterable[object],
    *,
    config: PaperRecommendationHealthConfig,
    generated_at: datetime,
) -> PaperRecommendationHealthReport:
    if type(config) is not PaperRecommendationHealthConfig:
        raise ValueError("config must be a PaperRecommendationHealthConfig")
    generated_at = _as_utc(generated_at)
    _require_safety_flags("config", config)
    input_rows = _normalize_input_rows(rows)

    recommend_count = _action_count(input_rows, "recommend")
    watch_count = _action_count(input_rows, "watch")
    reject_count = _action_count(input_rows, "reject")
    average_net_probability_edge = _average_decimal(
        row.net_probability_edge for row in input_rows
    )
    average_total_cost_per_share = _average_decimal(
        row.total_cost_per_share for row in input_rows
    )
    top_recommendation_score = (
        max(row.recommendation_score for row in input_rows)
        if input_rows
        else _quantize(ZERO)
    )

    return PaperRecommendationHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        row_count=len(input_rows),
        recommend_count=recommend_count,
        watch_count=watch_count,
        reject_count=reject_count,
        average_net_probability_edge=average_net_probability_edge,
        average_total_cost_per_share=average_total_cost_per_share,
        top_recommendation_score=top_recommendation_score,
        reason_code_counts=_reason_code_counts(input_rows),
        health_status=_health_status(
            row_count=len(input_rows),
            recommend_count=recommend_count,
            average_total_cost_per_share=average_total_cost_per_share,
            config=config,
        ),
        max_average_cost_per_share=config.max_average_cost_per_share,
        min_recommend_share=config.min_recommend_share,
    )


def _normalize_input_rows(
    rows: Iterable[object],
) -> tuple[PaperRecommendationHealthInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    return tuple(_coerce_input_row(row) for row in items)


def _coerce_input_row(row: object) -> PaperRecommendationHealthInputRow:
    if type(row) is PaperRecommendationHealthInputRow:
        _require_safety_flags("input row", row)
        return row
    return PaperRecommendationHealthInputRow(
        market_slug=_required_attr(row, "market_slug"),
        side=_required_attr(row, "side"),
        action=_row_action(row),
        net_probability_edge=_required_attr(row, "net_probability_edge"),
        total_cost_per_share=_required_attr(row, "total_cost_per_share"),
        recommendation_score=_required_attr(row, "recommendation_score"),
        reason_codes=_required_attr(row, "reason_codes"),
        paper_only=_required_attr(row, "paper_only"),
        report_only=_required_attr(row, "report_only"),
        readonly=_required_attr(row, "readonly"),
    )


def _row_action(row: object) -> object:
    if hasattr(row, "action"):
        return getattr(row, "action")
    return _required_attr(row, "status")


def _reason_code_counts(
    rows: tuple[PaperRecommendationHealthInputRow, ...],
) -> tuple[PaperRecommendationHealthReasonCodeCount, ...]:
    reason_counts: Counter[str] = Counter()
    for row in rows:
        reason_counts.update(row.reason_codes)
    return tuple(
        PaperRecommendationHealthReasonCodeCount(reason_code=reason_code, count=count)
        for reason_code, count in sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _action_count(
    rows: tuple[PaperRecommendationHealthInputRow, ...],
    action: str,
) -> int:
    return sum(1 for row in rows if row.action == action)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _quantize(ZERO)
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _health_status(
    *,
    row_count: int,
    recommend_count: int,
    average_total_cost_per_share: Decimal,
    config: PaperRecommendationHealthConfig,
) -> str:
    if row_count == 0 or recommend_count == 0:
        return "blocked"
    if average_total_cost_per_share > config.max_average_cost_per_share:
        return "watch"
    if _quantize(Decimal(recommend_count) / Decimal(row_count)) < config.min_recommend_share:
        return "watch"
    return "pass"


def _validate_report_consistency(report: PaperRecommendationHealthReport) -> None:
    if report.row_count != (
        report.recommend_count + report.watch_count + report.reject_count
    ):
        raise ValueError(
            "row_count must match recommend_count, watch_count, and reject_count",
        )
    if report.row_count == 0:
        if report.average_net_probability_edge != _quantize(ZERO):
            raise ValueError("average_net_probability_edge must be zero with no rows")
        if report.average_total_cost_per_share != _quantize(ZERO):
            raise ValueError("average_total_cost_per_share must be zero with no rows")
        if report.top_recommendation_score != _quantize(ZERO):
            raise ValueError("top_recommendation_score must be zero with no rows")
        if report.reason_code_counts:
            raise ValueError("reason_code_counts must be empty with no rows")
    elif not report.reason_code_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.health_status != _expected_health_status(report):
        raise ValueError("health_status must match health thresholds")


def _expected_health_status(report: PaperRecommendationHealthReport) -> str:
    if report.row_count == 0 or report.recommend_count == 0:
        return "blocked"
    if report.average_total_cost_per_share > report.max_average_cost_per_share:
        return "watch"
    if (
        _quantize(Decimal(report.recommend_count) / Decimal(report.row_count))
        < report.min_recommend_share
    ):
        return "watch"
    return "pass"


def _normalize_reason_code_counts(
    reason_code_counts: Iterable[PaperRecommendationHealthReasonCodeCount],
) -> tuple[PaperRecommendationHealthReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not PaperRecommendationHealthReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
    sorted_items = tuple(
        sorted(
            items,
            key=lambda item: (-item.count, item.reason_code),
        ),
    )
    if items != sorted_items:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return items


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_safety_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_finite_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
