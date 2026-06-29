from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


PROBABILITY_MODULE_NAME = (
    "polymarket_alpha_lab.supabase_paper_probability_recommendation_queue_config"
)
RISK_BUDGET_MODULE_NAME = (
    "polymarket_alpha_lab.supabase_paper_recommendation_risk_budget_config"
)


@pytest.fixture(
    params=[
        pytest.param(
            {
                "module_name": PROBABILITY_MODULE_NAME,
                "enabled_env_var": "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_ENABLED",
                "dsn_env_var": "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN",
                "table_env_var": "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_TABLE",
                "default_table": "paper_probability_recommendation_queue_reports",
                "config_name": "SupabasePaperProbabilityRecommendationQueueConfig",
                "factory_name": "from_paper_probability_recommendation_queue_db_env",
            },
            id="probability-recommendation-queue",
        ),
        pytest.param(
            {
                "module_name": RISK_BUDGET_MODULE_NAME,
                "enabled_env_var": "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_RISK_BUDGET_DB_ENABLED",
                "dsn_env_var": "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_RISK_BUDGET_DB_DSN",
                "table_env_var": "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_RISK_BUDGET_DB_TABLE",
                "default_table": "paper_recommendation_risk_budget_reports",
                "config_name": "SupabasePaperRecommendationRiskBudgetConfig",
                "factory_name": "from_paper_recommendation_risk_budget_db_env",
            },
            id="recommendation-risk-budget",
        ),
    ],
)
def surface(request: pytest.FixtureRequest) -> dict[str, Any]:
    return request.param


@pytest.fixture
def module(surface: dict[str, Any]) -> ModuleType:
    return importlib.import_module(surface["module_name"])


def test_public_constants_match_expected_env_surface(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    assert module.__dict__[f"{_prefix(surface)}_DB_ENABLED_ENV_VAR"] == surface["enabled_env_var"]
    assert module.__dict__[f"{_prefix(surface)}_DB_DSN_ENV_VAR"] == surface["dsn_env_var"]
    assert module.__dict__[f"{_prefix(surface)}_DB_TABLE_ENV_VAR"] == surface["table_env_var"]
    assert module.__dict__[f"DEFAULT_{_prefix(surface)}_DB_TABLE"] == surface["default_table"]
    assert surface["config_name"] in module.__all__
    assert surface["factory_name"] in module.__all__


def test_disabled_env_config_accepts_missing_dsn(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    config = _from_env(module, surface, {})

    assert config == _config_class(module, surface)(
        enabled=False,
        dsn=None,
        table_name=surface["default_table"],
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    secret_dsn = "postgresql://sensitive-token@localhost/postgres"

    with pytest.raises(ValueError) as exc_info:
        _from_env(
            module,
            surface,
            {
                surface["enabled_env_var"]: "true",
                surface["dsn_env_var"]: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert surface["dsn_env_var"] in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_enabled_config_requires_dsn_without_echoing_secret(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    secret_dsn = "postgresql://sensitive-token@localhost/postgres"

    with pytest.raises(ValueError) as exc_info:
        _config_class(module, surface)(
            enabled=True,
            dsn=None,
            table_name=surface["default_table"],
        )

    message = str(exc_info.value)
    assert surface["dsn_env_var"] in message
    assert secret_dsn not in message


def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    dsn = "postgresql://localhost/postgres"

    config = _from_env(
        module,
        surface,
        {
            surface["enabled_env_var"]: "1",
            surface["dsn_env_var"]: dsn,
            surface["table_env_var"]: "paper_recommendation_reports",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_recommendation_reports"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost/postgres",
        "postgres://localhost:54322/postgres",
        "postgresql://user:password@127.0.0.1:5432/postgres",
        "postgresql://user:password@[::1]:5432/postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=localhost port=54322 dbname=postgres",
        "host=/var/run/postgresql dbname=postgres",
    ],
)
def test_direct_config_accepts_local_postgres_dsn_forms(
    module: ModuleType,
    surface: dict[str, Any],
    dsn: str,
) -> None:
    config = _config_class(module, surface)(
        enabled=True,
        dsn=dsn,
        table_name=surface["default_table"],
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://example.invalid/postgres",
        "postgresql://user:sensitive-token@example.invalid/postgres",
        "postgres://db.example.com/postgres",
        "postgresql://192.168.1.10/postgres",
        "postgresql://localhost:70000/postgres",
        "postgresql:///postgres",
        "postgresql://localhost/postgres?host=localhost",
        "postgresql://localhost/postgres?hostaddr=127.0.0.1",
        "postgresql://localhost/postgres?service=local",
        "host=example.invalid dbname=postgres",
        "host=localhost,example.invalid dbname=postgres",
        "hostaddr=127.0.0.1 dbname=postgres",
        "service=local",
        "sqlite:///tmp/project.db",
    ],
)
def test_disabled_config_rejects_remote_or_unsafe_dsn_without_echoing_value(
    module: ModuleType,
    surface: dict[str, Any],
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        _config_class(module, surface)(
            enabled=False,
            dsn=dsn,
            table_name=surface["default_table"],
        )

    message = str(exc_info.value)
    assert surface["dsn_env_var"] in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "sensitive-token" not in message


def test_padded_enabled_dsn_is_rejected_without_echoing_secret(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    secret_dsn = "postgresql://sensitive-token@localhost/postgres"

    with pytest.raises(ValueError) as exc_info:
        _from_env(
            module,
            surface,
            {
                surface["enabled_env_var"]: "true",
                surface["dsn_env_var"]: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert surface["dsn_env_var"] in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    config = _config_class(module, surface)(
        enabled=True,
        dsn="postgresql://sensitive-token@localhost/postgres",
        table_name=surface["default_table"],
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    rendered = repr(
        _config_class(module, surface)(
            enabled=False,
            dsn=None,
            table_name=surface["default_table"],
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


def test_direct_config_rejects_non_string_dsn_without_echoing_value(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    with pytest.raises(ValueError) as exc_info:
        _config_class(module, surface)(
            enabled=True,
            dsn=object(),
            table_name=surface["default_table"],
        )

    message = str(exc_info.value)
    assert surface["dsn_env_var"] in message
    assert "object at 0x" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper.reports",
        "_paper_reports",
        "paper_reports_",
        "",
    ],
)
def test_table_name_must_match_store_simple_lowercase_identifier(
    module: ModuleType,
    surface: dict[str, Any],
    table_name: str,
) -> None:
    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        _config_class(module, surface)(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_probability_recommendation_queue_reports",
        "paper_recommendation_risk_budget_reports",
        "paper_1_recommendation_2_reports",
    ],
)
def test_table_name_accepts_store_simple_lowercase_identifier_values(
    module: ModuleType,
    surface: dict[str, Any],
    table_name: str,
) -> None:
    config = _config_class(module, surface)(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    with pytest.raises(ValueError) as exc_info:
        _from_env(
            module,
            surface,
            {
                surface["table_env_var"]: "PaperReports",
            },
        )

    assert surface["table_env_var"] in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match=surface["enabled_env_var"]):
        _from_env(
            module,
            surface,
            {
                surface["enabled_env_var"]: "yes",
                surface["dsn_env_var"]: "postgresql://localhost/postgres",
            },
        )


def test_direct_config_rejects_non_bool_enabled_flag(
    module: ModuleType,
    surface: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        _config_class(module, surface)(
            enabled=1,
            dsn="postgresql://localhost/postgres",
            table_name=surface["default_table"],
        )


def test_config_module_has_no_live_driver_or_network_imports(surface: dict[str, Any]) -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / f"{surface['module_name'].rsplit('.', 1)[1]}.py"
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


def _prefix(surface: dict[str, Any]) -> str:
    if surface["module_name"] == PROBABILITY_MODULE_NAME:
        return "PAPER_PROBABILITY_RECOMMENDATION_QUEUE"
    return "PAPER_RECOMMENDATION_RISK_BUDGET"


def _config_class(module: ModuleType, surface: dict[str, Any]) -> type[Any]:
    return module.__dict__[surface["config_name"]]


def _from_env(
    module: ModuleType,
    surface: dict[str, Any],
    env: dict[str, str],
) -> Any:
    return module.__dict__[surface["factory_name"]](env)


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
