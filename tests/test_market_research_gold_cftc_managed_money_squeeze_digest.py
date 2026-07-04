import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 21, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_gold_cftc_managed_money_squeeze_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "cftc-gold-alpha",
    *,
    market_slug: str = "gold-record-high-this-week",
    managed_money_long_contracts: str | Decimal = "85000.000000",
    managed_money_short_contracts: str | Decimal = "210000.000000",
    managed_money_net_contracts: str | Decimal = "-125000.000000",
    open_interest_contracts: str | Decimal = "500000.000000",
    net_position_percentile: str | Decimal = "0.040000",
    weekly_gold_return_pct: str | Decimal = "3.200000",
    four_week_gold_return_pct: str | Decimal = "6.500000",
    data_timestamp: datetime = datetime(2026, 7, 2, 19, 30, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("cftc_cot_public_release",),
):
    module = digest()
    return module.GoldCftcManagedMoneySqueezeObservation(
        source_id=source_id,
        market_slug=market_slug,
        managed_money_long_contracts=(
            managed_money_long_contracts
            if isinstance(managed_money_long_contracts, Decimal)
            else d(managed_money_long_contracts)
        ),
        managed_money_short_contracts=(
            managed_money_short_contracts
            if isinstance(managed_money_short_contracts, Decimal)
            else d(managed_money_short_contracts)
        ),
        managed_money_net_contracts=(
            managed_money_net_contracts
            if isinstance(managed_money_net_contracts, Decimal)
            else d(managed_money_net_contracts)
        ),
        open_interest_contracts=(
            open_interest_contracts
            if isinstance(open_interest_contracts, Decimal)
            else d(open_interest_contracts)
        ),
        net_position_percentile=(
            net_position_percentile
            if isinstance(net_position_percentile, Decimal)
            else d(net_position_percentile)
        ),
        weekly_gold_return_pct=(
            weekly_gold_return_pct
            if isinstance(weekly_gold_return_pct, Decimal)
            else d(weekly_gold_return_pct)
        ),
        four_week_gold_return_pct=(
            four_week_gold_return_pct
            if isinstance(four_week_gold_return_pct, Decimal)
            else d(four_week_gold_return_pct)
        ),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_gold_cftc_managed_money_squeeze_digest(
        rows,
        config=cfg or module.GoldCftcManagedMoneySqueezeDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.GoldCftcManagedMoneySqueezeDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-gold-cftc-managed-money-squeeze-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_gold_cftc_managed_money_squeeze_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.crowded_short_count == d("0.000000")
    assert digest_report.rally_confirmation_count == d("0.000000")
    assert digest_report.high_short_open_interest_count == d("0.000000")
    assert digest_report.max_short_open_interest_share == d("0.000000")
    assert digest_report.average_short_open_interest_share == d("0.000000")
    assert digest_report.squeeze_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "gold_cftc_managed_money_squeeze_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.GoldCftcManagedMoneySqueezeReasonCodeCount(
            reason_code="gold_cftc_managed_money_squeeze_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_managed_money_short_squeeze_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "cftc-gold-short-crowd",
            market_slug="gold-record-high-this-week",
            managed_money_long_contracts="85000.000000",
            managed_money_short_contracts="210000.000000",
            managed_money_net_contracts="-125000.000000",
            open_interest_contracts="500000.000000",
            net_position_percentile="0.040000",
            weekly_gold_return_pct="3.200000",
            four_week_gold_return_pct="6.500000",
        ),
        observation(
            "cftc-gold-watch",
            market_slug="gold-above-2500-friday",
            managed_money_long_contracts="105000.000000",
            managed_money_short_contracts="142000.000000",
            managed_money_net_contracts="-37000.000000",
            open_interest_contracts="620000.000000",
            net_position_percentile="0.120000",
            weekly_gold_return_pct="0.800000",
            four_week_gold_return_pct="2.100000",
            data_timestamp=datetime(2026, 7, 2, 15, 30, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "cftc-gold-inline",
            market_slug="gold-above-2300-friday",
            managed_money_long_contracts="160000.000000",
            managed_money_short_contracts="95000.000000",
            managed_money_net_contracts="65000.000000",
            open_interest_contracts="610000.000000",
            net_position_percentile="0.540000",
            weekly_gold_return_pct="0.300000",
            four_week_gold_return_pct="1.200000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_gold_cftc_managed_money_squeeze_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.crowded_short_count == d("2.000000")
    assert digest_report.rally_confirmation_count == d("1.000000")
    assert digest_report.high_short_open_interest_count == d("1.000000")
    assert digest_report.max_short_open_interest_share == d("0.420000")
    assert digest_report.average_short_open_interest_share == d("0.268257")
    assert digest_report.squeeze_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "gold_cftc_managed_money_squeeze_blocked_present",
        "gold_cftc_managed_money_crowded_short_present",
        "gold_cftc_managed_money_price_rally_present",
        "gold_cftc_managed_money_high_short_open_interest_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "gold-record-high-this-week",
        "gold-above-2500-friday",
        "gold-above-2300-friday",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.squeeze_status == "blocked"
    assert blocked.net_position_share == d("-0.250000")
    assert blocked.short_open_interest_share == d("0.420000")
    assert blocked.data_timestamp == datetime(2026, 7, 2, 19, 30, tzinfo=UTC)
    assert blocked.reason_codes == (
        "gold_cftc_managed_money_crowded_short",
        "gold_cftc_managed_money_four_week_rally",
        "gold_cftc_managed_money_high_short_open_interest",
        "gold_cftc_managed_money_price_rally",
        "gold_cftc_managed_money_short_squeeze_blocked",
    )
    assert watch.squeeze_status == "watch"
    assert watch.data_timestamp == datetime(2026, 7, 2, 19, 30, tzinfo=UTC)
    assert watch.reason_codes == (
        "gold_cftc_managed_money_crowded_short",
        "gold_cftc_managed_money_short_squeeze_watch",
    )
    assert passed.squeeze_status == "pass"
    assert passed.reason_codes == ("gold_cftc_managed_money_inline",)


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "cftc-watch-b",
        market_slug="zeta-watch",
        managed_money_long_contracts="120000.000000",
        managed_money_short_contracts="150000.000000",
        managed_money_net_contracts="-30000.000000",
        open_interest_contracts="600000.000000",
        net_position_percentile="0.140000",
        weekly_gold_return_pct="0.700000",
        four_week_gold_return_pct="1.100000",
    )
    second = observation(
        "cftc-blocked",
        market_slug="alpha-blocked",
        managed_money_long_contracts="90000.000000",
        managed_money_short_contracts="220000.000000",
        managed_money_net_contracts="-130000.000000",
        open_interest_contracts="500000.000000",
        net_position_percentile="0.050000",
        weekly_gold_return_pct="3.000000",
        four_week_gold_return_pct="7.000000",
    )
    third = observation(
        "cftc-watch-a",
        market_slug="alpha-watch",
        managed_money_long_contracts="115000.000000",
        managed_money_short_contracts="145000.000000",
        managed_money_net_contracts="-30000.000000",
        open_interest_contracts="580000.000000",
        net_position_percentile="0.140000",
        weekly_gold_return_pct="0.700000",
        four_week_gold_return_pct="1.100000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == (
        "gold_cftc_managed_money_squeeze_blocked_present",
        "gold_cftc_managed_money_crowded_short_present",
        "gold_cftc_managed_money_price_rally_present",
        "gold_cftc_managed_money_high_short_open_interest_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "gold_cftc_managed_money_squeeze_blocked_present",
        "gold_cftc_managed_money_crowded_short_present",
        "gold_cftc_managed_money_price_rally_present",
        "gold_cftc_managed_money_high_short_open_interest_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_squeeze_risk() -> None:
    module = digest()
    cfg = module.GoldCftcManagedMoneySqueezeDigestConfig(
        watch_net_position_percentile=d("0.080000"),
        blocked_net_position_percentile=d("0.020000"),
        weekly_rally_confirmation_pct=d("4.000000"),
        four_week_rally_confirmation_pct=d("9.000000"),
        high_short_open_interest_share=d("0.400000"),
    )

    digest_report = report(
        observation(
            "cftc-moderate",
            managed_money_long_contracts="105000.000000",
            managed_money_short_contracts="145000.000000",
            managed_money_net_contracts="-40000.000000",
            open_interest_contracts="580000.000000",
            net_position_percentile="0.120000",
            weekly_gold_return_pct="2.500000",
            four_week_gold_return_pct="5.500000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_gold_cftc_managed_money_squeeze_screening"
    )
    assert digest_report.rows[0].squeeze_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "gold_cftc_managed_money_inline",
    )
    assert digest_report.squeeze_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "gold_cftc_managed_money_squeeze_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="managed_money_long_contracts must be a Decimal"):
        observation(managed_money_long_contracts=_DecimalSubclass("85000.000000"))
    with pytest.raises(ValueError, match="open_interest_contracts must be positive"):
        observation(open_interest_contracts="0.000000")
    with pytest.raises(ValueError, match="net_position_percentile must be between zero and one"):
        observation(net_position_percentile="1.100000")
    with pytest.raises(ValueError, match="managed_money_net_contracts must equal"):
        observation(managed_money_net_contracts="-124999.000000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 2, 19, 30))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_gold_cftc_managed_money_squeeze_digest(
            (),
            config=module.GoldCftcManagedMoneySqueezeDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 21, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("cftc-dupe"), observation("cftc-dupe"))
    with pytest.raises(ValueError, match="blocked_net_position_percentile"):
        module.GoldCftcManagedMoneySqueezeDigestConfig(
            watch_net_position_percentile=d("0.050000"),
            blocked_net_position_percentile=d("0.100000"),
        )

    valid_row = report(observation("cftc-valid")).rows[0]
    with pytest.raises(ValueError, match="net_position_share must match"):
        replace(valid_row, net_position_share=d("-0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "gold_cftc_managed_money_inline",
                "gold_cftc_managed_money_crowded_short",
            ),
        )

    frozen_observation = observation("cftc-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("cftc-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.GoldCftcManagedMoneySqueezeDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("cftc-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("cftc-payload"))

    payload = module.market_research_gold_cftc_managed_money_squeeze_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["managed_money_short_contracts"] == "210000.000000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-02T19:30:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.GoldCftcManagedMoneySqueezeDigestConfig(),
        observation("cftc-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/market_research_gold_cftc_managed_money_squeeze_digest.py",
    ).read_text()
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
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
