"""Pure Phase 1 policy ballot access litigation shift reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_ACCESS_LITIGATION_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-policy-ballot-access-litigation-shift-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

BASE_REASON = "market_research_policy_ballot_access_litigation_shift_digest_"
ADVERSE_RULING_REASON = BASE_REASON + "adverse_ruling"
APPEAL_PENDING_REASON = BASE_REASON + "appeal_pending"
CONFIDENCE_GAP_REASON = BASE_REASON + "confidence_gap"
HIGH_RULING_SHIFT_REASON = BASE_REASON + "high_ruling_shift"
INJUNCTION_PENDING_REASON = BASE_REASON + "injunction_pending"
NEAR_DEADLINE_REASON = BASE_REASON + "near_deadline"
NO_INPUTS_REASON = BASE_REASON + "no_inputs"
READY_REASON = BASE_REASON + "ready"
RULING_SHIFT_REASON = BASE_REASON + "ruling_shift"
SOURCE_GAP_REASON = BASE_REASON + "source_gap"
STALE_SOURCE_REASON = BASE_REASON + "stale_source"

REASON_CODE_SEQUENCE = tuple(
    sorted(
        (
            ADVERSE_RULING_REASON,
            APPEAL_PENDING_REASON,
            CONFIDENCE_GAP_REASON,
            HIGH_RULING_SHIFT_REASON,
            INJUNCTION_PENDING_REASON,
            NEAR_DEADLINE_REASON,
            NO_INPUTS_REASON,
            READY_REASON,
            RULING_SHIFT_REASON,
            SOURCE_GAP_REASON,
            STALE_SOURCE_REASON,
        ),
    ),
)
ROW_REASON_CODE_SEQUENCE = tuple(
    reason for reason in REASON_CODE_SEQUENCE if reason != NO_INPUTS_REASON
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

RULING_SHIFT_WEIGHT = Decimal("0.350000")
ADVERSE_RULING_WEIGHT = Decimal("0.300000")
APPEAL_PENDING_WEIGHT = Decimal("0.175000")
INJUNCTION_PENDING_WEIGHT = Decimal("0.125000")
NEAR_DEADLINE_WEIGHT = Decimal("0.075000")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_ACCESS_LITIGATION_SHIFT_DIGEST_CONFIG_VERSION",
    "PolicyBallotAccessLitigationShiftDigestConfig",
    "PolicyBallotAccessLitigationShiftObservation",
    "PolicyBallotAccessLitigationShiftDigestRow",
    "PolicyBallotAccessLitigationShiftReasonCodeCount",
    "PolicyBallotAccessLitigationShiftDigestReport",
    "build_market_research_policy_ballot_access_litigation_shift_digest",
    "market_research_policy_ballot_access_litigation_shift_digest_payload",
)


@dataclass(frozen=True)
class PolicyBallotAccessLitigationShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_ACCESS_LITIGATION_SHIFT_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_litigation_shift_score: Decimal = Decimal("0.350000")
    blocked_litigation_shift_score: Decimal = Decimal("0.700000")
    material_ruling_shift_count: Decimal = Decimal("1.000000")
    high_ruling_shift_count: Decimal = Decimal("2.000000")
    near_deadline_days: Decimal = Decimal("14.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PolicyBallotAccessLitigationShiftDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, PolicyBallotAccessLitigationShiftDigestConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_ACCESS_LITIGATION_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_observation_age_seconds",
            "near_deadline_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_litigation_shift_score",
            "blocked_litigation_shift_score",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_count",
            "material_ruling_shift_count",
            "high_ruling_shift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_litigation_shift_score > self.blocked_litigation_shift_score:
            raise ValueError(
                "watch_litigation_shift_score must be at most "
                "blocked_litigation_shift_score",
            )
        if self.material_ruling_shift_count > self.high_ruling_shift_count:
            raise ValueError(
                "material_ruling_shift_count must be at most high_ruling_shift_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PolicyBallotAccessLitigationShiftObservation:
    source_id: str
    litigation_id: str
    contest_id: str
    jurisdiction: str
    candidate_id: str
    observed_at: datetime
    ruling_shift_count: Decimal
    adverse_ruling_count: Decimal
    appeal_pending_count: Decimal
    injunction_pending_count: Decimal
    ballot_deadline_days: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PolicyBallotAccessLitigationShiftObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("observation", self, PolicyBallotAccessLitigationShiftObservation)
        for field_name in (
            "source_id",
            "litigation_id",
            "contest_id",
            "jurisdiction",
            "candidate_id",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "ruling_shift_count",
            "adverse_ruling_count",
            "appeal_pending_count",
            "injunction_pending_count",
            "ballot_deadline_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_integral_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class PolicyBallotAccessLitigationShiftDigestRow:
    source_id: str
    litigation_id: str
    contest_id: str
    jurisdiction: str
    candidate_id: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    ruling_shift_count: Decimal
    adverse_ruling_count: Decimal
    appeal_pending_count: Decimal
    injunction_pending_count: Decimal
    ballot_deadline_days: Decimal
    source_count: Decimal
    confidence: Decimal
    max_observation_age_seconds: Decimal
    min_source_count: Decimal
    watch_litigation_shift_score: Decimal
    blocked_litigation_shift_score: Decimal
    material_ruling_shift_count: Decimal
    high_ruling_shift_count: Decimal
    near_deadline_days: Decimal
    min_confidence: Decimal
    litigation_shift_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PolicyBallotAccessLitigationShiftDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, PolicyBallotAccessLitigationShiftDigestRow)
        _revalidate_row(self, strict_utc=False)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class PolicyBallotAccessLitigationShiftReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PolicyBallotAccessLitigationShiftReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            PolicyBallotAccessLitigationShiftReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_integral_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PolicyBallotAccessLitigationShiftDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    ruling_shift_observation_count: Decimal
    adverse_ruling_observation_count: Decimal
    appeal_pending_observation_count: Decimal
    injunction_pending_observation_count: Decimal
    near_deadline_observation_count: Decimal
    source_gap_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    stale_source_observation_count: Decimal
    max_litigation_shift_score: Decimal
    average_litigation_shift_score: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    min_source_count: Decimal
    watch_litigation_shift_score: Decimal
    blocked_litigation_shift_score: Decimal
    material_ruling_shift_count: Decimal
    high_ruling_shift_count: Decimal
    near_deadline_days: Decimal
    min_confidence: Decimal
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[PolicyBallotAccessLitigationShiftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PolicyBallotAccessLitigationShiftDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, PolicyBallotAccessLitigationShiftDigestReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_ACCESS_LITIGATION_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        _revalidate_report_fields(self, strict_utc=False)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_ballot_access_litigation_shift_digest(
    observations: Iterable[PolicyBallotAccessLitigationShiftObservation],
    *,
    config: PolicyBallotAccessLitigationShiftDigestConfig | None = None,
    generated_at: datetime,
) -> PolicyBallotAccessLitigationShiftDigestReport:
    cfg = config or PolicyBallotAccessLitigationShiftDigestConfig()
    if type(cfg) is not PolicyBallotAccessLitigationShiftDigestConfig:
        raise ValueError(
            "config must be exactly PolicyBallotAccessLitigationShiftDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(
            observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for observation in normalized_observations
    )
    sorted_rows = _sort_rows(rows)
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return PolicyBallotAccessLitigationShiftDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        ruling_shift_observation_count=_reason_observation_count(
            sorted_rows,
            RULING_SHIFT_REASON,
        ),
        adverse_ruling_observation_count=_reason_observation_count(
            sorted_rows,
            ADVERSE_RULING_REASON,
        ),
        appeal_pending_observation_count=_reason_observation_count(
            sorted_rows,
            APPEAL_PENDING_REASON,
        ),
        injunction_pending_observation_count=_reason_observation_count(
            sorted_rows,
            INJUNCTION_PENDING_REASON,
        ),
        near_deadline_observation_count=_reason_observation_count(
            sorted_rows,
            NEAR_DEADLINE_REASON,
        ),
        source_gap_observation_count=_reason_observation_count(
            sorted_rows,
            SOURCE_GAP_REASON,
        ),
        confidence_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        stale_source_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_SOURCE_REASON,
        ),
        max_litigation_shift_score=max(
            (row.litigation_shift_score for row in sorted_rows),
            default=ZERO,
        ),
        average_litigation_shift_score=_ratio(
            _decimal_sum(row.litigation_shift_score for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        min_source_count=cfg.min_source_count,
        watch_litigation_shift_score=cfg.watch_litigation_shift_score,
        blocked_litigation_shift_score=cfg.blocked_litigation_shift_score,
        material_ruling_shift_count=cfg.material_ruling_shift_count,
        high_ruling_shift_count=cfg.high_ruling_shift_count,
        near_deadline_days=cfg.near_deadline_days,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.litigation_id, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_policy_ballot_access_litigation_shift_digest_payload(
    report: PolicyBallotAccessLitigationShiftDigestReport,
) -> MappingProxyType:
    if type(report) is not PolicyBallotAccessLitigationShiftDigestReport:
        raise ValueError(
            "report must be exactly PolicyBallotAccessLitigationShiftDigestReport",
        )
    _revalidate_public_dataclass(report)
    return _freeze(_payload_value(report))


def _row_for_observation(
    observation: PolicyBallotAccessLitigationShiftObservation,
    *,
    config: PolicyBallotAccessLitigationShiftDigestConfig,
    generated_at: datetime,
) -> PolicyBallotAccessLitigationShiftDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    litigation_shift_score = _litigation_shift_score(
        ruling_shift_count=observation.ruling_shift_count,
        adverse_ruling_count=observation.adverse_ruling_count,
        appeal_pending_count=observation.appeal_pending_count,
        injunction_pending_count=observation.injunction_pending_count,
        ballot_deadline_days=observation.ballot_deadline_days,
        config=config,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
    )
    return PolicyBallotAccessLitigationShiftDigestRow(
        source_id=observation.source_id,
        litigation_id=observation.litigation_id,
        contest_id=observation.contest_id,
        jurisdiction=observation.jurisdiction,
        candidate_id=observation.candidate_id,
        digest_status=_row_status(
            reason_codes,
            litigation_shift_score=litigation_shift_score,
            config=config,
        ),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        ruling_shift_count=observation.ruling_shift_count,
        adverse_ruling_count=observation.adverse_ruling_count,
        appeal_pending_count=observation.appeal_pending_count,
        injunction_pending_count=observation.injunction_pending_count,
        ballot_deadline_days=observation.ballot_deadline_days,
        source_count=observation.source_count,
        confidence=observation.confidence,
        max_observation_age_seconds=config.max_observation_age_seconds,
        min_source_count=config.min_source_count,
        watch_litigation_shift_score=config.watch_litigation_shift_score,
        blocked_litigation_shift_score=config.blocked_litigation_shift_score,
        material_ruling_shift_count=config.material_ruling_shift_count,
        high_ruling_shift_count=config.high_ruling_shift_count,
        near_deadline_days=config.near_deadline_days,
        min_confidence=config.min_confidence,
        litigation_shift_score=litigation_shift_score,
        reason_codes=reason_codes,
    )


def _litigation_shift_score(
    *,
    ruling_shift_count: Decimal,
    adverse_ruling_count: Decimal,
    appeal_pending_count: Decimal,
    injunction_pending_count: Decimal,
    ballot_deadline_days: Decimal,
    config: PolicyBallotAccessLitigationShiftDigestConfig,
) -> Decimal:
    ruling_component = (
        min(ONE, _ratio(ruling_shift_count, config.high_ruling_shift_count))
        * RULING_SHIFT_WEIGHT
    )
    adverse_component = min(ONE, adverse_ruling_count) * ADVERSE_RULING_WEIGHT
    appeal_component = min(ONE, appeal_pending_count) * APPEAL_PENDING_WEIGHT
    injunction_component = min(ONE, injunction_pending_count) * INJUNCTION_PENDING_WEIGHT
    deadline_component = (
        NEAR_DEADLINE_WEIGHT
        if ballot_deadline_days <= config.near_deadline_days
        else ZERO
    )
    return _quantize_decimal(
        min(
            ONE,
            ruling_component
            + adverse_component
            + appeal_component
            + injunction_component
            + deadline_component,
        ),
    )


def _row_reason_codes(
    *,
    observation: PolicyBallotAccessLitigationShiftObservation,
    config: PolicyBallotAccessLitigationShiftDigestConfig,
    observation_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.ruling_shift_count >= config.material_ruling_shift_count:
        reasons.append(RULING_SHIFT_REASON)
    if observation.ruling_shift_count >= config.high_ruling_shift_count:
        reasons.append(HIGH_RULING_SHIFT_REASON)
    if observation.adverse_ruling_count > ZERO:
        reasons.append(ADVERSE_RULING_REASON)
    if observation.appeal_pending_count > ZERO:
        reasons.append(APPEAL_PENDING_REASON)
    if observation.injunction_pending_count > ZERO:
        reasons.append(INJUNCTION_PENDING_REASON)
    if observation.ballot_deadline_days <= config.near_deadline_days:
        reasons.append(NEAR_DEADLINE_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_SOURCE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    litigation_shift_score: Decimal,
    config: PolicyBallotAccessLitigationShiftDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if litigation_shift_score >= config.blocked_litigation_shift_score:
        return STATUS_BLOCKED
    if any(reason in reason_codes for reason in (CONFIDENCE_GAP_REASON, STALE_SOURCE_REASON)):
        return STATUS_BLOCKED
    if litigation_shift_score >= config.watch_litigation_shift_score:
        return STATUS_WATCH
    return STATUS_WATCH


def _row_status_from_row(row: PolicyBallotAccessLitigationShiftDigestRow) -> str:
    if row.reason_codes == (READY_REASON,):
        return STATUS_READY
    if row.litigation_shift_score >= row.blocked_litigation_shift_score:
        return STATUS_BLOCKED
    if any(reason in row.reason_codes for reason in (CONFIDENCE_GAP_REASON, STALE_SOURCE_REASON)):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _sort_rows(
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...],
) -> tuple[PolicyBallotAccessLitigationShiftDigestRow, ...]:
    decorated_rows = tuple(
        (
            (
                _row_sort_tuple(row),
                row.litigation_id,
                row.source_id,
            ),
            row,
        )
        for row in rows
    )
    return tuple(row for _, row in sorted(decorated_rows))


def _row_sort_tuple(
    row: PolicyBallotAccessLitigationShiftDigestRow,
) -> tuple[int, Decimal, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(sum(1 for reason in row.reason_codes if reason != READY_REASON))
    return (status_rank, -severity, -row.litigation_shift_score)


def _report_status(rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_policy_ballot_access_litigation_shift_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_policy_ballot_access_litigation_shift_digest"
    return "allow_report_only_market_research_policy_ballot_access_litigation_shift_digest"


def _status_count(
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...],
) -> tuple[PolicyBallotAccessLitigationShiftReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    if not rows:
        return (
            PolicyBallotAccessLitigationShiftReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PolicyBallotAccessLitigationShiftReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(_decimal_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _revalidate_row(
    row: PolicyBallotAccessLitigationShiftDigestRow,
    *,
    strict_utc: bool,
) -> None:
    for field_name in (
        "source_id",
        "litigation_id",
        "contest_id",
        "jurisdiction",
        "candidate_id",
    ):
        _require_public_string(field_name, getattr(row, field_name))
    _require_status("digest_status", row.digest_status)
    if strict_utc:
        _require_utc_datetime("observed_at", row.observed_at)
    else:
        object.__setattr__(row, "observed_at", _as_utc("observed_at", row.observed_at))
    for field_name in (
        "observation_age_seconds",
        "ruling_shift_count",
        "adverse_ruling_count",
        "appeal_pending_count",
        "injunction_pending_count",
        "ballot_deadline_days",
        "max_observation_age_seconds",
        "near_deadline_days",
    ):
        object.__setattr__(
            row,
            field_name,
            _require_nonnegative_decimal(field_name, getattr(row, field_name)),
        )
    object.__setattr__(
        row,
        "source_count",
        _require_nonnegative_integral_decimal("source_count", row.source_count),
    )
    object.__setattr__(
        row,
        "confidence",
        _require_ratio_decimal("confidence", row.confidence),
    )
    for field_name in (
        "watch_litigation_shift_score",
        "blocked_litigation_shift_score",
        "min_confidence",
    ):
        object.__setattr__(
            row,
            field_name,
            _require_ratio_decimal(field_name, getattr(row, field_name)),
        )
    for field_name in (
        "min_source_count",
        "material_ruling_shift_count",
        "high_ruling_shift_count",
    ):
        object.__setattr__(
            row,
            field_name,
            _require_positive_integral_decimal(field_name, getattr(row, field_name)),
        )
    object.__setattr__(
        row,
        "litigation_shift_score",
        _require_ratio_decimal("litigation_shift_score", row.litigation_shift_score),
    )
    object.__setattr__(
        row,
        "reason_codes",
        _normalize_reason_codes("reason_codes", row.reason_codes, ROW_REASON_CODE_SEQUENCE),
    )
    _validate_row(row)


def _validate_row(row: PolicyBallotAccessLitigationShiftDigestRow) -> None:
    expected_score = _litigation_shift_score_from_row(row)
    if row.litigation_shift_score != expected_score:
        raise ValueError("litigation_shift_score does not match inputs")
    if row.watch_litigation_shift_score > row.blocked_litigation_shift_score:
        raise ValueError(
            "watch_litigation_shift_score must be at most "
            "blocked_litigation_shift_score",
        )
    if row.material_ruling_shift_count > row.high_ruling_shift_count:
        raise ValueError(
            "material_ruling_shift_count must be at most high_ruling_shift_count",
        )
    if row.digest_status != _row_status_from_row(row):
        raise ValueError("digest_status does not match reason_codes")


def _litigation_shift_score_from_row(
    row: PolicyBallotAccessLitigationShiftDigestRow,
) -> Decimal:
    cfg = PolicyBallotAccessLitigationShiftDigestConfig(
        max_observation_age_seconds=row.max_observation_age_seconds,
        min_source_count=row.min_source_count,
        watch_litigation_shift_score=row.watch_litigation_shift_score,
        blocked_litigation_shift_score=row.blocked_litigation_shift_score,
        material_ruling_shift_count=row.material_ruling_shift_count,
        high_ruling_shift_count=row.high_ruling_shift_count,
        near_deadline_days=row.near_deadline_days,
        min_confidence=row.min_confidence,
    )
    return _litigation_shift_score(
        ruling_shift_count=row.ruling_shift_count,
        adverse_ruling_count=row.adverse_ruling_count,
        appeal_pending_count=row.appeal_pending_count,
        injunction_pending_count=row.injunction_pending_count,
        ballot_deadline_days=row.ballot_deadline_days,
        config=cfg,
    )


def _revalidate_report_fields(
    report: PolicyBallotAccessLitigationShiftDigestReport,
    *,
    strict_utc: bool,
) -> None:
    if strict_utc:
        _require_utc_datetime("generated_at", report.generated_at)
    for field_name in (
        "observation_count",
        "ready_observation_count",
        "watch_observation_count",
        "blocked_observation_count",
        "ruling_shift_observation_count",
        "adverse_ruling_observation_count",
        "appeal_pending_observation_count",
        "injunction_pending_observation_count",
        "near_deadline_observation_count",
        "source_gap_observation_count",
        "confidence_gap_observation_count",
        "stale_source_observation_count",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_nonnegative_integral_decimal(field_name, getattr(report, field_name)),
        )
    for field_name in (
        "max_observation_age_seconds",
        "max_allowed_observation_age_seconds",
        "near_deadline_days",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_nonnegative_decimal(field_name, getattr(report, field_name)),
        )
    for field_name in (
        "max_litigation_shift_score",
        "average_litigation_shift_score",
        "watch_litigation_shift_score",
        "blocked_litigation_shift_score",
        "min_confidence",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_ratio_decimal(field_name, getattr(report, field_name)),
        )
    for field_name in (
        "min_source_count",
        "material_ruling_shift_count",
        "high_ruling_shift_count",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_positive_integral_decimal(field_name, getattr(report, field_name)),
        )
    object.__setattr__(report, "rows", _normalize_rows(report.rows))
    object.__setattr__(
        report,
        "source_config_versions",
        _normalize_source_config_versions(report.source_config_versions),
    )
    object.__setattr__(
        report,
        "reason_code_counts",
        _normalize_reason_code_counts(report.reason_code_counts),
    )
    object.__setattr__(
        report,
        "reason_codes",
        _normalize_reason_codes("reason_codes", report.reason_codes, REASON_CODE_SEQUENCE),
    )


def _validate_report(report: PolicyBallotAccessLitigationShiftDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (RULING_SHIFT_REASON, report.ruling_shift_observation_count),
        (ADVERSE_RULING_REASON, report.adverse_ruling_observation_count),
        (APPEAL_PENDING_REASON, report.appeal_pending_observation_count),
        (INJUNCTION_PENDING_REASON, report.injunction_pending_observation_count),
        (NEAR_DEADLINE_REASON, report.near_deadline_observation_count),
        (SOURCE_GAP_REASON, report.source_gap_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
        (STALE_SOURCE_REASON, report.stale_source_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.max_litigation_shift_score != max(
        (row.litigation_shift_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_litigation_shift_score does not match rows")
    if report.average_litigation_shift_score != _ratio(
        _decimal_sum(row.litigation_shift_score for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_litigation_shift_score does not match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_observations(
    observations: Iterable[PolicyBallotAccessLitigationShiftObservation],
) -> tuple[PolicyBallotAccessLitigationShiftObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be iterable")
    try:
        observation_tuple = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc
    seen_ids: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not PolicyBallotAccessLitigationShiftObservation:
            raise ValueError(
                "observations must contain PolicyBallotAccessLitigationShiftObservation",
            )
        if observation.litigation_id in seen_ids:
            raise ValueError("litigation_id values must be unique")
        seen_ids.add(observation.litigation_id)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[PolicyBallotAccessLitigationShiftDigestRow, ...],
) -> tuple[PolicyBallotAccessLitigationShiftDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not PolicyBallotAccessLitigationShiftDigestRow:
            raise ValueError("rows must contain PolicyBallotAccessLitigationShiftDigestRow")
        if row.litigation_id in seen_ids:
            raise ValueError("rows must not contain duplicate litigation_id values")
        seen_ids.add(row.litigation_id)
        _revalidate_row(row, strict_utc=False)
        _require_hard_flags("row", row)
    canonical = _sort_rows(rows)
    if rows != canonical:
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_source_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("source_config_versions must contain string pairs")
        litigation_id, source_config_version = value
        _require_public_string("litigation_id", litigation_id)
        _require_public_string("source_config_version", source_config_version)
        if litigation_id in seen_ids:
            raise ValueError("source_config_versions must not contain duplicates")
        seen_ids.add(litigation_id)
        normalized.append((litigation_id, source_config_version))
    canonical = tuple(sorted(normalized))
    if values != canonical:
        raise ValueError("source_config_versions must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    values: tuple[PolicyBallotAccessLitigationShiftReasonCodeCount, ...],
) -> tuple[PolicyBallotAccessLitigationShiftReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reasons: set[str] = set()
    for value in values:
        if type(value) is not PolicyBallotAccessLitigationShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PolicyBallotAccessLitigationShiftReasonCodeCount",
            )
        _require_reason_code("reason_code", value.reason_code)
        if value.reason_code in seen_reasons:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reasons.add(value.reason_code)
        _require_hard_flags("reason code count", value)
    canonical = tuple(
        item for reason in REASON_CODE_SEQUENCE for item in values if item.reason_code == reason
    )
    if values != canonical:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        _require_reason_code(field_name, value)
        if value not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    canonical = tuple(reason for reason in allowed if reason in seen)
    if values != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return values


def _revalidate_public_dataclass(value: object) -> None:
    if type(value) is PolicyBallotAccessLitigationShiftDigestReport:
        _require_utc_datetime("generated_at", value.generated_at)
        _revalidate_report_fields(value, strict_utc=True)
        _validate_report(value)
        _require_hard_flags("report", value)
        return
    if type(value) is PolicyBallotAccessLitigationShiftDigestRow:
        _revalidate_row(value, strict_utc=True)
        _require_hard_flags("row", value)
        return
    if type(value) is PolicyBallotAccessLitigationShiftReasonCodeCount:
        _require_reason_code("reason_code", value.reason_code)
        _require_positive_integral_decimal("count", value.count)
        _require_ratio_decimal("observation_ratio", value.observation_ratio)
        _require_hard_flags("reason code count", value)
        return
    if type(value) is PolicyBallotAccessLitigationShiftObservation:
        _require_utc_datetime("observed_at", value.observed_at)
        for field_name in (
            "ruling_shift_count",
            "adverse_ruling_count",
            "appeal_pending_count",
            "injunction_pending_count",
            "ballot_deadline_days",
        ):
            _require_nonnegative_decimal(field_name, getattr(value, field_name))
        _require_nonnegative_integral_decimal("source_count", value.source_count)
        _require_ratio_decimal("confidence", value.confidence)
        _require_hard_flags("observation", value)
        return
    if type(value) is PolicyBallotAccessLitigationShiftDigestConfig:
        _require_hard_flags("config", value)
        return
    raise ValueError("unsupported public dataclass")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        _require_decimal("payload decimal", value)
        return f"{value:.6f}"
    if type(value) is datetime:
        _require_utc_datetime("payload datetime", value)
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    return value


def _freeze(value: object) -> Any:
    if type(value) is dict:
        return MappingProxyType({item_name: _freeze(item) for item_name, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize_decimal(seconds + micros)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_integral_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be six-decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_DELTA:
        raise ValueError(f"{field_name} must be UTC")


ZERO_TIME_DELTA = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")
