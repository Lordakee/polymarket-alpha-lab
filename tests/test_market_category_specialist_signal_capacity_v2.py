from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_category_specialist_signal_capacity_v2"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def category(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "category": "macro",
        "signal_count": d("80"),
        "high_priority_signal_count": d("20"),
        "specialist_count": d("4"),
        "per_specialist_capacity": d("25"),
        "stale_signal_count": d("0"),
        "latest_signal_at": GENERATED_AT - timedelta(minutes=5),
    }
    values.update(overrides)
    return module.MarketCategorySpecialistSignalCapacityV2Input(**values)


def report(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_category_specialist_signal_capacity_v2_report(
        rows,
        generated_at=generated_at,
    )


def assert_decimal_only_dataclass(value: object) -> None:
    for item in fields(value):
        field_value = getattr(value, item.name)
        if type(field_value) in (bool, str, datetime, tuple, dict) or field_value is None:
            continue
        assert type(field_value) is Decimal


def assert_no_json_numeric_values(value: object) -> None:
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise AssertionError(f"payload contains JSON numeric value {value!r}")
    if type(value) is dict:
        for key, item in value.items():
            assert type(key) is str
            assert_no_json_numeric_values(item)
    elif type(value) is list:
        for item in value:
            assert_no_json_numeric_values(item)


def test_builds_category_signal_capacity_report_with_pass_watch_block_rows() -> None:
    result = report(
        category(category="sports", signal_count=d("80"), specialist_count=d("4")),
        category(
            category="macro",
            signal_count=d("101"),
            high_priority_signal_count=d("30"),
            specialist_count=d("4"),
            stale_signal_count=d("2"),
        ),
        category(
            category="crypto",
            signal_count=d("160"),
            high_priority_signal_count=d("55"),
            specialist_count=d("4"),
            stale_signal_count=d("8"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.category_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.over_capacity_count == d("2")
    assert result.stale_signal_count == d("10")
    assert result.high_priority_pressure_count == d("2")
    assert result.max_capacity_utilization_ratio == d("1.600000")
    assert result.report_status == "block"
    assert result.reason_code_counts == {
        "capacity_signal_pass": d("1"),
        "capacity_signal_watch": d("1"),
        "capacity_signal_block": d("1"),
        "signal_backlog_present": d("2"),
        "over_capacity": d("2"),
        "stale_signals_present": d("2"),
        "high_priority_pressure": d("2"),
    }
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.category for row in result.rows) == ("crypto", "macro", "sports")

    blocked, watched, passed = result.rows
    assert blocked.rank == d("1")
    assert blocked.signal_count == d("160")
    assert blocked.total_specialist_capacity == d("100")
    assert blocked.capacity_utilization_ratio == d("1.600000")
    assert blocked.signal_backlog_count == d("60")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "capacity_signal_block",
        "signal_backlog_present",
        "over_capacity",
        "stale_signals_present",
        "high_priority_pressure",
    )

    assert watched.rank == d("2")
    assert watched.capacity_utilization_ratio == d("1.010000")
    assert watched.signal_backlog_count == d("1")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "capacity_signal_watch",
        "signal_backlog_present",
        "over_capacity",
        "stale_signals_present",
        "high_priority_pressure",
    )

    assert passed.rank == d("3")
    assert passed.capacity_utilization_ratio == d("0.800000")
    assert passed.signal_backlog_count == d("0")
    assert passed.status == "pass"
    assert passed.reason_codes == ("capacity_signal_pass",)


def test_empty_input_returns_empty_status_and_zero_decimals() -> None:
    result = report()

    assert result.report_status == "empty"
    assert result.category_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.over_capacity_count == d("0")
    assert result.stale_signal_count == d("0")
    assert result.high_priority_pressure_count == d("0")
    assert result.max_capacity_utilization_ratio == d("0.000000")
    assert result.reason_code_counts == {}
    assert result.rows == ()
    assert len(result.derived_validation_digest) == 64


def test_no_specialist_capacity_blocks_with_reason_count_and_payload() -> None:
    module = api()
    result = report(
        category(
            category="macro",
            signal_count=d("12"),
            high_priority_signal_count=d("0"),
            specialist_count=d("0"),
        ),
    )

    row = result.rows[0]
    assert result.report_status == "block"
    assert result.block_count == d("1")
    assert result.over_capacity_count == d("1")
    assert result.reason_code_counts == {
        "capacity_signal_block": d("1"),
        "signal_backlog_present": d("1"),
        "over_capacity": d("1"),
        "no_specialist_capacity": d("1"),
    }
    assert row.total_specialist_capacity == d("0")
    assert row.capacity_utilization_ratio == d("12.000000")
    assert row.signal_backlog_count == d("12")
    assert row.status == "block"
    assert row.reason_codes == (
        "capacity_signal_block",
        "signal_backlog_present",
        "over_capacity",
        "no_specialist_capacity",
    )

    payload = module.market_category_specialist_signal_capacity_v2_payload(result)

    assert payload["reason_code_counts"]["no_specialist_capacity"] == "1"
    assert payload["rows"][0]["total_specialist_capacity"] == "0"
    assert payload["rows"][0]["capacity_utilization_ratio"] == "12.000000"


def test_payload_serializes_decimal_strings_and_revalidates_digest() -> None:
    module = api()
    first = report(
        category(category="sports", signal_count=d("80"), specialist_count=d("4")),
        category(category="macro", signal_count=d("101"), specialist_count=d("4")),
    )
    second = report(
        category(category="macro", signal_count=d("101"), specialist_count=d("4")),
        category(category="sports", signal_count=d("80"), specialist_count=d("4")),
    )

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.market_category_specialist_signal_capacity_v2_payload(first)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["category_count"] == "2"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["category"] == "macro"
    assert payload["rows"][0]["capacity_utilization_ratio"] == "1.010000"
    assert payload["reason_code_counts"] == {
        "capacity_signal_pass": "1",
        "capacity_signal_watch": "1",
        "signal_backlog_present": "1",
        "over_capacity": "1",
    }
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_json_numeric_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["category_count"] = "1"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.market_category_specialist_signal_capacity_v2_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    item = category()
    result = report(item)
    row = result.rows[0]

    for instance in (item, row, result):
        assert is_dataclass(instance)
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        assert_decimal_only_dataclass(instance)
        with pytest.raises(FrozenInstanceError):
            instance.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, signal_count=d("81"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, pass_count=d("0"))

    with pytest.raises(ValueError, match="report must be"):
        module.market_category_specialist_signal_capacity_v2_payload(object())


def test_validates_decimal_only_inputs_integral_counts_utc_and_duplicates() -> None:
    module = api()
    eastern = timezone_minus_four()
    converted = report(
        category(latest_signal_at=datetime(2026, 7, 7, 7, 30, tzinfo=eastern)),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=eastern),
    )
    assert converted.generated_at == GENERATED_AT
    assert converted.rows[0].latest_signal_at == datetime(2026, 7, 7, 11, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="signal_count"):
        category(signal_count=80)
    with pytest.raises(ValueError, match="high_priority_signal_count"):
        category(high_priority_signal_count=_DecimalSubclass("20"))
    with pytest.raises(ValueError, match="category"):
        category(category=" macro")
    with pytest.raises(ValueError, match="specialist_count"):
        category(specialist_count=d("4.5"))
    with pytest.raises(ValueError, match="per_specialist_capacity"):
        category(per_specialist_capacity=d("0"))
    with pytest.raises(ValueError, match="high_priority_signal_count"):
        category(signal_count=d("10"), high_priority_signal_count=d("11"))
    with pytest.raises(ValueError, match="stale_signal_count"):
        category(
            signal_count=d("10"),
            high_priority_signal_count=d("10"),
            stale_signal_count=d("11"),
        )

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="timezone-aware"):
        category(latest_signal_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(category(), generated_at=datetime(2026, 7, 7, 12, 0, tzinfo=MissingOffsetTz()))
    with pytest.raises(ValueError, match="inputs"):
        module.build_market_category_specialist_signal_capacity_v2_report(
            "not-inputs",
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(category(category="macro"), category(category="macro"))


def timezone_minus_four() -> tzinfo:
    class FixedMinusFour(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta:
            return timedelta(hours=-4)

        def dst(self, dt: datetime | None) -> timedelta:
            return timedelta(0)

    return FixedMinusFour()


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "li" "ve_surface",
        "au" "th_surface",
        "wal" "let_surface",
        "or" "der_surface",
        "net" "work_surface",
        "data" "base_surface",
        "per" "sist_surface",
        "sig" "ning_surface",
        "muta" "tion_surface",
        "b" "uy_surface",
        "se" "ll_surface",
        "tra" "de_surface",
    ),
)
def test_rejects_unsafe_public_payload_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        category(category=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public"):
        module.market_category_specialist_signal_capacity_v2_payload(
            {"note": unsafe_value, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.market_category_specialist_signal_capacity_v2_payload(
            {unsafe_value: "redacted", "paper_only": True, "report_only": True, "readonly": True},
        )


def test_module_scope_has_no_external_io_execution_or_live_surfaces() -> None:
    module = api()
    source_text = inspect.getsource(module)
    lowered_source = source_text.lower()
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_MARKET_CATEGORY_SPECIALIST_SIGNAL_CAPACITY_V2_CONFIG_VERSION",
        "ROW_STATUSES",
        "REPORT_STATUSES",
        "MarketCategorySpecialistSignalCapacityV2Input",
        "MarketCategorySpecialistSignalCapacityV2Row",
        "MarketCategorySpecialistSignalCapacityV2Report",
        "build_market_category_specialist_signal_capacity_v2_report",
        "market_category_specialist_signal_capacity_v2_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "au" "th",
        "wal" "let",
        "or" "der",
        "net" "work",
        "data" "base",
        "per" "sist",
        "sig" "ning",
        "muta" "tion",
        "b" "uy",
        "se" "ll",
        "tra" "de",
        "tra" "ding",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "wri" "te_text",
        "wri" "te_bytes",
    )
    assert all(term not in lowered_source for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
