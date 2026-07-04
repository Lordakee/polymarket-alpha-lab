"""Pure Phase 1 soccer set-piece xG swing digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_SOCCER_SET_PIECE_XG_SWING_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-set-piece-xg-swing-digest-v0"
)

XG_SWING_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "soccer_set_piece_xg_swing_set_piece_xg_delta",
    "soccer_set_piece_xg_swing_high_set_piece_share",
    "soccer_set_piece_xg_swing_corner_pressure_delta",
    "soccer_set_piece_xg_swing_aerial_mismatch",
    "soccer_set_piece_xg_swing_foul_zone_pressure",
    "soccer_set_piece_xg_swing_primary_taker_change",
    "soccer_set_piece_xg_swing_blocked",
    "soccer_set_piece_xg_swing_watch",
    "soccer_set_piece_xg_swing_clear",
)
REPORT_REASON_CODES = (
    "soccer_set_piece_xg_swing_blocked_present",
    "soccer_set_piece_xg_swing_watch_present",
    "soccer_set_piece_xg_swing_delta_present",
    "soccer_set_piece_xg_swing_share_present",
    "soccer_set_piece_xg_swing_corner_pressure_present",
    "soccer_set_piece_xg_swing_aerial_mismatch_present",
    "soccer_set_piece_xg_swing_foul_zone_present",
    "soccer_set_piece_xg_swing_taker_change_present",
    "soccer_set_piece_xg_swing_digest_clear",
    "soccer_set_piece_xg_swing_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_DENOMINATOR = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def _join_text(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_text("api", "_key"),
        _join_text("bear", "er"),
        _join_text("cre", "dential"),
        _join_text("pri", "vate"),
        _join_text("sec", "ret"),
        _join_text("to", "ken"),
        _join_text("wal", "let"),
        _join_text("tra", "ding"),
        _join_text("au", "th"),
        _join_text("ord", "er"),
        _join_text("can", "cel"),
        _join_text("rep", "lace"),
        _join_text("ex", "change"),
    ),
)


__all__ = (
    "DEFAULT_SOCCER_SET_PIECE_XG_SWING_DIGEST_CONFIG_VERSION",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "SoccerSetPieceXgSwingDigestConfig",
    "SoccerSetPieceXgSwingDigestReport",
    "SoccerSetPieceXgSwingDigestRow",
    "SoccerSetPieceXgSwingObservation",
    "SoccerSetPieceXgSwingReasonCodeCount",
    "build_market_research_soccer_set_piece_xg_swing_digest",
    "market_research_soccer_set_piece_xg_swing_digest_payload",
)


@dataclass(frozen=True)
class SoccerSetPieceXgSwingDigestConfig:
    config_version: str = DEFAULT_SOCCER_SET_PIECE_XG_SWING_DIGEST_CONFIG_VERSION
    material_set_piece_xg_delta: Decimal = Decimal("0.120000")
    high_set_piece_xg_share: Decimal = Decimal("0.350000")
    corner_pressure_delta: Decimal = Decimal("3.000000")
    aerial_mismatch_score: Decimal = Decimal("0.600000")
    foul_zone_entry_delta: Decimal = Decimal("4.000000")
    primary_taker_change_signal: Decimal = Decimal("0.500000")
    watch_xg_swing_signal_count: Decimal = Decimal("3.000000")
    blocked_xg_swing_signal_count: Decimal = Decimal("5.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SoccerSetPieceXgSwingDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_SOCCER_SET_PIECE_XG_SWING_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "material_set_piece_xg_delta",
            "corner_pressure_delta",
            "foul_zone_entry_delta",
            "watch_xg_swing_signal_count",
            "blocked_xg_swing_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_set_piece_xg_share",
            "aerial_mismatch_score",
            "primary_taker_change_signal",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_xg_swing_signal_count > self.blocked_xg_swing_signal_count:
            raise ValueError(
                "watch_xg_swing_signal_count must not exceed "
                "blocked_xg_swing_signal_count",
            )
        if self.blocked_xg_swing_signal_count > SIGNAL_DENOMINATOR:
            raise ValueError("blocked_xg_swing_signal_count must not exceed signal count")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SoccerSetPieceXgSwingObservation:
    source_id: str
    match_id: str
    market_slug: str
    club: str
    opponent: str
    baseline_set_piece_xg: Decimal
    projected_set_piece_xg: Decimal
    set_piece_xg_share: Decimal
    corner_pressure_delta: Decimal
    aerial_mismatch_score: Decimal
    foul_zone_entry_delta: Decimal
    primary_taker_change_signal: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SoccerSetPieceXgSwingObservation, "observation")
        for field_name in ("source_id", "match_id", "market_slug", "club", "opponent"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("baseline_set_piece_xg", "projected_set_piece_xg"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "set_piece_xg_share",
            _require_ratio("set_piece_xg_share", self.set_piece_xg_share),
        )
        for field_name in ("corner_pressure_delta", "foul_zone_entry_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("aerial_mismatch_score", "primary_taker_change_signal"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class SoccerSetPieceXgSwingDigestRow:
    source_id: str
    match_id: str
    market_slug: str
    club: str
    opponent: str
    baseline_set_piece_xg: Decimal
    projected_set_piece_xg: Decimal
    set_piece_xg_delta: Decimal
    absolute_set_piece_xg_delta: Decimal
    set_piece_xg_share: Decimal
    corner_pressure_delta: Decimal
    absolute_corner_pressure_delta: Decimal
    aerial_mismatch_score: Decimal
    foul_zone_entry_delta: Decimal
    absolute_foul_zone_entry_delta: Decimal
    primary_taker_change_signal: Decimal
    xg_swing_signal_count: Decimal
    xg_swing_pressure_score: Decimal
    observed_at: datetime
    xg_swing_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SoccerSetPieceXgSwingDigestRow, "row")
        for field_name in ("source_id", "match_id", "market_slug", "club", "opponent"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "baseline_set_piece_xg",
            "projected_set_piece_xg",
            "absolute_set_piece_xg_delta",
            "absolute_corner_pressure_delta",
            "aerial_mismatch_score",
            "absolute_foul_zone_entry_delta",
            "xg_swing_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "set_piece_xg_delta",
            "corner_pressure_delta",
            "foul_zone_entry_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "set_piece_xg_share",
            "primary_taker_change_signal",
            "xg_swing_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("xg_swing_status", self.xg_swing_status, XG_SWING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SoccerSetPieceXgSwingReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SoccerSetPieceXgSwingReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class SoccerSetPieceXgSwingDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    material_xg_delta_count: Decimal
    high_set_piece_share_count: Decimal
    corner_pressure_count: Decimal
    aerial_mismatch_count: Decimal
    foul_zone_pressure_count: Decimal
    primary_taker_change_count: Decimal
    max_xg_swing_pressure_score: Decimal
    average_xg_swing_pressure_score: Decimal
    max_absolute_set_piece_xg_delta: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...]
    reason_code_counts: tuple[SoccerSetPieceXgSwingReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SoccerSetPieceXgSwingDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_SOCCER_SET_PIECE_XG_SWING_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "material_xg_delta_count",
            "high_set_piece_share_count",
            "corner_pressure_count",
            "aerial_mismatch_count",
            "foul_zone_pressure_count",
            "primary_taker_change_count",
            "max_xg_swing_pressure_score",
            "average_xg_swing_pressure_score",
            "max_absolute_set_piece_xg_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("max_xg_swing_pressure_score", self.max_xg_swing_pressure_score)
        _require_ratio(
            "average_xg_swing_pressure_score",
            self.average_xg_swing_pressure_score,
        )
        _require_member("digest_status", self.digest_status, XG_SWING_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_soccer_set_piece_xg_swing_digest(
    observations: Iterable[SoccerSetPieceXgSwingObservation],
    *,
    config: SoccerSetPieceXgSwingDigestConfig,
    generated_at: datetime,
) -> SoccerSetPieceXgSwingDigestReport:
    if type(config) is not SoccerSetPieceXgSwingDigestConfig:
        raise ValueError("config must be exactly SoccerSetPieceXgSwingDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return SoccerSetPieceXgSwingDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        material_xg_delta_count=_reason_count(
            rows,
            "soccer_set_piece_xg_swing_set_piece_xg_delta",
        ),
        high_set_piece_share_count=_reason_count(
            rows,
            "soccer_set_piece_xg_swing_high_set_piece_share",
        ),
        corner_pressure_count=_reason_count(
            rows,
            "soccer_set_piece_xg_swing_corner_pressure_delta",
        ),
        aerial_mismatch_count=_reason_count(
            rows,
            "soccer_set_piece_xg_swing_aerial_mismatch",
        ),
        foul_zone_pressure_count=_reason_count(
            rows,
            "soccer_set_piece_xg_swing_foul_zone_pressure",
        ),
        primary_taker_change_count=_reason_count(
            rows,
            "soccer_set_piece_xg_swing_primary_taker_change",
        ),
        max_xg_swing_pressure_score=_max_row_decimal(
            rows,
            "xg_swing_pressure_score",
        ),
        average_xg_swing_pressure_score=_ratio(
            _sum_decimal(row.xg_swing_pressure_score for row in rows),
            row_count,
        ),
        max_absolute_set_piece_xg_delta=_max_row_decimal(
            rows,
            "absolute_set_piece_xg_delta",
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_soccer_set_piece_xg_swing_digest_payload(
    report: SoccerSetPieceXgSwingDigestReport,
) -> dict[str, Any]:
    if type(report) is not SoccerSetPieceXgSwingDigestReport:
        raise ValueError("report must be exactly SoccerSetPieceXgSwingDigestReport")
    _require_hard_flags("report", report)
    return _payload_value(report)


def _row_from_observation(
    observation: SoccerSetPieceXgSwingObservation,
    *,
    config: SoccerSetPieceXgSwingDigestConfig,
) -> SoccerSetPieceXgSwingDigestRow:
    reason_codes = _signal_reason_codes(observation, config=config)
    signal_count = _count_decimal(len(reason_codes))
    xg_swing_status = _xg_swing_status(signal_count, config=config)
    row_reason_codes = _row_reason_codes(reason_codes, xg_swing_status)
    xg_delta = _quantize_decimal(
        observation.projected_set_piece_xg - observation.baseline_set_piece_xg,
    )
    return SoccerSetPieceXgSwingDigestRow(
        source_id=observation.source_id,
        match_id=observation.match_id,
        market_slug=observation.market_slug,
        club=observation.club,
        opponent=observation.opponent,
        baseline_set_piece_xg=observation.baseline_set_piece_xg,
        projected_set_piece_xg=observation.projected_set_piece_xg,
        set_piece_xg_delta=xg_delta,
        absolute_set_piece_xg_delta=_quantize_decimal(abs(xg_delta)),
        set_piece_xg_share=observation.set_piece_xg_share,
        corner_pressure_delta=observation.corner_pressure_delta,
        absolute_corner_pressure_delta=_quantize_decimal(
            abs(observation.corner_pressure_delta),
        ),
        aerial_mismatch_score=observation.aerial_mismatch_score,
        foul_zone_entry_delta=observation.foul_zone_entry_delta,
        absolute_foul_zone_entry_delta=_quantize_decimal(
            abs(observation.foul_zone_entry_delta),
        ),
        primary_taker_change_signal=observation.primary_taker_change_signal,
        xg_swing_signal_count=signal_count,
        xg_swing_pressure_score=_ratio(signal_count, SIGNAL_DENOMINATOR),
        observed_at=observation.observed_at,
        xg_swing_status=xg_swing_status,
        reason_codes=row_reason_codes,
    )


def _signal_reason_codes(
    observation: SoccerSetPieceXgSwingObservation,
    *,
    config: SoccerSetPieceXgSwingDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    xg_delta = _quantize_decimal(
        observation.projected_set_piece_xg - observation.baseline_set_piece_xg,
    )
    if abs(xg_delta) >= config.material_set_piece_xg_delta:
        reason_codes.append("soccer_set_piece_xg_swing_set_piece_xg_delta")
    if observation.set_piece_xg_share >= config.high_set_piece_xg_share:
        reason_codes.append("soccer_set_piece_xg_swing_high_set_piece_share")
    if abs(observation.corner_pressure_delta) >= config.corner_pressure_delta:
        reason_codes.append("soccer_set_piece_xg_swing_corner_pressure_delta")
    if observation.aerial_mismatch_score >= config.aerial_mismatch_score:
        reason_codes.append("soccer_set_piece_xg_swing_aerial_mismatch")
    if observation.foul_zone_entry_delta >= config.foul_zone_entry_delta:
        reason_codes.append("soccer_set_piece_xg_swing_foul_zone_pressure")
    if observation.primary_taker_change_signal >= config.primary_taker_change_signal:
        reason_codes.append("soccer_set_piece_xg_swing_primary_taker_change")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_reason_codes(
    signal_reason_codes: tuple[str, ...],
    xg_swing_status: str,
) -> tuple[str, ...]:
    reason_codes = list(signal_reason_codes)
    if xg_swing_status == "blocked":
        reason_codes.append("soccer_set_piece_xg_swing_blocked")
    elif xg_swing_status == "watch":
        reason_codes.append("soccer_set_piece_xg_swing_watch")
    else:
        reason_codes.append("soccer_set_piece_xg_swing_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _xg_swing_status(
    signal_count: Decimal,
    *,
    config: SoccerSetPieceXgSwingDigestConfig,
) -> str:
    if signal_count >= config.blocked_xg_swing_signal_count:
        return "blocked"
    if signal_count >= config.watch_xg_swing_signal_count:
        return "watch"
    return "pass"


def _digest_status(rows: tuple[SoccerSetPieceXgSwingDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.xg_swing_status == "blocked" for row in rows):
        return "blocked"
    if any(row.xg_swing_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_soccer_set_piece_xg_swing_screening"
    if status == "watch":
        return "monitor_report_only_soccer_set_piece_xg_swing_screening"
    return "block_report_only_soccer_set_piece_xg_swing_screening"


def _report_reason_codes(
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("soccer_set_piece_xg_swing_digest_empty",)
    reason_codes: list[str] = []
    if any(row.xg_swing_status == "blocked" for row in rows):
        reason_codes.append("soccer_set_piece_xg_swing_blocked_present")
    if not any(row.xg_swing_status == "blocked" for row in rows) and any(
        row.xg_swing_status == "watch" for row in rows
    ):
        reason_codes.append("soccer_set_piece_xg_swing_watch_present")
    if _reason_count(rows, "soccer_set_piece_xg_swing_set_piece_xg_delta") > ZERO:
        reason_codes.append("soccer_set_piece_xg_swing_delta_present")
    if _reason_count(rows, "soccer_set_piece_xg_swing_high_set_piece_share") > ZERO:
        reason_codes.append("soccer_set_piece_xg_swing_share_present")
    if _reason_count(rows, "soccer_set_piece_xg_swing_corner_pressure_delta") > ZERO:
        reason_codes.append("soccer_set_piece_xg_swing_corner_pressure_present")
    if _reason_count(rows, "soccer_set_piece_xg_swing_aerial_mismatch") > ZERO:
        reason_codes.append("soccer_set_piece_xg_swing_aerial_mismatch_present")
    if _reason_count(rows, "soccer_set_piece_xg_swing_foul_zone_pressure") > ZERO:
        reason_codes.append("soccer_set_piece_xg_swing_foul_zone_present")
    if _reason_count(rows, "soccer_set_piece_xg_swing_primary_taker_change") > ZERO:
        reason_codes.append("soccer_set_piece_xg_swing_taker_change_present")
    if not reason_codes:
        reason_codes.append("soccer_set_piece_xg_swing_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...],
) -> tuple[SoccerSetPieceXgSwingReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("soccer_set_piece_xg_swing_digest_empty",):
        return (
            SoccerSetPieceXgSwingReasonCodeCount(
                reason_code="soccer_set_piece_xg_swing_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        SoccerSetPieceXgSwingReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "soccer_set_piece_xg_swing_blocked_present": (
            "soccer_set_piece_xg_swing_blocked"
        ),
        "soccer_set_piece_xg_swing_watch_present": "soccer_set_piece_xg_swing_watch",
        "soccer_set_piece_xg_swing_delta_present": (
            "soccer_set_piece_xg_swing_set_piece_xg_delta"
        ),
        "soccer_set_piece_xg_swing_share_present": (
            "soccer_set_piece_xg_swing_high_set_piece_share"
        ),
        "soccer_set_piece_xg_swing_corner_pressure_present": (
            "soccer_set_piece_xg_swing_corner_pressure_delta"
        ),
        "soccer_set_piece_xg_swing_aerial_mismatch_present": (
            "soccer_set_piece_xg_swing_aerial_mismatch"
        ),
        "soccer_set_piece_xg_swing_foul_zone_present": (
            "soccer_set_piece_xg_swing_foul_zone_pressure"
        ),
        "soccer_set_piece_xg_swing_taker_change_present": (
            "soccer_set_piece_xg_swing_primary_taker_change"
        ),
        "soccer_set_piece_xg_swing_digest_clear": (
            "soccer_set_piece_xg_swing_clear"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _validate_row(row: SoccerSetPieceXgSwingDigestRow) -> None:
    expected_delta = _quantize_decimal(
        row.projected_set_piece_xg - row.baseline_set_piece_xg,
    )
    if row.set_piece_xg_delta != expected_delta:
        raise ValueError("set_piece_xg_delta must match projected and baseline xg")
    if row.absolute_set_piece_xg_delta != abs(row.set_piece_xg_delta):
        raise ValueError("absolute_set_piece_xg_delta must match set_piece_xg_delta")
    if row.absolute_corner_pressure_delta != abs(row.corner_pressure_delta):
        raise ValueError("absolute_corner_pressure_delta must match corner_pressure_delta")
    if row.absolute_foul_zone_entry_delta != abs(row.foul_zone_entry_delta):
        raise ValueError("absolute_foul_zone_entry_delta must match foul_zone_entry_delta")
    if row.xg_swing_status == "pass":
        if "soccer_set_piece_xg_swing_clear" not in row.reason_codes:
            raise ValueError("reason_codes must match xg_swing_status")
        if (
            "soccer_set_piece_xg_swing_watch" in row.reason_codes
            or "soccer_set_piece_xg_swing_blocked" in row.reason_codes
        ):
            raise ValueError("reason_codes must match xg_swing_status")
    if row.xg_swing_status == "watch":
        if "soccer_set_piece_xg_swing_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match xg_swing_status")
        if (
            "soccer_set_piece_xg_swing_clear" in row.reason_codes
            or "soccer_set_piece_xg_swing_blocked" in row.reason_codes
        ):
            raise ValueError("reason_codes must match xg_swing_status")
    if row.xg_swing_status == "blocked":
        if "soccer_set_piece_xg_swing_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match xg_swing_status")
        if (
            "soccer_set_piece_xg_swing_clear" in row.reason_codes
            or "soccer_set_piece_xg_swing_watch" in row.reason_codes
        ):
            raise ValueError("reason_codes must match xg_swing_status")
    signal_count = _count_decimal(
        sum(
            1
            for reason_code in ROW_REASON_CODES[:6]
            if reason_code in row.reason_codes
        ),
    )
    if row.xg_swing_signal_count != signal_count:
        raise ValueError("xg_swing_signal_count must match reason_codes")
    if row.xg_swing_pressure_score != _ratio(
        row.xg_swing_signal_count,
        SIGNAL_DENOMINATOR,
    ):
        raise ValueError("xg_swing_pressure_score must match xg_swing_signal_count")


def _validate_report(report: SoccerSetPieceXgSwingDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    reason_count_pairs = (
        ("material_xg_delta_count", "soccer_set_piece_xg_swing_set_piece_xg_delta"),
        (
            "high_set_piece_share_count",
            "soccer_set_piece_xg_swing_high_set_piece_share",
        ),
        (
            "corner_pressure_count",
            "soccer_set_piece_xg_swing_corner_pressure_delta",
        ),
        ("aerial_mismatch_count", "soccer_set_piece_xg_swing_aerial_mismatch"),
        ("foul_zone_pressure_count", "soccer_set_piece_xg_swing_foul_zone_pressure"),
        (
            "primary_taker_change_count",
            "soccer_set_piece_xg_swing_primary_taker_change",
        ),
    )
    for field_name, reason_code in reason_count_pairs:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_xg_swing_pressure_score != _max_row_decimal(
        report.rows,
        "xg_swing_pressure_score",
    ):
        raise ValueError("max_xg_swing_pressure_score must match rows")
    if report.average_xg_swing_pressure_score != _ratio(
        _sum_decimal(row.xg_swing_pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_xg_swing_pressure_score must match rows")
    if report.max_absolute_set_piece_xg_delta != _max_row_decimal(
        report.rows,
        "absolute_set_piece_xg_delta",
    ):
        raise ValueError("max_absolute_set_piece_xg_delta must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[SoccerSetPieceXgSwingObservation],
) -> tuple[SoccerSetPieceXgSwingObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain SoccerSetPieceXgSwingObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not SoccerSetPieceXgSwingObservation:
            raise ValueError("observations must contain SoccerSetPieceXgSwingObservation")
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[SoccerSetPieceXgSwingDigestRow],
) -> tuple[SoccerSetPieceXgSwingDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain SoccerSetPieceXgSwingDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not SoccerSetPieceXgSwingDigestRow:
            raise ValueError("rows must contain SoccerSetPieceXgSwingDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[SoccerSetPieceXgSwingReasonCodeCount],
) -> tuple[SoccerSetPieceXgSwingReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not SoccerSetPieceXgSwingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain SoccerSetPieceXgSwingReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized: list[str] = []
    for value in values:
        _require_public_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: SoccerSetPieceXgSwingDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.xg_swing_status],
        -row.xg_swing_pressure_score,
        -row.absolute_set_piece_xg_delta,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.xg_swing_status == status))


def _reason_count(
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[SoccerSetPieceXgSwingDigestRow, ...],
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


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
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
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be safe public text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


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
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
