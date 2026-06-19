"""Pure paper-only risk-budget report for selected recommendation rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperRecommendationRiskBudgetConfig",
    "PaperRecommendationRiskBudgetReport",
    "build_paper_recommendation_risk_budget_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NOTIONAL_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
STATUSES = ("pass", "watch", "blocked")
BLOCKING_REASON_CODES = (
    "empty_selection",
    "total_utilization_cap_exceeded",
    "single_recommendation_share_exceeded",
    "min_remaining_notional_breached",
    "max_selected_count_exceeded",
)
WATCH_REASON_CODES = (
    "near_total_utilization_cap",
    "near_single_recommendation_share_cap",
    "near_min_remaining_notional",
    "near_max_selected_count",
)
PASS_REASON_CODE = "risk_budget_passed"
WATCH_THRESHOLD = Decimal("0.95")


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetConfig:
    config_version: str
    max_total_utilization: Decimal
    max_single_recommendation_share: Decimal
    min_remaining_notional: Decimal
    max_selected_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_ratio("max_total_utilization", self.max_total_utilization)
        if self.max_total_utilization <= ZERO:
            raise ValueError("max_total_utilization must be positive")
        _require_ratio(
            "max_single_recommendation_share",
            self.max_single_recommendation_share,
        )
        if self.max_single_recommendation_share <= ZERO:
            raise ValueError("max_single_recommendation_share must be positive")
        _require_notional("min_remaining_notional", self.min_remaining_notional)
        _require_positive_int("max_selected_count", self.max_selected_count)


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    total_suggested_notional: Decimal
    remaining_total_notional: Decimal | None
    total_notional_utilization: Decimal | None
    largest_single_recommendation_share: Decimal | None
    selected_count: int
    blocked_count: int
    max_total_utilization: Decimal
    max_single_recommendation_share: Decimal
    min_remaining_notional: Decimal
    max_selected_count: int
    selected_position_notional_values: tuple[Decimal, ...]
    nav_notional: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_notional("total_suggested_notional", self.total_suggested_notional)
        _require_optional_notional(
            "remaining_total_notional",
            self.remaining_total_notional,
        )
        _require_optional_ratio(
            "total_notional_utilization",
            self.total_notional_utilization,
        )
        _require_optional_ratio(
            "largest_single_recommendation_share",
            self.largest_single_recommendation_share,
        )
        _require_nonnegative_int("selected_count", self.selected_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_ratio("max_total_utilization", self.max_total_utilization)
        if self.max_total_utilization <= ZERO:
            raise ValueError("max_total_utilization must be positive")
        _require_ratio(
            "max_single_recommendation_share",
            self.max_single_recommendation_share,
        )
        if self.max_single_recommendation_share <= ZERO:
            raise ValueError("max_single_recommendation_share must be positive")
        _require_notional("min_remaining_notional", self.min_remaining_notional)
        _require_positive_int("max_selected_count", self.max_selected_count)
        object.__setattr__(
            self,
            "selected_position_notional_values",
            _normalize_selected_position_notional_values(
                self.selected_position_notional_values,
            ),
        )
        _require_optional_notional("nav_notional", self.nav_notional)
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")

    @property
    def utilization(self) -> Decimal | None:
        return self.total_notional_utilization


def build_paper_recommendation_risk_budget_report(
    selection_report: object,
    *,
    config: PaperRecommendationRiskBudgetConfig,
    generated_at: datetime,
    nav_risk_metrics_report: object | None = None,
) -> PaperRecommendationRiskBudgetReport:
    if type(config) is not PaperRecommendationRiskBudgetConfig:
        raise ValueError("config must be a PaperRecommendationRiskBudgetConfig")
    generated_at = _as_utc(generated_at)
    _validate_hard_flags("selection_report", selection_report)
    if nav_risk_metrics_report is not None:
        _validate_hard_flags("nav_risk_metrics_report", nav_risk_metrics_report)

    selected_values = _selected_position_notional_values(selection_report)
    total_suggested_notional = _quantize_notional(sum(selected_values, ZERO))
    nav_notional = _nav_notional(nav_risk_metrics_report)
    if nav_notional is None:
        remaining_total_notional = None
        total_notional_utilization = None
        largest_single_share = None
    else:
        remaining_total_notional = _remaining_total_notional(
            total_suggested_notional,
            nav_notional,
            config.max_total_utilization,
        )
        total_notional_utilization = _optional_ratio(total_suggested_notional, nav_notional)
        largest_single_share = _largest_single_recommendation_share(
            selected_values,
            nav_notional,
        )

    reason_codes = _risk_reason_codes(
        selected_values=selected_values,
        total_notional_utilization=total_notional_utilization,
        largest_single_share=largest_single_share,
        remaining_total_notional=remaining_total_notional,
        config=config,
    )
    blocked_count = _blocked_reason_count(reason_codes)
    status = _status_from_reason_codes(reason_codes)

    return PaperRecommendationRiskBudgetReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        reason_codes=reason_codes,
        total_suggested_notional=total_suggested_notional,
        remaining_total_notional=remaining_total_notional,
        total_notional_utilization=total_notional_utilization,
        largest_single_recommendation_share=largest_single_share,
        selected_count=len(selected_values),
        blocked_count=blocked_count,
        max_total_utilization=config.max_total_utilization,
        max_single_recommendation_share=config.max_single_recommendation_share,
        min_remaining_notional=config.min_remaining_notional,
        max_selected_count=config.max_selected_count,
        selected_position_notional_values=selected_values,
        nav_notional=nav_notional,
    )


def _selected_position_notional_values(selection_report: object) -> tuple[Decimal, ...]:
    rows = _selection_rows(selection_report)
    return tuple(
        _row_selected_position_notional(row)
        for row in rows
        if _row_decision(row) == "selected"
    )


def _selection_rows(selection_report: object) -> tuple[object, ...]:
    rows = _required_attr(selection_report, "selection_rows")
    if isinstance(rows, (str, bytes)):
        raise ValueError("selection_rows must be an iterable")
    try:
        return tuple(rows)
    except TypeError as exc:
        raise ValueError("selection_rows must be an iterable") from exc


def _row_decision(row: object) -> str:
    value = _required_attr(row, "decision")
    if type(value) is not str:
        raise ValueError("selection row decision must be a string")
    return value


def _row_selected_position_notional(row: object) -> Decimal:
    value = _required_attr(row, "selected_position_notional")
    _require_notional("selected_position_notional", value)
    return value


def _nav_notional(nav_risk_metrics_report: object | None) -> Decimal | None:
    if nav_risk_metrics_report is None:
        return None
    for field_name in (
        "latest_exit_nav",
        "exit_nav",
        "nav_notional",
        "latest_nav",
    ):
        if hasattr(nav_risk_metrics_report, field_name):
            value = getattr(nav_risk_metrics_report, field_name)
            if value is None:
                return None
            _require_notional(field_name, value)
            if value <= ZERO:
                return None
            return value
    raise ValueError("nav_risk_metrics_report must expose latest_exit_nav")


def _risk_reason_codes(
    *,
    selected_values: tuple[Decimal, ...],
    total_notional_utilization: Decimal | None,
    largest_single_share: Decimal | None,
    remaining_total_notional: Decimal | None,
    config: PaperRecommendationRiskBudgetConfig,
) -> tuple[str, ...]:
    blocking_reasons: list[str] = []
    watch_reasons: list[str] = []
    selected_count = len(selected_values)

    if selected_count == 0:
        blocking_reasons.append("empty_selection")
    if (
        total_notional_utilization is not None
        and total_notional_utilization > config.max_total_utilization
    ):
        blocking_reasons.append("total_utilization_cap_exceeded")
    elif (
        total_notional_utilization is not None
        and total_notional_utilization
        >= _quantize_ratio(config.max_total_utilization * WATCH_THRESHOLD)
    ):
        watch_reasons.append("near_total_utilization_cap")

    if (
        largest_single_share is not None
        and largest_single_share > config.max_single_recommendation_share
    ):
        blocking_reasons.append("single_recommendation_share_exceeded")
    elif (
        largest_single_share is not None
        and largest_single_share
        >= _quantize_ratio(config.max_single_recommendation_share * WATCH_THRESHOLD)
    ):
        watch_reasons.append("near_single_recommendation_share_cap")

    if (
        remaining_total_notional is not None
        and remaining_total_notional < config.min_remaining_notional
    ):
        blocking_reasons.append("min_remaining_notional_breached")
    elif (
        remaining_total_notional is not None
        and remaining_total_notional
        <= _quantize_notional(config.min_remaining_notional / WATCH_THRESHOLD)
    ):
        watch_reasons.append("near_min_remaining_notional")

    if selected_count > config.max_selected_count:
        blocking_reasons.append("max_selected_count_exceeded")
    elif selected_count == config.max_selected_count:
        watch_reasons.append("near_max_selected_count")

    if blocking_reasons:
        return tuple(blocking_reasons)
    if watch_reasons:
        return tuple(watch_reasons)
    return (PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _blocked_reason_count(reason_codes: tuple[str, ...]) -> int:
    return sum(1 for reason_code in reason_codes if reason_code in BLOCKING_REASON_CODES)


def _validate_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if hasattr(value, flag_name) and getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _validate_report_consistency(report: PaperRecommendationRiskBudgetReport) -> None:
    total_suggested_notional = _quantize_notional(
        sum(report.selected_position_notional_values, ZERO),
    )
    if report.total_suggested_notional != total_suggested_notional:
        raise ValueError("total_suggested_notional must match selected rows")
    if report.selected_count != len(report.selected_position_notional_values):
        raise ValueError("selected_count must match selected rows")
    if report.blocked_count != _blocked_reason_count(report.reason_codes):
        raise ValueError("blocked_count must match reason_codes")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.nav_notional is None:
        if report.remaining_total_notional is not None:
            raise ValueError("remaining_total_notional requires nav_notional")
        if report.total_notional_utilization is not None:
            raise ValueError("total_notional_utilization requires nav_notional")
        if report.largest_single_recommendation_share is not None:
            raise ValueError(
                "largest_single_recommendation_share requires nav_notional",
            )
    else:
        expected_remaining = _remaining_total_notional(
            report.total_suggested_notional,
            report.nav_notional,
            report.max_total_utilization,
        )
        if report.remaining_total_notional != expected_remaining:
            raise ValueError("remaining_total_notional must match nav_notional")
        expected_utilization = _optional_ratio(
            report.total_suggested_notional,
            report.nav_notional,
        )
        if report.total_notional_utilization != expected_utilization:
            raise ValueError(
                "total_notional_utilization must match total_suggested_notional",
            )
        expected_largest_share = _largest_single_recommendation_share(
            report.selected_position_notional_values,
            report.nav_notional,
        )
        if report.largest_single_recommendation_share != expected_largest_share:
            raise ValueError(
                "largest_single_recommendation_share must match selected rows",
            )
    expected_reason_codes = _risk_reason_codes(
        selected_values=report.selected_position_notional_values,
        total_notional_utilization=report.total_notional_utilization,
        largest_single_share=report.largest_single_recommendation_share,
        remaining_total_notional=report.remaining_total_notional,
        config=PaperRecommendationRiskBudgetConfig(
            config_version=report.config_version,
            max_total_utilization=report.max_total_utilization,
            max_single_recommendation_share=report.max_single_recommendation_share,
            min_remaining_notional=report.min_remaining_notional,
            max_selected_count=report.max_selected_count,
        ),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match risk budget metrics")


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_notional(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_notional(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_optional_notional(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_notional(field_name, value)


def _require_ratio(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    if value != _quantize_ratio(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_optional_ratio(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_ratio(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    allowed = set(BLOCKING_REASON_CODES) | set(WATCH_REASON_CODES) | {PASS_REASON_CODE}
    for item in items:
        _require_canonical_string("reason_codes", item)
        if item not in allowed:
            raise ValueError("reason_codes must match risk budget semantics")
    return items


def _normalize_selected_position_notional_values(
    value: tuple[Decimal, ...],
) -> tuple[Decimal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("selected_position_notional_values must be an iterable")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError(
            "selected_position_notional_values must be an iterable",
        ) from exc
    for item in values:
        _require_notional("selected_position_notional_values", item)
    return values


def _largest_single_recommendation_share(
    selected_values: tuple[Decimal, ...],
    nav_notional: Decimal,
) -> Decimal | None:
    if not selected_values or nav_notional <= ZERO:
        return None
    return _quantize_ratio(max(selected_values) / nav_notional)


def _remaining_total_notional(
    total_suggested_notional: Decimal,
    nav_notional: Decimal,
    max_total_utilization: Decimal,
) -> Decimal:
    total_budget_notional = _quantize_notional(nav_notional * max_total_utilization)
    return _quantize_notional(max(total_budget_notional - total_suggested_notional, ZERO))


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize_ratio(numerator / denominator)


def _quantize_notional(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("notional", value)
    return value.quantize(NOTIONAL_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)
