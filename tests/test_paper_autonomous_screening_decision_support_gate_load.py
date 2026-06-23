from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryConfig,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
    PaperResearchPacketOperatorFlowDbHistoryGateConfig,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_load import (
    load_paper_autonomous_screening_decision_support_gate_report,
)


GENERATED_AT = datetime(2026, 6, 23, 20, 0, tzinfo=UTC)


@dataclass(frozen=True)
class FakeReport:
    name: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeGateConfig:
    config_version: str = "paper-autonomous-screening-decision-support-gate-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class NoMutationConnection:
    def cursor(self) -> None:
        raise AssertionError("loader must not open cursors directly")

    def commit(self) -> None:
        raise AssertionError("loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("loader must not rollback")

    def close(self) -> None:
        raise AssertionError("loader must not close")

    def execute(self) -> None:
        raise AssertionError("loader must not execute directly")

    def executemany(self) -> None:
        raise AssertionError("loader must not execute directly")

    def insert(self) -> None:
        raise AssertionError("loader must not write")

    def update(self) -> None:
        raise AssertionError("loader must not write")

    def delete(self) -> None:
        raise AssertionError("loader must not write")

    def persist(self) -> None:
        raise AssertionError("loader must not persist")


def _gate_report() -> PaperAutonomousScreeningDecisionSupportGateReport:
    return PaperAutonomousScreeningDecisionSupportGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-autonomous-screening-decision-support-gate-v0",
        gate_status="pass",
        recommended_next_step="advance_paper_autonomous_screening_recommendations",
        reason_code_counts=(
            PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
                "paper_autonomous_screening_decision_support_gate_passed",
                1,
            ),
        ),
        reason_codes=("paper_autonomous_screening_decision_support_gate_passed",),
        operator_flow_gate_config_version=(
            "paper-research-packet-operator-flow-db-history-gate-v0"
        ),
        operator_flow_gate_generated_at=GENERATED_AT,
        operator_flow_gate_status="pass",
        operator_flow_recommended_next_step=(
            "allow_paper_autonomous_screening_decision_support"
        ),
        queue_priority_generated_at=GENERATED_AT,
        queue_risk_generated_at=GENERATED_AT,
        queue_risk_config_version="action-gated-queue-risk-v0",
        queue_risk_status="pass",
        queue_risk_recommended_next_step="allocate_paper_research_queue",
        queue_source_report_count=0,
        queue_research_ready_count=0,
        queue_watch_count=0,
        queue_blocked_count=0,
        queue_candidate_count=0,
        queue_ready_count=0,
        queue_candidate_watch_count=0,
        queue_candidate_blocked_count=0,
        queue_total_ready_notional=Decimal("0.000000"),
        queue_largest_ready_notional=Decimal("0.000000"),
        queue_top_research_priority_score=Decimal("0.000000"),
        queue_average_research_priority_score=Decimal("0.000000"),
        trend_source_snapshot_count=None,
        trend_latest_risk_status=None,
        trend_consecutive_latest_watch_count=None,
        trend_consecutive_latest_blocked_count=None,
        trend_duplicate_generated_at_count=None,
        rank_stability_status=None,
        rank_stable_ready_count=None,
        rank_unstable_ready_count=None,
        rank_blocked_count=None,
    )


def test_loader_composes_sources_and_calls_gate_reducer() -> None:
    connection = object()
    operator_flow_history_config = PaperResearchPacketOperatorFlowDbHistoryConfig()
    operator_flow_gate_config = PaperResearchPacketOperatorFlowDbHistoryGateConfig()
    gate_config = FakeGateConfig()
    operator_flow_gate_report = FakeReport("operator-flow-gate")
    latest_pair = (FakeReport("priority-latest"), FakeReport("risk-latest"))
    middle_pair = (FakeReport("priority-middle"), FakeReport("risk-middle"))
    earliest_pair = (FakeReport("priority-earliest"), FakeReport("risk-earliest"))
    trend_report = FakeReport("queue-trend")
    latest_rank_stability_report = FakeReport("rank-latest")
    older_rank_stability_report = FakeReport("rank-older")
    expected_gate_report = _gate_report()
    operator_loader_calls: list[dict[str, object]] = []
    action_queue_loader_calls: list[dict[str, object]] = []
    trend_builder_calls: list[dict[str, object]] = []
    rank_loader_calls: list[dict[str, object]] = []
    gate_builder_calls: list[dict[str, object]] = []

    def fake_operator_flow_gate_loader(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        history_config: PaperResearchPacketOperatorFlowDbHistoryConfig,
        gate_config: PaperResearchPacketOperatorFlowDbHistoryGateConfig,
        generated_at: datetime,
    ) -> FakeReport:
        operator_loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "history_config": history_config,
                "gate_config": gate_config,
                "generated_at": generated_at,
            },
        )
        return operator_flow_gate_report

    def fake_action_queue_loader(
        received_connection: object,
        *,
        risk_status: str | None,
        risk_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[tuple[FakeReport, FakeReport], ...]:
        action_queue_loader_calls.append(
            {
                "connection": received_connection,
                "risk_status": risk_status,
                "risk_config_version": risk_config_version,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (latest_pair, middle_pair, earliest_pair)

    def fake_trend_builder(
        action_gated_queue_reports: object,
        *,
        generated_at: datetime,
    ) -> FakeReport:
        trend_builder_calls.append(
            {
                "action_gated_queue_reports": action_gated_queue_reports,
                "generated_at": generated_at,
            },
        )
        return trend_report

    def fake_rank_stability_loader(
        received_connection: object,
        *,
        config_version: str | None,
        stability_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, FakeReport]:
        rank_loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "stability_status": stability_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (latest_rank_stability_report, older_rank_stability_report)

    def fake_gate_builder(
        *,
        operator_flow_gate_report: object,
        action_gated_queue_reports: object,
        action_gated_queue_trend_report: object,
        project_screening_rank_stability_report: object,
        config: object,
        generated_at: datetime,
    ) -> PaperAutonomousScreeningDecisionSupportGateReport:
        gate_builder_calls.append(
            {
                "operator_flow_gate_report": operator_flow_gate_report,
                "action_gated_queue_reports": action_gated_queue_reports,
                "action_gated_queue_trend_report": action_gated_queue_trend_report,
                "project_screening_rank_stability_report": (
                    project_screening_rank_stability_report
                ),
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_gate_report

    report = load_paper_autonomous_screening_decision_support_gate_report(
        connection,
        operator_flow_history_limit=3,
        operator_flow_table_name="operator_flow_reports",
        operator_flow_history_config=operator_flow_history_config,
        operator_flow_gate_config=operator_flow_gate_config,
        action_gated_queue_limit=5,
        action_gated_queue_table_name="action_queue_reports",
        action_gated_queue_risk_status="pass",
        action_gated_queue_risk_config_version="risk-v0",
        include_action_gated_queue_trend_report=True,
        project_screening_rank_stability_limit=2,
        project_screening_rank_stability_table_name="rank_stability_reports",
        project_screening_rank_stability_config_version="rank-v0",
        project_screening_rank_stability_status="stable",
        gate_config=gate_config,
        generated_at=GENERATED_AT,
        operator_flow_gate_loader=fake_operator_flow_gate_loader,
        action_gated_queue_loader=fake_action_queue_loader,
        action_gated_queue_trend_builder=fake_trend_builder,
        project_screening_rank_stability_loader=fake_rank_stability_loader,
        gate_report_builder=fake_gate_builder,
    )

    assert report is expected_gate_report
    assert operator_loader_calls == [
        {
            "connection": connection,
            "limit": 3,
            "table_name": "operator_flow_reports",
            "history_config": operator_flow_history_config,
            "gate_config": operator_flow_gate_config,
            "generated_at": GENERATED_AT,
        },
    ]
    assert action_queue_loader_calls == [
        {
            "connection": connection,
            "risk_status": "pass",
            "risk_config_version": "risk-v0",
            "limit": 5,
            "table_name": "action_queue_reports",
        },
    ]
    assert trend_builder_calls == [
        {
            "action_gated_queue_reports": (
                earliest_pair,
                middle_pair,
                latest_pair,
            ),
            "generated_at": GENERATED_AT,
        },
    ]
    assert rank_loader_calls == [
        {
            "connection": connection,
            "config_version": "rank-v0",
            "stability_status": "stable",
            "limit": 2,
            "table_name": "rank_stability_reports",
        },
    ]
    assert gate_builder_calls == [
        {
            "operator_flow_gate_report": operator_flow_gate_report,
            "action_gated_queue_reports": (
                earliest_pair,
                middle_pair,
                latest_pair,
            ),
            "action_gated_queue_trend_report": trend_report,
            "project_screening_rank_stability_report": latest_rank_stability_report,
            "config": gate_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_keeps_trend_and_rank_stability_optional() -> None:
    gate_builder_calls: list[dict[str, object]] = []
    expected_gate_report = _gate_report()

    def fake_gate_builder(
        **kwargs: object,
    ) -> PaperAutonomousScreeningDecisionSupportGateReport:
        gate_builder_calls.append(kwargs)
        return expected_gate_report

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("optional source must not be called")

    report = load_paper_autonomous_screening_decision_support_gate_report(
        object(),
        operator_flow_history_limit=None,
        operator_flow_table_name="operator_flow_reports",
        operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
        operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
        action_gated_queue_limit=None,
        action_gated_queue_table_name="action_queue_reports",
        gate_config=FakeGateConfig(),
        generated_at=GENERATED_AT,
        operator_flow_gate_loader=lambda *args, **kwargs: FakeReport("operator-gate"),
        action_gated_queue_loader=lambda *args, **kwargs: (),
        action_gated_queue_trend_builder=forbidden,
        project_screening_rank_stability_loader=forbidden,
        gate_report_builder=fake_gate_builder,
    )

    assert report == expected_gate_report
    assert gate_builder_calls[0]["action_gated_queue_reports"] == ()
    assert gate_builder_calls[0]["action_gated_queue_trend_report"] is None
    assert gate_builder_calls[0]["project_screening_rank_stability_report"] is None


def test_loader_rejects_invalid_phase_1_flags_before_gate_reducer() -> None:
    gate_builder_calls: list[object] = []

    def fake_gate_builder(**kwargs: object) -> FakeReport:
        gate_builder_calls.append(kwargs)
        return FakeReport("autonomous-gate")

    with pytest.raises(ValueError, match="gate_config must be paper_only"):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(paper_only=False),
            generated_at=GENERATED_AT,
            gate_report_builder=fake_gate_builder,
        )

    with pytest.raises(ValueError, match="operator_flow_gate_report must be readonly"):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=lambda *args, **kwargs: FakeReport(
                "operator-gate",
                readonly=False,
            ),
            gate_report_builder=fake_gate_builder,
        )

    with pytest.raises(ValueError, match="action_gated_queue_reports.0.1 must be report_only"):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=lambda *args, **kwargs: FakeReport("operator-gate"),
            action_gated_queue_loader=lambda *args, **kwargs: (
                (FakeReport("priority"), FakeReport("risk", report_only=False)),
            ),
            gate_report_builder=fake_gate_builder,
        )

    assert gate_builder_calls == []


def test_loader_rejects_injected_gate_builder_returning_non_gate_report() -> None:
    with pytest.raises(
        ValueError,
        match="gate_report_builder output must be a PaperAutonomousScreeningDecisionSupportGateReport",
    ):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=lambda *args, **kwargs: FakeReport("operator-gate"),
            action_gated_queue_loader=lambda *args, **kwargs: (),
            gate_report_builder=lambda **kwargs: FakeReport("not-autonomous-gate"),
        )


def test_loader_rejects_injected_gate_builder_output_with_false_hard_flags() -> None:
    invalid_report = _gate_report()
    object.__setattr__(invalid_report, "readonly", False)

    with pytest.raises(
        ValueError,
        match="gate_report_builder output must be readonly",
    ):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=lambda *args, **kwargs: FakeReport("operator-gate"),
            action_gated_queue_loader=lambda *args, **kwargs: (),
            gate_report_builder=lambda **kwargs: invalid_report,
        )


def test_loader_rejects_injected_trend_builder_output_with_false_hard_flags() -> None:
    def forbidden_gate_builder(**kwargs: object) -> object:
        raise AssertionError("gate builder must not run with invalid trend report")

    with pytest.raises(
        ValueError,
        match="action_gated_queue_trend_report must be readonly",
    ):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            include_action_gated_queue_trend_report=True,
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=lambda *args, **kwargs: FakeReport("operator-gate"),
            action_gated_queue_loader=lambda *args, **kwargs: (
                (FakeReport("priority"), FakeReport("risk")),
            ),
            action_gated_queue_trend_builder=lambda *args, **kwargs: FakeReport(
                "trend",
                readonly=False,
            ),
            gate_report_builder=forbidden_gate_builder,
        )


@pytest.mark.parametrize(
    "rank_filter_kwargs",
    (
        {"project_screening_rank_stability_limit": 1},
        {"project_screening_rank_stability_config_version": "rank-v0"},
        {"project_screening_rank_stability_status": "stable"},
    ),
)
def test_loader_rejects_rank_filters_without_rank_table_name(
    rank_filter_kwargs: dict[str, object],
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("source loaders must not run for invalid rank filters")

    with pytest.raises(
        ValueError,
        match="project_screening_rank_stability_table_name is required",
    ):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=forbidden,
            action_gated_queue_loader=forbidden,
            gate_report_builder=lambda **kwargs: _gate_report(),
            **rank_filter_kwargs,
        )


def test_loader_rejects_non_exact_operator_flow_configs_before_source_load() -> None:
    class HistoryConfigSubclass(PaperResearchPacketOperatorFlowDbHistoryConfig):
        pass

    class GateConfigSubclass(PaperResearchPacketOperatorFlowDbHistoryGateConfig):
        pass

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("source loader must not be called for invalid config")

    with pytest.raises(
        ValueError,
        match="operator_flow_history_config must be a PaperResearchPacketOperatorFlowDbHistoryConfig",
    ):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=HistoryConfigSubclass(),
            operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=forbidden,
        )

    with pytest.raises(
        ValueError,
        match="operator_flow_gate_config must be a PaperResearchPacketOperatorFlowDbHistoryGateConfig",
    ):
        load_paper_autonomous_screening_decision_support_gate_report(
            object(),
            operator_flow_history_limit=None,
            operator_flow_table_name="operator_flow_reports",
            operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
            operator_flow_gate_config=GateConfigSubclass(),
            action_gated_queue_limit=None,
            action_gated_queue_table_name="action_queue_reports",
            gate_config=FakeGateConfig(),
            generated_at=GENERATED_AT,
            operator_flow_gate_loader=forbidden,
        )


def test_loader_does_not_manage_connection_lifecycle_or_write() -> None:
    connection = NoMutationConnection()
    seen_connections: list[object] = []

    def fake_operator_flow_gate_loader(received_connection: object, **kwargs: object) -> FakeReport:
        seen_connections.append(received_connection)
        return FakeReport("operator-gate")

    def fake_action_queue_loader(
        received_connection: object,
        **kwargs: object,
    ) -> tuple[()]:
        seen_connections.append(received_connection)
        return ()

    report = load_paper_autonomous_screening_decision_support_gate_report(
        connection,
        operator_flow_history_limit=None,
        operator_flow_table_name="operator_flow_reports",
        operator_flow_history_config=PaperResearchPacketOperatorFlowDbHistoryConfig(),
        operator_flow_gate_config=PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
        action_gated_queue_limit=None,
        action_gated_queue_table_name="action_queue_reports",
        gate_config=FakeGateConfig(),
        generated_at=GENERATED_AT,
        operator_flow_gate_loader=fake_operator_flow_gate_loader,
        action_gated_queue_loader=fake_action_queue_loader,
        gate_report_builder=lambda **kwargs: _gate_report(),
    )

    assert report == _gate_report()
    assert seen_connections == [connection, connection]


def test_loader_module_has_no_db_lifecycle_live_or_mutation_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_screening_decision_support_gate_load.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    imported_names: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    allowed_modules = {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_store",
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend",
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate",
        "polymarket_alpha_lab.paper_project_screening_rank_stability_store",
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history",
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate",
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate_load",
    }
    banned_import_names = {
        "append_paper_trade_journal",
        "build_paper_project_screening_report",
        "create_public_client",
        "fetch_live_markets",
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_report",
        "insert_paper_project_screening_rank_stability_report",
        "run_strategy_cycle",
        "run_paper_execution",
    }
    banned_module_names = {
        "polymarket_alpha_lab.auth",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.client",
        "polymarket_alpha_lab.journal",
        "polymarket_alpha_lab.paper_execution",
        "polymarket_alpha_lab.project_screening",
        "polymarket_alpha_lab.strategy_cycle",
    }
    banned_module_fragments = (
        "live",
        "exchange",
        "wallet",
        "account",
        "order",
        "psycopg",
    )
    banned_call_or_attribute_names = {
        "api_key",
        "cancel",
        "close",
        "commit",
        "connect",
        "create_order",
        "cursor",
        "delete",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "persist",
        "private_key",
        "replace_order",
        "rollback",
        "sign",
        "submit",
        "update",
        "wallet",
    }

    assert set(imported_modules) <= allowed_modules
    assert not (set(imported_names) & banned_import_names)
    assert not (set(imported_modules) & banned_module_names)
    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
