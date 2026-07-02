from __future__ import annotations

import builtins
import inspect
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read import (
    PaperStrategyCandidateResearchQueueReadOptions,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config import (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_team_forecast_config import (
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
)
from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestConfig,
)
from polymarket_alpha_lab.team_research_assignment import (
    TeamResearchAssignmentConfig,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


COMMAND = "team-research-assignment"
ASSIGNMENT_CONFIG_VERSION = "team-research-assignment-v0"
HISTORY_CONFIG_VERSION = "team-diagnostics-snapshot-history-v0"
GATE_CONFIG_VERSION = "team-diagnostics-snapshot-history-gate-v0"
DIGEST_CONFIG_VERSION = "team-memory-readiness-digest-v0"
DB_SOURCE_MODULE = "polymarket_alpha_lab.team_research_assignment_db_source"
GATE_MODULE = "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate"
FORMATTER_MODULE = "polymarket_alpha_lab.team_research_assignment_cli_format"
QUEUE_DSN = "host=localhost port=54322 dbname=queue user=postgres"
ROUTE_DSN = "host=127.0.0.1 port=54323 dbname=routes user=postgres"
SNAPSHOT_DSN = "host=localhost port=54324 dbname=snapshots user=postgres"
QUEUE_TABLE = "paper_strategy_candidate_research_queue_reports_archive"
ROUTE_TABLE = "team_market_routes_archive"
SNAPSHOT_TABLE = "team_diagnostics_snapshot_archive"
REPORT_HASH = "a" * 64
PAYLOAD_HASH = "sensitive-payload-hash"

QUEUE_ENV_VARS = (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
)
ROUTE_ENV_VARS = (
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
)
SNAPSHOT_ENV_VARS = (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)


def test_root_help_lists_team_research_assignment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


def test_team_research_assignment_help_is_env_scoped_read_only_surface(
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
        "--queue-source-config-version",
        "--memory-config-version",
        "--queue-limit",
        "--route-limit",
        "--memory-limit",
    ):
        assert flag in help_text
    assert "--config-version" not in help_text
    assert "--market-slug" not in help_text
    assert "--forecast-id" not in help_text
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


def test_team_research_assignment_main_exposes_runner_injection_parameter() -> None:
    parameter = inspect.signature(main).parameters.get("team_research_assignment_runner")

    assert parameter is not None
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None


@pytest.mark.parametrize(
    ("target", "expected"),
    (
        ("queue_disabled", ("queue", "disabled")),
        ("queue_missing_dsn", ("queue", "dsn")),
        ("route_disabled", ("team forecast", "disabled")),
        ("route_missing_dsn", ("team forecast", "dsn")),
        ("snapshot_disabled", ("snapshot", "disabled")),
        ("snapshot_missing_dsn", ("snapshot", "dsn")),
    ),
)
def test_team_research_assignment_fails_closed_when_required_db_config_unavailable(
    target: str,
    expected: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_all_env(monkeypatch)
    if target == "queue_disabled":
        monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "false")
    elif target == "queue_missing_dsn":
        monkeypatch.delenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR)
    elif target == "route_disabled":
        monkeypatch.setenv(TEAM_FORECAST_DB_ENABLED_ENV_VAR, "false")
    elif target == "route_missing_dsn":
        monkeypatch.delenv(TEAM_FORECAST_DB_DSN_ENV_VAR)
    elif target == "snapshot_disabled":
        monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR, "false")
    elif target == "snapshot_missing_dsn":
        monkeypatch.delenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR)
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_research_assignment_runner=_forbidden_assignment_runner(side_effect_calls),
    )

    assert exit_code == 1
    assert side_effect_calls == []
    assert client_factory_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    for fragment in expected:
        assert fragment in combined.lower()
    for secret in (QUEUE_DSN, ROUTE_DSN, SNAPSHOT_DSN, QUEUE_TABLE, ROUTE_TABLE, SNAPSHOT_TABLE):
        assert secret not in combined
    assert "postgresql://" not in combined


@pytest.mark.parametrize(
    ("flag_name", "bad_value"),
    (
        ("--queue-limit", "0"),
        ("--queue-limit", "-1"),
        ("--route-limit", "0"),
        ("--route-limit", "-1"),
        ("--memory-limit", "0"),
        ("--memory-limit", "-1"),
    ),
)
def test_team_research_assignment_rejects_invalid_limits_before_env_reads(
    flag_name: str,
    bad_value: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_all_env(monkeypatch)
    env_calls: list[str] = []
    side_effect_calls: list[str] = []
    client_factory_calls: list[str] = []

    def forbidden_env() -> object:
        env_calls.append("env")
        raise AssertionError(f"{COMMAND} must reject invalid limits before env reads")

    import polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config as queue_env
    import polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config as snapshot_env
    import polymarket_alpha_lab.supabase_team_forecast_config as route_env

    monkeypatch.setattr(
        queue_env,
        "from_strategy_candidate_research_queue_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(route_env, "from_team_forecast_db_env", forbidden_env)
    monkeypatch.setattr(
        snapshot_env,
        "from_team_diagnostics_snapshot_db_env",
        forbidden_env,
    )
    _install_psycopg_connect_guard(monkeypatch, side_effect_calls)

    exit_code = _invoke_main(
        [COMMAND, flag_name, bad_value],
        client_factory=_forbidden_client_factory(client_factory_calls),
        team_research_assignment_runner=_forbidden_assignment_runner(side_effect_calls),
    )

    assert exit_code == 2
    assert env_calls == []
    assert side_effect_calls == []
    assert client_factory_calls == []
    combined = _combined_output(capsys)
    assert f"{COMMAND}:" in combined
    assert "must be a positive integer" in combined
    for secret in (QUEUE_DSN, ROUTE_DSN, SNAPSHOT_DSN):
        assert secret not in combined


def test_team_research_assignment_injected_runner_receives_env_config_objects_team_ids_and_prints_formatter_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    gate_api = _install_or_get_gate_api(monkeypatch)
    _install_or_get_formatter(monkeypatch)
    _enable_all_env(monkeypatch)
    runner_calls: list[dict[str, object]] = []
    report = _assignment_report()

    def runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        assert kwargs["queue_dsn"] == QUEUE_DSN
        assert kwargs["queue_table_name"] == QUEUE_TABLE
        assert kwargs["route_dsn"] == ROUTE_DSN
        assert kwargs["route_table_name"] == ROUTE_TABLE
        assert kwargs["snapshot_dsn"] == SNAPSHOT_DSN
        assert kwargs["snapshot_table_name"] == SNAPSHOT_TABLE
        assert kwargs["team_ids"] == ("crypto_btc", "macro_rates")
        assert kwargs["queue_source_config_version"] == "queue-source-v1"
        assert kwargs["memory_config_version"] == "memory-v1"
        assert kwargs["queue_limit"] == 2
        assert kwargs["route_limit"] == 17
        assert kwargs["memory_limit"] == 23
        assignment_config = kwargs["assignment_config"]
        assert type(assignment_config) is TeamResearchAssignmentConfig
        assert assignment_config.config_version == ASSIGNMENT_CONFIG_VERSION
        assert assignment_config.paper_only is True
        assert assignment_config.report_only is True
        assert assignment_config.readonly is True
        history_config = kwargs["history_config"]
        assert type(history_config) is TeamDiagnosticsSnapshotHistoryConfig
        assert history_config.config_version == HISTORY_CONFIG_VERSION
        gate_config = kwargs["gate_config"]
        assert type(gate_config) is gate_api.TeamDiagnosticsSnapshotHistoryGateConfig
        assert gate_config.config_version == GATE_CONFIG_VERSION
        digest_config = kwargs["digest_config"]
        assert type(digest_config) is TeamMemoryReadinessDigestConfig
        assert digest_config.config_version == DIGEST_CONFIG_VERSION
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        assert not {
            "dsn",
            "table_name",
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
            "--team-id",
            "crypto_btc",
            "--team-id",
            "macro_rates",
            "--queue-source-config-version",
            "queue-source-v1",
            "--memory-config-version",
            "memory-v1",
            "--queue-limit",
            "2",
            "--route-limit",
            "17",
            "--memory-limit",
            "23",
        ],
        team_research_assignment_runner=runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    assert "assignment_status=ready" in out
    assert "assignment_count=1" in out
    assert "team_summaries=crypto_btc:1:1/0/0:pass:allow" in out
    assert "rows=1:bitcoin-above-120k:crypto_btc:crypto:assigned:allow" in out
    assert "paper_only=True" in out
    assert "report_only=True" in out
    assert "readonly=True" in out
    for secret in (QUEUE_DSN, ROUTE_DSN, SNAPSHOT_DSN, QUEUE_TABLE, ROUTE_TABLE, SNAPSHOT_TABLE):
        assert secret not in out


def test_team_research_assignment_omitted_team_ids_default_to_all_known_teams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_formatter(monkeypatch)
    _enable_all_env(monkeypatch)
    runner_calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        return _assignment_report()

    exit_code = _invoke_main(
        [COMMAND],
        team_research_assignment_runner=runner,
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert runner_calls[0]["team_ids"] == TEAM_IDS


def test_team_research_assignment_default_path_wires_source_loaders_into_db_source_composer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    gate_api = _install_or_get_gate_api(monkeypatch)
    _install_or_get_formatter(monkeypatch)
    _enable_all_env(monkeypatch)
    fake_queue_reports = (object(),)
    fake_route_reports = (object(), object())
    fake_memory_report = object()
    queue_loader_calls: list[dict[str, object]] = []
    route_loader_calls: list[dict[str, object]] = []
    snapshot_loader_calls: list[dict[str, object]] = []
    history_source_calls: list[dict[str, object]] = []
    gate_source_calls: list[dict[str, object]] = []
    memory_source_calls: list[dict[str, object]] = []
    composer_calls: list[dict[str, object]] = []

    import polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read as queue_read
    import polymarket_alpha_lab.team_diagnostics_snapshot_history_db_source as history_source
    import polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_db_source as gate_source
    import polymarket_alpha_lab.team_diagnostics_snapshot_psycopg as snapshot_read
    import polymarket_alpha_lab.team_forecast_psycopg as route_read

    def load_queue(dsn: str, *, options: object) -> tuple[object, ...]:
        queue_loader_calls.append({"dsn": dsn, "options": options})
        assert dsn == QUEUE_DSN
        assert type(options) is PaperStrategyCandidateResearchQueueReadOptions
        assert options.source_config_version == "queue-source-v1"
        assert options.action_status == "research_ready"
        assert options.research_status == "ready"
        assert options.limit == 3
        assert options.table_name == QUEUE_TABLE
        return fake_queue_reports

    def load_routes(
        dsn: str,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[object, ...]:
        route_loader_calls.append(
            {
                "dsn": dsn,
                "team_id": team_id,
                "market_slug": market_slug,
                "limit": limit,
                "table_name": table_name,
            },
        )
        assert dsn == ROUTE_DSN
        assert team_id is None
        assert market_slug is None
        assert limit == 31
        assert table_name == ROUTE_TABLE
        return fake_route_reports

    monkeypatch.setattr(
        queue_read,
        "load_paper_strategy_candidate_research_queue_reports_with_psycopg",
        load_queue,
    )
    monkeypatch.setattr(route_read, "load_team_market_routes_with_psycopg", load_routes)

    def load_snapshots_from_env(*args: object, **kwargs: object) -> tuple[object, ...]:
        assert args == ()
        snapshot_loader_calls.append(kwargs)
        env = kwargs["env"]
        assert isinstance(env, dict)
        assert env[TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR] == "true"
        assert env[TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR] == SNAPSHOT_DSN
        assert env[TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR] == SNAPSHOT_TABLE
        assert kwargs["team_id"] == "crypto_btc"
        assert kwargs["market_slug"] is None
        assert kwargs["forecast_id"] is None
        assert kwargs["config_version"] == "memory-v1"
        assert kwargs["limit"] == 47
        return ()

    def load_history_report(**kwargs: object) -> object:
        history_source_calls.append(kwargs)
        load_snapshots = kwargs["load_snapshots"]
        assert callable(load_snapshots)
        assert type(kwargs["config"]) is TeamDiagnosticsSnapshotHistoryConfig
        assert isinstance(kwargs["generated_at"], datetime)
        assert kwargs["team_id"] == "crypto_btc"
        assert kwargs["market_slug"] is None
        assert kwargs["forecast_id"] is None
        assert kwargs["config_version"] == "memory-v1"
        assert kwargs["limit"] == 47
        load_snapshots(
            team_id=kwargs["team_id"],
            market_slug=kwargs["market_slug"],
            forecast_id=kwargs["forecast_id"],
            config_version=kwargs["config_version"],
            limit=kwargs["limit"],
        )
        return SimpleNamespace(paper_only=True, report_only=True, readonly=True)

    def load_gate_report(**kwargs: object) -> object:
        gate_source_calls.append(kwargs)
        history_loader = kwargs["history_loader"]
        assert callable(history_loader)
        assert kwargs["team_id"] == "crypto_btc"
        assert kwargs["market_slug"] is None
        assert kwargs["forecast_id"] is None
        assert kwargs["config_version"] == "memory-v1"
        assert kwargs["limit"] == 47
        return history_loader(
            history_config=kwargs["history_config"],
            generated_at=kwargs["generated_at"],
            team_id=kwargs["team_id"],
            market_slug=kwargs["market_slug"],
            forecast_id=kwargs["forecast_id"],
            config_version=kwargs["config_version"],
            limit=kwargs["limit"],
        )

    monkeypatch.setattr(
        snapshot_read,
        "load_team_diagnostics_snapshot_reports_from_env",
        load_snapshots_from_env,
    )
    monkeypatch.setattr(
        history_source,
        "load_team_diagnostics_snapshot_history_report",
        load_history_report,
    )
    monkeypatch.setattr(
        gate_source,
        "load_team_diagnostics_snapshot_history_gate_report",
        load_gate_report,
    )

    memory_source_module = ModuleType(
        "polymarket_alpha_lab.team_memory_readiness_digest_db_source",
    )

    def load_team_memory_readiness_digest_report(**kwargs: object) -> object:
        memory_source_calls.append(kwargs)
        assert kwargs["team_ids"] == ("crypto_btc", "macro_rates")
        assert kwargs["config_version"] == "memory-v1"
        assert kwargs["limit"] == 47
        assert type(kwargs["history_config"]) is TeamDiagnosticsSnapshotHistoryConfig
        assert type(kwargs["gate_config"]) is gate_api.TeamDiagnosticsSnapshotHistoryGateConfig
        assert type(kwargs["digest_config"]) is TeamMemoryReadinessDigestConfig
        assert callable(kwargs["gate_loader"])
        assert callable(kwargs["digest_builder"])
        assert isinstance(kwargs["generated_at"], datetime)
        assert kwargs["generated_at"].tzinfo is UTC
        assert (
            kwargs["gate_loader"](
                team_id="crypto_btc",
                history_config=kwargs["history_config"],
                gate_config=kwargs["gate_config"],
                generated_at=kwargs["generated_at"],
                config_version=kwargs["config_version"],
                limit=kwargs["limit"],
            ).paper_only
            is True
        )
        return fake_memory_report

    memory_source_module.load_team_memory_readiness_digest_report = (
        load_team_memory_readiness_digest_report
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_memory_readiness_digest_db_source",
        memory_source_module,
    )

    db_source_module = ModuleType(DB_SOURCE_MODULE)

    def load_team_research_assignment_report(**kwargs: object) -> object:
        from polymarket_alpha_lab.team_research_assignment import (
            build_team_research_assignment_report,
        )

        composer_calls.append(kwargs)
        assert kwargs["team_ids"] == ("crypto_btc", "macro_rates")
        assert kwargs["queue_source_config_version"] == "queue-source-v1"
        assert kwargs["queue_limit"] == 3
        assert kwargs["route_limit"] == 31
        assert kwargs["memory_config_version"] == "memory-v1"
        assert kwargs["memory_limit"] == 47
        assert type(kwargs["assignment_config"]) is TeamResearchAssignmentConfig
        assert kwargs["assignment_builder"] is build_team_research_assignment_report
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        assert kwargs["queue_loader"](
            source_config_version=kwargs["queue_source_config_version"],
            action_status="research_ready",
            research_status="ready",
            limit=kwargs["queue_limit"],
        ) is fake_queue_reports
        assert kwargs["route_loader"](limit=kwargs["route_limit"]) is fake_route_reports
        monkeypatch.setenv(
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
            "host=changed.example.test port=54324 dbname=changed user=postgres",
        )
        monkeypatch.setenv(
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
            "changed_team_diagnostics_snapshot_archive",
        )
        assert (
            kwargs["memory_loader"](
                team_ids=kwargs["team_ids"],
                config_version=kwargs["memory_config_version"],
                limit=kwargs["memory_limit"],
            )
            is fake_memory_report
        )
        return _assignment_report()

    db_source_module.load_team_research_assignment_report = (
        load_team_research_assignment_report
    )
    monkeypatch.setitem(sys.modules, DB_SOURCE_MODULE, db_source_module)

    exit_code = _invoke_main(
        [
            COMMAND,
            "--team-id",
            "crypto_btc",
            "--team-id",
            "macro_rates",
            "--queue-source-config-version",
            "queue-source-v1",
            "--memory-config-version",
            "memory-v1",
            "--queue-limit",
            "3",
            "--route-limit",
            "31",
            "--memory-limit",
            "47",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(composer_calls) == 1
    assert len(queue_loader_calls) == 1
    assert len(route_loader_calls) == 1
    assert len(snapshot_loader_calls) == 1
    assert len(history_source_calls) == 1
    assert len(gate_source_calls) == 1
    assert len(memory_source_calls) == 1
    out = capsys.readouterr().out
    assert out.startswith(f"{COMMAND}:")
    for secret in (QUEUE_DSN, ROUTE_DSN, SNAPSHOT_DSN, QUEUE_TABLE, ROUTE_TABLE, SNAPSHOT_TABLE):
        assert secret not in out


def test_team_research_assignment_runner_failure_redacts_db_and_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_formatter(monkeypatch)
    _enable_all_env(monkeypatch)
    failure_message = (
        f"queue_dsn={QUEUE_DSN} queue_table={QUEUE_TABLE} "
        f"route_dsn={ROUTE_DSN} route_table={ROUTE_TABLE} "
        f"snapshot_dsn={SNAPSHOT_DSN} snapshot_table={SNAPSHOT_TABLE} "
        "queue_host=localhost route_host=127.0.0.1 "
        "market=secret-market market_id=secret-market-id "
        "market_slug=bitcoin-above-120k "
        "marketSlug=camel-case-market "
        "raw_filter=bitcoin-above-120k "
        "rawFilter=raw-filter-secret "
        "question='secret market question' "
        "payload_json={'marketSlug': 'nested-market', 'question': 'nested question'} "
        f"report_sha256={REPORT_HASH} hash={PAYLOAD_HASH} "
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
        [COMMAND, "--team-id", "crypto_btc"],
        team_research_assignment_runner=runner,
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    for secret in (
        QUEUE_DSN,
        ROUTE_DSN,
        SNAPSHOT_DSN,
        QUEUE_TABLE,
        ROUTE_TABLE,
        SNAPSHOT_TABLE,
        "localhost",
        "127.0.0.1",
        "secret-market",
        "secret-market-id",
        "bitcoin-above-120k",
        "camel-case-market",
        "raw-filter-secret",
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


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_research_assignment_rejects_injected_runner_false_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_formatter(monkeypatch)
    _enable_all_env(monkeypatch)
    report = vars(_assignment_report()).copy()
    report[flag_name] = False

    exit_code = _invoke_main(
        [COMMAND],
        team_research_assignment_runner=lambda **_kwargs: SimpleNamespace(**report),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert f"{flag_name} must be True" in combined
    for secret in (QUEUE_DSN, ROUTE_DSN, SNAPSHOT_DSN, QUEUE_TABLE, ROUTE_TABLE, SNAPSHOT_TABLE):
        assert secret not in combined


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_team_research_assignment_rejects_injected_runner_missing_hard_flags(
    flag_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_gate_api(monkeypatch)
    _install_or_get_formatter(monkeypatch)
    _enable_all_env(monkeypatch)
    report = vars(_assignment_report()).copy()
    del report[flag_name]

    exit_code = _invoke_main(
        [COMMAND],
        team_research_assignment_runner=lambda **_kwargs: SimpleNamespace(**report),
    )

    assert exit_code == 1
    combined = _combined_output(capsys)
    assert f"{COMMAND} failed:" in combined
    assert f"{flag_name} must be True" in combined
    for secret in (QUEUE_DSN, ROUTE_DSN, SNAPSHOT_DSN, QUEUE_TABLE, ROUTE_TABLE, SNAPSHOT_TABLE):
        assert secret not in combined


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "host=localhost dbname=queue"],
        [COMMAND, "--table", "paper_strategy_candidate_research_queue_reports"],
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
def test_team_research_assignment_rejects_forbidden_flags(
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls: list[str] = []

    def forbidden_env() -> object:
        env_calls.append("env")
        raise AssertionError(f"{COMMAND} must reject forbidden flags before env reads")

    import polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config as queue_env
    import polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config as snapshot_env
    import polymarket_alpha_lab.supabase_team_forecast_config as route_env

    monkeypatch.setattr(
        queue_env,
        "from_strategy_candidate_research_queue_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(route_env, "from_team_forecast_db_env", forbidden_env)
    monkeypatch.setattr(
        snapshot_env,
        "from_team_diagnostics_snapshot_db_env",
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
        ([COMMAND, "--unknown-api-key", "super-secret-api-key"], "super-secret-api-key"),
    ),
)
def test_team_research_assignment_rejects_secret_like_args_without_echoing_values(
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


@pytest.mark.parametrize(
    ("flag_name", "bad_value", "forbidden_fragments"),
    (
        (
            "--queue-limit",
            "postgresql://user:pass@localhost:5432/db",
            ("postgresql://user:pass@localhost:5432/db", "user:pass", "localhost"),
        ),
        (
            "--route-limit",
            REPORT_HASH,
            (REPORT_HASH,),
        ),
        (
            "--memory-limit",
            "api_key=super-secret",
            ("api_key=super-secret", "super-secret"),
        ),
    ),
)
def test_team_research_assignment_limit_parse_errors_do_not_echo_sensitive_values(
    flag_name: str,
    bad_value: str,
    forbidden_fragments: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls: list[str] = []

    def forbidden_env() -> object:
        env_calls.append("env")
        raise AssertionError(f"{COMMAND} must reject invalid limits before env reads")

    import polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config as queue_env
    import polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config as snapshot_env
    import polymarket_alpha_lab.supabase_team_forecast_config as route_env

    monkeypatch.setattr(
        queue_env,
        "from_strategy_candidate_research_queue_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(route_env, "from_team_forecast_db_env", forbidden_env)
    monkeypatch.setattr(
        snapshot_env,
        "from_team_diagnostics_snapshot_db_env",
        forbidden_env,
    )

    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag_name, bad_value])

    assert exc_info.value.code == 2
    assert env_calls == []
    err = capsys.readouterr().err
    assert "must be a positive integer" in err
    for fragment in forbidden_fragments:
        assert fragment not in err


def _assignment_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        config_version=ASSIGNMENT_CONFIG_VERSION,
        source_queue_config_version="queue-source-v1",
        source_route_config_version="team-router-v0",
        source_memory_config_version=DIGEST_CONFIG_VERSION,
        assignment_status="ready",
        recommended_next_step="dispatch_team_research",
        assignment_count=1,
        assigned_count=1,
        watch_count=0,
        blocked_count=0,
        team_summaries=(
            SimpleNamespace(
                team_id="crypto_btc",
                assignment_count=1,
                assigned_count=1,
                watch_count=0,
                blocked_count=0,
                memory_readiness_status="pass",
                memory_use_policy="allow",
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        ),
        rows=(
            SimpleNamespace(
                research_rank=1,
                market_slug="bitcoin-above-120k",
                question="Will bitcoin be above 120k?",
                selected_side="yes",
                scoring_side="yes",
                team_id="crypto_btc",
                category_id="crypto",
                routing_confidence="0.900000",
                secondary_team_ids=(),
                queue_research_status="ready",
                queue_research_bucket="high_priority",
                queue_readiness_status="ready",
                memory_readiness_status="pass",
                memory_use_policy="allow",
                assignment_status="assigned",
                assignment_reason_codes=("assignment_ready",),
                evidence_gap_codes=(),
                source_reason_codes=("queue_ready",),
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        ),
        reason_codes=("team_research_assignment_ready",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _install_or_get_gate_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return sys.modules[GATE_MODULE]
    except KeyError:
        pass
    try:
        return __import__(GATE_MODULE, fromlist=("unused",))
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


def _install_or_get_formatter(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return sys.modules[FORMATTER_MODULE]
    except KeyError:
        pass
    try:
        return __import__(FORMATTER_MODULE, fromlist=("unused",))
    except ModuleNotFoundError as exc:
        if exc.name != FORMATTER_MODULE:
            raise

    module = ModuleType(FORMATTER_MODULE)

    def format_team_research_assignment_cli_stdout(report: object) -> str:
        return (
            f"{COMMAND}: "
            f"assignment_status={_string_value(getattr(report, 'assignment_status'))} "
            "recommended_next_step="
            f"{_string_value(getattr(report, 'recommended_next_step'))} "
            f"assignment_count={_string_value(getattr(report, 'assignment_count'))} "
            f"assigned_count={_string_value(getattr(report, 'assigned_count'))} "
            f"watch_count={_string_value(getattr(report, 'watch_count'))} "
            f"blocked_count={_string_value(getattr(report, 'blocked_count'))} "
            f"team_summaries={_team_summaries_value(getattr(report, 'team_summaries'))} "
            f"rows={_rows_value(getattr(report, 'rows'))} "
            f"reason_codes={_reason_codes_value(getattr(report, 'reason_codes'))} "
            f"paper_only={_string_value(getattr(report, 'paper_only'))} "
            f"report_only={_string_value(getattr(report, 'report_only'))} "
            f"readonly={_string_value(getattr(report, 'readonly'))}\n"
        )

    module.format_team_research_assignment_cli_stdout = (
        format_team_research_assignment_cli_stdout
    )
    monkeypatch.setitem(sys.modules, FORMATTER_MODULE, module)
    return module


def _team_summaries_value(team_summaries: object) -> str:
    values = tuple(team_summaries)
    if not values:
        return "none"
    return ",".join(
        f"{summary.team_id}:{summary.assignment_count}:"
        f"{summary.assigned_count}/{summary.watch_count}/{summary.blocked_count}:"
        f"{summary.memory_readiness_status}:{summary.memory_use_policy}"
        for summary in values
    )


def _rows_value(rows: object) -> str:
    values = tuple(rows)
    if not values:
        return "none"
    return ",".join(
        f"{row.research_rank}:{row.market_slug}:{row.team_id}:"
        f"{row.category_id}:{row.assignment_status}:{row.memory_use_policy}"
        for row in values
    )


def _reason_codes_value(reason_codes: object) -> str:
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


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in QUEUE_ENV_VARS + ROUTE_ENV_VARS + SNAPSHOT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _enable_all_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, QUEUE_DSN)
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
        QUEUE_TABLE,
    )
    monkeypatch.setenv(TEAM_FORECAST_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(TEAM_FORECAST_DB_DSN_ENV_VAR, ROUTE_DSN)
    monkeypatch.setenv(TEAM_ROUTE_DB_TABLE_ENV_VAR, ROUTE_TABLE)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR, SNAPSHOT_DSN)
    monkeypatch.setenv(TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR, SNAPSHOT_TABLE)


def _forbidden_client_factory(calls: list[str]):
    def factory() -> object:
        calls.append("client_factory")
        raise AssertionError(f"{COMMAND} must not build a market client")

    return factory


def _forbidden_assignment_runner(calls: list[str]):
    def runner(*args: object, **kwargs: object) -> object:
        del args, kwargs
        calls.append("assignment_runner")
        raise AssertionError(f"{COMMAND} must fail before loading assignment")

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
