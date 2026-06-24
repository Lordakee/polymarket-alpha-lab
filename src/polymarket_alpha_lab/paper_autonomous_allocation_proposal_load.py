"""Read-only loader composition for paper autonomous allocation proposals."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store import (
    load_paper_action_gated_strategy_recommendation_queue_reports,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_store import (
    load_paper_action_gated_strategy_recommendation_queue_decision_support_reports,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_psycopg_read import (
    PaperAutonomousScreeningDecisionSupportGateReadOptions,
    load_paper_autonomous_screening_decision_support_gate_reports,
)


__all__ = ("load_paper_autonomous_allocation_proposal_report",)


DEFAULT_ALLOCATION_CONFIG_VERSION = "paper-recommendation-allocation-v0"
DEFAULT_TOTAL_PAPER_BUDGET = Decimal("100.000000")
DEFAULT_PER_BUCKET_PAPER_NOTIONAL_CAP = Decimal("25.000000")


def load_paper_autonomous_allocation_proposal_report(
    connection: object,
    *,
    screening_gate_limit: int | None,
    screening_gate_table_name: str,
    action_gated_queue_decision_support_limit: int | None,
    action_gated_queue_decision_support_table_name: str,
    source_queue_limit: int | None,
    source_queue_table_name: str,
    generated_at: datetime,
    config: object | None = None,
    screening_gate_loader: Callable[..., object] = (
        load_paper_autonomous_screening_decision_support_gate_reports
    ),
    action_gated_queue_decision_support_loader: Callable[..., object] = (
        load_paper_action_gated_strategy_recommendation_queue_decision_support_reports
    ),
    source_queue_loader: Callable[..., object] = (
        load_paper_action_gated_strategy_recommendation_queue_reports
    ),
    proposal_report_builder: Callable[..., object] | None = None,
    proposal_report_type: type | None = None,
) -> object:
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    resolved_config = config if config is not None else _default_config()
    _validate_hard_flags("config", resolved_config)

    screening_gate_reports = tuple(
        screening_gate_loader(
            connection,
            options=PaperAutonomousScreeningDecisionSupportGateReadOptions(
                limit=_required_limit("screening_gate_limit", screening_gate_limit),
                table_name=screening_gate_table_name,
            ),
        ),
    )
    if not screening_gate_reports:
        raise ValueError("screening gate reports are required")
    screening_gate_report = screening_gate_reports[0]
    _validate_hard_flags("screening_gate_report", screening_gate_report)

    decision_support_reports = tuple(
        action_gated_queue_decision_support_loader(
            connection,
            risk_status=None,
            risk_config_version=None,
            limit=action_gated_queue_decision_support_limit,
            table_name=action_gated_queue_decision_support_table_name,
        ),
    )
    _validate_hard_flags_tree("decision_support_reports", decision_support_reports)
    priority_report, risk_report = _latest_decision_support_pair(
        decision_support_reports,
    )

    source_queue_reports = tuple(
        source_queue_loader(
            connection,
            source_config_version=None,
            action_status=None,
            limit=source_queue_limit,
            table_name=source_queue_table_name,
        ),
    )
    if not source_queue_reports:
        raise ValueError("source queue reports are required")
    _validate_hard_flags_tree("source_queue_reports", source_queue_reports)

    builder = (
        proposal_report_builder
        if proposal_report_builder is not None
        else _load_default_proposal_report_builder()
    )
    expected_report_type = (
        proposal_report_type
        if proposal_report_type is not None
        else _load_default_proposal_report_type()
    )
    if not isinstance(expected_report_type, type):
        raise ValueError("proposal_report_type must be a type")

    report = builder(
        screening_gate_report=screening_gate_report,
        priority_report=priority_report,
        risk_report=risk_report,
        source_queue_reports=source_queue_reports,
        config=resolved_config,
        generated_at=generated_at,
    )
    _validate_proposal_report_output(
        "proposal report",
        report,
        expected_report_type,
    )
    return report


def _default_config() -> object:
    allocation_config_type = _load_default_allocation_config_type()
    proposal_config_type = _load_default_proposal_config_type()
    allocation_config = allocation_config_type(
        config_version=DEFAULT_ALLOCATION_CONFIG_VERSION,
        total_paper_budget=DEFAULT_TOTAL_PAPER_BUDGET,
        max_paper_notional_per_market=DEFAULT_PER_BUCKET_PAPER_NOTIONAL_CAP,
        max_paper_notional_per_event=DEFAULT_PER_BUCKET_PAPER_NOTIONAL_CAP,
        max_paper_notional_per_theme=DEFAULT_PER_BUCKET_PAPER_NOTIONAL_CAP,
        max_paper_notional_per_correlation_group=(
            DEFAULT_PER_BUCKET_PAPER_NOTIONAL_CAP
        ),
    )
    return proposal_config_type(
        config_version=_load_default_config_version(),
        allocation_config=allocation_config,
    )


def _load_default_proposal_report_builder() -> Callable[..., object]:
    module = __import__(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal",
        fromlist=("build_paper_autonomous_allocation_proposal_report",),
    )
    return module.build_paper_autonomous_allocation_proposal_report


def _load_default_proposal_report_type() -> type:
    module = __import__(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal",
        fromlist=("PaperAutonomousAllocationProposalReport",),
    )
    return module.PaperAutonomousAllocationProposalReport


def _load_default_proposal_config_type() -> type:
    module = __import__(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal",
        fromlist=("PaperAutonomousAllocationProposalConfig",),
    )
    return module.PaperAutonomousAllocationProposalConfig


def _load_default_config_version() -> str:
    module = __import__(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal",
        fromlist=("DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION",),
    )
    return module.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION


def _load_default_allocation_config_type() -> type:
    module = __import__(
        "polymarket_alpha_lab.paper_recommendation_allocation",
        fromlist=("PaperRecommendationAllocationConfig",),
    )
    return module.PaperRecommendationAllocationConfig


def _latest_decision_support_pair(
    decision_support_reports: tuple[object, ...],
) -> tuple[object, object]:
    if not decision_support_reports:
        raise ValueError("decision-support reports are required")
    latest_pair = decision_support_reports[0]
    if type(latest_pair) is not tuple or len(latest_pair) != 2:
        raise ValueError("latest decision-support report must be a priority/risk pair")
    return latest_pair


def _required_limit(field_name: str, value: int | None) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _validate_hard_flags_tree(label: str, value: object) -> None:
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _validate_hard_flags_tree(f"{label}.{index}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_hard_flags_tree(f"{label}.{index}", item)
        return
    _validate_hard_flags(label, value)


def _validate_proposal_report_output(
    label: str,
    value: object,
    expected_report_type: type,
) -> None:
    if type(value) is not expected_report_type:
        raise ValueError(f"{label} must be a {expected_report_type.__name__}")
    _validate_hard_flags(label, value)
