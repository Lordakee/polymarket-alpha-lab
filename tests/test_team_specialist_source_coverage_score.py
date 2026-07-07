from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.team_specialist_source_coverage_score as api
from polymarket_alpha_lab.team_specialist_source_coverage_score import (
    TeamSpecialistSourceCoverageScoreConfig,
    TeamSpecialistSourceCoverageScoreInput,
    TeamSpecialistSourceCoverageScoreReasonCodeCount,
    TeamSpecialistSourceCoverageScoreReport,
    TeamSpecialistSourceCoverageScoreRow,
    build_team_specialist_source_coverage_score_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def coverage(
    team_id: str = "team_alpha",
    specialist_id: str = "specialist_a",
    category_id: str = "category_macro",
    *,
    required_source_count: Decimal = d("4.000000"),
    covered_source_count: Decimal = d("4.000000"),
    independent_source_ratio: Decimal = d("0.800000"),
    stale_source_ratio: Decimal = d("0.100000"),
    source_quality_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamSpecialistSourceCoverageScoreInput:
    return TeamSpecialistSourceCoverageScoreInput(
        team_id=team_id,
        specialist_id=specialist_id,
        category_id=category_id,
        required_source_count=required_source_count,
        covered_source_count=covered_source_count,
        independent_source_ratio=independent_source_ratio,
        stale_source_ratio=stale_source_ratio,
        source_quality_score=source_quality_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: TeamSpecialistSourceCoverageScoreInput,
    generated_at: datetime = NOW,
    config: TeamSpecialistSourceCoverageScoreConfig | None = None,
) -> TeamSpecialistSourceCoverageScoreReport:
    return build_team_specialist_source_coverage_score_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_complete_coverage_passes_with_decimal_rollups() -> None:
    result = report(coverage())

    assert result.report_status == "pass"
    assert result.item_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_coverage_score == d("0.880000")
    assert result.minimum_coverage_score == d("0.880000")
    assert result.reason_code_counts == (
        TeamSpecialistSourceCoverageScoreReasonCodeCount(
            "team_specialist_source_coverage_pass",
            d("1.000000"),
        ),
    )

    row = result.rows[0]
    assert row.rank == d("1.000000")
    assert row.team_id == "team_alpha"
    assert row.specialist_id == "specialist_a"
    assert row.category_id == "category_macro"
    assert row.coverage_ratio == d("1.000000")
    assert row.fresh_source_ratio == d("0.900000")
    assert row.coverage_score == d("0.880000")
    assert row.status == "pass"
    assert row.reason_codes == ("team_specialist_source_coverage_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_missing_coverage_blocks_even_when_other_signals_are_strong() -> None:
    result = report(
        coverage(
            covered_source_count=d("1.000000"),
            independent_source_ratio=d("1.000000"),
            stale_source_ratio=d("0.000000"),
            source_quality_score=d("1.000000"),
        ),
    )

    row = result.rows[0]
    assert row.coverage_ratio == d("0.250000")
    assert row.coverage_score == d("0.700000")
    assert row.status == "block"
    assert row.reason_codes == ("insufficient_public_source_coverage",)
    assert result.report_status == "block"
    assert result.block_count == d("1.000000")


def test_stale_coverage_watches_without_blocking() -> None:
    result = report(
        coverage(
            stale_source_ratio=d("0.350000"),
            source_quality_score=d("0.850000"),
        ),
    )

    row = result.rows[0]
    assert row.fresh_source_ratio == d("0.650000")
    assert row.coverage_score == d("0.770000")
    assert row.status == "watch"
    assert row.reason_codes == ("stale_public_source_coverage",)
    assert result.report_status == "watch"
    assert result.watch_count == d("1.000000")


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="required_source_count"):
        coverage(required_source_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="covered_source_count"):
        coverage(covered_source_count=d("4.500000"))
    with pytest.raises(ValueError, match="independent_source_ratio"):
        coverage(independent_source_ratio=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_source_ratio"):
        coverage(stale_source_ratio=d("0.1000001"))
    with pytest.raises(ValueError, match="source_quality_score"):
        coverage(source_quality_score=d("1.000001"))


def test_public_payload_rejects_leaks_and_unsafe_public_terms() -> None:
    unsafe_terms = (
        "market",
        "candidate",
        "slug",
        "question",
        "url",
        "source_ref",
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
    allowed_source_field_fragments = ("source_count", "source_ratio", "source_quality")
    allowed_source_identifiers = (
        "team_specialist_source_coverage_score",
        "source_coverage",
        "public_source",
        "fresh_source",
        "stale_source",
        "required_source_count",
        "covered_source_count",
        "source_quality_score",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert any(term not in lowered for term in unsafe_terms)
        for term in unsafe_terms:
            if term == "source" and any(identifier in lowered for identifier in allowed_source_identifiers):
                continue
            assert term not in lowered

    for cls in (
        TeamSpecialistSourceCoverageScoreConfig,
        TeamSpecialistSourceCoverageScoreInput,
        TeamSpecialistSourceCoverageScoreReasonCodeCount,
        TeamSpecialistSourceCoverageScoreRow,
        TeamSpecialistSourceCoverageScoreReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            for term in unsafe_terms:
                if term == "source" and any(fragment in lowered for fragment in allowed_source_field_fragments):
                    continue
                assert term not in lowered

    payload = report(coverage()).payload
    payload_text = json.dumps(payload, sort_keys=True).lower()
    for term in unsafe_terms:
        if term == "source":
            continue
        assert term not in payload_text

    with pytest.raises(ValueError, match="unsafe public"):
        coverage(team_id="team_token")
    with pytest.raises(ValueError, match="unsafe public"):
        coverage(category_id="https://example.invalid/category")


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    result = report(coverage())
    values = (
        TeamSpecialistSourceCoverageScoreConfig(),
        coverage(),
        result.reason_code_counts[0],
        result.rows[0],
        result,
    )

    for value in values:
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        TeamSpecialistSourceCoverageScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        coverage(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)


def test_payload_is_deterministic_and_json_safe() -> None:
    first = report(
        coverage("team_b", "specialist_b", "category_b"),
        coverage("team_a", "specialist_a", "category_a"),
    )
    second = report(
        coverage("team_a", "specialist_a", "category_a"),
        coverage("team_b", "specialist_b", "category_b"),
    )

    assert tuple((row.team_id, row.specialist_id, row.category_id) for row in first.rows) == (
        ("team_a", "specialist_a", "category_a"),
        ("team_b", "specialist_b", "category_b"),
    )
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first.payload, sort_keys=True)
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)


def test_report_consistency_rejects_tampering() -> None:
    result = report(
        coverage("team_pass", "specialist_a", "category_a"),
        coverage(
            "team_watch",
            "specialist_b",
            "category_b",
            stale_source_ratio=d("0.350000"),
            source_quality_score=d("0.850000"),
        ),
        coverage(
            "team_block",
            "specialist_c",
            "category_c",
            covered_source_count=d("1.000000"),
        ),
    )

    assert result.report_status == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(
            result,
            pass_count=d("2.000000"),
            derived_validation_digest=result.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public dataclass contains non-Decimal number: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
