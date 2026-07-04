"""Pure Phase 1 policy ballot counting rule change digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_COUNTING_RULE_CHANGE_DIGEST_CONFIG_VERSION = (
    "market-research-policy-ballot-counting-rule-change-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

RULE_CHANGE_BALLOT_COUNTING = "ballot-counting"
RULE_CHANGE_CURE = "cure"
RULE_CHANGE_PROVISIONAL = "provisional"
RULE_CHANGE_MAIL_BALLOT = "mail-ballot"
RULE_CHANGE_KINDS = (
    RULE_CHANGE_BALLOT_COUNTING,
    RULE_CHANGE_CURE,
    RULE_CHANGE_PROVISIONAL,
    RULE_CHANGE_MAIL_BALLOT,
)

REASON_PREFIX = "market_research_policy_ballot_counting_rule_change_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
HIGH_IMPLEMENTATION_UNCERTAINTY_REASON = (
    f"{REASON_PREFIX}high_implementation_uncertainty"
)
HIGH_LITIGATION_RISK_REASON = f"{REASON_PREFIX}high_litigation_risk"
HIGH_MARKET_RELEVANCE_REASON = f"{REASON_PREFIX}high_market_relevance"
HIGH_COUNTING_IMPACT_REASON = f"{REASON_PREFIX}high_counting_impact"
LATE_RULE_CHANGE_REASON = f"{REASON_PREFIX}late_rule_change"
CURE_RULE_CHANGE_REASON = f"{REASON_PREFIX}cure_rule_change"
PROVISIONAL_RULE_CHANGE_REASON = f"{REASON_PREFIX}provisional_rule_change"
MAIL_BALLOT_RULE_CHANGE_REASON = f"{REASON_PREFIX}mail_ballot_rule_change"
STALE_VERIFICATION_REASON = f"{REASON_PREFIX}stale_verification"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"

REASON_CODE_SEQUENCE = (
    HIGH_IMPLEMENTATION_UNCERTAINTY_REASON,
    HIGH_LITIGATION_RISK_REASON,
    HIGH_MARKET_RELEVANCE_REASON,
    HIGH_COUNTING_IMPACT_REASON,
    LATE_RULE_CHANGE_REASON,
    CURE_RULE_CHANGE_REASON,
    PROVISIONAL_RULE_CHANGE_REASON,
    MAIL_BALLOT_RULE_CHANGE_REASON,
    STALE_VERIFICATION_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HIGH_IMPLEMENTATION_UNCERTAINTY_REASON,
    HIGH_LITIGATION_RISK_REASON,
    HIGH_MARKET_RELEVANCE_REASON,
    HIGH_COUNTING_IMPACT_REASON,
    LATE_RULE_CHANGE_REASON,
    CURE_RULE_CHANGE_REASON,
    PROVISIONAL_RULE_CHANGE_REASON,
    MAIL_BALLOT_RULE_CHANGE_REASON,
    STALE_VERIFICATION_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_market_research_policy_ballot_counting_rule_change_digest",
    STATUS_WATCH: "watch_report_only_market_research_policy_ballot_counting_rule_change_digest",
    STATUS_BLOCKED: "block_report_only_market_research_policy_ballot_counting_rule_change_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_COUNTING_RULE_CHANGE_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyBallotCountingRuleChangeDigestConfig",
    "MarketResearchPolicyBallotCountingRuleChangeDigestInputRow",
    "MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount",
    "MarketResearchPolicyBallotCountingRuleChangeDigestReport",
    "MarketResearchPolicyBallotCountingRuleChangeDigestRow",
    "build_market_research_policy_ballot_counting_rule_change_digest",
    "market_research_policy_ballot_counting_rule_change_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyBallotCountingRuleChangeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_COUNTING_RULE_CHANGE_DIGEST_CONFIG_VERSION
    )
    late_change_window_seconds: Decimal = Decimal("604800.000000")
    stale_verification_seconds: Decimal = Decimal("86400.000000")
    high_implementation_uncertainty_threshold: Decimal = Decimal("0.600000")
    high_litigation_risk_threshold: Decimal = Decimal("0.600000")
    high_market_relevance_threshold: Decimal = Decimal("0.600000")
    high_counting_impact_threshold: Decimal = Decimal("0.600000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyBallotCountingRuleChangeDigestConfig:
            raise TypeError(
                "MarketResearchPolicyBallotCountingRuleChangeDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyBallotCountingRuleChangeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_BALLOT_COUNTING_RULE_CHANGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "late_change_window_seconds",
            "stale_verification_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_implementation_uncertainty_threshold",
            "high_litigation_risk_threshold",
            "high_market_relevance_threshold",
            "high_counting_impact_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyBallotCountingRuleChangeDigestInputRow:
    research_key: str
    condition_id: str
    jurisdiction_key: str
    election_key: str
    market_key: str
    rule_change_kind: str
    public_rule_reference: str
    rule_announced_at: datetime
    election_event_at: datetime
    last_verified_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    implementation_uncertainty_score: Decimal
    litigation_risk_score: Decimal
    market_relevance_score: Decimal
    counting_impact_score: Decimal
    rule_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyBallotCountingRuleChangeDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyBallotCountingRuleChangeDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyBallotCountingRuleChangeDigestInputRow,
            "input row",
        )
        for field_name in (
            "research_key",
            "condition_id",
            "jurisdiction_key",
            "election_key",
            "market_key",
            "rule_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_rule_change_kind("rule_change_kind", self.rule_change_kind)
        _require_reference("public_rule_reference", self.public_rule_reference)
        object.__setattr__(
            self,
            "rule_announced_at",
            _as_utc("rule_announced_at", self.rule_announced_at),
        )
        object.__setattr__(
            self,
            "election_event_at",
            _as_utc("election_event_at", self.election_event_at),
        )
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if self.rule_announced_at > self.election_event_at:
            raise ValueError("rule_announced_at must not be after election_event_at")
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "implementation_uncertainty_score",
            "litigation_risk_score",
            "market_relevance_score",
            "counting_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyBallotCountingRuleChangeDigestRow:
    research_key: str
    condition_id: str
    jurisdiction_key: str
    election_key: str
    market_key: str
    rule_change_kind: str
    screening_status: str
    rule_announced_at: datetime
    election_event_at: datetime
    last_verified_at: datetime
    acknowledged_at: datetime | None
    rule_change_lead_seconds: Decimal
    seconds_until_election_event: Decimal
    verification_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    implementation_uncertainty_score: Decimal
    litigation_risk_score: Decimal
    market_relevance_score: Decimal
    counting_impact_score: Decimal
    redacted_public_rule_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyBallotCountingRuleChangeDigestRow:
            raise TypeError(
                "MarketResearchPolicyBallotCountingRuleChangeDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchPolicyBallotCountingRuleChangeDigestRow, "row")
        for field_name in (
            "research_key",
            "condition_id",
            "jurisdiction_key",
            "election_key",
            "market_key",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_rule_change_kind("rule_change_kind", self.rule_change_kind)
        _require_status("screening_status", self.screening_status)
        object.__setattr__(
            self,
            "rule_announced_at",
            _as_utc("rule_announced_at", self.rule_announced_at),
        )
        object.__setattr__(
            self,
            "election_event_at",
            _as_utc("election_event_at", self.election_event_at),
        )
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "rule_change_lead_seconds",
            _require_nonnegative_decimal(
                "rule_change_lead_seconds",
                self.rule_change_lead_seconds,
            ),
        )
        object.__setattr__(
            self,
            "seconds_until_election_event",
            _require_decimal("seconds_until_election_event", self.seconds_until_election_event),
        )
        object.__setattr__(
            self,
            "verification_age_seconds",
            _require_nonnegative_decimal(
                "verification_age_seconds",
                self.verification_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "implementation_uncertainty_score",
            "litigation_risk_score",
            "market_relevance_score",
            "counting_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_rule_reference",
            _require_redacted_reference(
                "redacted_public_rule_reference",
                self.redacted_public_rule_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    rule_change_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "rule_change_ratio",
            _require_ratio_decimal("rule_change_ratio", self.rule_change_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyBallotCountingRuleChangeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    rule_change_count: Decimal
    pass_rule_change_count: Decimal
    watch_rule_change_count: Decimal
    blocked_rule_change_count: Decimal
    cure_rule_change_count: Decimal
    provisional_rule_change_count: Decimal
    mail_ballot_rule_change_count: Decimal
    late_rule_change_count: Decimal
    high_implementation_uncertainty_count: Decimal
    high_litigation_risk_count: Decimal
    high_market_relevance_count: Decimal
    high_counting_impact_count: Decimal
    stale_verification_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    average_implementation_uncertainty_score: Decimal
    average_litigation_risk_score: Decimal
    average_market_relevance_score: Decimal
    average_counting_impact_score: Decimal
    average_source_count: Decimal
    minimum_rule_change_lead_seconds: Decimal
    rows: tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...]
    rule_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyBallotCountingRuleChangeDigestReport:
            raise TypeError(
                "MarketResearchPolicyBallotCountingRuleChangeDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyBallotCountingRuleChangeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "rule_change_count",
            "pass_rule_change_count",
            "watch_rule_change_count",
            "blocked_rule_change_count",
            "cure_rule_change_count",
            "provisional_rule_change_count",
            "mail_ballot_rule_change_count",
            "late_rule_change_count",
            "high_implementation_uncertainty_count",
            "high_litigation_risk_count",
            "high_market_relevance_count",
            "high_counting_impact_count",
            "stale_verification_count",
            "thin_source_count",
            "missing_acknowledgement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_implementation_uncertainty_score",
            "average_litigation_risk_score",
            "average_market_relevance_score",
            "average_counting_impact_score",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_rule_change_lead_seconds",
            _require_nonnegative_decimal(
                "minimum_rule_change_lead_seconds",
                self.minimum_rule_change_lead_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "rule_config_versions",
            _normalize_rule_config_versions(self.rule_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_ballot_counting_rule_change_digest(
    input_rows: Iterable[MarketResearchPolicyBallotCountingRuleChangeDigestInputRow],
    *,
    config: MarketResearchPolicyBallotCountingRuleChangeDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyBallotCountingRuleChangeDigestReport:
    if type(config) is not MarketResearchPolicyBallotCountingRuleChangeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchPolicyBallotCountingRuleChangeDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_rows
    )
    sorted_rows = _sorted_rows(rows)
    rule_change_count = _count(len(sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows, rule_change_count)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = (
            MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                rule_change_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    pass_rule_change_count = _count(
        sum(1 for row in sorted_rows if row.screening_status == STATUS_PASS),
    )
    watch_rule_change_count = _count(
        sum(1 for row in sorted_rows if row.screening_status == STATUS_WATCH),
    )
    blocked_rule_change_count = _count(
        sum(1 for row in sorted_rows if row.screening_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(sorted_rows),
        blocked_rule_change_count=blocked_rule_change_count,
        watch_rule_change_count=watch_rule_change_count,
    )

    return MarketResearchPolicyBallotCountingRuleChangeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        rule_change_count=rule_change_count,
        pass_rule_change_count=pass_rule_change_count,
        watch_rule_change_count=watch_rule_change_count,
        blocked_rule_change_count=blocked_rule_change_count,
        cure_rule_change_count=_reason_rule_change_count(
            sorted_rows,
            CURE_RULE_CHANGE_REASON,
        ),
        provisional_rule_change_count=_reason_rule_change_count(
            sorted_rows,
            PROVISIONAL_RULE_CHANGE_REASON,
        ),
        mail_ballot_rule_change_count=_reason_rule_change_count(
            sorted_rows,
            MAIL_BALLOT_RULE_CHANGE_REASON,
        ),
        late_rule_change_count=_reason_rule_change_count(
            sorted_rows,
            LATE_RULE_CHANGE_REASON,
        ),
        high_implementation_uncertainty_count=_reason_rule_change_count(
            sorted_rows,
            HIGH_IMPLEMENTATION_UNCERTAINTY_REASON,
        ),
        high_litigation_risk_count=_reason_rule_change_count(
            sorted_rows,
            HIGH_LITIGATION_RISK_REASON,
        ),
        high_market_relevance_count=_reason_rule_change_count(
            sorted_rows,
            HIGH_MARKET_RELEVANCE_REASON,
        ),
        high_counting_impact_count=_reason_rule_change_count(
            sorted_rows,
            HIGH_COUNTING_IMPACT_REASON,
        ),
        stale_verification_count=_reason_rule_change_count(
            sorted_rows,
            STALE_VERIFICATION_REASON,
        ),
        thin_source_count=_reason_rule_change_count(sorted_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_rule_change_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        average_implementation_uncertainty_score=_ratio(
            _decimal_sum(row.implementation_uncertainty_score for row in sorted_rows),
            rule_change_count,
        ),
        average_litigation_risk_score=_ratio(
            _decimal_sum(row.litigation_risk_score for row in sorted_rows),
            rule_change_count,
        ),
        average_market_relevance_score=_ratio(
            _decimal_sum(row.market_relevance_score for row in sorted_rows),
            rule_change_count,
        ),
        average_counting_impact_score=_ratio(
            _decimal_sum(row.counting_impact_score for row in sorted_rows),
            rule_change_count,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            rule_change_count,
        ),
        minimum_rule_change_lead_seconds=min(
            (row.rule_change_lead_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        rule_config_versions=_rule_config_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_ballot_counting_rule_change_digest_payload(
    report: MarketResearchPolicyBallotCountingRuleChangeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyBallotCountingRuleChangeDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchPolicyBallotCountingRuleChangeDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _row_for_input(
    row: MarketResearchPolicyBallotCountingRuleChangeDigestInputRow,
    *,
    config: MarketResearchPolicyBallotCountingRuleChangeDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyBallotCountingRuleChangeDigestRow:
    _require_not_future("rule_announced_at", row.rule_announced_at, generated_at)
    _require_not_future("last_verified_at", row.last_verified_at, generated_at)
    if row.acknowledged_at is not None:
        _require_not_future("acknowledged_at", row.acknowledged_at, generated_at)
    rule_change_age_seconds = _seconds_between(generated_at, row.rule_announced_at)
    rule_change_lead_seconds = _seconds_between(row.election_event_at, row.rule_announced_at)
    seconds_until_election_event = _seconds_between(row.election_event_at, generated_at)
    verification_age_seconds = _seconds_between(generated_at, row.last_verified_at)
    acknowledgement_lag_seconds = (
        None
        if row.acknowledged_at is None
        else _seconds_between(row.acknowledged_at, row.last_verified_at)
    )
    reason_codes = _row_reason_codes(
        rule_change_age_seconds=rule_change_age_seconds,
        verification_age_seconds=verification_age_seconds,
        source_count=row.source_count,
        implementation_uncertainty_score=row.implementation_uncertainty_score,
        litigation_risk_score=row.litigation_risk_score,
        market_relevance_score=row.market_relevance_score,
        counting_impact_score=row.counting_impact_score,
        rule_change_kind=row.rule_change_kind,
        acknowledged_at=row.acknowledged_at,
        config=config,
    )
    return MarketResearchPolicyBallotCountingRuleChangeDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        jurisdiction_key=row.jurisdiction_key,
        election_key=row.election_key,
        market_key=row.market_key,
        rule_change_kind=row.rule_change_kind,
        screening_status=_row_status(reason_codes),
        rule_announced_at=row.rule_announced_at,
        election_event_at=row.election_event_at,
        last_verified_at=row.last_verified_at,
        acknowledged_at=row.acknowledged_at,
        rule_change_lead_seconds=rule_change_lead_seconds,
        seconds_until_election_event=seconds_until_election_event,
        verification_age_seconds=verification_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        implementation_uncertainty_score=row.implementation_uncertainty_score,
        litigation_risk_score=row.litigation_risk_score,
        market_relevance_score=row.market_relevance_score,
        counting_impact_score=row.counting_impact_score,
        redacted_public_rule_reference=_redact_reference(row.public_rule_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    rule_change_age_seconds: Decimal,
    verification_age_seconds: Decimal,
    source_count: Decimal,
    implementation_uncertainty_score: Decimal,
    litigation_risk_score: Decimal,
    market_relevance_score: Decimal,
    counting_impact_score: Decimal,
    rule_change_kind: str,
    acknowledged_at: datetime | None,
    config: MarketResearchPolicyBallotCountingRuleChangeDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if implementation_uncertainty_score >= config.high_implementation_uncertainty_threshold:
        reasons.append(HIGH_IMPLEMENTATION_UNCERTAINTY_REASON)
    if litigation_risk_score >= config.high_litigation_risk_threshold:
        reasons.append(HIGH_LITIGATION_RISK_REASON)
    if market_relevance_score >= config.high_market_relevance_threshold:
        reasons.append(HIGH_MARKET_RELEVANCE_REASON)
    if counting_impact_score >= config.high_counting_impact_threshold:
        reasons.append(HIGH_COUNTING_IMPACT_REASON)
    if rule_change_age_seconds <= config.late_change_window_seconds:
        reasons.append(LATE_RULE_CHANGE_REASON)
    if rule_change_kind == RULE_CHANGE_CURE:
        reasons.append(CURE_RULE_CHANGE_REASON)
    elif rule_change_kind == RULE_CHANGE_PROVISIONAL:
        reasons.append(PROVISIONAL_RULE_CHANGE_REASON)
    elif rule_change_kind == RULE_CHANGE_MAIL_BALLOT:
        reasons.append(MAIL_BALLOT_RULE_CHANGE_REASON)
    if verification_age_seconds > config.stale_verification_seconds:
        reasons.append(STALE_VERIFICATION_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if acknowledged_at is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(reasons, sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if (
        LATE_RULE_CHANGE_REASON in reason_codes
        and HIGH_MARKET_RELEVANCE_REASON in reason_codes
        and HIGH_COUNTING_IMPACT_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_rule_change_count: Decimal,
    watch_rule_change_count: Decimal,
) -> str:
    if not has_inputs or blocked_rule_change_count > ZERO:
        return STATUS_BLOCKED
    if watch_rule_change_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _sorted_rows(
    rows: tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...],
) -> tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.screening_status),
                _blocked_reason_rank(row.reason_codes),
                row.rule_change_lead_seconds,
                -row.counting_impact_score,
                -row.market_relevance_score,
                -row.litigation_risk_score,
                row.jurisdiction_key,
                row.research_key,
            ),
        ),
    )


def _blocked_reason_rank(reason_codes: tuple[str, ...]) -> int:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return 0
    if (
        LATE_RULE_CHANGE_REASON in reason_codes
        and HIGH_MARKET_RELEVANCE_REASON in reason_codes
        and HIGH_COUNTING_IMPACT_REASON in reason_codes
    ):
        return 1
    return 2


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...],
    rule_change_count: Decimal,
) -> tuple[MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            rule_change_ratio=_ratio(count, rule_change_count),
        )
        for reason_code, count in sorted(
            (
                (
                    reason_code,
                    _reason_rule_change_count(rows, reason_code),
                )
                for reason_code in REASON_CODE_SEQUENCE
                if any(reason_code in row.reason_codes for row in rows)
            ),
            key=lambda item: _reason_rank(item[0]),
        )
    )


def _reason_rule_change_count(
    rows: tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _rule_config_versions(
    rows: tuple[MarketResearchPolicyBallotCountingRuleChangeDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    versions = {row.condition_id: row.rule_config_version for row in rows}
    return tuple(sorted(versions.items()))


def _normalize_input_rows(
    input_rows: Iterable[MarketResearchPolicyBallotCountingRuleChangeDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchPolicyBallotCountingRuleChangeDigestInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable of input rows")
    try:
        rows = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable of input rows") from exc
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPolicyBallotCountingRuleChangeDigestInputRow:
            raise ValueError(
                "input_rows must contain "
                "MarketResearchPolicyBallotCountingRuleChangeDigestInputRow values",
            )
        _require_not_future("rule_announced_at", row.rule_announced_at, generated_at)
        _require_not_future("last_verified_at", row.last_verified_at, generated_at)
        if row.acknowledged_at is not None:
            _require_not_future("acknowledged_at", row.acknowledged_at, generated_at)
        if row.condition_id in seen_condition_ids:
            raise ValueError("condition_id values must be unique")
        seen_condition_ids.add(row.condition_id)
    return rows


def _normalize_rows(
    rows: Iterable[MarketResearchPolicyBallotCountingRuleChangeDigestRow],
) -> tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not MarketResearchPolicyBallotCountingRuleChangeDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicyBallotCountingRuleChangeDigestRow values",
            )
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must use deterministic rule change sort")
    return normalized


def _normalize_rule_config_versions(
    values: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rule_config_versions must be an iterable")
    try:
        normalized = tuple(tuple(item) for item in values)
    except TypeError as exc:
        raise ValueError("rule_config_versions must be an iterable") from exc
    if normalized != tuple(sorted(normalized)):
        raise ValueError("rule_config_versions must be sorted")
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("rule_config_versions entries must have two values")
        condition_id, config_version = item
        _require_public_string("rule_config_versions", condition_id)
        _require_public_string("rule_config_versions", config_version)
        if condition_id in seen:
            raise ValueError("rule_config_versions must have unique condition ids")
        seen.add(condition_id)
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount],
) -> tuple[MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount values",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(item.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda item: _reason_rank(item.reason_code))):
        raise ValueError("reason_code_counts must use deterministic reason code sort")
    return normalized


def _normalize_reason_codes(
    values: Iterable[str],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must include at least one code")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes include an unknown code")
    return tuple(sorted(normalized, key=lambda reason_code: sequence.index(reason_code)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_rule_change_kind(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RULE_CHANGE_KINDS:
        raise ValueError(f"{field_name} must be a supported rule change kind")


def _validate_row(row: MarketResearchPolicyBallotCountingRuleChangeDigestRow) -> None:
    if row.screening_status != _row_status(row.reason_codes):
        raise ValueError("screening_status must match reason_codes")
    if (row.acknowledged_at is None) != (
        MISSING_ACKNOWLEDGEMENT_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match acknowledgement state")
    if (row.rule_change_kind == RULE_CHANGE_CURE) != (
        CURE_RULE_CHANGE_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match cure rule change state")
    if (row.rule_change_kind == RULE_CHANGE_PROVISIONAL) != (
        PROVISIONAL_RULE_CHANGE_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match provisional rule change state")
    if (row.rule_change_kind == RULE_CHANGE_MAIL_BALLOT) != (
        MAIL_BALLOT_RULE_CHANGE_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match mail ballot rule change state")
    if row.rule_announced_at > row.election_event_at:
        raise ValueError("rule_announced_at must not be after election_event_at")
    if row.rule_change_lead_seconds != _seconds_between(
        row.election_event_at,
        row.rule_announced_at,
    ):
        raise ValueError("rule_change_lead_seconds must match datetimes")


def _validate_report(report: MarketResearchPolicyBallotCountingRuleChangeDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.rule_change_count != _count(len(report.rows)):
        raise ValueError("rule_change_count must match rows")
    if report.pass_rule_change_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_rule_change_count must match rows")
    if report.watch_rule_change_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_rule_change_count must match rows")
    if report.blocked_rule_change_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_rule_change_count must match rows")
    if report.cure_rule_change_count != _reason_rule_change_count(
        report.rows,
        CURE_RULE_CHANGE_REASON,
    ):
        raise ValueError("cure_rule_change_count must match rows")
    if report.provisional_rule_change_count != _reason_rule_change_count(
        report.rows,
        PROVISIONAL_RULE_CHANGE_REASON,
    ):
        raise ValueError("provisional_rule_change_count must match rows")
    if report.mail_ballot_rule_change_count != _reason_rule_change_count(
        report.rows,
        MAIL_BALLOT_RULE_CHANGE_REASON,
    ):
        raise ValueError("mail_ballot_rule_change_count must match rows")
    if report.late_rule_change_count != _reason_rule_change_count(
        report.rows,
        LATE_RULE_CHANGE_REASON,
    ):
        raise ValueError("late_rule_change_count must match rows")
    if report.high_implementation_uncertainty_count != _reason_rule_change_count(
        report.rows,
        HIGH_IMPLEMENTATION_UNCERTAINTY_REASON,
    ):
        raise ValueError("high_implementation_uncertainty_count must match rows")
    if report.high_litigation_risk_count != _reason_rule_change_count(
        report.rows,
        HIGH_LITIGATION_RISK_REASON,
    ):
        raise ValueError("high_litigation_risk_count must match rows")
    if report.high_market_relevance_count != _reason_rule_change_count(
        report.rows,
        HIGH_MARKET_RELEVANCE_REASON,
    ):
        raise ValueError("high_market_relevance_count must match rows")
    if report.high_counting_impact_count != _reason_rule_change_count(
        report.rows,
        HIGH_COUNTING_IMPACT_REASON,
    ):
        raise ValueError("high_counting_impact_count must match rows")
    if report.stale_verification_count != _reason_rule_change_count(
        report.rows,
        STALE_VERIFICATION_REASON,
    ):
        raise ValueError("stale_verification_count must match rows")
    if report.thin_source_count != _reason_rule_change_count(report.rows, THIN_SOURCES_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.missing_acknowledgement_count != _reason_rule_change_count(
        report.rows,
        MISSING_ACKNOWLEDGEMENT_REASON,
    ):
        raise ValueError("missing_acknowledgement_count must match rows")
    if report.average_implementation_uncertainty_score != _ratio(
        _decimal_sum(row.implementation_uncertainty_score for row in report.rows),
        report.rule_change_count,
    ):
        raise ValueError("average_implementation_uncertainty_score must match rows")
    if report.average_litigation_risk_score != _ratio(
        _decimal_sum(row.litigation_risk_score for row in report.rows),
        report.rule_change_count,
    ):
        raise ValueError("average_litigation_risk_score must match rows")
    if report.average_market_relevance_score != _ratio(
        _decimal_sum(row.market_relevance_score for row in report.rows),
        report.rule_change_count,
    ):
        raise ValueError("average_market_relevance_score must match rows")
    if report.average_counting_impact_score != _ratio(
        _decimal_sum(row.counting_impact_score for row in report.rows),
        report.rule_change_count,
    ):
        raise ValueError("average_counting_impact_score must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.rule_change_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.minimum_rule_change_lead_seconds != min(
        (row.rule_change_lead_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("minimum_rule_change_lead_seconds must match rows")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_rule_change_count=report.blocked_rule_change_count,
        watch_rule_change_count=report.watch_rule_change_count,
    ):
        raise ValueError("digest_status must match rows")
    expected_counts = _reason_code_counts(report.rows, report.rule_change_count)
    if not report.rows:
        expected_counts = (
            MarketResearchPolicyBallotCountingRuleChangeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                rule_change_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in expected_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _status_count(
    rows: tuple[MarketResearchPolicyBallotCountingRuleChangeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.screening_status == status))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_micros = Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
    total_micros += Decimal(delta.microseconds)
    return _quantize(total_micros / MICROSECONDS_PER_SECOND)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include timezone")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be in the future")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = str(value).lower()
    bad_fragments = (
        "".join(("cre", "dential")),
        "".join(("pri", "vate")),
        "token",
        "secret",
        "0x",
    )
    if any(fragment in lowered for fragment in bad_fragments):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and trimmed")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and trimmed")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_status(field_name: str, value: object) -> None:
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if not str(value).startswith("sha256:") or len(str(value)) != 19:
        raise ValueError(f"{field_name} must be redacted")
    return str(value)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _redact_reference(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _reason_rank(reason: str) -> int:
    if reason not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return REASON_CODE_SEQUENCE.index(reason)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _require_nonnegative_count_decimal("count", value)
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("JSON payload must not contain floats")
    return value
