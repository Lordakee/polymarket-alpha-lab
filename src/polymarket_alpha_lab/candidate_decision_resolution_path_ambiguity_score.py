"""Pure report-only resolution path ambiguity scorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_RESOLUTION_PATH_AMBIGUITY_SCORE_CONFIG_VERSION = (
    "candidate-decision-resolution-path-ambiguity-score-v1"
)

SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

PATH_COUNT_WEIGHT = Decimal("0.170000")
CONFLICT_WEIGHT = Decimal("0.250000")
RULE_BRANCH_WEIGHT = Decimal("0.050000")
ADJUDICATION_WEIGHT = Decimal("0.280000")
EVIDENCE_GAP_WEIGHT = Decimal("0.150000")
PRIMARY_CONFIDENCE_GAP_WEIGHT = Decimal("0.100000")

STATUSES = ("pass", "watch", "block")
RESULT_REASON_CODES = (
    "resolution_path_ambiguity_pass",
    "resolution_path_ambiguity_empty",
    "distinct_resolution_paths_block",
    "distinct_resolution_paths_watch",
    "conflicting_resolution_paths_block",
    "conflicting_resolution_paths_watch",
    "resolution_rule_branches_block",
    "resolution_rule_branches_watch",
    "adjudication_touchpoints_block",
    "adjudication_touchpoints_watch",
    "ambiguity_evidence_coverage_block",
    "ambiguity_evidence_coverage_watch",
    "primary_path_confidence_block",
    "primary_path_confidence_watch",
    "resolution_path_ambiguity_score_block",
    "resolution_path_ambiguity_score_watch",
)
REPORT_REASON_CODE_SEQUENCE = (
    "distinct_resolution_paths_block",
    "distinct_resolution_paths_watch",
    "conflicting_resolution_paths_block",
    "conflicting_resolution_paths_watch",
    "resolution_rule_branches_block",
    "resolution_rule_branches_watch",
    "adjudication_touchpoints_block",
    "adjudication_touchpoints_watch",
    "ambiguity_evidence_coverage_block",
    "ambiguity_evidence_coverage_watch",
    "primary_path_confidence_block",
    "primary_path_confidence_watch",
    "resolution_path_ambiguity_score_block",
    "resolution_path_ambiguity_score_watch",
)
BLOCK_REASON_CODES = (
    "distinct_resolution_paths_block",
    "conflicting_resolution_paths_block",
    "resolution_rule_branches_block",
    "adjudication_touchpoints_block",
    "ambiguity_evidence_coverage_block",
    "primary_path_confidence_block",
    "resolution_path_ambiguity_score_block",
)
WATCH_REASON_CODES = (
    "distinct_resolution_paths_watch",
    "conflicting_resolution_paths_watch",
    "resolution_rule_branches_watch",
    "adjudication_touchpoints_watch",
    "ambiguity_evidence_coverage_watch",
    "primary_path_confidence_watch",
    "resolution_path_ambiguity_score_watch",
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "credential",
    "private" + "_" + "key",
    "signing",
)
UNSAFE_PUBLIC_KEY_TOKENS = (
    "auth",
    "balance",
    "cancel",
    "credential",
    "d" + "sn",
    "market",
    "or" + "der",
    "pos" + "ition",
    "question",
    "secret",
    "slug",
    "source",
    "ta" + "ble",
    "token",
    "tra" + "de",
    "url",
    "wal" + "let",
)
UNSAFE_PUBLIC_VALUE_TERMS = (
    "auth",
    "b" + "uy",
    "d" + "sn",
    "market",
    "or" + "der",
    "pos" + "ition",
    "question",
    "recom" + "mendation",
    "s" + "ell",
    "secret",
    "slug",
    "source",
    "ta" + "ble",
    "token",
    "tra" + "de",
    "url",
    "wal" + "let",
)


@dataclass(frozen=True)
class CandidateDecisionResolutionPathAmbiguityScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_RESOLUTION_PATH_AMBIGUITY_SCORE_CONFIG_VERSION
    )
    max_pass_ambiguity_score: Decimal = Decimal("0.250000")
    max_watch_ambiguity_score: Decimal = Decimal("0.550000")
    max_pass_distinct_resolution_path_count: Decimal = Decimal("1.000000")
    max_watch_distinct_resolution_path_count: Decimal = Decimal("3.000000")
    max_pass_conflicting_path_count: Decimal = Decimal("0.000000")
    max_watch_conflicting_path_count: Decimal = Decimal("2.000000")
    max_pass_rule_branch_count: Decimal = Decimal("1.000000")
    max_watch_rule_branch_count: Decimal = Decimal("4.000000")
    max_pass_adjudication_touchpoint_count: Decimal = Decimal("0.000000")
    max_watch_adjudication_touchpoint_count: Decimal = Decimal("2.000000")
    min_pass_ambiguity_evidence_coverage: Decimal = Decimal("0.800000")
    min_watch_ambiguity_evidence_coverage: Decimal = Decimal("0.550000")
    min_pass_primary_path_confidence: Decimal = Decimal("0.750000")
    min_watch_primary_path_confidence: Decimal = Decimal("0.500000")
    max_distinct_resolution_path_count_for_score: Decimal = Decimal("5.000000")
    max_conflicting_path_count_for_score: Decimal = Decimal("4.000000")
    max_rule_branch_count_for_score: Decimal = Decimal("6.000000")
    max_adjudication_touchpoint_count_for_score: Decimal = Decimal("4.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionPathAmbiguityScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionResolutionPathAmbiguityScoreConfig",
            )
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "max_pass_ambiguity_score",
            "max_watch_ambiguity_score",
            "min_pass_ambiguity_evidence_coverage",
            "min_watch_ambiguity_evidence_coverage",
            "min_pass_primary_path_confidence",
            "min_watch_primary_path_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_distinct_resolution_path_count",
            "max_watch_distinct_resolution_path_count",
            "max_pass_conflicting_path_count",
            "max_watch_conflicting_path_count",
            "max_pass_rule_branch_count",
            "max_watch_rule_branch_count",
            "max_pass_adjudication_touchpoint_count",
            "max_watch_adjudication_touchpoint_count",
            "max_distinct_resolution_path_count_for_score",
            "max_conflicting_path_count_for_score",
            "max_rule_branch_count_for_score",
            "max_adjudication_touchpoint_count_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_ambiguity_score > self.max_watch_ambiguity_score:
            raise ValueError("max_pass_ambiguity_score must be at most watch threshold")
        if (
            self.max_pass_distinct_resolution_path_count
            > self.max_watch_distinct_resolution_path_count
        ):
            raise ValueError(
                "max_pass_distinct_resolution_path_count must be at most watch threshold",
            )
        if self.max_pass_conflicting_path_count > self.max_watch_conflicting_path_count:
            raise ValueError("max_pass_conflicting_path_count must be at most watch threshold")
        if self.max_pass_rule_branch_count > self.max_watch_rule_branch_count:
            raise ValueError("max_pass_rule_branch_count must be at most watch threshold")
        if (
            self.max_pass_adjudication_touchpoint_count
            > self.max_watch_adjudication_touchpoint_count
        ):
            raise ValueError(
                "max_pass_adjudication_touchpoint_count must be at most watch threshold",
            )
        if (
            self.min_pass_ambiguity_evidence_coverage
            < self.min_watch_ambiguity_evidence_coverage
        ):
            raise ValueError(
                "min_pass_ambiguity_evidence_coverage must be at least watch threshold",
            )
        if self.min_pass_primary_path_confidence < self.min_watch_primary_path_confidence:
            raise ValueError("min_pass_primary_path_confidence must be at least watch threshold")
        for field_name in (
            "max_distinct_resolution_path_count_for_score",
            "max_conflicting_path_count_for_score",
            "max_rule_branch_count_for_score",
            "max_adjudication_touchpoint_count_for_score",
        ):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        _reject_unsafe_public_payload("ambiguity config", self)
        require_paper_only_flags("ambiguity config", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionPathAmbiguityScoreCandidate:
    candidate_reference: str
    distinct_resolution_path_count: Decimal
    conflicting_path_count: Decimal
    rule_branch_count: Decimal
    adjudication_touchpoint_count: Decimal
    ambiguity_evidence_coverage: Decimal
    primary_path_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionPathAmbiguityScoreCandidate:
            raise ValueError(
                "candidate must be a CandidateDecisionResolutionPathAmbiguityScoreCandidate",
            )
        _require_identifier("candidate_reference", self.candidate_reference)
        for field_name in (
            "distinct_resolution_path_count",
            "conflicting_path_count",
            "rule_branch_count",
            "adjudication_touchpoint_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ambiguity_evidence_coverage",
            "primary_path_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("ambiguity candidate", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionPathAmbiguityScoreResult:
    redacted_candidate_reference: str
    distinct_resolution_path_count: Decimal
    conflicting_path_count: Decimal
    rule_branch_count: Decimal
    adjudication_touchpoint_count: Decimal
    ambiguity_evidence_coverage: Decimal
    primary_path_confidence: Decimal
    path_count_pressure: Decimal
    conflict_pressure: Decimal
    rule_branch_pressure: Decimal
    adjudication_pressure: Decimal
    ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    max_distinct_resolution_path_count_for_score: Decimal = Decimal("5.000000")
    max_conflicting_path_count_for_score: Decimal = Decimal("4.000000")
    max_rule_branch_count_for_score: Decimal = Decimal("6.000000")
    max_adjudication_touchpoint_count_for_score: Decimal = Decimal("4.000000")
    result_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionPathAmbiguityScoreResult:
            raise ValueError(
                "result must be a CandidateDecisionResolutionPathAmbiguityScoreResult",
            )
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        for field_name in (
            "distinct_resolution_path_count",
            "conflicting_path_count",
            "rule_branch_count",
            "adjudication_touchpoint_count",
            "max_distinct_resolution_path_count_for_score",
            "max_conflicting_path_count_for_score",
            "max_rule_branch_count_for_score",
            "max_adjudication_touchpoint_count_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ambiguity_evidence_coverage",
            "primary_path_confidence",
            "path_count_pressure",
            "conflict_pressure",
            "rule_branch_pressure",
            "adjudication_pressure",
            "ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _reject_unsafe_public_payload("ambiguity result", self)
        require_paper_only_flags("ambiguity result", self)
        if self.result_sha256 == "":
            object.__setattr__(self, "result_sha256", _result_sha256(self))
        else:
            object.__setattr__(
                self,
                "result_sha256",
                _normalize_sha256("result_sha256", self.result_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _result_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_result(self)


@dataclass(frozen=True)
class CandidateDecisionResolutionPathAmbiguityScoreReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_ambiguity_score: Decimal
    max_ambiguity_score: Decimal
    average_ambiguity_score: Decimal
    max_distinct_resolution_path_count: Decimal
    max_conflicting_path_count: Decimal
    max_rule_branch_count: Decimal
    max_adjudication_touchpoint_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionPathAmbiguityScoreReport:
            raise ValueError(
                "report must be a CandidateDecisionResolutionPathAmbiguityScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_distinct_resolution_path_count",
            "max_conflicting_path_count",
            "max_rule_branch_count",
            "max_adjudication_touchpoint_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ambiguity_score",
            "max_ambiguity_score",
            "average_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.results) is not tuple:
            raise ValueError("results must be a tuple")
        for result in self.results:
            if type(result) is not CandidateDecisionResolutionPathAmbiguityScoreResult:
                raise ValueError(
                    "results must contain CandidateDecisionResolutionPathAmbiguityScoreResult",
                )
            require_paper_only_flags("ambiguity result", result)
        _reject_unsafe_public_payload("ambiguity report", self)
        require_paper_only_flags("ambiguity report", self)
        if self.report_sha256 == "":
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        else:
            object.__setattr__(
                self,
                "report_sha256",
                _normalize_sha256("report_sha256", self.report_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_candidate_decision_resolution_path_ambiguity_score(
    candidates: object,
    *,
    config: CandidateDecisionResolutionPathAmbiguityScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionResolutionPathAmbiguityScoreReport:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of ambiguity candidates")
    try:
        candidate_rows = tuple(candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of ambiguity candidates") from exc
    if type(config) is not CandidateDecisionResolutionPathAmbiguityScoreConfig:
        raise ValueError("config must be a CandidateDecisionResolutionPathAmbiguityScoreConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    require_paper_only_flags("ambiguity config", config)

    seen_references: set[str] = set()
    results: list[CandidateDecisionResolutionPathAmbiguityScoreResult] = []
    for candidate in candidate_rows:
        if type(candidate) is not CandidateDecisionResolutionPathAmbiguityScoreCandidate:
            raise ValueError(
                "candidates must contain CandidateDecisionResolutionPathAmbiguityScoreCandidate",
            )
        require_paper_only_flags("ambiguity candidate", candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference")
        seen_references.add(candidate.candidate_reference)
        results.append(_build_result(candidate, config=config))

    sorted_results = tuple(
        sorted(
            results,
            key=lambda result: (
                -result.ambiguity_score,
                result.redacted_candidate_reference,
            ),
        ),
    )
    return CandidateDecisionResolutionPathAmbiguityScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_results)),
        pass_count=_count_decimal(sum(1 for result in sorted_results if result.status == "pass")),
        watch_count=_count_decimal(
            sum(1 for result in sorted_results if result.status == "watch"),
        ),
        block_count=_count_decimal(
            sum(1 for result in sorted_results if result.status == "block"),
        ),
        min_ambiguity_score=_min_ambiguity_score(sorted_results),
        max_ambiguity_score=_max_ambiguity_score(sorted_results),
        average_ambiguity_score=_average_ambiguity_score(sorted_results),
        max_distinct_resolution_path_count=_max_distinct_resolution_path_count(sorted_results),
        max_conflicting_path_count=_max_conflicting_path_count(sorted_results),
        max_rule_branch_count=_max_rule_branch_count(sorted_results),
        max_adjudication_touchpoint_count=_max_adjudication_touchpoint_count(sorted_results),
        status=_report_status(sorted_results),
        reason_codes=_report_reason_codes(sorted_results),
        results=sorted_results,
    )


def validate_candidate_decision_resolution_path_ambiguity_score_report(
    report: CandidateDecisionResolutionPathAmbiguityScoreReport,
) -> bool:
    if type(report) is not CandidateDecisionResolutionPathAmbiguityScoreReport:
        raise ValueError("report must be a CandidateDecisionResolutionPathAmbiguityScoreReport")
    _reject_unsafe_public_payload("ambiguity report", report)
    require_paper_only_flags("ambiguity report", report)
    _validate_report(report)
    return True


def validate_candidate_decision_resolution_path_ambiguity_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("ambiguity public payload", payload)
    _require_public_payload_flags(payload)
    return True


def candidate_decision_resolution_path_ambiguity_score_payload(
    report: CandidateDecisionResolutionPathAmbiguityScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionResolutionPathAmbiguityScoreReport:
        raise ValueError("report must be a CandidateDecisionResolutionPathAmbiguityScoreReport")
    validate_candidate_decision_resolution_path_ambiguity_score_report(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_resolution_path_ambiguity_score_public_payload(payload)
    return payload


def _build_result(
    candidate: CandidateDecisionResolutionPathAmbiguityScoreCandidate,
    *,
    config: CandidateDecisionResolutionPathAmbiguityScoreConfig,
) -> CandidateDecisionResolutionPathAmbiguityScoreResult:
    path_count_pressure = _excess_count_pressure(
        candidate.distinct_resolution_path_count,
        config.max_distinct_resolution_path_count_for_score,
    )
    conflict_pressure = _count_pressure(
        candidate.conflicting_path_count,
        config.max_conflicting_path_count_for_score,
    )
    rule_branch_pressure = _excess_count_pressure(
        candidate.rule_branch_count,
        config.max_rule_branch_count_for_score,
    )
    adjudication_pressure = _count_pressure(
        candidate.adjudication_touchpoint_count,
        config.max_adjudication_touchpoint_count_for_score,
    )
    ambiguity_score = _ambiguity_score(
        path_count_pressure=path_count_pressure,
        conflict_pressure=conflict_pressure,
        rule_branch_pressure=rule_branch_pressure,
        adjudication_pressure=adjudication_pressure,
        ambiguity_evidence_coverage=candidate.ambiguity_evidence_coverage,
        primary_path_confidence=candidate.primary_path_confidence,
    )
    reason_codes = _candidate_reason_codes(candidate, ambiguity_score=ambiguity_score, config=config)
    return CandidateDecisionResolutionPathAmbiguityScoreResult(
        redacted_candidate_reference=_redacted_candidate_reference(
            candidate.candidate_reference,
        ),
        distinct_resolution_path_count=candidate.distinct_resolution_path_count,
        conflicting_path_count=candidate.conflicting_path_count,
        rule_branch_count=candidate.rule_branch_count,
        adjudication_touchpoint_count=candidate.adjudication_touchpoint_count,
        ambiguity_evidence_coverage=candidate.ambiguity_evidence_coverage,
        primary_path_confidence=candidate.primary_path_confidence,
        path_count_pressure=path_count_pressure,
        conflict_pressure=conflict_pressure,
        rule_branch_pressure=rule_branch_pressure,
        adjudication_pressure=adjudication_pressure,
        ambiguity_score=ambiguity_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        max_distinct_resolution_path_count_for_score=(
            config.max_distinct_resolution_path_count_for_score
        ),
        max_conflicting_path_count_for_score=config.max_conflicting_path_count_for_score,
        max_rule_branch_count_for_score=config.max_rule_branch_count_for_score,
        max_adjudication_touchpoint_count_for_score=(
            config.max_adjudication_touchpoint_count_for_score
        ),
    )


def _candidate_reason_codes(
    candidate: CandidateDecisionResolutionPathAmbiguityScoreCandidate,
    *,
    ambiguity_score: Decimal,
    config: CandidateDecisionResolutionPathAmbiguityScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.distinct_resolution_path_count > config.max_watch_distinct_resolution_path_count:
        reason_codes.append("distinct_resolution_paths_block")
    elif candidate.distinct_resolution_path_count > config.max_pass_distinct_resolution_path_count:
        reason_codes.append("distinct_resolution_paths_watch")
    if candidate.conflicting_path_count > config.max_watch_conflicting_path_count:
        reason_codes.append("conflicting_resolution_paths_block")
    elif candidate.conflicting_path_count > config.max_pass_conflicting_path_count:
        reason_codes.append("conflicting_resolution_paths_watch")
    if candidate.rule_branch_count > config.max_watch_rule_branch_count:
        reason_codes.append("resolution_rule_branches_block")
    elif candidate.rule_branch_count > config.max_pass_rule_branch_count:
        reason_codes.append("resolution_rule_branches_watch")
    if candidate.adjudication_touchpoint_count > config.max_watch_adjudication_touchpoint_count:
        reason_codes.append("adjudication_touchpoints_block")
    elif candidate.adjudication_touchpoint_count > config.max_pass_adjudication_touchpoint_count:
        reason_codes.append("adjudication_touchpoints_watch")
    if candidate.ambiguity_evidence_coverage < config.min_watch_ambiguity_evidence_coverage:
        reason_codes.append("ambiguity_evidence_coverage_block")
    elif candidate.ambiguity_evidence_coverage < config.min_pass_ambiguity_evidence_coverage:
        reason_codes.append("ambiguity_evidence_coverage_watch")
    if candidate.primary_path_confidence < config.min_watch_primary_path_confidence:
        reason_codes.append("primary_path_confidence_block")
    elif candidate.primary_path_confidence < config.min_pass_primary_path_confidence:
        reason_codes.append("primary_path_confidence_watch")
    if ambiguity_score > config.max_watch_ambiguity_score:
        reason_codes.append("resolution_path_ambiguity_score_block")
    elif ambiguity_score > config.max_pass_ambiguity_score:
        reason_codes.append("resolution_path_ambiguity_score_watch")
    if not reason_codes:
        return ("resolution_path_ambiguity_pass",)
    return tuple(reason_codes)


def _excess_count_pressure(value: Decimal, max_value: Decimal) -> Decimal:
    if max_value <= ONE:
        raise ValueError("max_value must be above one")
    with localcontext(DECIMAL_CONTEXT):
        return _bounded_probability((value - ONE) / (max_value - ONE))


def _count_pressure(value: Decimal, max_value: Decimal) -> Decimal:
    if max_value <= ZERO:
        raise ValueError("max_value must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _bounded_probability(value / max_value)


def _ambiguity_score(
    *,
    path_count_pressure: Decimal,
    conflict_pressure: Decimal,
    rule_branch_pressure: Decimal,
    adjudication_pressure: Decimal,
    ambiguity_evidence_coverage: Decimal,
    primary_path_confidence: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            (path_count_pressure * PATH_COUNT_WEIGHT)
            + (conflict_pressure * CONFLICT_WEIGHT)
            + (rule_branch_pressure * RULE_BRANCH_WEIGHT)
            + (adjudication_pressure * ADJUDICATION_WEIGHT)
            + ((ONE - ambiguity_evidence_coverage) * EVIDENCE_GAP_WEIGHT)
            + ((ONE - primary_path_confidence) * PRIMARY_CONFIDENCE_GAP_WEIGHT)
        )
    return _bounded_probability(raw_score)


def _validate_result(result: CandidateDecisionResolutionPathAmbiguityScoreResult) -> None:
    expected_path_count_pressure = _excess_count_pressure(
        result.distinct_resolution_path_count,
        result.max_distinct_resolution_path_count_for_score,
    )
    expected_conflict_pressure = _count_pressure(
        result.conflicting_path_count,
        result.max_conflicting_path_count_for_score,
    )
    expected_rule_branch_pressure = _excess_count_pressure(
        result.rule_branch_count,
        result.max_rule_branch_count_for_score,
    )
    expected_adjudication_pressure = _count_pressure(
        result.adjudication_touchpoint_count,
        result.max_adjudication_touchpoint_count_for_score,
    )
    expected_ambiguity_score = _ambiguity_score(
        path_count_pressure=expected_path_count_pressure,
        conflict_pressure=expected_conflict_pressure,
        rule_branch_pressure=expected_rule_branch_pressure,
        adjudication_pressure=expected_adjudication_pressure,
        ambiguity_evidence_coverage=result.ambiguity_evidence_coverage,
        primary_path_confidence=result.primary_path_confidence,
    )
    if result.path_count_pressure != expected_path_count_pressure:
        raise ValueError("path_count_pressure must match candidate fields")
    if result.conflict_pressure != expected_conflict_pressure:
        raise ValueError("conflict_pressure must match candidate fields")
    if result.rule_branch_pressure != expected_rule_branch_pressure:
        raise ValueError("rule_branch_pressure must match candidate fields")
    if result.adjudication_pressure != expected_adjudication_pressure:
        raise ValueError("adjudication_pressure must match candidate fields")
    if result.ambiguity_score != expected_ambiguity_score:
        raise ValueError("ambiguity_score must match candidate fields")
    if result.status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("status must match reason_codes")
    if result.result_sha256 != _result_sha256(result):
        raise ValueError("result_sha256 must match result fields")
    if result.derived_validation_digest != _result_derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _validate_report(report: CandidateDecisionResolutionPathAmbiguityScoreReport) -> None:
    results = report.results
    if report.candidate_count != _count_decimal(len(results)):
        raise ValueError("candidate_count must match results")
    if report.pass_count != _count_decimal(sum(1 for result in results if result.status == "pass")):
        raise ValueError("pass_count must match results")
    if report.watch_count != _count_decimal(
        sum(1 for result in results if result.status == "watch"),
    ):
        raise ValueError("watch_count must match results")
    if report.block_count != _count_decimal(
        sum(1 for result in results if result.status == "block"),
    ):
        raise ValueError("block_count must match results")
    if report.min_ambiguity_score != _min_ambiguity_score(results):
        raise ValueError("min_ambiguity_score must match results")
    if report.max_ambiguity_score != _max_ambiguity_score(results):
        raise ValueError("max_ambiguity_score must match results")
    if report.average_ambiguity_score != _average_ambiguity_score(results):
        raise ValueError("average_ambiguity_score must match results")
    if report.max_distinct_resolution_path_count != _max_distinct_resolution_path_count(results):
        raise ValueError("max_distinct_resolution_path_count must match results")
    if report.max_conflicting_path_count != _max_conflicting_path_count(results):
        raise ValueError("max_conflicting_path_count must match results")
    if report.max_rule_branch_count != _max_rule_branch_count(results):
        raise ValueError("max_rule_branch_count must match results")
    if report.max_adjudication_touchpoint_count != _max_adjudication_touchpoint_count(results):
        raise ValueError("max_adjudication_touchpoint_count must match results")
    if report.status != _report_status(results):
        raise ValueError("status must match results")
    if report.reason_codes != _report_reason_codes(results):
        raise ValueError("reason_codes must match results")
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("resolution_path_ambiguity_pass",):
        return "pass"
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    raise ValueError("reason_codes must imply a supported status")


def _report_status(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> str:
    if not results:
        return "block"
    if any(result.status == "block" for result in results):
        return "block"
    if any(result.status == "watch" for result in results):
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> tuple[str, ...]:
    if not results:
        return ("resolution_path_ambiguity_empty",)
    aggregated: list[str] = []
    result_reason_codes = {
        reason_code for result in results for reason_code in result.reason_codes
    }
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        if reason_code in result_reason_codes:
            aggregated.append(reason_code)
    if not aggregated:
        return ("resolution_path_ambiguity_pass",)
    return tuple(aggregated)


def _min_ambiguity_score(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    return min(result.ambiguity_score for result in results)


def _max_ambiguity_score(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.ambiguity_score for result in results)


def _average_ambiguity_score(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            sum((result.ambiguity_score for result in results), ZERO)
            / _count_decimal(len(results)),
        )


def _max_distinct_resolution_path_count(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.distinct_resolution_path_count for result in results)


def _max_conflicting_path_count(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.conflicting_path_count for result in results)


def _max_rule_branch_count(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.rule_branch_count for result in results)


def _max_adjudication_touchpoint_count(
    results: tuple[CandidateDecisionResolutionPathAmbiguityScoreResult, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.adjudication_touchpoint_count for result in results)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SCORE_QUANT)


def _bounded_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_member(field_name, value, RESULT_REASON_CODES)
    return values


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_identifier(field_name, value)
    if not value.startswith("candidate_ref_"):
        raise ValueError(f"{field_name} must be redacted")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _redacted_candidate_reference(candidate_reference: str) -> str:
    return f"candidate_ref_{hashlib.sha256(candidate_reference.encode('utf-8')).hexdigest()[:16]}"


def _result_sha256(result: CandidateDecisionResolutionPathAmbiguityScoreResult) -> str:
    return _sha256(
        "result",
        (
            f"redacted_candidate_reference={result.redacted_candidate_reference}",
            f"distinct_resolution_path_count={result.distinct_resolution_path_count}",
            f"conflicting_path_count={result.conflicting_path_count}",
            f"rule_branch_count={result.rule_branch_count}",
            f"adjudication_touchpoint_count={result.adjudication_touchpoint_count}",
            f"ambiguity_evidence_coverage={result.ambiguity_evidence_coverage}",
            f"primary_path_confidence={result.primary_path_confidence}",
            f"path_count_pressure={result.path_count_pressure}",
            f"conflict_pressure={result.conflict_pressure}",
            f"rule_branch_pressure={result.rule_branch_pressure}",
            f"adjudication_pressure={result.adjudication_pressure}",
            f"ambiguity_score={result.ambiguity_score}",
            f"status={result.status}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            "max_distinct_resolution_path_count_for_score="
            f"{result.max_distinct_resolution_path_count_for_score}",
            f"max_conflicting_path_count_for_score={result.max_conflicting_path_count_for_score}",
            f"max_rule_branch_count_for_score={result.max_rule_branch_count_for_score}",
            "max_adjudication_touchpoint_count_for_score="
            f"{result.max_adjudication_touchpoint_count_for_score}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _result_derived_validation_digest(
    result: CandidateDecisionResolutionPathAmbiguityScoreResult,
) -> str:
    return _sha256(
        "result_derived",
        (
            f"path_count_pressure={result.path_count_pressure}",
            f"conflict_pressure={result.conflict_pressure}",
            f"rule_branch_pressure={result.rule_branch_pressure}",
            f"adjudication_pressure={result.adjudication_pressure}",
            f"ambiguity_score={result.ambiguity_score}",
            f"status={result.status}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            f"result_sha256={result.result_sha256}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _report_sha256(report: CandidateDecisionResolutionPathAmbiguityScoreReport) -> str:
    return _sha256(
        "report",
        (
            f"generated_at={report.generated_at.isoformat()}",
            f"config_version={report.config_version}",
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"block_count={report.block_count}",
            f"min_ambiguity_score={report.min_ambiguity_score}",
            f"max_ambiguity_score={report.max_ambiguity_score}",
            f"average_ambiguity_score={report.average_ambiguity_score}",
            "max_distinct_resolution_path_count="
            f"{report.max_distinct_resolution_path_count}",
            f"max_conflicting_path_count={report.max_conflicting_path_count}",
            f"max_rule_branch_count={report.max_rule_branch_count}",
            "max_adjudication_touchpoint_count="
            f"{report.max_adjudication_touchpoint_count}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            f"results={_digest_tuple(tuple(result.result_sha256 for result in report.results))}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _report_derived_validation_digest(
    report: CandidateDecisionResolutionPathAmbiguityScoreReport,
) -> str:
    return _sha256(
        "report_derived",
        (
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"block_count={report.block_count}",
            f"min_ambiguity_score={report.min_ambiguity_score}",
            f"max_ambiguity_score={report.max_ambiguity_score}",
            f"average_ambiguity_score={report.average_ambiguity_score}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            "result_derived_validation_digest="
            f"{_digest_tuple(tuple(result.derived_validation_digest for result in report.results))}",
            f"report_sha256={report.report_sha256}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _payload_keys(payload):
        if _is_unsafe_public_key(key):
            raise ValueError(f"unsafe public payload field in {label}: {key}")
    for value in _payload_string_values(payload):
        if _is_unsafe_public_value(value):
            raise ValueError(f"unsafe public payload value in {label}")


def _is_unsafe_public_key(key: str) -> bool:
    normalized_key = key.lower()
    if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        return True
    tokens = _surface_key_tokens(normalized_key)
    return any(token in tokens for token in UNSAFE_PUBLIC_KEY_TOKENS)


def _is_unsafe_public_value(value: str) -> bool:
    normalized_value = value.lower()
    return any(term in normalized_value for term in UNSAFE_PUBLIC_VALUE_TERMS)


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


def _payload_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_payload_keys(item))
        return tuple(keys)
    return ()


def _payload_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_string_values(asdict(value))
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_payload_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_payload_string_values(item))
        return tuple(values)
    return ()


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("public payload results must be a list")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("public payload results must contain dict rows")
        for field_name in ("paper_only", "report_only", "readonly"):
            if result.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True in public payload result")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_RESOLUTION_PATH_AMBIGUITY_SCORE_CONFIG_VERSION",
    "CandidateDecisionResolutionPathAmbiguityScoreCandidate",
    "CandidateDecisionResolutionPathAmbiguityScoreConfig",
    "CandidateDecisionResolutionPathAmbiguityScoreReport",
    "CandidateDecisionResolutionPathAmbiguityScoreResult",
    "build_candidate_decision_resolution_path_ambiguity_score",
    "candidate_decision_resolution_path_ambiguity_score_payload",
    "validate_candidate_decision_resolution_path_ambiguity_score_public_payload",
    "validate_candidate_decision_resolution_path_ambiguity_score_report",
)
