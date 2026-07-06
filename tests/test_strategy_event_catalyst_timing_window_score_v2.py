from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_event_catalyst_timing_window_score_v2 as module
from polymarket_alpha_lab.strategy_event_catalyst_timing_window_score_v2 import (
    StrategyEventCatalystTimingWindowScoreV2Config,
    StrategyEventCatalystTimingWindowScoreV2Input,
    build_strategy_event_catalyst_timing_window_score_v2,
    strategy_event_catalyst_timing_window_score_v2_payload,
    validate_strategy_event_catalyst_timing_window_score_v2_public_payload,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    *,
    reference: str = "alpha-candidate",
    slug: str = "alpha-market",
    lead_hours: int = 36,
    catalyst_age_hours: int = 2,
    strength: Decimal = d("0.900000"),
) -> StrategyEventCatalystTimingWindowScoreV2Input:
    return StrategyEventCatalystTimingWindowScoreV2Input(
        candidate_reference=reference,
        market_slug=slug,
        evaluated_at=NOW - timedelta(minutes=5),
        event_start_at=NOW + timedelta(hours=lead_hours),
        catalyst_observed_at=NOW - timedelta(hours=catalyst_age_hours),
        catalyst_strength_score=strength,
        reason_codes=("source_reviewed",),
    )


def build_report(*rows: StrategyEventCatalystTimingWindowScoreV2Input):
    return build_strategy_event_catalyst_timing_window_score_v2(
        rows,
        config=StrategyEventCatalystTimingWindowScoreV2Config(),
        generated_at=NOW,
    )


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if not field.name.startswith("_"):
                assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if type(value) in (tuple, list):
        for item in value:
            assert_public_numeric_values_are_decimal(item)
        return
    assert type(value) not in (int, float)


def test_catalyst_window_scoring_passes_for_fresh_candidate_inside_window() -> None:
    report = build_report(candidate())

    assert report.status == "pass"
    assert report.candidate_count == d("1")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.average_catalyst_timing_window_score == d("0.975000")
    assert report.reason_codes == ("catalyst_timing_window_score_passed",)

    row = report.rows[0]
    assert row.hours_until_event == d("36.000000")
    assert row.catalyst_age_hours == d("2.000000")
    assert row.catalyst_window_score == d("1.000000")
    assert row.stale_catalyst_decay_score == d("1.000000")
    assert row.near_resolution_risk_score == d("1.000000")
    assert row.catalyst_timing_window_score == d("0.975000")
    assert row.status == "pass"
    assert "catalyst_window_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_stale_catalyst_decay_blocks_old_catalysts() -> None:
    fresh = candidate(reference="fresh-candidate", slug="fresh-market")
    stale = candidate(
        reference="stale-candidate",
        slug="stale-market",
        catalyst_age_hours=30,
        strength=d("1.000000"),
    )

    report = build_report(fresh, stale)
    stale_row = next(row for row in report.rows if row.market_slug == "stale-market")
    fresh_row = next(row for row in report.rows if row.market_slug == "fresh-market")

    assert stale_row.status == "blocked"
    assert stale_row.stale_catalyst_decay_score == d("0.000000")
    assert stale_row.catalyst_timing_window_score < fresh_row.catalyst_timing_window_score
    assert "stale_catalyst_decay_blocked" in stale_row.reason_codes
    assert report.status == "blocked"
    assert report.blocked_count == d("1")


def test_near_resolution_risk_blocks_events_too_close_to_resolution() -> None:
    report = build_report(candidate(lead_hours=2, strength=d("1.000000")))
    row = report.rows[0]

    assert row.status == "blocked"
    assert row.hours_until_event == d("2.000000")
    assert row.catalyst_window_score == d("0.000000")
    assert row.near_resolution_risk_score == d("0.000000")
    assert row.catalyst_timing_window_score == d("0.500000")
    assert "near_resolution_risk_blocked" in row.reason_codes


def test_serialization_uses_decimal_strings_and_is_json_ready() -> None:
    report = build_report(candidate())

    payload = strategy_event_catalyst_timing_window_score_v2_payload(report)
    assert payload == report.payload
    assert payload["candidate_count"] == "1"
    assert payload["average_catalyst_timing_window_score"] == "0.975000"
    assert payload["rows"][0]["catalyst_timing_window_score"] == "0.975000"
    assert payload["rows"][0]["event_start_at"] == (
        NOW + timedelta(hours=36)
    ).isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["derived_validation_digest"], str)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_public_numeric_values_are_decimals() -> None:
    config = StrategyEventCatalystTimingWindowScoreV2Config()
    item = candidate()
    report = build_report(item)

    assert_public_numeric_values_are_decimal(config)
    assert_public_numeric_values_are_decimal(item)
    assert_public_numeric_values_are_decimal(report)
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].catalyst_timing_window_score = d("0")  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_inputs_and_reports() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        StrategyEventCatalystTimingWindowScoreV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(candidate(), report_only=False)

    report = build_report(candidate())
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report(candidate())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_catalyst_timing_window_score"):
        replace(report, average_catalyst_timing_window_score=d("0.100000"))


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    unsafe_terms = (
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
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public payload"):
            validate_strategy_event_catalyst_timing_window_score_v2_public_payload(
                {f"{term}_field": "safe"},
            )
        with pytest.raises(ValueError, match="unsafe public payload"):
            validate_strategy_event_catalyst_timing_window_score_v2_public_payload(
                {"safe_field": f"contains-{term}"},
            )
        with pytest.raises(ValueError, match="unsafe public payload"):
            StrategyEventCatalystTimingWindowScoreV2Input(
                candidate_reference=f"alpha-{term}",
                market_slug="safe-market",
                evaluated_at=NOW,
                event_start_at=NOW + timedelta(hours=36),
                catalyst_observed_at=NOW - timedelta(hours=1),
                catalyst_strength_score=d("0.900000"),
            )


def test_no_unsafe_public_surfaces_are_exposed() -> None:
    unsafe_terms = (
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
    public_names = [name for name in dir(module) if not name.startswith("_")]
    for name in public_names:
        lowered = name.lower()
        assert all(term not in lowered for term in unsafe_terms), name

    for obj in (
        StrategyEventCatalystTimingWindowScoreV2Config,
        StrategyEventCatalystTimingWindowScoreV2Input,
        build_strategy_event_catalyst_timing_window_score_v2,
        strategy_event_catalyst_timing_window_score_v2_payload,
        validate_strategy_event_catalyst_timing_window_score_v2_public_payload,
    ):
        signature = inspect.signature(obj)
        for parameter in signature.parameters:
            lowered = parameter.lower()
            assert all(term not in lowered for term in unsafe_terms), parameter

    source = inspect.getsource(module)
    assert "requests" not in source
    assert "socket" not in source
    assert "sqlite" not in source
    assert "psycopg" not in source
    assert "supabase" not in source
