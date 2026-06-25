from __future__ import annotations

import importlib
import sys
import traceback
import types
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    PaperAutonomousInvestmentLedgerEntry,
    PaperAutonomousInvestmentLedgerReasonCodeCount,
    PaperAutonomousInvestmentLedgerReport,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_row import (
    paper_autonomous_investment_ledger_report_to_db_row,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_config import (
    SupabasePaperAutonomousInvestmentLedgerConfig,
)


SECRET_DSN = "postgresql://worker:secret@example.invalid/polymarket"
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.paper_autonomous_investment_ledger_psycopg"
)


class FakeConnection:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


class FakeCursor:
    def __init__(self, *, rows: tuple[Any, ...] = ()) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.close_count = 0
        self.rowcount = 1
        self.rows = rows

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.close_count += 1


class FakeCursorConnection(FakeConnection):
    def __init__(self, *, rows: tuple[Any, ...] = ()) -> None:
        super().__init__()
        self.cursor_instance = FakeCursor(rows=rows)
        self.cursor_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance


class FakeCommitFailingConnection(FakeConnection):
    def commit(self) -> None:
        self.commit_count += 1
        raise RuntimeError("commit failed without dsn")


class FakeRollbackFailingConnection(FakeConnection):
    def rollback(self) -> None:
        self.rollback_count += 1
        raise RuntimeError("rollback failed without dsn")


class FakeCloseFailingConnection(FakeConnection):
    def close(self) -> None:
        self.close_count += 1
        raise RuntimeError("close failed without dsn")


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


def _install_fake_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    *,
    connect: Any,
) -> None:
    psycopg = types.ModuleType("psycopg")
    psycopg.connect = connect
    types_module = types.ModuleType("psycopg.types")
    json_module = types.ModuleType("psycopg.types.json")
    json_module.Jsonb = FakeJsonb
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types", types_module)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)


def _remove_psycopg_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    sys.modules.pop("polymarket_alpha_lab.paper_autonomous_investment_ledger_store", None)
    return importlib.import_module(ADAPTER_MODULE_NAME)


def _report() -> PaperAutonomousInvestmentLedgerReport:
    generated_at = datetime(2026, 6, 25, 12, 30, tzinfo=UTC)
    return PaperAutonomousInvestmentLedgerReport(
        generated_at=generated_at,
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
        recommended_next_step="review_paper_autonomous_investment_ledger",
        source_record_count=2,
        submitted_count=1,
        held_count=1,
        blocked_count=0,
        total_submitted_notional=Decimal("42.500000"),
        held_zero_notional_count=1,
        blocked_zero_notional_count=0,
        latest_generated_at=datetime(2026, 6, 25, 12, 29, 30, tzinfo=UTC),
        latest_age_seconds=30,
        reason_code_counts=(
            PaperAutonomousInvestmentLedgerReasonCodeCount(
                reason_code="paper_broker_execution_held",
                source_record_count=1,
            ),
            PaperAutonomousInvestmentLedgerReasonCodeCount(
                reason_code="paper_broker_execution_submitted",
                source_record_count=1,
            ),
        ),
        entries=(
            PaperAutonomousInvestmentLedgerEntry(
                entry_rank=1,
                source_generated_at=datetime(2026, 6, 25, 12, 29, tzinfo=UTC),
                source_config_version="paper-broker-v0",
                execution_status="paper_held",
                recommended_next_step="review_paper_broker_execution",
                source_gate_status="watch",
                source_proposal_count=2,
                source_proposal_total_notional=Decimal("42.500000"),
                execution_notional=Decimal("0.000000"),
                reason_codes=("paper_broker_execution_held",),
            ),
            PaperAutonomousInvestmentLedgerEntry(
                entry_rank=2,
                source_generated_at=datetime(2026, 6, 25, 12, 29, 30, tzinfo=UTC),
                source_config_version="paper-broker-v0",
                execution_status="paper_submitted",
                recommended_next_step="route_to_paper_order_lifecycle",
                source_gate_status="pass",
                source_proposal_count=1,
                source_proposal_total_notional=Decimal("42.500000"),
                execution_notional=Decimal("42.500000"),
                reason_codes=("paper_broker_execution_submitted",),
            ),
        ),
        reason_codes=("paper_autonomous_investment_ledger_held_records_present",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _unchecked_report(**overrides: object) -> PaperAutonomousInvestmentLedgerReport:
    values = dict(_report().__dict__)
    values.update(overrides)
    report = object.__new__(PaperAutonomousInvestmentLedgerReport)
    for name, value in values.items():
        object.__setattr__(report, name, value)
    return report


def _enabled_config() -> SupabasePaperAutonomousInvestmentLedgerConfig:
    return SupabasePaperAutonomousInvestmentLedgerConfig(
        enabled=True,
        dsn=SECRET_DSN,
        table_name="paper_autonomous_investment_ledger_archive",
    )


def _db_record_from_report(
    report: PaperAutonomousInvestmentLedgerReport,
) -> dict[str, object]:
    row = paper_autonomous_investment_ledger_report_to_db_row(report)
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "ledger_status": row.ledger_status,
        "recommended_next_step": row.recommended_next_step,
        "source_record_count": row.source_record_count,
        "submitted_count": row.submitted_count,
        "held_count": row.held_count,
        "blocked_count": row.blocked_count,
        "total_submitted_notional": row.total_submitted_notional,
        "held_zero_notional_count": row.held_zero_notional_count,
        "blocked_zero_notional_count": row.blocked_zero_notional_count,
        "latest_generated_at": row.latest_generated_at,
        "latest_age_seconds": row.latest_age_seconds,
        "reason_code_counts": row.reason_code_counts_json,
        "entries": row.entries_json,
        "reason_codes": row.reason_codes_json,
        "payload": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _unchecked_config(
    *,
    enabled: bool = True,
    dsn: str | None = SECRET_DSN,
    table_name: str = "paper_autonomous_investment_ledger_archive",
) -> SupabasePaperAutonomousInvestmentLedgerConfig:
    config = object.__new__(SupabasePaperAutonomousInvestmentLedgerConfig)
    object.__setattr__(config, "enabled", enabled)
    object.__setattr__(config, "dsn", dsn)
    object.__setattr__(config, "table_name", table_name)
    return config


def test_public_exports_and_import_do_not_require_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _remove_psycopg_modules(monkeypatch)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    module = importlib.import_module(ADAPTER_MODULE_NAME)

    assert module.__all__ == (
        "insert_paper_autonomous_investment_ledger_report_from_config",
        "insert_paper_autonomous_investment_ledger_report_with_psycopg",
        "load_paper_autonomous_investment_ledger_reports_from_config",
        "load_paper_autonomous_investment_ledger_reports_with_psycopg",
    )


def test_disabled_config_returns_none_without_connecting_for_insert_and_load(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    store_calls: list[object] = []
    config = SupabasePaperAutonomousInvestmentLedgerConfig(
        enabled=False,
        dsn=None,
        table_name="paper_autonomous_investment_ledger_reports",
    )

    insert_result = (
        adapter_module.insert_paper_autonomous_investment_ledger_report_from_config(
            config,
            _report(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: store_calls.append((args, kwargs)),
        )
    )
    load_result = adapter_module.load_paper_autonomous_investment_ledger_reports_from_config(
        config,
        connect=lambda dsn: connect_calls.append(dsn),
        load_reports=lambda *args, **kwargs: store_calls.append((args, kwargs)),
    )

    assert insert_result is None
    assert load_result is None
    assert connect_calls == []
    assert store_calls == []


def test_enabled_config_uses_dsn_table_connector_and_store_boundaries(
    adapter_module: types.ModuleType,
) -> None:
    insert_connection = FakeConnection()
    load_connection = FakeConnection()
    report = _report()
    expected_insert = object()
    expected_reports = (report,)
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, PaperAutonomousInvestmentLedgerReport, str]] = []
    load_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        if len(connect_calls) == 1:
            return insert_connection
        return load_connection

    def insert_report(
        connection_arg: Any,
        report_arg: PaperAutonomousInvestmentLedgerReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_insert

    def load_reports(
        connection_arg: Any,
        *,
        config_version: str | None,
        ledger_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperAutonomousInvestmentLedgerReport, ...]:
        load_calls.append(
            (connection_arg, config_version, ledger_status, limit, table_name),
        )
        return expected_reports

    insert_result = (
        adapter_module.insert_paper_autonomous_investment_ledger_report_from_config(
            _enabled_config(),
            report,
            connect=connect,
            insert_report=insert_report,
        )
    )
    load_result = adapter_module.load_paper_autonomous_investment_ledger_reports_from_config(
        _enabled_config(),
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
        limit=10,
        connect=connect,
        load_reports=load_reports,
    )

    assert insert_result is expected_insert
    assert load_result == expected_reports
    assert connect_calls == [SECRET_DSN, SECRET_DSN]
    store_connection, store_report, insert_table_name = insert_calls[0]
    assert store_connection is insert_connection
    assert store_report is report
    assert insert_table_name == "paper_autonomous_investment_ledger_archive"
    load_connection_arg, config_version, ledger_status, limit, load_table_name = (
        load_calls[0]
    )
    assert load_connection_arg is load_connection
    assert config_version == "paper-autonomous-investment-ledger-v0"
    assert ledger_status == "watch"
    assert limit == 10
    assert load_table_name == "paper_autonomous_investment_ledger_archive"
    assert insert_connection.commit_count == 1
    assert insert_connection.rollback_count == 0
    assert insert_connection.close_count == 1
    assert load_connection.commit_count == 1
    assert load_connection.rollback_count == 0
    assert load_connection.close_count == 1


def test_config_entrypoints_reject_invalid_config_report_and_dsn_before_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []

    with pytest.raises(ValueError, match="SupabasePaperAutonomousInvestmentLedgerConfig"):
        adapter_module.insert_paper_autonomous_investment_ledger_report_from_config(
            object(),
            _report(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: object(),
        )
    with pytest.raises(ValueError, match="PaperAutonomousInvestmentLedgerReport"):
        adapter_module.insert_paper_autonomous_investment_ledger_report_from_config(
            _enabled_config(),
            object(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: object(),
        )
    with pytest.raises(ValueError, match="DSN"):
        adapter_module.load_paper_autonomous_investment_ledger_reports_from_config(
            _unchecked_config(dsn=None),
            connect=lambda dsn: connect_calls.append(dsn),
            load_reports=lambda *args, **kwargs: (),
        )

    assert connect_calls == []


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_insert_config_entrypoint_rejects_false_report_flags_before_connecting(
    adapter_module: types.ModuleType,
    flag_name: str,
) -> None:
    connect_calls: list[str] = []

    with pytest.raises(ValueError, match=flag_name):
        adapter_module.insert_paper_autonomous_investment_ledger_report_from_config(
            _enabled_config(),
            _unchecked_report(**{flag_name: False}),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: object(),
        )

    assert connect_calls == []


def test_with_psycopg_opens_owned_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    insert_connection = FakeConnection()
    load_connection = FakeConnection()
    report = _report()
    expected_insert = object()
    expected_reports = (report,)
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, PaperAutonomousInvestmentLedgerReport, str]] = []
    load_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        if len(connect_calls) == 1:
            return insert_connection
        return load_connection

    _install_fake_psycopg(monkeypatch, connect=connect)

    def insert_report(
        connection_arg: Any,
        report_arg: PaperAutonomousInvestmentLedgerReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_insert

    def load_reports(
        connection_arg: Any,
        *,
        config_version: str | None,
        ledger_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperAutonomousInvestmentLedgerReport, ...]:
        load_calls.append(
            (connection_arg, config_version, ledger_status, limit, table_name),
        )
        return expected_reports

    insert_result = (
        adapter_module.insert_paper_autonomous_investment_ledger_report_with_psycopg(
            SECRET_DSN,
            report,
            table_name="paper_autonomous_investment_ledger_archive",
            insert_report=insert_report,
        )
    )
    load_result = adapter_module.load_paper_autonomous_investment_ledger_reports_with_psycopg(
        SECRET_DSN,
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
        limit=10,
        table_name="paper_autonomous_investment_ledger_archive",
        load_reports=load_reports,
    )

    assert insert_result is expected_insert
    assert load_result == expected_reports
    assert connect_calls == [SECRET_DSN, SECRET_DSN]
    store_connection, store_report, insert_table_name = insert_calls[0]
    assert store_connection is not insert_connection
    assert store_connection.connection is insert_connection
    assert store_report is report
    assert insert_table_name == "paper_autonomous_investment_ledger_archive"
    load_connection_arg, config_version, ledger_status, limit, load_table_name = (
        load_calls[0]
    )
    assert load_connection_arg is not load_connection
    assert load_connection_arg.connection is load_connection
    assert config_version == "paper-autonomous-investment-ledger-v0"
    assert ledger_status == "watch"
    assert limit == 10
    assert load_table_name == "paper_autonomous_investment_ledger_archive"
    assert insert_connection.commit_count == 1
    assert insert_connection.rollback_count == 0
    assert insert_connection.close_count == 1
    assert load_connection.commit_count == 1
    assert load_connection.rollback_count == 0
    assert load_connection.close_count == 1


def test_load_with_psycopg_default_path_reconstructs_reports_via_store_and_db_row_codec(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    report = _report()
    connection = FakeCursorConnection(rows=(_db_record_from_report(report),))
    connect_calls: list[str] = []

    def connect(dsn: str) -> FakeCursorConnection:
        connect_calls.append(dsn)
        return connection

    _install_fake_psycopg(monkeypatch, connect=connect)

    result = adapter_module.load_paper_autonomous_investment_ledger_reports_with_psycopg(
        SECRET_DSN,
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
        limit=10,
        table_name="paper_autonomous_investment_ledger_archive",
    )

    assert result == (report,)
    loaded = result[0]
    assert type(loaded) is PaperAutonomousInvestmentLedgerReport
    assert loaded.paper_only is True
    assert loaded.report_only is True
    assert loaded.readonly is True
    assert all(entry.paper_only is True for entry in loaded.entries)
    assert all(entry.report_only is True for entry in loaded.entries)
    assert all(entry.readonly is True for entry in loaded.entries)
    assert all(row.paper_only is True for row in loaded.reason_code_counts)
    assert all(row.report_only is True for row in loaded.reason_code_counts)
    assert all(row.readonly is True for row in loaded.reason_code_counts)
    assert connect_calls == [SECRET_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    sql, params = connection.cursor_instance.calls[0]
    assert "SELECT" in sql
    for column_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "ledger_status",
        "recommended_next_step",
        "source_record_count",
        "submitted_count",
        "held_count",
        "blocked_count",
        "total_submitted_notional",
        "held_zero_notional_count",
        "blocked_zero_notional_count",
        "latest_generated_at",
        "latest_age_seconds",
        "reason_code_counts",
        "entries",
        "reason_codes",
        "payload",
        "paper_only",
        "report_only",
        "readonly",
    ):
        assert column_name in sql
    assert "FROM paper_autonomous_investment_ledger_archive" in sql
    assert "WHERE config_version = %s AND ledger_status = %s" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert "LIMIT %s" in sql
    assert params == ("paper-autonomous-investment-ledger-v0", "watch", 10)
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_cursor_wraps_dict_and_list_params_in_jsonb_only(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_report(
        connection_arg: Any,
        report_arg: PaperAutonomousInvestmentLedgerReport,
        *,
        table_name: str,
    ) -> object:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    ["paper_autonomous_investment_ledger_held_records_present"],
                    Decimal("42.500000"),
                    "watch",
                    2,
                    None,
                ),
            )
            assert cursor.rowcount == 1
        finally:
            cursor.close()
        return object()

    adapter_module.insert_paper_autonomous_investment_ledger_report_with_psycopg(
        SECRET_DSN,
        _report(),
        insert_report=insert_report,
    )

    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == [
        "paper_autonomous_investment_ledger_held_records_present",
    ]
    assert params[2] == Decimal("42.500000")
    assert not isinstance(params[2], FakeJsonb)
    assert params[3] == "watch"
    assert params[4] == 2
    assert params[5] is None
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_operation_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def load_reports(
        connection_arg: Any,
        *,
        config_version: str | None,
        ledger_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise ValueError(f"store failed for {SECRET_DSN}")

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_autonomous_investment_ledger_reports_with_psycopg(
            SECRET_DSN,
            load_reports=load_reports,
        )

    message = str(exc_info.value)
    assert "<redacted>" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize(
    "connection",
    (
        FakeRollbackFailingConnection(),
        FakeCloseFailingConnection(),
    ),
)
def test_cleanup_failure_does_not_mask_operation_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
    connection: FakeConnection,
) -> None:
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_report(
        connection_arg: Any,
        report_arg: PaperAutonomousInvestmentLedgerReport,
        *,
        table_name: str,
    ) -> object:
        raise ValueError("store failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_autonomous_investment_ledger_report_with_psycopg(
            SECRET_DSN,
            _report(),
            insert_report=insert_report,
        )

    assert str(exc_info.value) == "store failed without dsn"
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_paper_autonomous_investment_ledger_report_with_psycopg(
            SECRET_DSN,
            _report(),
            insert_report=lambda *args, **kwargs: object(),
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_connect_failure_raises_clean_error_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    def fail_connect(dsn: str) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_autonomous_investment_ledger_reports_with_psycopg(
            SECRET_DSN,
            load_reports=lambda *args, **kwargs: (),
        )

    assert "failed to connect" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "example.invalid" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True
    formatted = "".join(
        traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb),
    )
    assert "postgresql://" not in formatted
    assert "secret" not in formatted


def test_missing_psycopg_raises_clean_runtime_error_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_autonomous_investment_ledger_reports_with_psycopg(
            SECRET_DSN,
            load_reports=lambda *args, **kwargs: (),
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
