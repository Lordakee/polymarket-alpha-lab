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
BASE_OBSERVED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-baseball-starting-pitcher-scratch-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_starting_pitcher_scratch_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "scratch_probability_watch_threshold": d("0.350000"),
        "lineup_confirmation_minute_threshold": d("90.000000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBaseballStartingPitcherScratchDigestConfig(**values)


def report_input(
    pitcher_key: str = "pitcher.cole",
    pitcher_name: str = "Gerrit Cole",
    team_key: str = "nyy",
    game_key: str = "mlb.nyy.bos.20260703",
    *,
    observed_at: datetime = BASE_OBSERVED_AT,
    scheduled_start_at: datetime = GENERATED_AT + timedelta(hours=2),
    scratch_probability: Decimal = d("0.120000"),
    source_count: Decimal = d("2.000000"),
    lineup_confirmed_at: datetime | None = GENERATED_AT - timedelta(minutes=45),
    replacement_pitcher_key: str | None = None,
    source_config_version: str = "starting-pitcher-scratch-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBaseballStartingPitcherScratchDigestInput(
        pitcher_key=pitcher_key,
        pitcher_name=pitcher_name,
        team_key=team_key,
        game_key=game_key,
        observed_at=observed_at,
        scheduled_start_at=scheduled_start_at,
        scratch_probability=scratch_probability,
        source_count=source_count,
        lineup_confirmed_at=lineup_confirmed_at,
        replacement_pitcher_key=replacement_pitcher_key,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*inputs, **overrides):
    digest = module()
    values = {
        "inputs": inputs,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_baseball_starting_pitcher_scratch_digest(**values)


def test_digest_flags_scratch_replacement_confirmation_and_source_risks() -> None:
    report = build_report(
        report_input(
            "pitcher.cole",
            "Gerrit Cole",
            "nyy",
            "mlb.nyy.bos.20260703",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            scratch_probability=d("0.420000"),
            source_count=d("1.000000"),
            lineup_confirmed_at=None,
            replacement_pitcher_key="pitcher.schmidt",
            source_config_version="scratch-feed-v1",
        ),
        report_input(
            "pitcher.webb",
            "Logan Webb",
            "sf",
            "mlb.sf.lad.20260703",
            observed_at=GENERATED_AT - timedelta(hours=1),
            scratch_probability=d("0.080000"),
            source_count=d("3.000000"),
            lineup_confirmed_at=GENERATED_AT - timedelta(minutes=20),
            source_config_version="scratch-feed-v0",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_baseball_starting_pitcher_scratch_digest"
    )
    assert report.pitcher_count == d("2")
    assert report.watch_pitcher_count == d("1")
    assert report.clear_pitcher_count == d("1")
    assert report.unconfirmed_pitcher_count == d("1")
    assert report.replacement_pitcher_count == d("1")
    assert report.thin_source_pitcher_count == d("1")
    assert report.high_scratch_probability_pitcher_count == d("1")
    assert report.max_scratch_probability == d("0.420000")
    assert report.reason_codes == (
        "baseball_starting_pitcher_scratch_high_probability",
        "baseball_starting_pitcher_scratch_replacement_named",
        "baseball_starting_pitcher_scratch_thin_sources",
        "baseball_starting_pitcher_scratch_unconfirmed_lineup",
    )
    assert report.reason_code_counts == (
        module().MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
            reason_code="baseball_starting_pitcher_scratch_high_probability",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
        module().MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
            reason_code="baseball_starting_pitcher_scratch_replacement_named",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
        module().MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
            reason_code="baseball_starting_pitcher_scratch_thin_sources",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
        module().MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
            reason_code="baseball_starting_pitcher_scratch_unconfirmed_lineup",
            pitcher_count=d("1"),
            pitcher_ratio=d("0.500000"),
        ),
    )
    assert report.source_config_versions == (
        ("pitcher.cole", "scratch-feed-v1"),
        ("pitcher.webb", "scratch-feed-v0"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.pitcher_key for row in report.rows) == (
        "pitcher.cole",
        "pitcher.webb",
    )
    risky = report.rows[0]
    assert risky.pitcher_name == "Gerrit Cole"
    assert risky.team_key == "nyy"
    assert risky.game_key == "mlb.nyy.bos.20260703"
    assert risky.minutes_until_start == d("120.000000")
    assert risky.lineup_confirmed_at is None
    assert risky.replacement_pitcher_key == "pitcher.schmidt"
    assert risky.digest_status == "watch"
    assert risky.reason_codes == (
        "baseball_starting_pitcher_scratch_high_probability",
        "baseball_starting_pitcher_scratch_replacement_named",
        "baseball_starting_pitcher_scratch_thin_sources",
        "baseball_starting_pitcher_scratch_unconfirmed_lineup",
    )

    stable = report.rows[1]
    assert stable.digest_status == "clear"
    assert stable.reason_codes == ("baseball_starting_pitcher_scratch_clear",)


def test_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.pitcher_count == d("0")
    assert empty_report.rows == ()
    assert empty_report.max_scratch_probability is None
    assert empty_report.reason_codes == ("baseball_starting_pitcher_scratch_empty",)

    stable_report = build_report(
        report_input("pitcher.alpha", "Alpha Starter", "lad", "mlb.lad.sd.20260703"),
        report_input(
            "pitcher.beta",
            "Beta Starter",
            "bos",
            "mlb.bos.tb.20260703",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            scratch_probability=d("0.050000"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("baseball_starting_pitcher_scratch_passed",)
    assert tuple((row.pitcher_key, row.digest_status) for row in stable_report.rows) == (
        ("pitcher.alpha", "clear"),
        ("pitcher.beta", "clear"),
    )


def test_payload_helper_uses_json_ready_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        report_input(
            "pitcher.payload",
            "Payload Starter",
            "sea",
            "mlb.sea.hou.20260703",
            observed_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=75),
            scratch_probability=d("0.360000"),
            lineup_confirmed_at=None,
        ),
    )

    payload = digest.market_research_baseball_starting_pitcher_scratch_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["pitcher_count"] == "1"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T14:00:00+00:00"
    assert payload["rows"][0]["scratch_probability"] == "0.360000"
    assert payload["rows"][0]["minutes_until_start"] == "75.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

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

    row_input = report_input()
    with pytest.raises(FrozenInstanceError):
        row_input.scratch_probability = d("0.200000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="scratch_probability must be a Decimal"):
        report_input(scratch_probability=0.2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        report_input(observed_at=datetime(2026, 7, 3, 16, 0))

    with pytest.raises(ValueError, match="pitcher_key must be a string"):
        report_input(pitcher_key=_StringSubclass("pitcher.cole"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            report_input(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="scratch_probability_watch_threshold"):
        config(scratch_probability_watch_threshold=_DecimalSubclass("0.350000"))

    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row_input, paper_only=False)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        build_report(
            report_input(source_config_version="v0"),
            report_input(source_config_version="v1"),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(report_input(observed_at=GENERATED_AT + timedelta(minutes=1)))

    report = build_report(
        report_input("pitcher.gamma", "Gamma Starter", "stl", "mlb.stl.chc.20260703"),
    )
    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["pitcher_count"] = d("2")
    with pytest.raises(ValueError, match="pitcher_count"):
        digest.MarketResearchBaseballStartingPitcherScratchDigestReport(
            **bad_report_values,
        )


def test_module_scope_has_no_io_live_trading_float_or_durable_store_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_baseball_starting_pitcher_scratch_digest.py",
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
