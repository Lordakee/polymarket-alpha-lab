from __future__ import annotations

import ast
import importlib
import json
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
    / "team_specialist_resolution_feedback_priority_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_resolution_feedback_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def feedback(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "macro_specialist",
        "resolution_id": "macro_resolution_001",
        "resolution_feedback_score": d("0.900000"),
        "missed_learning_count": d("0"),
        "calibration_impact_score": d("0.800000"),
    }
    values.update(overrides)
    return module.TeamSpecialistResolutionFeedbackV2Input(**values)


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
            feedback(
                team_id="alpha_specialists",
                specialist_id="macro_specialist",
                resolution_id="macro_resolution_001",
            ),
            feedback(
                team_id="beta_specialists",
                specialist_id="policy_specialist",
                resolution_id="policy_resolution_001",
                resolution_feedback_score=d("0.700000"),
                missed_learning_count=d("1"),
                calibration_impact_score=d("0.600000"),
            ),
            feedback(
                team_id="gamma_specialists",
                specialist_id="rates_specialist",
                resolution_id="rates_resolution_001",
                resolution_feedback_score=d("0.400000"),
                missed_learning_count=d("5"),
                calibration_impact_score=d("0.300000"),
            ),
        )
    return module.build_team_specialist_resolution_feedback_priority_v2(
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


def test_builds_ranked_resolution_feedback_priority_report() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.priority_status == "blocked"
    assert report.item_count == d("3")
    assert report.high_priority_count == d("1")
    assert report.medium_priority_count == d("1")
    assert report.low_priority_count == d("1")
    assert report.average_priority_score == d("0.625000")
    assert report.top_priority_score == d("0.900000")
    assert report.bottom_priority_score == d("0.275000")
    assert report.reason_codes == (
        "feedback_priority_low_rows",
        "feedback_priority_medium_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.priority_score for row in rows) == (
        d("0.900000"),
        d("0.700000"),
        d("0.275000"),
    )
    assert tuple(row.priority_tier for row in rows) == ("high", "medium", "low")
    assert rows[2].reason_codes == (
        "priority_low",
        "resolution_feedback_low",
        "missed_learning_penalty_high",
        "calibration_impact_low",
    )


def test_missed_learning_penalties_reduce_priority() -> None:
    clear = feedback(
        team_id="clear_team",
        specialist_id="clear_specialist",
        resolution_id="clear_resolution",
        resolution_feedback_score=d("0.700000"),
        missed_learning_count=d("0"),
        calibration_impact_score=d("0.600000"),
    )
    missed = feedback(
        team_id="missed_team",
        specialist_id="missed_specialist",
        resolution_id="missed_resolution",
        resolution_feedback_score=d("0.700000"),
        missed_learning_count=d("4"),
        calibration_impact_score=d("0.600000"),
    )
    report = build_report(clear, missed)

    assert tuple(row.team_id for row in report.rows) == ("clear_team", "missed_team")
    assert tuple(row.priority_score for row in report.rows) == (
        d("0.750000"),
        d("0.550000"),
    )
    assert report.rows[0].missed_learning_health_score == d("1.000000")
    assert report.rows[1].missed_learning_health_score == d("0.200000")
    assert "missed_learning_penalty_watch" in report.rows[1].reason_codes


def test_calibration_impact_boosts_priority() -> None:
    high = feedback(
        team_id="impact_high_team",
        specialist_id="impact_high_specialist",
        resolution_id="impact_high_resolution",
        resolution_feedback_score=d("0.600000"),
        missed_learning_count=d("1"),
        calibration_impact_score=d("1.000000"),
    )
    low = feedback(
        team_id="impact_low_team",
        specialist_id="impact_low_specialist",
        resolution_id="impact_low_resolution",
        resolution_feedback_score=d("0.600000"),
        missed_learning_count=d("1"),
        calibration_impact_score=d("0.000000"),
    )
    report = build_report(high, low)

    assert tuple(row.team_id for row in report.rows) == (
        "impact_high_team",
        "impact_low_team",
    )
    assert tuple(row.priority_score for row in report.rows) == (
        d("0.750000"),
        d("0.500000"),
    )
    assert "calibration_impact_high" in report.rows[0].reason_codes
    assert "calibration_impact_low" in report.rows[1].reason_codes


def test_serialization_uses_decimal_strings_and_digest_payload() -> None:
    report = build_report()
    payload = report.payload

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["item_count"] == "3"
    assert payload["average_priority_score"] == "0.625000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["priority_score"] == "0.900000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_decimal_strings(payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistResolutionFeedbackPriorityV2Config()
    sample = feedback()
    report = build_report(sample)
    row = report.rows[0]

    decimal_field_names = {
        "resolution_feedback_weight",
        "missed_learning_weight",
        "calibration_impact_weight",
        "max_missed_learning_count",
        "high_priority_floor",
        "medium_priority_floor",
        "resolution_feedback_score",
        "missed_learning_count",
        "calibration_impact_score",
        "rank",
        "missed_learning_health_score",
        "priority_score",
        "item_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "average_priority_score",
        "top_priority_score",
        "bottom_priority_score",
    }

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not int
            assert type(value) is not float
            if field.name in decimal_field_names:
                assert type(value) is Decimal


def test_hard_flags_are_enforced_on_every_public_dataclass() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistResolutionFeedbackPriorityV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        feedback(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "resolution_feedback_score",
            _DecimalSubclass("0.900000"),
            "resolution_feedback_score must be exactly Decimal",
        ),
        (
            "calibration_impact_score",
            d("1.000001"),
            "calibration_impact_score must be <= 1.000000",
        ),
        (
            "resolution_feedback_score",
            d("0.8500004"),
            "resolution_feedback_score must use six decimal places or fewer",
        ),
        (
            "calibration_impact_score",
            Decimal("NaN"),
            "calibration_impact_score must be finite",
        ),
        (
            "missed_learning_count",
            d("1.5"),
            "missed_learning_count must be an integral Decimal",
        ),
        (
            "missed_learning_count",
            d("-1"),
            "missed_learning_count must be >= 0.000000",
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

    with pytest.raises(ValueError, match="resolution_feedback_weight must be exactly Decimal"):
        module.TeamSpecialistResolutionFeedbackPriorityV2Config(
            resolution_feedback_weight=0,
        )
    with pytest.raises(ValueError, match="priority weights must sum to 1.000000"):
        module.TeamSpecialistResolutionFeedbackPriorityV2Config(
            calibration_impact_weight=d("0.260000"),
        )
    with pytest.raises(
        ValueError,
        match="medium_priority_floor must not exceed high_priority_floor",
    ):
        module.TeamSpecialistResolutionFeedbackPriorityV2Config(
            medium_priority_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistResolutionFeedbackPriorityV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="feedback_items must be an iterable"):
        module.build_team_specialist_resolution_feedback_priority_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="feedback items must be TeamSpecialistResolutionFeedbackV2Input",
    ):
        module.build_team_specialist_resolution_feedback_priority_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_resolution_feedback_priority_v2(
            [feedback()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="duplicate identities"):
        module.build_team_specialist_resolution_feedback_priority_v2(
            [feedback(), feedback()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_priority_score=d("0.600000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
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


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by priority score and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="priority counts must match rows"):
        replace(report, high_priority_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match priority_status"):
        replace(report, reason_codes=("feedback_priority_high_rows",))


def test_module_scope_has_no_unsafe_surfaces() -> None:
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

    unsafe_fragments = module.UNSAFE_PUBLIC_TEXT_FRAGMENTS
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
    assert not any(fragment in name.lower() for name in module.__all__ for fragment in unsafe_fragments)
    assert_no_float_values([imports, call_names, attribute_names])
