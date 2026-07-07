"""Report-only research source audit trail score reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION = (
    "research-source-audit-trail-score-v0"
)

PASS_REASON = "research_source_audit_trail_score_passed"
NO_INPUTS_REASON = "research_source_audit_trail_score_no_inputs"
STALE_REFRESH_REASON = "research_source_audit_trail_score_stale_refresh"
MISSING_REVISION_REASON = "research_source_audit_trail_score_missing_revision"
MISSING_CROSS_CHECK_REASON = "research_source_audit_trail_score_missing_cross_check"
MISSING_REVIEW_REASON = "research_source_audit_trail_score_missing_review"
LOW_AUDIT_TRAIL_SCORE_REASON = "research_source_audit_trail_score_low_score"

ROW_REASON_CODES = (
    STALE_REFRESH_REASON,
    MISSING_REVISION_REASON,
    MISSING_CROSS_CHECK_REASON,
    MISSING_REVIEW_REASON,
    LOW_AUDIT_TRAIL_SCORE_REASON,
)
REPORT_REASON_CODES = (PASS_REASON, NO_INPUTS_REASON) + ROW_REASON_CODES
BLOCKED_REASONS = frozenset(
    (
        NO_INPUTS_REASON,
        STALE_REFRESH_REASON,
        MISSING_REVISION_REASON,
        MISSING_CROSS_CHECK_REASON,
        MISSING_REVIEW_REASON,
        LOW_AUDIT_TRAIL_SCORE_REASON,
    ),
)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("can", "did", "ate"),
        _join_parts("mar", "ket"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("sou", "rce", "ref"),
        _join_parts("ur", "l"),
        _join_parts("tex", "t"),
        _join_parts("d", "sn"),
        _join_parts("tab", "le"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("posi", "tion"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("recom", "mendation"),
    ),
)


@dataclass(frozen=True)
class ResearchSourceAuditTrailScoreConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION
    max_refresh_age_seconds: Decimal = Decimal("86400.000000")
    watch_score_threshold: Decimal = Decimal("0.750000")
    block_score_threshold: Decimal = Decimal("0.500000")
    refresh_weight: Decimal = Decimal("0.250000")
    revision_weight: Decimal = Decimal("0.250000")
    cross_check_weight: Decimal = Decimal("0.250000")
    review_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuditTrailScoreConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_refresh_age_seconds",
            _normalize_positive_decimal(
                "max_refresh_age_seconds",
                self.max_refresh_age_seconds,
            ),
        )
        for field_name in ("watch_score_threshold", "block_score_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_score_threshold > self.watch_score_threshold:
            raise ValueError("block_score_threshold must not exceed watch_score_threshold")
        for field_name in (
            "refresh_weight",
            "revision_weight",
            "cross_check_weight",
            "review_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.refresh_weight
            + self.revision_weight
            + self.cross_check_weight
            + self.review_weight
            != ONE
        ):
            raise ValueError("audit trail score weights must sum to one")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceAuditTrailRecord:
    public_record_id: str
    research_theme: str
    refreshed_at: datetime | None
    revision_count: Decimal
    cross_check_count: Decimal
    review_count: Decimal
    conclusion_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchSourceAuditTrailRecord does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("public_record_id", "research_theme"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "refreshed_at",
            _as_optional_utc("refreshed_at", self.refreshed_at),
        )
        for field_name in (
            "revision_count",
            "cross_check_count",
            "review_count",
            "conclusion_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.conclusion_count <= ZERO:
            raise ValueError("conclusion_count must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceAuditTrailScoreRow:
    public_record_id: str
    research_theme: str
    refresh_age_seconds: Decimal | None
    revision_coverage_ratio: Decimal
    cross_check_coverage_ratio: Decimal
    review_coverage_ratio: Decimal
    audit_trail_score: Decimal
    audit_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchSourceAuditTrailScoreRow does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("public_record_id", "research_theme"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "refresh_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "refresh_age_seconds",
                self.refresh_age_seconds,
            ),
        )
        for field_name in (
            "revision_coverage_ratio",
            "cross_check_coverage_ratio",
            "review_coverage_ratio",
            "audit_trail_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("audit_status", self.audit_status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchSourceAuditTrailReasonCodeCount:
    reason_code: str
    record_count: Decimal
    record_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuditTrailReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "record_count",
            _normalize_positive_count("record_count", self.record_count),
        )
        object.__setattr__(
            self,
            "record_ratio",
            _normalize_ratio("record_ratio", self.record_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchSourceAuditTrailScoreReport:
    generated_at: datetime
    config_version: str
    audit_status: str
    record_count: Decimal
    pass_record_count: Decimal
    watch_record_count: Decimal
    block_record_count: Decimal
    attention_record_count: Decimal
    attention_record_ratio: Decimal
    stale_refresh_record_count: Decimal
    missing_revision_record_count: Decimal
    missing_cross_check_record_count: Decimal
    missing_review_record_count: Decimal
    low_score_record_count: Decimal
    min_audit_trail_score: Decimal
    mean_audit_trail_score: Decimal
    max_refresh_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceAuditTrailReasonCodeCount, ...]
    rows: tuple[ResearchSourceAuditTrailScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchSourceAuditTrailScoreReport does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_member("audit_status", self.audit_status, PUBLIC_STATUSES)
        for field_name in (
            "record_count",
            "pass_record_count",
            "watch_record_count",
            "block_record_count",
            "attention_record_count",
            "stale_refresh_record_count",
            "missing_revision_record_count",
            "missing_cross_check_record_count",
            "missing_review_record_count",
            "low_score_record_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "attention_record_ratio",
            "min_audit_trail_score",
            "mean_audit_trail_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_refresh_age_seconds",
            _normalize_nonnegative_decimal(
                "max_refresh_age_seconds",
                self.max_refresh_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_source_audit_trail_score_report(
    records: list[ResearchSourceAuditTrailRecord]
    | tuple[ResearchSourceAuditTrailRecord, ...],
    *,
    config: ResearchSourceAuditTrailScoreConfig,
    generated_at: datetime,
) -> ResearchSourceAuditTrailScoreReport:
    if type(config) is not ResearchSourceAuditTrailScoreConfig:
        raise ValueError("config must be a ResearchSourceAuditTrailScoreConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_records = _normalize_records(records)
    _validate_record_times(normalized_records, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_record(record, config=config, generated_at=generated_at_utc)
                for record in normalized_records
            ),
            key=_row_sort_key,
        ),
    )
    record_count = _count_decimal(len(rows))
    attention_count = _count_decimal(sum(1 for row in rows if row.audit_status != "pass"))
    return ResearchSourceAuditTrailScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        audit_status=_report_status(rows),
        record_count=record_count,
        pass_record_count=_status_count(rows, "pass"),
        watch_record_count=_status_count(rows, "watch"),
        block_record_count=_status_count(rows, "block"),
        attention_record_count=attention_count,
        attention_record_ratio=_safe_ratio(attention_count, record_count),
        stale_refresh_record_count=_reason_count(rows, STALE_REFRESH_REASON),
        missing_revision_record_count=_reason_count(rows, MISSING_REVISION_REASON),
        missing_cross_check_record_count=_reason_count(rows, MISSING_CROSS_CHECK_REASON),
        missing_review_record_count=_reason_count(rows, MISSING_REVIEW_REASON),
        low_score_record_count=_reason_count(rows, LOW_AUDIT_TRAIL_SCORE_REASON),
        min_audit_trail_score=min(
            (row.audit_trail_score for row in rows),
            default=ZERO,
        ),
        mean_audit_trail_score=_safe_ratio(
            _decimal_sum(row.audit_trail_score for row in rows),
            record_count,
        ),
        max_refresh_age_seconds=max(
            (
                row.refresh_age_seconds
                for row in rows
                if row.refresh_age_seconds is not None
            ),
            default=ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_audit_trail_score_payload(value: object) -> dict[str, Any]:
    if type(value) is ResearchSourceAuditTrailScoreReport:
        _revalidate_report(value)
        payload = _payload_value(value)
        validate_research_source_audit_trail_score_public_payload(payload)
        return payload
    if type(value) is dict:
        validate_research_source_audit_trail_score_public_payload(value)
        return dict(value)
    raise ValueError("value must be a ResearchSourceAuditTrailScoreReport or dict")


def validate_research_source_audit_trail_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    rows_value = payload.get("rows")
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows_value:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain dict values")
        _require_public_payload_flags(row_payload)
        row_digest = _payload_required_string(row_payload, "derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", row_digest)
        if row_digest != _public_row_digest(row_payload):
            raise ValueError("derived_validation_digest must match row payload")
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_report_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_record(
    record: ResearchSourceAuditTrailRecord,
    *,
    config: ResearchSourceAuditTrailScoreConfig,
    generated_at: datetime,
) -> ResearchSourceAuditTrailScoreRow:
    refresh_age_seconds = (
        None
        if record.refreshed_at is None
        else _duration_seconds(generated_at, record.refreshed_at)
    )
    revision_coverage_ratio = _safe_ratio(record.revision_count, record.conclusion_count)
    cross_check_coverage_ratio = _safe_ratio(
        record.cross_check_count,
        record.conclusion_count,
    )
    review_coverage_ratio = _safe_ratio(record.review_count, record.conclusion_count)
    refresh_component = (
        ZERO
        if refresh_age_seconds is None
        else ONE - min(_safe_ratio(refresh_age_seconds, config.max_refresh_age_seconds), ONE)
    )
    audit_trail_score = _quantize_decimal(
        refresh_component * config.refresh_weight
        + min(revision_coverage_ratio, ONE) * config.revision_weight
        + min(cross_check_coverage_ratio, ONE) * config.cross_check_weight
        + min(review_coverage_ratio, ONE) * config.review_weight,
    )
    reason_codes = _row_reason_codes(
        refresh_age_seconds=refresh_age_seconds,
        revision_coverage_ratio=revision_coverage_ratio,
        cross_check_coverage_ratio=cross_check_coverage_ratio,
        review_coverage_ratio=review_coverage_ratio,
        audit_trail_score=audit_trail_score,
        config=config,
    )
    return ResearchSourceAuditTrailScoreRow(
        public_record_id=record.public_record_id,
        research_theme=record.research_theme,
        refresh_age_seconds=refresh_age_seconds,
        revision_coverage_ratio=revision_coverage_ratio,
        cross_check_coverage_ratio=cross_check_coverage_ratio,
        review_coverage_ratio=review_coverage_ratio,
        audit_trail_score=audit_trail_score,
        audit_status=_row_status(reason_codes, config=config, score=audit_trail_score),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    refresh_age_seconds: Decimal | None,
    revision_coverage_ratio: Decimal,
    cross_check_coverage_ratio: Decimal,
    review_coverage_ratio: Decimal,
    audit_trail_score: Decimal,
    config: ResearchSourceAuditTrailScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if refresh_age_seconds is None or refresh_age_seconds > config.max_refresh_age_seconds:
        reason_codes.append(STALE_REFRESH_REASON)
    if revision_coverage_ratio < ONE:
        reason_codes.append(MISSING_REVISION_REASON)
    if cross_check_coverage_ratio < ONE:
        reason_codes.append(MISSING_CROSS_CHECK_REASON)
    if review_coverage_ratio < ONE:
        reason_codes.append(MISSING_REVIEW_REASON)
    if audit_trail_score < config.watch_score_threshold:
        reason_codes.append(LOW_AUDIT_TRAIL_SCORE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    config: ResearchSourceAuditTrailScoreConfig,
    score: Decimal,
) -> str:
    if score < config.block_score_threshold:
        return "block"
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceAuditTrailScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.audit_status == "block" for row in rows):
        return "block"
    if any(row.audit_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuditTrailScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuditTrailScoreRow, ...],
) -> tuple[ResearchSourceAuditTrailReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchSourceAuditTrailReasonCodeCount(
            reason_code=reason_code,
            record_count=_reason_count(rows, reason_code),
            record_ratio=_safe_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_records(
    value: object,
) -> tuple[ResearchSourceAuditTrailRecord, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    seen: set[str] = set()
    for record in records:
        if type(record) is not ResearchSourceAuditTrailRecord:
            raise ValueError("records must contain ResearchSourceAuditTrailRecord values")
        _require_hard_flags(record)
        if record.public_record_id in seen:
            raise ValueError("records must be unique by public_record_id")
        seen.add(record.public_record_id)
    return records


def _validate_record_times(
    records: tuple[ResearchSourceAuditTrailRecord, ...],
    *,
    generated_at: datetime,
) -> None:
    for record in records:
        if record.refreshed_at is not None and record.refreshed_at > generated_at:
            raise ValueError("refreshed_at must not be after generated_at")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuditTrailScoreRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuditTrailScoreRow:
            raise ValueError("rows must contain ResearchSourceAuditTrailScoreRow values")
        _require_hard_flags(row)
        if row.public_record_id in seen:
            raise ValueError("rows must be unique by public_record_id")
        seen.add(row.public_record_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceAuditTrailReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceAuditTrailReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchSourceAuditTrailReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODES
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_row(row: ResearchSourceAuditTrailScoreRow) -> None:
    if row.audit_status not in PUBLIC_STATUSES:
        raise ValueError("audit_status must be public")
    if row.audit_status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason code")
    if row.audit_status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("attention rows must not use pass reason code")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchSourceAuditTrailScoreReport) -> None:
    rows = report.rows
    record_count = _count_decimal(len(rows))
    if report.record_count != record_count:
        raise ValueError("record_count must match rows")
    for field_name, status in (
        ("pass_record_count", "pass"),
        ("watch_record_count", "watch"),
        ("block_record_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if (
        report.pass_record_count
        + report.watch_record_count
        + report.block_record_count
        != report.record_count
    ):
        raise ValueError("status counts must match record_count")
    if report.attention_record_count != _count_decimal(
        sum(1 for row in rows if row.audit_status != "pass"),
    ):
        raise ValueError("attention_record_count must match rows")
    if report.attention_record_ratio != _safe_ratio(
        report.attention_record_count,
        report.record_count,
    ):
        raise ValueError("attention_record_ratio must match counts")
    for field_name, reason_code in (
        ("stale_refresh_record_count", STALE_REFRESH_REASON),
        ("missing_revision_record_count", MISSING_REVISION_REASON),
        ("missing_cross_check_record_count", MISSING_CROSS_CHECK_REASON),
        ("missing_review_record_count", MISSING_REVIEW_REASON),
        ("low_score_record_count", LOW_AUDIT_TRAIL_SCORE_REASON),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.min_audit_trail_score != min(
        (row.audit_trail_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_audit_trail_score must match rows")
    if report.mean_audit_trail_score != _safe_ratio(
        _decimal_sum(row.audit_trail_score for row in rows),
        report.record_count,
    ):
        raise ValueError("mean_audit_trail_score must match rows")
    if report.max_refresh_age_seconds != max(
        (
            row.refresh_age_seconds
            for row in rows
            if row.refresh_age_seconds is not None
        ),
        default=ZERO,
    ):
        raise ValueError("max_refresh_age_seconds must match rows")
    if report.audit_status != _report_status(rows):
        raise ValueError("audit_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_sort_key(
    row: ResearchSourceAuditTrailScoreRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.audit_status],
        row.audit_trail_score,
        -_count_decimal(len(tuple(code for code in row.reason_codes if code != PASS_REASON))),
        row.public_record_id,
    )


def _status_count(
    rows: tuple[ResearchSourceAuditTrailScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.audit_status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuditTrailScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _decimal_sum(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize_decimal(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECOND_DIVISOR
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(seconds + microseconds)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    _reject_public_text(field_name, value)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be present and true")


def _require_public_payload_flags(value: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be present and true")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _revalidate_report(report: ResearchSourceAuditTrailScoreReport) -> None:
    if type(report) is not ResearchSourceAuditTrailScoreReport:
        raise ValueError("report must be a ResearchSourceAuditTrailScoreReport")
    for row in report.rows:
        _validate_row(row)
    _validate_report(report)


def _row_derived_validation_digest(row: ResearchSourceAuditTrailScoreRow) -> str:
    return _digest_payload(_without_top_digest(_payload_value(row)))


def _report_derived_validation_digest(report: ResearchSourceAuditTrailScoreReport) -> str:
    return _digest_payload(_without_top_digest(_payload_value(report)))


def _public_row_digest(payload: dict[str, Any]) -> str:
    return _digest_payload(_without_top_digest(payload))


def _public_report_digest(payload: dict[str, Any]) -> str:
    return _digest_payload(_without_top_digest(payload))


def _without_top_digest(payload: object) -> object:
    if type(payload) is dict:
        return {
            key: value
            for key, value in payload.items()
            if key != "derived_validation_digest"
        }
    return payload


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (int, float, Decimal):
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _reject_public_text(field_name: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION",
    "ResearchSourceAuditTrailReasonCodeCount",
    "ResearchSourceAuditTrailRecord",
    "ResearchSourceAuditTrailScoreConfig",
    "ResearchSourceAuditTrailScoreReport",
    "ResearchSourceAuditTrailScoreRow",
    "build_research_source_audit_trail_score_report",
    "research_source_audit_trail_score_payload",
    "validate_research_source_audit_trail_score_public_payload",
)
