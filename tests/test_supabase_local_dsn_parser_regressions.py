"""Offline regression tests for local DSN parsing; all fixtures are synthetic."""

from decimal import Decimal

import pytest

from polymarket_alpha_lab.supabase_local_dsn import (
    local_postgres_dsn_readiness,
    validate_local_postgres_dsn,
)


ENV_VAR = "POLYMARKET_ALPHA_LAB_TEST_DB_DSN"


# All DSNs below are synthetic fixtures. These tests never open a connection.
@pytest.mark.parametrize(
    "dsn",
    (
        pytest.param(
            'host=localhost password="fixture host=remote.invalid dbname=postgres"',
            id="keyword-double-quoted-shadow-host",
        ),
        pytest.param(
            'host=localhost password="fixture hostaddr=203.0.113.1 dbname=postgres"',
            id="keyword-double-quoted-shadow-hostaddr",
        ),
        pytest.param(
            'host=localhost password="fixture service=fixture_remote dbname=postgres"',
            id="keyword-double-quoted-shadow-service",
        ),
        pytest.param(
            'password="fixture host=remote.invalid dbname=postgres" host=localhost',
            id="keyword-double-quoted-duplicate-host",
        ),
        pytest.param(
            "host=localhost password='fixture'host=remote.invalid",
            id="keyword-adjacent-quoted-value",
        ),
        pytest.param(
            "host=localhost password='unterminated",
            id="keyword-unterminated-quote",
        ),
        pytest.param(
            "host=localhost password=fixture\\",
            id="keyword-dangling-escape",
        ),
        pytest.param("host = remote.invalid dbname=postgres", id="keyword-spaced-remote-host"),
        pytest.param("host=localhost host = remote.invalid", id="keyword-spaced-duplicate-host"),
        pytest.param("host=localhost hostaddr = 203.0.113.1", id="keyword-spaced-hostaddr"),
        pytest.param("host=localhost service = fixture_remote", id="keyword-spaced-service"),
        pytest.param("=localhost host=localhost", id="keyword-empty-key"),
        pytest.param("host=localhost dangling", id="keyword-missing-equals"),
        pytest.param("host=localhost password=fixture\x00", id="keyword-nul"),
        pytest.param(
            "postgresql://localhost/postgres#?host=remote.invalid",
            id="uri-fragment-shadow-host",
        ),
        pytest.param(
            "postgresql://localhost/postgres#?hostaddr=203.0.113.1",
            id="uri-fragment-shadow-hostaddr",
        ),
        pytest.param(
            "postgresql://localhost/postgres#?service=fixture_remote",
            id="uri-fragment-shadow-service",
        ),
        pytest.param(
            "postgresql://localhost/postgres?application_name=fixture#&host=remote.invalid",
            id="uri-query-fragment-shadow-host",
        ),
        pytest.param(
            "postgresql://localhost/postgres?application_name=fixture#&hostaddr=203.0.113.1",
            id="uri-query-fragment-shadow-hostaddr",
        ),
        pytest.param(
            "postgresql://localhost/postgres?application_name=fixture#&service=fixture_remote",
            id="uri-query-fragment-shadow-service",
        ),
        pytest.param(
            "postgresql://remote.invalid\x00@localhost/postgres",
            id="uri-nul-truncation",
        ),
        pytest.param("postgresql://localhost/postgres#", id="uri-empty-fragment"),
        pytest.param("postgresql://localhost/postgres\x00", id="uri-trailing-nul"),
    ),
)
def test_local_dsn_parser_ambiguities_fail_closed_without_leaking(dsn: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        validate_local_postgres_dsn(dsn, env_var_name=ENV_VAR)
    message = str(exc_info.value)
    assert ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "fixture" not in message
    assert "remote.invalid" not in message
    assert "203.0.113.1" not in message

    report = local_postgres_dsn_readiness(dsn, env_var_name=ENV_VAR)
    assert report.status == "blocker"
    assert "local_supabase_postgres_dsn_invalid_blocker" in report.reason_codes
    assert report.checked_dsn == "<redacted-dsn>"
    assert report.blocker_count == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert dsn not in repr(report)
    assert "fixture" not in repr(report)
    assert "remote.invalid" not in repr(report)
    assert "203.0.113.1" not in repr(report)


@pytest.mark.parametrize(
    "dsn",
    (
        pytest.param("host = localhost port = 54322 dbname = postgres", id="spaced-equals"),
        pytest.param("host='localhost' dbname='postgres'", id="quoted-host"),
        pytest.param("host=localhost password=''", id="empty-password"),
        pytest.param("host=localhost password=", id="empty-unquoted-password"),
        pytest.param("host=localhost password='fixture with spaces'", id="quoted-spaces"),
        pytest.param(
            r"host=localhost password='fixture\' quoted' dbname=postgres",
            id="escaped-single-quote",
        ),
        pytest.param(r"host=localhost password='fixture\\path'", id="escaped-backslash"),
        pytest.param(r"host=localhost password=fixture\ with\ spaces", id="unquoted-escapes"),
        pytest.param('host=localhost password=fixture"quote', id="literal-double-quote"),
        pytest.param(
            "host=localhost password='fixture host=remote.invalid hostaddr=203.0.113.1'",
            id="single-quoted-connection-words-are-password-data",
        ),
        pytest.param(
            "host=localhost password='fixture\" host=remote.invalid'",
            id="double-quote-inside-single-quoted-password",
        ),
        pytest.param("host=localhost password=fixture#text", id="keyword-hash-is-data"),
        pytest.param("\thost\t=\tlocalhost\r\ndbname=postgres\n", id="ascii-whitespace"),
        pytest.param("host='/var/run/postgresql' dbname=postgres", id="quoted-unix-socket"),
        pytest.param("postgresql://user:fixture%23text@localhost/postgres", id="encoded-password-hash"),
        pytest.param("postgresql://localhost/postgres%23fixture", id="encoded-database-hash"),
        pytest.param(
            "postgresql://localhost/postgres?application_name=fixture%23text",
            id="encoded-query-hash",
        ),
    ),
)
def test_local_dsn_libpq_value_syntax_preserves_local_readiness(dsn: str) -> None:
    validate_local_postgres_dsn(dsn, env_var_name=ENV_VAR)
    report = local_postgres_dsn_readiness(dsn, env_var_name=ENV_VAR)
    assert report.status == "ready"
    assert report.reason_codes == ("local_supabase_postgres_dsn_ready",)
    assert report.checked_dsn == "<redacted-dsn>"


@pytest.mark.parametrize("value", (None, 0, True, b"host=localhost", ["host=localhost"]))
def test_local_dsn_invalid_runtime_types_fail_closed(value: object) -> None:
    with pytest.raises(ValueError, match="local Postgres/Supabase"):
        validate_local_postgres_dsn(value, env_var_name=ENV_VAR)  # type: ignore[arg-type]
    report = local_postgres_dsn_readiness(value, env_var_name=ENV_VAR)  # type: ignore[arg-type]
    assert report.status == "blocker"
    assert report.reason_codes == ("local_supabase_postgres_dsn_invalid_blocker",)
    assert report.checked_dsn == "<redacted-dsn>"


def test_local_dsn_spaced_remote_keyword_is_classified_as_hosted() -> None:
    report = local_postgres_dsn_readiness("host = remote.invalid", env_var_name=ENV_VAR)
    assert report.status == "blocker"
    assert report.reason_codes == (
        "hosted_database_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
    )
