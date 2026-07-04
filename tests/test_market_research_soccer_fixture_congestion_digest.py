from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
BASE_KICKOFF_AT = datetime(2026, 7, 4, 19, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-soccer-fixture-congestion-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_fixture_congestion_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "min_rest_hours": d("72.000000"),
        "min_fixture_gap_hours": d("48.000000"),
        "max_fixture_count_lookback": d("3"),
        "high_travel_distance_km": d("1000.000000"),
        "min_source_count": d("2"),
        "max_conflicting_source_count": d("0"),
    }
    values.update(overrides)
    return digest.MarketResearchSoccerFixtureCongestionDigestConfig(**values)


def fixture(
    condition_id: str = "condition_alpha",
    league_key: str = "epl",
    team_key: str = "ars",
    fixture_ref: str = "alpha_fixture_old",
    *,
    kickoff_at: datetime = BASE_KICKOFF_AT,
    is_target_fixture: bool = True,
    travel_distance_km: Decimal = d("0"),
    source_count: Decimal = d("2"),
    conflicting_source_count: Decimal = d("0"),
    fixture_config_version: str = "soccer-fixture-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchSoccerFixtureCongestionDigestFixture(
        condition_id=condition_id,
        league_key=league_key,
        team_key=team_key,
        fixture_ref=fixture_ref,
        kickoff_at=kickoff_at,
        is_target_fixture=is_target_fixture,
        travel_distance_km=travel_distance_km,
        source_count=source_count,
        conflicting_source_count=conflicting_source_count,
        fixture_config_version=fixture_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*fixtures, **overrides):
    digest = module()
    values = {
        "fixtures": fixtures,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_soccer_fixture_congestion_digest(**values)


def test_digest_flags_rest_gap_fixture_density_travel_source_gap_and_conflicts() -> None:
    report = build_report(
        fixture(
            "condition_beta",
            "epl",
            "liv",
            "beta_old",
            kickoff_at=BASE_KICKOFF_AT - timedelta(hours=44),
            is_target_fixture=False,
            travel_distance_km=d("200.000000"),
            source_count=d("2"),
            fixture_config_version="soccer-fixture-feed-v0",
        ),
        fixture(
            "condition_beta",
            "epl",
            "liv",
            "beta_mid",
            kickoff_at=BASE_KICKOFF_AT - timedelta(hours=24),
            is_target_fixture=False,
            travel_distance_km=d("1200.000000"),
            source_count=d("2"),
            fixture_config_version="soccer-fixture-feed-v1",
        ),
        fixture(
            "condition_beta",
            "epl",
            "liv",
            "beta_target",
            kickoff_at=BASE_KICKOFF_AT,
            is_target_fixture=True,
            travel_distance_km=d("1500.000000"),
            source_count=d("1"),
            conflicting_source_count=d("1"),
            fixture_config_version="soccer-fixture-feed-v1",
        ),
        fixture(
            "condition_alpha",
            "ucl",
            "psg",
            "alpha_old",
            kickoff_at=BASE_KICKOFF_AT - timedelta(days=5),
            is_target_fixture=False,
            travel_distance_km=d("300.000000"),
            source_count=d("3"),
        ),
        fixture(
            "condition_alpha",
            "ucl",
            "psg",
            "alpha_target",
            kickoff_at=BASE_KICKOFF_AT,
            is_target_fixture=True,
            travel_distance_km=d("350.000000"),
            source_count=d("3"),
        ),
    )

    digest = module()
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_fixture_congestion_review"
    )
    assert report.condition_count == d("2")
    assert report.ready_condition_count == d("1")
    assert report.watch_condition_count == d("0")
    assert report.blocked_condition_count == d("1")
    assert report.fixture_count == d("5")
    assert report.rest_gap_condition_count == d("1")
    assert report.fixture_density_condition_count == d("1")
    assert report.travel_load_condition_count == d("1")
    assert report.source_gap_condition_count == d("1")
    assert report.conflict_condition_count == d("1")
    assert report.min_rest_hours_observed == d("24.000000")
    assert report.max_fixture_count_lookback_observed == d("3.000000")
    assert report.max_travel_distance_km_observed == d("1500.000000")
    assert report.reason_codes == (
        "soccer_fixture_congestion_conflicting_sources",
        "soccer_fixture_congestion_rest_gap_short",
        "soccer_fixture_congestion_fixture_density_high",
        "soccer_fixture_congestion_travel_load_high",
        "soccer_fixture_congestion_source_coverage_gap",
    )
    assert report.reason_code_counts == (
        digest.MarketResearchSoccerFixtureCongestionDigestReasonCodeCount(
            reason_code="soccer_fixture_congestion_conflicting_sources",
            condition_count=d("1"),
        ),
        digest.MarketResearchSoccerFixtureCongestionDigestReasonCodeCount(
            reason_code="soccer_fixture_congestion_rest_gap_short",
            condition_count=d("1"),
        ),
        digest.MarketResearchSoccerFixtureCongestionDigestReasonCodeCount(
            reason_code="soccer_fixture_congestion_fixture_density_high",
            condition_count=d("1"),
        ),
        digest.MarketResearchSoccerFixtureCongestionDigestReasonCodeCount(
            reason_code="soccer_fixture_congestion_travel_load_high",
            condition_count=d("1"),
        ),
        digest.MarketResearchSoccerFixtureCongestionDigestReasonCodeCount(
            reason_code="soccer_fixture_congestion_source_coverage_gap",
            condition_count=d("1"),
        ),
    )
    assert report.fixture_config_versions == (
        ("alpha_old", "soccer-fixture-feed-v0"),
        ("alpha_target", "soccer-fixture-feed-v0"),
        ("beta_mid", "soccer-fixture-feed-v1"),
        ("beta_old", "soccer-fixture-feed-v0"),
        ("beta_target", "soccer-fixture-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.league_key, row.team_key) for row in report.rows) == (
        ("condition_beta", "epl", "liv"),
        ("condition_alpha", "ucl", "psg"),
    )
    beta = report.rows[0]
    assert beta.target_fixture_ref == "beta_target"
    assert beta.target_kickoff_at == BASE_KICKOFF_AT
    assert beta.fixture_count_lookback == d("3.000000")
    assert beta.rest_hours_before_target == d("24.000000")
    assert beta.min_fixture_gap_hours_observed == d("20.000000")
    assert beta.travel_distance_km_latest == d("1500.000000")
    assert beta.source_count_latest == d("1.000000")
    assert beta.conflicting_source_count_latest == d("1.000000")
    assert beta.digest_status == "blocked"
    assert beta.reason_codes == (
        "soccer_fixture_congestion_conflicting_sources",
        "soccer_fixture_congestion_rest_gap_short",
        "soccer_fixture_congestion_fixture_density_high",
        "soccer_fixture_congestion_travel_load_high",
        "soccer_fixture_congestion_source_coverage_gap",
    )

    alpha = report.rows[1]
    assert alpha.fixture_count_lookback == d("1.000000")
    assert alpha.rest_hours_before_target == d("120.000000")
    assert alpha.min_fixture_gap_hours_observed == d("120.000000")
    assert alpha.digest_status == "ready"
    assert alpha.reason_codes == ("soccer_fixture_congestion_ready",)


def test_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.condition_count == d("0")
    assert empty_report.fixture_count == d("0")
    assert empty_report.reason_codes == ("soccer_fixture_congestion_empty",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.min_rest_hours_observed is None
    assert empty_report.max_fixture_count_lookback_observed is None
    assert empty_report.max_travel_distance_km_observed is None

    stable_report = build_report(
        fixture(
            "condition_stable",
            "laliga",
            "rma",
            "stable_old",
            kickoff_at=BASE_KICKOFF_AT - timedelta(days=6),
            is_target_fixture=False,
            travel_distance_km=d("250.000000"),
            source_count=d("2"),
        ),
        fixture(
            "condition_stable",
            "laliga",
            "rma",
            "stable_target",
            kickoff_at=BASE_KICKOFF_AT,
            is_target_fixture=True,
            travel_distance_km=d("300.000000"),
            source_count=d("2"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("soccer_fixture_congestion_passed",)
    assert stable_report.rows[0].digest_status == "ready"
    assert stable_report.rows[0].reason_codes == ("soccer_fixture_congestion_ready",)


def test_payload_helper_uses_json_ready_scalars_without_sensitive_terms() -> None:
    digest = module()
    report = build_report(
        fixture(
            "condition_payload",
            "seriea",
            "inter",
            "payload_old",
            kickoff_at=datetime(2026, 7, 2, 16, 0, tzinfo=timezone(timedelta(hours=-3))),
            travel_distance_km=d("400.000000"),
            source_count=d("2"),
            is_target_fixture=False,
        ),
        fixture(
            "condition_payload",
            "seriea",
            "inter",
            "payload_target",
            kickoff_at=BASE_KICKOFF_AT,
            is_target_fixture=True,
            travel_distance_km=d("1250.000000"),
            source_count=d("2"),
        ),
    )

    payload = digest.market_research_soccer_fixture_congestion_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["rows"][0]["rest_hours_before_target"] == "48.000000"
    assert payload["rows"][0]["target_kickoff_at"] == "2026-07-04T19:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
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
    ):
        assert token not in encoded.lower()


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal_only() -> None:
    cfg = config()
    item = fixture()
    report = build_report(fixture(travel_distance_km=d("1500.000000")))

    assert is_dataclass(cfg)
    assert is_dataclass(item)
    assert is_dataclass(report.rows[0])
    assert is_dataclass(report.reason_code_counts[0])
    with pytest.raises(FrozenInstanceError):
        cfg.min_rest_hours = d("80.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.source_count = d("3")  # type: ignore[misc]

    with pytest.raises(ValueError, match="min_rest_hours must be a Decimal"):
        config(min_rest_hours=72)
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        fixture(source_count=1)
    with pytest.raises(ValueError, match="travel_distance_km must be a Decimal"):
        fixture(travel_distance_km=_DecimalSubclass("100.000000"))

    numeric_field_names = {
        "min_rest_hours",
        "min_fixture_gap_hours",
        "max_fixture_count_lookback",
        "high_travel_distance_km",
        "min_source_count",
        "max_conflicting_source_count",
        "travel_distance_km",
        "source_count",
        "conflicting_source_count",
        "fixture_count_lookback",
        "rest_hours_before_target",
        "min_fixture_gap_hours_observed",
        "travel_distance_km_latest",
        "source_count_latest",
        "conflicting_source_count_latest",
        "condition_count",
        "ready_condition_count",
        "watch_condition_count",
        "blocked_condition_count",
        "fixture_count",
        "rest_gap_condition_count",
        "fixture_density_condition_count",
        "travel_load_condition_count",
        "source_gap_condition_count",
        "conflict_condition_count",
        "min_rest_hours_observed",
        "max_fixture_count_lookback_observed",
        "max_travel_distance_km_observed",
        "condition_count",
    }
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        for field_name, value in asdict(obj).items():
            if field_name in numeric_field_names and value is not None:
                assert type(value) is Decimal


def test_validation_rejects_unsafe_inputs_subclasses_future_times_and_inconsistent_reports() -> None:
    digest = module()

    with pytest.raises(ValueError, match="config_version must be a string"):
        config(config_version=_StringSubclass("test"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="target fixture must not be in the past"):
        build_report(fixture(is_target_fixture=True, kickoff_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="fixture_ref contains unsafe source detail"):
        fixture(fixture_ref="wallet_private_fixture")
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="fixtures must not contain duplicate"):
        build_report(fixture(fixture_ref="dup"), fixture(fixture_ref="dup"))
    with pytest.raises(ValueError, match="exactly one target fixture"):
        build_report(
            fixture("condition_multi", fixture_ref="multi_a", is_target_fixture=True),
            fixture("condition_multi", fixture_ref="multi_b", is_target_fixture=True),
        )

    report = build_report(
        fixture(
            "condition_blocked",
            "epl",
            "liv",
            "blocked_old",
            kickoff_at=BASE_KICKOFF_AT - timedelta(hours=44),
            is_target_fixture=False,
            travel_distance_km=d("200.000000"),
            source_count=d("2"),
        ),
        fixture(
            "condition_blocked",
            "epl",
            "liv",
            "blocked_target",
            kickoff_at=BASE_KICKOFF_AT,
            is_target_fixture=True,
            travel_distance_km=d("1500.000000"),
            source_count=d("1"),
            conflicting_source_count=d("1"),
        ),
        fixture(
            "condition_ready",
            "ucl",
            "psg",
            "ready_target",
            kickoff_at=BASE_KICKOFF_AT,
            is_target_fixture=True,
            travel_distance_km=d("200.000000"),
            source_count=d("2"),
        ),
    )
    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(report, recommended_next_step="continue_report_only_fixture_congestion")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        digest.MarketResearchSoccerFixtureCongestionDigestRow(
            condition_id="condition_manual",
            league_key="epl",
            team_key="ars",
            target_fixture_ref="manual_target",
            target_kickoff_at=BASE_KICKOFF_AT,
            fixture_count_lookback=d("3"),
            rest_hours_before_target=d("24.000000"),
            min_fixture_gap_hours_observed=d("20.000000"),
            travel_distance_km_latest=d("1500.000000"),
            source_count_latest=d("1"),
            conflicting_source_count_latest=d("1"),
            digest_status="blocked",
            reason_codes=(
                "soccer_fixture_congestion_rest_gap_short",
                "soccer_fixture_congestion_conflicting_sources",
            ),
        )


def test_module_exports_are_explicit_and_do_not_expose_live_trading_language() -> None:
    digest = module()
    source_path = Path(digest.__file__)
    tree = ast.parse(source_path.read_text())

    exported = set(digest.__all__)
    assert {
        "DEFAULT_MARKET_RESEARCH_SOCCER_FIXTURE_CONGESTION_DIGEST_CONFIG_VERSION",
        "MarketResearchSoccerFixtureCongestionDigestConfig",
        "MarketResearchSoccerFixtureCongestionDigestFixture",
        "MarketResearchSoccerFixtureCongestionDigestReasonCodeCount",
        "MarketResearchSoccerFixtureCongestionDigestRow",
        "MarketResearchSoccerFixtureCongestionDigestReport",
        "build_market_research_soccer_fixture_congestion_digest",
        "market_research_soccer_fixture_congestion_digest_payload",
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
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    public_text = "\n".join(
        name
        for name in exported
        if not name.startswith("_")
    ).lower()
    for token in ("wallet", "broker", "order", "auth", "signing", "live_trading"):
        assert token not in public_text
