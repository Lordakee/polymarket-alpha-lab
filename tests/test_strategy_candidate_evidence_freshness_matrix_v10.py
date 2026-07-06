from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_evidence_freshness_matrix_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object):
    module = api()
    values = {
        "market_id": "market-alpha",
        "source_family": "official",
        "evidence_age_minutes": d("20.000000"),
        "source_reliability_score": d("0.900000"),
        "confirmation_role": "primary",
        "market_time_sensitivity": d("0.200000"),
        "time_to_resolution_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return module.StrategyCandidateEvidenceFreshnessMatrixV10Input(**values)


def matrix(*rows: object, cfg=None):
    module = api()
    return module.build_strategy_candidate_evidence_freshness_matrix_v10(
        rows,
        config=cfg if cfg is not None else module.StrategyCandidateEvidenceFreshnessMatrixV10Config(),
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


def test_matrix_classifies_fresh_watch_and_stale_evidence_rows() -> None:
    result = matrix(
        evidence(
            market_id="market-fresh",
            source_family="official",
            evidence_age_minutes=d("20.000000"),
            source_reliability_score=d("0.900000"),
            confirmation_role="primary",
            market_time_sensitivity=d("0.200000"),
            time_to_resolution_minutes=d("1440.000000"),
        ),
        evidence(
            market_id="market-watch",
            source_family="polling",
            evidence_age_minutes=d("45.000000"),
            source_reliability_score=d("0.800000"),
            confirmation_role="confirming",
            market_time_sensitivity=d("1.000000"),
            time_to_resolution_minutes=d("90.000000"),
        ),
        evidence(
            market_id="market-stale",
            source_family="social",
            evidence_age_minutes=d("200.000000"),
            source_reliability_score=d("0.450000"),
            confirmation_role="context",
            market_time_sensitivity=d("0.500000"),
            time_to_resolution_minutes=d("300.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.matrix_status == "stale"
    assert result.stale_source_families == ("social",)
    assert result.reason_codes == (
        "evidence_age_stale",
        "source_reliability_low",
        "confirmation_role_context",
        "time_sensitivity_high",
        "resolution_urgency_high",
        "evidence_age_watch",
        "source_reliability_high",
        "confirmation_role_confirming",
        "confirmation_role_primary",
        "row_status_stale",
        "row_status_watch",
        "row_status_fresh",
        "matrix_status_stale",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.row_status for row in result.freshness_rows) == (
        "stale",
        "watch",
        "fresh",
    )
    stale, watched, fresh = result.freshness_rows

    assert stale.market_id == "market-stale"
    assert stale.source_family == "social"
    assert stale.effective_fresh_limit_minutes == d("45.000000")
    assert stale.effective_stale_limit_minutes == d("135.000000")
    assert stale.freshness_score == d("0.000000")
    assert stale.reason_codes == (
        "evidence_age_stale",
        "source_reliability_low",
        "confirmation_role_context",
        "row_status_stale",
    )

    assert watched.market_id == "market-watch"
    assert watched.effective_fresh_limit_minutes == d("30.000000")
    assert watched.effective_stale_limit_minutes == d("90.000000")
    assert watched.freshness_score == d("0.400000")
    assert watched.reason_codes == (
        "time_sensitivity_high",
        "resolution_urgency_high",
        "evidence_age_watch",
        "source_reliability_high",
        "confirmation_role_confirming",
        "row_status_watch",
    )

    assert fresh.market_id == "market-fresh"
    assert fresh.freshness_score == d("0.800000")
    assert fresh.reason_codes == (
        "source_reliability_high",
        "confirmation_role_primary",
        "row_status_fresh",
    )

    payload = result.payload
    assert payload == api().strategy_candidate_evidence_freshness_matrix_v10_payload(result)
    assert payload["config_version"] == "strategy-candidate-evidence-freshness-matrix-v10"
    assert payload["matrix_status"] == "stale"
    assert payload["stale_source_families"] == ["social"]
    assert payload["freshness_rows"][0]["evidence_age_minutes"] == "200.000000"
    assert payload["freshness_rows"][0]["freshness_score"] == "0.000000"
    assert payload["freshness_rows"][1]["effective_fresh_limit_minutes"] == "30.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_matrix_watch_status_when_only_time_pressure_degrades_freshness() -> None:
    result = matrix(
        evidence(
            market_id="market-watch",
            source_family="news",
            evidence_age_minutes=d("35.000000"),
            source_reliability_score=d("0.760000"),
            confirmation_role="confirming",
            market_time_sensitivity=d("1.000000"),
            time_to_resolution_minutes=d("60.000000"),
        ),
    )

    assert result.matrix_status == "watch"
    assert result.stale_source_families == ()
    assert result.freshness_rows[0].row_status == "watch"
    assert result.freshness_rows[0].freshness_score == d("0.464444")
    assert result.reason_codes == (
        "time_sensitivity_high",
        "resolution_urgency_high",
        "evidence_age_watch",
        "source_reliability_high",
        "confirmation_role_confirming",
        "row_status_watch",
        "matrix_status_watch",
    )


def test_empty_matrix_is_stale_and_readonly() -> None:
    result = matrix()

    assert result.matrix_status == "stale"
    assert result.freshness_rows == ()
    assert result.stale_source_families == ()
    assert result.reason_codes == (
        "freshness_matrix_empty",
        "matrix_status_stale",
    )
    assert result.payload["freshness_rows"] == []


def test_validation_requires_decimal_inputs_exact_types_and_hard_flags() -> None:
    module = api()
    result = matrix(evidence())

    with pytest.raises(FrozenInstanceError):
        result.matrix_status = "fresh"  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_id must be a canonical nonblank string"):
        evidence(market_id=" market-alpha")
    with pytest.raises(ValueError, match="evidence_age_minutes must be a Decimal"):
        evidence(evidence_age_minutes=20)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        evidence(source_reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        evidence(source_reliability_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_age_minutes must be finite"):
        evidence(evidence_age_minutes=Decimal("NaN"))
    with pytest.raises(ValueError, match="market_time_sensitivity must be between 0 and 1"):
        evidence(market_time_sensitivity=d("1.000001"))
    with pytest.raises(ValueError, match="confirmation_role must be one of"):
        evidence(confirmation_role="rumor")
    with pytest.raises(ValueError, match="input must be paper_only"):
        evidence(paper_only=False)

    class InputSubclass(module.StrategyCandidateEvidenceFreshnessMatrixV10Input):
        pass

    with pytest.raises(ValueError, match="evidence rows must contain"):
        matrix(object())
    with pytest.raises(ValueError, match="evidence rows must contain"):
        matrix(InputSubclass(**evidence().__dict__))
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_candidate_evidence_freshness_matrix_v10(
            [evidence()],
            config=object(),
        )
    with pytest.raises(ValueError, match="result must be readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("matrix_status_fresh",))


def test_payload_rejects_non_results_and_preserves_decimal_strings() -> None:
    module = api()
    result = matrix(evidence())
    payload = module.strategy_candidate_evidence_freshness_matrix_v10_payload(result)

    assert payload["freshness_rows"][0]["source_reliability_score"] == "0.900000"
    assert payload["freshness_rows"][0]["time_to_resolution_minutes"] == "1440.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="result must be"):
        module.strategy_candidate_evidence_freshness_matrix_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_evidence_freshness_matrix_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
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
            assert type(node.value) is not int
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "int", "open", "print", "input"}
