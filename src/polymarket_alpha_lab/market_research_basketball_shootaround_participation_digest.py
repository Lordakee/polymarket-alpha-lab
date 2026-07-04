"""Pure Phase 1 basketball shootaround participation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_BASKETBALL_SHOOTAROUND_PARTICIPATION_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-shootaround-participation-digest-v0"
)

SHOOTAROUND_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "basketball_shootaround_blocked_participation_score",
    "basketball_shootaround_late_to_tip",
    "basketball_shootaround_low_beat_confirmation",
    "basketball_shootaround_minutes_restriction_blocked",
    "basketball_shootaround_minutes_restriction_watch",
    "basketball_shootaround_noncontact_participation",
    "basketball_shootaround_participation_inline",
    "basketball_shootaround_source_disagreement",
    "basketball_shootaround_stale_injury_report",
    "basketball_shootaround_watch_participation_score",
)
REPORT_REASON_CODES = (
    "basketball_shootaround_blocked_signal_present",
    "basketball_shootaround_late_to_tip_present",
    "basketball_shootaround_low_confirmation_present",
    "basketball_shootaround_minutes_restriction_present",
    "basketball_shootaround_noncontact_participation_present",
    "basketball_shootaround_participation_digest_clear",
    "basketball_shootaround_participation_digest_empty",
    "basketball_shootaround_source_disagreement_present",
    "basketball_shootaround_stale_injury_report_present",
    "basketball_shootaround_watch_signal_present",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
BLOCKED_RISK_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_BASKETBALL_SHOOTAROUND_PARTICIPATION_DIGEST_CONFIG_VERSION",
    "BasketballShootaroundParticipationDigestConfig",
    "BasketballShootaroundParticipationObservation",
    "BasketballShootaroundParticipationDigestRow",
    "BasketballShootaroundParticipationReasonCodeCount",
    "BasketballShootaroundParticipationDigestReport",
    "build_market_research_basketball_shootaround_participation_digest",
    "market_research_basketball_shootaround_participation_digest_payload",
)


@dataclass(frozen=True)
class BasketballShootaroundParticipationDigestConfig:
    config_version: str = (
        DEFAULT_BASKETBALL_SHOOTAROUND_PARTICIPATION_DIGEST_CONFIG_VERSION
    )
    watch_participation_score: Decimal = Decimal("0.600000")
    blocked_participation_score: Decimal = Decimal("0.900000")
    watch_minutes_restriction_probability: Decimal = Decimal("0.400000")
    blocked_minutes_restriction_probability: Decimal = Decimal("0.650000")
    stale_injury_report_age_minutes: Decimal = Decimal("240.000000")
    minimum_beat_source_confirmation_count: Decimal = Decimal("2.000000")
    blocked_source_disagreement_count: Decimal = Decimal("2.000000")
    late_to_tip_minutes: Decimal = Decimal("120.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballShootaroundParticipationDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASKETBALL_SHOOTAROUND_PARTICIPATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_participation_score",
            "blocked_participation_score",
            "watch_minutes_restriction_probability",
            "blocked_minutes_restriction_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_injury_report_age_minutes",
            "late_to_tip_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_beat_source_confirmation_count",
            "blocked_source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_participation_score > self.blocked_participation_score:
            raise ValueError(
                "watch_participation_score must not exceed blocked_participation_score",
            )
        if (
            self.watch_minutes_restriction_probability
            > self.blocked_minutes_restriction_probability
        ):
            raise ValueError(
                "watch_minutes_restriction_probability must not exceed "
                "blocked_minutes_restriction_probability",
            )
        if self.blocked_source_disagreement_count <= ZERO:
            raise ValueError("blocked_source_disagreement_count must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BasketballShootaroundParticipationObservation:
    source_id: str
    team_slug: str
    player_slug: str
    opponent_slug: str
    market_slug: str
    participation_score: Decimal
    noncontact_participation_flag: Decimal
    minutes_restriction_probability: Decimal
    injury_report_age_minutes: Decimal
    beat_source_confirmation_count: Decimal
    source_disagreement_count: Decimal
    time_to_tip_minutes: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballShootaroundParticipationObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "team_slug",
            "player_slug",
            "opponent_slug",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "participation_score",
            _require_ratio("participation_score", self.participation_score),
        )
        object.__setattr__(
            self,
            "noncontact_participation_flag",
            _require_binary_decimal(
                "noncontact_participation_flag",
                self.noncontact_participation_flag,
            ),
        )
        object.__setattr__(
            self,
            "minutes_restriction_probability",
            _require_ratio(
                "minutes_restriction_probability",
                self.minutes_restriction_probability,
            ),
        )
        for field_name in (
            "injury_report_age_minutes",
            "time_to_tip_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "beat_source_confirmation_count",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class BasketballShootaroundParticipationDigestRow:
    source_id: str
    team_slug: str
    player_slug: str
    opponent_slug: str
    market_slug: str
    participation_score: Decimal
    noncontact_participation_flag: Decimal
    minutes_restriction_probability: Decimal
    injury_report_age_minutes: Decimal
    beat_source_confirmation_count: Decimal
    source_disagreement_count: Decimal
    time_to_tip_minutes: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    shootaround_status: str
    row_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, BasketballShootaroundParticipationDigestRow, "row")
        for field_name in (
            "source_id",
            "team_slug",
            "player_slug",
            "opponent_slug",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "participation_score",
            _require_ratio("participation_score", self.participation_score),
        )
        object.__setattr__(
            self,
            "noncontact_participation_flag",
            _require_binary_decimal(
                "noncontact_participation_flag",
                self.noncontact_participation_flag,
            ),
        )
        object.__setattr__(
            self,
            "minutes_restriction_probability",
            _require_ratio(
                "minutes_restriction_probability",
                self.minutes_restriction_probability,
            ),
        )
        for field_name in (
            "injury_report_age_minutes",
            "time_to_tip_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "beat_source_confirmation_count",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        _require_member("shootaround_status", self.shootaround_status, SHOOTAROUND_STATUSES)
        object.__setattr__(
            self,
            "row_risk_score",
            _require_ratio("row_risk_score", self.row_risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BasketballShootaroundParticipationReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BasketballShootaroundParticipationReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class BasketballShootaroundParticipationDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    noncontact_count: Decimal
    minutes_restriction_risk_count: Decimal
    stale_injury_report_count: Decimal
    low_confirmation_count: Decimal
    source_disagreement_row_count: Decimal
    late_to_tip_count: Decimal
    max_participation_score: Decimal
    average_participation_score: Decimal
    shootaround_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...]
    reason_code_counts: tuple[BasketballShootaroundParticipationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, BasketballShootaroundParticipationDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASKETBALL_SHOOTAROUND_PARTICIPATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "noncontact_count",
            "minutes_restriction_risk_count",
            "stale_injury_report_count",
            "low_confirmation_count",
            "source_disagreement_row_count",
            "late_to_tip_count",
            "max_participation_score",
            "average_participation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "shootaround_risk_score",
            _require_ratio("shootaround_risk_score", self.shootaround_risk_score),
        )
        _require_member("digest_status", self.digest_status, SHOOTAROUND_STATUSES)
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


def build_market_research_basketball_shootaround_participation_digest(
    observations: Iterable[BasketballShootaroundParticipationObservation],
    *,
    config: BasketballShootaroundParticipationDigestConfig,
    generated_at: datetime,
) -> BasketballShootaroundParticipationDigestReport:
    if type(config) is not BasketballShootaroundParticipationDigestConfig:
        raise ValueError(
            "config must be exactly BasketballShootaroundParticipationDigestConfig",
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

    return BasketballShootaroundParticipationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        noncontact_count=_reason_count(
            rows,
            "basketball_shootaround_noncontact_participation",
        ),
        minutes_restriction_risk_count=_combined_reason_count(
            rows,
            (
                "basketball_shootaround_minutes_restriction_blocked",
                "basketball_shootaround_minutes_restriction_watch",
            ),
        ),
        stale_injury_report_count=_reason_count(
            rows,
            "basketball_shootaround_stale_injury_report",
        ),
        low_confirmation_count=_reason_count(
            rows,
            "basketball_shootaround_low_beat_confirmation",
        ),
        source_disagreement_row_count=_reason_count(
            rows,
            "basketball_shootaround_source_disagreement",
        ),
        late_to_tip_count=_reason_count(rows, "basketball_shootaround_late_to_tip"),
        max_participation_score=_max_row_decimal(rows, "participation_score"),
        average_participation_score=_ratio(
            _sum_decimal(row.participation_score for row in rows),
            row_count,
        ),
        shootaround_risk_score=_shootaround_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_basketball_shootaround_participation_digest_payload(
    report: BasketballShootaroundParticipationDigestReport,
) -> dict[str, Any]:
    if type(report) is not BasketballShootaroundParticipationDigestReport:
        raise ValueError(
            "report must be exactly BasketballShootaroundParticipationDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    observation: BasketballShootaroundParticipationObservation,
    *,
    config: BasketballShootaroundParticipationDigestConfig,
) -> BasketballShootaroundParticipationDigestRow:
    reason_codes = _row_reason_codes(observation, config=config)
    shootaround_status = _row_status(observation, reason_codes, config=config)
    return BasketballShootaroundParticipationDigestRow(
        source_id=observation.source_id,
        team_slug=observation.team_slug,
        player_slug=observation.player_slug,
        opponent_slug=observation.opponent_slug,
        market_slug=observation.market_slug,
        participation_score=observation.participation_score,
        noncontact_participation_flag=observation.noncontact_participation_flag,
        minutes_restriction_probability=observation.minutes_restriction_probability,
        injury_report_age_minutes=observation.injury_report_age_minutes,
        beat_source_confirmation_count=observation.beat_source_confirmation_count,
        source_disagreement_count=observation.source_disagreement_count,
        time_to_tip_minutes=observation.time_to_tip_minutes,
        observed_at=observation.observed_at,
        upstream_reason_codes=observation.upstream_reason_codes,
        shootaround_status=shootaround_status,
        row_risk_score=_row_risk_score(shootaround_status),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: BasketballShootaroundParticipationObservation,
    *,
    config: BasketballShootaroundParticipationDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.participation_score >= config.blocked_participation_score:
        reason_codes.append("basketball_shootaround_blocked_participation_score")
    elif observation.participation_score >= config.watch_participation_score:
        reason_codes.append("basketball_shootaround_watch_participation_score")

    if (
        observation.minutes_restriction_probability
        >= config.blocked_minutes_restriction_probability
    ):
        reason_codes.append("basketball_shootaround_minutes_restriction_blocked")
    elif (
        observation.minutes_restriction_probability
        >= config.watch_minutes_restriction_probability
    ):
        reason_codes.append("basketball_shootaround_minutes_restriction_watch")

    if observation.noncontact_participation_flag == ONE:
        reason_codes.append("basketball_shootaround_noncontact_participation")
    if observation.injury_report_age_minutes >= config.stale_injury_report_age_minutes:
        reason_codes.append("basketball_shootaround_stale_injury_report")
    if (
        observation.beat_source_confirmation_count
        < config.minimum_beat_source_confirmation_count
    ):
        reason_codes.append("basketball_shootaround_low_beat_confirmation")
    if observation.source_disagreement_count > ZERO:
        reason_codes.append("basketball_shootaround_source_disagreement")
    if observation.time_to_tip_minutes <= config.late_to_tip_minutes:
        reason_codes.append("basketball_shootaround_late_to_tip")

    if not reason_codes:
        reason_codes.append("basketball_shootaround_participation_inline")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_status(
    observation: BasketballShootaroundParticipationObservation,
    reason_codes: tuple[str, ...],
    *,
    config: BasketballShootaroundParticipationDigestConfig,
) -> str:
    if (
        observation.participation_score >= config.blocked_participation_score
        or observation.minutes_restriction_probability
        >= config.blocked_minutes_restriction_probability
        or observation.source_disagreement_count >= config.blocked_source_disagreement_count
    ):
        return "blocked"
    if reason_codes != ("basketball_shootaround_participation_inline",):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("basketball_shootaround_participation_digest_empty",)
    reason_codes: list[str] = []
    if any(row.shootaround_status == "blocked" for row in rows):
        reason_codes.append("basketball_shootaround_blocked_signal_present")
    elif any(row.shootaround_status == "watch" for row in rows):
        reason_codes.append("basketball_shootaround_watch_signal_present")
    if _reason_count(rows, "basketball_shootaround_late_to_tip") > ZERO:
        reason_codes.append("basketball_shootaround_late_to_tip_present")
    if _reason_count(rows, "basketball_shootaround_low_beat_confirmation") > ZERO:
        reason_codes.append("basketball_shootaround_low_confirmation_present")
    if _combined_reason_count(
        rows,
        (
            "basketball_shootaround_minutes_restriction_blocked",
            "basketball_shootaround_minutes_restriction_watch",
        ),
    ) > ZERO:
        reason_codes.append("basketball_shootaround_minutes_restriction_present")
    if _reason_count(rows, "basketball_shootaround_noncontact_participation") > ZERO:
        reason_codes.append("basketball_shootaround_noncontact_participation_present")
    if _reason_count(rows, "basketball_shootaround_source_disagreement") > ZERO:
        reason_codes.append("basketball_shootaround_source_disagreement_present")
    if _reason_count(rows, "basketball_shootaround_stale_injury_report") > ZERO:
        reason_codes.append("basketball_shootaround_stale_injury_report_present")
    if not reason_codes:
        reason_codes.append("basketball_shootaround_participation_digest_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
) -> tuple[BasketballShootaroundParticipationReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("basketball_shootaround_participation_digest_empty",):
        return (
            BasketballShootaroundParticipationReasonCodeCount(
                reason_code="basketball_shootaround_participation_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        BasketballShootaroundParticipationReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
) -> Decimal:
    if reason_code == "basketball_shootaround_blocked_signal_present":
        return _status_count(rows, "blocked")
    if reason_code == "basketball_shootaround_watch_signal_present":
        return _status_count(rows, "watch")
    if reason_code == "basketball_shootaround_late_to_tip_present":
        return _reason_count(rows, "basketball_shootaround_late_to_tip")
    if reason_code == "basketball_shootaround_low_confirmation_present":
        return _reason_count(rows, "basketball_shootaround_low_beat_confirmation")
    if reason_code == "basketball_shootaround_minutes_restriction_present":
        return _combined_reason_count(
            rows,
            (
                "basketball_shootaround_minutes_restriction_blocked",
                "basketball_shootaround_minutes_restriction_watch",
            ),
        )
    if reason_code == "basketball_shootaround_noncontact_participation_present":
        return _reason_count(rows, "basketball_shootaround_noncontact_participation")
    if reason_code == "basketball_shootaround_participation_digest_clear":
        return _reason_count(rows, "basketball_shootaround_participation_inline")
    if reason_code == "basketball_shootaround_source_disagreement_present":
        return _reason_count(rows, "basketball_shootaround_source_disagreement")
    if reason_code == "basketball_shootaround_stale_injury_report_present":
        return _reason_count(rows, "basketball_shootaround_stale_injury_report")
    raise ValueError("reason_code must be supported")


def _digest_status(rows: tuple[BasketballShootaroundParticipationDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.shootaround_status == "blocked" for row in rows):
        return "blocked"
    if any(row.shootaround_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_basketball_shootaround_participation_screening"
    if status == "watch":
        return "monitor_report_only_basketball_shootaround_participation_screening"
    return "block_report_only_basketball_shootaround_participation_screening"


def _row_risk_score(status: str) -> Decimal:
    if status == "blocked":
        return BLOCKED_RISK_SCORE
    if status == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _shootaround_risk_score(
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.row_risk_score for row in rows)


def _validate_row(row: BasketballShootaroundParticipationDigestRow) -> None:
    if row.row_risk_score != _row_risk_score(row.shootaround_status):
        raise ValueError("row_risk_score must match shootaround_status")
    has_inline = "basketball_shootaround_participation_inline" in row.reason_codes
    if row.shootaround_status == "pass":
        if row.reason_codes != ("basketball_shootaround_participation_inline",):
            raise ValueError("reason_codes must match shootaround_status")
        return
    if has_inline:
        raise ValueError("reason_codes must match shootaround_status")
    if row.shootaround_status == "watch" and row.reason_codes == ():
        raise ValueError("reason_codes must match shootaround_status")
    if row.shootaround_status == "blocked" and row.reason_codes == ():
        raise ValueError("reason_codes must match shootaround_status")
    if (
        row.noncontact_participation_flag == ONE
    ) != ("basketball_shootaround_noncontact_participation" in row.reason_codes):
        raise ValueError("reason_codes must match noncontact_participation_flag")
    if (
        row.source_disagreement_count > ZERO
    ) != ("basketball_shootaround_source_disagreement" in row.reason_codes):
        raise ValueError("reason_codes must match source_disagreement_count")


def _validate_report(report: BasketballShootaroundParticipationDigestReport) -> None:
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
    if report.noncontact_count != _reason_count(
        report.rows,
        "basketball_shootaround_noncontact_participation",
    ):
        raise ValueError("noncontact_count must match rows")
    if report.minutes_restriction_risk_count != _combined_reason_count(
        report.rows,
        (
            "basketball_shootaround_minutes_restriction_blocked",
            "basketball_shootaround_minutes_restriction_watch",
        ),
    ):
        raise ValueError("minutes_restriction_risk_count must match rows")
    if report.stale_injury_report_count != _reason_count(
        report.rows,
        "basketball_shootaround_stale_injury_report",
    ):
        raise ValueError("stale_injury_report_count must match rows")
    if report.low_confirmation_count != _reason_count(
        report.rows,
        "basketball_shootaround_low_beat_confirmation",
    ):
        raise ValueError("low_confirmation_count must match rows")
    if report.source_disagreement_row_count != _reason_count(
        report.rows,
        "basketball_shootaround_source_disagreement",
    ):
        raise ValueError("source_disagreement_row_count must match rows")
    if report.late_to_tip_count != _reason_count(
        report.rows,
        "basketball_shootaround_late_to_tip",
    ):
        raise ValueError("late_to_tip_count must match rows")
    if report.max_participation_score != _max_row_decimal(
        report.rows,
        "participation_score",
    ):
        raise ValueError("max_participation_score must match rows")
    if report.average_participation_score != _ratio(
        _sum_decimal(row.participation_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_participation_score must match rows")
    if report.shootaround_risk_score != _shootaround_risk_score(report.rows):
        raise ValueError("shootaround_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[BasketballShootaroundParticipationObservation],
) -> tuple[BasketballShootaroundParticipationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain BasketballShootaroundParticipationObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not BasketballShootaroundParticipationObservation:
            raise ValueError(
                "observations must contain BasketballShootaroundParticipationObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[BasketballShootaroundParticipationDigestRow],
) -> tuple[BasketballShootaroundParticipationDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain BasketballShootaroundParticipationDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not BasketballShootaroundParticipationDigestRow:
            raise ValueError("rows must contain BasketballShootaroundParticipationDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[BasketballShootaroundParticipationReasonCodeCount],
) -> tuple[BasketballShootaroundParticipationReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not BasketballShootaroundParticipationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "BasketballShootaroundParticipationReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


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
    return tuple(sorted(normalized))


def _row_sort_key(
    row: BasketballShootaroundParticipationDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.shootaround_status],
        -row.row_risk_score,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.shootaround_status == status))


def _reason_count(
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _combined_reason_count(
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _max_row_decimal(
    rows: tuple[BasketballShootaroundParticipationDigestRow, ...],
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


def _require_binary_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        if decimal_value != decimal_value.to_integral_value():
            raise ValueError(f"{field_name} must be a whole Decimal")
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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


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
