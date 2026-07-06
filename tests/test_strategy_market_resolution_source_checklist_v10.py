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
        "polymarket_alpha_lab.strategy_market_resolution_source_checklist_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def checklist(**overrides: object):
    module = api()
    values = {
        "market_id": "market-001",
        "category": "politics",
        "resolution_source_family": "official",
        "official_source_score": d("0.900000"),
        "precedent_score": d("0.800000"),
        "rule_change_status": "stable",
        "time_to_resolution_minutes": d("720.000000"),
    }
    values.update(overrides)
    return module.MarketResolutionSourceChecklistV10Input(**values)


def evaluate(**overrides: object):
    return api().strategy_market_resolution_source_checklist_v10(
        checklist(**overrides),
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


def test_ready_official_resolution_source_returns_readonly_payload() -> None:
    result = evaluate()

    assert is_dataclass(result)
    assert result.checklist_status == "ready"
    assert result.required_checks == (
        "official_resolution_source_identified",
        "official_source_score_review",
        "precedent_alignment_review",
        "rule_change_review",
        "resolution_window_review",
    )
    assert result.missing_checks == ()
    assert result.reason_codes == (
        "resolution_source_family_official",
        "official_source_score_high",
        "precedent_score_high",
        "rule_change_status_stable",
        "resolution_window_normal",
        "checklist_ready",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == api().strategy_market_resolution_source_checklist_v10_payload(
        result,
    )
    assert payload["config_version"] == (
        "strategy-market-resolution-source-checklist-v10"
    )
    assert payload["market_id"] == "market-001"
    assert payload["official_source_score"] == "0.900000"
    assert payload["precedent_score"] == "0.800000"
    assert payload["time_to_resolution_minutes"] == "720.000000"
    assert payload["checklist_status"] == "ready"
    assert payload["missing_checks"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_unofficial_pending_imminent_resolution_is_blocked() -> None:
    result = evaluate(
        resolution_source_family="social",
        official_source_score=d("0.400000"),
        precedent_score=d("0.400000"),
        rule_change_status="pending",
        time_to_resolution_minutes=d("30.000000"),
    )

    assert result.checklist_status == "blocked"
    assert result.required_checks == (
        "official_resolution_source_identified",
        "official_source_score_review",
        "precedent_alignment_review",
        "rule_change_review",
        "resolution_window_review",
        "independent_source_family_crosscheck",
        "rule_change_confirmation",
        "imminent_resolution_timestamp_check",
    )
    assert result.missing_checks == (
        "official_resolution_source_identified",
        "official_source_score_review",
        "precedent_alignment_review",
        "independent_source_family_crosscheck",
        "rule_change_confirmation",
        "imminent_resolution_timestamp_check",
    )
    assert result.reason_codes == (
        "resolution_source_family_unofficial",
        "official_source_score_low",
        "precedent_score_low",
        "rule_change_status_pending",
        "resolution_window_imminent",
        "checklist_blocked",
    )


def test_official_source_with_medium_score_requires_review_not_block() -> None:
    result = evaluate(official_source_score=d("0.650000"))

    assert result.checklist_status == "review_required"
    assert result.missing_checks == ("official_source_score_review",)
    assert result.reason_codes == (
        "resolution_source_family_official",
        "official_source_score_medium",
        "precedent_score_high",
        "rule_change_status_stable",
        "resolution_window_normal",
        "checklist_review_required",
    )


def test_validation_requires_decimal_inputs_bounds_flags_and_frozen_outputs() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.checklist_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="official_source_score must be a Decimal"):
        checklist(official_source_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="precedent_score must be a Decimal"):
        checklist(precedent_score=_DecimalSubclass("0.800000"))

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be finite"):
        checklist(time_to_resolution_minutes=Decimal("NaN"))

    with pytest.raises(ValueError, match="official_source_score must be between 0 and 1"):
        checklist(official_source_score=d("1.000001"))

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        checklist(time_to_resolution_minutes=d("-1.000000"))

    with pytest.raises(ValueError, match="rule_change_status is not supported"):
        checklist(rule_change_status="speculative")

    with pytest.raises(ValueError, match="input must be paper_only"):
        checklist(paper_only=False)

    with pytest.raises(ValueError, match="result must be readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="reason_codes must match"):
        module.MarketResolutionSourceChecklistV10Result(
            market_id="market-001",
            category="politics",
            resolution_source_family="official",
            official_source_score=d("0.900000"),
            precedent_score=d("0.800000"),
            rule_change_status="stable",
            time_to_resolution_minutes=d("720.000000"),
            checklist_status="ready",
            required_checks=result.required_checks,
            missing_checks=(),
            reason_codes=("checklist_blocked",),
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.strategy_market_resolution_source_checklist_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_market_resolution_source_checklist_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "official_source_score": 0.5,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_market_resolution_source_checklist_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "time_to_resolution_minutes": 60,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_market_resolution_source_checklist_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "extra": "field"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_market_resolution_source_checklist_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_market_resolution_source_checklist_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "signing",
        "order placement",
        "submit",
        "cancel",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
