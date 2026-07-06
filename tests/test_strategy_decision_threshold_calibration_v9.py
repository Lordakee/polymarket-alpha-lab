from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_decision_threshold_calibration_v9.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_decision_threshold_calibration_v9",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-decision-threshold-calibration-v9",
        "base_recommended_threshold": d("0.040000"),
        "minimum_recommended_threshold": d("0.020000"),
        "maximum_recommended_threshold": d("0.200000"),
        "elevated_threshold": d("0.100000"),
        "blocked_threshold": d("0.160000"),
        "calibration_gap_weight": d("0.060000"),
        "source_quality_gap_weight": d("0.050000"),
        "cost_drag_weight": d("0.250000"),
        "resolution_risk_weight": d("0.060000"),
        "team_confidence_gap_weight": d("0.040000"),
        "weak_paper_calibration": d("0.650000"),
        "low_source_quality": d("0.550000"),
        "high_cost_drag": d("0.100000"),
        "high_resolution_risk": d("0.650000"),
        "low_team_confidence": d("0.550000"),
    }
    values.update(overrides)
    return module.StrategyDecisionThresholdCalibrationV9Config(**values)


def calibration_input(**overrides: object):
    module = api()
    values = {
        "historical_paper_calibration": d("0.900000"),
        "source_quality": d("0.950000"),
        "cost_drag": d("0.010000"),
        "resolution_risk": d("0.100000"),
        "team_confidence": d("0.900000"),
    }
    values.update(overrides)
    return module.StrategyDecisionThresholdCalibrationV9Input(**values)


def report(input_value=None, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_decision_threshold_calibration_v9_report(
        input_value if input_value is not None else calibration_input(),
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


def test_threshold_calibration_v9_blocks_on_poor_history_quality_and_risk() -> None:
    result = report(
        calibration_input(
            historical_paper_calibration=d("0.420000"),
            source_quality=d("0.400000"),
            cost_drag=d("0.180000"),
            resolution_risk=d("0.820000"),
            team_confidence=d("0.300000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-decision-threshold-calibration-v9"
    assert result.recommended_threshold == d("0.200000")
    assert result.threshold_status == "blocked"
    assert result.reason_codes == (
        "paper_calibration_weak",
        "source_quality_low",
        "cost_drag_high",
        "resolution_risk_high",
        "team_confidence_low",
        "recommended_threshold_blocked",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_threshold_calibration_v9_elevates_for_combined_moderate_drag() -> None:
    result = report(
        calibration_input(
            historical_paper_calibration=d("0.700000"),
            source_quality=d("0.600000"),
            cost_drag=d("0.080000"),
            resolution_risk=d("0.600000"),
            team_confidence=d("0.700000"),
        ),
    )

    assert result.recommended_threshold == d("0.146000")
    assert result.threshold_status == "elevated"
    assert result.reason_codes == ("recommended_threshold_elevated",)


def test_threshold_calibration_v9_keeps_standard_threshold_for_strong_inputs() -> None:
    result = report()

    assert result.recommended_threshold == d("0.061000")
    assert result.threshold_status == "standard"
    assert result.reason_codes == ("threshold_calibration_v9_stable",)


def test_payload_uses_decimal_strings_utc_timestamps_and_no_public_numbers() -> None:
    module = api()
    result = report(
        calibration_input(cost_drag=d("0.080000"), resolution_risk=d("0.400000")),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_decision_threshold_calibration_v9_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["historical_paper_calibration"] == "0.900000"
    assert payload["source_quality"] == "0.950000"
    assert payload["cost_drag"] == "0.080000"
    assert payload["resolution_risk"] == "0.400000"
    assert payload["team_confidence"] == "0.900000"
    assert payload["recommended_threshold"] == "0.096500"
    assert payload["threshold_status"] == "standard"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report()

    for klass in (
        module.StrategyDecisionThresholdCalibrationV9Config,
        module.StrategyDecisionThresholdCalibrationV9Input,
        module.StrategyDecisionThresholdCalibrationV9Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.threshold_status = "blocked"  # type: ignore[misc]

    decimal_result_fields = {
        "historical_paper_calibration",
        "source_quality",
        "cost_drag",
        "resolution_risk",
        "team_confidence",
        "recommended_threshold",
    }
    for field in fields(result):
        if field.name in decimal_result_fields:
            assert type(getattr(result, field.name)) is Decimal

    with pytest.raises(ValueError, match="historical_paper_calibration"):
        calibration_input(historical_paper_calibration=0.90)
    with pytest.raises(ValueError, match="source_quality"):
        calibration_input(source_quality=1)
    with pytest.raises(ValueError, match="cost_drag"):
        calibration_input(cost_drag=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))


def test_validation_rejects_bounds_threshold_sequences_flags_and_types() -> None:
    module = api()
    valid_input = calibration_input()

    with pytest.raises(ValueError, match="input_value"):
        module.build_strategy_decision_threshold_calibration_v9_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_decision_threshold_calibration_v9_report(
            valid_input,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        calibration_input(source_quality=d("1.000001"))
    with pytest.raises(ValueError, match="cost_drag"):
        calibration_input(cost_drag=d("-0.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="minimum_recommended_threshold"):
        config(minimum_recommended_threshold=d("0.050000"))
    with pytest.raises(ValueError, match="elevated_threshold"):
        config(elevated_threshold=d("0.170000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_input, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_decision_threshold_calibration_v9_payload(
            replace(report(), readonly=False),
        )
    with pytest.raises(ValueError, match="report"):
        module.strategy_decision_threshold_calibration_v9_payload(object())


def test_report_revalidates_derived_fields_status_and_reason_codes() -> None:
    result = report()

    with pytest.raises(ValueError, match="recommended_threshold"):
        replace(result, recommended_threshold=d("0.062000"))
    with pytest.raises(ValueError, match="threshold_status"):
        replace(result, threshold_status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result,
            reason_codes=(
                "threshold_calibration_v9_stable",
                "threshold_calibration_v9_stable",
            ),
        )
    with pytest.raises(ValueError, match="recommended_threshold"):
        replace(result, recommended_threshold=d("-0.000001"))


def test_module_scope_has_no_external_io_db_or_live_action_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_roots = {
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
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
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
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert module_name.split(".")[0] not in forbidden_import_roots
