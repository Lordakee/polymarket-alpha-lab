import pytest

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


ENV_VAR = "POLYMARKET_ALPHA_LAB_TEST_DB_DSN"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost/postgres",
        "postgresql://LOCALHOST/postgres",
        "postgres://localhost:54322/postgres",
        "postgresql://user:password@127.0.0.1:5432/postgres",
        "postgresql://user:password@[::1]:5432/postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "postgresql:///postgres?host=LOCALHOST",
        "host=localhost port=54322 dbname=postgres",
        "HOST=LOCALHOST port=54322 dbname=postgres",
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
        "postgresql://postgres:super-secret-password@db.example.invalid:5432/postgres",
        "postgresql://postgres:super-secret-password@db.abcdefghijklmnopqrst.supabase.co:5432/postgres",
        "postgresql://postgres:super-secret-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        "postgresql://postgres:super-secret-password@db.abcdefghijklmnopqrst.supabase.co:5432/postgres?sslmode=require&access_token=sbp_v0_secret_token",
        "postgresql://db.abcdefghijklmnopqrst.supabase.co/postgres?token=sbp_v0_secret_token",
        "postgresql://localhost,example.invalid/postgres",
        "postgresql://localhost:70000/postgres",
        "postgresql:///postgres",
        "postgresql://localhost/postgres?host=localhost",
        "postgresql://localhost/postgres?hostaddr=127.0.0.1",
        "postgresql://localhost/postgres?service=local",
        "postgresql:///postgres?host=localhost,example.invalid",
        "postgresql:///postgres?host=db.abcdefghijklmnopqrst.supabase.co",
        "host=example.invalid dbname=postgres",
        "host=localhost,example.invalid dbname=postgres",
        "host=db.abcdefghijklmnopqrst.supabase.co password=super-secret-password dbname=postgres",
        "host=aws-0-us-east-1.pooler.supabase.com password=super-secret-password dbname=postgres",
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
    assert "super-secret-password" not in message
    assert "sbp_v0_secret_token" not in message
    assert "example.invalid" not in message
    assert "db.abcdefghijklmnopqrst.supabase.co" not in message
    assert "aws-0-us-east-1.pooler.supabase.com" not in message
