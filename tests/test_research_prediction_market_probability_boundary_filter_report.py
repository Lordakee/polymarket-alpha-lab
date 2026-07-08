from __future__ import annotations

import ast
import dataclasses
import json
from datetime import UTC, datetime, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_prediction_market_probability_boundary_filter_report import (
    ResearchPredictionMarketProbabilityBoundaryFilterCandidate,
    ResearchPredictionMarketProbabilityBoundaryFilterConfig,
    ResearchPredictionMarketProbabilityBoundaryFilterReport,
    build_research_prediction_market_probability_boundary_filter_report,
    research_prediction_market_probability_boundary_filter_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def candidate(
    cohort: str = "macro-election-cluster",
    *,
    public_probability: Decimal = Decimal("0.420000"),
    public_depth_usd: Decimal = Decimal("5000.000000"),
    last_update_age_hours: Decimal = Decimal("2.000000"),
    ambiguity_score: Decimal = Decimal("0.100000"),
) -> ResearchPredictionMarketProbabilityBoundaryFilterCandidate:
    return ResearchPredictionMarketProbabilityBoundaryFilterCandidate(
        cohort=cohort,
        public_probability=public_probability,
        public_depth_usd=public_depth_usd,
        last_update_age_hours=last_update_age_hours,
        ambiguity_score=ambiguity_score,
    )


def test_empty_input_returns_report_only_public_status_counts() -> None:
    report = build_research_prediction_market_probability_boundary_filter_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
    )

    assert report == ResearchPredictionMarketProbabilityBoundaryFilterReport(
        generated_at=GENERATED_AT,
        config_version="research_prediction_market_probability_boundary_filter_report",
        candidate_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        lowest_boundary_distance=Decimal("0"),
        weakest_depth_usd=Decimal("0"),
        highest_staleness_hours=Decimal("0"),
        highest_ambiguity_score=Decimal("0"),
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_pass_watch_and_block_classification_use_public_aggregate_fields_only() -> None:
    report = build_research_prediction_market_probability_boundary_filter_report(
        (
            candidate("pass-cluster"),
            candidate(
                "near-boundary-watch-cluster",
                public_probability=Decimal("0.080000"),
            ),
            candidate(
                "thin-stale-ambiguous-block-cluster",
                public_probability=Decimal("0.980000"),
                public_depth_usd=Decimal("100.000000"),
                last_update_age_hours=Decimal("80.000000"),
                ambiguity_score=Decimal("0.920000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
    )

    assert tuple(row.cohort for row in report.rows) == (
        "near-boundary-watch-cluster",
        "pass-cluster",
        "thin-stale-ambiguous-block-cluster",
    )
    assert [row.public_status for row in report.rows] == ["watch", "pass", "block"]
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")

    watch_row = report.rows[0]
    assert watch_row.boundary_distance == Decimal("0.080000")
    assert watch_row.reason_codes == ("near_probability_boundary_watch",)

    block_row = report.rows[2]
    assert block_row.boundary_distance == Decimal("0.020000")
    assert block_row.reason_codes == (
        "ambiguous_event_block",
        "near_probability_boundary_block",
        "stale_event_block",
        "thin_event_block",
    )
    assert not _contains_forbidden_public_key(
        research_prediction_market_probability_boundary_filter_payload(report),
    )


def test_multiple_watch_flags_do_not_escalate_to_block_without_block_threshold() -> None:
    report = build_research_prediction_market_probability_boundary_filter_report(
        (
            candidate(
                public_probability=Decimal("0.090000"),
                public_depth_usd=Decimal("750.000000"),
                last_update_age_hours=Decimal("20.000000"),
                ambiguity_score=Decimal("0.650000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
    )

    row = report.rows[0]
    assert row.public_status == "watch"
    assert row.reason_codes == (
        "ambiguous_event_watch",
        "near_probability_boundary_watch",
        "stale_event_watch",
        "thin_event_watch",
    )


def test_payload_digest_is_deterministic_and_decimal_string_only() -> None:
    config = ResearchPredictionMarketProbabilityBoundaryFilterConfig()
    inputs = (
        candidate("z-cluster", public_probability=Decimal("0.970000")),
        candidate("a-cluster", public_depth_usd=Decimal("800.000000")),
        candidate("m-cluster", ambiguity_score=Decimal("0.800000")),
    )

    report = build_research_prediction_market_probability_boundary_filter_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_prediction_market_probability_boundary_filter_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )
    payload = research_prediction_market_probability_boundary_filter_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert [row.cohort for row in report.rows] == ["a-cluster", "m-cluster", "z-cluster"]
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_payload_digest == report.derived_payload_digest
    assert len(report.derived_payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_payload_digest)
    assert payload["derived_payload_digest"] == report.derived_payload_digest
    assert payload["rows"][0]["public_depth_usd"] == "800.000000"
    assert payload["candidate_count"] == "3.000000"
    assert payload["reason_code_counts"][0][1] == "1.000000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded

    tampered_payload = dict(payload)
    tampered_payload["candidate_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_payload_digest"):
        research_prediction_market_probability_boundary_filter_payload(tampered_payload)


def test_validation_rejects_non_decimal_numbers_datetimes_flags_and_public_leakage() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_prediction_market_probability_boundary_filter_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_prediction_market_probability_boundary_filter_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()),
            config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_research_prediction_market_probability_boundary_filter_report(
            (),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
        )
    with pytest.raises(ValueError, match="public_probability must be a Decimal"):
        candidate(public_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_depth_usd must be a Decimal"):
        candidate(public_depth_usd=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_probability must be between 0 and 1"):
        candidate(public_probability=Decimal("1.000001"))
    with pytest.raises(ValueError, match="last_update_age_hours must be nonnegative"):
        candidate(last_update_age_hours=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(
            ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="unsafe public"):
        candidate(cohort="contains-market-slug")

    payload = research_prediction_market_probability_boundary_filter_payload(
        build_research_prediction_market_probability_boundary_filter_report(
            (candidate(),),
            generated_at=GENERATED_AT,
            config=ResearchPredictionMarketProbabilityBoundaryFilterConfig(),
        ),
    )
    unsafe_payload = dict(payload)
    unsafe_payload["question"] = "Will this leak?"
    with pytest.raises(ValueError, match="unsafe public"):
        research_prediction_market_probability_boundary_filter_payload(unsafe_payload)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = ResearchPredictionMarketProbabilityBoundaryFilterConfig()
    input_row = candidate()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.cohort = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchPredictionMarketProbabilityBoundaryFilterConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class CandidateSubclass(ResearchPredictionMarketProbabilityBoundaryFilterCandidate):
            pass


def test_static_module_is_report_only_and_has_no_forbidden_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_prediction_market_probability_boundary_filter_report.py",
    ).read_text(encoding="utf-8")
    lowered_source = source.lower()
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "database",
        "persist",
        "private_key",
        "recommendation",
        "sizing",
        "notional",
        "position",
    )

    assert not [term for term in forbidden_terms if term in lowered_source]

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


def _contains_forbidden_public_key(value: object) -> bool:
    forbidden_fragments = (
        "_id",
        "id_",
        "slug",
        "question",
        "source",
        "storage",
        "auth",
        "trading",
    )
    if isinstance(value, dict):
        return any(
            any(fragment in key.lower() for fragment in forbidden_fragments)
            or _contains_forbidden_public_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_public_key(item) for item in value)
    return False
