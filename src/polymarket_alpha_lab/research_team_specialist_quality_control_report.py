from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_REPORT_CONFIG_VERSION = (
    "research-team-specialist-quality-control-report-v0"
)
RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "derived_validation_digest"

_PASS_REASON = "specialist_quality_control_pass"
_EMPTY_REASON = "specialist_quality_control_empty"
_BIAS_BLOCK_REASON = "bias_flags_block"
_BIAS_WATCH_REASON = "bias_flags_watch"
_CALIBRATION_BLOCK_REASON = "calibration_error_block"
_CALIBRATION_WATCH_REASON = "calibration_error_watch"
_CORRECTION_BLOCK_REASON = "correction_coverage_block"
_CORRECTION_WATCH_REASON = "correction_coverage_watch"
_REVIEW_BLOCK_REASON = "review_latency_block"
_REVIEW_WATCH_REASON = "review_latency_watch"
_DIVERSITY_BLOCK_REASON = "source_diversity_block"
_DIVERSITY_WATCH_REASON = "source_diversity_watch"
_MEMORY_BLOCK_REASON = "stale_memory_block"
_MEMORY_WATCH_REASON = "stale_memory_watch"

_REASON_SEQUENCE = (
    _BIAS_BLOCK_REASON,
    _BIAS_WATCH_REASON,
    _CALIBRATION_BLOCK_REASON,
    _CALIBRATION_WATCH_REASON,
    _CORRECTION_BLOCK_REASON,
    _CORRECTION_WATCH_REASON,
    _REVIEW_BLOCK_REASON,
    _REVIEW_WATCH_REASON,
    _DIVERSITY_BLOCK_REASON,
    _DIVERSITY_WATCH_REASON,
    _MEMORY_BLOCK_REASON,
    _MEMORY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)

_UNSAFE_PUBLIC_HEXES = (
    "63616e646964617465",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "6d61726b65742d736c7567",
    "77696c6c2d74686973",
    "3f",
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
    "6e6574776f726b",
    "6461746162617365",
    "6c697665",
)
_UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii") for value in _UNSAFE_PUBLIC_HEXES
)


@dataclass(frozen=True)
class ResearchTeamSpecialistQualityControlReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_REPORT_CONFIG_VERSION
    )
    calibration_watch_error_ratio: Decimal = Decimal("0.100000")
    calibration_block_error_ratio: Decimal = Decimal("0.250000")
    memory_watch_age_seconds: Decimal = Decimal("86400.000000")
    memory_block_age_seconds: Decimal = Decimal("259200.000000")
    bias_watch_flag_count: Decimal = Decimal("1")
    bias_block_flag_count: Decimal = Decimal("3")
    min_source_family_count: Decimal = Decimal("3")
    review_watch_latency_seconds: Decimal = Decimal("3600.000000")
    review_block_latency_seconds: Decimal = Decimal("7200.000000")
    correction_watch_gap_ratio: Decimal = Decimal("0.250000")
    correction_block_gap_ratio: Decimal = Decimal("0.500000")
    calibration_weight: Decimal = Decimal("0.250000")
    memory_weight: Decimal = Decimal("0.150000")
    bias_weight: Decimal = Decimal("0.200000")
    source_diversity_weight: Decimal = Decimal("0.150000")
    review_timeliness_weight: Decimal = Decimal("0.150000")
    correction_coverage_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistQualityControlReportConfig:
            raise TypeError(
                "ResearchTeamSpecialistQualityControlReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamSpecialistQualityControlReportConfig)
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "calibration_watch_error_ratio",
            "calibration_block_error_ratio",
            "correction_watch_gap_ratio",
            "correction_block_gap_ratio",
            "calibration_weight",
            "memory_weight",
            "bias_weight",
            "source_diversity_weight",
            "review_timeliness_weight",
            "correction_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_watch_age_seconds",
            "memory_block_age_seconds",
            "review_watch_latency_seconds",
            "review_block_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bias_watch_flag_count",
            "bias_block_flag_count",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.calibration_block_error_ratio <= self.calibration_watch_error_ratio:
            raise ValueError("calibration_block_error_ratio must exceed watch threshold")
        if self.memory_block_age_seconds <= self.memory_watch_age_seconds:
            raise ValueError("memory_block_age_seconds must exceed watch threshold")
        if self.bias_block_flag_count <= self.bias_watch_flag_count:
            raise ValueError("bias_block_flag_count must exceed watch threshold")
        if self.review_block_latency_seconds <= self.review_watch_latency_seconds:
            raise ValueError("review_block_latency_seconds must exceed watch threshold")
        if self.correction_block_gap_ratio <= self.correction_watch_gap_ratio:
            raise ValueError("correction_block_gap_ratio must exceed watch threshold")
        weight_sum = _six(
            self.calibration_weight
            + self.memory_weight
            + self.bias_weight
            + self.source_diversity_weight
            + self.review_timeliness_weight
            + self.correction_coverage_weight,
        )
        if weight_sum != _ONE_SCORE:
            raise ValueError("quality control weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistQualityControlRecord:
    team_ref: str
    specialist_ref: str
    specialist_output_digest: str
    calibration_record_digest: str
    observed_at: datetime
    memory_last_refreshed_at: datetime
    review_completed_at: datetime
    calibration_error_ratio: Decimal
    bias_flag_count: Decimal
    source_family_count: Decimal
    correction_required_count: Decimal
    correction_covered_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistQualityControlRecord:
            raise TypeError(
                "ResearchTeamSpecialistQualityControlRecord does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("record", self, ResearchTeamSpecialistQualityControlRecord)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("specialist_output_digest", "calibration_record_digest"):
            _require_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_last_refreshed_at",
            _as_utc("memory_last_refreshed_at", self.memory_last_refreshed_at),
        )
        object.__setattr__(
            self,
            "review_completed_at",
            _as_utc("review_completed_at", self.review_completed_at),
        )
        if self.review_completed_at < self.observed_at:
            raise ValueError("review_completed_at must be on or after observed_at")
        object.__setattr__(
            self,
            "calibration_error_ratio",
            _normalize_unit_decimal(
                "calibration_error_ratio",
                self.calibration_error_ratio,
            ),
        )
        for field_name in (
            "bias_flag_count",
            "source_family_count",
            "correction_required_count",
            "correction_covered_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.correction_covered_count > self.correction_required_count:
            raise ValueError("correction_covered_count must not exceed required count")
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistQualityControlRow:
    team_ref: str
    specialist_ref: str
    specialist_output_digest: str
    calibration_record_digest: str
    observed_at: datetime
    memory_last_refreshed_at: datetime
    review_completed_at: datetime
    review_latency_seconds: Decimal
    memory_age_seconds: Decimal
    calibration_error_ratio: Decimal
    bias_flag_count: Decimal
    source_family_count: Decimal
    correction_required_count: Decimal
    correction_covered_count: Decimal
    correction_gap_ratio: Decimal
    calibration_component: Decimal
    stale_memory_component: Decimal
    bias_component: Decimal
    source_diversity_gap: Decimal
    review_timeliness_component: Decimal
    correction_coverage_gap: Decimal
    quality_control_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistQualityControlRow:
            raise TypeError(
                "ResearchTeamSpecialistQualityControlRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamSpecialistQualityControlRow)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("specialist_output_digest", "calibration_record_digest"):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in ("observed_at", "memory_last_refreshed_at", "review_completed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "review_latency_seconds",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "calibration_error_ratio",
            _normalize_unit_decimal("calibration_error_ratio", self.calibration_error_ratio),
        )
        for field_name in (
            "bias_flag_count",
            "source_family_count",
            "correction_required_count",
            "correction_covered_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "correction_gap_ratio",
            "calibration_component",
            "stale_memory_component",
            "bias_component",
            "source_diversity_gap",
            "review_timeliness_component",
            "correction_coverage_gap",
            "quality_control_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_metrics(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")


@dataclass(frozen=True)
class ResearchTeamSpecialistQualityControlReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistQualityControlReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistQualityControlReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamSpecialistQualityControlReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistQualityControlReport:
    generated_at: datetime
    config_version: str
    output_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    bias_flagged_count: Decimal
    source_diversity_gap_count: Decimal
    delayed_review_count: Decimal
    correction_gap_count: Decimal
    max_quality_control_risk_score: Decimal
    average_quality_control_risk_score: Decimal
    status: str
    rows: tuple[ResearchTeamSpecialistQualityControlRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistQualityControlReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistQualityControlReport:
            raise TypeError(
                "ResearchTeamSpecialistQualityControlReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamSpecialistQualityControlReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "output_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "bias_flagged_count",
            "source_diversity_gap_count",
            "delayed_review_count",
            "correction_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_quality_control_risk_score",
            "average_quality_control_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_STATUSES)
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
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_research_team_specialist_quality_control_report(
    records: list[ResearchTeamSpecialistQualityControlRecord]
    | tuple[ResearchTeamSpecialistQualityControlRecord, ...],
    *,
    config: ResearchTeamSpecialistQualityControlReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistQualityControlReport:
    if type(config) is not ResearchTeamSpecialistQualityControlReportConfig:
        raise ValueError("config must be a quality control report config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_records(records, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_record(item, config=config, generated_at=generated_at_utc) for item in items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    return ResearchTeamSpecialistQualityControlReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        output_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        stale_memory_count=_count(
            sum(1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)),
        ),
        bias_flagged_count=_count(
            sum(1 for row in rows if _has_any(row, _BIAS_WATCH_REASON, _BIAS_BLOCK_REASON)),
        ),
        source_diversity_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _DIVERSITY_WATCH_REASON, _DIVERSITY_BLOCK_REASON)),
        ),
        delayed_review_count=_count(
            sum(1 for row in rows if _has_any(row, _REVIEW_WATCH_REASON, _REVIEW_BLOCK_REASON)),
        ),
        correction_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)),
        ),
        max_quality_control_risk_score=_max_risk_score(rows),
        average_quality_control_risk_score=_average_risk_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_specialist_quality_control_report_payload(
    report: ResearchTeamSpecialistQualityControlReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_non_string_numeric(report)
        _reject_unsafe_public_payload("quality control payload", report)
        _validate_payload_digest(report)
        return _validate_public_payload_schema(report)
    if type(report) is not ResearchTeamSpecialistQualityControlReport:
        raise ValueError("report must be a quality control report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload("quality control payload", payload)
    _validate_payload_digest(payload)
    return payload


def _validate_public_payload_schema(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact_payload_schema(
        "quality control payload",
        payload,
        ResearchTeamSpecialistQualityControlReport,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("quality control payload rows schema must be a list")
    rows = tuple(
        _row_from_public_payload(item, index=index)
        for index, item in enumerate(rows_value)
    )
    reason_code_counts_value = payload["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError(
            "quality control payload reason_code_counts schema must be a list",
        )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item, index=index)
        for index, item in enumerate(reason_code_counts_value)
    )
    report = ResearchTeamSpecialistQualityControlReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_schema_string(
            "config_version",
            payload["config_version"],
        ),
        output_count=_public_decimal("output_count", payload["output_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        stale_memory_count=_public_decimal(
            "stale_memory_count",
            payload["stale_memory_count"],
        ),
        bias_flagged_count=_public_decimal(
            "bias_flagged_count",
            payload["bias_flagged_count"],
        ),
        source_diversity_gap_count=_public_decimal(
            "source_diversity_gap_count",
            payload["source_diversity_gap_count"],
        ),
        delayed_review_count=_public_decimal(
            "delayed_review_count",
            payload["delayed_review_count"],
        ),
        correction_gap_count=_public_decimal(
            "correction_gap_count",
            payload["correction_gap_count"],
        ),
        max_quality_control_risk_score=_public_decimal(
            "max_quality_control_risk_score",
            payload["max_quality_control_risk_score"],
        ),
        average_quality_control_risk_score=_public_decimal(
            "average_quality_control_risk_score",
            payload["average_quality_control_risk_score"],
        ),
        status=_public_schema_string("status", payload["status"]),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_public_validation_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )
    canonical_payload = _payload_value(report)
    if type(canonical_payload) is not dict:
        raise ValueError("quality control payload schema must produce a dict")
    if canonical_payload != payload:
        raise ValueError("quality control payload must use canonical schema values")
    return canonical_payload


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamSpecialistQualityControlRow:
    label = f"quality control payload rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a JSON object")
    _require_exact_payload_schema(
        label,
        value,
        ResearchTeamSpecialistQualityControlRow,
    )
    return ResearchTeamSpecialistQualityControlRow(
        team_ref=_public_schema_string("team_ref", value["team_ref"]),
        specialist_ref=_public_schema_string(
            "specialist_ref",
            value["specialist_ref"],
        ),
        specialist_output_digest=_public_schema_string(
            "specialist_output_digest",
            value["specialist_output_digest"],
        ),
        calibration_record_digest=_public_schema_string(
            "calibration_record_digest",
            value["calibration_record_digest"],
        ),
        observed_at=_public_datetime("observed_at", value["observed_at"]),
        memory_last_refreshed_at=_public_datetime(
            "memory_last_refreshed_at",
            value["memory_last_refreshed_at"],
        ),
        review_completed_at=_public_datetime(
            "review_completed_at",
            value["review_completed_at"],
        ),
        review_latency_seconds=_public_decimal(
            "review_latency_seconds",
            value["review_latency_seconds"],
        ),
        memory_age_seconds=_public_decimal(
            "memory_age_seconds",
            value["memory_age_seconds"],
        ),
        calibration_error_ratio=_public_decimal(
            "calibration_error_ratio",
            value["calibration_error_ratio"],
        ),
        bias_flag_count=_public_decimal("bias_flag_count", value["bias_flag_count"]),
        source_family_count=_public_decimal(
            "source_family_count",
            value["source_family_count"],
        ),
        correction_required_count=_public_decimal(
            "correction_required_count",
            value["correction_required_count"],
        ),
        correction_covered_count=_public_decimal(
            "correction_covered_count",
            value["correction_covered_count"],
        ),
        correction_gap_ratio=_public_decimal(
            "correction_gap_ratio",
            value["correction_gap_ratio"],
        ),
        calibration_component=_public_decimal(
            "calibration_component",
            value["calibration_component"],
        ),
        stale_memory_component=_public_decimal(
            "stale_memory_component",
            value["stale_memory_component"],
        ),
        bias_component=_public_decimal("bias_component", value["bias_component"]),
        source_diversity_gap=_public_decimal(
            "source_diversity_gap",
            value["source_diversity_gap"],
        ),
        review_timeliness_component=_public_decimal(
            "review_timeliness_component",
            value["review_timeliness_component"],
        ),
        correction_coverage_gap=_public_decimal(
            "correction_coverage_gap",
            value["correction_coverage_gap"],
        ),
        quality_control_risk_score=_public_decimal(
            "quality_control_risk_score",
            value["quality_control_risk_score"],
        ),
        status=_public_schema_string("status", value["status"]),
        reason_codes=_public_string_tuple("reason_codes", value["reason_codes"]),
        derived_validation_digest=_public_validation_digest(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamSpecialistQualityControlReasonCodeCount:
    label = f"quality control payload reason_code_counts[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a JSON object")
    _require_exact_payload_schema(
        label,
        value,
        ResearchTeamSpecialistQualityControlReasonCodeCount,
    )
    return ResearchTeamSpecialistQualityControlReasonCodeCount(
        reason_code=_public_schema_string("reason_code", value["reason_code"]),
        count=_public_decimal("count", value["count"]),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _require_exact_payload_schema(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = {field.name for field in fields(expected_type)}
    if set(payload) != expected_fields:
        raise ValueError(f"{label} schema fields must match exactly")


def _public_schema_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} schema value must be a string")
    return value


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be a finite canonical Decimal string")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    if format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return decimal_value


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} schema value must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} schema values must be strings")
    return tuple(value)


def _public_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _row_from_record(
    record: ResearchTeamSpecialistQualityControlRecord,
    *,
    config: ResearchTeamSpecialistQualityControlReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistQualityControlRow:
    review_latency_seconds = _seconds_between(record.review_completed_at, record.observed_at)
    memory_age_seconds = _seconds_between(generated_at, record.memory_last_refreshed_at)
    correction_gap_ratio = _correction_gap_ratio(record)
    calibration_component = _capped_ratio(
        record.calibration_error_ratio,
        config.calibration_block_error_ratio,
    )
    stale_memory_component = _capped_ratio(memory_age_seconds, config.memory_block_age_seconds)
    bias_component = _capped_ratio(record.bias_flag_count, config.bias_block_flag_count)
    source_diversity_gap = _source_diversity_gap(record, config)
    review_timeliness_component = _capped_ratio(
        review_latency_seconds,
        config.review_block_latency_seconds,
    )
    correction_coverage_gap = correction_gap_ratio
    reason_codes = _row_reason_codes(
        record,
        config=config,
        review_latency_seconds=review_latency_seconds,
        memory_age_seconds=memory_age_seconds,
        correction_gap_ratio=correction_gap_ratio,
    )
    return ResearchTeamSpecialistQualityControlRow(
        team_ref=record.team_ref,
        specialist_ref=record.specialist_ref,
        specialist_output_digest=record.specialist_output_digest,
        calibration_record_digest=record.calibration_record_digest,
        observed_at=record.observed_at,
        memory_last_refreshed_at=record.memory_last_refreshed_at,
        review_completed_at=record.review_completed_at,
        review_latency_seconds=review_latency_seconds,
        memory_age_seconds=memory_age_seconds,
        calibration_error_ratio=record.calibration_error_ratio,
        bias_flag_count=record.bias_flag_count,
        source_family_count=record.source_family_count,
        correction_required_count=record.correction_required_count,
        correction_covered_count=record.correction_covered_count,
        correction_gap_ratio=correction_gap_ratio,
        calibration_component=calibration_component,
        stale_memory_component=stale_memory_component,
        bias_component=bias_component,
        source_diversity_gap=source_diversity_gap,
        review_timeliness_component=review_timeliness_component,
        correction_coverage_gap=correction_coverage_gap,
        quality_control_risk_score=_risk_score(
            calibration_component=calibration_component,
            stale_memory_component=stale_memory_component,
            bias_component=bias_component,
            source_diversity_gap=source_diversity_gap,
            review_timeliness_component=review_timeliness_component,
            correction_coverage_gap=correction_coverage_gap,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    record: ResearchTeamSpecialistQualityControlRecord,
    *,
    config: ResearchTeamSpecialistQualityControlReportConfig,
    review_latency_seconds: Decimal,
    memory_age_seconds: Decimal,
    correction_gap_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if record.bias_flag_count >= config.bias_block_flag_count:
        reason_codes.append(_BIAS_BLOCK_REASON)
    elif record.bias_flag_count >= config.bias_watch_flag_count:
        reason_codes.append(_BIAS_WATCH_REASON)
    if record.calibration_error_ratio >= config.calibration_block_error_ratio:
        reason_codes.append(_CALIBRATION_BLOCK_REASON)
    elif record.calibration_error_ratio >= config.calibration_watch_error_ratio:
        reason_codes.append(_CALIBRATION_WATCH_REASON)
    if correction_gap_ratio >= config.correction_block_gap_ratio:
        reason_codes.append(_CORRECTION_BLOCK_REASON)
    elif correction_gap_ratio >= config.correction_watch_gap_ratio:
        reason_codes.append(_CORRECTION_WATCH_REASON)
    if review_latency_seconds >= config.review_block_latency_seconds:
        reason_codes.append(_REVIEW_BLOCK_REASON)
    elif review_latency_seconds >= config.review_watch_latency_seconds:
        reason_codes.append(_REVIEW_WATCH_REASON)
    if record.source_family_count <= _ZERO_COUNT:
        reason_codes.append(_DIVERSITY_BLOCK_REASON)
    elif record.source_family_count < config.min_source_family_count:
        reason_codes.append(_DIVERSITY_WATCH_REASON)
    if memory_age_seconds >= config.memory_block_age_seconds:
        reason_codes.append(_MEMORY_BLOCK_REASON)
    elif memory_age_seconds >= config.memory_watch_age_seconds:
        reason_codes.append(_MEMORY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchTeamSpecialistQualityControlRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistQualityControlRow, ...],
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
    )
    if not reason_codes:
        return (_PASS_REASON,)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistQualityControlRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSpecialistQualityControlReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistQualityControlReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamSpecialistQualityControlReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _risk_score(
    *,
    calibration_component: Decimal,
    stale_memory_component: Decimal,
    bias_component: Decimal,
    source_diversity_gap: Decimal,
    review_timeliness_component: Decimal,
    correction_coverage_gap: Decimal,
    config: ResearchTeamSpecialistQualityControlReportConfig,
) -> Decimal:
    return _six(
        calibration_component * config.calibration_weight
        + stale_memory_component * config.memory_weight
        + bias_component * config.bias_weight
        + source_diversity_gap * config.source_diversity_weight
        + review_timeliness_component * config.review_timeliness_weight
        + correction_coverage_gap * config.correction_coverage_weight,
    )


def _correction_gap_ratio(record: ResearchTeamSpecialistQualityControlRecord) -> Decimal:
    if record.correction_required_count <= _ZERO_COUNT:
        return _ZERO_SCORE
    return _six(
        (record.correction_required_count - record.correction_covered_count)
        / record.correction_required_count,
    )


def _source_diversity_gap(
    record: ResearchTeamSpecialistQualityControlRecord,
    config: ResearchTeamSpecialistQualityControlReportConfig,
) -> Decimal:
    if record.source_family_count >= config.min_source_family_count:
        return _ZERO_SCORE
    return _six(
        (config.min_source_family_count - record.source_family_count)
        / config.min_source_family_count,
    )


def _max_risk_score(rows: tuple[ResearchTeamSpecialistQualityControlRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.quality_control_risk_score for row in rows)


def _average_risk_score(rows: tuple[ResearchTeamSpecialistQualityControlRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return _six(sum((row.quality_control_risk_score for row in rows), _ZERO_SCORE) / Decimal(len(rows)))


def _has_any(
    row: ResearchTeamSpecialistQualityControlRow,
    watch_reason: str,
    block_reason: str,
) -> bool:
    return watch_reason in row.reason_codes or block_reason in row.reason_codes


def _normalize_records(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistQualityControlRecord, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    seen: set[str] = set()
    for record in records:
        if type(record) is not ResearchTeamSpecialistQualityControlRecord:
            raise ValueError("records must contain exact quality control records")
        _require_hard_flags("record", record)
        for field_name in ("observed_at", "memory_last_refreshed_at", "review_completed_at"):
            if getattr(record, field_name) > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        if record.specialist_output_digest in seen:
            raise ValueError("records must not repeat specialist output digests")
        seen.add(record.specialist_output_digest)
    return tuple(sorted(records, key=lambda record: _record_sort_key(record)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamSpecialistQualityControlRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistQualityControlRow:
            raise ValueError("rows must contain exact quality control rows")
        _require_hard_flags("row", row)
        if row.specialist_output_digest in seen:
            raise ValueError("rows must not repeat specialist output digests")
        seen.add(row.specialist_output_digest)
        _validate_row_digest(row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by refs and digest")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSpecialistQualityControlReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSpecialistQualityControlReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted")
    return rows


def _validate_row_metrics(row: ResearchTeamSpecialistQualityControlRow) -> None:
    if row.correction_covered_count > row.correction_required_count:
        raise ValueError("correction_covered_count must not exceed required count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.review_completed_at < row.observed_at:
        raise ValueError("review_completed_at must be on or after observed_at")


def _validate_report_metrics(report: ResearchTeamSpecialistQualityControlReport) -> None:
    if report.output_count != _count(len(report.rows)):
        raise ValueError("output_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.stale_memory_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)
        ),
    ):
        raise ValueError("stale_memory_count must match rows")
    if report.bias_flagged_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _BIAS_WATCH_REASON, _BIAS_BLOCK_REASON)
        ),
    ):
        raise ValueError("bias_flagged_count must match rows")
    if report.source_diversity_gap_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _DIVERSITY_WATCH_REASON, _DIVERSITY_BLOCK_REASON)
        ),
    ):
        raise ValueError("source_diversity_gap_count must match rows")
    if report.delayed_review_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _REVIEW_WATCH_REASON, _REVIEW_BLOCK_REASON)
        ),
    ):
        raise ValueError("delayed_review_count must match rows")
    if report.correction_gap_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)
        ),
    ):
        raise ValueError("correction_gap_count must match rows")
    if report.max_quality_control_risk_score != _max_risk_score(report.rows):
        raise ValueError("max_quality_control_risk_score must match rows")
    if report.average_quality_control_risk_score != _average_risk_score(report.rows):
        raise ValueError("average_quality_control_risk_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _record_sort_key(record: ResearchTeamSpecialistQualityControlRecord) -> tuple[str, str, str]:
    return (record.team_ref, record.specialist_ref, record.specialist_output_digest)


def _row_sort_key(row: ResearchTeamSpecialistQualityControlRow) -> tuple[str, str, str]:
    return (row.team_ref, row.specialist_ref, row.specialist_output_digest)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _normalize_nonnegative_six_place_decimal("seconds", _six(seconds))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_SCORE:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < _ZERO_SCORE:
        return _ZERO_SCORE
    if value > _ONE_SCORE:
        return _ONE_SCORE
    return _six(value)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _six(value)
    if quantized < _ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized <= _ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized > _ONE_SCORE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    seen = set(reason_codes)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in seen)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(field_name: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exact {expected.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{field_name} must be a sha256 digest")
    suffix = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be a sha256 digest")
    _reject_unsafe_public_text(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("payload report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("payload readonly must be True")


def _validate_row_digest(row: ResearchTeamSpecialistQualityControlRow) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest tamper detected in row")


def _validate_report_digest(report: ResearchTeamSpecialistQualityControlReport) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest tamper detected in report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    expected = _payload_digest(payload)
    if payload.get(_DIGEST_FIELD) != expected:
        raise ValueError("derived_validation_digest must match payload")
    rows = payload.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is dict and _DIGEST_FIELD in row:
                expected_row_digest = _payload_digest(row)
                if row.get(_DIGEST_FIELD) != expected_row_digest:
                    raise ValueError("derived_validation_digest must match payload row")


def _payload_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is float:
        raise ValueError("float values are not supported in public payloads")
    if type(value) is int:
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public Decimal values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_STATUSES",
    "ResearchTeamSpecialistQualityControlReportConfig",
    "ResearchTeamSpecialistQualityControlRecord",
    "ResearchTeamSpecialistQualityControlReasonCodeCount",
    "ResearchTeamSpecialistQualityControlRow",
    "ResearchTeamSpecialistQualityControlReport",
    "build_research_team_specialist_quality_control_report",
    "research_team_specialist_quality_control_report_payload",
)
