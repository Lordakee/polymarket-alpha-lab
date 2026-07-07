from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_specialist_signal_confidence_blender_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_specialist_signal_confidence_blender_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "yes",
        "signal_probability": d("0.720000"),
        "team_calibration_score": d("0.900000"),
        "source_quality_score": d("0.800000"),
        "evidence_age_seconds": d("3600.000000"),
        "conflict_severity_score": d("0.100000"),
        "liquidity_exit_risk_score": d("0.200000"),
        "resolution_rule_clarity_score": d("0.950000"),
        "reason_codes": ("specialist_signal_screened",),
    }
    values.update(overrides)
    return module.StrategySpecialistSignalConfidenceBlenderV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            signal(team_id="macro_team"),
            signal(
                team_id="legal_team",
                signal_probability=d("0.640000"),
                team_calibration_score=d("0.700000"),
                source_quality_score=d("0.600000"),
                evidence_age_seconds=d("43200.000000"),
                conflict_severity_score=d("0.350000"),
                liquidity_exit_risk_score=d("0.450000"),
                resolution_rule_clarity_score=d("0.650000"),
            ),
            signal(
                team_id="liquidity_team",
                signal_probability=d("0.300000"),
                team_calibration_score=d("0.350000"),
                source_quality_score=d("0.400000"),
                evidence_age_seconds=d("90000.000000"),
                conflict_severity_score=d("0.800000"),
                liquidity_exit_risk_score=d("0.900000"),
                resolution_rule_clarity_score=d("0.300000"),
            ),
        )
    return module.build_strategy_specialist_signal_confidence_blender_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_blends_specialist_signals_into_confidence_adjusted_report() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.config_version == "strategy-specialist-signal-confidence-blender-v2"
    assert report.market_slug == "fed-cuts-by-september"
    assert report.outcome_name == "yes"
    assert report.signal_count == d("3")
    assert report.pass_signal_count == d("1")
    assert report.watch_signal_count == d("1")
    assert report.blocked_signal_count == d("1")
    assert report.blended_signal_probability == d("0.633463")
    assert report.average_specialist_confidence_score == d("0.580000")
    assert report.confidence_adjusted_probability == d("0.367409")
    assert report.max_conflict_severity_score == d("0.800000")
    assert report.max_liquidity_exit_risk_score == d("0.900000")
    assert report.min_resolution_rule_clarity_score == d("0.300000")
    assert report.recommendation_status == "blocked"
    assert report.recommended_next_step == "block_report_only_signal_confidence_review"
    assert report.reason_codes == (
        "signal_confidence_blocked_rows_present",
        "signal_confidence_adjusted_probability_watch",
        "signal_confidence_high_conflict_present",
        "signal_confidence_exit_risk_present",
        "signal_confidence_resolution_unclear",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "macro_team",
        "legal_team",
        "liquidity_team",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.specialist_confidence_score for row in rows) == (
        d("0.893750"),
        d("0.602500"),
        d("0.243750"),
    )
    assert tuple(row.row_status for row in rows) == ("pass", "watch", "blocked")
    assert all(row.paper_only and row.report_only and row.readonly for row in rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_public_payload_uses_decimal_strings_flags_and_digest() -> None:
    module = api()
    report = build_report()

    payload = module.strategy_specialist_signal_confidence_blender_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["signal_count"] == "3"
    assert payload["blended_signal_probability"] == "0.633463"
    assert payload["confidence_adjusted_probability"] == "0.367409"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["specialist_confidence_score"] == "0.893750"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert_no_public_numeric_scalars(payload)

    assert module.strategy_specialist_signal_confidence_blender_v2_payload(payload) == payload


def test_empty_report_is_blocked_report_only_decimal_and_digest_backed() -> None:
    report = build_report(use_default_items=False)

    assert report.market_slug == "unassigned"
    assert report.outcome_name == "unassigned"
    assert report.signal_count == d("0")
    assert report.blended_signal_probability == d("0.000000")
    assert report.average_specialist_confidence_score == d("0.000000")
    assert report.confidence_adjusted_probability == d("0.000000")
    assert report.recommendation_status == "blocked"
    assert report.rows == ()
    assert report.reason_codes == ("signal_confidence_no_specialist_signals",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_reject_bad_scalars() -> None:
    module = api()
    config = module.StrategySpecialistSignalConfidenceBlenderV2Config()
    sample = signal()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "team_calibration_weight",
                "source_quality_weight",
                "evidence_freshness_weight",
                "conflict_severity_weight",
                "liquidity_exit_risk_weight",
                "resolution_rule_clarity_weight",
                "max_evidence_age_seconds",
                "pass_confidence_floor",
                "watch_confidence_floor",
                "min_confidence_adjusted_probability",
                "watch_confidence_adjusted_probability",
                "signal_probability",
                "team_calibration_score",
                "source_quality_score",
                "evidence_age_seconds",
                "conflict_severity_score",
                "liquidity_exit_risk_score",
                "resolution_rule_clarity_score",
                "rank",
                "evidence_freshness_score",
                "specialist_confidence_score",
                "confidence_weighted_signal",
                "signal_count",
                "pass_signal_count",
                "watch_signal_count",
                "blocked_signal_count",
                "blended_signal_probability",
                "average_specialist_confidence_score",
                "confidence_adjusted_probability",
                "max_conflict_severity_score",
                "max_liquidity_exit_risk_score",
                "min_resolution_rule_clarity_score",
            }:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="signal_probability must be exactly Decimal"):
        signal(signal_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="team_calibration_score must be <= 1.000000"):
        signal(team_calibration_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_quality_score must use six decimal places or fewer"):
        signal(source_quality_score=d("0.7000004"))
    with pytest.raises(ValueError, match="evidence_age_seconds must be >= 0.000000"):
        signal(evidence_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a non-empty tuple"):
        signal(reason_codes=["specialist_signal_screened"])


def test_config_validation_and_build_inputs_are_strict() -> None:
    module = api()

    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        module.StrategySpecialistSignalConfidenceBlenderV2Config(
            team_calibration_weight=d("0.260000"),
        )
    with pytest.raises(ValueError, match="watch_confidence_floor must not exceed pass_confidence_floor"):
        module.StrategySpecialistSignalConfidenceBlenderV2Config(
            watch_confidence_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategySpecialistSignalConfidenceBlenderV2Config(paper_only=False)
    with pytest.raises(ValueError, match="signals must be an iterable"):
        module.build_strategy_specialist_signal_confidence_blender_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="signal items must be"):
        module.build_strategy_specialist_signal_confidence_blender_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_specialist_signal_confidence_blender_v2(
            [signal()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="same market_slug and outcome_name"):
        build_report(
            signal(team_id="macro_team"),
            signal(team_id="legal_team", outcome_name="no"),
        )


def test_derived_validation_digest_rejects_report_and_public_payload_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, confidence_adjusted_probability=d("0.360000"))

    payload = module.strategy_specialist_signal_confidence_blender_v2_payload(report)
    tampered = dict(payload)
    tampered["confidence_adjusted_probability"] = "0.360000"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.strategy_specialist_signal_confidence_blender_v2_payload(tampered)

    missing = dict(payload)
    missing.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_specialist_signal_confidence_blender_v2_payload(missing)


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()
    payload = module.strategy_specialist_signal_confidence_blender_v2_payload(build_report())

    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_reference",
        "order_ticket",
        "network_client",
        "database_path",
        "persist_target",
        "signing_key",
        "mutation_plan",
        "buy_button",
        "sell_button",
        "trade_route",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_specialist_signal_confidence_blender_v2_payload(unsafe_payload)

    for unsafe_value in (
        "live mode configured",
        "auth token configured",
        "wallet path configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
        "signing key configured",
        "mutation enabled",
        "buy signal configured",
        "sell signal configured",
        "trade route configured",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            signal(team_id=unsafe_value)


def test_module_scope_is_phase1_report_only_and_has_no_live_surfaces() -> None:
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
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
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
