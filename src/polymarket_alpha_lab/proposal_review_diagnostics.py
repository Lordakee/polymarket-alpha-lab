"""Report-only proposal-review diagnostics for Level 2."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_review import TradeProposalReviewRecord


__all__ = (
    "TradeProposalReviewDiagnosticBucketRow",
    "TradeProposalReviewDiagnosticConfig",
    "TradeProposalReviewDiagnosticLog",
    "TradeProposalReviewDiagnosticReasonRow",
    "TradeProposalReviewDiagnosticReport",
    "TradeProposalReviewDiagnosticSourceRow",
    "build_trade_proposal_review_diagnostic_report",
)


DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review diagnostic artifact using rejected "
    "human-review decisions as a false-positive proxy, not realized false-positive "
    "confirmation, approval workflow, trade instruction, order instruction, broker "
    "request, order request, account action, account authentication, private-key "
    "handling, wallet signature, live-execution signal, credential workflow, "
    "manual execution import, strategy-promotion signal, settlement review, "
    "reconciliation process, or automatic order-placement authorization."
)
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")
BUCKET_TYPES = ("market_slug", "strategy_type", "risk_tag", "review_focus")
REPORT_STATUSES = (
    "incomplete_review_data",
    "insufficient_review_sample",
    "high_rejection_proxy",
    "diagnostics_ready",
)


@dataclass(frozen=True)
class TradeProposalReviewDiagnosticConfig:
    config_version: str
    min_review_record_count: int = 1
    max_rejected_decision_ratio: Decimal = Decimal("0.5000")
    max_rejected_source_proposal_ratio: Decimal = Decimal("0.5000")
    max_reason_code_rejected_decision_share: Decimal = Decimal("0.7500")
    include_market_slug_buckets: bool = True
    include_strategy_type_buckets: bool = True
    include_risk_tag_buckets: bool = True
    include_review_focus_buckets: bool = True
    max_source_rows: int = 20
    boundary_statement: str = DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_review_record_count",
            self.min_review_record_count,
        )
        _require_probability_decimal(
            "max_rejected_decision_ratio",
            self.max_rejected_decision_ratio,
        )
        _require_probability_decimal(
            "max_rejected_source_proposal_ratio",
            self.max_rejected_source_proposal_ratio,
        )
        _require_probability_decimal(
            "max_reason_code_rejected_decision_share",
            self.max_reason_code_rejected_decision_share,
        )
        _require_bool("include_market_slug_buckets", self.include_market_slug_buckets)
        _require_bool(
            "include_strategy_type_buckets",
            self.include_strategy_type_buckets,
        )
        _require_bool("include_risk_tag_buckets", self.include_risk_tag_buckets)
        _require_bool("include_review_focus_buckets", self.include_review_focus_buckets)
        _require_nonnegative_int("max_source_rows", self.max_source_rows)
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalReviewDiagnosticReasonRow:
    reason_code: str
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_share: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int(
            "rejected_decision_count",
            self.rejected_decision_count,
        )
        _require_positive_int(
            "rejected_source_proposal_count",
            self.rejected_source_proposal_count,
        )
        if self.rejected_source_proposal_count > self.rejected_decision_count:
            raise ValueError(
                "rejected_source_proposal_count must not exceed rejected_decision_count"
            )
        _require_probability_decimal(
            "rejected_decision_share",
            self.rejected_decision_share,
        )


@dataclass(frozen=True)
class TradeProposalReviewDiagnosticBucketRow:
    bucket_type: str
    bucket_value: str
    review_record_count: int
    unique_source_proposal_count: int
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_ratio: Decimal

    def __post_init__(self) -> None:
        if self.bucket_type not in BUCKET_TYPES:
            raise ValueError(
                "bucket_type must be market_slug, strategy_type, risk_tag, or review_focus"
            )
        _require_canonical_string("bucket_value", self.bucket_value)
        _require_positive_int("review_record_count", self.review_record_count)
        _require_positive_int(
            "unique_source_proposal_count",
            self.unique_source_proposal_count,
        )
        _require_nonnegative_int(
            "rejected_decision_count",
            self.rejected_decision_count,
        )
        _require_nonnegative_int(
            "rejected_source_proposal_count",
            self.rejected_source_proposal_count,
        )
        if self.unique_source_proposal_count > self.review_record_count:
            raise ValueError(
                "unique_source_proposal_count must not exceed review_record_count"
            )
        if self.rejected_decision_count > self.review_record_count:
            raise ValueError(
                "rejected_decision_count must not exceed review_record_count"
            )
        if self.rejected_source_proposal_count > self.rejected_decision_count:
            raise ValueError(
                "rejected_source_proposal_count must not exceed rejected_decision_count"
            )
        if self.rejected_source_proposal_count > self.unique_source_proposal_count:
            raise ValueError(
                "rejected_source_proposal_count must not exceed unique_source_proposal_count"
            )
        expected_ratio = _ratio_from_counts(
            self.rejected_decision_count,
            self.review_record_count,
        )
        if self.rejected_decision_ratio != expected_ratio:
            raise ValueError(
                "rejected_decision_ratio must match rejected decision count"
            )
        _require_probability_decimal(
            "rejected_decision_ratio",
            self.rejected_decision_ratio,
        )


@dataclass(frozen=True)
class TradeProposalReviewDiagnosticSourceRow:
    source_proposal_packet_id: str
    source_proposal_fingerprint: str
    first_recorded_at: datetime
    last_recorded_at: datetime
    review_record_count: int
    rejected_decision_count: int
    reason_codes: tuple[str, ...]
    market_slug: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    review_focus: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "first_recorded_at", _as_utc(self.first_recorded_at))
        object.__setattr__(self, "last_recorded_at", _as_utc(self.last_recorded_at))
        _require_canonical_string(
            "source_proposal_packet_id",
            self.source_proposal_packet_id,
        )
        _require_canonical_string(
            "source_proposal_fingerprint",
            self.source_proposal_fingerprint,
        )
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("strategy_type", self.strategy_type)
        if self.first_recorded_at > self.last_recorded_at:
            raise ValueError("first_recorded_at must be before last_recorded_at")
        _require_positive_int("review_record_count", self.review_record_count)
        _require_positive_int("rejected_decision_count", self.rejected_decision_count)
        if self.rejected_decision_count > self.review_record_count:
            raise ValueError(
                "rejected_decision_count must not exceed review_record_count"
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_sorted_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "risk_tags",
            _normalize_sorted_string_tuple("risk_tags", self.risk_tags),
        )
        object.__setattr__(
            self,
            "review_focus",
            _normalize_sorted_string_tuple("review_focus", self.review_focus),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes are required")
        if not self.risk_tags:
            raise ValueError("risk_tags are required")
        if not self.review_focus:
            raise ValueError("review_focus is required")


@dataclass(frozen=True)
class TradeProposalReviewDiagnosticReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    review_record_count: int
    unique_source_proposal_count: int
    duplicate_source_proposal_review_count: int
    approved_decision_count: int
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_ratio: Decimal | None
    rejected_source_proposal_ratio: Decimal | None
    max_reason_code_rejected_decision_share: Decimal | None
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    status: str
    reason_rows: tuple[TradeProposalReviewDiagnosticReasonRow, ...]
    bucket_rows: tuple[TradeProposalReviewDiagnosticBucketRow, ...]
    source_rows: tuple[TradeProposalReviewDiagnosticSourceRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.first_recorded_at is not None:
            object.__setattr__(
                self,
                "first_recorded_at",
                _as_utc(self.first_recorded_at),
            )
        if self.last_recorded_at is not None:
            object.__setattr__(
                self,
                "last_recorded_at",
                _as_utc(self.last_recorded_at),
            )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "review_record_count",
            "unique_source_proposal_count",
            "duplicate_source_proposal_review_count",
            "approved_decision_count",
            "rejected_decision_count",
            "rejected_source_proposal_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.review_record_count != (
            self.approved_decision_count + self.rejected_decision_count
        ):
            raise ValueError(
                "review_record_count must equal approved and rejected decision counts"
            )
        if self.unique_source_proposal_count > self.review_record_count:
            raise ValueError(
                "unique_source_proposal_count must not exceed review_record_count"
            )
        if self.duplicate_source_proposal_review_count != (
            self.review_record_count - self.unique_source_proposal_count
        ):
            raise ValueError(
                "duplicate_source_proposal_review_count must equal review count minus unique source count"
            )
        if self.rejected_source_proposal_count > self.unique_source_proposal_count:
            raise ValueError(
                "rejected_source_proposal_count must not exceed unique_source_proposal_count"
            )
        if self.rejected_source_proposal_count > self.rejected_decision_count:
            raise ValueError(
                "rejected_source_proposal_count must not exceed rejected_decision_count"
            )
        object.__setattr__(
            self,
            "reason_rows",
            _normalize_typed_tuple(
                "reason_rows",
                self.reason_rows,
                TradeProposalReviewDiagnosticReasonRow,
            ),
        )
        object.__setattr__(
            self,
            "bucket_rows",
            _normalize_typed_tuple(
                "bucket_rows",
                self.bucket_rows,
                TradeProposalReviewDiagnosticBucketRow,
            ),
        )
        object.__setattr__(
            self,
            "source_rows",
            _normalize_typed_tuple(
                "source_rows",
                self.source_rows,
                TradeProposalReviewDiagnosticSourceRow,
            ),
        )
        if self.review_record_count == 0:
            if self.first_recorded_at is not None or self.last_recorded_at is not None:
                raise ValueError("recorded_at bounds must be absent without records")
            if any(
                value is not None
                for value in (
                    self.rejected_decision_ratio,
                    self.rejected_source_proposal_ratio,
                    self.max_reason_code_rejected_decision_share,
                )
            ):
                raise ValueError("diagnostic ratios must be absent without records")
            if self.reason_rows != ():
                raise ValueError("reason_rows must be empty without records")
            if self.bucket_rows != ():
                raise ValueError("bucket_rows must be empty without records")
            if self.source_rows != ():
                raise ValueError("source_rows must be empty without records")
        else:
            if self.first_recorded_at is None or self.last_recorded_at is None:
                raise ValueError("recorded_at bounds are required with records")
            if self.first_recorded_at > self.last_recorded_at:
                raise ValueError("first_recorded_at must be before last_recorded_at")
            expected_decision_ratio = _ratio_from_counts(
                self.rejected_decision_count,
                self.review_record_count,
            )
            if self.rejected_decision_ratio != expected_decision_ratio:
                raise ValueError(
                    "rejected_decision_ratio must match rejected decision count"
                )
        if self.unique_source_proposal_count == 0:
            if self.rejected_source_proposal_ratio is not None:
                raise ValueError(
                    "rejected_source_proposal_ratio must be absent without source proposals"
                )
        else:
            expected_source_ratio = _ratio_from_counts(
                self.rejected_source_proposal_count,
                self.unique_source_proposal_count,
            )
            if self.rejected_source_proposal_ratio != expected_source_ratio:
                raise ValueError(
                    "rejected_source_proposal_ratio must match rejected source count"
                )
        if self.rejected_decision_count == 0:
            if self.reason_rows != ():
                raise ValueError("reason_rows must be empty without rejected decisions")
            if self.source_rows != ():
                raise ValueError("source_rows must be empty without rejected decisions")
            if self.max_reason_code_rejected_decision_share is not None:
                raise ValueError(
                    "max_reason_code_rejected_decision_share must be absent without rejected decisions"
                )
        else:
            if self.reason_rows == ():
                raise ValueError("reason_rows are required with rejected decisions")
            for row in self.reason_rows:
                if row.rejected_decision_count > self.rejected_decision_count:
                    raise ValueError(
                        "reason_rows rejected_decision_count must not exceed rejected_decision_count"
                    )
                expected_row_share = _ratio_from_counts(
                    row.rejected_decision_count,
                    self.rejected_decision_count,
                )
                if row.rejected_decision_share != expected_row_share:
                    raise ValueError(
                        "rejected_decision_share must match reason row count"
                    )
            expected_reason_share = _ratio_from_counts(
                max(row.rejected_decision_count for row in self.reason_rows),
                self.rejected_decision_count,
            )
            if self.max_reason_code_rejected_decision_share != expected_reason_share:
                raise ValueError(
                    "max_reason_code_rejected_decision_share must match reason row counts"
                )
        for field_name in (
            "rejected_decision_ratio",
            "rejected_source_proposal_ratio",
            "max_reason_code_rejected_decision_share",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known proposal review diagnostic status")
        if tuple(sorted(self.reason_rows, key=lambda item: item.reason_code)) != self.reason_rows:
            raise ValueError("reason_rows must be sorted by reason_code")
        reason_codes = tuple(row.reason_code for row in self.reason_rows)
        if len(set(reason_codes)) != len(reason_codes):
            raise ValueError("reason_rows must not contain duplicate reason_code values")
        if tuple(
            sorted(
                self.bucket_rows,
                key=lambda item: (item.bucket_type, item.bucket_value),
            )
        ) != self.bucket_rows:
            raise ValueError("bucket_rows must be sorted by bucket_type and value")
        bucket_keys = tuple(
            (row.bucket_type, row.bucket_value) for row in self.bucket_rows
        )
        if len(set(bucket_keys)) != len(bucket_keys):
            raise ValueError("bucket_rows must not contain duplicate bucket keys")
        if tuple(
            sorted(
                self.source_rows,
                key=lambda item: (
                    -item.rejected_decision_count,
                    -item.review_record_count,
                    item.source_proposal_packet_id,
                    item.source_proposal_fingerprint,
                ),
            )
        ) != self.source_rows:
            raise ValueError("source_rows must be sorted by rejected counts and source identifiers")
        source_keys = tuple(
            (row.source_proposal_packet_id, row.source_proposal_fingerprint)
            for row in self.source_rows
        )
        if len(set(source_keys)) != len(source_keys):
            raise ValueError("source_rows must not contain duplicate source keys")


@dataclass(frozen=True)
class TradeProposalReviewDiagnosticLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalReviewDiagnosticReport) -> None:
        if type(report) is not TradeProposalReviewDiagnosticReport:
            raise ValueError("report must be a TradeProposalReviewDiagnosticReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_diagnostic_report(
    records: Iterable[TradeProposalReviewRecord],
    *,
    config: TradeProposalReviewDiagnosticConfig,
    generated_at: datetime,
) -> TradeProposalReviewDiagnosticReport:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable of TradeProposalReviewRecord values")
    if type(config) is not TradeProposalReviewDiagnosticConfig:
        raise ValueError("config must be a TradeProposalReviewDiagnosticConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    try:
        record_items = tuple(records)
    except TypeError as exc:
        raise ValueError(
            "records must be an iterable of TradeProposalReviewRecord values"
        ) from exc
    validated_records = tuple(_clone_review_record(record) for record in record_items)
    sorted_records = tuple(
        sorted(
            validated_records,
            key=lambda item: (_as_utc(item.recorded_at), item.review_record_id),
        )
    )
    seen_review_ids: set[str] = set()
    for record in sorted_records:
        if record.review_record_id in seen_review_ids:
            raise ValueError("duplicate review_record_id values are not allowed")
        seen_review_ids.add(record.review_record_id)

    review_record_count = len(sorted_records)
    source_ids = {record.source_proposal_packet_id for record in sorted_records}
    unique_source_proposal_count = len(source_ids)
    approved_decision_count = sum(
        1 for record in sorted_records if record.decision == "approved"
    )
    rejected_decision_count = sum(
        1 for record in sorted_records if record.decision == "rejected"
    )
    rejected_source_proposal_count = len(
        {
            record.source_proposal_packet_id
            for record in sorted_records
            if record.decision == "rejected"
        }
    )
    reason_rows = _build_reason_rows(sorted_records)
    max_reason_share = (
        _ratio_from_counts(
            max(row.rejected_decision_count for row in reason_rows),
            rejected_decision_count,
        )
        if rejected_decision_count > 0 and reason_rows
        else None
    )
    rejected_decision_ratio = _optional_ratio_from_counts(
        rejected_decision_count,
        review_record_count,
    )
    rejected_source_proposal_ratio = _optional_ratio_from_counts(
        rejected_source_proposal_count,
        unique_source_proposal_count,
    )
    status = _diagnostic_status(
        review_record_count=review_record_count,
        rejected_decision_ratio=rejected_decision_ratio,
        rejected_source_proposal_ratio=rejected_source_proposal_ratio,
        max_reason_code_rejected_decision_share=max_reason_share,
        config=config,
    )
    return TradeProposalReviewDiagnosticReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        review_record_count=review_record_count,
        unique_source_proposal_count=unique_source_proposal_count,
        duplicate_source_proposal_review_count=(
            review_record_count - unique_source_proposal_count
        ),
        approved_decision_count=approved_decision_count,
        rejected_decision_count=rejected_decision_count,
        rejected_source_proposal_count=rejected_source_proposal_count,
        rejected_decision_ratio=rejected_decision_ratio,
        rejected_source_proposal_ratio=rejected_source_proposal_ratio,
        max_reason_code_rejected_decision_share=max_reason_share,
        first_recorded_at=(
            _as_utc(sorted_records[0].recorded_at) if sorted_records else None
        ),
        last_recorded_at=(
            _as_utc(sorted_records[-1].recorded_at) if sorted_records else None
        ),
        status=status,
        reason_rows=reason_rows,
        bucket_rows=_build_bucket_rows(sorted_records, config),
        source_rows=_build_source_rows(sorted_records, config.max_source_rows),
    )


def _clone_review_record(
    record: TradeProposalReviewRecord,
) -> TradeProposalReviewRecord:
    if type(record) is not TradeProposalReviewRecord:
        raise ValueError("records must contain TradeProposalReviewRecord values")
    return TradeProposalReviewRecord(
        **{
            field.name: getattr(record, field.name)
            for field in fields(TradeProposalReviewRecord)
        }
    )


def _diagnostic_status(
    *,
    review_record_count: int,
    rejected_decision_ratio: Decimal | None,
    rejected_source_proposal_ratio: Decimal | None,
    max_reason_code_rejected_decision_share: Decimal | None,
    config: TradeProposalReviewDiagnosticConfig,
) -> str:
    if review_record_count == 0:
        return "incomplete_review_data"
    if review_record_count < config.min_review_record_count:
        return "insufficient_review_sample"
    if (
        rejected_decision_ratio is not None
        and rejected_decision_ratio > config.max_rejected_decision_ratio
    ):
        return "high_rejection_proxy"
    if (
        rejected_source_proposal_ratio is not None
        and rejected_source_proposal_ratio > config.max_rejected_source_proposal_ratio
    ):
        return "high_rejection_proxy"
    if (
        max_reason_code_rejected_decision_share is not None
        and max_reason_code_rejected_decision_share
        > config.max_reason_code_rejected_decision_share
    ):
        return "high_rejection_proxy"
    return "diagnostics_ready"


def _build_reason_rows(
    records: tuple[TradeProposalReviewRecord, ...],
) -> tuple[TradeProposalReviewDiagnosticReasonRow, ...]:
    rejected_records = tuple(record for record in records if record.decision == "rejected")
    total_rejected = len(rejected_records)
    reason_counts: dict[str, int] = {}
    reason_sources: dict[str, set[str]] = {}
    for record in rejected_records:
        for reason_code in frozenset(record.review_reason_codes):
            reason_counts[reason_code] = reason_counts.get(reason_code, 0) + 1
            reason_sources.setdefault(reason_code, set()).add(
                record.source_proposal_packet_id
            )
    return tuple(
        TradeProposalReviewDiagnosticReasonRow(
            reason_code=reason_code,
            rejected_decision_count=reason_counts[reason_code],
            rejected_source_proposal_count=len(reason_sources[reason_code]),
            rejected_decision_share=_ratio_from_counts(
                reason_counts[reason_code],
                total_rejected,
            ),
        )
        for reason_code in sorted(reason_counts)
    )


def _build_bucket_rows(
    records: tuple[TradeProposalReviewRecord, ...],
    config: TradeProposalReviewDiagnosticConfig,
) -> tuple[TradeProposalReviewDiagnosticBucketRow, ...]:
    buckets: dict[tuple[str, str], list[TradeProposalReviewRecord]] = {}
    for record in records:
        if config.include_market_slug_buckets:
            _add_bucket_record(buckets, "market_slug", record.market_slug, record)
        if config.include_strategy_type_buckets:
            _add_bucket_record(buckets, "strategy_type", record.strategy_type, record)
        if config.include_risk_tag_buckets:
            for risk_tag in frozenset(record.risk_tags):
                _add_bucket_record(buckets, "risk_tag", risk_tag, record)
        if config.include_review_focus_buckets:
            for review_focus in frozenset(record.review_focus):
                _add_bucket_record(buckets, "review_focus", review_focus, record)

    rows: list[TradeProposalReviewDiagnosticBucketRow] = []
    for (bucket_type, bucket_value), bucket_records in sorted(buckets.items()):
        review_record_count = len(bucket_records)
        rejected_records = tuple(
            record for record in bucket_records if record.decision == "rejected"
        )
        rows.append(
            TradeProposalReviewDiagnosticBucketRow(
                bucket_type=bucket_type,
                bucket_value=bucket_value,
                review_record_count=review_record_count,
                unique_source_proposal_count=len(
                    {
                        record.source_proposal_packet_id
                        for record in bucket_records
                    }
                ),
                rejected_decision_count=len(rejected_records),
                rejected_source_proposal_count=len(
                    {
                        record.source_proposal_packet_id
                        for record in rejected_records
                    }
                ),
                rejected_decision_ratio=_ratio_from_counts(
                    len(rejected_records),
                    review_record_count,
                ),
            )
        )
    return tuple(rows)


def _add_bucket_record(
    buckets: dict[tuple[str, str], list[TradeProposalReviewRecord]],
    bucket_type: str,
    bucket_value: str,
    record: TradeProposalReviewRecord,
) -> None:
    buckets.setdefault((bucket_type, bucket_value), []).append(record)


def _build_source_rows(
    records: tuple[TradeProposalReviewRecord, ...],
    max_source_rows: int,
) -> tuple[TradeProposalReviewDiagnosticSourceRow, ...]:
    groups: dict[tuple[str, str], list[TradeProposalReviewRecord]] = {}
    for record in records:
        groups.setdefault(
            (record.source_proposal_packet_id, record.source_proposal_fingerprint),
            [],
        ).append(record)

    rows: list[TradeProposalReviewDiagnosticSourceRow] = []
    for (source_proposal_packet_id, source_proposal_fingerprint), group_records in groups.items():
        rejected_records = tuple(
            record for record in group_records if record.decision == "rejected"
        )
        if not rejected_records:
            continue
        first_record = sorted(group_records, key=lambda item: (_as_utc(item.recorded_at), item.review_record_id))[0]
        rows.append(
            TradeProposalReviewDiagnosticSourceRow(
                source_proposal_packet_id=source_proposal_packet_id,
                source_proposal_fingerprint=source_proposal_fingerprint,
                first_recorded_at=min(_as_utc(record.recorded_at) for record in group_records),
                last_recorded_at=max(_as_utc(record.recorded_at) for record in group_records),
                review_record_count=len(group_records),
                rejected_decision_count=len(rejected_records),
                reason_codes=tuple(
                    sorted(
                        {
                            reason_code
                            for record in rejected_records
                            for reason_code in record.review_reason_codes
                        }
                    )
                ),
                market_slug=first_record.market_slug,
                strategy_type=first_record.strategy_type,
                risk_tags=tuple(
                    sorted(
                        {
                            risk_tag
                            for record in group_records
                            for risk_tag in record.risk_tags
                        }
                    )
                ),
                review_focus=tuple(
                    sorted(
                        {
                            review_focus
                            for record in group_records
                            for review_focus in record.review_focus
                        }
                    )
                ),
            )
        )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda item: (
                -item.rejected_decision_count,
                -item.review_record_count,
                item.source_proposal_packet_id,
                item.source_proposal_fingerprint,
            ),
        )
    )
    return sorted_rows[:max_source_rows]


def _validate_report_tree(
    report: TradeProposalReviewDiagnosticReport,
) -> TradeProposalReviewDiagnosticReport:
    reason_rows = tuple(
        TradeProposalReviewDiagnosticReasonRow(
            reason_code=row.reason_code,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_share=row.rejected_decision_share,
        )
        for row in report.reason_rows
    )
    bucket_rows = tuple(
        TradeProposalReviewDiagnosticBucketRow(
            bucket_type=row.bucket_type,
            bucket_value=row.bucket_value,
            review_record_count=row.review_record_count,
            unique_source_proposal_count=row.unique_source_proposal_count,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_ratio=row.rejected_decision_ratio,
        )
        for row in report.bucket_rows
    )
    source_rows = tuple(
        TradeProposalReviewDiagnosticSourceRow(
            source_proposal_packet_id=row.source_proposal_packet_id,
            source_proposal_fingerprint=row.source_proposal_fingerprint,
            first_recorded_at=row.first_recorded_at,
            last_recorded_at=row.last_recorded_at,
            review_record_count=row.review_record_count,
            rejected_decision_count=row.rejected_decision_count,
            reason_codes=row.reason_codes,
            market_slug=row.market_slug,
            strategy_type=row.strategy_type,
            risk_tags=row.risk_tags,
            review_focus=row.review_focus,
        )
        for row in report.source_rows
    )
    return TradeProposalReviewDiagnosticReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        review_record_count=report.review_record_count,
        unique_source_proposal_count=report.unique_source_proposal_count,
        duplicate_source_proposal_review_count=(
            report.duplicate_source_proposal_review_count
        ),
        approved_decision_count=report.approved_decision_count,
        rejected_decision_count=report.rejected_decision_count,
        rejected_source_proposal_count=report.rejected_source_proposal_count,
        rejected_decision_ratio=report.rejected_decision_ratio,
        rejected_source_proposal_ratio=report.rejected_source_proposal_ratio,
        max_reason_code_rejected_decision_share=(
            report.max_reason_code_rejected_decision_share
        ),
        first_recorded_at=report.first_recorded_at,
        last_recorded_at=report.last_recorded_at,
        status=report.status,
        reason_rows=reason_rows,
        bucket_rows=bucket_rows,
        source_rows=source_rows,
    )


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
        "proposal-review diagnostic",
        "rejected human-review decisions",
        "false-positive proxy",
        "not realized false-positive confirmation",
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
        "settlement review",
        "reconciliation process",
        "automatic order-placement authorization",
    )
    if any(part not in lowered for part in required_parts):
        raise ValueError(
            "boundary_statement must describe report-only proposal-review diagnostics"
        )


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


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


def _normalize_sorted_string_tuple(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    if tuple(sorted(items)) != items:
        raise ValueError(f"{field_name} must be sorted")
    return items


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
