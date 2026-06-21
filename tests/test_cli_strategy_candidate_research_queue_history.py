from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read import (
    PaperStrategyCandidateResearchQueueReadOptions,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_history_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
)


COMMAND = "strategy-candidate-research-queue-history"


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
        source_report_count=3,
        first_source_generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
        action_status_research_ready_count=1,
        action_status_watch_count=1,
        action_status_blocked_count=1,
        research_status_ready_count=1,
        research_status_watch_count=1,
        research_status_blocked_count=1,
        total_ready_notional=Decimal("42.000000"),
        total_selected_notional=Decimal("11.000000"),
        total_suggested_notional=Decimal("23.000000"),
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        latest_research_status="ready",
        latest_top_research_priority_score=Decimal("0.900000"),
        latest_average_research_ready_score=Decimal("0.800000"),
        status_transition_count=2,
        ready_notional_delta=Decimal("12.000000"),
        selected_notional_delta=Decimal("5.000000"),
        latest_selected_count=1,
        latest_skipped_count=1,
        latest_not_selected_count=1,
        latest_primary_reason_code_counts=(("queue_ready", 2), ("manual_review", 1)),
        latest_reason_codes=("queue_ready", "manual_review"),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_strategy_candidate_research_queue_history_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
        raising=False,
    )

    def forbidden_loader(**kwargs: Any) -> object:
        raise AssertionError("read-only loader should not run")

    def forbidden_builder(**kwargs: Any) -> object:
        raise AssertionError("history builder should not run")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=forbidden_loader,
        strategy_candidate_research_queue_history_builder=forbidden_builder,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        "requires strategy candidate research queue read-only DB config to be enabled"
        in captured.err
    )


def test_strategy_candidate_research_queue_history_cli_uses_injected_loader_and_builder(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://candidate-queue-history.example.invalid/db"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
        "strategy_candidate_research_queue_archive",
    )

    source_reports = (
        SimpleNamespace(payload_json={"raw": "history-payload-secret-marker"}),
        SimpleNamespace(payload_json={"raw": "history-second-payload-secret"}),
    )
    loader_calls: list[tuple[str, object]] = []
    builder_calls: list[tuple[object, datetime]] = []

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        loader_calls.append((dsn, options))
        return source_reports

    def fake_history_builder(
        reports: object,
        *,
        generated_at: datetime,
    ) -> object:
        builder_calls.append((reports, generated_at))
        return _history_report()

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
            "25",
        ],
        strategy_candidate_research_queue_loader=fake_loader,
        strategy_candidate_research_queue_history_builder=fake_history_builder,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(loader_calls) == 1
    assert loader_calls[0][0] == source_dsn
    read_options = loader_calls[0][1]
    assert isinstance(read_options, PaperStrategyCandidateResearchQueueReadOptions)
    assert (
        read_options.source_config_version
        == "action-gated-strategy-recommendation-queue-v0"
    )
    assert read_options.action_status == "research_ready"
    assert read_options.research_status == "ready"
    assert read_options.limit == 25
    assert read_options.table_name == "strategy_candidate_research_queue_archive"
    assert builder_calls == [(source_reports, builder_calls[0][1])]

    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "source_report_count=3" in captured.out
    assert "first_source_generated_at=2026-06-21T08:00:00+00:00" in captured.out
    assert "last_source_generated_at=2026-06-21T10:00:00+00:00" in captured.out
    assert "action_status_research_ready_count=1" in captured.out
    assert "action_status_watch_count=1" in captured.out
    assert "action_status_blocked_count=1" in captured.out
    assert "research_status_ready_count=1" in captured.out
    assert "research_status_watch_count=1" in captured.out
    assert "research_status_blocked_count=1" in captured.out
    assert "total_ready_notional=42.000000" in captured.out
    assert "total_selected_notional=11.000000" in captured.out
    assert "total_suggested_notional=23.000000" in captured.out
    assert "latest_action_status=research_ready" in captured.out
    assert "latest_recommended_next_step=review_candidate_research_queue" in (
        captured.out
    )
    assert "latest_research_status=ready" in captured.out
    assert "latest_top_research_priority_score=0.900000" in captured.out
    assert "latest_average_research_ready_score=0.800000" in captured.out
    assert "status_transition_count=2" in captured.out
    assert "ready_notional_delta=12.000000" in captured.out
    assert "selected_notional_delta=5.000000" in captured.out
    assert "latest_selected_count=1" in captured.out
    assert "latest_skipped_count=1" in captured.out
    assert "latest_not_selected_count=1" in captured.out
    assert "latest_primary_reason_code_counts=queue_ready=2,manual_review=1" in (
        captured.out
    )
    assert "latest_reason_codes=queue_ready,manual_review" in captured.out
    assert "persisted=False" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err


def test_strategy_candidate_research_queue_history_cli_redacts_source_dsn_on_loader_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://candidate-queue-history.example.invalid/source"
    source_table = "strategy_candidate_research_queue_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    calls: list[str] = []

    def broken_loader(dsn: str, *, options: object) -> object:
        calls.append("loader")
        raise RuntimeError(
            f"failed to read source reports from {dsn} table={source_table}",
        )

    def forbidden_builder(*args: Any, **kwargs: Any) -> object:
        calls.append("builder")
        raise AssertionError("history builder should not run")

    def forbidden_sink(*args: Any, **kwargs: Any) -> object:
        calls.append("sink")
        raise AssertionError("history sink should not run")

    def forbidden_client_factory() -> object:
        calls.append("client_factory")
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=broken_loader,
        strategy_candidate_research_queue_history_builder=forbidden_builder,
        strategy_candidate_research_queue_history_db_sink=forbidden_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert calls == ["loader"]
    captured = capsys.readouterr()
    assert (
        f"{COMMAND} failed: failed to read source reports from <redacted-dsn> "
        "table=<redacted-table>"
        in captured.err
    )
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert source_table not in captured.out
    assert source_table not in captured.err


def test_strategy_candidate_research_queue_history_cli_persists_built_report_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://candidate-queue-history.example.invalid/source"
    history_dsn = "postgresql://candidate-queue-history.example.invalid/history"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
        "strategy_candidate_research_queue_archive",
    )
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR,
        history_dsn,
    )
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
        "strategy_candidate_research_queue_history_archive",
    )

    source_reports = (SimpleNamespace(payload_json={"raw": "secret"}),)
    history_report = _history_report()
    loader_calls: list[tuple[str, object]] = []
    builder_calls: list[tuple[object, datetime]] = []
    sink_calls: list[tuple[str, object, str]] = []

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        loader_calls.append((dsn, options))
        return source_reports

    def fake_history_builder(
        reports: object,
        *,
        generated_at: datetime,
    ) -> object:
        builder_calls.append((reports, generated_at))
        return history_report

    def fake_history_sink(*, dsn: str, report: object, table_name: str) -> object:
        sink_calls.append((dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

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
            "--persist",
        ],
        strategy_candidate_research_queue_loader=fake_loader,
        strategy_candidate_research_queue_history_builder=fake_history_builder,
        strategy_candidate_research_queue_history_db_sink=fake_history_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert loader_calls[0][0] == source_dsn
    assert builder_calls == [(source_reports, builder_calls[0][1])]
    assert sink_calls == [
        (
            history_dsn,
            history_report,
            "strategy_candidate_research_queue_history_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "persisted=True" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err
    assert "strategy_candidate_research_queue_history_archive" not in captured.out


def test_strategy_candidate_research_queue_history_cli_requires_history_db_when_persisting_redacted(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://candidate-queue-history.example.invalid/source"
    history_dsn = "postgresql://candidate-queue-history.example.invalid/history"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.delenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR,
        history_dsn,
    )
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def forbidden_loader(*args: Any, **kwargs: Any) -> object:
        calls.append(("loader", args, kwargs))
        raise AssertionError("source loader should not run")

    def forbidden_builder(*args: Any, **kwargs: Any) -> object:
        calls.append(("builder", args, kwargs))
        raise AssertionError("history builder should not run")

    def forbidden_sink(*args: Any, **kwargs: Any) -> object:
        calls.append(("sink", args, kwargs))
        raise AssertionError("history sink should not run")

    exit_code = main(
        [COMMAND, "--persist"],
        strategy_candidate_research_queue_loader=forbidden_loader,
        strategy_candidate_research_queue_history_builder=forbidden_builder,
        strategy_candidate_research_queue_history_db_sink=forbidden_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert calls == []
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "history DB to be enabled" in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err


def test_strategy_candidate_research_queue_history_cli_redacts_dsns_on_sink_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://candidate-queue-history.example.invalid/source"
    history_dsn = "postgresql://candidate-queue-history.example.invalid/history"
    source_table = "strategy_candidate_research_queue_archive"
    history_table = "strategy_candidate_research_queue_history_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR,
        history_dsn,
    )
    monkeypatch.setenv(
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
        history_table,
    )

    source_reports = (SimpleNamespace(payload_json={"raw": "secret"}),)
    history_report = _history_report()

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        return source_reports

    def fake_history_builder(
        reports: object,
        *,
        generated_at: datetime,
    ) -> object:
        return history_report

    def broken_history_sink(*, dsn: str, report: object, table_name: str) -> object:
        raise RuntimeError(
            f"source={source_dsn} history={history_dsn} "
            f"source_table={source_table} history_table={history_table} "
            f"sink_table={table_name}",
        )

    exit_code = main(
        [COMMAND, "--persist"],
        strategy_candidate_research_queue_loader=fake_loader,
        strategy_candidate_research_queue_history_builder=fake_history_builder,
        strategy_candidate_research_queue_history_db_sink=broken_history_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        f"{COMMAND} failed: source=<redacted-dsn> history=<redacted-dsn> "
        "source_table=<redacted-table> history_table=<redacted-table> "
        "sink_table=<redacted-table>"
    ) in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err
    assert source_table not in captured.out
    assert source_table not in captured.err
    assert history_table not in captured.out
    assert history_table not in captured.err
