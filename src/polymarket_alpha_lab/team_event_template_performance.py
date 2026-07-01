"""Pure event-template performance diagnostics for team forecasts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")
STATUSES = frozenset(("validated", "candidate", "watch"))


@dataclass(frozen=True)
class TeamEventTemplatePerformanceConfig:
    config_version: str = "team-event-template-performance-v0"
    min_settled_forecasts: int = 3
    max_dispute_rate: Decimal = Decimal("0.250000")
    min_profitable_after_cost_rate: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_settled_forecasts", self.min_settled_forecasts)
        object.__setattr__(
            self,
            "max_dispute_rate",
            _normalize_probability("max_dispute_rate", self.max_dispute_rate),
        )
        object.__setattr__(
            self,
            "min_profitable_after_cost_rate",
            _normalize_probability(
                "min_profitable_after_cost_rate",
                self.min_profitable_after_cost_rate,
            ),
        )
        _require_true_flags("config", self)


@dataclass(frozen=True)
class TeamEventTemplatePerformanceRow:
    team_id: str
    category_id: str
    event_template: str
    forecast_count: int
    settled_count: int
    directionally_correct_count: int
    profitable_after_cost_count: int
    dispute_count: int
    average_brier_score: Decimal
    hit_rate: Decimal
    dispute_rate: Decimal
    profitable_after_cost_rate: Decimal
    paper_pnl: Decimal
    average_confidence: Decimal
    average_forecast_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "category_id", "event_template"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "forecast_count",
            "settled_count",
            "directionally_correct_count",
            "profitable_after_cost_count",
            "dispute_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "average_brier_score",
            "hit_rate",
            "dispute_rate",
            "profitable_after_cost_rate",
            "average_confidence",
            "average_forecast_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "paper_pnl", _normalize_decimal("paper_pnl", self.paper_pnl))
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_true_flags("row", self)


@dataclass(frozen=True)
class TeamEventTemplatePerformanceReport:
    generated_at: datetime
    config_version: str
    forecast_count: int
    outcome_count: int
    settled_count: int
    duplicate_forecast_count: int
    duplicate_outcome_count: int
    orphan_outcome_count: int
    row_count: int
    rows: tuple[TeamEventTemplatePerformanceRow, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_count",
            "outcome_count",
            "settled_count",
            "duplicate_forecast_count",
            "duplicate_outcome_count",
            "orphan_outcome_count",
            "row_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not TeamEventTemplatePerformanceRow:
                raise ValueError("rows items must be TeamEventTemplatePerformanceRow")
        if self.row_count != len(self.rows):
            raise ValueError("row_count must match rows")
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_true_flags("report", self)


def build_team_event_template_performance_report(
    forecast_rows: object,
    outcome_rows: object,
    *,
    config: TeamEventTemplatePerformanceConfig,
    generated_at: datetime,
) -> TeamEventTemplatePerformanceReport:
    if type(config) is not TeamEventTemplatePerformanceConfig:
        raise ValueError("config must be a TeamEventTemplatePerformanceConfig")
    generated_at = _as_utc("generated_at", generated_at)
    forecasts = _validate_forecast_rows(forecast_rows)
    outcomes = _validate_outcome_rows(outcome_rows)

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

    rows = _build_rows(latest_forecasts, matched_outcomes, config)
    status, status_reasons = _status_and_reasons(
        settled_count=len(matched_outcomes),
        dispute_count=sum(1 for row in matched_outcomes.values() if row.resolution_dispute_flag),
        profitable_after_cost_count=sum(
            1 for row in matched_outcomes.values() if row.profitable_after_cost
        ),
        config=config,
    )
    reason_codes = _report_reason_codes(
        duplicate_forecast_count=duplicate_forecast_count,
        duplicate_outcome_count=duplicate_outcome_count,
        orphan_outcome_count=orphan_outcome_count,
        status_reasons=status_reasons,
    )

    return TeamEventTemplatePerformanceReport(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast_count=len(latest_forecasts),
        outcome_count=len(latest_outcomes),
        settled_count=len(matched_outcomes),
        duplicate_forecast_count=duplicate_forecast_count,
        duplicate_outcome_count=duplicate_outcome_count,
        orphan_outcome_count=orphan_outcome_count,
        row_count=len(rows),
        rows=rows,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _validate_forecast_rows(rows: object) -> tuple[TeamForecastDbRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("forecast_rows must be a list or tuple")
    checked: list[TeamForecastDbRow] = []
    for row in rows:
        if type(row) is not TeamForecastDbRow:
            raise ValueError("forecast_rows items must be TeamForecastDbRow")
        _require_true_flags("forecast row", row)
        team_forecast_from_db_row(row)
        checked.append(row)
    return tuple(checked)


def _validate_outcome_rows(rows: object) -> tuple[TeamForecastOutcomeDbRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("outcome_rows must be a list or tuple")
    checked: list[TeamForecastOutcomeDbRow] = []
    for row in rows:
        if type(row) is not TeamForecastOutcomeDbRow:
            raise ValueError("outcome_rows items must be TeamForecastOutcomeDbRow")
        _require_true_flags("outcome row", row)
        team_forecast_outcome_from_db_row(row)
        checked.append(row)
    return tuple(checked)


def _latest_forecasts(
    rows: tuple[TeamForecastDbRow, ...],
) -> tuple[dict[str, TeamForecastDbRow], int]:
    latest: dict[str, TeamForecastDbRow] = {}
    for row in rows:
        current = latest.get(row.forecast_id)
        if current is None or _forecast_latest_key(row) > _forecast_latest_key(current):
            latest[row.forecast_id] = row
    return latest, len(rows) - len(latest)


def _latest_outcomes(
    rows: tuple[TeamForecastOutcomeDbRow, ...],
) -> tuple[dict[str, TeamForecastOutcomeDbRow], int]:
    latest: dict[str, TeamForecastOutcomeDbRow] = {}
    for row in rows:
        current = latest.get(row.forecast_id)
        if current is None or _outcome_latest_key(row) > _outcome_latest_key(current):
            latest[row.forecast_id] = row
    return latest, len(rows) - len(latest)


def _forecast_latest_key(row: TeamForecastDbRow) -> tuple[datetime, str]:
    return row.generated_at, row.payload_sha256


def _outcome_latest_key(row: TeamForecastOutcomeDbRow) -> tuple[datetime, datetime, str]:
    return row.resolved_at, row.generated_at, row.outcome_id


def _build_rows(
    forecasts: dict[str, TeamForecastDbRow],
    outcomes: dict[str, TeamForecastOutcomeDbRow],
    config: TeamEventTemplatePerformanceConfig,
) -> tuple[TeamEventTemplatePerformanceRow, ...]:
    groups: dict[tuple[str, str, str], list[TeamForecastDbRow]] = {}
    for row in forecasts.values():
        packet = team_forecast_from_db_row(row)
        key = (packet.team_id, packet.category_id, packet.event_template)
        groups.setdefault(key, []).append(row)

    result: list[TeamEventTemplatePerformanceRow] = []
    for key in sorted(groups):
        group_forecasts = groups[key]
        settled_pairs = tuple(
            (forecast, outcomes[forecast.forecast_id])
            for forecast in group_forecasts
            if forecast.forecast_id in outcomes
        )
        if not settled_pairs:
            continue
        team_id, category_id, event_template = key
        settled_count = len(settled_pairs)
        directionally_correct_count = sum(
            1 for _, outcome in settled_pairs if outcome.directionally_correct
        )
        profitable_after_cost_count = sum(
            1 for _, outcome in settled_pairs if outcome.profitable_after_cost
        )
        dispute_count = sum(1 for _, outcome in settled_pairs if outcome.resolution_dispute_flag)
        status, reason_codes = _status_and_reasons(
            settled_count=settled_count,
            dispute_count=dispute_count,
            profitable_after_cost_count=profitable_after_cost_count,
            config=config,
        )
        result.append(
            TeamEventTemplatePerformanceRow(
                team_id=team_id,
                category_id=category_id,
                event_template=event_template,
                forecast_count=len(group_forecasts),
                settled_count=settled_count,
                directionally_correct_count=directionally_correct_count,
                profitable_after_cost_count=profitable_after_cost_count,
                dispute_count=dispute_count,
                average_brier_score=_average(
                    outcome.brier_score for _, outcome in settled_pairs
                ),
                hit_rate=_rate(directionally_correct_count, settled_count),
                dispute_rate=_rate(dispute_count, settled_count),
                profitable_after_cost_rate=_rate(
                    profitable_after_cost_count,
                    settled_count,
                ),
                paper_pnl=_sum_decimal(outcome.paper_pnl for _, outcome in settled_pairs),
                average_confidence=_average(
                    forecast.confidence for forecast, _ in settled_pairs
                ),
                average_forecast_probability=_average(
                    forecast.forecast_probability for forecast, _ in settled_pairs
                ),
                status=status,
                reason_codes=reason_codes,
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        )
    return tuple(result)


def _status_and_reasons(
    *,
    settled_count: int,
    dispute_count: int,
    profitable_after_cost_count: int,
    config: TeamEventTemplatePerformanceConfig,
) -> tuple[str, tuple[str, ...]]:
    if settled_count < config.min_settled_forecasts:
        return "candidate", ("insufficient_settled_forecasts",)

    reasons: list[str] = []
    if _rate(dispute_count, settled_count) > config.max_dispute_rate:
        reasons.append("dispute_rate_above_threshold")
    if (
        _rate(profitable_after_cost_count, settled_count)
        < config.min_profitable_after_cost_rate
    ):
        reasons.append("profitability_rate_below_threshold")
    if reasons:
        return "watch", tuple(reasons)
    return "validated", ("min_settled_forecasts_met",)


def _report_reason_codes(
    *,
    duplicate_forecast_count: int,
    duplicate_outcome_count: int,
    orphan_outcome_count: int,
    status_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if duplicate_forecast_count:
        reasons.append("duplicate_forecasts_deduplicated")
    if duplicate_outcome_count:
        reasons.append("duplicate_outcomes_deduplicated")
    reasons.extend(status_reasons)
    if orphan_outcome_count:
        reasons.append("orphan_outcomes_ignored")
    return tuple(reasons)


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("average", _sum_decimal(items) / Decimal(len(items)))


def _rate(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("rate", Decimal(numerator) / Decimal(denominator))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_decimal("total", total)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(sorted(set(items)))


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
        return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_status(value: object) -> None:
    if value not in STATUSES:
        raise ValueError("status must be validated, candidate, or watch")


def _require_true_flags(label: str, value: object) -> None:
    for flag_name in SAFETY_FLAG_NAMES:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
        )
    return value.astimezone(UTC)


__all__ = (
    "TeamEventTemplatePerformanceConfig",
    "TeamEventTemplatePerformanceReport",
    "TeamEventTemplatePerformanceRow",
    "build_team_event_template_performance_report",
)
