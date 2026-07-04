"""Pure Phase 1 campaign finance filing lag digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_FILING_LAG_DIGEST_CONFIG_VERSION = (
    "market-research-policy-campaign-finance-filing-lag-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
FILING_LAG_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

FILING_TYPES = (
    "committee_report",
    "late_contribution",
    "independent_expenditure",
    "amendment",
    "missing_report",
)

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_campaign_finance_filing_lag_screening",
    WATCH_STATUS: "monitor_report_only_campaign_finance_filing_lag_screening",
    PASS_STATUS: "allow_report_only_campaign_finance_filing_lag_screening",
}

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_FILING_LAG_DIGEST_CONFIG_VERSION",
    "PolicyCampaignFinanceFilingLagDigestConfig",
    "PolicyCampaignFinanceFilingLagObservation",
    "PolicyCampaignFinanceFilingLagDigestRow",
    "PolicyCampaignFinanceFilingLagReasonCodeCount",
    "PolicyCampaignFinanceFilingLagDigestReport",
    "build_market_research_policy_campaign_finance_filing_lag_digest",
    "market_research_policy_campaign_finance_filing_lag_digest_payload",
)


@dataclass(frozen=True)
class PolicyCampaignFinanceFilingLagDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_FILING_LAG_DIGEST_CONFIG_VERSION
    )
    watch_lag_days: Decimal = Decimal("3.000000")
    blocked_lag_days: Decimal = Decimal("7.000000")
    watch_late_filing_amount_usd: Decimal = Decimal("250000.000000")
    blocked_late_filing_amount_usd: Decimal = Decimal("1000000.000000")
    watch_amendment_count: Decimal = Decimal("2.000000")
    blocked_amendment_count: Decimal = Decimal("4.000000")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCampaignFinanceFilingLagDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_FILING_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_lag_days",
            "blocked_lag_days",
            "watch_late_filing_amount_usd",
            "blocked_late_filing_amount_usd",
            "watch_amendment_count",
            "blocked_amendment_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_lag_days > self.blocked_lag_days:
            raise ValueError("watch_lag_days must not exceed blocked_lag_days")
        if self.watch_late_filing_amount_usd > self.blocked_late_filing_amount_usd:
            raise ValueError(
                "watch_late_filing_amount_usd must not exceed "
                "blocked_late_filing_amount_usd",
            )
        if self.watch_amendment_count > self.blocked_amendment_count:
            raise ValueError(
                "watch_amendment_count must not exceed blocked_amendment_count",
            )
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class PolicyCampaignFinanceFilingLagObservation:
    source_id: str
    market_slug: str
    jurisdiction: str
    committee_id: str
    filing_type: str
    expected_filing_count: Decimal
    received_filing_count: Decimal
    filing_lag_days: Decimal
    largest_late_filing_amount_usd: Decimal
    amendment_count: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCampaignFinanceFilingLagObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "jurisdiction",
            "committee_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("filing_type", self.filing_type, FILING_TYPES)
        for field_name in (
            "expected_filing_count",
            "received_filing_count",
            "filing_lag_days",
            "largest_late_filing_amount_usd",
            "amendment_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.received_filing_count > self.expected_filing_count:
            raise ValueError(
                "received_filing_count must not exceed expected_filing_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class PolicyCampaignFinanceFilingLagDigestRow:
    source_id: str
    market_slug: str
    jurisdiction: str
    committee_id: str
    filing_type: str
    expected_filing_count: Decimal
    received_filing_count: Decimal
    missing_filing_count: Decimal
    filing_lag_days: Decimal
    largest_late_filing_amount_usd: Decimal
    amendment_count: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    filing_lag_risk_score: Decimal
    filing_lag_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCampaignFinanceFilingLagDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "jurisdiction",
            "committee_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("filing_type", self.filing_type, FILING_TYPES)
        for field_name in (
            "expected_filing_count",
            "received_filing_count",
            "missing_filing_count",
            "filing_lag_days",
            "largest_late_filing_amount_usd",
            "amendment_count",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "filing_lag_risk_score",
            _normalize_probability("filing_lag_risk_score", self.filing_lag_risk_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("filing_lag_status", self.filing_lag_status, FILING_LAG_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class PolicyCampaignFinanceFilingLagReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            PolicyCampaignFinanceFilingLagReasonCodeCount,
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
class PolicyCampaignFinanceFilingLagDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    missing_filing_row_count: Decimal
    stale_source_count: Decimal
    amendment_burst_count: Decimal
    large_late_filing_count: Decimal
    max_filing_lag_days: Decimal
    max_late_filing_amount_usd: Decimal
    average_filing_lag_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PolicyCampaignFinanceFilingLagReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCampaignFinanceFilingLagDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CAMPAIGN_FINANCE_FILING_LAG_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "missing_filing_row_count",
            "stale_source_count",
            "amendment_burst_count",
            "large_late_filing_count",
            "max_filing_lag_days",
            "max_late_filing_amount_usd",
            "average_filing_lag_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, FILING_LAG_STATUSES)
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


def build_market_research_policy_campaign_finance_filing_lag_digest(
    observations: Iterable[PolicyCampaignFinanceFilingLagObservation],
    *,
    config: PolicyCampaignFinanceFilingLagDigestConfig,
    generated_at: datetime,
) -> PolicyCampaignFinanceFilingLagDigestReport:
    if type(config) is not PolicyCampaignFinanceFilingLagDigestConfig:
        raise ValueError(
            "config must be exactly PolicyCampaignFinanceFilingLagDigestConfig",
        )
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
    return PolicyCampaignFinanceFilingLagDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        missing_filing_row_count=_reason_count(
            rows,
            "campaign_finance_filing_missing_expected_report",
        ),
        stale_source_count=_reason_count(rows, "campaign_finance_filing_source_stale"),
        amendment_burst_count=_amendment_burst_count(rows),
        large_late_filing_count=_large_late_filing_count(rows),
        max_filing_lag_days=_max_row_decimal(rows, "filing_lag_days"),
        max_late_filing_amount_usd=_max_row_decimal(
            rows,
            "largest_late_filing_amount_usd",
        ),
        average_filing_lag_risk_score=_ratio(
            _sum_decimal(row.filing_lag_risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_policy_campaign_finance_filing_lag_digest_payload(
    report: PolicyCampaignFinanceFilingLagDigestReport,
) -> dict[str, Any]:
    if type(report) is not PolicyCampaignFinanceFilingLagDigestReport:
        raise ValueError(
            "report must be exactly PolicyCampaignFinanceFilingLagDigestReport",
        )
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: PolicyCampaignFinanceFilingLagObservation,
    *,
    config: PolicyCampaignFinanceFilingLagDigestConfig,
    generated_at: datetime,
) -> PolicyCampaignFinanceFilingLagDigestRow:
    missing_filing_count = _quantize_decimal(
        value.expected_filing_count - value.received_filing_count,
    )
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    filing_lag_status = _filing_lag_status(
        value,
        missing_filing_count=missing_filing_count,
        source_fresh=source_fresh,
        config=config,
    )
    return PolicyCampaignFinanceFilingLagDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        jurisdiction=value.jurisdiction,
        committee_id=value.committee_id,
        filing_type=value.filing_type,
        expected_filing_count=value.expected_filing_count,
        received_filing_count=value.received_filing_count,
        missing_filing_count=missing_filing_count,
        filing_lag_days=value.filing_lag_days,
        largest_late_filing_amount_usd=value.largest_late_filing_amount_usd,
        amendment_count=value.amendment_count,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        filing_lag_risk_score=_filing_lag_risk_score(
            value,
            missing_filing_count=missing_filing_count,
            source_fresh=source_fresh,
            config=config,
        ),
        filing_lag_status=filing_lag_status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            filing_lag_status=filing_lag_status,
            source_fresh=source_fresh,
            missing_filing_count=missing_filing_count,
            filing_lag_days=value.filing_lag_days,
            largest_late_filing_amount_usd=value.largest_late_filing_amount_usd,
            amendment_count=value.amendment_count,
            config=config,
        ),
    )


def _filing_lag_status(
    value: PolicyCampaignFinanceFilingLagObservation,
    *,
    missing_filing_count: Decimal,
    source_fresh: bool,
    config: PolicyCampaignFinanceFilingLagDigestConfig,
) -> str:
    if not source_fresh or missing_filing_count > ZERO:
        return BLOCKED_STATUS
    if value.filing_lag_days >= config.blocked_lag_days:
        return BLOCKED_STATUS
    if value.largest_late_filing_amount_usd >= config.blocked_late_filing_amount_usd:
        return BLOCKED_STATUS
    if value.amendment_count >= config.blocked_amendment_count:
        return BLOCKED_STATUS
    if value.filing_lag_days >= config.watch_lag_days:
        return WATCH_STATUS
    if value.largest_late_filing_amount_usd >= config.watch_late_filing_amount_usd:
        return WATCH_STATUS
    if value.amendment_count >= config.watch_amendment_count:
        return WATCH_STATUS
    return PASS_STATUS


def _filing_lag_risk_score(
    value: PolicyCampaignFinanceFilingLagObservation,
    *,
    missing_filing_count: Decimal,
    source_fresh: bool,
    config: PolicyCampaignFinanceFilingLagDigestConfig,
) -> Decimal:
    if not source_fresh or missing_filing_count > ZERO:
        return ONE
    return max(
        _capped_ratio(value.filing_lag_days, config.blocked_lag_days),
        _capped_ratio(
            value.largest_late_filing_amount_usd,
            config.blocked_late_filing_amount_usd,
        ),
        _capped_ratio(value.amendment_count, config.blocked_amendment_count),
    )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    filing_lag_status: str,
    source_fresh: bool,
    missing_filing_count: Decimal,
    filing_lag_days: Decimal,
    largest_late_filing_amount_usd: Decimal,
    amendment_count: Decimal,
    config: PolicyCampaignFinanceFilingLagDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(
        {
            BLOCKED_STATUS: "campaign_finance_filing_blocked",
            WATCH_STATUS: "campaign_finance_filing_watch",
            PASS_STATUS: "campaign_finance_filing_below_threshold",
        }[filing_lag_status],
    )
    reason_codes.append(
        "campaign_finance_filing_source_fresh"
        if source_fresh
        else "campaign_finance_filing_source_stale",
    )
    if missing_filing_count > ZERO:
        reason_codes.append("campaign_finance_filing_missing_expected_report")
    if filing_lag_days >= config.blocked_lag_days:
        reason_codes.append("campaign_finance_filing_late_blocked")
    elif filing_lag_days >= config.watch_lag_days:
        reason_codes.append("campaign_finance_filing_late_watch")
    if largest_late_filing_amount_usd >= config.blocked_late_filing_amount_usd:
        reason_codes.append("campaign_finance_filing_large_late_amount_blocked")
    elif largest_late_filing_amount_usd >= config.watch_late_filing_amount_usd:
        reason_codes.append("campaign_finance_filing_large_late_amount_watch")
    if amendment_count >= config.blocked_amendment_count:
        reason_codes.append("campaign_finance_filing_amendment_burst_blocked")
    elif amendment_count >= config.watch_amendment_count:
        reason_codes.append("campaign_finance_filing_amendment_burst_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("campaign_finance_filing_lag_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
) -> tuple[PolicyCampaignFinanceFilingLagReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("campaign_finance_filing_lag_digest_empty",):
        return (
            PolicyCampaignFinanceFilingLagReasonCodeCount(
                reason_code="campaign_finance_filing_lag_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        PolicyCampaignFinanceFilingLagReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[PolicyCampaignFinanceFilingLagObservation],
) -> tuple[PolicyCampaignFinanceFilingLagObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain PolicyCampaignFinanceFilingLagObservation",
        )
    normalized = tuple(observations)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyCampaignFinanceFilingLagObservation:
            raise ValueError(
                "observations must contain PolicyCampaignFinanceFilingLagObservation",
            )
        _require_hard_flags(value, "observation")
        if value.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[PolicyCampaignFinanceFilingLagDigestRow],
) -> tuple[PolicyCampaignFinanceFilingLagDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain PolicyCampaignFinanceFilingLagDigestRow")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not PolicyCampaignFinanceFilingLagDigestRow:
            raise ValueError("rows must contain PolicyCampaignFinanceFilingLagDigestRow")
        _require_hard_flags(row, "row")
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id")
        seen.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[PolicyCampaignFinanceFilingLagReasonCodeCount],
) -> tuple[PolicyCampaignFinanceFilingLagReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not PolicyCampaignFinanceFilingLagReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PolicyCampaignFinanceFilingLagReasonCodeCount",
            )
        _require_hard_flags(value, "reason_code_count")
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: PolicyCampaignFinanceFilingLagDigestRow) -> None:
    if row.missing_filing_count != _quantize_decimal(
        row.expected_filing_count - row.received_filing_count,
    ):
        raise ValueError("missing_filing_count must match expected and received filings")
    expected_status_reason = {
        BLOCKED_STATUS: "campaign_finance_filing_blocked",
        WATCH_STATUS: "campaign_finance_filing_watch",
        PASS_STATUS: "campaign_finance_filing_below_threshold",
    }[row.filing_lag_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("filing_lag_status must match reason_codes")
    if row.received_filing_count > row.expected_filing_count:
        raise ValueError(
            "received_filing_count must not exceed expected_filing_count",
        )


def _validate_report(report: PolicyCampaignFinanceFilingLagDigestReport) -> None:
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
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.missing_filing_row_count != _reason_count(
        report.rows,
        "campaign_finance_filing_missing_expected_report",
    ):
        raise ValueError("missing_filing_row_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "campaign_finance_filing_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.amendment_burst_count != _amendment_burst_count(report.rows):
        raise ValueError("amendment_burst_count must match rows")
    if report.large_late_filing_count != _large_late_filing_count(report.rows):
        raise ValueError("large_late_filing_count must match rows")
    if report.max_filing_lag_days != _max_row_decimal(report.rows, "filing_lag_days"):
        raise ValueError("max_filing_lag_days must match rows")
    if report.max_late_filing_amount_usd != _max_row_decimal(
        report.rows,
        "largest_late_filing_amount_usd",
    ):
        raise ValueError("max_late_filing_amount_usd must match rows")
    if report.average_filing_lag_risk_score != _ratio(
        _sum_decimal(row.filing_lag_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_filing_lag_risk_score must match rows")
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


def _digest_status(rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.filing_lag_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.filing_lag_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _row_sort_key(
    row: PolicyCampaignFinanceFilingLagDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.filing_lag_status],
        -row.filing_lag_risk_score,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.filing_lag_status == status))


def _amendment_burst_count(
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                "campaign_finance_filing_amendment_burst_blocked" in row.reason_codes
                or "campaign_finance_filing_amendment_burst_watch" in row.reason_codes
            )
        ),
    )


def _large_late_filing_count(
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                "campaign_finance_filing_large_late_amount_blocked" in row.reason_codes
                or "campaign_finance_filing_large_late_amount_watch" in row.reason_codes
            )
        ),
    )


def _reason_count(
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[PolicyCampaignFinanceFilingLagDigestRow, ...],
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


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return min(ONE, _ratio(numerator, denominator))


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
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


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
