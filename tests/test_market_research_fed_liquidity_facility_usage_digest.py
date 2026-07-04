from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_fed_liquidity_facility_usage_digest"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_fed_liquidity_facility_usage_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest_module():
    return importlib.import_module(MODULE_NAME)


def row(
    digest: Any,
    facility_key: str,
    *,
    facility_name: str | None = None,
    observed_at: datetime | None = None,
    usage_amount_usd: Decimal = Decimal("0.000000"),
    prior_usage_amount_usd: Decimal = Decimal("0.000000"),
    weekly_change_usd: Decimal | None = None,
    usage_share_of_capacity: Decimal = Decimal("0.000000"),
    counterparty_count: Decimal = Decimal("0.000000"),
    source_count: Decimal = Decimal("2.000000"),
    public_source_reference: str = "federal-reserve-h41-release",
    event_config_version: str = "fed-liquidity-facility-usage-v1",
):
    if facility_name is None:
        facility_name = facility_key.replace(".", "-")
    if observed_at is None:
        observed_at = GENERATED_AT - timedelta(hours=1)
    if weekly_change_usd is None:
        weekly_change_usd = usage_amount_usd - prior_usage_amount_usd
    return digest.MarketResearchFedLiquidityFacilityUsageDigestInputRow(
        facility_key=facility_key,
        facility_name=facility_name,
        observed_at=observed_at,
        usage_amount_usd=usage_amount_usd,
        prior_usage_amount_usd=prior_usage_amount_usd,
        weekly_change_usd=weekly_change_usd,
        usage_share_of_capacity=usage_share_of_capacity,
        counterparty_count=counterparty_count,
        source_count=source_count,
        public_source_reference=public_source_reference,
        event_config_version=event_config_version,
    )


def report(digest: Any, rows: tuple[Any, ...], *, generated_at: datetime = GENERATED_AT):
    return digest.build_market_research_fed_liquidity_facility_usage_digest(
        rows,
        config=digest.MarketResearchFedLiquidityFacilityUsageDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in JSON payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            assert_no_floats(item)


def test_fed_liquidity_facility_usage_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_fed_liquidity_facility_usage_digest_reduces_rows_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            row(
                digest,
                "fed.facility.srf",
                facility_name="standing-repo-facility",
                observed_at=GENERATED_AT - timedelta(hours=1),
                usage_amount_usd=d("12500000000.000000"),
                prior_usage_amount_usd=d("7000000000.000000"),
                usage_share_of_capacity=d("0.125000"),
                counterparty_count=d("7.000000"),
                source_count=d("3.000000"),
                public_source_reference="https://federalreserve.example/h41?token=secret",
            ),
            row(
                digest,
                "fed.facility.discount_window",
                facility_name="discount-window",
                observed_at=GENERATED_AT - timedelta(hours=3),
                usage_amount_usd=d("9000000000.000000"),
                prior_usage_amount_usd=d("1000000000.000000"),
                usage_share_of_capacity=d("0.810000"),
                counterparty_count=d("2.000000"),
                source_count=d("1.000000"),
                public_source_reference="private-liquidity-feed",
            ),
            row(
                digest,
                "fed.facility.btfp",
                facility_name="bank-term-funding-program",
                observed_at=GENERATED_AT - timedelta(hours=30),
                usage_amount_usd=d("0.000000"),
                prior_usage_amount_usd=d("0.000000"),
                usage_share_of_capacity=d("0.000000"),
                counterparty_count=d("0.000000"),
                source_count=d("2.000000"),
                event_config_version="fed-liquidity-facility-usage-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_liquidity_facility_usage_digest"
    )
    assert summary.facility_count == d("3.000000")
    assert summary.ready_facility_count == d("1.000000")
    assert summary.watch_facility_count == d("1.000000")
    assert summary.blocked_facility_count == d("1.000000")
    assert summary.active_facility_count == d("2.000000")
    assert summary.high_usage_facility_count == d("1.000000")
    assert summary.usage_spike_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.total_usage_amount_usd == d("21500000000.000000")
    assert summary.total_weekly_change_usd == d("13500000000.000000")
    assert summary.max_usage_share_of_capacity == d("0.810000")
    assert summary.average_usage_share_of_capacity == d("0.311667")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((item.facility_key, item.facility_name) for item in summary.rows) == (
        ("fed.facility.discount_window", "discount-window"),
        ("fed.facility.srf", "standing-repo-facility"),
        ("fed.facility.btfp", "bank-term-funding-program"),
    )

    discount_window = summary.rows[0]
    assert discount_window.facility_usage_status == "blocked"
    assert discount_window.observation_age_seconds == d("10800.000000")
    assert discount_window.weekly_change_usd == d("8000000000.000000")
    assert discount_window.redacted_public_source_reference == "source-<redacted>"
    assert discount_window.reason_codes == (
        "market_research_fed_liquidity_facility_usage_digest_high_usage",
        "market_research_fed_liquidity_facility_usage_digest_usage_spike",
        "market_research_fed_liquidity_facility_usage_digest_thin_sources",
    )

    srf = summary.rows[1]
    assert srf.facility_usage_status == "watch"
    assert srf.observation_age_seconds == d("3600.000000")
    assert srf.redacted_public_source_reference == (
        "https://federalreserve.example/h41?<redacted>"
    )
    assert srf.reason_codes == (
        "market_research_fed_liquidity_facility_usage_digest_usage_spike",
    )

    btfp = summary.rows[2]
    assert btfp.facility_usage_status == "ready"
    assert btfp.observation_age_seconds == d("108000.000000")
    assert btfp.reason_codes == (
        "market_research_fed_liquidity_facility_usage_digest_ready",
        "market_research_fed_liquidity_facility_usage_digest_stale_observation",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_liquidity_facility_usage_digest_high_usage"
            ),
            count=d("1.000000"),
            facility_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_liquidity_facility_usage_digest_usage_spike"
            ),
            count=d("2.000000"),
            facility_ratio=d("0.666667"),
        ),
        digest.MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_liquidity_facility_usage_digest_thin_sources"
            ),
            count=d("1.000000"),
            facility_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_liquidity_facility_usage_digest_ready"
            ),
            count=d("1.000000"),
            facility_ratio=d("0.333333"),
        ),
        digest.MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_liquidity_facility_usage_digest_stale_observation"
            ),
            count=d("1.000000"),
            facility_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.event_config_versions == (
        ("fed.facility.btfp", "fed-liquidity-facility-usage-v0"),
        ("fed.facility.discount_window", "fed-liquidity-facility-usage-v1"),
        ("fed.facility.srf", "fed-liquidity-facility-usage-v1"),
    )


def test_empty_inputs_return_blocked_zero_decimal_report() -> None:
    digest = digest_module()

    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_liquidity_facility_usage_digest"
    )
    assert summary.facility_count == d("0.000000")
    assert summary.ready_facility_count == d("0.000000")
    assert summary.watch_facility_count == d("0.000000")
    assert summary.blocked_facility_count == d("0.000000")
    assert summary.active_facility_count == d("0.000000")
    assert summary.high_usage_facility_count == d("0.000000")
    assert summary.usage_spike_count == d("0.000000")
    assert summary.thin_source_count == d("0.000000")
    assert summary.stale_observation_count == d("0.000000")
    assert summary.total_usage_amount_usd == d("0.000000")
    assert summary.total_weekly_change_usd == d("0.000000")
    assert summary.max_usage_share_of_capacity == d("0.000000")
    assert summary.average_usage_share_of_capacity == d("0.000000")
    assert summary.average_source_count == d("0.000000")
    assert summary.reason_codes == (
        "market_research_fed_liquidity_facility_usage_digest_no_inputs",
    )
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert summary.event_config_versions == ()


def test_payload_uses_decimal_strings_and_redacts_source_references() -> None:
    digest = digest_module()
    summary = report(
        digest,
        (
            row(
                digest,
                "fed.facility.discount_window",
                usage_amount_usd=d("9000000000.000000"),
                prior_usage_amount_usd=d("1000000000.000000"),
                usage_share_of_capacity=d("0.810000"),
                public_source_reference="https://user:secret@fed.example/h41?api_key=abc",
            ),
        ),
    )

    payload = digest.market_research_fed_liquidity_facility_usage_digest_payload(summary)

    assert payload["facility_count"] == "1.000000"
    assert payload["total_usage_amount_usd"] == "9000000000.000000"
    assert payload["rows"][0]["usage_share_of_capacity"] == "0.810000"
    assert payload["rows"][0]["redacted_public_source_reference"] == (
        "https://<redacted>@fed.example/h41?<redacted>"
    )
    assert "secret" not in repr(payload).lower()
    assert "api_key" not in repr(payload).lower()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal_or_none() -> None:
    digest = digest_module()
    summary = report(digest, (row(digest, "fed.facility.srf"),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "ready"  # type: ignore[misc]

    values = (summary, *summary.rows, *summary.reason_code_counts)
    numeric_names = {
        field.name
        for value in values
        for field in fields(value)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_usd")
            or field.name.endswith("_seconds")
            or field.name.endswith("_capacity")
        )
    }
    assert numeric_names
    for value in values:
        for field in fields(value):
            if field.name in numeric_names:
                public_value = getattr(value, field.name)
                assert public_value is None or type(public_value) is Decimal


def test_validation_rejects_bad_types_false_flags_and_inconsistent_change() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="config_version"):
        digest.MarketResearchFedLiquidityFacilityUsageDigestConfig(
            config_version=_StringSubclass(
                digest.DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(digest, (), generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="rows must be a tuple"):
        digest.build_market_research_fed_liquidity_facility_usage_digest(
            [],
            config=digest.MarketResearchFedLiquidityFacilityUsageDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="row must be exactly"):
        report(digest, (object(),))
    with pytest.raises(ValueError, match="usage_amount_usd"):
        row(digest, "fed.facility.srf", usage_amount_usd=_DecimalSubclass("1.0"))
    with pytest.raises(ValueError, match="observed_at"):
        row(digest, "fed.facility.srf", observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="weekly_change_usd"):
        row(
            digest,
            "fed.facility.srf",
            usage_amount_usd=d("2.000000"),
            prior_usage_amount_usd=d("1.000000"),
            weekly_change_usd=d("0.500000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(row(digest, "fed.facility.srf"), paper_only=False)


def test_module_stays_pure_report_only_and_unwired() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_names = {
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "supabase",
        "web3",
        "eth_account",
        "sqlite3",
        "open",
    }
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert imported_roots.isdisjoint(forbidden_names)
    assert "open" not in called_names
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "private_key",
        "secret_key",
        "access_token",
        "place_order",
        "cancel_order",
        "replace_order",
        "trade",
        "submit_order",
        "authentication",
    ):
        assert forbidden not in lowered

    public_values = (
        digest_module().market_research_fed_liquidity_facility_usage_digest_payload(
            report(digest_module(), (row(digest_module(), "fed.facility.srf"),)),
        )
    )
    assert public_values["paper_only"] is True
    assert public_values["report_only"] is True
    assert public_values["readonly"] is True
