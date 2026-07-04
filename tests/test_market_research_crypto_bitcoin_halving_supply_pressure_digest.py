from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_crypto_bitcoin_halving_supply_pressure_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_crypto_bitcoin_halving_supply_pressure_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def halving_observation(
    source_id: str = "source-alpha",
    *,
    miner_cohort_id: str = "public-miner-treasuries",
    market_slug: str = "btc-halving-miner-flow-pressure",
    miner_reserve_btc: str | Decimal = "45000.000000",
    supply_cut_ratio: str | Decimal = "0.030000",
    miner_exchange_inflow_ratio: str | Decimal = "0.090000",
    miner_reserve_drawdown_ratio: str | Decimal = "0.040000",
    hashprice_drawdown_ratio: str | Decimal = "0.160000",
    next_difficulty_adjustment_hours: str | Decimal = "48.000000",
    source_row_count: str | Decimal = "2",
    observation_timestamp: datetime = datetime(2026, 7, 3, 17, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = (
        "bitcoin_halving_supply_cut_active",
        "bitcoin_miner_exchange_inflow_pressure",
        "bitcoin_hashprice_drawdown_pressure",
        "bitcoin_difficulty_adjustment_window_near",
    ),
):
    module = api()
    return module.BitcoinHalvingSupplyPressureObservation(
        source_id=source_id,
        miner_cohort_id=miner_cohort_id,
        market_slug=market_slug,
        miner_reserve_btc=(
            miner_reserve_btc
            if isinstance(miner_reserve_btc, Decimal)
            else d(miner_reserve_btc)
        ),
        supply_cut_ratio=(
            supply_cut_ratio
            if isinstance(supply_cut_ratio, Decimal)
            else d(supply_cut_ratio)
        ),
        miner_exchange_inflow_ratio=(
            miner_exchange_inflow_ratio
            if isinstance(miner_exchange_inflow_ratio, Decimal)
            else d(miner_exchange_inflow_ratio)
        ),
        miner_reserve_drawdown_ratio=(
            miner_reserve_drawdown_ratio
            if isinstance(miner_reserve_drawdown_ratio, Decimal)
            else d(miner_reserve_drawdown_ratio)
        ),
        hashprice_drawdown_ratio=(
            hashprice_drawdown_ratio
            if isinstance(hashprice_drawdown_ratio, Decimal)
            else d(hashprice_drawdown_ratio)
        ),
        next_difficulty_adjustment_hours=(
            next_difficulty_adjustment_hours
            if isinstance(next_difficulty_adjustment_hours, Decimal)
            else d(next_difficulty_adjustment_hours)
        ),
        source_row_count=(
            source_row_count
            if isinstance(source_row_count, Decimal)
            else d(source_row_count)
        ),
        observation_timestamp=observation_timestamp,
        reason_codes=reason_codes,
    )


def digest_report(
    *rows: object,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
):
    module = api()
    return module.build_market_research_crypto_bitcoin_halving_supply_pressure_digest(
        rows,
        config=config or module.BitcoinHalvingSupplyPressureDigestConfig(),
        generated_at=generated_at,
    )


def assert_payload_has_no_public_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_public_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_public_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))


def test_bitcoin_halving_supply_pressure_digest_flags_high_risk_and_sorts_rows() -> None:
    module = api()

    report = digest_report(
        halving_observation(
            "source-watch",
            miner_cohort_id="mid-cap-miners",
            market_slug="btc-halving-watch-pressure",
            miner_reserve_btc="45000.000000",
            supply_cut_ratio="0.030000",
            miner_exchange_inflow_ratio="0.090000",
            miner_reserve_drawdown_ratio="0.040000",
            hashprice_drawdown_ratio="0.160000",
            next_difficulty_adjustment_hours="48.000000",
            source_row_count="3",
            reason_codes=(
                "bitcoin_halving_supply_cut_active",
                "bitcoin_miner_exchange_inflow_pressure",
                "bitcoin_hashprice_drawdown_pressure",
                "bitcoin_difficulty_adjustment_window_near",
            ),
        ),
        halving_observation(
            "source-pass",
            miner_cohort_id="large-public-miners",
            market_slug="btc-halving-low-pressure",
            miner_reserve_btc="120000.000000",
            supply_cut_ratio="0.010000",
            miner_exchange_inflow_ratio="0.020000",
            miner_reserve_drawdown_ratio="0.010000",
            hashprice_drawdown_ratio="0.020000",
            next_difficulty_adjustment_hours="140.000000",
            source_row_count="1",
            observation_timestamp=datetime(
                2026,
                7,
                3,
                10,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            reason_codes=("bitcoin_halving_supply_pressure_stable",),
        ),
        halving_observation(
            "source-blocked",
            miner_cohort_id="public-miner-treasuries",
            market_slug="btc-halving-blocked-pressure",
            miner_reserve_btc="30000.000000",
            supply_cut_ratio="0.060000",
            miner_exchange_inflow_ratio="0.180000",
            miner_reserve_drawdown_ratio="0.120000",
            hashprice_drawdown_ratio="0.350000",
            next_difficulty_adjustment_hours="24.000000",
            source_row_count="4",
            reason_codes=(
                "bitcoin_halving_supply_cut_active",
                "bitcoin_miner_exchange_inflow_pressure",
                "bitcoin_miner_reserve_drawdown_pressure",
                "bitcoin_hashprice_drawdown_pressure",
                "bitcoin_difficulty_adjustment_window_near",
            ),
        ),
    )

    assert isinstance(report, module.BitcoinHalvingSupplyPressureDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-bitcoin-halving-supply-pressure-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_bitcoin_halving_supply_pressure_digest"
    )
    assert report.source_row_count == d("8")
    assert report.observation_count == d("3")
    assert report.blocked_segment_count == d("1")
    assert report.watch_segment_count == d("1")
    assert report.pass_segment_count == d("1")
    assert report.total_miner_reserve_btc == d("195000.000000")
    assert report.max_pressure_score == d("1.000000")
    assert report.average_pressure_score == d("0.533333")
    assert report.blocked_observation_ratio == d("0.333333")
    assert report.reason_codes == (
        "bitcoin_halving_supply_pressure_blocked_risk_present",
        "bitcoin_halving_supply_pressure_watch_risk_present",
    )
    assert report.reason_code_counts == (
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_halving_blocked_supply_cut",
            count=d("1"),
            observation_ratio=d("0.333333"),
        ),
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_miner_exchange_inflow_pressure",
            count=d("2"),
            observation_ratio=d("0.666667"),
        ),
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_miner_reserve_drawdown_pressure",
            count=d("1"),
            observation_ratio=d("0.333333"),
        ),
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_hashprice_drawdown_pressure",
            count=d("2"),
            observation_ratio=d("0.666667"),
        ),
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_difficulty_adjustment_window_near",
            count=d("2"),
            observation_ratio=d("0.666667"),
        ),
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_halving_supply_pressure_watch",
            count=d("1"),
            observation_ratio=d("0.333333"),
        ),
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_halving_supply_pressure_stable",
            count=d("1"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.miner_cohort_id for row in report.segment_rows) == (
        "public-miner-treasuries",
        "mid-cap-miners",
        "large-public-miners",
    )
    blocked, watch, passed = report.segment_rows
    assert blocked.pressure_status == "blocked"
    assert blocked.pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "bitcoin_halving_blocked_supply_cut",
        "bitcoin_miner_exchange_inflow_pressure",
        "bitcoin_miner_reserve_drawdown_pressure",
        "bitcoin_hashprice_drawdown_pressure",
        "bitcoin_difficulty_adjustment_window_near",
    )
    assert watch.pressure_status == "watch"
    assert watch.pressure_score == d("0.600000")
    assert watch.reason_codes == (
        "bitcoin_miner_exchange_inflow_pressure",
        "bitcoin_hashprice_drawdown_pressure",
        "bitcoin_difficulty_adjustment_window_near",
        "bitcoin_halving_supply_pressure_watch",
    )
    assert passed.pressure_status == "pass"
    assert passed.pressure_score == d("0.000000")
    assert passed.observation_timestamp == datetime(2026, 7, 3, 14, 30, tzinfo=UTC)
    assert passed.reason_codes == ("bitcoin_halving_supply_pressure_stable",)


def test_empty_bitcoin_halving_digest_is_report_only_blocked_and_payload_stringed() -> None:
    module = api()

    report = digest_report()
    payload = (
        module.market_research_crypto_bitcoin_halving_supply_pressure_digest_payload(
            report,
        )
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_bitcoin_halving_supply_pressure_digest"
    )
    assert report.source_row_count == d("0")
    assert report.observation_count == d("0")
    assert report.blocked_segment_count == d("0")
    assert report.watch_segment_count == d("0")
    assert report.pass_segment_count == d("0")
    assert report.total_miner_reserve_btc == d("0.000000")
    assert report.max_pressure_score == d("0.000000")
    assert report.average_pressure_score == d("0.000000")
    assert report.blocked_observation_ratio == d("0.000000")
    assert report.segment_rows == ()
    assert report.reason_codes == ("bitcoin_halving_supply_pressure_digest_empty",)
    assert report.reason_code_counts == (
        module.BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code="bitcoin_halving_supply_pressure_digest_empty",
            count=d("1"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert payload["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["source_row_count"] == "0.000000"
    assert payload["total_miner_reserve_btc"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_payload_has_no_public_numbers(payload)


def test_validation_rejects_bad_inputs_flags_duplicates_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="miner_reserve_btc must be a Decimal"):
        halving_observation(miner_reserve_btc=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="supply_cut_ratio must be between zero and one"):
        halving_observation(supply_cut_ratio="1.100000")
    with pytest.raises(
        ValueError,
        match="next_difficulty_adjustment_hours must be nonnegative",
    ):
        halving_observation(next_difficulty_adjustment_hours="-1.000000")
    with pytest.raises(ValueError, match="observation_timestamp must be timezone-aware"):
        halving_observation(observation_timestamp=datetime(2026, 7, 3, 17, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_bitcoin_halving_supply_pressure_digest(
            (),
            config=module.BitcoinHalvingSupplyPressureDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest_report(
            halving_observation("source-dupe"),
            halving_observation("source-dupe"),
        )
    with pytest.raises(ValueError, match="reason_codes must be sorted deterministically"):
        halving_observation(
            supply_cut_ratio="0.060000",
            miner_exchange_inflow_ratio="0.180000",
            reason_codes=(
                "bitcoin_miner_exchange_inflow_pressure",
                "bitcoin_halving_supply_cut_active",
            ),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(halving_observation(), paper_only=False)
    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.BitcoinHalvingSupplyPressureDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="total_miner_reserve_btc must match rows"):
        replace(
            digest_report(halving_observation("source-valid")),
            total_miner_reserve_btc=d("1"),
        )

    row = halving_observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.miner_cohort_id = "other-cohort"  # type: ignore[misc]

    report = digest_report(halving_observation("source-dataclass"))
    for value in (
        module.BitcoinHalvingSupplyPressureDigestConfig(),
        halving_observation("source-public-numerics"),
        report.segment_rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if _is_public_numeric_field(field.name):
                assert type(getattr(value, field.name)) is Decimal, field.name


def test_non_default_config_threshold_can_escalate_miner_flow_pressure() -> None:
    module = api()
    config = module.BitcoinHalvingSupplyPressureDigestConfig(
        watch_miner_exchange_inflow_ratio=d("0.040000"),
        blocked_miner_exchange_inflow_ratio=d("0.090000"),
    )

    report = digest_report(
        halving_observation(
            "source-tight-threshold",
            miner_exchange_inflow_ratio="0.100000",
            supply_cut_ratio="0.010000",
            miner_reserve_drawdown_ratio="0.010000",
            hashprice_drawdown_ratio="0.020000",
            next_difficulty_adjustment_hours="120.000000",
            reason_codes=("bitcoin_miner_exchange_inflow_pressure",),
        ),
        config=config,
    )

    assert report.digest_status == "blocked"
    assert report.max_pressure_score == d("1.000000")
    assert report.segment_rows[0].pressure_status == "blocked"
    assert report.segment_rows[0].reason_codes == (
        "bitcoin_miner_exchange_inflow_pressure",
    )


def test_payload_rejects_wrong_report_type_and_module_has_no_impure_surfaces() -> None:
    module = api()
    report = digest_report(halving_observation("source-json"))
    payload = (
        module.market_research_crypto_bitcoin_halving_supply_pressure_digest_payload(
            report,
        )
    )

    assert payload["segment_rows"][0]["miner_reserve_btc"] == "45000.000000"
    assert payload["segment_rows"][0]["pressure_score"] == "0.600000"
    assert_payload_has_no_public_numbers(payload)

    with pytest.raises(ValueError, match="report must be exactly"):
        module.market_research_crypto_bitcoin_halving_supply_pressure_digest_payload(
            object(),
        )

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_call_names = {"connect", "execute", "urlopen"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "signed transaction",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_btc")
        or field_name.endswith("_count")
        or field_name.endswith("_hours")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
    )
