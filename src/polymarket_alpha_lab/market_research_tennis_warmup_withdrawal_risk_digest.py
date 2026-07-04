"""Pure Phase 1 tennis warmup withdrawal risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_TENNIS_WARMUP_WITHDRAWAL_RISK_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-warmup-withdrawal-risk-digest-v0"
)

RISK_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "tennis_warmup_withdrawal_low_warmup_participation",
    "tennis_warmup_withdrawal_medical_timeout_history",
    "tennis_warmup_withdrawal_travel_fatigue",
    "tennis_warmup_withdrawal_surface_transition",
    "tennis_warmup_withdrawal_match_start_imminent",
    "tennis_warmup_withdrawal_stale_source",
    "tennis_warmup_withdrawal_source_disagreement",
    "tennis_warmup_withdrawal_upstream_signal",
    "tennis_warmup_withdrawal_risk_score_watch",
    "tennis_warmup_withdrawal_risk_score_blocked",
    "tennis_warmup_withdrawal_inline",
)
REPORT_REASON_CODES = (
    "tennis_warmup_withdrawal_blocked_risk_present",
    "tennis_warmup_withdrawal_watch_risk_present",
    "tennis_warmup_withdrawal_low_warmup_participation_present",
    "tennis_warmup_withdrawal_medical_timeout_history_present",
    "tennis_warmup_withdrawal_travel_surface_overlap",
    "tennis_warmup_withdrawal_match_start_imminent_present",
    "tennis_warmup_withdrawal_source_quality_gap_present",
    "tennis_warmup_withdrawal_upstream_signal_present",
    "tennis_warmup_withdrawal_digest_clear",
    "tennis_warmup_withdrawal_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
SECONDS_PER_MINUTE = Decimal("60.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
MEDICAL_TIMEOUT_RISK_CAP = Decimal("2.000000")
MATCH_START_RISK_WINDOW = Decimal("45.000000")
STALE_SOURCE_RISK_WINDOW = Decimal("60.000000")
WARMUP_WEIGHT = Decimal("0.350000")
MEDICAL_WEIGHT = Decimal("0.200000")
TRAVEL_WEIGHT = Decimal("0.150000")
SURFACE_WEIGHT = Decimal("0.100000")
PROXIMITY_WEIGHT = Decimal("0.100000")
FRESHNESS_WEIGHT = Decimal("0.050000")
DISAGREEMENT_WEIGHT = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_TENNIS_WARMUP_WITHDRAWAL_RISK_DIGEST_CONFIG_VERSION",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "TennisWarmupWithdrawalRiskDigestConfig",
    "TennisWarmupWithdrawalRiskObservation",
    "TennisWarmupWithdrawalRiskDigestRow",
    "TennisWarmupWithdrawalRiskReasonCodeCount",
    "TennisWarmupWithdrawalRiskDigestReport",
    "build_market_research_tennis_warmup_withdrawal_risk_digest",
    "market_research_tennis_warmup_withdrawal_risk_digest_payload",
)


@dataclass(frozen=True)
class TennisWarmupWithdrawalRiskDigestConfig:
    config_version: str = DEFAULT_TENNIS_WARMUP_WITHDRAWAL_RISK_DIGEST_CONFIG_VERSION
    watch_risk_score_threshold: Decimal = Decimal("0.500000")
    blocked_risk_score_threshold: Decimal = Decimal("0.750000")
    watch_warmup_participation_score: Decimal = Decimal("0.500000")
    blocked_warmup_participation_score: Decimal = Decimal("0.250000")
    watch_medical_timeout_history_count: Decimal = Decimal("1.000000")
    blocked_medical_timeout_history_count: Decimal = Decimal("2.000000")
    travel_fatigue_watch_score: Decimal = Decimal("0.500000")
    surface_transition_watch_score: Decimal = Decimal("0.500000")
    match_start_imminent_minutes: Decimal = Decimal("45.000000")
    stale_source_after_minutes: Decimal = Decimal("60.000000")
    source_disagreement_watch_score: Decimal = Decimal("0.500000")
    source_disagreement_blocked_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisWarmupWithdrawalRiskDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TENNIS_WARMUP_WITHDRAWAL_RISK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_risk_score_threshold",
            "blocked_risk_score_threshold",
            "watch_warmup_participation_score",
            "blocked_warmup_participation_score",
            "travel_fatigue_watch_score",
            "surface_transition_watch_score",
            "source_disagreement_watch_score",
            "source_disagreement_blocked_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_medical_timeout_history_count",
            "blocked_medical_timeout_history_count",
            "match_start_imminent_minutes",
            "stale_source_after_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_risk_score_threshold > self.blocked_risk_score_threshold:
            raise ValueError(
                "watch_risk_score_threshold must not exceed blocked_risk_score_threshold",
            )
        if self.blocked_warmup_participation_score > self.watch_warmup_participation_score:
            raise ValueError(
                "blocked_warmup_participation_score must not exceed "
                "watch_warmup_participation_score",
            )
        if (
            self.watch_medical_timeout_history_count
            > self.blocked_medical_timeout_history_count
        ):
            raise ValueError(
                "watch_medical_timeout_history_count must not exceed "
                "blocked_medical_timeout_history_count",
            )
        if self.source_disagreement_watch_score > self.source_disagreement_blocked_score:
            raise ValueError(
                "source_disagreement_watch_score must not exceed "
                "source_disagreement_blocked_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TennisWarmupWithdrawalRiskObservation:
    source_id: str
    player: str
    opponent: str
    tournament: str
    market_slug: str
    warmup_participation_score: Decimal
    medical_timeout_history_count: Decimal
    travel_fatigue_score: Decimal
    surface_transition_score: Decimal
    source_disagreement_score: Decimal
    match_start_at: datetime
    source_reported_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisWarmupWithdrawalRiskObservation, "observation")
        for field_name in (
            "source_id",
            "player",
            "opponent",
            "tournament",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "warmup_participation_score",
            "travel_fatigue_score",
            "surface_transition_score",
            "source_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "medical_timeout_history_count",
            _require_nonnegative_decimal(
                "medical_timeout_history_count",
                self.medical_timeout_history_count,
            ),
        )
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(
            self,
            "source_reported_at",
            _as_utc("source_reported_at", self.source_reported_at),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class TennisWarmupWithdrawalRiskDigestRow:
    source_id: str
    player: str
    opponent: str
    tournament: str
    market_slug: str
    warmup_participation_score: Decimal
    medical_timeout_history_count: Decimal
    travel_fatigue_score: Decimal
    surface_transition_score: Decimal
    source_disagreement_score: Decimal
    match_start_at: datetime
    source_reported_at: datetime
    source_age_minutes: Decimal
    match_start_proximity_minutes: Decimal
    risk_score: Decimal
    risk_status: str
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisWarmupWithdrawalRiskDigestRow, "row")
        for field_name in (
            "source_id",
            "player",
            "opponent",
            "tournament",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "warmup_participation_score",
            "travel_fatigue_score",
            "surface_transition_score",
            "source_disagreement_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "medical_timeout_history_count",
            "source_age_minutes",
            "match_start_proximity_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(
            self,
            "source_reported_at",
            _as_utc("source_reported_at", self.source_reported_at),
        )
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class TennisWarmupWithdrawalRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TennisWarmupWithdrawalRiskReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class TennisWarmupWithdrawalRiskDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    low_warmup_participation_count: Decimal
    medical_timeout_history_count: Decimal
    source_quality_gap_count: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...]
    reason_code_counts: tuple[TennisWarmupWithdrawalRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisWarmupWithdrawalRiskDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TENNIS_WARMUP_WITHDRAWAL_RISK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "low_warmup_participation_count",
            "medical_timeout_history_count",
            "source_quality_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_risk_score", "average_risk_score", "risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, RISK_STATUSES)
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


def build_market_research_tennis_warmup_withdrawal_risk_digest(
    observations: Iterable[TennisWarmupWithdrawalRiskObservation],
    *,
    config: TennisWarmupWithdrawalRiskDigestConfig,
    generated_at: datetime,
) -> TennisWarmupWithdrawalRiskDigestReport:
    if type(config) is not TennisWarmupWithdrawalRiskDigestConfig:
        raise ValueError("config must be exactly TennisWarmupWithdrawalRiskDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return TennisWarmupWithdrawalRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        low_warmup_participation_count=_reason_count(
            rows,
            "tennis_warmup_withdrawal_low_warmup_participation",
        ),
        medical_timeout_history_count=_reason_count(
            rows,
            "tennis_warmup_withdrawal_medical_timeout_history",
        ),
        source_quality_gap_count=_source_quality_gap_count(rows),
        max_risk_score=_max_row_decimal(rows, "risk_score"),
        average_risk_score=_ratio(_sum_decimal(row.risk_score for row in rows), row_count),
        risk_score=_max_row_decimal(rows, "risk_score"),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_tennis_warmup_withdrawal_risk_digest_payload(
    report: TennisWarmupWithdrawalRiskDigestReport,
) -> dict[str, Any]:
    if type(report) is not TennisWarmupWithdrawalRiskDigestReport:
        raise ValueError("report must be exactly TennisWarmupWithdrawalRiskDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: TennisWarmupWithdrawalRiskObservation,
    *,
    config: TennisWarmupWithdrawalRiskDigestConfig,
    generated_at: datetime,
) -> TennisWarmupWithdrawalRiskDigestRow:
    source_age_minutes = _minutes_between(observation.source_reported_at, generated_at)
    match_start_proximity_minutes = _minutes_between(
        observation.source_reported_at,
        observation.match_start_at,
    )
    risk_score = _risk_score(
        warmup_participation_score=observation.warmup_participation_score,
        medical_timeout_history_count=observation.medical_timeout_history_count,
        travel_fatigue_score=observation.travel_fatigue_score,
        surface_transition_score=observation.surface_transition_score,
        match_start_proximity_minutes=match_start_proximity_minutes,
        source_age_minutes=source_age_minutes,
        source_disagreement_score=observation.source_disagreement_score,
    )
    risk_status = _risk_status(
        observation,
        risk_score=risk_score,
        config=config,
    )
    return TennisWarmupWithdrawalRiskDigestRow(
        source_id=observation.source_id,
        player=observation.player,
        opponent=observation.opponent,
        tournament=observation.tournament,
        market_slug=observation.market_slug,
        warmup_participation_score=observation.warmup_participation_score,
        medical_timeout_history_count=observation.medical_timeout_history_count,
        travel_fatigue_score=observation.travel_fatigue_score,
        surface_transition_score=observation.surface_transition_score,
        source_disagreement_score=observation.source_disagreement_score,
        match_start_at=observation.match_start_at,
        source_reported_at=observation.source_reported_at,
        source_age_minutes=source_age_minutes,
        match_start_proximity_minutes=match_start_proximity_minutes,
        risk_score=risk_score,
        risk_status=risk_status,
        upstream_reason_codes=observation.upstream_reason_codes,
        reason_codes=_row_reason_codes(
            observation,
            source_age_minutes=source_age_minutes,
            match_start_proximity_minutes=match_start_proximity_minutes,
            risk_score=risk_score,
            risk_status=risk_status,
            config=config,
        ),
    )


def _risk_status(
    observation: TennisWarmupWithdrawalRiskObservation,
    *,
    risk_score: Decimal,
    config: TennisWarmupWithdrawalRiskDigestConfig,
) -> str:
    if risk_score >= config.blocked_risk_score_threshold:
        return "blocked"
    if observation.warmup_participation_score <= config.blocked_warmup_participation_score:
        return "blocked"
    if (
        observation.medical_timeout_history_count
        >= config.blocked_medical_timeout_history_count
    ):
        return "blocked"
    if observation.source_disagreement_score >= config.source_disagreement_blocked_score:
        return "blocked"
    if risk_score >= config.watch_risk_score_threshold:
        return "watch"
    if observation.warmup_participation_score <= config.watch_warmup_participation_score:
        return "watch"
    if observation.medical_timeout_history_count >= config.watch_medical_timeout_history_count:
        return "watch"
    if observation.travel_fatigue_score >= config.travel_fatigue_watch_score:
        return "watch"
    if observation.surface_transition_score >= config.surface_transition_watch_score:
        return "watch"
    if observation.source_disagreement_score >= config.source_disagreement_watch_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: TennisWarmupWithdrawalRiskObservation,
    *,
    source_age_minutes: Decimal,
    match_start_proximity_minutes: Decimal,
    risk_score: Decimal,
    risk_status: str,
    config: TennisWarmupWithdrawalRiskDigestConfig,
) -> tuple[str, ...]:
    if risk_status == "pass":
        return ("tennis_warmup_withdrawal_inline",)

    reason_codes: list[str] = []
    if observation.warmup_participation_score <= config.watch_warmup_participation_score:
        reason_codes.append("tennis_warmup_withdrawal_low_warmup_participation")
    if observation.medical_timeout_history_count >= config.watch_medical_timeout_history_count:
        reason_codes.append("tennis_warmup_withdrawal_medical_timeout_history")
    if observation.travel_fatigue_score >= config.travel_fatigue_watch_score:
        reason_codes.append("tennis_warmup_withdrawal_travel_fatigue")
    if observation.surface_transition_score >= config.surface_transition_watch_score:
        reason_codes.append("tennis_warmup_withdrawal_surface_transition")
    if match_start_proximity_minutes <= config.match_start_imminent_minutes:
        reason_codes.append("tennis_warmup_withdrawal_match_start_imminent")
    if source_age_minutes >= config.stale_source_after_minutes:
        reason_codes.append("tennis_warmup_withdrawal_stale_source")
    if observation.source_disagreement_score >= config.source_disagreement_watch_score:
        reason_codes.append("tennis_warmup_withdrawal_source_disagreement")
    if observation.upstream_reason_codes:
        reason_codes.append("tennis_warmup_withdrawal_upstream_signal")
    if risk_score >= config.blocked_risk_score_threshold:
        reason_codes.append("tennis_warmup_withdrawal_risk_score_blocked")
    elif risk_score >= config.watch_risk_score_threshold:
        reason_codes.append("tennis_warmup_withdrawal_risk_score_watch")
    if not reason_codes:
        reason_codes.append("tennis_warmup_withdrawal_risk_score_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("tennis_warmup_withdrawal_digest_empty",)
    reason_codes: list[str] = []
    if any(row.risk_status == "blocked" for row in rows):
        reason_codes.append("tennis_warmup_withdrawal_blocked_risk_present")
    if any(row.risk_status == "watch" for row in rows):
        reason_codes.append("tennis_warmup_withdrawal_watch_risk_present")
    if _reason_count(rows, "tennis_warmup_withdrawal_low_warmup_participation") > ZERO:
        reason_codes.append("tennis_warmup_withdrawal_low_warmup_participation_present")
    if _reason_count(rows, "tennis_warmup_withdrawal_medical_timeout_history") > ZERO:
        reason_codes.append("tennis_warmup_withdrawal_medical_timeout_history_present")
    if _travel_surface_overlap_count(rows) > ZERO:
        reason_codes.append("tennis_warmup_withdrawal_travel_surface_overlap")
    if _reason_count(rows, "tennis_warmup_withdrawal_match_start_imminent") > ZERO:
        reason_codes.append("tennis_warmup_withdrawal_match_start_imminent_present")
    if _source_quality_gap_count(rows) > ZERO:
        reason_codes.append("tennis_warmup_withdrawal_source_quality_gap_present")
    if _reason_count(rows, "tennis_warmup_withdrawal_upstream_signal") > ZERO:
        reason_codes.append("tennis_warmup_withdrawal_upstream_signal_present")
    if not reason_codes:
        reason_codes.append("tennis_warmup_withdrawal_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
) -> tuple[TennisWarmupWithdrawalRiskReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("tennis_warmup_withdrawal_digest_empty",):
        return (
            TennisWarmupWithdrawalRiskReasonCodeCount(
                reason_code="tennis_warmup_withdrawal_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        TennisWarmupWithdrawalRiskReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
) -> Decimal:
    if reason_code == "tennis_warmup_withdrawal_blocked_risk_present":
        return _status_count(rows, "blocked")
    if reason_code == "tennis_warmup_withdrawal_watch_risk_present":
        return _status_count(rows, "watch")
    if reason_code == "tennis_warmup_withdrawal_travel_surface_overlap":
        return _travel_surface_overlap_count(rows)
    if reason_code == "tennis_warmup_withdrawal_source_quality_gap_present":
        return _source_quality_gap_count(rows)
    row_reason_code = {
        "tennis_warmup_withdrawal_low_warmup_participation_present": (
            "tennis_warmup_withdrawal_low_warmup_participation"
        ),
        "tennis_warmup_withdrawal_medical_timeout_history_present": (
            "tennis_warmup_withdrawal_medical_timeout_history"
        ),
        "tennis_warmup_withdrawal_match_start_imminent_present": (
            "tennis_warmup_withdrawal_match_start_imminent"
        ),
        "tennis_warmup_withdrawal_upstream_signal_present": (
            "tennis_warmup_withdrawal_upstream_signal"
        ),
        "tennis_warmup_withdrawal_digest_clear": "tennis_warmup_withdrawal_inline",
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.risk_status == "blocked" for row in rows):
        return "blocked"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_tennis_warmup_withdrawal_risk_screening"
    if status == "watch":
        return "monitor_report_only_tennis_warmup_withdrawal_risk_screening"
    return "block_report_only_tennis_warmup_withdrawal_risk_screening"


def _risk_score(
    *,
    warmup_participation_score: Decimal,
    medical_timeout_history_count: Decimal,
    travel_fatigue_score: Decimal,
    surface_transition_score: Decimal,
    match_start_proximity_minutes: Decimal,
    source_age_minutes: Decimal,
    source_disagreement_score: Decimal,
) -> Decimal:
    warmup_risk = ONE - warmup_participation_score
    medical_risk = _min_one(_ratio(medical_timeout_history_count, MEDICAL_TIMEOUT_RISK_CAP))
    proximity_risk = ONE if match_start_proximity_minutes <= MATCH_START_RISK_WINDOW else ZERO
    freshness_risk = ONE if source_age_minutes >= STALE_SOURCE_RISK_WINDOW else ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _min_one(
            _quantize_decimal(
                (warmup_risk * WARMUP_WEIGHT)
                + (medical_risk * MEDICAL_WEIGHT)
                + (travel_fatigue_score * TRAVEL_WEIGHT)
                + (surface_transition_score * SURFACE_WEIGHT)
                + (proximity_risk * PROXIMITY_WEIGHT)
                + (freshness_risk * FRESHNESS_WEIGHT)
                + (source_disagreement_score * DISAGREEMENT_WEIGHT),
            ),
        )


def _risk_score_from_row(row: TennisWarmupWithdrawalRiskDigestRow) -> Decimal:
    return _risk_score(
        warmup_participation_score=row.warmup_participation_score,
        medical_timeout_history_count=row.medical_timeout_history_count,
        travel_fatigue_score=row.travel_fatigue_score,
        surface_transition_score=row.surface_transition_score,
        match_start_proximity_minutes=row.match_start_proximity_minutes,
        source_age_minutes=row.source_age_minutes,
        source_disagreement_score=row.source_disagreement_score,
    )


def _validate_row(row: TennisWarmupWithdrawalRiskDigestRow) -> None:
    if row.match_start_proximity_minutes != _minutes_between(
        row.source_reported_at,
        row.match_start_at,
    ):
        raise ValueError("match_start_proximity_minutes must match match_start_at")
    if row.risk_score != _risk_score_from_row(row):
        raise ValueError("risk_score must match risk inputs")
    if row.risk_status == "pass":
        if row.reason_codes != ("tennis_warmup_withdrawal_inline",):
            raise ValueError("reason_codes must match risk_status")
        return
    if "tennis_warmup_withdrawal_inline" in row.reason_codes:
        raise ValueError("reason_codes must match risk_status")
    if row.risk_status == "blocked":
        blocked_reasons = (
            "tennis_warmup_withdrawal_low_warmup_participation",
            "tennis_warmup_withdrawal_medical_timeout_history",
            "tennis_warmup_withdrawal_source_disagreement",
            "tennis_warmup_withdrawal_risk_score_blocked",
        )
        if not any(reason_code in row.reason_codes for reason_code in blocked_reasons):
            raise ValueError("reason_codes must match risk_status")
    if row.risk_status == "watch" and not row.reason_codes:
        raise ValueError("reason_codes must match risk_status")


def _validate_report(report: TennisWarmupWithdrawalRiskDigestReport) -> None:
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
    if report.low_warmup_participation_count != _reason_count(
        report.rows,
        "tennis_warmup_withdrawal_low_warmup_participation",
    ):
        raise ValueError("low_warmup_participation_count must match rows")
    if report.medical_timeout_history_count != _reason_count(
        report.rows,
        "tennis_warmup_withdrawal_medical_timeout_history",
    ):
        raise ValueError("medical_timeout_history_count must match rows")
    if report.source_quality_gap_count != _source_quality_gap_count(report.rows):
        raise ValueError("source_quality_gap_count must match rows")
    if report.max_risk_score != _max_row_decimal(report.rows, "risk_score"):
        raise ValueError("max_risk_score must match rows")
    if report.average_risk_score != _ratio(
        _sum_decimal(row.risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_risk_score must match rows")
    if report.risk_score != report.max_risk_score:
        raise ValueError("risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[TennisWarmupWithdrawalRiskObservation],
) -> tuple[TennisWarmupWithdrawalRiskObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain TennisWarmupWithdrawalRiskObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not TennisWarmupWithdrawalRiskObservation:
            raise ValueError(
                "observations must contain TennisWarmupWithdrawalRiskObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[TennisWarmupWithdrawalRiskDigestRow],
) -> tuple[TennisWarmupWithdrawalRiskDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain TennisWarmupWithdrawalRiskDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not TennisWarmupWithdrawalRiskDigestRow:
            raise ValueError("rows must contain TennisWarmupWithdrawalRiskDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[TennisWarmupWithdrawalRiskReasonCodeCount],
) -> tuple[TennisWarmupWithdrawalRiskReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not TennisWarmupWithdrawalRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain TennisWarmupWithdrawalRiskReasonCodeCount",
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


def _row_sort_key(row: TennisWarmupWithdrawalRiskDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.risk_status],
        -row.risk_score,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.risk_status == status))


def _reason_count(
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _travel_surface_overlap_count(
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "tennis_warmup_withdrawal_travel_fatigue" in row.reason_codes
            and "tennis_warmup_withdrawal_surface_transition" in row.reason_codes
        ),
    )


def _source_quality_gap_count(
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "tennis_warmup_withdrawal_stale_source" in row.reason_codes
            or "tennis_warmup_withdrawal_source_disagreement" in row.reason_codes
        ),
    )


def _max_row_decimal(
    rows: tuple[TennisWarmupWithdrawalRiskDigestRow, ...],
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


def _minutes_between(start: datetime, end: datetime) -> Decimal:
    if end <= start:
        return ZERO
    delta = end - start
    total_seconds = (
        (Decimal(delta.days) * SECONDS_PER_DAY)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _ratio(_quantize_decimal(total_seconds), SECONDS_PER_MINUTE)


def _min_one(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _require_ratio(field_name: str, value: object) -> Decimal:
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
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
