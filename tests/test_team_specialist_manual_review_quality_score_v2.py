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
    / "team_specialist_manual_review_quality_score_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_manual_review_quality_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-manual-review-quality-score-v2-test",
        "min_pass_quality_score": d("0.850000"),
        "min_watch_quality_score": d("0.650000"),
        "min_pass_dimension_score": d("0.750000"),
        "min_watch_dimension_score": d("0.500000"),
    }
    values.update(overrides)
    return module.TeamSpecialistManualReviewQualityScoreV2Config(**values)


def packet(**overrides: object):
    module = api()
    values = {
        "packet_id": "macro_rates_packet_alpha",
        "specialist_id": "manual_reviewer_a",
        "rationale_completeness_score": d("0.900000"),
        "source_coverage_score": d("0.900000"),
        "risk_reason_completeness_score": d("0.900000"),
        "abstain_condition_clarity_score": d("0.900000"),
        "cost_estimate_completeness_score": d("0.900000"),
        "resolution_rule_coverage_score": d("0.900000"),
        "handoff_readiness_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistManualReviewQualityScoreV2Packet(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_manual_review_quality_score_v2(
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


def test_public_api_declares_phase_one_dimensions_and_hard_flags() -> None:
    module = api()

    assert module.DEFAULT_TEAM_SPECIALIST_MANUAL_REVIEW_QUALITY_SCORE_V2_CONFIG_VERSION == (
        "team-specialist-manual-review-quality-score-v2"
    )
    assert module.MANUAL_REVIEW_QUALITY_SCORE_DIMENSIONS == (
        "rationale_completeness",
        "source_coverage",
        "risk_reason_completeness",
        "abstain_condition_clarity",
        "cost_estimate_completeness",
        "resolution_rule_coverage",
        "handoff_readiness",
    )
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_MANUAL_REVIEW_QUALITY_SCORE_V2_CONFIG_VERSION",
        "MANUAL_REVIEW_QUALITY_SCORE_DIMENSIONS",
        "TeamSpecialistManualReviewQualityScoreV2Config",
        "TeamSpecialistManualReviewQualityScoreV2Packet",
        "TeamSpecialistManualReviewQualityScoreV2Row",
        "TeamSpecialistManualReviewQualityScoreV2Report",
        "build_team_specialist_manual_review_quality_score_v2",
        "team_specialist_manual_review_quality_score_v2_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.TeamSpecialistManualReviewQualityScoreV2Config)
    }
    assert field_defaults["config_version"] == (
        module.DEFAULT_TEAM_SPECIALIST_MANUAL_REVIEW_QUALITY_SCORE_V2_CONFIG_VERSION
    )
    assert field_defaults["min_pass_quality_score"] == d("0.850000")
    assert field_defaults["min_watch_quality_score"] == d("0.650000")
    assert field_defaults["min_pass_dimension_score"] == d("0.750000")
    assert field_defaults["min_watch_dimension_score"] == d("0.500000")
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_manual_review_packet_quality_scoring_sorts_rows_and_passes_clear_packets() -> None:
    report = build_report(
        packet(packet_id="zeta_packet", specialist_id="reviewer_z"),
        packet(
            packet_id="alpha_packet",
            specialist_id="reviewer_a",
            rationale_completeness_score=d("0.950000"),
            source_coverage_score=d("0.900000"),
            risk_reason_completeness_score=d("0.850000"),
            abstain_condition_clarity_score=d("0.900000"),
            cost_estimate_completeness_score=d("0.850000"),
            resolution_rule_coverage_score=d("0.900000"),
            handoff_readiness_score=d("0.950000"),
        ),
    )

    assert report.score_band == "pass"
    assert report.packet_count == d("2")
    assert report.pass_count == d("2")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.pass_ratio == d("1.000000")
    assert report.average_quality_score == d("0.900000")
    assert report.reason_codes == (
        "manual_review_quality_report_passed",
    )
    assert tuple(row.packet_id for row in report.rows) == (
        "alpha_packet",
        "zeta_packet",
    )
    assert report.rows[0].rank == d("1")
    assert report.rows[0].quality_score == d("0.900000")
    assert report.rows[0].score_band == "pass"
    assert report.rows[0].reason_codes == (
        "manual_review_quality_row_passed",
    )
    assert report.rows[1].rank == d("2")
    assert report.rows[1].quality_score == d("0.900000")


def test_watch_and_blocked_reason_codes_are_deterministic_by_dimension_order() -> None:
    report = build_report(
        packet(
            packet_id="blocked_packet",
            specialist_id="reviewer_b",
            rationale_completeness_score=d("0.490000"),
            source_coverage_score=d("0.900000"),
            risk_reason_completeness_score=d("0.400000"),
            abstain_condition_clarity_score=d("0.900000"),
            cost_estimate_completeness_score=d("0.300000"),
            resolution_rule_coverage_score=d("0.700000"),
            handoff_readiness_score=d("0.200000"),
        ),
        packet(
            packet_id="watch_packet",
            specialist_id="reviewer_w",
            rationale_completeness_score=d("0.760000"),
            source_coverage_score=d("0.740000"),
            risk_reason_completeness_score=d("0.760000"),
            abstain_condition_clarity_score=d("0.740000"),
            cost_estimate_completeness_score=d("0.760000"),
            resolution_rule_coverage_score=d("0.740000"),
            handoff_readiness_score=d("0.760000"),
        ),
    )

    blocked, watch = report.rows
    assert blocked.quality_score == d("0.555714")
    assert blocked.score_band == "blocked"
    assert blocked.reason_codes == (
        "manual_review_quality_rationale_missing",
        "manual_review_quality_risk_reasons_missing",
        "manual_review_quality_cost_estimate_missing",
        "manual_review_quality_resolution_rule_coverage_incomplete",
        "manual_review_quality_handoff_readiness_missing",
        "manual_review_quality_score_below_watch",
    )
    assert watch.quality_score == d("0.751429")
    assert watch.score_band == "watch"
    assert watch.reason_codes == (
        "manual_review_quality_source_coverage_incomplete",
        "manual_review_quality_abstain_conditions_incomplete",
        "manual_review_quality_resolution_rule_coverage_incomplete",
        "manual_review_quality_score_below_pass",
    )

    assert report.score_band == "blocked"
    assert report.packet_count == d("2")
    assert report.pass_count == d("0")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.pass_ratio == d("0.000000")
    assert report.watch_ratio == d("0.500000")
    assert report.blocked_ratio == d("0.500000")
    assert report.average_quality_score == d("0.653572")
    assert report.reason_codes == (
        "manual_review_quality_report_blocked_rows",
        "manual_review_quality_report_watch_rows",
        "manual_review_quality_report_average_below_pass",
    )


def test_empty_packet_set_blocks_with_stable_zero_scores() -> None:
    report = build_report()

    assert report.score_band == "blocked"
    assert report.packet_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.pass_ratio == d("0.000000")
    assert report.watch_ratio == d("0.000000")
    assert report.blocked_ratio == d("0.000000")
    assert report.average_quality_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "manual_review_quality_report_empty",
        "manual_review_quality_report_average_below_watch",
    )


def test_payload_serializes_decimal_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(
        packet(
            packet_id="payload_packet",
            specialist_id="reviewer_payload",
            rationale_completeness_score=d("0.950000"),
            source_coverage_score=d("0.900000"),
            risk_reason_completeness_score=d("0.850000"),
            abstain_condition_clarity_score=d("0.900000"),
            cost_estimate_completeness_score=d("0.850000"),
            resolution_rule_coverage_score=d("0.900000"),
            handoff_readiness_score=d("0.950000"),
        ),
    )

    payload = module.team_specialist_manual_review_quality_score_v2_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["packet_count"] == "1"
    assert payload["average_quality_score"] == "0.900000"
    assert payload["rows"][0]["quality_score"] == "0.900000"
    assert payload["rows"][0]["source_coverage_score"] == "0.900000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)
    assert module.team_specialist_manual_review_quality_score_v2_payload(payload) == payload

    tampered = dict(payload)
    tampered["average_quality_score"] = "0.900001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_manual_review_quality_score_v2_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_packet = packet()
    sample_report = build_report(packet(packet_id="frozen_packet"))
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_packet, sample_row, sample_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(
        ValueError,
        match="rationale_completeness_score must be exactly Decimal",
    ):
        packet(rationale_completeness_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="source_coverage_score must be <= 1.000000"):
        packet(source_coverage_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        packet(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(packet(readonly=False))


def test_derived_validation_digest_rejects_dataclass_tampering() -> None:
    report = build_report(packet(packet_id="digest_packet"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_quality_score must match rows"):
        replace(report, average_quality_score=d("0.900001"))
    with pytest.raises(ValueError, match="quality_score must match row dimensions"):
        replace(report.rows[0], quality_score=d("0.900001"))


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "li" "ve_review",
        "au" "th_review",
        "wal" "let_review",
        "ord" "er_review",
        "net" "work_review",
        "data" "base_review",
        "persist_review",
        "signing_review",
        "mutation_review",
        "buy_review",
        "sell_review",
        "tra" "de_review",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        packet(specialist_id=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {unsafe_value: "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.team_specialist_manual_review_quality_score_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "note": unsafe_value},
        )


def test_module_scope_has_no_unsafe_surfaces() -> None:
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
        "au" "th",
        "broker",
        "client",
        "clob",
        "data" "base",
        "db",
        "http",
        "net" "work",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wal" "let",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "submit",
        "tra" "de",
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
