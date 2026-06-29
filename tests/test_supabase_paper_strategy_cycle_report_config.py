from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_paper_strategy_cycle_report_config"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_strategy_cycle_report_config.py"
)
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def _load_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} should exist")
        raise


def test_disabled_env_config_accepts_missing_dsn_and_uses_default_table() -> None:
    module = _load_module()

    config = module.from_paper_strategy_cycle_report_db_env({})

    assert config == module.SupabasePaperStrategyCycleReportConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
    )
    assert config.table_name == "paper_strategy_cycle_reports"


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_accepts_explicit_true_values(enabled_value: str) -> None:
    module = _load_module()

    config = module.from_paper_strategy_cycle_report_db_env(
        {
            module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            module.PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE_ENV_VAR: (
                "paper_strategy_cycle_report_archive"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_POSTGRES_DSN
    assert config.table_name == "paper_strategy_cycle_report_archive"


@pytest.mark.parametrize("enabled_value", ["", "0", "false", " FALSE "])
def test_enabled_env_config_accepts_explicit_false_values(enabled_value: str) -> None:
    module = _load_module()

    config = module.from_paper_strategy_cycle_report_db_env(
        {
            module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR: enabled_value,
        },
    )

    assert config.enabled is False
    assert config.dsn is None


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2", "truthy"])
def test_enabled_env_config_rejects_invalid_enabled_values(enabled_value: str) -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_strategy_cycle_report_db_env(
            {
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR: enabled_value,
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR in message
    assert enabled_value not in message


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgres://postgres:postgres@127.0.0.1:54322/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=/var/run/postgresql dbname=postgres",
    ],
)
def test_config_accepts_local_postgres_dsn_shapes(dsn: str) -> None:
    module = _load_module()

    config = module.SupabasePaperStrategyCycleReportConfig(
        enabled=False,
        dsn=dsn,
        table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
    )

    assert config.dsn == dsn


def test_config_validates_dsn_with_strategy_cycle_report_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    calls: list[tuple[str, str]] = []

    def validate_spy(value: str, *, env_var_name: str) -> None:
        calls.append((value, env_var_name))

    monkeypatch.setattr(module, "validate_local_postgres_dsn", validate_spy)

    config = module.SupabasePaperStrategyCycleReportConfig(
        enabled=False,
        dsn=LOCAL_POSTGRES_DSN,
        table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
    )

    assert config.dsn == LOCAL_POSTGRES_DSN
    assert calls == [
        (LOCAL_POSTGRES_DSN, module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR),
    ]


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://topsecret@example.invalid/postgres",
        "postgres://db.example.com/postgres",
        "postgresql://localhost:54322/postgres?hostaddr=127.0.0.1",
        "host=example.invalid dbname=postgres",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    dsn: str,
) -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperStrategyCycleReportConfig(
            enabled=False,
            dsn=dsn,
            table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


@pytest.mark.parametrize(
    "dsn_value",
    [
        None,
        "",
        " ",
        "\t\n",
        " postgresql://sensitive-token:postgres@localhost:54322/postgres ",
    ],
)
def test_dsn_normalizes_missing_blank_or_padded_values_to_none(
    dsn_value: str | None,
) -> None:
    module = _load_module()

    config = module.SupabasePaperStrategyCycleReportConfig(
        enabled=False,
        dsn=dsn_value,
        table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
    )

    assert config.dsn is None


@pytest.mark.parametrize("dsn_value", [None, "", " ", "\t\n"])
def test_enabled_config_requires_dsn_without_echoing_secret(
    dsn_value: str | None,
) -> None:
    module = _load_module()
    secret_dsn = "postgresql://sensitive-token:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_strategy_cycle_report_db_env(
            {
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR: dsn_value,
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_padded_enabled_dsn_is_rejected_without_echoing_secret() -> None:
    module = _load_module()
    secret_dsn = "postgresql://sensitive-token:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_strategy_cycle_report_db_env(
            {
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _load_module()

    config = module.SupabasePaperStrategyCycleReportConfig(
        enabled=True,
        dsn="postgresql://sensitive-token:postgres@localhost:54322/postgres",
        table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    module = _load_module()

    rendered = repr(
        module.SupabasePaperStrategyCycleReportConfig(
            enabled=False,
            dsn=None,
            table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperStrategyCycleReports",
        "paper-strategy-cycle-reports",
        "paper.strategy_cycle_reports",
        "_paper_strategy_cycle_reports",
        "paper_strategy_cycle_reports_",
        "",
    ],
)
def test_table_name_must_match_simple_lowercase_identifier(
    table_name: str,
) -> None:
    module = _load_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a simple lowercase identifier",
    ):
        module.SupabasePaperStrategyCycleReportConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_strategy_cycle_reports",
        "paper_1_strategy_2_cycle_reports",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    module = _load_module()

    config = module.SupabasePaperStrategyCycleReportConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name_without_echoing_secret() -> None:
    module = _load_module()
    invalid_table_name = "PaperStrategyCycleReports"
    secret_dsn = "postgresql://sensitive-token:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_strategy_cycle_report_db_env(
            {
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR: secret_dsn,
                module.PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE_ENV_VAR: invalid_table_name,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE_ENV_VAR in message
    assert invalid_table_name not in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperStrategyCycleReportConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=LOCAL_POSTGRES_DSN,
            table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperStrategyCycleReportConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_module_exports_only_public_config_api() -> None:
    module = _load_module()

    assert module.__all__ == (
        "PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR",
        "PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR",
        "PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE_ENV_VAR",
        "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE",
        "SupabasePaperStrategyCycleReportConfig",
        "from_paper_strategy_cycle_report_db_env",
    )


def test_module_scope_does_not_import_live_api_auth_or_order_modules() -> None:
    assert MODULE_PATH.exists()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "os",
        "re",
        "typing",
        "polymarket_alpha_lab.supabase_local_dsn",
    }
    forbidden_fragments = ("api", "auth", "broker", "client", "order", "wallet")
    assert not {
        imported_module
        for imported_module in imported_modules
        if any(fragment in imported_module.lower() for fragment in forbidden_fragments)
    }


def test_loader_uses_process_environment_when_env_is_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    monkeypatch.setenv(module.PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(
        module.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR,
        LOCAL_POSTGRES_DSN,
    )
    monkeypatch.setenv(
        module.PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE_ENV_VAR,
        "paper_strategy_cycle_report_env",
    )

    config = module.from_paper_strategy_cycle_report_db_env()

    assert config == module.SupabasePaperStrategyCycleReportConfig(
        enabled=True,
        dsn=LOCAL_POSTGRES_DSN,
        table_name="paper_strategy_cycle_report_env",
    )
