from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_research_packet import (
    DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION,
    DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS,
    DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE,
    PaperResearchPacketConfig,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read import (
    PaperStrategyCandidateResearchQueueReadOptions,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-research-packet"


def _source_report(name: str, generated_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(name=name, generated_at=generated_at)


def _packet_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 4, 0, tzinfo=UTC),
        config_version="paper-research-packet-v1",
        input_row_count=3,
        packet_row_count=2,
        included_count=1,
        skipped_count=1,
        high_priority_count=1,
        medium_priority_count=0,
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


def test_paper_research_packet_cli_builds_latest_source_by_generated_at_without_persist(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    packet_dsn = "postgresql://localhost:54322/paper-research-packet_ignored"
    source_table = "strategy_candidate_research_queue_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "not-a-bool")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, packet_dsn)

    older_source = _source_report(
        "older",
        datetime(2026, 6, 23, 3, 0, tzinfo=UTC),
    )
    latest_source = _source_report(
        "latest",
        datetime(2026, 6, 23, 5, 0, tzinfo=UTC),
    )
    packet_report = _packet_report()
    loader_calls: list[tuple[str, object]] = []
    builder_calls: list[tuple[object, PaperResearchPacketConfig, datetime]] = []
    sink_calls: list[dict[str, object]] = []

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        loader_calls.append((dsn, options))
        return (older_source, latest_source)

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        builder_calls.append((source_report, config, generated_at))
        return packet_report

    def forbidden_packet_sink(**kwargs: object) -> object:
        sink_calls.append(kwargs)
        raise AssertionError("paper research packet DB sink should not run")

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
        ],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert loader_calls[0][0] == source_dsn
    read_options = loader_calls[0][1]
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
    source_report, config, generated_at = builder_calls[0]
    assert source_report is latest_source
    assert type(config) is PaperResearchPacketConfig
    assert config.config_version == "paper-research-packet-v1"
    assert config.max_packet_rows == 7
    assert config.min_score == Decimal("0.700000")
    assert generated_at.tzinfo is UTC
    assert sink_calls == []

    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "input_row_count=3" in captured.out
    assert "packet_row_count=2" in captured.out
    assert "high_priority_count=1" in captured.out
    assert "persisted=False" in captured.out
    assert "top_packet: rank=1 market_slug=<redacted-market>" in captured.out
    assert "reason_codes=positive_edge,settlement_review" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert packet_dsn not in captured.out
    assert packet_dsn not in captured.err


def test_paper_research_packet_cli_requires_at_least_one_source_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    source_table = "strategy_candidate_research_queue_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    calls: list[str] = []

    def empty_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        calls.append("loader")
        return ()

    def forbidden_packet_builder(*args: Any, **kwargs: Any) -> object:
        calls.append("builder")
        raise AssertionError("packet builder should not run")

    def forbidden_packet_sink(*args: Any, **kwargs: Any) -> object:
        calls.append("sink")
        raise AssertionError("paper research packet DB sink should not run")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=empty_loader,
        paper_research_packet_builder=forbidden_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert calls == ["loader"]
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "requires at least one source report" in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err


def test_paper_research_packet_cli_persists_packet_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    packet_dsn = "postgresql://localhost:54322/paper-research-packet_packet"
    source_table = "strategy_candidate_research_queue_archive"
    packet_table = "paper_research_packet_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, packet_dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, packet_table)

    source_report = _source_report(
        "latest",
        datetime(2026, 6, 23, 5, 0, tzinfo=UTC),
    )
    packet_report = _packet_report()
    builder_calls: list[tuple[object, PaperResearchPacketConfig, datetime]] = []
    sink_calls: list[tuple[str, object, str]] = []

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        return (source_report,)

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        builder_calls.append((source_report, config, generated_at))
        return packet_report

    def fake_packet_sink(*, dsn: str, report: object, table_name: str) -> object:
        sink_calls.append((dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

    exit_code = main(
        [COMMAND, "--persist"],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=fake_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(builder_calls) == 1
    source_report_arg, config, generated_at = builder_calls[0]
    assert source_report_arg is source_report
    assert type(config) is PaperResearchPacketConfig
    assert config.config_version == DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION
    assert config.max_packet_rows == DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS
    assert config.min_score == DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE
    assert generated_at.tzinfo is UTC
    assert sink_calls == [(packet_dsn, packet_report, packet_table)]
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "persisted=True" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert packet_dsn not in captured.out
    assert packet_dsn not in captured.err
    assert source_table not in captured.out
    assert packet_table not in captured.out


def test_paper_research_packet_cli_requires_packet_db_when_persisting(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    packet_dsn = "postgresql://localhost:54322/paper-research-packet_packet"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, packet_dsn)
    calls: list[str] = []

    def forbidden_loader(*args: Any, **kwargs: Any) -> object:
        calls.append("loader")
        raise AssertionError("source loader should not run")

    def forbidden_packet_builder(*args: Any, **kwargs: Any) -> object:
        calls.append("builder")
        raise AssertionError("packet builder should not run")

    def forbidden_packet_sink(*args: Any, **kwargs: Any) -> object:
        calls.append("sink")
        raise AssertionError("paper research packet DB sink should not run")

    exit_code = main(
        [COMMAND, "--persist"],
        strategy_candidate_research_queue_loader=forbidden_loader,
        paper_research_packet_builder=forbidden_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert calls == []
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "persistence requires packet DB to be enabled" in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert packet_dsn not in captured.out
    assert packet_dsn not in captured.err


def test_paper_research_packet_cli_redacts_source_dsn_on_loader_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    source_table = "strategy_candidate_research_queue_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    calls: list[str] = []

    def broken_loader(dsn: str, *, options: object) -> object:
        calls.append("loader")
        raise RuntimeError(f"read failed dsn={dsn} table={source_table}")

    def forbidden_packet_builder(*args: Any, **kwargs: Any) -> object:
        calls.append("builder")
        raise AssertionError("packet builder should not run")

    def forbidden_packet_sink(*args: Any, **kwargs: Any) -> object:
        calls.append("sink")
        raise AssertionError("paper research packet DB sink should not run")

    exit_code = main(
        [COMMAND],
        strategy_candidate_research_queue_loader=broken_loader,
        paper_research_packet_builder=forbidden_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert calls == ["loader"]
    captured = capsys.readouterr()
    assert (
        f"{COMMAND} failed: read failed dsn=<redacted-dsn> table=<redacted-table>"
        in captured.err
    )
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert source_table not in captured.out
    assert source_table not in captured.err


def test_paper_research_packet_cli_redacts_dsns_and_tables_on_builder_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    packet_dsn = "postgresql://localhost:54322/paper-research-packet_packet"
    source_table = "strategy_candidate_research_queue_archive"
    packet_table = "paper_research_packet_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, packet_dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, packet_table)
    calls: list[str] = []

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        calls.append("loader")
        return (
            _source_report(
                "latest",
                datetime(2026, 6, 23, 5, 0, tzinfo=UTC),
            ),
        )

    def broken_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        calls.append("builder")
        raise RuntimeError(
            f"source={source_dsn} packet={packet_dsn} "
            f"source_table={source_table} packet_table={packet_table}",
        )

    def forbidden_packet_sink(*args: Any, **kwargs: Any) -> object:
        calls.append("sink")
        raise AssertionError("paper research packet DB sink should not run")

    exit_code = main(
        [COMMAND, "--persist"],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=broken_packet_builder,
        paper_research_packet_db_sink=forbidden_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert calls == ["loader", "builder"]
    captured = capsys.readouterr()
    assert (
        f"{COMMAND} failed: source=<redacted-dsn> packet=<redacted-dsn> "
        "source_table=<redacted-table> packet_table=<redacted-table>"
    ) in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert packet_dsn not in captured.out
    assert packet_dsn not in captured.err
    assert source_table not in captured.out
    assert source_table not in captured.err
    assert packet_table not in captured.out
    assert packet_table not in captured.err


def test_paper_research_packet_cli_redacts_dsns_on_sink_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://localhost:54322/paper-research-packet_source"
    packet_dsn = "postgresql://localhost:54322/paper-research-packet_packet"
    source_table = "strategy_candidate_research_queue_archive"
    packet_table = "paper_research_packet_archive"
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR, source_table)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, packet_dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, packet_table)

    def fake_loader(dsn: str, *, options: object) -> tuple[object, ...]:
        return (
            _source_report(
                "latest",
                datetime(2026, 6, 23, 5, 0, tzinfo=UTC),
            ),
        )

    def fake_packet_builder(
        source_report: object,
        *,
        config: PaperResearchPacketConfig,
        generated_at: datetime,
    ) -> object:
        return _packet_report()

    def broken_packet_sink(*, dsn: str, report: object, table_name: str) -> object:
        raise RuntimeError(
            f"source={source_dsn} packet={packet_dsn} "
            f"source_table={source_table} packet_table={packet_table} "
            f"sink_table={table_name}",
        )

    exit_code = main(
        [COMMAND, "--persist"],
        strategy_candidate_research_queue_loader=fake_loader,
        paper_research_packet_builder=fake_packet_builder,
        paper_research_packet_db_sink=broken_packet_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        f"{COMMAND} failed: source=<redacted-dsn> packet=<redacted-dsn> "
        "source_table=<redacted-table> packet_table=<redacted-table> "
        "sink_table=<redacted-table>"
    ) in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert packet_dsn not in captured.out
    assert packet_dsn not in captured.err
    assert source_table not in captured.out
    assert source_table not in captured.err
    assert packet_table not in captured.out
    assert packet_table not in captured.err
