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
    / "team_specialist_evidence_review_coverage_score.py"
)
GENERATED_AT = datetime(2026, 7, 7, 13, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_evidence_review_coverage_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "team-specialist-evidence-review-coverage-score-test",
        "evidence_type_weight": d("0.300000"),
        "review_step_weight": d("0.300000"),
        "evidence_independence_weight": d("0.200000"),
        "cross_review_weight": d("0.200000"),
        "unresolved_gap_penalty_weight": d("0.200000"),
        "min_evidence_type_pass_ratio": d("0.800000"),
        "min_evidence_type_watch_ratio": d("0.500000"),
        "min_review_step_pass_ratio": d("0.800000"),
        "min_review_step_watch_ratio": d("0.500000"),
        "min_evidence_independence_pass_ratio": d("0.700000"),
        "min_evidence_independence_watch_ratio": d("0.400000"),
        "min_cross_review_pass_ratio": d("0.600000"),
        "min_cross_review_watch_ratio": d("0.300000"),
        "max_unresolved_gap_pass_ratio": d("0.200000"),
        "max_unresolved_gap_watch_ratio": d("0.400000"),
        "pass_score_floor": d("0.800000"),
        "watch_score_floor": d("0.600000"),
    }
    values.update(overrides)
    return module.TeamSpecialistEvidenceReviewCoverageScoreConfig(**values)


def coverage_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "team_id": "alpha_specialists",
        "specialist_id": "reviewer_alpha",
        "category_id": "category_macro",
        "required_evidence_type_count": d("4.000000"),
        "covered_evidence_type_count": d("4.000000"),
        "required_review_step_count": d("5.000000"),
        "completed_review_step_count": d("5.000000"),
        "independent_evidence_ratio": d("0.800000"),
        "cross_review_ratio": d("0.750000"),
        "unresolved_gap_ratio": d("0.100000"),
    }
    values.update(overrides)
    return module.TeamSpecialistEvidenceReviewCoverageScoreInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_evidence_review_coverage_score_report(
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
        "market",
        "candidate",
        "slug",
        "question",
        "source",
        "source_ref",
        "source_refs",
        "source_text",
        "http://",
        "https://",
        "url",
        "text",
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
        "position",
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

    assert module.DEFAULT_TEAM_SPECIALIST_EVIDENCE_REVIEW_COVERAGE_SCORE_CONFIG_VERSION == (
        "team-specialist-evidence-review-coverage-score-v1"
    )
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_EVIDENCE_REVIEW_COVERAGE_SCORE_CONFIG_VERSION",
        "TeamSpecialistEvidenceReviewCoverageScoreConfig",
        "TeamSpecialistEvidenceReviewCoverageScoreInput",
        "TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount",
        "TeamSpecialistEvidenceReviewCoverageScoreRow",
        "TeamSpecialistEvidenceReviewCoverageScoreReport",
        "build_team_specialist_evidence_review_coverage_score_report",
        "team_specialist_evidence_review_coverage_score_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.TeamSpecialistEvidenceReviewCoverageScoreConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_complete_evidence_and_review_coverage_passes() -> None:
    report = build_report(coverage_input())

    assert report.report_status == "pass"
    assert report.item_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_review_coverage_score == d("0.890000")
    assert report.minimum_review_coverage_score == d("0.890000")
    assert report.reason_code_counts == (
        api().TeamSpecialistEvidenceReviewCoverageScoreReasonCodeCount(
            "team_specialist_evidence_review_coverage_pass",
            d("1.000000"),
        ),
    )

    row = report.rows[0]
    assert row.rank == d("1.000000")
    assert row.evidence_type_coverage_ratio == d("1.000000")
    assert row.review_step_completion_ratio == d("1.000000")
    assert row.resolved_gap_ratio == d("0.900000")
    assert row.review_coverage_score == d("0.890000")
    assert row.status == "pass"
    assert row.reason_codes == ("team_specialist_evidence_review_coverage_pass",)


def test_partial_evidence_and_review_coverage_watches() -> None:
    report = build_report(
        coverage_input(
            completed_review_step_count=d("3.000000"),
            independent_evidence_ratio=d("0.650000"),
            cross_review_ratio=d("0.550000"),
            unresolved_gap_ratio=d("0.250000"),
        ),
    )

    row = report.rows[0]
    assert row.review_step_completion_ratio == d("0.600000")
    assert row.review_coverage_score == d("0.670000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "review_step_coverage_watch",
        "evidence_independence_watch",
        "cross_review_watch",
        "unresolved_gap_watch",
        "evidence_review_coverage_score_watch",
    )
    assert report.report_status == "watch"
    assert report.watch_count == d("1.000000")


def test_missing_evidence_and_review_coverage_blocks() -> None:
    report = build_report(
        coverage_input(
            covered_evidence_type_count=d("1.000000"),
            completed_review_step_count=d("2.000000"),
            independent_evidence_ratio=d("0.350000"),
            cross_review_ratio=d("0.250000"),
            unresolved_gap_ratio=d("0.500000"),
        ),
    )

    row = report.rows[0]
    assert row.evidence_type_coverage_ratio == d("0.250000")
    assert row.review_step_completion_ratio == d("0.400000")
    assert row.review_coverage_score == d("0.215000")
    assert row.status == "block"
    assert row.reason_codes == (
        "evidence_type_coverage_block",
        "review_step_coverage_block",
        "evidence_independence_block",
        "cross_review_block",
        "unresolved_gap_block",
        "evidence_review_coverage_score_block",
    )
    assert report.report_status == "block"
    assert report.block_count == d("1.000000")


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: coverage_input(required_evidence_type_count=4),
            "required_evidence_type_count must be exactly Decimal",
        ),
        (
            lambda: coverage_input(covered_evidence_type_count=d("4.500000")),
            "covered_evidence_type_count must be a whole Decimal count",
        ),
        (
            lambda: coverage_input(independent_evidence_ratio=_DecimalSubclass("0.800000")),
            "independent_evidence_ratio must be exactly Decimal",
        ),
        (
            lambda: coverage_input(cross_review_ratio=0.75),
            "cross_review_ratio must be exactly Decimal",
        ),
        (
            lambda: coverage_input(unresolved_gap_ratio=d("0.1000001")),
            "unresolved_gap_ratio must use six decimal places or fewer",
        ),
        (
            lambda: config(evidence_type_weight=0.3),
            "evidence_type_weight must be exactly Decimal",
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

    with pytest.raises(ValueError, match="unsafe public value"):
        coverage_input(team_id="market_alpha")

    with pytest.raises(ValueError, match="unsafe public value"):
        coverage_input(specialist_id="trade_signal")

    with pytest.raises(ValueError, match="unsafe public value"):
        coverage_input(category_id="https://example.invalid/path")

    report = build_report(coverage_input())
    payload = dict(report.payload)
    payload["candidate_id"] = "abc123"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.team_specialist_evidence_review_coverage_score_payload(payload)

    payload = dict(report.payload)
    payload["rows"] = [dict(payload["rows"][0])]
    payload["rows"][0]["team_id"] = "wallet_ops"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_evidence_review_coverage_score_payload(payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = coverage_input()
    report = build_report(item)
    row = report.rows[0]
    rollup = report.reason_code_counts[0]

    for value in (cfg, item, row, rollup, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistEvidenceReviewCoverageScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    payload = dict(report.payload)
    payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.team_specialist_evidence_review_coverage_score_payload(payload)


def test_payload_is_deterministic_decimal_stringed_and_status_limited() -> None:
    left = coverage_input(team_id="left_team", specialist_id="reviewer_left")
    right = coverage_input(team_id="right_team", specialist_id="reviewer_right")

    report_a = build_report(right, left)
    report_b = build_report(left, right)

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert tuple(row.team_id for row in report_a.rows) == ("left_team", "right_team")
    assert report_a.payload["item_count"] == "2.000000"
    assert report_a.payload["rows"][0]["rank"] == "1.000000"
    assert report_a.payload["rows"][0]["review_coverage_score"] == "0.890000"
    assert_no_float_values(report_a.payload)
    json.dumps(report_a.payload, sort_keys=True)

    statuses = {report_a.report_status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in statuses
    assert "ready" not in statuses
    assert "matched" not in statuses
    assert "supported" not in statuses


def test_report_consistency_and_digest_validation_reject_tampering() -> None:
    module = api()
    report = build_report(
        coverage_input(team_id="pass_team", specialist_id="reviewer_pass"),
        coverage_input(
            team_id="watch_team",
            specialist_id="reviewer_watch",
            completed_review_step_count=d("3.000000"),
            independent_evidence_ratio=d("0.650000"),
            cross_review_ratio=d("0.550000"),
            unresolved_gap_ratio=d("0.250000"),
        ),
        coverage_input(
            team_id="block_team",
            specialist_id="reviewer_block",
            covered_evidence_type_count=d("1.000000"),
        ),
    )

    assert report.report_status == "block"
    assert report.item_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))

    payload = dict(report.payload)
    payload["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.team_specialist_evidence_review_coverage_score_payload(payload)

    payload = module.team_specialist_evidence_review_coverage_score_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload == report.payload


def test_module_stays_report_only_without_network_persistence_or_trading_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])

    assert imported_names.isdisjoint(
        {
            "ccxt",
            "httpx",
            "polymarket",
            "psycopg",
            "psycopg2",
            "requests",
            "socket",
            "sqlalchemy",
            "supabase",
            "urllib",
            "web3",
        },
    )
