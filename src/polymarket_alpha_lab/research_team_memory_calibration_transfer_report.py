"""Pure report-only scoring for cross-domain memory calibration transfer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_REPORT_CONFIG_VERSION = (
    "research-team-memory-calibration-transfer-report-v0"
)
RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")

_PASS_REASON = "memory_calibration_transfer_pass"
_EMPTY_REASON = "memory_calibration_transfer_empty"
_PRECEDENT_BLOCK_REASON = "precedent_relevance_block"
_PRECEDENT_WATCH_REASON = "precedent_relevance_watch"
_CORRECTION_BLOCK_REASON = "correction_follow_through_block"
_CORRECTION_WATCH_REASON = "correction_follow_through_watch"
_MEMORY_BLOCK_REASON = "stale_memory_penalty_block"
_MEMORY_WATCH_REASON = "stale_memory_penalty_watch"
_EVIDENCE_BLOCK_REASON = "evidence_reuse_quality_block"
_EVIDENCE_WATCH_REASON = "evidence_reuse_quality_watch"
_PEER_REVIEW_BLOCK_REASON = "peer_review_coverage_block"
_PEER_REVIEW_WATCH_REASON = "peer_review_coverage_watch"
_REVIEW_LATENCY_BLOCK_REASON = "review_latency_block"
_REVIEW_LATENCY_WATCH_REASON = "review_latency_watch"

_REASON_SEQUENCE = (
    _PRECEDENT_BLOCK_REASON,
    _PRECEDENT_WATCH_REASON,
    _CORRECTION_BLOCK_REASON,
    _CORRECTION_WATCH_REASON,
    _MEMORY_BLOCK_REASON,
    _MEMORY_WATCH_REASON,
    _EVIDENCE_BLOCK_REASON,
    _EVIDENCE_WATCH_REASON,
    _PEER_REVIEW_BLOCK_REASON,
    _PEER_REVIEW_WATCH_REASON,
    _REVIEW_LATENCY_BLOCK_REASON,
    _REVIEW_LATENCY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_REASON_RANK = {reason_code: index for index, reason_code in enumerate(_REASON_SEQUENCE)}
_BLOCK_REASONS = {
    _PRECEDENT_BLOCK_REASON,
    _CORRECTION_BLOCK_REASON,
    _MEMORY_BLOCK_REASON,
    _EVIDENCE_BLOCK_REASON,
    _PEER_REVIEW_BLOCK_REASON,
    _REVIEW_LATENCY_BLOCK_REASON,
}
_STATUS_RANK = {
    status: index for index, status in enumerate(RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_STATUSES)
}

_UNSAFE_PUBLIC_HEXES = (
    "63616e646964617465",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
    "64736e",
    "706f7374677265733a2f2f",
    "7461626c655f6e616d65",
    "7461626c65",
    "746f6b656e",
    "736563726574",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "7472616465",
    "74726164696e67",
    "6c697665",
)
_UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii") for value in _UNSAFE_PUBLIC_HEXES
)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationTransferReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_REPORT_CONFIG_VERSION
    )
    min_pass_precedent_relevance_score: Decimal = Decimal("0.750000")
    min_watch_precedent_relevance_score: Decimal = Decimal("0.500000")
    min_pass_correction_follow_through_score: Decimal = Decimal("0.700000")
    min_watch_correction_follow_through_score: Decimal = Decimal("0.450000")
    memory_watch_age_seconds: Decimal = Decimal("86400.000000")
    memory_block_age_seconds: Decimal = Decimal("259200.000000")
    min_pass_evidence_reuse_quality_score: Decimal = Decimal("0.700000")
    min_watch_evidence_reuse_quality_score: Decimal = Decimal("0.450000")
    peer_review_watch_gap_ratio: Decimal = Decimal("0.250000")
    peer_review_block_gap_ratio: Decimal = Decimal("0.500000")
    review_latency_watch_seconds: Decimal = Decimal("86400.000000")
    review_latency_block_seconds: Decimal = Decimal("172800.000000")
    precedent_relevance_weight: Decimal = Decimal("0.200000")
    correction_follow_through_weight: Decimal = Decimal("0.200000")
    stale_memory_penalty_weight: Decimal = Decimal("0.200000")
    evidence_reuse_quality_weight: Decimal = Decimal("0.150000")
    peer_review_coverage_weight: Decimal = Decimal("0.150000")
    review_latency_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamMemoryCalibrationTransferReportConfig)
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_precedent_relevance_score",
            "min_watch_precedent_relevance_score",
            "min_pass_correction_follow_through_score",
            "min_watch_correction_follow_through_score",
            "min_pass_evidence_reuse_quality_score",
            "min_watch_evidence_reuse_quality_score",
            "peer_review_watch_gap_ratio",
            "peer_review_block_gap_ratio",
            "precedent_relevance_weight",
            "correction_follow_through_weight",
            "stale_memory_penalty_weight",
            "evidence_reuse_quality_weight",
            "peer_review_coverage_weight",
            "review_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_watch_age_seconds",
            "memory_block_age_seconds",
            "review_latency_watch_seconds",
            "review_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        _require_pass_above_watch(
            "precedent_relevance_score",
            self.min_pass_precedent_relevance_score,
            self.min_watch_precedent_relevance_score,
        )
        _require_pass_above_watch(
            "correction_follow_through_score",
            self.min_pass_correction_follow_through_score,
            self.min_watch_correction_follow_through_score,
        )
        _require_pass_above_watch(
            "evidence_reuse_quality_score",
            self.min_pass_evidence_reuse_quality_score,
            self.min_watch_evidence_reuse_quality_score,
        )
        if self.memory_block_age_seconds <= self.memory_watch_age_seconds:
            raise ValueError("memory_block_age_seconds must exceed watch threshold")
        if self.peer_review_block_gap_ratio <= self.peer_review_watch_gap_ratio:
            raise ValueError("peer_review_block_gap_ratio must exceed watch threshold")
        if self.review_latency_block_seconds <= self.review_latency_watch_seconds:
            raise ValueError("review_latency_block_seconds must exceed watch threshold")
        weight_sum = _six(
            self.precedent_relevance_weight
            + self.correction_follow_through_weight
            + self.stale_memory_penalty_weight
            + self.evidence_reuse_quality_weight
            + self.peer_review_coverage_weight
            + self.review_latency_weight,
        )
        if weight_sum != _ONE_SCORE:
            raise ValueError("memory calibration transfer weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationTransferRecord:
    team_ref: str
    source_domain_ref: str
    target_domain_ref: str
    transfer_digest: str
    precedent_bundle_digest: str
    correction_bundle_digest: str
    memory_snapshot_digest: str
    evidence_reuse_digest: str
    peer_review_digest: str
    observed_at: datetime
    memory_refreshed_at: datetime
    review_requested_at: datetime
    review_completed_at: datetime
    precedent_relevance_score: Decimal
    correction_follow_through_score: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_required_count: Decimal
    peer_review_completed_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("record", self, ResearchTeamMemoryCalibrationTransferRecord)
        for field_name in ("team_ref", "source_domain_ref", "target_domain_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "transfer_digest",
            "precedent_bundle_digest",
            "correction_bundle_digest",
            "memory_snapshot_digest",
            "evidence_reuse_digest",
            "peer_review_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in (
            "observed_at",
            "memory_refreshed_at",
            "review_requested_at",
            "review_completed_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        if self.review_completed_at < self.review_requested_at:
            raise ValueError("review_completed_at must not be before review_requested_at")
        for field_name in (
            "precedent_relevance_score",
            "correction_follow_through_score",
            "evidence_reuse_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("peer_review_required_count", "peer_review_completed_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.peer_review_completed_count > self.peer_review_required_count:
            raise ValueError("peer_review_completed_count must not exceed required count")
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationTransferRow:
    team_ref: str
    source_domain_ref: str
    target_domain_ref: str
    transfer_digest: str
    precedent_bundle_digest: str
    correction_bundle_digest: str
    memory_snapshot_digest: str
    evidence_reuse_digest: str
    peer_review_digest: str
    observed_at: datetime
    memory_refreshed_at: datetime
    review_requested_at: datetime
    review_completed_at: datetime
    memory_age_seconds: Decimal
    review_latency_seconds: Decimal
    precedent_relevance_score: Decimal
    precedent_relevance_gap: Decimal
    correction_follow_through_score: Decimal
    correction_follow_through_gap: Decimal
    stale_memory_component: Decimal
    evidence_reuse_quality_score: Decimal
    evidence_reuse_quality_gap: Decimal
    peer_review_required_count: Decimal
    peer_review_completed_count: Decimal
    peer_review_coverage_gap_ratio: Decimal
    review_latency_component: Decimal
    transfer_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamMemoryCalibrationTransferRow)
        for field_name in ("team_ref", "source_domain_ref", "target_domain_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "transfer_digest",
            "precedent_bundle_digest",
            "correction_bundle_digest",
            "memory_snapshot_digest",
            "evidence_reuse_digest",
            "peer_review_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in (
            "observed_at",
            "memory_refreshed_at",
            "review_requested_at",
            "review_completed_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        if self.review_completed_at < self.review_requested_at:
            raise ValueError("review_completed_at must not be before review_requested_at")
        for field_name in ("memory_age_seconds", "review_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "precedent_relevance_score",
            "precedent_relevance_gap",
            "correction_follow_through_score",
            "correction_follow_through_gap",
            "stale_memory_component",
            "evidence_reuse_quality_score",
            "evidence_reuse_quality_gap",
            "peer_review_coverage_gap_ratio",
            "review_latency_component",
            "transfer_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("peer_review_required_count", "peer_review_completed_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.peer_review_completed_count > self.peer_review_required_count:
            raise ValueError("peer_review_completed_count must not exceed required count")
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_STATUSES,
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
class ResearchTeamMemoryCalibrationTransferReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamMemoryCalibrationTransferReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCalibrationTransferReport:
    generated_at: datetime
    config_version: str
    transfer_record_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_precedent_relevance_count: Decimal
    correction_follow_through_gap_count: Decimal
    stale_memory_penalty_count: Decimal
    evidence_reuse_quality_gap_count: Decimal
    peer_review_gap_count: Decimal
    review_latency_gap_count: Decimal
    max_transfer_risk_score: Decimal
    average_transfer_risk_score: Decimal
    status: str
    rows: tuple[ResearchTeamMemoryCalibrationTransferRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryCalibrationTransferReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamMemoryCalibrationTransferReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "transfer_record_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_precedent_relevance_count",
            "correction_follow_through_gap_count",
            "stale_memory_penalty_count",
            "evidence_reuse_quality_gap_count",
            "peer_review_gap_count",
            "review_latency_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_transfer_risk_score", "average_transfer_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_STATUSES,
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


def build_research_team_memory_calibration_transfer_report(
    records: list[ResearchTeamMemoryCalibrationTransferRecord]
    | tuple[ResearchTeamMemoryCalibrationTransferRecord, ...],
    *,
    config: ResearchTeamMemoryCalibrationTransferReportConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryCalibrationTransferReport:
    if type(config) is not ResearchTeamMemoryCalibrationTransferReportConfig:
        raise ValueError("config must be a memory calibration transfer report config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_records(records, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_record(
                    record,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for record in items
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamMemoryCalibrationTransferReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        transfer_record_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        low_precedent_relevance_count=_count(
            sum(1 for row in rows if _has_any(row, _PRECEDENT_WATCH_REASON, _PRECEDENT_BLOCK_REASON)),
        ),
        correction_follow_through_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)),
        ),
        stale_memory_penalty_count=_count(
            sum(1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)),
        ),
        evidence_reuse_quality_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)),
        ),
        peer_review_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _PEER_REVIEW_WATCH_REASON, _PEER_REVIEW_BLOCK_REASON)),
        ),
        review_latency_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _REVIEW_LATENCY_WATCH_REASON, _REVIEW_LATENCY_BLOCK_REASON)),
        ),
        max_transfer_risk_score=_max_risk_score(rows),
        average_transfer_risk_score=_average_risk_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_memory_calibration_transfer_report_payload(
    report: ResearchTeamMemoryCalibrationTransferReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_non_string_numeric(report)
        _reject_unsafe_public_payload("memory calibration transfer payload", report)
        _validate_payload_digest(report)
        return report
    if type(report) is not ResearchTeamMemoryCalibrationTransferReport:
        raise ValueError("report must be a memory calibration transfer report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload("memory calibration transfer payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_team_memory_calibration_transfer_report_digest(
    report: ResearchTeamMemoryCalibrationTransferReport | dict[str, Any],
) -> str:
    payload = research_team_memory_calibration_transfer_report_payload(report)
    return _digest_payload_dict(payload)


def _row_from_record(
    record: ResearchTeamMemoryCalibrationTransferRecord,
    *,
    config: ResearchTeamMemoryCalibrationTransferReportConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryCalibrationTransferRow:
    memory_age_seconds = _seconds_between(
        "memory_refreshed_at",
        generated_at,
        record.memory_refreshed_at,
    )
    review_latency_seconds = _seconds_between(
        "review_completed_at",
        record.review_completed_at,
        record.review_requested_at,
    )
    precedent_relevance_gap = _six(_ONE_SCORE - record.precedent_relevance_score)
    correction_follow_through_gap = _six(
        _ONE_SCORE - record.correction_follow_through_score,
    )
    evidence_reuse_quality_gap = _six(_ONE_SCORE - record.evidence_reuse_quality_score)
    stale_memory_component = _capped_ratio(
        memory_age_seconds,
        config.memory_block_age_seconds,
    )
    peer_review_coverage_gap_ratio = _gap_ratio(
        record.peer_review_required_count,
        record.peer_review_completed_count,
    )
    review_latency_component = _capped_ratio(
        review_latency_seconds,
        config.review_latency_block_seconds,
    )
    reason_codes = _row_reason_codes(
        record,
        config=config,
        memory_age_seconds=memory_age_seconds,
        peer_review_coverage_gap_ratio=peer_review_coverage_gap_ratio,
        review_latency_seconds=review_latency_seconds,
    )
    return ResearchTeamMemoryCalibrationTransferRow(
        team_ref=record.team_ref,
        source_domain_ref=record.source_domain_ref,
        target_domain_ref=record.target_domain_ref,
        transfer_digest=record.transfer_digest,
        precedent_bundle_digest=record.precedent_bundle_digest,
        correction_bundle_digest=record.correction_bundle_digest,
        memory_snapshot_digest=record.memory_snapshot_digest,
        evidence_reuse_digest=record.evidence_reuse_digest,
        peer_review_digest=record.peer_review_digest,
        observed_at=record.observed_at,
        memory_refreshed_at=record.memory_refreshed_at,
        review_requested_at=record.review_requested_at,
        review_completed_at=record.review_completed_at,
        memory_age_seconds=memory_age_seconds,
        review_latency_seconds=review_latency_seconds,
        precedent_relevance_score=record.precedent_relevance_score,
        precedent_relevance_gap=precedent_relevance_gap,
        correction_follow_through_score=record.correction_follow_through_score,
        correction_follow_through_gap=correction_follow_through_gap,
        stale_memory_component=stale_memory_component,
        evidence_reuse_quality_score=record.evidence_reuse_quality_score,
        evidence_reuse_quality_gap=evidence_reuse_quality_gap,
        peer_review_required_count=record.peer_review_required_count,
        peer_review_completed_count=record.peer_review_completed_count,
        peer_review_coverage_gap_ratio=peer_review_coverage_gap_ratio,
        review_latency_component=review_latency_component,
        transfer_risk_score=_risk_score(
            precedent_relevance_gap=precedent_relevance_gap,
            correction_follow_through_gap=correction_follow_through_gap,
            stale_memory_component=stale_memory_component,
            evidence_reuse_quality_gap=evidence_reuse_quality_gap,
            peer_review_coverage_gap_ratio=peer_review_coverage_gap_ratio,
            review_latency_component=review_latency_component,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    record: ResearchTeamMemoryCalibrationTransferRecord,
    *,
    config: ResearchTeamMemoryCalibrationTransferReportConfig,
    memory_age_seconds: Decimal,
    peer_review_coverage_gap_ratio: Decimal,
    review_latency_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if record.precedent_relevance_score < config.min_watch_precedent_relevance_score:
        reason_codes.append(_PRECEDENT_BLOCK_REASON)
    elif record.precedent_relevance_score < config.min_pass_precedent_relevance_score:
        reason_codes.append(_PRECEDENT_WATCH_REASON)
    if (
        record.correction_follow_through_score
        < config.min_watch_correction_follow_through_score
    ):
        reason_codes.append(_CORRECTION_BLOCK_REASON)
    elif (
        record.correction_follow_through_score
        < config.min_pass_correction_follow_through_score
    ):
        reason_codes.append(_CORRECTION_WATCH_REASON)
    if memory_age_seconds >= config.memory_block_age_seconds:
        reason_codes.append(_MEMORY_BLOCK_REASON)
    elif memory_age_seconds >= config.memory_watch_age_seconds:
        reason_codes.append(_MEMORY_WATCH_REASON)
    if record.evidence_reuse_quality_score < config.min_watch_evidence_reuse_quality_score:
        reason_codes.append(_EVIDENCE_BLOCK_REASON)
    elif record.evidence_reuse_quality_score < config.min_pass_evidence_reuse_quality_score:
        reason_codes.append(_EVIDENCE_WATCH_REASON)
    if peer_review_coverage_gap_ratio >= config.peer_review_block_gap_ratio:
        reason_codes.append(_PEER_REVIEW_BLOCK_REASON)
    elif peer_review_coverage_gap_ratio >= config.peer_review_watch_gap_ratio:
        reason_codes.append(_PEER_REVIEW_WATCH_REASON)
    if review_latency_seconds >= config.review_latency_block_seconds:
        reason_codes.append(_REVIEW_LATENCY_BLOCK_REASON)
    elif review_latency_seconds >= config.review_latency_watch_seconds:
        reason_codes.append(_REVIEW_LATENCY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchTeamMemoryCalibrationTransferRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryCalibrationTransferRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes = tuple(
        reason_code
        for reason_code in _REASON_SEQUENCE
        if reason_code in present and reason_code != _PASS_REASON
    )
    if not reason_codes:
        return (_PASS_REASON,)
    return reason_codes


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryCalibrationTransferRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemoryCalibrationTransferReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamMemoryCalibrationTransferReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamMemoryCalibrationTransferReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _risk_score(
    *,
    precedent_relevance_gap: Decimal,
    correction_follow_through_gap: Decimal,
    stale_memory_component: Decimal,
    evidence_reuse_quality_gap: Decimal,
    peer_review_coverage_gap_ratio: Decimal,
    review_latency_component: Decimal,
    config: ResearchTeamMemoryCalibrationTransferReportConfig,
) -> Decimal:
    return _six(
        precedent_relevance_gap * config.precedent_relevance_weight
        + correction_follow_through_gap * config.correction_follow_through_weight
        + stale_memory_component * config.stale_memory_penalty_weight
        + evidence_reuse_quality_gap * config.evidence_reuse_quality_weight
        + peer_review_coverage_gap_ratio * config.peer_review_coverage_weight
        + review_latency_component * config.review_latency_weight,
    )


def _gap_ratio(total_count: Decimal, completed_count: Decimal) -> Decimal:
    if total_count <= _ZERO_COUNT:
        return _ZERO_SCORE
    return _six((total_count - completed_count) / total_count)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_SCORE:
        raise ValueError("ratio denominator must be positive")
    return min(_ONE_SCORE, _six(numerator / denominator))


def _max_risk_score(rows: tuple[ResearchTeamMemoryCalibrationTransferRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.transfer_risk_score for row in rows)


def _average_risk_score(rows: tuple[ResearchTeamMemoryCalibrationTransferRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return _six(
        sum((row.transfer_risk_score for row in rows), _ZERO_SCORE) / Decimal(len(rows)),
    )


def _has_any(
    row: ResearchTeamMemoryCalibrationTransferRow,
    watch_reason: str,
    block_reason: str,
) -> bool:
    return watch_reason in row.reason_codes or block_reason in row.reason_codes


def _normalize_records(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchTeamMemoryCalibrationTransferRecord, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    seen: set[tuple[str, str, str, str]] = set()
    for record in records:
        if type(record) is not ResearchTeamMemoryCalibrationTransferRecord:
            raise ValueError("records must contain memory calibration transfer records")
        _require_hard_flags("record", record)
        for field_name in (
            "observed_at",
            "memory_refreshed_at",
            "review_requested_at",
            "review_completed_at",
        ):
            if getattr(record, field_name) > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        key = (
            record.team_ref,
            record.source_domain_ref,
            record.target_domain_ref,
            record.transfer_digest,
        )
        if key in seen:
            raise ValueError("transfer records must be unique")
        seen.add(key)
    return records


def _normalize_rows(value: object) -> tuple[ResearchTeamMemoryCalibrationTransferRow, ...]:
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchTeamMemoryCalibrationTransferRow:
            raise ValueError("rows must contain memory calibration transfer rows")
        _require_hard_flags("row", row)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamMemoryCalibrationTransferReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchTeamMemoryCalibrationTransferReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        _require_hard_flags("reason_code_count", item)
    return tuple(sorted(value, key=lambda item: _REASON_RANK[item.reason_code]))


def _row_sort_key(
    row: ResearchTeamMemoryCalibrationTransferRow,
) -> tuple[int, str, str, str, str]:
    return (
        _STATUS_RANK[row.status],
        row.team_ref,
        row.source_domain_ref,
        row.target_domain_ref,
        row.transfer_digest,
    )


def _validate_row_metrics(row: ResearchTeamMemoryCalibrationTransferRow) -> None:
    if row.precedent_relevance_gap != _six(_ONE_SCORE - row.precedent_relevance_score):
        raise ValueError("precedent_relevance_gap must match precedent_relevance_score")
    if row.correction_follow_through_gap != _six(
        _ONE_SCORE - row.correction_follow_through_score,
    ):
        raise ValueError(
            "correction_follow_through_gap must match correction_follow_through_score",
        )
    if row.evidence_reuse_quality_gap != _six(_ONE_SCORE - row.evidence_reuse_quality_score):
        raise ValueError("evidence_reuse_quality_gap must match evidence_reuse_quality_score")
    expected_peer_gap = _gap_ratio(
        row.peer_review_required_count,
        row.peer_review_completed_count,
    )
    if row.peer_review_coverage_gap_ratio != expected_peer_gap:
        raise ValueError("peer_review_coverage_gap_ratio must match peer review counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_metrics(report: ResearchTeamMemoryCalibrationTransferReport) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.transfer_record_count != _count(len(rows)):
        raise ValueError("transfer_record_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    expected_counts = {
        "low_precedent_relevance_count": sum(
            1 for row in rows if _has_any(row, _PRECEDENT_WATCH_REASON, _PRECEDENT_BLOCK_REASON)
        ),
        "correction_follow_through_gap_count": sum(
            1 for row in rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)
        ),
        "stale_memory_penalty_count": sum(
            1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)
        ),
        "evidence_reuse_quality_gap_count": sum(
            1 for row in rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)
        ),
        "peer_review_gap_count": sum(
            1 for row in rows if _has_any(row, _PEER_REVIEW_WATCH_REASON, _PEER_REVIEW_BLOCK_REASON)
        ),
        "review_latency_gap_count": sum(
            1 for row in rows if _has_any(row, _REVIEW_LATENCY_WATCH_REASON, _REVIEW_LATENCY_BLOCK_REASON)
        ),
    }
    for field_name, expected_count in expected_counts.items():
        if getattr(report, field_name) != _count(expected_count):
            raise ValueError(f"{field_name} must match rows")
    if report.max_transfer_risk_score != _max_risk_score(rows):
        raise ValueError("max_transfer_risk_score must match rows")
    if report.average_transfer_risk_score != _average_risk_score(rows):
        raise ValueError("average_transfer_risk_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_digest(report: ResearchTeamMemoryCalibrationTransferReport) -> None:
    for row in report.rows:
        if row.derived_validation_digest != _digest_value(row):
            raise ValueError("derived_validation_digest tamper detected in row")
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest tamper detected in report")


def _validate_payload_digest(value: object) -> None:
    if type(value) is dict:
        if "derived_validation_digest" in value:
            digest = value["derived_validation_digest"]
            if type(digest) is not str:
                raise ValueError("derived_validation_digest must be a string")
            _require_derived_digest("derived_validation_digest", digest)
            if digest != _digest_payload_dict(value):
                raise ValueError("derived_validation_digest must match payload")
        for item in value.values():
            _validate_payload_digest(item)
        return
    if type(value) is list:
        for item in value:
            _validate_payload_digest(item)


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest value must be a dict")
    return _digest_payload_dict(payload)


def _digest_payload_dict(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is datetime:
        try:
            utc_offset = value.utcoffset()
        except NotImplementedError as exc:
            raise ValueError("datetime payload values must be timezone-aware") from exc
        if value.tzinfo is None or utc_offset is None:
            raise ValueError("datetime payload values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("payload values must not contain primitive numerics")
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool:
        return
    if type(value) is float:
        raise ValueError("payload float values are not allowed")
    if type(value) is int or type(value) is Decimal:
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) is list:
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _payload_value(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_payload_hard_flags(value: object) -> None:
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True")
        for item in value.values():
            if type(item) in (dict, list):
                _require_payload_hard_flags(item)
        return
    if type(value) is list:
        for item in value:
            if type(item) in (dict, list):
                _require_payload_hard_flags(item)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a digest string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{name} must start with sha256:")
    digest = value.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a sha256 digest")


def _require_derived_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a digest string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 digest")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a reason code")
    if value not in _REASON_RANK:
        raise ValueError(f"{name} must be a known reason code")


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{name} must be one of {allowed_values}")


def _require_pass_above_watch(name: str, pass_threshold: Decimal, watch_threshold: Decimal) -> None:
    if pass_threshold <= watch_threshold:
        raise ValueError(f"min pass {name} must exceed watch threshold")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(reason_codes, key=lambda reason_code: _REASON_RANK[reason_code]))


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO_SCORE or value > _ONE_SCORE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _six(value)


def _normalize_positive_six_place_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value <= _ZERO_SCORE:
        raise ValueError(f"{name} must be positive")
    return _six(value)


def _normalize_nonnegative_six_place_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO_SCORE:
        raise ValueError(f"{name} must be nonnegative")
    return _six(value)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return value.quantize(_COUNT_QUANTUM)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    return value.quantize(_SIX_PLACE_QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    try:
        utc_offset = value.utcoffset()
    except NotImplementedError as exc:
        raise ValueError(f"{name} must be timezone-aware datetime") from exc
    if value.tzinfo is None or utc_offset is None:
        raise ValueError(f"{name} must be timezone-aware datetime")
    return value.astimezone(UTC)


def _seconds_between(name: str, later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError(f"{name} must not be in the future")
    delta = later - earlier
    seconds = (
        Decimal(delta.days * int(_SECONDS_PER_DAY))
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _six(seconds)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_STATUSES",
    "ResearchTeamMemoryCalibrationTransferRecord",
    "ResearchTeamMemoryCalibrationTransferReasonCodeCount",
    "ResearchTeamMemoryCalibrationTransferReport",
    "ResearchTeamMemoryCalibrationTransferReportConfig",
    "ResearchTeamMemoryCalibrationTransferRow",
    "build_research_team_memory_calibration_transfer_report",
    "research_team_memory_calibration_transfer_report_digest",
    "research_team_memory_calibration_transfer_report_payload",
)
