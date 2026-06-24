from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
    PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    PaperAutonomousAllocationProposalDbHistoryMetricsReport,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load import (
    load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report,
)


NOW = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)


def _fake_metrics_report() -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    from tests.test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
        _metrics_report,
    )

    return _metrics_report()


class FakeMetricsLoader:
    def __init__(self) -> None:
        self.calls: list[tuple[object, dict[str, object]]] = []

    def __call__(
        self,
        connection: object,
        *,
        limit: int | None,
        table_name: str,
        config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
        if type(config) is not PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
            raise ValueError(
                "config must be a PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
            )
        self.calls.append(
            (
                connection,
                {
                    "limit": limit,
                    "table_name": table_name,
                    "config": config,
                    "generated_at": generated_at,
                },
            )
        )
        return _fake_metrics_report()


def test_loader_composes_metrics_loader_and_evaluation_reducer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_loader = FakeMetricsLoader()
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.load_paper_autonomous_allocation_proposal_db_history_metrics_report",
        fake_loader,
    )
    connection = object()
    evaluation_config = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig()

    report = load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        connection,
        limit=5,
        table_name="reports",
        config=evaluation_config,
        generated_at=NOW,
    )

    assert len(fake_loader.calls) == 1
    used_connection, kwargs = fake_loader.calls[0]
    assert used_connection is connection
    assert kwargs["limit"] == 5
    assert kwargs["table_name"] == "reports"
    assert kwargs["generated_at"] == NOW
    assert type(kwargs["config"]) is PaperAutonomousAllocationProposalDbHistoryMetricsConfig

    assert report.config_version == evaluation_config.config_version
    assert report.source_report_count == 3
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_metrics_evaluation_passed",
    )


def test_loader_rejects_non_exact_evaluation_config(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_loader = FakeMetricsLoader()
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.load_paper_autonomous_allocation_proposal_db_history_metrics_report",
        fake_loader,
    )
    with pytest.raises(ValueError, match="config"):
        load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
            object(),
            limit=5,
            table_name="reports",
            config="bad",
            generated_at=NOW,
        )
    assert fake_loader.calls == []
