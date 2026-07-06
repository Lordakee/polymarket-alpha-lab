from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    module_name = "polymarket_alpha_lab.strategy_candidate_scenario_balance_score_v2"
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_SCENARIO_BALANCE_SCORE_V2_CONFIG_VERSION
        ),
        "watch_score_threshold": d("0.400000"),
        "pass_score_threshold": d("0.700000"),
        "missing_scenario_penalty": d("0.150000"),
        "one_sided_share_threshold": d("0.800000"),
        "one_sided_penalty_scale": d("0.500000"),
        "balanced_source_boost": d("0.050000"),
        "min_balanced_source_kind_count": d("2"),
    }
    values.update(overrides)
    return module.StrategyCandidateScenarioBalanceScoreV2Config(**values)


def evidence(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-balanced",
        "scenario": "base",
        "source_reference": "source-alpha",
        "source_kind": "research",
        "evidence_weight": d("1.000000"),
        "confidence_score": d("1.000000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("candidate_evidence",),
    }
    values.update(overrides)
    return module.StrategyCandidateScenarioBalanceScoreV2Evidence(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_scenario_balance_score_v2(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_scores_bull_base_bear_scenario_balance() -> None:
    result = report(
        evidence(
            candidate_reference="candidate-balanced",
            scenario="bull",
            source_reference="source-balanced-bull",
            source_kind="research",
        ),
        evidence(
            candidate_reference="candidate-balanced",
            scenario="base",
            source_reference="source-balanced-base",
            source_kind="model",
        ),
        evidence(
            candidate_reference="candidate-balanced",
            scenario="bear",
            source_reference="source-balanced-bear",
            source_kind="survey",
        ),
        evidence(
            candidate_reference="candidate-two-sided",
            scenario="bull",
            source_reference="source-two-sided-bull",
            source_kind="research",
        ),
        evidence(
            candidate_reference="candidate-two-sided",
            scenario="base",
            source_reference="source-two-sided-base",
            source_kind="model",
        ),
        evidence(
            candidate_reference="candidate-one-sided",
            scenario="bull",
            source_reference="source-one-sided-bull",
            source_kind="research",
        ),
    )

    rows = {row.candidate_reference: row for row in result.rows}
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.block_count == d("2")
    assert result.status == "block"

    balanced = rows["candidate-balanced"]
    assert balanced.bull_scenario_share == d("0.333333")
    assert balanced.base_scenario_share == d("0.333333")
    assert balanced.bear_scenario_share == d("0.333333")
    assert balanced.scenario_imbalance_gap == d("0.000000")
    assert balanced.one_sided_evidence_penalty == d("0.000000")
    assert balanced.balanced_source_boost == d("0.050000")
    assert balanced.scenario_balance_score == d("1.000000")
    assert balanced.status == "pass"
    assert balanced.reason_codes == (
        "scenario_balance_pass",
        "bull_base_bear_evidence_present",
        "balanced_source_boost",
    )

    two_sided = rows["candidate-two-sided"]
    assert two_sided.bull_scenario_share == d("0.500000")
    assert two_sided.base_scenario_share == d("0.500000")
    assert two_sided.bear_scenario_share == d("0.000000")
    assert two_sided.scenario_imbalance_gap == d("0.500000")
    assert two_sided.one_sided_evidence_penalty == d("0.150000")
    assert two_sided.scenario_balance_score == d("0.350000")
    assert two_sided.status == "block"
    assert "missing_bear_scenario" in two_sided.reason_codes

    one_sided = rows["candidate-one-sided"]
    assert one_sided.bull_scenario_share == d("1.000000")
    assert one_sided.base_scenario_share == d("0.000000")
    assert one_sided.bear_scenario_share == d("0.000000")
    assert one_sided.scenario_imbalance_gap == d("1.000000")
    assert one_sided.one_sided_evidence_penalty == d("0.400000")
    assert one_sided.scenario_balance_score == d("0.000000")
    assert one_sided.status == "block"
    assert "missing_base_scenario" in one_sided.reason_codes
    assert "missing_bear_scenario" in one_sided.reason_codes
    assert "one_sided_evidence_penalty" in one_sided.reason_codes


def test_one_sided_penalties_and_balanced_source_boost_are_configurable() -> None:
    cfg = config(
        missing_scenario_penalty=d("0.050000"),
        one_sided_share_threshold=d("0.900000"),
        one_sided_penalty_scale=d("0.100000"),
        balanced_source_boost=d("0.000000"),
    )
    result = report(
        evidence(
            candidate_reference="candidate-one-sided",
            scenario="bear",
            source_reference="source-one-sided-bear",
        ),
        cfg=cfg,
    )

    row = result.rows[0]
    assert row.bear_scenario_share == d("1.000000")
    assert row.one_sided_evidence_penalty == d("0.110000")
    assert row.balanced_source_boost == d("0.000000")
    assert row.scenario_balance_score == d("0.000000")


def test_payload_serializes_decimal_values_as_strings_and_hard_flags() -> None:
    module = api()
    result = report(
        evidence(scenario="bull", source_kind="research", source_reference="src-bull"),
        evidence(scenario="base", source_kind="model", source_reference="src-base"),
        evidence(scenario="bear", source_kind="survey", source_reference="src-bear"),
    )

    payload = module.strategy_candidate_scenario_balance_score_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["average_scenario_balance_score"] == "1.000000"
    assert payload["rows"][0]["bull_scenario_share"] == "0.333333"
    assert payload["rows"][0]["balanced_source_boost"] == "0.050000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert rendered.count("1.000000") >= 1
    assert_no_int_or_float_values(payload)


def test_dataclasses_are_frozen_and_public_numeric_values_are_exact_decimals() -> None:
    module = api()
    result = report(evidence())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "pass"  # type: ignore[misc]

    for klass in (
        module.StrategyCandidateScenarioBalanceScoreV2Config,
        module.StrategyCandidateScenarioBalanceScoreV2Evidence,
        module.StrategyCandidateScenarioBalanceScoreV2Row,
        module.StrategyCandidateScenarioBalanceScoreV2Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for item in fields(row):
        item_value = getattr(row, item.name)
        if item.name.endswith(("_count", "_weight", "_share", "_gap", "_penalty", "_boost", "_score")):
            assert type(item_value) is Decimal
    for item in fields(result):
        item_value = getattr(result, item.name)
        if item.name.endswith(("_count", "_score", "_gap")):
            assert type(item_value) is Decimal

    with pytest.raises(ValueError, match="Decimal"):
        evidence(evidence_weight=1)
    with pytest.raises(ValueError, match="Decimal"):
        evidence(confidence_score=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        evidence(confidence_score=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="datetime"):
        evidence(observed_at=_DatetimeSubclass(2026, 7, 6, 11, 30, tzinfo=UTC))


def test_hard_flags_digest_tampering_and_unsafe_payloads_are_rejected() -> None:
    module = api()
    item = evidence()
    result = report(item)
    row = result.rows[0]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, scenario_balance_score=d("0.500000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, average_scenario_balance_score=d("0.500000"))

    with pytest.raises(ValueError, match="public payload"):
        evidence(candidate_reference="candidate-wallet")
    with pytest.raises(ValueError, match="public payload"):
        module.validate_strategy_candidate_scenario_balance_score_v2_public_payload(
            {"wallet_key": "safe-value"},
        )
    with pytest.raises(ValueError, match="public payload"):
        module.validate_strategy_candidate_scenario_balance_score_v2_public_payload(
            {"safe_key": "sell-pressure"},
        )


def test_rejects_invalid_inputs_and_empty_report_is_readonly() -> None:
    module = api()
    cfg = config()

    empty = report()
    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.average_scenario_balance_score == d("0.000000")
    assert empty.status == "pass"
    assert empty.reason_codes == ("scenario_balance_report_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    with pytest.raises(ValueError, match="items"):
        module.build_strategy_candidate_scenario_balance_score_v2(
            "bad-items",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyCandidateScenarioBalanceScoreV2Evidence"):
        module.build_strategy_candidate_scenario_balance_score_v2(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_scenario_balance_score_v2(
            [evidence()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="scenario"):
        evidence(scenario="middle")
    with pytest.raises(ValueError, match="pass_score_threshold"):
        config(watch_score_threshold=d("0.800000"), pass_score_threshold=d("0.700000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(evidence(), generated_at=datetime(2026, 7, 6, 12, 0))


def test_source_has_no_unsafe_runtime_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    banned_import_roots = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imports) & banned_import_roots)

    lowered = source.lower()
    for term in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert term not in lowered
