"""Pure Phase 1 campaign ad spend surge digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION = (
    "market-research-policy-campaign-ad-spend-surge-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_policy_campaign_ad_spend_surge_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
HIGH_SPEND_SURGE_REASON = f"{REASON_PREFIX}high_spend_surge"
HIGH_AD_VOLUME_REASON = f"{REASON_PREFIX}high_ad_volume"
HIGH_MESSAGE_SHIFT_REASON = f"{REASON_PREFIX}high_message_shift"
HIGH_OPPOSITION_RESPONSE_REASON = f"{REASON_PREFIX}high_opposition_response"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    HIGH_SPEND_SURGE_REASON,
    HIGH_AD_VOLUME_REASON,
    HIGH_MESSAGE_SHIFT_REASON,
    HIGH_OPPOSITION_RESPONSE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HIGH_SPEND_SURGE_REASON,
    HIGH_AD_VOLUME_REASON,
    HIGH_MESSAGE_SHIFT_REASON,
    HIGH_OPPOSITION_RESPONSE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_policy_campaign_ad_spend_surge_digest",
    STATUS_WATCH: "watch_report_only_market_research_policy_campaign_ad_spend_surge_digest",
    STATUS_BLOCKED: "block_report_only_market_research_policy_campaign_ad_spend_surge_digest",
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
        "://",
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
        _join_parts("tok", "en"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        "@",
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyCampaignAdSpendSurgeDigestConfig",
    "MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow",
    "MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount",
    "MarketResearchPolicyCampaignAdSpendSurgeDigestReport",
    "MarketResearchPolicyCampaignAdSpendSurgeDigestRow",
    "build_market_research_policy_campaign_ad_spend_surge_digest",
    "market_research_policy_campaign_ad_spend_surge_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignAdSpendSurgeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("86400.000000")
    high_spend_surge_threshold: Decimal = Decimal("0.650000")
    high_ad_volume_threshold: Decimal = Decimal("0.600000")
    high_message_shift_threshold: Decimal = Decimal("0.550000")
    high_opposition_response_threshold: Decimal = Decimal("0.500000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignAdSpendSurgeDigestConfig:
            raise TypeError(
                "MarketResearchPolicyCampaignAdSpendSurgeDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignAdSpendSurgeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_observation_max_age_seconds",
            _require_positive_decimal(
                "fresh_observation_max_age_seconds",
                self.fresh_observation_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "high_spend_surge_threshold",
            "high_ad_volume_threshold",
            "high_message_shift_threshold",
            "high_opposition_response_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow:
    research_id: str
    condition_id: str
    race_id: str
    campaign_id: str
    jurisdiction_id: str
    public_spend_reference: str
    observed_at: datetime
    source_count: Decimal
    spend_surge_score: Decimal
    ad_volume_score: Decimal
    message_shift_score: Decimal
    opposition_response_score: Decimal
    spend_model_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow,
            "input row",
        )
        for field_name in (
            "research_id",
            "condition_id",
            "race_id",
            "campaign_id",
            "jurisdiction_id",
            "spend_model_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_spend_reference", self.public_spend_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "spend_surge_score",
            "ad_volume_score",
            "message_shift_score",
            "opposition_response_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignAdSpendSurgeDigestRow:
    research_id: str
    condition_id: str
    race_id: str
    campaign_id: str
    jurisdiction_id: str
    surge_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    spend_surge_score: Decimal
    ad_volume_score: Decimal
    message_shift_score: Decimal
    opposition_response_score: Decimal
    redacted_public_spend_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignAdSpendSurgeDigestRow:
            raise TypeError(
                "MarketResearchPolicyCampaignAdSpendSurgeDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignAdSpendSurgeDigestRow,
            "row",
        )
        for field_name in (
            "research_id",
            "condition_id",
            "race_id",
            "campaign_id",
            "jurisdiction_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("surge_status", self.surge_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "spend_surge_score",
            "ad_volume_score",
            "message_shift_score",
            "opposition_response_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_spend_reference",
            _require_redacted_reference(
                "redacted_public_spend_reference",
                self.redacted_public_spend_reference,
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
class MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    campaign_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount,
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
            "campaign_ratio",
            _require_ratio_decimal("campaign_ratio", self.campaign_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignAdSpendSurgeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    campaign_count: Decimal
    ready_campaign_count: Decimal
    watch_campaign_count: Decimal
    blocked_campaign_count: Decimal
    high_spend_surge_count: Decimal
    high_ad_volume_count: Decimal
    high_message_shift_count: Decimal
    high_opposition_response_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    average_spend_surge_score: Decimal
    average_ad_volume_score: Decimal
    average_message_shift_score: Decimal
    average_opposition_response_score: Decimal
    average_source_count: Decimal
    max_observation_age_seconds: Decimal
    rows: tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...]
    spend_model_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignAdSpendSurgeDigestReport:
            raise TypeError(
                "MarketResearchPolicyCampaignAdSpendSurgeDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignAdSpendSurgeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "campaign_count",
            "ready_campaign_count",
            "watch_campaign_count",
            "blocked_campaign_count",
            "high_spend_surge_count",
            "high_ad_volume_count",
            "high_message_shift_count",
            "high_opposition_response_count",
            "stale_observation_count",
            "thin_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_spend_surge_score",
            "average_ad_volume_score",
            "average_message_shift_score",
            "average_opposition_response_score",
            "average_source_count",
            "max_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "spend_model_versions",
            _normalize_spend_model_versions(self.spend_model_versions),
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


def build_market_research_policy_campaign_ad_spend_surge_digest(
    input_rows: Iterable[MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow],
    *,
    config: MarketResearchPolicyCampaignAdSpendSurgeDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyCampaignAdSpendSurgeDigestReport:
    if type(config) is not MarketResearchPolicyCampaignAdSpendSurgeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchPolicyCampaignAdSpendSurgeDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_rows
    )
    sorted_rows = _sorted_rows(rows)
    campaign_count = _count(len(sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows, campaign_count)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = (
            MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                campaign_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    ready_campaign_count = _count(
        sum(1 for row in sorted_rows if row.surge_status == STATUS_READY),
    )
    watch_campaign_count = _count(
        sum(1 for row in sorted_rows if row.surge_status == STATUS_WATCH),
    )
    blocked_campaign_count = _count(
        sum(1 for row in sorted_rows if row.surge_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(sorted_rows),
        blocked_campaign_count=blocked_campaign_count,
        watch_campaign_count=watch_campaign_count,
    )

    return MarketResearchPolicyCampaignAdSpendSurgeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        campaign_count=campaign_count,
        ready_campaign_count=ready_campaign_count,
        watch_campaign_count=watch_campaign_count,
        blocked_campaign_count=blocked_campaign_count,
        high_spend_surge_count=_reason_campaign_count(
            sorted_rows,
            HIGH_SPEND_SURGE_REASON,
        ),
        high_ad_volume_count=_reason_campaign_count(
            sorted_rows,
            HIGH_AD_VOLUME_REASON,
        ),
        high_message_shift_count=_reason_campaign_count(
            sorted_rows,
            HIGH_MESSAGE_SHIFT_REASON,
        ),
        high_opposition_response_count=_reason_campaign_count(
            sorted_rows,
            HIGH_OPPOSITION_RESPONSE_REASON,
        ),
        stale_observation_count=_reason_campaign_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        thin_source_count=_reason_campaign_count(sorted_rows, THIN_SOURCES_REASON),
        average_spend_surge_score=_ratio(
            _decimal_sum(row.spend_surge_score for row in sorted_rows),
            campaign_count,
        ),
        average_ad_volume_score=_ratio(
            _decimal_sum(row.ad_volume_score for row in sorted_rows),
            campaign_count,
        ),
        average_message_shift_score=_ratio(
            _decimal_sum(row.message_shift_score for row in sorted_rows),
            campaign_count,
        ),
        average_opposition_response_score=_ratio(
            _decimal_sum(row.opposition_response_score for row in sorted_rows),
            campaign_count,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            campaign_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        spend_model_versions=_spend_model_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_campaign_ad_spend_surge_digest_payload(
    report: MarketResearchPolicyCampaignAdSpendSurgeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyCampaignAdSpendSurgeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchPolicyCampaignAdSpendSurgeDigestReport",
        )
    _require_hard_flags("report", report)
    return _report_payload(report)


def _row_for_input(
    row: MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow,
    *,
    config: MarketResearchPolicyCampaignAdSpendSurgeDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyCampaignAdSpendSurgeDigestRow:
    _require_not_future("observed_at", row.observed_at, generated_at)
    observation_age_seconds = _seconds_between(generated_at, row.observed_at)
    reason_codes = _row_reason_codes(
        observation_age_seconds=observation_age_seconds,
        source_count=row.source_count,
        spend_surge_score=row.spend_surge_score,
        ad_volume_score=row.ad_volume_score,
        message_shift_score=row.message_shift_score,
        opposition_response_score=row.opposition_response_score,
        config=config,
    )
    return MarketResearchPolicyCampaignAdSpendSurgeDigestRow(
        research_id=row.research_id,
        condition_id=row.condition_id,
        race_id=row.race_id,
        campaign_id=row.campaign_id,
        jurisdiction_id=row.jurisdiction_id,
        surge_status=_row_status(reason_codes),
        observed_at=row.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=row.source_count,
        spend_surge_score=row.spend_surge_score,
        ad_volume_score=row.ad_volume_score,
        message_shift_score=row.message_shift_score,
        opposition_response_score=row.opposition_response_score,
        redacted_public_spend_reference=_redact_reference(row.public_spend_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation_age_seconds: Decimal,
    source_count: Decimal,
    spend_surge_score: Decimal,
    ad_volume_score: Decimal,
    message_shift_score: Decimal,
    opposition_response_score: Decimal,
    config: MarketResearchPolicyCampaignAdSpendSurgeDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if spend_surge_score >= config.high_spend_surge_threshold:
        reasons.append(HIGH_SPEND_SURGE_REASON)
    if ad_volume_score >= config.high_ad_volume_threshold:
        reasons.append(HIGH_AD_VOLUME_REASON)
    if message_shift_score >= config.high_message_shift_threshold:
        reasons.append(HIGH_MESSAGE_SHIFT_REASON)
    if opposition_response_score >= config.high_opposition_response_threshold:
        reasons.append(HIGH_OPPOSITION_RESPONSE_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(tuple(reasons), sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        HIGH_SPEND_SURGE_REASON in reason_codes
        and HIGH_AD_VOLUME_REASON in reason_codes
        and HIGH_OPPOSITION_RESPONSE_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if STALE_OBSERVATION_REASON in reason_codes and THIN_SOURCES_REASON in reason_codes:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_campaign_count: Decimal,
    watch_campaign_count: Decimal,
) -> str:
    if not has_inputs or blocked_campaign_count > ZERO:
        return STATUS_BLOCKED
    if watch_campaign_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _sorted_rows(
    rows: tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...],
) -> tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...]:
    ranked = tuple((_row_sort_tuple(row), row) for row in rows)
    return tuple(item[1] for item in sorted(ranked))


def _row_sort_tuple(
    row: MarketResearchPolicyCampaignAdSpendSurgeDigestRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.surge_status),
        _blocked_reason_rank(row.reason_codes),
        -row.spend_surge_score,
        -row.ad_volume_score,
        -row.opposition_response_score,
        -row.message_shift_score,
        row.race_id,
        row.research_id,
    )


def _blocked_reason_rank(reason_codes: tuple[str, ...]) -> int:
    if (
        HIGH_SPEND_SURGE_REASON in reason_codes
        and HIGH_AD_VOLUME_REASON in reason_codes
        and HIGH_OPPOSITION_RESPONSE_REASON in reason_codes
    ):
        return 0
    if STALE_OBSERVATION_REASON in reason_codes and THIN_SOURCES_REASON in reason_codes:
        return 1
    return 2


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...],
    campaign_count: Decimal,
) -> tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount, ...]:
    ranked_counts = tuple(
        (
            _reason_rank(reason_code),
            reason_code,
            _reason_campaign_count(rows, reason_code),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )
    return tuple(
        MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            campaign_ratio=_ratio(count, campaign_count),
        )
        for _, reason_code, count in sorted(ranked_counts)
    )


def _reason_campaign_count(
    rows: tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _spend_model_versions(
    rows: tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((row.condition_id, row.spend_model_version) for row in rows))


def _normalize_input_rows(
    input_rows: Iterable[MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable of input rows")
    try:
        rows = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable of input rows") from exc
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow:
            raise ValueError(
                "input_rows must contain "
                "MarketResearchPolicyCampaignAdSpendSurgeDigestInputRow values",
            )
        _require_not_future("observed_at", row.observed_at, generated_at)
        if row.condition_id in seen_condition_ids:
            raise ValueError("condition_id values must be unique")
        seen_condition_ids.add(row.condition_id)
    return rows


def _normalize_rows(
    rows: tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...],
) -> tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPolicyCampaignAdSpendSurgeDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicyCampaignAdSpendSurgeDigestRow values",
            )
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic surge sequence")
    return rows


def _normalize_spend_model_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("spend_model_versions must be a tuple")
    normalized = tuple(tuple(item) for item in values)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("spend_model_versions must be sorted")
    seen_condition_ids: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("spend_model_versions entries must have two values")
        condition_id, model_version = item
        _require_public_string("spend_model_versions", condition_id)
        _require_public_string("spend_model_versions", model_version)
        if condition_id in seen_condition_ids:
            raise ValueError("spend_model_versions must have unique condition ids")
        seen_condition_ids.add(condition_id)
    return normalized


def _normalize_reason_code_counts(
    values: tuple[
        MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in values:
        if type(item) is not MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount values",
            )
    ranked = tuple((_reason_rank(item.reason_code), item) for item in values)
    if values != tuple(item[1] for item in sorted(ranked)):
        raise ValueError("reason_code_counts must use deterministic reason sequence")
    return values


def _normalize_reason_codes(
    values: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must include at least one code")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes include an unknown code")
    ranked = tuple((sequence.index(reason_code), reason_code) for reason_code in values)
    return tuple(reason_code for _, reason_code in sorted(ranked))


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _reason_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _validate_row(row: MarketResearchPolicyCampaignAdSpendSurgeDigestRow) -> None:
    expected_reason_codes = _row_reason_codes(
        observation_age_seconds=row.observation_age_seconds,
        source_count=row.source_count,
        spend_surge_score=row.spend_surge_score,
        ad_volume_score=row.ad_volume_score,
        message_shift_score=row.message_shift_score,
        opposition_response_score=row.opposition_response_score,
        config=MarketResearchPolicyCampaignAdSpendSurgeDigestConfig(),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")
    if row.surge_status != _row_status(row.reason_codes):
        raise ValueError("surge_status must match reason_codes")


def _validate_report(
    report: MarketResearchPolicyCampaignAdSpendSurgeDigestReport,
) -> None:
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_AD_SPEND_SURGE_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.campaign_count != _count(len(report.rows)):
        raise ValueError("campaign_count must match rows")

    expected_ready = _count(
        sum(1 for row in report.rows if row.surge_status == STATUS_READY),
    )
    expected_watch = _count(
        sum(1 for row in report.rows if row.surge_status == STATUS_WATCH),
    )
    expected_blocked = _count(
        sum(1 for row in report.rows if row.surge_status == STATUS_BLOCKED),
    )
    if report.ready_campaign_count != expected_ready:
        raise ValueError("ready_campaign_count must match rows")
    if report.watch_campaign_count != expected_watch:
        raise ValueError("watch_campaign_count must match rows")
    if report.blocked_campaign_count != expected_blocked:
        raise ValueError("blocked_campaign_count must match rows")
    if (
        report.ready_campaign_count
        + report.watch_campaign_count
        + report.blocked_campaign_count
        != report.campaign_count
    ):
        raise ValueError("campaign status counts must reconcile")

    reason_count_fields = (
        ("high_spend_surge_count", HIGH_SPEND_SURGE_REASON),
        ("high_ad_volume_count", HIGH_AD_VOLUME_REASON),
        ("high_message_shift_count", HIGH_MESSAGE_SHIFT_REASON),
        ("high_opposition_response_count", HIGH_OPPOSITION_RESPONSE_REASON),
        ("stale_observation_count", STALE_OBSERVATION_REASON),
        ("thin_source_count", THIN_SOURCES_REASON),
    )
    for field_name, reason_code in reason_count_fields:
        if getattr(report, field_name) != _reason_campaign_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")

    if report.average_spend_surge_score != _ratio(
        _decimal_sum(row.spend_surge_score for row in report.rows),
        report.campaign_count,
    ):
        raise ValueError("average_spend_surge_score must match rows")
    if report.average_ad_volume_score != _ratio(
        _decimal_sum(row.ad_volume_score for row in report.rows),
        report.campaign_count,
    ):
        raise ValueError("average_ad_volume_score must match rows")
    if report.average_message_shift_score != _ratio(
        _decimal_sum(row.message_shift_score for row in report.rows),
        report.campaign_count,
    ):
        raise ValueError("average_message_shift_score must match rows")
    if report.average_opposition_response_score != _ratio(
        _decimal_sum(row.opposition_response_score for row in report.rows),
        report.campaign_count,
    ):
        raise ValueError("average_opposition_response_score must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.campaign_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds must match rows")

    expected_reason_code_counts = _reason_code_counts(report.rows, report.campaign_count)
    if not report.rows:
        expected_reason_code_counts = (
            MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                campaign_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_campaign_count=report.blocked_campaign_count,
        watch_campaign_count=report.watch_campaign_count,
    ):
        raise ValueError("digest_status must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, field_name)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{label} {field_name} must be hard True")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose restricted text")


def _require_reference(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")


def _require_redacted_reference(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"{field_name} must be a redacted reference")
        return value
    _require_public_string(field_name, value)
    if not value.startswith("public-"):
        raise ValueError(f"{field_name} must be a public or redacted reference")
    return value


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    converted = value.astimezone(UTC)
    if converted.tzinfo is not UTC:
        raise ValueError(f"{field_name} must normalize to UTC")
    return converted


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be in the future")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    whole_seconds = Decimal(delta.days) * Decimal("86400") + Decimal(delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + fractional_seconds)


def _redact_reference(value: str) -> str:
    if value.startswith("public-") and not any(
        fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS
    ):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _format_datetime(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    return str(_require_decimal("payload decimal", value))


def _reason_count_payload(
    item: MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount,
) -> dict[str, Any]:
    if type(item) is not MarketResearchPolicyCampaignAdSpendSurgeDigestReasonCodeCount:
        raise ValueError("reason code count must be exact")
    _require_hard_flags("reason code count", item)
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "campaign_ratio": _decimal_payload(item.campaign_ratio),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _row_payload(row: MarketResearchPolicyCampaignAdSpendSurgeDigestRow) -> dict[str, Any]:
    if type(row) is not MarketResearchPolicyCampaignAdSpendSurgeDigestRow:
        raise ValueError("row must be exact")
    _require_hard_flags("row", row)
    return {
        "research_id": row.research_id,
        "condition_id": row.condition_id,
        "race_id": row.race_id,
        "campaign_id": row.campaign_id,
        "jurisdiction_id": row.jurisdiction_id,
        "surge_status": row.surge_status,
        "observed_at": _format_datetime(row.observed_at),
        "observation_age_seconds": _decimal_payload(row.observation_age_seconds),
        "source_count": _decimal_payload(row.source_count),
        "spend_surge_score": _decimal_payload(row.spend_surge_score),
        "ad_volume_score": _decimal_payload(row.ad_volume_score),
        "message_shift_score": _decimal_payload(row.message_shift_score),
        "opposition_response_score": _decimal_payload(row.opposition_response_score),
        "redacted_public_spend_reference": row.redacted_public_spend_reference,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_payload(
    report: MarketResearchPolicyCampaignAdSpendSurgeDigestReport,
) -> dict[str, Any]:
    return {
        "generated_at": _format_datetime(report.generated_at),
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "recommended_next_step": report.recommended_next_step,
        "campaign_count": _decimal_payload(report.campaign_count),
        "ready_campaign_count": _decimal_payload(report.ready_campaign_count),
        "watch_campaign_count": _decimal_payload(report.watch_campaign_count),
        "blocked_campaign_count": _decimal_payload(report.blocked_campaign_count),
        "high_spend_surge_count": _decimal_payload(report.high_spend_surge_count),
        "high_ad_volume_count": _decimal_payload(report.high_ad_volume_count),
        "high_message_shift_count": _decimal_payload(report.high_message_shift_count),
        "high_opposition_response_count": _decimal_payload(
            report.high_opposition_response_count,
        ),
        "stale_observation_count": _decimal_payload(report.stale_observation_count),
        "thin_source_count": _decimal_payload(report.thin_source_count),
        "average_spend_surge_score": _decimal_payload(
            report.average_spend_surge_score,
        ),
        "average_ad_volume_score": _decimal_payload(report.average_ad_volume_score),
        "average_message_shift_score": _decimal_payload(
            report.average_message_shift_score,
        ),
        "average_opposition_response_score": _decimal_payload(
            report.average_opposition_response_score,
        ),
        "average_source_count": _decimal_payload(report.average_source_count),
        "max_observation_age_seconds": _decimal_payload(
            report.max_observation_age_seconds,
        ),
        "rows": tuple(_row_payload(row) for row in report.rows),
        "spend_model_versions": report.spend_model_versions,
        "reason_code_counts": tuple(
            _reason_count_payload(item) for item in report.reason_code_counts
        ),
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
