from __future__ import annotations

import builtins
import inspect
import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_team_research_assignment_config import (
    TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR,
    TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR,
    TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.team_research_assignment_history import (
    TeamResearchAssignmentHistoryConfig,
)


COMMAND = "team-research-assignment-history"
HISTORY_CONFIG_VERSION = "team-research-assignment-history-v0"
ASSIGNMENT_CONFIG_VERSION = "team-research-assignment-v0"
ASSIGNMENT_DB_DSN = "host=localhost port=54325 dbname=assignments user=postgres"
ASSIGNMENT_DB_TABLE = "team_research_assignment_reports_archive"
REPORT_HASH = "b" * 64
PAYLOAD_HASH = "sensitive-assignment-payload-hash"

ASSIGNMENT_DB_ENV_VARS = (
    TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR,
    TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR,
    TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR,
)


def test_root_help_lists_team_research_assignment_history(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_team_research_assignment_history_help_is_env_scoped_read_only_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    normalized = help_text.lower()

    assert COMMAND in help_text
    for flag in (
        "--assignment-status",
        "--config-version",
        "--limit",
    ):
        assert flag in help_text
    assert "read-only" in normalized or "readonly" in normalized
    assert "report-only" in normalized or "report only" in normalized
    assert "local" in normalized
    assert "supabase" in normalized
    assert "postgres" in normalized

    for flag in (
        "--dsn",
        "--table",
        "--persist",
        "--live",
        "--auth",
        "--wallet",
        "--private-key",
        "--api-key",
        "--account",
        "--order",
        "--trade",
        "--execute",
        "--submit",
    ):
        assert flag not in help_text


def test_team_research_assignment_history_main_exposes_runner_injection_parameter() -> None:
    parameter = inspect.signature(main).parameters.get(
        "team_research_assignment_history_runner",
    )

    assert parameter is not None
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None


@pytest.mark.parametrize(
    ("target", "expected"),
    (
        ("disabled", ("assignment", "disabled")),
        ("missing_dsn", ("assignment", "dsn")),
    ),
)
def test_team_research_assignment_history_fails_closed_when_assignment_db_unavailable(
    target: str,
    expected: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_assignment_env(monkeypatch)
    if target == "disabled":
        monkeypatch.setenv(TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR, "false")
        monkeypatch.setenv(TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR, ASSIGNMENT_DB_DSN)
        monkeypatch.setenv(
            TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR,
            ASSIGNMENT_DB_TABLE,
        )
    elif target == "missing_dsn":
        monkeypatch.setenv(TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR, "true")
        monkeypatch.setenv(
            TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR,
            ASSIGNMENT_DB_TABLE,
        )
    side_effect_calls: list[str] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND],
        team_research_assignment_history_runner=_forbidden_history_runner(
            side_effect_calls,
        ),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    for fragment in expected:
        assert fragment in combined.lower()
    for secret in (ASSIGNMENT_DB_DSN, ASSIGNMENT_DB_TABLE):
        assert secret not in combined
    assert "postgresql://" not in combined


@pytest.mark.parametrize("bad_value", ("0", "-1"))
def test_team_research_assignment_history_rejects_nonpositive_limit_before_env_reads(
    bad_value: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls: list[str] = []

    def forbidden_env() -> object:
        env_calls.append("env")
        raise AssertionError(f"{COMMAND} must reject invalid limits before env reads")

    import polymarket_alpha_lab.supabase_team_research_assignment_config as assignment_env

    monkeypatch.setattr(
        assignment_env,
        "from_team_research_assignment_db_env",
        forbidden_env,
    )

    exit_code = _invoke_main([COMMAND, "--limit", bad_value])

    assert exit_code == 2
    assert env_calls == []
    err = capsys.readouterr().err
    assert f"{COMMAND}:" in err
    assert "must be a positive integer" in err
    assert ASSIGNMENT_DB_DSN not in err


def test_team_research_assignment_history_injected_runner_receives_env_kwargs_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_assignment_db_env(monkeypatch)
    runner_calls: list[dict[str, object]] = []
    report = _history_report()

    def runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        assert kwargs["dsn"] == ASSIGNMENT_DB_DSN
        assert kwargs["table_name"] == ASSIGNMENT_DB_TABLE
        assert kwargs["assignment_status"] == "ready"
        assert kwargs["config_version"] == ASSIGNMENT_CONFIG_VERSION
        assert kwargs["limit"] == 7
        history_config = kwargs["config"]
        assert type(history_config) is TeamResearchAssignmentHistoryConfig
        assert history_config.config_version == HISTORY_CONFIG_VERSION
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        assert not {
            "auth",
            "wallet",
            "order",
            "private_key",
            "api_key",
            "account",
            "persist",
        } & set(kwargs)
        return report

    exit_code = _invoke_main(
        [
            COMMAND,
            "--assignment-status",
            "ready",
            "--config-version",
            ASSIGNMENT_CONFIG_VERSION,
            "--limit",
            "7",
        ],
        team_research_assignment_history_runner=runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    assert "history_status=observed" in out
    assert "report_count=3" in out
    assert "status_rows=ready:2,watch:1,blocked:0" in out
    assert "latest_assignment_status=ready" in out
    assert "paper_only=True" in out
    assert "report_only=True" in out
    assert "readonly=True" in out
    for secret in (ASSIGNMENT_DB_DSN, ASSIGNMENT_DB_TABLE):
        assert secret not in out


def test_team_research_assignment_history_default_loader_uses_resolved_env_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_assignment_db_env(monkeypatch)
    load_calls: list[dict[str, object]] = []

    import polymarket_alpha_lab.team_research_assignment_psycopg as assignment_psycopg

    def load_reports(**kwargs: object) -> tuple[()]:
        load_calls.append(kwargs)
        return ()

    monkeypatch.setattr(
        assignment_psycopg,
        "load_team_research_assignment_reports",
        load_reports,
    )

    exit_code = _invoke_main(
        [
            COMMAND,
            "--assignment-status",
            "ready",
            "--config-version",
            ASSIGNMENT_CONFIG_VERSION,
            "--limit",
            "3",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert load_calls == [
        {
            "dsn": ASSIGNMENT_DB_DSN,
            "table_name": ASSIGNMENT_DB_TABLE,
            "assignment_status": "ready",
            "config_version": ASSIGNMENT_CONFIG_VERSION,
            "limit": 3,
        },
    ]
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    assert f"config_version={HISTORY_CONFIG_VERSION}" in out
    for secret in (ASSIGNMENT_DB_DSN, ASSIGNMENT_DB_TABLE):
        assert secret not in out


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_research_assignment_history_rejects_injected_runner_false_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_assignment_db_env(monkeypatch)
    report = vars(_history_report()).copy()
    report[flag_name] = False

    exit_code = _invoke_main(
        [COMMAND],
        team_research_assignment_history_runner=lambda **_kwargs: SimpleNamespace(
            **report,
        ),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert flag_name in combined
    assert "must be True" in combined
    for secret in (ASSIGNMENT_DB_DSN, ASSIGNMENT_DB_TABLE):
        assert secret not in combined


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_research_assignment_history_rejects_injected_runner_missing_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_assignment_db_env(monkeypatch)
    report = vars(_history_report()).copy()
    del report[flag_name]

    exit_code = _invoke_main(
        [COMMAND],
        team_research_assignment_history_runner=lambda **_kwargs: SimpleNamespace(
            **report,
        ),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert flag_name in combined
    assert "must be True" in combined
    for secret in (ASSIGNMENT_DB_DSN, ASSIGNMENT_DB_TABLE):
        assert secret not in combined


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "host=localhost dbname=assignments"],
        [COMMAND, "--table", "team_research_assignment_reports"],
        [COMMAND, "--persist"],
        [COMMAND, "--live"],
        [COMMAND, "--auth", "token"],
        [COMMAND, "--wallet", "wallet"],
        [COMMAND, "--private-key", "secret"],
        [COMMAND, "--api-key", "secret"],
        [COMMAND, "--account", "account"],
        [COMMAND, "--order", "order"],
        [COMMAND, "--trade", "trade"],
        [COMMAND, "--execute"],
        [COMMAND, "--submit"],
    ),
)
def test_team_research_assignment_history_rejects_forbidden_flags(
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls: list[str] = []

    def forbidden_env() -> object:
        env_calls.append("env")
        raise AssertionError(f"{COMMAND} must reject forbidden flags before env reads")

    import polymarket_alpha_lab.supabase_team_research_assignment_config as assignment_env

    monkeypatch.setattr(
        assignment_env,
        "from_team_research_assignment_db_env",
        forbidden_env,
    )

    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    assert env_calls == []
    err = capsys.readouterr().err
    assert "does not accept" in err
    rejected_option = argv[1].split("=", 1)[0]
    for value in argv[2:]:
        if not value.startswith("--") and value not in rejected_option:
            assert value not in err


@pytest.mark.parametrize(
    ("argv", "secret"),
    (
        ([COMMAND, "--auth", "super-secret-token"], "super-secret-token"),
        ([COMMAND, "--private-key=super-secret-key"], "super-secret-key"),
        (
            [COMMAND, "--unknown-api-key", "super-secret-api-key"],
            "super-secret-api-key",
        ),
    ),
)
def test_team_research_assignment_history_rejects_secret_like_args_without_echoing_values(
    argv: list[str],
    secret: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    err = capsys.readouterr().err
    assert COMMAND in err
    assert "does not accept" in err
    assert secret not in err


def test_team_research_assignment_history_runner_failure_redacts_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_assignment_db_env(monkeypatch)
    failure_message = (
        f"assignment_dsn={ASSIGNMENT_DB_DSN} assignment_table={ASSIGNMENT_DB_TABLE} "
        "assignment_host=localhost market_slug=bitcoin-above-120k "
        "question='secret market question' "
        "payload_json={'marketSlug': 'nested-market', 'question': 'nested question'} "
        f"report_sha256={REPORT_HASH} payload_hash={PAYLOAD_HASH} "
        "account=acct-123 wallet=wallet-abc auth=Bearer-secret "
        "accountId=account-camel walletAddress=wallet-camel "
        "private_key=private-secret api_key=api-secret key=generic-key "
        "privateKey=private-camel apiKey=api-camel "
        "credential_id=credential-id-secret credentials=credentials-secret "
        "secretKey=secret-key-camel apiSecret=api-secret-camel "
        "order=order-secret orderId=order-camel order_hash=order-hash "
        "orderHash=order-hash-camel trade=trade-secret "
        "trade_id=trade-id-secret tradeId=trade-id-camel"
    )

    def runner(**_kwargs: object) -> object:
        raise RuntimeError(failure_message)

    exit_code = _invoke_main(
        [COMMAND, "--limit", "3"],
        team_research_assignment_history_runner=runner,
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    for secret in (
        ASSIGNMENT_DB_DSN,
        ASSIGNMENT_DB_TABLE,
        "localhost",
        "bitcoin-above-120k",
        "secret market question",
        "nested-market",
        "nested question",
        REPORT_HASH,
        PAYLOAD_HASH,
        "acct-123",
        "account-camel",
        "wallet-abc",
        "wallet-camel",
        "Bearer-secret",
        "private-secret",
        "api-secret",
        "generic-key",
        "private-camel",
        "api-camel",
        "credential-id-secret",
        "credentials-secret",
        "secret-key-camel",
        "api-secret-camel",
        "order-secret",
        "order-camel",
        "order-hash",
        "order-hash-camel",
        "trade-secret",
        "trade-id-secret",
        "trade-id-camel",
    ):
        assert secret not in combined
    for replacement in (
        "<redacted-dsn>",
        "<redacted-host>",
        "<redacted-table>",
        "<redacted-market-slug>",
        "<redacted-question>",
        "<redacted-payload>",
        "<redacted-sha256>",
        "<redacted-hash>",
        "<redacted-account>",
        "<redacted-wallet>",
        "<redacted-secret>",
        "<redacted-order>",
    ):
        assert replacement in combined


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
        config_version=HISTORY_CONFIG_VERSION,
        history_status="observed",
        report_count=3,
        required_report_count=2,
        first_report_generated_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
        latest_report_generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        status_rows=(
            SimpleNamespace(assignment_status="ready", report_count=2),
            SimpleNamespace(assignment_status="watch", report_count=1),
            SimpleNamespace(assignment_status="blocked", report_count=0),
        ),
        latest_assignment_status="ready",
        latest_assignment_count=4,
        latest_assigned_count=4,
        latest_watch_count=0,
        latest_blocked_count=0,
        assignment_count_delta=2,
        assigned_count_delta=3,
        watch_count_delta=-1,
        blocked_count_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _invoke_main(argv: list[str], **kwargs: Any) -> int:
    accepted_kwargs = set(inspect.signature(main).parameters)
    call_kwargs = {
        name: value for name, value in kwargs.items() if name in accepted_kwargs
    }
    try:
        result = main(argv, **call_kwargs)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 1
    assert type(result) is int
    return result


def _combined_output(capsys: pytest.CaptureFixture[str]) -> str:
    captured = capsys.readouterr()
    return f"{captured.out}\n{captured.err}"


def _clear_assignment_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ASSIGNMENT_DB_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _enable_assignment_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_assignment_env(monkeypatch)
    monkeypatch.setenv(TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR, ASSIGNMENT_DB_DSN)
    monkeypatch.setenv(TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR, ASSIGNMENT_DB_TABLE)


def _forbidden_history_runner(calls: list[str]):
    def runner(*args: object, **kwargs: object) -> object:
        del args, kwargs
        calls.append("history_runner")
        raise AssertionError(f"{COMMAND} must fail before loading history")

    return runner


def _install_psycopg_connect_guard(
    monkeypatch: pytest.MonkeyPatch,
    side_effect_calls: list[str],
) -> None:
    def forbidden_connect(*args: object, **kwargs: object) -> object:
        del args, kwargs
        side_effect_calls.append("psycopg.connect")
        raise AssertionError(f"{COMMAND} must not open psycopg before env gates pass")

    existing_psycopg = sys.modules.get("psycopg")
    if existing_psycopg is not None:
        monkeypatch.setattr(existing_psycopg, "connect", forbidden_connect, raising=False)

    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        imported = original_import(name, globals, locals, fromlist, level)
        if name == "psycopg" or name.startswith("psycopg."):
            psycopg_module = sys.modules.get("psycopg", imported)
            monkeypatch.setattr(
                psycopg_module,
                "connect",
                forbidden_connect,
                raising=False,
            )
        return imported

    monkeypatch.setattr(builtins, "__import__", guarded_import)
