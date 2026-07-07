from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_probability_calibration_drift_digest.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_probability_calibration_drift_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-probability-calibration-drift-digest-test",
        "min_settled_sample_count": d("10"),
        "recent_brier_block_threshold": d("0.260000"),
        "calibration_delta_watch_threshold": d("0.050000"),
        "calibration_delta_block_threshold": d("0.150000"),
        "confidence_overstatement_watch_threshold": d("0.200000"),
        "source_reliability_decline_watch_threshold": d("0.050000"),
    }
    values.update(overrides)
    return module.TeamProbabilityCalibrationDriftDigestConfig(**values)


def fact(**overrides: object):
    module = api()
    values = {
        "team_id": "politics",
        "settled_sample_count": d("30"),
        "recent_brier_error": d("0.080000"),
        "trailing_brier_error": d("0.090000"),
        "calibration_error_delta": d("-0.010000"),
        "confidence_overstatement_rate": d("0.050000"),
        "source_reliability_delta": d("0.020000"),
    }
    values.update(overrides)
    return module.TeamProbabilityCalibrationDriftFact(**values)


def build_report(*facts: object, cfg=None):
    module = api()
    return module.build_team_probability_calibration_drift_digest(
        facts,
        config=cfg if cfg is not None else config(),
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


def test_builds_deterministic_rows_and_aggregate_memory_status() -> None:
    report = build_report(
        fact(
            team_id="equity_index",
            settled_sample_count=d("4"),
            recent_brier_error=d("0.290000"),
            trailing_brier_error=d("0.120000"),
            calibration_error_delta=d("0.170000"),
            confidence_overstatement_rate=d("0.100000"),
            source_reliability_delta=d("-0.020000"),
        ),
        fact(
            team_id="politics",
            settled_sample_count=d("30"),
            recent_brier_error=d("0.080000"),
            trailing_brier_error=d("0.090000"),
            calibration_error_delta=d("-0.010000"),
            confidence_overstatement_rate=d("0.050000"),
            source_reliability_delta=d("0.020000"),
        ),
        fact(
            team_id="crypto_btc",
            settled_sample_count=d("24"),
            recent_brier_error=d("0.170000"),
            trailing_brier_error=d("0.100000"),
            calibration_error_delta=d("0.070000"),
            confidence_overstatement_rate=d("0.220000"),
            source_reliability_delta=d("-0.080000"),
        ),
    )

    assert report.memory_status == "blocked"
    assert report.fact_count == d("3")
    assert report.row_count == d("3")
    assert report.total_settled_sample_count == d("58")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.average_recent_brier_error == d("0.131724")
    assert report.average_trailing_brier_error == d("0.096207")
    assert report.average_calibration_error_delta == d("0.035517")
    assert tuple(row.team_id for row in report.rows) == (
        "politics",
        "crypto_btc",
        "equity_index",
    )
    assert tuple(row.memory_status for row in report.rows) == (
        "pass",
        "watch",
        "blocked",
    )
    assert report.rows[0].reason_codes == (
        "team_probability_calibration_drift_digest_passed",
    )
    assert report.rows[1].reason_codes == (
        "team_probability_calibration_drift_digest_calibration_error_drift_watch",
        "team_probability_calibration_drift_digest_confidence_overstatement_watch",
        "team_probability_calibration_drift_digest_source_reliability_decline_watch",
    )
    assert report.rows[2].reason_codes == (
        "team_probability_calibration_drift_digest_insufficient_settled_sample",
        "team_probability_calibration_drift_digest_high_recent_brier_error",
        "team_probability_calibration_drift_digest_calibration_error_drift_block",
    )
    assert report.reason_codes == (
        "team_probability_calibration_drift_digest_insufficient_settled_sample",
        "team_probability_calibration_drift_digest_high_recent_brier_error",
        "team_probability_calibration_drift_digest_calibration_error_drift_block",
        "team_probability_calibration_drift_digest_calibration_error_drift_watch",
        "team_probability_calibration_drift_digest_confidence_overstatement_watch",
        "team_probability_calibration_drift_digest_source_reliability_decline_watch",
    )


def test_empty_fact_set_blocks_digest_without_rows() -> None:
    report = build_report()

    assert report.memory_status == "blocked"
    assert report.fact_count == d("0")
    assert report.row_count == d("0")
    assert report.total_settled_sample_count == d("0")
    assert report.average_recent_brier_error is None
    assert report.rows == ()
    assert report.reason_codes == (
        "team_probability_calibration_drift_digest_empty_facts",
    )
    assert report.reason_code_counts[0].reason_code == (
        "team_probability_calibration_drift_digest_empty_facts"
    )
    assert report.reason_code_counts[0].count == d("1")


def test_payload_serializes_public_aggregate_without_raw_refs_or_floats() -> None:
    module = api()
    report = build_report(fact())

    payload = module.team_probability_calibration_drift_digest_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["fact_count"] == "1"
    assert payload["total_settled_sample_count"] == "30"
    assert payload["average_recent_brier_error"] == "0.080000"
    assert payload["rows"][0]["recent_brier_error"] == "0.080000"
    assert payload["rows"][0]["memory_status"] == "pass"
    assert_no_float_values(payload)
    payload_keys = str(payload)
    for forbidden_fragment in (
        "market_id",
        "market_slug",
        "candidate_id",
        "source_reference",
        "source_url",
    ):
        assert forbidden_fragment not in payload_keys

    with pytest.raises(ValueError, match="float"):
        module.team_probability_calibration_drift_digest_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "value": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe surface field"):
        module.team_probability_calibration_drift_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_address": "0xdeadbeef",
            },
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_fact = fact()
    sample_report = build_report(sample_fact)
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (
        sample_config,
        sample_fact,
        sample_row,
        sample_reason_count,
        sample_report,
    ):
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
        fact(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(fact(readonly=False))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("settled_sample_count", 10, "settled_sample_count must not be an integer"),
        (
            "recent_brier_error",
            _DecimalSubclass("0.100000"),
            "recent_brier_error must be exactly Decimal",
        ),
        (
            "trailing_brier_error",
            d("0.1000001"),
            "trailing_brier_error must be quantized to 0.000001",
        ),
        (
            "calibration_error_delta",
            d("1.000001"),
            "calibration_error_delta must be between -1 and 1",
        ),
        (
            "confidence_overstatement_rate",
            0.10,
            "confidence_overstatement_rate must not be a float",
        ),
        (
            "source_reliability_delta",
            Decimal("NaN"),
            "source_reliability_delta must be finite",
        ),
    ),
)
def test_validation_rejects_non_decimal_and_out_of_range_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        fact(**{field_name: bad_value})


def test_validation_rejects_unknown_strategy_team_duplicates_and_bad_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id must be a known strategy team"):
        fact(team_id="macro_rates")
    with pytest.raises(ValueError, match="team_id values must be unique"):
        build_report(fact(team_id="politics"), fact(team_id="politics"))
    with pytest.raises(ValueError, match="config must be"):
        module.build_team_probability_calibration_drift_digest(
            (fact(),),
            config=object(),
        )
    with pytest.raises(ValueError, match="watch threshold must be below block threshold"):
        config(
            calibration_delta_watch_threshold=d("0.200000"),
            calibration_delta_block_threshold=d("0.150000"),
        )


def test_module_scope_has_no_file_database_network_trading_or_raw_reference_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    field_names: list[str] = []
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
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            field_names.append(node.target.id)
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
        "order",
        "os",
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
        "rollback",
        "send",
        "write",
    }
    forbidden_field_names = {
        "account_id",
        "auth_token",
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "order_id",
        "source_id",
        "source_reference",
        "source_url",
        "wallet_address",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(name in forbidden_field_names for name in field_names)
    assert_no_float_values([imports, call_names, attribute_names, field_names])
