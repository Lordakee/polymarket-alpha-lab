"""Pure Phase 1 baseball plate-umpire zone-bias digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASEBALL_PLATE_UMPIRE_ZONE_BIAS_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-plate-umpire-zone-bias-digest-v0"
)

ZONE_BIAS_DIRECTIONS = ("wide_zone", "tight_zone", "inline")
RISK_STATUSES = ("pass", "watch", "blocked")
SCREENING_NOTES = (
    "wide_zone_under_bias",
    "tight_zone_over_bias",
    "zone_bias_inline",
)
INPUT_REASON_CODES = (
    "baseball_plate_umpire_wide_zone_bias",
    "baseball_plate_umpire_tight_zone_bias",
    "baseball_plate_umpire_zone_bias_inline",
)
ROW_REASON_CODES = (
    "baseball_plate_umpire_wide_zone_bias_blocked",
    "baseball_plate_umpire_tight_zone_bias_blocked",
    "baseball_plate_umpire_wide_zone_bias_watch",
    "baseball_plate_umpire_tight_zone_bias_watch",
    "baseball_plate_umpire_zone_bias_inline",
)
REPORT_REASON_CODES = (
    "baseball_plate_umpire_zone_bias_digest_clear",
    "baseball_plate_umpire_zone_bias_blocked_present",
    "baseball_plate_umpire_zone_bias_watch_present",
    "baseball_plate_umpire_mixed_zone_bias_present",
    "baseball_plate_umpire_wide_zone_bias_present",
    "baseball_plate_umpire_tight_zone_bias_present",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
WATCH_ABS_ZONE_BIAS_SCORE = Decimal("0.020000")
BLOCKED_ABS_ZONE_BIAS_SCORE = Decimal("0.050000")
CALLED_STRIKE_BIAS_WEIGHT = Decimal("0.700000")
OUTSIDE_ZONE_STRIKE_WEIGHT = Decimal("0.200000")
INSIDE_ZONE_BALL_WEIGHT = Decimal("0.050000")
RUN_ENVIRONMENT_WEIGHT = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_PLATE_UMPIRE_ZONE_BIAS_DIGEST_CONFIG_VERSION",
    "BaseballPlateUmpireZoneBiasDigestConfig",
    "BaseballPlateUmpireZoneBiasObservation",
    "BaseballPlateUmpireZoneBiasDigestRow",
    "BaseballPlateUmpireZoneBiasDigestReport",
    "build_market_research_baseball_plate_umpire_zone_bias_digest",
    "market_research_baseball_plate_umpire_zone_bias_digest_payload",
)


@dataclass(frozen=True)
class BaseballPlateUmpireZoneBiasDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_PLATE_UMPIRE_ZONE_BIAS_DIGEST_CONFIG_VERSION
    )
    watch_abs_zone_bias_score: Decimal = WATCH_ABS_ZONE_BIAS_SCORE
    blocked_abs_zone_bias_score: Decimal = BLOCKED_ABS_ZONE_BIAS_SCORE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballPlateUmpireZoneBiasDigestConfig:
            raise TypeError(
                "BaseballPlateUmpireZoneBiasDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballPlateUmpireZoneBiasDigestConfig:
            raise ValueError(
                "config must be exactly BaseballPlateUmpireZoneBiasDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_PLATE_UMPIRE_ZONE_BIAS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_abs_zone_bias_score",
            _normalize_positive_ratio(
                "watch_abs_zone_bias_score",
                self.watch_abs_zone_bias_score,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_zone_bias_score",
            _normalize_positive_ratio(
                "blocked_abs_zone_bias_score",
                self.blocked_abs_zone_bias_score,
            ),
        )
        if self.blocked_abs_zone_bias_score < self.watch_abs_zone_bias_score:
            raise ValueError(
                "blocked_abs_zone_bias_score must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BaseballPlateUmpireZoneBiasObservation:
    source_id: str
    market_slug: str
    game_id: str
    plate_umpire_id: str
    called_strike_bias_rate: Decimal
    outside_zone_strike_rate_delta: Decimal
    inside_zone_ball_rate_delta: Decimal
    run_environment_delta: Decimal
    source_row_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballPlateUmpireZoneBiasObservation:
            raise TypeError(
                "BaseballPlateUmpireZoneBiasObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballPlateUmpireZoneBiasObservation:
            raise ValueError(
                "observation must be exactly BaseballPlateUmpireZoneBiasObservation",
            )
        for field_name in ("source_id", "market_slug", "game_id", "plate_umpire_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "called_strike_bias_rate",
            "outside_zone_strike_rate_delta",
            "inside_zone_ball_rate_delta",
            "run_environment_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
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
class BaseballPlateUmpireZoneBiasDigestRow:
    source_id: str
    market_slug: str
    game_id: str
    plate_umpire_id: str
    called_strike_bias_rate: Decimal
    outside_zone_strike_rate_delta: Decimal
    inside_zone_ball_rate_delta: Decimal
    run_environment_delta: Decimal
    zone_bias_score: Decimal
    abs_zone_bias_score: Decimal
    screening_priority_score: Decimal
    source_row_count: Decimal
    observed_at: datetime
    zone_bias_direction: str
    risk_status: str
    screening_note: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballPlateUmpireZoneBiasDigestRow:
            raise TypeError(
                "BaseballPlateUmpireZoneBiasDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballPlateUmpireZoneBiasDigestRow:
            raise ValueError("row must be exactly BaseballPlateUmpireZoneBiasDigestRow")
        for field_name in ("source_id", "market_slug", "game_id", "plate_umpire_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "called_strike_bias_rate",
            "outside_zone_strike_rate_delta",
            "inside_zone_ball_rate_delta",
            "run_environment_delta",
            "zone_bias_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "abs_zone_bias_score",
            _normalize_ratio("abs_zone_bias_score", self.abs_zone_bias_score),
        )
        object.__setattr__(
            self,
            "screening_priority_score",
            _normalize_ratio("screening_priority_score", self.screening_priority_score),
        )
        if self.screening_priority_score > ONE_RATIO:
            raise ValueError("screening_priority_score must not exceed one")
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("zone_bias_direction", self.zone_bias_direction, ZONE_BIAS_DIRECTIONS)
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        _require_member("screening_note", self.screening_note, SCREENING_NOTES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BaseballPlateUmpireZoneBiasDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_abs_zone_bias_score: Decimal
    average_zone_bias_score: Decimal
    top_screening_priority_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    bias_rows: tuple[BaseballPlateUmpireZoneBiasDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballPlateUmpireZoneBiasDigestReport:
            raise TypeError(
                "BaseballPlateUmpireZoneBiasDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballPlateUmpireZoneBiasDigestReport:
            raise ValueError("report must be exactly BaseballPlateUmpireZoneBiasDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
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
            "max_abs_zone_bias_score",
            "top_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_zone_bias_score",
            _normalize_signed_ratio(
                "average_zone_bias_score",
                self.average_zone_bias_score,
            ),
        )
        if self.top_screening_priority_score > ONE_RATIO:
            raise ValueError("top_screening_priority_score must not exceed one")
        _require_member("digest_status", self.digest_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "bias_rows",
            _normalize_rows(self.bias_rows),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_baseball_plate_umpire_zone_bias_digest(
    observations: tuple[BaseballPlateUmpireZoneBiasObservation, ...],
    *,
    config: BaseballPlateUmpireZoneBiasDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> BaseballPlateUmpireZoneBiasDigestReport:
    cfg = config or BaseballPlateUmpireZoneBiasDigestConfig()
    if type(cfg) is not BaseballPlateUmpireZoneBiasDigestConfig:
        raise ValueError("config must be exactly BaseballPlateUmpireZoneBiasDigestConfig")
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))

    source_ids: set[str] = set()
    rows: list[BaseballPlateUmpireZoneBiasDigestRow] = []
    for observation in observations:
        if type(observation) is not BaseballPlateUmpireZoneBiasObservation:
            raise ValueError(
                "observations must contain BaseballPlateUmpireZoneBiasObservation rows",
            )
        if observation.source_id in source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        source_ids.add(observation.source_id)
        rows.append(_build_row(observation, cfg))

    bias_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(bias_rows))
    source_row_count = _sum_counts(row.source_row_count for row in bias_rows)
    pass_count = _count_decimal(
        sum(1 for row in bias_rows if row.risk_status == "pass"),
    )
    watch_count = _count_decimal(
        sum(1 for row in bias_rows if row.risk_status == "watch"),
    )
    blocked_count = _count_decimal(
        sum(1 for row in bias_rows if row.risk_status == "blocked"),
    )
    max_abs_zone_bias_score = max(
        (row.abs_zone_bias_score for row in bias_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM)
    average_zone_bias_score = _average_ratio(
        tuple(row.zone_bias_score for row in bias_rows),
    )
    top_screening_priority_score = max(
        (row.screening_priority_score for row in bias_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM)
    digest_status = _digest_status(bias_rows)
    reason_codes = _report_reason_codes(
        digest_status,
        wide_count=_count_decimal(
            sum(1 for row in bias_rows if row.zone_bias_direction == "wide_zone"),
        ),
        tight_count=_count_decimal(
            sum(1 for row in bias_rows if row.zone_bias_direction == "tight_zone"),
        ),
    )

    return BaseballPlateUmpireZoneBiasDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_abs_zone_bias_score=max_abs_zone_bias_score,
        average_zone_bias_score=average_zone_bias_score,
        top_screening_priority_score=top_screening_priority_score,
        digest_status=digest_status,
        reason_codes=reason_codes,
        bias_rows=bias_rows,
    )


def market_research_baseball_plate_umpire_zone_bias_digest_payload(
    report: BaseballPlateUmpireZoneBiasDigestReport,
) -> dict[str, Any]:
    if type(report) is not BaseballPlateUmpireZoneBiasDigestReport:
        raise ValueError("report must be exactly BaseballPlateUmpireZoneBiasDigestReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _build_row(
    observation: BaseballPlateUmpireZoneBiasObservation,
    config: BaseballPlateUmpireZoneBiasDigestConfig,
) -> BaseballPlateUmpireZoneBiasDigestRow:
    zone_bias_score = _calculate_zone_bias_score(
        observation.called_strike_bias_rate,
        observation.outside_zone_strike_rate_delta,
        observation.inside_zone_ball_rate_delta,
        observation.run_environment_delta,
    )
    abs_zone_bias_score = abs(zone_bias_score).quantize(RATIO_QUANTUM)
    direction = _zone_bias_direction(zone_bias_score, config.watch_abs_zone_bias_score)
    status = _row_status(abs_zone_bias_score, config)
    return BaseballPlateUmpireZoneBiasDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        game_id=observation.game_id,
        plate_umpire_id=observation.plate_umpire_id,
        called_strike_bias_rate=observation.called_strike_bias_rate,
        outside_zone_strike_rate_delta=observation.outside_zone_strike_rate_delta,
        inside_zone_ball_rate_delta=observation.inside_zone_ball_rate_delta,
        run_environment_delta=observation.run_environment_delta,
        zone_bias_score=zone_bias_score,
        abs_zone_bias_score=abs_zone_bias_score,
        screening_priority_score=_screening_priority_score(
            abs_zone_bias_score,
            config.blocked_abs_zone_bias_score,
        ),
        source_row_count=observation.source_row_count,
        observed_at=observation.observed_at,
        zone_bias_direction=direction,
        risk_status=status,
        screening_note=_screening_note(direction),
        reason_codes=_row_reason_codes(direction, status),
    )


def _row_status(
    abs_zone_bias_score: Decimal,
    config: BaseballPlateUmpireZoneBiasDigestConfig,
) -> str:
    if abs_zone_bias_score >= config.blocked_abs_zone_bias_score:
        return "blocked"
    if abs_zone_bias_score >= config.watch_abs_zone_bias_score:
        return "watch"
    return "pass"


def _zone_bias_direction(zone_bias_score: Decimal, watch_abs_zone_bias_score: Decimal) -> str:
    if abs(zone_bias_score) < watch_abs_zone_bias_score:
        return "inline"
    if zone_bias_score > ZERO_RATIO:
        return "wide_zone"
    return "tight_zone"


def _input_direction(zone_bias_score: Decimal) -> str:
    if zone_bias_score > ZERO_RATIO:
        return "wide_zone"
    if zone_bias_score < ZERO_RATIO:
        return "tight_zone"
    return "inline"


def _screening_note(direction: str) -> str:
    if direction == "wide_zone":
        return "wide_zone_under_bias"
    if direction == "tight_zone":
        return "tight_zone_over_bias"
    return "zone_bias_inline"


def _row_reason_codes(direction: str, status: str) -> tuple[str, ...]:
    if status == "blocked" and direction == "wide_zone":
        return ("baseball_plate_umpire_wide_zone_bias_blocked",)
    if status == "blocked" and direction == "tight_zone":
        return ("baseball_plate_umpire_tight_zone_bias_blocked",)
    if status == "watch" and direction == "wide_zone":
        return ("baseball_plate_umpire_wide_zone_bias_watch",)
    if status == "watch" and direction == "tight_zone":
        return ("baseball_plate_umpire_tight_zone_bias_watch",)
    return ("baseball_plate_umpire_zone_bias_inline",)


def _digest_status(rows: tuple[BaseballPlateUmpireZoneBiasDigestRow, ...]) -> str:
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
        return ("baseball_plate_umpire_zone_bias_digest_clear",)
    reasons: list[str] = []
    if digest_status == "blocked":
        reasons.append("baseball_plate_umpire_zone_bias_blocked_present")
    else:
        reasons.append("baseball_plate_umpire_zone_bias_watch_present")
    if wide_count > ZERO_COUNT and tight_count > ZERO_COUNT:
        reasons.append("baseball_plate_umpire_mixed_zone_bias_present")
    elif wide_count > ZERO_COUNT:
        reasons.append("baseball_plate_umpire_wide_zone_bias_present")
    elif tight_count > ZERO_COUNT:
        reasons.append("baseball_plate_umpire_tight_zone_bias_present")
    return tuple(reasons)


def _row_sort_key(
    row: BaseballPlateUmpireZoneBiasDigestRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str, str, str, str]:
    return (
        -STATUS_WEIGHT[row.risk_status],
        -row.screening_priority_score,
        -row.abs_zone_bias_score,
        _reverse_datetime(row.observed_at),
        row.game_id,
        row.source_id,
        row.market_slug,
        row.plate_umpire_id,
    )


def _reverse_datetime(value: datetime) -> datetime:
    return datetime.max.replace(tzinfo=UTC) - (value - datetime.min.replace(tzinfo=UTC))


def _screening_priority_score(
    abs_zone_bias_score: Decimal,
    blocked_abs_zone_bias_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = abs_zone_bias_score / blocked_abs_zone_bias_score
        if score > ONE_RATIO:
            return ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _sum_counts(values: Any) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        total += value
    return total.quantize(COUNT_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_observation(row: BaseballPlateUmpireZoneBiasObservation) -> None:
    zone_bias_score = _calculate_zone_bias_score(
        row.called_strike_bias_rate,
        row.outside_zone_strike_rate_delta,
        row.inside_zone_ball_rate_delta,
        row.run_environment_delta,
    )
    if row.reason_codes not in _allowed_input_reason_codes(zone_bias_score):
        raise ValueError("reason_codes must match zone bias direction")


def _allowed_input_reason_codes(
    zone_bias_score: Decimal,
) -> tuple[tuple[str, ...], ...]:
    direction = _input_direction(zone_bias_score)
    direction_reason = {
        "wide_zone": "baseball_plate_umpire_wide_zone_bias",
        "tight_zone": "baseball_plate_umpire_tight_zone_bias",
        "inline": "baseball_plate_umpire_zone_bias_inline",
    }[direction]
    if abs(zone_bias_score) < WATCH_ABS_ZONE_BIAS_SCORE and direction != "inline":
        return (
            ("baseball_plate_umpire_zone_bias_inline",),
            (direction_reason,),
        )
    return ((direction_reason,),)


def _validate_row(row: BaseballPlateUmpireZoneBiasDigestRow) -> None:
    expected_score = _calculate_zone_bias_score(
        row.called_strike_bias_rate,
        row.outside_zone_strike_rate_delta,
        row.inside_zone_ball_rate_delta,
        row.run_environment_delta,
    )
    if row.zone_bias_score != expected_score:
        raise ValueError("zone_bias_score must match plate-umpire bias inputs")
    if row.abs_zone_bias_score != abs(row.zone_bias_score).quantize(RATIO_QUANTUM):
        raise ValueError("abs_zone_bias_score must match zone_bias_score")
    if row.screening_note != _screening_note(row.zone_bias_direction):
        raise ValueError("screening_note must match zone bias direction")
    if row.reason_codes != _row_reason_codes(row.zone_bias_direction, row.risk_status):
        raise ValueError("reason_codes must match zone bias direction and risk status")


def _validate_report(report: BaseballPlateUmpireZoneBiasDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.bias_rows)):
        raise ValueError("observation_count must match bias_rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.observation_count:
        raise ValueError("status counts must match observation_count")
    if report.source_row_count != _sum_counts(row.source_row_count for row in report.bias_rows):
        raise ValueError("source_row_count must match bias_rows")
    if report.digest_status != _digest_status(report.bias_rows):
        raise ValueError("digest_status must match bias_rows")
    wide_count = _count_decimal(
        sum(1 for row in report.bias_rows if row.zone_bias_direction == "wide_zone"),
    )
    tight_count = _count_decimal(
        sum(1 for row in report.bias_rows if row.zone_bias_direction == "tight_zone"),
    )
    if report.reason_codes != _report_reason_codes(
        report.digest_status,
        wide_count=wide_count,
        tight_count=tight_count,
    ):
        raise ValueError("reason_codes must match bias_rows")
    if report.max_abs_zone_bias_score != max(
        (row.abs_zone_bias_score for row in report.bias_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("max_abs_zone_bias_score must match bias_rows")
    if report.average_zone_bias_score != _average_ratio(
        tuple(row.zone_bias_score for row in report.bias_rows),
    ):
        raise ValueError("average_zone_bias_score must match bias_rows")
    if report.top_screening_priority_score != max(
        (row.screening_priority_score for row in report.bias_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("top_screening_priority_score must match bias_rows")


def _calculate_zone_bias_score(
    called_strike_bias_rate: Decimal,
    outside_zone_strike_rate_delta: Decimal,
    inside_zone_ball_rate_delta: Decimal,
    run_environment_delta: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            (called_strike_bias_rate * CALLED_STRIKE_BIAS_WEIGHT)
            + (outside_zone_strike_rate_delta * OUTSIDE_ZONE_STRIKE_WEIGHT)
            - (inside_zone_ball_rate_delta * INSIDE_ZONE_BALL_WEIGHT)
            - (run_environment_delta * RUN_ENVIRONMENT_WEIGHT)
        ).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_ratio(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
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
    rows: tuple[BaseballPlateUmpireZoneBiasDigestRow, ...],
) -> tuple[BaseballPlateUmpireZoneBiasDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("bias_rows must be a tuple")
    seen: set[str] = set()
    normalized: list[BaseballPlateUmpireZoneBiasDigestRow] = []
    for row in rows:
        if type(row) is not BaseballPlateUmpireZoneBiasDigestRow:
            raise ValueError("bias_rows must contain digest rows")
        if row.source_id in seen:
            raise ValueError("bias_rows must not contain duplicate source_id values")
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
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    raise ValueError("value is not a supported report field")
