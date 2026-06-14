"""Report-only proposal-review quality gates for Level 2."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryReport,
)


__all__ = (
    "TradeProposalReviewQualityConfig",
    "TradeProposalReviewQualityGateResult",
    "TradeProposalReviewQualityLog",
    "TradeProposalReviewQualityReasonTrend",
    "TradeProposalReviewQualityReport",
    "build_trade_proposal_review_quality_report",
)


DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review quality artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")
GATE_NAMES = (
    "data_integrity",
    "sample_size",
    "rejection_ratio",
    "reason_concentration",
    "duplicate_source_review_volume",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "incomplete_review_data",
    "insufficient_review_sample",
    "unstable_review_quality",
    "proposal_review_quality_ready",
)


@dataclass(frozen=True)
class TradeProposalReviewQualityConfig:
    config_version: str
    min_summary_report_count: int = 1
    min_total_review_record_count: int = 1
    max_overall_rejection_ratio: Decimal = Decimal("0.5000")
    max_worst_summary_rejection_ratio: Decimal = Decimal("0.7500")
    max_reason_code_rejection_share: Decimal = Decimal("0.7500")
    max_duplicate_source_proposal_ratio: Decimal = Decimal("0.2500")
    max_duplicate_source_proposal_count: int = 0
    boundary_statement: str = DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_summary_report_count",
            self.min_summary_report_count,
        )
        _require_nonnegative_int(
            "min_total_review_record_count",
            self.min_total_review_record_count,
        )
        _require_probability_decimal(
            "max_overall_rejection_ratio",
            self.max_overall_rejection_ratio,
        )
        _require_probability_decimal(
            "max_worst_summary_rejection_ratio",
            self.max_worst_summary_rejection_ratio,
        )
        _require_probability_decimal(
            "max_reason_code_rejection_share",
            self.max_reason_code_rejection_share,
        )
        _require_probability_decimal(
            "max_duplicate_source_proposal_ratio",
            self.max_duplicate_source_proposal_ratio,
        )
        _require_nonnegative_int(
            "max_duplicate_source_proposal_count",
            self.max_duplicate_source_proposal_count,
        )
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalReviewQualityGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known proposal review quality gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known proposal review quality gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalReviewQualityReasonTrend:
    reason_code: str
    summary_report_count: int
    total_rejected_decision_count: int
    max_rejected_decision_ratio: Decimal
    latest_rejected_decision_ratio: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("summary_report_count", self.summary_report_count)
        _require_positive_int(
            "total_rejected_decision_count",
            self.total_rejected_decision_count,
        )
        _require_probability_decimal(
            "max_rejected_decision_ratio",
            self.max_rejected_decision_ratio,
        )
        _require_probability_decimal(
            "latest_rejected_decision_ratio",
            self.latest_rejected_decision_ratio,
        )
        if self.latest_rejected_decision_ratio > self.max_rejected_decision_ratio:
            raise ValueError(
                "latest_rejected_decision_ratio must not exceed max_rejected_decision_ratio"
            )


@dataclass(frozen=True)
class TradeProposalReviewQualityReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    summary_report_count: int
    first_summary_generated_at: datetime | None
    last_summary_generated_at: datetime | None
    total_review_record_count: int
    summed_unique_source_proposal_count: int
    total_duplicate_source_proposal_count: int
    approved_decision_count: int
    rejected_decision_count: int
    overall_rejection_ratio: Decimal | None
    latest_summary_rejection_ratio: Decimal | None
    worst_summary_rejection_ratio: Decimal | None
    max_reason_code_rejection_share: Decimal | None
    duplicate_source_proposal_ratio: Decimal | None
    status: str
    gate_results: tuple[TradeProposalReviewQualityGateResult, ...]
    reason_trends: tuple[TradeProposalReviewQualityReasonTrend, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.first_summary_generated_at is not None:
            object.__setattr__(
                self,
                "first_summary_generated_at",
                _as_utc(self.first_summary_generated_at),
            )
        if self.last_summary_generated_at is not None:
            object.__setattr__(
                self,
                "last_summary_generated_at",
                _as_utc(self.last_summary_generated_at),
            )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "summary_report_count",
            "total_review_record_count",
            "summed_unique_source_proposal_count",
            "total_duplicate_source_proposal_count",
            "approved_decision_count",
            "rejected_decision_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.total_review_record_count != (
            self.approved_decision_count + self.rejected_decision_count
        ):
            raise ValueError(
                "total_review_record_count must equal approved and rejected decision counts"
            )
        if self.summed_unique_source_proposal_count > self.total_review_record_count:
            raise ValueError(
                "summed_unique_source_proposal_count must not exceed total_review_record_count"
            )
        if self.total_duplicate_source_proposal_count > self.total_review_record_count:
            raise ValueError(
                "total_duplicate_source_proposal_count must not exceed total_review_record_count"
            )
        if (
            self.summed_unique_source_proposal_count
            + self.total_duplicate_source_proposal_count
            != self.total_review_record_count
        ):
            raise ValueError(
                "summed_unique_source_proposal_count and total_duplicate_source_proposal_count "
                "must equal total_review_record_count"
            )
        if self.summary_report_count == 0:
            if (
                self.first_summary_generated_at is not None
                or self.last_summary_generated_at is not None
            ):
                raise ValueError("summary generated_at bounds must be absent without summaries")
            if any(
                value is not None
                for value in (
                    self.overall_rejection_ratio,
                    self.latest_summary_rejection_ratio,
                    self.worst_summary_rejection_ratio,
                    self.max_reason_code_rejection_share,
                    self.duplicate_source_proposal_ratio,
                )
            ):
                raise ValueError("ratios must be absent without summaries")
            if self.reason_trends != ():
                raise ValueError("reason_trends must be empty without summaries")
        else:
            if (
                self.first_summary_generated_at is None
                or self.last_summary_generated_at is None
            ):
                raise ValueError("summary generated_at bounds are required with summaries")
            if self.first_summary_generated_at > self.last_summary_generated_at:
                raise ValueError("first_summary_generated_at must be before last_summary_generated_at")
        if self.total_review_record_count == 0:
            if any(
                value is not None
                for value in (
                    self.overall_rejection_ratio,
                    self.latest_summary_rejection_ratio,
                    self.worst_summary_rejection_ratio,
                    self.duplicate_source_proposal_ratio,
                )
            ):
                raise ValueError("decision ratios must be absent without review records")
        else:
            expected_overall = _ratio_from_counts(
                self.rejected_decision_count,
                self.total_review_record_count,
            )
            if self.overall_rejection_ratio != expected_overall:
                raise ValueError(
                    "overall_rejection_ratio must match rejected decision count"
                )
            expected_duplicate = _ratio_from_counts(
                self.total_duplicate_source_proposal_count,
                self.total_review_record_count,
            )
            if self.duplicate_source_proposal_ratio != expected_duplicate:
                raise ValueError(
                    "duplicate_source_proposal_ratio must match duplicate source count"
                )
            if self.latest_summary_rejection_ratio is None:
                raise ValueError(
                    "latest_summary_rejection_ratio is required with review records"
                )
            if self.worst_summary_rejection_ratio is None:
                raise ValueError(
                    "worst_summary_rejection_ratio is required with review records"
                )
        for field_name in (
            "overall_rejection_ratio",
            "latest_summary_rejection_ratio",
            "worst_summary_rejection_ratio",
            "max_reason_code_rejection_share",
            "duplicate_source_proposal_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known proposal review quality status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                TradeProposalReviewQualityGateResult,
            ),
        )
        object.__setattr__(
            self,
            "reason_trends",
            _normalize_typed_tuple(
                "reason_trends",
                self.reason_trends,
                TradeProposalReviewQualityReasonTrend,
            ),
        )
        if tuple(row.gate_name for row in self.gate_results) != GATE_NAMES:
            raise ValueError("gate_results must contain the five proposal review quality gates")
        if self.status != _quality_status(self.gate_results):
            raise ValueError("status must match proposal review quality gate results")
        if tuple(sorted(self.reason_trends, key=lambda item: item.reason_code)) != self.reason_trends:
            raise ValueError("reason_trends must be sorted by reason_code")
        if (
            self.total_review_record_count > 0
            and self.overall_rejection_ratio is not None
            and self.worst_summary_rejection_ratio is not None
            and self.overall_rejection_ratio > self.worst_summary_rejection_ratio
        ):
            raise ValueError(
                "worst_summary_rejection_ratio must not be below overall_rejection_ratio"
            )
        if (
            self.latest_summary_rejection_ratio is not None
            and self.worst_summary_rejection_ratio is not None
            and self.latest_summary_rejection_ratio > self.worst_summary_rejection_ratio
        ):
            raise ValueError(
                "latest_summary_rejection_ratio must not exceed worst_summary_rejection_ratio"
            )
        if self.rejected_decision_count == 0:
            if self.max_reason_code_rejection_share is not None:
                raise ValueError(
                    "max_reason_code_rejection_share must be absent without rejected decisions"
                )
            if self.reason_trends != ():
                raise ValueError("reason_trends must be empty without rejected decisions")
        else:
            if self.max_reason_code_rejection_share is None:
                raise ValueError(
                    "max_reason_code_rejection_share is required with rejected decisions"
                )
            expected_reason_share = _ratio_from_counts(
                max(row.total_rejected_decision_count for row in self.reason_trends),
                self.rejected_decision_count,
            )
            if self.max_reason_code_rejection_share != expected_reason_share:
                raise ValueError(
                    "max_reason_code_rejection_share must match reason trend counts"
                )


@dataclass(frozen=True)
class TradeProposalReviewQualityLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalReviewQualityReport) -> None:
        if type(report) is not TradeProposalReviewQualityReport:
            raise ValueError("report must be a TradeProposalReviewQualityReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_quality_report(
    summaries: Iterable[TradeProposalReviewSummaryReport],
    *,
    config: TradeProposalReviewQualityConfig,
    generated_at: datetime,
) -> TradeProposalReviewQualityReport:
    if isinstance(summaries, (str, bytes)):
        raise ValueError(
            "summaries must be an iterable of TradeProposalReviewSummaryReport values"
        )
    if type(config) is not TradeProposalReviewQualityConfig:
        raise ValueError("config must be a TradeProposalReviewQualityConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    try:
        summary_items = tuple(summaries)
    except TypeError as exc:
        raise ValueError(
            "summaries must be an iterable of TradeProposalReviewSummaryReport values"
        ) from exc
    validated_summaries = tuple(_clone_summary_report(summary) for summary in summary_items)
    sorted_summaries = tuple(
        sorted(
            validated_summaries,
            key=lambda item: (_as_utc(item.generated_at), item.config_version),
        )
    )
    seen_generated_at: set[datetime] = set()
    for summary in sorted_summaries:
        summary_generated_at = _as_utc(summary.generated_at)
        if summary_generated_at in seen_generated_at:
            raise ValueError("duplicate summary generated_at values are not allowed")
        seen_generated_at.add(summary_generated_at)

    summary_report_count = len(sorted_summaries)
    total_review_record_count = sum(
        summary.review_record_count for summary in sorted_summaries
    )
    summed_unique_source_proposal_count = sum(
        summary.unique_source_proposal_count for summary in sorted_summaries
    )
    total_duplicate_source_proposal_count = sum(
        summary.duplicate_source_proposal_count for summary in sorted_summaries
    )
    approved_decision_count = sum(
        summary.approved_decision_count for summary in sorted_summaries
    )
    rejected_decision_count = sum(
        summary.rejected_decision_count for summary in sorted_summaries
    )
    non_empty_summary_ratios = tuple(
        summary.rejection_ratio
        for summary in sorted_summaries
        if summary.rejection_ratio is not None
    )
    reason_trends = _build_reason_trends(sorted_summaries)
    max_reason_code_rejection_share = (
        _ratio_from_counts(
            max(row.total_rejected_decision_count for row in reason_trends),
            rejected_decision_count,
        )
        if rejected_decision_count > 0 and reason_trends
        else None
    )
    overall_rejection_ratio = _optional_ratio_from_counts(
        rejected_decision_count,
        total_review_record_count,
    )
    latest_summary_rejection_ratio = (
        non_empty_summary_ratios[-1] if non_empty_summary_ratios else None
    )
    worst_summary_rejection_ratio = _max_optional_ratio(non_empty_summary_ratios)
    duplicate_source_proposal_ratio = _optional_ratio_from_counts(
        total_duplicate_source_proposal_count,
        total_review_record_count,
    )
    gate_results = _build_gate_results(
        summary_report_count=summary_report_count,
        total_review_record_count=total_review_record_count,
        overall_rejection_ratio=overall_rejection_ratio,
        worst_summary_rejection_ratio=worst_summary_rejection_ratio,
        max_reason_code_rejection_share=max_reason_code_rejection_share,
        duplicate_source_proposal_ratio=duplicate_source_proposal_ratio,
        total_duplicate_source_proposal_count=total_duplicate_source_proposal_count,
        rejected_decision_count=rejected_decision_count,
        reason_trend_count=len(reason_trends),
        config=config,
    )
    return TradeProposalReviewQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        summary_report_count=summary_report_count,
        first_summary_generated_at=(
            _as_utc(sorted_summaries[0].generated_at) if sorted_summaries else None
        ),
        last_summary_generated_at=(
            _as_utc(sorted_summaries[-1].generated_at) if sorted_summaries else None
        ),
        total_review_record_count=total_review_record_count,
        summed_unique_source_proposal_count=summed_unique_source_proposal_count,
        total_duplicate_source_proposal_count=total_duplicate_source_proposal_count,
        approved_decision_count=approved_decision_count,
        rejected_decision_count=rejected_decision_count,
        overall_rejection_ratio=overall_rejection_ratio,
        latest_summary_rejection_ratio=latest_summary_rejection_ratio,
        worst_summary_rejection_ratio=worst_summary_rejection_ratio,
        max_reason_code_rejection_share=max_reason_code_rejection_share,
        duplicate_source_proposal_ratio=duplicate_source_proposal_ratio,
        status=_quality_status(gate_results),
        gate_results=gate_results,
        reason_trends=reason_trends,
    )


def _build_reason_trends(
    summaries: tuple[TradeProposalReviewSummaryReport, ...],
) -> tuple[TradeProposalReviewQualityReasonTrend, ...]:
    reason_rows_by_code: dict[str, list[TradeProposalReviewReasonCodeSummary]] = {}
    for summary in summaries:
        for row in summary.reason_code_summaries:
            reason_rows_by_code.setdefault(row.reason_code, []).append(row)

    trend_rows: list[TradeProposalReviewQualityReasonTrend] = []
    for reason_code in sorted(reason_rows_by_code):
        rows = reason_rows_by_code[reason_code]
        trend_rows.append(
            TradeProposalReviewQualityReasonTrend(
                reason_code=reason_code,
                summary_report_count=len(rows),
                total_rejected_decision_count=sum(
                    row.rejected_decision_count for row in rows
                ),
                max_rejected_decision_ratio=max(
                    row.rejected_decision_ratio for row in rows
                ),
                latest_rejected_decision_ratio=rows[-1].rejected_decision_ratio,
            )
        )
    return tuple(trend_rows)


def _build_gate_results(
    *,
    summary_report_count: int,
    total_review_record_count: int,
    overall_rejection_ratio: Decimal | None,
    worst_summary_rejection_ratio: Decimal | None,
    max_reason_code_rejection_share: Decimal | None,
    duplicate_source_proposal_ratio: Decimal | None,
    total_duplicate_source_proposal_count: int,
    rejected_decision_count: int,
    reason_trend_count: int,
    config: TradeProposalReviewQualityConfig,
) -> tuple[TradeProposalReviewQualityGateResult, ...]:
    if summary_report_count == 0:
        return tuple(
            TradeProposalReviewQualityGateResult(
                gate_name=gate_name,
                status="incomplete",
                message="No proposal-review summary reports are available.",
                observed_value=0,
                threshold=1,
            )
            for gate_name in GATE_NAMES
        )

    sample_passes = (
        total_review_record_count > 0
        and summary_report_count >= config.min_summary_report_count
        and total_review_record_count >= config.min_total_review_record_count
    )
    rejection_complete = (
        overall_rejection_ratio is not None
        and worst_summary_rejection_ratio is not None
    )
    rejection_fails = (
        rejection_complete
        and (
            overall_rejection_ratio > config.max_overall_rejection_ratio
            or worst_summary_rejection_ratio > config.max_worst_summary_rejection_ratio
        )
    )
    reason_complete = (
        rejected_decision_count > 0
        and reason_trend_count > 0
        and max_reason_code_rejection_share is not None
    )
    reason_fails = (
        reason_complete
        and max_reason_code_rejection_share > config.max_reason_code_rejection_share
    )
    duplicate_complete = duplicate_source_proposal_ratio is not None
    duplicate_fails = (
        duplicate_complete
        and (
            duplicate_source_proposal_ratio > config.max_duplicate_source_proposal_ratio
            or total_duplicate_source_proposal_count
            > config.max_duplicate_source_proposal_count
        )
    )

    return (
        TradeProposalReviewQualityGateResult(
            gate_name="data_integrity",
            status="pass",
            message="Proposal-review summary reports are sorted and duplicate-free.",
            observed_value=summary_report_count,
            threshold=1,
        ),
        TradeProposalReviewQualityGateResult(
            gate_name="sample_size",
            status="pass" if sample_passes else "fail",
            message=(
                "Proposal-review sample-size thresholds are met."
                if sample_passes
                else "Proposal-review sample-size thresholds are not met."
            ),
            observed_value=(
                f"summary_report_count={summary_report_count}; "
                f"total_review_record_count={total_review_record_count}"
            ),
            threshold=(
                f"min_summary_report_count={config.min_summary_report_count}; "
                f"min_total_review_record_count={config.min_total_review_record_count}"
            ),
        ),
        TradeProposalReviewQualityGateResult(
            gate_name="rejection_ratio",
            status=(
                "pass"
                if rejection_complete and not rejection_fails
                else ("fail" if rejection_complete else "incomplete")
            ),
            message=(
                "Proposal-review rejection ratios are within thresholds."
                if rejection_complete and not rejection_fails
                else (
                    "Proposal-review rejection ratios breach thresholds."
                    if rejection_complete
                    else "No proposal-review decisions are available."
                )
            ),
            observed_value=(
                "overall_rejection_ratio="
                f"{_display_optional_decimal(overall_rejection_ratio)}; "
                "worst_summary_rejection_ratio="
                f"{_display_optional_decimal(worst_summary_rejection_ratio)}"
                if rejection_complete
                else None
            ),
            threshold=(
                f"max_overall_rejection_ratio={config.max_overall_rejection_ratio}; "
                "max_worst_summary_rejection_ratio="
                f"{config.max_worst_summary_rejection_ratio}"
            ),
        ),
        TradeProposalReviewQualityGateResult(
            gate_name="reason_concentration",
            status=(
                "pass"
                if reason_complete and not reason_fails
                else ("fail" if reason_complete else "incomplete")
            ),
            message=(
                "Rejected reason-code concentration is within threshold."
                if reason_complete and not reason_fails
                else (
                    "Rejected reason-code concentration breaches threshold."
                    if reason_complete
                    else "No rejected reason-code rows are available."
                )
            ),
            observed_value=max_reason_code_rejection_share if reason_complete else None,
            threshold=config.max_reason_code_rejection_share,
        ),
        TradeProposalReviewQualityGateResult(
            gate_name="duplicate_source_review_volume",
            status=(
                "pass"
                if duplicate_complete and not duplicate_fails
                else ("fail" if duplicate_complete else "incomplete")
            ),
            message=(
                "Duplicate source proposal review volume is within thresholds."
                if duplicate_complete and not duplicate_fails
                else (
                    "Duplicate source proposal review volume breaches thresholds."
                    if duplicate_complete
                    else "No proposal-review decisions are available."
                )
            ),
            observed_value=(
                "duplicate_source_proposal_ratio="
                f"{_display_optional_decimal(duplicate_source_proposal_ratio)}; "
                "total_duplicate_source_proposal_count="
                f"{total_duplicate_source_proposal_count}"
                if duplicate_complete
                else None
            ),
            threshold=(
                "max_duplicate_source_proposal_ratio="
                f"{config.max_duplicate_source_proposal_ratio}; "
                "max_duplicate_source_proposal_count="
                f"{config.max_duplicate_source_proposal_count}"
            ),
        ),
    )


def _quality_status(
    gate_results: tuple[TradeProposalReviewQualityGateResult, ...],
) -> str:
    gates = {gate.gate_name: gate for gate in gate_results}
    if gates["data_integrity"].status == "incomplete":
        return "incomplete_review_data"
    if gates["sample_size"].status in ("fail", "incomplete"):
        return "insufficient_review_sample"
    if (
        gates["rejection_ratio"].status == "fail"
        or gates["reason_concentration"].status == "fail"
        or gates["duplicate_source_review_volume"].status == "fail"
    ):
        return "unstable_review_quality"
    return "proposal_review_quality_ready"


def _clone_summary_report(
    summary: TradeProposalReviewSummaryReport,
) -> TradeProposalReviewSummaryReport:
    if type(summary) is not TradeProposalReviewSummaryReport:
        raise ValueError("summaries must contain TradeProposalReviewSummaryReport values")
    reason_code_summaries = tuple(
        TradeProposalReviewReasonCodeSummary(
            reason_code=row.reason_code,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_ratio=row.rejected_decision_ratio,
        )
        for row in summary.reason_code_summaries
    )
    bucket_summaries = tuple(
        TradeProposalReviewBucketSummary(
            bucket_type=row.bucket_type,
            bucket_value=row.bucket_value,
            review_record_count=row.review_record_count,
            unique_source_proposal_count=row.unique_source_proposal_count,
            approved_decision_count=row.approved_decision_count,
            rejected_decision_count=row.rejected_decision_count,
            rejection_ratio=row.rejection_ratio,
        )
        for row in summary.bucket_summaries
    )
    return TradeProposalReviewSummaryReport(
        generated_at=summary.generated_at,
        config_version=summary.config_version,
        report_only=summary.report_only,
        boundary_statement=summary.boundary_statement,
        review_record_count=summary.review_record_count,
        unique_source_proposal_count=summary.unique_source_proposal_count,
        duplicate_source_proposal_count=summary.duplicate_source_proposal_count,
        first_recorded_at=summary.first_recorded_at,
        last_recorded_at=summary.last_recorded_at,
        approved_decision_count=summary.approved_decision_count,
        rejected_decision_count=summary.rejected_decision_count,
        rejection_ratio=summary.rejection_ratio,
        status=summary.status,
        reason_code_summaries=reason_code_summaries,
        bucket_summaries=bucket_summaries,
    )


def _validate_report_tree(
    report: TradeProposalReviewQualityReport,
) -> TradeProposalReviewQualityReport:
    gate_results = tuple(
        TradeProposalReviewQualityGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in report.gate_results
    )
    reason_trends = tuple(
        TradeProposalReviewQualityReasonTrend(
            reason_code=row.reason_code,
            summary_report_count=row.summary_report_count,
            total_rejected_decision_count=row.total_rejected_decision_count,
            max_rejected_decision_ratio=row.max_rejected_decision_ratio,
            latest_rejected_decision_ratio=row.latest_rejected_decision_ratio,
        )
        for row in report.reason_trends
    )
    return TradeProposalReviewQualityReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        summary_report_count=report.summary_report_count,
        first_summary_generated_at=report.first_summary_generated_at,
        last_summary_generated_at=report.last_summary_generated_at,
        total_review_record_count=report.total_review_record_count,
        summed_unique_source_proposal_count=report.summed_unique_source_proposal_count,
        total_duplicate_source_proposal_count=report.total_duplicate_source_proposal_count,
        approved_decision_count=report.approved_decision_count,
        rejected_decision_count=report.rejected_decision_count,
        overall_rejection_ratio=report.overall_rejection_ratio,
        latest_summary_rejection_ratio=report.latest_summary_rejection_ratio,
        worst_summary_rejection_ratio=report.worst_summary_rejection_ratio,
        max_reason_code_rejection_share=report.max_reason_code_rejection_share,
        duplicate_source_proposal_ratio=report.duplicate_source_proposal_ratio,
        status=report.status,
        gate_results=gate_results,
        reason_trends=reason_trends,
    )


def _max_optional_ratio(values: Iterable[Decimal | None]) -> Decimal | None:
    sampled: list[Decimal] = []
    for value in values:
        if value is None:
            continue
        _require_probability_decimal("value", value)
        sampled.append(value)
    return max(sampled) if sampled else None


def _display_optional_decimal(value: Decimal | None) -> str:
    return "None" if value is None else str(value)


def _ratio_from_counts(numerator: int, denominator: int) -> Decimal:
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _optional_ratio_from_counts(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _ratio_from_counts(numerator, denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_finite_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    lowered = value.lower()
    required_parts = (
        "report-only",
        "proposal-review quality",
        "not an approval workflow",
        "trade instruction",
        "order instruction",
        "broker request",
        "order request",
        "account action",
        "account authentication",
        "private-key handling",
        "wallet signature",
        "live-execution signal",
        "credential workflow",
        "manual execution import",
        "strategy-promotion signal",
        "automatic order-placement authorization",
    )
    if any(part not in lowered for part in required_parts):
        raise ValueError(
            "boundary_statement must describe report-only proposal-review quality"
        )


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_gate_value(
    field_name: str,
    value: Decimal | int | str | None,
) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        _require_finite_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _normalize_typed_tuple(
    field_name: str,
    values: Iterable[Any],
    expected_type: type[Any],
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items
