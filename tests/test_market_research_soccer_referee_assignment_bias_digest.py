from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-soccer-referee-assignment-bias-digest-test-v0"


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_referee_assignment_bias_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "blocked_abs_bias_score_threshold": d("0.060000"),
        "watch_abs_bias_score_threshold": d("0.030000"),
        "minimum_historical_match_sample_threshold": d("8.000000"),
        "low_confidence_threshold": d("0.600000"),
        "stale_observation_seconds_threshold": d("7200.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchSoccerRefereeAssignmentBiasDigestConfig(**values)


def signal(
    fixture_id: str = "epl_mci_ars_20260704",
    referee_id: str = "ref_alpha",
    *,
    competition_id: str = "epl",
    home_team_id: str = "mci",
    away_team_id: str = "ars",
    source_ref: str = "official_bias_model",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    home_favorable_call_delta: Decimal = d("0.010000"),
    away_favorable_call_delta: Decimal = d("0.008000"),
    penalty_bias_delta: Decimal = d("0.000000"),
    card_bias_delta: Decimal = d("0.000000"),
    var_review_bias_delta: Decimal = d("0.000000"),
    historical_match_sample: Decimal = d("12.000000"),
    assignment_confidence: Decimal = d("0.950000"),
    signal_config_version: str = "soccer-referee-assignment-bias-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchSoccerRefereeAssignmentBiasDigestSignal(
        fixture_id=fixture_id,
        referee_id=referee_id,
        competition_id=competition_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        source_ref=source_ref,
        observed_at=observed_at,
        home_favorable_call_delta=home_favorable_call_delta,
        away_favorable_call_delta=away_favorable_call_delta,
        penalty_bias_delta=penalty_bias_delta,
        card_bias_delta=card_bias_delta,
        var_review_bias_delta=var_review_bias_delta,
        historical_match_sample=historical_match_sample,
        assignment_confidence=assignment_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    digest = module()
    values = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_soccer_referee_assignment_bias_digest(
        **values,
    )


def assert_no_float_or_int(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"numeric payload value is not a Decimal string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def test_assignment_bias_digest_flags_blocked_watch_stale_and_pass_rows() -> None:
    local_observed_at = datetime(
        2026,
        7,
        4,
        13,
        15,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    local_signal = signal(
        "epl_mci_ars_20260704",
        "ref_alpha",
        source_ref="local_bias_confirm",
        observed_at=local_observed_at,
        home_favorable_call_delta=d("0.080000"),
        away_favorable_call_delta=d("0.020000"),
        penalty_bias_delta=d("0.030000"),
        card_bias_delta=d("0.020000"),
        var_review_bias_delta=d("0.010000"),
        historical_match_sample=d("14.000000"),
        assignment_confidence=d("0.750000"),
        signal_config_version="soccer-referee-assignment-bias-feed-v1",
    )
    report = build_report(
        signal(
            "epl_mci_ars_20260704",
            "ref_alpha",
            source_ref="official_bias_model",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            home_favorable_call_delta=d("0.120000"),
            away_favorable_call_delta=d("0.010000"),
            penalty_bias_delta=d("0.050000"),
            card_bias_delta=d("0.040000"),
            var_review_bias_delta=d("0.020000"),
            historical_match_sample=d("18.000000"),
            assignment_confidence=d("0.900000"),
        ),
        local_signal,
        signal(
            "laliga_rma_bar_20260704",
            "ref_beta",
            competition_id="laliga",
            home_team_id="rma",
            away_team_id="bar",
            source_ref="away_bias_model",
            observed_at=GENERATED_AT - timedelta(minutes=35),
            home_favorable_call_delta=d("0.010000"),
            away_favorable_call_delta=d("0.070000"),
            penalty_bias_delta=d("-0.020000"),
            card_bias_delta=d("-0.010000"),
            var_review_bias_delta=d("-0.010000"),
            historical_match_sample=d("5.000000"),
            assignment_confidence=d("0.550000"),
        ),
        signal(
            "seriea_int_mil_20260704",
            "ref_gamma",
            competition_id="seriea",
            home_team_id="int",
            away_team_id="mil",
            source_ref="old_bias_model",
            observed_at=GENERATED_AT - timedelta(hours=4),
            home_favorable_call_delta=d("0.010000"),
            away_favorable_call_delta=d("0.005000"),
            historical_match_sample=d("16.000000"),
            assignment_confidence=d("0.900000"),
        ),
        signal(
            "ucl_psg_bay_20260704",
            "ref_delta",
            competition_id="ucl",
            home_team_id="psg",
            away_team_id="bay",
            source_ref="clear_bias_model",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
    )

    assert is_dataclass(report)
    assert local_signal.observed_at == datetime(2026, 7, 4, 17, 15, tzinfo=UTC)
    assert local_signal.observed_at.tzinfo is UTC
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_referee_assignment_bias_review"
    )
    assert report.fixture_count == d("4.000000")
    assert report.signal_count == d("5.000000")
    assert report.blocked_fixture_count == d("1.000000")
    assert report.watch_fixture_count == d("2.000000")
    assert report.pass_fixture_count == d("1.000000")
    assert report.stale_observation_fixture_count == d("1.000000")
    assert report.home_bias_fixture_count == d("1.000000")
    assert report.away_bias_fixture_count == d("1.000000")
    assert report.thin_sample_fixture_count == d("1.000000")
    assert report.low_confidence_fixture_count == d("1.000000")
    assert report.max_observation_age_seconds == d("14400.000000")
    assert report.max_abs_assignment_bias_score == d("0.075000")
    assert report.max_screening_priority_score == d("1.000000")
    assert report.reason_codes == (
        "soccer_referee_assignment_bias_stale_observation",
        "soccer_referee_assignment_bias_home_blocked",
        "soccer_referee_assignment_bias_away_watch",
        "soccer_referee_assignment_bias_thin_sample",
        "soccer_referee_assignment_bias_low_confidence",
    )
    assert report.reason_code_counts == (
        module().MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount(
            reason_code="soccer_referee_assignment_bias_stale_observation",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount(
            reason_code="soccer_referee_assignment_bias_home_blocked",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount(
            reason_code="soccer_referee_assignment_bias_away_watch",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount(
            reason_code="soccer_referee_assignment_bias_thin_sample",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount(
            reason_code="soccer_referee_assignment_bias_low_confidence",
            fixture_count=d("1.000000"),
        ),
    )
    assert report.signal_config_versions == (
        ("away_bias_model", "soccer-referee-assignment-bias-feed-v0"),
        ("clear_bias_model", "soccer-referee-assignment-bias-feed-v0"),
        ("local_bias_confirm", "soccer-referee-assignment-bias-feed-v1"),
        ("official_bias_model", "soccer-referee-assignment-bias-feed-v0"),
        ("old_bias_model", "soccer-referee-assignment-bias-feed-v0"),
    )

    assert tuple((row.fixture_id, row.referee_id, row.row_status) for row in report.rows) == (
        ("epl_mci_ars_20260704", "ref_alpha", "blocked"),
        ("laliga_rma_bar_20260704", "ref_beta", "watch"),
        ("seriea_int_mil_20260704", "ref_gamma", "watch"),
        ("ucl_psg_bay_20260704", "ref_delta", "pass"),
    )
    blocked = report.rows[0]
    assert blocked.signal_count == d("2.000000")
    assert blocked.observed_at_latest == datetime(2026, 7, 4, 17, 15, tzinfo=UTC)
    assert blocked.observation_age_seconds == d("2700.000000")
    assert blocked.historical_match_sample_max == d("18.000000")
    assert blocked.assignment_confidence_min == d("0.750000")
    assert blocked.assignment_confidence_max == d("0.900000")
    assert blocked.net_home_bias_score == d("0.075000")
    assert blocked.abs_assignment_bias_score == d("0.075000")
    assert blocked.screening_priority_score == d("1.000000")
    assert blocked.bias_direction == "home_favoring"
    assert blocked.reason_codes == ("soccer_referee_assignment_bias_home_blocked",)

    away_watch = report.rows[1]
    assert away_watch.net_home_bias_score == d("-0.037000")
    assert away_watch.bias_direction == "away_favoring"
    assert away_watch.screening_priority_score == d("0.616667")
    assert away_watch.reason_codes == (
        "soccer_referee_assignment_bias_away_watch",
        "soccer_referee_assignment_bias_thin_sample",
        "soccer_referee_assignment_bias_low_confidence",
    )

    stale = report.rows[2]
    assert stale.observation_age_seconds == d("14400.000000")
    assert stale.reason_codes == ("soccer_referee_assignment_bias_stale_observation",)
    assert report.rows[3].reason_codes == ("soccer_referee_assignment_bias_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_assignment_bias_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.fixture_count == d("0.000000")
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.reason_codes == ("soccer_referee_assignment_bias_empty",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.max_observation_age_seconds is None
    assert empty_report.max_abs_assignment_bias_score is None

    stable_report = build_report(
        signal(
            "epl_mci_ars_20260704",
            "ref_alpha",
            source_ref="official_current",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        signal(
            "seriea_int_mil_20260704",
            "ref_gamma",
            competition_id="seriea",
            home_team_id="int",
            away_team_id="mil",
            source_ref="official_second",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            home_favorable_call_delta=d("0.012000"),
            away_favorable_call_delta=d("0.010000"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("soccer_referee_assignment_bias_passed",)
    assert stable_report.reason_code_counts == ()
    assert tuple(row.row_status for row in stable_report.rows) == ("pass", "pass")


def test_assignment_bias_payload_uses_six_decimal_strings_and_utc_datetimes() -> None:
    report = build_report(
        signal(
            observed_at=datetime(
                2026,
                7,
                4,
                10,
                15,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            home_favorable_call_delta=d("0.020000"),
            away_favorable_call_delta=d("0.070000"),
            penalty_bias_delta=d("-0.020000"),
            card_bias_delta=d("-0.010000"),
            var_review_bias_delta=d("-0.010000"),
            historical_match_sample=d("7.000000"),
            assignment_confidence=d("0.700000"),
        ),
        generated_at=datetime(2026, 7, 4, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module().market_research_soccer_referee_assignment_bias_digest_payload(
        report,
    )

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T18:00:00Z"
    assert payload["fixture_count"] == "1.000000"
    assert payload["signal_count"] == "1.000000"
    assert payload["watch_fixture_count"] == "1.000000"
    assert payload["blocked_abs_bias_score_threshold"] == "0.060000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-04T17:15:00Z"
    assert payload["rows"][0]["observation_age_seconds"] == "2700.000000"
    assert payload["rows"][0]["net_home_bias_score"] == "-0.032000"
    assert payload["reason_code_counts"][0]["fixture_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int(payload)


def test_public_dataclasses_are_frozen_and_public_numerics_are_decimal() -> None:
    digest = module()

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_SOCCER_REFEREE_ASSIGNMENT_BIAS_DIGEST_CONFIG_VERSION",
        "MarketResearchSoccerRefereeAssignmentBiasDigestConfig",
        "MarketResearchSoccerRefereeAssignmentBiasDigestSignal",
        "MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount",
        "MarketResearchSoccerRefereeAssignmentBiasDigestRow",
        "MarketResearchSoccerRefereeAssignmentBiasDigestReport",
        "build_market_research_soccer_referee_assignment_bias_digest",
        "market_research_soccer_referee_assignment_bias_digest_payload",
    )
    for name in digest.__all__:
        value = getattr(digest, name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(signal())
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].fixture_id = "changed"

    numeric_name_parts = (
        "_threshold",
        "_seconds",
        "_sample",
        "_score",
        "_confidence",
        "_delta",
    )
    for public_type in (
        digest.MarketResearchSoccerRefereeAssignmentBiasDigestConfig,
        digest.MarketResearchSoccerRefereeAssignmentBiasDigestSignal,
        digest.MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount,
        digest.MarketResearchSoccerRefereeAssignmentBiasDigestRow,
        digest.MarketResearchSoccerRefereeAssignmentBiasDigestReport,
    ):
        for field in fields(public_type):
            if field.name.endswith("_count") or any(
                part in field.name for part in numeric_name_parts
            ):
                assert "Decimal" in str(field.type)


def test_assignment_bias_validation_rejects_bad_values_duplicates_and_drift() -> None:
    digest = module()

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 17, 0))

    with pytest.raises(ValueError, match="fixture_id must be a string"):
        signal(fixture_id=_StringSubclass("fixture_subclass"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 4, 18, tzinfo=UTC))

    with pytest.raises(ValueError, match="home_favorable_call_delta must be a Decimal"):
        signal(home_favorable_call_delta=_DecimalSubclass("0.010000"))

    with pytest.raises(ValueError, match="source_ref contains unsafe source detail"):
        signal(source_ref="source_wallet_hint")

    with pytest.raises(ValueError, match="signal readonly must be True"):
        signal(readonly=False)

    with pytest.raises(
        ValueError,
        match="blocked_abs_bias_score_threshold must be at least watch threshold",
    ):
        config(
            blocked_abs_bias_score_threshold=d("0.020000"),
            watch_abs_bias_score_threshold=d("0.030000"),
        )

    with pytest.raises(ValueError, match="duplicate fixture/referee/source triples"):
        build_report(signal(), signal())

    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    row = build_report(signal()).rows[0]
    with pytest.raises(ValueError, match="row status must match reason codes"):
        replace(row, row_status="blocked")

    with pytest.raises(ValueError, match="reason_codes must be sorted by reason code rank"):
        replace(
            row,
            row_status="watch",
            reason_codes=(
                "soccer_referee_assignment_bias_low_confidence",
                "soccer_referee_assignment_bias_stale_observation",
            ),
        )

    with pytest.raises(ValueError, match="report must be exactly"):
        digest.market_research_soccer_referee_assignment_bias_digest_payload(object())


def test_assignment_bias_module_stays_pure_report_only_and_unwired() -> None:
    module_path = Path(__file__).resolve().parents[1] / (
        "src/polymarket_alpha_lab/"
        "market_research_soccer_referee_assignment_bias_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "live trading",
        "payload_json",
        "wallet",
        "broker",
        "order",
        "auth",
        "secret",
        "private",
        "cancel",
        "replace",
        "exchange",
        "trade",
        "execute",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "supabase",
        "open(",
        "path(",
        "subprocess",
        "sqlite3",
    )
    assert all(term not in lowered for term in forbidden_terms)

    parsed = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(parsed)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "supabase",
        "sqlite3",
        "subprocess",
        "pathlib",
    } & imports
