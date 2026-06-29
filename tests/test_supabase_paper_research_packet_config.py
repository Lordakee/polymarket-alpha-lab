from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from polymarket_alpha_lab.paper_research_packet_store import (
    DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    DEFAULT_PAPER_RESEARCH_PACKET_DB_TABLE,
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
    SupabasePaperResearchPacketConfig,
    from_paper_research_packet_db_env,
)


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config = from_paper_research_packet_db_env({})

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == "paper_research_packet_reports"
    assert DEFAULT_PAPER_RESEARCH_PACKET_DB_TABLE == (
        DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_paper_research_packet_db_env(
            {
                PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR: "true",
                PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR: " postgresql://user:secret@db/app",
            },
        )

    assert PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_and_table() -> None:
    config = from_paper_research_packet_db_env(
        {
            PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR: "1",
            PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR: (
                "postgresql://user:secret@localhost:54322/app"
            ),
            PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR: "audit.paper_research_packet_reports",
        },
    )

    assert config.enabled is True
    assert config.dsn == "postgresql://user:secret@localhost:54322/app"
    assert config.table_name == "audit.paper_research_packet_reports"


def test_env_config_rejects_remote_dsn_without_echoing_secret() -> None:
    secret_dsn = "postgresql://user:topsecret@db.example.invalid/app"

    with pytest.raises(ValueError) as exc_info:
        from_paper_research_packet_db_env(
            {
                PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message
    assert "db.example.invalid" not in message


@pytest.mark.parametrize("value", ("", "0", "false", " FALSE "))
def test_disabled_values_are_strict_but_case_and_space_tolerant(value: str) -> None:
    assert from_paper_research_packet_db_env(
        {PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR: value},
    ).enabled is False


@pytest.mark.parametrize("value", ("1", "true", " TRUE "))
def test_enabled_values_are_strict_but_case_and_space_tolerant(value: str) -> None:
    config = from_paper_research_packet_db_env(
        {
            PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR: value,
            PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR: (
                "postgresql://user:secret@localhost:54322/app"
            ),
        },
    )

    assert config.enabled is True


@pytest.mark.parametrize("value", ("yes", "2", True))
def test_enabled_env_config_rejects_non_strict_values(value: object) -> None:
    with pytest.raises(ValueError, match=PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR):
        from_paper_research_packet_db_env(
            {PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR: value},  # type: ignore[dict-item]
        )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabasePaperResearchPacketConfig(
        enabled=True,
        dsn="postgresql://user:secret@localhost:54322/app",
        table_name="research_packet_archive",
    )

    assert "secret" not in repr(config)
    assert "<redacted>" in repr(config)
    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "table_name",
    (
        "research_packet_archive",
        "paper_research_packet_reports",
        "a",
        "a1",
        "audit.paper_research_packet_reports",
    ),
)
def test_table_name_accepts_store_simple_lowercase_identifier_values(table_name: str) -> None:
    assert SupabasePaperResearchPacketConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    ).table_name == table_name


@pytest.mark.parametrize(
    "table_name",
    (
        "audit..paper_research_packet_reports",
        "audit.paper.research_packet_reports",
        "PaperResearchPacketReports",
        "_paper_research_packet_reports",
        "paper_research_packet_reports_",
        "paper-research-packet-reports",
        "",
    ),
)
def test_table_name_rejects_values_outside_store_contract(table_name: str) -> None:
    with pytest.raises(ValueError, match=PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR):
        from_paper_research_packet_db_env(
            {PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR: table_name},
        )


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled"):
        SupabasePaperResearchPacketConfig(
            enabled="true",  # type: ignore[arg-type]
            dsn=None,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabasePaperResearchPacketConfig(
            enabled=False,
            dsn=object(),  # type: ignore[arg-type]
        )

    assert PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR in str(exc_info.value)
    assert "object" not in str(exc_info.value)
