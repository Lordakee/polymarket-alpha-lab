from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_housing_starts_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_HOUSING_STARTS_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchHousingStartsSurpriseDigestConfig,
    MarketResearchHousingStartsSurpriseDigestInputRow,
    MarketResearchHousingStartsSurpriseDigestReasonCodeCount,
    MarketResearchHousingStartsSurpriseDigestReport,
    MarketResearchHousingStartsSurpriseDigestRow,
    build_market_research_housing_starts_surprise_digest,
    market_research_housing_starts_surprise_digest_payload,
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


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchHousingStartsSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_HOUSING_STARTS_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold_units": d("50000.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchHousingStartsSurpriseDigestConfig(**values)


def input_row(
    research_key: str = "research.housing.starts",
    *,
    condition_id: str = "condition_housing_starts",
    market_slug: str = "us-housing-starts-above-consensus",
    housing_report_key: str = "census.housing.starts",
    housing_report_family: str = "housing",
    housing_report_reference: str = "public-census-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("2"),
    forecast_starts_units: Decimal = d("1350000.000000"),
    actual_starts_units: Decimal = d("1375000.000000"),
    surprise_score: Decimal = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchHousingStartsSurpriseDigestInputRow:
    return MarketResearchHousingStartsSurpriseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        housing_report_key=housing_report_key,
        housing_report_family=housing_report_family,
        housing_report_reference=housing_report_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_starts_units=forecast_starts_units,
        actual_starts_units=actual_starts_units,
        surprise_score=surprise_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchHousingStartsSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchHousingStartsSurpriseDigestReport:
    return build_market_research_housing_starts_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_housing_starts_surprise_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.housing.south.starts",
                condition_id="condition_south_starts",
                market_slug="south-housing-starts-miss",
                housing_report_key="census.housing.south",
                housing_report_family="regional",
                housing_report_reference="https://vendor.example/housing?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1"),
                forecast_starts_units=d("750000.000000"),
                actual_starts_units=d("625000.000000"),
                surprise_score=d("0.090000"),
            ),
            input_row(
                "research.housing.starts",
                condition_id="condition_housing_starts",
                market_slug="us-housing-starts-above-consensus",
                housing_report_key="census.housing.starts",
                housing_report_family="headline",
                housing_report_reference="public-census-calendar",
                released_at=GENERATED_AT - timedelta(minutes=40),
                acknowledged_at=GENERATED_AT - timedelta(minutes=35),
                source_count=d("3"),
                forecast_starts_units=d("1350000.000000"),
                actual_starts_units=d("1375000.000000"),
                surprise_score=d("0.020000"),
            ),
            input_row(
                "research.housing.multi.starts",
                condition_id="condition_multi_starts",
                market_slug="multifamily-starts-drop",
                housing_report_key="census.housing.multifamily",
                housing_report_family="multifamily",
                housing_report_reference="private-housing-feed",
                released_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_count=d("2"),
                forecast_starts_units=d("525000.000000"),
                actual_starts_units=d("430000.000000"),
                surprise_score=d("0.070000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_HOUSING_STARTS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_housing_starts_surprise_digest"
    )
    assert summary.housing_report_count == d("3")
    assert summary.ready_report_count == d("1")
    assert summary.watch_report_count == d("1")
    assert summary.blocked_report_count == d("1")
    assert summary.material_surprise_count == d("2")
    assert summary.stale_release_count == d("2")
    assert summary.thin_source_count == d("1")
    assert summary.missing_acknowledgement_count == d("1")
    assert summary.slow_acknowledgement_count == d("1")
    assert summary.average_surprise_score == d("0.060000")
    assert summary.max_release_age_seconds == d("18000.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.market_slug, row.housing_report_key) for row in summary.rows) == (
        ("multifamily-starts-drop", "census.housing.multifamily"),
        ("south-housing-starts-miss", "census.housing.south"),
        ("us-housing-starts-above-consensus", "census.housing.starts"),
    )

    multifamily = summary.rows[0]
    assert multifamily.surprise_status == "blocked"
    assert multifamily.release_age_seconds == d("18000.000000")
    assert multifamily.acknowledgement_lag_seconds is None
    assert multifamily.housing_starts_surprise_units == d("-95000.000000")
    assert multifamily.redacted_housing_report_reference == "sha256:4333e5695713"
    assert multifamily.reason_codes == (
        "market_research_housing_starts_surprise_digest_material_surprise",
        "market_research_housing_starts_surprise_digest_missing_acknowledgement",
        "market_research_housing_starts_surprise_digest_stale_release",
    )

    south = summary.rows[1]
    assert south.surprise_status == "watch"
    assert south.release_age_seconds == d("10800.000000")
    assert south.acknowledgement_lag_seconds == d("6000.000000")
    assert south.housing_starts_surprise_units == d("-125000.000000")
    assert south.redacted_housing_report_reference == "sha256:dbb4a248b56e"
    assert south.reason_codes == (
        "market_research_housing_starts_surprise_digest_material_surprise",
        "market_research_housing_starts_surprise_digest_slow_acknowledgement",
        "market_research_housing_starts_surprise_digest_stale_release",
        "market_research_housing_starts_surprise_digest_thin_sources",
    )

    headline = summary.rows[2]
    assert headline.surprise_status == "ready"
    assert headline.release_age_seconds == d("2400.000000")
    assert headline.acknowledgement_lag_seconds == d("300.000000")
    assert headline.housing_starts_surprise_units == d("25000.000000")
    assert headline.redacted_housing_report_reference == "public-census-calendar"
    assert headline.reason_codes == (
        "market_research_housing_starts_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code="market_research_housing_starts_surprise_digest_material_surprise",
            count=d("2"),
            report_ratio=d("0.666667"),
        ),
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code="market_research_housing_starts_surprise_digest_stale_release",
            count=d("2"),
            report_ratio=d("0.666667"),
        ),
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_housing_starts_surprise_digest_"
                "missing_acknowledgement"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code="market_research_housing_starts_surprise_digest_ready",
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_housing_starts_surprise_digest_"
                "slow_acknowledgement"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code="market_research_housing_starts_surprise_digest_thin_sources",
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
        "private-housing-feed",
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


def test_empty_housing_starts_surprise_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_housing_starts_surprise_digest"
    )
    assert summary.housing_report_count == ZERO
    assert summary.ready_report_count == ZERO
    assert summary.watch_report_count == ZERO
    assert summary.blocked_report_count == ZERO
    assert summary.average_surprise_score == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchHousingStartsSurpriseDigestReasonCodeCount(
            reason_code="market_research_housing_starts_surprise_digest_no_inputs",
            count=d("1.000000"),
            report_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_housing_starts_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_housing_starts_surprise_digest_payload_uses_decimal_strings_and_omits_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_housing_starts_surprise_digest_payload(summary)

    assert payload["housing_report_count"] == "1.000000"
    assert payload["average_surprise_score"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'housing_report_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_housing_starts_surprise_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchHousingStartsSurpriseDigestConfig)
    assert is_dataclass(MarketResearchHousingStartsSurpriseDigestInputRow)
    assert is_dataclass(MarketResearchHousingStartsSurpriseDigestRow)
    assert is_dataclass(MarketResearchHousingStartsSurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchHousingStartsSurpriseDigestReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("3")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("housing-starts-surprise-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="material_surprise_threshold_units"):
        config(material_surprise_threshold_units=_DecimalSubclass("50000"))
    with pytest.raises(ValueError, match="max_acknowledgement_lag_seconds"):
        config(max_acknowledgement_lag_seconds=Decimal("NaN"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="bad slug")
    with pytest.raises(ValueError, match="housing_report_family"):
        input_row(housing_report_family="broker_feed")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 3, 14, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_starts_units"):
        input_row(forecast_starts_units=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_starts_units"):
        input_row(actual_starts_units=_DecimalSubclass("1375000.000000"))
    with pytest.raises(ValueError, match="surprise_score"):
        input_row(surprise_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_housing_starts_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_housing_starts_surprise_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_false_hard_flags_are_rejected_on_every_public_record() -> None:
    summary = report((input_row(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    for field_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=f"config {field_name} must be True"):
            config(**{field_name: False})
        with pytest.raises(ValueError, match=f"input row {field_name} must be True"):
            input_row(**{field_name: False})
        with pytest.raises(ValueError, match=f"row {field_name} must be True"):
            replace(row, **{field_name: False})
        with pytest.raises(ValueError, match=f"reason count {field_name} must be True"):
            replace(reason_count, **{field_name: False})
        with pytest.raises(ValueError, match=f"report {field_name} must be True"):
            replace(summary, **{field_name: False})


def test_report_and_row_consistency_rejects_incoherent_manual_constructors() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_housing_starts_surprise_digest_ready",
                "market_research_housing_starts_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="surprise_status"):
        replace(ready, surprise_status="blocked")
    with pytest.raises(ValueError, match="housing_starts_surprise_units"):
        replace(ready, housing_starts_surprise_units=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_housing_report_reference"):
        replace(ready, redacted_housing_report_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_report_count"):
        replace(report((input_row(),)), ready_report_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        two_row_report = report(
            (
                input_row("research.housing.z", housing_report_key="census.housing.z"),
                input_row(),
            ),
        )
        replace(two_row_report, rows=tuple(reversed(two_row_report.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((input_row(),))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_housing_starts_surprise_digest.py",
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
        "count",
        "delta",
        "lag",
        "ratio",
        "score",
        "units",
        "value",
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
