from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_actionability_boundary_report"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_ACTIONABILITY_BOUNDARY_CONFIG_VERSION,
        "min_pass_boundary_score": d("0.750000"),
        "min_watch_boundary_score": d("0.500000"),
        "max_pass_uncertainty_score": d("0.300000"),
        "max_watch_uncertainty_score": d("0.600000"),
        "max_pass_conflict_count": d("0"),
        "max_watch_conflict_count": d("1"),
        "max_pass_missing_check_count": d("0"),
        "max_watch_missing_check_count": d("2"),
        "research_score_weight": d("0.500000"),
        "support_score_weight": d("0.300000"),
        "freshness_score_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchActionabilityBoundaryConfig(**values)


def item(**overrides: object):
    module = api()
    values = {
        "research_key": "alpha",
        "research_score": d("0.900000"),
        "support_score": d("0.800000"),
        "freshness_score": d("0.700000"),
        "uncertainty_score": d("0.100000"),
        "conflict_count": d("0"),
        "missing_check_count": d("0"),
        "reason_codes": ("human_screened",),
    }
    values.update(overrides)
    return module.ResearchActionabilityBoundaryInput(**values)


def report(rows: tuple[object, ...], *, cfg: object | None = None):
    module = api()
    return module.build_research_actionability_boundary_report(
        rows,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_json_scalars(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for key, nested in value.items():
            assert type(key) is str
            assert_public_json_scalars(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_public_json_scalars(nested)


def test_classifies_sanitized_research_results_as_pass_watch_and_block() -> None:
    module = api()

    boundary_report = report(
        (
            item(
                research_key="gamma",
                research_score=d("0.300000"),
                support_score=d("0.400000"),
                freshness_score=d("0.200000"),
                uncertainty_score=d("0.700000"),
                conflict_count=d("2"),
                missing_check_count=d("3"),
                reason_codes=("stale_review",),
            ),
            item(
                research_key="alpha",
                research_score=d("0.900000"),
                support_score=d("0.800000"),
                freshness_score=d("0.700000"),
                uncertainty_score=d("0.100000"),
                conflict_count=d("0"),
                missing_check_count=d("0"),
                reason_codes=("human_screened",),
            ),
            item(
                research_key="beta",
                research_score=d("0.650000"),
                support_score=d("0.600000"),
                freshness_score=d("0.550000"),
                uncertainty_score=d("0.400000"),
                conflict_count=d("0"),
                missing_check_count=d("1"),
                reason_codes=("needs_context",),
            ),
        ),
    )

    assert type(boundary_report) is module.ResearchActionabilityBoundaryReport
    assert boundary_report.status == "block"
    assert boundary_report.result_count == d("3")
    assert boundary_report.pass_count == d("1")
    assert boundary_report.watch_count == d("1")
    assert boundary_report.block_count == d("1")
    assert tuple(row.research_key for row in boundary_report.rows) == (
        "alpha",
        "beta",
        "gamma",
    )
    assert tuple(row.status for row in boundary_report.rows) == ("pass", "watch", "block")
    assert tuple(row.boundary_score for row in boundary_report.rows) == (
        d("0.830000"),
        d("0.615000"),
        d("0.310000"),
    )
    assert boundary_report.rows[0].reason_codes == (
        "boundary_score_pass",
        "conflict_count_pass",
        "input_human_screened",
        "manual_screening_only",
        "missing_check_count_pass",
        "research_actionability_boundary_pass",
        "uncertainty_score_pass",
    )
    assert "research_actionability_boundary_block" in boundary_report.reason_codes
    assert boundary_report.paper_only is True
    assert boundary_report.report_only is True
    assert boundary_report.readonly is True


def test_empty_input_is_blocked_report_only_manual_screening_report() -> None:
    boundary_report = report(())

    assert boundary_report.status == "block"
    assert boundary_report.result_count == d("0")
    assert boundary_report.rows == ()
    assert boundary_report.reason_codes == (
        "manual_screening_only",
        "no_sanitized_research_results",
        "research_actionability_boundary_block",
    )
    assert boundary_report.reason_code_counts[0].reason_code == "manual_screening_only"
    assert boundary_report.paper_only is True
    assert boundary_report.report_only is True
    assert boundary_report.readonly is True


def test_decimal_only_and_strict_type_rejection() -> None:
    module = api()

    with pytest.raises(ValueError, match="research_score must be an exact Decimal"):
        item(research_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="support_score must be a Decimal"):
        item(support_score=0.8)
    with pytest.raises(ValueError, match="conflict_count must be a Decimal"):
        item(conflict_count=1)
    with pytest.raises(ValueError, match="missing_check_count must be a whole count"):
        item(missing_check_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        item(reason_codes=["human_screened"])
    with pytest.raises(ValueError, match="research_key"):
        item(research_key="source_url")
    with pytest.raises(ValueError, match="rows must contain"):
        report((object(),))
    with pytest.raises(ValueError, match="config must be"):
        report((item(),), cfg=object())
    with pytest.raises(ValueError, match="config weights must sum to 1"):
        config(freshness_score_weight=d("0.210000"))
    with pytest.raises(ValueError, match="min_pass_boundary_score"):
        config(min_pass_boundary_score=d("0.400000"))

    with pytest.raises(ValueError, match="status"):
        module.ResearchActionabilityBoundaryRow(
            research_key="bad",
            research_score=d("0.900000"),
            support_score=d("0.800000"),
            freshness_score=d("0.700000"),
            uncertainty_score=d("0.100000"),
            conflict_count=d("0"),
            missing_check_count=d("0"),
            boundary_score=d("0.830000"),
            status="blocked",
            reason_codes=("manual_screening_only",),
        )


def test_public_payload_rejects_identifier_source_storage_and_execution_leaks() -> None:
    module = api()
    payload = module.research_actionability_boundary_report_payload(report((item(),)))

    unsafe_payloads = (
        {"candidate_id": "raw-candidate-123"},
        {"raw_candidate_id": "candidate-123"},
        {"market_id": "market-123"},
        {"market_slug": "will-event-resolve"},
        {"market_question": "Will this event resolve?"},
        {"source_ref": "source-123"},
        {"source_url": "https://example.invalid/source"},
        {"source_text": "raw source text"},
        {"URL": "https://example.invalid"},
        {"dsn": "postgresql://example.invalid/db"},
        {"table_name": "candidate_scores"},
        {"secret_token": "redacted"},
        {"status_note": "wallet"},
        {"status_note": "auth"},
        {"status_note": "order"},
        {"status_note": "trade"},
        {"status_note": "position"},
        {"status_note": "buy"},
        {"status_note": "sell"},
        {"status_note": "recommendation"},
    )
    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.validate_research_actionability_boundary_public_payload(
                {**payload, **unsafe_payload},
            )


def test_hard_flags_and_frozen_records_are_enforced() -> None:
    module = api()
    cfg = config()
    row_input = item()
    boundary_report = report((row_input,), cfg=cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(row_input)
    assert is_dataclass(boundary_report)
    assert module.ResearchActionabilityBoundaryConfig.__dataclass_params__.frozen
    assert module.ResearchActionabilityBoundaryInput.__dataclass_params__.frozen
    assert module.ResearchActionabilityBoundaryRow.__dataclass_params__.frozen
    assert module.ResearchActionabilityBoundaryReasonCodeCount.__dataclass_params__.frozen
    assert module.ResearchActionabilityBoundaryReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        row_input.research_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        boundary_report.status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(boundary_report, readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(boundary_report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.validate_research_actionability_boundary_public_payload(
            {**boundary_report.payload, "readonly": False},
        )


def test_deterministic_public_payload_uses_decimal_strings_and_public_statuses_only() -> None:
    module = api()
    rows = (
        item(research_key="gamma", research_score=d("0.300000"), support_score=d("0.400000")),
        item(research_key="alpha"),
        item(research_key="beta", uncertainty_score=d("0.400000")),
    )

    first = report(rows)
    second = report(tuple(reversed(rows)))

    assert first == second
    assert first.payload == second.payload
    assert json.dumps(first.payload, allow_nan=False, sort_keys=True) == json.dumps(
        second.payload,
        allow_nan=False,
        sort_keys=True,
    )

    payload = first.payload
    assert payload["rows"][0]["boundary_score"] == "0.830000"
    assert payload["rows"][0]["conflict_count"] == "0"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_json_scalars(payload)

    statuses = {payload["status"]}
    statuses.update(row["status"] for row in payload["rows"])
    assert statuses <= set(module.RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES)
    assert module.RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered


def test_module_scope_has_no_io_live_surface_or_forbidden_public_terms() -> None:
    module = api()
    module_path = Path(module.__file__)
    text = module_path.read_text(encoding="utf-8")
    lowered = text.lower()
    tree = ast.parse(text)
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open", "exec", "eval", "compile"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "typing",
    }
    for forbidden in (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "exchange",
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_RESEARCH_ACTIONABILITY_BOUNDARY_CONFIG_VERSION",
        "RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES",
        "ResearchActionabilityBoundaryConfig",
        "ResearchActionabilityBoundaryInput",
        "ResearchActionabilityBoundaryRow",
        "ResearchActionabilityBoundaryReasonCodeCount",
        "ResearchActionabilityBoundaryReport",
        "build_research_actionability_boundary_report",
        "research_actionability_boundary_report_payload",
        "validate_research_actionability_boundary_public_payload",
    )
