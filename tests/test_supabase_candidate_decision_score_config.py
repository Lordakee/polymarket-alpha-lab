from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from importlib import import_module
import inspect

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_candidate_decision_score_config"


def _load_module():
    return import_module(MODULE_NAME)


def test_constants_use_candidate_decision_score_env_names() -> None:
    module = _load_module()

    assert (
        module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_CANDIDATE_DECISION_SCORE_DB_ENABLED"
    )
    assert (
        module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_CANDIDATE_DECISION_SCORE_DB_DSN"
    )
    assert (
        module.CANDIDATE_DECISION_SCORE_DB_TABLE_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_CANDIDATE_DECISION_SCORE_DB_TABLE"
    )
    assert (
        module.DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE
        == "candidate_decision_score_reports"
    )


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    module = _load_module()

    config = module.from_candidate_decision_score_db_env({})

    assert config == module.SupabaseCandidateDecisionScoreConfig(
        enabled=False,
        dsn=None,
        table=module.DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _load_module()
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_candidate_decision_score_db_env(
            {
                module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": unrelated_secret,
            },
        )

    message = str(exc_info.value)
    assert module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_accepts_local_dsn_and_schema_qualified_table() -> None:
    module = _load_module()
    dsn = "postgresql://user:secret@localhost:54322/postgres"

    config = module.from_candidate_decision_score_db_env(
        {
            module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR: "true",
            module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR: dsn,
            module.CANDIDATE_DECISION_SCORE_DB_TABLE_ENV_VAR: (
                "audit.candidate_decision_score_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table == "audit.candidate_decision_score_reports"


def test_enabled_env_config_rejects_remote_dsn_without_echoing_secret() -> None:
    module = _load_module()
    secret_dsn = "postgresql://user:topsecret@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_candidate_decision_score_db_env(
            {
                module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR: "1",
                module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message
    assert "example.invalid" not in message


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        ("1", True),
        ("true", True),
    ],
)
def test_enabled_env_config_accepts_only_strict_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    module = _load_module()
    env = {
        module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR: enabled_value,
        module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR: (
            "postgresql://user:secret@localhost:54322/postgres"
        ),
    }

    config = module.from_candidate_decision_score_db_env(env)

    assert config.enabled is expected_enabled


@pytest.mark.parametrize(
    "enabled_value",
    [" TRUE ", "FALSE", "yes", "on", "2", True, 1],
)
def test_enabled_env_config_rejects_non_strict_values(enabled_value: object) -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_candidate_decision_score_db_env(
            {
                module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR: enabled_value,
                module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR: (
                    "postgresql://user:secret@localhost:54322/postgres"
                ),
            },
        )

    assert module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR in str(exc_info.value)


def test_enabled_env_config_rejects_padded_dsn_without_echoing_it() -> None:
    module = _load_module()
    secret_dsn = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_candidate_decision_score_db_env(
            {
                module.CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR: "true",
                module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message


@pytest.mark.parametrize(
    "table",
    [
        "a0",
        "candidate_decision_score_reports",
        "candidate_decision_score_1_reports",
        "public.candidate_decision_score_reports",
        "audit.candidate_decision_score_reports",
    ],
)
def test_table_accepts_lowercase_identifier_with_optional_schema(table: str) -> None:
    module = _load_module()

    config = module.SupabaseCandidateDecisionScoreConfig(
        enabled=False,
        dsn=None,
        table=table,
    )

    assert config.table == table


@pytest.mark.parametrize(
    "table",
    [
        "",
        " ",
        "CandidateDecisionScoreReports",
        "candidate-decision-score-reports",
        "_candidate_decision_score_reports",
        "candidate_decision_score_reports_",
        "public.audit.candidate_decision_score_reports",
        '"candidate_decision_score_reports"',
        "public.\"candidate_decision_score_reports\"",
        "candidate_decision_score_reports;drop table fills",
        "candidate_decision_score_reports drop table fills",
        "candidate_decision_score_reports--",
        "candidate_decision_score_reports/*comment*/",
    ],
)
def test_table_rejects_unsafe_blank_quoted_or_injection_strings(table: str) -> None:
    module = _load_module()

    with pytest.raises(
        ValueError,
        match="table must be a lowercase identifier with optional schema prefix",
    ):
        module.SupabaseCandidateDecisionScoreConfig(
            enabled=False,
            dsn=None,
            table=table,
        )


def test_env_table_error_mentions_variable_name() -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_candidate_decision_score_db_env(
            {
                module.CANDIDATE_DECISION_SCORE_DB_TABLE_ENV_VAR: (
                    "candidate_decision_score_reports;drop table fills"
                ),
            },
        )

    assert module.CANDIDATE_DECISION_SCORE_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _load_module()
    config = module.SupabaseCandidateDecisionScoreConfig(
        enabled=True,
        dsn="postgresql://topsecret@localhost:54322/postgres",
        table=module.DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered
    assert "table='candidate_decision_score_reports'" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    module = _load_module()

    rendered = repr(
        module.SupabaseCandidateDecisionScoreConfig(
            enabled=False,
            dsn=None,
            table=module.DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabaseCandidateDecisionScoreConfig(
            enabled=1,
            dsn="postgresql://user:secret@localhost:54322/postgres",
            table=module.DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabaseCandidateDecisionScoreConfig(
            enabled=True,
            dsn=object(),
            table=module.DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader() -> None:
    module = _load_module()

    assert module.__all__ == (
        "CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR",
        "CANDIDATE_DECISION_SCORE_DB_ENABLED_ENV_VAR",
        "CANDIDATE_DECISION_SCORE_DB_TABLE_ENV_VAR",
        "DEFAULT_CANDIDATE_DECISION_SCORE_DB_TABLE",
        "SupabaseCandidateDecisionScoreConfig",
        "from_candidate_decision_score_db_env",
    )


def test_module_has_no_db_cli_network_or_file_io_surface() -> None:
    module = _load_module()
    tree = ast.parse(inspect.getsource(module))
    forbidden_import_fragments = (
        "cli",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "read",
        "request",
        "run",
        "write",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
