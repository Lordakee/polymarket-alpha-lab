"""Pure Phase 1 hockey goalie confirmation lag digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_HOCKEY_GOALIE_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION = (
    "market-research-hockey-goalie-confirmation-lag-digest-v0"
)

CONFIRMATION_STATES = ("confirmed", "projected", "unconfirmed")
LAG_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "goalie_confirmed",
    "goalie_projected",
    "goalie_unconfirmed",
)
ROW_REASON_CODES = (
    "goalie_confirmation_lag_blocked",
    "goalie_confirmation_lag_watch",
    "projected_goalie_confirmation_blocked",
    "projected_goalie_confirmation_watch",
    "unconfirmed_goalie_confirmation_blocked",
    "unconfirmed_goalie_confirmation_watch",
    "thin_goalie_confirmation_source_watch",
    "goalie_confirmation_lag_clear",
)
REPORT_REASON_CODES = (
    "goalie_confirmation_lag_digest_blocked",
    "goalie_confirmation_lag_digest_watch",
    "goalie_confirmation_lag_digest_clear",
    "goalie_confirmation_lag_digest_empty",
    "goalie_confirmation_close_to_start_present",
    "goalie_confirmation_stale_present",
    "goalie_confirmation_low_source_present",
)
COUNT_REASON_CODES = ROW_REASON_CODES + ("goalie_confirmation_lag_digest_empty",)

VALUE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
DEFAULT_WATCH_UNCONFIRMED_WINDOW_SECONDS = Decimal("86400.000000")
DEFAULT_BLOCKED_UNCONFIRMED_WINDOW_SECONDS = Decimal("7200.000000")
DEFAULT_WATCH_CONFIRMATION_LAG_SECONDS = Decimal("21600.000000")
DEFAULT_BLOCKED_CONFIRMATION_LAG_SECONDS = Decimal("43200.000000")
DEFAULT_MIN_CONFIRMED_SOURCE_COUNT = Decimal("2")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_DAY = 86400
MICROSECONDS_PER_SECOND = 1000000
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
REASON_RISK_SCORE = {
    "goalie_confirmation_lag_blocked": Decimal("4.000000"),
    "goalie_confirmation_lag_watch": Decimal("2.000000"),
    "projected_goalie_confirmation_blocked": Decimal("4.000000"),
    "projected_goalie_confirmation_watch": Decimal("2.000000"),
    "unconfirmed_goalie_confirmation_blocked": Decimal("4.000000"),
    "unconfirmed_goalie_confirmation_watch": Decimal("2.000000"),
    "thin_goalie_confirmation_source_watch": Decimal("1.000000"),
    "goalie_confirmation_lag_clear": ZERO,
}
BLOCKED_ROW_REASON_CODES = (
    "goalie_confirmation_lag_blocked",
    "projected_goalie_confirmation_blocked",
    "unconfirmed_goalie_confirmation_blocked",
)
WATCH_ROW_REASON_CODES = (
    "goalie_confirmation_lag_watch",
    "projected_goalie_confirmation_watch",
    "unconfirmed_goalie_confirmation_watch",
    "thin_goalie_confirmation_source_watch",
)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_HOCKEY_GOALIE_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION",
    "HockeyGoalieConfirmationLagDigestConfig",
    "HockeyGoalieConfirmationLagObservation",
    "HockeyGoalieConfirmationLagDigestRow",
    "HockeyGoalieConfirmationLagReasonCodeCount",
    "HockeyGoalieConfirmationLagDigestReport",
    "build_market_research_hockey_goalie_confirmation_lag_digest",
    "market_research_hockey_goalie_confirmation_lag_digest_payload",
)


@dataclass(frozen=True)
class HockeyGoalieConfirmationLagDigestConfig:
    config_version: str = DEFAULT_HOCKEY_GOALIE_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION
    watch_unconfirmed_window_seconds: Decimal = DEFAULT_WATCH_UNCONFIRMED_WINDOW_SECONDS
    blocked_unconfirmed_window_seconds: Decimal = DEFAULT_BLOCKED_UNCONFIRMED_WINDOW_SECONDS
    watch_confirmation_lag_seconds: Decimal = DEFAULT_WATCH_CONFIRMATION_LAG_SECONDS
    blocked_confirmation_lag_seconds: Decimal = DEFAULT_BLOCKED_CONFIRMATION_LAG_SECONDS
    min_confirmed_source_count: Decimal = DEFAULT_MIN_CONFIRMED_SOURCE_COUNT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not HockeyGoalieConfirmationLagDigestConfig:
            raise TypeError(
                "HockeyGoalieConfirmationLagDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not HockeyGoalieConfirmationLagDigestConfig:
            raise ValueError(
                "config must be exactly HockeyGoalieConfirmationLagDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_HOCKEY_GOALIE_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_unconfirmed_window_seconds",
            "blocked_unconfirmed_window_seconds",
            "watch_confirmation_lag_seconds",
            "blocked_confirmation_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confirmed_source_count",
            _require_positive_count(
                "min_confirmed_source_count",
                self.min_confirmed_source_count,
            ),
        )
        if (
            self.blocked_unconfirmed_window_seconds
            > self.watch_unconfirmed_window_seconds
        ):
            raise ValueError(
                "blocked_unconfirmed_window_seconds must be at most watch threshold",
            )
        if self.watch_confirmation_lag_seconds > self.blocked_confirmation_lag_seconds:
            raise ValueError(
                "watch_confirmation_lag_seconds must be at most blocked threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class HockeyGoalieConfirmationLagObservation:
    source_id: str
    event_id: str
    market_slug: str
    team_id: str
    scheduled_start_at: datetime
    confirmation_updated_at: datetime
    confirmation_state: str
    source_count: Decimal
    source_row_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not HockeyGoalieConfirmationLagObservation:
            raise TypeError(
                "HockeyGoalieConfirmationLagObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not HockeyGoalieConfirmationLagObservation:
            raise ValueError(
                "observation must be exactly HockeyGoalieConfirmationLagObservation",
            )
        for field_name in ("source_id", "event_id", "market_slug", "team_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(
            self,
            "confirmation_updated_at",
            _as_utc("confirmation_updated_at", self.confirmation_updated_at),
        )
        _require_member("confirmation_state", self.confirmation_state, CONFIRMATION_STATES)
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class HockeyGoalieConfirmationLagDigestRow:
    source_id: str
    event_id: str
    market_slug: str
    team_id: str
    scheduled_start_at: datetime
    confirmation_updated_at: datetime
    confirmation_state: str
    source_count: Decimal
    source_row_count: Decimal
    seconds_to_start: Decimal
    confirmation_lag_seconds: Decimal
    lag_status: str
    risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not HockeyGoalieConfirmationLagDigestRow:
            raise TypeError(
                "HockeyGoalieConfirmationLagDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not HockeyGoalieConfirmationLagDigestRow:
            raise ValueError("row must be exactly HockeyGoalieConfirmationLagDigestRow")
        for field_name in ("source_id", "event_id", "market_slug", "team_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(
            self,
            "confirmation_updated_at",
            _as_utc("confirmation_updated_at", self.confirmation_updated_at),
        )
        _require_member("confirmation_state", self.confirmation_state, CONFIRMATION_STATES)
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "seconds_to_start",
            _require_nonnegative_decimal("seconds_to_start", self.seconds_to_start),
        )
        object.__setattr__(
            self,
            "confirmation_lag_seconds",
            _require_nonnegative_decimal(
                "confirmation_lag_seconds",
                self.confirmation_lag_seconds,
            ),
        )
        _require_member("lag_status", self.lag_status, LAG_STATUSES)
        object.__setattr__(
            self,
            "risk_score",
            _require_nonnegative_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class HockeyGoalieConfirmationLagReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not HockeyGoalieConfirmationLagReasonCodeCount:
            raise TypeError(
                "HockeyGoalieConfirmationLagReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not HockeyGoalieConfirmationLagReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly HockeyGoalieConfirmationLagReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, COUNT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class HockeyGoalieConfirmationLagDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    confirmed_count: Decimal
    projected_count: Decimal
    unconfirmed_count: Decimal
    close_to_start_count: Decimal
    stale_confirmation_count: Decimal
    low_source_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_confirmation_lag_seconds: Decimal
    max_risk_score: Decimal
    risk_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    goalie_rows: tuple[HockeyGoalieConfirmationLagDigestRow, ...]
    reason_code_counts: tuple[HockeyGoalieConfirmationLagReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not HockeyGoalieConfirmationLagDigestReport:
            raise TypeError(
                "HockeyGoalieConfirmationLagDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not HockeyGoalieConfirmationLagDigestReport:
            raise ValueError("report must be exactly HockeyGoalieConfirmationLagDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_HOCKEY_GOALIE_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "observation_count",
            "confirmed_count",
            "projected_count",
            "unconfirmed_count",
            "close_to_start_count",
            "stale_confirmation_count",
            "low_source_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_confirmation_lag_seconds",
            "max_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "risk_ratio", _require_ratio("risk_ratio", self.risk_ratio))
        _require_member("digest_status", self.digest_status, LAG_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "goalie_rows", _normalize_rows(self.goalie_rows))
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


def build_market_research_hockey_goalie_confirmation_lag_digest(
    inputs: Iterable[HockeyGoalieConfirmationLagObservation],
    *,
    config: HockeyGoalieConfirmationLagDigestConfig,
    generated_at: datetime,
) -> HockeyGoalieConfirmationLagDigestReport:
    if type(config) is not HockeyGoalieConfirmationLagDigestConfig:
        raise ValueError("config must be exactly HockeyGoalieConfirmationLagDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_inputs(inputs)
    rows = tuple(
        _row_for_observation(
            observation,
            config=config,
            generated_at=generated_at_utc,
        )
        for observation in observations
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(sorted_rows))
    blocked_count = _count_decimal(
        sum(1 for row in sorted_rows if row.lag_status == "blocked"),
    )
    watch_count = _count_decimal(
        sum(1 for row in sorted_rows if row.lag_status == "watch"),
    )
    reason_codes = _report_reason_codes(sorted_rows)

    return HockeyGoalieConfirmationLagDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_sum_count(row.source_row_count for row in sorted_rows),
        observation_count=observation_count,
        confirmed_count=_count_decimal(
            sum(1 for row in sorted_rows if row.confirmation_state == "confirmed"),
        ),
        projected_count=_count_decimal(
            sum(1 for row in sorted_rows if row.confirmation_state == "projected"),
        ),
        unconfirmed_count=_count_decimal(
            sum(1 for row in sorted_rows if row.confirmation_state == "unconfirmed"),
        ),
        close_to_start_count=_count_decimal(
            sum(1 for row in sorted_rows if _has_close_to_start_reason(row)),
        ),
        stale_confirmation_count=_count_decimal(
            sum(1 for row in sorted_rows if _has_stale_reason(row)),
        ),
        low_source_count=_count_decimal(
            sum(
                1
                for row in sorted_rows
                if "thin_goalie_confirmation_source_watch" in row.reason_codes
            ),
        ),
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_confirmation_lag_seconds=max(
            (row.confirmation_lag_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_risk_score=max((row.risk_score for row in sorted_rows), default=ZERO),
        risk_ratio=_ratio(watch_count + blocked_count, observation_count),
        digest_status=_digest_status(sorted_rows),
        recommended_next_step=_recommended_next_step(_digest_status(sorted_rows)),
        goalie_rows=sorted_rows,
        reason_code_counts=_reason_code_counts(sorted_rows, observation_count),
        reason_codes=reason_codes,
    )


def market_research_hockey_goalie_confirmation_lag_digest_payload(
    report: HockeyGoalieConfirmationLagDigestReport,
) -> dict[str, Any]:
    if type(report) is not HockeyGoalieConfirmationLagDigestReport:
        raise ValueError("report must be exactly HockeyGoalieConfirmationLagDigestReport")
    return _json_ready(asdict(report))


def _row_for_observation(
    observation: HockeyGoalieConfirmationLagObservation,
    *,
    config: HockeyGoalieConfirmationLagDigestConfig,
    generated_at: datetime,
) -> HockeyGoalieConfirmationLagDigestRow:
    if observation.confirmation_updated_at > generated_at:
        raise ValueError("confirmation_updated_at must not be after generated_at")
    seconds_to_start = _max_zero(_seconds_between(observation.scheduled_start_at, generated_at))
    confirmation_lag_seconds = _seconds_between(
        generated_at,
        observation.confirmation_updated_at,
    )
    reason_codes = _row_reason_codes(
        confirmation_state=observation.confirmation_state,
        seconds_to_start=seconds_to_start,
        confirmation_lag_seconds=confirmation_lag_seconds,
        source_count=observation.source_count,
        config=config,
    )
    return HockeyGoalieConfirmationLagDigestRow(
        source_id=observation.source_id,
        event_id=observation.event_id,
        market_slug=observation.market_slug,
        team_id=observation.team_id,
        scheduled_start_at=observation.scheduled_start_at,
        confirmation_updated_at=observation.confirmation_updated_at,
        confirmation_state=observation.confirmation_state,
        source_count=observation.source_count,
        source_row_count=observation.source_row_count,
        seconds_to_start=seconds_to_start,
        confirmation_lag_seconds=confirmation_lag_seconds,
        lag_status=_status_for_reason_codes(reason_codes),
        risk_score=_risk_score(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    confirmation_state: str,
    seconds_to_start: Decimal,
    confirmation_lag_seconds: Decimal,
    source_count: Decimal,
    config: HockeyGoalieConfirmationLagDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if confirmation_lag_seconds >= config.blocked_confirmation_lag_seconds:
        reasons.append("goalie_confirmation_lag_blocked")
    elif confirmation_lag_seconds >= config.watch_confirmation_lag_seconds:
        reasons.append("goalie_confirmation_lag_watch")

    if confirmation_state == "projected":
        if seconds_to_start <= config.blocked_unconfirmed_window_seconds:
            reasons.append("projected_goalie_confirmation_blocked")
        elif seconds_to_start <= config.watch_unconfirmed_window_seconds:
            reasons.append("projected_goalie_confirmation_watch")
    if confirmation_state == "unconfirmed":
        if seconds_to_start <= config.blocked_unconfirmed_window_seconds:
            reasons.append("unconfirmed_goalie_confirmation_blocked")
        elif seconds_to_start <= config.watch_unconfirmed_window_seconds:
            reasons.append("unconfirmed_goalie_confirmation_watch")
    if (
        confirmation_state == "confirmed"
        and source_count < config.min_confirmed_source_count
    ):
        reasons.append("thin_goalie_confirmation_source_watch")
    if not reasons:
        reasons.append("goalie_confirmation_lag_clear")
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[HockeyGoalieConfirmationLagDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("goalie_confirmation_lag_digest_empty",)
    status = _digest_status(rows)
    reasons: list[str] = []
    if status == "blocked":
        reasons.append("goalie_confirmation_lag_digest_blocked")
    elif status == "watch":
        reasons.append("goalie_confirmation_lag_digest_watch")
    else:
        reasons.append("goalie_confirmation_lag_digest_clear")
    if any(_has_close_to_start_reason(row) for row in rows):
        reasons.append("goalie_confirmation_close_to_start_present")
    if any(_has_stale_reason(row) for row in rows):
        reasons.append("goalie_confirmation_stale_present")
    if any("thin_goalie_confirmation_source_watch" in row.reason_codes for row in rows):
        reasons.append("goalie_confirmation_low_source_present")
    return _normalize_reason_codes("reason_codes", tuple(reasons), REPORT_REASON_CODES)


def _reason_code_counts(
    rows: tuple[HockeyGoalieConfirmationLagDigestRow, ...],
    observation_count: Decimal,
) -> tuple[HockeyGoalieConfirmationLagReasonCodeCount, ...]:
    if not rows:
        return (
            HockeyGoalieConfirmationLagReasonCodeCount(
                reason_code="goalie_confirmation_lag_digest_empty",
                count=ONE_COUNT,
                observation_ratio=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO_COUNT) + ONE_COUNT
    return tuple(
        HockeyGoalieConfirmationLagReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            observation_ratio=_ratio(counts[reason_code], observation_count),
        )
        for reason_code in COUNT_REASON_CODES
        if reason_code in counts
    )


def _digest_status(rows: tuple[HockeyGoalieConfirmationLagDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.lag_status == "blocked" for row in rows):
        return "blocked"
    if any(row.lag_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_hockey_goalie_confirmation_lag_digest"
    if status == "watch":
        return "monitor_report_only_market_research_hockey_goalie_confirmation_lag_digest"
    return "block_report_only_market_research_hockey_goalie_confirmation_lag_digest"


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_ROW_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_ROW_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _risk_score(reason_codes: tuple[str, ...]) -> Decimal:
    total = ZERO
    for reason_code in reason_codes:
        total += REASON_RISK_SCORE[reason_code]
    return _quantize(total)


def _has_close_to_start_reason(row: HockeyGoalieConfirmationLagDigestRow) -> bool:
    return any(
        reason_code
        in (
            "projected_goalie_confirmation_blocked",
            "projected_goalie_confirmation_watch",
            "unconfirmed_goalie_confirmation_blocked",
            "unconfirmed_goalie_confirmation_watch",
        )
        for reason_code in row.reason_codes
    )


def _has_stale_reason(row: HockeyGoalieConfirmationLagDigestRow) -> bool:
    return any(
        reason_code
        in (
            "goalie_confirmation_lag_blocked",
            "goalie_confirmation_lag_watch",
        )
        for reason_code in row.reason_codes
    )


def _validate_observation(observation: HockeyGoalieConfirmationLagObservation) -> None:
    expected_reason_codes = {
        "confirmed": ("goalie_confirmed",),
        "projected": ("goalie_projected",),
        "unconfirmed": ("goalie_unconfirmed",),
    }[observation.confirmation_state]
    if observation.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match confirmation_state")


def _validate_row(row: HockeyGoalieConfirmationLagDigestRow) -> None:
    if row.lag_status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("lag_status must match reason_codes")
    if row.risk_score != _risk_score(row.reason_codes):
        raise ValueError("risk_score must match reason_codes")
    if row.lag_status == "pass" and row.reason_codes != ("goalie_confirmation_lag_clear",):
        raise ValueError("pass rows must use clear reason_codes")
    if (
        row.confirmation_state == "confirmed"
        and any("projected_goalie" in reason_code for reason_code in row.reason_codes)
    ):
        raise ValueError("reason_codes must match confirmation_state")
    if (
        row.confirmation_state == "confirmed"
        and any("unconfirmed_goalie" in reason_code for reason_code in row.reason_codes)
    ):
        raise ValueError("reason_codes must match confirmation_state")
    if (
        row.confirmation_state == "projected"
        and any("unconfirmed_goalie" in reason_code for reason_code in row.reason_codes)
    ):
        raise ValueError("reason_codes must match confirmation_state")
    if (
        row.confirmation_state == "unconfirmed"
        and any("projected_goalie" in reason_code for reason_code in row.reason_codes)
    ):
        raise ValueError("reason_codes must match confirmation_state")


def _validate_report(report: HockeyGoalieConfirmationLagDigestReport) -> None:
    rows = report.goalie_rows
    if report.source_row_count != _sum_count(row.source_row_count for row in rows):
        raise ValueError("source_row_count must match goalie_rows")
    if report.observation_count != _count_decimal(len(rows)):
        raise ValueError("observation_count must match goalie_rows")
    if report.confirmed_count != _count_decimal(
        sum(1 for row in rows if row.confirmation_state == "confirmed"),
    ):
        raise ValueError("confirmed_count must match goalie_rows")
    if report.projected_count != _count_decimal(
        sum(1 for row in rows if row.confirmation_state == "projected"),
    ):
        raise ValueError("projected_count must match goalie_rows")
    if report.unconfirmed_count != _count_decimal(
        sum(1 for row in rows if row.confirmation_state == "unconfirmed"),
    ):
        raise ValueError("unconfirmed_count must match goalie_rows")
    if report.close_to_start_count != _count_decimal(
        sum(1 for row in rows if _has_close_to_start_reason(row)),
    ):
        raise ValueError("close_to_start_count must match goalie_rows")
    if report.stale_confirmation_count != _count_decimal(
        sum(1 for row in rows if _has_stale_reason(row)),
    ):
        raise ValueError("stale_confirmation_count must match goalie_rows")
    if report.low_source_count != _count_decimal(
        sum(1 for row in rows if "thin_goalie_confirmation_source_watch" in row.reason_codes),
    ):
        raise ValueError("low_source_count must match goalie_rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in rows if row.lag_status == "watch"),
    ):
        raise ValueError("watch_count must match goalie_rows")
    if report.blocked_count != _count_decimal(
        sum(1 for row in rows if row.lag_status == "blocked"),
    ):
        raise ValueError("blocked_count must match goalie_rows")
    if report.max_confirmation_lag_seconds != max(
        (row.confirmation_lag_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_confirmation_lag_seconds must match goalie_rows")
    if report.max_risk_score != max((row.risk_score for row in rows), default=ZERO):
        raise ValueError("max_risk_score must match goalie_rows")
    if report.risk_ratio != _ratio(report.watch_count + report.blocked_count, report.observation_count):
        raise ValueError("risk_ratio must match goalie_rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match goalie_rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match goalie_rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.observation_count):
        raise ValueError("reason_code_counts must match goalie_rows")


def _normalize_inputs(
    inputs: Iterable[HockeyGoalieConfirmationLagObservation],
) -> tuple[HockeyGoalieConfirmationLagObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain hockey goalie confirmation observations")
    try:
        observations = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must contain hockey goalie confirmation observations",
        ) from exc
    seen: set[str] = set()
    for observation in observations:
        if type(observation) is not HockeyGoalieConfirmationLagObservation:
            raise ValueError(
                "inputs must contain HockeyGoalieConfirmationLagObservation",
            )
        if observation.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen.add(observation.source_id)
    return observations


def _normalize_rows(value: object) -> tuple[HockeyGoalieConfirmationLagDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("goalie_rows must contain hockey goalie confirmation rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("goalie_rows must contain hockey goalie confirmation rows") from exc
    for row in rows:
        if type(row) is not HockeyGoalieConfirmationLagDigestRow:
            raise ValueError("goalie_rows must contain HockeyGoalieConfirmationLagDigestRow")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("goalie_rows must be sorted deterministically")
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("goalie_rows must not contain duplicate source_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[HockeyGoalieConfirmationLagReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not HockeyGoalieConfirmationLagReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain HockeyGoalieConfirmationLagReasonCodeCount",
            )
    if counts != tuple(
        sorted(counts, key=lambda item: COUNT_REASON_CODES.index(item.reason_code))
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
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(row: HockeyGoalieConfirmationLagDigestRow) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.lag_status],
        -row.risk_score,
        row.seconds_to_start,
        row.market_slug,
        row.source_id,
    )


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


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        ((delta.days * SECONDS_PER_DAY) + delta.seconds) * MICROSECONDS_PER_SECOND
    ) + delta.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(total_microseconds) / Decimal(MICROSECONDS_PER_SECOND))


def _max_zero(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_count(values: Iterable[Decimal]) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return total.quantize(COUNT_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


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


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > Decimal("1.000000"):
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


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(COUNT_QUANT)


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
