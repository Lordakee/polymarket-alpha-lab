from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class SourceReport:
    source_name: str
    generated_at: datetime = GENERATED_AT
    config_version: str = "source-v0"
    readiness_status: str = "pass"
    recommended_next_step: str = "review_source"
    reason_codes: tuple[str, ...] = ("source_passed",)
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

    def upsert(self) -> None:
        raise AssertionError("loader must not write")

    def persist(self) -> None:
        raise AssertionError("loader must not persist")


def _api():
    import importlib

    return importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_readiness_digest_load",
    )


def _config():
    import importlib

    module = importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_readiness_digest",
    )
    return module.PaperAutonomousReadinessDigestConfig()


def test_digest_loader_composes_injected_loaders_and_digest_reducer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    connection = object()
    config = _config()
    readiness_report = SourceReport("readiness")
    screening_report = SourceReport("screening")
    transition_report = SourceReport("transition")
    allocation_report = SourceReport("allocation")
    agreement_trend_gate_report = SourceReport("agreement_trend_gate")
    ledger_report = SourceReport("ledger")
    expected_digest = object()
    calls: list[tuple[str, object, str, int | None]] = []
    reducer_calls: list[dict[str, object]] = []

    def make_loader(name: str, report: SourceReport):
        def loader(
            received_connection: object,
            *,
            table_name: str,
            limit: int | None,
            generated_at: datetime,
        ) -> SourceReport:
            assert generated_at == GENERATED_AT
            calls.append((name, received_connection, table_name, limit))
            return report

        return loader

    def fake_reducer(
        readiness_report: object,
        *,
        screening_report: object | None = None,
        transition_report: object | None = None,
        allocation_report: object | None = None,
        agreement_trend_gate_report: object | None = None,
        ledger_report: object | None = None,
        config: object,
        generated_at: datetime,
    ) -> object:
        reducer_calls.append(
            {
                "readiness_report": readiness_report,
                "screening_report": screening_report,
                "transition_report": transition_report,
                "allocation_report": allocation_report,
                "agreement_trend_gate_report": agreement_trend_gate_report,
                "ledger_report": ledger_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_digest

    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_readiness_digest_report",
        fake_reducer,
    )

    result = module_under_test.load_paper_autonomous_readiness_digest_report(
        connection,
        readiness_loader=make_loader("readiness", readiness_report),
        readiness_table_name="readiness_reports",
        screening_loader=make_loader("screening", screening_report),
        screening_table_name="screening_reports",
        transition_loader=make_loader("transition", transition_report),
        transition_table_name="transition_reports",
        allocation_loader=make_loader("allocation", allocation_report),
        allocation_table_name="allocation_reports",
        agreement_trend_gate_loader=make_loader(
            "agreement_trend_gate",
            agreement_trend_gate_report,
        ),
        agreement_trend_gate_table_name="agreement_trend_gate_reports",
        ledger_loader=make_loader("ledger", ledger_report),
        ledger_table_name="ledger_reports",
        limit=5,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert result is expected_digest
    assert calls == [
        ("readiness", connection, "readiness_reports", 5),
        ("screening", connection, "screening_reports", 5),
        ("transition", connection, "transition_reports", 5),
        ("allocation", connection, "allocation_reports", 5),
        ("agreement_trend_gate", connection, "agreement_trend_gate_reports", 5),
        ("ledger", connection, "ledger_reports", 5),
    ]
    assert reducer_calls == [
        {
            "readiness_report": readiness_report,
            "screening_report": screening_report,
            "transition_report": transition_report,
            "allocation_report": allocation_report,
            "agreement_trend_gate_report": agreement_trend_gate_report,
            "ledger_report": ledger_report,
            "config": config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_digest_loader_skips_optional_missing_loaders() -> None:
    module_under_test = _api()
    connection = object()
    config = _config()
    readiness_report = SourceReport(
        "readiness",
        config_version="readiness-gate-v0",
        recommended_next_step="allow_paper_autonomous_readiness_review",
        reason_codes=("paper_autonomous_readiness_gate_passed",),
    )

    def readiness_loader(
        received_connection: object,
        *,
        table_name: str,
        limit: int | None,
        generated_at: datetime,
    ) -> SourceReport:
        assert received_connection is connection
        assert table_name == "readiness_reports"
        assert limit is None
        assert generated_at == GENERATED_AT
        return readiness_report

    report = module_under_test.load_paper_autonomous_readiness_digest_report(
        connection,
        readiness_loader=readiness_loader,
        readiness_table_name="readiness_reports",
        limit=None,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report.evidence[0].source_name == "readiness_gate"
    assert tuple(row.source_name for row in report.evidence) == ("readiness_gate",)


def test_digest_loader_rejects_bad_config_and_missing_required_loader() -> None:
    module_under_test = _api()

    with pytest.raises(
        ValueError,
        match="config must be a PaperAutonomousReadinessDigestConfig",
    ):
        module_under_test.load_paper_autonomous_readiness_digest_report(
            object(),
            readiness_loader=lambda *_args, **_kwargs: SourceReport("readiness"),
            readiness_table_name="readiness_reports",
            limit=1,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="readiness_loader is required"):
        module_under_test.load_paper_autonomous_readiness_digest_report(
            object(),
            readiness_loader=None,
            readiness_table_name="readiness_reports",
            limit=1,
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_digest_loader_does_not_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    connection = NoMutationConnection()
    config = _config()
    readiness_report = SourceReport("readiness")
    expected_digest = object()
    loader_calls: list[object] = []

    def readiness_loader(
        received_connection: object,
        *,
        table_name: str,
        limit: int | None,
        generated_at: datetime,
    ) -> SourceReport:
        loader_calls.append(received_connection)
        return readiness_report

    def fake_reducer(
        readiness_report: object,
        *,
        screening_report: object | None = None,
        transition_report: object | None = None,
        allocation_report: object | None = None,
        agreement_trend_gate_report: object | None = None,
        ledger_report: object | None = None,
        config: object,
        generated_at: datetime,
    ) -> object:
        return expected_digest

    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_readiness_digest_report",
        fake_reducer,
    )

    result = module_under_test.load_paper_autonomous_readiness_digest_report(
        connection,
        readiness_loader=readiness_loader,
        readiness_table_name="readiness_reports",
        limit=1,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert result is expected_digest
    assert loader_calls == [connection]


def test_digest_loader_module_has_no_db_lifecycle_env_cli_or_live_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_readiness_digest_load.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    observed_names: set[str] = set()
    banned_names = {
        "psycopg",
        "supabase",
        "environ",
        "migration",
        "commit",
        "rollback",
        "cursor",
        "execute",
        "executemany",
        "insert",
        "update",
        "delete",
        "upsert",
        "persist",
        "auth",
        "client",
        "exchange",
        "network",
        "wallet",
        "account",
        "order",
        "execution",
        "approval",
        "trade",
        "sign",
        "submit",
        "cancel",
        "replace",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                observed_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.add(node.module)
                observed_names.update(node.module.split("."))
            for alias in node.names:
                observed_names.add(alias.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                observed_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                observed_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            observed_names.add(node.attr)
        elif isinstance(node, ast.Name):
            observed_names.add(node.id)

    assert imported_modules <= {
        "__future__",
        "collections.abc",
        "datetime",
        "polymarket_alpha_lab.paper_autonomous_readiness_digest",
    }
    assert not (observed_names & banned_names)
