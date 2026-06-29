from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_CONFIG_VERSION,
    ProbabilitySelectionScorerAgreementConfig,
)
from polymarket_alpha_lab.supabase_autonomous_market_scorer_config import (
    AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
    AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR,
    AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR,
    DEFAULT_AUTONOMOUS_MARKET_SCORER_DB_TABLE,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_probability_selection_summary_config import (
    DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE,
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_probability_selection_scorer_agreement_config import (
    DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE,
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR,
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR,
)


COMMAND = "probability-selection-scorer-agreement"


def _agreement_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
        config_version=DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_CONFIG_VERSION,
        selection_generated_at=datetime(2026, 6, 28, 11, 45, tzinfo=UTC),
        scorer_generated_at=datetime(2026, 6, 28, 11, 50, tzinfo=UTC),
        selected_count=3,
        scorer_candidate_count=4,
        selected_market_overlap_count=2,
        selected_condition_overlap_count=2,
        rejected_but_scored_count=1,
        scored_but_unselected_count=2,
        scorer_gate_status="pass",
        agreement_status="low_overlap",
        recommended_next_step="review_selection_scorer_disagreement",
        reason_codes=(
            "low_selection_scorer_overlap",
            "rejected_but_scored",
            "scored_but_unselected",
            "reason_code_divergence",
        ),
        reason_code_divergence_counts=(
            ("cost_ok", 1),
            ("model_passed", 2),
        ),
        rows=(SimpleNamespace(market_slug="secret-selection-market"),),
        score_rows=(SimpleNamespace(market_slug="secret-scorer-market"),),
        source_reports=(SimpleNamespace(question="secret source question"),),
        payload_json='{"secret":"payload-json-secret"}',
        report_sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_selection_summary_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE,
) -> None:
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE_ENV_VAR,
        table_name,
    )


def _clear_selection_summary_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE_ENV_VAR,
        raising=False,
    )


def _set_scorer_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_DB_TABLE,
) -> None:
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, table_name)


def _clear_scorer_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, raising=False)


def _set_agreement_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE,
) -> None:
    monkeypatch.setenv(
        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR,
        "true",
    )
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
    monkeypatch.delenv(
        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR,
        raising=False,
    )


def test_parser_help_includes_probability_selection_scorer_agreement(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_agreement_command_help_declares_readonly_report_only_boundary(
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
        "--selection-dsn",
        "--selection-table",
        "--scorer-dsn",
        "--scorer-table",
        "--input",
        "--output",
        "--live",
        "--wallet",
        "--order",
        "--execute",
        "--auth",
        "--private-key",
        "--account",
    ),
)
def test_agreement_cli_rejects_db_file_live_wallet_order_and_auth_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_agreement_disabled_selection_summary_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_selection_summary_db_env(monkeypatch)
    _set_scorer_db_env(
        monkeypatch,
        "postgresql://scorer:secret@localhost:54322/postgres",
    )
    runner_calls = 0
    client_factory_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement runner should not run without selection DB")

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
        probability_selection_scorer_agreement_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires paper probability selection summary DB to be enabled"
        in captured.err
    )


def test_agreement_enabled_selection_summary_db_without_dsn_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.delenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR, raising=False)
    _set_scorer_db_env(
        monkeypatch,
        "postgresql://scorer:secret@localhost:54322/postgres",
    )
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        del kwargs
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement runner should not run without selection DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect without selection DSN")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR in captured.err
    assert "must be set when DB is enabled" in captured.err


def test_agreement_disabled_scorer_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_selection_summary_db_env(
        monkeypatch,
        "postgresql://selection:secret@localhost:54322/postgres",
    )
    _clear_scorer_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement runner should not run without scorer DB")

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
        probability_selection_scorer_agreement_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires autonomous market scorer DB to be enabled" in captured.err


def test_agreement_enabled_scorer_db_without_dsn_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_selection_summary_db_env(
        monkeypatch,
        "postgresql://selection:secret@localhost:54322/postgres",
    )
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, raising=False)
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        del kwargs
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement runner should not run without scorer DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect without scorer DSN")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR in captured.err
    assert "must be set when DB is enabled" in captured.err


@pytest.mark.parametrize("raw_limit", ("0", "-1"))
def test_agreement_cli_rejects_non_positive_limit_before_env_runner_or_connect(
    raw_limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selection_env_calls = 0
    scorer_env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_selection_env() -> object:
        nonlocal selection_env_calls
        selection_env_calls += 1
        raise AssertionError("selection DB env should not be read")

    def forbidden_scorer_env() -> object:
        nonlocal scorer_env_calls
        scorer_env_calls += 1
        raise AssertionError("scorer DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_paper_probability_selection_summary_db_env",
        forbidden_selection_env,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "from_autonomous_market_scorer_db_env",
        forbidden_scorer_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", raw_limit],
        probability_selection_scorer_agreement_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert selection_env_calls == 0
    assert scorer_env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert f"{COMMAND} limit must be positive" in capsys.readouterr().err


def test_agreement_cli_uses_source_env_configs_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selection_dsn = "postgres://selection:secret@localhost:54322/postgres"
    scorer_dsn = "postgres://scorer:secret@127.0.0.1:54322/postgres"
    selection_table = "paper_probability_selection_summary_reports"
    scorer_table = "autonomous_market_scorer_reports"
    _set_selection_summary_db_env(
        monkeypatch,
        selection_dsn,
        table_name=selection_table,
    )
    _set_scorer_db_env(monkeypatch, scorer_dsn, table_name=scorer_table)
    _clear_agreement_db_env(monkeypatch)
    calls: list[dict[str, object]] = []
    sink_calls: list[dict[str, object]] = []
    report = _agreement_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["selection_summary_dsn"] == selection_dsn
        assert kwargs["selection_summary_table_name"] == selection_table
        assert kwargs["scorer_dsn"] == scorer_dsn
        assert kwargs["scorer_table_name"] == scorer_table
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is ProbabilitySelectionScorerAgreementConfig
        assert (
            config.config_version
            == DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_CONFIG_VERSION
        )
        assert config.min_selected_overlap_share == Decimal("1.000000")
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        probability_selection_scorer_agreement_runner=fake_runner,
        probability_selection_scorer_agreement_db_sink=lambda **kwargs: sink_calls.append(
            dict(kwargs),
        ),
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert sink_calls == []
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    for stable_field in (
        "selected_count=3",
        "scorer_candidate_count=4",
        "selected_market_overlap_count=2",
        "selected_condition_overlap_count=2",
        "rejected_but_scored_count=1",
        "scored_but_unselected_count=2",
        "scorer_gate_status=pass",
        "agreement_status=low_overlap",
        "recommended_next_step=review_selection_scorer_disagreement",
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    ):
        assert stable_field in captured.out
    assert "low_selection_scorer_overlap" in captured.out
    assert "reason_code_divergence_counts" in captured.out
    assert "cost_ok:1" in captured.out
    assert "model_passed:2" in captured.out
    for leaked_fragment in (
        selection_dsn,
        scorer_dsn,
        selection_table,
        scorer_table,
        "secret-selection-market",
        "secret-scorer-market",
        "secret source question",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_agreement_cli_persists_aggregate_report_when_local_agreement_db_enabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selection_dsn = "postgresql://selection:secret@localhost:54322/postgres"
    scorer_dsn = "postgresql://scorer:secret@localhost:54322/postgres"
    agreement_dsn = "postgresql://agreement:secret@127.0.0.1:54322/postgres"
    agreement_table = "probability_selection_scorer_agreement_reports"
    _set_selection_summary_db_env(monkeypatch, selection_dsn)
    _set_scorer_db_env(monkeypatch, scorer_dsn)
    _set_agreement_db_env(
        monkeypatch,
        agreement_dsn,
        table_name=agreement_table,
    )
    report = _agreement_report()
    sink_calls: list[dict[str, object]] = []

    def fake_sink(**kwargs: Any) -> object:
        sink_calls.append(dict(kwargs))
        assert kwargs["dsn"] == agreement_dsn
        assert kwargs["table_name"] == agreement_table
        assert kwargs["report"] is report
        return SimpleNamespace(inserted=True)

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=lambda **kwargs: report,
        probability_selection_scorer_agreement_db_sink=fake_sink,
    )

    assert exit_code == 0
    assert len(sink_calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    for leaked_fragment in (agreement_dsn, agreement_table, "agreement:secret"):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_agreement_cli_redacts_agreement_sink_dsn_table_payload_and_hash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selection_dsn = "postgresql://selection:secret@localhost:54322/postgres"
    scorer_dsn = "postgresql://scorer:secret@localhost:54322/postgres"
    agreement_dsn = (
        "postgresql://agreement_user:agreement-secret-password@"
        "localhost:54322/postgres"
    )
    agreement_table = "probability_selection_scorer_agreement_reports_secret"
    _set_selection_summary_db_env(monkeypatch, selection_dsn)
    _set_scorer_db_env(monkeypatch, scorer_dsn)
    _set_agreement_db_env(
        monkeypatch,
        agreement_dsn,
        table_name=agreement_table,
    )

    def broken_sink(**kwargs: Any) -> object:
        del kwargs
        raise RuntimeError(
            f"agreement_dsn={agreement_dsn} "
            f"agreement_table={agreement_table} "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "question=secret-question market_slug=secret-market "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=lambda **kwargs: _agreement_report(),
        probability_selection_scorer_agreement_db_sink=broken_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "agreement_dsn=<redacted-dsn>" in captured.err
    assert "agreement_table=<redacted-table>" in captured.err
    for leaked_fragment in (
        agreement_dsn,
        agreement_table,
        "agreement-secret-password",
        "reports_secret",
        "payload-json-secret",
        "secret-question",
        "secret-market",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_agreement_cli_redacts_source_dsns_tables_payload_hash_and_source_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selection_dsn = (
        "postgresql://selection_user:selection-secret-password@"
        "localhost:54322/postgres?sslmode=disable"
    )
    scorer_dsn = (
        "postgresql://scorer_user:scorer-secret-password@"
        "127.0.0.1:54322/postgres?sslmode=disable"
    )
    selection_table = "paper_probability_selection_summary_reports_secret"
    scorer_table = "autonomous_market_scorer_reports_secret"
    _set_selection_summary_db_env(
        monkeypatch,
        selection_dsn,
        table_name=selection_table,
    )
    _set_scorer_db_env(monkeypatch, scorer_dsn, table_name=scorer_table)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"selection_dsn={selection_dsn} scorer_dsn={scorer_dsn} "
            f"selection_table={selection_table} scorer_table={scorer_table} "
            "question=secret-question market_slug=secret-market "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "selection_dsn=<redacted-dsn>" in captured.err
    assert "scorer_dsn=<redacted-dsn>" in captured.err
    assert "selection_table=<redacted-table>" in captured.err
    assert "scorer_table=<redacted-table>" in captured.err
    for leaked_fragment in (
        selection_dsn,
        scorer_dsn,
        "selection-secret-password",
        "scorer-secret-password",
        selection_table,
        scorer_table,
        "reports_secret",
        "secret-question",
        "secret-market",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_agreement_cli_stdout_reason_code_counts_redacts_sensitive_fragments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_selection_summary_db_env(
        monkeypatch,
        "postgresql://selection:secret@localhost:54322/postgres",
    )
    _set_scorer_db_env(
        monkeypatch,
        "postgresql://scorer:secret@127.0.0.1:54322/postgres",
    )
    report = _agreement_report()
    report.reason_codes = (
        "low_selection_scorer_overlap",
        "market_slug_secret_event",
        "credential_token_leak",
    )
    report.reason_code_divergence_counts = (
        ("condition_id_secret", 4),
        ("cost_ok", 1),
    )

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=lambda **kwargs: report,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "<redacted-reason-code>" in captured.out
    assert "cost_ok:1" in captured.out
    for leaked_fragment in (
        "market_slug_secret_event",
        "credential_token_leak",
        "condition_id_secret",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_agreement_cli_read_errors_redact_reason_code_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_selection_summary_db_env(
        monkeypatch,
        "postgresql://selection:secret@localhost:54322/postgres",
    )
    _set_scorer_db_env(
        monkeypatch,
        "postgresql://scorer:secret@127.0.0.1:54322/postgres",
    )

    def broken_runner(**kwargs: Any) -> object:
        del kwargs
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
        probability_selection_scorer_agreement_runner=broken_runner,
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


@pytest.mark.parametrize("remote_side", ("selection", "scorer"))
def test_agreement_cli_rejects_remote_db_dsn_before_connecting_or_running(
    remote_side: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    remote_dsn = (
        "postgresql://selection_user:selection-secret-password@"
        "remote-selection.example.invalid/postgres?sslmode=require"
    )
    local_selection_dsn = "postgresql://selection:secret@localhost:54322/postgres"
    local_scorer_dsn = "postgresql://scorer:secret@localhost:54322/postgres"
    selection_dsn = remote_dsn if remote_side == "selection" else local_selection_dsn
    scorer_dsn = remote_dsn if remote_side == "scorer" else local_scorer_dsn
    _set_selection_summary_db_env(monkeypatch, selection_dsn)
    _set_scorer_db_env(monkeypatch, scorer_dsn)
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        del kwargs
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement runner should not run with remote DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect with remote DSN")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        probability_selection_scorer_agreement_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "must point to local Postgres/Supabase" in captured.err
    for leaked_fragment in (
        remote_dsn,
        "selection-secret-password",
        "remote-selection.example.invalid",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


@pytest.mark.parametrize(
    "dsn",
    (
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        "postgresql://postgres:postgres@[::1]:54322/postgres",
        "postgresql:///postgres?host=/tmp",
        "host=/tmp dbname=postgres",
        "host=localhost dbname=postgres",
    ),
)
def test_agreement_local_postgres_dsn_validator_accepts_local_forms(dsn: str) -> None:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
    )


@pytest.mark.parametrize(
    "dsn",
    (
        "postgresql://remote.example.invalid/db",
        "postgresql://localhost/db?host=remote.example.invalid",
        "postgresql:///db?host=remote.example.invalid",
        "host=remote.example.invalid dbname=postgres",
        "hostaddr=8.8.8.8 dbname=postgres",
        "service=prod dbname=postgres",
        "host=localhost,remote.example.invalid dbname=postgres",
    ),
)
def test_agreement_local_postgres_dsn_validator_rejects_remote_forms(dsn: str) -> None:
    with pytest.raises(ValueError, match="must point to local Postgres/Supabase"):
        validate_local_postgres_dsn(
            dsn,
            env_var_name=PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
        )


def test_agreement_helper_default_load_path_is_readonly_and_honors_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_dsn = "postgresql://selection:secret@localhost:54322/postgres"
    scorer_dsn = "postgresql://scorer:secret@127.0.0.1:54322/postgres"
    selection_table = "paper_probability_selection_summary_reports"
    scorer_table = "autonomous_market_scorer_reports"
    selection_connection = SimpleNamespace(name="selection", closed=0)
    scorer_connection = SimpleNamespace(name="scorer", closed=0)
    connect_calls: list[dict[str, object]] = []
    load_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []
    selection_report = SimpleNamespace(
        generated_at=datetime(2026, 6, 28, 11, 45, tzinfo=UTC),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    scorer_report = SimpleNamespace(
        generated_at=datetime(2026, 6, 28, 11, 50, tzinfo=UTC),
        gate_status="pass",
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    report = _agreement_report()

    def attach_lifecycle(connection: SimpleNamespace) -> SimpleNamespace:
        def forbidden_commit() -> None:
            raise AssertionError("agreement helper must not commit")

        def forbidden_rollback() -> None:
            raise AssertionError("agreement helper must not rollback")

        def close() -> None:
            connection.closed += 1

        connection.commit = forbidden_commit
        connection.rollback = forbidden_rollback
        connection.close = close
        return connection

    attach_lifecycle(selection_connection)
    attach_lifecycle(scorer_connection)

    def fake_connect(dsn: str, *, autocommit: bool = False) -> object:
        connect_calls.append({"dsn": dsn, "autocommit": autocommit})
        if dsn == selection_dsn:
            return selection_connection
        if dsn == scorer_dsn:
            return scorer_connection
        raise AssertionError(f"unexpected DSN {dsn}")

    def fake_load_agreement(
        selection_connection_arg: object,
        scorer_connection_arg: object,
        **kwargs: object,
    ) -> object:
        load_calls.append(
            {
                "selection_connection": selection_connection_arg,
                "scorer_connection": scorer_connection_arg,
                **kwargs,
            },
        )
        assert kwargs["selection_limit"] == 9
        assert kwargs["scorer_limit"] == 9
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_load."
        "load_probability_selection_scorer_agreement_report",
        fake_load_agreement,
    )

    helper = getattr(cli, "_run_probability_selection_scorer_agreement")
    result = helper(
        selection_summary_dsn=selection_dsn,
        selection_summary_table_name=selection_table,
        scorer_dsn=scorer_dsn,
        scorer_table_name=scorer_table,
        limit=9,
        runner=None,
    )

    assert result is report
    assert connect_calls == [
        {"dsn": selection_dsn, "autocommit": True},
        {"dsn": scorer_dsn, "autocommit": True},
    ]
    assert len(load_calls) == 1
    assert load_calls[0]["selection_connection"] is selection_connection
    assert load_calls[0]["scorer_connection"] is scorer_connection
    assert load_calls[0]["selection_table_name"] == selection_table
    assert load_calls[0]["scorer_table_name"] == scorer_table
    assert type(load_calls[0]["config"]) is ProbabilitySelectionScorerAgreementConfig
    assert isinstance(load_calls[0]["generated_at"], datetime)
    assert selection_connection.closed == 1
    assert scorer_connection.closed == 1


def test_agreement_helper_closes_selection_connection_when_scorer_connect_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_dsn = "postgresql://selection:secret@localhost:54322/postgres"
    scorer_dsn = "postgresql://scorer:secret@127.0.0.1:54322/postgres"
    selection_connection = SimpleNamespace(closed=0)

    def close_selection() -> None:
        selection_connection.closed += 1

    selection_connection.close = close_selection
    selection_connection.commit = lambda: (_ for _ in ()).throw(
        AssertionError("agreement helper must not commit"),
    )
    selection_connection.rollback = lambda: (_ for _ in ()).throw(
        AssertionError("agreement helper must not rollback"),
    )

    def fake_connect(dsn: str, *, autocommit: bool = False) -> object:
        assert autocommit is True
        if dsn == selection_dsn:
            return selection_connection
        if dsn == scorer_dsn:
            raise RuntimeError("scorer connect failed")
        raise AssertionError(f"unexpected DSN {dsn}")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    helper = getattr(cli, "_run_probability_selection_scorer_agreement")
    with pytest.raises(RuntimeError, match="autonomous market scorer"):
        helper(
            selection_summary_dsn=selection_dsn,
            selection_summary_table_name="paper_probability_selection_summary_reports",
            scorer_dsn=scorer_dsn,
            scorer_table_name="autonomous_market_scorer_reports",
            limit=1,
            runner=None,
        )

    assert selection_connection.closed == 1


def test_agreement_helper_closes_both_connections_when_loader_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_dsn = "postgresql://selection:secret@localhost:54322/postgres"
    scorer_dsn = "postgresql://scorer:secret@127.0.0.1:54322/postgres"
    selection_connection = SimpleNamespace(closed=0)
    scorer_connection = SimpleNamespace(closed=0)

    def attach_lifecycle(connection: SimpleNamespace) -> None:
        connection.close = lambda: setattr(connection, "closed", connection.closed + 1)
        connection.commit = lambda: (_ for _ in ()).throw(
            AssertionError("agreement helper must not commit"),
        )
        connection.rollback = lambda: (_ for _ in ()).throw(
            AssertionError("agreement helper must not rollback"),
        )

    attach_lifecycle(selection_connection)
    attach_lifecycle(scorer_connection)

    def fake_connect(dsn: str, *, autocommit: bool = False) -> object:
        assert autocommit is True
        if dsn == selection_dsn:
            return selection_connection
        if dsn == scorer_dsn:
            return scorer_connection
        raise AssertionError(f"unexpected DSN {dsn}")

    def broken_loader(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise RuntimeError("loader failed")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_load."
        "load_probability_selection_scorer_agreement_report",
        broken_loader,
    )

    helper = getattr(cli, "_run_probability_selection_scorer_agreement")
    with pytest.raises(RuntimeError, match="loader failed"):
        helper(
            selection_summary_dsn=selection_dsn,
            selection_summary_table_name="paper_probability_selection_summary_reports",
            scorer_dsn=scorer_dsn,
            scorer_table_name="autonomous_market_scorer_reports",
            limit=1,
            runner=None,
        )

    assert selection_connection.closed == 1
    assert scorer_connection.closed == 1
