from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import inspect
import json
from pathlib import Path
from typing import get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_depth_fragility_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return importlib.import_module(MODULE_NAME)


def config(**overrides: object):
    values = {
        "config_version": "research-market-depth-fragility-report-v0",
        "component_watch_score": d("0.350000"),
        "component_block_score": d("0.700000"),
        "composite_watch_score": d("0.350000"),
        "composite_block_score": d("0.700000"),
        "depth_weight": d("0.300000"),
        "spread_weight": d("0.250000"),
        "cost_weight": d("0.250000"),
        "settlement_weight": d("0.200000"),
    }
    values.update(overrides)
    return api().ResearchMarketDepthFragilityConfig(**values)


def market(
    market_slug: str,
    *,
    public_event_label: str = "public-event",
    observed_at: datetime | None = None,
    aggregate_depth_fragility_score: Decimal = d("0.100000"),
    spread_instability_score: Decimal = d("0.100000"),
    cost_pressure_score: Decimal = d("0.100000"),
    settlement_friction_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
):
    return api().ResearchMarketDepthFragilityInput(
        market_slug=market_slug,
        public_event_label=public_event_label,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=5)
        ),
        aggregate_depth_fragility_score=aggregate_depth_fragility_score,
        spread_instability_score=spread_instability_score,
        cost_pressure_score=cost_pressure_score,
        settlement_friction_score=settlement_friction_score,
        reason_codes=reason_codes,
    )


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    return api().build_research_market_depth_fragility_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_manual_review_surface() -> None:
    depth_report = report()
    mod = api()

    assert type(depth_report) is mod.ResearchMarketDepthFragilityReport
    assert depth_report.generated_at == GENERATED_AT
    assert depth_report.config_version == "research-market-depth-fragility-report-v0"
    assert depth_report.status == "block"
    assert depth_report.market_count == d("0.000000")
    assert depth_report.pass_count == d("0.000000")
    assert depth_report.watch_count == d("0.000000")
    assert depth_report.block_count == d("0.000000")
    assert depth_report.manual_review_count == d("0.000000")
    assert depth_report.average_composite_fragility_score is None
    assert depth_report.reason_codes == ("no_market_depth_fragility_inputs",)
    assert depth_report.reason_code_counts == (
        mod.ResearchMarketDepthFragilityReasonCodeCount(
            reason_code="no_market_depth_fragility_inputs",
            count=d("1.000000"),
        ),
    )
    assert depth_report.rows == ()
    assert depth_report.paper_only is True
    assert depth_report.report_only is True
    assert depth_report.readonly is True


def test_build_report_classifies_depth_spread_cost_and_settlement_fragility() -> None:
    depth_report = report(
        market(
            "market-watch",
            aggregate_depth_fragility_score=d("0.400000"),
            spread_instability_score=d("0.450000"),
            cost_pressure_score=d("0.360000"),
            settlement_friction_score=d("0.200000"),
            reason_codes=("manual_review",),
        ),
        market("market-pass"),
        market(
            "market-block",
            aggregate_depth_fragility_score=d("0.820000"),
            spread_instability_score=d("0.760000"),
            cost_pressure_score=d("0.500000"),
            settlement_friction_score=d("0.880000"),
        ),
    )

    assert depth_report.status == "block"
    assert depth_report.reason_codes == (
        "aggregate_depth_fragility_present",
        "spread_instability_present",
        "cost_pressure_present",
        "settlement_friction_present",
        "composite_fragility_present",
    )
    assert depth_report.market_count == d("3.000000")
    assert depth_report.pass_count == d("1.000000")
    assert depth_report.watch_count == d("1.000000")
    assert depth_report.block_count == d("1.000000")
    assert depth_report.manual_review_count == d("2.000000")
    assert depth_report.aggregate_depth_fragility_count == d("2.000000")
    assert depth_report.spread_instability_count == d("2.000000")
    assert depth_report.cost_pressure_count == d("2.000000")
    assert depth_report.settlement_friction_count == d("1.000000")
    assert depth_report.composite_fragility_count == d("2.000000")
    assert depth_report.average_aggregate_depth_fragility_score == d("0.440000")
    assert depth_report.average_spread_instability_score == d("0.436667")
    assert depth_report.average_cost_pressure_score == d("0.320000")
    assert depth_report.average_settlement_friction_score == d("0.393333")
    assert depth_report.average_composite_fragility_score == d("0.399833")

    assert tuple(row.market_slug for row in depth_report.rows) == (
        "market-block",
        "market-watch",
        "market-pass",
    )

    block_row, watch_row, pass_row = depth_report.rows
    assert block_row.status == "block"
    assert block_row.composite_fragility_score == d("0.737000")
    assert block_row.reason_codes == (
        "aggregate_depth_fragility_block",
        "composite_fragility_block",
        "cost_pressure_watch",
        "settlement_friction_block",
        "spread_instability_block",
    )

    assert watch_row.status == "watch"
    assert watch_row.composite_fragility_score == d("0.362500")
    assert watch_row.reason_codes == (
        "aggregate_depth_fragility_watch",
        "composite_fragility_watch",
        "cost_pressure_watch",
        "input_manual_review",
        "spread_instability_watch",
    )

    assert pass_row.status == "pass"
    assert pass_row.composite_fragility_score == d("0.100000")
    assert pass_row.reason_codes == ("market_depth_fragility_pass",)


def test_payload_and_digest_are_deterministic_decimal_strings_only() -> None:
    mod = api()
    first = report(
        market("z-market", settlement_friction_score=d("0.900000")),
        market("a-market", reason_codes=("zeta", "alpha")),
        market(
            "m-market",
            aggregate_depth_fragility_score=d("0.500000"),
            spread_instability_score=d("0.500000"),
        ),
    )
    repeated = report(*reversed(first.rows))

    payload = mod.research_market_depth_fragility_report_payload(first)
    repeated_payload = mod.research_market_depth_fragility_report_payload(repeated)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == repeated_payload
    assert mod.research_market_depth_fragility_report_digest(
        first,
    ) == mod.research_market_depth_fragility_report_digest(repeated)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["market_count"] == "3.000000"
    assert payload["rows"][0]["composite_fragility_score"] == "0.260000"
    assert tuple(
        (item.reason_code, item.count)
        for item in first.reason_code_counts
        if item.reason_code.startswith("input_")
    ) == (("input_alpha", d("1.000000")), ("input_zeta", d("1.000000")))
    assert _float_paths(payload) == ()
    assert ": 0.5" not in encoded


def test_public_contract_is_frozen_decimal_only_and_tamper_evident() -> None:
    mod = api()
    public_classes = (
        mod.ResearchMarketDepthFragilityConfig,
        mod.ResearchMarketDepthFragilityInput,
        mod.ResearchMarketDepthFragilityRow,
        mod.ResearchMarketDepthFragilityReasonCodeCount,
        mod.ResearchMarketDepthFragilityReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(public_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(public_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint), field_name

    input_row = market("frozen-market")
    with pytest.raises(FrozenInstanceError):
        input_row.market_slug = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="component_watch_score"):
        config(component_watch_score=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_instability_score"):
        market("bad-float", spread_instability_score=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_pressure_score"):
        market("bad-subclass", cost_pressure_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        market("bad-time", observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            market("bad-generated"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate market_slug"):
        report(market("dupe"), market("dupe"))
    with pytest.raises(ValueError, match="observed_at"):
        report(market("future", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="market_slug"):
        market("raw_market_id=abc")
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)

    built_report = report(market("tamper-market"))
    with pytest.raises(ValueError, match="composite_fragility_score"):
        replace(built_report.rows[0], composite_fragility_score=d("0.900000"))
    with pytest.raises(ValueError, match="status"):
        replace(built_report, status="watch")


def test_module_is_pure_report_only_without_live_or_action_surface() -> None:
    mod = api()
    source = inspect.getsource(mod)
    lowered = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    assert mod.__all__ == (
        "DEFAULT_RESEARCH_MARKET_DEPTH_FRAGILITY_REPORT_CONFIG_VERSION",
        "MARKET_DEPTH_FRAGILITY_STATUSES",
        "ResearchMarketDepthFragilityConfig",
        "ResearchMarketDepthFragilityInput",
        "ResearchMarketDepthFragilityReasonCodeCount",
        "ResearchMarketDepthFragilityReport",
        "ResearchMarketDepthFragilityRow",
        "build_research_market_depth_fragility_report",
        "research_market_depth_fragility_report_digest",
        "research_market_depth_fragility_report_payload",
    )
    assert mod.MARKET_DEPTH_FRAGILITY_STATUSES == ("pass", "watch", "block")

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "patch",
                "place",
                "post",
                "put",
                "request",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live trading",
        "position sizing",
        "position_size",
        "trade recommendation",
        "buy",
        "sell",
    ):
        assert forbidden not in lowered

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_fragility_report.py"
    )
    assert module_path.read_text(encoding="utf-8") == source


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))
