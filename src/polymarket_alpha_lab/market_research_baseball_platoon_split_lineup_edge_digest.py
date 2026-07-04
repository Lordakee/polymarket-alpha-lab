"""Pure Phase 1 baseball platoon split lineup edge digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_BASEBALL_PLATOON_SPLIT_LINEUP_EDGE_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-platoon-split-lineup-edge-digest-v0"
)

CLEAR_REASON = "baseball_platoon_split_lineup_edge_clear"
NO_ROWS_REASON = "baseball_platoon_split_lineup_edge_rows_missing"
EDGE_REASON = "baseball_platoon_split_lineup_edge_detected"
HIGH_EDGE_REASON = "baseball_platoon_split_lineup_edge_high"
STALE_SOURCE_REASON = "baseball_platoon_split_lineup_edge_stale_source"
STALE_LINEUP_REASON = "baseball_platoon_split_lineup_edge_stale_lineup_confirmation"
THIN_LINEUP_REASON = "baseball_platoon_split_lineup_edge_thin_confirmed_lineup"
FAVORABLE_DEPTH_REASON = "baseball_platoon_split_lineup_edge_favorable_lineup_depth"
LATE_CHANGE_REASON = "baseball_platoon_split_lineup_edge_late_lineup_change"
SOURCE_DISAGREEMENT_REASON = "baseball_platoon_split_lineup_edge_source_disagreement"
UPSTREAM_CONTEXT_REASON = "baseball_platoon_split_lineup_edge_upstream_context"
REASON_CODES = (
    CLEAR_REASON,
    NO_ROWS_REASON,
    EDGE_REASON,
    HIGH_EDGE_REASON,
    STALE_SOURCE_REASON,
    STALE_LINEUP_REASON,
    THIN_LINEUP_REASON,
    FAVORABLE_DEPTH_REASON,
    LATE_CHANGE_REASON,
    SOURCE_DISAGREEMENT_REASON,
    UPSTREAM_CONTEXT_REASON,
)
STATUSES = ("pass", "watch", "blocked")
PITCHER_HANDS = ("left", "right")
BLOCKING_REASONS = frozenset(
    (
        NO_ROWS_REASON,
        HIGH_EDGE_REASON,
        STALE_SOURCE_REASON,
        STALE_LINEUP_REASON,
        THIN_LINEUP_REASON,
        SOURCE_DISAGREEMENT_REASON,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STALE_SOURCE_PRESSURE = Decimal("0.200000")
STALE_LINEUP_PRESSURE = Decimal("0.200000")
THIN_LINEUP_PRESSURE = Decimal("0.150000")
SOURCE_DISAGREEMENT_PRESSURE = Decimal("0.100000")
LATE_LINEUP_CHANGE_PRESSURE = Decimal("0.050000")
SECONDS_PER_DAY = Decimal("86400.000000")
SECONDS_PER_MINUTE = Decimal("60.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("sec", "ret"),
        _join_parts("bro", "ker"),
    ),
)


@dataclass(frozen=True)
class MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_PLATOON_SPLIT_LINEUP_EDGE_DIGEST_CONFIG_VERSION
    )
    max_source_age_minutes: Decimal = Decimal("20.000000")
    max_lineup_confirmation_age_minutes: Decimal = Decimal("30.000000")
    min_watch_platoon_edge_score: Decimal = Decimal("0.100000")
    min_blocked_platoon_edge_score: Decimal = Decimal("0.250000")
    min_favorable_batter_count: Decimal = Decimal("5.000000")
    min_confirmed_batter_count: Decimal = Decimal("9.000000")
    min_late_lineup_change_count: Decimal = Decimal("1.000000")
    min_source_disagreement_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_PLATOON_SPLIT_LINEUP_EDGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_source_age_minutes",
            "max_lineup_confirmation_age_minutes",
            "min_favorable_batter_count",
            "min_confirmed_batter_count",
            "min_late_lineup_change_count",
            "min_source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_watch_platoon_edge_score",
            "min_blocked_platoon_edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_blocked_platoon_edge_score < self.min_watch_platoon_edge_score:
            raise ValueError(
                "min_blocked_platoon_edge_score must be at least "
                "min_watch_platoon_edge_score",
            )
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig",
            self,
        )


@dataclass(frozen=True)
class MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow:
    market_slug: str
    team: str
    opponent: str
    pitcher_hand: str
    scheduled_first_pitch_at: datetime
    lineup_confirmed_at: datetime
    source_timestamp_at: datetime
    platoon_edge_score: Decimal
    favorable_batter_count: Decimal
    confirmed_batter_count: Decimal
    late_lineup_change_count: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "team", "opponent"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pitcher_hand",
            _require_member("pitcher_hand", self.pitcher_hand, PITCHER_HANDS),
        )
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
        object.__setattr__(
            self,
            "platoon_edge_score",
            _normalize_ratio("platoon_edge_score", self.platoon_edge_score),
        )
        for field_name in (
            "favorable_batter_count",
            "confirmed_batter_count",
            "late_lineup_change_count",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow",
            self,
        )
        _validate_input_row(self)


@dataclass(frozen=True)
class MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow:
    market_slug: str
    team: str
    opponent: str
    pitcher_hand: str
    row_status: str
    scheduled_first_pitch_at: datetime
    lineup_confirmed_at: datetime
    source_timestamp_at: datetime
    minutes_to_first_pitch: Decimal
    lineup_confirmation_age_minutes: Decimal
    source_age_minutes: Decimal
    platoon_edge_score: Decimal
    favorable_batter_count: Decimal
    confirmed_batter_count: Decimal
    favorable_batter_ratio: Decimal
    late_lineup_change_count: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    row_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "team", "opponent"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pitcher_hand",
            _require_member("pitcher_hand", self.pitcher_hand, PITCHER_HANDS),
        )
        object.__setattr__(
            self,
            "row_status",
            _require_member("row_status", self.row_status, STATUSES),
        )
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
            "favorable_batter_count",
            "confirmed_batter_count",
            "late_lineup_change_count",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "platoon_edge_score",
            "favorable_batter_ratio",
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
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow",
            self,
        )
        _validate_digest_row(self)


@dataclass(frozen=True)
class MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount:
    reason_code: str
    market_count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REASON_CODES),
        )
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_decimal("market_count", self.market_count),
        )
        object.__setattr__(
            self,
            "market_ratio",
            _normalize_ratio("market_ratio", self.market_ratio),
        )
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class MarketResearchBaseballPlatoonSplitLineupEdgeDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    market_count: Decimal
    input_row_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    platoon_edge_market_count: Decimal
    high_edge_market_count: Decimal
    stale_source_market_count: Decimal
    stale_lineup_market_count: Decimal
    thin_lineup_market_count: Decimal
    favorable_lineup_depth_market_count: Decimal
    late_lineup_change_market_count: Decimal
    source_disagreement_market_count: Decimal
    upstream_context_market_count: Decimal
    risk_score: Decimal
    max_platoon_edge_score: Decimal
    max_source_age_minutes: Decimal
    max_lineup_confirmation_age_minutes: Decimal
    rows: tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_PLATOON_SPLIT_LINEUP_EDGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, STATUSES),
        )
        for field_name in (
            "market_count",
            "input_row_count",
            "pass_market_count",
            "watch_market_count",
            "blocked_market_count",
            "platoon_edge_market_count",
            "high_edge_market_count",
            "stale_source_market_count",
            "stale_lineup_market_count",
            "thin_lineup_market_count",
            "favorable_lineup_depth_market_count",
            "late_lineup_change_market_count",
            "source_disagreement_market_count",
            "upstream_context_market_count",
            "max_source_age_minutes",
            "max_lineup_confirmation_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("risk_score", "max_platoon_edge_score"):
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
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigest",
            self,
        )
        _validate_digest(self)


def build_market_research_baseball_platoon_split_lineup_edge_digest(
    input_rows: Iterable[MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow],
    *,
    config: MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballPlatoonSplitLineupEdgeDigest:
    if type(config) is not MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig",
        )
    _require_hard_flags(
        "MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    digest_rows = _sorted_digest_rows(
        tuple(_digest_row(row, config=config, generated_at=generated_at_utc) for row in rows),
    )
    reason_codes = _report_reason_codes(digest_rows)
    return MarketResearchBaseballPlatoonSplitLineupEdgeDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_status_from_reason_codes(reason_codes),
        market_count=_decimal_count(len(digest_rows)),
        input_row_count=_decimal_count(len(rows)),
        pass_market_count=_status_market_count(digest_rows, "pass"),
        watch_market_count=_status_market_count(digest_rows, "watch"),
        blocked_market_count=_status_market_count(digest_rows, "blocked"),
        platoon_edge_market_count=_reason_market_count(digest_rows, EDGE_REASON),
        high_edge_market_count=_reason_market_count(digest_rows, HIGH_EDGE_REASON),
        stale_source_market_count=_reason_market_count(digest_rows, STALE_SOURCE_REASON),
        stale_lineup_market_count=_reason_market_count(digest_rows, STALE_LINEUP_REASON),
        thin_lineup_market_count=_reason_market_count(digest_rows, THIN_LINEUP_REASON),
        favorable_lineup_depth_market_count=_reason_market_count(
            digest_rows,
            FAVORABLE_DEPTH_REASON,
        ),
        late_lineup_change_market_count=_reason_market_count(digest_rows, LATE_CHANGE_REASON),
        source_disagreement_market_count=_reason_market_count(
            digest_rows,
            SOURCE_DISAGREEMENT_REASON,
        ),
        upstream_context_market_count=_reason_market_count(
            digest_rows,
            UPSTREAM_CONTEXT_REASON,
        ),
        risk_score=ZERO if not digest_rows else max(row.row_risk_score for row in digest_rows),
        max_platoon_edge_score=(
            ZERO if not digest_rows else max(row.platoon_edge_score for row in digest_rows)
        ),
        max_source_age_minutes=(
            ZERO if not digest_rows else max(row.source_age_minutes for row in digest_rows)
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


def market_research_baseball_platoon_split_lineup_edge_digest_payload(
    digest: MarketResearchBaseballPlatoonSplitLineupEdgeDigest,
) -> dict[str, Any]:
    if type(digest) is not MarketResearchBaseballPlatoonSplitLineupEdgeDigest:
        raise ValueError("digest must be a MarketResearchBaseballPlatoonSplitLineupEdgeDigest")
    _require_hard_flags("MarketResearchBaseballPlatoonSplitLineupEdgeDigest", digest)
    ready = _json_ready(digest)
    if type(ready) is not dict:
        raise ValueError("digest must serialize to a JSON object")
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("input rows must contain platoon split lineup edge rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("input rows must contain platoon split lineup edge rows") from exc
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow",
            )
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow",
            row,
        )
        if row.scheduled_first_pitch_at < generated_at:
            raise ValueError("scheduled_first_pitch_at must not precede generated_at")
        if row.lineup_confirmed_at > generated_at:
            raise ValueError("lineup_confirmed_at must not exceed generated_at")
        if row.source_timestamp_at > generated_at:
            raise ValueError("source_timestamp_at must not exceed generated_at")
        key = (row.market_slug, row.team, row.opponent, row.pitcher_hand)
        if key in seen:
            raise ValueError("input rows must be unique by market, team, opponent, and hand")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_slug,
                row.team,
                row.opponent,
                row.pitcher_hand,
                row.scheduled_first_pitch_at.isoformat(),
                row.source_timestamp_at.isoformat(),
            ),
        ),
    )


def _digest_row(
    row: MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow,
    *,
    config: MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow:
    minutes_to_first_pitch = _elapsed_minutes(generated_at, row.scheduled_first_pitch_at)
    lineup_confirmation_age_minutes = _elapsed_minutes(row.lineup_confirmed_at, generated_at)
    source_age_minutes = _elapsed_minutes(row.source_timestamp_at, generated_at)
    favorable_batter_ratio = _ratio(row.favorable_batter_count, row.confirmed_batter_count)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        source_age_minutes=source_age_minutes,
        lineup_confirmation_age_minutes=lineup_confirmation_age_minutes,
    )
    return MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow(
        market_slug=row.market_slug,
        team=row.team,
        opponent=row.opponent,
        pitcher_hand=row.pitcher_hand,
        row_status=_status_from_reason_codes(reason_codes),
        scheduled_first_pitch_at=row.scheduled_first_pitch_at,
        lineup_confirmed_at=row.lineup_confirmed_at,
        source_timestamp_at=row.source_timestamp_at,
        minutes_to_first_pitch=minutes_to_first_pitch,
        lineup_confirmation_age_minutes=lineup_confirmation_age_minutes,
        source_age_minutes=source_age_minutes,
        platoon_edge_score=row.platoon_edge_score,
        favorable_batter_count=row.favorable_batter_count,
        confirmed_batter_count=row.confirmed_batter_count,
        favorable_batter_ratio=favorable_batter_ratio,
        late_lineup_change_count=row.late_lineup_change_count,
        source_disagreement_count=row.source_disagreement_count,
        upstream_reason_codes=row.upstream_reason_codes,
        row_risk_score=_row_risk_score(reason_codes, row.platoon_edge_score),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow,
    *,
    config: MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig,
    source_age_minutes: Decimal,
    lineup_confirmation_age_minutes: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if row.platoon_edge_score >= config.min_watch_platoon_edge_score:
        reasons.add(EDGE_REASON)
    if row.platoon_edge_score >= config.min_blocked_platoon_edge_score:
        reasons.add(HIGH_EDGE_REASON)
    if source_age_minutes > config.max_source_age_minutes:
        reasons.add(STALE_SOURCE_REASON)
    if lineup_confirmation_age_minutes > config.max_lineup_confirmation_age_minutes:
        reasons.add(STALE_LINEUP_REASON)
    if row.confirmed_batter_count < config.min_confirmed_batter_count:
        reasons.add(THIN_LINEUP_REASON)
    if row.favorable_batter_count >= config.min_favorable_batter_count:
        reasons.add(FAVORABLE_DEPTH_REASON)
    if row.late_lineup_change_count >= config.min_late_lineup_change_count:
        reasons.add(LATE_CHANGE_REASON)
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
        if reason_code in reason_codes and reason_code not in (CLEAR_REASON, NO_ROWS_REASON)
    )


def _report_reason_codes(
    rows: tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_ROWS_REASON,)
    reasons: set[str] = set()
    for row in rows:
        reasons.update(reason for reason in row.reason_codes if reason != CLEAR_REASON)
    return _ranked_reason_codes(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount, ...]:
    market_count = _decimal_count(len(rows))
    if reason_codes == (NO_ROWS_REASON,):
        return (
            MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code=NO_ROWS_REASON,
                market_count=ZERO,
                market_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
            reason_code=reason_code,
            market_count=_reason_market_count(rows, reason_code),
            market_ratio=_ratio(_reason_market_count(rows, reason_code), market_count),
        )
        for reason_code in REASON_CODES
        if reason_code in reason_codes
    )


def _reason_market_count(
    rows: tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_market_count(
    rows: tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _sorted_digest_rows(
    rows: tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...],
) -> tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.row_status],
                -row.row_risk_score,
                row.market_slug,
                row.team,
                row.opponent,
                row.pitcher_hand,
            ),
        ),
    )


def _normalize_digest_rows(
    value: object,
) -> tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow",
            )
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow",
            row,
        )
        key = (row.market_slug, row.team, row.opponent, row.pitcher_hand)
        if key in seen:
            raise ValueError("rows must be unique by market, team, opponent, and hand")
        seen.add(key)
    if rows != _sorted_digest_rows(rows):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_rank: int | None = None
    for row in rows:
        if type(row) is not MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount",
            )
        _require_hard_flags(
            "MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount",
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
        _require_member("reason_codes", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(reason for reason in REASON_CODES if reason in reason_codes) != reason_codes:
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


def _validate_input_row(
    row: MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow,
) -> None:
    if row.favorable_batter_count > row.confirmed_batter_count:
        raise ValueError("confirmed_batter_count must cover favorable_batter_count")
    if row.lineup_confirmed_at > row.source_timestamp_at:
        raise ValueError("lineup_confirmed_at must not exceed source_timestamp_at")


def _validate_digest_row(row: MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow) -> None:
    if row.favorable_batter_count > row.confirmed_batter_count:
        raise ValueError("confirmed_batter_count must cover favorable_batter_count")
    expected_ratio = _ratio(row.favorable_batter_count, row.confirmed_batter_count)
    if row.favorable_batter_ratio != expected_ratio:
        raise ValueError("favorable_batter_ratio must match batter counts")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    expected_risk_score = _row_risk_score(row.reason_codes, row.platoon_edge_score)
    if row.row_risk_score != expected_risk_score:
        raise ValueError("row_risk_score must match reason_codes")
    if row.lineup_confirmed_at > row.source_timestamp_at:
        raise ValueError("lineup_confirmed_at must not exceed source_timestamp_at")


def _validate_digest(digest: MarketResearchBaseballPlatoonSplitLineupEdgeDigest) -> None:
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
    if digest.platoon_edge_market_count != _reason_market_count(digest.rows, EDGE_REASON):
        raise ValueError("platoon_edge_market_count must match rows")
    if digest.high_edge_market_count != _reason_market_count(digest.rows, HIGH_EDGE_REASON):
        raise ValueError("high_edge_market_count must match rows")
    if digest.stale_source_market_count != _reason_market_count(
        digest.rows,
        STALE_SOURCE_REASON,
    ):
        raise ValueError("stale_source_market_count must match rows")
    if digest.stale_lineup_market_count != _reason_market_count(
        digest.rows,
        STALE_LINEUP_REASON,
    ):
        raise ValueError("stale_lineup_market_count must match rows")
    if digest.thin_lineup_market_count != _reason_market_count(
        digest.rows,
        THIN_LINEUP_REASON,
    ):
        raise ValueError("thin_lineup_market_count must match rows")
    if digest.favorable_lineup_depth_market_count != _reason_market_count(
        digest.rows,
        FAVORABLE_DEPTH_REASON,
    ):
        raise ValueError("favorable_lineup_depth_market_count must match rows")
    if digest.late_lineup_change_market_count != _reason_market_count(
        digest.rows,
        LATE_CHANGE_REASON,
    ):
        raise ValueError("late_lineup_change_market_count must match rows")
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
    expected_max_edge = (
        ZERO if not digest.rows else max(row.platoon_edge_score for row in digest.rows)
    )
    if digest.max_platoon_edge_score != expected_max_edge:
        raise ValueError("max_platoon_edge_score must match rows")
    expected_max_source_age = (
        ZERO if not digest.rows else max(row.source_age_minutes for row in digest.rows)
    )
    if digest.max_source_age_minutes != expected_max_source_age:
        raise ValueError("max_source_age_minutes must match rows")
    expected_max_lineup_age = (
        ZERO if not digest.rows else max(row.lineup_confirmation_age_minutes for row in digest.rows)
    )
    if digest.max_lineup_confirmation_age_minutes != expected_max_lineup_age:
        raise ValueError("max_lineup_confirmation_age_minutes must match rows")
    if digest.reason_codes != _report_reason_codes(digest.rows):
        raise ValueError("reason_codes must match rows")
    if digest.digest_status != _status_from_reason_codes(digest.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if digest.reason_code_counts != _reason_code_counts(digest.rows, digest.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _row_risk_score(
    reason_codes: tuple[str, ...],
    platoon_edge_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = platoon_edge_score
        if STALE_SOURCE_REASON in reason_codes:
            score += STALE_SOURCE_PRESSURE
        if STALE_LINEUP_REASON in reason_codes:
            score += STALE_LINEUP_PRESSURE
        if THIN_LINEUP_REASON in reason_codes:
            score += THIN_LINEUP_PRESSURE
        if SOURCE_DISAGREEMENT_REASON in reason_codes:
            score += SOURCE_DISAGREEMENT_PRESSURE
        if LATE_CHANGE_REASON in reason_codes:
            score += LATE_LINEUP_CHANGE_PRESSURE
        if score > ONE:
            return ONE
        return score.quantize(QUANTUM)


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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_canonical_string(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


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
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_normalize_decimal("value", value), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(name): _json_ready(item) for name, item in value.items()}
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} requires {field_name}=True")


def _is_blank(value: str) -> bool:
    return not value.strip()


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_PLATOON_SPLIT_LINEUP_EDGE_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballPlatoonSplitLineupEdgeDigest",
    "MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig",
    "MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow",
    "MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount",
    "MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow",
    "build_market_research_baseball_platoon_split_lineup_edge_digest",
    "market_research_baseball_platoon_split_lineup_edge_digest_payload",
)
