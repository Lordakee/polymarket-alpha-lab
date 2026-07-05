"""Pure Phase 1 reducer for basketball minutes restriction research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_MINUTES_RESTRICTION_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-minutes-restriction-digest-v0"
)
BASKETBALL_MINUTES_RESTRICTION_RESEARCH_SCOPE = (
    "basketball minutes restriction research digest only"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLOSED_INPUT_STATUS = "blocked"
CLEAR_STATUS = "clear"
DIGEST_STATUSES = (CLOSED_INPUT_STATUS, PASS_STATUS, WATCH_STATUS)
ROW_STATUSES = (CLEAR_STATUS, WATCH_STATUS)

ACTIVE_REASON = "basketball_minutes_restriction_active"
LOW_CAP_REASON = "basketball_minutes_restriction_low_cap"
GAP_REASON = "basketball_minutes_restriction_gap_high"
CONFIDENCE_REASON = "basketball_minutes_restriction_confidence_high"
STALE_REASON = "basketball_minutes_restriction_stale"
CLEAR_REASON = "basketball_minutes_restriction_clear"
PASSED_REASON = "basketball_minutes_restriction_passed"
EMPTY_REASON = "basketball_minutes_restriction_empty"

ROW_REASON_CODES = (
    ACTIVE_REASON,
    LOW_CAP_REASON,
    GAP_REASON,
    CONFIDENCE_REASON,
    STALE_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    ACTIVE_REASON,
    LOW_CAP_REASON,
    GAP_REASON,
    CONFIDENCE_REASON,
    STALE_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
NEXT_STEP_BY_STATUS = {
    CLOSED_INPUT_STATUS: "block_report_only_basketball_minutes_restrictions",
    PASS_STATUS: "continue_report_only_basketball_minutes_restriction_monitoring",
    WATCH_STATUS: "review_report_only_basketball_minutes_restrictions",
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
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_MINUTES_RESTRICTION_DIGEST_CONFIG_VERSION",
    "BASKETBALL_MINUTES_RESTRICTION_RESEARCH_SCOPE",
    "MarketResearchBasketballMinutesRestrictionDigestConfig",
    "MarketResearchBasketballMinutesRestrictionDigestSignal",
    "MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount",
    "MarketResearchBasketballMinutesRestrictionDigestRow",
    "MarketResearchBasketballMinutesRestrictionDigestReport",
    "build_market_research_basketball_minutes_restriction_digest",
    "market_research_basketball_minutes_restriction_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBasketballMinutesRestrictionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_MINUTES_RESTRICTION_DIGEST_CONFIG_VERSION
    )
    minutes_cap_threshold: Decimal = Decimal("24.000000")
    minutes_gap_threshold: Decimal = Decimal("6.000000")
    confidence_threshold: Decimal = Decimal("0.700000")
    restriction_age_seconds_threshold: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballMinutesRestrictionDigestConfig:
            raise TypeError(
                "MarketResearchBasketballMinutesRestrictionDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballMinutesRestrictionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchBasketballMinutesRestrictionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minutes_cap_threshold",
            "minutes_gap_threshold",
            "confidence_threshold",
            "restriction_age_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_maximum_one_decimal("confidence_threshold", self.confidence_threshold)
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballMinutesRestrictionDigestSignal:
    condition_id: str
    league_key: str
    team_key: str
    player_key: str
    source_ref: str
    observed_at: datetime
    projected_minutes: Decimal
    restricted_minutes_cap: Decimal | None
    restriction_confidence: Decimal
    restriction_active: bool
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_MINUTES_RESTRICTION_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballMinutesRestrictionDigestSignal:
            raise TypeError(
                "MarketResearchBasketballMinutesRestrictionDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballMinutesRestrictionDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchBasketballMinutesRestrictionDigestSignal",
            )
        for field_name in (
            "condition_id",
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
            "restricted_minutes_cap",
            _normalize_optional_nonnegative_decimal(
                "restricted_minutes_cap",
                self.restricted_minutes_cap,
            ),
        )
        object.__setattr__(
            self,
            "restriction_confidence",
            _normalize_ratio_decimal(
                "restriction_confidence",
                self.restriction_confidence,
            ),
        )
        if type(self.restriction_active) is not bool:
            raise ValueError("restriction_active must be a bool")
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount:
    reason_code: str
    player_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "player_count",
            _normalize_positive_whole_decimal("player_count", self.player_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballMinutesRestrictionDigestRow:
    condition_id: str
    league_key: str
    team_key: str
    player_key: str
    signal_count: Decimal
    observed_at_latest: datetime
    projected_minutes_max: Decimal
    restricted_minutes_cap_min: Decimal | None
    minutes_gap: Decimal
    restriction_confidence_max: Decimal
    restriction_active: bool
    restriction_age_seconds: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballMinutesRestrictionDigestRow:
            raise TypeError(
                "MarketResearchBasketballMinutesRestrictionDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballMinutesRestrictionDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchBasketballMinutesRestrictionDigestRow",
            )
        for field_name in ("condition_id", "league_key", "team_key", "player_key"):
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
        object.__setattr__(
            self,
            "projected_minutes_max",
            _normalize_nonnegative_decimal(
                "projected_minutes_max",
                self.projected_minutes_max,
            ),
        )
        object.__setattr__(
            self,
            "restricted_minutes_cap_min",
            _normalize_optional_nonnegative_decimal(
                "restricted_minutes_cap_min",
                self.restricted_minutes_cap_min,
            ),
        )
        for field_name in (
            "minutes_gap",
            "restriction_confidence_max",
            "restriction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_maximum_one_decimal(
            "restriction_confidence_max",
            self.restriction_confidence_max,
        )
        if type(self.restriction_active) is not bool:
            raise ValueError("restriction_active must be a bool")
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballMinutesRestrictionDigestReport:
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    player_count: Decimal
    signal_count: Decimal
    clear_player_count: Decimal
    watch_player_count: Decimal
    active_restriction_player_count: Decimal
    low_cap_player_count: Decimal
    high_minutes_gap_player_count: Decimal
    high_confidence_player_count: Decimal
    stale_restriction_player_count: Decimal
    minutes_cap_threshold: Decimal
    minutes_gap_threshold: Decimal
    confidence_threshold: Decimal
    restriction_age_seconds_threshold: Decimal
    max_minutes_gap: Decimal | None
    max_restriction_age_seconds: Decimal | None
    average_restriction_confidence: Decimal
    rows: tuple[MarketResearchBasketballMinutesRestrictionDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballMinutesRestrictionDigestReport:
            raise TypeError(
                "MarketResearchBasketballMinutesRestrictionDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBasketballMinutesRestrictionDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchBasketballMinutesRestrictionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_MINUTES_RESTRICTION_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball minutes restriction scope")
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "player_count",
            "signal_count",
            "clear_player_count",
            "watch_player_count",
            "active_restriction_player_count",
            "low_cap_player_count",
            "high_minutes_gap_player_count",
            "high_confidence_player_count",
            "stale_restriction_player_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minutes_cap_threshold",
            "minutes_gap_threshold",
            "confidence_threshold",
            "restriction_age_seconds_threshold",
            "average_restriction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_maximum_one_decimal("confidence_threshold", self.confidence_threshold)
        _require_maximum_one_decimal(
            "average_restriction_confidence",
            self.average_restriction_confidence,
        )
        for field_name in ("max_minutes_gap", "max_restriction_age_seconds"):
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
    MarketResearchBasketballMinutesRestrictionDigestConfig,
    MarketResearchBasketballMinutesRestrictionDigestSignal,
    MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount,
    MarketResearchBasketballMinutesRestrictionDigestRow,
    MarketResearchBasketballMinutesRestrictionDigestReport,
)


def build_market_research_basketball_minutes_restriction_digest(
    signals: Iterable[MarketResearchBasketballMinutesRestrictionDigestSignal],
    *,
    config: MarketResearchBasketballMinutesRestrictionDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballMinutesRestrictionDigestReport:
    if type(config) is not MarketResearchBasketballMinutesRestrictionDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballMinutesRestrictionDigestConfig",
        )
    _require_flags("config", config)
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
        CLOSED_INPUT_STATUS
        if not rows
        else WATCH_STATUS if row_reason_codes else PASS_STATUS
    )
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchBasketballMinutesRestrictionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_MINUTES_RESTRICTION_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        player_count=_whole(len(rows)),
        signal_count=_whole(len(signal_items)),
        clear_player_count=_whole(sum(1 for row in rows if row.digest_status == CLEAR_STATUS)),
        watch_player_count=_whole(sum(1 for row in rows if row.digest_status == WATCH_STATUS)),
        active_restriction_player_count=_whole(
            sum(1 for row in rows if ACTIVE_REASON in row.reason_codes),
        ),
        low_cap_player_count=_whole(
            sum(1 for row in rows if LOW_CAP_REASON in row.reason_codes),
        ),
        high_minutes_gap_player_count=_whole(
            sum(1 for row in rows if GAP_REASON in row.reason_codes),
        ),
        high_confidence_player_count=_whole(
            sum(1 for row in rows if CONFIDENCE_REASON in row.reason_codes),
        ),
        stale_restriction_player_count=_whole(
            sum(1 for row in rows if STALE_REASON in row.reason_codes),
        ),
        minutes_cap_threshold=config.minutes_cap_threshold,
        minutes_gap_threshold=config.minutes_gap_threshold,
        confidence_threshold=config.confidence_threshold,
        restriction_age_seconds_threshold=config.restriction_age_seconds_threshold,
        max_minutes_gap=_max_or_none(row.minutes_gap for row in rows),
        max_restriction_age_seconds=_max_or_none(
            row.restriction_age_seconds for row in rows
        ),
        average_restriction_confidence=_average_or_zero(
            row.restriction_confidence_max for row in rows
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
        reason_code_counts=_reason_code_counts(reason_codes, row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_basketball_minutes_restriction_digest_payload(
    report: MarketResearchBasketballMinutesRestrictionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballMinutesRestrictionDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBasketballMinutesRestrictionDigestReport",
        )
    _require_payload_safe_value("report", report)
    payload = _to_plain(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_rows(
    signals: tuple[MarketResearchBasketballMinutesRestrictionDigestSignal, ...],
    *,
    config: MarketResearchBasketballMinutesRestrictionDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBasketballMinutesRestrictionDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str],
        list[MarketResearchBasketballMinutesRestrictionDigestSignal],
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
        observed_at_latest = max(item.observed_at for item in sorted_signals)
        projected_minutes_max = max(item.projected_minutes for item in sorted_signals)
        cap_values = tuple(
            item.restricted_minutes_cap
            for item in sorted_signals
            if item.restricted_minutes_cap is not None
        )
        restricted_minutes_cap_min = min(cap_values) if cap_values else None
        restriction_confidence_max = max(
            item.restriction_confidence for item in sorted_signals
        )
        restriction_active = any(item.restriction_active for item in sorted_signals)
        minutes_gap = (
            _quantize(projected_minutes_max - restricted_minutes_cap_min)
            if restricted_minutes_cap_min is not None
            else ZERO.quantize(QUANTUM)
        )
        if minutes_gap < ZERO:
            minutes_gap = ZERO.quantize(QUANTUM)
        restriction_age_seconds = _quantize(
            Decimal(str((generated_at - observed_at_latest).total_seconds())),
        )
        if restriction_age_seconds < ZERO:
            raise ValueError("observed_at values must be at or before generated_at")

        reason_codes = []
        if restriction_active:
            reason_codes.append(ACTIVE_REASON)
        if (
            restricted_minutes_cap_min is not None
            and restricted_minutes_cap_min <= config.minutes_cap_threshold
        ):
            reason_codes.append(LOW_CAP_REASON)
        if minutes_gap >= config.minutes_gap_threshold:
            reason_codes.append(GAP_REASON)
        if restriction_confidence_max >= config.confidence_threshold:
            reason_codes.append(CONFIDENCE_REASON)
        if (
            restriction_active
            and restriction_age_seconds >= config.restriction_age_seconds_threshold
        ):
            reason_codes.append(STALE_REASON)
        digest_status = WATCH_STATUS if reason_codes else CLEAR_STATUS
        if not reason_codes:
            reason_codes.append(CLEAR_REASON)

        rows.append(
            MarketResearchBasketballMinutesRestrictionDigestRow(
                condition_id=condition_id,
                league_key=league_key,
                team_key=team_key,
                player_key=player_key,
                signal_count=_whole(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                projected_minutes_max=projected_minutes_max,
                restricted_minutes_cap_min=restricted_minutes_cap_min,
                minutes_gap=minutes_gap,
                restriction_confidence_max=restriction_confidence_max,
                restriction_active=restriction_active,
                restriction_age_seconds=restriction_age_seconds,
                digest_status=digest_status,
                reason_codes=tuple(reason_codes),
            ),
        )

    return tuple(
        sorted(
            rows,
            key=lambda row: (
                0 if row.digest_status == WATCH_STATUS else 1,
                -row.minutes_gap,
                -row.restriction_confidence_max,
                -row.restriction_age_seconds,
                row.player_key,
                row.condition_id,
            ),
        ),
    )


def _reason_code_counts(
    report_reason_codes: tuple[str, ...],
    row_reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount, ...]:
    if report_reason_codes == (EMPTY_REASON,):
        return (
            MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                player_count=_whole(1),
            ),
        )
    return tuple(
        MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount(
            reason_code=reason_code,
            player_count=_whole(sum(1 for item in row_reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchBasketballMinutesRestrictionDigestSignal],
) -> tuple[MarketResearchBasketballMinutesRestrictionDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchBasketballMinutesRestrictionDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchBasketballMinutesRestrictionDigestSignal records",
            )
        _require_flags("signal", signal)
        key = (signal.condition_id, signal.player_key, signal.source_ref)
        if key in seen:
            raise ValueError("signals must not contain duplicate player/source pairs")
        seen.add(key)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBasketballMinutesRestrictionDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchBasketballMinutesRestrictionDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBasketballMinutesRestrictionDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                0 if row.digest_status == WATCH_STATUS else 1,
                -row.minutes_gap,
                -row.restriction_confidence_max,
                -row.restriction_age_seconds,
                row.player_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    pairs: list[tuple[str, str]] = []
    seen_refs: set[str] = set()
    for item in value:
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
        pairs.append((source_ref, config_version))
    normalized = tuple(pairs)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    seen_reason_codes: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballMinutesRestrictionDigestReasonCodeCount "
                "records",
            )
        if item.reason_code not in DIGEST_REASON_CODES:
            raise ValueError("reason_code_counts contains invalid reason code for this field")
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


def _validate_row(row: MarketResearchBasketballMinutesRestrictionDigestRow) -> None:
    expected_status = (
        WATCH_STATUS
        if any(reason_code != CLEAR_REASON for reason_code in row.reason_codes)
        else CLEAR_STATUS
    )
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == CLEAR_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear rows must use the clear reason")
    expected_gap = (
        _quantize(row.projected_minutes_max - row.restricted_minutes_cap_min)
        if row.restricted_minutes_cap_min is not None
        else ZERO.quantize(QUANTUM)
    )
    if expected_gap < ZERO:
        expected_gap = ZERO.quantize(QUANTUM)
    if row.minutes_gap != expected_gap:
        raise ValueError("minutes_gap must match calculated value")
    if row.restricted_minutes_cap_min is None and LOW_CAP_REASON in row.reason_codes:
        raise ValueError("low cap reason requires restricted_minutes_cap_min")
    if row.restriction_active is False and STALE_REASON in row.reason_codes:
        raise ValueError("stale reason requires an active restriction")


def _validate_report(report: MarketResearchBasketballMinutesRestrictionDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.player_count != _whole(len(report.rows)):
        raise ValueError("player_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.clear_player_count != _whole(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_player_count must match rows")
    if report.watch_player_count != _whole(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_player_count must match rows")
    if report.player_count != report.clear_player_count + report.watch_player_count:
        raise ValueError("player counts must reconcile")
    if report.active_restriction_player_count != _reason_count(report.rows, ACTIVE_REASON):
        raise ValueError("active_restriction_player_count must match rows")
    if report.low_cap_player_count != _reason_count(report.rows, LOW_CAP_REASON):
        raise ValueError("low_cap_player_count must match rows")
    if report.high_minutes_gap_player_count != _reason_count(report.rows, GAP_REASON):
        raise ValueError("high_minutes_gap_player_count must match rows")
    if report.high_confidence_player_count != _reason_count(report.rows, CONFIDENCE_REASON):
        raise ValueError("high_confidence_player_count must match rows")
    if report.stale_restriction_player_count != _reason_count(report.rows, STALE_REASON):
        raise ValueError("stale_restriction_player_count must match rows")
    if report.digest_status == PASS_STATUS and any(
        reason_code not in (PASSED_REASON, EMPTY_REASON)
        for reason_code in report.reason_codes
    ):
        raise ValueError("pass reports must not include watch reasons")
    expected_digest_status = (
        CLOSED_INPUT_STATUS
        if not report.rows
        else WATCH_STATUS if report.watch_player_count > ZERO else PASS_STATUS
    )
    if report.digest_status != expected_digest_status:
        raise ValueError("digest_status must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.max_minutes_gap != _max_or_none(row.minutes_gap for row in report.rows):
        raise ValueError("max_minutes_gap must match rows")
    if report.max_restriction_age_seconds != _max_or_none(
        row.restriction_age_seconds for row in report.rows
    ):
        raise ValueError("max_restriction_age_seconds must match rows")
    if report.average_restriction_confidence != _average_or_zero(
        row.restriction_confidence_max for row in report.rows
    ):
        raise ValueError("average_restriction_confidence must match rows")
    expected_counts = _reason_code_counts(report.reason_codes, row_reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.digest_status == WATCH_STATUS and not report.reason_code_counts:
        raise ValueError("watch reports require reason counts")


def _reason_count(
    rows: tuple[MarketResearchBasketballMinutesRestrictionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if reason_code in row.reason_codes))


def _to_plain(value: Any) -> Any:
    if type(value) is Decimal:
        _require_payload_safe_value("value", value)
        return value.quantize(QUANTUM).to_eng_string()
    if type(value) is datetime:
        _require_payload_safe_value("value", value)
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("value", value)
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        _require_payload_safe_value("value", value)
        return [_to_plain(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not safe for payload serialization")


def _require_payload_safe_value(name: str, value: object) -> None:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{name} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{name} must be finite")
        try:
            quantized = value.quantize(QUANTUM)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{name} must be finite") from exc
        if value != quantized:
            raise ValueError(f"{name} must be quantized to six decimals")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{name} must be exactly datetime")
        _as_utc(name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{name} must be a known public dataclass")
        _require_flags(name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{name}[{index}]", item)
        return
    if value is None or type(value) in (str, bool):
        return
    if type(value) is int:
        raise ValueError(f"{name} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{name} must not be a float")
    if type(value) in (list, dict, set):
        raise ValueError(f"{name} must remain constructor-normalized")
    raise ValueError(f"{name} must be payload safe")


def _reconstruct_public_dataclass(name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must remain constructor-valid") from exc


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


def _normalize_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _whole(value: int) -> Decimal:
    return Decimal(value).quantize(Decimal("1"))


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _average_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return (sum(items, ZERO) / Decimal(len(items))).quantize(QUANTUM)
