from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cli import main


NOW = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)


def _report(**overrides: object) -> object:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
        build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report,
    )
    from tests.test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
        _metrics_report,
    )

    base = {
        "metrics_report": _metrics_report(),
        "config": PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        "generated_at": NOW,
    }
    base.update(overrides)
    return build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(**base)


def test_disabled_env_fails_before_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED", raising=False)
    assert main(["paper-autonomous-allocation-proposal-db-history-metrics-evaluation", "--limit", "5"]) == 1


def test_runner_path_receives_injected_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def runner(**kwargs: object) -> object:
        captured.update(kwargs)
        return _report()

    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN",
        "postgresql://localhost/db",
    )
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_NAME",
        "reports",
    )
    assert (
        main(
            ["paper-autonomous-allocation-proposal-db-history-metrics-evaluation", "--limit", "5"],
            paper_autonomous_allocation_proposal_db_history_metrics_evaluation_runner=runner,
        )
        == 0
    )
    assert captured["limit"] == 5
    assert captured["table_name"] == "paper_autonomous_allocation_proposal_reports"
    assert captured["dsn"] == "postgresql://localhost/db"
    assert captured["generated_at"].tzinfo == UTC
