from __future__ import annotations

from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab import (
    paper_execution_reconciliation_db_history_load as module_under_test,
)
from polymarket_alpha_lab.paper_execution_reconciliation_db_history_load import (
    load_paper_execution_reconciliation_db_history_report,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


class PaperExecutionReconciliationDbHistoryConfig:
    pass


def test_loader_uses_injected_report_loader_and_builds_chronological_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    config = PaperExecutionReconciliationDbHistoryConfig()
    loaded_reports = ("newest", "oldest")
    history_report = object()
    loader_calls: list[
        tuple[object, str | None, str | None, int | None, str]
    ] = []
    builder_calls: list[
        tuple[
            tuple[object, ...],
            PaperExecutionReconciliationDbHistoryConfig,
            datetime,
        ]
    ] = []

    monkeypatch.setattr(
        module_under_test,
        "PaperExecutionReconciliationDbHistoryConfig",
        PaperExecutionReconciliationDbHistoryConfig,
    )

    def fake_load(
        received_connection: object,
        *,
        config_version: str | None = None,
        reconciliation_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[str, str]:
        loader_calls.append(
            (
                received_connection,
                config_version,
                reconciliation_status,
                limit,
                table_name,
            ),
        )
        return loaded_reports

    def fake_build(
        reports: object,
        *,
        config: PaperExecutionReconciliationDbHistoryConfig,
        generated_at: datetime,
    ) -> object:
        chronological_reports = tuple(reports)  # type: ignore[arg-type]
        assert type(config) is module_under_test.PaperExecutionReconciliationDbHistoryConfig
        builder_calls.append((chronological_reports, config, generated_at))
        return history_report

    monkeypatch.setattr(
        module_under_test,
        "build_paper_execution_reconciliation_db_history_report",
        fake_build,
    )

    result = load_paper_execution_reconciliation_db_history_report(
        connection,
        config_version="paper-execution-reconciliation-v0",
        reconciliation_status="has_pending",
        limit=5,
        table_name="paper_execution_reconciliation_archive",
        config=config,
        generated_at=GENERATED_AT,
        report_loader=fake_load,
    )

    assert result is history_report
    assert loader_calls == [
        (
            connection,
            "paper-execution-reconciliation-v0",
            "has_pending",
            5,
            "paper_execution_reconciliation_archive",
        ),
    ]
    assert builder_calls == [
        ((loaded_reports[1], loaded_reports[0]), config, GENERATED_AT),
    ]


def test_loader_rejects_non_exact_history_config_before_reading() -> None:
    def fail_load(*args: object, **kwargs: object) -> tuple[object, ...]:
        raise AssertionError("loader must validate config before reading")

    with pytest.raises(
        ValueError,
        match="config must be a PaperExecutionReconciliationDbHistoryConfig",
    ):
        load_paper_execution_reconciliation_db_history_report(
            object(),
            config_version=None,
            reconciliation_status=None,
            limit=None,
            table_name="paper_execution_reconciliation_reports",
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
            report_loader=fail_load,
        )


def test_loader_does_not_own_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Connection:
        def __init__(self) -> None:
            self.closed = False
            self.committed = False
            self.rolled_back = False

        def close(self) -> None:
            self.closed = True

        def commit(self) -> None:
            self.committed = True

        def rollback(self) -> None:
            self.rolled_back = True

    class Config:
        pass

    connection = Connection()
    config = Config()

    monkeypatch.setattr(
        module_under_test,
        "PaperExecutionReconciliationDbHistoryConfig",
        Config,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_execution_reconciliation_db_history_report",
        lambda reports, *, config, generated_at: tuple(reports),
    )

    result = load_paper_execution_reconciliation_db_history_report(
        connection,
        config_version=None,
        reconciliation_status=None,
        limit=None,
        table_name="paper_execution_reconciliation_reports",
        config=config,
        generated_at=GENERATED_AT,
        report_loader=lambda received_connection, **_: ("newest", "oldest"),
    )

    assert result == ("oldest", "newest")
    assert connection.closed is False
    assert connection.committed is False
    assert connection.rolled_back is False
