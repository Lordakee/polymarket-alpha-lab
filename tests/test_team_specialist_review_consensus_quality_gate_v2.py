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
    / "team_specialist_review_consensus_quality_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_review_consensus_quality_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-review-consensus-quality-gate-v2-test",
        "evidence_weight": d("0.400000"),
        "rationale_weight": d("0.400000"),
        "confidence_weight": d("0.200000"),
        "disagreement_penalty_weight": d("0.500000"),
        "min_pass_consensus_score": d("0.800000"),
        "min_watch_consensus_score": d("0.600000"),
        "max_pass_disagreement_ratio": d("0.200000"),
        "max_watch_disagreement_ratio": d("0.400000"),
        "min_quorum_participation_ratio": d("0.750000"),
        "min_specialist_count": d("3"),
    }
    values.update(overrides)
    return module.TeamSpecialistReviewConsensusQualityGateV2Config(**values)


def review(**overrides: object):
    module = api()
    values = {
        "cohort_id": "macro_rates_review_group",
        "specialist_id": "rates_reviewer_a",
        "evidence_score": d("0.900000"),
        "rationale_score": d("0.900000"),
        "confidence_score": d("0.900000"),
        "review_complete": True,
    }
    values.update(overrides)
    return module.TeamSpecialistReviewConsensusQualityGateV2Review(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_review_consensus_quality_gate_v2(
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


def test_specialist_consensus_scoring_passes_when_scores_align() -> None:
    report = build_report(
        review(specialist_id="rates_reviewer_a", evidence_score=d("0.900000")),
        review(
            specialist_id="rates_reviewer_b",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
        review(
            specialist_id="rates_reviewer_c",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
    )

    assert report.gate_status == "pass"
    assert report.specialist_count == d("3")
    assert report.complete_review_count == d("3")
    assert report.quorum_participation_ratio == d("1.000000")
    assert report.average_raw_review_score == d("0.866667")
    assert report.disagreement_ratio == d("0.050000")
    assert report.disagreement_penalty == d("0.025000")
    assert report.consensus_quality_score == d("0.841667")
    assert report.reason_codes == (
        "team_specialist_review_consensus_quality_gate_passed",
    )
    assert tuple(row.specialist_id for row in report.rows) == (
        "rates_reviewer_a",
        "rates_reviewer_b",
        "rates_reviewer_c",
    )
    assert tuple(row.raw_review_score for row in report.rows) == (
        d("0.900000"),
        d("0.850000"),
        d("0.850000"),
    )


def test_disagreement_penalties_reduce_consensus_quality_and_rows() -> None:
    report = build_report(
        review(
            specialist_id="rates_reviewer_a",
            evidence_score=d("1.000000"),
            rationale_score=d("1.000000"),
            confidence_score=d("1.000000"),
        ),
        review(
            specialist_id="rates_reviewer_b",
            evidence_score=d("0.500000"),
            rationale_score=d("0.500000"),
            confidence_score=d("0.500000"),
        ),
        review(
            specialist_id="rates_reviewer_c",
            evidence_score=d("0.500000"),
            rationale_score=d("0.500000"),
            confidence_score=d("0.500000"),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.average_raw_review_score == d("0.666667")
    assert report.disagreement_ratio == d("0.500000")
    assert report.disagreement_penalty == d("0.250000")
    assert report.consensus_quality_score == d("0.416667")
    assert report.reason_codes == (
        "team_specialist_review_consensus_quality_gate_disagreement_blocked",
        "team_specialist_review_consensus_quality_gate_consensus_below_watch",
    )
    assert tuple(row.peer_deviation_score for row in report.rows) == (
        d("0.333333"),
        d("0.166667"),
        d("0.166667"),
    )
    assert tuple(row.disagreement_penalty for row in report.rows) == (
        d("0.166666"),
        d("0.083334"),
        d("0.083334"),
    )
    assert tuple(row.consensus_contribution_score for row in report.rows) == (
        d("0.833334"),
        d("0.416666"),
        d("0.416666"),
    )


def test_quorum_gates_block_incomplete_or_too_small_review_sets() -> None:
    incomplete = build_report(
        review(specialist_id="rates_reviewer_a"),
        review(specialist_id="rates_reviewer_b"),
        review(specialist_id="rates_reviewer_c", review_complete=False),
    )
    too_small = build_report(
        review(specialist_id="rates_reviewer_a"),
        review(specialist_id="rates_reviewer_b"),
    )

    assert incomplete.gate_status == "blocked"
    assert incomplete.complete_review_count == d("2")
    assert incomplete.quorum_participation_ratio == d("0.666667")
    assert incomplete.reason_codes == (
        "team_specialist_review_consensus_quality_gate_quorum_unmet",
        "team_specialist_review_consensus_quality_gate_incomplete_reviews",
    )
    assert too_small.gate_status == "blocked"
    assert too_small.reason_codes == (
        "team_specialist_review_consensus_quality_gate_min_specialist_count_unmet",
    )


def test_serialization_uses_decimal_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(
        review(specialist_id="rates_reviewer_a", evidence_score=d("0.900000")),
        review(
            specialist_id="rates_reviewer_b",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
        review(
            specialist_id="rates_reviewer_c",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
    )

    payload = module.team_specialist_review_consensus_quality_gate_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["specialist_count"] == "3"
    assert payload["consensus_quality_score"] == "0.841667"
    assert payload["rows"][0]["raw_review_score"] == "0.900000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)

    tampered = dict(payload)
    tampered["consensus_quality_score"] = "0.841668"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_review_consensus_quality_gate_v2_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_review = review()
    sample_report = build_report(
        review(specialist_id="rates_reviewer_a", evidence_score=d("0.900000")),
        review(
            specialist_id="rates_reviewer_b",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
        review(
            specialist_id="rates_reviewer_c",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
    )
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_review, sample_row, sample_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="evidence_score must be exactly Decimal"):
        review(evidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="review_complete must be a bool"):
        review(review_complete=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        review(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(review(readonly=False))


def test_derived_validation_digest_rejects_dataclass_tampering() -> None:
    report = build_report(
        review(specialist_id="rates_reviewer_a", evidence_score=d("0.900000")),
        review(
            specialist_id="rates_reviewer_b",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
        review(
            specialist_id="rates_reviewer_c",
            evidence_score=d("0.850000"),
            rationale_score=d("0.850000"),
            confidence_score=d("0.850000"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, consensus_quality_score=d("0.841668"))


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "live_review",
        "auth_review",
        "wallet_review",
        "order_review",
        "network_review",
        "database_review",
        "persist_review",
        "signing_review",
        "mutation_review",
        "buy_review",
        "sell_review",
        "trade_review",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        review(specialist_id=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {unsafe_value: "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.team_specialist_review_consensus_quality_gate_v2_payload(
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
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
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
