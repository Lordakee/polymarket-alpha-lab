from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_drag_threshold_breach_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_DRAG_THRESHOLD_BREACH_REPORT_CONFIG_VERSION
        ),
        "max_pass_total_fee_drag_rate": d("0.020000"),
        "max_watch_total_fee_drag_rate": d("0.060000"),
        "max_pass_fee_drag_rate": d("0.010000"),
        "max_watch_fee_drag_rate": d("0.030000"),
        "max_pass_spread_drag_rate": d("0.005000"),
        "max_watch_spread_drag_rate": d("0.020000"),
        "max_pass_settlement_cost_rate": d("0.003000"),
        "max_watch_settlement_cost_rate": d("0.010000"),
        "max_pass_transfer_cost_rate": d("0.002000"),
        "max_watch_transfer_cost_rate": d("0.008000"),
        "max_pass_fee_quote_age_seconds": d("3600.000000"),
        "max_watch_fee_quote_age_seconds": d("14400.000000"),
        "max_pass_spread_quote_age_seconds": d("300.000000"),
        "max_watch_spread_quote_age_seconds": d("1200.000000"),
        "max_pass_settlement_quote_age_seconds": d("86400.000000"),
        "max_watch_settlement_quote_age_seconds": d("172800.000000"),
        "max_pass_transfer_quote_age_seconds": d("86400.000000"),
        "max_watch_transfer_quote_age_seconds": d("172800.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeDragThresholdBreachConfig(**values)


def input_row(
    research_key: str = "fee-drag-pass",
    *,
    fee_drag_rate: Decimal = d("0.005000"),
    spread_drag_rate: Decimal = d("0.004000"),
    settlement_cost_rate: Decimal = d("0.002000"),
    transfer_cost_rate: Decimal = d("0.001000"),
    fee_quote_age_seconds: Decimal = d("1800.000000"),
    spread_quote_age_seconds: Decimal = d("120.000000"),
    settlement_quote_age_seconds: Decimal = d("43200.000000"),
    transfer_quote_age_seconds: Decimal = d("43200.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketFeeDragThresholdBreachInput(
        research_key=research_key,
        fee_drag_rate=fee_drag_rate,
        spread_drag_rate=spread_drag_rate,
        settlement_cost_rate=settlement_cost_rate,
        transfer_cost_rate=transfer_cost_rate,
        fee_quote_age_seconds=fee_quote_age_seconds,
        spread_quote_age_seconds=spread_quote_age_seconds,
        settlement_quote_age_seconds=settlement_quote_age_seconds,
        transfer_quote_age_seconds=transfer_quote_age_seconds,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_fee_drag_threshold_breach_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_fee_drag_review() -> None:
    module = api()
    fee_report = report()

    assert module.FEE_DRAG_THRESHOLD_BREACH_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "FEE_DRAG_THRESHOLD_BREACH_STATUSES",
        "DEFAULT_RESEARCH_MARKET_FEE_DRAG_THRESHOLD_BREACH_REPORT_CONFIG_VERSION",
        "ResearchMarketFeeDragThresholdBreachConfig",
        "ResearchMarketFeeDragThresholdBreachInput",
        "ResearchMarketFeeDragThresholdBreachReasonCodeCount",
        "ResearchMarketFeeDragThresholdBreachReport",
        "ResearchMarketFeeDragThresholdBreachRow",
        "build_research_market_fee_drag_threshold_breach_report",
        "research_market_fee_drag_threshold_breach_report_digest",
        "research_market_fee_drag_threshold_breach_report_payload",
        "validate_research_market_fee_drag_threshold_breach_report_payload",
    )
    assert type(fee_report) is module.ResearchMarketFeeDragThresholdBreachReport
    assert is_dataclass(fee_report)
    assert fee_report.generated_at == GENERATED_AT
    assert fee_report.config_version == (
        "research-market-fee-drag-threshold-breach-report-v0"
    )
    assert fee_report.input_count == ZERO
    assert fee_report.pass_count == ZERO
    assert fee_report.watch_count == ZERO
    assert fee_report.block_count == ZERO
    assert fee_report.average_fee_drag_pressure_score is None
    assert fee_report.max_total_fee_drag_rate == ZERO
    assert fee_report.max_fee_drag_rate == ZERO
    assert fee_report.max_spread_drag_rate == ZERO
    assert fee_report.max_settlement_cost_rate == ZERO
    assert fee_report.max_transfer_cost_rate == ZERO
    assert fee_report.max_fee_quote_age_seconds == ZERO
    assert fee_report.max_spread_quote_age_seconds == ZERO
    assert fee_report.max_settlement_quote_age_seconds == ZERO
    assert fee_report.max_transfer_quote_age_seconds == ZERO
    assert fee_report.status == "block"
    assert fee_report.reason_codes == ("no_fee_drag_threshold_breach_inputs",)
    assert fee_report.reason_code_counts == (
        module.ResearchMarketFeeDragThresholdBreachReasonCodeCount(
            reason_code="no_fee_drag_threshold_breach_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert fee_report.rows == ()
    assert fee_report.paper_only is True
    assert fee_report.report_only is True
    assert fee_report.readonly is True


def test_fee_drag_breaches_rank_pass_watch_and_block_rows() -> None:
    fee_report = report(
        input_row(
            "fee-drag-watch",
            fee_drag_rate=d("0.020000"),
            spread_drag_rate=d("0.010000"),
            settlement_cost_rate=d("0.006000"),
            transfer_cost_rate=d("0.005000"),
            fee_quote_age_seconds=d("7200.000000"),
            spread_quote_age_seconds=d("600.000000"),
            settlement_quote_age_seconds=d("100000.000000"),
            transfer_quote_age_seconds=d("100000.000000"),
        ),
        input_row(
            "fee-drag-block",
            fee_drag_rate=d("0.040000"),
            spread_drag_rate=d("0.030000"),
            settlement_cost_rate=d("0.020000"),
            transfer_cost_rate=d("0.012000"),
            fee_quote_age_seconds=d("20000.000000"),
            spread_quote_age_seconds=d("1800.000000"),
            settlement_quote_age_seconds=d("200000.000000"),
            transfer_quote_age_seconds=d("200000.000000"),
            reason_codes=("analyst_cost_refresh",),
        ),
        input_row("fee-drag-pass"),
    )

    assert fee_report.input_count == d("3.000000")
    assert fee_report.pass_count == d("1.000000")
    assert fee_report.watch_count == d("1.000000")
    assert fee_report.block_count == d("1.000000")
    assert fee_report.average_fee_drag_pressure_score == d("0.581906")
    assert fee_report.max_total_fee_drag_rate == d("0.102000")
    assert fee_report.max_fee_drag_rate == d("0.040000")
    assert fee_report.max_spread_drag_rate == d("0.030000")
    assert fee_report.max_settlement_cost_rate == d("0.020000")
    assert fee_report.max_transfer_cost_rate == d("0.012000")
    assert fee_report.max_fee_quote_age_seconds == d("20000.000000")
    assert fee_report.max_spread_quote_age_seconds == d("1800.000000")
    assert fee_report.max_settlement_quote_age_seconds == d("200000.000000")
    assert fee_report.max_transfer_quote_age_seconds == d("200000.000000")
    assert fee_report.status == "block"
    assert fee_report.reason_codes == (
        "fee_drag_threshold_breach_block",
        "total_fee_drag_block",
        "fee_component_drag_block",
        "spread_component_drag_block",
        "settlement_cost_block",
        "transfer_cost_block",
        "fee_cost_freshness_block",
        "spread_cost_freshness_block",
        "settlement_cost_freshness_block",
        "transfer_cost_freshness_block",
        "total_fee_drag_watch",
        "fee_component_drag_watch",
        "spread_component_drag_watch",
        "settlement_cost_watch",
        "transfer_cost_watch",
        "fee_cost_freshness_watch",
        "spread_cost_freshness_watch",
        "settlement_cost_freshness_watch",
        "transfer_cost_freshness_watch",
    )

    block_row, pass_row, watch_row = fee_report.rows
    assert tuple(row.research_key for row in fee_report.rows) == (
        "fee-drag-block",
        "fee-drag-pass",
        "fee-drag-watch",
    )
    assert tuple(row.status for row in fee_report.rows) == ("block", "pass", "watch")
    assert block_row.total_fee_drag_rate == d("0.102000")
    assert block_row.fee_drag_pressure_score == d("1.000000")
    assert block_row.reason_codes == (
        "fee_component_drag_block",
        "fee_cost_freshness_block",
        "fee_drag_threshold_breach_block",
        "input_analyst_cost_refresh",
        "settlement_cost_block",
        "settlement_cost_freshness_block",
        "spread_component_drag_block",
        "spread_cost_freshness_block",
        "total_fee_drag_block",
        "transfer_cost_block",
        "transfer_cost_freshness_block",
    )
    assert pass_row.fee_drag_pressure_score == d("0.177083")
    assert pass_row.status == "pass"
    assert "fee_drag_threshold_breach_pass" in pass_row.reason_codes
    assert watch_row.total_fee_drag_rate == d("0.041000")
    assert watch_row.fee_drag_pressure_score == d("0.568634")
    assert watch_row.status == "watch"
    assert "total_fee_drag_watch" in watch_row.reason_codes
    assert "settlement_cost_freshness_watch" in watch_row.reason_codes


def test_payload_digest_validation_is_deterministic_and_public_safe() -> None:
    module = api()
    first = report(
        input_row("fee-drag-z", reason_codes=("zeta", "alpha")),
        input_row("fee-drag-a"),
    )
    second = report(
        input_row("fee-drag-a"),
        input_row("fee-drag-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_fee_drag_threshold_breach_report_payload(
        first,
    )
    second_payload = module.research_market_fee_drag_threshold_breach_report_payload(
        second,
    )
    digest = module.research_market_fee_drag_threshold_breach_report_digest(first)
    encoded = json.dumps(first_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert digest == module.research_market_fee_drag_threshold_breach_report_digest(
        second,
    )
    assert digest == sha256(encoded.encode("utf-8")).hexdigest()
    assert len(digest) == 64
    assert module.validate_research_market_fee_drag_threshold_breach_report_payload(
        first_payload,
        expected_digest=digest,
    ) == first_payload
    assert first_payload["rows"][0]["research_key"] == "fee-drag-a"
    assert first_payload["rows"][0]["fee_drag_pressure_score"] == "0.177083"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ":0." not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )

    with pytest.raises(ValueError, match="payload digest mismatch"):
        module.validate_research_market_fee_drag_threshold_breach_report_payload(
            {**first_payload, "status": "watch"},
            expected_digest=digest,
        )
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_fee_drag_threshold_breach_report_payload(
            {**first_payload, "status": "blocked"},
        )
    with pytest.raises(ValueError, match="unsafe public payload key"):
        module.validate_research_market_fee_drag_threshold_breach_report_payload(
            {**first_payload, "market_slug": "leaked"},
        )
    with pytest.raises(ValueError, match="unsafe public payload value"):
        leaked = {**first_payload, "rows": [{**first_payload["rows"][0]}]}
        leaked["rows"][0]["research_key"] = "wallet-leak"
        module.validate_research_market_fee_drag_threshold_breach_report_payload(leaked)


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
            if item.name.endswith(("_count", "_score", "_rate", "_seconds", "_ratio")):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].fee_drag_pressure_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_pass_total_fee_drag_rate"):
        config(max_pass_total_fee_drag_rate=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_fee_drag_rate"):
        config(max_watch_fee_drag_rate=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" raw-fee-drag")
    with pytest.raises(ValueError, match="fee_drag_rate"):
        input_row(fee_drag_rate=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_drag_rate"):
        input_row(spread_drag_rate=d("1.100000"))
    with pytest.raises(ValueError, match="transfer_quote_age_seconds"):
        input_row(transfer_quote_age_seconds=-d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="fee_drag_pressure_score"):
        replace(populated.rows[0], fee_drag_pressure_score=d("0.900000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_drag_threshold_breach_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_side_effect_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_drag_threshold_breach_report.py"
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
        joined("data", "base"),
        joined("net", "work"),
        joined("wal", "let"),
        joined("au", "th"),
        joined("or", "der"),
        joined("tra", "de"),
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
        "candidate_id",
        "condition_id",
        "dsn",
        "execution",
        "market_id",
        "market_slug",
        "question",
        "raw_text",
        "source_reference",
        "source_text",
        "source_url",
        "table_name",
        "token_id",
    }


def joined(*parts: str) -> str:
    return "".join(parts)
