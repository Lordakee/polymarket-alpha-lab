from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import importlib
import sys
import traceback
import types
from typing import Any

import pytest

from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryReport,
)


SECRET_DSN = "postgresql://selection-history:secret@localhost:54322/db"
REMOTE_DSN = (
    "postgresql://selection-history:remote-token@db.remote-supabase.example/db"
)
REMOTE_HOST = "db.remote-supabase.example"
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.paper_probability_selection_summary_history_psycopg"
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
        raise RuntimeError(f"commit failed for {SECRET_DSN}")


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


def _report() -> PaperProbabilitySelectionSummaryHistoryReport:
    return PaperProbabilitySelectionSummaryHistoryReport(
        generated_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=3,
        first_generated_at=datetime(2026, 6, 22, 10, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 6, 22, 11, 45, tzinfo=UTC),
        history_span_seconds=6300,
        latest_age_seconds=900,
        latest_queue_count=6,
        latest_selected_count=4,
        latest_pending_count=1,
        latest_rejected_count=1,
        latest_skipped_count=1,
        aggregate_queue_count=15,
        aggregate_selected_count=9,
        aggregate_pending_count=3,
        aggregate_rejected_count=3,
        aggregate_skipped_count=2,
        latest_selected_share=Decimal("0.666667"),
        average_selected_share=Decimal("0.600000"),
        distinct_config_versions=("paper-probability-selection-summary-v0",),
        reason_code_counts=(
            ("cost_stress_passed", 6),
            ("source_edge", 5),
            ("watch_selection_rows_present", 4),
        ),
        history_status="watch",
        recommended_next_step="review_probability_selection",
        reason_codes=(
            "latest_selection_has_blocked_rows",
            "latest_selection_has_watch_rows",
        ),
    )


def _enabled_config() -> object:
    from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
        SupabasePaperProbabilitySelectionSummaryHistoryConfig,
    )

    return SupabasePaperProbabilitySelectionSummaryHistoryConfig(
        enabled=True,
        dsn=SECRET_DSN,
        table_name="paper_probability_selection_summary_history_archive",
    )


def _disabled_config() -> object:
    from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
        SupabasePaperProbabilitySelectionSummaryHistoryConfig,
    )

    return SupabasePaperProbabilitySelectionSummaryHistoryConfig(
        enabled=False,
        dsn=None,
        table_name="paper_probability_selection_summary_history_reports",
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
        "insert_paper_probability_selection_summary_history_report_from_config",
        "insert_paper_probability_selection_summary_history_report_with_psycopg",
        "load_paper_probability_selection_summary_history_reports_from_config",
        "load_paper_probability_selection_summary_history_reports_with_psycopg",
    )


def test_disabled_config_returns_none_without_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    insert_calls: list[object] = []
    load_calls: list[object] = []
    config = _disabled_config()

    inserted = (
        adapter_module
        .insert_paper_probability_selection_summary_history_report_from_config(
            config,
            _report(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: insert_calls.append((args, kwargs)),
        )
    )
    loaded = (
        adapter_module
        .load_paper_probability_selection_summary_history_reports_from_config(
            config,
            config_version="paper-probability-selection-summary-history-v0",
            history_status="watch",
            limit=10,
            connect=lambda dsn: connect_calls.append(dsn),
            load_reports=lambda *args, **kwargs: load_calls.append((args, kwargs)),
        )
    )

    assert inserted is None
    assert loaded is None
    assert connect_calls == []
    assert insert_calls == []
    assert load_calls == []


def test_insert_from_enabled_config_uses_dsn_table_connector_and_store_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _report()
    expected_result = object()
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, PaperProbabilitySelectionSummaryHistoryReport, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def insert_report(
        connection_arg: Any,
        report_arg: PaperProbabilitySelectionSummaryHistoryReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_result

    result = (
        adapter_module
        .insert_paper_probability_selection_summary_history_report_from_config(
            _enabled_config(),
            report,
            connect=connect,
            insert_report=insert_report,
        )
    )

    assert result is expected_result
    assert connect_calls == [SECRET_DSN]
    store_connection, store_report, table_name = insert_calls[0]
    assert store_connection is connection
    assert store_report is report
    assert table_name == "paper_probability_selection_summary_history_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_from_enabled_config_uses_dsn_table_filters_and_store_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _report()
    connect_calls: list[str] = []
    load_calls: list[
        tuple[Any, str | None, str | None, int | None, str]
    ] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def load_reports(
        connection_arg: Any,
        *,
        config_version: str | None,
        history_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperProbabilitySelectionSummaryHistoryReport, ...]:
        load_calls.append(
            (
                connection_arg,
                config_version,
                history_status,
                limit,
                table_name,
            ),
        )
        return (report,)

    result = (
        adapter_module
        .load_paper_probability_selection_summary_history_reports_from_config(
            _enabled_config(),
            config_version="paper-probability-selection-summary-history-v0",
            history_status="watch",
            limit=10,
            connect=connect,
            load_reports=load_reports,
        )
    )

    assert result == (report,)
    assert connect_calls == [SECRET_DSN]
    store_connection, config_version, history_status, limit, table_name = load_calls[0]
    assert store_connection is connection
    assert config_version == "paper-probability-selection-summary-history-v0"
    assert history_status == "watch"
    assert limit == 10
    assert table_name == "paper_probability_selection_summary_history_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_config_entrypoints_reject_wrong_config_and_report_before_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []

    with pytest.raises(
        ValueError,
        match="SupabasePaperProbabilitySelectionSummaryHistoryConfig",
    ):
        adapter_module.insert_paper_probability_selection_summary_history_report_from_config(
            object(),
            _report(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: object(),
        )

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryHistoryReport"):
        adapter_module.insert_paper_probability_selection_summary_history_report_from_config(
            _enabled_config(),
            object(),
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: object(),
        )

    with pytest.raises(
        ValueError,
        match="SupabasePaperProbabilitySelectionSummaryHistoryConfig",
    ):
        adapter_module.load_paper_probability_selection_summary_history_reports_from_config(
            object(),
            connect=lambda dsn: connect_calls.append(dsn),
            load_reports=lambda *args, **kwargs: (),
        )

    assert connect_calls == []


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_insert_from_config_rejects_false_report_flags_before_connecting(
    adapter_module: types.ModuleType,
    flag_name: str,
) -> None:
    connect_calls: list[str] = []
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        adapter_module.insert_paper_probability_selection_summary_history_report_from_config(
            _enabled_config(),
            report,
            connect=lambda dsn: connect_calls.append(dsn),
            insert_report=lambda *args, **kwargs: object(),
        )

    assert connect_calls == []


def test_insert_with_psycopg_opens_owned_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _report()
    expected_result = object()
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, PaperProbabilitySelectionSummaryHistoryReport, str]] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def insert_report(
        connection_arg: Any,
        report_arg: PaperProbabilitySelectionSummaryHistoryReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_result

    result = (
        adapter_module
        .insert_paper_probability_selection_summary_history_report_with_psycopg(
            SECRET_DSN,
            report,
            table_name="paper_probability_selection_summary_history_archive",
            insert_report=insert_report,
        )
    )

    assert result is expected_result
    assert connect_calls == [SECRET_DSN]
    store_connection, store_report, table_name = insert_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report is report
    assert table_name == "paper_probability_selection_summary_history_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_with_psycopg_delegates_filters_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _report()
    connect_calls: list[str] = []
    load_calls: list[
        tuple[Any, str | None, str | None, int | None, str]
    ] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def load_reports(
        connection_arg: Any,
        *,
        config_version: str | None,
        history_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperProbabilitySelectionSummaryHistoryReport, ...]:
        load_calls.append(
            (
                connection_arg,
                config_version,
                history_status,
                limit,
                table_name,
            ),
        )
        return (report,)

    loaded = (
        adapter_module
        .load_paper_probability_selection_summary_history_reports_with_psycopg(
            SECRET_DSN,
            config_version="paper-probability-selection-summary-history-v0",
            history_status="watch",
            limit=10,
            table_name="paper_probability_selection_summary_history_archive",
            load_reports=load_reports,
        )
    )

    assert loaded == (report,)
    assert connect_calls == [SECRET_DSN]
    store_connection, config_version, history_status, limit, table_name = load_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert config_version == "paper-probability-selection-summary-history-v0"
    assert history_status == "watch"
    assert limit == 10
    assert table_name == "paper_probability_selection_summary_history_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_success_connection_close_failure_propagates_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCloseFailingConnection()
    report = _report()
    connect_calls: list[str] = []
    load_calls: list[Any] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def load_reports(
        connection_arg: Any,
        *,
        config_version: str | None,
        history_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperProbabilitySelectionSummaryHistoryReport, ...]:
        load_calls.append(connection_arg)
        return (report,)

    with pytest.raises(RuntimeError) as exc_info:
        (
            adapter_module
            .load_paper_probability_selection_summary_history_reports_with_psycopg(
                SECRET_DSN,
                config_version="paper-probability-selection-summary-history-v0",
                history_status="watch",
                table_name="paper_probability_selection_summary_history_archive",
                load_reports=load_reports,
            )
        )

    assert str(exc_info.value) == "close failed without dsn"
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "localhost" not in str(exc_info.value)
    assert "54322" not in str(exc_info.value)
    assert connect_calls == [SECRET_DSN]
    assert load_calls[0] is not connection
    assert load_calls[0].connection is connection
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_remote_dsn_is_rejected_before_psycopg_import_or_connect_without_leak(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)
    connect_calls: list[str] = []

    class RejectingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname.startswith("psycopg"):
                raise AssertionError("psycopg must not be imported for remote DSN")
            return None

    finder = RejectingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_probability_selection_summary_history_reports_with_psycopg(
            REMOTE_DSN,
            connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
        )

    message = str(exc_info.value)
    assert (
        "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN"
        in message
    )
    assert REMOTE_DSN not in message
    assert "remote-token" not in message
    assert REMOTE_HOST not in message
    assert connect_calls == []


def test_default_boundaries_use_history_store_functions(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _report()
    expected_insert = object()
    expected_load = (report,)
    insert_calls: list[tuple[Any, PaperProbabilitySelectionSummaryHistoryReport, str]] = []
    load_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(
        connection_arg: Any,
        report_arg: PaperProbabilitySelectionSummaryHistoryReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_insert

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        history_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[PaperProbabilitySelectionSummaryHistoryReport, ...]:
        load_calls.append(
            (
                connection_arg,
                config_version,
                history_status,
                limit,
                table_name,
            ),
        )
        return expected_load

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_probability_selection_summary_history_report",
        fake_insert,
    )
    monkeypatch.setattr(
        adapter_module,
        "load_paper_probability_selection_summary_history_reports",
        fake_load,
    )

    inserted = (
        adapter_module
        .insert_paper_probability_selection_summary_history_report_with_psycopg(
            SECRET_DSN,
            report,
        )
    )
    loaded = (
        adapter_module
        .load_paper_probability_selection_summary_history_reports_with_psycopg(
            SECRET_DSN,
            history_status="watch",
        )
    )

    assert inserted is expected_insert
    assert loaded == expected_load
    assert insert_calls[0][1] is report
    assert load_calls[0][2] == "watch"


def test_cursor_wraps_dict_and_list_params_in_jsonb_only(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_report(
        connection_arg: Any,
        report_arg: PaperProbabilitySelectionSummaryHistoryReport,
        *,
        table_name: str,
    ) -> object:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    ["latest_selection_has_watch_rows"],
                    Decimal("0.600000"),
                    "watch",
                    3,
                    None,
                ),
            )
            assert cursor.rowcount == 1
        finally:
            cursor.close()
        return object()

    adapter_module.insert_paper_probability_selection_summary_history_report_with_psycopg(
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
    assert params[1].value == ["latest_selection_has_watch_rows"]
    assert params[2] == Decimal("0.600000")
    assert not isinstance(params[2], FakeJsonb)
    assert params[3] == "watch"
    assert params[4] == 3
    assert params[5] is None
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_store_failure_rolls_back_closes_reraises_and_redacts_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def insert_report(
        connection_arg: Any,
        report_arg: PaperProbabilitySelectionSummaryHistoryReport,
        *,
        table_name: str,
    ) -> object:
        raise ValueError(f"store failed for {SECRET_DSN}")

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_selection_summary_history_report_with_psycopg(
            SECRET_DSN,
            _report(),
            insert_report=insert_report,
        )

    message = str(exc_info.value)
    assert "store failed for <redacted>" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message
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

    def insert_report(
        connection_arg: Any,
        report_arg: PaperProbabilitySelectionSummaryHistoryReport,
        *,
        table_name: str,
    ) -> object:
        raise ValueError("store failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_selection_summary_history_report_with_psycopg(
            SECRET_DSN,
            _report(),
            insert_report=insert_report,
        )

    assert str(exc_info.value) == "store failed without dsn"
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_redacts_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_paper_probability_selection_summary_history_report_with_psycopg(
            SECRET_DSN,
            _report(),
            insert_report=lambda *args, **kwargs: object(),
        )

    message = str(exc_info.value)
    assert "commit failed for <redacted>" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message
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
        adapter_module.load_paper_probability_selection_summary_history_reports_with_psycopg(
            SECRET_DSN,
        )

    assert "failed to connect" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "localhost" not in str(exc_info.value)
    assert "54322" not in str(exc_info.value)
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
        adapter_module.load_paper_probability_selection_summary_history_reports_with_psycopg(
            SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
