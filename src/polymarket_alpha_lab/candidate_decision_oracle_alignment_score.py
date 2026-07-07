"""Pure candidate oracle alignment score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
CONTRADICTION_ALIGNMENT_WEIGHT = Decimal("0.013333333333333333")
AMBIGUITY_RISK_PENALTY_WEIGHT = Decimal("0.030000")
SUPPORT_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_UNSAFE_TERM_PARTS = (
    ("raw", "_candidate", "_id"),
    ("market", "_id"),
    ("market", "_slug"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "_url"),
    ("source", "_text"),
    ("d", "sn"),
    ("tab", "le"),
    ("to", "ken"),
    ("li", "ve"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("trad", "ing"),
    ("posi", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("recommen", "dation"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_RATIO_FIELDS = (
    "public_evidence_alignment_score",
    "resolution_rule_alignment_score",
    "official_evidence_coverage_score",
    "resolver_consistency_score",
    "contradiction_risk_score",
    "ambiguity_risk_score",
    "min_pass_oracle_alignment_score",
    "min_watch_oracle_alignment_score",
    "max_watch_contradiction_risk_score",
    "max_block_contradiction_risk_score",
    "max_watch_ambiguity_risk_score",
    "max_block_ambiguity_risk_score",
)
_RESULT_DIGEST_FIELDS = (
    "redacted_candidate_ref",
    "public_evidence_alignment_score",
    "resolution_rule_alignment_score",
    "official_evidence_coverage_score",
    "resolver_consistency_score",
    "contradiction_risk_score",
    "ambiguity_risk_score",
    "evidence_observation_count",
    "oracle_alignment_score",
    "min_pass_oracle_alignment_score",
    "min_watch_oracle_alignment_score",
    "max_watch_contradiction_risk_score",
    "max_block_contradiction_risk_score",
    "max_watch_ambiguity_risk_score",
    "max_block_ambiguity_risk_score",
    "support_status",
    "reason_codes",
    "blocker_codes",
    "fact_set_version",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "result_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "min_oracle_alignment_score",
    "average_oracle_alignment_score",
    "max_contradiction_risk_score",
    "max_ambiguity_risk_score",
    "results",
    "fact_set_versions",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_REASON_SUMMARY_CODES = (
    "contradiction_risk_block",
    "ambiguity_risk_block",
    "oracle_alignment_score_below_watch",
    "contradiction_risk_watch",
    "ambiguity_risk_watch",
    "oracle_alignment_score_between_watch_and_pass",
    "oracle_alignment_pass",
)


@dataclass(frozen=True)
class CandidateDecisionOracleAlignmentFacts:
    redacted_candidate_ref: str
    public_evidence_alignment_score: Decimal
    resolution_rule_alignment_score: Decimal
    official_evidence_coverage_score: Decimal
    resolver_consistency_score: Decimal
    contradiction_risk_score: Decimal
    ambiguity_risk_score: Decimal
    evidence_observation_count: Decimal
    min_pass_oracle_alignment_score: Decimal
    min_watch_oracle_alignment_score: Decimal
    max_watch_contradiction_risk_score: Decimal
    max_block_contradiction_risk_score: Decimal
    max_watch_ambiguity_risk_score: Decimal
    max_block_ambiguity_risk_score: Decimal
    fact_set_version: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionOracleAlignmentFacts, "facts")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in _RATIO_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observation_count",
            _normalize_count(
                "evidence_observation_count",
                self.evidence_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "fact_set_version",
            _require_public_string("fact_set_version", self.fact_set_version),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_thresholds(self)
        _require_hard_flags("facts", self)
        reject_candidate_decision_oracle_alignment_unsafe_payload(
            "candidate oracle alignment facts",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionOracleAlignmentResult:
    redacted_candidate_ref: str
    public_evidence_alignment_score: Decimal
    resolution_rule_alignment_score: Decimal
    official_evidence_coverage_score: Decimal
    resolver_consistency_score: Decimal
    contradiction_risk_score: Decimal
    ambiguity_risk_score: Decimal
    evidence_observation_count: Decimal
    oracle_alignment_score: Decimal
    min_pass_oracle_alignment_score: Decimal
    min_watch_oracle_alignment_score: Decimal
    max_watch_contradiction_risk_score: Decimal
    max_block_contradiction_risk_score: Decimal
    max_watch_ambiguity_risk_score: Decimal
    max_block_ambiguity_risk_score: Decimal
    support_status: str
    reason_codes: tuple[str, ...]
    blocker_codes: tuple[str, ...]
    fact_set_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionOracleAlignmentResult, "result")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        for field_name in _RATIO_FIELDS + ("oracle_alignment_score",):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observation_count",
            _normalize_count(
                "evidence_observation_count",
                self.evidence_observation_count,
            ),
        )
        _validate_thresholds(self)
        _require_support_status("support_status", self.support_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "blocker_codes",
            _normalize_reason_codes("blocker_codes", self.blocker_codes),
        )
        object.__setattr__(
            self,
            "fact_set_version",
            _require_public_string("fact_set_version", self.fact_set_version),
        )
        _require_hard_flags("result", self)
        reject_candidate_decision_oracle_alignment_unsafe_payload(
            "candidate oracle alignment result",
            self,
        )
        _validate_result_consistency(self)
        expected_digest = _result_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_oracle_alignment_payload(self)


@dataclass(frozen=True)
class CandidateDecisionOracleAlignmentReport:
    result_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_oracle_alignment_score: Decimal
    average_oracle_alignment_score: Decimal
    max_contradiction_risk_score: Decimal
    max_ambiguity_risk_score: Decimal
    results: tuple[CandidateDecisionOracleAlignmentResult, ...]
    fact_set_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionOracleAlignmentReport, "report")
        for field_name in (
            "result_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_oracle_alignment_score",
            "average_oracle_alignment_score",
            "max_contradiction_risk_score",
            "max_ambiguity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "results", _normalize_results(self.results))
        object.__setattr__(
            self,
            "fact_set_versions",
            _normalize_fact_set_versions(self.fact_set_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        reject_candidate_decision_oracle_alignment_unsafe_payload(
            "candidate oracle alignment report",
            self,
        )
        _validate_report_consistency(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_oracle_alignment_payload(self)


def score_candidate_decision_oracle_alignment(
    facts: CandidateDecisionOracleAlignmentFacts,
) -> CandidateDecisionOracleAlignmentResult:
    if type(facts) is not CandidateDecisionOracleAlignmentFacts:
        raise ValueError("facts must be a CandidateDecisionOracleAlignmentFacts")
    _require_hard_flags("facts", facts)
    reject_candidate_decision_oracle_alignment_unsafe_payload(
        "candidate oracle alignment facts",
        facts,
    )
    score = _oracle_alignment_score(facts)
    blocker_codes = _blocker_codes(facts)
    support_status = _support_status(facts, score, blocker_codes)
    return CandidateDecisionOracleAlignmentResult(
        redacted_candidate_ref=facts.redacted_candidate_ref,
        public_evidence_alignment_score=facts.public_evidence_alignment_score,
        resolution_rule_alignment_score=facts.resolution_rule_alignment_score,
        official_evidence_coverage_score=facts.official_evidence_coverage_score,
        resolver_consistency_score=facts.resolver_consistency_score,
        contradiction_risk_score=facts.contradiction_risk_score,
        ambiguity_risk_score=facts.ambiguity_risk_score,
        evidence_observation_count=facts.evidence_observation_count,
        oracle_alignment_score=score,
        min_pass_oracle_alignment_score=facts.min_pass_oracle_alignment_score,
        min_watch_oracle_alignment_score=facts.min_watch_oracle_alignment_score,
        max_watch_contradiction_risk_score=facts.max_watch_contradiction_risk_score,
        max_block_contradiction_risk_score=facts.max_block_contradiction_risk_score,
        max_watch_ambiguity_risk_score=facts.max_watch_ambiguity_risk_score,
        max_block_ambiguity_risk_score=facts.max_block_ambiguity_risk_score,
        support_status=support_status,
        reason_codes=_result_reason_codes(
            facts.reason_codes,
            facts=facts,
            score=score,
            support_status=support_status,
            blocker_codes=blocker_codes,
        ),
        blocker_codes=blocker_codes,
        fact_set_version=facts.fact_set_version,
    )


def build_candidate_decision_oracle_alignment_report(
    facts_list: tuple[CandidateDecisionOracleAlignmentFacts, ...]
    | list[CandidateDecisionOracleAlignmentFacts],
) -> CandidateDecisionOracleAlignmentReport:
    if type(facts_list) not in (tuple, list):
        raise ValueError("facts_list must be a tuple or list")
    for facts in facts_list:
        if type(facts) is not CandidateDecisionOracleAlignmentFacts:
            raise ValueError("facts_list must contain CandidateDecisionOracleAlignmentFacts")
    results = _normalize_results(
        tuple(score_candidate_decision_oracle_alignment(facts) for facts in facts_list),
    )
    result_count = _count_from_length(results)
    score_sum = _sum_decimal(result.oracle_alignment_score for result in results)
    return CandidateDecisionOracleAlignmentReport(
        result_count=result_count,
        pass_count=_count_status(results, "pass"),
        watch_count=_count_status(results, "watch"),
        blocked_count=_count_status(results, "block"),
        min_oracle_alignment_score=_min_result_decimal(
            results,
            "oracle_alignment_score",
        ),
        average_oracle_alignment_score=(
            ZERO
            if result_count == ZERO
            else _normalize_decimal("average_oracle_alignment_score", score_sum / result_count)
        ),
        max_contradiction_risk_score=_max_result_decimal(
            results,
            "contradiction_risk_score",
        ),
        max_ambiguity_risk_score=_max_result_decimal(results, "ambiguity_risk_score"),
        results=results,
        fact_set_versions=tuple(
            sorted((result.redacted_candidate_ref, result.fact_set_version) for result in results),
        ),
        reason_codes=_report_reason_codes(results),
    )


def candidate_decision_oracle_alignment_payload(
    value: CandidateDecisionOracleAlignmentResult | CandidateDecisionOracleAlignmentReport,
) -> dict[str, Any]:
    if type(value) not in (
        CandidateDecisionOracleAlignmentResult,
        CandidateDecisionOracleAlignmentReport,
    ):
        raise ValueError("value must be an oracle alignment result or report")
    _require_hard_flags("candidate oracle alignment payload", value)
    if type(value) is CandidateDecisionOracleAlignmentResult:
        if value.derived_validation_digest != _result_validation_digest(value):
            raise ValueError("derived_validation_digest must match result fields")
    else:
        if value.derived_validation_digest != _report_validation_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_oracle_alignment_unsafe_payload(
        "candidate oracle alignment payload",
        value,
    )
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    if type(value) is CandidateDecisionOracleAlignmentReport:
        payload["support_status"] = _report_support_status(value.results)
    reject_candidate_decision_oracle_alignment_unsafe_payload(
        "candidate oracle alignment payload",
        payload,
    )
    return payload


def reject_candidate_decision_oracle_alignment_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _oracle_alignment_score(value: object) -> Decimal:
    base_score = (
        getattr(value, "public_evidence_alignment_score")
        + getattr(value, "resolution_rule_alignment_score")
        + getattr(value, "official_evidence_coverage_score")
        + getattr(value, "resolver_consistency_score")
    ) / FOUR
    adjusted_score = (
        base_score
        + (ONE - getattr(value, "contradiction_risk_score"))
        * CONTRADICTION_ALIGNMENT_WEIGHT
        - getattr(value, "ambiguity_risk_score") * AMBIGUITY_RISK_PENALTY_WEIGHT
    )
    if adjusted_score < ZERO:
        return ZERO
    if adjusted_score > ONE:
        return ONE
    return _normalize_unit_decimal("oracle_alignment_score", adjusted_score)


def _blocker_codes(value: object) -> tuple[str, ...]:
    codes: list[str] = []
    if getattr(value, "evidence_observation_count") == ZERO:
        codes.append("public_evidence_observation_missing")
    if (
        getattr(value, "contradiction_risk_score")
        >= getattr(value, "max_block_contradiction_risk_score")
    ):
        codes.append("contradiction_risk_block")
    if getattr(value, "ambiguity_risk_score") >= getattr(
        value,
        "max_block_ambiguity_risk_score",
    ):
        codes.append("ambiguity_risk_block")
    return tuple(codes)


def _support_status(
    value: object,
    score: Decimal,
    blocker_codes: tuple[str, ...],
) -> str:
    if blocker_codes or score < getattr(value, "min_watch_oracle_alignment_score"):
        return "block"
    if (
        score < getattr(value, "min_pass_oracle_alignment_score")
        or getattr(value, "contradiction_risk_score")
        > getattr(value, "max_watch_contradiction_risk_score")
        or getattr(value, "ambiguity_risk_score")
        > getattr(value, "max_watch_ambiguity_risk_score")
    ):
        return "watch"
    return "pass"


def _result_reason_codes(
    existing: tuple[str, ...],
    *,
    facts: CandidateDecisionOracleAlignmentFacts,
    score: Decimal,
    support_status: str,
    blocker_codes: tuple[str, ...],
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_oracle_alignment_score",
        f"support_{support_status}",
        _minimum_reason(
            "public_evidence_alignment",
            facts.public_evidence_alignment_score,
            facts.min_pass_oracle_alignment_score,
            facts.min_watch_oracle_alignment_score,
        ),
        _minimum_reason(
            "resolution_rule_alignment",
            facts.resolution_rule_alignment_score,
            facts.min_pass_oracle_alignment_score,
            facts.min_watch_oracle_alignment_score,
        ),
        _minimum_reason(
            "official_evidence_coverage",
            facts.official_evidence_coverage_score,
            facts.min_pass_oracle_alignment_score,
            facts.min_watch_oracle_alignment_score,
        ),
        _minimum_reason(
            "resolver_consistency",
            facts.resolver_consistency_score,
            facts.min_pass_oracle_alignment_score,
            facts.min_watch_oracle_alignment_score,
        ),
        _risk_reason(
            "contradiction_risk",
            facts.contradiction_risk_score,
            facts.max_watch_contradiction_risk_score,
            facts.max_block_contradiction_risk_score,
        ),
        _risk_reason(
            "ambiguity_risk",
            facts.ambiguity_risk_score,
            facts.max_watch_ambiguity_risk_score,
            facts.max_block_ambiguity_risk_score,
        ),
    ]
    additions.extend(blocker_codes)
    if score < facts.min_watch_oracle_alignment_score:
        additions.append("oracle_alignment_score_below_watch")
    elif score < facts.min_pass_oracle_alignment_score:
        additions.append("oracle_alignment_score_between_watch_and_pass")
    else:
        additions.append("oracle_alignment_pass")
    return _append_reason_codes(existing, tuple(additions))


def _minimum_reason(
    label: str,
    value: Decimal,
    pass_level: Decimal,
    watch_level: Decimal,
) -> str:
    if value >= pass_level:
        return f"{label}_pass"
    if value >= watch_level:
        return f"{label}_watch"
    return f"{label}_block"


def _risk_reason(
    label: str,
    value: Decimal,
    watch_level: Decimal,
    block_level: Decimal,
) -> str:
    if value >= block_level:
        return f"{label}_block"
    if value > watch_level:
        return f"{label}_watch"
    return f"{label}_pass"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _report_reason_codes(
    results: tuple[CandidateDecisionOracleAlignmentResult, ...],
) -> tuple[str, ...]:
    codes = [f"oracle_alignment_report_{_report_support_status(results)}"]
    for result in results:
        for reason_code in result.reason_codes:
            if reason_code in _REPORT_REASON_SUMMARY_CODES and reason_code not in codes:
                codes.append(reason_code)
    if not results:
        codes.append("oracle_alignment_report_empty")
    return tuple(codes)


def _report_support_status(
    results: tuple[CandidateDecisionOracleAlignmentResult, ...],
) -> str:
    if not results or any(result.support_status == "block" for result in results):
        return "block"
    if any(result.support_status == "watch" for result in results):
        return "watch"
    return "pass"


def _validate_thresholds(value: object) -> None:
    if (
        getattr(value, "min_watch_oracle_alignment_score")
        > getattr(value, "min_pass_oracle_alignment_score")
    ):
        raise ValueError("min_watch_oracle_alignment_score must not exceed pass level")
    if (
        getattr(value, "max_watch_contradiction_risk_score")
        > getattr(value, "max_block_contradiction_risk_score")
    ):
        raise ValueError(
            "max_watch_contradiction_risk_score must not exceed block level",
        )
    if (
        getattr(value, "max_watch_ambiguity_risk_score")
        > getattr(value, "max_block_ambiguity_risk_score")
    ):
        raise ValueError("max_watch_ambiguity_risk_score must not exceed block level")


def _validate_result_consistency(
    result: CandidateDecisionOracleAlignmentResult,
) -> None:
    if result.oracle_alignment_score != _oracle_alignment_score(result):
        raise ValueError("oracle_alignment_score must match public evidence inputs")
    expected_blockers = _blocker_codes(result)
    if result.blocker_codes != expected_blockers:
        raise ValueError("blocker_codes must match risk inputs")
    expected_status = _support_status(
        result,
        result.oracle_alignment_score,
        result.blocker_codes,
    )
    if result.support_status != expected_status:
        raise ValueError("support_status must match oracle alignment score")


def _validate_report_consistency(
    report: CandidateDecisionOracleAlignmentReport,
) -> None:
    if report.result_count != _count_from_length(report.results):
        raise ValueError("result_count must match results")
    if report.pass_count != _count_status(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _count_status(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.blocked_count != _count_status(report.results, "block"):
        raise ValueError("blocked_count must match results")
    if report.min_oracle_alignment_score != _min_result_decimal(
        report.results,
        "oracle_alignment_score",
    ):
        raise ValueError("min_oracle_alignment_score must match results")
    score_sum = _sum_decimal(result.oracle_alignment_score for result in report.results)
    expected_average = (
        ZERO
        if report.result_count == ZERO
        else _normalize_decimal("average_oracle_alignment_score", score_sum / report.result_count)
    )
    if report.average_oracle_alignment_score != expected_average:
        raise ValueError("average_oracle_alignment_score must match results")
    if report.max_contradiction_risk_score != _max_result_decimal(
        report.results,
        "contradiction_risk_score",
    ):
        raise ValueError("max_contradiction_risk_score must match results")
    if report.max_ambiguity_risk_score != _max_result_decimal(
        report.results,
        "ambiguity_risk_score",
    ):
        raise ValueError("max_ambiguity_risk_score must match results")
    expected_versions = tuple(
        sorted(
            (result.redacted_candidate_ref, result.fact_set_version)
            for result in report.results
        ),
    )
    if report.fact_set_versions != expected_versions:
        raise ValueError("fact_set_versions must match results")


def _normalize_results(
    value: object,
) -> tuple[CandidateDecisionOracleAlignmentResult, ...]:
    if type(value) is not tuple:
        raise ValueError("results must be a tuple")
    for result in value:
        if type(result) is not CandidateDecisionOracleAlignmentResult:
            raise ValueError("results must contain CandidateDecisionOracleAlignmentResult")
        _require_hard_flags("result", result)
    return tuple(
        sorted(
            value,
            key=lambda result: (
                _STATUS_RANK[result.support_status],
                result.oracle_alignment_score,
                result.redacted_candidate_ref,
            ),
        ),
    )


def _normalize_fact_set_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("fact_set_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("fact_set_versions entries must be pairs")
        redacted_candidate_ref = _require_redacted_candidate_ref(
            "fact_set_versions redacted_candidate_ref",
            item[0],
        )
        fact_set_version = _require_public_string("fact_set_version", item[1])
        normalized.append((redacted_candidate_ref, fact_set_version))
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("fact_set_versions must be sorted")
    return result


def _count_status(
    results: tuple[CandidateDecisionOracleAlignmentResult, ...],
    support_status: str,
) -> Decimal:
    return _count_from_length(
        tuple(result for result in results if result.support_status == support_status),
    )


def _count_from_length(value: tuple[object, ...]) -> Decimal:
    return Decimal(len(value)).quantize(COUNT_QUANTUM)


def _min_result_decimal(
    results: tuple[CandidateDecisionOracleAlignmentResult, ...],
    field_name: str,
) -> Decimal:
    if not results:
        return ZERO
    return min(getattr(result, field_name) for result in results)


def _max_result_decimal(
    results: tuple[CandidateDecisionOracleAlignmentResult, ...],
    field_name: str,
) -> Decimal:
    if not results:
        return ZERO
    return max(getattr(result, field_name) for result in results)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_decimal("total", total)


def _result_validation_digest(result: CandidateDecisionOracleAlignmentResult) -> str:
    return _digest_from_fields(result, _RESULT_DIGEST_FIELDS)


def _report_validation_digest(report: CandidateDecisionOracleAlignmentReport) -> str:
    return _digest_from_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(value, field_name))}"
        for field_name in field_names
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return "{" + ",".join(
            f"{field.name}:{_digest_value(getattr(value, field.name))}"
            for field in fields(value)
            if field.name != "derived_validation_digest"
        ) + "}"
    if type(value) is tuple:
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_support_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SUPPORT_STATUSES:
        raise ValueError(f"{field_name} must be one of {SUPPORT_STATUSES!r}")


def _require_redacted_candidate_ref(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if not value.startswith("redacted-candidate-"):
        raise ValueError(f"{field_name} must be a redacted candidate reference")
    if any(term in value.lower() for term in _UNSAFE_TERMS):
        raise ValueError(f"{field_name} must be a safe redacted candidate reference")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_canonical_digest(value: object) -> None:
    _require_public_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (str, bool):
        return value
    raise ValueError("JSON value must be public data")


__all__ = (
    "SUPPORT_STATUSES",
    "CandidateDecisionOracleAlignmentFacts",
    "CandidateDecisionOracleAlignmentResult",
    "CandidateDecisionOracleAlignmentReport",
    "score_candidate_decision_oracle_alignment",
    "build_candidate_decision_oracle_alignment_report",
    "candidate_decision_oracle_alignment_payload",
    "reject_candidate_decision_oracle_alignment_unsafe_payload",
)
