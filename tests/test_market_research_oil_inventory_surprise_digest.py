from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_oil_inventory_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_OIL_INVENTORY_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchOilInventorySurpriseDigestConfig,
    MarketResearchOilInventorySurpriseDigestInputRow,
    MarketResearchOilInventorySurpriseDigestReasonCodeCount,
    MarketResearchOilInventorySurpriseDigestReport,
    MarketResearchOilInventorySurpriseDigestRow,
    build_market_research_oil_inventory_surprise_digest,
    market_research_oil_inventory_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchOilInventorySurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_OIL_INVENTORY_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold_barrels": d("2000000.000000"),
        "material_price_reaction_threshold": d("0.010000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchOilInventorySurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.wti.eia",
    *,
    condition_id: str = "condition_wti_eia",
    market_slug: str = "wti-weekly-inventory",
    inventory_report_key: str = "eia.weekly.petroleum",
    inventory_report_family: str = "eia",
    inventory_report_reference: str = "public-eia-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("2"),
    forecast_change_barrels: Decimal = d("1000000.000000"),
    actual_change_barrels: Decimal = d("2500000.000000"),
    surprise_score: Decimal = d("0.020000"),
    expected_price_reaction: Decimal = d("-0.004000"),
    observed_price_reaction: Decimal = d("-0.003000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchOilInventorySurpriseDigestInputRow:
    return MarketResearchOilInventorySurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        inventory_report_key=inventory_report_key,
        inventory_report_family=inventory_report_family,
        inventory_report_reference=inventory_report_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_change_barrels=forecast_change_barrels,
        actual_change_barrels=actual_change_barrels,
        surprise_score=surprise_score,
        expected_price_reaction=expected_price_reaction,
        observed_price_reaction=observed_price_reaction,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchOilInventorySurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchOilInventorySurpriseDigestReport:
    return build_market_research_oil_inventory_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_oil_inventory_surprise_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.brent.api",
                condition_id="condition_brent_api",
                market_slug="brent-weekly-inventory",
                inventory_report_key="api.weekly.crude",
                inventory_report_family="api",
                inventory_report_reference="https://vendor.example/oil?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1"),
                forecast_change_barrels=d("-500000.000000"),
                actual_change_barrels=d("2500000.000000"),
                surprise_score=d("0.060000"),
                expected_price_reaction=d("-0.012000"),
                observed_price_reaction=d("0.018000"),
            ),
            input_row(
                "research.wti.eia",
                condition_id="condition_wti_eia",
                market_slug="wti-weekly-inventory",
                inventory_report_key="eia.weekly.petroleum",
                inventory_report_family="eia",
                inventory_report_reference="public-eia-calendar",
                released_at=GENERATED_AT - timedelta(minutes=40),
                acknowledged_at=GENERATED_AT - timedelta(minutes=35),
                source_count=d("3"),
                forecast_change_barrels=d("1000000.000000"),
                actual_change_barrels=d("2500000.000000"),
                surprise_score=d("0.020000"),
                expected_price_reaction=d("-0.004000"),
                observed_price_reaction=d("-0.003000"),
            ),
            input_row(
                "research.diesel.distillate",
                condition_id="condition_diesel_distillate",
                market_slug="diesel-distillate-draw",
                inventory_report_key="eia.distillate",
                inventory_report_family="distillate",
                inventory_report_reference="private-inventory-feed",
                released_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("2"),
                forecast_change_barrels=d("500000.000000"),
                actual_change_barrels=d("-2500000.000000"),
                surprise_score=d("0.070000"),
                expected_price_reaction=d("0.020000"),
                observed_price_reaction=d("0.025000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_OIL_INVENTORY_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_oil_inventory_surprise_digest"
    )
    assert summary.inventory_report_count == d("3")
    assert summary.ready_report_count == d("1")
    assert summary.watch_report_count == d("1")
    assert summary.blocked_report_count == d("1")
    assert summary.material_surprise_count == d("2")
    assert summary.stale_release_count == d("2")
    assert summary.thin_source_count == d("1")
    assert summary.missing_acknowledgement_count == d("1")
    assert summary.slow_acknowledgement_count == d("1")
    assert summary.contrary_price_reaction_count == d("1")
    assert summary.average_surprise_score == d("0.050000")
    assert summary.max_release_age_seconds == d("18000.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.market_slug, row.inventory_report_key) for row in summary.rows) == (
        ("diesel-distillate-draw", "eia.distillate"),
        ("brent-weekly-inventory", "api.weekly.crude"),
        ("wti-weekly-inventory", "eia.weekly.petroleum"),
    )

    distillate = summary.rows[0]
    assert distillate.surprise_status == "blocked"
    assert distillate.release_age_seconds == d("18000.000000")
    assert distillate.acknowledgement_lag_seconds is None
    assert distillate.inventory_surprise_barrels == d("-3000000.000000")
    assert distillate.redacted_inventory_report_reference == "sha256:5a6a2f178458"
    assert distillate.reason_codes == (
        "market_research_oil_inventory_surprise_digest_material_surprise",
        "market_research_oil_inventory_surprise_digest_missing_acknowledgement",
        "market_research_oil_inventory_surprise_digest_stale_release",
    )

    api = summary.rows[1]
    assert api.surprise_status == "watch"
    assert api.release_age_seconds == d("10800.000000")
    assert api.acknowledgement_lag_seconds == d("6000.000000")
    assert api.inventory_surprise_barrels == d("3000000.000000")
    assert api.redacted_inventory_report_reference == "sha256:83404e56ec4f"
    assert api.reason_codes == (
        "market_research_oil_inventory_surprise_digest_material_surprise",
        "market_research_oil_inventory_surprise_digest_contrary_price_reaction",
        "market_research_oil_inventory_surprise_digest_slow_acknowledgement",
        "market_research_oil_inventory_surprise_digest_stale_release",
        "market_research_oil_inventory_surprise_digest_thin_sources",
    )

    eia = summary.rows[2]
    assert eia.surprise_status == "ready"
    assert eia.release_age_seconds == d("2400.000000")
    assert eia.acknowledgement_lag_seconds == d("300.000000")
    assert eia.inventory_surprise_barrels == d("1500000.000000")
    assert eia.redacted_inventory_report_reference == "public-eia-calendar"
    assert eia.reason_codes == (
        "market_research_oil_inventory_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code="market_research_oil_inventory_surprise_digest_material_surprise",
            count=d("2"),
            report_ratio=d("0.666667"),
        ),
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code="market_research_oil_inventory_surprise_digest_stale_release",
            count=d("2"),
            report_ratio=d("0.666667"),
        ),
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_oil_inventory_surprise_digest_"
                "contrary_price_reaction"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_oil_inventory_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code="market_research_oil_inventory_surprise_digest_ready",
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_oil_inventory_surprise_digest_"
                "slow_acknowledgement"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code="market_research_oil_inventory_surprise_digest_thin_sources",
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-inventory-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_oil_inventory_surprise_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_oil_inventory_surprise_digest"
    )
    assert summary.inventory_report_count == ZERO
    assert summary.ready_report_count == ZERO
    assert summary.watch_report_count == ZERO
    assert summary.blocked_report_count == ZERO
    assert summary.average_surprise_score == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code="market_research_oil_inventory_surprise_digest_no_inputs",
            count=d("1.000000"),
            report_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_oil_inventory_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_oil_inventory_surprise_payload_uses_decimal_strings_and_omits_sensitive_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_oil_inventory_surprise_digest_payload(summary)

    assert payload["inventory_report_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'inventory_report_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_oil_inventory_surprise_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchOilInventorySurpriseDigestConfig)
    assert is_dataclass(MarketResearchOilInventorySurpriseDigestInputRow)
    assert is_dataclass(MarketResearchOilInventorySurpriseDigestRow)
    assert is_dataclass(MarketResearchOilInventorySurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchOilInventorySurpriseDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("3")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("oil-inventory-surprise-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="material_surprise_threshold_barrels"):
        config(material_surprise_threshold_barrels=Decimal("NaN"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=_DecimalSubclass("1800"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="WTI Weekly Inventory")
    with pytest.raises(ValueError, match="inventory_report_family"):
        input_row(inventory_report_family="broker_feed")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="released_at"):
        input_row(
            released_at=datetime(
                2026,
                7,
                3,
                14,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_change_barrels"):
        input_row(forecast_change_barrels=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_change_barrels"):
        input_row(actual_change_barrels=_DecimalSubclass("2500000"))
    with pytest.raises(ValueError, match="surprise_score"):
        input_row(surprise_score=d("1.000001"))
    with pytest.raises(ValueError, match="expected_price_reaction"):
        input_row(expected_price_reaction=d("1.000001"))
    with pytest.raises(ValueError, match="observed_price_reaction"):
        input_row(observed_price_reaction=d("-1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_oil_inventory_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_oil_inventory_surprise_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_oil_inventory_surprise_digest(
            (),
            config=config(),
            generated_at=datetime(
                2026,
                7,
                3,
                14,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_public_oil_inventory_surprise_records_reject_subclassing() -> None:
    public_types = (
        MarketResearchOilInventorySurpriseDigestConfig,
        MarketResearchOilInventorySurpriseDigestInputRow,
        MarketResearchOilInventorySurpriseDigestRow,
        MarketResearchOilInventorySurpriseDigestReasonCodeCount,
        MarketResearchOilInventorySurpriseDigestReport,
    )
    for public_type in public_types:
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsafe{public_type.__name__}", (public_type,), {})


def test_oil_inventory_surprise_rejects_false_flags_on_public_records() -> None:
    summary = report((input_row(),))

    with pytest.raises(ValueError, match="config report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="config readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="input row report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="input row readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="row report_only"):
        replace(summary.rows[0], report_only=False)
    with pytest.raises(ValueError, match="reason count readonly"):
        replace(summary.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only"):
        replace(summary, paper_only=False)


def test_oil_inventory_surprise_rejects_subquantum_boundary_violations() -> None:
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=d("-0.0000004"))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=d("2.0000004"))
    with pytest.raises(ValueError, match="surprise_score"):
        input_row(surprise_score=d("1.0000004"))
    with pytest.raises(ValueError, match="expected_price_reaction"):
        input_row(expected_price_reaction=d("-1.0000004"))


def test_oil_inventory_surprise_canonicalizes_signed_zero_numerics() -> None:
    summary = report(
        (
            input_row(
                source_count=d("-0.000000"),
                forecast_change_barrels=d("-0.000000"),
                actual_change_barrels=d("-0.000000"),
                surprise_score=d("-0.000000"),
                expected_price_reaction=d("-0.000000"),
                observed_price_reaction=d("-0.000000"),
            ),
        ),
    )

    payload = market_research_oil_inventory_surprise_digest_payload(summary)

    assert payload["rows"][0]["source_count"] == "0.000000"
    assert payload["rows"][0]["forecast_change_barrels"] == "0.000000"
    assert payload["rows"][0]["actual_change_barrels"] == "0.000000"
    assert payload["rows"][0]["surprise_score"] == "0.000000"
    assert payload["rows"][0]["expected_price_reaction"] == "0.000000"
    assert payload["rows"][0]["observed_price_reaction"] == "0.000000"


def test_report_and_row_consistency_rejects_incoherent_manual_constructors() -> None:
    ready = report((input_row(),)).rows[0]
    multi_reason_summary = report(
        (
            input_row(
                "research.multi",
                inventory_report_key="multi.reason",
                acknowledged_at=None,
                released_at=GENERATED_AT - timedelta(hours=3),
                forecast_change_barrels=d("0.000000"),
                actual_change_barrels=d("3000000.000000"),
            ),
        ),
    )
    multi_reason_row = multi_reason_summary.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_oil_inventory_surprise_digest_ready",
                "market_research_oil_inventory_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="surprise_status"):
        replace(ready, surprise_status="blocked")
    with pytest.raises(ValueError, match="inventory_surprise_barrels"):
        replace(ready, inventory_surprise_barrels=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_inventory_report_reference"):
        replace(
            ready,
            redacted_inventory_report_reference="https://host?token=secret",
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason_row,
            reason_codes=tuple(reversed(multi_reason_row.reason_codes)),
        )

    with pytest.raises(ValueError, match="count"):
        MarketResearchOilInventorySurpriseDigestReasonCodeCount(
            reason_code="market_research_oil_inventory_surprise_digest_no_inputs",
            count=ZERO,
            report_ratio=ZERO,
        )

    with pytest.raises(ValueError, match="ready_report_count"):
        replace(report((input_row(),)), ready_report_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        replace(
            report(
                (
                    input_row("research.z", inventory_report_key="z.report"),
                    input_row(),
                ),
            ),
            rows=tuple(
                reversed(
                    report(
                        (
                            input_row("research.z", inventory_report_key="z.report"),
                            input_row(),
                        ),
                    ).rows,
                ),
            ),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            multi_reason_summary,
            reason_code_counts=tuple(reversed(multi_reason_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason_summary,
            reason_codes=tuple(reversed(multi_reason_summary.reason_codes)),
        )


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_oil_inventory_surprise_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    assert "persist" not in source.lower()
    assert "database" not in source.lower()
    assert "advice" not in source.lower()


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "barrels",
        "count",
        "lag",
        "ratio",
        "reaction",
        "score",
    )
    for field in value.__dataclass_fields__.values():
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
