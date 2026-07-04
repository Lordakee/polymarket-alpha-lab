"""Pure Phase 1 basketball starting lineup confirmation lag digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_BASKETBALL_STARTING_LINEUP_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-starting-lineup-confirmation-lag-digest-v0"
)

LINEUP_LAG_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
    "basketball_starting_lineup_confirmation_lag_close_to_tip",
    "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
    "basketball_starting_lineup_confirmation_lag_stale_injury_report",
    "basketball_starting_lineup_confirmation_lag_beat_source_disagreement",
    "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
    "basketball_starting_lineup_confirmation_lag_blocked",
    "basketball_starting_lineup_confirmation_lag_watch",
    "basketball_starting_lineup_confirmation_lag_clear",
)
REPORT_REASON_CODES = (
    "basketball_starting_lineup_confirmation_lag_blocked_present",
    "basketball_starting_lineup_confirmation_lag_watch_present",
    "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present",
    "basketball_starting_lineup_confirmation_lag_close_to_tip_present",
    "basketball_starting_lineup_confirmation_lag_starter_uncertainty_present",
    "basketball_starting_lineup_confirmation_lag_stale_injury_report_present",
    "basketball_starting_lineup_confirmation_lag_beat_disagreement_present",
    "basketball_starting_lineup_confirmation_lag_implied_minute_volatility_present",
    "basketball_starting_lineup_confirmation_lag_digest_clear",
    "basketball_starting_lineup_confirmation_lag_digest_empty",
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


__all__ = (
    "DEFAULT_BASKETBALL_STARTING_LINEUP_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "BasketballStartingLineupConfirmationLagDigestConfig",
    "BasketballStartingLineupConfirmationLagObservation",
    "BasketballStartingLineupConfirmationLagDigestRow",
    "BasketballStartingLineupConfirmationLagReasonCodeCount",
    "BasketballStartingLineupConfirmationLagDigestReport",
    "build_market_research_basketball_starting_lineup_confirmation_lag_digest",
    "market_research_basketball_starting_lineup_confirmation_lag_digest_payload",
)


@dataclass(frozen=True)
class BasketballStartingLineupConfirmationLagDigestConfig:
    config_version: str = (
        DEFAULT_BASKETBALL_STARTING_LINEUP_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION
    )
    close_to_tip_minutes: Decimal = Decimal("45.000000")
    projected_starter_uncertainty_count: Decimal = Decimal("2.000000")
    stale_injury_report_age_minutes: Decimal = Decimal("180.000000")
    beat_source_disagreement_count: Decimal = Decimal("1.000000")
    implied_minute_volatility: Decimal = Decimal("0.100000")
    watch_lag_signal_count: Decimal = Decimal("2.000000")
    blocked_lag_signal_count: Decimal = Decimal("4.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballStartingLineupConfirmationLagDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASKETBALL_STARTING_LINEUP_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "close_to_tip_minutes",
            "projected_starter_uncertainty_count",
            "stale_injury_report_age_minutes",
            "beat_source_disagreement_count",
            "watch_lag_signal_count",
            "blocked_lag_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "projected_starter_uncertainty_count",
            _require_whole_positive_decimal(
                "projected_starter_uncertainty_count",
                self.projected_starter_uncertainty_count,
            ),
        )
        object.__setattr__(
            self,
            "beat_source_disagreement_count",
            _require_whole_positive_decimal(
                "beat_source_disagreement_count",
                self.beat_source_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "implied_minute_volatility",
            _require_positive_ratio(
                "implied_minute_volatility",
                self.implied_minute_volatility,
            ),
        )
        if self.watch_lag_signal_count > self.blocked_lag_signal_count:
            raise ValueError(
                "watch_lag_signal_count must not exceed blocked_lag_signal_count",
            )
        if self.blocked_lag_signal_count > SIGNAL_DENOMINATOR:
            raise ValueError("blocked_lag_signal_count must not exceed signal count")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BasketballStartingLineupConfirmationLagObservation:
    source_id: str
    event_id: str
    team: str
    opponent: str
    market_slug: str
    minutes_to_tip: Decimal
    lineup_confirmed_flag: Decimal
    projected_starter_uncertainty_count: Decimal
    injury_report_freshness_age_minutes: Decimal
    beat_source_disagreement_count: Decimal
    implied_minute_volatility: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballStartingLineupConfirmationLagObservation,
            "observation",
        )
        for field_name in ("source_id", "event_id", "team", "opponent", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "minutes_to_tip",
            _require_nonnegative_decimal("minutes_to_tip", self.minutes_to_tip),
        )
        object.__setattr__(
            self,
            "lineup_confirmed_flag",
            _require_binary_decimal(
                "lineup_confirmed_flag",
                self.lineup_confirmed_flag,
            ),
        )
        object.__setattr__(
            self,
            "projected_starter_uncertainty_count",
            _require_whole_nonnegative_decimal(
                "projected_starter_uncertainty_count",
                self.projected_starter_uncertainty_count,
            ),
        )
        object.__setattr__(
            self,
            "injury_report_freshness_age_minutes",
            _require_nonnegative_decimal(
                "injury_report_freshness_age_minutes",
                self.injury_report_freshness_age_minutes,
            ),
        )
        object.__setattr__(
            self,
            "beat_source_disagreement_count",
            _require_whole_nonnegative_decimal(
                "beat_source_disagreement_count",
                self.beat_source_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "implied_minute_volatility",
            _require_ratio(
                "implied_minute_volatility",
                self.implied_minute_volatility,
            ),
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
class BasketballStartingLineupConfirmationLagDigestRow:
    source_id: str
    event_id: str
    team: str
    opponent: str
    market_slug: str
    minutes_to_tip: Decimal
    lineup_confirmed_flag: Decimal
    projected_starter_uncertainty_count: Decimal
    injury_report_freshness_age_minutes: Decimal
    beat_source_disagreement_count: Decimal
    implied_minute_volatility: Decimal
    lineup_lag_signal_count: Decimal
    lineup_lag_risk_score: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    lineup_lag_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballStartingLineupConfirmationLagDigestRow,
            "row",
        )
        for field_name in ("source_id", "event_id", "team", "opponent", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "minutes_to_tip",
            "injury_report_freshness_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lineup_confirmed_flag",
            _require_binary_decimal(
                "lineup_confirmed_flag",
                self.lineup_confirmed_flag,
            ),
        )
        for field_name in (
            "projected_starter_uncertainty_count",
            "beat_source_disagreement_count",
            "lineup_lag_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("implied_minute_volatility", "lineup_lag_risk_score"):
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
        _require_member("lineup_lag_status", self.lineup_lag_status, LINEUP_LAG_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BasketballStartingLineupConfirmationLagReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballStartingLineupConfirmationLagReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class BasketballStartingLineupConfirmationLagDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    unconfirmed_lineup_count: Decimal
    close_to_tip_count: Decimal
    starter_uncertainty_count: Decimal
    stale_injury_report_count: Decimal
    beat_disagreement_count: Decimal
    implied_minute_volatility_count: Decimal
    max_lineup_lag_risk_score: Decimal
    average_lineup_lag_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...]
    reason_code_counts: tuple[BasketballStartingLineupConfirmationLagReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballStartingLineupConfirmationLagDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASKETBALL_STARTING_LINEUP_CONFIRMATION_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "unconfirmed_lineup_count",
            "close_to_tip_count",
            "starter_uncertainty_count",
            "stale_injury_report_count",
            "beat_disagreement_count",
            "implied_minute_volatility_count",
            "max_lineup_lag_risk_score",
            "average_lineup_lag_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("max_lineup_lag_risk_score", self.max_lineup_lag_risk_score)
        _require_ratio(
            "average_lineup_lag_risk_score",
            self.average_lineup_lag_risk_score,
        )
        _require_member("digest_status", self.digest_status, LINEUP_LAG_STATUSES)
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_basketball_starting_lineup_confirmation_lag_digest(
    observations: Iterable[BasketballStartingLineupConfirmationLagObservation],
    *,
    config: BasketballStartingLineupConfirmationLagDigestConfig,
    generated_at: datetime,
) -> BasketballStartingLineupConfirmationLagDigestReport:
    if type(config) is not BasketballStartingLineupConfirmationLagDigestConfig:
        raise ValueError(
            "config must be exactly BasketballStartingLineupConfirmationLagDigestConfig",
        )
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

    return BasketballStartingLineupConfirmationLagDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        unconfirmed_lineup_count=_reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        ),
        close_to_tip_count=_reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_close_to_tip",
        ),
        starter_uncertainty_count=_reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
        ),
        stale_injury_report_count=_reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_stale_injury_report",
        ),
        beat_disagreement_count=_reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_beat_source_disagreement",
        ),
        implied_minute_volatility_count=_reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
        ),
        max_lineup_lag_risk_score=_max_row_decimal(rows, "lineup_lag_risk_score"),
        average_lineup_lag_risk_score=_ratio(
            _sum_decimal(row.lineup_lag_risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_basketball_starting_lineup_confirmation_lag_digest_payload(
    report: BasketballStartingLineupConfirmationLagDigestReport,
) -> dict[str, Any]:
    if type(report) is not BasketballStartingLineupConfirmationLagDigestReport:
        raise ValueError(
            "report must be exactly BasketballStartingLineupConfirmationLagDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    observation: BasketballStartingLineupConfirmationLagObservation,
    *,
    config: BasketballStartingLineupConfirmationLagDigestConfig,
) -> BasketballStartingLineupConfirmationLagDigestRow:
    reason_codes = _signal_reason_codes(observation, config=config)
    signal_count = _count_decimal(len(reason_codes))
    lineup_lag_status = _lineup_lag_status(signal_count, config=config)
    row_reason_codes = _row_reason_codes(reason_codes, lineup_lag_status)
    return BasketballStartingLineupConfirmationLagDigestRow(
        source_id=observation.source_id,
        event_id=observation.event_id,
        team=observation.team,
        opponent=observation.opponent,
        market_slug=observation.market_slug,
        minutes_to_tip=observation.minutes_to_tip,
        lineup_confirmed_flag=observation.lineup_confirmed_flag,
        projected_starter_uncertainty_count=(
            observation.projected_starter_uncertainty_count
        ),
        injury_report_freshness_age_minutes=(
            observation.injury_report_freshness_age_minutes
        ),
        beat_source_disagreement_count=observation.beat_source_disagreement_count,
        implied_minute_volatility=observation.implied_minute_volatility,
        lineup_lag_signal_count=signal_count,
        lineup_lag_risk_score=_ratio(signal_count, SIGNAL_DENOMINATOR),
        observed_at=observation.observed_at,
        upstream_reason_codes=observation.upstream_reason_codes,
        lineup_lag_status=lineup_lag_status,
        reason_codes=row_reason_codes,
    )


def _signal_reason_codes(
    observation: BasketballStartingLineupConfirmationLagObservation,
    *,
    config: BasketballStartingLineupConfirmationLagDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.lineup_confirmed_flag == ZERO:
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        )
        if observation.minutes_to_tip <= config.close_to_tip_minutes:
            reason_codes.append(
                "basketball_starting_lineup_confirmation_lag_close_to_tip",
            )
    if (
        observation.projected_starter_uncertainty_count
        >= config.projected_starter_uncertainty_count
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
        )
    if (
        observation.injury_report_freshness_age_minutes
        >= config.stale_injury_report_age_minutes
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_stale_injury_report",
        )
    if observation.beat_source_disagreement_count >= config.beat_source_disagreement_count:
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_beat_source_disagreement",
        )
    if observation.implied_minute_volatility >= config.implied_minute_volatility:
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
        )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_reason_codes(
    signal_reason_codes: tuple[str, ...],
    lineup_lag_status: str,
) -> tuple[str, ...]:
    reason_codes = list(signal_reason_codes)
    if lineup_lag_status == "blocked":
        reason_codes.append("basketball_starting_lineup_confirmation_lag_blocked")
    elif lineup_lag_status == "watch":
        reason_codes.append("basketball_starting_lineup_confirmation_lag_watch")
    else:
        reason_codes.append("basketball_starting_lineup_confirmation_lag_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _lineup_lag_status(
    signal_count: Decimal,
    *,
    config: BasketballStartingLineupConfirmationLagDigestConfig,
) -> str:
    if signal_count >= config.blocked_lag_signal_count:
        return "blocked"
    if signal_count >= config.watch_lag_signal_count:
        return "watch"
    return "pass"


def _digest_status(
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.lineup_lag_status == "blocked" for row in rows):
        return "blocked"
    if any(row.lineup_lag_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_basketball_starting_lineup_confirmation_lag_screening"
    if status == "watch":
        return "monitor_report_only_basketball_starting_lineup_confirmation_lag_screening"
    return "block_report_only_basketball_starting_lineup_confirmation_lag_screening"


def _report_reason_codes(
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("basketball_starting_lineup_confirmation_lag_digest_empty",)
    reason_codes: list[str] = []
    if any(row.lineup_lag_status == "blocked" for row in rows):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_blocked_present",
        )
    if not any(row.lineup_lag_status == "blocked" for row in rows) and any(
        row.lineup_lag_status == "watch" for row in rows
    ):
        reason_codes.append("basketball_starting_lineup_confirmation_lag_watch_present")
    if (
        _reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        )
        > ZERO
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present",
        )
    if (
        _reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_close_to_tip",
        )
        > ZERO
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_close_to_tip_present",
        )
    if (
        _reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
        )
        > ZERO
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_starter_uncertainty_present",
        )
    if (
        _reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_stale_injury_report",
        )
        > ZERO
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_stale_injury_report_present",
        )
    if (
        _reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_beat_source_disagreement",
        )
        > ZERO
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_beat_disagreement_present",
        )
    if (
        _reason_count(
            rows,
            "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
        )
        > ZERO
    ):
        reason_codes.append(
            "basketball_starting_lineup_confirmation_lag_implied_minute_volatility_present",
        )
    if not reason_codes:
        reason_codes.append("basketball_starting_lineup_confirmation_lag_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
) -> tuple[BasketballStartingLineupConfirmationLagReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("basketball_starting_lineup_confirmation_lag_digest_empty",):
        return (
            BasketballStartingLineupConfirmationLagReasonCodeCount(
                reason_code="basketball_starting_lineup_confirmation_lag_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        BasketballStartingLineupConfirmationLagReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "basketball_starting_lineup_confirmation_lag_blocked_present": (
            "basketball_starting_lineup_confirmation_lag_blocked"
        ),
        "basketball_starting_lineup_confirmation_lag_watch_present": (
            "basketball_starting_lineup_confirmation_lag_watch"
        ),
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present": (
            "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup"
        ),
        "basketball_starting_lineup_confirmation_lag_close_to_tip_present": (
            "basketball_starting_lineup_confirmation_lag_close_to_tip"
        ),
        "basketball_starting_lineup_confirmation_lag_starter_uncertainty_present": (
            "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty"
        ),
        "basketball_starting_lineup_confirmation_lag_stale_injury_report_present": (
            "basketball_starting_lineup_confirmation_lag_stale_injury_report"
        ),
        "basketball_starting_lineup_confirmation_lag_beat_disagreement_present": (
            "basketball_starting_lineup_confirmation_lag_beat_source_disagreement"
        ),
        "basketball_starting_lineup_confirmation_lag_implied_minute_volatility_present": (
            "basketball_starting_lineup_confirmation_lag_implied_minute_volatility"
        ),
        "basketball_starting_lineup_confirmation_lag_digest_clear": (
            "basketball_starting_lineup_confirmation_lag_clear"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _validate_row(row: BasketballStartingLineupConfirmationLagDigestRow) -> None:
    if row.lineup_lag_status == "pass":
        if "basketball_starting_lineup_confirmation_lag_clear" not in row.reason_codes:
            raise ValueError("reason_codes must match lineup_lag_status")
        if (
            "basketball_starting_lineup_confirmation_lag_watch" in row.reason_codes
            or "basketball_starting_lineup_confirmation_lag_blocked" in row.reason_codes
        ):
            raise ValueError("reason_codes must match lineup_lag_status")
    if row.lineup_lag_status == "watch":
        if "basketball_starting_lineup_confirmation_lag_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match lineup_lag_status")
        if (
            "basketball_starting_lineup_confirmation_lag_clear" in row.reason_codes
            or "basketball_starting_lineup_confirmation_lag_blocked" in row.reason_codes
        ):
            raise ValueError("reason_codes must match lineup_lag_status")
    if row.lineup_lag_status == "blocked":
        if "basketball_starting_lineup_confirmation_lag_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match lineup_lag_status")
        if (
            "basketball_starting_lineup_confirmation_lag_clear" in row.reason_codes
            or "basketball_starting_lineup_confirmation_lag_watch" in row.reason_codes
        ):
            raise ValueError("reason_codes must match lineup_lag_status")
    signal_count = _count_decimal(
        sum(
            1
            for reason_code in ROW_REASON_CODES[:6]
            if reason_code in row.reason_codes
        ),
    )
    if row.lineup_lag_signal_count != signal_count:
        raise ValueError("lineup_lag_signal_count must match reason_codes")
    if row.lineup_lag_risk_score != _ratio(row.lineup_lag_signal_count, SIGNAL_DENOMINATOR):
        raise ValueError("lineup_lag_risk_score must match lineup_lag_signal_count")


def _validate_report(report: BasketballStartingLineupConfirmationLagDigestReport) -> None:
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
        (
            "unconfirmed_lineup_count",
            "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        ),
        (
            "close_to_tip_count",
            "basketball_starting_lineup_confirmation_lag_close_to_tip",
        ),
        (
            "starter_uncertainty_count",
            "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
        ),
        (
            "stale_injury_report_count",
            "basketball_starting_lineup_confirmation_lag_stale_injury_report",
        ),
        (
            "beat_disagreement_count",
            "basketball_starting_lineup_confirmation_lag_beat_source_disagreement",
        ),
        (
            "implied_minute_volatility_count",
            "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
        ),
    )
    for field_name, reason_code in reason_count_pairs:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_lineup_lag_risk_score != _max_row_decimal(
        report.rows,
        "lineup_lag_risk_score",
    ):
        raise ValueError("max_lineup_lag_risk_score must match rows")
    if report.average_lineup_lag_risk_score != _ratio(
        _sum_decimal(row.lineup_lag_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_lineup_lag_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[BasketballStartingLineupConfirmationLagObservation],
) -> tuple[BasketballStartingLineupConfirmationLagObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain BasketballStartingLineupConfirmationLagObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not BasketballStartingLineupConfirmationLagObservation:
            raise ValueError(
                "observations must contain BasketballStartingLineupConfirmationLagObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[BasketballStartingLineupConfirmationLagDigestRow],
) -> tuple[BasketballStartingLineupConfirmationLagDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain BasketballStartingLineupConfirmationLagDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not BasketballStartingLineupConfirmationLagDigestRow:
            raise ValueError("rows must contain BasketballStartingLineupConfirmationLagDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[BasketballStartingLineupConfirmationLagReasonCodeCount],
) -> tuple[BasketballStartingLineupConfirmationLagReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    seen_reason_codes: set[str] = set()
    for value in normalized:
        if type(value) is not BasketballStartingLineupConfirmationLagReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "BasketballStartingLineupConfirmationLagReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        seen_reason_codes.add(value.reason_code)
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
        _require_canonical_string("reason_code", value)
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
    row: BasketballStartingLineupConfirmationLagDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.lineup_lag_status],
        -row.lineup_lag_risk_score,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.lineup_lag_status == status))


def _reason_count(
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[BasketballStartingLineupConfirmationLagDigestRow, ...],
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


def _require_whole_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_binary_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be zero or one")
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
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
