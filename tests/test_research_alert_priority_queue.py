from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_alert_priority_queue.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.research_alert_priority_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_ALERT_PRIORITY_QUEUE_CONFIG_VERSION,
    }
    values.update(overrides)
    return module.ResearchAlertPriorityQueueConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "raw-candidate-alpha",
        "market_reference": "raw-market-alpha",
        "market_slug": "will-alpha-resolve",
        "market_question": "Will alpha resolve?",
        "source_reference": "https://source.invalid/private-alpha",
        "source_text": "private source text",
        "source_refresh_score": d("0.800000"),
        "evidence_conflict_score": d("0.300000"),
        "rule_risk_score": d("0.200000"),
        "team_sla_age_seconds": d("7200.000000"),
        "team_sla_limit_seconds": d("14400.000000"),
    }
    values.update(overrides)
    return module.ResearchAlertSignal(**values)


def report(*signals: object, cfg=None):
    module = api()
    return module.build_research_alert_priority_queue(
        signals,
        config=cfg if cfg is not None else config(),
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
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
    forbidden = (
        "raw-candidate",
        "raw-market",
        "will-alpha-resolve",
        "will alpha resolve",
        "source.invalid",
        "private source",
        "postgres",
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
    )
    rendered = json.dumps(value, sort_keys=True).lower()
    for fragment in forbidden:
        assert fragment not in rendered


def test_alert_queue_assigns_pass_watch_and_block_public_statuses() -> None:
    result = report(
        signal(
            candidate_reference="raw-candidate-watch",
            source_refresh_score=d("0.800000"),
            evidence_conflict_score=d("0.100000"),
            rule_risk_score=d("0.100000"),
            team_sla_age_seconds=d("7200.000000"),
            team_sla_limit_seconds=d("14400.000000"),
        ),
        signal(
            candidate_reference="raw-candidate-pass",
            market_reference="raw-market-pass",
            market_slug="will-pass-resolve",
            market_question="Will pass resolve?",
            source_reference="source-ref-pass",
            source_text="private pass text",
            source_refresh_score=d("0.100000"),
            evidence_conflict_score=d("0.100000"),
            rule_risk_score=d("0.100000"),
            team_sla_age_seconds=d("60.000000"),
            team_sla_limit_seconds=d("14400.000000"),
        ),
        signal(
            candidate_reference="raw-candidate-block",
            market_reference="raw-market-block",
            market_slug="will-block-resolve",
            market_question="Will block resolve?",
            source_reference="source-ref-block",
            source_text="private block text",
            source_refresh_score=d("0.200000"),
            evidence_conflict_score=d("0.950000"),
            rule_risk_score=d("0.900000"),
            team_sla_age_seconds=d("28800.000000"),
            team_sla_limit_seconds=d("14400.000000"),
        ),
    )

    assert result.queue_status == "block"
    assert result.input_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert tuple(row.public_status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.alert_rank for row in result.rows) == (d("1"), d("2"), d("3"))
    assert result.rows[0].priority_score == d("0.862500")
    assert result.rows[0].next_research_action == "escalate_rule_and_conflict_review"
    assert result.rows[0].reason_codes == (
        "evidence_conflict_blocking",
        "evidence_conflict_high",
        "rule_risk_blocking",
        "rule_risk_high",
        "team_sla_breached",
    )
    assert result.rows[1].public_status == "watch"
    assert result.rows[1].next_research_action == "refresh_sources"
    assert "source_refresh_due" in result.rows[1].reason_codes
    assert result.rows[2].public_status == "pass"
    assert result.rows[2].next_research_action == "no_alert"
    assert result.reason_codes == (
        "alert_block_present",
        "alert_watch_present",
        "alert_pass_present",
        "source_refresh_due",
        "evidence_conflict_high",
        "evidence_conflict_blocking",
        "rule_risk_high",
        "rule_risk_blocking",
        "team_sla_breached",
    )


def test_alert_queue_payload_redacts_raw_identifiers_and_rejects_leaks() -> None:
    module = api()
    result = report(signal())
    payload = module.research_alert_priority_queue_payload(result)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert_no_forbidden_public_text(payload)
    assert "derived_validation_digest" in payload
    assert len(payload["derived_validation_digest"]) == 64

    accepted = module.research_alert_priority_queue_payload(payload)
    assert accepted == payload

    tampered = dict(payload)
    tampered["highest_priority_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_alert_priority_queue_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["market_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload surface"):
        module.research_alert_priority_queue_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["rows"] = [{**payload["rows"][0], "next_research_action": "buy now"}]
    with pytest.raises(ValueError, match="unsafe public payload surface"):
        module.research_alert_priority_queue_payload(unsafe_value)


def test_alert_queue_rejects_non_exact_decimal_and_noncanonical_values() -> None:
    module = api()
    item = signal()

    with pytest.raises(FrozenInstanceError):
        item.source_refresh_score = d("0.900000")

    with pytest.raises(ValueError, match="source_refresh_score must be exactly Decimal"):
        signal(source_refresh_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_refresh_score must be exactly Decimal"):
        signal(source_refresh_score=_DecimalSubclass("0.800000"))

    with pytest.raises(ValueError, match="rule_risk_score must use six decimal places"):
        signal(rule_risk_score=d("0.1234567"))

    with pytest.raises(ValueError, match="candidate_reference must be a canonical string"):
        signal(candidate_reference=" raw-candidate ")

    with pytest.raises(ValueError, match="signals must contain ResearchAlertSignal"):
        report({"candidate_reference": "raw-candidate"})

    with pytest.raises(ValueError, match="public_status is unsupported"):
        module.ResearchAlertPriorityQueueRow(
            redacted_alert_id="alert_test",
            public_status="research_next",
            priority_score=d("0.100000"),
            alert_rank=d("1"),
            next_research_action="no_alert",
            reason_codes=("alert_pass",),
        )


def test_alert_queue_enforces_hard_flags_everywhere() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config(), paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(signal(), report_only=False)

    result = report(signal())
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result.rows[0], readonly=False)

    payload = module.research_alert_priority_queue_payload(result)
    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        module.research_alert_priority_queue_payload(payload)


def test_alert_queue_output_is_deterministic_and_source_is_pure() -> None:
    module = api()
    inputs = (
        signal(candidate_reference="raw-candidate-zulu"),
        signal(candidate_reference="raw-candidate-alpha"),
    )

    first = module.research_alert_priority_queue_payload(report(*inputs))
    second = module.research_alert_priority_queue_payload(report(*reversed(inputs)))
    assert first == second
    assert tuple(row["redacted_alert_id"] for row in first["rows"]) == tuple(
        sorted(row["redacted_alert_id"] for row in first["rows"])
    )

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
