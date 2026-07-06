from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_probability_event_research_readiness_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_probability_event_research_readiness_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-pass",
        "event_id": "event-pass",
        "official_source_anchor_score": d("0.900000"),
        "information_quality_score": d("0.900000"),
        "source_crosscheck_score": d("0.900000"),
        "rule_clarity_score": d("0.900000"),
        "probability_movement_context_score": d("0.900000"),
        "source_freshness_exception_score": d("0.900000"),
        "specialist_confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityEventResearchReadinessEvidenceV2(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            evidence(candidate_id="candidate-pass", event_id="event-pass"),
            evidence(
                candidate_id="candidate-watch",
                event_id="event-watch",
                official_source_anchor_score=d("0.760000"),
                information_quality_score=d("0.700000"),
                source_crosscheck_score=d("0.700000"),
                rule_clarity_score=d("0.750000"),
                probability_movement_context_score=d("0.650000"),
                source_freshness_exception_score=d("0.700000"),
                specialist_confidence_score=d("0.700000"),
            ),
            evidence(
                candidate_id="candidate-blocked",
                event_id="event-blocked",
                official_source_anchor_score=d("0.600000"),
                information_quality_score=d("0.800000"),
                source_crosscheck_score=d("0.800000"),
                rule_clarity_score=d("0.800000"),
                probability_movement_context_score=d("0.800000"),
                source_freshness_exception_score=d("0.800000"),
                specialist_confidence_score=d("0.800000"),
            ),
        )
    return module.build_strategy_probability_event_research_readiness_gate_v2(
        items,
        config=config,
        generated_at=generated_at,
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


def test_builds_decimal_readiness_gate_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.gate_status == "blocked"
    assert report.strategy_promotion_blocked is True
    assert report.candidate_count == d("3")
    assert report.pass_candidate_count == d("1")
    assert report.watch_candidate_count == d("1")
    assert report.blocked_candidate_count == d("1")
    assert report.average_research_readiness_score == d("0.793333")
    assert report.reason_codes == (
        "research_readiness_gate_watch_rows",
        "research_readiness_gate_blocked_rows",
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-blocked",
        "candidate-watch",
        "candidate-pass",
    )
    assert tuple(row.readiness_status for row in report.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert tuple(row.research_readiness_score for row in report.rows) == (
        d("0.771429"),
        d("0.708571"),
        d("0.900000"),
    )
    assert "official_source_anchor_weak" in report.rows[0].reason_codes

    payload = report.payload
    assert payload["candidate_count"] == "3"
    assert payload["average_research_readiness_score"] == "0.793333"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["strategy_promotion_blocked"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["research_readiness_score"] == "0.771429"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_gate_is_report_only_digest_backed_and_blocking() -> None:
    report = build_report(
        *(),
        generated_at=GENERATED_AT,
        use_default_items=False,
    )

    assert report.gate_status == "blocked"
    assert report.strategy_promotion_blocked is True
    assert report.candidate_count == d("0")
    assert report.average_research_readiness_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("research_readiness_gate_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyProbabilityEventResearchReadinessGateV2Config()
    item = evidence()
    report = build_report(item)
    row = report.rows[0]

    for obj in (config, item, row, report):
        assert obj.paper_only is True
        assert obj.report_only is True
        assert obj.readonly is True
        with pytest.raises(FrozenInstanceError):
            obj.paper_only = False  # type: ignore[misc]
        for field in fields(obj):
            value = getattr(obj, field.name)
            if field.name.endswith("_score") or field.name.endswith("_floor"):
                assert type(value) is Decimal
            if field.name.endswith("_count"):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="official_source_anchor_score must be exactly Decimal"):
        evidence(official_source_anchor_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="information_quality_score must be exactly Decimal"):
        evidence(information_quality_score=0)
    with pytest.raises(ValueError, match="rule_clarity_score must be <= 1.000000"):
        evidence(rule_clarity_score=d("1.000001"))
    with pytest.raises(
        ValueError,
        match="source_crosscheck_score must use six decimal places or fewer",
    ):
        evidence(source_crosscheck_score=d("0.7000004"))
    with pytest.raises(ValueError, match="specialist_confidence_score must be finite"):
        evidence(specialist_confidence_score=Decimal("NaN"))


def test_config_and_build_validation_reject_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="pass_score_floor must be exactly Decimal"):
        module.StrategyProbabilityEventResearchReadinessGateV2Config(
            pass_score_floor=0,
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed pass_score_floor"):
        module.StrategyProbabilityEventResearchReadinessGateV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyProbabilityEventResearchReadinessGateV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readiness evidence must be an iterable"):
        module.build_strategy_probability_event_research_readiness_gate_v2(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="readiness evidence items must be StrategyProbabilityEventResearchReadinessEvidenceV2",
    ):
        module.build_strategy_probability_event_research_readiness_gate_v2(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_probability_event_research_readiness_gate_v2(
            [evidence()],
            generated_at=datetime(2026, 7, 6),
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_research_readiness_score=d("0.790000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_candidate",
        "auth_candidate",
        "wallet_candidate",
        "order_candidate",
        "network_candidate",
        "database_candidate",
        "persist_candidate",
        "signing_candidate",
        "mutation_candidate",
        "buy_candidate",
        "sell_candidate",
        "trade_candidate",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            evidence(candidate_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by status and candidate_id"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_candidate_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match gate_status"):
        replace(report, reason_codes=("research_readiness_gate_passed",))


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
