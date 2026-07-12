from __future__ import annotations

import builtins
import inspect
import os
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

import polymarket_alpha_lab.cli as cli_module
from polymarket_alpha_lab.cli import main
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
TEAM_FORECAST_TABLE = "diagnostic_team_forecasts"
TEAM_FORECAST_EVIDENCE_TABLE = "diagnostic_team_evidence"
TEAM_FORECAST_OUTCOME_TABLE = "diagnostic_team_outcomes"

TEAM_FORECAST_ENV_VARS = (
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_PROFILE_DB_TABLE_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
)


@dataclass(frozen=True)
class _FakeOutputRow:
    section: str
    label: str
    value: str


@dataclass(frozen=True)
class _FakeCliResult:
    request: object
    forecasts: tuple[object, ...]
    evidence: tuple[object, ...]
    outcomes: tuple[object, ...]
    bundle: object
    summary_rows: tuple[_FakeOutputRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_root_help_lists_team_diagnostics(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "team-diagnostics" in captured.out


def test_team_diagnostics_help_declares_readonly_local_postgres_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["team-diagnostics", "--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    help_text = captured.out
    normalized = help_text.lower()

    assert "team-diagnostics" in help_text
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


@pytest.mark.parametrize("bad_limit", ["0", "-1"])
def test_team_diagnostics_rejects_nonpositive_limit_before_side_effects(
    bad_limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_team_forecast_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_forbidden_env_reads(monkeypatch, side_effect_calls)
    _install_forbidden_team_diagnostics_runner(monkeypatch, side_effect_calls)
    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        ["team-diagnostics", "--limit", bad_limit],
        client_factory=_forbidden_client_factory(client_factory_calls),
    )

    assert exit_code != 0
    assert side_effect_calls == []
    assert client_factory_calls == []
    captured = capsys.readouterr()
    assert "team-diagnostics" in captured.err
    assert "limit" in captured.err.lower()
    assert "positive" in captured.err.lower()


@pytest.mark.parametrize(
    ("case_name", "env_values", "expected_fragment"),
    (
        ("missing", {}, "team forecast db"),
        ("disabled", {TEAM_FORECAST_DB_ENABLED_ENV_VAR: "false"}, "disabled"),
    ),
)
def test_team_diagnostics_fails_closed_when_team_forecast_db_env_is_unavailable(
    case_name: str,
    env_values: dict[str, str],
    expected_fragment: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_team_forecast_env(monkeypatch)
    for name, value in env_values.items():
        monkeypatch.setenv(name, value)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_forbidden_team_diagnostics_runner(monkeypatch, side_effect_calls)
    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        ["team-diagnostics", "--limit", "5"],
        client_factory=_forbidden_client_factory(client_factory_calls),
    )

    assert exit_code == 1, case_name
    assert side_effect_calls == []
    assert client_factory_calls == []
    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "team-diagnostics failed:" in combined
    assert expected_fragment in combined.lower()
    assert LOCAL_TEAM_FORECAST_DSN not in combined
    assert "postgresql://" not in combined


def test_team_diagnostics_accepts_filters_and_prints_compact_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_team_forecast_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []
    observed_requests: list[object] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)
    _install_successful_team_diagnostics_injections(monkeypatch, observed_requests)

    exit_code = _invoke_main(
        [
            "team-diagnostics",
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
    )

    assert exit_code == 0
    assert side_effect_calls == []
    assert client_factory_calls == []
    assert observed_requests
    for request in observed_requests:
        _assert_request_filters(request)

    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "team-diagnostics:" in captured.out
    assert "paper_only=True" in captured.out
    assert "report_only=True" in captured.out
    assert "readonly=True" in captured.out
    assert "row-counts:" in captured.out
    assert "calibration=1" in captured.out
    assert "memory-eligible-references: count=1" in captured.out
    assert LOCAL_TEAM_FORECAST_DSN not in combined
    assert TEAM_FORECAST_TABLE not in combined
    assert TEAM_FORECAST_EVIDENCE_TABLE not in combined
    assert TEAM_FORECAST_OUTCOME_TABLE not in combined


def test_team_diagnostics_rejects_output_missing_phase1_boundary_flags(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_team_forecast_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []
    observed_requests: list[object] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)
    _install_successful_team_diagnostics_injections(monkeypatch, observed_requests)

    exit_code = _invoke_main(
        [
            "team-diagnostics",
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
        team_diagnostics_stdout_formatter=lambda _bundle: (
            "team-diagnostics:\n"
            "row-counts: calibration=1 event_template_rows=1 "
            "source_reliability_rows=1 evidence_quality_rows=1 "
            "memory_eligible_references=1\n"
        ),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "team-diagnostics failed:" in captured.err
    assert "paper_only=True" in captured.err
    assert "report_only=True" in captured.err
    assert "readonly=True" in captured.err


def test_team_diagnostics_redacts_dsn_and_table_on_source_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_team_forecast_env(monkeypatch)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []
    failure_message = (
        f"could not read {LOCAL_TEAM_FORECAST_DSN} table={TEAM_FORECAST_TABLE} "
        "market_slug=bitcoin-above-120k question='secret market question'"
    )

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)
    _install_failing_team_diagnostics_injections(monkeypatch, failure_message)

    exit_code = _invoke_main(
        ["team-diagnostics", "--team-id", "crypto_btc", "--limit", "5"],
        client_factory=_forbidden_client_factory(client_factory_calls),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "team-diagnostics failed:" in combined
    assert LOCAL_TEAM_FORECAST_DSN not in combined
    assert TEAM_FORECAST_TABLE not in combined
    assert "bitcoin-above-120k" not in combined
    assert "secret market question" not in combined
    assert "<redacted-dsn>" in combined
    assert "<redacted-table>" in combined
    assert "<redacted-market-slug>" in combined
    assert "<redacted-question>" in combined


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


def _forbidden_client_factory(calls: list[str]):
    def factory() -> object:
        calls.append("client_factory")
        raise AssertionError("team-diagnostics must not build a market client")

    return factory


def _install_forbidden_env_reads(
    monkeypatch: pytest.MonkeyPatch,
    side_effect_calls: list[str],
) -> None:
    def forbidden_env_read(*args: object, **kwargs: object) -> object:
        side_effect_calls.append("team_forecast_env")
        raise AssertionError("team-diagnostics limit validation must run before env")

    import polymarket_alpha_lab.supabase_team_forecast_config as env_module

    monkeypatch.setattr(
        env_module,
        "from_team_forecast_db_env",
        forbidden_env_read,
    )
    monkeypatch.setattr(
        cli_module,
        "from_team_forecast_db_env",
        forbidden_env_read,
        raising=False,
    )

    original_os_getenv = os.getenv
    original_environ_get = os.environ.get

    def forbidden_os_getenv(key: str, *args: object, **kwargs: object) -> str | None:
        if key in TEAM_FORECAST_ENV_VARS:
            side_effect_calls.append("os.getenv")
            raise AssertionError(
                "team-diagnostics limit validation must run before team forecast env",
            )
        return original_os_getenv(key, *args, **kwargs)

    def forbidden_environ_get(key: str, *args: object, **kwargs: object) -> str | None:
        if key in TEAM_FORECAST_ENV_VARS:
            side_effect_calls.append("os.environ.get")
            raise AssertionError(
                "team-diagnostics limit validation must run before team forecast env",
            )
        return original_environ_get(key, *args, **kwargs)

    monkeypatch.setattr(os, "getenv", forbidden_os_getenv)
    monkeypatch.setattr(os.environ, "get", forbidden_environ_get)


def _install_forbidden_team_diagnostics_runner(
    monkeypatch: pytest.MonkeyPatch,
    side_effect_calls: list[str],
) -> None:
    def forbidden_runner(*args: object, **kwargs: object) -> object:
        side_effect_calls.append("team_diagnostics_runner")
        raise AssertionError("team-diagnostics runner must not be called")

    def forbidden_source(*args: object, **kwargs: object) -> object:
        side_effect_calls.append("team_diagnostics_source")
        raise AssertionError("team-diagnostics DB source must not be called")

    import polymarket_alpha_lab.team_cli_wiring as wiring_module
    import polymarket_alpha_lab.team_diagnostics_db_source as source_module

    monkeypatch.setattr(
        wiring_module,
        "run_team_diagnostics_cli_request",
        forbidden_runner,
    )
    monkeypatch.setattr(
        cli_module,
        "run_team_diagnostics_cli_request",
        forbidden_runner,
        raising=False,
    )
    monkeypatch.setattr(
        source_module,
        "load_team_diagnostics_rows_from_env",
        forbidden_source,
    )
    monkeypatch.setattr(
        cli_module,
        "load_team_diagnostics_rows_from_env",
        forbidden_source,
        raising=False,
    )


def _install_psycopg_connect_guard(
    monkeypatch: pytest.MonkeyPatch,
    side_effect_calls: list[str],
) -> None:
    def forbidden_connect(*args: object, **kwargs: object) -> object:
        side_effect_calls.append("psycopg.connect")
        raise AssertionError("team-diagnostics must not connect through psycopg")

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


def _install_successful_team_diagnostics_injections(
    monkeypatch: pytest.MonkeyPatch,
    observed_requests: list[object],
) -> None:
    fake_bundle = _fake_bundle()

    def fake_load_rows_from_env(*args: object, **kwargs: object) -> object:
        request = kwargs.get("request")
        observed_requests.append(request)
        _assert_request_filters(request)
        return _fake_db_rows()

    def fake_runner(request: object, *args: object, **kwargs: object) -> _FakeCliResult:
        observed_requests.append(request)
        _assert_request_filters(request)
        return _FakeCliResult(
            request=request,
            forecasts=("forecast-row",),
            evidence=("evidence-row",),
            outcomes=("outcome-row",),
            bundle=fake_bundle,
            summary_rows=(
                _FakeOutputRow("filter", "team_id", "crypto_btc"),
                _FakeOutputRow("filter", "market_slug", "bitcoin-above-120k"),
                _FakeOutputRow("filter", "forecast_id", "forecast-btc-1"),
                _FakeOutputRow("filter", "limit", "7"),
                _FakeOutputRow("count", "forecasts", "1"),
                _FakeOutputRow("count", "evidence", "1"),
                _FakeOutputRow("count", "outcomes", "1"),
            ),
        )

    def fake_builder(*args: object, **kwargs: object) -> object:
        return fake_bundle

    def fake_formatter(bundle: object) -> str:
        return (
            "team-diagnostics: paper_only=True report_only=True readonly=True\n"
            "row-counts: calibration=1 event_template_rows=1 "
            "source_reliability_rows=1 evidence_quality_rows=1 "
            "memory_eligible_references=1\n"
            "memory-eligible-references: count=1\n"
            "calibration-summary: bucket_count=1 observation_count=1 "
            "brier_mean=0.04 ece=0.02\n"
        )

    import polymarket_alpha_lab.team_cli_wiring as wiring_module
    import polymarket_alpha_lab.team_diagnostics_bundle as bundle_module
    import polymarket_alpha_lab.team_diagnostics_cli_format as format_module
    import polymarket_alpha_lab.team_diagnostics_db_source as source_module

    monkeypatch.setattr(
        source_module,
        "load_team_diagnostics_rows_from_env",
        fake_load_rows_from_env,
    )
    monkeypatch.setattr(
        cli_module,
        "load_team_diagnostics_rows_from_env",
        fake_load_rows_from_env,
        raising=False,
    )
    monkeypatch.setattr(
        wiring_module,
        "run_team_diagnostics_cli_request",
        fake_runner,
    )
    monkeypatch.setattr(
        cli_module,
        "run_team_diagnostics_cli_request",
        fake_runner,
        raising=False,
    )
    monkeypatch.setattr(
        bundle_module,
        "build_team_diagnostics_bundle_report",
        fake_builder,
    )
    monkeypatch.setattr(
        cli_module,
        "build_team_diagnostics_bundle_report",
        fake_builder,
        raising=False,
    )
    monkeypatch.setattr(
        format_module,
        "format_team_diagnostics_cli_stdout",
        fake_formatter,
    )
    monkeypatch.setattr(
        cli_module,
        "format_team_diagnostics_cli_stdout",
        fake_formatter,
        raising=False,
    )


def _install_failing_team_diagnostics_injections(
    monkeypatch: pytest.MonkeyPatch,
    failure_message: str,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise RuntimeError(failure_message)

    import polymarket_alpha_lab.team_cli_wiring as wiring_module
    import polymarket_alpha_lab.team_diagnostics_db_source as source_module

    monkeypatch.setattr(source_module, "load_team_diagnostics_rows_from_env", fail)
    monkeypatch.setattr(
        cli_module,
        "load_team_diagnostics_rows_from_env",
        fail,
        raising=False,
    )
    monkeypatch.setattr(wiring_module, "run_team_diagnostics_cli_request", fail)
    monkeypatch.setattr(
        cli_module,
        "run_team_diagnostics_cli_request",
        fail,
        raising=False,
    )


def _fake_db_rows() -> object:
    return SimpleNamespace(
        forecasts=("forecast-row",),
        evidence=("evidence-row",),
        outcomes=("outcome-row",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _fake_bundle() -> object:
    return SimpleNamespace(
        paper_only=True,
        report_only=True,
        readonly=True,
        row_counts={
            "calibration": 1,
            "event_template_rows": 1,
            "source_reliability_rows": 1,
            "evidence_quality_rows": 1,
            "memory_eligible_references": 1,
        },
        memory_eligible_references=(
            SimpleNamespace(
                condition_id="0xbtc",
                market_slug="bitcoin-above-120k",
                reason="resolved_outcome",
                score="0.42",
            ),
        ),
        calibration_summary={
            "bucket_count": 1,
            "observation_count": 1,
            "brier_mean": "0.04",
            "ece": "0.02",
        },
        event_template_rows=(),
        source_reliability_rows=(),
        evidence_quality_rows=(),
    )


def _assert_request_filters(request: object) -> None:
    assert request is not None
    assert getattr(request, "team_id") == "crypto_btc"
    assert getattr(request, "market_slug") == "bitcoin-above-120k"
    assert getattr(request, "forecast_id") == "forecast-btc-1"
    assert getattr(request, "limit") == 7
