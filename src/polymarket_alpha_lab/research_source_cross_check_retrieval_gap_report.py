"""Pure report-only reducer for source cross-check retrieval gaps."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION",
    "ResearchSourceCrossCheckRetrievalGapConfig",
    "ResearchSourceCrossCheckRetrievalGapInputRow",
    "ResearchSourceCrossCheckRetrievalGapReportRow",
    "ResearchSourceCrossCheckRetrievalGapReport",
    "build_research_source_cross_check_retrieval_gap_report",
    "research_source_cross_check_retrieval_gap_report_payload",
)


DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION = (
    "research-source-cross-check-retrieval-gap-report-v0"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_SECONDS_PER_DAY = Decimal("86400.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_DEFAULT_REQUIRED_SOURCE_CLASSES = ("official", "primary", "secondary")
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_REVIEW_ACTION_BY_STATUS = {
    "pass": "continue_source_cross_check",
    "watch": "review_cross_check_retrieval_gaps",
    "block": "pause_cross_check_until_retrieval_gaps_clear",
}
_PASS_REASON = "source_cross_check_retrieval_gap_pass"
_REASON_CODE_ORDER = (
    "missing_corroborating_source_class_watch",
    "missing_corroborating_source_class_block",
    "retrieval_freshness_watch",
    "retrieval_freshness_block",
    "parse_reliability_watch",
    "parse_reliability_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "retry_backlog_watch",
    "retry_backlog_block",
    "manual_review_urgency_watch",
    "manual_review_urgency_block",
    _PASS_REASON,
)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw_url",
    "raw_text",
    "source_text",
    "market_id",
    "market_slug",
    "candidate_id",
    "candidate_identifier",
    "dsn",
    "table_name",
    "private_token",
    "private_key",
    "api_key",
    "password",
    "secret",
    "wallet",
    "account",
    "broker",
    "order",
    "trade",
    "trading",
)

_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "report_status",
    "review_action",
    "review_bucket_count",
    "pass_count",
    "watch_count",
    "block_count",
    "source_observation_count",
    "missing_corroborating_source_class_count",
    "max_retrieval_age_seconds",
    "average_parse_reliability_score",
    "max_contradiction_pressure_score",
    "retry_backlog_count",
    "max_manual_review_urgency_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "review_bucket",
    "required_source_class_count",
    "source_observation_count",
    "observed_source_class_count",
    "missing_corroborating_source_class_count",
    "retrieval_age_seconds",
    "retrieval_freshness_score",
    "parse_success_count",
    "parse_failure_count",
    "parse_attempt_count",
    "parse_reliability_score",
    "contradiction_count",
    "contradiction_pressure_score",
    "retry_backlog_count",
    "retry_backlog_pressure_score",
    "manual_review_due_at",
    "manual_review_urgency_score",
    "gap_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchSourceCrossCheckRetrievalGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION
    )
    required_source_classes: tuple[str, ...] = _DEFAULT_REQUIRED_SOURCE_CLASSES
    freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    min_watch_parse_reliability_score: Decimal = Decimal("0.750000")
    min_pass_parse_reliability_score: Decimal = Decimal("0.900000")
    contradiction_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_block_threshold: Decimal = Decimal("0.500000")
    retry_backlog_watch_threshold: Decimal = Decimal("0.250000")
    retry_backlog_block_threshold: Decimal = Decimal("0.500000")
    manual_review_watch_horizon_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossCheckRetrievalGapConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceCrossCheckRetrievalGapConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "required_source_classes",
            _normalize_required_source_classes(self.required_source_classes),
        )
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
            "manual_review_watch_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_watch_parse_reliability_score",
            "min_pass_parse_reliability_score",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "retry_backlog_watch_threshold",
            "retry_backlog_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.freshness_block_age_seconds <= self.freshness_watch_age_seconds:
            raise ValueError(
                "freshness block age must exceed freshness watch age",
            )
        if (
            self.min_pass_parse_reliability_score
            <= self.min_watch_parse_reliability_score
        ):
            raise ValueError(
                "min_pass_parse_reliability_score must exceed "
                "min_watch_parse_reliability_score",
            )
        if self.contradiction_block_threshold <= self.contradiction_watch_threshold:
            raise ValueError(
                "contradiction block threshold must exceed watch threshold",
            )
        if self.retry_backlog_block_threshold <= self.retry_backlog_watch_threshold:
            raise ValueError(
                "retry_backlog block threshold must exceed watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceCrossCheckRetrievalGapInputRow:
    review_bucket: str
    source_class: str
    retrieved_at: datetime
    parse_success_count: Decimal
    parse_failure_count: Decimal
    contradiction_count: Decimal
    retry_backlog_count: Decimal
    manual_review_due_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossCheckRetrievalGapInputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input row",
            self,
            ResearchSourceCrossCheckRetrievalGapInputRow,
        )
        _require_public_identifier("review_bucket", self.review_bucket)
        _require_public_identifier("source_class", self.source_class)
        object.__setattr__(
            self,
            "retrieved_at",
            _as_utc("retrieved_at", self.retrieved_at),
        )
        for field_name in (
            "parse_success_count",
            "parse_failure_count",
            "contradiction_count",
            "retry_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_review_due_at",
            _as_optional_utc("manual_review_due_at", self.manual_review_due_at),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchSourceCrossCheckRetrievalGapReportRow:
    review_bucket: str
    required_source_class_count: Decimal
    source_observation_count: Decimal
    observed_source_class_count: Decimal
    missing_corroborating_source_class_count: Decimal
    retrieval_age_seconds: Decimal
    retrieval_freshness_score: Decimal
    parse_success_count: Decimal
    parse_failure_count: Decimal
    parse_attempt_count: Decimal
    parse_reliability_score: Decimal
    contradiction_count: Decimal
    contradiction_pressure_score: Decimal
    retry_backlog_count: Decimal
    retry_backlog_pressure_score: Decimal
    manual_review_due_at: datetime | None
    manual_review_urgency_score: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossCheckRetrievalGapReportRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report row",
            self,
            ResearchSourceCrossCheckRetrievalGapReportRow,
        )
        _require_public_identifier("review_bucket", self.review_bucket)
        object.__setattr__(
            self,
            "required_source_class_count",
            _normalize_positive_count(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        for field_name in (
            "source_observation_count",
            "observed_source_class_count",
            "missing_corroborating_source_class_count",
            "parse_success_count",
            "parse_failure_count",
            "parse_attempt_count",
            "contradiction_count",
            "retry_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "retrieval_age_seconds",
            _normalize_nonnegative_decimal(
                "retrieval_age_seconds",
                self.retrieval_age_seconds,
            ),
        )
        for field_name in (
            "retrieval_freshness_score",
            "parse_reliability_score",
            "contradiction_pressure_score",
            "retry_backlog_pressure_score",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_review_due_at",
            _as_optional_utc("manual_review_due_at", self.manual_review_due_at),
        )
        _require_member("gap_status", self.gap_status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report row", self)
        _validate_report_row(self)


@dataclass(frozen=True)
class ResearchSourceCrossCheckRetrievalGapReport:
    generated_at: datetime
    config_version: str
    report_status: str
    review_action: str
    review_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    source_observation_count: Decimal
    missing_corroborating_source_class_count: Decimal
    max_retrieval_age_seconds: Decimal
    average_parse_reliability_score: Decimal
    max_contradiction_pressure_score: Decimal
    retry_backlog_count: Decimal
    max_manual_review_urgency_score: Decimal
    rows: tuple[ResearchSourceCrossCheckRetrievalGapReportRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossCheckRetrievalGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceCrossCheckRetrievalGapReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CROSS_CHECK_RETRIEVAL_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, _STATUSES)
        _require_member(
            "review_action",
            self.review_action,
            tuple(_REVIEW_ACTION_BY_STATUS.values()),
        )
        for field_name in (
            "review_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "source_observation_count",
            "missing_corroborating_source_class_count",
            "retry_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_retrieval_age_seconds",
            _normalize_nonnegative_decimal(
                "max_retrieval_age_seconds",
                self.max_retrieval_age_seconds,
            ),
        )
        for field_name in (
            "average_parse_reliability_score",
            "max_contradiction_pressure_score",
            "max_manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _verify_report_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_cross_check_retrieval_gap_report_payload(self)


def build_research_source_cross_check_retrieval_gap_report(
    input_rows: Iterable[ResearchSourceCrossCheckRetrievalGapInputRow],
    *,
    generated_at: datetime,
    config: ResearchSourceCrossCheckRetrievalGapConfig,
) -> ResearchSourceCrossCheckRetrievalGapReport:
    if type(config) is not ResearchSourceCrossCheckRetrievalGapConfig:
        raise ValueError(
            "config must be exactly ResearchSourceCrossCheckRetrievalGapConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_input_rows(input_rows)

    grouped: dict[str, list[ResearchSourceCrossCheckRetrievalGapInputRow]] = {}
    seen_keys: set[tuple[str, str]] = set()
    for input_row in normalized_inputs:
        if input_row.retrieved_at > generated_at:
            raise ValueError("retrieved_at cannot be in the future")
        key = (input_row.review_bucket, input_row.source_class)
        if key in seen_keys:
            raise ValueError(
                "duplicate source_class within review_bucket is not allowed",
            )
        seen_keys.add(key)
        grouped.setdefault(input_row.review_bucket, []).append(input_row)

    rows = tuple(
        sorted(
            (
                _row_from_group(
                    review_bucket,
                    tuple(group_inputs),
                    generated_at=generated_at,
                    config=config,
                )
                for review_bucket, group_inputs in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": report_status,
        "review_action": _REVIEW_ACTION_BY_STATUS[report_status],
        "review_bucket_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(
            sum(1 for row in rows if row.gap_status == "pass"),
        ),
        "watch_count": _count_decimal(
            sum(1 for row in rows if row.gap_status == "watch"),
        ),
        "block_count": _count_decimal(
            sum(1 for row in rows if row.gap_status == "block"),
        ),
        "source_observation_count": _sum_decimal(
            tuple(row.source_observation_count for row in rows),
        ),
        "missing_corroborating_source_class_count": _sum_decimal(
            tuple(
                row.missing_corroborating_source_class_count for row in rows
            ),
        ),
        "max_retrieval_age_seconds": max(
            (row.retrieval_age_seconds for row in rows),
            default=_ZERO,
        ),
        "average_parse_reliability_score": _average_decimal(
            tuple(row.parse_reliability_score for row in rows),
        ),
        "max_contradiction_pressure_score": max(
            (row.contradiction_pressure_score for row in rows),
            default=_ZERO,
        ),
        "retry_backlog_count": _sum_decimal(
            tuple(row.retry_backlog_count for row in rows),
        ),
        "max_manual_review_urgency_score": max(
            (row.manual_review_urgency_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    unsigned_payload = _json_ready(values)
    if type(unsigned_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return ResearchSourceCrossCheckRetrievalGapReport(
        **values,
        derived_validation_digest=_digest_payload(unsigned_payload),
    )


def research_source_cross_check_retrieval_gap_report_payload(
    report: ResearchSourceCrossCheckRetrievalGapReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchSourceCrossCheckRetrievalGapReport:
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    elif isinstance(report, Mapping):
        copied = _copy_json_value(dict(report))
        if type(copied) is not dict:
            raise ValueError("report payload must be a JSON object")
        payload = copied
    else:
        raise ValueError(
            "report must be a ResearchSourceCrossCheckRetrievalGapReport or mapping",
        )
    reconstructed = _validate_and_reconstruct_public_payload(payload)
    canonical = _json_ready(asdict(reconstructed))
    if type(canonical) is not dict:
        raise ValueError("report payload must be a JSON object")
    return canonical


def _row_from_group(
    review_bucket: str,
    group_inputs: tuple[ResearchSourceCrossCheckRetrievalGapInputRow, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceCrossCheckRetrievalGapConfig,
) -> ResearchSourceCrossCheckRetrievalGapReportRow:
    source_classes = frozenset(item.source_class for item in group_inputs)
    required_source_classes = frozenset(config.required_source_classes)
    required_source_class_count = _count_decimal(len(required_source_classes))
    source_observation_count = _count_decimal(len(group_inputs))
    observed_source_class_count = _count_decimal(len(source_classes))
    missing_source_class_count = _count_decimal(
        len(required_source_classes.difference(source_classes)),
    )
    retrieval_age_seconds = max(
        _duration_seconds(item.retrieved_at, generated_at) for item in group_inputs
    )
    retrieval_freshness_score = _capped_ratio(
        retrieval_age_seconds,
        config.freshness_block_age_seconds,
    )
    parse_success_count = _sum_decimal(
        tuple(item.parse_success_count for item in group_inputs),
    )
    parse_failure_count = _sum_decimal(
        tuple(item.parse_failure_count for item in group_inputs),
    )
    parse_attempt_count = _sum_decimal(
        (parse_success_count, parse_failure_count),
    )
    parse_reliability_score = _ratio(parse_success_count, parse_attempt_count)
    contradiction_count = _sum_decimal(
        tuple(item.contradiction_count for item in group_inputs),
    )
    contradiction_pressure_score = _capped_ratio(
        contradiction_count,
        observed_source_class_count,
    )
    retry_backlog_count = _sum_decimal(
        tuple(item.retry_backlog_count for item in group_inputs),
    )
    retry_backlog_pressure_score = _capped_ratio(
        retry_backlog_count,
        required_source_class_count,
    )
    due_values = tuple(
        item.manual_review_due_at
        for item in group_inputs
        if item.manual_review_due_at is not None
    )
    manual_review_due_at = min(due_values, default=None)
    manual_review_urgency_score = _manual_review_urgency_score(
        manual_review_due_at,
        generated_at=generated_at,
        watch_horizon_seconds=config.manual_review_watch_horizon_seconds,
    )
    reason_codes = _row_reason_codes(
        missing_source_class_count=missing_source_class_count,
        retrieval_age_seconds=retrieval_age_seconds,
        parse_reliability_score=parse_reliability_score,
        contradiction_pressure_score=contradiction_pressure_score,
        retry_backlog_pressure_score=retry_backlog_pressure_score,
        manual_review_due_at=manual_review_due_at,
        manual_review_urgency_score=manual_review_urgency_score,
        generated_at=generated_at,
        config=config,
    )
    return ResearchSourceCrossCheckRetrievalGapReportRow(
        review_bucket=review_bucket,
        required_source_class_count=required_source_class_count,
        source_observation_count=source_observation_count,
        observed_source_class_count=observed_source_class_count,
        missing_corroborating_source_class_count=missing_source_class_count,
        retrieval_age_seconds=retrieval_age_seconds,
        retrieval_freshness_score=retrieval_freshness_score,
        parse_success_count=parse_success_count,
        parse_failure_count=parse_failure_count,
        parse_attempt_count=parse_attempt_count,
        parse_reliability_score=parse_reliability_score,
        contradiction_count=contradiction_count,
        contradiction_pressure_score=contradiction_pressure_score,
        retry_backlog_count=retry_backlog_count,
        retry_backlog_pressure_score=retry_backlog_pressure_score,
        manual_review_due_at=manual_review_due_at,
        manual_review_urgency_score=manual_review_urgency_score,
        gap_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_reason_codes(
    *,
    missing_source_class_count: Decimal,
    retrieval_age_seconds: Decimal,
    parse_reliability_score: Decimal,
    contradiction_pressure_score: Decimal,
    retry_backlog_pressure_score: Decimal,
    manual_review_due_at: datetime | None,
    manual_review_urgency_score: Decimal,
    generated_at: datetime,
    config: ResearchSourceCrossCheckRetrievalGapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if missing_source_class_count >= _TWO:
        reasons.append("missing_corroborating_source_class_block")
    elif missing_source_class_count > _ZERO:
        reasons.append("missing_corroborating_source_class_watch")
    if retrieval_age_seconds >= config.freshness_block_age_seconds:
        reasons.append("retrieval_freshness_block")
    elif retrieval_age_seconds >= config.freshness_watch_age_seconds:
        reasons.append("retrieval_freshness_watch")
    if parse_reliability_score < config.min_watch_parse_reliability_score:
        reasons.append("parse_reliability_block")
    elif parse_reliability_score < config.min_pass_parse_reliability_score:
        reasons.append("parse_reliability_watch")
    if contradiction_pressure_score >= config.contradiction_block_threshold:
        reasons.append("contradiction_pressure_block")
    elif contradiction_pressure_score >= config.contradiction_watch_threshold:
        reasons.append("contradiction_pressure_watch")
    if retry_backlog_pressure_score >= config.retry_backlog_block_threshold:
        reasons.append("retry_backlog_block")
    elif retry_backlog_pressure_score >= config.retry_backlog_watch_threshold:
        reasons.append("retry_backlog_watch")
    if manual_review_due_at is not None and manual_review_due_at <= generated_at:
        reasons.append("manual_review_urgency_block")
    elif manual_review_urgency_score > _ZERO:
        reasons.append("manual_review_urgency_watch")
    if not reasons:
        reasons.append(_PASS_REASON)
    return _ordered_reason_codes(reasons)


def _manual_review_urgency_score(
    manual_review_due_at: datetime | None,
    *,
    generated_at: datetime,
    watch_horizon_seconds: Decimal,
) -> Decimal:
    if manual_review_due_at is None:
        return _ZERO
    if manual_review_due_at <= generated_at:
        return _ONE
    seconds_remaining = _duration_seconds(generated_at, manual_review_due_at)
    if seconds_remaining >= watch_horizon_seconds:
        return _ZERO
    return _normalize_probability(
        "manual_review_urgency_score",
        _ONE - _ratio(seconds_remaining, watch_horizon_seconds),
    )


def _row_sort_key(
    row: ResearchSourceCrossCheckRetrievalGapReportRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_RANK[row.gap_status],
        -row.manual_review_urgency_score,
        -row.retrieval_freshness_score,
        row.parse_reliability_score,
        -row.contradiction_pressure_score,
        -row.retry_backlog_pressure_score,
        row.review_bucket,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchSourceCrossCheckRetrievalGapReportRow, ...],
) -> str:
    if any(row.gap_status == "block" for row in rows):
        return "block"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceCrossCheckRetrievalGapReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_PASS_REASON,)
    return _ordered_reason_codes(
        reason_code for row in rows for reason_code in row.reason_codes
    )


def _validate_report_row(
    row: ResearchSourceCrossCheckRetrievalGapReportRow,
) -> None:
    if row.source_observation_count <= _ZERO:
        raise ValueError("source_observation_count must be positive for a report row")
    if row.observed_source_class_count != row.source_observation_count:
        raise ValueError(
            "observed_source_class_count must match source_observation_count",
        )
    if (
        row.missing_corroborating_source_class_count
        > row.required_source_class_count
    ):
        raise ValueError(
            "missing_corroborating_source_class_count must not exceed required count",
        )
    expected_attempt_count = _sum_decimal(
        (row.parse_success_count, row.parse_failure_count),
    )
    if row.parse_attempt_count != expected_attempt_count:
        raise ValueError("parse_attempt_count must match parse counts")
    if row.parse_reliability_score != _ratio(
        row.parse_success_count,
        row.parse_attempt_count,
    ):
        raise ValueError("parse_reliability_score must match parse counts")
    if row.contradiction_pressure_score != _capped_ratio(
        row.contradiction_count,
        row.observed_source_class_count,
    ):
        raise ValueError(
            "contradiction_pressure_score must match contradiction and source counts",
        )
    if row.retry_backlog_pressure_score != _capped_ratio(
        row.retry_backlog_count,
        row.required_source_class_count,
    ):
        raise ValueError(
            "retry_backlog_pressure_score must match backlog and required counts",
        )
    if row.manual_review_due_at is None and row.manual_review_urgency_score != _ZERO:
        raise ValueError(
            "manual_review_urgency_score must be zero without a review due time",
        )
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.gap_status != expected_status:
        raise ValueError("gap_status must match reason_codes")
    if row.gap_status == "pass":
        if row.reason_codes != (_PASS_REASON,):
            raise ValueError("passing rows must use the pass reason code")
    elif _PASS_REASON in row.reason_codes:
        raise ValueError("non-passing rows must not use the pass reason code")


def _validate_report_consistency(
    report: ResearchSourceCrossCheckRetrievalGapReport,
) -> None:
    rows = report.rows
    expected_values: dict[str, object] = {
        "review_bucket_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(
            sum(1 for row in rows if row.gap_status == "pass"),
        ),
        "watch_count": _count_decimal(
            sum(1 for row in rows if row.gap_status == "watch"),
        ),
        "block_count": _count_decimal(
            sum(1 for row in rows if row.gap_status == "block"),
        ),
        "source_observation_count": _sum_decimal(
            tuple(row.source_observation_count for row in rows),
        ),
        "missing_corroborating_source_class_count": _sum_decimal(
            tuple(
                row.missing_corroborating_source_class_count for row in rows
            ),
        ),
        "max_retrieval_age_seconds": max(
            (row.retrieval_age_seconds for row in rows),
            default=_ZERO,
        ),
        "average_parse_reliability_score": _average_decimal(
            tuple(row.parse_reliability_score for row in rows),
        ),
        "max_contradiction_pressure_score": max(
            (row.contradiction_pressure_score for row in rows),
            default=_ZERO,
        ),
        "retry_backlog_count": _sum_decimal(
            tuple(row.retry_backlog_count for row in rows),
        ),
        "max_manual_review_urgency_score": max(
            (row.manual_review_urgency_score for row in rows),
            default=_ZERO,
        ),
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    expected_action = _REVIEW_ACTION_BY_STATUS[report.report_status]
    if report.review_action != expected_action:
        raise ValueError("review_action must match report_status")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic severity ordering")
    review_buckets = tuple(row.review_bucket for row in rows)
    if len(set(review_buckets)) != len(review_buckets):
        raise ValueError("rows must have unique review_bucket values")


def _verify_report_digest(
    report: ResearchSourceCrossCheckRetrievalGapReport,
) -> None:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_payload(unsigned_payload) != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_and_reconstruct_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceCrossCheckRetrievalGapReport:
    _require_exact_payload_keys("report payload", payload, _REPORT_PAYLOAD_KEYS)
    _reject_unsafe_public_payload("report payload", payload)
    _require_true_payload_flag("paper_only", payload["paper_only"])
    _require_true_payload_flag("report_only", payload["report_only"])
    _require_true_payload_flag("readonly", payload["readonly"])
    digest = payload["derived_validation_digest"]
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_payload(unsigned_payload) != digest:
        raise ValueError("derived_validation_digest does not match report payload")

    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list in the public payload")
    rows = tuple(_report_row_from_payload(value) for value in rows_value)
    reason_codes = _reason_codes_from_payload(
        "reason_codes",
        payload["reason_codes"],
    )
    return ResearchSourceCrossCheckRetrievalGapReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_identifier_from_payload(
            "config_version",
            payload["config_version"],
        ),
        report_status=_member_from_payload(
            "report_status",
            payload["report_status"],
            _STATUSES,
        ),
        review_action=_member_from_payload(
            "review_action",
            payload["review_action"],
            tuple(_REVIEW_ACTION_BY_STATUS.values()),
        ),
        review_bucket_count=_count_from_payload(
            "review_bucket_count",
            payload["review_bucket_count"],
        ),
        pass_count=_count_from_payload("pass_count", payload["pass_count"]),
        watch_count=_count_from_payload("watch_count", payload["watch_count"]),
        block_count=_count_from_payload("block_count", payload["block_count"]),
        source_observation_count=_count_from_payload(
            "source_observation_count",
            payload["source_observation_count"],
        ),
        missing_corroborating_source_class_count=_count_from_payload(
            "missing_corroborating_source_class_count",
            payload["missing_corroborating_source_class_count"],
        ),
        max_retrieval_age_seconds=_nonnegative_decimal_from_payload(
            "max_retrieval_age_seconds",
            payload["max_retrieval_age_seconds"],
        ),
        average_parse_reliability_score=_probability_from_payload(
            "average_parse_reliability_score",
            payload["average_parse_reliability_score"],
        ),
        max_contradiction_pressure_score=_probability_from_payload(
            "max_contradiction_pressure_score",
            payload["max_contradiction_pressure_score"],
        ),
        retry_backlog_count=_count_from_payload(
            "retry_backlog_count",
            payload["retry_backlog_count"],
        ),
        max_manual_review_urgency_score=_probability_from_payload(
            "max_manual_review_urgency_score",
            payload["max_manual_review_urgency_score"],
        ),
        rows=rows,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
        paper_only=_require_true_payload_flag("paper_only", payload["paper_only"]),
        report_only=_require_true_payload_flag("report_only", payload["report_only"]),
        readonly=_require_true_payload_flag("readonly", payload["readonly"]),
    )


def _report_row_from_payload(
    value: object,
) -> ResearchSourceCrossCheckRetrievalGapReportRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_payload_keys("row payload", value, _ROW_PAYLOAD_KEYS)
    return ResearchSourceCrossCheckRetrievalGapReportRow(
        review_bucket=_identifier_from_payload(
            "review_bucket",
            value["review_bucket"],
        ),
        required_source_class_count=_positive_count_from_payload(
            "required_source_class_count",
            value["required_source_class_count"],
        ),
        source_observation_count=_count_from_payload(
            "source_observation_count",
            value["source_observation_count"],
        ),
        observed_source_class_count=_count_from_payload(
            "observed_source_class_count",
            value["observed_source_class_count"],
        ),
        missing_corroborating_source_class_count=_count_from_payload(
            "missing_corroborating_source_class_count",
            value["missing_corroborating_source_class_count"],
        ),
        retrieval_age_seconds=_nonnegative_decimal_from_payload(
            "retrieval_age_seconds",
            value["retrieval_age_seconds"],
        ),
        retrieval_freshness_score=_probability_from_payload(
            "retrieval_freshness_score",
            value["retrieval_freshness_score"],
        ),
        parse_success_count=_count_from_payload(
            "parse_success_count",
            value["parse_success_count"],
        ),
        parse_failure_count=_count_from_payload(
            "parse_failure_count",
            value["parse_failure_count"],
        ),
        parse_attempt_count=_count_from_payload(
            "parse_attempt_count",
            value["parse_attempt_count"],
        ),
        parse_reliability_score=_probability_from_payload(
            "parse_reliability_score",
            value["parse_reliability_score"],
        ),
        contradiction_count=_count_from_payload(
            "contradiction_count",
            value["contradiction_count"],
        ),
        contradiction_pressure_score=_probability_from_payload(
            "contradiction_pressure_score",
            value["contradiction_pressure_score"],
        ),
        retry_backlog_count=_count_from_payload(
            "retry_backlog_count",
            value["retry_backlog_count"],
        ),
        retry_backlog_pressure_score=_probability_from_payload(
            "retry_backlog_pressure_score",
            value["retry_backlog_pressure_score"],
        ),
        manual_review_due_at=_optional_datetime_from_payload(
            "manual_review_due_at",
            value["manual_review_due_at"],
        ),
        manual_review_urgency_score=_probability_from_payload(
            "manual_review_urgency_score",
            value["manual_review_urgency_score"],
        ),
        gap_status=_member_from_payload(
            "gap_status",
            value["gap_status"],
            _STATUSES,
        ),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            value["reason_codes"],
        ),
        paper_only=_require_true_payload_flag("paper_only", value["paper_only"]),
        report_only=_require_true_payload_flag(
            "report_only",
            value["report_only"],
        ),
        readonly=_require_true_payload_flag("readonly", value["readonly"]),
    )


def _normalize_input_rows(
    input_rows: Iterable[ResearchSourceCrossCheckRetrievalGapInputRow],
) -> tuple[ResearchSourceCrossCheckRetrievalGapInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable of input rows")
    try:
        normalized = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable of input rows") from exc
    for input_row in normalized:
        if type(input_row) is not ResearchSourceCrossCheckRetrievalGapInputRow:
            raise ValueError(
                "input_rows must contain exactly "
                "ResearchSourceCrossCheckRetrievalGapInputRow",
            )
    return normalized


def _normalize_report_rows(
    rows: object,
) -> tuple[ResearchSourceCrossCheckRetrievalGapReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceCrossCheckRetrievalGapReportRow:
            raise ValueError(
                "rows must contain exactly ResearchSourceCrossCheckRetrievalGapReportRow",
            )
    return rows


def _normalize_required_source_classes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("required_source_classes must be a tuple")
    if not value:
        raise ValueError("required_source_classes must be non-empty")
    normalized = tuple(
        _require_public_identifier("required_source_classes", item) for item in value
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError("required_source_classes must be unique")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != _ordered_reason_codes(normalized):
        raise ValueError(f"{field_name} must use canonical ordering")
    return normalized


def _ordered_reason_codes(reasons: Iterable[str]) -> tuple[str, ...]:
    present = frozenset(reasons)
    unknown = present.difference(_REASON_CODE_ORDER)
    if unknown:
        raise ValueError("reason_codes contain an unsupported value")
    return tuple(reason for reason in _REASON_CODE_ORDER if reason in present)


def _require_reason_code(field_name: str, value: object) -> str:
    normalized = _require_public_identifier(field_name, value)
    if normalized not in _REASON_CODE_ORDER:
        raise ValueError(f"{field_name} must contain supported reason codes")
    return normalized


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool for {label}")
        if flag is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _duration_seconds(start_at: datetime, end_at: datetime) -> Decimal:
    delta = end_at - start_at
    with localcontext(_DECIMAL_CONTEXT):
        value = (
            Decimal(delta.days) * _SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
        )
    return _normalize_nonnegative_decimal("duration_seconds", value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if decimal_value == _ZERO:
        return _ZERO
    return _quantize(field_name, decimal_value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(field_name, decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value == _ZERO:
        return _ZERO
    return _quantize(field_name, decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    if decimal_value == _ZERO:
        return _ZERO
    return _quantize(field_name, decimal_value)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_QUANTUM)
    except DecimalException as exc:
        raise ValueError(f"{field_name} cannot be represented deterministically") from exc


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize("count", Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        summed = sum(values, _ZERO)
    return _normalize_nonnegative_decimal("sum", summed)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        average = sum(values, _ZERO) / Decimal(len(values))
    return _normalize_probability("average", average)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        ratio = numerator / denominator
    return _normalize_nonnegative_decimal("ratio", ratio)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return min(_ONE, _ratio(numerator, denominator))


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _copy_json_value(value: object) -> Any:
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload must contain only JSON-ready values")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            if any(
                fragment in lowered_key for fragment in _UNSAFE_PUBLIC_FRAGMENTS
            ):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _require_exact_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if set(value) != set(expected_keys):
        raise ValueError(f"{label} must contain exactly the supported fields")


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not _PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a six-place decimal string")
    try:
        return Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc


def _count_from_payload(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        _decimal_from_payload(field_name, value),
    )


def _positive_count_from_payload(field_name: str, value: object) -> Decimal:
    return _normalize_positive_count(
        field_name,
        _decimal_from_payload(field_name, value),
    )


def _nonnegative_decimal_from_payload(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(
        field_name,
        _decimal_from_payload(field_name, value),
    )


def _probability_from_payload(field_name: str, value: object) -> Decimal:
    return _normalize_probability(
        field_name,
        _decimal_from_payload(field_name, value),
    )


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must use canonical UTC formatting")
    return normalized


def _optional_datetime_from_payload(
    field_name: str,
    value: object,
) -> datetime | None:
    if value is None:
        return None
    return _datetime_from_payload(field_name, value)


def _identifier_from_payload(field_name: str, value: object) -> str:
    return _require_public_identifier(field_name, value)


def _member_from_payload(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    return _require_member(field_name, value, allowed_values)


def _reason_codes_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list in the public payload")
    return _normalize_reason_codes(field_name, tuple(value))


def _require_true_payload_flag(field_name: str, value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{field_name} must be True in the public payload")
    return value
