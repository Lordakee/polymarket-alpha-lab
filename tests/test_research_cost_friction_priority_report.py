from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_cost_friction_priority_report import (
    DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION,
    ResearchCostFrictionPriorityConfig,
    ResearchCostFrictionPriorityInput,
    ResearchCostFrictionPriorityReasonCodeCount,
    ResearchCostFrictionPriorityReport,
    ResearchCostFrictionPriorityRow,
    build_research_cost_friction_priority_report,
    research_cost_friction_priority_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 15, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 15, 10, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCostFrictionPriorityConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION,
        "max_pass_total_friction_rate": d("0.030000"),
        "max_watch_total_friction_rate": d("0.060000"),
        "max_pass_spread_rate": d("0.020000"),
        "max_watch_spread_rate": d("0.040000"),
        "max_pass_settlement_delay_days": d("7.000000"),
        "max_watch_settlement_delay_days": d("30.000000"),
        "max_pass_resolution_dispute_risk": d("0.200000"),
        "max_watch_resolution_dispute_risk": d("0.500000"),
        "min_pass_liquidity_score": d("0.600000"),
        "min_watch_liquidity_score": d("0.300000"),
        "settlement_delay_cost_per_day": d("0.000100"),
    }
    values.update(overrides)
    return ResearchCostFrictionPriorityConfig(**values)


def event(
    event_id: str = "internal-event-alpha",
    *,
    market_slug: str = "market-election-2028",
    source_label: str = "source-newswire-alpha",
    fee_rate: Decimal = d("0.004000"),
    spread_rate: Decimal = d("0.010000"),
    slippage_rate: Decimal = d("0.005000"),
    settlement_delay_days: Decimal = d("2.000000"),
    resolution_dispute_risk: Decimal = d("0.100000"),
    liquidity_score: Decimal = d("0.800000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("cost_inputs_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchCostFrictionPriorityInput:
    return ResearchCostFrictionPriorityInput(
        event_id=event_id,
        market_slug=market_slug,
        source_label=source_label,
        fee_rate=fee_rate,
        spread_rate=spread_rate,
        slippage_rate=slippage_rate,
        settlement_delay_days=settlement_delay_days,
        resolution_dispute_risk=resolution_dispute_risk,
        liquidity_score=liquidity_score,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchCostFrictionPriorityInput,
    cfg: ResearchCostFrictionPriorityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCostFrictionPriorityReport:
    return build_research_cost_friction_priority_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def test_scores_pass_watch_and_block_cost_friction_rows() -> None:
    digest = report(
        event(
            "event-pass",
            market_slug="market-low-cost-alpha",
            source_label="source-internal-alpha",
            reason_codes=("low_cost_snapshot_ready",),
        ),
        event(
            "event-watch",
            market_slug="market-wide-spread-beta",
            source_label="source-internal-beta",
            fee_rate=d("0.010000"),
            spread_rate=d("0.025000"),
            slippage_rate=d("0.012000"),
            settlement_delay_days=d("14.000000"),
            resolution_dispute_risk=d("0.300000"),
            liquidity_score=d("0.500000"),
        ),
        event(
            "event-block",
            market_slug="market-friction-heavy-gamma",
            source_label="source-internal-gamma",
            fee_rate=d("0.020000"),
            spread_rate=d("0.050000"),
            slippage_rate=d("0.020000"),
            settlement_delay_days=d("45.000000"),
            resolution_dispute_risk=d("0.700000"),
            liquidity_score=d("0.200000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "research-cost-friction-priority-report-v0"
    assert digest.event_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.max_total_friction_rate == d("0.094500")
    assert digest.max_spread_rate == d("0.050000")
    assert digest.max_settlement_delay_days == d("45.000000")
    assert digest.max_resolution_dispute_risk == d("0.700000")
    assert digest.min_liquidity_score == d("0.200000")
    assert digest.status == "blocked"
    assert digest.summary_explanation == (
        "blocked: one or more cost friction rows exceed research limits"
    )
    assert digest.reason_codes == (
        "cost_friction_report_blocked",
        "cost_total_friction_blocked",
        "cost_spread_blocked",
        "cost_settlement_delay_blocked",
        "cost_resolution_friction_blocked",
        "cost_liquidity_thin_blocked",
        "cost_total_friction_watch",
        "cost_spread_watch",
        "cost_settlement_delay_watch",
        "cost_resolution_friction_watch",
        "cost_liquidity_thin_watch",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.priority_status for row in digest.rows) == ("blocked", "watch", "pass")
    assert blocked.event_id == "event-block"
    assert blocked.total_friction_rate == d("0.094500")
    assert blocked.settlement_friction_rate == d("0.004500")
    assert blocked.priority_score == d("1.000000")
    assert blocked.friction_explanation == (
        "blocked: cost friction exceeds research limits; keep in research queue"
    )
    assert blocked.reason_codes == (
        "cost_inputs_ready",
        "cost_total_friction_blocked",
        "cost_spread_blocked",
        "cost_settlement_delay_blocked",
        "cost_resolution_friction_blocked",
        "cost_liquidity_thin_blocked",
    )
    assert watched.priority_status == "watch"
    assert watched.total_friction_rate == d("0.048400")
    assert watched.reason_codes == (
        "cost_inputs_ready",
        "cost_total_friction_watch",
        "cost_spread_watch",
        "cost_settlement_delay_watch",
        "cost_resolution_friction_watch",
        "cost_liquidity_thin_watch",
    )
    assert passed.priority_status == "pass"
    assert passed.reason_codes == ("low_cost_snapshot_ready", "cost_friction_clear")

    assert digest.reason_code_counts[0] == ResearchCostFrictionPriorityReasonCodeCount(
        reason_code="cost_inputs_ready",
        count=d("2.000000"),
        event_ratio=d("0.666667"),
    )


def test_empty_report_is_pass_with_decimal_counts_and_frozen_flags() -> None:
    digest = report()

    assert digest.event_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.max_total_friction_rate == ZERO
    assert digest.status == "pass"
    assert digest.summary_explanation == "pass: no cost friction rows supplied"
    assert digest.reason_codes == ("cost_friction_report_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()

    populated = report(event())
    for value in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            if item.name.endswith(("_count", "_rate", "_days", "_risk", "_score", "_ratio")):
                assert type(item_value) is Decimal

    frozen = event()
    with pytest.raises(FrozenInstanceError):
        frozen.event_id = "changed"  # type: ignore[misc]


def test_public_payload_uses_decimal_strings_and_hides_market_and_source_details() -> None:
    digest = report(
        event(
            observed_at=datetime(
                2026,
                7,
                6,
                8,
                10,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            6,
            8,
            30,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = research_cost_friction_priority_report_payload(digest)

    assert payload["generated_at"] == "2026-07-06T15:30:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["max_total_friction_rate"] == "0.019200"
    assert payload["derived_validation_digest"] == digest.derived_validation_digest
    assert payload["rows"][0]["public_event_ref"] == "event_000001"
    assert payload["rows"][0]["priority_status"] == "pass"
    assert payload["rows"][0]["total_friction_rate"] == "0.019200"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T15:10:00+00:00"
    assert "event_id" not in payload["rows"][0]
    assert "market_slug" not in payload["rows"][0]
    assert "source_label" not in payload["rows"][0]

    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "internal-event-alpha",
        "market-election-2028",
        "source-newswire-alpha",
        "buy",
        "sell",
        "position",
        "recommendation",
    ):
        assert forbidden not in encoded
    assert_no_public_numeric_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_cost_friction_priority_report_payload(tampered)

    with pytest.raises(ValueError, match="pass_count"):
        replace(digest, pass_count=d("2.000000"))


def test_public_payload_rejects_unsafe_keys_values_flags_and_numbers() -> None:
    payload = research_cost_friction_priority_report_payload(report(event()))

    for key in (
        "market_slug",
        "source_label",
        "live_url",
        "auth_header",
        "wallet_address",
        "order_id",
        "network_url",
        "database_table",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_instruction",
        "sell_instruction",
        "position_size",
        "recommendation_text",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_cost_friction_priority_report_payload(unsafe)

    for value in (
        "market slug hidden",
        "source label hidden",
        "live quote",
        "auth token",
        "wallet signer",
        "buy now",
        "sell now",
        "position sizing",
        "recommendation",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            research_cost_friction_priority_report_payload(unsafe)

    numeric = dict(payload)
    numeric["event_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_cost_friction_priority_report_payload(numeric)

    decimal_numeric = dict(payload)
    decimal_numeric["event_count"] = d("1.000000")
    with pytest.raises(ValueError, match="numeric"):
        research_cost_friction_priority_report_payload(decimal_numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_cost_friction_priority_report_payload(downgraded)


def test_validation_rejects_non_decimal_values_duplicates_and_bad_time_boundaries() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        event(fee_rate=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        event(fee_rate=_DecimalSubclass("0.010000"))

    with pytest.raises(ValueError, match="fee_rate"):
        event(fee_rate=d("-0.010000"))

    with pytest.raises(ValueError, match="observed_at"):
        event(observed_at=datetime(2026, 7, 6, 15, 10))

    with pytest.raises(ValueError, match="observed_at"):
        event(
            observed_at=_DatetimeSubclass(
                2026,
                7,
                6,
                15,
                10,
                tzinfo=UTC,
            ),
        )

    with pytest.raises(ValueError, match="generated_at"):
        report(event("aware"), generated_at=datetime(2026, 7, 6, 15, 30))

    with pytest.raises(ValueError, match="future"):
        report(event(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        report(event("duplicate"), event("duplicate"))

    with pytest.raises(ValueError, match="paper_only"):
        event(paper_only=False)

    with pytest.raises(ValueError, match="threshold"):
        config(max_pass_total_friction_rate=d("0.070000"))

    with pytest.raises(ValueError, match="subclass"):
        ResearchCostFrictionPriorityConfig.__new__(
            type(
                "ConfigSubclass",
                (ResearchCostFrictionPriorityConfig,),
                {},
            ),
        )


def test_report_constructors_reject_inconsistent_materialized_fields() -> None:
    digest = report(event())
    row = digest.rows[0]

    with pytest.raises(ValueError, match="total_friction_rate"):
        ResearchCostFrictionPriorityRow(
            **{
                **row.__dict__,
                "total_friction_rate": d("0.010000"),
            },
        )

    with pytest.raises(ValueError, match="status"):
        ResearchCostFrictionPriorityReport(
            **{
                **digest.__dict__,
                "status": "blocked",
            },
        )


def test_module_exposes_no_live_order_wallet_db_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_cost_friction_priority_report.py"
    )
    tree = ast.parse(module_path.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
