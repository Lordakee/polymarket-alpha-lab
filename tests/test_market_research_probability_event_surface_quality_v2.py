from __future__ import annotations

import ast
import dataclasses
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_probability_event_surface_quality_v2 import (
    MarketResearchProbabilityEventSurfaceQualityConfig,
    MarketResearchProbabilityEventSurfaceQualityInput,
    MarketResearchProbabilityEventSurfaceQualityReport,
    build_market_research_probability_event_surface_quality_report,
    market_research_probability_event_surface_quality_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=10)


def surface(
    surface_id: str = "surface-a",
    market_slug: str = "candidate-a-2026-mayor",
    category: str = "politics",
    *,
    question: str = (
        "Will Candidate A win the 2026 New York mayoral election by certified final results?"
    ),
    resolution_criteria: str = (
        "Resolves yes only if the official city election board certifies Candidate A "
        "as winner; otherwise resolves no."
    ),
    observed_at: datetime = OBSERVED_AT,
    catalyst_at: datetime | None = OBSERVED_AT + timedelta(hours=48),
    source_references: tuple[str, ...] = (
        "city-election-board-results",
        "local-campaign-calendar",
        "state-election-calendar",
    ),
    official_source_count: Decimal = Decimal("2"),
    bid_depth_usd: Decimal = Decimal("2500"),
    ask_depth_usd: Decimal = Decimal("3000"),
    contradiction_count: Decimal = Decimal("0"),
    highest_contradiction_severity: Decimal = Decimal("0"),
    reason_codes: tuple[str, ...] = ("election_board",),
) -> MarketResearchProbabilityEventSurfaceQualityInput:
    return MarketResearchProbabilityEventSurfaceQualityInput(
        surface_id=surface_id,
        market_slug=market_slug,
        category=category,
        question=question,
        resolution_criteria=resolution_criteria,
        observed_at=observed_at,
        catalyst_at=catalyst_at,
        source_references=source_references,
        official_source_count=official_source_count,
        bid_depth_usd=bid_depth_usd,
        ask_depth_usd=ask_depth_usd,
        contradiction_count=contradiction_count,
        highest_contradiction_severity=highest_contradiction_severity,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_empty_digest() -> None:
    report = build_market_research_probability_event_surface_quality_report(
        (),
        generated_at=GENERATED_AT,
        config=MarketResearchProbabilityEventSurfaceQualityConfig(),
    )

    assert report == MarketResearchProbabilityEventSurfaceQualityReport(
        generated_at=GENERATED_AT,
        config_version="market_research_probability_event_surface_quality_v2",
        row_count=Decimal("0"),
        surface_count=Decimal("0"),
        category_count=Decimal("0"),
        ready_count=Decimal("0"),
        watch_count=Decimal("0"),
        review_count=Decimal("0"),
        average_quality_score=Decimal("0"),
        weakest_quality_score=Decimal("0"),
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_quality_surface_scores_ready_with_decimal_only_dimensions() -> None:
    report = build_market_research_probability_event_surface_quality_report(
        (surface(),),
        generated_at=GENERATED_AT,
        config=MarketResearchProbabilityEventSurfaceQualityConfig(),
    )

    row = report.rows[0]
    assert row.surface_id == "surface-a"
    assert row.source_references == (
        "city-election-board-results",
        "local-campaign-calendar",
        "state-election-calendar",
    )
    assert row.source_reference_count == Decimal("3")
    assert row.official_source_count == Decimal("2")
    assert row.total_depth_usd == Decimal("5500.0000")
    assert row.catalyst_hours_until == Decimal("48.0000")
    assert row.question_specificity_score == Decimal("1.0000")
    assert row.resolution_criteria_clarity_score == Decimal("1.0000")
    assert row.source_availability_score == Decimal("1.0000")
    assert row.catalyst_timing_score == Decimal("1.0000")
    assert row.liquidity_depth_score == Decimal("1.0000")
    assert row.contradiction_risk_score == Decimal("0.0000")
    assert row.quality_score == Decimal("1.0000")
    assert row.quality_status == "surface_quality_ready"
    assert row.reason_codes == ("election_board", "surface_quality_ready")
    assert report.ready_count == Decimal("1")


def test_weak_surface_flags_each_quality_dimension_and_contradiction_risk() -> None:
    report = build_market_research_probability_event_surface_quality_report(
        (
            surface(
                question="Will it happen?",
                resolution_criteria="See rules.",
                catalyst_at=None,
                source_references=(),
                official_source_count=Decimal("0"),
                bid_depth_usd=Decimal("0"),
                ask_depth_usd=Decimal("0"),
                contradiction_count=Decimal("2"),
                highest_contradiction_severity=Decimal("0.8"),
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=MarketResearchProbabilityEventSurfaceQualityConfig(),
    )

    row = report.rows[0]
    assert row.quality_status == "surface_quality_review"
    assert row.quality_score == Decimal("0.1814")
    assert row.contradiction_risk_score == Decimal("0.9000")
    assert row.reason_codes == (
        "catalyst_timing_gap",
        "high_contradiction_risk",
        "limited_source_availability",
        "low_surface_quality_score",
        "surface_quality_review",
        "thin_liquidity_depth",
        "unclear_resolution_criteria",
        "vague_question",
    )
    assert report.review_count == Decimal("1")


def test_rows_reason_counts_and_digest_are_deterministic() -> None:
    config = MarketResearchProbabilityEventSurfaceQualityConfig()
    inputs = (
        surface(
            "surface-z",
            "z-market",
            "sports",
            source_references=("sports-fixture", "league-notice"),
            official_source_count=Decimal("1"),
            bid_depth_usd=Decimal("1000"),
            ask_depth_usd=Decimal("1200"),
            reason_codes=("zeta", "alpha"),
        ),
        surface(
            "surface-a",
            "a-market",
            "politics",
            source_references=("state-election-calendar", "city-election-board-results"),
            official_source_count=Decimal("1"),
            reason_codes=("alpha",),
        ),
        surface(
            "surface-m",
            "m-market",
            "politics",
            contradiction_count=Decimal("1"),
            highest_contradiction_severity=Decimal("0.4"),
            reason_codes=("beta",),
        ),
    )

    report = build_market_research_probability_event_surface_quality_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_market_research_probability_event_surface_quality_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.surface_id for row in report.rows] == ["surface-a", "surface-m", "surface-z"]
    assert report.reason_code_counts == (
        ("alpha", Decimal("2")),
        ("beta", Decimal("1")),
        ("surface_quality_ready", Decimal("2")),
        ("surface_quality_review", Decimal("1")),
        ("thin_liquidity_depth", Decimal("1")),
        ("zeta", Decimal("1")),
    )
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest


def test_payload_helper_uses_decimal_strings_and_revalidates_digest() -> None:
    report = build_market_research_probability_event_surface_quality_report(
        (surface(),),
        generated_at=GENERATED_AT,
        config=MarketResearchProbabilityEventSurfaceQualityConfig(),
    )

    payload = market_research_probability_event_surface_quality_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["quality_score"] == "1.0000"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_research_probability_event_surface_quality_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_ref"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        market_research_probability_event_surface_quality_payload(unsafe_key_payload)


def test_validation_rejects_invalid_decimals_datetimes_counts_and_flags() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_research_probability_event_surface_quality_report(
            (),
            generated_at=datetime(2026, 7, 6, 12, 0),
            config=MarketResearchProbabilityEventSurfaceQualityConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        surface(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        surface(observed_at=datetime(2026, 7, 6, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        surface(observed_at=DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="bid_depth_usd"):
        surface(bid_depth_usd=Decimal("-1"))
    with pytest.raises(ValueError, match="official_source_count"):
        surface(official_source_count=Decimal("4"))
    with pytest.raises(ValueError, match="highest_contradiction_severity"):
        surface(highest_contradiction_severity=Decimal("1.1"))
    with pytest.raises(ValueError, match="question_specificity_weight"):
        MarketResearchProbabilityEventSurfaceQualityConfig(
            question_specificity_weight=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="quality weights"):
        MarketResearchProbabilityEventSurfaceQualityConfig(
            contradiction_risk_weight=Decimal("0.2000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(MarketResearchProbabilityEventSurfaceQualityConfig(), paper_only=False)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = MarketResearchProbabilityEventSurfaceQualityConfig()
    input_row = surface()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.surface_id = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(MarketResearchProbabilityEventSurfaceQualityConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(MarketResearchProbabilityEventSurfaceQualityInput):
            pass


def test_static_module_has_no_forbidden_side_effect_surface_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_probability_event_surface_quality_v2.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "network",
        "database",
        "persist",
        "private_key",
    )

    assert not [term for term in forbidden_terms if term in source.lower()]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)
