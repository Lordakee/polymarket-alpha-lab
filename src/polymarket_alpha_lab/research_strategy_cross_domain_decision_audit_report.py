"""Report-only cross-domain decision audit scorecard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_CONFIG_VERSION = (
    "research-strategy-cross-domain-decision-audit-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_EMPTY_INPUT = "empty_input"
REASON_CROSS_DOMAIN_DECISION_READY = "cross_domain_decision_ready"
REASON_DOMAIN_CONFLICT_OBSERVED = "domain_conflict_observed"
REASON_EVIDENCE_TRACE_GAP_OBSERVED = "evidence_trace_gap_observed"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_MEMORY_CALIBRATION_REVIEW_REQUESTED = (
    "memory_calibration_review_requested"
)
REASON_DOMAIN_QUORUM_BLOCK = "domain_quorum_block"
REASON_DOMAIN_QUORUM_WATCH = "domain_quorum_watch"
REASON_EVIDENCE_ALIGNMENT_BLOCK = "evidence_alignment_block"
REASON_EVIDENCE_ALIGNMENT_WATCH = "evidence_alignment_watch"
REASON_DECISION_TRACE_BLOCK = "decision_trace_block"
REASON_DECISION_TRACE_WATCH = "decision_trace_watch"
REASON_RESOLUTION_READINESS_BLOCK = "resolution_readiness_block"
REASON_RESOLUTION_READINESS_WATCH = "resolution_readiness_watch"
REASON_STALE_EVIDENCE_BLOCK = "stale_evidence_block"
REASON_STALE_EVIDENCE_WATCH = "stale_evidence_watch"
REASON_CROSS_DOMAIN_CONFLICT_BLOCK = "cross_domain_conflict_block"
REASON_CROSS_DOMAIN_CONFLICT_WATCH = "cross_domain_conflict_watch"
REASON_MEMORY_CALIBRATION_BLOCK = "memory_calibration_block"
REASON_MEMORY_CALIBRATION_WATCH = "memory_calibration_watch"
REASON_UNRESOLVED_BLOCKER_BLOCK = "unresolved_blocker_block"
REASON_UNRESOLVED_BLOCKER_WATCH = "unresolved_blocker_watch"
REASON_DECISION_AUDIT_SCORE_BLOCK = "decision_audit_score_block"
REASON_DECISION_AUDIT_SCORE_WATCH = "decision_audit_score_watch"
REASON_CROSS_DOMAIN_DECISION_AUDIT_PASS = "cross_domain_decision_audit_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_CROSS_DOMAIN_DECISION_READY,
    REASON_DOMAIN_CONFLICT_OBSERVED,
    REASON_EVIDENCE_TRACE_GAP_OBSERVED,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_MEMORY_CALIBRATION_REVIEW_REQUESTED,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_DOMAIN_QUORUM_BLOCK,
    REASON_DOMAIN_QUORUM_WATCH,
    REASON_EVIDENCE_ALIGNMENT_BLOCK,
    REASON_EVIDENCE_ALIGNMENT_WATCH,
    REASON_DECISION_TRACE_BLOCK,
    REASON_DECISION_TRACE_WATCH,
    REASON_RESOLUTION_READINESS_BLOCK,
    REASON_RESOLUTION_READINESS_WATCH,
    REASON_STALE_EVIDENCE_BLOCK,
    REASON_STALE_EVIDENCE_WATCH,
    REASON_CROSS_DOMAIN_CONFLICT_BLOCK,
    REASON_CROSS_DOMAIN_CONFLICT_WATCH,
    REASON_MEMORY_CALIBRATION_BLOCK,
    REASON_MEMORY_CALIBRATION_WATCH,
    REASON_UNRESOLVED_BLOCKER_BLOCK,
    REASON_UNRESOLVED_BLOCKER_WATCH,
    REASON_DECISION_AUDIT_SCORE_BLOCK,
    REASON_DECISION_AUDIT_SCORE_WATCH,
    REASON_CROSS_DOMAIN_DECISION_AUDIT_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REPORT_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    if reason_code.endswith("_block")
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUS_VALUES = frozenset(RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_STATUSES)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_CONFIG_PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "pass_min_audit_score",
        "watch_min_audit_score",
        "min_pass_domain_quorum_ratio",
        "min_watch_domain_quorum_ratio",
        "max_pass_conflict_ratio",
        "max_watch_conflict_ratio",
        "max_pass_stale_evidence_ratio",
        "max_watch_stale_evidence_ratio",
        "max_pass_unresolved_blocker_count",
        "max_watch_unresolved_blocker_count",
        "domain_quorum_weight",
        "evidence_alignment_weight",
        "decision_trace_weight",
        "resolution_readiness_weight",
        "stale_evidence_control_weight",
        "conflict_control_weight",
        "memory_calibration_weight",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "config",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_decision_audit_score",
        "min_decision_audit_score",
        "min_domain_quorum_ratio",
        "max_cross_domain_conflict_ratio",
        "max_stale_evidence_ratio",
        "max_unresolved_blocker_count",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "audit_item_digest",
        "domain_quorum_ratio",
        "evidence_alignment_score",
        "decision_trace_score",
        "resolution_readiness_score",
        "stale_evidence_ratio",
        "stale_evidence_control_score",
        "cross_domain_conflict_ratio",
        "conflict_control_score",
        "memory_calibration_score",
        "unresolved_blocker_count",
        "decision_audit_score",
        "weakest_dimension_score",
        "observed_at",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "live",
    "raw",
    "private key",
    "http://",
    "https://",
    "://",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_STATUSES",
    "ResearchStrategyCrossDomainDecisionAuditConfig",
    "ResearchStrategyCrossDomainDecisionAuditInput",
    "ResearchStrategyCrossDomainDecisionAuditReasonCodeCount",
    "ResearchStrategyCrossDomainDecisionAuditReport",
    "ResearchStrategyCrossDomainDecisionAuditRow",
    "build_research_strategy_cross_domain_decision_audit_report",
    "research_strategy_cross_domain_decision_audit_report_digest",
    "research_strategy_cross_domain_decision_audit_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyCrossDomainDecisionAuditConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_CONFIG_VERSION
    )
    pass_min_audit_score: Decimal = Decimal("0.800000")
    watch_min_audit_score: Decimal = Decimal("0.600000")
    min_pass_domain_quorum_ratio: Decimal = Decimal("0.750000")
    min_watch_domain_quorum_ratio: Decimal = Decimal("0.500000")
    max_pass_conflict_ratio: Decimal = Decimal("0.200000")
    max_watch_conflict_ratio: Decimal = Decimal("0.400000")
    max_pass_stale_evidence_ratio: Decimal = Decimal("0.150000")
    max_watch_stale_evidence_ratio: Decimal = Decimal("0.350000")
    max_pass_unresolved_blocker_count: Decimal = Decimal("0.000000")
    max_watch_unresolved_blocker_count: Decimal = Decimal("1.000000")
    domain_quorum_weight: Decimal = Decimal("0.220000")
    evidence_alignment_weight: Decimal = Decimal("0.180000")
    decision_trace_weight: Decimal = Decimal("0.170000")
    resolution_readiness_weight: Decimal = Decimal("0.150000")
    stale_evidence_control_weight: Decimal = Decimal("0.130000")
    conflict_control_weight: Decimal = Decimal("0.100000")
    memory_calibration_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainDecisionAuditConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_audit_score",
            "watch_min_audit_score",
            "min_pass_domain_quorum_ratio",
            "min_watch_domain_quorum_ratio",
            "max_pass_conflict_ratio",
            "max_watch_conflict_ratio",
            "max_pass_stale_evidence_ratio",
            "max_watch_stale_evidence_ratio",
            "domain_quorum_weight",
            "evidence_alignment_weight",
            "decision_trace_weight",
            "resolution_readiness_weight",
            "stale_evidence_control_weight",
            "conflict_control_weight",
            "memory_calibration_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_unresolved_blocker_count",
            "max_watch_unresolved_blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_audit_score < self.watch_min_audit_score:
            raise ValueError("pass_min_audit_score must be at least watch_min_audit_score")
        if self.min_pass_domain_quorum_ratio < self.min_watch_domain_quorum_ratio:
            raise ValueError(
                "min_pass_domain_quorum_ratio must be at least "
                "min_watch_domain_quorum_ratio",
            )
        if self.max_pass_conflict_ratio > self.max_watch_conflict_ratio:
            raise ValueError(
                "max_pass_conflict_ratio must not exceed max_watch_conflict_ratio",
            )
        if self.max_pass_stale_evidence_ratio > self.max_watch_stale_evidence_ratio:
            raise ValueError(
                "max_pass_stale_evidence_ratio must not exceed "
                "max_watch_stale_evidence_ratio",
            )
        if (
            self.max_pass_unresolved_blocker_count
            > self.max_watch_unresolved_blocker_count
        ):
            raise ValueError(
                "max_pass_unresolved_blocker_count must not exceed "
                "max_watch_unresolved_blocker_count",
            )
        if _config_weight_sum(self) != _ONE:
            raise ValueError("cross-domain decision audit weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossDomainDecisionAuditInput(_FinalPublicDataclass):
    audit_item_ref: str
    domain_quorum_ratio: Decimal
    evidence_alignment_score: Decimal
    decision_trace_score: Decimal
    resolution_readiness_score: Decimal
    stale_evidence_ratio: Decimal
    cross_domain_conflict_ratio: Decimal
    memory_calibration_score: Decimal
    unresolved_blocker_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainDecisionAuditInput, "input")
        object.__setattr__(
            self,
            "audit_item_ref",
            _require_private_ref("audit_item_ref", self.audit_item_ref),
        )
        for field_name in (
            "domain_quorum_ratio",
            "evidence_alignment_score",
            "decision_trace_score",
            "resolution_readiness_score",
            "stale_evidence_ratio",
            "cross_domain_conflict_ratio",
            "memory_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_blocker_count",
            _require_nonnegative_count_decimal(
                "unresolved_blocker_count",
                self.unresolved_blocker_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCrossDomainDecisionAuditRow(_FinalPublicDataclass):
    audit_item_digest: str
    domain_quorum_ratio: Decimal
    evidence_alignment_score: Decimal
    decision_trace_score: Decimal
    resolution_readiness_score: Decimal
    stale_evidence_ratio: Decimal
    stale_evidence_control_score: Decimal
    cross_domain_conflict_ratio: Decimal
    conflict_control_score: Decimal
    memory_calibration_score: Decimal
    unresolved_blocker_count: Decimal
    decision_audit_score: Decimal
    weakest_dimension_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyCrossDomainDecisionAuditConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyCrossDomainDecisionAuditConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainDecisionAuditRow, "row")
        object.__setattr__(
            self,
            "audit_item_digest",
            _require_private_digest("audit_item_digest", self.audit_item_digest),
        )
        for field_name in (
            "domain_quorum_ratio",
            "evidence_alignment_score",
            "decision_trace_score",
            "resolution_readiness_score",
            "stale_evidence_ratio",
            "stale_evidence_control_score",
            "cross_domain_conflict_ratio",
            "conflict_control_score",
            "memory_calibration_score",
            "decision_audit_score",
            "weakest_dimension_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_blocker_count",
            _require_nonnegative_count_decimal(
                "unresolved_blocker_count",
                self.unresolved_blocker_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCrossDomainDecisionAuditReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossDomainDecisionAuditReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyCrossDomainDecisionAuditReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategyCrossDomainDecisionAuditConfig
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decision_audit_score: Decimal
    min_decision_audit_score: Decimal
    min_domain_quorum_ratio: Decimal
    max_cross_domain_conflict_ratio: Decimal
    max_stale_evidence_ratio: Decimal
    max_unresolved_blocker_count: Decimal
    rows: tuple[ResearchStrategyCrossDomainDecisionAuditRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCrossDomainDecisionAuditReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossDomainDecisionAuditReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if type(self.config) is not ResearchStrategyCrossDomainDecisionAuditConfig:
            raise ValueError(
                "config must be a ResearchStrategyCrossDomainDecisionAuditConfig",
            )
        _require_hard_flags("config", self.config)
        if self.config.config_version != self.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_decision_audit_score",
            "min_decision_audit_score",
            "min_domain_quorum_ratio",
            "max_cross_domain_conflict_ratio",
            "max_stale_evidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_blocker_count",
            _require_nonnegative_count_decimal(
                "max_unresolved_blocker_count",
                self.max_unresolved_blocker_count,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_cross_domain_decision_audit_report_payload(self)


def build_research_strategy_cross_domain_decision_audit_report(
    inputs: Sequence[ResearchStrategyCrossDomainDecisionAuditInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyCrossDomainDecisionAuditConfig | None = None,
) -> ResearchStrategyCrossDomainDecisionAuditReport:
    """Build a deterministic, readonly cross-domain decision audit report."""

    cfg = config or ResearchStrategyCrossDomainDecisionAuditConfig()
    if type(cfg) is not ResearchStrategyCrossDomainDecisionAuditConfig:
        raise ValueError("config must be a ResearchStrategyCrossDomainDecisionAuditConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyCrossDomainDecisionAuditReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "config": cfg,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_decision_audit_score": _average_ratio(
            tuple(row.decision_audit_score for row in rows),
        ),
        "min_decision_audit_score": min(
            (row.decision_audit_score for row in rows),
            default=_ZERO,
        ),
        "min_domain_quorum_ratio": min(
            (row.domain_quorum_ratio for row in rows),
            default=_ZERO,
        ),
        "max_cross_domain_conflict_ratio": max(
            (row.cross_domain_conflict_ratio for row in rows),
            default=_ZERO,
        ),
        "max_stale_evidence_ratio": max(
            (row.stale_evidence_ratio for row in rows),
            default=_ZERO,
        ),
        "max_unresolved_blocker_count": max(
            (row.unresolved_blocker_count for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCrossDomainDecisionAuditReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_cross_domain_decision_audit_report_payload(
    value: ResearchStrategyCrossDomainDecisionAuditReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyCrossDomainDecisionAuditReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyCrossDomainDecisionAuditReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    _validate_public_payload_schema(payload)
    return payload


def research_strategy_cross_domain_decision_audit_report_digest(
    report: ResearchStrategyCrossDomainDecisionAuditReport,
) -> str:
    if type(report) is not ResearchStrategyCrossDomainDecisionAuditReport:
        raise ValueError("report must be a ResearchStrategyCrossDomainDecisionAuditReport")
    return _report_digest(report)


def _row_for_input(
    row: ResearchStrategyCrossDomainDecisionAuditInput,
    config: ResearchStrategyCrossDomainDecisionAuditConfig,
) -> ResearchStrategyCrossDomainDecisionAuditRow:
    stale_evidence_control_score = _inverse_ratio(row.stale_evidence_ratio)
    conflict_control_score = _inverse_ratio(row.cross_domain_conflict_ratio)
    decision_audit_score = _decision_audit_score(
        domain_quorum_ratio=row.domain_quorum_ratio,
        evidence_alignment_score=row.evidence_alignment_score,
        decision_trace_score=row.decision_trace_score,
        resolution_readiness_score=row.resolution_readiness_score,
        stale_evidence_control_score=stale_evidence_control_score,
        conflict_control_score=conflict_control_score,
        memory_calibration_score=row.memory_calibration_score,
        config=config,
    )
    weakest_dimension_score = min(
        row.domain_quorum_ratio,
        row.evidence_alignment_score,
        row.decision_trace_score,
        row.resolution_readiness_score,
        stale_evidence_control_score,
        conflict_control_score,
        row.memory_calibration_score,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        domain_quorum_ratio=row.domain_quorum_ratio,
        evidence_alignment_score=row.evidence_alignment_score,
        decision_trace_score=row.decision_trace_score,
        resolution_readiness_score=row.resolution_readiness_score,
        stale_evidence_ratio=row.stale_evidence_ratio,
        cross_domain_conflict_ratio=row.cross_domain_conflict_ratio,
        memory_calibration_score=row.memory_calibration_score,
        unresolved_blocker_count=row.unresolved_blocker_count,
        decision_audit_score=decision_audit_score,
        config=config,
    )
    return ResearchStrategyCrossDomainDecisionAuditRow(
        audit_item_digest=_private_ref_digest(row.audit_item_ref),
        domain_quorum_ratio=row.domain_quorum_ratio,
        evidence_alignment_score=row.evidence_alignment_score,
        decision_trace_score=row.decision_trace_score,
        resolution_readiness_score=row.resolution_readiness_score,
        stale_evidence_ratio=row.stale_evidence_ratio,
        stale_evidence_control_score=stale_evidence_control_score,
        cross_domain_conflict_ratio=row.cross_domain_conflict_ratio,
        conflict_control_score=conflict_control_score,
        memory_calibration_score=row.memory_calibration_score,
        unresolved_blocker_count=row.unresolved_blocker_count,
        decision_audit_score=decision_audit_score,
        weakest_dimension_score=weakest_dimension_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    domain_quorum_ratio: Decimal,
    evidence_alignment_score: Decimal,
    decision_trace_score: Decimal,
    resolution_readiness_score: Decimal,
    stale_evidence_ratio: Decimal,
    cross_domain_conflict_ratio: Decimal,
    memory_calibration_score: Decimal,
    unresolved_blocker_count: Decimal,
    decision_audit_score: Decimal,
    config: ResearchStrategyCrossDomainDecisionAuditConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_DOMAIN_QUORUM_BLOCK,
        watch_code=REASON_DOMAIN_QUORUM_WATCH,
        value=domain_quorum_ratio,
        block_floor=config.min_watch_domain_quorum_ratio,
        pass_floor=config.min_pass_domain_quorum_ratio,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_EVIDENCE_ALIGNMENT_BLOCK,
        watch_code=REASON_EVIDENCE_ALIGNMENT_WATCH,
        value=evidence_alignment_score,
        block_floor=config.min_watch_domain_quorum_ratio,
        pass_floor=config.pass_min_audit_score,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_DECISION_TRACE_BLOCK,
        watch_code=REASON_DECISION_TRACE_WATCH,
        value=decision_trace_score,
        block_floor=config.min_watch_domain_quorum_ratio,
        pass_floor=config.pass_min_audit_score,
    )
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_RESOLUTION_READINESS_BLOCK,
        watch_code=REASON_RESOLUTION_READINESS_WATCH,
        value=resolution_readiness_score,
        block_floor=config.min_watch_domain_quorum_ratio,
        pass_floor=config.pass_min_audit_score,
    )
    if stale_evidence_ratio > config.max_watch_stale_evidence_ratio:
        reason_codes.append(REASON_STALE_EVIDENCE_BLOCK)
    elif stale_evidence_ratio > config.max_pass_stale_evidence_ratio:
        reason_codes.append(REASON_STALE_EVIDENCE_WATCH)
    if cross_domain_conflict_ratio > config.max_watch_conflict_ratio:
        reason_codes.append(REASON_CROSS_DOMAIN_CONFLICT_BLOCK)
    elif cross_domain_conflict_ratio > config.max_pass_conflict_ratio:
        reason_codes.append(REASON_CROSS_DOMAIN_CONFLICT_WATCH)
    _append_dimension_reason(
        reason_codes,
        block_code=REASON_MEMORY_CALIBRATION_BLOCK,
        watch_code=REASON_MEMORY_CALIBRATION_WATCH,
        value=memory_calibration_score,
        block_floor=config.min_watch_domain_quorum_ratio,
        pass_floor=config.pass_min_audit_score,
    )
    if unresolved_blocker_count > config.max_watch_unresolved_blocker_count:
        reason_codes.append(REASON_UNRESOLVED_BLOCKER_BLOCK)
    elif unresolved_blocker_count > config.max_pass_unresolved_blocker_count:
        reason_codes.append(REASON_UNRESOLVED_BLOCKER_WATCH)
    if decision_audit_score < config.watch_min_audit_score:
        reason_codes.append(REASON_DECISION_AUDIT_SCORE_BLOCK)
    elif decision_audit_score < config.pass_min_audit_score:
        reason_codes.append(REASON_DECISION_AUDIT_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_CROSS_DOMAIN_DECISION_AUDIT_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _append_dimension_reason(
    reason_codes: list[str],
    *,
    block_code: str,
    watch_code: str,
    value: Decimal,
    block_floor: Decimal,
    pass_floor: Decimal,
) -> None:
    if value < block_floor:
        reason_codes.append(block_code)
    elif value < pass_floor:
        reason_codes.append(watch_code)


def _decision_audit_score(
    *,
    domain_quorum_ratio: Decimal,
    evidence_alignment_score: Decimal,
    decision_trace_score: Decimal,
    resolution_readiness_score: Decimal,
    stale_evidence_control_score: Decimal,
    conflict_control_score: Decimal,
    memory_calibration_score: Decimal,
    config: ResearchStrategyCrossDomainDecisionAuditConfig,
) -> Decimal:
    score = (
        domain_quorum_ratio * config.domain_quorum_weight
        + evidence_alignment_score * config.evidence_alignment_weight
        + decision_trace_score * config.decision_trace_weight
        + resolution_readiness_score * config.resolution_readiness_weight
        + stale_evidence_control_score * config.stale_evidence_control_weight
        + conflict_control_score * config.conflict_control_weight
        + memory_calibration_score * config.memory_calibration_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyCrossDomainDecisionAuditRow,
    config: ResearchStrategyCrossDomainDecisionAuditConfig | None,
) -> None:
    expected_stale_control = _inverse_ratio(row.stale_evidence_ratio)
    expected_conflict_control = _inverse_ratio(row.cross_domain_conflict_ratio)
    expected_weakest = min(
        row.domain_quorum_ratio,
        row.evidence_alignment_score,
        row.decision_trace_score,
        row.resolution_readiness_score,
        row.stale_evidence_control_score,
        row.conflict_control_score,
        row.memory_calibration_score,
    )
    if row.stale_evidence_control_score != expected_stale_control:
        raise ValueError("stale_evidence_control_score must match stale_evidence_ratio")
    if row.conflict_control_score != expected_conflict_control:
        raise ValueError("conflict_control_score must match cross_domain_conflict_ratio")
    if row.weakest_dimension_score != expected_weakest:
        raise ValueError("weakest_dimension_score must match dimensions")
    if type(config) is not ResearchStrategyCrossDomainDecisionAuditConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchStrategyCrossDomainDecisionAuditConfig",
        )
    expected_score = _decision_audit_score(
        domain_quorum_ratio=row.domain_quorum_ratio,
        evidence_alignment_score=row.evidence_alignment_score,
        decision_trace_score=row.decision_trace_score,
        resolution_readiness_score=row.resolution_readiness_score,
        stale_evidence_control_score=row.stale_evidence_control_score,
        conflict_control_score=row.conflict_control_score,
        memory_calibration_score=row.memory_calibration_score,
        config=config,
    )
    if row.decision_audit_score != expected_score:
        raise ValueError("decision_audit_score must match component scores")
    upstream_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
    )
    expected_reasons = _row_reason_codes(
        upstream_reason_codes=upstream_reason_codes,
        domain_quorum_ratio=row.domain_quorum_ratio,
        evidence_alignment_score=row.evidence_alignment_score,
        decision_trace_score=row.decision_trace_score,
        resolution_readiness_score=row.resolution_readiness_score,
        stale_evidence_ratio=row.stale_evidence_ratio,
        cross_domain_conflict_ratio=row.cross_domain_conflict_ratio,
        memory_calibration_score=row.memory_calibration_score,
        unresolved_blocker_count=row.unresolved_blocker_count,
        decision_audit_score=row.decision_audit_score,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategyCrossDomainDecisionAuditReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if any(row.observed_at > report.generated_at for row in report.rows):
        raise ValueError("observed_at must not be after generated_at")
    for row in report.rows:
        _validate_row(row, report.config)
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_decision_audit_score != _average_ratio(
        tuple(row.decision_audit_score for row in report.rows),
    ):
        raise ValueError("average_decision_audit_score must match rows")
    if report.min_decision_audit_score != min(
        (row.decision_audit_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_decision_audit_score must match rows")
    if report.min_domain_quorum_ratio != min(
        (row.domain_quorum_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_domain_quorum_ratio must match rows")
    if report.max_cross_domain_conflict_ratio != max(
        (row.cross_domain_conflict_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_cross_domain_conflict_ratio must match rows")
    if report.max_stale_evidence_ratio != max(
        (row.stale_evidence_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_stale_evidence_ratio must match rows")
    if report.max_unresolved_blocker_count != max(
        (row.unresolved_blocker_count for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_unresolved_blocker_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyCrossDomainDecisionAuditReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyCrossDomainDecisionAuditInput],
) -> tuple[ResearchStrategyCrossDomainDecisionAuditInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainDecisionAuditInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCrossDomainDecisionAuditInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.audit_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by audit item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyCrossDomainDecisionAuditRow, ...],
) -> tuple[ResearchStrategyCrossDomainDecisionAuditRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainDecisionAuditRow:
            raise ValueError("rows must contain ResearchStrategyCrossDomainDecisionAuditRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.audit_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique audit item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyCrossDomainDecisionAuditReasonCodeCount, ...],
) -> tuple[ResearchStrategyCrossDomainDecisionAuditReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCrossDomainDecisionAuditReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCrossDomainDecisionAuditReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _UPSTREAM_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code
        for reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_CROSS_DOMAIN_DECISION_AUDIT_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_CROSS_DOMAIN_DECISION_AUDIT_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REPORT_REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(report: ResearchStrategyCrossDomainDecisionAuditReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        config=report.config,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_decision_audit_score=report.average_decision_audit_score,
        min_decision_audit_score=report.min_decision_audit_score,
        min_domain_quorum_ratio=report.min_domain_quorum_ratio,
        max_cross_domain_conflict_ratio=report.max_cross_domain_conflict_ratio,
        max_stale_evidence_ratio=report.max_stale_evidence_ratio,
        max_unresolved_blocker_count=report.max_unresolved_blocker_count,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchStrategyCrossDomainDecisionAuditReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "config": report.config,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_decision_audit_score": report.average_decision_audit_score,
            "min_decision_audit_score": report.min_decision_audit_score,
            "min_domain_quorum_ratio": report.min_domain_quorum_ratio,
            "max_cross_domain_conflict_ratio": report.max_cross_domain_conflict_ratio,
            "max_stale_evidence_ratio": report.max_stale_evidence_ratio,
            "max_unresolved_blocker_count": report.max_unresolved_blocker_count,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_public_payload_schema(payload: dict[str, object]) -> None:
    _require_payload_fields(
        "payload",
        payload,
        _REPORT_PUBLIC_PAYLOAD_FIELDS,
    )
    config_version = _require_payload_string(
        "payload.config_version",
        payload["config_version"],
    )
    validation_config = _config_from_public_payload(payload["config"])
    rows = tuple(
        _row_from_public_payload(
            item,
            index=index,
            validation_config=validation_config,
        )
        for index, item in enumerate(
            _require_payload_list("payload.rows", payload["rows"]),
        )
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item, index=index)
        for index, item in enumerate(
            _require_payload_list(
                "payload.reason_code_counts",
                payload["reason_code_counts"],
            ),
        )
    )
    report = ResearchStrategyCrossDomainDecisionAuditReport(
        generated_at=_public_payload_datetime(
            "payload.generated_at",
            payload["generated_at"],
        ),
        config_version=config_version,
        config=validation_config,
        status=_require_payload_string("payload.status", payload["status"]),
        row_count=_public_payload_count("payload.row_count", payload["row_count"]),
        pass_count=_public_payload_count("payload.pass_count", payload["pass_count"]),
        watch_count=_public_payload_count(
            "payload.watch_count",
            payload["watch_count"],
        ),
        block_count=_public_payload_count(
            "payload.block_count",
            payload["block_count"],
        ),
        average_decision_audit_score=_public_payload_ratio(
            "payload.average_decision_audit_score",
            payload["average_decision_audit_score"],
        ),
        min_decision_audit_score=_public_payload_ratio(
            "payload.min_decision_audit_score",
            payload["min_decision_audit_score"],
        ),
        min_domain_quorum_ratio=_public_payload_ratio(
            "payload.min_domain_quorum_ratio",
            payload["min_domain_quorum_ratio"],
        ),
        max_cross_domain_conflict_ratio=_public_payload_ratio(
            "payload.max_cross_domain_conflict_ratio",
            payload["max_cross_domain_conflict_ratio"],
        ),
        max_stale_evidence_ratio=_public_payload_ratio(
            "payload.max_stale_evidence_ratio",
            payload["max_stale_evidence_ratio"],
        ),
        max_unresolved_blocker_count=_public_payload_count(
            "payload.max_unresolved_blocker_count",
            payload["max_unresolved_blocker_count"],
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_public_payload_reason_codes(
            "payload.reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=_require_payload_string(
            "payload.derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_payload_true(
            "payload.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            "payload.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true("payload.readonly", payload["readonly"]),
    )
    if _report_payload(report) != payload:
        raise ValueError("payload must use the canonical public schema")


def _config_from_public_payload(
    value: object,
) -> ResearchStrategyCrossDomainDecisionAuditConfig:
    label = "payload.config"
    payload = _require_payload_object(label, value)
    _require_payload_fields(label, payload, _CONFIG_PUBLIC_PAYLOAD_FIELDS)
    return ResearchStrategyCrossDomainDecisionAuditConfig(
        config_version=_require_payload_string(
            f"{label}.config_version",
            payload["config_version"],
        ),
        pass_min_audit_score=_public_payload_ratio(
            f"{label}.pass_min_audit_score",
            payload["pass_min_audit_score"],
        ),
        watch_min_audit_score=_public_payload_ratio(
            f"{label}.watch_min_audit_score",
            payload["watch_min_audit_score"],
        ),
        min_pass_domain_quorum_ratio=_public_payload_ratio(
            f"{label}.min_pass_domain_quorum_ratio",
            payload["min_pass_domain_quorum_ratio"],
        ),
        min_watch_domain_quorum_ratio=_public_payload_ratio(
            f"{label}.min_watch_domain_quorum_ratio",
            payload["min_watch_domain_quorum_ratio"],
        ),
        max_pass_conflict_ratio=_public_payload_ratio(
            f"{label}.max_pass_conflict_ratio",
            payload["max_pass_conflict_ratio"],
        ),
        max_watch_conflict_ratio=_public_payload_ratio(
            f"{label}.max_watch_conflict_ratio",
            payload["max_watch_conflict_ratio"],
        ),
        max_pass_stale_evidence_ratio=_public_payload_ratio(
            f"{label}.max_pass_stale_evidence_ratio",
            payload["max_pass_stale_evidence_ratio"],
        ),
        max_watch_stale_evidence_ratio=_public_payload_ratio(
            f"{label}.max_watch_stale_evidence_ratio",
            payload["max_watch_stale_evidence_ratio"],
        ),
        max_pass_unresolved_blocker_count=_public_payload_count(
            f"{label}.max_pass_unresolved_blocker_count",
            payload["max_pass_unresolved_blocker_count"],
        ),
        max_watch_unresolved_blocker_count=_public_payload_count(
            f"{label}.max_watch_unresolved_blocker_count",
            payload["max_watch_unresolved_blocker_count"],
        ),
        domain_quorum_weight=_public_payload_ratio(
            f"{label}.domain_quorum_weight",
            payload["domain_quorum_weight"],
        ),
        evidence_alignment_weight=_public_payload_ratio(
            f"{label}.evidence_alignment_weight",
            payload["evidence_alignment_weight"],
        ),
        decision_trace_weight=_public_payload_ratio(
            f"{label}.decision_trace_weight",
            payload["decision_trace_weight"],
        ),
        resolution_readiness_weight=_public_payload_ratio(
            f"{label}.resolution_readiness_weight",
            payload["resolution_readiness_weight"],
        ),
        stale_evidence_control_weight=_public_payload_ratio(
            f"{label}.stale_evidence_control_weight",
            payload["stale_evidence_control_weight"],
        ),
        conflict_control_weight=_public_payload_ratio(
            f"{label}.conflict_control_weight",
            payload["conflict_control_weight"],
        ),
        memory_calibration_weight=_public_payload_ratio(
            f"{label}.memory_calibration_weight",
            payload["memory_calibration_weight"],
        ),
        paper_only=_require_payload_true(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true(
            f"{label}.readonly",
            payload["readonly"],
        ),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
    validation_config: ResearchStrategyCrossDomainDecisionAuditConfig,
) -> ResearchStrategyCrossDomainDecisionAuditRow:
    label = f"payload.rows[{index}]"
    payload = _require_payload_object(label, value)
    _require_payload_fields(label, payload, _ROW_PUBLIC_PAYLOAD_FIELDS)
    return ResearchStrategyCrossDomainDecisionAuditRow(
        audit_item_digest=_require_payload_string(
            f"{label}.audit_item_digest",
            payload["audit_item_digest"],
        ),
        domain_quorum_ratio=_public_payload_ratio(
            f"{label}.domain_quorum_ratio",
            payload["domain_quorum_ratio"],
        ),
        evidence_alignment_score=_public_payload_ratio(
            f"{label}.evidence_alignment_score",
            payload["evidence_alignment_score"],
        ),
        decision_trace_score=_public_payload_ratio(
            f"{label}.decision_trace_score",
            payload["decision_trace_score"],
        ),
        resolution_readiness_score=_public_payload_ratio(
            f"{label}.resolution_readiness_score",
            payload["resolution_readiness_score"],
        ),
        stale_evidence_ratio=_public_payload_ratio(
            f"{label}.stale_evidence_ratio",
            payload["stale_evidence_ratio"],
        ),
        stale_evidence_control_score=_public_payload_ratio(
            f"{label}.stale_evidence_control_score",
            payload["stale_evidence_control_score"],
        ),
        cross_domain_conflict_ratio=_public_payload_ratio(
            f"{label}.cross_domain_conflict_ratio",
            payload["cross_domain_conflict_ratio"],
        ),
        conflict_control_score=_public_payload_ratio(
            f"{label}.conflict_control_score",
            payload["conflict_control_score"],
        ),
        memory_calibration_score=_public_payload_ratio(
            f"{label}.memory_calibration_score",
            payload["memory_calibration_score"],
        ),
        unresolved_blocker_count=_public_payload_count(
            f"{label}.unresolved_blocker_count",
            payload["unresolved_blocker_count"],
        ),
        decision_audit_score=_public_payload_ratio(
            f"{label}.decision_audit_score",
            payload["decision_audit_score"],
        ),
        weakest_dimension_score=_public_payload_ratio(
            f"{label}.weakest_dimension_score",
            payload["weakest_dimension_score"],
        ),
        observed_at=_public_payload_datetime(
            f"{label}.observed_at",
            payload["observed_at"],
        ),
        status=_require_payload_string(f"{label}.status", payload["status"]),
        reason_codes=_public_payload_reason_codes(
            f"{label}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_require_payload_true(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true(f"{label}.readonly", payload["readonly"]),
        validation_config=validation_config,
    )


def _reason_code_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyCrossDomainDecisionAuditReasonCodeCount:
    label = f"payload.reason_code_counts[{index}]"
    payload = _require_payload_object(label, value)
    _require_payload_fields(
        label,
        payload,
        _REASON_CODE_COUNT_PUBLIC_PAYLOAD_FIELDS,
    )
    return ResearchStrategyCrossDomainDecisionAuditReasonCodeCount(
        reason_code=_require_payload_string(
            f"{label}.reason_code",
            payload["reason_code"],
        ),
        count=_public_payload_count(f"{label}.count", payload["count"]),
        row_ratio=_public_payload_ratio(f"{label}.row_ratio", payload["row_ratio"]),
        paper_only=_require_payload_true(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true(f"{label}.readonly", payload["readonly"]),
    )


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{label} fields must match the public schema")


def _require_payload_object(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_payload_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON array")
    return value


def _require_payload_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    return value


def _require_payload_true(label: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{label} must be True")
    return True


def _public_payload_decimal(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{label} must be finite")
    return parsed


def _public_payload_ratio(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_ratio_decimal(label, _public_payload_decimal(label, text))
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_count(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_nonnegative_count_decimal(
        label,
        _public_payload_decimal(label, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_datetime(label: str, value: object) -> datetime:
    text = _require_payload_string(label, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 datetime string") from exc
    normalized = _as_utc(label, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return normalized


def _public_payload_reason_codes(label: str, value: object) -> tuple[str, ...]:
    items = _require_payload_list(label, value)
    return tuple(
        _require_payload_string(f"{label}[{index}]", item)
        for index, item in enumerate(items)
    )


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if type(value) is dict:
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, Mapping):
        raise ValueError("payload JSON objects must use exact dict values")
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if isinstance(value, list):
        raise ValueError("payload JSON arrays must use exact list values")
    raise ValueError("payload value is not JSON serializable")


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    raise ValueError("payload value is not JSON serializable")


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
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use negative zero")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("denominator must be nonzero")
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio(sum(values, _ZERO), _decimal_count(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _config_weight_sum(config: ResearchStrategyCrossDomainDecisionAuditConfig) -> Decimal:
    return _quantize(
        config.domain_quorum_weight
        + config.evidence_alignment_weight
        + config.decision_trace_weight
        + config.resolution_readiness_weight
        + config.stale_evidence_control_weight
        + config.conflict_control_weight
        + config.memory_calibration_weight,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_CROSS_DOMAIN_DECISION_AUDIT_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyCrossDomainDecisionAuditRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyCrossDomainDecisionAuditRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyCrossDomainDecisionAuditRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.decision_audit_score, row.audit_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyCrossDomainDecisionAuditRow, ...],
) -> tuple[ResearchStrategyCrossDomainDecisionAuditReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyCrossDomainDecisionAuditReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _private_ref_digest(value: str) -> str:
    _require_private_ref("audit_item_ref", value)
    digest = sha256(f"cross-domain-decision-audit:{value}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public text")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    compact = value.replace("_", "")
    if value.lower() != value or not compact.isalnum():
        raise ValueError(f"{field_name} must be lowercase snake case")
    if value not in allowed_values:
        raise ValueError(f"{field_name} is not supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    if value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{label} Decimal value must be finite")
        return
    if type(value) is datetime:
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{label} numeric values must use Decimal strings")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list) and allow_json_containers:
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    raise ValueError(f"{label} payload value is not supported")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    compact = "".join(character for character in normalized if character.isalnum())
    for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in normalized:
            return True
        fragment_compact = "".join(
            character for character in fragment.lower() if character.isalnum()
        )
        if fragment_compact and fragment_compact in compact:
            return True
    return False
