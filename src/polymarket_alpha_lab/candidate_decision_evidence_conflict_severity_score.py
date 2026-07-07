"""Pure report-only evidence conflict severity scoring."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CANDIDATE_DECISION_EVIDENCE_CONFLICT_SEVERITY_SCORE_VERSION = (
    "candidate-decision-evidence-conflict-severity-score-v1"
)

SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
PUBLIC_STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "CandidateDecisionEvidenceConflictSeverityScoreConfig",
        "CandidateDecisionEvidenceConflictSeverityFacts",
        "CandidateDecisionEvidenceConflictSeverityScoreRow",
        "CandidateDecisionEvidenceConflictSeverityScoreReport",
    ),
)

ROW_REASON_CODE_SEQUENCE = (
    "conflicting_claim_count_block",
    "conflicting_claim_count_watch",
    "highest_conflict_severity_block",
    "highest_conflict_severity_watch",
    "primary_evidence_alignment_block",
    "primary_evidence_alignment_watch",
    "independent_public_evidence_block",
    "independent_public_evidence_watch",
    "recency_skew_block",
    "recency_skew_watch",
    "resolution_rule_ambiguity_block",
    "resolution_rule_ambiguity_watch",
    "evidence_conflict_severity_score_block",
    "evidence_conflict_severity_score_watch",
    "evidence_conflict_severity_pass",
)
BLOCK_REASON_CODES = frozenset(
    (
        "conflicting_claim_count_block",
        "highest_conflict_severity_block",
        "primary_evidence_alignment_block",
        "independent_public_evidence_block",
        "recency_skew_block",
        "resolution_rule_ambiguity_block",
        "evidence_conflict_severity_score_block",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "conflicting_claim_count_watch",
        "highest_conflict_severity_watch",
        "primary_evidence_alignment_watch",
        "independent_public_evidence_watch",
        "recency_skew_watch",
        "resolution_rule_ambiguity_watch",
        "evidence_conflict_severity_score_watch",
    ),
)
REPORT_REASON_CODE_SEQUENCE = (
    "evidence_conflict_severity_report_pass",
    "evidence_conflict_severity_report_watch",
    "evidence_conflict_severity_report_block",
    "evidence_conflict_severity_report_empty",
    *ROW_REASON_CODE_SEQUENCE,
)

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "public_status",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_evidence_conflict_severity_score",
        "min_evidence_conflict_severity_score",
        "average_evidence_conflict_severity_score",
        "max_conflicting_claim_count",
        "max_highest_conflict_severity_score",
        "rows",
        "evidence_batch_versions",
        "reason_codes",
        "report_sha256",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "rank",
        "redacted_candidate_ref",
        "observed_at",
        "conflicting_claim_count",
        "highest_conflict_severity_score",
        "primary_evidence_alignment_score",
        "independent_public_evidence_count",
        "recency_skew_score",
        "resolution_rule_ambiguity_score",
        "claim_count_pressure",
        "independent_public_evidence_score",
        "primary_alignment_gap_score",
        "evidence_conflict_severity_score",
        "public_status",
        "reason_codes",
        "evidence_batch_version",
        "max_pass_evidence_conflict_severity_score",
        "max_watch_evidence_conflict_severity_score",
        "max_pass_conflicting_claim_count",
        "max_watch_conflicting_claim_count",
        "max_conflicting_claim_count_for_score",
        "min_pass_independent_public_evidence_count",
        "min_watch_independent_public_evidence_count",
        "min_pass_primary_evidence_alignment_score",
        "min_watch_primary_evidence_alignment_score",
        "max_pass_recency_skew_score",
        "max_watch_recency_skew_score",
        "max_pass_resolution_rule_ambiguity_score",
        "max_watch_resolution_rule_ambiguity_score",
        "conflict_severity_weight",
        "claim_count_weight",
        "primary_alignment_gap_weight",
        "independence_gap_weight",
        "recency_skew_weight",
        "rule_ambiguity_weight",
        "row_sha256",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "".join(("candidate", "_id")),
        "".join(("raw", "_candidate")),
        "".join(("market", "_id")),
        "".join(("market", "_slug")),
        "question",
        "".join(("source", "_ref")),
        "".join(("source", "_url")),
        "".join(("source", "_text")),
        "".join(("raw", "_text")),
        "".join(("http", "://")),
        "".join(("https", "://")),
        "".join(("ds", "n")),
        "".join(("ta", "ble")),
        "".join(("to", "ken")),
        "".join(("sec", "ret")),
        "".join(("au", "th")),
        "".join(("wal", "let")),
        "".join(("or", "der")),
        "".join(("tr", "ade")),
        "".join(("posi", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("recomm", "endation")),
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class CandidateDecisionEvidenceConflictSeverityScoreConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_EVIDENCE_CONFLICT_SEVERITY_SCORE_VERSION
    )
    max_pass_evidence_conflict_severity_score: Decimal = Decimal("0.250000")
    max_watch_evidence_conflict_severity_score: Decimal = Decimal("0.650000")
    max_pass_conflicting_claim_count: Decimal = Decimal("1.000000")
    max_watch_conflicting_claim_count: Decimal = Decimal("3.000000")
    max_conflicting_claim_count_for_score: Decimal = Decimal("5.000000")
    min_pass_independent_public_evidence_count: Decimal = Decimal("3.000000")
    min_watch_independent_public_evidence_count: Decimal = Decimal("1.000000")
    min_pass_primary_evidence_alignment_score: Decimal = Decimal("0.750000")
    min_watch_primary_evidence_alignment_score: Decimal = Decimal("0.500000")
    max_pass_recency_skew_score: Decimal = Decimal("0.200000")
    max_watch_recency_skew_score: Decimal = Decimal("0.600000")
    max_pass_resolution_rule_ambiguity_score: Decimal = Decimal("0.250000")
    max_watch_resolution_rule_ambiguity_score: Decimal = Decimal("0.600000")
    conflict_severity_weight: Decimal = Decimal("0.350000")
    claim_count_weight: Decimal = Decimal("0.200000")
    primary_alignment_gap_weight: Decimal = Decimal("0.200000")
    independence_gap_weight: Decimal = Decimal("0.150000")
    recency_skew_weight: Decimal = Decimal("0.050000")
    rule_ambiguity_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionEvidenceConflictSeverityScoreConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVIDENCE_CONFLICT_SEVERITY_SCORE_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_conflicting_claim_count",
            "max_watch_conflicting_claim_count",
            "max_conflicting_claim_count_for_score",
            "min_pass_independent_public_evidence_count",
            "min_watch_independent_public_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_evidence_conflict_severity_score",
            "max_watch_evidence_conflict_severity_score",
            "min_pass_primary_evidence_alignment_score",
            "min_watch_primary_evidence_alignment_score",
            "max_pass_recency_skew_score",
            "max_watch_recency_skew_score",
            "max_pass_resolution_rule_ambiguity_score",
            "max_watch_resolution_rule_ambiguity_score",
            "conflict_severity_weight",
            "claim_count_weight",
            "primary_alignment_gap_weight",
            "independence_gap_weight",
            "recency_skew_weight",
            "rule_ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionEvidenceConflictSeverityFacts(_FinalPublicDataclass):
    redacted_candidate_ref: str
    observed_at: datetime
    conflicting_claim_count: Decimal
    highest_conflict_severity_score: Decimal
    primary_evidence_alignment_score: Decimal
    independent_public_evidence_count: Decimal
    recency_skew_score: Decimal
    resolution_rule_ambiguity_score: Decimal
    evidence_batch_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionEvidenceConflictSeverityFacts, "facts")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "conflicting_claim_count",
            "independent_public_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_conflict_severity_score",
            "primary_evidence_alignment_score",
            "recency_skew_score",
            "resolution_rule_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_batch_version",
            _require_public_string("evidence_batch_version", self.evidence_batch_version),
        )
        _require_hard_flags("facts", self)
        _reject_unsafe_public_payload("facts", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionEvidenceConflictSeverityScoreRow(_FinalPublicDataclass):
    rank: Decimal
    redacted_candidate_ref: str
    observed_at: datetime
    conflicting_claim_count: Decimal
    highest_conflict_severity_score: Decimal
    primary_evidence_alignment_score: Decimal
    independent_public_evidence_count: Decimal
    recency_skew_score: Decimal
    resolution_rule_ambiguity_score: Decimal
    claim_count_pressure: Decimal
    independent_public_evidence_score: Decimal
    primary_alignment_gap_score: Decimal
    evidence_conflict_severity_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    evidence_batch_version: str
    max_pass_evidence_conflict_severity_score: Decimal = Decimal("0.250000")
    max_watch_evidence_conflict_severity_score: Decimal = Decimal("0.650000")
    max_pass_conflicting_claim_count: Decimal = Decimal("1.000000")
    max_watch_conflicting_claim_count: Decimal = Decimal("3.000000")
    max_conflicting_claim_count_for_score: Decimal = Decimal("5.000000")
    min_pass_independent_public_evidence_count: Decimal = Decimal("3.000000")
    min_watch_independent_public_evidence_count: Decimal = Decimal("1.000000")
    min_pass_primary_evidence_alignment_score: Decimal = Decimal("0.750000")
    min_watch_primary_evidence_alignment_score: Decimal = Decimal("0.500000")
    max_pass_recency_skew_score: Decimal = Decimal("0.200000")
    max_watch_recency_skew_score: Decimal = Decimal("0.600000")
    max_pass_resolution_rule_ambiguity_score: Decimal = Decimal("0.250000")
    max_watch_resolution_rule_ambiguity_score: Decimal = Decimal("0.600000")
    conflict_severity_weight: Decimal = Decimal("0.350000")
    claim_count_weight: Decimal = Decimal("0.200000")
    primary_alignment_gap_weight: Decimal = Decimal("0.200000")
    independence_gap_weight: Decimal = Decimal("0.150000")
    recency_skew_weight: Decimal = Decimal("0.050000")
    rule_ambiguity_weight: Decimal = Decimal("0.050000")
    row_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionEvidenceConflictSeverityScoreRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "conflicting_claim_count",
            "independent_public_evidence_count",
            "max_pass_conflicting_claim_count",
            "max_watch_conflicting_claim_count",
            "max_conflicting_claim_count_for_score",
            "min_pass_independent_public_evidence_count",
            "min_watch_independent_public_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_conflict_severity_score",
            "primary_evidence_alignment_score",
            "recency_skew_score",
            "resolution_rule_ambiguity_score",
            "claim_count_pressure",
            "independent_public_evidence_score",
            "primary_alignment_gap_score",
            "evidence_conflict_severity_score",
            "max_pass_evidence_conflict_severity_score",
            "max_watch_evidence_conflict_severity_score",
            "min_pass_primary_evidence_alignment_score",
            "min_watch_primary_evidence_alignment_score",
            "max_pass_recency_skew_score",
            "max_watch_recency_skew_score",
            "max_pass_resolution_rule_ambiguity_score",
            "max_watch_resolution_rule_ambiguity_score",
            "conflict_severity_weight",
            "claim_count_weight",
            "primary_alignment_gap_weight",
            "independence_gap_weight",
            "recency_skew_weight",
            "rule_ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "evidence_batch_version",
            _require_public_string("evidence_batch_version", self.evidence_batch_version),
        )
        object.__setattr__(self, "row_sha256", _normalize_optional_sha256("row_sha256", self.row_sha256))
        object.__setattr__(
            self,
            "derived_validation_digest",
            _normalize_optional_sha256(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        _validate_row(self)
        if self.row_sha256 == "":
            object.__setattr__(self, "row_sha256", _row_sha256(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        _validate_row_digests(self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceConflictSeverityScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_evidence_conflict_severity_score: Decimal
    min_evidence_conflict_severity_score: Decimal
    average_evidence_conflict_severity_score: Decimal
    max_conflicting_claim_count: Decimal
    max_highest_conflict_severity_score: Decimal
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...]
    evidence_batch_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionEvidenceConflictSeverityScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_public_status("public_status", self.public_status)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_conflicting_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_conflict_severity_score",
            "min_evidence_conflict_severity_score",
            "average_evidence_conflict_severity_score",
            "max_highest_conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "evidence_batch_versions",
            _require_evidence_batch_versions(self.evidence_batch_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "report_sha256",
            _normalize_optional_sha256("report_sha256", self.report_sha256),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _normalize_optional_sha256(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        if self.report_sha256 == "":
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _validate_report_digests(self)


def build_candidate_decision_evidence_conflict_severity_score(
    facts: Iterable[CandidateDecisionEvidenceConflictSeverityFacts],
    *,
    config: CandidateDecisionEvidenceConflictSeverityScoreConfig | None = None,
    generated_at: datetime,
) -> CandidateDecisionEvidenceConflictSeverityScoreReport:
    cfg = config or CandidateDecisionEvidenceConflictSeverityScoreConfig()
    if type(cfg) is not CandidateDecisionEvidenceConflictSeverityScoreConfig:
        raise ValueError("config must be exactly CandidateDecisionEvidenceConflictSeverityScoreConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_facts(facts)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    ranked_rows = tuple(
        _row_from_values(rank=index, values=values)
        for index, values in enumerate(
            sorted(
                (_row_values(item, cfg) for item in normalized),
                key=_row_values_sort_key,
            ),
            start=1,
        )
    )
    return CandidateDecisionEvidenceConflictSeverityScoreReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        public_status=_report_status(ranked_rows),
        candidate_count=_count_decimal(len(ranked_rows)),
        pass_count=_status_count(ranked_rows, STATUS_PASS),
        watch_count=_status_count(ranked_rows, STATUS_WATCH),
        block_count=_status_count(ranked_rows, STATUS_BLOCK),
        max_evidence_conflict_severity_score=_max_severity_score(ranked_rows),
        min_evidence_conflict_severity_score=_min_severity_score(ranked_rows),
        average_evidence_conflict_severity_score=_average_severity_score(ranked_rows),
        max_conflicting_claim_count=_max_conflicting_claim_count(ranked_rows),
        max_highest_conflict_severity_score=_max_highest_conflict_severity_score(
            ranked_rows,
        ),
        rows=ranked_rows,
        evidence_batch_versions=tuple(
            sorted((row.redacted_candidate_ref, row.evidence_batch_version) for row in ranked_rows),
        ),
        reason_codes=_report_reason_codes(ranked_rows),
    )


def validate_candidate_decision_evidence_conflict_severity_score_report(
    report: CandidateDecisionEvidenceConflictSeverityScoreReport,
) -> bool:
    if type(report) is not CandidateDecisionEvidenceConflictSeverityScoreReport:
        raise ValueError("report must be exactly CandidateDecisionEvidenceConflictSeverityScoreReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", _payload_value(report))
    _validate_report(report)
    _validate_report_digests(report)
    return True


def candidate_decision_evidence_conflict_severity_score_payload(
    report: CandidateDecisionEvidenceConflictSeverityScoreReport,
) -> dict[str, Any]:
    validate_candidate_decision_evidence_conflict_severity_score_report(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_evidence_conflict_severity_score_payload(payload)
    return payload


def validate_candidate_decision_evidence_conflict_severity_score_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_payload_numbers(payload)
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_shape(payload)
    _require_payload_hard_flags(payload)
    _require_payload_digests(payload)
    validate_candidate_decision_evidence_conflict_severity_score_report(
        _report_from_payload(payload),
    )
    return True


def _row_values(
    item: CandidateDecisionEvidenceConflictSeverityFacts,
    config: CandidateDecisionEvidenceConflictSeverityScoreConfig,
) -> dict[str, object]:
    claim_count_pressure = _coverage_score(
        item.conflicting_claim_count,
        config.max_conflicting_claim_count_for_score,
    )
    independent_public_evidence_score = _coverage_score(
        item.independent_public_evidence_count,
        config.min_pass_independent_public_evidence_count,
    )
    primary_alignment_gap_score = _clamp_ratio(ONE - item.primary_evidence_alignment_score)
    severity_score = _evidence_conflict_severity_score(
        conflicting_claim_count=item.conflicting_claim_count,
        highest_conflict_severity_score=item.highest_conflict_severity_score,
        primary_evidence_alignment_score=item.primary_evidence_alignment_score,
        independent_public_evidence_count=item.independent_public_evidence_count,
        recency_skew_score=item.recency_skew_score,
        resolution_rule_ambiguity_score=item.resolution_rule_ambiguity_score,
        config=config,
    )
    reason_codes = _reason_codes_for_values(
        conflicting_claim_count=item.conflicting_claim_count,
        highest_conflict_severity_score=item.highest_conflict_severity_score,
        primary_evidence_alignment_score=item.primary_evidence_alignment_score,
        independent_public_evidence_count=item.independent_public_evidence_count,
        recency_skew_score=item.recency_skew_score,
        resolution_rule_ambiguity_score=item.resolution_rule_ambiguity_score,
        evidence_conflict_severity_score=severity_score,
        config=config,
    )
    return {
        "redacted_candidate_ref": item.redacted_candidate_ref,
        "observed_at": item.observed_at,
        "conflicting_claim_count": item.conflicting_claim_count,
        "highest_conflict_severity_score": item.highest_conflict_severity_score,
        "primary_evidence_alignment_score": item.primary_evidence_alignment_score,
        "independent_public_evidence_count": item.independent_public_evidence_count,
        "recency_skew_score": item.recency_skew_score,
        "resolution_rule_ambiguity_score": item.resolution_rule_ambiguity_score,
        "claim_count_pressure": claim_count_pressure,
        "independent_public_evidence_score": independent_public_evidence_score,
        "primary_alignment_gap_score": primary_alignment_gap_score,
        "evidence_conflict_severity_score": severity_score,
        "public_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "evidence_batch_version": item.evidence_batch_version,
        "max_pass_evidence_conflict_severity_score": (
            config.max_pass_evidence_conflict_severity_score
        ),
        "max_watch_evidence_conflict_severity_score": (
            config.max_watch_evidence_conflict_severity_score
        ),
        "max_pass_conflicting_claim_count": config.max_pass_conflicting_claim_count,
        "max_watch_conflicting_claim_count": config.max_watch_conflicting_claim_count,
        "max_conflicting_claim_count_for_score": (
            config.max_conflicting_claim_count_for_score
        ),
        "min_pass_independent_public_evidence_count": (
            config.min_pass_independent_public_evidence_count
        ),
        "min_watch_independent_public_evidence_count": (
            config.min_watch_independent_public_evidence_count
        ),
        "min_pass_primary_evidence_alignment_score": (
            config.min_pass_primary_evidence_alignment_score
        ),
        "min_watch_primary_evidence_alignment_score": (
            config.min_watch_primary_evidence_alignment_score
        ),
        "max_pass_recency_skew_score": config.max_pass_recency_skew_score,
        "max_watch_recency_skew_score": config.max_watch_recency_skew_score,
        "max_pass_resolution_rule_ambiguity_score": (
            config.max_pass_resolution_rule_ambiguity_score
        ),
        "max_watch_resolution_rule_ambiguity_score": (
            config.max_watch_resolution_rule_ambiguity_score
        ),
        "conflict_severity_weight": config.conflict_severity_weight,
        "claim_count_weight": config.claim_count_weight,
        "primary_alignment_gap_weight": config.primary_alignment_gap_weight,
        "independence_gap_weight": config.independence_gap_weight,
        "recency_skew_weight": config.recency_skew_weight,
        "rule_ambiguity_weight": config.rule_ambiguity_weight,
    }


def _row_values_sort_key(values: dict[str, object]) -> tuple[object, ...]:
    status = values["public_status"]
    severity_score = values["evidence_conflict_severity_score"]
    claim_count = values["conflicting_claim_count"]
    severity = values["highest_conflict_severity_score"]
    ref = values["redacted_candidate_ref"]
    observed_at = values["observed_at"]
    if type(status) is not str:
        raise ValueError("public_status must be a string")
    if type(severity_score) is not Decimal:
        raise ValueError("evidence_conflict_severity_score must be a Decimal")
    if type(claim_count) is not Decimal:
        raise ValueError("conflicting_claim_count must be a Decimal")
    if type(severity) is not Decimal:
        raise ValueError("highest_conflict_severity_score must be a Decimal")
    if type(ref) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    if type(observed_at) is not datetime:
        raise ValueError("observed_at must be a datetime")
    return (
        PUBLIC_STATUS_RANK[status],
        -severity_score,
        -claim_count,
        -severity,
        ref,
        observed_at.isoformat(),
    )


def _row_sort_key(row: CandidateDecisionEvidenceConflictSeverityScoreRow) -> tuple[object, ...]:
    return (
        PUBLIC_STATUS_RANK[row.public_status],
        -row.evidence_conflict_severity_score,
        -row.conflicting_claim_count,
        -row.highest_conflict_severity_score,
        row.redacted_candidate_ref,
        row.observed_at.isoformat(),
    )


def _row_from_values(
    *,
    rank: int,
    values: dict[str, object],
) -> CandidateDecisionEvidenceConflictSeverityScoreRow:
    return CandidateDecisionEvidenceConflictSeverityScoreRow(
        rank=_count_decimal(rank),
        redacted_candidate_ref=_value(values, "redacted_candidate_ref", str),
        observed_at=_value(values, "observed_at", datetime),
        conflicting_claim_count=_value(values, "conflicting_claim_count", Decimal),
        highest_conflict_severity_score=_value(
            values,
            "highest_conflict_severity_score",
            Decimal,
        ),
        primary_evidence_alignment_score=_value(
            values,
            "primary_evidence_alignment_score",
            Decimal,
        ),
        independent_public_evidence_count=_value(
            values,
            "independent_public_evidence_count",
            Decimal,
        ),
        recency_skew_score=_value(values, "recency_skew_score", Decimal),
        resolution_rule_ambiguity_score=_value(
            values,
            "resolution_rule_ambiguity_score",
            Decimal,
        ),
        claim_count_pressure=_value(values, "claim_count_pressure", Decimal),
        independent_public_evidence_score=_value(
            values,
            "independent_public_evidence_score",
            Decimal,
        ),
        primary_alignment_gap_score=_value(values, "primary_alignment_gap_score", Decimal),
        evidence_conflict_severity_score=_value(
            values,
            "evidence_conflict_severity_score",
            Decimal,
        ),
        public_status=_value(values, "public_status", str),
        reason_codes=_value(values, "reason_codes", tuple),
        evidence_batch_version=_value(values, "evidence_batch_version", str),
        max_pass_evidence_conflict_severity_score=_value(
            values,
            "max_pass_evidence_conflict_severity_score",
            Decimal,
        ),
        max_watch_evidence_conflict_severity_score=_value(
            values,
            "max_watch_evidence_conflict_severity_score",
            Decimal,
        ),
        max_pass_conflicting_claim_count=_value(
            values,
            "max_pass_conflicting_claim_count",
            Decimal,
        ),
        max_watch_conflicting_claim_count=_value(
            values,
            "max_watch_conflicting_claim_count",
            Decimal,
        ),
        max_conflicting_claim_count_for_score=_value(
            values,
            "max_conflicting_claim_count_for_score",
            Decimal,
        ),
        min_pass_independent_public_evidence_count=_value(
            values,
            "min_pass_independent_public_evidence_count",
            Decimal,
        ),
        min_watch_independent_public_evidence_count=_value(
            values,
            "min_watch_independent_public_evidence_count",
            Decimal,
        ),
        min_pass_primary_evidence_alignment_score=_value(
            values,
            "min_pass_primary_evidence_alignment_score",
            Decimal,
        ),
        min_watch_primary_evidence_alignment_score=_value(
            values,
            "min_watch_primary_evidence_alignment_score",
            Decimal,
        ),
        max_pass_recency_skew_score=_value(values, "max_pass_recency_skew_score", Decimal),
        max_watch_recency_skew_score=_value(values, "max_watch_recency_skew_score", Decimal),
        max_pass_resolution_rule_ambiguity_score=_value(
            values,
            "max_pass_resolution_rule_ambiguity_score",
            Decimal,
        ),
        max_watch_resolution_rule_ambiguity_score=_value(
            values,
            "max_watch_resolution_rule_ambiguity_score",
            Decimal,
        ),
        conflict_severity_weight=_value(values, "conflict_severity_weight", Decimal),
        claim_count_weight=_value(values, "claim_count_weight", Decimal),
        primary_alignment_gap_weight=_value(values, "primary_alignment_gap_weight", Decimal),
        independence_gap_weight=_value(values, "independence_gap_weight", Decimal),
        recency_skew_weight=_value(values, "recency_skew_weight", Decimal),
        rule_ambiguity_weight=_value(values, "rule_ambiguity_weight", Decimal),
    )


def _value(values: dict[str, object], name: str, expected_type: type[object]) -> Any:
    value = values[name]
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")
    return value


def _normalize_facts(
    facts: Iterable[CandidateDecisionEvidenceConflictSeverityFacts],
) -> tuple[CandidateDecisionEvidenceConflictSeverityFacts, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        normalized = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not CandidateDecisionEvidenceConflictSeverityFacts:
            raise ValueError(
                "facts must contain CandidateDecisionEvidenceConflictSeverityFacts",
            )
        _require_hard_flags("facts", item)
        if item.redacted_candidate_ref in seen:
            raise ValueError("duplicate redacted_candidate_ref")
        seen.add(item.redacted_candidate_ref)
    return normalized


def _coverage_score(value: Decimal, target: Decimal) -> Decimal:
    if target <= ZERO:
        raise ValueError("target must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _evidence_conflict_severity_score(
    *,
    conflicting_claim_count: Decimal,
    highest_conflict_severity_score: Decimal,
    primary_evidence_alignment_score: Decimal,
    independent_public_evidence_count: Decimal,
    recency_skew_score: Decimal,
    resolution_rule_ambiguity_score: Decimal,
    config: CandidateDecisionEvidenceConflictSeverityScoreConfig,
) -> Decimal:
    claim_count_pressure = _coverage_score(
        conflicting_claim_count,
        config.max_conflicting_claim_count_for_score,
    )
    independent_public_evidence_score = _coverage_score(
        independent_public_evidence_count,
        config.min_pass_independent_public_evidence_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        weighted = (
            highest_conflict_severity_score * config.conflict_severity_weight
            + claim_count_pressure * config.claim_count_weight
            + (ONE - primary_evidence_alignment_score) * config.primary_alignment_gap_weight
            + (ONE - independent_public_evidence_score) * config.independence_gap_weight
            + recency_skew_score * config.recency_skew_weight
            + resolution_rule_ambiguity_score * config.rule_ambiguity_weight
        )
    return _clamp_ratio(weighted)


def _reason_codes_for_values(
    *,
    conflicting_claim_count: Decimal,
    highest_conflict_severity_score: Decimal,
    primary_evidence_alignment_score: Decimal,
    independent_public_evidence_count: Decimal,
    recency_skew_score: Decimal,
    resolution_rule_ambiguity_score: Decimal,
    evidence_conflict_severity_score: Decimal,
    config: CandidateDecisionEvidenceConflictSeverityScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if conflicting_claim_count > config.max_watch_conflicting_claim_count:
        codes.append("conflicting_claim_count_block")
    elif conflicting_claim_count > config.max_pass_conflicting_claim_count:
        codes.append("conflicting_claim_count_watch")
    if highest_conflict_severity_score > config.max_watch_evidence_conflict_severity_score:
        codes.append("highest_conflict_severity_block")
    elif highest_conflict_severity_score > config.max_pass_evidence_conflict_severity_score:
        codes.append("highest_conflict_severity_watch")
    if primary_evidence_alignment_score < config.min_watch_primary_evidence_alignment_score:
        codes.append("primary_evidence_alignment_block")
    elif primary_evidence_alignment_score < config.min_pass_primary_evidence_alignment_score:
        codes.append("primary_evidence_alignment_watch")
    if independent_public_evidence_count < config.min_watch_independent_public_evidence_count:
        codes.append("independent_public_evidence_block")
    elif independent_public_evidence_count < config.min_pass_independent_public_evidence_count:
        codes.append("independent_public_evidence_watch")
    if recency_skew_score > config.max_watch_recency_skew_score:
        codes.append("recency_skew_block")
    elif recency_skew_score > config.max_pass_recency_skew_score:
        codes.append("recency_skew_watch")
    if resolution_rule_ambiguity_score > config.max_watch_resolution_rule_ambiguity_score:
        codes.append("resolution_rule_ambiguity_block")
    elif resolution_rule_ambiguity_score > config.max_pass_resolution_rule_ambiguity_score:
        codes.append("resolution_rule_ambiguity_watch")
    if evidence_conflict_severity_score > config.max_watch_evidence_conflict_severity_score:
        codes.append("evidence_conflict_severity_score_block")
    elif evidence_conflict_severity_score > config.max_pass_evidence_conflict_severity_score:
        codes.append("evidence_conflict_severity_score_watch")
    if not codes:
        return ("evidence_conflict_severity_pass",)
    return tuple(codes)


def _config_from_row(
    row: CandidateDecisionEvidenceConflictSeverityScoreRow,
) -> CandidateDecisionEvidenceConflictSeverityScoreConfig:
    return CandidateDecisionEvidenceConflictSeverityScoreConfig(
        max_pass_evidence_conflict_severity_score=(
            row.max_pass_evidence_conflict_severity_score
        ),
        max_watch_evidence_conflict_severity_score=(
            row.max_watch_evidence_conflict_severity_score
        ),
        max_pass_conflicting_claim_count=row.max_pass_conflicting_claim_count,
        max_watch_conflicting_claim_count=row.max_watch_conflicting_claim_count,
        max_conflicting_claim_count_for_score=row.max_conflicting_claim_count_for_score,
        min_pass_independent_public_evidence_count=(
            row.min_pass_independent_public_evidence_count
        ),
        min_watch_independent_public_evidence_count=(
            row.min_watch_independent_public_evidence_count
        ),
        min_pass_primary_evidence_alignment_score=(
            row.min_pass_primary_evidence_alignment_score
        ),
        min_watch_primary_evidence_alignment_score=(
            row.min_watch_primary_evidence_alignment_score
        ),
        max_pass_recency_skew_score=row.max_pass_recency_skew_score,
        max_watch_recency_skew_score=row.max_watch_recency_skew_score,
        max_pass_resolution_rule_ambiguity_score=(
            row.max_pass_resolution_rule_ambiguity_score
        ),
        max_watch_resolution_rule_ambiguity_score=(
            row.max_watch_resolution_rule_ambiguity_score
        ),
        conflict_severity_weight=row.conflict_severity_weight,
        claim_count_weight=row.claim_count_weight,
        primary_alignment_gap_weight=row.primary_alignment_gap_weight,
        independence_gap_weight=row.independence_gap_weight,
        recency_skew_weight=row.recency_skew_weight,
        rule_ambiguity_weight=row.rule_ambiguity_weight,
    )


def _validate_row(row: CandidateDecisionEvidenceConflictSeverityScoreRow) -> None:
    config = _config_from_row(row)
    expected_claim_pressure = _coverage_score(
        row.conflicting_claim_count,
        row.max_conflicting_claim_count_for_score,
    )
    expected_independence_score = _coverage_score(
        row.independent_public_evidence_count,
        row.min_pass_independent_public_evidence_count,
    )
    expected_alignment_gap = _clamp_ratio(ONE - row.primary_evidence_alignment_score)
    expected_score = _evidence_conflict_severity_score(
        conflicting_claim_count=row.conflicting_claim_count,
        highest_conflict_severity_score=row.highest_conflict_severity_score,
        primary_evidence_alignment_score=row.primary_evidence_alignment_score,
        independent_public_evidence_count=row.independent_public_evidence_count,
        recency_skew_score=row.recency_skew_score,
        resolution_rule_ambiguity_score=row.resolution_rule_ambiguity_score,
        config=config,
    )
    expected_reasons = _reason_codes_for_values(
        conflicting_claim_count=row.conflicting_claim_count,
        highest_conflict_severity_score=row.highest_conflict_severity_score,
        primary_evidence_alignment_score=row.primary_evidence_alignment_score,
        independent_public_evidence_count=row.independent_public_evidence_count,
        recency_skew_score=row.recency_skew_score,
        resolution_rule_ambiguity_score=row.resolution_rule_ambiguity_score,
        evidence_conflict_severity_score=row.evidence_conflict_severity_score,
        config=config,
    )
    if row.claim_count_pressure != expected_claim_pressure:
        raise ValueError("claim_count_pressure must match facts")
    if row.independent_public_evidence_score != expected_independence_score:
        raise ValueError("independent_public_evidence_score must match facts")
    if row.primary_alignment_gap_score != expected_alignment_gap:
        raise ValueError("primary_alignment_gap_score must match facts")
    if row.evidence_conflict_severity_score != expected_score:
        raise ValueError("evidence_conflict_severity_score must match facts")
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match facts")
    if row.public_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("public_status must match reason_codes")


def _validate_row_digests(row: CandidateDecisionEvidenceConflictSeverityScoreRow) -> None:
    if row.row_sha256 != _row_sha256(row):
        raise ValueError("row_sha256 must match row fields")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("evidence_conflict_severity_pass",):
        return STATUS_PASS
    if any(code in BLOCK_REASON_CODES for code in reason_codes):
        return STATUS_BLOCK
    if any(code in WATCH_REASON_CODES for code in reason_codes):
        return STATUS_WATCH
    raise ValueError("reason_codes must imply pass, watch, or block")


def _report_status(rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("evidence_conflict_severity_report_empty",)
    status = _report_status(rows)
    codes = [f"evidence_conflict_severity_report_{status}"]
    row_code_set = {code for row in rows for code in row.reason_codes}
    for code in ROW_REASON_CODE_SEQUENCE:
        if code != "evidence_conflict_severity_pass" and code in row_code_set:
            codes.append(code)
    return tuple(codes)


def _validate_report(report: CandidateDecisionEvidenceConflictSeverityScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.public_status != _report_status(rows):
        raise ValueError("public_status must match rows")
    if report.max_evidence_conflict_severity_score != _max_severity_score(rows):
        raise ValueError("max_evidence_conflict_severity_score must match rows")
    if report.min_evidence_conflict_severity_score != _min_severity_score(rows):
        raise ValueError("min_evidence_conflict_severity_score must match rows")
    if report.average_evidence_conflict_severity_score != _average_severity_score(rows):
        raise ValueError("average_evidence_conflict_severity_score must match rows")
    if report.max_conflicting_claim_count != _max_conflicting_claim_count(rows):
        raise ValueError("max_conflicting_claim_count must match rows")
    if report.max_highest_conflict_severity_score != (
        _max_highest_conflict_severity_score(rows)
    ):
        raise ValueError("max_highest_conflict_severity_score must match rows")
    expected_versions = tuple(
        sorted((row.redacted_candidate_ref, row.evidence_batch_version) for row in rows),
    )
    if report.evidence_batch_versions != expected_versions:
        raise ValueError("evidence_batch_versions must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_digests(report: CandidateDecisionEvidenceConflictSeverityScoreReport) -> None:
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _status_count(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _max_severity_score(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.evidence_conflict_severity_score for row in rows)


def _min_severity_score(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.evidence_conflict_severity_score for row in rows)


def _average_severity_score(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((row.evidence_conflict_severity_score for row in rows), ZERO)
            / _count_decimal(len(rows)),
        )


def _max_conflicting_claim_count(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.conflicting_claim_count for row in rows)


def _max_highest_conflict_severity_score(
    rows: tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.highest_conflict_severity_score for row in rows)


def _validate_config(config: CandidateDecisionEvidenceConflictSeverityScoreConfig) -> None:
    if (
        config.max_pass_evidence_conflict_severity_score
        > config.max_watch_evidence_conflict_severity_score
    ):
        raise ValueError("max_pass_evidence_conflict_severity_score must be at most watch")
    if config.max_pass_conflicting_claim_count > config.max_watch_conflicting_claim_count:
        raise ValueError("max_pass_conflicting_claim_count must be at most watch")
    if config.max_watch_conflicting_claim_count > config.max_conflicting_claim_count_for_score:
        raise ValueError("max_watch_conflicting_claim_count must be at most scoring max")
    if config.max_conflicting_claim_count_for_score <= ZERO:
        raise ValueError("max_conflicting_claim_count_for_score must be positive")
    if (
        config.min_pass_independent_public_evidence_count
        < config.min_watch_independent_public_evidence_count
    ):
        raise ValueError("min_pass_independent_public_evidence_count must be at least watch")
    if config.min_watch_independent_public_evidence_count <= ZERO:
        raise ValueError("min_watch_independent_public_evidence_count must be positive")
    if config.min_pass_independent_public_evidence_count <= ZERO:
        raise ValueError("min_pass_independent_public_evidence_count must be positive")
    if (
        config.min_pass_primary_evidence_alignment_score
        < config.min_watch_primary_evidence_alignment_score
    ):
        raise ValueError("min_pass_primary_evidence_alignment_score must be at least watch")
    if config.max_pass_recency_skew_score > config.max_watch_recency_skew_score:
        raise ValueError("max_pass_recency_skew_score must be at most watch")
    if (
        config.max_pass_resolution_rule_ambiguity_score
        > config.max_watch_resolution_rule_ambiguity_score
    ):
        raise ValueError("max_pass_resolution_rule_ambiguity_score must be at most watch")
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.conflict_severity_weight
            + config.claim_count_weight
            + config.primary_alignment_gap_weight
            + config.independence_gap_weight
            + config.recency_skew_weight
            + config.rule_ambiguity_weight
        )
    if weight_total != ONE:
        raise ValueError("weights must sum to 1.000000")


def _require_rows(
    rows: object,
) -> tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not CandidateDecisionEvidenceConflictSeverityScoreRow:
            raise ValueError("rows must contain CandidateDecisionEvidenceConflictSeverityScoreRow")
        _require_hard_flags("row", row)
        _validate_row(row)
        _validate_row_digests(row)
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(row.redacted_candidate_ref)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted highest severity first")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be contiguous")
    return rows


def _require_evidence_batch_versions(values: object) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("evidence_batch_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("evidence_batch_versions entries must be pairs")
        redacted_candidate_ref, evidence_batch_version = value
        normalized.append(
            (
                _require_redacted_candidate_ref(
                    "evidence_batch_versions redacted_candidate_ref",
                    redacted_candidate_ref,
                ),
                _require_public_string(
                    "evidence_batch_versions evidence_batch_version",
                    evidence_batch_version,
                ),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("evidence_batch_versions must be sorted")
    return result


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        for field_name in ("paper_only", "report_only", "readonly"):
            if row.get(field_name) is not True:
                raise ValueError(f"payload row {field_name} must be True")


def _require_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        _require_payload_keys("payload row", row, ROW_PAYLOAD_KEYS)


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    keys: frozenset[str],
) -> None:
    if frozenset(payload) != keys:
        raise ValueError(f"{label} keys must match")


def _report_from_payload(
    payload: dict[str, Any],
) -> CandidateDecisionEvidenceConflictSeverityScoreReport:
    return CandidateDecisionEvidenceConflictSeverityScoreReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        public_status=_payload_public_status(payload, "public_status"),
        candidate_count=_payload_decimal(payload, "candidate_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        block_count=_payload_decimal(payload, "block_count"),
        max_evidence_conflict_severity_score=_payload_decimal(
            payload,
            "max_evidence_conflict_severity_score",
        ),
        min_evidence_conflict_severity_score=_payload_decimal(
            payload,
            "min_evidence_conflict_severity_score",
        ),
        average_evidence_conflict_severity_score=_payload_decimal(
            payload,
            "average_evidence_conflict_severity_score",
        ),
        max_conflicting_claim_count=_payload_decimal(
            payload,
            "max_conflicting_claim_count",
        ),
        max_highest_conflict_severity_score=_payload_decimal(
            payload,
            "max_highest_conflict_severity_score",
        ),
        rows=_payload_rows(payload),
        evidence_batch_versions=_payload_evidence_batch_versions(payload),
        reason_codes=_payload_reason_codes(
            payload,
            "reason_codes",
            REPORT_REASON_CODE_SEQUENCE,
        ),
        report_sha256=_payload_sha256(payload, "report_sha256"),
        derived_validation_digest=_payload_sha256(payload, "derived_validation_digest"),
        paper_only=_payload_bool(payload, "paper_only"),
        report_only=_payload_bool(payload, "report_only"),
        readonly=_payload_bool(payload, "readonly"),
    )


def _payload_rows(
    payload: dict[str, Any],
) -> tuple[CandidateDecisionEvidenceConflictSeverityScoreRow, ...]:
    values = payload.get("rows")
    if type(values) is not list:
        raise ValueError("payload rows must be a list")
    return tuple(_row_from_payload(row) for row in values)


def _row_from_payload(
    payload: dict[str, Any],
) -> CandidateDecisionEvidenceConflictSeverityScoreRow:
    _require_payload_hash(payload, "row", "row_sha256")
    return CandidateDecisionEvidenceConflictSeverityScoreRow(
        rank=_payload_decimal(payload, "rank"),
        redacted_candidate_ref=_payload_redacted_candidate_ref(
            payload,
            "redacted_candidate_ref",
        ),
        observed_at=_payload_datetime(payload, "observed_at"),
        conflicting_claim_count=_payload_decimal(payload, "conflicting_claim_count"),
        highest_conflict_severity_score=_payload_decimal(
            payload,
            "highest_conflict_severity_score",
        ),
        primary_evidence_alignment_score=_payload_decimal(
            payload,
            "primary_evidence_alignment_score",
        ),
        independent_public_evidence_count=_payload_decimal(
            payload,
            "independent_public_evidence_count",
        ),
        recency_skew_score=_payload_decimal(payload, "recency_skew_score"),
        resolution_rule_ambiguity_score=_payload_decimal(
            payload,
            "resolution_rule_ambiguity_score",
        ),
        claim_count_pressure=_payload_decimal(payload, "claim_count_pressure"),
        independent_public_evidence_score=_payload_decimal(
            payload,
            "independent_public_evidence_score",
        ),
        primary_alignment_gap_score=_payload_decimal(payload, "primary_alignment_gap_score"),
        evidence_conflict_severity_score=_payload_decimal(
            payload,
            "evidence_conflict_severity_score",
        ),
        public_status=_payload_public_status(payload, "public_status"),
        reason_codes=_payload_reason_codes(
            payload,
            "reason_codes",
            ROW_REASON_CODE_SEQUENCE,
        ),
        evidence_batch_version=_payload_string(payload, "evidence_batch_version"),
        max_pass_evidence_conflict_severity_score=_payload_decimal(
            payload,
            "max_pass_evidence_conflict_severity_score",
        ),
        max_watch_evidence_conflict_severity_score=_payload_decimal(
            payload,
            "max_watch_evidence_conflict_severity_score",
        ),
        max_pass_conflicting_claim_count=_payload_decimal(
            payload,
            "max_pass_conflicting_claim_count",
        ),
        max_watch_conflicting_claim_count=_payload_decimal(
            payload,
            "max_watch_conflicting_claim_count",
        ),
        max_conflicting_claim_count_for_score=_payload_decimal(
            payload,
            "max_conflicting_claim_count_for_score",
        ),
        min_pass_independent_public_evidence_count=_payload_decimal(
            payload,
            "min_pass_independent_public_evidence_count",
        ),
        min_watch_independent_public_evidence_count=_payload_decimal(
            payload,
            "min_watch_independent_public_evidence_count",
        ),
        min_pass_primary_evidence_alignment_score=_payload_decimal(
            payload,
            "min_pass_primary_evidence_alignment_score",
        ),
        min_watch_primary_evidence_alignment_score=_payload_decimal(
            payload,
            "min_watch_primary_evidence_alignment_score",
        ),
        max_pass_recency_skew_score=_payload_decimal(
            payload,
            "max_pass_recency_skew_score",
        ),
        max_watch_recency_skew_score=_payload_decimal(
            payload,
            "max_watch_recency_skew_score",
        ),
        max_pass_resolution_rule_ambiguity_score=_payload_decimal(
            payload,
            "max_pass_resolution_rule_ambiguity_score",
        ),
        max_watch_resolution_rule_ambiguity_score=_payload_decimal(
            payload,
            "max_watch_resolution_rule_ambiguity_score",
        ),
        conflict_severity_weight=_payload_decimal(payload, "conflict_severity_weight"),
        claim_count_weight=_payload_decimal(payload, "claim_count_weight"),
        primary_alignment_gap_weight=_payload_decimal(
            payload,
            "primary_alignment_gap_weight",
        ),
        independence_gap_weight=_payload_decimal(payload, "independence_gap_weight"),
        recency_skew_weight=_payload_decimal(payload, "recency_skew_weight"),
        rule_ambiguity_weight=_payload_decimal(payload, "rule_ambiguity_weight"),
        row_sha256=_payload_sha256(payload, "row_sha256"),
        derived_validation_digest=_payload_sha256(payload, "derived_validation_digest"),
        paper_only=_payload_bool(payload, "paper_only"),
        report_only=_payload_bool(payload, "report_only"),
        readonly=_payload_bool(payload, "readonly"),
    )


def _payload_evidence_batch_versions(payload: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    values = payload.get("evidence_batch_versions")
    if type(values) is not list:
        raise ValueError("evidence_batch_versions must be a list")
    pairs: list[tuple[str, str]] = []
    for value in values:
        if type(value) is not list or len(value) != 2:
            raise ValueError("evidence_batch_versions entries must be pairs")
        pairs.append(
            (
                _require_redacted_candidate_ref("evidence_batch_versions", value[0]),
                _require_public_string("evidence_batch_versions", value[1]),
            ),
        )
    return tuple(pairs)


def _payload_reason_codes(
    payload: dict[str, Any],
    field_name: str,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    values = payload.get(field_name)
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _require_reason_codes(field_name, tuple(values), allowed_sequence)


def _payload_public_status(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_public_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_string(payload: dict[str, Any], field_name: str) -> str:
    return _require_public_string(field_name, payload.get(field_name))


def _payload_redacted_candidate_ref(payload: dict[str, Any], field_name: str) -> str:
    return _require_redacted_candidate_ref(field_name, payload.get(field_name))


def _payload_sha256(payload: dict[str, Any], field_name: str) -> str:
    return _normalize_sha256(field_name, payload.get(field_name))


def _payload_bool(payload: dict[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _payload_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    normalized = _require_decimal(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    return normalized


def _payload_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    return normalized


def _require_payload_hash(payload: dict[str, Any], label: str, hash_key: str) -> None:
    hash_value = _normalize_sha256(hash_key, payload.get(hash_key))
    hash_payload = dict(payload)
    hash_payload.pop(hash_key, None)
    hash_payload.pop("derived_validation_digest", None)
    expected = _sha256_from_payload(label, hash_payload)
    if hash_value != expected:
        raise ValueError(f"{hash_key} must match {label} payload")


def _require_payload_digests(payload: dict[str, Any]) -> None:
    _require_payload_hash(payload, "report", "report_sha256")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        _require_payload_hash(row, "row", "row_sha256")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_redacted_candidate_ref(field_name: str, value: object) -> str:
    normalized = _require_public_string(field_name, value)
    if not normalized.startswith("candidate_ref_"):
        raise ValueError(f"{field_name} must be redacted")
    return normalized


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_codes(
    field_name: str,
    values: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    allowed = frozenset(allowed_sequence)
    for value in values:
        if type(value) is not str or value not in allowed:
            raise ValueError(f"{field_name} contains unknown reason code")
        _require_public_string(field_name, value)
    return values


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _quantize_decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_payload_numbers(payload: object) -> None:
    if type(payload) is Decimal or type(payload) is float:
        raise ValueError("payload must use decimal strings")
    if type(payload) is int and type(payload) is not bool:
        raise ValueError("payload must use decimal strings")
    if type(payload) is dict:
        for item in payload.values():
            _reject_payload_numbers(item)
        return
    if type(payload) is list:
        for item in payload:
            _reject_payload_numbers(item)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is list:
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str:
        _reject_unsafe_public_string(label, payload)
        return
    if type(payload) in (bool,) or payload is None:
        return
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public surface in {label}")


def _normalize_optional_sha256(field_name: str, value: object) -> str:
    if value == "":
        return ""
    return _normalize_sha256(field_name, value)


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _row_sha256(row: CandidateDecisionEvidenceConflictSeverityScoreRow) -> str:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    payload.pop("row_sha256", None)
    payload.pop("derived_validation_digest", None)
    return _sha256_from_payload("row", payload)


def _row_derived_validation_digest(
    row: CandidateDecisionEvidenceConflictSeverityScoreRow,
) -> str:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _sha256_from_payload("row_validation", payload)


def _report_sha256(report: CandidateDecisionEvidenceConflictSeverityScoreReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("report_sha256", None)
    payload.pop("derived_validation_digest", None)
    return _sha256_from_payload("report", payload)


def _report_derived_validation_digest(
    report: CandidateDecisionEvidenceConflictSeverityScoreReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _sha256_from_payload("report_validation", payload)


def _sha256_from_payload(label: str, payload: object) -> str:
    _reject_unsafe_public_payload(label, payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
