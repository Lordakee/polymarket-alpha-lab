from __future__ import annotations

import ast
import importlib
import inspect
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


DEFAULT_TABLE = "candidate_decision_score_reports"


@dataclass(frozen=True)
class FakeCandidateDecisionScoreReport:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_id: str
    normalized_market_question: str
    primary_team_id: str
    action: str
    decision_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeCandidateDecisionScoreDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_id: str
    normalized_market_question: str
    primary_team_id: str
    secondary_team_ids_json: list[str]
    selected_side: str
    forecast_probability: Decimal | None
    executable_price: Decimal | None
    gross_edge: Decimal | None
    estimated_cost_drag: Decimal
    net_edge: Decimal | None
    cost_score: Decimal
    liquidity_score: Decimal
    evidence_score: Decimal
    resolution_score: Decimal
    team_memory_score: Decimal
    team_memory_policy: str
    decision_score: Decimal
    action: str
    hard_blocker_codes_json: list[str]
    reason_codes_json: list[str]
    source_report_refs_json: list[str]
    derived_validation_digest: str
    boundary_statement: str
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
        self.close_count = 0

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.close_count += 1
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        cursor: FakeCursor | None = None,
    ) -> None:
        self.cursor_instance = cursor if cursor is not None else FakeCursor(rows)
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


@dataclass(frozen=True)
class StoreFixture:
    module: types.ModuleType
    conversion_calls: list[FakeCandidateDecisionScoreReport]
    from_row_calls: list[FakeCandidateDecisionScoreDbRow]


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _report(
    *,
    action: str = "paper_recommend",
    primary_team_id: str = "crypto_news",
) -> FakeCandidateDecisionScoreReport:
    return FakeCandidateDecisionScoreReport(
        generated_at=datetime(2026, 7, 7, 13, 45, tzinfo=UTC),
        config_version="candidate-decision-score-v0",
        candidate_id="candidate_001",
        market_id="market_001",
        normalized_market_question="will example resolve yes",
        primary_team_id=primary_team_id,
        action=action,
        decision_score=Decimal("0.820000"),
    )


def _db_row(report: FakeCandidateDecisionScoreReport) -> FakeCandidateDecisionScoreDbRow:
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_id": report.candidate_id,
        "market_id": report.market_id,
        "normalized_market_question": report.normalized_market_question,
        "primary_team_id": report.primary_team_id,
        "secondary_team_ids": ["election_models"],
        "selected_side": "yes",
        "decision_score": str(report.decision_score),
        "action": report.action,
        "boundary_statement": (
            "Paper-only candidate decision support; no trading or execution authorization."
        ),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    return FakeCandidateDecisionScoreDbRow(
        report_sha256="d" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_id=report.candidate_id,
        market_id=report.market_id,
        normalized_market_question=report.normalized_market_question,
        primary_team_id=report.primary_team_id,
        secondary_team_ids_json=["election_models"],
        selected_side="yes",
        forecast_probability=Decimal("0.710000"),
        executable_price=Decimal("0.630000"),
        gross_edge=Decimal("0.080000"),
        estimated_cost_drag=Decimal("0.010000"),
        net_edge=Decimal("0.070000"),
        cost_score=Decimal("0.900000"),
        liquidity_score=Decimal("0.760000"),
        evidence_score=Decimal("0.830000"),
        resolution_score=Decimal("0.810000"),
        team_memory_score=Decimal("0.800000"),
        team_memory_policy="allow",
        decision_score=report.decision_score,
        action=report.action,
        hard_blocker_codes_json=[],
        reason_codes_json=[f"candidate_decision_{report.action}"],
        source_report_refs_json=["source_report_001"],
        derived_validation_digest="e" * 64,
        boundary_statement=payload["boundary_statement"],
        payload_json=payload,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _row_values(row: FakeCandidateDecisionScoreDbRow) -> tuple[Any, ...]:
    return (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.candidate_id,
        row.market_id,
        row.normalized_market_question,
        row.primary_team_id,
        row.secondary_team_ids_json,
        row.selected_side,
        row.forecast_probability,
        row.executable_price,
        row.gross_edge,
        row.estimated_cost_drag,
        row.net_edge,
        row.cost_score,
        row.liquidity_score,
        row.evidence_score,
        row.resolution_score,
        row.team_memory_score,
        row.team_memory_policy,
        row.decision_score,
        row.action,
        row.hard_blocker_codes_json,
        row.reason_codes_json,
        row.source_report_refs_json,
        row.derived_validation_digest,
        row.boundary_statement,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _row_dict(row: FakeCandidateDecisionScoreDbRow) -> dict[str, Any]:
    return dict(zip(_select_columns(), _row_values(row), strict=True))


def _select_columns() -> tuple[str, ...]:
    return (
        "report_sha256",
        "generated_at",
        "config_version",
        "candidate_id",
        "market_id",
        "normalized_market_question",
        "primary_team_id",
        "secondary_team_ids",
        "selected_side",
        "forecast_probability",
        "executable_price",
        "gross_edge",
        "estimated_cost_drag",
        "net_edge",
        "cost_score",
        "liquidity_score",
        "evidence_score",
        "resolution_score",
        "team_memory_score",
        "team_memory_policy",
        "decision_score",
        "action",
        "hard_blocker_codes",
        "reason_codes",
        "source_report_refs",
        "derived_validation_digest",
        "boundary_statement",
        "payload",
        "paper_only",
        "report_only",
        "readonly",
    )


@pytest.fixture()
def store_fixture(monkeypatch: pytest.MonkeyPatch) -> StoreFixture:
    conversion_calls: list[FakeCandidateDecisionScoreReport] = []
    from_row_calls: list[FakeCandidateDecisionScoreDbRow] = []
    companion = types.ModuleType("polymarket_alpha_lab.candidate_decision_score_db_row")

    def to_db_row(
        report: FakeCandidateDecisionScoreReport,
    ) -> FakeCandidateDecisionScoreDbRow:
        conversion_calls.append(report)
        if type(report) is not FakeCandidateDecisionScoreReport:
            raise ValueError("report must be a CandidateDecisionScoreReport")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if getattr(report, flag_name, None) is not True:
                raise ValueError(f"report must be {flag_name}")
        return _db_row(report)

    def from_db_row(
        row: FakeCandidateDecisionScoreDbRow,
    ) -> FakeCandidateDecisionScoreReport:
        from_row_calls.append(row)
        if type(row) is not FakeCandidateDecisionScoreDbRow:
            raise ValueError("row must be a CandidateDecisionScoreDbRow")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if getattr(row, flag_name, None) is not True:
                raise ValueError(f"DB row must be {flag_name}")
        return _report(action=row.action, primary_team_id=row.primary_team_id)

    companion.CandidateDecisionScoreDbRow = FakeCandidateDecisionScoreDbRow
    companion.candidate_decision_score_report_to_db_row = to_db_row
    companion.candidate_decision_score_report_from_db_row = from_db_row
    companion.to_db_row = to_db_row
    companion.from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.candidate_decision_score_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.candidate_decision_score_store", None)
    module = importlib.import_module("polymarket_alpha_lab.candidate_decision_score_store")
    yield StoreFixture(
        module=module,
        conversion_calls=conversion_calls,
        from_row_calls=from_row_calls,
    )
    sys.modules.pop("polymarket_alpha_lab.candidate_decision_score_store", None)


def test_module_import_does_not_require_db_row_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(
        sys.modules,
        "polymarket_alpha_lab.candidate_decision_score_db_row",
        raising=False,
    )
    sys.modules.pop("polymarket_alpha_lab.candidate_decision_score_store", None)

    module = importlib.import_module("polymarket_alpha_lab.candidate_decision_score_store")

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_SCORE_REPORT_TABLE",
        "insert_candidate_decision_score_report",
        "load_candidate_decision_score_reports",
        "candidate_decision_score_report_sink_from_config",
    )
    sys.modules.pop("polymarket_alpha_lab.candidate_decision_score_store", None)


def test_insert_candidate_decision_score_report_uses_codec_and_parameterized_insert(
    store_fixture: StoreFixture,
) -> None:
    connection = FakeConnection()
    report = _report()
    expected = _db_row(report)

    inserted = store_fixture.module.insert_candidate_decision_score_report(
        connection,
        report,
    )

    assert inserted == expected
    assert store_fixture.conversion_calls == [report]
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO candidate_decision_score_reports (
            report_sha256,
            generated_at,
            config_version,
            candidate_id,
            market_id,
            normalized_market_question,
            primary_team_id,
            secondary_team_ids,
            selected_side,
            forecast_probability,
            executable_price,
            gross_edge,
            estimated_cost_drag,
            net_edge,
            cost_score,
            liquidity_score,
            evidence_score,
            resolution_score,
            team_memory_score,
            team_memory_policy,
            decision_score,
            action,
            hard_blocker_codes,
            reason_codes,
            source_report_refs,
            derived_validation_digest,
            boundary_statement,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected)


@pytest.mark.parametrize(
    "table_name",
    [
        "candidate_decision_score_reports; drop table fills",
        "CandidateDecisionScoreReports",
        "audit.CandidateDecisionScoreReports",
        "_candidate_decision_score_reports",
        "candidate_decision_score_reports_",
        "public.audit.candidate_decision_score_reports",
        "candidate_decision_score_reports--",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    store_fixture: StoreFixture,
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_fixture.module.insert_candidate_decision_score_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert store_fixture.conversion_calls == []


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_insert_preserves_paper_report_readonly_boundary_before_cursor_creation(
    store_fixture: StoreFixture,
    flag_name: str,
) -> None:
    report = _report()
    object.__setattr__(report, flag_name, False)
    connection = FakeConnection()

    with pytest.raises(ValueError, match=flag_name):
        store_fixture.module.insert_candidate_decision_score_report(connection, report)

    assert store_fixture.conversion_calls == [report]
    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_closes_cursor_and_preserves_execute_error_when_close_fails(
    store_fixture: StoreFixture,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(execute_error=execute_error, close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_fixture.module.insert_candidate_decision_score_report(
            connection,
            _report(),
        )

    assert exc_info.value is execute_error
    assert cursor.close_count == 1
    assert cursor.closed is True


def test_insert_propagates_cursor_close_error_after_successful_execute(
    store_fixture: StoreFixture,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_fixture.module.insert_candidate_decision_score_report(
            connection,
            _report(),
        )

    assert exc_info.value is close_error
    assert cursor.close_count == 1
    assert cursor.calls


def test_load_candidate_decision_score_reports_filters_limits_and_orders_with_params(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_report())
    connection = FakeConnection(rows=(row,))

    reports = store_fixture.module.load_candidate_decision_score_reports(
        connection,
        action="paper_recommend",
        primary_team_id="crypto_news",
        limit=25,
        table_name="audit.candidate_decision_score_reports",
    )

    assert reports == (_report(),)
    assert store_fixture.from_row_calls == [row]
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
            candidate_id,
            market_id,
            normalized_market_question,
            primary_team_id,
            secondary_team_ids,
            selected_side,
            forecast_probability,
            executable_price,
            gross_edge,
            estimated_cost_drag,
            net_edge,
            cost_score,
            liquidity_score,
            evidence_score,
            resolution_score,
            team_memory_score,
            team_memory_policy,
            decision_score,
            action,
            hard_blocker_codes,
            reason_codes,
            source_report_refs,
            derived_validation_digest,
            boundary_statement,
            payload,
            paper_only,
            report_only,
            readonly
        FROM audit.candidate_decision_score_reports
        WHERE action = %s AND primary_team_id = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper_recommend", "crypto_news", 25)
    assert "paper_recommend" not in sql
    assert "crypto_news" not in sql


def test_load_candidate_decision_score_reports_accepts_tuple_dict_and_namedtuple_records(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_report(action="watch", primary_team_id="macro_news"))
    Record = namedtuple("Record", _select_columns())
    connection = FakeConnection(
        rows=(
            _row_values(row),
            _row_dict(row),
            Record(*_row_values(row)),
        ),
    )

    reports = store_fixture.module.load_candidate_decision_score_reports(connection)

    assert reports == (
        _report(action="watch", primary_team_id="macro_news"),
        _report(action="watch", primary_team_id="macro_news"),
        _report(action="watch", primary_team_id="macro_news"),
    )
    assert len(store_fixture.from_row_calls) == 3


def test_load_closes_cursor_when_row_codec_rejects_report_boundary(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_report())
    bad_row = FakeCandidateDecisionScoreDbRow(
        **{
            **row.__dict__,
            "readonly": False,
        },
    )
    connection = FakeConnection(rows=(bad_row,))

    with pytest.raises(ValueError, match="readonly"):
        store_fixture.module.load_candidate_decision_score_reports(connection)

    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_closes_cursor_and_preserves_fetchall_error_when_close_fails(
    store_fixture: StoreFixture,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(fetchall_error=fetchall_error, close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="fetchall failed") as exc_info:
        store_fixture.module.load_candidate_decision_score_reports(connection)

    assert exc_info.value is fetchall_error
    assert cursor.close_count == 1
    assert cursor.closed is True


def test_load_propagates_cursor_close_error_after_successful_fetch(
    store_fixture: StoreFixture,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(rows=(_db_row(_report()),), close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_fixture.module.load_candidate_decision_score_reports(connection)

    assert exc_info.value is close_error
    assert cursor.close_count == 1
    assert cursor.calls


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.candidate_decision_score_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"action": ""}, "action"),
        ({"action": " paper_recommend"}, "action"),
        ({"primary_team_id": ""}, "primary_team_id"),
        ({"primary_team_id": " crypto_news"}, "primary_team_id"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_before_cursor_creation(
    store_fixture: StoreFixture,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_fixture.module.load_candidate_decision_score_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_disabled_config_returns_no_candidate_decision_score_sink(
    store_fixture: StoreFixture,
) -> None:
    config_module = importlib.import_module(
        "polymarket_alpha_lab.supabase_candidate_decision_score_config",
    )
    config = config_module.SupabaseCandidateDecisionScoreConfig(
        enabled=False,
        dsn=None,
        table=DEFAULT_TABLE,
    )
    calls: list[str] = []

    def connection_factory(dsn: str) -> FakeConnection:
        calls.append(dsn)
        return FakeConnection()

    sink = store_fixture.module.candidate_decision_score_report_sink_from_config(
        config,
        connection_factory=connection_factory,
    )

    assert sink is None
    assert calls == []
    assert store_fixture.conversion_calls == []


def test_enabled_config_sink_uses_configured_table_without_committing(
    store_fixture: StoreFixture,
) -> None:
    config_module = importlib.import_module(
        "polymarket_alpha_lab.supabase_candidate_decision_score_config",
    )
    secret_dsn = "postgresql://candidate:topsecret@localhost:54322/postgres"
    config = config_module.SupabaseCandidateDecisionScoreConfig(
        enabled=True,
        dsn=secret_dsn,
        table="audit.candidate_decision_score_reports",
    )
    connection = FakeConnection()
    factory_calls: list[str] = []

    def connection_factory(dsn: str) -> FakeConnection:
        factory_calls.append(dsn)
        return connection

    sink = store_fixture.module.candidate_decision_score_report_sink_from_config(
        config,
        connection_factory=connection_factory,
    )

    assert callable(sink)
    result = sink(_report())

    assert result == _db_row(_report())
    assert factory_calls == [secret_dsn]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    sql, _params = connection.cursor_instance.calls[0]
    assert "INSERT INTO audit.candidate_decision_score_reports" in normalize_sql(sql)


def test_enabled_config_sink_redacts_dsn_from_repr_and_errors(
    store_fixture: StoreFixture,
) -> None:
    config_module = importlib.import_module(
        "polymarket_alpha_lab.supabase_candidate_decision_score_config",
    )
    secret_dsn = "postgresql://candidate:topsecret@localhost:54322/postgres"
    config = config_module.SupabaseCandidateDecisionScoreConfig(
        enabled=True,
        dsn=secret_dsn,
        table=DEFAULT_TABLE,
    )

    def connection_factory(dsn: str) -> FakeConnection:
        raise RuntimeError(f"failed to connect to {dsn}")

    sink = store_fixture.module.candidate_decision_score_report_sink_from_config(
        config,
        connection_factory=connection_factory,
    )

    assert callable(sink)
    rendered = repr(sink)
    assert secret_dsn not in rendered
    assert "topsecret" not in rendered
    assert "dsn=<redacted>" in rendered
    with pytest.raises(RuntimeError) as exc_info:
        sink(_report())

    message = str(exc_info.value)
    assert "failed" in message
    assert "postgresql://" not in message
    assert "topsecret" not in message
    assert "localhost:54322" not in message


def test_store_surface_has_no_cli_network_psycopg_or_trading_auth_dependencies(
    store_fixture: StoreFixture,
) -> None:
    module = store_fixture.module
    tree = ast.parse(inspect.getsource(module))
    forbidden_import_fragments = (
        "argparse",
        "click",
        "cli",
        "http",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "typer",
        "urllib",
    )
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    forbidden_parameter_names = {"auth", "wallet", "order", "live_trading", "client"}
    for public_name in (
        "insert_candidate_decision_score_report",
        "load_candidate_decision_score_reports",
        "candidate_decision_score_report_sink_from_config",
    ):
        parameter_names = set(inspect.signature(getattr(module, public_name)).parameters)
        assert forbidden_parameter_names.isdisjoint(parameter_names)
