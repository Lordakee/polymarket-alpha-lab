"""Pure Phase 1 policy emergency rule stay-window digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION = (
    "market-research-policy-emergency-rule-stay-window-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
REPORT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

STAY_MOTION_NOT_FILED = "not_filed"
STAY_MOTION_ANTICIPATED = "anticipated"
STAY_MOTION_FILED = "filed"
STAY_MOTION_GRANTED = "granted"
STAY_MOTION_DENIED = "denied"
STAY_MOTION_UNKNOWN = "unknown"
STAY_MOTION_STATUSES = (
    STAY_MOTION_NOT_FILED,
    STAY_MOTION_ANTICIPATED,
    STAY_MOTION_FILED,
    STAY_MOTION_GRANTED,
    STAY_MOTION_DENIED,
    STAY_MOTION_UNKNOWN,
)

REASON_PREFIX = "market_research_policy_emergency_rule_stay_window_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
HIGH_INJUNCTION_PROBABILITY_REASON = f"{REASON_PREFIX}high_injunction_probability"
EFFECTIVE_DATE_BLOCK_REASON = f"{REASON_PREFIX}effective_date_block"
RESPONSE_DEADLINE_BLOCK_REASON = f"{REASON_PREFIX}response_deadline_block"
STAY_MOTION_GRANTED_REASON = f"{REASON_PREFIX}stay_motion_granted"
THIN_LEGAL_SOURCE_QUORUM_REASON = f"{REASON_PREFIX}thin_legal_source_quorum"
STALE_DOCKET_REASON = f"{REASON_PREFIX}stale_docket"
UPSTREAM_BLOCK_REASON = f"{REASON_PREFIX}upstream_block"
RISK_SCORE_BLOCK_REASON = f"{REASON_PREFIX}risk_score_block"
ELEVATED_INJUNCTION_PROBABILITY_REASON = (
    f"{REASON_PREFIX}elevated_injunction_probability"
)
EFFECTIVE_DATE_WATCH_REASON = f"{REASON_PREFIX}effective_date_watch"
RESPONSE_DEADLINE_WATCH_REASON = f"{REASON_PREFIX}response_deadline_watch"
STAY_MOTION_FILED_REASON = f"{REASON_PREFIX}stay_motion_filed"
STAY_MOTION_PENDING_REASON = f"{REASON_PREFIX}stay_motion_pending"
BROAD_AFFECTED_JURISDICTION_REASON = f"{REASON_PREFIX}broad_affected_jurisdiction"
UPSTREAM_WATCH_REASON = f"{REASON_PREFIX}upstream_watch"
RISK_SCORE_WATCH_REASON = f"{REASON_PREFIX}risk_score_watch"
PASS_REASON = f"{REASON_PREFIX}pass"

REASON_CODE_SEQUENCE = (
    HIGH_INJUNCTION_PROBABILITY_REASON,
    EFFECTIVE_DATE_BLOCK_REASON,
    RESPONSE_DEADLINE_BLOCK_REASON,
    STAY_MOTION_GRANTED_REASON,
    THIN_LEGAL_SOURCE_QUORUM_REASON,
    STALE_DOCKET_REASON,
    UPSTREAM_BLOCK_REASON,
    RISK_SCORE_BLOCK_REASON,
    ELEVATED_INJUNCTION_PROBABILITY_REASON,
    EFFECTIVE_DATE_WATCH_REASON,
    RESPONSE_DEADLINE_WATCH_REASON,
    STAY_MOTION_FILED_REASON,
    STAY_MOTION_PENDING_REASON,
    BROAD_AFFECTED_JURISDICTION_REASON,
    UPSTREAM_WATCH_REASON,
    RISK_SCORE_WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code != NO_INPUTS_REASON
)
BLOCK_REASON_CODES = (
    HIGH_INJUNCTION_PROBABILITY_REASON,
    EFFECTIVE_DATE_BLOCK_REASON,
    RESPONSE_DEADLINE_BLOCK_REASON,
    STAY_MOTION_GRANTED_REASON,
    UPSTREAM_BLOCK_REASON,
    RISK_SCORE_BLOCK_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: (
        "pass_report_only_market_research_policy_emergency_rule_stay_window_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_policy_emergency_rule_stay_window_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_policy_emergency_rule_stay_window_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
MICROSECONDS_PER_DAY = Decimal("86400000000")

PROBABILITY_WEIGHT = Decimal("0.400000")
EFFECTIVE_WINDOW_WEIGHT = Decimal("0.200000")
RESPONSE_WINDOW_WEIGHT = Decimal("0.150000")
STAY_MOTION_WEIGHT = Decimal("0.100000")
SOURCE_QUORUM_WEIGHT = Decimal("0.075000")
DOCKET_FRESHNESS_WEIGHT = Decimal("0.050000")
JURISDICTION_BREADTH_WEIGHT = Decimal("0.025000")
STAY_MOTION_FILED_SCORE = Decimal("0.700000")
STAY_MOTION_PENDING_SCORE = Decimal("0.400000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = (
    _join_parts("au", "th"),
    _join_parts("bro", "ker"),
    _join_parts("sig", "ning"),
    _join_parts("sub", "mit"),
    _join_parts("can", "cel"),
    _join_parts("wal", "let"),
    _join_parts("acc", "ount"),
    _join_parts("pri", "vate"),
    _join_parts("sec", "ret"),
    _join_parts("to", "ken"),
    _join_parts("cred", "ential"),
    _join_parts("or", "der"),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyEmergencyRuleStayWindowDigestConfig",
    "MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow",
    "MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount",
    "MarketResearchPolicyEmergencyRuleStayWindowDigestReport",
    "MarketResearchPolicyEmergencyRuleStayWindowDigestRow",
    "MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount",
    "build_market_research_policy_emergency_rule_stay_window_digest",
    "market_research_policy_emergency_rule_stay_window_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyEmergencyRuleStayWindowDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION
    )
    effective_date_watch_days: Decimal = Decimal("14.000000")
    effective_date_block_days: Decimal = Decimal("3.000000")
    response_deadline_watch_days: Decimal = Decimal("7.000000")
    response_deadline_block_days: Decimal = Decimal("1.000000")
    max_docket_freshness_age_days: Decimal = Decimal("2.000000")
    legal_source_quorum_count: Decimal = Decimal("2.000000")
    broad_affected_jurisdiction_count: Decimal = Decimal("3.000000")
    injunction_probability_watch_threshold: Decimal = Decimal("0.350000")
    injunction_probability_block_threshold: Decimal = Decimal("0.650000")
    risk_score_watch_threshold: Decimal = Decimal("0.350000")
    risk_score_block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyEmergencyRuleStayWindowDigestConfig:
            raise TypeError(
                "MarketResearchPolicyEmergencyRuleStayWindowDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyEmergencyRuleStayWindowDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "effective_date_watch_days",
            "effective_date_block_days",
            "response_deadline_watch_days",
            "response_deadline_block_days",
            "max_docket_freshness_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "legal_source_quorum_count",
            "broad_affected_jurisdiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "injunction_probability_watch_threshold",
            "injunction_probability_block_threshold",
            "risk_score_watch_threshold",
            "risk_score_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.effective_date_block_days > self.effective_date_watch_days:
            raise ValueError(
                "effective_date_block_days must be no greater than "
                "effective_date_watch_days",
            )
        if self.response_deadline_block_days > self.response_deadline_watch_days:
            raise ValueError(
                "response_deadline_block_days must be no greater than "
                "response_deadline_watch_days",
            )
        if (
            self.injunction_probability_watch_threshold
            > self.injunction_probability_block_threshold
        ):
            raise ValueError(
                "injunction_probability_block_threshold must be at least "
                "injunction_probability_watch_threshold",
            )
        if self.risk_score_watch_threshold > self.risk_score_block_threshold:
            raise ValueError(
                "risk_score_block_threshold must be at least risk_score_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow:
    research_key: str
    market_slug: str
    agency_court_source_id: str
    emergency_rule_reference: str
    effective_at: datetime
    response_deadline_at: datetime
    docket_checked_at: datetime
    stay_motion_status: str
    injunction_probability_proxy: Decimal
    affected_jurisdiction_count: Decimal
    legal_source_count: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow",
            )
        for field_name in (
            "research_key",
            "market_slug",
            "agency_court_source_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("emergency_rule_reference", self.emergency_rule_reference)
        object.__setattr__(self, "effective_at", _as_utc("effective_at", self.effective_at))
        object.__setattr__(
            self,
            "response_deadline_at",
            _as_utc("response_deadline_at", self.response_deadline_at),
        )
        object.__setattr__(
            self,
            "docket_checked_at",
            _as_utc("docket_checked_at", self.docket_checked_at),
        )
        _require_stay_motion_status("stay_motion_status", self.stay_motion_status)
        object.__setattr__(
            self,
            "injunction_probability_proxy",
            _require_ratio_decimal(
                "injunction_probability_proxy",
                self.injunction_probability_proxy,
            ),
        )
        for field_name in (
            "affected_jurisdiction_count",
            "legal_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyEmergencyRuleStayWindowDigestRow:
    research_key: str
    market_slug: str
    agency_court_source_id: str
    effective_at: datetime
    response_deadline_at: datetime
    docket_checked_at: datetime
    days_until_effective_date: Decimal
    days_until_response_deadline: Decimal
    docket_freshness_age_days: Decimal
    stay_motion_status: str
    injunction_probability_proxy: Decimal
    affected_jurisdiction_count: Decimal
    legal_source_count: Decimal
    legal_source_quorum_count: Decimal
    stay_window_risk_score: Decimal
    row_status: str
    redacted_emergency_rule_reference: str
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyEmergencyRuleStayWindowDigestRow:
            raise TypeError(
                "MarketResearchPolicyEmergencyRuleStayWindowDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyEmergencyRuleStayWindowDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestRow",
            )
        for field_name in (
            "research_key",
            "market_slug",
            "agency_court_source_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "effective_at", _as_utc("effective_at", self.effective_at))
        object.__setattr__(
            self,
            "response_deadline_at",
            _as_utc("response_deadline_at", self.response_deadline_at),
        )
        object.__setattr__(
            self,
            "docket_checked_at",
            _as_utc("docket_checked_at", self.docket_checked_at),
        )
        for field_name in (
            "days_until_effective_date",
            "days_until_response_deadline",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "docket_freshness_age_days",
            _require_nonnegative_decimal(
                "docket_freshness_age_days",
                self.docket_freshness_age_days,
            ),
        )
        _require_stay_motion_status("stay_motion_status", self.stay_motion_status)
        object.__setattr__(
            self,
            "injunction_probability_proxy",
            _require_ratio_decimal(
                "injunction_probability_proxy",
                self.injunction_probability_proxy,
            ),
        )
        for field_name in (
            "affected_jurisdiction_count",
            "legal_source_count",
            "legal_source_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stay_window_risk_score",
            _require_ratio_decimal(
                "stay_window_risk_score",
                self.stay_window_risk_score,
            ),
        )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "redacted_emergency_rule_reference",
            _require_redacted_reference(
                "redacted_emergency_rule_reference",
                self.redacted_emergency_rule_reference,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    rule_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "rule_ratio",
            _require_ratio_decimal("rule_ratio", self.rule_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount:
    upstream_reason_code: str
    count: Decimal
    rule_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls
            is not MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount
        ):
            raise TypeError(
                "MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount
        ):
            raise ValueError(
                "upstream reason code count must be exactly "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount",
            )
        _require_upstream_reason_code(
            "upstream_reason_code",
            self.upstream_reason_code,
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "rule_ratio",
            _require_ratio_decimal("rule_ratio", self.rule_ratio),
        )
        _require_hard_flags("upstream reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyEmergencyRuleStayWindowDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    rule_count: Decimal
    pass_rule_count: Decimal
    watch_rule_count: Decimal
    blocked_rule_count: Decimal
    stay_motion_filed_count: Decimal
    stay_motion_granted_count: Decimal
    high_injunction_probability_count: Decimal
    elevated_injunction_probability_count: Decimal
    effective_date_block_count: Decimal
    effective_date_watch_count: Decimal
    response_deadline_block_count: Decimal
    response_deadline_watch_count: Decimal
    stale_docket_count: Decimal
    thin_legal_source_quorum_count: Decimal
    broad_affected_jurisdiction_count: Decimal
    upstream_block_count: Decimal
    upstream_watch_count: Decimal
    risk_score_block_count: Decimal
    risk_score_watch_count: Decimal
    average_stay_window_risk_score: Decimal
    max_stay_window_risk_score: Decimal
    rows: tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount,
        ...,
    ]
    upstream_reason_code_counts: tuple[
        MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyEmergencyRuleStayWindowDigestReport:
            raise TypeError(
                "MarketResearchPolicyEmergencyRuleStayWindowDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyEmergencyRuleStayWindowDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("next_step", self.next_step)
        for field_name in (
            "rule_count",
            "pass_rule_count",
            "watch_rule_count",
            "blocked_rule_count",
            "stay_motion_filed_count",
            "stay_motion_granted_count",
            "high_injunction_probability_count",
            "elevated_injunction_probability_count",
            "effective_date_block_count",
            "effective_date_watch_count",
            "response_deadline_block_count",
            "response_deadline_watch_count",
            "stale_docket_count",
            "thin_legal_source_quorum_count",
            "broad_affected_jurisdiction_count",
            "upstream_block_count",
            "upstream_watch_count",
            "risk_score_block_count",
            "risk_score_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_stay_window_risk_score",
            "max_stay_window_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "upstream_reason_code_counts",
            _normalize_upstream_reason_code_counts(self.upstream_reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_emergency_rule_stay_window_digest(
    input_rows: tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow, ...]
    | list[MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow],
    *,
    config: MarketResearchPolicyEmergencyRuleStayWindowDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyEmergencyRuleStayWindowDigestReport:
    if type(config) is not MarketResearchPolicyEmergencyRuleStayWindowDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchPolicyEmergencyRuleStayWindowDigestConfig",
        )
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(
        _row_for_input(input_row, config=config, generated_at=report_time)
        for input_row in normalized_inputs
    )
    ranked_rows = _ranked_rows(built_rows)
    rule_count = _count_from_int(len(ranked_rows))
    pass_rule_count = _reason_row_count(ranked_rows, PASS_REASON)
    watch_rule_count = _count_from_int(
        sum(1 for row in ranked_rows if row.row_status == STATUS_WATCH),
    )
    blocked_rule_count = _count_from_int(
        sum(1 for row in ranked_rows if row.row_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows, rule_count)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                rule_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_rule_count=blocked_rule_count,
        watch_rule_count=watch_rule_count,
    )
    return MarketResearchPolicyEmergencyRuleStayWindowDigestReport(
        generated_at=report_time,
        config_version=config.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        rule_count=rule_count,
        pass_rule_count=pass_rule_count,
        watch_rule_count=watch_rule_count,
        blocked_rule_count=blocked_rule_count,
        stay_motion_filed_count=_reason_row_count(
            ranked_rows,
            STAY_MOTION_FILED_REASON,
        ),
        stay_motion_granted_count=_reason_row_count(
            ranked_rows,
            STAY_MOTION_GRANTED_REASON,
        ),
        high_injunction_probability_count=_reason_row_count(
            ranked_rows,
            HIGH_INJUNCTION_PROBABILITY_REASON,
        ),
        elevated_injunction_probability_count=_reason_row_count(
            ranked_rows,
            ELEVATED_INJUNCTION_PROBABILITY_REASON,
        ),
        effective_date_block_count=_reason_row_count(
            ranked_rows,
            EFFECTIVE_DATE_BLOCK_REASON,
        ),
        effective_date_watch_count=_reason_row_count(
            ranked_rows,
            EFFECTIVE_DATE_WATCH_REASON,
        ),
        response_deadline_block_count=_reason_row_count(
            ranked_rows,
            RESPONSE_DEADLINE_BLOCK_REASON,
        ),
        response_deadline_watch_count=_reason_row_count(
            ranked_rows,
            RESPONSE_DEADLINE_WATCH_REASON,
        ),
        stale_docket_count=_reason_row_count(ranked_rows, STALE_DOCKET_REASON),
        thin_legal_source_quorum_count=_reason_row_count(
            ranked_rows,
            THIN_LEGAL_SOURCE_QUORUM_REASON,
        ),
        broad_affected_jurisdiction_count=_reason_row_count(
            ranked_rows,
            BROAD_AFFECTED_JURISDICTION_REASON,
        ),
        upstream_block_count=_reason_row_count(ranked_rows, UPSTREAM_BLOCK_REASON),
        upstream_watch_count=_reason_row_count(ranked_rows, UPSTREAM_WATCH_REASON),
        risk_score_block_count=_reason_row_count(ranked_rows, RISK_SCORE_BLOCK_REASON),
        risk_score_watch_count=_reason_row_count(ranked_rows, RISK_SCORE_WATCH_REASON),
        average_stay_window_risk_score=_ratio(
            _decimal_sum(row.stay_window_risk_score for row in ranked_rows),
            rule_count,
        ),
        max_stay_window_risk_score=max(
            (row.stay_window_risk_score for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        upstream_reason_code_counts=_upstream_reason_code_counts(
            ranked_rows,
            rule_count,
        ),
        reason_codes=reason_codes,
    )


def market_research_policy_emergency_rule_stay_window_digest_payload(
    report: MarketResearchPolicyEmergencyRuleStayWindowDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyEmergencyRuleStayWindowDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchPolicyEmergencyRuleStayWindowDigestReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", asdict(report))
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _row_for_input(
    row: MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow,
    *,
    config: MarketResearchPolicyEmergencyRuleStayWindowDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyEmergencyRuleStayWindowDigestRow:
    days_until_effective_date = _days_between(row.effective_at, generated_at)
    days_until_response_deadline = _days_between(
        row.response_deadline_at,
        generated_at,
    )
    docket_freshness_age_days = _days_between(generated_at, row.docket_checked_at)
    risk_score = _stay_window_risk_score(
        days_until_effective_date=days_until_effective_date,
        days_until_response_deadline=days_until_response_deadline,
        docket_freshness_age_days=docket_freshness_age_days,
        stay_motion_status=row.stay_motion_status,
        injunction_probability_proxy=row.injunction_probability_proxy,
        affected_jurisdiction_count=row.affected_jurisdiction_count,
        legal_source_count=row.legal_source_count,
        legal_source_quorum_count=config.legal_source_quorum_count,
        config=config,
    )
    reason_codes = _row_reason_codes(
        days_until_effective_date=days_until_effective_date,
        days_until_response_deadline=days_until_response_deadline,
        docket_freshness_age_days=docket_freshness_age_days,
        stay_motion_status=row.stay_motion_status,
        injunction_probability_proxy=row.injunction_probability_proxy,
        affected_jurisdiction_count=row.affected_jurisdiction_count,
        legal_source_count=row.legal_source_count,
        legal_source_quorum_count=config.legal_source_quorum_count,
        stay_window_risk_score=risk_score,
        upstream_reason_codes=row.upstream_reason_codes,
        config=config,
    )
    return MarketResearchPolicyEmergencyRuleStayWindowDigestRow(
        research_key=row.research_key,
        market_slug=row.market_slug,
        agency_court_source_id=row.agency_court_source_id,
        effective_at=row.effective_at,
        response_deadline_at=row.response_deadline_at,
        docket_checked_at=row.docket_checked_at,
        days_until_effective_date=days_until_effective_date,
        days_until_response_deadline=days_until_response_deadline,
        docket_freshness_age_days=docket_freshness_age_days,
        stay_motion_status=row.stay_motion_status,
        injunction_probability_proxy=row.injunction_probability_proxy,
        affected_jurisdiction_count=row.affected_jurisdiction_count,
        legal_source_count=row.legal_source_count,
        legal_source_quorum_count=config.legal_source_quorum_count,
        stay_window_risk_score=risk_score,
        row_status=_row_status(reason_codes),
        redacted_emergency_rule_reference=_redacted_reference(
            row.emergency_rule_reference,
        ),
        upstream_reason_codes=row.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("input rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestInputRow values",
            )
        _require_hard_flags("input row", row)
        _require_not_future("docket_checked_at", row.docket_checked_at, generated_at)
        key = (row.market_slug, row.agency_court_source_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate source windows")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    days_until_effective_date: Decimal,
    days_until_response_deadline: Decimal,
    docket_freshness_age_days: Decimal,
    stay_motion_status: str,
    injunction_probability_proxy: Decimal,
    affected_jurisdiction_count: Decimal,
    legal_source_count: Decimal,
    legal_source_quorum_count: Decimal,
    stay_window_risk_score: Decimal,
    upstream_reason_codes: tuple[str, ...],
    config: MarketResearchPolicyEmergencyRuleStayWindowDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if injunction_probability_proxy >= config.injunction_probability_block_threshold:
        reason_codes.append(HIGH_INJUNCTION_PROBABILITY_REASON)
    elif injunction_probability_proxy >= config.injunction_probability_watch_threshold:
        reason_codes.append(ELEVATED_INJUNCTION_PROBABILITY_REASON)
    if days_until_effective_date <= config.effective_date_block_days:
        reason_codes.append(EFFECTIVE_DATE_BLOCK_REASON)
    elif days_until_effective_date <= config.effective_date_watch_days:
        reason_codes.append(EFFECTIVE_DATE_WATCH_REASON)
    if days_until_response_deadline <= config.response_deadline_block_days:
        reason_codes.append(RESPONSE_DEADLINE_BLOCK_REASON)
    elif days_until_response_deadline <= config.response_deadline_watch_days:
        reason_codes.append(RESPONSE_DEADLINE_WATCH_REASON)
    if stay_motion_status == STAY_MOTION_GRANTED:
        reason_codes.append(STAY_MOTION_GRANTED_REASON)
    elif stay_motion_status == STAY_MOTION_FILED:
        reason_codes.append(STAY_MOTION_FILED_REASON)
    elif stay_motion_status in (STAY_MOTION_ANTICIPATED, STAY_MOTION_UNKNOWN):
        reason_codes.append(STAY_MOTION_PENDING_REASON)
    if legal_source_count < legal_source_quorum_count:
        reason_codes.append(THIN_LEGAL_SOURCE_QUORUM_REASON)
    if docket_freshness_age_days > config.max_docket_freshness_age_days:
        reason_codes.append(STALE_DOCKET_REASON)
    if affected_jurisdiction_count >= config.broad_affected_jurisdiction_count:
        reason_codes.append(BROAD_AFFECTED_JURISDICTION_REASON)
    if _has_upstream_block(upstream_reason_codes):
        reason_codes.append(UPSTREAM_BLOCK_REASON)
    if _has_upstream_watch(upstream_reason_codes):
        reason_codes.append(UPSTREAM_WATCH_REASON)
    if stay_window_risk_score >= config.risk_score_block_threshold:
        reason_codes.append(RISK_SCORE_BLOCK_REASON)
    elif stay_window_risk_score >= config.risk_score_watch_threshold:
        reason_codes.append(RISK_SCORE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(reason_codes, sequence=ROW_REASON_CODE_SEQUENCE)


def _stay_window_risk_score(
    *,
    days_until_effective_date: Decimal,
    days_until_response_deadline: Decimal,
    docket_freshness_age_days: Decimal,
    stay_motion_status: str,
    injunction_probability_proxy: Decimal,
    affected_jurisdiction_count: Decimal,
    legal_source_count: Decimal,
    legal_source_quorum_count: Decimal,
    config: MarketResearchPolicyEmergencyRuleStayWindowDigestConfig,
) -> Decimal:
    raw_score = (
        (injunction_probability_proxy * PROBABILITY_WEIGHT)
        + (
            _window_component(
                days_until_effective_date,
                block_days=config.effective_date_block_days,
                watch_days=config.effective_date_watch_days,
            )
            * EFFECTIVE_WINDOW_WEIGHT
        )
        + (
            _window_component(
                days_until_response_deadline,
                block_days=config.response_deadline_block_days,
                watch_days=config.response_deadline_watch_days,
            )
            * RESPONSE_WINDOW_WEIGHT
        )
        + (_stay_motion_component(stay_motion_status) * STAY_MOTION_WEIGHT)
        + (
            _source_quorum_component(
                legal_source_count,
                legal_source_quorum_count,
            )
            * SOURCE_QUORUM_WEIGHT
        )
        + (
            _docket_freshness_component(
                docket_freshness_age_days,
                config.max_docket_freshness_age_days,
            )
            * DOCKET_FRESHNESS_WEIGHT
        )
        + (
            _jurisdiction_breadth_component(
                affected_jurisdiction_count,
                config.broad_affected_jurisdiction_count,
            )
            * JURISDICTION_BREADTH_WEIGHT
        )
    )
    return min(_quantize(raw_score), ONE)


def _window_component(
    value_days: Decimal,
    *,
    block_days: Decimal,
    watch_days: Decimal,
) -> Decimal:
    if value_days <= block_days:
        return ONE
    if value_days <= watch_days:
        return HALF
    return ZERO


def _stay_motion_component(stay_motion_status: str) -> Decimal:
    if stay_motion_status == STAY_MOTION_GRANTED:
        return ONE
    if stay_motion_status == STAY_MOTION_FILED:
        return STAY_MOTION_FILED_SCORE
    if stay_motion_status in (STAY_MOTION_ANTICIPATED, STAY_MOTION_UNKNOWN):
        return STAY_MOTION_PENDING_SCORE
    return ZERO


def _source_quorum_component(
    legal_source_count: Decimal,
    legal_source_quorum_count: Decimal,
) -> Decimal:
    if legal_source_count < legal_source_quorum_count:
        return ONE
    return ZERO


def _docket_freshness_component(
    docket_freshness_age_days: Decimal,
    max_docket_freshness_age_days: Decimal,
) -> Decimal:
    if docket_freshness_age_days > max_docket_freshness_age_days:
        return ONE
    return ZERO


def _jurisdiction_breadth_component(
    affected_jurisdiction_count: Decimal,
    broad_affected_jurisdiction_count: Decimal,
) -> Decimal:
    if affected_jurisdiction_count >= broad_affected_jurisdiction_count:
        return ONE
    return ZERO


def _has_upstream_block(upstream_reason_codes: tuple[str, ...]) -> bool:
    return any(
        _has_upstream_token(reason_code, "blocked")
        or _has_upstream_token(reason_code, "block")
        for reason_code in upstream_reason_codes
    )


def _has_upstream_watch(upstream_reason_codes: tuple[str, ...]) -> bool:
    return any(
        _has_upstream_token(reason_code, "watch")
        for reason_code in upstream_reason_codes
    )


def _has_upstream_token(reason_code: str, token: str) -> bool:
    return token in tuple(reason_code.lower().split("_"))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCKED
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_rule_count: Decimal,
    watch_rule_count: Decimal,
) -> str:
    if not has_inputs or blocked_rule_count > ZERO:
        return STATUS_BLOCKED
    if watch_rule_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...],
) -> tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.row_status),
                -row.stay_window_risk_score,
                row.days_until_effective_date,
                row.days_until_response_deadline,
                row.agency_court_source_id,
                row.market_slug,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...],
    rule_count: Decimal,
) -> tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in counts:
                counts[reason_code] += 1
            else:
                counts[reason_code] = 1
    return tuple(
        MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count_from_int(counts[reason_code]),
            rule_ratio=_ratio(_count_from_int(counts[reason_code]), rule_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _upstream_reason_code_counts(
    rows: tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...],
    rule_count: Decimal,
) -> tuple[
    MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount,
    ...,
]:
    counts: dict[str, int] = {}
    for row in rows:
        for upstream_reason_code in row.upstream_reason_codes:
            if upstream_reason_code in counts:
                counts[upstream_reason_code] += 1
            else:
                counts[upstream_reason_code] = 1
    return tuple(
        MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount(
            upstream_reason_code=upstream_reason_code,
            count=_count_from_int(counts[upstream_reason_code]),
            rule_ratio=_ratio(_count_from_int(counts[upstream_reason_code]), rule_count),
        )
        for upstream_reason_code in sorted(counts)
    )


def _reason_row_count(
    rows: tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPolicyEmergencyRuleStayWindowDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPolicyEmergencyRuleStayWindowDigestRow:
            raise ValueError(
                "rows must contain MarketResearchPolicyEmergencyRuleStayWindowDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must use deterministic sort")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[
    MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount,
    ...,
]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_index = -1
    for row in rows:
        if type(row) is not MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        current_index = REASON_CODE_SEQUENCE.index(row.reason_code)
        if current_index <= previous_index:
            raise ValueError("reason_code_counts must be unique and sorted")
        previous_index = current_index
    return rows


def _normalize_upstream_reason_code_counts(
    rows: object,
) -> tuple[
    MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount,
    ...,
]:
    if type(rows) is not tuple:
        raise ValueError("upstream_reason_code_counts must be a tuple")
    previous_value = ""
    for row in rows:
        if (
            type(row)
            is not MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount
        ):
            raise ValueError(
                "upstream_reason_code_counts must contain "
                "MarketResearchPolicyEmergencyRuleStayWindowDigestUpstreamReasonCodeCount",
            )
        _require_hard_flags("upstream reason code count", row)
        if previous_value and row.upstream_reason_code <= previous_value:
            raise ValueError(
                "upstream_reason_code_counts must be unique and sorted",
            )
        previous_value = row.upstream_reason_code
    return rows


def _normalize_reason_codes(
    values: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple and type(values) is not list:
        raise ValueError("reason_codes must be a tuple or list")
    normalized = tuple(values)
    if not normalized:
        raise ValueError("reason_codes must include at least one code")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code, sequence)
    sorted_codes = tuple(
        reason_code for reason_code in sequence if reason_code in normalized
    )
    if (
        sequence is ROW_REASON_CODE_SEQUENCE
        and PASS_REASON in sorted_codes
        and len(sorted_codes) != 1
    ):
        raise ValueError("reason_codes must not mix pass with risk reasons")
    if NO_INPUTS_REASON in sorted_codes and len(sorted_codes) != 1:
        raise ValueError("reason_codes must not mix no_inputs with row reasons")
    return sorted_codes


def _normalize_upstream_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple and type(values) is not list:
        raise ValueError("upstream_reason_codes must be a tuple or list")
    normalized = tuple(values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("upstream_reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_upstream_reason_code("upstream_reason_codes", reason_code)
    return tuple(sorted(normalized))


def _validate_row(row: MarketResearchPolicyEmergencyRuleStayWindowDigestRow) -> None:
    config = MarketResearchPolicyEmergencyRuleStayWindowDigestConfig()
    expected_risk_score = _stay_window_risk_score(
        days_until_effective_date=row.days_until_effective_date,
        days_until_response_deadline=row.days_until_response_deadline,
        docket_freshness_age_days=row.docket_freshness_age_days,
        stay_motion_status=row.stay_motion_status,
        injunction_probability_proxy=row.injunction_probability_proxy,
        affected_jurisdiction_count=row.affected_jurisdiction_count,
        legal_source_count=row.legal_source_count,
        legal_source_quorum_count=row.legal_source_quorum_count,
        config=config,
    )
    if row.stay_window_risk_score != expected_risk_score:
        raise ValueError("stay_window_risk_score must match row inputs")
    expected_reason_codes = _row_reason_codes(
        days_until_effective_date=row.days_until_effective_date,
        days_until_response_deadline=row.days_until_response_deadline,
        docket_freshness_age_days=row.docket_freshness_age_days,
        stay_motion_status=row.stay_motion_status,
        injunction_probability_proxy=row.injunction_probability_proxy,
        affected_jurisdiction_count=row.affected_jurisdiction_count,
        legal_source_count=row.legal_source_count,
        legal_source_quorum_count=row.legal_source_quorum_count,
        stay_window_risk_score=row.stay_window_risk_score,
        upstream_reason_codes=row.upstream_reason_codes,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report(
    report: MarketResearchPolicyEmergencyRuleStayWindowDigestReport,
) -> None:
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_POLICY_EMERGENCY_RULE_STAY_WINDOW_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.rule_count != _count_from_int(len(report.rows)):
        raise ValueError("rule_count must match rows")
    if report.pass_rule_count != _count_from_int(
        sum(1 for row in report.rows if row.row_status == STATUS_PASS),
    ):
        raise ValueError("pass_rule_count must match rows")
    if report.watch_rule_count != _count_from_int(
        sum(1 for row in report.rows if row.row_status == STATUS_WATCH),
    ):
        raise ValueError("watch_rule_count must match rows")
    if report.blocked_rule_count != _count_from_int(
        sum(1 for row in report.rows if row.row_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_rule_count must match rows")
    if report.pass_rule_count + report.watch_rule_count + report.blocked_rule_count != report.rule_count:
        raise ValueError("rule status counts must match rows")
    for field_name, reason_code in (
        ("stay_motion_filed_count", STAY_MOTION_FILED_REASON),
        ("stay_motion_granted_count", STAY_MOTION_GRANTED_REASON),
        ("high_injunction_probability_count", HIGH_INJUNCTION_PROBABILITY_REASON),
        ("elevated_injunction_probability_count", ELEVATED_INJUNCTION_PROBABILITY_REASON),
        ("effective_date_block_count", EFFECTIVE_DATE_BLOCK_REASON),
        ("effective_date_watch_count", EFFECTIVE_DATE_WATCH_REASON),
        ("response_deadline_block_count", RESPONSE_DEADLINE_BLOCK_REASON),
        ("response_deadline_watch_count", RESPONSE_DEADLINE_WATCH_REASON),
        ("stale_docket_count", STALE_DOCKET_REASON),
        ("thin_legal_source_quorum_count", THIN_LEGAL_SOURCE_QUORUM_REASON),
        ("broad_affected_jurisdiction_count", BROAD_AFFECTED_JURISDICTION_REASON),
        ("upstream_block_count", UPSTREAM_BLOCK_REASON),
        ("upstream_watch_count", UPSTREAM_WATCH_REASON),
        ("risk_score_block_count", RISK_SCORE_BLOCK_REASON),
        ("risk_score_watch_count", RISK_SCORE_WATCH_REASON),
    ):
        if getattr(report, field_name) != _reason_row_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_stay_window_risk_score != _ratio(
        _decimal_sum(row.stay_window_risk_score for row in report.rows),
        report.rule_count,
    ):
        raise ValueError("average_stay_window_risk_score must match rows")
    if report.max_stay_window_risk_score != max(
        (row.stay_window_risk_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_stay_window_risk_score must match rows")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_rule_count=report.blocked_rule_count,
        watch_rule_count=report.watch_rule_count,
    ):
        raise ValueError("digest_status must match rows")
    expected_reason_counts = _reason_code_counts(report.rows, report.rule_count)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchPolicyEmergencyRuleStayWindowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                rule_ratio=ZERO,
            ),
        )
        expected_reason_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_upstream_counts = _upstream_reason_code_counts(
        report.rows,
        report.rule_count,
    )
    if report.upstream_reason_code_counts != expected_upstream_counts:
        raise ValueError("upstream_reason_code_counts must match rows")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must not contain restricted text")


def _require_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    if value.startswith(("http://", "https://")):
        raise ValueError(f"{field_name} must be redacted")
    if value.startswith("public-") and not _contains_unsafe_text(value):
        return value
    if value.startswith("sha256:") and not _contains_unsafe_text(value):
        return value
    raise ValueError(f"{field_name} must be redacted")


def _redacted_reference(value: str) -> str:
    if value.startswith("public-") and not _contains_unsafe_text(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_reason_code(
    field_name: str,
    value: str,
    sequence: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in sequence:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_upstream_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must not contain restricted text")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be one of {REPORT_STATUSES!r}")


def _require_stay_motion_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STAY_MOTION_STATUSES:
        raise ValueError(f"{field_name} must be one of {STAY_MOTION_STATUSES!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty stripped string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be future relative to generated_at")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _days_between(end: datetime, start: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    return _quantize(Decimal(microseconds) / MICROSECONDS_PER_DAY)


def _count_from_int(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a non-negative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_sum(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer-valued Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, float) or isinstance(value, int):
        raise ValueError("payload value must not be a binary numeric")
    if isinstance(value, dict):
        return {key: _json_ready(value[key]) for key in value}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not supported")


def _reject_unsafe_payload(label: str, value: Any) -> None:
    if isinstance(value, str):
        if _contains_unsafe_text(value) or value.startswith(("http://", "https://")):
            raise ValueError(f"{label} contains unsafe text")
        return
    if isinstance(value, dict):
        for key in value:
            _reject_unsafe_payload(label, key)
            _reject_unsafe_payload(label, value[key])
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(label, item)
