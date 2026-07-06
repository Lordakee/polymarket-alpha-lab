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
    / "strategy_recommendation_outcome_feedback_weight_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_outcome_feedback_weight_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def feedback(**overrides: object):
    module = api()
    values = {
        "recommendation_id": "rec_alpha",
        "market_slug": "fed_cut_decision",
        "specialist_team_id": "macro_rates",
        "prior_paper_outcome_score": d("0.900000"),
        "calibration_error": d("0.050000"),
        "source_reliability_score": d("0.850000"),
        "resolution_lag_hours": d("6"),
        "liquidity_exit_slippage": d("0.020000"),
        "specialist_team_performance_score": d("0.880000"),
        "base_recommendation_weight": d("0.750000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationOutcomeFeedbackV2Input(**values)


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
            feedback(recommendation_id="rec_alpha"),
            feedback(
                recommendation_id="rec_beta",
                market_slug="inflation_print",
                specialist_team_id="macro_data",
                prior_paper_outcome_score=d("0.700000"),
                calibration_error=d("0.200000"),
                source_reliability_score=d("0.700000"),
                resolution_lag_hours=d("24"),
                liquidity_exit_slippage=d("0.100000"),
                specialist_team_performance_score=d("0.650000"),
                base_recommendation_weight=d("0.650000"),
            ),
            feedback(
                recommendation_id="rec_gamma",
                market_slug="policy_speech",
                specialist_team_id="event_risk",
                prior_paper_outcome_score=d("0.350000"),
                calibration_error=d("0.450000"),
                source_reliability_score=d("0.400000"),
                resolution_lag_hours=d("72"),
                liquidity_exit_slippage=d("0.250000"),
                specialist_team_performance_score=d("0.300000"),
                base_recommendation_weight=d("0.600000"),
            ),
        )
    return module.build_strategy_recommendation_outcome_feedback_weight_v2_report(
        items,
        config=config,
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


def test_builds_decimal_future_weight_report_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.report_status == "blocked"
    assert report.recommendation_count == d("3")
    assert report.pass_recommendation_count == d("1")
    assert report.watch_recommendation_count == d("1")
    assert report.blocked_recommendation_count == d("1")
    assert report.average_future_recommendation_weight == d("0.442445")
    assert report.top_future_recommendation_weight == d("0.676250")
    assert report.bottom_future_recommendation_weight == d("0.195000")
    assert report.reason_codes == (
        "future_weight_report_blocked_rows",
        "future_weight_report_watch_rows",
    )

    rows = report.rows
    assert tuple(row.recommendation_id for row in rows) == (
        "rec_alpha",
        "rec_beta",
        "rec_gamma",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.feedback_weight_score for row in rows) == (
        d("0.901667"),
        d("0.701667"),
        d("0.325000"),
    )
    assert tuple(row.future_recommendation_weight for row in rows) == (
        d("0.676250"),
        d("0.456084"),
        d("0.195000"),
    )
    assert tuple(row.weight_status for row in rows) == ("pass", "watch", "blocked")

    payload = report.payload
    assert payload["recommendation_count"] == "3"
    assert payload["average_future_recommendation_weight"] == "0.442445"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["future_recommendation_weight"] == "0.676250"
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_report_is_report_only_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.report_status == "blocked"
    assert report.recommendation_count == d("0")
    assert report.average_future_recommendation_weight == d("0.000000")
    assert report.top_future_recommendation_weight == d("0.000000")
    assert report.bottom_future_recommendation_weight == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("future_weight_report_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyRecommendationOutcomeFeedbackWeightV2Config()
    sample = feedback()
    report = build_report(sample)
    row = report.rows[0]

    decimal_fields = {
        "prior_paper_outcome_weight",
        "calibration_accuracy_weight",
        "source_reliability_weight",
        "resolution_lag_weight",
        "liquidity_exit_weight",
        "specialist_team_performance_weight",
        "max_resolution_lag_hours",
        "max_liquidity_exit_slippage",
        "pass_weight_floor",
        "watch_weight_floor",
        "prior_paper_outcome_score",
        "calibration_error",
        "source_reliability_score",
        "resolution_lag_hours",
        "liquidity_exit_slippage",
        "specialist_team_performance_score",
        "base_recommendation_weight",
        "rank",
        "calibration_accuracy_score",
        "resolution_lag_score",
        "liquidity_exit_score",
        "feedback_weight_score",
        "future_recommendation_weight",
        "recommendation_count",
        "pass_recommendation_count",
        "watch_recommendation_count",
        "blocked_recommendation_count",
        "average_future_recommendation_weight",
        "top_future_recommendation_weight",
        "bottom_future_recommendation_weight",
    }

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "prior_paper_outcome_score",
            _DecimalSubclass("0.900000"),
            "prior_paper_outcome_score must be exactly Decimal",
        ),
        (
            "calibration_error",
            d("1.000001"),
            "calibration_error must be <= 1.000000",
        ),
        (
            "source_reliability_score",
            d("0.8500004"),
            "source_reliability_score must use six decimal places or fewer",
        ),
        (
            "resolution_lag_hours",
            Decimal("NaN"),
            "resolution_lag_hours must be finite",
        ),
        (
            "liquidity_exit_slippage",
            d("-0.000001"),
            "liquidity_exit_slippage must be >= 0.000000",
        ),
        (
            "base_recommendation_weight",
            1,
            "base_recommendation_weight must be exactly Decimal",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        feedback(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="prior_paper_outcome_weight must be exactly Decimal"):
        module.StrategyRecommendationOutcomeFeedbackWeightV2Config(
            prior_paper_outcome_weight=0,
        )
    with pytest.raises(ValueError, match="feedback weights must sum to 1.000000"):
        module.StrategyRecommendationOutcomeFeedbackWeightV2Config(
            source_reliability_weight=d("0.260000"),
        )
    with pytest.raises(ValueError, match="watch_weight_floor must not exceed pass_weight_floor"):
        module.StrategyRecommendationOutcomeFeedbackWeightV2Config(
            watch_weight_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyRecommendationOutcomeFeedbackWeightV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="feedback_items must be an iterable"):
        module.build_strategy_recommendation_outcome_feedback_weight_v2_report(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="feedback items must be StrategyRecommendationOutcomeFeedbackV2Input",
    ):
        module.build_strategy_recommendation_outcome_feedback_weight_v2_report(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_outcome_feedback_weight_v2_report(
            [feedback()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        feedback(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_future_recommendation_weight=d("0.415000"),
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            feedback(specialist_team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("future_weight_trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by future weight and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            pass_recommendation_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match report_status"):
        replace(
            report,
            reason_codes=("future_weight_report_passed",),
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
