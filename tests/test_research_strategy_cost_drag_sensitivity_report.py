from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_cost_drag_sensitivity_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def decimal_input(value: object) -> object:
    return d(value) if type(value) is str else value


def row(
    research_reference: str = "research-alpha",
    *,
    evaluated_at: datetime = datetime(2026, 7, 8, 11, 30, tzinfo=timezone(timedelta(hours=-4))),
    gross_edge_ratio: str | Decimal = "0.100000",
    fee_ratio: str | Decimal = "0.005000",
    spread_ratio: str | Decimal = "0.005000",
    slippage_ratio: str | Decimal = "0.005000",
    settlement_wait_days: str | Decimal = "1.000000",
    daily_wait_cost_ratio: str | Decimal = "0.001000",
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyCostDragSensitivityInput(
        research_reference=research_reference,
        evaluated_at=evaluated_at,
        gross_edge_ratio=decimal_input(gross_edge_ratio),
        fee_ratio=decimal_input(fee_ratio),
        spread_ratio=decimal_input(spread_ratio),
        slippage_ratio=decimal_input(slippage_ratio),
        settlement_wait_days=decimal_input(settlement_wait_days),
        daily_wait_cost_ratio=decimal_input(daily_wait_cost_ratio),
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object):
    module = api()
    values = {
        "watch_total_cost_drag_ratio": d("0.020000"),
        "block_total_cost_drag_ratio": d("0.050000"),
        "watch_cost_to_edge_ratio": d("0.500000"),
        "block_cost_to_edge_ratio": d("1.000000"),
        "watch_settlement_wait_days": d("3.000000"),
        "block_settlement_wait_days": d("7.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCostDragSensitivityConfig(**values)


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_cost_drag_sensitivity_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_values(child)
        return
    if isinstance(value, list):
        for child in value:
            assert_no_float_values(child)
        return
    assert type(value) is not float


def joined(*parts: str) -> str:
    return "".join(parts)


def status_rows():
    return (
        row(
            "research-pass",
            gross_edge_ratio="0.100000",
            fee_ratio="0.005000",
            spread_ratio="0.005000",
            slippage_ratio="0.005000",
            settlement_wait_days="1.000000",
            daily_wait_cost_ratio="0.001000",
        ),
        row(
            "research-watch",
            gross_edge_ratio="0.060000",
            fee_ratio="0.010000",
            spread_ratio="0.010000",
            slippage_ratio="0.005000",
            settlement_wait_days="3.000000",
            daily_wait_cost_ratio="0.001000",
            upstream_reason_codes=("thin_cost_basis",),
        ),
        row(
            "research-block",
            gross_edge_ratio="0.040000",
            fee_ratio="0.015000",
            spread_ratio="0.015000",
            slippage_ratio="0.010000",
            settlement_wait_days="8.000000",
            daily_wait_cost_ratio="0.001000",
        ),
    )


def test_pass_watch_block_statuses_and_cost_drag_metrics() -> None:
    sensitivity_report = report(*status_rows())

    assert is_dataclass(sensitivity_report)
    assert sensitivity_report.__dataclass_params__.frozen
    assert sensitivity_report.generated_at == GENERATED_AT
    assert sensitivity_report.config_version == (
        "research-strategy-cost-drag-sensitivity-report-v0"
    )
    assert sensitivity_report.input_count == d("3.000000")
    assert sensitivity_report.row_count == d("3.000000")
    assert sensitivity_report.pass_count == d("1.000000")
    assert sensitivity_report.watch_count == d("1.000000")
    assert sensitivity_report.block_count == d("1.000000")
    assert sensitivity_report.risk_status == "block"
    assert sensitivity_report.max_total_cost_drag_ratio == d("0.048000")
    assert sensitivity_report.max_cost_to_edge_ratio == d("1.200000")
    assert sensitivity_report.min_net_edge_ratio == d("-0.008000")
    assert sensitivity_report.max_settlement_wait_days == d("8.000000")
    assert sensitivity_report.reason_codes == (
        "cost_to_edge_block_present",
        "settlement_wait_block_present",
        "net_edge_depleted_block_present",
        "total_cost_drag_watch_present",
        "settlement_wait_watch_present",
        "cost_drag_sensitivity_watch_present",
    )

    blocked, watched, passed = sensitivity_report.rows
    assert tuple(item.risk_status for item in sensitivity_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(item.public_rank for item in sensitivity_report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert blocked.public_research_reference.startswith("research_ref_")
    assert blocked.public_research_reference != "research-block"
    assert blocked.settlement_wait_drag_ratio == d("0.008000")
    assert blocked.total_cost_drag_ratio == d("0.048000")
    assert blocked.net_edge_ratio == d("-0.008000")
    assert blocked.cost_to_edge_ratio == d("1.200000")
    assert blocked.reason_codes == (
        "cost_to_edge_block",
        "settlement_wait_block",
        "net_edge_depleted_block",
        "total_cost_drag_watch",
    )
    assert watched.reason_codes == (
        "thin_cost_basis",
        "total_cost_drag_watch",
        "settlement_wait_watch",
    )
    assert passed.reason_codes == ("cost_drag_sensitivity_passed",)
    assert all(item.risk_status in {"pass", "watch", "block"} for item in sensitivity_report.rows)


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = api()
    input_row = row("research-frozen")
    sensitivity_report = report(input_row)

    with pytest.raises(FrozenInstanceError):
        input_row.research_reference = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sensitivity_report.risk_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sensitivity_report.rows[0].risk_status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="fee_ratio must be a Decimal"):
        row("bad-decimal", fee_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="gross_edge_ratio must be a Decimal"):
        row("bad-subclass", gross_edge_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="research_reference must be a plain str"):
        row(_StringSubclass("bad-string"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_strategy_cost_drag_sensitivity_report(
            (input_row,),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(input_row, generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        report(row("future", evaluated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate research_reference"):
        report(row("dupe"), row("dupe"))

    public_records = (
        config(),
        input_row,
        sensitivity_report,
        sensitivity_report.rows[0],
    )
    for public_record in public_records:
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_public_payload_redacts_references_and_rejects_leakage() -> None:
    module = api()
    raw_reference = "candidate-17-market_slug-question-source_url-token"
    sensitivity_report = report(row(raw_reference))

    payload = module.research_strategy_cost_drag_sensitivity_report_to_jsonable(
        sensitivity_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert raw_reference not in encoded
    assert "candidate-17" not in encoded
    assert "market_slug" not in encoded
    assert "question" not in encoded
    assert "source_url" not in encoded
    assert "token" not in encoded
    assert payload["rows"][0]["public_research_reference"].startswith("research_ref_")
    assert payload["rows"][0]["gross_edge_ratio"] == "0.100000"
    assert payload["rows"][0]["evaluated_at"] == "2026-07-08T15:30:00+00:00"
    assert_no_float_values(payload)

    original_asdict = module.asdict
    try:
        module.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "candidate_id": "candidate-17",
        }
        with pytest.raises(ValueError, match="unsafe public surface field"):
            module.research_strategy_cost_drag_sensitivity_report_to_jsonable(
                sensitivity_report,
            )

        module.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "extra_note": "wallet_auth_order",
        }
        with pytest.raises(ValueError, match="unsafe public surface value"):
            module.research_strategy_cost_drag_sensitivity_report_to_jsonable(
                sensitivity_report,
            )
    finally:
        module.asdict = original_asdict  # type: ignore[method-assign]


def test_hard_flags_are_enforced_for_config_input_report_and_rows() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        row("bad-report-flag", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        row("bad-readonly-flag", readonly=False)

    sensitivity_report = report(row("tamper-row"))
    object.__setattr__(sensitivity_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.research_strategy_cost_drag_sensitivity_report_to_jsonable(
            sensitivity_report,
        )


def test_payload_is_deterministic_and_report_digest_is_consistent() -> None:
    module = api()
    first, second, third = status_rows()

    forward = report(first, second, third)
    reverse = report(third, second, first)
    assert forward == reverse

    forward_payload = module.research_strategy_cost_drag_sensitivity_report_to_jsonable(
        forward,
    )
    reverse_payload = module.research_strategy_cost_drag_sensitivity_report_to_jsonable(
        reverse,
    )
    assert json.dumps(forward_payload, sort_keys=True) == json.dumps(
        reverse_payload,
        sort_keys=True,
    )
    assert tuple(item["public_rank"] for item in forward_payload["rows"]) == (
        "1.000000",
        "2.000000",
        "3.000000",
    )

    digest = module.build_research_strategy_cost_drag_sensitivity_digest(forward)
    digest_payload = module.research_strategy_cost_drag_sensitivity_digest_to_jsonable(
        digest,
    )
    report_digest_payload = (
        module.research_strategy_cost_drag_sensitivity_report_digest_to_jsonable(forward)
    )

    assert digest.input_count == forward.input_count
    assert digest.row_count == forward.row_count
    assert digest.pass_count == forward.pass_count
    assert digest.watch_count == forward.watch_count
    assert digest.block_count == forward.block_count
    assert digest.risk_status == forward.risk_status
    assert digest.reason_codes == forward.reason_codes
    assert digest_payload == report_digest_payload
    assert "rows" not in digest_payload
    assert_no_float_values(digest_payload)


def test_module_has_no_forbidden_side_effect_or_public_action_surface() -> None:
    source = inspect.getsource(api()).lower()

    assert "float(" not in source
    assert ".total_seconds(" not in source
    assert "open(" not in source
    assert "path(" not in source
    assert "psycopg" not in source
    assert "sqlalchemy" not in source
    for fragment in (
        joined("net", "work"),
        joined("au", "th"),
        joined("wal", "let"),
        joined("or", "der"),
        joined("tra", "de"),
        joined("po", "sition"),
        joined("b", "uy"),
        joined("s", "ell"),
        joined("recom", "mend"),
        "socket",
        "requests",
        "http",
        "live",
    ):
        assert fragment not in source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
