"""Pure report-only specialist disagreement memory reducer."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_DISAGREEMENT_MEMORY_REPORT_CONFIG_VERSION = (
    "research-team-specialist-disagreement-memory-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SPECIALIST_DISAGREEMENT_MEMORY_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("6.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_OBSERVATIONS_REASON = "specialist_disagreement_memory_no_observations"
CLEAR_REASON = "specialist_disagreement_memory_clear"
SEVERITY_CAPTURE_BLOCK_REASON = "disagreement_severity_capture_block"
SEVERITY_CAPTURE_WATCH_REASON = "disagreement_severity_capture_watch"
EVIDENCE_COVERAGE_BLOCK_REASON = "evidence_coverage_block"
EVIDENCE_COVERAGE_WATCH_REASON = "evidence_coverage_watch"
RESOLUTION_FOLLOW_UP_BLOCK_REASON = "resolution_follow_up_block"
RESOLUTION_FOLLOW_UP_WATCH_REASON = "resolution_follow_up_watch"
CALIBRATION_MOVEMENT_BLOCK_REASON = "calibration_movement_block"
CALIBRATION_MOVEMENT_WATCH_REASON = "calibration_movement_watch"
STALE_MEMORY_HANDLING_BLOCK_REASON = "stale_memory_handling_block"
STALE_MEMORY_HANDLING_WATCH_REASON = "stale_memory_handling_watch"
PEER_REVIEW_LATENCY_BLOCK_REASON = "peer_review_latency_block"
PEER_REVIEW_LATENCY_WATCH_REASON = "peer_review_latency_watch"

ROW_REASON_CODE_SEQUENCE = (
    SEVERITY_CAPTURE_BLOCK_REASON,
    SEVERITY_CAPTURE_WATCH_REASON,
    EVIDENCE_COVERAGE_BLOCK_REASON,
    EVIDENCE_COVERAGE_WATCH_REASON,
    RESOLUTION_FOLLOW_UP_BLOCK_REASON,
    RESOLUTION_FOLLOW_UP_WATCH_REASON,
    CALIBRATION_MOVEMENT_BLOCK_REASON,
    CALIBRATION_MOVEMENT_WATCH_REASON,
    STALE_MEMORY_HANDLING_BLOCK_REASON,
    STALE_MEMORY_HANDLING_WATCH_REASON,
    PEER_REVIEW_LATENCY_BLOCK_REASON,
    PEER_REVIEW_LATENCY_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "specialist_disagreement_memory_report_clear"
REPORT_BLOCK_PRESENT_REASON = "specialist_disagreement_memory_block_present"
REPORT_WATCH_PRESENT_REASON = "specialist_disagreement_memory_watch_present"
REPORT_SEVERITY_CAPTURE_GAP_REASON = "disagreement_severity_capture_gap_present"
REPORT_EVIDENCE_COVERAGE_GAP_REASON = "evidence_coverage_gap_present"
REPORT_RESOLUTION_FOLLOW_UP_GAP_REASON = "resolution_follow_up_gap_present"
REPORT_CALIBRATION_MOVEMENT_GAP_REASON = "calibration_movement_gap_present"
REPORT_STALE_MEMORY_HANDLING_GAP_REASON = "stale_memory_handling_gap_present"
REPORT_PEER_REVIEW_LATENCY_GAP_REASON = "peer_review_latency_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_SEVERITY_CAPTURE_GAP_REASON,
    REPORT_EVIDENCE_COVERAGE_GAP_REASON,
    REPORT_RESOLUTION_FOLLOW_UP_GAP_REASON,
    REPORT_CALIBRATION_MOVEMENT_GAP_REASON,
    REPORT_STALE_MEMORY_HANDLING_GAP_REASON,
    REPORT_PEER_REVIEW_LATENCY_GAP_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "use_specialist_disagreement_memory_for_research",
    STATUS_WATCH: "review_specialist_disagreement_memory_before_reuse",
    STATUS_BLOCK: "block_specialist_disagreement_memory_until_review",
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
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    _join_parts("priv", "ate"),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_DISAGREEMENT_MEMORY_REPORT_CONFIG_VERSION",
    "SPECIALIST_DISAGREEMENT_MEMORY_STATUSES",
    "ResearchTeamSpecialistDisagreementMemoryConfig",
    "ResearchTeamSpecialistDisagreementMemoryObservation",
    "ResearchTeamSpecialistDisagreementMemoryReasonCodeCount",
    "ResearchTeamSpecialistDisagreementMemoryReport",
    "ResearchTeamSpecialistDisagreementMemoryRow",
    "build_research_team_specialist_disagreement_memory_report",
    "research_team_specialist_disagreement_memory_report_digest",
    "research_team_specialist_disagreement_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistDisagreementMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_DISAGREEMENT_MEMORY_REPORT_CONFIG_VERSION
    )
    min_pass_severity_capture_ratio: Decimal = Decimal("0.850000")
    min_watch_severity_capture_ratio: Decimal = Decimal("0.650000")
    min_pass_evidence_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_evidence_coverage_ratio: Decimal = Decimal("0.600000")
    min_pass_resolution_follow_up_ratio: Decimal = Decimal("0.800000")
    min_watch_resolution_follow_up_ratio: Decimal = Decimal("0.600000")
    min_pass_calibration_movement_ratio: Decimal = Decimal("0.700000")
    min_watch_calibration_movement_ratio: Decimal = Decimal("0.500000")
    min_pass_stale_memory_handling_ratio: Decimal = Decimal("0.800000")
    min_watch_stale_memory_handling_ratio: Decimal = Decimal("0.600000")
    max_pass_peer_review_latency_seconds: Decimal = Decimal("86400.000000")
    max_watch_peer_review_latency_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistDisagreementMemoryConfig:
            raise TypeError(
                "ResearchTeamSpecialistDisagreementMemoryConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistDisagreementMemoryConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_DISAGREEMENT_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "min_pass_severity_capture_ratio",
            "min_watch_severity_capture_ratio",
            "min_pass_evidence_coverage_ratio",
            "min_watch_evidence_coverage_ratio",
            "min_pass_resolution_follow_up_ratio",
            "min_watch_resolution_follow_up_ratio",
            "min_pass_calibration_movement_ratio",
            "min_watch_calibration_movement_ratio",
            "min_pass_stale_memory_handling_ratio",
            "min_watch_stale_memory_handling_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        for name in (
            "max_pass_peer_review_latency_seconds",
            "max_watch_peer_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        if self.min_watch_severity_capture_ratio > self.min_pass_severity_capture_ratio:
            raise ValueError("min_watch_severity_capture_ratio must not exceed pass")
        if self.min_watch_evidence_coverage_ratio > self.min_pass_evidence_coverage_ratio:
            raise ValueError("min_watch_evidence_coverage_ratio must not exceed pass")
        if (
            self.min_watch_resolution_follow_up_ratio
            > self.min_pass_resolution_follow_up_ratio
        ):
            raise ValueError("min_watch_resolution_follow_up_ratio must not exceed pass")
        if (
            self.min_watch_calibration_movement_ratio
            > self.min_pass_calibration_movement_ratio
        ):
            raise ValueError("min_watch_calibration_movement_ratio must not exceed pass")
        if (
            self.min_watch_stale_memory_handling_ratio
            > self.min_pass_stale_memory_handling_ratio
        ):
            raise ValueError("min_watch_stale_memory_handling_ratio must not exceed pass")
        if self.max_watch_peer_review_latency_seconds < (
            self.max_pass_peer_review_latency_seconds
        ):
            raise ValueError("max_watch_peer_review_latency_seconds must be at least pass")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistDisagreementMemoryObservation:
    domain_label: str
    observed_at: datetime
    disagreement_case_count: Decimal
    severe_disagreement_count: Decimal
    severe_disagreement_captured_count: Decimal
    evidence_required_count: Decimal
    evidence_documented_count: Decimal
    resolution_due_count: Decimal
    resolution_followed_up_count: Decimal
    calibration_case_count: Decimal
    calibration_moved_count: Decimal
    stale_memory_item_count: Decimal
    stale_memory_handled_count: Decimal
    peer_review_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistDisagreementMemoryObservation:
            raise TypeError(
                "ResearchTeamSpecialistDisagreementMemoryObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistDisagreementMemoryObservation,
            "item",
        )
        object.__setattr__(
            self,
            "domain_label",
            _require_public_label("domain_label", self.domain_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "disagreement_case_count",
            _require_positive_decimal(
                "disagreement_case_count",
                self.disagreement_case_count,
            ),
        )
        for name in (
            "severe_disagreement_count",
            "severe_disagreement_captured_count",
            "evidence_required_count",
            "evidence_documented_count",
            "resolution_due_count",
            "resolution_followed_up_count",
            "calibration_case_count",
            "calibration_moved_count",
            "stale_memory_item_count",
            "stale_memory_handled_count",
            "peer_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _validate_observation_counts(self)
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistDisagreementMemoryRow:
    domain_label: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    disagreement_case_count: Decimal
    severe_disagreement_count: Decimal
    severe_disagreement_captured_count: Decimal
    evidence_required_count: Decimal
    evidence_documented_count: Decimal
    resolution_due_count: Decimal
    resolution_followed_up_count: Decimal
    calibration_case_count: Decimal
    calibration_moved_count: Decimal
    stale_memory_item_count: Decimal
    stale_memory_handled_count: Decimal
    peer_review_latency_seconds: Decimal
    severity_capture_ratio: Decimal
    evidence_coverage_ratio: Decimal
    resolution_follow_up_ratio: Decimal
    calibration_movement_ratio: Decimal
    stale_memory_handling_ratio: Decimal
    peer_review_timeliness_score: Decimal
    disagreement_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistDisagreementMemoryRow:
            raise TypeError(
                "ResearchTeamSpecialistDisagreementMemoryRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistDisagreementMemoryRow, "row")
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
        object.__setattr__(
            self,
            "disagreement_case_count",
            _require_positive_decimal(
                "disagreement_case_count",
                self.disagreement_case_count,
            ),
        )
        for name in (
            "severe_disagreement_count",
            "severe_disagreement_captured_count",
            "evidence_required_count",
            "evidence_documented_count",
            "resolution_due_count",
            "resolution_followed_up_count",
            "calibration_case_count",
            "calibration_moved_count",
            "stale_memory_item_count",
            "stale_memory_handled_count",
            "peer_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "severity_capture_ratio",
            "evidence_coverage_ratio",
            "resolution_follow_up_ratio",
            "calibration_movement_ratio",
            "stale_memory_handling_ratio",
            "peer_review_timeliness_score",
            "disagreement_memory_score",
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
class ResearchTeamSpecialistDisagreementMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistDisagreementMemoryReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistDisagreementMemoryReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistDisagreementMemoryReasonCodeCount,
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
class ResearchTeamSpecialistDisagreementMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    observation_count: Decimal
    domain_count: Decimal
    disagreement_case_count: Decimal
    severe_disagreement_count: Decimal
    severe_disagreement_captured_count: Decimal
    evidence_required_count: Decimal
    evidence_documented_count: Decimal
    resolution_due_count: Decimal
    resolution_followed_up_count: Decimal
    calibration_case_count: Decimal
    calibration_moved_count: Decimal
    stale_memory_item_count: Decimal
    stale_memory_handled_count: Decimal
    peer_review_latency_seconds: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    severity_capture_ratio: Decimal
    evidence_coverage_ratio: Decimal
    resolution_follow_up_ratio: Decimal
    calibration_movement_ratio: Decimal
    stale_memory_handling_ratio: Decimal
    peer_review_timeliness_score: Decimal
    disagreement_memory_score: Decimal
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistDisagreementMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistDisagreementMemoryReport:
            raise TypeError(
                "ResearchTeamSpecialistDisagreementMemoryReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistDisagreementMemoryReport, "report")
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
            "disagreement_case_count",
            "severe_disagreement_count",
            "severe_disagreement_captured_count",
            "evidence_required_count",
            "evidence_documented_count",
            "resolution_due_count",
            "resolution_followed_up_count",
            "calibration_case_count",
            "calibration_moved_count",
            "stale_memory_item_count",
            "stale_memory_handled_count",
            "peer_review_latency_seconds",
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
            "severity_capture_ratio",
            "evidence_coverage_ratio",
            "resolution_follow_up_ratio",
            "calibration_movement_ratio",
            "stale_memory_handling_ratio",
            "peer_review_timeliness_score",
            "disagreement_memory_score",
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
        return research_team_specialist_disagreement_memory_report_payload(self)


def build_research_team_specialist_disagreement_memory_report(
    observations: Iterable[ResearchTeamSpecialistDisagreementMemoryObservation],
    *,
    config: ResearchTeamSpecialistDisagreementMemoryConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistDisagreementMemoryReport:
    cfg = config or ResearchTeamSpecialistDisagreementMemoryConfig()
    if type(cfg) is not ResearchTeamSpecialistDisagreementMemoryConfig:
        raise ValueError(
            "config must be exactly ResearchTeamSpecialistDisagreementMemoryConfig",
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
    return ResearchTeamSpecialistDisagreementMemoryReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        observation_count=_count_decimal(len(normalized_observations)),
        domain_count=_count_decimal(len({row.domain_label for row in rows})),
        disagreement_case_count=_sum_decimal(row.disagreement_case_count for row in rows),
        severe_disagreement_count=_sum_decimal(
            row.severe_disagreement_count for row in rows
        ),
        severe_disagreement_captured_count=_sum_decimal(
            row.severe_disagreement_captured_count for row in rows
        ),
        evidence_required_count=_sum_decimal(row.evidence_required_count for row in rows),
        evidence_documented_count=_sum_decimal(
            row.evidence_documented_count for row in rows
        ),
        resolution_due_count=_sum_decimal(row.resolution_due_count for row in rows),
        resolution_followed_up_count=_sum_decimal(
            row.resolution_followed_up_count for row in rows
        ),
        calibration_case_count=_sum_decimal(row.calibration_case_count for row in rows),
        calibration_moved_count=_sum_decimal(row.calibration_moved_count for row in rows),
        stale_memory_item_count=_sum_decimal(row.stale_memory_item_count for row in rows),
        stale_memory_handled_count=_sum_decimal(
            row.stale_memory_handled_count for row in rows
        ),
        peer_review_latency_seconds=_average_decimal(
            row.peer_review_latency_seconds for row in rows
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        severity_capture_ratio=_aggregate_severity_capture_ratio(rows),
        evidence_coverage_ratio=_aggregate_evidence_coverage_ratio(rows),
        resolution_follow_up_ratio=_aggregate_resolution_follow_up_ratio(rows),
        calibration_movement_ratio=_aggregate_calibration_movement_ratio(rows),
        stale_memory_handling_ratio=_aggregate_stale_memory_handling_ratio(rows),
        peer_review_timeliness_score=_aggregate_peer_review_timeliness_score(rows),
        disagreement_memory_score=_aggregate_disagreement_memory_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows, len(normalized_observations)),
    )


def research_team_specialist_disagreement_memory_report_payload(
    value: object,
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _reject_raw_payload_numbers(payload)
    _validate_payload_digest(payload)
    _validate_public_payload_shape(payload)
    return payload


def research_team_specialist_disagreement_memory_report_digest(
    report: ResearchTeamSpecialistDisagreementMemoryReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistDisagreementMemoryReport:
        raise ValueError(
            "report must be exactly ResearchTeamSpecialistDisagreementMemoryReport",
        )
    return report.derived_validation_digest


def _row_from_observation(
    observation: ResearchTeamSpecialistDisagreementMemoryObservation,
    *,
    config: ResearchTeamSpecialistDisagreementMemoryConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistDisagreementMemoryRow:
    severity_capture_ratio = _coverage_ratio(
        observation.severe_disagreement_captured_count,
        observation.severe_disagreement_count,
    )
    evidence_coverage_ratio = _coverage_ratio(
        observation.evidence_documented_count,
        observation.evidence_required_count,
    )
    resolution_follow_up_ratio = _coverage_ratio(
        observation.resolution_followed_up_count,
        observation.resolution_due_count,
    )
    calibration_movement_ratio = _coverage_ratio(
        observation.calibration_moved_count,
        observation.calibration_case_count,
    )
    stale_memory_handling_ratio = _coverage_ratio(
        observation.stale_memory_handled_count,
        observation.stale_memory_item_count,
    )
    peer_review_timeliness_score = _peer_review_timeliness_score(
        observation.peer_review_latency_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        severity_capture_ratio=severity_capture_ratio,
        evidence_coverage_ratio=evidence_coverage_ratio,
        resolution_follow_up_ratio=resolution_follow_up_ratio,
        calibration_movement_ratio=calibration_movement_ratio,
        stale_memory_handling_ratio=stale_memory_handling_ratio,
        peer_review_latency_seconds=observation.peer_review_latency_seconds,
        config=config,
    )
    return ResearchTeamSpecialistDisagreementMemoryRow(
        domain_label=observation.domain_label,
        observed_at=observation.observed_at,
        snapshot_age_seconds=_age_seconds(generated_at, observation.observed_at),
        disagreement_case_count=observation.disagreement_case_count,
        severe_disagreement_count=observation.severe_disagreement_count,
        severe_disagreement_captured_count=observation.severe_disagreement_captured_count,
        evidence_required_count=observation.evidence_required_count,
        evidence_documented_count=observation.evidence_documented_count,
        resolution_due_count=observation.resolution_due_count,
        resolution_followed_up_count=observation.resolution_followed_up_count,
        calibration_case_count=observation.calibration_case_count,
        calibration_moved_count=observation.calibration_moved_count,
        stale_memory_item_count=observation.stale_memory_item_count,
        stale_memory_handled_count=observation.stale_memory_handled_count,
        peer_review_latency_seconds=observation.peer_review_latency_seconds,
        severity_capture_ratio=severity_capture_ratio,
        evidence_coverage_ratio=evidence_coverage_ratio,
        resolution_follow_up_ratio=resolution_follow_up_ratio,
        calibration_movement_ratio=calibration_movement_ratio,
        stale_memory_handling_ratio=stale_memory_handling_ratio,
        peer_review_timeliness_score=peer_review_timeliness_score,
        disagreement_memory_score=_disagreement_memory_score(
            severity_capture_ratio=severity_capture_ratio,
            evidence_coverage_ratio=evidence_coverage_ratio,
            resolution_follow_up_ratio=resolution_follow_up_ratio,
            calibration_movement_ratio=calibration_movement_ratio,
            stale_memory_handling_ratio=stale_memory_handling_ratio,
            peer_review_timeliness_score=peer_review_timeliness_score,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    severity_capture_ratio: Decimal,
    evidence_coverage_ratio: Decimal,
    resolution_follow_up_ratio: Decimal,
    calibration_movement_ratio: Decimal,
    stale_memory_handling_ratio: Decimal,
    peer_review_latency_seconds: Decimal,
    config: ResearchTeamSpecialistDisagreementMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if severity_capture_ratio < config.min_watch_severity_capture_ratio:
        reason_codes.append(SEVERITY_CAPTURE_BLOCK_REASON)
    elif severity_capture_ratio < config.min_pass_severity_capture_ratio:
        reason_codes.append(SEVERITY_CAPTURE_WATCH_REASON)
    if evidence_coverage_ratio < config.min_watch_evidence_coverage_ratio:
        reason_codes.append(EVIDENCE_COVERAGE_BLOCK_REASON)
    elif evidence_coverage_ratio < config.min_pass_evidence_coverage_ratio:
        reason_codes.append(EVIDENCE_COVERAGE_WATCH_REASON)
    if resolution_follow_up_ratio < config.min_watch_resolution_follow_up_ratio:
        reason_codes.append(RESOLUTION_FOLLOW_UP_BLOCK_REASON)
    elif resolution_follow_up_ratio < config.min_pass_resolution_follow_up_ratio:
        reason_codes.append(RESOLUTION_FOLLOW_UP_WATCH_REASON)
    if calibration_movement_ratio < config.min_watch_calibration_movement_ratio:
        reason_codes.append(CALIBRATION_MOVEMENT_BLOCK_REASON)
    elif calibration_movement_ratio < config.min_pass_calibration_movement_ratio:
        reason_codes.append(CALIBRATION_MOVEMENT_WATCH_REASON)
    if stale_memory_handling_ratio < config.min_watch_stale_memory_handling_ratio:
        reason_codes.append(STALE_MEMORY_HANDLING_BLOCK_REASON)
    elif stale_memory_handling_ratio < config.min_pass_stale_memory_handling_ratio:
        reason_codes.append(STALE_MEMORY_HANDLING_WATCH_REASON)
    if peer_review_latency_seconds > config.max_watch_peer_review_latency_seconds:
        reason_codes.append(PEER_REVIEW_LATENCY_BLOCK_REASON)
    elif peer_review_latency_seconds > config.max_pass_peer_review_latency_seconds:
        reason_codes.append(PEER_REVIEW_LATENCY_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
    observation_count: int,
) -> tuple[str, ...]:
    if observation_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if _row_reason_count(
        rows,
        (SEVERITY_CAPTURE_BLOCK_REASON, SEVERITY_CAPTURE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_SEVERITY_CAPTURE_GAP_REASON)
    if _row_reason_count(
        rows,
        (EVIDENCE_COVERAGE_BLOCK_REASON, EVIDENCE_COVERAGE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_EVIDENCE_COVERAGE_GAP_REASON)
    if _row_reason_count(
        rows,
        (RESOLUTION_FOLLOW_UP_BLOCK_REASON, RESOLUTION_FOLLOW_UP_WATCH_REASON),
    ):
        reason_codes.append(REPORT_RESOLUTION_FOLLOW_UP_GAP_REASON)
    if _row_reason_count(
        rows,
        (CALIBRATION_MOVEMENT_BLOCK_REASON, CALIBRATION_MOVEMENT_WATCH_REASON),
    ):
        reason_codes.append(REPORT_CALIBRATION_MOVEMENT_GAP_REASON)
    if _row_reason_count(
        rows,
        (STALE_MEMORY_HANDLING_BLOCK_REASON, STALE_MEMORY_HANDLING_WATCH_REASON),
    ):
        reason_codes.append(REPORT_STALE_MEMORY_HANDLING_GAP_REASON)
    if _row_reason_count(
        rows,
        (PEER_REVIEW_LATENCY_BLOCK_REASON, PEER_REVIEW_LATENCY_WATCH_REASON),
    ):
        reason_codes.append(REPORT_PEER_REVIEW_LATENCY_GAP_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _disagreement_memory_score(
    *,
    severity_capture_ratio: Decimal,
    evidence_coverage_ratio: Decimal,
    resolution_follow_up_ratio: Decimal,
    calibration_movement_ratio: Decimal,
    stale_memory_handling_ratio: Decimal,
    peer_review_timeliness_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                severity_capture_ratio
                + evidence_coverage_ratio
                + resolution_follow_up_ratio
                + calibration_movement_ratio
                + stale_memory_handling_ratio
                + peer_review_timeliness_score
            )
            / COMPONENT_COUNT,
        )


def _peer_review_timeliness_score(
    latency_seconds: Decimal,
    *,
    config: ResearchTeamSpecialistDisagreementMemoryConfig,
) -> Decimal:
    if latency_seconds <= config.max_pass_peer_review_latency_seconds:
        return ONE
    if latency_seconds >= config.max_watch_peer_review_latency_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = (
            config.max_watch_peer_review_latency_seconds
            - config.max_pass_peer_review_latency_seconds
        )
        return _quantize(
            (config.max_watch_peer_review_latency_seconds - latency_seconds) / span,
        )


def _aggregate_severity_capture_ratio(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    return _coverage_ratio(
        _sum_decimal(row.severe_disagreement_captured_count for row in rows),
        _sum_decimal(row.severe_disagreement_count for row in rows),
    )


def _aggregate_evidence_coverage_ratio(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    return _coverage_ratio(
        _sum_decimal(row.evidence_documented_count for row in rows),
        _sum_decimal(row.evidence_required_count for row in rows),
    )


def _aggregate_resolution_follow_up_ratio(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    return _coverage_ratio(
        _sum_decimal(row.resolution_followed_up_count for row in rows),
        _sum_decimal(row.resolution_due_count for row in rows),
    )


def _aggregate_calibration_movement_ratio(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    return _coverage_ratio(
        _sum_decimal(row.calibration_moved_count for row in rows),
        _sum_decimal(row.calibration_case_count for row in rows),
    )


def _aggregate_stale_memory_handling_ratio(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    return _coverage_ratio(
        _sum_decimal(row.stale_memory_handled_count for row in rows),
        _sum_decimal(row.stale_memory_item_count for row in rows),
    )


def _aggregate_peer_review_timeliness_score(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    return _average_decimal(row.peer_review_timeliness_score for row in rows)


def _aggregate_disagreement_memory_score(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _disagreement_memory_score(
        severity_capture_ratio=_aggregate_severity_capture_ratio(rows),
        evidence_coverage_ratio=_aggregate_evidence_coverage_ratio(rows),
        resolution_follow_up_ratio=_aggregate_resolution_follow_up_ratio(rows),
        calibration_movement_ratio=_aggregate_calibration_movement_ratio(rows),
        stale_memory_handling_ratio=_aggregate_stale_memory_handling_ratio(rows),
        peer_review_timeliness_score=_aggregate_peer_review_timeliness_score(rows),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> tuple[ResearchTeamSpecialistDisagreementMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistDisagreementMemoryReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamSpecialistDisagreementMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
            row_ratio=_safe_divide(_count_decimal(counter[reason_code]), len_decimal),
        )
        for reason_code in COUNT_REASON_CODE_SEQUENCE
        if counter.get(reason_code, 0)
        for len_decimal in (_count_decimal(len(rows)),)
    )


def _report_status(rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...]) -> str:
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


def _status_count(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _row_reason_count(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> int:
    return sum(
        1
        for row in rows
        if any(reason_code in row.reason_codes for reason_code in reason_codes)
    )


def _row_sort_key(
    row: ResearchTeamSpecialistDisagreementMemoryRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.disagreement_memory_score,
        row.domain_label,
    )


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistDisagreementMemoryObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistDisagreementMemoryObservation, ...]:
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc
    labels: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchTeamSpecialistDisagreementMemoryObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamSpecialistDisagreementMemoryObservation items",
            )
        _require_hard_flags("item", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if observation.domain_label in labels:
            raise ValueError("domain_label values must be unique")
        labels.add(observation.domain_label)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...],
) -> tuple[ResearchTeamSpecialistDisagreementMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecialistDisagreementMemoryRow:
            raise ValueError("rows must contain ResearchTeamSpecialistDisagreementMemoryRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistDisagreementMemoryReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistDisagreementMemoryReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamSpecialistDisagreementMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistDisagreementMemoryReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(
        sorted(counts, key=lambda item: COUNT_REASON_CODE_SEQUENCE.index(item.reason_code)),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _validate_observation_counts(
    observation: ResearchTeamSpecialistDisagreementMemoryObservation,
) -> None:
    _require_not_exceed(
        "severe_disagreement_count",
        observation.severe_disagreement_count,
        "disagreement_case_count",
        observation.disagreement_case_count,
    )
    _require_not_exceed(
        "severe_disagreement_captured_count",
        observation.severe_disagreement_captured_count,
        "severe_disagreement_count",
        observation.severe_disagreement_count,
    )
    _require_not_exceed(
        "evidence_documented_count",
        observation.evidence_documented_count,
        "evidence_required_count",
        observation.evidence_required_count,
    )
    _require_not_exceed(
        "resolution_followed_up_count",
        observation.resolution_followed_up_count,
        "resolution_due_count",
        observation.resolution_due_count,
    )
    _require_not_exceed(
        "calibration_moved_count",
        observation.calibration_moved_count,
        "calibration_case_count",
        observation.calibration_case_count,
    )
    _require_not_exceed(
        "stale_memory_handled_count",
        observation.stale_memory_handled_count,
        "stale_memory_item_count",
        observation.stale_memory_item_count,
    )


def _validate_row(row: ResearchTeamSpecialistDisagreementMemoryRow) -> None:
    _require_not_exceed(
        "severe_disagreement_count",
        row.severe_disagreement_count,
        "disagreement_case_count",
        row.disagreement_case_count,
    )
    _require_not_exceed(
        "severe_disagreement_captured_count",
        row.severe_disagreement_captured_count,
        "severe_disagreement_count",
        row.severe_disagreement_count,
    )
    _require_not_exceed(
        "evidence_documented_count",
        row.evidence_documented_count,
        "evidence_required_count",
        row.evidence_required_count,
    )
    _require_not_exceed(
        "resolution_followed_up_count",
        row.resolution_followed_up_count,
        "resolution_due_count",
        row.resolution_due_count,
    )
    _require_not_exceed(
        "calibration_moved_count",
        row.calibration_moved_count,
        "calibration_case_count",
        row.calibration_case_count,
    )
    _require_not_exceed(
        "stale_memory_handled_count",
        row.stale_memory_handled_count,
        "stale_memory_item_count",
        row.stale_memory_item_count,
    )
    if row.severity_capture_ratio != _coverage_ratio(
        row.severe_disagreement_captured_count,
        row.severe_disagreement_count,
    ):
        raise ValueError("severity_capture_ratio must match row counts")
    if row.evidence_coverage_ratio != _coverage_ratio(
        row.evidence_documented_count,
        row.evidence_required_count,
    ):
        raise ValueError("evidence_coverage_ratio must match row counts")
    if row.resolution_follow_up_ratio != _coverage_ratio(
        row.resolution_followed_up_count,
        row.resolution_due_count,
    ):
        raise ValueError("resolution_follow_up_ratio must match row counts")
    if row.calibration_movement_ratio != _coverage_ratio(
        row.calibration_moved_count,
        row.calibration_case_count,
    ):
        raise ValueError("calibration_movement_ratio must match row counts")
    if row.stale_memory_handling_ratio != _coverage_ratio(
        row.stale_memory_handled_count,
        row.stale_memory_item_count,
    ):
        raise ValueError("stale_memory_handling_ratio must match row counts")
    expected_score = _disagreement_memory_score(
        severity_capture_ratio=row.severity_capture_ratio,
        evidence_coverage_ratio=row.evidence_coverage_ratio,
        resolution_follow_up_ratio=row.resolution_follow_up_ratio,
        calibration_movement_ratio=row.calibration_movement_ratio,
        stale_memory_handling_ratio=row.stale_memory_handling_ratio,
        peer_review_timeliness_score=row.peer_review_timeliness_score,
    )
    if row.disagreement_memory_score != expected_score:
        raise ValueError("disagreement_memory_score must match row component ratios")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match row reason codes")


def _validate_report(report: ResearchTeamSpecialistDisagreementMemoryReport) -> None:
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.domain_count != _count_decimal(len({row.domain_label for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.disagreement_case_count != _sum_decimal(
        row.disagreement_case_count for row in report.rows
    ):
        raise ValueError("disagreement_case_count must match rows")
    if report.severe_disagreement_count != _sum_decimal(
        row.severe_disagreement_count for row in report.rows
    ):
        raise ValueError("severe_disagreement_count must match rows")
    if report.severe_disagreement_captured_count != _sum_decimal(
        row.severe_disagreement_captured_count for row in report.rows
    ):
        raise ValueError("severe_disagreement_captured_count must match rows")
    if report.evidence_required_count != _sum_decimal(
        row.evidence_required_count for row in report.rows
    ):
        raise ValueError("evidence_required_count must match rows")
    if report.evidence_documented_count != _sum_decimal(
        row.evidence_documented_count for row in report.rows
    ):
        raise ValueError("evidence_documented_count must match rows")
    if report.resolution_due_count != _sum_decimal(
        row.resolution_due_count for row in report.rows
    ):
        raise ValueError("resolution_due_count must match rows")
    if report.resolution_followed_up_count != _sum_decimal(
        row.resolution_followed_up_count for row in report.rows
    ):
        raise ValueError("resolution_followed_up_count must match rows")
    if report.calibration_case_count != _sum_decimal(
        row.calibration_case_count for row in report.rows
    ):
        raise ValueError("calibration_case_count must match rows")
    if report.calibration_moved_count != _sum_decimal(
        row.calibration_moved_count for row in report.rows
    ):
        raise ValueError("calibration_moved_count must match rows")
    if report.stale_memory_item_count != _sum_decimal(
        row.stale_memory_item_count for row in report.rows
    ):
        raise ValueError("stale_memory_item_count must match rows")
    if report.stale_memory_handled_count != _sum_decimal(
        row.stale_memory_handled_count for row in report.rows
    ):
        raise ValueError("stale_memory_handled_count must match rows")
    if report.peer_review_latency_seconds != _average_decimal(
        row.peer_review_latency_seconds for row in report.rows
    ):
        raise ValueError("peer_review_latency_seconds must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.severity_capture_ratio != _aggregate_severity_capture_ratio(report.rows):
        raise ValueError("severity_capture_ratio must match rows")
    if report.evidence_coverage_ratio != _aggregate_evidence_coverage_ratio(report.rows):
        raise ValueError("evidence_coverage_ratio must match rows")
    if report.resolution_follow_up_ratio != _aggregate_resolution_follow_up_ratio(
        report.rows,
    ):
        raise ValueError("resolution_follow_up_ratio must match rows")
    if report.calibration_movement_ratio != _aggregate_calibration_movement_ratio(
        report.rows,
    ):
        raise ValueError("calibration_movement_ratio must match rows")
    if report.stale_memory_handling_ratio != _aggregate_stale_memory_handling_ratio(
        report.rows,
    ):
        raise ValueError("stale_memory_handling_ratio must match rows")
    if report.peer_review_timeliness_score != _aggregate_peer_review_timeliness_score(
        report.rows,
    ):
        raise ValueError("peer_review_timeliness_score must match rows")
    if report.disagreement_memory_score != _aggregate_disagreement_memory_score(
        report.rows,
    ):
        raise ValueError("disagreement_memory_score must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, len(report.rows)):
        raise ValueError("reason_codes must match rows")


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ONE
    return _safe_divide(numerator, denominator)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _safe_divide(_sum_decimal(normalized), _count_decimal(len(normalized)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            if type(value) is not Decimal:
                raise ValueError("sum values must be exactly Decimal")
            total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    return _quantize(Decimal(value))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
        )


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty")
    if normalized != value:
        raise ValueError(f"{name} must not have surrounding whitespace")
    if _has_unsafe_public_fragment(normalized):
        raise ValueError(f"{name} must be public-safe")
    return normalized


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must not exceed 1.000000")
    return normalized


def _require_not_exceed(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value > upper_value:
        raise ValueError(f"{lower_name} must not exceed {upper_name}")


def _require_member(name: str, value: str, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if value not in allowed_values:
        raise ValueError(f"{name} must be one of {', '.join(allowed_values)}")
    return value


def _require_status(name: str, value: str) -> str:
    return _require_member(name, value, SPECIALIST_DISAGREEMENT_MEMORY_STATUSES)


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")
    for value in values:
        _require_member(name, value, allowed_values)
    sorted_values = tuple(
        sorted(values, key=lambda value: allowed_values.index(value)),
    )
    if values != sorted_values:
        raise ValueError(f"{name} must be sorted deterministically")
    return values


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hexadecimal")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _require_supported_payload_input(value: object) -> None:
    if type(value) in (ResearchTeamSpecialistDisagreementMemoryReport, dict):
        return
    raise ValueError("payload input must be a report or dict")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return _json_ready(value)
    raise ValueError("payload input must be a report or dict")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, int, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _derived_validation_digest(
    report: ResearchTeamSpecialistDisagreementMemoryReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(payload)
    _reject_raw_payload_numbers(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest_value)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = sha256(encoded.encode("utf-8")).hexdigest()
    if digest_value != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_exact_public_keys(
        payload,
        _public_field_names(ResearchTeamSpecialistDisagreementMemoryReport),
        "unexpected public payload keys",
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list in payload")
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list in payload")
    ResearchTeamSpecialistDisagreementMemoryReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        status=payload["status"],
        next_review_step=payload["next_review_step"],
        observation_count=_payload_decimal(
            "observation_count",
            payload["observation_count"],
        ),
        domain_count=_payload_decimal("domain_count", payload["domain_count"]),
        disagreement_case_count=_payload_decimal(
            "disagreement_case_count",
            payload["disagreement_case_count"],
        ),
        severe_disagreement_count=_payload_decimal(
            "severe_disagreement_count",
            payload["severe_disagreement_count"],
        ),
        severe_disagreement_captured_count=_payload_decimal(
            "severe_disagreement_captured_count",
            payload["severe_disagreement_captured_count"],
        ),
        evidence_required_count=_payload_decimal(
            "evidence_required_count",
            payload["evidence_required_count"],
        ),
        evidence_documented_count=_payload_decimal(
            "evidence_documented_count",
            payload["evidence_documented_count"],
        ),
        resolution_due_count=_payload_decimal(
            "resolution_due_count",
            payload["resolution_due_count"],
        ),
        resolution_followed_up_count=_payload_decimal(
            "resolution_followed_up_count",
            payload["resolution_followed_up_count"],
        ),
        calibration_case_count=_payload_decimal(
            "calibration_case_count",
            payload["calibration_case_count"],
        ),
        calibration_moved_count=_payload_decimal(
            "calibration_moved_count",
            payload["calibration_moved_count"],
        ),
        stale_memory_item_count=_payload_decimal(
            "stale_memory_item_count",
            payload["stale_memory_item_count"],
        ),
        stale_memory_handled_count=_payload_decimal(
            "stale_memory_handled_count",
            payload["stale_memory_handled_count"],
        ),
        peer_review_latency_seconds=_payload_decimal(
            "peer_review_latency_seconds",
            payload["peer_review_latency_seconds"],
        ),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        severity_capture_ratio=_payload_decimal(
            "severity_capture_ratio",
            payload["severity_capture_ratio"],
        ),
        evidence_coverage_ratio=_payload_decimal(
            "evidence_coverage_ratio",
            payload["evidence_coverage_ratio"],
        ),
        resolution_follow_up_ratio=_payload_decimal(
            "resolution_follow_up_ratio",
            payload["resolution_follow_up_ratio"],
        ),
        calibration_movement_ratio=_payload_decimal(
            "calibration_movement_ratio",
            payload["calibration_movement_ratio"],
        ),
        stale_memory_handling_ratio=_payload_decimal(
            "stale_memory_handling_ratio",
            payload["stale_memory_handling_ratio"],
        ),
        peer_review_timeliness_score=_payload_decimal(
            "peer_review_timeliness_score",
            payload["peer_review_timeliness_score"],
        ),
        disagreement_memory_score=_payload_decimal(
            "disagreement_memory_score",
            payload["disagreement_memory_score"],
        ),
        rows=tuple(_payload_row(row) for row in rows),
        reason_code_counts=tuple(
            _payload_reason_code_count(item) for item in reason_code_counts
        ),
        reason_codes=_payload_reason_codes("reason_codes", payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _payload_row(value: object) -> ResearchTeamSpecialistDisagreementMemoryRow:
    if type(value) is not dict:
        raise ValueError("rows must contain objects in payload")
    _require_exact_public_keys(
        value,
        _public_field_names(ResearchTeamSpecialistDisagreementMemoryRow),
        "unexpected public row keys",
    )
    return ResearchTeamSpecialistDisagreementMemoryRow(
        domain_label=value["domain_label"],
        observed_at=_payload_datetime("observed_at", value["observed_at"]),
        snapshot_age_seconds=_payload_decimal(
            "snapshot_age_seconds",
            value["snapshot_age_seconds"],
        ),
        disagreement_case_count=_payload_decimal(
            "disagreement_case_count",
            value["disagreement_case_count"],
        ),
        severe_disagreement_count=_payload_decimal(
            "severe_disagreement_count",
            value["severe_disagreement_count"],
        ),
        severe_disagreement_captured_count=_payload_decimal(
            "severe_disagreement_captured_count",
            value["severe_disagreement_captured_count"],
        ),
        evidence_required_count=_payload_decimal(
            "evidence_required_count",
            value["evidence_required_count"],
        ),
        evidence_documented_count=_payload_decimal(
            "evidence_documented_count",
            value["evidence_documented_count"],
        ),
        resolution_due_count=_payload_decimal(
            "resolution_due_count",
            value["resolution_due_count"],
        ),
        resolution_followed_up_count=_payload_decimal(
            "resolution_followed_up_count",
            value["resolution_followed_up_count"],
        ),
        calibration_case_count=_payload_decimal(
            "calibration_case_count",
            value["calibration_case_count"],
        ),
        calibration_moved_count=_payload_decimal(
            "calibration_moved_count",
            value["calibration_moved_count"],
        ),
        stale_memory_item_count=_payload_decimal(
            "stale_memory_item_count",
            value["stale_memory_item_count"],
        ),
        stale_memory_handled_count=_payload_decimal(
            "stale_memory_handled_count",
            value["stale_memory_handled_count"],
        ),
        peer_review_latency_seconds=_payload_decimal(
            "peer_review_latency_seconds",
            value["peer_review_latency_seconds"],
        ),
        severity_capture_ratio=_payload_decimal(
            "severity_capture_ratio",
            value["severity_capture_ratio"],
        ),
        evidence_coverage_ratio=_payload_decimal(
            "evidence_coverage_ratio",
            value["evidence_coverage_ratio"],
        ),
        resolution_follow_up_ratio=_payload_decimal(
            "resolution_follow_up_ratio",
            value["resolution_follow_up_ratio"],
        ),
        calibration_movement_ratio=_payload_decimal(
            "calibration_movement_ratio",
            value["calibration_movement_ratio"],
        ),
        stale_memory_handling_ratio=_payload_decimal(
            "stale_memory_handling_ratio",
            value["stale_memory_handling_ratio"],
        ),
        peer_review_timeliness_score=_payload_decimal(
            "peer_review_timeliness_score",
            value["peer_review_timeliness_score"],
        ),
        disagreement_memory_score=_payload_decimal(
            "disagreement_memory_score",
            value["disagreement_memory_score"],
        ),
        status=value["status"],
        reason_codes=_payload_reason_codes("reason_codes", value["reason_codes"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _payload_reason_code_count(
    value: object,
) -> ResearchTeamSpecialistDisagreementMemoryReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain objects in payload")
    _require_exact_public_keys(
        value,
        _public_field_names(ResearchTeamSpecialistDisagreementMemoryReasonCodeCount),
        "unexpected public reason_code_count keys",
    )
    return ResearchTeamSpecialistDisagreementMemoryReasonCodeCount(
        reason_code=value["reason_code"],
        count=_payload_decimal("count", value["count"]),
        row_ratio=_payload_decimal("row_ratio", value["row_ratio"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _payload_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list in payload")
    return tuple(value)


def _payload_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string in payload")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string in payload") from exc


def _payload_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string in payload")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string in payload") from exc
    return _as_utc(name, parsed)


def _require_exact_public_keys(
    value: dict[str, Any],
    expected_keys: frozenset[str],
    error_message: str,
) -> None:
    if frozenset(value) != expected_keys:
        raise ValueError(error_message)


def _public_field_names(value: type[object]) -> frozenset[str]:
    return frozenset(item.name for item in fields(value))


def _validate_payload_flags(payload: dict[str, Any], label: str) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _reject_raw_payload_numbers(value: object) -> None:
    if type(value) in (Decimal, int, float):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_payload_numbers(item)
    elif type(value) is list:
        for item in value:
            _reject_raw_payload_numbers(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("unsafe public payload value")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
