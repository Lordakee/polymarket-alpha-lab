"""Pure Phase 1 reducer for basketball referee foul-rate shift signals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-referee-foul-rate-shift-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
ROW_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
DIGEST_STATUSES = ROW_STATUSES

STALE_OBSERVATION_REASON = "basketball_referee_foul_rate_shift_stale_observation"
FOUL_RATE_BLOCKED_REASON = "basketball_referee_foul_rate_shift_foul_rate_blocked"
TECHNICAL_FREE_THROW_BLOCKED_REASON = (
    "basketball_referee_foul_rate_shift_technical_free_throw_blocked"
)
FOUL_RATE_WATCH_REASON = "basketball_referee_foul_rate_shift_foul_rate_watch"
TECHNICAL_FREE_THROW_WATCH_REASON = (
    "basketball_referee_foul_rate_shift_technical_free_throw_watch"
)
THIN_SAMPLE_REASON = "basketball_referee_foul_rate_shift_thin_sample"
PASS_REASON = "basketball_referee_foul_rate_shift_pass"
PASSED_REASON = "basketball_referee_foul_rate_shift_passed"
EMPTY_REASON = "basketball_referee_foul_rate_shift_empty"

ROW_REASON_CODES = (
    STALE_OBSERVATION_REASON,
    FOUL_RATE_BLOCKED_REASON,
    TECHNICAL_FREE_THROW_BLOCKED_REASON,
    FOUL_RATE_WATCH_REASON,
    TECHNICAL_FREE_THROW_WATCH_REASON,
    THIN_SAMPLE_REASON,
    PASS_REASON,
)
DIGEST_REASON_CODES = (
    STALE_OBSERVATION_REASON,
    FOUL_RATE_BLOCKED_REASON,
    TECHNICAL_FREE_THROW_BLOCKED_REASON,
    FOUL_RATE_WATCH_REASON,
    TECHNICAL_FREE_THROW_WATCH_REASON,
    THIN_SAMPLE_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))

NEXT_STEP_BY_STATUS = {
    BLOCKED_STATUS: "block_report_only_basketball_referee_foul_rate_shift_review",
    WATCH_STATUS: "watch_report_only_basketball_referee_foul_rate_shift_review",
    PASS_STATUS: "continue_report_only_basketball_referee_foul_rate_shift_monitoring",
}
STATUS_RANK = {
    BLOCKED_STATUS: 0,
    WATCH_STATUS: 1,
    PASS_STATUS: 2,
}

_BLOCKED_WORDS = (
    "pay" "load_" "json",
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "au" "th",
    "se" "cret",
    "pri" "vate",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "tra" "de",
    "sign" "ing",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_SHIFT_DIGEST_CONFIG_VERSION",
    "MarketResearchBasketballRefereeFoulRateShiftDigestConfig",
    "MarketResearchBasketballRefereeFoulRateShiftDigestSignal",
    "MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount",
    "MarketResearchBasketballRefereeFoulRateShiftDigestRow",
    "MarketResearchBasketballRefereeFoulRateShiftDigestReport",
    "build_market_research_basketball_referee_foul_rate_shift_digest",
    "market_research_basketball_referee_foul_rate_shift_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBasketballRefereeFoulRateShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_SHIFT_DIGEST_CONFIG_VERSION
    )
    blocked_foul_rate_delta_threshold: Decimal = Decimal("6.000000")
    watch_foul_rate_delta_threshold: Decimal = Decimal("3.000000")
    blocked_technical_free_throw_delta_threshold: Decimal = Decimal("2.000000")
    watch_technical_free_throw_delta_threshold: Decimal = Decimal("1.000000")
    minimum_crew_games_sample_threshold: Decimal = Decimal("10.000000")
    stale_observation_seconds_threshold: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballRefereeFoulRateShiftDigestConfig:
            raise TypeError(
                "MarketResearchBasketballRefereeFoulRateShiftDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballRefereeFoulRateShiftDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchBasketballRefereeFoulRateShiftDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "blocked_foul_rate_delta_threshold",
            "watch_foul_rate_delta_threshold",
            "blocked_technical_free_throw_delta_threshold",
            "watch_technical_free_throw_delta_threshold",
            "minimum_crew_games_sample_threshold",
            "stale_observation_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_foul_rate_delta_threshold < self.watch_foul_rate_delta_threshold:
            raise ValueError(
                "blocked_foul_rate_delta_threshold must be at least watch threshold",
            )
        if (
            self.blocked_technical_free_throw_delta_threshold
            < self.watch_technical_free_throw_delta_threshold
        ):
            raise ValueError(
                "blocked_technical_free_throw_delta_threshold "
                "must be at least watch threshold",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballRefereeFoulRateShiftDigestSignal:
    fixture_id: str
    crew_key: str
    league_key: str
    home_team_key: str
    away_team_key: str
    source_ref: str
    observed_at: datetime
    crew_games_sample: Decimal
    foul_rate_shift_per_game: Decimal
    technical_free_throw_shift_per_game: Decimal
    market_sensitivity_score: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_SHIFT_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballRefereeFoulRateShiftDigestSignal:
            raise TypeError(
                "MarketResearchBasketballRefereeFoulRateShiftDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballRefereeFoulRateShiftDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchBasketballRefereeFoulRateShiftDigestSignal",
            )
        for field_name in (
            "fixture_id",
            "crew_key",
            "league_key",
            "home_team_key",
            "away_team_key",
            "source_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "crew_games_sample",
            _normalize_nonnegative_decimal("crew_games_sample", self.crew_games_sample),
        )
        for field_name in (
            "foul_rate_shift_per_game",
            "technical_free_throw_shift_per_game",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_sensitivity_score",
            _normalize_ratio_decimal("market_sensitivity_score", self.market_sensitivity_score),
        )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount:
    reason_code: str
    fixture_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "fixture_count",
            _normalize_nonnegative_decimal("fixture_count", self.fixture_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballRefereeFoulRateShiftDigestRow:
    fixture_id: str
    crew_key: str
    league_key: str
    home_team_key: str
    away_team_key: str
    signal_count: Decimal
    observed_at_latest: datetime
    observation_age_seconds: Decimal
    crew_games_sample_max: Decimal
    foul_rate_shift_per_game_max: Decimal
    technical_free_throw_shift_per_game_max: Decimal
    market_sensitivity_score_max: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballRefereeFoulRateShiftDigestRow:
            raise TypeError(
                "MarketResearchBasketballRefereeFoulRateShiftDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballRefereeFoulRateShiftDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchBasketballRefereeFoulRateShiftDigestRow",
            )
        for field_name in (
            "fixture_id",
            "crew_key",
            "league_key",
            "home_team_key",
            "away_team_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "observed_at_latest",
            _as_utc("observed_at_latest", self.observed_at_latest),
        )
        for field_name in (
            "observation_age_seconds",
            "crew_games_sample_max",
            "foul_rate_shift_per_game_max",
            "technical_free_throw_shift_per_game_max",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_sensitivity_score_max",
            _normalize_ratio_decimal(
                "market_sensitivity_score_max",
                self.market_sensitivity_score_max,
            ),
        )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballRefereeFoulRateShiftDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    fixture_count: Decimal
    signal_count: Decimal
    blocked_fixture_count: Decimal
    watch_fixture_count: Decimal
    pass_fixture_count: Decimal
    stale_observation_fixture_count: Decimal
    foul_rate_shift_fixture_count: Decimal
    technical_free_throw_shift_fixture_count: Decimal
    thin_sample_fixture_count: Decimal
    blocked_foul_rate_delta_threshold: Decimal
    watch_foul_rate_delta_threshold: Decimal
    blocked_technical_free_throw_delta_threshold: Decimal
    watch_technical_free_throw_delta_threshold: Decimal
    minimum_crew_games_sample_threshold: Decimal
    stale_observation_seconds_threshold: Decimal
    max_observation_age_seconds: Decimal | None
    max_foul_rate_shift_per_game: Decimal | None
    max_technical_free_throw_shift_per_game: Decimal | None
    max_market_sensitivity_score: Decimal | None
    rows: tuple[MarketResearchBasketballRefereeFoulRateShiftDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballRefereeFoulRateShiftDigestReport:
            raise TypeError(
                "MarketResearchBasketballRefereeFoulRateShiftDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballRefereeFoulRateShiftDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchBasketballRefereeFoulRateShiftDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "fixture_count",
            "signal_count",
            "blocked_fixture_count",
            "watch_fixture_count",
            "pass_fixture_count",
            "stale_observation_fixture_count",
            "foul_rate_shift_fixture_count",
            "technical_free_throw_shift_fixture_count",
            "thin_sample_fixture_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_foul_rate_delta_threshold",
            "watch_foul_rate_delta_threshold",
            "blocked_technical_free_throw_delta_threshold",
            "watch_technical_free_throw_delta_threshold",
            "minimum_crew_games_sample_threshold",
            "stale_observation_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_observation_age_seconds",
            "max_foul_rate_shift_per_game",
            "max_technical_free_throw_shift_per_game",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_market_sensitivity_score",
            _normalize_optional_ratio_decimal(
                "max_market_sensitivity_score",
                self.max_market_sensitivity_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
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


def build_market_research_basketball_referee_foul_rate_shift_digest(
    signals: Iterable[MarketResearchBasketballRefereeFoulRateShiftDigestSignal],
    *,
    config: MarketResearchBasketballRefereeFoulRateShiftDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballRefereeFoulRateShiftDigestReport:
    if type(config) is not MarketResearchBasketballRefereeFoulRateShiftDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballRefereeFoulRateShiftDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    rows = _build_rows(signal_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    digest_status = _digest_status(rows)
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchBasketballRefereeFoulRateShiftDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        fixture_count=_decimal_count(len(rows)),
        signal_count=_decimal_count(len(signal_items)),
        blocked_fixture_count=_decimal_count(
            sum(1 for row in rows if row.row_status == BLOCKED_STATUS),
        ),
        watch_fixture_count=_decimal_count(
            sum(1 for row in rows if row.row_status == WATCH_STATUS),
        ),
        pass_fixture_count=_decimal_count(
            sum(1 for row in rows if row.row_status == PASS_STATUS),
        ),
        stale_observation_fixture_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        foul_rate_shift_fixture_count=_decimal_count(
            sum(
                1
                for row in rows
                if (
                    FOUL_RATE_BLOCKED_REASON in row.reason_codes
                    or FOUL_RATE_WATCH_REASON in row.reason_codes
                )
            ),
        ),
        technical_free_throw_shift_fixture_count=_decimal_count(
            sum(
                1
                for row in rows
                if (
                    TECHNICAL_FREE_THROW_BLOCKED_REASON in row.reason_codes
                    or TECHNICAL_FREE_THROW_WATCH_REASON in row.reason_codes
                )
            ),
        ),
        thin_sample_fixture_count=_reason_count(rows, THIN_SAMPLE_REASON),
        blocked_foul_rate_delta_threshold=config.blocked_foul_rate_delta_threshold,
        watch_foul_rate_delta_threshold=config.watch_foul_rate_delta_threshold,
        blocked_technical_free_throw_delta_threshold=(
            config.blocked_technical_free_throw_delta_threshold
        ),
        watch_technical_free_throw_delta_threshold=(
            config.watch_technical_free_throw_delta_threshold
        ),
        minimum_crew_games_sample_threshold=config.minimum_crew_games_sample_threshold,
        stale_observation_seconds_threshold=config.stale_observation_seconds_threshold,
        max_observation_age_seconds=_max_or_none(row.observation_age_seconds for row in rows),
        max_foul_rate_shift_per_game=_max_or_none(
            row.foul_rate_shift_per_game_max for row in rows
        ),
        max_technical_free_throw_shift_per_game=_max_or_none(
            row.technical_free_throw_shift_per_game_max for row in rows
        ),
        max_market_sensitivity_score=_max_or_none(
            row.market_sensitivity_score_max for row in rows
        ),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (signal.source_ref, signal.signal_config_version)
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_basketball_referee_foul_rate_shift_digest_payload(
    report: MarketResearchBasketballRefereeFoulRateShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballRefereeFoulRateShiftDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBasketballRefereeFoulRateShiftDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _build_rows(
    signals: tuple[MarketResearchBasketballRefereeFoulRateShiftDigestSignal, ...],
    *,
    config: MarketResearchBasketballRefereeFoulRateShiftDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBasketballRefereeFoulRateShiftDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str, str],
        list[MarketResearchBasketballRefereeFoulRateShiftDigestSignal],
    ] = {}
    for signal in signals:
        grouped.setdefault(
            (
                signal.fixture_id,
                signal.crew_key,
                signal.league_key,
                signal.home_team_key,
                signal.away_team_key,
            ),
            [],
        ).append(signal)

    rows = []
    for (
        fixture_id,
        crew_key,
        league_key,
        home_team_key,
        away_team_key,
    ), fixture_signals in grouped.items():
        sorted_signals = sorted(
            fixture_signals,
            key=lambda item: (item.observed_at, item.source_ref),
        )
        observed_at_latest = max(item.observed_at for item in sorted_signals)
        observation_age_seconds = _quantize(
            Decimal(str((generated_at - observed_at_latest).total_seconds())),
        )
        if observation_age_seconds < ZERO:
            raise ValueError("observed_at values must be at or before generated_at")

        crew_games_sample_max = max(item.crew_games_sample for item in sorted_signals)
        foul_rate_shift_per_game_max = max(
            item.foul_rate_shift_per_game for item in sorted_signals
        )
        technical_free_throw_shift_per_game_max = max(
            item.technical_free_throw_shift_per_game for item in sorted_signals
        )
        market_sensitivity_score_max = max(
            item.market_sensitivity_score for item in sorted_signals
        )

        reason_codes = []
        if observation_age_seconds >= config.stale_observation_seconds_threshold:
            reason_codes.append(STALE_OBSERVATION_REASON)
        if foul_rate_shift_per_game_max >= config.blocked_foul_rate_delta_threshold:
            reason_codes.append(FOUL_RATE_BLOCKED_REASON)
        elif foul_rate_shift_per_game_max >= config.watch_foul_rate_delta_threshold:
            reason_codes.append(FOUL_RATE_WATCH_REASON)
        if (
            technical_free_throw_shift_per_game_max
            >= config.blocked_technical_free_throw_delta_threshold
        ):
            reason_codes.append(TECHNICAL_FREE_THROW_BLOCKED_REASON)
        elif (
            technical_free_throw_shift_per_game_max
            >= config.watch_technical_free_throw_delta_threshold
        ):
            reason_codes.append(TECHNICAL_FREE_THROW_WATCH_REASON)
        if crew_games_sample_max < config.minimum_crew_games_sample_threshold:
            reason_codes.append(THIN_SAMPLE_REASON)

        row_status = _row_status_from_reason_codes(tuple(reason_codes))
        if not reason_codes:
            reason_codes.append(PASS_REASON)
        else:
            reason_codes = list(_sort_reason_codes(tuple(reason_codes), ROW_REASON_CODES))

        rows.append(
            MarketResearchBasketballRefereeFoulRateShiftDigestRow(
                fixture_id=fixture_id,
                crew_key=crew_key,
                league_key=league_key,
                home_team_key=home_team_key,
                away_team_key=away_team_key,
                signal_count=_decimal_count(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                observation_age_seconds=observation_age_seconds,
                crew_games_sample_max=crew_games_sample_max,
                foul_rate_shift_per_game_max=foul_rate_shift_per_game_max,
                technical_free_throw_shift_per_game_max=(
                    technical_free_throw_shift_per_game_max
                ),
                market_sensitivity_score_max=market_sensitivity_score_max,
                row_status=row_status,
                reason_codes=tuple(reason_codes),
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            STALE_OBSERVATION_REASON,
            FOUL_RATE_BLOCKED_REASON,
            TECHNICAL_FREE_THROW_BLOCKED_REASON,
        )
        for reason_code in reason_codes
    ):
        return BLOCKED_STATUS
    if reason_codes:
        return WATCH_STATUS
    return PASS_STATUS


def _digest_status(
    rows: tuple[MarketResearchBasketballRefereeFoulRateShiftDigestRow, ...],
) -> str:
    if any(row.row_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.row_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount(
            reason_code=reason_code,
            fixture_count=_decimal_count(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchBasketballRefereeFoulRateShiftDigestSignal],
) -> tuple[MarketResearchBasketballRefereeFoulRateShiftDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchBasketballRefereeFoulRateShiftDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchBasketballRefereeFoulRateShiftDigestSignal records",
            )
        _require_flags("signal", signal)
        key = (signal.fixture_id, signal.crew_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate fixture/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBasketballRefereeFoulRateShiftDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchBasketballRefereeFoulRateShiftDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBasketballRefereeFoulRateShiftDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError("signal_config_versions entries must be source/version pairs")
        source_ref, config_version = item
        _require_canonical_string("signal_config_versions source_ref", source_ref)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("signal_config_versions source_ref", source_ref)
        _reject_sensitive_text("signal_config_versions config_version", config_version)
        if source_ref in seen_refs:
            raise ValueError("signal_config_versions source_ref values must be unique")
        seen_refs.add(source_ref)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount "
                "records",
            )
    if normalized != tuple(
        sorted(normalized, key=lambda item: DIGEST_REASON_CODES.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _validate_row(row: MarketResearchBasketballRefereeFoulRateShiftDigestRow) -> None:
    expected_status = _row_status_from_reason_codes(
        tuple(reason_code for reason_code in row.reason_codes if reason_code != PASS_REASON),
    )
    if row.row_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.row_status == PASS_STATUS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use the pass reason")
    if row.row_status != PASS_STATUS and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not use the pass reason")


def _validate_report(
    report: MarketResearchBasketballRefereeFoulRateShiftDigestReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.fixture_count != _decimal_count(len(report.rows)):
        raise ValueError("fixture_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.blocked_fixture_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status == BLOCKED_STATUS),
    ):
        raise ValueError("blocked_fixture_count must match rows")
    if report.watch_fixture_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status == WATCH_STATUS),
    ):
        raise ValueError("watch_fixture_count must match rows")
    if report.pass_fixture_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status == PASS_STATUS),
    ):
        raise ValueError("pass_fixture_count must match rows")
    if (
        report.fixture_count
        != report.blocked_fixture_count
        + report.watch_fixture_count
        + report.pass_fixture_count
    ):
        raise ValueError("fixture status counts must reconcile")
    if report.stale_observation_fixture_count != _reason_count(
        report.rows,
        STALE_OBSERVATION_REASON,
    ):
        raise ValueError("stale_observation_fixture_count must match rows")
    if report.foul_rate_shift_fixture_count != _decimal_count(
        sum(
            1
            for row in report.rows
            if (
                FOUL_RATE_BLOCKED_REASON in row.reason_codes
                or FOUL_RATE_WATCH_REASON in row.reason_codes
            )
        ),
    ):
        raise ValueError("foul_rate_shift_fixture_count must match rows")
    if report.technical_free_throw_shift_fixture_count != _decimal_count(
        sum(
            1
            for row in report.rows
            if (
                TECHNICAL_FREE_THROW_BLOCKED_REASON in row.reason_codes
                or TECHNICAL_FREE_THROW_WATCH_REASON in row.reason_codes
            )
        ),
    ):
        raise ValueError("technical_free_throw_shift_fixture_count must match rows")
    if report.thin_sample_fixture_count != _reason_count(report.rows, THIN_SAMPLE_REASON):
        raise ValueError("thin_sample_fixture_count must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.digest_status == PASS_STATUS and any(
        reason_code not in (PASSED_REASON, EMPTY_REASON)
        for reason_code in report.reason_codes
    ):
        raise ValueError("pass reports must not include watch reasons")
    if report.digest_status != PASS_STATUS and not report.reason_code_counts:
        raise ValueError("non-pass reports require reason counts")
    if report.max_observation_age_seconds != _max_or_none(
        row.observation_age_seconds for row in report.rows
    ):
        raise ValueError("max_observation_age_seconds must match rows")
    if report.max_foul_rate_shift_per_game != _max_or_none(
        row.foul_rate_shift_per_game_max for row in report.rows
    ):
        raise ValueError("max_foul_rate_shift_per_game must match rows")
    if report.max_technical_free_throw_shift_per_game != _max_or_none(
        row.technical_free_throw_shift_per_game_max for row in report.rows
    ):
        raise ValueError("max_technical_free_throw_shift_per_game must match rows")
    if report.max_market_sensitivity_score != _max_or_none(
        row.market_sensitivity_score_max for row in report.rows
    ):
        raise ValueError("max_market_sensitivity_score must match rows")
    expected_counts = _reason_code_counts(
        tuple(
            reason_code
            for row in report.rows
            for reason_code in row.reason_codes
            if reason_code != PASS_REASON
        ),
    )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _reason_count(
    rows: tuple[MarketResearchBasketballRefereeFoulRateShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchBasketballRefereeFoulRateShiftDigestRow,
) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.row_status],
        -row.foul_rate_shift_per_game_max,
        -row.technical_free_throw_shift_per_game_max,
        -row.market_sensitivity_score_max,
        -row.observation_age_seconds,
        row.fixture_id,
        row.crew_key,
    )


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value.quantize(QUANTUM), "f")
    if isinstance(value, datetime):
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if is_dataclass(value):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


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
        raise ValueError(f"{name} must be unique")
    sorted_codes = _sort_reason_codes(reason_codes, allowed)
    if reason_codes != sorted_codes:
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} entries must be strings")
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} contains unknown reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(blocked in lowered for blocked in _BLOCKED_WORDS):
        raise ValueError(f"{name} contains unsafe source detail")


def _require_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio_decimal(field_name, value)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value must fit six decimal places") from exc


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)
