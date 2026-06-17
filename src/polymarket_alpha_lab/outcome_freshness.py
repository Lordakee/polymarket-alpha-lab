"""Paper-only freshness summaries over outcome-tracking reports.

Pure reducer over already-built ``OutcomeTrackingReport`` values. This module is
local/report-only: it does not read files, fetch markets, construct clients,
authenticate, touch wallets, place orders, rank markets, recommend trades, or
provide financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport


__all__ = (
    "OutcomeFreshnessConfig",
    "OutcomeFreshnessStatusRow",
    "OutcomeFreshnessReport",
    "build_outcome_freshness_report",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

OUTCOME_FRESHNESS_STATUSES = (
    "empty_outcome_history",
    "latest_outcomes_fresh",
    "latest_outcomes_pending",
    "latest_outcomes_stale",
)


@dataclass(frozen=True)
class OutcomeFreshnessConfig:
    config_version: str
    stale_after_seconds: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("stale_after_seconds", self.stale_after_seconds)


@dataclass(frozen=True)
class OutcomeFreshnessStatusRow:
    status: str
    outcome_report_count: int
    outcome_report_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.status not in OUTCOME_FRESHNESS_STATUSES:
            raise ValueError("status must be a known outcome freshness status")
        _require_nonnegative_int("outcome_report_count", self.outcome_report_count)
        _require_optional_probability_decimal(
            "outcome_report_ratio",
            self.outcome_report_ratio,
        )


@dataclass(frozen=True)
class OutcomeFreshnessReport:
    generated_at: datetime
    config_version: str
    outcome_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_total_markets_checked: int
    latest_resolved_count: int
    latest_pending_count: int
    latest_resolved_ratio: Decimal | None
    latest_pending_ratio: Decimal | None
    latest_report_age_seconds: int | None
    consecutive_pending_count: int
    status: str
    status_rows: tuple[OutcomeFreshnessStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(self.first_report_generated_at),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(self.latest_report_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "outcome_report_count",
            "latest_total_markets_checked",
            "latest_resolved_count",
            "latest_pending_count",
            "consecutive_pending_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.latest_report_age_seconds is not None:
            _require_nonnegative_int(
                "latest_report_age_seconds",
                self.latest_report_age_seconds,
            )
        _require_optional_probability_decimal(
            "latest_resolved_ratio",
            self.latest_resolved_ratio,
        )
        _require_optional_probability_decimal(
            "latest_pending_ratio",
            self.latest_pending_ratio,
        )
        if self.status not in OUTCOME_FRESHNESS_STATUSES:
            raise ValueError("status must be a known outcome freshness status")
        object.__setattr__(self, "status_rows", _normalize_status_rows(self.status_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")

    @property
    def report_count(self) -> int:
        return self.outcome_report_count

    @property
    def days_since_latest_report(self) -> int | None:
        if self.latest_report_age_seconds is None:
            return None
        return self.latest_report_age_seconds // 86_400


def build_outcome_freshness_report(
    reports: list[OutcomeTrackingReport] | tuple[OutcomeTrackingReport, ...],
    *,
    config: OutcomeFreshnessConfig,
    generated_at: datetime,
) -> OutcomeFreshnessReport:
    if type(config) is not OutcomeFreshnessConfig:
        raise ValueError("config must be an OutcomeFreshnessConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    report_items = _normalize_outcome_reports(reports)
    generated_at_utc = _as_utc(generated_at)
    latest = report_items[-1] if report_items else None
    latest_age_seconds = (
        _age_seconds(
            generated_at_utc=generated_at_utc,
            report_generated_at=latest.generated_at,
            field_name="latest_report_age_seconds",
        )
        if latest is not None
        else None
    )
    status_counts = _status_counts(
        report_items,
        generated_at_utc=generated_at_utc,
        stale_after_seconds=config.stale_after_seconds,
    )

    return OutcomeFreshnessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        outcome_report_count=len(report_items),
        first_report_generated_at=(
            _as_utc(report_items[0].generated_at) if report_items else None
        ),
        latest_report_generated_at=(
            _as_utc(latest.generated_at) if latest is not None else None
        ),
        latest_total_markets_checked=(
            latest.total_markets_checked if latest is not None else 0
        ),
        latest_resolved_count=latest.resolved_count if latest is not None else 0,
        latest_pending_count=latest.pending_count if latest is not None else 0,
        latest_resolved_ratio=(
            _ratio(latest.resolved_count, latest.total_markets_checked)
            if latest is not None
            else None
        ),
        latest_pending_ratio=(
            _ratio(latest.pending_count, latest.total_markets_checked)
            if latest is not None
            else None
        ),
        latest_report_age_seconds=latest_age_seconds,
        consecutive_pending_count=_consecutive_pending_count(report_items),
        status=(
            _status_for_report(
                report=latest,
                age_seconds=latest_age_seconds,
                stale_after_seconds=config.stale_after_seconds,
            )
            if latest is not None
            else "empty_outcome_history"
        ),
        status_rows=_build_status_rows(status_counts, len(report_items)),
    )


def _normalize_outcome_reports(
    reports: list[OutcomeTrackingReport] | tuple[OutcomeTrackingReport, ...],
) -> tuple[OutcomeTrackingReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple of OutcomeTrackingReport values")
    items = tuple(reports)
    for report in items:
        if type(report) is not OutcomeTrackingReport:
            raise ValueError("reports must contain OutcomeTrackingReport values")
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only OutcomeTrackingReport values")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only OutcomeTrackingReport values")
    return items


def _status_counts(
    reports: tuple[OutcomeTrackingReport, ...],
    *,
    generated_at_utc: datetime,
    stale_after_seconds: int,
) -> dict[str, int]:
    counts = {status: 0 for status in OUTCOME_FRESHNESS_STATUSES}
    for report in reports:
        age_seconds = _age_seconds(
            generated_at_utc=generated_at_utc,
            report_generated_at=report.generated_at,
            field_name="report_age_seconds",
        )
        counts[
            _status_for_report(
                report=report,
                age_seconds=age_seconds,
                stale_after_seconds=stale_after_seconds,
            )
        ] += 1
    return counts


def _status_for_report(
    *,
    report: OutcomeTrackingReport | None,
    age_seconds: int | None,
    stale_after_seconds: int,
) -> str:
    if report is None:
        return "empty_outcome_history"
    if age_seconds is None:
        raise ValueError("report age seconds is required with outcome reports")
    if age_seconds > stale_after_seconds:
        return "latest_outcomes_stale"
    if report.pending_count > 0:
        return "latest_outcomes_pending"
    return "latest_outcomes_fresh"


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[OutcomeFreshnessStatusRow, ...]:
    return tuple(
        OutcomeFreshnessStatusRow(
            status=status,
            outcome_report_count=status_counts[status],
            outcome_report_ratio=_ratio(status_counts[status], total),
        )
        for status in OUTCOME_FRESHNESS_STATUSES
    )


def _consecutive_pending_count(
    reports: tuple[OutcomeTrackingReport, ...],
) -> int:
    count = 0
    for report in reversed(reports):
        if report.pending_count == 0:
            break
        count += 1
    return count


def _age_seconds(
    *,
    generated_at_utc: datetime,
    report_generated_at: datetime,
    field_name: str,
) -> int:
    delta_seconds = (
        generated_at_utc - _as_utc(report_generated_at)
    ).total_seconds()
    if delta_seconds < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return int(delta_seconds)


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_consistency(report: OutcomeFreshnessReport) -> None:
    if report.outcome_report_count == 0:
        if report.first_report_generated_at is not None:
            raise ValueError("first_report_generated_at must be absent without reports")
        if report.latest_report_generated_at is not None:
            raise ValueError("latest_report_generated_at must be absent without reports")
        if report.latest_report_age_seconds is not None:
            raise ValueError("latest_report_age_seconds must be absent without reports")
        if (
            report.latest_total_markets_checked != 0
            or report.latest_resolved_count != 0
            or report.latest_pending_count != 0
        ):
            raise ValueError("latest counts must be zero without reports")
        if report.latest_resolved_ratio is not None:
            raise ValueError("latest_resolved_ratio must be absent without reports")
        if report.latest_pending_ratio is not None:
            raise ValueError("latest_pending_ratio must be absent without reports")
        if report.consecutive_pending_count != 0:
            raise ValueError("consecutive_pending_count must be zero without reports")
        if report.status != "empty_outcome_history":
            raise ValueError("status must match outcome freshness observations")
    else:
        if report.first_report_generated_at is None:
            raise ValueError("first_report_generated_at is required with reports")
        if report.latest_report_generated_at is None:
            raise ValueError("latest_report_generated_at is required with reports")
        if report.latest_report_age_seconds is None:
            raise ValueError("latest_report_age_seconds is required with reports")
        if (
            report.latest_resolved_count + report.latest_pending_count
            != report.latest_total_markets_checked
        ):
            raise ValueError(
                "latest resolved and pending counts must sum to latest total",
            )
        if report.latest_resolved_ratio != _ratio(
            report.latest_resolved_count,
            report.latest_total_markets_checked,
        ):
            raise ValueError("latest_resolved_ratio must match latest counts")
        if report.latest_pending_ratio != _ratio(
            report.latest_pending_count,
            report.latest_total_markets_checked,
        ):
            raise ValueError("latest_pending_ratio must match latest counts")
        if report.consecutive_pending_count > report.outcome_report_count:
            raise ValueError(
                "consecutive_pending_count must not exceed outcome_report_count",
            )
        if report.latest_pending_count > 0:
            if report.status == "latest_outcomes_fresh":
                raise ValueError("status must match latest outcome counts")
        elif report.status == "latest_outcomes_pending":
            raise ValueError("status must match latest outcome counts")
        if report.status == "empty_outcome_history":
            raise ValueError("status must match outcome freshness observations")

    status_row_keys = tuple(row.status for row in report.status_rows)
    if status_row_keys != OUTCOME_FRESHNESS_STATUSES:
        raise ValueError("status_rows must cover outcome freshness statuses")
    if (
        sum(row.outcome_report_count for row in report.status_rows)
        != report.outcome_report_count
    ):
        raise ValueError("status_rows counts must sum to outcome_report_count")
    for row in report.status_rows:
        if row.outcome_report_ratio != _ratio(
            row.outcome_report_count,
            report.outcome_report_count,
        ):
            raise ValueError("status_rows ratios must match outcome report counts")


def _normalize_status_rows(
    rows: tuple[OutcomeFreshnessStatusRow, ...],
) -> tuple[OutcomeFreshnessStatusRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("status_rows must be a tuple")
    normalized: list[OutcomeFreshnessStatusRow] = []
    for row in rows:
        if type(row) is not OutcomeFreshnessStatusRow:
            raise ValueError(
                "status_rows must contain OutcomeFreshnessStatusRow values",
            )
        normalized.append(
            OutcomeFreshnessStatusRow(
                status=row.status,
                outcome_report_count=row.outcome_report_count,
                outcome_report_ratio=row.outcome_report_ratio,
            ),
        )
    return tuple(normalized)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")


@dataclass(frozen=True)
class PaperOutcomeFreshnessConfig:
    config_version: str
    stale_after_days: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("stale_after_days", self.stale_after_days)


PaperOutcomeFreshnessReport = OutcomeFreshnessReport


def build_paper_outcome_freshness_report(
    reports: list[OutcomeTrackingReport] | tuple[OutcomeTrackingReport, ...],
    *,
    config: PaperOutcomeFreshnessConfig,
    generated_at: datetime,
) -> OutcomeFreshnessReport:
    if type(config) is not PaperOutcomeFreshnessConfig:
        raise ValueError("config must be a PaperOutcomeFreshnessConfig")
    return build_outcome_freshness_report(
        reports,
        config=OutcomeFreshnessConfig(
            config_version=config.config_version,
            stale_after_seconds=config.stale_after_days * 86_400,
        ),
        generated_at=generated_at,
    )
