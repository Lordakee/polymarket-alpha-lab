"""Pure Phase 1 report-only reducer for basketball coach rotation signals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_COACH_ROTATION_SIGNAL_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-coach-rotation-signal-digest-v0"
)
BASKETBALL_COACH_ROTATION_SIGNAL_RESEARCH_SCOPE = (
    "basketball coach rotation signal research digest only"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS)
ROW_STATUSES = (CLEAR_STATUS, WATCH_STATUS)

SCORE_REASON = "basketball_coach_rotation_signal_score_high"
ACTIVE_REASON = "basketball_coach_rotation_signal_active"
MINUTES_DELTA_REASON = "basketball_coach_rotation_minutes_delta_high"
BENCH_SHARE_DELTA_REASON = "basketball_coach_rotation_bench_share_delta_high"
CONFIDENCE_REASON = "basketball_coach_rotation_confidence_high"
STALE_REASON = "basketball_coach_rotation_signal_stale"
CLEAR_REASON = "basketball_coach_rotation_signal_clear"
PASSED_REASON = "basketball_coach_rotation_signal_passed"
EMPTY_REASON = "basketball_coach_rotation_signal_empty"

ROW_REASON_CODES = (
    SCORE_REASON,
    ACTIVE_REASON,
    MINUTES_DELTA_REASON,
    BENCH_SHARE_DELTA_REASON,
    CONFIDENCE_REASON,
    STALE_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    SCORE_REASON,
    ACTIVE_REASON,
    MINUTES_DELTA_REASON,
    BENCH_SHARE_DELTA_REASON,
    CONFIDENCE_REASON,
    STALE_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_basketball_coach_rotation_signal_monitoring",
    WATCH_STATUS: "review_report_only_basketball_coach_rotation_signals",
}
WATCH_RANK = Decimal("0.000000")
CLEAR_RANK = Decimal("1.000000")

_BLOCKED_TEXT_PARTS = (
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
    "private_" "key",
    "api_" "key",
    "sec" "ret",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_COACH_ROTATION_SIGNAL_DIGEST_CONFIG_VERSION",
    "BASKETBALL_COACH_ROTATION_SIGNAL_RESEARCH_SCOPE",
    "MarketResearchBasketballCoachRotationSignalDigestConfig",
    "MarketResearchBasketballCoachRotationSignalDigestSignal",
    "MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount",
    "MarketResearchBasketballCoachRotationSignalDigestRow",
    "MarketResearchBasketballCoachRotationSignalDigestReport",
    "build_market_research_basketball_coach_rotation_signal_digest",
    "market_research_basketball_coach_rotation_signal_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBasketballCoachRotationSignalDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_COACH_ROTATION_SIGNAL_DIGEST_CONFIG_VERSION
    )
    rotation_signal_score_threshold: Decimal = Decimal("0.650000")
    minutes_delta_threshold: Decimal = Decimal("6.000000")
    bench_share_delta_threshold: Decimal = Decimal("0.120000")
    confidence_threshold: Decimal = Decimal("0.700000")
    signal_age_seconds_threshold: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballCoachRotationSignalDigestConfig:
            raise TypeError(
                "MarketResearchBasketballCoachRotationSignalDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballCoachRotationSignalDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_COACH_ROTATION_SIGNAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "rotation_signal_score_threshold",
            "minutes_delta_threshold",
            "bench_share_delta_threshold",
            "signal_age_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_threshold",
            _normalize_ratio_decimal("confidence_threshold", self.confidence_threshold),
        )
        _require_maximum_one_decimal(
            "rotation_signal_score_threshold",
            self.rotation_signal_score_threshold,
        )
        _require_maximum_one_decimal(
            "bench_share_delta_threshold",
            self.bench_share_delta_threshold,
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballCoachRotationSignalDigestSignal:
    condition_id: str
    league_key: str
    team_key: str
    coach_key: str
    rotation_unit_key: str
    source_ref: str
    observed_at: datetime
    baseline_minutes: Decimal
    projected_minutes: Decimal
    baseline_bench_share: Decimal
    projected_bench_share: Decimal
    signal_confidence: Decimal
    coach_rotation_signal_active: bool
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_COACH_ROTATION_SIGNAL_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballCoachRotationSignalDigestSignal:
            raise TypeError(
                "MarketResearchBasketballCoachRotationSignalDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballCoachRotationSignalDigestSignal,
            "signal",
        )
        for field_name in (
            "condition_id",
            "league_key",
            "team_key",
            "coach_key",
            "rotation_unit_key",
            "source_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("baseline_minutes", "projected_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "baseline_bench_share",
            "projected_bench_share",
            "signal_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.coach_rotation_signal_active) is not bool:
            raise ValueError("coach_rotation_signal_active must be a bool")
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount:
    reason_code: str
    unit_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "unit_count",
            _normalize_nonnegative_decimal("unit_count", self.unit_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballCoachRotationSignalDigestRow:
    condition_id: str
    league_key: str
    team_key: str
    coach_key: str
    rotation_unit_key: str
    signal_count: Decimal
    observed_at_latest: datetime
    minutes_delta_abs_max: Decimal
    bench_share_delta_abs_max: Decimal
    signal_confidence_max: Decimal
    rotation_signal_score: Decimal
    signal_age_seconds: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballCoachRotationSignalDigestRow:
            raise TypeError(
                "MarketResearchBasketballCoachRotationSignalDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballCoachRotationSignalDigestRow,
            "row",
        )
        for field_name in (
            "condition_id",
            "league_key",
            "team_key",
            "coach_key",
            "rotation_unit_key",
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
            "minutes_delta_abs_max",
            "bench_share_delta_abs_max",
            "signal_confidence_max",
            "rotation_signal_score",
            "signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bench_share_delta_abs_max",
            "signal_confidence_max",
            "rotation_signal_score",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballCoachRotationSignalDigestReport:
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    rotation_unit_count: Decimal
    signal_count: Decimal
    clear_unit_count: Decimal
    watch_unit_count: Decimal
    high_score_unit_count: Decimal
    active_signal_unit_count: Decimal
    high_minutes_delta_unit_count: Decimal
    high_bench_share_delta_unit_count: Decimal
    high_confidence_unit_count: Decimal
    stale_signal_unit_count: Decimal
    rotation_signal_score_threshold: Decimal
    minutes_delta_threshold: Decimal
    bench_share_delta_threshold: Decimal
    confidence_threshold: Decimal
    signal_age_seconds_threshold: Decimal
    max_rotation_signal_score: Decimal
    max_minutes_delta_abs: Decimal
    max_signal_age_seconds: Decimal
    average_signal_confidence: Decimal
    rows: tuple[MarketResearchBasketballCoachRotationSignalDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballCoachRotationSignalDigestReport:
            raise TypeError(
                "MarketResearchBasketballCoachRotationSignalDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballCoachRotationSignalDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_COACH_ROTATION_SIGNAL_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball coach rotation signal scope")
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "rotation_unit_count",
            "signal_count",
            "clear_unit_count",
            "watch_unit_count",
            "high_score_unit_count",
            "active_signal_unit_count",
            "high_minutes_delta_unit_count",
            "high_bench_share_delta_unit_count",
            "high_confidence_unit_count",
            "stale_signal_unit_count",
            "rotation_signal_score_threshold",
            "minutes_delta_threshold",
            "bench_share_delta_threshold",
            "confidence_threshold",
            "signal_age_seconds_threshold",
            "max_rotation_signal_score",
            "max_minutes_delta_abs",
            "max_signal_age_seconds",
            "average_signal_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rotation_signal_score_threshold",
            "bench_share_delta_threshold",
            "confidence_threshold",
            "max_rotation_signal_score",
            "average_signal_confidence",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
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


def build_market_research_basketball_coach_rotation_signal_digest(
    signals: Iterable[MarketResearchBasketballCoachRotationSignalDigestSignal],
    *,
    config: MarketResearchBasketballCoachRotationSignalDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballCoachRotationSignalDigestReport:
    _require_exact_type(
        config,
        MarketResearchBasketballCoachRotationSignalDigestConfig,
        "config",
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    rows = _build_rows(signal_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    digest_status = WATCH_STATUS if row_reason_codes else PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchBasketballCoachRotationSignalDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_COACH_ROTATION_SIGNAL_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        rotation_unit_count=_count_decimal(len(rows)),
        signal_count=_count_decimal(len(signal_items)),
        clear_unit_count=_count_decimal(
            sum(ONE for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_unit_count=_count_decimal(
            sum(ONE for row in rows if row.digest_status == WATCH_STATUS),
        ),
        high_score_unit_count=_reason_count(rows, SCORE_REASON),
        active_signal_unit_count=_reason_count(rows, ACTIVE_REASON),
        high_minutes_delta_unit_count=_reason_count(rows, MINUTES_DELTA_REASON),
        high_bench_share_delta_unit_count=_reason_count(rows, BENCH_SHARE_DELTA_REASON),
        high_confidence_unit_count=_reason_count(rows, CONFIDENCE_REASON),
        stale_signal_unit_count=_reason_count(rows, STALE_REASON),
        rotation_signal_score_threshold=config.rotation_signal_score_threshold,
        minutes_delta_threshold=config.minutes_delta_threshold,
        bench_share_delta_threshold=config.bench_share_delta_threshold,
        confidence_threshold=config.confidence_threshold,
        signal_age_seconds_threshold=config.signal_age_seconds_threshold,
        max_rotation_signal_score=_max_decimal(row.rotation_signal_score for row in rows),
        max_minutes_delta_abs=_max_decimal(row.minutes_delta_abs_max for row in rows),
        max_signal_age_seconds=_max_decimal(row.signal_age_seconds for row in rows),
        average_signal_confidence=_average_or_zero(
            (row.signal_confidence_max for row in rows),
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


def market_research_basketball_coach_rotation_signal_digest_payload(
    report: MarketResearchBasketballCoachRotationSignalDigestReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        MarketResearchBasketballCoachRotationSignalDigestReport,
        "report",
    )
    _require_flags("report", report)
    payload = _to_plain(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _build_rows(
    signals: tuple[MarketResearchBasketballCoachRotationSignalDigestSignal, ...],
    *,
    config: MarketResearchBasketballCoachRotationSignalDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBasketballCoachRotationSignalDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str, str],
        list[MarketResearchBasketballCoachRotationSignalDigestSignal],
    ] = {}
    for signal in signals:
        grouped.setdefault(
            (
                signal.condition_id,
                signal.league_key,
                signal.team_key,
                signal.coach_key,
                signal.rotation_unit_key,
            ),
            [],
        ).append(signal)

    rows: list[MarketResearchBasketballCoachRotationSignalDigestRow] = []
    for (
        condition_id,
        league_key,
        team_key,
        coach_key,
        rotation_unit_key,
    ), unit_signals in grouped.items():
        sorted_signals = sorted(
            unit_signals,
            key=lambda item: (item.observed_at, item.source_ref),
        )
        observed_at_latest = max(item.observed_at for item in sorted_signals)
        signal_age_seconds = _datetime_delta_seconds(generated_at, observed_at_latest)
        if signal_age_seconds < ZERO:
            raise ValueError("observed_at values must be at or before generated_at")
        minutes_delta_abs_max = max(
            _abs_decimal(item.projected_minutes - item.baseline_minutes)
            for item in sorted_signals
        )
        bench_share_delta_abs_max = max(
            _abs_decimal(item.projected_bench_share - item.baseline_bench_share)
            for item in sorted_signals
        )
        signal_confidence_max = max(item.signal_confidence for item in sorted_signals)
        active_signal_seen = any(
            item.coach_rotation_signal_active for item in sorted_signals
        )
        rotation_signal_score = _rotation_signal_score(
            minutes_delta_abs=minutes_delta_abs_max,
            bench_share_delta_abs=bench_share_delta_abs_max,
            signal_confidence=signal_confidence_max,
            active_signal_seen=active_signal_seen,
            config=config,
        )
        reason_codes = _row_reason_codes(
            rotation_signal_score=rotation_signal_score,
            minutes_delta_abs=minutes_delta_abs_max,
            bench_share_delta_abs=bench_share_delta_abs_max,
            signal_confidence=signal_confidence_max,
            active_signal_seen=active_signal_seen,
            signal_age_seconds=signal_age_seconds,
            config=config,
        )
        rows.append(
            MarketResearchBasketballCoachRotationSignalDigestRow(
                condition_id=condition_id,
                league_key=league_key,
                team_key=team_key,
                coach_key=coach_key,
                rotation_unit_key=rotation_unit_key,
                signal_count=_count_decimal(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                minutes_delta_abs_max=minutes_delta_abs_max,
                bench_share_delta_abs_max=bench_share_delta_abs_max,
                signal_confidence_max=signal_confidence_max,
                rotation_signal_score=rotation_signal_score,
                signal_age_seconds=signal_age_seconds,
                digest_status=WATCH_STATUS
                if reason_codes != (CLEAR_REASON,)
                else CLEAR_STATUS,
                reason_codes=reason_codes,
            ),
        )

    return tuple(sorted(rows, key=_row_sort_key))


def _row_reason_codes(
    *,
    rotation_signal_score: Decimal,
    minutes_delta_abs: Decimal,
    bench_share_delta_abs: Decimal,
    signal_confidence: Decimal,
    active_signal_seen: bool,
    signal_age_seconds: Decimal,
    config: MarketResearchBasketballCoachRotationSignalDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if rotation_signal_score >= config.rotation_signal_score_threshold:
        reason_codes.append(SCORE_REASON)
    if active_signal_seen:
        reason_codes.append(ACTIVE_REASON)
    if minutes_delta_abs >= config.minutes_delta_threshold:
        reason_codes.append(MINUTES_DELTA_REASON)
    if bench_share_delta_abs >= config.bench_share_delta_threshold:
        reason_codes.append(BENCH_SHARE_DELTA_REASON)
    if signal_confidence >= config.confidence_threshold:
        reason_codes.append(CONFIDENCE_REASON)
    if active_signal_seen and signal_age_seconds >= config.signal_age_seconds_threshold:
        reason_codes.append(STALE_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _rotation_signal_score(
    *,
    minutes_delta_abs: Decimal,
    bench_share_delta_abs: Decimal,
    signal_confidence: Decimal,
    active_signal_seen: bool,
    config: MarketResearchBasketballCoachRotationSignalDigestConfig,
) -> Decimal:
    return _quantize(
        max(
            ONE if active_signal_seen else ZERO,
            _bounded_ratio(minutes_delta_abs, config.minutes_delta_threshold),
            _bounded_ratio(bench_share_delta_abs, config.bench_share_delta_threshold),
            signal_confidence,
        ),
    )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize(numerator / denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount(
            reason_code=reason_code,
            unit_count=_count_decimal(sum(ONE for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchBasketballCoachRotationSignalDigestSignal],
) -> tuple[MarketResearchBasketballCoachRotationSignalDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        _require_exact_type(
            signal,
            MarketResearchBasketballCoachRotationSignalDigestSignal,
            "signal",
        )
        _require_flags("signal", signal)
        key = (signal.condition_id, signal.rotation_unit_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate unit/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBasketballCoachRotationSignalDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        _require_exact_type(
            row,
            MarketResearchBasketballCoachRotationSignalDigestRow,
            "row",
        )
        _require_flags("row", row)
        key = (row.condition_id, row.rotation_unit_key)
        if key in seen:
            raise ValueError("rows must not contain duplicate condition/unit pairs")
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
        if type(item) not in (tuple, list):
            raise ValueError("signal_config_versions entries must be source/version pairs")
        if Decimal(len(item)) != Decimal("2"):
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
) -> tuple[MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        _require_exact_type(
            item,
            MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount,
            "reason_code_count",
        )
    return normalized


def _validate_row(row: MarketResearchBasketballCoachRotationSignalDigestRow) -> None:
    if row.digest_status == CLEAR_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear rows must use the clear reason")
    expected_status = (
        WATCH_STATUS
        if any(reason_code != CLEAR_REASON for reason_code in row.reason_codes)
        else CLEAR_STATUS
    )
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == WATCH_STATUS and row.reason_codes == (CLEAR_REASON,):
        raise ValueError("watch rows must include a watch reason")
    if row.rotation_signal_score == ZERO and row.digest_status == WATCH_STATUS:
        raise ValueError("watch rows must have positive rotation_signal_score")


def _validate_report(
    report: MarketResearchBasketballCoachRotationSignalDigestReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.rotation_unit_count != _count_decimal(len(report.rows)):
        raise ValueError("rotation_unit_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.clear_unit_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_unit_count must match rows")
    if report.watch_unit_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_unit_count must match rows")
    if report.rotation_unit_count != report.clear_unit_count + report.watch_unit_count:
        raise ValueError("unit counts must reconcile")
    if report.high_score_unit_count != _reason_count(report.rows, SCORE_REASON):
        raise ValueError("high_score_unit_count must match rows")
    if report.active_signal_unit_count != _reason_count(report.rows, ACTIVE_REASON):
        raise ValueError("active_signal_unit_count must match rows")
    if report.high_minutes_delta_unit_count != _reason_count(
        report.rows,
        MINUTES_DELTA_REASON,
    ):
        raise ValueError("high_minutes_delta_unit_count must match rows")
    if report.high_bench_share_delta_unit_count != _reason_count(
        report.rows,
        BENCH_SHARE_DELTA_REASON,
    ):
        raise ValueError("high_bench_share_delta_unit_count must match rows")
    if report.high_confidence_unit_count != _reason_count(report.rows, CONFIDENCE_REASON):
        raise ValueError("high_confidence_unit_count must match rows")
    if report.stale_signal_unit_count != _reason_count(report.rows, STALE_REASON):
        raise ValueError("stale_signal_unit_count must match rows")
    if report.max_rotation_signal_score != _max_decimal(
        row.rotation_signal_score for row in report.rows
    ):
        raise ValueError("max_rotation_signal_score must match rows")
    if report.max_minutes_delta_abs != _max_decimal(
        row.minutes_delta_abs_max for row in report.rows
    ):
        raise ValueError("max_minutes_delta_abs must match rows")
    if report.max_signal_age_seconds != _max_decimal(
        row.signal_age_seconds for row in report.rows
    ):
        raise ValueError("max_signal_age_seconds must match rows")
    if report.average_signal_confidence != _average_or_zero(
        row.signal_confidence_max for row in report.rows
    ):
        raise ValueError("average_signal_confidence must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_status = WATCH_STATUS if row_reason_codes else PASS_STATUS
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _reason_count(
    rows: tuple[MarketResearchBasketballCoachRotationSignalDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(ONE for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchBasketballCoachRotationSignalDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.rotation_signal_score,
        -row.signal_confidence_max,
        -row.minutes_delta_abs_max,
        -row.bench_share_delta_abs_max,
        -row.signal_age_seconds,
        row.rotation_unit_key,
        row.condition_id,
    )


def _status_rank(status: str) -> Decimal:
    if status == WATCH_STATUS:
        return WATCH_RANK
    return CLEAR_RANK


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text.removesuffix("+00:00") + "Z"
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
    if Decimal(len(reason_codes)) != Decimal(len(set(reason_codes))):
        raise ValueError(f"{name} must be unique")
    if reason_codes != _sort_reason_codes(reason_codes, allowed):
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
    if any(blocked in lowered for blocked in _BLOCKED_TEXT_PARTS):
        raise ValueError(f"{name} contains unsafe text")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized == ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


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


def _normalize_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    _require_maximum_one_decimal(name, normalized)
    return normalized


def _require_maximum_one_decimal(name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{name} must be at most 1")


def _require_flags(name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{name} {flag} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _count_decimal(value: object) -> Decimal:
    return _quantize(Decimal(value))


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(max(normalized))


def _average_or_zero(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / _count_decimal(len(normalized)))


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _quantize(value: Decimal) -> Decimal:
    try:
        normalized = value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("decimal value must be finite") from exc
    if not normalized.is_finite():
        raise ValueError("decimal value must be finite")
    return normalized
