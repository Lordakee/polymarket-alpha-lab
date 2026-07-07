from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_calibrated_recommendation_thresholds_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 15, 45, tzinfo=UTC)
CONFIG_VERSION = "strategy-calibrated-recommendation-thresholds-v2-test"
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_calibrated_recommendation_thresholds_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "base_block_edge_probability": d("0.000000"),
        "base_watch_edge_probability": d("0.020000"),
        "base_promote_edge_probability": d("0.040000"),
        "historical_calibration_gap_weight": d("0.020000"),
        "source_quality_gap_weight": d("0.020000"),
        "liquidity_exit_gap_weight": d("0.020000"),
        "resolution_risk_weight": d("0.020000"),
        "specialist_quorum_gap_weight": d("0.020000"),
        "min_historical_calibration_score": d("0.700000"),
        "min_source_quality_score": d("0.700000"),
        "max_cost_break_even_probability": d("0.060000"),
        "min_liquidity_exit_feasibility_score": d("0.600000"),
        "max_resolution_risk_score": d("0.400000"),
        "min_specialist_quorum_score": d("0.650000"),
        "max_observation_age_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.StrategyCalibratedRecommendationThresholdsV2Config(**values)


def candidate(candidate_id: str = "candidate-alpha", **overrides: object):
    module = api()
    values = {
        "candidate_id": candidate_id,
        "market_id": "market-alpha",
        "recommendation_side": "yes",
        "observed_at": OBSERVED_AT,
        "calibrated_edge_probability": d("0.100000"),
        "historical_calibration_score": d("0.900000"),
        "source_quality_score": d("0.850000"),
        "cost_break_even_probability": d("0.010000"),
        "liquidity_exit_feasibility_score": d("0.900000"),
        "resolution_risk_score": d("0.050000"),
        "specialist_quorum_score": d("0.900000"),
        "reason_codes": ("candidate_calibrated",),
    }
    values.update(overrides)
    return module.StrategyCalibratedRecommendationThresholdsV2Input(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_calibrated_recommendation_thresholds_v2_report(
        items,
        config=cfg or config(),
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


def payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_input,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def test_report_derives_promote_watch_and_block_thresholds_from_all_risk_inputs() -> None:
    report = build_report(
        candidate(
            "candidate-alpha",
            calibrated_edge_probability=d("0.100000"),
            historical_calibration_score=d("0.900000"),
            source_quality_score=d("0.850000"),
            cost_break_even_probability=d("0.010000"),
            liquidity_exit_feasibility_score=d("0.900000"),
            resolution_risk_score=d("0.050000"),
            specialist_quorum_score=d("0.900000"),
        ),
        candidate(
            "candidate-beta",
            market_id="market-beta",
            calibrated_edge_probability=d("0.045000"),
            historical_calibration_score=d("0.800000"),
            source_quality_score=d("0.750000"),
            cost_break_even_probability=d("0.015000"),
            liquidity_exit_feasibility_score=d("0.800000"),
            resolution_risk_score=d("0.100000"),
            specialist_quorum_score=d("0.750000"),
        ),
        candidate(
            "candidate-gamma",
            market_id="market-gamma",
            calibrated_edge_probability=d("0.030000"),
            historical_calibration_score=d("0.600000"),
            source_quality_score=d("0.650000"),
            cost_break_even_probability=d("0.080000"),
            liquidity_exit_feasibility_score=d("0.500000"),
            resolution_risk_score=d("0.500000"),
            specialist_quorum_score=d("0.500000"),
        ),
        generated_at=datetime(2026, 7, 6, 11, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == d("3.000000")
    assert report.promote_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.status == "block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-gamma",
        "candidate-beta",
        "candidate-alpha",
    )
    blocked, watched, promoted = report.rows
    assert promoted.recommendation_status == "promote"
    assert promoted.threshold_adjustment_probability == d("0.011000")
    assert promoted.derived_block_threshold_probability == d("0.011000")
    assert promoted.derived_watch_threshold_probability == d("0.031000")
    assert promoted.derived_promote_threshold_probability == d("0.051000")
    assert promoted.reason_codes == (
        "candidate_calibrated",
        "cost_break_even_applied",
        "historical_calibration_applied",
        "liquidity_exit_feasibility_applied",
        "promote_threshold_met",
        "resolution_risk_applied",
        "source_quality_applied",
        "specialist_quorum_applied",
    )

    assert watched.recommendation_status == "watch"
    assert watched.threshold_adjustment_probability == d("0.017000")
    assert watched.derived_watch_threshold_probability == d("0.037000")
    assert watched.derived_promote_threshold_probability == d("0.057000")
    assert "promote_threshold_gap" in watched.reason_codes

    assert blocked.recommendation_status == "block"
    assert blocked.derived_block_threshold_probability == d("0.098000")
    assert "cost_break_even_block" in blocked.reason_codes
    assert "resolution_risk_block" in blocked.reason_codes
    assert "specialist_quorum_gap" in blocked.reason_codes

    payload = api().strategy_calibrated_recommendation_thresholds_v2_payload(report)
    assert payload["candidate_count"] == "3.000000"
    assert payload["promote_count"] == "1.000000"
    assert payload["rows"][2]["derived_promote_threshold_probability"] == "0.051000"
    assert payload["rows"][2]["derived_validation_digest"] == promoted.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)


def test_empty_report_is_readonly_report_only_paper_only_and_decimal_zeroed() -> None:
    report = build_report()

    assert report.candidate_count == ZERO
    assert report.promote_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.status == "watch"
    assert report.reason_codes == ("empty_calibrated_recommendation_set",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    populated = build_report(candidate())
    for value in (report, populated, *populated.rows):
        for item in fields(value):
            if item.name in {
                "derived_validation_digest",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_score",
                    "_seconds",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_revalidates_digest_flags_and_rejects_unsafe_public_content() -> None:
    module = api()
    report = build_report(candidate(), candidate("candidate-beta", market_id="market-beta"))
    payload = module.strategy_calibrated_recommendation_thresholds_v2_payload(report)

    assert module.strategy_calibrated_recommendation_thresholds_v2_payload(payload) == payload

    tampered_count = {**payload, "candidate_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0]), dict(payload["rows"][1])]
    tampered_row["rows"][0]["derived_promote_threshold_probability"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(tampered_row)

    downgraded = {**payload, "paper_only": False}
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(downgraded)

    unsafe_key = {**payload, "wallet_reference": "paper"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(unsafe_key)

    unsafe_value = {**payload, "status": "live_mode"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(unsafe_value)

    decimal_drift = {**payload, "candidate_count": d("2.000000")}
    with pytest.raises(ValueError, match="Decimal string"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(decimal_drift)

    numeric_count = {**payload, "candidate_count": 2}
    numeric_count["derived_validation_digest"] = payload_digest(numeric_count)
    with pytest.raises(ValueError, match="Decimal string"):
        module.strategy_calibrated_recommendation_thresholds_v2_payload(numeric_count)


def test_frozen_dataclasses_decimal_only_canonical_inputs_and_public_safety() -> None:
    module = api()
    report = build_report(candidate())

    assert is_dataclass(module.StrategyCalibratedRecommendationThresholdsV2Config)
    assert is_dataclass(module.StrategyCalibratedRecommendationThresholdsV2Input)
    assert is_dataclass(module.StrategyCalibratedRecommendationThresholdsV2Row)
    assert is_dataclass(module.StrategyCalibratedRecommendationThresholdsV2Report)
    with pytest.raises(FrozenInstanceError):
        report.status = "promote"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].recommendation_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="calibrated_edge_probability"):
        candidate(calibrated_edge_probability=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_quality_score"):
        candidate(source_quality_score=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(candidate(), generated_at=datetime(2026, 7, 6, 16, 0))
    with pytest.raises(ValueError, match="unsafe"):
        candidate(candidate_id="wallet_candidate")
    with pytest.raises(ValueError, match="duplicate"):
        build_report(candidate(), candidate())
    with pytest.raises(ValueError, match="ordered"):
        candidate(reason_codes={"alpha_reason", "beta_reason"})
    with pytest.raises(ValueError, match="rows must contain"):
        module.StrategyCalibratedRecommendationThresholdsV2Report(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            candidate_count=d("1.000000"),
            row_count=d("1.000000"),
            promote_count=d("0.000000"),
            watch_count=d("1.000000"),
            block_count=d("0.000000"),
            status="watch",
            reason_codes=("empty_calibrated_recommendation_set",),
            rows=(object(),),  # type: ignore[arg-type]
        )


def test_reconstructing_with_stale_digest_rejects_tampered_derived_values() -> None:
    report = build_report(candidate())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report.rows[0],
            derived_promote_threshold_probability=d("0.500000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, promote_count=d("9.000000"))


def test_module_scope_has_no_live_state_io_auth_order_or_persistence_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
