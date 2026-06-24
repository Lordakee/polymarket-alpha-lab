from __future__ import annotations

from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab import (
    paper_autonomous_allocation_proposal_db_history_load as module_under_test,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_load import (
    load_paper_autonomous_allocation_proposal_db_history_report,
)


GENERATED_AT = datetime(2026, 6, 24, 9, 0, tzinfo=UTC)


class PaperAutonomousAllocationProposalDbHistoryConfig:
    pass


def test_loader_passes_filters_and_builds_chronological_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    config = PaperAutonomousAllocationProposalDbHistoryConfig()
    loaded_reports = ("newest", "oldest")
    history_report = object()
    store_calls: list[
        tuple[
            object,
            str | None,
            str | None,
            str | None,
            str | None,
            int | None,
            str,
        ]
    ] = []
    builder_calls: list[
        tuple[
            tuple[object, ...],
            PaperAutonomousAllocationProposalDbHistoryConfig,
            datetime,
        ]
    ] = []

    monkeypatch.setattr(
        module_under_test,
        "PaperAutonomousAllocationProposalDbHistoryConfig",
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )

    def fake_load(
        received_connection: object,
        *,
        config_version: str | None = None,
        proposal_status: str | None = None,
        screening_gate_status: str | None = None,
        allocation_config_version: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[str, str]:
        store_calls.append(
            (
                received_connection,
                config_version,
                proposal_status,
                screening_gate_status,
                allocation_config_version,
                limit,
                table_name,
            ),
        )
        return loaded_reports

    def fake_build(
        reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryConfig,
        generated_at: datetime,
    ) -> object:
        chronological_reports = tuple(reports)  # type: ignore[arg-type]
        assert (
            type(config)
            is module_under_test.PaperAutonomousAllocationProposalDbHistoryConfig
        )
        builder_calls.append((chronological_reports, config, generated_at))
        return history_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_load,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_report",
        fake_build,
    )

    result = load_paper_autonomous_allocation_proposal_db_history_report(
        connection,
        config_version="proposal-v0",
        proposal_status="pass",
        screening_gate_status="watch",
        allocation_config_version="allocation-v0",
        limit=7,
        table_name="custom_allocation_proposal_reports",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert result is history_report
    assert store_calls == [
        (
            connection,
            "proposal-v0",
            "pass",
            "watch",
            "allocation-v0",
            7,
            "custom_allocation_proposal_reports",
        ),
    ]
    assert builder_calls == [
        ((loaded_reports[1], loaded_reports[0]), config, GENERATED_AT),
    ]


def test_loader_rejects_non_exact_history_config_before_store_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module_under_test,
        "PaperAutonomousAllocationProposalDbHistoryConfig",
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )

    def fail_load(*args: object, **kwargs: object) -> tuple[object, ...]:
        raise AssertionError("loader must validate config before reading store")

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fail_load,
    )

    with pytest.raises(
        ValueError,
        match="config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
    ):
        load_paper_autonomous_allocation_proposal_db_history_report(
            object(),
            config_version=None,
            proposal_status=None,
            screening_gate_status=None,
            allocation_config_version=None,
            limit=None,
            table_name="paper_autonomous_allocation_proposal_reports",
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
