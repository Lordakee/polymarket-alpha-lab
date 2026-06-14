"""Report-only proposal-review summaries for Level 2."""

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
    "TradeProposalReviewBucketSummary",
    "TradeProposalReviewReasonCodeSummary",
    "TradeProposalReviewSummaryConfig",
    "TradeProposalReviewSummaryLog",
    "TradeProposalReviewSummaryReport",
    "build_trade_proposal_review_summary_report",
)


DEFAULT_REVIEW_SUMMARY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review summary artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")
BUCKET_TYPES = ("market_slug", "strategy_type", "risk_tag")
REPORT_STATUSES = (
    "insufficient_review_sample",
    "high_rejection_ratio",
    "summary_ready",
)


@dataclass(frozen=True)
class TradeProposalReviewSummaryConfig:
    config_version: str
    min_review_record_count: int = 1
    max_rejection_ratio: Decimal = Decimal("1.0000")
    boundary_statement: str = DEFAULT_REVIEW_SUMMARY_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_review_record_count",
            self.min_review_record_count,
        )
        _require_probability_decimal("max_rejection_ratio", self.max_rejection_ratio)
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalReviewReasonCodeSummary:
    reason_code: str
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_ratio: Decimal

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
        _require_probability_decimal(
            "rejected_decision_ratio",
            self.rejected_decision_ratio,
        )


@dataclass(frozen=True)
class TradeProposalReviewBucketSummary:
    bucket_type: str
    bucket_value: str
    review_record_count: int
    unique_source_proposal_count: int
    approved_decision_count: int
    rejected_decision_count: int
    rejection_ratio: Decimal

    def __post_init__(self) -> None:
        if self.bucket_type not in BUCKET_TYPES:
            raise ValueError("bucket_type must be market_slug, strategy_type, or risk_tag")
        _require_canonical_string("bucket_value", self.bucket_value)
        _require_positive_int("review_record_count", self.review_record_count)
        _require_positive_int(
            "unique_source_proposal_count",
            self.unique_source_proposal_count,
        )
        _require_nonnegative_int(
            "approved_decision_count",
            self.approved_decision_count,
        )
        _require_nonnegative_int(
            "rejected_decision_count",
            self.rejected_decision_count,
        )
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
        expected_ratio = _ratio_from_counts(
            self.rejected_decision_count,
            self.review_record_count,
        )
        if self.rejection_ratio != expected_ratio:
            raise ValueError("rejection_ratio must match rejected decision count")
        _require_probability_decimal("rejection_ratio", self.rejection_ratio)


@dataclass(frozen=True)
class TradeProposalReviewSummaryReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    review_record_count: int
    unique_source_proposal_count: int
    duplicate_source_proposal_count: int
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    approved_decision_count: int
    rejected_decision_count: int
    rejection_ratio: Decimal | None
    status: str
    reason_code_summaries: tuple[TradeProposalReviewReasonCodeSummary, ...]
    bucket_summaries: tuple[TradeProposalReviewBucketSummary, ...]

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
            "duplicate_source_proposal_count",
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
        if self.unique_source_proposal_count > self.review_record_count:
            raise ValueError(
                "unique_source_proposal_count must not exceed review_record_count"
            )
        if self.duplicate_source_proposal_count != (
            self.review_record_count - self.unique_source_proposal_count
        ):
            raise ValueError(
                "duplicate_source_proposal_count must equal review count minus unique source count"
            )
        if self.review_record_count == 0:
            if self.first_recorded_at is not None or self.last_recorded_at is not None:
                raise ValueError("recorded_at bounds must be absent without records")
            if self.rejection_ratio is not None:
                raise ValueError("rejection_ratio must be absent without records")
            if self.reason_code_summaries != ():
                raise ValueError("reason_code_summaries must be empty without records")
            if self.bucket_summaries != ():
                raise ValueError("bucket_summaries must be empty without records")
        else:
            if self.first_recorded_at is None or self.last_recorded_at is None:
                raise ValueError("recorded_at bounds are required with records")
            if self.first_recorded_at > self.last_recorded_at:
                raise ValueError("first_recorded_at must be before last_recorded_at")
            if self.rejection_ratio is None:
                raise ValueError("rejection_ratio is required with records")
            expected_ratio = _ratio_from_counts(
                self.rejected_decision_count,
                self.review_record_count,
            )
            if self.rejection_ratio != expected_ratio:
                raise ValueError("rejection_ratio must match rejected decision count")
            _require_probability_decimal("rejection_ratio", self.rejection_ratio)
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known proposal review summary status")
        object.__setattr__(
            self,
            "reason_code_summaries",
            _normalize_typed_tuple(
                "reason_code_summaries",
                self.reason_code_summaries,
                TradeProposalReviewReasonCodeSummary,
            ),
        )
        object.__setattr__(
            self,
            "bucket_summaries",
            _normalize_typed_tuple(
                "bucket_summaries",
                self.bucket_summaries,
                TradeProposalReviewBucketSummary,
            ),
        )
        if tuple(
            sorted(self.reason_code_summaries, key=lambda item: item.reason_code)
        ) != self.reason_code_summaries:
            raise ValueError("reason_code_summaries must be sorted by reason_code")
        if tuple(
            sorted(
                self.bucket_summaries,
                key=lambda item: (item.bucket_type, item.bucket_value),
            )
        ) != self.bucket_summaries:
            raise ValueError("bucket_summaries must be sorted by bucket_type and value")


@dataclass(frozen=True)
class TradeProposalReviewSummaryLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalReviewSummaryReport) -> None:
        if type(report) is not TradeProposalReviewSummaryReport:
            raise ValueError("report must be a TradeProposalReviewSummaryReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_summary_report(
    records: Iterable[TradeProposalReviewRecord],
    *,
    config: TradeProposalReviewSummaryConfig,
    generated_at: datetime,
) -> TradeProposalReviewSummaryReport:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable of TradeProposalReviewRecord values")
    if type(config) is not TradeProposalReviewSummaryConfig:
        raise ValueError("config must be a TradeProposalReviewSummaryConfig")
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
    unique_source_proposal_count = len(
        {record.source_proposal_packet_id for record in sorted_records}
    )
    approved_decision_count = sum(
        1 for record in sorted_records if record.decision == "approved"
    )
    rejected_decision_count = sum(
        1 for record in sorted_records if record.decision == "rejected"
    )
    rejection_ratio = _optional_ratio_from_counts(
        rejected_decision_count,
        review_record_count,
    )
    status = _summary_status(
        review_record_count=review_record_count,
        rejection_ratio=rejection_ratio,
        config=config,
    )
    return TradeProposalReviewSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        review_record_count=review_record_count,
        unique_source_proposal_count=unique_source_proposal_count,
        duplicate_source_proposal_count=(
            review_record_count - unique_source_proposal_count
        ),
        first_recorded_at=(
            _as_utc(sorted_records[0].recorded_at) if sorted_records else None
        ),
        last_recorded_at=(
            _as_utc(sorted_records[-1].recorded_at) if sorted_records else None
        ),
        approved_decision_count=approved_decision_count,
        rejected_decision_count=rejected_decision_count,
        rejection_ratio=rejection_ratio,
        status=status,
        reason_code_summaries=_build_reason_code_summaries(sorted_records),
        bucket_summaries=_build_bucket_summaries(sorted_records),
    )


def _clone_review_record(record: TradeProposalReviewRecord) -> TradeProposalReviewRecord:
    if type(record) is not TradeProposalReviewRecord:
        raise ValueError("records must contain TradeProposalReviewRecord values")
    return TradeProposalReviewRecord(
        **{field.name: getattr(record, field.name) for field in fields(TradeProposalReviewRecord)}
    )


def _summary_status(
    *,
    review_record_count: int,
    rejection_ratio: Decimal | None,
    config: TradeProposalReviewSummaryConfig,
) -> str:
    if review_record_count < config.min_review_record_count:
        return "insufficient_review_sample"
    if rejection_ratio is not None and rejection_ratio > config.max_rejection_ratio:
        return "high_rejection_ratio"
    return "summary_ready"


def _build_reason_code_summaries(
    records: tuple[TradeProposalReviewRecord, ...],
) -> tuple[TradeProposalReviewReasonCodeSummary, ...]:
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
        TradeProposalReviewReasonCodeSummary(
            reason_code=reason_code,
            rejected_decision_count=reason_counts[reason_code],
            rejected_source_proposal_count=len(reason_sources[reason_code]),
            rejected_decision_ratio=_ratio_from_counts(
                reason_counts[reason_code],
                total_rejected,
            ),
        )
        for reason_code in sorted(reason_counts)
    )


def _build_bucket_summaries(
    records: tuple[TradeProposalReviewRecord, ...],
) -> tuple[TradeProposalReviewBucketSummary, ...]:
    buckets: dict[tuple[str, str], list[TradeProposalReviewRecord]] = {}
    for record in records:
        _add_bucket_record(buckets, "market_slug", record.market_slug, record)
        _add_bucket_record(buckets, "strategy_type", record.strategy_type, record)
        for risk_tag in frozenset(record.risk_tags):
            _add_bucket_record(buckets, "risk_tag", risk_tag, record)

    rows: list[TradeProposalReviewBucketSummary] = []
    for (bucket_type, bucket_value), bucket_records in sorted(buckets.items()):
        review_record_count = len(bucket_records)
        approved_decision_count = sum(
            1 for record in bucket_records if record.decision == "approved"
        )
        rejected_decision_count = sum(
            1 for record in bucket_records if record.decision == "rejected"
        )
        rows.append(
            TradeProposalReviewBucketSummary(
                bucket_type=bucket_type,
                bucket_value=bucket_value,
                review_record_count=review_record_count,
                unique_source_proposal_count=len(
                    {
                        record.source_proposal_packet_id
                        for record in bucket_records
                    }
                ),
                approved_decision_count=approved_decision_count,
                rejected_decision_count=rejected_decision_count,
                rejection_ratio=_ratio_from_counts(
                    rejected_decision_count,
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


def _ratio_from_counts(numerator: int, denominator: int) -> Decimal:
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _optional_ratio_from_counts(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _ratio_from_counts(numerator, denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_finite_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _validate_report_tree(
    report: TradeProposalReviewSummaryReport,
) -> TradeProposalReviewSummaryReport:
    reason_code_summaries = tuple(
        TradeProposalReviewReasonCodeSummary(
            reason_code=row.reason_code,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_ratio=row.rejected_decision_ratio,
        )
        for row in report.reason_code_summaries
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
        for row in report.bucket_summaries
    )
    return TradeProposalReviewSummaryReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        review_record_count=report.review_record_count,
        unique_source_proposal_count=report.unique_source_proposal_count,
        duplicate_source_proposal_count=report.duplicate_source_proposal_count,
        first_recorded_at=report.first_recorded_at,
        last_recorded_at=report.last_recorded_at,
        approved_decision_count=report.approved_decision_count,
        rejected_decision_count=report.rejected_decision_count,
        rejection_ratio=report.rejection_ratio,
        status=report.status,
        reason_code_summaries=reason_code_summaries,
        bucket_summaries=bucket_summaries,
    )


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
        "proposal-review summary",
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
        raise ValueError("boundary_statement must describe report-only proposal-review summary")


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
