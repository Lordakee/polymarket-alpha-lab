from __future__ import annotations

import ast
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 6, 25, 18, 0, tzinfo=UTC)


class NoLifecycleConnection:
    def cursor(self) -> None:
        raise AssertionError("health loader must not open cursors directly")

    def commit(self) -> None:
        raise AssertionError("health loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("health loader must not rollback")

    def close(self) -> None:
        raise AssertionError("health loader must not close")

    def execute(self) -> None:
        raise AssertionError("health loader must not execute directly")


def _api():
    return import_module(
        "polymarket_alpha_lab."
        "paper_project_screening_rank_stability_db_history_health_load",
    )


def _health_api():
    return import_module(
        "polymarket_alpha_lab."
        "paper_project_screening_rank_stability_db_history_health",
    )


def _config(**overrides):
    return (
        _health_api()
        .PaperProjectScreeningRankStabilityDbHistoryHealthConfig(**overrides)
    )


def test_loader_public_exports_loader_only() -> None:
    api = _api()

    assert api.__all__ == (
        "load_paper_project_screening_rank_stability_db_history_health_report",
    )


def test_loader_uses_injected_report_loader_reverses_desc_order_and_does_not_own_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    connection = NoLifecycleConnection()
    config = _config(
        min_rank_stability_report_count=1,
    )
    expected_report = object()
    loader_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []

    def fake_report_loader(
        received_connection: object,
        *,
        config_version: str | None,
        stability_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[str, ...]:
        loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "stability_status": stability_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return ("newest", "oldest")

    def fake_health_builder(
        rank_stability_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> object:
        builder_calls.append(
            {
                "rank_stability_reports": tuple(rank_stability_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_report

    monkeypatch.setattr(
        module_under_test,
        "build_paper_project_screening_rank_stability_db_history_health_report",
        fake_health_builder,
    )

    result = (
        module_under_test
        .load_paper_project_screening_rank_stability_db_history_health_report(
            connection,
            config_version="project-screening-rank-stability-v0",
            stability_status="watch",
            limit=5,
            table_name="paper_project_screening_rank_stability_archive",
            config=config,
            generated_at=GENERATED_AT,
            report_loader=fake_report_loader,
        )
    )

    assert result is expected_report
    assert loader_calls == [
        {
            "connection": connection,
            "config_version": "project-screening-rank-stability-v0",
            "stability_status": "watch",
            "limit": 5,
            "table_name": "paper_project_screening_rank_stability_archive",
        },
    ]
    assert builder_calls == [
        {
            "rank_stability_reports": ("oldest", "newest"),
            "config": config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_rejects_non_exact_health_config_before_reading() -> None:
    api = _api()
    calls: list[object] = []

    def fake_report_loader(*args: object, **kwargs: object) -> tuple[object, ...]:
        calls.append((args, kwargs))
        return ()

    invalid_configs = (object(),)
    for config in invalid_configs:
        with pytest.raises(
            ValueError,
            match=(
                "config must be a "
                "PaperProjectScreeningRankStabilityDbHistoryHealthConfig"
            ),
        ):
            api.load_paper_project_screening_rank_stability_db_history_health_report(
                NoLifecycleConnection(),
                limit=1,
                config=config,
                generated_at=GENERATED_AT,
                report_loader=fake_report_loader,
            )

    assert calls == []


def test_loader_rejects_non_callable_report_loader_before_reading() -> None:
    api = _api()

    with pytest.raises(ValueError, match="report_loader must be callable"):
        api.load_paper_project_screening_rank_stability_db_history_health_report(
            NoLifecycleConnection(),
            limit=1,
            config=_config(),
            generated_at=GENERATED_AT,
            report_loader=object(),
        )


def test_loader_default_loader_delegates_to_store_filters_and_builds_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _api()
    connection = object()
    config = _config()
    expected_report = object()
    loader_calls: list[dict[str, object]] = []
    builder_calls: list[dict[str, object]] = []

    def fake_store_loader(
        received_connection: object,
        *,
        config_version: str | None,
        stability_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[str, ...]:
        loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "stability_status": stability_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return ("latest", "middle", "earliest")

    def fake_health_builder(
        rank_stability_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> object:
        builder_calls.append(
            {
                "rank_stability_reports": tuple(rank_stability_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_project_screening_rank_stability_reports",
        fake_store_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_project_screening_rank_stability_db_history_health_report",
        fake_health_builder,
    )

    result = (
        module_under_test
        .load_paper_project_screening_rank_stability_db_history_health_report(
            connection,
            config_version="project-screening-rank-stability-v0",
            stability_status="blocked",
            limit=3,
            table_name="paper_project_screening_rank_stability_reports",
            config=config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_report
    assert loader_calls == [
        {
            "connection": connection,
            "config_version": "project-screening-rank-stability-v0",
            "stability_status": "blocked",
            "limit": 3,
            "table_name": "paper_project_screening_rank_stability_reports",
        },
    ]
    assert builder_calls == [
        {
            "rank_stability_reports": ("earliest", "middle", "latest"),
            "config": config,
            "generated_at": GENERATED_AT,
        },
    ]


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
        "polymarket_alpha_lab.paper_project_screening_rank_stability_db_history_health",
        "polymarket_alpha_lab.paper_project_screening_rank_stability_store",
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
