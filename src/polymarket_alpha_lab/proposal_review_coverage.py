"""Report-only proposal-review coverage artifacts for Level 2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_packet import TradeProposalPacket
from polymarket_alpha_lab.proposal_review import TradeProposalReviewRecord


__all__ = (
    "TradeProposalReviewCoverageBucketRow",
    "TradeProposalReviewCoverageConfig",
    "TradeProposalReviewCoverageGateResult",
    "TradeProposalReviewCoverageLog",
    "TradeProposalReviewCoveragePacketRow",
    "TradeProposalReviewCoverageReport",
    "build_trade_proposal_review_coverage_report",
)


DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review coverage artifact, not an approval "
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
    "proposal_sample",
    "review_coverage",
    "duplicate_review_volume",
    "decision_consistency",
)
GATE_STATUSES = ("pass", "fail")
REPORT_STATUSES = (
    "incomplete_proposal_sample",
    "incomplete_review_coverage",
    "inconsistent_review_coverage",
    "proposal_review_coverage_ready",
)
BUCKET_NAMES = (
    "conflicting_decision",
    "duplicate_reviewed",
    "orphan_review_record",
    "reviewed",
    "unreviewed",
)
COVERAGE_BUCKETS = (
    "reviewed",
    "unreviewed",
    "duplicate_reviewed",
    "conflicting_decision",
    "orphan_review_record",
)
COVERAGE_STATUSES = (
    "conflicting",
    "duplicate_reviewed",
    "orphan",
    "reviewed",
    "unreviewed",
)
SOURCE_FINGERPRINT_FIELDS = (
    "source_proposal_packet_id",
    "source_proposal_generated_at",
    "source_proposal_config_version",
    "source_proposal_boundary_statement",
    "source_queue_boundary_statement",
    "source_proposal_only",
    "source_human_approval_required",
    "source_queue_item_id",
    "source_queue_rank",
    "source_manual_review_status",
    "source_packet_id",
    "source_paper_only",
    "condition_id",
    "token_id",
    "market_slug",
    "market_url",
    "question",
    "outcome_name",
    "strategy_type",
    "side",
    "intended_order_type",
    "executable_price_assumption",
    "maximum_size",
    "source_max_executable_size",
    "cost_adjusted_edge",
    "theoretical_edge",
    "fair_value_estimate",
    "model_probability",
    "confidence",
    "source_score",
    "market_score_total",
    "exposure_after_trade",
    "exit_rule",
    "thesis",
    "invalidating_conditions",
    "rule_text_hash",
    "resolution_source",
    "risk_tags",
    "reason_trade_could_be_wrong",
    "readiness_summary",
    "risk_summary",
    "evidence_summary",
    "why_in_queue",
    "primary_reason_code",
    "supporting_reason_codes",
    "review_focus",
    "evidence_scope",
    "history_status",
    "forecast_status",
    "history_gate_pass_count",
    "forecast_gate_pass_count",
    "history_gate_fail_count",
    "forecast_gate_fail_count",
    "risk_gate_passed",
    "hard_block_count",
    "blocking_reason_codes",
)


@dataclass(frozen=True)
class TradeProposalReviewCoverageConfig:
    config_version: str
    min_proposal_packet_count: int = 1
    min_review_coverage_ratio: Decimal = Decimal("1.0000")
    max_duplicate_reviewed_proposal_packet_ratio: Decimal = Decimal("1.0000")
    max_duplicate_reviewed_proposal_packet_count: int = 0
    max_conflicting_decision_proposal_packet_ratio: Decimal = Decimal("1.0000")
    max_conflicting_decision_proposal_packet_count: int = 0
    max_orphan_review_record_ratio: Decimal = Decimal("1.0000")
    max_orphan_review_record_count: int = 0
    boundary_statement: str = DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_proposal_packet_count",
            self.min_proposal_packet_count,
        )
        _require_probability_decimal(
            "min_review_coverage_ratio",
            self.min_review_coverage_ratio,
        )
        _require_probability_decimal(
            "max_duplicate_reviewed_proposal_packet_ratio",
            self.max_duplicate_reviewed_proposal_packet_ratio,
        )
        _require_nonnegative_int(
            "max_duplicate_reviewed_proposal_packet_count",
            self.max_duplicate_reviewed_proposal_packet_count,
        )
        _require_probability_decimal(
            "max_conflicting_decision_proposal_packet_ratio",
            self.max_conflicting_decision_proposal_packet_ratio,
        )
        _require_nonnegative_int(
            "max_conflicting_decision_proposal_packet_count",
            self.max_conflicting_decision_proposal_packet_count,
        )
        _require_probability_decimal(
            "max_orphan_review_record_ratio",
            self.max_orphan_review_record_ratio,
        )
        _require_nonnegative_int(
            "max_orphan_review_record_count",
            self.max_orphan_review_record_count,
        )
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalReviewCoverageGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known proposal review coverage gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be pass or fail")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalReviewCoverageBucketRow:
    bucket_name: str
    proposal_packet_count: int
    review_record_count: int
    coverage_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.bucket_name not in BUCKET_NAMES:
            raise ValueError("bucket_name must be a known proposal review coverage bucket")
        _require_nonnegative_int("proposal_packet_count", self.proposal_packet_count)
        _require_nonnegative_int("review_record_count", self.review_record_count)
        _require_optional_probability_decimal("coverage_ratio", self.coverage_ratio)


@dataclass(frozen=True)
class TradeProposalReviewCoveragePacketRow:
    coverage_status: str
    proposal_packet_id: str
    source_proposal_fingerprint: str | None
    first_proposal_generated_at: datetime | None
    last_proposal_generated_at: datetime | None
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    review_record_count: int
    approved_decision_count: int
    rejected_decision_count: int
    market_slug: str | None
    strategy_type: str | None
    risk_tags: tuple[str, ...]
    review_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.coverage_status not in COVERAGE_STATUSES:
            raise ValueError("coverage_status must be a known coverage status")
        _require_canonical_string("proposal_packet_id", self.proposal_packet_id)
        if self.source_proposal_fingerprint is not None:
            _require_canonical_string(
                "source_proposal_fingerprint",
                self.source_proposal_fingerprint,
            )
        if self.first_proposal_generated_at is not None:
            object.__setattr__(
                self,
                "first_proposal_generated_at",
                _as_utc(self.first_proposal_generated_at),
            )
        if self.last_proposal_generated_at is not None:
            object.__setattr__(
                self,
                "last_proposal_generated_at",
                _as_utc(self.last_proposal_generated_at),
            )
        if self.first_recorded_at is not None:
            object.__setattr__(self, "first_recorded_at", _as_utc(self.first_recorded_at))
        if self.last_recorded_at is not None:
            object.__setattr__(self, "last_recorded_at", _as_utc(self.last_recorded_at))
        for field_name in (
            "review_record_count",
            "approved_decision_count",
            "rejected_decision_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.approved_decision_count > self.review_record_count:
            raise ValueError(
                "approved_decision_count must not exceed review_record_count"
            )
        if self.rejected_decision_count > self.review_record_count:
            raise ValueError(
                "rejected_decision_count must not exceed review_record_count"
            )
        if self.review_record_count != (
            self.approved_decision_count + self.rejected_decision_count
        ):
            raise ValueError(
                "review_record_count must equal approved and rejected decision counts"
            )
        if self.market_slug is not None:
            _require_canonical_string("market_slug", self.market_slug)
        if self.strategy_type is not None:
            _require_canonical_string("strategy_type", self.strategy_type)
        object.__setattr__(
            self,
            "risk_tags",
            _normalize_sorted_string_tuple("risk_tags", self.risk_tags),
        )
        object.__setattr__(
            self,
            "review_record_ids",
            _normalize_string_tuple("review_record_ids", self.review_record_ids),
        )
        if tuple(sorted(self.review_record_ids)) != self.review_record_ids:
            raise ValueError("review_record_ids must be sorted")
        if len(self.review_record_ids) != self.review_record_count:
            raise ValueError("review_record_ids must match review_record_count")
        if len(set(self.review_record_ids)) != len(self.review_record_ids):
            raise ValueError("review_record_ids must be unique")
        if self.coverage_status == "unreviewed":
            if self.review_record_count != 0 or self.review_record_ids != ():
                raise ValueError("unreviewed packet rows must not contain review records")
            if self.first_recorded_at is not None or self.last_recorded_at is not None:
                raise ValueError("recorded_at bounds must be absent without records")
        else:
            if self.review_record_count == 0:
                raise ValueError("review_record_count must be positive for reviewed rows")
            if self.first_recorded_at is None or self.last_recorded_at is None:
                raise ValueError("recorded_at bounds are required with records")
        if self.first_recorded_at is not None and self.last_recorded_at is not None:
            if self.first_recorded_at > self.last_recorded_at:
                raise ValueError("first_recorded_at must be before last_recorded_at")
        if (
            self.first_proposal_generated_at is not None
            and self.last_proposal_generated_at is not None
            and self.first_proposal_generated_at > self.last_proposal_generated_at
        ):
            raise ValueError(
                "first_proposal_generated_at must be before last_proposal_generated_at"
            )
        if self.coverage_status == "orphan":
            if self.first_proposal_generated_at is not None:
                raise ValueError("orphan rows must not contain proposal generated_at bounds")
            if self.last_proposal_generated_at is not None:
                raise ValueError("orphan rows must not contain proposal generated_at bounds")
        else:
            if (
                self.first_proposal_generated_at is None
                or self.last_proposal_generated_at is None
            ):
                raise ValueError("proposal generated_at bounds are required")


@dataclass(frozen=True)
class TradeProposalReviewCoverageReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    proposal_packet_count: int
    review_record_count: int
    reviewed_proposal_packet_count: int
    unreviewed_proposal_packet_count: int
    duplicate_reviewed_proposal_packet_count: int
    conflicting_decision_proposal_packet_count: int
    orphan_review_record_count: int
    approved_decision_count: int
    rejected_decision_count: int
    review_coverage_ratio: Decimal | None
    unreviewed_proposal_packet_ratio: Decimal | None
    duplicate_reviewed_proposal_packet_ratio: Decimal | None
    conflicting_decision_proposal_packet_ratio: Decimal | None
    orphan_review_record_ratio: Decimal | None
    first_proposal_generated_at: datetime | None
    last_proposal_generated_at: datetime | None
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalReviewCoverageGateResult, ...]
    bucket_rows: tuple[TradeProposalReviewCoverageBucketRow, ...]
    packet_rows: tuple[TradeProposalReviewCoveragePacketRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.first_proposal_generated_at is not None:
            object.__setattr__(
                self,
                "first_proposal_generated_at",
                _as_utc(self.first_proposal_generated_at),
            )
        if self.last_proposal_generated_at is not None:
            object.__setattr__(
                self,
                "last_proposal_generated_at",
                _as_utc(self.last_proposal_generated_at),
            )
        if self.first_recorded_at is not None:
            object.__setattr__(self, "first_recorded_at", _as_utc(self.first_recorded_at))
        if self.last_recorded_at is not None:
            object.__setattr__(self, "last_recorded_at", _as_utc(self.last_recorded_at))
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "proposal_packet_count",
            "review_record_count",
            "reviewed_proposal_packet_count",
            "unreviewed_proposal_packet_count",
            "duplicate_reviewed_proposal_packet_count",
            "conflicting_decision_proposal_packet_count",
            "orphan_review_record_count",
            "approved_decision_count",
            "rejected_decision_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.review_record_count != (
            self.approved_decision_count + self.rejected_decision_count
        ):
            raise ValueError(
                "review_record_count must equal approved and rejected decision counts"
            )
        if self.proposal_packet_count != (
            self.reviewed_proposal_packet_count
            + self.unreviewed_proposal_packet_count
        ):
            raise ValueError(
                "proposal_packet_count must equal reviewed and unreviewed counts"
            )
        if self.duplicate_reviewed_proposal_packet_count > self.proposal_packet_count:
            raise ValueError(
                "duplicate_reviewed_proposal_packet_count must not exceed proposal_packet_count"
            )
        if self.conflicting_decision_proposal_packet_count > self.proposal_packet_count:
            raise ValueError(
                "conflicting_decision_proposal_packet_count must not exceed proposal_packet_count"
            )
        if self.orphan_review_record_count > self.review_record_count:
            raise ValueError("orphan_review_record_count must not exceed review_record_count")
        if self.proposal_packet_count == 0:
            if any(
                value is not None
                for value in (
                    self.review_coverage_ratio,
                    self.unreviewed_proposal_packet_ratio,
                    self.duplicate_reviewed_proposal_packet_ratio,
                    self.conflicting_decision_proposal_packet_ratio,
                )
            ):
                raise ValueError("proposal ratios must be absent without proposals")
            if self.first_proposal_generated_at is not None:
                raise ValueError("proposal generated_at bounds must be absent")
            if self.last_proposal_generated_at is not None:
                raise ValueError("proposal generated_at bounds must be absent")
        else:
            expected_review = _ratio_from_counts(
                self.reviewed_proposal_packet_count,
                self.proposal_packet_count,
            )
            if self.review_coverage_ratio != expected_review:
                raise ValueError("review_coverage_ratio must match reviewed proposals")
            expected_unreviewed = _ratio_from_counts(
                self.unreviewed_proposal_packet_count,
                self.proposal_packet_count,
            )
            if self.unreviewed_proposal_packet_ratio != expected_unreviewed:
                raise ValueError(
                    "unreviewed_proposal_packet_ratio must match unreviewed proposals"
                )
            expected_duplicate = _ratio_from_counts(
                self.duplicate_reviewed_proposal_packet_count,
                self.proposal_packet_count,
            )
            if self.duplicate_reviewed_proposal_packet_ratio != expected_duplicate:
                raise ValueError(
                    "duplicate_reviewed_proposal_packet_ratio must match duplicate proposals"
                )
            expected_conflict = _ratio_from_counts(
                self.conflicting_decision_proposal_packet_count,
                self.proposal_packet_count,
            )
            if self.conflicting_decision_proposal_packet_ratio != expected_conflict:
                raise ValueError(
                    "conflicting_decision_proposal_packet_ratio must match conflicting proposals"
                )
            if (
                self.first_proposal_generated_at is None
                or self.last_proposal_generated_at is None
            ):
                raise ValueError("proposal generated_at bounds are required")
            if self.first_proposal_generated_at > self.last_proposal_generated_at:
                raise ValueError(
                    "first_proposal_generated_at must be before last_proposal_generated_at"
                )
        if self.review_record_count == 0:
            if self.orphan_review_record_ratio is not None:
                raise ValueError("orphan_review_record_ratio must be absent without records")
            if self.first_recorded_at is not None or self.last_recorded_at is not None:
                raise ValueError("recorded_at bounds must be absent without records")
        else:
            expected_orphan = _ratio_from_counts(
                self.orphan_review_record_count,
                self.review_record_count,
            )
            if self.orphan_review_record_ratio != expected_orphan:
                raise ValueError("orphan_review_record_ratio must match orphan records")
            if self.first_recorded_at is None or self.last_recorded_at is None:
                raise ValueError("recorded_at bounds are required with records")
            if self.first_recorded_at > self.last_recorded_at:
                raise ValueError("first_recorded_at must be before last_recorded_at")
        for field_name in (
            "review_coverage_ratio",
            "unreviewed_proposal_packet_ratio",
            "duplicate_reviewed_proposal_packet_ratio",
            "conflicting_decision_proposal_packet_ratio",
            "orphan_review_record_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known proposal review coverage status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                TradeProposalReviewCoverageGateResult,
            ),
        )
        object.__setattr__(
            self,
            "bucket_rows",
            _normalize_typed_tuple(
                "bucket_rows",
                self.bucket_rows,
                TradeProposalReviewCoverageBucketRow,
            ),
        )
        object.__setattr__(
            self,
            "packet_rows",
            _normalize_typed_tuple(
                "packet_rows",
                self.packet_rows,
                TradeProposalReviewCoveragePacketRow,
            ),
        )
        if self.proposal_packet_count == 0 and self.review_record_count == 0:
            if self.bucket_rows != ():
                raise ValueError("bucket_rows must be empty without evidence")
            if self.packet_rows != ():
                raise ValueError("packet_rows must be empty without evidence")
        _validate_packet_rows_match_report(self)
        _validate_bucket_rows_match_report(self)
        if tuple(row.gate_name for row in self.gate_results) != GATE_NAMES:
            raise ValueError("gate_results must contain proposal review coverage gates")
        if self.status != _report_status(self.gate_results, self.proposal_packet_count):
            raise ValueError("status must match proposal review coverage gates")
        if tuple(row.bucket_name for row in self.bucket_rows) != tuple(
            sorted(row.bucket_name for row in self.bucket_rows)
        ):
            raise ValueError("bucket_rows must be sorted by bucket_name")
        if tuple(
            sorted(
                self.packet_rows,
                key=lambda row: (
                    row.coverage_status,
                    row.proposal_packet_id,
                    row.source_proposal_fingerprint or "",
                ),
            )
        ) != self.packet_rows:
            raise ValueError("packet_rows must be sorted")


@dataclass(frozen=True)
class TradeProposalReviewCoverageLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))
        _validate_log_parent(self.path)

    def append(self, report: TradeProposalReviewCoverageReport) -> None:
        if type(report) is not TradeProposalReviewCoverageReport:
            raise ValueError("report must be a TradeProposalReviewCoverageReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_coverage_report(
    proposals: Iterable[TradeProposalPacket],
    records: Iterable[TradeProposalReviewRecord],
    *,
    config: TradeProposalReviewCoverageConfig,
    generated_at: datetime,
) -> TradeProposalReviewCoverageReport:
    if type(config) is not TradeProposalReviewCoverageConfig:
        raise ValueError("config must be a TradeProposalReviewCoverageConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    generated_at = _as_utc(generated_at)
    packet_rows = tuple(sorted(_collect_iterable("proposals", proposals), key=lambda item: (
        item.generated_at,
        item.proposal_packet_id,
    )))
    record_rows = tuple(sorted(_collect_iterable("records", records), key=lambda item: (
        item.recorded_at,
        item.review_record_id,
    )))
    _reject_duplicate_ids(
        "duplicate proposal_packet_id",
        (packet.proposal_packet_id for packet in packet_rows),
    )
    _reject_duplicate_ids(
        "duplicate review_record_id",
        (record.review_record_id for record in record_rows),
    )

    packets_by_id = {packet.proposal_packet_id: packet for packet in packet_rows}
    matched_records: dict[str, list[TradeProposalReviewRecord]] = {
        packet.proposal_packet_id: [] for packet in packet_rows
    }
    orphan_records: dict[tuple[str, str], list[TradeProposalReviewRecord]] = {}

    for record in record_rows:
        packet = packets_by_id.get(record.source_proposal_packet_id)
        if packet is None:
            key = (record.source_proposal_packet_id, record.source_proposal_fingerprint)
            orphan_records.setdefault(key, []).append(record)
            continue
        _validate_record_matches_packet(record, packet)
        matched_records[packet.proposal_packet_id].append(record)

    row_list = _build_packet_rows(packet_rows, matched_records, orphan_records)
    proposal_packet_count = len(packet_rows)
    review_record_count = len(record_rows)
    reviewed_proposal_packet_count = sum(
        1 for packet in packet_rows if matched_records[packet.proposal_packet_id]
    )
    unreviewed_proposal_packet_count = proposal_packet_count - reviewed_proposal_packet_count
    duplicate_reviewed_proposal_packet_count = sum(
        1
        for packet in packet_rows
        if len(matched_records[packet.proposal_packet_id]) > 1
    )
    conflicting_decision_proposal_packet_count = sum(
        1
        for packet in packet_rows
        if _has_conflicting_decisions(matched_records[packet.proposal_packet_id])
    )
    orphan_review_record_count = sum(len(items) for items in orphan_records.values())
    approved_decision_count = sum(1 for record in record_rows if record.decision == "approved")
    rejected_decision_count = sum(1 for record in record_rows if record.decision == "rejected")

    review_coverage_ratio = _optional_ratio_from_counts(
        reviewed_proposal_packet_count,
        proposal_packet_count,
    )
    unreviewed_proposal_packet_ratio = _optional_ratio_from_counts(
        unreviewed_proposal_packet_count,
        proposal_packet_count,
    )
    duplicate_reviewed_proposal_packet_ratio = _optional_ratio_from_counts(
        duplicate_reviewed_proposal_packet_count,
        proposal_packet_count,
    )
    conflicting_decision_proposal_packet_ratio = _optional_ratio_from_counts(
        conflicting_decision_proposal_packet_count,
        proposal_packet_count,
    )
    orphan_review_record_ratio = _optional_ratio_from_counts(
        orphan_review_record_count,
        review_record_count,
    )
    first_proposal_generated_at = packet_rows[0].generated_at if packet_rows else None
    last_proposal_generated_at = packet_rows[-1].generated_at if packet_rows else None
    first_recorded_at = record_rows[0].recorded_at if record_rows else None
    last_recorded_at = record_rows[-1].recorded_at if record_rows else None

    gate_results = _build_gate_results(
        config=config,
        proposal_packet_count=proposal_packet_count,
        review_coverage_ratio=review_coverage_ratio,
        duplicate_reviewed_proposal_packet_count=duplicate_reviewed_proposal_packet_count,
        duplicate_reviewed_proposal_packet_ratio=duplicate_reviewed_proposal_packet_ratio,
        conflicting_decision_proposal_packet_count=conflicting_decision_proposal_packet_count,
        conflicting_decision_proposal_packet_ratio=conflicting_decision_proposal_packet_ratio,
        orphan_review_record_count=orphan_review_record_count,
        orphan_review_record_ratio=orphan_review_record_ratio,
    )
    status = _report_status(gate_results, proposal_packet_count)

    return TradeProposalReviewCoverageReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        proposal_packet_count=proposal_packet_count,
        review_record_count=review_record_count,
        reviewed_proposal_packet_count=reviewed_proposal_packet_count,
        unreviewed_proposal_packet_count=unreviewed_proposal_packet_count,
        duplicate_reviewed_proposal_packet_count=duplicate_reviewed_proposal_packet_count,
        conflicting_decision_proposal_packet_count=conflicting_decision_proposal_packet_count,
        orphan_review_record_count=orphan_review_record_count,
        approved_decision_count=approved_decision_count,
        rejected_decision_count=rejected_decision_count,
        review_coverage_ratio=review_coverage_ratio,
        unreviewed_proposal_packet_ratio=unreviewed_proposal_packet_ratio,
        duplicate_reviewed_proposal_packet_ratio=duplicate_reviewed_proposal_packet_ratio,
        conflicting_decision_proposal_packet_ratio=conflicting_decision_proposal_packet_ratio,
        orphan_review_record_ratio=orphan_review_record_ratio,
        first_proposal_generated_at=first_proposal_generated_at,
        last_proposal_generated_at=last_proposal_generated_at,
        first_recorded_at=first_recorded_at,
        last_recorded_at=last_recorded_at,
        status=status,
        gate_results=gate_results,
        bucket_rows=_build_bucket_rows(
            proposal_packet_count=proposal_packet_count,
            review_record_count=review_record_count,
            unreviewed_proposal_packet_count=unreviewed_proposal_packet_count,
            duplicate_reviewed_proposal_packet_count=duplicate_reviewed_proposal_packet_count,
            conflicting_decision_proposal_packet_count=conflicting_decision_proposal_packet_count,
            orphan_review_record_count=orphan_review_record_count,
            matched_records=matched_records,
            orphan_records=orphan_records,
        ),
        packet_rows=row_list,
    )


def _build_packet_rows(
    packets: tuple[TradeProposalPacket, ...],
    matched_records: dict[str, list[TradeProposalReviewRecord]],
    orphan_records: dict[tuple[str, str], list[TradeProposalReviewRecord]],
) -> tuple[TradeProposalReviewCoveragePacketRow, ...]:
    rows: list[TradeProposalReviewCoveragePacketRow] = []
    for packet in packets:
        records = tuple(matched_records[packet.proposal_packet_id])
        if not records:
            coverage_status = "unreviewed"
        elif _has_conflicting_decisions(records):
            coverage_status = "conflicting"
        elif len(records) > 1:
            coverage_status = "duplicate_reviewed"
        else:
            coverage_status = "reviewed"
        rows.append(
            TradeProposalReviewCoveragePacketRow(
                coverage_status=coverage_status,
                proposal_packet_id=packet.proposal_packet_id,
                source_proposal_fingerprint=_source_proposal_fingerprint(packet),
                first_proposal_generated_at=packet.generated_at,
                last_proposal_generated_at=packet.generated_at,
                first_recorded_at=records[0].recorded_at if records else None,
                last_recorded_at=records[-1].recorded_at if records else None,
                review_record_count=len(records),
                approved_decision_count=sum(
                    1 for record in records if record.decision == "approved"
                ),
                rejected_decision_count=sum(
                    1 for record in records if record.decision == "rejected"
                ),
                market_slug=packet.market_slug,
                strategy_type=packet.strategy_type,
                risk_tags=packet.risk_tags,
                review_record_ids=tuple(sorted(record.review_record_id for record in records)),
            )
        )
    for (source_id, fingerprint), records in orphan_records.items():
        records_tuple = tuple(records)
        first = records_tuple[0]
        rows.append(
            TradeProposalReviewCoveragePacketRow(
                coverage_status="orphan",
                proposal_packet_id=source_id,
                source_proposal_fingerprint=fingerprint,
                first_proposal_generated_at=None,
                last_proposal_generated_at=None,
                first_recorded_at=records_tuple[0].recorded_at,
                last_recorded_at=records_tuple[-1].recorded_at,
                review_record_count=len(records_tuple),
                approved_decision_count=sum(
                    1 for record in records_tuple if record.decision == "approved"
                ),
                rejected_decision_count=sum(
                    1 for record in records_tuple if record.decision == "rejected"
                ),
                market_slug=first.market_slug,
                strategy_type=first.strategy_type,
                risk_tags=first.risk_tags,
                review_record_ids=tuple(
                    sorted(record.review_record_id for record in records_tuple)
                ),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.coverage_status,
                row.proposal_packet_id,
                row.source_proposal_fingerprint or "",
            ),
        )
    )


def _build_bucket_rows(
    *,
    proposal_packet_count: int,
    review_record_count: int,
    unreviewed_proposal_packet_count: int,
    duplicate_reviewed_proposal_packet_count: int,
    conflicting_decision_proposal_packet_count: int,
    orphan_review_record_count: int,
    matched_records: dict[str, list[TradeProposalReviewRecord]],
    orphan_records: dict[tuple[str, str], list[TradeProposalReviewRecord]],
) -> tuple[TradeProposalReviewCoverageBucketRow, ...]:
    if proposal_packet_count == 0 and review_record_count == 0:
        return ()
    reviewed_bucket_proposal_count = sum(
        1 for records in matched_records.values() if len(records) == 1
    )
    reviewed_bucket_record_count = sum(
        len(records) for records in matched_records.values() if len(records) == 1
    )
    duplicate_records = sum(
        len(records) for records in matched_records.values() if len(records) > 1
    )
    conflicting_records = sum(
        len(records)
        for records in matched_records.values()
        if _has_conflicting_decisions(records)
    )
    orphan_records_count = sum(len(records) for records in orphan_records.values())
    rows = (
        TradeProposalReviewCoverageBucketRow(
            bucket_name="conflicting_decision",
            proposal_packet_count=conflicting_decision_proposal_packet_count,
            review_record_count=conflicting_records,
            coverage_ratio=_optional_ratio_from_counts(
                conflicting_decision_proposal_packet_count,
                proposal_packet_count,
            ),
        ),
        TradeProposalReviewCoverageBucketRow(
            bucket_name="duplicate_reviewed",
            proposal_packet_count=duplicate_reviewed_proposal_packet_count,
            review_record_count=duplicate_records,
            coverage_ratio=_optional_ratio_from_counts(
                duplicate_reviewed_proposal_packet_count,
                proposal_packet_count,
            ),
        ),
        TradeProposalReviewCoverageBucketRow(
            bucket_name="orphan_review_record",
            proposal_packet_count=0,
            review_record_count=orphan_records_count,
            coverage_ratio=_optional_ratio_from_counts(
                orphan_review_record_count,
                review_record_count,
            ),
        ),
        TradeProposalReviewCoverageBucketRow(
            bucket_name="reviewed",
            proposal_packet_count=reviewed_bucket_proposal_count,
            review_record_count=reviewed_bucket_record_count,
            coverage_ratio=_optional_ratio_from_counts(
                reviewed_bucket_proposal_count,
                proposal_packet_count,
            ),
        ),
        TradeProposalReviewCoverageBucketRow(
            bucket_name="unreviewed",
            proposal_packet_count=unreviewed_proposal_packet_count,
            review_record_count=0,
            coverage_ratio=_optional_ratio_from_counts(
                unreviewed_proposal_packet_count,
                proposal_packet_count,
            ),
        ),
    )
    return tuple(sorted(rows, key=lambda row: row.bucket_name))


def _build_gate_results(
    *,
    config: TradeProposalReviewCoverageConfig,
    proposal_packet_count: int,
    review_coverage_ratio: Decimal | None,
    duplicate_reviewed_proposal_packet_count: int,
    duplicate_reviewed_proposal_packet_ratio: Decimal | None,
    conflicting_decision_proposal_packet_count: int,
    conflicting_decision_proposal_packet_ratio: Decimal | None,
    orphan_review_record_count: int,
    orphan_review_record_ratio: Decimal | None,
) -> tuple[TradeProposalReviewCoverageGateResult, ...]:
    data_integrity_failed = (
        orphan_review_record_count > config.max_orphan_review_record_count
        or (
            orphan_review_record_ratio is not None
            and orphan_review_record_ratio > config.max_orphan_review_record_ratio
        )
    )
    proposal_sample_failed = proposal_packet_count < config.min_proposal_packet_count
    review_coverage_failed = (
        proposal_packet_count == 0
        or review_coverage_ratio is None
        or review_coverage_ratio < config.min_review_coverage_ratio
    )
    duplicate_failed = (
        duplicate_reviewed_proposal_packet_count
        > config.max_duplicate_reviewed_proposal_packet_count
        or (
            duplicate_reviewed_proposal_packet_ratio is not None
            and duplicate_reviewed_proposal_packet_ratio
            > config.max_duplicate_reviewed_proposal_packet_ratio
        )
    )
    conflict_failed = (
        conflicting_decision_proposal_packet_count
        > config.max_conflicting_decision_proposal_packet_count
        or (
            conflicting_decision_proposal_packet_ratio is not None
            and conflicting_decision_proposal_packet_ratio
            > config.max_conflicting_decision_proposal_packet_ratio
        )
    )
    return (
        TradeProposalReviewCoverageGateResult(
            gate_name="data_integrity",
            status="fail" if data_integrity_failed else "pass",
            message="Orphan review records are within configured coverage limits."
            if not data_integrity_failed
            else "Orphan review records exceed configured coverage limits.",
            observed_value=orphan_review_record_ratio,
            threshold=config.max_orphan_review_record_ratio,
        ),
        TradeProposalReviewCoverageGateResult(
            gate_name="proposal_sample",
            status="fail" if proposal_sample_failed else "pass",
            message="Proposal packet sample meets the configured minimum."
            if not proposal_sample_failed
            else "Proposal packet sample is below the configured minimum.",
            observed_value=proposal_packet_count,
            threshold=config.min_proposal_packet_count,
        ),
        TradeProposalReviewCoverageGateResult(
            gate_name="review_coverage",
            status="fail" if review_coverage_failed else "pass",
            message="Proposal packet review coverage meets the configured minimum."
            if not review_coverage_failed
            else "Proposal packet review coverage is below the configured minimum.",
            observed_value=review_coverage_ratio,
            threshold=config.min_review_coverage_ratio,
        ),
        TradeProposalReviewCoverageGateResult(
            gate_name="duplicate_review_volume",
            status="fail" if duplicate_failed else "pass",
            message="Duplicate review volume is within configured limits."
            if not duplicate_failed
            else "Duplicate review volume exceeds configured limits.",
            observed_value=duplicate_reviewed_proposal_packet_ratio,
            threshold=config.max_duplicate_reviewed_proposal_packet_ratio,
        ),
        TradeProposalReviewCoverageGateResult(
            gate_name="decision_consistency",
            status="fail" if conflict_failed else "pass",
            message="Conflicting review decisions are within configured limits."
            if not conflict_failed
            else "Conflicting review decisions exceed configured limits.",
            observed_value=conflicting_decision_proposal_packet_ratio,
            threshold=config.max_conflicting_decision_proposal_packet_ratio,
        ),
    )


def _report_status(
    gate_results: tuple[TradeProposalReviewCoverageGateResult, ...],
    proposal_packet_count: int,
) -> str:
    gate_statuses = {row.gate_name: row.status for row in gate_results}
    if proposal_packet_count == 0:
        return "incomplete_proposal_sample"
    if gate_statuses.get("review_coverage") == "fail":
        return "incomplete_review_coverage"
    if any(row.status == "fail" for row in gate_results):
        return "inconsistent_review_coverage"
    return "proposal_review_coverage_ready"


def _validate_packet_rows_match_report(
    report: TradeProposalReviewCoverageReport,
) -> None:
    if report.proposal_packet_count == 0 and report.review_record_count == 0:
        return
    supplied_rows = tuple(
        row for row in report.packet_rows if row.coverage_status != "orphan"
    )
    orphan_rows = tuple(
        row for row in report.packet_rows if row.coverage_status == "orphan"
    )
    supplied_ids = tuple(row.proposal_packet_id for row in supplied_rows)
    if len(set(supplied_ids)) != len(supplied_ids):
        raise ValueError("packet_rows proposal_packet_id values must be unique")
    orphan_keys = tuple(
        (row.proposal_packet_id, row.source_proposal_fingerprint)
        for row in orphan_rows
    )
    if len(set(orphan_keys)) != len(orphan_keys):
        raise ValueError("orphan packet_rows must be grouped by source proposal")
    supplied_id_set = set(supplied_ids)
    if any(row.proposal_packet_id in supplied_id_set for row in orphan_rows):
        raise ValueError("orphan packet_rows must not duplicate supplied proposals")
    review_record_ids = tuple(
        review_record_id
        for row in report.packet_rows
        for review_record_id in row.review_record_ids
    )
    if len(review_record_ids) != report.review_record_count:
        raise ValueError("packet_rows review_record_ids must match review_record_count")
    if len(set(review_record_ids)) != len(review_record_ids):
        raise ValueError("packet_rows review_record_ids must be unique")
    if len(supplied_rows) != report.proposal_packet_count:
        raise ValueError("packet_rows must match proposal_packet_count")
    if sum(row.review_record_count for row in report.packet_rows) != report.review_record_count:
        raise ValueError("packet_rows must match review_record_count")
    if sum(row.approved_decision_count for row in report.packet_rows) != report.approved_decision_count:
        raise ValueError("packet_rows must match approved_decision_count")
    if sum(row.rejected_decision_count for row in report.packet_rows) != report.rejected_decision_count:
        raise ValueError("packet_rows must match rejected_decision_count")
    if sum(1 for row in supplied_rows if row.review_record_count > 0) != report.reviewed_proposal_packet_count:
        raise ValueError("packet_rows must match reviewed_proposal_packet_count")
    if sum(1 for row in supplied_rows if row.coverage_status == "unreviewed") != report.unreviewed_proposal_packet_count:
        raise ValueError("packet_rows must match unreviewed_proposal_packet_count")
    if sum(1 for row in supplied_rows if row.review_record_count > 1) != report.duplicate_reviewed_proposal_packet_count:
        raise ValueError("packet_rows must match duplicate_reviewed_proposal_packet_count")
    if sum(1 for row in supplied_rows if row.coverage_status == "conflicting") != report.conflicting_decision_proposal_packet_count:
        raise ValueError("packet_rows must match conflicting_decision_proposal_packet_count")
    if sum(row.review_record_count for row in orphan_rows) != report.orphan_review_record_count:
        raise ValueError("packet_rows must match orphan_review_record_count")
    for row in supplied_rows:
        if row.coverage_status == "reviewed" and row.review_record_count != 1:
            raise ValueError("packet_rows reviewed rows must contain one record")
        if row.coverage_status == "duplicate_reviewed":
            if row.review_record_count <= 1:
                raise ValueError("packet_rows duplicate rows must contain multiple records")
            if row.approved_decision_count and row.rejected_decision_count:
                raise ValueError("packet_rows duplicate rows must not contain conflicts")
        if row.coverage_status == "conflicting":
            if not row.approved_decision_count or not row.rejected_decision_count:
                raise ValueError("packet_rows conflicting rows must contain both decisions")
    proposal_dates = tuple(
        date
        for row in supplied_rows
        for date in (row.first_proposal_generated_at, row.last_proposal_generated_at)
        if date is not None
    )
    if proposal_dates:
        if min(proposal_dates) != report.first_proposal_generated_at:
            raise ValueError("packet_rows must match first_proposal_generated_at")
        if max(proposal_dates) != report.last_proposal_generated_at:
            raise ValueError("packet_rows must match last_proposal_generated_at")
    recorded_dates = tuple(
        date
        for row in report.packet_rows
        for date in (row.first_recorded_at, row.last_recorded_at)
        if date is not None
    )
    if recorded_dates:
        if min(recorded_dates) != report.first_recorded_at:
            raise ValueError("packet_rows must match first_recorded_at")
        if max(recorded_dates) != report.last_recorded_at:
            raise ValueError("packet_rows must match last_recorded_at")


def _validate_bucket_rows_match_report(
    report: TradeProposalReviewCoverageReport,
) -> None:
    if report.proposal_packet_count == 0 and report.review_record_count == 0:
        return
    if tuple(row.bucket_name for row in report.bucket_rows) != BUCKET_NAMES:
        raise ValueError("bucket_rows must contain proposal review coverage buckets")
    supplied_rows = tuple(
        row for row in report.packet_rows if row.coverage_status != "orphan"
    )
    orphan_rows = tuple(
        row for row in report.packet_rows if row.coverage_status == "orphan"
    )
    expected = {
        "conflicting_decision": (
            report.conflicting_decision_proposal_packet_count,
            sum(row.review_record_count for row in supplied_rows if row.coverage_status == "conflicting"),
            report.conflicting_decision_proposal_packet_ratio,
        ),
        "duplicate_reviewed": (
            report.duplicate_reviewed_proposal_packet_count,
            sum(row.review_record_count for row in supplied_rows if row.review_record_count > 1),
            report.duplicate_reviewed_proposal_packet_ratio,
        ),
        "orphan_review_record": (
            0,
            sum(row.review_record_count for row in orphan_rows),
            report.orphan_review_record_ratio,
        ),
        "reviewed": (
            sum(1 for row in supplied_rows if row.coverage_status == "reviewed"),
            sum(
                row.review_record_count
                for row in supplied_rows
                if row.coverage_status == "reviewed"
            ),
            _optional_ratio_from_counts(
                sum(1 for row in supplied_rows if row.coverage_status == "reviewed"),
                report.proposal_packet_count,
            ),
        ),
        "unreviewed": (
            report.unreviewed_proposal_packet_count,
            0,
            report.unreviewed_proposal_packet_ratio,
        ),
    }
    for row in report.bucket_rows:
        expected_proposals, expected_records, expected_ratio = expected[row.bucket_name]
        if row.proposal_packet_count != expected_proposals:
            raise ValueError("bucket_rows proposal_packet_count must match report")
        if row.review_record_count != expected_records:
            raise ValueError("bucket_rows review_record_count must match report")
        if row.coverage_ratio != expected_ratio:
            raise ValueError("bucket_rows coverage_ratio must match report")


def _collect_iterable(
    field_name: str,
    values: Iterable[Any],
) -> tuple[TradeProposalPacket, ...] | tuple[TradeProposalReviewRecord, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of review artifacts")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of review artifacts") from exc
    if field_name == "proposals":
        return tuple(_clone_proposal_packet(item) for item in items)
    return tuple(_clone_review_record(item) for item in items)


def _clone_proposal_packet(packet: Any) -> TradeProposalPacket:
    if type(packet) is not TradeProposalPacket:
        raise ValueError("proposal must be a TradeProposalPacket")
    return TradeProposalPacket(
        **{field.name: getattr(packet, field.name) for field in fields(TradeProposalPacket)}
    )


def _clone_review_record(record: Any) -> TradeProposalReviewRecord:
    if type(record) is not TradeProposalReviewRecord:
        raise ValueError("record must be a TradeProposalReviewRecord")
    return TradeProposalReviewRecord(
        **{field.name: getattr(record, field.name) for field in fields(TradeProposalReviewRecord)}
    )


def _reject_duplicate_ids(message: str, values: Iterable[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(message)
        seen.add(value)


def _validate_record_matches_packet(
    record: TradeProposalReviewRecord,
    packet: TradeProposalPacket,
) -> None:
    source_fields = _source_fields_from_proposal(packet)
    for field_name, expected_value in source_fields.items():
        if getattr(record, field_name) != expected_value:
            raise ValueError(
                "source_proposal_fingerprint source snapshot must match supplied proposal"
            )
    expected_fingerprint = _source_proposal_fingerprint(packet)
    if record.source_proposal_fingerprint != expected_fingerprint:
        raise ValueError("source_proposal_fingerprint must match supplied proposal")


def _source_fields_from_proposal(packet: TradeProposalPacket) -> dict[str, Any]:
    return {
        "source_proposal_packet_id": packet.proposal_packet_id,
        "source_proposal_generated_at": packet.generated_at,
        "source_proposal_config_version": packet.proposal_config_version,
        "source_proposal_boundary_statement": packet.boundary_statement,
        "source_queue_boundary_statement": packet.source_boundary_statement,
        "source_proposal_only": packet.proposal_only,
        "source_human_approval_required": packet.human_approval_required,
        "source_queue_item_id": packet.source_queue_item_id,
        "source_queue_rank": packet.source_queue_rank,
        "source_manual_review_status": packet.source_manual_review_status,
        "source_packet_id": packet.source_packet_id,
        "source_paper_only": packet.source_paper_only,
        "condition_id": packet.condition_id,
        "token_id": packet.token_id,
        "market_slug": packet.market_slug,
        "market_url": packet.market_url,
        "question": packet.question,
        "outcome_name": packet.outcome_name,
        "strategy_type": packet.strategy_type,
        "side": packet.side,
        "intended_order_type": packet.intended_order_type,
        "executable_price_assumption": packet.executable_price_assumption,
        "maximum_size": packet.maximum_size,
        "source_max_executable_size": packet.source_max_executable_size,
        "cost_adjusted_edge": packet.cost_adjusted_edge,
        "theoretical_edge": packet.theoretical_edge,
        "fair_value_estimate": packet.fair_value_estimate,
        "model_probability": packet.model_probability,
        "confidence": packet.confidence,
        "source_score": packet.source_score,
        "market_score_total": packet.market_score_total,
        "exposure_after_trade": packet.exposure_after_trade,
        "exit_rule": packet.exit_rule,
        "thesis": packet.thesis,
        "invalidating_conditions": packet.invalidating_conditions,
        "rule_text_hash": packet.rule_text_hash,
        "resolution_source": packet.resolution_source,
        "risk_tags": packet.risk_tags,
        "reason_trade_could_be_wrong": packet.reason_trade_could_be_wrong,
        "readiness_summary": packet.readiness_summary,
        "risk_summary": packet.risk_summary,
        "evidence_summary": packet.evidence_summary,
        "why_in_queue": packet.why_in_queue,
        "primary_reason_code": packet.primary_reason_code,
        "supporting_reason_codes": packet.supporting_reason_codes,
        "review_focus": packet.review_focus,
        "evidence_scope": packet.evidence_scope,
        "history_status": packet.history_status,
        "forecast_status": packet.forecast_status,
        "history_gate_pass_count": packet.history_gate_pass_count,
        "forecast_gate_pass_count": packet.forecast_gate_pass_count,
        "history_gate_fail_count": packet.history_gate_fail_count,
        "forecast_gate_fail_count": packet.forecast_gate_fail_count,
        "risk_gate_passed": packet.risk_gate_passed,
        "hard_block_count": packet.hard_block_count,
        "blocking_reason_codes": packet.blocking_reason_codes,
    }


def _source_proposal_fingerprint(packet: TradeProposalPacket) -> str:
    values = _source_fields_from_proposal(packet)
    raw = json.dumps(
        _json_ready(
            {field_name: values[field_name] for field_name in SOURCE_FINGERPRINT_FIELDS}
        ),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"source-proposal-{digest}"


def _has_conflicting_decisions(records: Iterable[TradeProposalReviewRecord]) -> bool:
    return len({record.decision for record in records}) > 1


def _optional_ratio_from_counts(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _ratio_from_counts(numerator, denominator)


def _ratio_from_counts(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_tree(
    report: TradeProposalReviewCoverageReport,
) -> TradeProposalReviewCoverageReport:
    gate_results = tuple(
        TradeProposalReviewCoverageGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in report.gate_results
    )
    bucket_rows = tuple(
        TradeProposalReviewCoverageBucketRow(
            bucket_name=row.bucket_name,
            proposal_packet_count=row.proposal_packet_count,
            review_record_count=row.review_record_count,
            coverage_ratio=row.coverage_ratio,
        )
        for row in report.bucket_rows
    )
    packet_rows = tuple(
        TradeProposalReviewCoveragePacketRow(
            coverage_status=row.coverage_status,
            proposal_packet_id=row.proposal_packet_id,
            source_proposal_fingerprint=row.source_proposal_fingerprint,
            first_proposal_generated_at=row.first_proposal_generated_at,
            last_proposal_generated_at=row.last_proposal_generated_at,
            first_recorded_at=row.first_recorded_at,
            last_recorded_at=row.last_recorded_at,
            review_record_count=row.review_record_count,
            approved_decision_count=row.approved_decision_count,
            rejected_decision_count=row.rejected_decision_count,
            market_slug=row.market_slug,
            strategy_type=row.strategy_type,
            risk_tags=row.risk_tags,
            review_record_ids=row.review_record_ids,
        )
        for row in report.packet_rows
    )
    return TradeProposalReviewCoverageReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        proposal_packet_count=report.proposal_packet_count,
        review_record_count=report.review_record_count,
        reviewed_proposal_packet_count=report.reviewed_proposal_packet_count,
        unreviewed_proposal_packet_count=report.unreviewed_proposal_packet_count,
        duplicate_reviewed_proposal_packet_count=(
            report.duplicate_reviewed_proposal_packet_count
        ),
        conflicting_decision_proposal_packet_count=(
            report.conflicting_decision_proposal_packet_count
        ),
        orphan_review_record_count=report.orphan_review_record_count,
        approved_decision_count=report.approved_decision_count,
        rejected_decision_count=report.rejected_decision_count,
        review_coverage_ratio=report.review_coverage_ratio,
        unreviewed_proposal_packet_ratio=report.unreviewed_proposal_packet_ratio,
        duplicate_reviewed_proposal_packet_ratio=(
            report.duplicate_reviewed_proposal_packet_ratio
        ),
        conflicting_decision_proposal_packet_ratio=(
            report.conflicting_decision_proposal_packet_ratio
        ),
        orphan_review_record_ratio=report.orphan_review_record_ratio,
        first_proposal_generated_at=report.first_proposal_generated_at,
        last_proposal_generated_at=report.last_proposal_generated_at,
        first_recorded_at=report.first_recorded_at,
        last_recorded_at=report.last_recorded_at,
        status=report.status,
        gate_results=gate_results,
        bucket_rows=bucket_rows,
        packet_rows=packet_rows,
    )


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_typed_tuple(
    field_name: str,
    values: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for value in normalized:
        if type(value) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__}")
    return normalized


def _normalize_string_tuple(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for value in normalized:
        _require_canonical_string(field_name, value)
    return normalized


def _normalize_sorted_string_tuple(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    normalized = _normalize_string_tuple(field_name, values)
    return tuple(sorted(normalized))


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    lower = value.lower()
    for fragment in (
        "report-only",
        "proposal-review coverage",
        "not",
        "approval workflow",
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
    ):
        if fragment not in lower:
            raise ValueError("boundary_statement is missing required coverage boundary text")


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_probability_decimal(field_name, value)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < RATIO_QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed four decimal places")


def _require_gate_value(
    field_name: str,
    value: Decimal | int | str | None,
) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, Decimal):
        _require_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            converted[key] = _json_ready(item)
        return converted
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(path: Path | str) -> Path:
    if isinstance(path, str):
        if not path.strip():
            raise ValueError("path must not be blank")
        normalized = Path(path)
    elif isinstance(path, Path):
        normalized = path
    else:
        raise ValueError("path must be a Path or string")
    if normalized.exists() and normalized.is_dir():
        raise ValueError("path must not be an existing directory")
    return normalized


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
