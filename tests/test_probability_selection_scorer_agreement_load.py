from __future__ import annotations

import ast
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementConfig,
)


GENERATED_AT = datetime(2026, 6, 28, 5, 45, tzinfo=UTC)


class NoLifecycleConnection:
    def cursor(self) -> None:
        raise AssertionError("agreement loader must not open cursors directly")

    def commit(self) -> None:
        raise AssertionError("agreement loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("agreement loader must not rollback")

    def close(self) -> None:
        raise AssertionError("agreement loader must not close")


def _api():
    return import_module(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_load",
    )


def test_loader_public_exports_loader_only() -> None:
    api = _api()

    assert api.__all__ == (
        "load_probability_selection_scorer_agreement_report",
    )


def test_loader_uses_injected_loaders_and_does_not_own_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    selection_connection = NoLifecycleConnection()
    scorer_connection = NoLifecycleConnection()
    config = ProbabilitySelectionScorerAgreementConfig()
    selection_report = object()
    scorer_report = object()
    expected_report = object()
    selection_loader_calls: list[dict[str, object]] = []
    scorer_loader_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []

    def fake_selection_loader(
        received_connection: object,
        *,
        config_version: str | None,
        source_queue_config_version: str | None,
        source_cost_stress_config_version: str | None,
        selection_status: str | None,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        selection_loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "source_queue_config_version": source_queue_config_version,
                "source_cost_stress_config_version": source_cost_stress_config_version,
                "selection_status": selection_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (selection_report,)

    def fake_scorer_loader(
        received_connection: object,
        *,
        config_version: str | None,
        gate_status: str | None,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        scorer_loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "gate_status": gate_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (scorer_report,)

    def fake_builder(
        *,
        selection_input: object | None,
        scorer_input: object | None,
        generated_at: datetime,
        config: ProbabilitySelectionScorerAgreementConfig | None,
    ) -> object:
        builder_calls.append(
            {
                "selection_input": selection_input,
                "scorer_input": scorer_input,
                "generated_at": generated_at,
                "config": config,
            },
        )
        return expected_report

    monkeypatch.setattr(
        module_under_test,
        "build_probability_selection_scorer_agreement_report",
        fake_builder,
    )

    result = module_under_test.load_probability_selection_scorer_agreement_report(
        selection_connection,
        scorer_connection,
        selection_config_version="paper-probability-selection-summary-v0",
        selection_source_queue_config_version="paper-probability-queue-v0",
        selection_source_cost_stress_config_version="paper-cost-stress-v0",
        selection_status="ready",
        scorer_config_version="autonomous-market-scorer-v0",
        scorer_gate_status="pass",
        selection_limit=3,
        scorer_limit=4,
        selection_table_name="paper_probability_selection_summary_archive",
        scorer_table_name="autonomous_market_scorer_archive",
        config=config,
        generated_at=GENERATED_AT,
        selection_report_loader=fake_selection_loader,
        scorer_report_loader=fake_scorer_loader,
    )

    assert result is expected_report
    assert selection_loader_calls == [
        {
            "connection": selection_connection,
            "config_version": "paper-probability-selection-summary-v0",
            "source_queue_config_version": "paper-probability-queue-v0",
            "source_cost_stress_config_version": "paper-cost-stress-v0",
            "selection_status": "ready",
            "limit": 3,
            "table_name": "paper_probability_selection_summary_archive",
        },
    ]
    assert scorer_loader_calls == [
        {
            "connection": scorer_connection,
            "config_version": "autonomous-market-scorer-v0",
            "gate_status": "pass",
            "limit": 4,
            "table_name": "autonomous_market_scorer_archive",
        },
    ]
    assert builder_calls == [
        {
            "selection_input": selection_report,
            "scorer_input": scorer_report,
            "generated_at": GENERATED_AT,
            "config": config,
        },
    ]


def test_loader_uses_none_inputs_when_persisted_sources_are_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    expected_report = object()
    builder_calls: list[dict[str, object]] = []

    def fake_builder(
        *,
        selection_input: object | None,
        scorer_input: object | None,
        generated_at: datetime,
        config: ProbabilitySelectionScorerAgreementConfig | None,
    ) -> object:
        builder_calls.append(
            {
                "selection_input": selection_input,
                "scorer_input": scorer_input,
                "generated_at": generated_at,
                "config": config,
            },
        )
        return expected_report

    monkeypatch.setattr(
        module_under_test,
        "build_probability_selection_scorer_agreement_report",
        fake_builder,
    )

    result = module_under_test.load_probability_selection_scorer_agreement_report(
        object(),
        object(),
        selection_limit=1,
        scorer_limit=1,
        config=None,
        generated_at=GENERATED_AT,
        selection_report_loader=lambda *args, **kwargs: (),
        scorer_report_loader=lambda *args, **kwargs: (),
    )

    assert result is expected_report
    assert builder_calls == [
        {
            "selection_input": None,
            "scorer_input": None,
            "generated_at": GENERATED_AT,
            "config": None,
        },
    ]


def test_loader_default_loaders_delegate_to_store_filters_and_build_agreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    selection_connection = object()
    scorer_connection = object()
    config = ProbabilitySelectionScorerAgreementConfig(
        config_version="agreement-loader-test-v0",
    )
    selection_report = object()
    scorer_report = object()
    expected_report = object()
    selection_loader_calls: list[dict[str, object]] = []
    scorer_loader_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []

    def fake_selection_store_loader(
        received_connection: object,
        *,
        config_version: str | None,
        source_queue_config_version: str | None,
        source_cost_stress_config_version: str | None,
        selection_status: str | None,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        selection_loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "source_queue_config_version": source_queue_config_version,
                "source_cost_stress_config_version": source_cost_stress_config_version,
                "selection_status": selection_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (selection_report,)

    def fake_scorer_store_loader(
        received_connection: object,
        *,
        config_version: str | None,
        gate_status: str | None,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        scorer_loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "gate_status": gate_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (scorer_report,)

    def fake_builder(
        *,
        selection_input: object | None,
        scorer_input: object | None,
        generated_at: datetime,
        config: ProbabilitySelectionScorerAgreementConfig | None,
    ) -> object:
        builder_calls.append(
            {
                "selection_input": selection_input,
                "scorer_input": scorer_input,
                "generated_at": generated_at,
                "config": config,
            },
        )
        return expected_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_probability_selection_summary_reports",
        fake_selection_store_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "load_autonomous_market_scorer_reports",
        fake_scorer_store_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_probability_selection_scorer_agreement_report",
        fake_builder,
    )

    result = module_under_test.load_probability_selection_scorer_agreement_report(
        selection_connection,
        scorer_connection,
        selection_config_version="selection-v0",
        selection_source_queue_config_version="queue-v0",
        selection_source_cost_stress_config_version="stress-v0",
        selection_status="watch",
        scorer_config_version="scorer-v0",
        scorer_gate_status="watch",
        selection_limit=2,
        scorer_limit=5,
        selection_table_name="paper_probability_selection_summary_reports",
        scorer_table_name="autonomous_market_scorer_reports",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert result is expected_report
    assert selection_loader_calls == [
        {
            "connection": selection_connection,
            "config_version": "selection-v0",
            "source_queue_config_version": "queue-v0",
            "source_cost_stress_config_version": "stress-v0",
            "selection_status": "watch",
            "limit": 2,
            "table_name": "paper_probability_selection_summary_reports",
        },
    ]
    assert scorer_loader_calls == [
        {
            "connection": scorer_connection,
            "config_version": "scorer-v0",
            "gate_status": "watch",
            "limit": 5,
            "table_name": "autonomous_market_scorer_reports",
        },
    ]
    assert builder_calls == [
        {
            "selection_input": selection_report,
            "scorer_input": scorer_report,
            "generated_at": GENERATED_AT,
            "config": config,
        },
    ]


def test_loader_rejects_non_exact_agreement_config_before_reading() -> None:
    api = _api()
    selection_calls: list[object] = []
    scorer_calls: list[object] = []

    def fake_selection_loader(*args: object, **kwargs: object) -> tuple[object, ...]:
        selection_calls.append((args, kwargs))
        return ()

    def fake_scorer_loader(*args: object, **kwargs: object) -> tuple[object, ...]:
        scorer_calls.append((args, kwargs))
        return ()

    with pytest.raises(
        ValueError,
        match="config must be a ProbabilitySelectionScorerAgreementConfig",
    ):
        api.load_probability_selection_scorer_agreement_report(
            object(),
            object(),
            selection_limit=1,
            scorer_limit=1,
            config=object(),
            generated_at=GENERATED_AT,
            selection_report_loader=fake_selection_loader,
            scorer_report_loader=fake_scorer_loader,
        )

    assert selection_calls == []
    assert scorer_calls == []


@pytest.mark.parametrize(
    ("loader_name", "kwargs"),
    (
        (
            "selection_report_loader",
            {
                "selection_report_loader": object(),
                "scorer_report_loader": lambda *args, **kwargs: (),
            },
        ),
        (
            "scorer_report_loader",
            {
                "selection_report_loader": lambda *args, **kwargs: (),
                "scorer_report_loader": object(),
            },
        ),
    ),
)
def test_loader_rejects_non_callable_injected_loaders_before_reading(
    loader_name: str,
    kwargs: dict[str, object],
) -> None:
    api = _api()

    with pytest.raises(ValueError, match=f"{loader_name} must be callable"):
        api.load_probability_selection_scorer_agreement_report(
            object(),
            object(),
            selection_limit=1,
            scorer_limit=1,
            config=ProbabilitySelectionScorerAgreementConfig(),
            generated_at=GENERATED_AT,
            **kwargs,
        )


def test_loader_module_has_no_db_lifecycle_env_cli_or_live_trading_surface() -> None:
    module_under_test = _api()
    module_path = module_under_test.__file__
    assert module_path is not None
    source = Path(module_path).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)
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
        "polymarket_alpha_lab.autonomous_market_scorer_store",
        "polymarket_alpha_lab.paper_probability_selection_summary_store",
        "polymarket_alpha_lab.probability_selection_scorer_agreement",
    }
    banned_module_fragments = (
        "psycopg",
        "cli",
        "_env",
        "env",
        "auth",
        "client",
        "supabase",
        "exchange",
        "live_trading",
        "live-trading",
        "network",
        "order",
        "wallet",
        "account",
        "execution",
        "approval",
        "advice",
        "migration",
        "migrate",
    )
    banned_call_or_attribute_names = {
        "account",
        "api_key",
        "approval",
        "approve",
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
        "execution",
        "getenv",
        "insert",
        "migrate",
        "persist",
        "print",
        "private_key",
        "replace_order",
        "rollback",
        "sign",
        "submit",
        "trade",
        "update",
        "upsert",
        "wallet",
    }

    assert set(imported_modules) <= allowed_modules
    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
