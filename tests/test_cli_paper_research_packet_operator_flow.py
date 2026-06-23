from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
)
from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityConfig,
)
from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryConfig,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read import (
    PaperStrategyCandidateResearchQueueReadOptions,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_quality_config import (
    PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-research-packet-operator-flow"


def _set_source_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str,
) -> None:
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, table_name)


def _set_packet_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str,
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, table_name)


def _set_quality_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str,
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR, table_name)


def _source_report(name: str, generated_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(name=name, generated_at=generated_at)


def _packet_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        config_version="paper-research-packet-v1",
        input_row_count=3,
        packet_row_count=2,
        included_count=2,
        skipped_count=1,
        high_priority_count=1,
        medium_priority_count=1,
        low_priority_count=0,
        packet_rows=(
            SimpleNamespace(
                packet_rank=1,
                market_slug="market-alpha",
                side="yes",
                research_priority="high",
                recommendation_score=Decimal("0.910000"),
                net_edge=Decimal("0.080000"),
                allocated_notional=Decimal("12.500000"),
                requested_notional=Decimal("15.000000"),
                reason_codes=("positive_edge", "settlement_review"),
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _quality_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
        quality_status="watch",
        source_generated_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        source_age_seconds=1800,
        included_share=Decimal("0.666667"),
        skipped_share=Decimal("0.333333"),
        check_count=3,
        pass_count=2,
        watch_count=1,
        blocked_count=0,
        check_rows=(
            SimpleNamespace(check_name="source_freshness", status="pass"),
            SimpleNamespace(check_name="packet_population", status="pass"),
            SimpleNamespace(check_name="skip_pressure", status="watch"),
        ),
        reason_code_counts=(
            SimpleNamespace(reason_code="positive_edge", count=2),
            SimpleNamespace(reason_code="skipped_share_above_threshold", count=1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 13, 0, tzinfo=UTC),
        history_status="pass",
        source_report_count=4,
        first_source_generated_at=datetime(2026, 6, 23, 9, 0, tzinfo=UTC),
        latest_source_generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
        latest_quality_status="watch",
        latest_source_age_seconds=1800,
        latest_included_share=Decimal("0.666667"),
        latest_skipped_share=Decimal("0.333333"),
        duplicate_generated_at_count=0,
        quality_status_rows=(
            SimpleNamespace(quality_status="pass", status_count=3),
            SimpleNamespace(quality_status="watch", status_count=1),
            SimpleNamespace(quality_status="blocked", status_count=0),
        ),
        latest_check_rows=(
            SimpleNamespace(check_name="source_freshness", status="pass"),
            SimpleNamespace(check_name="packet_population", status="pass"),
            SimpleNamespace(check_name="skip_pressure", status="watch"),
        ),
        recurring_reason_code_rows=(),
        reason_codes=("paper_research_packet_quality_history_passed",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_operator_flow_cli_uses_injected_helpers_persists_reports_and_prints_status_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://operator-flow.example.invalid/source"
    packet_dsn = "postgresql://operator-flow.example.invalid/packet"
    quality_dsn = "postgresql://operator-flow.example.invalid/quality"
    source_table = "strategy_candidate_research_queue_archive"
    packet_table = "paper_research_packet_archive"
    quality_table = "paper_research_packet_quality_archive"
    _set_source_db_env(monkeypatch, source_dsn, table_name=source_table)
    _set_packet_db_env(monkeypatch, packet_dsn, table_name=packet_table)
    _set_quality_db_env(monkeypatch, quality_dsn, table_name=quality_table)

    older_source = _source_report("older", datetime(2026, 6, 23, 10, 0, tzinfo=UTC))
    latest_source = _source_report("latest", datetime(2026, 6, 23, 11, 0, tzinfo=UTC))
    packet_report = _packet_report()
    quality_report = _quality_report()
    history_report = _history_report()
    events: list[str] = []
    loader_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []
    packet_sink_calls: list[dict[str, object]] = []
    quality_runner_calls: list[dict[str, object]] = []
    quality_insert_calls: list[dict[str, object]] = []
    history_runner_calls: list[dict[str, object]] = []

    class FakeQualityConnection:
        def __init__(self) -> None:
            self.commit_count = 0
            self.rollback_count = 0
            self.close_count = 0

        def commit(self) -> None:
            events.append("commit-quality")
            self.commit_count += 1

        def rollback(self) -> None:
            events.append("rollback-quality")
            self.rollback_count += 1

        def close(self) -> None:
            events.append("close-quality")
            self.close_count += 1

    quality_connection = FakeQualityConnection()

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        events.append("load-source")
        loader_calls.append({"dsn": dsn, "options": options})
        return (older_source, latest_source)

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        events.append("build-packet")
        builder_calls.append(
            {
                "source_report": source_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return packet_report

    def fake_packet_sink(*, dsn: str, report: object, table_name: str) -> object:
        events.append("persist-packet")
        packet_sink_calls.append(
            {"dsn": dsn, "report": report, "table_name": table_name},
        )
        return SimpleNamespace(report_sha256="a" * 64)

    def fake_quality_runner(**kwargs: object) -> object:
        events.append("build-quality")
        quality_runner_calls.append(dict(kwargs))
        return quality_report

    def fake_connect(connect_dsn: str, **kwargs: object) -> FakeQualityConnection:
        events.append("connect-quality")
        assert connect_dsn == quality_dsn
        assert kwargs == {}
        return quality_connection

    def fake_quality_insert(
        connection: object,
        report: object,
        *,
        table_name: str,
    ) -> object:
        events.append("persist-quality")
        quality_insert_calls.append(
            {"connection": connection, "report": report, "table_name": table_name},
        )
        return object()

    def fake_history_runner(**kwargs: object) -> object:
        events.append("history")
        history_runner_calls.append(dict(kwargs))
        return history_report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_quality_store."
        "insert_paper_research_packet_quality_report",
        fake_quality_insert,
    )

    exit_code = main(
        [
            COMMAND,
            "--source-config-version",
            "action-gated-strategy-recommendation-queue-v0",
            "--action-status",
            "research_ready",
            "--research-status",
            "ready",
            "--limit",
            "5",
            "--packet-config-version",
            "paper-research-packet-v1",
            "--max-packet-rows",
            "7",
            "--min-score",
            "0.700000",
            "--quality-history-limit",
            "4",
        ],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=fake_packet_sink,
        paper_research_packet_quality_runner=fake_quality_runner,
        paper_research_packet_quality_db_history_runner=fake_history_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(loader_calls) == 1
    assert loader_calls[0]["dsn"] == source_dsn
    read_options = loader_calls[0]["options"]
    assert isinstance(read_options, PaperStrategyCandidateResearchQueueReadOptions)
    assert (
        read_options.source_config_version
        == "action-gated-strategy-recommendation-queue-v0"
    )
    assert read_options.action_status == "research_ready"
    assert read_options.research_status == "ready"
    assert read_options.limit == 5
    assert read_options.table_name == source_table

    assert len(builder_calls) == 1
    assert builder_calls[0]["source_report"] is latest_source
    packet_config = builder_calls[0]["config"]
    assert type(packet_config) is PaperResearchPacketConfig
    assert packet_config.config_version == "paper-research-packet-v1"
    assert packet_config.max_packet_rows == 7
    assert packet_config.min_score == Decimal("0.700000")
    assert packet_config.paper_only is True
    assert packet_config.report_only is True
    assert packet_config.readonly is True
    packet_generated_at = builder_calls[0]["generated_at"]
    assert isinstance(packet_generated_at, datetime)
    assert packet_generated_at.tzinfo is UTC

    assert packet_sink_calls == [
        {"dsn": packet_dsn, "report": packet_report, "table_name": packet_table},
    ]

    assert len(quality_runner_calls) == 1
    assert quality_runner_calls[0]["dsn"] == packet_dsn
    assert quality_runner_calls[0]["table_name"] == packet_table
    quality_config = quality_runner_calls[0]["config"]
    assert type(quality_config) is PaperResearchPacketQualityConfig
    assert quality_config.paper_only is True
    assert quality_config.report_only is True
    assert quality_config.readonly is True
    quality_generated_at = quality_runner_calls[0]["generated_at"]
    assert isinstance(quality_generated_at, datetime)
    assert quality_generated_at.tzinfo is UTC

    assert quality_insert_calls == [
        {
            "connection": quality_connection,
            "report": quality_report,
            "table_name": quality_table,
        },
    ]
    assert quality_connection.commit_count == 1
    assert quality_connection.rollback_count == 0
    assert quality_connection.close_count == 1

    assert len(history_runner_calls) == 1
    assert history_runner_calls[0]["dsn"] == quality_dsn
    assert history_runner_calls[0]["table_name"] == quality_table
    assert history_runner_calls[0]["limit"] == 4
    history_config = history_runner_calls[0]["config"]
    assert type(history_config) is PaperResearchPacketQualityHistoryConfig
    assert history_config.paper_only is True
    assert history_config.report_only is True
    assert history_config.readonly is True
    history_generated_at = history_runner_calls[0]["generated_at"]
    assert isinstance(history_generated_at, datetime)
    assert history_generated_at.tzinfo is UTC

    assert events.index("persist-packet") < events.index("build-quality")
    assert events.index("persist-quality") < events.index("history")
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "packet_persisted=True" in captured.out
    assert "packet_row_count=2" in captured.out
    assert "quality_status=watch" in captured.out
    assert "quality_persisted=True" in captured.out
    assert "history_status=pass" in captured.out
    assert "history_source_report_count=4" in captured.out
    for secret in (
        source_dsn,
        packet_dsn,
        quality_dsn,
        source_table,
        packet_table,
        quality_table,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_operator_flow_cli_redacts_packet_builder_failure_across_all_databases(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = (
        "postgresql://source_user:source-secret@"
        "operator-flow-builder-source-secret.example.invalid/db"
    )
    packet_dsn = (
        "postgresql://packet_user:packet-secret@"
        "operator-flow-builder-packet-secret.example.invalid/db"
    )
    quality_dsn = (
        "postgresql://quality_user:quality-secret@"
        "operator-flow-builder-quality-secret.example.invalid/db"
    )
    source_table = "source_schema.strategy_candidate_research_queue_archive"
    packet_table = "packet_schema.paper_research_packet_archive"
    quality_table = "quality_schema.paper_research_packet_quality_archive"
    payload_json = '{"secret":"builder-payload-json-secret"}'
    question = "Will hidden builder market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_source_db_env(monkeypatch, source_dsn, table_name=source_table)
    _set_packet_db_env(monkeypatch, packet_dsn, table_name=packet_table)
    _set_quality_db_env(monkeypatch, quality_dsn, table_name=quality_table)
    source_report = _source_report("latest", datetime(2026, 6, 23, 11, 0, tzinfo=UTC))
    packet_sink_calls = 0
    quality_calls = 0
    history_calls = 0

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        assert dsn == source_dsn
        assert isinstance(options, PaperStrategyCandidateResearchQueueReadOptions)
        return (source_report,)

    def broken_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        assert type(config) is PaperResearchPacketConfig
        assert generated_at.tzinfo is UTC
        raise RuntimeError(
            f"builder failed source_dsn={source_dsn} source_table={source_table} "
            f"packet_dsn={packet_dsn} packet_table={packet_table} "
            f"quality_dsn={quality_dsn} quality_table={quality_table} "
            "source_schema=source_schema source_tail=strategy_candidate_research_queue_archive "
            "packet_schema=packet_schema packet_tail=paper_research_packet_archive "
            "quality_schema=quality_schema quality_tail=paper_research_packet_quality_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    def forbidden_packet_sink(**kwargs: object) -> object:
        nonlocal packet_sink_calls
        packet_sink_calls += 1
        raise AssertionError("packet sink should not run after builder failure")

    def forbidden_quality_runner(**kwargs: object) -> object:
        nonlocal quality_calls
        quality_calls += 1
        raise AssertionError("quality runner should not run after builder failure")

    def forbidden_history_runner(**kwargs: object) -> object:
        nonlocal history_calls
        history_calls += 1
        raise AssertionError("history runner should not run after builder failure")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=broken_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        paper_research_packet_quality_runner=forbidden_quality_runner,
        paper_research_packet_quality_db_history_runner=forbidden_history_runner,
    )

    assert exit_code == 1
    assert packet_sink_calls == 0
    assert quality_calls == 0
    assert history_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "packet_dsn=<redacted-dsn>" in captured.err
    assert "quality_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "packet_table=<redacted-table>" in captured.err
    assert "quality_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        "source-secret",
        packet_dsn,
        "packet-secret",
        quality_dsn,
        "quality-secret",
        source_table,
        packet_table,
        quality_table,
        "source_schema",
        "packet_schema",
        "quality_schema",
        "strategy_candidate_research_queue_archive",
        "paper_research_packet_archive",
        "paper_research_packet_quality_archive",
        payload_json,
        "builder-payload-json-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_operator_flow_cli_redacts_source_loader_failure_across_all_databases(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = (
        "postgresql://source_user:source-secret@"
        "operator-flow-loader-source-secret.example.invalid/db"
    )
    packet_dsn = (
        "postgresql://packet_user:packet-secret@"
        "operator-flow-loader-packet-secret.example.invalid/db"
    )
    quality_dsn = (
        "postgresql://quality_user:quality-secret@"
        "operator-flow-loader-quality-secret.example.invalid/db"
    )
    source_table = "source_schema.strategy_candidate_research_queue_archive"
    packet_table = "packet_schema.paper_research_packet_archive"
    quality_table = "quality_schema.paper_research_packet_quality_archive"
    payload_json = '{"secret":"loader-payload-json-secret"}'
    question = "Will hidden loader market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_source_db_env(monkeypatch, source_dsn, table_name=source_table)
    _set_packet_db_env(monkeypatch, packet_dsn, table_name=packet_table)
    _set_quality_db_env(monkeypatch, quality_dsn, table_name=quality_table)
    builder_calls = 0
    packet_sink_calls = 0
    quality_calls = 0
    history_calls = 0

    def broken_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        assert dsn == source_dsn
        assert isinstance(options, PaperStrategyCandidateResearchQueueReadOptions)
        raise RuntimeError(
            f"loader failed source_dsn={source_dsn} source_table={source_table} "
            f"packet_dsn={packet_dsn} packet_table={packet_table} "
            f"quality_dsn={quality_dsn} quality_table={quality_table} "
            "source_schema=source_schema source_tail=strategy_candidate_research_queue_archive "
            "packet_schema=packet_schema packet_tail=paper_research_packet_archive "
            "quality_schema=quality_schema quality_tail=paper_research_packet_quality_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    def forbidden_packet_builder(*args: object, **kwargs: object) -> object:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("packet builder should not run after loader failure")

    def forbidden_packet_sink(**kwargs: object) -> object:
        nonlocal packet_sink_calls
        packet_sink_calls += 1
        raise AssertionError("packet sink should not run after loader failure")

    def forbidden_quality_runner(**kwargs: object) -> object:
        nonlocal quality_calls
        quality_calls += 1
        raise AssertionError("quality runner should not run after loader failure")

    def forbidden_history_runner(**kwargs: object) -> object:
        nonlocal history_calls
        history_calls += 1
        raise AssertionError("history runner should not run after loader failure")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=broken_loader,
        paper_research_packet_builder=forbidden_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        paper_research_packet_quality_runner=forbidden_quality_runner,
        paper_research_packet_quality_db_history_runner=forbidden_history_runner,
    )

    assert exit_code == 1
    assert builder_calls == 0
    assert packet_sink_calls == 0
    assert quality_calls == 0
    assert history_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "packet_dsn=<redacted-dsn>" in captured.err
    assert "quality_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "packet_table=<redacted-table>" in captured.err
    assert "quality_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        "source-secret",
        packet_dsn,
        "packet-secret",
        quality_dsn,
        "quality-secret",
        source_table,
        packet_table,
        quality_table,
        "source_schema",
        "packet_schema",
        "quality_schema",
        "strategy_candidate_research_queue_archive",
        "paper_research_packet_archive",
        "paper_research_packet_quality_archive",
        payload_json,
        "loader-payload-json-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_operator_flow_cli_redacts_packet_sink_failure_across_all_databases(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = (
        "postgresql://source_user:source-secret@"
        "operator-flow-sink-source-secret.example.invalid/db"
    )
    packet_dsn = (
        "postgresql://packet_user:packet-secret@"
        "operator-flow-sink-packet-secret.example.invalid/db"
    )
    quality_dsn = (
        "postgresql://quality_user:quality-secret@"
        "operator-flow-sink-quality-secret.example.invalid/db"
    )
    source_table = "source_schema.strategy_candidate_research_queue_archive"
    packet_table = "packet_schema.paper_research_packet_archive"
    quality_table = "quality_schema.paper_research_packet_quality_archive"
    payload_json = '{"secret":"sink-payload-json-secret"}'
    question = "Will hidden sink market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_source_db_env(monkeypatch, source_dsn, table_name=source_table)
    _set_packet_db_env(monkeypatch, packet_dsn, table_name=packet_table)
    _set_quality_db_env(monkeypatch, quality_dsn, table_name=quality_table)
    source_report = _source_report("latest", datetime(2026, 6, 23, 11, 0, tzinfo=UTC))
    packet_report = _packet_report()
    quality_calls = 0
    history_calls = 0

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        assert dsn == source_dsn
        assert isinstance(options, PaperStrategyCandidateResearchQueueReadOptions)
        return (source_report,)

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        assert type(config) is PaperResearchPacketConfig
        assert generated_at.tzinfo is UTC
        return packet_report

    def broken_packet_sink(*, dsn: str, report: object, table_name: str) -> object:
        assert (dsn, report, table_name) == (packet_dsn, packet_report, packet_table)
        raise RuntimeError(
            f"sink failed source_dsn={source_dsn} source_table={source_table} "
            f"packet_dsn={packet_dsn} packet_table={packet_table} "
            f"quality_dsn={quality_dsn} quality_table={quality_table} "
            "source_schema=source_schema source_tail=strategy_candidate_research_queue_archive "
            "packet_schema=packet_schema packet_tail=paper_research_packet_archive "
            "quality_schema=quality_schema quality_tail=paper_research_packet_quality_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    def forbidden_quality_runner(**kwargs: object) -> object:
        nonlocal quality_calls
        quality_calls += 1
        raise AssertionError("quality runner should not run after packet sink failure")

    def forbidden_history_runner(**kwargs: object) -> object:
        nonlocal history_calls
        history_calls += 1
        raise AssertionError("history runner should not run after packet sink failure")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=broken_packet_sink,
        paper_research_packet_quality_runner=forbidden_quality_runner,
        paper_research_packet_quality_db_history_runner=forbidden_history_runner,
    )

    assert exit_code == 1
    assert quality_calls == 0
    assert history_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "packet_dsn=<redacted-dsn>" in captured.err
    assert "quality_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "packet_table=<redacted-table>" in captured.err
    assert "quality_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        "source-secret",
        packet_dsn,
        "packet-secret",
        quality_dsn,
        "quality-secret",
        source_table,
        packet_table,
        quality_table,
        "source_schema",
        "packet_schema",
        "quality_schema",
        "strategy_candidate_research_queue_archive",
        "paper_research_packet_archive",
        "paper_research_packet_quality_archive",
        payload_json,
        "sink-payload-json-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_operator_flow_cli_redacts_quality_runner_failure_across_all_databases(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = (
        "postgresql://source_user:source-secret@"
        "operator-flow-source-secret.example.invalid/db"
    )
    packet_dsn = (
        "postgresql://packet_user:packet-secret@"
        "operator-flow-packet-secret.example.invalid/db"
    )
    quality_dsn = (
        "postgresql://quality_user:quality-secret@"
        "operator-flow-quality-secret.example.invalid/db"
    )
    source_table = "source_schema.strategy_candidate_research_queue_archive"
    packet_table = "packet_schema.paper_research_packet_archive"
    quality_table = "quality_schema.paper_research_packet_quality_archive"
    payload_json = '{"secret":"payload-json-secret"}'
    question = "Will secret market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_source_db_env(monkeypatch, source_dsn, table_name=source_table)
    _set_packet_db_env(monkeypatch, packet_dsn, table_name=packet_table)
    _set_quality_db_env(monkeypatch, quality_dsn, table_name=quality_table)
    source_report = _source_report("latest", datetime(2026, 6, 23, 11, 0, tzinfo=UTC))
    packet_report = _packet_report()
    history_calls = 0

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        assert dsn == source_dsn
        assert isinstance(options, PaperStrategyCandidateResearchQueueReadOptions)
        return (source_report,)

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        assert type(config) is PaperResearchPacketConfig
        assert generated_at.tzinfo is UTC
        return packet_report

    def fake_packet_sink(*, dsn: str, report: object, table_name: str) -> object:
        assert (dsn, report, table_name) == (packet_dsn, packet_report, packet_table)
        return SimpleNamespace(report_sha256="a" * 64)

    def broken_quality_runner(**kwargs: object) -> object:
        assert kwargs["dsn"] == packet_dsn
        assert kwargs["table_name"] == packet_table
        raise RuntimeError(
            f"quality failed source_dsn={source_dsn} source_table={source_table} "
            f"packet_dsn={packet_dsn} packet_table={packet_table} "
            f"quality_dsn={quality_dsn} quality_table={quality_table} "
            "source_schema=source_schema source_tail=strategy_candidate_research_queue_archive "
            "packet_schema=packet_schema packet_tail=paper_research_packet_archive "
            "quality_schema=quality_schema quality_tail=paper_research_packet_quality_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    def forbidden_history_runner(**kwargs: object) -> object:
        nonlocal history_calls
        history_calls += 1
        raise AssertionError("history runner should not run after quality failure")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=fake_packet_sink,
        paper_research_packet_quality_runner=broken_quality_runner,
        paper_research_packet_quality_db_history_runner=forbidden_history_runner,
    )

    assert exit_code == 1
    assert history_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "packet_dsn=<redacted-dsn>" in captured.err
    assert "quality_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "packet_table=<redacted-table>" in captured.err
    assert "quality_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        "source-secret",
        packet_dsn,
        "packet-secret",
        quality_dsn,
        "quality-secret",
        source_table,
        packet_table,
        quality_table,
        "source_schema",
        "packet_schema",
        "quality_schema",
        "strategy_candidate_research_queue_archive",
        "paper_research_packet_archive",
        "paper_research_packet_quality_archive",
        payload_json,
        "payload-json-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_operator_flow_cli_redacts_history_failure_after_quality_persistence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = (
        "postgresql://source_user:source-secret@"
        "operator-flow-history-source-secret.example.invalid/db"
    )
    packet_dsn = (
        "postgresql://packet_user:packet-secret@"
        "operator-flow-history-packet-secret.example.invalid/db"
    )
    quality_dsn = (
        "postgresql://quality_user:quality-secret@"
        "operator-flow-history-quality-secret.example.invalid/db"
    )
    source_table = "source_schema.strategy_candidate_research_queue_archive"
    packet_table = "packet_schema.paper_research_packet_archive"
    quality_table = "quality_schema.paper_research_packet_quality_archive"
    payload_json = '{"secret":"history-payload-json-secret"}'
    question = "Will hidden history market resolve yes?"
    report_sha256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_source_db_env(monkeypatch, source_dsn, table_name=source_table)
    _set_packet_db_env(monkeypatch, packet_dsn, table_name=packet_table)
    _set_quality_db_env(monkeypatch, quality_dsn, table_name=quality_table)
    source_report = _source_report("latest", datetime(2026, 6, 23, 11, 0, tzinfo=UTC))
    packet_report = _packet_report()
    quality_report = _quality_report()
    events: list[str] = []

    class FakeQualityConnection:
        def __init__(self) -> None:
            self.commit_count = 0
            self.rollback_count = 0
            self.close_count = 0

        def commit(self) -> None:
            events.append("commit-quality")
            self.commit_count += 1

        def rollback(self) -> None:
            events.append("rollback-quality")
            self.rollback_count += 1

        def close(self) -> None:
            events.append("close-quality")
            self.close_count += 1

    quality_connection = FakeQualityConnection()

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        events.append("load-source")
        assert dsn == source_dsn
        assert isinstance(options, PaperStrategyCandidateResearchQueueReadOptions)
        return (source_report,)

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        events.append("build-packet")
        assert type(config) is PaperResearchPacketConfig
        assert generated_at.tzinfo is UTC
        return packet_report

    def fake_packet_sink(*, dsn: str, report: object, table_name: str) -> object:
        events.append("persist-packet")
        assert (dsn, report, table_name) == (packet_dsn, packet_report, packet_table)
        return SimpleNamespace(report_sha256="b" * 64)

    def fake_quality_runner(**kwargs: object) -> object:
        events.append("build-quality")
        assert kwargs["dsn"] == packet_dsn
        assert kwargs["table_name"] == packet_table
        return quality_report

    def fake_connect(connect_dsn: str, **kwargs: object) -> FakeQualityConnection:
        events.append("connect-quality")
        assert connect_dsn == quality_dsn
        assert kwargs == {}
        return quality_connection

    def fake_quality_insert(
        connection: object,
        report: object,
        *,
        table_name: str,
    ) -> object:
        events.append("persist-quality")
        assert connection is quality_connection
        assert report is quality_report
        assert table_name == quality_table
        return object()

    def broken_history_runner(**kwargs: object) -> object:
        events.append("history")
        assert kwargs["dsn"] == quality_dsn
        assert kwargs["table_name"] == quality_table
        raise RuntimeError(
            f"history failed source_dsn={source_dsn} source_table={source_table} "
            f"packet_dsn={packet_dsn} packet_table={packet_table} "
            f"quality_dsn={quality_dsn} quality_table={quality_table} "
            "source_schema=source_schema source_tail=strategy_candidate_research_queue_archive "
            "packet_schema=packet_schema packet_tail=paper_research_packet_archive "
            "quality_schema=quality_schema quality_tail=paper_research_packet_quality_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_quality_store."
        "insert_paper_research_packet_quality_report",
        fake_quality_insert,
    )

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=fake_packet_sink,
        paper_research_packet_quality_runner=fake_quality_runner,
        paper_research_packet_quality_db_history_runner=broken_history_runner,
    )

    assert exit_code == 1
    assert events == [
        "load-source",
        "build-packet",
        "persist-packet",
        "build-quality",
        "connect-quality",
        "persist-quality",
        "commit-quality",
        "close-quality",
        "history",
    ]
    assert quality_connection.commit_count == 1
    assert quality_connection.rollback_count == 0
    assert quality_connection.close_count == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "packet_dsn=<redacted-dsn>" in captured.err
    assert "quality_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "packet_table=<redacted-table>" in captured.err
    assert "quality_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        "source-secret",
        packet_dsn,
        "packet-secret",
        quality_dsn,
        "quality-secret",
        source_table,
        packet_table,
        quality_table,
        "source_schema",
        "packet_schema",
        "quality_schema",
        "strategy_candidate_research_queue_archive",
        "paper_research_packet_archive",
        "paper_research_packet_quality_archive",
        payload_json,
        "history-payload-json-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err
