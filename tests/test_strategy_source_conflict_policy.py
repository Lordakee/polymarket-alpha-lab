from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_source_conflict_policy",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def judgment(
    source_id: str,
    value: str,
    *,
    source_role: str = "supporting",
    source_family: str = "news",
    observed_at: datetime | None = None,
    arbitration_id: str | None = None,
):
    policy = api()
    return policy.StrategySourceJudgment(
        strategy_id="strategy-alpha",
        market_id="market-123",
        source_family=source_family,
        source_id=source_id,
        source_role=source_role,
        judgment_value=value,
        observed_at=observed_at or (GENERATED_AT - timedelta(minutes=15)),
        arbitration_id=arbitration_id,
    )


def config(**overrides: object):
    policy = api()
    values = {
        "config_version": "strategy-source-conflict-policy-v0",
        "freshness_window_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return policy.StrategySourceConflictPolicyConfig(**values)


def decision(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    policy = api()
    return policy.evaluate_strategy_source_conflict_policy(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name.endswith("_score") or field.name.endswith("_seconds"):
            assert type(getattr(value, field.name)) is Decimal


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_aligned_sources_pass_with_zero_conflict_score() -> None:
    policy_decision = decision(
        judgment("official-a", "yes", source_role="official", source_family="official"),
        judgment("primary-a", "yes", source_role="primary", source_family="oracle"),
        judgment("supporting-a", "yes"),
    )

    assert is_dataclass(policy_decision)
    assert policy_decision.strategy_id == "strategy-alpha"
    assert policy_decision.market_id == "market-123"
    assert policy_decision.source_count == d("3")
    assert policy_decision.primary_source_count == d("1")
    assert policy_decision.official_source_count == d("1")
    assert policy_decision.fresh_source_count == d("3")
    assert policy_decision.stale_source_count == d("0")
    assert policy_decision.status == "pass"
    assert policy_decision.conflict_score == d("0.000000")
    assert policy_decision.reason_codes == ("source_conflict_policy_pass",)
    assert policy_decision.paper_only is True
    assert policy_decision.report_only is True
    assert policy_decision.readonly is True
    assert_decimal_public_numbers(policy_decision)


def test_primary_source_disagreement_without_arbitration_blocks() -> None:
    policy_decision = decision(
        judgment("primary-a", "yes", source_role="primary", source_family="oracle"),
        judgment("primary-b", "no", source_role="primary", source_family="model"),
    )

    assert policy_decision.status == "blocked"
    assert policy_decision.primary_source_disagreement is True
    assert policy_decision.stale_vs_fresh_conflict is False
    assert policy_decision.official_source_override is False
    assert policy_decision.missing_arbitration is True
    assert policy_decision.conflict_score == d("1.000000")
    assert policy_decision.reason_codes == (
        "primary_source_disagreement",
        "missing_arbitration",
        "source_conflict_policy_blocked",
    )


def test_fresh_official_override_of_stale_disagreement_is_watch() -> None:
    policy_decision = decision(
        judgment("official-a", "yes", source_role="official", source_family="official"),
        judgment(
            "stale-supporting-a",
            "no",
            source_family="archive",
            observed_at=GENERATED_AT - timedelta(hours=3),
        ),
    )

    assert policy_decision.status == "watch"
    assert policy_decision.primary_source_disagreement is False
    assert policy_decision.stale_vs_fresh_conflict is True
    assert policy_decision.official_source_override is True
    assert policy_decision.missing_arbitration is False
    assert policy_decision.fresh_source_count == d("1")
    assert policy_decision.stale_source_count == d("1")
    assert policy_decision.conflict_score == d("0.600000")
    assert policy_decision.reason_codes == (
        "stale_vs_fresh_conflict",
        "official_source_override",
        "source_conflict_policy_watch",
    )


def test_fresh_unofficial_disagreement_missing_arbitration_blocks() -> None:
    policy_decision = decision(
        judgment("supporting-a", "yes", source_family="news"),
        judgment("supporting-b", "no", source_family="research"),
    )

    assert policy_decision.status == "blocked"
    assert policy_decision.primary_source_disagreement is False
    assert policy_decision.stale_vs_fresh_conflict is False
    assert policy_decision.official_source_override is False
    assert policy_decision.missing_arbitration is True
    assert policy_decision.conflict_score == d("1.000000")
    assert policy_decision.reason_codes == (
        "missing_arbitration",
        "source_conflict_policy_blocked",
    )


def test_arbitration_id_downgrades_unofficial_disagreement_to_watch() -> None:
    policy_decision = decision(
        judgment("supporting-a", "yes", source_family="news", arbitration_id="arb-001"),
        judgment("supporting-b", "no", source_family="research", arbitration_id="arb-001"),
    )

    assert policy_decision.status == "watch"
    assert policy_decision.missing_arbitration is False
    assert policy_decision.conflict_score == d("0.400000")
    assert policy_decision.reason_codes == ("source_conflict_policy_watch",)


def test_payload_helper_is_json_ready_uses_decimal_strings_and_no_floats() -> None:
    policy = api()
    payload = policy.strategy_source_conflict_policy_payload(
        decision(
            judgment("official-a", "yes", source_role="official", source_family="official"),
            judgment(
                "stale-supporting-a",
                "no",
                source_family="archive",
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
    )

    assert_no_float_values(payload)
    assert json.dumps(payload, sort_keys=True)
    assert payload["source_count"] == "2"
    assert payload["conflict_score"] == "0.600000"
    assert payload["paper_only"] is True
    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "private_key",
        "seed_phrase",
        "signing",
        "investment_advice",
        "live_trading",
    ):
        assert forbidden not in payload_text


def test_non_utc_datetimes_are_normalized_before_freshness_checks() -> None:
    policy_decision = decision(
        judgment(
            "official-offset",
            "yes",
            source_role="official",
            source_family="official",
            observed_at=datetime(
                2026,
                7,
                6,
                12,
                30,
                tzinfo=timezone(timedelta(hours=1)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            6,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert policy_decision.generated_at == GENERATED_AT
    assert policy_decision.generated_at.tzinfo is UTC
    assert policy_decision.fresh_source_count == d("1")
    assert policy_decision.stale_source_count == d("0")
    assert policy_decision.status == "pass"


def test_validation_rejects_unsafe_shapes_and_non_decimal_config_values() -> None:
    policy = api()

    with pytest.raises(ValueError, match="freshness_window_seconds must be a Decimal"):
        config(freshness_window_seconds=3600)

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        judgment("naive-source", "yes", observed_at=datetime(2026, 7, 6, 11, 0))

    with pytest.raises(ValueError, match="source_role must be one of"):
        judgment("bad-role", "yes", source_role="trusted")

    with pytest.raises(ValueError, match="strategy_id must be a canonical nonblank string"):
        judgment("bad-strategy", "yes").__class__(
            strategy_id=" strategy-alpha",
            market_id="market-123",
            source_family="news",
            source_id="source-a",
            source_role="supporting",
            judgment_value="yes",
            observed_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        decision(
            judgment("duplicate-source", "yes"),
            judgment("duplicate-source", "no"),
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        decision(
            judgment("future-source", "yes", observed_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(
        ValueError,
        match="config must be a StrategySourceConflictPolicyConfig",
    ):
        policy.evaluate_strategy_source_conflict_policy(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_dataclasses_are_frozen_and_flags_are_hard_required() -> None:
    policy = api()
    row = judgment("frozen-source", "yes")

    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    policy_decision = decision(row)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(policy_decision, readonly=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        policy.StrategySourceConflictPolicyConfig(report_only=False)


def test_module_scope_has_no_file_network_live_trading_or_advice_surface_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_source_conflict_policy.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "http",
        "socket",
        "sqlite",
        "postgres",
        "mysql",
        "wallet",
        "broker",
        "private_key",
        "seed_phrase",
        "mnemonic",
        "signing",
        "place_trade",
        "submit_trade",
        "live_trading",
        "investment_advice",
        "open(",
        "subprocess",
        "argparse",
        "click.",
        "typer",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
