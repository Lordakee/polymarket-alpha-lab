"""Pure Phase 1 basketball line movement injury correlation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-line-movement-injury-correlation-digest-v0"
)
BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_RESEARCH_SCOPE = (
    "basketball_line_movement_injury_correlation"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
STATUS_RANK = {
    STATUS_BLOCKED: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_READY: Decimal("2.000000"),
}

REASON_PREFIX = "market_research_basketball_line_movement_injury_correlation_digest"
MATERIAL_LINE_MOVE_REASON = f"{REASON_PREFIX}_material_line_move"
MATERIAL_PROBABILITY_DELTA_REASON = f"{REASON_PREFIX}_material_probability_delta"
HIGH_PLAYER_IMPACT_REASON = f"{REASON_PREFIX}_high_player_impact"
CORRELATION_BLOCKED_REASON = f"{REASON_PREFIX}_correlation_blocked"
CORRELATION_WATCH_REASON = f"{REASON_PREFIX}_correlation_watch"
SOURCE_GAP_REASON = f"{REASON_PREFIX}_source_gap"
LIQUIDITY_GAP_REASON = f"{REASON_PREFIX}_liquidity_gap"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}_stale_observation"
READY_REASON = f"{REASON_PREFIX}_ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}_no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_LINE_MOVE_REASON,
    MATERIAL_PROBABILITY_DELTA_REASON,
    HIGH_PLAYER_IMPACT_REASON,
    CORRELATION_BLOCKED_REASON,
    CORRELATION_WATCH_REASON,
    SOURCE_GAP_REASON,
    LIQUIDITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    READY_REASON,
)
REASON_CODE_SEQUENCE = ROW_REASON_CODE_SEQUENCE + (NO_INPUTS_REASON,)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
UNSAFE_REFERENCE_FRAGMENTS = (
    "token",
    "credential",
    "password",
    "bearer",
    "cookie",
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION",
    "BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_RESEARCH_SCOPE",
    "MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig",
    "MarketResearchBasketballLineMovementInjuryCorrelationObservation",
    "MarketResearchBasketballLineMovementInjuryCorrelationDigestRow",
    "MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount",
    "MarketResearchBasketballLineMovementInjuryCorrelationDigestReport",
    "build_market_research_basketball_line_movement_injury_correlation_digest",
    "market_research_basketball_line_movement_injury_correlation_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_line_move_points: Decimal = Decimal("2.500000")
    min_implied_probability_delta: Decimal = Decimal("0.050000")
    high_player_impact_threshold: Decimal = Decimal("0.750000")
    correlation_watch_threshold: Decimal = Decimal("0.650000")
    correlation_blocked_threshold: Decimal = Decimal("0.850000")
    min_market_liquidity_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION
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
            "min_line_move_points",
            _require_positive_decimal("min_line_move_points", self.min_line_move_points),
        )
        for field_name in (
            "min_implied_probability_delta",
            "high_player_impact_threshold",
            "correlation_watch_threshold",
            "correlation_blocked_threshold",
            "min_market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_independent_source_count > self.min_source_count:
            raise ValueError("min_independent_source_count must not exceed min_source_count")
        if self.correlation_watch_threshold > self.correlation_blocked_threshold:
            raise ValueError(
                "correlation_watch_threshold must not exceed blocked threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineMovementInjuryCorrelationObservation(_NoSubclass):
    source_id: str
    condition_id: str
    basketball_event_key: str
    league_key: str
    team_key: str
    opponent_key: str
    player_key: str
    injury_status: str
    market_slug: str
    public_line_reference: str
    public_injury_reference: str
    observed_at: datetime
    line_move_points: Decimal
    implied_probability_delta: Decimal
    player_impact_score: Decimal
    injury_correlation_score: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    market_liquidity_score: Decimal
    item_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballLineMovementInjuryCorrelationObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "condition_id",
            "basketball_event_key",
            "league_key",
            "team_key",
            "opponent_key",
            "player_key",
            "injury_status",
            "market_slug",
            "item_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_reference("public_line_reference", self.public_line_reference)
        _require_public_reference("public_injury_reference", self.public_injury_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "line_move_points",
            _require_nonnegative_decimal("line_move_points", self.line_move_points),
        )
        for field_name in (
            "implied_probability_delta",
            "player_impact_score",
            "injury_correlation_score",
            "market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
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
class MarketResearchBasketballLineMovementInjuryCorrelationDigestRow(_NoSubclass):
    source_id: str
    condition_id: str
    basketball_event_key: str
    league_key: str
    team_key: str
    opponent_key: str
    player_key: str
    injury_status: str
    market_slug: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    line_move_points: Decimal
    implied_probability_delta: Decimal
    player_impact_score: Decimal
    injury_correlation_score: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_diversity_ratio: Decimal
    market_liquidity_score: Decimal
    redacted_public_line_reference: str
    redacted_public_injury_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballLineMovementInjuryCorrelationDigestRow,
            "row",
        )
        for field_name in (
            "source_id",
            "condition_id",
            "basketball_event_key",
            "league_key",
            "team_key",
            "opponent_key",
            "player_key",
            "injury_status",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("observation_age_seconds", "line_move_points"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "implied_probability_delta",
            "player_impact_score",
            "injury_correlation_score",
            "source_diversity_ratio",
            "market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_public_reference(
            "redacted_public_line_reference",
            self.redacted_public_line_reference,
        )
        _require_public_reference(
            "redacted_public_injury_reference",
            self.redacted_public_injury_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineMovementInjuryCorrelationDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    ready_count: Decimal
    material_line_move_count: Decimal
    probability_delta_count: Decimal
    high_player_impact_count: Decimal
    correlation_pressure_count: Decimal
    source_gap_count: Decimal
    liquidity_gap_count: Decimal
    stale_observation_count: Decimal
    max_observation_age_seconds: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    min_line_move_points: Decimal
    min_implied_probability_delta: Decimal
    high_player_impact_threshold: Decimal
    correlation_watch_threshold: Decimal
    correlation_blocked_threshold: Decimal
    min_market_liquidity_score: Decimal
    max_observation_age_seconds_observed: Decimal
    max_line_move_points: Decimal
    max_implied_probability_delta: Decimal
    max_injury_correlation_score: Decimal
    average_injury_correlation_score: Decimal
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...]
    item_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballLineMovementInjuryCorrelationDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.research_scope != BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball line movement injury scope")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "ready_count",
            "material_line_move_count",
            "probability_delta_count",
            "high_player_impact_count",
            "correlation_pressure_count",
            "source_gap_count",
            "liquidity_gap_count",
            "stale_observation_count",
            "max_observation_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "min_line_move_points",
            "max_observation_age_seconds_observed",
            "max_line_move_points",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_implied_probability_delta",
            "high_player_impact_threshold",
            "correlation_watch_threshold",
            "correlation_blocked_threshold",
            "min_market_liquidity_score",
            "max_implied_probability_delta",
            "max_injury_correlation_score",
            "average_injury_correlation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "item_config_versions",
            _normalize_item_config_versions(self.item_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_basketball_line_movement_injury_correlation_digest(
    items: Iterable[MarketResearchBasketballLineMovementInjuryCorrelationObservation],
    *,
    config: MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballLineMovementInjuryCorrelationDigestReport:
    if type(config) is not MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(items)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    return MarketResearchBasketballLineMovementInjuryCorrelationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_RESEARCH_SCOPE,
        digest_status=_digest_status(rows),
        recommended_next_step=_recommended_next_step(_digest_status(rows)),
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, STATUS_BLOCKED),
        watch_count=_status_count(rows, STATUS_WATCH),
        ready_count=_status_count(rows, STATUS_READY),
        material_line_move_count=_reason_count(rows, MATERIAL_LINE_MOVE_REASON),
        probability_delta_count=_reason_count(rows, MATERIAL_PROBABILITY_DELTA_REASON),
        high_player_impact_count=_reason_count(rows, HIGH_PLAYER_IMPACT_REASON),
        correlation_pressure_count=_any_reason_count(
            rows,
            (CORRELATION_BLOCKED_REASON, CORRELATION_WATCH_REASON),
        ),
        source_gap_count=_reason_count(rows, SOURCE_GAP_REASON),
        liquidity_gap_count=_reason_count(rows, LIQUIDITY_GAP_REASON),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        max_observation_age_seconds=_six(config.max_observation_age_seconds),
        min_source_count=_six(config.min_source_count),
        min_independent_source_count=_six(config.min_independent_source_count),
        min_line_move_points=_six(config.min_line_move_points),
        min_implied_probability_delta=_six(config.min_implied_probability_delta),
        high_player_impact_threshold=_six(config.high_player_impact_threshold),
        correlation_watch_threshold=_six(config.correlation_watch_threshold),
        correlation_blocked_threshold=_six(config.correlation_blocked_threshold),
        min_market_liquidity_score=_six(config.min_market_liquidity_score),
        max_observation_age_seconds_observed=_max_row_decimal(
            rows,
            "observation_age_seconds",
        ),
        max_line_move_points=_max_row_decimal(rows, "line_move_points"),
        max_implied_probability_delta=_max_row_decimal(
            rows,
            "implied_probability_delta",
        ),
        max_injury_correlation_score=_max_row_decimal(
            rows,
            "injury_correlation_score",
        ),
        average_injury_correlation_score=_ratio(
            _sum_decimal(row.injury_correlation_score for row in rows),
            row_count,
        ),
        rows=rows,
        item_config_versions=_item_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_line_movement_injury_correlation_digest_payload(
    report: MarketResearchBasketballLineMovementInjuryCorrelationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballLineMovementInjuryCorrelationDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBasketballLineMovementInjuryCorrelationDigestReport",
        )
    _require_hard_flags("report", report)
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report output must be a dict")
    return value


def _row_from_observation(
    item: MarketResearchBasketballLineMovementInjuryCorrelationObservation,
    *,
    config: MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballLineMovementInjuryCorrelationDigestRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, item.observed_at)
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        observation_age_seconds=observation_age_seconds,
    )
    return MarketResearchBasketballLineMovementInjuryCorrelationDigestRow(
        source_id=item.source_id,
        condition_id=item.condition_id,
        basketball_event_key=item.basketball_event_key,
        league_key=item.league_key,
        team_key=item.team_key,
        opponent_key=item.opponent_key,
        player_key=item.player_key,
        injury_status=item.injury_status,
        market_slug=item.market_slug,
        digest_status=_row_status(reason_codes),
        observed_at=item.observed_at,
        observation_age_seconds=observation_age_seconds,
        line_move_points=_six(item.line_move_points),
        implied_probability_delta=_six(item.implied_probability_delta),
        player_impact_score=_six(item.player_impact_score),
        injury_correlation_score=_six(item.injury_correlation_score),
        source_count=_six(item.source_count),
        independent_source_count=_six(item.independent_source_count),
        source_diversity_ratio=_ratio(item.independent_source_count, item.source_count),
        market_liquidity_score=_six(item.market_liquidity_score),
        redacted_public_line_reference=item.public_line_reference,
        redacted_public_injury_reference=item.public_injury_reference,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: MarketResearchBasketballLineMovementInjuryCorrelationObservation,
    config: MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig,
    observation_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.line_move_points >= config.min_line_move_points:
        reason_codes.append(MATERIAL_LINE_MOVE_REASON)
    if item.implied_probability_delta >= config.min_implied_probability_delta:
        reason_codes.append(MATERIAL_PROBABILITY_DELTA_REASON)
    if item.player_impact_score >= config.high_player_impact_threshold:
        reason_codes.append(HIGH_PLAYER_IMPACT_REASON)
    if item.injury_correlation_score >= config.correlation_blocked_threshold:
        reason_codes.append(CORRELATION_BLOCKED_REASON)
    elif item.injury_correlation_score >= config.correlation_watch_threshold:
        reason_codes.append(CORRELATION_WATCH_REASON)
    if (
        item.source_count < config.min_source_count
        or item.independent_source_count < config.min_independent_source_count
    ):
        reason_codes.append(SOURCE_GAP_REASON)
    if item.market_liquidity_score < config.min_market_liquidity_score:
        reason_codes.append(LIQUIDITY_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            CORRELATION_BLOCKED_REASON,
            SOURCE_GAP_REASON,
            LIQUIDITY_GAP_REASON,
            STALE_OBSERVATION_REASON,
        )
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _digest_status(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "allow_report_only_basketball_line_movement_injury_correlation_screening"
    if status == STATUS_WATCH:
        return "monitor_report_only_basketball_line_movement_injury_correlation_screening"
    return "block_report_only_basketball_line_movement_injury_correlation_screening"


def _validate_row(
    row: MarketResearchBasketballLineMovementInjuryCorrelationDigestRow,
) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("reason_codes must match digest_status")


def _validate_report(
    report: MarketResearchBasketballLineMovementInjuryCorrelationDigestReport,
) -> None:
    rows = report.rows
    if report.input_count != _count_decimal(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.ready_count != _status_count(rows, STATUS_READY):
        raise ValueError("ready_count must match rows")
    if report.blocked_count + report.watch_count + report.ready_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.material_line_move_count != _reason_count(rows, MATERIAL_LINE_MOVE_REASON):
        raise ValueError("material_line_move_count must match rows")
    if report.probability_delta_count != _reason_count(
        rows,
        MATERIAL_PROBABILITY_DELTA_REASON,
    ):
        raise ValueError("probability_delta_count must match rows")
    if report.high_player_impact_count != _reason_count(rows, HIGH_PLAYER_IMPACT_REASON):
        raise ValueError("high_player_impact_count must match rows")
    if report.correlation_pressure_count != _any_reason_count(
        rows,
        (CORRELATION_BLOCKED_REASON, CORRELATION_WATCH_REASON),
    ):
        raise ValueError("correlation_pressure_count must match rows")
    if report.source_gap_count != _reason_count(rows, SOURCE_GAP_REASON):
        raise ValueError("source_gap_count must match rows")
    if report.liquidity_gap_count != _reason_count(rows, LIQUIDITY_GAP_REASON):
        raise ValueError("liquidity_gap_count must match rows")
    if report.stale_observation_count != _reason_count(rows, STALE_OBSERVATION_REASON):
        raise ValueError("stale_observation_count must match rows")
    if report.max_observation_age_seconds_observed != _max_row_decimal(
        rows,
        "observation_age_seconds",
    ):
        raise ValueError("max_observation_age_seconds_observed must match rows")
    if report.max_line_move_points != _max_row_decimal(rows, "line_move_points"):
        raise ValueError("max_line_move_points must match rows")
    if report.max_implied_probability_delta != _max_row_decimal(
        rows,
        "implied_probability_delta",
    ):
        raise ValueError("max_implied_probability_delta must match rows")
    if report.max_injury_correlation_score != _max_row_decimal(
        rows,
        "injury_correlation_score",
    ):
        raise ValueError("max_injury_correlation_score must match rows")
    if report.average_injury_correlation_score != _ratio(
        _sum_decimal(row.injury_correlation_score for row in rows),
        report.row_count,
    ):
        raise ValueError("average_injury_correlation_score must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _expected_reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_observations(
    items: Iterable[MarketResearchBasketballLineMovementInjuryCorrelationObservation],
) -> tuple[MarketResearchBasketballLineMovementInjuryCorrelationObservation, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Iterable):
        raise ValueError(
            "items must contain "
            "MarketResearchBasketballLineMovementInjuryCorrelationObservation",
        )
    normalized = tuple(items)
    seen_source_ids: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchBasketballLineMovementInjuryCorrelationObservation:
            raise ValueError(
                "items must contain "
                "MarketResearchBasketballLineMovementInjuryCorrelationObservation",
            )
        _require_hard_flags("observation", item)
        if item.source_id in seen_source_ids:
            raise ValueError("items must not contain duplicate source_id values")
        seen_source_ids.add(item.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow],
) -> tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError(
            "rows must contain MarketResearchBasketballLineMovementInjuryCorrelationDigestRow",
        )
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchBasketballLineMovementInjuryCorrelationDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBasketballLineMovementInjuryCorrelationDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_item_config_versions(
    values: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("item_config_versions must contain source config version pairs")
    normalized = tuple(values)
    seen_source_ids: set[str] = set()
    for value in normalized:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("item_config_versions must contain source config version pairs")
        source_id, item_config_version = value
        _require_canonical_string("source_id", source_id)
        _require_canonical_string("item_config_version", item_config_version)
        if source_id in seen_source_ids:
            raise ValueError("item_config_versions must not contain duplicate source_id values")
        seen_source_ids.add(source_id)
    return tuple(sorted(normalized, key=lambda value: value[0]))


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount],
) -> tuple[MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    seen_reason_codes: set[str] = set()
    for value in normalized:
        if type(value) is not MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_reason_codes.add(value.reason_code)
    return tuple(
        sorted(normalized, key=lambda value: REASON_CODE_SEQUENCE.index(value.reason_code)),
    )


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _item_config_versions(
    items: tuple[MarketResearchBasketballLineMovementInjuryCorrelationObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return _normalize_item_config_versions(
        (item.source_id, item.item_config_version) for item in items
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
) -> tuple[MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount, ...]:
    return _expected_reason_code_counts(rows)


def _expected_reason_code_counts(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
) -> tuple[MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if not rows:
        return (
            MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, row_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if (count := _reason_count(rows, reason_code)) > ZERO
    )


def _row_sort_key(
    row: MarketResearchBasketballLineMovementInjuryCorrelationDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.digest_status],
        -row.injury_correlation_score,
        -row.line_move_points,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _any_reason_count(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _max_row_decimal(
    rows: tuple[MarketResearchBasketballLineMovementInjuryCorrelationDigestRow, ...],
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
    return _six(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(numerator / denominator)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _six(Decimal(str((later - earlier).total_seconds())))


def _count_decimal(value: int) -> Decimal:
    return _six(Decimal(value))


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, DIGEST_STATUSES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_REFERENCE_FRAGMENTS):
        raise ValueError(f"{field_name} must be unsafe-fragment-free")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat().replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
