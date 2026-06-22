from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_recommendation_risk_budget_db_history_load as db_history_load
from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetReport,
)


GENERATED_AT = datetime(2026, 6, 22, 11, 0, tzinfo=UTC)
BASE_REPORT_AT = datetime(2026, 6, 22, 8, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "risk-budget-db-history-load-v0"


def _report(
    *,
    generated_at: datetime,
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("risk_budget_passed",),
    total_notional_utilization: Decimal | None = Decimal("0.100000"),
    largest_single_recommendation_share: Decimal | None = Decimal("0.050000"),
    selected_count: int = 2,
    total_suggested_notional: Decimal = Decimal("100.000000"),
    nav_notional: Decimal | None = Decimal("1000.000000"),
    max_selected_count: int = 5,
) -> PaperRecommendationRiskBudgetReport:
    if nav_notional is not None and total_notional_utilization is not None:
        total_suggested_notional = (
            nav_notional * total_notional_utilization
        ).quantize(Decimal("0.000001"))
    selected_values = _selected_values(
        total_suggested_notional=total_suggested_notional,
        largest_single_recommendation_share=largest_single_recommendation_share,
        selected_count=selected_count,
        nav_notional=nav_notional,
    )
    return PaperRecommendationRiskBudgetReport(
        generated_at=generated_at,
        config_version="risk-budget-v0",
        status=status,
        reason_codes=reason_codes,
        total_suggested_notional=total_suggested_notional,
        remaining_total_notional=_remaining_total_notional(
            total_suggested_notional,
            nav_notional,
        ),
        total_notional_utilization=total_notional_utilization,
        largest_single_recommendation_share=largest_single_recommendation_share,
        selected_count=selected_count,
        blocked_count=_blocked_count(reason_codes),
        max_total_utilization=Decimal("0.250000"),
        max_single_recommendation_share=Decimal("0.100000"),
        min_remaining_notional=Decimal("0.000000"),
        max_selected_count=max_selected_count,
        selected_position_notional_values=selected_values,
        nav_notional=nav_notional,
    )


def _selected_values(
    *,
    total_suggested_notional: Decimal,
    largest_single_recommendation_share: Decimal | None,
    selected_count: int,
    nav_notional: Decimal | None,
) -> tuple[Decimal, ...]:
    if selected_count == 0:
        return ()
    if nav_notional is not None and largest_single_recommendation_share is not None:
        largest = (nav_notional * largest_single_recommendation_share).quantize(
            Decimal("0.000001"),
        )
    else:
        largest = (total_suggested_notional / Decimal(selected_count)).quantize(
            Decimal("0.000001"),
        )
    if selected_count == 1:
        return (total_suggested_notional,)
    remaining = total_suggested_notional - largest
    tail_count = selected_count - 1
    tail_value = (remaining / Decimal(tail_count)).quantize(Decimal("0.000001"))
    values = [largest, *(tail_value for _ in range(tail_count))]
    values[-1] = total_suggested_notional - sum(values[:-1], Decimal("0.000000"))
    return tuple(values)


def _remaining_total_notional(
    total_suggested_notional: Decimal,
    nav_notional: Decimal | None,
) -> Decimal | None:
    if nav_notional is None:
        return None
    remaining = nav_notional * Decimal("0.250000") - total_suggested_notional
    if remaining < Decimal("0.000000"):
        return Decimal("0.000000")
    return remaining.quantize(Decimal("0.000001"))


def _blocked_count(reason_codes: tuple[str, ...]) -> int:
    blocking_reason_codes = {
        "empty_selection",
        "total_utilization_cap_exceeded",
        "single_recommendation_share_exceeded",
        "min_remaining_notional_breached",
        "max_selected_count_exceeded",
    }
    return sum(1 for reason_code in reason_codes if reason_code in blocking_reason_codes)


def test_load_risk_budget_db_history_builds_from_store_desc_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def load_reports(
        connection_arg: object,
        *,
        config_version: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_risk_budget_reports",
    ) -> tuple[PaperRecommendationRiskBudgetReport, ...]:
        calls.append((connection_arg, config_version, status, limit, table_name))
        return (
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=2),
                status="blocked",
                reason_codes=("max_selected_count_exceeded",),
                total_notional_utilization=Decimal("0.160000"),
                largest_single_recommendation_share=Decimal("0.040000"),
                selected_count=4,
                max_selected_count=3,
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=1),
                status="watch",
                reason_codes=("near_total_utilization_cap",),
                total_notional_utilization=Decimal("0.240000"),
                largest_single_recommendation_share=Decimal("0.080000"),
                selected_count=3,
            ),
            _report(
                generated_at=BASE_REPORT_AT,
                status="pass",
                reason_codes=("risk_budget_passed",),
                total_notional_utilization=Decimal("0.100000"),
                largest_single_recommendation_share=Decimal("0.050000"),
            ),
        )

    monkeypatch.setattr(
        db_history_load.paper_recommendation_risk_budget_store,
        "load_paper_recommendation_risk_budget_reports",
        load_reports,
    )

    history = db_history_load.load_paper_recommendation_risk_budget_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=connection,
        risk_budget_config_version="risk-budget-v0",
        risk_budget_status="blocked",
        limit=25,
        table_name="risk_budget_archive",
    )

    assert calls == [
        (connection, "risk-budget-v0", "blocked", 25, "risk_budget_archive"),
    ]
    assert history.generated_at == GENERATED_AT
    assert history.config_version == HISTORY_CONFIG_VERSION
    assert history.status == "latest_paper_recommendation_risk_budget_blocked"
    assert history.report_count == 3
    assert history.first_report_generated_at == BASE_REPORT_AT
    assert history.latest_report_generated_at == BASE_REPORT_AT + timedelta(minutes=2)
    assert history.latest_status == "blocked"
    assert history.status_counts == (("pass", 1), ("watch", 1), ("blocked", 1))
    assert history.latest_total_notional_utilization == Decimal("0.160000")
    assert history.worst_total_notional_utilization == Decimal("0.240000")
    assert history.latest_largest_single_recommendation_share == Decimal("0.040000")
    assert history.worst_largest_single_recommendation_share == Decimal("0.080000")
    assert history.latest_selected_count == 4
    assert history.latest_blocked_count == 1
    assert history.reason_code_counts == (
        ("max_selected_count_exceeded", 1),
        ("near_total_utilization_cap", 1),
        ("risk_budget_passed", 1),
    )


def test_load_risk_budget_db_history_keeps_empty_history_readonly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        config_version: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_risk_budget_reports",
    ) -> tuple[PaperRecommendationRiskBudgetReport, ...]:
        return ()

    monkeypatch.setattr(
        db_history_load.paper_recommendation_risk_budget_store,
        "load_paper_recommendation_risk_budget_reports",
        load_reports,
    )

    history = db_history_load.load_paper_recommendation_risk_budget_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
    )

    assert history.status == "empty_paper_recommendation_risk_budget_db_history"
    assert history.report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.latest_status is None
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_load_risk_budget_db_history_reverses_store_desc_ties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    same_generated_at = BASE_REPORT_AT + timedelta(minutes=3)

    def load_reports(
        connection_arg: object,
        *,
        config_version: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_risk_budget_reports",
    ) -> tuple[PaperRecommendationRiskBudgetReport, ...]:
        return (
            _report(
                generated_at=same_generated_at,
                status="blocked",
                reason_codes=("max_selected_count_exceeded",),
                largest_single_recommendation_share=Decimal("0.040000"),
                selected_count=4,
                max_selected_count=3,
            ),
            _report(
                generated_at=same_generated_at,
                status="watch",
                reason_codes=("near_total_utilization_cap",),
                total_notional_utilization=Decimal("0.240000"),
                largest_single_recommendation_share=Decimal("0.080000"),
                selected_count=3,
            ),
        )

    monkeypatch.setattr(
        db_history_load.paper_recommendation_risk_budget_store,
        "load_paper_recommendation_risk_budget_reports",
        load_reports,
    )

    history = db_history_load.load_paper_recommendation_risk_budget_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
    )

    assert history.report_count == 2
    assert history.first_report_generated_at == same_generated_at
    assert history.latest_report_generated_at == same_generated_at
    assert history.latest_status == "blocked"
    assert history.latest_selected_count == 4
    assert history.latest_blocked_count == 1
    assert history.duplicate_generated_at_count == 1


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_risk_budget_db_history_rejects_unsafe_loaded_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        config_version: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_risk_budget_reports",
    ) -> tuple[PaperRecommendationRiskBudgetReport, ...]:
        report = replace(_report(generated_at=BASE_REPORT_AT))
        object.__setattr__(report, flag_name, False)
        return (report,)

    monkeypatch.setattr(
        db_history_load.paper_recommendation_risk_budget_store,
        "load_paper_recommendation_risk_budget_reports",
        load_reports,
    )

    with pytest.raises(ValueError, match=message):
        db_history_load.load_paper_recommendation_risk_budget_db_history_report(
            generated_at=GENERATED_AT,
            config_version=HISTORY_CONFIG_VERSION,
            connection=object(),
        )


def test_risk_budget_db_history_load_module_has_no_live_driver_or_cli_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_recommendation_risk_budget_db_history_load.py"
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
