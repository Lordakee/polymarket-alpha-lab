from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)
from polymarket_alpha_lab.paper_research_packet_quality import (
    DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION,
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityConfig,
    PaperResearchPacketQualityReasonCodeCount,
    PaperResearchPacketQualityReport,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-research-packet-quality"
QUALITY_CONFIG_VERSION = DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION


def _set_packet_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_research_packet_archive",
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, table_name)


def _quality_report() -> PaperResearchPacketQualityReport:
    return PaperResearchPacketQualityReport(
        generated_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        config_version=QUALITY_CONFIG_VERSION,
        source_generated_at=datetime(2026, 6, 23, 10, 0, tzinfo=UTC),
        source_config_version="paper-research-packet-v1",
        input_row_count=5,
        packet_row_count=4,
        included_count=3,
        skipped_count=1,
        high_priority_count=1,
        medium_priority_count=1,
        low_priority_count=1,
        source_age_seconds=7200,
        included_share=Decimal("0.750000"),
        skipped_share=Decimal("0.250000"),
        check_count=3,
        pass_count=3,
        watch_count=0,
        blocked_count=0,
        quality_status="pass",
        check_rows=(
            PaperResearchPacketQualityCheckRow(
                check_name="source_freshness",
                status="pass",
                observed_value=7200,
                threshold=21600,
                reason_codes=("source_freshness_passed",),
            ),
            PaperResearchPacketQualityCheckRow(
                check_name="packet_population",
                status="pass",
                observed_value=3,
                threshold=1,
                reason_codes=("packet_population_passed",),
            ),
            PaperResearchPacketQualityCheckRow(
                check_name="skip_pressure",
                status="pass",
                observed_value=Decimal("0.250000"),
                threshold=Decimal("0.500000"),
                reason_codes=("skip_pressure_passed",),
            ),
        ),
        reason_code_counts=(
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="positive_edge",
                count=3,
            ),
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="settlement_review",
                count=2,
            ),
            PaperResearchPacketQualityReasonCodeCount(
                reason_code="packet_population_passed",
                count=1,
            ),
        ),
    )


def _packet_report() -> PaperResearchPacketReport:
    return PaperResearchPacketReport(
        generated_at=datetime(2020, 1, 1, 12, 0, tzinfo=UTC),
        config_version="paper-research-packet-v1",
        input_row_count=1,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows=(
            PaperResearchPacketRow(
                packet_rank=1,
                market_slug="market-alpha",
                question="Will market alpha resolve yes?",
                side="yes",
                research_priority="high",
                required_checks=(
                    "outcome_definition",
                    "liquidity_depth",
                    "cost_sensitivity",
                    "settlement_timing",
                ),
                reason_codes=("positive_edge",),
                recommendation_score=Decimal("0.910000"),
                net_edge=Decimal("0.080000"),
                allocated_notional=Decimal("12.500000"),
                requested_notional=Decimal("15.000000"),
            ),
        ),
    )


def test_packet_quality_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://paper-quality.example.invalid/db"
    table_name = "paper_research_packet_archive"
    _set_packet_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _quality_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert "limit" not in kwargs
        config = kwargs["config"]
        assert type(config) is PaperResearchPacketQualityConfig
        assert config.config_version == QUALITY_CONFIG_VERSION
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND],
        paper_research_packet_quality_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "quality_status=pass" in captured.out
    assert "source_generated_at=2026-06-23T10:00:00+00:00" in captured.out
    assert "source_age_seconds=7200" in captured.out
    assert "included_share=0.750000" in captured.out
    assert "skipped_share=0.250000" in captured.out
    assert "check_count=3" in captured.out
    assert "pass_count=3" in captured.out
    assert "watch_count=0" in captured.out
    assert "blocked_count=0" in captured.out
    assert "checks: source_freshness=pass packet_population=pass skip_pressure=pass" in (
        captured.out
    )
    assert "top_reason_codes: positive_edge=3 settlement_review=2" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err


def test_packet_quality_helper_default_load_path_builds_report_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://paper-quality.example.invalid/db"
    table_name = "paper_research_packet_archive"
    source_report = _packet_report()
    connect_calls: list[tuple[str, bool]] = []
    loader_calls: list[dict[str, object]] = []

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0
            self.commit_count = 0
            self.rollback_count = 0

        def commit(self) -> None:
            self.commit_count += 1
            raise AssertionError("read-only helper must not commit")

        def rollback(self) -> None:
            self.rollback_count += 1
            raise AssertionError("read-only helper must not rollback")

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((connect_dsn, autocommit))
        return connection

    def fake_load(
        received_connection: object,
        *,
        limit: int,
        table_name: str,
    ) -> tuple[PaperResearchPacketReport, ...]:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (source_report,)

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_store."
        "load_paper_research_packet_reports",
        fake_load,
    )

    helper = getattr(cli, "_run_paper_research_packet_quality")
    result = helper(
        dsn=dsn,
        table_name=table_name,
        runner=None,
    )

    assert type(result) is PaperResearchPacketQualityReport
    assert result.source_config_version == "paper-research-packet-v1"
    assert result.input_row_count == 1
    assert result.packet_row_count == 1
    assert result.included_share == Decimal("1.000000")
    assert result.skipped_share == Decimal("0.000000")
    assert connect_calls == [(dsn, True)]
    assert loader_calls == [
        {
            "connection": connection,
            "limit": 1,
            "table_name": table_name,
        },
    ]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_packet_quality_cli_requires_enabled_packet_db_config_before_connect(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    connect_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper research packet quality runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("DB connect should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_research_packet_quality_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires paper research packet DB to be enabled" in captured.err


def test_packet_quality_cli_rejects_limit_flag_before_env_runner_or_connect(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0
    client_factory_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("packet DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper research packet quality runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("DB connect should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    monkeypatch.setattr(cli, "from_paper_research_packet_db_env", forbidden_env)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, "--limit", "0"],
            paper_research_packet_quality_runner=forbidden_runner,
            client_factory=forbidden_client_factory,
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "unrecognized arguments: --limit 0" in captured.err


def test_packet_quality_cli_fails_clearly_when_no_source_packet_available(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://paper-quality-secret.example.invalid/db"
    table_name = "paper_research_packet_archive"
    _set_packet_db_env(monkeypatch, dsn, table_name=table_name)

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        assert connect_dsn == dsn
        assert autocommit is True
        return connection

    def empty_load(
        received_connection: object,
        *,
        limit: int,
        table_name: str,
    ) -> tuple[PaperResearchPacketReport, ...]:
        assert received_connection is connection
        assert limit == 1
        assert table_name == "paper_research_packet_archive"
        return ()

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_store."
        "load_paper_research_packet_reports",
        empty_load,
    )

    exit_code = main([COMMAND])

    assert exit_code == 1
    assert connection.close_count == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "no persisted paper research packet reports found" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err


def test_packet_quality_cli_runner_failure_redacts_dsn_schema_table_and_tail(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://quality_user:super-secret-password@"
        "paper-quality-secret.example.invalid/db"
    )
    table_name = "secret_schema.paper_research_packet_archive"
    payload_json = '{"secret":"payload-json-secret"}'
    question = "Will secret market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    _set_packet_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "schema=secret_schema tail=paper_research_packet_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256}",
        )

    exit_code = main(
        [COMMAND],
        paper_research_packet_quality_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "schema=<redacted-table>" in captured.err
    assert "tail=<redacted-table>" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "super-secret-password" not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
    assert "secret_schema" not in captured.err
    assert "paper_research_packet_archive" not in captured.err
    assert payload_json not in captured.err
    assert "payload-json-secret" not in captured.err
    assert question not in captured.err
    assert report_sha256 not in captured.err
