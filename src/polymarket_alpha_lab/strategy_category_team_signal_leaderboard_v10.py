"""Paper-only category/team signal quality leaderboard reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


__all__ = (
    "StrategyCategoryTeamSignalInput",
    "StrategyCategoryTeamSignalLeaderboardConfig",
    "StrategyCategoryTeamSignalLeaderboardReport",
    "StrategyCategoryTeamSignalLeaderboardRow",
    "build_strategy_category_team_signal_leaderboard",
    "strategy_category_team_signal_leaderboard_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-category-team-signal-leaderboard-v10"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HIT_RATE_WEIGHT = Decimal("0.700000")
SOURCE_QUALITY_WEIGHT = Decimal("0.150000")
FRESHNESS_WEIGHT = Decimal("0.150000")
CALIBRATION_ERROR_PENALTY_WEIGHT = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64)
ELIGIBILITY_STATUSES = (
    "eligible",
    "insufficient_sample",
    "insufficient_recent_resolution",
    "low_quality",
)
ROTATION_SIGNALS = ("leader", "runner_up", "watch")
ROTATION_RECOMMENDATIONS = (
    "rotate_to_top_team",
    "hold_current_leaderboard",
    "watch",
)
EMPTY_REASON_CODE = "category_team_signal_leaderboard_empty"
LEADER_REASON_CODE = "category_team_signal_leader_identified"
ROTATION_REASON_CODE = "category_team_signal_rotation_recommended"
HOLD_REASON_CODE = "category_team_signal_rotation_hold"
WATCH_REASON_CODE = "category_team_signal_watch"
RANK_1_REASON_CODE = "category_team_signal_rank_1"
RUNNER_UP_REASON_CODE = "category_team_signal_runner_up"
QUALITY_PASS_REASON_CODE = "category_team_signal_quality_pass"
QUALITY_WATCH_REASON_CODE = "category_team_signal_quality_watch"
QUALITY_LOW_REASON_CODE = "category_team_signal_quality_low"
SAMPLE_SUFFICIENT_REASON_CODE = "category_team_signal_sample_sufficient"
INSUFFICIENT_SAMPLE_REASON_CODE = "category_team_signal_insufficient_sample"
RECENT_SUFFICIENT_REASON_CODE = "category_team_signal_recent_resolution_sufficient"
INSUFFICIENT_RECENT_REASON_CODE = (
    "category_team_signal_insufficient_recent_resolution"
)
ROW_REASON_PRIORITY = (
    "team_signal_input",
    RANK_1_REASON_CODE,
    RUNNER_UP_REASON_CODE,
    WATCH_REASON_CODE,
    QUALITY_PASS_REASON_CODE,
    QUALITY_WATCH_REASON_CODE,
    QUALITY_LOW_REASON_CODE,
    SAMPLE_SUFFICIENT_REASON_CODE,
    INSUFFICIENT_SAMPLE_REASON_CODE,
    RECENT_SUFFICIENT_REASON_CODE,
    INSUFFICIENT_RECENT_REASON_CODE,
)
REPORT_REASON_PRIORITY = (
    LEADER_REASON_CODE,
    ROTATION_REASON_CODE,
    HOLD_REASON_CODE,
    WATCH_REASON_CODE,
    QUALITY_PASS_REASON_CODE,
    QUALITY_WATCH_REASON_CODE,
    QUALITY_LOW_REASON_CODE,
    INSUFFICIENT_SAMPLE_REASON_CODE,
    INSUFFICIENT_RECENT_REASON_CODE,
    EMPTY_REASON_CODE,
)
ROW_REASON_SORT_PRIORITY = {
    reason_code: index for index, reason_code in enumerate(ROW_REASON_PRIORITY)
}
REPORT_REASON_SORT_PRIORITY = {
    reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)
}
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "signed",
    "signing",
    "signature",
    "exchange_mutation",
)


@dataclass(frozen=True)
class StrategyCategoryTeamSignalLeaderboardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_sample_size: Decimal = Decimal("50")
    min_recent_resolved_count: Decimal = Decimal("5")
    min_signal_quality_score: Decimal = Decimal("0.650000")
    watch_signal_quality_score: Decimal = Decimal("0.550000")
    minimum_top_team_margin: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_canonical_string("config_version", self.config_version)
        for field_name in ("min_sample_size", "min_recent_resolved_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_signal_quality_score",
            "watch_signal_quality_score",
            "minimum_top_team_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_signal_quality_score > self.min_signal_quality_score:
            raise ValueError(
                "watch_signal_quality_score must not exceed min_signal_quality_score",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryTeamSignalInput:
    category: str
    team_id: str
    hit_rate: Decimal
    calibration_error: Decimal
    source_quality_score: Decimal
    freshness_score: Decimal
    sample_size: Decimal
    recent_resolved_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_canonical_string("category", self.category)
        _require_public_canonical_string("team_id", self.team_id)
        for field_name in (
            "hit_rate",
            "calibration_error",
            "source_quality_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("sample_size", "recent_resolved_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                require_nonempty=True,
                priority=ROW_REASON_SORT_PRIORITY,
            ),
        )
        require_paper_only_flags("team signal", self)


@dataclass(frozen=True)
class StrategyCategoryTeamSignalLeaderboardRow:
    rank: Decimal
    category: str
    team_id: str
    hit_rate: Decimal
    calibration_error: Decimal
    source_quality_score: Decimal
    freshness_score: Decimal
    sample_size: Decimal
    recent_resolved_count: Decimal
    signal_quality_score: Decimal
    eligibility_status: str
    rotation_signal: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_count_decimal("rank", self.rank))
        _require_public_canonical_string("category", self.category)
        _require_public_canonical_string("team_id", self.team_id)
        for field_name in (
            "hit_rate",
            "calibration_error",
            "source_quality_score",
            "freshness_score",
            "signal_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("sample_size", "recent_resolved_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "eligibility_status",
            self.eligibility_status,
            ELIGIBILITY_STATUSES,
        )
        _require_member("rotation_signal", self.rotation_signal, ROTATION_SIGNALS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                require_nonempty=True,
                priority=ROW_REASON_SORT_PRIORITY,
            ),
        )
        _validate_row(self)
        require_paper_only_flags("leaderboard row", self)


@dataclass(frozen=True)
class StrategyCategoryTeamSignalLeaderboardReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    category_count: Decimal
    eligible_team_count: Decimal
    top_team_id: str | None
    top_category: str | None
    rotation_recommendation: str
    reason_codes: tuple[str, ...]
    leaderboard_rows: tuple[StrategyCategoryTeamSignalLeaderboardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_canonical_string("config_version", self.config_version)
        for field_name in ("team_count", "category_count", "eligible_team_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_optional_public_canonical_string("top_team_id", self.top_team_id)
        _require_optional_public_canonical_string("top_category", self.top_category)
        _require_member(
            "rotation_recommendation",
            self.rotation_recommendation,
            ROTATION_RECOMMENDATIONS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                require_nonempty=True,
                priority=REPORT_REASON_SORT_PRIORITY,
            ),
        )
        object.__setattr__(
            self,
            "leaderboard_rows",
            _normalize_rows(self.leaderboard_rows),
        )
        _validate_report(self)
        _reject_unsafe_surface_fields("category team signal leaderboard report", self)
        require_paper_only_flags("leaderboard report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_category_team_signal_leaderboard_payload(self)


def build_strategy_category_team_signal_leaderboard(
    signals: Iterable[object],
    *,
    config: StrategyCategoryTeamSignalLeaderboardConfig,
    generated_at: datetime,
) -> StrategyCategoryTeamSignalLeaderboardReport:
    if type(config) is not StrategyCategoryTeamSignalLeaderboardConfig:
        raise ValueError(
            "config must be a StrategyCategoryTeamSignalLeaderboardConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("config", config)
    source_signals = _normalize_signal_inputs(signals)
    rows_without_rank = tuple(
        sorted(
            (_row_from_signal(signal, config=config) for signal in source_signals),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        _ranked_row_from_unranked(row, rank=index + 1)
        for index, row in enumerate(rows_without_rank)
    )
    recommendation = _rotation_recommendation(rows, config)
    return StrategyCategoryTeamSignalLeaderboardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        team_count=_count_decimal(len(rows)),
        category_count=_count_decimal(len({row.category for row in rows})),
        eligible_team_count=_count_decimal(
            sum(1 for row in rows if row.eligibility_status == "eligible"),
        ),
        top_team_id=_top_row(rows).team_id if _top_row(rows) is not None else None,
        top_category=_top_row(rows).category if _top_row(rows) is not None else None,
        rotation_recommendation=recommendation,
        reason_codes=_report_reason_codes(rows, recommendation),
        leaderboard_rows=rows,
    )


def strategy_category_team_signal_leaderboard_payload(
    report: StrategyCategoryTeamSignalLeaderboardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryTeamSignalLeaderboardReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_surface_fields("category team signal leaderboard report", report)
        return _report_payload(report)
    if type(report) is dict:
        _reject_unsafe_surface_fields("category team signal leaderboard payload", report)
        ready = json_ready_no_floats(report)
        _reject_unsafe_surface_fields("category team signal leaderboard payload", ready)
        require_paper_only_flags("payload", _DictFlags(ready))
        return ready
    raise ValueError("report must be a StrategyCategoryTeamSignalLeaderboardReport")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


@dataclass(frozen=True)
class _UnrankedRow:
    category: str
    team_id: str
    hit_rate: Decimal
    calibration_error: Decimal
    source_quality_score: Decimal
    freshness_score: Decimal
    sample_size: Decimal
    recent_resolved_count: Decimal
    signal_quality_score: Decimal
    eligibility_status: str
    rotation_signal: str
    reason_codes: tuple[str, ...]


def _report_payload(report: StrategyCategoryTeamSignalLeaderboardReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "team_count": _count_payload(report.team_count),
        "category_count": _count_payload(report.category_count),
        "eligible_team_count": _count_payload(report.eligible_team_count),
        "top_team_id": report.top_team_id,
        "top_category": report.top_category,
        "rotation_recommendation": report.rotation_recommendation,
        "reason_codes": list(report.reason_codes),
        "leaderboard_rows": [_row_payload(row) for row in report.leaderboard_rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: StrategyCategoryTeamSignalLeaderboardRow) -> dict[str, Any]:
    return {
        "rank": _count_payload(row.rank),
        "category": row.category,
        "team_id": row.team_id,
        "hit_rate": _decimal_payload(row.hit_rate),
        "calibration_error": _decimal_payload(row.calibration_error),
        "source_quality_score": _decimal_payload(row.source_quality_score),
        "freshness_score": _decimal_payload(row.freshness_score),
        "sample_size": _count_payload(row.sample_size),
        "recent_resolved_count": _count_payload(row.recent_resolved_count),
        "signal_quality_score": _decimal_payload(row.signal_quality_score),
        "eligibility_status": row.eligibility_status,
        "rotation_signal": row.rotation_signal,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_from_signal(
    signal: StrategyCategoryTeamSignalInput,
    *,
    config: StrategyCategoryTeamSignalLeaderboardConfig,
) -> _UnrankedRow:
    signal_quality_score = _signal_quality_score(signal)
    eligibility_status = _eligibility_status(signal, signal_quality_score, config)
    return _UnrankedRow(
        category=signal.category,
        team_id=signal.team_id,
        hit_rate=signal.hit_rate,
        calibration_error=signal.calibration_error,
        source_quality_score=signal.source_quality_score,
        freshness_score=signal.freshness_score,
        sample_size=signal.sample_size,
        recent_resolved_count=signal.recent_resolved_count,
        signal_quality_score=signal_quality_score,
        eligibility_status=eligibility_status,
        rotation_signal="watch",
        reason_codes=_row_reason_codes(
            signal,
            signal_quality_score=signal_quality_score,
            eligibility_status=eligibility_status,
            config=config,
        ),
    )


def _ranked_row_from_unranked(
    row: _UnrankedRow,
    *,
    rank: int,
) -> StrategyCategoryTeamSignalLeaderboardRow:
    rotation_signal = _rotation_signal_for_rank(row, rank)
    reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code
        not in {
            RANK_1_REASON_CODE,
            RUNNER_UP_REASON_CODE,
            WATCH_REASON_CODE,
        }
    )
    if rotation_signal == "leader":
        reason_codes = (*reason_codes, RANK_1_REASON_CODE)
    elif rotation_signal == "runner_up":
        reason_codes = (*reason_codes, RUNNER_UP_REASON_CODE)
    else:
        reason_codes = (*reason_codes, WATCH_REASON_CODE)
    return StrategyCategoryTeamSignalLeaderboardRow(
        rank=_count_decimal(rank),
        category=row.category,
        team_id=row.team_id,
        hit_rate=row.hit_rate,
        calibration_error=row.calibration_error,
        source_quality_score=row.source_quality_score,
        freshness_score=row.freshness_score,
        sample_size=row.sample_size,
        recent_resolved_count=row.recent_resolved_count,
        signal_quality_score=row.signal_quality_score,
        eligibility_status=row.eligibility_status,
        rotation_signal=rotation_signal,
        reason_codes=_normalize_reason_codes(
            reason_codes,
            require_nonempty=True,
            priority=ROW_REASON_SORT_PRIORITY,
        ),
    )


def _signal_quality_score(signal: StrategyCategoryTeamSignalInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quality = (
            signal.hit_rate * HIT_RATE_WEIGHT
            + signal.source_quality_score * SOURCE_QUALITY_WEIGHT
            + signal.freshness_score * FRESHNESS_WEIGHT
            - signal.calibration_error * CALIBRATION_ERROR_PENALTY_WEIGHT
        )
    if quality < ZERO:
        quality = ZERO
    if quality > ONE:
        quality = ONE
    return _normalize_probability_decimal("signal_quality_score", quality)


def _eligibility_status(
    signal: StrategyCategoryTeamSignalInput,
    signal_quality_score: Decimal,
    config: StrategyCategoryTeamSignalLeaderboardConfig,
) -> str:
    if signal.sample_size < config.min_sample_size:
        return "insufficient_sample"
    if signal.recent_resolved_count < config.min_recent_resolved_count:
        return "insufficient_recent_resolution"
    if signal_quality_score < config.watch_signal_quality_score:
        return "low_quality"
    return "eligible"


def _row_reason_codes(
    signal: StrategyCategoryTeamSignalInput,
    *,
    signal_quality_score: Decimal,
    eligibility_status: str,
    config: StrategyCategoryTeamSignalLeaderboardConfig,
) -> tuple[str, ...]:
    reason_codes = [*signal.reason_codes]
    if signal_quality_score >= config.min_signal_quality_score:
        reason_codes.append(QUALITY_PASS_REASON_CODE)
    elif signal_quality_score >= config.watch_signal_quality_score:
        reason_codes.append(QUALITY_WATCH_REASON_CODE)
    else:
        reason_codes.append(QUALITY_LOW_REASON_CODE)

    if eligibility_status == "insufficient_sample":
        reason_codes.append(INSUFFICIENT_SAMPLE_REASON_CODE)
    else:
        reason_codes.append(SAMPLE_SUFFICIENT_REASON_CODE)

    if signal.recent_resolved_count < config.min_recent_resolved_count:
        reason_codes.append(INSUFFICIENT_RECENT_REASON_CODE)
    else:
        reason_codes.append(RECENT_SUFFICIENT_REASON_CODE)

    return _normalize_reason_codes(
        tuple(reason_codes),
        require_nonempty=True,
        priority=ROW_REASON_SORT_PRIORITY,
    )


def _rotation_signal_for_rank(row: _UnrankedRow, rank: int) -> str:
    if row.eligibility_status != "eligible":
        return "watch"
    if rank == 1:
        return "leader"
    return "runner_up"


def _rotation_recommendation(
    rows: tuple[StrategyCategoryTeamSignalLeaderboardRow, ...],
    config: StrategyCategoryTeamSignalLeaderboardConfig,
) -> str:
    if not rows:
        return "watch"
    top = _top_row(rows)
    if top is None:
        return "watch"
    runner_up = _runner_up_row(rows)
    if runner_up is None:
        return "rotate_to_top_team"
    if (
        _subtract_decimal(top.signal_quality_score, runner_up.signal_quality_score)
        >= config.minimum_top_team_margin
    ):
        return "rotate_to_top_team"
    return "hold_current_leaderboard"


def _top_row(
    rows: tuple[StrategyCategoryTeamSignalLeaderboardRow, ...],
) -> StrategyCategoryTeamSignalLeaderboardRow | None:
    for row in rows:
        if row.eligibility_status == "eligible":
            return row
    return None


def _runner_up_row(
    rows: tuple[StrategyCategoryTeamSignalLeaderboardRow, ...],
) -> StrategyCategoryTeamSignalLeaderboardRow | None:
    eligible_seen = 0
    for row in rows:
        if row.eligibility_status == "eligible":
            eligible_seen += 1
        if eligible_seen == 2:
            return row
    return None


def _normalize_signal_inputs(
    signals: Iterable[object],
) -> tuple[StrategyCategoryTeamSignalInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not StrategyCategoryTeamSignalInput:
            raise ValueError("signal must be a StrategyCategoryTeamSignalInput")
        require_paper_only_flags("team signal", signal)
        key = (signal.category, signal.team_id)
        if key in seen:
            raise ValueError("duplicate category/team_id")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyCategoryTeamSignalLeaderboardRow, ...],
) -> tuple[StrategyCategoryTeamSignalLeaderboardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("leaderboard_rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyCategoryTeamSignalLeaderboardRow:
            raise ValueError("leaderboard row must be a StrategyCategoryTeamSignalLeaderboardRow")
        require_paper_only_flags("leaderboard row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("leaderboard_rows must be deterministically sorted")
    return rows


def _unranked_row_sort_key(row: _UnrankedRow) -> tuple[int, Decimal, str, str]:
    return (
        0 if row.eligibility_status == "eligible" else 1,
        -row.signal_quality_score,
        row.category,
        row.team_id,
    )


def _row_sort_key(
    row: StrategyCategoryTeamSignalLeaderboardRow,
) -> tuple[Decimal, int, Decimal, str, str]:
    return (
        row.rank,
        0 if row.eligibility_status == "eligible" else 1,
        -row.signal_quality_score,
        row.category,
        row.team_id,
    )


def _report_reason_codes(
    rows: tuple[StrategyCategoryTeamSignalLeaderboardRow, ...],
    recommendation: str,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    row_only_reason_codes = {
        RANK_1_REASON_CODE,
        RUNNER_UP_REASON_CODE,
        WATCH_REASON_CODE,
    }
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code not in row_only_reason_codes
    }
    if _top_row(rows) is not None:
        found.add(LEADER_REASON_CODE)
    if recommendation == "rotate_to_top_team":
        found.add(ROTATION_REASON_CODE)
    elif recommendation == "hold_current_leaderboard":
        found.add(HOLD_REASON_CODE)
    else:
        found.add(WATCH_REASON_CODE)
    return tuple(
        reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in found
    )


def _validate_row(row: StrategyCategoryTeamSignalLeaderboardRow) -> None:
    if row.rank <= ZERO:
        raise ValueError("rank must be positive")
    expected_quality = _signal_quality_score(
        StrategyCategoryTeamSignalInput(
            category=row.category,
            team_id=row.team_id,
            hit_rate=row.hit_rate,
            calibration_error=row.calibration_error,
            source_quality_score=row.source_quality_score,
            freshness_score=row.freshness_score,
            sample_size=row.sample_size,
            recent_resolved_count=row.recent_resolved_count,
            reason_codes=("team_signal_input",),
        ),
    )
    if row.signal_quality_score != expected_quality:
        raise ValueError("signal_quality_score must match input metrics")
    if row.eligibility_status != "eligible" and row.rotation_signal != "watch":
        raise ValueError("rotation_signal must be watch unless row is eligible")


def _validate_report(report: StrategyCategoryTeamSignalLeaderboardReport) -> None:
    rows = report.leaderboard_rows
    if report.team_count != _count_decimal(len(rows)):
        raise ValueError("team_count must match leaderboard_rows")
    if report.category_count != _count_decimal(len({row.category for row in rows})):
        raise ValueError("category_count must match leaderboard_rows")
    if report.eligible_team_count != _count_decimal(
        sum(1 for row in rows if row.eligibility_status == "eligible"),
    ):
        raise ValueError("eligible_team_count must match leaderboard_rows")
    top = _top_row(rows)
    if report.top_team_id != (top.team_id if top is not None else None):
        raise ValueError("top_team_id must match leaderboard_rows")
    if report.top_category != (top.category if top is not None else None):
        raise ValueError("top_category must match leaderboard_rows")
    expected_recommendation = _rotation_recommendation(
        rows,
        StrategyCategoryTeamSignalLeaderboardConfig(
            config_version=report.config_version,
            minimum_top_team_margin=Decimal("0.050000"),
        ),
    )
    if report.rotation_recommendation not in ROTATION_RECOMMENDATIONS:
        raise ValueError("rotation_recommendation must be known")
    if report.reason_codes != _report_reason_codes(rows, report.rotation_recommendation):
        raise ValueError("reason_codes must match leaderboard_rows")
    if not rows and expected_recommendation != report.rotation_recommendation:
        raise ValueError("rotation_recommendation must match empty leaderboard")


def _reject_unsafe_surface_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_keys(json_ready_no_floats(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_canonical_string(field_name: str, value: Any) -> None:
    _require_canonical_string(field_name, value)


def _require_optional_public_canonical_string(
    field_name: str,
    value: str | None,
) -> None:
    if value is None:
        return
    _require_public_canonical_string(field_name, value)


def _require_member(field_name: str, value: Any, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
    priority: dict[str, int],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if not all(char.islower() or char.isdigit() or char == "_" for char in reason_code):
            raise ValueError("reason_code must be lowercase snake case")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=lambda item: (priority.get(item, len(priority)), item)))


def _validate_report_only_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))
