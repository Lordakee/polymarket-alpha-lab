from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
from typing import Any, Mapping


DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_REPORT_CONFIG_VERSION = (
    "research-team-specialist-evidence-reuse-quality-report-v0"
)
RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_FIELD = "derived_validation_digest"

_PASS_REASON = "evidence_reuse_quality_pass"
_EMPTY_REASON = "evidence_reuse_quality_empty"
_PRECEDENT_BLOCK_REASON = "precedent_relevance_block"
_PRECEDENT_WATCH_REASON = "precedent_relevance_watch"
_SOURCE_BLOCK_REASON = "source_freshness_block"
_SOURCE_WATCH_REASON = "source_freshness_watch"
_MEMORY_BLOCK_REASON = "stale_memory_block"
_MEMORY_WATCH_REASON = "stale_memory_watch"
_CALIBRATION_BLOCK_REASON = "calibration_contribution_block"
_CALIBRATION_WATCH_REASON = "calibration_contribution_watch"
_CONTRADICTION_BLOCK_REASON = "contradiction_handling_block"
_CONTRADICTION_WATCH_REASON = "contradiction_handling_watch"
_PEER_REVIEW_BLOCK_REASON = "peer_review_coverage_block"
_PEER_REVIEW_WATCH_REASON = "peer_review_coverage_watch"

_REASON_SEQUENCE = (
    _PRECEDENT_BLOCK_REASON,
    _PRECEDENT_WATCH_REASON,
    _SOURCE_BLOCK_REASON,
    _SOURCE_WATCH_REASON,
    _MEMORY_BLOCK_REASON,
    _MEMORY_WATCH_REASON,
    _CALIBRATION_BLOCK_REASON,
    _CALIBRATION_WATCH_REASON,
    _CONTRADICTION_BLOCK_REASON,
    _CONTRADICTION_WATCH_REASON,
    _PEER_REVIEW_BLOCK_REASON,
    _PEER_REVIEW_WATCH_REASON,
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
class ResearchTeamSpecialistEvidenceReuseQualityReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_REPORT_CONFIG_VERSION
    )
    min_pass_precedent_relevance_score: Decimal = Decimal("0.750000")
    min_watch_precedent_relevance_score: Decimal = Decimal("0.500000")
    source_watch_age_seconds: Decimal = Decimal("86400.000000")
    source_block_age_seconds: Decimal = Decimal("259200.000000")
    memory_watch_age_seconds: Decimal = Decimal("86400.000000")
    memory_block_age_seconds: Decimal = Decimal("259200.000000")
    min_pass_calibration_contribution_score: Decimal = Decimal("0.650000")
    min_watch_calibration_contribution_score: Decimal = Decimal("0.400000")
    contradiction_watch_gap_ratio: Decimal = Decimal("0.250000")
    contradiction_block_gap_ratio: Decimal = Decimal("0.500000")
    peer_review_watch_gap_ratio: Decimal = Decimal("0.250000")
    peer_review_block_gap_ratio: Decimal = Decimal("0.500000")
    precedent_relevance_weight: Decimal = Decimal("0.200000")
    source_freshness_weight: Decimal = Decimal("0.150000")
    stale_memory_weight: Decimal = Decimal("0.150000")
    calibration_contribution_weight: Decimal = Decimal("0.200000")
    contradiction_handling_weight: Decimal = Decimal("0.150000")
    peer_review_coverage_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamSpecialistEvidenceReuseQualityReportConfig,
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_precedent_relevance_score",
            "min_watch_precedent_relevance_score",
            "min_pass_calibration_contribution_score",
            "min_watch_calibration_contribution_score",
            "contradiction_watch_gap_ratio",
            "contradiction_block_gap_ratio",
            "peer_review_watch_gap_ratio",
            "peer_review_block_gap_ratio",
            "precedent_relevance_weight",
            "source_freshness_weight",
            "stale_memory_weight",
            "calibration_contribution_weight",
            "contradiction_handling_weight",
            "peer_review_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_watch_age_seconds",
            "source_block_age_seconds",
            "memory_watch_age_seconds",
            "memory_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_precedent_relevance_score
            <= self.min_watch_precedent_relevance_score
        ):
            raise ValueError("min_pass_precedent_relevance_score must exceed watch threshold")
        if self.source_block_age_seconds <= self.source_watch_age_seconds:
            raise ValueError("source_block_age_seconds must exceed watch threshold")
        if self.memory_block_age_seconds <= self.memory_watch_age_seconds:
            raise ValueError("memory_block_age_seconds must exceed watch threshold")
        if (
            self.min_pass_calibration_contribution_score
            <= self.min_watch_calibration_contribution_score
        ):
            raise ValueError(
                "min_pass_calibration_contribution_score must exceed watch threshold",
            )
        if self.contradiction_block_gap_ratio <= self.contradiction_watch_gap_ratio:
            raise ValueError("contradiction_block_gap_ratio must exceed watch threshold")
        if self.peer_review_block_gap_ratio <= self.peer_review_watch_gap_ratio:
            raise ValueError("peer_review_block_gap_ratio must exceed watch threshold")
        weight_sum = _six(
            self.precedent_relevance_weight
            + self.source_freshness_weight
            + self.stale_memory_weight
            + self.calibration_contribution_weight
            + self.contradiction_handling_weight
            + self.peer_review_coverage_weight,
        )
        if weight_sum != _ONE_SCORE:
            raise ValueError("evidence reuse quality weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReuseQualityRecord:
    team_ref: str
    specialist_ref: str
    evidence_reuse_digest: str
    precedent_bundle_digest: str
    source_bundle_digest: str
    memory_snapshot_digest: str
    calibration_digest: str
    peer_review_digest: str
    observed_at: datetime
    source_last_observed_at: datetime
    memory_refreshed_at: datetime
    precedent_relevance_score: Decimal
    calibration_contribution_score: Decimal
    contradiction_total_count: Decimal
    contradiction_resolved_count: Decimal
    peer_review_required_count: Decimal
    peer_review_completed_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("record", self, ResearchTeamSpecialistEvidenceReuseQualityRecord)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_reuse_digest",
            "precedent_bundle_digest",
            "source_bundle_digest",
            "memory_snapshot_digest",
            "calibration_digest",
            "peer_review_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in (
            "observed_at",
            "source_last_observed_at",
            "memory_refreshed_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "precedent_relevance_score",
            "calibration_contribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_total_count",
            "contradiction_resolved_count",
            "peer_review_required_count",
            "peer_review_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.contradiction_resolved_count > self.contradiction_total_count:
            raise ValueError("contradiction_resolved_count must not exceed total count")
        if self.peer_review_completed_count > self.peer_review_required_count:
            raise ValueError("peer_review_completed_count must not exceed required count")
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReuseQualityRow:
    team_ref: str
    specialist_ref: str
    evidence_reuse_digest: str
    precedent_bundle_digest: str
    source_bundle_digest: str
    memory_snapshot_digest: str
    calibration_digest: str
    peer_review_digest: str
    observed_at: datetime
    source_last_observed_at: datetime
    memory_refreshed_at: datetime
    source_age_seconds: Decimal
    memory_age_seconds: Decimal
    precedent_relevance_score: Decimal
    precedent_relevance_gap: Decimal
    source_freshness_component: Decimal
    stale_memory_component: Decimal
    calibration_contribution_score: Decimal
    calibration_contribution_gap: Decimal
    contradiction_total_count: Decimal
    contradiction_resolved_count: Decimal
    contradiction_handling_gap_ratio: Decimal
    peer_review_required_count: Decimal
    peer_review_completed_count: Decimal
    peer_review_coverage_gap_ratio: Decimal
    evidence_reuse_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamSpecialistEvidenceReuseQualityRow)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_reuse_digest",
            "precedent_bundle_digest",
            "source_bundle_digest",
            "memory_snapshot_digest",
            "calibration_digest",
            "peer_review_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in (
            "observed_at",
            "source_last_observed_at",
            "memory_refreshed_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in ("source_age_seconds", "memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "precedent_relevance_score",
            "precedent_relevance_gap",
            "source_freshness_component",
            "stale_memory_component",
            "calibration_contribution_score",
            "calibration_contribution_gap",
            "contradiction_handling_gap_ratio",
            "peer_review_coverage_gap_ratio",
            "evidence_reuse_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_total_count",
            "contradiction_resolved_count",
            "peer_review_required_count",
            "peer_review_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES,
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
class ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReuseQualityReport:
    generated_at: datetime
    config_version: str
    reuse_record_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_precedent_relevance_count: Decimal
    stale_source_count: Decimal
    stale_memory_count: Decimal
    low_calibration_contribution_count: Decimal
    contradiction_gap_count: Decimal
    peer_review_gap_count: Decimal
    max_evidence_reuse_risk_score: Decimal
    average_evidence_reuse_risk_score: Decimal
    status: str
    rows: tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamSpecialistEvidenceReuseQualityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "reuse_record_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_precedent_relevance_count",
            "stale_source_count",
            "stale_memory_count",
            "low_calibration_contribution_count",
            "contradiction_gap_count",
            "peer_review_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_reuse_risk_score",
            "average_evidence_reuse_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES,
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


def build_research_team_specialist_evidence_reuse_quality_report(
    records: list[ResearchTeamSpecialistEvidenceReuseQualityRecord]
    | tuple[ResearchTeamSpecialistEvidenceReuseQualityRecord, ...],
    *,
    config: ResearchTeamSpecialistEvidenceReuseQualityReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistEvidenceReuseQualityReport:
    if type(config) is not ResearchTeamSpecialistEvidenceReuseQualityReportConfig:
        raise ValueError("config must be an evidence reuse quality report config")
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
    return ResearchTeamSpecialistEvidenceReuseQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        reuse_record_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        low_precedent_relevance_count=_count(
            sum(1 for row in rows if _has_any(row, _PRECEDENT_WATCH_REASON, _PRECEDENT_BLOCK_REASON)),
        ),
        stale_source_count=_count(
            sum(1 for row in rows if _has_any(row, _SOURCE_WATCH_REASON, _SOURCE_BLOCK_REASON)),
        ),
        stale_memory_count=_count(
            sum(1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)),
        ),
        low_calibration_contribution_count=_count(
            sum(1 for row in rows if _has_any(row, _CALIBRATION_WATCH_REASON, _CALIBRATION_BLOCK_REASON)),
        ),
        contradiction_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _CONTRADICTION_WATCH_REASON, _CONTRADICTION_BLOCK_REASON)),
        ),
        peer_review_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _PEER_REVIEW_WATCH_REASON, _PEER_REVIEW_BLOCK_REASON)),
        ),
        max_evidence_reuse_risk_score=_max_risk_score(rows),
        average_evidence_reuse_risk_score=_average_risk_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_specialist_evidence_reuse_quality_report_payload(
    report: ResearchTeamSpecialistEvidenceReuseQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_non_string_numeric(report)
        _reject_unsafe_public_payload("evidence reuse quality payload", report)
        _validate_payload_digest(report)
        return report
    if type(report) is not ResearchTeamSpecialistEvidenceReuseQualityReport:
        raise ValueError("report must be an evidence reuse quality report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload("evidence reuse quality payload", payload)
    _validate_payload_digest(payload)
    return payload


def _row_from_record(
    record: ResearchTeamSpecialistEvidenceReuseQualityRecord,
    *,
    config: ResearchTeamSpecialistEvidenceReuseQualityReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistEvidenceReuseQualityRow:
    source_age_seconds = _seconds_between(generated_at, record.source_last_observed_at)
    memory_age_seconds = _seconds_between(generated_at, record.memory_refreshed_at)
    contradiction_handling_gap_ratio = _gap_ratio(
        record.contradiction_total_count,
        record.contradiction_resolved_count,
    )
    peer_review_coverage_gap_ratio = _gap_ratio(
        record.peer_review_required_count,
        record.peer_review_completed_count,
    )
    precedent_relevance_gap = _six(_ONE_SCORE - record.precedent_relevance_score)
    calibration_contribution_gap = _six(
        _ONE_SCORE - record.calibration_contribution_score,
    )
    source_freshness_component = _capped_ratio(
        source_age_seconds,
        config.source_block_age_seconds,
    )
    stale_memory_component = _capped_ratio(
        memory_age_seconds,
        config.memory_block_age_seconds,
    )
    reason_codes = _row_reason_codes(
        record,
        config=config,
        source_age_seconds=source_age_seconds,
        memory_age_seconds=memory_age_seconds,
        contradiction_handling_gap_ratio=contradiction_handling_gap_ratio,
        peer_review_coverage_gap_ratio=peer_review_coverage_gap_ratio,
    )
    return ResearchTeamSpecialistEvidenceReuseQualityRow(
        team_ref=record.team_ref,
        specialist_ref=record.specialist_ref,
        evidence_reuse_digest=record.evidence_reuse_digest,
        precedent_bundle_digest=record.precedent_bundle_digest,
        source_bundle_digest=record.source_bundle_digest,
        memory_snapshot_digest=record.memory_snapshot_digest,
        calibration_digest=record.calibration_digest,
        peer_review_digest=record.peer_review_digest,
        observed_at=record.observed_at,
        source_last_observed_at=record.source_last_observed_at,
        memory_refreshed_at=record.memory_refreshed_at,
        source_age_seconds=source_age_seconds,
        memory_age_seconds=memory_age_seconds,
        precedent_relevance_score=record.precedent_relevance_score,
        precedent_relevance_gap=precedent_relevance_gap,
        source_freshness_component=source_freshness_component,
        stale_memory_component=stale_memory_component,
        calibration_contribution_score=record.calibration_contribution_score,
        calibration_contribution_gap=calibration_contribution_gap,
        contradiction_total_count=record.contradiction_total_count,
        contradiction_resolved_count=record.contradiction_resolved_count,
        contradiction_handling_gap_ratio=contradiction_handling_gap_ratio,
        peer_review_required_count=record.peer_review_required_count,
        peer_review_completed_count=record.peer_review_completed_count,
        peer_review_coverage_gap_ratio=peer_review_coverage_gap_ratio,
        evidence_reuse_risk_score=_risk_score(
            precedent_relevance_gap=precedent_relevance_gap,
            source_freshness_component=source_freshness_component,
            stale_memory_component=stale_memory_component,
            calibration_contribution_gap=calibration_contribution_gap,
            contradiction_handling_gap_ratio=contradiction_handling_gap_ratio,
            peer_review_coverage_gap_ratio=peer_review_coverage_gap_ratio,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    record: ResearchTeamSpecialistEvidenceReuseQualityRecord,
    *,
    config: ResearchTeamSpecialistEvidenceReuseQualityReportConfig,
    source_age_seconds: Decimal,
    memory_age_seconds: Decimal,
    contradiction_handling_gap_ratio: Decimal,
    peer_review_coverage_gap_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if record.precedent_relevance_score < config.min_watch_precedent_relevance_score:
        reason_codes.append(_PRECEDENT_BLOCK_REASON)
    elif record.precedent_relevance_score < config.min_pass_precedent_relevance_score:
        reason_codes.append(_PRECEDENT_WATCH_REASON)
    if source_age_seconds >= config.source_block_age_seconds:
        reason_codes.append(_SOURCE_BLOCK_REASON)
    elif source_age_seconds >= config.source_watch_age_seconds:
        reason_codes.append(_SOURCE_WATCH_REASON)
    if memory_age_seconds >= config.memory_block_age_seconds:
        reason_codes.append(_MEMORY_BLOCK_REASON)
    elif memory_age_seconds >= config.memory_watch_age_seconds:
        reason_codes.append(_MEMORY_WATCH_REASON)
    if record.calibration_contribution_score < config.min_watch_calibration_contribution_score:
        reason_codes.append(_CALIBRATION_BLOCK_REASON)
    elif record.calibration_contribution_score < config.min_pass_calibration_contribution_score:
        reason_codes.append(_CALIBRATION_WATCH_REASON)
    if contradiction_handling_gap_ratio >= config.contradiction_block_gap_ratio:
        reason_codes.append(_CONTRADICTION_BLOCK_REASON)
    elif contradiction_handling_gap_ratio >= config.contradiction_watch_gap_ratio:
        reason_codes.append(_CONTRADICTION_WATCH_REASON)
    if peer_review_coverage_gap_ratio >= config.peer_review_block_gap_ratio:
        reason_codes.append(_PEER_REVIEW_BLOCK_REASON)
    elif peer_review_coverage_gap_ratio >= config.peer_review_watch_gap_ratio:
        reason_codes.append(_PEER_REVIEW_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...],
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
    rows: tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _risk_score(
    *,
    precedent_relevance_gap: Decimal,
    source_freshness_component: Decimal,
    stale_memory_component: Decimal,
    calibration_contribution_gap: Decimal,
    contradiction_handling_gap_ratio: Decimal,
    peer_review_coverage_gap_ratio: Decimal,
    config: ResearchTeamSpecialistEvidenceReuseQualityReportConfig,
) -> Decimal:
    return _six(
        precedent_relevance_gap * config.precedent_relevance_weight
        + source_freshness_component * config.source_freshness_weight
        + stale_memory_component * config.stale_memory_weight
        + calibration_contribution_gap * config.calibration_contribution_weight
        + contradiction_handling_gap_ratio * config.contradiction_handling_weight
        + peer_review_coverage_gap_ratio * config.peer_review_coverage_weight,
    )


def _gap_ratio(total_count: Decimal, completed_count: Decimal) -> Decimal:
    if total_count <= _ZERO_COUNT:
        return _ZERO_SCORE
    return _six((total_count - completed_count) / total_count)


def _max_risk_score(
    rows: tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.evidence_reuse_risk_score for row in rows)


def _average_risk_score(
    rows: tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return _six(
        sum((row.evidence_reuse_risk_score for row in rows), _ZERO_SCORE)
        / Decimal(len(rows)),
    )


def _has_any(
    row: ResearchTeamSpecialistEvidenceReuseQualityRow,
    watch_reason: str,
    block_reason: str,
) -> bool:
    return watch_reason in row.reason_codes or block_reason in row.reason_codes


def _normalize_records(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistEvidenceReuseQualityRecord, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    seen: set[str] = set()
    for record in records:
        if type(record) is not ResearchTeamSpecialistEvidenceReuseQualityRecord:
            raise ValueError("records must contain exact evidence reuse quality records")
        _require_hard_flags("record", record)
        for field_name in (
            "observed_at",
            "source_last_observed_at",
            "memory_refreshed_at",
        ):
            if getattr(record, field_name) > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        if record.evidence_reuse_digest in seen:
            raise ValueError("records must not repeat evidence reuse digests")
        seen.add(record.evidence_reuse_digest)
    return tuple(sorted(records, key=lambda record: _record_sort_key(record)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamSpecialistEvidenceReuseQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistEvidenceReuseQualityRow:
            raise ValueError("rows must contain exact evidence reuse quality rows")
        _require_hard_flags("row", row)
        if row.evidence_reuse_digest in seen:
            raise ValueError("rows must not repeat evidence reuse digests")
        seen.add(row.evidence_reuse_digest)
        _validate_row_digest(row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by refs and digest")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat reason codes")
        seen.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=lambda row: _reason_index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return rows


def _validate_row_metrics(row: ResearchTeamSpecialistEvidenceReuseQualityRow) -> None:
    if row.contradiction_resolved_count > row.contradiction_total_count:
        raise ValueError("contradiction_resolved_count must not exceed total count")
    if row.peer_review_completed_count > row.peer_review_required_count:
        raise ValueError("peer_review_completed_count must not exceed required count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_metrics(report: ResearchTeamSpecialistEvidenceReuseQualityReport) -> None:
    if report.reuse_record_count != _count(len(report.rows)):
        raise ValueError("reuse_record_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.low_precedent_relevance_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _PRECEDENT_WATCH_REASON, _PRECEDENT_BLOCK_REASON)
        ),
    ):
        raise ValueError("low_precedent_relevance_count must match rows")
    if report.stale_source_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _SOURCE_WATCH_REASON, _SOURCE_BLOCK_REASON)
        ),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.stale_memory_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)
        ),
    ):
        raise ValueError("stale_memory_count must match rows")
    if report.low_calibration_contribution_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _CALIBRATION_WATCH_REASON, _CALIBRATION_BLOCK_REASON)
        ),
    ):
        raise ValueError("low_calibration_contribution_count must match rows")
    if report.contradiction_gap_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _CONTRADICTION_WATCH_REASON, _CONTRADICTION_BLOCK_REASON)
        ),
    ):
        raise ValueError("contradiction_gap_count must match rows")
    if report.peer_review_gap_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _PEER_REVIEW_WATCH_REASON, _PEER_REVIEW_BLOCK_REASON)
        ),
    ):
        raise ValueError("peer_review_gap_count must match rows")
    if report.max_evidence_reuse_risk_score != _max_risk_score(report.rows):
        raise ValueError("max_evidence_reuse_risk_score must match rows")
    if report.average_evidence_reuse_risk_score != _average_risk_score(report.rows):
        raise ValueError("average_evidence_reuse_risk_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _validate_report_digest(report: ResearchTeamSpecialistEvidenceReuseQualityReport) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    expected_digest = _digest_value(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_digest(row: ResearchTeamSpecialistEvidenceReuseQualityRow) -> None:
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
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not repeat values")
        seen.add(reason_code)
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
    with localcontext(_DECIMAL_CONTEXT):
        ratio = _six(numerator / denominator)
    if ratio < _ZERO_SCORE:
        return _ZERO_SCORE
    if ratio > _ONE_SCORE:
        return _ONE_SCORE
    return ratio


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    if earlier_utc > later_utc:
        raise ValueError("timestamp order must not produce negative age")
    return _six(Decimal(str((later_utc - earlier_utc).total_seconds())))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        offset = value.utcoffset()
    except NotImplementedError as exc:
        raise ValueError(f"{field_name} datetime must have a concrete UTC offset") from exc
    if offset is None:
        raise ValueError(f"{field_name} datetime must have a concrete UTC offset")
    return value.astimezone(UTC)


def _record_sort_key(
    record: ResearchTeamSpecialistEvidenceReuseQualityRecord,
) -> tuple[str, str, str]:
    return (record.team_ref, record.specialist_ref, record.evidence_reuse_digest)


def _row_sort_key(
    row: ResearchTeamSpecialistEvidenceReuseQualityRow,
) -> tuple[str, str, str]:
    return (row.team_ref, row.specialist_ref, row.evidence_reuse_digest)


def _reason_index(reason_code: str) -> int:
    return _REASON_SEQUENCE.index(reason_code)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES",
    "ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount",
    "ResearchTeamSpecialistEvidenceReuseQualityRecord",
    "ResearchTeamSpecialistEvidenceReuseQualityReport",
    "ResearchTeamSpecialistEvidenceReuseQualityReportConfig",
    "ResearchTeamSpecialistEvidenceReuseQualityRow",
    "build_research_team_specialist_evidence_reuse_quality_report",
    "research_team_specialist_evidence_reuse_quality_report_payload",
)
