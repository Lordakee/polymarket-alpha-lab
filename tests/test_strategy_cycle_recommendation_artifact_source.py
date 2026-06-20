import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import inspect

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport
from polymarket_alpha_lab.strategy_cycle_recommendation_artifact_source import (
    build_strategy_cycle_recommendation_artifacts,
)


GENERATED_AT = datetime(2026, 6, 19, 19, 15, tzinfo=UTC)
CONFIG_VERSION = "strategy-cycle-recommendation-artifact-source-v0"
SAFETY_FLAGS = ("paper_only", "report_only", "readonly")
GATE_NAMES = (
    "data_integrity",
    "confidence",
    "spread",
    "resolution_risk",
    "yes_depth",
    "no_depth",
    "edge_threshold",
)


@dataclass(frozen=True)
class FakeLegacyCycleReport:
    __module__ = "polymarket_alpha_lab.strategy_cycle"
    generated_at: datetime = GENERATED_AT
    config_version: str = CONFIG_VERSION
    scan_market_count: int = 0
    considered_count: int = 0
    snapshot_ready_count: int = 0
    cost_aware_report_count: int = 0
    blocked_counts: tuple[tuple[str, int], ...] = ()
    screening_report: object | None = None
    paper_only: bool = True
    report_only: bool = True


@dataclass(frozen=True)
class FakeScreeningReport:
    ready_count: int = 1
    blocked_count: int = 0
    watch_count: int = 0
    defer_count: int = 0
    paper_only: bool = True
    report_only: bool = True


def _cycle_report(
    *,
    scan_market_count: int = 0,
    considered_count: int = 0,
    snapshot_ready_count: int = 0,
    cost_aware_report_count: int = 0,
    blocked_counts: tuple[tuple[str, int], ...] = (),
    screening_report: object | None = None,
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


def _enriched_cycle_report(
    *,
    scan_market_count: int = 0,
    considered_count: int = 0,
    snapshot_ready_count: int = 0,
    cost_aware_report_count: int = 0,
    blocked_counts: tuple[tuple[str, int], ...] = (),
    screening_report: object | None = None,
    cost_aware_reports: tuple[PaperCostAwareEventStrategyReport, ...] = (),
) -> FakeLegacyCycleReport:
    report = FakeLegacyCycleReport(
        scan_market_count=scan_market_count,
        considered_count=considered_count,
        snapshot_ready_count=snapshot_ready_count,
        cost_aware_report_count=cost_aware_report_count,
        blocked_counts=blocked_counts,
        screening_report=screening_report,
    )
    object.__setattr__(report, "cost_aware_reports", cost_aware_reports)
    return report


def _artifact_by_name(artifacts: tuple[object, ...]) -> dict[str, object]:
    return {artifact.artifact_name: artifact for artifact in artifacts}


def _gate_results(
    *,
    failing_gate_name: str | None = None,
) -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    return tuple(
        PaperCostAwareEventStrategyGateResult(
            gate_name=gate_name,
            status="fail" if gate_name == failing_gate_name else "pass",
            reason_code=f"{gate_name}_ready",
            message=f"{gate_name} ready.",
            observed_value=Decimal("1"),
            threshold=Decimal("0"),
        )
        for gate_name in GATE_NAMES
    )


def _side_result(
    side: str,
    *,
    net_edge_per_share: Decimal | None = Decimal("0.030000"),
) -> PaperCostAwareEventSideResult:
    has_edge = net_edge_per_share is not None
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=Decimal("0.6200"),
        executable_price=Decimal("0.5000") if has_edge else None,
        ask_size=Decimal("10.0000") if has_edge else None,
        gross_edge_per_share=net_edge_per_share,
        fee_cost_per_share=Decimal("0.000000") if has_edge else None,
        non_fee_cost_per_share=Decimal("0.000000") if has_edge else None,
        total_cost_per_share=Decimal("0.000000") if has_edge else None,
        net_edge_per_share=net_edge_per_share,
        reason_codes=("paper_edge_complete",) if has_edge else ("missing_ask",),
    )


def _cost_aware_report(
    market_slug: str,
    *,
    status: str = "paper_review_ready",
    generated_at: datetime = GENERATED_AT,
) -> PaperCostAwareEventStrategyReport:
    return PaperCostAwareEventStrategyReport(
        generated_at=generated_at,
        config_version="cost-aware-event-v0",
        market_slug=market_slug,
        question=f"{market_slug}?",
        fair_probability_yes=Decimal("0.6200"),
        confidence=Decimal("0.8000"),
        yes_bid=Decimal("0.4900"),
        no_bid=Decimal("0.4800"),
        spread=Decimal("0.0200"),
        resolution_risk=Decimal("0.0500"),
        selected_side="yes" if status == "paper_review_ready" else "none",
        status=status,
        yes_result=_side_result("yes"),
        no_result=_side_result("no", net_edge_per_share=Decimal("0.020000")),
        gate_results=_gate_results(
            failing_gate_name="data_integrity"
            if status == "blocked_by_inputs"
            else None,
        ),
    )


def test_strategy_cycle_recommendation_artifacts_include_cost_aware_unavailable_fallback():
    cycle_report = FakeLegacyCycleReport()

    artifacts = build_strategy_cycle_recommendation_artifacts(cycle_report)

    assert tuple(artifact.artifact_name for artifact in artifacts) == (
        "strategy_cycle_blocked_counts",
        "strategy_cycle_cost_aware_reports",
        "strategy_cycle_screening_report",
    )
    assert all(artifact.config_version == CONFIG_VERSION for artifact in artifacts)
    assert all(artifact.generated_at == GENERATED_AT for artifact in artifacts)
    assert all(artifact.flags == SAFETY_FLAGS for artifact in artifacts)
    assert all(artifact.paper_only is True for artifact in artifacts)
    assert all(artifact.report_only is True for artifact in artifacts)
    assert all(artifact.readonly is True for artifact in artifacts)

    artifact_by_name = _artifact_by_name(artifacts)
    cost_aware_artifact = artifact_by_name["strategy_cycle_cost_aware_reports"]
    assert cost_aware_artifact.status == "watch"
    assert cost_aware_artifact.item_count == 0
    assert cost_aware_artifact.reason_codes == ("cost_aware_reports_unavailable",)

    index_report = build_paper_recommendation_artifact_index_report(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        artifacts=artifacts,
    )

    assert index_report.row_count == 3
    assert index_report.watch_count == 2
    assert index_report.blocked_count == 0


def test_strategy_cycle_recommendation_artifacts_accept_current_cycle_report_shape():
    cycle_report = _cycle_report()

    artifact = _artifact_by_name(
        build_strategy_cycle_recommendation_artifacts(cycle_report),
    )["strategy_cycle_cost_aware_reports"]

    assert artifact.status == "watch"
    assert artifact.item_count == 0
    assert artifact.reason_codes == ("no_cost_aware_reports",)


def test_strategy_cycle_recommendation_artifacts_summarize_present_cost_aware_reports():
    cycle_report = _enriched_cycle_report(
        scan_market_count=3,
        considered_count=2,
        snapshot_ready_count=2,
        cost_aware_report_count=2,
        screening_report=FakeScreeningReport(),
        cost_aware_reports=(
            _cost_aware_report("alpha-market"),
            _cost_aware_report("beta-market"),
        ),
    )

    artifacts = build_strategy_cycle_recommendation_artifacts(cycle_report)

    artifact_by_name = _artifact_by_name(artifacts)
    cost_aware_artifact = artifact_by_name["strategy_cycle_cost_aware_reports"]
    assert cost_aware_artifact.status == "pass"
    assert cost_aware_artifact.item_count == 2
    assert cost_aware_artifact.reason_codes == (
        "cost_aware_paper_review_ready",
    )
    assert artifact_by_name["strategy_cycle_blocked_counts"].status == "pass"

    index_report = build_paper_recommendation_artifact_index_report(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        artifacts=artifacts,
    )
    assert index_report.pass_count == 3
    assert index_report.watch_count == 0
    assert index_report.blocked_count == 0


def test_strategy_cycle_recommendation_artifacts_watch_for_mixed_cost_aware_reports():
    cycle_report = _enriched_cycle_report(
        scan_market_count=2,
        considered_count=2,
        snapshot_ready_count=2,
        cost_aware_report_count=2,
        cost_aware_reports=(
            _cost_aware_report("alpha-market", status="paper_review_ready"),
            _cost_aware_report("beta-market", status="blocked_by_cost"),
        ),
    )

    artifact = _artifact_by_name(
        build_strategy_cycle_recommendation_artifacts(cycle_report),
    )["strategy_cycle_cost_aware_reports"]

    assert artifact.status == "watch"
    assert artifact.item_count == 2
    assert artifact.reason_codes == (
        "cost_aware_blocked_by_cost",
        "cost_aware_paper_review_ready",
    )


def test_strategy_cycle_recommendation_artifacts_block_for_risk_or_input_blocked_reports():
    cycle_report = _enriched_cycle_report(
        scan_market_count=1,
        considered_count=1,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        cost_aware_reports=(
            _cost_aware_report("alpha-market", status="blocked_by_inputs"),
        ),
    )

    artifact = _artifact_by_name(
        build_strategy_cycle_recommendation_artifacts(cycle_report),
    )["strategy_cycle_cost_aware_reports"]

    assert artifact.status == "blocked"
    assert artifact.reason_codes == ("cost_aware_blocked_by_inputs",)


def test_strategy_cycle_recommendation_artifacts_block_when_cost_report_count_mismatches():
    cycle_report = FakeLegacyCycleReport(
        scan_market_count=2,
        considered_count=2,
        snapshot_ready_count=2,
        cost_aware_report_count=2,
    )
    object.__setattr__(
        cycle_report,
        "cost_aware_reports",
        (_cost_aware_report("alpha-market"),),
    )

    artifact = _artifact_by_name(
        build_strategy_cycle_recommendation_artifacts(cycle_report),
    )["strategy_cycle_cost_aware_reports"]

    assert artifact.status == "blocked"
    assert artifact.item_count == 1
    assert artifact.reason_codes == ("cost_aware_report_count_mismatch",)


def test_strategy_cycle_recommendation_artifacts_reject_non_paper_cycle_report():
    cycle_report = FakeLegacyCycleReport()
    object.__setattr__(cycle_report, "paper_only", False)

    with pytest.raises(ValueError, match="paper_only"):
        build_strategy_cycle_recommendation_artifacts(cycle_report)


def test_strategy_cycle_recommendation_artifacts_reject_non_paper_cost_reports():
    cycle_report = FakeLegacyCycleReport(
        scan_market_count=1,
        considered_count=1,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
    )
    report = _cost_aware_report("alpha-market")
    object.__setattr__(report, "report_only", False)
    object.__setattr__(cycle_report, "cost_aware_reports", (report,))

    with pytest.raises(ValueError, match="report_only"):
        build_strategy_cycle_recommendation_artifacts(cycle_report)


def test_strategy_cycle_recommendation_artifact_dataclass_is_frozen_and_validates_flags():
    artifacts = build_strategy_cycle_recommendation_artifacts(FakeLegacyCycleReport())
    artifact = artifacts[0]

    with pytest.raises(FrozenInstanceError):
        artifact.status = "watch"
    with pytest.raises(ValueError, match="flags"):
        replace(artifact, flags=("paper_only", "report_only"))


def test_strategy_cycle_recommendation_artifacts_reject_generated_at_mismatch():
    with pytest.raises(ValueError, match="generated_at"):
        build_strategy_cycle_recommendation_artifacts(
            FakeLegacyCycleReport(),
            generated_at=GENERATED_AT + timedelta(minutes=1),
        )


def test_strategy_cycle_recommendation_artifact_source_has_no_db_api_auth_order_imports():
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_cycle_recommendation_artifact_source",
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
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert called_names.isdisjoint(forbidden_call_names)
