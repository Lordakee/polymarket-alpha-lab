"""Read-only probability calibration drift summaries for settled paper forecasts."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_FLOOR, localcontext
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_CALIBRATION_DRIFT_MONITOR_CONFIG_VERSION = "calibration-drift-monitor-v0"

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
YES = "yes"
GROUP_BY_VALUES = frozenset(("team", "category"))
SLICE_STATUSES = frozenset(("baseline", "stable", "drift_watch", "insufficient_slice_sample"))
REPORT_STATUSES = frozenset(("empty", "stable", "drift_watch"))

__all__ = (
    "DEFAULT_CALIBRATION_DRIFT_MONITOR_CONFIG_VERSION",
    "CalibrationDriftMonitorConfig",
    "CalibrationDriftMonitorReport",
    "CalibrationDriftSlice",
    "build_calibration_drift_monitor_report",
)


@dataclass(frozen=True)
class CalibrationDriftMonitorConfig:
    config_version: str = DEFAULT_CALIBRATION_DRIFT_MONITOR_CONFIG_VERSION
    slice_days: int = 14
    min_settled_per_slice: int = 30
    ece_bucket_count: int = 10
    group_by: str = "team"
    brier_drift_warn_threshold: Decimal = Decimal("0.050000")
    ece_drift_warn_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("slice_days", self.slice_days)
        _require_positive_int("ece_bucket_count", self.ece_bucket_count)
        _require_nonnegative_int("min_settled_per_slice", self.min_settled_per_slice)
        if type(self.group_by) is not str or self.group_by not in GROUP_BY_VALUES:
            raise ValueError("group_by must be team or category")
        object.__setattr__(
            self,
            "brier_drift_warn_threshold",
            _normalize_probability(
                "brier_drift_warn_threshold",
                self.brier_drift_warn_threshold,
            ),
        )
        object.__setattr__(
            self,
            "ece_drift_warn_threshold",
            _normalize_probability(
                "ece_drift_warn_threshold",
                self.ece_drift_warn_threshold,
            ),
        )
        require_paper_only_flags("calibration drift monitor config", self)


@dataclass(frozen=True)
class CalibrationDriftSlice:
    group_type: str
    group_key: str
    team_id: str
    category_id: str | None
    slice_start_at: datetime
    slice_end_at: datetime
    settled_count: int
    average_brier_score: Decimal
    expected_calibration_error: Decimal
    previous_average_brier_score: Decimal | None
    previous_expected_calibration_error: Decimal | None
    brier_score_delta: Decimal | None
    expected_calibration_error_delta: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.group_type) is not str or self.group_type not in GROUP_BY_VALUES:
            raise ValueError("group_type must be team or category")
        _require_canonical_string("group_key", self.group_key)
        _require_canonical_string("team_id", self.team_id)
        if self.group_type == "team" and self.category_id is not None:
            raise ValueError("team slices must not include category_id")
        if self.group_type == "category":
            _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "slice_start_at",
            _as_utc("slice_start_at", self.slice_start_at),
        )
        object.__setattr__(
            self,
            "slice_end_at",
            _as_utc("slice_end_at", self.slice_end_at),
        )
        if self.slice_end_at <= self.slice_start_at:
            raise ValueError("slice_end_at must be after slice_start_at")
        _require_nonnegative_int("settled_count", self.settled_count)
        object.__setattr__(
            self,
            "average_brier_score",
            _normalize_probability("average_brier_score", self.average_brier_score),
        )
        object.__setattr__(
            self,
            "expected_calibration_error",
            _normalize_probability(
                "expected_calibration_error",
                self.expected_calibration_error,
            ),
        )
        for field_name in (
            "previous_average_brier_score",
            "previous_expected_calibration_error",
            "brier_score_delta",
            "expected_calibration_error_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        if type(self.status) is not str or self.status not in SLICE_STATUSES:
            raise ValueError("status must be a known calibration drift slice status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_slice_consistency(self)
        require_paper_only_flags("calibration drift slice", self)


@dataclass(frozen=True)
class CalibrationDriftMonitorReport:
    generated_at: datetime
    config_version: str
    group_by: str
    forecast_count: int
    settled_count: int
    duplicate_forecast_count: int
    duplicate_outcome_count: int
    orphan_outcome_count: int
    group_count: int
    slice_count: int
    drift_watch_count: int
    status: str
    reason_codes: tuple[str, ...]
    slices: tuple[CalibrationDriftSlice, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if type(self.group_by) is not str or self.group_by not in GROUP_BY_VALUES:
            raise ValueError("group_by must be team or category")
        for field_name in (
            "forecast_count",
            "settled_count",
            "duplicate_forecast_count",
            "duplicate_outcome_count",
            "orphan_outcome_count",
            "group_count",
            "slice_count",
            "drift_watch_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.settled_count > self.forecast_count:
            raise ValueError("settled_count must not exceed forecast_count")
        if type(self.status) is not str or self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known calibration drift report status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "slices", _normalize_slices(self.slices))
        _validate_report_consistency(self)
        require_paper_only_flags("calibration drift monitor report", self)


@dataclass(frozen=True)
class _ForecastItem:
    forecast_id: str
    generated_at: datetime
    payload_sha256: str
    team_id: str
    market_slug: str
    category_id: str
    forecast_probability: Decimal


@dataclass(frozen=True)
class _OutcomeItem:
    outcome_id: str
    forecast_id: str
    generated_at: datetime
    team_id: str
    market_slug: str
    resolved_at: datetime
    actual_outcome: str


def build_calibration_drift_monitor_report(
    forecast_rows: object,
    outcome_rows: object,
    *,
    config: CalibrationDriftMonitorConfig,
    generated_at: datetime,
) -> CalibrationDriftMonitorReport:
    if type(config) is not CalibrationDriftMonitorConfig:
        raise ValueError("config must be a CalibrationDriftMonitorConfig")
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("calibration drift monitor config", config)

    forecasts = _forecast_items(forecast_rows)
    outcomes = _outcome_items(outcome_rows)
    latest_forecasts, duplicate_forecast_count = _latest_forecasts(forecasts)
    latest_outcomes, duplicate_outcome_count = _latest_outcomes(outcomes)
    orphan_outcome_count = sum(
        1 for forecast_id in latest_outcomes if forecast_id not in latest_forecasts
    )
    matched = tuple(
        (forecast, latest_outcomes[forecast.forecast_id])
        for forecast in latest_forecasts.values()
        if forecast.forecast_id in latest_outcomes
    )
    for forecast, outcome in matched:
        _require_pair(forecast, outcome)

    slices = _build_slices(matched, config=config, generated_at=generated_at)
    drift_watch_count = sum(1 for row in slices if row.status == "drift_watch")
    return CalibrationDriftMonitorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        group_by=config.group_by,
        forecast_count=len(latest_forecasts),
        settled_count=len(matched),
        duplicate_forecast_count=duplicate_forecast_count,
        duplicate_outcome_count=duplicate_outcome_count,
        orphan_outcome_count=orphan_outcome_count,
        group_count=len({row.group_key for row in slices}),
        slice_count=len(slices),
        drift_watch_count=drift_watch_count,
        status=_report_status(settled_count=len(matched), drift_watch_count=drift_watch_count),
        reason_codes=_report_reason_codes(
            settled_count=len(matched),
            drift_watch_count=drift_watch_count,
            duplicate_forecast_count=duplicate_forecast_count,
            duplicate_outcome_count=duplicate_outcome_count,
            orphan_outcome_count=orphan_outcome_count,
        ),
        slices=slices,
    )


def _forecast_items(value: object) -> tuple[_ForecastItem, ...]:
    rows = _rows_tuple("forecast_rows", value)
    items: list[_ForecastItem] = []
    for row in rows:
        if type(row) is not TeamForecastDbRow:
            raise ValueError("forecast_rows must contain TeamForecastDbRow values")
        require_paper_only_flags("TeamForecastDbRow", row)
        clean = TeamForecastDbRow(
            **{field.name: getattr(row, field.name) for field in fields(TeamForecastDbRow)}
        )
        packet = team_forecast_from_db_row(clean)
        items.append(
            _ForecastItem(
                forecast_id=clean.forecast_id,
                generated_at=clean.generated_at,
                payload_sha256=clean.payload_sha256,
                team_id=clean.team_id,
                market_slug=clean.market_slug,
                category_id=packet.category_id,
                forecast_probability=clean.forecast_probability,
            ),
        )
    return tuple(items)


def _outcome_items(value: object) -> tuple[_OutcomeItem, ...]:
    rows = _rows_tuple("outcome_rows", value)
    items: list[_OutcomeItem] = []
    for row in rows:
        if type(row) is not TeamForecastOutcomeDbRow:
            raise ValueError("outcome_rows must contain TeamForecastOutcomeDbRow values")
        require_paper_only_flags("TeamForecastOutcomeDbRow", row)
        clean = TeamForecastOutcomeDbRow(
            **{
                field.name: getattr(row, field.name)
                for field in fields(TeamForecastOutcomeDbRow)
            },
        )
        outcome = team_forecast_outcome_from_db_row(clean)
        items.append(
            _OutcomeItem(
                outcome_id=clean.outcome_id,
                forecast_id=clean.forecast_id,
                generated_at=clean.generated_at,
                team_id=clean.team_id,
                market_slug=clean.market_slug,
                resolved_at=clean.resolved_at,
                actual_outcome=outcome.actual_outcome,
            ),
        )
    return tuple(items)


def _rows_tuple(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    return tuple(value)


def _latest_forecasts(
    items: tuple[_ForecastItem, ...],
) -> tuple[dict[str, _ForecastItem], int]:
    latest: dict[str, _ForecastItem] = {}
    duplicate_count = 0
    for item in items:
        current = latest.get(item.forecast_id)
        if current is None:
            latest[item.forecast_id] = item
            continue
        duplicate_count += 1
        if _forecast_rank(item) > _forecast_rank(current):
            latest[item.forecast_id] = item
    return latest, duplicate_count


def _latest_outcomes(
    items: tuple[_OutcomeItem, ...],
) -> tuple[dict[str, _OutcomeItem], int]:
    latest: dict[str, _OutcomeItem] = {}
    duplicate_count = 0
    for item in items:
        current = latest.get(item.forecast_id)
        if current is None:
            latest[item.forecast_id] = item
            continue
        duplicate_count += 1
        if _outcome_rank(item) > _outcome_rank(current):
            latest[item.forecast_id] = item
    return latest, duplicate_count


def _forecast_rank(item: _ForecastItem) -> tuple[datetime, str]:
    return item.generated_at, item.payload_sha256


def _outcome_rank(item: _OutcomeItem) -> tuple[datetime, datetime, str]:
    return item.resolved_at, item.generated_at, item.outcome_id


def _require_pair(forecast: _ForecastItem, outcome: _OutcomeItem) -> None:
    if outcome.team_id != forecast.team_id:
        raise ValueError("outcome team_id must match forecast team_id")
    if outcome.market_slug != forecast.market_slug:
        raise ValueError("outcome market_slug must match forecast market_slug")


def _build_slices(
    settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...],
    *,
    config: CalibrationDriftMonitorConfig,
    generated_at: datetime,
) -> tuple[CalibrationDriftSlice, ...]:
    groups: dict[tuple[str, str, str | None], list[tuple[_ForecastItem, _OutcomeItem]]] = {}
    for forecast, outcome in settled:
        group_type, group_key, category_id = _group_identity(forecast, config.group_by)
        groups.setdefault((group_type, group_key, category_id), []).append((forecast, outcome))

    rows: list[CalibrationDriftSlice] = []
    for (group_type, group_key, category_id), items in sorted(groups.items()):
        rows.extend(
            _group_slices(
                group_type=group_type,
                group_key=group_key,
                team_id=items[0][0].team_id,
                category_id=category_id,
                settled=tuple(items),
                config=config,
                generated_at=generated_at,
            ),
        )
    return tuple(sorted(rows, key=_slice_sort_key))


def _group_identity(
    forecast: _ForecastItem,
    group_by: str,
) -> tuple[str, str, str | None]:
    if group_by == "team":
        return "team", forecast.team_id, None
    return "category", f"{forecast.team_id}:{forecast.category_id}", forecast.category_id


def _group_slices(
    *,
    group_type: str,
    group_key: str,
    team_id: str,
    category_id: str | None,
    settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...],
    config: CalibrationDriftMonitorConfig,
    generated_at: datetime,
) -> tuple[CalibrationDriftSlice, ...]:
    grouped: dict[int, list[tuple[_ForecastItem, _OutcomeItem]]] = {}
    for item in settled:
        grouped.setdefault(
            _slice_index(item[1].resolved_at, generated_at, config.slice_days),
            [],
        ).append(item)

    previous: CalibrationDriftSlice | None = None
    rows: list[CalibrationDriftSlice] = []
    for index, items in sorted(grouped.items()):
        slice_start, slice_end = _slice_bounds(index, generated_at, config.slice_days)
        row = _slice_row(
            group_type=group_type,
            group_key=group_key,
            team_id=team_id,
            category_id=category_id,
            slice_start_at=slice_start,
            slice_end_at=slice_end,
            settled=tuple(items),
            previous=previous,
            config=config,
        )
        rows.append(row)
        if row.status != "insufficient_slice_sample":
            previous = row
    return tuple(rows)


def _slice_row(
    *,
    group_type: str,
    group_key: str,
    team_id: str,
    category_id: str | None,
    slice_start_at: datetime,
    slice_end_at: datetime,
    settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...],
    previous: CalibrationDriftSlice | None,
    config: CalibrationDriftMonitorConfig,
) -> CalibrationDriftSlice:
    average_brier_score = _average_brier_score(settled)
    expected_calibration_error = _expected_calibration_error(
        settled,
        config.ece_bucket_count,
    )
    brier_delta = (
        None
        if previous is None
        else _absolute_decimal(average_brier_score - previous.average_brier_score)
    )
    ece_delta = (
        None
        if previous is None
        else _absolute_decimal(
            expected_calibration_error - previous.expected_calibration_error,
        )
    )
    status, reason_codes = _slice_status_and_reasons(
        settled_count=len(settled),
        brier_score_delta=brier_delta,
        expected_calibration_error_delta=ece_delta,
        previous=previous,
        config=config,
    )
    return CalibrationDriftSlice(
        group_type=group_type,
        group_key=group_key,
        team_id=team_id,
        category_id=category_id,
        slice_start_at=slice_start_at,
        slice_end_at=slice_end_at,
        settled_count=len(settled),
        average_brier_score=average_brier_score,
        expected_calibration_error=expected_calibration_error,
        previous_average_brier_score=(
            None if previous is None else previous.average_brier_score
        ),
        previous_expected_calibration_error=(
            None if previous is None else previous.expected_calibration_error
        ),
        brier_score_delta=brier_delta,
        expected_calibration_error_delta=ece_delta,
        status=status,
        reason_codes=reason_codes,
    )


def _slice_status_and_reasons(
    *,
    settled_count: int,
    brier_score_delta: Decimal | None,
    expected_calibration_error_delta: Decimal | None,
    previous: CalibrationDriftSlice | None,
    config: CalibrationDriftMonitorConfig,
) -> tuple[str, tuple[str, ...]]:
    if settled_count < config.min_settled_per_slice:
        return "insufficient_slice_sample", ("insufficient_settled_slice_sample",)
    if previous is None:
        return "baseline", ("baseline_slice",)

    reason_codes: list[str] = []
    if brier_score_delta >= config.brier_drift_warn_threshold:
        reason_codes.append("brier_score_drift")
    if expected_calibration_error_delta >= config.ece_drift_warn_threshold:
        reason_codes.append("expected_calibration_error_drift")
    if reason_codes:
        return "drift_watch", tuple(reason_codes)
    return "stable", ("calibration_drift_not_detected",)


def _slice_index(resolved_at: datetime, generated_at: datetime, slice_days: int) -> int:
    resolved = _as_utc("resolved_at", resolved_at)
    if resolved >= generated_at:
        return 0
    slice_seconds = slice_days * 86_400
    age_seconds = int((generated_at - resolved).total_seconds())
    return -(age_seconds // slice_seconds)


def _slice_bounds(
    index: int,
    generated_at: datetime,
    slice_days: int,
) -> tuple[datetime, datetime]:
    width = timedelta(days=slice_days)
    end_at = generated_at + (width * index)
    return end_at - width, end_at


def _average_brier_score(
    settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...],
) -> Decimal:
    return _mean(tuple(_brier_score(forecast, outcome) for forecast, outcome in settled))


def _expected_calibration_error(
    settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...],
    bucket_count: int,
) -> Decimal:
    grouped: dict[int, list[tuple[_ForecastItem, _OutcomeItem]]] = {}
    for forecast, outcome in settled:
        grouped.setdefault(_bucket_index(forecast.forecast_probability, bucket_count), []).append(
            (forecast, outcome),
        )
    total_count = Decimal(len(settled))
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "expected_calibration_error",
            sum(
                (
                    Decimal(len(items))
                    / total_count
                    * _bucket_error(tuple(items))
                    for items in grouped.values()
                ),
                ZERO,
            ),
        )


def _bucket_error(settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...]) -> Decimal:
    return _absolute_decimal(_mean(tuple(forecast.forecast_probability for forecast, _ in settled)) - _mean(tuple(_actual_yes(outcome) for _, outcome in settled)))


def _brier_score(forecast: _ForecastItem, outcome: _OutcomeItem) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_brier_score",
            (forecast.forecast_probability - _actual_yes(outcome)) ** 2,
        )


def _actual_yes(outcome: _OutcomeItem) -> Decimal:
    if outcome.actual_outcome == YES:
        return ONE
    return ZERO


def _bucket_index(probability: Decimal, bucket_count: int) -> int:
    if probability == ONE:
        return bucket_count - 1
    with localcontext(DECIMAL_CONTEXT):
        index = (probability * Decimal(bucket_count)).to_integral_value(
            rounding=ROUND_FLOOR,
        )
    return int(index)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("mean", sum(values, ZERO) / Decimal(len(values)))


def _report_status(*, settled_count: int, drift_watch_count: int) -> str:
    if settled_count == 0:
        return "empty"
    if drift_watch_count > 0:
        return "drift_watch"
    return "stable"


def _report_reason_codes(
    *,
    settled_count: int,
    drift_watch_count: int,
    duplicate_forecast_count: int,
    duplicate_outcome_count: int,
    orphan_outcome_count: int,
) -> tuple[str, ...]:
    if settled_count == 0:
        return ("no_settled_forecasts",)
    reason_codes = [
        "calibration_drift_detected"
        if drift_watch_count > 0
        else "calibration_drift_not_detected",
    ]
    if duplicate_forecast_count > 0:
        reason_codes.append("duplicate_forecasts_deduplicated")
    if duplicate_outcome_count > 0:
        reason_codes.append("duplicate_outcomes_deduplicated")
    if orphan_outcome_count > 0:
        reason_codes.append("orphan_outcomes_ignored")
    return tuple(reason_codes)


def _validate_slice_consistency(row: CalibrationDriftSlice) -> None:
    if row.status == "baseline":
        if row.previous_average_brier_score is not None:
            raise ValueError("baseline slices must not include previous_average_brier_score")
        if row.previous_expected_calibration_error is not None:
            raise ValueError("baseline slices must not include previous_expected_calibration_error")
        if row.brier_score_delta is not None:
            raise ValueError("baseline slices must not include brier_score_delta")
        if row.expected_calibration_error_delta is not None:
            raise ValueError("baseline slices must not include expected_calibration_error_delta")
    if row.status == "stable" or row.status == "drift_watch":
        if row.previous_average_brier_score is None:
            raise ValueError("compared slices require previous_average_brier_score")
        if row.previous_expected_calibration_error is None:
            raise ValueError("compared slices require previous_expected_calibration_error")
        if row.brier_score_delta is None:
            raise ValueError("compared slices require brier_score_delta")
        if row.expected_calibration_error_delta is None:
            raise ValueError("compared slices require expected_calibration_error_delta")
    if row.status == "drift_watch" and not any(
        reason_code in row.reason_codes
        for reason_code in ("brier_score_drift", "expected_calibration_error_drift")
    ):
        raise ValueError("drift_watch slices require a drift reason code")
    if row.status == "insufficient_slice_sample" and row.reason_codes != (
        "insufficient_settled_slice_sample",
    ):
        raise ValueError("insufficient slices require insufficient sample reason")


def _validate_report_consistency(report: CalibrationDriftMonitorReport) -> None:
    if report.slice_count != len(report.slices):
        raise ValueError("slice_count must match slices")
    if report.group_count != len({row.group_key for row in report.slices}):
        raise ValueError("group_count must match slices")
    if report.drift_watch_count != sum(
        1 for row in report.slices if row.status == "drift_watch"
    ):
        raise ValueError("drift_watch_count must match slices")
    if report.slices != tuple(sorted(report.slices, key=_slice_sort_key)):
        raise ValueError("slices must be sorted")
    if report.status != _report_status(
        settled_count=report.settled_count,
        drift_watch_count=report.drift_watch_count,
    ):
        raise ValueError("status must match drift counts")


def _slice_sort_key(row: CalibrationDriftSlice) -> tuple[str, datetime]:
    return row.group_key, row.slice_start_at


def _normalize_slices(value: object) -> tuple[CalibrationDriftSlice, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("slices must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("slices must be an iterable") from exc
    for item in items:
        if type(item) is not CalibrationDriftSlice:
            raise ValueError("slices must contain CalibrationDriftSlice values")
        require_paper_only_flags("calibration drift slice", item)
    return items


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not items:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for item in items:
        _require_canonical_string("reason_codes", item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("absolute", abs(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
