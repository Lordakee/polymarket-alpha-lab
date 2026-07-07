from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    module_name = (
        "polymarket_alpha_lab."
        "strategy_candidate_tail_risk_event_asymmetry_gate_v2"
    )
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_EVENT_ASYMMETRY_GATE_V2_CONFIG_VERSION
        ),
        "watch_component_score": d("0.350000"),
        "block_component_score": d("0.700000"),
        "watch_penalty_score": d("0.350000"),
        "block_penalty_score": d("0.700000"),
        "liquidity_exit_weight": d("0.250000"),
        "ambiguity_weight": d("0.200000"),
        "negative_catalyst_cluster_weight": d("0.250000"),
        "settlement_lag_weight": d("0.150000"),
        "source_disagreement_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.StrategyCandidateTailRiskEventAsymmetryGateConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate_alpha",
        "market_slug": "market_alpha",
        "observed_at": OBSERVED_AT,
        "base_candidate_score": d("0.800000"),
        "liquidity_exit_risk_score": d("0.100000"),
        "ambiguity_risk_score": d("0.120000"),
        "negative_catalyst_cluster_score": d("0.130000"),
        "settlement_lag_risk_score": d("0.140000"),
        "source_disagreement_score": d("0.150000"),
    }
    values.update(overrides)
    return module.StrategyCandidateTailRiskEventAsymmetryCandidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report(
        candidates,
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


def test_gate_penalizes_pass_watch_and_block_event_asymmetry() -> None:
    result = report(
        candidate(
            candidate_id="candidate_pass",
            market_slug="market_pass",
            liquidity_exit_risk_score=d("0.100000"),
            ambiguity_risk_score=d("0.120000"),
            negative_catalyst_cluster_score=d("0.130000"),
            settlement_lag_risk_score=d("0.140000"),
            source_disagreement_score=d("0.150000"),
        ),
        candidate(
            candidate_id="candidate_watch",
            market_slug="market_watch",
            base_candidate_score=d("0.900000"),
            liquidity_exit_risk_score=d("0.400000"),
            ambiguity_risk_score=d("0.360000"),
            negative_catalyst_cluster_score=d("0.200000"),
            settlement_lag_risk_score=d("0.200000"),
            source_disagreement_score=d("0.200000"),
        ),
        candidate(
            candidate_id="candidate_block",
            market_slug="market_block",
            liquidity_exit_risk_score=d("0.900000"),
            ambiguity_risk_score=d("0.800000"),
            negative_catalyst_cluster_score=d("0.750000"),
            settlement_lag_risk_score=d("0.720000"),
            source_disagreement_score=d("0.830000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "strategy-candidate-tail-risk-event-asymmetry-gate-v2"
    )
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.max_asymmetry_penalty_score == d("0.805000")
    assert result.min_adjusted_candidate_score == ZERO
    assert result.status == "block"
    assert result.reason_codes == (
        "low_liquidity_exit_block",
        "high_ambiguity_block",
        "negative_catalyst_cluster_block",
        "settlement_lag_block",
        "source_disagreement_block",
        "event_asymmetry_penalty_block",
        "low_liquidity_exit_watch",
        "high_ambiguity_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.gate_status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows
    assert blocked.asymmetry_penalty_score == d("0.805000")
    assert blocked.adjusted_candidate_score == ZERO
    assert blocked.reason_codes == (
        "low_liquidity_exit_block",
        "high_ambiguity_block",
        "negative_catalyst_cluster_block",
        "settlement_lag_block",
        "source_disagreement_block",
        "event_asymmetry_penalty_block",
    )
    assert watched.asymmetry_penalty_score == d("0.282000")
    assert watched.adjusted_candidate_score == d("0.618000")
    assert watched.reason_codes == (
        "low_liquidity_exit_watch",
        "high_ambiguity_watch",
    )
    assert passed.asymmetry_penalty_score == d("0.125000")
    assert passed.adjusted_candidate_score == d("0.675000")
    assert passed.reason_codes == ("tail_risk_event_asymmetry_gate_pass",)


def test_empty_report_is_pass_zeroed_decimal_and_readonly() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_asymmetry_penalty_score == ZERO
    assert result.min_adjusted_candidate_score == ZERO
    assert result.status == "pass"
    assert result.reason_codes == ("tail_risk_event_asymmetry_gate_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(candidate())
    for value in (result, *populated.rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_score")):
                assert type(item_value) is Decimal


def test_payload_serializes_decimals_as_strings_and_no_public_numbers() -> None:
    module = api()
    result = report(
        candidate(
            candidate_id="candidate_block",
            market_slug="market_block",
            liquidity_exit_risk_score=d("0.900000"),
            ambiguity_risk_score=d("0.800000"),
            negative_catalyst_cluster_score=d("0.750000"),
            settlement_lag_risk_score=d("0.720000"),
            source_disagreement_score=d("0.830000"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_candidate_tail_risk_event_asymmetry_gate_v2_payload(result)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_asymmetry_penalty_score"] == "0.805000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["asymmetry_penalty_score"] == "0.805000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)


def test_rejects_invalid_inputs_thresholds_datetimes_and_flags() -> None:
    module = api()
    valid_candidate = candidate()
    cfg = config()

    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report(
            "bad-candidates",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyCandidateTailRiskEventAsymmetryCandidate"):
        module.build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report(
            [valid_candidate],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report(
            [valid_candidate],
            config=cfg,
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        report(replace(valid_candidate, observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        report(valid_candidate, valid_candidate)
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_candidate, paper_only=False)
    with pytest.raises(ValueError, match="block_component_score"):
        config(block_component_score=d("0.300000"))
    with pytest.raises(ValueError, match="block_penalty_score"):
        config(block_penalty_score=d("0.300000"))
    with pytest.raises(ValueError, match="weight"):
        config(
            liquidity_exit_weight=d("0.000000"),
            ambiguity_weight=d("0.000000"),
            negative_catalyst_cluster_weight=d("0.000000"),
            settlement_lag_weight=d("0.000000"),
            source_disagreement_weight=d("0.000000"),
        )
    with pytest.raises(ValueError, match="report"):
        module.strategy_candidate_tail_risk_event_asymmetry_gate_v2_payload(object())


def test_dataclasses_are_frozen_exact_and_reject_float_int_or_subclass_values() -> None:
    module = api()
    row = report(candidate()).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.gate_status = "block"  # type: ignore[misc]

    for klass in (
        module.StrategyCandidateTailRiskEventAsymmetryGateConfig,
        module.StrategyCandidateTailRiskEventAsymmetryCandidate,
        module.StrategyCandidateTailRiskEventAsymmetryGateRow,
        module.StrategyCandidateTailRiskEventAsymmetryGateReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(TypeError):

        class BadCandidate(module.StrategyCandidateTailRiskEventAsymmetryCandidate):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        candidate(liquidity_exit_risk_score=0.5)
    with pytest.raises(ValueError, match="Decimal"):
        candidate(liquidity_exit_risk_score=1)
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(liquidity_exit_risk_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 6, 11, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report(candidate()), candidate_count=1)


def test_source_has_no_io_db_network_or_live_action_surface() -> None:
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
        "csv",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    assert not (set(imports) & banned_import_roots)

    lowered = source.lower()
    for term in (
        "auth",
        "wallet",
        "network",
        "database",
        "sqlite",
        "psycopg",
        "requests",
        "urllib",
        "web3",
        "ccxt",
    ):
        assert term not in lowered
