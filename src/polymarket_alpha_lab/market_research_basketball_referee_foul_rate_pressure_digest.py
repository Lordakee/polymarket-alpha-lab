"""Pure Phase 1 basketball referee foul-rate pressure digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-referee-foul-rate-pressure-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
PRESSURE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_basketball_referee_foul_rate_pressure_screening",
    WATCH_STATUS: "monitor_report_only_basketball_referee_foul_rate_pressure_screening",
    PASS_STATUS: "allow_report_only_basketball_referee_foul_rate_pressure_screening",
}

ROW_REASON_CODES = tuple(
    sorted(
        (
            "basketball_referee_foul_pressure_below_threshold",
            "basketball_referee_foul_pressure_blocked",
            "basketball_referee_foul_pressure_late_game_delta",
            "basketball_referee_foul_pressure_low_sample",
            "basketball_referee_foul_pressure_rate_delta",
            "basketball_referee_foul_pressure_source_fresh",
            "basketball_referee_foul_pressure_source_stale",
            "basketball_referee_foul_pressure_watch",
        ),
    ),
)
REPORT_REASON_CODES = tuple(
    sorted(
        (
            "basketball_referee_foul_pressure_blocked_present",
            "basketball_referee_foul_pressure_digest_clear",
            "basketball_referee_foul_pressure_digest_empty",
            "basketball_referee_foul_pressure_late_game_delta_present",
            "basketball_referee_foul_pressure_low_sample_present",
            "basketball_referee_foul_pressure_rate_delta_present",
            "basketball_referee_foul_pressure_stale_source_present",
            "basketball_referee_foul_pressure_watch_present",
        ),
    ),
)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_PRESSURE_DIGEST_CONFIG_VERSION",
    "BasketballRefereeFoulRatePressureDigestConfig",
    "BasketballRefereeFoulRatePressureObservation",
    "BasketballRefereeFoulRatePressureDigestRow",
    "BasketballRefereeFoulRatePressureReasonCodeCount",
    "BasketballRefereeFoulRatePressureDigestReport",
    "build_market_research_basketball_referee_foul_rate_pressure_digest",
    "market_research_basketball_referee_foul_rate_pressure_digest_payload",
)


@dataclass(frozen=True)
class BasketballRefereeFoulRatePressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_PRESSURE_DIGEST_CONFIG_VERSION
    )
    watch_foul_rate_delta_per_game: Decimal = Decimal("3.000000")
    blocked_foul_rate_delta_per_game: Decimal = Decimal("6.000000")
    watch_late_game_foul_delta_per_game: Decimal = Decimal("1.500000")
    blocked_late_game_foul_delta_per_game: Decimal = Decimal("3.000000")
    min_lookback_games: Decimal = Decimal("8.000000")
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BasketballRefereeFoulRatePressureDigestConfig:
            raise TypeError(
                "BasketballRefereeFoulRatePressureDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballRefereeFoulRatePressureDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_foul_rate_delta_per_game",
            "blocked_foul_rate_delta_per_game",
            "watch_late_game_foul_delta_per_game",
            "blocked_late_game_foul_delta_per_game",
            "min_lookback_games",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class BasketballRefereeFoulRatePressureObservation:
    source_id: str
    event_id: str
    league_key: str
    referee_id: str
    team_key: str
    crew_fouls_per_game: Decimal
    league_fouls_per_game: Decimal
    late_game_foul_delta_per_game: Decimal
    lookback_games: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BasketballRefereeFoulRatePressureObservation:
            raise TypeError(
                "BasketballRefereeFoulRatePressureObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballRefereeFoulRatePressureObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "event_id",
            "league_key",
            "referee_id",
            "team_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "crew_fouls_per_game",
            "league_fouls_per_game",
            "lookback_games",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "late_game_foul_delta_per_game",
            _require_decimal(
                "late_game_foul_delta_per_game",
                self.late_game_foul_delta_per_game,
            ),
        )
        object.__setattr__(
            self,
            "evidence_confidence",
            _require_probability("evidence_confidence", self.evidence_confidence),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _require_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                require_nonempty=True,
            ),
        )
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class BasketballRefereeFoulRatePressureDigestRow:
    source_id: str
    event_id: str
    league_key: str
    referee_id: str
    team_key: str
    crew_fouls_per_game: Decimal
    league_fouls_per_game: Decimal
    foul_rate_delta_per_game: Decimal
    absolute_foul_rate_delta_per_game: Decimal
    late_game_foul_delta_per_game: Decimal
    absolute_late_game_foul_delta_per_game: Decimal
    lookback_games: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    pressure_score: Decimal
    pressure_status: str
    watch_foul_rate_delta_per_game: Decimal
    blocked_foul_rate_delta_per_game: Decimal
    watch_late_game_foul_delta_per_game: Decimal
    blocked_late_game_foul_delta_per_game: Decimal
    min_lookback_games: Decimal
    max_source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BasketballRefereeFoulRatePressureDigestRow:
            raise TypeError(
                "BasketballRefereeFoulRatePressureDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballRefereeFoulRatePressureDigestRow,
            "row",
        )
        for field_name in (
            "source_id",
            "event_id",
            "league_key",
            "referee_id",
            "team_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "crew_fouls_per_game",
            "league_fouls_per_game",
            "absolute_foul_rate_delta_per_game",
            "absolute_late_game_foul_delta_per_game",
            "lookback_games",
            "source_age_seconds",
            "watch_foul_rate_delta_per_game",
            "blocked_foul_rate_delta_per_game",
            "watch_late_game_foul_delta_per_game",
            "blocked_late_game_foul_delta_per_game",
            "min_lookback_games",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "foul_rate_delta_per_game",
            "late_game_foul_delta_per_game",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_confidence",
            _require_probability("evidence_confidence", self.evidence_confidence),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "pressure_score",
            _require_probability("pressure_score", self.pressure_score),
        )
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                require_nonempty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class BasketballRefereeFoulRatePressureReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BasketballRefereeFoulRatePressureReasonCodeCount:
            raise TypeError(
                "BasketballRefereeFoulRatePressureReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballRefereeFoulRatePressureReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self, "reason_code_count")


@dataclass(frozen=True)
class BasketballRefereeFoulRatePressureDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    elevated_foul_rate_count: Decimal
    late_game_pressure_count: Decimal
    low_sample_count: Decimal
    max_pressure_score: Decimal
    average_pressure_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[BasketballRefereeFoulRatePressureReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BasketballRefereeFoulRatePressureDigestReport:
            raise TypeError(
                "BasketballRefereeFoulRatePressureDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballRefereeFoulRatePressureDigestReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "elevated_foul_rate_count",
            "late_game_pressure_count",
            "low_sample_count",
            "max_pressure_score",
            "average_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, PRESSURE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "rows",
            _require_rows(self.rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                require_nonempty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self, "report")


def build_market_research_basketball_referee_foul_rate_pressure_digest(
    observations: Iterable[BasketballRefereeFoulRatePressureObservation],
    *,
    config: BasketballRefereeFoulRatePressureDigestConfig,
    generated_at: datetime,
) -> BasketballRefereeFoulRatePressureDigestReport:
    if type(config) is not BasketballRefereeFoulRatePressureDigestConfig:
        raise ValueError(
            "config must be exactly BasketballRefereeFoulRatePressureDigestConfig",
        )
    _validate_config(config)
    _require_hard_flags(config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _require_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return BasketballRefereeFoulRatePressureDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        elevated_foul_rate_count=_reason_count(
            rows,
            "basketball_referee_foul_pressure_rate_delta",
        ),
        late_game_pressure_count=_reason_count(
            rows,
            "basketball_referee_foul_pressure_late_game_delta",
        ),
        low_sample_count=_reason_count(
            rows,
            "basketball_referee_foul_pressure_low_sample",
        ),
        max_pressure_score=_max_row_decimal(rows, "pressure_score"),
        average_pressure_score=_ratio(
            _sum_decimal(row.pressure_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_basketball_referee_foul_rate_pressure_digest_payload(
    report: BasketballRefereeFoulRatePressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not BasketballRefereeFoulRatePressureDigestReport:
        raise ValueError(
            "report must be exactly BasketballRefereeFoulRatePressureDigestReport",
        )
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: BasketballRefereeFoulRatePressureObservation,
    *,
    config: BasketballRefereeFoulRatePressureDigestConfig,
    generated_at: datetime,
) -> BasketballRefereeFoulRatePressureDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    foul_rate_delta_per_game = _quantize_decimal(
        value.crew_fouls_per_game - value.league_fouls_per_game,
    )
    absolute_foul_rate_delta_per_game = _quantize_decimal(
        abs(foul_rate_delta_per_game),
    )
    absolute_late_game_foul_delta_per_game = _quantize_decimal(
        abs(value.late_game_foul_delta_per_game),
    )
    pressure_score = _pressure_score(
        absolute_foul_rate_delta_per_game=absolute_foul_rate_delta_per_game,
        absolute_late_game_foul_delta_per_game=(
            absolute_late_game_foul_delta_per_game
        ),
        blocked_foul_rate_delta_per_game=config.blocked_foul_rate_delta_per_game,
        blocked_late_game_foul_delta_per_game=(
            config.blocked_late_game_foul_delta_per_game
        ),
    )
    pressure_status = _pressure_status(
        absolute_foul_rate_delta_per_game=absolute_foul_rate_delta_per_game,
        absolute_late_game_foul_delta_per_game=(
            absolute_late_game_foul_delta_per_game
        ),
        lookback_games=value.lookback_games,
        source_age_seconds=source_age_seconds,
        watch_foul_rate_delta_per_game=config.watch_foul_rate_delta_per_game,
        blocked_foul_rate_delta_per_game=config.blocked_foul_rate_delta_per_game,
        watch_late_game_foul_delta_per_game=(
            config.watch_late_game_foul_delta_per_game
        ),
        blocked_late_game_foul_delta_per_game=(
            config.blocked_late_game_foul_delta_per_game
        ),
        min_lookback_games=config.min_lookback_games,
        max_source_age_seconds=config.max_source_age_seconds,
    )
    return BasketballRefereeFoulRatePressureDigestRow(
        source_id=value.source_id,
        event_id=value.event_id,
        league_key=value.league_key,
        referee_id=value.referee_id,
        team_key=value.team_key,
        crew_fouls_per_game=value.crew_fouls_per_game,
        league_fouls_per_game=value.league_fouls_per_game,
        foul_rate_delta_per_game=foul_rate_delta_per_game,
        absolute_foul_rate_delta_per_game=absolute_foul_rate_delta_per_game,
        late_game_foul_delta_per_game=value.late_game_foul_delta_per_game,
        absolute_late_game_foul_delta_per_game=(
            absolute_late_game_foul_delta_per_game
        ),
        lookback_games=value.lookback_games,
        evidence_confidence=value.evidence_confidence,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        pressure_score=pressure_score,
        pressure_status=pressure_status,
        watch_foul_rate_delta_per_game=config.watch_foul_rate_delta_per_game,
        blocked_foul_rate_delta_per_game=config.blocked_foul_rate_delta_per_game,
        watch_late_game_foul_delta_per_game=(
            config.watch_late_game_foul_delta_per_game
        ),
        blocked_late_game_foul_delta_per_game=(
            config.blocked_late_game_foul_delta_per_game
        ),
        min_lookback_games=config.min_lookback_games,
        max_source_age_seconds=config.max_source_age_seconds,
        reason_codes=_row_reason_codes(
            pressure_status=pressure_status,
            absolute_foul_rate_delta_per_game=absolute_foul_rate_delta_per_game,
            absolute_late_game_foul_delta_per_game=(
                absolute_late_game_foul_delta_per_game
            ),
            lookback_games=value.lookback_games,
            source_age_seconds=source_age_seconds,
            watch_foul_rate_delta_per_game=config.watch_foul_rate_delta_per_game,
            watch_late_game_foul_delta_per_game=(
                config.watch_late_game_foul_delta_per_game
            ),
            min_lookback_games=config.min_lookback_games,
            max_source_age_seconds=config.max_source_age_seconds,
        ),
    )


def _pressure_score(
    *,
    absolute_foul_rate_delta_per_game: Decimal,
    absolute_late_game_foul_delta_per_game: Decimal,
    blocked_foul_rate_delta_per_game: Decimal,
    blocked_late_game_foul_delta_per_game: Decimal,
) -> Decimal:
    return min(
        ONE,
        max(
            _ratio(
                absolute_foul_rate_delta_per_game,
                blocked_foul_rate_delta_per_game,
            ),
            _ratio(
                absolute_late_game_foul_delta_per_game,
                blocked_late_game_foul_delta_per_game,
            ),
        ),
    )


def _pressure_status(
    *,
    absolute_foul_rate_delta_per_game: Decimal,
    absolute_late_game_foul_delta_per_game: Decimal,
    lookback_games: Decimal,
    source_age_seconds: Decimal,
    watch_foul_rate_delta_per_game: Decimal,
    blocked_foul_rate_delta_per_game: Decimal,
    watch_late_game_foul_delta_per_game: Decimal,
    blocked_late_game_foul_delta_per_game: Decimal,
    min_lookback_games: Decimal,
    max_source_age_seconds: Decimal,
) -> str:
    if (
        absolute_foul_rate_delta_per_game >= blocked_foul_rate_delta_per_game
        or absolute_late_game_foul_delta_per_game
        >= blocked_late_game_foul_delta_per_game
    ):
        return BLOCKED_STATUS
    if (
        absolute_foul_rate_delta_per_game >= watch_foul_rate_delta_per_game
        or absolute_late_game_foul_delta_per_game
        >= watch_late_game_foul_delta_per_game
        or lookback_games < min_lookback_games
        or source_age_seconds > max_source_age_seconds
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    pressure_status: str,
    absolute_foul_rate_delta_per_game: Decimal,
    absolute_late_game_foul_delta_per_game: Decimal,
    lookback_games: Decimal,
    source_age_seconds: Decimal,
    watch_foul_rate_delta_per_game: Decimal,
    watch_late_game_foul_delta_per_game: Decimal,
    min_lookback_games: Decimal,
    max_source_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if pressure_status == BLOCKED_STATUS:
        reason_codes.append("basketball_referee_foul_pressure_blocked")
    elif pressure_status == WATCH_STATUS:
        reason_codes.append("basketball_referee_foul_pressure_watch")
    else:
        reason_codes.append("basketball_referee_foul_pressure_below_threshold")
    if absolute_foul_rate_delta_per_game >= watch_foul_rate_delta_per_game:
        reason_codes.append("basketball_referee_foul_pressure_rate_delta")
    if absolute_late_game_foul_delta_per_game >= watch_late_game_foul_delta_per_game:
        reason_codes.append("basketball_referee_foul_pressure_late_game_delta")
    if lookback_games < min_lookback_games:
        reason_codes.append("basketball_referee_foul_pressure_low_sample")
    reason_codes.append(
        "basketball_referee_foul_pressure_source_stale"
        if source_age_seconds > max_source_age_seconds
        else "basketball_referee_foul_pressure_source_fresh",
    )
    return _require_reason_codes(
        "reason_codes",
        tuple(sorted(reason_codes)),
        allowed=ROW_REASON_CODES,
        require_nonempty=True,
    )


def _report_reason_codes(
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("basketball_referee_foul_pressure_digest_empty",)
    reason_codes: list[str] = []
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        reason_codes.append("basketball_referee_foul_pressure_blocked_present")
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        reason_codes.append("basketball_referee_foul_pressure_watch_present")
    if _reason_count(rows, "basketball_referee_foul_pressure_rate_delta") > ZERO:
        reason_codes.append("basketball_referee_foul_pressure_rate_delta_present")
    if _reason_count(rows, "basketball_referee_foul_pressure_late_game_delta") > ZERO:
        reason_codes.append("basketball_referee_foul_pressure_late_game_delta_present")
    if _reason_count(rows, "basketball_referee_foul_pressure_low_sample") > ZERO:
        reason_codes.append("basketball_referee_foul_pressure_low_sample_present")
    if _reason_count(rows, "basketball_referee_foul_pressure_source_stale") > ZERO:
        reason_codes.append("basketball_referee_foul_pressure_stale_source_present")
    if not reason_codes:
        reason_codes.append("basketball_referee_foul_pressure_digest_clear")
    return _require_reason_codes(
        "reason_codes",
        tuple(sorted(reason_codes)),
        allowed=REPORT_REASON_CODES,
        require_nonempty=True,
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
) -> tuple[BasketballRefereeFoulRatePressureReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("basketball_referee_foul_pressure_digest_empty",):
        return (
            BasketballRefereeFoulRatePressureReasonCodeCount(
                reason_code="basketball_referee_foul_pressure_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        BasketballRefereeFoulRatePressureReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
) -> Decimal:
    if reason_code == "basketball_referee_foul_pressure_blocked_present":
        return _status_count(rows, BLOCKED_STATUS)
    if reason_code == "basketball_referee_foul_pressure_watch_present":
        return _status_count(rows, WATCH_STATUS)
    if reason_code == "basketball_referee_foul_pressure_digest_clear":
        return _status_count(rows, PASS_STATUS)
    row_reason_code = {
        "basketball_referee_foul_pressure_late_game_delta_present": (
            "basketball_referee_foul_pressure_late_game_delta"
        ),
        "basketball_referee_foul_pressure_low_sample_present": (
            "basketball_referee_foul_pressure_low_sample"
        ),
        "basketball_referee_foul_pressure_rate_delta_present": (
            "basketball_referee_foul_pressure_rate_delta"
        ),
        "basketball_referee_foul_pressure_stale_source_present": (
            "basketball_referee_foul_pressure_source_stale"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _validate_config(
    config: BasketballRefereeFoulRatePressureDigestConfig,
) -> None:
    if (
        config.config_version
        != DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_PRESSURE_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if config.watch_foul_rate_delta_per_game > config.blocked_foul_rate_delta_per_game:
        raise ValueError(
            "watch_foul_rate_delta_per_game must not exceed "
            "blocked_foul_rate_delta_per_game",
        )
    if (
        config.watch_late_game_foul_delta_per_game
        > config.blocked_late_game_foul_delta_per_game
    ):
        raise ValueError(
            "watch_late_game_foul_delta_per_game must not exceed "
            "blocked_late_game_foul_delta_per_game",
        )


def _validate_row(row: BasketballRefereeFoulRatePressureDigestRow) -> None:
    if row.foul_rate_delta_per_game != _quantize_decimal(
        row.crew_fouls_per_game - row.league_fouls_per_game,
    ):
        raise ValueError("foul_rate_delta_per_game must match foul rate inputs")
    if row.absolute_foul_rate_delta_per_game != _quantize_decimal(
        abs(row.foul_rate_delta_per_game),
    ):
        raise ValueError(
            "absolute_foul_rate_delta_per_game must match foul_rate_delta_per_game",
        )
    if row.absolute_late_game_foul_delta_per_game != _quantize_decimal(
        abs(row.late_game_foul_delta_per_game),
    ):
        raise ValueError(
            "absolute_late_game_foul_delta_per_game must match "
            "late_game_foul_delta_per_game",
        )
    if row.pressure_score != _pressure_score(
        absolute_foul_rate_delta_per_game=row.absolute_foul_rate_delta_per_game,
        absolute_late_game_foul_delta_per_game=(
            row.absolute_late_game_foul_delta_per_game
        ),
        blocked_foul_rate_delta_per_game=row.blocked_foul_rate_delta_per_game,
        blocked_late_game_foul_delta_per_game=(
            row.blocked_late_game_foul_delta_per_game
        ),
    ):
        raise ValueError("pressure_score must match row factors")
    expected_status = _pressure_status(
        absolute_foul_rate_delta_per_game=row.absolute_foul_rate_delta_per_game,
        absolute_late_game_foul_delta_per_game=(
            row.absolute_late_game_foul_delta_per_game
        ),
        lookback_games=row.lookback_games,
        source_age_seconds=row.source_age_seconds,
        watch_foul_rate_delta_per_game=row.watch_foul_rate_delta_per_game,
        blocked_foul_rate_delta_per_game=row.blocked_foul_rate_delta_per_game,
        watch_late_game_foul_delta_per_game=row.watch_late_game_foul_delta_per_game,
        blocked_late_game_foul_delta_per_game=(
            row.blocked_late_game_foul_delta_per_game
        ),
        min_lookback_games=row.min_lookback_games,
        max_source_age_seconds=row.max_source_age_seconds,
    )
    if row.pressure_status != expected_status:
        raise ValueError("pressure_status must match row factors")
    if row.reason_codes != _row_reason_codes(
        pressure_status=row.pressure_status,
        absolute_foul_rate_delta_per_game=row.absolute_foul_rate_delta_per_game,
        absolute_late_game_foul_delta_per_game=(
            row.absolute_late_game_foul_delta_per_game
        ),
        lookback_games=row.lookback_games,
        source_age_seconds=row.source_age_seconds,
        watch_foul_rate_delta_per_game=row.watch_foul_rate_delta_per_game,
        watch_late_game_foul_delta_per_game=row.watch_late_game_foul_delta_per_game,
        min_lookback_games=row.min_lookback_games,
        max_source_age_seconds=row.max_source_age_seconds,
    ):
        raise ValueError("pressure_status must match reason_codes")


def _validate_report(report: BasketballRefereeFoulRatePressureDigestReport) -> None:
    if report.config_version != (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_PRESSURE_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.elevated_foul_rate_count != _reason_count(
        report.rows,
        "basketball_referee_foul_pressure_rate_delta",
    ):
        raise ValueError("elevated_foul_rate_count must match rows")
    if report.late_game_pressure_count != _reason_count(
        report.rows,
        "basketball_referee_foul_pressure_late_game_delta",
    ):
        raise ValueError("late_game_pressure_count must match rows")
    if report.low_sample_count != _reason_count(
        report.rows,
        "basketball_referee_foul_pressure_low_sample",
    ):
        raise ValueError("low_sample_count must match rows")
    if report.max_pressure_score != _max_row_decimal(report.rows, "pressure_score"):
        raise ValueError("max_pressure_score must match rows")
    if report.average_pressure_score != _ratio(
        _sum_decimal(row.pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_pressure_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _require_observations(
    observations: Iterable[BasketballRefereeFoulRatePressureObservation],
) -> tuple[BasketballRefereeFoulRatePressureObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain BasketballRefereeFoulRatePressureObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for value in normalized:
        if type(value) is not BasketballRefereeFoulRatePressureObservation:
            raise ValueError(
                "observations must contain BasketballRefereeFoulRatePressureObservation",
            )
        _require_hard_flags(value, "observation")
        if value.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(value.source_id)
    return normalized


def _require_rows(
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
) -> tuple[BasketballRefereeFoulRatePressureDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = rows
    for row in normalized:
        if type(row) is not BasketballRefereeFoulRatePressureDigestRow:
            raise ValueError(
                "rows must contain BasketballRefereeFoulRatePressureDigestRow",
            )
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    seen_source_ids: set[str] = set()
    for row in normalized:
        _require_hard_flags(row, "row")
        _validate_row(row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return normalized


def _require_reason_code_counts(
    values: tuple[BasketballRefereeFoulRatePressureReasonCodeCount, ...],
) -> tuple[BasketballRefereeFoulRatePressureReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = values
    for value in normalized:
        if type(value) is not BasketballRefereeFoulRatePressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "BasketballRefereeFoulRatePressureReasonCodeCount",
            )
    if normalized != tuple(sorted(normalized, key=lambda value: value.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    for value in normalized:
        _require_hard_flags(value, "reason_code_count")
    return normalized


def _digest_status(
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _row_sort_key(
    row: BasketballRefereeFoulRatePressureDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.pressure_status],
        -row.pressure_score,
        row.event_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_status == status))


def _reason_count(
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[BasketballRefereeFoulRatePressureDigestRow, ...],
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
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six-decimal precision")
    decimal_value = _quantize_decimal(value)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use six-decimal precision")
    return decimal_value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_payload_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_DELTA:
        raise ValueError(f"{field_name} must be UTC before payload serialization")
    return value


ZERO_TIME_DELTA = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allowed: tuple[str, ...] | None = None,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = values
    if require_nonempty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    for value in normalized:
        _require_canonical_string("reason_code", value)
        if allowed is not None and value not in allowed:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _require_hard_flags(value: object, label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{_require_decimal('payload_decimal', value):.6f}"
    if isinstance(value, datetime):
        return _require_payload_utc_datetime("payload_datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value


def _require_payload_public_dataclass(value: object) -> None:
    if type(value) not in PUBLIC_DATACLASS_TYPES:
        raise ValueError("payload public dataclass must be supported")
    _require_payload_field_values(value)
    if type(value) is BasketballRefereeFoulRatePressureDigestConfig:
        _validate_config(value)
        _require_hard_flags(value, "config")
    elif type(value) is BasketballRefereeFoulRatePressureObservation:
        _require_hard_flags(value, "observation")
    elif type(value) is BasketballRefereeFoulRatePressureDigestRow:
        _validate_row(value)
        _require_hard_flags(value, "row")
    elif type(value) is BasketballRefereeFoulRatePressureReasonCodeCount:
        _require_hard_flags(value, "reason_code_count")
    elif type(value) is BasketballRefereeFoulRatePressureDigestReport:
        _validate_report(value)
        _require_hard_flags(value, "report")


def _require_payload_field_values(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if isinstance(field_value, Decimal):
            _require_decimal(field.name, field_value)
        elif isinstance(field_value, datetime):
            _require_payload_utc_datetime(field.name, field_value)
        elif is_dataclass(field_value) and not isinstance(field_value, type):
            if type(field_value) not in PUBLIC_DATACLASS_TYPES:
                raise ValueError("payload public dataclass must be supported")
        elif isinstance(field_value, tuple):
            _require_payload_tuple(field.name, field_value)
        elif isinstance(field_value, (str, bool)) or field_value is None:
            continue
        else:
            raise ValueError(f"{field.name} must be payload-safe")


def _require_payload_tuple(field_name: str, values: tuple[object, ...]) -> None:
    for value in values:
        if isinstance(value, Decimal):
            _require_decimal(field_name, value)
        elif isinstance(value, datetime):
            _require_payload_utc_datetime(field_name, value)
        elif is_dataclass(value) and not isinstance(value, type):
            if type(value) not in PUBLIC_DATACLASS_TYPES:
                raise ValueError("payload public dataclass must be supported")
        elif isinstance(value, tuple):
            _require_payload_tuple(field_name, value)
        elif isinstance(value, (str, bool)) or value is None:
            continue
        else:
            raise ValueError(f"{field_name} must contain payload-safe values")


PUBLIC_DATACLASS_TYPES = {
    BasketballRefereeFoulRatePressureDigestConfig,
    BasketballRefereeFoulRatePressureObservation,
    BasketballRefereeFoulRatePressureDigestRow,
    BasketballRefereeFoulRatePressureReasonCodeCount,
    BasketballRefereeFoulRatePressureDigestReport,
}
