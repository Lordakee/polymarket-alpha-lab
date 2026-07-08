from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_cost_input_refresh_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_COST_INPUT_REFRESH_SLA_REPORT_CONFIG_VERSION
        ),
        "max_pass_fee_age_seconds": d("3600.000000"),
        "max_watch_fee_age_seconds": d("14400.000000"),
        "max_pass_spread_observation_age_seconds": d("300.000000"),
        "max_watch_spread_observation_age_seconds": d("1200.000000"),
        "min_pass_depth_confidence": d("0.800000"),
        "min_watch_depth_confidence": d("0.550000"),
        "max_pass_settlement_friction_rate": d("0.005000"),
        "max_watch_settlement_friction_rate": d("0.020000"),
        "max_pass_manual_recheck_urgency": d("0.300000"),
        "max_watch_manual_recheck_urgency": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostInputRefreshSlaConfig(**values)


def input_row(
    research_key: str = "refresh-case-pass",
    *,
    fee_age_seconds: Decimal = d("1800.000000"),
    spread_observation_age_seconds: Decimal = d("120.000000"),
    depth_confidence: Decimal = d("0.900000"),
    settlement_friction_rate: Decimal = d("0.002000"),
    manual_recheck_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketCostInputRefreshSlaInput(
        research_key=research_key,
        fee_age_seconds=fee_age_seconds,
        spread_observation_age_seconds=spread_observation_age_seconds,
        depth_confidence=depth_confidence,
        settlement_friction_rate=settlement_friction_rate,
        manual_recheck_urgency=manual_recheck_urgency,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_input_refresh_sla_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_manual_refresh_sla_review() -> None:
    module = api()
    refresh = report()

    assert module.COST_INPUT_REFRESH_SLA_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "COST_INPUT_REFRESH_SLA_STATUSES",
        "DEFAULT_RESEARCH_MARKET_COST_INPUT_REFRESH_SLA_REPORT_CONFIG_VERSION",
        "ResearchMarketCostInputRefreshSlaConfig",
        "ResearchMarketCostInputRefreshSlaInput",
        "ResearchMarketCostInputRefreshSlaReasonCodeCount",
        "ResearchMarketCostInputRefreshSlaReport",
        "ResearchMarketCostInputRefreshSlaRow",
        "build_research_market_cost_input_refresh_sla_report",
        "research_market_cost_input_refresh_sla_report_digest",
        "research_market_cost_input_refresh_sla_report_payload",
    )
    assert type(refresh) is module.ResearchMarketCostInputRefreshSlaReport
    assert is_dataclass(refresh)
    assert refresh.generated_at == GENERATED_AT
    assert refresh.config_version == "research-market-cost-input-refresh-sla-report-v0"
    assert refresh.input_count == ZERO
    assert refresh.pass_count == ZERO
    assert refresh.watch_count == ZERO
    assert refresh.block_count == ZERO
    assert refresh.average_refresh_sla_score is None
    assert refresh.max_fee_age_seconds == ZERO
    assert refresh.max_spread_observation_age_seconds == ZERO
    assert refresh.min_depth_confidence == ZERO
    assert refresh.max_settlement_friction_rate == ZERO
    assert refresh.max_manual_recheck_urgency == ZERO
    assert refresh.status == "block"
    assert refresh.reason_codes == ("no_cost_input_refresh_sla_inputs",)
    assert refresh.reason_code_counts == (
        module.ResearchMarketCostInputRefreshSlaReasonCodeCount(
            reason_code="no_cost_input_refresh_sla_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert refresh.rows == ()
    assert refresh.paper_only is True
    assert refresh.report_only is True
    assert refresh.readonly is True


def test_refresh_sla_scores_pass_watch_and_block_inputs() -> None:
    refresh = report(
        input_row("refresh-case-watch", fee_age_seconds=d("7200.000000"), spread_observation_age_seconds=d("600.000000"), depth_confidence=d("0.700000"), settlement_friction_rate=d("0.010000"), manual_recheck_urgency=d("0.500000")),
        input_row("refresh-case-block", fee_age_seconds=d("20000.000000"), spread_observation_age_seconds=d("1800.000000"), depth_confidence=d("0.400000"), settlement_friction_rate=d("0.030000"), manual_recheck_urgency=d("0.900000"), reason_codes=("manual_cost_input_recheck",)),
        input_row("refresh-case-pass"),
    )

    assert refresh.input_count == d("3.000000")
    assert refresh.pass_count == d("1.000000")
    assert refresh.watch_count == d("1.000000")
    assert refresh.block_count == d("1.000000")
    assert refresh.average_refresh_sla_score == d("0.511667")
    assert refresh.max_fee_age_seconds == d("20000.000000")
    assert refresh.max_spread_observation_age_seconds == d("1800.000000")
    assert refresh.min_depth_confidence == d("0.400000")
    assert refresh.max_settlement_friction_rate == d("0.030000")
    assert refresh.max_manual_recheck_urgency == d("0.900000")
    assert refresh.status == "block"
    assert refresh.reason_codes == (
        "cost_input_refresh_sla_block",
        "fee_freshness_block",
        "spread_observation_age_block",
        "depth_confidence_block",
        "settlement_friction_block",
        "manual_recheck_urgency_block",
        "fee_freshness_watch",
        "spread_observation_age_watch",
        "depth_confidence_watch",
        "settlement_friction_watch",
        "manual_recheck_urgency_watch",
    )

    block_row, pass_row, watch_row = refresh.rows
    assert tuple(row.research_key for row in refresh.rows) == (
        "refresh-case-block",
        "refresh-case-pass",
        "refresh-case-watch",
    )
    assert tuple(row.status for row in refresh.rows) == ("block", "pass", "watch")
    assert block_row.refresh_sla_score == d("0.100000")
    assert block_row.fee_freshness_score == ZERO
    assert block_row.spread_observation_freshness_score == ZERO
    assert block_row.reason_codes == (
        "cost_input_refresh_sla_block",
        "depth_confidence_block",
        "fee_freshness_block",
        "input_manual_cost_input_recheck",
        "manual_recheck_urgency_block",
        "manual_refresh_recheck_block",
        "settlement_friction_block",
        "spread_observation_age_block",
    )
    assert pass_row.refresh_sla_score == d("0.895000")
    assert pass_row.status == "pass"
    assert "manual_refresh_recheck_pass" in pass_row.reason_codes
    assert watch_row.refresh_sla_score == d("0.540000")
    assert watch_row.status == "watch"
    assert "fee_freshness_watch" in watch_row.reason_codes
    assert "spread_observation_age_watch" in watch_row.reason_codes
    assert "depth_confidence_watch" in watch_row.reason_codes
    assert "settlement_friction_watch" in watch_row.reason_codes
    assert "manual_recheck_urgency_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        input_row("refresh-case-z", reason_codes=("zeta", "alpha")),
        input_row("refresh-case-a"),
    )
    second = report(
        input_row("refresh-case-a"),
        input_row("refresh-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_cost_input_refresh_sla_report_payload(first)
    second_payload = module.research_market_cost_input_refresh_sla_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_cost_input_refresh_sla_report_digest(first) == (
        module.research_market_cost_input_refresh_sla_report_digest(second)
    )
    assert len(module.research_market_cost_input_refresh_sla_report_digest(first)) == 64
    assert first_payload["rows"][0]["research_key"] == "refresh-case-a"
    assert first_payload["rows"][0]["refresh_sla_score"] == "0.895000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    module = api()
    populated = report(input_row())

    for value in (config(), input_row(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_rate",
                    "_confidence",
                    "_seconds",
                    "_urgency",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].refresh_sla_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_pass_fee_age_seconds"):
        config(max_pass_fee_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_fee_age_seconds"):
        config(max_watch_fee_age_seconds=_DecimalSubclass("14400.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" raw-refresh")
    with pytest.raises(ValueError, match="fee_age_seconds"):
        input_row(fee_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_confidence"):
        input_row(depth_confidence=d("1.100000"))
    with pytest.raises(ValueError, match="manual_recheck_urgency"):
        input_row(manual_recheck_urgency=-d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="refresh_sla_score"):
        replace(populated.rows[0], refresh_sla_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="report"):
        module.research_market_cost_input_refresh_sla_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_side_effect_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_input_refresh_sla_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "condition_id",
        "execution",
        "market_id",
        "market_slug",
        "question",
        "raw_text",
        "source_reference",
        "source_text",
        "source_url",
        "token_id",
    }
