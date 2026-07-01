from __future__ import annotations

import builtins
import importlib
import inspect
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
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
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


COMMAND = "team-memory-readiness-digest"
DIGEST_CONFIG_VERSION = "team-memory-readiness-digest-v0"
HISTORY_CONFIG_VERSION = "team-diagnostics-snapshot-history-v0"
GATE_CONFIG_VERSION = "team-diagnostics-snapshot-history-gate-v0"
DIGEST_MODULE = "polymarket_alpha_lab.team_memory_readiness_digest"
DIGEST_FORMATTER_MODULE = "polymarket_alpha_lab.team_memory_readiness_digest_cli_format"
DIGEST_DB_SOURCE_MODULE = "polymarket_alpha_lab.team_memory_readiness_digest_db_source"
GATE_MODULE = "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate"
LOCAL_SNAPSHOT_DSN = "host=localhost port=54322 dbname=postgres user=postgres"
SNAPSHOT_TABLE = "team_diagnostics_snapshot_archive"
REPORT_HASH = "a" * 64

TEAM_DIAGNOSTICS_SNAPSHOT_ENV_VARS = (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)


def test_root_help_lists_team_memory_readiness_digest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_team_memory_readiness_digest_help_is_env_scoped_read_only_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    normalized = help_text.lower()

    assert COMMAND in help_text
    for flag in ("--team-id", "--config-version", "--limit"):
        assert flag in help_text
    assert "--market-slug" not in help_text
    assert "--forecast-id" not in help_text
    assert "read-only" in normalized or "readonly" in normalized
    assert "report-only" in normalized or "report only" in normalized
    assert "local" in normalized
    assert "supabase" in normalized
    assert "postgres" in normalized

    forbidden_flags = (
        "--dsn",
        "--table",
        "--persist",
        "--live",
        "--auth",
        "--wallet",
        "--order",
        "--private-key",
        "--account",
    )
    for flag in forbidden_flags:
        assert flag not in help_text


def test_team_memory_readiness_digest_fails_closed_when_snapshot_db_disabled(
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
        team_memory_readiness_digest_runner=_forbidden_digest_runner(
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


def test_team_memory_readiness_digest_fails_closed_when_snapshot_db_dsn_missing(
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
        team_memory_readiness_digest_runner=_forbidden_digest_runner(
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


@pytest.mark.parametrize("bad_limit", ("0", "-1"))
def test_team_memory_readiness_digest_fails_before_env_or_side_effects_on_non_positive_limit(
    bad_limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_snapshot_env(monkeypatch)
    env_calls: list[str] = []
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    def forbidden_env() -> object:
        env_calls.append("env")
        raise AssertionError(f"{COMMAND} must reject invalid limits before env reads")

    import polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config as snapshot_env

    monkeypatch.setattr(
        snapshot_env,
        "from_team_diagnostics_snapshot_db_env",
        forbidden_env,
    )
    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND, "--limit", bad_limit],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_memory_readiness_digest_runner=_forbidden_digest_runner(
            side_effect_calls,
        ),
    )

    assert exit_code == 1
    assert env_calls == []
    assert side_effect_calls == []
    assert client_factory_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert "limit must be positive" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert "postgresql://" not in combined


def test_team_memory_readiness_digest_injected_runner_receives_env_team_ids_configs_and_prints_formatter_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    digest_api = _install_or_get_digest_api(monkeypatch)
    gate_api = _install_or_get_gate_api(monkeypatch)
    _install_or_get_digest_formatter(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    runner_calls: list[dict[str, object]] = []
    report = _digest_report()

    def runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        assert kwargs["dsn"] == LOCAL_SNAPSHOT_DSN
        assert kwargs["table_name"] == SNAPSHOT_TABLE
        assert kwargs["team_ids"] == ("crypto_btc", "macro_rates")
        assert kwargs["config_version"] == "snapshot-history-v1"
        assert kwargs["limit"] == 7
        history_config = kwargs["history_config"]
        assert type(history_config) is TeamDiagnosticsSnapshotHistoryConfig
        assert history_config.config_version == HISTORY_CONFIG_VERSION
        assert history_config.paper_only is True
        assert history_config.report_only is True
        assert history_config.readonly is True
        gate_config = kwargs["gate_config"]
        assert type(gate_config) is gate_api.TeamDiagnosticsSnapshotHistoryGateConfig
        assert gate_config.config_version == GATE_CONFIG_VERSION
        assert gate_config.paper_only is True
        assert gate_config.report_only is True
        assert gate_config.readonly is True
        digest_config = kwargs["digest_config"]
        assert type(digest_config) is digest_api.TeamMemoryReadinessDigestConfig
        assert digest_config.config_version == DIGEST_CONFIG_VERSION
        assert digest_config.paper_only is True
        assert digest_config.report_only is True
        assert digest_config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
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
            "--team-id",
            "macro_rates",
            "--config-version",
            "snapshot-history-v1",
            "--limit",
            "7",
        ],
        team_memory_readiness_digest_runner=runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    assert "digest_status=watch" in out
    assert "recommended_next_step=throttle_team_memory_readiness_use" in out
    assert "team_count=2" in out
    assert "source_statuses=crypto_btc:pass:120:3/2,macro_rates:watch:300:2/2" in out
    assert (
        "source_config_versions="
        "crypto_btc:team-diagnostics-snapshot-history-v0,"
        "macro_rates:team-diagnostics-snapshot-history-v0"
    ) in out
    assert "reason_code_counts=team_memory_readiness_digest_watch_sources_present:1" in out
    assert "reason_codes=team_memory_readiness_digest_watch_sources_present" in out
    assert "paper_only=True" in out
    assert "report_only=True" in out
    assert "readonly=True" in out
    assert "persisted=" not in out
    assert LOCAL_SNAPSHOT_DSN not in out
    assert SNAPSHOT_TABLE not in out


def test_team_memory_readiness_digest_omitted_team_ids_default_to_all_known_teams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_digest_api(monkeypatch)
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_digest_formatter(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    runner_calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        return _digest_report(team_ids=tuple(TEAM_IDS))

    exit_code = _invoke_main(
        [COMMAND, "--limit", "5"],
        team_memory_readiness_digest_runner=runner,
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert runner_calls[0]["team_ids"] == TEAM_IDS


def test_team_memory_readiness_digest_default_path_wraps_gate_reports_before_digest_builder(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    digest_api = _install_or_get_digest_api(monkeypatch)
    gate_api = _install_or_get_gate_api(monkeypatch)
    _install_or_get_digest_formatter(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    fake_history_report = object()
    fake_snapshot_loader = object()
    history_source_calls: list[dict[str, object]] = []
    gate_source_calls: list[dict[str, object]] = []
    digest_source_calls: list[dict[str, object]] = []

    history_source_module = ModuleType(
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_db_source",
    )

    def load_team_diagnostics_snapshot_history_report(**kwargs: object) -> object:
        from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
            build_team_diagnostics_snapshot_history_report,
        )

        history_source_calls.append(kwargs)
        assert kwargs["load_snapshots"] is fake_snapshot_loader
        assert kwargs["team_id"] in ("crypto_btc", "macro_rates")
        assert kwargs["market_slug"] is None
        assert kwargs["forecast_id"] is None
        assert kwargs["config_version"] == "snapshot-history-v1"
        assert kwargs["limit"] == 7
        assert type(kwargs["config"]) is TeamDiagnosticsSnapshotHistoryConfig
        assert kwargs["history_builder"] is build_team_diagnostics_snapshot_history_report
        return fake_history_report

    history_source_module.load_team_diagnostics_snapshot_history_report = (
        load_team_diagnostics_snapshot_history_report
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_db_source",
        history_source_module,
    )

    psycopg_module = ModuleType("polymarket_alpha_lab.team_diagnostics_snapshot_psycopg")
    psycopg_module.load_team_diagnostics_snapshot_reports_from_env = fake_snapshot_loader
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_diagnostics_snapshot_psycopg",
        psycopg_module,
    )

    gate_source_module = ModuleType(
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_db_source",
    )

    def load_team_diagnostics_snapshot_history_gate_report(**kwargs: object) -> object:
        from polymarket_alpha_lab.team_diagnostics_snapshot_history_gate import (
            build_team_diagnostics_snapshot_history_gate_report,
        )

        gate_source_calls.append(kwargs)
        team_id = kwargs["team_id"]
        assert team_id in ("crypto_btc", "macro_rates")
        assert kwargs["market_slug"] is None
        assert kwargs["forecast_id"] is None
        assert kwargs["config_version"] == "snapshot-history-v1"
        assert kwargs["limit"] == 7
        assert type(kwargs["history_config"]) is TeamDiagnosticsSnapshotHistoryConfig
        assert type(kwargs["gate_config"]) is gate_api.TeamDiagnosticsSnapshotHistoryGateConfig
        assert isinstance(kwargs["generated_at"], datetime)
        assert kwargs["generated_at"].tzinfo is UTC
        assert kwargs["gate_builder"] is build_team_diagnostics_snapshot_history_gate_report
        history_report = kwargs["history_loader"](
            config=kwargs["history_config"],
            generated_at=kwargs["generated_at"],
            team_id=team_id,
            market_slug=kwargs["market_slug"],
            forecast_id=kwargs["forecast_id"],
            config_version=kwargs["config_version"],
            limit=kwargs["limit"],
        )
        assert history_report is fake_history_report
        return _gate_report(str(team_id))

    gate_source_module.load_team_diagnostics_snapshot_history_gate_report = (
        load_team_diagnostics_snapshot_history_gate_report
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_db_source",
        gate_source_module,
    )

    digest_source_module = ModuleType(DIGEST_DB_SOURCE_MODULE)

    def load_team_memory_readiness_digest_report(**kwargs: object) -> object:
        digest_source_calls.append(kwargs)
        assert kwargs["team_ids"] == ("crypto_btc", "macro_rates")
        assert kwargs["config_version"] == "snapshot-history-v1"
        assert kwargs["limit"] == 7
        assert type(kwargs["history_config"]) is TeamDiagnosticsSnapshotHistoryConfig
        assert type(kwargs["gate_config"]) is gate_api.TeamDiagnosticsSnapshotHistoryGateConfig
        assert type(kwargs["digest_config"]) is digest_api.TeamMemoryReadinessDigestConfig
        assert kwargs["digest_builder"] is digest_api.build_team_memory_readiness_digest_report
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        gate_reports = tuple(
            kwargs["gate_loader"](
                team_id=team_id,
                history_config=kwargs["history_config"],
                gate_config=kwargs["gate_config"],
                generated_at=generated_at,
                config_version=kwargs["config_version"],
                limit=kwargs["limit"],
            )
            for team_id in kwargs["team_ids"]
        )
        assert tuple(report.config_version for report in gate_reports) == (
            GATE_CONFIG_VERSION,
            GATE_CONFIG_VERSION,
        )
        assert all(not hasattr(report, "team_id") for report in gate_reports)
        digest_sources = tuple(
            digest_api.TeamMemoryReadinessDigestSource(
                team_id=team_id,
                gate_report=gate_report,
            )
            for team_id, gate_report in zip(kwargs["team_ids"], gate_reports)
        )
        return kwargs["digest_builder"](
            digest_sources,
            config=kwargs["digest_config"],
            generated_at=generated_at,
        )

    digest_source_module.load_team_memory_readiness_digest_report = (
        load_team_memory_readiness_digest_report
    )
    monkeypatch.setitem(sys.modules, DIGEST_DB_SOURCE_MODULE, digest_source_module)

    exit_code = _invoke_main(
        [
            COMMAND,
            "--team-id",
            "crypto_btc",
            "--team-id",
            "macro_rates",
            "--config-version",
            "snapshot-history-v1",
            "--limit",
            "7",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(digest_source_calls) == 1
    assert len(gate_source_calls) == 2
    assert len(history_source_calls) == 2
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    assert "digest_status=watch" in out
    assert LOCAL_SNAPSHOT_DSN not in out
    assert SNAPSHOT_TABLE not in out


def test_team_memory_readiness_digest_runner_failure_redacts_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_digest_api(monkeypatch)
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_digest_formatter(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    failure_message = (
        f"load failed dsn={LOCAL_SNAPSHOT_DSN} table={SNAPSHOT_TABLE} "
        "market_slug=bitcoin-above-120k "
        "marketSlug=camel-case-market "
        "raw_filter=bitcoin-above-120k "
        "question='secret market question' "
        "payload_json={'marketSlug': 'nested-market', 'question': 'nested question'} "
        f"report_sha256={REPORT_HASH}"
    )

    def runner(**_kwargs: object) -> object:
        raise RuntimeError(failure_message)

    exit_code = _invoke_main(
        [COMMAND, "--team-id", "crypto_btc", "--limit", "5"],
        team_memory_readiness_digest_runner=runner,
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined
    assert "bitcoin-above-120k" not in combined
    assert "camel-case-market" not in combined
    assert "secret market question" not in combined
    assert "nested-market" not in combined
    assert "nested question" not in combined
    assert REPORT_HASH not in combined
    assert "<redacted-dsn>" in combined
    assert "<redacted-table>" in combined
    assert "<redacted-market-slug>" in combined
    assert "<redacted-question>" in combined
    assert "<redacted-payload>" in combined
    assert "<redacted-sha256>" in combined


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_memory_readiness_digest_rejects_injected_runner_false_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_digest_api(monkeypatch)
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_digest_formatter(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    report = vars(_digest_report()).copy()
    report[flag_name] = False

    exit_code = _invoke_main(
        [COMMAND, "--limit", "5"],
        team_memory_readiness_digest_runner=lambda **_kwargs: SimpleNamespace(
            **report,
        ),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert f"{flag_name} must be True" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_memory_readiness_digest_rejects_injected_runner_missing_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_digest_api(monkeypatch)
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_digest_formatter(monkeypatch)
    _enable_snapshot_env(monkeypatch)
    report = vars(_digest_report()).copy()
    del report[flag_name]

    exit_code = _invoke_main(
        [COMMAND, "--limit", "5"],
        team_memory_readiness_digest_runner=lambda **_kwargs: SimpleNamespace(
            **report,
        ),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert f"{flag_name} must be True" in combined
    assert LOCAL_SNAPSHOT_DSN not in combined
    assert SNAPSHOT_TABLE not in combined


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "host=localhost dbname=snapshot_history_gate"],
        [COMMAND, "--table", "team_diagnostics_snapshot_archive"],
        [COMMAND, "--persist"],
        [COMMAND, "--live"],
        [COMMAND, "--auth", "token"],
        [COMMAND, "--wallet", "wallet"],
        [COMMAND, "--order", "order"],
        [COMMAND, "--private-key", "secret"],
        [COMMAND, "--account", "account"],
        [COMMAND, "--market-slug", "bitcoin-above-120k"],
        [COMMAND, "--forecast-id", "forecast-btc-1"],
    ),
)
def test_team_memory_readiness_digest_rejects_forbidden_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def _digest_report(
    *,
    team_ids: tuple[str, ...] = ("crypto_btc", "macro_rates"),
) -> SimpleNamespace:
    source_statuses = tuple(
        SimpleNamespace(
            team_id=team_id,
            gate_status="watch" if team_id == "macro_rates" else "pass",
            recommended_next_step=(
                "review_team_diagnostics_snapshot_history"
                if team_id == "macro_rates"
                else "allow_team_diagnostics_snapshot_history_use"
            ),
            source_config_version=HISTORY_CONFIG_VERSION,
            latest_snapshot_age_seconds=300 if team_id == "macro_rates" else 120,
            source_snapshot_count=2 if team_id == "macro_rates" else 3,
            source_required_snapshot_count=2,
            source_status="observed",
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for team_id in team_ids
    )
    return SimpleNamespace(
        generated_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        config_version=DIGEST_CONFIG_VERSION,
        digest_status="watch",
        recommended_next_step="throttle_team_memory_readiness_use",
        team_count=len(team_ids),
        pass_count=max(len(team_ids) - 1, 0),
        watch_count=1 if team_ids else 0,
        blocked_count=0,
        source_statuses=source_statuses,
        source_config_versions=(
            tuple((team_id, HISTORY_CONFIG_VERSION) for team_id in team_ids)
        ),
        reason_code_counts=(
            SimpleNamespace(
                reason_code="team_memory_readiness_digest_watch_sources_present",
                count=1,
            ),
        ),
        reason_codes=("team_memory_readiness_digest_watch_sources_present",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _gate_report(team_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        config_version=GATE_CONFIG_VERSION,
        gate_status="watch" if team_id == "macro_rates" else "pass",
        recommended_next_step="review_team_diagnostics_snapshot_history",
        source_config_version=HISTORY_CONFIG_VERSION,
        latest_snapshot_age_seconds=300 if team_id == "macro_rates" else 120,
        source_snapshot_count=2,
        source_required_snapshot_count=2,
        source_status="observed",
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _install_or_get_digest_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    module = ModuleType(DIGEST_MODULE)
    module.DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION = DIGEST_CONFIG_VERSION

    @dataclass(frozen=True)
    class TeamMemoryReadinessDigestConfig:
        config_version: str = DIGEST_CONFIG_VERSION
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    @dataclass(frozen=True)
    class TeamMemoryReadinessDigestSource:
        team_id: str
        gate_report: object
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    def build_team_memory_readiness_digest_report(
        sources: object,
        *,
        config: TeamMemoryReadinessDigestConfig,
        generated_at: datetime,
    ) -> SimpleNamespace:
        del config, generated_at
        source_rows = tuple(sources)
        for source in source_rows:
            assert type(source) is TeamMemoryReadinessDigestSource
            assert source.team_id in TEAM_IDS
            gate_report = source.gate_report
            assert not hasattr(gate_report, "team_id")
            assert gate_report.config_version == GATE_CONFIG_VERSION
            assert gate_report.paper_only is True
            assert gate_report.report_only is True
            assert gate_report.readonly is True
        return _digest_report(team_ids=tuple(source.team_id for source in source_rows))

    module.TeamMemoryReadinessDigestConfig = TeamMemoryReadinessDigestConfig
    module.TeamMemoryReadinessDigestSource = TeamMemoryReadinessDigestSource
    module.build_team_memory_readiness_digest_report = (
        build_team_memory_readiness_digest_report
    )
    monkeypatch.setitem(sys.modules, DIGEST_MODULE, module)
    return module


def _install_or_get_gate_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(GATE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != GATE_MODULE:
            raise

    module = ModuleType(GATE_MODULE)

    @dataclass(frozen=True)
    class TeamDiagnosticsSnapshotHistoryGateConfig:
        config_version: str = GATE_CONFIG_VERSION
        min_source_snapshot_count: int = 2
        max_latest_snapshot_age_seconds: int = 86_400
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    def build_team_diagnostics_snapshot_history_gate_report(
        history_report: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryGateConfig,
        generated_at: datetime,
    ) -> object:
        del config, generated_at
        return history_report

    module.TeamDiagnosticsSnapshotHistoryGateConfig = (
        TeamDiagnosticsSnapshotHistoryGateConfig
    )
    module.build_team_diagnostics_snapshot_history_gate_report = (
        build_team_diagnostics_snapshot_history_gate_report
    )
    monkeypatch.setitem(sys.modules, GATE_MODULE, module)
    return module


def _install_or_get_digest_formatter(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(DIGEST_FORMATTER_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != DIGEST_FORMATTER_MODULE:
            raise

    module = ModuleType(DIGEST_FORMATTER_MODULE)

    def format_team_memory_readiness_digest_cli_stdout(report: object) -> str:
        return (
            f"{COMMAND}: "
            f"digest_status={_string_value(getattr(report, 'digest_status'))} "
            "recommended_next_step="
            f"{_string_value(getattr(report, 'recommended_next_step'))} "
            f"team_count={_string_value(getattr(report, 'team_count'))} "
            f"pass_count={_string_value(getattr(report, 'pass_count'))} "
            f"watch_count={_string_value(getattr(report, 'watch_count'))} "
            f"blocked_count={_string_value(getattr(report, 'blocked_count'))} "
            f"source_statuses={_source_statuses_value(getattr(report, 'source_statuses'))} "
            "source_config_versions="
            f"{_source_config_versions_value(getattr(report, 'source_config_versions'))} "
            "reason_code_counts="
            f"{_reason_code_counts_value(getattr(report, 'reason_code_counts'))} "
            f"reason_codes={_reason_codes_value(getattr(report, 'reason_codes'))} "
            f"paper_only={_string_value(getattr(report, 'paper_only'))} "
            f"report_only={_string_value(getattr(report, 'report_only'))} "
            f"readonly={_string_value(getattr(report, 'readonly'))}\n"
        )

    module.format_team_memory_readiness_digest_cli_stdout = (
        format_team_memory_readiness_digest_cli_stdout
    )
    monkeypatch.setitem(sys.modules, DIGEST_FORMATTER_MODULE, module)
    return module


def _source_statuses_value(source_statuses: object) -> str:
    if source_statuses is None:
        return "none"
    values = tuple(source_statuses)
    if not values:
        return "none"
    return ",".join(
        f"{row.team_id}:{row.gate_status}:{row.latest_snapshot_age_seconds}:"
        f"{row.source_snapshot_count}/{row.source_required_snapshot_count}"
        for row in values
    )


def _source_config_versions_value(source_config_versions: object) -> str:
    if source_config_versions is None:
        return "none"
    values = tuple(source_config_versions)
    if not values:
        return "none"
    return ",".join(f"{team_id}:{version}" for team_id, version in values)


def _reason_code_counts_value(reason_code_counts: object) -> str:
    if reason_code_counts is None:
        return "none"
    values = tuple(reason_code_counts)
    if not values:
        return "none"
    return ",".join(
        f"{getattr(row, 'reason_code')}:{getattr(row, 'count')}"
        for row in values
    )


def _reason_codes_value(reason_codes: object) -> str:
    if reason_codes is None:
        return "none"
    values = tuple(reason_codes)
    if not values:
        return "none"
    return ",".join(str(reason_code) for reason_code in values)


def _string_value(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


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


def _forbidden_digest_runner(calls: list[str]):
    def runner(*args: object, **kwargs: object) -> object:
        del args, kwargs
        calls.append("digest_runner")
        raise AssertionError(f"{COMMAND} must fail before loading digest")

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
