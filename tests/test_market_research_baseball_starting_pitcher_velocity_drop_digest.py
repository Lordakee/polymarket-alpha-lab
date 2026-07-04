from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 3, 17, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-baseball-starting-pitcher-velocity-drop-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_baseball_starting_pitcher_velocity_drop_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "velocity_drop_watch_threshold": d("1.500000"),
        "severe_velocity_drop_watch_threshold": d("2.500000"),
        "low_latest_velocity_threshold": d("91.000000"),
        "late_window_minutes": d("45.000000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBaseballStartingPitcherVelocityDropDigestConfig(
        **values,
    )


def observation(
    pitcher_key: str = "pitcher.cole",
    pitcher_name: str = "Gerrit Cole",
    team_key: str = "nyy",
    game_key: str = "mlb.nyy.bos.20260703",
    *,
    observed_at: datetime = BASE_OBSERVED_AT,
    scheduled_start_at: datetime = GENERATED_AT + timedelta(minutes=60),
    baseline_fastball_velocity_mph: Decimal = d("96.000000"),
    latest_fastball_velocity_mph: Decimal = d("95.200000"),
    source_count: Decimal = d("2.000000"),
    source_config_version: str = "starting-pitcher-velocity-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBaseballStartingPitcherVelocityDropObservation(
        pitcher_key=pitcher_key,
        pitcher_name=pitcher_name,
        team_key=team_key,
        game_key=game_key,
        observed_at=observed_at,
        scheduled_start_at=scheduled_start_at,
        baseline_fastball_velocity_mph=baseline_fastball_velocity_mph,
        latest_fastball_velocity_mph=latest_fastball_velocity_mph,
        source_count=source_count,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations, **overrides):
    digest = module()
    values = {
        "observations": observations,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_baseball_starting_pitcher_velocity_drop_digest(
        **values,
    )


def test_digest_flags_starting_pitcher_velocity_drop_context() -> None:
    report = build_report(
        observation(
            "pitcher.cole",
            "Gerrit Cole",
            "nyy",
            "mlb.nyy.bos.20260703",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=30),
            baseline_fastball_velocity_mph=d("96.800000"),
            latest_fastball_velocity_mph=d("94.100000"),
            source_count=d("1.000000"),
            source_config_version="velocity-feed-v2",
        ),
        observation(
            "pitcher.webb",
            "Logan Webb",
            "sf",
            "mlb.sf.lad.20260703",
            observed_at=GENERATED_AT - timedelta(minutes=50),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=120),
            baseline_fastball_velocity_mph=d("93.000000"),
            latest_fastball_velocity_mph=d("90.900000"),
            source_count=d("3.000000"),
            source_config_version="velocity-feed-v1",
        ),
        observation(
            "pitcher.kirby",
            "George Kirby",
            "sea",
            "mlb.sea.hou.20260703",
            observed_at=GENERATED_AT - timedelta(minutes=75),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=150),
            baseline_fastball_velocity_mph=d("95.100000"),
            latest_fastball_velocity_mph=d("94.900000"),
            source_count=d("4.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_baseball_starting_pitcher_velocity_drop_digest"
    )
    assert report.pitcher_count == d("3.000000")
    assert report.watch_pitcher_count == d("2.000000")
    assert report.clear_pitcher_count == d("1.000000")
    assert report.velocity_drop_pitcher_count == d("2.000000")
    assert report.severe_velocity_drop_pitcher_count == d("1.000000")
    assert report.low_recent_velocity_pitcher_count == d("1.000000")
    assert report.late_observation_pitcher_count == d("1.000000")
    assert report.thin_source_pitcher_count == d("1.000000")
    assert report.max_velocity_drop_mph == d("2.700000")
    assert report.reason_codes == (
        "baseball_starting_pitcher_velocity_drop_late_window",
        "baseball_starting_pitcher_velocity_drop_low_recent_velocity",
        "baseball_starting_pitcher_velocity_drop_severe_drop",
        "baseball_starting_pitcher_velocity_drop_thin_sources",
        "baseball_starting_pitcher_velocity_drop_watch_drop",
    )
    assert report.reason_code_counts == (
        module().MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
            reason_code="baseball_starting_pitcher_velocity_drop_late_window",
            pitcher_count=d("1.000000"),
            pitcher_ratio=d("0.333333"),
        ),
        module().MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
            reason_code="baseball_starting_pitcher_velocity_drop_low_recent_velocity",
            pitcher_count=d("1.000000"),
            pitcher_ratio=d("0.333333"),
        ),
        module().MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
            reason_code="baseball_starting_pitcher_velocity_drop_severe_drop",
            pitcher_count=d("1.000000"),
            pitcher_ratio=d("0.333333"),
        ),
        module().MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
            reason_code="baseball_starting_pitcher_velocity_drop_thin_sources",
            pitcher_count=d("1.000000"),
            pitcher_ratio=d("0.333333"),
        ),
        module().MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
            reason_code="baseball_starting_pitcher_velocity_drop_watch_drop",
            pitcher_count=d("1.000000"),
            pitcher_ratio=d("0.333333"),
        ),
    )
    assert report.source_config_versions == (
        ("pitcher.cole", "velocity-feed-v2"),
        ("pitcher.kirby", "starting-pitcher-velocity-source-v0"),
        ("pitcher.webb", "velocity-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.pitcher_key for row in report.rows) == (
        "pitcher.cole",
        "pitcher.webb",
        "pitcher.kirby",
    )

    severe = report.rows[0]
    assert severe.pitcher_name == "Gerrit Cole"
    assert severe.team_key == "nyy"
    assert severe.game_key == "mlb.nyy.bos.20260703"
    assert severe.minutes_until_start == d("30.000000")
    assert severe.velocity_drop_mph == d("2.700000")
    assert severe.digest_status == "watch"
    assert severe.reason_codes == (
        "baseball_starting_pitcher_velocity_drop_late_window",
        "baseball_starting_pitcher_velocity_drop_severe_drop",
        "baseball_starting_pitcher_velocity_drop_thin_sources",
    )

    watch = report.rows[1]
    assert watch.velocity_drop_mph == d("2.100000")
    assert watch.reason_codes == (
        "baseball_starting_pitcher_velocity_drop_low_recent_velocity",
        "baseball_starting_pitcher_velocity_drop_watch_drop",
    )

    clear = report.rows[2]
    assert clear.digest_status == "clear"
    assert clear.reason_codes == ("baseball_starting_pitcher_velocity_drop_clear",)


def test_digest_passes_for_empty_stable_and_improved_velocity_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.pitcher_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.max_velocity_drop_mph is None
    assert empty_report.reason_codes == (
        "baseball_starting_pitcher_velocity_drop_empty",
    )

    stable_report = build_report(
        observation(
            "pitcher.alpha",
            "Alpha Starter",
            "lad",
            "mlb.lad.sd.20260703",
            baseline_fastball_velocity_mph=d("94.500000"),
            latest_fastball_velocity_mph=d("94.300000"),
        ),
        observation(
            "pitcher.beta",
            "Beta Starter",
            "bos",
            "mlb.bos.tb.20260703",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=15),
            baseline_fastball_velocity_mph=d("92.000000"),
            latest_fastball_velocity_mph=d("92.400000"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "baseball_starting_pitcher_velocity_drop_passed",
    )
    assert tuple((row.pitcher_key, row.velocity_drop_mph) for row in stable_report.rows) == (
        ("pitcher.alpha", d("0.200000")),
        ("pitcher.beta", d("0.000000")),
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "pitcher.beta",
        "Beta Starter",
        "bos",
        "mlb.bos.nyy.20260703",
        baseline_fastball_velocity_mph=d("95.000000"),
        latest_fastball_velocity_mph=d("92.900000"),
    )
    second = observation(
        "pitcher.alpha",
        "Alpha Starter",
        "lad",
        "mlb.lad.sf.20260703",
        scheduled_start_at=GENERATED_AT + timedelta(minutes=20),
        baseline_fastball_velocity_mph=d("96.000000"),
        latest_fastball_velocity_mph=d("93.300000"),
        source_count=d("1.000000"),
    )
    third = observation(
        "pitcher.gamma",
        "Gamma Starter",
        "stl",
        "mlb.stl.chc.20260703",
        baseline_fastball_velocity_mph=d("94.000000"),
        latest_fastball_velocity_mph=d("93.900000"),
    )

    forward = build_report(first, second, third)
    reverse = build_report(third, second, first)

    assert forward == reverse
    assert tuple(row.pitcher_key for row in forward.rows) == (
        "pitcher.alpha",
        "pitcher.beta",
        "pitcher.gamma",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))


def test_payload_uses_six_decimal_json_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        observation(
            "pitcher.payload",
            "Payload Starter",
            "sea",
            "mlb.sea.hou.20260703",
            observed_at=datetime(2026, 7, 3, 12, 30, tzinfo=timezone(timedelta(hours=-4))),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=75),
            baseline_fastball_velocity_mph=d("95.000000"),
            latest_fastball_velocity_mph=d("93.400000"),
        ),
    )

    payload = digest.market_research_baseball_starting_pitcher_velocity_drop_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["pitcher_count"] == "1.000000"
    assert payload["velocity_drop_watch_threshold"] == "1.500000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T16:30:00+00:00"
    assert payload["rows"][0]["minutes_until_start"] == "75.000000"
    assert payload["rows"][0]["velocity_drop_mph"] == "1.600000"
    assert payload["reason_code_counts"][0]["pitcher_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, datetime) for value in _walk_payload_values(payload))

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
    ):
        assert forbidden not in payload_text


def test_dataclasses_validate_decimal_datetime_flags_consistency_and_types() -> None:
    digest = module()

    row_input = observation()
    with pytest.raises(FrozenInstanceError):
        row_input.latest_fastball_velocity_mph = d("94.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="baseline_fastball_velocity_mph must be a Decimal"):
        observation(baseline_fastball_velocity_mph=95.2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 3, 17, 0))

    with pytest.raises(ValueError, match="pitcher_key must be a string"):
        observation(pitcher_key=_StringSubclass("pitcher.cole"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="velocity_drop_watch_threshold"):
        config(velocity_drop_watch_threshold=_DecimalSubclass("1.500000"))

    with pytest.raises(ValueError, match="severe_velocity_drop_watch_threshold"):
        config(
            velocity_drop_watch_threshold=d("2.500000"),
            severe_velocity_drop_watch_threshold=d("1.500000"),
        )

    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.500000"))

    with pytest.raises(ValueError, match="source_count must be whole"):
        observation(source_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row_input, paper_only=False)

    with pytest.raises(ValueError, match="observations must not contain duplicate"):
        build_report(
            observation(source_config_version="v0"),
            observation(source_config_version="v1"),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(minutes=1)))

    with pytest.raises(ValueError, match="scheduled_start_at must not precede observed_at"):
        observation(
            observed_at=GENERATED_AT,
            scheduled_start_at=GENERATED_AT - timedelta(minutes=1),
        )

    report = build_report(
        observation(
            "pitcher.gamma",
            "Gamma Starter",
            "stl",
            "mlb.stl.chc.20260703",
            baseline_fastball_velocity_mph=d("94.000000"),
            latest_fastball_velocity_mph=d("92.300000"),
        ),
    )
    with pytest.raises(ValueError, match="velocity_drop_mph must match"):
        replace(report.rows[0], velocity_drop_mph=d("9.000000"))

    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["pitcher_count"] = d("2.000000")
    with pytest.raises(ValueError, match="pitcher_count"):
        digest.MarketResearchBaseballStartingPitcherVelocityDropDigestReport(
            **bad_report_values,
        )

    for public_record in (
        config(),
        row_input,
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_module_scope_has_no_io_live_trading_float_or_durable_store_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_baseball_starting_pitcher_velocity_drop_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()

    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "auth",
        "private",
        "secret",
        "token",
        "open(",
        "requests",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "sql",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
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
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_payload_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload_values(item)
    else:
        yield value
