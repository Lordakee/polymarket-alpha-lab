"""Pure Phase 1 baseball starting-pitcher late swap risk digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import math
import re
from typing import Any


DEFAULT_BASEBALL_STARTING_PITCHER_LATE_SWAP_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-starting-pitcher-late-swap-digest-v0"
)

STARTER_STATUSES = ("confirmed", "questionable", "changed")
SWAP_RISK_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "baseball_starting_pitcher_confirmed",
    "baseball_starting_pitcher_questionable",
    "baseball_starting_pitcher_changed",
    "baseball_starting_pitcher_confirmation_stale",
)
STARTER_STATUS_REASON_CODES = INPUT_REASON_CODES[:3]
ROW_REASON_CODES = (
    "baseball_starting_pitcher_late_swap_changed_starter",
    "baseball_starting_pitcher_late_swap_high_scratch_probability",
    "baseball_starting_pitcher_late_swap_watch_scratch_probability",
    "baseball_starting_pitcher_late_swap_questionable_near_first_pitch",
    "baseball_starting_pitcher_late_swap_stale_confirmation_near_first_pitch",
    "baseball_starting_pitcher_late_swap_clear",
)
REPORT_REASON_CODES = (
    "baseball_starting_pitcher_late_swap_digest_clear",
    "baseball_starting_pitcher_late_swap_blocked_risk_present",
    "baseball_starting_pitcher_late_swap_changed_starter_present",
    "baseball_starting_pitcher_late_swap_watch_risk_present",
)

COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
PROBABILITY_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_VALUE = Decimal("0.000000")
ZERO_PROBABILITY = Decimal("0.000000")
ONE_PROBABILITY = Decimal("1.000000")
WATCH_SCRATCH_PROBABILITY = Decimal("0.120000")
BLOCKED_SCRATCH_PROBABILITY = Decimal("0.250000")
WATCH_MINUTES_UNTIL_FIRST_PITCH = Decimal("180.000000")
BLOCKED_MINUTES_UNTIL_FIRST_PITCH = Decimal("60.000000")
STALE_CONFIRMATION_AGE_MINUTES = Decimal("120.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_BASEBALL_STARTING_PITCHER_LATE_SWAP_DIGEST_CONFIG_VERSION",
    "BaseballStartingPitcherLateSwapDigestConfig",
    "BaseballStartingPitcherLateSwapObservation",
    "BaseballStartingPitcherLateSwapDigestRow",
    "BaseballStartingPitcherLateSwapDigestReport",
    "build_market_research_baseball_starting_pitcher_late_swap_digest",
    "market_research_baseball_starting_pitcher_late_swap_digest_payload",
)


@dataclass(frozen=True)
class BaseballStartingPitcherLateSwapDigestConfig:
    config_version: str = DEFAULT_BASEBALL_STARTING_PITCHER_LATE_SWAP_DIGEST_CONFIG_VERSION
    watch_scratch_probability: Decimal = WATCH_SCRATCH_PROBABILITY
    blocked_scratch_probability: Decimal = BLOCKED_SCRATCH_PROBABILITY
    watch_minutes_until_first_pitch: Decimal = WATCH_MINUTES_UNTIL_FIRST_PITCH
    blocked_minutes_until_first_pitch: Decimal = BLOCKED_MINUTES_UNTIL_FIRST_PITCH
    stale_confirmation_age_minutes: Decimal = STALE_CONFIRMATION_AGE_MINUTES
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballStartingPitcherLateSwapDigestConfig:
            raise TypeError(
                "BaseballStartingPitcherLateSwapDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballStartingPitcherLateSwapDigestConfig:
            raise ValueError(
                "config must be exactly BaseballStartingPitcherLateSwapDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASEBALL_STARTING_PITCHER_LATE_SWAP_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_scratch_probability",
            _normalize_positive_probability(
                "watch_scratch_probability",
                self.watch_scratch_probability,
            ),
        )
        object.__setattr__(
            self,
            "blocked_scratch_probability",
            _normalize_positive_probability(
                "blocked_scratch_probability",
                self.blocked_scratch_probability,
            ),
        )
        object.__setattr__(
            self,
            "watch_minutes_until_first_pitch",
            _normalize_positive_value(
                "watch_minutes_until_first_pitch",
                self.watch_minutes_until_first_pitch,
            ),
        )
        object.__setattr__(
            self,
            "blocked_minutes_until_first_pitch",
            _normalize_positive_value(
                "blocked_minutes_until_first_pitch",
                self.blocked_minutes_until_first_pitch,
            ),
        )
        object.__setattr__(
            self,
            "stale_confirmation_age_minutes",
            _normalize_positive_value(
                "stale_confirmation_age_minutes",
                self.stale_confirmation_age_minutes,
            ),
        )
        if self.blocked_scratch_probability < self.watch_scratch_probability:
            raise ValueError(
                "blocked_scratch_probability must be at least watch threshold",
            )
        if self.blocked_minutes_until_first_pitch > self.watch_minutes_until_first_pitch:
            raise ValueError(
                "blocked_minutes_until_first_pitch must be at most watch window",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BaseballStartingPitcherLateSwapObservation:
    source_id: str
    game_id: str
    market_slug: str
    team_id: str
    scheduled_starter_id: str
    current_listed_starter_id: str
    starter_status: str
    minutes_until_first_pitch: Decimal
    lineup_confirmation_age_minutes: Decimal
    scratch_probability: Decimal
    market_probability: Decimal
    liquidity_usd: Decimal
    source_row_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballStartingPitcherLateSwapObservation:
            raise TypeError(
                "BaseballStartingPitcherLateSwapObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballStartingPitcherLateSwapObservation:
            raise ValueError(
                "observation must be exactly BaseballStartingPitcherLateSwapObservation",
            )
        for field_name in (
            "source_id",
            "game_id",
            "market_slug",
            "team_id",
            "scheduled_starter_id",
            "current_listed_starter_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("starter_status", self.starter_status, STARTER_STATUSES)
        for field_name in (
            "minutes_until_first_pitch",
            "lineup_confirmation_age_minutes",
            "liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in ("scratch_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_starter_consistency(
            self.starter_status,
            self.scheduled_starter_id,
            self.current_listed_starter_id,
        )
        _validate_observation_reason_codes(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class BaseballStartingPitcherLateSwapDigestRow:
    source_id: str
    game_id: str
    market_slug: str
    team_id: str
    scheduled_starter_id: str
    current_listed_starter_id: str
    starter_status: str
    minutes_until_first_pitch: Decimal
    lineup_confirmation_age_minutes: Decimal
    scratch_probability: Decimal
    market_probability: Decimal
    liquidity_usd: Decimal
    source_row_count: Decimal
    observed_at: datetime
    swap_risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballStartingPitcherLateSwapDigestRow:
            raise TypeError(
                "BaseballStartingPitcherLateSwapDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballStartingPitcherLateSwapDigestRow:
            raise ValueError("row must be exactly BaseballStartingPitcherLateSwapDigestRow")
        for field_name in (
            "source_id",
            "game_id",
            "market_slug",
            "team_id",
            "scheduled_starter_id",
            "current_listed_starter_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("starter_status", self.starter_status, STARTER_STATUSES)
        for field_name in (
            "minutes_until_first_pitch",
            "lineup_confirmation_age_minutes",
            "liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in ("scratch_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("swap_risk_status", self.swap_risk_status, SWAP_RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_starter_consistency(
            self.starter_status,
            self.scheduled_starter_id,
            self.current_listed_starter_id,
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BaseballStartingPitcherLateSwapDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    blocked_swap_risk_count: Decimal
    watch_swap_risk_count: Decimal
    pass_swap_risk_count: Decimal
    changed_starter_count: Decimal
    max_scratch_probability: Decimal
    average_scratch_probability: Decimal
    min_minutes_until_first_pitch: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    risk_rows: tuple[BaseballStartingPitcherLateSwapDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BaseballStartingPitcherLateSwapDigestReport:
            raise TypeError(
                "BaseballStartingPitcherLateSwapDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BaseballStartingPitcherLateSwapDigestReport:
            raise ValueError("report must be exactly BaseballStartingPitcherLateSwapDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "observation_count",
            "blocked_swap_risk_count",
            "watch_swap_risk_count",
            "pass_swap_risk_count",
            "changed_starter_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_scratch_probability",
            "average_scratch_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_minutes_until_first_pitch",
            _normalize_nonnegative_value(
                "min_minutes_until_first_pitch",
                self.min_minutes_until_first_pitch,
            ),
        )
        _require_member("digest_status", self.digest_status, SWAP_RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "risk_rows", _normalize_rows(self.risk_rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_baseball_starting_pitcher_late_swap_digest(
    observations: tuple[BaseballStartingPitcherLateSwapObservation, ...],
    *,
    config: BaseballStartingPitcherLateSwapDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> BaseballStartingPitcherLateSwapDigestReport:
    cfg = config or BaseballStartingPitcherLateSwapDigestConfig()
    if type(cfg) is not BaseballStartingPitcherLateSwapDigestConfig:
        raise ValueError(
            "config must be exactly BaseballStartingPitcherLateSwapDigestConfig",
        )
    _require_hard_flags("config", cfg)
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))

    source_ids: set[str] = set()
    rows: list[BaseballStartingPitcherLateSwapDigestRow] = []
    for observation in observations:
        if type(observation) is not BaseballStartingPitcherLateSwapObservation:
            raise ValueError(
                "observations must contain BaseballStartingPitcherLateSwapObservation rows",
            )
        if observation.source_id in source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        source_ids.add(observation.source_id)
        rows.append(_build_row(observation, cfg))

    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(sorted_rows))
    source_row_count = _sum_counts(row.source_row_count for row in sorted_rows)
    blocked_count = _count_decimal(
        sum(1 for row in sorted_rows if row.swap_risk_status == "blocked"),
    )
    watch_count = _count_decimal(
        sum(1 for row in sorted_rows if row.swap_risk_status == "watch"),
    )
    pass_count = _count_decimal(
        sum(1 for row in sorted_rows if row.swap_risk_status == "pass"),
    )
    changed_count = _count_decimal(
        sum(1 for row in sorted_rows if row.starter_status == "changed"),
    )
    max_scratch_probability = max(
        (row.scratch_probability for row in sorted_rows),
        default=ZERO_PROBABILITY,
    ).quantize(PROBABILITY_QUANTUM)
    average_scratch_probability = _average_probability(
        tuple(row.scratch_probability for row in sorted_rows),
    )
    min_minutes_until_first_pitch = min(
        (row.minutes_until_first_pitch for row in sorted_rows),
        default=ZERO_VALUE,
    ).quantize(VALUE_QUANTUM)
    digest_status = _digest_status(sorted_rows)
    reason_codes = _report_reason_codes(
        digest_status,
        blocked_count=blocked_count,
        watch_count=watch_count,
        changed_count=changed_count,
    )

    return BaseballStartingPitcherLateSwapDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        observation_count=observation_count,
        blocked_swap_risk_count=blocked_count,
        watch_swap_risk_count=watch_count,
        pass_swap_risk_count=pass_count,
        changed_starter_count=changed_count,
        max_scratch_probability=max_scratch_probability,
        average_scratch_probability=average_scratch_probability,
        min_minutes_until_first_pitch=min_minutes_until_first_pitch,
        digest_status=digest_status,
        reason_codes=reason_codes,
        risk_rows=sorted_rows,
    )


def market_research_baseball_starting_pitcher_late_swap_digest_payload(
    report: BaseballStartingPitcherLateSwapDigestReport,
) -> dict[str, Any]:
    if type(report) is not BaseballStartingPitcherLateSwapDigestReport:
        raise ValueError("report must be exactly BaseballStartingPitcherLateSwapDigestReport")
    return _json_ready(asdict(report))


def _build_row(
    observation: BaseballStartingPitcherLateSwapObservation,
    config: BaseballStartingPitcherLateSwapDigestConfig,
) -> BaseballStartingPitcherLateSwapDigestRow:
    swap_risk_status = _row_status(observation, config)
    reason_codes = _row_reason_codes(observation, config)
    return BaseballStartingPitcherLateSwapDigestRow(
        source_id=observation.source_id,
        game_id=observation.game_id,
        market_slug=observation.market_slug,
        team_id=observation.team_id,
        scheduled_starter_id=observation.scheduled_starter_id,
        current_listed_starter_id=observation.current_listed_starter_id,
        starter_status=observation.starter_status,
        minutes_until_first_pitch=observation.minutes_until_first_pitch,
        lineup_confirmation_age_minutes=observation.lineup_confirmation_age_minutes,
        scratch_probability=observation.scratch_probability,
        market_probability=observation.market_probability,
        liquidity_usd=observation.liquidity_usd,
        source_row_count=observation.source_row_count,
        observed_at=observation.observed_at,
        swap_risk_status=swap_risk_status,
        reason_codes=reason_codes,
    )


def _row_status(
    observation: BaseballStartingPitcherLateSwapObservation,
    config: BaseballStartingPitcherLateSwapDigestConfig,
) -> str:
    if observation.starter_status == "changed":
        return "blocked"
    if observation.scratch_probability >= config.blocked_scratch_probability:
        return "blocked"
    if (
        observation.starter_status == "questionable"
        and observation.minutes_until_first_pitch
        <= config.blocked_minutes_until_first_pitch
    ):
        return "blocked"
    if observation.scratch_probability >= config.watch_scratch_probability:
        return "watch"
    if (
        observation.starter_status == "questionable"
        and observation.minutes_until_first_pitch <= config.watch_minutes_until_first_pitch
    ):
        return "watch"
    if (
        observation.lineup_confirmation_age_minutes
        >= config.stale_confirmation_age_minutes
        and observation.minutes_until_first_pitch <= config.watch_minutes_until_first_pitch
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: BaseballStartingPitcherLateSwapObservation,
    config: BaseballStartingPitcherLateSwapDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.starter_status == "changed":
        reasons.append("baseball_starting_pitcher_late_swap_changed_starter")
    if observation.scratch_probability >= config.blocked_scratch_probability:
        reasons.append("baseball_starting_pitcher_late_swap_high_scratch_probability")
    elif observation.scratch_probability >= config.watch_scratch_probability:
        reasons.append("baseball_starting_pitcher_late_swap_watch_scratch_probability")
    if (
        observation.starter_status == "questionable"
        and observation.minutes_until_first_pitch <= config.watch_minutes_until_first_pitch
    ):
        reasons.append("baseball_starting_pitcher_late_swap_questionable_near_first_pitch")
    if (
        observation.lineup_confirmation_age_minutes
        >= config.stale_confirmation_age_minutes
        and observation.minutes_until_first_pitch <= config.watch_minutes_until_first_pitch
    ):
        reasons.append(
            "baseball_starting_pitcher_late_swap_stale_confirmation_near_first_pitch",
        )
    if not reasons:
        reasons.append("baseball_starting_pitcher_late_swap_clear")
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _digest_status(rows: tuple[BaseballStartingPitcherLateSwapDigestRow, ...]) -> str:
    if any(row.swap_risk_status == "blocked" for row in rows):
        return "blocked"
    if any(row.swap_risk_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    digest_status: str,
    *,
    blocked_count: Decimal,
    watch_count: Decimal,
    changed_count: Decimal,
) -> tuple[str, ...]:
    if digest_status == "pass":
        return ("baseball_starting_pitcher_late_swap_digest_clear",)
    reasons: list[str] = []
    if blocked_count > ZERO_COUNT:
        reasons.append("baseball_starting_pitcher_late_swap_blocked_risk_present")
    if changed_count > ZERO_COUNT:
        reasons.append("baseball_starting_pitcher_late_swap_changed_starter_present")
    if watch_count > ZERO_COUNT:
        reasons.append("baseball_starting_pitcher_late_swap_watch_risk_present")
    return _normalize_reason_codes("reason_codes", tuple(reasons), REPORT_REASON_CODES)


def _row_sort_key(
    row: BaseballStartingPitcherLateSwapDigestRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str, str, str, str]:
    return (
        -STATUS_WEIGHT[row.swap_risk_status],
        -row.scratch_probability,
        row.minutes_until_first_pitch,
        _reverse_datetime(row.observed_at),
        row.game_id,
        row.team_id,
        row.source_id,
        row.market_slug,
    )


def _reverse_datetime(value: datetime) -> datetime:
    return datetime.max.replace(tzinfo=UTC) - (value - datetime.min.replace(tzinfo=UTC))


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_PROBABILITY
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_PROBABILITY) / Decimal(len(values))).quantize(
            PROBABILITY_QUANTUM,
        )


def _sum_counts(values: Any) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        total += value
    return total.quantize(COUNT_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_starter_consistency(
    starter_status: str,
    scheduled_starter_id: str,
    current_listed_starter_id: str,
) -> None:
    if starter_status == "changed":
        if current_listed_starter_id == scheduled_starter_id:
            raise ValueError("changed starters must change pitcher ids")
        return
    if current_listed_starter_id != scheduled_starter_id:
        raise ValueError("unchanged statuses must keep pitcher ids aligned")


def _validate_observation_reason_codes(
    observation: BaseballStartingPitcherLateSwapObservation,
) -> None:
    expected_status_reason = {
        "confirmed": "baseball_starting_pitcher_confirmed",
        "questionable": "baseball_starting_pitcher_questionable",
        "changed": "baseball_starting_pitcher_changed",
    }[observation.starter_status]
    present_status_reasons = tuple(
        reason
        for reason in STARTER_STATUS_REASON_CODES
        if reason in observation.reason_codes
    )
    if present_status_reasons != (expected_status_reason,):
        raise ValueError("reason_codes must match starter_status")


def _validate_row(row: BaseballStartingPitcherLateSwapDigestRow) -> None:
    has_clear = "baseball_starting_pitcher_late_swap_clear" in row.reason_codes
    if row.swap_risk_status == "pass":
        if row.reason_codes != ("baseball_starting_pitcher_late_swap_clear",):
            raise ValueError("pass rows must only carry the clear reason code")
        return
    if has_clear:
        raise ValueError("non-pass rows must not carry the clear reason code")


def _validate_report(report: BaseballStartingPitcherLateSwapDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.risk_rows)):
        raise ValueError("observation_count must match risk_rows")
    if (
        report.blocked_swap_risk_count
        + report.watch_swap_risk_count
        + report.pass_swap_risk_count
        != report.observation_count
    ):
        raise ValueError("risk status counts must match observation_count")
    if report.changed_starter_count != _count_decimal(
        sum(1 for row in report.risk_rows if row.starter_status == "changed"),
    ):
        raise ValueError("changed_starter_count must match risk_rows")
    if report.source_row_count != _sum_counts(row.source_row_count for row in report.risk_rows):
        raise ValueError("source_row_count must match risk_rows")
    if report.max_scratch_probability != max(
        (row.scratch_probability for row in report.risk_rows),
        default=ZERO_PROBABILITY,
    ).quantize(PROBABILITY_QUANTUM):
        raise ValueError("max_scratch_probability must match risk_rows")
    if report.average_scratch_probability != _average_probability(
        tuple(row.scratch_probability for row in report.risk_rows),
    ):
        raise ValueError("average_scratch_probability must match risk_rows")
    if report.min_minutes_until_first_pitch != min(
        (row.minutes_until_first_pitch for row in report.risk_rows),
        default=ZERO_VALUE,
    ).quantize(VALUE_QUANTUM):
        raise ValueError("min_minutes_until_first_pitch must match risk_rows")
    if report.digest_status != _digest_status(report.risk_rows):
        raise ValueError("digest_status must match risk_rows")
    if report.reason_codes != _report_reason_codes(
        report.digest_status,
        blocked_count=report.blocked_swap_risk_count,
        watch_count=report.watch_swap_risk_count,
        changed_count=report.changed_starter_count,
    ):
        raise ValueError("reason_codes must match risk_rows")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(VALUE_QUANTUM)
    if normalized < ZERO_VALUE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized <= ZERO_VALUE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(PROBABILITY_QUANTUM)
    if normalized < ZERO_PROBABILITY or normalized > ONE_PROBABILITY:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized <= ZERO_PROBABILITY:
        raise ValueError(f"{field_name} must be positive")
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
    rows: tuple[BaseballStartingPitcherLateSwapDigestRow, ...],
) -> tuple[BaseballStartingPitcherLateSwapDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("risk_rows must be a tuple")
    seen: set[str] = set()
    normalized: list[BaseballStartingPitcherLateSwapDigestRow] = []
    for row in rows:
        if type(row) is not BaseballStartingPitcherLateSwapDigestRow:
            raise ValueError("risk_rows must contain digest rows")
        if row.source_id in seen:
            raise ValueError("risk_rows must not contain duplicate source_id values")
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
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        raise ValueError("payload contains a non-Decimal numeric value")
    return value
