"""Public-safe specialist playbook revision queue report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_STATUSES",
    "ResearchTeamSpecialistPlaybookRevisionQueueConfig",
    "ResearchTeamSpecialistPlaybookRevisionQueueInput",
    "ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount",
    "ResearchTeamSpecialistPlaybookRevisionQueueReport",
    "ResearchTeamSpecialistPlaybookRevisionQueueRow",
    "build_research_team_specialist_playbook_revision_queue_report",
    "research_team_specialist_playbook_revision_queue_report_payload",
)


DEFAULT_RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_REPORT_CONFIG_VERSION = (
    "research-team-specialist-playbook-revision-queue-report-v0"
)
RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_STATUSES = (
    "pass",
    "watch",
    "block",
)

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_FIELD = "derived_validation_digest"

_PASS_REASON = "playbook_revision_clear"
_EMPTY_REASON = "playbook_revision_queue_empty"
_QUEUE_PASS_REASON = "playbook_revision_queue_pass"
_QUEUE_WATCH_REASON = "playbook_revision_queue_watch"
_QUEUE_BLOCK_REASON = "playbook_revision_queue_block"
_FORECAST_BLOCK_REASON = "forecast_error_attribution_block"
_FORECAST_WATCH_REASON = "forecast_error_attribution_watch"
_STALE_MEMORY_BLOCK_REASON = "stale_memory_reuse_block"
_STALE_MEMORY_WATCH_REASON = "stale_memory_reuse_watch"
_CORRECTION_BLOCK_REASON = "correction_follow_through_block"
_CORRECTION_WATCH_REASON = "correction_follow_through_watch"
_EVIDENCE_BLOCK_REASON = "evidence_coverage_block"
_EVIDENCE_WATCH_REASON = "evidence_coverage_watch"
_PEER_REVIEW_BLOCK_REASON = "peer_review_depth_block"
_PEER_REVIEW_WATCH_REASON = "peer_review_depth_watch"
_LATENCY_BLOCK_REASON = "review_latency_block"
_LATENCY_WATCH_REASON = "review_latency_watch"

_PAPER_ACTION_BY_STATUS = {
    "pass": "paper_playbook_revision_monitor",
    "watch": "paper_playbook_revision_watch",
    "block": "paper_playbook_revision_block",
}
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REPORT_REASON_SEQUENCE = (
    _QUEUE_BLOCK_REASON,
    _QUEUE_WATCH_REASON,
    _QUEUE_PASS_REASON,
    _FORECAST_BLOCK_REASON,
    _STALE_MEMORY_BLOCK_REASON,
    _CORRECTION_BLOCK_REASON,
    _EVIDENCE_BLOCK_REASON,
    _PEER_REVIEW_BLOCK_REASON,
    _LATENCY_BLOCK_REASON,
    _FORECAST_WATCH_REASON,
    _STALE_MEMORY_WATCH_REASON,
    _CORRECTION_WATCH_REASON,
    _EVIDENCE_WATCH_REASON,
    _PEER_REVIEW_WATCH_REASON,
    _LATENCY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_ROW_REASON_SEQUENCE = (
    _FORECAST_BLOCK_REASON,
    _STALE_MEMORY_BLOCK_REASON,
    _CORRECTION_BLOCK_REASON,
    _EVIDENCE_BLOCK_REASON,
    _PEER_REVIEW_BLOCK_REASON,
    _LATENCY_BLOCK_REASON,
    _FORECAST_WATCH_REASON,
    _STALE_MEMORY_WATCH_REASON,
    _CORRECTION_WATCH_REASON,
    _EVIDENCE_WATCH_REASON,
    _PEER_REVIEW_WATCH_REASON,
    _LATENCY_WATCH_REASON,
    _PASS_REASON,
)
_KNOWN_REASON_CODES = frozenset((*_REPORT_REASON_SEQUENCE, *_ROW_REASON_SEQUENCE))

_UNSAFE_PUBLIC_HEXES = (
    "63616e646964617465",
    "6d61726b6574",
    "736c7567",
    "7175657374696f6e",
    "75726c",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
    "64736e",
    "706f7374677265733a2f2f",
    "7461626c65",
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
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ResearchTeamSpecialistPlaybookRevisionQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_REPORT_CONFIG_VERSION
    )
    forecast_error_watch_ratio: Decimal = Decimal("0.080000")
    forecast_error_block_ratio: Decimal = Decimal("0.200000")
    stale_memory_reuse_watch_ratio: Decimal = Decimal("0.150000")
    stale_memory_reuse_block_ratio: Decimal = Decimal("0.350000")
    correction_gap_watch_ratio: Decimal = Decimal("0.250000")
    correction_gap_block_ratio: Decimal = Decimal("0.500000")
    evidence_gap_watch_ratio: Decimal = Decimal("0.250000")
    evidence_gap_block_ratio: Decimal = Decimal("0.500000")
    peer_review_depth_gap_watch_ratio: Decimal = Decimal("0.250000")
    peer_review_depth_gap_block_ratio: Decimal = Decimal("0.500000")
    review_latency_watch_seconds: Decimal = Decimal("3600.000000")
    review_latency_block_seconds: Decimal = Decimal("7200.000000")
    forecast_error_weight: Decimal = Decimal("0.250000")
    stale_memory_reuse_weight: Decimal = Decimal("0.150000")
    correction_follow_through_weight: Decimal = Decimal("0.200000")
    evidence_coverage_weight: Decimal = Decimal("0.150000")
    peer_review_depth_weight: Decimal = Decimal("0.100000")
    review_latency_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamSpecialistPlaybookRevisionQueueConfig,
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "forecast_error_watch_ratio",
            "forecast_error_block_ratio",
            "stale_memory_reuse_watch_ratio",
            "stale_memory_reuse_block_ratio",
            "correction_gap_watch_ratio",
            "correction_gap_block_ratio",
            "evidence_gap_watch_ratio",
            "evidence_gap_block_ratio",
            "peer_review_depth_gap_watch_ratio",
            "peer_review_depth_gap_block_ratio",
            "forecast_error_weight",
            "stale_memory_reuse_weight",
            "correction_follow_through_weight",
            "evidence_coverage_weight",
            "peer_review_depth_weight",
            "review_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_latency_watch_seconds",
            "review_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "forecast_error",
            self.forecast_error_watch_ratio,
            self.forecast_error_block_ratio,
        )
        _require_threshold_order(
            "stale_memory_reuse",
            self.stale_memory_reuse_watch_ratio,
            self.stale_memory_reuse_block_ratio,
        )
        _require_threshold_order(
            "correction_gap",
            self.correction_gap_watch_ratio,
            self.correction_gap_block_ratio,
        )
        _require_threshold_order(
            "evidence_gap",
            self.evidence_gap_watch_ratio,
            self.evidence_gap_block_ratio,
        )
        _require_threshold_order(
            "peer_review_depth_gap",
            self.peer_review_depth_gap_watch_ratio,
            self.peer_review_depth_gap_block_ratio,
        )
        if self.review_latency_block_seconds <= self.review_latency_watch_seconds:
            raise ValueError("review_latency_block_seconds must exceed watch threshold")
        weight_sum = _six(
            self.forecast_error_weight
            + self.stale_memory_reuse_weight
            + self.correction_follow_through_weight
            + self.evidence_coverage_weight
            + self.peer_review_depth_weight
            + self.review_latency_weight,
        )
        if weight_sum != _ONE_RATIO:
            raise ValueError("playbook revision queue weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistPlaybookRevisionQueueInput:
    revision_ref: str
    specialist_ref: str
    playbook_ref: str
    observed_at: datetime
    forecast_error_attribution: Decimal
    stale_memory_reuse_ratio: Decimal
    correction_required_count: Decimal
    correction_completed_count: Decimal
    required_evidence_count: Decimal
    covered_evidence_count: Decimal
    required_peer_review_count: Decimal
    completed_peer_review_count: Decimal
    review_due_at: datetime
    reviewed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchTeamSpecialistPlaybookRevisionQueueInput,
        )
        for field_name in ("revision_ref", "specialist_ref", "playbook_ref"):
            _require_safe_public_ref(field_name, getattr(self, field_name))
        for field_name in ("observed_at", "review_due_at", "reviewed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("forecast_error_attribution", "stale_memory_reuse_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "correction_required_count",
            "correction_completed_count",
            "required_evidence_count",
            "covered_evidence_count",
            "required_peer_review_count",
            "completed_peer_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.reviewed_at < self.review_due_at:
            raise ValueError("reviewed_at must be on or after review_due_at")
        if self.correction_completed_count > self.correction_required_count:
            raise ValueError("correction_completed_count must not exceed required count")
        if self.covered_evidence_count > self.required_evidence_count:
            raise ValueError("covered_evidence_count must not exceed required count")
        if self.completed_peer_review_count > self.required_peer_review_count:
            raise ValueError("completed_peer_review_count must not exceed required count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistPlaybookRevisionQueueRow:
    revision_ref_digest: str
    specialist_ref_digest: str
    playbook_ref_digest: str
    observed_at: datetime
    forecast_error_attribution: Decimal
    stale_memory_reuse_ratio: Decimal
    correction_required_count: Decimal
    correction_completed_count: Decimal
    correction_gap_ratio: Decimal
    required_evidence_count: Decimal
    covered_evidence_count: Decimal
    evidence_gap_ratio: Decimal
    required_peer_review_count: Decimal
    completed_peer_review_count: Decimal
    peer_review_depth_gap_ratio: Decimal
    review_due_at: datetime
    reviewed_at: datetime
    review_latency_seconds: Decimal
    review_latency_component: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchTeamSpecialistPlaybookRevisionQueueRow,
        )
        for field_name in (
            "revision_ref_digest",
            "specialist_ref_digest",
            "playbook_ref_digest",
        ):
            _require_redacted_ref_digest(field_name, getattr(self, field_name))
        for field_name in ("observed_at", "review_due_at", "reviewed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_error_attribution",
            "stale_memory_reuse_ratio",
            "correction_gap_ratio",
            "evidence_gap_ratio",
            "peer_review_depth_gap_ratio",
            "review_latency_component",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "correction_required_count",
            "correction_completed_count",
            "required_evidence_count",
            "covered_evidence_count",
            "required_peer_review_count",
            "completed_peer_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_latency_seconds",
            _normalize_nonnegative_decimal(
                "review_latency_seconds",
                self.review_latency_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _validate_row_metrics(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")


@dataclass(frozen=True)
class ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount:
    reason_code: str
    count: Decimal
    revision_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "revision_ratio",
            _normalize_ratio_decimal("revision_ratio", self.revision_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistPlaybookRevisionQueueReport:
    generated_at: datetime
    config_version: str
    revision_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    forecast_error_flag_count: Decimal
    stale_memory_reuse_flag_count: Decimal
    correction_gap_count: Decimal
    evidence_gap_count: Decimal
    peer_review_depth_gap_count: Decimal
    review_latency_flag_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    max_review_latency_seconds: Decimal
    status: str
    paper_queue_action: str
    rows: tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchTeamSpecialistPlaybookRevisionQueueReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "revision_count",
            "pass_count",
            "watch_count",
            "block_count",
            "forecast_error_flag_count",
            "stale_memory_reuse_flag_count",
            "correction_gap_count",
            "evidence_gap_count",
            "peer_review_depth_gap_count",
            "review_latency_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_priority_score", "average_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_review_latency_seconds",
            _normalize_nonnegative_decimal(
                "max_review_latency_seconds",
                self.max_review_latency_seconds,
            ),
        )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != _PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("report", self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_metrics(self)
        _reject_unsafe_public_payload("report", _payload_value(self))


def build_research_team_specialist_playbook_revision_queue_report(
    revisions: Iterable[ResearchTeamSpecialistPlaybookRevisionQueueInput],
    *,
    config: ResearchTeamSpecialistPlaybookRevisionQueueConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistPlaybookRevisionQueueReport:
    if type(config) is not ResearchTeamSpecialistPlaybookRevisionQueueConfig:
        raise ValueError("config must be a playbook revision queue config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(revisions)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamSpecialistPlaybookRevisionQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        revision_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        forecast_error_flag_count=_flag_count(
            rows,
            _FORECAST_WATCH_REASON,
            _FORECAST_BLOCK_REASON,
        ),
        stale_memory_reuse_flag_count=_flag_count(
            rows,
            _STALE_MEMORY_WATCH_REASON,
            _STALE_MEMORY_BLOCK_REASON,
        ),
        correction_gap_count=_flag_count(
            rows,
            _CORRECTION_WATCH_REASON,
            _CORRECTION_BLOCK_REASON,
        ),
        evidence_gap_count=_flag_count(
            rows,
            _EVIDENCE_WATCH_REASON,
            _EVIDENCE_BLOCK_REASON,
        ),
        peer_review_depth_gap_count=_flag_count(
            rows,
            _PEER_REVIEW_WATCH_REASON,
            _PEER_REVIEW_BLOCK_REASON,
        ),
        review_latency_flag_count=_flag_count(
            rows,
            _LATENCY_WATCH_REASON,
            _LATENCY_BLOCK_REASON,
        ),
        max_priority_score=_max_ratio(tuple(row.priority_score for row in rows)),
        average_priority_score=_average_ratio(tuple(row.priority_score for row in rows)),
        max_review_latency_seconds=_max_decimal(
            tuple(row.review_latency_seconds for row in rows),
        ),
        status=status,
        paper_queue_action=_PAPER_ACTION_BY_STATUS[status],
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_team_specialist_playbook_revision_queue_report_payload(
    report: ResearchTeamSpecialistPlaybookRevisionQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_unsafe_public_payload("playbook revision queue payload", report)
        _reject_non_string_numeric(report)
        _validate_payload_digest(report)
        return report
    if type(report) is not ResearchTeamSpecialistPlaybookRevisionQueueReport:
        raise ValueError("report must be a playbook revision queue report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload("playbook revision queue payload", payload)
    _reject_non_string_numeric(payload)
    _validate_payload_digest(payload)
    return payload


def _row_from_input(
    item: ResearchTeamSpecialistPlaybookRevisionQueueInput,
    *,
    config: ResearchTeamSpecialistPlaybookRevisionQueueConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistPlaybookRevisionQueueRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    correction_gap_ratio = _gap_ratio(
        item.correction_required_count,
        item.correction_completed_count,
    )
    evidence_gap_ratio = _gap_ratio(
        item.required_evidence_count,
        item.covered_evidence_count,
    )
    peer_review_depth_gap_ratio = _gap_ratio(
        item.required_peer_review_count,
        item.completed_peer_review_count,
    )
    review_latency_seconds = _seconds_between(item.reviewed_at, item.review_due_at)
    review_latency_component = _capped_ratio(
        review_latency_seconds,
        config.review_latency_block_seconds,
    )
    reason_codes = _row_reason_codes(
        config=config,
        forecast_error_attribution=item.forecast_error_attribution,
        stale_memory_reuse_ratio=item.stale_memory_reuse_ratio,
        correction_gap_ratio=correction_gap_ratio,
        evidence_gap_ratio=evidence_gap_ratio,
        peer_review_depth_gap_ratio=peer_review_depth_gap_ratio,
        review_latency_seconds=review_latency_seconds,
    )
    return ResearchTeamSpecialistPlaybookRevisionQueueRow(
        revision_ref_digest=_redacted_ref_digest(item.revision_ref),
        specialist_ref_digest=_redacted_ref_digest(item.specialist_ref),
        playbook_ref_digest=_redacted_ref_digest(item.playbook_ref),
        observed_at=item.observed_at,
        forecast_error_attribution=item.forecast_error_attribution,
        stale_memory_reuse_ratio=item.stale_memory_reuse_ratio,
        correction_required_count=item.correction_required_count,
        correction_completed_count=item.correction_completed_count,
        correction_gap_ratio=correction_gap_ratio,
        required_evidence_count=item.required_evidence_count,
        covered_evidence_count=item.covered_evidence_count,
        evidence_gap_ratio=evidence_gap_ratio,
        required_peer_review_count=item.required_peer_review_count,
        completed_peer_review_count=item.completed_peer_review_count,
        peer_review_depth_gap_ratio=peer_review_depth_gap_ratio,
        review_due_at=item.review_due_at,
        reviewed_at=item.reviewed_at,
        review_latency_seconds=review_latency_seconds,
        review_latency_component=review_latency_component,
        priority_score=_priority_score(
            config=config,
            forecast_error_attribution=item.forecast_error_attribution,
            stale_memory_reuse_ratio=item.stale_memory_reuse_ratio,
            correction_gap_ratio=correction_gap_ratio,
            evidence_gap_ratio=evidence_gap_ratio,
            peer_review_depth_gap_ratio=peer_review_depth_gap_ratio,
            review_latency_component=review_latency_component,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    config: ResearchTeamSpecialistPlaybookRevisionQueueConfig,
    forecast_error_attribution: Decimal,
    stale_memory_reuse_ratio: Decimal,
    correction_gap_ratio: Decimal,
    evidence_gap_ratio: Decimal,
    peer_review_depth_gap_ratio: Decimal,
    review_latency_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        value=forecast_error_attribution,
        watch_threshold=config.forecast_error_watch_ratio,
        block_threshold=config.forecast_error_block_ratio,
        watch_reason=_FORECAST_WATCH_REASON,
        block_reason=_FORECAST_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=stale_memory_reuse_ratio,
        watch_threshold=config.stale_memory_reuse_watch_ratio,
        block_threshold=config.stale_memory_reuse_block_ratio,
        watch_reason=_STALE_MEMORY_WATCH_REASON,
        block_reason=_STALE_MEMORY_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=correction_gap_ratio,
        watch_threshold=config.correction_gap_watch_ratio,
        block_threshold=config.correction_gap_block_ratio,
        watch_reason=_CORRECTION_WATCH_REASON,
        block_reason=_CORRECTION_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=evidence_gap_ratio,
        watch_threshold=config.evidence_gap_watch_ratio,
        block_threshold=config.evidence_gap_block_ratio,
        watch_reason=_EVIDENCE_WATCH_REASON,
        block_reason=_EVIDENCE_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=peer_review_depth_gap_ratio,
        watch_threshold=config.peer_review_depth_gap_watch_ratio,
        block_threshold=config.peer_review_depth_gap_block_ratio,
        watch_reason=_PEER_REVIEW_WATCH_REASON,
        block_reason=_PEER_REVIEW_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=review_latency_seconds,
        watch_threshold=config.review_latency_watch_seconds,
        block_threshold=config.review_latency_block_seconds,
        watch_reason=_LATENCY_WATCH_REASON,
        block_reason=_LATENCY_BLOCK_REASON,
    )
    if not reasons:
        return (_PASS_REASON,)
    return tuple(sorted(reasons, key=_reason_key))


def _append_threshold_reason(
    reasons: list[str],
    *,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reasons.append(block_reason)
    elif value >= watch_threshold:
        reasons.append(watch_reason)


def _priority_score(
    *,
    config: ResearchTeamSpecialistPlaybookRevisionQueueConfig,
    forecast_error_attribution: Decimal,
    stale_memory_reuse_ratio: Decimal,
    correction_gap_ratio: Decimal,
    evidence_gap_ratio: Decimal,
    peer_review_depth_gap_ratio: Decimal,
    review_latency_component: Decimal,
) -> Decimal:
    return _six(
        forecast_error_attribution * config.forecast_error_weight
        + stale_memory_reuse_ratio * config.stale_memory_reuse_weight
        + correction_gap_ratio * config.correction_follow_through_weight
        + evidence_gap_ratio * config.evidence_coverage_weight
        + peer_review_depth_gap_ratio * config.peer_review_depth_weight
        + review_latency_component * config.review_latency_weight,
    )


def _normalize_inputs(
    revisions: Iterable[ResearchTeamSpecialistPlaybookRevisionQueueInput],
) -> tuple[ResearchTeamSpecialistPlaybookRevisionQueueInput, ...]:
    if isinstance(revisions, (str, bytes)):
        raise ValueError("revisions must be an iterable")
    try:
        items = tuple(revisions)
    except TypeError as exc:
        raise ValueError("revisions must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistPlaybookRevisionQueueInput:
            raise ValueError(
                "revisions must contain ResearchTeamSpecialistPlaybookRevisionQueueInput",
            )
        _require_hard_flags("input", item)
        if item.revision_ref in seen:
            raise ValueError("revision_ref values must be unique")
        seen.add(item.revision_ref)
    return items


def _report_status(
    rows: tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    status = _report_status(rows)
    queue_reason = {
        "pass": _QUEUE_PASS_REASON,
        "watch": _QUEUE_WATCH_REASON,
        "block": _QUEUE_BLOCK_REASON,
    }[status]
    row_reasons = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if status == "pass" or reason != _PASS_REASON
            },
            key=_reason_key,
        ),
    )
    if not row_reasons:
        return (queue_reason,)
    return (queue_reason, *row_reasons)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...],
) -> tuple[ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount(
                reason_code=_EMPTY_REASON,
                count=Decimal("1"),
                revision_ratio=_ZERO_RATIO,
            ),
        )
    counts: Counter[str] = Counter(
        reason for row in rows for reason in row.reason_codes
    )
    revision_count = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            revision_ratio=_ratio(_count(count), revision_count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: _reason_key(item[0]))
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _flag_count(
    rows: tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...],
    watch_reason: str,
    block_reason: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if watch_reason in row.reason_codes or block_reason in row.reason_codes
        ),
    )


def _validate_row_metrics(
    row: ResearchTeamSpecialistPlaybookRevisionQueueRow,
) -> None:
    if row.reviewed_at < row.review_due_at:
        raise ValueError("reviewed_at must be on or after review_due_at")
    if row.correction_completed_count > row.correction_required_count:
        raise ValueError("correction_completed_count must not exceed required count")
    if row.covered_evidence_count > row.required_evidence_count:
        raise ValueError("covered_evidence_count must not exceed required count")
    if row.completed_peer_review_count > row.required_peer_review_count:
        raise ValueError("completed_peer_review_count must not exceed required count")
    if row.correction_gap_ratio != _gap_ratio(
        row.correction_required_count,
        row.correction_completed_count,
    ):
        raise ValueError("correction_gap_ratio must match correction counts")
    if row.evidence_gap_ratio != _gap_ratio(
        row.required_evidence_count,
        row.covered_evidence_count,
    ):
        raise ValueError("evidence_gap_ratio must match evidence counts")
    if row.peer_review_depth_gap_ratio != _gap_ratio(
        row.required_peer_review_count,
        row.completed_peer_review_count,
    ):
        raise ValueError("peer_review_depth_gap_ratio must match peer review counts")
    if row.review_latency_seconds != _seconds_between(row.reviewed_at, row.review_due_at):
        raise ValueError("review_latency_seconds must match review timestamps")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_metrics(
    report: ResearchTeamSpecialistPlaybookRevisionQueueReport,
) -> None:
    rows = report.rows
    if report.revision_count != _count(len(rows)):
        raise ValueError("revision_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    expected_flags = {
        "forecast_error_flag_count": (_FORECAST_WATCH_REASON, _FORECAST_BLOCK_REASON),
        "stale_memory_reuse_flag_count": (
            _STALE_MEMORY_WATCH_REASON,
            _STALE_MEMORY_BLOCK_REASON,
        ),
        "correction_gap_count": (_CORRECTION_WATCH_REASON, _CORRECTION_BLOCK_REASON),
        "evidence_gap_count": (_EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON),
        "peer_review_depth_gap_count": (
            _PEER_REVIEW_WATCH_REASON,
            _PEER_REVIEW_BLOCK_REASON,
        ),
        "review_latency_flag_count": (_LATENCY_WATCH_REASON, _LATENCY_BLOCK_REASON),
    }
    for field_name, reasons in expected_flags.items():
        if getattr(report, field_name) != _flag_count(rows, *reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.max_priority_score != _max_ratio(tuple(row.priority_score for row in rows)):
        raise ValueError("max_priority_score must match rows")
    if report.average_priority_score != _average_ratio(
        tuple(row.priority_score for row in rows),
    ):
        raise ValueError("average_priority_score must match rows")
    if report.max_review_latency_seconds != _max_decimal(
        tuple(row.review_latency_seconds for row in rows),
    ):
        raise ValueError("max_review_latency_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamSpecialistPlaybookRevisionQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistPlaybookRevisionQueueRow:
            raise ValueError("rows must contain playbook revision queue rows")
        _require_hard_flags("row", row)
        _validate_report_digest(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic order")
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in normalized:
        if type(value) is not ResearchTeamSpecialistPlaybookRevisionQueueReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        _require_hard_flags("reason_code_count", value)
    if normalized != tuple(sorted(normalized, key=lambda item: _reason_key(item.reason_code))):
        raise ValueError("reason_code_counts must use deterministic order")
    return normalized


def _row_sort_key(
    row: ResearchTeamSpecialistPlaybookRevisionQueueRow,
) -> tuple[int, Decimal, str]:
    return (
        _STATUS_RANK[row.status],
        -row.priority_score,
        row.revision_ref_digest,
    )


def _reason_key(reason_code: str) -> tuple[int, str]:
    try:
        index = _REPORT_REASON_SEQUENCE.index(reason_code)
    except ValueError:
        index = len(_REPORT_REASON_SEQUENCE)
    return (index, reason_code)


def _gap_ratio(required_count: Decimal, completed_count: Decimal) -> Decimal:
    if required_count == _ZERO_COUNT:
        return _ZERO_RATIO
    return _ratio(required_count - completed_count, required_count)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    return _six(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    value = _six(numerator / denominator)
    if value > _ONE_RATIO:
        return _ONE_RATIO
    if value < _ZERO_RATIO:
        return _ZERO_RATIO
    return value


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return _normalize_ratio_decimal("max_ratio", max(values))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return _ratio(sum(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return _six(max(values))


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("later timestamp must be on or after earlier timestamp")
    return _six(Decimal(str((later - earlier).total_seconds())))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value.quantize(_COUNT_QUANTUM)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _six(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _require_threshold_order(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{name}_block_ratio must exceed watch threshold")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_TEAM_SPECIALIST_PLAYBOOK_REVISION_QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in _KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(value: object, *, require_nonempty: bool) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reasons:
        raise ValueError("reason_codes must not be empty")
    if len(reasons) != len(set(reasons)):
        raise ValueError("reason_codes must be unique")
    for reason in reasons:
        _require_reason_code("reason_code", reason)
    ordered = tuple(sorted(reasons, key=_reason_key))
    if reasons != ordered:
        raise ValueError("reason_codes must use deterministic order")
    return reasons


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe public surface")
    return value


def _require_safe_public_ref(field_name: str, value: object) -> str:
    public_value = _require_public_string(field_name, value)
    if len(public_value) > 96:
        raise ValueError(f"{field_name} must be a compact safe public reference")
    return public_value


def _redacted_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _require_redacted_ref_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")
    digest = value.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in _HEX_CHARS for char in digest):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _validate_report_digest(value: object) -> None:
    digest = getattr(value, _DIGEST_FIELD, None)
    _require_sha256_digest(_DIGEST_FIELD, digest)
    if digest != _digest_value(value):
        raise ValueError("derived_validation_digest must match report fields")


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest value must be a dict payload")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(_DIGEST_FIELD, None)
    return sha256(_canonical_payload(digest_payload).encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    supplied_digest = payload.get(_DIGEST_FIELD)
    _require_sha256_digest(_DIGEST_FIELD, supplied_digest)
    for row in payload.get("rows", ()):
        if type(row) is not dict:
            raise ValueError("rows must contain dict payloads")
        row_digest = row.get(_DIGEST_FIELD)
        _require_sha256_digest(_DIGEST_FIELD, row_digest)
        if row_digest != _payload_validation_digest(row):
            raise ValueError("derived_validation_digest must match row payload")
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _canonical_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not public JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _payload_value(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public payload field in {label}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list or type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"unsafe public payload value in {label}")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must use Decimal-derived string values")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) is list or type(value) is tuple:
        for item in value:
            _reject_non_string_numeric(item)


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
