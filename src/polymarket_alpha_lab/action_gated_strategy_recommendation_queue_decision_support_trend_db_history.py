"""Read-only history aggregation for persisted decision-support trend rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_row import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
)


RISK_STATUSES = ("pass", "watch", "blocked")
DECIMAL_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport:
    generated_at: datetime
    config_version: str
    trend_count: int
    total_source_snapshot_count: int
    first_trend_generated_at: datetime | None
    latest_trend_generated_at: datetime | None
    latest_risk_status: str | None
    risk_status_counts: tuple[tuple[str, int], ...]
    duplicate_generated_at_count: int
    consecutive_latest_pass_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    ready_notional_delta: Decimal | None
    top_priority_score_delta: Decimal | None
    average_priority_score_delta: Decimal | None
    source_queue_count_delta: int | None
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "trend_count",
            "total_source_snapshot_count",
            "duplicate_generated_at_count",
            "consecutive_latest_pass_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_trend_generated_at",
            _as_optional_utc(
                "first_trend_generated_at",
                self.first_trend_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_trend_generated_at",
            _as_optional_utc(
                "latest_trend_generated_at",
                self.latest_trend_generated_at,
            ),
        )
        if self.latest_risk_status is not None:
            _require_risk_status("latest_risk_status", self.latest_risk_status)
        object.__setattr__(
            self,
            "risk_status_counts",
            _normalize_risk_status_counts(self.risk_status_counts),
        )
        for field_name in (
            "ready_notional_delta",
            "top_priority_score_delta",
            "average_priority_score_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_optional_decimal(field_name, getattr(self, field_name)),
            )
        if self.source_queue_count_delta is not None:
            _require_int("source_queue_count_delta", self.source_queue_count_delta)
        object.__setattr__(
            self,
            "latest_reason_code_counts",
            _normalize_reason_code_counts(
                "latest_reason_code_counts",
                self.latest_reason_code_counts,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report(
    db_rows: object,
    *,
    config: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport:
    if (
        type(config)
        is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig
    ):
        raise ValueError(
            "config must be a "
            "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    rows = _normalize_db_rows(db_rows)
    chronological_rows = tuple(
        sorted(
            rows,
            key=lambda item: (
                item.trend_row.generated_at,
                item.trend_row.trend_sha256,
            ),
        ),
    )
    latest = chronological_rows[-1].trend_row if chronological_rows else None

    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        trend_count=len(chronological_rows),
        total_source_snapshot_count=sum(
            row.trend_row.source_snapshot_count for row in chronological_rows
        ),
        first_trend_generated_at=(
            chronological_rows[0].trend_row.generated_at
            if chronological_rows
            else None
        ),
        latest_trend_generated_at=latest.generated_at if latest is not None else None,
        latest_risk_status=latest.latest_risk_status if latest is not None else None,
        risk_status_counts=_risk_status_counts(chronological_rows),
        duplicate_generated_at_count=_duplicate_generated_at_count(
            chronological_rows,
        ),
        consecutive_latest_pass_count=_latest_status_streak(
            chronological_rows,
            "pass",
        ),
        consecutive_latest_watch_count=_latest_status_streak(
            chronological_rows,
            "watch",
        ),
        consecutive_latest_blocked_count=_latest_status_streak(
            chronological_rows,
            "blocked",
        ),
        ready_notional_delta=(
            latest.ready_notional_delta if latest is not None else None
        ),
        top_priority_score_delta=(
            latest.top_priority_score_delta if latest is not None else None
        ),
        average_priority_score_delta=(
            latest.average_priority_score_delta if latest is not None else None
        ),
        source_queue_count_delta=(
            latest.source_queue_count_delta if latest is not None else None
        ),
        latest_reason_code_counts=(
            tuple(sorted(latest.latest_reason_code_counts_json.items()))
            if latest is not None
            else ()
        ),
    )


def _normalize_db_rows(
    value: object,
) -> tuple[
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
    ...,
]:
    if type(value) not in (list, tuple):
        raise ValueError("db_rows must be a list or tuple")
    rows = tuple(value)
    normalized = []
    for row in rows:
        if (
            type(row)
            is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows
        ):
            raise ValueError("db_rows must contain TrendDbRows values")
        _require_hard_flags(row.trend_row)
        for source_row in row.source_rows:
            _require_hard_flags(source_row)
        normalized.append(row)
    return tuple(normalized)


def _risk_status_counts(
    rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
        ...,
    ],
) -> tuple[tuple[str, int], ...]:
    counts = {status: 0 for status in RISK_STATUSES}
    for row in rows:
        status = row.trend_row.latest_risk_status
        if status in counts:
            counts[status] += 1
    return tuple((status, counts[status]) for status in RISK_STATUSES)


def _duplicate_generated_at_count(
    rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
        ...,
    ],
) -> int:
    counts: dict[datetime, int] = {}
    for row in rows:
        generated_at = row.trend_row.generated_at
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _latest_status_streak(
    rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
        ...,
    ],
    status: str,
) -> int:
    count = 0
    for row in reversed(rows):
        if row.trend_row.latest_risk_status != status:
            break
        count += 1
    return count


def _normalize_risk_status_counts(
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("risk_status_counts must be a tuple")
    rows = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("risk_status_counts must contain status/count pairs")
        status, count = item
        _require_risk_status("risk_status", status)
        _require_nonnegative_int("risk_status_count", count)
        rows.append((status, count))
    if tuple(status for status, _ in rows) != RISK_STATUSES:
        raise ValueError("risk_status_counts must cover risk statuses")
    return tuple(rows)


def _normalize_reason_code_counts(
    field_name: str,
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(f"{field_name} must contain reason/count pairs")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        _require_nonnegative_int("reason_code_count", count)
        normalized.append((reason_code, count))
    if tuple(sorted(normalized)) != tuple(normalized):
        raise ValueError(f"{field_name} must be sorted")
    return tuple(normalized)


def _validate_report_consistency(
    report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport,
) -> None:
    if report.trend_count == 0:
        if report.total_source_snapshot_count != 0:
            raise ValueError("total_source_snapshot_count must be zero without trends")
        if report.first_trend_generated_at is not None:
            raise ValueError("first_trend_generated_at must be absent without trends")
        if report.latest_trend_generated_at is not None:
            raise ValueError("latest_trend_generated_at must be absent without trends")
        if report.latest_risk_status is not None:
            raise ValueError("latest_risk_status must be absent without trends")
        if report.consecutive_latest_pass_count != 0:
            raise ValueError(
                "consecutive_latest_pass_count must be zero without trends",
            )
        if report.consecutive_latest_watch_count != 0:
            raise ValueError(
                "consecutive_latest_watch_count must be zero without trends",
            )
        if report.consecutive_latest_blocked_count != 0:
            raise ValueError(
                "consecutive_latest_blocked_count must be zero without trends",
            )
        if report.ready_notional_delta is not None:
            raise ValueError("ready_notional_delta must be absent without trends")
        if report.top_priority_score_delta is not None:
            raise ValueError("top_priority_score_delta must be absent without trends")
        if report.average_priority_score_delta is not None:
            raise ValueError("average_priority_score_delta must be absent without trends")
        if report.source_queue_count_delta is not None:
            raise ValueError("source_queue_count_delta must be absent without trends")
        if report.latest_reason_code_counts:
            raise ValueError("latest_reason_code_counts must be empty without trends")
    else:
        if report.total_source_snapshot_count < report.trend_count:
            raise ValueError("total_source_snapshot_count must cover trends")
        if report.first_trend_generated_at is None:
            raise ValueError("first_trend_generated_at is required with trends")
        if report.latest_trend_generated_at is None:
            raise ValueError("latest_trend_generated_at is required with trends")
        if report.latest_risk_status is None:
            raise ValueError("latest_risk_status is required with trends")
        if report.ready_notional_delta is None:
            raise ValueError("ready_notional_delta is required with trends")
        if report.top_priority_score_delta is None:
            raise ValueError("top_priority_score_delta is required with trends")
        if report.average_priority_score_delta is None:
            raise ValueError("average_priority_score_delta is required with trends")
        if report.source_queue_count_delta is None:
            raise ValueError("source_queue_count_delta is required with trends")
    if sum(count for _, count in report.risk_status_counts) > report.trend_count:
        raise ValueError("risk_status_counts must not exceed trend_count")
    _validate_latest_status_streaks(report)


def _validate_latest_status_streaks(
    report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport,
) -> None:
    risk_status_counts = dict(report.risk_status_counts)
    if report.trend_count == 0:
        return

    streaks = (
        ("pass", "consecutive_latest_pass_count", report.consecutive_latest_pass_count),
        (
            "watch",
            "consecutive_latest_watch_count",
            report.consecutive_latest_watch_count,
        ),
        (
            "blocked",
            "consecutive_latest_blocked_count",
            report.consecutive_latest_blocked_count,
        ),
    )
    for status, field_name, count in streaks:
        if report.latest_risk_status == status:
            if count <= 0:
                raise ValueError(
                    f"{field_name} must be positive when latest_risk_status is {status}",
                )
        elif count != 0:
            raise ValueError(
                f"{field_name} must be zero unless latest_risk_status is {status}",
            )
        if count > risk_status_counts[status]:
            raise ValueError(
                f"{field_name} must not exceed {status} risk_status_count",
            )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _quantize_optional_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.quantize(DECIMAL_QUANTUM):
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return value


def _require_risk_status(field_name: str, value: Any) -> None:
    if type(value) is not str or value not in RISK_STATUSES:
        raise ValueError(f"{field_name} must be a known risk status")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig",
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport",
    "build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report",
)
