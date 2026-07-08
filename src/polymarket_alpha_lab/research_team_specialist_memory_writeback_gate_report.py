"""Pure aggregate specialist memory writeback gate report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_WRITEBACK_GATE_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-writeback-gate-report-v0"
)
SPECIALIST_MEMORY_WRITEBACK_GATE_STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
COMPONENT_COUNT = Decimal("4.000000")

NO_NOTES_REASON = "specialist_memory_writeback_no_outcome_learning_notes"
GATE_PASS_REASON = "specialist_memory_writeback_gate_pass"
GATE_WATCH_REASON = "specialist_memory_writeback_gate_watch"
GATE_BLOCK_REASON = "specialist_memory_writeback_gate_block"
MANUAL_PASS_REASON = "manual_review_specialist_memory_writeback_pass"
MANUAL_WATCH_REASON = "manual_review_specialist_memory_writeback_watch"
MANUAL_BLOCK_REASON = "manual_review_specialist_memory_writeback_block"
CALIBRATION_WATCH_REASON = "calibration_feedback_completeness_watch"
CALIBRATION_BLOCK_REASON = "calibration_feedback_completeness_block"
STALE_LABEL_WATCH_REASON = "stale_thesis_label_coverage_watch"
STALE_LABEL_BLOCK_REASON = "stale_thesis_label_coverage_block"
ERROR_TAXONOMY_WATCH_REASON = "error_taxonomy_coverage_watch"
ERROR_TAXONOMY_BLOCK_REASON = "error_taxonomy_coverage_block"
BACKLOG_WATCH_REASON = "review_backlog_pressure_watch"
BACKLOG_BLOCK_REASON = "review_backlog_pressure_block"

REASON_CODES = (
    NO_NOTES_REASON,
    GATE_BLOCK_REASON,
    MANUAL_BLOCK_REASON,
    CALIBRATION_BLOCK_REASON,
    STALE_LABEL_BLOCK_REASON,
    ERROR_TAXONOMY_BLOCK_REASON,
    BACKLOG_BLOCK_REASON,
    GATE_WATCH_REASON,
    MANUAL_WATCH_REASON,
    CALIBRATION_WATCH_REASON,
    STALE_LABEL_WATCH_REASON,
    ERROR_TAXONOMY_WATCH_REASON,
    BACKLOG_WATCH_REASON,
    GATE_PASS_REASON,
    MANUAL_PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
SUMMARY_REASON_PRIORITY = (
    GATE_BLOCK_REASON,
    CALIBRATION_BLOCK_REASON,
    STALE_LABEL_BLOCK_REASON,
    ERROR_TAXONOMY_BLOCK_REASON,
    BACKLOG_BLOCK_REASON,
    GATE_WATCH_REASON,
    CALIBRATION_WATCH_REASON,
    STALE_LABEL_WATCH_REASON,
    ERROR_TAXONOMY_WATCH_REASON,
    BACKLOG_WATCH_REASON,
    GATE_PASS_REASON,
)
NEXT_REVIEW_STEPS = {
    "pass": "allow_specialist_memory_writeback",
    "watch": "review_specialist_memory_writeback_before_use",
    "block": "block_specialist_memory_writeback_until_review",
}
UNSAFE_PUBLIC_FRAGMENTS = (
    "ra" + "w",
    "wall" + "et",
    "sec" + "ret",
    "cred" + "ential",
    "priv" + "ate",
    "source" + "_id",
    "source" + "_text",
    "source" + "_url",
    "source" + "_reference",
    "market" + "_id",
    "market" + "_slug",
    "condition" + "_id",
    "token" + "_id",
    "quest" + "ion",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_WRITEBACK_GATE_REPORT_CONFIG_VERSION",
    "SPECIALIST_MEMORY_WRITEBACK_GATE_STATUSES",
    "ResearchTeamSpecialistMemoryWritebackGateConfig",
    "ResearchTeamSpecialistMemoryWritebackGateInput",
    "ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount",
    "ResearchTeamSpecialistMemoryWritebackGateReport",
    "ResearchTeamSpecialistMemoryWritebackGateRow",
    "build_research_team_specialist_memory_writeback_gate_report",
    "research_team_specialist_memory_writeback_gate_report_digest",
    "research_team_specialist_memory_writeback_gate_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryWritebackGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_WRITEBACK_GATE_REPORT_CONFIG_VERSION
    )
    min_pass_calibration_feedback_completeness_ratio: Decimal = Decimal("0.800000")
    min_watch_calibration_feedback_completeness_ratio: Decimal = Decimal("0.600000")
    min_pass_stale_thesis_label_ratio: Decimal = Decimal("0.750000")
    min_watch_stale_thesis_label_ratio: Decimal = Decimal("0.500000")
    min_pass_error_taxonomy_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_error_taxonomy_coverage_ratio: Decimal = Decimal("0.600000")
    max_pass_review_backlog_pressure: Decimal = Decimal("0.100000")
    max_watch_review_backlog_pressure: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryWritebackGateConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_WRITEBACK_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_calibration_feedback_completeness_ratio",
            "min_watch_calibration_feedback_completeness_ratio",
            "min_pass_stale_thesis_label_ratio",
            "min_watch_stale_thesis_label_ratio",
            "min_pass_error_taxonomy_coverage_ratio",
            "min_watch_error_taxonomy_coverage_ratio",
            "max_pass_review_backlog_pressure",
            "max_watch_review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_watch_calibration_feedback_completeness_ratio
            > self.min_pass_calibration_feedback_completeness_ratio
        ):
            raise ValueError("min_watch_calibration_feedback must not exceed pass")
        if self.min_watch_stale_thesis_label_ratio > self.min_pass_stale_thesis_label_ratio:
            raise ValueError("min_watch_stale_thesis must not exceed pass")
        if (
            self.min_watch_error_taxonomy_coverage_ratio
            > self.min_pass_error_taxonomy_coverage_ratio
        ):
            raise ValueError("min_watch_error_taxonomy must not exceed pass")
        if self.max_pass_review_backlog_pressure > self.max_watch_review_backlog_pressure:
            raise ValueError("max_pass_review_backlog_pressure must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryWritebackGateInput:
    specialist_label: str
    category_label: str
    observed_at: datetime
    outcome_learning_note_count: Decimal
    calibration_feedback_complete_count: Decimal
    stale_thesis_labeled_count: Decimal
    error_taxonomy_tagged_count: Decimal
    open_review_backlog_count: Decimal
    high_priority_review_backlog_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryWritebackGateInput,
            "input",
        )
        _require_public_label("specialist_label", self.specialist_label)
        _require_public_label("category_label", self.category_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "outcome_learning_note_count",
            _require_positive_whole_decimal(
                "outcome_learning_note_count",
                self.outcome_learning_note_count,
            ),
        )
        for field_name in (
            "calibration_feedback_complete_count",
            "stale_thesis_labeled_count",
            "error_taxonomy_tagged_count",
            "open_review_backlog_count",
            "high_priority_review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryWritebackGateRow:
    specialist_label: str
    category_label: str
    observed_at: datetime
    outcome_learning_note_count: Decimal
    calibration_feedback_complete_count: Decimal
    stale_thesis_labeled_count: Decimal
    error_taxonomy_tagged_count: Decimal
    open_review_backlog_count: Decimal
    high_priority_review_backlog_count: Decimal
    calibration_feedback_completeness_ratio: Decimal
    stale_thesis_label_ratio: Decimal
    error_taxonomy_coverage_ratio: Decimal
    review_backlog_pressure: Decimal
    writeback_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryWritebackGateRow,
            "row",
        )
        _require_public_label("specialist_label", self.specialist_label)
        _require_public_label("category_label", self.category_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "outcome_learning_note_count",
            _require_positive_whole_decimal(
                "outcome_learning_note_count",
                self.outcome_learning_note_count,
            ),
        )
        for field_name in (
            "calibration_feedback_complete_count",
            "stale_thesis_labeled_count",
            "error_taxonomy_tagged_count",
            "open_review_backlog_count",
            "high_priority_review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_feedback_completeness_ratio",
            "stale_thesis_label_ratio",
            "error_taxonomy_coverage_ratio",
            "review_backlog_pressure",
            "writeback_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_row_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryWritebackGateReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    specialist_category_count: Decimal
    outcome_learning_note_count: Decimal
    calibration_feedback_complete_count: Decimal
    stale_thesis_labeled_count: Decimal
    error_taxonomy_tagged_count: Decimal
    open_review_backlog_count: Decimal
    high_priority_review_backlog_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    calibration_feedback_completeness_ratio: Decimal
    stale_thesis_label_ratio: Decimal
    error_taxonomy_coverage_ratio: Decimal
    review_backlog_pressure: Decimal
    writeback_readiness_score: Decimal
    status: str
    next_review_step: str
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryWritebackGateReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "specialist_category_count",
            "outcome_learning_note_count",
            "calibration_feedback_complete_count",
            "stale_thesis_labeled_count",
            "error_taxonomy_tagged_count",
            "open_review_backlog_count",
            "high_priority_review_backlog_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_feedback_completeness_ratio",
            "stale_thesis_label_ratio",
            "error_taxonomy_coverage_ratio",
            "review_backlog_pressure",
            "writeback_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_label("next_review_step", self.next_review_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_summary_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_payload_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_team_specialist_memory_writeback_gate_report(
    inputs: Iterable[object],
    *,
    config: ResearchTeamSpecialistMemoryWritebackGateConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryWritebackGateReport:
    if type(config) is not ResearchTeamSpecialistMemoryWritebackGateConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistMemoryWritebackGateConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs, generated_at=generated_at_utc)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(
            input_items,
            key=lambda item: (item.specialist_label, item.category_label),
        )
    )
    reason_codes = _summary_reason_codes(rows)
    status = _summary_status(reason_codes)
    return ResearchTeamSpecialistMemoryWritebackGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        specialist_category_count=_decimal_count(len(rows)),
        outcome_learning_note_count=_sum_row_decimal(rows, "outcome_learning_note_count"),
        calibration_feedback_complete_count=_sum_row_decimal(
            rows,
            "calibration_feedback_complete_count",
        ),
        stale_thesis_labeled_count=_sum_row_decimal(rows, "stale_thesis_labeled_count"),
        error_taxonomy_tagged_count=_sum_row_decimal(rows, "error_taxonomy_tagged_count"),
        open_review_backlog_count=_sum_row_decimal(rows, "open_review_backlog_count"),
        high_priority_review_backlog_count=_sum_row_decimal(
            rows,
            "high_priority_review_backlog_count",
        ),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        calibration_feedback_completeness_ratio=_aggregate_ratio(
            rows,
            "calibration_feedback_complete_count",
        ),
        stale_thesis_label_ratio=_aggregate_ratio(rows, "stale_thesis_labeled_count"),
        error_taxonomy_coverage_ratio=_aggregate_ratio(rows, "error_taxonomy_tagged_count"),
        review_backlog_pressure=_aggregate_ratio(rows, "open_review_backlog_count"),
        writeback_readiness_score=_aggregate_readiness_score(rows),
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_specialist_memory_writeback_gate_report_payload(
    value: object,
) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchTeamSpecialistMemoryWritebackGateConfig,
            ResearchTeamSpecialistMemoryWritebackGateInput,
            ResearchTeamSpecialistMemoryWritebackGateRow,
            ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount,
            ResearchTeamSpecialistMemoryWritebackGateReport,
        ),
    ):
        _require_hard_flags("payload", value)
    elif type(value) is not dict:
        raise ValueError(
            "value must be a specialist memory writeback gate dataclass or JSON object",
        )
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("specialist memory writeback gate payload must be an object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    return payload


def research_team_specialist_memory_writeback_gate_report_digest(
    report: ResearchTeamSpecialistMemoryWritebackGateReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistMemoryWritebackGateReport:
        raise ValueError(
            "report must be a ResearchTeamSpecialistMemoryWritebackGateReport",
        )
    return report.derived_validation_digest


def _row_from_input(
    item: ResearchTeamSpecialistMemoryWritebackGateInput,
    *,
    config: ResearchTeamSpecialistMemoryWritebackGateConfig,
) -> ResearchTeamSpecialistMemoryWritebackGateRow:
    calibration_ratio = _safe_ratio(
        item.calibration_feedback_complete_count,
        item.outcome_learning_note_count,
    )
    stale_label_ratio = _safe_ratio(
        item.stale_thesis_labeled_count,
        item.outcome_learning_note_count,
    )
    taxonomy_ratio = _safe_ratio(
        item.error_taxonomy_tagged_count,
        item.outcome_learning_note_count,
    )
    backlog_pressure = _safe_ratio(
        item.open_review_backlog_count,
        item.outcome_learning_note_count,
    )
    status = _row_status(
        calibration_feedback_completeness_ratio=calibration_ratio,
        stale_thesis_label_ratio=stale_label_ratio,
        error_taxonomy_coverage_ratio=taxonomy_ratio,
        review_backlog_pressure=backlog_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        calibration_feedback_completeness_ratio=calibration_ratio,
        stale_thesis_label_ratio=stale_label_ratio,
        error_taxonomy_coverage_ratio=taxonomy_ratio,
        review_backlog_pressure=backlog_pressure,
        status=status,
        input_reason_codes=item.reason_codes,
        config=config,
    )
    return ResearchTeamSpecialistMemoryWritebackGateRow(
        specialist_label=item.specialist_label,
        category_label=item.category_label,
        observed_at=item.observed_at,
        outcome_learning_note_count=item.outcome_learning_note_count,
        calibration_feedback_complete_count=item.calibration_feedback_complete_count,
        stale_thesis_labeled_count=item.stale_thesis_labeled_count,
        error_taxonomy_tagged_count=item.error_taxonomy_tagged_count,
        open_review_backlog_count=item.open_review_backlog_count,
        high_priority_review_backlog_count=item.high_priority_review_backlog_count,
        calibration_feedback_completeness_ratio=calibration_ratio,
        stale_thesis_label_ratio=stale_label_ratio,
        error_taxonomy_coverage_ratio=taxonomy_ratio,
        review_backlog_pressure=backlog_pressure,
        writeback_readiness_score=_readiness_score(
            calibration_feedback_completeness_ratio=calibration_ratio,
            stale_thesis_label_ratio=stale_label_ratio,
            error_taxonomy_coverage_ratio=taxonomy_ratio,
            review_backlog_pressure=backlog_pressure,
        ),
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    calibration_feedback_completeness_ratio: Decimal,
    stale_thesis_label_ratio: Decimal,
    error_taxonomy_coverage_ratio: Decimal,
    review_backlog_pressure: Decimal,
    config: ResearchTeamSpecialistMemoryWritebackGateConfig,
) -> str:
    if (
        calibration_feedback_completeness_ratio
        < config.min_watch_calibration_feedback_completeness_ratio
        or stale_thesis_label_ratio < config.min_watch_stale_thesis_label_ratio
        or error_taxonomy_coverage_ratio < config.min_watch_error_taxonomy_coverage_ratio
        or review_backlog_pressure > config.max_watch_review_backlog_pressure
    ):
        return "block"
    if (
        calibration_feedback_completeness_ratio
        < config.min_pass_calibration_feedback_completeness_ratio
        or stale_thesis_label_ratio < config.min_pass_stale_thesis_label_ratio
        or error_taxonomy_coverage_ratio < config.min_pass_error_taxonomy_coverage_ratio
        or review_backlog_pressure > config.max_pass_review_backlog_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    calibration_feedback_completeness_ratio: Decimal,
    stale_thesis_label_ratio: Decimal,
    error_taxonomy_coverage_ratio: Decimal,
    review_backlog_pressure: Decimal,
    status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchTeamSpecialistMemoryWritebackGateConfig,
) -> tuple[str, ...]:
    codes: list[str] = [
        {
            "pass": GATE_PASS_REASON,
            "watch": GATE_WATCH_REASON,
            "block": GATE_BLOCK_REASON,
        }[status],
        {
            "pass": MANUAL_PASS_REASON,
            "watch": MANUAL_WATCH_REASON,
            "block": MANUAL_BLOCK_REASON,
        }[status],
    ]
    _append_component_reason(
        codes,
        _minimum_component_status(
            calibration_feedback_completeness_ratio,
            config.min_pass_calibration_feedback_completeness_ratio,
            config.min_watch_calibration_feedback_completeness_ratio,
        ),
        watch_reason=CALIBRATION_WATCH_REASON,
        block_reason=CALIBRATION_BLOCK_REASON,
    )
    _append_component_reason(
        codes,
        _minimum_component_status(
            stale_thesis_label_ratio,
            config.min_pass_stale_thesis_label_ratio,
            config.min_watch_stale_thesis_label_ratio,
        ),
        watch_reason=STALE_LABEL_WATCH_REASON,
        block_reason=STALE_LABEL_BLOCK_REASON,
    )
    _append_component_reason(
        codes,
        _minimum_component_status(
            error_taxonomy_coverage_ratio,
            config.min_pass_error_taxonomy_coverage_ratio,
            config.min_watch_error_taxonomy_coverage_ratio,
        ),
        watch_reason=ERROR_TAXONOMY_WATCH_REASON,
        block_reason=ERROR_TAXONOMY_BLOCK_REASON,
    )
    _append_component_reason(
        codes,
        _maximum_component_status(
            review_backlog_pressure,
            config.max_pass_review_backlog_pressure,
            config.max_watch_review_backlog_pressure,
        ),
        watch_reason=BACKLOG_WATCH_REASON,
        block_reason=BACKLOG_BLOCK_REASON,
    )
    for code in input_reason_codes:
        codes.append(f"input_{code}")
    return tuple(sorted(set(codes), key=_reason_code_sort_key))


def _minimum_component_status(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _maximum_component_status(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _append_component_reason(
    codes: list[str],
    status: str,
    *,
    watch_reason: str,
    block_reason: str,
) -> None:
    if status == "watch":
        codes.append(watch_reason)
    elif status == "block":
        codes.append(block_reason)


def _normalize_inputs(
    inputs: Iterable[object],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistMemoryWritebackGateInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized: list[ResearchTeamSpecialistMemoryWritebackGateInput] = []
    seen_pairs: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not ResearchTeamSpecialistMemoryWritebackGateInput:
            raise ValueError(
                "inputs must contain ResearchTeamSpecialistMemoryWritebackGateInput",
            )
        _require_hard_flags("input", value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        pair = (value.specialist_label, value.category_label)
        if pair in seen_pairs:
            raise ValueError("specialist/category values must be unique")
        seen_pairs.add(pair)
        normalized.append(value)
    return tuple(normalized)


def _summary_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_NOTES_REASON,)
    if all(row.status == "pass" for row in rows):
        return (GATE_PASS_REASON,)
    row_codes = {code for row in rows for code in row.reason_codes}
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append(GATE_BLOCK_REASON)
    elif any(row.status == "watch" for row in rows):
        codes.append(GATE_WATCH_REASON)
    for code in (
        CALIBRATION_BLOCK_REASON,
        STALE_LABEL_BLOCK_REASON,
        ERROR_TAXONOMY_BLOCK_REASON,
        BACKLOG_BLOCK_REASON,
        CALIBRATION_WATCH_REASON,
        STALE_LABEL_WATCH_REASON,
        ERROR_TAXONOMY_WATCH_REASON,
        BACKLOG_WATCH_REASON,
    ):
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (NO_NOTES_REASON,):
        return "block"
    if GATE_BLOCK_REASON in reason_codes:
        return "block"
    if GATE_WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount(
                reason_code=NO_NOTES_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in reason_codes
    )


def _aggregate_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
    field_name: str,
) -> Decimal:
    total_notes = _sum_row_decimal(rows, "outcome_learning_note_count")
    if total_notes == ZERO:
        return ZERO
    return _safe_ratio(_sum_row_decimal(rows, field_name), total_notes)


def _aggregate_readiness_score(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _readiness_score(
        calibration_feedback_completeness_ratio=_aggregate_ratio(
            rows,
            "calibration_feedback_complete_count",
        ),
        stale_thesis_label_ratio=_aggregate_ratio(rows, "stale_thesis_labeled_count"),
        error_taxonomy_coverage_ratio=_aggregate_ratio(rows, "error_taxonomy_tagged_count"),
        review_backlog_pressure=_aggregate_ratio(rows, "open_review_backlog_count"),
    )


def _readiness_score(
    *,
    calibration_feedback_completeness_ratio: Decimal,
    stale_thesis_label_ratio: Decimal,
    error_taxonomy_coverage_ratio: Decimal,
    review_backlog_pressure: Decimal,
) -> Decimal:
    return _quantize(
        (
            calibration_feedback_completeness_ratio
            + stale_thesis_label_ratio
            + error_taxonomy_coverage_ratio
            + (ONE - review_backlog_pressure)
        )
        / COMPONENT_COUNT,
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _sum_row_decimal(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
    field_name: str,
) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO)


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_input_counts(
    item: ResearchTeamSpecialistMemoryWritebackGateInput,
) -> None:
    for field_name in (
        "calibration_feedback_complete_count",
        "stale_thesis_labeled_count",
        "error_taxonomy_tagged_count",
        "open_review_backlog_count",
    ):
        if getattr(item, field_name) > item.outcome_learning_note_count:
            raise ValueError(f"{field_name} cannot exceed outcome_learning_note_count")
    if item.high_priority_review_backlog_count > item.open_review_backlog_count:
        raise ValueError(
            "high_priority_review_backlog_count cannot exceed open_review_backlog_count",
        )


def _validate_row_consistency(
    row: ResearchTeamSpecialistMemoryWritebackGateRow,
) -> None:
    expected_ratios = {
        "calibration_feedback_completeness_ratio": _safe_ratio(
            row.calibration_feedback_complete_count,
            row.outcome_learning_note_count,
        ),
        "stale_thesis_label_ratio": _safe_ratio(
            row.stale_thesis_labeled_count,
            row.outcome_learning_note_count,
        ),
        "error_taxonomy_coverage_ratio": _safe_ratio(
            row.error_taxonomy_tagged_count,
            row.outcome_learning_note_count,
        ),
        "review_backlog_pressure": _safe_ratio(
            row.open_review_backlog_count,
            row.outcome_learning_note_count,
        ),
    }
    for field_name, expected_value in expected_ratios.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match row counts")
    expected_score = _readiness_score(
        calibration_feedback_completeness_ratio=row.calibration_feedback_completeness_ratio,
        stale_thesis_label_ratio=row.stale_thesis_label_ratio,
        error_taxonomy_coverage_ratio=row.error_taxonomy_coverage_ratio,
        review_backlog_pressure=row.review_backlog_pressure,
    )
    if row.writeback_readiness_score != expected_score:
        raise ValueError("writeback_readiness_score must match row ratios")
    expected_status_code = {
        "pass": GATE_PASS_REASON,
        "watch": GATE_WATCH_REASON,
        "block": GATE_BLOCK_REASON,
    }[row.status]
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(
        code.endswith(("_watch", "_block")) for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")
    if row.status == "watch" and any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")


def _validate_report_consistency(
    report: ResearchTeamSpecialistMemoryWritebackGateReport,
) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.specialist_category_count != _decimal_count(len(report.rows)):
        raise ValueError("specialist_category_count must match rows")
    for field_name in (
        "outcome_learning_note_count",
        "calibration_feedback_complete_count",
        "stale_thesis_labeled_count",
        "error_taxonomy_tagged_count",
        "open_review_backlog_count",
        "high_priority_review_backlog_count",
    ):
        if getattr(report, field_name) != _sum_row_decimal(report.rows, field_name):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_ratios = {
        "calibration_feedback_completeness_ratio": _aggregate_ratio(
            report.rows,
            "calibration_feedback_complete_count",
        ),
        "stale_thesis_label_ratio": _aggregate_ratio(
            report.rows,
            "stale_thesis_labeled_count",
        ),
        "error_taxonomy_coverage_ratio": _aggregate_ratio(
            report.rows,
            "error_taxonomy_tagged_count",
        ),
        "review_backlog_pressure": _aggregate_ratio(
            report.rows,
            "open_review_backlog_count",
        ),
        "writeback_readiness_score": _aggregate_readiness_score(report.rows),
    }
    for field_name, expected_value in expected_ratios.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryWritebackGateRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_pairs: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistMemoryWritebackGateRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistMemoryWritebackGateRow",
            )
        _require_hard_flags("row", row)
        pair = (row.specialist_label, row.category_label)
        if pair in seen_pairs:
            raise ValueError("rows specialist/category values must be unique")
        seen_pairs.add(pair)
    if normalized != tuple(
        sorted(normalized, key=lambda row: (row.specialist_label, row.category_label))
    ):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistMemoryWritebackGateReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda count: _reason_code_sort_key(count.reason_code))):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized


def _normalize_input_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code("reason_codes", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must be nonempty")
    normalized = tuple(values)
    for value in normalized:
        _require_reason_code("reason_codes", value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(sorted(normalized, key=_reason_code_sort_key)):
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _normalize_summary_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_row_reason_codes(values)
    if not all(value in SUMMARY_REASON_PRIORITY or value == NO_NOTES_REASON for value in normalized):
        raise ValueError("reason_codes must contain summary reason codes")
    return normalized


def _reason_code_sort_key(value: str) -> tuple[int, str]:
    return (REASON_CODE_RANK.get(value, len(REASON_CODE_RANK)), value)


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _validate_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, nested_item in enumerate(item):
                    if type(nested_item) is dict:
                        _validate_payload_flags(nested_item, f"{field_path}.{key}.{index}")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        return
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if digest != _digest_payload(payload):
        raise ValueError("derived_validation_digest must match payload")


def _report_payload_digest(report: ResearchTeamSpecialistMemoryWritebackGateReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload field or value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public safe")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    if " " in value:
        raise ValueError(f"{field_name} must contain compact reason codes")
    _reject_unsafe_public_text(value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_MEMORY_WRITEBACK_GATE_STATUSES:
        raise ValueError(
            f"{field_name} must be one of {SPECIALIST_MEMORY_WRITEBACK_GATE_STATUSES}",
        )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
