from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
KICKOFF_AT = datetime(2026, 7, 4, 19, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-soccer-var-check-delay-digest-test-v0"


class _DateTimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_var_check_delay_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "var_review_rate_delta_watch": d("0.120000"),
        "var_review_rate_delta_blocked": d("0.250000"),
        "average_check_duration_seconds_watch": d("60"),
        "average_check_duration_seconds_blocked": d("120"),
        "referee_var_propensity_watch": d("0.650000"),
        "referee_var_propensity_blocked": d("0.850000"),
        "source_delay_age_seconds_watch": d("20"),
        "source_delay_age_seconds_blocked": d("45"),
        "incident_density_watch": d("0.500000"),
        "incident_density_blocked": d("0.800000"),
        "source_disagreement_count_watch": d("1"),
        "source_disagreement_count_blocked": d("2"),
    }
    values.update(overrides)
    return digest.MarketResearchSoccerVarCheckDelayDigestConfig(**values)


def signal(
    match_ref: str = "match_alpha",
    league_key: str = "epl",
    market_slug: str = "epl-alpha-beta-var-delay",
    source_ref: str = "public_var_feed",
    *,
    kickoff_at: datetime = KICKOFF_AT,
    source_timestamp: datetime = GENERATED_AT - timedelta(minutes=30),
    var_review_rate_delta: Decimal = d("0.020000"),
    average_check_duration_seconds: Decimal = d("25.000000"),
    referee_var_propensity: Decimal = d("0.250000"),
    source_delay_age_seconds: Decimal = d("5.000000"),
    incident_density: Decimal = d("0.100000"),
    source_disagreement_count: Decimal = d("0"),
    upstream_reason_codes: tuple[str, ...] = (),
    signal_config_version: str = "soccer-var-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchSoccerVarCheckDelayDigestSignal(
        match_ref=match_ref,
        league_key=league_key,
        market_slug=market_slug,
        source_ref=source_ref,
        kickoff_at=kickoff_at,
        source_timestamp=source_timestamp,
        var_review_rate_delta=var_review_rate_delta,
        average_check_duration_seconds=average_check_duration_seconds,
        referee_var_propensity=referee_var_propensity,
        source_delay_age_seconds=source_delay_age_seconds,
        incident_density=incident_density,
        source_disagreement_count=source_disagreement_count,
        upstream_reason_codes=upstream_reason_codes,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals, **overrides):
    digest = module()
    values = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_soccer_var_check_delay_digest(**values)


def test_digest_flags_var_delay_pressure_with_deterministic_rows_reasons_counts() -> None:
    report = build_report(
        signal(
            "match_beta",
            "epl",
            "epl-man-city-arsenal-var-delay",
            "stadium_timing_public",
            source_timestamp=GENERATED_AT - timedelta(minutes=12),
            var_review_rate_delta=d("0.100000"),
            average_check_duration_seconds=d("45.000000"),
            referee_var_propensity=d("0.700000"),
            source_delay_age_seconds=d("10.000000"),
            incident_density=d("0.300000"),
            source_disagreement_count=d("0"),
            signal_config_version="soccer-var-feed-v0",
        ),
        signal(
            "match_beta",
            "epl",
            "epl-man-city-arsenal-var-delay",
            "broadcast_public",
            source_timestamp=GENERATED_AT - timedelta(minutes=3),
            var_review_rate_delta=d("0.300000"),
            average_check_duration_seconds=d("140.000000"),
            referee_var_propensity=d("0.900000"),
            source_delay_age_seconds=d("55.000000"),
            incident_density=d("0.850000"),
            source_disagreement_count=d("2"),
            upstream_reason_codes=("clock_reconciled", "var_audio_late"),
            signal_config_version="soccer-var-feed-v1",
        ),
        signal(
            "match_gamma",
            "mls",
            "mls-austin-dallas-var-review",
            "gamma_feed",
            source_timestamp=GENERATED_AT - timedelta(minutes=7),
            var_review_rate_delta=d("0.130000"),
            average_check_duration_seconds=d("70.000000"),
            referee_var_propensity=d("0.400000"),
            source_delay_age_seconds=d("25.000000"),
            incident_density=d("0.400000"),
            source_disagreement_count=d("1"),
        ),
        signal(
            "match_alpha",
            "ucl",
            "ucl-benfica-porto-match-result",
            "alpha_feed",
        ),
    )

    digest = module()
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_var_check_delay_review"
    )
    assert report.match_count == d("3.000000")
    assert report.clear_match_count == d("1.000000")
    assert report.watch_match_count == d("1.000000")
    assert report.blocked_match_count == d("1.000000")
    assert report.signal_count == d("4.000000")
    assert report.var_review_rate_delta_match_count == d("2.000000")
    assert report.average_check_duration_match_count == d("2.000000")
    assert report.referee_var_propensity_match_count == d("1.000000")
    assert report.source_delay_age_match_count == d("2.000000")
    assert report.incident_density_match_count == d("1.000000")
    assert report.source_disagreement_match_count == d("2.000000")
    assert report.upstream_reason_match_count == d("1.000000")
    assert report.risk_score == d("1.000000")
    assert report.max_var_review_rate_delta_observed == d("0.300000")
    assert report.max_average_check_duration_seconds == d("140.000000")
    assert report.max_referee_var_propensity_observed == d("0.900000")
    assert report.max_source_delay_age_seconds == d("55.000000")
    assert report.max_incident_density_observed == d("0.850000")
    assert report.max_source_disagreement_count == d("2.000000")
    assert report.reason_codes == (
        "soccer_var_check_delay_source_disagreement_blocked",
        "soccer_var_check_delay_source_delay_age_blocked",
        "soccer_var_check_delay_review_rate_delta_blocked",
        "soccer_var_check_delay_average_check_duration_blocked",
        "soccer_var_check_delay_referee_propensity_blocked",
        "soccer_var_check_delay_incident_density_blocked",
        "soccer_var_check_delay_source_disagreement_watch",
        "soccer_var_check_delay_source_delay_age_watch",
        "soccer_var_check_delay_review_rate_delta_watch",
        "soccer_var_check_delay_average_check_duration_watch",
        "soccer_var_check_delay_upstream_reason_present",
    )
    assert report.reason_code_counts == (
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_source_disagreement_blocked",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_source_delay_age_blocked",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_review_rate_delta_blocked",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_average_check_duration_blocked",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_referee_propensity_blocked",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_incident_density_blocked",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_source_disagreement_watch",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_source_delay_age_watch",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_review_rate_delta_watch",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_average_check_duration_watch",
            match_count=d("1"),
        ),
        digest.MarketResearchSoccerVarCheckDelayDigestReasonCodeCount(
            reason_code="soccer_var_check_delay_upstream_reason_present",
            match_count=d("1"),
        ),
    )
    assert report.signal_config_versions == (
        ("alpha_feed", "soccer-var-feed-v0"),
        ("broadcast_public", "soccer-var-feed-v1"),
        ("gamma_feed", "soccer-var-feed-v0"),
        ("stadium_timing_public", "soccer-var-feed-v0"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.match_ref, row.league_key, row.market_slug) for row in report.rows) == (
        ("match_beta", "epl", "epl-man-city-arsenal-var-delay"),
        ("match_gamma", "mls", "mls-austin-dallas-var-review"),
        ("match_alpha", "ucl", "ucl-benfica-porto-match-result"),
    )
    beta = report.rows[0]
    assert beta.latest_source_timestamp == GENERATED_AT - timedelta(minutes=3)
    assert beta.update_age_seconds == d("180.000000")
    assert beta.var_review_rate_delta_max == d("0.300000")
    assert beta.average_check_duration_seconds_max == d("140.000000")
    assert beta.referee_var_propensity_max == d("0.900000")
    assert beta.source_delay_age_seconds_max == d("55.000000")
    assert beta.incident_density_max == d("0.850000")
    assert beta.source_disagreement_count_max == d("2.000000")
    assert beta.risk_score == d("1.000000")
    assert beta.upstream_reason_codes == ("clock_reconciled", "var_audio_late")
    assert beta.digest_status == "blocked"

    gamma = report.rows[1]
    assert gamma.digest_status == "watch"
    assert gamma.reason_codes == (
        "soccer_var_check_delay_source_disagreement_watch",
        "soccer_var_check_delay_source_delay_age_watch",
        "soccer_var_check_delay_review_rate_delta_watch",
        "soccer_var_check_delay_average_check_duration_watch",
    )

    alpha = report.rows[2]
    assert alpha.digest_status == "clear"
    assert alpha.reason_codes == ("soccer_var_check_delay_clear",)
    assert alpha.risk_score == d("0.000000")


def test_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.match_count == d("0.000000")
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.risk_score == d("0.000000")
    assert empty_report.reason_codes == ("soccer_var_check_delay_empty",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.max_var_review_rate_delta_observed is None
    assert empty_report.max_source_disagreement_count is None

    stable_report = build_report(
        signal(
            "match_stable",
            "serie_a",
            "serie-a-atalanta-roma-stable",
            "stable_feed",
            var_review_rate_delta=d("0.020000"),
            average_check_duration_seconds=d("20.000000"),
            referee_var_propensity=d("0.200000"),
            source_delay_age_seconds=d("5.000000"),
            incident_density=d("0.100000"),
            source_disagreement_count=d("0"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.risk_score == d("0.000000")
    assert stable_report.reason_codes == ("soccer_var_check_delay_passed",)
    assert stable_report.rows[0].digest_status == "clear"
    assert stable_report.rows[0].reason_codes == ("soccer_var_check_delay_clear",)


def test_payload_uses_utc_iso_and_six_decimal_strings() -> None:
    digest = module()
    report = build_report(
        signal(
            "match_payload",
            "laliga",
            "laliga-real-madrid-barcelona-var-check",
            "public_broadcast_ref",
            source_timestamp=datetime(
                2026,
                7,
                4,
                7,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            var_review_rate_delta=d("0.130000"),
            average_check_duration_seconds=d("70.000000"),
            source_delay_age_seconds=d("25.000000"),
            source_disagreement_count=d("1"),
        ),
    )

    payload = digest.market_research_soccer_var_check_delay_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["match_count"] == "1.000000"
    assert payload["risk_score"] == "0.359815"
    assert payload["rows"][0]["latest_source_timestamp"] == "2026-07-04T11:45:00+00:00"
    assert payload["rows"][0]["var_review_rate_delta_max"] == "0.130000"
    assert payload["rows"][0]["average_check_duration_seconds_max"] == "70.000000"
    assert payload["rows"][0]["source_disagreement_count_max"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def assert_no_floats(value: object) -> None:
        if isinstance(value, float):
            pytest.fail(f"float found in JSON payload: {value!r}")
        if isinstance(value, dict):
            for item in value.values():
                assert_no_floats(item)
        if isinstance(value, list):
            for item in value:
                assert_no_floats(item)

    assert_no_floats(payload)


def test_dataclasses_are_frozen_decimal_only_and_normalize_utc_datetimes() -> None:
    digest = module()
    sig = signal(
        source_timestamp=datetime(2026, 7, 4, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
        kickoff_at=datetime(2026, 7, 4, 15, 0, tzinfo=timezone(timedelta(hours=-4))),
        upstream_reason_codes=("zeta_code", "alpha_code"),
    )

    assert sig.source_timestamp == datetime(2026, 7, 4, 11, 30, tzinfo=UTC)
    assert sig.kickoff_at == KICKOFF_AT
    assert sig.source_timestamp.tzinfo is UTC
    assert sig.var_review_rate_delta == d("0.020000")
    assert sig.source_disagreement_count == d("0.000000")
    assert sig.upstream_reason_codes == ("alpha_code", "zeta_code")
    with pytest.raises(FrozenInstanceError):
        sig.market_slug = "other"  # type: ignore[misc]

    report = build_report(sig)
    for value in (config(), sig, report, report.rows[0]):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.endswith("_count") or field.name.endswith("_score"):
                assert type(field_value) is Decimal
            if field.name.endswith("_seconds") or field.name.endswith("_delta"):
                assert type(field_value) is Decimal
            if field.name.endswith("_propensity") or field.name.endswith("_density"):
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="Decimal"):
        signal(var_review_rate_delta=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="whole"):
        signal(source_disagreement_count=d("1.5"))
    with pytest.raises(ValueError, match="datetime"):
        signal(source_timestamp=_DateTimeSubclass(2026, 7, 4, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(source_timestamp=datetime(2026, 7, 4, 10, 0))

    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(sig, readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)

    with pytest.raises(TypeError):

        class BadSignal(digest.MarketResearchSoccerVarCheckDelayDigestSignal):
            pass


def test_rejects_invalid_inputs_duplicates_sensitive_text_and_future_observations() -> None:
    digest = module()

    with pytest.raises(ValueError, match="iterable"):
        digest.build_market_research_soccer_var_check_delay_digest(
            "not-signals",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        digest.build_market_research_soccer_var_check_delay_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        build_report(signal(source_timestamp=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        build_report(signal(), signal())
    with pytest.raises(ValueError, match="sensitive"):
        signal(source_ref="wallet_ref")
    with pytest.raises(ValueError, match="canonical"):
        signal(source_ref=_StringSubclass("public_ref"))
    with pytest.raises(ValueError, match="probability"):
        signal(referee_var_propensity=d("1.000001"))
    with pytest.raises(ValueError, match="threshold"):
        config(var_review_rate_delta_watch=d("0.300000"))
    with pytest.raises(ValueError, match="match group"):
        build_report(
            signal("match_mismatch", "epl", "slug_a", "source_a"),
            signal("match_mismatch", "epl", "slug_b", "source_b"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        digest.MarketResearchSoccerVarCheckDelayDigestRow(
            match_ref="match_manual",
            league_key="epl",
            market_slug="epl-manual-var-delay",
            kickoff_at=KICKOFF_AT,
            latest_source_timestamp=GENERATED_AT,
            signal_count=d("1"),
            update_age_seconds=d("0"),
            var_review_rate_delta_max=d("0"),
            average_check_duration_seconds_max=d("0"),
            referee_var_propensity_max=d("0"),
            source_delay_age_seconds_max=d("0"),
            incident_density_max=d("0"),
            source_disagreement_count_max=d("0"),
            upstream_reason_codes=(),
            risk_score=d("0"),
            digest_status="clear",
            reason_codes=(
                "soccer_var_check_delay_clear",
                "soccer_var_check_delay_clear",
            ),
        )


def test_module_is_pure_report_only_and_has_no_forbidden_surfaces() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_soccer_var_check_delay_digest.py"
    )
    source_text = path.read_text()
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    banned_import_roots = {
        "os",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
        "eth_account",
    }
    banned_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "run",
        "popen",
        "getenv",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(banned_import_roots)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    public_names = set(module().__all__)
    for token in (
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "broker",
        "private_key",
        "api_key",
        "secret",
        "trade",
        "trading",
        "exchange_mutation",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "supabase",
        "subprocess",
    ):
        assert token not in lowered
        assert all(token not in name.lower() for name in public_names)
