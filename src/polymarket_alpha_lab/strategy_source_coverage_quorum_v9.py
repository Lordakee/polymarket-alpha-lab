"""Read-only strategy source coverage quorum v9 reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_SOURCE_COVERAGE_QUORUM_V9_CONFIG_VERSION = (
    "strategy-source-coverage-quorum-v9"
)

COUNT_QUANTUM = Decimal("1")
HOUR_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_HOURS = Decimal("0.000000")
SECONDS_PER_HOUR = Decimal("3600")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_FAMILIES = ("primary", "official", "secondary", "market_data")
QUORUM_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "strategy_source_coverage_quorum_v9_missing_primary",
    "strategy_source_coverage_quorum_v9_missing_official",
    "strategy_source_coverage_quorum_v9_missing_secondary",
    "strategy_source_coverage_quorum_v9_missing_market_data",
    "strategy_source_coverage_quorum_v9_stale_sources",
    "strategy_source_coverage_quorum_v9_passed",
)
REPORT_REASON_CODES = (
    "strategy_source_coverage_quorum_v9_clear",
    "strategy_source_coverage_quorum_v9_missing_primary",
    "strategy_source_coverage_quorum_v9_missing_official",
    "strategy_source_coverage_quorum_v9_missing_secondary",
    "strategy_source_coverage_quorum_v9_missing_market_data",
    "strategy_source_coverage_quorum_v9_stale_sources_present",
    "strategy_source_coverage_quorum_v9_passed",
)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}


@dataclass(frozen=True)
class StrategySourceCoverageQuorumV9Config:
    config_version: str = DEFAULT_STRATEGY_SOURCE_COVERAGE_QUORUM_V9_CONFIG_VERSION
    max_source_age_hours: Decimal = Decimal("6.000000")
    required_source_families: tuple[str, ...] = SOURCE_FAMILIES
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategySourceCoverageQuorumV9Config,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_hours",
            _normalize_positive_hours(
                "max_source_age_hours",
                self.max_source_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_required_source_families(self.required_source_families),
        )
        require_paper_only_flags("StrategySourceCoverageQuorumV9Config", self)


@dataclass(frozen=True)
class StrategySourceCoverageQuorumV9Source:
    candidate_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "source",
            self,
            StrategySourceCoverageQuorumV9Source,
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("source_id", self.source_id)
        _require_source_family("source_family", self.source_family)
        object.__setattr__(
            self,
            "observed_at",
            _as_exact_utc("observed_at", self.observed_at),
        )
        require_paper_only_flags("StrategySourceCoverageQuorumV9Source", self)


@dataclass(frozen=True)
class StrategySourceCoverageQuorumV9Row:
    candidate_id: str
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    primary_source_count: Decimal
    official_source_count: Decimal
    secondary_source_count: Decimal
    market_data_source_count: Decimal
    quorum_status: str
    missing_source_families: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategySourceCoverageQuorumV9Row)
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "primary_source_count",
            "official_source_count",
            "secondary_source_count",
            "market_data_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("quorum_status", self.quorum_status, QUORUM_STATUSES)
        object.__setattr__(
            self,
            "missing_source_families",
            _normalize_source_families(
                "missing_source_families",
                self.missing_source_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("StrategySourceCoverageQuorumV9Row", self)


@dataclass(frozen=True)
class StrategySourceCoverageQuorumV9Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    stale_candidate_count: Decimal
    quorum_status: str
    missing_source_families: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[StrategySourceCoverageQuorumV9Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategySourceCoverageQuorumV9Report)
        object.__setattr__(
            self,
            "generated_at",
            _as_exact_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "stale_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("quorum_status", self.quorum_status, QUORUM_STATUSES)
        object.__setattr__(
            self,
            "missing_source_families",
            _normalize_source_families(
                "missing_source_families",
                self.missing_source_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("strategy source coverage quorum v9 report", self)
        require_paper_only_flags("StrategySourceCoverageQuorumV9Report", self)


def build_strategy_source_coverage_quorum_v9(
    sources: list[StrategySourceCoverageQuorumV9Source]
    | tuple[StrategySourceCoverageQuorumV9Source, ...],
    *,
    config: StrategySourceCoverageQuorumV9Config,
    generated_at: datetime,
) -> StrategySourceCoverageQuorumV9Report:
    if type(config) is not StrategySourceCoverageQuorumV9Config:
        raise ValueError("config must be a StrategySourceCoverageQuorumV9Config")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_exact_utc("generated_at", generated_at)
    input_rows = _normalize_sources(sources, generated_at_utc)
    groups = _candidate_groups(input_rows)
    rows = tuple(
        sorted(
            (
                _candidate_row(candidate_id, candidate_sources, config, generated_at_utc)
                for candidate_id, candidate_sources in groups
            ),
            key=_row_sort_key,
        ),
    )
    return StrategySourceCoverageQuorumV9Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(input_rows)),
        candidate_count=_count(len(rows)),
        pass_candidate_count=_status_count(rows, "pass"),
        watch_candidate_count=_status_count(rows, "watch"),
        blocked_candidate_count=_status_count(rows, "blocked"),
        stale_candidate_count=_reason_count(
            rows,
            "strategy_source_coverage_quorum_v9_stale_sources",
        ),
        quorum_status=_report_status(rows),
        missing_source_families=_report_missing_source_families(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_source_coverage_quorum_v9_payload(
    report: StrategySourceCoverageQuorumV9Report,
) -> dict[str, Any]:
    if type(report) is not StrategySourceCoverageQuorumV9Report:
        raise ValueError("report must be a StrategySourceCoverageQuorumV9Report")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy source coverage quorum v9 report", report)
    return json_ready_no_floats(report)


def _candidate_row(
    candidate_id: str,
    sources: tuple[StrategySourceCoverageQuorumV9Source, ...],
    config: StrategySourceCoverageQuorumV9Config,
    generated_at: datetime,
) -> StrategySourceCoverageQuorumV9Row:
    fresh_sources = tuple(
        source
        for source in sources
        if _age_hours(generated_at, source.observed_at) <= config.max_source_age_hours
    )
    fresh_families = tuple(sorted({source.source_family for source in fresh_sources}))
    stale_source_count = _count(len(sources) - len(fresh_sources))
    missing_source_families = tuple(
        family
        for family in config.required_source_families
        if family not in fresh_families
    )
    reason_codes = _row_reason_codes(
        missing_source_families=missing_source_families,
        stale_source_count=stale_source_count,
    )
    return StrategySourceCoverageQuorumV9Row(
        candidate_id=candidate_id,
        source_count=_count(len(sources)),
        fresh_source_count=_count(len(fresh_sources)),
        stale_source_count=stale_source_count,
        primary_source_count=_source_family_count(fresh_sources, "primary"),
        official_source_count=_source_family_count(fresh_sources, "official"),
        secondary_source_count=_source_family_count(fresh_sources, "secondary"),
        market_data_source_count=_source_family_count(fresh_sources, "market_data"),
        quorum_status=_row_status(reason_codes),
        missing_source_families=missing_source_families,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_source_families: tuple[str, ...],
    stale_source_count: Decimal,
) -> tuple[str, ...]:
    codes = [
        f"strategy_source_coverage_quorum_v9_missing_{family}"
        for family in missing_source_families
    ]
    if stale_source_count > ZERO_COUNT:
        codes.append("strategy_source_coverage_quorum_v9_stale_sources")
    if not codes:
        codes.append("strategy_source_coverage_quorum_v9_passed")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any("_missing_" in reason_code for reason_code in reason_codes):
        return "blocked"
    if "strategy_source_coverage_quorum_v9_stale_sources" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[StrategySourceCoverageQuorumV9Row, ...]) -> str:
    if any(row.quorum_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quorum_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_missing_source_families(
    rows: tuple[StrategySourceCoverageQuorumV9Row, ...],
) -> tuple[str, ...]:
    missing = {
        family
        for row in rows
        for family in row.missing_source_families
    }
    return tuple(family for family in SOURCE_FAMILIES if family in missing)


def _report_reason_codes(
    rows: tuple[StrategySourceCoverageQuorumV9Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_source_coverage_quorum_v9_clear",)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    codes: list[str] = []
    for family in SOURCE_FAMILIES:
        missing_code = f"strategy_source_coverage_quorum_v9_missing_{family}"
        if missing_code in row_codes:
            codes.append(missing_code)
    if "strategy_source_coverage_quorum_v9_stale_sources" in row_codes:
        codes.append("strategy_source_coverage_quorum_v9_stale_sources_present")
    if not codes:
        codes.append("strategy_source_coverage_quorum_v9_passed")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: StrategySourceCoverageQuorumV9Row,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.quorum_status],
        -row.stale_source_count,
        _count(len(row.missing_source_families)),
        row.candidate_id,
    )


def _candidate_groups(
    sources: tuple[StrategySourceCoverageQuorumV9Source, ...],
) -> tuple[tuple[str, tuple[StrategySourceCoverageQuorumV9Source, ...]], ...]:
    candidate_ids = tuple(dict.fromkeys(source.candidate_id for source in sources))
    return tuple(
        (
            candidate_id,
            tuple(source for source in sources if source.candidate_id == candidate_id),
        )
        for candidate_id in candidate_ids
    )


def _normalize_sources(
    sources: list[StrategySourceCoverageQuorumV9Source]
    | tuple[StrategySourceCoverageQuorumV9Source, ...],
    generated_at: datetime,
) -> tuple[StrategySourceCoverageQuorumV9Source, ...]:
    if not isinstance(sources, (list, tuple)):
        raise ValueError("sources must be a list or tuple")
    normalized: list[StrategySourceCoverageQuorumV9Source] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        if type(source) is not StrategySourceCoverageQuorumV9Source:
            raise ValueError("sources must contain StrategySourceCoverageQuorumV9Source")
        require_paper_only_flags("source", source)
        if source.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        key = (source.candidate_id, source.source_id)
        if key in seen:
            raise ValueError("duplicate source_id for candidate_id")
        seen.add(key)
        normalized.append(source)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[StrategySourceCoverageQuorumV9Row, ...],
) -> tuple[StrategySourceCoverageQuorumV9Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategySourceCoverageQuorumV9Row:
            raise ValueError("rows must contain StrategySourceCoverageQuorumV9Row")
        require_paper_only_flags("row", row)
    return rows


def _normalize_required_source_families(
    values: tuple[str, ...],
) -> tuple[str, ...]:
    families = _normalize_source_families(
        "required_source_families",
        values,
        allow_empty=False,
    )
    if len(set(families)) != len(families):
        raise ValueError("required_source_families must be unique")
    return families


def _normalize_source_families(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        _require_source_family(field_name, value)
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported value")
        if value in seen:
            raise ValueError(f"{field_name} contains duplicate value")
        seen.add(value)
    return tuple(value for value in allowed_values if value in seen)


def _normalize_positive_hours(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(HOUR_QUANTUM)
    if normalized <= ZERO_HOURS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _source_family_count(
    sources: tuple[StrategySourceCoverageQuorumV9Source, ...],
    source_family: str,
) -> Decimal:
    return _count(sum(1 for source in sources if source.source_family == source_family))


def _status_count(
    rows: tuple[StrategySourceCoverageQuorumV9Row, ...],
    quorum_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.quorum_status == quorum_status))


def _reason_count(
    rows: tuple[StrategySourceCoverageQuorumV9Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400 + delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return (seconds / SECONDS_PER_HOUR).quantize(HOUR_QUANTUM)


def _as_exact_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC timezone-aware")
    return value


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_source_family(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in SOURCE_FAMILIES:
        raise ValueError(f"{field_name} must be a supported source family")


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _validate_row(row: StrategySourceCoverageQuorumV9Row) -> None:
    if row.fresh_source_count + row.stale_source_count != row.source_count:
        raise ValueError("source_count must equal fresh plus stale sources")
    if row.quorum_status != _row_status(row.reason_codes):
        raise ValueError("quorum_status does not match reason_codes")
    if row.quorum_status == "pass" and row.missing_source_families:
        raise ValueError("missing_source_families must be empty when quorum passes")
    if row.quorum_status == "blocked" and not row.missing_source_families:
        raise ValueError("blocked rows must include missing_source_families")
    expected_missing = tuple(
        reason_code.rsplit("_missing_", maxsplit=1)[1]
        for reason_code in row.reason_codes
        if "_missing_" in reason_code
    )
    if row.missing_source_families != expected_missing:
        raise ValueError("missing_source_families must match reason_codes")


def _validate_report(report: StrategySourceCoverageQuorumV9Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.input_count != sum((row.source_count for row in report.rows), ZERO_COUNT):
        raise ValueError("input_count must match row source counts")
    if report.pass_candidate_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_candidate_count must match rows")
    if report.watch_candidate_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.stale_candidate_count != _reason_count(
        report.rows,
        "strategy_source_coverage_quorum_v9_stale_sources",
    ):
        raise ValueError("stale_candidate_count must match rows")
    if report.quorum_status != _report_status(report.rows):
        raise ValueError("quorum_status must match rows")
    if report.missing_source_families != _report_missing_source_families(report.rows):
        raise ValueError("missing_source_families must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


__all__ = (
    "DEFAULT_STRATEGY_SOURCE_COVERAGE_QUORUM_V9_CONFIG_VERSION",
    "StrategySourceCoverageQuorumV9Config",
    "StrategySourceCoverageQuorumV9Source",
    "StrategySourceCoverageQuorumV9Row",
    "StrategySourceCoverageQuorumV9Report",
    "build_strategy_source_coverage_quorum_v9",
    "strategy_source_coverage_quorum_v9_payload",
)
