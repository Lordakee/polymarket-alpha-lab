"""Pure manual decision-readiness gate report."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-decision-readiness-gate-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SEVEN = Decimal("7.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_CANDIDATES_REASON = "decision_readiness_gate_no_candidates"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "min_readiness_score",
    "gate_status",
    "manual_decision_review_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_PRIORITY = (
    "evidence_item_count_block",
    "independent_source_count_block",
    "source_agreement_block",
    "source_conflict_block",
    "liquidity_sanity_block",
    "cost_sanity_block",
    "review_coverage_block",
    "unresolved_review_block",
    "decision_readiness_gate_block",
    "evidence_item_count_watch",
    "independent_source_count_watch",
    "source_agreement_watch",
    "source_conflict_watch",
    "liquidity_sanity_watch",
    "cost_sanity_watch",
    "review_coverage_watch",
    "unresolved_review_watch",
    "decision_readiness_gate_watch",
    "decision_readiness_gate_pass",
    NO_CANDIDATES_REASON,
)
UNSAFE_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "private" "_" "key",
    "api" "_" "key",
    "sec" "ret",
    "po" "sition",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "req" "uests",
    "ht" "tp",
    "sock" "et",
    "sub" "process",
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessGateConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION
    )
    min_evidence_item_count: Decimal = Decimal("3.000000")
    evidence_item_count_pass_floor: Decimal = Decimal("4.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    independent_source_count_pass_floor: Decimal = Decimal("3.000000")
    source_agreement_watch_floor: Decimal = Decimal("0.750000")
    source_agreement_block_floor: Decimal = Decimal("0.500000")
    source_conflict_watch_ceiling: Decimal = Decimal("0.300000")
    source_conflict_block_ceiling: Decimal = Decimal("0.600000")
    liquidity_sanity_watch_floor: Decimal = Decimal("0.700000")
    liquidity_sanity_block_floor: Decimal = Decimal("0.400000")
    cost_sanity_watch_floor: Decimal = Decimal("0.700000")
    cost_sanity_block_floor: Decimal = Decimal("0.400000")
    review_coverage_watch_floor: Decimal = Decimal("0.750000")
    review_coverage_block_floor: Decimal = Decimal("0.500000")
    unresolved_review_watch_ceiling: Decimal = Decimal("0.000000")
    unresolved_review_block_ceiling: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessGateConfig, "config")
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "min_evidence_item_count",
            "evidence_item_count_pass_floor",
            "min_independent_source_count",
            "independent_source_count_pass_floor",
            "unresolved_review_watch_ceiling",
            "unresolved_review_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_agreement_watch_floor",
            "source_agreement_block_floor",
            "source_conflict_watch_ceiling",
            "source_conflict_block_ceiling",
            "liquidity_sanity_watch_floor",
            "liquidity_sanity_block_floor",
            "cost_sanity_watch_floor",
            "cost_sanity_block_floor",
            "review_coverage_watch_floor",
            "review_coverage_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_item_count_pass_floor",
            self.evidence_item_count_pass_floor,
            self.min_evidence_item_count,
        )
        _require_at_least(
            "independent_source_count_pass_floor",
            self.independent_source_count_pass_floor,
            self.min_independent_source_count,
        )
        _require_at_least(
            "source_agreement_watch_floor",
            self.source_agreement_watch_floor,
            self.source_agreement_block_floor,
        )
        _require_at_most(
            "source_conflict_watch_ceiling",
            self.source_conflict_watch_ceiling,
            self.source_conflict_block_ceiling,
        )
        _require_at_least(
            "liquidity_sanity_watch_floor",
            self.liquidity_sanity_watch_floor,
            self.liquidity_sanity_block_floor,
        )
        _require_at_least(
            "cost_sanity_watch_floor",
            self.cost_sanity_watch_floor,
            self.cost_sanity_block_floor,
        )
        _require_at_least(
            "review_coverage_watch_floor",
            self.review_coverage_watch_floor,
            self.review_coverage_block_floor,
        )
        _require_at_most(
            "unresolved_review_watch_ceiling",
            self.unresolved_review_watch_ceiling,
            self.unresolved_review_block_ceiling,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessGateCandidate(_FinalDataclass):
    candidate_ref: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    source_agreement_score: Decimal
    source_conflict_score: Decimal
    liquidity_sanity_score: Decimal
    cost_sanity_score: Decimal
    review_coverage_score: Decimal
    unresolved_review_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessGateCandidate, "candidate")
        _require_public_text("candidate_ref", self.candidate_ref)
        for field_name in (
            "evidence_item_count",
            "independent_source_count",
            "unresolved_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError("independent_source_count must not exceed evidence_item_count")
        for field_name in (
            "source_agreement_score",
            "source_conflict_score",
            "liquidity_sanity_score",
            "cost_sanity_score",
            "review_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessGateRow(_FinalDataclass):
    candidate_ref: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    source_agreement_score: Decimal
    source_conflict_score: Decimal
    liquidity_sanity_score: Decimal
    cost_sanity_score: Decimal
    review_coverage_score: Decimal
    unresolved_review_count: Decimal
    evidence_coverage_ratio: Decimal
    independent_source_ratio: Decimal
    source_consensus_score: Decimal
    readiness_score: Decimal
    gate_status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessGateRow, "row")
        _require_public_text("candidate_ref", self.candidate_ref)
        for field_name in (
            "evidence_item_count",
            "independent_source_count",
            "unresolved_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError("independent_source_count must not exceed evidence_item_count")
        for field_name in (
            "source_agreement_score",
            "source_conflict_score",
            "liquidity_sanity_score",
            "cost_sanity_score",
            "review_coverage_score",
            "evidence_coverage_ratio",
            "independent_source_ratio",
            "source_consensus_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        _require_manual_state("manual_decision_review_state", self.manual_decision_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _require_hard_phase_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionReadinessGateReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_readiness_score: Decimal | None
    gate_status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyDecisionReadinessGateRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionReadinessGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_readiness_score is not None:
            object.__setattr__(
                self,
                "min_readiness_score",
                _normalize_ratio("min_readiness_score", self.min_readiness_score),
            )
        _require_status("gate_status", self.gate_status)
        _require_manual_state("manual_decision_review_state", self.manual_decision_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)


def build_research_strategy_decision_readiness_gate_report(
    candidates: Iterable[ResearchStrategyDecisionReadinessGateCandidate],
    *,
    config: ResearchStrategyDecisionReadinessGateConfig,
    generated_at: datetime,
) -> ResearchStrategyDecisionReadinessGateReport:
    if type(config) is not ResearchStrategyDecisionReadinessGateConfig:
        raise ValueError("config must be a ResearchStrategyDecisionReadinessGateConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in candidate_rows),
            key=_row_sort_key,
        ),
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "min_readiness_score": (
            None if not rows else min(row.readiness_score for row in rows)
        ),
        "gate_status": _report_status(rows),
        "manual_decision_review_state": _manual_state(_report_status(rows)),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDecisionReadinessGateReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_decision_readiness_gate_report_payload(
    report: ResearchStrategyDecisionReadinessGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDecisionReadinessGateReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyDecisionReadinessGateReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    return payload


def research_strategy_decision_readiness_gate_report_digest(
    report: ResearchStrategyDecisionReadinessGateReport,
) -> dict[str, Any]:
    payload = research_strategy_decision_readiness_gate_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_candidate(
    candidate: ResearchStrategyDecisionReadinessGateCandidate,
    *,
    config: ResearchStrategyDecisionReadinessGateConfig,
) -> ResearchStrategyDecisionReadinessGateRow:
    evidence_coverage_ratio = _capped_ratio(
        candidate.evidence_item_count,
        config.evidence_item_count_pass_floor,
    )
    independent_source_ratio = _capped_ratio(
        candidate.independent_source_count,
        config.independent_source_count_pass_floor,
    )
    source_consensus_score = _source_consensus_score(
        candidate.source_agreement_score,
        candidate.source_conflict_score,
    )
    reason_codes = _row_reason_codes(candidate, config=config)
    row_values = {
        "candidate_ref": candidate.candidate_ref,
        "evidence_item_count": candidate.evidence_item_count,
        "independent_source_count": candidate.independent_source_count,
        "source_agreement_score": candidate.source_agreement_score,
        "source_conflict_score": candidate.source_conflict_score,
        "liquidity_sanity_score": candidate.liquidity_sanity_score,
        "cost_sanity_score": candidate.cost_sanity_score,
        "review_coverage_score": candidate.review_coverage_score,
        "unresolved_review_count": candidate.unresolved_review_count,
        "evidence_coverage_ratio": evidence_coverage_ratio,
        "independent_source_ratio": independent_source_ratio,
        "source_consensus_score": source_consensus_score,
        "readiness_score": _readiness_score(
            (
                evidence_coverage_ratio,
                independent_source_ratio,
                candidate.source_agreement_score,
                _conflict_clear_score(candidate.source_conflict_score),
                candidate.liquidity_sanity_score,
                candidate.cost_sanity_score,
                candidate.review_coverage_score,
            ),
        ),
        "gate_status": _row_status(reason_codes),
        "manual_decision_review_state": _manual_state(_row_status(reason_codes)),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDecisionReadinessGateRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    candidate: ResearchStrategyDecisionReadinessGateCandidate,
    *,
    config: ResearchStrategyDecisionReadinessGateConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if candidate.evidence_item_count < config.min_evidence_item_count:
        block_reasons.append("evidence_item_count_block")
    elif candidate.evidence_item_count < config.evidence_item_count_pass_floor:
        watch_reasons.append("evidence_item_count_watch")
    if candidate.independent_source_count < config.min_independent_source_count:
        block_reasons.append("independent_source_count_block")
    elif candidate.independent_source_count < config.independent_source_count_pass_floor:
        watch_reasons.append("independent_source_count_watch")
    if candidate.source_agreement_score < config.source_agreement_block_floor:
        block_reasons.append("source_agreement_block")
    elif candidate.source_agreement_score < config.source_agreement_watch_floor:
        watch_reasons.append("source_agreement_watch")
    if candidate.source_conflict_score >= config.source_conflict_block_ceiling:
        block_reasons.append("source_conflict_block")
    elif candidate.source_conflict_score >= config.source_conflict_watch_ceiling:
        watch_reasons.append("source_conflict_watch")
    if candidate.liquidity_sanity_score < config.liquidity_sanity_block_floor:
        block_reasons.append("liquidity_sanity_block")
    elif candidate.liquidity_sanity_score < config.liquidity_sanity_watch_floor:
        watch_reasons.append("liquidity_sanity_watch")
    if candidate.cost_sanity_score < config.cost_sanity_block_floor:
        block_reasons.append("cost_sanity_block")
    elif candidate.cost_sanity_score < config.cost_sanity_watch_floor:
        watch_reasons.append("cost_sanity_watch")
    if candidate.review_coverage_score < config.review_coverage_block_floor:
        block_reasons.append("review_coverage_block")
    elif candidate.review_coverage_score < config.review_coverage_watch_floor:
        watch_reasons.append("review_coverage_watch")
    if candidate.unresolved_review_count >= config.unresolved_review_block_ceiling:
        block_reasons.append("unresolved_review_block")
    elif candidate.unresolved_review_count > config.unresolved_review_watch_ceiling:
        watch_reasons.append("unresolved_review_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("decision_readiness_gate_pass",)
    return _normalize_reason_codes(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyDecisionReadinessGateRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_state(status: str) -> str:
    if status == "block":
        return "manual_decision_review_block"
    if status == "watch":
        return "manual_decision_review_watch"
    return "manual_decision_review_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDecisionReadinessGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "decision_readiness_gate_pass"
    )
    return _normalize_reason_codes((*values, f"decision_readiness_gate_{status}"))


def _source_consensus_score(source_agreement_score: Decimal, source_conflict_score: Decimal) -> Decimal:
    return _readiness_score(
        (source_agreement_score, _conflict_clear_score(source_conflict_score)),
        denominator=TWO,
    )


def _conflict_clear_score(source_conflict_score: Decimal) -> Decimal:
    return _quantize(ONE - source_conflict_score)


def _readiness_score(
    values: tuple[Decimal, ...],
    *,
    denominator: Decimal = SEVEN,
) -> Decimal:
    return _ratio(_sum_decimal(values), denominator)


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyDecisionReadinessGateCandidate],
) -> tuple[ResearchStrategyDecisionReadinessGateCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not ResearchStrategyDecisionReadinessGateCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyDecisionReadinessGateCandidate",
            )
        _require_hard_phase_flags("candidate", candidate)
        if candidate.candidate_ref in seen:
            raise ValueError("candidate_ref values must be unique")
        seen.add(candidate.candidate_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyDecisionReadinessGateRow],
) -> tuple[ResearchStrategyDecisionReadinessGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDecisionReadinessGateRow:
            raise ValueError("rows must contain ResearchStrategyDecisionReadinessGateRow")
        _require_hard_phase_flags("row", row)
        if row.candidate_ref in seen:
            raise ValueError("candidate_ref values must be unique")
        seen.add(row.candidate_ref)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyDecisionReadinessGateRow) -> None:
    if row.source_consensus_score != _source_consensus_score(
        row.source_agreement_score,
        row.source_conflict_score,
    ):
        raise ValueError("source_consensus_score must match source inputs")
    expected_readiness = _readiness_score(
        (
            row.evidence_coverage_ratio,
            row.independent_source_ratio,
            row.source_agreement_score,
            _conflict_clear_score(row.source_conflict_score),
            row.liquidity_sanity_score,
            row.cost_sanity_score,
            row.review_coverage_score,
        ),
    )
    if row.readiness_score != expected_readiness:
        raise ValueError("readiness_score must match component scores")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.manual_decision_review_state != _manual_state(row.gate_status):
        raise ValueError("manual_decision_review_state must match gate_status")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyDecisionReadinessGateReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_min = None if not report.rows else min(row.readiness_score for row in report.rows)
    if report.min_readiness_score != expected_min:
        raise ValueError("min_readiness_score must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.manual_decision_review_state != _manual_state(report.gate_status):
        raise ValueError("manual_decision_review_state must match gate_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchStrategyDecisionReadinessGateRow) -> dict[str, Any]:
    return {
        "candidate_ref": row.candidate_ref,
        "evidence_item_count": row.evidence_item_count,
        "independent_source_count": row.independent_source_count,
        "source_agreement_score": row.source_agreement_score,
        "source_conflict_score": row.source_conflict_score,
        "liquidity_sanity_score": row.liquidity_sanity_score,
        "cost_sanity_score": row.cost_sanity_score,
        "review_coverage_score": row.review_coverage_score,
        "unresolved_review_count": row.unresolved_review_count,
        "evidence_coverage_ratio": row.evidence_coverage_ratio,
        "independent_source_ratio": row.independent_source_ratio,
        "source_consensus_score": row.source_consensus_score,
        "readiness_score": row.readiness_score,
        "gate_status": row.gate_status,
        "manual_decision_review_state": row.manual_decision_review_state,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyDecisionReadinessGateReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "min_readiness_score": report.min_readiness_score,
        "gate_status": report.gate_status,
        "manual_decision_review_state": report.manual_decision_review_state,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_sort_key(row: ResearchStrategyDecisionReadinessGateRow) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.gate_status], row.readiness_score, row.candidate_ref)


def _status_count(
    rows: tuple[ResearchStrategyDecisionReadinessGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        compact = "".join(part for part in reason_code if part != "_")
        if not compact.isalnum() or reason_code.lower() != reason_code:
            raise ValueError("reason_codes must be lowercase snake case")
    normalized = tuple(sorted(dict.fromkeys(reason_codes), key=_reason_sort_key))
    if "decision_readiness_gate_pass" in normalized and len(normalized) != 1:
        raise ValueError("decision_readiness_gate_pass must stand alone")
    if NO_CANDIDATES_REASON in normalized and len(normalized) != 1:
        raise ValueError("no candidates reason must stand alone")
    return normalized


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE:
        return ONE
    return value


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_at_least(name: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{name} must be at least its paired floor")


def _require_at_most(name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{name} must be at most its paired ceiling")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_manual_state(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in {
        "manual_decision_review_ready",
        "manual_decision_review_watch",
        "manual_decision_review_block",
    }:
        raise ValueError(f"{name} must be a manual decision review state")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_text("payload key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategyDecisionReadinessGateCandidate",
    "ResearchStrategyDecisionReadinessGateConfig",
    "ResearchStrategyDecisionReadinessGateReport",
    "ResearchStrategyDecisionReadinessGateRow",
    "build_research_strategy_decision_readiness_gate_report",
    "research_strategy_decision_readiness_gate_report_digest",
    "research_strategy_decision_readiness_gate_report_payload",
)
