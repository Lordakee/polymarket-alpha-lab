from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_autonomous_screening_decision_support_gate_transition_trend_config.py"
)
DEFAULT_TABLE = "paper_autonomous_screening_gate_transition_trend_reports"
LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_GATE_TRANSITION_TREND_DB_ENABLED"
)
DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_GATE_TRANSITION_TREND_DB_DSN"
)
TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_GATE_TRANSITION_TREND_DB_TABLE"
)


def _config_module():
    import polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_transition_trend_config as config_module

    return config_module


def test_trend_config_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_store import (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_trend_config_disabled_env_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {},
        )
    )

    assert config == (
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionTrendConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        )
    )


def test_trend_config_enabled_env_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_trend_config_reads_explicit_dsn_at_process_edge() -> None:
    config_module = _config_module()

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {
                ENABLED_ENV_VAR: "1",
                DSN_ENV_VAR: LOCAL_DSN,
                TABLE_ENV_VAR: "paper_autonomous_screening_gate_transition_trend_archive",
            },
        )
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_DSN
    assert config.table_name == "paper_autonomous_screening_gate_transition_trend_archive"


def test_trend_config_rejects_remote_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://worker:sensitive-token@db.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {
                ENABLED_ENV_VAR: "false",
                DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message
    assert "secret" not in message.lower()


def test_trend_config_validates_dsn_with_trend_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_module = _config_module()
    calls: list[tuple[str, str]] = []

    def validate_spy(value: str, *, env_var_name: str) -> None:
        calls.append((value, env_var_name))

    monkeypatch.setattr(config_module, "validate_local_postgres_dsn", validate_spy)

    config = config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionTrendConfig(
        enabled=False,
        dsn=LOCAL_DSN,
        table_name=DEFAULT_TABLE,
    )

    assert config.dsn == LOCAL_DSN
    assert calls == [(LOCAL_DSN, DSN_ENV_VAR)]


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        (" FALSE ", False),
        ("1", True),
        ("true", True),
        (" TRUE ", True),
    ],
)
def test_trend_config_accepts_only_strict_enabled_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    config_module = _config_module()

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_DSN,
            },
        )
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_trend_config_rejects_non_strict_enabled_values(
    enabled_value: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_DSN,
            },
        )


def test_trend_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionTrendConfig(
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
    assert DEFAULT_TABLE in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper.reports",
        "_paper_reports",
        "paper_reports_",
        "a",
        "",
    ],
)
def test_trend_config_table_name_must_be_simple_lowercase_identifier(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionTrendConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_trend_config_env_table_name_error_mentions_variable_without_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://postgres:sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env(
            {
                DSN_ENV_VAR: secret_dsn,
                TABLE_ENV_VAR: "PaperReports",
            },
        )

    message = str(exc_info.value)
    assert TABLE_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_trend_config_public_exports_include_constants_config_and_loader() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_TABLE",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousScreeningDecisionSupportGateTransitionTrendConfig",
        "from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env",
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
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_store",
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
    config_module = _config_module()
    monkeypatch.setenv(ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(DSN_ENV_VAR, LOCAL_DSN)
    monkeypatch.setenv(
        TABLE_ENV_VAR,
        "paper_autonomous_screening_gate_transition_trend_env",
    )

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_trend_db_env()
    )

    assert config == (
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionTrendConfig(
            enabled=True,
            dsn=LOCAL_DSN,
            table_name="paper_autonomous_screening_gate_transition_trend_env",
        )
    )
