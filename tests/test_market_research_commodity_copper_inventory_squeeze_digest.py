import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_commodity_copper_inventory_squeeze_digest"
)
GENERATED_AT = datetime(2026, 7, 5, 16, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "lme-copper-alpha",
    *,
    event_key: str = "copper-inventory-squeeze-this-week",
    warehouse_region: str = "lme-asia",
    visible_inventory_tonnes: str | Decimal = "300000.000000",
    weekly_inventory_change_tonnes: str | Decimal = "-18000.000000",
    open_interest_tonnes: str | Decimal = "4200000.000000",
    inventory_percentile: str | Decimal = "0.040000",
    cash_3m_spread_pct: str | Decimal = "0.800000",
    weekly_copper_return_pct: str | Decimal = "2.400000",
    data_timestamp: datetime = datetime(2026, 7, 5, 10, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("lme_public_inventory_report",),
) -> Any:
    module = api()
    return module.CommodityCopperInventorySqueezeObservation(
        source_id=source_id,
        event_key=event_key,
        warehouse_region=warehouse_region,
        visible_inventory_tonnes=(
            visible_inventory_tonnes
            if isinstance(visible_inventory_tonnes, Decimal)
            else d(visible_inventory_tonnes)
        ),
        weekly_inventory_change_tonnes=(
            weekly_inventory_change_tonnes
            if isinstance(weekly_inventory_change_tonnes, Decimal)
            else d(weekly_inventory_change_tonnes)
        ),
        open_interest_tonnes=(
            open_interest_tonnes
            if isinstance(open_interest_tonnes, Decimal)
            else d(open_interest_tonnes)
        ),
        inventory_percentile=(
            inventory_percentile
            if isinstance(inventory_percentile, Decimal)
            else d(inventory_percentile)
        ),
        cash_3m_spread_pct=(
            cash_3m_spread_pct
            if isinstance(cash_3m_spread_pct, Decimal)
            else d(cash_3m_spread_pct)
        ),
        weekly_copper_return_pct=(
            weekly_copper_return_pct
            if isinstance(weekly_copper_return_pct, Decimal)
            else d(weekly_copper_return_pct)
        ),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def digest(*rows: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_market_research_commodity_copper_inventory_squeeze_digest(
        rows,
        config=cfg or module.CommodityCopperInventorySqueezeDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_blocked_report_only_digest() -> None:
    module = api()

    report = digest()

    assert isinstance(report, module.CommodityCopperInventorySqueezeDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-commodity-copper-inventory-squeeze-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_commodity_copper_inventory_squeeze_screening"
    )
    assert report.input_count == ZERO
    assert report.row_count == ZERO
    assert report.blocked_count == ZERO
    assert report.watch_count == ZERO
    assert report.pass_count == ZERO
    assert report.low_inventory_count == ZERO
    assert report.active_withdrawal_count == ZERO
    assert report.backwardation_count == ZERO
    assert report.price_rally_count == ZERO
    assert report.max_withdrawal_pressure_pct == ZERO
    assert report.min_inventory_coverage_ratio == ZERO
    assert report.average_inventory_coverage_ratio == ZERO
    assert report.squeeze_risk_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == (
        "commodity_copper_inventory_squeeze_digest_empty",
    )
    assert report.reason_code_counts == (
        module.CommodityCopperInventorySqueezeReasonCodeCount(
            reason_code="commodity_copper_inventory_squeeze_digest_empty",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_inventory_squeeze_blocks_probability_screening() -> None:
    report = digest(
        observation(
            "lme-copper-blocked",
            event_key="copper-above-11000-this-week",
            visible_inventory_tonnes="300000.000000",
            weekly_inventory_change_tonnes="-18000.000000",
            open_interest_tonnes="4200000.000000",
            inventory_percentile="0.040000",
            cash_3m_spread_pct="0.800000",
            weekly_copper_return_pct="2.400000",
        ),
        observation(
            "shfe-copper-watch",
            event_key="copper-inventory-drawdown-this-week",
            warehouse_region="shfe-bonded",
            visible_inventory_tonnes="520000.000000",
            weekly_inventory_change_tonnes="-9000.000000",
            open_interest_tonnes="3600000.000000",
            inventory_percentile="0.150000",
            cash_3m_spread_pct="0.100000",
            weekly_copper_return_pct="0.900000",
            data_timestamp=datetime(2026, 7, 5, 6, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "comex-copper-inline",
            event_key="copper-rangebound-this-week",
            warehouse_region="comex-us",
            visible_inventory_tonnes="920000.000000",
            weekly_inventory_change_tonnes="4000.000000",
            open_interest_tonnes="2800000.000000",
            inventory_percentile="0.550000",
            cash_3m_spread_pct="-0.100000",
            weekly_copper_return_pct="0.200000",
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_commodity_copper_inventory_squeeze_screening"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.low_inventory_count == d("2.000000")
    assert report.active_withdrawal_count == d("1.000000")
    assert report.backwardation_count == d("1.000000")
    assert report.price_rally_count == d("1.000000")
    assert report.max_withdrawal_pressure_pct == d("6.000000")
    assert report.min_inventory_coverage_ratio == d("0.071429")
    assert report.average_inventory_coverage_ratio == d("0.181481")
    assert report.squeeze_risk_score == d("1.000000")
    assert report.reason_codes == (
        "commodity_copper_inventory_squeeze_blocked_present",
        "commodity_copper_inventory_low_visible_inventory_present",
        "commodity_copper_inventory_active_withdrawal_present",
        "commodity_copper_inventory_backwardation_present",
        "commodity_copper_inventory_price_rally_present",
    )
    assert tuple(row.event_key for row in report.rows) == (
        "copper-above-11000-this-week",
        "copper-inventory-drawdown-this-week",
        "copper-rangebound-this-week",
    )

    blocked, watch, passed = report.rows
    assert blocked.squeeze_status == "blocked"
    assert blocked.inventory_coverage_ratio == d("0.071429")
    assert blocked.withdrawal_pressure_pct == d("6.000000")
    assert blocked.data_timestamp == datetime(2026, 7, 5, 10, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "commodity_copper_inventory_active_withdrawal",
        "commodity_copper_inventory_backwardation",
        "commodity_copper_inventory_low_visible_inventory",
        "commodity_copper_inventory_open_interest_coverage_low",
        "commodity_copper_inventory_price_rally",
        "commodity_copper_inventory_squeeze_blocked",
    )
    assert watch.squeeze_status == "watch"
    assert watch.data_timestamp == datetime(2026, 7, 5, 10, 0, tzinfo=UTC)
    assert watch.reason_codes == (
        "commodity_copper_inventory_low_visible_inventory",
        "commodity_copper_inventory_squeeze_watch",
    )
    assert passed.squeeze_status == "pass"
    assert passed.reason_codes == ("commodity_copper_inventory_inline",)


def test_rows_reason_codes_and_public_constructors_require_canonical_order() -> None:
    first = observation(
        "copper-watch-b",
        event_key="zeta-watch",
        warehouse_region="lme-europe",
        visible_inventory_tonnes="600000.000000",
        weekly_inventory_change_tonnes="-6000.000000",
        open_interest_tonnes="3600000.000000",
        inventory_percentile="0.120000",
        cash_3m_spread_pct="0.200000",
        weekly_copper_return_pct="0.700000",
    )
    second = observation(
        "copper-blocked",
        event_key="alpha-blocked",
        warehouse_region="lme-asia",
        visible_inventory_tonnes="280000.000000",
        weekly_inventory_change_tonnes="-20000.000000",
        open_interest_tonnes="4200000.000000",
        inventory_percentile="0.060000",
        cash_3m_spread_pct="0.900000",
        weekly_copper_return_pct="3.000000",
    )
    third = observation(
        "copper-watch-a",
        event_key="alpha-watch",
        warehouse_region="shfe-bonded",
        visible_inventory_tonnes="590000.000000",
        weekly_inventory_change_tonnes="-5000.000000",
        open_interest_tonnes="3300000.000000",
        inventory_percentile="0.120000",
        cash_3m_spread_pct="0.200000",
        weekly_copper_return_pct="0.700000",
    )

    forward = digest(first, second, third)
    reverse = digest(third, second, first)

    assert forward == reverse
    assert tuple(row.event_key for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))

    with pytest.raises(ValueError, match="rows must be canonical"):
        replace(forward, rows=tuple(reversed(forward.rows)))
    with pytest.raises(ValueError, match="rows must contain"):
        replace(forward, rows=list(forward.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        replace(forward, reason_codes=tuple(reversed(forward.reason_codes)))
    with pytest.raises(ValueError, match="reason_codes must contain"):
        replace(forward, reason_codes=list(forward.reason_codes))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts must contain"):
        replace(
            forward,
            reason_code_counts=list(forward.reason_code_counts),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="upstream_reason_codes must be canonical"):
        observation(upstream_reason_codes=("zeta_reason", "alpha_reason"))
    with pytest.raises(ValueError, match="upstream_reason_codes must contain"):
        observation(upstream_reason_codes=["alpha_reason"])  # type: ignore[arg-type]


def test_non_default_thresholds_can_downgrade_moderate_squeeze_risk() -> None:
    module = api()
    cfg = module.CommodityCopperInventorySqueezeDigestConfig(
        watch_inventory_percentile=d("0.080000"),
        blocked_inventory_percentile=d("0.020000"),
        watch_inventory_coverage_ratio=d("0.090000"),
        blocked_inventory_coverage_ratio=d("0.040000"),
        withdrawal_pressure_pct=d("8.000000"),
        backwardation_confirmation_pct=d("1.200000"),
        price_rally_confirmation_pct=d("4.000000"),
    )

    report = digest(
        observation(
            "copper-moderate",
            visible_inventory_tonnes="420000.000000",
            weekly_inventory_change_tonnes="-18000.000000",
            open_interest_tonnes="4200000.000000",
            inventory_percentile="0.120000",
            cash_3m_spread_pct="0.800000",
            weekly_copper_return_pct="2.400000",
        ),
        cfg=cfg,
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "allow_report_only_commodity_copper_inventory_squeeze_screening"
    )
    assert report.rows[0].squeeze_status == "pass"
    assert report.rows[0].reason_codes == (
        "commodity_copper_inventory_inline",
    )
    assert report.squeeze_risk_score == ZERO
    assert report.reason_codes == (
        "commodity_copper_inventory_squeeze_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="visible_inventory_tonnes must be a Decimal"):
        observation(visible_inventory_tonnes=_DecimalSubclass("300000.000000"))
    with pytest.raises(ValueError, match="visible_inventory_tonnes must be six-decimal"):
        observation(visible_inventory_tonnes=d("300000"))
    with pytest.raises(ValueError, match="open_interest_tonnes must be positive"):
        observation(open_interest_tonnes="0.000000")
    with pytest.raises(ValueError, match="inventory_percentile must be between zero and one"):
        observation(inventory_percentile="1.100000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 5, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_commodity_copper_inventory_squeeze_digest(
            (),
            config=module.CommodityCopperInventorySqueezeDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 16, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="data_timestamp must not be after generated_at"):
        digest(observation(data_timestamp=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observations must contain"):
        digest("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        digest(observation("copper-dupe"), observation("copper-dupe"))
    with pytest.raises(ValueError, match="blocked_inventory_percentile"):
        module.CommodityCopperInventorySqueezeDigestConfig(
            watch_inventory_percentile=d("0.050000"),
            blocked_inventory_percentile=d("0.100000"),
        )

    valid_row = digest(observation("copper-valid")).rows[0]
    with pytest.raises(ValueError, match="inventory_coverage_ratio must match"):
        replace(valid_row, inventory_coverage_ratio=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "commodity_copper_inventory_inline",
                "commodity_copper_inventory_low_visible_inventory",
            ),
        )

    frozen_observation = observation("copper-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_payload_recursively_revalidates_and_serializes_string_numerics() -> None:
    module = api()
    report = digest(observation("copper-payload"))

    payload = module.market_research_commodity_copper_inventory_squeeze_digest_payload(
        report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["visible_inventory_tonnes"] == "300000.000000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-05T10:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "api_key" not in lowered
                assert "market_slug" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.CommodityCopperInventorySqueezeDigestConfig(),
        observation("copper-dataclass"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal
                assert field_value.as_tuple().exponent == -6

    tampered_report = digest(observation("copper-tampered"))
    object.__setattr__(tampered_report.rows[0], "data_timestamp", datetime(2026, 7, 5, 6, 0, tzinfo=timezone(timedelta(hours=-4))))
    with pytest.raises(ValueError, match="UTC"):
        module.market_research_commodity_copper_inventory_squeeze_digest_payload(
            tampered_report,
        )

    nested_tampered_report = digest(observation("copper-nested"))
    object.__setattr__(nested_tampered_report, "rows", ({"not": "a dataclass"},))
    with pytest.raises(ValueError, match="rows must contain"):
        module.market_research_commodity_copper_inventory_squeeze_digest_payload(
            nested_tampered_report,
        )

    false_flag_report = digest(observation("copper-flags"))
    object.__setattr__(false_flag_report.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_commodity_copper_inventory_squeeze_digest_payload(
            false_flag_report,
        )

    unsafe_report = digest(observation("copper-unsafe"))
    object.__setattr__(unsafe_report, "recommended_next_step", "api_key")
    with pytest.raises(ValueError, match="unsafe|secret"):
        module.market_research_commodity_copper_inventory_squeeze_digest_payload(
            unsafe_report,
        )

    with pytest.raises(ValueError, match="CommodityCopperInventorySqueezeDigestReport"):
        module.market_research_commodity_copper_inventory_squeeze_digest_payload(payload)

    with pytest.raises(ValueError, match="count must be positive"):
        replace(report.reason_code_counts[0], count=ZERO)

    mismatched_count_report = digest(observation("copper-count-mismatch"))
    mismatched_count = replace(
        mismatched_count_report.reason_code_counts[0],
        count=d("2.000000"),
    )
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(mismatched_count_report, reason_code_counts=(mismatched_count,))


def test_module_has_no_durable_io_live_trading_or_asdict_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_commodity_copper_inventory_squeeze_digest.py",
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
        "pathlib",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "asdict",
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "market_slug",
    ):
        assert forbidden not in source.lower()
