"""Pure exporter: forecast rows + settled outcomes -> evaluation document.

Selection rules (frozen before evaluation): earliest eligible forecast
per (condition_id, team_id, config_version) generated before the cutoff,
baseline provenance required (config cohort prefix), deterministic
ordering with forecast_id as the final tie-breaker. Pending = eligible
selected forecasts without a current settled outcome. Every exclusion
carries a reason; nothing is silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .central_data_contracts import _as_utc


REQUIRED_CONFIG_PREFIX = "p1-"
EXCLUSION_BASELINE_HINT = "baseline_hint_default"
EXCLUSION_FORECAST_AFTER_CUTOFF = "forecast_after_cutoff"
EXCLUSION_INVALID_ROW = "invalid_forecast_row"
EXCLUSION_NOT_EARLIEST = "not_earliest_forecast"
EXCLUSION_NO_OUTCOME_COMPLETES_ELIGIBLE_AS_PENDING = None  # sentinel docs only


@dataclass(frozen=True)
class ForecastRowView:
    forecast_id: str
    condition_id: str
    team_id: str
    config_version: str
    forecast_p_yes: Decimal
    market_implied_p_yes: Decimal
    generated_at: datetime

    def __post_init__(self) -> None:
        for name in ("forecast_id", "condition_id", "team_id", "config_version"):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        for name in ("forecast_p_yes", "market_implied_p_yes"):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not Decimal(0) < value < Decimal(1):
                raise ValueError(f"{name} must be a Decimal strictly between 0 and 1")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))


@dataclass(frozen=True)
class SettledOutcomeView:
    condition_id: str
    outcome: str
    observed_at: datetime
    dispute_flag: bool = False

    def __post_init__(self) -> None:
        if type(self.condition_id) is not str or not self.condition_id:
            raise ValueError("condition_id must be a canonical nonblank string")
        if self.outcome not in ("yes", "no"):
            raise ValueError("outcome must be 'yes' or 'no'")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.dispute_flag) is not bool:
            raise ValueError("dispute_flag must be a bool")


@dataclass(frozen=True)
class ExportResult:
    document: str
    manifest: str
    included_count: int
    pending_count: int
    exclusion_reasons: tuple[tuple[str, int], ...]

    @property
    def export_id(self) -> str:
        return hashlib.sha256(self.document.encode("utf-8")).hexdigest()


def _current_outcomes(outcomes: Sequence[SettledOutcomeView]) -> dict[str, SettledOutcomeView]:
    current: dict[str, SettledOutcomeView] = {}
    for outcome in outcomes:
        existing = current.get(outcome.condition_id)
        if existing is None or outcome.observed_at > existing.observed_at:
            current[outcome.condition_id] = outcome
    return current


def build_settlement_export(
    forecasts: Sequence[ForecastRowView],
    outcomes: Sequence[SettledOutcomeView],
    *,
    as_of_evaluation_cutoff: datetime,
    invalid_forecast_row_count: int = 0,
) -> ExportResult:
    if type(invalid_forecast_row_count) is not int or invalid_forecast_row_count < 0:
        raise ValueError("invalid_forecast_row_count must be a nonnegative int")
    cutoff = _as_utc("cutoff", as_of_evaluation_cutoff)
    current_outcomes = _current_outcomes(outcomes)
    exclusions: dict[str, int] = {}

    def _exclude(reason: str) -> None:
        exclusions[reason] = exclusions.get(reason, 0) + 1

    if invalid_forecast_row_count:
        exclusions[EXCLUSION_INVALID_ROW] = invalid_forecast_row_count

    eligible: list[ForecastRowView] = []
    for row in forecasts:
        if not row.config_version.startswith(REQUIRED_CONFIG_PREFIX):
            _exclude(EXCLUSION_BASELINE_HINT)
            continue
        if row.generated_at > cutoff:
            _exclude(EXCLUSION_FORECAST_AFTER_CUTOFF)
            continue
        eligible.append(row)

    selected: dict[tuple[str, str, str], ForecastRowView] = {}
    for row in eligible:
        key = (row.condition_id, row.team_id, row.config_version)
        existing = selected.get(key)
        if existing is None:
            selected[key] = row
            continue
        _exclude(EXCLUSION_NOT_EARLIEST)
        if (row.generated_at, row.forecast_id) < (
            existing.generated_at,
            existing.forecast_id,
        ):
            selected[key] = row

    ordered = sorted(
        selected.values(),
        key=lambda row: (row.condition_id, row.team_id, row.generated_at, row.forecast_id),
    )
    samples: list[dict[str, Any]] = []
    pending = 0
    for row in ordered:
        outcome = current_outcomes.get(row.condition_id)
        if outcome is None or outcome.dispute_flag:
            pending += 1
            continue
        samples.append(
            {
                "condition_id": row.condition_id,
                "team_id": row.team_id,
                "forecast_p_yes": format(row.forecast_p_yes, "f"),
                "market_implied_p_yes": format(row.market_implied_p_yes, "f"),
                "actual_outcome": outcome.outcome,
                "generated_at": row.generated_at.isoformat(),
                "settled_at": outcome.observed_at.isoformat(),
            }
        )

    document = json.dumps(
        {
            "as_of_evaluation_cutoff": cutoff.isoformat(),
            "pending_count": pending,
            "samples": samples,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
    export_id = hashlib.sha256(document.encode("utf-8")).hexdigest()
    manifest = json.dumps(
        {
            "selection_rule": "earliest eligible forecast per (condition_id, team_id, config_version) generated before the cutoff",
            "baseline_provenance": f"config_version prefix {REQUIRED_CONFIG_PREFIX}",
            "ordering": "condition_id asc, team_id asc, generated_at asc, forecast_id asc",
            "forecast_cutoff": cutoff.isoformat(),
            "included_count": len(samples),
            "pending_count": pending,
            "exclusion_reasons": dict(sorted(exclusions.items())),
            "input_forecast_rows": len(forecasts) + invalid_forecast_row_count,
            "input_outcome_rows": len(outcomes),
            "selected_forecast_ids": [row.forecast_id for row in ordered],
            "disputed_pending": sum(
                1 for o in current_outcomes.values() if o.dispute_flag
            ),
            "export_id": export_id,
        },
        indent=2,
        sort_keys=True,
    )
    return ExportResult(
        document=document,
        manifest=manifest + "\n",
        included_count=len(samples),
        pending_count=pending,
        exclusion_reasons=tuple(sorted(exclusions.items())),
    )


__all__ = (
    "EXCLUSION_BASELINE_HINT",
    "EXCLUSION_FORECAST_AFTER_CUTOFF",
    "EXCLUSION_INVALID_ROW",
    "EXCLUSION_NOT_EARLIEST",
    "ExportResult",
    "ForecastRowView",
    "REQUIRED_CONFIG_PREFIX",
    "SettledOutcomeView",
    "build_settlement_export",
)
