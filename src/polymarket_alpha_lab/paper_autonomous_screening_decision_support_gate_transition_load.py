"""Read-only loader composition for paper autonomous screening transitions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE,
    load_paper_autonomous_screening_decision_support_gate_reports,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION,
    PaperAutonomousScreeningDecisionSupportGateTransitionReport,
    build_paper_autonomous_screening_decision_support_gate_transition_report,
)


__all__ = (
    "load_paper_autonomous_screening_decision_support_gate_transition_report",
)


def load_paper_autonomous_screening_decision_support_gate_transition_report(
    connection: object,
    *,
    screening_gate_config_version: str | None = None,
    screening_gate_status: str | None = None,
    screening_gate_queue_risk_config_version: str | None = None,
    screening_gate_operator_flow_gate_status: str | None = None,
    screening_gate_limit: int | None = None,
    screening_gate_table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
    ),
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION
    ),
    generated_at: datetime | None = None,
    screening_gate_loader: Callable[..., object] = (
        load_paper_autonomous_screening_decision_support_gate_reports
    ),
    transition_report_builder: Callable[..., object] = (
        build_paper_autonomous_screening_decision_support_gate_transition_report
    ),
) -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    _require_canonical_string("config_version", config_version)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    loaded_gate_reports = screening_gate_loader(
        connection,
        config_version=screening_gate_config_version,
        gate_status=screening_gate_status,
        queue_risk_config_version=screening_gate_queue_risk_config_version,
        operator_flow_gate_status=screening_gate_operator_flow_gate_status,
        limit=screening_gate_limit,
        table_name=screening_gate_table_name,
    )
    gate_reports = tuple(reversed(tuple(loaded_gate_reports)))
    _validate_hard_flags_tree("screening_gate_reports", gate_reports)

    transition_report = transition_report_builder(
        gate_reports,
        config_version=config_version,
        generated_at=generated_at,
    )
    _validate_transition_report_output(
        "transition_report_builder output",
        transition_report,
    )
    return transition_report


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


def _validate_transition_report_output(label: str, value: object) -> None:
    if type(value) is not PaperAutonomousScreeningDecisionSupportGateTransitionReport:
        raise ValueError(
            f"{label} must be a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionReport",
        )
    _validate_hard_flags(label, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
