from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_cost_regime_shift_alert_report import (
    COST_REGIME_SHIFT_ALERT_STATUSES,
    DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION,
    ResearchMarketCostRegimeShiftAlertConfig,
    ResearchMarketCostRegimeShiftAlertInput,
    ResearchMarketCostRegimeShiftAlertReasonCodeCount,
    ResearchMarketCostRegimeShiftAlertReport,
    ResearchMarketCostRegimeShiftAlertRow,
    build_research_market_cost_regime_shift_alert_report,
    research_market_cost_regime_shift_alert_report_payload,
    validate_research_market_cost_regime_shift_alert_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 18, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_cost_regime_shift_alert_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def case_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def config(**overrides: object) -> ResearchMarketCostRegimeShiftAlertConfig:
    values: dict[str, object] = {
        "config_version": DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION,
        "watch_total_cost_rate": d("0.060000"),
        "block_total_cost_rate": d("0.100000"),
        "watch_cost_increase_rate": d("0.020000"),
        "block_cost_increase_rate": d("0.050000"),
    }
    values.update(overrides)
    return ResearchMarketCostRegimeShiftAlertConfig(**values)


def input_row(
    source_reference: str = "case-pass",
    *,
    baseline_spread_rate: Decimal = d("0.005000"),
    current_spread_rate: Decimal = d("0.006000"),
    baseline_depth_impact_rate: Decimal = d("0.005000"),
    current_depth_impact_rate: Decimal = d("0.006000"),
    baseline_slippage_rate: Decimal = d("0.004000"),
    current_slippage_rate: Decimal = d("0.005000"),
    baseline_fee_drag_rate: Decimal = d("0.003000"),
    current_fee_drag_rate: Decimal = d("0.004000"),
    baseline_volatility_cost_rate: Decimal = d("0.002000"),
    current_volatility_cost_rate: Decimal = d("0.003000"),
    baseline_settlement_friction_rate: Decimal = d("0.001000"),
    current_settlement_friction_rate: Decimal = d("0.002000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketCostRegimeShiftAlertInput:
    return ResearchMarketCostRegimeShiftAlertInput(
        source_reference=source_reference,
        baseline_spread_rate=baseline_spread_rate,
        current_spread_rate=current_spread_rate,
        baseline_depth_impact_rate=baseline_depth_impact_rate,
        current_depth_impact_rate=current_depth_impact_rate,
        baseline_slippage_rate=baseline_slippage_rate,
        current_slippage_rate=current_slippage_rate,
        baseline_fee_drag_rate=baseline_fee_drag_rate,
        current_fee_drag_rate=current_fee_drag_rate,
        baseline_volatility_cost_rate=baseline_volatility_cost_rate,
        current_volatility_cost_rate=current_volatility_cost_rate,
        baseline_settlement_friction_rate=baseline_settlement_friction_rate,
        current_settlement_friction_rate=current_settlement_friction_rate,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketCostRegimeShiftAlertInput,
    cfg: ResearchMarketCostRegimeShiftAlertConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketCostRegimeShiftAlertReport:
    return build_research_market_cost_regime_shift_alert_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def redigest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    updated: dict[str, Any] = json.loads(json.dumps(payload))
    digest_payload = dict(updated)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    updated["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return updated


def test_builds_cost_regime_shift_alert_counts_and_rows() -> None:
    built = report(
        input_row(
            "case-watch",
            current_spread_rate=d("0.015000"),
            current_depth_impact_rate=d("0.014000"),
            current_slippage_rate=d("0.010000"),
            current_fee_drag_rate=d("0.006000"),
            current_volatility_cost_rate=d("0.006000"),
            current_settlement_friction_rate=d("0.005000"),
        ),
        input_row(
            "case-block",
            current_spread_rate=d("0.030000"),
            current_depth_impact_rate=d("0.025000"),
            current_slippage_rate=d("0.020000"),
            current_fee_drag_rate=d("0.015000"),
            current_volatility_cost_rate=d("0.014000"),
            current_settlement_friction_rate=d("0.010000"),
            upstream_reason_codes=("manual_recheck",),
        ),
        input_row("case-pass", upstream_reason_codes=("monitor_only",)),
    )

    assert COST_REGIME_SHIFT_ALERT_STATUSES == ("pass", "watch", "block")
    assert type(built) is ResearchMarketCostRegimeShiftAlertReport
    assert built.generated_at == GENERATED_AT
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_current_total_cost_rate == d("0.114000")
    assert built.max_cost_increase_rate == d("0.094000")
    assert built.average_cost_increase_rate == d("0.045333")
    assert built.status == "block"
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    block_row, watch_row, pass_row = built.rows
    assert [(row.alert_status, row.cost_increase_rate) for row in built.rows] == [
        ("block", d("0.094000")),
        ("watch", d("0.036000")),
        ("pass", d("0.006000")),
    ]
    assert tuple(row.case_digest for row in built.rows) == (
        case_digest("case-block"),
        case_digest("case-watch"),
        case_digest("case-pass"),
    )
    assert type(block_row) is ResearchMarketCostRegimeShiftAlertRow
    assert block_row.baseline_total_cost_rate == d("0.020000")
    assert block_row.current_total_cost_rate == d("0.114000")
    assert block_row.reason_codes == (
        "cost_regime_depth_shift",
        "cost_regime_fee_drag_shift",
        "cost_regime_settlement_friction_shift",
        "cost_regime_shift_block",
        "cost_regime_slippage_shift",
        "cost_regime_spread_shift",
        "cost_regime_status_block",
        "cost_regime_volatility_shift",
        "input_manual_recheck",
    )
    assert watch_row.current_total_cost_rate == d("0.056000")
    assert "cost_regime_shift_watch" in watch_row.reason_codes
    assert pass_row.reason_codes == (
        "cost_regime_depth_shift",
        "cost_regime_fee_drag_shift",
        "cost_regime_settlement_friction_shift",
        "cost_regime_slippage_shift",
        "cost_regime_spread_shift",
        "cost_regime_status_pass",
        "cost_regime_volatility_shift",
        "input_monitor_only",
    )

    counts_by_code = {item.reason_code: item.count for item in built.reason_code_counts}
    assert counts_by_code["cost_regime_spread_shift"] == d("3.000000")
    assert counts_by_code["cost_regime_status_block"] == d("1.000000")
    assert built.reason_code_counts == tuple(
        sorted(built.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert built.reason_codes == tuple(sorted(built.reason_codes))


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    first = research_market_cost_regime_shift_alert_report_payload(
        report(
            input_row("case-z", upstream_reason_codes=("zeta", "alpha")),
            input_row("case-a", upstream_reason_codes=("alpha", "zeta")),
        ),
    )
    second = research_market_cost_regime_shift_alert_report_payload(
        report(
            input_row("case-a", upstream_reason_codes=("zeta", "alpha")),
            input_row("case-z", upstream_reason_codes=("alpha", "zeta")),
        ),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True)
    assert not any(isinstance(value, float) for value in walk_values(first))
    assert not any(isinstance(value, Decimal) for value in walk_values(first))
    assert first["row_count"] == "2.000000"
    assert first["rows"][0]["current_spread_rate"] == "0.006000"
    assert first["rows"][0]["cost_increase_rate"] == "0.006000"
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True

    digest_payload = dict(first)
    provided_digest = digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert provided_digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert validate_research_market_cost_regime_shift_alert_report_payload(first) == first

    tampered = dict(first)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_market_cost_regime_shift_alert_report_payload(tampered)


def test_public_payload_excludes_raw_references_market_text_urls_and_live_surfaces() -> None:
    source_reference = (
        "candidate-777 market_id=123 market_slug=will-this-resolve "
        "question=https://example.test/source?token=secret dsn=postgres "
        "table_name=orders wallet=abc trade=manual live_surface"
    )
    built = report(input_row(source_reference))
    payload = research_market_cost_regime_shift_alert_report_payload(built)
    rendered = repr(payload).lower()

    for forbidden in (
        "candidate-777",
        "market_id",
        "market_slug",
        "will-this-resolve",
        "question=",
        "https://example.test",
        "token=secret",
        "dsn=postgres",
        "table_name",
        "orders",
        "wallet=abc",
        "trade=manual",
        "live_surface",
        "source_reference",
    ):
        assert forbidden not in rendered


@pytest.mark.parametrize(
    "unsafe_reason_code",
    (
        "candidate-777",
        "market-id-123",
        "market-slug-will-this-resolve",
        "source_text_excerpt",
        "source-url",
        "recommendation_surface",
        "position_sizing",
    ),
)
def test_upstream_reason_codes_reject_public_market_action_leakage(
    unsafe_reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="reason_code has unsafe public payload"):
        input_row(upstream_reason_codes=(unsafe_reason_code,))


def test_payload_validation_rejects_redigested_invalid_public_shapes() -> None:
    payload = research_market_cost_regime_shift_alert_report_payload(report(input_row()))

    nested_flag = json.loads(json.dumps(payload))
    nested_flag["rows"][0]["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        validate_research_market_cost_regime_shift_alert_report_payload(
            redigest_payload(nested_flag),
        )

    invalid_status = json.loads(json.dumps(payload))
    invalid_status["rows"][0]["alert_status"] = "hold"
    with pytest.raises(ValueError, match="alert_status"):
        validate_research_market_cost_regime_shift_alert_report_payload(
            redigest_payload(invalid_status),
        )

    float_count = json.loads(json.dumps(payload))
    float_count["row_count"] = 1.0
    with pytest.raises(ValueError, match="row_count"):
        validate_research_market_cost_regime_shift_alert_report_payload(
            redigest_payload(float_count),
        )


def test_validation_rejects_non_decimal_values_bad_datetimes_flags_and_inconsistent_rows() -> None:
    with pytest.raises(ValueError, match="current_spread_rate"):
        input_row(current_spread_rate=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="baseline_spread_rate"):
        input_row(baseline_spread_rate=_DecimalSubclass("0.005000"))

    with pytest.raises(ValueError, match="watch_total_cost_rate"):
        config(watch_total_cost_rate=d("-0.010000"))

    with pytest.raises(ValueError, match="block_total_cost_rate"):
        config(block_total_cost_rate=d("0.050000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 18, 30))

    with pytest.raises(ValueError, match="datetime"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        report(input_row(readonly=False))

    built = report(input_row())
    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_market_cost_regime_shift_alert_report_payload(unsafe_report)

    inconsistent_row = replace(
        built.rows[0],
        current_total_cost_rate=d("0.999000"),
    )
    with pytest.raises(ValueError, match="current_total_cost_rate"):
        ResearchMarketCostRegimeShiftAlertReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION,
            status="pass",
            input_count=d("1.000000"),
            row_count=d("1.000000"),
            pass_count=d("1.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            max_current_total_cost_rate=d("0.999000"),
            max_cost_increase_rate=inconsistent_row.cost_increase_rate,
            average_cost_increase_rate=inconsistent_row.cost_increase_rate,
            reason_codes=inconsistent_row.reason_codes,
            reason_code_counts=(),
            rows=(inconsistent_row,),
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_only_numeric_fields() -> None:
    built = report(input_row())

    for item in (config(), input_row(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]

    public_classes = (
        ResearchMarketCostRegimeShiftAlertConfig,
        ResearchMarketCostRegimeShiftAlertInput,
        ResearchMarketCostRegimeShiftAlertRow,
        ResearchMarketCostRegimeShiftAlertReasonCodeCount,
        ResearchMarketCostRegimeShiftAlertReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_empty_report_is_report_only_readonly_and_has_valid_digest() -> None:
    built = report()
    payload = research_market_cost_regime_shift_alert_report_payload(built)

    assert built.input_count == d("0.000000")
    assert built.row_count == d("0.000000")
    assert built.status == "block"
    assert built.reason_codes == ("cost_regime_shift_alert_report_empty",)
    assert built.reason_code_counts == ()
    assert built.rows == ()
    assert payload["generated_at"] == "2026-07-08T18:30:00+00:00"
    assert validate_research_market_cost_regime_shift_alert_report_payload(payload) == payload


def test_module_has_no_io_or_market_action_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "private_key",
        "api_key",
        "requests",
        "httpx",
        "urllib",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "redis",
        "os.environ",
        "getenv",
        "open(",
        "read_text",
        "write_text",
        "path(",
        "connect(",
        "execute(",
    ):
        assert token not in source

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
