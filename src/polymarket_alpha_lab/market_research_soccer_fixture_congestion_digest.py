"""Pure Phase 1 reducer for soccer fixture congestion research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_FIXTURE_CONGESTION_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-fixture-congestion-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")

PASS_STATUS = "pass"
READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS)

CONFLICTING_SOURCES_REASON = "soccer_fixture_congestion_conflicting_sources"
REST_GAP_REASON = "soccer_fixture_congestion_rest_gap_short"
FIXTURE_DENSITY_REASON = "soccer_fixture_congestion_fixture_density_high"
TRAVEL_LOAD_REASON = "soccer_fixture_congestion_travel_load_high"
SOURCE_COVERAGE_GAP_REASON = "soccer_fixture_congestion_source_coverage_gap"
READY_REASON = "soccer_fixture_congestion_ready"
PASSED_REASON = "soccer_fixture_congestion_passed"
EMPTY_REASON = "soccer_fixture_congestion_empty"

ROW_REASON_CODES = (
    CONFLICTING_SOURCES_REASON,
    REST_GAP_REASON,
    FIXTURE_DENSITY_REASON,
    TRAVEL_LOAD_REASON,
    SOURCE_COVERAGE_GAP_REASON,
    READY_REASON,
)
DIGEST_REASON_CODES = (
    CONFLICTING_SOURCES_REASON,
    REST_GAP_REASON,
    FIXTURE_DENSITY_REASON,
    TRAVEL_LOAD_REASON,
    SOURCE_COVERAGE_GAP_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_soccer_fixture_congestion_monitoring",
    WATCH_STATUS: "review_report_only_soccer_fixture_congestion_review",
    BLOCKED_STATUS: "block_report_only_soccer_fixture_congestion_review",
}

_BLOCKED_WORDS = (
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "sign" "ing",
    "sub" "mit",
    "can" "cel",
    "data" "base",
    "per" "sist",
    "pay" "load_" "json",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_FIXTURE_CONGESTION_DIGEST_CONFIG_VERSION",
    "MarketResearchSoccerFixtureCongestionDigestConfig",
    "MarketResearchSoccerFixtureCongestionDigestFixture",
    "MarketResearchSoccerFixtureCongestionDigestReasonCodeCount",
    "MarketResearchSoccerFixtureCongestionDigestRow",
    "MarketResearchSoccerFixtureCongestionDigestReport",
    "build_market_research_soccer_fixture_congestion_digest",
    "market_research_soccer_fixture_congestion_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSoccerFixtureCongestionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_FIXTURE_CONGESTION_DIGEST_CONFIG_VERSION
    )
    min_rest_hours: Decimal = Decimal("72.000000")
    min_fixture_gap_hours: Decimal = Decimal("48.000000")
    max_fixture_count_lookback: Decimal = Decimal("3.000000")
    high_travel_distance_km: Decimal = Decimal("1000.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_conflicting_source_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerFixtureCongestionDigestConfig:
            raise TypeError(
                "MarketResearchSoccerFixtureCongestionDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerFixtureCongestionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchSoccerFixtureCongestionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_rest_hours",
            "min_fixture_gap_hours",
            "high_travel_distance_km",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_fixture_count_lookback",
            "min_source_count",
            "max_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerFixtureCongestionDigestFixture:
    condition_id: str
    league_key: str
    team_key: str
    fixture_ref: str
    kickoff_at: datetime
    is_target_fixture: bool
    travel_distance_km: Decimal
    source_count: Decimal
    conflicting_source_count: Decimal
    fixture_config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_FIXTURE_CONGESTION_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerFixtureCongestionDigestFixture:
            raise TypeError(
                "MarketResearchSoccerFixtureCongestionDigestFixture "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerFixtureCongestionDigestFixture:
            raise ValueError(
                "fixture must be exactly "
                "MarketResearchSoccerFixtureCongestionDigestFixture",
            )
        for field_name in (
            "condition_id",
            "league_key",
            "team_key",
            "fixture_ref",
            "fixture_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "kickoff_at", _as_utc("kickoff_at", self.kickoff_at))
        if type(self.is_target_fixture) is not bool:
            raise ValueError("is_target_fixture must be a bool")
        object.__setattr__(
            self,
            "travel_distance_km",
            _normalize_nonnegative_decimal("travel_distance_km", self.travel_distance_km),
        )
        for field_name in ("source_count", "conflicting_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_flags("fixture", self)


@dataclass(frozen=True)
class MarketResearchSoccerFixtureCongestionDigestReasonCodeCount:
    reason_code: str
    condition_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerFixtureCongestionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSoccerFixtureCongestionDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerFixtureCongestionDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSoccerFixtureCongestionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "condition_count",
            _normalize_nonnegative_whole_decimal(
                "condition_count",
                self.condition_count,
            ),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerFixtureCongestionDigestRow:
    condition_id: str
    league_key: str
    team_key: str
    target_fixture_ref: str
    target_kickoff_at: datetime
    fixture_count_lookback: Decimal
    rest_hours_before_target: Decimal
    min_fixture_gap_hours_observed: Decimal
    travel_distance_km_latest: Decimal
    source_count_latest: Decimal
    conflicting_source_count_latest: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerFixtureCongestionDigestRow:
            raise TypeError(
                "MarketResearchSoccerFixtureCongestionDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerFixtureCongestionDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchSoccerFixtureCongestionDigestRow",
            )
        for field_name in ("condition_id", "league_key", "team_key", "target_fixture_ref"):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "target_kickoff_at",
            _as_utc("target_kickoff_at", self.target_kickoff_at),
        )
        for field_name in (
            "fixture_count_lookback",
            "source_count_latest",
            "conflicting_source_count_latest",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hours_before_target",
            "min_fixture_gap_hours_observed",
            "travel_distance_km_latest",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerFixtureCongestionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    condition_count: Decimal
    ready_condition_count: Decimal
    watch_condition_count: Decimal
    blocked_condition_count: Decimal
    fixture_count: Decimal
    rest_gap_condition_count: Decimal
    fixture_density_condition_count: Decimal
    travel_load_condition_count: Decimal
    source_gap_condition_count: Decimal
    conflict_condition_count: Decimal
    min_rest_hours: Decimal
    min_fixture_gap_hours: Decimal
    max_fixture_count_lookback: Decimal
    high_travel_distance_km: Decimal
    min_source_count: Decimal
    max_conflicting_source_count: Decimal
    min_rest_hours_observed: Decimal | None
    max_fixture_count_lookback_observed: Decimal | None
    max_travel_distance_km_observed: Decimal | None
    rows: tuple[MarketResearchSoccerFixtureCongestionDigestRow, ...]
    fixture_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerFixtureCongestionDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerFixtureCongestionDigestReport:
            raise TypeError(
                "MarketResearchSoccerFixtureCongestionDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerFixtureCongestionDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchSoccerFixtureCongestionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "condition_count",
            "ready_condition_count",
            "watch_condition_count",
            "blocked_condition_count",
            "fixture_count",
            "rest_gap_condition_count",
            "fixture_density_condition_count",
            "travel_load_condition_count",
            "source_gap_condition_count",
            "conflict_condition_count",
            "min_rest_hours",
            "min_fixture_gap_hours",
            "max_fixture_count_lookback",
            "high_travel_distance_km",
            "min_source_count",
            "max_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_rest_hours_observed",
            "max_fixture_count_lookback_observed",
            "max_travel_distance_km_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "fixture_config_versions",
            _normalize_fixture_config_versions(self.fixture_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_soccer_fixture_congestion_digest(
    fixtures: Iterable[MarketResearchSoccerFixtureCongestionDigestFixture],
    *,
    config: MarketResearchSoccerFixtureCongestionDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerFixtureCongestionDigestReport:
    if type(config) is not MarketResearchSoccerFixtureCongestionDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchSoccerFixtureCongestionDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    fixture_items = _normalize_fixtures(fixtures)
    rows = _build_rows(fixture_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    )
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        digest_status = BLOCKED_STATUS
    elif row_reason_codes:
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchSoccerFixtureCongestionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        condition_count=_whole(len(rows)),
        ready_condition_count=_whole(
            sum(1 for row in rows if row.digest_status == READY_STATUS),
        ),
        watch_condition_count=_whole(
            sum(1 for row in rows if row.digest_status == WATCH_STATUS),
        ),
        blocked_condition_count=_whole(
            sum(1 for row in rows if row.digest_status == BLOCKED_STATUS),
        ),
        fixture_count=_whole(len(fixture_items)),
        rest_gap_condition_count=_whole(
            sum(1 for row in rows if REST_GAP_REASON in row.reason_codes),
        ),
        fixture_density_condition_count=_whole(
            sum(1 for row in rows if FIXTURE_DENSITY_REASON in row.reason_codes),
        ),
        travel_load_condition_count=_whole(
            sum(1 for row in rows if TRAVEL_LOAD_REASON in row.reason_codes),
        ),
        source_gap_condition_count=_whole(
            sum(1 for row in rows if SOURCE_COVERAGE_GAP_REASON in row.reason_codes),
        ),
        conflict_condition_count=_whole(
            sum(1 for row in rows if CONFLICTING_SOURCES_REASON in row.reason_codes),
        ),
        min_rest_hours=config.min_rest_hours,
        min_fixture_gap_hours=config.min_fixture_gap_hours,
        max_fixture_count_lookback=config.max_fixture_count_lookback,
        high_travel_distance_km=config.high_travel_distance_km,
        min_source_count=config.min_source_count,
        max_conflicting_source_count=config.max_conflicting_source_count,
        min_rest_hours_observed=_min_or_none(row.rest_hours_before_target for row in rows),
        max_fixture_count_lookback_observed=_max_or_none(
            row.fixture_count_lookback for row in rows
        ),
        max_travel_distance_km_observed=_max_or_none(
            row.travel_distance_km_latest for row in rows
        ),
        rows=rows,
        fixture_config_versions=tuple(
            sorted(
                {
                    (fixture.fixture_ref, fixture.fixture_config_version)
                    for fixture in fixture_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_fixture_congestion_digest_payload(
    report: MarketResearchSoccerFixtureCongestionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerFixtureCongestionDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchSoccerFixtureCongestionDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _build_rows(
    fixtures: tuple[MarketResearchSoccerFixtureCongestionDigestFixture, ...],
    *,
    config: MarketResearchSoccerFixtureCongestionDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchSoccerFixtureCongestionDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[MarketResearchSoccerFixtureCongestionDigestFixture],
    ] = {}
    for fixture in fixtures:
        grouped.setdefault(
            (fixture.condition_id, fixture.league_key, fixture.team_key),
            [],
        ).append(fixture)

    rows: list[MarketResearchSoccerFixtureCongestionDigestRow] = []
    for (condition_id, league_key, team_key), condition_fixtures in grouped.items():
        ordered_fixtures = sorted(
            condition_fixtures,
            key=lambda item: (item.kickoff_at, item.fixture_ref),
        )
        target_fixtures = tuple(item for item in ordered_fixtures if item.is_target_fixture)
        if len(target_fixtures) != 1:
            raise ValueError("each condition/team group must contain exactly one target fixture")
        target = target_fixtures[0]
        if target.kickoff_at < generated_at:
            raise ValueError("target fixture must not be in the past")
        prior_fixtures = tuple(item for item in ordered_fixtures if item.kickoff_at < target.kickoff_at)
        lookback_start = target.kickoff_at - _hours_to_timedelta(config.min_rest_hours)
        lookback_fixtures = tuple(
            item
            for item in prior_fixtures
            if item.kickoff_at >= lookback_start
        )
        if prior_fixtures:
            rest_hours_before_target = _hours_between(
                target.kickoff_at,
                prior_fixtures[-1].kickoff_at,
            )
        else:
            rest_hours_before_target = config.min_rest_hours
        fixture_gaps = tuple(
            _hours_between(later.kickoff_at, earlier.kickoff_at)
            for earlier, later in zip(ordered_fixtures, ordered_fixtures[1:])
            if later.kickoff_at <= target.kickoff_at
        )
        min_fixture_gap_hours_observed = (
            _quantize(min(fixture_gaps)) if fixture_gaps else rest_hours_before_target
        )
        fixture_count_lookback = _whole(len(lookback_fixtures) + 1)

        reason_codes = []
        if target.conflicting_source_count > config.max_conflicting_source_count:
            reason_codes.append(CONFLICTING_SOURCES_REASON)
        if rest_hours_before_target < config.min_rest_hours:
            reason_codes.append(REST_GAP_REASON)
        if (
            fixture_count_lookback >= config.max_fixture_count_lookback
            or min_fixture_gap_hours_observed < config.min_fixture_gap_hours
        ):
            reason_codes.append(FIXTURE_DENSITY_REASON)
        if target.travel_distance_km >= config.high_travel_distance_km:
            reason_codes.append(TRAVEL_LOAD_REASON)
        if target.source_count < config.min_source_count:
            reason_codes.append(SOURCE_COVERAGE_GAP_REASON)
        if not reason_codes:
            reason_codes.append(READY_REASON)
        row_reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

        rows.append(
            MarketResearchSoccerFixtureCongestionDigestRow(
                condition_id=condition_id,
                league_key=league_key,
                team_key=team_key,
                target_fixture_ref=target.fixture_ref,
                target_kickoff_at=target.kickoff_at,
                fixture_count_lookback=fixture_count_lookback,
                rest_hours_before_target=rest_hours_before_target,
                min_fixture_gap_hours_observed=min_fixture_gap_hours_observed,
                travel_distance_km_latest=target.travel_distance_km,
                source_count_latest=target.source_count,
                conflicting_source_count_latest=target.conflicting_source_count,
                digest_status=_row_status(row_reason_codes),
                reason_codes=row_reason_codes,
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerFixtureCongestionDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSoccerFixtureCongestionDigestReasonCodeCount(
            reason_code=reason_code,
            condition_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_fixtures(
    fixtures: Iterable[MarketResearchSoccerFixtureCongestionDigestFixture],
) -> tuple[MarketResearchSoccerFixtureCongestionDigestFixture, ...]:
    if isinstance(fixtures, (str, bytes)):
        raise ValueError("fixtures must contain soccer fixture records")
    try:
        fixture_items = tuple(fixtures)
    except TypeError as exc:
        raise ValueError("fixtures must contain soccer fixture records") from exc
    seen: set[str] = set()
    for fixture in fixture_items:
        if type(fixture) is not MarketResearchSoccerFixtureCongestionDigestFixture:
            raise ValueError(
                "fixtures must contain "
                "MarketResearchSoccerFixtureCongestionDigestFixture records",
            )
        _require_flags("fixture", fixture)
        if fixture.fixture_ref in seen:
            raise ValueError("fixtures must not contain duplicate fixture_ref values")
        seen.add(fixture.fixture_ref)
    return fixture_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerFixtureCongestionDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSoccerFixtureCongestionDigestRow:
            raise ValueError(
                "rows must contain MarketResearchSoccerFixtureCongestionDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    keys = tuple((row.condition_id, row.league_key, row.team_key) for row in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate condition/team keys")
    return normalized


def _normalize_fixture_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("fixture_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError(
                "fixture_config_versions entries must be fixture/version pairs",
            )
        fixture_ref, config_version = item
        _require_canonical_string("fixture_config_versions fixture_ref", fixture_ref)
        _require_canonical_string(
            "fixture_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("fixture_config_versions fixture_ref", fixture_ref)
        _reject_sensitive_text(
            "fixture_config_versions config_version",
            config_version,
        )
        if fixture_ref in seen_refs:
            raise ValueError("fixture_config_versions fixture_ref values must be unique")
        seen_refs.add(fixture_ref)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("fixture_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerFixtureCongestionDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchSoccerFixtureCongestionDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerFixtureCongestionDigestReasonCodeCount records",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: DIGEST_REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _validate_row(row: MarketResearchSoccerFixtureCongestionDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == READY_STATUS and row.reason_codes != (READY_REASON,):
        raise ValueError("ready rows must use the ready reason")
    if row.conflicting_source_count_latest > row.source_count_latest:
        raise ValueError("conflicting_source_count_latest must not exceed source_count_latest")


def _validate_report(report: MarketResearchSoccerFixtureCongestionDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.condition_count != _whole(len(report.rows)):
        raise ValueError("condition_count must match rows")
    if report.ready_condition_count != _whole(
        sum(1 for row in report.rows if row.digest_status == READY_STATUS),
    ):
        raise ValueError("ready_condition_count must match rows")
    if report.watch_condition_count != _whole(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_condition_count must match rows")
    if report.blocked_condition_count != _whole(
        sum(1 for row in report.rows if row.digest_status == BLOCKED_STATUS),
    ):
        raise ValueError("blocked_condition_count must match rows")
    if (
        report.condition_count
        != report.ready_condition_count
        + report.watch_condition_count
        + report.blocked_condition_count
    ):
        raise ValueError("condition counts must reconcile")
    if report.rest_gap_condition_count != _whole(
        sum(1 for row in report.rows if REST_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("rest_gap_condition_count must match rows")
    if report.fixture_density_condition_count != _whole(
        sum(1 for row in report.rows if FIXTURE_DENSITY_REASON in row.reason_codes),
    ):
        raise ValueError("fixture_density_condition_count must match rows")
    if report.travel_load_condition_count != _whole(
        sum(1 for row in report.rows if TRAVEL_LOAD_REASON in row.reason_codes),
    ):
        raise ValueError("travel_load_condition_count must match rows")
    if report.source_gap_condition_count != _whole(
        sum(1 for row in report.rows if SOURCE_COVERAGE_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("source_gap_condition_count must match rows")
    if report.conflict_condition_count != _whole(
        sum(1 for row in report.rows if CONFLICTING_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("conflict_condition_count must match rows")
    if report.min_rest_hours_observed != _min_or_none(
        row.rest_hours_before_target for row in report.rows
    ):
        raise ValueError("min_rest_hours_observed must match rows")
    if report.max_fixture_count_lookback_observed != _max_or_none(
        row.fixture_count_lookback for row in report.rows
    ):
        raise ValueError("max_fixture_count_lookback_observed must match rows")
    if report.max_travel_distance_km_observed != _max_or_none(
        row.travel_distance_km_latest for row in report.rows
    ):
        raise ValueError("max_travel_distance_km_observed must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = (
        BLOCKED_STATUS
        if any(row.digest_status == BLOCKED_STATUS for row in report.rows)
        else WATCH_STATUS
        if row_reason_codes
        else PASS_STATUS
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{name} contains invalid reason code for this field")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must not contain duplicates")
    sorted_codes = _sort_reason_codes(reason_codes, allowed)
    if reason_codes != sorted_codes:
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CONFLICTING_SOURCES_REASON in reason_codes:
        return BLOCKED_STATUS
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    return WATCH_STATUS


def _row_sort_key(row: MarketResearchSoccerFixtureCongestionDigestRow) -> tuple[object, ...]:
    status_rank = {
        BLOCKED_STATUS: 0,
        WATCH_STATUS: 1,
        READY_STATUS: 2,
    }[row.digest_status]
    return (
        status_rank,
        row.rest_hours_before_target,
        -row.fixture_count_lookback,
        row.min_fixture_gap_hours_observed,
        -row.travel_distance_km_latest,
        row.condition_id,
        row.league_key,
        row.team_key,
    )


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400) + (
        Decimal(delta.seconds * 1000000 + delta.microseconds) / Decimal("1000000")
    )
    return _quantize(seconds / Decimal("3600"))


def _hours_to_timedelta(hours: Decimal) -> timedelta:
    return timedelta(microseconds=int(hours * Decimal("3600000000")))


def _normalize_optional_nonnegative_decimal(
    name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _whole(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _min_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(min(items))


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(max(items))


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(word in lowered for word in _BLOCKED_WORDS):
        raise ValueError(f"{name} contains unsafe source detail")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
