from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_geopolitical_shipping_risk_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_source_count": d("2"),
        "watch_risk_threshold": d("0.250000"),
        "blocked_risk_threshold": d("0.500000"),
        "fresh_signal_max_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return module.MarketResearchGeopoliticalShippingRiskDigestConfig(**values)


def input_row(
    research_key: str = "risk-alpha",
    *,
    market_slug: str = "red-sea-shipping-risk-watch",
    route_key: str = "red-sea-suez",
    region_key: str = "mena",
    risk_signal_source: str = "maritime_bulletin",
    source_reference: str = "maritime-bulletin-red-sea-20260704",
    observed_at: datetime = datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
    acknowledged_at: datetime = datetime(2026, 7, 4, 10, 30, tzinfo=UTC),
    source_count: Decimal = d("3"),
    incident_count: Decimal = d("2"),
    reroute_probability: Decimal = d("0.620000"),
    port_delay_days: Decimal = d("4.500000"),
    market_probability: Decimal = d("0.390000"),
    implied_probability: Decimal = d("0.610000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchGeopoliticalShippingRiskDigestInputRow(
        research_key=research_key,
        market_slug=market_slug,
        route_key=route_key,
        region_key=region_key,
        risk_signal_source=risk_signal_source,
        source_reference=source_reference,
        observed_at=observed_at,
        acknowledged_at=acknowledged_at,
        source_count=source_count,
        incident_count=incident_count,
        reroute_probability=reroute_probability,
        port_delay_days=port_delay_days,
        market_probability=market_probability,
        implied_probability=implied_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_geopolitical_shipping_risk_digest(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def test_digest_summarizes_shipping_risk_with_deterministic_rows() -> None:
    module = api()

    digest_report = report(
        input_row(
            "risk-watch",
            market_slug="panama-canal-delay-watch",
            route_key="panama-canal",
            region_key="amer",
            source_count=d("2"),
            incident_count=d("1"),
            reroute_probability=d("0.300000"),
            port_delay_days=d("2.000000"),
            market_probability=d("0.410000"),
            implied_probability=d("0.310000"),
            observed_at=datetime(2026, 7, 4, 5, 0, tzinfo=timezone(timedelta(hours=-5))),
            acknowledged_at=datetime(
                2026,
                7,
                4,
                5,
                10,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
        ),
        input_row(
            "risk-ready",
            market_slug="north-atlantic-lane-normal",
            route_key="north-atlantic",
            region_key="atlantic",
            source_count=d("4"),
            incident_count=d("0"),
            reroute_probability=d("0.050000"),
            port_delay_days=d("0.500000"),
            market_probability=d("0.200000"),
            implied_probability=d("0.090000"),
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 4, 11, 40, tzinfo=UTC),
        ),
        input_row(
            "risk-blocked",
            market_slug="red-sea-shipping-risk-blocked",
            route_key="red-sea-suez",
            region_key="mena",
            source_count=d("1"),
            incident_count=d("3"),
            reroute_probability=d("0.740000"),
            port_delay_days=d("6.000000"),
            market_probability=d("0.350000"),
            implied_probability=d("0.720000"),
            observed_at=datetime(2026, 7, 3, 8, 0, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
        ),
    )

    assert isinstance(
        digest_report,
        module.MarketResearchGeopoliticalShippingRiskDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-geopolitical-shipping-risk-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.next_step == (
        "block_report_only_market_research_geopolitical_shipping_risk_digest"
    )
    assert digest_report.route_count == d("3")
    assert digest_report.ready_route_count == d("1")
    assert digest_report.watch_route_count == d("1")
    assert digest_report.blocked_route_count == d("1")
    assert digest_report.thin_source_count == d("1")
    assert digest_report.stale_signal_count == d("1")
    assert digest_report.probability_discount_count == d("1")
    assert digest_report.max_risk_score == d("0.766786")
    assert digest_report.average_risk_score == d("0.443095")
    assert digest_report.max_signal_age_seconds == d("100800.000000")
    assert digest_report.average_port_delay_days == d("2.833333")
    assert digest_report.reason_codes == (
        "market_research_geopolitical_shipping_risk_digest_blocked_risk",
        "market_research_geopolitical_shipping_risk_digest_watch_risk",
        "market_research_geopolitical_shipping_risk_digest_probability_discount",
        "market_research_geopolitical_shipping_risk_digest_stale_signal",
        "market_research_geopolitical_shipping_risk_digest_thin_sources",
        "market_research_geopolitical_shipping_risk_digest_ready",
    )
    assert digest_report.reason_code_counts == (
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code="market_research_geopolitical_shipping_risk_digest_blocked_risk",
            count=d("1"),
            route_ratio=d("0.333333"),
        ),
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code="market_research_geopolitical_shipping_risk_digest_watch_risk",
            count=d("1"),
            route_ratio=d("0.333333"),
        ),
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code=(
                "market_research_geopolitical_shipping_risk_digest_"
                "probability_discount"
            ),
            count=d("1"),
            route_ratio=d("0.333333"),
        ),
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code="market_research_geopolitical_shipping_risk_digest_stale_signal",
            count=d("1"),
            route_ratio=d("0.333333"),
        ),
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code="market_research_geopolitical_shipping_risk_digest_thin_sources",
            count=d("1"),
            route_ratio=d("0.333333"),
        ),
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code="market_research_geopolitical_shipping_risk_digest_ready",
            count=d("1"),
            route_ratio=d("0.333333"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.research_key for row in digest_report.rows) == (
        "risk-blocked",
        "risk-watch",
        "risk-ready",
    )
    blocked, watch, ready = digest_report.rows
    assert blocked.risk_status == "blocked"
    assert blocked.risk_score == d("0.766786")
    assert blocked.signal_age_seconds == d("100800.000000")
    assert blocked.reason_codes == (
        "market_research_geopolitical_shipping_risk_digest_blocked_risk",
        "market_research_geopolitical_shipping_risk_digest_probability_discount",
        "market_research_geopolitical_shipping_risk_digest_stale_signal",
        "market_research_geopolitical_shipping_risk_digest_thin_sources",
    )
    assert blocked.redacted_source_reference.startswith("ref:")
    assert "20260704" not in blocked.redacted_source_reference
    assert watch.risk_status == "watch"
    assert watch.observed_at == datetime(2026, 7, 4, 10, 0, tzinfo=UTC)
    assert watch.reason_codes == (
        "market_research_geopolitical_shipping_risk_digest_watch_risk",
    )
    assert ready.risk_status == "ready"
    assert ready.reason_codes == (
        "market_research_geopolitical_shipping_risk_digest_ready",
    )


def test_empty_digest_is_report_only_blocked_and_zeroed() -> None:
    module = api()

    digest_report = report()

    assert digest_report.digest_status == "blocked"
    assert digest_report.next_step == (
        "block_report_only_market_research_geopolitical_shipping_risk_digest"
    )
    assert digest_report.route_count == d("0")
    assert digest_report.ready_route_count == d("0")
    assert digest_report.watch_route_count == d("0")
    assert digest_report.blocked_route_count == d("0")
    assert digest_report.thin_source_count == d("0")
    assert digest_report.stale_signal_count == d("0")
    assert digest_report.probability_discount_count == d("0")
    assert digest_report.max_risk_score == d("0.000000")
    assert digest_report.average_risk_score == d("0.000000")
    assert digest_report.max_signal_age_seconds == d("0.000000")
    assert digest_report.average_port_delay_days == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "market_research_geopolitical_shipping_risk_digest_no_inputs",
    )
    assert digest_report.reason_code_counts == (
        module.MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code="market_research_geopolitical_shipping_risk_digest_no_inputs",
            count=d("1"),
            route_ratio=d("1.000000"),
        ),
    )


def test_validates_decimal_datetime_flags_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("bad-version"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.5"))
    with pytest.raises(ValueError, match="watch_risk_threshold"):
        config(watch_risk_threshold=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocked_risk_threshold"):
        config(blocked_risk_threshold=d("0.200000"))
    with pytest.raises(ValueError, match="research_key"):
        input_row("bad key")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 4, 10, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 4, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="incident_count"):
        input_row(incident_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="reroute_probability"):
        input_row(reroute_probability=d("1.000001"))
    with pytest.raises(ValueError, match="port_delay_days"):
        input_row(port_delay_days=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="config report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="config readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_market_research_geopolitical_shipping_risk_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report(object())
    with pytest.raises(ValueError, match="duplicate"):
        report(input_row("dupe"), input_row("dupe"))

    frozen_config = config()
    frozen_input = input_row("frozen-input")
    frozen_report = report(input_row("frozen-report"))
    frozen = frozen_report.rows[0]
    frozen_reason_count = frozen_report.reason_code_counts[0]
    with pytest.raises(FrozenInstanceError):
        frozen_config.min_source_count = d("3")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_input.research_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen.risk_score = d("0.1")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_reason_count.count = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_report.digest_status = "ready"  # type: ignore[misc]

    flag_report = report(input_row("flag-report"))
    flag_row = flag_report.rows[0]
    flag_reason_count = flag_report.reason_code_counts[0]
    with pytest.raises(ValueError, match="row paper_only"):
        replace(flag_row, paper_only=False)
    with pytest.raises(ValueError, match="row report_only"):
        replace(flag_row, report_only=False)
    with pytest.raises(ValueError, match="row readonly"):
        replace(flag_row, readonly=False)
    with pytest.raises(ValueError, match="reason count paper_only"):
        replace(flag_reason_count, paper_only=False)
    with pytest.raises(ValueError, match="reason count report_only"):
        replace(flag_reason_count, report_only=False)
    with pytest.raises(ValueError, match="reason count readonly"):
        replace(flag_reason_count, readonly=False)
    with pytest.raises(ValueError, match="report paper_only"):
        replace(flag_report, paper_only=False)
    with pytest.raises(ValueError, match="report report_only"):
        replace(flag_report, report_only=False)
    with pytest.raises(ValueError, match="report readonly"):
        replace(flag_report, readonly=False)


def test_payload_uses_decimal_strings_and_no_unsafe_public_values() -> None:
    module = api()
    digest_report = report(input_row("risk-json"))

    payload = module.market_research_geopolitical_shipping_risk_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["route_count"] == "1.000000"
    assert payload["average_risk_score"] == "0.678712"
    assert payload["rows"][0]["risk_score"] == "0.678712"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T10:00:00+00:00"
    assert "maritime-bulletin" not in repr(payload)

    _assert_no_float_int_decimal_datetime(payload)
    asdict_text = repr(asdict(digest_report)).lower()
    for token in ("wallet", "auth", "order", "cancel", "private", "secret"):
        assert token not in asdict_text

    for value in (
        config(),
        input_row("typed"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            field_value = getattr(value, field.name)
            if _is_public_numeric_field(field.name):
                assert type(field_value) is Decimal, field.name


def test_module_scope_excludes_forbidden_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_geopolitical_shipping_risk_digest.py",
    ).read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    source_lower = source.lower()
    for token in (
        "live trading",
        "wallet",
        "auth",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "database",
        "network",
        "secret",
        "private_key",
        "api_key",
    ):
        assert token not in source_lower


def _assert_no_float_int_decimal_datetime(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_int_decimal_datetime(child)
        return
    if isinstance(value, list):
        for child in value:
            _assert_no_float_int_decimal_datetime(child)
        return
    assert not isinstance(value, (Decimal, datetime, float, int))


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
        or field_name.endswith("_seconds")
        or field_name.endswith("_days")
        or field_name.endswith("_probability")
    )
