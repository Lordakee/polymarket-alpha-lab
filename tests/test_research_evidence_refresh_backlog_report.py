from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_evidence_refresh_backlog_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_evidence_refresh_backlog_report.py"
)


class DerivedDecimal(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION,
    }
    values.update(overrides)
    return module.ResearchEvidenceRefreshBacklogConfig(**values)


def item(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "raw-candidate-alpha",
        "market_id": "raw-market-alpha",
        "market_slug": "will-alpha-resolve",
        "market_question": "Will alpha resolve?",
        "source_ref": "source-ref-alpha",
        "source_url": "https://source.invalid/private-alpha",
        "source_text": "private source text",
        "source_refresh_score": d("0.100000"),
        "collection_gap_score": d("0.100000"),
        "coverage_gap_score": d("0.100000"),
        "team_sla_elapsed_hours": d("1.000000"),
        "team_sla_limit_hours": d("10.000000"),
    }
    values.update(overrides)
    return module.ResearchEvidenceRefreshBacklogItem(**values)


def report(*items: object, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_evidence_refresh_backlog_report(
        items,
        config=cfg if cfg is not None else config(),
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_public_numeric_scalars(nested)
        return
    if isinstance(value, list):
        for nested in value:
            assert_no_public_numeric_scalars(nested)
        return
    assert type(value) not in {Decimal, int, float}


def assert_no_forbidden_public_text(value: object) -> None:
    rendered = json.dumps(value, sort_keys=True).lower()
    for fragment in (
        "raw-candidate",
        "raw-market",
        "will-alpha-resolve",
        "will alpha resolve",
        "source-ref-alpha",
        "source.invalid",
        "private source text",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "://",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert fragment not in rendered


def test_module_contract_names_are_available() -> None:
    module = api()

    assert importlib.util.find_spec(MODULE_NAME) is not None
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION",
        "ResearchEvidenceRefreshBacklogConfig",
        "ResearchEvidenceRefreshBacklogItem",
        "ResearchEvidenceRefreshBacklogReport",
        "ResearchEvidenceRefreshBacklogRow",
        "build_research_evidence_refresh_backlog_report",
        "research_evidence_refresh_backlog_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)


def test_report_assigns_pass_watch_and_block_refresh_backlog_statuses() -> None:
    result = report(
        item(
            candidate_id="raw-candidate-watch",
            source_refresh_score=d("0.800000"),
            collection_gap_score=d("0.100000"),
            coverage_gap_score=d("0.100000"),
            team_sla_elapsed_hours=d("5.000000"),
            team_sla_limit_hours=d("10.000000"),
        ),
        item(
            candidate_id="raw-candidate-pass",
            market_id="raw-market-pass",
            market_slug="will-pass-resolve",
            market_question="Will pass resolve?",
            source_ref="source-ref-pass",
            source_url="https://source.invalid/private-pass",
            source_text="private pass text",
            source_refresh_score=d("0.100000"),
            collection_gap_score=d("0.100000"),
            coverage_gap_score=d("0.100000"),
            team_sla_elapsed_hours=d("1.000000"),
            team_sla_limit_hours=d("10.000000"),
        ),
        item(
            candidate_id="raw-candidate-block",
            market_id="raw-market-block",
            market_slug="will-block-resolve",
            market_question="Will block resolve?",
            source_ref="source-ref-block",
            source_url="https://source.invalid/private-block",
            source_text="private block text",
            source_refresh_score=d("0.900000"),
            collection_gap_score=d("1.000000"),
            coverage_gap_score=d("0.800000"),
            team_sla_elapsed_hours=d("24.000000"),
            team_sla_limit_hours=d("12.000000"),
        ),
    )

    assert result.status == "block"
    assert result.input_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.highest_priority_score == d("0.920000")
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.refresh_rank for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert result.rows[0].priority_score == d("0.920000")
    assert result.rows[0].next_refresh_action == "escalate_refresh_review"
    assert result.rows[0].reason_codes == (
        "evidence_refresh_due",
        "collection_gap_blocking",
        "collection_gap_high",
        "coverage_gap_high",
        "team_sla_breached",
    )
    assert result.rows[1].status == "watch"
    assert result.rows[1].next_refresh_action == "refresh_evidence"
    assert result.rows[1].reason_codes == ("evidence_refresh_due",)
    assert result.rows[2].status == "pass"
    assert result.rows[2].next_refresh_action == "no_refresh_needed"
    assert result.rows[2].reason_codes == ("refresh_backlog_pass",)
    assert result.reason_codes == (
        "refresh_backlog_block_present",
        "refresh_backlog_watch_present",
        "refresh_backlog_pass_present",
        "evidence_refresh_due",
        "collection_gap_blocking",
        "collection_gap_high",
        "coverage_gap_high",
        "team_sla_breached",
    )


def test_payload_redacts_raw_surfaces_accepts_safe_dicts_and_detects_tampering() -> None:
    module = api()
    result = report(item())
    payload = module.research_evidence_refresh_backlog_report_payload(result)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_public_numeric_scalars(payload)
    assert_no_forbidden_public_text(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    accepted = module.research_evidence_refresh_backlog_report_payload(payload)
    assert accepted == payload

    tampered = dict(payload)
    tampered["highest_priority_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_evidence_refresh_backlog_report_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["market_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload surface"):
        module.research_evidence_refresh_backlog_report_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["rows"] = [{**payload["rows"][0], "next_refresh_action": "buy now"}]
    with pytest.raises(ValueError, match="unsafe public payload surface"):
        module.research_evidence_refresh_backlog_report_payload(unsafe_value)


def test_decimal_exactness_frozen_dataclasses_flags_and_determinism() -> None:
    module = api()
    signal = item()

    with pytest.raises(FrozenInstanceError):
        signal.source_refresh_score = d("0.200000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_refresh_score must be exactly Decimal"):
        item(source_refresh_score=0.1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="collection_gap_score must be exactly Decimal"):
        item(collection_gap_score=DerivedDecimal("0.100000"))

    with pytest.raises(ValueError, match="coverage_gap_score must use six decimal places"):
        item(coverage_gap_score=d("0.1234567"))

    with pytest.raises(ValueError, match="team_sla_limit_hours must be positive"):
        item(team_sla_limit_hours=d("0.000000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config(), paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item(), report_only=False)

    result = report(item())
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result.rows[0], readonly=False)

    left = module.research_evidence_refresh_backlog_report_payload(
        report(
            item(candidate_id="raw-candidate-zulu"),
            item(candidate_id="raw-candidate-alpha"),
        ),
    )
    right = module.research_evidence_refresh_backlog_report_payload(
        report(
            item(candidate_id="raw-candidate-alpha"),
            item(candidate_id="raw-candidate-zulu"),
        ),
    )
    assert left == right
    assert tuple(row["redacted_refresh_id"] for row in left["rows"]) == tuple(
        sorted(row["redacted_refresh_id"] for row in left["rows"]),
    )

    for klass in (
        module.ResearchEvidenceRefreshBacklogConfig,
        module.ResearchEvidenceRefreshBacklogItem,
        module.ResearchEvidenceRefreshBacklogRow,
        module.ResearchEvidenceRefreshBacklogReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Unsafe{klass.__name__}", (klass,), {})


def test_module_is_report_only_readonly_and_external_io_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", maxsplit=1)[0])
    assert imports.isdisjoint(forbidden_import_roots)

    forbidden_call_names = {
        "connect",
        "execute",
        "fetch",
        "input",
        "open",
        "place_order",
        "print",
        "submit_order",
        "trade",
        "write",
    }
    call_names: set[str] = set()
    public_definition_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            public_definition_names.add(node.name)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert call_names.isdisjoint(forbidden_call_names)
    assert all("wallet" not in name.lower() for name in public_definition_names)
    assert all("auth" not in name.lower() for name in public_definition_names)
