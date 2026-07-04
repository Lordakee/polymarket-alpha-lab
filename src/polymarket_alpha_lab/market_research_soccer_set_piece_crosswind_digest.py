"""Pure soccer set-piece crosswind research digest."""

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


DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_CROSSWIND_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-set-piece-crosswind-digest-v0"
)

REDACTED_EVIDENCE_REF_VALUE = "[redacted-ref]"

CLEAR_REASON = "soccer_set_piece_crosswind_clear"
NO_ROWS_REASON = "soccer_set_piece_crosswind_rows_missing"
STALE_WEATHER_REASON = "soccer_set_piece_crosswind_stale_weather"
EVIDENCE_GAP_REASON = "soccer_set_piece_crosswind_evidence_gap"
HIGH_CROSSWIND_REASON = "soccer_set_piece_crosswind_high_crosswind"
GUST_REASON = "soccer_set_piece_crosswind_gust_risk"
HIGH_SET_PIECE_VOLUME_REASON = "soccer_set_piece_crosswind_high_set_piece_volume"
OPEN_VENUE_REASON = "soccer_set_piece_crosswind_open_venue"
REASON_CODES = (
    CLEAR_REASON,
    NO_ROWS_REASON,
    STALE_WEATHER_REASON,
    EVIDENCE_GAP_REASON,
    HIGH_CROSSWIND_REASON,
    GUST_REASON,
    HIGH_SET_PIECE_VOLUME_REASON,
    OPEN_VENUE_REASON,
)
STATUSES = ("pass", "watch", "blocked")
VENUE_EXPOSURES = ("open", "partial", "covered")
EXPOSED_VENUE_VALUES = frozenset(("open", "partial"))
BLOCKING_REASONS = frozenset((NO_ROWS_REASON, STALE_WEATHER_REASON, EVIDENCE_GAP_REASON))

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cre", "dential"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("sign", "ing"),
        _join_parts("ad", "vice"),
    ),
)
SENSITIVE_EVIDENCE_REF_FRAGMENTS = frozenset(
    (
        _join_parts("api", "_key"),
        _join_parts("bear", "er"),
        _join_parts("cre", "dential"),
        _join_parts("pass", "word"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
    ),
)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceCrosswindDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_CROSSWIND_DIGEST_CONFIG_VERSION
    )
    max_weather_age_seconds: Decimal = Decimal("7200.000000")
    min_crosswind_mph: Decimal = Decimal("15.000000")
    min_gust_wind_mph: Decimal = Decimal("25.000000")
    min_projected_set_piece_count: Decimal = Decimal("10.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_weather_age_seconds",
            "min_crosswind_mph",
            "min_gust_wind_mph",
            "min_projected_set_piece_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "MarketResearchSoccerSetPieceCrosswindDigestConfig",
            self,
        )


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceCrosswindInputRow:
    market_id: str
    event_id: str
    market_family: str
    scheduled_start_at: datetime
    weather_observed_at: datetime
    venue_exposure: str
    projected_set_piece_count: Decimal
    sustained_wind_mph: Decimal
    crosswind_mph: Decimal
    gust_wind_mph: Decimal
    evidence_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "event_id", "market_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(
            self,
            "weather_observed_at",
            _as_utc("weather_observed_at", self.weather_observed_at),
        )
        _require_member("venue_exposure", self.venue_exposure, VENUE_EXPOSURES)
        for field_name in (
            "projected_set_piece_count",
            "sustained_wind_mph",
            "crosswind_mph",
            "gust_wind_mph",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs("evidence_refs", self.evidence_refs),
        )
        require_paper_only_flags(
            "MarketResearchSoccerSetPieceCrosswindInputRow",
            self,
        )
        _validate_input_row(self)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceCrosswindDigestRow:
    market_id: str
    event_id: str
    market_family: str
    row_status: str
    scheduled_start_at: datetime
    weather_observed_at: datetime
    weather_age_seconds: Decimal
    venue_exposure: str
    projected_set_piece_count: Decimal
    sustained_wind_mph: Decimal
    crosswind_mph: Decimal
    gust_wind_mph: Decimal
    evidence_ref_count: Decimal
    redacted_evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "event_id", "market_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(
            self,
            "weather_observed_at",
            _as_utc("weather_observed_at", self.weather_observed_at),
        )
        _require_member("venue_exposure", self.venue_exposure, VENUE_EXPOSURES)
        for field_name in (
            "weather_age_seconds",
            "projected_set_piece_count",
            "sustained_wind_mph",
            "crosswind_mph",
            "gust_wind_mph",
            "evidence_ref_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_evidence_refs",
            _normalize_evidence_refs("redacted_evidence_refs", self.redacted_evidence_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags(
            "MarketResearchSoccerSetPieceCrosswindDigestRow",
            self,
        )
        _validate_digest_row(self)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceCrosswindReasonCodeCount:
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
            "MarketResearchSoccerSetPieceCrosswindReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceCrosswindDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    market_count: Decimal
    input_row_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    stale_weather_count: Decimal
    evidence_gap_count: Decimal
    high_crosswind_market_count: Decimal
    gust_market_count: Decimal
    high_set_piece_volume_market_count: Decimal
    open_venue_market_count: Decimal
    max_weather_age_seconds: Decimal
    max_crosswind_mph: Decimal
    max_gust_wind_mph: Decimal
    max_projected_set_piece_count: Decimal
    min_crosswind_mph: Decimal
    min_gust_wind_mph: Decimal
    min_projected_set_piece_count: Decimal
    rows: tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...]
    reason_code_counts: tuple[MarketResearchSoccerSetPieceCrosswindReasonCodeCount, ...]
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
            "stale_weather_count",
            "evidence_gap_count",
            "high_crosswind_market_count",
            "gust_market_count",
            "high_set_piece_volume_market_count",
            "open_venue_market_count",
            "max_weather_age_seconds",
            "max_crosswind_mph",
            "max_gust_wind_mph",
            "max_projected_set_piece_count",
            "min_crosswind_mph",
            "min_gust_wind_mph",
            "min_projected_set_piece_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            "MarketResearchSoccerSetPieceCrosswindDigest",
            self,
        )
        reject_unsafe_surface_fields(
            "market_research_soccer_set_piece_crosswind_digest",
            self,
        )
        _validate_digest(self)


def build_market_research_soccer_set_piece_crosswind_digest(
    input_rows: list[MarketResearchSoccerSetPieceCrosswindInputRow]
    | tuple[MarketResearchSoccerSetPieceCrosswindInputRow, ...],
    *,
    config: MarketResearchSoccerSetPieceCrosswindDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerSetPieceCrosswindDigest:
    if type(config) is not MarketResearchSoccerSetPieceCrosswindDigestConfig:
        raise ValueError(
            "config must be a MarketResearchSoccerSetPieceCrosswindDigestConfig",
        )
    require_paper_only_flags(
        "MarketResearchSoccerSetPieceCrosswindDigestConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    digest_rows = _digest_rows(rows, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(digest_rows)
    return MarketResearchSoccerSetPieceCrosswindDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_status_from_reason_codes(reason_codes),
        market_count=_decimal_count(len(digest_rows)),
        input_row_count=_decimal_count(len(rows)),
        pass_market_count=_status_market_count(digest_rows, "pass"),
        watch_market_count=_status_market_count(digest_rows, "watch"),
        blocked_market_count=_status_market_count(digest_rows, "blocked"),
        stale_weather_count=_reason_market_count(digest_rows, STALE_WEATHER_REASON),
        evidence_gap_count=_reason_market_count(digest_rows, EVIDENCE_GAP_REASON),
        high_crosswind_market_count=_reason_market_count(
            digest_rows,
            HIGH_CROSSWIND_REASON,
        ),
        gust_market_count=_reason_market_count(digest_rows, GUST_REASON),
        high_set_piece_volume_market_count=_reason_market_count(
            digest_rows,
            HIGH_SET_PIECE_VOLUME_REASON,
        ),
        open_venue_market_count=_reason_market_count(digest_rows, OPEN_VENUE_REASON),
        max_weather_age_seconds=(
            ZERO if not digest_rows else max(row.weather_age_seconds for row in digest_rows)
        ),
        max_crosswind_mph=(
            ZERO if not digest_rows else max(row.crosswind_mph for row in digest_rows)
        ),
        max_gust_wind_mph=(
            ZERO if not digest_rows else max(row.gust_wind_mph for row in digest_rows)
        ),
        max_projected_set_piece_count=(
            ZERO
            if not digest_rows
            else max(row.projected_set_piece_count for row in digest_rows)
        ),
        min_crosswind_mph=config.min_crosswind_mph,
        min_gust_wind_mph=config.min_gust_wind_mph,
        min_projected_set_piece_count=config.min_projected_set_piece_count,
        rows=digest_rows,
        reason_code_counts=_reason_code_counts(digest_rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_set_piece_crosswind_digest_payload(
    digest: MarketResearchSoccerSetPieceCrosswindDigest,
) -> dict[str, Any]:
    if type(digest) is not MarketResearchSoccerSetPieceCrosswindDigest:
        raise ValueError("digest must be a MarketResearchSoccerSetPieceCrosswindDigest")
    require_paper_only_flags(
        "MarketResearchSoccerSetPieceCrosswindDigest",
        digest,
    )
    ready = json_ready_no_floats(digest)
    if type(ready) is not dict:
        raise ValueError("digest must reduce to a JSON object")
    reject_unsafe_surface_fields(
        "market_research_soccer_set_piece_crosswind_digest",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResearchSoccerSetPieceCrosswindInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchSoccerSetPieceCrosswindInputRow:
            raise ValueError(
                "input rows must contain MarketResearchSoccerSetPieceCrosswindInputRow",
            )
        require_paper_only_flags(
            "MarketResearchSoccerSetPieceCrosswindInputRow",
            row,
        )
        if row.weather_observed_at > generated_at:
            raise ValueError("weather_observed_at must not be in the future")
        key = (row.market_id, row.event_id)
        if key in seen:
            raise ValueError("input rows must be unique by market and event")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_id,
                row.event_id,
                row.scheduled_start_at.isoformat(),
                row.weather_observed_at.isoformat(),
            ),
        ),
    )


def _digest_rows(
    rows: tuple[MarketResearchSoccerSetPieceCrosswindInputRow, ...],
    *,
    config: MarketResearchSoccerSetPieceCrosswindDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...]:
    return tuple(_digest_row(row, config=config, generated_at=generated_at) for row in rows)


def _digest_row(
    row: MarketResearchSoccerSetPieceCrosswindInputRow,
    *,
    config: MarketResearchSoccerSetPieceCrosswindDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerSetPieceCrosswindDigestRow:
    age_seconds = _age_seconds(generated_at, row.weather_observed_at)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        weather_age_seconds=age_seconds,
    )
    return MarketResearchSoccerSetPieceCrosswindDigestRow(
        market_id=row.market_id,
        event_id=row.event_id,
        market_family=row.market_family,
        row_status=_status_from_reason_codes(reason_codes),
        scheduled_start_at=row.scheduled_start_at,
        weather_observed_at=row.weather_observed_at,
        weather_age_seconds=age_seconds,
        venue_exposure=row.venue_exposure,
        projected_set_piece_count=row.projected_set_piece_count,
        sustained_wind_mph=row.sustained_wind_mph,
        crosswind_mph=row.crosswind_mph,
        gust_wind_mph=row.gust_wind_mph,
        evidence_ref_count=_decimal_count(len(row.evidence_refs)),
        redacted_evidence_refs=row.evidence_refs,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchSoccerSetPieceCrosswindInputRow,
    *,
    config: MarketResearchSoccerSetPieceCrosswindDigestConfig,
    weather_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    venue_exposed = row.venue_exposure in EXPOSED_VENUE_VALUES
    high_set_piece_volume = (
        row.projected_set_piece_count >= config.min_projected_set_piece_count
    )
    high_crosswind = (
        venue_exposed
        and high_set_piece_volume
        and row.crosswind_mph >= config.min_crosswind_mph
    )
    high_gust = (
        venue_exposed
        and high_set_piece_volume
        and row.gust_wind_mph >= config.min_gust_wind_mph
    )
    if weather_age_seconds > config.max_weather_age_seconds:
        reasons.add(STALE_WEATHER_REASON)
    if not row.evidence_refs:
        reasons.add(EVIDENCE_GAP_REASON)
    if high_crosswind:
        reasons.add(HIGH_CROSSWIND_REASON)
    if high_gust:
        reasons.add(GUST_REASON)
    if high_crosswind or high_gust:
        reasons.add(HIGH_SET_PIECE_VOLUME_REASON)
        if row.venue_exposure == "open":
            reasons.add(OPEN_VENUE_REASON)
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
    rows: tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...],
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
    rows: tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerSetPieceCrosswindReasonCodeCount, ...]:
    if reason_codes == (NO_ROWS_REASON,):
        return (
            MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
                reason_code=NO_ROWS_REASON,
                market_count=ZERO,
            ),
        )
    return tuple(
        MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
            reason_code=reason_code,
            market_count=_reason_market_count(rows, reason_code),
        )
        for reason_code in REASON_CODES
        if reason_code in reason_codes
    )


def _reason_market_count(
    rows: tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_market_count(
    rows: tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _normalize_digest_rows(
    value: object,
) -> tuple[MarketResearchSoccerSetPieceCrosswindDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchSoccerSetPieceCrosswindDigestRow:
            raise ValueError(
                "rows must contain MarketResearchSoccerSetPieceCrosswindDigestRow",
            )
        require_paper_only_flags(
            "MarketResearchSoccerSetPieceCrosswindDigestRow",
            row,
        )
        key = (row.market_id, row.event_id)
        if key in seen:
            raise ValueError("rows must be unique by market and event")
        seen.add(key)
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_id,
                row.event_id,
                row.scheduled_start_at.isoformat(),
                row.weather_observed_at.isoformat(),
            ),
        ),
    )
    if rows != expected:
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerSetPieceCrosswindReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_rank: int | None = None
    for row in rows:
        if type(row) is not MarketResearchSoccerSetPieceCrosswindReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerSetPieceCrosswindReasonCodeCount",
            )
        require_paper_only_flags(
            "MarketResearchSoccerSetPieceCrosswindReasonCodeCount",
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


def _normalize_evidence_refs(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(sorted(_redact_evidence_ref(item) for item in value))
    for item in normalized:
        _require_canonical_string(field_name, item)
    return normalized


def _validate_input_row(row: MarketResearchSoccerSetPieceCrosswindInputRow) -> None:
    if row.weather_observed_at > row.scheduled_start_at:
        raise ValueError("weather_observed_at must not exceed scheduled_start_at")
    if row.gust_wind_mph < row.sustained_wind_mph:
        raise ValueError("gust_wind_mph must be at least sustained_wind_mph")


def _validate_digest_row(row: MarketResearchSoccerSetPieceCrosswindDigestRow) -> None:
    if row.evidence_ref_count != _decimal_count(len(row.redacted_evidence_refs)):
        raise ValueError("evidence_ref_count must match redacted_evidence_refs")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    if row.weather_observed_at > row.scheduled_start_at:
        raise ValueError("weather_observed_at must not exceed scheduled_start_at")
    if row.gust_wind_mph < row.sustained_wind_mph:
        raise ValueError("gust_wind_mph must be at least sustained_wind_mph")


def _validate_digest(digest: MarketResearchSoccerSetPieceCrosswindDigest) -> None:
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
    if digest.stale_weather_count != _reason_market_count(
        digest.rows,
        STALE_WEATHER_REASON,
    ):
        raise ValueError("stale_weather_count must match rows")
    if digest.evidence_gap_count != _reason_market_count(
        digest.rows,
        EVIDENCE_GAP_REASON,
    ):
        raise ValueError("evidence_gap_count must match rows")
    if digest.high_crosswind_market_count != _reason_market_count(
        digest.rows,
        HIGH_CROSSWIND_REASON,
    ):
        raise ValueError("high_crosswind_market_count must match rows")
    if digest.gust_market_count != _reason_market_count(digest.rows, GUST_REASON):
        raise ValueError("gust_market_count must match rows")
    if digest.high_set_piece_volume_market_count != _reason_market_count(
        digest.rows,
        HIGH_SET_PIECE_VOLUME_REASON,
    ):
        raise ValueError("high_set_piece_volume_market_count must match rows")
    if digest.open_venue_market_count != _reason_market_count(
        digest.rows,
        OPEN_VENUE_REASON,
    ):
        raise ValueError("open_venue_market_count must match rows")
    expected_max_age = (
        ZERO if not digest.rows else max(row.weather_age_seconds for row in digest.rows)
    )
    if digest.max_weather_age_seconds != expected_max_age:
        raise ValueError("max_weather_age_seconds must match rows")
    expected_max_crosswind = (
        ZERO if not digest.rows else max(row.crosswind_mph for row in digest.rows)
    )
    if digest.max_crosswind_mph != expected_max_crosswind:
        raise ValueError("max_crosswind_mph must match rows")
    expected_max_gust = (
        ZERO if not digest.rows else max(row.gust_wind_mph for row in digest.rows)
    )
    if digest.max_gust_wind_mph != expected_max_gust:
        raise ValueError("max_gust_wind_mph must match rows")
    expected_max_set_piece_count = (
        ZERO
        if not digest.rows
        else max(row.projected_set_piece_count for row in digest.rows)
    )
    if digest.max_projected_set_piece_count != expected_max_set_piece_count:
        raise ValueError("max_projected_set_piece_count must match rows")
    if digest.reason_codes != _report_reason_codes(digest.rows):
        raise ValueError("reason_codes must match rows")
    if digest.digest_status != _status_from_reason_codes(digest.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if digest.reason_code_counts != _reason_code_counts(
        digest.rows,
        digest.reason_codes,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _redact_evidence_ref(value: object) -> str:
    if type(value) is not str:
        raise ValueError("evidence_refs must contain strings")
    if _is_blank(value):
        raise ValueError("evidence_refs must contain non-empty strings")
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_EVIDENCE_REF_FRAGMENTS):
        return REDACTED_EVIDENCE_REF_VALUE
    _require_canonical_string("evidence_refs", value)
    return value


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


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be a known value")
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
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _normalize_nonnegative_decimal(
        "weather_age_seconds",
        whole_seconds + fractional_seconds,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _is_blank(value: object) -> bool:
    return type(value) is not str or not value.strip()


__all__ = [
    "CLEAR_REASON",
    "DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_CROSSWIND_DIGEST_CONFIG_VERSION",
    "EVIDENCE_GAP_REASON",
    "GUST_REASON",
    "HIGH_CROSSWIND_REASON",
    "HIGH_SET_PIECE_VOLUME_REASON",
    "MarketResearchSoccerSetPieceCrosswindDigest",
    "MarketResearchSoccerSetPieceCrosswindDigestConfig",
    "MarketResearchSoccerSetPieceCrosswindDigestRow",
    "MarketResearchSoccerSetPieceCrosswindInputRow",
    "MarketResearchSoccerSetPieceCrosswindReasonCodeCount",
    "NO_ROWS_REASON",
    "OPEN_VENUE_REASON",
    "REDACTED_EVIDENCE_REF_VALUE",
    "STALE_WEATHER_REASON",
    "build_market_research_soccer_set_piece_crosswind_digest",
    "market_research_soccer_set_piece_crosswind_digest_payload",
]
