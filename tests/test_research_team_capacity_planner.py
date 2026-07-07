from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path("src/polymarket_alpha_lab/research_team_capacity_planner.py")
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
PUBLIC_STATES = {"pass", "watch", "block"}


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.research_team_capacity_planner")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "watch_queue_pressure_ratio": d("0.750000"),
        "block_queue_pressure_ratio": d("1.000000"),
        "watch_sla_breach_count": d("1.000000"),
        "block_sla_breach_count": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamCapacityPlannerConfig(**values)


def team_input(**overrides: object):
    module = api()
    values = {
        "team_code": "macro_research",
        "domain_code": "finance.rates",
        "specialist_role_code": "rates_analyst",
        "queued_item_count": d("1.000000"),
        "active_item_count": d("2.000000"),
        "capacity_item_count": d("8.000000"),
        "sla_breach_count": d("0.000000"),
        "required_domain_count": d("1.000000"),
        "covered_domain_count": d("1.000000"),
        "required_specialist_count": d("1.000000"),
        "staffed_specialist_count": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamCapacityPlannerInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_capacity_plan(
        items,
        generated_at=generated_at,
        config=cfg if cfg is not None else config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if isinstance(value, datetime):
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_public_states_only(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status") or key.endswith("_state") or key == "status":
                assert item in PUBLIC_STATES
            assert_public_states_only(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_states_only(item)


def reason_count_map(report: object) -> dict[str, Decimal]:
    return {
        item.reason_code: item.count
        for item in getattr(report, "reason_code_counts")
    }


def test_capacity_sufficient_returns_pass_capacity_plan() -> None:
    report = build_report(
        team_input(
            team_code="macro_research",
            domain_code="finance.rates",
            specialist_role_code="rates_analyst",
            queued_item_count=d("1.000000"),
            active_item_count=d("2.000000"),
            capacity_item_count=d("8.000000"),
        ),
        team_input(
            team_code="sports_research",
            domain_code="sports.basketball",
            specialist_role_code="injury_analyst",
            queued_item_count=d("0.000000"),
            active_item_count=d("3.000000"),
            capacity_item_count=d("10.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.report_status == "pass"
    assert report.team_count == d("2.000000")
    assert report.pass_count == d("2.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.max_queue_pressure_ratio == d("0.375000")
    assert report.total_specialist_role_gap == d("0.000000")
    assert report.total_domain_coverage_gap == d("0.000000")
    assert report.total_sla_breach_count == d("0.000000")
    assert tuple(row.status for row in report.rows) == ("pass", "pass")
    assert report.rows[0].capacity_plan == "maintain_capacity"
    assert report.rows[0].reason_codes == (
        "capacity_plan_pass",
        "domain_coverage_complete",
        "specialist_role_covered",
        "available_capacity_present",
    )
    assert reason_count_map(report)["capacity_plan_pass"] == d("2.000000")
    assert_public_numeric_values_are_decimal(report)


def test_tight_queue_pressure_and_sla_return_watch() -> None:
    report = build_report(
        team_input(
            team_code="crypto_research",
            domain_code="crypto.btc",
            specialist_role_code="liquidity_analyst",
            queued_item_count=d("3.000000"),
            active_item_count=d("5.000000"),
            capacity_item_count=d("10.000000"),
            sla_breach_count=d("1.000000"),
        ),
    )

    assert report.report_status == "watch"
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert report.max_queue_pressure_ratio == d("0.800000")
    assert report.total_sla_breach_count == d("1.000000")
    row = report.rows[0]
    assert row.status == "watch"
    assert row.queue_pressure_ratio == d("0.800000")
    assert row.available_item_count == d("2.000000")
    assert row.capacity_plan == "watch_capacity_pressure"
    assert row.reason_codes == (
        "capacity_plan_watch",
        "queue_pressure_watch",
        "sla_watch",
        "domain_coverage_complete",
        "specialist_role_covered",
        "available_capacity_present",
    )


def test_domain_or_specialist_gap_blocks_capacity_plan() -> None:
    report = build_report(
        team_input(
            team_code="policy_research",
            domain_code="politics.elections",
            specialist_role_code="polling_analyst",
            queued_item_count=d("1.000000"),
            active_item_count=d("2.000000"),
            capacity_item_count=d("10.000000"),
            required_domain_count=d("2.000000"),
            covered_domain_count=d("1.000000"),
            required_specialist_count=d("3.000000"),
            staffed_specialist_count=d("1.000000"),
        ),
    )

    assert report.report_status == "block"
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("1.000000")
    assert report.total_specialist_role_gap == d("2.000000")
    assert report.total_domain_coverage_gap == d("1.000000")
    row = report.rows[0]
    assert row.status == "block"
    assert row.domain_coverage_ratio == d("0.500000")
    assert row.domain_coverage_gap == d("1.000000")
    assert row.specialist_role_gap == d("2.000000")
    assert row.capacity_plan == "block_role_or_domain_gap"
    assert row.reason_codes == (
        "capacity_plan_block",
        "domain_coverage_gap_block",
        "specialist_role_gap_block",
        "available_capacity_present",
    )


def test_input_order_does_not_change_rows_payload_or_digest() -> None:
    first = team_input(team_code="team_alpha", domain_code="macro.cpi")
    second = team_input(team_code="team_beta", domain_code="sports.nba")
    left = build_report(second, first)
    right = build_report(first, second)

    assert tuple((row.team_code, row.domain_code) for row in left.rows) == (
        ("team_alpha", "macro.cpi"),
        ("team_beta", "sports.nba"),
    )
    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.payload == right.payload
    assert_public_states_only(left.payload)


def test_payload_has_hard_flags_decimal_strings_and_validated_digest() -> None:
    module = api()
    report = build_report(team_input())

    payload = module.research_team_capacity_plan_payload(report)

    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["team_count"] == "1.000000"
    assert payload["max_queue_pressure_ratio"] == "0.375000"
    assert payload["rows"][0]["queue_pressure_ratio"] == "0.375000"
    assert payload["rows"][0]["available_item_count"] == "5.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["max_queue_pressure_ratio"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_capacity_plan_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_capacity_plan_payload(tampered_digest)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_input = team_input()
    sample_report = build_report(sample_input)
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (
        sample_config,
        sample_input,
        sample_row,
        sample_reason_count,
        sample_report,
    ):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        team_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(sample_report, readonly=False)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "queued_item_count",
            _DecimalSubclass("1.000000"),
            "queued_item_count must be exactly Decimal",
        ),
        (
            "active_item_count",
            d("-1.000000"),
            "active_item_count must be nonnegative",
        ),
        (
            "capacity_item_count",
            d("0.000000"),
            "capacity_item_count must be positive",
        ),
        (
            "sla_breach_count",
            Decimal("NaN"),
            "sla_breach_count must be finite",
        ),
        (
            "required_specialist_count",
            d("1.000001"),
            "required_specialist_count must be a whole number",
        ),
    ),
)
def test_strict_decimal_type_validation_rejects_bad_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        team_input(**{field_name: bad_value})


def test_validation_rejects_inconsistent_config_inputs_and_sequences() -> None:
    module = api()

    with pytest.raises(ValueError, match="covered_domain_count must not exceed"):
        team_input(required_domain_count=d("1.000000"), covered_domain_count=d("2.000000"))
    with pytest.raises(ValueError, match="staffed_specialist_count must not exceed"):
        team_input(
            required_specialist_count=d("1.000000"),
            staffed_specialist_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="team_code must be a public identifier"):
        team_input(team_code="macro research")
    with pytest.raises(ValueError, match="inputs must be a sequence"):
        module.build_research_team_capacity_plan(
            object(),
            generated_at=GENERATED_AT,
            config=config(),
        )
    with pytest.raises(ValueError, match="inputs must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="duplicate team/domain/role"):
        build_report(team_input(), team_input())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(team_input(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="watch_queue_pressure_ratio must not exceed"):
        config(watch_queue_pressure_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(build_report(team_input()), derived_validation_digest="0" * 64)


def test_unsafe_public_surface_terms_are_rejected() -> None:
    module = api()

    for unsafe_value in (
        "raw_candidate_123",
        "market_alpha",
        "event_slug",
        "question_text",
        "source_ref",
        "https://example.test/data",
        "dsn_table",
        "token_wallet",
        "auth_order",
        "trade_position",
        "buy_signal",
        "sell_signal",
        "recommendation_text",
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            team_input(team_code=unsafe_value)

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth_header",
        "order_id",
        "trade_id",
        "position_size",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public field"):
            module.research_team_capacity_plan_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "derived_validation_digest": "0" * 64,
                    unsafe_key: "redacted",
                },
            )

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_team_capacity_plan_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "safe_field": "market_slug",
            },
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_capacity_plan_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "max_queue_pressure_ratio": 0.1,
            },
        )


def test_static_module_surface_is_pure_report_only_without_io_or_execution_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "place_order",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }

    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_modules
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
