import ast
import importlib
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
SIX_DECIMAL_RE = re.compile(r"^-?[0-9]+\.[0-9]{6}$")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_gold_mint_premium_spread_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "mint-premium-alpha",
    *,
    market_slug: str = "gold-above-2500-july",
    mint_product_id: str = "american-eagle-1oz",
    primary_mint_premium_pct: str | Decimal = "19.500000",
    secondary_market_premium_pct: str | Decimal = "7.250000",
    premium_spread_pct: str | Decimal = "12.250000",
    available_inventory_units: str | Decimal = "300.000000",
    days_since_last_mint_price_update: str | Decimal = "2.000000",
    confidence_score: str | Decimal = "0.820000",
    observed_at: datetime = datetime(2026, 7, 4, 12, 30, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("public_mint_product_page",),
):
    module = digest()
    return module.GoldMintPremiumSpreadObservation(
        source_id=source_id,
        market_slug=market_slug,
        mint_product_id=mint_product_id,
        primary_mint_premium_pct=(
            primary_mint_premium_pct
            if isinstance(primary_mint_premium_pct, Decimal)
            else d(primary_mint_premium_pct)
        ),
        secondary_market_premium_pct=(
            secondary_market_premium_pct
            if isinstance(secondary_market_premium_pct, Decimal)
            else d(secondary_market_premium_pct)
        ),
        premium_spread_pct=(
            premium_spread_pct
            if isinstance(premium_spread_pct, Decimal)
            else d(premium_spread_pct)
        ),
        available_inventory_units=(
            available_inventory_units
            if isinstance(available_inventory_units, Decimal)
            else d(available_inventory_units)
        ),
        days_since_last_mint_price_update=(
            days_since_last_mint_price_update
            if isinstance(days_since_last_mint_price_update, Decimal)
            else d(days_since_last_mint_price_update)
        ),
        confidence_score=(
            confidence_score
            if isinstance(confidence_score, Decimal)
            else d(confidence_score)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_gold_mint_premium_spread_digest(
        rows,
        config=cfg or module.GoldMintPremiumSpreadDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.GoldMintPremiumSpreadDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-gold-mint-premium-spread-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_gold_mint_premium_spread_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.wide_spread_count == d("0.000000")
    assert digest_report.elevated_mint_premium_count == d("0.000000")
    assert digest_report.low_inventory_count == d("0.000000")
    assert digest_report.stale_quote_count == d("0.000000")
    assert digest_report.low_confidence_count == d("0.000000")
    assert digest_report.max_premium_spread_pct == d("0.000000")
    assert digest_report.average_premium_spread_pct == d("0.000000")
    assert digest_report.max_primary_mint_premium_pct == d("0.000000")
    assert digest_report.mint_premium_spread_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "gold_mint_premium_spread_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.GoldMintPremiumSpreadReasonCodeCount(
            reason_code="gold_mint_premium_spread_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_wide_mint_premium_spread_blocks_gold_probability_screening() -> None:
    digest_report = report(
        observation(
            "mint-blocked",
            market_slug="gold-record-high-july",
            mint_product_id="american-eagle-1oz",
            primary_mint_premium_pct="21.500000",
            secondary_market_premium_pct="8.000000",
            premium_spread_pct="13.500000",
            available_inventory_units="250.000000",
            days_since_last_mint_price_update="3.000000",
            confidence_score="0.820000",
        ),
        observation(
            "mint-watch",
            market_slug="gold-above-2400-july",
            mint_product_id="maple-leaf-1oz",
            primary_mint_premium_pct="13.750000",
            secondary_market_premium_pct="7.500000",
            premium_spread_pct="6.250000",
            available_inventory_units="2500.000000",
            days_since_last_mint_price_update="9.000000",
            confidence_score="0.500000",
            observed_at=datetime(2026, 7, 4, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "mint-pass",
            market_slug="gold-above-2300-july",
            mint_product_id="buffalo-1oz",
            primary_mint_premium_pct="8.000000",
            secondary_market_premium_pct="6.900000",
            premium_spread_pct="1.100000",
            available_inventory_units="4000.000000",
            days_since_last_mint_price_update="1.000000",
            confidence_score="0.910000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_gold_mint_premium_spread_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.wide_spread_count == d("2.000000")
    assert digest_report.elevated_mint_premium_count == d("2.000000")
    assert digest_report.low_inventory_count == d("1.000000")
    assert digest_report.stale_quote_count == d("1.000000")
    assert digest_report.low_confidence_count == d("1.000000")
    assert digest_report.max_premium_spread_pct == d("13.500000")
    assert digest_report.average_premium_spread_pct == d("6.950000")
    assert digest_report.max_primary_mint_premium_pct == d("21.500000")
    assert digest_report.mint_premium_spread_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "gold_mint_premium_spread_blocked_present",
        "gold_mint_premium_spread_wide_present",
        "gold_mint_premium_primary_premium_elevated_present",
        "gold_mint_premium_low_inventory_present",
        "gold_mint_premium_stale_quote_present",
        "gold_mint_premium_low_confidence_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "gold-record-high-july",
        "gold-above-2400-july",
        "gold-above-2300-july",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.spread_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 4, 12, 30, tzinfo=UTC)
    assert blocked.reason_codes == (
        "gold_mint_premium_low_inventory",
        "gold_mint_premium_primary_premium_extreme",
        "gold_mint_premium_spread_blocked",
        "gold_mint_premium_spread_extreme",
    )
    assert watched.spread_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 4, 12, 30, tzinfo=UTC)
    assert watched.reason_codes == (
        "gold_mint_premium_low_confidence",
        "gold_mint_premium_primary_premium_elevated",
        "gold_mint_premium_spread_watch",
        "gold_mint_premium_spread_wide",
        "gold_mint_premium_stale_quote",
    )
    assert passed.spread_status == "pass"
    assert passed.reason_codes == ("gold_mint_premium_spread_inline",)


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "mint-watch-b",
        market_slug="zeta-watch",
        mint_product_id="zeta-coin",
        primary_mint_premium_pct="13.000000",
        secondary_market_premium_pct="7.300000",
        premium_spread_pct="5.700000",
        available_inventory_units="2000.000000",
    )
    second = observation(
        "mint-blocked",
        market_slug="alpha-blocked",
        mint_product_id="alpha-coin",
        primary_mint_premium_pct="20.000000",
        secondary_market_premium_pct="8.000000",
        premium_spread_pct="12.000000",
        available_inventory_units="400.000000",
    )
    third = observation(
        "mint-watch-a",
        market_slug="alpha-watch",
        mint_product_id="alpha-watch-coin",
        primary_mint_premium_pct="13.000000",
        secondary_market_premium_pct="7.300000",
        premium_spread_pct="5.700000",
        available_inventory_units="2000.000000",
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
        "gold_mint_premium_spread_blocked_present",
        "gold_mint_premium_spread_wide_present",
        "gold_mint_premium_primary_premium_elevated_present",
        "gold_mint_premium_low_inventory_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "gold_mint_premium_spread_blocked_present",
        "gold_mint_premium_spread_wide_present",
        "gold_mint_premium_primary_premium_elevated_present",
        "gold_mint_premium_low_inventory_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_spread_risk() -> None:
    module = digest()
    cfg = module.GoldMintPremiumSpreadDigestConfig(
        watch_premium_spread_pct=d("8.000000"),
        blocked_premium_spread_pct=d("16.000000"),
        watch_primary_mint_premium_pct=d("16.000000"),
        blocked_primary_mint_premium_pct=d("24.000000"),
        low_inventory_units=d("100.000000"),
        stale_price_update_days=d("12.000000"),
        low_confidence_score=d("0.450000"),
    )

    digest_report = report(
        observation(
            "mint-moderate",
            primary_mint_premium_pct="13.750000",
            secondary_market_premium_pct="7.500000",
            premium_spread_pct="6.250000",
            available_inventory_units="2500.000000",
            days_since_last_mint_price_update="9.000000",
            confidence_score="0.500000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_gold_mint_premium_spread_screening"
    )
    assert digest_report.rows[0].spread_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "gold_mint_premium_spread_inline",
    )
    assert digest_report.mint_premium_spread_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "gold_mint_premium_spread_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="primary_mint_premium_pct must be a Decimal"):
        observation(primary_mint_premium_pct=_DecimalSubclass("19.500000"))
    with pytest.raises(ValueError, match="available_inventory_units must be nonnegative"):
        observation(available_inventory_units="-1.000000")
    with pytest.raises(ValueError, match="confidence_score must be between zero and one"):
        observation(confidence_score="1.100000")
    with pytest.raises(ValueError, match="premium_spread_pct must equal"):
        observation(premium_spread_pct="12.260000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 30))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_gold_mint_premium_spread_digest(
            (),
            config=module.GoldMintPremiumSpreadDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("mint-dupe"), observation("mint-dupe"))
    with pytest.raises(ValueError, match="blocked_premium_spread_pct"):
        module.GoldMintPremiumSpreadDigestConfig(
            watch_premium_spread_pct=d("10.000000"),
            blocked_premium_spread_pct=d("9.000000"),
        )

    valid_row = report(observation("mint-valid")).rows[0]
    with pytest.raises(ValueError, match="premium_spread_pct must equal"):
        replace(valid_row, premium_spread_pct=d("99.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "gold_mint_premium_low_inventory",
                "gold_mint_premium_spread_inline",
            ),
        )

    frozen_observation = observation("mint-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("mint-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.GoldMintPremiumSpreadDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("mint-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("mint-payload"))

    payload = module.market_research_gold_mint_premium_spread_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["max_premium_spread_pct"] == "12.250000"
    assert payload["rows"][0]["primary_mint_premium_pct"] == "19.500000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:30:00+00:00"

    numeric_key_fragments = (
        "_count",
        "_pct",
        "_ratio",
        "_score",
        "_units",
        "_days",
        "input_count",
        "row_count",
        "count",
    )

    def walk_payload(value: object, *, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                lowered = child_key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child, key=child_key)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child, key=key)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            if isinstance(value, str) and any(fragment in key for fragment in numeric_key_fragments):
                assert SIX_DECIMAL_RE.fullmatch(value), key

    walk_payload(payload)

    for public_record in (
        module.GoldMintPremiumSpreadDigestConfig(),
        observation("mint-dataclass"),
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
        "src/polymarket_alpha_lab/market_research_gold_mint_premium_spread_digest.py",
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
        "api_key",
        "secret",
        "fast mode",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
