from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_bonds_signal_memory_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_bonds_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "bonds-signal-memory-quality-test",
        "stale_auction_after_seconds": d("604800.000000"),
        "stale_curve_after_seconds": d("172800.000000"),
        "stale_duration_after_seconds": d("1209600.000000"),
        "stale_issuance_after_seconds": d("604800.000000"),
        "stale_policy_after_seconds": d("604800.000000"),
        "conflict_block_threshold_count": d("1"),
        "stale_memory_penalty": d("0.250000"),
        "conflict_penalty": d("0.400000"),
        "min_pass_quality_score": d("0.700000"),
        "min_watch_quality_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchDomainBondsSignalMemoryQualityConfig(**values)


def memory(**overrides: object):
    module = api()
    values = {
        "memory_ref": "bonds-memory-auction-ready",
        "team_ref": "rates-research-team",
        "handoff_ref": "rates-event-handoff-a",
        "input_family": "auction",
        "memory_present": True,
        "observed_at": GENERATED_AT - timedelta(hours=12),
        "evidence_count": d("3"),
        "conflicting_evidence_count": d("0"),
        "confidence_score": d("0.820000"),
    }
    values.update(overrides)
    return module.ResearchDomainBondsSignalMemoryInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_bonds_signal_memory_quality_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_payload_has_no_forbidden_public_surface(value: object) -> None:
    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "http",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "network",
        "database",
        "position",
        "sizing",
        "recommend",
        "buy",
        "sell",
        "live",
    )
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            assert_payload_has_no_forbidden_public_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_forbidden_public_surface(item)


def test_bonds_memory_quality_identifies_stale_conflicting_and_missing_inputs() -> None:
    report = build_report(
        memory(memory_ref="bonds-memory-auction-ready", input_family="auction"),
        memory(
            memory_ref="bonds-memory-curve-stale",
            input_family="curve",
            observed_at=GENERATED_AT - timedelta(days=4),
            confidence_score=d("0.760000"),
        ),
        memory(
            memory_ref="bonds-memory-duration-conflict",
            input_family="duration",
            evidence_count=d("2"),
            conflicting_evidence_count=d("1"),
            confidence_score=d("0.880000"),
        ),
        memory(
            memory_ref="bonds-memory-issuance-missing",
            input_family="issuance",
            memory_present=False,
            observed_at=None,
            evidence_count=d("0"),
            confidence_score=d("0.000000"),
        ),
        memory(
            memory_ref="bonds-memory-policy-stale",
            input_family="policy",
            observed_at=GENERATED_AT - timedelta(days=10),
            confidence_score=d("0.700000"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("5")
    assert report.row_count == d("5")
    assert report.pass_count == d("1")
    assert report.watch_count == d("2")
    assert report.block_count == d("2")
    assert report.stale_count == d("2")
    assert report.conflict_count == d("1")
    assert report.missing_count == d("1")
    assert report.average_quality_score == d("0.532000")
    assert tuple(row.row_status for row in report.rows) == (
        "block",
        "block",
        "watch",
        "watch",
        "pass",
    )
    assert tuple(row.input_family for row in report.rows) == (
        "duration",
        "issuance",
        "curve",
        "policy",
        "auction",
    )
    assert report.reason_codes == (
        "missing_memory_present",
        "stale_memory_present",
        "conflicting_memory_present",
    )


def test_empty_report_watches_before_forecast_handoff() -> None:
    report = build_report()

    assert report.status == "watch"
    assert report.input_count == d("0")
    assert report.row_count == d("0")
    assert report.average_quality_score == d("0.000000")
    assert report.reason_codes == ("no_bonds_memory_inputs_supplied",)


def test_payload_serializes_decimal_strings_and_validates_sha256_digest() -> None:
    module = api()
    report = build_report(memory())

    payload = module.research_domain_bonds_signal_memory_quality_report_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1"
    assert payload["average_quality_score"] == "0.820000"
    assert payload["rows"][0]["quality_score"] == "0.820000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)
    assert_payload_has_no_forbidden_public_surface(payload)

    payload_again = module.research_domain_bonds_signal_memory_quality_report_payload(
        report,
    )
    assert payload_again == payload

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_bonds_signal_memory_quality_report_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_memory = memory()
    sample_report = build_report(sample_memory)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_memory, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(memory(readonly=False))


def test_report_rejects_derived_validation_digest_tampering() -> None:
    module = api()
    report = build_report(memory())
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["derived_validation_digest"] = "f" * 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchDomainBondsSignalMemoryQualityReport(**values)


@pytest.mark.parametrize(
    "payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "market_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "candidate_ref": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "question": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "url": "https://x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy signal"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "live trade"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ),
)
def test_unsafe_public_payload_keys_values_and_flag_downgrades_rejected(
    payload: dict[str, object],
) -> None:
    module = api()

    with pytest.raises(ValueError):
        module.research_domain_bonds_signal_memory_quality_report_payload(payload)


def test_input_validation_rejects_raw_identifiers_and_invalid_status_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        memory(handoff_ref="market-ref-raw")
    with pytest.raises(ValueError, match="unsafe public value"):
        memory(memory_ref="live-rate-memory")
    with pytest.raises(ValueError, match="input_family"):
        memory(input_family="weather")
    with pytest.raises(ValueError, match="observed_at"):
        memory(memory_present=True, observed_at=None)
    with pytest.raises(ValueError, match="observed_at"):
        build_report(memory(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="row_status"):
        module.ResearchDomainBondsSignalMemoryQualityRow(
            memory_ref="bonds-memory-row",
            team_ref="rates-research-team",
            handoff_ref="rates-event-handoff-a",
            input_family="auction",
            row_status="blocked",
            memory_present=True,
            memory_age_seconds=d("1.000000"),
            freshness_limit_seconds=d("604800.000000"),
            evidence_count=d("1"),
            conflicting_evidence_count=d("0"),
            confidence_score=d("0.800000"),
            stale_memory_penalty=d("0.000000"),
            conflict_penalty=d("0.000000"),
            quality_score=d("0.800000"),
            reason_codes=("memory_ready",),
        )


def test_module_scope_has_no_db_network_wallet_order_trading_or_sizing_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
