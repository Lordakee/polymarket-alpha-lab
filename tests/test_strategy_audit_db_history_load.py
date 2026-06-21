from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.strategy_audit_db_history_load as db_history_load
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "strategy-audit-db-history-load-v0"
ALL_GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)


def _audit_report(
    status: str,
    *,
    generated_at: datetime,
) -> PaperStrategyRiskAuditReport:
    status_map = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = status_map[status]
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=tuple(
            PaperStrategyRiskAuditGateResult(
                gate_name=gate_name,
                status=gate_status,
                message="gate-message",
            )
            for gate_name in ALL_GATE_NAMES
        ),
    )


def test_load_strategy_audit_db_history_builds_from_store_desc_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, int | None, str]] = []

    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "strategy_risk_audit_reports",
    ) -> tuple[PaperStrategyRiskAuditReport, ...]:
        calls.append((connection_arg, limit, table_name))
        return (
            _audit_report(
                "blocked_by_risk",
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
            ),
            _audit_report(
                "insufficient_evidence",
                generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
            ),
            _audit_report(
                "audit_ready",
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
            ),
        )

    monkeypatch.setattr(
        db_history_load.strategy_risk_audit_store,
        "load_strategy_risk_audit_reports",
        load_reports,
    )

    history = db_history_load.load_strategy_audit_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=connection,
        limit=25,
        table_name="audit.strategy_risk_audit_archive",
    )

    assert calls == [(connection, 25, "audit.strategy_risk_audit_archive")]
    assert history.generated_at == GENERATED_AT
    assert history.config_version == HISTORY_CONFIG_VERSION
    assert history.status == "latest_blocked_by_risk"
    assert history.audit_report_count == 3
    assert history.audit_ready_count == 1
    assert history.insufficient_evidence_count == 1
    assert history.blocked_by_risk_count == 1
    assert history.first_audit_generated_at == datetime(2026, 6, 21, 7, 0, tzinfo=UTC)
    assert history.latest_audit_generated_at == datetime(2026, 6, 21, 9, 0, tzinfo=UTC)
    assert history.latest_audit_status == "blocked_by_risk"
    assert history.latest_failed_gate_names == ALL_GATE_NAMES
    assert history.latest_incomplete_gate_names == ()
    assert history.consecutive_non_ready_count == 2
    assert history.consecutive_blocked_by_risk_count == 1
    assert history.consecutive_insufficient_evidence_count == 0


def test_load_strategy_audit_db_history_preserves_empty_history_readonly_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "strategy_risk_audit_reports",
    ) -> tuple[PaperStrategyRiskAuditReport, ...]:
        return ()

    monkeypatch.setattr(
        db_history_load.strategy_risk_audit_store,
        "load_strategy_risk_audit_reports",
        load_reports,
    )

    history = db_history_load.load_strategy_audit_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
    )

    assert history.status == "empty_audit_history"
    assert history.audit_report_count == 0
    assert history.audit_ready_count == 0
    assert history.insufficient_evidence_count == 0
    assert history.blocked_by_risk_count == 0
    assert history.latest_audit_status is None
    assert history.first_audit_generated_at is None
    assert history.latest_audit_generated_at is None
    assert history.latest_failed_gate_names == ()
    assert history.latest_incomplete_gate_names == ()
    assert history.paper_only is True
    assert history.report_only is True


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
    ),
)
def test_load_strategy_audit_db_history_rejects_unsafe_loaded_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "strategy_risk_audit_reports",
    ) -> tuple[PaperStrategyRiskAuditReport, ...]:
        report = replace(
            _audit_report(
                "audit_ready",
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
            ),
        )
        object.__setattr__(report, flag_name, False)
        return (report,)

    monkeypatch.setattr(
        db_history_load.strategy_risk_audit_store,
        "load_strategy_risk_audit_reports",
        load_reports,
    )

    with pytest.raises(ValueError, match=message):
        db_history_load.load_strategy_audit_db_history_report(
            generated_at=GENERATED_AT,
            config_version=HISTORY_CONFIG_VERSION,
            connection=object(),
        )


def test_strategy_audit_db_history_load_module_has_no_live_driver_or_cli_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_audit_db_history_load.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

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
