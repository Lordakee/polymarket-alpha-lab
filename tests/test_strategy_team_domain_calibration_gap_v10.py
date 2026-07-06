from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_domain_calibration_gap_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_domain_calibration_gap_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def calibration(**overrides: object):
    module = api()
    values = {
        "domain_id": "macro_rates",
        "team_id": "rates_specialists",
        "recent_brier_error": d("0.080000"),
        "resolved_market_count": d("60"),
        "confidence_overstatement": d("0.050000"),
        "source_reliability_drift": d("0.030000"),
        "postmortem_completion": d("1.000000"),
    }
    values.update(overrides)
    return module.TeamDomainCalibrationGapV10Input(**values)


def score(**overrides: object):
    module = api()
    return module.score_team_domain_calibration_gap_v10(calibration(**overrides))


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_strong_recent_calibration_scores_as_calibrated_and_low_priority() -> None:
    result = score()

    assert is_dataclass(result)
    assert result.domain_id == "macro_rates"
    assert result.team_id == "rates_specialists"
    assert result.calibration_gap_score == d("0.046500")
    assert result.calibration_status == "calibrated"
    assert result.remediation_priority == "low"
    assert result.reason_codes == (
        "team_domain_calibration_calibrated",
        "brier_error_low",
        "resolved_count_strong",
        "confidence_overstatement_low",
        "source_reliability_drift_low",
        "postmortem_completion_complete",
        "calibration_priority_low",
    )


def test_overconfident_sparse_drifting_team_scores_as_gap_and_high_priority() -> None:
    result = score(
        recent_brier_error=d("0.420000"),
        resolved_market_count=d("6"),
        confidence_overstatement=d("0.310000"),
        source_reliability_drift=d("0.240000"),
        postmortem_completion=d("0.400000"),
    )

    assert result.calibration_gap_score == d("0.441000")
    assert result.calibration_status == "gap"
    assert result.remediation_priority == "high"
    assert result.reason_codes == (
        "team_domain_calibration_gap",
        "brier_error_high",
        "resolved_count_low",
        "confidence_overstatement_high",
        "source_reliability_drift_high",
        "postmortem_completion_low",
        "calibration_priority_high",
    )


def test_mid_quality_signals_score_as_watch_and_medium_priority() -> None:
    result = score(
        recent_brier_error=d("0.190000"),
        resolved_market_count=d("20"),
        confidence_overstatement=d("0.180000"),
        source_reliability_drift=d("0.110000"),
        postmortem_completion=d("0.750000"),
    )

    assert result.calibration_gap_score == d("0.216000")
    assert result.calibration_status == "watch"
    assert result.remediation_priority == "medium"
    assert result.reason_codes == (
        "team_domain_calibration_watch",
        "brier_error_watch",
        "resolved_count_watch",
        "confidence_overstatement_watch",
        "source_reliability_drift_watch",
        "postmortem_completion_watch",
        "calibration_priority_medium",
    )


def test_inputs_config_and_results_are_frozen_decimal_only_and_readonly() -> None:
    module = api()
    sample = calibration()
    config = module.TeamDomainCalibrationGapV10Config()
    result = score()

    for item in (sample, config, result):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.domain_id = "crypto_btc"  # type: ignore[attr-defined, misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "recent_brier_error",
                "resolved_market_count",
                "confidence_overstatement",
                "source_reliability_drift",
                "postmortem_completion",
                "brier_error_weight",
                "resolved_count_weight",
                "confidence_overstatement_weight",
                "source_reliability_drift_weight",
                "postmortem_incompletion_weight",
                "strong_resolved_market_count",
                "watch_resolved_market_count",
                "watch_gap_score",
                "high_gap_score",
                "calibration_gap_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("recent_brier_error", 0.08, "recent_brier_error must be exactly Decimal"),
        (
            "confidence_overstatement",
            _DecimalSubclass("0.050000"),
            "confidence_overstatement must be exactly Decimal",
        ),
        (
            "source_reliability_drift",
            d("1.000001"),
            "source_reliability_drift must be <= 1.000000",
        ),
        (
            "postmortem_completion",
            d("-0.000001"),
            "postmortem_completion must be >= 0.000000",
        ),
        (
            "resolved_market_count",
            d("12.5"),
            "resolved_market_count must be an integral Decimal",
        ),
        ("recent_brier_error", Decimal("NaN"), "recent_brier_error must be finite"),
    ),
)
def test_validation_rejects_non_decimal_and_out_of_range_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        calibration(**{field_name: bad_value})


def test_validation_rejects_decimal_overprecision() -> None:
    module = api()

    with pytest.raises(
        ValueError,
        match="recent_brier_error must use six decimal places or fewer",
    ):
        calibration(recent_brier_error=d("0.0800004"))
    with pytest.raises(
        ValueError,
        match="watch_gap_score must use six decimal places or fewer",
    ):
        module.TeamDomainCalibrationGapV10Config(watch_gap_score=d("0.1500004"))


def test_validation_rejects_blank_strings_unsafe_flags_and_wrong_input_type() -> None:
    module = api()

    with pytest.raises(ValueError, match="domain_id must be a non-empty string"):
        calibration(domain_id=" ")
    with pytest.raises(ValueError, match="team_id must be a non-empty string"):
        calibration(team_id="")
    with pytest.raises(ValueError, match="paper_only must be True"):
        calibration(paper_only=False)
    with pytest.raises(
        ValueError,
        match="calibration must be a TeamDomainCalibrationGapV10Input",
        ):
        module.score_team_domain_calibration_gap_v10(object())


def test_rejects_unsafe_public_payload_strings() -> None:
    with pytest.raises(
        ValueError,
        match="unsafe string value in TeamDomainCalibrationGapV10Input",
    ):
        calibration(domain_id="wallet")

    with pytest.raises(
        ValueError,
        match="unsafe string value in TeamDomainCalibrationGapV10Result",
    ):
        replace(score(), team_id="live_trader")


def test_config_rejects_non_decimal_weights_threshold_order_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="brier_error_weight must be exactly Decimal"):
        module.TeamDomainCalibrationGapV10Config(brier_error_weight=0)
    with pytest.raises(ValueError, match="calibration gap weights must sum to 1.000000"):
        module.TeamDomainCalibrationGapV10Config(brier_error_weight=d("0.300000"))
    with pytest.raises(
        ValueError,
        match="watch_resolved_market_count must not exceed strong_resolved_market_count",
    ):
        module.TeamDomainCalibrationGapV10Config(
            watch_resolved_market_count=d("50"),
        )
    with pytest.raises(ValueError, match="watch_gap_score must not exceed high_gap_score"):
        module.TeamDomainCalibrationGapV10Config(watch_gap_score=d("0.500000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        module.TeamDomainCalibrationGapV10Config(readonly=False)


def test_result_revalidates_derived_priority_and_reason_codes() -> None:
    result = score()

    with pytest.raises(
        ValueError,
        match="remediation_priority must match calibration_status",
    ):
        replace(result, remediation_priority="high")
    with pytest.raises(
        ValueError,
        match="reason_codes must start with calibration_status",
    ):
        replace(
            result,
            reason_codes=(
                "team_domain_calibration_watch",
                *result.reason_codes[1:],
            ),
        )
    with pytest.raises(
        ValueError,
        match="reason_codes must end with remediation_priority",
    ):
        replace(
            result,
            reason_codes=(
                *result.reason_codes[:-1],
                "calibration_priority_medium",
            ),
        )


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
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
        "cancel",
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
    assert_no_float_values([imports, call_names, attribute_names])
