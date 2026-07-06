from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_cross_domain_signal_divergence_gate_v2"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_cross_domain_signal_divergence_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)
CONFIG_VERSION = "strategy-cross-domain-signal-divergence-gate-v2-test"


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "max_probability_spread": d("0.200000"),
        "max_expected_edge_spread": d("0.050000"),
        "min_consensus_lift": d("0.050000"),
        "min_domain_count": d("2"),
    }
    values.update(overrides)
    return module.StrategyCrossDomainSignalDivergenceGateV2Config(**values)


def signal(domain_id: str, **overrides: object) -> Any:
    module = api()
    values = {
        "condition_id": "condition-alpha",
        "domain_id": domain_id,
        "forecast_probability": d("0.600000"),
        "expected_edge": d("0.080000"),
        "confidence": d("0.500000"),
        "observed_at": OBSERVED_AT,
        "source_reference": "internal-research-reference",
    }
    values.update(overrides)
    return module.StrategyCrossDomainSignalDivergenceGateV2Signal(**values)


def report(*signals: object, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_cross_domain_signal_divergence_gate_v2(
        signals,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool or value is None or field.name.startswith("_"):
            continue
        assert type(value) is not int
        assert type(value) is not float
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_public_numeric_values(value: object) -> None:
    assert type(value) is not int
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def test_cross_domain_divergence_blocks_condition() -> None:
    result = report(
        signal(
            "forecast",
            forecast_probability=d("0.820000"),
            expected_edge=d("0.120000"),
            confidence=d("0.900000"),
            source_reference="postgres://secret.invalid/source",
        ),
        signal(
            "news",
            forecast_probability=d("0.510000"),
            expected_edge=d("0.030000"),
            confidence=d("0.400000"),
            source_reference="https://private.invalid/source-token",
        ),
    )

    assert result.gate_status == "blocked"
    assert result.condition_count == d("1")
    assert result.signal_count == d("2")
    assert result.blocked_count == d("1")
    assert result.watch_count == d("0")
    assert result.pass_count == d("0")
    assert result.consensus_lift_condition_count == d("0")
    assert result.consensus_lift_condition_ratio == d("0.000000")
    assert result.reason_codes == (
        "cross_domain_probability_divergence_high",
        "cross_domain_expected_edge_divergence_high",
    )

    row = result.rows[0]
    assert row.condition_id == "condition-alpha"
    assert row.row_status == "blocked"
    assert row.domain_count == d("2")
    assert row.minimum_forecast_probability == d("0.510000")
    assert row.maximum_forecast_probability == d("0.820000")
    assert row.average_forecast_probability == d("0.665000")
    assert row.cross_domain_probability_spread == d("0.310000")
    assert row.minimum_expected_edge == d("0.030000")
    assert row.maximum_expected_edge == d("0.120000")
    assert row.cross_domain_expected_edge_spread == d("0.090000")
    assert row.confidence_weighted_probability == d("0.724615")
    assert row.consensus_lift == d("0.059615")
    assert row.source_references == ("<redacted-source-reference>",)
    assert row.reason_codes == result.reason_codes
    assert row.derived_validation_digest.startswith("scdsdgv2-v0:")
    assert result.derived_validation_digest.startswith("scdsdgv2-v0:")
    assert "secret" not in repr(signal("leak-check", source_reference="secret-token"))
    assert "private.invalid" not in repr(row)


def test_consensus_lift_passes_aligned_cross_domain_condition() -> None:
    result = report(
        signal(
            "market",
            forecast_probability=d("0.520000"),
            expected_edge=d("0.070000"),
            confidence=d("0.200000"),
        ),
        signal(
            "research",
            forecast_probability=d("0.700000"),
            expected_edge=d("0.090000"),
            confidence=d("0.800000"),
        ),
    )

    assert result.gate_status == "pass"
    assert result.condition_count == d("1")
    assert result.pass_count == d("1")
    assert result.consensus_lift_condition_count == d("1")
    assert result.consensus_lift_condition_ratio == d("1.000000")
    assert result.reason_codes == ("cross_domain_consensus_lift_pass",)

    row = result.rows[0]
    assert row.row_status == "pass"
    assert row.average_forecast_probability == d("0.610000")
    assert row.confidence_weighted_probability == d("0.664000")
    assert row.consensus_lift == d("0.054000")
    assert row.divergence_score == d("0.200000")
    assert row.reason_codes == ("cross_domain_consensus_lift_pass",)


def test_payload_serializes_decimals_as_strings_and_rejects_unsafe_payloads() -> None:
    module = api()
    result = report(
        signal(
            "market",
            forecast_probability=d("0.520000"),
            confidence=d("0.200000"),
        ),
        signal(
            "research",
            forecast_probability=d("0.700000"),
            confidence=d("0.800000"),
        ),
    )

    payload = module.strategy_cross_domain_signal_divergence_gate_v2_payload(result)
    json.dumps(payload, sort_keys=True)

    assert payload["condition_count"] == "1"
    assert payload["rows"][0]["consensus_lift"] == "0.054000"
    assert payload["rows"][0]["derived_validation_digest"] == result.rows[
        0
    ].derived_validation_digest
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)

    for unsafe in (
        {"paper_only": True, "report_only": True, "readonly": True, "wallet_key": "safe"},
        {"paper_only": True, "report_only": True, "readonly": True, "safe": "live order"},
        {"paper_only": True, "report_only": True, "readonly": True, "safe": "database persist"},
        {"paper_only": True, "report_only": True, "readonly": True, "safe": "buy sell trade"},
        {"paper_only": True, "report_only": True, "readonly": True, "safe": "auth signing mutation"},
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            module.strategy_cross_domain_signal_divergence_gate_v2_payload(unsafe)


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    module = api()
    cfg = config()
    item = signal("market")
    result = report(item, signal("research", forecast_probability=d("0.620000")))

    for instance in (cfg, item, result, result.rows[0]):
        assert is_dataclass(instance)
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        assert_public_numeric_fields_are_decimal(instance)
        with pytest.raises(FrozenInstanceError):
            instance.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal("unsafe-report", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.StrategyCrossDomainSignalDivergenceGateV2Report(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            condition_count=d("0"),
            signal_count=d("0"),
            pass_count=d("0"),
            watch_count=d("0"),
            blocked_count=d("0"),
            consensus_lift_condition_count=d("0"),
            consensus_lift_condition_ratio=None,
            gate_status="watch",
            reason_codes=("strategy_cross_domain_signal_divergence_gate_v2_empty",),
            rows=(),
            readonly=False,
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    module = api()
    result = report(
        signal(
            "market",
            forecast_probability=d("0.520000"),
            confidence=d("0.200000"),
        ),
        signal(
            "research",
            forecast_probability=d("0.700000"),
            confidence=d("0.800000"),
        ),
    )

    tampered_row = replace(
        result.rows[0],
        consensus_lift=d("0.000000"),
    )
    object.__setattr__(tampered_row, "derived_validation_digest", result.rows[0].derived_validation_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCrossDomainSignalDivergenceGateV2Report(
            generated_at=result.generated_at,
            config_version=result.config_version,
            condition_count=result.condition_count,
            signal_count=result.signal_count,
            pass_count=result.pass_count,
            watch_count=result.watch_count,
            blocked_count=result.blocked_count,
            consensus_lift_condition_count=result.consensus_lift_condition_count,
            consensus_lift_condition_ratio=result.consensus_lift_condition_ratio,
            gate_status=result.gate_status,
            reason_codes=result.reason_codes,
            rows=(tampered_row,),
        )

    object.__setattr__(result, "derived_validation_digest", "scdsdgv2-v0:" + "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_cross_domain_signal_divergence_gate_v2_payload(result)


def test_no_unsafe_surface_imports_or_public_names() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert not imported_roots & {
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "web3",
    }

    public_names = tuple(module.__all__)
    lowered_public_names = " ".join(public_names).lower()
    for unsafe_fragment in (
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
        assert unsafe_fragment not in lowered_public_names
