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
    / "team_specialist_event_coverage_heatmap_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_event_coverage_heatmap_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sample(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "event_category": "election",
        "specialist_id": "election_specialist",
        "open_backlog_count": d("1"),
        "calibration_quality_score": d("0.900000"),
        "source_family_count": d("4"),
        "recent_error": d("0.050000"),
        "upcoming_event_count": d("2"),
    }
    values.update(overrides)
    return module.TeamSpecialistEventCoverageHeatmapV2Input(**values)


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
            sample(team_id="alpha_specialists"),
            sample(
                team_id="beta_specialists",
                event_category="sports",
                specialist_id="sports_specialist",
                open_backlog_count=d("5"),
                calibration_quality_score=d("0.650000"),
                source_family_count=d("2"),
                recent_error=d("0.200000"),
                upcoming_event_count=d("5"),
            ),
            sample(
                team_id="gamma_specialists",
                event_category="crypto",
                specialist_id=None,
                open_backlog_count=d("10"),
                calibration_quality_score=d("0.350000"),
                source_family_count=d("1"),
                recent_error=d("0.600000"),
                upcoming_event_count=d("8"),
            ),
        )
    return module.build_team_specialist_event_coverage_heatmap_v2(
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


def test_builds_ranked_decimal_event_coverage_heatmap_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.heatmap_status == "blocked"
    assert report.row_count == d("3")
    assert report.category_count == d("3")
    assert report.pass_row_count == d("1")
    assert report.watch_row_count == d("1")
    assert report.blocked_row_count == d("1")
    assert report.average_heatmap_score == d("0.595833")
    assert report.max_backlog_pressure_count == d("10")
    assert report.max_upcoming_event_count == d("8")
    assert report.reason_codes == (
        "event_coverage_heatmap_blocked_rows",
        "event_coverage_heatmap_watch_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.event_category for row in rows) == ("election", "sports", "crypto")
    assert tuple(row.heatmap_score for row in rows) == (
        d("0.932500"),
        d("0.687500"),
        d("0.167500"),
    )
    assert tuple(row.row_status for row in rows) == ("pass", "watch", "blocked")
    assert rows[0].coverage_score == d("1.000000")
    assert rows[0].backlog_pressure_score == d("0.900000")
    assert rows[0].source_family_coverage_score == d("1.000000")
    assert rows[0].recent_error_score == d("0.950000")
    assert rows[0].upcoming_event_load_score == d("0.750000")

    payload = report.payload
    assert payload["row_count"] == "3"
    assert payload["average_heatmap_score"] == "0.595833"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["heatmap_score"] == "0.932500"
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_heatmap_is_report_only_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.heatmap_status == "blocked"
    assert report.row_count == d("0")
    assert report.category_count == d("0")
    assert report.average_heatmap_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("event_coverage_heatmap_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistEventCoverageHeatmapV2Config()
    item = sample()
    report = build_report(item)
    row = report.rows[0]

    decimal_fields = {
        "coverage_weight",
        "backlog_pressure_weight",
        "calibration_quality_weight",
        "source_family_coverage_weight",
        "recent_error_weight",
        "upcoming_event_load_weight",
        "min_source_family_count",
        "backlog_blocked_floor",
        "upcoming_event_blocked_floor",
        "pass_score_floor",
        "watch_score_floor",
        "open_backlog_count",
        "calibration_quality_score",
        "source_family_count",
        "recent_error",
        "upcoming_event_count",
        "rank",
        "coverage_score",
        "backlog_pressure_score",
        "source_family_coverage_score",
        "recent_error_score",
        "upcoming_event_load_score",
        "heatmap_score",
        "row_count",
        "category_count",
        "pass_row_count",
        "watch_row_count",
        "blocked_row_count",
        "average_heatmap_score",
        "max_backlog_pressure_count",
        "max_upcoming_event_count",
    }

    for frozen_item in (config, item, row, report):
        assert frozen_item.paper_only is True
        assert frozen_item.report_only is True
        assert frozen_item.readonly is True
        with pytest.raises(FrozenInstanceError):
            frozen_item.readonly = False  # type: ignore[misc]
        for field in fields(frozen_item):
            if field.name in decimal_fields:
                assert type(getattr(frozen_item, field.name)) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "open_backlog_count",
            _DecimalSubclass("1"),
            "open_backlog_count must be exactly Decimal",
        ),
        (
            "calibration_quality_score",
            d("1.000001"),
            "calibration_quality_score must be <= 1.000000",
        ),
        (
            "recent_error",
            d("0.0500004"),
            "recent_error must use six decimal places or fewer",
        ),
        (
            "source_family_count",
            Decimal("NaN"),
            "source_family_count must be finite",
        ),
        (
            "upcoming_event_count",
            d("1.5"),
            "upcoming_event_count must be an integral Decimal",
        ),
        (
            "open_backlog_count",
            d("-1"),
            "open_backlog_count must be >= 0.000000",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        sample(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="coverage_weight must be exactly Decimal"):
        module.TeamSpecialistEventCoverageHeatmapV2Config(coverage_weight=0)
    with pytest.raises(ValueError, match="heatmap weights must sum to 1.000000"):
        module.TeamSpecialistEventCoverageHeatmapV2Config(
            source_family_coverage_weight=d("0.160000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed"):
        module.TeamSpecialistEventCoverageHeatmapV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistEventCoverageHeatmapV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_duplicates_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="coverage_inputs must be an iterable"):
        module.build_team_specialist_event_coverage_heatmap_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="coverage inputs must be TeamSpecialistEventCoverageHeatmapV2Input",
    ):
        module.build_team_specialist_event_coverage_heatmap_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate team/category keys"):
        build_report(sample(), sample())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_event_coverage_heatmap_v2(
            [sample()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        sample(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_heatmap_score=d("0.600000"))


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
            sample(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_row_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match heatmap_status"):
        replace(report, reason_codes=("event_coverage_heatmap_passed",))


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
