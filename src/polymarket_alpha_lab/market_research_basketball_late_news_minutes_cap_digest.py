"""Pure Phase 1 reducer for basketball late news minutes cap research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_LATE_NEWS_MINUTES_CAP_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-late-news-minutes-cap-digest-v0"
)
BASKETBALL_LATE_NEWS_MINUTES_CAP_RESEARCH_SCOPE = (
    "basketball late news minutes cap research digest only"
)

QUANTUM = Decimal("0.000001")
WHOLE_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
CLEAR_STATUS = "clear"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (CLEAR_STATUS, WATCH_STATUS, BLOCKED_STATUS)

LATE_NEWS_REASON = "basketball_late_news_minutes_cap_late_news"
ACTIVE_CAP_REASON = "basketball_late_news_minutes_cap_active_cap"
LOW_CAP_REASON = "basketball_late_news_minutes_cap_low_cap"
DELTA_REASON = "basketball_late_news_minutes_cap_delta_high"
CONFIDENCE_REASON = "basketball_late_news_minutes_cap_confidence_high"
CRITICAL_REASON = "basketball_late_news_minutes_cap_critical_risk"
CLEAR_REASON = "basketball_late_news_minutes_cap_clear"
BLOCKED_PRESENT_REASON = "basketball_late_news_minutes_cap_blocked_present"
WATCH_PRESENT_REASON = "basketball_late_news_minutes_cap_watch_present"
PASSED_REASON = "basketball_late_news_minutes_cap_passed"
EMPTY_REASON = "basketball_late_news_minutes_cap_empty"

ROW_REASON_CODES = (
    LATE_NEWS_REASON,
    ACTIVE_CAP_REASON,
    LOW_CAP_REASON,
    DELTA_REASON,
    CONFIDENCE_REASON,
    CRITICAL_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    BLOCKED_PRESENT_REASON,
    WATCH_PRESENT_REASON,
    LATE_NEWS_REASON,
    ACTIVE_CAP_REASON,
    LOW_CAP_REASON,
    DELTA_REASON,
    CONFIDENCE_REASON,
    CRITICAL_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_basketball_late_news_minutes_cap_monitoring",
    WATCH_STATUS: "review_report_only_basketball_late_news_minutes_cap_watchlist",
    BLOCKED_STATUS: "review_report_only_basketball_late_news_minutes_cap_screening",
}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

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
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_LATE_NEWS_MINUTES_CAP_DIGEST_CONFIG_VERSION",
    "BASKETBALL_LATE_NEWS_MINUTES_CAP_RESEARCH_SCOPE",
    "MarketResearchBasketballLateNewsMinutesCapDigestConfig",
    "MarketResearchBasketballLateNewsMinutesCapDigestSignal",
    "MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount",
    "MarketResearchBasketballLateNewsMinutesCapDigestRow",
    "MarketResearchBasketballLateNewsMinutesCapDigestReport",
    "build_market_research_basketball_late_news_minutes_cap_digest",
    "market_research_basketball_late_news_minutes_cap_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBasketballLateNewsMinutesCapDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_LATE_NEWS_MINUTES_CAP_DIGEST_CONFIG_VERSION
    )
    late_news_seconds_to_start_threshold: Decimal = Decimal("3600.000000")
    minutes_cap_threshold: Decimal = Decimal("24.000000")
    minutes_delta_threshold: Decimal = Decimal("6.000000")
    critical_minutes_delta_threshold: Decimal = Decimal("10.000000")
    confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLateNewsMinutesCapDigestConfig:
            raise TypeError(
                "MarketResearchBasketballLateNewsMinutesCapDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLateNewsMinutesCapDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchBasketballLateNewsMinutesCapDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "late_news_seconds_to_start_threshold",
            _normalize_positive_decimal(
                "late_news_seconds_to_start_threshold",
                self.late_news_seconds_to_start_threshold,
            ),
        )
        for name in (
            "minutes_cap_threshold",
            "minutes_delta_threshold",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "critical_minutes_delta_threshold",
            _normalize_positive_decimal(
                "critical_minutes_delta_threshold",
                self.critical_minutes_delta_threshold,
            ),
        )
        object.__setattr__(
            self,
            "confidence_threshold",
            _normalize_ratio_decimal("confidence_threshold", self.confidence_threshold),
        )
        if self.critical_minutes_delta_threshold < self.minutes_delta_threshold:
            raise ValueError(
                "critical_minutes_delta_threshold must be at least minutes_delta_threshold",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballLateNewsMinutesCapDigestSignal:
    condition_id: str
    league_key: str
    team_key: str
    player_key: str
    source_ref: str
    observed_at: datetime
    scheduled_start_at: datetime
    baseline_projected_minutes: Decimal
    capped_minutes: Decimal | None
    news_confidence: Decimal
    cap_active: bool
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_LATE_NEWS_MINUTES_CAP_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLateNewsMinutesCapDigestSignal:
            raise TypeError(
                "MarketResearchBasketballLateNewsMinutesCapDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLateNewsMinutesCapDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchBasketballLateNewsMinutesCapDigestSignal",
            )
        for name in (
            "condition_id",
            "league_key",
            "team_key",
            "player_key",
            "source_ref",
            "signal_config_version",
        ):
            _require_canonical_string(name, getattr(self, name))
            _reject_sensitive_text(name, getattr(self, name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        if self.scheduled_start_at < self.observed_at:
            raise ValueError("scheduled_start_at must be at or after observed_at")
        object.__setattr__(
            self,
            "baseline_projected_minutes",
            _normalize_nonnegative_decimal(
                "baseline_projected_minutes",
                self.baseline_projected_minutes,
            ),
        )
        object.__setattr__(
            self,
            "capped_minutes",
            _normalize_optional_nonnegative_decimal(
                "capped_minutes",
                self.capped_minutes,
            ),
        )
        object.__setattr__(
            self,
            "news_confidence",
            _normalize_ratio_decimal("news_confidence", self.news_confidence),
        )
        if type(self.cap_active) is not bool:
            raise ValueError("cap_active must be a bool")
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount:
    reason_code: str
    player_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "player_count",
            _normalize_nonnegative_whole_decimal("player_count", self.player_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballLateNewsMinutesCapDigestRow:
    condition_id: str
    league_key: str
    team_key: str
    player_key: str
    signal_count: Decimal
    observed_at_latest: datetime
    scheduled_start_at: datetime
    baseline_projected_minutes_max: Decimal
    capped_minutes_min: Decimal | None
    minutes_delta: Decimal
    seconds_to_start_at_latest_news: Decimal
    news_confidence_max: Decimal
    cap_active: bool
    screening_priority_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLateNewsMinutesCapDigestRow:
            raise TypeError(
                "MarketResearchBasketballLateNewsMinutesCapDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLateNewsMinutesCapDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchBasketballLateNewsMinutesCapDigestRow",
            )
        for name in ("condition_id", "league_key", "team_key", "player_key"):
            _require_canonical_string(name, getattr(self, name))
            _reject_sensitive_text(name, getattr(self, name))
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
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        if self.scheduled_start_at < self.observed_at_latest:
            raise ValueError("scheduled_start_at must be at or after observed_at_latest")
        for name in (
            "baseline_projected_minutes_max",
            "minutes_delta",
            "seconds_to_start_at_latest_news",
            "news_confidence_max",
            "screening_priority_score",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "capped_minutes_min",
            _normalize_optional_nonnegative_decimal(
                "capped_minutes_min",
                self.capped_minutes_min,
            ),
        )
        _require_maximum_one_decimal(
            "news_confidence_max",
            self.news_confidence_max,
        )
        _require_maximum_one_decimal(
            "screening_priority_score",
            self.screening_priority_score,
        )
        if type(self.cap_active) is not bool:
            raise ValueError("cap_active must be a bool")
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballLateNewsMinutesCapDigestReport:
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    player_count: Decimal
    signal_count: Decimal
    clear_player_count: Decimal
    watch_player_count: Decimal
    blocked_player_count: Decimal
    late_news_player_count: Decimal
    active_cap_player_count: Decimal
    low_cap_player_count: Decimal
    high_minutes_delta_player_count: Decimal
    high_confidence_player_count: Decimal
    critical_cap_risk_player_count: Decimal
    late_news_seconds_to_start_threshold: Decimal
    minutes_cap_threshold: Decimal
    minutes_delta_threshold: Decimal
    critical_minutes_delta_threshold: Decimal
    confidence_threshold: Decimal
    max_minutes_delta: Decimal | None
    min_seconds_to_start: Decimal | None
    average_news_confidence: Decimal
    rows: tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballLateNewsMinutesCapDigestReport:
            raise TypeError(
                "MarketResearchBasketballLateNewsMinutesCapDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballLateNewsMinutesCapDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchBasketballLateNewsMinutesCapDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_LATE_NEWS_MINUTES_CAP_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball late news minutes cap scope")
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for name in (
            "player_count",
            "signal_count",
            "clear_player_count",
            "watch_player_count",
            "blocked_player_count",
            "late_news_player_count",
            "active_cap_player_count",
            "low_cap_player_count",
            "high_minutes_delta_player_count",
            "high_confidence_player_count",
            "critical_cap_risk_player_count",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_whole_decimal(name, getattr(self, name)),
            )
        for name in (
            "late_news_seconds_to_start_threshold",
            "minutes_cap_threshold",
            "minutes_delta_threshold",
            "critical_minutes_delta_threshold",
            "confidence_threshold",
            "average_news_confidence",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_maximum_one_decimal("confidence_threshold", self.confidence_threshold)
        _require_maximum_one_decimal(
            "average_news_confidence",
            self.average_news_confidence,
        )
        for name in ("max_minutes_delta", "min_seconds_to_start"):
            object.__setattr__(
                self,
                name,
                _normalize_optional_nonnegative_decimal(name, getattr(self, name)),
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


def build_market_research_basketball_late_news_minutes_cap_digest(
    signals: Iterable[MarketResearchBasketballLateNewsMinutesCapDigestSignal],
    *,
    config: MarketResearchBasketballLateNewsMinutesCapDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballLateNewsMinutesCapDigestReport:
    if type(config) is not MarketResearchBasketballLateNewsMinutesCapDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballLateNewsMinutesCapDigestConfig",
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
    digest_status = _digest_status(rows)
    reason_codes = _report_reason_codes(digest_status, rows, row_reason_codes)

    return MarketResearchBasketballLateNewsMinutesCapDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_LATE_NEWS_MINUTES_CAP_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        player_count=_whole(len(rows)),
        signal_count=_whole(len(signal_items)),
        clear_player_count=_whole(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_player_count=_whole(
            sum(1 for row in rows if row.digest_status == WATCH_STATUS),
        ),
        blocked_player_count=_whole(
            sum(1 for row in rows if row.digest_status == BLOCKED_STATUS),
        ),
        late_news_player_count=_reason_count(rows, LATE_NEWS_REASON),
        active_cap_player_count=_reason_count(rows, ACTIVE_CAP_REASON),
        low_cap_player_count=_reason_count(rows, LOW_CAP_REASON),
        high_minutes_delta_player_count=_reason_count(rows, DELTA_REASON),
        high_confidence_player_count=_reason_count(rows, CONFIDENCE_REASON),
        critical_cap_risk_player_count=_reason_count(rows, CRITICAL_REASON),
        late_news_seconds_to_start_threshold=config.late_news_seconds_to_start_threshold,
        minutes_cap_threshold=config.minutes_cap_threshold,
        minutes_delta_threshold=config.minutes_delta_threshold,
        critical_minutes_delta_threshold=config.critical_minutes_delta_threshold,
        confidence_threshold=config.confidence_threshold,
        max_minutes_delta=_max_or_none(row.minutes_delta for row in rows),
        min_seconds_to_start=_min_or_none(
            row.seconds_to_start_at_latest_news for row in rows
        ),
        average_news_confidence=_average_or_zero(row.news_confidence_max for row in rows),
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


def market_research_basketball_late_news_minutes_cap_digest_payload(
    report: MarketResearchBasketballLateNewsMinutesCapDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballLateNewsMinutesCapDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBasketballLateNewsMinutesCapDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _build_rows(
    signals: tuple[MarketResearchBasketballLateNewsMinutesCapDigestSignal, ...],
    *,
    config: MarketResearchBasketballLateNewsMinutesCapDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str],
        list[MarketResearchBasketballLateNewsMinutesCapDigestSignal],
    ] = {}
    for signal in signals:
        grouped.setdefault(
            (
                signal.condition_id,
                signal.league_key,
                signal.team_key,
                signal.player_key,
            ),
            [],
        ).append(signal)

    rows = []
    for (condition_id, league_key, team_key, player_key), player_signals in grouped.items():
        sorted_signals = sorted(
            player_signals,
            key=lambda item: (item.observed_at, item.source_ref),
        )
        latest_signal = max(
            sorted_signals,
            key=lambda item: (item.observed_at, item.source_ref),
        )
        observed_at_latest = latest_signal.observed_at
        if observed_at_latest > generated_at:
            raise ValueError("observed_at values must be at or before generated_at")
        scheduled_start_at = latest_signal.scheduled_start_at
        baseline_projected_minutes_max = max(
            item.baseline_projected_minutes for item in sorted_signals
        )
        cap_values = tuple(
            item.capped_minutes
            for item in sorted_signals
            if item.capped_minutes is not None
        )
        capped_minutes_min = min(cap_values) if cap_values else None
        news_confidence_max = max(item.news_confidence for item in sorted_signals)
        cap_active = any(item.cap_active for item in sorted_signals)
        minutes_delta = (
            _quantize(baseline_projected_minutes_max - capped_minutes_min)
            if capped_minutes_min is not None
            else ZERO.quantize(QUANTUM)
        )
        if minutes_delta < ZERO:
            minutes_delta = ZERO.quantize(QUANTUM)
        seconds_to_start = _timedelta_seconds(scheduled_start_at - observed_at_latest)
        if seconds_to_start < ZERO:
            raise ValueError("scheduled_start_at must be at or after observed_at_latest")

        late_news = seconds_to_start <= config.late_news_seconds_to_start_threshold
        low_cap = (
            capped_minutes_min is not None
            and capped_minutes_min <= config.minutes_cap_threshold
        )
        high_delta = minutes_delta >= config.minutes_delta_threshold
        high_confidence = news_confidence_max >= config.confidence_threshold
        critical_risk = (
            late_news
            and cap_active
            and low_cap
            and high_delta
            and high_confidence
            and minutes_delta >= config.critical_minutes_delta_threshold
        )

        reason_codes = []
        if late_news:
            reason_codes.append(LATE_NEWS_REASON)
        if cap_active:
            reason_codes.append(ACTIVE_CAP_REASON)
        if low_cap:
            reason_codes.append(LOW_CAP_REASON)
        if high_delta:
            reason_codes.append(DELTA_REASON)
        if high_confidence:
            reason_codes.append(CONFIDENCE_REASON)
        if critical_risk:
            reason_codes.append(CRITICAL_REASON)
        if critical_risk:
            digest_status = BLOCKED_STATUS
        elif reason_codes:
            digest_status = WATCH_STATUS
        else:
            digest_status = CLEAR_STATUS
            reason_codes.append(CLEAR_REASON)

        rows.append(
            MarketResearchBasketballLateNewsMinutesCapDigestRow(
                condition_id=condition_id,
                league_key=league_key,
                team_key=team_key,
                player_key=player_key,
                signal_count=_whole(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                scheduled_start_at=scheduled_start_at,
                baseline_projected_minutes_max=baseline_projected_minutes_max,
                capped_minutes_min=capped_minutes_min,
                minutes_delta=minutes_delta,
                seconds_to_start_at_latest_news=seconds_to_start,
                news_confidence_max=news_confidence_max,
                cap_active=cap_active,
                screening_priority_score=_screening_priority_score(
                    minutes_delta,
                    config.critical_minutes_delta_threshold,
                ),
                digest_status=digest_status,
                reason_codes=tuple(reason_codes),
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_signals(
    signals: Iterable[MarketResearchBasketballLateNewsMinutesCapDigestSignal],
) -> tuple[MarketResearchBasketballLateNewsMinutesCapDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchBasketballLateNewsMinutesCapDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchBasketballLateNewsMinutesCapDigestSignal records",
            )
        _require_flags("signal", signal)
        key = (signal.condition_id, signal.player_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate player/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchBasketballLateNewsMinutesCapDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBasketballLateNewsMinutesCapDigestRow records",
            )
        _require_flags("row", row)
        key = (row.condition_id, row.player_key)
        if key in seen:
            raise ValueError("rows must not contain duplicate player values")
        seen.add(key)
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
) -> tuple[MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount "
                "records",
            )
        _require_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: DIGEST_REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _validate_row(row: MarketResearchBasketballLateNewsMinutesCapDigestRow) -> None:
    risk_reasons = tuple(
        reason_code for reason_code in row.reason_codes if reason_code != CLEAR_REASON
    )
    expected_status = (
        BLOCKED_STATUS
        if CRITICAL_REASON in risk_reasons
        else WATCH_STATUS
        if risk_reasons
        else CLEAR_STATUS
    )
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == CLEAR_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear rows must use the clear reason")
    expected_delta = (
        _quantize(row.baseline_projected_minutes_max - row.capped_minutes_min)
        if row.capped_minutes_min is not None
        else ZERO.quantize(QUANTUM)
    )
    if expected_delta < ZERO:
        expected_delta = ZERO.quantize(QUANTUM)
    if row.minutes_delta != expected_delta:
        raise ValueError("minutes_delta must match calculated value")
    expected_seconds = _timedelta_seconds(row.scheduled_start_at - row.observed_at_latest)
    if row.seconds_to_start_at_latest_news != expected_seconds:
        raise ValueError("seconds_to_start_at_latest_news must match datetimes")
    if (ACTIVE_CAP_REASON in row.reason_codes) != row.cap_active:
        raise ValueError("active cap reason must match cap_active")
    if row.capped_minutes_min is None and LOW_CAP_REASON in row.reason_codes:
        raise ValueError("low cap reason requires capped_minutes_min")
    if CRITICAL_REASON in row.reason_codes:
        required = {
            LATE_NEWS_REASON,
            ACTIVE_CAP_REASON,
            LOW_CAP_REASON,
            DELTA_REASON,
            CONFIDENCE_REASON,
        }
        if not required.issubset(set(row.reason_codes)):
            raise ValueError("critical risk reason requires all risk gates")


def _validate_report(report: MarketResearchBasketballLateNewsMinutesCapDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.player_count != _whole(len(report.rows)):
        raise ValueError("player_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.clear_player_count != _status_count(report.rows, CLEAR_STATUS):
        raise ValueError("clear_player_count must match rows")
    if report.watch_player_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_player_count must match rows")
    if report.blocked_player_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_player_count must match rows")
    if (
        report.player_count
        != report.clear_player_count
        + report.watch_player_count
        + report.blocked_player_count
    ):
        raise ValueError("player counts must reconcile")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.late_news_player_count != _reason_count(report.rows, LATE_NEWS_REASON):
        raise ValueError("late_news_player_count must match rows")
    if report.active_cap_player_count != _reason_count(report.rows, ACTIVE_CAP_REASON):
        raise ValueError("active_cap_player_count must match rows")
    if report.low_cap_player_count != _reason_count(report.rows, LOW_CAP_REASON):
        raise ValueError("low_cap_player_count must match rows")
    if report.high_minutes_delta_player_count != _reason_count(report.rows, DELTA_REASON):
        raise ValueError("high_minutes_delta_player_count must match rows")
    if report.high_confidence_player_count != _reason_count(report.rows, CONFIDENCE_REASON):
        raise ValueError("high_confidence_player_count must match rows")
    if report.critical_cap_risk_player_count != _reason_count(report.rows, CRITICAL_REASON):
        raise ValueError("critical_cap_risk_player_count must match rows")
    if report.max_minutes_delta != _max_or_none(row.minutes_delta for row in report.rows):
        raise ValueError("max_minutes_delta must match rows")
    if report.min_seconds_to_start != _min_or_none(
        row.seconds_to_start_at_latest_news for row in report.rows
    ):
        raise ValueError("min_seconds_to_start must match rows")
    if report.average_news_confidence != _average_or_zero(
        row.news_confidence_max for row in report.rows
    ):
        raise ValueError("average_news_confidence must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_reasons = _report_reason_codes(
        report.digest_status,
        report.rows,
        row_reason_codes,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")


def _digest_status(
    rows: tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...],
) -> str:
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.digest_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    digest_status: str,
    rows: tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...],
    row_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if digest_status == PASS_STATUS:
        return (PASSED_REASON,)
    lead_reason = (
        BLOCKED_PRESENT_REASON
        if digest_status == BLOCKED_STATUS
        else WATCH_PRESENT_REASON
    )
    return (lead_reason, *_sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount(
            reason_code=reason_code,
            player_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _row_sort_key(
    row: MarketResearchBasketballLateNewsMinutesCapDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    status_weight = {
        BLOCKED_STATUS: Decimal("0"),
        WATCH_STATUS: Decimal("1"),
        CLEAR_STATUS: Decimal("2"),
    }[row.digest_status]
    return (
        status_weight,
        -row.screening_priority_score,
        -row.minutes_delta,
        row.seconds_to_start_at_latest_news,
        row.player_key,
        row.condition_id,
    )


def _status_count(
    rows: tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...],
    status: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchBasketballLateNewsMinutesCapDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if reason_code in row.reason_codes))


def _screening_priority_score(
    minutes_delta: Decimal,
    critical_minutes_delta_threshold: Decimal,
) -> Decimal:
    if minutes_delta == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        score = minutes_delta / critical_minutes_delta_threshold
        if score > ONE:
            return ONE.quantize(QUANTUM)
        return score.quantize(QUANTUM)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items).quantize(QUANTUM)


def _min_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return min(items).quantize(QUANTUM)


def _average_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return (sum(items, ZERO) / Decimal(len(items))).quantize(QUANTUM)


def _whole(value: int) -> Decimal:
    return Decimal(value).quantize(WHOLE_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _timedelta_seconds(value: timedelta) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(value.days * 86400 + value.seconds)
        micros = Decimal(value.microseconds) / Decimal(1000000)
        return (seconds + micros).quantize(QUANTUM)


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
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
    if reason_codes != _sort_reason_codes(reason_codes, allowed):
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _normalize_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    checked = _require_decimal(name, value)
    normalized = checked.quantize(WHOLE_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != checked:
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value).quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    _require_maximum_one_decimal(name, normalized)
    return normalized


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be finite") from exc


def _require_maximum_one_decimal(name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{name} must be at most 1")


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


def _require_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, flag_name)
        if type(flag) is not bool:
            raise ValueError(f"{name} {flag_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{flag_name} must be True")
