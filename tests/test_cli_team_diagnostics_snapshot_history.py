from __future__ import annotations

import builtins
import inspect
import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config import (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
    TeamDiagnosticsSnapshotHistoryReport,
)


COMMAND = "team-diagnostics-snapshot-history"
LOCAL_SNAPSHOT_DSN = (
    "postgresql://"
    "postgres:snapshot-history-secret@localhost:54322/postgres"
)
SNAPSHOT_TABLE = "team_diagnostics_snapshot_archive"
REPORT_HASH = "a" * 64


TEAM_DIAGNOSTICS_SNAPSHOT_ENV_VARS = (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)


def test_root_help_lists_team_diagnostics_snapshot_history(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_team_diagnostics_snapshot_history_help_is_env_scoped_read_only_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    normalized = help_text.lower()

    assert COMMAND in help_text
    for flag in (
        "--team-id",
        "--market-slug",
        "--forecast-id",
        "--config-version",
        "--limit",
    ):
        assert flag in help_text
    assert "read-only" in normalized or "readonly" in normalized
    assert "report-only" in normalized or "report only" in normalized
    assert "local" in normalized
    assert "supabase" in normalized
    assert "postgres" in normalized

    forbidden_flags = (
        "--persist",
        "--dsn",
        "--table",
        "--input",
        "--output",
        "--live",
        "--auth",
        "--wallet",
        "--order",
        "--private-key",
        "--account",
    )
    for flag in forbidden_flags:
        assert flag not in help_text


def test_team_diagnostics_snapshot_history_fails_closed_when_snapshot_db_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _disable_snapshot_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND, "--limit", "5"],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_diagnostics_snapshot_history_runner=_forbidden_history_runner(
            side_effect_calls,
        ),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert "snapshot" in combined.lower()
    assert "disabled" in combined.lower()
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert "postgresql://" not in combined


@pytest.mark.parametrize("bad_limit", ("0", "-1"))
def test_team_diagnostics_snapshot_history_fails_before_side_effects_on_non_positive_limit(
    bad_limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_snapshot_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND, "--limit", bad_limit],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_diagnostics_snapshot_history_runner=_forbidden_history_runner(
            side_effect_calls,
        ),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert "limit must be positive" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert "postgresql://" not in combined


def test_team_diagnostics_snapshot_history_fails_closed_when_snapshot_db_dsn_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_snapshot_env_without_dsn(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND, "--limit", "5"],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_diagnostics_snapshot_history_runner=_forbidden_history_runner(
            side_effect_calls,
        ),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert "snapshot" in combined.lower()
    assert "dsn" in combined.lower()
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined
    assert "postgresql://" not in combined


def test_team_diagnostics_snapshot_history_injected_runner_receives_filters_and_prints_formatter_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_snapshot_env(monkeypatch)
    runner_calls: list[dict[str, object]] = []
    report = _history_report()

    def runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        assert kwargs["dsn"] == LOCAL_SNAPSHOT_DSN
        assert kwargs["table_name"] == SNAPSHOT_TABLE
        assert kwargs["team_id"] == "crypto_btc"
        assert kwargs["market_slug"] == "bitcoin-above-120k"
        assert kwargs["forecast_id"] == "forecast-btc-1"
        assert kwargs["config_version"] == "team-diagnostics-snapshot-v0"
        assert kwargs["limit"] == 7
        assert type(kwargs["config"]) is TeamDiagnosticsSnapshotHistoryConfig
        assert isinstance(kwargs["generated_at"], datetime)
        assert kwargs["generated_at"].tzinfo is UTC
        assert not {
            "auth",
            "wallet",
            "order",
            "private_key",
            "account",
        } & set(kwargs)
        return report

    exit_code = _invoke_main(
        [
            COMMAND,
            "--team-id",
            "crypto_btc",
            "--market-slug",
            "bitcoin-above-120k",
            "--forecast-id",
            "forecast-btc-1",
            "--config-version",
            "team-diagnostics-snapshot-v0",
            "--limit",
            "7",
        ],
        team_diagnostics_snapshot_history_runner=runner,
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    assert "status=observed" in out
    assert "snapshot_count=3" in out
    assert "required_snapshot_count=2" in out
    assert "status_counts=observed:3" in out
    assert "evidence_quality_average_delta=0.200000" in out
    assert "memory_eligible_delta=2" in out
    assert "settled_calibration_delta=1" in out
    assert "reason_codes=none" in out
    assert "paper_only=True" in out
    assert "report_only=True" in out
    assert "readonly=True" in out
    assert "persisted=" not in out
    assert LOCAL_SNAPSHOT_DSN not in out
    assert SNAPSHOT_TABLE not in out


def test_team_diagnostics_snapshot_history_runner_failure_redacts_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_snapshot_env(monkeypatch)
    failure_message = (
        f"load failed dsn={LOCAL_SNAPSHOT_DSN} table={SNAPSHOT_TABLE} "
        "market_slug=bitcoin-above-120k question='secret market question' "
        "payload_json={'report_sha256': '"
        + REPORT_HASH
        + "'}"
    )

    def runner(**_kwargs: object) -> object:
        raise RuntimeError(failure_message)

    exit_code = _invoke_main(
        [COMMAND, "--market-slug", "bitcoin-above-120k", "--limit", "5"],
        team_diagnostics_snapshot_history_runner=runner,
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined
    assert "bitcoin-above-120k" not in combined
    assert "secret market question" not in combined
    assert REPORT_HASH not in combined
    assert "<redacted-dsn>" in combined
    assert "<redacted-table>" in combined
    assert "<redacted-market-slug>" in combined
    assert "<redacted-question>" in combined
    assert "<redacted-payload>" in combined


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_diagnostics_snapshot_history_rejects_injected_runner_false_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_snapshot_env(monkeypatch)
    values = {
        "status": "observed",
        "snapshot_count": 1,
        "required_snapshot_count": 2,
        "earliest_generated_at": datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
        "latest_generated_at": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        "span_seconds": 3600,
        "status_counts": (("observed", 1),),
        "evidence_quality_average_delta": Decimal("0"),
        "memory_eligible_delta": 0,
        "settled_calibration_delta": 0,
        "duplicate_latest_generated_at": False,
        "reason_codes": (),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values[flag_name] = False

    exit_code = _invoke_main(
        [COMMAND, "--limit", "5"],
        team_diagnostics_snapshot_history_runner=lambda **_kwargs: SimpleNamespace(
            **values,
        ),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert f"{flag_name} must be True" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined


def _history_report() -> TeamDiagnosticsSnapshotHistoryReport:
    return TeamDiagnosticsSnapshotHistoryReport(
        generated_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        config_version="team-diagnostics-snapshot-history-v0",
        snapshot_count=3,
        required_snapshot_count=2,
        status="observed",
        reason_codes=(),
        latest_snapshot=None,
        earliest_generated_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        span_seconds=3600,
        status_counts=(("observed", 3),),
        evidence_quality_average_delta=Decimal("0.200000"),
        evidence_quality_delta=Decimal("0.200000"),
        memory_eligible_delta=2,
        settled_calibration_delta=1,
        duplicate_latest_generated_at=False,
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


def _clear_snapshot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in TEAM_DIAGNOSTICS_SNAPSHOT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _enable_snapshot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_snapshot_env(monkeypatch)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR, LOCAL_SNAPSHOT_DSN)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR, SNAPSHOT_TABLE)


def _disable_snapshot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_snapshot_env(monkeypatch)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR, "false")
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR, LOCAL_SNAPSHOT_DSN)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR, SNAPSHOT_TABLE)


def _enable_snapshot_env_without_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_snapshot_env(monkeypatch)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR, SNAPSHOT_TABLE)


def _forbidden_client_factory(calls: list[str]):
    def factory() -> object:
        calls.append("client_factory")
        raise AssertionError(f"{COMMAND} must not build a market client")

    return factory


def _forbidden_history_runner(calls: list[str]):
    def runner(*args: object, **kwargs: object) -> object:
        calls.append("history_runner")
        raise AssertionError(f"{COMMAND} must fail before loading history")

    return runner


def _install_psycopg_connect_guard(
    monkeypatch: pytest.MonkeyPatch,
    side_effect_calls: list[str],
) -> None:
    def forbidden_connect(*args: object, **kwargs: object) -> object:
        side_effect_calls.append("psycopg.connect")
        raise AssertionError(f"{COMMAND} must not open psycopg when DB is disabled")

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
