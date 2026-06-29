from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest


def _config_api():
    try:
        return import_module(
            "polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing module: {exc.name}")


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    api = _config_api()
    config = api.from_paper_research_packet_operator_flow_db_env({})

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == "paper_research_packet_operator_flow_reports"
    assert api.DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE == (
        "paper_research_packet_operator_flow_reports"
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    api = _config_api()
    with pytest.raises(ValueError) as exc_info:
        api.from_paper_research_packet_operator_flow_db_env(
            {
                api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR: "true",
                api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR: (
                    " postgresql://user:secret@db/app"
                ),
            },
        )

    assert api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_and_table() -> None:
    api = _config_api()
    config = api.from_paper_research_packet_operator_flow_db_env(
        {
            api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR: "1",
            api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR: (
                "postgresql://user:secret@localhost:54322/app"
            ),
            api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR: (
                "audit.paper_research_packet_operator_flow_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == "postgresql://user:secret@localhost:54322/app"
    assert config.table_name == "audit.paper_research_packet_operator_flow_reports"


def test_env_config_rejects_remote_dsn_without_echoing_secret() -> None:
    api = _config_api()
    secret_dsn = "postgresql://user:topsecret@db.example.invalid/app"

    with pytest.raises(ValueError) as exc_info:
        api.from_paper_research_packet_operator_flow_db_env(
            {
                api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message
    assert "db.example.invalid" not in message


@pytest.mark.parametrize("value", ("", "0", "false", " FALSE "))
def test_disabled_values_are_strict_but_case_and_space_tolerant(value: str) -> None:
    api = _config_api()
    assert api.from_paper_research_packet_operator_flow_db_env(
        {api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR: value},
    ).enabled is False


@pytest.mark.parametrize("value", ("1", "true", " TRUE "))
def test_enabled_values_are_strict_but_case_and_space_tolerant(value: str) -> None:
    api = _config_api()
    config = api.from_paper_research_packet_operator_flow_db_env(
        {
            api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR: value,
            api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR: (
                "postgresql://user:secret@localhost:54322/app"
            ),
        },
    )

    assert config.enabled is True


@pytest.mark.parametrize("value", ("yes", "2", True))
def test_enabled_env_config_rejects_non_strict_values(value: object) -> None:
    api = _config_api()
    with pytest.raises(
        ValueError,
        match=api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
    ):
        api.from_paper_research_packet_operator_flow_db_env(
            {api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR: value},  # type: ignore[dict-item]
        )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    api = _config_api()
    config = api.SupabasePaperResearchPacketOperatorFlowConfig(
        enabled=True,
        dsn="postgresql://user:secret@localhost:54322/app",
        table_name="operator_flow_archive",
    )

    assert "secret" not in repr(config)
    assert "<redacted>" in repr(config)
    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "table_name",
    (
        "operator_flow_archive",
        "paper_research_packet_operator_flow_reports",
        "a",
        "a1",
        "audit.paper_research_packet_operator_flow_reports",
    ),
)
def test_table_name_accepts_lowercase_identifier_values(table_name: str) -> None:
    api = _config_api()
    assert api.SupabasePaperResearchPacketOperatorFlowConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    ).table_name == table_name


@pytest.mark.parametrize(
    "table_name",
    (
        "audit..paper_research_packet_operator_flow_reports",
        "audit.paper.research_packet_operator_flow_reports",
        "PaperResearchPacketOperatorFlowReports",
        "_paper_research_packet_operator_flow_reports",
        "paper_research_packet_operator_flow_reports_",
        "paper-research-packet-operator-flow-reports",
        "",
    ),
)
def test_table_name_rejects_values_outside_identifier_contract(table_name: str) -> None:
    api = _config_api()
    with pytest.raises(
        ValueError,
        match=api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
    ):
        api.from_paper_research_packet_operator_flow_db_env(
            {api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR: table_name},
        )


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    api = _config_api()
    with pytest.raises(ValueError, match="enabled"):
        api.SupabasePaperResearchPacketOperatorFlowConfig(
            enabled="true",  # type: ignore[arg-type]
            dsn=None,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    api = _config_api()
    with pytest.raises(ValueError) as exc_info:
        api.SupabasePaperResearchPacketOperatorFlowConfig(
            enabled=False,
            dsn=object(),  # type: ignore[arg-type]
        )

    assert api.PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR in str(exc_info.value)
    assert "object" not in str(exc_info.value)
