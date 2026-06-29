from __future__ import annotations

import sys
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.probability_selection_scorer_agreement_trend import (
    DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_CONFIG_VERSION,
    ProbabilitySelectionScorerAgreementTrendConfig,
    ProbabilitySelectionScorerAgreementTrendReport,
)
from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
    DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION,
    ProbabilitySelectionScorerAgreementTrendGateConfig,
    ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount,
    ProbabilitySelectionScorerAgreementTrendGateReport,
)
from polymarket_alpha_lab.supabase_probability_selection_scorer_agreement_config import (
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR,
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR,
)


COMMAND = "probability-selection-scorer-agreement-trend-gate"
TREND_CONFIG_VERSION = DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_CONFIG_VERSION
GATE_CONFIG_VERSION = (
    DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION
)


def _trend_report() -> ProbabilitySelectionScorerAgreementTrendReport:
    return ProbabilitySelectionScorerAgreementTrendReport(
        generated_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
        config_version=TREND_CONFIG_VERSION,
        source_report_count=4,
        first_generated_at=datetime(2026, 6, 29, 8, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 6, 29, 11, 30, tzinfo=UTC),
        history_span_seconds=12_600,
        latest_agreement_status="low_overlap",
        latest_status_streak=2,
        aligned_report_count=1,
        low_overlap_report_count=2,
        gate_blocked_report_count=1,
        missing_inputs_report_count=0,
        insufficient_identifiers_report_count=0,
        average_selected_count=Decimal("3.250000"),
        average_scorer_candidate_count=Decimal("4.500000"),
        recurring_reason_code_counts=(
            ("low_selection_scorer_overlap", 2),
            ("scored_but_unselected", 3),
        ),
        trend_status="watch",
        recommended_next_step="review_selection_scorer_disagreement",
        reason_codes=(
            "latest_agreement_low_overlap",
            "recurring_agreement_reason_codes",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _gate_report() -> ProbabilitySelectionScorerAgreementTrendGateReport:
    return ProbabilitySelectionScorerAgreementTrendGateReport(
        generated_at=datetime(2026, 6, 29, 12, 5, tzinfo=UTC),
        config_version=GATE_CONFIG_VERSION,
        source_config_version=TREND_CONFIG_VERSION,
        source_generated_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
        trend_report_age_seconds=300,
        gate_status="watch",
        recommended_next_step=(
            "throttle_probability_selection_scorer_agreement_trend_review"
        ),
        reason_code_counts=(
            ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
                "latest_probability_selection_scorer_agreement_trend_watch",
                1,
            ),
            ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
                "repeated_probability_selection_scorer_agreement_trend_watch_threshold_exceeded",
                1,
            ),
        ),
        source_report_count=4,
        source_trend_status="watch",
        source_recommended_next_step="review_selection_scorer_disagreement",
        latest_agreement_status="low_overlap",
        latest_agreement_status_streak=2,
        aligned_report_count=1,
        low_overlap_report_count=2,
        gate_blocked_report_count=1,
        missing_inputs_report_count=0,
        insufficient_identifiers_report_count=0,
        average_selected_count=Decimal("3.250000"),
        average_scorer_candidate_count=Decimal("4.500000"),
        latest_source_reason_codes=(
            "latest_agreement_low_overlap",
            "recurring_agreement_reason_codes",
        ),
        recurring_source_reason_code_counts=(
            ("low_selection_scorer_overlap", 2),
            ("scored_but_unselected", 3),
        ),
        reason_codes=(
            "latest_probability_selection_scorer_agreement_trend_watch",
            "repeated_probability_selection_scorer_agreement_trend_watch_threshold_exceeded",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_agreement_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "probability_selection_scorer_agreement_reports",
) -> None:
    monkeypatch.setenv(PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR,
        table_name,
    )


def _clear_agreement_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(
        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(
        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR,
        raising=False,
    )


def test_parser_help_includes_probability_selection_scorer_agreement_trend_gate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_agreement_trend_gate_command_help_declares_readonly_report_only_boundary(
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
def test_agreement_trend_gate_cli_rejects_db_file_live_wallet_order_auth_and_fast_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_agreement_trend_gate_disabled_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_agreement_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run without DB")

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
        probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires probability selection scorer agreement DB" in captured.err


def test_agreement_trend_gate_enabled_db_without_dsn_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.delenv(PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR, raising=False)
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run without DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect without DSN")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR in captured.err
    assert "must be set when DB is enabled" in captured.err


@pytest.mark.parametrize("raw_limit", ("0", "-1"))
def test_agreement_trend_gate_cli_rejects_non_positive_limit_before_env_runner_or_connect(
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
        raise AssertionError("agreement DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_probability_selection_scorer_agreement_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", raw_limit],
        probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert f"{COMMAND} limit must be positive" in capsys.readouterr().err


def test_agreement_trend_gate_cli_uses_agreement_env_config_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://agreement:secret@localhost:54322/postgres"
    table_name = "probability_selection_scorer_agreement_reports"
    _set_agreement_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _gate_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        trend_config = kwargs["trend_config"]
        assert type(trend_config) is ProbabilitySelectionScorerAgreementTrendConfig
        assert trend_config.config_version == TREND_CONFIG_VERSION
        gate_config = kwargs["gate_config"]
        assert type(gate_config) is ProbabilitySelectionScorerAgreementTrendGateConfig
        assert gate_config.config_version == GATE_CONFIG_VERSION
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        probability_selection_scorer_agreement_trend_gate_runner=fake_runner,
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
        "recommended_next_step=throttle_probability_selection_scorer_agreement_trend_review",
        "source_report_count=4",
        "source_trend_status=watch",
        "source_generated_at=2026-06-29T12:00:00+00:00",
        "trend_report_age_seconds=300",
        "latest_agreement_status=low_overlap",
        "latest_agreement_status_streak=2",
        "aligned_report_count=1",
        "low_overlap_report_count=2",
        "gate_blocked_report_count=1",
        "missing_inputs_report_count=0",
        "insufficient_identifiers_report_count=0",
        "average_selected_count=3.250000",
        "average_scorer_candidate_count=4.500000",
    ):
        assert stable_field in captured.out
    assert (
        "latest_probability_selection_scorer_agreement_trend_watch,"
        "repeated_probability_selection_scorer_agreement_trend_watch_threshold_exceeded"
    ) in captured.out
    assert (
        "reason_code_counts: "
        "latest_probability_selection_scorer_agreement_trend_watch:1,"
        "repeated_probability_selection_scorer_agreement_trend_watch_threshold_exceeded:1"
    ) in captured.out
    assert (
        "recurring_source_reason_code_counts: "
        "low_selection_scorer_overlap:2,scored_but_unselected:3"
    ) in captured.out
    for leaked_fragment in (
        dsn,
        table_name,
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_agreement_trend_gate_cli_rejects_injected_runner_result_that_is_not_gate_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_agreement_db_env(
        monkeypatch,
        "postgresql://agreement:secret@localhost:54322/postgres",
    )
    unsafe_report = SimpleNamespace(
        **{
            **_gate_report().__dict__,
            "average_selected_count": "payload_json={\"secret\":\"payload-json-secret\"}",
            "paper_only": False,
            "report_only": False,
            "readonly": False,
        },
    )

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_trend_gate_runner=(
            lambda **kwargs: unsafe_report
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "ProbabilitySelectionScorerAgreementTrendGateReport" in captured.err
    assert "payload-json-secret" not in captured.out
    assert "payload-json-secret" not in captured.err


def test_agreement_trend_gate_cli_read_errors_redact_dsn_table_payload_and_hash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://agreement_user:super-secret-password@"
        "localhost:54322/postgres"
    )
    table_name = "probability_selection_scorer_agreement_reports_secret"
    _set_agreement_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        del kwargs
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "question=secret-question market_slug=secret-market "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_trend_gate_runner=broken_runner,
    )

    assert exit_code == 1
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


def test_agreement_trend_gate_cli_sanitizes_exact_report_source_reason_codes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://agreement:secret@localhost:54322/postgres"
    table_name = "probability_selection_scorer_agreement_reports"
    _set_agreement_db_env(monkeypatch, dsn, table_name=table_name)
    report = replace(
        _gate_report(),
        latest_source_reason_codes=(
            "market_slug_secret_event",
            "credential_token_leak",
        ),
        recurring_source_reason_code_counts=(
            ("condition_id_secret", 4),
            ("scored_but_unselected", 3),
        ),
    )

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_trend_gate_runner=(
            lambda **kwargs: report
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "<redacted-reason-code>" in captured.out
    assert "latest_source_reason_codes:" in captured.out
    assert "recurring_source_reason_code_counts:" in captured.out
    assert "scored_but_unselected:3" in captured.out
    for leaked_fragment in (
        "market_slug_secret_event",
        "credential_token_leak",
        "condition_id_secret",
        dsn,
        table_name,
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_agreement_trend_gate_summary_sanitizes_reason_code_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = SimpleNamespace(
        **{
            **_gate_report().__dict__,
            "reason_codes": (
                "latest_probability_selection_scorer_agreement_trend_watch",
                "market_slug_secret_event",
                "credential_token_leak",
            ),
            "reason_code_counts": (
                SimpleNamespace(
                    reason_code="condition_id_secret",
                    report_count=4,
                ),
                SimpleNamespace(
                    reason_code=(
                        "latest_probability_selection_scorer_agreement_trend_watch"
                    ),
                    report_count=1,
                ),
            ),
            "recurring_source_reason_code_counts": (
                ("condition_id_secret", 4),
                ("scored_but_unselected", 3),
            ),
        },
    )

    getattr(cli, "_print_probability_selection_scorer_agreement_trend_gate_summary")(
        report,
    )

    captured = capsys.readouterr()
    assert "<redacted-reason-code>" in captured.out
    assert "latest_probability_selection_scorer_agreement_trend_watch:1" in captured.out
    assert "scored_but_unselected:3" in captured.out
    for leaked_fragment in (
        "market_slug_secret_event",
        "credential_token_leak",
        "condition_id_secret",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_agreement_trend_gate_helper_default_load_path_reads_reports_chronologically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://agreement:secret@localhost:54322/postgres"
    table_name = "probability_selection_scorer_agreement_reports"
    trend_report = _trend_report()
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
        config: ProbabilitySelectionScorerAgreementTrendConfig,
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
        assert type(config) is ProbabilitySelectionScorerAgreementTrendConfig
        assert config.config_version == TREND_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return trend_report

    def fake_gate_builder(
        source_report: object,
        *,
        config: ProbabilitySelectionScorerAgreementTrendGateConfig,
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
        assert type(config) is ProbabilitySelectionScorerAgreementTrendGateConfig
        assert config.config_version == GATE_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return gate_report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_store."
        "load_probability_selection_scorer_agreement_reports",
        fake_load,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_trend."
        "build_probability_selection_scorer_agreement_trend_report",
        fake_trend_builder,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate."
        "build_probability_selection_scorer_agreement_trend_gate_report",
        fake_gate_builder,
    )

    helper = getattr(cli, "_run_probability_selection_scorer_agreement_trend_gate")
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
    assert connection.close_count == 1


def test_agreement_trend_gate_cli_default_load_errors_close_and_redact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://agreement_user:super-secret-password@"
        "localhost:54322/postgres"
    )
    table_name = "probability_selection_scorer_agreement_reports_secret"
    _set_agreement_db_env(monkeypatch, dsn, table_name=table_name)

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
        "polymarket_alpha_lab.probability_selection_scorer_agreement_store."
        "load_probability_selection_scorer_agreement_reports",
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


def test_agreement_trend_gate_cli_rejects_remote_db_dsn_before_connecting_or_running(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    remote_dsn = (
        "postgresql://agreement_user:super-secret-password@"
        "remote-agreement.example.invalid/postgres"
    )
    _set_agreement_db_env(monkeypatch, remote_dsn)
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run with remote DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect with remote DSN")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
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
        "remote-agreement.example.invalid",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out
