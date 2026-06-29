from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_strategy_recommendation_reason_trend_config"
ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RECOMMENDATION_REASON_TREND_DB_ENABLED"
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RECOMMENDATION_REASON_TREND_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RECOMMENDATION_REASON_TREND_DB_TABLE"
DEFAULT_TABLE = "strategy_recommendation_reason_trend_reports"
LOCAL_POSTGRESQL_DSN = "postgresql://localhost:54322/postgres"


@pytest.fixture()
def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def _config_class(module: Any) -> type[Any]:
    return module.SupabaseStrategyRecommendationReasonTrendConfig


def _from_env(module: Any, env: dict[str, str]) -> Any:
    return module.from_strategy_recommendation_reason_trend_db_env(env)


def test_public_constants_match_expected_env_surface(module: Any) -> None:
    assert module.STRATEGY_RECOMMENDATION_REASON_TREND_DB_ENABLED_ENV_VAR == ENABLED_ENV_VAR
    assert module.STRATEGY_RECOMMENDATION_REASON_TREND_DB_DSN_ENV_VAR == DSN_ENV_VAR
    assert module.STRATEGY_RECOMMENDATION_REASON_TREND_DB_TABLE_ENV_VAR == TABLE_ENV_VAR
    assert module.DEFAULT_STRATEGY_RECOMMENDATION_REASON_TREND_DB_TABLE == DEFAULT_TABLE
    assert "SupabaseStrategyRecommendationReasonTrendConfig" in module.__all__
    assert "from_strategy_recommendation_reason_trend_db_env" in module.__all__


def test_disabled_env_config_accepts_missing_dsn(module: Any) -> None:
    config = _from_env(module, {})

    assert config == _config_class(module)(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret(module: Any) -> None:
    secret_dsn = "postgresql://sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        _from_env(
            module,
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_enabled_config_requires_dsn_without_echoing_secret(module: Any) -> None:
    secret_dsn = "postgresql://sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        _config_class(module)(
            enabled=True,
            dsn=None,
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message


def test_enabled_env_config_reads_explicit_dsn_at_process_edge(module: Any) -> None:
    dsn = LOCAL_POSTGRESQL_DSN

    config = _from_env(
        module,
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "strategy_reason_trend_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "strategy_reason_trend_archive"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost:54322/postgres",
        "postgres://127.0.0.1:5432/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
    ],
)
def test_config_accepts_local_postgres_dsn_forms(module: Any, dsn: str) -> None:
    config = _config_class(module)(
        enabled=True,
        dsn=dsn,
        table_name=DEFAULT_TABLE,
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://sensitive-token@db.example.com/postgres",
        "postgres://192.168.1.10/postgres",
        "hostaddr=127.0.0.1 password=sensitive-token dbname=postgres",
        "sqlite:///tmp/sensitive-token.db",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    module: Any,
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        _config_class(module)(
            enabled=True,
            dsn=dsn,
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "sensitive-token" not in message


def test_padded_enabled_dsn_is_rejected_without_echoing_secret(module: Any) -> None:
    secret_dsn = "postgresql://sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        _from_env(
            module,
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr(module: Any) -> None:
    config = _config_class(module)(
        enabled=True,
        dsn="postgresql://sensitive-token@localhost:54322/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape(module: Any) -> None:
    rendered = repr(
        _config_class(module)(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


def test_direct_config_rejects_non_string_dsn_without_echoing_value(module: Any) -> None:
    with pytest.raises(ValueError) as exc_info:
        _config_class(module)(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "StrategyReports",
        "strategy-reports",
        "strategy.reports",
        "_strategy_reports",
        "strategy_reports_",
        "",
    ],
)
def test_table_name_must_match_store_simple_lowercase_identifier(
    module: Any,
    table_name: str,
) -> None:
    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        _config_class(module)(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "strategy_recommendation_reason_trend_reports",
        "strategy_1_reason_2_reports",
    ],
)
def test_table_name_accepts_store_simple_lowercase_identifier_values(
    module: Any,
    table_name: str,
) -> None:
    config = _config_class(module)(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name(module: Any) -> None:
    with pytest.raises(ValueError) as exc_info:
        _from_env(
            module,
            {
                TABLE_ENV_VAR: "StrategyReports",
            },
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict(module: Any) -> None:
    with pytest.raises(
        ValueError,
        match=ENABLED_ENV_VAR,
    ):
        _from_env(
            module,
            {
                ENABLED_ENV_VAR: "yes",
                DSN_ENV_VAR: LOCAL_POSTGRESQL_DSN,
            },
        )


def test_direct_config_rejects_non_bool_enabled_flag(module: Any) -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        _config_class(module)(
            enabled=1,
            dsn=LOCAL_POSTGRESQL_DSN,
            table_name=DEFAULT_TABLE,
        )


def test_config_module_has_no_live_driver_or_network_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "supabase_strategy_recommendation_reason_trend_config.py"
    )

    imported_roots = _imported_roots(module_path)

    assert not imported_roots & {
        "aiohttp",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "websocket",
        "websockets",
    }


def _imported_roots(module_path: Path) -> set[str]:
    import ast

    module = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    return imported_roots
