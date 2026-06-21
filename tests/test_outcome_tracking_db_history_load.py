from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.outcome_tracking_db_history_load as db_history_load
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.outcome_freshness import OutcomeFreshnessReport
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "outcome-tracking-db-history-load-v0"


def _observation(
    generated_at: datetime,
    suffix: str,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=generated_at,
        source_packet_id=f"pkt-{suffix}",
        condition_id=f"0x{suffix}",
        token_id=f"tok-{suffix}",
        market_slug=f"market-{suffix}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("1"),
        actual_outcome_value=Decimal("1"),
    )


def _tracking_report(
    *,
    generated_at: datetime,
    total_markets_checked: int,
    resolved_count: int,
    pending_count: int,
    suffix: str,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OutcomeTrackingReport:
    observations = tuple(
        _observation(generated_at, f"{suffix}-{index}")
        for index in range(resolved_count)
    )
    forecast_evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=generated_at,
        )
        if observations
        else None
    )
    return OutcomeTrackingReport(
        generated_at=generated_at,
        config_version="outcome-tracker-v1",
        total_markets_checked=total_markets_checked,
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=forecast_evidence_report,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_load_outcome_tracking_db_history_builds_from_desc_store_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, int | None, str]] = []

    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "outcome_tracking_reports",
    ) -> tuple[OutcomeTrackingReport, ...]:
        calls.append((connection_arg, limit, table_name))
        return (
            _tracking_report(
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
                total_markets_checked=2,
                resolved_count=2,
                pending_count=0,
                suffix="latest",
            ),
            _tracking_report(
                generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
                total_markets_checked=2,
                resolved_count=1,
                pending_count=1,
                suffix="middle",
            ),
            _tracking_report(
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
                total_markets_checked=1,
                resolved_count=0,
                pending_count=1,
                suffix="first",
            ),
        )

    monkeypatch.setattr(
        db_history_load.outcome_tracking_store,
        "load_outcome_tracking_reports",
        load_reports,
    )

    history = db_history_load.load_outcome_tracking_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=connection,
        stale_after_seconds=3_601,
        limit=25,
        table_name="outcome_tracking_archive",
    )

    assert isinstance(history, OutcomeFreshnessReport)
    assert calls == [(connection, 25, "outcome_tracking_archive")]
    assert history.generated_at == GENERATED_AT
    assert history.config_version == HISTORY_CONFIG_VERSION
    assert history.outcome_report_count == 3
    assert history.first_report_generated_at == datetime(2026, 6, 21, 7, 0, tzinfo=UTC)
    assert history.latest_report_generated_at == datetime(2026, 6, 21, 9, 0, tzinfo=UTC)
    assert history.latest_total_markets_checked == 2
    assert history.latest_resolved_count == 2
    assert history.latest_pending_count == 0
    assert history.latest_report_age_seconds == 3600
    assert history.consecutive_pending_count == 0
    assert history.status == "latest_outcomes_fresh"


def test_load_outcome_tracking_db_history_keeps_empty_history_readonly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "outcome_tracking_reports",
    ) -> tuple[OutcomeTrackingReport, ...]:
        return ()

    monkeypatch.setattr(
        db_history_load.outcome_tracking_store,
        "load_outcome_tracking_reports",
        load_reports,
    )

    history = db_history_load.load_outcome_tracking_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
        stale_after_seconds=3600,
    )

    assert history.status == "empty_outcome_history"
    assert history.outcome_report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_outcome_tracking_db_history_rejects_unsafe_loaded_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "outcome_tracking_reports",
    ) -> tuple[OutcomeTrackingReport, ...]:
        report = replace(
            _tracking_report(
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
                total_markets_checked=1,
                resolved_count=1,
                pending_count=0,
                suffix="unsafe",
            ),
        )
        object.__setattr__(report, flag_name, False)
        return (report,)

    monkeypatch.setattr(
        db_history_load.outcome_tracking_store,
        "load_outcome_tracking_reports",
        load_reports,
    )

    with pytest.raises(ValueError, match=message):
        db_history_load.load_outcome_tracking_db_history_report(
            generated_at=GENERATED_AT,
            config_version=HISTORY_CONFIG_VERSION,
            connection=object(),
            stale_after_seconds=3600,
        )


def test_outcome_tracking_db_history_load_module_has_no_live_driver_or_cli_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "outcome_tracking_db_history_load.py"
    )
    module = ast.parse(module_path.read_text())
    imported_modules: set[str] = set()
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                imported_roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            imported_roots.add(node.module.split(".", 1)[0])

    assert "polymarket_alpha_lab.cli" not in imported_modules
    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "click",
        "eth_account",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "websocket",
        "websockets",
    }
