"""Pure correction-safe settlement sample exporter.

Selection is frozen before evaluation: earliest eligible forecast per
(condition_id, team_id, config_version), a distinct outcome-observation cutoff,
and deterministic identities for every selected row. Pending forecasts have no
eligible outcome or a latest disputed outcome. Every other dropped input has a
reason code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Sequence

from .central_data_contracts import _as_utc


EXPORT_SCHEMA_VERSION = "p2a-settlement-export-v1"
REQUIRED_CONFIG_PREFIX = "p1-"
EXCLUSION_BASELINE_HINT = "baseline_hint_default"
EXCLUSION_FORECAST_AFTER_CUTOFF = "forecast_after_cutoff"
EXCLUSION_INVALID_ROW = "invalid_forecast_row"
EXCLUSION_INVALID_OUTCOME_ROW = "invalid_outcome_row"
EXCLUSION_NOT_EARLIEST = "not_earliest_forecast"
EXCLUSION_OUTCOME_AFTER_CUTOFF = "outcome_after_cutoff"
EXCLUSION_OUTCOME_BEFORE_FORECAST = "outcome_before_forecast"


@dataclass(frozen=True)
class ForecastRowView:
    forecast_id: str
    condition_id: str
    team_id: str
    config_version: str
    forecast_p_yes: Decimal
    market_implied_p_yes: Decimal
    generated_at: datetime
    payload_sha256: str | None = None
    event_id: str | None = None

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
        if self.payload_sha256 is not None and (
            type(self.payload_sha256) is not str
            or len(self.payload_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.payload_sha256)
        ):
            raise ValueError("payload_sha256 must be a lowercase SHA-256 or None")
        if self.event_id is not None and (
            type(self.event_id) is not str
            or not self.event_id
            or self.event_id.strip() != self.event_id
        ):
            raise ValueError("event_id must be a canonical nonblank string or None")


@dataclass(frozen=True)
class SettledOutcomeView:
    condition_id: str
    outcome: str
    observed_at: datetime
    dispute_flag: bool = False
    payload_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self.condition_id) is not str or not self.condition_id:
            raise ValueError("condition_id must be a canonical nonblank string")
        if self.outcome not in ("yes", "no"):
            raise ValueError("outcome must be 'yes' or 'no'")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.dispute_flag) is not bool:
            raise ValueError("dispute_flag must be a bool")
        if self.payload_sha256 is not None and (
            type(self.payload_sha256) is not str
            or len(self.payload_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.payload_sha256)
        ):
            raise ValueError("payload_sha256 must be a lowercase SHA-256 or None")

    @property
    def outcome_id(self) -> str:
        identity = (
            f"{self.condition_id}|{self.observed_at.isoformat()}|"
            f"{self.outcome}|{self.payload_sha256 or 'unknown'}"
        )
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()


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


def build_settlement_export(
    forecasts: Sequence[ForecastRowView],
    outcomes: Sequence[SettledOutcomeView],
    *,
    as_of_evaluation_cutoff: datetime,
    as_of_outcome_cutoff: datetime,
    invalid_forecast_row_count: int = 0,
    invalid_outcome_row_count: int = 0,
    prior_export_id: str | None = None,
) -> ExportResult:
    for name, value in (
        ("invalid_forecast_row_count", invalid_forecast_row_count),
        ("invalid_outcome_row_count", invalid_outcome_row_count),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative int")
    if prior_export_id is not None and (
        type(prior_export_id) is not str
        or len(prior_export_id) != 64
        or any(char not in "0123456789abcdef" for char in prior_export_id)
    ):
        raise ValueError("prior_export_id must be a lowercase SHA-256 or None")

    forecast_cutoff = _as_utc("as_of_evaluation_cutoff", as_of_evaluation_cutoff)
    outcome_cutoff = _as_utc("as_of_outcome_cutoff", as_of_outcome_cutoff)
    if outcome_cutoff < forecast_cutoff:
        raise ValueError("as_of_outcome_cutoff must not precede as_of_evaluation_cutoff")

    exclusions: dict[str, int] = {}

    def exclude(reason: str, count: int = 1) -> None:
        exclusions[reason] = exclusions.get(reason, 0) + count

    if invalid_forecast_row_count:
        exclude(EXCLUSION_INVALID_ROW, invalid_forecast_row_count)
    if invalid_outcome_row_count:
        exclude(EXCLUSION_INVALID_OUTCOME_ROW, invalid_outcome_row_count)

    current_outcomes: dict[str, SettledOutcomeView] = {}
    for outcome in outcomes:
        if outcome.observed_at > outcome_cutoff:
            exclude(EXCLUSION_OUTCOME_AFTER_CUTOFF)
            continue
        existing = current_outcomes.get(outcome.condition_id)
        if existing is None or (
            outcome.observed_at,
            outcome.outcome_id,
        ) > (existing.observed_at, existing.outcome_id):
            current_outcomes[outcome.condition_id] = outcome

    eligible: list[ForecastRowView] = []
    for row in forecasts:
        if not row.config_version.startswith(REQUIRED_CONFIG_PREFIX):
            exclude(EXCLUSION_BASELINE_HINT)
        elif row.generated_at > forecast_cutoff:
            exclude(EXCLUSION_FORECAST_AFTER_CUTOFF)
        else:
            eligible.append(row)

    selected: dict[tuple[str, str, str], ForecastRowView] = {}
    for row in eligible:
        key = (row.condition_id, row.team_id, row.config_version)
        existing = selected.get(key)
        if existing is None:
            selected[key] = row
            continue
        exclude(EXCLUSION_NOT_EARLIEST)
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
    selected_outcome_ids: list[str] = []
    selected_outcome_payload_hashes: list[str | None] = []
    pending = 0
    disputed_pending = 0
    for row in ordered:
        outcome = current_outcomes.get(row.condition_id)
        if outcome is None:
            pending += 1
            continue
        if outcome.observed_at < row.generated_at:
            exclude(EXCLUSION_OUTCOME_BEFORE_FORECAST)
            continue
        if outcome.dispute_flag:
            pending += 1
            disputed_pending += 1
            continue
        selected_outcome_ids.append(outcome.outcome_id)
        selected_outcome_payload_hashes.append(outcome.payload_sha256)
        samples.append(
            {
                "condition_id": row.condition_id,
                "config_version": row.config_version,
                "event_id": row.event_id,
                "forecast_id": row.forecast_id,
                "forecast_payload_sha256": row.payload_sha256,
                "outcome_id": outcome.outcome_id,
                "outcome_payload_sha256": outcome.payload_sha256,
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
            "as_of_evaluation_cutoff": forecast_cutoff.isoformat(),
            "as_of_outcome_cutoff": outcome_cutoff.isoformat(),
            "pending_count": pending,
            "samples": samples,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
    export_id = hashlib.sha256(document.encode("utf-8")).hexdigest()
    manifest = json.dumps(
        {
            "schema_version": EXPORT_SCHEMA_VERSION,
            "selection_rule": "earliest eligible forecast per (condition_id, team_id, config_version) generated before the forecast cutoff",
            "outcome_selection_rule": "latest outcome per condition observed at or before the outcome cutoff",
            "baseline_provenance": f"config_version prefix {REQUIRED_CONFIG_PREFIX}",
            "ordering": "condition_id asc, team_id asc, generated_at asc, forecast_id asc",
            "forecast_cutoff": forecast_cutoff.isoformat(),
            "outcome_cutoff": outcome_cutoff.isoformat(),
            "included_count": len(samples),
            "pending_count": pending,
            "exclusion_reasons": dict(sorted(exclusions.items())),
            "input_forecast_rows": len(forecasts) + invalid_forecast_row_count,
            "input_outcome_rows": len(outcomes) + invalid_outcome_row_count,
            "selected_forecast_ids": [row.forecast_id for row in ordered],
            "selected_forecast_payload_sha256": [row.payload_sha256 for row in ordered],
            "selected_forecast_event_ids": [row.event_id for row in ordered],
            "selected_outcome_ids": selected_outcome_ids,
            "selected_outcome_payload_sha256": selected_outcome_payload_hashes,
            "selected_event_ids": sorted({row.event_id for row in ordered if row.event_id}),
            "unknown_event_lineage_count": sum(row.event_id is None for row in ordered),
            "config_versions": sorted({row.config_version for row in ordered}),
            "selected_cohorts": sorted(
                {f"{row.team_id}:{row.config_version}" for row in ordered}
            ),
            "disputed_pending": disputed_pending,
            "prior_export_id": prior_export_id,
            "export_id": export_id,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
    return ExportResult(
        document=document,
        manifest=manifest,
        included_count=len(samples),
        pending_count=pending,
        exclusion_reasons=tuple(sorted(exclusions.items())),
    )


__all__ = (
    "EXPORT_SCHEMA_VERSION",
    "EXCLUSION_BASELINE_HINT",
    "EXCLUSION_FORECAST_AFTER_CUTOFF",
    "EXCLUSION_INVALID_OUTCOME_ROW",
    "EXCLUSION_INVALID_ROW",
    "EXCLUSION_NOT_EARLIEST",
    "EXCLUSION_OUTCOME_AFTER_CUTOFF",
    "EXCLUSION_OUTCOME_BEFORE_FORECAST",
    "ExportResult",
    "ForecastRowView",
    "REQUIRED_CONFIG_PREFIX",
    "SettledOutcomeView",
    "build_settlement_export",
)
