from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_research_source_family_independence_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def source_input(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "market_slug": "fed-cut-by-september",
        "source_count": d("12"),
        "source_family_count": d("4"),
        "required_family_count": d("3"),
        "largest_source_family_count": d("4"),
        "direct_source_count": d("7"),
        "contradicting_source_count": d("1"),
        "recent_source_count": d("10"),
    }
    values.update(overrides)
    return module.ResearchSourceFamilyIndependenceV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.strategy_research_source_family_independence_v10(
        source_input(**overrides),
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(walk(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(walk(child))
        return tuple(items)
    return (value,)


def test_independent_packet_scores_source_family_quality_and_payload() -> None:
    module = api()

    result = evaluate()

    assert is_dataclass(result)
    assert result == module.ResearchSourceFamilyIndependenceV10Report(
        packet_id="packet-alpha",
        market_slug="fed-cut-by-september",
        source_count=d("12"),
        source_family_count=d("4"),
        required_family_count=d("3"),
        largest_source_family_count=d("4"),
        direct_source_count=d("7"),
        contradicting_source_count=d("1"),
        recent_source_count=d("10"),
        family_count_score=d("1.000000"),
        repeated_source_concentration=d("0.333333"),
        concentration_independence_score=d("0.666667"),
        direct_source_share=d("0.583333"),
        contradiction_rate=d("0.083333"),
        contradiction_quality_score=d("0.916667"),
        recency_coverage=d("0.833333"),
        independence_score=d("0.820833"),
        independence_status="independent",
        recommendation="use_packet",
        reason_codes=(
            "family_count_met",
            "concentration_balanced",
            "direct_share_strong",
            "contradiction_rate_low",
            "recency_coverage_current",
            "independence_independent",
        ),
    )
    assert type(result.independence_score) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == module.strategy_research_source_family_independence_v10_payload(result)
    assert payload["config_version"] == "strategy-research-source-family-independence-v10"
    assert payload["source_count"] == "12.000000"
    assert payload["independence_score"] == "0.820833"
    assert payload["independence_status"] == "independent"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_family_quorum_shortfall_blocks_even_when_other_signals_are_usable() -> None:
    result = evaluate(
        source_count=d("6"),
        source_family_count=d("2"),
        required_family_count=d("3"),
        largest_source_family_count=d("4"),
        direct_source_count=d("3"),
        contradicting_source_count=d("0"),
        recent_source_count=d("5"),
    )

    assert result.independence_status == "blocked"
    assert result.recommendation == "block_until_family_quorum"
    assert result.independence_score == d("0.633333")
    assert result.family_count_score == d("0.666667")
    assert result.reason_codes == (
        "family_count_insufficient",
        "concentration_elevated",
        "direct_share_strong",
        "contradiction_rate_low",
        "recency_coverage_current",
        "independence_blocked",
    )


def test_watch_status_flags_concentration_and_direct_source_followup() -> None:
    result = evaluate(
        source_count=d("8"),
        source_family_count=d("3"),
        required_family_count=d("3"),
        largest_source_family_count=d("5"),
        direct_source_count=d("2"),
        contradicting_source_count=d("2"),
        recent_source_count=d("5"),
    )

    assert result.independence_status == "watch"
    assert result.recommendation == "add_confirming_direct_source"
    assert result.independence_score == d("0.650000")
    assert result.repeated_source_concentration == d("0.625000")
    assert result.direct_source_share == d("0.250000")
    assert result.contradiction_rate == d("0.250000")
    assert result.recency_coverage == d("0.625000")
    assert result.reason_codes == (
        "family_count_met",
        "concentration_elevated",
        "direct_share_adequate",
        "contradiction_rate_moderate",
        "recency_coverage_partial",
        "independence_watch",
    )


def test_validation_requires_exact_decimals_bounds_flags_and_frozen_outputs() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.independence_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        source_input(source_count=12)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="direct_source_count must be a Decimal"):
        source_input(direct_source_count=_DecimalSubclass("7"))

    with pytest.raises(ValueError, match="source_family_count must not exceed source_count"):
        source_input(source_count=d("3"), source_family_count=d("4"))

    with pytest.raises(ValueError, match="largest_source_family_count must not exceed"):
        source_input(
            source_count=d("3"),
            source_family_count=d("3"),
            largest_source_family_count=d("4"),
        )

    with pytest.raises(ValueError, match="required_family_count must be positive"):
        source_input(required_family_count=d("0"))

    with pytest.raises(ValueError, match="recent_source_count must be a whole Decimal"):
        source_input(recent_source_count=d("1.5"))

    with pytest.raises(ValueError, match="market_slug must be a canonical nonblank string"):
        source_input(market_slug=" fed-cut-by-september ")

    with pytest.raises(ValueError, match="input must be paper_only"):
        source_input(paper_only=False)

    with pytest.raises(ValueError, match="report must be readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="independence_score must match input fields"):
        module.ResearchSourceFamilyIndependenceV10Report(
            packet_id="packet-alpha",
            market_slug="fed-cut-by-september",
            source_count=d("12"),
            source_family_count=d("4"),
            required_family_count=d("3"),
            largest_source_family_count=d("4"),
            direct_source_count=d("7"),
            contradicting_source_count=d("1"),
            recent_source_count=d("10"),
            family_count_score=d("1.000000"),
            repeated_source_concentration=d("0.333333"),
            concentration_independence_score=d("0.666667"),
            direct_source_share=d("0.583333"),
            contradiction_rate=d("0.083333"),
            contradiction_quality_score=d("0.916667"),
            recency_coverage=d("0.833333"),
            independence_score=d("0.100000"),
            independence_status="independent",
            recommendation="use_packet",
            reason_codes=result.reason_codes,
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.strategy_research_source_family_independence_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_research_source_family_independence_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "independence_score": 0.1,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_research_source_family_independence_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "source_count": 12,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_research_source_family_independence_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "extra": "field"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_research_source_family_independence_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_source_family_independence_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "signing",
        "submit_order",
        "cancel_order",
        "place_order",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "clob",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
