from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.autonomous_market_scorer_history import (
    AutonomousMarketScorerHistoryConfig,
)
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_autonomous_market_scorer_config import (
    AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
    AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR,
    AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR,
)


COMMAND = "autonomous-market-scorer-history"
HISTORY_CONFIG_VERSION = "autonomous-market-scorer-history-v0"
LOCAL_SCORER_DSN = "postgresql://market-scorer:secret@localhost:54322/db"


def _recurring_market(market_slug: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(market_slug=market_slug, report_count=report_count)


def _recurring_condition(condition_id: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(condition_id=condition_id, report_count=report_count)


def _recurring_reason(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 28, 12, 5, tzinfo=UTC),
        config_version=HISTORY_CONFIG_VERSION,
        source_report_count=3,
        first_generated_at=datetime(2026, 6, 28, 10, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
        history_span_seconds=7_200,
        latest_gate_status="pass",
        latest_gate_status_streak=2,
        recurring_market_slug_counts=(
            _recurring_market("secret-alpha-market", 3),
            _recurring_market("secret-beta-market", 2),
        ),
        recurring_condition_id_counts=(
            _recurring_condition("secret-condition-alpha", 3),
        ),
        recurring_reason_code_counts=(
            _recurring_reason("shared_reason", 3),
            _recurring_reason("market_slug_secret_alpha", 2),
        ),
        latest_candidate_count=2,
        average_candidate_count=Decimal("2.000000"),
        latest_recommended_notional=Decimal("15.000000"),
        total_recommended_notional=Decimal("40.000000"),
        notional_delta=Decimal("5.000000"),
        blocked_report_count=0,
        skipped_report_count=1,
        history_status="stable",
        recommended_next_step="continue_monitoring",
        reason_codes=(
            "autonomous_market_scorer_history_stable",
            "market_question_secret_event",
            "shared_reason",
        ),
        score_rows=(
            SimpleNamespace(
                market_slug="score-row-secret-market",
                condition_id="score-row-secret-condition",
                question="score row secret question",
            ),
        ),
        source_reports=(SimpleNamespace(question="source report secret question"),),
        payload_json='{"secret":"payload-json-secret"}',
        report_sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_scorer_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "autonomous_market_scorer_reports",
) -> None:
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, table_name)


def _clear_scorer_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, raising=False)


def test_parser_help_includes_autonomous_market_scorer_history(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


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
        "--config-version",
        "--live",
        "--wallet",
        "--order",
        "--execute",
        "--auth",
        "--private-key",
        "--account",
    ),
)
def test_history_cli_rejects_persist_db_file_live_wallet_order_and_auth_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_history_disabled_scorer_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_scorer_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history runner should not run without scorer DB config")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        autonomous_market_scorer_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires autonomous market scorer DB to be enabled" in captured.err


def test_history_enabled_scorer_db_without_dsn_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, raising=False)
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history runner should not run without a scorer DB DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        autonomous_market_scorer_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR} "
        "must be set when DB is enabled"
    ) in captured.err


@pytest.mark.parametrize("raw_limit", ("0", "-1"))
def test_history_cli_rejects_non_positive_limit_before_env_runner_or_connect(
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
        raise AssertionError("scorer DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_autonomous_market_scorer_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", raw_limit],
        autonomous_market_scorer_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert f"{COMMAND} limit must be positive" in capsys.readouterr().err


def test_history_cli_uses_scorer_env_config_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = LOCAL_SCORER_DSN
    table_name = "autonomous_market_scorer_reports"
    _set_scorer_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _history_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is AutonomousMarketScorerHistoryConfig
        assert config.config_version == HISTORY_CONFIG_VERSION
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        autonomous_market_scorer_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "source_report_count=3" in captured.out
    assert "first_generated_at=2026-06-28T10:00:00+00:00" in captured.out
    assert "latest_generated_at=2026-06-28T12:00:00+00:00" in captured.out
    assert "history_span_seconds=7200" in captured.out
    assert "latest_gate_status=pass" in captured.out
    assert "latest_gate_status_streak=2" in captured.out
    assert "latest_candidate_count=2" in captured.out
    assert "average_candidate_count=2.000000" in captured.out
    assert "latest_recommended_notional=15.000000" in captured.out
    assert "total_recommended_notional=40.000000" in captured.out
    assert "notional_delta=5.000000" in captured.out
    assert "blocked_report_count=0" in captured.out
    assert "skipped_report_count=1" in captured.out
    assert "history_status=stable" in captured.out
    assert "recommended_next_step=continue_monitoring" in captured.out
    assert "identifier_recurrence:" in captured.out
    assert "recurring_market_slug_count=2" in captured.out
    assert "max_recurring_market_slug_report_count=3" in captured.out
    assert "recurring_condition_id_count=1" in captured.out
    assert "max_recurring_condition_id_report_count=3" in captured.out
    assert (
        "reason_codes: autonomous_market_scorer_history_stable,"
        "<redacted-reason-code>,shared_reason redacted_reason_code_count=1"
    ) in captured.out
    assert (
        "recurring_reason_code_counts: shared_reason:3 "
        "redacted_recurring_reason_code_count=1"
    ) in captured.out
    for leaked_fragment in (
        dsn,
        table_name,
        "secret-alpha-market",
        "secret-beta-market",
        "secret-condition-alpha",
        "market_slug_secret_alpha",
        "market_question_secret_event",
        "score-row-secret-market",
        "score-row-secret-condition",
        "score row secret question",
        "source report secret question",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_history_cli_read_errors_redact_dsn_table_payload_market_and_hash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://scorer_user:super-secret-password@"
        "localhost:54322/db?sslmode=disable"
    )
    table_name = "autonomous_market_scorer_reports_secret"
    _set_scorer_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "question=secret-question market_slug=secret-market "
            "condition_id=secret-condition "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND],
        autonomous_market_scorer_history_runner=broken_runner,
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
        "secret-condition",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_cli_read_errors_redact_reason_code_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = LOCAL_SCORER_DSN
    table_name = "autonomous_market_scorer_reports"
    _set_scorer_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            "read failed "
            "reason_codes=market_question_secret_event "
            "reason_code=credential_token_leak "
            '"reason_codes": ["wallet_address_leak"] '
            '"reasonCode": "condition_id_secret" '
            '"reasonCodes": ["score_rows_secret"]',
        )

    exit_code = main(
        [COMMAND],
        autonomous_market_scorer_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "reason_codes=<redacted-reason-codes>" in captured.err
    assert "reason_code=<redacted-reason-codes>" in captured.err
    assert '"reason_codes": "<redacted-reason-codes>"' in captured.err
    assert '"reasonCode": "<redacted-reason-codes>"' in captured.err
    assert '"reasonCodes": "<redacted-reason-codes>"' in captured.err
    for leaked_fragment in (
        "market_question_secret_event",
        "credential_token_leak",
        "wallet_address_leak",
        "condition_id_secret",
        "score_rows_secret",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_cli_read_errors_redact_quoted_structured_payload_values(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = LOCAL_SCORER_DSN
    table_name = "autonomous_market_scorer_reports"
    _set_scorer_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            "read failed "
            "payload_json='{\"secret\":\"payload-json-secret\",\"foo\":\"leaked\"}' "
            "score_rows='[{\"market_slug\":\"secret-market\",\"condition_id\":\"secret-condition\"}]' "
            "next_key=safe",
        )

    exit_code = main(
        [COMMAND],
        autonomous_market_scorer_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "payload_json=<redacted-payload>" in captured.err
    assert "score_rows=<redacted-score-rows>" in captured.err
    assert "next_key=safe" in captured.err
    for leaked_fragment in (
        "payload-json-secret",
        "leaked",
        "secret-market",
        "secret-condition",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_cli_read_errors_redact_market_detail_and_secret_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = LOCAL_SCORER_DSN
    table_name = "autonomous_market_scorer_reports"
    _set_scorer_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            "read failed "
            "market_question=will-secret-event-resolve "
            '"market_details": "classified-market-detail" '
            "details=internal-detail "
            "description=private-description "
            "title=private-title "
            "condition_id=private-condition "
            "secret=raw-secret "
            "password=raw-password "
            "token=raw-token "
            "api_key=raw-api-key "
            "private_key=raw-private-key "
            "authorization=raw-authorization "
            "credential=raw-credential",
        )

    exit_code = main(
        [COMMAND],
        autonomous_market_scorer_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "market_question=<redacted-market-detail>" in captured.err
    assert '"market_details": "<redacted-market-detail>"' in captured.err
    assert "condition_id=<redacted-market-detail>" in captured.err
    assert "secret=<redacted-secret>" in captured.err
    assert "password=<redacted-secret>" in captured.err
    assert "token=<redacted-secret>" in captured.err
    assert "api_key=<redacted-secret>" in captured.err
    assert "private_key=<redacted-secret>" in captured.err
    assert "authorization=<redacted-secret>" in captured.err
    assert "credential=<redacted-secret>" in captured.err
    for leaked_fragment in (
        "will-secret-event-resolve",
        "classified-market-detail",
        "internal-detail",
        "private-description",
        "private-title",
        "private-condition",
        "raw-secret",
        "raw-password",
        "raw-token",
        "raw-api-key",
        "raw-private-key",
        "raw-authorization",
        "raw-credential",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_helper_default_load_path_reads_scorer_reports_chronologically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = LOCAL_SCORER_DSN
    table_name = "autonomous_market_scorer_reports"
    report = _history_report()
    newest = SimpleNamespace(generated_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC))
    oldest = SimpleNamespace(generated_at=datetime(2026, 6, 28, 10, 0, tzinfo=UTC))
    load_calls: list[dict[str, object]] = []
    build_calls: list[dict[str, object]] = []
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

    def fake_builder(
        reports: tuple[object, ...],
        *,
        config: AutonomousMarketScorerHistoryConfig,
        generated_at: datetime,
    ) -> object:
        build_calls.append(
            {
                "reports": reports,
                "config": config,
                "generated_at": generated_at,
            },
        )
        assert reports == (oldest, newest)
        assert type(config) is AutonomousMarketScorerHistoryConfig
        assert config.config_version == HISTORY_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.autonomous_market_scorer_store."
        "load_autonomous_market_scorer_reports",
        fake_load,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.autonomous_market_scorer_history."
        "build_autonomous_market_scorer_history_report",
        fake_builder,
    )

    helper = getattr(cli, "_run_autonomous_market_scorer_history")
    result = helper(
        dsn=dsn,
        table_name=table_name,
        limit=7,
        runner=None,
    )

    assert result is report
    assert connect_calls == [(dsn, True)]
    assert load_calls == [
        {"connection": connection, "limit": 7, "table_name": table_name},
    ]
    assert len(build_calls) == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("limit", (0, -1, True, "1", Decimal("1")))
def test_history_helper_rejects_invalid_limit_before_runner_or_connect(
    limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    helper = getattr(cli, "_run_autonomous_market_scorer_history")
    with pytest.raises(ValueError, match="limit must be positive"):
        helper(
            dsn=LOCAL_SCORER_DSN,
            table_name="autonomous_market_scorer_reports",
            limit=limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0
