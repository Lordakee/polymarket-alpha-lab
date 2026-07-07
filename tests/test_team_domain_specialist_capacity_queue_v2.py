from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/team_domain_specialist_capacity_queue_v2.py",
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_domain_specialist_capacity_queue_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-domain-specialist-capacity-queue-v2-test",
        "watch_utilization_ratio": d("0.800000"),
        "block_utilization_ratio": d("1.000000"),
        "overdue_watch_count": d("1.000000"),
        "high_priority_watch_count": d("2.000000"),
        "stale_assignment_after_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return module.TeamDomainSpecialistCapacityQueueV2Config(**values)


def assignment(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_research",
        "domain": "finance.rates",
        "active_packet_count": d("3.000000"),
        "max_packet_capacity": d("6.000000"),
        "overdue_packet_count": d("0.000000"),
        "high_priority_packet_count": d("0.000000"),
        "latest_assignment_at": GENERATED_AT - timedelta(days=1),
    }
    values.update(overrides)
    return module.TeamDomainSpecialistCapacityQueueV2Input(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_domain_specialist_capacity_queue_v2(
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


def reason_count_map(report: object) -> dict[str, Decimal]:
    return {
        item.reason_code: item.count
        for item in getattr(report, "reason_code_counts")
    }


def test_queues_specialist_capacity_with_deterministic_rows_and_rollups() -> None:
    report = build_report(
        assignment(
            team_id="macro_research",
            domain="finance.rates",
            active_packet_count=d("3.000000"),
            max_packet_capacity=d("6.000000"),
            overdue_packet_count=d("0.000000"),
            high_priority_packet_count=d("0.000000"),
            latest_assignment_at=GENERATED_AT - timedelta(days=1),
        ),
        assignment(
            team_id="crypto_research",
            domain="crypto.btc",
            active_packet_count=d("8.000000"),
            max_packet_capacity=d("10.000000"),
            overdue_packet_count=d("1.000000"),
            high_priority_packet_count=d("2.000000"),
            latest_assignment_at=GENERATED_AT - timedelta(days=8),
        ),
        assignment(
            team_id="sports_research",
            domain="sports.basketball",
            active_packet_count=d("12.000000"),
            max_packet_capacity=d("10.000000"),
            overdue_packet_count=d("3.000000"),
            high_priority_packet_count=d("4.000000"),
            latest_assignment_at=GENERATED_AT - timedelta(hours=6),
        ),
    )

    assert is_dataclass(report)
    assert report.report_status == "block"
    assert report.team_domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.over_capacity_count == d("1.000000")
    assert report.overdue_count == d("2.000000")
    assert report.high_priority_pressure_count == d("2.000000")
    assert report.max_utilization_ratio == d("1.200000")

    assert tuple((row.team_id, row.domain) for row in report.rows) == (
        ("sports_research", "sports.basketball"),
        ("crypto_research", "crypto.btc"),
        ("macro_research", "finance.rates"),
    )
    assert tuple(row.utilization_ratio for row in report.rows) == (
        d("1.200000"),
        d("0.800000"),
        d("0.500000"),
    )
    assert tuple(row.capacity_gap for row in report.rows) == (
        d("-2.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.assignment_age_seconds for row in report.rows) == (
        d("21600.000000"),
        d("691200.000000"),
        d("86400.000000"),
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].reason_codes == (
        "specialist_capacity_block",
        "specialist_capacity_over_capacity",
        "specialist_capacity_overdue",
        "specialist_capacity_high_priority_pressure",
    )
    assert report.rows[1].reason_codes == (
        "specialist_capacity_watch",
        "specialist_capacity_overdue",
        "specialist_capacity_high_priority_pressure",
        "specialist_capacity_stale_assignment",
    )
    assert report.rows[2].reason_codes == (
        "specialist_capacity_pass",
        "specialist_capacity_available",
        "specialist_capacity_assignment_current",
    )

    counts = reason_count_map(report)
    assert counts["specialist_capacity_pass"] == d("1.000000")
    assert counts["specialist_capacity_watch"] == d("1.000000")
    assert counts["specialist_capacity_block"] == d("1.000000")
    assert counts["specialist_capacity_over_capacity"] == d("1.000000")
    assert counts["specialist_capacity_overdue"] == d("2.000000")
    assert counts["specialist_capacity_high_priority_pressure"] == d("2.000000")
    assert counts["specialist_capacity_stale_assignment"] == d("1.000000")


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    report = build_report()

    assert report.report_status == "empty"
    assert report.team_domain_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.over_capacity_count == d("0.000000")
    assert report.overdue_count == d("0.000000")
    assert report.high_priority_pressure_count == d("0.000000")
    assert report.max_utilization_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert len(report.derived_validation_digest) == 64


def test_input_order_does_not_change_rows_payload_or_digest() -> None:
    first = assignment(team_id="team_alpha", domain="politics")
    second = assignment(team_id="team_beta", domain="commodities.gold")

    left = build_report(first, second)
    right = build_report(second, first)

    assert tuple((row.team_id, row.domain) for row in left.rows) == (
        ("team_alpha", "politics"),
        ("team_beta", "commodities.gold"),
    )
    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.payload == right.payload


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(assignment())

    payload = module.team_domain_specialist_capacity_queue_v2_payload(report)

    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["team_domain_count"] == "1.000000"
    assert payload["max_utilization_ratio"] == "0.500000"
    assert payload["rows"][0]["utilization_ratio"] == "0.500000"
    assert payload["rows"][0]["capacity_gap"] == "3.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["max_utilization_ratio"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_domain_specialist_capacity_queue_v2_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_domain_specialist_capacity_queue_v2_payload(tampered_digest)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_assignment = assignment()
    sample_report = build_report(sample_assignment)
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (
        sample_config,
        sample_assignment,
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
        assignment(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(assignment(readonly=False))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "active_packet_count",
            _DecimalSubclass("1.000000"),
            "active_packet_count must be exactly Decimal",
        ),
        (
            "max_packet_capacity",
            d("0.000000"),
            "max_packet_capacity must be positive",
        ),
        (
            "overdue_packet_count",
            Decimal("NaN"),
            "overdue_packet_count must be finite",
        ),
        (
            "high_priority_packet_count",
            d("-1.000000"),
            "high_priority_packet_count must be nonnegative",
        ),
    ),
)
def test_input_validation_rejects_bad_decimal_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        assignment(**{field_name: bad_value})


def test_validation_rejects_inconsistent_inputs_config_and_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="overdue_packet_count must not exceed"):
        assignment(
            active_packet_count=d("3.000000"),
            overdue_packet_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="domain must be a public identifier"):
        assignment(domain="sports soccer")
    with pytest.raises(ValueError, match="assignments must be a sequence"):
        module.build_team_domain_specialist_capacity_queue_v2(
            object(),
            generated_at=GENERATED_AT,
            config=config(),
        )
    with pytest.raises(ValueError, match="assignments must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="duplicate team/domain"):
        build_report(assignment(), assignment())
    with pytest.raises(ValueError, match="latest_assignment_at must not be after"):
        build_report(assignment(latest_assignment_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(assignment(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="watch_utilization_ratio must not exceed"):
        config(watch_utilization_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(build_report(assignment()), derived_validation_digest="0" * 64)


def test_unsafe_public_surface_terms_are_rejected() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
        "order_team",
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            assignment(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public field"):
        module.team_domain_specialist_capacity_queue_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_field": "safe_value",
            },
        )
    with pytest.raises(ValueError, match="float"):
        module.team_domain_specialist_capacity_queue_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "max_utilization_ratio": 0.1,
            },
        )


def test_static_module_surface_has_no_io_auth_wallet_order_network_or_db_writes() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
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
