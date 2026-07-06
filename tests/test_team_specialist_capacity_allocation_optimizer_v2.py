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


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_capacity_allocation_optimizer_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_capacity_allocation_optimizer_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(**overrides: object) -> Any:
    module = api()
    values = {
        "specialist_id": "alpha_specialist",
        "queue_id": "macro_resolution",
        "requested_units": d("4.000000"),
        "available_capacity_units": d("10.000000"),
        "current_load_units": d("2.000000"),
        "queue_priority_score": d("0.900000"),
        "urgency_score": d("0.800000"),
        "specialist_fit_score": d("0.900000"),
        "readiness_score": d("0.850000"),
    }
    values.update(overrides)
    return module.TeamSpecialistCapacityAllocationV2Input(**values)


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            item(specialist_id="alpha_specialist"),
            item(
                specialist_id="beta_specialist",
                queue_id="policy_resolution",
                requested_units=d("6.000000"),
                available_capacity_units=d("8.000000"),
                current_load_units=d("4.000000"),
                queue_priority_score=d("0.950000"),
                urgency_score=d("0.750000"),
                specialist_fit_score=d("0.700000"),
                readiness_score=d("0.700000"),
            ),
            item(
                specialist_id="gamma_specialist",
                queue_id="regional_resolution",
                requested_units=d("5.000000"),
                available_capacity_units=d("4.000000"),
                current_load_units=d("4.000000"),
                queue_priority_score=d("0.400000"),
                urgency_score=d("0.500000"),
                specialist_fit_score=d("0.450000"),
                readiness_score=d("0.400000"),
            ),
        )
    return module.build_team_specialist_capacity_allocation_optimizer_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_float_or_int(item_value)
    if isinstance(value, (list, tuple)):
        for item_value in value:
            assert_no_float_or_int(item_value)


def test_capacity_allocation_and_decimal_serialization_payload() -> None:
    module = api()
    report = build_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.optimizer_status == "defer"
    assert report.item_count == d("3")
    assert report.allocate_count == d("1")
    assert report.watch_count == d("1")
    assert report.defer_count == d("1")
    assert report.total_requested_units == d("15.000000")
    assert report.total_allocated_units == d("8.000000")
    assert report.total_overload_units == d("7.000000")
    assert report.allocation_rate == d("0.533333")
    assert report.average_allocation_priority_score == d("0.547222")
    assert report.top_allocation_priority_score == d("0.905000")
    assert report.bottom_allocation_priority_score == d("0.057500")
    assert report.reason_codes == (
        "capacity_allocation_optimizer_defer_rows",
        "capacity_allocation_optimizer_watch_rows",
    )

    rows = report.rows
    assert tuple(row.specialist_id for row in rows) == (
        "alpha_specialist",
        "beta_specialist",
        "gamma_specialist",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.allocated_units for row in rows) == (
        d("4.000000"),
        d("4.000000"),
        d("0.000000"),
    )
    assert tuple(row.overload_units for row in rows) == (
        d("0.000000"),
        d("2.000000"),
        d("5.000000"),
    )
    assert tuple(row.allocation_priority_score for row in rows) == (
        d("0.905000"),
        d("0.679167"),
        d("0.057500"),
    )
    assert tuple(row.allocation_status for row in rows) == (
        "allocate",
        "watch",
        "defer",
    )

    payload = module.team_specialist_capacity_allocation_optimizer_v2_payload(report)
    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["item_count"] == "3"
    assert payload["total_allocated_units"] == "8.000000"
    assert payload["allocation_rate"] == "0.533333"
    assert payload["rows"][1]["capacity_fill_ratio"] == "0.666667"
    assert payload["rows"][2]["overload_penalty_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.derived_validation_digest) == 64
    assert module.validate_team_specialist_capacity_allocation_optimizer_v2_payload(payload)
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_overload_penalties_reduce_priority_and_flag_limited_capacity() -> None:
    report = build_report(
        item(
            specialist_id="clear_capacity",
            requested_units=d("4.000000"),
            available_capacity_units=d("8.000000"),
            current_load_units=d("0.000000"),
            queue_priority_score=d("0.700000"),
            urgency_score=d("0.700000"),
            specialist_fit_score=d("0.700000"),
            readiness_score=d("0.700000"),
        ),
        item(
            specialist_id="limited_capacity",
            requested_units=d("4.000000"),
            available_capacity_units=d("2.000000"),
            current_load_units=d("0.000000"),
            queue_priority_score=d("0.700000"),
            urgency_score=d("0.700000"),
            specialist_fit_score=d("0.700000"),
            readiness_score=d("0.700000"),
        ),
    )

    clear, limited = report.rows
    assert clear.specialist_id == "clear_capacity"
    assert clear.allocation_priority_score == d("0.790000")
    assert clear.overload_penalty_score == d("0.000000")
    assert "capacity_clear" in clear.reason_codes

    assert limited.specialist_id == "limited_capacity"
    assert limited.allocated_units == d("2.000000")
    assert limited.overload_units == d("2.000000")
    assert limited.capacity_fill_ratio == d("0.500000")
    assert limited.overload_penalty_score == d("0.500000")
    assert limited.allocation_priority_score == d("0.515000")
    assert limited.allocation_status == "watch"
    assert "capacity_limited" in limited.reason_codes
    assert "overload_penalty_high" in limited.reason_codes


def test_queue_priority_controls_rank_when_capacity_is_equal() -> None:
    report = build_report(
        item(
            specialist_id="low_priority_specialist",
            queue_id="analysis_low",
            requested_units=d("3.000000"),
            available_capacity_units=d("3.000000"),
            current_load_units=d("0.000000"),
            queue_priority_score=d("0.300000"),
            urgency_score=d("0.600000"),
            specialist_fit_score=d("0.600000"),
            readiness_score=d("0.600000"),
        ),
        item(
            specialist_id="high_priority_specialist",
            queue_id="analysis_high",
            requested_units=d("3.000000"),
            available_capacity_units=d("3.000000"),
            current_load_units=d("0.000000"),
            queue_priority_score=d("0.900000"),
            urgency_score=d("0.600000"),
            specialist_fit_score=d("0.600000"),
            readiness_score=d("0.600000"),
        ),
    )

    assert tuple(row.specialist_id for row in report.rows) == (
        "high_priority_specialist",
        "low_priority_specialist",
    )
    assert report.rows[0].allocation_priority_score == d("0.795000")
    assert report.rows[1].allocation_priority_score == d("0.645000")


def test_empty_report_is_report_only_readonly_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=GENERATED_AT,
        use_default_items=False,
    )

    assert report.optimizer_status == "defer"
    assert report.item_count == d("0")
    assert report.total_requested_units == d("0.000000")
    assert report.total_allocated_units == d("0.000000")
    assert report.total_overload_units == d("0.000000")
    assert report.allocation_rate == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("capacity_allocation_optimizer_empty",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCapacityAllocationOptimizerV2Config()
    sample = item()
    report = build_report(sample)
    row = report.rows[0]

    for exported_name in module.__all__:
        exported_value = getattr(module, exported_name)
        if isinstance(exported_value, type):
            assert is_dataclass(exported_value)

    for instance in (config, sample, row, report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        with pytest.raises(FrozenInstanceError):
            instance.readonly = False  # type: ignore[misc]
        for field in fields(instance):
            value = getattr(instance, field.name)
            if field.name.endswith("_score") or field.name.endswith("_units"):
                assert type(value) is Decimal
            if field.name.endswith("_count") or field.name.endswith("_rate"):
                assert type(value) is Decimal
            if field.name in {"rank", "allocate_score_floor", "watch_score_floor"}:
                assert type(value) is Decimal

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.TeamSpecialistCapacityAllocationOptimizerV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeInput(module.TeamSpecialistCapacityAllocationV2Input):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.TeamSpecialistCapacityAllocationOptimizerV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.TeamSpecialistCapacityAllocationOptimizerV2Report):
            pass


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "requested_units",
            _DecimalSubclass("4.000000"),
            "requested_units must be exactly Decimal",
        ),
        (
            "available_capacity_units",
            d("-0.000001"),
            "available_capacity_units must be >= 0.000000",
        ),
        (
            "current_load_units",
            d("1.0000004"),
            "current_load_units must use six decimal places or fewer",
        ),
        (
            "queue_priority_score",
            d("1.000001"),
            "queue_priority_score must be <= 1.000000",
        ),
        (
            "urgency_score",
            Decimal("NaN"),
            "urgency_score must be finite",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        item(**{field_name: bad_value})


def test_hard_flags_config_and_builder_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="allocation score weights must sum to 1.000000"):
        module.TeamSpecialistCapacityAllocationOptimizerV2Config(
            readiness_weight=d("0.110000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed"):
        module.TeamSpecialistCapacityAllocationOptimizerV2Config(
            watch_score_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCapacityAllocationOptimizerV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        item(readonly=False)
    with pytest.raises(ValueError, match="capacity_items must be a list or tuple"):
        module.build_team_specialist_capacity_allocation_optimizer_v2(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="capacity_items must contain TeamSpecialistCapacityAllocationV2Input",
    ):
        module.build_team_specialist_capacity_allocation_optimizer_v2(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_capacity_allocation_optimizer_v2(
            [item()],
            generated_at=datetime(2026, 7, 6, 12, 0),
        )


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            config_version="team-specialist-capacity-allocation-optimizer-v2-mutated",
        )

    payload = dict(report.payload)
    payload["allocation_rate"] = "0.500000"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.validate_team_specialist_capacity_allocation_optimizer_v2_payload(payload)


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_specialist",
        "auth_specialist",
        "wallet_specialist",
        "order_specialist",
        "network_specialist",
        "database_specialist",
        "persist_specialist",
        "signing_specialist",
        "mutation_specialist",
        "buy_specialist",
        "sell_specialist",
        "trade_specialist",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            item(specialist_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_team_specialist_capacity_allocation_optimizer_v2_payload(
            {"order_id": "redacted", "derived_validation_digest": "0" * 64},
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": 1})
    with pytest.raises(ValueError, match="reason_codes must contain known reason codes"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_sorting_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by priority and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, allocate_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match optimizer_status"):
        replace(report, reason_codes=("capacity_allocation_optimizer_passed",))
    with pytest.raises(ValueError, match="allocation_rate must match rows"):
        replace(report, allocation_rate=d("0.500000"))


def test_module_scope_has_no_network_auth_wallet_database_or_action_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
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
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_or_int([imports, call_names, attribute_names])
