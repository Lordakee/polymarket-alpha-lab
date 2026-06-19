"""Paper-only recommendation calibration gate reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


__all__ = (
    "PaperRecommendationCalibrationGateConfig",
    "PaperRecommendationCalibrationGateMetric",
    "PaperRecommendationCalibrationGateSourceRow",
    "PaperRecommendationCalibrationGateRow",
    "PaperRecommendationCalibrationGateReport",
    "build_paper_recommendation_calibration_gate_report",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no")
CALIBRATION_STATUSES = ("pass", "watch", "fail")
GATE_STATUSES = ("pass", "watch", "blocked")
MISSING_METRIC_GATE_STATUSES = ("watch", "blocked")
PASS_REASON_CODE = "calibration_gate_passed"
EMPTY_REASON_CODE = "calibration_gate_empty"
REASON_PRIORITY = (
    "calibration_status_fail",
    "brier_score_exceeds_threshold",
    "missing_calibration_metrics",
    "insufficient_calibration_sample",
    "calibration_status_watch",
    PASS_REASON_CODE,
    EMPTY_REASON_CODE,
)
ROW_SORT_STATUS_PRIORITY = {"pass": 0, "watch": 1, "blocked": 2}


@dataclass(frozen=True)
class PaperRecommendationCalibrationGateConfig:
    config_version: str
    min_sample_count: int
    max_brier_score: Decimal
    fail_penalty_per_share: Decimal
    watch_penalty_per_share: Decimal
    missing_metrics_gate_status: str = "blocked"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_sample_count", self.min_sample_count)
        object.__setattr__(
            self,
            "max_brier_score",
            _normalize_probability("max_brier_score", self.max_brier_score),
        )
        for field_name in (
            "fail_penalty_per_share",
            "watch_penalty_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            type(self.missing_metrics_gate_status) is not str
            or self.missing_metrics_gate_status not in MISSING_METRIC_GATE_STATUSES
        ):
            raise ValueError("missing_metrics_gate_status must be watch or blocked")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationCalibrationGateMetric:
    forecaster_id: str
    sample_count: int
    brier_score: Decimal
    log_loss: Decimal | None
    calibration_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("forecaster_id", self.forecaster_id)
        _require_nonnegative_int("sample_count", self.sample_count)
        object.__setattr__(
            self,
            "brier_score",
            _normalize_probability("brier_score", self.brier_score),
        )
        if self.log_loss is not None:
            object.__setattr__(
                self,
                "log_loss",
                _normalize_nonnegative_decimal("log_loss", self.log_loss),
            )
        if (
            type(self.calibration_status) is not str
            or self.calibration_status not in CALIBRATION_STATUSES
        ):
            raise ValueError("calibration_status must be pass, watch, or fail")
        _require_safety_flags("metric", self)


@dataclass(frozen=True)
class PaperRecommendationCalibrationGateSourceRow:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    forecaster_id: str
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
        _require_canonical_string("forecaster_id", self.forecaster_id)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("source row", self)


@dataclass(frozen=True)
class PaperRecommendationCalibrationGateRow:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    forecaster_id: str
    calibration_gate_status: str
    calibration_cost_per_share: Decimal
    adjusted_net_probability_edge: Decimal
    reason_codes: tuple[str, ...]
    sample_count: int | None = None
    brier_score: Decimal | None = None
    log_loss: Decimal | None = None
    metric_calibration_status: str | None = None
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
        _require_canonical_string("forecaster_id", self.forecaster_id)
        _require_gate_status("calibration_gate_status", self.calibration_gate_status)
        object.__setattr__(
            self,
            "calibration_cost_per_share",
            _normalize_nonnegative_decimal(
                "calibration_cost_per_share",
                self.calibration_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "adjusted_net_probability_edge",
            _normalize_decimal(
                "adjusted_net_probability_edge",
                self.adjusted_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.sample_count is not None:
            _require_nonnegative_int("sample_count", self.sample_count)
        if self.brier_score is not None:
            object.__setattr__(
                self,
                "brier_score",
                _normalize_probability("brier_score", self.brier_score),
            )
        if self.log_loss is not None:
            object.__setattr__(
                self,
                "log_loss",
                _normalize_nonnegative_decimal("log_loss", self.log_loss),
            )
        if self.metric_calibration_status is not None and (
            type(self.metric_calibration_status) is not str
            or self.metric_calibration_status not in CALIBRATION_STATUSES
        ):
            raise ValueError(
                "metric_calibration_status must be pass, watch, fail, or None",
            )
        _validate_row_consistency(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class PaperRecommendationCalibrationGateReport:
    generated_at: datetime
    config_version: str
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    reason_codes: tuple[str, ...]
    rows: tuple[PaperRecommendationCalibrationGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags("report", self)


def build_paper_recommendation_calibration_gate_report(
    rows: Iterable[object],
    metrics: Iterable[object],
    *,
    config: PaperRecommendationCalibrationGateConfig,
    generated_at: datetime,
) -> PaperRecommendationCalibrationGateReport:
    if type(config) is not PaperRecommendationCalibrationGateConfig:
        raise ValueError("config must be a PaperRecommendationCalibrationGateConfig")
    generated_at = _as_utc(generated_at)
    _require_safety_flags("config", config)

    source_rows = _normalize_source_rows(rows)
    metric_map = _metric_map(metrics)
    gate_rows = tuple(
        sorted(
            (
                _gate_row_from_source_row(
                    source_row,
                    metric=metric_map.get(source_row.forecaster_id),
                    config=config,
                )
                for source_row in source_rows
            ),
            key=_row_sort_key,
        ),
    )

    return PaperRecommendationCalibrationGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        row_count=len(gate_rows),
        pass_count=_gate_status_count(gate_rows, "pass"),
        watch_count=_gate_status_count(gate_rows, "watch"),
        blocked_count=_gate_status_count(gate_rows, "blocked"),
        reason_codes=_report_reason_codes(gate_rows),
        rows=gate_rows,
    )


def _gate_row_from_source_row(
    row: PaperRecommendationCalibrationGateSourceRow,
    *,
    metric: PaperRecommendationCalibrationGateMetric | None,
    config: PaperRecommendationCalibrationGateConfig,
) -> PaperRecommendationCalibrationGateRow:
    status, reason_code = _gate_status_and_reason(row.forecaster_id, metric, config)
    calibration_cost_per_share = _calibration_cost_per_share(status, config)
    adjusted_net_probability_edge = _subtract_decimal(
        row.net_probability_edge,
        calibration_cost_per_share,
    )
    reason_codes = _normalize_reason_codes(
        (*row.reason_codes, reason_code),
        require_nonempty=True,
    )

    return PaperRecommendationCalibrationGateRow(
        market_slug=row.market_slug,
        side=row.side,
        action=row.action,
        recommendation_score=row.recommendation_score,
        net_probability_edge=row.net_probability_edge,
        forecaster_id=row.forecaster_id,
        calibration_gate_status=status,
        calibration_cost_per_share=calibration_cost_per_share,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        reason_codes=reason_codes,
        sample_count=None if metric is None else metric.sample_count,
        brier_score=None if metric is None else metric.brier_score,
        log_loss=None if metric is None else metric.log_loss,
        metric_calibration_status=None if metric is None else metric.calibration_status,
    )


def _gate_status_and_reason(
    forecaster_id: str,
    metric: PaperRecommendationCalibrationGateMetric | None,
    config: PaperRecommendationCalibrationGateConfig,
) -> tuple[str, str]:
    _require_canonical_string("forecaster_id", forecaster_id)
    if metric is None:
        return config.missing_metrics_gate_status, "missing_calibration_metrics"
    if metric.calibration_status == "fail":
        return "blocked", "calibration_status_fail"
    if metric.brier_score > config.max_brier_score:
        return "blocked", "brier_score_exceeds_threshold"
    if metric.sample_count < config.min_sample_count:
        return "watch", "insufficient_calibration_sample"
    if metric.calibration_status == "watch":
        return "watch", "calibration_status_watch"
    return "pass", PASS_REASON_CODE


def _calibration_cost_per_share(
    status: str,
    config: PaperRecommendationCalibrationGateConfig,
) -> Decimal:
    if status == "blocked":
        return config.fail_penalty_per_share
    if status == "watch":
        return config.watch_penalty_per_share
    return ZERO.quantize(QUANTUM)


def _normalize_source_rows(
    rows: Iterable[object],
) -> tuple[PaperRecommendationCalibrationGateSourceRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    return tuple(_source_row_from_supplied_row(row) for row in items)


def _source_row_from_supplied_row(
    row: object,
) -> PaperRecommendationCalibrationGateSourceRow:
    if type(row) is PaperRecommendationCalibrationGateSourceRow:
        _require_safety_flags("source row", row)
        return row
    _require_safety_flags("source row", row)
    return PaperRecommendationCalibrationGateSourceRow(
        market_slug=_required_attr(row, "market_slug"),
        side=_required_attr(row, "side"),
        action=_required_attr(row, "action"),
        recommendation_score=_required_attr(row, "recommendation_score"),
        net_probability_edge=_required_attr(row, "net_probability_edge"),
        forecaster_id=_required_attr(row, "forecaster_id"),
        reason_codes=_required_attr(row, "reason_codes"),
    )


def _metric_map(
    metrics: Iterable[object],
) -> dict[str, PaperRecommendationCalibrationGateMetric]:
    if isinstance(metrics, (str, bytes)):
        raise ValueError("metrics must be an iterable")
    try:
        items = tuple(metrics)
    except TypeError as exc:
        raise ValueError("metrics must be an iterable") from exc
    mapped: dict[str, PaperRecommendationCalibrationGateMetric] = {}
    for item in items:
        metric = _metric_from_supplied_metric(item)
        if metric.forecaster_id in mapped:
            raise ValueError("metrics must not contain duplicate forecaster_id values")
        mapped[metric.forecaster_id] = metric
    return mapped


def _metric_from_supplied_metric(
    metric: object,
) -> PaperRecommendationCalibrationGateMetric:
    if type(metric) is PaperRecommendationCalibrationGateMetric:
        _require_safety_flags("metric", metric)
        return metric
    _require_safety_flags("metric", metric)
    return PaperRecommendationCalibrationGateMetric(
        forecaster_id=_required_attr(metric, "forecaster_id"),
        sample_count=_required_attr(metric, "sample_count"),
        brier_score=_required_attr(metric, "brier_score"),
        log_loss=_required_attr(metric, "log_loss"),
        calibration_status=_required_attr(metric, "calibration_status"),
    )


def _normalize_rows(
    rows: Iterable[PaperRecommendationCalibrationGateRow],
) -> tuple[PaperRecommendationCalibrationGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not PaperRecommendationCalibrationGateRow:
            raise ValueError(
                "rows must contain PaperRecommendationCalibrationGateRow values",
            )
        _require_safety_flags("row", row)
    return items


def _report_reason_codes(
    rows: tuple[PaperRecommendationCalibrationGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in REASON_PRIORITY:
                continue
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(sorted(reason_codes, key=_reason_priority))


def _reason_priority(reason_code: str) -> int:
    try:
        return REASON_PRIORITY.index(reason_code)
    except ValueError:
        return len(REASON_PRIORITY)


def _row_sort_key(
    row: PaperRecommendationCalibrationGateRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        ROW_SORT_STATUS_PRIORITY[row.calibration_gate_status],
        -row.recommendation_score,
        -row.adjusted_net_probability_edge,
        row.market_slug,
        row.side,
    )


def _gate_status_count(
    rows: tuple[PaperRecommendationCalibrationGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.calibration_gate_status == status)


def _validate_row_consistency(row: PaperRecommendationCalibrationGateRow) -> None:
    if row.calibration_gate_status == "pass":
        if row.calibration_cost_per_share != ZERO.quantize(QUANTUM):
            raise ValueError("calibration_cost_per_share must be zero for pass")
        if PASS_REASON_CODE not in row.reason_codes:
            raise ValueError("reason_codes must include calibration_gate_passed")
    if row.calibration_gate_status == "watch":
        if row.calibration_cost_per_share <= ZERO:
            raise ValueError("calibration_cost_per_share must be positive for watch")
    if row.calibration_gate_status == "blocked":
        if row.calibration_cost_per_share <= ZERO:
            raise ValueError("calibration_cost_per_share must be positive for blocked")
    expected_adjusted = _subtract_decimal(
        row.net_probability_edge,
        row.calibration_cost_per_share,
    )
    if row.adjusted_net_probability_edge != expected_adjusted:
        raise ValueError("adjusted_net_probability_edge must match net edge less cost")
    if row.sample_count is None:
        if row.brier_score is not None:
            raise ValueError("brier_score requires sample_count")
        if row.log_loss is not None:
            raise ValueError("log_loss requires sample_count")
        if row.metric_calibration_status is not None:
            raise ValueError("metric_calibration_status requires sample_count")
    elif row.brier_score is None or row.metric_calibration_status is None:
        raise ValueError("sample_count requires calibration metrics")


def _validate_report_consistency(
    report: PaperRecommendationCalibrationGateReport,
) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.pass_count != _gate_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _gate_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _gate_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.row_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("row_count must match status counts")
    identities = tuple((row.market_slug, row.side) for row in report.rows)
    if len(set(identities)) != len(identities):
        raise ValueError("rows must contain unique market_slug and side values")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


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


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_finite_decimal(field_name, value)
    quantized = _quantize(value)
    if value != quantized:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return quantized


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if require_nonempty and not items:
        raise ValueError("reason_codes must contain at least one value")
    normalized: list[str] = []
    for item in items:
        _require_canonical_string("reason_codes", item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _require_safety_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
