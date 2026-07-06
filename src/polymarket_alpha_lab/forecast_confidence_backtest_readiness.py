"""Report-only readiness checks for confidence calibration backtests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
)
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_FORECAST_CONFIDENCE_BACKTEST_READINESS_CONFIG_VERSION = (
    "forecast-confidence-backtest-readiness-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
GROUP_BY_VALUES = frozenset(("team", "category"))
ROW_STATUSES = frozenset(("ready", "watch", "blocked"))
REPORT_STATUSES = ROW_STATUSES
STATUS_RANK = {"ready": 0, "watch": 1, "blocked": 2}
YES = "yes"
UNSAFE_SURFACE_FRAGMENTS = frozenset(
    (
        "live",
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "network",
        "database",
        "persist",
        "persistence",
    ),
)


@dataclass(frozen=True)
class ForecastConfidenceBacktestReadinessConfig:
    config_version: str = DEFAULT_FORECAST_CONFIDENCE_BACKTEST_READINESS_CONFIG_VERSION
    group_by: str = "team"
    min_resolved_observations: int = 30
    min_confidence_bucket_count: int = 3
    min_average_confidence: Decimal = Decimal("0.600000")
    min_resolution_coverage_ratio: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if type(self.group_by) is not str or self.group_by not in GROUP_BY_VALUES:
            raise ValueError("group_by must be team or category")
        _require_positive_int("min_resolved_observations", self.min_resolved_observations)
        _require_positive_int(
            "min_confidence_bucket_count",
            self.min_confidence_bucket_count,
        )
        object.__setattr__(
            self,
            "min_average_confidence",
            _normalize_probability("min_average_confidence", self.min_average_confidence),
        )
        object.__setattr__(
            self,
            "min_resolution_coverage_ratio",
            _normalize_probability(
                "min_resolution_coverage_ratio",
                self.min_resolution_coverage_ratio,
            ),
        )
        require_paper_only_flags("forecast confidence backtest readiness config", self)


@dataclass(frozen=True)
class ForecastConfidenceBacktestReadinessRow:
    group_type: str
    group_key: str
    team_id: str
    category_id: str | None
    forecast_count: Decimal
    resolved_observation_count: Decimal
    unresolved_forecast_count: Decimal
    disputed_outcome_count: Decimal
    resolution_coverage_ratio: Decimal
    average_confidence: Decimal
    min_confidence: Decimal
    max_confidence: Decimal
    confidence_bucket_count: Decimal
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
            raise ValueError("team rows must not include category_id")
        if self.group_type == "category":
            _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "forecast_count",
            "resolved_observation_count",
            "unresolved_forecast_count",
            "disputed_outcome_count",
            "confidence_bucket_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_coverage_ratio",
            "average_confidence",
            "min_confidence",
            "max_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if type(self.status) is not str or self.status not in ROW_STATUSES:
            raise ValueError("status must be ready, watch, or blocked")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        require_paper_only_flags("forecast confidence backtest readiness row", self)


@dataclass(frozen=True)
class ForecastConfidenceBacktestReadinessReport:
    generated_at: datetime
    config_version: str
    group_by: str
    forecast_count: Decimal
    resolved_observation_count: Decimal
    unresolved_forecast_count: Decimal
    duplicate_forecast_count: Decimal
    duplicate_outcome_count: Decimal
    orphan_outcome_count: Decimal
    disputed_outcome_count: Decimal
    group_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ForecastConfidenceBacktestReadinessRow, ...]
    derived_validation_digest: str = ""
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
            "resolved_observation_count",
            "unresolved_forecast_count",
            "duplicate_forecast_count",
            "duplicate_outcome_count",
            "orphan_outcome_count",
            "disputed_outcome_count",
            "group_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if type(self.status) is not str or self.status not in REPORT_STATUSES:
            raise ValueError("status must be ready, watch, or blocked")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        require_paper_only_flags("forecast confidence backtest readiness report", self)
        reject_unsafe_surface_fields("forecast confidence backtest readiness report", self)
        _reject_unsafe_surface_values("forecast confidence backtest readiness report", self)
        _set_or_validate_derived_validation_digest(self)


@dataclass(frozen=True)
class _ForecastItem:
    forecast_id: str
    generated_at: datetime
    payload_sha256: str
    team_id: str
    market_slug: str
    category_id: str
    confidence: Decimal


@dataclass(frozen=True)
class _OutcomeItem:
    outcome_id: str
    forecast_id: str
    generated_at: datetime
    team_id: str
    market_slug: str
    resolved_at: datetime
    actual_outcome: str
    resolution_dispute_flag: bool


def build_forecast_confidence_backtest_readiness_report(
    forecast_rows: object,
    outcome_rows: object,
    *,
    config: ForecastConfidenceBacktestReadinessConfig,
    generated_at: datetime,
) -> ForecastConfidenceBacktestReadinessReport:
    if type(config) is not ForecastConfidenceBacktestReadinessConfig:
        raise ValueError("config must be a ForecastConfidenceBacktestReadinessConfig")
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("forecast confidence backtest readiness config", config)

    forecasts = _forecast_items(forecast_rows)
    outcomes = _outcome_items(outcome_rows)
    latest_forecasts, duplicate_forecast_count = _latest_forecasts(forecasts)
    latest_outcomes, duplicate_outcome_count = _latest_outcomes(outcomes)
    orphan_outcome_count = sum(
        1 for forecast_id in latest_outcomes if forecast_id not in latest_forecasts
    )
    matched_outcomes = {
        forecast_id: outcome
        for forecast_id, outcome in latest_outcomes.items()
        if forecast_id in latest_forecasts
    }
    for forecast_id, outcome in matched_outcomes.items():
        _require_pair(latest_forecasts[forecast_id], outcome)

    rows = _build_rows(
        tuple(latest_forecasts.values()),
        matched_outcomes,
        config=config,
    )
    resolved_observation_count = Decimal(len(matched_outcomes))
    forecast_count = Decimal(len(latest_forecasts))
    disputed_outcome_count = Decimal(
        sum(1 for outcome in matched_outcomes.values() if outcome.resolution_dispute_flag),
    )
    return ForecastConfidenceBacktestReadinessReport(
        generated_at=generated_at,
        config_version=config.config_version,
        group_by=config.group_by,
        forecast_count=forecast_count,
        resolved_observation_count=resolved_observation_count,
        unresolved_forecast_count=forecast_count - resolved_observation_count,
        duplicate_forecast_count=Decimal(duplicate_forecast_count),
        duplicate_outcome_count=Decimal(duplicate_outcome_count),
        orphan_outcome_count=Decimal(orphan_outcome_count),
        disputed_outcome_count=disputed_outcome_count,
        group_count=Decimal(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows, forecast_count, resolved_observation_count),
        reason_codes=_report_reason_codes(
            rows=rows,
            forecast_count=forecast_count,
            resolved_observation_count=resolved_observation_count,
            duplicate_forecast_count=duplicate_forecast_count,
            duplicate_outcome_count=duplicate_outcome_count,
            orphan_outcome_count=orphan_outcome_count,
        ),
        rows=rows,
    )


def forecast_confidence_backtest_readiness_payload(
    report: ForecastConfidenceBacktestReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ForecastConfidenceBacktestReadinessReport:
        raise ValueError("report must be a ForecastConfidenceBacktestReadinessReport")
    require_paper_only_flags("forecast confidence backtest readiness report", report)
    reject_unsafe_surface_fields("forecast confidence backtest readiness report", report)
    _reject_unsafe_surface_values("forecast confidence backtest readiness report", report)
    payload = json_ready_no_floats(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _validate_payload_hard_flags(payload, "payload")
    reject_unsafe_surface_fields("forecast confidence backtest readiness payload", payload)
    _reject_unsafe_surface_values("forecast confidence backtest readiness payload", payload)
    return payload


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
                confidence=clean.confidence,
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
                resolution_dispute_flag=outcome.resolution_dispute_flag,
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


def _build_rows(
    forecasts: tuple[_ForecastItem, ...],
    outcomes: dict[str, _OutcomeItem],
    *,
    config: ForecastConfidenceBacktestReadinessConfig,
) -> tuple[ForecastConfidenceBacktestReadinessRow, ...]:
    groups: dict[tuple[str, str, str | None], list[_ForecastItem]] = {}
    for forecast in forecasts:
        group_type, group_key, category_id = _group_identity(forecast, config.group_by)
        groups.setdefault((group_type, group_key, category_id), []).append(forecast)

    rows = tuple(
        _row_from_group(
            group_type=group_type,
            group_key=group_key,
            category_id=category_id,
            forecasts=tuple(group_forecasts),
            outcomes=outcomes,
            config=config,
        )
        for (group_type, group_key, category_id), group_forecasts in groups.items()
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _group_identity(
    forecast: _ForecastItem,
    group_by: str,
) -> tuple[str, str, str | None]:
    if group_by == "team":
        return "team", forecast.team_id, None
    return "category", f"{forecast.team_id}:{forecast.category_id}", forecast.category_id


def _row_from_group(
    *,
    group_type: str,
    group_key: str,
    category_id: str | None,
    forecasts: tuple[_ForecastItem, ...],
    outcomes: dict[str, _OutcomeItem],
    config: ForecastConfidenceBacktestReadinessConfig,
) -> ForecastConfidenceBacktestReadinessRow:
    resolved = tuple(
        forecast for forecast in forecasts if forecast.forecast_id in outcomes
    )
    disputed_outcome_count = sum(
        1
        for forecast in resolved
        if outcomes[forecast.forecast_id].resolution_dispute_flag
    )
    status, reason_codes = _row_status_and_reasons(
        forecasts=forecasts,
        resolved=resolved,
        disputed_outcome_count=disputed_outcome_count,
        config=config,
    )
    return ForecastConfidenceBacktestReadinessRow(
        group_type=group_type,
        group_key=group_key,
        team_id=forecasts[0].team_id,
        category_id=category_id,
        forecast_count=Decimal(len(forecasts)),
        resolved_observation_count=Decimal(len(resolved)),
        unresolved_forecast_count=Decimal(len(forecasts) - len(resolved)),
        disputed_outcome_count=Decimal(disputed_outcome_count),
        resolution_coverage_ratio=_resolution_coverage_ratio(
            forecast_count=len(forecasts),
            resolved_count=len(resolved),
        ),
        average_confidence=_average_confidence(resolved),
        min_confidence=_min_confidence(resolved),
        max_confidence=_max_confidence(resolved),
        confidence_bucket_count=Decimal(len({forecast.confidence for forecast in resolved})),
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    *,
    forecasts: tuple[_ForecastItem, ...],
    resolved: tuple[_ForecastItem, ...],
    disputed_outcome_count: int,
    config: ForecastConfidenceBacktestReadinessConfig,
) -> tuple[str, tuple[str, ...]]:
    if not forecasts:
        return "blocked", ("no_forecasts",)
    reason_codes: list[str] = []
    if not resolved:
        reason_codes.append("no_resolved_observations")
    elif len(resolved) < config.min_resolved_observations:
        reason_codes.append("insufficient_resolved_observations")
    coverage_ratio = _resolution_coverage_ratio(
        forecast_count=len(forecasts),
        resolved_count=len(resolved),
    )
    if coverage_ratio < config.min_resolution_coverage_ratio:
        reason_codes.append("low_resolution_coverage")
    average_confidence = _average_confidence(resolved)
    if average_confidence < config.min_average_confidence:
        reason_codes.append("low_average_confidence")
    bucket_count = len({forecast.confidence for forecast in resolved})
    if bucket_count <= 1 and len(resolved) >= config.min_resolved_observations:
        reason_codes.append("single_confidence_bucket")
    elif bucket_count < config.min_confidence_bucket_count:
        reason_codes.append("confidence_bucket_coverage_watch")
    if disputed_outcome_count > 0:
        reason_codes.append("disputed_outcomes_present")

    if not reason_codes:
        return "ready", ("backtest_readiness_ready",)
    if _has_blocking_reason(reason_codes):
        return "blocked", tuple(reason_codes)
    return "watch", tuple(reason_codes)


def _has_blocking_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code
        in {
            "no_forecasts",
            "no_resolved_observations",
            "single_confidence_bucket",
            "low_average_confidence",
            "disputed_outcomes_present",
        }
        for reason_code in reason_codes
    )


def _resolution_coverage_ratio(*, forecast_count: int, resolved_count: int) -> Decimal:
    if forecast_count == 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "resolution_coverage_ratio",
            Decimal(resolved_count) / Decimal(forecast_count),
        )


def _average_confidence(forecasts: tuple[_ForecastItem, ...]) -> Decimal:
    if not forecasts:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_confidence",
            sum((forecast.confidence for forecast in forecasts), ZERO)
            / Decimal(len(forecasts)),
        )


def _min_confidence(forecasts: tuple[_ForecastItem, ...]) -> Decimal:
    if not forecasts:
        return ZERO
    return _normalize_probability(
        "min_confidence",
        min(forecast.confidence for forecast in forecasts),
    )


def _max_confidence(forecasts: tuple[_ForecastItem, ...]) -> Decimal:
    if not forecasts:
        return ZERO
    return _normalize_probability(
        "max_confidence",
        max(forecast.confidence for forecast in forecasts),
    )


def _report_status(
    rows: tuple[ForecastConfidenceBacktestReadinessRow, ...],
    forecast_count: Decimal,
    resolved_observation_count: Decimal,
) -> str:
    if forecast_count == ZERO or resolved_observation_count == ZERO:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    *,
    rows: tuple[ForecastConfidenceBacktestReadinessRow, ...],
    forecast_count: Decimal,
    resolved_observation_count: Decimal,
    duplicate_forecast_count: int,
    duplicate_outcome_count: int,
    orphan_outcome_count: int,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if forecast_count == ZERO:
        reason_codes.append("no_forecasts")
    if resolved_observation_count == ZERO:
        reason_codes.append("no_resolved_observations")
    if not reason_codes:
        if any(row.status == "blocked" for row in rows):
            reason_codes.append("blocked_backtest_readiness_group")
        if any(row.status == "watch" for row in rows):
            reason_codes.append("watch_backtest_readiness_group")
        if not reason_codes:
            reason_codes.append("backtest_readiness_ready")
    if duplicate_forecast_count > 0:
        reason_codes.append("duplicate_forecasts_deduplicated")
    if duplicate_outcome_count > 0:
        reason_codes.append("duplicate_outcomes_deduplicated")
    if orphan_outcome_count > 0:
        reason_codes.append("orphan_outcomes_ignored")
    return tuple(reason_codes)


def _validate_row_consistency(row: ForecastConfidenceBacktestReadinessRow) -> None:
    if row.forecast_count != row.resolved_observation_count + row.unresolved_forecast_count:
        raise ValueError("forecast_count must match resolved and unresolved counts")
    if row.disputed_outcome_count > row.resolved_observation_count:
        raise ValueError("disputed_outcome_count must not exceed resolved observations")
    if row.resolved_observation_count == ZERO:
        for field_name in (
            "resolution_coverage_ratio",
            "average_confidence",
            "min_confidence",
            "max_confidence",
            "confidence_bucket_count",
        ):
            if getattr(row, field_name) != ZERO:
                raise ValueError(f"{field_name} must be zero without resolved observations")
    if row.status == "ready" and row.reason_codes != ("backtest_readiness_ready",):
        raise ValueError("ready rows require backtest_readiness_ready")
    if row.status != "ready" and row.reason_codes == ("backtest_readiness_ready",):
        raise ValueError("non-ready rows require non-ready reason codes")


def _validate_report_consistency(report: ForecastConfidenceBacktestReadinessReport) -> None:
    if report.group_count != Decimal(len(report.rows)):
        raise ValueError("group_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.group_count != report.ready_count + report.watch_count + report.blocked_count:
        raise ValueError("group_count must match status counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.resolved_observation_count > report.forecast_count:
        raise ValueError("resolved_observation_count must not exceed forecast_count")
    if report.unresolved_forecast_count != (
        report.forecast_count - report.resolved_observation_count
    ):
        raise ValueError("unresolved_forecast_count must match forecast and resolved counts")
    if report.disputed_outcome_count != _sum_count(
        row.disputed_outcome_count for row in report.rows
    ):
        raise ValueError("disputed_outcome_count must match rows")
    if report.status != _report_status(
        report.rows,
        report.forecast_count,
        report.resolved_observation_count,
    ):
        raise ValueError("status must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ForecastConfidenceBacktestReadinessRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ForecastConfidenceBacktestReadinessRow:
            raise ValueError(
                "rows must contain ForecastConfidenceBacktestReadinessRow values",
            )
        require_paper_only_flags("forecast confidence backtest readiness row", row)
    return rows


def _row_sort_key(
    row: ForecastConfidenceBacktestReadinessRow,
) -> tuple[int, str]:
    return STATUS_RANK[row.status], row.group_key


def _status_count(
    rows: tuple[ForecastConfidenceBacktestReadinessRow, ...],
    status: str,
) -> Decimal:
    return _normalize_nonnegative_count("status_count", Decimal(sum(1 for row in rows if row.status == status)))


def _sum_count(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_nonnegative_count("count_sum", total)


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
    return tuple(sorted(normalized))


def _validate_payload_hard_flags(value: object, field_path: str) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{field_path} {flag_name} must be True")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _validate_payload_hard_flags(item, f"{field_path} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_hard_flags(item, f"{field_path} {index}")


def _set_or_validate_derived_validation_digest(
    report: ForecastConfidenceBacktestReadinessReport,
) -> None:
    provided = report.derived_validation_digest
    if type(provided) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_validation_digest(report)
    if provided == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if provided != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _derived_validation_digest(report: ForecastConfidenceBacktestReadinessReport) -> str:
    material = asdict(report)
    material.pop("derived_validation_digest", None)
    payload = json_ready_no_floats(material)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_surface_values(label: str, value: object) -> None:
    _reject_unsafe_surface_values_at(label, value, label)


def _reject_unsafe_surface_values_at(label: str, value: object, path: str) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_surface_values_at(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {label}: {path}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_surface_values_at(label, item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_surface_values_at(label, item, f"{path}[{index}]")


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FRAGMENTS)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


__all__ = (
    "DEFAULT_FORECAST_CONFIDENCE_BACKTEST_READINESS_CONFIG_VERSION",
    "ForecastConfidenceBacktestReadinessConfig",
    "ForecastConfidenceBacktestReadinessReport",
    "ForecastConfidenceBacktestReadinessRow",
    "build_forecast_confidence_backtest_readiness_report",
    "forecast_confidence_backtest_readiness_payload",
)
