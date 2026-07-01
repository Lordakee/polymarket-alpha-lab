"""Pure team memory synthesis reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


_DECIMAL_QUANTUM = Decimal("0.000001")
_DECIMAL_CONTEXT = Context(prec=64)
_ZERO = Decimal("0")
_ONE = Decimal("1")
_CATEGORY_TEMPLATE = "all_event_templates"
_CATEGORY_SCOPE = "team_category"
_TEMPLATE_SCOPE = "event_template"
_GATE_ELIGIBLE = "eligible"
_GATE_LOW_SAMPLE = "low_sample"


@dataclass(frozen=True)
class TeamMemorySynthesisConfig:
    config_version: str = "team-memory-synthesis-v0"
    min_category_settled_forecasts: int = 30
    min_event_template_settled_forecasts: int = 10
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int(
            "min_category_settled_forecasts",
            self.min_category_settled_forecasts,
        )
        _require_positive_int(
            "min_event_template_settled_forecasts",
            self.min_event_template_settled_forecasts,
        )
        require_paper_only_flags("team memory synthesis config", self)


@dataclass(frozen=True)
class TeamMemoryReferenceRow:
    reference_id: str
    reference_scope: str
    team_id: str
    category_id: str
    event_template: str
    settled_forecast_count: int
    required_settled_forecast_count: int
    evidence_row_count: int
    directionally_correct_count: int
    directionally_correct_ratio: Decimal
    average_forecast_probability: Decimal
    average_forecast_error: Decimal
    average_brier_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "reference_id",
            "team_id",
            "category_id",
            "event_template",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.reference_scope not in (_CATEGORY_SCOPE, _TEMPLATE_SCOPE):
            raise ValueError("reference_scope must be a known team memory scope")
        if self.reference_scope == _CATEGORY_SCOPE:
            if self.event_template != _CATEGORY_TEMPLATE:
                raise ValueError("team_category event_template must be all_event_templates")
        elif self.event_template == _CATEGORY_TEMPLATE:
            raise ValueError("event_template row must name a concrete event template")
        for field_name in (
            "settled_forecast_count",
            "required_settled_forecast_count",
            "evidence_row_count",
            "directionally_correct_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.required_settled_forecast_count <= 0:
            raise ValueError("required_settled_forecast_count must be positive")
        if self.directionally_correct_count > self.settled_forecast_count:
            raise ValueError(
                "directionally_correct_count must not exceed settled_forecast_count",
            )
        object.__setattr__(
            self,
            "directionally_correct_ratio",
            _normalize_probability_decimal(
                "directionally_correct_ratio",
                self.directionally_correct_ratio,
            ),
        )
        for field_name in (
            "average_forecast_probability",
            "average_forecast_error",
            "average_brier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.gate_status not in (_GATE_ELIGIBLE, _GATE_LOW_SAMPLE):
            raise ValueError("gate_status must be a known team memory gate status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("team memory reference row", self)


@dataclass(frozen=True)
class TeamMemorySynthesisReport:
    generated_at: datetime
    config_version: str
    forecast_row_count: int
    unique_forecast_count: int
    duplicate_forecast_count: int
    evidence_row_count: int
    outcome_row_count: int
    orphan_evidence_count: int
    orphan_outcome_count: int
    settled_forecast_count: int
    reference_count: int
    eligible_reference_count: int
    rows: tuple[TeamMemoryReferenceRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_row_count",
            "unique_forecast_count",
            "duplicate_forecast_count",
            "evidence_row_count",
            "outcome_row_count",
            "orphan_evidence_count",
            "orphan_outcome_count",
            "settled_forecast_count",
            "reference_count",
            "eligible_reference_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_reference_rows(self.rows))
        if self.reference_count != len(self.rows):
            raise ValueError("reference_count must equal rows length")
        eligible_count = sum(1 for row in self.rows if row.gate_status == _GATE_ELIGIBLE)
        if self.eligible_reference_count != eligible_count:
            raise ValueError("eligible_reference_count must match rows")
        if self.unique_forecast_count > self.forecast_row_count:
            raise ValueError("unique_forecast_count must not exceed forecast_row_count")
        if self.duplicate_forecast_count != (
            self.forecast_row_count - self.unique_forecast_count
        ):
            raise ValueError("duplicate_forecast_count must match forecast counts")
        require_paper_only_flags("team memory synthesis report", self)


@dataclass(frozen=True)
class _ForecastEntry:
    row: TeamForecastDbRow
    packet: Any
    seq_idx: int


def build_team_memory_synthesis_report(
    forecasts: list[TeamForecastDbRow] | tuple[TeamForecastDbRow, ...],
    evidence: list[TeamForecastEvidenceDbRow] | tuple[TeamForecastEvidenceDbRow, ...],
    outcomes: list[TeamForecastOutcomeDbRow] | tuple[TeamForecastOutcomeDbRow, ...],
    *,
    config: TeamMemorySynthesisConfig,
    generated_at: datetime,
) -> TeamMemorySynthesisReport:
    if type(config) is not TeamMemorySynthesisConfig:
        raise ValueError("config must be a TeamMemorySynthesisConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    forecast_rows = _normalize_rows("forecasts", forecasts, TeamForecastDbRow)
    evidence_rows = _normalize_rows("evidence", evidence, TeamForecastEvidenceDbRow)
    outcome_rows = _normalize_rows("outcomes", outcomes, TeamForecastOutcomeDbRow)

    forecast_entries = _forecast_entries(forecast_rows)
    selected_forecasts = _selected_forecasts(forecast_entries)
    evidence_by_forecast, orphan_evidence_count = _evidence_by_forecast(
        evidence_rows,
        selected_forecasts,
    )
    latest_outcomes, orphan_outcome_count = _latest_outcomes(
        outcome_rows,
        selected_forecasts,
    )
    rows = _build_reference_rows(
        selected_forecasts,
        evidence_by_forecast,
        latest_outcomes,
        config=config,
    )

    return TeamMemorySynthesisReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        forecast_row_count=len(forecast_rows),
        unique_forecast_count=len(selected_forecasts),
        duplicate_forecast_count=len(forecast_rows) - len(selected_forecasts),
        evidence_row_count=len(evidence_rows),
        outcome_row_count=len(outcome_rows),
        orphan_evidence_count=orphan_evidence_count,
        orphan_outcome_count=orphan_outcome_count,
        settled_forecast_count=len(latest_outcomes),
        reference_count=len(rows),
        eligible_reference_count=sum(
            1 for row in rows if row.gate_status == _GATE_ELIGIBLE
        ),
        rows=rows,
    )


def _normalize_rows(
    field_name: str,
    value: object,
    row_type: type[Any],
) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple of DB rows")
    normalized: list[Any] = []
    for row in value:
        if type(row) is not row_type:
            raise ValueError(f"{field_name} must contain only {row_type.__name__}")
        normalized.append(_canonical_db_row(row_type, row))
    return tuple(normalized)


def _canonical_db_row(row_type: type[Any], row: Any) -> Any:
    return row_type(**{field.name: getattr(row, field.name) for field in fields(row_type)})


def _forecast_entries(rows: tuple[TeamForecastDbRow, ...]) -> tuple[_ForecastEntry, ...]:
    entries: list[_ForecastEntry] = []
    for seq_idx, row in enumerate(rows):
        packet = team_forecast_from_db_row(row)
        entries.append(_ForecastEntry(row=row, packet=packet, seq_idx=seq_idx))
    return tuple(entries)


def _selected_forecasts(
    entries: tuple[_ForecastEntry, ...],
) -> dict[str, _ForecastEntry]:
    selected: dict[str, _ForecastEntry] = {}
    for entry in entries:
        existing = selected.get(entry.row.forecast_id)
        if existing is None or _forecast_key(entry) > _forecast_key(existing):
            selected[entry.row.forecast_id] = entry
    return selected


def _forecast_key(entry: _ForecastEntry) -> tuple[datetime, str, int]:
    return (entry.row.generated_at, entry.row.payload_sha256, entry.seq_idx)


def _evidence_by_forecast(
    rows: tuple[TeamForecastEvidenceDbRow, ...],
    selected_forecasts: dict[str, _ForecastEntry],
) -> tuple[dict[str, tuple[TeamForecastEvidenceDbRow, ...]], int]:
    grouped: dict[str, list[TeamForecastEvidenceDbRow]] = {}
    orphan_count = 0
    for row in rows:
        entry = selected_forecasts.get(row.forecast_id)
        if entry is None:
            orphan_count += 1
            continue
        _validate_joined_row("evidence", row, entry)
        grouped.setdefault(row.forecast_id, []).append(row)
    return ({key: tuple(value) for key, value in grouped.items()}, orphan_count)


def _latest_outcomes(
    rows: tuple[TeamForecastOutcomeDbRow, ...],
    selected_forecasts: dict[str, _ForecastEntry],
) -> tuple[dict[str, TeamForecastOutcomeDbRow], int]:
    selected: dict[str, TeamForecastOutcomeDbRow] = {}
    orphan_count = 0
    for row in rows:
        entry = selected_forecasts.get(row.forecast_id)
        if entry is None:
            orphan_count += 1
            continue
        _validate_joined_row("outcome", row, entry)
        existing = selected.get(row.forecast_id)
        if existing is None or _outcome_key(row) > _outcome_key(existing):
            selected[row.forecast_id] = row
    return selected, orphan_count


def _outcome_key(row: TeamForecastOutcomeDbRow) -> tuple[datetime, datetime, str]:
    return (row.resolved_at, row.generated_at, row.outcome_id)


def _validate_joined_row(label: str, row: Any, entry: _ForecastEntry) -> None:
    if row.team_id != entry.row.team_id:
        raise ValueError(f"{label} team_id must match forecast")
    if row.market_slug != entry.row.market_slug:
        raise ValueError(f"{label} market_slug must match forecast")


def _build_reference_rows(
    selected_forecasts: dict[str, _ForecastEntry],
    evidence_by_forecast: dict[str, tuple[TeamForecastEvidenceDbRow, ...]],
    latest_outcomes: dict[str, TeamForecastOutcomeDbRow],
    *,
    config: TeamMemorySynthesisConfig,
) -> tuple[TeamMemoryReferenceRow, ...]:
    category_groups: dict[tuple[str, str], list[tuple[_ForecastEntry, TeamForecastOutcomeDbRow]]] = {}
    template_groups: dict[
        tuple[str, str, str],
        list[tuple[_ForecastEntry, TeamForecastOutcomeDbRow]],
    ] = {}
    for forecast_id, outcome in latest_outcomes.items():
        entry = selected_forecasts[forecast_id]
        category_key = (entry.packet.team_id, entry.packet.category_id)
        template_key = (
            entry.packet.team_id,
            entry.packet.category_id,
            entry.packet.event_template,
        )
        category_groups.setdefault(category_key, []).append((entry, outcome))
        template_groups.setdefault(template_key, []).append((entry, outcome))

    rows: list[TeamMemoryReferenceRow] = []
    for (team_id, category_id), items in category_groups.items():
        rows.append(
            _reference_row(
                reference_scope=_CATEGORY_SCOPE,
                team_id=team_id,
                category_id=category_id,
                event_template=_CATEGORY_TEMPLATE,
                items=tuple(items),
                evidence_by_forecast=evidence_by_forecast,
                required_count=config.min_category_settled_forecasts,
            ),
        )
    for (team_id, category_id, event_template), items in template_groups.items():
        rows.append(
            _reference_row(
                reference_scope=_TEMPLATE_SCOPE,
                team_id=team_id,
                category_id=category_id,
                event_template=event_template,
                items=tuple(items),
                evidence_by_forecast=evidence_by_forecast,
                required_count=config.min_event_template_settled_forecasts,
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                0 if row.reference_scope == _CATEGORY_SCOPE else 1,
                row.team_id,
                row.category_id,
                row.event_template,
            ),
        ),
    )


def _reference_row(
    *,
    reference_scope: str,
    team_id: str,
    category_id: str,
    event_template: str,
    items: tuple[tuple[_ForecastEntry, TeamForecastOutcomeDbRow], ...],
    evidence_by_forecast: dict[str, tuple[TeamForecastEvidenceDbRow, ...]],
    required_count: int,
) -> TeamMemoryReferenceRow:
    settled_count = len(items)
    directionally_correct_count = sum(1 for _, outcome in items if outcome.directionally_correct)
    evidence_count = sum(
        len(evidence_by_forecast.get(entry.row.forecast_id, ()))
        for entry, _ in items
    )
    gate_status = _GATE_ELIGIBLE if settled_count >= required_count else _GATE_LOW_SAMPLE
    reason_codes = (
        ("eligible_memory_reference",)
        if gate_status == _GATE_ELIGIBLE
        else ("below_min_settled_forecasts",)
    )
    return TeamMemoryReferenceRow(
        reference_id=(
            f"team_memory:{team_id}:{category_id}:{event_template}"
        ),
        reference_scope=reference_scope,
        team_id=team_id,
        category_id=category_id,
        event_template=event_template,
        settled_forecast_count=settled_count,
        required_settled_forecast_count=required_count,
        evidence_row_count=evidence_count,
        directionally_correct_count=directionally_correct_count,
        directionally_correct_ratio=_ratio(directionally_correct_count, settled_count),
        average_forecast_probability=_average(
            tuple(entry.packet.forecast_probability for entry, _ in items),
        ),
        average_forecast_error=_average(tuple(outcome.forecast_error for _, outcome in items)),
        average_brier_score=_average(tuple(outcome.brier_score for _, outcome in items)),
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("average values must not be empty")
    with localcontext(_DECIMAL_CONTEXT):
        return (sum(values, _ZERO) / Decimal(len(values))).quantize(_DECIMAL_QUANTUM)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        raise ValueError("ratio denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return (Decimal(numerator) / Decimal(denominator)).quantize(_DECIMAL_QUANTUM)


def _normalize_reference_rows(value: object) -> tuple[TeamMemoryReferenceRow, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple of TeamMemoryReferenceRow")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemoryReferenceRow:
            raise ValueError("rows must contain only TeamMemoryReferenceRow")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple of canonical strings")
    items = tuple(value)
    if not items:
        raise ValueError("reason_codes must contain canonical strings")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_DECIMAL_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "TeamMemoryReferenceRow",
    "TeamMemorySynthesisConfig",
    "TeamMemorySynthesisReport",
    "build_team_memory_synthesis_report",
)
