from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import paper_strategy_cycle_report_db_history as db_history
from polymarket_alpha_lab.paper_strategy_cycle_report_db_history import (
    load_paper_strategy_cycle_report_history_report,
)
from polymarket_alpha_lab.paper_strategy_cycle_report_history import (
    PaperStrategyCycleReportHistoryConfig,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


GENERATED_AT = datetime(2026, 6, 29, 16, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _history_config() -> PaperStrategyCycleReportHistoryConfig:
    return PaperStrategyCycleReportHistoryConfig(
        min_report_count=1,
        min_latest_snapshot_ready_share=d("0.000000"),
    )


def _cycle_report(*, generated_at: datetime) -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=1,
        considered_count=0,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(),
        screening_report=None,
        cost_aware_reports=(),
    )


def test_load_paper_strategy_cycle_report_history_delegates_and_reverses_newest_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oldest = _cycle_report(generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC))
    middle = _cycle_report(generated_at=datetime(2026, 6, 29, 10, 0, tzinfo=UTC))
    newest = _cycle_report(generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC))
    connection = object()
    calls: list[tuple[Any, str | None, int | None, str]] = []

    def fake_load_paper_strategy_cycle_reports(
        received_connection: Any,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_strategy_cycle_reports",
    ) -> tuple[PaperStrategyCycleReport, ...]:
        calls.append((received_connection, config_version, limit, table_name))
        return (newest, middle, oldest)

    monkeypatch.setattr(
        db_history.paper_strategy_cycle_report_store,
        "load_paper_strategy_cycle_reports",
        fake_load_paper_strategy_cycle_reports,
    )

    history = load_paper_strategy_cycle_report_history_report(
        generated_at=GENERATED_AT,
        config=_history_config(),
        connection=connection,
        source_config_version="strategy-cycle-v1",
        limit=25,
        table_name="strategy_cycle_report_archive",
    )

    assert calls == [
        (connection, "strategy-cycle-v1", 25, "strategy_cycle_report_archive"),
    ]
    assert history.report_count == 3
    assert history.first_report_generated_at == oldest.generated_at
    assert history.latest_report_generated_at == newest.generated_at


def test_load_paper_strategy_cycle_report_history_rejects_empty_store_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        db_history.paper_strategy_cycle_report_store,
        "load_paper_strategy_cycle_reports",
        lambda *_args, **_kwargs: (),
    )

    with pytest.raises(ValueError, match="no paper strategy cycle reports found"):
        load_paper_strategy_cycle_report_history_report(
            generated_at=GENERATED_AT,
            config=_history_config(),
            connection=object(),
        )


@pytest.mark.parametrize("field_name", ("paper_only", "report_only"))
def test_load_paper_strategy_cycle_report_history_rejects_unsafe_loaded_report_flags(
    field_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _cycle_report(generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC))
    object.__setattr__(report, field_name, False)
    monkeypatch.setattr(
        db_history.paper_strategy_cycle_report_store,
        "load_paper_strategy_cycle_reports",
        lambda *_args, **_kwargs: (report,),
    )

    with pytest.raises(ValueError, match=field_name):
        load_paper_strategy_cycle_report_history_report(
            generated_at=GENERATED_AT,
            config=_history_config(),
            connection=object(),
        )


def test_paper_strategy_cycle_report_db_history_module_scope_stays_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_strategy_cycle_report_db_history.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
    ):
        assert banned not in source.lower()
