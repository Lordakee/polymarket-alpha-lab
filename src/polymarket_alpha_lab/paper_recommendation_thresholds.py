"""Paper-only threshold reducer for side-edge recommendation rows."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


__all__ = (
    "PaperRecommendationThresholdsInputRow",
    "PaperRecommendationThresholdsConfig",
    "PaperRecommendationThresholdsRow",
    "PaperRecommendationThresholdsReport",
    "build_paper_recommendation_thresholds_report",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no")
THRESHOLD_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {
    "pass": 0,
    "watch": 1,
    "blocked": 2,
}
THRESHOLD_SEQUENCE = (
    "min_net_probability_edge",
    "min_recommendation_score",
    "min_executable_paper_shares",
    "max_total_cost_per_share",
)
THRESHOLD_REASON_CODES = {
    "min_net_probability_edge": "below_min_net_probability_edge",
    "min_recommendation_score": "below_min_recommendation_score",
    "min_executable_paper_shares": "below_min_executable_paper_shares",
    "max_total_cost_per_share": "above_max_total_cost_per_share",
}


@dataclass(frozen=True)
class PaperRecommendationThresholdsInputRow:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    executable_paper_shares: Decimal
    total_cost_per_share: Decimal
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
            "recommendation_score",
            _normalize_probability("recommendation_score", self.recommendation_score),
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
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags("input row", self)


@dataclass(frozen=True)
class PaperRecommendationThresholdsConfig:
    config_version: str
    min_net_probability_edge: Decimal
    min_recommendation_score: Decimal
    min_executable_paper_shares: Decimal
    max_total_cost_per_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_net_probability_edge",
            _normalize_probability(
                "min_net_probability_edge",
                self.min_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "min_recommendation_score",
            _normalize_probability(
                "min_recommendation_score",
                self.min_recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "min_executable_paper_shares",
            _normalize_nonnegative_decimal(
                "min_executable_paper_shares",
                self.min_executable_paper_shares,
            ),
        )
        object.__setattr__(
            self,
            "max_total_cost_per_share",
            _normalize_nonnegative_decimal(
                "max_total_cost_per_share",
                self.max_total_cost_per_share,
            ),
        )
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationThresholdsRow:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    executable_paper_shares: Decimal
    total_cost_per_share: Decimal
    threshold_status: str
    failed_thresholds: tuple[str, ...]
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
            "recommendation_score",
            _normalize_probability("recommendation_score", self.recommendation_score),
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
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        _require_threshold_status("threshold_status", self.threshold_status)
        object.__setattr__(
            self,
            "failed_thresholds",
            _normalize_failed_thresholds(self.failed_thresholds),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_threshold_row(self)
        _require_safety_flags("threshold row", self)


@dataclass(frozen=True)
class PaperRecommendationThresholdsReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    rows: tuple[PaperRecommendationThresholdsRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("threshold report", self)


def build_paper_recommendation_thresholds_report(
    rows: Iterable[PaperRecommendationThresholdsInputRow],
    *,
    config: PaperRecommendationThresholdsConfig,
    generated_at: datetime,
) -> PaperRecommendationThresholdsReport:
    if type(config) is not PaperRecommendationThresholdsConfig:
        raise ValueError("config must be a PaperRecommendationThresholdsConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_safety_flags("config", config)

    input_rows = _normalize_input_rows(rows)
    threshold_rows = tuple(
        sorted(
            (_threshold_row(row, config=config) for row in input_rows),
            key=_threshold_row_sort_key,
        ),
    )
    return PaperRecommendationThresholdsReport(
        generated_at=_as_utc(generated_at),
        config_version=config.config_version,
        input_count=len(input_rows),
        row_count=len(threshold_rows),
        pass_count=_status_count(threshold_rows, "pass"),
        watch_count=_status_count(threshold_rows, "watch"),
        blocked_count=_status_count(threshold_rows, "blocked"),
        rows=threshold_rows,
    )


def _threshold_row(
    row: PaperRecommendationThresholdsInputRow,
    *,
    config: PaperRecommendationThresholdsConfig,
) -> PaperRecommendationThresholdsRow:
    failed_thresholds = _failed_thresholds(row, config=config)
    threshold_status = _threshold_status(row.action, failed_thresholds)
    return PaperRecommendationThresholdsRow(
        market_slug=row.market_slug,
        side=row.side,
        action=row.action,
        recommendation_score=row.recommendation_score,
        net_probability_edge=row.net_probability_edge,
        executable_paper_shares=row.executable_paper_shares,
        total_cost_per_share=row.total_cost_per_share,
        threshold_status=threshold_status,
        failed_thresholds=failed_thresholds,
        reason_codes=_reason_codes(
            row.reason_codes,
            action=row.action,
            failed_thresholds=failed_thresholds,
        ),
    )


def _failed_thresholds(
    row: PaperRecommendationThresholdsInputRow,
    *,
    config: PaperRecommendationThresholdsConfig,
) -> tuple[str, ...]:
    failed = []
    if row.net_probability_edge < config.min_net_probability_edge:
        failed.append("min_net_probability_edge")
    if row.recommendation_score < config.min_recommendation_score:
        failed.append("min_recommendation_score")
    if row.executable_paper_shares < config.min_executable_paper_shares:
        failed.append("min_executable_paper_shares")
    if row.total_cost_per_share > config.max_total_cost_per_share:
        failed.append("max_total_cost_per_share")
    return tuple(failed)


def _threshold_status(action: str, failed_thresholds: tuple[str, ...]) -> str:
    if action == "reject":
        return "blocked"
    if action == "watch":
        return "watch"
    if failed_thresholds:
        return "watch"
    return "pass"


def _reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    action: str,
    failed_thresholds: tuple[str, ...],
) -> tuple[str, ...]:
    action_codes = ()
    if action == "reject":
        action_codes = ("action_reject",)
    elif action == "watch":
        action_codes = ("action_watch",)
    threshold_codes = tuple(
        THRESHOLD_REASON_CODES[threshold] for threshold in failed_thresholds
    )
    return _normalize_reason_codes((*source_reason_codes, *action_codes, *threshold_codes))


def _threshold_row_sort_key(
    row: PaperRecommendationThresholdsRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.threshold_status],
        -row.recommendation_score,
        -row.net_probability_edge,
        -row.executable_paper_shares,
        row.total_cost_per_share,
        row.market_slug,
        row.side,
        row.action,
    )


def _status_count(
    rows: tuple[PaperRecommendationThresholdsRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.threshold_status == status)


def _normalize_input_rows(
    rows: Iterable[PaperRecommendationThresholdsInputRow],
) -> tuple[PaperRecommendationThresholdsInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of PaperRecommendationThresholdsInputRow")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must be an iterable of PaperRecommendationThresholdsInputRow",
        ) from exc
    for row in normalized:
        if type(row) is not PaperRecommendationThresholdsInputRow:
            raise ValueError("rows must contain PaperRecommendationThresholdsInputRow values")
        _require_safety_flags("input row", row)
    return normalized


def _normalize_report_rows(
    rows: Iterable[PaperRecommendationThresholdsRow],
) -> tuple[PaperRecommendationThresholdsRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of PaperRecommendationThresholdsRow")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must be an iterable of PaperRecommendationThresholdsRow",
        ) from exc
    for row in normalized:
        if type(row) is not PaperRecommendationThresholdsRow:
            raise ValueError("rows must contain PaperRecommendationThresholdsRow values")
        _require_safety_flags("threshold row", row)
    return normalized


def _validate_threshold_row(row: PaperRecommendationThresholdsRow) -> None:
    if row.threshold_status == "pass" and row.failed_thresholds:
        raise ValueError("failed_thresholds must be empty for pass rows")
    expected_status = _threshold_status(row.action, row.failed_thresholds)
    if row.threshold_status != expected_status:
        raise ValueError("threshold_status must match action and failed_thresholds")


def _validate_report(report: PaperRecommendationThresholdsReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must equal rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must equal rows")
    if report.row_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("row_count must equal status counts")
    if report.rows != tuple(sorted(report.rows, key=_threshold_row_sort_key)):
        raise ValueError("rows must be sorted")


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
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
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _normalize_failed_thresholds(failed_thresholds: Iterable[str]) -> tuple[str, ...]:
    if isinstance(failed_thresholds, (str, bytes)):
        raise ValueError("failed_thresholds must be an iterable of strings")
    try:
        normalized = tuple(failed_thresholds)
    except TypeError as exc:
        raise ValueError("failed_thresholds must be an iterable of strings") from exc
    for failed_threshold in normalized:
        _require_canonical_string("failed_thresholds", failed_threshold)
        if failed_threshold not in THRESHOLD_SEQUENCE:
            raise ValueError("failed_thresholds must contain known threshold names")
    threshold_set = set(normalized)
    return tuple(
        threshold for threshold in THRESHOLD_SEQUENCE if threshold in threshold_set
    )


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_side(field_name: str, value: str) -> None:
    if value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_action(field_name: str, value: str) -> None:
    if value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_threshold_status(field_name: str, value: str) -> None:
    if value not in THRESHOLD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
