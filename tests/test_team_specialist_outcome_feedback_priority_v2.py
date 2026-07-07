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
    / "team_specialist_outcome_feedback_priority_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_outcome_feedback_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def resolved_at(hours_ago: str) -> datetime:
    seconds = d(hours_ago) * d("3600")
    return datetime(2026, 7, 7, 12, 0, tzinfo=UTC) - timedelta(
        seconds=int(seconds),
    )


def outcome(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "macro_specialist",
        "category_id": "macro",
        "market_id": "fed_cut_2026_07",
        "outcome_id": "fed_cut_yes",
        "forecast_probability": d("0.900000"),
        "resolved_probability": d("0.000000"),
        "confidence_score": d("0.950000"),
        "category_importance_score": d("0.800000"),
        "source_contradiction_score": d("0.700000"),
        "resolution_ambiguity_score": d("0.600000"),
        "resolved_at": resolved_at("1"),
    }
    values.update(overrides)
    return module.TeamSpecialistOutcomeFeedbackPriorityV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            outcome(
                team_id="alpha_specialists",
                specialist_id="macro_specialist",
                category_id="macro",
                market_id="fed_cut_2026_07",
                outcome_id="fed_cut_yes",
            ),
            outcome(
                team_id="beta_specialists",
                specialist_id="policy_specialist",
                category_id="policy",
                market_id="ballot_case_2026",
                outcome_id="case_affirmed",
                forecast_probability=d("0.600000"),
                resolved_probability=d("0.000000"),
                confidence_score=d("0.650000"),
                category_importance_score=d("0.500000"),
                source_contradiction_score=d("0.200000"),
                resolution_ambiguity_score=d("0.400000"),
                resolved_at=resolved_at("12"),
            ),
            outcome(
                team_id="gamma_specialists",
                specialist_id="sports_specialist",
                category_id="sports",
                market_id="final_score_2026",
                outcome_id="home_cover",
                forecast_probability=d("0.510000"),
                resolved_probability=d("0.500000"),
                confidence_score=d("0.550000"),
                category_importance_score=d("0.200000"),
                source_contradiction_score=d("0.000000"),
                resolution_ambiguity_score=d("0.100000"),
                resolved_at=resolved_at("48"),
            ),
        )
    return module.build_team_specialist_outcome_feedback_priority_v2(
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


def test_builds_ranked_phase_1_outcome_feedback_priority_report() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.priority_status == "high"
    assert report.item_count == d("3")
    assert report.high_priority_count == d("1")
    assert report.medium_priority_count == d("1")
    assert report.low_priority_count == d("1")
    assert report.average_priority_score == d("0.458944")
    assert report.top_priority_score == d("0.820833")
    assert report.bottom_priority_score == d("0.131000")
    assert report.reason_codes == (
        "outcome_feedback_priority_high_rows",
        "outcome_feedback_priority_medium_rows",
        "outcome_feedback_priority_low_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.priority_score for row in rows) == (
        d("0.820833"),
        d("0.425000"),
        d("0.131000"),
    )
    assert tuple(row.priority_tier for row in rows) == ("high", "medium", "low")
    assert rows[0].forecast_error_score == d("0.900000")
    assert rows[0].confidence_gap_score == d("0.850000")
    assert rows[0].recency_score == d("0.958333")
    assert rows[0].outcome_age_seconds == d("3600.000000")
    assert rows[0].reason_codes == (
        "priority_high",
        "forecast_error_high",
        "confidence_gap_high",
        "category_importance_high",
        "source_contradiction_high",
        "resolution_ambiguity_high",
        "recency_current",
    )


def test_priority_sorting_reasons_and_digests_are_deterministic() -> None:
    items = (
        outcome(
            team_id="same_score_b",
            specialist_id="specialist_b",
            category_id="macro",
            market_id="market_b",
            outcome_id="outcome_b",
            forecast_probability=d("0.600000"),
            resolved_probability=d("0.000000"),
            confidence_score=d("0.650000"),
            category_importance_score=d("0.500000"),
            source_contradiction_score=d("0.200000"),
            resolution_ambiguity_score=d("0.400000"),
            resolved_at=resolved_at("12"),
        ),
        outcome(
            team_id="same_score_a",
            specialist_id="specialist_a",
            category_id="macro",
            market_id="market_a",
            outcome_id="outcome_a",
            forecast_probability=d("0.600000"),
            resolved_probability=d("0.000000"),
            confidence_score=d("0.650000"),
            category_importance_score=d("0.500000"),
            source_contradiction_score=d("0.200000"),
            resolution_ambiguity_score=d("0.400000"),
            resolved_at=resolved_at("12"),
        ),
    )

    report = build_report(*items)
    reversed_report = build_report(*reversed(items))

    assert tuple(row.team_id for row in report.rows) == (
        "same_score_a",
        "same_score_b",
    )
    assert report.payload == reversed_report.payload
    assert report.derived_validation_digest == reversed_report.derived_validation_digest
    assert tuple(row.row_digest for row in report.rows) == tuple(
        row.row_digest for row in reversed_report.rows
    )
    assert all(len(row.row_digest) == 64 for row in report.rows)
    assert all(set(row.row_digest) <= set("0123456789abcdef") for row in report.rows)


def test_recency_score_clamps_and_future_resolutions_are_rejected() -> None:
    stale = outcome(
        resolved_at=resolved_at("48"),
        forecast_probability=d("0.900000"),
        resolved_probability=d("0.000000"),
        confidence_score=d("0.950000"),
    )
    report = build_report(stale)

    assert report.rows[0].recency_score == d("0.000000")
    assert report.rows[0].outcome_age_seconds == d("172800.000000")
    assert "recency_stale" in report.rows[0].reason_codes

    with pytest.raises(ValueError, match="resolved_at must not be after generated_at"):
        build_report(
            outcome(resolved_at=datetime(2026, 7, 7, 12, 1, tzinfo=UTC)),
        )


def test_serialization_uses_decimal_strings_and_validation_digests() -> None:
    report = build_report()
    payload = report.payload

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["item_count"] == "3"
    assert payload["average_priority_score"] == "0.458944"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["priority_score"] == "0.820833"
    assert payload["rows"][0]["row_digest"] == report.rows[0].row_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_decimal_strings(payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistOutcomeFeedbackPriorityV2Config()
    sample = outcome()
    report = build_report(sample)
    row = report.rows[0]

    decimal_field_names = {
        "forecast_error_weight",
        "confidence_gap_weight",
        "category_importance_weight",
        "source_contradiction_weight",
        "resolution_ambiguity_weight",
        "recency_weight",
        "max_recency_age_seconds",
        "high_priority_floor",
        "medium_priority_floor",
        "forecast_probability",
        "resolved_probability",
        "confidence_score",
        "category_importance_score",
        "source_contradiction_score",
        "resolution_ambiguity_score",
        "rank",
        "forecast_error_score",
        "confidence_gap_score",
        "recency_score",
        "outcome_age_seconds",
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
        module.TeamSpecialistOutcomeFeedbackPriorityV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        outcome(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "forecast_probability",
            _DecimalSubclass("0.900000"),
            "forecast_probability must be exactly Decimal",
        ),
        (
            "resolved_probability",
            d("1.000001"),
            "resolved_probability must be <= 1.000000",
        ),
        (
            "confidence_score",
            d("0.8500004"),
            "confidence_score must use six decimal places or fewer",
        ),
        (
            "category_importance_score",
            Decimal("NaN"),
            "category_importance_score must be finite",
        ),
        (
            "source_contradiction_score",
            d("-0.000001"),
            "source_contradiction_score must be >= 0.000000",
        ),
        (
            "resolution_ambiguity_score",
            d("1.000001"),
            "resolution_ambiguity_score must be <= 1.000000",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        outcome(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="forecast_error_weight must be exactly Decimal"):
        module.TeamSpecialistOutcomeFeedbackPriorityV2Config(
            forecast_error_weight=0,
        )
    with pytest.raises(ValueError, match="priority weights must sum to 1.000000"):
        module.TeamSpecialistOutcomeFeedbackPriorityV2Config(
            recency_weight=d("0.110000"),
        )
    with pytest.raises(
        ValueError,
        match="medium_priority_floor must not exceed high_priority_floor",
    ):
        module.TeamSpecialistOutcomeFeedbackPriorityV2Config(
            medium_priority_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="max_recency_age_seconds must be positive"):
        module.TeamSpecialistOutcomeFeedbackPriorityV2Config(
            max_recency_age_seconds=d("0.000000"),
        )


def test_build_validation_rejects_wrong_types_duplicates_and_bad_times() -> None:
    module = api()

    with pytest.raises(ValueError, match="outcome_items must be an iterable"):
        module.build_team_specialist_outcome_feedback_priority_v2(
            object(),
            generated_at=datetime(2026, 7, 7, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="outcome items must be TeamSpecialistOutcomeFeedbackPriorityV2Input",
    ):
        module.build_team_specialist_outcome_feedback_priority_v2(
            [object()],
            generated_at=datetime(2026, 7, 7, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_outcome_feedback_priority_v2(
            [outcome()],
            generated_at=datetime(2026, 7, 7),
        )
    with pytest.raises(ValueError, match="duplicate identities"):
        module.build_team_specialist_outcome_feedback_priority_v2(
            [outcome(), outcome()],
            generated_at=datetime(2026, 7, 7, tzinfo=UTC),
        )


def test_validation_digests_reject_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="row_digest must match row fields"):
        replace(report.rows[0], row_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_priority_score=d("0.400000"))


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
            outcome(team_id=f"{term}_value")
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("example", {f"{term}_key": "safe"})
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("example", {"safe_key": f"{term}_value"})


def test_report_revalidates_row_sorting_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by priority score and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="priority counts must match rows"):
        replace(report, high_priority_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match priority_status"):
        replace(report, reason_codes=("outcome_feedback_priority_medium_rows",))


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
    assert not any(
        fragment in name.lower()
        for name in module.__all__
        for fragment in unsafe_fragments
    )
    assert_no_float_values([imports, call_names, attribute_names])
