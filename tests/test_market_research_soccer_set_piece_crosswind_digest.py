from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_soccer_set_piece_crosswind_digest import (
    DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_CROSSWIND_DIGEST_CONFIG_VERSION,
    REDACTED_EVIDENCE_REF_VALUE,
    MarketResearchSoccerSetPieceCrosswindDigest,
    MarketResearchSoccerSetPieceCrosswindDigestConfig,
    MarketResearchSoccerSetPieceCrosswindDigestRow,
    MarketResearchSoccerSetPieceCrosswindInputRow,
    MarketResearchSoccerSetPieceCrosswindReasonCodeCount,
    build_market_research_soccer_set_piece_crosswind_digest,
    market_research_soccer_set_piece_crosswind_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
START_AT = datetime(2026, 7, 4, 21, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchSoccerSetPieceCrosswindDigestConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_CROSSWIND_DIGEST_CONFIG_VERSION
        ),
        "max_weather_age_seconds": d("3600.000000"),
        "min_crosswind_mph": d("15.000000"),
        "min_gust_wind_mph": d("25.000000"),
        "min_projected_set_piece_count": d("10.000000"),
    }
    values.update(overrides)
    return MarketResearchSoccerSetPieceCrosswindDigestConfig(**values)


def _row(
    market_id: str,
    *,
    event_id: str = "soccer-ars-che-20260704",
    market_family: str = "match-goals",
    scheduled_start_at: datetime = START_AT,
    weather_observed_at: datetime | None = None,
    venue_exposure: str = "open",
    projected_set_piece_count: Decimal = d("6.000000"),
    sustained_wind_mph: Decimal = d("8.000000"),
    crosswind_mph: Decimal = d("4.000000"),
    gust_wind_mph: Decimal = d("12.000000"),
    evidence_refs: tuple[str, ...] = ("public-weather-note",),
) -> MarketResearchSoccerSetPieceCrosswindInputRow:
    return MarketResearchSoccerSetPieceCrosswindInputRow(
        market_id=market_id,
        event_id=event_id,
        market_family=market_family,
        scheduled_start_at=scheduled_start_at,
        weather_observed_at=weather_observed_at
        or GENERATED_AT - timedelta(seconds=900),
        venue_exposure=venue_exposure,
        projected_set_piece_count=projected_set_piece_count,
        sustained_wind_mph=sustained_wind_mph,
        crosswind_mph=crosswind_mph,
        gust_wind_mph=gust_wind_mph,
        evidence_refs=evidence_refs,
    )


def test_digest_flags_high_risk_set_piece_crosswind_deterministically() -> None:
    pacific_weather_at = datetime(
        2026,
        7,
        4,
        10,
        45,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    digest = build_market_research_soccer_set_piece_crosswind_digest(
        (
            _row(
                "zeta",
                event_id="soccer-zeta",
                weather_observed_at=GENERATED_AT - timedelta(seconds=3601),
                evidence_refs=("zeta-note",),
            ),
            _row("clear", event_id="soccer-clear"),
            _row(
                "alpha",
                event_id="soccer-alpha",
                weather_observed_at=pacific_weather_at,
                projected_set_piece_count=d("12.000000"),
                sustained_wind_mph=d("17.000000"),
                crosswind_mph=d("19.000000"),
                gust_wind_mph=d("27.000000"),
                evidence_refs=(
                    "alpha-note",
                    "https://example.test/weather?api_key=abcd",
                ),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert digest == MarketResearchSoccerSetPieceCrosswindDigest(
        generated_at=GENERATED_AT,
        config_version=(
            DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_CROSSWIND_DIGEST_CONFIG_VERSION
        ),
        digest_status="blocked",
        market_count=d("3.000000"),
        input_row_count=d("3.000000"),
        pass_market_count=d("1.000000"),
        watch_market_count=d("1.000000"),
        blocked_market_count=d("1.000000"),
        stale_weather_count=d("1.000000"),
        evidence_gap_count=d("0.000000"),
        high_crosswind_market_count=d("1.000000"),
        gust_market_count=d("1.000000"),
        high_set_piece_volume_market_count=d("1.000000"),
        open_venue_market_count=d("1.000000"),
        max_weather_age_seconds=d("3601.000000"),
        max_crosswind_mph=d("19.000000"),
        max_gust_wind_mph=d("27.000000"),
        max_projected_set_piece_count=d("12.000000"),
        min_crosswind_mph=d("15.000000"),
        min_gust_wind_mph=d("25.000000"),
        min_projected_set_piece_count=d("10.000000"),
        rows=(
            MarketResearchSoccerSetPieceCrosswindDigestRow(
                market_id="alpha",
                event_id="soccer-alpha",
                market_family="match-goals",
                row_status="watch",
                scheduled_start_at=START_AT,
                weather_observed_at=datetime(2026, 7, 4, 17, 45, tzinfo=UTC),
                weather_age_seconds=d("900.000000"),
                venue_exposure="open",
                projected_set_piece_count=d("12.000000"),
                sustained_wind_mph=d("17.000000"),
                crosswind_mph=d("19.000000"),
                gust_wind_mph=d("27.000000"),
                evidence_ref_count=d("2.000000"),
                redacted_evidence_refs=(REDACTED_EVIDENCE_REF_VALUE, "alpha-note"),
                reason_codes=(
                    "soccer_set_piece_crosswind_high_crosswind",
                    "soccer_set_piece_crosswind_gust_risk",
                    "soccer_set_piece_crosswind_high_set_piece_volume",
                    "soccer_set_piece_crosswind_open_venue",
                ),
            ),
            MarketResearchSoccerSetPieceCrosswindDigestRow(
                market_id="clear",
                event_id="soccer-clear",
                market_family="match-goals",
                row_status="pass",
                scheduled_start_at=START_AT,
                weather_observed_at=GENERATED_AT - timedelta(seconds=900),
                weather_age_seconds=d("900.000000"),
                venue_exposure="open",
                projected_set_piece_count=d("6.000000"),
                sustained_wind_mph=d("8.000000"),
                crosswind_mph=d("4.000000"),
                gust_wind_mph=d("12.000000"),
                evidence_ref_count=d("1.000000"),
                redacted_evidence_refs=("public-weather-note",),
                reason_codes=("soccer_set_piece_crosswind_clear",),
            ),
            MarketResearchSoccerSetPieceCrosswindDigestRow(
                market_id="zeta",
                event_id="soccer-zeta",
                market_family="match-goals",
                row_status="blocked",
                scheduled_start_at=START_AT,
                weather_observed_at=GENERATED_AT - timedelta(seconds=3601),
                weather_age_seconds=d("3601.000000"),
                venue_exposure="open",
                projected_set_piece_count=d("6.000000"),
                sustained_wind_mph=d("8.000000"),
                crosswind_mph=d("4.000000"),
                gust_wind_mph=d("12.000000"),
                evidence_ref_count=d("1.000000"),
                redacted_evidence_refs=("zeta-note",),
                reason_codes=("soccer_set_piece_crosswind_stale_weather",),
            ),
        ),
        reason_code_counts=(
            MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
                reason_code="soccer_set_piece_crosswind_stale_weather",
                market_count=d("1.000000"),
            ),
            MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
                reason_code="soccer_set_piece_crosswind_high_crosswind",
                market_count=d("1.000000"),
            ),
            MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
                reason_code="soccer_set_piece_crosswind_gust_risk",
                market_count=d("1.000000"),
            ),
            MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
                reason_code="soccer_set_piece_crosswind_high_set_piece_volume",
                market_count=d("1.000000"),
            ),
            MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
                reason_code="soccer_set_piece_crosswind_open_venue",
                market_count=d("1.000000"),
            ),
        ),
        reason_codes=(
            "soccer_set_piece_crosswind_stale_weather",
            "soccer_set_piece_crosswind_high_crosswind",
            "soccer_set_piece_crosswind_gust_risk",
            "soccer_set_piece_crosswind_high_set_piece_volume",
            "soccer_set_piece_crosswind_open_venue",
        ),
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_empty_input_returns_blocked_report_only_reason() -> None:
    digest = build_market_research_soccer_set_piece_crosswind_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert digest.digest_status == "blocked"
    assert digest.market_count == d("0.000000")
    assert digest.input_row_count == d("0.000000")
    assert digest.rows == ()
    assert digest.reason_codes == ("soccer_set_piece_crosswind_rows_missing",)
    assert digest.reason_code_counts == (
        MarketResearchSoccerSetPieceCrosswindReasonCodeCount(
            reason_code="soccer_set_piece_crosswind_rows_missing",
            market_count=d("0.000000"),
        ),
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_non_default_thresholds_can_suppress_watch_risk() -> None:
    digest = build_market_research_soccer_set_piece_crosswind_digest(
        (
            _row(
                "alpha",
                event_id="soccer-alpha",
                projected_set_piece_count=d("12.000000"),
                sustained_wind_mph=d("17.000000"),
                crosswind_mph=d("19.000000"),
                gust_wind_mph=d("27.000000"),
            ),
        ),
        config=_config(
            min_crosswind_mph=d("22.000000"),
            min_gust_wind_mph=d("31.000000"),
            min_projected_set_piece_count=d("15.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert digest.digest_status == "pass"
    assert digest.pass_market_count == d("1.000000")
    assert digest.watch_market_count == d("0.000000")
    assert digest.high_crosswind_market_count == d("0.000000")
    assert digest.gust_market_count == d("0.000000")
    assert digest.high_set_piece_volume_market_count == d("0.000000")
    assert digest.rows[0].reason_codes == ("soccer_set_piece_crosswind_clear",)
    assert digest.min_crosswind_mph == d("22.000000")
    assert digest.min_gust_wind_mph == d("31.000000")
    assert digest.min_projected_set_piece_count == d("15.000000")


def test_payload_is_json_ready_decimal_only_and_redacts_sensitive_refs() -> None:
    digest = build_market_research_soccer_set_piece_crosswind_digest(
        (
            _row(
                "alpha",
                event_id="soccer-alpha",
                evidence_refs=("public-ref", "https://example.test/path?token=abcd"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_research_soccer_set_piece_crosswind_digest_payload(digest)
    payload_text = repr(payload).lower()

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["rows"][0]["weather_age_seconds"] == "900.000000"
    assert payload["rows"][0]["redacted_evidence_refs"] == [
        REDACTED_EVIDENCE_REF_VALUE,
        "public-ref",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload, allow_nan=False, sort_keys=True)) == payload
    _assert_no_floats(payload)
    assert "token" not in payload_text
    assert "abcd" not in payload_text
    for forbidden in (
        "trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
    ):
        assert forbidden not in payload_text


def test_validates_frozen_decimal_datetime_flags_and_reason_contracts() -> None:
    row = _row("alpha", event_id="soccer-alpha")
    config = _config()
    digest = build_market_research_soccer_set_piece_crosswind_digest(
        (row,),
        config=config,
        generated_at=GENERATED_AT,
    )

    for value in (config, row, digest, digest.rows[0], digest.reason_code_counts[0]):
        assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        row.market_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.digest_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_weather_age_seconds"):
        _config(max_weather_age_seconds=2)
    with pytest.raises(ValueError, match="min_crosswind_mph"):
        _config(min_crosswind_mph=_DecimalSubclass("12.000000"))
    with pytest.raises(ValueError, match="min_gust_wind_mph"):
        _config(min_gust_wind_mph=Decimal("NaN"))
    with pytest.raises(ValueError, match="scheduled_start_at"):
        _row("naive-start", scheduled_start_at=datetime(2026, 7, 4, 21, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_soccer_set_piece_crosswind_digest(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 4, 18, 0),
        )
    with pytest.raises(ValueError, match="market_id"):
        _row("wallet-feed")
    with pytest.raises(ValueError, match="evidence_refs"):
        _row("blank-ref", evidence_refs=("",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)
    with pytest.raises(ValueError, match="future"):
        build_market_research_soccer_set_piece_crosswind_digest(
            (
                _row(
                    "future",
                    weather_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="input rows"):
        build_market_research_soccer_set_piece_crosswind_digest(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="gust_wind_mph"):
        _row(
            "bad-gust",
            sustained_wind_mph=d("20.000000"),
            gust_wind_mph=d("19.000000"),
        )
    with pytest.raises(ValueError, match="row_status"):
        MarketResearchSoccerSetPieceCrosswindDigestRow(
            market_id="manual",
            event_id="soccer-manual",
            market_family="match-goals",
            row_status="pass",
            scheduled_start_at=START_AT,
            weather_observed_at=GENERATED_AT - timedelta(seconds=60),
            weather_age_seconds=d("60.000000"),
            venue_exposure="open",
            projected_set_piece_count=d("12.000000"),
            sustained_wind_mph=d("17.000000"),
            crosswind_mph=d("19.000000"),
            gust_wind_mph=d("27.000000"),
            evidence_ref_count=d("1.000000"),
            redacted_evidence_refs=("public",),
            reason_codes=("soccer_set_piece_crosswind_high_crosswind",),
        )


def test_public_numeric_fields_are_decimal_only() -> None:
    public_classes = (
        MarketResearchSoccerSetPieceCrosswindDigestConfig,
        MarketResearchSoccerSetPieceCrosswindInputRow,
        MarketResearchSoccerSetPieceCrosswindDigestRow,
        MarketResearchSoccerSetPieceCrosswindReasonCodeCount,
        MarketResearchSoccerSetPieceCrosswindDigest,
    )
    numeric_name_fragments = (
        "count",
        "mph",
        "seconds",
    )

    for cls in public_classes:
        for field in fields(cls):
            if field.name == "reason_code_counts":
                continue
            if any(fragment in field.name for fragment in numeric_name_fragments):
                assert field.type in (Decimal, "Decimal")


def test_module_scope_excludes_io_persistence_sensitive_surfaces_and_float_literals() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_set_piece_crosswind_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    for forbidden in (
        "trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
    ):
        assert forbidden not in lowered_source

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "write",
    }
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (called_names & forbidden_call_names)


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_floats(nested)
    if isinstance(value, list):
        for nested in value:
            _assert_no_floats(nested)
