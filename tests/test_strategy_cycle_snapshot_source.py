import ast
import importlib
import inspect
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


GENERATED_AT = datetime(2026, 6, 19, 18, 30, tzinfo=UTC)
CONFIG_VERSION = "strategy-cycle-snapshot-source-v0"
SAFETY_FLAGS = ("paper_only", "report_only", "readonly")
PIPELINE_STAGE_NAMES = (
    "market_scan",
    "market_consideration",
    "cost_aware_snapshot",
    "project_screening",
)
GATE_NAMES = (
    "data_integrity",
    "confidence",
    "spread",
    "resolution_risk",
    "yes_depth",
    "no_depth",
    "edge_threshold",
)


def _build_strategy_cycle_snapshot_source_report(
    cycle_report: object,
) -> PaperRecommendationCycleSnapshotReport:
    from polymarket_alpha_lab.strategy_cycle_snapshot_source import (
        build_strategy_cycle_snapshot_source_report,
    )

    return build_strategy_cycle_snapshot_source_report(cycle_report)


def _cycle_report(
    *,
    scan_market_count: int,
    considered_count: int,
    snapshot_ready_count: int,
    cost_aware_report_count: int,
    blocked_counts: tuple[tuple[str, int], ...],
    screening_report: PaperProjectScreeningReport | None,
    cost_aware_reports: tuple[PaperCostAwareEventStrategyReport, ...] = (),
) -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        scan_market_count=scan_market_count,
        considered_count=considered_count,
        snapshot_ready_count=snapshot_ready_count,
        cost_aware_report_count=cost_aware_report_count,
        blocked_counts=blocked_counts,
        screening_report=screening_report,
        cost_aware_reports=cost_aware_reports,
    )


def _screening_gate_results() -> tuple[PaperProjectScreeningGateResult, ...]:
    return (
        PaperProjectScreeningGateResult(
            gate_name="input_count",
            status="pass",
            reason_code="source_reports_supplied",
            message="At least one source report is supplied.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="candidate_types",
            status="pass",
            reason_code="source_report_types_ready",
            message="Every candidate source is a cost-aware event strategy report.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="unique_slugs",
            status="pass",
            reason_code="unique_market_slugs",
            message="Every source report has a unique market slug.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="screenable_candidates",
            status="pass",
            reason_code="screenable_candidates_ready",
            message="At least one candidate can be screened.",
            observed_value=1,
            threshold=1,
        ),
    )


def _screening_report() -> PaperProjectScreeningReport:
    candidate = PaperProjectScreeningCandidate(
        market_slug="alpha-market",
        question="Will alpha resolve yes",
        source_status="paper_review_ready",
        scoring_side="yes",
        valid_depth=True,
        net_edge_per_share=Decimal("0.060000"),
        total_cost_per_share=Decimal("0.020000"),
        ask_size=Decimal("125.0000"),
        edge_component=Decimal("0.060000"),
        confidence_component=Decimal("0.240000"),
        depth_component=Decimal("0.100000"),
        spread_penalty=Decimal("0.010000"),
        resolution_risk_penalty=Decimal("0.020000"),
        cost_penalty=Decimal("0.006000"),
        screening_score=Decimal("0.364000"),
        screening_status="screening_ready",
        reason_codes=("source_paper_review_ready", "yes_depth_ready"),
    )
    queue_item = PaperProjectScreeningQueueItem(
        queue_position=1,
        market_slug=candidate.market_slug,
        question=candidate.question,
        research_bucket="research_ready",
        screening_score=candidate.screening_score,
        source_status=candidate.source_status,
        scoring_side=candidate.scoring_side,
        reason_codes=candidate.reason_codes,
    )
    return PaperProjectScreeningReport(
        generated_at=GENERATED_AT,
        config_version="project-screening-v0",
        candidate_count=1,
        ready_count=1,
        watch_count=0,
        defer_count=0,
        blocked_count=0,
        gate_results=_screening_gate_results(),
        candidates=(candidate,),
        queue_items=(queue_item,),
    )


def _cost_aware_gate_results() -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    return tuple(
        PaperCostAwareEventStrategyGateResult(
            gate_name=gate_name,
            status="pass",
            reason_code=f"{gate_name}_ready",
            message=f"{gate_name} ready.",
            observed_value=Decimal("1"),
            threshold=Decimal("0"),
        )
        for gate_name in GATE_NAMES
    )


def _cost_aware_side_result(side: str) -> PaperCostAwareEventSideResult:
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=Decimal("0.6200"),
        executable_price=Decimal("0.5000"),
        ask_size=Decimal("10.0000"),
        gross_edge_per_share=Decimal("0.030000"),
        fee_cost_per_share=Decimal("0.000000"),
        non_fee_cost_per_share=Decimal("0.000000"),
        total_cost_per_share=Decimal("0.000000"),
        net_edge_per_share=Decimal("0.030000"),
        reason_codes=("paper_edge_complete",),
    )


def _cost_aware_report(market_slug: str) -> PaperCostAwareEventStrategyReport:
    return PaperCostAwareEventStrategyReport(
        generated_at=GENERATED_AT,
        config_version="cost-aware-event-v0",
        market_slug=market_slug,
        question=f"{market_slug}?",
        fair_probability_yes=Decimal("0.6200"),
        confidence=Decimal("0.8000"),
        yes_bid=Decimal("0.4900"),
        no_bid=Decimal("0.4800"),
        spread=Decimal("0.0200"),
        resolution_risk=Decimal("0.0500"),
        selected_side="yes",
        status="paper_review_ready",
        yes_result=_cost_aware_side_result("yes"),
        no_result=_cost_aware_side_result("no"),
        gate_results=_cost_aware_gate_results(),
    )


def _stage_by_name(report: PaperRecommendationCycleSnapshotReport):
    return {stage.stage_name: stage for stage in report.pipeline_report.stages}


def _row_by_name(report: PaperRecommendationCycleSnapshotReport):
    return {row.artifact_name: row for row in report.artifact_index_report.rows}


def test_strategy_cycle_snapshot_source_converts_blocked_cycle_without_screening():
    cycle_report = _cycle_report(
        scan_market_count=4,
        considered_count=3,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(
            ("blocked_fetch_error", 2),
            ("blocked_non_binary_market", 1),
        ),
        screening_report=None,
    )
    assert not hasattr(cycle_report, "readonly")

    snapshot = _build_strategy_cycle_snapshot_source_report(cycle_report)

    assert isinstance(snapshot, PaperRecommendationCycleSnapshotReport)
    assert snapshot.generated_at == GENERATED_AT
    assert snapshot.config_version == CONFIG_VERSION
    assert snapshot.paper_only is True
    assert snapshot.report_only is True
    assert snapshot.readonly is True
    assert snapshot.final_status == "blocked"

    assert snapshot.pipeline_report.generated_at == GENERATED_AT
    assert snapshot.pipeline_report.config_version == CONFIG_VERSION
    assert (
        tuple(stage.stage_name for stage in snapshot.pipeline_report.stages)
        == PIPELINE_STAGE_NAMES
    )
    stages = _stage_by_name(snapshot)
    assert stages["market_scan"].status == "pass"
    assert stages["market_scan"].input_count == 0
    assert stages["market_scan"].output_count == 4
    assert stages["market_consideration"].status == "pass"
    assert stages["market_consideration"].input_count == 4
    assert stages["market_consideration"].output_count == 3
    assert stages["cost_aware_snapshot"].status == "blocked"
    assert stages["cost_aware_snapshot"].input_count == 3
    assert stages["cost_aware_snapshot"].output_count == 0
    assert stages["project_screening"].status == "blocked"
    assert stages["project_screening"].input_count == 0
    assert stages["project_screening"].output_count == 0

    assert snapshot.artifact_index_report.generated_at == GENERATED_AT
    assert snapshot.artifact_index_report.config_version == CONFIG_VERSION
    assert snapshot.artifact_index_report.flags == SAFETY_FLAGS
    rows = _row_by_name(snapshot)
    assert "paper_strategy_cycle_report" not in rows
    assert "strategy_cycle_blocked_counts" in rows
    assert "strategy_cycle_cost_aware_reports" in rows
    assert "strategy_cycle_screening_report" in rows
    assert rows["strategy_cycle_blocked_counts"].status == "blocked"
    assert rows["strategy_cycle_blocked_counts"].item_count == 3
    assert rows["strategy_cycle_blocked_counts"].reason_codes == (
        "blocked_fetch_error",
        "blocked_non_binary_market",
    )
    assert rows["strategy_cycle_cost_aware_reports"].status == "watch"
    assert rows["strategy_cycle_cost_aware_reports"].item_count == 0
    assert rows["strategy_cycle_cost_aware_reports"].reason_codes == (
        "no_cost_aware_reports",
    )
    assert rows["strategy_cycle_screening_report"].status == "blocked"
    assert rows["strategy_cycle_screening_report"].item_count == 0
    assert rows["strategy_cycle_screening_report"].reason_codes == (
        "missing_screening_report",
    )
    assert all(row.flags[:3] == SAFETY_FLAGS for row in rows.values())
    assert "blocked_fetch_error" in snapshot.reason_codes
    assert "blocked_non_binary_market" in snapshot.reason_codes
    assert "missing_screening_report" in snapshot.reason_codes


def test_strategy_cycle_snapshot_source_surfaces_cost_aware_mismatch_with_screening_report():
    screening_report = _screening_report()
    cycle_report = _cycle_report(
        scan_market_count=2,
        considered_count=1,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(),
        screening_report=screening_report,
    )
    assert not hasattr(screening_report, "readonly")

    snapshot = _build_strategy_cycle_snapshot_source_report(cycle_report)

    assert snapshot.generated_at == GENERATED_AT
    assert snapshot.config_version == CONFIG_VERSION
    assert snapshot.final_status == "blocked"
    assert snapshot.stage_count == 4
    assert snapshot.artifact_count == snapshot.artifact_index_report.row_count
    assert snapshot.blocked_artifact_count == 1
    assert snapshot.watch_artifact_count == 0
    assert snapshot.paper_only is True
    assert snapshot.report_only is True
    assert snapshot.readonly is True

    assert (
        tuple(stage.stage_name for stage in snapshot.pipeline_report.stages)
        == PIPELINE_STAGE_NAMES
    )
    stages = _stage_by_name(snapshot)
    assert tuple(stage.status for stage in snapshot.pipeline_report.stages) == (
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert stages["project_screening"].input_count == 1
    assert stages["project_screening"].output_count == 1

    rows = _row_by_name(snapshot)
    assert "paper_strategy_cycle_report" not in rows
    assert "paper_project_screening_report" not in rows
    assert "strategy_cycle_cost_aware_reports" in rows
    assert "strategy_cycle_screening_report" in rows
    assert rows["strategy_cycle_cost_aware_reports"].status == "blocked"
    assert rows["strategy_cycle_cost_aware_reports"].item_count == 0
    assert rows["strategy_cycle_cost_aware_reports"].reason_codes == (
        "cost_aware_report_count_mismatch",
    )
    assert rows["strategy_cycle_blocked_counts"].status == "pass"
    assert rows["strategy_cycle_blocked_counts"].item_count == 0
    assert rows["strategy_cycle_blocked_counts"].reason_codes == ()
    assert rows["strategy_cycle_screening_report"].status == "pass"
    assert rows["strategy_cycle_screening_report"].item_count == 1
    assert rows["strategy_cycle_screening_report"].reason_codes == (
        "screening_ready_candidates",
    )
    assert all(row.flags[:3] == SAFETY_FLAGS for row in rows.values())


def test_strategy_cycle_snapshot_source_uses_rich_cost_aware_artifacts_when_available():
    screening_report = _screening_report()
    cycle_report = _cycle_report(
        scan_market_count=2,
        considered_count=1,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(),
        screening_report=screening_report,
        cost_aware_reports=(_cost_aware_report("alpha-market"),),
    )

    snapshot = _build_strategy_cycle_snapshot_source_report(cycle_report)

    assert (
        tuple(stage.stage_name for stage in snapshot.pipeline_report.stages)
        == PIPELINE_STAGE_NAMES
    )
    rows = _row_by_name(snapshot)
    assert tuple(rows) == (
        "strategy_cycle_blocked_counts",
        "strategy_cycle_cost_aware_reports",
        "strategy_cycle_screening_report",
    )
    cost_aware_row = rows["strategy_cycle_cost_aware_reports"]
    assert cost_aware_row.status == "pass"
    assert cost_aware_row.item_count == 1
    assert cost_aware_row.reason_codes == ("cost_aware_paper_review_ready",)
    assert snapshot.artifact_count == 3
    assert snapshot.final_status == "pass"
    assert all(row.flags[:3] == SAFETY_FLAGS for row in rows.values())


def test_strategy_cycle_snapshot_source_rejects_wrong_input_type():
    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        _build_strategy_cycle_snapshot_source_report(object())


def test_strategy_cycle_snapshot_source_has_no_db_api_auth_order_imports():
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_cycle_snapshot_source",
    )

    tree = ast.parse(inspect.getsource(module))
    forbidden_import_roots = {
        "aiohttp",
        "asyncpg",
        "eth_account",
        "httpx",
        "polymarket",
        "polymarket_clob_client",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
        "websocket",
        "websockets",
    }
    forbidden_polymarket_modules = {
        "polymarket_alpha_lab.api",
        "polymarket_alpha_lab.journal",
        "polymarket_alpha_lab.paper",
        "polymarket_alpha_lab.paper_execution",
        "polymarket_alpha_lab.positions",
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row",
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_store",
    }
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "connect",
        "create_order",
        "delete",
        "login",
        "patch",
        "post",
        "put",
        "request",
        "sign",
        "sign_message",
        "submit_order",
    }

    imported_roots: set[str] = set()
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                imported_roots.add(alias.name.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert all(
        imported_module != forbidden_module
        and not imported_module.startswith(f"{forbidden_module}.")
        for imported_module in imported_modules
        for forbidden_module in forbidden_polymarket_modules
    )
    assert called_names.isdisjoint(forbidden_call_names)
