from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_candidate_research_priority_rollup_dashboard"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 40, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    report_module = module()
    values = {
        "watch_priority_threshold": d("0.450000"),
        "min_evidence_freshness_score": d("0.250000"),
        "min_source_diversity_score": d("0.300000"),
        "max_cost_friction_score": d("0.750000"),
        "urgent_market_timing_threshold": d("0.800000"),
        "high_uncertainty_threshold": d("0.700000"),
    }
    values.update(overrides)
    return report_module.ResearchCandidateResearchPriorityRollupConfig(**values)


def candidate(**overrides: object) -> Any:
    report_module = module()
    values = {
        "summary_ref": "summary-alpha",
        "team_ref": "team-macro",
        "category_ref": "category-rates",
        "observed_at": OBSERVED_AT,
        "evidence_freshness_score": d("0.800000"),
        "source_diversity_score": d("0.750000"),
        "market_timing_score": d("0.300000"),
        "uncertainty_score": d("0.200000"),
        "cost_friction_score": d("0.100000"),
        "reason_codes": ("candidate_summary_ready",),
    }
    values.update(overrides)
    return report_module.ResearchCandidateResearchPriorityInput(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_research_candidate_research_priority_rollup_dashboard(
        items,
        config=config(),
        generated_at=generated_at,
    )


def test_rolls_up_priority_across_teams_with_public_safe_payload() -> None:
    report_module = module()
    report = build_report(
        candidate(),
        candidate(
            summary_ref="summary-beta",
            team_ref="team-macro",
            category_ref="category-policy",
            evidence_freshness_score=d("0.500000"),
            source_diversity_score=d("0.550000"),
            market_timing_score=d("0.850000"),
            uncertainty_score=d("0.650000"),
            cost_friction_score=d("0.200000"),
            reason_codes=("timing_window_open",),
        ),
        candidate(
            summary_ref="summary-gamma",
            team_ref="team-policy",
            category_ref="category-policy",
            evidence_freshness_score=d("0.150000"),
            source_diversity_score=d("0.250000"),
            market_timing_score=d("0.600000"),
            uncertainty_score=d("0.800000"),
            cost_friction_score=d("0.800000"),
            reason_codes=("evidence_refresh_needed",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.summary_count == d("3.000000")
    assert report.team_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.status == "block"
    assert report.top_summary_ref == "summary-gamma"
    assert report.top_team_ref == "team-policy"
    assert report.max_priority_score == d("0.682500")
    assert report.average_priority_score == d("0.551667")
    assert report.reason_codes == (
        "research_priority_block_present",
        "cost_friction_limit_present",
        "evidence_freshness_gap_present",
        "source_diversity_gap_present",
        "research_priority_watch_present",
    )
    assert report.public_summary == (
        "block: research queue has freshness diversity or cost gates to clear",
        "watch: prioritize timing and uncertainty follow-up",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.status, row.summary_ref, row.priority_score) for row in report.rows) == (
        ("block", "summary-gamma", d("0.682500")),
        ("watch", "summary-beta", d("0.665000")),
        ("pass", "summary-alpha", d("0.307500")),
    )
    assert report.rows[0].reason_codes == (
        "cost_friction_limit",
        "evidence_freshness_gap",
        "evidence_refresh_needed",
        "research_priority_block",
        "source_diversity_gap",
        "uncertainty_high",
    )
    assert report.rows[1].reason_codes == (
        "market_timing_pressure",
        "research_priority_watch",
        "timing_window_open",
    )
    assert tuple((team.team_ref, team.status, team.summary_count) for team in report.team_rollups) == (
        ("team-policy", "block", d("1.000000")),
        ("team-macro", "watch", d("2.000000")),
    )

    payload = report_module.research_candidate_research_priority_rollup_dashboard_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["summary_count"] == "3.000000"
    assert payload["team_rollups"][0]["max_priority_score"] == "0.682500"
    assert payload["rows"][0]["status"] == "block"
    assert payload["rows"][0]["priority_score"] == "0.682500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert report_module.validate_research_candidate_research_priority_rollup_dashboard_payload(
        payload,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_no_public_numeric(payload)
    assert_no_public_forbidden_terms(payload)


def test_empty_and_reordered_inputs_are_deterministic() -> None:
    empty = build_report()
    assert empty.summary_count == ZERO
    assert empty.team_count == ZERO
    assert empty.status == "pass"
    assert empty.top_summary_ref is None
    assert empty.top_team_ref is None
    assert empty.max_priority_score == ZERO
    assert empty.average_priority_score is None
    assert empty.reason_codes == ("research_priority_rollup_empty",)
    assert empty.rows == ()
    assert empty.team_rollups == ()

    left = build_report(
        candidate(summary_ref="summary-beta", team_ref="team-beta"),
        candidate(summary_ref="summary-alpha", team_ref="team-alpha"),
    )
    right = build_report(
        candidate(summary_ref="summary-alpha", team_ref="team-alpha"),
        candidate(summary_ref="summary-beta", team_ref="team-beta"),
    )
    assert left.derived_validation_digest == right.derived_validation_digest
    assert (
        module().research_candidate_research_priority_rollup_dashboard_payload(left)
        == module().research_candidate_research_priority_rollup_dashboard_payload(right)
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_hard() -> None:
    report_module = module()

    assert report_module.PUBLIC_STATUSES == ("pass", "watch", "block")
    assert report_module.__all__ == (
        "DEFAULT_RESEARCH_CANDIDATE_RESEARCH_PRIORITY_ROLLUP_DASHBOARD_CONFIG_VERSION",
        "PUBLIC_STATUSES",
        "ResearchCandidateResearchPriorityInput",
        "ResearchCandidateResearchPriorityRollupConfig",
        "ResearchCandidateResearchPriorityRollupDashboard",
        "ResearchCandidateResearchPriorityRow",
        "ResearchCandidateResearchPriorityTeamRollup",
        "build_research_candidate_research_priority_rollup_dashboard",
        "research_candidate_research_priority_rollup_dashboard_payload",
        "validate_research_candidate_research_priority_rollup_dashboard_payload",
    )
    for exported_name in report_module.__all__:
        exported = getattr(report_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report(candidate())
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = ZERO  # type: ignore[misc]

    for item in (config(), candidate(), report, *report.rows, *report.team_rollups):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not int
            assert type(value) is not float
            if field.name.endswith(("_count", "_score")):
                assert value is None or type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="evidence_freshness_score must be a Decimal"):
        candidate(evidence_freshness_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="market_timing_score must be a Decimal"):
        candidate(market_timing_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="uncertainty_score must use six decimal places"):
        candidate(uncertainty_score=d("0.80"))
    with pytest.raises(ValueError, match="watch_priority_threshold must be a Decimal"):
        config(watch_priority_threshold=0.45)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.ResearchCandidateResearchPriorityRow):
            pass


def test_validation_rejects_public_leaks_bad_statuses_duplicates_and_dates() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="summary_ref"):
        candidate(summary_ref="candidate-alpha")
    with pytest.raises(ValueError, match="unsafe public value"):
        candidate(reason_codes=("".join(("bu", "y")) + "_signal",))
    with pytest.raises(ValueError, match="duplicate summary_ref"):
        build_report(candidate(), candidate(team_ref="team-beta"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 40, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(candidate(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="status"):
        replace(build_report(candidate()).rows[0], status="blocked")

    payload = report_module.research_candidate_research_priority_rollup_dashboard_payload(
        build_report(candidate()),
    )
    bad_key_payload = dict(payload)
    bad_key_payload["".join(("wal", "let"))] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        report_module.validate_research_candidate_research_priority_rollup_dashboard_payload(
            bad_key_payload,
        )

    bad_value_payload = dict(payload)
    bad_value_payload["public_summary"] = ["".join(("rec", "ommend")) + " action"]
    with pytest.raises(ValueError, match="unsafe public"):
        report_module.validate_research_candidate_research_priority_rollup_dashboard_payload(
            bad_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["summary_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        report_module.validate_research_candidate_research_priority_rollup_dashboard_payload(
            numeric_payload,
        )


def test_module_omits_runtime_action_and_write_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_candidate_research_priority_rollup_dashboard.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "psycopg",
        "sqlalchemy",
        "private_key",
        "broker",
        "authorization",
        "database",
        "network",
    ):
        assert forbidden not in lowered

    for forbidden in (
        "".join(("wal", "let")),
        "".join(("au", "th")),
        "".join(("ord", "er")),
        "".join(("tra", "de")),
        "".join(("bu", "y")),
        "".join(("sel", "l")),
        "".join(("rec", "ommend")),
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}


def assert_no_public_numeric(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("float found in public payload")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError("int found in public payload")
    if isinstance(value, Decimal):
        raise AssertionError("Decimal found in public payload")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_public_numeric(nested)
    elif isinstance(value, list | tuple):
        for nested in value:
            assert_no_public_numeric(nested)


def assert_no_public_forbidden_terms(value: Any) -> None:
    forbidden = (
        "".join(("wal", "let")),
        "".join(("au", "th")),
        "".join(("ord", "er")),
        "".join(("tra", "de")),
        "".join(("bu", "y")),
        "".join(("sel", "l")),
        "".join(("rec", "ommend")),
    )
    if isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in forbidden):
            raise AssertionError(f"unsafe term in payload: {value!r}")
    elif isinstance(value, dict):
        for key, nested in value.items():
            assert_no_public_forbidden_terms(key)
            assert_no_public_forbidden_terms(nested)
    elif isinstance(value, list | tuple):
        for nested in value:
            assert_no_public_forbidden_terms(nested)
