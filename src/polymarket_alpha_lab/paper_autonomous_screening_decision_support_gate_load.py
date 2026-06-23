"""Read-only loader composition for the paper autonomous screening gate."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_store import (
    load_paper_action_gated_strategy_recommendation_queue_decision_support_reports,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
    build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from polymarket_alpha_lab.paper_project_screening_rank_stability_store import (
    load_paper_project_screening_rank_stability_reports,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryConfig,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
    PaperResearchPacketOperatorFlowDbHistoryGateConfig,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate_load import (
    load_paper_research_packet_operator_flow_db_history_gate_report,
)

__all__ = ("load_paper_autonomous_screening_decision_support_gate_report",)


def load_paper_autonomous_screening_decision_support_gate_report(
    connection: object,
    *,
    operator_flow_history_limit: int | None,
    operator_flow_table_name: str,
    operator_flow_history_config: PaperResearchPacketOperatorFlowDbHistoryConfig,
    operator_flow_gate_config: PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    action_gated_queue_limit: int | None,
    action_gated_queue_table_name: str,
    gate_config: object,
    generated_at: datetime,
    action_gated_queue_risk_status: str | None = None,
    action_gated_queue_risk_config_version: str | None = None,
    include_action_gated_queue_trend_report: bool = False,
    project_screening_rank_stability_limit: int | None = None,
    project_screening_rank_stability_table_name: str | None = None,
    project_screening_rank_stability_config_version: str | None = None,
    project_screening_rank_stability_status: str | None = None,
    operator_flow_gate_loader: Callable[..., object]
    = load_paper_research_packet_operator_flow_db_history_gate_report,
    action_gated_queue_loader: Callable[..., object]
    = load_paper_action_gated_strategy_recommendation_queue_decision_support_reports,
    action_gated_queue_trend_builder: Callable[..., object]
    = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
    project_screening_rank_stability_loader: Callable[..., object]
    = load_paper_project_screening_rank_stability_reports,
    gate_report_builder: Callable[..., object] | None = None,
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    if (
        type(operator_flow_history_config)
        is not PaperResearchPacketOperatorFlowDbHistoryConfig
    ):
        raise ValueError(
            "operator_flow_history_config must be a "
            "PaperResearchPacketOperatorFlowDbHistoryConfig",
        )
    if type(operator_flow_gate_config) is not PaperResearchPacketOperatorFlowDbHistoryGateConfig:
        raise ValueError(
            "operator_flow_gate_config must be a "
            "PaperResearchPacketOperatorFlowDbHistoryGateConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("operator_flow_history_config", operator_flow_history_config)
    _validate_hard_flags("operator_flow_gate_config", operator_flow_gate_config)
    _validate_hard_flags("gate_config", gate_config)
    _validate_rank_stability_options(
        project_screening_rank_stability_table_name=(
            project_screening_rank_stability_table_name
        ),
        project_screening_rank_stability_limit=project_screening_rank_stability_limit,
        project_screening_rank_stability_config_version=(
            project_screening_rank_stability_config_version
        ),
        project_screening_rank_stability_status=project_screening_rank_stability_status,
    )

    operator_flow_gate_report = operator_flow_gate_loader(
        connection,
        limit=operator_flow_history_limit,
        table_name=operator_flow_table_name,
        history_config=operator_flow_history_config,
        gate_config=operator_flow_gate_config,
        generated_at=generated_at,
    )
    _validate_hard_flags("operator_flow_gate_report", operator_flow_gate_report)

    loaded_action_gated_queue_reports = action_gated_queue_loader(
        connection,
        risk_status=action_gated_queue_risk_status,
        risk_config_version=action_gated_queue_risk_config_version,
        limit=action_gated_queue_limit,
        table_name=action_gated_queue_table_name,
    )
    # Store readbacks are newest-first; the trend builder expects chronological
    # oldest-to-newest input, and the latest pair remains at ``[-1]`` below.
    action_gated_queue_reports = tuple(reversed(tuple(loaded_action_gated_queue_reports)))
    _validate_hard_flags_tree(
        "action_gated_queue_reports",
        action_gated_queue_reports,
    )

    action_gated_queue_trend_report = None
    if include_action_gated_queue_trend_report:
        action_gated_queue_trend_report = action_gated_queue_trend_builder(
            action_gated_queue_reports,
            generated_at=generated_at,
        )
        _validate_hard_flags(
            "action_gated_queue_trend_report",
            action_gated_queue_trend_report,
        )

    project_screening_rank_stability_report = None
    if project_screening_rank_stability_table_name is not None:
        loaded_rank_stability_reports = project_screening_rank_stability_loader(
            connection,
            config_version=project_screening_rank_stability_config_version,
            stability_status=project_screening_rank_stability_status,
            limit=project_screening_rank_stability_limit,
            table_name=project_screening_rank_stability_table_name,
        )
        rank_stability_reports = tuple(loaded_rank_stability_reports)
        _validate_hard_flags_tree(
            "project_screening_rank_stability_reports",
            rank_stability_reports,
        )
        # Rank-stability store readbacks are newest-first; index 0 is latest.
        project_screening_rank_stability_report = (
            rank_stability_reports[0] if rank_stability_reports else None
        )

    if gate_report_builder is not None:
        gate_report = gate_report_builder(
            operator_flow_gate_report=operator_flow_gate_report,
            action_gated_queue_reports=action_gated_queue_reports,
            action_gated_queue_trend_report=action_gated_queue_trend_report,
            project_screening_rank_stability_report=(
                project_screening_rank_stability_report
            ),
            config=gate_config,
            generated_at=generated_at,
        )
        _validate_gate_report_output("gate_report_builder output", gate_report)
        return gate_report

    priority_report, risk_report = _latest_action_gated_queue_pair(
        action_gated_queue_reports,
    )
    gate_report = _load_default_gate_report_builder()(
        operator_flow_gate_report=operator_flow_gate_report,
        priority_report=priority_report,
        risk_report=risk_report,
        generated_at=generated_at,
        trend_report=action_gated_queue_trend_report,
        rank_stability_report=project_screening_rank_stability_report,
        config_version=_config_version(gate_config),
    )
    _validate_gate_report_output("gate report", gate_report)
    return gate_report


def _load_default_gate_report_builder() -> Callable[..., object]:
    module = __import__(
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate",
        fromlist=("build_paper_autonomous_screening_decision_support_gate_report",),
    )
    return module.build_paper_autonomous_screening_decision_support_gate_report


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


def _validate_gate_report_output(label: str, value: object) -> None:
    if type(value) is not PaperAutonomousScreeningDecisionSupportGateReport:
        raise ValueError(
            f"{label} must be a PaperAutonomousScreeningDecisionSupportGateReport",
        )
    _validate_hard_flags(label, value)


def _validate_rank_stability_options(
    *,
    project_screening_rank_stability_table_name: str | None,
    project_screening_rank_stability_limit: int | None,
    project_screening_rank_stability_config_version: str | None,
    project_screening_rank_stability_status: str | None,
) -> None:
    if project_screening_rank_stability_table_name is not None:
        return
    if any(
        value is not None
        for value in (
            project_screening_rank_stability_limit,
            project_screening_rank_stability_config_version,
            project_screening_rank_stability_status,
        )
    ):
        raise ValueError(
            "project_screening_rank_stability_table_name is required "
            "when rank filters are supplied",
        )


def _latest_action_gated_queue_pair(
    action_gated_queue_reports: tuple[object, ...],
) -> tuple[object, object]:
    if not action_gated_queue_reports:
        raise ValueError("action_gated_queue_reports is required")
    latest_pair = action_gated_queue_reports[-1]
    if type(latest_pair) is not tuple or len(latest_pair) != 2:
        raise ValueError("action_gated_queue_reports must contain priority/risk pairs")
    return latest_pair


def _config_version(gate_config: object) -> str:
    value = getattr(gate_config, "config_version", None)
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("gate_config config_version must be a canonical string")
    return value
