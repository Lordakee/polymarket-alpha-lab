from __future__ import annotations

import importlib
import sys
import traceback
import types
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord
from polymarket_alpha_lab.supabase_paper_broker_config import (
    SupabasePaperBrokerConfig,
)


SECRET_DSN = "postgresql://worker:secret@example.invalid/polymarket"
ADAPTER_MODULE_NAME = "polymarket_alpha_lab.paper_broker_psycopg"


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
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.close_count = 0
        self.rowcount = 1

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def close(self) -> None:
        self.close_count += 1


class FakeCursorConnection(FakeConnection):
    def __init__(self) -> None:
        super().__init__()
        self.cursor_instance = FakeCursor()
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
    return importlib.import_module(ADAPTER_MODULE_NAME)


def _record() -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=datetime(2026, 6, 25, 12, 30, tzinfo=UTC),
        config_version="paper-broker-v0",
        execution_status="paper_submitted",
        recommended_next_step="route_to_paper_order_lifecycle",
        source_gate_status="pass",
        source_proposal_count=2,
        source_proposal_total_notional=Decimal("42.500000"),
        execution_notional=Decimal("42.500000"),
        reason_codes=("paper_broker_execution_submitted",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _unchecked_record(**overrides: object) -> PaperBrokerExecutionRecord:
    values = dict(_record().__dict__)
    values.update(overrides)
    record = object.__new__(PaperBrokerExecutionRecord)
    for name, value in values.items():
        object.__setattr__(record, name, value)
    return record


def _enabled_config() -> SupabasePaperBrokerConfig:
    return SupabasePaperBrokerConfig(
        enabled=True,
        dsn=SECRET_DSN,
        table_name="paper_broker_execution_archive",
    )


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
        "insert_paper_broker_execution_record_from_config",
        "insert_paper_broker_execution_record_with_psycopg",
    )


def test_disabled_config_returns_none_without_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    insert_calls: list[object] = []
    config = SupabasePaperBrokerConfig(
        enabled=False,
        dsn=None,
        table_name="paper_broker_execution_records",
    )

    result = adapter_module.insert_paper_broker_execution_record_from_config(
        config,
        _record(),
        connect=lambda dsn: connect_calls.append(dsn),
        insert_record=lambda *args, **kwargs: insert_calls.append((args, kwargs)),
    )

    assert result is None
    assert connect_calls == []
    assert insert_calls == []


def test_enabled_config_uses_dsn_table_connector_and_insert_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    record = _record()
    expected_result = object()
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, PaperBrokerExecutionRecord, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def insert_record(
        connection_arg: Any,
        record_arg: PaperBrokerExecutionRecord,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, record_arg, table_name))
        return expected_result

    result = adapter_module.insert_paper_broker_execution_record_from_config(
        _enabled_config(),
        record,
        connect=connect,
        insert_record=insert_record,
    )

    assert result is expected_result
    assert connect_calls == [SECRET_DSN]
    store_connection, store_record, table_name = insert_calls[0]
    assert store_connection is connection
    assert store_record is record
    assert table_name == "paper_broker_execution_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_config_entrypoint_rejects_wrong_config_and_record_before_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []

    with pytest.raises(ValueError, match="SupabasePaperBrokerConfig"):
        adapter_module.insert_paper_broker_execution_record_from_config(
            object(),
            _record(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_record=lambda *args, **kwargs: object(),
        )

    with pytest.raises(ValueError, match="PaperBrokerExecutionRecord"):
        adapter_module.insert_paper_broker_execution_record_from_config(
            _enabled_config(),
            object(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_record=lambda *args, **kwargs: object(),
        )

    assert connect_calls == []


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_config_entrypoint_rejects_false_record_flags_before_connecting(
    adapter_module: types.ModuleType,
    flag_name: str,
) -> None:
    connect_calls: list[str] = []

    with pytest.raises(ValueError, match=flag_name):
        adapter_module.insert_paper_broker_execution_record_from_config(
            _enabled_config(),
            _unchecked_record(**{flag_name: False}),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_record=lambda *args, **kwargs: object(),
        )

    assert connect_calls == []


def test_with_psycopg_opens_owned_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    record = _record()
    expected_result = object()
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, PaperBrokerExecutionRecord, str]] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def insert_record(
        connection_arg: Any,
        record_arg: PaperBrokerExecutionRecord,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, record_arg, table_name))
        return expected_result

    result = adapter_module.insert_paper_broker_execution_record_with_psycopg(
        SECRET_DSN,
        record,
        table_name="paper_broker_execution_archive",
        insert_record=insert_record,
    )

    assert result is expected_result
    assert connect_calls == [SECRET_DSN]
    store_connection, store_record, table_name = insert_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_record is record
    assert table_name == "paper_broker_execution_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_cursor_wraps_dict_and_list_params_in_jsonb_only(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_record(
        connection_arg: Any,
        record_arg: PaperBrokerExecutionRecord,
        *,
        table_name: str,
    ) -> object:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    ["paper_broker_execution_submitted"],
                    Decimal("42.500000"),
                    "paper_submitted",
                    2,
                    None,
                ),
            )
            assert cursor.rowcount == 1
        finally:
            cursor.close()
        return object()

    adapter_module.insert_paper_broker_execution_record_with_psycopg(
        SECRET_DSN,
        _record(),
        insert_record=insert_record,
    )

    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["paper_broker_execution_submitted"]
    assert params[2] == Decimal("42.500000")
    assert not isinstance(params[2], FakeJsonb)
    assert params[3] == "paper_submitted"
    assert params[4] == 2
    assert params[5] is None
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_store_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_record(
        connection_arg: Any,
        record_arg: PaperBrokerExecutionRecord,
        *,
        table_name: str,
    ) -> object:
        raise ValueError("store failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_broker_execution_record_with_psycopg(
            SECRET_DSN,
            _record(),
            insert_record=insert_record,
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
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
def test_cleanup_failure_does_not_mask_store_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
    connection: FakeConnection,
) -> None:
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_record(
        connection_arg: Any,
        record_arg: PaperBrokerExecutionRecord,
        *,
        table_name: str,
    ) -> object:
        raise ValueError("store failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_broker_execution_record_with_psycopg(
            SECRET_DSN,
            _record(),
            insert_record=insert_record,
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
        adapter_module.insert_paper_broker_execution_record_with_psycopg(
            SECRET_DSN,
            _record(),
            insert_record=lambda *args, **kwargs: object(),
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
        adapter_module.insert_paper_broker_execution_record_with_psycopg(
            SECRET_DSN,
            _record(),
            insert_record=lambda *args, **kwargs: object(),
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
        adapter_module.insert_paper_broker_execution_record_with_psycopg(
            SECRET_DSN,
            _record(),
            insert_record=lambda *args, **kwargs: object(),
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
