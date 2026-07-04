from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
BASE_MATCH_START_AT = datetime(2026, 7, 5, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-soccer-travel-visa-availability-digest-test-v0"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_soccer_travel_visa_availability_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_travel_visa_availability_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "blocked_risk_score_threshold": d("0.800000"),
        "watch_risk_score_threshold": d("0.400000"),
        "max_input_age_hours": d("24.000000"),
        "min_source_count": d("2"),
        "max_conflicting_source_count": d("0"),
    }
    values.update(overrides)
    return module.MarketResearchSoccerTravelVisaAvailabilityDigestConfig(**values)


def signal(
    condition_id: str = "condition_alpha",
    market_slug: str = "will-player-start-alpha",
    competition_id: str = "ucl",
    match_ref: str = "alpha_match",
    team_id: str = "ars",
    player_id: str = "player_alpha",
    *,
    player_role: str = "starter",
    match_start_at: datetime = BASE_MATCH_START_AT,
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    visa_status: str = "cleared",
    travel_status: str = "cleared",
    player_availability_status: str = "available",
    risk_score: Decimal = d("0.100000"),
    source_count: Decimal = d("2"),
    conflicting_source_count: Decimal = d("0"),
    signal_ref: str = "local_travel_visa_feed_v0",
    signal_config_version: str = "soccer-travel-visa-availability-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchSoccerTravelVisaAvailabilityDigestSignal(
        condition_id=condition_id,
        market_slug=market_slug,
        competition_id=competition_id,
        match_ref=match_ref,
        team_id=team_id,
        player_id=player_id,
        player_role=player_role,
        match_start_at=match_start_at,
        observed_at=observed_at,
        visa_status=visa_status,
        travel_status=travel_status,
        player_availability_status=player_availability_status,
        risk_score=risk_score,
        source_count=source_count,
        conflicting_source_count=conflicting_source_count,
        signal_ref=signal_ref,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    module = api()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_market_research_soccer_travel_visa_availability_digest(
        **values,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in JSON payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_floats(child)
    if isinstance(value, list):
        for child in value:
            assert_no_floats(child)


def test_digest_flags_blocked_watch_and_pass_travel_visa_availability_risk() -> None:
    module = api()

    report = build_report(
        signal(
            "condition_watch",
            "will-player-start-watch",
            "cwc",
            "watch_match",
            "psg",
            "player_watch",
            player_role="rotation",
            match_start_at=BASE_MATCH_START_AT + timedelta(hours=2),
            observed_at=GENERATED_AT - timedelta(hours=1),
            visa_status="pending",
            travel_status="pending",
            player_availability_status="questionable",
            risk_score=d("0.550000"),
            source_count=d("2"),
            signal_config_version="soccer-travel-visa-availability-feed-v1",
        ),
        signal(
            "condition_pass",
            "will-player-start-pass",
            "epl",
            "pass_match",
            "mci",
            "player_pass",
            match_start_at=BASE_MATCH_START_AT + timedelta(hours=3),
            observed_at=GENERATED_AT - timedelta(minutes=30),
            risk_score=d("0.100000"),
            source_count=d("3"),
        ),
        signal(
            "condition_blocked",
            "will-player-start-blocked",
            "ucl",
            "blocked_match",
            "liv",
            "player_blocked",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=3),
            visa_status="denied",
            travel_status="blocked",
            player_availability_status="unavailable",
            risk_score=d("0.920000"),
            source_count=d("1"),
            conflicting_source_count=d("1"),
            signal_config_version="soccer-travel-visa-availability-feed-v2",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_travel_visa_availability_review"
    )
    assert report.signal_count == d("3.000000")
    assert report.pass_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.conflict_signal_count == d("1.000000")
    assert report.blocked_risk_signal_count == d("1.000000")
    assert report.watch_risk_signal_count == d("1.000000")
    assert report.visa_blocked_signal_count == d("1.000000")
    assert report.visa_watch_signal_count == d("1.000000")
    assert report.travel_blocked_signal_count == d("1.000000")
    assert report.travel_watch_signal_count == d("1.000000")
    assert report.player_unavailable_signal_count == d("1.000000")
    assert report.player_watch_signal_count == d("1.000000")
    assert report.source_gap_signal_count == d("1.000000")
    assert report.max_risk_score_observed == d("0.920000")
    assert report.average_risk_score == d("0.523333")
    assert report.reason_codes == (
        "soccer_travel_visa_availability_conflicting_sources",
        "soccer_travel_visa_availability_risk_score_blocked",
        "soccer_travel_visa_availability_visa_blocked",
        "soccer_travel_visa_availability_travel_blocked",
        "soccer_travel_visa_availability_player_unavailable",
        "soccer_travel_visa_availability_source_coverage_gap",
        "soccer_travel_visa_availability_risk_score_watch",
        "soccer_travel_visa_availability_visa_watch",
        "soccer_travel_visa_availability_travel_watch",
        "soccer_travel_visa_availability_player_watch",
    )
    assert report.reason_code_counts == (
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_conflicting_sources",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_risk_score_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_visa_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_travel_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_player_unavailable",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_source_coverage_gap",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_risk_score_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_visa_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_travel_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code="soccer_travel_visa_availability_player_watch",
            signal_count=d("1.000000"),
        ),
    )
    assert report.signal_config_versions == (
        ("blocked_match", "player_blocked", "soccer-travel-visa-availability-feed-v2"),
        ("pass_match", "player_pass", "soccer-travel-visa-availability-feed-v0"),
        ("watch_match", "player_watch", "soccer-travel-visa-availability-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.condition_id for row in report.rows) == (
        "condition_blocked",
        "condition_watch",
        "condition_pass",
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.reason_codes == (
        "soccer_travel_visa_availability_conflicting_sources",
        "soccer_travel_visa_availability_risk_score_blocked",
        "soccer_travel_visa_availability_visa_blocked",
        "soccer_travel_visa_availability_travel_blocked",
        "soccer_travel_visa_availability_player_unavailable",
        "soccer_travel_visa_availability_source_coverage_gap",
    )
    watch = report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.reason_codes == (
        "soccer_travel_visa_availability_risk_score_watch",
        "soccer_travel_visa_availability_visa_watch",
        "soccer_travel_visa_availability_travel_watch",
        "soccer_travel_visa_availability_player_watch",
    )
    passed = report.rows[2]
    assert passed.digest_status == "pass"
    assert passed.reason_codes == ("soccer_travel_visa_availability_clear",)


def test_empty_and_clear_inputs_pass_with_decimal_zeroes() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_codes == ("soccer_travel_visa_availability_empty",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.max_risk_score_observed is None
    assert empty_report.average_risk_score == d("0.000000")

    clear_report = build_report(
        signal(
            "condition_clear",
            "will-player-start-clear",
            "laliga",
            "clear_match",
            "rma",
            "player_clear",
            risk_score=d("0.150000"),
            source_count=d("3"),
        ),
    )

    assert clear_report.digest_status == "pass"
    assert clear_report.reason_codes == ("soccer_travel_visa_availability_passed",)
    assert clear_report.rows[0].digest_status == "pass"
    assert clear_report.rows[0].reason_codes == (
        "soccer_travel_visa_availability_clear",
    )


def test_payload_helper_uses_decimal_strings_utc_datetimes_and_no_sensitive_terms() -> None:
    module = api()
    report = build_report(
        signal(
            "condition_payload",
            "will-player-start-payload",
            "bundesliga",
            "payload_match",
            "bayern",
            "player_payload",
            match_start_at=datetime(2026, 7, 5, 21, 0, tzinfo=timezone(timedelta(hours=2))),
            observed_at=datetime(2026, 7, 4, 13, 30, tzinfo=timezone(timedelta(hours=2))),
            visa_status="pending",
            travel_status="cleared",
            player_availability_status="available",
            risk_score=d("0.400000"),
            source_count=d("2"),
        ),
    )

    payload = module.market_research_soccer_travel_visa_availability_digest_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["match_start_at"] == "2026-07-05T19:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T11:30:00+00:00"
    assert payload["rows"][0]["risk_score"] == "0.400000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    for token in (
        "wallet",
        "broker",
        "order",
        "account",
        "auth",
        "signing",
        "submit",
        "cancel",
        "advice",
        "database",
        "persist",
        "payload_json",
        "private_key",
        "exchange",
    ):
        assert token not in encoded.lower()


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal_only() -> None:
    cfg = config()
    item = signal()
    report = build_report(signal(risk_score=d("0.850000")))

    assert is_dataclass(cfg)
    assert is_dataclass(item)
    assert is_dataclass(report.rows[0])
    assert is_dataclass(report.reason_code_counts[0])
    with pytest.raises(FrozenInstanceError):
        cfg.blocked_risk_score_threshold = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.source_count = d("3")  # type: ignore[misc]

    with pytest.raises(ValueError, match="blocked_risk_score_threshold must be a Decimal"):
        config(blocked_risk_score_threshold=1)
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        signal(source_count=1)
    with pytest.raises(ValueError, match="risk_score must be a Decimal"):
        signal(risk_score=_DecimalSubclass("0.100000"))

    numeric_field_names = {
        "blocked_risk_score_threshold",
        "watch_risk_score_threshold",
        "max_input_age_hours",
        "min_source_count",
        "max_conflicting_source_count",
        "risk_score",
        "source_count",
        "conflicting_source_count",
        "signal_count",
        "pass_signal_count",
        "watch_signal_count",
        "blocked_signal_count",
        "conflict_signal_count",
        "blocked_risk_signal_count",
        "watch_risk_signal_count",
        "visa_blocked_signal_count",
        "visa_watch_signal_count",
        "travel_blocked_signal_count",
        "travel_watch_signal_count",
        "player_unavailable_signal_count",
        "player_watch_signal_count",
        "source_gap_signal_count",
        "max_risk_score_observed",
        "average_risk_score",
    }
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        assert is_dataclass(obj)
        assert obj.__dataclass_params__.frozen
        for field_name, value in asdict(obj).items():
            if field_name in numeric_field_names and value is not None:
                assert type(value) is Decimal
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(obj):
            if field.name in numeric_field_names:
                assert type(getattr(obj, field.name)) is Decimal


def test_validation_rejects_unsafe_inputs_subclasses_duplicates_and_stale_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version must be a string"):
        config(config_version=_StringSubclass("test"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observed_at exceeds max_input_age_hours"):
        build_report(signal(observed_at=GENERATED_AT - timedelta(hours=25)))
    with pytest.raises(ValueError, match="match_start_at must not be in the past"):
        build_report(signal(match_start_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="signal_ref contains unsafe source detail"):
        signal(signal_ref="wallet_private_feed")
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(signal(signal_ref="dup"), signal(signal_ref="dup"))

    report = build_report(
        signal(
            "condition_blocked",
            "will-player-start-blocked",
            "ucl",
            "blocked_match",
            "liv",
            "player_blocked",
            visa_status="denied",
            travel_status="blocked",
            player_availability_status="unavailable",
            risk_score=d("0.920000"),
            source_count=d("1"),
            conflicting_source_count=d("1"),
        ),
        signal(
            "condition_pass",
            "will-player-start-pass",
            "epl",
            "pass_match",
            "mci",
            "player_pass",
            match_start_at=BASE_MATCH_START_AT + timedelta(hours=2),
            risk_score=d("0.100000"),
            source_count=d("3"),
        ),
    )
    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(report, recommended_next_step="continue_report_only_soccer_visa_review")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        module.MarketResearchSoccerTravelVisaAvailabilityDigestRow(
            condition_id="condition_manual",
            market_slug="will-player-start-manual",
            competition_id="ucl",
            match_ref="manual_match",
            team_id="ars",
            player_id="player_manual",
            player_role="starter",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=1),
            visa_status="denied",
            travel_status="blocked",
            player_availability_status="available",
            risk_score=d("0.900000"),
            source_count=d("2"),
            conflicting_source_count=d("0"),
            signal_ref="manual_signal",
            digest_status="blocked",
            reason_codes=(
                "soccer_travel_visa_availability_visa_blocked",
                "soccer_travel_visa_availability_risk_score_blocked",
            ),
        )


def test_module_exports_are_explicit_and_do_not_expose_live_or_external_io_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text())

    exported = set(module.__all__)
    assert {
        "DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_VISA_AVAILABILITY_DIGEST_CONFIG_VERSION",
        "MarketResearchSoccerTravelVisaAvailabilityDigestConfig",
        "MarketResearchSoccerTravelVisaAvailabilityDigestSignal",
        "MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount",
        "MarketResearchSoccerTravelVisaAvailabilityDigestRow",
        "MarketResearchSoccerTravelVisaAvailabilityDigestReport",
        "build_market_research_soccer_travel_visa_availability_digest",
        "market_research_soccer_travel_visa_availability_digest_payload",
    } <= exported

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "patch",
        "commit",
        "execute",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "web3",
        "http",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    source = MODULE_PATH.read_text().lower()
    public_text = "\n".join(
        name
        for name in exported
        if not name.startswith("_")
    ).lower()
    for token in (
        "wallet",
        "broker",
        "order",
        "account",
        "auth",
        "signing",
        "live_trading",
        "exchange",
        "network",
        "secret",
        "database",
        "subprocess",
        "socket",
        "psycopg",
        "supabase",
        "private_key",
    ):
        assert token not in public_text
        assert token not in source
