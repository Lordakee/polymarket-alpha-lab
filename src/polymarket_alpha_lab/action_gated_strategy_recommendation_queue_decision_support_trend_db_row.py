"""Pure row codec for action-gated queue decision-support trend manifests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_db_row import (
    paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
    build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)


__all__ = (
    "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION",
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow",
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow",
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows",
    "paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows",
    "paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows",
)


ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION = (
    "action-gated-queue-decision-support-trend-v1"
)
DECIMAL_QUANTUM = Decimal("0.000001")
RISK_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow:
    trend_sha256: str
    trend_schema_version: str
    source_window_sha256: str
    generated_at: datetime
    source_snapshot_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_risk_status: str | None
    risk_pass_count: int
    risk_watch_count: int
    risk_blocked_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    duplicate_generated_at_count: int
    ready_notional_first: Decimal | None
    ready_notional_latest: Decimal | None
    ready_notional_delta: Decimal | None
    top_priority_score_first: Decimal | None
    top_priority_score_latest: Decimal | None
    top_priority_score_delta: Decimal | None
    average_priority_score_first: Decimal | None
    average_priority_score_latest: Decimal | None
    average_priority_score_delta: Decimal | None
    source_queue_count_first: int | None
    source_queue_count_latest: int | None
    source_queue_count_delta: int | None
    latest_reason_code_counts_json: dict[str, int]
    total_reason_code_counts_json: dict[str, int]
    repeated_reason_code_counts_json: dict[str, int]
    reason_code_rows_json: list[dict[str, object]]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("trend_sha256", self.trend_sha256)
        if self.trend_schema_version != ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION:
            raise ValueError("trend_schema_version must match current schema version")
        _require_sha256("source_window_sha256", self.source_window_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc("first_generated_at", self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )

        for field_name in (
            "source_snapshot_count",
            "risk_pass_count",
            "risk_watch_count",
            "risk_blocked_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
            "duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.latest_risk_status is not None:
            _require_risk_status("latest_risk_status", self.latest_risk_status)

        for field_name in (
            "ready_notional_first",
            "ready_notional_latest",
            "ready_notional_delta",
            "top_priority_score_first",
            "top_priority_score_latest",
            "top_priority_score_delta",
            "average_priority_score_first",
            "average_priority_score_latest",
            "average_priority_score_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_optional_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ready_notional_first",
            "ready_notional_latest",
            "top_priority_score_first",
            "top_priority_score_latest",
            "average_priority_score_first",
            "average_priority_score_latest",
        ):
            value = getattr(self, field_name)
            if value is not None and value < Decimal("0"):
                raise ValueError(f"{field_name} must be nonnegative")
        for field_name in (
            "source_queue_count_first",
            "source_queue_count_latest",
            "source_queue_count_delta",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_int(field_name, value)

        for field_name in (
            "latest_reason_code_counts_json",
            "total_reason_code_counts_json",
            "repeated_reason_code_counts_json",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_json_object(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_rows_json",
            _normalize_reason_code_rows_json(
                "reason_code_rows_json",
                self.reason_code_rows_json,
            ),
        )

        _validate_hard_flags("trend row", self)
        _validate_trend_row_shape(self)
        _validate_reason_count_maps(self)
        expected_trend_sha256 = _trend_sha256(self)
        if self.trend_sha256 != expected_trend_sha256:
            raise ValueError(
                "trend_sha256 must match source_window_sha256 and scalar summary fields",
            )


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow:
    trend_sha256: str
    trend_ordinal: int
    source_input_position: int
    snapshot_sha256: str
    source_generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("trend_sha256", self.trend_sha256)
        _require_positive_int("trend_ordinal", self.trend_ordinal)
        _require_positive_int("source_input_position", self.source_input_position)
        _require_sha256("snapshot_sha256", self.snapshot_sha256)
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _validate_hard_flags("trend source row", self)


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows:
    trend_row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow
    source_rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
        ...
    ]

    def __post_init__(self) -> None:
        if type(self.trend_row) is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow:
            raise ValueError("trend_row must be a TrendDbRow")
        if type(self.source_rows) is not tuple:
            raise ValueError("source_rows must be a tuple")
        for source_row in self.source_rows:
            if (
                type(source_row)
                is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow
            ):
                raise ValueError("source_rows must contain TrendSourceDbRow values")

        ordinals = tuple(source_row.trend_ordinal for source_row in self.source_rows)
        expected_ordinals = tuple(range(1, len(self.source_rows) + 1))
        if ordinals != expected_ordinals:
            raise ValueError(
                "trend_ordinal values must be sorted, unique, and contiguous",
            )
        input_positions = tuple(
            source_row.source_input_position for source_row in self.source_rows
        )
        if tuple(sorted(input_positions)) != expected_ordinals:
            raise ValueError("source_input_position values must be unique and contiguous")
        for source_row in self.source_rows:
            if source_row.trend_sha256 != self.trend_row.trend_sha256:
                raise ValueError("source_rows trend_sha256 must match trend_row")
        if self.trend_row.source_snapshot_count != len(self.source_rows):
            raise ValueError("source_snapshot_count must match source_rows")

        expected_source_window_sha256 = _source_window_sha256(self.source_rows)
        if self.trend_row.source_window_sha256 != expected_source_window_sha256:
            raise ValueError("source_window_sha256 must match source_rows")
        _validate_source_generated_at_bounds(self.trend_row, self.source_rows)


def paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
    trend_report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
    snapshot_pairs: object,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows:
    if (
        type(trend_report)
        is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport
    ):
        raise ValueError(
            "trend_report must be a "
            "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport",
        )
    _validate_hard_flags("trend_report", trend_report)
    pairs = _normalize_snapshot_pairs(snapshot_pairs)
    expected_trend_report = (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            pairs,
            generated_at=trend_report.generated_at,
        )
    )
    if trend_report != expected_trend_report:
        raise ValueError("trend_report must match snapshot_pairs")

    snapshot_rows_by_input_position = {
        input_position: paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )
        for input_position, (priority_report, risk_report) in enumerate(pairs, start=1)
    }
    source_rows_without_trend_hash = []
    for trend_ordinal, summary in enumerate(trend_report.source_summaries, start=1):
        snapshot_row = snapshot_rows_by_input_position[summary.input_position]
        if snapshot_row.generated_at != summary.generated_at:
            raise ValueError("source snapshot generated_at must match trend summary")
        source_rows_without_trend_hash.append(
            {
                "trend_ordinal": trend_ordinal,
                "source_input_position": summary.input_position,
                "snapshot_sha256": snapshot_row.snapshot_sha256,
                "source_generated_at": snapshot_row.generated_at,
            },
        )

    placeholder_source_rows = tuple(
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
            trend_sha256="0" * 64,
            **source_row,
        )
        for source_row in source_rows_without_trend_hash
    )
    source_window_sha256 = _source_window_sha256(placeholder_source_rows)
    risk_counts = dict(trend_report.risk_status_counts)
    trend_row_values = {
        "trend_schema_version": ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION,
        "source_window_sha256": source_window_sha256,
        "generated_at": trend_report.generated_at,
        "source_snapshot_count": trend_report.source_snapshot_count,
        "first_generated_at": trend_report.first_generated_at,
        "latest_generated_at": trend_report.latest_generated_at,
        "latest_risk_status": trend_report.latest_risk_status,
        "risk_pass_count": risk_counts.get("pass", 0),
        "risk_watch_count": risk_counts.get("watch", 0),
        "risk_blocked_count": risk_counts.get("blocked", 0),
        "consecutive_latest_watch_count": trend_report.consecutive_latest_watch_count,
        "consecutive_latest_blocked_count": (
            trend_report.consecutive_latest_blocked_count
        ),
        "duplicate_generated_at_count": trend_report.duplicate_generated_at_count,
        "ready_notional_first": trend_report.ready_notional_first,
        "ready_notional_latest": trend_report.ready_notional_latest,
        "ready_notional_delta": trend_report.ready_notional_delta,
        "top_priority_score_first": trend_report.top_priority_score_first,
        "top_priority_score_latest": trend_report.top_priority_score_latest,
        "top_priority_score_delta": trend_report.top_priority_score_delta,
        "average_priority_score_first": trend_report.average_priority_score_first,
        "average_priority_score_latest": trend_report.average_priority_score_latest,
        "average_priority_score_delta": trend_report.average_priority_score_delta,
        "source_queue_count_first": trend_report.source_queue_count_first,
        "source_queue_count_latest": trend_report.source_queue_count_latest,
        "source_queue_count_delta": trend_report.source_queue_count_delta,
        "latest_reason_code_counts_json": _counts_json_from_pairs(
            "latest_reason_code_counts",
            trend_report.latest_reason_code_counts,
        ),
        "total_reason_code_counts_json": _counts_json_from_pairs(
            "total_reason_code_counts",
            trend_report.total_reason_code_counts,
        ),
        "repeated_reason_code_counts_json": _counts_json_from_pairs(
            "repeated_reason_code_counts",
            trend_report.repeated_reason_code_counts,
        ),
        "reason_code_rows_json": [
            {
                "reason_code": row.reason_code,
                "total_count": row.total_count,
                "latest_count": row.latest_count,
                "snapshot_count": row.snapshot_count,
            }
            for row in trend_report.reason_code_rows
        ],
    }
    trend_sha256 = _trend_sha256_from_values(trend_row_values)
    trend_row = PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow(
        trend_sha256=trend_sha256,
        **trend_row_values,
    )
    source_rows = tuple(
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
            trend_sha256=trend_row.trend_sha256,
            **source_row,
        )
        for source_row in source_rows_without_trend_hash
    )
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
        trend_row=trend_row,
        source_rows=source_rows,
    )


def paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
    db_rows: object,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows:
    if (
        type(db_rows)
        is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows
    ):
        raise ValueError("db_rows must be TrendDbRows")
    if (
        type(db_rows.trend_row)
        is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow
    ):
        raise ValueError("trend_row must be a TrendDbRow")
    source_rows = []
    for source_row in db_rows.source_rows:
        if (
            type(source_row)
            is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow
        ):
            raise ValueError("source_rows must contain TrendSourceDbRow values")
        source_rows.append(
            PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
                trend_sha256=source_row.trend_sha256,
                trend_ordinal=source_row.trend_ordinal,
                source_input_position=source_row.source_input_position,
                snapshot_sha256=source_row.snapshot_sha256,
                source_generated_at=source_row.source_generated_at,
                paper_only=source_row.paper_only,
                report_only=source_row.report_only,
                readonly=source_row.readonly,
            ),
        )
    trend_row = PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow(
        trend_sha256=db_rows.trend_row.trend_sha256,
        trend_schema_version=db_rows.trend_row.trend_schema_version,
        source_window_sha256=db_rows.trend_row.source_window_sha256,
        generated_at=db_rows.trend_row.generated_at,
        source_snapshot_count=db_rows.trend_row.source_snapshot_count,
        first_generated_at=db_rows.trend_row.first_generated_at,
        latest_generated_at=db_rows.trend_row.latest_generated_at,
        latest_risk_status=db_rows.trend_row.latest_risk_status,
        risk_pass_count=db_rows.trend_row.risk_pass_count,
        risk_watch_count=db_rows.trend_row.risk_watch_count,
        risk_blocked_count=db_rows.trend_row.risk_blocked_count,
        consecutive_latest_watch_count=db_rows.trend_row.consecutive_latest_watch_count,
        consecutive_latest_blocked_count=(
            db_rows.trend_row.consecutive_latest_blocked_count
        ),
        duplicate_generated_at_count=db_rows.trend_row.duplicate_generated_at_count,
        ready_notional_first=db_rows.trend_row.ready_notional_first,
        ready_notional_latest=db_rows.trend_row.ready_notional_latest,
        ready_notional_delta=db_rows.trend_row.ready_notional_delta,
        top_priority_score_first=db_rows.trend_row.top_priority_score_first,
        top_priority_score_latest=db_rows.trend_row.top_priority_score_latest,
        top_priority_score_delta=db_rows.trend_row.top_priority_score_delta,
        average_priority_score_first=db_rows.trend_row.average_priority_score_first,
        average_priority_score_latest=db_rows.trend_row.average_priority_score_latest,
        average_priority_score_delta=db_rows.trend_row.average_priority_score_delta,
        source_queue_count_first=db_rows.trend_row.source_queue_count_first,
        source_queue_count_latest=db_rows.trend_row.source_queue_count_latest,
        source_queue_count_delta=db_rows.trend_row.source_queue_count_delta,
        latest_reason_code_counts_json=db_rows.trend_row.latest_reason_code_counts_json,
        total_reason_code_counts_json=db_rows.trend_row.total_reason_code_counts_json,
        repeated_reason_code_counts_json=db_rows.trend_row.repeated_reason_code_counts_json,
        reason_code_rows_json=db_rows.trend_row.reason_code_rows_json,
        paper_only=db_rows.trend_row.paper_only,
        report_only=db_rows.trend_row.report_only,
        readonly=db_rows.trend_row.readonly,
    )
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
        trend_row=trend_row,
        source_rows=tuple(source_rows),
    )


def _normalize_snapshot_pairs(
    value: object,
) -> tuple[
    tuple[
        PaperActionGatedStrategyRecommendationQueuePriorityReport,
        PaperActionGatedStrategyRecommendationQueueRiskReport,
    ],
    ...,
]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshot_pairs must be a list or tuple")
    pairs = tuple(value)
    normalized = []
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("snapshot_pairs must contain priority/risk report pairs")
        priority_report, risk_report = pair
        if type(priority_report) is not PaperActionGatedStrategyRecommendationQueuePriorityReport:
            raise ValueError("snapshot_pairs must contain PriorityReport values")
        if type(risk_report) is not PaperActionGatedStrategyRecommendationQueueRiskReport:
            raise ValueError("snapshot_pairs must contain RiskReport values")
        normalized.append((priority_report, risk_report))
    return tuple(normalized)


def _source_window_sha256(
    source_rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
        ...
    ],
) -> str:
    return _json_sha256(
        {
            "sources": [
                {
                    "snapshot_sha256": source_row.snapshot_sha256,
                    "source_input_position": source_row.source_input_position,
                    "trend_ordinal": source_row.trend_ordinal,
                }
                for source_row in source_rows
            ],
        },
    )


def _trend_sha256(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> str:
    return _trend_sha256_from_values(
        {
            "trend_schema_version": row.trend_schema_version,
            "source_window_sha256": row.source_window_sha256,
            "source_snapshot_count": row.source_snapshot_count,
            "first_generated_at": row.first_generated_at,
            "latest_generated_at": row.latest_generated_at,
            "latest_risk_status": row.latest_risk_status,
            "risk_pass_count": row.risk_pass_count,
            "risk_watch_count": row.risk_watch_count,
            "risk_blocked_count": row.risk_blocked_count,
            "consecutive_latest_watch_count": row.consecutive_latest_watch_count,
            "consecutive_latest_blocked_count": row.consecutive_latest_blocked_count,
            "duplicate_generated_at_count": row.duplicate_generated_at_count,
            "ready_notional_first": row.ready_notional_first,
            "ready_notional_latest": row.ready_notional_latest,
            "ready_notional_delta": row.ready_notional_delta,
            "top_priority_score_first": row.top_priority_score_first,
            "top_priority_score_latest": row.top_priority_score_latest,
            "top_priority_score_delta": row.top_priority_score_delta,
            "average_priority_score_first": row.average_priority_score_first,
            "average_priority_score_latest": row.average_priority_score_latest,
            "average_priority_score_delta": row.average_priority_score_delta,
            "source_queue_count_first": row.source_queue_count_first,
            "source_queue_count_latest": row.source_queue_count_latest,
            "source_queue_count_delta": row.source_queue_count_delta,
            "latest_reason_code_counts_json": row.latest_reason_code_counts_json,
            "total_reason_code_counts_json": row.total_reason_code_counts_json,
            "repeated_reason_code_counts_json": row.repeated_reason_code_counts_json,
            "reason_code_rows_json": row.reason_code_rows_json,
        },
    )


def _trend_sha256_from_values(values: dict[str, Any]) -> str:
    return _json_sha256(
        {
            "trend_schema_version": values["trend_schema_version"],
            "source_window_sha256": values["source_window_sha256"],
            "source_snapshot_count": values["source_snapshot_count"],
            "first_generated_at": _datetime_json(values["first_generated_at"]),
            "latest_generated_at": _datetime_json(values["latest_generated_at"]),
            "latest_risk_status": values["latest_risk_status"],
            "risk_pass_count": values["risk_pass_count"],
            "risk_watch_count": values["risk_watch_count"],
            "risk_blocked_count": values["risk_blocked_count"],
            "consecutive_latest_watch_count": values[
                "consecutive_latest_watch_count"
            ],
            "consecutive_latest_blocked_count": values[
                "consecutive_latest_blocked_count"
            ],
            "duplicate_generated_at_count": values["duplicate_generated_at_count"],
            "ready_notional_first": _decimal_json(values["ready_notional_first"]),
            "ready_notional_latest": _decimal_json(values["ready_notional_latest"]),
            "ready_notional_delta": _decimal_json(values["ready_notional_delta"]),
            "top_priority_score_first": _decimal_json(values["top_priority_score_first"]),
            "top_priority_score_latest": _decimal_json(
                values["top_priority_score_latest"],
            ),
            "top_priority_score_delta": _decimal_json(values["top_priority_score_delta"]),
            "average_priority_score_first": _decimal_json(
                values["average_priority_score_first"],
            ),
            "average_priority_score_latest": _decimal_json(
                values["average_priority_score_latest"],
            ),
            "average_priority_score_delta": _decimal_json(
                values["average_priority_score_delta"],
            ),
            "source_queue_count_first": values["source_queue_count_first"],
            "source_queue_count_latest": values["source_queue_count_latest"],
            "source_queue_count_delta": values["source_queue_count_delta"],
            "latest_reason_code_counts_json": values[
                "latest_reason_code_counts_json"
            ],
            "total_reason_code_counts_json": values["total_reason_code_counts_json"],
            "repeated_reason_code_counts_json": values[
                "repeated_reason_code_counts_json"
            ],
            "reason_code_rows_json": values["reason_code_rows_json"],
        },
    )


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _counts_json_from_pairs(
    field_name: str,
    value: tuple[tuple[str, int], ...],
) -> dict[str, int]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    items = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(f"{field_name} entries must be reason/count pairs")
        reason_code, count = item
        _require_canonical_string(f"{field_name} reason_code", reason_code)
        _require_positive_int(f"{field_name} count", count)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
        items.append((reason_code, count))
    expected_items = sorted(items, key=lambda pair: (-pair[1], pair[0]))
    if items != expected_items:
        raise ValueError(f"{field_name} must use canonical count order")
    return {reason_code: count for reason_code, count in items}


def _normalize_count_json_object(field_name: str, value: object) -> dict[str, int]:
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    items = []
    seen: set[str] = set()
    for reason_code, count in value.items():
        _require_canonical_string(f"{field_name} reason_code", reason_code)
        _require_positive_int(f"{field_name} count", count)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
        items.append((reason_code, count))
    return {
        reason_code: count
        for reason_code, count in sorted(items, key=lambda pair: (-pair[1], pair[0]))
    }


def _normalize_reason_code_rows_json(
    field_name: str,
    value: object,
) -> list[dict[str, object]]:
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    rows = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} entries must be JSON objects")
        if set(item) != {"reason_code", "total_count", "latest_count", "snapshot_count"}:
            raise ValueError(f"{field_name} entries must have canonical keys")
        reason_code = item["reason_code"]
        total_count = item["total_count"]
        latest_count = item["latest_count"]
        snapshot_count = item["snapshot_count"]
        _require_canonical_string(f"{field_name} reason_code", reason_code)
        _require_positive_int(f"{field_name} total_count", total_count)
        _require_nonnegative_int(f"{field_name} latest_count", latest_count)
        _require_positive_int(f"{field_name} snapshot_count", snapshot_count)
        if latest_count > total_count:
            raise ValueError(f"{field_name} latest_count must not exceed total_count")
        if snapshot_count > total_count:
            raise ValueError(f"{field_name} snapshot_count must not exceed total_count")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
        rows.append(
            {
                "latest_count": latest_count,
                "reason_code": reason_code,
                "snapshot_count": snapshot_count,
                "total_count": total_count,
            },
        )
    expected_rows = sorted(
        rows,
        key=lambda row: (-int(row["total_count"]), str(row["reason_code"])),
    )
    if rows != expected_rows:
        raise ValueError(f"{field_name} must use canonical count order")
    return rows


def _validate_reason_count_maps(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> None:
    latest_counts = {
        str(reason_row["reason_code"]): int(reason_row["latest_count"])
        for reason_row in row.reason_code_rows_json
        if int(reason_row["latest_count"]) > 0
    }
    total_counts = {
        str(reason_row["reason_code"]): int(reason_row["total_count"])
        for reason_row in row.reason_code_rows_json
    }
    repeated_counts = {
        reason_code: count
        for reason_code, count in total_counts.items()
        if count > 1
    }
    if row.latest_reason_code_counts_json != latest_counts:
        raise ValueError("latest_reason_code_counts_json must match reason_code_rows_json")
    if row.total_reason_code_counts_json != total_counts:
        raise ValueError("total_reason_code_counts_json must match reason_code_rows_json")
    if row.repeated_reason_code_counts_json != repeated_counts:
        raise ValueError("repeated_reason_code_counts_json must match reason_code_rows_json")


def _validate_trend_row_shape(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> None:
    risk_status_total = (
        row.risk_pass_count + row.risk_watch_count + row.risk_blocked_count
    )
    if risk_status_total != row.source_snapshot_count:
        raise ValueError("risk status counts must match source_snapshot_count")
    if row.source_snapshot_count == 0:
        _validate_empty_trend_row(row)
        return
    _validate_non_empty_trend_row(row)


def _validate_empty_trend_row(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> None:
    if row.first_generated_at is not None or row.latest_generated_at is not None:
        raise ValueError("generated_at bounds must be absent without source rows")
    if row.latest_risk_status is not None:
        raise ValueError("latest_risk_status must be absent without source rows")
    for field_name in (
        "ready_notional_first",
        "ready_notional_latest",
        "ready_notional_delta",
        "top_priority_score_first",
        "top_priority_score_latest",
        "top_priority_score_delta",
        "average_priority_score_first",
        "average_priority_score_latest",
        "average_priority_score_delta",
        "source_queue_count_first",
        "source_queue_count_latest",
        "source_queue_count_delta",
    ):
        if getattr(row, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without source rows")
    for field_name in (
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
        "duplicate_generated_at_count",
    ):
        if getattr(row, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without source rows")
    if (
        row.latest_reason_code_counts_json
        or row.total_reason_code_counts_json
        or row.repeated_reason_code_counts_json
        or row.reason_code_rows_json
    ):
        raise ValueError("reason code JSON fields must be empty without source rows")


def _validate_non_empty_trend_row(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> None:
    if row.first_generated_at is None or row.latest_generated_at is None:
        raise ValueError("generated_at bounds must be present with source rows")
    if row.first_generated_at > row.latest_generated_at:
        raise ValueError("first_generated_at must not exceed latest_generated_at")
    if row.latest_risk_status is None:
        raise ValueError("latest_risk_status must be present with source rows")
    required_optional_fields = (
        "ready_notional_first",
        "ready_notional_latest",
        "ready_notional_delta",
        "top_priority_score_first",
        "top_priority_score_latest",
        "top_priority_score_delta",
        "average_priority_score_first",
        "average_priority_score_latest",
        "average_priority_score_delta",
        "source_queue_count_first",
        "source_queue_count_latest",
        "source_queue_count_delta",
    )
    for field_name in required_optional_fields:
        if getattr(row, field_name) is None:
            raise ValueError(f"{field_name} must be present with source rows")
    if row.duplicate_generated_at_count >= row.source_snapshot_count:
        raise ValueError("duplicate_generated_at_count must be less than source count")
    if row.latest_risk_status == "watch":
        if row.consecutive_latest_watch_count < 1:
            raise ValueError("consecutive_latest_watch_count must match latest_risk_status")
    elif row.consecutive_latest_watch_count != 0:
        raise ValueError("consecutive_latest_watch_count must match latest_risk_status")
    if row.latest_risk_status == "blocked":
        if row.consecutive_latest_blocked_count < 1:
            raise ValueError(
                "consecutive_latest_blocked_count must match latest_risk_status",
            )
    elif row.consecutive_latest_blocked_count != 0:
        raise ValueError(
            "consecutive_latest_blocked_count must match latest_risk_status",
        )
    if row.consecutive_latest_watch_count > row.risk_watch_count:
        raise ValueError("consecutive_latest_watch_count must not exceed risk_watch_count")
    if row.consecutive_latest_blocked_count > row.risk_blocked_count:
        raise ValueError(
            "consecutive_latest_blocked_count must not exceed risk_blocked_count",
        )


def _validate_source_generated_at_bounds(
    trend_row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
    source_rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
        ...
    ],
) -> None:
    if not source_rows:
        return
    if trend_row.first_generated_at != source_rows[0].source_generated_at:
        raise ValueError("first_generated_at must match source_rows")
    if trend_row.latest_generated_at != source_rows[-1].source_generated_at:
        raise ValueError("latest_generated_at must match source_rows")
    generated_at_counts: dict[datetime, int] = {}
    for source_row in source_rows:
        generated_at_counts[source_row.source_generated_at] = (
            generated_at_counts.get(source_row.source_generated_at, 0) + 1
        )
    duplicate_count = sum(
        count - 1
        for count in generated_at_counts.values()
        if count > 1
    )
    if trend_row.duplicate_generated_at_count != duplicate_count:
        raise ValueError("duplicate_generated_at_count must match source_rows")


def _datetime_json(value: object) -> str | None:
    if value is None:
        return None
    return _as_utc("datetime", value).isoformat()


def _decimal_json(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError("hash Decimal value must be a Decimal")
    if not value.is_finite():
        raise ValueError("hash Decimal value must be finite")
    return str(value.quantize(DECIMAL_QUANTUM))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _quantize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _reject_json_floats(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_risk_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
