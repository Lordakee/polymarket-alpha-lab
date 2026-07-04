"""Pure paper-only recommendation evidence freshness digest reports.

This module reduces caller-supplied recommendation candidate evidence into a
deterministic in-memory report. It performs no file IO, network access,
privileged handling, custody handling, placement actions, execution, or advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


__all__ = (
    "StrategyRecommendationEvidenceCandidate",
    "StrategyRecommendationEvidenceFreshnessDigestConfig",
    "StrategyRecommendationEvidenceFreshnessDigestReport",
    "StrategyRecommendationEvidenceFreshnessDigestRollup",
    "StrategyRecommendationEvidenceFreshnessDigestRow",
    "StrategyRecommendationEvidenceSource",
    "build_strategy_recommendation_evidence_freshness_digest",
    "strategy_recommendation_evidence_freshness_digest_payload",
)


ROW_STATUSES = ("pass", "watch", "blocked")
ROLLUP_STATUSES = ROW_STATUSES
REPORT_STATUSES = ROW_STATUSES
MARKET_CLOSE_PRESSURES = ("none", "watch", "closed")
SEVERITY_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
REASON_WEIGHT = {
    "no_recommendation_candidates": 0,
    "missing_evidence_family": 10,
    "market_already_closed": 20,
    "stale_required_evidence": 30,
    "stale_resolution_evidence": 40,
    "market_close_pressure": 50,
    "evidence_fresh": 90,
}


@dataclass(frozen=True)
class StrategyRecommendationEvidenceSource:
    family: str
    source_id: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("family", self.family)
        _require_canonical_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc(self.observed_at, field_name="observed_at"),
        )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceCandidate:
    candidate_id: str
    market_slug: str
    market_close_at: datetime
    evidence: tuple[StrategyRecommendationEvidenceSource, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc(self.market_close_at, field_name="market_close_at"),
        )
        object.__setattr__(self, "evidence", _normalize_sources(self.evidence))
        _validate_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceFreshnessDigestConfig:
    config_version: str
    required_source_families: tuple[str, ...]
    resolution_source_families: tuple[str, ...]
    max_evidence_age_seconds: Decimal
    max_resolution_evidence_age_seconds: Decimal
    close_pressure_window_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_family_tuple(
                "required_source_families",
                self.required_source_families,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "resolution_source_families",
            _normalize_family_tuple(
                "resolution_source_families",
                self.resolution_source_families,
                allow_empty=True,
            ),
        )
        _require_nonnegative_decimal(
            "max_evidence_age_seconds",
            self.max_evidence_age_seconds,
        )
        _require_nonnegative_decimal(
            "max_resolution_evidence_age_seconds",
            self.max_resolution_evidence_age_seconds,
        )
        _require_nonnegative_decimal(
            "close_pressure_window_seconds",
            self.close_pressure_window_seconds,
        )
        missing_resolution_families = (
            set(self.resolution_source_families) - set(self.required_source_families)
        )
        if missing_resolution_families:
            raise ValueError(
                "resolution_source_families must be included in "
                "required_source_families",
            )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceFreshnessDigestRow:
    candidate_id: str
    market_slug: str
    market_close_at: datetime
    newest_evidence_at: datetime | None
    newest_evidence_age_seconds: Decimal | None
    oldest_required_source_age_seconds: Decimal | None
    seconds_until_market_close: Decimal
    market_close_pressure: str
    evidence_count: Decimal
    evidence_family_count: Decimal
    required_family_count: Decimal
    missing_family_count: Decimal
    stale_resolution_family_count: Decimal
    missing_evidence_families: tuple[str, ...]
    stale_resolution_evidence_families: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc(self.market_close_at, field_name="market_close_at"),
        )
        object.__setattr__(
            self,
            "newest_evidence_at",
            _as_optional_utc(
                self.newest_evidence_at,
                field_name="newest_evidence_at",
            ),
        )
        _require_optional_nonnegative_decimal(
            "newest_evidence_age_seconds",
            self.newest_evidence_age_seconds,
        )
        _require_optional_nonnegative_decimal(
            "oldest_required_source_age_seconds",
            self.oldest_required_source_age_seconds,
        )
        _require_decimal("seconds_until_market_close", self.seconds_until_market_close)
        _require_nonnegative_decimal("evidence_count", self.evidence_count)
        _require_nonnegative_decimal("evidence_family_count", self.evidence_family_count)
        _require_nonnegative_decimal("required_family_count", self.required_family_count)
        _require_nonnegative_decimal("missing_family_count", self.missing_family_count)
        _require_nonnegative_decimal(
            "stale_resolution_family_count",
            self.stale_resolution_family_count,
        )
        if (
            type(self.market_close_pressure) is not str
            or self.market_close_pressure not in MARKET_CLOSE_PRESSURES
        ):
            raise ValueError("market_close_pressure must be a known pressure status")
        object.__setattr__(
            self,
            "missing_evidence_families",
            _normalize_family_tuple(
                "missing_evidence_families",
                self.missing_evidence_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "stale_resolution_evidence_families",
            _normalize_family_tuple(
                "stale_resolution_evidence_families",
                self.stale_resolution_evidence_families,
                allow_empty=True,
            ),
        )
        _require_status("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceFreshnessDigestRollup:
    family: str
    candidate_count: Decimal
    present_count: Decimal
    missing_count: Decimal
    stale_required_count: Decimal
    stale_resolution_count: Decimal
    newest_evidence_age_seconds: Decimal | None
    oldest_evidence_age_seconds: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("family", self.family)
        _require_nonnegative_decimal("candidate_count", self.candidate_count)
        _require_nonnegative_decimal("present_count", self.present_count)
        _require_nonnegative_decimal("missing_count", self.missing_count)
        _require_nonnegative_decimal("stale_required_count", self.stale_required_count)
        _require_nonnegative_decimal(
            "stale_resolution_count",
            self.stale_resolution_count,
        )
        _require_optional_nonnegative_decimal(
            "newest_evidence_age_seconds",
            self.newest_evidence_age_seconds,
        )
        _require_optional_nonnegative_decimal(
            "oldest_evidence_age_seconds",
            self.oldest_evidence_age_seconds,
        )
        _require_status("status", self.status, ROLLUP_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceFreshnessDigestReport:
    generated_at: datetime
    config_version: str
    required_source_families: tuple[str, ...]
    resolution_source_families: tuple[str, ...]
    max_evidence_age_seconds: Decimal
    max_resolution_evidence_age_seconds: Decimal
    close_pressure_window_seconds: Decimal
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_family_count: Decimal
    stale_resolution_candidate_count: Decimal
    close_pressure_candidate_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...]
    rollups: tuple[StrategyRecommendationEvidenceFreshnessDigestRollup, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc(self.generated_at, field_name="generated_at"),
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_family_tuple(
                "required_source_families",
                self.required_source_families,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "resolution_source_families",
            _normalize_family_tuple(
                "resolution_source_families",
                self.resolution_source_families,
                allow_empty=True,
            ),
        )
        _require_nonnegative_decimal(
            "max_evidence_age_seconds",
            self.max_evidence_age_seconds,
        )
        _require_nonnegative_decimal(
            "max_resolution_evidence_age_seconds",
            self.max_resolution_evidence_age_seconds,
        )
        _require_nonnegative_decimal(
            "close_pressure_window_seconds",
            self.close_pressure_window_seconds,
        )
        _require_nonnegative_decimal("candidate_count", self.candidate_count)
        _require_nonnegative_decimal("pass_count", self.pass_count)
        _require_nonnegative_decimal("watch_count", self.watch_count)
        _require_nonnegative_decimal("blocked_count", self.blocked_count)
        _require_nonnegative_decimal("missing_family_count", self.missing_family_count)
        _require_nonnegative_decimal(
            "stale_resolution_candidate_count",
            self.stale_resolution_candidate_count,
        )
        _require_nonnegative_decimal(
            "close_pressure_candidate_count",
            self.close_pressure_candidate_count,
        )
        _require_status("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "rollups", _normalize_rollups(self.rollups))
        _validate_hard_flags(self)


def build_strategy_recommendation_evidence_freshness_digest(
    candidates: tuple[StrategyRecommendationEvidenceCandidate, ...]
    | list[StrategyRecommendationEvidenceCandidate],
    *,
    config: StrategyRecommendationEvidenceFreshnessDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationEvidenceFreshnessDigestReport:
    if type(config) is not StrategyRecommendationEvidenceFreshnessDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationEvidenceFreshnessDigestConfig",
        )
    generated_at_utc = _as_utc(generated_at, field_name="generated_at")
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in source_candidates
            ),
            key=_row_sort_key,
        ),
    )
    rollups = _build_rollups(
        rows,
        candidates=source_candidates,
        generated_at=generated_at_utc,
        required_source_families=config.required_source_families,
        resolution_source_families=config.resolution_source_families,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
    )
    status = _report_status(rows)
    return StrategyRecommendationEvidenceFreshnessDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        required_source_families=config.required_source_families,
        resolution_source_families=config.resolution_source_families,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
        max_resolution_evidence_age_seconds=config.max_resolution_evidence_age_seconds,
        close_pressure_window_seconds=config.close_pressure_window_seconds,
        candidate_count=Decimal(len(source_candidates)),
        pass_count=_count_rows_with_status(rows, "pass"),
        watch_count=_count_rows_with_status(rows, "watch"),
        blocked_count=_count_rows_with_status(rows, "blocked"),
        missing_family_count=sum(
            (row.missing_family_count for row in rows),
            Decimal(0),
        ),
        stale_resolution_candidate_count=Decimal(
            sum(1 for row in rows if row.stale_resolution_family_count > Decimal(0)),
        ),
        close_pressure_candidate_count=Decimal(
            sum(1 for row in rows if row.market_close_pressure != "none"),
        ),
        status=status,
        reason_codes=_report_reason_codes(rows, status=status),
        rows=rows,
        rollups=rollups,
    )


def strategy_recommendation_evidence_freshness_digest_payload(
    report: StrategyRecommendationEvidenceFreshnessDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationEvidenceFreshnessDigestReport:
        raise ValueError(
            "report must be a StrategyRecommendationEvidenceFreshnessDigestReport",
        )
    _validate_hard_flags(report)
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "required_source_families": list(report.required_source_families),
        "resolution_source_families": list(report.resolution_source_families),
        "max_evidence_age_seconds": _decimal_payload(
            report.max_evidence_age_seconds,
        ),
        "max_resolution_evidence_age_seconds": _decimal_payload(
            report.max_resolution_evidence_age_seconds,
        ),
        "close_pressure_window_seconds": _decimal_payload(
            report.close_pressure_window_seconds,
        ),
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "missing_family_count": _decimal_payload(report.missing_family_count),
        "stale_resolution_candidate_count": _decimal_payload(
            report.stale_resolution_candidate_count,
        ),
        "close_pressure_candidate_count": _decimal_payload(
            report.close_pressure_candidate_count,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "rollups": [_rollup_payload(rollup) for rollup in report.rollups],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: StrategyRecommendationEvidenceCandidate,
    *,
    config: StrategyRecommendationEvidenceFreshnessDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationEvidenceFreshnessDigestRow:
    family_ages = _newest_age_by_family(candidate.evidence, generated_at=generated_at)
    missing_families = tuple(
        family
        for family in config.required_source_families
        if family not in family_ages
    )
    required_ages = tuple(
        family_ages[family]
        for family in config.required_source_families
        if family in family_ages
    )
    newest_age = min(family_ages.values()) if family_ages else None
    newest_at = max((source.observed_at for source in candidate.evidence), default=None)
    oldest_required_age = max(required_ages) if required_ages else None
    stale_resolution_families = tuple(
        family
        for family in config.resolution_source_families
        if family in family_ages
        and family_ages[family] > config.max_resolution_evidence_age_seconds
    )
    seconds_until_market_close = _seconds_between(
        generated_at,
        candidate.market_close_at,
    )
    pressure = _market_close_pressure(
        seconds_until_market_close,
        close_pressure_window_seconds=config.close_pressure_window_seconds,
    )
    reason_codes = _row_reason_codes(
        missing_families=missing_families,
        oldest_required_age=oldest_required_age,
        stale_resolution_families=stale_resolution_families,
        market_close_pressure=pressure,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
    )
    status = _status_from_reason_codes(reason_codes)
    return StrategyRecommendationEvidenceFreshnessDigestRow(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        market_close_at=candidate.market_close_at,
        newest_evidence_at=newest_at,
        newest_evidence_age_seconds=newest_age,
        oldest_required_source_age_seconds=oldest_required_age,
        seconds_until_market_close=seconds_until_market_close,
        market_close_pressure=pressure,
        evidence_count=Decimal(len(candidate.evidence)),
        evidence_family_count=Decimal(len(family_ages)),
        required_family_count=Decimal(len(config.required_source_families)),
        missing_family_count=Decimal(len(missing_families)),
        stale_resolution_family_count=Decimal(len(stale_resolution_families)),
        missing_evidence_families=missing_families,
        stale_resolution_evidence_families=stale_resolution_families,
        status=status,
        reason_codes=reason_codes,
    )


def _build_rollups(
    rows: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...],
    *,
    candidates: tuple[StrategyRecommendationEvidenceCandidate, ...],
    generated_at: datetime,
    required_source_families: tuple[str, ...],
    resolution_source_families: tuple[str, ...],
    max_evidence_age_seconds: Decimal,
) -> tuple[StrategyRecommendationEvidenceFreshnessDigestRollup, ...]:
    family_ages_by_candidate_id = {
        candidate.candidate_id: _newest_age_by_family(
            candidate.evidence,
            generated_at=generated_at,
        )
        for candidate in candidates
    }
    rollups = tuple(
        _rollup_from_rows(
            family,
            rows,
            family_ages_by_candidate_id=family_ages_by_candidate_id,
            is_resolution_family=family in resolution_source_families,
            max_evidence_age_seconds=max_evidence_age_seconds,
        )
        for family in required_source_families
    )
    if not rows:
        return ()
    return tuple(sorted(rollups, key=_rollup_sort_key))


def _rollup_from_rows(
    family: str,
    rows: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...],
    *,
    family_ages_by_candidate_id: dict[str, dict[str, Decimal]],
    is_resolution_family: bool,
    max_evidence_age_seconds: Decimal,
) -> StrategyRecommendationEvidenceFreshnessDigestRollup:
    candidate_count = Decimal(len(rows))
    missing_count = Decimal(
        sum(1 for row in rows if family in row.missing_evidence_families),
    )
    present_count = candidate_count - missing_count
    ages = tuple(
        family_ages_by_candidate_id[row.candidate_id].get(family)
        for row in rows
        if family not in row.missing_evidence_families
    )
    stale_required_count = Decimal(
        sum(1 for age in ages if age is not None and age > max_evidence_age_seconds),
    )
    stale_resolution_count = Decimal(
        sum(1 for row in rows if family in row.stale_resolution_evidence_families),
    )
    reason_codes = _rollup_reason_codes(
        missing_count=missing_count,
        stale_required_count=stale_required_count,
        stale_resolution_count=stale_resolution_count,
        is_resolution_family=is_resolution_family,
    )
    return StrategyRecommendationEvidenceFreshnessDigestRollup(
        family=family,
        candidate_count=candidate_count,
        present_count=present_count,
        missing_count=missing_count,
        stale_required_count=stale_required_count,
        stale_resolution_count=stale_resolution_count,
        newest_evidence_age_seconds=(
            min(age for age in ages if age is not None) if ages else None
        ),
        oldest_evidence_age_seconds=(
            max(age for age in ages if age is not None) if ages else None
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _newest_age_by_family(
    sources: tuple[StrategyRecommendationEvidenceSource, ...],
    *,
    generated_at: datetime,
) -> dict[str, Decimal]:
    ages: dict[str, Decimal] = {}
    for source in sources:
        if source.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        age = _seconds_between(source.observed_at, generated_at)
        previous_age = ages.get(source.family)
        if previous_age is None or age < previous_age:
            ages[source.family] = age
    return ages


def _row_reason_codes(
    *,
    missing_families: tuple[str, ...],
    oldest_required_age: Decimal | None,
    stale_resolution_families: tuple[str, ...],
    market_close_pressure: str,
    max_evidence_age_seconds: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_families:
        codes.append("missing_evidence_family")
    if market_close_pressure == "closed":
        codes.append("market_already_closed")
    if (
        oldest_required_age is not None
        and oldest_required_age > max_evidence_age_seconds
    ):
        codes.append("stale_required_evidence")
    if stale_resolution_families:
        codes.append("stale_resolution_evidence")
    if market_close_pressure == "watch":
        codes.append("market_close_pressure")
    if not codes:
        codes.append("evidence_fresh")
    return _sort_reason_codes(codes)


def _rollup_reason_codes(
    *,
    missing_count: Decimal,
    stale_required_count: Decimal,
    stale_resolution_count: Decimal,
    is_resolution_family: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_count > Decimal(0):
        codes.append("missing_evidence_family")
    if stale_required_count > Decimal(0):
        codes.append("stale_required_evidence")
    if is_resolution_family and stale_resolution_count > Decimal(0):
        codes.append("stale_resolution_evidence")
    if not codes:
        codes.append("evidence_fresh")
    return _sort_reason_codes(codes)


def _report_reason_codes(
    rows: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("no_recommendation_candidates",)
    codes = tuple(
        code
        for row in rows
        for code in row.reason_codes
        if code != "evidence_fresh"
    )
    if not codes and status == "pass":
        return ("evidence_fresh",)
    return _sort_reason_codes(codes)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "missing_evidence_family" in reason_codes:
        return "blocked"
    if "market_already_closed" in reason_codes:
        return "blocked"
    if reason_codes == ("evidence_fresh",):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _market_close_pressure(
    seconds_until_market_close: Decimal,
    *,
    close_pressure_window_seconds: Decimal,
) -> str:
    if seconds_until_market_close < Decimal(0):
        return "closed"
    if seconds_until_market_close <= close_pressure_window_seconds:
        return "watch"
    return "none"


def _count_rows_with_status(
    rows: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status))


def _row_sort_key(
    row: StrategyRecommendationEvidenceFreshnessDigestRow,
) -> tuple[int, str]:
    return (SEVERITY_WEIGHT[row.status], row.market_slug)


def _rollup_sort_key(
    rollup: StrategyRecommendationEvidenceFreshnessDigestRollup,
) -> tuple[int, str]:
    return (SEVERITY_WEIGHT[rollup.status], rollup.family)


def _sort_reason_codes(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            set(values),
            key=lambda value: (REASON_WEIGHT.get(value, 1_000), value),
        ),
    )


def _row_payload(
    row: StrategyRecommendationEvidenceFreshnessDigestRow,
) -> dict[str, Any]:
    return {
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "market_close_at": _datetime_payload(row.market_close_at),
        "newest_evidence_at": _optional_datetime_payload(row.newest_evidence_at),
        "newest_evidence_age_seconds": _optional_decimal_payload(
            row.newest_evidence_age_seconds,
        ),
        "oldest_required_source_age_seconds": _optional_decimal_payload(
            row.oldest_required_source_age_seconds,
        ),
        "seconds_until_market_close": _decimal_payload(
            row.seconds_until_market_close,
        ),
        "market_close_pressure": row.market_close_pressure,
        "evidence_count": _decimal_payload(row.evidence_count),
        "evidence_family_count": _decimal_payload(row.evidence_family_count),
        "required_family_count": _decimal_payload(row.required_family_count),
        "missing_family_count": _decimal_payload(row.missing_family_count),
        "stale_resolution_family_count": _decimal_payload(
            row.stale_resolution_family_count,
        ),
        "missing_evidence_families": list(row.missing_evidence_families),
        "stale_resolution_evidence_families": list(
            row.stale_resolution_evidence_families,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _rollup_payload(
    rollup: StrategyRecommendationEvidenceFreshnessDigestRollup,
) -> dict[str, Any]:
    return {
        "family": rollup.family,
        "candidate_count": _decimal_payload(rollup.candidate_count),
        "present_count": _decimal_payload(rollup.present_count),
        "missing_count": _decimal_payload(rollup.missing_count),
        "stale_required_count": _decimal_payload(rollup.stale_required_count),
        "stale_resolution_count": _decimal_payload(rollup.stale_resolution_count),
        "newest_evidence_age_seconds": _optional_decimal_payload(
            rollup.newest_evidence_age_seconds,
        ),
        "oldest_evidence_age_seconds": _optional_decimal_payload(
            rollup.oldest_evidence_age_seconds,
        ),
        "status": rollup.status,
        "reason_codes": list(rollup.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _datetime_payload(value: datetime) -> str:
    return value.isoformat()


def _optional_datetime_payload(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_payload(value)


def _decimal_payload(value: Decimal) -> str:
    return str(value)


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_payload(value)


def _normalize_sources(
    values: tuple[StrategyRecommendationEvidenceSource, ...],
) -> tuple[StrategyRecommendationEvidenceSource, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("evidence must be an iterable of sources")
    try:
        sources = tuple(values)
    except TypeError as exc:
        raise ValueError("evidence must be an iterable of sources") from exc
    for source in sources:
        if type(source) is not StrategyRecommendationEvidenceSource:
            raise ValueError(
                "evidence must contain StrategyRecommendationEvidenceSource values",
            )
        _require_safety_object("evidence source", source)
    return sources


def _normalize_candidates(
    values: tuple[StrategyRecommendationEvidenceCandidate, ...]
    | list[StrategyRecommendationEvidenceCandidate],
) -> tuple[StrategyRecommendationEvidenceCandidate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("candidates must be an iterable of candidates")
    try:
        candidates = tuple(values)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of candidates") from exc
    for candidate in candidates:
        if type(candidate) is not StrategyRecommendationEvidenceCandidate:
            raise ValueError(
                "candidates must contain StrategyRecommendationEvidenceCandidate values",
            )
        _require_safety_object("candidate", candidate)
    return candidates


def _normalize_rows(
    values: tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...],
) -> tuple[StrategyRecommendationEvidenceFreshnessDigestRow, ...]:
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of rows") from exc
    for row in rows:
        if type(row) is not StrategyRecommendationEvidenceFreshnessDigestRow:
            raise ValueError(
                "rows must contain StrategyRecommendationEvidenceFreshnessDigestRow "
                "values",
            )
        _require_safety_object("row", row)
    return rows


def _normalize_rollups(
    values: tuple[StrategyRecommendationEvidenceFreshnessDigestRollup, ...],
) -> tuple[StrategyRecommendationEvidenceFreshnessDigestRollup, ...]:
    try:
        rollups = tuple(values)
    except TypeError as exc:
        raise ValueError("rollups must be an iterable of rollups") from exc
    for rollup in rollups:
        if type(rollup) is not StrategyRecommendationEvidenceFreshnessDigestRollup:
            raise ValueError(
                "rollups must contain StrategyRecommendationEvidenceFreshnessDigestRollup "
                "values",
            )
        _require_safety_object("rollup", rollup)
    return rollups


def _normalize_family_tuple(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return _sort_reason_codes(items)


def _require_status(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known digest status")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty trimmed string")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < Decimal(0):
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _as_utc(value: datetime, *, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value


def _as_optional_utc(value: datetime | None, *, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value, field_name=field_name)


def _seconds_between(start_at: datetime, end_at: datetime) -> Decimal:
    delta = end_at - start_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _require_safety_object(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _validate_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")
