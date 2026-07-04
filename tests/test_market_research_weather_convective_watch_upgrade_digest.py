from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_weather_convective_watch_upgrade_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_weather_convective_watch_upgrade_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "weather-convective-watch-upgrade-digest-v1",
        "max_source_age_seconds": Decimal("900.000000"),
        "watch_upgrade_pressure_threshold": Decimal("0.500000"),
        "blocked_upgrade_pressure_threshold": Decimal("0.750000"),
        "source_quorum_minimum": Decimal("2.000000"),
        "cape_shear_watch_threshold": Decimal("0.600000"),
        "model_agreement_watch_threshold": Decimal("0.650000"),
        "short_warning_lead_time_minutes": Decimal("60.000000"),
        "population_exposure_watch_threshold": Decimal("0.650000"),
        "airport_exposure_watch_threshold": Decimal("0.500000"),
    }
    values.update(overrides)
    return module.ConvectiveWatchUpgradeDigestConfig(**values)


def observation(
    event_id: str = "ok-tornado-watch-upgrade",
    *,
    market_slug: str = "will-oklahoma-tornado-watch-be-issued",
    market_category: str = "weather",
    region_id: str = "oklahoma-central",
    forecast_office: str = "OUN",
    target_watch_type: str = "tornado",
    source_reference: str = "spc-md-17",
    forecast_valid_at: datetime = GENERATED_AT + timedelta(minutes=30),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    cape_shear_composite: Decimal = Decimal("0.950000"),
    model_agreement_score: Decimal = Decimal("0.900000"),
    warning_lead_time_minutes: Decimal = Decimal("15.000000"),
    population_exposure_score: Decimal = Decimal("0.800000"),
    airport_exposure_score: Decimal = Decimal("0.750000"),
    source_quorum_count: Decimal = Decimal("3.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ConvectiveWatchUpgradeObservation(
        event_id=event_id,
        market_slug=market_slug,
        market_category=market_category,
        region_id=region_id,
        forecast_office=forecast_office,
        target_watch_type=target_watch_type,
        source_reference=source_reference,
        forecast_valid_at=forecast_valid_at,
        source_observed_at=source_observed_at,
        cape_shear_composite=cape_shear_composite,
        model_agreement_score=model_agreement_score,
        warning_lead_time_minutes=warning_lead_time_minutes,
        population_exposure_score=population_exposure_score,
        airport_exposure_score=airport_exposure_score,
        source_quorum_count=source_quorum_count,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    observations: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_market_research_weather_convective_watch_upgrade_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"public numeric payload must not contain float/int: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_builds_convective_watch_digest_with_threshold_sorting_counts_and_reasons() -> None:
    report = digest(
        (
            observation(
                "gamma-stale",
                market_slug="will-kansas-severe-thunderstorm-watch-expand",
                region_id="kansas-central",
                forecast_office="ICT",
                target_watch_type="tornado",
                source_observed_at=GENERATED_AT - timedelta(seconds=3600),
                cape_shear_composite=Decimal("0.100000"),
                model_agreement_score=Decimal("0.100000"),
                warning_lead_time_minutes=Decimal("120.000000"),
                population_exposure_score=Decimal("0.200000"),
                airport_exposure_score=Decimal("0.100000"),
                source_quorum_count=Decimal("2.000000"),
                upstream_reason_codes=("spc_mesoanalysis",),
            ),
            observation(
                "alpha-blocked",
                forecast_valid_at=datetime(
                    2026,
                    7,
                    4,
                    8,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                source_observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    58,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("radar_rotation", "mesoscale_discussion"),
            ),
            observation(
                "beta-watch",
                market_slug="will-illinois-severe-thunderstorm-watch-be-issued",
                region_id="illinois-north",
                forecast_office="LOT",
                target_watch_type="severe_thunderstorm",
                cape_shear_composite=Decimal("0.600000"),
                model_agreement_score=Decimal("0.700000"),
                warning_lead_time_minutes=Decimal("45.000000"),
                population_exposure_score=Decimal("0.500000"),
                airport_exposure_score=Decimal("0.200000"),
                source_quorum_count=Decimal("2.000000"),
            ),
            observation(
                "delta-quorum-low",
                market_slug="will-missouri-severe-thunderstorm-watch-expand",
                region_id="missouri-east",
                forecast_office="LSX",
                target_watch_type="severe_thunderstorm",
                cape_shear_composite=Decimal("0.400000"),
                model_agreement_score=Decimal("0.300000"),
                warning_lead_time_minutes=Decimal("90.000000"),
                population_exposure_score=Decimal("0.200000"),
                airport_exposure_score=Decimal("0.100000"),
                source_quorum_count=Decimal("1.000000"),
            ),
            observation(
                "epsilon-pass",
                market_slug="will-iowa-severe-thunderstorm-watch-be-issued",
                region_id="iowa-central",
                forecast_office="DMX",
                target_watch_type="severe_thunderstorm",
                cape_shear_composite=Decimal("0.200000"),
                model_agreement_score=Decimal("0.200000"),
                warning_lead_time_minutes=Decimal("90.000000"),
                population_exposure_score=Decimal("0.200000"),
                airport_exposure_score=Decimal("0.100000"),
                source_quorum_count=Decimal("2.000000"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.input_count == Decimal("5.000000")
    assert report.row_count == Decimal("5.000000")
    assert report.blocked_count == Decimal("3.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.source_quorum_low_count == Decimal("1.000000")
    assert report.tornado_watch_count == Decimal("2.000000")
    assert report.severe_thunderstorm_watch_count == Decimal("3.000000")
    assert report.max_risk_score == Decimal("0.872500")
    assert report.max_cape_shear_composite == Decimal("0.950000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.event_id, row.upgrade_status, row.risk_score)
        for row in report.rows
    ] == [
        ("alpha-blocked", "blocked", Decimal("0.872500")),
        ("delta-quorum-low", "blocked", Decimal("0.270000")),
        ("gamma-stale", "blocked", Decimal("0.190000")),
        ("beta-watch", "watch", Decimal("0.552500")),
        ("epsilon-pass", "pass", Decimal("0.240000")),
    ]

    blocked = report.rows[0]
    assert blocked.forecast_valid_at == datetime(2026, 7, 4, 12, 30, tzinfo=UTC)
    assert blocked.source_observed_at == datetime(2026, 7, 4, 11, 58, tzinfo=UTC)
    assert blocked.source_age_seconds == Decimal("120.000000")
    assert blocked.source_quorum_score == Decimal("1.000000")
    assert blocked.warning_lead_pressure == Decimal("0.750000")
    assert blocked.redacted_source_reference == "spc-md-17"
    assert blocked.reason_codes == (
        "convective_watch_airport_exposure",
        "convective_watch_cape_shear_threshold_met",
        "convective_watch_forecast_office_oun",
        "convective_watch_market_category_weather",
        "convective_watch_model_agreement",
        "convective_watch_population_exposure",
        "convective_watch_short_warning_lead_time",
        "convective_watch_source_fresh",
        "convective_watch_source_quorum_met",
        "convective_watch_type_tornado",
        "convective_watch_upgrade_pressure_blocked",
        "mesoscale_discussion",
        "radar_rotation",
    )

    quorum_low = report.rows[1]
    assert quorum_low.reason_codes == (
        "convective_watch_forecast_office_lsx",
        "convective_watch_market_category_weather",
        "convective_watch_source_fresh",
        "convective_watch_source_quorum_low",
        "convective_watch_type_severe_thunderstorm",
    )

    stale = report.rows[2]
    assert stale.source_age_seconds == Decimal("3600.000000")
    assert stale.reason_codes == (
        "convective_watch_forecast_office_ict",
        "convective_watch_market_category_weather",
        "convective_watch_source_quorum_met",
        "convective_watch_source_stale",
        "convective_watch_type_tornado",
        "spc_mesoanalysis",
    )

    counts_by_code = {
        item.reason_code: item.count for item in report.reason_code_counts
    }
    assert counts_by_code["convective_watch_source_fresh"] == Decimal("4.000000")
    assert counts_by_code["convective_watch_source_quorum_met"] == Decimal("4.000000")
    assert counts_by_code["convective_watch_type_severe_thunderstorm"] == Decimal(
        "3.000000",
    )
    assert counts_by_code["convective_watch_source_quorum_low"] == Decimal("1.000000")
    assert report.reason_code_counts == tuple(
        sorted(report.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert report.reason_codes == tuple(sorted(report.reason_codes))


def test_empty_digest_and_payload_are_report_only_readonly_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_weather_convective_watch_upgrade_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.reason_codes == ("convective_watch_upgrade_digest_empty",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))


def test_deterministic_sorting_reason_counts_and_payload_for_reordered_inputs() -> None:
    observations = (
        observation(
            "gamma",
            upstream_reason_codes=("spc_mesoanalysis", "radar_rotation", "spc_mesoanalysis"),
        ),
        observation(
            "alpha",
            cape_shear_composite=Decimal("0.200000"),
            model_agreement_score=Decimal("0.200000"),
            warning_lead_time_minutes=Decimal("90.000000"),
            population_exposure_score=Decimal("0.200000"),
            airport_exposure_score=Decimal("0.100000"),
            source_quorum_count=Decimal("2.000000"),
        ),
        observation(
            "beta",
            cape_shear_composite=Decimal("0.600000"),
            model_agreement_score=Decimal("0.700000"),
            warning_lead_time_minutes=Decimal("45.000000"),
            population_exposure_score=Decimal("0.500000"),
            airport_exposure_score=Decimal("0.200000"),
            source_quorum_count=Decimal("2.000000"),
        ),
    )

    module = api()
    first = module.market_research_weather_convective_watch_upgrade_digest_payload(
        digest(observations),
    )
    second = module.market_research_weather_convective_watch_upgrade_digest_payload(
        digest(tuple(reversed(observations))),
    )

    assert first == second
    assert [row["event_id"] for row in first["rows"]] == ["gamma", "beta", "alpha"]
    assert first["rows"][0]["reason_codes"] == sorted(first["rows"][0]["reason_codes"])
    assert first["reason_codes"] == sorted(first["reason_codes"])
    assert first["reason_code_counts"] == sorted(
        first["reason_code_counts"],
        key=lambda item: (-Decimal(item["count"]), item["reason_code"]),
    )


def test_rejects_float_inputs_naive_datetimes_subclasses_future_sources_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="cape_shear_composite"):
        observation(cape_shear_composite=Decimal("NaN"))

    with pytest.raises(ValueError, match="model_agreement_score"):
        observation(model_agreement_score=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="airport_exposure_score"):
        observation(airport_exposure_score=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=900)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_quorum_minimum"):
        config(source_quorum_minimum=Decimal("0.000000"))

    with pytest.raises(ValueError, match="blocked_upgrade_pressure_threshold"):
        config(blocked_upgrade_pressure_threshold=Decimal("0.400000"))

    with pytest.raises(ValueError, match="target_watch_type"):
        observation(target_watch_type="flood")

    with pytest.raises(ValueError, match="market_category"):
        observation(market_category="sports")

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(source_observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        digest((observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        digest((observation(readonly=False),))

    with pytest.raises(ValueError, match="redacted_source_reference"):
        replace(
            digest((observation(source_reference="https://wx.example/?secret=123"),)).rows[
                0
            ],
            redacted_source_reference="https://wx.example/?secret=123",
        )

    report = digest((observation(),))
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_weather_convective_watch_upgrade_digest_payload(
            unsafe_report,
        )

    with pytest.raises(ValueError, match="report"):
        module.market_research_weather_convective_watch_upgrade_digest_payload(
            {"bad": "value"},
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    report = digest((observation(),))

    for item in (config(), observation(), report, *report.reason_code_counts, *report.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        report.row_count = Decimal("2.000000")  # type: ignore[misc]

    public_classes = (
        module.ConvectiveWatchUpgradeDigestConfig,
        module.ConvectiveWatchUpgradeObservation,
        module.ConvectiveWatchUpgradeDigestRow,
        module.ConvectiveWatchUpgradeReasonCodeCount,
        module.WeatherConvectiveWatchUpgradeDigestReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_payload_redacts_sensitive_references_and_rejects_unsafe_public_content() -> None:
    module = api()
    report = digest(
        (
            observation(
                source_reference="https://wx.example/convective?credential=secret-123",
            ),
        ),
    )
    payload = module.market_research_weather_convective_watch_upgrade_digest_payload(
        report,
    )

    assert payload == module.market_research_weather_convective_watch_upgrade_digest_payload(
        report,
    )
    assert payload["rows"][0]["redacted_source_reference"].startswith("sha256:")
    assert "secret-123" not in repr(payload).lower()
    assert "credential" not in repr(payload).lower()
    assert "wallet" not in repr(payload).lower()
    assert_no_public_float_or_int(payload)


def test_module_has_no_live_trading_auth_io_or_durable_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "private_key",
        "api_key",
        "auth",
        "wallet",
        "requests",
        "httpx",
        "urllib",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "postgres",
        "redis",
        "os.environ",
        "getenv",
        "open(",
        "read_text",
        "write_text",
        "path(",
        "connect(",
        "execute(",
    ):
        assert token not in source

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    exported = module_path.read_text().split("__all__ = (", 1)[1].split(")", 1)[0]
    assert "build_market_research_weather_convective_watch_upgrade_digest" in exported
    assert "market_research_weather_convective_watch_upgrade_digest_payload" in exported
    assert inspect.signature(
        api().build_market_research_weather_convective_watch_upgrade_digest,
    ).parameters["config"].kind is inspect.Parameter.KEYWORD_ONLY
