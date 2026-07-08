from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_memory_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object):
    module = api()
    values = {
        "domain_group": "macro_rates",
        "specialist_group": "rates_memory",
        "domain_memory_count": d("10.000000"),
        "domain_target_count": d("10.000000"),
        "stale_memory_age_seconds": d("86400.000000"),
        "calibration_drift_score": d("0.030000"),
        "source_coverage_ratio": d("0.900000"),
        "pending_review_count": d("2.000000"),
        "review_capacity_count": d("10.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistMemoryGapObservation(**values)


def build_report(*rows: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    return module.build_research_team_specialist_memory_gap_report(
        rows,
        generated_at=generated_at,
        **overrides,
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


def test_report_scores_public_specialist_memory_gaps_across_statuses() -> None:
    report = build_report(
        observation(),
        observation(
            domain_group="policy_regulation",
            specialist_group="policy_memory",
            domain_memory_count=d("7.000000"),
            stale_memory_age_seconds=d("3456000.000000"),
            calibration_drift_score=d("0.100000"),
            source_coverage_ratio=d("0.700000"),
            pending_review_count=d("9.000000"),
        ),
        observation(
            domain_group="sports_soccer",
            specialist_group="soccer_memory",
            domain_memory_count=d("5.000000"),
            stale_memory_age_seconds=d("6048000.000000"),
            calibration_drift_score=d("0.200000"),
            source_coverage_ratio=d("0.400000"),
            pending_review_count=d("12.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.public_status == "block"
    assert report.observation_count == d("3.000000")
    assert report.domain_group_count == d("3.000000")
    assert report.specialist_group_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.domain_coverage_gap_count == d("2.000000")
    assert report.stale_memory_gap_count == d("2.000000")
    assert report.calibration_drift_gap_count == d("2.000000")
    assert report.source_coverage_gap_count == d("2.000000")
    assert report.review_capacity_gap_count == d("2.000000")
    assert report.average_domain_coverage_ratio == d("0.733333")
    assert report.max_stale_memory_age_seconds == d("6048000.000000")
    assert report.max_calibration_drift_score == d("0.200000")
    assert report.average_source_coverage_ratio == d("0.666667")
    assert report.weighted_review_capacity_utilization == d("0.766667")
    assert report.reason_codes == (
        "specialist_memory_gap_block_present",
        "specialist_memory_gap_watch_present",
        "domain_coverage_gap_present",
        "stale_memory_gap_present",
        "calibration_drift_gap_present",
        "source_coverage_gap_present",
        "review_capacity_gap_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.public_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )

    blocked = report.rows[0]
    assert blocked.domain_group == "sports_soccer"
    assert blocked.domain_coverage_ratio == d("0.500000")
    assert blocked.review_capacity_utilization == d("1.200000")
    assert blocked.reason_codes == (
        "domain_coverage_block",
        "stale_memory_block",
        "calibration_drift_block",
        "source_coverage_block",
        "review_capacity_block",
    )

    watched = report.rows[1]
    assert watched.domain_group == "policy_regulation"
    assert watched.domain_coverage_ratio == d("0.700000")
    assert watched.review_capacity_utilization == d("0.900000")
    assert watched.reason_codes == (
        "domain_coverage_watch",
        "stale_memory_watch",
        "calibration_drift_watch",
        "source_coverage_watch",
        "review_capacity_watch",
    )

    passed = report.rows[2]
    assert passed.domain_group == "macro_rates"
    assert passed.reason_codes == ("specialist_memory_gap_clear",)

    assert report.reason_code_counts[0].reason_code == "domain_coverage_block"
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.333333")


def test_report_handles_empty_pass_and_watch_rollups() -> None:
    empty = build_report()
    assert empty.public_status == "pass"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("specialist_memory_gap_no_observations",)

    passed = build_report(observation())
    assert passed.public_status == "pass"
    assert passed.rows[0].public_status == "pass"
    assert passed.reason_codes == ("specialist_memory_gap_report_clear",)

    watched = build_report(
        observation(
            domain_memory_count=d("7.000000"),
            stale_memory_age_seconds=d("3456000.000000"),
        ),
    )
    assert watched.public_status == "watch"
    assert watched.rows[0].public_status == "watch"


def test_payload_uses_decimal_strings_public_lists_and_stable_digest() -> None:
    module = api()
    row_a = observation(domain_group="macro_rates", specialist_group="rates_memory")
    row_b = observation(
        domain_group="policy_regulation",
        specialist_group="policy_memory",
        domain_memory_count=d("7.000000"),
        stale_memory_age_seconds=d("3456000.000000"),
        calibration_drift_score=d("0.100000"),
        source_coverage_ratio=d("0.700000"),
        pending_review_count=d("9.000000"),
    )

    first = build_report(row_b, row_a)
    second = build_report(row_a, row_b)
    payload = module.research_team_specialist_memory_gap_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first.payload == payload
    assert first.payload_digest == second.payload_digest
    assert payload["payload_digest"] == first.payload_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["average_domain_coverage_ratio"] == "0.850000"
    assert payload["rows"][0]["domain_group"] == "policy_regulation"
    assert payload["rows"][0]["domain_coverage_ratio"] == "0.700000"
    assert payload["rows"][0]["reason_codes"] == [
        "domain_coverage_watch",
        "stale_memory_watch",
        "calibration_drift_watch",
        "source_coverage_watch",
        "review_capacity_watch",
    ]
    assert '"0.850000"' in encoded
    assert_no_float_values(payload)


def test_public_numeric_dataclass_fields_are_decimal_only_and_statuses_exact() -> None:
    module = api()
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")

    numeric_fields = {
        "min_pass_domain_coverage_ratio",
        "min_watch_domain_coverage_ratio",
        "stale_memory_watch_age_seconds",
        "stale_memory_block_age_seconds",
        "calibration_watch_drift_score",
        "calibration_block_drift_score",
        "min_pass_source_coverage_ratio",
        "min_watch_source_coverage_ratio",
        "review_watch_utilization",
        "review_block_utilization",
        "domain_memory_count",
        "domain_target_count",
        "stale_memory_age_seconds",
        "calibration_drift_score",
        "source_coverage_ratio",
        "pending_review_count",
        "review_capacity_count",
        "domain_coverage_ratio",
        "review_capacity_utilization",
        "count",
        "row_ratio",
        "observation_count",
        "domain_group_count",
        "specialist_group_count",
        "pass_count",
        "watch_count",
        "block_count",
        "domain_coverage_gap_count",
        "stale_memory_gap_count",
        "calibration_drift_gap_count",
        "source_coverage_gap_count",
        "review_capacity_gap_count",
        "average_domain_coverage_ratio",
        "max_stale_memory_age_seconds",
        "max_calibration_drift_score",
        "average_source_coverage_ratio",
        "weighted_review_capacity_utilization",
    }
    for cls in (
        module.ResearchTeamSpecialistMemoryGapConfig,
        module.ResearchTeamSpecialistMemoryGapObservation,
        module.ResearchTeamSpecialistMemoryGapRow,
        module.ResearchTeamSpecialistMemoryGapReasonCodeCount,
        module.ResearchTeamSpecialistMemoryGapReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_types_ranges_raw_identifiers_flags_and_mutation() -> None:
    module = api()

    with pytest.raises(ValueError, match="domain_group must be exactly str"):
        observation(domain_group=_StringSubclass("macro_rates"))

    with pytest.raises(ValueError, match="domain_memory_count must be a Decimal"):
        observation(domain_memory_count=10)

    with pytest.raises(ValueError, match="calibration_drift_score must be exactly Decimal"):
        observation(calibration_drift_score=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="domain_target_count must be positive"):
        observation(domain_target_count=d("0.000000"))

    with pytest.raises(ValueError, match="domain_memory_count must be nonnegative"):
        observation(domain_memory_count=d("-0.000001"))

    with pytest.raises(ValueError, match="domain_memory_count must not exceed"):
        observation(domain_memory_count=d("11.000000"))

    with pytest.raises(ValueError, match="source_coverage_ratio must be between 0 and 1"):
        observation(source_coverage_ratio=d("1.000001"))

    with pytest.raises(ValueError, match="required decimal precision"):
        observation(calibration_drift_score=d("0.3333333"))

    with pytest.raises(ValueError, match="public-safe aggregate label"):
        observation(domain_group="event_id_hidden")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(build_report(observation()), readonly=False)

    with pytest.raises(ValueError, match="public_status must be one of pass, watch, block"):
        module.ResearchTeamSpecialistMemoryGapRow(
            domain_group="macro_rates",
            specialist_group="rates_memory",
            domain_memory_count=d("10.000000"),
            domain_target_count=d("10.000000"),
            domain_coverage_ratio=d("1.000000"),
            stale_memory_age_seconds=d("86400.000000"),
            calibration_drift_score=d("0.030000"),
            source_coverage_ratio=d("0.900000"),
            pending_review_count=d("2.000000"),
            review_capacity_count=d("10.000000"),
            review_capacity_utilization=d("0.200000"),
            public_status="ready",
            reason_codes=("specialist_memory_gap_clear",),
        )

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]


def test_module_scope_is_report_only_public_safe_with_no_io_or_action_language() -> None:
    module = api()
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "raw_event",
        "raw_market",
        "raw_source",
        "slug",
        "url",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live execution",
        "execution",
        "database",
        "network",
        "requests",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "open(",
        "recommend",
        "recommendation",
        "position sizing",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    for cls in (
        module.ResearchTeamSpecialistMemoryGapConfig,
        module.ResearchTeamSpecialistMemoryGapObservation,
        module.ResearchTeamSpecialistMemoryGapRow,
        module.ResearchTeamSpecialistMemoryGapReasonCodeCount,
        module.ResearchTeamSpecialistMemoryGapReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
