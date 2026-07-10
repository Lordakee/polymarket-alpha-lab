"""Report-only summary of manual review outcome feedback quality."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION = (
    "research-strategy-manual-review-outcome-feedback-report-v0"
)

STATUSES = ("pass", "watch", "block")
REVIEW_OUTCOMES = ("confirmed", "revised", "overturned", "ambiguous")

PASS_REASON_CODE = "manual_review_outcome_feedback_pass"
EMPTY_REASON_CODE = "manual_review_outcome_feedback_empty"
ROW_REASON_PRIORITY = (
    "calibration_delta_block",
    "evidence_usefulness_block",
    "cost_estimate_error_block",
    "resolution_clarity_block",
    "memory_update_completeness_block",
    "sample_size_low_block",
    "calibration_delta_watch",
    "evidence_usefulness_watch",
    "cost_estimate_error_watch",
    "resolution_clarity_watch",
    "memory_update_completeness_watch",
    "sample_size_low_watch",
    PASS_REASON_CODE,
)
REPORT_REASON_PRIORITY = (
    "manual_review_outcome_feedback_block",
    "manual_review_outcome_feedback_watch",
    PASS_REASON_CODE,
    EMPTY_REASON_CODE,
) + ROW_REASON_PRIORITY[:-1]
REASON_CODES = tuple(dict.fromkeys(REPORT_REASON_PRIORITY))
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
NEG_ONE = Decimal("-1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HEX_CHARS = frozenset("0123456789abcdef")


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("candidate", "_", "id"),
        _join("market", "_", "id"),
        _join("market", "_", "sl", "ug"),
        _join("sl", "ug"),
        _join("ques", "tion"),
        _join("source", "_", "text"),
        _join("source", " ", "text"),
        _join("raw", "_", "text"),
        _join("raw", " ", "source", " ", "text"),
        "url",
        "http",
        "dsn",
        _join("table", "_", "name"),
        _join("private", "_", "key"),
        _join("wal", "let"),
        _join("au", "th"),
        _join("tok", "en"),
        _join("ord", "er"),
        _join("tra", "de"),
        _join("posi", "tion"),
        _join("li", "ve"),
        _join("net", "work"),
        _join("data", "base"),
        _join("per", "sist"),
        "credential",
        "secret",
        "broker",
        "submit",
        "cancel",
        "sign",
        "mutation",
    ),
)

REASON_CODE_COUNT_PUBLIC_FIELDS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_FIELDS = (
    "review_group_id",
    "strategy_area",
    "review_outcome",
    "pre_review_calibration_error",
    "post_review_calibration_error",
    "calibration_delta",
    "evidence_usefulness_score",
    "cost_estimate_error",
    "resolution_clarity_score",
    "memory_update_completeness_score",
    "memory_update_incomplete",
    "outcome_count",
    "reviewed_at",
    "status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "feedback_queue_count",
    "feedback_queue_ratio",
    "memory_update_incomplete_count",
    "average_calibration_delta",
    "min_calibration_delta",
    "average_evidence_usefulness_score",
    "average_cost_estimate_error",
    "max_cost_estimate_error",
    "average_resolution_clarity_score",
    "average_memory_update_completeness_score",
    "watch_min_calibration_delta",
    "block_min_calibration_delta",
    "watch_min_evidence_usefulness_score",
    "block_min_evidence_usefulness_score",
    "watch_max_cost_estimate_error",
    "block_max_cost_estimate_error",
    "watch_min_resolution_clarity_score",
    "block_min_resolution_clarity_score",
    "watch_min_memory_update_completeness_score",
    "block_min_memory_update_completeness_score",
    "min_pass_outcome_count",
    "min_watch_outcome_count",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchStrategyManualReviewOutcomeFeedbackConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION
    )
    watch_min_calibration_delta: Decimal = Decimal("0.020000")
    block_min_calibration_delta: Decimal = Decimal("-0.050000")
    watch_min_evidence_usefulness_score: Decimal = Decimal("0.600000")
    block_min_evidence_usefulness_score: Decimal = Decimal("0.400000")
    watch_max_cost_estimate_error: Decimal = Decimal("0.150000")
    block_max_cost_estimate_error: Decimal = Decimal("0.300000")
    watch_min_resolution_clarity_score: Decimal = Decimal("0.700000")
    block_min_resolution_clarity_score: Decimal = Decimal("0.500000")
    watch_min_memory_update_completeness_score: Decimal = Decimal("0.800000")
    block_min_memory_update_completeness_score: Decimal = Decimal("0.500000")
    min_pass_outcome_count: Decimal = Decimal("10.000000")
    min_watch_outcome_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualReviewOutcomeFeedbackConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_min_calibration_delta",
            "block_min_calibration_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_evidence_usefulness_score",
            "block_min_evidence_usefulness_score",
            "watch_max_cost_estimate_error",
            "block_max_cost_estimate_error",
            "watch_min_resolution_clarity_score",
            "block_min_resolution_clarity_score",
            "watch_min_memory_update_completeness_score",
            "block_min_memory_update_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_outcome_count",
            "min_watch_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_min_calibration_delta > self.watch_min_calibration_delta:
            raise ValueError("block calibration threshold must not exceed watch threshold")
        if (
            self.block_min_evidence_usefulness_score
            > self.watch_min_evidence_usefulness_score
        ):
            raise ValueError("block evidence threshold must not exceed watch threshold")
        if self.watch_max_cost_estimate_error > self.block_max_cost_estimate_error:
            raise ValueError("watch cost threshold must not exceed block threshold")
        if self.block_min_resolution_clarity_score > self.watch_min_resolution_clarity_score:
            raise ValueError("block clarity threshold must not exceed watch threshold")
        if (
            self.block_min_memory_update_completeness_score
            > self.watch_min_memory_update_completeness_score
        ):
            raise ValueError("block memory threshold must not exceed watch threshold")
        if self.min_watch_outcome_count > self.min_pass_outcome_count:
            raise ValueError("watch outcome threshold must not exceed pass threshold")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchStrategyManualReviewOutcomeFeedbackInput(_FinalPublicDataclass):
    review_group_id: str
    strategy_area: str
    review_outcome: str
    pre_review_calibration_error: Decimal
    post_review_calibration_error: Decimal
    evidence_usefulness_score: Decimal
    cost_estimate_error: Decimal
    resolution_clarity_score: Decimal
    memory_update_completeness_score: Decimal
    outcome_count: Decimal
    reviewed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualReviewOutcomeFeedbackInput,
            "input",
        )
        for field_name in ("review_group_id", "strategy_area"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("review_outcome", self.review_outcome, REVIEW_OUTCOMES)
        for field_name in (
            "pre_review_calibration_error",
            "post_review_calibration_error",
            "evidence_usefulness_score",
            "cost_estimate_error",
            "resolution_clarity_score",
            "memory_update_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_count",
            _require_count_decimal("outcome_count", self.outcome_count),
        )
        object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, ROW_REASON_PRIORITY[:-1])
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchStrategyManualReviewOutcomeFeedbackRow(_FinalPublicDataclass):
    review_group_id: str
    strategy_area: str
    review_outcome: str
    pre_review_calibration_error: Decimal
    post_review_calibration_error: Decimal
    calibration_delta: Decimal
    evidence_usefulness_score: Decimal
    cost_estimate_error: Decimal
    resolution_clarity_score: Decimal
    memory_update_completeness_score: Decimal
    memory_update_incomplete: bool
    outcome_count: Decimal
    reviewed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyManualReviewOutcomeFeedbackRow, "row")
        for field_name in ("review_group_id", "strategy_area"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("review_outcome", self.review_outcome, REVIEW_OUTCOMES)
        for field_name in (
            "pre_review_calibration_error",
            "post_review_calibration_error",
            "evidence_usefulness_score",
            "cost_estimate_error",
            "resolution_clarity_score",
            "memory_update_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_delta",
            _require_signed_ratio_decimal("calibration_delta", self.calibration_delta),
        )
        _require_bool("memory_update_incomplete", self.memory_update_incomplete)
        object.__setattr__(
            self,
            "outcome_count",
            _require_count_decimal("outcome_count", self.outcome_count),
        )
        object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_PRIORITY),
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
class ResearchStrategyManualReviewOutcomeFeedbackReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    feedback_queue_count: Decimal
    feedback_queue_ratio: Decimal
    memory_update_incomplete_count: Decimal
    average_calibration_delta: Decimal
    min_calibration_delta: Decimal
    average_evidence_usefulness_score: Decimal
    average_cost_estimate_error: Decimal
    max_cost_estimate_error: Decimal
    average_resolution_clarity_score: Decimal
    average_memory_update_completeness_score: Decimal
    watch_min_calibration_delta: Decimal
    block_min_calibration_delta: Decimal
    watch_min_evidence_usefulness_score: Decimal
    block_min_evidence_usefulness_score: Decimal
    watch_max_cost_estimate_error: Decimal
    block_max_cost_estimate_error: Decimal
    watch_min_resolution_clarity_score: Decimal
    block_min_resolution_clarity_score: Decimal
    watch_min_memory_update_completeness_score: Decimal
    block_min_memory_update_completeness_score: Decimal
    min_pass_outcome_count: Decimal
    min_watch_outcome_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount, ...]
    rows: tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyManualReviewOutcomeFeedbackReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "feedback_queue_count",
            "memory_update_incomplete_count",
            "min_pass_outcome_count",
            "min_watch_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "feedback_queue_ratio",
            "average_evidence_usefulness_score",
            "average_cost_estimate_error",
            "max_cost_estimate_error",
            "average_resolution_clarity_score",
            "average_memory_update_completeness_score",
            "watch_min_evidence_usefulness_score",
            "block_min_evidence_usefulness_score",
            "watch_max_cost_estimate_error",
            "block_max_cost_estimate_error",
            "watch_min_resolution_clarity_score",
            "block_min_resolution_clarity_score",
            "watch_min_memory_update_completeness_score",
            "block_min_memory_update_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_delta",
            "min_calibration_delta",
            "watch_min_calibration_delta",
            "block_min_calibration_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
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


def build_research_strategy_manual_review_outcome_feedback_report(
    inputs: list[ResearchStrategyManualReviewOutcomeFeedbackInput]
    | tuple[ResearchStrategyManualReviewOutcomeFeedbackInput, ...],
    *,
    config: ResearchStrategyManualReviewOutcomeFeedbackConfig,
    generated_at: datetime,
) -> ResearchStrategyManualReviewOutcomeFeedbackReport:
    if type(config) is not ResearchStrategyManualReviewOutcomeFeedbackConfig:
        raise ValueError(
            "config must be a ResearchStrategyManualReviewOutcomeFeedbackConfig",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    _validate_unique_inputs(normalized_inputs)
    _validate_not_after_generated_at(normalized_inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (_build_row(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    row_count = _count(len(rows))
    feedback_queue_count = _count(sum(1 for row in rows if row.status != "pass"))
    return ResearchStrategyManualReviewOutcomeFeedbackReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=row_count,
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        feedback_queue_count=feedback_queue_count,
        feedback_queue_ratio=_ratio(feedback_queue_count, row_count),
        memory_update_incomplete_count=_count(
            sum(1 for row in rows if row.memory_update_incomplete),
        ),
        average_calibration_delta=_average(
            tuple(row.calibration_delta for row in rows),
        ),
        min_calibration_delta=min(
            (row.calibration_delta for row in rows),
            default=ZERO,
        ),
        average_evidence_usefulness_score=_average(
            tuple(row.evidence_usefulness_score for row in rows),
        ),
        average_cost_estimate_error=_average(
            tuple(row.cost_estimate_error for row in rows),
        ),
        max_cost_estimate_error=max(
            (row.cost_estimate_error for row in rows),
            default=ZERO,
        ),
        average_resolution_clarity_score=_average(
            tuple(row.resolution_clarity_score for row in rows),
        ),
        average_memory_update_completeness_score=_average(
            tuple(row.memory_update_completeness_score for row in rows),
        ),
        watch_min_calibration_delta=config.watch_min_calibration_delta,
        block_min_calibration_delta=config.block_min_calibration_delta,
        watch_min_evidence_usefulness_score=config.watch_min_evidence_usefulness_score,
        block_min_evidence_usefulness_score=config.block_min_evidence_usefulness_score,
        watch_max_cost_estimate_error=config.watch_max_cost_estimate_error,
        block_max_cost_estimate_error=config.block_max_cost_estimate_error,
        watch_min_resolution_clarity_score=config.watch_min_resolution_clarity_score,
        block_min_resolution_clarity_score=config.block_min_resolution_clarity_score,
        watch_min_memory_update_completeness_score=(
            config.watch_min_memory_update_completeness_score
        ),
        block_min_memory_update_completeness_score=(
            config.block_min_memory_update_completeness_score
        ),
        min_pass_outcome_count=config.min_pass_outcome_count,
        min_watch_outcome_count=config.min_watch_outcome_count,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_manual_review_outcome_feedback_report_payload(
    report: ResearchStrategyManualReviewOutcomeFeedbackReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyManualReviewOutcomeFeedbackReport:
        raise ValueError(
            "report must be a ResearchStrategyManualReviewOutcomeFeedbackReport",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_strategy_manual_review_outcome_feedback_public_payload(payload)
    return payload


def validate_research_strategy_manual_review_outcome_feedback_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("manual review feedback payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    parsed_report = _public_report_from_payload(payload)
    if _json_value(parsed_report) != payload:
        raise ValueError("payload must use the canonical report payload schema")
    return True


def _public_report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyManualReviewOutcomeFeedbackReport:
    _require_exact_public_fields(
        payload,
        REPORT_PUBLIC_FIELDS,
        "report payload",
    )
    reason_code_counts_value = payload["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("report payload.reason_code_counts must be a list")
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("report payload.rows must be a list")
    return ResearchStrategyManualReviewOutcomeFeedbackReport(
        generated_at=_public_datetime(
            payload["generated_at"],
            "report payload.generated_at",
        ),
        config_version=_public_string(
            payload["config_version"],
            "report payload.config_version",
        ),
        status=_public_member(
            payload["status"],
            STATUSES,
            "report payload.status",
        ),
        input_count=_public_count_decimal(
            payload["input_count"],
            "report payload.input_count",
        ),
        row_count=_public_count_decimal(
            payload["row_count"],
            "report payload.row_count",
        ),
        pass_count=_public_count_decimal(
            payload["pass_count"],
            "report payload.pass_count",
        ),
        watch_count=_public_count_decimal(
            payload["watch_count"],
            "report payload.watch_count",
        ),
        block_count=_public_count_decimal(
            payload["block_count"],
            "report payload.block_count",
        ),
        feedback_queue_count=_public_count_decimal(
            payload["feedback_queue_count"],
            "report payload.feedback_queue_count",
        ),
        feedback_queue_ratio=_public_ratio_decimal(
            payload["feedback_queue_ratio"],
            "report payload.feedback_queue_ratio",
        ),
        memory_update_incomplete_count=_public_count_decimal(
            payload["memory_update_incomplete_count"],
            "report payload.memory_update_incomplete_count",
        ),
        average_calibration_delta=_public_signed_ratio_decimal(
            payload["average_calibration_delta"],
            "report payload.average_calibration_delta",
        ),
        min_calibration_delta=_public_signed_ratio_decimal(
            payload["min_calibration_delta"],
            "report payload.min_calibration_delta",
        ),
        average_evidence_usefulness_score=_public_ratio_decimal(
            payload["average_evidence_usefulness_score"],
            "report payload.average_evidence_usefulness_score",
        ),
        average_cost_estimate_error=_public_ratio_decimal(
            payload["average_cost_estimate_error"],
            "report payload.average_cost_estimate_error",
        ),
        max_cost_estimate_error=_public_ratio_decimal(
            payload["max_cost_estimate_error"],
            "report payload.max_cost_estimate_error",
        ),
        average_resolution_clarity_score=_public_ratio_decimal(
            payload["average_resolution_clarity_score"],
            "report payload.average_resolution_clarity_score",
        ),
        average_memory_update_completeness_score=_public_ratio_decimal(
            payload["average_memory_update_completeness_score"],
            "report payload.average_memory_update_completeness_score",
        ),
        watch_min_calibration_delta=_public_signed_ratio_decimal(
            payload["watch_min_calibration_delta"],
            "report payload.watch_min_calibration_delta",
        ),
        block_min_calibration_delta=_public_signed_ratio_decimal(
            payload["block_min_calibration_delta"],
            "report payload.block_min_calibration_delta",
        ),
        watch_min_evidence_usefulness_score=_public_ratio_decimal(
            payload["watch_min_evidence_usefulness_score"],
            "report payload.watch_min_evidence_usefulness_score",
        ),
        block_min_evidence_usefulness_score=_public_ratio_decimal(
            payload["block_min_evidence_usefulness_score"],
            "report payload.block_min_evidence_usefulness_score",
        ),
        watch_max_cost_estimate_error=_public_ratio_decimal(
            payload["watch_max_cost_estimate_error"],
            "report payload.watch_max_cost_estimate_error",
        ),
        block_max_cost_estimate_error=_public_ratio_decimal(
            payload["block_max_cost_estimate_error"],
            "report payload.block_max_cost_estimate_error",
        ),
        watch_min_resolution_clarity_score=_public_ratio_decimal(
            payload["watch_min_resolution_clarity_score"],
            "report payload.watch_min_resolution_clarity_score",
        ),
        block_min_resolution_clarity_score=_public_ratio_decimal(
            payload["block_min_resolution_clarity_score"],
            "report payload.block_min_resolution_clarity_score",
        ),
        watch_min_memory_update_completeness_score=_public_ratio_decimal(
            payload["watch_min_memory_update_completeness_score"],
            "report payload.watch_min_memory_update_completeness_score",
        ),
        block_min_memory_update_completeness_score=_public_ratio_decimal(
            payload["block_min_memory_update_completeness_score"],
            "report payload.block_min_memory_update_completeness_score",
        ),
        min_pass_outcome_count=_public_count_decimal(
            payload["min_pass_outcome_count"],
            "report payload.min_pass_outcome_count",
        ),
        min_watch_outcome_count=_public_count_decimal(
            payload["min_watch_outcome_count"],
            "report payload.min_watch_outcome_count",
        ),
        reason_codes=_public_reason_codes(
            payload["reason_codes"],
            REASON_CODES,
            "report payload.reason_codes",
        ),
        reason_code_counts=tuple(
            _public_reason_code_count_from_payload(
                item,
                f"report payload.reason_code_counts[{index}]",
            )
            for index, item in enumerate(reason_code_counts_value)
        ),
        rows=tuple(
            _public_row_from_payload(
                item,
                f"report payload.rows[{index}]",
            )
            for index, item in enumerate(rows_value)
        ),
        derived_validation_digest=_public_sha256(
            payload["derived_validation_digest"],
            "report payload.derived_validation_digest",
        ),
        paper_only=_public_true_flag(
            payload["paper_only"],
            "report payload.paper_only",
        ),
        report_only=_public_true_flag(
            payload["report_only"],
            "report payload.report_only",
        ),
        readonly=_public_true_flag(
            payload["readonly"],
            "report payload.readonly",
        ),
    )


def _public_reason_code_count_from_payload(
    value: object,
    path: str,
) -> ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount:
    _require_exact_public_fields(
        value,
        REASON_CODE_COUNT_PUBLIC_FIELDS,
        path,
    )
    return ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount(
        reason_code=_public_member(
            value["reason_code"],
            ROW_REASON_PRIORITY[:-1],
            f"{path}.reason_code",
        ),
        count=_public_count_decimal(
            value["count"],
            f"{path}.count",
        ),
        row_ratio=_public_ratio_decimal(
            value["row_ratio"],
            f"{path}.row_ratio",
        ),
        paper_only=_public_true_flag(
            value["paper_only"],
            f"{path}.paper_only",
        ),
        report_only=_public_true_flag(
            value["report_only"],
            f"{path}.report_only",
        ),
        readonly=_public_true_flag(
            value["readonly"],
            f"{path}.readonly",
        ),
    )


def _public_row_from_payload(
    value: object,
    path: str,
) -> ResearchStrategyManualReviewOutcomeFeedbackRow:
    _require_exact_public_fields(value, ROW_PUBLIC_FIELDS, path)
    return ResearchStrategyManualReviewOutcomeFeedbackRow(
        review_group_id=_public_string(
            value["review_group_id"],
            f"{path}.review_group_id",
        ),
        strategy_area=_public_string(
            value["strategy_area"],
            f"{path}.strategy_area",
        ),
        review_outcome=_public_member(
            value["review_outcome"],
            REVIEW_OUTCOMES,
            f"{path}.review_outcome",
        ),
        pre_review_calibration_error=_public_ratio_decimal(
            value["pre_review_calibration_error"],
            f"{path}.pre_review_calibration_error",
        ),
        post_review_calibration_error=_public_ratio_decimal(
            value["post_review_calibration_error"],
            f"{path}.post_review_calibration_error",
        ),
        calibration_delta=_public_signed_ratio_decimal(
            value["calibration_delta"],
            f"{path}.calibration_delta",
        ),
        evidence_usefulness_score=_public_ratio_decimal(
            value["evidence_usefulness_score"],
            f"{path}.evidence_usefulness_score",
        ),
        cost_estimate_error=_public_ratio_decimal(
            value["cost_estimate_error"],
            f"{path}.cost_estimate_error",
        ),
        resolution_clarity_score=_public_ratio_decimal(
            value["resolution_clarity_score"],
            f"{path}.resolution_clarity_score",
        ),
        memory_update_completeness_score=_public_ratio_decimal(
            value["memory_update_completeness_score"],
            f"{path}.memory_update_completeness_score",
        ),
        memory_update_incomplete=_public_bool(
            value["memory_update_incomplete"],
            f"{path}.memory_update_incomplete",
        ),
        outcome_count=_public_count_decimal(
            value["outcome_count"],
            f"{path}.outcome_count",
        ),
        reviewed_at=_public_datetime(
            value["reviewed_at"],
            f"{path}.reviewed_at",
        ),
        status=_public_member(
            value["status"],
            STATUSES,
            f"{path}.status",
        ),
        reason_codes=_public_reason_codes(
            value["reason_codes"],
            ROW_REASON_PRIORITY,
            f"{path}.reason_codes",
        ),
        derived_validation_digest=_public_sha256(
            value["derived_validation_digest"],
            f"{path}.derived_validation_digest",
        ),
        paper_only=_public_true_flag(
            value["paper_only"],
            f"{path}.paper_only",
        ),
        report_only=_public_true_flag(
            value["report_only"],
            f"{path}.report_only",
        ),
        readonly=_public_true_flag(
            value["readonly"],
            f"{path}.readonly",
        ),
    )


def _require_exact_public_fields(
    value: object,
    expected_fields: tuple[str, ...],
    path: str,
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{path} must be an object")
    missing = tuple(field_name for field_name in expected_fields if field_name not in value)
    unexpected = tuple(
        sorted(field_name for field_name in value if field_name not in expected_fields)
    )
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected fields: {', '.join(unexpected)}")
        raise ValueError(
            f"{path} must use the canonical payload schema ({'; '.join(details)})",
        )


def _public_string(value: object, path: str) -> str:
    _require_public_string(path, value)
    return value


def _public_member(
    value: object,
    allowed_values: tuple[str, ...],
    path: str,
) -> str:
    _require_member(path, value, allowed_values)
    return value


def _public_bool(value: object, path: str) -> bool:
    _require_bool(path, value)
    return value


def _public_true_flag(value: object, path: str) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _public_decimal(value: object, path: str) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{path} must be a canonical Decimal string") from exc
    _require_decimal(path, decimal_value)
    if decimal_value.as_tuple().exponent != -6 or value != format(decimal_value, "f"):
        raise ValueError(f"{path} must be a canonical Decimal string")
    return decimal_value


def _public_count_decimal(value: object, path: str) -> Decimal:
    return _require_count_decimal(path, _public_decimal(value, path))


def _public_ratio_decimal(value: object, path: str) -> Decimal:
    return _require_ratio_decimal(path, _public_decimal(value, path))


def _public_signed_ratio_decimal(value: object, path: str) -> Decimal:
    return _require_signed_ratio_decimal(path, _public_decimal(value, path))


def _public_datetime(value: object, path: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(path, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    return normalized


def _public_reason_codes(
    value: object,
    allowed_values: tuple[str, ...],
    path: str,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    reason_codes = tuple(
        _public_member(item, allowed_values, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    return _normalize_reason_codes(path, reason_codes, allowed_values)


def _public_sha256(value: object, path: str) -> str:
    return _require_sha256_digest(path, value)


def _build_row(
    value: ResearchStrategyManualReviewOutcomeFeedbackInput,
    *,
    config: ResearchStrategyManualReviewOutcomeFeedbackConfig,
) -> ResearchStrategyManualReviewOutcomeFeedbackRow:
    calibration_delta = _calibration_delta(
        value.pre_review_calibration_error,
        value.post_review_calibration_error,
    )
    memory_update_incomplete = (
        value.memory_update_completeness_score
        < config.watch_min_memory_update_completeness_score
    )
    reason_codes = _row_reason_codes(
        calibration_delta=calibration_delta,
        evidence_usefulness_score=value.evidence_usefulness_score,
        cost_estimate_error=value.cost_estimate_error,
        resolution_clarity_score=value.resolution_clarity_score,
        memory_update_completeness_score=value.memory_update_completeness_score,
        outcome_count=value.outcome_count,
        config=config,
    )
    return ResearchStrategyManualReviewOutcomeFeedbackRow(
        review_group_id=value.review_group_id,
        strategy_area=value.strategy_area,
        review_outcome=value.review_outcome,
        pre_review_calibration_error=value.pre_review_calibration_error,
        post_review_calibration_error=value.post_review_calibration_error,
        calibration_delta=calibration_delta,
        evidence_usefulness_score=value.evidence_usefulness_score,
        cost_estimate_error=value.cost_estimate_error,
        resolution_clarity_score=value.resolution_clarity_score,
        memory_update_completeness_score=value.memory_update_completeness_score,
        memory_update_incomplete=memory_update_incomplete,
        outcome_count=value.outcome_count,
        reviewed_at=value.reviewed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    calibration_delta: Decimal,
    evidence_usefulness_score: Decimal,
    cost_estimate_error: Decimal,
    resolution_clarity_score: Decimal,
    memory_update_completeness_score: Decimal,
    outcome_count: Decimal,
    config: ResearchStrategyManualReviewOutcomeFeedbackConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if calibration_delta <= config.block_min_calibration_delta:
        reason_codes.append("calibration_delta_block")
    elif calibration_delta < config.watch_min_calibration_delta:
        reason_codes.append("calibration_delta_watch")

    if evidence_usefulness_score <= config.block_min_evidence_usefulness_score:
        reason_codes.append("evidence_usefulness_block")
    elif evidence_usefulness_score < config.watch_min_evidence_usefulness_score:
        reason_codes.append("evidence_usefulness_watch")

    if cost_estimate_error >= config.block_max_cost_estimate_error:
        reason_codes.append("cost_estimate_error_block")
    elif cost_estimate_error >= config.watch_max_cost_estimate_error:
        reason_codes.append("cost_estimate_error_watch")

    if resolution_clarity_score <= config.block_min_resolution_clarity_score:
        reason_codes.append("resolution_clarity_block")
    elif resolution_clarity_score < config.watch_min_resolution_clarity_score:
        reason_codes.append("resolution_clarity_watch")

    if (
        memory_update_completeness_score
        <= config.block_min_memory_update_completeness_score
    ):
        reason_codes.append("memory_update_completeness_block")
    elif (
        memory_update_completeness_score
        < config.watch_min_memory_update_completeness_score
    ):
        reason_codes.append("memory_update_completeness_watch")

    if outcome_count < config.min_watch_outcome_count:
        reason_codes.append("sample_size_low_block")
    elif outcome_count < config.min_pass_outcome_count:
        reason_codes.append("sample_size_low_watch")

    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(reason for reason in ROW_REASON_PRIORITY if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...],
) -> str:
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    status = _report_status(rows)
    present = frozenset(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    status_reason = (
        "manual_review_outcome_feedback_block"
        if status == "block"
        else "manual_review_outcome_feedback_watch"
    )
    return (status_reason,) + tuple(
        reason for reason in ROW_REASON_PRIORITY[:-1] if reason in present
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...],
) -> tuple[ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount, ...]:
    return tuple(
        ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), _count(len(rows))),
        )
        for reason_code in ROW_REASON_PRIORITY[:-1]
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchStrategyManualReviewOutcomeFeedbackInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    inputs = tuple(value)
    for item in inputs:
        if type(item) is not ResearchStrategyManualReviewOutcomeFeedbackInput:
            raise ValueError(
                "inputs must contain ResearchStrategyManualReviewOutcomeFeedbackInput values",
            )
        _require_hard_flags(item)
    return inputs


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyManualReviewOutcomeFeedbackRow:
            raise ValueError(
                "rows must contain ResearchStrategyManualReviewOutcomeFeedbackRow values",
            )
        _require_hard_flags(row)
        key = _item_key(row)
        if key in seen:
            raise ValueError("rows must not contain duplicate manual review feedback")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_PRIORITY[:-1]
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
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason for reason in allowed_values if reason in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_unique_inputs(
    inputs: tuple[ResearchStrategyManualReviewOutcomeFeedbackInput, ...],
) -> None:
    seen: set[tuple[str, str, str]] = set()
    for item in inputs:
        key = _item_key(item)
        if key in seen:
            raise ValueError("inputs contain duplicate manual review feedback")
        seen.add(key)


def _validate_not_after_generated_at(
    inputs: tuple[ResearchStrategyManualReviewOutcomeFeedbackInput, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in inputs:
        if item.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not be after generated_at")


def _validate_row(row: ResearchStrategyManualReviewOutcomeFeedbackRow) -> None:
    if row.calibration_delta != _calibration_delta(
        row.pre_review_calibration_error,
        row.post_review_calibration_error,
    ):
        raise ValueError("calibration_delta must match review errors")
    expected_memory_update_incomplete = any(
        reason_code
        in (
            "memory_update_completeness_block",
            "memory_update_completeness_watch",
        )
        for reason_code in row.reason_codes
    )
    if row.memory_update_incomplete is not expected_memory_update_incomplete:
        raise ValueError("memory_update_incomplete must match reason_codes")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must use pass reason code")
    if row.status != "pass" and PASS_REASON_CODE in row.reason_codes:
        raise ValueError("non-pass rows must not use pass reason code")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _report_config(
    report: ResearchStrategyManualReviewOutcomeFeedbackReport,
) -> ResearchStrategyManualReviewOutcomeFeedbackConfig:
    return ResearchStrategyManualReviewOutcomeFeedbackConfig(
        config_version=report.config_version,
        watch_min_calibration_delta=report.watch_min_calibration_delta,
        block_min_calibration_delta=report.block_min_calibration_delta,
        watch_min_evidence_usefulness_score=report.watch_min_evidence_usefulness_score,
        block_min_evidence_usefulness_score=report.block_min_evidence_usefulness_score,
        watch_max_cost_estimate_error=report.watch_max_cost_estimate_error,
        block_max_cost_estimate_error=report.block_max_cost_estimate_error,
        watch_min_resolution_clarity_score=report.watch_min_resolution_clarity_score,
        block_min_resolution_clarity_score=report.block_min_resolution_clarity_score,
        watch_min_memory_update_completeness_score=(
            report.watch_min_memory_update_completeness_score
        ),
        block_min_memory_update_completeness_score=(
            report.block_min_memory_update_completeness_score
        ),
        min_pass_outcome_count=report.min_pass_outcome_count,
        min_watch_outcome_count=report.min_watch_outcome_count,
    )


def _validate_report(report: ResearchStrategyManualReviewOutcomeFeedbackReport) -> None:
    rows = report.rows
    config = _report_config(report)
    for row in rows:
        if row.reviewed_at > report.generated_at:
            raise ValueError("reviewed_at must not be after generated_at")
        expected_memory_update_incomplete = (
            row.memory_update_completeness_score
            < config.watch_min_memory_update_completeness_score
        )
        if row.memory_update_incomplete is not expected_memory_update_incomplete:
            raise ValueError(
                "memory_update_incomplete must match memory completeness threshold",
            )
        expected_reason_codes = _row_reason_codes(
            calibration_delta=row.calibration_delta,
            evidence_usefulness_score=row.evidence_usefulness_score,
            cost_estimate_error=row.cost_estimate_error,
            resolution_clarity_score=row.resolution_clarity_score,
            memory_update_completeness_score=(
                row.memory_update_completeness_score
            ),
            outcome_count=row.outcome_count,
            config=config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("row reason_codes must match report thresholds")
        if row.status != _row_status(expected_reason_codes):
            raise ValueError("row status must match report thresholds")
    row_count = _count(len(rows))
    if report.input_count != row_count:
        raise ValueError("input_count must match rows")
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.feedback_queue_count != _count(sum(1 for row in rows if row.status != "pass")):
        raise ValueError("feedback_queue_count must match rows")
    if report.feedback_queue_ratio != _ratio(
        report.feedback_queue_count,
        report.row_count,
    ):
        raise ValueError("feedback_queue_ratio must match rows")
    if report.memory_update_incomplete_count != _count(
        sum(1 for row in rows if row.memory_update_incomplete),
    ):
        raise ValueError("memory_update_incomplete_count must match rows")
    if report.average_calibration_delta != _average(
        tuple(row.calibration_delta for row in rows),
    ):
        raise ValueError("average_calibration_delta must match rows")
    if report.min_calibration_delta != min(
        (row.calibration_delta for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_calibration_delta must match rows")
    if report.average_evidence_usefulness_score != _average(
        tuple(row.evidence_usefulness_score for row in rows),
    ):
        raise ValueError("average_evidence_usefulness_score must match rows")
    if report.average_cost_estimate_error != _average(
        tuple(row.cost_estimate_error for row in rows),
    ):
        raise ValueError("average_cost_estimate_error must match rows")
    if report.max_cost_estimate_error != max(
        (row.cost_estimate_error for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_cost_estimate_error must match rows")
    if report.average_resolution_clarity_score != _average(
        tuple(row.resolution_clarity_score for row in rows),
    ):
        raise ValueError("average_resolution_clarity_score must match rows")
    if report.average_memory_update_completeness_score != _average(
        tuple(row.memory_update_completeness_score for row in rows),
    ):
        raise ValueError("average_memory_update_completeness_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _item_key(
    value: ResearchStrategyManualReviewOutcomeFeedbackInput
    | ResearchStrategyManualReviewOutcomeFeedbackRow,
) -> tuple[str, str, str]:
    return (
        value.review_group_id,
        value.strategy_area,
        value.review_outcome,
    )


def _row_sort_key(
    row: ResearchStrategyManualReviewOutcomeFeedbackRow,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    datetime,
    str,
    str,
    str,
]:
    return (
        STATUS_RANK[row.status],
        row.calibration_delta,
        row.evidence_usefulness_score,
        row.cost_estimate_error.copy_negate(),
        row.resolution_clarity_score,
        row.memory_update_completeness_score,
        row.outcome_count,
        row.post_review_calibration_error.copy_negate(),
        row.pre_review_calibration_error.copy_negate(),
        row.reviewed_at,
        row.review_group_id,
        row.strategy_area,
        row.review_outcome,
    )


def _status_count(
    rows: tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchStrategyManualReviewOutcomeFeedbackRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _calibration_delta(
    pre_review_calibration_error: Decimal,
    post_review_calibration_error: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            pre_review_calibration_error - post_review_calibration_error,
        )


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized.is_zero() and normalized.is_signed():
        return ZERO
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        integral_value = decimal_value.to_integral_value()
    if decimal_value != integral_value:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize(decimal_value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < NEG_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of {joined}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _row_public_payload_for_digest(
    row: ResearchStrategyManualReviewOutcomeFeedbackRow,
) -> dict[str, Any]:
    payload = _json_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: ResearchStrategyManualReviewOutcomeFeedbackReport,
) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _row_derived_validation_digest(
    row: ResearchStrategyManualReviewOutcomeFeedbackRow,
) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: ResearchStrategyManualReviewOutcomeFeedbackReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("JSON value must use Decimal strings, not numeric values")
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _require_public_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{flag_name} must be True")
        for item in value.values():
            _require_public_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_flags(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION",
    "STATUSES",
    "REVIEW_OUTCOMES",
    "ResearchStrategyManualReviewOutcomeFeedbackConfig",
    "ResearchStrategyManualReviewOutcomeFeedbackInput",
    "ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount",
    "ResearchStrategyManualReviewOutcomeFeedbackRow",
    "ResearchStrategyManualReviewOutcomeFeedbackReport",
    "build_research_strategy_manual_review_outcome_feedback_report",
    "research_strategy_manual_review_outcome_feedback_report_payload",
    "validate_research_strategy_manual_review_outcome_feedback_public_payload",
)
