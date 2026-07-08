from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_candidate_manual_review_blocker_report import (
    DEFAULT_RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_CONFIG_VERSION,
    RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS,
    STATUSES,
    ResearchCandidateManualReviewBlockerAggregate,
    ResearchCandidateManualReviewBlockerConfig,
    ResearchCandidateManualReviewBlockerDimensionRow,
    ResearchCandidateManualReviewBlockerReasonCodeCount,
    ResearchCandidateManualReviewBlockerReport,
    build_research_candidate_manual_review_blocker_report,
    research_candidate_manual_review_blocker_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_candidate_manual_review_blocker_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCandidateManualReviewBlockerConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_CONFIG_VERSION,
        "watch_blocker_score": d("0.300000"),
        "block_blocker_score": d("0.700000"),
        "dimension_watch_threshold": d("0.300000"),
        "dimension_block_threshold": d("0.700000"),
        "aggregate_evidence_gap_weight": d("0.250000"),
        "source_freshness_gap_weight": d("0.150000"),
        "rule_ambiguity_weight": d("0.200000"),
        "cost_input_quality_gap_weight": d("0.150000"),
        "team_capacity_gap_weight": d("0.100000"),
        "settlement_risk_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchCandidateManualReviewBlockerConfig(**values)


def aggregate(**overrides: object) -> ResearchCandidateManualReviewBlockerAggregate:
    values = {
        "aggregate_evidence_gap_score": d("0.100000"),
        "source_freshness_gap_score": d("0.100000"),
        "rule_ambiguity_score": d("0.100000"),
        "cost_input_quality_gap_score": d("0.100000"),
        "team_capacity_gap_score": d("0.100000"),
        "settlement_risk_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchCandidateManualReviewBlockerAggregate(**values)


def report(
    item: ResearchCandidateManualReviewBlockerAggregate,
    *,
    cfg: ResearchCandidateManualReviewBlockerConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCandidateManualReviewBlockerReport:
    return build_research_candidate_manual_review_blocker_report(
        item,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload_values(item))
        return tuple(nested)
    return (value,)


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
    if isinstance(value, (dict, list, tuple)):
        children = value.values() if isinstance(value, dict) else value
        for child in children:
            assert_public_numeric_values_are_decimal(child)


def test_public_api_declares_dimensions_statuses_and_hard_flags() -> None:
    assert DEFAULT_RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_CONFIG_VERSION == (
        "research-candidate-manual-review-blocker-report-v0"
    )
    assert STATUSES == ("pass", "watch", "block")
    assert RESEARCH_CANDIDATE_MANUAL_REVIEW_BLOCKER_DIMENSIONS == (
        "aggregate_evidence_gap",
        "source_freshness_gap",
        "rule_ambiguity",
        "cost_input_quality_gap",
        "team_capacity_gap",
        "settlement_risk",
    )

    defaults = {
        field.name: field.default
        for field in fields(ResearchCandidateManualReviewBlockerConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True
    assert defaults["watch_blocker_score"] == d("0.300000")
    assert defaults["block_blocker_score"] == d("0.700000")


def test_blocks_public_manual_review_when_aggregate_gaps_are_severe() -> None:
    summary = report(
        aggregate(
            aggregate_evidence_gap_score=d("0.900000"),
            source_freshness_gap_score=d("0.800000"),
            rule_ambiguity_score=d("0.750000"),
            cost_input_quality_gap_score=d("0.850000"),
            team_capacity_gap_score=d("0.720000"),
            settlement_risk_score=d("0.650000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.status == "block"
    assert summary.dimension_count == d("6")
    assert summary.pass_count == d("0")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("5")
    assert summary.aggregate_blocker_score == d("0.792000")
    assert summary.max_dimension_score == d("0.900000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.dimension, row.status, row.blocker_score) for row in summary.rows) == (
        ("aggregate_evidence_gap", "block", d("0.900000")),
        ("source_freshness_gap", "block", d("0.800000")),
        ("rule_ambiguity", "block", d("0.750000")),
        ("cost_input_quality_gap", "block", d("0.850000")),
        ("team_capacity_gap", "block", d("0.720000")),
        ("settlement_risk", "watch", d("0.650000")),
    )
    assert summary.rows[0].reason_codes == ("aggregate_evidence_gap_block",)
    assert summary.rows[-1].reason_codes == ("settlement_risk_watch",)
    assert summary.reason_codes == (
        "manual_review_blocker_report_block_dimensions",
        "manual_review_blocker_report_watch_dimensions",
        "manual_review_blocker_score_block",
    )


def test_watches_moderate_freshness_and_cost_quality_gaps() -> None:
    summary = report(
        aggregate(
            aggregate_evidence_gap_score=d("0.100000"),
            source_freshness_gap_score=d("0.400000"),
            rule_ambiguity_score=d("0.200000"),
            cost_input_quality_gap_score=d("0.450000"),
            team_capacity_gap_score=d("0.250000"),
            settlement_risk_score=d("0.200000"),
        ),
    )

    assert summary.status == "watch"
    assert summary.aggregate_blocker_score == d("0.247500")
    assert summary.pass_count == d("4")
    assert summary.watch_count == d("2")
    assert summary.block_count == d("0")
    assert summary.reason_codes == (
        "manual_review_blocker_report_watch_dimensions",
    )
    assert tuple(row.reason_codes for row in summary.rows if row.status == "watch") == (
        ("source_freshness_gap_watch",),
        ("cost_input_quality_gap_watch",),
    )


def test_passes_when_all_public_review_blockers_are_below_thresholds() -> None:
    summary = report(aggregate())

    assert summary.status == "pass"
    assert summary.aggregate_blocker_score == d("0.100000")
    assert summary.max_dimension_score == d("0.100000")
    assert summary.pass_count == d("6")
    assert summary.watch_count == d("0")
    assert summary.block_count == d("0")
    assert summary.reason_codes == ("manual_review_blocker_report_pass",)
    assert tuple(row.status for row in summary.rows) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )


def test_payload_and_digest_are_deterministic_public_safe_and_string_numeric() -> None:
    input_row = aggregate(
        aggregate_evidence_gap_score=d("0.500000"),
        source_freshness_gap_score=d("0.350000"),
        rule_ambiguity_score=d("0.250000"),
        cost_input_quality_gap_score=d("0.450000"),
        team_capacity_gap_score=d("0.200000"),
        settlement_risk_score=d("0.300000"),
    )

    first = report(input_row)
    second = report(input_row)
    payload_first = research_candidate_manual_review_blocker_report_payload(first)
    payload_second = research_candidate_manual_review_blocker_report_payload(second)

    assert first.report_digest == second.report_digest
    assert payload_first == payload_second
    assert len(first.report_digest) == 64
    assert payload_first["report_digest"] == first.report_digest
    assert payload_first["aggregate_blocker_score"] == "0.360000"
    assert payload_first["rows"][0]["blocker_score"] == "0.500000"
    assert payload_first["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert not any(
        type(value) in (Decimal, int, float)
        for value in walk_payload_values(payload_first)
    )

    payload_text = repr(payload_first).lower()
    for fragment in (
        "candidate_id",
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "wal" "let",
        "au" "th",
        "ord" "er",
        "tra" "de",
        "li" "ve",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "position_size",
        "position sizing",
    ):
        assert fragment not in payload_text

    tampered = dict(payload_first)
    tampered["aggregate_blocker_score"] = "0.380001"
    with pytest.raises(ValueError, match="report_digest"):
        research_candidate_manual_review_blocker_report_payload(tampered)


def test_validation_rejects_non_decimal_inputs_raw_ids_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="aggregate_evidence_gap_score must be a Decimal"):
        aggregate(aggregate_evidence_gap_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_freshness_gap_score must be a Decimal"):
        aggregate(source_freshness_gap_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        aggregate(rule_ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="raw public identifiers"):
        config(config_version="public-candidate_id-hidden")
    with pytest.raises(ValueError, match="paper_only must be True"):
        aggregate(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_research_candidate_manual_review_blocker_report(
            aggregate(readonly=False),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="watch_blocker_score"):
        config(watch_blocker_score=d("0.800000"), block_blocker_score=d("0.700000"))
    with pytest.raises(ValueError, match="component weights must sum to 1"):
        config(aggregate_evidence_gap_weight=d("0.260000"))


def test_dataclasses_are_frozen_decimal_only_and_consistency_checked() -> None:
    sample_config = config()
    sample_aggregate = aggregate()
    sample_report = report(sample_aggregate)
    sample_row = sample_report.rows[0]
    sample_count = sample_report.reason_code_counts[0]

    for item in (sample_config, sample_aggregate, sample_row, sample_count, sample_report):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="report_digest must match report fields"):
        replace(sample_report, report_digest="0" * 64)
    with pytest.raises(ValueError, match="aggregate_blocker_score must match rows"):
        replace(sample_report, aggregate_blocker_score=d("0.100001"))
    with pytest.raises(ValueError, match="reason_codes must match row fields"):
        replace(sample_row, reason_codes=("aggregate_evidence_gap_watch",))


def test_module_scope_has_no_durable_or_action_surfaces() -> None:
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
        "request",
        "urllib",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "supabase",
        "client",
        "broker",
        "store",
        "data" "base",
        "wal" "let",
        "au" "th",
    )
    forbidden_call_or_attribute_names = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "fetch",
        "insert",
        "send",
        "submit",
        "sign",
        "b" "uy",
        "se" "ll",
        "tra" "de",
        "write",
    }
    source_text = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for fragment in (
        "wal" "let",
        "au" "th",
        "ord" "er",
        "tra" "de",
        "li" "ve execution",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "position_size",
        "position sizing",
    ):
        assert fragment not in source_text
