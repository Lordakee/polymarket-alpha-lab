from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
from typing import Any, Mapping


DEFAULT_RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_REPORT_CONFIG_VERSION = (
    "research-team-review-feedback-absorption-report-v0"
)
RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_FIELD = "derived_validation_digest"

_PASS_REASON = "review_feedback_absorption_pass"
_EMPTY_REASON = "review_feedback_absorption_empty"
_CORRECTION_BLOCK_REASON = "correction_follow_through_block"
_CORRECTION_WATCH_REASON = "correction_follow_through_watch"
_MEMORY_BLOCK_REASON = "stale_memory_reduction_block"
_MEMORY_WATCH_REASON = "stale_memory_reduction_watch"
_CALIBRATION_BLOCK_REASON = "calibration_movement_block"
_CALIBRATION_WATCH_REASON = "calibration_movement_watch"
_EVIDENCE_BLOCK_REASON = "evidence_reuse_quality_block"
_EVIDENCE_WATCH_REASON = "evidence_reuse_quality_watch"
_PEER_REVIEW_BLOCK_REASON = "peer_review_coverage_block"
_PEER_REVIEW_WATCH_REASON = "peer_review_coverage_watch"
_LATENCY_BLOCK_REASON = "review_latency_block"
_LATENCY_WATCH_REASON = "review_latency_watch"

_REASON_SEQUENCE = (
    _CORRECTION_BLOCK_REASON,
    _CORRECTION_WATCH_REASON,
    _MEMORY_BLOCK_REASON,
    _MEMORY_WATCH_REASON,
    _CALIBRATION_BLOCK_REASON,
    _CALIBRATION_WATCH_REASON,
    _EVIDENCE_BLOCK_REASON,
    _EVIDENCE_WATCH_REASON,
    _PEER_REVIEW_BLOCK_REASON,
    _PEER_REVIEW_WATCH_REASON,
    _LATENCY_BLOCK_REASON,
    _LATENCY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)

_UNSAFE_PUBLIC_HEXES = (
    "63616e646964617465",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "6d61726b65742d736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "75726c",
    "74657874",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
    "64736e",
    "706f7374677265733a2f2f",
    "7461626c655f6e616d65",
    "746f6b656e",
    "736563726574",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "7472616465",
    "74726164696e67",
    "627579",
    "73656c6c",
    "6461746162617365",
    "6c697665",
)
_UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii") for value in _UNSAFE_PUBLIC_HEXES
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_STATUSES",
    "ResearchTeamReviewFeedbackAbsorptionReportConfig",
    "ResearchTeamReviewFeedbackAbsorptionRecord",
    "ResearchTeamReviewFeedbackAbsorptionRow",
    "ResearchTeamReviewFeedbackAbsorptionReasonCodeCount",
    "ResearchTeamReviewFeedbackAbsorptionReport",
    "build_research_team_review_feedback_absorption_report",
    "research_team_review_feedback_absorption_report_digest",
    "research_team_review_feedback_absorption_report_payload",
    "validate_research_team_review_feedback_absorption_public_payload",
)


@dataclass(frozen=True)
class ResearchTeamReviewFeedbackAbsorptionReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_REPORT_CONFIG_VERSION
    )
    min_pass_correction_follow_through_ratio: Decimal = Decimal("0.900000")
    min_watch_correction_follow_through_ratio: Decimal = Decimal("0.750000")
    min_pass_stale_memory_reduction_ratio: Decimal = Decimal("0.750000")
    min_watch_stale_memory_reduction_ratio: Decimal = Decimal("0.500000")
    min_pass_calibration_movement_ratio: Decimal = Decimal("0.600000")
    min_watch_calibration_movement_ratio: Decimal = Decimal("0.300000")
    min_pass_evidence_reuse_quality_score: Decimal = Decimal("0.800000")
    min_watch_evidence_reuse_quality_score: Decimal = Decimal("0.600000")
    min_pass_peer_review_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_peer_review_coverage_ratio: Decimal = Decimal("0.750000")
    review_latency_watch_seconds: Decimal = Decimal("86400.000000")
    review_latency_block_seconds: Decimal = Decimal("259200.000000")
    correction_follow_through_weight: Decimal = Decimal("0.200000")
    stale_memory_reduction_weight: Decimal = Decimal("0.150000")
    calibration_movement_weight: Decimal = Decimal("0.200000")
    evidence_reuse_quality_weight: Decimal = Decimal("0.150000")
    peer_review_coverage_weight: Decimal = Decimal("0.150000")
    review_latency_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewFeedbackAbsorptionReportConfig:
            raise TypeError(
                "ResearchTeamReviewFeedbackAbsorptionReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamReviewFeedbackAbsorptionReportConfig)
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_correction_follow_through_ratio",
            "min_watch_correction_follow_through_ratio",
            "min_pass_stale_memory_reduction_ratio",
            "min_watch_stale_memory_reduction_ratio",
            "min_pass_calibration_movement_ratio",
            "min_watch_calibration_movement_ratio",
            "min_pass_evidence_reuse_quality_score",
            "min_watch_evidence_reuse_quality_score",
            "min_pass_peer_review_coverage_ratio",
            "min_watch_peer_review_coverage_ratio",
            "correction_follow_through_weight",
            "stale_memory_reduction_weight",
            "calibration_movement_weight",
            "evidence_reuse_quality_weight",
            "peer_review_coverage_weight",
            "review_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("review_latency_watch_seconds", "review_latency_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_correction_follow_through_ratio
            <= self.min_watch_correction_follow_through_ratio
        ):
            raise ValueError(
                "min_pass_correction_follow_through_ratio must exceed watch threshold",
            )
        if (
            self.min_pass_stale_memory_reduction_ratio
            <= self.min_watch_stale_memory_reduction_ratio
        ):
            raise ValueError(
                "min_pass_stale_memory_reduction_ratio must exceed watch threshold",
            )
        if self.min_pass_calibration_movement_ratio <= self.min_watch_calibration_movement_ratio:
            raise ValueError("min_pass_calibration_movement_ratio must exceed watch threshold")
        if (
            self.min_pass_evidence_reuse_quality_score
            <= self.min_watch_evidence_reuse_quality_score
        ):
            raise ValueError(
                "min_pass_evidence_reuse_quality_score must exceed watch threshold",
            )
        if self.min_pass_peer_review_coverage_ratio <= self.min_watch_peer_review_coverage_ratio:
            raise ValueError("min_pass_peer_review_coverage_ratio must exceed watch threshold")
        if self.review_latency_block_seconds <= self.review_latency_watch_seconds:
            raise ValueError("review_latency_block_seconds must exceed watch threshold")
        weight_sum = _six(
            self.correction_follow_through_weight
            + self.stale_memory_reduction_weight
            + self.calibration_movement_weight
            + self.evidence_reuse_quality_weight
            + self.peer_review_coverage_weight
            + self.review_latency_weight,
        )
        if weight_sum != _ONE_SCORE:
            raise ValueError("review feedback absorption weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewFeedbackAbsorptionRecord:
    team_ref: str
    review_stream_ref: str
    feedback_cycle_digest: str
    correction_batch_digest: str
    memory_snapshot_digest: str
    calibration_snapshot_digest: str
    evidence_bundle_digest: str
    peer_review_digest: str
    review_requested_at: datetime
    review_completed_at: datetime
    correction_required_count: Decimal
    correction_completed_count: Decimal
    stale_memory_before_count: Decimal
    stale_memory_after_count: Decimal
    calibration_error_before: Decimal
    calibration_error_after: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_required_count: Decimal
    peer_review_completed_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewFeedbackAbsorptionRecord:
            raise TypeError(
                "ResearchTeamReviewFeedbackAbsorptionRecord does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("record", self, ResearchTeamReviewFeedbackAbsorptionRecord)
        for field_name in ("team_ref", "review_stream_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "feedback_cycle_digest",
            "correction_batch_digest",
            "memory_snapshot_digest",
            "calibration_snapshot_digest",
            "evidence_bundle_digest",
            "peer_review_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in ("review_requested_at", "review_completed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "correction_required_count",
            "correction_completed_count",
            "stale_memory_before_count",
            "stale_memory_after_count",
            "peer_review_required_count",
            "peer_review_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error_before",
            "calibration_error_after",
            "evidence_reuse_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_record_metrics(self)
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class ResearchTeamReviewFeedbackAbsorptionRow:
    team_ref: str
    review_stream_ref: str
    feedback_cycle_digest: str
    correction_batch_digest: str
    memory_snapshot_digest: str
    calibration_snapshot_digest: str
    evidence_bundle_digest: str
    peer_review_digest: str
    review_requested_at: datetime
    review_completed_at: datetime
    review_latency_seconds: Decimal
    correction_required_count: Decimal
    correction_completed_count: Decimal
    correction_follow_through_ratio: Decimal
    stale_memory_before_count: Decimal
    stale_memory_after_count: Decimal
    stale_memory_reduction_ratio: Decimal
    calibration_error_before: Decimal
    calibration_error_after: Decimal
    calibration_movement_ratio: Decimal
    evidence_reuse_quality_score: Decimal
    evidence_reuse_quality_gap: Decimal
    peer_review_required_count: Decimal
    peer_review_completed_count: Decimal
    peer_review_coverage_ratio: Decimal
    feedback_absorption_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewFeedbackAbsorptionRow:
            raise TypeError(
                "ResearchTeamReviewFeedbackAbsorptionRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamReviewFeedbackAbsorptionRow)
        for field_name in ("team_ref", "review_stream_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "feedback_cycle_digest",
            "correction_batch_digest",
            "memory_snapshot_digest",
            "calibration_snapshot_digest",
            "evidence_bundle_digest",
            "peer_review_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in ("review_requested_at", "review_completed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "review_latency_seconds",
            _normalize_nonnegative_six_place_decimal(
                "review_latency_seconds",
                self.review_latency_seconds,
            ),
        )
        for field_name in (
            "correction_required_count",
            "correction_completed_count",
            "stale_memory_before_count",
            "stale_memory_after_count",
            "peer_review_required_count",
            "peer_review_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "correction_follow_through_ratio",
            "stale_memory_reduction_ratio",
            "calibration_error_before",
            "calibration_error_after",
            "calibration_movement_ratio",
            "evidence_reuse_quality_score",
            "evidence_reuse_quality_gap",
            "peer_review_coverage_ratio",
            "feedback_absorption_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_STATUSES,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_metrics(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_derived_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")


@dataclass(frozen=True)
class ResearchTeamReviewFeedbackAbsorptionReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewFeedbackAbsorptionReasonCodeCount:
            raise TypeError(
                "ResearchTeamReviewFeedbackAbsorptionReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamReviewFeedbackAbsorptionReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamReviewFeedbackAbsorptionReport:
    generated_at: datetime
    config_version: str
    feedback_record_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    correction_gap_count: Decimal
    stale_memory_reduction_gap_count: Decimal
    calibration_movement_gap_count: Decimal
    low_evidence_reuse_quality_count: Decimal
    peer_review_gap_count: Decimal
    review_latency_gap_count: Decimal
    max_feedback_absorption_risk_score: Decimal
    average_feedback_absorption_risk_score: Decimal
    status: str
    rows: tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...]
    reason_code_counts: tuple[ResearchTeamReviewFeedbackAbsorptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewFeedbackAbsorptionReport:
            raise TypeError(
                "ResearchTeamReviewFeedbackAbsorptionReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamReviewFeedbackAbsorptionReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "feedback_record_count",
            "pass_count",
            "watch_count",
            "block_count",
            "correction_gap_count",
            "stale_memory_reduction_gap_count",
            "calibration_movement_gap_count",
            "low_evidence_reuse_quality_count",
            "peer_review_gap_count",
            "review_latency_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_feedback_absorption_risk_score",
            "average_feedback_absorption_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_STATUSES,
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report_metrics(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_derived_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")


def build_research_team_review_feedback_absorption_report(
    records: list[ResearchTeamReviewFeedbackAbsorptionRecord]
    | tuple[ResearchTeamReviewFeedbackAbsorptionRecord, ...],
    *,
    config: ResearchTeamReviewFeedbackAbsorptionReportConfig,
    generated_at: datetime,
) -> ResearchTeamReviewFeedbackAbsorptionReport:
    if type(config) is not ResearchTeamReviewFeedbackAbsorptionReportConfig:
        raise ValueError("config must be a review feedback absorption report config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_records(records, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_record(item, config=config)
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamReviewFeedbackAbsorptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        feedback_record_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        correction_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)),
        ),
        stale_memory_reduction_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)),
        ),
        calibration_movement_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _CALIBRATION_WATCH_REASON, _CALIBRATION_BLOCK_REASON)),
        ),
        low_evidence_reuse_quality_count=_count(
            sum(1 for row in rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)),
        ),
        peer_review_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _PEER_REVIEW_WATCH_REASON, _PEER_REVIEW_BLOCK_REASON)),
        ),
        review_latency_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _LATENCY_WATCH_REASON, _LATENCY_BLOCK_REASON)),
        ),
        max_feedback_absorption_risk_score=_max_risk_score(rows),
        average_feedback_absorption_risk_score=_average_risk_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_review_feedback_absorption_report_payload(
    report: ResearchTeamReviewFeedbackAbsorptionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        validated_report = _report_from_public_payload(report)
        payload = _payload_value(validated_report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        return payload
    if type(report) is not ResearchTeamReviewFeedbackAbsorptionReport:
        raise ValueError("report must be a review feedback absorption report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _report_from_public_payload(payload)
    return payload


def research_team_review_feedback_absorption_report_digest(
    report: ResearchTeamReviewFeedbackAbsorptionReport | dict[str, Any],
) -> str:
    if type(report) is ResearchTeamReviewFeedbackAbsorptionReport:
        _require_hard_flags("report", report)
        _validate_report_digest(report)
        return _digest_value(report)
    if type(report) is dict:
        validated_report = _report_from_public_payload(report)
        return _digest_value(validated_report)
    raise ValueError("report must be a review feedback absorption report or payload dict")


def validate_research_team_review_feedback_absorption_public_payload(
    payload: object,
) -> bool:
    try:
        _report_from_public_payload(payload)
    except (ArithmeticError, TypeError, ValueError):
        return False
    return True


def _report_from_public_payload(
    value: object,
) -> ResearchTeamReviewFeedbackAbsorptionReport:
    if type(value) is not dict:
        raise ValueError("report payload must be a dict")
    payload = value
    _require_payload_hard_flags(payload)
    _reject_non_string_numeric(payload)
    _reject_unsafe_public_payload("review feedback absorption payload", payload)
    payload = _require_payload_dict(
        "report payload",
        payload,
        ResearchTeamReviewFeedbackAbsorptionReport,
    )
    _validate_payload_digest(payload)
    report = ResearchTeamReviewFeedbackAbsorptionReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        feedback_record_count=_payload_decimal(
            "feedback_record_count",
            payload["feedback_record_count"],
        ),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        correction_gap_count=_payload_decimal(
            "correction_gap_count",
            payload["correction_gap_count"],
        ),
        stale_memory_reduction_gap_count=_payload_decimal(
            "stale_memory_reduction_gap_count",
            payload["stale_memory_reduction_gap_count"],
        ),
        calibration_movement_gap_count=_payload_decimal(
            "calibration_movement_gap_count",
            payload["calibration_movement_gap_count"],
        ),
        low_evidence_reuse_quality_count=_payload_decimal(
            "low_evidence_reuse_quality_count",
            payload["low_evidence_reuse_quality_count"],
        ),
        peer_review_gap_count=_payload_decimal(
            "peer_review_gap_count",
            payload["peer_review_gap_count"],
        ),
        review_latency_gap_count=_payload_decimal(
            "review_latency_gap_count",
            payload["review_latency_gap_count"],
        ),
        max_feedback_absorption_risk_score=_payload_decimal(
            "max_feedback_absorption_risk_score",
            payload["max_feedback_absorption_risk_score"],
        ),
        average_feedback_absorption_risk_score=_payload_decimal(
            "average_feedback_absorption_risk_score",
            payload["average_feedback_absorption_risk_score"],
        ),
        status=_payload_string("status", payload["status"]),
        rows=_payload_rows(payload["rows"]),
        reason_code_counts=_payload_reason_code_counts(payload["reason_code_counts"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )
    canonical_payload = _payload_value(report)
    if canonical_payload != payload:
        raise ValueError("report payload must use canonical public schema values")
    return report


def _row_from_public_payload(value: object) -> ResearchTeamReviewFeedbackAbsorptionRow:
    payload = _require_payload_dict(
        "row payload",
        value,
        ResearchTeamReviewFeedbackAbsorptionRow,
    )
    return ResearchTeamReviewFeedbackAbsorptionRow(
        team_ref=_payload_string("team_ref", payload["team_ref"]),
        review_stream_ref=_payload_string("review_stream_ref", payload["review_stream_ref"]),
        feedback_cycle_digest=_payload_string(
            "feedback_cycle_digest",
            payload["feedback_cycle_digest"],
        ),
        correction_batch_digest=_payload_string(
            "correction_batch_digest",
            payload["correction_batch_digest"],
        ),
        memory_snapshot_digest=_payload_string(
            "memory_snapshot_digest",
            payload["memory_snapshot_digest"],
        ),
        calibration_snapshot_digest=_payload_string(
            "calibration_snapshot_digest",
            payload["calibration_snapshot_digest"],
        ),
        evidence_bundle_digest=_payload_string(
            "evidence_bundle_digest",
            payload["evidence_bundle_digest"],
        ),
        peer_review_digest=_payload_string("peer_review_digest", payload["peer_review_digest"]),
        review_requested_at=_payload_datetime(
            "review_requested_at",
            payload["review_requested_at"],
        ),
        review_completed_at=_payload_datetime(
            "review_completed_at",
            payload["review_completed_at"],
        ),
        review_latency_seconds=_payload_decimal(
            "review_latency_seconds",
            payload["review_latency_seconds"],
        ),
        correction_required_count=_payload_decimal(
            "correction_required_count",
            payload["correction_required_count"],
        ),
        correction_completed_count=_payload_decimal(
            "correction_completed_count",
            payload["correction_completed_count"],
        ),
        correction_follow_through_ratio=_payload_decimal(
            "correction_follow_through_ratio",
            payload["correction_follow_through_ratio"],
        ),
        stale_memory_before_count=_payload_decimal(
            "stale_memory_before_count",
            payload["stale_memory_before_count"],
        ),
        stale_memory_after_count=_payload_decimal(
            "stale_memory_after_count",
            payload["stale_memory_after_count"],
        ),
        stale_memory_reduction_ratio=_payload_decimal(
            "stale_memory_reduction_ratio",
            payload["stale_memory_reduction_ratio"],
        ),
        calibration_error_before=_payload_decimal(
            "calibration_error_before",
            payload["calibration_error_before"],
        ),
        calibration_error_after=_payload_decimal(
            "calibration_error_after",
            payload["calibration_error_after"],
        ),
        calibration_movement_ratio=_payload_decimal(
            "calibration_movement_ratio",
            payload["calibration_movement_ratio"],
        ),
        evidence_reuse_quality_score=_payload_decimal(
            "evidence_reuse_quality_score",
            payload["evidence_reuse_quality_score"],
        ),
        evidence_reuse_quality_gap=_payload_decimal(
            "evidence_reuse_quality_gap",
            payload["evidence_reuse_quality_gap"],
        ),
        peer_review_required_count=_payload_decimal(
            "peer_review_required_count",
            payload["peer_review_required_count"],
        ),
        peer_review_completed_count=_payload_decimal(
            "peer_review_completed_count",
            payload["peer_review_completed_count"],
        ),
        peer_review_coverage_ratio=_payload_decimal(
            "peer_review_coverage_ratio",
            payload["peer_review_coverage_ratio"],
        ),
        feedback_absorption_risk_score=_payload_decimal(
            "feedback_absorption_risk_score",
            payload["feedback_absorption_risk_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchTeamReviewFeedbackAbsorptionReasonCodeCount:
    payload = _require_payload_dict(
        "reason code count payload",
        value,
        ResearchTeamReviewFeedbackAbsorptionReasonCodeCount,
    )
    return ResearchTeamReviewFeedbackAbsorptionReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _require_payload_dict(
    label: str,
    value: object,
    expected_type: type[object],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    expected_keys = {field.name for field in fields(expected_type)}
    actual_keys = set(value)
    if actual_keys != expected_keys:
        raise ValueError(f"{label} must match the exact public schema")
    return value


def _payload_rows(value: object) -> tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list in public payload")
    return tuple(_row_from_public_payload(item) for item in value)


def _payload_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamReviewFeedbackAbsorptionReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list in public payload")
    return tuple(_reason_code_count_from_public_payload(item) for item in value)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list in public payload")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string in public payload")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string in public payload")
    try:
        parsed = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a Decimal string in public payload") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return parsed


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string in public payload")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True for payload")
    return True


def _row_from_record(
    record: ResearchTeamReviewFeedbackAbsorptionRecord,
    *,
    config: ResearchTeamReviewFeedbackAbsorptionReportConfig,
) -> ResearchTeamReviewFeedbackAbsorptionRow:
    review_latency_seconds = _seconds_between(
        record.review_completed_at,
        record.review_requested_at,
    )
    correction_follow_through_ratio = _completion_ratio(
        record.correction_required_count,
        record.correction_completed_count,
    )
    stale_memory_reduction_ratio = _reduction_ratio(
        record.stale_memory_before_count,
        record.stale_memory_after_count,
    )
    calibration_movement_ratio = _reduction_ratio(
        record.calibration_error_before,
        record.calibration_error_after,
    )
    evidence_reuse_quality_gap = _six(_ONE_SCORE - record.evidence_reuse_quality_score)
    peer_review_coverage_ratio = _completion_ratio(
        record.peer_review_required_count,
        record.peer_review_completed_count,
    )
    reason_codes = _row_reason_codes(
        correction_follow_through_ratio=correction_follow_through_ratio,
        stale_memory_reduction_ratio=stale_memory_reduction_ratio,
        calibration_movement_ratio=calibration_movement_ratio,
        evidence_reuse_quality_score=record.evidence_reuse_quality_score,
        peer_review_coverage_ratio=peer_review_coverage_ratio,
        review_latency_seconds=review_latency_seconds,
        config=config,
    )
    return ResearchTeamReviewFeedbackAbsorptionRow(
        team_ref=record.team_ref,
        review_stream_ref=record.review_stream_ref,
        feedback_cycle_digest=record.feedback_cycle_digest,
        correction_batch_digest=record.correction_batch_digest,
        memory_snapshot_digest=record.memory_snapshot_digest,
        calibration_snapshot_digest=record.calibration_snapshot_digest,
        evidence_bundle_digest=record.evidence_bundle_digest,
        peer_review_digest=record.peer_review_digest,
        review_requested_at=record.review_requested_at,
        review_completed_at=record.review_completed_at,
        review_latency_seconds=review_latency_seconds,
        correction_required_count=record.correction_required_count,
        correction_completed_count=record.correction_completed_count,
        correction_follow_through_ratio=correction_follow_through_ratio,
        stale_memory_before_count=record.stale_memory_before_count,
        stale_memory_after_count=record.stale_memory_after_count,
        stale_memory_reduction_ratio=stale_memory_reduction_ratio,
        calibration_error_before=record.calibration_error_before,
        calibration_error_after=record.calibration_error_after,
        calibration_movement_ratio=calibration_movement_ratio,
        evidence_reuse_quality_score=record.evidence_reuse_quality_score,
        evidence_reuse_quality_gap=evidence_reuse_quality_gap,
        peer_review_required_count=record.peer_review_required_count,
        peer_review_completed_count=record.peer_review_completed_count,
        peer_review_coverage_ratio=peer_review_coverage_ratio,
        feedback_absorption_risk_score=_risk_score(
            correction_follow_through_ratio=correction_follow_through_ratio,
            stale_memory_reduction_ratio=stale_memory_reduction_ratio,
            calibration_movement_ratio=calibration_movement_ratio,
            evidence_reuse_quality_gap=evidence_reuse_quality_gap,
            peer_review_coverage_ratio=peer_review_coverage_ratio,
            review_latency_seconds=review_latency_seconds,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    correction_follow_through_ratio: Decimal,
    stale_memory_reduction_ratio: Decimal,
    calibration_movement_ratio: Decimal,
    evidence_reuse_quality_score: Decimal,
    peer_review_coverage_ratio: Decimal,
    review_latency_seconds: Decimal,
    config: ResearchTeamReviewFeedbackAbsorptionReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if correction_follow_through_ratio < config.min_watch_correction_follow_through_ratio:
        reason_codes.append(_CORRECTION_BLOCK_REASON)
    elif correction_follow_through_ratio < config.min_pass_correction_follow_through_ratio:
        reason_codes.append(_CORRECTION_WATCH_REASON)
    if stale_memory_reduction_ratio < config.min_watch_stale_memory_reduction_ratio:
        reason_codes.append(_MEMORY_BLOCK_REASON)
    elif stale_memory_reduction_ratio < config.min_pass_stale_memory_reduction_ratio:
        reason_codes.append(_MEMORY_WATCH_REASON)
    if calibration_movement_ratio < config.min_watch_calibration_movement_ratio:
        reason_codes.append(_CALIBRATION_BLOCK_REASON)
    elif calibration_movement_ratio < config.min_pass_calibration_movement_ratio:
        reason_codes.append(_CALIBRATION_WATCH_REASON)
    if evidence_reuse_quality_score < config.min_watch_evidence_reuse_quality_score:
        reason_codes.append(_EVIDENCE_BLOCK_REASON)
    elif evidence_reuse_quality_score < config.min_pass_evidence_reuse_quality_score:
        reason_codes.append(_EVIDENCE_WATCH_REASON)
    if peer_review_coverage_ratio < config.min_watch_peer_review_coverage_ratio:
        reason_codes.append(_PEER_REVIEW_BLOCK_REASON)
    elif peer_review_coverage_ratio < config.min_pass_peer_review_coverage_ratio:
        reason_codes.append(_PEER_REVIEW_WATCH_REASON)
    if review_latency_seconds >= config.review_latency_block_seconds:
        reason_codes.append(_LATENCY_BLOCK_REASON)
    elif review_latency_seconds >= config.review_latency_watch_seconds:
        reason_codes.append(_LATENCY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reason_codes = sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != _PASS_REASON
        },
        key=_reason_index,
    )
    if not reason_codes:
        return (_PASS_REASON,)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamReviewFeedbackAbsorptionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamReviewFeedbackAbsorptionReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamReviewFeedbackAbsorptionReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _risk_score(
    *,
    correction_follow_through_ratio: Decimal,
    stale_memory_reduction_ratio: Decimal,
    calibration_movement_ratio: Decimal,
    evidence_reuse_quality_gap: Decimal,
    peer_review_coverage_ratio: Decimal,
    review_latency_seconds: Decimal,
    config: ResearchTeamReviewFeedbackAbsorptionReportConfig,
) -> Decimal:
    return _six(
        (_ONE_SCORE - correction_follow_through_ratio)
        * config.correction_follow_through_weight
        + (_ONE_SCORE - stale_memory_reduction_ratio)
        * config.stale_memory_reduction_weight
        + (_ONE_SCORE - calibration_movement_ratio) * config.calibration_movement_weight
        + evidence_reuse_quality_gap * config.evidence_reuse_quality_weight
        + (_ONE_SCORE - peer_review_coverage_ratio) * config.peer_review_coverage_weight
        + _capped_ratio(review_latency_seconds, config.review_latency_block_seconds)
        * config.review_latency_weight,
    )


def _completion_ratio(required_count: Decimal, completed_count: Decimal) -> Decimal:
    if required_count <= _ZERO_COUNT:
        return _ONE_SCORE
    return _six(completed_count / required_count)


def _reduction_ratio(before_value: Decimal, after_value: Decimal) -> Decimal:
    if before_value <= _ZERO_SCORE:
        return _ONE_SCORE
    return _six((before_value - after_value) / before_value)


def _max_risk_score(rows: tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.feedback_absorption_risk_score for row in rows)


def _average_risk_score(rows: tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return _six(
        sum((row.feedback_absorption_risk_score for row in rows), _ZERO_SCORE)
        / Decimal(len(rows)),
    )


def _has_any(
    row: ResearchTeamReviewFeedbackAbsorptionRow,
    watch_reason: str,
    block_reason: str,
) -> bool:
    return watch_reason in row.reason_codes or block_reason in row.reason_codes


def _normalize_records(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchTeamReviewFeedbackAbsorptionRecord, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    seen: set[str] = set()
    for record in records:
        if type(record) is not ResearchTeamReviewFeedbackAbsorptionRecord:
            raise ValueError("records must contain exact review feedback absorption records")
        _require_hard_flags("record", record)
        for field_name in ("review_requested_at", "review_completed_at"):
            if getattr(record, field_name) > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        if record.feedback_cycle_digest in seen:
            raise ValueError("records must not repeat feedback cycle digests")
        seen.add(record.feedback_cycle_digest)
    return tuple(sorted(records, key=_record_sort_key))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamReviewFeedbackAbsorptionRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamReviewFeedbackAbsorptionRow:
            raise ValueError("rows must contain exact review feedback absorption rows")
        _require_hard_flags("row", row)
        if row.feedback_cycle_digest in seen:
            raise ValueError("rows must not repeat feedback cycle digests")
        seen.add(row.feedback_cycle_digest)
        _validate_row_digest(row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status, refs, and digest")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamReviewFeedbackAbsorptionReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamReviewFeedbackAbsorptionReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat reason codes")
        seen.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=lambda row: _reason_index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return rows


def _validate_record_metrics(record: ResearchTeamReviewFeedbackAbsorptionRecord) -> None:
    if record.review_completed_at < record.review_requested_at:
        raise ValueError("review_completed_at must not be before review_requested_at")
    if record.correction_completed_count > record.correction_required_count:
        raise ValueError("correction_completed_count must not exceed required count")
    if record.stale_memory_after_count > record.stale_memory_before_count:
        raise ValueError("stale_memory_after_count must not exceed before count")
    if record.calibration_error_after > record.calibration_error_before:
        raise ValueError("calibration_error_after must not exceed before value")
    if record.peer_review_completed_count > record.peer_review_required_count:
        raise ValueError("peer_review_completed_count must not exceed required count")


def _validate_row_metrics(row: ResearchTeamReviewFeedbackAbsorptionRow) -> None:
    if row.review_completed_at < row.review_requested_at:
        raise ValueError("review_completed_at must not be before review_requested_at")
    if row.correction_completed_count > row.correction_required_count:
        raise ValueError("correction_completed_count must not exceed required count")
    if row.stale_memory_after_count > row.stale_memory_before_count:
        raise ValueError("stale_memory_after_count must not exceed before count")
    if row.calibration_error_after > row.calibration_error_before:
        raise ValueError("calibration_error_after must not exceed before value")
    if row.peer_review_completed_count > row.peer_review_required_count:
        raise ValueError("peer_review_completed_count must not exceed required count")
    expected_review_latency_seconds = _seconds_between(
        row.review_completed_at,
        row.review_requested_at,
    )
    if row.review_latency_seconds != expected_review_latency_seconds:
        raise ValueError("review_latency_seconds must match review timestamps")
    expected_correction_follow_through_ratio = _completion_ratio(
        row.correction_required_count,
        row.correction_completed_count,
    )
    if row.correction_follow_through_ratio != expected_correction_follow_through_ratio:
        raise ValueError(
            "correction_follow_through_ratio must match correction counts",
        )
    expected_stale_memory_reduction_ratio = _reduction_ratio(
        row.stale_memory_before_count,
        row.stale_memory_after_count,
    )
    if row.stale_memory_reduction_ratio != expected_stale_memory_reduction_ratio:
        raise ValueError(
            "stale_memory_reduction_ratio must match stale memory counts",
        )
    expected_calibration_movement_ratio = _reduction_ratio(
        row.calibration_error_before,
        row.calibration_error_after,
    )
    if row.calibration_movement_ratio != expected_calibration_movement_ratio:
        raise ValueError(
            "calibration_movement_ratio must match calibration errors",
        )
    expected_evidence_reuse_quality_gap = _six(
        _ONE_SCORE - row.evidence_reuse_quality_score,
    )
    if row.evidence_reuse_quality_gap != expected_evidence_reuse_quality_gap:
        raise ValueError(
            "evidence_reuse_quality_gap must match evidence_reuse_quality_score",
        )
    expected_peer_review_coverage_ratio = _completion_ratio(
        row.peer_review_required_count,
        row.peer_review_completed_count,
    )
    if row.peer_review_coverage_ratio != expected_peer_review_coverage_ratio:
        raise ValueError(
            "peer_review_coverage_ratio must match peer review counts",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_metrics(report: ResearchTeamReviewFeedbackAbsorptionReport) -> None:
    rows = report.rows
    if report.feedback_record_count != _count(len(rows)):
        raise ValueError("feedback_record_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    expected_gap_counts = {
        "correction_gap_count": sum(
            1 for row in rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)
        ),
        "stale_memory_reduction_gap_count": sum(
            1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)
        ),
        "calibration_movement_gap_count": sum(
            1 for row in rows if _has_any(row, _CALIBRATION_WATCH_REASON, _CALIBRATION_BLOCK_REASON)
        ),
        "low_evidence_reuse_quality_count": sum(
            1 for row in rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)
        ),
        "peer_review_gap_count": sum(
            1 for row in rows if _has_any(row, _PEER_REVIEW_WATCH_REASON, _PEER_REVIEW_BLOCK_REASON)
        ),
        "review_latency_gap_count": sum(
            1 for row in rows if _has_any(row, _LATENCY_WATCH_REASON, _LATENCY_BLOCK_REASON)
        ),
    }
    for field_name, expected_count in expected_gap_counts.items():
        if getattr(report, field_name) != _count(expected_count):
            raise ValueError(f"{field_name} must match rows")
    if report.max_feedback_absorption_risk_score != _max_risk_score(rows):
        raise ValueError("max_feedback_absorption_risk_score must match rows")
    if report.average_feedback_absorption_risk_score != _average_risk_score(rows):
        raise ValueError("average_feedback_absorption_risk_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_digest(report: ResearchTeamReviewFeedbackAbsorptionReport) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    expected_digest = _digest_value(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_digest(row: ResearchTeamReviewFeedbackAbsorptionRow) -> None:
    expected_digest = _digest_value(row)
    if row.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match row fields")


def _validate_payload_digest(value: Mapping[str, Any]) -> None:
    for item in value.values():
        if isinstance(item, Mapping):
            _validate_payload_digest(item)
        elif type(item) is list:
            for nested in item:
                if isinstance(nested, Mapping):
                    _validate_payload_digest(nested)
    if _DIGEST_FIELD not in value:
        return
    digest = value[_DIGEST_FIELD]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_derived_digest("derived_validation_digest", digest)
    expected_digest = _digest_mapping(value)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _digest_value(value: object) -> str:
    payload = _payload_value(value, omit_digest=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest_mapping(value: Mapping[str, Any]) -> str:
    payload = _payload_value(value, omit_digest=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, omit_digest: bool = False) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            if omit_digest and field.name == _DIGEST_FIELD:
                continue
            payload[field.name] = _payload_value(getattr(value, field.name), omit_digest=omit_digest)
        return payload
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        payload = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            payload[key] = _payload_value(item, omit_digest=omit_digest)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _require_payload_hard_flags(value: Mapping[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is float:
        raise ValueError("float payload values are not allowed")
    if type(value) is int:
        raise ValueError("numeric payload values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("Decimal payload values must be serialized as strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, label)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_key(key, label)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(key: str, label: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 128:
        raise ValueError(f"{field_name} must not exceed 128 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    prefix = "sha256:"
    digest = value[len(prefix) :] if value.startswith(prefix) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a sha256 digest reference")
    return value


def _require_derived_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not repeat values")
        seen.add(reason_code)
    if _PASS_REASON in seen and len(seen) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if _EMPTY_REASON in seen and len(seen) != 1:
        raise ValueError("empty reason_codes must stand alone")
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in seen)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(_COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized <= _ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO_SCORE or normalized > _ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_SCORE:
        raise ValueError("denominator must be positive")
    return min(_ONE_SCORE, _six(numerator / denominator))


def _seconds_between(finished_at: datetime, started_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    return _six(
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    try:
        offset = value.utcoffset()
    except NotImplementedError as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _record_sort_key(
    record: ResearchTeamReviewFeedbackAbsorptionRecord,
) -> tuple[str, str, str]:
    return (record.team_ref, record.review_stream_ref, record.feedback_cycle_digest)


def _row_sort_key(
    row: ResearchTeamReviewFeedbackAbsorptionRow,
) -> tuple[int, str, str, str]:
    return (_status_rank(row.status), row.team_ref, row.review_stream_ref, row.feedback_cycle_digest)


def _status_rank(status: str) -> int:
    return {"pass": 0, "watch": 1, "block": 2}[status]


def _reason_index(reason_code: str) -> int:
    return _REASON_SEQUENCE.index(reason_code)
