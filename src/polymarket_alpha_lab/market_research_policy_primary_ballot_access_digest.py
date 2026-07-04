"""Pure report-only primary ballot access digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_PRIMARY_BALLOT_ACCESS_DIGEST_CONFIG_VERSION",
    "PolicyPrimaryBallotAccessDigestConfig",
    "PolicyPrimaryBallotAccessObservation",
    "PolicyPrimaryBallotAccessDigestRow",
    "PolicyPrimaryBallotAccessReasonCodeCount",
    "PolicyPrimaryBallotAccessDigestReport",
    "build_market_research_policy_primary_ballot_access_digest",
    "market_research_policy_primary_ballot_access_digest_payload",
)


DEFAULT_MARKET_RESEARCH_POLICY_PRIMARY_BALLOT_ACCESS_DIGEST_CONFIG_VERSION = (
    "market-research-policy-primary-ballot-access-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

QUALIFIED_FILING_STATUS = "qualified"
CERTIFIED_FILING_STATUS = "certified"
FILED_FILING_STATUS = "filed"
PENDING_FILING_STATUS = "pending"
CHALLENGED_FILING_STATUS = "challenged"
REMOVED_FILING_STATUS = "removed"
DISQUALIFIED_FILING_STATUS = "disqualified"
FILING_STATUSES = (
    QUALIFIED_FILING_STATUS,
    CERTIFIED_FILING_STATUS,
    FILED_FILING_STATUS,
    PENDING_FILING_STATUS,
    CHALLENGED_FILING_STATUS,
    REMOVED_FILING_STATUS,
    DISQUALIFIED_FILING_STATUS,
)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
ACCESS_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_primary_ballot_access_screening",
    WATCH_STATUS: "monitor_report_only_primary_ballot_access_screening",
    PASS_STATUS: "allow_report_only_primary_ballot_access_screening",
}

HIGH_CHALLENGE_COUNT = Decimal("2.000000")
ADVERSE_RULING_SIGNAL_COUNT = Decimal("1.000000")
IMMINENT_DEADLINE_DAYS = Decimal("14.000000")

FILING_STATUS_RISK_COMPONENTS = {
    QUALIFIED_FILING_STATUS: ZERO,
    CERTIFIED_FILING_STATUS: ZERO,
    FILED_FILING_STATUS: ZERO,
    PENDING_FILING_STATUS: Decimal("0.150000"),
    CHALLENGED_FILING_STATUS: Decimal("0.300000"),
    REMOVED_FILING_STATUS: ONE,
    DISQUALIFIED_FILING_STATUS: ONE,
}
CHALLENGE_RISK_WEIGHT = Decimal("0.250000")
ADVERSE_RULING_RISK_WEIGHT = Decimal("0.500000")
APPEAL_PENDING_RISK_WEIGHT = Decimal("0.150000")
IMMINENT_DEADLINE_RISK_WEIGHT = Decimal("0.100000")


@dataclass(frozen=True)
class PolicyPrimaryBallotAccessDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_PRIMARY_BALLOT_ACCESS_DIGEST_CONFIG_VERSION
    )
    watch_disqualification_risk_score: Decimal = Decimal("0.350000")
    blocked_disqualification_risk_score: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("900.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    clear_confidence_cap: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPrimaryBallotAccessDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_PRIMARY_BALLOT_ACCESS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_disqualification_risk_score",
            "blocked_disqualification_risk_score",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_confidence_cap", "clear_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.watch_disqualification_risk_score
            > self.blocked_disqualification_risk_score
        ):
            raise ValueError(
                "watch_disqualification_risk_score must not exceed "
                "blocked_disqualification_risk_score",
            )
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class PolicyPrimaryBallotAccessObservation:
    source_id: str
    market_slug: str
    jurisdiction: str
    candidate_name: str
    office_key: str
    party_key: str
    filing_status: str
    challenge_count: Decimal
    adverse_ruling_count: Decimal
    appeal_pending_count: Decimal
    days_until_ballot_deadline: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPrimaryBallotAccessObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "jurisdiction",
            "candidate_name",
            "office_key",
            "party_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("filing_status", self.filing_status, FILING_STATUSES)
        for field_name in (
            "challenge_count",
            "adverse_ruling_count",
            "appeal_pending_count",
            "days_until_ballot_deadline",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_confidence",
            _normalize_probability("evidence_confidence", self.evidence_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class PolicyPrimaryBallotAccessDigestRow:
    source_id: str
    market_slug: str
    jurisdiction: str
    candidate_name: str
    office_key: str
    party_key: str
    filing_status: str
    challenge_count: Decimal
    adverse_ruling_count: Decimal
    appeal_pending_count: Decimal
    days_until_ballot_deadline: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    disqualification_risk_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    access_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPrimaryBallotAccessDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "jurisdiction",
            "candidate_name",
            "office_key",
            "party_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("filing_status", self.filing_status, FILING_STATUSES)
        for field_name in (
            "challenge_count",
            "adverse_ruling_count",
            "appeal_pending_count",
            "days_until_ballot_deadline",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_confidence",
            "disqualification_risk_score",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("access_status", self.access_status, ACCESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class PolicyPrimaryBallotAccessReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            PolicyPrimaryBallotAccessReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self, "reason_code_count")


@dataclass(frozen=True)
class PolicyPrimaryBallotAccessDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    active_challenge_count: Decimal
    adverse_ruling_row_count: Decimal
    max_disqualification_risk_score: Decimal
    average_disqualification_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PolicyPrimaryBallotAccessReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyPrimaryBallotAccessDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_PRIMARY_BALLOT_ACCESS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "active_challenge_count",
            "adverse_ruling_row_count",
            "max_disqualification_risk_score",
            "average_disqualification_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, ACCESS_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self, "report")


def build_market_research_policy_primary_ballot_access_digest(
    observations: Iterable[PolicyPrimaryBallotAccessObservation],
    *,
    config: PolicyPrimaryBallotAccessDigestConfig,
    generated_at: datetime,
) -> PolicyPrimaryBallotAccessDigestReport:
    if type(config) is not PolicyPrimaryBallotAccessDigestConfig:
        raise ValueError("config must be exactly PolicyPrimaryBallotAccessDigestConfig")
    _require_hard_flags(config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return PolicyPrimaryBallotAccessDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "primary_ballot_access_source_stale"),
        active_challenge_count=_active_challenge_count(rows),
        adverse_ruling_row_count=_adverse_ruling_row_count(rows),
        max_disqualification_risk_score=_max_row_decimal(
            rows,
            "disqualification_risk_score",
        ),
        average_disqualification_risk_score=_ratio(
            _sum_decimal(row.disqualification_risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_policy_primary_ballot_access_digest_payload(
    report: PolicyPrimaryBallotAccessDigestReport,
) -> dict[str, Any]:
    if type(report) is not PolicyPrimaryBallotAccessDigestReport:
        raise ValueError("report must be exactly PolicyPrimaryBallotAccessDigestReport")
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: PolicyPrimaryBallotAccessObservation,
    *,
    config: PolicyPrimaryBallotAccessDigestConfig,
    generated_at: datetime,
) -> PolicyPrimaryBallotAccessDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    disqualification_risk_score = _disqualification_risk_score(
        filing_status=value.filing_status,
        challenge_count=value.challenge_count,
        adverse_ruling_count=value.adverse_ruling_count,
        appeal_pending_count=value.appeal_pending_count,
        days_until_ballot_deadline=value.days_until_ballot_deadline,
    )
    access_status = _access_status(disqualification_risk_score, config=config)
    confidence_cap = _confidence_cap(
        access_status=access_status,
        source_fresh=source_fresh,
        config=config,
    )
    return PolicyPrimaryBallotAccessDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        jurisdiction=value.jurisdiction,
        candidate_name=value.candidate_name,
        office_key=value.office_key,
        party_key=value.party_key,
        filing_status=value.filing_status,
        challenge_count=value.challenge_count,
        adverse_ruling_count=value.adverse_ruling_count,
        appeal_pending_count=value.appeal_pending_count,
        days_until_ballot_deadline=value.days_until_ballot_deadline,
        evidence_confidence=value.evidence_confidence,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        disqualification_risk_score=disqualification_risk_score,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.evidence_confidence, confidence_cap),
        access_status=access_status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            access_status=access_status,
            filing_status=value.filing_status,
            challenge_count=value.challenge_count,
            adverse_ruling_count=value.adverse_ruling_count,
            appeal_pending_count=value.appeal_pending_count,
            days_until_ballot_deadline=value.days_until_ballot_deadline,
            source_fresh=source_fresh,
        ),
    )


def _disqualification_risk_score(
    *,
    filing_status: str,
    challenge_count: Decimal,
    adverse_ruling_count: Decimal,
    appeal_pending_count: Decimal,
    days_until_ballot_deadline: Decimal,
) -> Decimal:
    filing_component = FILING_STATUS_RISK_COMPONENTS[filing_status]
    challenge_component = (
        min(ONE, challenge_count / HIGH_CHALLENGE_COUNT) * CHALLENGE_RISK_WEIGHT
    )
    adverse_component = (
        min(ONE, adverse_ruling_count / ADVERSE_RULING_SIGNAL_COUNT)
        * ADVERSE_RULING_RISK_WEIGHT
    )
    appeal_component = min(ONE, appeal_pending_count) * APPEAL_PENDING_RISK_WEIGHT
    deadline_component = (
        IMMINENT_DEADLINE_RISK_WEIGHT
        if days_until_ballot_deadline <= IMMINENT_DEADLINE_DAYS
        else ZERO
    )
    return _quantize_decimal(
        min(
            ONE,
            filing_component
            + challenge_component
            + adverse_component
            + appeal_component
            + deadline_component,
        ),
    )


def _access_status(
    disqualification_risk_score: Decimal,
    *,
    config: PolicyPrimaryBallotAccessDigestConfig,
) -> str:
    if disqualification_risk_score >= config.blocked_disqualification_risk_score:
        return BLOCKED_STATUS
    if disqualification_risk_score >= config.watch_disqualification_risk_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    access_status: str,
    source_fresh: bool,
    config: PolicyPrimaryBallotAccessDigestConfig,
) -> Decimal:
    caps = [ONE]
    if access_status == PASS_STATUS:
        caps.append(config.clear_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    access_status: str,
    filing_status: str,
    challenge_count: Decimal,
    adverse_ruling_count: Decimal,
    appeal_pending_count: Decimal,
    days_until_ballot_deadline: Decimal,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if access_status == BLOCKED_STATUS:
        reason_codes.append("primary_ballot_access_blocked")
    elif access_status == WATCH_STATUS:
        reason_codes.append("primary_ballot_access_watch")
    else:
        reason_codes.append("primary_ballot_access_below_threshold")
    reason_codes.append(
        "primary_ballot_access_source_fresh"
        if source_fresh
        else "primary_ballot_access_source_stale",
    )
    if filing_status == CHALLENGED_FILING_STATUS:
        reason_codes.append("primary_ballot_access_challenged_status")
    elif filing_status in (REMOVED_FILING_STATUS, DISQUALIFIED_FILING_STATUS):
        reason_codes.append("primary_ballot_access_removed_status")
    elif filing_status == PENDING_FILING_STATUS:
        reason_codes.append("primary_ballot_access_pending_status")
    if challenge_count > ZERO:
        reason_codes.append("primary_ballot_access_active_challenge")
    if challenge_count >= HIGH_CHALLENGE_COUNT:
        reason_codes.append("primary_ballot_access_many_challenges")
    if adverse_ruling_count > ZERO:
        reason_codes.append("primary_ballot_access_adverse_ruling")
    if appeal_pending_count > ZERO:
        reason_codes.append("primary_ballot_access_appeal_pending")
    if days_until_ballot_deadline <= IMMINENT_DEADLINE_DAYS:
        reason_codes.append("primary_ballot_access_deadline_imminent")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("primary_ballot_access_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
) -> tuple[PolicyPrimaryBallotAccessReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("primary_ballot_access_digest_empty",):
        return (
            PolicyPrimaryBallotAccessReasonCodeCount(
                reason_code="primary_ballot_access_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        PolicyPrimaryBallotAccessReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[PolicyPrimaryBallotAccessObservation],
) -> tuple[PolicyPrimaryBallotAccessObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyPrimaryBallotAccessObservation:
            raise ValueError("observations must contain PolicyPrimaryBallotAccessObservation")
        _require_hard_flags(value, "observation")
        if value.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[PolicyPrimaryBallotAccessDigestRow],
) -> tuple[PolicyPrimaryBallotAccessDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PolicyPrimaryBallotAccessDigestRow:
            raise ValueError("rows must contain PolicyPrimaryBallotAccessDigestRow")
        _require_hard_flags(row, "row")
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[PolicyPrimaryBallotAccessReasonCodeCount],
) -> tuple[PolicyPrimaryBallotAccessReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not PolicyPrimaryBallotAccessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PolicyPrimaryBallotAccessReasonCodeCount",
            )
        _require_hard_flags(value, "reason_code_count")
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: PolicyPrimaryBallotAccessDigestRow) -> None:
    if row.disqualification_risk_score != _disqualification_risk_score(
        filing_status=row.filing_status,
        challenge_count=row.challenge_count,
        adverse_ruling_count=row.adverse_ruling_count,
        appeal_pending_count=row.appeal_pending_count,
        days_until_ballot_deadline=row.days_until_ballot_deadline,
    ):
        raise ValueError("disqualification_risk_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_reason_code = {
        BLOCKED_STATUS: "primary_ballot_access_blocked",
        WATCH_STATUS: "primary_ballot_access_watch",
        PASS_STATUS: "primary_ballot_access_below_threshold",
    }[row.access_status]
    if expected_reason_code not in row.reason_codes:
        raise ValueError("access_status must match reason_codes")


def _validate_report(report: PolicyPrimaryBallotAccessDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "primary_ballot_access_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.active_challenge_count != _active_challenge_count(report.rows):
        raise ValueError("active_challenge_count must match rows")
    if report.adverse_ruling_row_count != _adverse_ruling_row_count(report.rows):
        raise ValueError("adverse_ruling_row_count must match rows")
    if report.max_disqualification_risk_score != _max_row_decimal(
        report.rows,
        "disqualification_risk_score",
    ):
        raise ValueError("max_disqualification_risk_score must match rows")
    if report.average_disqualification_risk_score != _ratio(
        _sum_decimal(row.disqualification_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_disqualification_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _digest_status(rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.access_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.access_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.access_status == status))


def _active_challenge_count(
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.challenge_count > ZERO))


def _adverse_ruling_row_count(
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.adverse_ruling_count > ZERO))


def _reason_count(
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[PolicyPrimaryBallotAccessDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
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
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object, label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: PolicyPrimaryBallotAccessDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.access_status],
        -row.disqualification_risk_score,
        row.market_slug,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
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
