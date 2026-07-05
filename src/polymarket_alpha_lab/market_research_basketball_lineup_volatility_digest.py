"""Pure Phase 1 reducer for basketball lineup volatility."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_LINEUP_VOLATILITY_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-lineup-volatility-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
CLEAR_STATUS = "clear"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (CLEAR_STATUS, WATCH_STATUS)

MINUTES_DELTA_REASON = "basketball_lineup_volatility_minutes_delta_high"
SOURCE_DISAGREEMENT_REASON = (
    "basketball_lineup_volatility_source_disagreement_high"
)
STALE_UPDATE_REASON = "basketball_lineup_volatility_stale_update_cadence"
STARTER_FLIP_REASON = "basketball_lineup_volatility_starter_flip_high"
CLEAR_REASON = "basketball_lineup_volatility_clear"
PASSED_REASON = "basketball_lineup_volatility_passed"
EMPTY_REASON = "basketball_lineup_volatility_empty"

ROW_REASON_CODES = (
    MINUTES_DELTA_REASON,
    SOURCE_DISAGREEMENT_REASON,
    STALE_UPDATE_REASON,
    STARTER_FLIP_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    MINUTES_DELTA_REASON,
    SOURCE_DISAGREEMENT_REASON,
    STALE_UPDATE_REASON,
    STARTER_FLIP_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_basketball_lineup_volatility_monitoring",
    WATCH_STATUS: "review_report_only_basketball_lineup_volatility",
    BLOCKED_STATUS: "block_report_only_basketball_lineup_volatility",
}

_BLOCKED_WORDS = (
    "mar" "ket_" "slug",
    "ques" "tion",
    "pay" "load_" "json",
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "sign" "ing",
    "api_" "key",
    "private_" "key",
    "sec" "ret",
    "to" "ken",
    "ex" "change",
    "can" "cel",
    "re" "place",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_LINEUP_VOLATILITY_DIGEST_CONFIG_VERSION",
    "MarketResearchBasketballLineupVolatilityDigestConfig",
    "MarketResearchBasketballLineupVolatilityDigestSignal",
    "MarketResearchBasketballLineupVolatilityDigestReasonCodeCount",
    "MarketResearchBasketballLineupVolatilityDigestRow",
    "MarketResearchBasketballLineupVolatilityDigestReport",
    "build_market_research_basketball_lineup_volatility_digest",
    "market_research_basketball_lineup_volatility_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBasketballLineupVolatilityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_LINEUP_VOLATILITY_DIGEST_CONFIG_VERSION
    )
    volatility_score_threshold: Decimal = Decimal("0.250000")
    minutes_delta_threshold: Decimal = Decimal("6.000000")
    starter_flip_threshold: Decimal = Decimal("1")
    source_disagreement_threshold: Decimal = Decimal("1")
    stale_update_seconds_threshold: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLineupVolatilityDigestConfig:
            raise TypeError(
                "MarketResearchBasketballLineupVolatilityDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLineupVolatilityDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchBasketballLineupVolatilityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "volatility_score_threshold",
            "minutes_delta_threshold",
            "starter_flip_threshold",
            "source_disagreement_threshold",
            "stale_update_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineupVolatilityDigestSignal:
    condition_id: str
    lineup_key: str
    league_key: str
    team_key: str
    player_key: str
    source_ref: str
    observed_at: datetime
    projected_minutes: Decimal
    starter_probability: Decimal
    status_rank: Decimal
    source_disagreement_count: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_LINEUP_VOLATILITY_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLineupVolatilityDigestSignal:
            raise TypeError(
                "MarketResearchBasketballLineupVolatilityDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLineupVolatilityDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchBasketballLineupVolatilityDigestSignal",
            )
        for field_name in (
            "condition_id",
            "lineup_key",
            "league_key",
            "team_key",
            "player_key",
            "source_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "projected_minutes",
            _normalize_nonnegative_decimal("projected_minutes", self.projected_minutes),
        )
        object.__setattr__(
            self,
            "starter_probability",
            _normalize_ratio_decimal("starter_probability", self.starter_probability),
        )
        for field_name in ("status_rank", "source_disagreement_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineupVolatilityDigestReasonCodeCount:
    reason_code: str
    lineup_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLineupVolatilityDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBasketballLineupVolatilityDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLineupVolatilityDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchBasketballLineupVolatilityDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "lineup_count",
            _normalize_nonnegative_whole_decimal("lineup_count", self.lineup_count),
        )
        if self.lineup_count <= ZERO:
            raise ValueError("lineup_count must be positive")
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineupVolatilityDigestRow:
    condition_id: str
    lineup_key: str
    league_key: str
    team_key: str
    player_key: str
    signal_count: Decimal
    observed_at_latest: datetime
    minutes_min: Decimal
    minutes_max: Decimal
    minutes_delta: Decimal
    starter_probability_min: Decimal
    starter_probability_max: Decimal
    starter_probability_delta: Decimal
    status_rank_min: Decimal
    status_rank_max: Decimal
    status_rank_delta: Decimal
    source_disagreement_count: Decimal
    update_age_seconds: Decimal
    volatility_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLineupVolatilityDigestRow:
            raise TypeError(
                "MarketResearchBasketballLineupVolatilityDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLineupVolatilityDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchBasketballLineupVolatilityDigestRow",
            )
        for field_name in (
            "condition_id",
            "lineup_key",
            "league_key",
            "team_key",
            "player_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_whole_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "observed_at_latest",
            _as_utc("observed_at_latest", self.observed_at_latest),
        )
        for field_name in (
            "minutes_min",
            "minutes_max",
            "minutes_delta",
            "starter_probability_min",
            "starter_probability_max",
            "starter_probability_delta",
            "status_rank_min",
            "status_rank_max",
            "status_rank_delta",
            "source_disagreement_count",
            "update_age_seconds",
            "volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "starter_probability_min",
            "starter_probability_max",
            "starter_probability_delta",
            "volatility_score",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
        for field_name in ("status_rank_min", "status_rank_max", "status_rank_delta"):
            if getattr(self, field_name) != getattr(self, field_name).to_integral_value():
                raise ValueError(f"{field_name} must be whole")
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballLineupVolatilityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    lineup_count: Decimal
    clear_lineup_count: Decimal
    watch_lineup_count: Decimal
    signal_count: Decimal
    high_minutes_delta_lineup_count: Decimal
    starter_flip_lineup_count: Decimal
    source_disagreement_lineup_count: Decimal
    stale_update_lineup_count: Decimal
    volatility_score_threshold: Decimal
    minutes_delta_threshold: Decimal
    starter_flip_threshold: Decimal
    source_disagreement_threshold: Decimal
    stale_update_seconds_threshold: Decimal
    max_minutes_delta: Decimal | None
    max_starter_probability_delta: Decimal | None
    max_status_rank_delta: Decimal | None
    max_update_age_seconds: Decimal | None
    rows: tuple[MarketResearchBasketballLineupVolatilityDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballLineupVolatilityDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLineupVolatilityDigestReport:
            raise TypeError(
                "MarketResearchBasketballLineupVolatilityDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLineupVolatilityDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchBasketballLineupVolatilityDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "lineup_count",
            "clear_lineup_count",
            "watch_lineup_count",
            "signal_count",
            "high_minutes_delta_lineup_count",
            "starter_flip_lineup_count",
            "source_disagreement_lineup_count",
            "stale_update_lineup_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "volatility_score_threshold",
            "minutes_delta_threshold",
            "starter_flip_threshold",
            "source_disagreement_threshold",
            "stale_update_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_minutes_delta",
            "max_starter_probability_delta",
            "max_status_rank_delta",
            "max_update_age_seconds",
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


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchBasketballLineupVolatilityDigestConfig,
    MarketResearchBasketballLineupVolatilityDigestSignal,
    MarketResearchBasketballLineupVolatilityDigestReasonCodeCount,
    MarketResearchBasketballLineupVolatilityDigestRow,
    MarketResearchBasketballLineupVolatilityDigestReport,
)


def build_market_research_basketball_lineup_volatility_digest(
    signals: Iterable[MarketResearchBasketballLineupVolatilityDigestSignal],
    *,
    config: MarketResearchBasketballLineupVolatilityDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballLineupVolatilityDigestReport:
    if type(config) is not MarketResearchBasketballLineupVolatilityDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballLineupVolatilityDigestConfig",
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
        if reason_code != CLEAR_REASON
    )
    digest_status = (
        BLOCKED_STATUS if not rows else WATCH_STATUS if row_reason_codes else PASS_STATUS
    )
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    reason_code_counts = _reason_code_counts(row_reason_codes)
    if not rows:
        reason_code_counts = (
            MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                lineup_count=ONE,
            ),
        )

    return MarketResearchBasketballLineupVolatilityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        lineup_count=_whole(len(rows)),
        clear_lineup_count=_whole(sum(1 for row in rows if row.digest_status == CLEAR_STATUS)),
        watch_lineup_count=_whole(sum(1 for row in rows if row.digest_status == WATCH_STATUS)),
        signal_count=_whole(len(signal_items)),
        high_minutes_delta_lineup_count=_whole(
            sum(1 for row in rows if MINUTES_DELTA_REASON in row.reason_codes),
        ),
        starter_flip_lineup_count=_whole(
            sum(1 for row in rows if STARTER_FLIP_REASON in row.reason_codes),
        ),
        source_disagreement_lineup_count=_whole(
            sum(1 for row in rows if SOURCE_DISAGREEMENT_REASON in row.reason_codes),
        ),
        stale_update_lineup_count=_whole(
            sum(1 for row in rows if STALE_UPDATE_REASON in row.reason_codes),
        ),
        volatility_score_threshold=config.volatility_score_threshold,
        minutes_delta_threshold=config.minutes_delta_threshold,
        starter_flip_threshold=config.starter_flip_threshold,
        source_disagreement_threshold=config.source_disagreement_threshold,
        stale_update_seconds_threshold=config.stale_update_seconds_threshold,
        max_minutes_delta=_max_or_none(row.minutes_delta for row in rows),
        max_starter_probability_delta=_max_or_none(
            row.starter_probability_delta for row in rows
        ),
        max_status_rank_delta=_max_or_none(row.status_rank_delta for row in rows),
        max_update_age_seconds=_max_or_none(row.update_age_seconds for row in rows),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (signal.source_ref, signal.signal_config_version)
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_lineup_volatility_digest_payload(
    report: MarketResearchBasketballLineupVolatilityDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballLineupVolatilityDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBasketballLineupVolatilityDigestReport",
        )
    _require_flags("report", report)
    _revalidate_public_dataclass_for_payload("report", report)
    return _to_plain(report)


def _build_rows(
    signals: tuple[MarketResearchBasketballLineupVolatilityDigestSignal, ...],
    *,
    config: MarketResearchBasketballLineupVolatilityDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBasketballLineupVolatilityDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str, str],
        list[MarketResearchBasketballLineupVolatilityDigestSignal],
    ] = {}
    for signal in signals:
        grouped.setdefault(
            (
                signal.condition_id,
                signal.lineup_key,
                signal.league_key,
                signal.team_key,
                signal.player_key,
            ),
            [],
        ).append(signal)

    rows = []
    for (
        condition_id,
        lineup_key,
        league_key,
        team_key,
        player_key,
    ), lineup_signals in grouped.items():
        sorted_signals = sorted(lineup_signals, key=lambda item: (item.observed_at, item.source_ref))
        minutes_values = tuple(item.projected_minutes for item in sorted_signals)
        starter_values = tuple(item.starter_probability for item in sorted_signals)
        rank_values = tuple(item.status_rank for item in sorted_signals)
        observed_at_latest = max(item.observed_at for item in sorted_signals)
        minutes_min = min(minutes_values)
        minutes_max = max(minutes_values)
        minutes_delta = _quantize(minutes_max - minutes_min)
        starter_probability_min = min(starter_values)
        starter_probability_max = max(starter_values)
        starter_probability_delta = _quantize(
            starter_probability_max - starter_probability_min,
        )
        status_rank_min = min(rank_values)
        status_rank_max = max(rank_values)
        status_rank_delta = _quantize(status_rank_max - status_rank_min)
        source_disagreement_count = max(
            item.source_disagreement_count for item in sorted_signals
        )
        update_age_seconds = _quantize(
            Decimal(str((generated_at - observed_at_latest).total_seconds())),
        )
        if update_age_seconds < ZERO:
            raise ValueError("observed_at values must be at or before generated_at")
        volatility_score = _volatility_score(
            minutes_delta=minutes_delta,
            minutes_threshold=config.minutes_delta_threshold,
            starter_delta=starter_probability_delta,
            rank_delta=status_rank_delta,
            starter_threshold=config.starter_flip_threshold,
            disagreement_count=source_disagreement_count,
            disagreement_threshold=config.source_disagreement_threshold,
        )
        reason_codes = []
        if minutes_delta >= config.minutes_delta_threshold:
            reason_codes.append(MINUTES_DELTA_REASON)
        if source_disagreement_count >= config.source_disagreement_threshold:
            reason_codes.append(SOURCE_DISAGREEMENT_REASON)
        if update_age_seconds >= config.stale_update_seconds_threshold:
            reason_codes.append(STALE_UPDATE_REASON)
        if status_rank_delta >= config.starter_flip_threshold:
            reason_codes.append(STARTER_FLIP_REASON)
        if not reason_codes and volatility_score >= config.volatility_score_threshold:
            reason_codes.append(MINUTES_DELTA_REASON)
        digest_status = WATCH_STATUS if reason_codes else CLEAR_STATUS
        if not reason_codes:
            reason_codes.append(CLEAR_REASON)

        rows.append(
            MarketResearchBasketballLineupVolatilityDigestRow(
                condition_id=condition_id,
                lineup_key=lineup_key,
                league_key=league_key,
                team_key=team_key,
                player_key=player_key,
                signal_count=_whole(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                minutes_min=minutes_min,
                minutes_max=minutes_max,
                minutes_delta=minutes_delta,
                starter_probability_min=starter_probability_min,
                starter_probability_max=starter_probability_max,
                starter_probability_delta=starter_probability_delta,
                status_rank_min=status_rank_min,
                status_rank_max=status_rank_max,
                status_rank_delta=status_rank_delta,
                source_disagreement_count=source_disagreement_count,
                update_age_seconds=update_age_seconds,
                volatility_score=volatility_score,
                digest_status=digest_status,
                reason_codes=tuple(reason_codes),
            ),
        )

    return tuple(
        sorted(
            rows,
            key=lambda row: (
                0 if row.digest_status == WATCH_STATUS else 1,
                -row.volatility_score,
                -row.minutes_delta,
                -row.status_rank_delta,
                -row.update_age_seconds,
                row.lineup_key,
                row.condition_id,
            ),
        ),
    )


def _volatility_score(
    *,
    minutes_delta: Decimal,
    minutes_threshold: Decimal,
    starter_delta: Decimal,
    rank_delta: Decimal,
    starter_threshold: Decimal,
    disagreement_count: Decimal,
    disagreement_threshold: Decimal,
) -> Decimal:
    components = (
        _ratio(minutes_delta, Decimal("100.000000")),
        starter_delta,
        _ratio(rank_delta, starter_threshold),
        _ratio(disagreement_count, disagreement_threshold),
    )
    return min(ONE, sum(components, ZERO)).quantize(QUANTUM)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBasketballLineupVolatilityDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
            reason_code=reason_code,
            lineup_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchBasketballLineupVolatilityDigestSignal],
) -> tuple[MarketResearchBasketballLineupVolatilityDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchBasketballLineupVolatilityDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchBasketballLineupVolatilityDigestSignal records",
            )
        _require_flags("signal", signal)
        key = (signal.condition_id, signal.lineup_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate lineup/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBasketballLineupVolatilityDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchBasketballLineupVolatilityDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBasketballLineupVolatilityDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                0 if row.digest_status == WATCH_STATUS else 1,
                -row.volatility_score,
                -row.minutes_delta,
                -row.status_rank_delta,
                -row.update_age_seconds,
                row.lineup_key,
                row.condition_id,
            ),
        ),
    ):
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
        _reject_sensitive_text(
            "signal_config_versions config_version",
            config_version,
        )
        if source_ref in seen_refs:
            raise ValueError("signal_config_versions source_ref values must be unique")
        seen_refs.add(source_ref)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBasketballLineupVolatilityDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    seen_reason_codes: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchBasketballLineupVolatilityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballLineupVolatilityDigestReasonCodeCount "
                "records",
            )
        _require_flags("reason_code_count", item)
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(item.reason_code)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: DIGEST_REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _validate_row(row: MarketResearchBasketballLineupVolatilityDigestRow) -> None:
    expected_status = (
        WATCH_STATUS
        if any(reason_code != CLEAR_REASON for reason_code in row.reason_codes)
        else CLEAR_STATUS
    )
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == CLEAR_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear rows must use the clear reason")
    if row.minutes_max < row.minutes_min:
        raise ValueError("minutes_max must be greater than or equal to minutes_min")
    if row.starter_probability_max < row.starter_probability_min:
        raise ValueError(
            "starter_probability_max must be greater than or equal to minimum",
        )
    if row.status_rank_max < row.status_rank_min:
        raise ValueError("status_rank_max must be greater than or equal to minimum")


def _validate_report(report: MarketResearchBasketballLineupVolatilityDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.lineup_count != _whole(len(report.rows)):
        raise ValueError("lineup_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.clear_lineup_count != _whole(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_lineup_count must match rows")
    if report.watch_lineup_count != _whole(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_lineup_count must match rows")
    if report.lineup_count != report.clear_lineup_count + report.watch_lineup_count:
        raise ValueError("lineup counts must reconcile")
    expected_digest_status = (
        BLOCKED_STATUS
        if not report.rows
        else WATCH_STATUS if any(row.digest_status == WATCH_STATUS for row in report.rows) else PASS_STATUS
    )
    if report.digest_status != expected_digest_status:
        raise ValueError("digest_status must match rows")
    if report.digest_status == PASS_STATUS and any(
        reason_code not in (PASSED_REASON, EMPTY_REASON)
        for reason_code in report.reason_codes
    ):
        raise ValueError("pass reports must not include watch reasons")
    if report.digest_status == BLOCKED_STATUS and report.rows:
        raise ValueError("blocked reports must not include rows")
    if report.digest_status == BLOCKED_STATUS and report.reason_codes != (EMPTY_REASON,):
        raise ValueError("blocked reports must use the empty reason")
    if report.digest_status == WATCH_STATUS and not report.reason_code_counts:
        raise ValueError("watch reports require reason counts")
    expected_row_reasons = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    expected_reason_code_counts = _reason_code_counts(expected_row_reasons)
    expected_reason_codes = (
        _sort_reason_codes(set(expected_row_reasons), DIGEST_REASON_CODES)
        if expected_row_reasons
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if not report.rows:
        expected_reason_code_counts = (
            MarketResearchBasketballLineupVolatilityDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                lineup_count=ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.max_minutes_delta != _max_or_none(row.minutes_delta for row in report.rows):
        raise ValueError("max_minutes_delta must match rows")
    if report.max_starter_probability_delta != _max_or_none(
        row.starter_probability_delta for row in report.rows
    ):
        raise ValueError("max_starter_probability_delta must match rows")
    if report.max_status_rank_delta != _max_or_none(row.status_rank_delta for row in report.rows):
        raise ValueError("max_status_rank_delta must match rows")
    if report.max_update_age_seconds != _max_or_none(row.update_age_seconds for row in report.rows):
        raise ValueError("max_update_age_seconds must match rows")


def _to_plain(value: Any) -> Any:
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if isinstance(value, Decimal):
        raise ValueError("Decimal values must be exact Decimal")
    if type(value) is datetime:
        _require_payload_datetime_utc("datetime", value)
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("datetime values must be exactly datetime")
    if is_dataclass(value):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("dataclass values must be digest records")
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_to_plain(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (list, dict, set):
        raise ValueError("payload values must be JSON-ready digest values")
    raise ValueError("payload values must be JSON-ready digest values")


def _revalidate_public_dataclass_for_payload(name: str, value: object) -> None:
    if type(value) not in _PUBLIC_DATACLASS_TYPES:
        raise ValueError(f"{name} must be a digest record")
    _require_flags(_payload_record_label(value), value)
    for field in fields(value):
        _revalidate_public_value_for_payload(
            f"{name}.{field.name}",
            getattr(value, field.name),
        )
    type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _revalidate_public_value_for_payload(name: str, value: object) -> None:
    if is_dataclass(value):
        _revalidate_public_dataclass_for_payload(name, value)
        return
    if type(value) is Decimal:
        _require_payload_decimal_scale(name, value)
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{name} must be a Decimal")
    if type(value) is datetime:
        _require_payload_datetime_utc(name, value)
        return
    if isinstance(value, datetime):
        raise ValueError(f"{name} must be exactly datetime")
    if type(value) is tuple:
        for index, item in enumerate(value):
            _revalidate_public_value_for_payload(f"{name}[{index}]", item)
        return
    if value is None or type(value) in (str, bool):
        if type(value) is str:
            _require_canonical_string(name, value)
        return
    raise ValueError(f"{name} must contain JSON-ready values")


def _payload_record_label(value: object) -> str:
    if type(value) is MarketResearchBasketballLineupVolatilityDigestReport:
        return "report"
    if type(value) is MarketResearchBasketballLineupVolatilityDigestRow:
        return "row"
    if type(value) is MarketResearchBasketballLineupVolatilityDigestReasonCodeCount:
        return "reason_code_count"
    if type(value) is MarketResearchBasketballLineupVolatilityDigestSignal:
        return "signal"
    if type(value) is MarketResearchBasketballLineupVolatilityDigestConfig:
        return "config"
    return "record"


def _require_payload_decimal_scale(name: str, value: Decimal) -> None:
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if (
        value.as_tuple().exponent != QUANTUM.as_tuple().exponent
        and not _payload_decimal_allows_whole_count(name, value)
    ):
        raise ValueError(f"{name} must be six-decimal")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{name} must be six-decimal")
    try:
        scaled = value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be six-decimal") from exc
    if value != scaled:
        raise ValueError(f"{name} must be six-decimal")


def _payload_decimal_allows_whole_count(name: str, value: Decimal) -> bool:
    field_name = name.rsplit(".", maxsplit=1)[-1]
    return field_name.endswith("_count") and value == value.to_integral_value()


def _require_payload_datetime_utc(name: str, value: datetime) -> None:
    _as_utc(name, value)
    if value.tzinfo is not UTC:
        raise ValueError(f"{name} must be UTC")


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
        raise ValueError(f"{name} must not contain duplicates")
    sorted_codes = _sort_reason_codes(reason_codes, allowed)
    if reason_codes != sorted_codes:
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} is not recognized")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{name} must not contain leading or trailing whitespace")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(blocked in lowered for blocked in _BLOCKED_WORDS):
        raise ValueError(f"{name} contains unsafe source detail")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    try:
        normalized = value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not normalized.is_finite():
        raise ValueError(f"{name} must be finite")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be whole")
    return normalized.quantize(Decimal("1"))


def _normalize_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    _require_maximum_one_decimal(name, normalized)
    return normalized


def _require_maximum_one_decimal(name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{name} must be less than or equal to 1")


def _require_flags(name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{name} {flag} must be True")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _whole(value: int) -> Decimal:
    return Decimal(value).quantize(Decimal("1"))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    return (numerator / denominator).quantize(QUANTUM)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)
