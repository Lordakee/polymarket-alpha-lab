"""Paper-only candidate decision engine orchestrator."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.candidate_decision_cost_liquidity_adapter import (
    CandidateDecisionCostLiquidityAdapterOutput,
    adapter_output_to_candidate_decision_fields,
)
from polymarket_alpha_lab.candidate_decision_evidence_adapter import (
    CandidateDecisionEvidenceAdapterResult,
    candidate_decision_evidence_adapter_decision_fields,
)
from polymarket_alpha_lab.candidate_decision_resolution_risk_adapter import (
    CandidateDecisionResolutionRiskAdapterReport,
)
from polymarket_alpha_lab.candidate_decision_score import (
    ACTION_STATES,
    CandidateDecisionScoreConfig,
    CandidateDecisionScoreInput,
    CandidateDecisionScoreReport,
    build_candidate_decision_score_report,
)
from polymarket_alpha_lab.candidate_decision_team_memory_adapter import (
    CandidateDecisionTeamMemoryAdapterResult,
)
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_PAPER_CANDIDATE_DECISION_ENGINE_VERSION = "paper-candidate-decision-engine-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
COUNT_QUANTUM = Decimal("1")
SELECTED_SIDES = ("yes", "no")
TEAM_MEMORY_POLICIES = ("allow", "throttle", "block")


@dataclass(frozen=True)
class PaperCandidateDecisionEngineInput:
    candidate_id: str
    market_id: str
    normalized_market_question: str
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    selected_side: str
    forecast_probability: Decimal | None
    executable_price: Decimal | None
    source_report_refs: tuple[str, ...]
    cost_liquidity: CandidateDecisionCostLiquidityAdapterOutput
    evidence: CandidateDecisionEvidenceAdapterResult
    resolution_risk: CandidateDecisionResolutionRiskAdapterReport
    team_memory: CandidateDecisionTeamMemoryAdapterResult
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperCandidateDecisionEngineInput:
            raise ValueError("input must be exactly PaperCandidateDecisionEngineInput")
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string(
            "normalized_market_question",
            self.normalized_market_question,
        )
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(self.secondary_team_ids, self.primary_team_id),
        )
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        for field_name in ("forecast_probability", "executable_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_string_tuple("source_report_refs", self.source_report_refs),
        )
        _require_exact_adapter_outputs(self)
        require_paper_only_flags("PaperCandidateDecisionEngineInput", self)
        _reject_unsafe_envelope_fields("paper candidate decision engine input", self)
        _validate_input_identity(self)


@dataclass(frozen=True)
class PaperCandidateDecisionEngineReasonCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperCandidateDecisionEngineReasonCount:
            raise ValueError(
                "reason count must be exactly PaperCandidateDecisionEngineReasonCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_count_decimal("count", self.count),
        )
        require_paper_only_flags("PaperCandidateDecisionEngineReasonCount", self)
        reject_unsafe_surface_fields("paper candidate decision engine reason count", self)


@dataclass(frozen=True)
class PaperCandidateDecisionEngineRow:
    candidate_id: str
    market_id: str
    normalized_market_question: str
    score_input: CandidateDecisionScoreInput
    score_report: CandidateDecisionScoreReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperCandidateDecisionEngineRow:
            raise ValueError("row must be exactly PaperCandidateDecisionEngineRow")
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string(
            "normalized_market_question",
            self.normalized_market_question,
        )
        if type(self.score_input) is not CandidateDecisionScoreInput:
            raise ValueError("score_input must be a CandidateDecisionScoreInput")
        if type(self.score_report) is not CandidateDecisionScoreReport:
            raise ValueError("score_report must be a CandidateDecisionScoreReport")
        require_paper_only_flags("CandidateDecisionScoreInput", self.score_input)
        require_paper_only_flags("CandidateDecisionScoreReport", self.score_report)
        if self.candidate_id != self.score_input.candidate_id:
            raise ValueError("candidate_id must match score_input")
        if self.candidate_id != self.score_report.candidate_id:
            raise ValueError("candidate_id must match score_report")
        if self.market_id != self.score_input.market_id:
            raise ValueError("market_id must match score_input")
        if self.market_id != self.score_report.market_id:
            raise ValueError("market_id must match score_report")
        if self.normalized_market_question != self.score_input.normalized_market_question:
            raise ValueError("normalized_market_question must match score_input")
        if self.normalized_market_question != self.score_report.normalized_market_question:
            raise ValueError("normalized_market_question must match score_report")
        require_paper_only_flags("PaperCandidateDecisionEngineRow", self)
        reject_unsafe_surface_fields("paper candidate decision engine row", self)


@dataclass(frozen=True)
class PaperCandidateDecisionEngineReport:
    generated_at: datetime
    config_version: str
    rows: tuple[PaperCandidateDecisionEngineRow, ...]
    candidate_count: Decimal
    reject_count: Decimal
    watch_count: Decimal
    research_more_count: Decimal
    paper_recommend_count: Decimal
    reason_counts: tuple[PaperCandidateDecisionEngineReasonCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperCandidateDecisionEngineReport:
            raise ValueError("report must be exactly PaperCandidateDecisionEngineReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_PAPER_CANDIDATE_DECISION_ENGINE_VERSION:
            raise ValueError("config_version must be the supported engine version")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in (
            "candidate_count",
            "reject_count",
            "watch_count",
            "research_more_count",
            "paper_recommend_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_counts",
            _normalize_reason_counts(self.reason_counts),
        )
        require_paper_only_flags("PaperCandidateDecisionEngineReport", self)
        reject_unsafe_surface_fields("paper candidate decision engine report", self)
        _validate_report_counts(self)


def build_paper_candidate_decision_engine_report(
    inputs: tuple[PaperCandidateDecisionEngineInput, ...]
    | list[PaperCandidateDecisionEngineInput],
    *,
    generated_at: datetime,
    score_config: CandidateDecisionScoreConfig | None = None,
) -> PaperCandidateDecisionEngineReport:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    candidates = tuple(inputs)
    for input_value in candidates:
        if type(input_value) is not PaperCandidateDecisionEngineInput:
            raise ValueError("inputs must contain PaperCandidateDecisionEngineInput values")
        require_paper_only_flags("PaperCandidateDecisionEngineInput", input_value)
        _reject_unsafe_envelope_fields("paper candidate decision engine input", input_value)
    _require_unique_candidate_market_pairs(candidates)

    if score_config is None:
        score_config = CandidateDecisionScoreConfig()
    if type(score_config) is not CandidateDecisionScoreConfig:
        raise ValueError("score_config must be a CandidateDecisionScoreConfig")
    require_paper_only_flags("CandidateDecisionScoreConfig", score_config)
    generated_at_utc = _as_utc("generated_at", generated_at)

    rows = tuple(
        _row_for_input(
            input_value,
            generated_at=generated_at_utc,
            score_config=score_config,
        )
        for input_value in candidates
    )
    rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.score_report.candidate_id,
                row.score_report.market_id,
            ),
        ),
    )
    action_counts = Counter(row.score_report.action for row in rows)
    reason_counts = _reason_counts(rows)
    return PaperCandidateDecisionEngineReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_PAPER_CANDIDATE_DECISION_ENGINE_VERSION,
        rows=rows,
        candidate_count=_count_decimal(len(rows)),
        reject_count=_count_decimal(action_counts["reject"]),
        watch_count=_count_decimal(action_counts["watch"]),
        research_more_count=_count_decimal(action_counts["research_more"]),
        paper_recommend_count=_count_decimal(action_counts["paper_recommend"]),
        reason_counts=reason_counts,
    )


def paper_candidate_decision_engine_payload(
    report: PaperCandidateDecisionEngineReport,
) -> dict[str, Any]:
    if type(report) is not PaperCandidateDecisionEngineReport:
        raise ValueError("report must be a PaperCandidateDecisionEngineReport")
    require_paper_only_flags("PaperCandidateDecisionEngineReport", report)
    reject_unsafe_surface_fields("paper candidate decision engine report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("paper candidate decision engine payload", payload)
    return payload


def _row_for_input(
    input_value: PaperCandidateDecisionEngineInput,
    *,
    generated_at: datetime,
    score_config: CandidateDecisionScoreConfig,
) -> PaperCandidateDecisionEngineRow:
    score_input = _score_input_for(input_value)
    score_report = build_candidate_decision_score_report(
        score_input,
        config=score_config,
        generated_at=generated_at,
    )
    return PaperCandidateDecisionEngineRow(
        candidate_id=input_value.candidate_id,
        market_id=input_value.market_id,
        normalized_market_question=input_value.normalized_market_question,
        score_input=score_input,
        score_report=score_report,
    )


def _score_input_for(
    input_value: PaperCandidateDecisionEngineInput,
) -> CandidateDecisionScoreInput:
    cost_fields = adapter_output_to_candidate_decision_fields(
        input_value.cost_liquidity,
    )
    evidence_fields = candidate_decision_evidence_adapter_decision_fields(
        input_value.evidence,
    )
    source_report_refs = _merge_source_report_refs(input_value)
    adapter_reason_codes = _merge_adapter_reason_codes(input_value)
    return CandidateDecisionScoreInput(
        candidate_id=input_value.candidate_id,
        market_id=input_value.market_id,
        normalized_market_question=input_value.normalized_market_question,
        primary_team_id=input_value.primary_team_id,
        secondary_team_ids=input_value.secondary_team_ids,
        selected_side=input_value.selected_side,
        forecast_probability=input_value.forecast_probability,
        executable_price=input_value.executable_price,
        gross_edge=cost_fields["gross_edge"],
        estimated_cost_drag=cost_fields["estimated_cost_drag"],
        cost_score=cost_fields["cost_score"],
        liquidity_score=cost_fields["liquidity_score"],
        evidence_score=evidence_fields["evidence_score"],
        resolution_score=input_value.resolution_risk.resolution_score,
        team_memory_score=input_value.team_memory.team_memory_score,
        team_memory_policy=input_value.team_memory.team_memory_policy,
        source_report_refs=source_report_refs,
        adapter_reason_codes=adapter_reason_codes,
    )


def _merge_source_report_refs(
    input_value: PaperCandidateDecisionEngineInput,
) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "source_report_refs",
        (
            *input_value.source_report_refs,
            *input_value.evidence.source_report_refs,
            *input_value.resolution_risk.source_report_refs,
            *input_value.team_memory.source_report_refs,
        ),
    )


def _merge_adapter_reason_codes(
    input_value: PaperCandidateDecisionEngineInput,
) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "adapter_reason_codes",
        (
            *input_value.cost_liquidity.reason_codes,
            *input_value.evidence.reason_codes,
            *input_value.resolution_risk.reason_codes,
            *input_value.team_memory.reason_codes,
        ),
    )


def _reason_counts(
    rows: tuple[PaperCandidateDecisionEngineRow, ...],
) -> tuple[PaperCandidateDecisionEngineReasonCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.score_report.reason_codes)
    return tuple(
        PaperCandidateDecisionEngineReasonCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _validate_input_identity(input_value: PaperCandidateDecisionEngineInput) -> None:
    _validate_cost_liquidity_identity(input_value)
    _validate_resolution_risk_identity(input_value)
    _validate_team_memory_identity(input_value)
    _validate_cross_adapter_values(input_value)


def _validate_cost_liquidity_identity(
    input_value: PaperCandidateDecisionEngineInput,
) -> None:
    cost = input_value.cost_liquidity
    _expect_equal("cost_liquidity.candidate_id", cost.candidate_id, input_value.candidate_id)
    _expect_equal("cost_liquidity.market_id", cost.market_id, input_value.market_id)
    _expect_equal("cost_liquidity.selected_side", cost.selected_side, input_value.selected_side)
    _expect_equal(
        "cost_liquidity.forecast_probability",
        cost.forecast_probability,
        input_value.forecast_probability,
    )
    _expect_equal(
        "cost_liquidity.executable_price",
        cost.executable_price,
        input_value.executable_price,
    )


def _validate_resolution_risk_identity(
    input_value: PaperCandidateDecisionEngineInput,
) -> None:
    resolution = input_value.resolution_risk
    _expect_equal(
        "resolution_risk.candidate_id",
        resolution.candidate_id,
        input_value.candidate_id,
    )
    _expect_equal("resolution_risk.market_id", resolution.market_id, input_value.market_id)
    _expect_equal(
        "resolution_risk.normalized_market_question",
        resolution.normalized_market_question,
        input_value.normalized_market_question,
    )
    _expect_equal(
        "resolution_risk.primary_team_id",
        resolution.primary_team_id,
        input_value.primary_team_id,
    )
    _expect_equal(
        "resolution_risk.secondary_team_ids",
        resolution.secondary_team_ids,
        input_value.secondary_team_ids,
    )
    _expect_equal(
        "resolution_risk.selected_side",
        resolution.selected_side,
        input_value.selected_side,
    )
    _expect_equal(
        "resolution_risk.forecast_probability",
        resolution.forecast_probability,
        input_value.forecast_probability,
    )
    _expect_equal(
        "resolution_risk.executable_price",
        resolution.executable_price,
        input_value.executable_price,
    )


def _validate_team_memory_identity(
    input_value: PaperCandidateDecisionEngineInput,
) -> None:
    memory = input_value.team_memory
    _expect_equal(
        "team_memory.primary_team_id",
        memory.primary_team_id,
        input_value.primary_team_id,
    )
    _expect_equal(
        "team_memory.secondary_team_ids",
        memory.secondary_team_ids,
        input_value.secondary_team_ids,
    )


def _validate_cross_adapter_values(
    input_value: PaperCandidateDecisionEngineInput,
) -> None:
    cost = input_value.cost_liquidity
    evidence = input_value.evidence
    resolution = input_value.resolution_risk
    memory = input_value.team_memory
    _expect_equal("resolution_risk.gross_edge", resolution.gross_edge, cost.gross_edge)
    _expect_equal(
        "resolution_risk.estimated_cost_drag",
        resolution.estimated_cost_drag,
        cost.estimated_cost_drag,
    )
    _expect_equal("resolution_risk.cost_score", resolution.cost_score, cost.cost_score)
    _expect_equal(
        "resolution_risk.liquidity_score",
        resolution.liquidity_score,
        cost.liquidity_score,
    )
    _expect_equal("resolution_risk.evidence_score", resolution.evidence_score, evidence.evidence_score)
    _expect_equal(
        "resolution_risk.team_memory_score",
        resolution.team_memory_score,
        memory.team_memory_score,
    )
    _expect_equal(
        "resolution_risk.team_memory_policy",
        resolution.team_memory_policy,
        memory.team_memory_policy,
    )


def _require_exact_adapter_outputs(
    input_value: PaperCandidateDecisionEngineInput,
) -> None:
    if type(input_value.cost_liquidity) is not CandidateDecisionCostLiquidityAdapterOutput:
        raise ValueError(
            "cost_liquidity must be a CandidateDecisionCostLiquidityAdapterOutput",
        )
    if type(input_value.evidence) is not CandidateDecisionEvidenceAdapterResult:
        raise ValueError("evidence must be a CandidateDecisionEvidenceAdapterResult")
    if type(input_value.resolution_risk) is not CandidateDecisionResolutionRiskAdapterReport:
        raise ValueError(
            "resolution_risk must be a CandidateDecisionResolutionRiskAdapterReport",
        )
    if type(input_value.team_memory) is not CandidateDecisionTeamMemoryAdapterResult:
        raise ValueError("team_memory must be a CandidateDecisionTeamMemoryAdapterResult")
    require_paper_only_flags(
        "CandidateDecisionCostLiquidityAdapterOutput",
        input_value.cost_liquidity,
    )
    require_paper_only_flags(
        "CandidateDecisionEvidenceAdapterResult",
        input_value.evidence,
    )
    require_paper_only_flags(
        "CandidateDecisionResolutionRiskAdapterReport",
        input_value.resolution_risk,
    )
    require_paper_only_flags(
        "CandidateDecisionTeamMemoryAdapterResult",
        input_value.team_memory,
    )


def _reject_unsafe_envelope_fields(label: str, value: object) -> None:
    field_names = getattr(value, "__dataclass_fields__", None)
    if type(field_names) is not dict:
        raise ValueError(f"{label} must be a dataclass instance")
    reject_unsafe_surface_fields(label, {field_name: None for field_name in field_names})


def _expect_equal(field_name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise ValueError(f"{field_name} must match candidate input")


def _require_unique_candidate_market_pairs(
    inputs: tuple[PaperCandidateDecisionEngineInput, ...],
) -> None:
    pairs = tuple((item.candidate_id, item.market_id) for item in inputs)
    if len(set(pairs)) != len(pairs):
        raise ValueError("inputs must not contain duplicate candidate/market pairs")


def _normalize_rows(value: object) -> tuple[PaperCandidateDecisionEngineRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not PaperCandidateDecisionEngineRow:
            raise ValueError("rows must contain PaperCandidateDecisionEngineRow values")
        require_paper_only_flags("PaperCandidateDecisionEngineRow", row)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.score_report.candidate_id,
                row.score_report.market_id,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by candidate_id and market_id")
    return rows


def _normalize_reason_counts(
    value: object,
) -> tuple[PaperCandidateDecisionEngineReasonCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_counts must be a list or tuple")
    counts = tuple(value)
    for item in counts:
        if type(item) is not PaperCandidateDecisionEngineReasonCount:
            raise ValueError(
                "reason_counts must contain PaperCandidateDecisionEngineReasonCount values",
            )
        require_paper_only_flags("PaperCandidateDecisionEngineReasonCount", item)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_counts must be sorted by reason_code")
    reason_codes = tuple(item.reason_code for item in counts)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_counts must not contain duplicate reason codes")
    return counts


def _validate_report_counts(report: PaperCandidateDecisionEngineReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    action_counts = Counter(row.score_report.action for row in report.rows)
    expected_counts = {
        "reject_count": action_counts["reject"],
        "watch_count": action_counts["watch"],
        "research_more_count": action_counts["research_more"],
        "paper_recommend_count": action_counts["paper_recommend"],
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != _count_decimal(expected):
            raise ValueError(f"{field_name} must match rows")
    if sum(action_counts.values()) != len(report.rows):
        raise ValueError("row action counts must match rows")
    for action in action_counts:
        if action not in ACTION_STATES:
            raise ValueError("rows must contain known actions")
    expected_reason_counts = _reason_counts(report.rows)
    if report.reason_counts != expected_reason_counts:
        raise ValueError("reason_counts must match rows")


def _normalize_secondary_team_ids(value: object, primary_team_id: str) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("secondary_team_ids must be a list or tuple")
    team_ids = tuple(require_team_id("secondary_team_ids", item) for item in value)
    if primary_team_id in team_ids:
        raise ValueError("secondary_team_ids must not include primary_team_id")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("secondary_team_ids must be unique")
    return team_ids


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(items))


def _normalize_optional_unit_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


__all__ = (
    "DEFAULT_PAPER_CANDIDATE_DECISION_ENGINE_VERSION",
    "PaperCandidateDecisionEngineInput",
    "PaperCandidateDecisionEngineReasonCount",
    "PaperCandidateDecisionEngineRow",
    "PaperCandidateDecisionEngineReport",
    "build_paper_candidate_decision_engine_report",
    "paper_candidate_decision_engine_payload",
)
