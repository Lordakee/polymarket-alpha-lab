"""Pure Phase 1 OPEC quota compliance digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION = (
    "market-research-energy-opec-quota-compliance-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

RISK_LOW = "low"
RISK_WATCH = "watch"
RISK_HIGH = "high"
RISK_STATUSES = (RISK_LOW, RISK_WATCH, RISK_HIGH)
RISK_SORT_RANK = {
    RISK_HIGH: 0,
    RISK_WATCH: 1,
    RISK_LOW: 2,
}

REASON_PREFIX = "market_research_energy_opec_quota_compliance_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
LOW_RISK_REASON = f"{REASON_PREFIX}low_risk"
OVERPRODUCTION_REASON = f"{REASON_PREFIX}overproduction"
SEVERE_OVERPRODUCTION_REASON = f"{REASON_PREFIX}severe_overproduction"
PRODUCTION_REVISION_REASON = f"{REASON_PREFIX}production_revision"
STALE_REPORT_REASON = f"{REASON_PREFIX}stale_report"
THIN_SECONDARY_SOURCES_REASON = f"{REASON_PREFIX}thin_secondary_sources"
THIN_SPARE_CAPACITY_REASON = f"{REASON_PREFIX}thin_spare_capacity"

HIGH_RISK_PRESENT_REASON = f"{REASON_PREFIX}high_risk_present"
WATCH_RISK_PRESENT_REASON = f"{REASON_PREFIX}watch_risk_present"
STALE_REPORT_PRESENT_REASON = f"{REASON_PREFIX}stale_report_present"
THIN_SECONDARY_SOURCES_PRESENT_REASON = (
    f"{REASON_PREFIX}thin_secondary_sources_present"
)
ALL_LOW_RISK_REASON = f"{REASON_PREFIX}all_low_risk"

ROW_REASON_CODE_SEQUENCE = (
    SEVERE_OVERPRODUCTION_REASON,
    OVERPRODUCTION_REASON,
    PRODUCTION_REVISION_REASON,
    STALE_REPORT_REASON,
    THIN_SECONDARY_SOURCES_REASON,
    THIN_SPARE_CAPACITY_REASON,
    LOW_RISK_REASON,
)
REASON_CODE_COUNT_SEQUENCE = (
    OVERPRODUCTION_REASON,
    PRODUCTION_REVISION_REASON,
    SEVERE_OVERPRODUCTION_REASON,
    STALE_REPORT_REASON,
    THIN_SECONDARY_SOURCES_REASON,
    THIN_SPARE_CAPACITY_REASON,
    LOW_RISK_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    HIGH_RISK_PRESENT_REASON,
    WATCH_RISK_PRESENT_REASON,
    STALE_REPORT_PRESENT_REASON,
    THIN_SECONDARY_SOURCES_PRESENT_REASON,
    ALL_LOW_RISK_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_energy_opec_quota_compliance_digest",
    STATUS_WATCH: "watch_report_only_market_research_energy_opec_quota_compliance_digest",
    STATUS_BLOCKED: (
        "escalate_report_only_market_research_energy_opec_quota_compliance_digest"
    ),
}
NO_INPUT_NEXT_STEP = (
    "hold_report_only_market_research_energy_opec_quota_compliance_digest"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

REFERENCE_REDACTION_FRAGMENTS = (
    "://",
    "?",
    "token",
    "secret",
    "vendor",
    "private",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyOpecQuotaComplianceDigestConfig",
    "MarketResearchEnergyOpecQuotaComplianceDigestInputRow",
    "MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount",
    "MarketResearchEnergyOpecQuotaComplianceDigestReport",
    "MarketResearchEnergyOpecQuotaComplianceDigestRow",
    "build_market_research_energy_opec_quota_compliance_digest",
    "market_research_energy_opec_quota_compliance_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyOpecQuotaComplianceDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION
    )
    fresh_report_max_age_seconds: Decimal = Decimal("86400.000000")
    min_secondary_source_count: Decimal = Decimal("2.000000")
    material_overproduction_threshold_bpd: Decimal = Decimal("250000.000000")
    severe_overproduction_threshold_bpd: Decimal = Decimal("750000.000000")
    material_revision_threshold_bpd: Decimal = Decimal("300000.000000")
    thin_spare_capacity_threshold_bpd: Decimal = Decimal("1000000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyOpecQuotaComplianceDigestConfig:
            raise TypeError(
                "MarketResearchEnergyOpecQuotaComplianceDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyOpecQuotaComplianceDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEnergyOpecQuotaComplianceDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_report_max_age_seconds",
            _require_positive_decimal(
                "fresh_report_max_age_seconds",
                self.fresh_report_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_secondary_source_count",
            _require_positive_count_decimal(
                "min_secondary_source_count",
                self.min_secondary_source_count,
            ),
        )
        for field_name in (
            "material_overproduction_threshold_bpd",
            "severe_overproduction_threshold_bpd",
            "material_revision_threshold_bpd",
            "thin_spare_capacity_threshold_bpd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.severe_overproduction_threshold_bpd
            < self.material_overproduction_threshold_bpd
        ):
            raise ValueError(
                "severe_overproduction_threshold_bpd must be at least "
                "material_overproduction_threshold_bpd",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyOpecQuotaComplianceDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    producer_group: str
    member_country: str
    quota_period: str
    quota_source_reference: str
    report_timestamp: datetime
    acknowledged_at: datetime | None
    secondary_source_count: Decimal
    quota_bpd: Decimal
    estimated_production_bpd: Decimal
    prior_estimated_production_bpd: Decimal
    spare_capacity_bpd: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyOpecQuotaComplianceDigestInputRow:
            raise TypeError(
                "MarketResearchEnergyOpecQuotaComplianceDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyOpecQuotaComplianceDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchEnergyOpecQuotaComplianceDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "market_slug",
            "producer_group",
            "member_country",
            "quota_period",
            "quota_source_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "report_timestamp",
            _as_utc("report_timestamp", self.report_timestamp),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "secondary_source_count",
            _require_nonnegative_count_decimal(
                "secondary_source_count",
                self.secondary_source_count,
            ),
        )
        object.__setattr__(
            self,
            "quota_bpd",
            _require_positive_decimal("quota_bpd", self.quota_bpd),
        )
        for field_name in (
            "estimated_production_bpd",
            "prior_estimated_production_bpd",
            "spare_capacity_bpd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    report_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount",
            )
        _require_member(
            "reason_code",
            self.reason_code,
            REASON_CODE_COUNT_SEQUENCE,
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "report_ratio",
            _require_ratio_decimal("report_ratio", self.report_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyOpecQuotaComplianceDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    producer_group: str
    member_country: str
    quota_period: str
    redacted_quota_source_reference: str
    risk_status: str
    report_timestamp: datetime
    acknowledged_at: datetime | None
    report_age_seconds: Decimal
    secondary_source_count: Decimal
    quota_bpd: Decimal
    estimated_production_bpd: Decimal
    prior_estimated_production_bpd: Decimal
    spare_capacity_bpd: Decimal
    production_surprise_bpd: Decimal
    production_revision_bpd: Decimal
    overproduction_bpd: Decimal
    compliance_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyOpecQuotaComplianceDigestRow:
            raise TypeError(
                "MarketResearchEnergyOpecQuotaComplianceDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyOpecQuotaComplianceDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchEnergyOpecQuotaComplianceDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "market_slug",
            "producer_group",
            "member_country",
            "quota_period",
            "redacted_quota_source_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "report_timestamp",
            _as_utc("report_timestamp", self.report_timestamp),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in (
            "report_age_seconds",
            "secondary_source_count",
            "estimated_production_bpd",
            "prior_estimated_production_bpd",
            "spare_capacity_bpd",
            "overproduction_bpd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "secondary_source_count",
            _require_nonnegative_count_decimal(
                "secondary_source_count",
                self.secondary_source_count,
            ),
        )
        object.__setattr__(
            self,
            "quota_bpd",
            _require_positive_decimal("quota_bpd", self.quota_bpd),
        )
        for field_name in ("production_surprise_bpd", "production_revision_bpd"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "compliance_ratio",
            _require_nonnegative_decimal("compliance_ratio", self.compliance_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyOpecQuotaComplianceDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    screened_market_count: Decimal
    low_risk_count: Decimal
    watch_risk_count: Decimal
    high_risk_count: Decimal
    overproduction_count: Decimal
    severe_overproduction_count: Decimal
    production_revision_count: Decimal
    thin_secondary_source_count: Decimal
    stale_report_count: Decimal
    thin_spare_capacity_count: Decimal
    max_overproduction_bpd: Decimal
    average_compliance_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount,
        ...,
    ]
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyOpecQuotaComplianceDigestReport:
            raise TypeError(
                "MarketResearchEnergyOpecQuotaComplianceDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyOpecQuotaComplianceDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchEnergyOpecQuotaComplianceDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "screened_market_count",
            "low_risk_count",
            "watch_risk_count",
            "high_risk_count",
            "overproduction_count",
            "severe_overproduction_count",
            "production_revision_count",
            "thin_secondary_source_count",
            "stale_report_count",
            "thin_spare_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_overproduction_bpd", "average_compliance_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_energy_opec_quota_compliance_digest(
    rows: tuple[object, ...] | list[object],
    *,
    config: MarketResearchEnergyOpecQuotaComplianceDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyOpecQuotaComplianceDigestReport:
    """Reduce OPEC quota compliance observations into a report-only screen."""

    if type(config) is not MarketResearchEnergyOpecQuotaComplianceDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEnergyOpecQuotaComplianceDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)

    if not input_rows:
        return MarketResearchEnergyOpecQuotaComplianceDigestReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            source_row_count=ZERO,
            screened_market_count=ZERO,
            low_risk_count=ZERO,
            watch_risk_count=ZERO,
            high_risk_count=ZERO,
            overproduction_count=ZERO,
            severe_overproduction_count=ZERO,
            production_revision_count=ZERO,
            thin_secondary_source_count=ZERO,
            stale_report_count=ZERO,
            thin_spare_capacity_count=ZERO,
            max_overproduction_bpd=ZERO,
            average_compliance_ratio=ZERO,
            digest_status=STATUS_READY,
            recommended_next_step=NO_INPUT_NEXT_STEP,
            reason_codes=(NO_INPUTS_REASON,),
            reason_code_counts=(),
            rows=(),
        )

    output_rows = tuple(
        sorted(
            (_digest_row(row, config=config, generated_at=generated_at_utc) for row in input_rows),
            key=_row_sort_key,
        ),
    )

    low_count = _count_rows_with_status(output_rows, RISK_LOW)
    watch_count = _count_rows_with_status(output_rows, RISK_WATCH)
    high_count = _count_rows_with_status(output_rows, RISK_HIGH)
    overproduction_count = _count_rows_matching(
        output_rows,
        lambda row: row.production_surprise_bpd
        >= config.material_overproduction_threshold_bpd,
    )
    severe_overproduction_count = _count_rows_matching(
        output_rows,
        lambda row: row.production_surprise_bpd
        >= config.severe_overproduction_threshold_bpd,
    )
    production_revision_count = _count_rows_with_reason(
        output_rows,
        PRODUCTION_REVISION_REASON,
    )
    thin_secondary_source_count = _count_rows_with_reason(
        output_rows,
        THIN_SECONDARY_SOURCES_REASON,
    )
    stale_report_count = _count_rows_with_reason(output_rows, STALE_REPORT_REASON)
    thin_spare_capacity_count = _count_rows_with_reason(
        output_rows,
        THIN_SPARE_CAPACITY_REASON,
    )
    digest_status = _digest_status(high_count=high_count, watch_count=watch_count)

    return MarketResearchEnergyOpecQuotaComplianceDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_decimal_count(len(input_rows)),
        screened_market_count=_decimal_count(len(output_rows)),
        low_risk_count=low_count,
        watch_risk_count=watch_count,
        high_risk_count=high_count,
        overproduction_count=overproduction_count,
        severe_overproduction_count=severe_overproduction_count,
        production_revision_count=production_revision_count,
        thin_secondary_source_count=thin_secondary_source_count,
        stale_report_count=stale_report_count,
        thin_spare_capacity_count=thin_spare_capacity_count,
        max_overproduction_bpd=_max_overproduction_bpd(output_rows),
        average_compliance_ratio=_average_compliance_ratio(output_rows),
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reason_codes=_report_reason_codes(
            rows=output_rows,
            high_count=high_count,
            watch_count=watch_count,
            stale_report_count=stale_report_count,
            thin_secondary_source_count=thin_secondary_source_count,
        ),
        reason_code_counts=_reason_code_counts(output_rows),
        rows=output_rows,
    )


def market_research_energy_opec_quota_compliance_digest_payload(
    report: MarketResearchEnergyOpecQuotaComplianceDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyOpecQuotaComplianceDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchEnergyOpecQuotaComplianceDigestReport",
        )
    _require_hard_flags("report", report)
    return _payload_value(report)


def _digest_row(
    row: MarketResearchEnergyOpecQuotaComplianceDigestInputRow,
    *,
    config: MarketResearchEnergyOpecQuotaComplianceDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyOpecQuotaComplianceDigestRow:
    if row.report_timestamp > generated_at:
        raise ValueError("report_timestamp cannot be after generated_at")
    report_age_seconds = _seconds_between(generated_at, row.report_timestamp)
    production_surprise_bpd = _quantize(row.estimated_production_bpd - row.quota_bpd)
    production_revision_bpd = _quantize(
        row.estimated_production_bpd - row.prior_estimated_production_bpd,
    )
    overproduction_bpd = max(production_surprise_bpd, ZERO)
    compliance_ratio = _divide(row.estimated_production_bpd, row.quota_bpd)
    reason_codes = _row_reason_codes(
        production_surprise_bpd=production_surprise_bpd,
        production_revision_bpd=production_revision_bpd,
        report_age_seconds=report_age_seconds,
        row=row,
        config=config,
    )
    risk_status = _risk_status(reason_codes)

    return MarketResearchEnergyOpecQuotaComplianceDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        market_slug=row.market_slug,
        producer_group=row.producer_group,
        member_country=row.member_country,
        quota_period=row.quota_period,
        redacted_quota_source_reference=_redact_reference(row.quota_source_reference),
        risk_status=risk_status,
        report_timestamp=row.report_timestamp,
        acknowledged_at=row.acknowledged_at,
        report_age_seconds=report_age_seconds,
        secondary_source_count=row.secondary_source_count,
        quota_bpd=row.quota_bpd,
        estimated_production_bpd=row.estimated_production_bpd,
        prior_estimated_production_bpd=row.prior_estimated_production_bpd,
        spare_capacity_bpd=row.spare_capacity_bpd,
        production_surprise_bpd=production_surprise_bpd,
        production_revision_bpd=production_revision_bpd,
        overproduction_bpd=overproduction_bpd,
        compliance_ratio=compliance_ratio,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    production_surprise_bpd: Decimal,
    production_revision_bpd: Decimal,
    report_age_seconds: Decimal,
    row: MarketResearchEnergyOpecQuotaComplianceDigestInputRow,
    config: MarketResearchEnergyOpecQuotaComplianceDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if production_surprise_bpd >= config.severe_overproduction_threshold_bpd:
        reasons.append(SEVERE_OVERPRODUCTION_REASON)
    elif production_surprise_bpd >= config.material_overproduction_threshold_bpd:
        reasons.append(OVERPRODUCTION_REASON)
    if abs(production_revision_bpd) >= config.material_revision_threshold_bpd:
        reasons.append(PRODUCTION_REVISION_REASON)
    if report_age_seconds > config.fresh_report_max_age_seconds:
        reasons.append(STALE_REPORT_REASON)
    if row.secondary_source_count < config.min_secondary_source_count:
        reasons.append(THIN_SECONDARY_SOURCES_REASON)
    if row.spare_capacity_bpd < config.thin_spare_capacity_threshold_bpd:
        reasons.append(THIN_SPARE_CAPACITY_REASON)
    if not reasons:
        reasons.append(LOW_RISK_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODE_SEQUENCE,
    )


def _risk_status(reason_codes: tuple[str, ...]) -> str:
    if SEVERE_OVERPRODUCTION_REASON in reason_codes:
        return RISK_HIGH
    if (
        OVERPRODUCTION_REASON in reason_codes
        and PRODUCTION_REVISION_REASON in reason_codes
    ):
        return RISK_HIGH
    if LOW_RISK_REASON in reason_codes and len(reason_codes) == 1:
        return RISK_LOW
    return RISK_WATCH


def _digest_status(*, high_count: Decimal, watch_count: Decimal) -> str:
    if high_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    *,
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
    high_count: Decimal,
    watch_count: Decimal,
    stale_report_count: Decimal,
    thin_secondary_source_count: Decimal,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons: list[str] = []
    if high_count > ZERO:
        reasons.append(HIGH_RISK_PRESENT_REASON)
    if watch_count > ZERO:
        reasons.append(WATCH_RISK_PRESENT_REASON)
    if stale_report_count > ZERO:
        reasons.append(STALE_REPORT_PRESENT_REASON)
    if thin_secondary_source_count > ZERO:
        reasons.append(THIN_SECONDARY_SOURCES_PRESENT_REASON)
    if not reasons:
        reasons.append(ALL_LOW_RISK_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
) -> tuple[MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    denominator = _decimal_count(len(rows))
    counts = []
    for reason_code in REASON_CODE_COUNT_SEQUENCE:
        count = _count_rows_with_reason(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    report_ratio=_divide(count, denominator),
                ),
            )
    return tuple(counts)


def _row_sort_key(
    row: MarketResearchEnergyOpecQuotaComplianceDigestRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        RISK_SORT_RANK[row.risk_status],
        -row.overproduction_bpd,
        row.market_slug,
        row.member_country,
        row.research_key,
    )


def _normalize_input_rows(
    rows: tuple[object, ...] | list[object],
) -> tuple[MarketResearchEnergyOpecQuotaComplianceDigestInputRow, ...]:
    if type(rows) not in (tuple, list):
        raise TypeError("rows must be a tuple or list")
    normalized = []
    for row in rows:
        if type(row) is not MarketResearchEnergyOpecQuotaComplianceDigestInputRow:
            raise ValueError(
                "rows must contain only "
                "MarketResearchEnergyOpecQuotaComplianceDigestInputRow",
            )
        _require_hard_flags("input row", row)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...]:
    if type(rows) is not tuple:
        raise TypeError("rows must be a tuple")
    normalized = []
    for row in rows:
        if type(row) is not MarketResearchEnergyOpecQuotaComplianceDigestRow:
            raise ValueError(
                "rows must contain only "
                "MarketResearchEnergyOpecQuotaComplianceDigestRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise TypeError("reason_code_counts must be a tuple")
    normalized = []
    for row in rows:
        if type(row) is not MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain only "
                "MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: REASON_CODE_COUNT_SEQUENCE.index(row.reason_code),
        ),
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_member(field_name, reason_code, allowed_sequence)
    deduped = tuple(
        reason_code for reason_code in allowed_sequence if reason_code in value
    )
    if len(deduped) != len(value):
        raise ValueError(f"{field_name} must not contain duplicate reason codes")
    if not deduped:
        raise ValueError(f"{field_name} must not be empty")
    return deduped


def _validate_row(row: MarketResearchEnergyOpecQuotaComplianceDigestRow) -> None:
    if row.overproduction_bpd != max(row.production_surprise_bpd, ZERO):
        raise ValueError("overproduction_bpd must match positive production surprise")
    if row.risk_status != _risk_status(row.reason_codes):
        raise ValueError("risk_status must match row reason codes")


def _validate_report(report: MarketResearchEnergyOpecQuotaComplianceDigestReport) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.screened_market_count != row_count:
        raise ValueError("screened_market_count must match rows")
    if report.source_row_count != row_count:
        raise ValueError("source_row_count must match rows")
    if (
        report.low_risk_count + report.watch_risk_count + report.high_risk_count
        != report.screened_market_count
    ):
        raise ValueError("risk counts must sum to screened_market_count")
    if report.digest_status != _digest_status(
        high_count=report.high_risk_count,
        watch_count=report.watch_risk_count,
    ):
        raise ValueError("digest_status must match risk counts")
    if not report.rows and report.recommended_next_step != NO_INPUT_NEXT_STEP:
        raise ValueError("recommended_next_step must hold empty reports")
    if report.rows and report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _count_rows_with_status(
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.risk_status == status))


def _count_rows_with_reason(
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count_rows_matching(
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
    predicate: object,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if predicate(row)))


def _max_overproduction_bpd(
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(max(row.overproduction_bpd for row in rows))


def _average_compliance_ratio(
    rows: tuple[MarketResearchEnergyOpecQuotaComplianceDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _divide(
        sum((row.compliance_ratio for row in rows), ZERO),
        _decimal_count(len(rows)),
    )


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in REFERENCE_REDACTION_FRAGMENTS):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _payload_value(value: object) -> Any:
    if is_dataclass(value):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("later datetime must be at or after earlier datetime")
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be single-line text")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_hard_flags(label: str, value: object) -> None:
    if (
        getattr(value, "paper_only", None) is not True
        or getattr(value, "report_only", None) is not True
        or getattr(value, "readonly", None) is not True
    ):
        raise ValueError(f"{label} hard flags must be true")
