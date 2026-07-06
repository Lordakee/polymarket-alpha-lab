from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect
import json

import pytest

import polymarket_alpha_lab.strategy_resolution_conflict_adjusted_edge_score_v2 as api
from polymarket_alpha_lab.strategy_resolution_conflict_adjusted_edge_score_v2 import (
    StrategyResolutionConflictAdjustedEdgeScoreV2Candidate,
    StrategyResolutionConflictAdjustedEdgeScoreV2Config,
    StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem,
    StrategyResolutionConflictAdjustedEdgeScoreV2Report,
    StrategyResolutionConflictAdjustedEdgeScoreV2Row,
    build_strategy_resolution_conflict_adjusted_edge_score_v2_report,
    strategy_resolution_conflict_adjusted_edge_score_v2_payload,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
UNSAFE_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


def _candidate(
    *,
    candidate_id: str = "candidate_a",
    market_slug: str = "market_alpha",
    recommendation_side: str = "yes",
    forecast_probability: Decimal = Decimal("0.620000"),
    implied_probability: Decimal = Decimal("0.520000"),
    confidence_score: Decimal = Decimal("0.800000"),
    resolution_conflict_count: Decimal = Decimal("1.000000"),
    unresolved_resolution_conflict_count: Decimal = Decimal("1.000000"),
    official_resolution_source_count: Decimal = Decimal("2.000000"),
    reason_codes: tuple[str, ...] = ("resolution_review_ready",),
) -> StrategyResolutionConflictAdjustedEdgeScoreV2Candidate:
    return StrategyResolutionConflictAdjustedEdgeScoreV2Candidate(
        candidate_id=candidate_id,
        market_slug=market_slug,
        recommendation_side=recommendation_side,
        forecast_probability=forecast_probability,
        implied_probability=implied_probability,
        confidence_score=confidence_score,
        resolution_conflict_count=resolution_conflict_count,
        unresolved_resolution_conflict_count=unresolved_resolution_conflict_count,
        official_resolution_source_count=official_resolution_source_count,
        observed_at=NOW,
        reason_codes=reason_codes,
    )


def _report(
    candidates: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2Candidate, ...],
    *,
    config: StrategyResolutionConflictAdjustedEdgeScoreV2Config | None = None,
    public_payload: tuple[StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem, ...] = (),
) -> StrategyResolutionConflictAdjustedEdgeScoreV2Report:
    return build_strategy_resolution_conflict_adjusted_edge_score_v2_report(
        candidates,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_conflict_adjusted_edge_scoring_uses_decimal_math() -> None:
    report = _report((_candidate(),))

    row = report.rows[0]
    assert row.raw_edge == Decimal("0.100000")
    assert row.confidence_weighted_edge == Decimal("0.080000")
    assert row.unresolved_resolution_conflict_penalty == Decimal("0.040000")
    assert row.official_resolution_source_boost == Decimal("0.040000")
    assert row.conflict_adjusted_edge_score == Decimal("0.080000")
    assert row.edge_status == "qualified"
    assert report.qualified_count == Decimal("1.000000")
    assert report.average_conflict_adjusted_edge_score == Decimal("0.080000")
    assert "conflict_adjusted_edge_qualified" in row.reason_codes


def test_unresolved_resolution_conflicts_penalize_and_block_rows() -> None:
    report = _report(
        (
            _candidate(
                resolution_conflict_count=Decimal("3.000000"),
                unresolved_resolution_conflict_count=Decimal("3.000000"),
                official_resolution_source_count=Decimal("0.000000"),
            ),
        ),
    )

    row = report.rows[0]
    assert row.unresolved_resolution_conflict_penalty == Decimal("0.120000")
    assert row.official_resolution_source_boost == Decimal("0.000000")
    assert row.conflict_adjusted_edge_score == Decimal("-0.040000")
    assert row.edge_status == "blocked"
    assert report.status == "blocked"
    assert "unresolved_resolution_conflict_penalty" in row.reason_codes
    assert "conflict_adjusted_edge_blocked" in report.reason_codes


def test_official_resolution_source_boost_can_qualify_watch_edge() -> None:
    unboosted = _report(
        (
            _candidate(
                forecast_probability=Decimal("0.560000"),
                implied_probability=Decimal("0.520000"),
                confidence_score=Decimal("0.500000"),
                unresolved_resolution_conflict_count=Decimal("0.000000"),
                official_resolution_source_count=Decimal("0.000000"),
            ),
        ),
    )
    boosted = _report(
        (
            _candidate(
                forecast_probability=Decimal("0.560000"),
                implied_probability=Decimal("0.520000"),
                confidence_score=Decimal("0.500000"),
                unresolved_resolution_conflict_count=Decimal("0.000000"),
                official_resolution_source_count=Decimal("2.000000"),
            ),
        ),
    )

    assert unboosted.rows[0].conflict_adjusted_edge_score == Decimal("0.020000")
    assert unboosted.rows[0].edge_status == "watch"
    assert boosted.rows[0].official_resolution_source_boost == Decimal("0.040000")
    assert boosted.rows[0].conflict_adjusted_edge_score == Decimal("0.060000")
    assert boosted.rows[0].edge_status == "qualified"
    assert "official_resolution_source_boost" in boosted.rows[0].reason_codes


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    report = _report(
        (_candidate(),),
        public_payload=(
            StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem(
                "safe_key",
                "safe value",
            ),
        ),
    )

    payload = report.payload
    assert payload == strategy_resolution_conflict_adjusted_edge_score_v2_payload(report)
    json.dumps(payload, sort_keys=True)
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_conflict_adjusted_edge_score"] == "0.080000"
    assert payload["rows"][0]["raw_edge"] == "0.100000"
    assert payload["rows"][0]["official_resolution_source_boost"] == "0.040000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_public_non_decimal_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_candidate(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.rows[0].edge_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(StrategyResolutionConflictAdjustedEdgeScoreV2Config):
            pass


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        StrategyResolutionConflictAdjustedEdgeScoreV2Config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _candidate().__class__(
            candidate_id="candidate_a",
            market_slug="market_alpha",
            recommendation_side="yes",
            forecast_probability=Decimal("0.620000"),
            implied_probability=Decimal("0.520000"),
            confidence_score=Decimal("0.800000"),
            resolution_conflict_count=Decimal("1.000000"),
            unresolved_resolution_conflict_count=Decimal("1.000000"),
            official_resolution_source_count=Decimal("2.000000"),
            observed_at=NOW,
            reason_codes=("resolution_review_ready",),
            report_only=False,
        )

    report = _report((_candidate(),))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report((_candidate(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem(
                    "safe_key",
                    "changed value",
                ),
            ),
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, rows=(replace(report.rows[0], derived_validation_digest="f" * 64),))


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for term in UNSAFE_TERMS:
        with pytest.raises(ValueError, match="unsafe public"):
            StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem(
                f"{term}_key",
                "safe value",
            )
        with pytest.raises(ValueError, match="unsafe public"):
            StrategyResolutionConflictAdjustedEdgeScoreV2PublicPayloadItem(
                "safe_key",
                f"{term} value",
            )

    with pytest.raises(ValueError, match="unsafe public"):
        _candidate(market_slug="wallet_alpha")

    with pytest.raises(ValueError, match="unsafe public"):
        _candidate(reason_codes=("live_reason",))


def test_no_unsafe_surfaces_are_exposed() -> None:
    public_names = tuple(name.lower() for name in api.__all__)
    for name in public_names:
        assert not any(term in name for term in UNSAFE_TERMS)

    forbidden_public_modules = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
    )
    module_source = inspect.getsource(api)
    for forbidden in forbidden_public_modules:
        assert forbidden not in module_source


def _assert_no_public_non_decimal_numbers(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_public_non_decimal_numbers(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_no_public_non_decimal_numbers(item)
        return
    if type(value) in (int, float):
        raise AssertionError(f"non-Decimal public numeric value: {value!r}")


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"Decimal object was not serialized: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)
