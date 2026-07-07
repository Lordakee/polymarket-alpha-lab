"""Pure Phase 1 candidate evidence gap score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIMENSION_SCORE_BPS = Decimal("100.000000")
SUPPORT_STATUSES = ("pass", "watch", "block")
SUPPORT_DECISIONS = ("research_next", "watch", "block")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
    ("ht", "tp"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("market", "_id"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIMENSIONS = (
    (
        "official_resolution_source",
        "official_resolution_source_count",
        "required_official_resolution_source_count",
    ),
    (
        "market_terms_rule",
        "market_terms_rule_count",
        "required_market_terms_rule_count",
    ),
    ("fresh_data", "fresh_data_point_count", "required_fresh_data_point_count"),
    (
        "contradiction_check",
        "contradiction_check_count",
        "required_contradiction_check_count",
    ),
    (
        "base_rate_context",
        "base_rate_context_count",
        "required_base_rate_context_count",
    ),
    ("specialist_review", "specialist_review_count", "required_specialist_review_count"),
)
_FACT_COUNT_FIELDS = tuple(field_name for _, field_name, _ in _DIMENSIONS)
_FACT_REQUIRED_FIELDS = tuple(field_name for _, _, field_name in _DIMENSIONS)
_RESULT_DIGEST_FIELDS = (
    "candidate_ref",
    "official_resolution_source_count",
    "required_official_resolution_source_count",
    "market_terms_rule_count",
    "required_market_terms_rule_count",
    "fresh_data_point_count",
    "required_fresh_data_point_count",
    "contradiction_check_count",
    "required_contradiction_check_count",
    "base_rate_context_count",
    "required_base_rate_context_count",
    "specialist_review_count",
    "required_specialist_review_count",
    "official_resolution_source_coverage_ratio",
    "market_terms_rule_coverage_ratio",
    "fresh_data_coverage_ratio",
    "contradiction_check_coverage_ratio",
    "base_rate_context_coverage_ratio",
    "specialist_review_coverage_ratio",
    "evidence_gap_count",
    "aggregate_evidence_score_bps",
    "minimum_pass_score_bps",
    "minimum_watch_score_bps",
    "support_status",
    "support_decision",
    "reason_codes",
    "blocker_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "result_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "average_evidence_score_bps",
    "max_evidence_gap_count",
    "results",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionEvidenceGapFacts:
    candidate_ref: str
    official_resolution_source_count: Decimal
    required_official_resolution_source_count: Decimal
    market_terms_rule_count: Decimal
    required_market_terms_rule_count: Decimal
    fresh_data_point_count: Decimal
    required_fresh_data_point_count: Decimal
    contradiction_check_count: Decimal
    required_contradiction_check_count: Decimal
    base_rate_context_count: Decimal
    required_base_rate_context_count: Decimal
    specialist_review_count: Decimal
    required_specialist_review_count: Decimal
    minimum_pass_score_bps: Decimal
    minimum_watch_score_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("candidate_ref", self.candidate_ref)
        for field_name in _FACT_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in _FACT_REQUIRED_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_pass_score_bps",
            _normalize_nonnegative_decimal(
                "minimum_pass_score_bps",
                self.minimum_pass_score_bps,
            ),
        )
        object.__setattr__(
            self,
            "minimum_watch_score_bps",
            _normalize_nonnegative_decimal(
                "minimum_watch_score_bps",
                self.minimum_watch_score_bps,
            ),
        )
        if self.minimum_watch_score_bps > self.minimum_pass_score_bps:
            raise ValueError("minimum_watch_score_bps must not exceed pass level")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_candidate_decision_evidence_gap_unsafe_payload(
            "candidate evidence gap facts",
            self,
        )
        _require_paper_flags("candidate evidence gap facts", self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceGapResult:
    candidate_ref: str
    official_resolution_source_count: Decimal
    required_official_resolution_source_count: Decimal
    market_terms_rule_count: Decimal
    required_market_terms_rule_count: Decimal
    fresh_data_point_count: Decimal
    required_fresh_data_point_count: Decimal
    contradiction_check_count: Decimal
    required_contradiction_check_count: Decimal
    base_rate_context_count: Decimal
    required_base_rate_context_count: Decimal
    specialist_review_count: Decimal
    required_specialist_review_count: Decimal
    official_resolution_source_coverage_ratio: Decimal
    market_terms_rule_coverage_ratio: Decimal
    fresh_data_coverage_ratio: Decimal
    contradiction_check_coverage_ratio: Decimal
    base_rate_context_coverage_ratio: Decimal
    specialist_review_coverage_ratio: Decimal
    evidence_gap_count: Decimal
    aggregate_evidence_score_bps: Decimal
    minimum_pass_score_bps: Decimal
    minimum_watch_score_bps: Decimal
    support_status: str
    support_decision: str
    reason_codes: tuple[str, ...]
    blocker_codes: tuple[str, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("candidate_ref", self.candidate_ref)
        for field_name in _FACT_COUNT_FIELDS + _FACT_REQUIRED_FIELDS + (
            "evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in _FACT_REQUIRED_FIELDS:
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        for field_name in (
            "official_resolution_source_coverage_ratio",
            "market_terms_rule_coverage_ratio",
            "fresh_data_coverage_ratio",
            "contradiction_check_coverage_ratio",
            "base_rate_context_coverage_ratio",
            "specialist_review_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_evidence_score_bps",
            "minimum_pass_score_bps",
            "minimum_watch_score_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_watch_score_bps > self.minimum_pass_score_bps:
            raise ValueError("minimum_watch_score_bps must not exceed pass level")
        _require_choice("support_status", self.support_status, SUPPORT_STATUSES)
        _require_choice("support_decision", self.support_decision, SUPPORT_DECISIONS)
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
        _validate_result_consistency(self)
        reject_candidate_decision_evidence_gap_unsafe_payload(
            "candidate evidence gap result",
            self,
        )
        _require_paper_flags("candidate evidence gap result", self)
        expected_digest = _result_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_evidence_gap_payload(self)


@dataclass(frozen=True)
class CandidateDecisionEvidenceGapReport:
    result_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_evidence_score_bps: Decimal
    max_evidence_gap_count: Decimal
    results: tuple[CandidateDecisionEvidenceGapResult, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "result_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_evidence_score_bps",
            _normalize_nonnegative_decimal(
                "average_evidence_score_bps",
                self.average_evidence_score_bps,
            ),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        reject_candidate_decision_evidence_gap_unsafe_payload(
            "candidate evidence gap report",
            self,
        )
        _require_paper_flags("candidate evidence gap report", self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_evidence_gap_payload(self)


def score_candidate_decision_evidence_gap(
    facts: CandidateDecisionEvidenceGapFacts,
) -> CandidateDecisionEvidenceGapResult:
    if type(facts) is not CandidateDecisionEvidenceGapFacts:
        raise ValueError("facts must be a CandidateDecisionEvidenceGapFacts")
    reject_candidate_decision_evidence_gap_unsafe_payload(
        "candidate evidence gap facts",
        facts,
    )
    _require_paper_flags("candidate evidence gap facts", facts)

    ratios = tuple(
        _coverage_ratio(
            getattr(facts, count_field),
            getattr(facts, required_field),
        )
        for _, count_field, required_field in _DIMENSIONS
    )
    gap_count = _sum_decimal(
        _gap_count(getattr(facts, count_field), getattr(facts, required_field))
        for _, count_field, required_field in _DIMENSIONS
    )
    aggregate_score = _aggregate_score_bps(ratios)
    blocker_codes = _blocker_codes(facts)
    support_status = _support_status(
        aggregate_score,
        facts.minimum_pass_score_bps,
        facts.minimum_watch_score_bps,
        blocker_codes,
    )

    return CandidateDecisionEvidenceGapResult(
        candidate_ref=facts.candidate_ref,
        official_resolution_source_count=facts.official_resolution_source_count,
        required_official_resolution_source_count=(
            facts.required_official_resolution_source_count
        ),
        market_terms_rule_count=facts.market_terms_rule_count,
        required_market_terms_rule_count=facts.required_market_terms_rule_count,
        fresh_data_point_count=facts.fresh_data_point_count,
        required_fresh_data_point_count=facts.required_fresh_data_point_count,
        contradiction_check_count=facts.contradiction_check_count,
        required_contradiction_check_count=facts.required_contradiction_check_count,
        base_rate_context_count=facts.base_rate_context_count,
        required_base_rate_context_count=facts.required_base_rate_context_count,
        specialist_review_count=facts.specialist_review_count,
        required_specialist_review_count=facts.required_specialist_review_count,
        official_resolution_source_coverage_ratio=ratios[0],
        market_terms_rule_coverage_ratio=ratios[1],
        fresh_data_coverage_ratio=ratios[2],
        contradiction_check_coverage_ratio=ratios[3],
        base_rate_context_coverage_ratio=ratios[4],
        specialist_review_coverage_ratio=ratios[5],
        evidence_gap_count=gap_count,
        aggregate_evidence_score_bps=aggregate_score,
        minimum_pass_score_bps=facts.minimum_pass_score_bps,
        minimum_watch_score_bps=facts.minimum_watch_score_bps,
        support_status=support_status,
        support_decision=_support_decision(support_status),
        reason_codes=_reason_codes(
            facts.reason_codes,
            ratios=ratios,
            support_status=support_status,
            aggregate_score=aggregate_score,
            minimum_pass_score_bps=facts.minimum_pass_score_bps,
            minimum_watch_score_bps=facts.minimum_watch_score_bps,
            blocker_codes=blocker_codes,
        ),
        blocker_codes=blocker_codes,
    )


def build_candidate_decision_evidence_gap_report(
    facts_list: tuple[CandidateDecisionEvidenceGapFacts, ...]
    | list[CandidateDecisionEvidenceGapFacts],
) -> CandidateDecisionEvidenceGapReport:
    if type(facts_list) not in (tuple, list):
        raise ValueError("facts_list must be a tuple or list")
    for facts in facts_list:
        if type(facts) is not CandidateDecisionEvidenceGapFacts:
            raise ValueError("facts_list must contain CandidateDecisionEvidenceGapFacts")
    results = _normalize_results(
        tuple(score_candidate_decision_evidence_gap(facts) for facts in facts_list),
    )
    result_count = _count_from_length(results)
    pass_count = _count_status(results, "pass")
    watch_count = _count_status(results, "watch")
    blocked_count = _count_status(results, "block")
    score_sum = _sum_decimal(result.aggregate_evidence_score_bps for result in results)
    gap_values = tuple(result.evidence_gap_count for result in results)

    return CandidateDecisionEvidenceGapReport(
        result_count=result_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_evidence_score_bps=(
            ZERO if result_count == ZERO else _normalize_decimal("average", score_sum / result_count)
        ),
        max_evidence_gap_count=ZERO if not gap_values else max(gap_values),
        results=results,
        reason_codes=_report_reason_codes(
            pass_count=pass_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
    )


def candidate_decision_evidence_gap_payload(
    value: CandidateDecisionEvidenceGapResult | CandidateDecisionEvidenceGapReport,
) -> dict[str, Any]:
    if type(value) not in (
        CandidateDecisionEvidenceGapResult,
        CandidateDecisionEvidenceGapReport,
    ):
        raise ValueError("value must be an evidence gap result or report")
    _require_paper_flags("candidate evidence gap payload", value)
    if type(value) is CandidateDecisionEvidenceGapResult:
        if value.derived_validation_digest != _result_validation_digest(value):
            raise ValueError("derived_validation_digest must match result fields")
    else:
        if value.derived_validation_digest != _report_validation_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_evidence_gap_unsafe_payload(
        "candidate evidence gap payload",
        value,
    )
    return _json_ready(asdict(value))


def reject_candidate_decision_evidence_gap_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _coverage_ratio(count: Decimal, required_count: Decimal) -> Decimal:
    if count >= required_count:
        return ONE
    return _normalize_unit_decimal("coverage_ratio", count / required_count)


def _gap_count(count: Decimal, required_count: Decimal) -> Decimal:
    return _normalize_count("gap_count", max(required_count - count, ZERO))


def _aggregate_score_bps(ratios: tuple[Decimal, ...]) -> Decimal:
    return _normalize_nonnegative_decimal(
        "aggregate_evidence_score_bps",
        _sum_decimal(ratio * DIMENSION_SCORE_BPS for ratio in ratios),
    )


def _blocker_codes(value: object) -> tuple[str, ...]:
    codes: list[str] = []
    if getattr(value, "official_resolution_source_count") == ZERO:
        codes.append("official_resolution_source_missing")
    if getattr(value, "market_terms_rule_count") == ZERO:
        codes.append("market_terms_rule_missing")
    return tuple(codes)


def _support_status(
    aggregate_score: Decimal,
    minimum_pass_score_bps: Decimal,
    minimum_watch_score_bps: Decimal,
    blocker_codes: tuple[str, ...],
) -> str:
    if blocker_codes:
        return "block"
    if aggregate_score < minimum_watch_score_bps:
        return "block"
    if aggregate_score < minimum_pass_score_bps:
        return "watch"
    return "pass"


def _support_decision(support_status: str) -> str:
    if support_status == "pass":
        return "research_next"
    if support_status == "watch":
        return "watch"
    if support_status == "block":
        return "block"
    raise ValueError("support_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    ratios: tuple[Decimal, ...],
    support_status: str,
    aggregate_score: Decimal,
    minimum_pass_score_bps: Decimal,
    minimum_watch_score_bps: Decimal,
    blocker_codes: tuple[str, ...],
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_evidence_gap_score",
        f"support_{support_status}",
    ]
    for index, (dimension_name, _, _) in enumerate(_DIMENSIONS):
        if ratios[index] >= ONE:
            additions.append(f"{dimension_name}_coverage_met")
        else:
            additions.append(f"{dimension_name}_gap")
    additions.extend(blocker_codes)
    if aggregate_score >= minimum_pass_score_bps and not blocker_codes:
        additions.append("minimum_pass_score_met")
    elif aggregate_score >= minimum_watch_score_bps and not blocker_codes:
        additions.append("score_between_watch_and_pass")
    elif blocker_codes and aggregate_score >= minimum_watch_score_bps:
        additions.append("blocking_evidence_source_missing")
    else:
        additions.append("score_below_watch_threshold")
    return _append_reason_codes(existing, tuple(additions))


def _report_reason_codes(
    *,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> tuple[str, ...]:
    additions = ["candidate_decision_evidence_gap_report"]
    if blocked_count > ZERO:
        additions.append("blocked_support_present")
    if watch_count > ZERO:
        additions.append("watch_support_present")
    if pass_count > ZERO:
        additions.append("pass_support_present")
    if pass_count == watch_count == blocked_count == ZERO:
        additions.append("empty_report")
    return tuple(additions)


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_result_consistency(result: CandidateDecisionEvidenceGapResult) -> None:
    ratios = tuple(
        _coverage_ratio(
            getattr(result, count_field),
            getattr(result, required_field),
        )
        for _, count_field, required_field in _DIMENSIONS
    )
    for index, (dimension_name, _, _) in enumerate(_DIMENSIONS):
        ratio_field = f"{dimension_name}_coverage_ratio"
        if getattr(result, ratio_field) != ratios[index]:
            raise ValueError(f"{ratio_field} must match evidence counts")
    expected_gap_count = _sum_decimal(
        _gap_count(getattr(result, count_field), getattr(result, required_field))
        for _, count_field, required_field in _DIMENSIONS
    )
    if result.evidence_gap_count != expected_gap_count:
        raise ValueError("evidence_gap_count must match evidence counts")
    if result.aggregate_evidence_score_bps != _aggregate_score_bps(ratios):
        raise ValueError("aggregate_evidence_score_bps must match coverage ratios")
    if result.blocker_codes != _blocker_codes(result):
        raise ValueError("blocker_codes must match evidence counts")
    if result.support_status != _support_status(
        result.aggregate_evidence_score_bps,
        result.minimum_pass_score_bps,
        result.minimum_watch_score_bps,
        result.blocker_codes,
    ):
        raise ValueError("support_status must match aggregate score")
    if result.support_decision != _support_decision(result.support_status):
        raise ValueError("support_decision must match support_status")


def _validate_report_consistency(report: CandidateDecisionEvidenceGapReport) -> None:
    if report.result_count != _count_from_length(report.results):
        raise ValueError("result_count must match results")
    if report.pass_count != _count_status(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _count_status(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.blocked_count != _count_status(report.results, "block"):
        raise ValueError("blocked_count must match results")
    score_sum = _sum_decimal(result.aggregate_evidence_score_bps for result in report.results)
    expected_average = (
        ZERO
        if report.result_count == ZERO
        else _normalize_decimal("average", score_sum / report.result_count)
    )
    if report.average_evidence_score_bps != expected_average:
        raise ValueError("average_evidence_score_bps must match results")
    gap_values = tuple(result.evidence_gap_count for result in report.results)
    expected_gap = ZERO if not gap_values else max(gap_values)
    if report.max_evidence_gap_count != expected_gap:
        raise ValueError("max_evidence_gap_count must match results")


def _normalize_results(value: object) -> tuple[CandidateDecisionEvidenceGapResult, ...]:
    if type(value) is not tuple:
        raise ValueError("results must be a tuple")
    for result in value:
        if type(result) is not CandidateDecisionEvidenceGapResult:
            raise ValueError("results must contain CandidateDecisionEvidenceGapResult")
        _require_paper_flags("candidate evidence gap result", result)
    return tuple(
        sorted(
            value,
            key=lambda result: (
                _STATUS_RANK[result.support_status],
                result.aggregate_evidence_score_bps,
                result.candidate_ref,
            ),
        ),
    )


def _count_status(
    results: tuple[CandidateDecisionEvidenceGapResult, ...],
    support_status: str,
) -> Decimal:
    return _count_from_length(
        tuple(result for result in results if result.support_status == support_status),
    )


def _count_from_length(value: tuple[object, ...]) -> Decimal:
    return Decimal(len(value)).quantize(COUNT_QUANTUM)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_decimal("total", total)


def _result_validation_digest(result: CandidateDecisionEvidenceGapResult) -> str:
    return _digest_from_fields(result, _RESULT_DIGEST_FIELDS)


def _report_validation_digest(report: CandidateDecisionEvidenceGapReport) -> str:
    return _digest_from_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(value, field_name))}"
        for field_name in field_names
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return "{" + ",".join(
            f"{field.name}:{_digest_value(getattr(value, field.name))}"
            for field in fields(value)
            if field.name != "derived_validation_digest"
        ) + "}"
    if isinstance(value, tuple):
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
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_redacted_ref(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith("redacted-candidate-"):
        raise ValueError(f"{field_name} must be a redacted candidate reference")
    if any(term in value.lower() for term in _UNSAFE_TERMS):
        raise ValueError(f"{field_name} must be a safe redacted candidate reference")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
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
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool):
        return value
    raise ValueError("JSON value must be public data")


__all__ = (
    "SUPPORT_STATUSES",
    "SUPPORT_DECISIONS",
    "CandidateDecisionEvidenceGapFacts",
    "CandidateDecisionEvidenceGapResult",
    "CandidateDecisionEvidenceGapReport",
    "score_candidate_decision_evidence_gap",
    "build_candidate_decision_evidence_gap_report",
    "candidate_decision_evidence_gap_payload",
    "reject_candidate_decision_evidence_gap_unsafe_payload",
)
