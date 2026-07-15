from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal

import pytest

from polymarket_alpha_lab.supabase_local_dsn import (
    LocalPostgresDsnReadiness,
    local_postgres_dsn_readiness,
    validate_local_postgres_dsn,
)


ENV_VAR = "POLYMARKET_ALPHA_LAB_TEST_DB_DSN"


def test_local_dsn_readiness_cannot_be_subclassed() -> None:
    with pytest.raises(TypeError, match="may not be subclassed"):
        type(
            "UnsafeLocalPostgresDsnReadiness",
            (LocalPostgresDsnReadiness,),
            {"__post_init__": lambda self: None},
        )


@pytest.mark.parametrize(
    (
        "status",
        "ready_check_count",
        "blocker_count",
        "required_check_count",
        "reason_codes",
        "error_match",
    ),
    (
        (
            "ready",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_ready",),
            "ready status",
        ),
        (
            "blocker",
            Decimal("4.000000"),
            Decimal("0.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "blocker_count",
        ),
        (
            "blocker",
            Decimal("5.000000"),
            Decimal("-1.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "blocker_count",
        ),
        (
            "blocker",
            Decimal("-1.000000"),
            Decimal("5.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "ready_check_count must be nonnegative",
        ),
        (
            "blocker",
            Decimal("3.500000"),
            Decimal("0.500000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "ready_check_count must be whole",
        ),
        (
            "blocker",
            Decimal("NaN"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "ready_check_count must be finite",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("Infinity"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "blocker_count must be finite",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("NaN"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "required_check_count must be finite",
        ),
        (
            "ready",
            Decimal("4.000000"),
            Decimal("0.000000"),
            Decimal("4.000000"),
            (
                "local_supabase_postgres_dsn_ready",
                "local_supabase_postgres_dsn_invalid_blocker",
            ),
            "ready reason code",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_ready",),
            "blocker reason codes",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            ("forged_reason_blocker",),
            "known blocker reason codes",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            ["local_supabase_postgres_dsn_invalid_blocker"],
            "reason_codes must be a tuple",
        ),
        (
            "blocker",
            Decimal("2.000000"),
            Decimal("2.000000"),
            Decimal("4.000000"),
            (
                "local_supabase_postgres_dsn_invalid_blocker",
                "local_supabase_postgres_dsn_invalid_blocker",
            ),
            "reason_codes must not contain duplicates",
        ),
        (
            "blocker",
            Decimal("2.000000"),
            Decimal("2.000000"),
            Decimal("4.000000"),
            ("local_supabase_postgres_dsn_invalid_blocker",),
            "blocker status counts",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            (
                "local_supabase_postgres_dsn_invalid_blocker",
                "hosted_database_dsn_rejected_blocker",
            ),
            "exact ordered blocker reason tuple",
        ),
        (
            "blocker",
            Decimal("3.000000"),
            Decimal("1.000000"),
            Decimal("4.000000"),
            ("hosted_database_dsn_rejected_blocker",),
            "exact ordered blocker reason tuple",
        ),
    ),
)
def test_local_dsn_readiness_rejects_inconsistent_direct_construction(
    status: str,
    ready_check_count: Decimal,
    blocker_count: Decimal,
    required_check_count: Decimal,
    reason_codes: tuple[str, ...],
    error_match: str,
) -> None:
    with pytest.raises(ValueError, match=error_match):
        LocalPostgresDsnReadiness(
            env_var_name=ENV_VAR,
            status=status,
            validator_name="validate_local_postgres_dsn",
            durable_persistence_target="local_supabase_postgres",
            allowed_local_hosts=("localhost", "127.0.0.1", "::1"),
            checked_dsn="<redacted-dsn>",
            local_supabase_postgres_only=True,
            rejects_jsonl_file_fallback=True,
            rejects_sqlite_fallback=True,
            rejects_hosted_database_fallback=True,
            ready_check_count=ready_check_count,
            blocker_count=blocker_count,
            required_check_count=required_check_count,
            reason_codes=reason_codes,
        )


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
        "host=example.invalid HOST=localhost dbname=postgres",
        "HOST=localhost host=example.invalid dbname=postgres",
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


def test_local_postgres_dsn_readiness_reports_local_only_contract_without_leaking_dsn() -> None:
    ready = local_postgres_dsn_readiness(
        "postgresql://postgres:secret@localhost:54322/postgres",
        env_var_name=ENV_VAR,
    )
    hosted = local_postgres_dsn_readiness(
        "postgresql://postgres:super-secret-password@db.abcdefghijklmnopqrst.supabase.co:5432/postgres",
        env_var_name=ENV_VAR,
    )
    sqlite = local_postgres_dsn_readiness(
        "sqlite:///tmp/project.db",
        env_var_name=ENV_VAR,
    )

    assert is_dataclass(ready)
    assert ready.__dataclass_params__.frozen is True
    for item in (ready, hosted, sqlite):
        assert item.env_var_name == ENV_VAR
        assert item.validator_name == "validate_local_postgres_dsn"
        assert item.durable_persistence_target == "local_supabase_postgres"
        assert item.allowed_local_hosts == ("localhost", "127.0.0.1", "::1")
        assert item.local_supabase_postgres_only is True
        assert item.rejects_jsonl_file_fallback is True
        assert item.rejects_sqlite_fallback is True
        assert item.rejects_hosted_database_fallback is True
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert item.checked_dsn == "<redacted-dsn>"
        assert item.ready_check_count + item.blocker_count == item.required_check_count
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name.endswith("_count"):
                assert type(value) is Decimal

    assert ready.status == "ready"
    assert ready.reason_codes == ("local_supabase_postgres_dsn_ready",)
    assert ready.ready_check_count == Decimal("4.000000")
    assert ready.blocker_count == Decimal("0.000000")
    assert ready.required_check_count == Decimal("4.000000")

    assert hosted.status == "blocker"
    assert hosted.reason_codes == (
        "hosted_database_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
    )
    assert hosted.ready_check_count == Decimal("3.000000")
    assert hosted.blocker_count == Decimal("1.000000")

    assert sqlite.status == "blocker"
    assert sqlite.reason_codes == (
        "sqlite_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
    )
    assert sqlite.ready_check_count == Decimal("3.000000")
    assert sqlite.blocker_count == Decimal("1.000000")

    assert "super-secret-password" not in repr(hosted)
    assert "db.abcdefghijklmnopqrst.supabase.co" not in repr(hosted)
    assert "sqlite:///tmp/project.db" not in repr(sqlite)

    with pytest.raises(FrozenInstanceError):
        ready.status = "blocker"  # type: ignore[misc]
