from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from importlib import import_module
import json

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.research_market_liquidity_exit_friction_report",
    )


def _config(**overrides):
    values = {
        "config_version": "research-market-liquidity-exit-friction-report-test-v1",
        "pass_exit_friction_threshold": d("0.350000"),
        "block_exit_friction_threshold": d("0.700000"),
        "reference_bid_depth": d("100.0000"),
        "wide_spread_threshold": d("0.040000"),
        "steep_depth_decay_threshold": d("0.500000"),
        "long_settlement_window_hours": d("48.000000"),
        "high_volatility_threshold": d("0.200000"),
        "high_fee_drag_threshold": d("0.050000"),
    }
    values.update(overrides)
    return _api().ResearchMarketLiquidityExitFrictionConfig(**values)


def _snapshot(
    *,
    review_reference: str,
    bid_depth: Decimal,
    ask_depth: Decimal,
    spread: Decimal,
    depth_decay: Decimal,
    settlement_window_hours: Decimal,
    volatility: Decimal,
    fee_drag: Decimal,
    observed_at: datetime = OBSERVED_AT,
):
    return _api().ResearchMarketLiquidityExitFrictionSnapshot(
        review_reference=review_reference,
        observed_at=observed_at,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        spread=spread,
        depth_decay=depth_decay,
        settlement_window_hours=settlement_window_hours,
        volatility=volatility,
        fee_drag=fee_drag,
    )


def _report(*snapshots, **config_overrides):
    return _api().build_research_market_liquidity_exit_friction_report(
        snapshots,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _walk_json(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_json(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _walk_json(item)
        return
    yield value


def test_liquidity_exit_friction_report_scores_rows_and_sorts_by_review_risk() -> None:
    api = _api()
    high_raw_reference = (
        "candidate-alpha market-slug question text https://example.invalid token=secret"
    )
    report = _report(
        _snapshot(
            review_reference="candidate-beta",
            bid_depth=d("250.0000"),
            ask_depth=d("50.0000"),
            spread=d("0.005000"),
            depth_decay=d("0.100000"),
            settlement_window_hours=d("6.000000"),
            volatility=d("0.040000"),
            fee_drag=d("0.005000"),
        ),
        _snapshot(
            review_reference=high_raw_reference,
            bid_depth=d("20.0000"),
            ask_depth=d("180.0000"),
            spread=d("0.080000"),
            depth_decay=d("0.800000"),
            settlement_window_hours=d("96.000000"),
            volatility=d("0.350000"),
            fee_drag=d("0.070000"),
        ),
    )

    assert type(report) is api.ResearchMarketLiquidityExitFrictionReport
    assert report.source_snapshot_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.block_count == d("1")
    assert report.exit_friction_status == "block"
    assert report.highest_exit_friction_score == d("0.940000")
    assert report.reason_codes == (
        "bid_depth_block",
        "ask_depth_imbalance_watch",
        "spread_block",
        "depth_decay_block",
        "settlement_window_block",
        "volatility_block",
        "fee_drag_block",
        "score_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    high_risk, low_risk = report.rows
    assert high_risk.exit_friction_status == "block"
    assert high_risk.exit_friction_score == d("0.940000")
    assert high_risk.bid_depth_score == d("0.200000")
    assert high_risk.ask_depth_imbalance_score == d("0.090000")
    assert low_risk.exit_friction_status == "pass"
    assert low_risk.exit_friction_score == d("0.114167")
    assert high_risk.review_digest != low_risk.review_digest
    assert high_raw_reference not in (high_risk.review_digest, low_risk.review_digest)


def test_public_payload_is_json_ready_digest_bound_and_redacts_raw_market_surfaces() -> None:
    api = _api()
    raw_reference = (
        "candidate-alpha market-slug question text https://example.invalid token=secret"
    )
    report = _report(
        _snapshot(
            review_reference=raw_reference,
            bid_depth=d("20.0000"),
            ask_depth=d("180.0000"),
            spread=d("0.080000"),
            depth_decay=d("0.800000"),
            settlement_window_hours=d("96.000000"),
            volatility=d("0.350000"),
            fee_drag=d("0.070000"),
        ),
    )

    payload = api.research_market_liquidity_exit_friction_report_payload(report)
    encoded_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["highest_exit_friction_score"] == "0.940000"
    assert payload["rows"][0]["bid_depth"] == "20.0000"
    assert payload["rows"][0]["review_digest"] == report.rows[0].review_digest
    assert raw_reference not in encoded_payload
    for forbidden in (
        "candidate-alpha",
        "market-slug",
        "question text",
        "https://example.invalid",
        "token=secret",
    ):
        assert forbidden not in encoded_payload
    assert not any(isinstance(value, float) for value in _walk_json(payload))

    changed_report = _report(
        _snapshot(
            review_reference=raw_reference,
            bid_depth=d("19.0000"),
            ask_depth=d("180.0000"),
            spread=d("0.080000"),
            depth_decay=d("0.800000"),
            settlement_window_hours=d("96.000000"),
            volatility=d("0.350000"),
            fee_drag=d("0.070000"),
        ),
    )
    assert changed_report.derived_validation_digest != report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_empty_input_is_blocked_for_manual_review_without_row_leakage() -> None:
    report = _report()

    assert report.source_snapshot_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.highest_exit_friction_score == d("0.000000")
    assert report.exit_friction_status == "block"
    assert report.reason_codes == ("missing_liquidity_snapshots",)
    assert report.rows == ()


def test_validation_enforces_frozen_decimal_only_hard_flagged_contracts() -> None:
    api = _api()
    snapshot = _snapshot(
        review_reference="candidate-alpha",
        bid_depth=d("20.0000"),
        ask_depth=d("180.0000"),
        spread=d("0.080000"),
        depth_decay=d("0.800000"),
        settlement_window_hours=d("96.000000"),
        volatility=d("0.350000"),
        fee_drag=d("0.070000"),
    )
    report = _report(snapshot)

    with pytest.raises(FrozenInstanceError):
        report.exit_friction_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config_version must not contain raw identifiers"):
        _config(config_version="https://example.invalid token=secret")
    with pytest.raises(ValueError, match="bid_depth must be a Decimal"):
        _snapshot(
            review_reference="candidate-alpha",
            bid_depth=_DecimalSubclass("1.0000"),
            ask_depth=d("1.0000"),
            spread=d("0.010000"),
            depth_decay=d("0.100000"),
            settlement_window_hours=d("1.000000"),
            volatility=d("0.010000"),
            fee_drag=d("0.001000"),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _snapshot(
            review_reference="candidate-alpha",
            observed_at=datetime(2026, 7, 8, 11, 45, tzinfo=_NoneOffsetTimezone()),
            bid_depth=d("1.0000"),
            ask_depth=d("1.0000"),
            spread=d("0.010000"),
            depth_decay=d("0.100000"),
            settlement_window_hours=d("1.000000"),
            volatility=d("0.010000"),
            fee_drag=d("0.001000"),
        )

    public_dataclasses = (
        api.ResearchMarketLiquidityExitFrictionConfig,
        api.ResearchMarketLiquidityExitFrictionSnapshot,
        api.ResearchMarketLiquidityExitFrictionReportRow,
        api.ResearchMarketLiquidityExitFrictionReport,
    )
    for contract in public_dataclasses:
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (float, int) for field in fields(contract))
    assert {row.exit_friction_status for row in report.rows} <= {"pass", "watch", "block"}
    assert report.exit_friction_status in {"pass", "watch", "block"}


def test_payload_contract_excludes_raw_identifiers_and_live_execution_surfaces() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = api.__loader__.get_source(api.__name__).lower()
    report = _report(
        _snapshot(
            review_reference=(
                "candidate-alpha market-id market-slug question text "
                "https://example.invalid dsn=postgres table=markets token=secret"
            ),
            bid_depth=d("20.0000"),
            ask_depth=d("180.0000"),
            spread=d("0.080000"),
            depth_decay=d("0.800000"),
            settlement_window_hours=d("96.000000"),
            volatility=d("0.350000"),
            fee_drag=d("0.070000"),
        ),
    )
    payload = api.research_market_liquidity_exit_friction_report_payload(report)

    assert "research_market_liquidity_exit_friction_report_payload" in public_names
    assert "derived_validation_digest" in payload
    for key_or_value in _walk_json(payload):
        if isinstance(key_or_value, str):
            lowered = key_or_value.lower()
            for forbidden in (
                "candidate-alpha",
                "market-id",
                "market-slug",
                "question text",
                "https://",
                "dsn=",
                "table=markets",
                "token=secret",
                "wallet",
            ):
                assert forbidden not in lowered
    for banned in (
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "private_key",
        "wallet",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "os.environ",
        "open(",
        ".write(",
        ".read(",
        "socket",
    ):
        assert banned not in source
