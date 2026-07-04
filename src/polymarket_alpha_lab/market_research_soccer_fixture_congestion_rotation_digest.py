"""Pure Phase 1 soccer fixture congestion rotation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_SOCCER_FIXTURE_CONGESTION_ROTATION_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-fixture-congestion-rotation-digest-v0"
)
INPUT_REASON_CODES = (
    "soccer_fixture_congestion_pressure_high",
    "soccer_fixture_congestion_pressure_watch",
    "soccer_fixture_congestion_pressure_inline",
)
ROW_REASON_CODES = (
    "soccer_fixture_congestion_high_pressure",
    "soccer_fixture_congestion_watch_pressure",
    "soccer_fixture_congestion_inline_pressure",
    "soccer_fixture_congestion_short_rest",
    "soccer_fixture_congestion_travel_burden",
    "soccer_fixture_congestion_rotation_likely",
    "soccer_fixture_congestion_lineup_uncertain",
)
REPORT_REASON_CODES = (
    "soccer_fixture_congestion_high_pressure_present",
    "soccer_fixture_congestion_watch_pressure_present",
    "soccer_fixture_congestion_short_rest_present",
    "soccer_fixture_congestion_travel_burden_present",
    "soccer_fixture_congestion_rotation_likelihood_present",
    "soccer_fixture_congestion_lineup_uncertainty_present",
    "soccer_fixture_congestion_digest_clear",
    "soccer_fixture_congestion_digest_empty",
)
REASON_COUNT_CODES = REPORT_REASON_CODES
PRESSURE_BUCKETS = ("high_pressure", "watch_pressure", "inline_pressure")
PRESSURE_STATUSES = ("blocked", "watch", "pass")

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_CONGESTION_SCORE = Decimal("0.500000")
HIGH_CONGESTION_SCORE = Decimal("0.700000")
MIN_REST_HOURS = Decimal("72.000000")
HIGH_TRAVEL_DISTANCE_KM = Decimal("1200.000000")
CONGESTED_MATCH_COUNT = Decimal("5.000000")
LINEUP_UNCERTAINTY_THRESHOLD = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_SOCCER_FIXTURE_CONGESTION_ROTATION_DIGEST_CONFIG_VERSION",
    "SoccerFixtureCongestionRotationDigestConfig",
    "SoccerFixtureCongestionRotationSignal",
    "SoccerFixtureCongestionRotationDigestRow",
    "SoccerFixtureCongestionRotationReasonCodeCount",
    "SoccerFixtureCongestionRotationDigestReport",
    "build_market_research_soccer_fixture_congestion_rotation_digest",
    "market_research_soccer_fixture_congestion_rotation_digest_payload",
)


@dataclass(frozen=True)
class SoccerFixtureCongestionRotationDigestConfig:
    config_version: str = DEFAULT_SOCCER_FIXTURE_CONGESTION_ROTATION_DIGEST_CONFIG_VERSION
    watch_congestion_score: Decimal = WATCH_CONGESTION_SCORE
    high_congestion_score: Decimal = HIGH_CONGESTION_SCORE
    min_rest_hours: Decimal = MIN_REST_HOURS
    high_travel_distance_km: Decimal = HIGH_TRAVEL_DISTANCE_KM
    congested_match_count: Decimal = CONGESTED_MATCH_COUNT
    lineup_uncertainty_threshold: Decimal = LINEUP_UNCERTAINTY_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerFixtureCongestionRotationDigestConfig:
            raise TypeError(
                "SoccerFixtureCongestionRotationDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerFixtureCongestionRotationDigestConfig:
            raise ValueError(
                "config must be exactly SoccerFixtureCongestionRotationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_SOCCER_FIXTURE_CONGESTION_ROTATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_congestion_score",
            "high_congestion_score",
            "lineup_uncertainty_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_rest_hours",
            "high_travel_distance_km",
            "congested_match_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_congestion_score < self.watch_congestion_score:
            raise ValueError("high_congestion_score must be at least watch threshold")
        for field_name, expected in (
            ("watch_congestion_score", WATCH_CONGESTION_SCORE),
            ("high_congestion_score", HIGH_CONGESTION_SCORE),
            ("min_rest_hours", MIN_REST_HOURS),
            ("high_travel_distance_km", HIGH_TRAVEL_DISTANCE_KM),
            ("congested_match_count", CONGESTED_MATCH_COUNT),
            ("lineup_uncertainty_threshold", LINEUP_UNCERTAINTY_THRESHOLD),
        ):
            if getattr(self, field_name) != expected:
                raise ValueError(f"{field_name} must use supported default threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SoccerFixtureCongestionRotationSignal:
    signal_id: str
    match_id: str
    team_id: str
    opponent_id: str
    market_slug: str
    kickoff_at: datetime
    observed_at: datetime
    rest_hours: Decimal
    travel_distance_km: Decimal
    matches_last_14_days: Decimal
    rotation_likelihood: Decimal
    lineup_uncertainty: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerFixtureCongestionRotationSignal:
            raise TypeError(
                "SoccerFixtureCongestionRotationSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerFixtureCongestionRotationSignal:
            raise ValueError(
                "signal must be exactly SoccerFixtureCongestionRotationSignal",
            )
        for field_name in (
            "signal_id",
            "match_id",
            "team_id",
            "opponent_id",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "kickoff_at", _as_utc("kickoff_at", self.kickoff_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rest_hours",
            "travel_distance_km",
            "matches_last_14_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("rotation_likelihood", "lineup_uncertainty"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_signal(self)
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class SoccerFixtureCongestionRotationDigestRow:
    signal_id: str
    match_id: str
    team_id: str
    opponent_id: str
    market_slug: str
    kickoff_at: datetime
    observed_at: datetime
    rest_hours: Decimal
    travel_distance_km: Decimal
    matches_last_14_days: Decimal
    rotation_likelihood: Decimal
    lineup_uncertainty: Decimal
    congestion_score: Decimal
    pressure_bucket: str
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerFixtureCongestionRotationDigestRow:
            raise TypeError(
                "SoccerFixtureCongestionRotationDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerFixtureCongestionRotationDigestRow:
            raise ValueError(
                "row must be exactly SoccerFixtureCongestionRotationDigestRow",
            )
        for field_name in (
            "signal_id",
            "match_id",
            "team_id",
            "opponent_id",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "kickoff_at", _as_utc("kickoff_at", self.kickoff_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rest_hours",
            "travel_distance_km",
            "matches_last_14_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rotation_likelihood",
            "lineup_uncertainty",
            "congestion_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_member("pressure_bucket", self.pressure_bucket, PRESSURE_BUCKETS)
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SoccerFixtureCongestionRotationReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerFixtureCongestionRotationReasonCodeCount:
            raise TypeError(
                "SoccerFixtureCongestionRotationReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerFixtureCongestionRotationReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "SoccerFixtureCongestionRotationReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_COUNT_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class SoccerFixtureCongestionRotationDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    high_pressure_count: Decimal
    watch_pressure_count: Decimal
    inline_pressure_count: Decimal
    short_rest_count: Decimal
    travel_burden_count: Decimal
    rotation_pressure_count: Decimal
    lineup_uncertainty_count: Decimal
    max_congestion_score: Decimal
    average_rest_hours: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...]
    reason_code_counts: tuple[SoccerFixtureCongestionRotationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerFixtureCongestionRotationDigestReport:
            raise TypeError(
                "SoccerFixtureCongestionRotationDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerFixtureCongestionRotationDigestReport:
            raise ValueError(
                "report must be exactly SoccerFixtureCongestionRotationDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_SOCCER_FIXTURE_CONGESTION_ROTATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "high_pressure_count",
            "watch_pressure_count",
            "inline_pressure_count",
            "short_rest_count",
            "travel_burden_count",
            "rotation_pressure_count",
            "lineup_uncertainty_count",
            "average_rest_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_congestion_score",
            _require_probability("max_congestion_score", self.max_congestion_score),
        )
        _require_member("digest_status", self.digest_status, PRESSURE_STATUSES)
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


def build_market_research_soccer_fixture_congestion_rotation_digest(
    signals: Iterable[SoccerFixtureCongestionRotationSignal],
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
    generated_at: datetime,
) -> SoccerFixtureCongestionRotationDigestReport:
    if type(config) is not SoccerFixtureCongestionRotationDigestConfig:
        raise ValueError(
            "config must be exactly SoccerFixtureCongestionRotationDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_signal(signal, config=config) for signal in normalized_signals),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return SoccerFixtureCongestionRotationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_signals)),
        row_count=row_count,
        high_pressure_count=_bucket_count(rows, "high_pressure"),
        watch_pressure_count=_bucket_count(rows, "watch_pressure"),
        inline_pressure_count=_bucket_count(rows, "inline_pressure"),
        short_rest_count=_reason_count(rows, "soccer_fixture_congestion_short_rest"),
        travel_burden_count=_reason_count(
            rows,
            "soccer_fixture_congestion_travel_burden",
        ),
        rotation_pressure_count=_reason_count(
            rows,
            "soccer_fixture_congestion_rotation_likely",
        ),
        lineup_uncertainty_count=_reason_count(
            rows,
            "soccer_fixture_congestion_lineup_uncertain",
        ),
        max_congestion_score=max((row.congestion_score for row in rows), default=ZERO),
        average_rest_hours=_ratio(
            _sum_decimal(row.rest_hours for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_soccer_fixture_congestion_rotation_digest_payload(
    report: SoccerFixtureCongestionRotationDigestReport,
) -> dict[str, Any]:
    if type(report) is not SoccerFixtureCongestionRotationDigestReport:
        raise ValueError(
            "report must be exactly SoccerFixtureCongestionRotationDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_signal(
    signal: SoccerFixtureCongestionRotationSignal,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> SoccerFixtureCongestionRotationDigestRow:
    congestion_score = _congestion_score(signal, config=config)
    bucket = _pressure_bucket(congestion_score, config=config)
    return SoccerFixtureCongestionRotationDigestRow(
        signal_id=signal.signal_id,
        match_id=signal.match_id,
        team_id=signal.team_id,
        opponent_id=signal.opponent_id,
        market_slug=signal.market_slug,
        kickoff_at=signal.kickoff_at,
        observed_at=signal.observed_at,
        rest_hours=signal.rest_hours,
        travel_distance_km=signal.travel_distance_km,
        matches_last_14_days=signal.matches_last_14_days,
        rotation_likelihood=signal.rotation_likelihood,
        lineup_uncertainty=signal.lineup_uncertainty,
        congestion_score=congestion_score,
        pressure_bucket=bucket,
        pressure_status=_pressure_status(bucket),
        reason_codes=_row_reason_codes(signal, bucket=bucket, config=config),
    )


def _congestion_score(
    value: object,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> Decimal:
    score = max(
        _rest_pressure(value.rest_hours, config=config),  # type: ignore[attr-defined]
        _travel_pressure(value.travel_distance_km, config=config),  # type: ignore[attr-defined]
        _fixture_pressure(value.matches_last_14_days, config=config),  # type: ignore[attr-defined]
        value.rotation_likelihood,  # type: ignore[attr-defined]
        value.lineup_uncertainty,  # type: ignore[attr-defined]
    )
    return _quantize(score)


def _rest_pressure(
    rest_hours: Decimal,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> Decimal:
    if rest_hours >= config.min_rest_hours:
        return ZERO
    return _ratio(config.min_rest_hours - rest_hours, config.min_rest_hours)


def _travel_pressure(
    travel_distance_km: Decimal,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> Decimal:
    return _capped_ratio(travel_distance_km, config.high_travel_distance_km)


def _fixture_pressure(
    matches_last_14_days: Decimal,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> Decimal:
    return _capped_ratio(matches_last_14_days, config.congested_match_count)


def _pressure_bucket(
    congestion_score: Decimal,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> str:
    if congestion_score >= config.high_congestion_score:
        return "high_pressure"
    if congestion_score >= config.watch_congestion_score:
        return "watch_pressure"
    return "inline_pressure"


def _pressure_status(bucket: str) -> str:
    if bucket == "high_pressure":
        return "blocked"
    if bucket == "watch_pressure":
        return "watch"
    return "pass"


def _input_reason_codes(
    value: object,
    *,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> tuple[str, ...]:
    bucket = _pressure_bucket(_congestion_score(value, config=config), config=config)
    if bucket == "high_pressure":
        return ("soccer_fixture_congestion_pressure_high",)
    if bucket == "watch_pressure":
        return ("soccer_fixture_congestion_pressure_watch",)
    return ("soccer_fixture_congestion_pressure_inline",)


def _row_reason_codes(
    value: object,
    *,
    bucket: str,
    config: SoccerFixtureCongestionRotationDigestConfig,
) -> tuple[str, ...]:
    primary = {
        "high_pressure": "soccer_fixture_congestion_high_pressure",
        "watch_pressure": "soccer_fixture_congestion_watch_pressure",
        "inline_pressure": "soccer_fixture_congestion_inline_pressure",
    }[bucket]
    reason_codes = [primary]
    if value.rest_hours < config.min_rest_hours:  # type: ignore[attr-defined]
        reason_codes.append("soccer_fixture_congestion_short_rest")
    if (
        _travel_pressure(value.travel_distance_km, config=config)  # type: ignore[attr-defined]
        >= config.watch_congestion_score
    ):
        reason_codes.append("soccer_fixture_congestion_travel_burden")
    if value.rotation_likelihood >= config.watch_congestion_score:  # type: ignore[attr-defined]
        reason_codes.append("soccer_fixture_congestion_rotation_likely")
    if value.lineup_uncertainty >= config.lineup_uncertainty_threshold:  # type: ignore[attr-defined]
        reason_codes.append("soccer_fixture_congestion_lineup_uncertain")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("soccer_fixture_congestion_digest_empty",)
    reasons: list[str] = []
    if any(row.pressure_bucket == "high_pressure" for row in rows):
        reasons.append("soccer_fixture_congestion_high_pressure_present")
    if any(row.pressure_bucket == "watch_pressure" for row in rows):
        reasons.append("soccer_fixture_congestion_watch_pressure_present")
    if _reason_count(rows, "soccer_fixture_congestion_short_rest") > ZERO:
        reasons.append("soccer_fixture_congestion_short_rest_present")
    if _reason_count(rows, "soccer_fixture_congestion_travel_burden") > ZERO:
        reasons.append("soccer_fixture_congestion_travel_burden_present")
    if _reason_count(rows, "soccer_fixture_congestion_rotation_likely") > ZERO:
        reasons.append("soccer_fixture_congestion_rotation_likelihood_present")
    if _reason_count(rows, "soccer_fixture_congestion_lineup_uncertain") > ZERO:
        reasons.append("soccer_fixture_congestion_lineup_uncertainty_present")
    if not reasons:
        reasons.append("soccer_fixture_congestion_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...],
) -> tuple[SoccerFixtureCongestionRotationReasonCodeCount, ...]:
    if reason_codes == ("soccer_fixture_congestion_digest_empty",):
        return (
            SoccerFixtureCongestionRotationReasonCodeCount(
                reason_code="soccer_fixture_congestion_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(len(rows))
    return tuple(
        SoccerFixtureCongestionRotationReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "soccer_fixture_congestion_high_pressure_present": (
            "soccer_fixture_congestion_high_pressure"
        ),
        "soccer_fixture_congestion_watch_pressure_present": (
            "soccer_fixture_congestion_watch_pressure"
        ),
        "soccer_fixture_congestion_short_rest_present": (
            "soccer_fixture_congestion_short_rest"
        ),
        "soccer_fixture_congestion_travel_burden_present": (
            "soccer_fixture_congestion_travel_burden"
        ),
        "soccer_fixture_congestion_rotation_likelihood_present": (
            "soccer_fixture_congestion_rotation_likely"
        ),
        "soccer_fixture_congestion_lineup_uncertainty_present": (
            "soccer_fixture_congestion_lineup_uncertain"
        ),
        "soccer_fixture_congestion_digest_clear": (
            "soccer_fixture_congestion_inline_pressure"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.pressure_status == "blocked" for row in rows):
        return "blocked"
    if any(row.pressure_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_soccer_fixture_congestion_rotation_digest"
    if status == "watch":
        return "monitor_report_only_market_research_soccer_fixture_congestion_rotation_digest"
    return "block_report_only_market_research_soccer_fixture_congestion_rotation_digest"


def _validate_signal(signal: SoccerFixtureCongestionRotationSignal) -> None:
    # Thresholds are intentionally fixed for this Phase 1 digest config.
    expected_reason_codes = _input_reason_codes(
        signal,
        config=SoccerFixtureCongestionRotationDigestConfig(),
    )
    if signal.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match congestion_score")


def _validate_row(row: SoccerFixtureCongestionRotationDigestRow) -> None:
    # Thresholds are intentionally fixed for this Phase 1 digest config.
    config = SoccerFixtureCongestionRotationDigestConfig()
    congestion_score = _congestion_score(row, config=config)
    if row.congestion_score != congestion_score:
        raise ValueError("congestion_score must match row pressure inputs")
    bucket = _pressure_bucket(congestion_score, config=config)
    if row.pressure_bucket != bucket:
        raise ValueError("pressure_bucket must match congestion_score")
    if row.pressure_status != _pressure_status(row.pressure_bucket):
        raise ValueError("pressure_status must match pressure_bucket")
    if row.reason_codes != _row_reason_codes(row, bucket=row.pressure_bucket, config=config):
        raise ValueError("reason_codes must match row pressure evidence")


def _validate_report(report: SoccerFixtureCongestionRotationDigestReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.high_pressure_count != _bucket_count(report.rows, "high_pressure"):
        raise ValueError("high_pressure_count must match rows")
    if report.watch_pressure_count != _bucket_count(report.rows, "watch_pressure"):
        raise ValueError("watch_pressure_count must match rows")
    if report.inline_pressure_count != _bucket_count(report.rows, "inline_pressure"):
        raise ValueError("inline_pressure_count must match rows")
    if (
        report.high_pressure_count
        + report.watch_pressure_count
        + report.inline_pressure_count
        != report.row_count
    ):
        raise ValueError("pressure counts must match rows")
    if report.short_rest_count != _reason_count(
        report.rows,
        "soccer_fixture_congestion_short_rest",
    ):
        raise ValueError("short_rest_count must match rows")
    if report.travel_burden_count != _reason_count(
        report.rows,
        "soccer_fixture_congestion_travel_burden",
    ):
        raise ValueError("travel_burden_count must match rows")
    if report.rotation_pressure_count != _reason_count(
        report.rows,
        "soccer_fixture_congestion_rotation_likely",
    ):
        raise ValueError("rotation_pressure_count must match rows")
    if report.lineup_uncertainty_count != _reason_count(
        report.rows,
        "soccer_fixture_congestion_lineup_uncertain",
    ):
        raise ValueError("lineup_uncertainty_count must match rows")
    if report.max_congestion_score != max(
        (row.congestion_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_congestion_score must match rows")
    if report.average_rest_hours != _ratio(
        _sum_decimal(row.rest_hours for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_rest_hours must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_signals(
    signals: Iterable[SoccerFixtureCongestionRotationSignal],
) -> tuple[SoccerFixtureCongestionRotationSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain soccer fixture congestion rotation signals")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError(
            "signals must contain soccer fixture congestion rotation signals",
        ) from exc
    seen: set[str] = set()
    for signal in normalized:
        if type(signal) is not SoccerFixtureCongestionRotationSignal:
            raise ValueError("signals must contain SoccerFixtureCongestionRotationSignal")
        _require_hard_flags("signal", signal)
        if signal.signal_id in seen:
            raise ValueError("signals must not contain duplicate signal_id values")
        seen.add(signal.signal_id)
    return normalized


def _normalize_rows(value: object) -> tuple[SoccerFixtureCongestionRotationDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain soccer fixture congestion rotation digest rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain soccer fixture congestion rotation digest rows",
        ) from exc
    for row in rows:
        if type(row) is not SoccerFixtureCongestionRotationDigestRow:
            raise ValueError("rows must contain SoccerFixtureCongestionRotationDigestRow")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.signal_id for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate signal_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[SoccerFixtureCongestionRotationReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not SoccerFixtureCongestionRotationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "SoccerFixtureCongestionRotationReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    if len({item.reason_code for item in counts}) != len(counts):
        raise ValueError("reason_code_counts must be unique")
    if counts != tuple(
        sorted(counts, key=lambda item: REASON_COUNT_CODES.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code)),
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: SoccerFixtureCongestionRotationDigestRow,
) -> tuple[Decimal, Decimal, datetime, str, str]:
    return (
        -STATUS_WEIGHT[row.pressure_status],
        -row.congestion_score,
        row.kickoff_at,
        row.market_slug,
        row.signal_id,
    )


def _bucket_count(
    rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...],
    bucket: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_bucket == bucket))


def _reason_count(
    rows: tuple[SoccerFixtureCongestionRotationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _ratio(numerator, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
