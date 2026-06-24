from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

COMMAND = "paper-autonomous-allocation-proposal-db-history-metrics"
METRICS_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-metrics-v0"
METRICS_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics"
)
METRICS_LOADER_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_load"
)


def _install_metrics_api_stub_for_package_import() -> None:
    if METRICS_MODULE in sys.modules:
        return

    module = ModuleType(METRICS_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
        config_version: str = METRICS_CONFIG_VERSION
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    class PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow:
        pass

    class PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow:
        pass

    class PaperAutonomousAllocationProposalDbHistoryMetricsReport:
        pass

    class PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary:
        pass

    def build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        *_args: object,
        **_kwargs: object,
    ) -> object:
        raise AssertionError("metrics reducer should not run in CLI tests")

    module.PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow = (
        PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsConfig = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsReport = (
        PaperAutonomousAllocationProposalDbHistoryMetricsReport
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary = (
        PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary
    )
    module.build_paper_autonomous_allocation_proposal_db_history_metrics_report = (
        build_paper_autonomous_allocation_proposal_db_history_metrics_report
    )
    sys.modules[METRICS_MODULE] = module


_install_metrics_api_stub_for_package_import()

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
)


def _set_allocation_proposal_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_autonomous_allocation_proposal_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
        table_name,
    )


def _install_or_get_metrics_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(METRICS_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != METRICS_MODULE:
            raise

    module = ModuleType(METRICS_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
        config_version: str = METRICS_CONFIG_VERSION
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    module.PaperAutonomousAllocationProposalDbHistoryMetricsConfig = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig
    )
    monkeypatch.setitem(sys.modules, METRICS_MODULE, module)
    return module


def _install_metrics_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_autonomous_allocation_proposal_db_history_metrics_report: object,
) -> None:
    module = ModuleType(METRICS_LOADER_MODULE)
    module.load_paper_autonomous_allocation_proposal_db_history_metrics_report = (
        load_paper_autonomous_allocation_proposal_db_history_metrics_report
    )
    monkeypatch.setitem(sys.modules, METRICS_LOADER_MODULE, module)


def _market_share_row(kind: str, share: Decimal) -> SimpleNamespace:
    return SimpleNamespace(kind=kind, share=share)


def _metrics_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version=METRICS_CONFIG_VERSION,
        source_report_count=4,
        latest_proposal_status="watch",
        latest_budget_utilization=Decimal("0.750000"),
        latest_requested_fill_ratio=Decimal("0.500000"),
        latest_total_allocated_paper_notional=Decimal("125.000000"),
        latest_largest_concentration_rows=(
            _market_share_row("side", Decimal("0.800000")),
            _market_share_row("market", Decimal("0.625000")),
        ),
        latest_added_market_side_count=2,
        latest_removed_market_side_count=1,
        latest_notional_turnover=Decimal("33.250000"),
        latest_allocated_edge_share=Decimal("0.875000"),
        latest_expected_edge_notional=Decimal("12.500000"),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_allocation_proposal_db_history_metrics_cli_requires_enabled_db_config_before_runner_connect_or_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    client_factory_calls = 0
    connect_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history metrics runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_db_history_metrics_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires autonomous allocation proposal DB to be enabled" in (
        captured.err
    )


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_allocation_proposal_db_history_metrics_cli_rejects_non_positive_limit_before_env_runner_connect_or_client(
    limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0
    client_factory_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("allocation proposal DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history metrics runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_env",
        forbidden_env,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_allocation_proposal_db_history_metrics_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


def test_allocation_proposal_db_history_metrics_cli_requires_dsn_before_runner_or_connect(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history metrics runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_db_history_metrics_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR in captured.err
    assert "must be set when DB is enabled" in captured.err


def test_allocation_proposal_db_history_metrics_cli_uses_injected_runner_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics_api = _install_or_get_metrics_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-metrics.example.invalid/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _metrics_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert (
            type(config)
            is metrics_api.PaperAutonomousAllocationProposalDbHistoryMetricsConfig
        )
        assert config.config_version == METRICS_CONFIG_VERSION
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_autonomous_allocation_proposal_db_history_metrics_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: source_report_count=4 latest_proposal_status=watch "
            "latest_budget_utilization=0.750000 "
            "latest_requested_fill_ratio=0.500000 "
            "latest_total_allocated_paper_notional=125.000000 "
            "latest_largest_market_share=0.625000 "
            "latest_added_market_side_count=2 "
            "latest_removed_market_side_count=1 "
            "latest_notional_turnover=33.250000 "
            "latest_allocated_edge_share=0.875000 "
            "latest_expected_edge_notional=12.500000"
        ),
    ]
    assert captured.err == ""
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_metrics_helper_default_load_path_imports_psycopg_lazily_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_api = _install_or_get_metrics_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-metrics.example.invalid/db"
    table_name = "paper_autonomous_allocation_proposal_reports"
    report = _metrics_report()
    connect_calls: list[tuple[str, bool]] = []
    loader_calls: list[dict[str, object]] = []
    psycopg_import_calls = 0
    real_import = builtins.__import__

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0
            self.commit_count = 0
            self.rollback_count = 0

        def commit(self) -> None:
            self.commit_count += 1
            raise AssertionError("read-only helper must not commit")

        def rollback(self) -> None:
            self.rollback_count += 1
            raise AssertionError("read-only helper must not rollback")

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((connect_dsn, autocommit))
        return connection

    def counting_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        nonlocal psycopg_import_calls
        if name == "psycopg":
            psycopg_import_calls += 1
        return real_import(name, globals, locals, fromlist, level)

    def fake_load(
        received_connection: object,
        *,
        limit: int,
        table_name: str,
        config: object,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setattr(builtins, "__import__", counting_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_metrics_loader(monkeypatch, fake_load)

    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_metrics",
    )
    result = helper(
        dsn=dsn,
        table_name=table_name,
        limit=7,
        runner=None,
    )

    assert result is report
    assert psycopg_import_calls == 1
    assert connect_calls == [(dsn, True)]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert loader_calls[0]["limit"] == 7
    assert loader_calls[0]["table_name"] == table_name
    config = loader_calls[0]["config"]
    assert (
        type(config)
        is metrics_api.PaperAutonomousAllocationProposalDbHistoryMetricsConfig
    )
    assert config.config_version == METRICS_CONFIG_VERSION
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_allocation_proposal_db_history_metrics_helper_raises_on_missing_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_metrics_api(monkeypatch)
    _install_metrics_loader(
        monkeypatch,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("loader should not run without psycopg"),
        ),
    )
    monkeypatch.setitem(sys.modules, "psycopg", None)
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_metrics",
    )
    dsn = "postgresql://allocation-proposal-history-metrics-secret.example.invalid/db"

    with pytest.raises(RuntimeError, match="psycopg is required"):
        helper(
            dsn=dsn,
            table_name="paper_autonomous_allocation_proposal_reports",
            limit=7,
            runner=None,
        )


def test_allocation_proposal_db_history_metrics_cli_connect_failure_redacts_dsn_schema_table_tail_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_metrics_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-metrics-secret.example.invalid/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    payload_json = '{"market_slug":"secret-market-slug","question":"nested secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)
    _install_metrics_loader(
        monkeypatch,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("loader should not run after connect failure"),
        ),
    )

    def broken_connect(*_args: Any, **_kwargs: Any) -> object:
        raise RuntimeError(
            f"connect failed dsn={dsn} table={table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=broken_connect))

    exit_code = main([COMMAND])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_metrics_cli_loader_failure_redacts_dsn_schema_table_tail_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_metrics_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-metrics-secret.example.invalid/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    payload_json = '{"market_slug":"secret-market-slug","question":"nested secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)

    class FakeConnection:
        def close(self) -> None:
            pass

    def broken_load(*_args: Any, **_kwargs: Any) -> object:
        raise RuntimeError(
            f"load failed dsn={dsn} table={table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_args, **_kwargs: FakeConnection()),
    )
    _install_metrics_loader(monkeypatch, broken_load)

    exit_code = main([COMMAND])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err
