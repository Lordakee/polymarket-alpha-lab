"""Phase 1 source coverage digest for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_COVERAGE_DIGEST_CONFIG_VERSION = (
    "strategy-source-coverage-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

COVERAGE_STATUSES = ("sufficient", "watch", "blocked")
INPUT_REASON_CODES = ("source_coverage_input",)
ROW_REASON_CODES = (
    "source_coverage_sources_below_minimum",
    "source_coverage_family_diversity_below_minimum",
    "source_coverage_resolution_evidence_missing",
    "source_coverage_sources_stale",
    "source_coverage_sufficient",
)
REPORT_REASON_CODES = (
    "source_coverage_digest_clear",
    "source_coverage_sources_below_minimum",
    "source_coverage_family_diversity_low",
    "source_coverage_resolution_evidence_missing",
    "source_coverage_stale_sources_present",
    "source_coverage_digest_sufficient",
)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "sufficient": Decimal("0"),
}


@dataclass(frozen=True)
class StrategyRecommendationSourceCoverageDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_COVERAGE_DIGEST_CONFIG_VERSION
    )
    min_source_count: Decimal = Decimal("3")
    min_source_family_count: Decimal = Decimal("2")
    max_source_age_hours: Decimal = Decimal("24")
    require_resolution_source_evidence: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_source_count",
            "min_source_family_count",
            "max_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if type(self.require_resolution_source_evidence) is not bool:
            raise ValueError("require_resolution_source_evidence must be a bool")
        require_paper_only_flags(
            "StrategyRecommendationSourceCoverageDigestConfig",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationSourceCoverageDigestInput:
    candidate_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    resolution_source_evidence: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("source_id", self.source_id)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.resolution_source_evidence) is not bool:
            raise ValueError("resolution_source_evidence must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        require_paper_only_flags(
            "StrategyRecommendationSourceCoverageDigestInput",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationSourceCoverageDigestRow:
    candidate_id: str
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    source_family_count: Decimal
    fresh_source_family_count: Decimal
    resolution_source_evidence_count: Decimal
    source_coverage_ratio: Decimal
    source_family_coverage_ratio: Decimal
    observed_source_families: tuple[str, ...]
    coverage_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "source_family_count",
            "fresh_source_family_count",
            "resolution_source_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_coverage_ratio",
            "source_family_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observed_source_families",
            _normalize_string_tuple(
                "observed_source_families",
                self.observed_source_families,
                allow_empty=True,
            ),
        )
        _require_member("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("StrategyRecommendationSourceCoverageDigestRow", self)


@dataclass(frozen=True)
class StrategyRecommendationSourceCoverageDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    candidate_count: Decimal
    sufficient_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    stale_candidate_count: Decimal
    missing_resolution_candidate_count: Decimal
    low_source_family_candidate_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationSourceCoverageDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "candidate_count",
            "sufficient_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "stale_candidate_count",
            "missing_resolution_candidate_count",
            "low_source_family_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ("pass", "watch", "blocked"))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("strategy source coverage digest report", self)
        require_paper_only_flags(
            "StrategyRecommendationSourceCoverageDigestReport",
            self,
        )


def build_strategy_recommendation_source_coverage_digest(
    inputs: list[StrategyRecommendationSourceCoverageDigestInput]
    | tuple[StrategyRecommendationSourceCoverageDigestInput, ...],
    *,
    config: StrategyRecommendationSourceCoverageDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationSourceCoverageDigestReport:
    if type(config) is not StrategyRecommendationSourceCoverageDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationSourceCoverageDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs, generated_at_utc)
    candidate_groups = _candidate_groups(rows)
    digest_rows = tuple(
        sorted(
            (
                _candidate_row(candidate_id, candidate_rows, config, generated_at_utc)
                for candidate_id, candidate_rows in candidate_groups
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationSourceCoverageDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        candidate_count=_count(len(digest_rows)),
        sufficient_candidate_count=_status_count(digest_rows, "sufficient"),
        watch_candidate_count=_status_count(digest_rows, "watch"),
        blocked_candidate_count=_status_count(digest_rows, "blocked"),
        stale_candidate_count=_reason_count(
            digest_rows,
            "source_coverage_sources_stale",
        ),
        missing_resolution_candidate_count=_reason_count(
            digest_rows,
            "source_coverage_resolution_evidence_missing",
        ),
        low_source_family_candidate_count=_reason_count(
            digest_rows,
            "source_coverage_family_diversity_below_minimum",
        ),
        status=_report_status(digest_rows),
        reason_codes=_report_reason_codes(digest_rows),
        rows=digest_rows,
    )


def strategy_recommendation_source_coverage_digest_payload(
    report: StrategyRecommendationSourceCoverageDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationSourceCoverageDigestReport:
        raise ValueError(
            "report must be a StrategyRecommendationSourceCoverageDigestReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy source coverage digest report", report)
    return json_ready_no_floats(report)


def _candidate_row(
    candidate_id: str,
    rows: tuple[StrategyRecommendationSourceCoverageDigestInput, ...],
    config: StrategyRecommendationSourceCoverageDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationSourceCoverageDigestRow:
    fresh_rows = tuple(
        row
        for row in rows
        if _count_age_hours(generated_at, row.observed_at) <= config.max_source_age_hours
    )
    observed_source_families = tuple(sorted({row.source_family for row in rows}))
    fresh_source_families = tuple(sorted({row.source_family for row in fresh_rows}))
    resolution_source_evidence_count = _count(
        sum(1 for row in rows if row.resolution_source_evidence),
    )
    fresh_resolution_source_evidence_count = _count(
        sum(1 for row in fresh_rows if row.resolution_source_evidence),
    )
    reason_codes = _row_reason_codes(
        fresh_source_count=_count(len(fresh_rows)),
        fresh_source_family_count=_count(len(fresh_source_families)),
        stale_source_count=_count(len(rows) - len(fresh_rows)),
        resolution_source_evidence_count=fresh_resolution_source_evidence_count,
        config=config,
    )
    return StrategyRecommendationSourceCoverageDigestRow(
        candidate_id=candidate_id,
        source_count=_count(len(rows)),
        fresh_source_count=_count(len(fresh_rows)),
        stale_source_count=_count(len(rows) - len(fresh_rows)),
        source_family_count=_count(len(observed_source_families)),
        fresh_source_family_count=_count(len(fresh_source_families)),
        resolution_source_evidence_count=resolution_source_evidence_count,
        source_coverage_ratio=_coverage_ratio(
            _count(len(fresh_rows)),
            config.min_source_count,
        ),
        source_family_coverage_ratio=_coverage_ratio(
            _count(len(fresh_source_families)),
            config.min_source_family_count,
        ),
        observed_source_families=observed_source_families,
        coverage_status=_coverage_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    fresh_source_count: Decimal,
    fresh_source_family_count: Decimal,
    stale_source_count: Decimal,
    resolution_source_evidence_count: Decimal,
    config: StrategyRecommendationSourceCoverageDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if fresh_source_count < config.min_source_count:
        codes.append("source_coverage_sources_below_minimum")
    if fresh_source_family_count < config.min_source_family_count:
        codes.append("source_coverage_family_diversity_below_minimum")
    if (
        config.require_resolution_source_evidence
        and resolution_source_evidence_count == ZERO_COUNT
    ):
        codes.append("source_coverage_resolution_evidence_missing")
    if stale_source_count > ZERO_COUNT:
        codes.append("source_coverage_sources_stale")
    if not codes:
        codes.append("source_coverage_sufficient")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _coverage_status(reason_codes: tuple[str, ...]) -> str:
    blocked_codes = {
        "source_coverage_sources_below_minimum",
        "source_coverage_family_diversity_below_minimum",
        "source_coverage_resolution_evidence_missing",
    }
    if any(reason_code in blocked_codes for reason_code in reason_codes):
        return "blocked"
    if "source_coverage_sources_stale" in reason_codes:
        return "watch"
    return "sufficient"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationSourceCoverageDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_coverage_digest_clear",)
    codes: list[str] = []
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    if "source_coverage_sources_below_minimum" in row_codes:
        codes.append("source_coverage_sources_below_minimum")
    if "source_coverage_family_diversity_below_minimum" in row_codes:
        codes.append("source_coverage_family_diversity_low")
    if "source_coverage_resolution_evidence_missing" in row_codes:
        codes.append("source_coverage_resolution_evidence_missing")
    if "source_coverage_sources_stale" in row_codes:
        codes.append("source_coverage_stale_sources_present")
    if not codes:
        codes.append("source_coverage_digest_sufficient")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status(rows: tuple[StrategyRecommendationSourceCoverageDigestRow, ...]) -> str:
    if any(row.coverage_status == "blocked" for row in rows):
        return "blocked"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: StrategyRecommendationSourceCoverageDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.coverage_status],
        -row.stale_source_count,
        -row.source_coverage_ratio,
        -row.source_family_coverage_ratio,
        row.candidate_id,
    )


def _candidate_groups(
    rows: tuple[StrategyRecommendationSourceCoverageDigestInput, ...],
) -> tuple[tuple[str, tuple[StrategyRecommendationSourceCoverageDigestInput, ...]], ...]:
    candidate_ids = tuple(dict.fromkeys(row.candidate_id for row in rows))
    return tuple(
        (
            candidate_id,
            tuple(row for row in rows if row.candidate_id == candidate_id),
        )
        for candidate_id in candidate_ids
    )


def _normalize_inputs(
    inputs: list[StrategyRecommendationSourceCoverageDigestInput]
    | tuple[StrategyRecommendationSourceCoverageDigestInput, ...],
    generated_at: datetime,
) -> tuple[StrategyRecommendationSourceCoverageDigestInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationSourceCoverageDigestInput:
            raise ValueError(
                "inputs must contain StrategyRecommendationSourceCoverageDigestInput values",
            )
        require_paper_only_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.candidate_id, row.source_id)
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate candidate source values")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyRecommendationSourceCoverageDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not StrategyRecommendationSourceCoverageDigestRow:
            raise ValueError(
                "rows must contain StrategyRecommendationSourceCoverageDigestRow values",
            )
        require_paper_only_flags("row", row)
    return rows


def _validate_row(row: StrategyRecommendationSourceCoverageDigestRow) -> None:
    if row.fresh_source_count + row.stale_source_count != row.source_count:
        raise ValueError("source_count must match fresh and stale source counts")
    if row.fresh_source_family_count > row.source_family_count:
        raise ValueError("fresh_source_family_count must not exceed source_family_count")
    if row.resolution_source_evidence_count > row.source_count:
        raise ValueError("resolution_source_evidence_count must not exceed source_count")
    if row.source_family_count != _count(len(row.observed_source_families)):
        raise ValueError("source_family_count must match observed_source_families")
    if row.coverage_status != _coverage_status(row.reason_codes):
        raise ValueError("coverage_status must match reason_codes")


def _validate_report(report: StrategyRecommendationSourceCoverageDigestReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.sufficient_candidate_count != _status_count(report.rows, "sufficient"):
        raise ValueError("sufficient_candidate_count must match rows")
    if report.watch_candidate_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.stale_candidate_count != _reason_count(
        report.rows,
        "source_coverage_sources_stale",
    ):
        raise ValueError("stale_candidate_count must match rows")
    if report.missing_resolution_candidate_count != _reason_count(
        report.rows,
        "source_coverage_resolution_evidence_missing",
    ):
        raise ValueError("missing_resolution_candidate_count must match rows")
    if report.low_source_family_candidate_count != _reason_count(
        report.rows,
        "source_coverage_family_diversity_below_minimum",
    ):
        raise ValueError("low_source_family_candidate_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sort")


def _status_count(
    rows: tuple[StrategyRecommendationSourceCoverageDigestRow, ...],
    coverage_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.coverage_status == coverage_status))


def _reason_count(
    rows: tuple[StrategyRecommendationSourceCoverageDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator >= denominator:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("coverage_ratio", numerator / denominator)


def _count_age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal("1000000")
        )
        return (age_seconds / Decimal("3600")).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(items)) != items:
        raise ValueError(f"{field_name} must be sorted")
    return items


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe surface text")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_COVERAGE_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationSourceCoverageDigestConfig",
    "StrategyRecommendationSourceCoverageDigestInput",
    "StrategyRecommendationSourceCoverageDigestReport",
    "StrategyRecommendationSourceCoverageDigestRow",
    "build_strategy_recommendation_source_coverage_digest",
    "strategy_recommendation_source_coverage_digest_payload",
)
