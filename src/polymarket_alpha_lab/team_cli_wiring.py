"""Pure-ish wiring helpers for a team diagnostics CLI command.

This module deliberately stays below the actual CLI and database layers.  It
validates already-parsed CLI-style options, calls injected read-only loaders,
and adapts the diagnostics bundle into compact rows suitable for printing.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any


__all__ = (
    "TeamDiagnosticsCliLoaders",
    "TeamDiagnosticsCliOutputRow",
    "TeamDiagnosticsCliRequest",
    "TeamDiagnosticsCliResult",
    "run_team_diagnostics_cli_request",
)


Loader = Callable[..., Iterable[Any]]
BundleBuilder = Callable[..., Any]


@dataclass(frozen=True)
class TeamDiagnosticsCliRequest:
    team_id: str | None = None
    market_slug: str | None = None
    forecast_id: str | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        _require_optional_canonical_string("team_id", self.team_id)
        _require_optional_canonical_string("market_slug", self.market_slug)
        _require_optional_canonical_string("forecast_id", self.forecast_id)
        if self.limit is not None:
            _require_positive_int("limit", self.limit)


@dataclass(frozen=True)
class TeamDiagnosticsCliLoaders:
    load_forecasts: Loader
    load_evidence: Loader
    load_outcomes: Loader

    def __post_init__(self) -> None:
        for field_name in ("load_forecasts", "load_evidence", "load_outcomes"):
            if not callable(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be callable")


@dataclass(frozen=True)
class TeamDiagnosticsCliOutputRow:
    section: str
    label: str
    value: str

    def __post_init__(self) -> None:
        _require_canonical_string("section", self.section)
        _require_canonical_string("label", self.label)
        _require_canonical_string("value", self.value)


@dataclass(frozen=True)
class TeamDiagnosticsCliResult:
    request: TeamDiagnosticsCliRequest
    forecasts: tuple[Any, ...]
    evidence: tuple[Any, ...]
    outcomes: tuple[Any, ...]
    bundle: Any
    summary_rows: tuple[TeamDiagnosticsCliOutputRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.request) is not TeamDiagnosticsCliRequest:
            raise ValueError("request must be a TeamDiagnosticsCliRequest")
        object.__setattr__(self, "forecasts", _require_tuple("forecasts", self.forecasts))
        object.__setattr__(self, "evidence", _require_tuple("evidence", self.evidence))
        object.__setattr__(self, "outcomes", _require_tuple("outcomes", self.outcomes))
        object.__setattr__(
            self,
            "summary_rows",
            _normalize_output_rows(self.summary_rows),
        )
        _require_hard_flags("team diagnostics CLI result", self)
        _require_hard_flags_if_present("diagnostics bundle", self.bundle)


def run_team_diagnostics_cli_request(
    request: TeamDiagnosticsCliRequest,
    *,
    loaders: TeamDiagnosticsCliLoaders,
    bundle_builder: BundleBuilder | None = None,
) -> TeamDiagnosticsCliResult:
    if type(request) is not TeamDiagnosticsCliRequest:
        raise ValueError("request must be a TeamDiagnosticsCliRequest")
    if type(loaders) is not TeamDiagnosticsCliLoaders:
        raise ValueError("loaders must be TeamDiagnosticsCliLoaders")
    if bundle_builder is not None and not callable(bundle_builder):
        raise ValueError("bundle_builder must be callable or None")

    forecast_filters = _forecast_filters(request)
    evidence_filters = _evidence_filters(request)
    outcome_filters = _outcome_filters(request)

    forecasts = _load_rows("forecasts", loaders.load_forecasts, forecast_filters)
    evidence = _load_rows("evidence", loaders.load_evidence, evidence_filters)
    outcomes = _load_rows("outcomes", loaders.load_outcomes, outcome_filters)

    builder = bundle_builder if bundle_builder is not None else _default_bundle_builder()
    bundle = (
        builder(forecasts=forecasts, evidence=evidence, outcomes=outcomes)
        if builder is not None
        else None
    )
    _require_hard_flags_if_present("diagnostics bundle", bundle)

    return TeamDiagnosticsCliResult(
        request=request,
        forecasts=forecasts,
        evidence=evidence,
        outcomes=outcomes,
        bundle=bundle,
        summary_rows=(
            *_filter_rows(request),
            TeamDiagnosticsCliOutputRow("count", "forecasts", str(len(forecasts))),
            TeamDiagnosticsCliOutputRow("count", "evidence", str(len(evidence))),
            TeamDiagnosticsCliOutputRow("count", "outcomes", str(len(outcomes))),
            *_bundle_summary_rows(bundle),
        ),
    )


def _forecast_filters(request: TeamDiagnosticsCliRequest) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if request.team_id is not None:
        values["team_id"] = request.team_id
    if request.market_slug is not None:
        values["market_slug"] = request.market_slug
    if request.limit is not None:
        values["limit"] = request.limit
    return values


def _evidence_filters(request: TeamDiagnosticsCliRequest) -> dict[str, Any]:
    values = _forecast_filters(request)
    if request.forecast_id is not None:
        ordered: dict[str, Any] = {"forecast_id": request.forecast_id}
        ordered.update(values)
        return ordered
    return values


def _outcome_filters(request: TeamDiagnosticsCliRequest) -> dict[str, Any]:
    return _forecast_filters(request)


def _filter_rows(
    request: TeamDiagnosticsCliRequest,
) -> tuple[TeamDiagnosticsCliOutputRow, ...]:
    rows: list[TeamDiagnosticsCliOutputRow] = []
    for field_name in ("team_id", "market_slug", "forecast_id", "limit"):
        value = getattr(request, field_name)
        if value is not None:
            rows.append(TeamDiagnosticsCliOutputRow("filter", field_name, str(value)))
    return tuple(rows)


def _load_rows(
    label: str,
    loader: Loader,
    filters: dict[str, Any],
) -> tuple[Any, ...]:
    loaded = loader(**filters)
    if isinstance(loaded, (str, bytes)) or not isinstance(loaded, Iterable):
        raise ValueError(f"{label} loader must return an iterable")
    rows = tuple(loaded)
    for row in rows:
        _require_hard_flags_if_present(f"{label} row", row)
    return rows


def _default_bundle_builder() -> BundleBuilder | None:
    try:
        module = importlib.import_module("polymarket_alpha_lab.team_diagnostics_bundle")
    except ModuleNotFoundError as exc:
        if exc.name == "polymarket_alpha_lab.team_diagnostics_bundle":
            return None
        raise

    candidate = getattr(module, "build_team_diagnostics_bundle_report", None)
    if callable(candidate):
        return candidate
    return None


def _bundle_summary_rows(bundle: Any) -> tuple[TeamDiagnosticsCliOutputRow, ...]:
    if bundle is None:
        return (TeamDiagnosticsCliOutputRow("bundle", "status", "unavailable"),)

    rows: list[TeamDiagnosticsCliOutputRow] = []
    for field_name in (
        "bundle_status",
        "diagnostic_status",
        "status",
        "overall_status",
        "readiness_status",
    ):
        if hasattr(bundle, field_name):
            value = getattr(bundle, field_name)
            if value is not None:
                rows.append(
                    TeamDiagnosticsCliOutputRow(
                        "bundle",
                        field_name,
                        _string_value(value),
                    ),
                )
                break

    rows.extend(_explicit_bundle_rows(bundle))
    if not rows:
        rows.append(TeamDiagnosticsCliOutputRow("bundle", "status", "available"))
    return tuple(rows)


def _explicit_bundle_rows(bundle: Any) -> tuple[TeamDiagnosticsCliOutputRow, ...]:
    explicit_rows = getattr(bundle, "summary_rows", None)
    if explicit_rows is None:
        explicit_rows = getattr(bundle, "rows", None)
    if explicit_rows is None:
        return ()
    if isinstance(explicit_rows, (str, bytes)) or not isinstance(explicit_rows, Iterable):
        raise ValueError("bundle rows must be iterable")
    return tuple(_coerce_output_row(row) for row in explicit_rows)


def _coerce_output_row(row: Any) -> TeamDiagnosticsCliOutputRow:
    if type(row) is TeamDiagnosticsCliOutputRow:
        return row
    if isinstance(row, Mapping):
        return TeamDiagnosticsCliOutputRow(
            _string_value(row.get("section", "bundle")),
            _string_value(row.get("label", row.get("name", "value"))),
            _string_value(row.get("value", "")),
        )
    return TeamDiagnosticsCliOutputRow(
        _string_value(getattr(row, "section", "bundle")),
        _string_value(getattr(row, "label", getattr(row, "name", "value"))),
        _string_value(getattr(row, "value", "")),
    )


def _normalize_output_rows(
    rows: tuple[TeamDiagnosticsCliOutputRow, ...],
) -> tuple[TeamDiagnosticsCliOutputRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("summary_rows must be iterable")
    return tuple(_coerce_output_row(row) for row in rows)


def _require_tuple(field_name: str, value: tuple[Any, ...]) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_optional_canonical_string(field_name: str, value: object) -> None:
    if value is not None:
        _require_canonical_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_hard_flags_if_present(label: str, value: object) -> None:
    if value is None:
        return
    present = tuple(
        field_name
        for field_name in ("paper_only", "report_only", "readonly")
        if hasattr(value, field_name)
    )
    if not present:
        return
    for field_name in present:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value)
