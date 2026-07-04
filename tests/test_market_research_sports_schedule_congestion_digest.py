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
BASE_SCHEDULED_AT = datetime(2026, 7, 4, 19, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-sports-schedule-congestion-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_sports_schedule_congestion_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "min_rest_hours": d("48.000000"),
        "min_schedule_gap_hours": d("36.000000"),
        "max_event_count_window": d("3"),
        "high_travel_distance_km": d("1000.000000"),
        "min_source_count": d("2"),
        "max_conflicting_source_count": d("0"),
    }
    values.update(overrides)
    return digest.MarketResearchSportsScheduleCongestionDigestConfig(**values)


def scheduled_event(
    condition_id: str = "condition_alpha",
    sport_category: str = "basketball",
    league_key: str = "nba",
    team_key: str = "bos",
    event_ref: str = "alpha_event_old",
    *,
    scheduled_at: datetime = BASE_SCHEDULED_AT,
    is_target_event: bool = True,
    travel_distance_km: Decimal = d("0"),
    source_count: Decimal = d("2"),
    conflicting_source_count: Decimal = d("0"),
    event_config_version: str = "sports-schedule-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchSportsScheduleCongestionDigestEvent(
        condition_id=condition_id,
        sport_category=sport_category,
        league_key=league_key,
        team_key=team_key,
        event_ref=event_ref,
        scheduled_at=scheduled_at,
        is_target_event=is_target_event,
        travel_distance_km=travel_distance_km,
        source_count=source_count,
        conflicting_source_count=conflicting_source_count,
        event_config_version=event_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*events, **overrides):
    digest = module()
    values = {
        "events": events,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_sports_schedule_congestion_digest(**values)


def test_digest_flags_rest_density_travel_source_gap_and_conflicts() -> None:
    report = build_report(
        scheduled_event(
            "condition_beta",
            "football",
            "nfl",
            "kc",
            "beta_old",
            scheduled_at=BASE_SCHEDULED_AT - timedelta(hours=44),
            is_target_event=False,
            travel_distance_km=d("200.000000"),
            source_count=d("2"),
            event_config_version="sports-schedule-feed-v0",
        ),
        scheduled_event(
            "condition_beta",
            "football",
            "nfl",
            "kc",
            "beta_mid",
            scheduled_at=BASE_SCHEDULED_AT - timedelta(hours=24),
            is_target_event=False,
            travel_distance_km=d("1200.000000"),
            source_count=d("2"),
            event_config_version="sports-schedule-feed-v1",
        ),
        scheduled_event(
            "condition_beta",
            "football",
            "nfl",
            "kc",
            "beta_target",
            scheduled_at=BASE_SCHEDULED_AT,
            is_target_event=True,
            travel_distance_km=d("1500.000000"),
            source_count=d("1"),
            conflicting_source_count=d("1"),
            event_config_version="sports-schedule-feed-v1",
        ),
        scheduled_event(
            "condition_alpha",
            "basketball",
            "nba",
            "bos",
            "alpha_old",
            scheduled_at=BASE_SCHEDULED_AT - timedelta(days=5),
            is_target_event=False,
            travel_distance_km=d("300.000000"),
            source_count=d("3"),
        ),
        scheduled_event(
            "condition_alpha",
            "basketball",
            "nba",
            "bos",
            "alpha_target",
            scheduled_at=BASE_SCHEDULED_AT,
            is_target_event=True,
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
        "block_report_only_sports_schedule_congestion_review"
    )
    assert report.condition_count == d("2.000000")
    assert report.ready_condition_count == d("1.000000")
    assert report.watch_condition_count == d("0.000000")
    assert report.blocked_condition_count == d("1.000000")
    assert report.event_count == d("5.000000")
    assert report.rest_gap_condition_count == d("1.000000")
    assert report.schedule_density_condition_count == d("1.000000")
    assert report.travel_load_condition_count == d("1.000000")
    assert report.source_gap_condition_count == d("1.000000")
    assert report.conflict_condition_count == d("1.000000")
    assert report.min_rest_hours_observed == d("24.000000")
    assert report.max_event_count_window_observed == d("3.000000")
    assert report.max_travel_distance_km_observed == d("1500.000000")
    assert report.reason_codes == (
        "sports_schedule_congestion_conflicting_sources",
        "sports_schedule_congestion_rest_gap_short",
        "sports_schedule_congestion_event_density_high",
        "sports_schedule_congestion_travel_load_high",
        "sports_schedule_congestion_source_coverage_gap",
    )
    assert report.reason_code_counts == (
        digest.MarketResearchSportsScheduleCongestionDigestReasonCodeCount(
            reason_code="sports_schedule_congestion_conflicting_sources",
            condition_count=d("1.000000"),
        ),
        digest.MarketResearchSportsScheduleCongestionDigestReasonCodeCount(
            reason_code="sports_schedule_congestion_rest_gap_short",
            condition_count=d("1.000000"),
        ),
        digest.MarketResearchSportsScheduleCongestionDigestReasonCodeCount(
            reason_code="sports_schedule_congestion_event_density_high",
            condition_count=d("1.000000"),
        ),
        digest.MarketResearchSportsScheduleCongestionDigestReasonCodeCount(
            reason_code="sports_schedule_congestion_travel_load_high",
            condition_count=d("1.000000"),
        ),
        digest.MarketResearchSportsScheduleCongestionDigestReasonCodeCount(
            reason_code="sports_schedule_congestion_source_coverage_gap",
            condition_count=d("1.000000"),
        ),
    )
    assert report.event_config_versions == (
        ("alpha_old", "sports-schedule-feed-v0"),
        ("alpha_target", "sports-schedule-feed-v0"),
        ("beta_mid", "sports-schedule-feed-v1"),
        ("beta_old", "sports-schedule-feed-v0"),
        ("beta_target", "sports-schedule-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(
        (row.condition_id, row.sport_category, row.league_key, row.team_key)
        for row in report.rows
    ) == (
        ("condition_beta", "football", "nfl", "kc"),
        ("condition_alpha", "basketball", "nba", "bos"),
    )
    beta = report.rows[0]
    assert beta.target_event_ref == "beta_target"
    assert beta.target_scheduled_at == BASE_SCHEDULED_AT
    assert beta.event_count_window == d("3.000000")
    assert beta.rest_hours_before_target == d("24.000000")
    assert beta.min_schedule_gap_hours_observed == d("20.000000")
    assert beta.travel_distance_km_latest == d("1500.000000")
    assert beta.source_count_latest == d("1.000000")
    assert beta.conflicting_source_count_latest == d("1.000000")
    assert beta.digest_status == "blocked"
    assert beta.reason_codes == (
        "sports_schedule_congestion_conflicting_sources",
        "sports_schedule_congestion_rest_gap_short",
        "sports_schedule_congestion_event_density_high",
        "sports_schedule_congestion_travel_load_high",
        "sports_schedule_congestion_source_coverage_gap",
    )

    alpha = report.rows[1]
    assert alpha.event_count_window == d("1.000000")
    assert alpha.rest_hours_before_target == d("120.000000")
    assert alpha.min_schedule_gap_hours_observed == d("120.000000")
    assert alpha.digest_status == "ready"
    assert alpha.reason_codes == ("sports_schedule_congestion_ready",)


def test_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.condition_count == d("0.000000")
    assert empty_report.event_count == d("0.000000")
    assert empty_report.reason_codes == ("sports_schedule_congestion_empty",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.min_rest_hours_observed is None
    assert empty_report.max_event_count_window_observed is None
    assert empty_report.max_travel_distance_km_observed is None

    stable_report = build_report(
        scheduled_event(
            "condition_stable",
            "hockey",
            "nhl",
            "nyr",
            "stable_old",
            scheduled_at=BASE_SCHEDULED_AT - timedelta(days=6),
            is_target_event=False,
            travel_distance_km=d("250.000000"),
            source_count=d("2"),
        ),
        scheduled_event(
            "condition_stable",
            "hockey",
            "nhl",
            "nyr",
            "stable_target",
            scheduled_at=BASE_SCHEDULED_AT,
            is_target_event=True,
            travel_distance_km=d("300.000000"),
            source_count=d("2"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("sports_schedule_congestion_passed",)
    assert stable_report.rows[0].digest_status == "ready"
    assert stable_report.rows[0].reason_codes == ("sports_schedule_congestion_ready",)


def test_payload_helper_uses_json_ready_scalars_without_sensitive_terms() -> None:
    digest = module()
    report = build_report(
        scheduled_event(
            "condition_payload",
            "baseball",
            "mlb",
            "nyy",
            "payload_old",
            scheduled_at=datetime(2026, 7, 2, 16, 0, tzinfo=timezone(timedelta(hours=-3))),
            travel_distance_km=d("400.000000"),
            source_count=d("2"),
            is_target_event=False,
        ),
        scheduled_event(
            "condition_payload",
            "baseball",
            "mlb",
            "nyy",
            "payload_target",
            scheduled_at=BASE_SCHEDULED_AT,
            is_target_event=True,
            travel_distance_km=d("1250.000000"),
            source_count=d("2"),
        ),
    )

    payload = digest.market_research_sports_schedule_congestion_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["rows"][0]["rest_hours_before_target"] == "48.000000"
    assert payload["rows"][0]["target_scheduled_at"] == "2026-07-04T19:00:00+00:00"
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
    item = scheduled_event()
    report = build_report(scheduled_event(travel_distance_km=d("1500.000000")))

    assert is_dataclass(cfg)
    assert is_dataclass(item)
    assert is_dataclass(report.rows[0])
    assert is_dataclass(report.reason_code_counts[0])
    with pytest.raises(FrozenInstanceError):
        cfg.min_rest_hours = d("50.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.source_count = d("3")  # type: ignore[misc]

    with pytest.raises(ValueError, match="min_rest_hours must be a Decimal"):
        config(min_rest_hours=48)
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        scheduled_event(source_count=1)
    with pytest.raises(ValueError, match="travel_distance_km must be a Decimal"):
        scheduled_event(travel_distance_km=_DecimalSubclass("100.000000"))

    numeric_field_names = {
        "min_rest_hours",
        "min_schedule_gap_hours",
        "max_event_count_window",
        "high_travel_distance_km",
        "min_source_count",
        "max_conflicting_source_count",
        "travel_distance_km",
        "source_count",
        "conflicting_source_count",
        "event_count_window",
        "rest_hours_before_target",
        "min_schedule_gap_hours_observed",
        "travel_distance_km_latest",
        "source_count_latest",
        "conflicting_source_count_latest",
        "condition_count",
        "ready_condition_count",
        "watch_condition_count",
        "blocked_condition_count",
        "event_count",
        "rest_gap_condition_count",
        "schedule_density_condition_count",
        "travel_load_condition_count",
        "source_gap_condition_count",
        "conflict_condition_count",
        "min_rest_hours_observed",
        "max_event_count_window_observed",
        "max_travel_distance_km_observed",
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
    with pytest.raises(ValueError, match="target event must not be in the past"):
        build_report(scheduled_event(is_target_event=True, scheduled_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="event_ref contains unsafe source detail"):
        scheduled_event(event_ref="wallet_private_event")
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="events must not contain duplicate"):
        build_report(scheduled_event(event_ref="dup"), scheduled_event(event_ref="dup"))
    with pytest.raises(ValueError, match="exactly one target event"):
        build_report(
            scheduled_event("condition_multi", event_ref="multi_a", is_target_event=True),
            scheduled_event("condition_multi", event_ref="multi_b", is_target_event=True),
        )

    report = build_report(
        scheduled_event(
            "condition_blocked",
            "football",
            "nfl",
            "kc",
            "blocked_old",
            scheduled_at=BASE_SCHEDULED_AT - timedelta(hours=44),
            is_target_event=False,
            travel_distance_km=d("200.000000"),
            source_count=d("2"),
        ),
        scheduled_event(
            "condition_blocked",
            "football",
            "nfl",
            "kc",
            "blocked_target",
            scheduled_at=BASE_SCHEDULED_AT,
            is_target_event=True,
            travel_distance_km=d("1500.000000"),
            source_count=d("1"),
            conflicting_source_count=d("1"),
        ),
        scheduled_event(
            "condition_ready",
            "basketball",
            "nba",
            "bos",
            "ready_target",
            scheduled_at=BASE_SCHEDULED_AT,
            is_target_event=True,
            travel_distance_km=d("200.000000"),
            source_count=d("2"),
        ),
    )
    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(report, recommended_next_step="continue_report_only_schedule_congestion")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        digest.MarketResearchSportsScheduleCongestionDigestRow(
            condition_id="condition_manual",
            sport_category="football",
            league_key="nfl",
            team_key="kc",
            target_event_ref="manual_target",
            target_scheduled_at=BASE_SCHEDULED_AT,
            event_count_window=d("3"),
            rest_hours_before_target=d("24.000000"),
            min_schedule_gap_hours_observed=d("20.000000"),
            travel_distance_km_latest=d("1500.000000"),
            source_count_latest=d("1"),
            conflicting_source_count_latest=d("1"),
            digest_status="blocked",
            reason_codes=(
                "sports_schedule_congestion_rest_gap_short",
                "sports_schedule_congestion_conflicting_sources",
            ),
        )


def test_module_exports_are_explicit_and_omit_forbidden_source_substrings() -> None:
    digest = module()
    source_path = Path(digest.__file__)
    source = source_path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    exported = set(digest.__all__)
    assert {
        "DEFAULT_MARKET_RESEARCH_SPORTS_SCHEDULE_CONGESTION_DIGEST_CONFIG_VERSION",
        "MarketResearchSportsScheduleCongestionDigestConfig",
        "MarketResearchSportsScheduleCongestionDigestEvent",
        "MarketResearchSportsScheduleCongestionDigestReasonCodeCount",
        "MarketResearchSportsScheduleCongestionDigestRow",
        "MarketResearchSportsScheduleCongestionDigestReport",
        "build_market_research_sports_schedule_congestion_digest",
        "market_research_sports_schedule_congestion_digest_payload",
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
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    for token in (
        "live trading",
        "live_trading",
        "wallet",
        "broker",
        "order",
        "auth",
        "signing",
        "submit",
        "cancel",
        "replace",
        "exchange",
        "account",
        "advice",
        "private_key",
        "api_key",
        "secret",
        "database",
        "persist",
        "payload_json",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert token not in lowered
