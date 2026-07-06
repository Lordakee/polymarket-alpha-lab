from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_market_candidate_triage_v10 as triage_module
from polymarket_alpha_lab.strategy_market_candidate_triage_v10 import (
    StrategyMarketCandidateTriageV10Config,
    StrategyMarketCandidateTriageV10Input,
    StrategyMarketCandidateTriageV10Payload,
    StrategyMarketCandidateTriageV10Result,
    build_strategy_market_candidate_triage_v10_result,
    strategy_market_candidate_triage_v10_payload,
    triage_strategy_market_candidate_v10,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyMarketCandidateTriageV10Config:
    values = {
        "config_version": "strategy-market-candidate-triage-v10",
        "minimum_information_edge_score": d("0.550000"),
        "minimum_expected_value_score": d("0.550000"),
        "minimum_liquidity_score": d("0.400000"),
        "maximum_resolution_risk_score": d("0.650000"),
        "minimum_team_fit_score": d("0.500000"),
        "maximum_cost_drag_score": d("0.550000"),
        "minimum_time_to_resolution_minutes": d("60.000000"),
        "minimum_pass_composite_score": d("0.650000"),
        "rank_band_a_minimum_score": d("0.800000"),
        "rank_band_b_minimum_score": d("0.650000"),
        "rank_band_c_minimum_score": d("0.500000"),
        "information_edge_weight": d("0.250000"),
        "expected_value_weight": d("0.250000"),
        "liquidity_weight": d("0.200000"),
        "team_fit_weight": d("0.150000"),
        "resolution_quality_weight": d("0.100000"),
        "cost_quality_weight": d("0.050000"),
    }
    values.update(overrides)
    return StrategyMarketCandidateTriageV10Config(**values)


def candidate(**overrides: object) -> StrategyMarketCandidateTriageV10Input:
    values = {
        "market_id": "market-alpha",
        "category": "Macro policy",
        "information_edge_score": d("0.900000"),
        "expected_value_score": d("0.880000"),
        "liquidity_score": d("0.800000"),
        "resolution_risk_score": d("0.200000"),
        "team_fit_score": d("0.850000"),
        "cost_drag_score": d("0.100000"),
        "time_to_resolution_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return StrategyMarketCandidateTriageV10Input(**values)


def result(
    candidate_row: StrategyMarketCandidateTriageV10Input | None = None,
    *,
    cfg: StrategyMarketCandidateTriageV10Config | None = None,
) -> StrategyMarketCandidateTriageV10Result:
    return build_strategy_market_candidate_triage_v10_result(
        candidate_row or candidate(),
        config=cfg or config(),
    )


def test_pass_candidate_returns_ranked_readonly_payload() -> None:
    triage = result()

    assert is_dataclass(triage)
    assert triage.triage_status == "pass"
    assert triage.triage_rank_band == "A"
    assert triage.recommended_next_step == "advance_to_readonly_research_packet"
    assert triage.blocking_reasons == ()
    assert triage.reason_codes == ("candidate_triage_clear",)
    assert triage.paper_only is True
    assert triage.report_only is True
    assert triage.readonly is True

    assert triage.payload.market_id == "market-alpha"
    assert triage.payload.category == "Macro policy"
    assert triage.payload.resolution_quality_score == d("0.800000")
    assert triage.payload.cost_quality_score == d("0.900000")
    assert triage.payload.composite_score == d("0.857500")
    assert type(triage.payload.composite_score) is Decimal

    payload = strategy_market_candidate_triage_v10_payload(triage)
    assert payload["triage_status"] == "pass"
    assert payload["payload"]["composite_score"] == "0.857500"
    assert payload["payload"]["time_to_resolution_minutes"] == "1440.000000"
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_watch_candidate_keeps_rank_band_and_reason_codes() -> None:
    triage = result(
        candidate(
            information_edge_score=d("0.500000"),
            expected_value_score=d("0.500000"),
        ),
    )

    assert triage.triage_status == "watch"
    assert triage.triage_rank_band == "B"
    assert triage.recommended_next_step == "refresh_scores_before_specialist_review"
    assert triage.blocking_reasons == ()
    assert triage.reason_codes == (
        "candidate_information_edge_watch",
        "candidate_expected_value_watch",
    )
    assert triage.payload.composite_score == d("0.662500")


def test_blocked_candidate_reports_hard_blockers_and_rank_band_d() -> None:
    triage = result(
        candidate(
            liquidity_score=d("0.200000"),
            resolution_risk_score=d("0.800000"),
            team_fit_score=d("0.300000"),
            cost_drag_score=d("0.800000"),
            time_to_resolution_minutes=d("30.000000"),
        ),
    )

    assert triage.triage_status == "blocked"
    assert triage.triage_rank_band == "D"
    assert triage.recommended_next_step == "do_not_advance_until_blockers_clear"
    assert triage.blocking_reasons == (
        "liquidity_score_below_floor",
        "resolution_risk_score_above_limit",
        "team_fit_score_below_floor",
        "cost_drag_score_above_limit",
        "time_to_resolution_below_floor",
    )
    assert triage.reason_codes == (
        "candidate_liquidity_score_below_floor_blocked",
        "candidate_resolution_risk_score_above_limit_blocked",
        "candidate_team_fit_score_below_floor_blocked",
        "candidate_cost_drag_score_above_limit_blocked",
        "candidate_time_to_resolution_below_floor_blocked",
    )


def test_direct_function_accepts_required_input_surface() -> None:
    triage = triage_strategy_market_candidate_v10(
        market_id="market-direct",
        category="Sports",
        information_edge_score=d("0.700000"),
        expected_value_score=d("0.720000"),
        liquidity_score=d("0.750000"),
        resolution_risk_score=d("0.300000"),
        team_fit_score=d("0.800000"),
        cost_drag_score=d("0.120000"),
        time_to_resolution_minutes=d("720.000000"),
    )

    assert triage.triage_status == "pass"
    assert triage.triage_rank_band == "B"
    assert triage.payload.market_id == "market-direct"
    assert triage.payload.composite_score == d("0.739000")


def test_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    cfg = config()
    candidate_row = candidate()
    triage = result(candidate_row, cfg=cfg)

    for dataclass_type in (
        StrategyMarketCandidateTriageV10Config,
        StrategyMarketCandidateTriageV10Input,
        StrategyMarketCandidateTriageV10Payload,
        StrategyMarketCandidateTriageV10Result,
    ):
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        triage.triage_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage.payload.composite_score = d("0.000000")  # type: ignore[misc]

    decimal_fields_by_object = (
        (
            cfg,
            (
                "minimum_information_edge_score",
                "minimum_expected_value_score",
                "minimum_liquidity_score",
                "maximum_resolution_risk_score",
                "minimum_team_fit_score",
                "maximum_cost_drag_score",
                "minimum_time_to_resolution_minutes",
                "minimum_pass_composite_score",
                "rank_band_a_minimum_score",
                "rank_band_b_minimum_score",
                "rank_band_c_minimum_score",
                "information_edge_weight",
                "expected_value_weight",
                "liquidity_weight",
                "team_fit_weight",
                "resolution_quality_weight",
                "cost_quality_weight",
            ),
        ),
        (
            candidate_row,
            (
                "information_edge_score",
                "expected_value_score",
                "liquidity_score",
                "resolution_risk_score",
                "team_fit_score",
                "cost_drag_score",
                "time_to_resolution_minutes",
            ),
        ),
        (
            triage.payload,
            (
                "information_edge_score",
                "expected_value_score",
                "liquidity_score",
                "resolution_risk_score",
                "team_fit_score",
                "cost_drag_score",
                "time_to_resolution_minutes",
                "resolution_quality_score",
                "cost_quality_score",
                "composite_score",
            ),
        ),
    )
    for item, field_names in decimal_fields_by_object:
        for field_name in field_names:
            assert type(getattr(item, field_name)) is Decimal
        for field_name, value in item.__dict__.items():
            assert type(value) not in (int, float), field_name


def test_validation_rejects_bad_scores_flags_and_inconsistent_objects() -> None:
    with pytest.raises(ValueError, match="market_id"):
        candidate(market_id=" market-alpha")
    with pytest.raises(ValueError, match="category"):
        candidate(category="")
    with pytest.raises(ValueError, match="information_edge_score"):
        candidate(information_edge_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="expected_value_score"):
        candidate(expected_value_score=d("1.000001"))
    with pytest.raises(ValueError, match="liquidity_score"):
        candidate(liquidity_score=d("-0.000001"))
    with pytest.raises(ValueError, match="resolution_risk_score"):
        candidate(resolution_risk_score=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes"):
        candidate(time_to_resolution_minutes=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="rank band"):
        config(rank_band_a_minimum_score=d("0.600000"))
    with pytest.raises(ValueError, match="score weights"):
        config(cost_quality_weight=d("0.060000"))
    with pytest.raises(ValueError, match="candidate must be"):
        build_strategy_market_candidate_triage_v10_result(
            object(),  # type: ignore[arg-type]
            config=config(),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result(), readonly=False)
    with pytest.raises(ValueError, match="triage_status"):
        replace(result(), triage_status="blocked")


def test_payload_rejects_flag_downgrades_and_unsafe_public_text() -> None:
    with pytest.raises(ValueError, match="readonly"):
        strategy_market_candidate_triage_v10_payload(
            {
                "triage_status": "pass",
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )

    with pytest.raises(ValueError, match="unsafe"):
        candidate(market_id="market-" + "wal" "let")

    with pytest.raises(ValueError, match="unsafe"):
        strategy_market_candidate_triage_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "summary": "contains " + "sign" + "al surface",
            },
        )


def test_module_surface_stays_report_only_without_external_side_effects() -> None:
    source = inspect.getsource(triage_module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    float_literals: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)

    forbidden_imports = {
        "os",
        "pathlib",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "open",
        "urlopen",
        "submit_" + "order",
        "cancel_" + "order",
        "sign_" + "order",
        "place_" + "order",
    }
    forbidden_fragments = (
        "li" "ve",
        "trad" "ing",
        "au" "th",
        "wal" "let",
        "or" "der",
        "sign",
        "private" "_" "key",
        "bro" "ker",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
