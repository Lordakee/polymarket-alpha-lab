from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module

import pytest


loader = import_module(
    "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_load",
)


GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-operator-flow-db-history-v0",
        "min_report_count": 3,
        "max_blocked_flow_report_count": 0,
        "max_watch_flow_report_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperResearchPacketOperatorFlowDbHistoryConfig(**values)


def test_load_delegates_filters_to_store_and_returns_reducer_report(monkeypatch):
    connection = object()
    config = _config()
    db_descending_reports = ("latest", "earliest")
    expected_report = object()
    store_calls = []
    reducer_calls = []

    def fake_store(
        connection_arg,
        *,
        config_version,
        flow_status,
        limit,
        table_name,
    ):
        store_calls.append(
            {
                "connection": connection_arg,
                "config_version": config_version,
                "flow_status": flow_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return db_descending_reports

    def fake_reducer(operator_flow_reports, *, config, generated_at):
        reducer_calls.append(
            {
                "operator_flow_reports": operator_flow_reports,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_report

    monkeypatch.setattr(
        loader,
        "load_paper_research_packet_operator_flow_reports",
        fake_store,
    )
    monkeypatch.setattr(
        loader,
        "build_paper_research_packet_operator_flow_db_history_report",
        fake_reducer,
    )

    report = loader.load_paper_research_packet_operator_flow_db_history_report(
        connection,
        config_version="paper-research-packet-operator-flow-v0",
        flow_status="watch",
        limit=5,
        table_name="operator_flow_reports_test",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report is expected_report
    assert store_calls == [
        {
            "connection": connection,
            "config_version": "paper-research-packet-operator-flow-v0",
            "flow_status": "watch",
            "limit": 5,
            "table_name": "operator_flow_reports_test",
        },
    ]
    assert reducer_calls == [
        {
            "operator_flow_reports": ("earliest", "latest"),
            "config": config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_load_reverses_db_descending_reports_before_reducer(monkeypatch):
    config = _config()
    captured_reports = []

    def fake_store(
        connection,
        *,
        config_version,
        flow_status,
        limit,
        table_name,
    ):
        return ("latest", "middle", "earliest")

    def fake_reducer(operator_flow_reports, *, config, generated_at):
        captured_reports.append(operator_flow_reports)
        return "history-report"

    monkeypatch.setattr(
        loader,
        "load_paper_research_packet_operator_flow_reports",
        fake_store,
    )
    monkeypatch.setattr(
        loader,
        "build_paper_research_packet_operator_flow_db_history_report",
        fake_reducer,
    )

    report = loader.load_paper_research_packet_operator_flow_db_history_report(
        object(),
        limit=None,
        table_name="operator_flow_reports_test",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report == "history-report"
    assert captured_reports == [("earliest", "middle", "latest")]


def test_load_rejects_non_exact_config_before_store_call(monkeypatch):
    api = _api()

    class ConfigSubclass(api.PaperResearchPacketOperatorFlowDbHistoryConfig):
        pass

    invalid_configs = (
        object(),
        ConfigSubclass(
            config_version="paper-research-packet-operator-flow-db-history-v0",
            min_report_count=3,
            max_blocked_flow_report_count=0,
            max_watch_flow_report_count=0,
            max_duplicate_generated_at_count=0,
        ),
    )

    def fake_store(*args, **kwargs):
        raise AssertionError("store must not be called for invalid config")

    monkeypatch.setattr(
        loader,
        "load_paper_research_packet_operator_flow_reports",
        fake_store,
    )

    for invalid_config in invalid_configs:
        with pytest.raises(
            ValueError,
            match="config must be a PaperResearchPacketOperatorFlowDbHistoryConfig",
        ):
            loader.load_paper_research_packet_operator_flow_db_history_report(
                object(),
                limit=None,
                table_name="operator_flow_reports_test",
                config=invalid_config,
                generated_at=GENERATED_AT,
            )


def test_load_does_not_manage_connection_transaction_or_lifecycle(monkeypatch):
    config = _config()
    calls = []

    class GuardedConnection:
        def cursor(self):
            calls.append("cursor")
            raise AssertionError("loader must not read the DB directly")

        def commit(self):
            calls.append("commit")
            raise AssertionError("loader must not commit")

        def rollback(self):
            calls.append("rollback")
            raise AssertionError("loader must not rollback")

        def close(self):
            calls.append("close")
            raise AssertionError("loader must not close")

    def fake_store(
        connection,
        *,
        config_version,
        flow_status,
        limit,
        table_name,
    ):
        assert isinstance(connection, GuardedConnection)
        return ()

    def fake_reducer(operator_flow_reports, *, config, generated_at):
        assert operator_flow_reports == ()
        return "history-report"

    monkeypatch.setattr(
        loader,
        "load_paper_research_packet_operator_flow_reports",
        fake_store,
    )
    monkeypatch.setattr(
        loader,
        "build_paper_research_packet_operator_flow_db_history_report",
        fake_reducer,
    )

    report = loader.load_paper_research_packet_operator_flow_db_history_report(
        GuardedConnection(),
        config_version=None,
        flow_status=None,
        limit=None,
        table_name="operator_flow_reports_test",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report == "history-report"
    assert calls == []
