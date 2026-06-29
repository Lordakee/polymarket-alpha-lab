from __future__ import annotations

from dataclasses import FrozenInstanceError
import ast
import importlib
from pathlib import Path
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_paper_recommendation_consistency_config"
ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_CONSISTENCY_DB_ENABLED"
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_CONSISTENCY_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_CONSISTENCY_DB_TABLE"
DEFAULT_TABLE = "paper_recommendation_consistency_reports"
LOCAL_SUPABASE_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


@pytest.fixture()
def module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def test_public_constants_match_expected_env_surface(module: ModuleType) -> None:
    assert module.PAPER_RECOMMENDATION_CONSISTENCY_DB_ENABLED_ENV_VAR == ENABLED_ENV_VAR
    assert module.PAPER_RECOMMENDATION_CONSISTENCY_DB_DSN_ENV_VAR == DSN_ENV_VAR
    assert module.PAPER_RECOMMENDATION_CONSISTENCY_DB_TABLE_ENV_VAR == TABLE_ENV_VAR
    assert module.DEFAULT_PAPER_RECOMMENDATION_CONSISTENCY_DB_TABLE == DEFAULT_TABLE
    assert "SupabasePaperRecommendationConsistencyConfig" in module.__all__
    assert "from_paper_recommendation_consistency_db_env" in module.__all__


def test_disabled_env_config_accepts_missing_dsn(module: ModuleType) -> None:
    config = module.from_paper_recommendation_consistency_db_env({})

    assert config == module.SupabasePaperRecommendationConsistencyConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret(
    module: ModuleType,
) -> None:
    secret_dsn = "postgresql://postgres:sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_recommendation_consistency_db_env(
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


def test_enabled_config_requires_dsn_without_echoing_secret(
    module: ModuleType,
) -> None:
    secret_dsn = "postgresql://postgres:sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperRecommendationConsistencyConfig(
            enabled=True,
            dsn=None,
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message


def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    module: ModuleType,
) -> None:
    dsn = LOCAL_SUPABASE_DSN

    config = module.from_paper_recommendation_consistency_db_env(
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "paper_recommendation_consistency_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_recommendation_consistency_archive"


def test_padded_enabled_dsn_is_rejected_without_echoing_secret(
    module: ModuleType,
) -> None:
    secret_dsn = "postgresql://postgres:sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_recommendation_consistency_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgres://postgres:postgres@127.0.0.1:54322/postgres",
        "postgresql://postgres:postgres@[::1]:54322/postgres",
        "host=localhost port=54322 dbname=postgres user=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=/var/run/postgresql dbname=postgres user=postgres",
    ],
)
def test_enabled_env_config_accepts_local_postgres_dsns(
    module: ModuleType,
    dsn: str,
) -> None:
    config = module.from_paper_recommendation_consistency_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: dsn,
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == DEFAULT_TABLE


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:super-secret@hosted.example.invalid:5432/postgres",
        "postgres://postgres:super-secret@192.168.1.10:5432/postgres",
        "host=hosted.example.invalid dbname=postgres password=super-secret",
        "postgresql:///postgres?hostaddr=127.0.0.1",
        "postgresql:///postgres?service=local-supabase",
        "hostaddr=127.0.0.1 dbname=postgres password=super-secret",
        "service=local-supabase password=super-secret",
    ],
)
def test_enabled_env_config_rejects_remote_or_unsafe_dsns_without_echoing_secret(
    module: ModuleType,
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        module.from_paper_recommendation_consistency_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "hosted.example.invalid" not in message
    assert "192.168.1.10" not in message
    assert "super-secret" not in message


def test_config_is_frozen_and_masks_dsn_in_repr(module: ModuleType) -> None:
    config = module.SupabasePaperRecommendationConsistencyConfig(
        enabled=True,
        dsn="postgresql://postgres:sensitive-token@localhost:54322/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape(
    module: ModuleType,
) -> None:
    rendered = repr(
        module.SupabasePaperRecommendationConsistencyConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


def test_direct_config_rejects_non_string_dsn_without_echoing_value(
    module: ModuleType,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperRecommendationConsistencyConfig(
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
    table_name: str,
) -> None:
    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        module.SupabasePaperRecommendationConsistencyConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_recommendation_consistency_reports",
        "paper_1_recommendation_2_reports",
    ],
)
def test_table_name_accepts_store_simple_lowercase_identifier_values(
    module: ModuleType,
    table_name: str,
) -> None:
    config = module.SupabasePaperRecommendationConsistencyConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name(module: ModuleType) -> None:
    with pytest.raises(ValueError) as exc_info:
        module.from_paper_recommendation_consistency_db_env(
            {
                TABLE_ENV_VAR: "PaperReports",
            },
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict(module: ModuleType) -> None:
    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        module.from_paper_recommendation_consistency_db_env(
            {
                ENABLED_ENV_VAR: "yes",
                DSN_ENV_VAR: LOCAL_SUPABASE_DSN,
            },
        )


def test_direct_config_rejects_non_bool_enabled_flag(module: ModuleType) -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperRecommendationConsistencyConfig(
            enabled=1,
            dsn=LOCAL_SUPABASE_DSN,
            table_name=DEFAULT_TABLE,
        )


def test_config_module_has_no_live_driver_or_network_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "supabase_paper_recommendation_consistency_config.py"
    )

    module = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

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
