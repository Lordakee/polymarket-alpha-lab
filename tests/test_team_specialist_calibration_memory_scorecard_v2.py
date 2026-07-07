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
    / "team_specialist_calibration_memory_scorecard_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_calibration_memory_scorecard_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "domain_id": "macro_rates",
        "domain_calibration_score": d("0.900000"),
        "recent_forecast_error": d("0.050000"),
        "evidence_quality_score": d("0.850000"),
        "source_diversity_score": d("0.800000"),
        "stale_lesson_count": d("0"),
        "unresolved_postmortem_action_count": d("0"),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationMemoryV2Input(**values)


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
            memory(team_id="alpha_specialists"),
            memory(
                team_id="beta_specialists",
                domain_calibration_score=d("0.700000"),
                recent_forecast_error=d("0.180000"),
                evidence_quality_score=d("0.700000"),
                source_diversity_score=d("0.600000"),
                stale_lesson_count=d("1"),
                unresolved_postmortem_action_count=d("1"),
            ),
            memory(
                team_id="gamma_specialists",
                domain_calibration_score=d("0.400000"),
                recent_forecast_error=d("0.450000"),
                evidence_quality_score=d("0.300000"),
                source_diversity_score=d("0.250000"),
                stale_lesson_count=d("5"),
                unresolved_postmortem_action_count=d("3"),
            ),
        )
    return module.build_team_specialist_calibration_memory_scorecard_v2(
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


def test_builds_ranked_decimal_scorecard_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.scorecard_status == "blocked"
    assert report.team_count == d("3")
    assert report.pass_team_count == d("1")
    assert report.watch_team_count == d("1")
    assert report.blocked_team_count == d("1")
    assert report.average_calibration_memory_score == d("0.654250")
    assert report.top_calibration_memory_score == d("0.900000")
    assert report.bottom_calibration_memory_score == d("0.346250")
    assert report.reason_codes == (
        "team_specialist_memory_scorecard_blocked_rows",
        "team_specialist_memory_scorecard_watch_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.calibration_memory_score for row in rows) == (
        d("0.900000"),
        d("0.716500"),
        d("0.346250"),
    )
    assert tuple(row.memory_status for row in rows) == ("pass", "watch", "blocked")

    payload = report.payload
    assert payload["team_count"] == "3"
    assert payload["average_calibration_memory_score"] == "0.654250"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["calibration_memory_score"] == "0.900000"
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_scorecard_is_report_only_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.scorecard_status == "blocked"
    assert report.team_count == d("0")
    assert report.average_calibration_memory_score == d("0.000000")
    assert report.top_calibration_memory_score == d("0.000000")
    assert report.bottom_calibration_memory_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("team_specialist_memory_scorecard_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCalibrationMemoryScorecardV2Config()
    sample = memory()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "domain_calibration_weight",
                "recent_forecast_error_weight",
                "evidence_quality_weight",
                "source_diversity_weight",
                "stale_lessons_weight",
                "unresolved_postmortem_actions_weight",
                "max_stale_lesson_count",
                "max_unresolved_postmortem_action_count",
                "pass_score_floor",
                "watch_score_floor",
                "domain_calibration_score",
                "recent_forecast_error",
                "evidence_quality_score",
                "source_diversity_score",
                "stale_lesson_count",
                "unresolved_postmortem_action_count",
                "rank",
                "forecast_accuracy_score",
                "stale_lesson_score",
                "postmortem_action_score",
                "calibration_memory_score",
                "team_count",
                "pass_team_count",
                "watch_team_count",
                "blocked_team_count",
                "average_calibration_memory_score",
                "top_calibration_memory_score",
                "bottom_calibration_memory_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "domain_calibration_score",
            _DecimalSubclass("0.900000"),
            "domain_calibration_score must be exactly Decimal",
        ),
        (
            "recent_forecast_error",
            d("1.000001"),
            "recent_forecast_error must be <= 1.000000",
        ),
        (
            "evidence_quality_score",
            d("0.8500004"),
            "evidence_quality_score must use six decimal places or fewer",
        ),
        (
            "source_diversity_score",
            Decimal("NaN"),
            "source_diversity_score must be finite",
        ),
        (
            "stale_lesson_count",
            d("1.5"),
            "stale_lesson_count must be an integral Decimal",
        ),
        (
            "unresolved_postmortem_action_count",
            d("-1"),
            "unresolved_postmortem_action_count must be >= 0.000000",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        memory(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="domain_calibration_weight must be exactly Decimal"):
        module.TeamSpecialistCalibrationMemoryScorecardV2Config(
            domain_calibration_weight=0,
        )
    with pytest.raises(
        ValueError,
        match="scorecard weights must sum to 1.000000",
    ):
        module.TeamSpecialistCalibrationMemoryScorecardV2Config(
            source_diversity_weight=d("0.160000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed pass_score_floor"):
        module.TeamSpecialistCalibrationMemoryScorecardV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCalibrationMemoryScorecardV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_memories must be an iterable"):
        module.build_team_specialist_calibration_memory_scorecard_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="team memory items must be TeamSpecialistCalibrationMemoryV2Input",
    ):
        module.build_team_specialist_calibration_memory_scorecard_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_calibration_memory_scorecard_v2(
            [memory()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        memory(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_calibration_memory_score=d("0.650000"),
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
            memory(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            pass_team_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match scorecard_status"):
        replace(
            report,
            reason_codes=("team_specialist_memory_scorecard_passed",),
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
