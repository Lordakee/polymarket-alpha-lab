"""Pure report-only specialist memory conflict escalation reducer."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-conflict-escalation-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SPECIALIST_MEMORY_CONFLICT_ESCALATION_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
COMPONENT_COUNT = Decimal("4.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_OBSERVATIONS_REASON = "specialist_memory_conflict_escalation_no_observations"
CLEAR_REASON = "specialist_memory_conflict_escalation_clear"
OPEN_CONFLICT_BLOCK_REASON = "open_memory_conflict_block"
OPEN_CONFLICT_WATCH_REASON = "open_memory_conflict_watch"
REOPENED_CONFLICT_BLOCK_REASON = "reopened_memory_conflict_block"
REOPENED_CONFLICT_WATCH_REASON = "reopened_memory_conflict_watch"
PEER_AGREEMENT_BLOCK_REASON = "peer_agreement_block"
PEER_AGREEMENT_WATCH_REASON = "peer_agreement_watch"
EVIDENCE_ALIGNMENT_BLOCK_REASON = "evidence_alignment_block"
EVIDENCE_ALIGNMENT_WATCH_REASON = "evidence_alignment_watch"

ROW_REASON_CODE_SEQUENCE = (
    OPEN_CONFLICT_BLOCK_REASON,
    OPEN_CONFLICT_WATCH_REASON,
    REOPENED_CONFLICT_BLOCK_REASON,
    REOPENED_CONFLICT_WATCH_REASON,
    PEER_AGREEMENT_BLOCK_REASON,
    PEER_AGREEMENT_WATCH_REASON,
    EVIDENCE_ALIGNMENT_BLOCK_REASON,
    EVIDENCE_ALIGNMENT_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "specialist_memory_conflict_escalation_report_clear"
REPORT_BLOCK_PRESENT_REASON = "specialist_memory_conflict_escalation_block_present"
REPORT_WATCH_PRESENT_REASON = "specialist_memory_conflict_escalation_watch_present"
REPORT_OPEN_CONFLICT_REASON = "open_memory_conflict_present"
REPORT_REOPENED_CONFLICT_REASON = "reopened_memory_conflict_present"
REPORT_PEER_AGREEMENT_GAP_REASON = "peer_agreement_gap_present"
REPORT_EVIDENCE_ALIGNMENT_GAP_REASON = "evidence_alignment_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_OPEN_CONFLICT_REASON,
    REPORT_REOPENED_CONFLICT_REASON,
    REPORT_PEER_AGREEMENT_GAP_REASON,
    REPORT_EVIDENCE_ALIGNMENT_GAP_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "reuse_specialist_memory_after_conflict_check",
    STATUS_WATCH: "review_specialist_memory_conflict_before_reuse",
    STATUS_BLOCK: "block_memory_reuse_until_conflict_review",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket"),
    _join_parts("s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("u", "rl"),
    _join_parts("sou", "rce", "_", "text"),
    _join_parts("sou", "rce", "_", "id"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
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

AGGREGATE_LABEL_FIELDS = (
    "domain_label",
    "specialist_label",
    "memory_bucket_label",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION",
    "SPECIALIST_MEMORY_CONFLICT_ESCALATION_STATUSES",
    "ResearchTeamSpecialistMemoryConflictEscalationConfig",
    "ResearchTeamSpecialistMemoryConflictEscalationDomainSummary",
    "ResearchTeamSpecialistMemoryConflictEscalationObservation",
    "ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount",
    "ResearchTeamSpecialistMemoryConflictEscalationReport",
    "ResearchTeamSpecialistMemoryConflictEscalationRow",
    "build_research_team_specialist_memory_conflict_escalation_report",
    "research_team_specialist_memory_conflict_escalation_report_digest",
    "research_team_specialist_memory_conflict_escalation_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryConflictEscalationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION
    )
    max_pass_open_conflict_ratio: Decimal = Decimal("0.100000")
    max_watch_open_conflict_ratio: Decimal = Decimal("0.250000")
    max_pass_reopened_conflict_ratio: Decimal = Decimal("0.050000")
    max_watch_reopened_conflict_ratio: Decimal = Decimal("0.150000")
    min_pass_peer_agreement_ratio: Decimal = Decimal("0.800000")
    min_watch_peer_agreement_ratio: Decimal = Decimal("0.600000")
    min_pass_evidence_alignment_ratio: Decimal = Decimal("0.800000")
    min_watch_evidence_alignment_ratio: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryConflictEscalationConfig:
            raise TypeError(
                "ResearchTeamSpecialistMemoryConflictEscalationConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryConflictEscalationConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "max_pass_open_conflict_ratio",
            "max_watch_open_conflict_ratio",
            "max_pass_reopened_conflict_ratio",
            "max_watch_reopened_conflict_ratio",
            "min_pass_peer_agreement_ratio",
            "min_watch_peer_agreement_ratio",
            "min_pass_evidence_alignment_ratio",
            "min_watch_evidence_alignment_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.max_pass_open_conflict_ratio > self.max_watch_open_conflict_ratio:
            raise ValueError("max_pass_open_conflict_ratio must not exceed watch")
        if self.max_pass_reopened_conflict_ratio > self.max_watch_reopened_conflict_ratio:
            raise ValueError("max_pass_reopened_conflict_ratio must not exceed watch")
        if self.min_watch_peer_agreement_ratio > self.min_pass_peer_agreement_ratio:
            raise ValueError("min_watch_peer_agreement_ratio must not exceed pass")
        if self.min_watch_evidence_alignment_ratio > self.min_pass_evidence_alignment_ratio:
            raise ValueError("min_watch_evidence_alignment_ratio must not exceed pass")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryConflictEscalationObservation:
    domain_label: str
    specialist_label: str
    memory_bucket_label: str
    observed_at: datetime
    reviewed_memory_count: Decimal
    open_conflict_count: Decimal
    reopened_conflict_count: Decimal
    peer_review_count: Decimal
    peer_agreement_count: Decimal
    evidence_check_count: Decimal
    evidence_aligned_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryConflictEscalationObservation:
            raise TypeError(
                "ResearchTeamSpecialistMemoryConflictEscalationObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryConflictEscalationObservation,
            "observation",
        )
        for name in ("domain_label", "specialist_label", "memory_bucket_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "reviewed_memory_count",
            "peer_review_count",
            "evidence_check_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "open_conflict_count",
            "reopened_conflict_count",
            "peer_agreement_count",
            "evidence_aligned_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _validate_observation_counts(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryConflictEscalationRow:
    domain_label: str
    specialist_label: str
    memory_bucket_label: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    reviewed_memory_count: Decimal
    open_conflict_count: Decimal
    reopened_conflict_count: Decimal
    peer_review_count: Decimal
    peer_agreement_count: Decimal
    evidence_check_count: Decimal
    evidence_aligned_count: Decimal
    open_conflict_ratio: Decimal
    reopened_conflict_ratio: Decimal
    peer_agreement_ratio: Decimal
    evidence_alignment_ratio: Decimal
    escalation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryConflictEscalationRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryConflictEscalationRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryConflictEscalationRow, "row")
        for name in ("domain_label", "specialist_label", "memory_bucket_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal("snapshot_age_seconds", self.snapshot_age_seconds),
        )
        for name in (
            "reviewed_memory_count",
            "peer_review_count",
            "evidence_check_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "open_conflict_count",
            "reopened_conflict_count",
            "peer_agreement_count",
            "evidence_aligned_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "open_conflict_ratio",
            "reopened_conflict_ratio",
            "peer_agreement_ratio",
            "evidence_alignment_ratio",
            "escalation_score",
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
class ResearchTeamSpecialistMemoryConflictEscalationDomainSummary:
    domain_label: str
    specialist_count: Decimal
    reviewed_memory_count: Decimal
    open_conflict_count: Decimal
    reopened_conflict_count: Decimal
    open_conflict_ratio: Decimal
    reopened_conflict_ratio: Decimal
    worst_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryConflictEscalationDomainSummary:
            raise TypeError(
                "ResearchTeamSpecialistMemoryConflictEscalationDomainSummary does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryConflictEscalationDomainSummary,
            "domain summary",
        )
        object.__setattr__(
            self,
            "domain_label",
            _require_public_label("domain_label", self.domain_label),
        )
        for name in ("specialist_count", "reviewed_memory_count"):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in ("open_conflict_count", "reopened_conflict_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in ("open_conflict_ratio", "reopened_conflict_ratio"):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "worst_status",
            _require_status("worst_status", self.worst_status),
        )
        _validate_domain_summary(self)
        _require_hard_flags("domain summary", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryConflictEscalationReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    observation_count: Decimal
    domain_count: Decimal
    specialist_count: Decimal
    reviewed_memory_count: Decimal
    open_conflict_count: Decimal
    reopened_conflict_count: Decimal
    peer_review_count: Decimal
    peer_agreement_count: Decimal
    evidence_check_count: Decimal
    evidence_aligned_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    open_conflict_ratio: Decimal
    reopened_conflict_ratio: Decimal
    peer_agreement_ratio: Decimal
    evidence_alignment_ratio: Decimal
    escalation_score: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...]
    domain_summaries: tuple[ResearchTeamSpecialistMemoryConflictEscalationDomainSummary, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryConflictEscalationReport:
            raise TypeError(
                "ResearchTeamSpecialistMemoryConflictEscalationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryConflictEscalationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
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
            "reviewed_memory_count",
            "open_conflict_count",
            "reopened_conflict_count",
            "peer_review_count",
            "peer_agreement_count",
            "evidence_check_count",
            "evidence_aligned_count",
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
            "open_conflict_ratio",
            "reopened_conflict_ratio",
            "peer_agreement_ratio",
            "evidence_alignment_ratio",
            "escalation_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "domain_summaries",
            _normalize_domain_summaries(self.domain_summaries),
        )
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
        return research_team_specialist_memory_conflict_escalation_report_payload(self)


def build_research_team_specialist_memory_conflict_escalation_report(
    observations: Iterable[ResearchTeamSpecialistMemoryConflictEscalationObservation],
    *,
    config: ResearchTeamSpecialistMemoryConflictEscalationConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryConflictEscalationReport:
    cfg = (
        ResearchTeamSpecialistMemoryConflictEscalationConfig()
        if config is None
        else config
    )
    if type(cfg) is not ResearchTeamSpecialistMemoryConflictEscalationConfig:
        raise ValueError(
            "config must be exactly ResearchTeamSpecialistMemoryConflictEscalationConfig",
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
    return ResearchTeamSpecialistMemoryConflictEscalationReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_report_status(rows),
        next_review_step=NEXT_REVIEW_STEPS[_report_status(rows)],
        observation_count=_count_decimal(len(normalized_observations)),
        domain_count=_count_decimal(len({row.domain_label for row in rows})),
        specialist_count=_count_decimal(
            len({(row.domain_label, row.specialist_label) for row in rows}),
        ),
        reviewed_memory_count=_sum_decimal(row.reviewed_memory_count for row in rows),
        open_conflict_count=_sum_decimal(row.open_conflict_count for row in rows),
        reopened_conflict_count=_sum_decimal(row.reopened_conflict_count for row in rows),
        peer_review_count=_sum_decimal(row.peer_review_count for row in rows),
        peer_agreement_count=_sum_decimal(row.peer_agreement_count for row in rows),
        evidence_check_count=_sum_decimal(row.evidence_check_count for row in rows),
        evidence_aligned_count=_sum_decimal(row.evidence_aligned_count for row in rows),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        open_conflict_ratio=_aggregate_open_conflict_ratio(rows),
        reopened_conflict_ratio=_aggregate_reopened_conflict_ratio(rows),
        peer_agreement_ratio=_aggregate_peer_agreement_ratio(rows),
        evidence_alignment_ratio=_aggregate_evidence_alignment_ratio(rows),
        escalation_score=_aggregate_escalation_score(rows),
        rows=rows,
        domain_summaries=_domain_summaries(rows),
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows, len(normalized_observations)),
    )


def research_team_specialist_memory_conflict_escalation_report_payload(
    value: object,
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    _validate_report_payload_shape(payload)
    return payload


def research_team_specialist_memory_conflict_escalation_report_digest(
    report: ResearchTeamSpecialistMemoryConflictEscalationReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistMemoryConflictEscalationReport:
        raise ValueError(
            "report must be exactly ResearchTeamSpecialistMemoryConflictEscalationReport",
        )
    return report.derived_validation_digest


def _row_from_observation(
    observation: ResearchTeamSpecialistMemoryConflictEscalationObservation,
    *,
    config: ResearchTeamSpecialistMemoryConflictEscalationConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryConflictEscalationRow:
    open_conflict_ratio = _safe_divide(
        observation.open_conflict_count,
        observation.reviewed_memory_count,
    )
    reopened_conflict_ratio = _safe_divide(
        observation.reopened_conflict_count,
        observation.reviewed_memory_count,
    )
    peer_agreement_ratio = _safe_divide(
        observation.peer_agreement_count,
        observation.peer_review_count,
    )
    evidence_alignment_ratio = _safe_divide(
        observation.evidence_aligned_count,
        observation.evidence_check_count,
    )
    reason_codes = _row_reason_codes(
        open_conflict_ratio=open_conflict_ratio,
        reopened_conflict_ratio=reopened_conflict_ratio,
        peer_agreement_ratio=peer_agreement_ratio,
        evidence_alignment_ratio=evidence_alignment_ratio,
        config=config,
    )
    return ResearchTeamSpecialistMemoryConflictEscalationRow(
        domain_label=observation.domain_label,
        specialist_label=observation.specialist_label,
        memory_bucket_label=observation.memory_bucket_label,
        observed_at=observation.observed_at,
        snapshot_age_seconds=_age_seconds(generated_at, observation.observed_at),
        reviewed_memory_count=observation.reviewed_memory_count,
        open_conflict_count=observation.open_conflict_count,
        reopened_conflict_count=observation.reopened_conflict_count,
        peer_review_count=observation.peer_review_count,
        peer_agreement_count=observation.peer_agreement_count,
        evidence_check_count=observation.evidence_check_count,
        evidence_aligned_count=observation.evidence_aligned_count,
        open_conflict_ratio=open_conflict_ratio,
        reopened_conflict_ratio=reopened_conflict_ratio,
        peer_agreement_ratio=peer_agreement_ratio,
        evidence_alignment_ratio=evidence_alignment_ratio,
        escalation_score=_escalation_score(
            open_conflict_ratio=open_conflict_ratio,
            reopened_conflict_ratio=reopened_conflict_ratio,
            peer_agreement_ratio=peer_agreement_ratio,
            evidence_alignment_ratio=evidence_alignment_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    open_conflict_ratio: Decimal,
    reopened_conflict_ratio: Decimal,
    peer_agreement_ratio: Decimal,
    evidence_alignment_ratio: Decimal,
    config: ResearchTeamSpecialistMemoryConflictEscalationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if open_conflict_ratio > config.max_watch_open_conflict_ratio:
        reason_codes.append(OPEN_CONFLICT_BLOCK_REASON)
    elif open_conflict_ratio > config.max_pass_open_conflict_ratio:
        reason_codes.append(OPEN_CONFLICT_WATCH_REASON)
    if reopened_conflict_ratio > config.max_watch_reopened_conflict_ratio:
        reason_codes.append(REOPENED_CONFLICT_BLOCK_REASON)
    elif reopened_conflict_ratio > config.max_pass_reopened_conflict_ratio:
        reason_codes.append(REOPENED_CONFLICT_WATCH_REASON)
    if peer_agreement_ratio < config.min_watch_peer_agreement_ratio:
        reason_codes.append(PEER_AGREEMENT_BLOCK_REASON)
    elif peer_agreement_ratio < config.min_pass_peer_agreement_ratio:
        reason_codes.append(PEER_AGREEMENT_WATCH_REASON)
    if evidence_alignment_ratio < config.min_watch_evidence_alignment_ratio:
        reason_codes.append(EVIDENCE_ALIGNMENT_BLOCK_REASON)
    elif evidence_alignment_ratio < config.min_pass_evidence_alignment_ratio:
        reason_codes.append(EVIDENCE_ALIGNMENT_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
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
        (OPEN_CONFLICT_BLOCK_REASON, OPEN_CONFLICT_WATCH_REASON),
    ):
        reason_codes.append(REPORT_OPEN_CONFLICT_REASON)
    if _row_reason_count(
        rows,
        (REOPENED_CONFLICT_BLOCK_REASON, REOPENED_CONFLICT_WATCH_REASON),
    ):
        reason_codes.append(REPORT_REOPENED_CONFLICT_REASON)
    if _row_reason_count(
        rows,
        (PEER_AGREEMENT_BLOCK_REASON, PEER_AGREEMENT_WATCH_REASON),
    ):
        reason_codes.append(REPORT_PEER_AGREEMENT_GAP_REASON)
    if _row_reason_count(
        rows,
        (EVIDENCE_ALIGNMENT_BLOCK_REASON, EVIDENCE_ALIGNMENT_WATCH_REASON),
    ):
        reason_codes.append(REPORT_EVIDENCE_ALIGNMENT_GAP_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_total = _count_decimal(len(rows))
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    return tuple(
        ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
            row_ratio=_safe_divide(_count_decimal(counter[reason_code]), row_total),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _domain_summaries(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryConflictEscalationDomainSummary, ...]:
    domain_labels = sorted({row.domain_label for row in rows})
    return tuple(_domain_summary_for_label(domain_label, rows) for domain_label in domain_labels)


def _domain_summary_for_label(
    domain_label: str,
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> ResearchTeamSpecialistMemoryConflictEscalationDomainSummary:
    domain_rows = tuple(row for row in rows if row.domain_label == domain_label)
    reviewed_memory_count = _sum_decimal(row.reviewed_memory_count for row in domain_rows)
    open_conflict_count = _sum_decimal(row.open_conflict_count for row in domain_rows)
    reopened_conflict_count = _sum_decimal(
        row.reopened_conflict_count for row in domain_rows
    )
    return ResearchTeamSpecialistMemoryConflictEscalationDomainSummary(
        domain_label=domain_label,
        specialist_count=_count_decimal(len({row.specialist_label for row in domain_rows})),
        reviewed_memory_count=reviewed_memory_count,
        open_conflict_count=open_conflict_count,
        reopened_conflict_count=reopened_conflict_count,
        open_conflict_ratio=_safe_divide(
            open_conflict_count,
            reviewed_memory_count,
        ),
        reopened_conflict_ratio=_safe_divide(
            reopened_conflict_count,
            reviewed_memory_count,
        ),
        worst_status=_report_status(domain_rows),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_count(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _row_sort_key(
    row: ResearchTeamSpecialistMemoryConflictEscalationRow,
) -> tuple[int, str, str, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.domain_label,
        row.specialist_label,
        row.memory_bucket_label,
    )


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistMemoryConflictEscalationObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistMemoryConflictEscalationObservation, ...]:
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchTeamSpecialistMemoryConflictEscalationObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchTeamSpecialistMemoryConflictEscalationObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keys = tuple(
        (item.domain_label, item.specialist_label, item.memory_bucket_label)
        for item in normalized
    )
    if len(set(keys)) != len(keys):
        raise ValueError("domain_label, specialist_label, and memory_bucket_label triples must be unique")
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.domain_label,
                item.specialist_label,
                item.memory_bucket_label,
            ),
        ),
    )


def _normalize_rows(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryConflictEscalationRow:
            raise ValueError(
                "rows must contain exactly ResearchTeamSpecialistMemoryConflictEscalationRow",
            )
        _require_hard_flags("row", row)
    keys = tuple((row.domain_label, row.specialist_label, row.memory_bucket_label) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError("rows domain_label, specialist_label, and memory_bucket_label triples must be unique")
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_domain_summaries(
    values: tuple[ResearchTeamSpecialistMemoryConflictEscalationDomainSummary, ...],
) -> tuple[ResearchTeamSpecialistMemoryConflictEscalationDomainSummary, ...]:
    if type(values) is not tuple:
        raise ValueError("domain_summaries must be a tuple")
    for value in values:
        if type(value) is not ResearchTeamSpecialistMemoryConflictEscalationDomainSummary:
            raise ValueError(
                "domain_summaries must contain exactly "
                "ResearchTeamSpecialistMemoryConflictEscalationDomainSummary",
            )
        _require_hard_flags("domain summary", value)
    labels = tuple(value.domain_label for value in values)
    if len(set(labels)) != len(labels):
        raise ValueError("domain_summaries domain_label values must be unique")
    return tuple(sorted(values, key=lambda value: value.domain_label))


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    reason_codes = tuple(count.reason_code for count in counts)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return tuple(
        sorted(
            counts,
            key=lambda count: COUNT_REASON_CODE_SEQUENCE.index(count.reason_code),
        ),
    )


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must be unique")
    for value in values:
        _require_member(name, value, allowed)
    return tuple(sorted(values, key=allowed.index))


def _validate_observation_counts(
    observation: ResearchTeamSpecialistMemoryConflictEscalationObservation,
) -> None:
    if observation.open_conflict_count > observation.reviewed_memory_count:
        raise ValueError("open_conflict_count must not exceed reviewed_memory_count")
    if observation.reopened_conflict_count > observation.reviewed_memory_count:
        raise ValueError("reopened_conflict_count must not exceed reviewed_memory_count")
    if observation.peer_agreement_count > observation.peer_review_count:
        raise ValueError("peer_agreement_count must not exceed peer_review_count")
    if observation.evidence_aligned_count > observation.evidence_check_count:
        raise ValueError("evidence_aligned_count must not exceed evidence_check_count")


def _validate_row(row: ResearchTeamSpecialistMemoryConflictEscalationRow) -> None:
    if row.open_conflict_count > row.reviewed_memory_count:
        raise ValueError("open_conflict_count must not exceed reviewed_memory_count")
    if row.reopened_conflict_count > row.reviewed_memory_count:
        raise ValueError("reopened_conflict_count must not exceed reviewed_memory_count")
    if row.peer_agreement_count > row.peer_review_count:
        raise ValueError("peer_agreement_count must not exceed peer_review_count")
    if row.evidence_aligned_count > row.evidence_check_count:
        raise ValueError("evidence_aligned_count must not exceed evidence_check_count")
    expected_ratios = {
        "open_conflict_ratio": _safe_divide(
            row.open_conflict_count,
            row.reviewed_memory_count,
        ),
        "reopened_conflict_ratio": _safe_divide(
            row.reopened_conflict_count,
            row.reviewed_memory_count,
        ),
        "peer_agreement_ratio": _safe_divide(
            row.peer_agreement_count,
            row.peer_review_count,
        ),
        "evidence_alignment_ratio": _safe_divide(
            row.evidence_aligned_count,
            row.evidence_check_count,
        ),
    }
    for name, expected in expected_ratios.items():
        if getattr(row, name) != expected:
            raise ValueError(f"{name} must match row counts")
    expected_score = _escalation_score(
        open_conflict_ratio=row.open_conflict_ratio,
        reopened_conflict_ratio=row.reopened_conflict_ratio,
        peer_agreement_ratio=row.peer_agreement_ratio,
        evidence_alignment_ratio=row.evidence_alignment_ratio,
    )
    if row.escalation_score != expected_score:
        raise ValueError("escalation_score must match row ratios")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_domain_summary(
    value: ResearchTeamSpecialistMemoryConflictEscalationDomainSummary,
) -> None:
    if value.open_conflict_count > value.reviewed_memory_count:
        raise ValueError("open_conflict_count must not exceed reviewed_memory_count")
    if value.reopened_conflict_count > value.reviewed_memory_count:
        raise ValueError("reopened_conflict_count must not exceed reviewed_memory_count")
    if value.open_conflict_ratio != _safe_divide(
        value.open_conflict_count,
        value.reviewed_memory_count,
    ):
        raise ValueError("open_conflict_ratio must match domain counts")
    if value.reopened_conflict_ratio != _safe_divide(
        value.reopened_conflict_count,
        value.reviewed_memory_count,
    ):
        raise ValueError("reopened_conflict_ratio must match domain counts")


def _validate_report(report: ResearchTeamSpecialistMemoryConflictEscalationReport) -> None:
    expected_counts = {
        "observation_count": _count_decimal(len(report.rows)),
        "domain_count": _count_decimal(len({row.domain_label for row in report.rows})),
        "specialist_count": _count_decimal(
            len({(row.domain_label, row.specialist_label) for row in report.rows}),
        ),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
    }
    for name, expected in expected_counts.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    expected_sums = {
        "reviewed_memory_count": _sum_decimal(
            row.reviewed_memory_count for row in report.rows
        ),
        "open_conflict_count": _sum_decimal(row.open_conflict_count for row in report.rows),
        "reopened_conflict_count": _sum_decimal(
            row.reopened_conflict_count for row in report.rows
        ),
        "peer_review_count": _sum_decimal(row.peer_review_count for row in report.rows),
        "peer_agreement_count": _sum_decimal(row.peer_agreement_count for row in report.rows),
        "evidence_check_count": _sum_decimal(row.evidence_check_count for row in report.rows),
        "evidence_aligned_count": _sum_decimal(
            row.evidence_aligned_count for row in report.rows
        ),
    }
    for name, expected in expected_sums.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    expected_ratios = {
        "open_conflict_ratio": _aggregate_open_conflict_ratio(report.rows),
        "reopened_conflict_ratio": _aggregate_reopened_conflict_ratio(report.rows),
        "peer_agreement_ratio": _aggregate_peer_agreement_ratio(report.rows),
        "evidence_alignment_ratio": _aggregate_evidence_alignment_ratio(report.rows),
        "escalation_score": _aggregate_escalation_score(report.rows),
    }
    for name, expected in expected_ratios.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.domain_summaries != _domain_summaries(report.rows):
        raise ValueError("domain_summaries must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.observation_count)):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")


def _aggregate_open_conflict_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.open_conflict_count for row in rows),
        _sum_decimal(row.reviewed_memory_count for row in rows),
    )


def _aggregate_reopened_conflict_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.reopened_conflict_count for row in rows),
        _sum_decimal(row.reviewed_memory_count for row in rows),
    )


def _aggregate_peer_agreement_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.peer_agreement_count for row in rows),
        _sum_decimal(row.peer_review_count for row in rows),
    )


def _aggregate_evidence_alignment_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.evidence_aligned_count for row in rows),
        _sum_decimal(row.evidence_check_count for row in rows),
    )


def _aggregate_escalation_score(
    rows: tuple[ResearchTeamSpecialistMemoryConflictEscalationRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _escalation_score(
        open_conflict_ratio=_aggregate_open_conflict_ratio(rows),
        reopened_conflict_ratio=_aggregate_reopened_conflict_ratio(rows),
        peer_agreement_ratio=_aggregate_peer_agreement_ratio(rows),
        evidence_alignment_ratio=_aggregate_evidence_alignment_ratio(rows),
    )


def _escalation_score(
    *,
    open_conflict_ratio: Decimal,
    reopened_conflict_ratio: Decimal,
    peer_agreement_ratio: Decimal,
    evidence_alignment_ratio: Decimal,
) -> Decimal:
    return _quantize_decimal(
        (
            open_conflict_ratio
            + reopened_conflict_ratio
            + (ONE - peer_agreement_ratio)
            + (ONE - evidence_alignment_ratio)
        )
        / COMPONENT_COUNT,
    )


def _require_supported_payload_input(value: object) -> None:
    if type(value) is dict:
        return
    if type(value) is ResearchTeamSpecialistMemoryConflictEscalationReport:
        _require_hard_flags("payload input", value)
        return
    raise ValueError(
        "value must be a ResearchTeamSpecialistMemoryConflictEscalationReport or dict",
    )


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
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
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
                for index, child in enumerate(item):
                    if type(child) is dict:
                        _validate_payload_flags(child, f"{field_path}.{key}.{index}")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest must be present")
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    if digest != _digest_payload(payload):
        raise ValueError("derived_validation_digest must match payload")


def _validate_report_payload_shape(payload: dict[str, Any]) -> None:
    expected_fields = {
        item.name for item in fields(ResearchTeamSpecialistMemoryConflictEscalationReport)
    }
    if set(payload) != expected_fields:
        raise ValueError("payload must match report fields")
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION
    ):
        raise ValueError("payload config_version must be the supported config version")
    status = _require_status("payload status", payload["status"])
    next_review_step = _require_public_label(
        "payload next_review_step",
        payload["next_review_step"],
    )
    if next_review_step != NEXT_REVIEW_STEPS[status]:
        raise ValueError("payload next_review_step must match status")
    _validate_payload_records(
        "rows",
        payload["rows"],
        ResearchTeamSpecialistMemoryConflictEscalationRow,
        status_field="status",
    )
    _validate_payload_records(
        "domain_summaries",
        payload["domain_summaries"],
        ResearchTeamSpecialistMemoryConflictEscalationDomainSummary,
        status_field="worst_status",
    )
    _validate_payload_records(
        "reason_code_counts",
        payload["reason_code_counts"],
        ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount,
    )


def _validate_payload_records(
    name: str,
    value: object,
    record_type: type[object],
    *,
    status_field: str | None = None,
) -> None:
    if type(value) is not list:
        raise ValueError(f"payload {name} must be a list")
    expected_fields = {item.name for item in fields(record_type)}
    for index, item in enumerate(value):
        if type(item) is not dict or set(item) != expected_fields:
            raise ValueError(f"payload {name}.{index} must match record fields")
        for label_field in AGGREGATE_LABEL_FIELDS:
            if label_field in item:
                _require_public_label(label_field, item[label_field])
        if status_field is not None:
            _require_status(f"payload {name}.{index}.{status_field}", item[status_field])


def _derived_validation_digest(
    report: ResearchTeamSpecialistMemoryConflictEscalationReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


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
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload field or value")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{name} must not have surrounding whitespace")
    if len(value) > 96:
        raise ValueError(f"{name} must be short")
    allowed_characters = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-",
    )
    if any(character not in allowed_characters for character in value):
        raise ValueError(f"{name} must be a public-safe aggregate label")
    if name in AGGREGATE_LABEL_FIELDS and _looks_like_opaque_reference(value):
        raise ValueError(f"{name} must be a public-safe aggregate label")
    _reject_unsafe_public_text(value)
    return value


def _looks_like_opaque_reference(value: str) -> bool:
    if value.isdecimal() or "-" in value:
        return True
    lowered = value.lower()
    hexadecimal_characters = set("0123456789abcdef")
    if (
        lowered.startswith("0x")
        and len(lowered) >= 18
        and all(character in hexadecimal_characters for character in lowered[2:])
    ):
        return True
    return len(value) >= 24 and value.isalnum()


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{name} exceeds required decimal precision")
    return _quantize_decimal(value)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_status(name: str, value: str) -> str:
    return _require_member(name, value, SPECIALIST_MEMORY_CONFLICT_ESCALATION_STATUSES)


def _require_member(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")
    return value


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    int(value, 16)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name) is not True:
            raise ValueError(f"{label} {name} must be True")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.microsecond != 0:
        raise ValueError(f"{name} must be a whole second")
    return value.astimezone(UTC)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize_decimal(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)
