"""Pure baseball late scratch lineup gap research digest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_SCRATCH_LINEUP_GAP_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-late-scratch-lineup-gap-digest-v0"
)

CLEAR_REASON = "baseball_late_scratch_lineup_gap_clear"
NO_ROWS_REASON = "baseball_late_scratch_lineup_gap_rows_missing"
LATE_WINDOW_REASON = "baseball_late_scratch_lineup_gap_late_window"
CRITICAL_TIMING_REASON = "baseball_late_scratch_lineup_gap_critical_timing"
STALE_LINEUP_REASON = "baseball_late_scratch_lineup_gap_stale_lineup_confirmation"
IMPACT_REASON = "baseball_late_scratch_lineup_gap_scratched_player_impact"
SUBSTITUTE_DROP_REASON = "baseball_late_scratch_lineup_gap_substitute_quality_drop"
QUALITY_GAP_REASON = "baseball_late_scratch_lineup_gap_quality_gap"
HANDEDNESS_FIT_REASON = "baseball_late_scratch_lineup_gap_pitcher_handedness_fit"
SOURCE_DISAGREEMENT_REASON = "baseball_late_scratch_lineup_gap_source_disagreement"
UPSTREAM_CONTEXT_REASON = "baseball_late_scratch_lineup_gap_upstream_context"
REASON_CODES = (
    CLEAR_REASON,
    NO_ROWS_REASON,
    LATE_WINDOW_REASON,
    CRITICAL_TIMING_REASON,
    STALE_LINEUP_REASON,
    IMPACT_REASON,
    SUBSTITUTE_DROP_REASON,
    QUALITY_GAP_REASON,
    HANDEDNESS_FIT_REASON,
    SOURCE_DISAGREEMENT_REASON,
    UPSTREAM_CONTEXT_REASON,
)
STATUSES = ("pass", "watch", "blocked")
BLOCKING_REASONS = frozenset(
    (
        NO_ROWS_REASON,
        CRITICAL_TIMING_REASON,
        STALE_LINEUP_REASON,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
LATE_TIMING_PRESSURE = Decimal("0.100000")
CRITICAL_TIMING_PRESSURE = Decimal("0.200000")
STALE_LINEUP_PRESSURE = Decimal("0.200000")
SOURCE_DISAGREEMENT_PRESSURE = Decimal("0.100000")
SECONDS_PER_DAY = Decimal("86400.000000")
SECONDS_PER_MINUTE = Decimal("60.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("bro", "ker"),
    ),
)


@dataclass(frozen=True)
class MarketResearchBaseballLateScratchLineupGapDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_SCRATCH_LINEUP_GAP_DIGEST_CONFIG_VERSION
    )
    max_watch_minutes_to_first_pitch: Decimal = Decimal("60.000000")
    max_blocked_minutes_to_first_pitch: Decimal = Decimal("20.000000")
    max_lineup_confirmation_age_minutes: Decimal = Decimal("30.000000")
    min_scratched_player_impact_score: Decimal = Decimal("0.700000")
    max_substitute_quality_score: Decimal = Decimal("0.450000")
    min_quality_gap_score: Decimal = Decimal("0.250000")
    min_pitcher_handedness_fit_score: Decimal = Decimal("0.600000")
    min_source_disagreement_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_watch_minutes_to_first_pitch",
            "max_blocked_minutes_to_first_pitch",
            "max_lineup_confirmation_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_scratched_player_impact_score",
            "max_substitute_quality_score",
            "min_quality_gap_score",
            "min_pitcher_handedness_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_disagreement_count",
            _normalize_nonnegative_decimal(
                "min_source_disagreement_count",
                self.min_source_disagreement_count,
            ),
        )
        if self.max_blocked_minutes_to_first_pitch > self.max_watch_minutes_to_first_pitch:
            raise ValueError(
                "max_blocked_minutes_to_first_pitch must not exceed "
                "max_watch_minutes_to_first_pitch",
            )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestConfig",
            self,
        )


@dataclass(frozen=True)
class MarketResearchBaseballLateScratchLineupGapDigestInputRow:
    market_slug: str
    team: str
    opponent: str
    scratched_player_id: str
    scheduled_first_pitch_at: datetime
    lineup_confirmed_at: datetime
    source_timestamp_at: datetime
    scratched_player_impact_score: Decimal
    substitute_quality_score: Decimal
    pitcher_handedness_fit_score: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "team",
            "opponent",
            "scratched_player_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "scheduled_first_pitch_at",
            "lineup_confirmed_at",
            "source_timestamp_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scratched_player_impact_score",
            "substitute_quality_score",
            "pitcher_handedness_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_disagreement_count",
            _normalize_nonnegative_decimal(
                "source_disagreement_count",
                self.source_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestInputRow",
            self,
        )


@dataclass(frozen=True)
class MarketResearchBaseballLateScratchLineupGapDigestRow:
    market_slug: str
    team: str
    opponent: str
    scratched_player_id: str
    row_status: str
    scheduled_first_pitch_at: datetime
    lineup_confirmed_at: datetime
    source_timestamp_at: datetime
    minutes_to_first_pitch: Decimal
    lineup_confirmation_age_minutes: Decimal
    source_age_minutes: Decimal
    scratched_player_impact_score: Decimal
    substitute_quality_score: Decimal
    quality_gap_score: Decimal
    pitcher_handedness_fit_score: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    row_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "team",
            "opponent",
            "scratched_player_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("row_status", self.row_status)
        for field_name in (
            "scheduled_first_pitch_at",
            "lineup_confirmed_at",
            "source_timestamp_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minutes_to_first_pitch",
            "lineup_confirmation_age_minutes",
            "source_age_minutes",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scratched_player_impact_score",
            "substitute_quality_score",
            "quality_gap_score",
            "pitcher_handedness_fit_score",
            "row_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestRow",
            self,
        )
        _validate_digest_row(self)


@dataclass(frozen=True)
class MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount:
    reason_code: str
    market_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_decimal("market_count", self.market_count),
        )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class MarketResearchBaseballLateScratchLineupGapDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    market_count: Decimal
    input_row_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    late_window_market_count: Decimal
    critical_timing_market_count: Decimal
    stale_lineup_confirmation_market_count: Decimal
    scratched_player_impact_market_count: Decimal
    substitute_quality_drop_market_count: Decimal
    quality_gap_market_count: Decimal
    pitcher_handedness_fit_market_count: Decimal
    source_disagreement_market_count: Decimal
    upstream_context_market_count: Decimal
    risk_score: Decimal
    max_quality_gap_score: Decimal
    min_minutes_to_first_pitch: Decimal
    max_lineup_confirmation_age_minutes: Decimal
    rows: tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        for field_name in (
            "market_count",
            "input_row_count",
            "pass_market_count",
            "watch_market_count",
            "blocked_market_count",
            "late_window_market_count",
            "critical_timing_market_count",
            "stale_lineup_confirmation_market_count",
            "scratched_player_impact_market_count",
            "substitute_quality_drop_market_count",
            "quality_gap_market_count",
            "pitcher_handedness_fit_market_count",
            "source_disagreement_market_count",
            "upstream_context_market_count",
            "min_minutes_to_first_pitch",
            "max_lineup_confirmation_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("risk_score", "max_quality_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_digest_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigest",
            self,
        )
        reject_unsafe_surface_fields(
            "market_research_baseball_late_scratch_lineup_gap_digest",
            self,
        )
        _validate_digest(self)


def build_market_research_baseball_late_scratch_lineup_gap_digest(
    input_rows: list[MarketResearchBaseballLateScratchLineupGapDigestInputRow]
    | tuple[MarketResearchBaseballLateScratchLineupGapDigestInputRow, ...],
    *,
    config: MarketResearchBaseballLateScratchLineupGapDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballLateScratchLineupGapDigest:
    if type(config) is not MarketResearchBaseballLateScratchLineupGapDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBaseballLateScratchLineupGapDigestConfig",
        )
    require_paper_only_flags(
        "MarketResearchBaseballLateScratchLineupGapDigestConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    digest_rows = _digest_rows(rows, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(digest_rows)
    return MarketResearchBaseballLateScratchLineupGapDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_status_from_reason_codes(reason_codes),
        market_count=_decimal_count(len(digest_rows)),
        input_row_count=_decimal_count(len(rows)),
        pass_market_count=_status_market_count(digest_rows, "pass"),
        watch_market_count=_status_market_count(digest_rows, "watch"),
        blocked_market_count=_status_market_count(digest_rows, "blocked"),
        late_window_market_count=_reason_market_count(digest_rows, LATE_WINDOW_REASON),
        critical_timing_market_count=_reason_market_count(
            digest_rows,
            CRITICAL_TIMING_REASON,
        ),
        stale_lineup_confirmation_market_count=_reason_market_count(
            digest_rows,
            STALE_LINEUP_REASON,
        ),
        scratched_player_impact_market_count=_reason_market_count(
            digest_rows,
            IMPACT_REASON,
        ),
        substitute_quality_drop_market_count=_reason_market_count(
            digest_rows,
            SUBSTITUTE_DROP_REASON,
        ),
        quality_gap_market_count=_reason_market_count(digest_rows, QUALITY_GAP_REASON),
        pitcher_handedness_fit_market_count=_reason_market_count(
            digest_rows,
            HANDEDNESS_FIT_REASON,
        ),
        source_disagreement_market_count=_reason_market_count(
            digest_rows,
            SOURCE_DISAGREEMENT_REASON,
        ),
        upstream_context_market_count=_reason_market_count(
            digest_rows,
            UPSTREAM_CONTEXT_REASON,
        ),
        risk_score=ZERO if not digest_rows else max(row.row_risk_score for row in digest_rows),
        max_quality_gap_score=(
            ZERO if not digest_rows else max(row.quality_gap_score for row in digest_rows)
        ),
        min_minutes_to_first_pitch=(
            ZERO if not digest_rows else min(row.minutes_to_first_pitch for row in digest_rows)
        ),
        max_lineup_confirmation_age_minutes=(
            ZERO
            if not digest_rows
            else max(row.lineup_confirmation_age_minutes for row in digest_rows)
        ),
        rows=digest_rows,
        reason_code_counts=_reason_code_counts(digest_rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_research_baseball_late_scratch_lineup_gap_digest_payload(
    digest: MarketResearchBaseballLateScratchLineupGapDigest,
) -> dict[str, Any]:
    if type(digest) is not MarketResearchBaseballLateScratchLineupGapDigest:
        raise ValueError(
            "digest must be a MarketResearchBaseballLateScratchLineupGapDigest",
        )
    require_paper_only_flags(
        "MarketResearchBaseballLateScratchLineupGapDigest",
        digest,
    )
    ready = json_ready_no_floats(digest)
    if type(ready) is not dict:
        raise ValueError("digest must reduce to a JSON object")
    reject_unsafe_surface_fields(
        "market_research_baseball_late_scratch_lineup_gap_digest",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballLateScratchLineupGapDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballLateScratchLineupGapDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchBaseballLateScratchLineupGapDigestInputRow",
            )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestInputRow",
            row,
        )
        if row.scheduled_first_pitch_at < generated_at:
            raise ValueError("scheduled_first_pitch_at must not precede generated_at")
        if row.lineup_confirmed_at > generated_at:
            raise ValueError("lineup_confirmed_at must not exceed generated_at")
        if row.source_timestamp_at > generated_at:
            raise ValueError("source_timestamp_at must not exceed generated_at")
        key = (
            row.market_slug,
            row.team,
            row.opponent,
            row.scratched_player_id,
        )
        if key in seen:
            raise ValueError("input rows must be unique by market, team, and player")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_slug,
                row.team,
                row.opponent,
                row.scratched_player_id,
                row.scheduled_first_pitch_at.isoformat(),
                row.source_timestamp_at.isoformat(),
            ),
        ),
    )


def _digest_rows(
    rows: tuple[MarketResearchBaseballLateScratchLineupGapDigestInputRow, ...],
    *,
    config: MarketResearchBaseballLateScratchLineupGapDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...]:
    return tuple(_digest_row(row, config=config, generated_at=generated_at) for row in rows)


def _digest_row(
    row: MarketResearchBaseballLateScratchLineupGapDigestInputRow,
    *,
    config: MarketResearchBaseballLateScratchLineupGapDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballLateScratchLineupGapDigestRow:
    minutes_to_first_pitch = _elapsed_minutes(generated_at, row.scheduled_first_pitch_at)
    lineup_confirmation_age_minutes = _elapsed_minutes(row.lineup_confirmed_at, generated_at)
    source_age_minutes = _elapsed_minutes(row.source_timestamp_at, generated_at)
    quality_gap_score = _quality_gap_score(
        row.scratched_player_impact_score,
        row.substitute_quality_score,
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        minutes_to_first_pitch=minutes_to_first_pitch,
        lineup_confirmation_age_minutes=lineup_confirmation_age_minutes,
        quality_gap_score=quality_gap_score,
    )
    return MarketResearchBaseballLateScratchLineupGapDigestRow(
        market_slug=row.market_slug,
        team=row.team,
        opponent=row.opponent,
        scratched_player_id=row.scratched_player_id,
        row_status=_status_from_reason_codes(reason_codes),
        scheduled_first_pitch_at=row.scheduled_first_pitch_at,
        lineup_confirmed_at=row.lineup_confirmed_at,
        source_timestamp_at=row.source_timestamp_at,
        minutes_to_first_pitch=minutes_to_first_pitch,
        lineup_confirmation_age_minutes=lineup_confirmation_age_minutes,
        source_age_minutes=source_age_minutes,
        scratched_player_impact_score=row.scratched_player_impact_score,
        substitute_quality_score=row.substitute_quality_score,
        quality_gap_score=quality_gap_score,
        pitcher_handedness_fit_score=row.pitcher_handedness_fit_score,
        source_disagreement_count=row.source_disagreement_count,
        upstream_reason_codes=row.upstream_reason_codes,
        row_risk_score=_row_risk_score(reason_codes, quality_gap_score),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchBaseballLateScratchLineupGapDigestInputRow,
    *,
    config: MarketResearchBaseballLateScratchLineupGapDigestConfig,
    minutes_to_first_pitch: Decimal,
    lineup_confirmation_age_minutes: Decimal,
    quality_gap_score: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if minutes_to_first_pitch <= config.max_watch_minutes_to_first_pitch:
        reasons.add(LATE_WINDOW_REASON)
    if minutes_to_first_pitch <= config.max_blocked_minutes_to_first_pitch:
        reasons.add(CRITICAL_TIMING_REASON)
    if lineup_confirmation_age_minutes > config.max_lineup_confirmation_age_minutes:
        reasons.add(STALE_LINEUP_REASON)
    if row.scratched_player_impact_score >= config.min_scratched_player_impact_score:
        reasons.add(IMPACT_REASON)
    if row.substitute_quality_score <= config.max_substitute_quality_score:
        reasons.add(SUBSTITUTE_DROP_REASON)
    if quality_gap_score >= config.min_quality_gap_score:
        reasons.add(QUALITY_GAP_REASON)
    if row.pitcher_handedness_fit_score >= config.min_pitcher_handedness_fit_score:
        reasons.add(HANDEDNESS_FIT_REASON)
    if row.source_disagreement_count >= config.min_source_disagreement_count:
        reasons.add(SOURCE_DISAGREEMENT_REASON)
    if row.upstream_reason_codes:
        reasons.add(UPSTREAM_CONTEXT_REASON)
    return _ranked_reason_codes(reasons)


def _ranked_reason_codes(reason_codes: set[str]) -> tuple[str, ...]:
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code in reason_codes and reason_code != CLEAR_REASON
    )


def _report_reason_codes(
    rows: tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_ROWS_REASON,)
    reasons: set[str] = set()
    for row in rows:
        reasons.update(code for code in row.reason_codes if code != CLEAR_REASON)
    return _ranked_reason_codes(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount, ...]:
    if reason_codes == (NO_ROWS_REASON,):
        return (
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code=NO_ROWS_REASON,
                market_count=ZERO,
            ),
        )
    return tuple(
        MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
            reason_code=reason_code,
            market_count=_reason_market_count(rows, reason_code),
        )
        for reason_code in REASON_CODES
        if reason_code in reason_codes
    )


def _reason_market_count(
    rows: tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_market_count(
    rows: tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _normalize_digest_rows(
    value: object,
) -> tuple[MarketResearchBaseballLateScratchLineupGapDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballLateScratchLineupGapDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballLateScratchLineupGapDigestRow",
            )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestRow",
            row,
        )
        key = (
            row.market_slug,
            row.team,
            row.opponent,
            row.scratched_player_id,
        )
        if key in seen:
            raise ValueError("rows must be unique by market, team, and player")
        seen.add(key)
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_slug,
                row.team,
                row.opponent,
                row.scratched_player_id,
                row.scheduled_first_pitch_at.isoformat(),
                row.source_timestamp_at.isoformat(),
            ),
        ),
    )
    if rows != expected:
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_rank: int | None = None
    for row in rows:
        if type(row) is not MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount",
            )
        require_paper_only_flags(
            "MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount",
            row,
        )
        rank = REASON_CODES.index(row.reason_code)
        if previous_rank is not None and rank <= previous_rank:
            raise ValueError("reason_code_counts must be deterministic")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
        previous_rank = rank
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    if CLEAR_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("clear reason must be the only clear reason")
    if NO_ROWS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("missing rows reason must be the only missing rows reason")
    return reason_codes


def _normalize_upstream_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(sorted(_require_public_string(field_name, item) for item in value))
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return reason_codes


def _validate_digest_row(row: MarketResearchBaseballLateScratchLineupGapDigestRow) -> None:
    expected_gap_score = _quality_gap_score(
        row.scratched_player_impact_score,
        row.substitute_quality_score,
    )
    if row.quality_gap_score != expected_gap_score:
        raise ValueError("quality_gap_score must match impact and substitute quality")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    expected_risk_score = _row_risk_score(row.reason_codes, row.quality_gap_score)
    if row.row_risk_score != expected_risk_score:
        raise ValueError("row_risk_score must match reason_codes")
    if row.lineup_confirmed_at > row.source_timestamp_at:
        raise ValueError("lineup_confirmed_at must not exceed source_timestamp_at")


def _validate_digest(digest: MarketResearchBaseballLateScratchLineupGapDigest) -> None:
    if digest.market_count != _decimal_count(len(digest.rows)):
        raise ValueError("market_count must match rows")
    if digest.input_row_count != digest.market_count:
        raise ValueError("input_row_count must match market_count")
    if digest.pass_market_count != _status_market_count(digest.rows, "pass"):
        raise ValueError("pass_market_count must match rows")
    if digest.watch_market_count != _status_market_count(digest.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if digest.blocked_market_count != _status_market_count(digest.rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if digest.late_window_market_count != _reason_market_count(
        digest.rows,
        LATE_WINDOW_REASON,
    ):
        raise ValueError("late_window_market_count must match rows")
    if digest.critical_timing_market_count != _reason_market_count(
        digest.rows,
        CRITICAL_TIMING_REASON,
    ):
        raise ValueError("critical_timing_market_count must match rows")
    if digest.stale_lineup_confirmation_market_count != _reason_market_count(
        digest.rows,
        STALE_LINEUP_REASON,
    ):
        raise ValueError("stale_lineup_confirmation_market_count must match rows")
    if digest.scratched_player_impact_market_count != _reason_market_count(
        digest.rows,
        IMPACT_REASON,
    ):
        raise ValueError("scratched_player_impact_market_count must match rows")
    if digest.substitute_quality_drop_market_count != _reason_market_count(
        digest.rows,
        SUBSTITUTE_DROP_REASON,
    ):
        raise ValueError("substitute_quality_drop_market_count must match rows")
    if digest.quality_gap_market_count != _reason_market_count(
        digest.rows,
        QUALITY_GAP_REASON,
    ):
        raise ValueError("quality_gap_market_count must match rows")
    if digest.pitcher_handedness_fit_market_count != _reason_market_count(
        digest.rows,
        HANDEDNESS_FIT_REASON,
    ):
        raise ValueError("pitcher_handedness_fit_market_count must match rows")
    if digest.source_disagreement_market_count != _reason_market_count(
        digest.rows,
        SOURCE_DISAGREEMENT_REASON,
    ):
        raise ValueError("source_disagreement_market_count must match rows")
    if digest.upstream_context_market_count != _reason_market_count(
        digest.rows,
        UPSTREAM_CONTEXT_REASON,
    ):
        raise ValueError("upstream_context_market_count must match rows")
    expected_risk_score = ZERO if not digest.rows else max(row.row_risk_score for row in digest.rows)
    if digest.risk_score != expected_risk_score:
        raise ValueError("risk_score must match rows")
    expected_max_gap_score = (
        ZERO if not digest.rows else max(row.quality_gap_score for row in digest.rows)
    )
    if digest.max_quality_gap_score != expected_max_gap_score:
        raise ValueError("max_quality_gap_score must match rows")
    expected_min_minutes = (
        ZERO if not digest.rows else min(row.minutes_to_first_pitch for row in digest.rows)
    )
    if digest.min_minutes_to_first_pitch != expected_min_minutes:
        raise ValueError("min_minutes_to_first_pitch must match rows")
    expected_max_age = (
        ZERO
        if not digest.rows
        else max(row.lineup_confirmation_age_minutes for row in digest.rows)
    )
    if digest.max_lineup_confirmation_age_minutes != expected_max_age:
        raise ValueError("max_lineup_confirmation_age_minutes must match rows")
    if digest.reason_codes != _report_reason_codes(digest.rows):
        raise ValueError("reason_codes must match rows")
    if digest.digest_status != _status_from_reason_codes(digest.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if digest.reason_code_counts != _reason_code_counts(
        digest.rows,
        digest.reason_codes,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _quality_gap_score(impact_score: Decimal, substitute_quality_score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        gap_score = (impact_score - substitute_quality_score).quantize(QUANTUM)
    if gap_score < ZERO:
        return ZERO
    return gap_score


def _row_risk_score(
    reason_codes: tuple[str, ...],
    quality_gap_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = quality_gap_score
        if CRITICAL_TIMING_REASON in reason_codes:
            score += CRITICAL_TIMING_PRESSURE
        elif LATE_WINDOW_REASON in reason_codes:
            score += LATE_TIMING_PRESSURE
        if STALE_LINEUP_REASON in reason_codes:
            score += STALE_LINEUP_PRESSURE
        if SOURCE_DISAGREEMENT_REASON in reason_codes:
            score += SOURCE_DISAGREEMENT_PRESSURE
        if score > ONE:
            return ONE
        return score.quantize(QUANTUM)


def _require_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be safe public text")
    return text


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or _is_blank(value):
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit decimal precision") from exc


def _decimal_count(value: int) -> Decimal:
    return _normalize_nonnegative_decimal("count", Decimal(value))


def _elapsed_minutes(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    if end_utc < start_utc:
        raise ValueError("end must not precede start")
    delta = end_utc - start_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return (seconds / SECONDS_PER_MINUTE).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _is_blank(value: str) -> bool:
    return not value.strip()


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_SCRATCH_LINEUP_GAP_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballLateScratchLineupGapDigest",
    "MarketResearchBaseballLateScratchLineupGapDigestConfig",
    "MarketResearchBaseballLateScratchLineupGapDigestInputRow",
    "MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount",
    "MarketResearchBaseballLateScratchLineupGapDigestRow",
    "build_market_research_baseball_late_scratch_lineup_gap_digest",
    "market_research_baseball_late_scratch_lineup_gap_digest_payload",
)
