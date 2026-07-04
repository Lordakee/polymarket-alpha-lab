"""Pure Phase 1 soccer VAR/referee assignment pressure digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_VAR_ASSIGNMENT_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-var-assignment-pressure-digest-v0"
)

ASSIGNMENT_ROLES = ("center_referee", "var_official")
PRESSURE_DIRECTIONS = (
    "favorite_pressure",
    "underdog_pressure",
    "balanced_pressure",
)
PRESSURE_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "soccer_var_assignment_favorite_pressure",
    "soccer_var_assignment_underdog_pressure",
    "soccer_var_assignment_balanced_pressure",
)
ROW_REASON_CODES = (
    "soccer_var_assignment_pressure_blocked_favorite",
    "soccer_var_assignment_pressure_blocked_underdog",
    "soccer_var_assignment_pressure_blocked_balanced",
    "soccer_var_assignment_pressure_watch_favorite",
    "soccer_var_assignment_pressure_watch_underdog",
    "soccer_var_assignment_pressure_watch_balanced",
    "soccer_var_assignment_pressure_pass",
)
REPORT_REASON_CODES = (
    "soccer_var_assignment_pressure_digest_clear",
    "soccer_var_assignment_pressure_blocked_present",
    "soccer_var_assignment_pressure_watch_present",
    "soccer_var_assignment_pressure_mixed_direction_present",
    "soccer_var_assignment_pressure_favorite_present",
    "soccer_var_assignment_pressure_underdog_present",
    "soccer_var_assignment_pressure_balanced_present",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
WATCH_ASSIGNMENT_PRESSURE_SCORE = Decimal("0.500000")
BLOCKED_ASSIGNMENT_PRESSURE_SCORE = Decimal("0.750000")
DIRECTIONAL_MOVE_THRESHOLD = Decimal("0.030000")
PUBLIC_PRESSURE_WEIGHT = Decimal("0.350000")
VAR_OVERTURN_WEIGHT = Decimal("0.300000")
CONTROVERSY_RECENCY_WEIGHT = Decimal("0.250000")
MARKET_MOVE_WEIGHT = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_VAR_ASSIGNMENT_PRESSURE_DIGEST_CONFIG_VERSION",
    "SoccerVarAssignmentPressureDigestConfig",
    "SoccerVarAssignmentPressureObservation",
    "SoccerVarAssignmentPressureDigestRow",
    "SoccerVarAssignmentPressureDigestReport",
    "build_market_research_soccer_var_assignment_pressure_digest",
    "market_research_soccer_var_assignment_pressure_digest_payload",
)


@dataclass(frozen=True)
class SoccerVarAssignmentPressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_VAR_ASSIGNMENT_PRESSURE_DIGEST_CONFIG_VERSION
    )
    watch_assignment_pressure_score: Decimal = WATCH_ASSIGNMENT_PRESSURE_SCORE
    blocked_assignment_pressure_score: Decimal = BLOCKED_ASSIGNMENT_PRESSURE_SCORE
    directional_move_threshold: Decimal = DIRECTIONAL_MOVE_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerVarAssignmentPressureDigestConfig:
            raise TypeError(
                "SoccerVarAssignmentPressureDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerVarAssignmentPressureDigestConfig:
            raise ValueError(
                "config must be exactly SoccerVarAssignmentPressureDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SOCCER_VAR_ASSIGNMENT_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_assignment_pressure_score",
            _normalize_positive_ratio(
                "watch_assignment_pressure_score",
                self.watch_assignment_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "blocked_assignment_pressure_score",
            _normalize_positive_ratio(
                "blocked_assignment_pressure_score",
                self.blocked_assignment_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "directional_move_threshold",
            _normalize_positive_ratio(
                "directional_move_threshold",
                self.directional_move_threshold,
            ),
        )
        if self.blocked_assignment_pressure_score < self.watch_assignment_pressure_score:
            raise ValueError(
                "blocked_assignment_pressure_score must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SoccerVarAssignmentPressureObservation:
    source_id: str
    market_slug: str
    match_slug: str
    competition: str
    official_id: str
    assignment_role: str
    public_pressure_index: Decimal
    var_overturn_tendency: Decimal
    controversy_recency_score: Decimal
    market_probability_move: Decimal
    source_row_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerVarAssignmentPressureObservation:
            raise TypeError(
                "SoccerVarAssignmentPressureObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerVarAssignmentPressureObservation:
            raise ValueError(
                "observation must be exactly SoccerVarAssignmentPressureObservation",
            )
        for field_name in (
            "source_id",
            "market_slug",
            "match_slug",
            "competition",
            "official_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("assignment_role", self.assignment_role, ASSIGNMENT_ROLES)
        for field_name in (
            "public_pressure_index",
            "var_overturn_tendency",
            "controversy_recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_probability_move",
            _normalize_probability_move(
                "market_probability_move",
                self.market_probability_move,
            ),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
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
class SoccerVarAssignmentPressureDigestRow:
    source_id: str
    market_slug: str
    match_slug: str
    competition: str
    official_id: str
    assignment_role: str
    public_pressure_index: Decimal
    var_overturn_tendency: Decimal
    controversy_recency_score: Decimal
    market_probability_move: Decimal
    directional_move_abs: Decimal
    assignment_pressure_score: Decimal
    screening_priority_score: Decimal
    source_row_count: Decimal
    observed_at: datetime
    pressure_direction: str
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerVarAssignmentPressureDigestRow:
            raise TypeError(
                "SoccerVarAssignmentPressureDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerVarAssignmentPressureDigestRow:
            raise ValueError("row must be exactly SoccerVarAssignmentPressureDigestRow")
        for field_name in (
            "source_id",
            "market_slug",
            "match_slug",
            "competition",
            "official_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("assignment_role", self.assignment_role, ASSIGNMENT_ROLES)
        for field_name in (
            "public_pressure_index",
            "var_overturn_tendency",
            "controversy_recency_score",
            "directional_move_abs",
            "assignment_pressure_score",
            "screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_probability_move",
            _normalize_probability_move(
                "market_probability_move",
                self.market_probability_move,
            ),
        )
        if self.screening_priority_score > ONE_RATIO:
            raise ValueError("screening_priority_score must not exceed one")
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("pressure_direction", self.pressure_direction, PRESSURE_DIRECTIONS)
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SoccerVarAssignmentPressureDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_assignment_pressure_score: Decimal
    average_assignment_pressure_score: Decimal
    top_screening_priority_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    pressure_rows: tuple[SoccerVarAssignmentPressureDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SoccerVarAssignmentPressureDigestReport:
            raise TypeError(
                "SoccerVarAssignmentPressureDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SoccerVarAssignmentPressureDigestReport:
            raise ValueError("report must be exactly SoccerVarAssignmentPressureDigestReport")
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
            "max_assignment_pressure_score",
            "average_assignment_pressure_score",
            "top_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.top_screening_priority_score > ONE_RATIO:
            raise ValueError("top_screening_priority_score must not exceed one")
        _require_member("digest_status", self.digest_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "pressure_rows",
            _normalize_rows(self.pressure_rows),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_soccer_var_assignment_pressure_digest(
    observations: tuple[SoccerVarAssignmentPressureObservation, ...],
    *,
    config: SoccerVarAssignmentPressureDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> SoccerVarAssignmentPressureDigestReport:
    cfg = config or SoccerVarAssignmentPressureDigestConfig()
    if type(cfg) is not SoccerVarAssignmentPressureDigestConfig:
        raise ValueError("config must be exactly SoccerVarAssignmentPressureDigestConfig")
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))

    source_ids: set[str] = set()
    rows: list[SoccerVarAssignmentPressureDigestRow] = []
    for observation in observations:
        if type(observation) is not SoccerVarAssignmentPressureObservation:
            raise ValueError(
                "observations must contain SoccerVarAssignmentPressureObservation rows",
            )
        if observation.source_id in source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        source_ids.add(observation.source_id)
        rows.append(_build_row(observation, cfg))

    pressure_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(pressure_rows))
    source_row_count = _sum_counts(row.source_row_count for row in pressure_rows)
    pass_count = _count_decimal(
        sum(1 for row in pressure_rows if row.pressure_status == "pass"),
    )
    watch_count = _count_decimal(
        sum(1 for row in pressure_rows if row.pressure_status == "watch"),
    )
    blocked_count = _count_decimal(
        sum(1 for row in pressure_rows if row.pressure_status == "blocked"),
    )
    max_assignment_pressure_score = max(
        (row.assignment_pressure_score for row in pressure_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM)
    average_assignment_pressure_score = _average_ratio(
        tuple(row.assignment_pressure_score for row in pressure_rows),
    )
    top_screening_priority_score = max(
        (row.screening_priority_score for row in pressure_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM)
    digest_status = _digest_status(pressure_rows)
    reason_codes = _report_reason_codes(digest_status, pressure_rows)

    return SoccerVarAssignmentPressureDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_assignment_pressure_score=max_assignment_pressure_score,
        average_assignment_pressure_score=average_assignment_pressure_score,
        top_screening_priority_score=top_screening_priority_score,
        digest_status=digest_status,
        reason_codes=reason_codes,
        pressure_rows=pressure_rows,
    )


def market_research_soccer_var_assignment_pressure_digest_payload(
    report: SoccerVarAssignmentPressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not SoccerVarAssignmentPressureDigestReport:
        raise ValueError("report must be exactly SoccerVarAssignmentPressureDigestReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _build_row(
    observation: SoccerVarAssignmentPressureObservation,
    config: SoccerVarAssignmentPressureDigestConfig,
) -> SoccerVarAssignmentPressureDigestRow:
    directional_move_abs = abs(observation.market_probability_move).quantize(
        RATIO_QUANTUM,
    )
    assignment_pressure_score = _calculate_assignment_pressure_score(
        observation.public_pressure_index,
        observation.var_overturn_tendency,
        observation.controversy_recency_score,
        directional_move_abs,
    )
    direction = _pressure_direction(
        observation.market_probability_move,
        config.directional_move_threshold,
    )
    status = _row_status(assignment_pressure_score, config)
    return SoccerVarAssignmentPressureDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        match_slug=observation.match_slug,
        competition=observation.competition,
        official_id=observation.official_id,
        assignment_role=observation.assignment_role,
        public_pressure_index=observation.public_pressure_index,
        var_overturn_tendency=observation.var_overturn_tendency,
        controversy_recency_score=observation.controversy_recency_score,
        market_probability_move=observation.market_probability_move,
        directional_move_abs=directional_move_abs,
        assignment_pressure_score=assignment_pressure_score,
        screening_priority_score=_screening_priority_score(
            assignment_pressure_score,
            config.blocked_assignment_pressure_score,
        ),
        source_row_count=observation.source_row_count,
        observed_at=observation.observed_at,
        pressure_direction=direction,
        pressure_status=status,
        reason_codes=_row_reason_codes(direction, status),
    )


def _row_status(
    assignment_pressure_score: Decimal,
    config: SoccerVarAssignmentPressureDigestConfig,
) -> str:
    if assignment_pressure_score >= config.blocked_assignment_pressure_score:
        return "blocked"
    if assignment_pressure_score >= config.watch_assignment_pressure_score:
        return "watch"
    return "pass"


def _pressure_direction(
    market_probability_move: Decimal,
    directional_move_threshold: Decimal,
) -> str:
    if market_probability_move >= directional_move_threshold:
        return "favorite_pressure"
    if market_probability_move <= -directional_move_threshold:
        return "underdog_pressure"
    return "balanced_pressure"


def _row_reason_codes(direction: str, status: str) -> tuple[str, ...]:
    if status == "blocked" and direction == "favorite_pressure":
        return ("soccer_var_assignment_pressure_blocked_favorite",)
    if status == "blocked" and direction == "underdog_pressure":
        return ("soccer_var_assignment_pressure_blocked_underdog",)
    if status == "blocked" and direction == "balanced_pressure":
        return ("soccer_var_assignment_pressure_blocked_balanced",)
    if status == "watch" and direction == "favorite_pressure":
        return ("soccer_var_assignment_pressure_watch_favorite",)
    if status == "watch" and direction == "underdog_pressure":
        return ("soccer_var_assignment_pressure_watch_underdog",)
    if status == "watch" and direction == "balanced_pressure":
        return ("soccer_var_assignment_pressure_watch_balanced",)
    return ("soccer_var_assignment_pressure_pass",)


def _digest_status(rows: tuple[SoccerVarAssignmentPressureDigestRow, ...]) -> str:
    if any(row.pressure_status == "blocked" for row in rows):
        return "blocked"
    if any(row.pressure_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    digest_status: str,
    rows: tuple[SoccerVarAssignmentPressureDigestRow, ...],
) -> tuple[str, ...]:
    if digest_status == "pass":
        return ("soccer_var_assignment_pressure_digest_clear",)

    active_directions = {
        row.pressure_direction
        for row in rows
        if row.pressure_status in ("watch", "blocked")
    }
    reasons: list[str] = []
    if digest_status == "blocked":
        reasons.append("soccer_var_assignment_pressure_blocked_present")
    else:
        reasons.append("soccer_var_assignment_pressure_watch_present")

    directional = active_directions & {"favorite_pressure", "underdog_pressure"}
    if len(directional) > 1:
        reasons.append("soccer_var_assignment_pressure_mixed_direction_present")
    elif "favorite_pressure" in directional:
        reasons.append("soccer_var_assignment_pressure_favorite_present")
    elif "underdog_pressure" in directional:
        reasons.append("soccer_var_assignment_pressure_underdog_present")
    else:
        reasons.append("soccer_var_assignment_pressure_balanced_present")
    return tuple(reasons)


def _row_sort_key(
    row: SoccerVarAssignmentPressureDigestRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str, str, str, str]:
    return (
        -STATUS_WEIGHT[row.pressure_status],
        -row.screening_priority_score,
        -row.assignment_pressure_score,
        _reverse_datetime(row.observed_at),
        row.competition,
        row.match_slug,
        row.source_id,
        row.market_slug,
    )


def _reverse_datetime(value: datetime) -> datetime:
    return datetime.max.replace(tzinfo=UTC) - (value - datetime.min.replace(tzinfo=UTC))


def _screening_priority_score(
    assignment_pressure_score: Decimal,
    blocked_assignment_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = assignment_pressure_score / blocked_assignment_pressure_score
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


def _calculate_assignment_pressure_score(
    public_pressure_index: Decimal,
    var_overturn_tendency: Decimal,
    controversy_recency_score: Decimal,
    directional_move_abs: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            public_pressure_index * PUBLIC_PRESSURE_WEIGHT
            + var_overturn_tendency * VAR_OVERTURN_WEIGHT
            + controversy_recency_score * CONTROVERSY_RECENCY_WEIGHT
            + directional_move_abs * MARKET_MOVE_WEIGHT
        )
        if score > ONE_RATIO:
            return ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _validate_observation(row: SoccerVarAssignmentPressureObservation) -> None:
    direction = _pressure_direction(row.market_probability_move, DIRECTIONAL_MOVE_THRESHOLD)
    if row.reason_codes != _input_reason_codes(direction):
        raise ValueError("reason_codes must match pressure direction")


def _input_reason_codes(direction: str) -> tuple[str, ...]:
    return (
        {
            "favorite_pressure": "soccer_var_assignment_favorite_pressure",
            "underdog_pressure": "soccer_var_assignment_underdog_pressure",
            "balanced_pressure": "soccer_var_assignment_balanced_pressure",
        }[direction],
    )


def _validate_row(row: SoccerVarAssignmentPressureDigestRow) -> None:
    expected_directional_move_abs = abs(row.market_probability_move).quantize(
        RATIO_QUANTUM,
    )
    if row.directional_move_abs != expected_directional_move_abs:
        raise ValueError("directional_move_abs must match market_probability_move")
    expected_score = _calculate_assignment_pressure_score(
        row.public_pressure_index,
        row.var_overturn_tendency,
        row.controversy_recency_score,
        row.directional_move_abs,
    )
    if row.assignment_pressure_score != expected_score:
        raise ValueError("assignment_pressure_score must match pressure inputs")
    if row.reason_codes != _row_reason_codes(row.pressure_direction, row.pressure_status):
        raise ValueError("reason_codes must match pressure direction and status")


def _validate_report(report: SoccerVarAssignmentPressureDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.pressure_rows)):
        raise ValueError("observation_count must match pressure_rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.observation_count:
        raise ValueError("status counts must match observation_count")
    if report.source_row_count != _sum_counts(
        row.source_row_count for row in report.pressure_rows
    ):
        raise ValueError("source_row_count must match pressure_rows")
    if report.digest_status != _digest_status(report.pressure_rows):
        raise ValueError("digest_status must match pressure_rows")
    if report.max_assignment_pressure_score != max(
        (row.assignment_pressure_score for row in report.pressure_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("max_assignment_pressure_score must match pressure_rows")
    if report.average_assignment_pressure_score != _average_ratio(
        tuple(row.assignment_pressure_score for row in report.pressure_rows),
    ):
        raise ValueError("average_assignment_pressure_score must match pressure_rows")
    if report.top_screening_priority_score != max(
        (row.screening_priority_score for row in report.pressure_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("top_screening_priority_score must match pressure_rows")
    if report.reason_codes != _report_reason_codes(report.digest_status, report.pressure_rows):
        raise ValueError("reason_codes must match pressure_rows")


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
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _normalize_positive_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability_move(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < -ONE_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


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
    rows: tuple[SoccerVarAssignmentPressureDigestRow, ...],
) -> tuple[SoccerVarAssignmentPressureDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("pressure_rows must be a tuple")
    seen: set[str] = set()
    normalized: list[SoccerVarAssignmentPressureDigestRow] = []
    for row in rows:
        if type(row) is not SoccerVarAssignmentPressureDigestRow:
            raise ValueError("pressure_rows must contain digest rows")
        if row.source_id in seen:
            raise ValueError("pressure_rows must not contain duplicate source_id values")
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
