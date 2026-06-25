from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    PaperAutonomousScreeningDecisionSupportGateTransitionReport,
    build_paper_autonomous_screening_decision_support_gate_transition_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_load import (
    load_paper_autonomous_screening_decision_support_gate_transition_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 30, tzinfo=UTC)


@dataclass(frozen=True)
class FakeReport:
    name: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class NoMutationConnection:
    def cursor(self) -> None:
        raise AssertionError("loader must not open cursors directly")

    def commit(self) -> None:
        raise AssertionError("loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("loader must not rollback")

    def close(self) -> None:
        raise AssertionError("loader must not close")

    def execute(self) -> None:
        raise AssertionError("loader must not execute directly")

    def executemany(self) -> None:
        raise AssertionError("loader must not execute directly")

    def insert(self) -> None:
        raise AssertionError("loader must not write")

    def update(self) -> None:
        raise AssertionError("loader must not write")

    def delete(self) -> None:
        raise AssertionError("loader must not write")

    def persist(self) -> None:
        raise AssertionError("loader must not persist")


def _transition_report() -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    return build_paper_autonomous_screening_decision_support_gate_transition_report(
        [
            _gate_report(generated_at=datetime(2026, 6, 22, tzinfo=UTC), gate_status="pass"),
            _gate_report(generated_at=datetime(2026, 6, 23, tzinfo=UTC), gate_status="watch"),
            _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status="blocked"),
        ],
        generated_at=GENERATED_AT,
    )


def test_loader_reads_persisted_gate_reports_newest_first_and_calls_transition_reducer() -> None:
    connection = object()
    earliest = _gate_report(generated_at=datetime(2026, 6, 22, tzinfo=UTC), gate_status="pass")
    middle = _gate_report(generated_at=datetime(2026, 6, 23, tzinfo=UTC), gate_status="watch")
    latest = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status="blocked")
    expected_report = _transition_report()
    gate_loader_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []

    def fake_gate_loader(
        received_connection: object,
        *,
        config_version: str | None,
        gate_status: str | None,
        queue_risk_config_version: str | None,
        operator_flow_gate_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[object, ...]:
        gate_loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "gate_status": gate_status,
                "queue_risk_config_version": queue_risk_config_version,
                "operator_flow_gate_status": operator_flow_gate_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (latest, middle, earliest)

    def fake_transition_builder(
        gate_reports: object,
        *,
        config_version: str,
        generated_at: datetime,
    ) -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
        builder_calls.append(
            {
                "gate_reports": gate_reports,
                "config_version": config_version,
                "generated_at": generated_at,
            },
        )
        return expected_report

    report = load_paper_autonomous_screening_decision_support_gate_transition_report(
        connection,
        screening_gate_config_version="screening-gate-v0",
        screening_gate_status="watch",
        screening_gate_queue_risk_config_version="risk-v0",
        screening_gate_operator_flow_gate_status="pass",
        screening_gate_limit=10,
        screening_gate_table_name="paper_autonomous_screening_gate_archive",
        config_version="paper-autonomous-screening-decision-support-gate-transition-v0",
        generated_at=GENERATED_AT,
        screening_gate_loader=fake_gate_loader,
        transition_report_builder=fake_transition_builder,
    )

    assert report is expected_report
    assert gate_loader_calls == [
        {
            "connection": connection,
            "config_version": "screening-gate-v0",
            "gate_status": "watch",
            "queue_risk_config_version": "risk-v0",
            "operator_flow_gate_status": "pass",
            "limit": 10,
            "table_name": "paper_autonomous_screening_gate_archive",
        },
    ]
    assert builder_calls == [
        {
            "gate_reports": (earliest, middle, latest),
            "config_version": (
                "paper-autonomous-screening-decision-support-gate-transition-v0"
            ),
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_does_not_manage_connection_lifecycle_or_write() -> None:
    connection = NoMutationConnection()
    seen_connections: list[object] = []

    def fake_gate_loader(received_connection: object, **kwargs: object) -> tuple[object, ...]:
        seen_connections.append(received_connection)
        return ()

    report = load_paper_autonomous_screening_decision_support_gate_transition_report(
        connection,
        screening_gate_limit=None,
        screening_gate_table_name="paper_autonomous_screening_gate_reports",
        generated_at=GENERATED_AT,
        screening_gate_loader=fake_gate_loader,
    )

    assert report.gate_report_count == 0
    assert report.transition_count == 0
    assert seen_connections == [connection]


def test_loader_rejects_invalid_loaded_gate_report_flags_before_reducer() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="watch",
    )
    object.__setattr__(gate_report, "readonly", False)
    builder_calls: list[object] = []

    def fake_builder(*args: object, **kwargs: object) -> object:
        builder_calls.append((args, kwargs))
        raise AssertionError("transition builder must not run")

    with pytest.raises(ValueError, match="screening_gate_reports.0 must be readonly"):
        load_paper_autonomous_screening_decision_support_gate_transition_report(
            object(),
            screening_gate_limit=None,
            screening_gate_table_name="paper_autonomous_screening_gate_reports",
            generated_at=GENERATED_AT,
            screening_gate_loader=lambda *args, **kwargs: (gate_report,),
            transition_report_builder=fake_builder,
        )

    assert builder_calls == []


def test_loader_rejects_builder_returning_non_transition_report() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "transition_report_builder output must be a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionReport"
        ),
    ):
        load_paper_autonomous_screening_decision_support_gate_transition_report(
            object(),
            screening_gate_limit=None,
            screening_gate_table_name="paper_autonomous_screening_gate_reports",
            generated_at=GENERATED_AT,
            screening_gate_loader=lambda *args, **kwargs: (),
            transition_report_builder=lambda *args, **kwargs: FakeReport("not-transition"),
        )


def test_loader_rejects_builder_output_with_false_hard_flags() -> None:
    invalid_report = _transition_report()
    object.__setattr__(invalid_report, "readonly", False)

    with pytest.raises(
        ValueError,
        match="transition_report_builder output must be readonly",
    ):
        load_paper_autonomous_screening_decision_support_gate_transition_report(
            object(),
            screening_gate_limit=None,
            screening_gate_table_name="paper_autonomous_screening_gate_reports",
            generated_at=GENERATED_AT,
            screening_gate_loader=lambda *args, **kwargs: (),
            transition_report_builder=lambda *args, **kwargs: invalid_report,
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"generated_at": "2026-06-25T12:30:00Z"}, "generated_at"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " transition-v0"}, "config_version"),
    ),
)
def test_loader_rejects_invalid_inputs_before_source_load(
    kwargs: dict[str, object],
    message: str,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("source loader must not run")

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_screening_decision_support_gate_transition_report(
            object(),
            screening_gate_limit=None,
            screening_gate_table_name="paper_autonomous_screening_gate_reports",
            screening_gate_loader=forbidden,
            **kwargs,
        )


def test_loader_module_has_no_db_lifecycle_live_or_mutation_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_screening_decision_support_gate_transition_load.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    imported_names: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    allowed_modules = {
        "__future__",
        "collections.abc",
        "datetime",
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store",
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition",
    }
    banned_import_names = {
        "append_paper_trade_journal",
        "build_paper_project_screening_report",
        "create_public_client",
        "fetch_live_markets",
        "insert_paper_autonomous_screening_decision_support_gate_transition_report",
        "run_strategy_cycle",
        "run_paper_execution",
    }
    banned_module_names = {
        "polymarket_alpha_lab.auth",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.client",
        "polymarket_alpha_lab.journal",
        "polymarket_alpha_lab.paper_execution",
        "polymarket_alpha_lab.project_screening",
        "polymarket_alpha_lab.strategy_cycle",
    }
    banned_module_fragments = (
        "live",
        "exchange",
        "wallet",
        "account",
        "order",
        "psycopg",
    )
    banned_call_or_attribute_names = {
        "api_key",
        "cancel",
        "close",
        "commit",
        "connect",
        "create_order",
        "cursor",
        "delete",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "persist",
        "private_key",
        "replace_order",
        "rollback",
        "sign",
        "submit",
        "update",
        "wallet",
    }

    assert set(imported_modules) <= allowed_modules
    assert not (set(imported_names) & banned_import_names)
    assert not (set(imported_modules) & banned_module_names)
    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
