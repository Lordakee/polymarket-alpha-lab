"""Pure Phase 1 candidate conflict confidence scoring."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CANDIDATE_DECISION_CONFLICT_RESOLUTION_SCORE_VERSION = (
    "candidate-decision-conflict-resolution-score-v1"
)

SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "block"
SUPPORT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
SUPPORT_STATUS_RANK = {
    STATUS_BLOCKED: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "CandidateDecisionConflictResolutionScoreConfig",
        "CandidateDecisionConflictResolutionFacts",
        "CandidateDecisionConflictResolutionScoreRow",
        "CandidateDecisionConflictResolutionScoreReport",
    ),
)

ROW_REASON_CODE_SEQUENCE = (
    "unresolved_contradictions_blocked",
    "unresolved_contradictions_watch",
    "unresolved_contradiction_severity_blocked",
    "unresolved_contradiction_severity_watch",
    "official_hierarchy_strength_blocked",
    "official_hierarchy_strength_watch",
    "independent_corroboration_blocked",
    "independent_corroboration_watch",
    "analyst_dissent_blocked",
    "analyst_dissent_watch",
    "ambiguity_dispute_risk_blocked",
    "ambiguity_dispute_risk_watch",
    "conflict_resolution_confidence_blocked_score",
    "conflict_resolution_confidence_watch_score",
    "conflict_resolution_pass",
)
BLOCK_REASON_CODES = frozenset(
    (
        "unresolved_contradictions_blocked",
        "unresolved_contradiction_severity_blocked",
        "official_hierarchy_strength_blocked",
        "independent_corroboration_blocked",
        "analyst_dissent_blocked",
        "ambiguity_dispute_risk_blocked",
        "conflict_resolution_confidence_blocked_score",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "unresolved_contradictions_watch",
        "unresolved_contradiction_severity_watch",
        "official_hierarchy_strength_watch",
        "independent_corroboration_watch",
        "analyst_dissent_watch",
        "ambiguity_dispute_risk_watch",
        "conflict_resolution_confidence_watch_score",
    ),
)
REPORT_REASON_CODE_SEQUENCE = (
    "conflict_resolution_report_pass",
    "conflict_resolution_report_watch",
    "conflict_resolution_report_block",
    "conflict_resolution_report_empty",
    *ROW_REASON_CODE_SEQUENCE,
)
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "support_status",
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "min_conflict_resolution_confidence",
        "max_conflict_resolution_confidence",
        "average_conflict_resolution_confidence",
        "max_unresolved_contradiction_count",
        "max_unresolved_contradiction_severity",
        "max_analyst_dissent_score",
        "max_ambiguity_dispute_risk_score",
        "rows",
        "fact_set_versions",
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
        "unresolved_contradiction_count",
        "highest_unresolved_contradiction_severity",
        "official_hierarchy_strength",
        "independent_corroboration_count",
        "analyst_dissent_score",
        "ambiguity_dispute_risk_score",
        "contradiction_count_pressure",
        "independent_corroboration_score",
        "conflict_resolution_confidence",
        "support_status",
        "reason_codes",
        "fact_set_version",
        "max_pass_unresolved_contradiction_count",
        "max_watch_unresolved_contradiction_count",
        "max_unresolved_contradiction_count_for_score",
        "max_pass_unresolved_contradiction_severity",
        "max_watch_unresolved_contradiction_severity",
        "min_pass_official_hierarchy_strength",
        "min_watch_official_hierarchy_strength",
        "min_pass_independent_corroboration_count",
        "min_watch_independent_corroboration_count",
        "max_pass_analyst_dissent_score",
        "max_watch_analyst_dissent_score",
        "max_pass_ambiguity_dispute_risk_score",
        "max_watch_ambiguity_dispute_risk_score",
        "min_pass_conflict_resolution_confidence",
        "min_watch_conflict_resolution_confidence",
        "official_hierarchy_weight",
        "independent_corroboration_weight",
        "contradiction_count_weight",
        "contradiction_severity_weight",
        "analyst_consensus_weight",
        "low_ambiguity_weight",
        "row_sha256",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "".join(("acc", "ount")),
        "".join(("au", "th")),
        "".join(("b", "uy")),
        "".join(("lin", "k")),
        "".join(("li", "ve")),
        "".join(("mar", "ket")),
        "".join(("or", "der")),
        "".join(("posi", "tion")),
        "".join(("quest", "ion")),
        "".join(("ra", "w")),
        "".join(("recommen", "dation")),
        "".join(("s", "ell")),
        "".join(("siz", "ing")),
        "".join(("sl", "ug")),
        "".join(("so", "urce")),
        "".join(("te", "xt")),
        "".join(("tr", "ade")),
        "".join(("ur", "i")),
        "".join(("ur", "l")),
        "".join(("wal", "let")),
    ),
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "".join(("api", "_key")),
        "".join(("private", "_key")),
        "".join(("raw", "_text")),
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class CandidateDecisionConflictResolutionScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CANDIDATE_DECISION_CONFLICT_RESOLUTION_SCORE_VERSION
    max_pass_unresolved_contradiction_count: Decimal = Decimal("1.000000")
    max_watch_unresolved_contradiction_count: Decimal = Decimal("3.000000")
    max_unresolved_contradiction_count_for_score: Decimal = Decimal("5.000000")
    max_pass_unresolved_contradiction_severity: Decimal = Decimal("0.300000")
    max_watch_unresolved_contradiction_severity: Decimal = Decimal("0.700000")
    min_pass_official_hierarchy_strength: Decimal = Decimal("0.750000")
    min_watch_official_hierarchy_strength: Decimal = Decimal("0.500000")
    min_pass_independent_corroboration_count: Decimal = Decimal("3.000000")
    min_watch_independent_corroboration_count: Decimal = Decimal("1.000000")
    max_pass_analyst_dissent_score: Decimal = Decimal("0.200000")
    max_watch_analyst_dissent_score: Decimal = Decimal("0.500000")
    max_pass_ambiguity_dispute_risk_score: Decimal = Decimal("0.250000")
    max_watch_ambiguity_dispute_risk_score: Decimal = Decimal("0.600000")
    min_pass_conflict_resolution_confidence: Decimal = Decimal("0.750000")
    min_watch_conflict_resolution_confidence: Decimal = Decimal("0.500000")
    official_hierarchy_weight: Decimal = Decimal("0.300000")
    independent_corroboration_weight: Decimal = Decimal("0.250000")
    contradiction_count_weight: Decimal = Decimal("0.200000")
    contradiction_severity_weight: Decimal = Decimal("0.150000")
    analyst_consensus_weight: Decimal = Decimal("0.050000")
    low_ambiguity_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionConflictResolutionScoreConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "max_pass_unresolved_contradiction_count",
            "max_watch_unresolved_contradiction_count",
            "max_unresolved_contradiction_count_for_score",
            "min_pass_independent_corroboration_count",
            "min_watch_independent_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_unresolved_contradiction_severity",
            "max_watch_unresolved_contradiction_severity",
            "min_pass_official_hierarchy_strength",
            "min_watch_official_hierarchy_strength",
            "max_pass_analyst_dissent_score",
            "max_watch_analyst_dissent_score",
            "max_pass_ambiguity_dispute_risk_score",
            "max_watch_ambiguity_dispute_risk_score",
            "min_pass_conflict_resolution_confidence",
            "min_watch_conflict_resolution_confidence",
            "official_hierarchy_weight",
            "independent_corroboration_weight",
            "contradiction_count_weight",
            "contradiction_severity_weight",
            "analyst_consensus_weight",
            "low_ambiguity_weight",
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
class CandidateDecisionConflictResolutionFacts(_FinalPublicDataclass):
    redacted_candidate_ref: str
    observed_at: datetime
    unresolved_contradiction_count: Decimal
    highest_unresolved_contradiction_severity: Decimal
    official_hierarchy_strength: Decimal
    independent_corroboration_count: Decimal
    analyst_dissent_score: Decimal
    ambiguity_dispute_risk_score: Decimal
    fact_set_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionConflictResolutionFacts, "facts")
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
            "unresolved_contradiction_count",
            "independent_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_unresolved_contradiction_severity",
            "official_hierarchy_strength",
            "analyst_dissent_score",
            "ambiguity_dispute_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fact_set_version",
            _require_public_string("fact_set_version", self.fact_set_version),
        )
        _require_hard_flags("facts", self)
        _reject_unsafe_public_payload("facts", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionConflictResolutionScoreRow(_FinalPublicDataclass):
    rank: Decimal
    redacted_candidate_ref: str
    observed_at: datetime
    unresolved_contradiction_count: Decimal
    highest_unresolved_contradiction_severity: Decimal
    official_hierarchy_strength: Decimal
    independent_corroboration_count: Decimal
    analyst_dissent_score: Decimal
    ambiguity_dispute_risk_score: Decimal
    contradiction_count_pressure: Decimal
    independent_corroboration_score: Decimal
    conflict_resolution_confidence: Decimal
    support_status: str
    reason_codes: tuple[str, ...]
    fact_set_version: str
    max_pass_unresolved_contradiction_count: Decimal = Decimal("1.000000")
    max_watch_unresolved_contradiction_count: Decimal = Decimal("3.000000")
    max_unresolved_contradiction_count_for_score: Decimal = Decimal("5.000000")
    max_pass_unresolved_contradiction_severity: Decimal = Decimal("0.300000")
    max_watch_unresolved_contradiction_severity: Decimal = Decimal("0.700000")
    min_pass_official_hierarchy_strength: Decimal = Decimal("0.750000")
    min_watch_official_hierarchy_strength: Decimal = Decimal("0.500000")
    min_pass_independent_corroboration_count: Decimal = Decimal("3.000000")
    min_watch_independent_corroboration_count: Decimal = Decimal("1.000000")
    max_pass_analyst_dissent_score: Decimal = Decimal("0.200000")
    max_watch_analyst_dissent_score: Decimal = Decimal("0.500000")
    max_pass_ambiguity_dispute_risk_score: Decimal = Decimal("0.250000")
    max_watch_ambiguity_dispute_risk_score: Decimal = Decimal("0.600000")
    min_pass_conflict_resolution_confidence: Decimal = Decimal("0.750000")
    min_watch_conflict_resolution_confidence: Decimal = Decimal("0.500000")
    official_hierarchy_weight: Decimal = Decimal("0.300000")
    independent_corroboration_weight: Decimal = Decimal("0.250000")
    contradiction_count_weight: Decimal = Decimal("0.200000")
    contradiction_severity_weight: Decimal = Decimal("0.150000")
    analyst_consensus_weight: Decimal = Decimal("0.050000")
    low_ambiguity_weight: Decimal = Decimal("0.050000")
    row_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionConflictResolutionScoreRow, "row")
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
            "unresolved_contradiction_count",
            "independent_corroboration_count",
            "max_pass_unresolved_contradiction_count",
            "max_watch_unresolved_contradiction_count",
            "max_unresolved_contradiction_count_for_score",
            "min_pass_independent_corroboration_count",
            "min_watch_independent_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_unresolved_contradiction_severity",
            "official_hierarchy_strength",
            "analyst_dissent_score",
            "ambiguity_dispute_risk_score",
            "contradiction_count_pressure",
            "independent_corroboration_score",
            "conflict_resolution_confidence",
            "max_pass_unresolved_contradiction_severity",
            "max_watch_unresolved_contradiction_severity",
            "min_pass_official_hierarchy_strength",
            "min_watch_official_hierarchy_strength",
            "max_pass_analyst_dissent_score",
            "max_watch_analyst_dissent_score",
            "max_pass_ambiguity_dispute_risk_score",
            "max_watch_ambiguity_dispute_risk_score",
            "min_pass_conflict_resolution_confidence",
            "min_watch_conflict_resolution_confidence",
            "official_hierarchy_weight",
            "independent_corroboration_weight",
            "contradiction_count_weight",
            "contradiction_severity_weight",
            "analyst_consensus_weight",
            "low_ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_support_status("support_status", self.support_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "fact_set_version",
            _require_public_string("fact_set_version", self.fact_set_version),
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
class CandidateDecisionConflictResolutionScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    support_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_conflict_resolution_confidence: Decimal
    max_conflict_resolution_confidence: Decimal
    average_conflict_resolution_confidence: Decimal
    max_unresolved_contradiction_count: Decimal
    max_unresolved_contradiction_severity: Decimal
    max_analyst_dissent_score: Decimal
    max_ambiguity_dispute_risk_score: Decimal
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...]
    fact_set_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionConflictResolutionScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_support_status("support_status", self.support_status)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_conflict_resolution_confidence",
            "max_conflict_resolution_confidence",
            "average_conflict_resolution_confidence",
            "max_unresolved_contradiction_severity",
            "max_analyst_dissent_score",
            "max_ambiguity_dispute_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "fact_set_versions",
            _require_fact_set_versions(self.fact_set_versions),
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


def build_candidate_decision_conflict_resolution_score(
    facts: Iterable[CandidateDecisionConflictResolutionFacts],
    *,
    config: CandidateDecisionConflictResolutionScoreConfig | None = None,
    generated_at: datetime,
) -> CandidateDecisionConflictResolutionScoreReport:
    cfg = config or CandidateDecisionConflictResolutionScoreConfig()
    if type(cfg) is not CandidateDecisionConflictResolutionScoreConfig:
        raise ValueError("config must be exactly CandidateDecisionConflictResolutionScoreConfig")
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
    return CandidateDecisionConflictResolutionScoreReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        support_status=_report_status(ranked_rows),
        candidate_count=_count_decimal(len(ranked_rows)),
        pass_count=_status_count(ranked_rows, STATUS_PASS),
        watch_count=_status_count(ranked_rows, STATUS_WATCH),
        blocked_count=_status_count(ranked_rows, STATUS_BLOCKED),
        min_conflict_resolution_confidence=_min_confidence(ranked_rows),
        max_conflict_resolution_confidence=_max_confidence(ranked_rows),
        average_conflict_resolution_confidence=_average_confidence(ranked_rows),
        max_unresolved_contradiction_count=_max_unresolved_contradiction_count(ranked_rows),
        max_unresolved_contradiction_severity=_max_unresolved_contradiction_severity(
            ranked_rows,
        ),
        max_analyst_dissent_score=_max_analyst_dissent_score(ranked_rows),
        max_ambiguity_dispute_risk_score=_max_ambiguity_dispute_risk_score(ranked_rows),
        rows=ranked_rows,
        fact_set_versions=tuple(
            sorted((row.redacted_candidate_ref, row.fact_set_version) for row in ranked_rows),
        ),
        reason_codes=_report_reason_codes(ranked_rows),
    )


def validate_candidate_decision_conflict_resolution_score_report(
    report: CandidateDecisionConflictResolutionScoreReport,
) -> bool:
    if type(report) is not CandidateDecisionConflictResolutionScoreReport:
        raise ValueError("report must be exactly CandidateDecisionConflictResolutionScoreReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", _payload_value(report))
    _validate_report(report)
    _validate_report_digests(report)
    return True


def candidate_decision_conflict_resolution_score_payload(
    report: CandidateDecisionConflictResolutionScoreReport,
) -> dict[str, Any]:
    validate_candidate_decision_conflict_resolution_score_report(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_conflict_resolution_score_payload(payload)
    return payload


def validate_candidate_decision_conflict_resolution_score_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_shape(payload)
    _require_payload_hard_flags(payload)
    _require_payload_digests(payload)
    validate_candidate_decision_conflict_resolution_score_report(
        _report_from_payload(payload),
    )
    return True


def _row_values(
    item: CandidateDecisionConflictResolutionFacts,
    config: CandidateDecisionConflictResolutionScoreConfig,
) -> dict[str, object]:
    contradiction_count_pressure = _coverage_score(
        item.unresolved_contradiction_count,
        config.max_unresolved_contradiction_count_for_score,
    )
    independent_corroboration_score = _coverage_score(
        item.independent_corroboration_count,
        config.min_pass_independent_corroboration_count,
    )
    confidence = _conflict_resolution_confidence(
        unresolved_contradiction_count=item.unresolved_contradiction_count,
        highest_unresolved_contradiction_severity=(
            item.highest_unresolved_contradiction_severity
        ),
        official_hierarchy_strength=item.official_hierarchy_strength,
        independent_corroboration_count=item.independent_corroboration_count,
        analyst_dissent_score=item.analyst_dissent_score,
        ambiguity_dispute_risk_score=item.ambiguity_dispute_risk_score,
        config=config,
    )
    reason_codes = _reason_codes_for_values(
        unresolved_contradiction_count=item.unresolved_contradiction_count,
        highest_unresolved_contradiction_severity=(
            item.highest_unresolved_contradiction_severity
        ),
        official_hierarchy_strength=item.official_hierarchy_strength,
        independent_corroboration_count=item.independent_corroboration_count,
        analyst_dissent_score=item.analyst_dissent_score,
        ambiguity_dispute_risk_score=item.ambiguity_dispute_risk_score,
        conflict_resolution_confidence=confidence,
        config=config,
    )
    return {
        "redacted_candidate_ref": item.redacted_candidate_ref,
        "observed_at": item.observed_at,
        "unresolved_contradiction_count": item.unresolved_contradiction_count,
        "highest_unresolved_contradiction_severity": (
            item.highest_unresolved_contradiction_severity
        ),
        "official_hierarchy_strength": item.official_hierarchy_strength,
        "independent_corroboration_count": item.independent_corroboration_count,
        "analyst_dissent_score": item.analyst_dissent_score,
        "ambiguity_dispute_risk_score": item.ambiguity_dispute_risk_score,
        "contradiction_count_pressure": contradiction_count_pressure,
        "independent_corroboration_score": independent_corroboration_score,
        "conflict_resolution_confidence": confidence,
        "support_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "fact_set_version": item.fact_set_version,
        "max_pass_unresolved_contradiction_count": (
            config.max_pass_unresolved_contradiction_count
        ),
        "max_watch_unresolved_contradiction_count": (
            config.max_watch_unresolved_contradiction_count
        ),
        "max_unresolved_contradiction_count_for_score": (
            config.max_unresolved_contradiction_count_for_score
        ),
        "max_pass_unresolved_contradiction_severity": (
            config.max_pass_unresolved_contradiction_severity
        ),
        "max_watch_unresolved_contradiction_severity": (
            config.max_watch_unresolved_contradiction_severity
        ),
        "min_pass_official_hierarchy_strength": (
            config.min_pass_official_hierarchy_strength
        ),
        "min_watch_official_hierarchy_strength": (
            config.min_watch_official_hierarchy_strength
        ),
        "min_pass_independent_corroboration_count": (
            config.min_pass_independent_corroboration_count
        ),
        "min_watch_independent_corroboration_count": (
            config.min_watch_independent_corroboration_count
        ),
        "max_pass_analyst_dissent_score": config.max_pass_analyst_dissent_score,
        "max_watch_analyst_dissent_score": config.max_watch_analyst_dissent_score,
        "max_pass_ambiguity_dispute_risk_score": (
            config.max_pass_ambiguity_dispute_risk_score
        ),
        "max_watch_ambiguity_dispute_risk_score": (
            config.max_watch_ambiguity_dispute_risk_score
        ),
        "min_pass_conflict_resolution_confidence": (
            config.min_pass_conflict_resolution_confidence
        ),
        "min_watch_conflict_resolution_confidence": (
            config.min_watch_conflict_resolution_confidence
        ),
        "official_hierarchy_weight": config.official_hierarchy_weight,
        "independent_corroboration_weight": config.independent_corroboration_weight,
        "contradiction_count_weight": config.contradiction_count_weight,
        "contradiction_severity_weight": config.contradiction_severity_weight,
        "analyst_consensus_weight": config.analyst_consensus_weight,
        "low_ambiguity_weight": config.low_ambiguity_weight,
    }


def _row_values_sort_key(values: dict[str, object]) -> tuple[object, ...]:
    status = values["support_status"]
    if type(status) is not str:
        raise ValueError("support_status must be a string")
    confidence = values["conflict_resolution_confidence"]
    contradiction_count = values["unresolved_contradiction_count"]
    severity = values["highest_unresolved_contradiction_severity"]
    ref = values["redacted_candidate_ref"]
    observed_at = values["observed_at"]
    if type(confidence) is not Decimal:
        raise ValueError("conflict_resolution_confidence must be a Decimal")
    if type(contradiction_count) is not Decimal:
        raise ValueError("unresolved_contradiction_count must be a Decimal")
    if type(severity) is not Decimal:
        raise ValueError("highest_unresolved_contradiction_severity must be a Decimal")
    if type(ref) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    if type(observed_at) is not datetime:
        raise ValueError("observed_at must be a datetime")
    return (
        SUPPORT_STATUS_RANK[status],
        confidence,
        -contradiction_count,
        -severity,
        ref,
        observed_at.isoformat(),
    )


def _row_sort_key(row: CandidateDecisionConflictResolutionScoreRow) -> tuple[object, ...]:
    return (
        SUPPORT_STATUS_RANK[row.support_status],
        row.conflict_resolution_confidence,
        -row.unresolved_contradiction_count,
        -row.highest_unresolved_contradiction_severity,
        row.redacted_candidate_ref,
        row.observed_at.isoformat(),
    )


def _row_from_values(
    *,
    rank: int,
    values: dict[str, object],
) -> CandidateDecisionConflictResolutionScoreRow:
    return CandidateDecisionConflictResolutionScoreRow(
        rank=_count_decimal(rank),
        redacted_candidate_ref=_value(values, "redacted_candidate_ref", str),
        observed_at=_value(values, "observed_at", datetime),
        unresolved_contradiction_count=_value(
            values,
            "unresolved_contradiction_count",
            Decimal,
        ),
        highest_unresolved_contradiction_severity=_value(
            values,
            "highest_unresolved_contradiction_severity",
            Decimal,
        ),
        official_hierarchy_strength=_value(values, "official_hierarchy_strength", Decimal),
        independent_corroboration_count=_value(
            values,
            "independent_corroboration_count",
            Decimal,
        ),
        analyst_dissent_score=_value(values, "analyst_dissent_score", Decimal),
        ambiguity_dispute_risk_score=_value(values, "ambiguity_dispute_risk_score", Decimal),
        contradiction_count_pressure=_value(
            values,
            "contradiction_count_pressure",
            Decimal,
        ),
        independent_corroboration_score=_value(
            values,
            "independent_corroboration_score",
            Decimal,
        ),
        conflict_resolution_confidence=_value(
            values,
            "conflict_resolution_confidence",
            Decimal,
        ),
        support_status=_value(values, "support_status", str),
        reason_codes=_value(values, "reason_codes", tuple),
        fact_set_version=_value(values, "fact_set_version", str),
        max_pass_unresolved_contradiction_count=_value(
            values,
            "max_pass_unresolved_contradiction_count",
            Decimal,
        ),
        max_watch_unresolved_contradiction_count=_value(
            values,
            "max_watch_unresolved_contradiction_count",
            Decimal,
        ),
        max_unresolved_contradiction_count_for_score=_value(
            values,
            "max_unresolved_contradiction_count_for_score",
            Decimal,
        ),
        max_pass_unresolved_contradiction_severity=_value(
            values,
            "max_pass_unresolved_contradiction_severity",
            Decimal,
        ),
        max_watch_unresolved_contradiction_severity=_value(
            values,
            "max_watch_unresolved_contradiction_severity",
            Decimal,
        ),
        min_pass_official_hierarchy_strength=_value(
            values,
            "min_pass_official_hierarchy_strength",
            Decimal,
        ),
        min_watch_official_hierarchy_strength=_value(
            values,
            "min_watch_official_hierarchy_strength",
            Decimal,
        ),
        min_pass_independent_corroboration_count=_value(
            values,
            "min_pass_independent_corroboration_count",
            Decimal,
        ),
        min_watch_independent_corroboration_count=_value(
            values,
            "min_watch_independent_corroboration_count",
            Decimal,
        ),
        max_pass_analyst_dissent_score=_value(
            values,
            "max_pass_analyst_dissent_score",
            Decimal,
        ),
        max_watch_analyst_dissent_score=_value(
            values,
            "max_watch_analyst_dissent_score",
            Decimal,
        ),
        max_pass_ambiguity_dispute_risk_score=_value(
            values,
            "max_pass_ambiguity_dispute_risk_score",
            Decimal,
        ),
        max_watch_ambiguity_dispute_risk_score=_value(
            values,
            "max_watch_ambiguity_dispute_risk_score",
            Decimal,
        ),
        min_pass_conflict_resolution_confidence=_value(
            values,
            "min_pass_conflict_resolution_confidence",
            Decimal,
        ),
        min_watch_conflict_resolution_confidence=_value(
            values,
            "min_watch_conflict_resolution_confidence",
            Decimal,
        ),
        official_hierarchy_weight=_value(values, "official_hierarchy_weight", Decimal),
        independent_corroboration_weight=_value(
            values,
            "independent_corroboration_weight",
            Decimal,
        ),
        contradiction_count_weight=_value(values, "contradiction_count_weight", Decimal),
        contradiction_severity_weight=_value(
            values,
            "contradiction_severity_weight",
            Decimal,
        ),
        analyst_consensus_weight=_value(values, "analyst_consensus_weight", Decimal),
        low_ambiguity_weight=_value(values, "low_ambiguity_weight", Decimal),
    )


def _value(values: dict[str, object], name: str, expected_type: type[object]) -> Any:
    value = values[name]
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")
    return value


def _normalize_facts(
    facts: Iterable[CandidateDecisionConflictResolutionFacts],
) -> tuple[CandidateDecisionConflictResolutionFacts, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        normalized = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not CandidateDecisionConflictResolutionFacts:
            raise ValueError(
                "facts must contain CandidateDecisionConflictResolutionFacts",
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


def _conflict_resolution_confidence(
    *,
    unresolved_contradiction_count: Decimal,
    highest_unresolved_contradiction_severity: Decimal,
    official_hierarchy_strength: Decimal,
    independent_corroboration_count: Decimal,
    analyst_dissent_score: Decimal,
    ambiguity_dispute_risk_score: Decimal,
    config: CandidateDecisionConflictResolutionScoreConfig,
) -> Decimal:
    contradiction_count_pressure = _coverage_score(
        unresolved_contradiction_count,
        config.max_unresolved_contradiction_count_for_score,
    )
    independent_corroboration_score = _coverage_score(
        independent_corroboration_count,
        config.min_pass_independent_corroboration_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        weighted = (
            official_hierarchy_strength * config.official_hierarchy_weight
            + independent_corroboration_score * config.independent_corroboration_weight
            + (ONE - contradiction_count_pressure) * config.contradiction_count_weight
            + (ONE - highest_unresolved_contradiction_severity)
            * config.contradiction_severity_weight
            + (ONE - analyst_dissent_score) * config.analyst_consensus_weight
            + (ONE - ambiguity_dispute_risk_score) * config.low_ambiguity_weight
        )
    return _clamp_ratio(weighted)


def _reason_codes_for_values(
    *,
    unresolved_contradiction_count: Decimal,
    highest_unresolved_contradiction_severity: Decimal,
    official_hierarchy_strength: Decimal,
    independent_corroboration_count: Decimal,
    analyst_dissent_score: Decimal,
    ambiguity_dispute_risk_score: Decimal,
    conflict_resolution_confidence: Decimal,
    config: CandidateDecisionConflictResolutionScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if unresolved_contradiction_count > config.max_watch_unresolved_contradiction_count:
        codes.append("unresolved_contradictions_blocked")
    elif unresolved_contradiction_count > config.max_pass_unresolved_contradiction_count:
        codes.append("unresolved_contradictions_watch")
    if (
        highest_unresolved_contradiction_severity
        > config.max_watch_unresolved_contradiction_severity
    ):
        codes.append("unresolved_contradiction_severity_blocked")
    elif (
        highest_unresolved_contradiction_severity
        > config.max_pass_unresolved_contradiction_severity
    ):
        codes.append("unresolved_contradiction_severity_watch")
    if official_hierarchy_strength < config.min_watch_official_hierarchy_strength:
        codes.append("official_hierarchy_strength_blocked")
    elif official_hierarchy_strength < config.min_pass_official_hierarchy_strength:
        codes.append("official_hierarchy_strength_watch")
    if independent_corroboration_count < config.min_watch_independent_corroboration_count:
        codes.append("independent_corroboration_blocked")
    elif independent_corroboration_count < config.min_pass_independent_corroboration_count:
        codes.append("independent_corroboration_watch")
    if analyst_dissent_score > config.max_watch_analyst_dissent_score:
        codes.append("analyst_dissent_blocked")
    elif analyst_dissent_score > config.max_pass_analyst_dissent_score:
        codes.append("analyst_dissent_watch")
    if ambiguity_dispute_risk_score > config.max_watch_ambiguity_dispute_risk_score:
        codes.append("ambiguity_dispute_risk_blocked")
    elif ambiguity_dispute_risk_score > config.max_pass_ambiguity_dispute_risk_score:
        codes.append("ambiguity_dispute_risk_watch")
    if conflict_resolution_confidence < config.min_watch_conflict_resolution_confidence:
        codes.append("conflict_resolution_confidence_blocked_score")
    elif conflict_resolution_confidence < config.min_pass_conflict_resolution_confidence:
        codes.append("conflict_resolution_confidence_watch_score")
    if not codes:
        return ("conflict_resolution_pass",)
    return tuple(codes)


def _config_from_row(
    row: CandidateDecisionConflictResolutionScoreRow,
) -> CandidateDecisionConflictResolutionScoreConfig:
    return CandidateDecisionConflictResolutionScoreConfig(
        max_pass_unresolved_contradiction_count=(
            row.max_pass_unresolved_contradiction_count
        ),
        max_watch_unresolved_contradiction_count=(
            row.max_watch_unresolved_contradiction_count
        ),
        max_unresolved_contradiction_count_for_score=(
            row.max_unresolved_contradiction_count_for_score
        ),
        max_pass_unresolved_contradiction_severity=(
            row.max_pass_unresolved_contradiction_severity
        ),
        max_watch_unresolved_contradiction_severity=(
            row.max_watch_unresolved_contradiction_severity
        ),
        min_pass_official_hierarchy_strength=row.min_pass_official_hierarchy_strength,
        min_watch_official_hierarchy_strength=row.min_watch_official_hierarchy_strength,
        min_pass_independent_corroboration_count=(
            row.min_pass_independent_corroboration_count
        ),
        min_watch_independent_corroboration_count=(
            row.min_watch_independent_corroboration_count
        ),
        max_pass_analyst_dissent_score=row.max_pass_analyst_dissent_score,
        max_watch_analyst_dissent_score=row.max_watch_analyst_dissent_score,
        max_pass_ambiguity_dispute_risk_score=(
            row.max_pass_ambiguity_dispute_risk_score
        ),
        max_watch_ambiguity_dispute_risk_score=(
            row.max_watch_ambiguity_dispute_risk_score
        ),
        min_pass_conflict_resolution_confidence=(
            row.min_pass_conflict_resolution_confidence
        ),
        min_watch_conflict_resolution_confidence=(
            row.min_watch_conflict_resolution_confidence
        ),
        official_hierarchy_weight=row.official_hierarchy_weight,
        independent_corroboration_weight=row.independent_corroboration_weight,
        contradiction_count_weight=row.contradiction_count_weight,
        contradiction_severity_weight=row.contradiction_severity_weight,
        analyst_consensus_weight=row.analyst_consensus_weight,
        low_ambiguity_weight=row.low_ambiguity_weight,
    )


def _validate_row(row: CandidateDecisionConflictResolutionScoreRow) -> None:
    config = _config_from_row(row)
    expected_count_pressure = _coverage_score(
        row.unresolved_contradiction_count,
        row.max_unresolved_contradiction_count_for_score,
    )
    expected_corroboration_score = _coverage_score(
        row.independent_corroboration_count,
        row.min_pass_independent_corroboration_count,
    )
    expected_confidence = _conflict_resolution_confidence(
        unresolved_contradiction_count=row.unresolved_contradiction_count,
        highest_unresolved_contradiction_severity=(
            row.highest_unresolved_contradiction_severity
        ),
        official_hierarchy_strength=row.official_hierarchy_strength,
        independent_corroboration_count=row.independent_corroboration_count,
        analyst_dissent_score=row.analyst_dissent_score,
        ambiguity_dispute_risk_score=row.ambiguity_dispute_risk_score,
        config=config,
    )
    expected_reasons = _reason_codes_for_values(
        unresolved_contradiction_count=row.unresolved_contradiction_count,
        highest_unresolved_contradiction_severity=(
            row.highest_unresolved_contradiction_severity
        ),
        official_hierarchy_strength=row.official_hierarchy_strength,
        independent_corroboration_count=row.independent_corroboration_count,
        analyst_dissent_score=row.analyst_dissent_score,
        ambiguity_dispute_risk_score=row.ambiguity_dispute_risk_score,
        conflict_resolution_confidence=row.conflict_resolution_confidence,
        config=config,
    )
    if row.contradiction_count_pressure != expected_count_pressure:
        raise ValueError("contradiction_count_pressure must match facts")
    if row.independent_corroboration_score != expected_corroboration_score:
        raise ValueError("independent_corroboration_score must match facts")
    if row.conflict_resolution_confidence != expected_confidence:
        raise ValueError("conflict_resolution_confidence must match facts")
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match facts")
    if row.support_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("support_status must match reason_codes")


def _validate_row_digests(row: CandidateDecisionConflictResolutionScoreRow) -> None:
    if row.row_sha256 != _row_sha256(row):
        raise ValueError("row_sha256 must match row fields")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("conflict_resolution_pass",):
        return STATUS_PASS
    if any(code in BLOCK_REASON_CODES for code in reason_codes):
        return STATUS_BLOCKED
    if any(code in WATCH_REASON_CODES for code in reason_codes):
        return STATUS_WATCH
    raise ValueError("reason_codes must imply pass, watch, or block")


def _report_status(rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.support_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.support_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("conflict_resolution_report_empty",)
    status = _report_status(rows)
    codes = [f"conflict_resolution_report_{status}"]
    row_code_set = {code for row in rows for code in row.reason_codes}
    for code in ROW_REASON_CODE_SEQUENCE:
        if code != "conflict_resolution_pass" and code in row_code_set:
            codes.append(code)
    return tuple(codes)


def _validate_report(report: CandidateDecisionConflictResolutionScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    if report.support_status != _report_status(rows):
        raise ValueError("support_status must match rows")
    if report.min_conflict_resolution_confidence != _min_confidence(rows):
        raise ValueError("min_conflict_resolution_confidence must match rows")
    if report.max_conflict_resolution_confidence != _max_confidence(rows):
        raise ValueError("max_conflict_resolution_confidence must match rows")
    if report.average_conflict_resolution_confidence != _average_confidence(rows):
        raise ValueError("average_conflict_resolution_confidence must match rows")
    if report.max_unresolved_contradiction_count != _max_unresolved_contradiction_count(
        rows,
    ):
        raise ValueError("max_unresolved_contradiction_count must match rows")
    if report.max_unresolved_contradiction_severity != (
        _max_unresolved_contradiction_severity(rows)
    ):
        raise ValueError("max_unresolved_contradiction_severity must match rows")
    if report.max_analyst_dissent_score != _max_analyst_dissent_score(rows):
        raise ValueError("max_analyst_dissent_score must match rows")
    if report.max_ambiguity_dispute_risk_score != _max_ambiguity_dispute_risk_score(rows):
        raise ValueError("max_ambiguity_dispute_risk_score must match rows")
    expected_fact_set_versions = tuple(
        sorted((row.redacted_candidate_ref, row.fact_set_version) for row in rows),
    )
    if report.fact_set_versions != expected_fact_set_versions:
        raise ValueError("fact_set_versions must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_digests(report: CandidateDecisionConflictResolutionScoreReport) -> None:
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _status_count(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.support_status == status))


def _min_confidence(rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.conflict_resolution_confidence for row in rows)


def _max_confidence(rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.conflict_resolution_confidence for row in rows)


def _average_confidence(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((row.conflict_resolution_confidence for row in rows), ZERO)
            / _count_decimal(len(rows)),
        )


def _max_unresolved_contradiction_count(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.unresolved_contradiction_count for row in rows)


def _max_unresolved_contradiction_severity(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.highest_unresolved_contradiction_severity for row in rows)


def _max_analyst_dissent_score(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.analyst_dissent_score for row in rows)


def _max_ambiguity_dispute_risk_score(
    rows: tuple[CandidateDecisionConflictResolutionScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.ambiguity_dispute_risk_score for row in rows)


def _validate_config(config: CandidateDecisionConflictResolutionScoreConfig) -> None:
    if (
        config.max_pass_unresolved_contradiction_count
        > config.max_watch_unresolved_contradiction_count
    ):
        raise ValueError("max_pass_unresolved_contradiction_count must be at most watch")
    if (
        config.max_watch_unresolved_contradiction_count
        > config.max_unresolved_contradiction_count_for_score
    ):
        raise ValueError("max_watch_unresolved_contradiction_count must be at most scoring max")
    if config.max_unresolved_contradiction_count_for_score <= ZERO:
        raise ValueError("max_unresolved_contradiction_count_for_score must be positive")
    if (
        config.max_pass_unresolved_contradiction_severity
        > config.max_watch_unresolved_contradiction_severity
    ):
        raise ValueError("max_pass_unresolved_contradiction_severity must be at most watch")
    if (
        config.min_pass_official_hierarchy_strength
        < config.min_watch_official_hierarchy_strength
    ):
        raise ValueError("min_pass_official_hierarchy_strength must be at least watch")
    if (
        config.min_pass_independent_corroboration_count
        < config.min_watch_independent_corroboration_count
    ):
        raise ValueError("min_pass_independent_corroboration_count must be at least watch")
    if config.min_watch_independent_corroboration_count <= ZERO:
        raise ValueError("min_watch_independent_corroboration_count must be positive")
    if config.min_pass_independent_corroboration_count <= ZERO:
        raise ValueError("min_pass_independent_corroboration_count must be positive")
    if config.max_pass_analyst_dissent_score > config.max_watch_analyst_dissent_score:
        raise ValueError("max_pass_analyst_dissent_score must be at most watch")
    if (
        config.max_pass_ambiguity_dispute_risk_score
        > config.max_watch_ambiguity_dispute_risk_score
    ):
        raise ValueError("max_pass_ambiguity_dispute_risk_score must be at most watch")
    if (
        config.min_pass_conflict_resolution_confidence
        < config.min_watch_conflict_resolution_confidence
    ):
        raise ValueError("min_pass_conflict_resolution_confidence must be at least watch")
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.official_hierarchy_weight
            + config.independent_corroboration_weight
            + config.contradiction_count_weight
            + config.contradiction_severity_weight
            + config.analyst_consensus_weight
            + config.low_ambiguity_weight
        )
    if weight_total != ONE:
        raise ValueError("weights must sum to 1.000000")


def _require_rows(
    rows: object,
) -> tuple[CandidateDecisionConflictResolutionScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not CandidateDecisionConflictResolutionScoreRow:
            raise ValueError("rows must contain CandidateDecisionConflictResolutionScoreRow")
        _require_hard_flags("row", row)
        _validate_row(row)
        _validate_row_digests(row)
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(row.redacted_candidate_ref)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted weakest first")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be contiguous")
    return rows


def _require_fact_set_versions(values: object) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("fact_set_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("fact_set_versions entries must be pairs")
        redacted_candidate_ref, fact_set_version = value
        normalized.append(
            (
                _require_redacted_candidate_ref(
                    "fact_set_versions redacted_candidate_ref",
                    redacted_candidate_ref,
                ),
                _require_public_string("fact_set_versions fact_set_version", fact_set_version),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("fact_set_versions must be sorted")
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
) -> CandidateDecisionConflictResolutionScoreReport:
    support_status = _payload_support_status(payload, "support_status")
    return CandidateDecisionConflictResolutionScoreReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        support_status=support_status,
        candidate_count=_payload_decimal(payload, "candidate_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        blocked_count=_payload_decimal(payload, "blocked_count"),
        min_conflict_resolution_confidence=_payload_decimal(
            payload,
            "min_conflict_resolution_confidence",
        ),
        max_conflict_resolution_confidence=_payload_decimal(
            payload,
            "max_conflict_resolution_confidence",
        ),
        average_conflict_resolution_confidence=_payload_decimal(
            payload,
            "average_conflict_resolution_confidence",
        ),
        max_unresolved_contradiction_count=_payload_decimal(
            payload,
            "max_unresolved_contradiction_count",
        ),
        max_unresolved_contradiction_severity=_payload_decimal(
            payload,
            "max_unresolved_contradiction_severity",
        ),
        max_analyst_dissent_score=_payload_decimal(
            payload,
            "max_analyst_dissent_score",
        ),
        max_ambiguity_dispute_risk_score=_payload_decimal(
            payload,
            "max_ambiguity_dispute_risk_score",
        ),
        rows=_payload_rows(payload),
        fact_set_versions=_payload_fact_set_versions(payload),
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
) -> tuple[CandidateDecisionConflictResolutionScoreRow, ...]:
    values = payload.get("rows")
    if type(values) is not list:
        raise ValueError("payload rows must be a list")
    return tuple(_row_from_payload(row) for row in values)


def _row_from_payload(payload: dict[str, Any]) -> CandidateDecisionConflictResolutionScoreRow:
    support_status = _payload_support_status(payload, "support_status")
    _require_payload_hash(payload, "row", "row_sha256")
    return CandidateDecisionConflictResolutionScoreRow(
        rank=_payload_decimal(payload, "rank"),
        redacted_candidate_ref=_payload_redacted_candidate_ref(
            payload,
            "redacted_candidate_ref",
        ),
        observed_at=_payload_datetime(payload, "observed_at"),
        unresolved_contradiction_count=_payload_decimal(
            payload,
            "unresolved_contradiction_count",
        ),
        highest_unresolved_contradiction_severity=_payload_decimal(
            payload,
            "highest_unresolved_contradiction_severity",
        ),
        official_hierarchy_strength=_payload_decimal(
            payload,
            "official_hierarchy_strength",
        ),
        independent_corroboration_count=_payload_decimal(
            payload,
            "independent_corroboration_count",
        ),
        analyst_dissent_score=_payload_decimal(payload, "analyst_dissent_score"),
        ambiguity_dispute_risk_score=_payload_decimal(
            payload,
            "ambiguity_dispute_risk_score",
        ),
        contradiction_count_pressure=_payload_decimal(
            payload,
            "contradiction_count_pressure",
        ),
        independent_corroboration_score=_payload_decimal(
            payload,
            "independent_corroboration_score",
        ),
        conflict_resolution_confidence=_payload_decimal(
            payload,
            "conflict_resolution_confidence",
        ),
        support_status=support_status,
        reason_codes=_payload_reason_codes(
            payload,
            "reason_codes",
            ROW_REASON_CODE_SEQUENCE,
        ),
        fact_set_version=_payload_string(payload, "fact_set_version"),
        max_pass_unresolved_contradiction_count=_payload_decimal(
            payload,
            "max_pass_unresolved_contradiction_count",
        ),
        max_watch_unresolved_contradiction_count=_payload_decimal(
            payload,
            "max_watch_unresolved_contradiction_count",
        ),
        max_unresolved_contradiction_count_for_score=_payload_decimal(
            payload,
            "max_unresolved_contradiction_count_for_score",
        ),
        max_pass_unresolved_contradiction_severity=_payload_decimal(
            payload,
            "max_pass_unresolved_contradiction_severity",
        ),
        max_watch_unresolved_contradiction_severity=_payload_decimal(
            payload,
            "max_watch_unresolved_contradiction_severity",
        ),
        min_pass_official_hierarchy_strength=_payload_decimal(
            payload,
            "min_pass_official_hierarchy_strength",
        ),
        min_watch_official_hierarchy_strength=_payload_decimal(
            payload,
            "min_watch_official_hierarchy_strength",
        ),
        min_pass_independent_corroboration_count=_payload_decimal(
            payload,
            "min_pass_independent_corroboration_count",
        ),
        min_watch_independent_corroboration_count=_payload_decimal(
            payload,
            "min_watch_independent_corroboration_count",
        ),
        max_pass_analyst_dissent_score=_payload_decimal(
            payload,
            "max_pass_analyst_dissent_score",
        ),
        max_watch_analyst_dissent_score=_payload_decimal(
            payload,
            "max_watch_analyst_dissent_score",
        ),
        max_pass_ambiguity_dispute_risk_score=_payload_decimal(
            payload,
            "max_pass_ambiguity_dispute_risk_score",
        ),
        max_watch_ambiguity_dispute_risk_score=_payload_decimal(
            payload,
            "max_watch_ambiguity_dispute_risk_score",
        ),
        min_pass_conflict_resolution_confidence=_payload_decimal(
            payload,
            "min_pass_conflict_resolution_confidence",
        ),
        min_watch_conflict_resolution_confidence=_payload_decimal(
            payload,
            "min_watch_conflict_resolution_confidence",
        ),
        official_hierarchy_weight=_payload_decimal(payload, "official_hierarchy_weight"),
        independent_corroboration_weight=_payload_decimal(
            payload,
            "independent_corroboration_weight",
        ),
        contradiction_count_weight=_payload_decimal(
            payload,
            "contradiction_count_weight",
        ),
        contradiction_severity_weight=_payload_decimal(
            payload,
            "contradiction_severity_weight",
        ),
        analyst_consensus_weight=_payload_decimal(payload, "analyst_consensus_weight"),
        low_ambiguity_weight=_payload_decimal(payload, "low_ambiguity_weight"),
        row_sha256=_payload_sha256(payload, "row_sha256"),
        derived_validation_digest=_payload_sha256(payload, "derived_validation_digest"),
        paper_only=_payload_bool(payload, "paper_only"),
        report_only=_payload_bool(payload, "report_only"),
        readonly=_payload_bool(payload, "readonly"),
    )


def _payload_fact_set_versions(payload: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    values = payload.get("fact_set_versions")
    if type(values) is not list:
        raise ValueError("fact_set_versions must be a list")
    pairs: list[tuple[str, str]] = []
    for value in values:
        if type(value) is not list or len(value) != 2:
            raise ValueError("fact_set_versions entries must be pairs")
        pairs.append(
            (
                _require_redacted_candidate_ref("fact_set_versions", value[0]),
                _require_public_string("fact_set_versions", value[1]),
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


def _payload_support_status(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_support_status(field_name, value)
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


def _require_support_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SUPPORT_STATUSES:
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


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_key(label, key)
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


def _reject_unsafe_public_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")
    if any(token in UNSAFE_PUBLIC_KEY_TOKENS for token in _surface_key_tokens(lowered)):
        raise ValueError(f"unsafe public surface in {label}")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in UNSAFE_PUBLIC_KEY_TOKENS):
        raise ValueError(f"unsafe public surface in {label}")


def _surface_key_tokens(key: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in key:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _normalize_optional_sha256(field_name: str, value: object) -> str:
    if value == "":
        return ""
    return _normalize_sha256(field_name, value)


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    return value


def _require_payload_digests(payload: dict[str, Any]) -> None:
    _require_payload_digest(payload, "report")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        _require_payload_digest(row, "row")


def _require_payload_digest(payload: dict[str, Any], label: str) -> None:
    digest_key = "derived_validation_digest"
    digest_value = payload.get(digest_key)
    _normalize_sha256(digest_key, digest_value)
    expected = _derived_validation_digest(payload, digest_key)
    if digest_value != expected:
        raise ValueError(f"{digest_key} must match {label} payload")


def _row_sha256(row: CandidateDecisionConflictResolutionScoreRow) -> str:
    return _sha256_from_payload("row", _row_payload_for_digest(row, include_hashes=False))


def _row_derived_validation_digest(row: CandidateDecisionConflictResolutionScoreRow) -> str:
    return _derived_validation_digest(
        _row_payload_for_digest(row, include_hashes=True),
        "derived_validation_digest",
    )


def _report_sha256(report: CandidateDecisionConflictResolutionScoreReport) -> str:
    return _sha256_from_payload(
        "report",
        _report_payload_for_digest(report, include_hashes=False),
    )


def _report_derived_validation_digest(
    report: CandidateDecisionConflictResolutionScoreReport,
) -> str:
    return _derived_validation_digest(
        _report_payload_for_digest(report, include_hashes=True),
        "derived_validation_digest",
    )


def _row_payload_for_digest(
    row: CandidateDecisionConflictResolutionScoreRow,
    *,
    include_hashes: bool,
) -> dict[str, object]:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    if not include_hashes:
        payload.pop("row_sha256", None)
        payload.pop("derived_validation_digest", None)
    else:
        payload.pop("derived_validation_digest", None)
    return payload


def _report_payload_for_digest(
    report: CandidateDecisionConflictResolutionScoreReport,
    *,
    include_hashes: bool,
) -> dict[str, object]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    if not include_hashes:
        payload.pop("report_sha256", None)
        payload.pop("derived_validation_digest", None)
    else:
        payload.pop("derived_validation_digest", None)
    return payload


def _sha256_from_payload(label: str, payload: dict[str, object]) -> str:
    encoded = json.dumps(
        {"label": label, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _derived_validation_digest(payload: dict[str, Any], digest_key: str) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(digest_key, None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_CONFLICT_RESOLUTION_SCORE_VERSION",
    "CandidateDecisionConflictResolutionFacts",
    "CandidateDecisionConflictResolutionScoreConfig",
    "CandidateDecisionConflictResolutionScoreReport",
    "CandidateDecisionConflictResolutionScoreRow",
    "build_candidate_decision_conflict_resolution_score",
    "candidate_decision_conflict_resolution_score_payload",
    "validate_candidate_decision_conflict_resolution_score_payload",
    "validate_candidate_decision_conflict_resolution_score_report",
)
