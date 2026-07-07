from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module("polymarket_alpha_lab.research_source_collection_runbook")


def runbook_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "collection_scope": "macro-rates:official:public-web",
        "registry_key": "redacted-source-registry-001",
        "source_category": "official",
        "scope_status": "pass",
        "registry_status": "pass",
        "freshness_status": "pass",
        "freshness_age_seconds": d("3600.000000"),
        "audit_trail_state": "complete",
        "audit_event_count": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceCollectionRunbookInput(**values)


def build(*inputs: object):
    module = api()
    return module.build_research_source_collection_runbook(
        inputs or (runbook_input(),),
        config=module.ResearchSourceCollectionRunbookConfig(),
    )


def assert_payload_has_no_numeric_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_payload_has_no_numeric_values(key)
            assert_payload_has_no_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_numeric_values(item)


def assert_payload_has_no_forbidden_public_text(value: Any) -> None:
    forbidden_fragments = (
        "raw candidate",
        "raw-candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommendation",
    )
    if isinstance(value, str):
        lowered = f" {value.lower().replace('_', ' ').replace('-', ' ')} "
        raw_lowered = value.lower()
        for fragment in forbidden_fragments:
            assert fragment not in raw_lowered
        assert " buy " not in lowered
        assert " sell " not in lowered
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_payload_has_no_forbidden_public_text(key)
            assert_payload_has_no_forbidden_public_text(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_forbidden_public_text(item)


def test_builds_pass_watch_and_block_collection_runbook() -> None:
    module = api()
    report = build(
        runbook_input(),
        runbook_input(
            collection_scope="election-admin:regulatory:public-web",
            registry_key="redacted-source-registry-002",
            source_category="regulatory",
            scope_status="watch",
            registry_status="pass",
            freshness_status="watch",
            freshness_age_seconds=d("90000.000000"),
            audit_trail_state="partial",
            audit_event_count=d("1.000000"),
        ),
        runbook_input(
            collection_scope="sports-rules:news:public-web",
            registry_key="redacted-source-registry-003",
            source_category="news",
            scope_status="block",
            registry_status="watch",
            freshness_status="block",
            freshness_age_seconds=None,
            audit_trail_state="missing",
            audit_event_count=d("0.000000"),
        ),
    )

    assert type(report) is module.ResearchSourceCollectionRunbookReport
    assert report.collection_status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.step_count == d("15.000000")
    assert report.reason_codes == (
        "audit_event_count_low_watch",
        "audit_event_count_missing_block",
        "audit_trail_missing_block",
        "audit_trail_partial_watch",
        "freshness_control_block",
        "freshness_control_watch",
        "registry_control_watch",
        "scope_control_block",
        "scope_control_watch",
        "collection_runbook_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block, watch, passed = report.rows
    assert tuple(row.collection_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert block.collection_scope == "sports-rules:news:public-web"
    assert block.runbook_rank == d("1.000000")
    assert block.runbook_steps[-1].step_code == "hold_collection_controls"
    assert block.runbook_steps[-1].step_status == "block"
    assert watch.runbook_steps[-1].step_code == "complete_watch_review"
    assert passed.runbook_steps[-1].step_code == "prepare_readonly_collection_notes"
    assert all(len(row.runbook_digest) == 64 for row in report.rows)
    assert len({row.runbook_digest for row in report.rows}) == 3

    payload = module.research_source_collection_runbook_payload(report)
    assert payload == report.payload
    assert payload["input_count"] == "3.000000"
    assert payload["step_count"] == "15.000000"
    assert payload["rows"][0]["runbook_steps"][0]["step_rank"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert_payload_has_no_numeric_values(payload)
    assert_payload_has_no_forbidden_public_text(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_inputs_block_with_no_inputs_reason() -> None:
    module = api()
    report = module.build_research_source_collection_runbook(
        (),
        config=module.ResearchSourceCollectionRunbookConfig(),
    )

    assert report.collection_status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.step_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("collection_runbook_no_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_deterministic_ordering_and_digest_validation() -> None:
    module = api()
    passed = runbook_input(
        collection_scope="macro-rates:official:public-web",
        registry_key="redacted-source-registry-001",
    )
    watch = runbook_input(
        collection_scope="election-admin:regulatory:public-web",
        registry_key="redacted-source-registry-002",
        source_category="regulatory",
        scope_status="watch",
        freshness_status="watch",
        audit_trail_state="partial",
        audit_event_count=d("1.000000"),
    )

    first = build(passed, watch)
    second = build(watch, passed)

    assert first == second
    assert tuple(row.runbook_rank for row in first.rows) == (d("1.000000"), d("2.000000"))
    assert first.derived_validation_digest == second.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="collection_status must match reason_codes"):
        replace(first.rows[0], collection_status="pass")


def test_public_dataclasses_are_frozen_exact_typed_and_decimal_only() -> None:
    module = api()
    subject = runbook_input()
    report = build(subject)

    public_classes = (
        module.ResearchSourceCollectionRunbookConfig,
        module.ResearchSourceCollectionRunbookInput,
        module.ResearchSourceCollectionRunbookStep,
        module.ResearchSourceCollectionRunbookRow,
        module.ResearchSourceCollectionRunbookReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.collection_scope = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.collection_status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedInput", (module.ResearchSourceCollectionRunbookInput,), {})
    with pytest.raises(ValueError, match="freshness_age_seconds must be a Decimal"):
        runbook_input(freshness_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="audit_event_count must be a Decimal"):
        runbook_input(audit_event_count="3.000000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="audit_event_count must not exceed six"):
        runbook_input(audit_event_count=d("1.0000001"))
    with pytest.raises(ValueError, match="scope_status must be a known value"):
        runbook_input(scope_status="blocked")
    with pytest.raises(ValueError, match="paper_only must be True"):
        runbook_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_source_collection_runbook((), config=object())
    with pytest.raises(ValueError, match="inputs must be an iterable"):
        module.build_research_source_collection_runbook(object())
    with pytest.raises(ValueError, match="unique by collection_scope and registry_key"):
        build(subject, subject)


def test_unsafe_public_payload_rejects_raw_ids_market_source_refs_and_trading_language() -> None:
    module = api()

    unsafe_values = (
        {"collection_scope": "raw-candidate-alpha"},
        {"collection_scope": "market-slug-alpha"},
        {"collection_scope": "market_id_alpha"},
        {"collection_scope": "question-alpha"},
        {"registry_key": "source_ref_alpha"},
        {"registry_key": "source_url_alpha"},
        {"registry_key": "source_text_alpha"},
        {"registry_key": "https://example.test/item"},
        {"registry_key": "dsn-alpha"},
        {"registry_key": "table-alpha"},
        {"registry_key": "token-alpha"},
        {"registry_key": "wallet-alpha"},
        {"registry_key": "auth-alpha"},
        {"registry_key": "order-alpha"},
        {"registry_key": "trade-alpha"},
        {"registry_key": "position-alpha"},
        {"registry_key": "buy alpha"},
        {"registry_key": "sell alpha"},
        {"registry_key": "recommendation-alpha"},
    )
    for overrides in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public payload"):
            runbook_input(**overrides)

    payload = module.research_source_collection_runbook_payload(build(runbook_input()))
    with pytest.raises(ValueError, match="unsupported"):
        module.research_source_collection_runbook_payload(
            {**payload, "source_url": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_source_collection_runbook_payload(
            {**payload, "collection_status": "buy now"},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_collection_runbook_payload({**payload, "readonly": False})


def test_module_is_pure_report_only_decimal_only_and_unwired() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "AUDIT_TRAIL_STATES",
        "DEFAULT_RESEARCH_SOURCE_COLLECTION_RUNBOOK_CONFIG_VERSION",
        "ResearchSourceCollectionRunbookConfig",
        "ResearchSourceCollectionRunbookInput",
        "ResearchSourceCollectionRunbookReport",
        "ResearchSourceCollectionRunbookRow",
        "ResearchSourceCollectionRunbookStep",
        "SOURCE_CATEGORIES",
        "STATUSES",
        "build_research_source_collection_runbook",
        "research_source_collection_runbook_payload",
    )

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    }
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
