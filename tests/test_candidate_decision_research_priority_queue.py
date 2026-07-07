from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_research_priority_queue",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return module.CandidateDecisionResearchPriorityQueueConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_id": "raw-market-alpha",
        "question": "Will alpha resolve in favor of the thesis?",
        "source_references": ("private-source-alpha",),
        "expected_gross_edge": d("0.140000"),
        "expected_cost_drag": d("0.020000"),
        "missing_evidence_score": d("0.700000"),
        "resolution_seconds": d("3600.000000"),
        "source_age_seconds": d("7200.000000"),
        "available_liquidity": d("500.000000"),
        "team_memory_readiness_score": d("0.800000"),
        "missing_evidence_codes": ("decision_evidence_missing",),
        "hard_block_reason_codes": (),
    }
    values.update(overrides)
    return module.CandidateDecisionResearchCandidateAggregate(**values)


def report(*candidates: object, cfg=None):
    module = api()
    return module.build_candidate_decision_research_priority_queue(
        candidates,
        config=cfg if cfg is not None else config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_ranks_research_next_by_evidence_edge_urgency_freshness_and_tie_breaking() -> None:
    result = report(
        candidate(
            candidate_reference="candidate-slower",
            market_id="raw-market-slower",
            expected_gross_edge=d("0.150000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.900000"),
            resolution_seconds=d("80000.000000"),
            source_age_seconds=d("7200.000000"),
            missing_evidence_codes=("slow_evidence_missing",),
        ),
        candidate(
            candidate_reference="candidate-urgent",
            market_id="raw-market-urgent",
            expected_gross_edge=d("0.150000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.900000"),
            resolution_seconds=d("60.000000"),
            source_age_seconds=d("7200.000000"),
            missing_evidence_codes=("urgent_evidence_missing",),
        ),
        candidate(
            candidate_reference="candidate-tie-zulu",
            market_id="raw-market-tie-zulu",
            expected_gross_edge=d("0.100000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.600000"),
            resolution_seconds=d("4000.000000"),
            source_age_seconds=d("9000.000000"),
            missing_evidence_codes=("tie_evidence_missing",),
        ),
        candidate(
            candidate_reference="candidate-tie-alpha",
            market_id="raw-market-tie-alpha",
            expected_gross_edge=d("0.100000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.600000"),
            resolution_seconds=d("4000.000000"),
            source_age_seconds=d("9000.000000"),
            missing_evidence_codes=("tie_evidence_missing",),
        ),
    )

    assert result.queue_status == "research_next"
    assert result.input_count == d("4")
    assert result.research_next_count == d("4")
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.highest_priority_score == result.rows[0].priority_score
    assert tuple(row.research_rank for row in result.rows) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
    )
    assert result.rows[0].bucket == "research_next"
    assert "resolution_urgent" in result.rows[0].reason_codes
    assert "urgent_evidence_missing" in result.rows[0].reason_codes
    assert result.rows[0].priority_score > result.rows[1].priority_score

    tie_rows = tuple(
        row for row in result.rows if "tie_evidence_missing" in row.reason_codes
    )
    assert len(tie_rows) == 2
    assert tie_rows[0].priority_score == tie_rows[1].priority_score
    assert tuple(row.redacted_candidate_reference for row in tie_rows) == tuple(
        sorted(row.redacted_candidate_reference for row in tie_rows),
    )
    assert result.reason_codes == (
        "research_next_ready",
        "missing_evidence_high",
        "resolution_urgent",
        "source_refresh_needed",
        "liquidity_cost_ready",
        "team_memory_ready",
    )


def test_missing_evidence_drives_research_next_bucket_and_reason_codes() -> None:
    result = report(
        candidate(
            missing_evidence_score=d("0.950000"),
            expected_gross_edge=d("0.090000"),
            expected_cost_drag=d("0.010000"),
            resolution_seconds=d("20000.000000"),
            source_age_seconds=d("10800.000000"),
            missing_evidence_codes=(
                "market_resolution_rule_missing",
                "contradictory_source_check_missing",
            ),
        ),
    )

    row = result.rows[0]
    assert row.bucket == "research_next"
    assert row.missing_evidence_score == d("0.950000")
    assert row.source_refresh_priority_score == d("1.000000")
    assert row.next_research_action == "collect_missing_evidence"
    assert row.reason_codes == (
        "contradictory_source_check_missing",
        "liquidity_cost_ready",
        "market_resolution_rule_missing",
        "missing_evidence_high",
        "net_edge_positive",
        "source_refresh_needed",
        "team_memory_ready",
    )


def test_cost_drag_and_liquidity_readiness_can_hold_candidate_in_watch() -> None:
    result = report(
        candidate(
            candidate_reference="candidate-clean-cost",
            market_id="raw-market-clean-cost",
            expected_gross_edge=d("0.120000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.800000"),
        ),
        candidate(
            candidate_reference="candidate-expensive-cost",
            market_id="raw-market-expensive-cost",
            expected_gross_edge=d("0.120000"),
            expected_cost_drag=d("0.080000"),
            missing_evidence_score=d("0.800000"),
        ),
        candidate(
            candidate_reference="candidate-thin-liquidity",
            market_id="raw-market-thin-liquidity",
            expected_gross_edge=d("0.120000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.800000"),
            available_liquidity=d("20.000000"),
        ),
    )

    assert tuple(row.bucket for row in result.rows) == (
        "research_next",
        "watch",
        "watch",
    )
    clean, expensive, thin = result.rows
    assert clean.liquidity_cost_readiness_score == d("0.861112")
    expensive = next(row for row in result.rows if "cost_drag_elevated" in row.reason_codes)
    thin = next(row for row in result.rows if "liquidity_thin" in row.reason_codes)
    assert expensive.expected_net_edge == d("0.040000")
    assert expensive.cost_drag_share == d("0.666667")
    assert expensive.liquidity_cost_readiness_score == d("0.500000")
    assert expensive.next_research_action == "wait_for_cost_readiness"
    assert thin.liquidity_cost_readiness_score == d("0.461112")


def test_team_memory_block_and_hard_block_reason_codes() -> None:
    result = report(
        candidate(
            candidate_reference="candidate-memory-block",
            market_id="raw-market-memory-block",
            team_memory_readiness_score=d("0.100000"),
        ),
        candidate(
            candidate_reference="candidate-policy-block",
            market_id="raw-market-policy-block",
            hard_block_reason_codes=("risk_policy_block",),
        ),
    )

    assert result.queue_status == "block"
    assert result.block_count == d("2")
    assert tuple(row.bucket for row in result.rows) == ("block", "block")
    memory_row = next(
        row for row in result.rows if "team_memory_not_ready" in row.reason_codes
    )
    policy_row = next(
        row for row in result.rows if "candidate_hard_flagged" in row.reason_codes
    )
    assert memory_row.next_research_action == "repair_team_memory_before_research"
    assert "risk_policy_block" in policy_row.reason_codes


def test_hard_flags_frozen_dataclasses_and_consistency_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_candidate_decision_research_priority_queue(
            (),
            config=object(),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(candidate(), readonly=False)
    with pytest.raises(ValueError, match="hard_block_reason_codes"):
        candidate(hard_block_reason_codes=("z_reason", "a_reason"))
    with pytest.raises(ValueError, match="rows"):
        replace(report(candidate()), rows=())

    frozen = candidate(candidate_reference="candidate-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.market_id = "changed"  # type: ignore[misc]


def test_empty_queue_is_watch_not_clear_or_blocked_recommendation() -> None:
    result = report()

    assert result.queue_status == "watch"
    assert result.input_count == ZERO
    assert result.research_next_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.highest_priority_score == ZERO
    assert result.rows == ()
    assert result.reason_codes == (
        "candidate_decision_research_priority_queue_empty",
    )


def test_public_payload_redacts_raw_market_question_source_and_candidate_values() -> None:
    module = api()
    raw_market = "raw-market-secret-wallet-token-123"
    raw_question = "Will the private wallet token question leak?"
    raw_source = "source-ref://private-wallet-token-source"
    result = report(
        candidate(
            candidate_reference="wallet-token-private-key-candidate",
            market_id=raw_market,
            question=raw_question,
            source_references=(raw_source,),
        ),
    )

    payload = module.candidate_decision_research_priority_queue_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert "rows" not in payload
    assert "redacted_candidate_reference" not in rendered
    assert "candidate_reference" not in rendered
    assert "candidate_ref_" not in rendered
    assert "market_id" not in rendered
    assert "market_slug" not in rendered
    assert "question" not in rendered
    assert "source_references" not in rendered
    assert "source-ref://" not in rendered
    assert raw_market.lower() not in rendered
    assert raw_question.lower() not in rendered
    assert raw_source.lower() not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert "private-key" not in rendered
    assert payload["highest_priority_score"] == "0.809940"
    assert_no_float_values(payload)


def test_public_payload_is_aggregate_redacted_and_decision_support_only() -> None:
    module = api()
    result = report(
        candidate(candidate_reference="candidate-order-alpha"),
        candidate(
            candidate_reference="candidate-trade-beta",
            expected_gross_edge=d("0.030000"),
            expected_cost_drag=d("0.010000"),
            missing_evidence_score=d("0.100000"),
            source_age_seconds=d("60.000000"),
        ),
        candidate(
            candidate_reference="candidate-auth-gamma",
            hard_block_reason_codes=("manual_policy_block",),
        ),
    )

    payload = module.candidate_decision_research_priority_queue_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION
        ),
        "queue_status": "block",
        "input_count": "3.000000",
        "research_next_count": "1.000000",
        "watch_count": "1.000000",
        "block_count": "1.000000",
        "highest_priority_score": "0.809940",
            "reason_codes": [
                "research_next_ready",
                "watch_research_later",
                "research_block",
                "missing_evidence_high",
                "resolution_urgent",
                "source_refresh_needed",
                "cost_drag_elevated",
                "liquidity_cost_ready",
                "liquidity_cost_not_ready",
                "team_memory_ready",
                "candidate_hard_flagged",
            ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    for public_status in ("research_next", "watch", "block"):
        assert public_status in rendered
    for forbidden in (
        "candidate-order-alpha",
        "candidate-trade-beta",
        "candidate-auth-gamma",
        "redacted_candidate_reference",
        "candidate_ref_",
        "market",
        "slug",
        "question",
        "source_references",
        "source-ref",
        "url",
        "dsn",
        "table",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "size",
        "buy",
        "sell",
        "token",
        "private",
        "secret",
        "blocked",
    ):
        assert forbidden not in rendered


def test_public_payload_rejects_unsafe_public_config_text() -> None:
    module = api()
    result = report(
        candidate(),
        cfg=config(config_version="wallet_auth_order_trade_token_secret"),
    )

    with pytest.raises(ValueError, match="unsafe public payload"):
        module.candidate_decision_research_priority_queue_payload(result)


def test_decimal_only_validation_and_payload_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="missing_evidence_score"):
        candidate(missing_evidence_score=0.5)
    with pytest.raises(ValueError, match="expected_cost_drag"):
        candidate(expected_cost_drag=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="source_age_seconds"):
        candidate(source_age_seconds=Decimal("NaN"))

    result = report(candidate())
    for value in (result, *result.rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_edge",
                    "_share",
                    "_seconds",
                    "_liquidity",
                    "_rank",
                ),
            ):
                assert type(item_value) is Decimal

    payload = module.candidate_decision_research_priority_queue_payload(result)
    assert payload["input_count"] == "1.000000"
    assert payload["highest_priority_score"] == "0.809940"
    assert_no_float_values(payload)


def test_deterministic_output_is_independent_of_input_sequence() -> None:
    module = api()
    candidates = (
        candidate(candidate_reference="candidate-zulu", market_id="raw-market-zulu"),
        candidate(candidate_reference="candidate-alpha", market_id="raw-market-alpha"),
        candidate(candidate_reference="candidate-bravo", market_id="raw-market-bravo"),
    )

    first = module.candidate_decision_research_priority_queue_payload(
        report(*candidates),
    )
    second = module.candidate_decision_research_priority_queue_payload(
        report(*reversed(candidates)),
    )

    assert first == second
    assert "rows" not in first


def test_public_api_and_static_pure_boundary_guard() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION",
        "CandidateDecisionResearchCandidateAggregate",
        "CandidateDecisionResearchPriorityQueueConfig",
        "CandidateDecisionResearchPriorityQueueReport",
        "CandidateDecisionResearchPriorityQueueRow",
        "build_candidate_decision_research_priority_queue",
        "candidate_decision_research_priority_queue_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src/polymarket_alpha_lab/candidate_decision_research_priority_queue.py"
    )
    source = source_path.read_text()
    lowered_source = source.lower()
    forbidden_terms = (
        "account",
        "api_key",
        "auth",
        "cancel",
        "dotenv",
        "exchange",
        "private_key",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    for term in forbidden_terms:
        assert term not in lowered_source
    assert "os.environ" not in lowered_source

    tree = ast.parse(source)
    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "getenv",
        "open",
        "patch",
        "post",
        "put",
        "read",
        "request",
        "run",
        "system",
        "write",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float literal found: {node.value!r}")

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
