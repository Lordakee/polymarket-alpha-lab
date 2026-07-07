from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_source_family_rotation_need_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_source_family_rotation_need_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-source-family-rotation-need-v2-test",
        "max_source_family_share": d("0.500000"),
        "stale_evidence_after_seconds": d("604800.000000"),
        "max_source_latency_seconds": d("600.000000"),
        "medium_rotation_need_score": d("0.333333"),
        "high_rotation_need_score": d("0.666667"),
    }
    values.update(overrides)
    return module.TeamSpecialistSourceFamilyRotationNeedV2Config(**values)


def evidence(**overrides: object):
    module = api()
    values = {
        "evidence_id": "evidence-official-current",
        "team_id": "macro_rates",
        "category_id": "finance.macro.rates",
        "specialist_id": "rates-research-specialist",
        "source_family": "official",
        "source_domain": "finance.macro.rates",
        "expected_domain": "finance.macro.rates",
        "observed_at": GENERATED_AT - timedelta(hours=2),
        "evidence_updated_at": GENERATED_AT - timedelta(hours=2),
        "recent_miss_count": d("0"),
        "source_latency_seconds": d("120.000000"),
        "contradiction_count": d("0"),
        "contradiction_resolved_count": d("0"),
    }
    values.update(overrides)
    return module.TeamSpecialistSourceFamilyRotationNeedV2Evidence(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_source_family_rotation_need_v2(
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


def test_high_rotation_need_prioritizes_all_source_family_risk_signals() -> None:
    report = build_report(
        evidence(
            evidence_id="evidence-social-critical",
            source_family="social",
            source_domain="politics.social",
            evidence_updated_at=GENERATED_AT - timedelta(days=12),
            recent_miss_count=d("2"),
            source_latency_seconds=d("900.000000"),
            contradiction_count=d("3"),
            contradiction_resolved_count=d("1"),
        ),
        evidence(
            evidence_id="evidence-social-late",
            source_family="social",
            evidence_updated_at=GENERATED_AT - timedelta(days=9),
            recent_miss_count=d("1"),
            source_latency_seconds=d("720.000000"),
        ),
        evidence(
            evidence_id="evidence-social-stale",
            source_family="social",
            evidence_updated_at=GENERATED_AT - timedelta(days=8),
        ),
        evidence(
            evidence_id="evidence-official-fresh",
            source_family="official",
            evidence_updated_at=GENERATED_AT - timedelta(hours=4),
        ),
    )

    assert report.rotation_priority == "high"
    assert report.recommendation == "rotate_now"
    assert report.source_count == d("4")
    assert report.source_family_count == d("2")
    assert report.dominant_source_family == "social"
    assert report.dominant_source_family_share == d("0.750000")
    assert report.recent_miss_count == d("3")
    assert report.stale_evidence_count == d("3")
    assert report.domain_mismatch_count == d("1")
    assert report.latency_breach_count == d("2")
    assert report.unresolved_contradiction_count == d("2")
    assert report.rotation_need_score == d("1.000000")
    assert report.reason_codes == (
        "source_family_concentrated",
        "recent_misses_present",
        "stale_evidence_present",
        "domain_mismatch_present",
        "source_latency_breached",
        "unresolved_contradiction_history",
    )
    assert tuple(row.evidence_id for row in report.rows) == (
        "evidence-social-critical",
        "evidence-social-late",
        "evidence-social-stale",
        "evidence-official-fresh",
    )

    first = report.rows[0]
    assert first.row_priority == "high"
    assert first.family_source_share == d("0.750000")
    assert first.evidence_age_seconds == d("1036800.000000")
    assert first.unresolved_contradiction_count == d("2")
    assert first.rotation_need_score == d("1.000000")
    assert first.reason_codes == (
        "source_family_concentrated",
        "recent_misses_present",
        "stale_evidence_present",
        "domain_mismatch_present",
        "source_latency_breached",
        "unresolved_contradiction_history",
    )


def test_healthy_diverse_current_sources_do_not_recommend_rotation() -> None:
    report = build_report(
        evidence(evidence_id="evidence-official", source_family="official"),
        evidence(evidence_id="evidence-academic", source_family="academic"),
        evidence(evidence_id="evidence-market", source_family="market"),
    )

    assert report.rotation_priority == "low"
    assert report.recommendation == "keep_source_family_mix"
    assert report.source_count == d("3")
    assert report.dominant_source_family_share == d("0.333333")
    assert report.rotation_need_score == d("0.000000")
    assert report.reason_codes == ("source_family_rotation_not_needed",)
    assert all(row.row_priority == "low" for row in report.rows)
    assert all(row.reason_codes == ("source_family_fit_current",) for row in report.rows)


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(evidence())

    payload = module.team_specialist_source_family_rotation_need_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_count"] == "1"
    assert payload["rotation_need_score"] == "1.000000"
    assert payload["rows"][0]["source_latency_seconds"] == "120.000000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)

    tampered = dict(payload)
    tampered["rotation_priority"] = "low"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_source_family_rotation_need_v2_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_evidence = evidence()
    sample_report = build_report(sample_evidence)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_evidence, sample_row, sample_report):
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
        evidence(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(evidence(readonly=False))


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: config(max_source_family_share=d("1.500000")),
            "max_source_family_share must be at most 1",
        ),
        (
            lambda: config(high_rotation_need_score=d("0.250000")),
            "medium_rotation_need_score must not exceed high_rotation_need_score",
        ),
        (
            lambda: evidence(recent_miss_count=1),
            "recent_miss_count must be a Decimal",
        ),
        (
            lambda: evidence(source_latency_seconds=d("-1.000000")),
            "source_latency_seconds must be nonnegative",
        ),
        (
            lambda: evidence(
                contradiction_count=d("1"),
                contradiction_resolved_count=d("2"),
            ),
            "contradiction_resolved_count must not exceed contradiction_count",
        ),
        (
            lambda: build_report(evidence(), cfg=object()),
            "config must be a TeamSpecialistSourceFamilyRotationNeedV2Config",
        ),
        (
            lambda: build_report(object()),
            "evidence rows must contain TeamSpecialistSourceFamilyRotationNeedV2Evidence",
        ),
        (
            lambda: build_report(evidence(), generated_at=datetime(2026, 7, 7, 12, 0)),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_validation_rejects_invalid_inputs(factory, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


@pytest.mark.parametrize(
    "payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "wallet_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy signal"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "live trade"},
        {"paper_only": True, "report_only": True, "readonly": True, "network": "mainnet"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ),
)
def test_unsafe_public_payload_keys_values_and_flag_downgrades_rejected(
    payload: dict[str, object],
) -> None:
    module = api()

    with pytest.raises(ValueError):
        module.team_specialist_source_family_rotation_need_v2_payload(payload)


def test_public_string_values_reject_unsafe_live_surface_terms() -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        evidence(evidence_id="live-family-evidence")
    with pytest.raises(ValueError, match="unsafe public value"):
        evidence(source_family="order-book")


def test_module_scope_has_no_network_auth_wallet_order_db_or_trading_surface() -> None:
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
