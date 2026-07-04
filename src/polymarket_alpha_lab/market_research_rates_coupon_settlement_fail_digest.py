"""Pure Phase 1 Treasury coupon settlement-fail stress digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_RATES_COUPON_SETTLEMENT_FAIL_DIGEST_CONFIG_VERSION = (
    "market-research-rates-coupon-settlement-fail-digest-v0"
)

SETTLEMENT_FAIL_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "rates_coupon_settlement_fail_aged_fail",
    "rates_coupon_settlement_fail_auction_cycle_pressure",
    "rates_coupon_settlement_fail_high_fail_rate",
    "rates_coupon_settlement_fail_inline",
    "rates_coupon_settlement_fail_low_source_quorum",
    "rates_coupon_settlement_fail_repo_specialness",
    "rates_coupon_settlement_fail_stale_source",
    "rates_coupon_settlement_fail_thin_deliverable_supply",
    "rates_coupon_settlement_fail_watch_age",
    "rates_coupon_settlement_fail_watch_fail_rate",
)
REPORT_REASON_CODES = (
    "rates_coupon_settlement_fail_aged_fail_present",
    "rates_coupon_settlement_fail_auction_cycle_pressure_present",
    "rates_coupon_settlement_fail_digest_clear",
    "rates_coupon_settlement_fail_digest_empty",
    "rates_coupon_settlement_fail_high_fail_rate_present",
    "rates_coupon_settlement_fail_low_source_quorum_present",
    "rates_coupon_settlement_fail_repo_specialness_present",
    "rates_coupon_settlement_fail_stale_source_present",
    "rates_coupon_settlement_fail_thin_deliverable_supply_present",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
STATUS_RISK_SCORE = {
    "blocked": ONE,
    "watch": WATCH_RISK_SCORE,
    "pass": ZERO,
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_CUSIP_RE = re.compile(r"^[A-Z0-9]{9}$")


__all__ = (
    "DEFAULT_RATES_COUPON_SETTLEMENT_FAIL_DIGEST_CONFIG_VERSION",
    "RatesCouponSettlementFailDigestConfig",
    "RatesCouponSettlementFailObservation",
    "RatesCouponSettlementFailDigestRow",
    "RatesCouponSettlementFailReasonCodeCount",
    "RatesCouponSettlementFailDigestReport",
    "build_market_research_rates_coupon_settlement_fail_digest",
    "market_research_rates_coupon_settlement_fail_digest_payload",
)


@dataclass(frozen=True)
class RatesCouponSettlementFailDigestConfig:
    config_version: str = DEFAULT_RATES_COUPON_SETTLEMENT_FAIL_DIGEST_CONFIG_VERSION
    watch_fail_rate_bps: Decimal = Decimal("250.000000")
    blocked_fail_rate_bps: Decimal = Decimal("500.000000")
    watch_settlement_age_days: Decimal = Decimal("2.000000")
    blocked_settlement_age_days: Decimal = Decimal("5.000000")
    watch_repo_specialness_bps: Decimal = Decimal("75.000000")
    blocked_repo_specialness_bps: Decimal = Decimal("150.000000")
    auction_cycle_window_days: Decimal = Decimal("5.000000")
    thin_deliverable_supply_score: Decimal = Decimal("0.350000")
    stale_source_minutes: Decimal = Decimal("120.000000")
    min_source_quorum: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesCouponSettlementFailDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RATES_COUPON_SETTLEMENT_FAIL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_fail_rate_bps",
            "blocked_fail_rate_bps",
            "watch_settlement_age_days",
            "blocked_settlement_age_days",
            "watch_repo_specialness_bps",
            "blocked_repo_specialness_bps",
            "auction_cycle_window_days",
            "stale_source_minutes",
            "min_source_quorum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "thin_deliverable_supply_score",
            _require_ratio(
                "thin_deliverable_supply_score",
                self.thin_deliverable_supply_score,
            ),
        )
        if self.watch_fail_rate_bps > self.blocked_fail_rate_bps:
            raise ValueError(
                "watch_fail_rate_bps must not exceed blocked_fail_rate_bps",
            )
        if self.watch_settlement_age_days > self.blocked_settlement_age_days:
            raise ValueError(
                "watch_settlement_age_days must not exceed "
                "blocked_settlement_age_days",
            )
        if self.watch_repo_specialness_bps > self.blocked_repo_specialness_bps:
            raise ValueError(
                "watch_repo_specialness_bps must not exceed "
                "blocked_repo_specialness_bps",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class RatesCouponSettlementFailObservation:
    source_id: str
    cusip: str
    tenor_bucket: str
    market_slug: str
    fail_rate_bps: Decimal
    settlement_age_days: Decimal
    repo_specialness_bps: Decimal
    auction_cycle_proximity_days: Decimal
    deliverable_supply_score: Decimal
    source_freshness_minutes: Decimal
    source_quorum: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesCouponSettlementFailObservation, "observation")
        _require_canonical_string("source_id", self.source_id)
        _require_cusip("cusip", self.cusip)
        for field_name in ("tenor_bucket", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "fail_rate_bps",
            "settlement_age_days",
            "repo_specialness_bps",
            "auction_cycle_proximity_days",
            "source_freshness_minutes",
            "source_quorum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "deliverable_supply_score",
            _require_ratio("deliverable_supply_score", self.deliverable_supply_score),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class RatesCouponSettlementFailDigestRow:
    source_id: str
    cusip: str
    tenor_bucket: str
    market_slug: str
    fail_rate_bps: Decimal
    settlement_age_days: Decimal
    repo_specialness_bps: Decimal
    auction_cycle_proximity_days: Decimal
    deliverable_supply_score: Decimal
    source_freshness_minutes: Decimal
    source_quorum: Decimal
    data_timestamp: datetime
    settlement_fail_status: str
    risk_score: Decimal
    reason_codes: tuple[str, ...]
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesCouponSettlementFailDigestRow, "row")
        _require_canonical_string("source_id", self.source_id)
        _require_cusip("cusip", self.cusip)
        for field_name in ("tenor_bucket", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "fail_rate_bps",
            "settlement_age_days",
            "repo_specialness_bps",
            "auction_cycle_proximity_days",
            "source_freshness_minutes",
            "source_quorum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "deliverable_supply_score",
            _require_ratio("deliverable_supply_score", self.deliverable_supply_score),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member(
            "settlement_fail_status",
            self.settlement_fail_status,
            SETTLEMENT_FAIL_STATUSES,
        )
        object.__setattr__(
            self,
            "risk_score",
            _require_ratio("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class RatesCouponSettlementFailReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RatesCouponSettlementFailReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class RatesCouponSettlementFailDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    high_fail_rate_count: Decimal
    aged_fail_count: Decimal
    repo_specialness_count: Decimal
    auction_cycle_pressure_count: Decimal
    thin_deliverable_supply_count: Decimal
    stale_source_count: Decimal
    low_source_quorum_count: Decimal
    max_fail_rate_bps: Decimal
    max_settlement_age_days: Decimal
    max_repo_specialness_bps: Decimal
    average_fail_rate_bps: Decimal
    settlement_fail_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesCouponSettlementFailDigestRow, ...]
    reason_code_counts: tuple[RatesCouponSettlementFailReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesCouponSettlementFailDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RATES_COUPON_SETTLEMENT_FAIL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "high_fail_rate_count",
            "aged_fail_count",
            "repo_specialness_count",
            "auction_cycle_pressure_count",
            "thin_deliverable_supply_count",
            "stale_source_count",
            "low_source_quorum_count",
            "max_fail_rate_bps",
            "max_settlement_age_days",
            "max_repo_specialness_bps",
            "average_fail_rate_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_fail_risk_score",
            _require_ratio("settlement_fail_risk_score", self.settlement_fail_risk_score),
        )
        _require_member("digest_status", self.digest_status, SETTLEMENT_FAIL_STATUSES)
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_rates_coupon_settlement_fail_digest(
    observations: Iterable[RatesCouponSettlementFailObservation],
    *,
    config: RatesCouponSettlementFailDigestConfig,
    generated_at: datetime,
) -> RatesCouponSettlementFailDigestReport:
    if type(config) is not RatesCouponSettlementFailDigestConfig:
        raise ValueError(
            "config must be exactly RatesCouponSettlementFailDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return RatesCouponSettlementFailDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        high_fail_rate_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_high_fail_rate",
        ),
        aged_fail_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_aged_fail",
        ),
        repo_specialness_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_repo_specialness",
        ),
        auction_cycle_pressure_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_auction_cycle_pressure",
        ),
        thin_deliverable_supply_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_thin_deliverable_supply",
        ),
        stale_source_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_stale_source",
        ),
        low_source_quorum_count=_reason_count(
            rows,
            "rates_coupon_settlement_fail_low_source_quorum",
        ),
        max_fail_rate_bps=_max_row_decimal(rows, "fail_rate_bps"),
        max_settlement_age_days=_max_row_decimal(rows, "settlement_age_days"),
        max_repo_specialness_bps=_max_row_decimal(rows, "repo_specialness_bps"),
        average_fail_rate_bps=_ratio(
            _sum_decimal(row.fail_rate_bps for row in rows),
            row_count,
        ),
        settlement_fail_risk_score=_ratio(
            _sum_decimal(row.risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_rates_coupon_settlement_fail_digest_payload(
    report: RatesCouponSettlementFailDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesCouponSettlementFailDigestReport:
        raise ValueError(
            "report must be exactly RatesCouponSettlementFailDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    observation: RatesCouponSettlementFailObservation,
    *,
    config: RatesCouponSettlementFailDigestConfig,
) -> RatesCouponSettlementFailDigestRow:
    reason_codes = _row_reason_codes(observation, config=config)
    status = _settlement_fail_status(observation, config=config, reason_codes=reason_codes)
    return RatesCouponSettlementFailDigestRow(
        source_id=observation.source_id,
        cusip=observation.cusip,
        tenor_bucket=observation.tenor_bucket,
        market_slug=observation.market_slug,
        fail_rate_bps=observation.fail_rate_bps,
        settlement_age_days=observation.settlement_age_days,
        repo_specialness_bps=observation.repo_specialness_bps,
        auction_cycle_proximity_days=observation.auction_cycle_proximity_days,
        deliverable_supply_score=observation.deliverable_supply_score,
        source_freshness_minutes=observation.source_freshness_minutes,
        source_quorum=observation.source_quorum,
        data_timestamp=observation.data_timestamp,
        settlement_fail_status=status,
        risk_score=STATUS_RISK_SCORE[status],
        reason_codes=reason_codes,
        upstream_reason_codes=observation.upstream_reason_codes,
    )


def _row_reason_codes(
    observation: RatesCouponSettlementFailObservation,
    *,
    config: RatesCouponSettlementFailDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.fail_rate_bps >= config.blocked_fail_rate_bps:
        reason_codes.append("rates_coupon_settlement_fail_high_fail_rate")
    elif observation.fail_rate_bps >= config.watch_fail_rate_bps:
        reason_codes.append("rates_coupon_settlement_fail_watch_fail_rate")

    if observation.settlement_age_days >= config.blocked_settlement_age_days:
        reason_codes.append("rates_coupon_settlement_fail_aged_fail")
    elif observation.settlement_age_days >= config.watch_settlement_age_days:
        reason_codes.append("rates_coupon_settlement_fail_watch_age")

    if observation.repo_specialness_bps >= config.watch_repo_specialness_bps:
        reason_codes.append("rates_coupon_settlement_fail_repo_specialness")
    if observation.auction_cycle_proximity_days <= config.auction_cycle_window_days:
        reason_codes.append("rates_coupon_settlement_fail_auction_cycle_pressure")
    if observation.deliverable_supply_score <= config.thin_deliverable_supply_score:
        reason_codes.append("rates_coupon_settlement_fail_thin_deliverable_supply")
    if observation.source_freshness_minutes >= config.stale_source_minutes:
        reason_codes.append("rates_coupon_settlement_fail_stale_source")
    if observation.source_quorum < config.min_source_quorum:
        reason_codes.append("rates_coupon_settlement_fail_low_source_quorum")
    if not reason_codes:
        reason_codes.append("rates_coupon_settlement_fail_inline")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _settlement_fail_status(
    observation: RatesCouponSettlementFailObservation,
    *,
    config: RatesCouponSettlementFailDigestConfig,
    reason_codes: tuple[str, ...],
) -> str:
    if (
        "rates_coupon_settlement_fail_high_fail_rate" in reason_codes
        or "rates_coupon_settlement_fail_aged_fail" in reason_codes
        or observation.repo_specialness_bps >= config.blocked_repo_specialness_bps
    ):
        return "blocked"
    if "rates_coupon_settlement_fail_inline" in reason_codes:
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[RatesCouponSettlementFailDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("rates_coupon_settlement_fail_digest_empty",)
    reason_codes: list[str] = []
    if _reason_count(rows, "rates_coupon_settlement_fail_aged_fail") > ZERO:
        reason_codes.append("rates_coupon_settlement_fail_aged_fail_present")
    if _reason_count(rows, "rates_coupon_settlement_fail_auction_cycle_pressure") > ZERO:
        reason_codes.append(
            "rates_coupon_settlement_fail_auction_cycle_pressure_present",
        )
    if _reason_count(rows, "rates_coupon_settlement_fail_high_fail_rate") > ZERO:
        reason_codes.append("rates_coupon_settlement_fail_high_fail_rate_present")
    if _reason_count(rows, "rates_coupon_settlement_fail_low_source_quorum") > ZERO:
        reason_codes.append("rates_coupon_settlement_fail_low_source_quorum_present")
    if _reason_count(rows, "rates_coupon_settlement_fail_repo_specialness") > ZERO:
        reason_codes.append("rates_coupon_settlement_fail_repo_specialness_present")
    if _reason_count(rows, "rates_coupon_settlement_fail_stale_source") > ZERO:
        reason_codes.append("rates_coupon_settlement_fail_stale_source_present")
    if _reason_count(rows, "rates_coupon_settlement_fail_thin_deliverable_supply") > ZERO:
        reason_codes.append(
            "rates_coupon_settlement_fail_thin_deliverable_supply_present",
        )
    if not reason_codes:
        reason_codes.append("rates_coupon_settlement_fail_digest_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesCouponSettlementFailDigestRow, ...],
) -> tuple[RatesCouponSettlementFailReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("rates_coupon_settlement_fail_digest_empty",):
        return (
            RatesCouponSettlementFailReasonCodeCount(
                reason_code="rates_coupon_settlement_fail_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RatesCouponSettlementFailReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[RatesCouponSettlementFailDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "rates_coupon_settlement_fail_aged_fail_present": (
            "rates_coupon_settlement_fail_aged_fail"
        ),
        "rates_coupon_settlement_fail_auction_cycle_pressure_present": (
            "rates_coupon_settlement_fail_auction_cycle_pressure"
        ),
        "rates_coupon_settlement_fail_digest_clear": (
            "rates_coupon_settlement_fail_inline"
        ),
        "rates_coupon_settlement_fail_high_fail_rate_present": (
            "rates_coupon_settlement_fail_high_fail_rate"
        ),
        "rates_coupon_settlement_fail_low_source_quorum_present": (
            "rates_coupon_settlement_fail_low_source_quorum"
        ),
        "rates_coupon_settlement_fail_repo_specialness_present": (
            "rates_coupon_settlement_fail_repo_specialness"
        ),
        "rates_coupon_settlement_fail_stale_source_present": (
            "rates_coupon_settlement_fail_stale_source"
        ),
        "rates_coupon_settlement_fail_thin_deliverable_supply_present": (
            "rates_coupon_settlement_fail_thin_deliverable_supply"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[RatesCouponSettlementFailDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.settlement_fail_status == "blocked" for row in rows):
        return "blocked"
    if any(row.settlement_fail_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_rates_coupon_settlement_fail_screening"
    if status == "watch":
        return "monitor_report_only_rates_coupon_settlement_fail_screening"
    return "block_report_only_rates_coupon_settlement_fail_screening"


def _validate_row(row: RatesCouponSettlementFailDigestRow) -> None:
    if row.risk_score != STATUS_RISK_SCORE[row.settlement_fail_status]:
        raise ValueError("risk_score must match settlement_fail_status")
    if row.settlement_fail_status == "pass":
        if row.reason_codes != ("rates_coupon_settlement_fail_inline",):
            raise ValueError("reason_codes must match settlement_fail_status")
        return
    if "rates_coupon_settlement_fail_inline" in row.reason_codes:
        raise ValueError("reason_codes must match settlement_fail_status")
    hard_blocked_reason_present = (
        "rates_coupon_settlement_fail_high_fail_rate" in row.reason_codes
        or "rates_coupon_settlement_fail_aged_fail" in row.reason_codes
    )
    repo_reason_present = (
        "rates_coupon_settlement_fail_repo_specialness" in row.reason_codes
    )
    if (
        row.settlement_fail_status == "blocked"
        and not hard_blocked_reason_present
        and not repo_reason_present
    ):
        raise ValueError("reason_codes must match settlement_fail_status")
    if row.settlement_fail_status == "watch" and hard_blocked_reason_present:
        raise ValueError("reason_codes must match settlement_fail_status")


def _validate_report(report: RatesCouponSettlementFailDigestReport) -> None:
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
    if report.high_fail_rate_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_high_fail_rate",
    ):
        raise ValueError("high_fail_rate_count must match rows")
    if report.aged_fail_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_aged_fail",
    ):
        raise ValueError("aged_fail_count must match rows")
    if report.repo_specialness_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_repo_specialness",
    ):
        raise ValueError("repo_specialness_count must match rows")
    if report.auction_cycle_pressure_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_auction_cycle_pressure",
    ):
        raise ValueError("auction_cycle_pressure_count must match rows")
    if report.thin_deliverable_supply_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_thin_deliverable_supply",
    ):
        raise ValueError("thin_deliverable_supply_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_stale_source",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.low_source_quorum_count != _reason_count(
        report.rows,
        "rates_coupon_settlement_fail_low_source_quorum",
    ):
        raise ValueError("low_source_quorum_count must match rows")
    if report.max_fail_rate_bps != _max_row_decimal(report.rows, "fail_rate_bps"):
        raise ValueError("max_fail_rate_bps must match rows")
    if report.max_settlement_age_days != _max_row_decimal(
        report.rows,
        "settlement_age_days",
    ):
        raise ValueError("max_settlement_age_days must match rows")
    if report.max_repo_specialness_bps != _max_row_decimal(
        report.rows,
        "repo_specialness_bps",
    ):
        raise ValueError("max_repo_specialness_bps must match rows")
    if report.average_fail_rate_bps != _ratio(
        _sum_decimal(row.fail_rate_bps for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_fail_rate_bps must match rows")
    if report.settlement_fail_risk_score != _ratio(
        _sum_decimal(row.risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("settlement_fail_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[RatesCouponSettlementFailObservation],
) -> tuple[RatesCouponSettlementFailObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain RatesCouponSettlementFailObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not RatesCouponSettlementFailObservation:
            raise ValueError(
                "observations must contain RatesCouponSettlementFailObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[RatesCouponSettlementFailDigestRow],
) -> tuple[RatesCouponSettlementFailDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain RatesCouponSettlementFailDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not RatesCouponSettlementFailDigestRow:
            raise ValueError("rows must contain RatesCouponSettlementFailDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[RatesCouponSettlementFailReasonCodeCount],
) -> tuple[RatesCouponSettlementFailReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not RatesCouponSettlementFailReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain RatesCouponSettlementFailReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


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
    return tuple(sorted(normalized))


def _row_sort_key(
    row: RatesCouponSettlementFailDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.settlement_fail_status],
        -row.risk_score,
        -row.fail_rate_bps,
        -row.settlement_age_days,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[RatesCouponSettlementFailDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.settlement_fail_status == status),
    )


def _reason_count(
    rows: tuple[RatesCouponSettlementFailDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[RatesCouponSettlementFailDigestRow, ...],
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


def _require_cusip(field_name: str, value: object) -> None:
    if type(value) is not str or _CUSIP_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a 9-character CUSIP")


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
