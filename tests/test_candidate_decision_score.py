from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.candidate_decision_score")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_CANDIDATE_DECISION_SCORE_CONFIG_VERSION,
        "min_component_score_for_paper_recommend": d("0.650000"),
        "min_decision_score_for_paper_recommend": d("0.700000"),
        "min_net_edge_for_paper_recommend": d("0.010000"),
        "evidence_block_score": d("0.350000"),
        "resolution_block_score": d("0.350000"),
        "liquidity_block_score": d("0.250000"),
    }
    values.update(overrides)
    return module.CandidateDecisionScoreConfig(**values)


def decision_input(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-btc-fed-001",
        "market_id": "market-btc-fed-001",
        "normalized_market_question": "btc above threshold after fed decision",
        "primary_team_id": "crypto_btc",
        "secondary_team_ids": ("macro_rates",),
        "selected_side": "yes",
        "forecast_probability": d("0.620000"),
        "executable_price": d("0.570000"),
        "gross_edge": d("0.050000"),
        "estimated_cost_drag": d("0.015000"),
        "cost_score": d("0.780000"),
        "liquidity_score": d("0.740000"),
        "evidence_score": d("0.810000"),
        "resolution_score": d("0.760000"),
        "team_memory_score": d("0.720000"),
        "team_memory_policy": "allow",
        "source_report_refs": ("evidence-digest:abc123", "liquidity-report:def456"),
        "adapter_reason_codes": ("source_quorum_met", "cost_drag_acceptable"),
    }
    values.update(overrides)
    return module.CandidateDecisionScoreInput(**values)


def report(input_value=None, cfg=None):
    module = api()
    return module.build_candidate_decision_score_report(
        input_value or decision_input(),
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_builds_paper_recommend_decision_with_net_edge_and_digest() -> None:
    module = api()
    decision = report()

    assert type(decision) is module.CandidateDecisionScoreReport
    assert is_dataclass(decision)
    assert decision.generated_at == GENERATED_AT
    assert decision.config_version == "candidate-decision-score-v0"
    assert decision.action == "paper_recommend"
    assert decision.candidate_id == "candidate-btc-fed-001"
    assert decision.primary_team_id == "crypto_btc"
    assert decision.secondary_team_ids == ("macro_rates",)
    assert decision.selected_side == "yes"
    assert decision.gross_edge == d("0.050000")
    assert decision.estimated_cost_drag == d("0.015000")
    assert decision.net_edge == d("0.035000")
    assert decision.decision_score == d("0.762000")
    assert decision.reason_codes == (
        "candidate_decision_paper_recommend",
        "cost_drag_acceptable",
        "source_quorum_met",
    )
    assert decision.hard_blocker_codes == ()
    assert decision.boundary_statement == module.BOUNDARY_STATEMENT
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True
    assert len(decision.derived_validation_digest) == 64
    assert all(char in "0123456789abcdef" for char in decision.derived_validation_digest)


def test_hard_blockers_reject_before_positive_edge_or_high_average_score() -> None:
    decision = report(
        decision_input(
            evidence_score=d("0.300000"),
            resolution_score=d("0.300000"),
            team_memory_policy="block",
            gross_edge=d("0.200000"),
            estimated_cost_drag=d("0.010000"),
            cost_score=d("1.000000"),
            liquidity_score=d("1.000000"),
            team_memory_score=d("1.000000"),
        ),
    )

    assert decision.action == "reject"
    assert decision.net_edge == d("0.190000")
    assert decision.decision_score == d("0.720000")
    assert decision.hard_blocker_codes == (
        "evidence_score_below_blocking_threshold",
        "resolution_score_below_blocking_threshold",
        "team_memory_policy_blocked",
    )
    assert decision.reason_codes == (
        "candidate_decision_reject",
        "evidence_score_below_blocking_threshold",
        "resolution_score_below_blocking_threshold",
        "team_memory_policy_blocked",
    )


def test_research_more_and_watch_states_are_separated_from_promotion() -> None:
    research = report(
        decision_input(
            evidence_score=d("0.640000"),
            team_memory_policy="throttle",
        ),
    )
    watch = report(
        decision_input(
            gross_edge=d("0.020000"),
            estimated_cost_drag=d("0.015000"),
        ),
    )
    missing_edge = report(
        decision_input(
            gross_edge=None,
            estimated_cost_drag=d("0.015000"),
        ),
    )

    assert research.action == "research_more"
    assert research.reason_codes == (
        "candidate_decision_research_more",
        "component_score_below_paper_recommend_threshold",
        "cost_drag_acceptable",
        "source_quorum_met",
        "team_memory_policy_throttled",
    )
    assert watch.action == "watch"
    assert watch.net_edge == d("0.005000")
    assert watch.reason_codes == (
        "candidate_decision_watch",
        "cost_drag_acceptable",
        "net_edge_below_paper_recommend_threshold",
        "source_quorum_met",
    )
    assert missing_edge.action == "research_more"
    assert missing_edge.net_edge is None
    assert "net_edge_missing" in missing_edge.reason_codes


def test_validation_rejects_bad_types_values_flags_and_team_ids() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("candidate-decision-score-v0"))
    with pytest.raises(ValueError, match="min_net_edge_for_paper_recommend"):
        config(min_net_edge_for_paper_recommend=d("-0.010000"))
    with pytest.raises(ValueError, match="cost_score"):
        decision_input(cost_score=0.8)
    with pytest.raises(ValueError, match="evidence_score"):
        decision_input(evidence_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="primary_team_id"):
        decision_input(primary_team_id="general")
    with pytest.raises(ValueError, match="secondary_team_ids"):
        decision_input(secondary_team_ids=("macro_rates", "macro_rates"))
    with pytest.raises(ValueError, match="selected_side"):
        decision_input(selected_side="maybe")
    with pytest.raises(ValueError, match="team_memory_policy"):
        decision_input(team_memory_policy="maybe")
    with pytest.raises(ValueError, match="paper_only"):
        decision_input(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_candidate_decision_score_report(
            decision_input(),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="CandidateDecisionScoreInput"):
        module.build_candidate_decision_score_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )

    offset = module.build_candidate_decision_score_report(
        decision_input(),
        config=config(),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert offset.generated_at == GENERATED_AT


def test_report_is_frozen_consistent_and_payload_is_json_ready() -> None:
    module = api()
    decision = report()
    rebuilt = report()
    changed = report(decision_input(cost_score=d("0.790000")))

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_SCORE_CONFIG_VERSION",
        "BOUNDARY_STATEMENT",
        "CandidateDecisionScoreConfig",
        "CandidateDecisionScoreInput",
        "CandidateDecisionScoreReport",
        "build_candidate_decision_score_report",
        "candidate_decision_score_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        decision.action = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="net_edge"):
        replace(decision, net_edge=d("0.040000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decision, derived_validation_digest="0" * 64)

    assert decision.derived_validation_digest == rebuilt.derived_validation_digest
    assert decision.derived_validation_digest != changed.derived_validation_digest

    payload = module.candidate_decision_score_payload(decision)
    payload_text = repr(payload).lower()
    assert payload["decision_score"] == "0.762000"
    assert payload["net_edge"] == "0.035000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in payload_text
    assert "private_key" not in payload_text
    assert "api_key" not in payload_text
    assert "secret" not in payload_text
    assert "token" not in payload_text
    assert asdict(decision)["readonly"] is True


def test_static_module_has_no_network_database_or_execution_surfaces() -> None:
    source = Path("src/polymarket_alpha_lab/candidate_decision_score.py").read_text(
        encoding="utf-8",
    )
    lowered = source.lower()
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        ".write(",
        "private_key",
        "wallet",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
