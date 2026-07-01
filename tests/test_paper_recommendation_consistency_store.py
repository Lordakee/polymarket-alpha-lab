from __future__ import annotations

import importlib
import re
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeConsistencyReport:
    generated_at: datetime
    config_version: str
    consistency_status: str


@dataclass(frozen=True)
class FakeConsistencyDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    consistency_status: str
    reason_codes_json: list[str]
    group_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    max_edge_spread: Decimal
    max_score_spread: Decimal
    min_source_count: int
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
    config_version: str = "recommendation-consistency-v1",
    consistency_status: str = "watch",
    reason_codes_json: list[str] | None = None,
) -> FakeConsistencyDbRow:
    return FakeConsistencyDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        consistency_status=consistency_status,
        reason_codes_json=reason_codes_json or ["missing_recommendation_sources"],
        group_count=2,
        pass_count=1,
        watch_count=1,
        blocked_count=0,
        max_edge_spread=Decimal("0.020000"),
        max_score_spread=Decimal("0.050000"),
        min_source_count=2,
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "consistency_status": consistency_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_consistency_db_row",
    )

    def to_db_row(report: FakeConsistencyReport) -> FakeConsistencyDbRow:
        return FakeConsistencyDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            consistency_status=report.consistency_status,
            reason_codes_json=["recommendation_consistency_passed"],
            group_count=1,
            pass_count=1,
            watch_count=0,
            blocked_count=0,
            max_edge_spread=Decimal("0.020000"),
            max_score_spread=Decimal("0.050000"),
            min_source_count=2,
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "consistency_status": report.consistency_status,
            },
        )

    def from_db_row(row: FakeConsistencyDbRow) -> FakeConsistencyReport:
        return FakeConsistencyReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            consistency_status=row.consistency_status,
        )

    companion.PaperRecommendationConsistencyDbRow = FakeConsistencyDbRow
    companion.paper_recommendation_consistency_report_to_db_row = to_db_row
    companion.paper_recommendation_consistency_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_consistency_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_consistency_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_consistency_store",
    )


def test_insert_paper_recommendation_consistency_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeConsistencyReport(
        generated_at=datetime(2026, 6, 21, 9, 30, tzinfo=UTC),
        config_version="recommendation-consistency-v1",
        consistency_status="pass",
    )

    inserted = store_module.insert_paper_recommendation_consistency_report(
        connection,
        report,
    )

    assert inserted == FakeConsistencyDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        consistency_status=report.consistency_status,
        reason_codes_json=["recommendation_consistency_passed"],
        group_count=1,
        pass_count=1,
        watch_count=0,
        blocked_count=0,
        max_edge_spread=Decimal("0.020000"),
        max_score_spread=Decimal("0.050000"),
        min_source_count=2,
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "consistency_status": report.consistency_status,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_consistency_reports (
            report_sha256,
            generated_at,
            config_version,
            consistency_status,
            reason_codes,
            group_count,
            pass_count,
            watch_count,
            blocked_count,
            max_edge_spread,
            max_score_spread,
            min_source_count,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        "pass",
        ["recommendation_consistency_passed"],
        1,
        1,
        0,
        0,
        Decimal("0.020000"),
        Decimal("0.050000"),
        2,
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "consistency_status": report.consistency_status,
        },
        True,
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_recommendation_consistency_report(
            connection,
            FakeConsistencyReport(
                generated_at=datetime(2026, 6, 21, 9, 30, tzinfo=UTC),
                config_version="recommendation-consistency-v1",
                consistency_status="pass",
            ),
            table_name="paper_recommendation_consistency_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_insert_preserves_execute_exception_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.insert_paper_recommendation_consistency_report(
            connection,
            FakeConsistencyReport(
                generated_at=datetime(2026, 6, 21, 9, 30, tzinfo=UTC),
                config_version="recommendation-consistency-v1",
                consistency_status="pass",
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_exception_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.insert_paper_recommendation_consistency_report(
            connection,
            FakeConsistencyReport(
                generated_at=datetime(2026, 6, 21, 9, 30, tzinfo=UTC),
                config_version="recommendation-consistency-v1",
                consistency_status="pass",
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_propagates_cursor_close_exception_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        rows=(fake_db_row(consistency_status="pass"),),
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_recommendation_consistency_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_preserves_fetchall_exception_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="fetchall failed") as exc_info:
        store_module.load_paper_recommendation_consistency_reports(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.closed is True


def test_load_paper_recommendation_consistency_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(consistency_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_consistency_reports(
        connection,
        config_version="recommendation-consistency-v1",
        consistency_status="blocked",
        limit=25,
        table_name="consistency_archive",
    )

    assert reports == (
        FakeConsistencyReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            consistency_status=row.consistency_status,
        ),
    )
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            consistency_status,
            reason_codes,
            group_count,
            pass_count,
            watch_count,
            blocked_count,
            max_edge_spread,
            max_score_spread,
            min_source_count,
            payload,
            paper_only,
            report_only,
            readonly
        FROM consistency_archive
        WHERE config_version = %s AND consistency_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("recommendation-consistency-v1", "blocked", 25)


def test_load_paper_recommendation_consistency_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 11, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "recommendation-consistency-v1",
                "pass",
                ["recommendation_consistency_passed"],
                1,
                1,
                0,
                0,
                Decimal("0.020000"),
                Decimal("0.050000"),
                2,
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "recommendation-consistency-v1",
                    "consistency_status": "pass",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_consistency_reports(connection)

    assert reports == (
        FakeConsistencyReport(
            generated_at=generated_at,
            config_version="recommendation-consistency-v1",
            consistency_status="pass",
        ),
    )


def test_load_paper_recommendation_consistency_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "recommendation-consistency-v1",
                "consistency_status": "watch",
                "reason_codes": ["missing_recommendation_sources"],
                "group_count": 2,
                "pass_count": 1,
                "watch_count": 1,
                "blocked_count": 0,
                "max_edge_spread": Decimal("0.020000"),
                "max_score_spread": Decimal("0.050000"),
                "min_source_count": 2,
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "recommendation-consistency-v1",
                    "consistency_status": "watch",
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_recommendation_consistency_reports(connection)

    assert reports == (
        FakeConsistencyReport(
            generated_at=generated_at,
            config_version="recommendation-consistency-v1",
            consistency_status="watch",
        ),
    )


def test_load_paper_recommendation_consistency_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 13, 0, tzinfo=UTC)
    record_type = namedtuple(
        "ConsistencyRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "consistency_status",
            "reason_codes",
            "group_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_edge_spread",
            "max_score_spread",
            "min_source_count",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    connection = FakeConnection(
        rows=(
            record_type(
                "e" * 64,
                generated_at,
                "recommendation-consistency-v1",
                "blocked",
                ["edge_spread_exceeds_consistency_cap"],
                1,
                0,
                0,
                1,
                Decimal("0.020000"),
                Decimal("0.050000"),
                2,
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "recommendation-consistency-v1",
                    "consistency_status": "blocked",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_consistency_reports(connection)

    assert reports == (
        FakeConsistencyReport(
            generated_at=generated_at,
            config_version="recommendation-consistency-v1",
            consistency_status="blocked",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_consistency_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " recommendation-consistency-v1"}, "config_version"),
        ({"consistency_status": "selected"}, "consistency_status"),
        ({"consistency_status": True}, "consistency_status"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_recommendation_consistency_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000001_paper_recommendation_consistency_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_consistency_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_consistency_reports"
    return compact(match.group(1))


def test_migration_creates_consistency_report_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "consistency_status text not null",
        "reason_codes jsonb not null default '[]'::jsonb",
        "group_count integer not null",
        "pass_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "max_edge_spread numeric not null",
        "max_score_spread numeric not null",
        "min_source_count integer not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_consistency_report_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (consistency_status in ('pass', 'watch', 'blocked'))",
        "check (jsonb_typeof(reason_codes) = 'array')",
        "check (group_count >= 0)",
        "check (pass_count >= 0)",
        "check (watch_count >= 0)",
        "check (blocked_count >= 0)",
        "check (max_edge_spread >= 0)",
        "check (max_score_spread >= 0)",
        "check (min_source_count > 0)",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_uses_numeric_for_decimal_scalars_and_jsonb_for_payloads():
    body = table_body(migration_sql())

    assert "max_edge_spread numeric" in body
    assert "max_score_spread numeric" in body
    assert "reason_codes jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prcr_generated_at on public.paper_recommendation_consistency_reports (generated_at desc);",
        "create index if not exists idx_prcr_config_version_generated_at on public.paper_recommendation_consistency_reports (config_version, generated_at desc);",
        "create index if not exists idx_prcr_consistency_status_generated_at on public.paper_recommendation_consistency_reports (consistency_status, generated_at desc);",
        "create index if not exists idx_prcr_reason_codes_gin on public.paper_recommendation_consistency_reports using gin (reason_codes jsonb_path_ops);",
        "create index if not exists idx_prcr_payload_gin on public.paper_recommendation_consistency_reports using gin (payload jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_account_terms():
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern
