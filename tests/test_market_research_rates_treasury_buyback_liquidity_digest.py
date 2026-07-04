from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def digest() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_rates_treasury_buyback_liquidity_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = digest()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_accepted_amount_billion": d("5.000000"),
        "max_accepted_gap_billion": d("5.000000"),
        "watch_offer_to_accept_ratio": d("2.500000"),
        "blocked_offer_to_accept_ratio": d("4.000000"),
        "watch_price_concession_bp": d("3.000000"),
        "blocked_price_concession_bp": d("8.000000"),
        "watch_liquidity_stress_score": d("0.450000"),
        "blocked_liquidity_stress_score": d("0.750000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_reason": d("0.050000"),
        "watch_confidence_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.MarketResearchRatesTreasuryBuybackLiquidityDigestConfig(**values)


def buyback_signal(
    condition_id: str = "condition.alpha",
    *,
    operation_window_key: str = "treasury.buyback.weekly",
    tenor_bucket: str = "coupon-7-to-20-year",
    public_signal_reference: str = "treasury-buyback-public-result",
    observed_at: datetime | None = None,
    signal_age_seconds: Decimal = d("900.000000"),
    accepted_amount_billion: Decimal = d("15.000000"),
    offered_amount_billion: Decimal = d("25.000000"),
    scheduled_amount_billion: Decimal = d("14.000000"),
    offer_to_accept_ratio: Decimal = d("1.666667"),
    average_price_concession_bp: Decimal = d("1.500000"),
    liquidity_stress_score: Decimal = d("0.200000"),
    source_family_count: Decimal = d("4.000000"),
    stale_source_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.820000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "rates-treasury-buyback-liquidity-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = digest()
    return module.MarketResearchRatesTreasuryBuybackLiquidityDigestSignal(
        condition_id=condition_id,
        operation_window_key=operation_window_key,
        tenor_bucket=tenor_bucket,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        signal_age_seconds=signal_age_seconds,
        accepted_amount_billion=accepted_amount_billion,
        offered_amount_billion=offered_amount_billion,
        scheduled_amount_billion=scheduled_amount_billion,
        offer_to_accept_ratio=offer_to_accept_ratio,
        average_price_concession_bp=average_price_concession_bp,
        liquidity_stress_score=liquidity_stress_score,
        source_family_count=source_family_count,
        stale_source_ratio=stale_source_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = digest()
    return module.build_market_research_rates_treasury_buyback_liquidity_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_buyback_liquidity_digest_reduces_signals_with_blocked_watch_pass_thresholds() -> None:
    module = digest()

    summary = report(
        (
            buyback_signal(
                "condition.watch",
                operation_window_key="treasury.buyback.watch",
                tenor_bucket="coupon-2-to-7-year",
                accepted_amount_billion=d("8.000000"),
                offered_amount_billion=d("24.000000"),
                scheduled_amount_billion=d("12.000000"),
                offer_to_accept_ratio=d("3.000000"),
                average_price_concession_bp=d("5.000000"),
                liquidity_stress_score=d("0.520000"),
                confirmation_ratio=d("0.600000"),
                base_confidence=d("0.780000"),
            ),
            buyback_signal(
                "condition.pass",
                operation_window_key="treasury.buyback.pass",
                tenor_bucket="coupon-20-to-30-year",
                public_signal_reference="treasury-buyback-pass-reference",
                observed_at=GENERATED_AT - timedelta(minutes=10),
                signal_age_seconds=d("600.000000"),
                accepted_amount_billion=d("15.000000"),
                offered_amount_billion=d("25.000000"),
                scheduled_amount_billion=d("14.000000"),
                offer_to_accept_ratio=d("1.666667"),
                average_price_concession_bp=d("1.500000"),
                liquidity_stress_score=d("0.200000"),
            ),
            buyback_signal(
                "condition.blocked",
                operation_window_key="treasury.buyback.blocked",
                tenor_bucket="coupon-off-the-run",
                public_signal_reference=("cred" "ential-buyback-snapshot"),
                observed_at=GENERATED_AT - timedelta(hours=3),
                signal_age_seconds=d("10800.000000"),
                accepted_amount_billion=d("3.000000"),
                offered_amount_billion=d("18.000000"),
                scheduled_amount_billion=d("12.000000"),
                offer_to_accept_ratio=d("6.000000"),
                average_price_concession_bp=d("12.000000"),
                liquidity_stress_score=d("0.850000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.450000"),
                base_confidence=d("0.920000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(
        summary,
        module.MarketResearchRatesTreasuryBuybackLiquidityDigestReport,
    )
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_treasury_buyback_liquidity_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.pass_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.low_accepted_amount_signal_count == d("1.000000")
    assert summary.accepted_gap_signal_count == d("1.000000")
    assert summary.blocked_offer_pressure_signal_count == d("1.000000")
    assert summary.watch_offer_pressure_signal_count == d("1.000000")
    assert summary.blocked_price_concession_signal_count == d("1.000000")
    assert summary.watch_price_concession_signal_count == d("1.000000")
    assert summary.blocked_liquidity_stress_signal_count == d("1.000000")
    assert summary.watch_liquidity_stress_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.650000")
    assert summary.average_final_confidence == d("0.636667")
    assert summary.average_accepted_gap_billion == d("4.666667")
    assert summary.average_unaccepted_offer_billion == d("13.666667")
    assert summary.average_liquidity_stress_score == d("0.523333")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.operation_window_key for row in summary.rows) == (
        "treasury.buyback.blocked",
        "treasury.buyback.watch",
        "treasury.buyback.pass",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.accepted_gap_billion == d("9.000000")
    assert blocked.unaccepted_offer_billion == d("15.000000")
    assert blocked.confidence_decay_factor == d("0.450000")
    assert blocked.final_confidence == d("0.470000")
    assert blocked.redacted_public_signal_reference == redacted(
        "cred" "ential-buyback-snapshot",
    )
    assert blocked.reason_codes == (
        "market_research_rates_treasury_buyback_liquidity_digest_stale_signal",
        "market_research_rates_treasury_buyback_liquidity_digest_low_accepted_amount",
        "market_research_rates_treasury_buyback_liquidity_digest_accepted_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_price_concession_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_source_family_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_stale_source_ratio",
        "market_research_rates_treasury_buyback_liquidity_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.accepted_gap_billion == d("4.000000")
    assert watch.unaccepted_offer_billion == d("16.000000")
    assert watch.confidence_decay_factor == d("0.200000")
    assert watch.final_confidence == d("0.580000")
    assert watch.reason_codes == (
        "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_price_concession_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_confirmation_gap",
    )

    passed = summary.rows[2]
    assert passed.digest_status == "pass"
    assert passed.accepted_gap_billion == d("1.000000")
    assert passed.unaccepted_offer_billion == d("10.000000")
    assert passed.final_confidence == d("0.860000")
    assert passed.reason_codes == (
        "market_research_rates_treasury_buyback_liquidity_digest_pass",
    )

    assert summary.reason_codes == (
        "market_research_rates_treasury_buyback_liquidity_digest_stale_signal",
        "market_research_rates_treasury_buyback_liquidity_digest_low_accepted_amount",
        "market_research_rates_treasury_buyback_liquidity_digest_accepted_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_price_concession_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_source_family_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_stale_source_ratio",
        "market_research_rates_treasury_buyback_liquidity_digest_confirmation_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_price_concession_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_watch",
    )
    assert tuple(item.reason_code for item in summary.reason_code_counts) == (
        "market_research_rates_treasury_buyback_liquidity_digest_stale_signal",
        "market_research_rates_treasury_buyback_liquidity_digest_low_accepted_amount",
        "market_research_rates_treasury_buyback_liquidity_digest_accepted_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_price_concession_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_blocked",
        "market_research_rates_treasury_buyback_liquidity_digest_source_family_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_stale_source_ratio",
        "market_research_rates_treasury_buyback_liquidity_digest_confirmation_gap",
        "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_price_concession_watch",
        "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_watch",
    )
    assert summary.reason_code_counts[2].count == d("1.000000")
    assert summary.reason_code_counts[2].signal_ratio == d("0.333333")
    assert summary.reason_code_counts[8].count == d("2.000000")
    assert summary.reason_code_counts[8].signal_ratio == d("0.666667")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in summary.rows)


def test_empty_inputs_block_with_decimal_zeroes_and_no_rows() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_treasury_buyback_liquidity_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.pass_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.total_confidence_decay == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_accepted_gap_billion == ZERO
    assert summary.average_unaccepted_offer_billion == ZERO
    assert summary.average_liquidity_stress_score == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == ()
    assert summary.reason_codes == (
        "market_research_rates_treasury_buyback_liquidity_digest_no_inputs",
    )


def test_payload_uses_utc_datetimes_decimal_strings_and_report_only_flags() -> None:
    module = digest()
    summary = report(
        (
            buyback_signal(
                "condition.payload",
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    9,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                signal_age_seconds=d("900.000000"),
                public_signal_reference=("cred" "ential-buyback-snapshot"),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            4,
            10,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    payload = module.market_research_rates_treasury_buyback_liquidity_digest_payload(
        summary,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T14:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["min_accepted_amount_billion"] == "5.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T13:45:00+00:00"
    assert payload["rows"][0]["accepted_amount_billion"] == "15.000000"
    assert payload["rows"][0]["offer_to_accept_ratio"] == "1.666667"
    assert payload["rows"][0]["redacted_public_signal_reference"] == redacted(
        "cred" "ential-buyback-snapshot",
    )
    assert payload["reason_code_counts"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in walk_payload_values(payload)
    )


def test_rejects_bad_types_duplicates_future_inputs_and_stale_age_mismatch() -> None:
    module = digest()

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                module.DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DateTimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 4, 14, 0))
    with pytest.raises(ValueError, match="signals"):
        report((object(),))
    with pytest.raises(ValueError, match="accepted_amount_billion"):
        buyback_signal(accepted_amount_billion=5.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_stress_score"):
        buyback_signal(liquidity_stress_score=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="observed_at"):
        buyback_signal(observed_at=datetime(2026, 7, 4, 14, 0))
    with pytest.raises(ValueError, match="signal_age_seconds"):
        report(
            (
                buyback_signal(
                    observed_at=GENERATED_AT - timedelta(minutes=15),
                    signal_age_seconds=d("600.000000"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="offer_to_accept_ratio"):
        report((buyback_signal(offer_to_accept_ratio=d("9.000000")),))
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                buyback_signal("condition.alpha"),
                buyback_signal("condition.beta"),
            ),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(
            (
                buyback_signal(
                    "condition.future",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                    signal_age_seconds=d("0.000000"),
                ),
            ),
        )


def test_public_dataclasses_are_frozen_and_expose_decimal_only_numerics() -> None:
    module = digest()
    summary = report((buyback_signal(),))
    row = summary.rows[0]
    reason_count = module.MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount(
        reason_code=(
            "market_research_rates_treasury_buyback_liquidity_digest_accepted_gap"
        ),
        count=d("1.000000"),
        signal_ratio=d("1.000000"),
    )

    public_classes = (
        module.MarketResearchRatesTreasuryBuybackLiquidityDigestConfig,
        module.MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount,
        module.MarketResearchRatesTreasuryBuybackLiquidityDigestReport,
        module.MarketResearchRatesTreasuryBuybackLiquidityDigestRow,
        module.MarketResearchRatesTreasuryBuybackLiquidityDigestSignal,
    )
    for public_class in public_classes:
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        row.paper_only = False

    numeric_suffixes = (
        "_billion",
        "_bp",
        "_count",
        "_ratio",
        "_score",
        "_seconds",
        "_confidence",
        "_decay",
        "_threshold",
        "_factor",
    )
    for value in (config(), buyback_signal(), summary, row, reason_count):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(numeric_suffixes):
                public_value = getattr(value, field.name)
                assert public_value is None or type(public_value) is Decimal


def test_hard_flags_are_enforced_on_config_signals_rows_and_report() -> None:
    summary = report((buyback_signal(),))

    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="signal report_only must be True"):
        buyback_signal(report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(summary, paper_only=False)


def test_module_scope_has_no_io_external_connection_or_execution_surface() -> None:
    module = digest()
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION",
        "MarketResearchRatesTreasuryBuybackLiquidityDigestConfig",
        "MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount",
        "MarketResearchRatesTreasuryBuybackLiquidityDigestReport",
        "MarketResearchRatesTreasuryBuybackLiquidityDigestRow",
        "MarketResearchRatesTreasuryBuybackLiquidityDigestSignal",
        "build_market_research_rates_treasury_buyback_liquidity_digest",
        "market_research_rates_treasury_buyback_liquidity_digest_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_name_fragments = (
        "auth",
        "cancel",
        "exchange",
        "order",
        "trade",
        "wallet",
    )
    forbidden_source_fragments = (
        "api_key",
        "cancel_order",
        "connect(",
        "execute(",
        "exchange",
        "httpx",
        "live trading",
        "open(",
        "private_key",
        "psycopg",
        "replace_order",
        "requests",
        "secret",
        "socket",
        "submit_order",
        "subprocess",
        "supabase",
        "token",
        "urllib",
        "wallet",
    )

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_name_fragments)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open"

    lowered_source = source.lower()
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source


def redacted(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for item_key, item in value.items():
            items.append(item_key)
            items.extend(walk_payload_values(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(walk_payload_values(item))
        return tuple(items)
    return (value,)
