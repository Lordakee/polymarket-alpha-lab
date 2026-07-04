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


GENERATED_AT = datetime(2026, 7, 3, 23, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_baseball_bullpen_availability_squeeze_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_baseball_bullpen_availability_squeeze_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(
    source_id: str = "source-bullpen-alpha",
    *,
    team_id: str = "nyy",
    opponent_id: str = "bos",
    market_slug: str = "nyy-bos-moneyline",
    reliever_workload_index: str | Decimal = "0.400000",
    back_to_back_usage_count: str | Decimal = "0.000000",
    leverage_arm_available_count: str | Decimal = "3.000000",
    starter_expected_innings: str | Decimal = "6.000000",
    travel_rest_pressure_index: str | Decimal = "0.200000",
    source_disagreement_index: str | Decimal = "0.100000",
    source_updated_at: datetime = datetime(2026, 7, 3, 21, 30, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_bullpen_card",),
):
    module = api()
    return module.MarketResearchBaseballBullpenAvailabilitySqueezeInputRow(
        source_id=source_id,
        team_id=team_id,
        opponent_id=opponent_id,
        market_slug=market_slug,
        reliever_workload_index=(
            reliever_workload_index
            if isinstance(reliever_workload_index, Decimal)
            else d(reliever_workload_index)
        ),
        back_to_back_usage_count=(
            back_to_back_usage_count
            if isinstance(back_to_back_usage_count, Decimal)
            else d(back_to_back_usage_count)
        ),
        leverage_arm_available_count=(
            leverage_arm_available_count
            if isinstance(leverage_arm_available_count, Decimal)
            else d(leverage_arm_available_count)
        ),
        starter_expected_innings=(
            starter_expected_innings
            if isinstance(starter_expected_innings, Decimal)
            else d(starter_expected_innings)
        ),
        travel_rest_pressure_index=(
            travel_rest_pressure_index
            if isinstance(travel_rest_pressure_index, Decimal)
            else d(travel_rest_pressure_index)
        ),
        source_disagreement_index=(
            source_disagreement_index
            if isinstance(source_disagreement_index, Decimal)
            else d(source_disagreement_index)
        ),
        source_updated_at=source_updated_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def digest_report(*rows: object, cfg: object | None = None):
    module = api()
    return module.build_market_research_baseball_bullpen_availability_squeeze_digest(
        rows,
        config=cfg or module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"float found in JSON payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            assert_no_floats(item)


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = api()

    report = digest_report()

    assert isinstance(
        report,
        module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport,
    )
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-baseball-bullpen-availability-squeeze-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_baseball_bullpen_squeeze_screening"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.workload_pressure_count == d("0.000000")
    assert report.leverage_availability_pressure_count == d("0.000000")
    assert report.starter_length_pressure_count == d("0.000000")
    assert report.travel_rest_pressure_count == d("0.000000")
    assert report.source_quality_pressure_count == d("0.000000")
    assert report.max_reliever_workload_index == d("0.000000")
    assert report.max_back_to_back_usage_count == d("0.000000")
    assert report.min_leverage_arm_available_count == d("0.000000")
    assert report.min_starter_expected_innings == d("0.000000")
    assert report.max_source_age_minutes == d("0.000000")
    assert report.risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "baseball_bullpen_squeeze_digest_empty",
    )
    assert report.reason_code_counts == (
        module.MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount(
            reason_code="baseball_bullpen_squeeze_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_bullpen_squeeze_blocks_event_market_screening() -> None:
    report = digest_report(
        input_row(
            "source-blocked",
            market_slug="nyy-bos-moneyline",
            reliever_workload_index="0.910000",
            back_to_back_usage_count="3.000000",
            leverage_arm_available_count="0.000000",
            starter_expected_innings="3.200000",
            travel_rest_pressure_index="0.820000",
            source_disagreement_index="0.750000",
            source_updated_at=datetime(2026, 7, 3, 19, 30, tzinfo=UTC),
            upstream_reason_codes=(
                "beat_writer_availability_note",
                "official_bullpen_card",
            ),
        ),
        input_row(
            "source-watch",
            team_id="lad",
            opponent_id="sfg",
            market_slug="lad-sfg-total-runs",
            reliever_workload_index="0.700000",
            back_to_back_usage_count="2.000000",
            leverage_arm_available_count="1.000000",
            starter_expected_innings="4.800000",
            travel_rest_pressure_index="0.650000",
            source_disagreement_index="0.450000",
            source_updated_at=datetime(
                2026,
                7,
                3,
                17,
                15,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        input_row(
            "source-pass",
            team_id="sea",
            opponent_id="tex",
            market_slug="sea-tex-moneyline",
            source_updated_at=datetime(2026, 7, 3, 22, 30, tzinfo=UTC),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_baseball_bullpen_squeeze_screening"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.workload_pressure_count == d("2.000000")
    assert report.leverage_availability_pressure_count == d("2.000000")
    assert report.starter_length_pressure_count == d("2.000000")
    assert report.travel_rest_pressure_count == d("2.000000")
    assert report.source_quality_pressure_count == d("2.000000")
    assert report.max_reliever_workload_index == d("0.910000")
    assert report.max_back_to_back_usage_count == d("3.000000")
    assert report.min_leverage_arm_available_count == d("0.000000")
    assert report.min_starter_expected_innings == d("3.200000")
    assert report.max_source_age_minutes == d("210.000000")
    assert report.risk_score == d("1.000000")
    assert report.reason_codes == (
        "baseball_bullpen_squeeze_blocked_market_present",
        "baseball_bullpen_squeeze_watch_market_present",
        "baseball_bullpen_squeeze_workload_pressure_present",
        "baseball_bullpen_squeeze_leverage_availability_pressure_present",
        "baseball_bullpen_squeeze_starter_length_pressure_present",
        "baseball_bullpen_squeeze_travel_rest_pressure_present",
        "baseball_bullpen_squeeze_source_quality_pressure_present",
    )
    assert tuple(row.market_slug for row in report.rows) == (
        "nyy-bos-moneyline",
        "lad-sfg-total-runs",
        "sea-tex-moneyline",
    )

    blocked, watch, passed = report.rows
    assert blocked.row_status == "blocked"
    assert blocked.source_age_minutes == d("210.000000")
    assert blocked.squeeze_risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == (
        "beat_writer_availability_note",
        "official_bullpen_card",
    )
    assert blocked.reason_codes == (
        "baseball_bullpen_squeeze_back_to_back_usage",
        "baseball_bullpen_squeeze_high_reliever_workload",
        "baseball_bullpen_squeeze_leverage_arms_unavailable",
        "baseball_bullpen_squeeze_short_starter_expectation",
        "baseball_bullpen_squeeze_source_disagreement",
        "baseball_bullpen_squeeze_stale_source",
        "baseball_bullpen_squeeze_travel_rest_pressure",
    )
    assert watch.row_status == "watch"
    assert watch.source_updated_at == datetime(2026, 7, 3, 21, 15, tzinfo=UTC)
    assert watch.squeeze_risk_score == d("0.750000")
    assert watch.reason_codes == (
        "baseball_bullpen_squeeze_back_to_back_usage",
        "baseball_bullpen_squeeze_leverage_arms_thin",
        "baseball_bullpen_squeeze_short_starter_expectation",
        "baseball_bullpen_squeeze_source_disagreement",
        "baseball_bullpen_squeeze_stale_source",
        "baseball_bullpen_squeeze_travel_rest_pressure",
        "baseball_bullpen_squeeze_watch_reliever_workload",
    )
    assert passed.row_status == "pass"
    assert passed.reason_codes == ("baseball_bullpen_squeeze_clear",)


def test_rows_reasons_and_counts_are_sorted_deterministically() -> None:
    first = input_row(
        "source-watch-b",
        market_slug="beta-watch",
        reliever_workload_index="0.700000",
    )
    second = input_row(
        "source-blocked",
        market_slug="alpha-blocked",
        reliever_workload_index="0.910000",
    )
    third = input_row(
        "source-watch-a",
        market_slug="alpha-watch",
        reliever_workload_index="0.700000",
    )

    forward = digest_report(first, second, third)
    reverse = digest_report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "baseball_bullpen_squeeze_blocked_market_present",
        "baseball_bullpen_squeeze_watch_market_present",
        "baseball_bullpen_squeeze_workload_pressure_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_pressure_to_pass() -> None:
    module = api()
    cfg = module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig(
        watch_reliever_workload_index=d("0.800000"),
        blocked_reliever_workload_index=d("0.950000"),
        watch_back_to_back_usage_count=d("4.000000"),
        blocked_back_to_back_usage_count=d("5.000000"),
        watch_available_leverage_arm_count=d("0.000000"),
        blocked_available_leverage_arm_count=d("0.000000"),
        watch_starter_expected_innings=d("4.000000"),
        blocked_starter_expected_innings=d("3.000000"),
        watch_source_age_minutes=d("120.000000"),
    )

    report = digest_report(
        input_row(
            "source-moderate",
            reliever_workload_index="0.700000",
            back_to_back_usage_count="2.000000",
            leverage_arm_available_count="1.000000",
            starter_expected_innings="4.800000",
        ),
        cfg=cfg,
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "allow_report_only_baseball_bullpen_squeeze_screening"
    )
    assert report.rows[0].row_status == "pass"
    assert report.rows[0].reason_codes == ("baseball_bullpen_squeeze_clear",)
    assert report.risk_score == d("0.000000")
    assert report.reason_codes == ("baseball_bullpen_squeeze_digest_clear",)


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="reliever_workload_index must be a Decimal"):
        input_row(reliever_workload_index=_DecimalSubclass("0.420000"))
    with pytest.raises(ValueError, match="starter_expected_innings must be nonnegative"):
        input_row(starter_expected_innings="-1.000000")
    with pytest.raises(ValueError, match="source_updated_at must be timezone-aware"):
        input_row(source_updated_at=datetime(2026, 7, 3, 21, 30))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_baseball_bullpen_availability_squeeze_digest(
            (),
            config=module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 23, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows must contain"):
        digest_report("not-a-row")
    with pytest.raises(ValueError, match="duplicate source_id"):
        digest_report(input_row("source-dupe"), input_row("source-dupe"))
    with pytest.raises(ValueError, match="watch_reliever_workload_index"):
        module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig(
            watch_reliever_workload_index=d("0.950000"),
            blocked_reliever_workload_index=d("0.900000"),
        )

    valid_row = digest_report(input_row("source-valid")).rows[0]
    with pytest.raises(ValueError, match="source_age_minutes must match"):
        replace(valid_row, source_age_minutes=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "baseball_bullpen_squeeze_clear",
                "baseball_bullpen_squeeze_watch_reliever_workload",
            ),
        )

    frozen_input = input_row("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_input.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = api()

    report = digest_report(input_row("source-hard-flags"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig(
            paper_only=False,
        )
    with pytest.raises(ValueError, match="input row report_only must be True"):
        replace(input_row("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)


def test_payload_uses_six_decimal_strings_and_module_has_no_live_surfaces() -> None:
    module = api()
    report = digest_report(input_row("source-payload"))

    payload = module.market_research_baseball_bullpen_availability_squeeze_digest_payload(
        report,
    )

    json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["reliever_workload_index"] == "0.400000"
    assert payload["rows"][0]["source_updated_at"] == "2026-07-03T21:30:00+00:00"
    assert_no_floats(payload)

    for public_record in (
        module.MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig(),
        input_row("source-dataclass"),
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

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "api_key",
        "auth",
        "balance",
        "cancel",
        "connect(",
        "environ",
        "execute(",
        "private_key",
        "replace_order",
        "request",
        "submit_order",
        "token",
        "urlopen",
        "wallet",
    ):
        assert forbidden not in source.lower()
