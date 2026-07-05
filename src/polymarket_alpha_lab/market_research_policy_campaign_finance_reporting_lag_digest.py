"""Pure Phase 1 policy campaign finance reporting lag digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION = (
    "market-research-policy-campaign-finance-reporting-lag-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
LAG_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_policy_campaign_finance_reporting_lag_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
REPORTING_LAG_BLOCK_REASON = f"{REASON_PREFIX}reporting_lag_block"
MISSING_FILING_REASON = f"{REASON_PREFIX}missing_filing"
REPORTING_LAG_WATCH_REASON = f"{REASON_PREFIX}reporting_lag_watch"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
MATERIAL_BLOCK_REASON = f"{REASON_PREFIX}material_block"
MATERIAL_WATCH_REASON = f"{REASON_PREFIX}material_watch"
READY_REASON = f"{REASON_PREFIX}ready"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    REPORTING_LAG_BLOCK_REASON,
    MISSING_FILING_REASON,
    REPORTING_LAG_WATCH_REASON,
    THIN_SOURCES_REASON,
    MATERIAL_BLOCK_REASON,
    MATERIAL_WATCH_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    REPORTING_LAG_BLOCK_REASON,
    MISSING_FILING_REASON,
    REPORTING_LAG_WATCH_REASON,
    THIN_SOURCES_REASON,
    MATERIAL_BLOCK_REASON,
    MATERIAL_WATCH_REASON,
    READY_REASON,
)

RECOMMENDED_NEXT_STEPS = {
    STATUS_READY: "allow_report_only_policy_campaign_finance_reporting_lag_digest",
    STATUS_WATCH: "watch_report_only_policy_campaign_finance_reporting_lag_digest",
    STATUS_BLOCKED: "block_report_only_policy_campaign_finance_reporting_lag_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

SENSITIVE_REFERENCE_FRAGMENTS = (
    "credential",
    "private",
    "secret",
    "token",
)
PUBLIC_REFERENCE_FRAGMENTS = (
    "campaign",
    "fec",
    "finance",
    "filing",
    "public",
    "report",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyCampaignFinanceReportingLagDigestConfig",
    "MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow",
    "MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount",
    "MarketResearchPolicyCampaignFinanceReportingLagDigestReport",
    "MarketResearchPolicyCampaignFinanceReportingLagDigestRow",
    "build_market_research_policy_campaign_finance_reporting_lag_digest",
    "market_research_policy_campaign_finance_reporting_lag_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignFinanceReportingLagDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION
    )
    max_ready_reporting_lag_seconds: Decimal = Decimal("86400.000000")
    max_watch_reporting_lag_seconds: Decimal = Decimal("259200.000000")
    min_public_source_count: Decimal = Decimal("2.000000")
    materiality_watch_threshold: Decimal = Decimal("0.150000")
    materiality_block_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignFinanceReportingLagDigestConfig:
            raise TypeError(
                "MarketResearchPolicyCampaignFinanceReportingLagDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignFinanceReportingLagDigestConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_ready_reporting_lag_seconds",
            "max_watch_reporting_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_six_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_nonnegative_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        for field_name in (
            "materiality_watch_threshold",
            "materiality_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_ready_reporting_lag_seconds > self.max_watch_reporting_lag_seconds:
            raise ValueError(
                "max_watch_reporting_lag_seconds must be at least "
                "max_ready_reporting_lag_seconds",
            )
        if self.materiality_watch_threshold > self.materiality_block_threshold:
            raise ValueError(
                "materiality_block_threshold must be at least "
                "materiality_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow:
    research_id: str
    condition_id: str
    committee_id: str
    filing_type: str
    reporting_period_end_at: datetime
    filing_due_at: datetime
    filing_published_at: datetime | None
    source_observed_at: datetime
    public_source_reference: str
    public_source_count: Decimal
    disclosure_amount_usd: Decimal
    estimated_probability_impact: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
            "input row",
        )
        for field_name in (
            "research_id",
            "condition_id",
            "committee_id",
            "filing_type",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reporting_period_end_at",
            _as_utc("reporting_period_end_at", self.reporting_period_end_at),
        )
        object.__setattr__(
            self,
            "filing_due_at",
            _as_utc("filing_due_at", self.filing_due_at),
        )
        object.__setattr__(
            self,
            "filing_published_at",
            _as_optional_utc("filing_published_at", self.filing_published_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        if self.filing_due_at < self.reporting_period_end_at:
            raise ValueError(
                "filing_due_at must be on or after reporting_period_end_at",
            )
        if (
            self.filing_published_at is not None
            and self.source_observed_at < self.filing_published_at
        ):
            raise ValueError(
                "source_observed_at must be on or after filing_published_at",
            )
        _require_reference("public_source_reference", self.public_source_reference)
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        object.__setattr__(
            self,
            "disclosure_amount_usd",
            _require_nonnegative_six_decimal(
                "disclosure_amount_usd",
                self.disclosure_amount_usd,
            ),
        )
        object.__setattr__(
            self,
            "estimated_probability_impact",
            _require_ratio_decimal(
                "estimated_probability_impact",
                self.estimated_probability_impact,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignFinanceReportingLagDigestRow:
    research_id: str
    condition_id: str
    committee_id: str
    filing_type: str
    lag_status: str
    reporting_period_end_at: datetime
    filing_due_at: datetime
    filing_published_at: datetime | None
    source_observed_at: datetime
    reporting_lag_seconds: Decimal
    source_age_seconds: Decimal
    public_source_count: Decimal
    disclosure_amount_usd: Decimal
    estimated_probability_impact: Decimal
    redacted_public_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignFinanceReportingLagDigestRow:
            raise TypeError(
                "MarketResearchPolicyCampaignFinanceReportingLagDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignFinanceReportingLagDigestRow,
            "row",
        )
        for field_name in (
            "research_id",
            "condition_id",
            "committee_id",
            "filing_type",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("lag_status", self.lag_status)
        object.__setattr__(
            self,
            "reporting_period_end_at",
            _as_utc("reporting_period_end_at", self.reporting_period_end_at),
        )
        object.__setattr__(
            self,
            "filing_due_at",
            _as_utc("filing_due_at", self.filing_due_at),
        )
        object.__setattr__(
            self,
            "filing_published_at",
            _as_optional_utc("filing_published_at", self.filing_published_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in ("reporting_lag_seconds", "source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_six_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        object.__setattr__(
            self,
            "disclosure_amount_usd",
            _require_nonnegative_six_decimal(
                "disclosure_amount_usd",
                self.disclosure_amount_usd,
            ),
        )
        object.__setattr__(
            self,
            "estimated_probability_impact",
            _require_ratio_decimal(
                "estimated_probability_impact",
                self.estimated_probability_impact,
            ),
        )
        object.__setattr__(
            self,
            "redacted_public_source_reference",
            _require_redacted_reference(
                "redacted_public_source_reference",
                self.redacted_public_source_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    filing_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "filing_ratio",
            _require_ratio_decimal("filing_ratio", self.filing_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyCampaignFinanceReportingLagDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    filing_count: Decimal
    ready_filing_count: Decimal
    watch_filing_count: Decimal
    blocked_filing_count: Decimal
    missing_filing_count: Decimal
    lagged_filing_count: Decimal
    thin_source_count: Decimal
    material_filing_count: Decimal
    average_reporting_lag_seconds: Decimal
    max_reporting_lag_seconds: Decimal
    average_probability_impact: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyCampaignFinanceReportingLagDigestReport:
            raise TypeError(
                "MarketResearchPolicyCampaignFinanceReportingLagDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_REPORTING_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "filing_count",
            "ready_filing_count",
            "watch_filing_count",
            "blocked_filing_count",
            "missing_filing_count",
            "lagged_filing_count",
            "thin_source_count",
            "material_filing_count",
            "average_reporting_lag_seconds",
            "max_reporting_lag_seconds",
            "average_probability_impact",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_six_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_campaign_finance_reporting_lag_digest(
    input_rows: tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow, ...],
    *,
    config: MarketResearchPolicyCampaignFinanceReportingLagDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchPolicyCampaignFinanceReportingLagDigestReport:
    cfg = config or MarketResearchPolicyCampaignFinanceReportingLagDigestConfig()
    _require_exact_type(
        cfg,
        MarketResearchPolicyCampaignFinanceReportingLagDigestConfig,
        "config",
    )
    cfg = _rebuild_dataclass(
        cfg,
        MarketResearchPolicyCampaignFinanceReportingLagDigestConfig,
    )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(
        _row_from_input(input_row, config=cfg, generated_at=report_time)
        for input_row in normalized_inputs
    )
    rows = _ranked_rows(built_rows)
    filing_count = _count_decimal(len(rows))
    ready_filing_count = _count_decimal(
        sum(1 for row in rows if row.lag_status == STATUS_READY),
    )
    watch_filing_count = _count_decimal(
        sum(1 for row in rows if row.lag_status == STATUS_WATCH),
    )
    blocked_filing_count = _count_decimal(
        sum(1 for row in rows if row.lag_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(count.reason_code for count in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                filing_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(rows),
        blocked_filing_count=blocked_filing_count,
        watch_filing_count=watch_filing_count,
    )

    return MarketResearchPolicyCampaignFinanceReportingLagDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        filing_count=filing_count,
        ready_filing_count=ready_filing_count,
        watch_filing_count=watch_filing_count,
        blocked_filing_count=blocked_filing_count,
        missing_filing_count=_count_decimal(
            sum(1 for row in rows if MISSING_FILING_REASON in row.reason_codes),
        ),
        lagged_filing_count=_count_decimal(
            sum(
                1
                for row in rows
                if REPORTING_LAG_BLOCK_REASON in row.reason_codes
                or REPORTING_LAG_WATCH_REASON in row.reason_codes
            ),
        ),
        thin_source_count=_count_decimal(
            sum(1 for row in rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        material_filing_count=_count_decimal(
            sum(
                1
                for row in rows
                if MATERIAL_BLOCK_REASON in row.reason_codes
                or MATERIAL_WATCH_REASON in row.reason_codes
            ),
        ),
        average_reporting_lag_seconds=_ratio(
            _sum_decimal(row.reporting_lag_seconds for row in rows),
            filing_count,
        ),
        max_reporting_lag_seconds=max(
            (row.reporting_lag_seconds for row in rows),
            default=ZERO,
        ),
        average_probability_impact=_ratio(
            _sum_decimal(row.estimated_probability_impact for row in rows),
            filing_count,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in rows),
            filing_count,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_campaign_finance_reporting_lag_digest_payload(
    report: MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
) -> MappingProxyType:
    _require_exact_type(
        report,
        MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
        "report",
    )
    _revalidate_report_for_payload(report)
    return _freeze(_payload_value(report))


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow, ...]:
    if type(input_rows) is not tuple:
        raise ValueError("input rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for input_row in input_rows:
        _require_exact_type(
            input_row,
            MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
            "input row",
        )
        rebuilt_input_row = _rebuild_dataclass(
            input_row,
            MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
        )
        _require_hard_flags("input row", input_row)
        if rebuilt_input_row.reporting_period_end_at > generated_at:
            raise ValueError("reporting_period_end_at must not be in the future")
        if rebuilt_input_row.filing_due_at > generated_at:
            raise ValueError("filing_due_at must not be in the future")
        if (
            rebuilt_input_row.filing_published_at is not None
            and rebuilt_input_row.filing_published_at > generated_at
        ):
            raise ValueError("filing_published_at must not be in the future")
        if rebuilt_input_row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be in the future")
        key = (rebuilt_input_row.research_id, rebuilt_input_row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate research ids")
        seen.add(key)
    return tuple(
        _rebuild_dataclass(
            input_row,
            MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
        )
        for input_row in input_rows
    )


def _row_from_input(
    input_row: MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
    *,
    config: MarketResearchPolicyCampaignFinanceReportingLagDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyCampaignFinanceReportingLagDigestRow:
    lag_end = input_row.filing_published_at or generated_at
    reporting_lag_seconds = _nonnegative_seconds_between(
        input_row.filing_due_at,
        lag_end,
    )
    source_age_seconds = _nonnegative_seconds_between(
        input_row.source_observed_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        input_row,
        config=config,
        reporting_lag_seconds=reporting_lag_seconds,
    )
    return MarketResearchPolicyCampaignFinanceReportingLagDigestRow(
        research_id=input_row.research_id,
        condition_id=input_row.condition_id,
        committee_id=input_row.committee_id,
        filing_type=input_row.filing_type,
        lag_status=_row_status(reason_codes),
        reporting_period_end_at=input_row.reporting_period_end_at,
        filing_due_at=input_row.filing_due_at,
        filing_published_at=input_row.filing_published_at,
        source_observed_at=input_row.source_observed_at,
        reporting_lag_seconds=reporting_lag_seconds,
        source_age_seconds=source_age_seconds,
        public_source_count=input_row.public_source_count,
        disclosure_amount_usd=input_row.disclosure_amount_usd,
        estimated_probability_impact=input_row.estimated_probability_impact,
        redacted_public_source_reference=_redacted_reference(
            input_row.public_source_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    input_row: MarketResearchPolicyCampaignFinanceReportingLagDigestInputRow,
    *,
    config: MarketResearchPolicyCampaignFinanceReportingLagDigestConfig,
    reporting_lag_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if input_row.filing_published_at is None:
        reasons.append(MISSING_FILING_REASON)
    elif reporting_lag_seconds > config.max_watch_reporting_lag_seconds:
        reasons.append(REPORTING_LAG_BLOCK_REASON)
    elif reporting_lag_seconds > config.max_ready_reporting_lag_seconds:
        reasons.append(REPORTING_LAG_WATCH_REASON)
    if input_row.public_source_count < config.min_public_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if input_row.estimated_probability_impact >= config.materiality_block_threshold:
        reasons.append(MATERIAL_BLOCK_REASON)
    elif input_row.estimated_probability_impact >= config.materiality_watch_threshold:
        reasons.append(MATERIAL_WATCH_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        REPORTING_LAG_BLOCK_REASON in reason_codes
        or MISSING_FILING_REASON in reason_codes
        or MATERIAL_BLOCK_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_filing_count: Decimal,
    watch_filing_count: Decimal,
) -> str:
    if not has_inputs or blocked_filing_count > ZERO:
        return STATUS_BLOCKED
    if watch_filing_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestRow, ...],
) -> tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.lag_status),
                -row.estimated_probability_impact,
                row.committee_id,
                row.research_id,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[status]


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestRow, ...],
) -> tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount, ...]:
    total = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
            reason_code=reason_code,
            count=_require_positive_count_decimal("count", counts[reason_code]),
            filing_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(
            row,
            MarketResearchPolicyCampaignFinanceReportingLagDigestRow,
            "row",
        )
        _rebuild_dataclass(row, MarketResearchPolicyCampaignFinanceReportingLagDigestRow)
        _require_hard_flags("row", row)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_index = -1
    for count in counts:
        _require_exact_type(
            count,
            MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
            "reason code count",
        )
        _rebuild_dataclass(
            count,
            MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
        )
        _require_hard_flags("reason code count", count)
        index = REASON_CODE_SEQUENCE.index(count.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must be unique and sorted")
        previous_index = index
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in values
    )
    if normalized != values:
        raise ValueError("reason_codes must be unique and sorted")
    if not values:
        raise ValueError("reason_codes must not be empty")
    if READY_REASON in values and len(values) != 1:
        raise ValueError("reason_codes cannot mix ready with risk reasons")
    return values


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in values
    )
    if normalized != values:
        raise ValueError("reason_codes must be unique and sorted")
    if not values:
        raise ValueError("reason_codes must not be empty")
    return values


def _validate_row(
    row: MarketResearchPolicyCampaignFinanceReportingLagDigestRow,
) -> None:
    if row.filing_due_at < row.reporting_period_end_at:
        raise ValueError("filing_due_at must be on or after reporting_period_end_at")
    if (
        row.filing_published_at is not None
        and row.source_observed_at < row.filing_published_at
    ):
        raise ValueError("source_observed_at must be on or after filing_published_at")
    if row.filing_published_at is None:
        if MISSING_FILING_REASON not in row.reason_codes:
            raise ValueError("reason_codes must include missing filing")
    elif MISSING_FILING_REASON in row.reason_codes:
        raise ValueError("reason_codes must not include missing filing when present")
    if row.filing_published_at is not None:
        expected_lag = _nonnegative_seconds_between(
            row.filing_due_at,
            row.filing_published_at,
        )
        if row.reporting_lag_seconds != expected_lag:
            raise ValueError("reporting_lag_seconds must match filing timestamps")
    if row.lag_status != _row_status(row.reason_codes):
        raise ValueError("lag_status must match reason_codes")


def _validate_report(
    report: MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
) -> None:
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    filing_count = _count_decimal(len(report.rows))
    ready_filing_count = _count_decimal(
        sum(1 for row in report.rows if row.lag_status == STATUS_READY),
    )
    watch_filing_count = _count_decimal(
        sum(1 for row in report.rows if row.lag_status == STATUS_WATCH),
    )
    blocked_filing_count = _count_decimal(
        sum(1 for row in report.rows if row.lag_status == STATUS_BLOCKED),
    )
    if report.filing_count != filing_count:
        raise ValueError("filing_count must match rows")
    if report.ready_filing_count != ready_filing_count:
        raise ValueError("ready_filing_count must match rows")
    if report.watch_filing_count != watch_filing_count:
        raise ValueError("watch_filing_count must match rows")
    if report.blocked_filing_count != blocked_filing_count:
        raise ValueError("blocked_filing_count must match rows")
    if report.missing_filing_count != _count_decimal(
        sum(1 for row in report.rows if MISSING_FILING_REASON in row.reason_codes),
    ):
        raise ValueError("missing_filing_count must match rows")
    if report.lagged_filing_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if REPORTING_LAG_BLOCK_REASON in row.reason_codes
            or REPORTING_LAG_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("lagged_filing_count must match rows")
    if report.thin_source_count != _count_decimal(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.material_filing_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if MATERIAL_BLOCK_REASON in row.reason_codes
            or MATERIAL_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("material_filing_count must match rows")
    if report.average_reporting_lag_seconds != _ratio(
        _sum_decimal(row.reporting_lag_seconds for row in report.rows),
        report.filing_count,
    ):
        raise ValueError("average_reporting_lag_seconds must match rows")
    if report.max_reporting_lag_seconds != max(
        (row.reporting_lag_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_reporting_lag_seconds must match rows")
    if report.average_probability_impact != _ratio(
        _sum_decimal(row.estimated_probability_impact for row in report.rows),
        report.filing_count,
    ):
        raise ValueError("average_probability_impact must match rows")
    if report.average_public_source_count != _ratio(
        _sum_decimal(row.public_source_count for row in report.rows),
        report.filing_count,
    ):
        raise ValueError("average_public_source_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(count.reason_code for count in expected_counts)
    if not report.rows:
        expected_counts = (
            MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                filing_ratio=ONE,
            ),
        )
        expected_reason_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_filing_count=report.blocked_filing_count,
        watch_filing_count=report.watch_filing_count,
    ):
        raise ValueError("digest_status must match rows")


def _revalidate_report_for_payload(
    report: MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
) -> None:
    _require_exact_type(
        report,
        MarketResearchPolicyCampaignFinanceReportingLagDigestReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_normalized_utc_datetime("generated_at", report.generated_at)
    if _normalize_rows(report.rows) != report.rows:
        raise ValueError("rows must be deterministically sorted")
    if _normalize_reason_code_counts(report.reason_code_counts) != report.reason_code_counts:
        raise ValueError("reason_code_counts must be deterministically sorted")
    if _normalize_report_reason_codes(report.reason_codes) != report.reason_codes:
        raise ValueError("reason_codes must be canonical")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    for count in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(count)
    _rebuild_dataclass(report, MarketResearchPolicyCampaignFinanceReportingLagDigestReport)
    _validate_report(report)


def _revalidate_row_for_payload(
    row: MarketResearchPolicyCampaignFinanceReportingLagDigestRow,
) -> None:
    _require_exact_type(
        row,
        MarketResearchPolicyCampaignFinanceReportingLagDigestRow,
        "row",
    )
    _require_hard_flags("row", row)
    for field_name in (
        "reporting_period_end_at",
        "filing_due_at",
        "source_observed_at",
    ):
        _require_normalized_utc_datetime(field_name, getattr(row, field_name))
    if row.filing_published_at is not None:
        _require_normalized_utc_datetime(
            "filing_published_at",
            row.filing_published_at,
        )
    _rebuild_dataclass(row, MarketResearchPolicyCampaignFinanceReportingLagDigestRow)
    _validate_row(row)


def _revalidate_reason_code_count_for_payload(
    count: MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
) -> None:
    _require_exact_type(
        count,
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
        "reason code count",
    )
    _require_hard_flags("reason code count", count)
    _rebuild_dataclass(
        count,
        MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount,
    )


def _rebuild_dataclass(value: object, expected_type: type[object]) -> Any:
    return expected_type(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _payload_value(value: Any, *, field_name: str = "payload") -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return format(value, "f")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    if type(value) is datetime:
        _require_normalized_utc_datetime(field_name, value)
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) is MarketResearchPolicyCampaignFinanceReportingLagDigestReport:
            _revalidate_report_for_payload(value)
        elif type(value) is MarketResearchPolicyCampaignFinanceReportingLagDigestRow:
            _revalidate_row_for_payload(value)
        elif (
            type(value)
            is MarketResearchPolicyCampaignFinanceReportingLagDigestReasonCodeCount
        ):
            _revalidate_reason_code_count_for_payload(value)
        else:
            raise ValueError("payload value contains an unsupported dataclass")
        return {
            field.name: _payload_value(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if type(value) is tuple:
        return tuple(_payload_value(item, field_name=field_name) for item in value)
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError(f"{field_name} must not be a public numeric primitive")
    raise ValueError("payload value is not supported")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in LAG_STATUSES:
        raise ValueError(f"{field_name} must be one of {LAG_STATUSES}")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    lowered = value.lower()
    if "://" in lowered or any(
        fragment in lowered for fragment in SENSITIVE_REFERENCE_FRAGMENTS
    ):
        raise ValueError(f"{field_name} must be a public string")
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical reference")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_reference(field_name, value)
    if not _is_redacted_reference(text):
        raise ValueError(f"{field_name} must be redacted or public")
    return text


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 19:
        return True
    lowered = value.lower()
    if "://" in lowered:
        return False
    if any(fragment in lowered for fragment in SENSITIVE_REFERENCE_FRAGMENTS):
        return False
    return any(fragment in lowered for fragment in PUBLIC_REFERENCE_FRAGMENTS)


def _redacted_reference(value: str) -> str:
    if _is_redacted_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_normalized_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")


def _require_six_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    return value


def _require_nonnegative_six_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_six_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _nonnegative_seconds_between(start: datetime, end: datetime) -> Decimal:
    if end <= start:
        return ZERO
    return _seconds_between(start, end)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


ZERO_TIME_OFFSET = UTC.utcoffset(None)
