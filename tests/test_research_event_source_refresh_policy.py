from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_source_refresh_policy.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_source_refresh_policy",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def policy_input(**overrides: object):
    module = api()
    values = {
        "event_domain": "corporate",
        "time_to_settlement_minutes": d("1440.000000"),
        "evidence_age_minutes": d("60.000000"),
        "source_conflict_score": d("0.100000"),
        "source_reliability": d("0.900000"),
        "stale_evidence_sensitivity": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchEventSourceRefreshPolicyInput(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_research_event_source_refresh_policy(
        policy_input(**overrides),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_pass_policy_uses_domain_cadence_and_payload_is_safe() -> None:
    module = api()
    decision = evaluate()

    assert is_dataclass(decision)
    assert decision.event_domain == "corporate"
    assert decision.time_to_settlement_minutes == d("1440.000000")
    assert decision.evidence_age_minutes == d("60.000000")
    assert decision.source_conflict_score == d("0.100000")
    assert decision.source_reliability == d("0.900000")
    assert decision.stale_evidence_sensitivity == d("0.200000")
    assert decision.domain_refresh_interval_minutes == d("120.000000")
    assert decision.settlement_refresh_interval_minutes == d("120.000000")
    assert decision.required_refresh_interval_minutes == d("120.000000")
    assert decision.evidence_stale_ratio == d("0.500000")
    assert decision.policy_status == "pass"
    assert decision.refresh_action == "keep_domain_cadence"
    assert decision.reason_codes == (
        "refresh_policy_pass",
        "domain_corporate_cadence",
        "evidence_within_refresh_window",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True

    payload = module.research_event_source_refresh_policy_payload(decision)
    encoded = json.dumps(payload, sort_keys=True)

    assert decision.payload == payload
    assert payload["event_domain"] == "corporate"
    assert payload["time_to_settlement_minutes"] == "1440.000000"
    assert payload["evidence_age_minutes"] == "60.000000"
    assert payload["source_conflict_score"] == "0.100000"
    assert payload["source_reliability"] == "0.900000"
    assert payload["stale_evidence_sensitivity"] == "0.200000"
    assert payload["domain_refresh_interval_minutes"] == "120.000000"
    assert payload["settlement_refresh_interval_minutes"] == "120.000000"
    assert payload["required_refresh_interval_minutes"] == "120.000000"
    assert payload["evidence_stale_ratio"] == "0.500000"
    assert payload["policy_status"] == "pass"
    assert payload["refresh_action"] == "keep_domain_cadence"
    assert payload["reason_codes"] == [
        "refresh_policy_pass",
        "domain_corporate_cadence",
        "evidence_within_refresh_window",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"120.000000"' in encoded
    assert_no_float_values(payload)


def test_domain_and_settlement_windows_adjust_refresh_frequency() -> None:
    crypto = evaluate(
        event_domain="crypto",
        evidence_age_minutes=d("5.000000"),
    )
    legal = evaluate(
        event_domain="legal",
        evidence_age_minutes=d("100.000000"),
    )
    imminent = evaluate(
        event_domain="sports",
        time_to_settlement_minutes=d("45.000000"),
        evidence_age_minutes=d("8.000000"),
    )

    assert crypto.domain_refresh_interval_minutes == d("15.000000")
    assert crypto.settlement_refresh_interval_minutes == d("15.000000")
    assert crypto.required_refresh_interval_minutes == d("15.000000")
    assert crypto.policy_status == "pass"

    assert legal.domain_refresh_interval_minutes == d("240.000000")
    assert legal.settlement_refresh_interval_minutes == d("240.000000")
    assert legal.required_refresh_interval_minutes == d("240.000000")
    assert legal.policy_status == "pass"

    assert imminent.domain_refresh_interval_minutes == d("30.000000")
    assert imminent.settlement_refresh_interval_minutes == d("7.500000")
    assert imminent.required_refresh_interval_minutes == d("7.500000")
    assert imminent.evidence_stale_ratio == d("1.066667")
    assert imminent.policy_status == "watch"
    assert imminent.refresh_action == "refresh_before_research_use"
    assert imminent.reason_codes == (
        "refresh_policy_watch",
        "domain_sports_cadence",
        "settlement_imminent",
        "evidence_stale_watch",
    )


def test_conflict_near_settlement_blocks_even_when_evidence_is_fresh() -> None:
    decision = evaluate(
        event_domain="politics",
        time_to_settlement_minutes=d("30.000000"),
        evidence_age_minutes=d("4.000000"),
        source_conflict_score=d("0.750000"),
        source_reliability=d("0.800000"),
        stale_evidence_sensitivity=d("0.300000"),
    )

    assert decision.domain_refresh_interval_minutes == d("60.000000")
    assert decision.settlement_refresh_interval_minutes == d("15.000000")
    assert decision.required_refresh_interval_minutes == d("7.500000")
    assert decision.evidence_stale_ratio == d("0.266667")
    assert decision.policy_status == "block"
    assert decision.refresh_action == "pause_until_source_refresh"
    assert decision.reason_codes == (
        "refresh_policy_block",
        "domain_politics_cadence",
        "settlement_imminent",
        "conflict_signal_high",
        "conflict_near_settlement_block",
    )


def test_stale_evidence_blocks_and_conflict_watch_accelerates_refresh() -> None:
    stale = evaluate(
        event_domain="legal",
        time_to_settlement_minutes=d("720.000000"),
        evidence_age_minutes=d("600.000000"),
        source_conflict_score=d("0.200000"),
        source_reliability=d("0.700000"),
        stale_evidence_sensitivity=d("0.800000"),
    )
    conflict_watch = evaluate(
        event_domain="macro",
        time_to_settlement_minutes=d("480.000000"),
        evidence_age_minutes=d("10.000000"),
        source_conflict_score=d("0.400000"),
        source_reliability=d("0.900000"),
        stale_evidence_sensitivity=d("0.200000"),
    )

    assert stale.settlement_refresh_interval_minutes == d("240.000000")
    assert stale.required_refresh_interval_minutes == d("240.000000")
    assert stale.evidence_stale_ratio == d("2.500000")
    assert stale.policy_status == "block"
    assert stale.refresh_action == "pause_until_source_refresh"
    assert stale.reason_codes == (
        "refresh_policy_block",
        "domain_legal_cadence",
        "evidence_stale_block",
        "stale_evidence_sensitivity_high",
    )

    assert conflict_watch.domain_refresh_interval_minutes == d("45.000000")
    assert conflict_watch.settlement_refresh_interval_minutes == d("45.000000")
    assert conflict_watch.required_refresh_interval_minutes == d("22.500000")
    assert conflict_watch.evidence_stale_ratio == d("0.222222")
    assert conflict_watch.policy_status == "watch"
    assert conflict_watch.refresh_action == "refresh_before_research_use"
    assert conflict_watch.reason_codes == (
        "refresh_policy_watch",
        "domain_macro_cadence",
        "conflict_signal_watch",
    )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "time_to_settlement_minutes",
        "evidence_age_minutes",
        "source_conflict_score",
        "source_reliability",
        "stale_evidence_sensitivity",
        "domain_refresh_interval_minutes",
        "settlement_refresh_interval_minutes",
        "required_refresh_interval_minutes",
        "evidence_stale_ratio",
    }

    for cls in (
        module.ResearchEventSourceRefreshPolicyInput,
        module.ResearchEventSourceRefreshPolicyResult,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="event_domain"):
        policy_input(event_domain=_StringSubclass("corporate"))

    with pytest.raises(ValueError, match="event_domain must be a known value"):
        policy_input(event_domain="finance")

    with pytest.raises(ValueError, match="time_to_settlement_minutes must be a Decimal"):
        policy_input(time_to_settlement_minutes=1)

    with pytest.raises(ValueError, match="source_conflict_score must be a Decimal"):
        policy_input(source_conflict_score=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="evidence_age_minutes must be nonnegative"):
        policy_input(evidence_age_minutes=d("-0.000001"))

    with pytest.raises(ValueError, match="source_reliability must be between 0 and 1"):
        policy_input(source_reliability=d("1.000001"))

    with pytest.raises(ValueError, match="source_conflict_score must use"):
        policy_input(source_conflict_score=Decimal("0.1234567"))

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.ResearchEventSourceRefreshPolicyResult(
            event_domain="macro",
            time_to_settlement_minutes=d("480.000000"),
            evidence_age_minutes=d("10.000000"),
            source_conflict_score=d("0.400000"),
            source_reliability=d("0.900000"),
            stale_evidence_sensitivity=d("0.200000"),
            domain_refresh_interval_minutes=d("45.000000"),
            settlement_refresh_interval_minutes=d("45.000000"),
            required_refresh_interval_minutes=d("22.500000"),
            evidence_stale_ratio=d("0.222222"),
            policy_status="watch",
            refresh_action="refresh_before_research_use",
            reason_codes=("conflict_signal_watch", "conflict_signal_watch"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(policy_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(evaluate(), readonly=False)

    with pytest.raises(FrozenInstanceError):
        decision = evaluate()
        decision.policy_status = "watch"  # type: ignore[misc]


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        policy_input(event_domain="postgresql://user:secret@db.example.local/source")


def test_module_scope_is_paper_report_readonly_with_no_external_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "open(",
        "requests",
        "http",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
