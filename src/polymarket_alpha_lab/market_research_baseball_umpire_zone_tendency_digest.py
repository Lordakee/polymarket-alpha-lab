"""Pure Phase 1 baseball umpire zone tendency digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASEBALL_UMPIRE_ZONE_TENDENCY_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-umpire-zone-tendency-digest-v0"
)

ZONE_TENDENCY_DIRECTIONS = ("wide_zone", "tight_zone", "inline")
RISK_STATUSES = ("pass", "watch", "blocked")
SCREENING_NOTES = (
    "wide_zone_run_suppression",
    "tight_zone_run_inflation",
    "zone_tendency_inline",
)
INPUT_REASON_CODES = (
    "baseball_umpire_zone_tendency_wide_zone_reported",
    "baseball_umpire_zone_tendency_tight_zone_reported",
    "baseball_umpire_zone_tendency_inline_reported",
)
ROW_REASON_CODES = (
    "baseball_umpire_zone_tendency_wide_zone_blocked",
    "baseball_umpire_zone_tendency_tight_zone_blocked",
    "baseball_umpire_zone_tendency_wide_zone_watch",
    "baseball_umpire_zone_tendency_tight_zone_watch",
    "baseball_umpire_zone_tendency_inline",
)
REPORT_REASON_CODES = (
    "baseball_umpire_zone_tendency_digest_clear",
    "baseball_umpire_zone_tendency_blocked_present",
    "baseball_umpire_zone_tendency_watch_present",
    "baseball_umpire_zone_tendency_mixed_tendency_present",
    "baseball_umpire_zone_tendency_wide_zone_present",
    "baseball_umpire_zone_tendency_tight_zone_present",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
WATCH_ABS_ZONE_TENDENCY_SCORE = Decimal("0.025000")
BLOCKED_ABS_ZONE_TENDENCY_SCORE = Decimal("0.060000")
CALLED_STRIKE_RATE_WEIGHT = Decimal("0.550000")
SHADOW_ZONE_STRIKE_RATE_WEIGHT = Decimal("0.250000")
OUTSIDE_ZONE_STRIKE_RATE_WEIGHT = Decimal("0.150000")
WALK_RATE_WEIGHT = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_UMPIRE_ZONE_TENDENCY_DIGEST_CONFIG_VERSION",
    "BaseballUmpireZoneTendencyDigestConfig",
    "BaseballUmpireZoneTendencyObservation",
    "BaseballUmpireZoneTendencyDigestRow",
    "BaseballUmpireZoneTendencyDigestReport",
    "build_market_research_baseball_umpire_zone_tendency_digest",
    "market_research_baseball_umpire_zone_tendency_digest_payload",
)


@dataclass(frozen=True)
class BaseballUmpireZoneTendencyDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_UMPIRE_ZONE_TENDENCY_DIGEST_CONFIG_VERSION
    )
    watch_abs_zone_tendency_score: Decimal = WATCH_ABS_ZONE_TENDENCY_SCORE
    blocked_abs_zone_tendency_score: Decimal = BLOCKED_ABS_ZONE_TENDENCY_SCORE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballUmpireZoneTendencyDigestConfig:
            raise TypeError(
                "BaseballUmpireZoneTendencyDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballUmpireZoneTendencyDigestConfig:
            raise ValueError(
                "config must be exactly BaseballUmpireZoneTendencyDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_UMPIRE_ZONE_TENDENCY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_abs_zone_tendency_score",
            _normalize_positive_ratio(
                "watch_abs_zone_tendency_score",
                self.watch_abs_zone_tendency_score,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_zone_tendency_score",
            _normalize_positive_ratio(
                "blocked_abs_zone_tendency_score",
                self.blocked_abs_zone_tendency_score,
            ),
        )
        if self.blocked_abs_zone_tendency_score < self.watch_abs_zone_tendency_score:
            raise ValueError(
                "blocked_abs_zone_tendency_score must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BaseballUmpireZoneTendencyObservation:
    source_id: str
    market_slug: str
    game_id: str
    plate_umpire_id: str
    called_strike_rate_delta: Decimal
    shadow_zone_strike_rate_delta: Decimal
    outside_zone_strike_rate_delta: Decimal
    walk_rate_delta: Decimal
    source_pitch_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballUmpireZoneTendencyObservation:
            raise TypeError(
                "BaseballUmpireZoneTendencyObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballUmpireZoneTendencyObservation:
            raise ValueError(
                "observation must be exactly BaseballUmpireZoneTendencyObservation",
            )
        for field_name in ("source_id", "market_slug", "game_id", "plate_umpire_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "called_strike_rate_delta",
            "shadow_zone_strike_rate_delta",
            "outside_zone_strike_rate_delta",
            "walk_rate_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_pitch_count",
            _normalize_nonnegative_count("source_pitch_count", self.source_pitch_count),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class BaseballUmpireZoneTendencyDigestRow:
    source_id: str
    market_slug: str
    game_id: str
    plate_umpire_id: str
    called_strike_rate_delta: Decimal
    shadow_zone_strike_rate_delta: Decimal
    outside_zone_strike_rate_delta: Decimal
    walk_rate_delta: Decimal
    zone_tendency_score: Decimal
    abs_zone_tendency_score: Decimal
    screening_priority_score: Decimal
    source_pitch_count: Decimal
    observed_at: datetime
    zone_tendency_direction: str
    risk_status: str
    screening_note: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballUmpireZoneTendencyDigestRow:
            raise TypeError(
                "BaseballUmpireZoneTendencyDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballUmpireZoneTendencyDigestRow:
            raise ValueError("row must be exactly BaseballUmpireZoneTendencyDigestRow")
        for field_name in ("source_id", "market_slug", "game_id", "plate_umpire_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "called_strike_rate_delta",
            "shadow_zone_strike_rate_delta",
            "outside_zone_strike_rate_delta",
            "walk_rate_delta",
            "zone_tendency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "abs_zone_tendency_score",
            _normalize_ratio("abs_zone_tendency_score", self.abs_zone_tendency_score),
        )
        object.__setattr__(
            self,
            "screening_priority_score",
            _normalize_ratio("screening_priority_score", self.screening_priority_score),
        )
        if self.screening_priority_score > ONE:
            raise ValueError("screening_priority_score must not exceed one")
        object.__setattr__(
            self,
            "source_pitch_count",
            _normalize_nonnegative_count("source_pitch_count", self.source_pitch_count),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_member(
            "zone_tendency_direction",
            self.zone_tendency_direction,
            ZONE_TENDENCY_DIRECTIONS,
        )
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        _require_member("screening_note", self.screening_note, SCREENING_NOTES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BaseballUmpireZoneTendencyDigestReport:
    generated_at: datetime
    config_version: str
    source_pitch_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_abs_zone_tendency_score: Decimal
    average_zone_tendency_score: Decimal
    top_screening_priority_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    tendency_rows: tuple[BaseballUmpireZoneTendencyDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballUmpireZoneTendencyDigestReport:
            raise TypeError(
                "BaseballUmpireZoneTendencyDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballUmpireZoneTendencyDigestReport:
            raise ValueError("report must be exactly BaseballUmpireZoneTendencyDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_pitch_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_abs_zone_tendency_score",
            "top_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_zone_tendency_score",
            _normalize_signed_ratio(
                "average_zone_tendency_score",
                self.average_zone_tendency_score,
            ),
        )
        if self.top_screening_priority_score > ONE:
            raise ValueError("top_screening_priority_score must not exceed one")
        _require_member("digest_status", self.digest_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "tendency_rows",
            _normalize_rows(self.tendency_rows),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_baseball_umpire_zone_tendency_digest(
    observations: Iterable[BaseballUmpireZoneTendencyObservation],
    *,
    config: BaseballUmpireZoneTendencyDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> BaseballUmpireZoneTendencyDigestReport:
    cfg = config or BaseballUmpireZoneTendencyDigestConfig()
    if type(cfg) is not BaseballUmpireZoneTendencyDigestConfig:
        raise ValueError("config must be exactly BaseballUmpireZoneTendencyDigestConfig")
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))

    source_ids: set[str] = set()
    rows: list[BaseballUmpireZoneTendencyDigestRow] = []
    for observation in observations:
        if type(observation) is not BaseballUmpireZoneTendencyObservation:
            raise ValueError(
                "observations must contain BaseballUmpireZoneTendencyObservation rows",
            )
        if observation.source_id in source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        source_ids.add(observation.source_id)
        rows.append(_build_row(observation, cfg))

    tendency_rows = tuple(sorted(rows, key=_row_sort_key))
    source_pitch_count = _sum_counts(row.source_pitch_count for row in tendency_rows)
    observation_count = _count_decimal(len(tendency_rows))
    pass_count = _count_decimal(
        sum(1 for row in tendency_rows if row.risk_status == "pass"),
    )
    watch_count = _count_decimal(
        sum(1 for row in tendency_rows if row.risk_status == "watch"),
    )
    blocked_count = _count_decimal(
        sum(1 for row in tendency_rows if row.risk_status == "blocked"),
    )
    max_abs_zone_tendency_score = max(
        (row.abs_zone_tendency_score for row in tendency_rows),
        default=ZERO,
    ).quantize(QUANTUM)
    average_zone_tendency_score = _average_ratio(
        tuple(row.zone_tendency_score for row in tendency_rows),
    )
    top_screening_priority_score = max(
        (row.screening_priority_score for row in tendency_rows),
        default=ZERO,
    ).quantize(QUANTUM)
    digest_status = _digest_status(tendency_rows)
    reason_codes = _report_reason_codes(
        digest_status,
        wide_count=_count_decimal(
            sum(
                1
                for row in tendency_rows
                if row.zone_tendency_direction == "wide_zone"
            ),
        ),
        tight_count=_count_decimal(
            sum(
                1
                for row in tendency_rows
                if row.zone_tendency_direction == "tight_zone"
            ),
        ),
    )

    return BaseballUmpireZoneTendencyDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        source_pitch_count=source_pitch_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_abs_zone_tendency_score=max_abs_zone_tendency_score,
        average_zone_tendency_score=average_zone_tendency_score,
        top_screening_priority_score=top_screening_priority_score,
        digest_status=digest_status,
        reason_codes=reason_codes,
        tendency_rows=tendency_rows,
    )


def market_research_baseball_umpire_zone_tendency_digest_payload(
    report: BaseballUmpireZoneTendencyDigestReport,
) -> dict[str, Any]:
    if type(report) is not BaseballUmpireZoneTendencyDigestReport:
        raise ValueError("report must be exactly BaseballUmpireZoneTendencyDigestReport")
    _require_hard_flags("report", report)
    value = _json_ready(asdict(report))
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _build_row(
    observation: BaseballUmpireZoneTendencyObservation,
    config: BaseballUmpireZoneTendencyDigestConfig,
) -> BaseballUmpireZoneTendencyDigestRow:
    zone_tendency_score = _calculate_zone_tendency_score(
        observation.called_strike_rate_delta,
        observation.shadow_zone_strike_rate_delta,
        observation.outside_zone_strike_rate_delta,
        observation.walk_rate_delta,
    )
    abs_zone_tendency_score = abs(zone_tendency_score).quantize(QUANTUM)
    direction = _zone_tendency_direction(
        zone_tendency_score,
        config.watch_abs_zone_tendency_score,
    )
    status = _row_status(abs_zone_tendency_score, config)
    return BaseballUmpireZoneTendencyDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        game_id=observation.game_id,
        plate_umpire_id=observation.plate_umpire_id,
        called_strike_rate_delta=observation.called_strike_rate_delta,
        shadow_zone_strike_rate_delta=observation.shadow_zone_strike_rate_delta,
        outside_zone_strike_rate_delta=observation.outside_zone_strike_rate_delta,
        walk_rate_delta=observation.walk_rate_delta,
        zone_tendency_score=zone_tendency_score,
        abs_zone_tendency_score=abs_zone_tendency_score,
        screening_priority_score=_screening_priority_score(
            abs_zone_tendency_score,
            config.blocked_abs_zone_tendency_score,
        ),
        source_pitch_count=observation.source_pitch_count,
        observed_at=observation.observed_at,
        zone_tendency_direction=direction,
        risk_status=status,
        screening_note=_screening_note(direction),
        reason_codes=_row_reason_codes(direction, status),
    )


def _row_status(
    abs_zone_tendency_score: Decimal,
    config: BaseballUmpireZoneTendencyDigestConfig,
) -> str:
    if abs_zone_tendency_score >= config.blocked_abs_zone_tendency_score:
        return "blocked"
    if abs_zone_tendency_score >= config.watch_abs_zone_tendency_score:
        return "watch"
    return "pass"


def _zone_tendency_direction(
    zone_tendency_score: Decimal,
    watch_abs_zone_tendency_score: Decimal,
) -> str:
    if abs(zone_tendency_score) < watch_abs_zone_tendency_score:
        return "inline"
    if zone_tendency_score > ZERO:
        return "wide_zone"
    return "tight_zone"


def _input_direction(zone_tendency_score: Decimal) -> str:
    if zone_tendency_score > ZERO:
        return "wide_zone"
    if zone_tendency_score < ZERO:
        return "tight_zone"
    return "inline"


def _screening_note(direction: str) -> str:
    if direction == "wide_zone":
        return "wide_zone_run_suppression"
    if direction == "tight_zone":
        return "tight_zone_run_inflation"
    return "zone_tendency_inline"


def _row_reason_codes(direction: str, status: str) -> tuple[str, ...]:
    if status == "blocked" and direction == "wide_zone":
        return ("baseball_umpire_zone_tendency_wide_zone_blocked",)
    if status == "blocked" and direction == "tight_zone":
        return ("baseball_umpire_zone_tendency_tight_zone_blocked",)
    if status == "watch" and direction == "wide_zone":
        return ("baseball_umpire_zone_tendency_wide_zone_watch",)
    if status == "watch" and direction == "tight_zone":
        return ("baseball_umpire_zone_tendency_tight_zone_watch",)
    return ("baseball_umpire_zone_tendency_inline",)


def _digest_status(rows: tuple[BaseballUmpireZoneTendencyDigestRow, ...]) -> str:
    if any(row.risk_status == "blocked" for row in rows):
        return "blocked"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    digest_status: str,
    *,
    wide_count: Decimal,
    tight_count: Decimal,
) -> tuple[str, ...]:
    if digest_status == "pass":
        return ("baseball_umpire_zone_tendency_digest_clear",)
    reasons: list[str] = []
    if digest_status == "blocked":
        reasons.append("baseball_umpire_zone_tendency_blocked_present")
    else:
        reasons.append("baseball_umpire_zone_tendency_watch_present")
    if wide_count > ZERO and tight_count > ZERO:
        reasons.append("baseball_umpire_zone_tendency_mixed_tendency_present")
    elif wide_count > ZERO:
        reasons.append("baseball_umpire_zone_tendency_wide_zone_present")
    elif tight_count > ZERO:
        reasons.append("baseball_umpire_zone_tendency_tight_zone_present")
    return tuple(reasons)


def _row_sort_key(
    row: BaseballUmpireZoneTendencyDigestRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str, str, str, str]:
    return (
        -STATUS_WEIGHT[row.risk_status],
        -row.screening_priority_score,
        -row.abs_zone_tendency_score,
        _reverse_datetime(row.observed_at),
        row.game_id,
        row.source_id,
        row.market_slug,
        row.plate_umpire_id,
    )


def _reverse_datetime(value: datetime) -> datetime:
    return datetime.max.replace(tzinfo=UTC) - (value - datetime.min.replace(tzinfo=UTC))


def _screening_priority_score(
    abs_zone_tendency_score: Decimal,
    blocked_abs_zone_tendency_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = abs_zone_tendency_score / blocked_abs_zone_tendency_score
        if score > ONE:
            return ONE
        return score.quantize(QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANTUM)


def _sum_counts(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _validate_observation(row: BaseballUmpireZoneTendencyObservation) -> None:
    zone_tendency_score = _calculate_zone_tendency_score(
        row.called_strike_rate_delta,
        row.shadow_zone_strike_rate_delta,
        row.outside_zone_strike_rate_delta,
        row.walk_rate_delta,
    )
    if row.reason_codes not in _allowed_input_reason_codes(zone_tendency_score):
        raise ValueError("reason_codes must match zone tendency direction")


def _allowed_input_reason_codes(
    zone_tendency_score: Decimal,
) -> tuple[tuple[str, ...], ...]:
    direction = _input_direction(zone_tendency_score)
    direction_reason = {
        "wide_zone": "baseball_umpire_zone_tendency_wide_zone_reported",
        "tight_zone": "baseball_umpire_zone_tendency_tight_zone_reported",
        "inline": "baseball_umpire_zone_tendency_inline_reported",
    }[direction]
    if abs(zone_tendency_score) < WATCH_ABS_ZONE_TENDENCY_SCORE and direction != "inline":
        return (
            ("baseball_umpire_zone_tendency_inline_reported",),
            (direction_reason,),
        )
    return ((direction_reason,),)


def _validate_row(row: BaseballUmpireZoneTendencyDigestRow) -> None:
    expected_score = _calculate_zone_tendency_score(
        row.called_strike_rate_delta,
        row.shadow_zone_strike_rate_delta,
        row.outside_zone_strike_rate_delta,
        row.walk_rate_delta,
    )
    if row.zone_tendency_score != expected_score:
        raise ValueError("zone_tendency_score must match umpire tendency inputs")
    if row.abs_zone_tendency_score != abs(row.zone_tendency_score).quantize(QUANTUM):
        raise ValueError("abs_zone_tendency_score must match zone_tendency_score")
    if row.screening_note != _screening_note(row.zone_tendency_direction):
        raise ValueError("screening_note must match zone tendency direction")
    if row.reason_codes != _row_reason_codes(
        row.zone_tendency_direction,
        row.risk_status,
    ):
        raise ValueError("reason_codes must match zone tendency direction and risk status")


def _validate_report(report: BaseballUmpireZoneTendencyDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.tendency_rows)):
        raise ValueError("observation_count must match tendency_rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.observation_count:
        raise ValueError("status counts must match observation_count")
    if report.source_pitch_count != _sum_counts(
        row.source_pitch_count for row in report.tendency_rows
    ):
        raise ValueError("source_pitch_count must match tendency_rows")
    if report.digest_status != _digest_status(report.tendency_rows):
        raise ValueError("digest_status must match tendency_rows")
    wide_count = _count_decimal(
        sum(1 for row in report.tendency_rows if row.zone_tendency_direction == "wide_zone"),
    )
    tight_count = _count_decimal(
        sum(1 for row in report.tendency_rows if row.zone_tendency_direction == "tight_zone"),
    )
    if report.reason_codes != _report_reason_codes(
        report.digest_status,
        wide_count=wide_count,
        tight_count=tight_count,
    ):
        raise ValueError("reason_codes must match tendency_rows")
    if report.max_abs_zone_tendency_score != max(
        (row.abs_zone_tendency_score for row in report.tendency_rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("max_abs_zone_tendency_score must match tendency_rows")
    if report.average_zone_tendency_score != _average_ratio(
        tuple(row.zone_tendency_score for row in report.tendency_rows),
    ):
        raise ValueError("average_zone_tendency_score must match tendency_rows")
    if report.top_screening_priority_score != max(
        (row.screening_priority_score for row in report.tendency_rows),
        default=ZERO,
    ).quantize(QUANTUM):
        raise ValueError("top_screening_priority_score must match tendency_rows")


def _calculate_zone_tendency_score(
    called_strike_rate_delta: Decimal,
    shadow_zone_strike_rate_delta: Decimal,
    outside_zone_strike_rate_delta: Decimal,
    walk_rate_delta: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            (called_strike_rate_delta * CALLED_STRIKE_RATE_WEIGHT)
            + (shadow_zone_strike_rate_delta * SHADOW_ZONE_STRIKE_RATE_WEIGHT)
            + (outside_zone_strike_rate_delta * OUTSIDE_ZONE_STRIKE_RATE_WEIGHT)
            - (walk_rate_delta * WALK_RATE_WEIGHT)
        ).quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _normalize_positive_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(QUANTUM)
    if normalized < NEGATIVE_ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if value not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(value)
    return tuple(value for value in allowed if value in seen)


def _normalize_rows(
    rows: tuple[BaseballUmpireZoneTendencyDigestRow, ...],
) -> tuple[BaseballUmpireZoneTendencyDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("tendency_rows must be a tuple")
    seen: set[str] = set()
    normalized: list[BaseballUmpireZoneTendencyDigestRow] = []
    for row in rows:
        if type(row) is not BaseballUmpireZoneTendencyDigestRow:
            raise ValueError("tendency_rows must contain digest rows")
        if row.source_id in seen:
            raise ValueError("tendency_rows must not contain duplicate source_id values")
        seen.add(row.source_id)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {key: _json_ready(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    if isinstance(value, list):
        return [_json_ready(child) for child in value]
    if type(value) is Decimal:
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    raise ValueError("value is not a supported report field")
