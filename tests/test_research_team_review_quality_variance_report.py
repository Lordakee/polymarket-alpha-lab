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
    / "research_team_review_quality_variance_report.py"
)
NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_quality_variance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-review-quality-variance-report-test",
        "min_pass_calibration_score": d("0.800000"),
        "min_watch_calibration_score": d("0.600000"),
        "min_pass_evidence_completeness_score": d("0.850000"),
        "min_watch_evidence_completeness_score": d("0.650000"),
        "max_pass_contradiction_miss_rate": d("0.050000"),
        "max_watch_contradiction_miss_rate": d("0.250000"),
        "max_pass_review_latency_hours": d("12.000000"),
        "max_watch_review_latency_hours": d("36.000000"),
        "max_pass_memory_age_days": d("7.000000"),
        "max_watch_memory_age_days": d("21.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewQualityVarianceConfig(**values)


def snapshot(**overrides: object):
    module = api()
    values = {
        "specialist_team_key": "macro_review",
        "reviewed_packet_count": d("20"),
        "calibrated_packet_count": d("18"),
        "evidence_required_count": d("40"),
        "evidence_complete_count": d("38"),
        "contradiction_flag_count": d("5"),
        "contradiction_resolved_count": d("5"),
        "mean_review_latency_hours": d("6.000000"),
        "mean_memory_age_days": d("2.000000"),
    }
    values.update(overrides)
    return module.SpecialistTeamReviewQualitySnapshot(**values)


def build_report(
    *items: object,
    cfg=None,
    generated_at: datetime = NOW,
):
    module = api()
    return module.build_research_team_review_quality_variance_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected non-Decimal numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
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


def assert_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "event",
        "market",
        "source",
        "question",
        "slug",
        "url",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_variance_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_VARIANCE_CONFIG_VERSION == (
        "research-team-review-quality-variance-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_VARIANCE_CONFIG_VERSION",
        "ResearchTeamReviewQualityReasonCodeCount",
        "ResearchTeamReviewQualityVarianceConfig",
        "ResearchTeamReviewQualityVarianceReport",
        "ResearchTeamReviewQualityVarianceRow",
        "SpecialistTeamReviewQualitySnapshot",
        "build_research_team_review_quality_variance_report",
        "research_team_review_quality_variance_report_digest",
        "research_team_review_quality_variance_report_payload",
    )

    for public_type in (
        module.ResearchTeamReviewQualityReasonCodeCount,
        module.ResearchTeamReviewQualityVarianceConfig,
        module.ResearchTeamReviewQualityVarianceReport,
        module.ResearchTeamReviewQualityVarianceRow,
        module.SpecialistTeamReviewQualitySnapshot,
    ):
        assert is_dataclass(public_type)
        defaults = {field.name: field.default for field in fields(public_type)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True


def test_aggregates_review_quality_variance_into_pass_watch_block_rows() -> None:
    report = build_report(
        snapshot(specialist_team_key="macro_review"),
        snapshot(
            specialist_team_key="policy_review",
            reviewed_packet_count=d("10"),
            calibrated_packet_count=d("7"),
            evidence_required_count=d("20"),
            evidence_complete_count=d("15"),
            contradiction_flag_count=d("4"),
            contradiction_resolved_count=d("3"),
            mean_review_latency_hours=d("20.000000"),
            mean_memory_age_days=d("12.000000"),
        ),
        snapshot(
            specialist_team_key="sports_review",
            reviewed_packet_count=d("5"),
            calibrated_packet_count=d("2"),
            evidence_required_count=d("10"),
            evidence_complete_count=d("5"),
            contradiction_flag_count=d("3"),
            contradiction_resolved_count=d("1"),
            mean_review_latency_hours=d("72.000000"),
            mean_memory_age_days=d("45.000000"),
        ),
    )

    assert report.status == "block"
    assert report.team_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.mean_calibration_score == d("0.666667")
    assert report.mean_evidence_completeness_score == d("0.733333")
    assert report.mean_contradiction_handling_score == d("0.694444")
    assert report.mean_review_latency_hours == d("32.666667")
    assert report.mean_memory_age_days == d("19.666667")
    assert report.mean_quality_variance_score == d("0.360338")
    assert report.max_quality_variance_score == d("0.811966")
    assert report.reason_codes == (
        "review_quality_variance_report_block_rows",
        "review_quality_variance_report_watch_rows",
    )

    assert tuple(row.specialist_team_key for row in report.rows) == (
        "macro_review",
        "policy_review",
        "sports_review",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].quality_variance_score == d("0.000000")
    assert report.rows[1].calibration_score == d("0.700000")
    assert report.rows[1].evidence_completeness_score == d("0.750000")
    assert report.rows[1].contradiction_miss_rate == d("0.250000")
    assert report.rows[1].quality_variance_score == d("0.269048")
    assert report.rows[2].contradiction_handling_score == d("0.333333")
    assert report.rows[2].quality_variance_score == d("0.811966")
    assert report.rows[2].reason_codes == (
        "review_quality_variance_block",
        "calibration_low",
        "evidence_completeness_low",
        "contradiction_handling_low",
        "review_latency_slow",
        "memory_freshness_stale",
    )


def test_empty_input_blocks_as_report_only_public_diagnostic() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.team_count == d("0.000000")
    assert report.block_count == d("1.000000")
    assert report.rows == ()
    assert report.reason_codes == ("review_quality_variance_empty_input",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: snapshot(reviewed_packet_count=20),
            "reviewed_packet_count must be exactly Decimal",
        ),
        (
            lambda: snapshot(mean_memory_age_days=_DecimalSubclass("2.000000")),
            "mean_memory_age_days must be exactly Decimal",
        ),
        (
            lambda: snapshot(mean_review_latency_hours=d("6.0000001")),
            "mean_review_latency_hours must use six decimal places or fewer",
        ),
        (
            lambda: snapshot(reviewed_packet_count=d("20.500000")),
            "reviewed_packet_count must be a whole number",
        ),
        (
            lambda: build_report(snapshot(), generated_at=datetime(2026, 7, 8, 12, 0)),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_strict_type_validation_rejects_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_hard_flags_are_enforced_and_public_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = snapshot()
    report = build_report(item)
    row = report.rows[0]
    count = report.reason_code_counts[0]

    for value in (cfg, item, row, count, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamReviewQualityVarianceConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_digest_are_deterministic_decimal_stringed_and_status_limited() -> None:
    left = snapshot(specialist_team_key="policy_review")
    right = snapshot(specialist_team_key="macro_review")

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload_a = report_a.payload
    payload_b = report_b.payload

    assert payload_a == payload_b
    assert report_a.public_digest == report_b.public_digest
    assert report_a.public_digest == payload_a["public_digest"]
    assert report_a.public_digest == api().research_team_review_quality_variance_report_digest(
        report_a,
    )
    assert payload_a["team_count"] == "2.000000"
    assert payload_a["rows"][0]["quality_variance_score"] == "0.000000"
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert_no_float_or_int_values(payload_a)
    json.dumps(payload_a, sort_keys=True)

    statuses = {report_a.status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in statuses
    assert "ready" not in statuses


def test_public_payload_rejects_leaky_identifiers_and_execution_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        snapshot(specialist_team_key="raw_event_bucket")

    with pytest.raises(ValueError, match="unsafe public value"):
        snapshot(specialist_team_key="market_source_review")

    report = build_report(snapshot())
    payload = dict(report.payload)
    payload["market_reference"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_review_quality_variance_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_reference"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_review_quality_variance_report_payload(row_payload)

    assert_payload_has_no_forbidden_surface(report.payload)


def test_report_consistency_and_digest_validation_reject_tampering() -> None:
    module = api()
    report = build_report(snapshot())

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0.000000"))

    with pytest.raises(ValueError, match="mean_calibration_score must match rows"):
        replace(report, mean_calibration_score=d("0.500000"))

    payload = dict(report.payload)
    payload["status"] = "watch"
    with pytest.raises(ValueError, match="public_digest must match payload fields"):
        module.research_team_review_quality_variance_report_payload(payload)


def test_module_stays_pure_report_only_without_io_or_execution_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_names.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "request",
            "post",
            "put",
            "delete",
            "execute",
            "executemany",
        },
    )
