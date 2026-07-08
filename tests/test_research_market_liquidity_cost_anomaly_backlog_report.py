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


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_liquidity_cost_anomaly_backlog_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def backlog():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_liquidity_cost_anomaly_backlog_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def public_key(seed: str) -> str:
    return "sha256:" + seed * 64


def signal(
    public_backlog_key: str = public_key("a"),
    *,
    observed_at: datetime = datetime(2026, 7, 8, 14, 55, tzinfo=UTC),
    spread_shock_bps: str | Decimal = "3.000000",
    depth_fade_ratio: str | Decimal = "0.050000",
    quote_staleness_seconds: str | Decimal = "20.000000",
    fee_friction_bps: str | Decimal = "4.000000",
    volume_burst_ratio: str | Decimal = "1.200000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = backlog()
    return module.ResearchMarketLiquidityCostAnomalyBacklogReportInput(
        public_backlog_key=public_backlog_key,
        observed_at=observed_at,
        spread_shock_bps=(
            spread_shock_bps if isinstance(spread_shock_bps, Decimal) else d(spread_shock_bps)
        ),
        depth_fade_ratio=(
            depth_fade_ratio if isinstance(depth_fade_ratio, Decimal) else d(depth_fade_ratio)
        ),
        quote_staleness_seconds=(
            quote_staleness_seconds
            if isinstance(quote_staleness_seconds, Decimal)
            else d(quote_staleness_seconds)
        ),
        fee_friction_bps=(
            fee_friction_bps if isinstance(fee_friction_bps, Decimal) else d(fee_friction_bps)
        ),
        volume_burst_ratio=(
            volume_burst_ratio if isinstance(volume_burst_ratio, Decimal) else d(volume_burst_ratio)
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**kwargs: object):
    module = backlog()
    return module.ResearchMarketLiquidityCostAnomalyBacklogReportConfig(**kwargs)


def report(*rows: object, cfg: object | None = None):
    module = backlog()
    return module.build_research_market_liquidity_cost_anomaly_backlog_report(
        rows,
        config=(
            cfg
            if cfg is not None
            else module.ResearchMarketLiquidityCostAnomalyBacklogReportConfig()
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )


def blocked_signal():
    return signal(
        public_key("b"),
        observed_at=datetime(2026, 7, 8, 10, 40, tzinfo=timezone(timedelta(hours=-4))),
        spread_shock_bps="42.000000",
        depth_fade_ratio="0.720000",
        quote_staleness_seconds="420.000000",
        fee_friction_bps="72.000000",
        volume_burst_ratio="6.500000",
    )


def watch_signal():
    return signal(
        public_key("c"),
        spread_shock_bps="12.500000",
        depth_fade_ratio="0.320000",
        quote_staleness_seconds="130.000000",
        fee_friction_bps="22.000000",
        volume_burst_ratio="2.400000",
    )


def test_empty_input_returns_report_only_block_backlog() -> None:
    module = backlog()

    summary = report()

    assert isinstance(
        summary,
        module.ResearchMarketLiquidityCostAnomalyBacklogReport,
    )
    assert is_dataclass(summary)
    assert summary.__dataclass_params__.frozen
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        "research-market-liquidity-cost-anomaly-backlog-report-v0"
    )
    assert summary.backlog_status == "block"
    assert summary.input_count == d("0.000000")
    assert summary.row_count == d("0.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.block_count == d("0.000000")
    assert summary.liquidity_cost_anomaly_score == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("liquidity_cost_anomaly_backlog_empty",)
    assert summary.reason_code_counts == (
        module.ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount(
            reason_code="liquidity_cost_anomaly_backlog_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert summary.report_digest.startswith("sha256:")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_block_watch_and_pass_rows_build_public_safe_backlog() -> None:
    summary = report(blocked_signal(), watch_signal(), signal(public_key("d")))

    assert summary.backlog_status == "block"
    assert summary.input_count == d("3.000000")
    assert summary.row_count == d("3.000000")
    assert summary.block_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.spread_shock_count == d("2.000000")
    assert summary.depth_fade_count == d("2.000000")
    assert summary.quote_staleness_count == d("2.000000")
    assert summary.fee_friction_count == d("2.000000")
    assert summary.volume_burst_count == d("2.000000")
    assert summary.max_spread_shock_bps == d("42.000000")
    assert summary.max_depth_fade_ratio == d("0.720000")
    assert summary.max_quote_staleness_seconds == d("420.000000")
    assert summary.max_fee_friction_bps == d("72.000000")
    assert summary.max_volume_burst_ratio == d("6.500000")
    assert summary.liquidity_cost_anomaly_score == d("0.500000")

    assert tuple(row.public_backlog_key for row in summary.rows) == (
        public_key("b"),
        public_key("c"),
        public_key("d"),
    )

    blocked, watched, passed = summary.rows
    assert blocked.backlog_status == "block"
    assert blocked.observed_at == datetime(2026, 7, 8, 14, 40, tzinfo=UTC)
    assert blocked.risk_score == d("1.000000")
    assert blocked.reason_codes == (
        "liquidity_cost_spread_shock_block",
        "liquidity_cost_depth_fade_block",
        "liquidity_cost_quote_staleness_block",
        "liquidity_cost_fee_friction_block",
        "liquidity_cost_volume_burst_block",
    )
    assert watched.backlog_status == "watch"
    assert watched.risk_score == d("0.500000")
    assert watched.reason_codes == (
        "liquidity_cost_spread_shock_watch",
        "liquidity_cost_depth_fade_watch",
        "liquidity_cost_quote_staleness_watch",
        "liquidity_cost_fee_friction_watch",
        "liquidity_cost_volume_burst_watch",
    )
    assert passed.backlog_status == "pass"
    assert passed.reason_codes == ("liquidity_cost_anomaly_pass",)

    assert summary.reason_codes == (
        "liquidity_cost_spread_shock_block",
        "liquidity_cost_spread_shock_watch",
        "liquidity_cost_depth_fade_block",
        "liquidity_cost_depth_fade_watch",
        "liquidity_cost_quote_staleness_block",
        "liquidity_cost_quote_staleness_watch",
        "liquidity_cost_fee_friction_block",
        "liquidity_cost_fee_friction_watch",
        "liquidity_cost_volume_burst_block",
        "liquidity_cost_volume_burst_watch",
        "liquidity_cost_anomaly_watch_present",
    )
    assert summary.reason_code_counts[-1] == (
        backlog().ResearchMarketLiquidityCostAnomalyBacklogReasonCodeCount(
            reason_code="liquidity_cost_anomaly_watch_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_non_default_thresholds_can_downgrade_watch_metrics_to_pass() -> None:
    cfg = config(
        watch_spread_shock_bps=d("20.000000"),
        block_spread_shock_bps=d("60.000000"),
        watch_depth_fade_ratio=d("0.400000"),
        block_depth_fade_ratio=d("0.800000"),
        watch_quote_staleness_seconds=d("180.000000"),
        block_quote_staleness_seconds=d("600.000000"),
        watch_fee_friction_bps=d("30.000000"),
        block_fee_friction_bps=d("90.000000"),
        watch_volume_burst_ratio=d("3.000000"),
        block_volume_burst_ratio=d("8.000000"),
    )

    summary = report(watch_signal(), cfg=cfg)

    assert summary.backlog_status == "pass"
    assert summary.rows[0].backlog_status == "pass"
    assert summary.rows[0].reason_codes == ("liquidity_cost_anomaly_pass",)
    assert summary.reason_codes == ("liquidity_cost_anomaly_backlog_clear",)
    assert summary.liquidity_cost_anomaly_score == d("0.000000")


def test_rows_reason_codes_and_digest_are_deterministic() -> None:
    first = watch_signal()
    second = blocked_signal()
    third = signal(public_key("d"))

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.public_backlog_key for row in forward.rows) == (
        public_key("b"),
        public_key("c"),
        public_key("d"),
    )
    assert forward.reason_code_counts == tuple(
        sorted(
            forward.reason_code_counts,
            key=lambda item: forward.reason_codes.index(item.reason_code),
        ),
    )
    assert forward.report_digest == reverse.report_digest
    assert (
        backlog().research_market_liquidity_cost_anomaly_backlog_report_digest(forward)
        == forward.report_digest
    )


def test_validation_frozen_dataclasses_decimal_inputs_and_hard_flags() -> None:
    module = backlog()
    row = signal(public_key("e"))
    summary = report(row)

    with pytest.raises(FrozenInstanceError):
        row.public_backlog_key = public_key("f")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.backlog_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadInput",
            (module.ResearchMarketLiquidityCostAnomalyBacklogReportInput,),
            {},
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(public_key("f"), observed_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="spread_shock_bps must be a Decimal"):
        signal(public_key("f"), spread_shock_bps=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="public_backlog_key must be a plain str"):
        signal(_StringSubclass(public_key("f")))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_market_liquidity_cost_anomaly_backlog_report(
            (row,),
            config=module.ResearchMarketLiquidityCostAnomalyBacklogReportConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs must contain"):
        report("not-an-input")
    with pytest.raises(ValueError, match="duplicate public_backlog_key"):
        report(signal(public_key("f")), signal(public_key("f")))
    with pytest.raises(ValueError, match="paper_only"):
        signal(public_key("f"), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="watch_spread_shock_bps"):
        config(
            watch_spread_shock_bps=d("70.000000"),
            block_spread_shock_bps=d("60.000000"),
        )
    with pytest.raises(ValueError, match="watch_depth_fade_ratio"):
        config(
            watch_depth_fade_ratio=d("0.900000"),
            block_depth_fade_ratio=d("0.800000"),
        )

    valid_row = summary.rows[0]
    with pytest.raises(ValueError, match="risk_score must match"):
        replace(valid_row, risk_score=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "liquidity_cost_anomaly_pass",
                "liquidity_cost_quote_staleness_watch",
            ),
        )
    with pytest.raises(ValueError, match="report_digest must match"):
        replace(summary, report_digest="sha256:" + "0" * 64)


def test_payload_uses_decimal_strings_digest_and_no_raw_identifiers() -> None:
    module = backlog()
    summary = report(blocked_signal(), watch_signal(), signal(public_key("d")))

    payload = module.research_market_liquidity_cost_anomaly_backlog_report_payload(
        summary,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "3.000000"
    assert payload["liquidity_cost_anomaly_score"] == "0.500000"
    assert payload["max_quote_staleness_seconds"] == "420.000000"
    assert payload["rows"][0]["spread_shock_bps"] == "42.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T14:40:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.333333"
    assert payload["report_digest"] == summary.report_digest
    assert payload["report_digest"].startswith("sha256:")
    json.dumps(payload, sort_keys=True)

    forbidden_keys = {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_id",
        "source_url",
        "raw_market",
        "raw_source",
    }

    def walk_payload(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in forbidden_keys
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "submit" not in lowered
                assert "cancel" not in lowered
                assert "replace" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.ResearchMarketLiquidityCostAnomalyBacklogReportConfig(),
        signal(public_key("e")),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_module_has_no_forbidden_side_effect_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
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
        "sqlite",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "submit",
        "cancel",
        "replace_order",
        "place_order",
        "sizing",
        "recommendation",
        "getenv",
        "environ",
        "connect(",
        "execute(",
    ):
        assert forbidden not in source.lower()
