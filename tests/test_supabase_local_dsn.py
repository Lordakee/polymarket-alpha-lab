import pytest

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


ENV_VAR = "POLYMARKET_ALPHA_LAB_TEST_DB_DSN"


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
def test_validate_local_postgres_dsn_accepts_local_dsns(dsn: str) -> None:
    validate_local_postgres_dsn(dsn, env_var_name=ENV_VAR)


@pytest.mark.parametrize(
    "dsn",
    [
        "",
        "postgresql://example.invalid/postgres",
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
def test_validate_local_postgres_dsn_rejects_nonlocal_or_unsafe_dsns(
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        validate_local_postgres_dsn(dsn, env_var_name=ENV_VAR)

    message = str(exc_info.value)
    assert ENV_VAR in message
    assert "local Postgres/Supabase" in message
    if dsn:
        assert dsn not in message
