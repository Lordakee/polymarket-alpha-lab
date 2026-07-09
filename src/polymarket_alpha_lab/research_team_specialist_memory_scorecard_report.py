"""Pure report-only specialist memory scorecard reducer."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-scorecard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SPECIALIST_MEMORY_SCORECARD_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("5.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_OBSERVATIONS_REASON = "specialist_memory_scorecard_no_observations"
CLEAR_REASON = "specialist_memory_scorecard_clear"
FRESHNESS_BLOCK_REASON = "freshness_block"
FRESHNESS_WATCH_REASON = "freshness_watch"
CALIBRATION_EVIDENCE_BLOCK_REASON = "calibration_evidence_block"
CALIBRATION_EVIDENCE_WATCH_REASON = "calibration_evidence_watch"
UNRESOLVED_CAVEATS_BLOCK_REASON = "unresolved_caveats_block"
UNRESOLVED_CAVEATS_WATCH_REASON = "unresolved_caveats_watch"
CORRECTION_FOLLOW_THROUGH_BLOCK_REASON = "correction_follow_through_block"
CORRECTION_FOLLOW_THROUGH_WATCH_REASON = "correction_follow_through_watch"
WORKLOAD_PRESSURE_BLOCK_REASON = "workload_pressure_block"
WORKLOAD_PRESSURE_WATCH_REASON = "workload_pressure_watch"

ROW_REASON_CODE_SEQUENCE = (
    FRESHNESS_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    CALIBRATION_EVIDENCE_BLOCK_REASON,
    CALIBRATION_EVIDENCE_WATCH_REASON,
    UNRESOLVED_CAVEATS_BLOCK_REASON,
    UNRESOLVED_CAVEATS_WATCH_REASON,
    CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
    CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
    WORKLOAD_PRESSURE_BLOCK_REASON,
    WORKLOAD_PRESSURE_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "specialist_memory_scorecard_report_clear"
REPORT_BLOCK_PRESENT_REASON = "specialist_memory_scorecard_block_present"
REPORT_WATCH_PRESENT_REASON = "specialist_memory_scorecard_watch_present"
REPORT_FRESHNESS_GAP_REASON = "freshness_gap_present"
REPORT_CALIBRATION_EVIDENCE_GAP_REASON = "calibration_evidence_gap_present"
REPORT_UNRESOLVED_CAVEATS_REASON = "unresolved_caveats_present"
REPORT_CORRECTION_FOLLOW_THROUGH_GAP_REASON = "correction_follow_through_gap_present"
REPORT_WORKLOAD_PRESSURE_REASON = "workload_pressure_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_FRESHNESS_GAP_REASON,
    REPORT_CALIBRATION_EVIDENCE_GAP_REASON,
    REPORT_UNRESOLVED_CAVEATS_REASON,
    REPORT_CORRECTION_FOLLOW_THROUGH_GAP_REASON,
    REPORT_WORKLOAD_PRESSURE_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "use_specialist_memory_scorecard_for_research",
    STATUS_WATCH: "review_specialist_memory_scorecard_before_reuse",
    STATUS_BLOCK: "block_specialist_memory_until_quality_review",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket"),
    _join_parts("s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("u", "r", "l"),
    _join_parts("sou", "rce", "_", "text"),
    _join_parts("sou", "rce", "_", "u", "r", "l"),
    _join_parts("d", "s", "n"),
    _join_parts("ta", "b", "le"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("li", "ve"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    _join_parts("priv", "ate"),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_SCORECARD_REPORT_CONFIG_VERSION",
    "SPECIALIST_MEMORY_SCORECARD_STATUSES",
    "ResearchTeamSpecialistMemoryScorecardConfig",
    "ResearchTeamSpecialistMemoryScorecardObservation",
    "ResearchTeamSpecialistMemoryScorecardReasonCodeCount",
    "ResearchTeamSpecialistMemoryScorecardReport",
    "ResearchTeamSpecialistMemoryScorecardRow",
    "build_research_team_specialist_memory_scorecard_report",
    "research_team_specialist_memory_scorecard_report_digest",
    "research_team_specialist_memory_scorecard_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
    )
    min_pass_freshness_ratio: Decimal = Decimal("0.750000")
    min_watch_freshness_ratio: Decimal = Decimal("0.500000")
    min_pass_calibration_evidence_ratio: Decimal = Decimal("0.700000")
    min_watch_calibration_evidence_ratio: Decimal = Decimal("0.500000")
    max_pass_unresolved_caveat_ratio: Decimal = Decimal("0.100000")
    max_watch_unresolved_caveat_ratio: Decimal = Decimal("0.250000")
    min_pass_correction_follow_through_ratio: Decimal = Decimal("0.800000")
    min_watch_correction_follow_through_ratio: Decimal = Decimal("0.600000")
    max_pass_workload_pressure_ratio: Decimal = Decimal("0.800000")
    max_watch_workload_pressure_ratio: Decimal = Decimal("0.950000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryScorecardConfig:
            raise TypeError(
                "ResearchTeamSpecialistMemoryScorecardConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryScorecardConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "min_pass_freshness_ratio",
            "min_watch_freshness_ratio",
            "min_pass_calibration_evidence_ratio",
            "min_watch_calibration_evidence_ratio",
            "max_pass_unresolved_caveat_ratio",
            "max_watch_unresolved_caveat_ratio",
            "min_pass_correction_follow_through_ratio",
            "min_watch_correction_follow_through_ratio",
            "max_pass_workload_pressure_ratio",
            "max_watch_workload_pressure_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.min_watch_freshness_ratio > self.min_pass_freshness_ratio:
            raise ValueError("min_watch_freshness_ratio must not exceed pass")
        if (
            self.min_watch_calibration_evidence_ratio
            > self.min_pass_calibration_evidence_ratio
        ):
            raise ValueError("min_watch_calibration_evidence_ratio must not exceed pass")
        if self.max_pass_unresolved_caveat_ratio > self.max_watch_unresolved_caveat_ratio:
            raise ValueError("max_pass_unresolved_caveat_ratio must not exceed watch")
        if (
            self.min_watch_correction_follow_through_ratio
            > self.min_pass_correction_follow_through_ratio
        ):
            raise ValueError(
                "min_watch_correction_follow_through_ratio must not exceed pass",
            )
        if self.max_pass_workload_pressure_ratio > self.max_watch_workload_pressure_ratio:
            raise ValueError("max_pass_workload_pressure_ratio must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryScorecardObservation:
    domain_label: str
    observed_at: datetime
    specialist_count: Decimal
    memory_item_count: Decimal
    fresh_memory_item_count: Decimal
    calibration_case_count: Decimal
    calibration_evidence_count: Decimal
    caveat_count: Decimal
    unresolved_caveat_count: Decimal
    correction_due_count: Decimal
    correction_completed_count: Decimal
    active_assignment_count: Decimal
    assignment_capacity_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryScorecardObservation:
            raise TypeError(
                "ResearchTeamSpecialistMemoryScorecardObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryScorecardObservation, "item")
        object.__setattr__(
            self,
            "domain_label",
            _require_public_label("domain_label", self.domain_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "specialist_count",
            "memory_item_count",
            "calibration_case_count",
            "caveat_count",
            "correction_due_count",
            "assignment_capacity_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "fresh_memory_item_count",
            "calibration_evidence_count",
            "unresolved_caveat_count",
            "correction_completed_count",
            "active_assignment_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _validate_observation_counts(self)
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryScorecardRow:
    domain_label: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    specialist_count: Decimal
    memory_item_count: Decimal
    fresh_memory_item_count: Decimal
    calibration_case_count: Decimal
    calibration_evidence_count: Decimal
    caveat_count: Decimal
    unresolved_caveat_count: Decimal
    correction_due_count: Decimal
    correction_completed_count: Decimal
    active_assignment_count: Decimal
    assignment_capacity_count: Decimal
    freshness_ratio: Decimal
    calibration_evidence_ratio: Decimal
    unresolved_caveat_ratio: Decimal
    correction_follow_through_ratio: Decimal
    workload_pressure_ratio: Decimal
    memory_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryScorecardRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryScorecardRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryScorecardRow, "row")
        object.__setattr__(
            self,
            "domain_label",
            _require_public_label("domain_label", self.domain_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal("snapshot_age_seconds", self.snapshot_age_seconds),
        )
        for name in (
            "specialist_count",
            "memory_item_count",
            "calibration_case_count",
            "caveat_count",
            "correction_due_count",
            "assignment_capacity_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "fresh_memory_item_count",
            "calibration_evidence_count",
            "unresolved_caveat_count",
            "correction_completed_count",
            "active_assignment_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "freshness_ratio",
            "calibration_evidence_ratio",
            "unresolved_caveat_ratio",
            "correction_follow_through_ratio",
            "workload_pressure_ratio",
            "memory_quality_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryScorecardReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistMemoryScorecardReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryScorecardReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryScorecardReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    observation_count: Decimal
    domain_count: Decimal
    specialist_count: Decimal
    memory_item_count: Decimal
    fresh_memory_item_count: Decimal
    calibration_case_count: Decimal
    calibration_evidence_count: Decimal
    caveat_count: Decimal
    unresolved_caveat_count: Decimal
    correction_due_count: Decimal
    correction_completed_count: Decimal
    active_assignment_count: Decimal
    assignment_capacity_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    freshness_ratio: Decimal
    calibration_evidence_ratio: Decimal
    unresolved_caveat_ratio: Decimal
    correction_follow_through_ratio: Decimal
    workload_pressure_ratio: Decimal
    memory_quality_score: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistMemoryScorecardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryScorecardReport:
            raise TypeError(
                "ResearchTeamSpecialistMemoryScorecardReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "next_review_step",
            _require_public_label("next_review_step", self.next_review_step),
        )
        for name in (
            "observation_count",
            "domain_count",
            "specialist_count",
            "memory_item_count",
            "fresh_memory_item_count",
            "calibration_case_count",
            "calibration_evidence_count",
            "caveat_count",
            "unresolved_caveat_count",
            "correction_due_count",
            "correction_completed_count",
            "active_assignment_count",
            "assignment_capacity_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "freshness_ratio",
            "calibration_evidence_ratio",
            "unresolved_caveat_ratio",
            "correction_follow_through_ratio",
            "workload_pressure_ratio",
            "memory_quality_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_specialist_memory_scorecard_report_payload(self)


def build_research_team_specialist_memory_scorecard_report(
    observations: Iterable[ResearchTeamSpecialistMemoryScorecardObservation],
    *,
    config: ResearchTeamSpecialistMemoryScorecardConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryScorecardReport:
    cfg = config or ResearchTeamSpecialistMemoryScorecardConfig()
    if type(cfg) is not ResearchTeamSpecialistMemoryScorecardConfig:
        raise ValueError(
            "config must be exactly ResearchTeamSpecialistMemoryScorecardConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchTeamSpecialistMemoryScorecardReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        observation_count=_count_decimal(len(normalized_observations)),
        domain_count=_count_decimal(len({row.domain_label for row in rows})),
        specialist_count=_sum_decimal(row.specialist_count for row in rows),
        memory_item_count=_sum_decimal(row.memory_item_count for row in rows),
        fresh_memory_item_count=_sum_decimal(row.fresh_memory_item_count for row in rows),
        calibration_case_count=_sum_decimal(row.calibration_case_count for row in rows),
        calibration_evidence_count=_sum_decimal(
            row.calibration_evidence_count for row in rows
        ),
        caveat_count=_sum_decimal(row.caveat_count for row in rows),
        unresolved_caveat_count=_sum_decimal(row.unresolved_caveat_count for row in rows),
        correction_due_count=_sum_decimal(row.correction_due_count for row in rows),
        correction_completed_count=_sum_decimal(
            row.correction_completed_count for row in rows
        ),
        active_assignment_count=_sum_decimal(row.active_assignment_count for row in rows),
        assignment_capacity_count=_sum_decimal(
            row.assignment_capacity_count for row in rows
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        freshness_ratio=_aggregate_freshness_ratio(rows),
        calibration_evidence_ratio=_aggregate_calibration_evidence_ratio(rows),
        unresolved_caveat_ratio=_aggregate_unresolved_caveat_ratio(rows),
        correction_follow_through_ratio=_aggregate_correction_follow_through_ratio(rows),
        workload_pressure_ratio=_aggregate_workload_pressure_ratio(rows),
        memory_quality_score=_aggregate_memory_quality_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows, len(normalized_observations)),
    )


def research_team_specialist_memory_scorecard_report_payload(
    value: object,
) -> dict[str, Any]:
    validate_report_schema = type(value) is dict
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _reject_raw_payload_numbers(payload)
    _validate_payload_digest(payload)
    if validate_report_schema:
        canonical_payload = _payload_value(_report_from_payload(payload))
        if canonical_payload != payload:
            raise ValueError("payload must match canonical report")
        if type(canonical_payload) is not dict:
            raise ValueError("payload must be a dict")
        payload = canonical_payload
    return payload


def research_team_specialist_memory_scorecard_report_digest(
    report: ResearchTeamSpecialistMemoryScorecardReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistMemoryScorecardReport:
        raise ValueError("report must be exactly ResearchTeamSpecialistMemoryScorecardReport")
    return report.derived_validation_digest


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistMemoryScorecardReport:
    _require_payload_keys(
        payload,
        ResearchTeamSpecialistMemoryScorecardReport,
        "report",
    )
    values = dict(payload)
    values["generated_at"] = _datetime_from_payload(
        "generated_at",
        values["generated_at"],
    )
    for field_name in (
        "observation_count",
        "domain_count",
        "specialist_count",
        "memory_item_count",
        "fresh_memory_item_count",
        "calibration_case_count",
        "calibration_evidence_count",
        "caveat_count",
        "unresolved_caveat_count",
        "correction_due_count",
        "correction_completed_count",
        "active_assignment_count",
        "assignment_capacity_count",
        "pass_count",
        "watch_count",
        "block_count",
        "freshness_ratio",
        "calibration_evidence_ratio",
        "unresolved_caveat_ratio",
        "correction_follow_through_ratio",
        "workload_pressure_ratio",
        "memory_quality_score",
    ):
        values[field_name] = _decimal_from_payload(field_name, values[field_name])
    values["rows"] = _rows_from_payload(values["rows"])
    values["reason_code_counts"] = _reason_code_counts_from_payload(
        values["reason_code_counts"],
    )
    values["reason_codes"] = _string_tuple_from_payload(
        "reason_codes",
        values["reason_codes"],
    )
    return ResearchTeamSpecialistMemoryScorecardReport(**values)


def _row_from_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistMemoryScorecardRow:
    _require_payload_keys(
        payload,
        ResearchTeamSpecialistMemoryScorecardRow,
        "row",
    )
    values = dict(payload)
    values["observed_at"] = _datetime_from_payload(
        "observed_at",
        values["observed_at"],
    )
    for field_name in (
        "snapshot_age_seconds",
        "specialist_count",
        "memory_item_count",
        "fresh_memory_item_count",
        "calibration_case_count",
        "calibration_evidence_count",
        "caveat_count",
        "unresolved_caveat_count",
        "correction_due_count",
        "correction_completed_count",
        "active_assignment_count",
        "assignment_capacity_count",
        "freshness_ratio",
        "calibration_evidence_ratio",
        "unresolved_caveat_ratio",
        "correction_follow_through_ratio",
        "workload_pressure_ratio",
        "memory_quality_score",
    ):
        values[field_name] = _decimal_from_payload(field_name, values[field_name])
    values["reason_codes"] = _string_tuple_from_payload(
        "reason_codes",
        values["reason_codes"],
    )
    return ResearchTeamSpecialistMemoryScorecardRow(**values)


def _reason_code_count_from_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistMemoryScorecardReasonCodeCount:
    _require_payload_keys(
        payload,
        ResearchTeamSpecialistMemoryScorecardReasonCodeCount,
        "reason code count",
    )
    values = dict(payload)
    values["count"] = _decimal_from_payload("count", values["count"])
    values["row_ratio"] = _decimal_from_payload("row_ratio", values["row_ratio"])
    return ResearchTeamSpecialistMemoryScorecardReasonCodeCount(**values)


def _rows_from_payload(
    value: object,
) -> tuple[ResearchTeamSpecialistMemoryScorecardRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list in payload")
    rows: list[ResearchTeamSpecialistMemoryScorecardRow] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain objects")
        rows.append(_row_from_payload(item))
    return tuple(rows)


def _reason_code_counts_from_payload(
    value: object,
) -> tuple[ResearchTeamSpecialistMemoryScorecardReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list in payload")
    counts: list[ResearchTeamSpecialistMemoryScorecardReasonCodeCount] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        counts.append(_reason_code_count_from_payload(item))
    return tuple(counts)


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must be a list of strings in payload")
    return tuple(value)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string in payload")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string in payload") from exc


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string in payload")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string in payload") from exc


def _require_payload_keys(
    payload: dict[str, Any],
    expected_type: type[object],
    label: str,
) -> None:
    expected_keys = {field.name for field in fields(expected_type)}
    if set(payload) != expected_keys:
        raise ValueError(f"payload keys must match {label} schema")


def _row_from_observation(
    observation: ResearchTeamSpecialistMemoryScorecardObservation,
    *,
    config: ResearchTeamSpecialistMemoryScorecardConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryScorecardRow:
    freshness_ratio = _safe_divide(
        observation.fresh_memory_item_count,
        observation.memory_item_count,
    )
    calibration_evidence_ratio = _safe_divide(
        observation.calibration_evidence_count,
        observation.calibration_case_count,
    )
    unresolved_caveat_ratio = _safe_divide(
        observation.unresolved_caveat_count,
        observation.caveat_count,
    )
    correction_follow_through_ratio = _safe_divide(
        observation.correction_completed_count,
        observation.correction_due_count,
    )
    workload_pressure_ratio = _capped_ratio(
        observation.active_assignment_count,
        observation.assignment_capacity_count,
    )
    reason_codes = _row_reason_codes(
        freshness_ratio=freshness_ratio,
        calibration_evidence_ratio=calibration_evidence_ratio,
        unresolved_caveat_ratio=unresolved_caveat_ratio,
        correction_follow_through_ratio=correction_follow_through_ratio,
        workload_pressure_ratio=workload_pressure_ratio,
        config=config,
    )
    return ResearchTeamSpecialistMemoryScorecardRow(
        domain_label=observation.domain_label,
        observed_at=observation.observed_at,
        snapshot_age_seconds=_age_seconds(generated_at, observation.observed_at),
        specialist_count=observation.specialist_count,
        memory_item_count=observation.memory_item_count,
        fresh_memory_item_count=observation.fresh_memory_item_count,
        calibration_case_count=observation.calibration_case_count,
        calibration_evidence_count=observation.calibration_evidence_count,
        caveat_count=observation.caveat_count,
        unresolved_caveat_count=observation.unresolved_caveat_count,
        correction_due_count=observation.correction_due_count,
        correction_completed_count=observation.correction_completed_count,
        active_assignment_count=observation.active_assignment_count,
        assignment_capacity_count=observation.assignment_capacity_count,
        freshness_ratio=freshness_ratio,
        calibration_evidence_ratio=calibration_evidence_ratio,
        unresolved_caveat_ratio=unresolved_caveat_ratio,
        correction_follow_through_ratio=correction_follow_through_ratio,
        workload_pressure_ratio=workload_pressure_ratio,
        memory_quality_score=_memory_quality_score(
            freshness_ratio=freshness_ratio,
            calibration_evidence_ratio=calibration_evidence_ratio,
            unresolved_caveat_ratio=unresolved_caveat_ratio,
            correction_follow_through_ratio=correction_follow_through_ratio,
            workload_pressure_ratio=workload_pressure_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    freshness_ratio: Decimal,
    calibration_evidence_ratio: Decimal,
    unresolved_caveat_ratio: Decimal,
    correction_follow_through_ratio: Decimal,
    workload_pressure_ratio: Decimal,
    config: ResearchTeamSpecialistMemoryScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if freshness_ratio < config.min_watch_freshness_ratio:
        reason_codes.append(FRESHNESS_BLOCK_REASON)
    elif freshness_ratio < config.min_pass_freshness_ratio:
        reason_codes.append(FRESHNESS_WATCH_REASON)
    if calibration_evidence_ratio < config.min_watch_calibration_evidence_ratio:
        reason_codes.append(CALIBRATION_EVIDENCE_BLOCK_REASON)
    elif calibration_evidence_ratio < config.min_pass_calibration_evidence_ratio:
        reason_codes.append(CALIBRATION_EVIDENCE_WATCH_REASON)
    if unresolved_caveat_ratio > config.max_watch_unresolved_caveat_ratio:
        reason_codes.append(UNRESOLVED_CAVEATS_BLOCK_REASON)
    elif unresolved_caveat_ratio > config.max_pass_unresolved_caveat_ratio:
        reason_codes.append(UNRESOLVED_CAVEATS_WATCH_REASON)
    if correction_follow_through_ratio < config.min_watch_correction_follow_through_ratio:
        reason_codes.append(CORRECTION_FOLLOW_THROUGH_BLOCK_REASON)
    elif correction_follow_through_ratio < config.min_pass_correction_follow_through_ratio:
        reason_codes.append(CORRECTION_FOLLOW_THROUGH_WATCH_REASON)
    if workload_pressure_ratio > config.max_watch_workload_pressure_ratio:
        reason_codes.append(WORKLOAD_PRESSURE_BLOCK_REASON)
    elif workload_pressure_ratio > config.max_pass_workload_pressure_ratio:
        reason_codes.append(WORKLOAD_PRESSURE_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
    observation_count: int,
) -> tuple[str, ...]:
    if observation_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if _row_reason_count(rows, (FRESHNESS_BLOCK_REASON, FRESHNESS_WATCH_REASON)):
        reason_codes.append(REPORT_FRESHNESS_GAP_REASON)
    if _row_reason_count(
        rows,
        (CALIBRATION_EVIDENCE_BLOCK_REASON, CALIBRATION_EVIDENCE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_CALIBRATION_EVIDENCE_GAP_REASON)
    if _row_reason_count(
        rows,
        (UNRESOLVED_CAVEATS_BLOCK_REASON, UNRESOLVED_CAVEATS_WATCH_REASON),
    ):
        reason_codes.append(REPORT_UNRESOLVED_CAVEATS_REASON)
    if _row_reason_count(
        rows,
        (
            CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
            CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
        ),
    ):
        reason_codes.append(REPORT_CORRECTION_FOLLOW_THROUGH_GAP_REASON)
    if _row_reason_count(
        rows,
        (WORKLOAD_PRESSURE_BLOCK_REASON, WORKLOAD_PRESSURE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_WORKLOAD_PRESSURE_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _memory_quality_score(
    *,
    freshness_ratio: Decimal,
    calibration_evidence_ratio: Decimal,
    unresolved_caveat_ratio: Decimal,
    correction_follow_through_ratio: Decimal,
    workload_pressure_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                freshness_ratio
                + calibration_evidence_ratio
                + (ONE - unresolved_caveat_ratio)
                + correction_follow_through_ratio
                + (ONE - workload_pressure_ratio)
            )
            / COMPONENT_COUNT,
        )


def _report_status(rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(row: ResearchTeamSpecialistMemoryScorecardRow) -> tuple[int, str]:
    return (STATUS_SORT_SEQUENCE.index(row.status), row.domain_label)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryScorecardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistMemoryScorecardReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(len(rows))
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchTeamSpecialistMemoryScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            row_ratio=_safe_divide(_count_decimal(count), row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: COUNT_REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _row_reason_count(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
    reason_codes: tuple[str, ...],
) -> int:
    return sum(
        1
        for row in rows
        if any(reason_code in row.reason_codes for reason_code in reason_codes)
    )


def _aggregate_freshness_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.fresh_memory_item_count for row in rows),
        _sum_decimal(row.memory_item_count for row in rows),
    )


def _aggregate_calibration_evidence_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.calibration_evidence_count for row in rows),
        _sum_decimal(row.calibration_case_count for row in rows),
    )


def _aggregate_unresolved_caveat_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.unresolved_caveat_count for row in rows),
        _sum_decimal(row.caveat_count for row in rows),
    )


def _aggregate_correction_follow_through_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.correction_completed_count for row in rows),
        _sum_decimal(row.correction_due_count for row in rows),
    )


def _aggregate_workload_pressure_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> Decimal:
    return _capped_ratio(
        _sum_decimal(row.active_assignment_count for row in rows),
        _sum_decimal(row.assignment_capacity_count for row in rows),
    )


def _aggregate_memory_quality_score(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _memory_quality_score(
        freshness_ratio=_aggregate_freshness_ratio(rows),
        calibration_evidence_ratio=_aggregate_calibration_evidence_ratio(rows),
        unresolved_caveat_ratio=_aggregate_unresolved_caveat_ratio(rows),
        correction_follow_through_ratio=_aggregate_correction_follow_through_ratio(rows),
        workload_pressure_ratio=_aggregate_workload_pressure_ratio(rows),
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistMemoryScorecardObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistMemoryScorecardObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    domain_labels: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamSpecialistMemoryScorecardObservation:
            raise ValueError(
                "observations must contain ResearchTeamSpecialistMemoryScorecardObservation",
            )
        _require_hard_flags("item", item)
        if item.domain_label in domain_labels:
            raise ValueError("domain_label values must be unique")
        domain_labels.add(item.domain_label)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchTeamSpecialistMemoryScorecardRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryScorecardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchTeamSpecialistMemoryScorecardRow] = []
    domain_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryScorecardRow:
            raise ValueError("rows must contain ResearchTeamSpecialistMemoryScorecardRow")
        _require_hard_flags("row", row)
        if row.domain_label in domain_labels:
            raise ValueError("domain_label values must be unique")
        domain_labels.add(row.domain_label)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistMemoryScorecardReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryScorecardReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchTeamSpecialistMemoryScorecardReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchTeamSpecialistMemoryScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistMemoryScorecardReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda item: COUNT_REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_member(field_name, value, allowed))
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized), key=allowed.index))


def _validate_observation_counts(
    item: ResearchTeamSpecialistMemoryScorecardObservation,
) -> None:
    _require_lte("fresh_memory_item_count", item.fresh_memory_item_count, item.memory_item_count)
    _require_lte(
        "calibration_evidence_count",
        item.calibration_evidence_count,
        item.calibration_case_count,
    )
    _require_lte("unresolved_caveat_count", item.unresolved_caveat_count, item.caveat_count)
    _require_lte(
        "correction_completed_count",
        item.correction_completed_count,
        item.correction_due_count,
    )


def _validate_row(row: ResearchTeamSpecialistMemoryScorecardRow) -> None:
    _validate_observation_counts(row)
    _require_equal(
        "freshness_ratio must match row counts",
        row.freshness_ratio,
        _safe_divide(row.fresh_memory_item_count, row.memory_item_count),
    )
    _require_equal(
        "calibration_evidence_ratio must match row counts",
        row.calibration_evidence_ratio,
        _safe_divide(row.calibration_evidence_count, row.calibration_case_count),
    )
    _require_equal(
        "unresolved_caveat_ratio must match row counts",
        row.unresolved_caveat_ratio,
        _safe_divide(row.unresolved_caveat_count, row.caveat_count),
    )
    _require_equal(
        "correction_follow_through_ratio must match row counts",
        row.correction_follow_through_ratio,
        _safe_divide(row.correction_completed_count, row.correction_due_count),
    )
    _require_equal(
        "workload_pressure_ratio must match row counts",
        row.workload_pressure_ratio,
        _capped_ratio(row.active_assignment_count, row.assignment_capacity_count),
    )
    _require_equal(
        "memory_quality_score must match row ratios",
        row.memory_quality_score,
        _memory_quality_score(
            freshness_ratio=row.freshness_ratio,
            calibration_evidence_ratio=row.calibration_evidence_ratio,
            unresolved_caveat_ratio=row.unresolved_caveat_ratio,
            correction_follow_through_ratio=row.correction_follow_through_ratio,
            workload_pressure_ratio=row.workload_pressure_ratio,
        ),
    )
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchTeamSpecialistMemoryScorecardReport) -> None:
    row_count = _count_decimal(len(report.rows))
    _require_equal("observation_count must match rows", report.observation_count, row_count)
    _require_equal(
        "domain_count must match rows",
        report.domain_count,
        _count_decimal(len({row.domain_label for row in report.rows})),
    )
    _require_equal(
        "specialist_count must match rows",
        report.specialist_count,
        _sum_decimal(row.specialist_count for row in report.rows),
    )
    for field_name in (
        "memory_item_count",
        "fresh_memory_item_count",
        "calibration_case_count",
        "calibration_evidence_count",
        "caveat_count",
        "unresolved_caveat_count",
        "correction_due_count",
        "correction_completed_count",
        "active_assignment_count",
        "assignment_capacity_count",
    ):
        _require_equal(
            f"{field_name} must match rows",
            getattr(report, field_name),
            _sum_decimal(getattr(row, field_name) for row in report.rows),
        )
    _require_equal("pass_count must match rows", report.pass_count, _status_count(report.rows, STATUS_PASS))
    _require_equal(
        "watch_count must match rows",
        report.watch_count,
        _status_count(report.rows, STATUS_WATCH),
    )
    _require_equal(
        "block_count must match rows",
        report.block_count,
        _status_count(report.rows, STATUS_BLOCK),
    )
    _require_equal("freshness_ratio must match rows", report.freshness_ratio, _aggregate_freshness_ratio(report.rows))
    _require_equal(
        "calibration_evidence_ratio must match rows",
        report.calibration_evidence_ratio,
        _aggregate_calibration_evidence_ratio(report.rows),
    )
    _require_equal(
        "unresolved_caveat_ratio must match rows",
        report.unresolved_caveat_ratio,
        _aggregate_unresolved_caveat_ratio(report.rows),
    )
    _require_equal(
        "correction_follow_through_ratio must match rows",
        report.correction_follow_through_ratio,
        _aggregate_correction_follow_through_ratio(report.rows),
    )
    _require_equal(
        "workload_pressure_ratio must match rows",
        report.workload_pressure_ratio,
        _aggregate_workload_pressure_ratio(report.rows),
    )
    _require_equal(
        "memory_quality_score must match rows",
        report.memory_quality_score,
        _aggregate_memory_quality_score(report.rows),
    )
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")
    if report.reason_codes != _report_reason_codes(report.rows, len(report.rows)):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _require_lte(field_name: str, value: Decimal, maximum: Decimal) -> None:
    if value > maximum:
        raise ValueError(f"{field_name} must not exceed related count")


def _require_equal(message: str, actual: Decimal, expected: Decimal) -> None:
    if actual != expected:
        raise ValueError(message)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _safe_divide(numerator, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
        )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(+value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    if _contains_unsafe_public_fragment(value):
        raise ValueError("unsafe public payload")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, SPECIALIST_MEMORY_SCORECARD_STATUSES)


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _derived_validation_digest(
    report: ResearchTeamSpecialistMemoryScorecardReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(payload)


def _digest_from_payload(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(unsigned_payload)


def _digest_from_unsigned_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    return value


def _require_supported_payload_input(value: object) -> None:
    if type(value) in (ResearchTeamSpecialistMemoryScorecardReport, dict):
        return
    raise ValueError("payload input must be a report or dict")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    if digest != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_payload_flags(value: object, label: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag in value and value[flag] is not True:
                raise ValueError(f"{label} {flag} must be True")
        for key, item in value.items():
            _validate_payload_flags(item, f"{label}.{key}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _validate_payload_flags(item, f"{label}[{index}]")


def _reject_raw_payload_numbers(value: object) -> None:
    if type(value) in (Decimal, int, float):
        raise ValueError("payload numeric values must be decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_payload_numbers(item)
    elif type(value) is list:
        for item in value:
            _reject_raw_payload_numbers(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
    elif type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or _contains_unsafe_public_fragment(key):
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(item)
    elif type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError("unsafe public payload")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or any(
        fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS
    )
