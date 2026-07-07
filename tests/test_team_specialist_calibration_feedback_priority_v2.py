from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
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
    / "team_specialist_calibration_feedback_priority_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_calibration_feedback_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def feedback(**overrides: object) -> Any:
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "domain": "crypto",
        "forecast_count": d("100"),
        "resolved_count": d("80"),
        "miscalibrated_count": d("64"),
        "average_probability_error": d("0.600000"),
        "latest_feedback_at": GENERATED_AT - timedelta(days=3),
        "unresolved_feedback_count": d("5"),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationFeedbackPriorityV2Input(**values)


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            feedback(
                team_id="alpha_specialists",
                domain="crypto",
                forecast_count=d("100"),
                resolved_count=d("80"),
                miscalibrated_count=d("64"),
                average_probability_error=d("0.600000"),
                latest_feedback_at=GENERATED_AT - timedelta(days=3),
                unresolved_feedback_count=d("5"),
            ),
            feedback(
                team_id="beta_specialists",
                domain="macro",
                forecast_count=d("90"),
                resolved_count=d("60"),
                miscalibrated_count=d("18"),
                average_probability_error=d("0.300000"),
                latest_feedback_at=GENERATED_AT - timedelta(hours=36),
                unresolved_feedback_count=d("3"),
            ),
            feedback(
                team_id="gamma_specialists",
                domain="sports",
                forecast_count=d("30"),
                resolved_count=d("30"),
                miscalibrated_count=d("0"),
                average_probability_error=d("0.030000"),
                latest_feedback_at=GENERATED_AT - timedelta(hours=1),
                unresolved_feedback_count=d("0"),
            ),
        )
    return module.build_team_specialist_calibration_feedback_priority_v2(
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


def assert_decimal_strings(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_decimal_strings(item)
    if isinstance(value, list):
        for item in value:
            assert_decimal_strings(item)
    assert_no_float_values(value)


def test_builds_ranked_calibration_feedback_priority_report() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.TeamSpecialistCalibrationFeedbackPriorityV2Report
    assert is_dataclass(report)
    assert report.report_status == "block"
    assert report.team_count == d("3")
    assert report.high_priority_count == d("1")
    assert report.medium_priority_count == d("1")
    assert report.low_priority_count == d("1")
    assert report.blocked_feedback_count == d("1")
    assert report.stale_feedback_count == d("2")
    assert report.max_calibration_gap_score == d("0.770000")
    assert report.reason_code_counts == (
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="calibration_gap_high",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="calibration_gap_low",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="calibration_gap_medium",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="feedback_stale",
            count=d("2"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="forecast_outcome_gap_closed",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="forecast_outcome_gap_open",
            count=d("2"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="miscalibration_rate_clear",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="miscalibration_rate_high",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="miscalibration_rate_watch",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="probability_error_clear",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="probability_error_high",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="probability_error_watch",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="unresolved_feedback_block",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="unresolved_feedback_clear",
            count=d("1"),
        ),
        module.TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code="unresolved_feedback_watch",
            count=d("1"),
        ),
    )

    rows = report.rows
    assert tuple((row.team_id, row.domain, row.status) for row in rows) == (
        ("alpha_specialists", "crypto", "block"),
        ("beta_specialists", "macro", "watch"),
        ("gamma_specialists", "sports", "pass"),
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.calibration_gap_score for row in rows) == (
        d("0.770000"),
        d("0.400000"),
        d("0.014667"),
    )
    assert tuple(row.feedback_age_seconds for row in rows) == (
        d("259200.000000"),
        d("129600.000000"),
        d("3600.000000"),
    )
    assert tuple(row.priority_tier for row in rows) == ("high", "medium", "low")
    assert rows[0].reason_codes == (
        "calibration_gap_high",
        "miscalibration_rate_high",
        "probability_error_high",
        "unresolved_feedback_block",
        "feedback_stale",
        "forecast_outcome_gap_open",
    )


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    report = build_report(use_default_items=False)

    assert report.report_status == "empty"
    assert report.team_count == d("0")
    assert report.high_priority_count == d("0")
    assert report.medium_priority_count == d("0")
    assert report.low_priority_count == d("0")
    assert report.blocked_feedback_count == d("0")
    assert report.stale_feedback_count == d("0")
    assert report.max_calibration_gap_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()


def test_deterministic_sorting_uses_gap_age_and_identity_tiebreakers() -> None:
    first = feedback(
        team_id="alpha_specialists",
        domain="macro",
        forecast_count=d("10"),
        resolved_count=d("10"),
        miscalibrated_count=d("4"),
        average_probability_error=d("0.200000"),
        latest_feedback_at=GENERATED_AT - timedelta(hours=2),
        unresolved_feedback_count=d("1"),
    )
    second = feedback(
        team_id="beta_specialists",
        domain="crypto",
        forecast_count=d("10"),
        resolved_count=d("10"),
        miscalibrated_count=d("4"),
        average_probability_error=d("0.200000"),
        latest_feedback_at=GENERATED_AT - timedelta(hours=3),
        unresolved_feedback_count=d("1"),
    )
    third = feedback(
        team_id="alpha_specialists",
        domain="crypto",
        forecast_count=d("10"),
        resolved_count=d("10"),
        miscalibrated_count=d("4"),
        average_probability_error=d("0.200000"),
        latest_feedback_at=GENERATED_AT - timedelta(hours=2),
        unresolved_feedback_count=d("1"),
    )
    report = build_report(first, second, third)

    assert tuple((row.team_id, row.domain) for row in report.rows) == (
        ("beta_specialists", "crypto"),
        ("alpha_specialists", "crypto"),
        ("alpha_specialists", "macro"),
    )


def test_payload_is_json_ready_decimal_stringed_and_digest_protected() -> None:
    report = build_report()
    payload = report.payload

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["team_count"] == "3"
    assert payload["max_calibration_gap_score"] == "0.770000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["calibration_gap_score"] == "0.770000"
    assert payload["reason_code_counts"][0] == {
        "reason_code": "calibration_gap_high",
        "count": "1",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_decimal_strings(payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="team_count must match rows"):
        replace(report, team_count=d("4"))


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCalibrationFeedbackPriorityV2Config()
    item = feedback()
    report = build_report(item)
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    decimal_field_names = {
        "miscalibrated_rate_weight",
        "probability_error_weight",
        "unresolved_feedback_weight",
        "feedback_staleness_weight",
        "max_unresolved_feedback_count",
        "stale_feedback_after_seconds",
        "high_priority_floor",
        "medium_priority_floor",
        "forecast_count",
        "resolved_count",
        "miscalibrated_count",
        "average_probability_error",
        "unresolved_feedback_count",
        "rank",
        "calibration_gap_score",
        "feedback_age_seconds",
        "team_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "blocked_feedback_count",
        "stale_feedback_count",
        "max_calibration_gap_score",
        "count",
    }

    for item_to_check in (config, item, row, report, reason_count):
        assert is_dataclass(item_to_check)
        assert item_to_check.paper_only is True
        assert item_to_check.report_only is True
        assert item_to_check.readonly is True
        with pytest.raises(FrozenInstanceError):
            item_to_check.paper_only = False  # type: ignore[misc]
        for field in fields(item_to_check):
            value = getattr(item_to_check, field.name)
            assert type(value) is not int
            assert type(value) is not float
            if field.name in decimal_field_names:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCalibrationFeedbackPriorityV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        feedback(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("forecast_count", d("-1"), "forecast_count must be >= 0.000000"),
        ("forecast_count", d("1.5"), "forecast_count must be an integral Decimal"),
        (
            "resolved_count",
            _DecimalSubclass("1"),
            "resolved_count must be exactly Decimal",
        ),
        (
            "average_probability_error",
            d("1.000001"),
            "average_probability_error must be <= 1.000000",
        ),
        (
            "average_probability_error",
            d("0.1234567"),
            "average_probability_error must use six decimal places or fewer",
        ),
        (
            "unresolved_feedback_count",
            d("-1"),
            "unresolved_feedback_count must be >= 0.000000",
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


def test_build_validation_rejects_inconsistent_counts_times_duplicates_and_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="config must be"):
        module.build_team_specialist_calibration_feedback_priority_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="feedback_items must be an iterable"):
        module.build_team_specialist_calibration_feedback_priority_v2(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="must be TeamSpecialistCalibrationFeedbackPriorityV2Input"):
        module.build_team_specialist_calibration_feedback_priority_v2(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="resolved_count must not exceed forecast_count"):
        feedback(forecast_count=d("1"), resolved_count=d("2"))
    with pytest.raises(ValueError, match="miscalibrated_count must not exceed resolved_count"):
        feedback(resolved_count=d("1"), miscalibrated_count=d("2"))
    with pytest.raises(ValueError, match="latest_feedback_at must not be after generated_at"):
        build_report(feedback(latest_feedback_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="latest_feedback_at must be timezone-aware"):
        feedback(latest_feedback_at=datetime(2026, 7, 6, 11, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="duplicate team/domain"):
        build_report(feedback(), feedback())
    with pytest.raises(ValueError, match="priority weights must sum to 1.000000"):
        module.TeamSpecialistCalibrationFeedbackPriorityV2Config(
            feedback_staleness_weight=d("0.110000"),
        )
    with pytest.raises(
        ValueError,
        match="medium_priority_floor must not exceed high_priority_floor",
    ):
        module.TeamSpecialistCalibrationFeedbackPriorityV2Config(
            medium_priority_floor=d("0.800000"),
        )


def test_report_revalidates_row_order_and_rollups() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by calibration gap and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="priority counts must match rows"):
        replace(report, high_priority_count=d("2"))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="report_status must match rows"):
        replace(report, report_status="pass")


def test_rejects_unsafe_public_payload_terms() -> None:
    module = api()
    unsafe_terms = (
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
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public payload"):
            feedback(team_id=f"{term}_value")
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("example", {f"{term}_key": "safe"})
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("example", {"safe_key": f"{term}_value"})


def test_module_scope_has_no_io_db_network_live_trading_or_float_surface() -> None:
    module = api()
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

    forbidden_import_roots = {
        "os",
        "pathlib",
        "sqlite3",
        "psycopg",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "supabase",
    }
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
    assert not any(imported.split(".")[0] in forbidden_import_roots for imported in imports)
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(
        fragment in name.lower()
        for name in module.__all__
        for fragment in module.UNSAFE_PUBLIC_TEXT_FRAGMENTS
    )
    assert_no_float_values([imports, call_names, attribute_names])
