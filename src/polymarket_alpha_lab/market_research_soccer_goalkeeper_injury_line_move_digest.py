"""Pure Phase 1 report-only reducer for soccer goalkeeper injury line moves."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-goalkeeper-injury-line-move-digest-v0"
)
SOCCER_GOALKEEPER_INJURY_LINE_MOVE_RESEARCH_SCOPE = (
    "soccer goalkeeper injury line move research digest only"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

CLEAR_REASON = "soccer_goalkeeper_injury_line_move_clear"
MATERIAL_LINE_MOVE_REASON = "soccer_goalkeeper_injury_line_move_material_line_move"
MATERIAL_PROBABILITY_DELTA_REASON = (
    "soccer_goalkeeper_injury_line_move_material_probability_delta"
)
INJURY_RISK_REASON = "soccer_goalkeeper_injury_line_move_injury_risk"
HIGH_KEEPER_IMPACT_REASON = "soccer_goalkeeper_injury_line_move_high_keeper_impact"
SOURCE_CONFIDENCE_REASON = "soccer_goalkeeper_injury_line_move_source_confidence"
SOURCE_GAP_REASON = "soccer_goalkeeper_injury_line_move_source_gap"
STALE_OBSERVATION_REASON = "soccer_goalkeeper_injury_line_move_stale_observation"
BLOCKED_PRESENT_REASON = "soccer_goalkeeper_injury_line_move_blocked_present"
WATCH_PRESENT_REASON = "soccer_goalkeeper_injury_line_move_watch_present"
DIGEST_CLEAR_REASON = "soccer_goalkeeper_injury_line_move_digest_clear"
DIGEST_EMPTY_REASON = "soccer_goalkeeper_injury_line_move_digest_empty"

ROW_REASON_CODES = (
    CLEAR_REASON,
    MATERIAL_LINE_MOVE_REASON,
    MATERIAL_PROBABILITY_DELTA_REASON,
    INJURY_RISK_REASON,
    HIGH_KEEPER_IMPACT_REASON,
    SOURCE_CONFIDENCE_REASON,
    SOURCE_GAP_REASON,
    STALE_OBSERVATION_REASON,
)
REPORT_REASON_CODES = (
    BLOCKED_PRESENT_REASON,
    WATCH_PRESENT_REASON,
    MATERIAL_LINE_MOVE_REASON,
    MATERIAL_PROBABILITY_DELTA_REASON,
    INJURY_RISK_REASON,
    HIGH_KEEPER_IMPACT_REASON,
    SOURCE_CONFIDENCE_REASON,
    SOURCE_GAP_REASON,
    STALE_OBSERVATION_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*REPORT_REASON_CODES, *ROW_REASON_CODES)))

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "allow_report_only_soccer_goalkeeper_injury_line_move_screening",
    WATCH_STATUS: "watch_report_only_soccer_goalkeeper_injury_line_move_screening",
    BLOCKED_STATUS: "block_report_only_soccer_goalkeeper_injury_line_move_screening",
}

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION",
    "SOCCER_GOALKEEPER_INJURY_LINE_MOVE_RESEARCH_SCOPE",
    "MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig",
    "MarketResearchSoccerGoalkeeperInjuryLineMoveObservation",
    "MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount",
    "MarketResearchSoccerGoalkeeperInjuryLineMoveRow",
    "MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport",
    "build_market_research_soccer_goalkeeper_injury_line_move_digest",
    "market_research_soccer_goalkeeper_injury_line_move_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_line_move_goals: Decimal = Decimal("0.250000")
    min_implied_probability_delta: Decimal = Decimal("0.050000")
    watch_goalkeeper_injury_probability: Decimal = Decimal("0.350000")
    blocked_goalkeeper_injury_probability: Decimal = Decimal("0.650000")
    keeper_impact_threshold: Decimal = Decimal("0.750000")
    source_confidence_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _require_positive_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        for field_name in ("min_source_count", "min_independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_line_move_goals",
            _require_positive_decimal("min_line_move_goals", self.min_line_move_goals),
        )
        for field_name in (
            "min_implied_probability_delta",
            "watch_goalkeeper_injury_probability",
            "blocked_goalkeeper_injury_probability",
            "keeper_impact_threshold",
            "source_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_independent_source_count > self.min_source_count:
            raise ValueError("min_independent_source_count must not exceed min_source_count")
        if (
            self.watch_goalkeeper_injury_probability
            > self.blocked_goalkeeper_injury_probability
        ):
            raise ValueError(
                "watch_goalkeeper_injury_probability must not exceed blocked threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerGoalkeeperInjuryLineMoveObservation(_NoSubclass):
    condition_id: str
    event_id: str
    league_id: str
    team_id: str
    opponent_id: str
    goalkeeper_id: str
    source_id: str
    observed_at: datetime
    line_move_goals: Decimal
    implied_probability_delta: Decimal
    goalkeeper_injury_probability: Decimal
    keeper_impact_score: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_confidence: Decimal
    line_reference: str
    injury_reference: str
    observation_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerGoalkeeperInjuryLineMoveObservation,
            "observation",
        )
        for field_name in (
            "condition_id",
            "event_id",
            "league_id",
            "team_id",
            "opponent_id",
            "goalkeeper_id",
            "source_id",
            "line_reference",
            "injury_reference",
            "observation_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "line_move_goals",
            _require_nonnegative_decimal("line_move_goals", self.line_move_goals),
        )
        for field_name in (
            "implied_probability_delta",
            "goalkeeper_injury_probability",
            "keeper_impact_score",
            "source_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchSoccerGoalkeeperInjuryLineMoveRow(_NoSubclass):
    condition_id: str
    event_id: str
    league_id: str
    team_id: str
    opponent_id: str
    goalkeeper_id: str
    source_id: str
    observed_at: datetime
    observation_age_seconds: Decimal
    line_move_goals: Decimal
    implied_probability_delta: Decimal
    goalkeeper_injury_probability: Decimal
    keeper_impact_score: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_diversity_ratio: Decimal
    source_confidence: Decimal
    risk_score: Decimal
    digest_status: str
    line_reference: str
    injury_reference: str
    observation_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchSoccerGoalkeeperInjuryLineMoveRow, "row")
        for field_name in (
            "condition_id",
            "event_id",
            "league_id",
            "team_id",
            "opponent_id",
            "goalkeeper_id",
            "source_id",
            "line_reference",
            "injury_reference",
            "observation_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("observation_age_seconds", "line_move_goals"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "implied_probability_delta",
            "goalkeeper_injury_probability",
            "keeper_impact_score",
            "source_diversity_ratio",
            "source_confidence",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    material_line_move_count: Decimal
    probability_delta_count: Decimal
    injury_risk_count: Decimal
    high_keeper_impact_count: Decimal
    source_confidence_count: Decimal
    source_gap_count: Decimal
    stale_observation_count: Decimal
    max_observation_age_seconds_observed: Decimal
    max_line_move_goals: Decimal
    max_implied_probability_delta: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...]
    observation_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.research_scope != SOCCER_GOALKEEPER_INJURY_LINE_MOVE_RESEARCH_SCOPE:
            raise ValueError("research_scope must match soccer goalkeeper line move scope")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "material_line_move_count",
            "probability_delta_count",
            "injury_risk_count",
            "high_keeper_impact_count",
            "source_confidence_count",
            "source_gap_count",
            "stale_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_observation_age_seconds_observed",
            "max_line_move_goals",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_implied_probability_delta",
            "max_risk_score",
            "average_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "observation_config_versions",
            _normalize_observation_config_versions(self.observation_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_soccer_goalkeeper_injury_line_move_digest(
    observations: Iterable[MarketResearchSoccerGoalkeeperInjuryLineMoveObservation],
    *,
    config: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    if type(config) is not MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig:
        raise ValueError(
            "config must be a MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    _validate_observations(items, generated_at=generated_at_utc)

    rows = _build_rows(items, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows)
    return MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=SOCCER_GOALKEEPER_INJURY_LINE_MOVE_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        observation_count=_count_decimal(len(items)),
        row_count=_count_decimal(len(rows)),
        blocked_count=_count_by_status(rows, BLOCKED_STATUS),
        watch_count=_count_by_status(rows, WATCH_STATUS),
        pass_count=_count_by_status(rows, PASS_STATUS),
        material_line_move_count=_count_by_reason(rows, MATERIAL_LINE_MOVE_REASON),
        probability_delta_count=_count_by_reason(rows, MATERIAL_PROBABILITY_DELTA_REASON),
        injury_risk_count=_count_by_reason(rows, INJURY_RISK_REASON),
        high_keeper_impact_count=_count_by_reason(rows, HIGH_KEEPER_IMPACT_REASON),
        source_confidence_count=_count_by_reason(rows, SOURCE_CONFIDENCE_REASON),
        source_gap_count=_count_by_reason(rows, SOURCE_GAP_REASON),
        stale_observation_count=_count_by_reason(rows, STALE_OBSERVATION_REASON),
        max_observation_age_seconds_observed=_max_row_decimal(
            rows,
            "observation_age_seconds",
        ),
        max_line_move_goals=_max_row_decimal(rows, "line_move_goals"),
        max_implied_probability_delta=_max_row_decimal(
            rows,
            "implied_probability_delta",
        ),
        max_risk_score=_max_row_decimal(rows, "risk_score"),
        average_risk_score=_ratio(_sum_decimal(row.risk_score for row in rows), _count_decimal(len(rows))),
        rows=rows,
        observation_config_versions=_observation_config_versions(items),
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_soccer_goalkeeper_injury_line_move_digest_payload(
    report: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport:
        raise ValueError(
            "report must be a MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport",
        )
    _revalidate_public_value(report)
    value = _to_payload_value(report)
    if type(value) is not dict:
        raise ValueError("report output must be a dict")
    return value


def _validate_observations(
    items: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveObservation, ...],
    *,
    generated_at: datetime,
) -> None:
    seen_source_ids: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchSoccerGoalkeeperInjuryLineMoveObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchSoccerGoalkeeperInjuryLineMoveObservation values",
            )
        _require_hard_flags("observation", item)
        _revalidate_public_value(item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.source_id in seen_source_ids:
            raise ValueError("observations must use unique source_id values")
        seen_source_ids.add(item.source_id)


def _build_rows(
    items: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveObservation, ...],
    *,
    config: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...]:
    rows = tuple(_row_from_observation(item, config=config, generated_at=generated_at) for item in items)
    return tuple(row for _, row in sorted((_row_sort_key(row), row) for row in rows))


def _row_from_observation(
    item: MarketResearchSoccerGoalkeeperInjuryLineMoveObservation,
    *,
    config: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerGoalkeeperInjuryLineMoveRow:
    observation_age_seconds = _age_seconds(generated_at, item.observed_at)
    risk_score = _risk_score(item)
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        observation_age_seconds=observation_age_seconds,
    )
    return MarketResearchSoccerGoalkeeperInjuryLineMoveRow(
        condition_id=item.condition_id,
        event_id=item.event_id,
        league_id=item.league_id,
        team_id=item.team_id,
        opponent_id=item.opponent_id,
        goalkeeper_id=item.goalkeeper_id,
        source_id=item.source_id,
        observed_at=item.observed_at,
        observation_age_seconds=observation_age_seconds,
        line_move_goals=item.line_move_goals,
        implied_probability_delta=item.implied_probability_delta,
        goalkeeper_injury_probability=item.goalkeeper_injury_probability,
        keeper_impact_score=item.keeper_impact_score,
        source_count=item.source_count,
        independent_source_count=item.independent_source_count,
        source_diversity_ratio=_ratio(item.independent_source_count, item.source_count),
        source_confidence=item.source_confidence,
        risk_score=risk_score,
        digest_status=_row_status(
            item=item,
            config=config,
            reason_codes=reason_codes,
        ),
        line_reference=item.line_reference,
        injury_reference=item.injury_reference,
        observation_config_version=item.observation_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: MarketResearchSoccerGoalkeeperInjuryLineMoveObservation,
    config: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
    observation_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.line_move_goals >= config.min_line_move_goals:
        reason_codes.append(MATERIAL_LINE_MOVE_REASON)
    if item.implied_probability_delta >= config.min_implied_probability_delta:
        reason_codes.append(MATERIAL_PROBABILITY_DELTA_REASON)
    if item.goalkeeper_injury_probability >= config.watch_goalkeeper_injury_probability:
        reason_codes.append(INJURY_RISK_REASON)
    if item.keeper_impact_score >= config.keeper_impact_threshold:
        reason_codes.append(HIGH_KEEPER_IMPACT_REASON)
    if item.source_confidence >= config.source_confidence_threshold:
        reason_codes.append(SOURCE_CONFIDENCE_REASON)
    if (
        item.source_count < config.min_source_count
        or item.independent_source_count < config.min_independent_source_count
    ):
        reason_codes.append(SOURCE_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _sort_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    item: MarketResearchSoccerGoalkeeperInjuryLineMoveObservation,
    config: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
    reason_codes: tuple[str, ...],
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return PASS_STATUS
    if (
        item.goalkeeper_injury_probability >= config.blocked_goalkeeper_injury_probability
        or SOURCE_GAP_REASON in reason_codes
        or STALE_OBSERVATION_REASON in reason_codes
    ):
        return BLOCKED_STATUS
    return WATCH_STATUS


def _report_status(rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.digest_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        reason_codes.append(BLOCKED_PRESENT_REASON)
    if any(row.digest_status == WATCH_STATUS for row in rows):
        reason_codes.append(WATCH_PRESENT_REASON)
    for reason_code in ROW_REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(DIGEST_CLEAR_REASON)
    return _sort_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
) -> tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount, ...]:
    row_total = _count_decimal(len(rows))
    counts: list[MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount] = []
    for reason_code in reason_codes:
        if reason_code == DIGEST_EMPTY_REASON:
            count = ONE
        elif reason_code == DIGEST_CLEAR_REASON:
            count = row_total
        elif reason_code == BLOCKED_PRESENT_REASON:
            count = _count_by_status(rows, BLOCKED_STATUS)
        elif reason_code == WATCH_PRESENT_REASON:
            count = _count_by_status(rows, WATCH_STATUS)
        else:
            count = _count_by_reason(rows, reason_code)
        if count <= ZERO:
            raise ValueError("reason_code_counts must reconcile with rows")
        counts.append(
            MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount(
                reason_code=reason_code,
                count=count,
                row_ratio=_ratio(count, row_total),
            ),
        )
    return tuple(counts)


def _validate_row(row: MarketResearchSoccerGoalkeeperInjuryLineMoveRow) -> None:
    expected_risk_score = _risk_score(row)
    if row.risk_score != expected_risk_score:
        raise ValueError("risk_score must match injury probability and keeper impact")
    if row.source_diversity_ratio != _ratio(row.independent_source_count, row.source_count):
        raise ValueError("source_diversity_ratio must match source counts")
    if row.reason_codes == (CLEAR_REASON,):
        if row.digest_status != PASS_STATUS:
            raise ValueError("clear rows must use pass digest_status")
    elif row.digest_status == PASS_STATUS:
        raise ValueError("pass rows must only use the clear reason")
    if row.digest_status == BLOCKED_STATUS and row.reason_codes == (CLEAR_REASON,):
        raise ValueError("blocked rows must include risk reasons")


def _validate_report(
    report: MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport,
) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must equal row count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must equal row count")
    for field_name, status in (
        ("blocked_count", BLOCKED_STATUS),
        ("watch_count", WATCH_STATUS),
        ("pass_count", PASS_STATUS),
    ):
        if getattr(report, field_name) != _count_by_status(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    for field_name, reason_code in (
        ("material_line_move_count", MATERIAL_LINE_MOVE_REASON),
        ("probability_delta_count", MATERIAL_PROBABILITY_DELTA_REASON),
        ("injury_risk_count", INJURY_RISK_REASON),
        ("high_keeper_impact_count", HIGH_KEEPER_IMPACT_REASON),
        ("source_confidence_count", SOURCE_CONFIDENCE_REASON),
        ("source_gap_count", SOURCE_GAP_REASON),
        ("stale_observation_count", STALE_OBSERVATION_REASON),
    ):
        if getattr(report, field_name) != _count_by_reason(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_observation_age_seconds_observed != _max_row_decimal(
        report.rows,
        "observation_age_seconds",
    ):
        raise ValueError("max_observation_age_seconds_observed must match rows")
    if report.max_line_move_goals != _max_row_decimal(report.rows, "line_move_goals"):
        raise ValueError("max_line_move_goals must match rows")
    if report.max_implied_probability_delta != _max_row_decimal(
        report.rows,
        "implied_probability_delta",
    ):
        raise ValueError("max_implied_probability_delta must match rows")
    if report.max_risk_score != _max_row_decimal(report.rows, "risk_score"):
        raise ValueError("max_risk_score must match rows")
    if report.average_risk_score != _ratio(
        _sum_decimal(row.risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_risk_score must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.observation_config_versions != _observation_config_versions_from_rows(
        report.rows,
    ):
        raise ValueError("observation_config_versions must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(expected_reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes and rows")


def _normalize_rows(
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
) -> tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchSoccerGoalkeeperInjuryLineMoveRow:
            raise ValueError(
                "rows must contain MarketResearchSoccerGoalkeeperInjuryLineMoveRow values",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must use unique source_id values")
        seen_source_ids.add(row.source_id)
    expected_rows = tuple(row for _, row in sorted((_row_sort_key(row), row) for row in rows))
    if rows != expected_rows:
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_observation_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("observation_config_versions must be a tuple")
    seen_source_ids: set[str] = set()
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("observation_config_versions must contain pairs")
        source_id, config_version = value
        _require_canonical_string("source_id", source_id)
        _require_canonical_string("observation_config_version", config_version)
        if source_id in seen_source_ids:
            raise ValueError("observation_config_versions must use unique source_id values")
        seen_source_ids.add(source_id)
    expected_values = tuple(sorted(values, key=lambda value: value[0]))
    if values != expected_values:
        raise ValueError("observation_config_versions must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount, ...],
) -> tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount values",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must use unique reason_code values")
        seen_reason_codes.add(count.reason_code)
    expected_counts = tuple(
        count
        for _, count in sorted((_reason_rank(count.reason_code), count) for count in counts)
    )
    if counts != expected_counts:
        raise ValueError("reason_code_counts must use canonical sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains invalid reason code")
    if _sort_reason_codes(tuple(dict.fromkeys(reason_codes))) != reason_codes:
        raise ValueError(f"{field_name} must be unique and canonical")
    return reason_codes


def _row_sort_key(row: MarketResearchSoccerGoalkeeperInjuryLineMoveRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        _status_rank(row.digest_status),
        -row.risk_score,
        -row.line_move_goals,
        row.condition_id,
    )


def _status_rank(status: str) -> int:
    return {BLOCKED_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}[status]


def _reason_rank(reason_code: str) -> int:
    return KNOWN_REASON_CODES.index(reason_code)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        reason_code
        for _, reason_code in sorted(
            (_reason_rank(reason_code), reason_code) for reason_code in reason_codes
        )
    )


def _count_by_status(
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _count_by_reason(
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _risk_score(value: object) -> Decimal:
    return _quantize(
        max(
            getattr(value, "goalkeeper_injury_probability"),
            getattr(value, "keeper_impact_score"),
        ),
    )


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(str((later - earlier).total_seconds())))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _observation_config_versions(
    items: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (item.source_id, item.observation_config_version) for item in items
        ),
    )


def _observation_config_versions_from_rows(
    rows: tuple[MarketResearchSoccerGoalkeeperInjuryLineMoveRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((row.source_id, row.observation_config_version) for row in rows),
    )


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_payload_utc(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _revalidate_public_value(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_TYPES:
            raise ValueError("public dataclass has unsupported type")
        _require_hard_flags(type(value).__name__, value)
        attrs = {field.name: getattr(value, field.name) for field in fields(value)}
        for field in fields(value):
            field_value = attrs[field.name]
            if type(field_value) is datetime:
                _require_payload_utc(field.name, field_value)
            _revalidate_public_value(field_value)
        type(value)(**attrs)
        return
    if type(value) is tuple:
        for item in value:
            _revalidate_public_value(item)
        return
    if type(value) is datetime:
        _require_payload_utc("datetime", value)
        return
    if type(value) is Decimal:
        _require_decimal("decimal", value)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) is int:
        raise ValueError("public numerics must be Decimals")


def _to_payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_to_payload_value(item) for item in value]
    return value


_PUBLIC_TYPES = (
    MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
    MarketResearchSoccerGoalkeeperInjuryLineMoveObservation,
    MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount,
    MarketResearchSoccerGoalkeeperInjuryLineMoveRow,
    MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport,
)
