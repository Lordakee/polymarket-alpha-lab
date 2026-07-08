from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_market_microstructure_research_gate_report as api
from polymarket_alpha_lab.research_market_microstructure_research_gate_report import (
    MarketMicrostructureGateConfig,
    MarketMicrostructureInput,
    MarketMicrostructureReport,
    MarketMicrostructureRow,
    build_market_microstructure_research_gate_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    research_case_key: str = "case_a",
    spread_pct: Decimal = d("0.020000"),
    top_of_book_depth: Decimal = d("1500.000000"),
    quote_age_seconds: Decimal = d("10.000000"),
    top_liquidity_share: Decimal = d("0.400000"),
    volume_burst_ratio: Decimal = d("1.200000"),
    fee_friction_pct: Decimal = d("0.015000"),
) -> MarketMicrostructureInput:
    return MarketMicrostructureInput(
        research_case_key=research_case_key,
        observed_at=NOW,
        spread_pct=spread_pct,
        top_of_book_depth=top_of_book_depth,
        quote_age_seconds=quote_age_seconds,
        top_liquidity_share=top_liquidity_share,
        volume_burst_ratio=volume_burst_ratio,
        fee_friction_pct=fee_friction_pct,
    )


def report(
    rows: tuple[MarketMicrostructureInput, ...],
    *,
    config: MarketMicrostructureGateConfig | None = None,
) -> MarketMicrostructureReport:
    return build_market_microstructure_research_gate_report(
        rows,
        generated_at=NOW,
        config=config,
    )


def test_passes_when_all_microstructure_metrics_are_research_ready() -> None:
    built = report((observation(),))

    row = built.rows[0]
    assert built.report_status == "pass"
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert row.status == "pass"
    assert row.microstructure_readiness_score == d("0.900000")
    assert row.reason_codes == ("microstructure_research_gate_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_watch_and_block_statuses_reflect_metric_thresholds() -> None:
    built = report(
        (
            observation(research_case_key="case_pass"),
            observation(
                research_case_key="case_watch",
                spread_pct=d("0.080000"),
                top_of_book_depth=d("650.000000"),
                quote_age_seconds=d("80.000000"),
                top_liquidity_share=d("0.700000"),
                volume_burst_ratio=d("3.500000"),
                fee_friction_pct=d("0.045000"),
            ),
            observation(
                research_case_key="case_block",
                spread_pct=d("0.150000"),
                top_of_book_depth=d("200.000000"),
                quote_age_seconds=d("400.000000"),
                top_liquidity_share=d("0.920000"),
                volume_burst_ratio=d("8.500000"),
                fee_friction_pct=d("0.110000"),
            ),
        ),
    )

    rows = {row.research_case_key: row for row in built.rows}
    assert built.report_status == "block"
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert rows["case_watch"].status == "watch"
    assert "spread_watch" in rows["case_watch"].reason_codes
    assert "depth_watch" in rows["case_watch"].reason_codes
    assert "quote_staleness_watch" in rows["case_watch"].reason_codes
    assert "liquidity_concentration_watch" in rows["case_watch"].reason_codes
    assert "volume_burst_watch" in rows["case_watch"].reason_codes
    assert "fee_friction_watch" in rows["case_watch"].reason_codes
    assert rows["case_block"].status == "block"
    assert "spread_block" in rows["case_block"].reason_codes
    assert "depth_block" in rows["case_block"].reason_codes
    assert "quote_staleness_block" in rows["case_block"].reason_codes
    assert "liquidity_concentration_block" in rows["case_block"].reason_codes
    assert "volume_burst_block" in rows["case_block"].reason_codes
    assert "fee_friction_block" in rows["case_block"].reason_codes


def test_payload_is_deterministic_json_ready_and_decimal_stringed() -> None:
    first = report(
        (
            observation(research_case_key="z_case", spread_pct=d("0.030000")),
            observation(research_case_key="a_case", spread_pct=d("0.020000")),
        ),
    )
    second = report(
        (
            observation(research_case_key="a_case", spread_pct=d("0.020000")),
            observation(research_case_key="z_case", spread_pct=d("0.030000")),
        ),
    )

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == second.payload
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["case_count"] == "2.000000"
    assert payload["rows"][0]["research_case_key"] == "a_case"
    assert payload["rows"][0]["spread_pct"] == "0.020000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(first)


def test_dataclasses_are_frozen_and_digest_rejects_tampering() -> None:
    built = report((observation(),))

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest|average"):
        replace(built, average_readiness_score=d("0.100000"))


def test_hard_flags_decimal_only_and_status_contract_are_enforced() -> None:
    for cls in (
        MarketMicrostructureGateConfig,
        MarketMicrostructureInput,
        MarketMicrostructureRow,
        MarketMicrostructureReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(
                forbidden in lowered
                for forbidden in (
                    "market_id",
                    "market_slug",
                    "source_id",
                    "token_id",
                    "condition_id",
                    "wallet",
                    "auth",
                    "order",
                    "trade",
                )
            )

    assert api.STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="paper_only"):
        MarketMicrostructureGateConfig(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        observation(spread_pct=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="status"):
        replace(report((observation(),)).rows[0], status="blocked")


def test_public_surface_has_no_execution_or_raw_identifier_dependencies() -> None:
    unsafe_terms = (
        "wallet",
        "auth",
        "order",
        "trade",
        "private",
        "execution",
        "market_id",
        "market_slug",
        "source_id",
        "token_id",
        "condition_id",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
