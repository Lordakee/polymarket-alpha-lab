from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_weather_convective_outlook_upgrade_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_weather_convective_outlook_upgrade_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "weather-convective-outlook-upgrade-digest-v1",
        "max_source_age_seconds": Decimal("900.000000"),
        "high_upgrade_risk_score": Decimal("0.700000"),
        "watch_upgrade_risk_score": Decimal("0.500000"),
        "severe_probability_watch": Decimal("0.150000"),
        "significant_severe_probability_watch": Decimal("0.100000"),
        "model_agreement_watch": Decimal("0.650000"),
        "population_exposure_watch": Decimal("0.650000"),
        "high_confidence_threshold": Decimal("0.800000"),
    }
    values.update(overrides)
    return module.ConvectiveOutlookUpgradeDigestConfig(**values)


def outlook(
    outlook_id: str = "day1-central-2026-07-04",
    *,
    region_key: str = "central-plains",
    current_risk_category: str = "slight",
    target_risk_category: str = "enhanced",
    outlook_valid_at: datetime = GENERATED_AT - timedelta(minutes=30),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    upgrade_signal_probability: Decimal = Decimal("0.850000"),
    severe_probability: Decimal = Decimal("0.600000"),
    significant_severe_probability: Decimal = Decimal("0.300000"),
    model_agreement_score: Decimal = Decimal("0.900000"),
    population_exposure_score: Decimal = Decimal("0.800000"),
    forecast_confidence: Decimal = Decimal("0.920000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ConvectiveOutlookUpgradeObservation(
        outlook_id=outlook_id,
        region_key=region_key,
        current_risk_category=current_risk_category,
        target_risk_category=target_risk_category,
        outlook_valid_at=outlook_valid_at,
        source_observed_at=source_observed_at,
        upgrade_signal_probability=upgrade_signal_probability,
        severe_probability=severe_probability,
        significant_severe_probability=significant_severe_probability,
        model_agreement_score=model_agreement_score,
        population_exposure_score=population_exposure_score,
        forecast_confidence=forecast_confidence,
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
    return module.build_market_research_weather_convective_outlook_upgrade_digest(
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


def test_builds_high_risk_digest_with_decimal_counts_utc_sorting_and_reasons() -> None:
    report = digest(
        (
            outlook(
                "zeta-low-stale",
                current_risk_category="marginal",
                target_risk_category="slight",
                source_observed_at=GENERATED_AT - timedelta(seconds=3600),
                upgrade_signal_probability=Decimal("0.100000"),
                severe_probability=Decimal("0.050000"),
                significant_severe_probability=Decimal("0.000000"),
                model_agreement_score=Decimal("0.200000"),
                population_exposure_score=Decimal("0.200000"),
                forecast_confidence=Decimal("0.400000"),
                upstream_reason_codes=("spc_day1",),
            ),
            outlook(
                "alpha-high",
                current_risk_category="slight",
                target_risk_category="moderate",
                outlook_valid_at=datetime(
                    2026,
                    7,
                    4,
                    7,
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
                upgrade_signal_probability=Decimal("0.950000"),
                severe_probability=Decimal("0.700000"),
                significant_severe_probability=Decimal("0.400000"),
                model_agreement_score=Decimal("0.950000"),
                population_exposure_score=Decimal("0.900000"),
                forecast_confidence=Decimal("0.920000"),
                upstream_reason_codes=("ensemble_signal",),
            ),
            outlook(
                "beta-watch",
                current_risk_category="slight",
                target_risk_category="enhanced",
                upgrade_signal_probability=Decimal("0.650000"),
                severe_probability=Decimal("0.350000"),
                significant_severe_probability=Decimal("0.100000"),
                model_agreement_score=Decimal("0.700000"),
                population_exposure_score=Decimal("0.500000"),
                forecast_confidence=Decimal("0.720000"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.input_count == Decimal("3.000000")
    assert report.row_count == Decimal("3.000000")
    assert report.high_upgrade_risk_count == Decimal("1.000000")
    assert report.upgrade_watch_count == Decimal("1.000000")
    assert report.low_upgrade_risk_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.max_upgrade_risk_score == Decimal("0.800000")
    assert report.max_severe_probability == Decimal("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [(row.outlook_id, row.upgrade_status) for row in report.rows] == [
        ("alpha-high", "high_upgrade_risk"),
        ("beta-watch", "upgrade_watch"),
        ("zeta-low-stale", "low_upgrade_risk"),
    ]

    high = report.rows[0]
    assert high.outlook_valid_at == datetime(2026, 7, 4, 11, 30, tzinfo=UTC)
    assert high.source_observed_at == datetime(2026, 7, 4, 11, 58, tzinfo=UTC)
    assert high.source_age_seconds == Decimal("120.000000")
    assert high.upgrade_step_count == Decimal("2.000000")
    assert high.upgrade_risk_score == Decimal("0.800000")
    assert high.confidence_cap == Decimal("1.000000")
    assert high.capped_confidence == Decimal("0.920000")
    assert high.reason_codes == (
        "convective_outlook_upgrade_high_confidence",
        "convective_outlook_upgrade_high_risk",
        "convective_outlook_upgrade_model_agreement",
        "convective_outlook_upgrade_multi_step",
        "convective_outlook_upgrade_population_exposure",
        "convective_outlook_upgrade_severe_probability",
        "convective_outlook_upgrade_significant_severe_probability",
        "convective_outlook_upgrade_source_fresh",
        "ensemble_signal",
    )

    stale = report.rows[2]
    assert stale.source_age_seconds == Decimal("3600.000000")
    assert stale.confidence_cap == Decimal("0.500000")
    assert stale.capped_confidence == Decimal("0.400000")
    assert stale.reason_codes == (
        "convective_outlook_upgrade_low_risk",
        "convective_outlook_upgrade_source_stale",
        "spc_day1",
    )

    assert report.reason_codes == (
        "convective_outlook_upgrade_high_confidence",
        "convective_outlook_upgrade_high_risk",
        "convective_outlook_upgrade_low_risk",
        "convective_outlook_upgrade_model_agreement",
        "convective_outlook_upgrade_multi_step",
        "convective_outlook_upgrade_population_exposure",
        "convective_outlook_upgrade_severe_probability",
        "convective_outlook_upgrade_significant_severe_probability",
        "convective_outlook_upgrade_source_fresh",
        "convective_outlook_upgrade_source_stale",
        "convective_outlook_upgrade_watch",
        "ensemble_signal",
        "spc_day1",
    )


def test_empty_digest_and_payload_are_report_only_readonly_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_weather_convective_outlook_upgrade_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.high_upgrade_risk_count == Decimal("0.000000")
    assert report.reason_codes == ("convective_outlook_upgrade_digest_empty",)
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)


def test_deterministic_sorting_reason_codes_and_payload_for_reordered_inputs() -> None:
    observations = (
        outlook(
            "gamma",
            upstream_reason_codes=("spc_day1", "ensemble_signal", "spc_day1"),
        ),
        outlook(
            "alpha",
            current_risk_category="marginal",
            target_risk_category="slight",
            upgrade_signal_probability=Decimal("0.100000"),
            severe_probability=Decimal("0.050000"),
            significant_severe_probability=Decimal("0.000000"),
            model_agreement_score=Decimal("0.100000"),
            population_exposure_score=Decimal("0.100000"),
            forecast_confidence=Decimal("0.400000"),
            upstream_reason_codes=("zeta_source", "alpha_source"),
        ),
        outlook(
            "beta",
            upgrade_signal_probability=Decimal("0.650000"),
            severe_probability=Decimal("0.350000"),
            significant_severe_probability=Decimal("0.100000"),
            model_agreement_score=Decimal("0.700000"),
            population_exposure_score=Decimal("0.500000"),
            forecast_confidence=Decimal("0.720000"),
        ),
    )

    module = api()
    first = module.market_research_weather_convective_outlook_upgrade_digest_payload(
        digest(observations),
    )
    second = module.market_research_weather_convective_outlook_upgrade_digest_payload(
        digest(tuple(reversed(observations))),
    )

    assert first == second
    assert [row["outlook_id"] for row in first["rows"]] == ["gamma", "beta", "alpha"]
    assert first["rows"][0]["reason_codes"] == sorted(first["rows"][0]["reason_codes"])
    assert first["reason_codes"] == sorted(first["reason_codes"])


def test_rejects_float_inputs_naive_datetimes_subclasses_future_sources_and_bad_categories() -> None:
    with pytest.raises(ValueError, match="upgrade_signal_probability"):
        outlook(upgrade_signal_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="severe_probability"):
        outlook(severe_probability=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="forecast_confidence"):
        outlook(forecast_confidence=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=900)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="high_upgrade_risk_score"):
        config(
            high_upgrade_risk_score=Decimal("0.400000"),
            watch_upgrade_risk_score=Decimal("0.500000"),
        )

    with pytest.raises(ValueError, match="UTC-aware"):
        outlook(source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        outlook(source_observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        digest((outlook(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="current_risk_category"):
        outlook(current_risk_category="unknown")

    with pytest.raises(ValueError, match="target_risk_category must be higher"):
        outlook(current_risk_category="enhanced", target_risk_category="slight")


def test_hard_flags_frozen_dataclasses_and_public_numeric_types_are_enforced() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        outlook(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        outlook(readonly=False)

    report = digest((outlook(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.ConvectiveOutlookUpgradeDigestConfig,
        module.ConvectiveOutlookUpgradeObservation,
        module.ConvectiveOutlookUpgradeDigestRow,
        module.WeatherConvectiveOutlookUpgradeDigestReport,
    )
    for type_ in classes:
        assert is_dataclass(type_)
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_non_default_thresholds_can_raise_upgrade_screening_status() -> None:
    candidate = outlook(
        "threshold-candidate",
        current_risk_category="marginal",
        target_risk_category="slight",
        upgrade_signal_probability=Decimal("0.800000"),
        severe_probability=Decimal("0.100000"),
        significant_severe_probability=Decimal("0.000000"),
        model_agreement_score=Decimal("0.300000"),
        population_exposure_score=Decimal("0.200000"),
        forecast_confidence=Decimal("0.700000"),
    )

    default_report = digest((candidate,))
    assert default_report.rows[0].upgrade_status == "low_upgrade_risk"
    assert default_report.rows[0].upgrade_risk_score == Decimal("0.395000")

    custom_report = digest(
        (candidate,),
        cfg=config(
            high_upgrade_risk_score=Decimal("0.390000"),
            watch_upgrade_risk_score=Decimal("0.300000"),
            severe_probability_watch=Decimal("0.900000"),
            significant_severe_probability_watch=Decimal("0.900000"),
            model_agreement_watch=Decimal("0.900000"),
            population_exposure_watch=Decimal("0.900000"),
        ),
    )
    assert custom_report.rows[0].upgrade_status == "high_upgrade_risk"
    assert custom_report.high_upgrade_risk_count == Decimal("1.000000")
    assert "convective_outlook_upgrade_high_risk" in custom_report.reason_codes


def test_module_scope_is_pure_without_io_or_mutation_surface_terms() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "token",
        "live trading",
    ):
        assert forbidden not in source

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
