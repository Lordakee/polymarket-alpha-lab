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
    / "team_specialist_review_quality_score.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_review_quality_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-review-quality-score-test",
        "evidence_completeness_weight": d("0.300000"),
        "calibration_weight": d("0.300000"),
        "correction_rate_weight": d("0.200000"),
        "fresh_review_weight": d("0.100000"),
        "gap_resolution_weight": d("0.100000"),
        "min_pass_quality_score": d("0.850000"),
        "min_watch_quality_score": d("0.650000"),
        "min_reviewed_case_count": d("3"),
        "max_pass_stale_review_ratio": d("0.200000"),
        "max_watch_stale_review_ratio": d("0.400000"),
        "max_pass_unresolved_gap_ratio": d("0.150000"),
        "max_watch_unresolved_gap_ratio": d("0.350000"),
    }
    values.update(overrides)
    return module.TeamSpecialistReviewQualityScoreConfig(**values)


def review_input(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "reviewer_alpha",
        "reviewed_case_count": d("12"),
        "evidence_completeness_score": d("0.900000"),
        "calibration_score": d("0.900000"),
        "correction_rate_score": d("0.900000"),
        "stale_review_ratio": d("0.050000"),
        "unresolved_gap_ratio": d("0.050000"),
    }
    values.update(overrides)
    return module.TeamSpecialistReviewQualityInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_review_quality_score(
        items,
        config=cfg if cfg is not None else config(),
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


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "market_id",
        "candidate_id",
        "market_slug",
        "market_question",
        "question",
        "http://",
        "https://",
        "source_ref",
        "source_refs",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position-sizing",
        "position_sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_contract() -> None:
    module = api()

    assert module.DEFAULT_TEAM_SPECIALIST_REVIEW_QUALITY_SCORE_CONFIG_VERSION == (
        "team-specialist-review-quality-score"
    )
    assert module.SPECIALIST_REVIEW_QUALITY_SCORE_FACTORS == (
        "evidence_completeness",
        "calibration",
        "correction_rate",
        "fresh_review",
        "gap_resolution",
    )
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_REVIEW_QUALITY_SCORE_CONFIG_VERSION",
        "SPECIALIST_REVIEW_QUALITY_SCORE_FACTORS",
        "TeamSpecialistReviewQualityScoreConfig",
        "TeamSpecialistReviewQualityInput",
        "TeamSpecialistReviewQualityRow",
        "TeamSpecialistReviewQualityReport",
        "build_team_specialist_review_quality_score",
        "team_specialist_review_quality_score_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.TeamSpecialistReviewQualityScoreConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_high_quality_specialist_reviews_pass_with_deterministic_rows() -> None:
    report = build_report(
        review_input(team_id="zeta_specialists", specialist_id="reviewer_z"),
        review_input(
            team_id="alpha_specialists",
            specialist_id="reviewer_a",
            evidence_completeness_score=d("0.950000"),
            calibration_score=d("0.900000"),
            correction_rate_score=d("0.850000"),
            stale_review_ratio=d("0.100000"),
            unresolved_gap_ratio=d("0.050000"),
        ),
    )

    assert report.report_status == "pass"
    assert report.specialist_count == d("2")
    assert report.pass_count == d("2")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.pass_ratio == d("1.000000")
    assert report.average_specialist_review_quality_score == d("0.910000")
    assert report.reason_codes == ("specialist_review_quality_report_pass",)
    assert tuple(row.team_id for row in report.rows) == (
        "alpha_specialists",
        "zeta_specialists",
    )
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"))
    assert tuple(row.specialist_review_quality_score for row in report.rows) == (
        d("0.910000"),
        d("0.910000"),
    )
    assert tuple(row.status for row in report.rows) == ("pass", "pass")
    assert report.rows[0].reason_codes == ("specialist_review_quality_row_pass",)


def test_low_quality_specialist_review_blocks() -> None:
    report = build_report(
        review_input(
            reviewed_case_count=d("1"),
            evidence_completeness_score=d("0.400000"),
            calibration_score=d("0.500000"),
            correction_rate_score=d("0.400000"),
            stale_review_ratio=d("0.600000"),
            unresolved_gap_ratio=d("0.500000"),
        ),
    )

    row = report.rows[0]
    assert row.specialist_review_quality_score == d("0.440000")
    assert row.status == "block"
    assert row.reason_codes == (
        "specialist_review_quality_insufficient_review_volume",
        "specialist_review_quality_score_below_watch",
        "specialist_review_quality_stale_review_ratio_above_watch",
        "specialist_review_quality_unresolved_gap_ratio_above_watch",
    )
    assert report.report_status == "block"
    assert report.specialist_count == d("1")
    assert report.block_count == d("1")
    assert report.reason_codes == (
        "specialist_review_quality_report_block_rows",
        "specialist_review_quality_report_average_below_watch",
    )


def test_stale_review_ratio_watches_otherwise_high_quality_reviews() -> None:
    report = build_report(
        review_input(
            evidence_completeness_score=d("0.950000"),
            calibration_score=d("0.950000"),
            correction_rate_score=d("0.950000"),
            stale_review_ratio=d("0.300000"),
            unresolved_gap_ratio=d("0.050000"),
        ),
    )

    row = report.rows[0]
    assert row.specialist_review_quality_score == d("0.925000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "specialist_review_quality_stale_review_ratio_above_pass",
    )
    assert report.report_status == "watch"
    assert report.watch_count == d("1")
    assert report.reason_codes == ("specialist_review_quality_report_watch_rows",)


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: review_input(evidence_completeness_score=_DecimalSubclass("0.900000")),
            "evidence_completeness_score must be exactly Decimal",
        ),
        (
            lambda: review_input(reviewed_case_count=12),
            "reviewed_case_count must be exactly Decimal",
        ),
        (
            lambda: config(evidence_completeness_weight=0.3),
            "evidence_completeness_weight must be exactly Decimal",
        ),
        (
            lambda: review_input(stale_review_ratio=d("0.1000001")),
            "stale_review_ratio must use six decimal places or fewer",
        ),
    ),
)
def test_decimal_exact_type_validation_rejects_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_public_payload_rejects_leaky_identifiers_and_live_surface_terms() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        review_input(team_id="https://example.com/market/path")

    with pytest.raises(ValueError, match="unsafe public payload"):
        review_input(specialist_id="trade_signal")

    report = build_report(review_input())
    payload = dict(report.payload)
    payload["market_id"] = "abc123"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.team_specialist_review_quality_score_payload(payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = review_input()
    report = build_report(item)
    row = report.rows[0]

    for value in (cfg, item, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistReviewQualityScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_is_decimal_stringed_deterministic_and_status_limited() -> None:
    left = review_input(team_id="left_team", specialist_id="reviewer_left")
    right = review_input(team_id="right_team", specialist_id="reviewer_right")

    report_a = build_report(right, left)
    report_b = build_report(left, right)

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.payload["specialist_count"] == "2"
    assert report_a.payload["rows"][0]["rank"] == "1"
    assert report_a.payload["rows"][0]["specialist_review_quality_score"] == "0.910000"
    assert_no_float_values(report_a.payload)

    statuses = {report_a.report_status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in statuses
    assert "ready" not in statuses
    assert "matched" not in statuses
    assert "supported" not in statuses


def test_report_consistency_and_digest_validation_reject_tampering() -> None:
    module = api()
    report = build_report(review_input())

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0"))

    with pytest.raises(ValueError, match="average_specialist_review_quality_score must match rows"):
        replace(report, average_specialist_review_quality_score=d("0.500000"))

    payload = dict(report.payload)
    payload["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.team_specialist_review_quality_score_payload(payload)


def test_module_stays_report_only_without_network_or_persistence_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])

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
        },
    )
