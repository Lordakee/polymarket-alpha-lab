from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import (
    _redacted_paper_research_packet_db_history_error,
    _run_paper_autonomous_readiness_digest,
    main,
)
from polymarket_alpha_lab.paper_autonomous_readiness_digest import (
    PaperAutonomousReadinessDigestConfig,
)


COMMAND = "paper-autonomous-readiness-digest"
READINESS_GATE_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_GATE_DB_ENABLED"
)
READINESS_GATE_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_GATE_DB_DSN"
)
READINESS_GATE_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_GATE_DB_TABLE"
)
DIGEST_CONFIG_VERSION = "paper-autonomous-readiness-digest-v0"


def _set_readiness_gate_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_autonomous_readiness_gate_reports",
) -> None:
    monkeypatch.setenv(READINESS_GATE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(READINESS_GATE_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(READINESS_GATE_DB_TABLE_ENV_VAR, table_name)


def _clear_readiness_gate_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(READINESS_GATE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(READINESS_GATE_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(READINESS_GATE_DB_TABLE_ENV_VAR, raising=False)


def _evidence(source_name: str, status: str, *, required: bool) -> SimpleNamespace:
    return SimpleNamespace(
        source_name=source_name,
        status=status,
        recommended_next_step=f"review_{source_name}_{status}",
        generated_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
        config_version=f"{source_name}-config-v0",
        reason_codes=(f"{source_name}_{status}",),
        required=required,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _digest_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 28, 12, 15, tzinfo=UTC),
        config_version=DIGEST_CONFIG_VERSION,
        digest_status="watch",
        recommended_next_review_action=(
            "review_watch_paper_autonomous_readiness_evidence"
        ),
        evidence=(
            _evidence("readiness_gate", "pass", required=True),
            _evidence("screening", "watch", required=False),
            _evidence("transition", "pass", required=False),
            _evidence("allocation", "pass", required=False),
            _evidence("ledger", "pass", required=False),
        ),
        source_config_versions=(
            ("readiness_gate", "readiness_gate-config-v0"),
            ("screening", "screening-config-v0"),
            ("transition", "transition-config-v0"),
            ("allocation", "allocation-config-v0"),
            ("ledger", "ledger-config-v0"),
        ),
        reason_code_counts=(
            _reason_count("screening_watch", 2),
            _reason_count("readiness_gate_pass", 1),
        ),
        reason_codes=("readiness_gate_pass", "screening_watch"),
        payload_json='{"secret":"payload-json-secret"}',
        condition_id="secret-condition-id",
        question="secret question",
        market_slug="secret-market-slug",
        report_sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        wallet="0xsecretwallet",
        order_id="secret-order-id",
        private_key="secret-private-key",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_parser_help_includes_paper_autonomous_readiness_digest(
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
        "--live",
        "--wallet",
        "--order",
        "--execute",
        "--auth",
        "--private-key",
        "--account",
    ),
)
def test_digest_cli_rejects_persist_db_file_live_wallet_order_and_auth_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_digest_disabled_readiness_gate_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_readiness_gate_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("digest runner should not run without readiness gate DB")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_autonomous_readiness_digest_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires paper autonomous readiness gate DB" in captured.err


def test_digest_cli_rejects_limit_above_500_before_env_runner_or_client_factory(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("env config should not be loaded for invalid limit")

    def forbidden_runner(**kwargs: Any) -> object:
        del kwargs
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("digest runner should not run for invalid limit")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed for invalid limit")

    monkeypatch.setattr(
        "polymarket_alpha_lab.cli.from_paper_autonomous_readiness_gate_db_env",
        forbidden_env,
    )

    exit_code = main(
        [COMMAND, "--limit", "501"],
        paper_autonomous_readiness_digest_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "limit" in captured.err
    assert "500" in captured.err


def test_digest_helper_rejects_limit_above_500_before_runner_or_connect() -> None:
    runner_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        del kwargs
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("digest runner should not run for invalid limit")

    with pytest.raises(ValueError) as exc_info:
        _run_paper_autonomous_readiness_digest(
            dsn="postgresql://readiness_gate:secret@localhost:54322/db",
            table_name="paper_autonomous_readiness_gate_reports",
            limit=501,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert str(exc_info.value) == f"{COMMAND} limit must be less than or equal to 500"


def test_digest_cli_uses_readiness_gate_env_config_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://readiness_gate:secret@localhost:54322/db"
    table_name = "paper_autonomous_readiness_gate_reports"
    _set_readiness_gate_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _digest_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 7
        config = kwargs["config"]
        assert type(config) is PaperAutonomousReadinessDigestConfig
        assert config.config_version == DIGEST_CONFIG_VERSION
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "7"],
        paper_autonomous_readiness_digest_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "digest_status=watch" in captured.out
    assert (
        "recommended_next_review_action="
        "review_watch_paper_autonomous_readiness_evidence"
    ) in captured.out
    assert "evidence_statuses:" in captured.out
    assert "readiness_gate=pass" in captured.out
    assert "screening=watch" in captured.out
    assert "transition=pass" in captured.out
    assert "allocation=pass" in captured.out
    assert "ledger=pass" in captured.out
    assert "reason_code_counts:" in captured.out
    assert "screening_watch:2" in captured.out
    assert "readiness_gate_pass:1" in captured.out
    assert "persisted=" not in captured.out
    for leaked_fragment in (
        dsn,
        table_name,
        "secret-condition-id",
        "secret question",
        "secret-market-slug",
        "payload-json-secret",
        "abcdef0123456789",
        "0xsecretwallet",
        "secret-order-id",
        "secret-private-key",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_digest_cli_runner_failure_redacts_db_payload_market_reason_and_auth_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://readiness_user:super-secret-password@"
        "localhost:54322/db?sslmode=disable"
    )
    table_name = "paper_autonomous_readiness_gate_secret_archive"
    condition_id = "secret-condition-id"
    question = "will-secret-question-resolve"
    market_slug = "secret-market-slug"
    report_hash = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    wallet = "0xsecretwallet"
    order_id = "secret-order-id"
    auth_token = "secret-auth-token"
    private_key = "secret-private-key"
    _set_readiness_gate_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "payload_json={'secret':'payload-json-secret'} "
            f"condition_id={condition_id} question={question} "
            f"market_slug={market_slug} hash={report_hash} "
            "reason_codes=market_slug_secret,credential_secret "
            f"wallet={wallet} order_id={order_id} auth_token={auth_token} "
            f"private_key={private_key}",
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_readiness_digest_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    for redacted in (
        "dsn=<redacted-dsn>",
        "table=<redacted-table>",
        "payload_json=<redacted-payload>",
        "condition_id=<redacted-market-detail>",
        "question=<redacted-question>",
        "market_slug=<redacted-market-slug>",
        "hash=<redacted-sha256>",
        "reason_codes=<redacted-reason-codes>",
        "wallet=<redacted-wallet>",
        "order_id=<redacted-order>",
        "auth_token=<redacted-secret>",
        "private_key=<redacted-secret>",
    ):
        assert redacted in captured.err
    for leaked_fragment in (
        dsn,
        "super-secret-password",
        table_name,
        "paper_autonomous_readiness_gate_reports",
        "payload-json-secret",
        condition_id,
        question,
        market_slug,
        "abcdef0123456789",
        "market_slug_secret",
        "credential_secret",
        wallet,
        order_id,
        auth_token,
        private_key,
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_digest_cli_runner_failure_redacts_bare_auth_and_python_repr_dict_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://readiness_user:super-secret@localhost:54322/db"
    table_name = "paper_autonomous_readiness_gate_repr_archive"
    payload_json = "repr-payload-json-secret"
    condition_id = "repr-secret-condition-id"
    question = "repr secret question"
    market_slug = "repr-secret-market-slug"
    reason_code = "repr_market_slug_reason"
    wallet = "0xreprsecretwallet"
    order_id = "repr-secret-order-id"
    auth = "secret-auth"
    private_key = "repr-secret-private-key"
    _set_readiness_gate_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        del kwargs
        row_repr = {
            "payload_json": payload_json,
            "condition_id": condition_id,
            "question": question,
            "market_slug": market_slug,
            "reason_codes": [reason_code],
            "wallet": wallet,
            "order_id": order_id,
            "private_key": private_key,
        }
        raise RuntimeError(f"read failed row={row_repr} auth={auth}")

    exit_code = main(
        [COMMAND],
        paper_autonomous_readiness_digest_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    for redacted in (
        "<redacted-payload>",
        "<redacted-market-detail>",
        "<redacted-question>",
        "<redacted-market-slug>",
        "<redacted-reason-codes>",
        "<redacted-wallet>",
        "<redacted-order>",
        "<redacted-secret>",
        "auth=<redacted-secret>",
    ):
        assert redacted in captured.err
    for leaked_fragment in (
        dsn,
        "super-secret",
        table_name,
        payload_json,
        condition_id,
        question,
        market_slug,
        reason_code,
        wallet,
        order_id,
        auth,
        private_key,
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_digest_redaction_does_not_treat_single_quoted_text_as_repr_key() -> None:
    exc = RuntimeError(
        "read failed question=Will 'foo': bar matter? next_field=visible "
        "private_key=secret-private-key",
    )

    redacted = _redacted_paper_research_packet_db_history_error(
        exc,
        dsn="postgresql://readiness_gate:secret@localhost:54322/db",
        table_name="paper_autonomous_readiness_gate_reports",
    )

    message = str(redacted)
    assert "question=<redacted-question>" in message
    assert "Will 'foo': bar matter?" not in message
    assert "next_field=visible" in message
    assert "private_key=<redacted-secret>" in message
    assert "secret-private-key" not in message


def test_digest_cli_stdout_reason_code_counts_redacts_sensitive_fragments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_readiness_gate_db_env(
        monkeypatch,
        "postgresql://readiness_gate:secret@localhost:54322/db",
    )
    report = _digest_report()
    report.reason_code_counts = (
        _reason_count("auth_token_required", 6),
        _reason_count("market_slug_mismatch", 5),
        _reason_count("wallet_not_verified", 4),
        _reason_count("order_payload_private_key_seen", 3),
        _reason_count("payload_json_missing", 2),
        _reason_count("screening_watch", 1),
    )
    report.reason_codes = tuple(
        row.reason_code for row in report.reason_code_counts
    )

    def fake_runner(**kwargs: Any) -> object:
        del kwargs
        return report

    exit_code = main(
        [COMMAND],
        paper_autonomous_readiness_digest_runner=fake_runner,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    reason_counts_line = next(
        line
        for line in captured.out.splitlines()
        if line.startswith("reason_code_counts:")
    )
    assert "screening_watch:1" in reason_counts_line
    for expected_count in ("6", "5", "4", "3", "2"):
        assert f"<redacted-reason-code>:{expected_count}" in reason_counts_line
    for leaked_fragment in (
        "auth",
        "market_slug",
        "wallet",
        "order",
        "private_key",
        "payload",
    ):
        assert leaked_fragment not in reason_counts_line
