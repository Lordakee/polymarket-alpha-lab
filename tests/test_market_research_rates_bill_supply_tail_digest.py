from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_rates_bill_supply_tail_digest"
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DateSubclass(date):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def digest_module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> object:
    module = digest_module()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_RATES_BILL_SUPPLY_TAIL_DIGEST_CONFIG_VERSION
        ),
        "max_source_age_seconds": d("7200.000000"),
        "min_announced_supply_surprise_billion": d("10.000000"),
        "min_tail_bps": d("1.500000"),
        "max_bid_to_cover_delta": d("-0.050000"),
        "max_indirect_takedown_delta": d("-0.020000"),
        "min_direct_takedown_delta": d("0.020000"),
        "min_tga_paydown_pressure_billion": d("20.000000"),
        "min_repo_specialness_proxy_bps": d("5.000000"),
        "min_upstream_reason_code_count": d("2.000000"),
        "risk_penalty_per_gap": d("0.100000"),
        "blocked_risk_threshold": d("0.500000"),
        "watch_risk_threshold": d("0.650000"),
        "pass_risk_threshold": d("0.800000"),
    }
    values.update(overrides)
    return module.MarketResearchRatesBillSupplyTailDigestConfig(**values)


def tail_signal(
    condition_id: str = "condition.alpha",
    *,
    market_slug: str = "fed-rates-july-2026",
    tenor: str = "13w",
    auction_date: date = date(2026, 7, 6),
    source_timestamp: datetime | None = None,
    announced_supply_surprise_billion: Decimal = d("18.000000"),
    tail_bps: Decimal = d("2.200000"),
    bid_to_cover_delta: Decimal = d("-0.080000"),
    indirect_takedown_delta: Decimal = d("-0.030000"),
    direct_takedown_delta: Decimal = d("0.030000"),
    tga_paydown_pressure_billion: Decimal = d("35.000000"),
    repo_specialness_proxy_bps: Decimal = d("8.000000"),
    base_risk_score: Decimal = d("0.880000"),
    upstream_reason_codes: tuple[str, ...] = (
        "auction_tail_pressure",
        "bill_supply_surprise",
    ),
    signal_config_version: str = "rates-bill-supply-tail-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> object:
    module = digest_module()
    return module.MarketResearchRatesBillSupplyTailDigestSignal(
        condition_id=condition_id,
        market_slug=market_slug,
        tenor=tenor,
        auction_date=auction_date,
        source_timestamp=source_timestamp or GENERATED_AT - timedelta(minutes=15),
        announced_supply_surprise_billion=announced_supply_surprise_billion,
        tail_bps=tail_bps,
        bid_to_cover_delta=bid_to_cover_delta,
        indirect_takedown_delta=indirect_takedown_delta,
        direct_takedown_delta=direct_takedown_delta,
        tga_paydown_pressure_billion=tga_paydown_pressure_billion,
        repo_specialness_proxy_bps=repo_specialness_proxy_bps,
        base_risk_score=base_risk_score,
        upstream_reason_codes=upstream_reason_codes,
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
) -> object:
    module = digest_module()
    return module.build_market_research_rates_bill_supply_tail_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_rates_bill_supply_tail_digest_reduces_signals_deterministically() -> None:
    module = digest_module()

    summary = report(
        (
            tail_signal(
                "condition.watch",
                market_slug="fed-rates-august-2026",
                tenor="26w",
                announced_supply_surprise_billion=d("14.000000"),
                tail_bps=d("1.800000"),
                bid_to_cover_delta=d("-0.060000"),
                indirect_takedown_delta=d("-0.025000"),
                direct_takedown_delta=d("0.025000"),
                tga_paydown_pressure_billion=d("25.000000"),
                repo_specialness_proxy_bps=d("2.000000"),
                base_risk_score=d("0.780000"),
                upstream_reason_codes=(
                    "front_end_cash_pressure",
                    "repo_specialness_gap",
                ),
            ),
            tail_signal(
                "condition.pass",
                market_slug="fed-rates-july-2026",
                tenor="13w",
                source_timestamp=GENERATED_AT - timedelta(minutes=10),
                announced_supply_surprise_billion=d("18.000000"),
                tail_bps=d("2.200000"),
                bid_to_cover_delta=d("-0.080000"),
                indirect_takedown_delta=d("-0.030000"),
                direct_takedown_delta=d("0.030000"),
                tga_paydown_pressure_billion=d("35.000000"),
                repo_specialness_proxy_bps=d("8.000000"),
                base_risk_score=d("0.880000"),
                upstream_reason_codes=(
                    "auction_tail_pressure",
                    "bill_supply_surprise",
                ),
            ),
            tail_signal(
                "condition.blocked",
                market_slug="fed-rates-september-2026",
                tenor="4w",
                source_timestamp=GENERATED_AT - timedelta(hours=3),
                announced_supply_surprise_billion=d("3.000000"),
                tail_bps=d("0.600000"),
                bid_to_cover_delta=d("-0.010000"),
                indirect_takedown_delta=d("-0.005000"),
                direct_takedown_delta=d("0.005000"),
                tga_paydown_pressure_billion=d("8.000000"),
                repo_specialness_proxy_bps=d("1.000000"),
                base_risk_score=d("0.950000"),
                upstream_reason_codes=("source:calendar",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(summary, module.MarketResearchRatesBillSupplyTailDigestReport)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_RATES_BILL_SUPPLY_TAIL_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_bill_supply_tail_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.pass_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.low_supply_surprise_signal_count == d("1.000000")
    assert summary.low_tail_signal_count == d("1.000000")
    assert summary.bid_to_cover_gap_signal_count == d("1.000000")
    assert summary.takedown_shift_gap_signal_count == d("1.000000")
    assert summary.tga_paydown_gap_signal_count == d("1.000000")
    assert summary.repo_specialness_gap_signal_count == d("2.000000")
    assert summary.upstream_reason_gap_signal_count == d("1.000000")
    assert summary.total_gap_penalty_score == d("0.900000")
    assert summary.average_final_risk_score == d("0.570000")
    assert summary.max_final_risk_score == d("0.880000")
    assert summary.risk_score == d("0.880000")
    assert summary.average_announced_supply_surprise_billion == d("11.666667")
    assert summary.average_tail_bps == d("1.533333")
    assert summary.average_bid_to_cover_delta == d("-0.050000")
    assert summary.average_indirect_takedown_delta == d("-0.020000")
    assert summary.average_direct_takedown_delta == d("0.020000")
    assert summary.average_tga_paydown_pressure_billion == d("22.666667")
    assert summary.average_repo_specialness_proxy_bps == d("3.666667")
    assert summary.max_observed_source_age_seconds == d("10800.000000")
    assert summary.upstream_reason_codes == (
        "auction_tail_pressure",
        "bill_supply_surprise",
        "front_end_cash_pressure",
        "repo_specialness_gap",
        "source:calendar",
    )
    assert tuple(row.market_slug for row in summary.rows) == (
        "fed-rates-september-2026",
        "fed-rates-august-2026",
        "fed-rates-july-2026",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.source_age_seconds == d("10800.000000")
    assert blocked.gap_penalty_score == d("0.800000")
    assert blocked.final_risk_score == d("0.150000")
    assert blocked.upstream_reason_codes == ("source:calendar",)
    assert blocked.reason_codes == (
        "market_research_rates_bill_supply_tail_digest_stale_source",
        "market_research_rates_bill_supply_tail_digest_low_supply_surprise",
        "market_research_rates_bill_supply_tail_digest_low_tail",
        "market_research_rates_bill_supply_tail_digest_bid_to_cover_gap",
        "market_research_rates_bill_supply_tail_digest_takedown_shift_gap",
        "market_research_rates_bill_supply_tail_digest_tga_paydown_gap",
        "market_research_rates_bill_supply_tail_digest_repo_specialness_gap",
        "market_research_rates_bill_supply_tail_digest_upstream_reason_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.gap_penalty_score == d("0.100000")
    assert watch.final_risk_score == d("0.680000")
    assert watch.upstream_reason_codes == (
        "front_end_cash_pressure",
        "repo_specialness_gap",
    )
    assert watch.reason_codes == (
        "market_research_rates_bill_supply_tail_digest_repo_specialness_gap",
    )

    passed = summary.rows[2]
    assert passed.digest_status == "pass"
    assert passed.final_risk_score == d("0.880000")
    assert passed.reason_codes == (
        "market_research_rates_bill_supply_tail_digest_pass",
    )

    assert summary.reason_codes == (
        "market_research_rates_bill_supply_tail_digest_stale_source",
        "market_research_rates_bill_supply_tail_digest_low_supply_surprise",
        "market_research_rates_bill_supply_tail_digest_low_tail",
        "market_research_rates_bill_supply_tail_digest_bid_to_cover_gap",
        "market_research_rates_bill_supply_tail_digest_takedown_shift_gap",
        "market_research_rates_bill_supply_tail_digest_tga_paydown_gap",
        "market_research_rates_bill_supply_tail_digest_repo_specialness_gap",
        "market_research_rates_bill_supply_tail_digest_upstream_reason_gap",
    )
    assert summary.reason_code_counts == (
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_stale_source",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_low_supply_surprise",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_low_tail",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_bid_to_cover_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_takedown_shift_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_tga_paydown_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_repo_specialness_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code="market_research_rates_bill_supply_tail_digest_upstream_reason_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    serialized = repr(asdict(summary)).lower()
    for token in ("buy", "sell", "trade", "wallet", "order", "position", "auth"):
        assert token not in serialized


def test_empty_inputs_block_with_decimal_zeroes_and_no_rows() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_bill_supply_tail_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.pass_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.stale_source_signal_count == ZERO
    assert summary.low_supply_surprise_signal_count == ZERO
    assert summary.low_tail_signal_count == ZERO
    assert summary.bid_to_cover_gap_signal_count == ZERO
    assert summary.takedown_shift_gap_signal_count == ZERO
    assert summary.tga_paydown_gap_signal_count == ZERO
    assert summary.repo_specialness_gap_signal_count == ZERO
    assert summary.upstream_reason_gap_signal_count == ZERO
    assert summary.total_gap_penalty_score == ZERO
    assert summary.average_final_risk_score == ZERO
    assert summary.max_final_risk_score == ZERO
    assert summary.risk_score == ZERO
    assert summary.average_announced_supply_surprise_billion == ZERO
    assert summary.average_tail_bps == ZERO
    assert summary.average_bid_to_cover_delta == ZERO
    assert summary.average_indirect_takedown_delta == ZERO
    assert summary.average_direct_takedown_delta == ZERO
    assert summary.average_tga_paydown_pressure_billion == ZERO
    assert summary.average_repo_specialness_proxy_bps == ZERO
    assert summary.max_observed_source_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.upstream_reason_codes == ()
    assert summary.reason_code_counts == ()
    assert summary.reason_codes == (
        "market_research_rates_bill_supply_tail_digest_no_inputs",
    )


def test_all_public_numeric_fields_are_decimal_or_none() -> None:
    summary = report((tail_signal(),))

    numeric_names = {
        field.name
        for value in (summary, *summary.rows, *summary.reason_code_counts)
        for field in fields(value)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_score")
            or field.name.endswith("_threshold")
            or field.name.endswith("_billion")
            or field.name.endswith("_bps")
            or field.name.endswith("_delta")
        )
    }
    assert numeric_names
    for value in (summary, *summary.rows, *summary.reason_code_counts):
        for field in fields(value):
            if field.name in numeric_names:
                public_value = getattr(value, field.name)
                assert public_value is None or type(public_value) is Decimal


def test_rejects_bad_types_inconsistent_inputs_and_false_hard_flags() -> None:
    module = digest_module()

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                module.DEFAULT_MARKET_RESEARCH_RATES_BILL_SUPPLY_TAIL_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="signals"):
        report((object(),))
    with pytest.raises(ValueError, match="tail_bps"):
        tail_signal(tail_bps=_DecimalSubclass("1.0"))
    with pytest.raises(ValueError, match="auction_date"):
        tail_signal(auction_date=_DateSubclass(2026, 7, 6))
    with pytest.raises(ValueError, match="source_timestamp"):
        tail_signal(source_timestamp=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="source_timestamp"):
        report((tail_signal(source_timestamp=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(tail_signal(), paper_only=False)
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        tail_signal(upstream_reason_codes=("b", "a"))

    summary = report((tail_signal(),))
    assert summary.digest_status == "pass"
    with pytest.raises(ValueError, match="pass_signal_count"):
        replace(summary, pass_signal_count=ZERO)
    with pytest.raises(ValueError, match="digest_status"):
        replace(summary, digest_status="blocked")
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=(replace(summary.rows[0], digest_status="watch"), summary.rows[0]))


def test_payload_serializes_decimal_datetime_and_date_to_strings() -> None:
    module = digest_module()
    summary = report((tail_signal(),))

    payload = module.market_research_rates_bill_supply_tail_digest_payload(summary)

    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["risk_score"] == "0.880000"
    assert payload["rows"][0]["auction_date"] == "2026-07-06"
    assert payload["rows"][0]["source_timestamp"] == (
        GENERATED_AT - timedelta(minutes=15)
    ).isoformat()
    assert payload["rows"][0]["announced_supply_surprise_billion"] == "18.000000"
    assert payload["rows"][0]["tail_bps"] == "2.200000"
    assert payload["reason_code_counts"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_dataclasses_are_frozen() -> None:
    module = digest_module()
    summary = report((tail_signal(),))
    values = (
        config(),
        tail_signal(),
        summary.rows[0],
        module.MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code=(
                "market_research_rates_bill_supply_tail_digest_repo_specialness_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("1.000000"),
        ),
        summary,
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_module_scope_excludes_io_durable_store_and_execution_surfaces() -> None:
    module = digest_module()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "buy",
        "sell",
        "trade",
        "wallet",
        "order",
        "position",
        "auth",
        "secret",
        "private_key",
        "api_key",
        "cancel",
        "replace",
        "mutation",
        "network",
        "file io",
        "env",
        "subprocess",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
