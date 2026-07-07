"""Phase 1 readonly candidate triage report for Polymarket strategy research."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_MARKET_CANDIDATE_TRIAGE_V2_CONFIG_VERSION = (
    "strategy-market-candidate-triage-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

TRIAGE_BUCKETS = ("promote", "watch", "block", "research-needed")
NEXT_STEP_BY_BUCKET = {
    "promote": "promote_to_phase_1_packet",
    "watch": "keep_on_watchlist",
    "block": "block_until_constraints_clear",
    "research-needed": "collect_more_public_evidence",
}

UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV2Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_CANDIDATE_TRIAGE_V2_CONFIG_VERSION
    minimum_promote_cost_adjusted_edge: Decimal = Decimal("0.050000")
    minimum_watch_cost_adjusted_edge: Decimal = Decimal("0.010000")
    maximum_cost_break_even_probability: Decimal = Decimal("0.950000")
    minimum_promote_evidence_quality_score: Decimal = Decimal("0.750000")
    minimum_watch_evidence_quality_score: Decimal = Decimal("0.550000")
    minimum_specialist_review_count: Decimal = Decimal("2.000000")
    minimum_specialist_quorum_ratio: Decimal = Decimal("0.666667")
    minimum_promote_liquidity_exit_feasibility_score: Decimal = Decimal("0.650000")
    minimum_watch_liquidity_exit_feasibility_score: Decimal = Decimal("0.450000")
    maximum_promote_resolution_risk_score: Decimal = Decimal("0.350000")
    maximum_watch_resolution_risk_score: Decimal = Decimal("0.550000")
    maximum_promote_category_exposure_score: Decimal = Decimal("0.350000")
    maximum_watch_category_exposure_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "minimum_promote_cost_adjusted_edge",
            "minimum_watch_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_cost_break_even_probability",
            "minimum_promote_evidence_quality_score",
            "minimum_watch_evidence_quality_score",
            "minimum_specialist_quorum_ratio",
            "minimum_promote_liquidity_exit_feasibility_score",
            "minimum_watch_liquidity_exit_feasibility_score",
            "maximum_promote_resolution_risk_score",
            "maximum_watch_resolution_risk_score",
            "maximum_promote_category_exposure_score",
            "maximum_watch_category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_specialist_review_count",
            _normalize_count(
                "minimum_specialist_review_count",
                self.minimum_specialist_review_count,
            ),
        )
        if (
            self.minimum_promote_cost_adjusted_edge
            < self.minimum_watch_cost_adjusted_edge
        ):
            raise ValueError("promote edge threshold must be at least watch threshold")
        if (
            self.minimum_promote_evidence_quality_score
            < self.minimum_watch_evidence_quality_score
        ):
            raise ValueError("promote evidence threshold must be at least watch threshold")
        if (
            self.minimum_promote_liquidity_exit_feasibility_score
            < self.minimum_watch_liquidity_exit_feasibility_score
        ):
            raise ValueError("promote liquidity threshold must be at least watch threshold")
        if (
            self.maximum_promote_resolution_risk_score
            > self.maximum_watch_resolution_risk_score
        ):
            raise ValueError("promote resolution risk must be no higher than watch limit")
        if (
            self.maximum_promote_category_exposure_score
            > self.maximum_watch_category_exposure_score
        ):
            raise ValueError("promote category exposure must be no higher than watch limit")
        _require_phase_flags("StrategyMarketCandidateTriageV2Config", self)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV2Candidate:
    market_id: str
    category: str
    model_probability: Decimal
    market_probability: Decimal
    estimated_cost_probability: Decimal
    evidence_quality_score: Decimal
    specialist_approval_count: Decimal
    specialist_review_count: Decimal
    liquidity_exit_feasibility_score: Decimal
    resolution_risk_score: Decimal
    category_exposure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_public_text("category", self.category)
        for field_name in (
            "model_probability",
            "market_probability",
            "estimated_cost_probability",
            "evidence_quality_score",
            "liquidity_exit_feasibility_score",
            "resolution_risk_score",
            "category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("specialist_approval_count", "specialist_review_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.specialist_approval_count > self.specialist_review_count:
            raise ValueError("specialist_approval_count must not exceed reviews")
        _require_phase_flags("StrategyMarketCandidateTriageV2Candidate", self)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV2Row:
    config_version: str
    market_id: str
    category: str
    triage_bucket: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    model_probability: Decimal
    market_probability: Decimal
    estimated_cost_probability: Decimal
    cost_break_even_probability: Decimal
    cost_adjusted_edge: Decimal
    evidence_quality_score: Decimal
    specialist_approval_count: Decimal
    specialist_review_count: Decimal
    specialist_quorum_ratio: Decimal
    liquidity_exit_feasibility_score: Decimal
    resolution_risk_score: Decimal
    category_exposure_score: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        _require_identifier("market_id", self.market_id)
        _require_public_text("category", self.category)
        _require_member("triage_bucket", self.triage_bucket, TRIAGE_BUCKETS)
        _require_member(
            "recommended_next_step",
            self.recommended_next_step,
            tuple(NEXT_STEP_BY_BUCKET.values()),
        )
        if self.recommended_next_step != NEXT_STEP_BY_BUCKET[self.triage_bucket]:
            raise ValueError("recommended_next_step must match triage_bucket")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "blocking_reasons",
            _normalize_reason_codes(
                "blocking_reasons",
                self.blocking_reasons,
                allow_empty=True,
            ),
        )
        for field_name in (
            "model_probability",
            "market_probability",
            "estimated_cost_probability",
            "evidence_quality_score",
            "specialist_quorum_ratio",
            "liquidity_exit_feasibility_score",
            "resolution_risk_score",
            "category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("specialist_approval_count", "specialist_review_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_break_even_probability",
            _normalize_nonnegative_decimal(
                "cost_break_even_probability",
                self.cost_break_even_probability,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        if self.specialist_approval_count > self.specialist_review_count:
            raise ValueError("specialist_approval_count must not exceed reviews")
        if self.cost_break_even_probability != _quantize(
            self.market_probability + self.estimated_cost_probability,
        ):
            raise ValueError("cost_break_even_probability must match market and cost")
        if self.cost_adjusted_edge != _quantize(
            self.model_probability - self.cost_break_even_probability,
        ):
            raise ValueError("cost_adjusted_edge must match model and break-even")
        if self.specialist_quorum_ratio != _specialist_quorum_ratio(
            self.specialist_approval_count,
            self.specialist_review_count,
        ):
            raise ValueError("specialist_quorum_ratio must match specialist counts")
        if bool(self.blocking_reasons) != (self.triage_bucket == "block"):
            raise ValueError("blocking_reasons must match triage_bucket")
        _require_phase_flags("StrategyMarketCandidateTriageV2Row", self)
        expected_digest = _row_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(DIGEST_FIELD, self.derived_validation_digest)


@dataclass(frozen=True)
class StrategyMarketCandidateTriageV2Report:
    config_version: str
    candidate_count: Decimal
    promote_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    research_needed_count: Decimal
    rows: tuple[StrategyMarketCandidateTriageV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "promote_count",
            "watch_count",
            "block_count",
            "research_needed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            _require_row_integrity(row)
            if row.config_version != self.config_version:
                raise ValueError("row config_version must match report config_version")
        expected_counts = _bucket_counts(self.rows)
        if self.candidate_count != _count(len(self.rows)):
            raise ValueError("candidate_count must match rows")
        if self.promote_count != expected_counts["promote"]:
            raise ValueError("promote_count must match rows")
        if self.watch_count != expected_counts["watch"]:
            raise ValueError("watch_count must match rows")
        if self.block_count != expected_counts["block"]:
            raise ValueError("block_count must match rows")
        if self.research_needed_count != expected_counts["research-needed"]:
            raise ValueError("research_needed_count must match rows")
        _require_phase_flags("StrategyMarketCandidateTriageV2Report", self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(DIGEST_FIELD, self.derived_validation_digest)


def build_strategy_market_candidate_triage_v2_report(
    candidates: tuple[StrategyMarketCandidateTriageV2Candidate, ...],
    *,
    config: StrategyMarketCandidateTriageV2Config | None = None,
) -> StrategyMarketCandidateTriageV2Report:
    """Build a readonly Phase 1 triage report without side effects."""

    if type(candidates) is not tuple:
        raise ValueError("candidates must be a tuple")
    cfg = config or StrategyMarketCandidateTriageV2Config()
    if type(cfg) is not StrategyMarketCandidateTriageV2Config:
        raise ValueError("config must be a StrategyMarketCandidateTriageV2Config")
    _require_phase_flags("config", cfg)

    rows = tuple(_triage_row(candidate, config=cfg) for candidate in candidates)
    counts = _bucket_counts(rows)
    return StrategyMarketCandidateTriageV2Report(
        config_version=cfg.config_version,
        candidate_count=_count(len(rows)),
        promote_count=counts["promote"],
        watch_count=counts["watch"],
        block_count=counts["block"],
        research_needed_count=counts["research-needed"],
        rows=rows,
    )


def triage_strategy_market_candidate_v2(
    *,
    market_id: str,
    category: str,
    model_probability: Decimal,
    market_probability: Decimal,
    estimated_cost_probability: Decimal,
    evidence_quality_score: Decimal,
    specialist_approval_count: Decimal,
    specialist_review_count: Decimal,
    liquidity_exit_feasibility_score: Decimal,
    resolution_risk_score: Decimal,
    category_exposure_score: Decimal,
    config: StrategyMarketCandidateTriageV2Config | None = None,
) -> StrategyMarketCandidateTriageV2Report:
    candidate = StrategyMarketCandidateTriageV2Candidate(
        market_id=market_id,
        category=category,
        model_probability=model_probability,
        market_probability=market_probability,
        estimated_cost_probability=estimated_cost_probability,
        evidence_quality_score=evidence_quality_score,
        specialist_approval_count=specialist_approval_count,
        specialist_review_count=specialist_review_count,
        liquidity_exit_feasibility_score=liquidity_exit_feasibility_score,
        resolution_risk_score=resolution_risk_score,
        category_exposure_score=category_exposure_score,
    )
    return build_strategy_market_candidate_triage_v2_report((candidate,), config=config)


def strategy_market_candidate_triage_v2_payload(
    report: StrategyMarketCandidateTriageV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyMarketCandidateTriageV2Report:
        _require_report_integrity(report)
        payload = _report_public_payload(report, include_digest=True)
    elif type(report) is dict:
        payload = _copy_public_payload(report)
        validate_strategy_market_candidate_triage_v2_public_payload(payload)
    else:
        raise ValueError("report must be a StrategyMarketCandidateTriageV2Report")
    _reject_unsafe_public_payload("strategy market candidate triage v2 payload", payload)
    return payload


def validate_strategy_market_candidate_triage_v2_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("strategy market candidate triage v2 payload", payload)
    _require_public_payload_flags("payload", payload)
    _require_digest(DIGEST_FIELD, payload.get(DIGEST_FIELD))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_public_payload_flags("row", row)
        _require_digest(DIGEST_FIELD, row.get(DIGEST_FIELD))
        row_unsigned = dict(row)
        row_digest = row_unsigned.pop(DIGEST_FIELD)
        if row_digest != _payload_digest(row_unsigned):
            raise ValueError("derived_validation_digest mismatch")
    unsigned = dict(payload)
    digest = unsigned.pop(DIGEST_FIELD)
    if digest != _payload_digest(unsigned):
        raise ValueError("derived_validation_digest mismatch")


def _triage_row(
    candidate: StrategyMarketCandidateTriageV2Candidate,
    *,
    config: StrategyMarketCandidateTriageV2Config,
) -> StrategyMarketCandidateTriageV2Row:
    if type(candidate) is not StrategyMarketCandidateTriageV2Candidate:
        raise ValueError("candidate must be a StrategyMarketCandidateTriageV2Candidate")
    _require_phase_flags("candidate", candidate)
    with localcontext(DECIMAL_CONTEXT):
        cost_break_even_probability = _quantize(
            candidate.market_probability + candidate.estimated_cost_probability,
        )
        cost_adjusted_edge = _quantize(
            candidate.model_probability - cost_break_even_probability,
        )
    quorum_ratio = _specialist_quorum_ratio(
        candidate.specialist_approval_count,
        candidate.specialist_review_count,
    )
    blocking_reasons = _blocking_reasons(
        candidate,
        config=config,
        cost_break_even_probability=cost_break_even_probability,
        cost_adjusted_edge=cost_adjusted_edge,
    )
    research_reasons = _research_needed_reasons(
        candidate,
        config=config,
        specialist_quorum_ratio=quorum_ratio,
    )
    bucket = _triage_bucket(
        candidate,
        config=config,
        cost_break_even_probability=cost_break_even_probability,
        cost_adjusted_edge=cost_adjusted_edge,
        specialist_quorum_ratio=quorum_ratio,
        blocking_reasons=blocking_reasons,
        research_reasons=research_reasons,
    )
    reason_codes = _reason_codes(
        candidate,
        config=config,
        bucket=bucket,
        blocking_reasons=blocking_reasons,
        research_reasons=research_reasons,
        cost_adjusted_edge=cost_adjusted_edge,
        specialist_quorum_ratio=quorum_ratio,
    )
    return StrategyMarketCandidateTriageV2Row(
        config_version=config.config_version,
        market_id=candidate.market_id,
        category=candidate.category,
        triage_bucket=bucket,
        recommended_next_step=NEXT_STEP_BY_BUCKET[bucket],
        reason_codes=reason_codes,
        blocking_reasons=blocking_reasons if bucket == "block" else (),
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        estimated_cost_probability=candidate.estimated_cost_probability,
        cost_break_even_probability=cost_break_even_probability,
        cost_adjusted_edge=cost_adjusted_edge,
        evidence_quality_score=candidate.evidence_quality_score,
        specialist_approval_count=candidate.specialist_approval_count,
        specialist_review_count=candidate.specialist_review_count,
        specialist_quorum_ratio=quorum_ratio,
        liquidity_exit_feasibility_score=candidate.liquidity_exit_feasibility_score,
        resolution_risk_score=candidate.resolution_risk_score,
        category_exposure_score=candidate.category_exposure_score,
    )


def _triage_bucket(
    candidate: StrategyMarketCandidateTriageV2Candidate,
    *,
    config: StrategyMarketCandidateTriageV2Config,
    cost_break_even_probability: Decimal,
    cost_adjusted_edge: Decimal,
    specialist_quorum_ratio: Decimal,
    blocking_reasons: tuple[str, ...],
    research_reasons: tuple[str, ...],
) -> str:
    del cost_break_even_probability
    if blocking_reasons:
        return "block"
    if research_reasons:
        return "research-needed"
    if (
        cost_adjusted_edge >= config.minimum_promote_cost_adjusted_edge
        and candidate.evidence_quality_score
        >= config.minimum_promote_evidence_quality_score
        and specialist_quorum_ratio >= config.minimum_specialist_quorum_ratio
        and candidate.specialist_review_count >= config.minimum_specialist_review_count
        and candidate.liquidity_exit_feasibility_score
        >= config.minimum_promote_liquidity_exit_feasibility_score
        and candidate.resolution_risk_score <= config.maximum_promote_resolution_risk_score
        and candidate.category_exposure_score
        <= config.maximum_promote_category_exposure_score
    ):
        return "promote"
    return "watch"


def _blocking_reasons(
    candidate: StrategyMarketCandidateTriageV2Candidate,
    *,
    config: StrategyMarketCandidateTriageV2Config,
    cost_break_even_probability: Decimal,
    cost_adjusted_edge: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if cost_adjusted_edge < ZERO:
        reasons.append("cost_adjusted_edge_negative")
    if cost_break_even_probability > config.maximum_cost_break_even_probability:
        reasons.append("cost_break_even_above_limit")
    if (
        candidate.liquidity_exit_feasibility_score
        < config.minimum_watch_liquidity_exit_feasibility_score
    ):
        reasons.append("liquidity_exit_feasibility_below_floor")
    if candidate.resolution_risk_score > config.maximum_watch_resolution_risk_score:
        reasons.append("resolution_risk_above_limit")
    if candidate.category_exposure_score > config.maximum_watch_category_exposure_score:
        reasons.append("category_exposure_above_limit")
    return tuple(reasons)


def _research_needed_reasons(
    candidate: StrategyMarketCandidateTriageV2Candidate,
    *,
    config: StrategyMarketCandidateTriageV2Config,
    specialist_quorum_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.evidence_quality_score < config.minimum_watch_evidence_quality_score:
        reasons.append("evidence_quality_below_floor")
    if candidate.specialist_review_count < config.minimum_specialist_review_count:
        reasons.append("specialist_review_count_below_quorum")
    if specialist_quorum_ratio < config.minimum_specialist_quorum_ratio:
        reasons.append("specialist_quorum_ratio_below_floor")
    return tuple(reasons)


def _reason_codes(
    candidate: StrategyMarketCandidateTriageV2Candidate,
    *,
    config: StrategyMarketCandidateTriageV2Config,
    bucket: str,
    blocking_reasons: tuple[str, ...],
    research_reasons: tuple[str, ...],
    cost_adjusted_edge: Decimal,
    specialist_quorum_ratio: Decimal,
) -> tuple[str, ...]:
    if bucket == "block":
        return tuple(f"candidate_{reason}_block" for reason in blocking_reasons)
    if bucket == "research-needed":
        return tuple(f"candidate_{reason}_research_needed" for reason in research_reasons)
    if bucket == "promote":
        return ("candidate_promote_clear",)

    reasons: list[str] = []
    if cost_adjusted_edge < config.minimum_promote_cost_adjusted_edge:
        if cost_adjusted_edge < config.minimum_watch_cost_adjusted_edge:
            reasons.append("candidate_cost_adjusted_edge_below_watch")
        else:
            reasons.append("candidate_cost_adjusted_edge_below_promote")
    if (
        candidate.evidence_quality_score
        < config.minimum_promote_evidence_quality_score
    ):
        reasons.append("candidate_evidence_quality_below_promote")
    if specialist_quorum_ratio < config.minimum_specialist_quorum_ratio:
        reasons.append("candidate_specialist_quorum_below_promote")
    if (
        candidate.liquidity_exit_feasibility_score
        < config.minimum_promote_liquidity_exit_feasibility_score
    ):
        reasons.append("candidate_liquidity_exit_feasibility_below_promote")
    if candidate.resolution_risk_score > config.maximum_promote_resolution_risk_score:
        reasons.append("candidate_resolution_risk_above_promote")
    if (
        candidate.category_exposure_score
        > config.maximum_promote_category_exposure_score
    ):
        reasons.append("candidate_category_exposure_above_promote")
    if not reasons:
        reasons.append("candidate_watch_refresh")
    return tuple(reasons)


def _specialist_quorum_ratio(
    specialist_approval_count: Decimal,
    specialist_review_count: Decimal,
) -> Decimal:
    if specialist_review_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(specialist_approval_count / specialist_review_count)


def _bucket_counts(
    rows: tuple[StrategyMarketCandidateTriageV2Row, ...],
) -> dict[str, Decimal]:
    counts = {bucket: ZERO for bucket in TRIAGE_BUCKETS}
    for row in rows:
        counts[row.triage_bucket] = _count(int(counts[row.triage_bucket]) + 1)
    return counts


def _require_row_integrity(row: object) -> None:
    if type(row) is not StrategyMarketCandidateTriageV2Row:
        raise ValueError("rows must contain StrategyMarketCandidateTriageV2Row")
    _require_phase_flags("row", row)
    if row.derived_validation_digest != _row_validation_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_integrity(report: StrategyMarketCandidateTriageV2Report) -> None:
    _require_phase_flags("report", report)
    for row in report.rows:
        _require_row_integrity(row)
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _row_validation_digest(row: StrategyMarketCandidateTriageV2Row) -> str:
    return _payload_digest(_row_public_payload(row, include_digest=False))


def _report_validation_digest(report: StrategyMarketCandidateTriageV2Report) -> str:
    return _payload_digest(_report_public_payload(report, include_digest=False))


def _row_public_payload(
    row: StrategyMarketCandidateTriageV2Row,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "config_version": row.config_version,
        "market_id": row.market_id,
        "category": row.category,
        "triage_bucket": row.triage_bucket,
        "recommended_next_step": row.recommended_next_step,
        "reason_codes": list(row.reason_codes),
        "blocking_reasons": list(row.blocking_reasons),
        "model_probability": _decimal_payload(row.model_probability),
        "market_probability": _decimal_payload(row.market_probability),
        "estimated_cost_probability": _decimal_payload(row.estimated_cost_probability),
        "cost_break_even_probability": _decimal_payload(
            row.cost_break_even_probability,
        ),
        "cost_adjusted_edge": _decimal_payload(row.cost_adjusted_edge),
        "evidence_quality_score": _decimal_payload(row.evidence_quality_score),
        "specialist_approval_count": _decimal_payload(row.specialist_approval_count),
        "specialist_review_count": _decimal_payload(row.specialist_review_count),
        "specialist_quorum_ratio": _decimal_payload(row.specialist_quorum_ratio),
        "liquidity_exit_feasibility_score": _decimal_payload(
            row.liquidity_exit_feasibility_score,
        ),
        "resolution_risk_score": _decimal_payload(row.resolution_risk_score),
        "category_exposure_score": _decimal_payload(row.category_exposure_score),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload[DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _report_public_payload(
    report: StrategyMarketCandidateTriageV2Report,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "promote_count": _decimal_payload(report.promote_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "research_needed_count": _decimal_payload(report.research_needed_count),
        "rows": [
            _row_public_payload(row, include_digest=True)
            for row in report.rows
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload[DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _copy_public_payload(value: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    copied = json.loads(encoded)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _payload_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload numeric value must be Decimal")
    if not value.is_finite():
        raise ValueError("payload numeric value must be finite")
    return str(value)


def _require_public_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_phase_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be canonical non-empty text")
    _reject_unsafe_public_text(field_name, value)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} is not supported")
    _reject_unsafe_public_text(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reasons = tuple(value)
    if not allow_empty and not reasons:
        raise ValueError(f"{field_name} must not be empty")
    for reason in reasons:
        _require_identifier(field_name, reason)
    if len(reasons) != len(set(reasons)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return reasons


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != _quantize(normalized.to_integral_value()):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
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
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is bool or value is None:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("public payload value is not JSON serializable")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface text")


__all__ = (
    "DEFAULT_STRATEGY_MARKET_CANDIDATE_TRIAGE_V2_CONFIG_VERSION",
    "StrategyMarketCandidateTriageV2Candidate",
    "StrategyMarketCandidateTriageV2Config",
    "StrategyMarketCandidateTriageV2Report",
    "StrategyMarketCandidateTriageV2Row",
    "build_strategy_market_candidate_triage_v2_report",
    "strategy_market_candidate_triage_v2_payload",
    "triage_strategy_market_candidate_v2",
    "validate_strategy_market_candidate_triage_v2_public_payload",
)
