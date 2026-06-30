from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any, Callable

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_probability_selection_summary_history_trend import (
    DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_CONFIG_VERSION,
    PaperProbabilitySelectionSummaryHistoryTrendConfig,
)
from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-probability-selection-summary-history-trend-gate"
GATE_MODULE_NAME = (
    "polymarket_alpha_lab.paper_probability_selection_summary_history_trend_gate"
)
TREND_CONFIG_VERSION = (
    DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_CONFIG_VERSION
)
GATE_CONFIG_VERSION = "paper-probability-selection-summary-history-trend-gate-v0"


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendGateConfig:
    config_version: str = GATE_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    trend_report_age_seconds: int
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount,
        ...,
    ]
    source_history_count: int
    source_trend_status: str
    source_recommended_next_step: str
    latest_history_status: str
    latest_status_streak: int
    latest_selected_share: Decimal
    average_selected_share: Decimal
    selected_share_delta: Decimal
    stale_history_count: int
    thin_history_count: int
    latest_source_reason_codes: tuple[str, ...]
    recurring_source_reason_code_counts: tuple[tuple[str, int], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _gate_report() -> PaperProbabilitySelectionSummaryHistoryTrendGateReport:
    return PaperProbabilitySelectionSummaryHistoryTrendGateReport(
        generated_at=datetime(2026, 6, 29, 12, 5, tzinfo=UTC),
        config_version=GATE_CONFIG_VERSION,
        source_config_version=TREND_CONFIG_VERSION,
        source_generated_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
        trend_report_age_seconds=300,
        gate_status="watch",
        recommended_next_step=(
            "throttle_probability_selection_summary_history_trend_review"
        ),
        reason_code_counts=(
            PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
                "latest_paper_probability_selection_summary_history_trend_watch",
                1,
            ),
            PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
                "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded",
                1,
            ),
        ),
        source_history_count=4,
        source_trend_status="watch",
        source_recommended_next_step="review_probability_selection_trend",
        latest_history_status="watch",
        latest_status_streak=2,
        latest_selected_share=Decimal("0.400000"),
        average_selected_share=Decimal("0.450000"),
        selected_share_delta=Decimal("-0.050000"),
        stale_history_count=1,
        thin_history_count=1,
        latest_source_reason_codes=(
            "latest_history_watch",
            "stale_history_reports_present",
        ),
        recurring_source_reason_code_counts=(
            ("latest_selection_has_watch_rows", 2),
            ("source_next_step_skip", 2),
        ),
        reason_codes=(
            "latest_paper_probability_selection_summary_history_trend_watch",
            "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _install_fake_gate_module(
    monkeypatch: pytest.MonkeyPatch,
    *,
    builder: Callable[..., object] | None = None,
) -> ModuleType:
    module = ModuleType(GATE_MODULE_NAME)
    module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION = (
        GATE_CONFIG_VERSION
    )
    module.PaperProbabilitySelectionSummaryHistoryTrendGateConfig = (
        PaperProbabilitySelectionSummaryHistoryTrendGateConfig
    )
    module.PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount = (
        PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount
    )
    module.PaperProbabilitySelectionSummaryHistoryTrendGateReport = (
        PaperProbabilitySelectionSummaryHistoryTrendGateReport
    )
    if builder is None:

        def builder(source_report: object, *, config: object, generated_at: datetime) -> object:
            del source_report, config, generated_at
            return _gate_report()

    module.build_paper_probability_selection_summary_history_trend_gate_report = builder
    monkeypatch.setitem(sys.modules, GATE_MODULE_NAME, module)
    return module


def _set_history_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_probability_selection_summary_history_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
        table_name,
    )


def _clear_history_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
        raising=False,
    )


def test_parser_help_includes_selection_summary_history_trend_gate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_selection_summary_trend_gate_command_help_declares_readonly_report_only_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "read-only" in captured.out
    assert "report-only" in captured.out
    assert "--persist" not in captured.out
    assert "--dsn" not in captured.out
    assert "--table" not in captured.out


@pytest.mark.parametrize(
    "flag",
    (
        "--persist",
        "--dsn",
        "--db-dsn",
        "--table",
        "--db-table",
        "--input",
        "--output",
        "--live",
        "--wallet",
        "--order",
        "--execute",
        "--auth",
        "--private-key",
        "--account",
        "--fast",
    ),
)
def test_selection_summary_trend_gate_cli_rejects_db_file_live_wallet_order_auth_and_fast_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_selection_summary_trend_gate_disabled_history_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_history_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend gate runner should not run without DB config")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_gate_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires paper probability selection summary history DB"
        in captured.err
    )


def test_selection_summary_trend_gate_enabled_history_db_without_dsn_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend gate runner should not run without a DB DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR} "
        "must be set when DB is enabled"
    ) in captured.err


@pytest.mark.parametrize("raw_limit", ("0", "-1"))
def test_selection_summary_trend_gate_cli_rejects_non_positive_limit_before_env_runner_or_connect(
    raw_limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("history DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend gate runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_paper_probability_selection_summary_history_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", raw_limit],
        paper_probability_selection_summary_history_trend_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert f"{COMMAND} limit must be positive" in capsys.readouterr().err


def test_selection_summary_trend_gate_cli_uses_history_env_config_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)
    _install_fake_gate_module(monkeypatch)
    calls: list[dict[str, object]] = []
    report = _gate_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        trend_config = kwargs["trend_config"]
        assert type(trend_config) is PaperProbabilitySelectionSummaryHistoryTrendConfig
        assert trend_config.config_version == TREND_CONFIG_VERSION
        gate_config = kwargs["gate_config"]
        assert type(gate_config) is PaperProbabilitySelectionSummaryHistoryTrendGateConfig
        assert gate_config.config_version == GATE_CONFIG_VERSION
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_probability_selection_summary_history_trend_gate_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    for stable_field in (
        "gate_status=watch",
        "recommended_next_step=throttle_probability_selection_summary_history_trend_review",
        "source_history_count=4",
        "source_trend_status=watch",
        "source_recommended_next_step=review_probability_selection_trend",
        "source_generated_at=2026-06-29T12:00:00+00:00",
        "trend_report_age_seconds=300",
        "latest_history_status=watch",
        "latest_status_streak=2",
        "latest_selected_share=0.400000",
        "average_selected_share=0.450000",
        "selected_share_delta=-0.050000",
        "stale_history_count=1",
        "thin_history_count=1",
    ):
        assert stable_field in captured.out
    assert (
        "latest_paper_probability_selection_summary_history_trend_watch,"
        "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded"
    ) in captured.out
    assert (
        "reason_code_counts: "
        "latest_paper_probability_selection_summary_history_trend_watch:1,"
        "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded:1"
    ) in captured.out
    assert "latest_source_reason_codes: latest_history_watch,stale_history_reports_present" in (
        captured.out
    )
    assert (
        "recurring_source_reason_code_counts: "
        "latest_selection_has_watch_rows:2,source_next_step_skip:2"
    ) in captured.out
    for leaked_fragment in (
        dsn,
        table_name,
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_selection_summary_trend_gate_cli_rejects_injected_runner_result_that_is_not_gate_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_history_db_env(
        monkeypatch,
        "postgresql://selection-history:secret@localhost:54322/db",
    )
    _install_fake_gate_module(monkeypatch)
    unsafe_report = SimpleNamespace(
        **{
            **_gate_report().__dict__,
            "latest_selected_share": (
                'payload_json={"secret":"payload-json-secret"}'
            ),
            "paper_only": False,
            "report_only": False,
            "readonly": False,
        },
    )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_gate_runner=(
            lambda **kwargs: unsafe_report
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "PaperProbabilitySelectionSummaryHistoryTrendGateReport" in captured.err
    assert "payload-json-secret" not in captured.out
    assert "payload-json-secret" not in captured.err


def test_selection_summary_trend_gate_cli_read_errors_redact_dsn_table_payload_hash_market_question_and_reason(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://history_user:super-secret-password@"
        "localhost:54322/db?sslmode=require"
    )
    table_name = "paper_probability_selection_summary_history_reports_secret"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)
    _install_fake_gate_module(monkeypatch)

    def broken_runner(**kwargs: Any) -> object:
        del kwargs
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "question=secret-question market_slug=secret-market "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "reason_code=secret-reason "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_gate_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "reason_code=<redacted-reason-codes>" in captured.err
    for leaked_fragment in (
        dsn,
        "super-secret-password",
        table_name,
        "reports_secret",
        "secret-question",
        "secret-market",
        "payload-json-secret",
        "secret-reason",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_selection_summary_trend_gate_summary_sanitizes_reason_code_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = replace(
        _gate_report(),
        reason_codes=(
            "latest_paper_probability_selection_summary_history_trend_watch",
            "market_slug_secret_event",
            "credential_token_leak",
        ),
        reason_code_counts=(
            PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
                "condition_id_secret",
                4,
            ),
            PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
                "latest_paper_probability_selection_summary_history_trend_watch",
                1,
            ),
        ),
        latest_source_reason_codes=(
            "market_slug_secret_event",
            "credential_token_leak",
        ),
        recurring_source_reason_code_counts=(
            ("condition_id_secret", 4),
            ("source_next_step_skip", 2),
        ),
    )

    getattr(cli, "_print_paper_probability_selection_summary_history_trend_gate_summary")(
        report,
    )

    captured = capsys.readouterr()
    assert "<redacted-reason-code>" in captured.out
    assert (
        "latest_paper_probability_selection_summary_history_trend_watch:1"
        in captured.out
    )
    assert "source_next_step_skip:2" in captured.out
    for leaked_fragment in (
        "market_slug_secret_event",
        "credential_token_leak",
        "condition_id_secret",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_selection_summary_trend_gate_helper_default_load_path_reads_history_chronologically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    trend_report = SimpleNamespace(generated_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC))
    gate_report = _gate_report()
    newest = SimpleNamespace(generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC))
    oldest = SimpleNamespace(generated_at=datetime(2026, 6, 29, 10, 0, tzinfo=UTC))
    load_calls: list[dict[str, object]] = []
    trend_build_calls: list[dict[str, object]] = []
    gate_build_calls: list[dict[str, object]] = []
    connect_calls: list[tuple[str, bool]] = []

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0

        def commit(self) -> None:
            raise AssertionError("read-only helper should not commit")

        def rollback(self) -> None:
            raise AssertionError("read-only helper should not rollback")

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((connect_dsn, autocommit))
        return connection

    def fake_load(
        load_connection: object,
        *,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        load_calls.append(
            {
                "connection": load_connection,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (newest, oldest)

    def fake_trend_builder(
        reports: tuple[object, ...],
        *,
        config: PaperProbabilitySelectionSummaryHistoryTrendConfig,
        generated_at: datetime,
    ) -> object:
        trend_build_calls.append(
            {
                "reports": reports,
                "config": config,
                "generated_at": generated_at,
            },
        )
        assert reports == (oldest, newest)
        assert type(config) is PaperProbabilitySelectionSummaryHistoryTrendConfig
        assert config.config_version == TREND_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return trend_report

    def fake_gate_builder(
        source_report: object,
        *,
        config: PaperProbabilitySelectionSummaryHistoryTrendGateConfig,
        generated_at: datetime,
    ) -> object:
        gate_build_calls.append(
            {
                "source_report": source_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        assert source_report is trend_report
        assert type(config) is PaperProbabilitySelectionSummaryHistoryTrendGateConfig
        assert config.config_version == GATE_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return gate_report

    _install_fake_gate_module(monkeypatch, builder=fake_gate_builder)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_store."
        "load_paper_probability_selection_summary_history_reports",
        fake_load,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_trend."
        "build_paper_probability_selection_summary_history_trend_report",
        fake_trend_builder,
    )

    helper = getattr(cli, "_run_paper_probability_selection_summary_history_trend_gate")
    result = helper(
        dsn=dsn,
        table_name=table_name,
        limit=7,
        runner=None,
    )

    assert result is gate_report
    assert connect_calls == [(dsn, True)]
    assert load_calls == [
        {"connection": connection, "limit": 7, "table_name": table_name},
    ]
    assert len(trend_build_calls) == 1
    assert len(gate_build_calls) == 1
    assert gate_build_calls[0]["generated_at"] is trend_build_calls[0]["generated_at"]
    assert connection.close_count == 1


def test_selection_summary_trend_gate_cli_default_load_errors_close_and_redact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://history_user:super-secret-password@"
        "localhost:54322/db?sslmode=require"
    )
    table_name = "paper_probability_selection_summary_history_reports_secret"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)
    _install_fake_gate_module(monkeypatch)

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        assert connect_dsn == dsn
        assert autocommit is True
        return connection

    def broken_load(
        load_connection: object,
        *,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        assert load_connection is connection
        assert limit == 25
        raise RuntimeError(
            f"load failed dsn={dsn} table={table_name} "
            "question=secret-question market_slug=secret-market "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_store."
        "load_paper_probability_selection_summary_history_reports",
        broken_load,
    )

    exit_code = main([COMMAND])

    assert exit_code == 1
    assert connection.close_count == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    for leaked_fragment in (
        dsn,
        "super-secret-password",
        table_name,
        "reports_secret",
        "secret-question",
        "secret-market",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_selection_summary_trend_gate_cli_rejects_remote_db_dsn_before_connecting_or_running(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    remote_dsn = (
        "postgresql://history_user:super-secret-password@"
        "remote-history.example.invalid/postgres"
    )
    _set_history_db_env(monkeypatch, remote_dsn)
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend gate runner should not run with remote DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect with remote DSN")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "must point to local Postgres/Supabase" in captured.err
    for leaked_fragment in (
        remote_dsn,
        "super-secret-password",
        "remote-history.example.invalid",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out
