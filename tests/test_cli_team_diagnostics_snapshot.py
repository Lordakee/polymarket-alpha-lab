from __future__ import annotations

import builtins
import inspect
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config import (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_team_forecast_config import (
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
    TEAM_PROFILE_DB_TABLE_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
)


LOCAL_TEAM_FORECAST_DSN = (
    "postgresql://postgres:local-secret@localhost:54322/postgres"
)
LOCAL_SNAPSHOT_DSN = (
    "postgresql://postgres:snapshot-secret@localhost:54322/postgres"
)
TEAM_FORECAST_TABLE = "diagnostic_team_forecasts"
TEAM_FORECAST_EVIDENCE_TABLE = "diagnostic_team_evidence"
TEAM_FORECAST_OUTCOME_TABLE = "diagnostic_team_outcomes"
SNAPSHOT_TABLE = "team_diagnostics_snapshot_archive"
REPORT_HASH = "b" * 64

TEAM_FORECAST_ENV_VARS = (
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_PROFILE_DB_TABLE_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
)
TEAM_DIAGNOSTICS_SNAPSHOT_ENV_VARS = (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)


@dataclass(frozen=True)
class _FakeSnapshot:
    status: str = "watch"
    forecast_row_count: int = 2
    evidence_row_count: int = 3
    outcome_row_count: int = 1
    memory_eligible_reference_count: int = 1
    calibration_status: str = "pass"
    event_template_status: str = "pass"
    evidence_quality_status: str = "watch"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_root_help_lists_team_diagnostics_snapshot(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "team-diagnostics-snapshot" in captured.out


def test_team_diagnostics_snapshot_help_declares_env_scoped_report_only_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["team-diagnostics-snapshot", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    normalized = help_text.lower()

    assert "team-diagnostics-snapshot" in help_text
    assert "--team-id" in help_text
    assert "--market-slug" in help_text
    assert "--forecast-id" in help_text
    assert "--limit" in help_text
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


def test_team_diagnostics_snapshot_fails_closed_when_snapshot_db_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_team_forecast_env(monkeypatch)
    _disable_snapshot_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        ["team-diagnostics-snapshot", "--limit", "5"],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_diagnostics_rows_loader=_forbidden_rows_loader(side_effect_calls),
        team_diagnostics_snapshot_db_sink=_forbidden_snapshot_sink(side_effect_calls),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "team-diagnostics-snapshot failed:" in combined
    assert "snapshot" in combined.lower()
    assert "disabled" in combined.lower()
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert "postgresql://" not in combined


def test_team_diagnostics_snapshot_persists_injected_snapshot_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_team_forecast_env(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []
    observed_requests: list[object] = []
    observed_snapshot_inputs: list[tuple[object, object, str | None, str | None, str | None]] = []
    persisted_snapshots: list[object] = []
    fake_bundle = _fake_bundle()
    fake_snapshot = _FakeSnapshot()

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    def rows_loader(*args: object, **kwargs: object) -> object:
        request = kwargs.get("request")
        observed_requests.append(request)
        _assert_request_filters(request)
        return _fake_db_rows()

    def bundle_builder(*args: object, **kwargs: object) -> object:
        assert kwargs["forecasts"] == ("forecast-a", "forecast-b")
        assert kwargs["evidence"] == ("evidence-a", "evidence-b", "evidence-c")
        assert kwargs["outcomes"] == ("outcome-a",)
        assert "generated_at" in kwargs
        return fake_bundle

    def snapshot_builder(
        bundle_report: object,
        *,
        config: object,
        team_id: str | None,
        market_slug: str | None,
        forecast_id: str | None,
    ) -> object:
        observed_snapshot_inputs.append(
            (bundle_report, config, team_id, market_slug, forecast_id),
        )
        return fake_snapshot

    def snapshot_sink(report: object) -> object:
        persisted_snapshots.append(report)
        return SimpleNamespace(
            row=SimpleNamespace(report_sha256=REPORT_HASH),
            inserted=True,
        )

    exit_code = _invoke_main(
        [
            "team-diagnostics-snapshot",
            "--team-id",
            "crypto_btc",
            "--market-slug",
            "bitcoin-above-120k",
            "--forecast-id",
            "forecast-btc-1",
            "--limit",
            "7",
        ],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_diagnostics_rows_loader=rows_loader,
        team_diagnostics_bundle_builder=bundle_builder,
        team_diagnostics_snapshot_builder=snapshot_builder,
        team_diagnostics_snapshot_db_sink=snapshot_sink,
    )

    assert exit_code == 0
    assert side_effect_calls == []
    assert client_factory_calls == []
    assert observed_requests
    for request in observed_requests:
        _assert_request_filters(request)
    assert observed_snapshot_inputs == [
        (
            fake_bundle,
            observed_snapshot_inputs[0][1],
            "crypto_btc",
            "bitcoin-above-120k",
            "forecast-btc-1",
        ),
    ]
    assert persisted_snapshots == [fake_snapshot]

    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "team-diagnostics-snapshot:" in captured.out
    assert f"report_sha256={REPORT_HASH}" in captured.out
    assert "inserted=True" in captured.out
    assert "status=watch" in captured.out
    assert "forecast_count=2" in captured.out
    assert "evidence_count=3" in captured.out
    assert "outcome_count=1" in captured.out
    assert "paper_only=True" in captured.out
    assert "report_only=True" in captured.out
    assert "readonly=True" in captured.out
    assert LOCAL_TEAM_FORECAST_DSN not in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined


def test_team_diagnostics_snapshot_redacts_dsn_table_and_payload_on_write_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_team_forecast_env(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []
    failure_message = (
        f"insert failed dsn={LOCAL_SNAPSHOT_DSN} table={SNAPSHOT_TABLE} "
        "market_slug=bitcoin-above-120k question='secret market question' "
        "payload_json={'report_sha256': '"
        + REPORT_HASH
        + "'}"
    )

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    def snapshot_sink(_report: object) -> object:
        raise RuntimeError(failure_message)

    exit_code = _invoke_main(
        ["team-diagnostics-snapshot", "--team-id", "crypto_btc", "--limit", "5"],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_diagnostics_rows_loader=lambda *args, **kwargs: _fake_db_rows(),
        team_diagnostics_bundle_builder=lambda *args, **kwargs: _fake_bundle(),
        team_diagnostics_snapshot_builder=lambda *args, **kwargs: _FakeSnapshot(),
        team_diagnostics_snapshot_db_sink=snapshot_sink,
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "team-diagnostics-snapshot failed:" in combined
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


def _clear_team_forecast_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in TEAM_FORECAST_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _clear_snapshot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in TEAM_DIAGNOSTICS_SNAPSHOT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _enable_team_forecast_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_team_forecast_env(monkeypatch)
    monkeypatch.setenv(TEAM_FORECAST_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(TEAM_FORECAST_DB_DSN_ENV_VAR, LOCAL_TEAM_FORECAST_DSN)
    monkeypatch.setenv(TEAM_FORECAST_DB_TABLE_ENV_VAR, TEAM_FORECAST_TABLE)
    monkeypatch.setenv(
        TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
        TEAM_FORECAST_EVIDENCE_TABLE,
    )
    monkeypatch.setenv(
        TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
        TEAM_FORECAST_OUTCOME_TABLE,
    )


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


def _forbidden_client_factory(calls: list[str]):
    def factory() -> object:
        calls.append("client_factory")
        raise AssertionError("team-diagnostics-snapshot must not build a market client")

    return factory


def _forbidden_rows_loader(calls: list[str]):
    def loader(*args: object, **kwargs: object) -> object:
        calls.append("rows_loader")
        raise AssertionError("team-diagnostics-snapshot must fail before loading rows")

    return loader


def _forbidden_snapshot_sink(calls: list[str]):
    def sink(*args: object, **kwargs: object) -> object:
        calls.append("snapshot_sink")
        raise AssertionError("team-diagnostics-snapshot must fail before persistence")

    return sink


def _install_psycopg_connect_guard(
    monkeypatch: pytest.MonkeyPatch,
    side_effect_calls: list[str],
) -> None:
    def forbidden_connect(*args: object, **kwargs: object) -> object:
        side_effect_calls.append("psycopg.connect")
        raise AssertionError("team-diagnostics-snapshot must not open psycopg in CLI tests")

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


def _fake_db_rows() -> object:
    return SimpleNamespace(
        forecasts=("forecast-a", "forecast-b"),
        evidence=("evidence-a", "evidence-b", "evidence-c"),
        outcomes=("outcome-a",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _fake_bundle() -> object:
    return SimpleNamespace(
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _assert_request_filters(request: object) -> None:
    assert request is not None
    assert getattr(request, "team_id") == "crypto_btc"
    assert getattr(request, "market_slug") == "bitcoin-above-120k"
    assert getattr(request, "forecast_id") == "forecast-btc-1"
    assert getattr(request, "limit") == 7
