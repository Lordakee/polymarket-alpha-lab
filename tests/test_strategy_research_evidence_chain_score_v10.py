from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from json import dumps

import pytest

import polymarket_alpha_lab.strategy_research_evidence_chain_score_v10 as score_module
from polymarket_alpha_lab.strategy_research_evidence_chain_score_v10 import (
    StrategyResearchEvidenceChainScoreV10Config,
    StrategyResearchEvidenceChainScoreV10Input,
    StrategyResearchEvidenceChainScoreV10Result,
    score_strategy_research_evidence_chain_score_v10,
    strategy_research_evidence_chain_score_v10_payload,
)


ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object) -> StrategyResearchEvidenceChainScoreV10Input:
    values = {
        "evidence_item_count": d("5"),
        "independent_source_count": d("3"),
        "primary_source_count": d("1"),
        "contradiction_count": d("0"),
        "average_source_reliability": d("0.900000"),
        "freshness_weight": d("0.800000"),
        "resolution_alignment_score": d("0.900000"),
    }
    values.update(overrides)
    return StrategyResearchEvidenceChainScoreV10Input(**values)


def score(
    item: StrategyResearchEvidenceChainScoreV10Input,
    *,
    cfg: StrategyResearchEvidenceChainScoreV10Config | None = None,
) -> StrategyResearchEvidenceChainScoreV10Result:
    return score_strategy_research_evidence_chain_score_v10(
        item,
        config=cfg or StrategyResearchEvidenceChainScoreV10Config(),
    )


def test_evidence_chain_score_v10_passes_strong_evidence_chain() -> None:
    result = score(evidence())

    assert result == StrategyResearchEvidenceChainScoreV10Result(
        config_version="strategy-research-evidence-chain-score-v10",
        evidence_item_count=d("5"),
        independent_source_count=d("3"),
        primary_source_count=d("1"),
        contradiction_count=d("0"),
        average_source_reliability=d("0.900000"),
        freshness_weight=d("0.800000"),
        resolution_alignment_score=d("0.900000"),
        evidence_chain_score=d("0.945000"),
        evidence_chain_status="pass",
        needs_more_sources=False,
        reason_codes=("evidence_chain_passed",),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_evidence_chain_score_v10_watches_source_quorum_gaps() -> None:
    result = score(
        evidence(
            evidence_item_count=d("2"),
            independent_source_count=d("1"),
            primary_source_count=d("0"),
            average_source_reliability=d("0.800000"),
            freshness_weight=d("0.700000"),
            resolution_alignment_score=d("0.800000"),
        ),
    )

    assert result.evidence_chain_score == d("0.583333")
    assert result.evidence_chain_status == "watch"
    assert result.needs_more_sources is True
    assert result.reason_codes == (
        "insufficient_evidence_items",
        "insufficient_independent_sources",
        "missing_primary_source",
        "evidence_chain_watch_score",
    )


def test_evidence_chain_score_v10_blocks_contradictory_chain() -> None:
    result = score(
        evidence(
            contradiction_count=d("1"),
            average_source_reliability=d("0.700000"),
            freshness_weight=d("0.800000"),
            resolution_alignment_score=d("0.800000"),
        ),
    )

    assert result.evidence_chain_score == d("0.640000")
    assert result.evidence_chain_status == "blocked"
    assert result.needs_more_sources is True
    assert result.reason_codes == (
        "source_contradictions_present",
        "evidence_chain_watch_score",
    )


def test_evidence_chain_score_v10_payload_is_json_ready_readonly_and_decimal_safe() -> None:
    result = score(evidence())
    payload = strategy_research_evidence_chain_score_v10_payload(result)

    dumps(payload, sort_keys=True)
    assert result.payload == payload
    assert payload["config_version"] == "strategy-research-evidence-chain-score-v10"
    assert payload["evidence_item_count"] == "5"
    assert payload["average_source_reliability"] == "0.900000"
    assert payload["evidence_chain_score"] == "0.945000"
    assert payload["evidence_chain_status"] == "pass"
    assert payload["needs_more_sources"] is False
    assert payload["reason_codes"] == ["evidence_chain_passed"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)


def test_evidence_chain_score_v10_validates_decimal_types_counts_ratios_and_flags() -> None:
    result = score(evidence())

    with pytest.raises(FrozenInstanceError):
        result.evidence_chain_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="evidence_item_count must be a Decimal"):
        evidence(evidence_item_count=5)
    with pytest.raises(ValueError, match="average_source_reliability must be a Decimal"):
        evidence(average_source_reliability=0.9)
    with pytest.raises(ValueError, match="freshness_weight must be a Decimal"):
        evidence(freshness_weight=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="evidence_item_count must be a whole Decimal"):
        evidence(evidence_item_count=d("2.500000"))
    with pytest.raises(ValueError, match="resolution_alignment_score must be between"):
        evidence(resolution_alignment_score=d("1.000001"))
    with pytest.raises(ValueError, match="primary_source_count must not exceed"):
        evidence(evidence_item_count=d("1"), primary_source_count=d("2"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        evidence(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        StrategyResearchEvidenceChainScoreV10Config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_evidence_chain_score_v10_rejects_manual_inconsistent_outputs() -> None:
    valid = score(evidence())

    with pytest.raises(ValueError, match="pass result must not need more sources"):
        replace(valid, needs_more_sources=True)
    with pytest.raises(ValueError, match="evidence_chain_passed requires pass status"):
        replace(valid, evidence_chain_status="watch")
    with pytest.raises(ValueError, match="needs_more_sources must include"):
        replace(
            valid,
            evidence_chain_status="watch",
            needs_more_sources=True,
            reason_codes=("low_average_source_reliability",),
        )
    with pytest.raises(ValueError, match="blocked result must include"):
        StrategyResearchEvidenceChainScoreV10Result(
            config_version=valid.config_version,
            evidence_item_count=valid.evidence_item_count,
            independent_source_count=valid.independent_source_count,
            primary_source_count=valid.primary_source_count,
            contradiction_count=valid.contradiction_count,
            average_source_reliability=d("0.100000"),
            freshness_weight=valid.freshness_weight,
            resolution_alignment_score=valid.resolution_alignment_score,
            evidence_chain_score=d("0.490000"),
            evidence_chain_status="blocked",
            needs_more_sources=False,
            reason_codes=("low_average_source_reliability",),
        )


def test_evidence_chain_score_v10_accepts_only_exact_input_and_config_types() -> None:
    with pytest.raises(
        ValueError,
        match="evidence must be a StrategyResearchEvidenceChainScoreV10Input",
    ):
        score_strategy_research_evidence_chain_score_v10(object())  # type: ignore[arg-type]
    with pytest.raises(
        ValueError,
        match="config must be a StrategyResearchEvidenceChainScoreV10Config",
    ):
        score_strategy_research_evidence_chain_score_v10(
            evidence(),
            config=object(),  # type: ignore[arg-type]
        )


def test_evidence_chain_score_v10_public_numeric_annotations_are_decimal() -> None:
    decimal_fields = {
        "StrategyResearchEvidenceChainScoreV10Config": {
            "minimum_evidence_item_count",
            "minimum_independent_source_count",
            "minimum_primary_source_count",
            "maximum_contradiction_count",
            "minimum_average_source_reliability",
            "minimum_freshness_weight",
            "minimum_resolution_alignment_score",
            "pass_score_threshold",
            "watch_score_threshold",
            "evidence_item_weight",
            "independent_source_weight",
            "primary_source_weight",
            "reliability_weight",
            "freshness_weight_weight",
            "resolution_alignment_weight",
            "contradiction_penalty_weight",
        },
        "StrategyResearchEvidenceChainScoreV10Input": {
            "evidence_item_count",
            "independent_source_count",
            "primary_source_count",
            "contradiction_count",
            "average_source_reliability",
            "freshness_weight",
            "resolution_alignment_score",
        },
        "StrategyResearchEvidenceChainScoreV10Result": {
            "evidence_item_count",
            "independent_source_count",
            "primary_source_count",
            "contradiction_count",
            "average_source_reliability",
            "freshness_weight",
            "resolution_alignment_score",
            "evidence_chain_score",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(score_module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


def test_evidence_chain_score_v10_has_no_live_trading_persistence_or_network_surface() -> None:
    source = inspect.getsource(score_module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "urllib",
        "web3",
    }
    forbidden_calls = {"open", "connect", "request", "urlopen"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
    lowered = source.lower()
    for token in ("wallet", "private_key", "signing", "order placement", "live trading"):
        assert token not in lowered


def _assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected concrete numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)
