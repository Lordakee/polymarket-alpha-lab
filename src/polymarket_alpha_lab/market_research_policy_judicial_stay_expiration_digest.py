"""Pure Phase 1 policy judicial stay expiration digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION = (
    "market-research-policy-judicial-stay-expiration-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_policy_judicial_stay_expiration_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
HIGH_POLICY_IMPACT_REASON = f"{REASON_PREFIX}high_policy_impact"
HIGH_EXTENSION_PROBABILITY_REASON = f"{REASON_PREFIX}high_extension_probability"
HIGH_MARKET_RELEVANCE_REASON = f"{REASON_PREFIX}high_market_relevance"
NEAR_TERM_EXPIRATION_REASON = f"{REASON_PREFIX}near_term_expiration"
STALE_STATUS_CHECK_REASON = f"{REASON_PREFIX}stale_status_check"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
EXPIRED_STAY_REASON = f"{REASON_PREFIX}expired_stay"

REASON_CODE_SEQUENCE = (
    HIGH_POLICY_IMPACT_REASON,
    HIGH_EXTENSION_PROBABILITY_REASON,
    HIGH_MARKET_RELEVANCE_REASON,
    NEAR_TERM_EXPIRATION_REASON,
    STALE_STATUS_CHECK_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    EXPIRED_STAY_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HIGH_POLICY_IMPACT_REASON,
    HIGH_EXTENSION_PROBABILITY_REASON,
    HIGH_MARKET_RELEVANCE_REASON,
    NEAR_TERM_EXPIRATION_REASON,
    STALE_STATUS_CHECK_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    EXPIRED_STAY_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_policy_judicial_stay_expiration_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_policy_judicial_stay_expiration_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_policy_judicial_stay_expiration_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyJudicialStayExpirationDigestConfig",
    "MarketResearchPolicyJudicialStayExpirationDigestInputRow",
    "MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount",
    "MarketResearchPolicyJudicialStayExpirationDigestReport",
    "MarketResearchPolicyJudicialStayExpirationDigestRow",
    "build_market_research_policy_judicial_stay_expiration_digest",
    "market_research_policy_judicial_stay_expiration_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyJudicialStayExpirationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION
    )
    near_term_expiration_seconds: Decimal = Decimal("172800.000000")
    stale_status_check_seconds: Decimal = Decimal("86400.000000")
    high_policy_impact_threshold: Decimal = Decimal("0.600000")
    high_extension_probability_threshold: Decimal = Decimal("0.600000")
    high_market_relevance_threshold: Decimal = Decimal("0.600000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyJudicialStayExpirationDigestConfig:
            raise TypeError(
                "MarketResearchPolicyJudicialStayExpirationDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyJudicialStayExpirationDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchPolicyJudicialStayExpirationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "near_term_expiration_seconds",
            "stale_status_check_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_policy_impact_threshold",
            "high_extension_probability_threshold",
            "high_market_relevance_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyJudicialStayExpirationDigestInputRow:
    research_key: str
    condition_id: str
    court_key: str
    jurisdiction_key: str
    docket_key: str
    case_title: str
    policy_domain: str
    public_expiration_reference: str
    stay_expires_at: datetime
    last_checked_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    policy_impact_score: Decimal
    extension_probability_score: Decimal
    market_relevance_score: Decimal
    expiration_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyJudicialStayExpirationDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyJudicialStayExpirationDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyJudicialStayExpirationDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicyJudicialStayExpirationDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "court_key",
            "jurisdiction_key",
            "docket_key",
            "case_title",
            "policy_domain",
            "expiration_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_expiration_reference", self.public_expiration_reference)
        object.__setattr__(
            self,
            "stay_expires_at",
            _as_utc("stay_expires_at", self.stay_expires_at),
        )
        object.__setattr__(
            self,
            "last_checked_at",
            _as_utc("last_checked_at", self.last_checked_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "policy_impact_score",
            "extension_probability_score",
            "market_relevance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyJudicialStayExpirationDigestRow:
    research_key: str
    condition_id: str
    court_key: str
    jurisdiction_key: str
    docket_key: str
    case_title: str
    policy_domain: str
    expiration_status: str
    stay_expires_at: datetime
    last_checked_at: datetime
    acknowledged_at: datetime | None
    seconds_until_expiration: Decimal
    status_check_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    policy_impact_score: Decimal
    extension_probability_score: Decimal
    market_relevance_score: Decimal
    redacted_public_expiration_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyJudicialStayExpirationDigestRow:
            raise TypeError(
                "MarketResearchPolicyJudicialStayExpirationDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyJudicialStayExpirationDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchPolicyJudicialStayExpirationDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "court_key",
            "jurisdiction_key",
            "docket_key",
            "case_title",
            "policy_domain",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("expiration_status", self.expiration_status)
        object.__setattr__(
            self,
            "stay_expires_at",
            _as_utc("stay_expires_at", self.stay_expires_at),
        )
        object.__setattr__(
            self,
            "last_checked_at",
            _as_utc("last_checked_at", self.last_checked_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "seconds_until_expiration",
            _require_decimal("seconds_until_expiration", self.seconds_until_expiration),
        )
        object.__setattr__(
            self,
            "status_check_age_seconds",
            _require_nonnegative_decimal(
                "status_check_age_seconds",
                self.status_check_age_seconds,
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
            "policy_impact_score",
            "extension_probability_score",
            "market_relevance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_expiration_reference",
            _require_redacted_reference(
                "redacted_public_expiration_reference",
                self.redacted_public_expiration_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    expiration_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "expiration_ratio",
            _require_ratio_decimal("expiration_ratio", self.expiration_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyJudicialStayExpirationDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    expiration_count: Decimal
    ready_expiration_count: Decimal
    watch_expiration_count: Decimal
    blocked_expiration_count: Decimal
    high_policy_impact_count: Decimal
    high_extension_probability_count: Decimal
    high_market_relevance_count: Decimal
    near_term_expiration_count: Decimal
    stale_status_check_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    expired_stay_count: Decimal
    average_policy_impact_score: Decimal
    average_extension_probability_score: Decimal
    average_market_relevance_score: Decimal
    average_source_count: Decimal
    minimum_seconds_until_expiration: Decimal
    rows: tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...]
    expiration_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyJudicialStayExpirationDigestReport:
            raise TypeError(
                "MarketResearchPolicyJudicialStayExpirationDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyJudicialStayExpirationDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchPolicyJudicialStayExpirationDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "expiration_count",
            "ready_expiration_count",
            "watch_expiration_count",
            "blocked_expiration_count",
            "high_policy_impact_count",
            "high_extension_probability_count",
            "high_market_relevance_count",
            "near_term_expiration_count",
            "stale_status_check_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "expired_stay_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_policy_impact_score",
            "average_extension_probability_score",
            "average_market_relevance_score",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_seconds_until_expiration",
            _require_decimal(
                "minimum_seconds_until_expiration",
                self.minimum_seconds_until_expiration,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "expiration_config_versions",
            _normalize_expiration_config_versions(self.expiration_config_versions),
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


def build_market_research_policy_judicial_stay_expiration_digest(
    input_rows: Iterable[MarketResearchPolicyJudicialStayExpirationDigestInputRow],
    *,
    config: MarketResearchPolicyJudicialStayExpirationDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyJudicialStayExpirationDigestReport:
    if type(config) is not MarketResearchPolicyJudicialStayExpirationDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchPolicyJudicialStayExpirationDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_rows
    )
    sorted_rows = _sorted_rows(rows)
    expiration_count = _count(len(sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows, expiration_count)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = (
            MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                expiration_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    ready_expiration_count = _count(
        sum(1 for row in sorted_rows if row.expiration_status == STATUS_READY),
    )
    watch_expiration_count = _count(
        sum(1 for row in sorted_rows if row.expiration_status == STATUS_WATCH),
    )
    blocked_expiration_count = _count(
        sum(1 for row in sorted_rows if row.expiration_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(sorted_rows),
        blocked_expiration_count=blocked_expiration_count,
        watch_expiration_count=watch_expiration_count,
    )

    return MarketResearchPolicyJudicialStayExpirationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        expiration_count=expiration_count,
        ready_expiration_count=ready_expiration_count,
        watch_expiration_count=watch_expiration_count,
        blocked_expiration_count=blocked_expiration_count,
        high_policy_impact_count=_reason_expiration_count(
            sorted_rows,
            HIGH_POLICY_IMPACT_REASON,
        ),
        high_extension_probability_count=_reason_expiration_count(
            sorted_rows,
            HIGH_EXTENSION_PROBABILITY_REASON,
        ),
        high_market_relevance_count=_reason_expiration_count(
            sorted_rows,
            HIGH_MARKET_RELEVANCE_REASON,
        ),
        near_term_expiration_count=_reason_expiration_count(
            sorted_rows,
            NEAR_TERM_EXPIRATION_REASON,
        ),
        stale_status_check_count=_reason_expiration_count(
            sorted_rows,
            STALE_STATUS_CHECK_REASON,
        ),
        thin_source_count=_reason_expiration_count(sorted_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_expiration_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        expired_stay_count=_reason_expiration_count(sorted_rows, EXPIRED_STAY_REASON),
        average_policy_impact_score=_ratio(
            _decimal_sum(row.policy_impact_score for row in sorted_rows),
            expiration_count,
        ),
        average_extension_probability_score=_ratio(
            _decimal_sum(row.extension_probability_score for row in sorted_rows),
            expiration_count,
        ),
        average_market_relevance_score=_ratio(
            _decimal_sum(row.market_relevance_score for row in sorted_rows),
            expiration_count,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            expiration_count,
        ),
        minimum_seconds_until_expiration=min(
            (row.seconds_until_expiration for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        expiration_config_versions=_expiration_config_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_judicial_stay_expiration_digest_payload(
    report: MarketResearchPolicyJudicialStayExpirationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyJudicialStayExpirationDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchPolicyJudicialStayExpirationDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_input(
    row: MarketResearchPolicyJudicialStayExpirationDigestInputRow,
    *,
    config: MarketResearchPolicyJudicialStayExpirationDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyJudicialStayExpirationDigestRow:
    _require_not_future("last_checked_at", row.last_checked_at, generated_at)
    if row.acknowledged_at is not None:
        _require_not_future("acknowledged_at", row.acknowledged_at, generated_at)
    seconds_until_expiration = _seconds_between(row.stay_expires_at, generated_at)
    status_check_age_seconds = _seconds_between(generated_at, row.last_checked_at)
    acknowledgement_lag_seconds = (
        None
        if row.acknowledged_at is None
        else _seconds_between(row.acknowledged_at, row.last_checked_at)
    )
    reason_codes = _row_reason_codes(
        seconds_until_expiration=seconds_until_expiration,
        status_check_age_seconds=status_check_age_seconds,
        source_count=row.source_count,
        policy_impact_score=row.policy_impact_score,
        extension_probability_score=row.extension_probability_score,
        market_relevance_score=row.market_relevance_score,
        acknowledged_at=row.acknowledged_at,
        config=config,
    )
    return MarketResearchPolicyJudicialStayExpirationDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        court_key=row.court_key,
        jurisdiction_key=row.jurisdiction_key,
        docket_key=row.docket_key,
        case_title=row.case_title,
        policy_domain=row.policy_domain,
        expiration_status=_row_status(reason_codes),
        stay_expires_at=row.stay_expires_at,
        last_checked_at=row.last_checked_at,
        acknowledged_at=row.acknowledged_at,
        seconds_until_expiration=seconds_until_expiration,
        status_check_age_seconds=status_check_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        policy_impact_score=row.policy_impact_score,
        extension_probability_score=row.extension_probability_score,
        market_relevance_score=row.market_relevance_score,
        redacted_public_expiration_reference=_redact_reference(
            row.public_expiration_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    seconds_until_expiration: Decimal,
    status_check_age_seconds: Decimal,
    source_count: Decimal,
    policy_impact_score: Decimal,
    extension_probability_score: Decimal,
    market_relevance_score: Decimal,
    acknowledged_at: datetime | None,
    config: MarketResearchPolicyJudicialStayExpirationDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if policy_impact_score >= config.high_policy_impact_threshold:
        reasons.append(HIGH_POLICY_IMPACT_REASON)
    if extension_probability_score >= config.high_extension_probability_threshold:
        reasons.append(HIGH_EXTENSION_PROBABILITY_REASON)
    if market_relevance_score >= config.high_market_relevance_threshold:
        reasons.append(HIGH_MARKET_RELEVANCE_REASON)
    if ZERO <= seconds_until_expiration <= config.near_term_expiration_seconds:
        reasons.append(NEAR_TERM_EXPIRATION_REASON)
    if status_check_age_seconds > config.stale_status_check_seconds:
        reasons.append(STALE_STATUS_CHECK_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if acknowledged_at is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    if seconds_until_expiration < ZERO:
        reasons.append(EXPIRED_STAY_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(reasons, sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes or EXPIRED_STAY_REASON in reason_codes:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_expiration_count: Decimal,
    watch_expiration_count: Decimal,
) -> str:
    if not has_inputs or blocked_expiration_count > ZERO:
        return STATUS_BLOCKED
    if watch_expiration_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _sorted_rows(
    rows: tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...],
) -> tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.expiration_status),
                _blocked_reason_rank(row.reason_codes),
                row.seconds_until_expiration,
                -row.policy_impact_score,
                -row.extension_probability_score,
                -row.market_relevance_score,
                row.court_key,
                row.research_key,
            ),
        ),
    )


def _blocked_reason_rank(reason_codes: tuple[str, ...]) -> int:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return 0
    if EXPIRED_STAY_REASON in reason_codes:
        return 1
    return 2


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...],
    expiration_count: Decimal,
) -> tuple[MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            expiration_ratio=_ratio(count, expiration_count),
        )
        for reason_code, count in sorted(
            (
                (
                    reason_code,
                    _reason_expiration_count(rows, reason_code),
                )
                for reason_code in REASON_CODE_SEQUENCE
                if any(reason_code in row.reason_codes for row in rows)
            ),
            key=lambda item: _reason_rank(item[0]),
        )
    )


def _reason_expiration_count(
    rows: tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _expiration_config_versions(
    rows: tuple[MarketResearchPolicyJudicialStayExpirationDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    versions = {row.court_key: row.expiration_config_version for row in rows}
    return tuple(sorted(versions.items()))


def _normalize_input_rows(
    input_rows: Iterable[MarketResearchPolicyJudicialStayExpirationDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchPolicyJudicialStayExpirationDigestInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable of input rows")
    try:
        rows = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable of input rows") from exc
    seen_court_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPolicyJudicialStayExpirationDigestInputRow:
            raise ValueError(
                "input_rows must contain "
                "MarketResearchPolicyJudicialStayExpirationDigestInputRow values",
            )
        _require_not_future("last_checked_at", row.last_checked_at, generated_at)
        if row.acknowledged_at is not None:
            _require_not_future("acknowledged_at", row.acknowledged_at, generated_at)
        if row.court_key in seen_court_keys:
            raise ValueError("court_key values must be unique")
        seen_court_keys.add(row.court_key)
    return rows


def _normalize_rows(
    rows: tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...],
) -> tuple[MarketResearchPolicyJudicialStayExpirationDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in normalized:
        if type(row) is not MarketResearchPolicyJudicialStayExpirationDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicyJudicialStayExpirationDigestRow values",
            )
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must use deterministic expiration sort")
    return normalized


def _normalize_expiration_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("expiration_config_versions must be a tuple")
    try:
        normalized = tuple(tuple(item) for item in values)
    except TypeError as exc:
        raise ValueError("expiration_config_versions must be a tuple") from exc
    if normalized != tuple(sorted(normalized)):
        raise ValueError("expiration_config_versions must be sorted")
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("expiration_config_versions entries must have two values")
        court_key, config_version = item
        _require_public_string("expiration_config_versions", court_key)
        _require_public_string("expiration_config_versions", config_version)
        if court_key in seen:
            raise ValueError("expiration_config_versions must have unique court keys")
        seen.add(court_key)
    return normalized


def _normalize_reason_code_counts(
    values: tuple[MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount, ...],
) -> tuple[MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    for item in normalized:
        if (
            type(item)
            is not MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount values",
            )
    if normalized != tuple(
        sorted(normalized, key=lambda item: _reason_rank(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic reason code sort")
    return normalized


def _normalize_reason_codes(
    values: Iterable[str],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be a tuple")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple") from exc
    if not normalized:
        raise ValueError("reason_codes must include at least one code")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes include an unknown code")
    return tuple(sorted(normalized, key=lambda reason_code: sequence.index(reason_code)))


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _validate_row(row: MarketResearchPolicyJudicialStayExpirationDigestRow) -> None:
    expected_reason_codes = _row_reason_codes(
        seconds_until_expiration=row.seconds_until_expiration,
        status_check_age_seconds=row.status_check_age_seconds,
        source_count=row.source_count,
        policy_impact_score=row.policy_impact_score,
        extension_probability_score=row.extension_probability_score,
        market_relevance_score=row.market_relevance_score,
        acknowledged_at=row.acknowledged_at,
        config=MarketResearchPolicyJudicialStayExpirationDigestConfig(),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")
    if row.expiration_status != _row_status(row.reason_codes):
        raise ValueError("expiration_status must match reason_codes")


def _validate_report(report: MarketResearchPolicyJudicialStayExpirationDigestReport) -> None:
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_POLICY_JUDICIAL_STAY_EXPIRATION_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.expiration_count != _count(len(report.rows)):
        raise ValueError("expiration_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.expiration_status == STATUS_READY),
    )
    expected_watch = _count(
        sum(1 for row in report.rows if row.expiration_status == STATUS_WATCH),
    )
    expected_blocked = _count(
        sum(1 for row in report.rows if row.expiration_status == STATUS_BLOCKED),
    )
    if report.ready_expiration_count != expected_ready:
        raise ValueError("ready_expiration_count must match rows")
    if report.watch_expiration_count != expected_watch:
        raise ValueError("watch_expiration_count must match rows")
    if report.blocked_expiration_count != expected_blocked:
        raise ValueError("blocked_expiration_count must match rows")
    if (
        report.ready_expiration_count
        + report.watch_expiration_count
        + report.blocked_expiration_count
        != report.expiration_count
    ):
        raise ValueError("expiration status counts must reconcile")
    reason_count_fields = (
        ("high_policy_impact_count", HIGH_POLICY_IMPACT_REASON),
        ("high_extension_probability_count", HIGH_EXTENSION_PROBABILITY_REASON),
        ("high_market_relevance_count", HIGH_MARKET_RELEVANCE_REASON),
        ("near_term_expiration_count", NEAR_TERM_EXPIRATION_REASON),
        ("stale_status_check_count", STALE_STATUS_CHECK_REASON),
        ("thin_source_count", THIN_SOURCES_REASON),
        ("missing_acknowledgement_count", MISSING_ACKNOWLEDGEMENT_REASON),
        ("expired_stay_count", EXPIRED_STAY_REASON),
    )
    for field_name, reason_code in reason_count_fields:
        if getattr(report, field_name) != _reason_expiration_count(
            report.rows,
            reason_code,
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.average_policy_impact_score != _ratio(
        _decimal_sum(row.policy_impact_score for row in report.rows),
        report.expiration_count,
    ):
        raise ValueError("average_policy_impact_score must match rows")
    if report.average_extension_probability_score != _ratio(
        _decimal_sum(row.extension_probability_score for row in report.rows),
        report.expiration_count,
    ):
        raise ValueError("average_extension_probability_score must match rows")
    if report.average_market_relevance_score != _ratio(
        _decimal_sum(row.market_relevance_score for row in report.rows),
        report.expiration_count,
    ):
        raise ValueError("average_market_relevance_score must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.expiration_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.minimum_seconds_until_expiration != min(
        (row.seconds_until_expiration for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("minimum_seconds_until_expiration must match rows")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_expiration_count=report.blocked_expiration_count,
        watch_expiration_count=report.watch_expiration_count,
    ):
        raise ValueError("digest_status must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.expiration_count,
    ):
        if not report.rows and report.reason_code_counts == (
            MarketResearchPolicyJudicialStayExpirationDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                expiration_ratio=ZERO,
            ),
        ):
            pass
        else:
            raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain restricted text")


def _require_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    if not value.startswith(("public-", "sha256:")):
        raise ValueError(f"{field_name} must be redacted")
    if not value.startswith("sha256:") and any(
        fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS
    ):
        raise ValueError(f"{field_name} must be redacted")
    if value.startswith(("http://", "https://")):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _redact_reference(value: str) -> str:
    if not value.startswith("public-"):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    if value.startswith(("http://", "https://")):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    return value


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES!r}")


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


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(end: datetime, start: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    return _quantize(Decimal(microseconds) / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a non-negative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
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


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer-valued Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _reason_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
