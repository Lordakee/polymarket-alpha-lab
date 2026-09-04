import pytest

from polymarket_alpha_lab.supabase_central_data_config import (
    CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR,
    CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR,
    SupabaseCentralDataConfig,
    from_central_data_env,
    validate_local_postgres_dsn,
)


LOCAL = "postgresql://postgres:secret@localhost:54322/postgres"


def test_default_disabled_and_repr_redacts_dsn() -> None:
    config = from_central_data_env({})
    assert config.enabled is False
    assert config.dsn is None
    enabled = SupabaseCentralDataConfig(True, LOCAL)
    assert "secret" not in repr(enabled)
    assert "<redacted>" in repr(enabled)


def test_enabled_requires_explicit_local_postgres_role() -> None:
    with pytest.raises(ValueError):
        from_central_data_env({CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR: "true"})
    for dsn in (
        "postgresql://postgres:secret@remote.example/postgres",
        "postgresql://post%67res:secret@localhost:54322/postgres",
        "sqlite:///tmp/db",
        "postgresql://other:secret@localhost:54322/postgres",
    ):
        with pytest.raises(ValueError):
            validate_local_postgres_dsn(dsn)


def test_disabled_supplied_dsn_is_validated_but_not_exposed_as_active() -> None:
    config = from_central_data_env(
        {
            CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR: "false",
            CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR: LOCAL,
        }
    )
    assert config.enabled is False
    assert config.dsn is None
