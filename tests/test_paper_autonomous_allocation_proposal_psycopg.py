from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


SECRET_DSN = "postgresql://worker:secret@example.invalid/polymarket"
STORE_MODULE_NAME = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_store"
ADAPTER_MODULE_NAME = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg"


@dataclass(frozen=True)
class FakeReport:
    proposal_status: str


@dataclass(frozen=True)
class FakeRow:
    report_sha256: str


@dataclass(frozen=True)
class FakeResult:
    row: FakeRow
    inserted: bool


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


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


def _install_fake_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    *,
    connect: Any,
) -> None:
    psycopg = types.SimpleNamespace(connect=connect)
    json_module = types.SimpleNamespace(Jsonb=FakeJsonb)
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)


def _install_fake_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    insert: Any | None = None,
    insert_with_result: Any | None = None,
    load: Any | None = None,
) -> None:
    store_module = types.ModuleType(STORE_MODULE_NAME)
    store_module.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE = (
        "paper_autonomous_allocation_proposal_reports"
    )
    store_module.insert_paper_autonomous_allocation_proposal_report = (
        insert if insert is not None else _unexpected_store_call("insert")
    )
    store_module.insert_paper_autonomous_allocation_proposal_report_with_result = (
        insert_with_result
        if insert_with_result is not None
        else _unexpected_store_call("insert_with_result")
    )
    store_module.load_paper_autonomous_allocation_proposal_reports = (
        load if load is not None else _unexpected_store_call("load")
    )
    monkeypatch.setitem(sys.modules, STORE_MODULE_NAME, store_module)


def _unexpected_store_call(name: str) -> Any:
    def raise_unexpected_call(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(f"unexpected {name} store call")

    return raise_unexpected_call


def _import_adapter(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _install_fake_store(monkeypatch)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    return importlib.import_module(ADAPTER_MODULE_NAME)


def test_importing_adapter_does_not_import_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    adapter_module = _import_adapter(monkeypatch)

    assert hasattr(
        adapter_module,
        "insert_paper_autonomous_allocation_proposal_report_with_psycopg",
    )


def test_missing_psycopg_error_mentions_install_extra_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_autonomous_allocation_proposal_reports_with_psycopg(
            SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message


def test_successful_insert_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(proposal_status="pass")
    row = FakeRow(report_sha256="a" * 64)
    result = FakeResult(row=row, inserted=True)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, Any, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert_with_result(
        connection_arg: Any,
        report_arg: Any,
        *,
        table_name: str,
    ) -> FakeResult:
        store_calls.append((connection_arg, report_arg, table_name))
        return result

    _install_fake_store(monkeypatch, insert_with_result=fake_insert_with_result)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    inserted = (
        adapter_module.insert_paper_autonomous_allocation_proposal_report_with_psycopg(
            SECRET_DSN,
            report,
            table_name="paper_autonomous_allocation_proposal_archive",
        )
    )

    assert inserted == result
    assert connect_calls == [SECRET_DSN]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "paper_autonomous_allocation_proposal_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_load_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(proposal_status="pass")
    connect_calls: list[str] = []
    store_calls: list[
        tuple[Any, str | None, str | None, str | None, str | None, int | None, str]
    ] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        proposal_status: str | None,
        screening_gate_status: str | None,
        allocation_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append(
            (
                connection_arg,
                config_version,
                proposal_status,
                screening_gate_status,
                allocation_config_version,
                limit,
                table_name,
            ),
        )
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    loaded = adapter_module.load_paper_autonomous_allocation_proposal_reports_with_psycopg(
        SECRET_DSN,
        config_version="paper-autonomous-allocation-proposal-v0",
        proposal_status="pass",
        screening_gate_status="pass",
        allocation_config_version="allocation-v0",
        limit=25,
        table_name="paper_autonomous_allocation_proposal_archive",
    )

    assert loaded == (report,)
    assert connect_calls == [SECRET_DSN]
    (
        store_connection,
        config_version,
        proposal_status,
        screening_gate_status,
        allocation_config_version,
        limit,
        table_name,
    ) = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert config_version == "paper-autonomous-allocation-proposal-v0"
    assert proposal_status == "pass"
    assert screening_gate_status == "pass"
    assert allocation_config_version == "allocation-v0"
    assert limit == 25
    assert table_name == "paper_autonomous_allocation_proposal_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert_with_result(
        connection_arg: Any,
        report_arg: Any,
        *,
        table_name: str,
    ) -> FakeResult:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert_with_result=fake_insert_with_result)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_autonomous_allocation_proposal_report_with_psycopg(
            SECRET_DSN,
            FakeReport(proposal_status="pass"),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCommitFailingConnection()
    report = FakeReport(proposal_status="pass")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        proposal_status: str | None,
        screening_gate_status: str | None,
        allocation_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        assert config_version is None
        assert proposal_status is None
        assert screening_gate_status is None
        assert allocation_config_version is None
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_autonomous_allocation_proposal_reports_with_psycopg(
            SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_connect_failure_raises_redacted_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_connect(dsn: str) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)
    adapter_module = _import_adapter(monkeypatch)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_autonomous_allocation_proposal_reports_with_psycopg(
            SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert exc_info.value.__cause__ is not None
    assert type(exc_info.value.__cause__) is RuntimeError
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message


def test_dict_and_list_params_are_wrapped_in_jsonb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCursorConnection()
    connect_calls: list[str] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert_with_result(
        connection_arg: Any,
        report_arg: Any,
        *,
        table_name: str,
    ) -> FakeResult:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    [{"market_slug": "alpha"}],
                    "scalar",
                    2,
                ),
            )
        finally:
            cursor.close()
        return FakeResult(row=FakeRow(report_sha256="a" * 64), inserted=True)

    _install_fake_store(monkeypatch, insert_with_result=fake_insert_with_result)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    adapter_module.insert_paper_autonomous_allocation_proposal_report_with_psycopg(
        SECRET_DSN,
        FakeReport(proposal_status="pass"),
    )

    assert connect_calls == [SECRET_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == [{"market_slug": "alpha"}]
    assert params[2] == "scalar"
    assert params[3] == 2
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_json_cursor_exposes_rowcount_for_duplicate_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCursorConnection()
    connection.cursor_instance.rowcount = 0

    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert_with_result(
        connection_arg: Any,
        report_arg: Any,
        *,
        table_name: str,
    ) -> FakeResult:
        cursor = connection_arg.cursor()
        try:
            cursor.execute("insert", ())
            return FakeResult(
                row=FakeRow(report_sha256="a" * 64),
                inserted=cursor.rowcount == 1,
            )
        finally:
            cursor.close()

    _install_fake_store(monkeypatch, insert_with_result=fake_insert_with_result)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    result = (
        adapter_module.insert_paper_autonomous_allocation_proposal_report_with_psycopg(
            SECRET_DSN,
            FakeReport(proposal_status="pass"),
        )
    )

    assert result.inserted is False
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_public_exports_include_adapter_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)

    assert adapter_module.__all__ == (
        "insert_paper_autonomous_allocation_proposal_report_with_psycopg",
        "load_paper_autonomous_allocation_proposal_reports_with_psycopg",
    )
