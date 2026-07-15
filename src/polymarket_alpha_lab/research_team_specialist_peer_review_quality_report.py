from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP, localcontext
import hashlib
import json
from typing import Any, final


DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION = (
    "research-team-specialist-peer-review-quality-report-v0"
)
RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

_PASS_REASON = "peer_review_quality_pass"
_EMPTY_REASON = "peer_review_quality_empty"
_CORRECTION_BLOCK_REASON = "peer_review_correction_follow_through_block"
_CORRECTION_WATCH_REASON = "peer_review_correction_follow_through_watch"
_DISAGREEMENT_BLOCK_REASON = "peer_review_disagreement_handling_block"
_DISAGREEMENT_WATCH_REASON = "peer_review_disagreement_handling_watch"
_EVIDENCE_BLOCK_REASON = "peer_review_evidence_coverage_block"
_EVIDENCE_WATCH_REASON = "peer_review_evidence_coverage_watch"
_LATENCY_BLOCK_REASON = "peer_review_reviewer_latency_block"
_LATENCY_WATCH_REASON = "peer_review_reviewer_latency_watch"
_MEMORY_BLOCK_REASON = "peer_review_stale_memory_block"
_MEMORY_WATCH_REASON = "peer_review_stale_memory_watch"

_REASON_SEQUENCE = (
    _CORRECTION_BLOCK_REASON,
    _CORRECTION_WATCH_REASON,
    _DISAGREEMENT_BLOCK_REASON,
    _DISAGREEMENT_WATCH_REASON,
    _EVIDENCE_BLOCK_REASON,
    _EVIDENCE_WATCH_REASON,
    _LATENCY_BLOCK_REASON,
    _LATENCY_WATCH_REASON,
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


@final
@dataclass(frozen=True)
class ResearchTeamSpecialistPeerReviewQualityReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION
    )
    disagreement_watch_gap_ratio: Decimal = Decimal("0.250000")
    disagreement_block_gap_ratio: Decimal = Decimal("0.500000")
    evidence_watch_gap_ratio: Decimal = Decimal("0.250000")
    evidence_block_gap_ratio: Decimal = Decimal("0.500000")
    correction_watch_gap_ratio: Decimal = Decimal("0.250000")
    correction_block_gap_ratio: Decimal = Decimal("0.500000")
    stale_memory_watch_seconds: Decimal = Decimal("86400.000000")
    stale_memory_block_seconds: Decimal = Decimal("259200.000000")
    reviewer_latency_watch_seconds: Decimal = Decimal("3600.000000")
    reviewer_latency_block_seconds: Decimal = Decimal("7200.000000")
    disagreement_weight: Decimal = Decimal("0.250000")
    evidence_weight: Decimal = Decimal("0.200000")
    correction_weight: Decimal = Decimal("0.200000")
    stale_memory_weight: Decimal = Decimal("0.150000")
    reviewer_latency_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamSpecialistPeerReviewQualityReportConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "disagreement_watch_gap_ratio",
            "disagreement_block_gap_ratio",
            "evidence_watch_gap_ratio",
            "evidence_block_gap_ratio",
            "correction_watch_gap_ratio",
            "correction_block_gap_ratio",
            "disagreement_weight",
            "evidence_weight",
            "correction_weight",
            "stale_memory_weight",
            "reviewer_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_memory_watch_seconds",
            "stale_memory_block_seconds",
            "reviewer_latency_watch_seconds",
            "reviewer_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        if self.disagreement_block_gap_ratio <= self.disagreement_watch_gap_ratio:
            raise ValueError("disagreement_block_gap_ratio must exceed watch threshold")
        if self.evidence_block_gap_ratio <= self.evidence_watch_gap_ratio:
            raise ValueError("evidence_block_gap_ratio must exceed watch threshold")
        if self.correction_block_gap_ratio <= self.correction_watch_gap_ratio:
            raise ValueError("correction_block_gap_ratio must exceed watch threshold")
        if self.stale_memory_block_seconds <= self.stale_memory_watch_seconds:
            raise ValueError("stale_memory_block_seconds must exceed watch threshold")
        if self.reviewer_latency_block_seconds <= self.reviewer_latency_watch_seconds:
            raise ValueError("reviewer_latency_block_seconds must exceed watch threshold")
        with localcontext(_DECIMAL_CONTEXT):
            weight_sum = _six(
                self.disagreement_weight
                + self.evidence_weight
                + self.correction_weight
                + self.stale_memory_weight
                + self.reviewer_latency_weight,
            )
        if weight_sum != _ONE_SCORE:
            raise ValueError("peer review quality weights must sum to 1")
        for config_field in fields(self):
            if config_field.name in (
                "config_version",
                "paper_only",
                "report_only",
                "readonly",
            ):
                continue
            if getattr(self, config_field.name) != config_field.default:
                raise ValueError(f"{config_field.name} must use supported default")
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True)
class ResearchTeamSpecialistPeerReviewQualitySnapshot:
    team_ref: str
    reviewer_ref: str
    review_artifact_digest: str
    reviewed_output_digest: str
    evidence_bundle_digest: str
    review_due_at: datetime
    reviewed_at: datetime
    memory_refreshed_at: datetime
    disagreement_total_count: Decimal
    disagreement_resolved_count: Decimal
    required_evidence_count: Decimal
    covered_evidence_count: Decimal
    correction_required_count: Decimal
    correction_completed_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("snapshot", self, ResearchTeamSpecialistPeerReviewQualitySnapshot)
        for field_name in ("team_ref", "reviewer_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "review_artifact_digest",
            "reviewed_output_digest",
            "evidence_bundle_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in ("review_due_at", "reviewed_at", "memory_refreshed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        if self.reviewed_at < self.review_due_at:
            raise ValueError("reviewed_at must be on or after review_due_at")
        for field_name in (
            "disagreement_total_count",
            "disagreement_resolved_count",
            "required_evidence_count",
            "covered_evidence_count",
            "correction_required_count",
            "correction_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.disagreement_resolved_count > self.disagreement_total_count:
            raise ValueError("disagreement_resolved_count must not exceed total count")
        if self.covered_evidence_count > self.required_evidence_count:
            raise ValueError("covered_evidence_count must not exceed required count")
        if self.correction_completed_count > self.correction_required_count:
            raise ValueError("correction_completed_count must not exceed required count")
        _require_hard_flags("snapshot", self)


@final
@dataclass(frozen=True)
class ResearchTeamSpecialistPeerReviewQualityRow:
    team_ref: str
    reviewer_ref: str
    review_artifact_digest: str
    reviewed_output_digest: str
    evidence_bundle_digest: str
    review_due_at: datetime
    reviewed_at: datetime
    memory_refreshed_at: datetime
    reviewer_latency_seconds: Decimal
    memory_age_seconds: Decimal
    disagreement_total_count: Decimal
    disagreement_resolved_count: Decimal
    disagreement_gap_ratio: Decimal
    required_evidence_count: Decimal
    covered_evidence_count: Decimal
    evidence_coverage_gap_ratio: Decimal
    correction_required_count: Decimal
    correction_completed_count: Decimal
    correction_follow_through_gap_ratio: Decimal
    stale_memory_component: Decimal
    reviewer_latency_component: Decimal
    peer_review_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamSpecialistPeerReviewQualityRow)
        for field_name in ("team_ref", "reviewer_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "review_artifact_digest",
            "reviewed_output_digest",
            "evidence_bundle_digest",
        ):
            _require_digest(field_name, getattr(self, field_name))
        for field_name in ("review_due_at", "reviewed_at", "memory_refreshed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in ("reviewer_latency_seconds", "memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "disagreement_total_count",
            "disagreement_resolved_count",
            "required_evidence_count",
            "covered_evidence_count",
            "correction_required_count",
            "correction_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "disagreement_gap_ratio",
            "evidence_coverage_gap_ratio",
            "correction_follow_through_gap_ratio",
            "stale_memory_component",
            "reviewer_latency_component",
            "peer_review_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_metrics(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")


@final
@dataclass(frozen=True)
class ResearchTeamSpecialistPeerReviewQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamSpecialistPeerReviewQualityReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@final
@dataclass(frozen=True)
class ResearchTeamSpecialistPeerReviewQualityReport:
    generated_at: datetime
    config_version: str
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    unresolved_disagreement_count: Decimal
    evidence_gap_count: Decimal
    correction_gap_count: Decimal
    stale_memory_count: Decimal
    delayed_reviewer_count: Decimal
    max_peer_review_risk_score: Decimal
    average_peer_review_risk_score: Decimal
    status: str
    rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistPeerReviewQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamSpecialistPeerReviewQualityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "review_count",
            "pass_count",
            "watch_count",
            "block_count",
            "unresolved_disagreement_count",
            "evidence_gap_count",
            "correction_gap_count",
            "stale_memory_count",
            "delayed_reviewer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_peer_review_risk_score",
            "average_peer_review_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES)
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


def build_research_team_specialist_peer_review_quality_report(
    snapshots: list[ResearchTeamSpecialistPeerReviewQualitySnapshot]
    | tuple[ResearchTeamSpecialistPeerReviewQualitySnapshot, ...],
    *,
    config: ResearchTeamSpecialistPeerReviewQualityReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistPeerReviewQualityReport:
    config = _revalidated_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_snapshots(snapshots, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_snapshot(item, config=config, generated_at=generated_at_utc) for item in items),
            key=_row_sort_key,
        ),
    )
    return _report_from_rows(
        rows,
        config=config,
        generated_at=generated_at_utc,
    )


def _report_from_rows(
    rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...],
    *,
    config: ResearchTeamSpecialistPeerReviewQualityReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistPeerReviewQualityReport:
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    return ResearchTeamSpecialistPeerReviewQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        review_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        unresolved_disagreement_count=_count(
            sum(1 for row in rows if _has_any(row, _DISAGREEMENT_WATCH_REASON, _DISAGREEMENT_BLOCK_REASON)),
        ),
        evidence_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)),
        ),
        correction_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)),
        ),
        stale_memory_count=_count(
            sum(1 for row in rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)),
        ),
        delayed_reviewer_count=_count(
            sum(1 for row in rows if _has_any(row, _LATENCY_WATCH_REASON, _LATENCY_BLOCK_REASON)),
        ),
        max_peer_review_risk_score=_max_risk_score(rows),
        average_peer_review_risk_score=_average_risk_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_specialist_peer_review_quality_report_payload(
    report: ResearchTeamSpecialistPeerReviewQualityReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistPeerReviewQualityReport:
        _require_hard_flags("report", report)
        _validate_report_metrics(report)
        _validate_report_digest(report)
        payload = _payload_value(report)
    elif isinstance(report, Mapping):
        payload = _plain_payload_mapping(report)
        _require_canonical_public_payload(payload)
        _reject_unsafe_public_payload("peer review quality payload", payload)
        _require_public_payload_schema(payload)
        _require_payload_hard_flags(payload)
        _validate_payload_digest(payload)
        payload = _payload_value(_report_from_public_payload(payload))
    else:
        raise ValueError(
            "report must be a peer review quality report or payload mapping",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _require_public_payload_schema(payload)
    _reject_unsafe_public_payload("peer review quality payload", payload)
    _validate_payload_digest(payload)
    return payload


def _plain_payload_mapping(value: Mapping[str, object]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload schema keys must be strings")
        payload[key] = _plain_payload_value(item)
    return payload


def _plain_payload_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _plain_payload_mapping(value)
    if type(value) is list:
        return [_plain_payload_value(item) for item in value]
    return value


def _require_canonical_public_payload(payload: Mapping[str, object]) -> None:
    _reject_non_string_numeric(payload)


def _require_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_mapping_schema(
        "report payload",
        payload,
        ResearchTeamSpecialistPeerReviewQualityReport,
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("report payload rows must be a list")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("report payload rows must contain mappings")
        _require_mapping_schema(
            "row payload",
            row,
            ResearchTeamSpecialistPeerReviewQualityRow,
        )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("report payload reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        if not isinstance(reason_code_count, Mapping):
            raise ValueError(
                "report payload reason_code_counts must contain mappings",
            )
        _require_mapping_schema(
            "reason code count payload",
            reason_code_count,
            ResearchTeamSpecialistPeerReviewQualityReasonCodeCount,
        )


def _require_mapping_schema(
    label: str,
    value: Mapping[str, object],
    expected_type: type[object],
) -> None:
    actual_fields = tuple(value)
    if any(type(field_name) is not str for field_name in actual_fields):
        raise ValueError(f"{label} schema keys must be strings")
    expected_fields = tuple(field.name for field in fields(expected_type))
    if frozenset(actual_fields) != frozenset(expected_fields):
        raise ValueError(f"{label} must use exact schema")
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must use canonical field sequence")


def _report_from_public_payload(
    payload: Mapping[str, object],
) -> ResearchTeamSpecialistPeerReviewQualityReport:
    generated_at = _public_datetime("generated_at", payload["generated_at"])
    config_version = _public_string("config_version", payload["config_version"])
    config = _config_for_version(config_version)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a public list")
    rows = tuple(
        _row_from_public_payload(
            _plain_payload_mapping(row),
            config=config,
            generated_at=generated_at,
        )
        for row in rows_value
        if isinstance(row, Mapping)
    )
    if len(rows) != len(rows_value):
        raise ValueError("rows must contain public mappings")
    expected = _report_from_rows(
        rows,
        config=config,
        generated_at=generated_at,
    )
    supplied_values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config_version,
        "review_count": _public_decimal(
            "review_count",
            payload["review_count"],
            _normalize_nonnegative_count,
        ),
        "pass_count": _public_decimal(
            "pass_count",
            payload["pass_count"],
            _normalize_nonnegative_count,
        ),
        "watch_count": _public_decimal(
            "watch_count",
            payload["watch_count"],
            _normalize_nonnegative_count,
        ),
        "block_count": _public_decimal(
            "block_count",
            payload["block_count"],
            _normalize_nonnegative_count,
        ),
        "unresolved_disagreement_count": _public_decimal(
            "unresolved_disagreement_count",
            payload["unresolved_disagreement_count"],
            _normalize_nonnegative_count,
        ),
        "evidence_gap_count": _public_decimal(
            "evidence_gap_count",
            payload["evidence_gap_count"],
            _normalize_nonnegative_count,
        ),
        "correction_gap_count": _public_decimal(
            "correction_gap_count",
            payload["correction_gap_count"],
            _normalize_nonnegative_count,
        ),
        "stale_memory_count": _public_decimal(
            "stale_memory_count",
            payload["stale_memory_count"],
            _normalize_nonnegative_count,
        ),
        "delayed_reviewer_count": _public_decimal(
            "delayed_reviewer_count",
            payload["delayed_reviewer_count"],
            _normalize_nonnegative_count,
        ),
        "max_peer_review_risk_score": _public_decimal(
            "max_peer_review_risk_score",
            payload["max_peer_review_risk_score"],
            _normalize_unit_decimal,
        ),
        "average_peer_review_risk_score": _public_decimal(
            "average_peer_review_risk_score",
            payload["average_peer_review_risk_score"],
            _normalize_unit_decimal,
        ),
        "status": _public_member(
            "status",
            payload["status"],
            RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts_from_public_payload(
            payload["reason_code_counts"],
        ),
        "reason_codes": _reason_codes_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        "derived_validation_digest": _public_validation_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        "paper_only": _public_true("paper_only", payload["paper_only"]),
        "report_only": _public_true("report_only", payload["report_only"]),
        "readonly": _public_true("readonly", payload["readonly"]),
    }
    _require_values_match_dataclass(
        "report",
        supplied_values,
        expected,
    )
    return expected


def _row_from_public_payload(
    payload: Mapping[str, object],
    *,
    config: ResearchTeamSpecialistPeerReviewQualityReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistPeerReviewQualityRow:
    source_values: dict[str, object] = {
        "team_ref": _public_string("team_ref", payload["team_ref"]),
        "reviewer_ref": _public_string("reviewer_ref", payload["reviewer_ref"]),
        "review_artifact_digest": _public_input_digest(
            "review_artifact_digest",
            payload["review_artifact_digest"],
        ),
        "reviewed_output_digest": _public_input_digest(
            "reviewed_output_digest",
            payload["reviewed_output_digest"],
        ),
        "evidence_bundle_digest": _public_input_digest(
            "evidence_bundle_digest",
            payload["evidence_bundle_digest"],
        ),
        "review_due_at": _public_datetime(
            "review_due_at",
            payload["review_due_at"],
        ),
        "reviewed_at": _public_datetime("reviewed_at", payload["reviewed_at"]),
        "memory_refreshed_at": _public_datetime(
            "memory_refreshed_at",
            payload["memory_refreshed_at"],
        ),
        "disagreement_total_count": _public_decimal(
            "disagreement_total_count",
            payload["disagreement_total_count"],
            _normalize_nonnegative_count,
        ),
        "disagreement_resolved_count": _public_decimal(
            "disagreement_resolved_count",
            payload["disagreement_resolved_count"],
            _normalize_nonnegative_count,
        ),
        "required_evidence_count": _public_decimal(
            "required_evidence_count",
            payload["required_evidence_count"],
            _normalize_nonnegative_count,
        ),
        "covered_evidence_count": _public_decimal(
            "covered_evidence_count",
            payload["covered_evidence_count"],
            _normalize_nonnegative_count,
        ),
        "correction_required_count": _public_decimal(
            "correction_required_count",
            payload["correction_required_count"],
            _normalize_nonnegative_count,
        ),
        "correction_completed_count": _public_decimal(
            "correction_completed_count",
            payload["correction_completed_count"],
            _normalize_nonnegative_count,
        ),
        "paper_only": _public_true("paper_only", payload["paper_only"]),
        "report_only": _public_true("report_only", payload["report_only"]),
        "readonly": _public_true("readonly", payload["readonly"]),
    }
    for field_name in ("review_due_at", "reviewed_at", "memory_refreshed_at"):
        if source_values[field_name] > generated_at:
            raise ValueError(f"{field_name} must not be in the future")
    snapshot = ResearchTeamSpecialistPeerReviewQualitySnapshot(**source_values)
    expected = _row_from_snapshot(
        snapshot,
        config=config,
        generated_at=generated_at,
    )
    supplied_values = {
        **source_values,
        "reviewer_latency_seconds": _public_decimal(
            "reviewer_latency_seconds",
            payload["reviewer_latency_seconds"],
            _normalize_nonnegative_six_place_decimal,
        ),
        "memory_age_seconds": _public_decimal(
            "memory_age_seconds",
            payload["memory_age_seconds"],
            _normalize_nonnegative_six_place_decimal,
        ),
        "disagreement_gap_ratio": _public_decimal(
            "disagreement_gap_ratio",
            payload["disagreement_gap_ratio"],
            _normalize_unit_decimal,
        ),
        "evidence_coverage_gap_ratio": _public_decimal(
            "evidence_coverage_gap_ratio",
            payload["evidence_coverage_gap_ratio"],
            _normalize_unit_decimal,
        ),
        "correction_follow_through_gap_ratio": _public_decimal(
            "correction_follow_through_gap_ratio",
            payload["correction_follow_through_gap_ratio"],
            _normalize_unit_decimal,
        ),
        "stale_memory_component": _public_decimal(
            "stale_memory_component",
            payload["stale_memory_component"],
            _normalize_unit_decimal,
        ),
        "reviewer_latency_component": _public_decimal(
            "reviewer_latency_component",
            payload["reviewer_latency_component"],
            _normalize_unit_decimal,
        ),
        "peer_review_risk_score": _public_decimal(
            "peer_review_risk_score",
            payload["peer_review_risk_score"],
            _normalize_unit_decimal,
        ),
        "status": _public_member(
            "status",
            payload["status"],
            RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES,
        ),
        "reason_codes": _reason_codes_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        "derived_validation_digest": _public_validation_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
    }
    _require_values_match_dataclass("row", supplied_values, expected)
    return expected


def _reason_code_counts_from_public_payload(
    value: object,
) -> tuple[ResearchTeamSpecialistPeerReviewQualityReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a public list")
    counts: list[ResearchTeamSpecialistPeerReviewQualityReasonCodeCount] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("reason_code_counts must contain public mappings")
        payload = _plain_payload_mapping(item)
        _require_mapping_schema(
            "reason code count payload",
            payload,
            ResearchTeamSpecialistPeerReviewQualityReasonCodeCount,
        )
        counts.append(
            ResearchTeamSpecialistPeerReviewQualityReasonCodeCount(
                reason_code=_public_reason_code(
                    "reason_code",
                    payload["reason_code"],
                ),
                count=_public_decimal(
                    "count",
                    payload["count"],
                    _normalize_positive_count,
                ),
                paper_only=_public_true("paper_only", payload["paper_only"]),
                report_only=_public_true("report_only", payload["report_only"]),
                readonly=_public_true("readonly", payload["readonly"]),
            ),
        )
    normalized = tuple(counts)
    if normalized != tuple(sorted(normalized, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must use canonical sequence")
    return normalized


def _reason_codes_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    normalized = _normalize_reason_codes(tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use canonical sequence")
    return normalized


def _require_values_match_dataclass(
    label: str,
    supplied_values: Mapping[str, object],
    expected: object,
) -> None:
    for expected_field in fields(expected):
        field_name = expected_field.name
        if supplied_values[field_name] != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match derived {label}")


def _config_for_version(
    config_version: str,
) -> ResearchTeamSpecialistPeerReviewQualityReportConfig:
    if (
        config_version
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    return ResearchTeamSpecialistPeerReviewQualityReportConfig()


def _public_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        raw_value = Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, raw_value)
    if value != format(normalized, "f"):
        raise ValueError(f"{field_name} must use canonical Decimal string")
    return normalized


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must use canonical UTC format")
    return normalized


def _public_string(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    return value


def _public_input_digest(field_name: str, value: object) -> str:
    _require_digest(field_name, value)
    return value


def _public_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _public_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    _require_member(field_name, value, allowed)
    return value


def _public_reason_code(field_name: str, value: object) -> str:
    _require_reason_code(field_name, value)
    return value


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _row_from_snapshot(
    snapshot: ResearchTeamSpecialistPeerReviewQualitySnapshot,
    *,
    config: ResearchTeamSpecialistPeerReviewQualityReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistPeerReviewQualityRow:
    reviewer_latency_seconds = _seconds_between(snapshot.reviewed_at, snapshot.review_due_at)
    memory_age_seconds = _seconds_between(generated_at, snapshot.memory_refreshed_at)
    disagreement_gap_ratio = _gap_ratio(
        snapshot.disagreement_total_count,
        snapshot.disagreement_resolved_count,
    )
    evidence_coverage_gap_ratio = _gap_ratio(
        snapshot.required_evidence_count,
        snapshot.covered_evidence_count,
    )
    correction_follow_through_gap_ratio = _gap_ratio(
        snapshot.correction_required_count,
        snapshot.correction_completed_count,
    )
    stale_memory_component = _capped_ratio(
        memory_age_seconds,
        config.stale_memory_block_seconds,
    )
    reviewer_latency_component = _capped_ratio(
        reviewer_latency_seconds,
        config.reviewer_latency_block_seconds,
    )
    reason_codes = _row_reason_codes(
        config=config,
        disagreement_gap_ratio=disagreement_gap_ratio,
        evidence_coverage_gap_ratio=evidence_coverage_gap_ratio,
        correction_follow_through_gap_ratio=correction_follow_through_gap_ratio,
        reviewer_latency_seconds=reviewer_latency_seconds,
        memory_age_seconds=memory_age_seconds,
    )
    return ResearchTeamSpecialistPeerReviewQualityRow(
        team_ref=snapshot.team_ref,
        reviewer_ref=snapshot.reviewer_ref,
        review_artifact_digest=snapshot.review_artifact_digest,
        reviewed_output_digest=snapshot.reviewed_output_digest,
        evidence_bundle_digest=snapshot.evidence_bundle_digest,
        review_due_at=snapshot.review_due_at,
        reviewed_at=snapshot.reviewed_at,
        memory_refreshed_at=snapshot.memory_refreshed_at,
        reviewer_latency_seconds=reviewer_latency_seconds,
        memory_age_seconds=memory_age_seconds,
        disagreement_total_count=snapshot.disagreement_total_count,
        disagreement_resolved_count=snapshot.disagreement_resolved_count,
        disagreement_gap_ratio=disagreement_gap_ratio,
        required_evidence_count=snapshot.required_evidence_count,
        covered_evidence_count=snapshot.covered_evidence_count,
        evidence_coverage_gap_ratio=evidence_coverage_gap_ratio,
        correction_required_count=snapshot.correction_required_count,
        correction_completed_count=snapshot.correction_completed_count,
        correction_follow_through_gap_ratio=correction_follow_through_gap_ratio,
        stale_memory_component=stale_memory_component,
        reviewer_latency_component=reviewer_latency_component,
        peer_review_risk_score=_risk_score(
            disagreement_gap_ratio=disagreement_gap_ratio,
            evidence_coverage_gap_ratio=evidence_coverage_gap_ratio,
            correction_follow_through_gap_ratio=correction_follow_through_gap_ratio,
            stale_memory_component=stale_memory_component,
            reviewer_latency_component=reviewer_latency_component,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    config: ResearchTeamSpecialistPeerReviewQualityReportConfig,
    disagreement_gap_ratio: Decimal,
    evidence_coverage_gap_ratio: Decimal,
    correction_follow_through_gap_ratio: Decimal,
    reviewer_latency_seconds: Decimal,
    memory_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if correction_follow_through_gap_ratio >= config.correction_block_gap_ratio:
        reason_codes.append(_CORRECTION_BLOCK_REASON)
    elif correction_follow_through_gap_ratio >= config.correction_watch_gap_ratio:
        reason_codes.append(_CORRECTION_WATCH_REASON)
    if disagreement_gap_ratio >= config.disagreement_block_gap_ratio:
        reason_codes.append(_DISAGREEMENT_BLOCK_REASON)
    elif disagreement_gap_ratio >= config.disagreement_watch_gap_ratio:
        reason_codes.append(_DISAGREEMENT_WATCH_REASON)
    if evidence_coverage_gap_ratio >= config.evidence_block_gap_ratio:
        reason_codes.append(_EVIDENCE_BLOCK_REASON)
    elif evidence_coverage_gap_ratio >= config.evidence_watch_gap_ratio:
        reason_codes.append(_EVIDENCE_WATCH_REASON)
    if reviewer_latency_seconds >= config.reviewer_latency_block_seconds:
        reason_codes.append(_LATENCY_BLOCK_REASON)
    elif reviewer_latency_seconds >= config.reviewer_latency_watch_seconds:
        reason_codes.append(_LATENCY_WATCH_REASON)
    if memory_age_seconds >= config.stale_memory_block_seconds:
        reason_codes.append(_MEMORY_BLOCK_REASON)
    elif memory_age_seconds >= config.stale_memory_watch_seconds:
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


def _report_status(rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...],
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
    rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSpecialistPeerReviewQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistPeerReviewQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamSpecialistPeerReviewQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _risk_score(
    *,
    disagreement_gap_ratio: Decimal,
    evidence_coverage_gap_ratio: Decimal,
    correction_follow_through_gap_ratio: Decimal,
    stale_memory_component: Decimal,
    reviewer_latency_component: Decimal,
    config: ResearchTeamSpecialistPeerReviewQualityReportConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _six(
            disagreement_gap_ratio * config.disagreement_weight
            + evidence_coverage_gap_ratio * config.evidence_weight
            + correction_follow_through_gap_ratio * config.correction_weight
            + stale_memory_component * config.stale_memory_weight
            + reviewer_latency_component * config.reviewer_latency_weight,
        )


def _gap_ratio(total_count: Decimal, completed_count: Decimal) -> Decimal:
    if total_count <= _ZERO_COUNT:
        return _ZERO_SCORE
    with localcontext(_DECIMAL_CONTEXT):
        return _six((total_count - completed_count) / total_count)


def _max_risk_score(rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.peer_review_risk_score for row in rows)


def _average_risk_score(rows: tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...]) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    with localcontext(_DECIMAL_CONTEXT):
        return _six(
            sum((row.peer_review_risk_score for row in rows), _ZERO_SCORE)
            / Decimal(len(rows)),
        )


def _has_any(
    row: ResearchTeamSpecialistPeerReviewQualityRow,
    watch_reason: str,
    block_reason: str,
) -> bool:
    return watch_reason in row.reason_codes or block_reason in row.reason_codes


def _normalize_snapshots(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistPeerReviewQualitySnapshot, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    seen: set[str] = set()
    revalidated: list[ResearchTeamSpecialistPeerReviewQualitySnapshot] = []
    for snapshot_value in snapshots:
        snapshot = _revalidated_snapshot(snapshot_value)
        for field_name in ("review_due_at", "reviewed_at", "memory_refreshed_at"):
            if getattr(snapshot, field_name) > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        if snapshot.review_artifact_digest in seen:
            raise ValueError("snapshots must not repeat review artifact digests")
        seen.add(snapshot.review_artifact_digest)
        revalidated.append(snapshot)
    return tuple(sorted(revalidated, key=_snapshot_sort_key))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamSpecialistPeerReviewQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    revalidated: list[ResearchTeamSpecialistPeerReviewQualityRow] = []
    for row_value in rows:
        row = _revalidated_row(row_value)
        if type(row) is not ResearchTeamSpecialistPeerReviewQualityRow:
            raise ValueError("rows must contain exact peer review quality rows")
        if row.review_artifact_digest in seen:
            raise ValueError("rows must not repeat review artifact digests")
        seen.add(row.review_artifact_digest)
        _validate_row_digest(row)
        revalidated.append(row)
    normalized_rows = tuple(revalidated)
    sorted_rows = tuple(sorted(normalized_rows, key=_row_sort_key))
    if normalized_rows != sorted_rows:
        raise ValueError("rows must use the canonical sequence")
    return normalized_rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSpecialistPeerReviewQualityReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    normalized_rows = tuple(_revalidated_reason_code_count(row) for row in rows)
    sorted_rows = tuple(sorted(normalized_rows, key=lambda row: row.reason_code))
    if normalized_rows != sorted_rows:
        raise ValueError("reason_code_counts must use the canonical sequence")
    return normalized_rows


def _validate_row_metrics(row: ResearchTeamSpecialistPeerReviewQualityRow) -> None:
    if row.disagreement_resolved_count > row.disagreement_total_count:
        raise ValueError("disagreement_resolved_count must not exceed total count")
    if row.covered_evidence_count > row.required_evidence_count:
        raise ValueError("covered_evidence_count must not exceed required count")
    if row.correction_completed_count > row.correction_required_count:
        raise ValueError("correction_completed_count must not exceed required count")
    if row.reviewed_at < row.review_due_at:
        raise ValueError("reviewed_at must be on or after review_due_at")
    config = ResearchTeamSpecialistPeerReviewQualityReportConfig()
    expected_values: tuple[tuple[str, object], ...] = (
        (
            "reviewer_latency_seconds",
            _seconds_between(row.reviewed_at, row.review_due_at),
        ),
        (
            "disagreement_gap_ratio",
            _gap_ratio(
                row.disagreement_total_count,
                row.disagreement_resolved_count,
            ),
        ),
        (
            "evidence_coverage_gap_ratio",
            _gap_ratio(row.required_evidence_count, row.covered_evidence_count),
        ),
        (
            "correction_follow_through_gap_ratio",
            _gap_ratio(
                row.correction_required_count,
                row.correction_completed_count,
            ),
        ),
        (
            "stale_memory_component",
            _capped_ratio(
                row.memory_age_seconds,
                config.stale_memory_block_seconds,
            ),
        ),
        (
            "reviewer_latency_component",
            _capped_ratio(
                row.reviewer_latency_seconds,
                config.reviewer_latency_block_seconds,
            ),
        ),
    )
    expected_by_name = dict(expected_values)
    expected_reason_codes = _row_reason_codes(
        config=config,
        disagreement_gap_ratio=expected_by_name["disagreement_gap_ratio"],
        evidence_coverage_gap_ratio=expected_by_name[
            "evidence_coverage_gap_ratio"
        ],
        correction_follow_through_gap_ratio=expected_by_name[
            "correction_follow_through_gap_ratio"
        ],
        reviewer_latency_seconds=expected_by_name["reviewer_latency_seconds"],
        memory_age_seconds=row.memory_age_seconds,
    )
    expected_values += (
        (
            "peer_review_risk_score",
            _risk_score(
                disagreement_gap_ratio=expected_by_name[
                    "disagreement_gap_ratio"
                ],
                evidence_coverage_gap_ratio=expected_by_name[
                    "evidence_coverage_gap_ratio"
                ],
                correction_follow_through_gap_ratio=expected_by_name[
                    "correction_follow_through_gap_ratio"
                ],
                stale_memory_component=expected_by_name[
                    "stale_memory_component"
                ],
                reviewer_latency_component=expected_by_name[
                    "reviewer_latency_component"
                ],
                config=config,
            ),
        ),
        ("status", _row_status(expected_reason_codes)),
        ("reason_codes", expected_reason_codes),
    )
    for field_name, expected_value in expected_values:
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match source fields")


def _validate_report_metrics(report: ResearchTeamSpecialistPeerReviewQualityReport) -> None:
    config = _config_for_version(report.config_version)
    for row in report.rows:
        for field_name in ("review_due_at", "reviewed_at", "memory_refreshed_at"):
            if getattr(row, field_name) > report.generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        expected_row = _row_from_snapshot(
            ResearchTeamSpecialistPeerReviewQualitySnapshot(
                team_ref=row.team_ref,
                reviewer_ref=row.reviewer_ref,
                review_artifact_digest=row.review_artifact_digest,
                reviewed_output_digest=row.reviewed_output_digest,
                evidence_bundle_digest=row.evidence_bundle_digest,
                review_due_at=row.review_due_at,
                reviewed_at=row.reviewed_at,
                memory_refreshed_at=row.memory_refreshed_at,
                disagreement_total_count=row.disagreement_total_count,
                disagreement_resolved_count=row.disagreement_resolved_count,
                required_evidence_count=row.required_evidence_count,
                covered_evidence_count=row.covered_evidence_count,
                correction_required_count=row.correction_required_count,
                correction_completed_count=row.correction_completed_count,
                paper_only=row.paper_only,
                report_only=row.report_only,
                readonly=row.readonly,
            ),
            config=config,
            generated_at=report.generated_at,
        )
        for row_field in fields(row):
            field_name = row_field.name
            if getattr(row, field_name) != getattr(expected_row, field_name):
                raise ValueError(f"{field_name} must match report source fields")
    if report.review_count != _count(len(report.rows)):
        raise ValueError("review_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.unresolved_disagreement_count != _count(
        sum(1 for row in report.rows if _has_any(row, _DISAGREEMENT_WATCH_REASON, _DISAGREEMENT_BLOCK_REASON)),
    ):
        raise ValueError("unresolved_disagreement_count must match rows")
    if report.evidence_gap_count != _count(
        sum(1 for row in report.rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)),
    ):
        raise ValueError("evidence_gap_count must match rows")
    if report.correction_gap_count != _count(
        sum(1 for row in report.rows if _has_any(row, _CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON)),
    ):
        raise ValueError("correction_gap_count must match rows")
    if report.stale_memory_count != _count(
        sum(1 for row in report.rows if _has_any(row, _MEMORY_WATCH_REASON, _MEMORY_BLOCK_REASON)),
    ):
        raise ValueError("stale_memory_count must match rows")
    if report.delayed_reviewer_count != _count(
        sum(1 for row in report.rows if _has_any(row, _LATENCY_WATCH_REASON, _LATENCY_BLOCK_REASON)),
    ):
        raise ValueError("delayed_reviewer_count must match rows")
    if report.max_peer_review_risk_score != _max_risk_score(report.rows):
        raise ValueError("max_peer_review_risk_score must match rows")
    if report.average_peer_review_risk_score != _average_risk_score(report.rows):
        raise ValueError("average_peer_review_risk_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _snapshot_sort_key(
    snapshot: ResearchTeamSpecialistPeerReviewQualitySnapshot,
) -> tuple[str, str, str]:
    return (snapshot.team_ref, snapshot.reviewer_ref, snapshot.review_artifact_digest)


def _row_sort_key(
    row: ResearchTeamSpecialistPeerReviewQualityRow,
) -> tuple[Any, ...]:
    return (
        row.team_ref,
        row.reviewer_ref,
        _STATUS_RANK[row.status],
        -row.peer_review_risk_score,
        -row.correction_follow_through_gap_ratio,
        -row.disagreement_gap_ratio,
        -row.evidence_coverage_gap_ratio,
        -row.reviewer_latency_component,
        -row.stale_memory_component,
        -row.reviewer_latency_seconds,
        -row.memory_age_seconds,
        row.review_due_at,
        row.reviewed_at,
        row.memory_refreshed_at,
        -row.correction_required_count,
        -row.correction_completed_count,
        -row.disagreement_total_count,
        -row.disagreement_resolved_count,
        -row.required_evidence_count,
        -row.covered_evidence_count,
        row.reason_codes,
        row.review_artifact_digest,
        row.reviewed_output_digest,
        row.evidence_bundle_digest,
    )


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(_DECIMAL_CONTEXT):
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
    return _quantize_decimal("count source", Decimal(value), _COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    return _quantize_decimal("Decimal value", value, _SIX_PLACE_QUANTUM)


def _require_exact_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(quantum)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must fit the fixed Decimal context") from exc


def _revalidated_config(
    value: object,
) -> ResearchTeamSpecialistPeerReviewQualityReportConfig:
    if type(value) is not ResearchTeamSpecialistPeerReviewQualityReportConfig:
        raise ValueError("config must be a peer review quality report config")
    return ResearchTeamSpecialistPeerReviewQualityReportConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidated_snapshot(
    value: object,
) -> ResearchTeamSpecialistPeerReviewQualitySnapshot:
    if type(value) is not ResearchTeamSpecialistPeerReviewQualitySnapshot:
        raise ValueError("snapshots must contain exact peer review quality snapshots")
    return ResearchTeamSpecialistPeerReviewQualitySnapshot(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidated_row(value: object) -> ResearchTeamSpecialistPeerReviewQualityRow:
    if type(value) is not ResearchTeamSpecialistPeerReviewQualityRow:
        raise ValueError("rows must contain exact peer review quality rows")
    return ResearchTeamSpecialistPeerReviewQualityRow(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidated_reason_code_count(
    value: object,
) -> ResearchTeamSpecialistPeerReviewQualityReasonCodeCount:
    if type(value) is not ResearchTeamSpecialistPeerReviewQualityReasonCodeCount:
        raise ValueError("reason_code_counts must contain exact reason code counts")
    return ResearchTeamSpecialistPeerReviewQualityReasonCodeCount(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_finite_decimal(field_name, value)
    if decimal_value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = _quantize_decimal(field_name, decimal_value, _COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_finite_decimal(field_name, value)
    if decimal_value < _ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(field_name, decimal_value, _SIX_PLACE_QUANTUM)


def _normalize_positive_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized <= _ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_finite_decimal(field_name, value)
    if decimal_value < _ZERO_SCORE or decimal_value > _ONE_SCORE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_decimal(field_name, decimal_value, _SIX_PLACE_QUANTUM)


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


def _validate_row_digest(row: ResearchTeamSpecialistPeerReviewQualityRow) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest tamper detected in row")


def _validate_report_digest(report: ResearchTeamSpecialistPeerReviewQualityReport) -> None:
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
    payload_without_digest = _strip_digest_fields(payload)
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    stripped = _strip_digest_fields(payload)
    encoded = json.dumps(stripped, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _strip_digest_fields(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != _DIGEST_FIELD
        }
    if type(value) is list:
        return [_strip_digest_fields(item) for item in value]
    return value


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
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES",
    "ResearchTeamSpecialistPeerReviewQualityReportConfig",
    "ResearchTeamSpecialistPeerReviewQualitySnapshot",
    "ResearchTeamSpecialistPeerReviewQualityReasonCodeCount",
    "ResearchTeamSpecialistPeerReviewQualityRow",
    "ResearchTeamSpecialistPeerReviewQualityReport",
    "build_research_team_specialist_peer_review_quality_report",
    "research_team_specialist_peer_review_quality_report_payload",
)
