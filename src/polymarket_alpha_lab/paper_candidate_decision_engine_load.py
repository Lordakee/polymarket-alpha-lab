"""Pure loader composition for paper candidate decision engine reports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.candidate_decision_cost_liquidity_adapter import (
    CandidateDecisionCostLiquidityAdapterOutput,
)
from polymarket_alpha_lab.candidate_decision_evidence_adapter import (
    CandidateDecisionEvidenceAdapterResult,
)
from polymarket_alpha_lab.candidate_decision_resolution_risk_adapter import (
    CandidateDecisionResolutionRiskAdapterReport,
)
from polymarket_alpha_lab.candidate_decision_score import CandidateDecisionScoreConfig
from polymarket_alpha_lab.candidate_decision_team_memory_adapter import (
    CandidateDecisionTeamMemoryAdapterResult,
)
from polymarket_alpha_lab.paper_candidate_decision_engine import (
    PaperCandidateDecisionEngineInput,
    PaperCandidateDecisionEngineReport,
    build_paper_candidate_decision_engine_report,
)
from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


SELECTED_SIDES = ("yes", "no")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")


@dataclass(frozen=True)
class PaperCandidateDecisionEngineCandidateBundle:
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
        if type(self) is not PaperCandidateDecisionEngineCandidateBundle:
            raise ValueError(
                "bundle must be exactly PaperCandidateDecisionEngineCandidateBundle",
            )
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
        require_paper_only_flags("PaperCandidateDecisionEngineCandidateBundle", self)
        _reject_unsafe_envelope_fields("paper candidate decision engine candidate bundle", self)


def paper_candidate_decision_engine_input_from_bundle(
    bundle: PaperCandidateDecisionEngineCandidateBundle,
) -> PaperCandidateDecisionEngineInput:
    _require_bundle("bundle", bundle)
    return PaperCandidateDecisionEngineInput(
        candidate_id=bundle.candidate_id,
        market_id=bundle.market_id,
        normalized_market_question=bundle.normalized_market_question,
        primary_team_id=bundle.primary_team_id,
        secondary_team_ids=bundle.secondary_team_ids,
        selected_side=bundle.selected_side,
        forecast_probability=bundle.forecast_probability,
        executable_price=bundle.executable_price,
        source_report_refs=bundle.source_report_refs,
        cost_liquidity=bundle.cost_liquidity,
        evidence=bundle.evidence,
        resolution_risk=bundle.resolution_risk,
        team_memory=bundle.team_memory,
    )


def load_paper_candidate_decision_engine_report(
    *,
    generated_at: datetime,
    score_config: CandidateDecisionScoreConfig | None = None,
    candidate_bundles: tuple[PaperCandidateDecisionEngineCandidateBundle, ...]
    | list[PaperCandidateDecisionEngineCandidateBundle]
    | None = None,
    candidate_bundle_loader: Callable[[], object] | None = None,
    candidate_inputs: tuple[PaperCandidateDecisionEngineInput, ...]
    | list[PaperCandidateDecisionEngineInput]
    | None = None,
    candidate_input_loader: Callable[[], object] | None = None,
    report_builder: Callable[..., object] = build_paper_candidate_decision_engine_report,
) -> PaperCandidateDecisionEngineReport:
    _require_generated_at(generated_at)
    if score_config is not None:
        _require_score_config(score_config)
    if not callable(report_builder):
        raise ValueError("report_builder must be callable")

    source_count = sum(
        value is not None
        for value in (
            candidate_bundles,
            candidate_bundle_loader,
            candidate_inputs,
            candidate_input_loader,
        )
    )
    if source_count != 1:
        raise ValueError("exactly one candidate source is required")

    inputs = _load_candidate_inputs(
        candidate_bundles=candidate_bundles,
        candidate_bundle_loader=candidate_bundle_loader,
        candidate_inputs=candidate_inputs,
        candidate_input_loader=candidate_input_loader,
    )
    report = report_builder(
        inputs,
        generated_at=generated_at,
        score_config=score_config,
    )
    if type(report) is not PaperCandidateDecisionEngineReport:
        raise ValueError(
            "paper candidate decision engine report must be a "
            "PaperCandidateDecisionEngineReport",
        )
    require_paper_only_flags("PaperCandidateDecisionEngineReport", report)
    return report


def _load_candidate_inputs(
    *,
    candidate_bundles: tuple[PaperCandidateDecisionEngineCandidateBundle, ...]
    | list[PaperCandidateDecisionEngineCandidateBundle]
    | None,
    candidate_bundle_loader: Callable[[], object] | None,
    candidate_inputs: tuple[PaperCandidateDecisionEngineInput, ...]
    | list[PaperCandidateDecisionEngineInput]
    | None,
    candidate_input_loader: Callable[[], object] | None,
) -> tuple[PaperCandidateDecisionEngineInput, ...]:
    if candidate_bundles is not None:
        return _inputs_from_bundles("candidate_bundles", candidate_bundles)
    if candidate_bundle_loader is not None:
        if not callable(candidate_bundle_loader):
            raise ValueError("candidate_bundle_loader must be callable")
        return _inputs_from_bundles(
            "candidate_bundle_loader",
            candidate_bundle_loader(),
        )
    if candidate_inputs is not None:
        return _normalize_inputs("candidate_inputs", candidate_inputs)
    if candidate_input_loader is not None:
        if not callable(candidate_input_loader):
            raise ValueError("candidate_input_loader must be callable")
        return _normalize_inputs(
            "candidate_input_loader",
            candidate_input_loader(),
        )
    raise ValueError("exactly one candidate source is required")


def _inputs_from_bundles(
    label: str,
    value: object,
) -> tuple[PaperCandidateDecisionEngineInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{label} must be a list or tuple")
    bundles = tuple(value)
    inputs: list[PaperCandidateDecisionEngineInput] = []
    for index, bundle in enumerate(bundles):
        _require_bundle(f"{label}.{index}", bundle)
        inputs.append(paper_candidate_decision_engine_input_from_bundle(bundle))
    return tuple(inputs)


def _normalize_inputs(
    label: str,
    value: object,
) -> tuple[PaperCandidateDecisionEngineInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{label} must be a list or tuple")
    inputs = tuple(value)
    for index, input_value in enumerate(inputs):
        _require_input(f"{label}.{index}", input_value)
    return inputs


def _require_bundle(
    label: str,
    value: object,
) -> None:
    if type(value) is not PaperCandidateDecisionEngineCandidateBundle:
        raise ValueError(
            f"{label} must be exactly PaperCandidateDecisionEngineCandidateBundle",
        )
    require_paper_only_flags(label, value)
    _reject_unsafe_envelope_fields(label, value)
    _require_exact_adapter_outputs(value)


def _require_input(
    label: str,
    value: object,
) -> None:
    if type(value) is not PaperCandidateDecisionEngineInput:
        raise ValueError(f"{label} must be exactly PaperCandidateDecisionEngineInput")
    require_paper_only_flags(label, value)
    _reject_unsafe_envelope_fields(label, value)


def _require_score_config(value: object) -> None:
    if type(value) is not CandidateDecisionScoreConfig:
        raise ValueError("score_config must be a CandidateDecisionScoreConfig")
    require_paper_only_flags("CandidateDecisionScoreConfig", value)


def _require_generated_at(value: object) -> None:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")


def _require_exact_adapter_outputs(
    bundle: PaperCandidateDecisionEngineCandidateBundle,
) -> None:
    if type(bundle.cost_liquidity) is not CandidateDecisionCostLiquidityAdapterOutput:
        raise ValueError(
            "cost_liquidity must be a CandidateDecisionCostLiquidityAdapterOutput",
        )
    if type(bundle.evidence) is not CandidateDecisionEvidenceAdapterResult:
        raise ValueError("evidence must be a CandidateDecisionEvidenceAdapterResult")
    if type(bundle.resolution_risk) is not CandidateDecisionResolutionRiskAdapterReport:
        raise ValueError(
            "resolution_risk must be a CandidateDecisionResolutionRiskAdapterReport",
        )
    if type(bundle.team_memory) is not CandidateDecisionTeamMemoryAdapterResult:
        raise ValueError("team_memory must be a CandidateDecisionTeamMemoryAdapterResult")
    require_paper_only_flags(
        "CandidateDecisionCostLiquidityAdapterOutput",
        bundle.cost_liquidity,
    )
    require_paper_only_flags(
        "CandidateDecisionEvidenceAdapterResult",
        bundle.evidence,
    )
    require_paper_only_flags(
        "CandidateDecisionResolutionRiskAdapterReport",
        bundle.resolution_risk,
    )
    require_paper_only_flags(
        "CandidateDecisionTeamMemoryAdapterResult",
        bundle.team_memory,
    )


def _reject_unsafe_envelope_fields(label: str, value: object) -> None:
    field_names = getattr(value, "__dataclass_fields__", None)
    if type(field_names) is not dict:
        raise ValueError(f"{label} must be a dataclass instance")
    reject_unsafe_surface_fields(label, {field_name: None for field_name in field_names})


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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


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
    "PaperCandidateDecisionEngineCandidateBundle",
    "load_paper_candidate_decision_engine_report",
    "paper_candidate_decision_engine_input_from_bundle",
)
