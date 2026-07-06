from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_expected_value_consistency_gate_v2 import (
    DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION,
    StrategyExpectedValueConsistencyGateV2Config,
    StrategyExpectedValueConsistencyGateV2Input,
    StrategyExpectedValueConsistencyGateV2ReasonCodeCount,
    StrategyExpectedValueConsistencyGateV2Report,
    StrategyExpectedValueConsistencyGateV2Row,
    build_strategy_expected_value_consistency_gate_v2_report,
    strategy_expected_value_consistency_gate_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 17, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyExpectedValueConsistencyGateV2Config:
    values = {
        "config_version": DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION,
        "minimum_pass_net_expected_value": d("0.020000"),
        "minimum_watch_net_expected_value": d("0.000000"),
        "maximum_fee_adjusted_break_even_premium": d("0.050000"),
        "maximum_liquidity_exit_penalty": d("0.050000"),
        "maximum_resolution_risk_probability": d("0.100000"),
        "maximum_capital_lockup_penalty": d("0.030000"),
        "maximum_capital_lockup_days": d("45.000000"),
    }
    values.update(overrides)
    return StrategyExpectedValueConsistencyGateV2Config(**values)


def candidate(
    candidate_id: str = "candidate-alpha",
    *,
    market_slug: str = "macro-rate-cut-july",
    forecast_probability: Decimal = d("0.700000"),
    market_probability: Decimal = d("0.550000"),
    fee_adjusted_break_even_probability: Decimal = d("0.565000"),
    liquidity_exit_penalty: Decimal = d("0.010000"),
    resolution_risk_probability: Decimal = d("0.020000"),
    capital_lockup_penalty: Decimal = d("0.005000"),
    capital_lockup_days: Decimal = d("12.000000"),
    observed_at: datetime = OBSERVED_AT,
    source_config_version: str = "phase1-local-snapshot-v0",
    reason_codes: tuple[str, ...] = ("forecast_input_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyExpectedValueConsistencyGateV2Input:
    return StrategyExpectedValueConsistencyGateV2Input(
        candidate_id=candidate_id,
        market_slug=market_slug,
        forecast_probability=forecast_probability,
        market_probability=market_probability,
        fee_adjusted_break_even_probability=fee_adjusted_break_even_probability,
        liquidity_exit_penalty=liquidity_exit_penalty,
        resolution_risk_probability=resolution_risk_probability,
        capital_lockup_penalty=capital_lockup_penalty,
        capital_lockup_days=capital_lockup_days,
        observed_at=observed_at,
        source_config_version=source_config_version,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: StrategyExpectedValueConsistencyGateV2Input,
    cfg: StrategyExpectedValueConsistencyGateV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyExpectedValueConsistencyGateV2Report:
    return build_strategy_expected_value_consistency_gate_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def test_gate_scores_pass_watch_and_block_expected_value_postures() -> None:
    digest = report(
        candidate(
            "candidate-pass",
            market_slug="macro-rate-cut-july",
            forecast_probability=d("0.700000"),
            market_probability=d("0.550000"),
            fee_adjusted_break_even_probability=d("0.565000"),
            liquidity_exit_penalty=d("0.010000"),
            resolution_risk_probability=d("0.020000"),
            capital_lockup_penalty=d("0.005000"),
            capital_lockup_days=d("12.000000"),
            reason_codes=("model_edge_positive",),
        ),
        candidate(
            "candidate-watch",
            market_slug="policy-cpi-print",
            forecast_probability=d("0.739000"),
            market_probability=d("0.550000"),
            fee_adjusted_break_even_probability=d("0.565000"),
            liquidity_exit_penalty=d("0.045000"),
            resolution_risk_probability=d("0.085000"),
            capital_lockup_penalty=d("0.025000"),
            capital_lockup_days=d("40.000000"),
        ),
        candidate(
            "candidate-block",
            market_slug="sports-final-outcome",
            forecast_probability=d("0.590000"),
            market_probability=d("0.550000"),
            fee_adjusted_break_even_probability=d("0.565000"),
            liquidity_exit_penalty=d("0.070000"),
            resolution_risk_probability=d("0.120000"),
            capital_lockup_penalty=d("0.040000"),
            capital_lockup_days=d("60.000000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "strategy-expected-value-consistency-gate-v2"
    assert digest.candidate_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.min_net_expected_value_probability == d("-0.205000")
    assert digest.max_penalty_adjusted_break_even_probability == d("0.795000")
    assert digest.max_liquidity_exit_penalty == d("0.070000")
    assert digest.max_resolution_risk_probability == d("0.120000")
    assert digest.max_capital_lockup_days == d("60.000000")
    assert digest.status == "blocked"
    assert digest.recommended_next_step == "block_expected_value_posture"
    assert digest.reason_codes == (
        "ev_consistency_gate_blocked",
        "evc_net_expected_value_negative_blocked",
        "evc_liquidity_exit_penalty_high_blocked",
        "evc_resolution_risk_high_blocked",
        "evc_capital_lockup_days_high_blocked",
        "evc_capital_lockup_penalty_high_blocked",
        "evc_net_expected_value_thin_watch",
        "evc_liquidity_exit_penalty_elevated_watch",
        "evc_resolution_risk_elevated_watch",
        "evc_capital_lockup_elevated_watch",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.gate_status for row in digest.rows) == ("blocked", "watch", "pass")
    assert blocked.candidate_id == "candidate-block"
    assert blocked.raw_probability_edge == d("0.040000")
    assert blocked.total_penalty_probability == d("0.230000")
    assert blocked.penalty_adjusted_break_even_probability == d("0.795000")
    assert blocked.net_expected_value_probability == d("-0.205000")
    assert blocked.reason_codes == (
        "forecast_input_ready",
        "evc_net_expected_value_negative_blocked",
        "evc_liquidity_exit_penalty_high_blocked",
        "evc_resolution_risk_high_blocked",
        "evc_capital_lockup_days_high_blocked",
        "evc_capital_lockup_penalty_high_blocked",
    )
    assert watched.gate_status == "watch"
    assert watched.net_expected_value_probability == d("0.019000")
    assert watched.reason_codes == (
        "forecast_input_ready",
        "evc_net_expected_value_thin_watch",
        "evc_liquidity_exit_penalty_elevated_watch",
        "evc_resolution_risk_elevated_watch",
        "evc_capital_lockup_elevated_watch",
    )
    assert passed.gate_status == "pass"
    assert passed.reason_codes == ("model_edge_positive", "evc_consistency_clear")

    assert digest.reason_code_counts[:2] == (
        StrategyExpectedValueConsistencyGateV2ReasonCodeCount(
            reason_code="forecast_input_ready",
            count=d("2.000000"),
            candidate_ratio=d("0.666667"),
        ),
        StrategyExpectedValueConsistencyGateV2ReasonCodeCount(
            reason_code="evc_capital_lockup_days_high_blocked",
            count=d("1.000000"),
            candidate_ratio=d("0.333333"),
        ),
    )


def test_empty_gate_is_pass_with_decimal_counts_and_hard_flags() -> None:
    digest = report()

    assert digest.candidate_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.min_net_expected_value_probability == ZERO
    assert digest.max_penalty_adjusted_break_even_probability == ZERO
    assert digest.status == "pass"
    assert digest.recommended_next_step == "paper_monitor_only"
    assert digest.reason_codes == ("ev_consistency_gate_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()

    populated = report(candidate())
    for value in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_probability", "_penalty", "_days", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_serializes_decimals_as_strings_and_rejects_tamper() -> None:
    digest = report(
        candidate(
            observed_at=datetime(
                2026,
                7,
                6,
                9,
                45,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            6,
            10,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = strategy_expected_value_consistency_gate_v2_payload(digest)

    assert payload["generated_at"] == "2026-07-06T17:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["net_expected_value_probability"] == "0.100000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T16:45:00+00:00"
    assert payload["derived_validation_digest"] == digest.derived_validation_digest
    assert_no_public_numeric_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_expected_value_consistency_gate_v2_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest, pass_count=d("2.000000"))


def test_public_payload_rejects_unsafe_keys_values_flags_and_numbers() -> None:
    digest = report(candidate())
    payload = strategy_expected_value_consistency_gate_v2_payload(digest)

    for key in (
        "live_mode",
        "auth_header",
        "wallet_address",
        "order_id",
        "network_url",
        "database_table",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_instruction",
        "sell_instruction",
        "trade_route",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            strategy_expected_value_consistency_gate_v2_payload(unsafe)

    for value in ("live quote", "auth token", "wallet signer", "buy now", "sell now"):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            strategy_expected_value_consistency_gate_v2_payload(unsafe)

    numeric = dict(payload)
    numeric["candidate_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        strategy_expected_value_consistency_gate_v2_payload(numeric)

    decimal_numeric = dict(payload)
    decimal_numeric["candidate_count"] = d("1.000000")
    with pytest.raises(ValueError, match="numeric"):
        strategy_expected_value_consistency_gate_v2_payload(decimal_numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        strategy_expected_value_consistency_gate_v2_payload(downgraded)


def test_validation_rejects_non_decimal_values_duplicate_ids_and_bad_boundaries() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        candidate(forecast_probability=0.6)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        candidate(forecast_probability=_DecimalSubclass("0.600000"))

    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("aware"), generated_at=datetime(2026, 7, 6, 17, 0))

    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 6, 16, 45))

    with pytest.raises(ValueError, match="future"):
        report(candidate(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        report(candidate("duplicate"), candidate("duplicate"))

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)

    with pytest.raises(ValueError, match="subclass"):
        StrategyExpectedValueConsistencyGateV2Config.__new__(
            type(
                "ConfigSubclass",
                (StrategyExpectedValueConsistencyGateV2Config,),
                {},
            ),
        )

    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 6, 17, 0, tzinfo=UTC),
        )

    frozen = candidate()
    with pytest.raises(FrozenInstanceError):
        frozen.candidate_id = "changed"  # type: ignore[misc]


def test_report_constructors_reject_inconsistent_materialized_fields() -> None:
    digest = report(candidate())
    row = digest.rows[0]

    with pytest.raises(ValueError, match="net_expected_value_probability"):
        StrategyExpectedValueConsistencyGateV2Row(
            **{
                **row.__dict__,
                "net_expected_value_probability": d("0.010000"),
            },
        )

    with pytest.raises(ValueError, match="status"):
        StrategyExpectedValueConsistencyGateV2Report(
            **{
                **digest.__dict__,
                "status": "blocked",
            },
        )

    break_even_inconsistent = report(
        candidate(
            "break-even-below",
            market_probability=d("0.550000"),
            fee_adjusted_break_even_probability=d("0.540000"),
        ),
    )
    assert break_even_inconsistent.status == "blocked"
    assert "evc_break_even_below_market_blocked" in (
        break_even_inconsistent.rows[0].reason_codes
    )


def test_module_exposes_no_network_order_wallet_db_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_expected_value_consistency_gate_v2.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
