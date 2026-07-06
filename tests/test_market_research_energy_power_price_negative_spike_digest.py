from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_energy_power_price_negative_spike_digest import (
    DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestReport,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestRow,
    build_market_research_energy_power_price_negative_spike_digest,
    market_research_energy_power_price_negative_spike_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "min_source_count": d("3.000000"),
        "watch_negative_price_mwh": d("10.000000"),
        "blocked_negative_price_mwh": d("50.000000"),
        "sharp_price_drop_mwh": d("35.000000"),
        "high_renewable_share": d("0.700000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    spike_id: str = "pjm_ready_interval",
    *,
    grid_region: str = "PJM-West",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    source_count: Decimal = d("3.000000"),
    settlement_price_mwh: Decimal = d("25.000000"),
    prior_price_mwh: Decimal = d("30.000000"),
    day_ahead_price_mwh: Decimal = d("28.000000"),
    renewable_share: Decimal = d("0.300000"),
    load_mw: Decimal = d("40000.000000"),
    confidence: Decimal = d("0.900000"),
    source_config_version: str = "energy-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation:
    return MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation(
        condition_id=condition_id,
        spike_id=spike_id,
        grid_region=grid_region,
        observed_at=observed_at,
        source_count=source_count,
        settlement_price_mwh=settlement_price_mwh,
        prior_price_mwh=prior_price_mwh,
        day_ahead_price_mwh=day_ahead_price_mwh,
        renewable_share=renewable_share,
        load_mw=load_mw,
        confidence=confidence,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *observations: MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
    config: MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEnergyPowerPriceNegativeSpikeDigestReport:
    return build_market_research_energy_power_price_negative_spike_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_negative_spike_digest_flags_pressure_and_sorts_rows() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "ercot_negative_spike",
            grid_region="ERCOT-North",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            source_count=d("1.000000"),
            settlement_price_mwh=d("-75.000000"),
            prior_price_mwh=d("15.000000"),
            day_ahead_price_mwh=d("20.000000"),
            renewable_share=d("0.850000"),
            load_mw=d("52000.000000"),
            confidence=d("0.500000"),
        ),
        _observation(
            "condition_alpha",
            "pjm_ready_interval",
        ),
        _observation(
            "condition_gamma",
            "caiso_negative_spike",
            grid_region="CAISO-SP15",
            source_count=d("2.000000"),
            settlement_price_mwh=d("-15.000000"),
            prior_price_mwh=d("10.000000"),
            day_ahead_price_mwh=d("12.000000"),
            renewable_share=d("0.750000"),
            load_mw=d("33000.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_energy_power_price_negative_spike_digest"
    )
    assert report.observation_count == d("3.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("1.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.negative_spike_count == d("2.000000")
    assert report.sharp_price_drop_count == d("1.000000")
    assert report.high_renewable_share_count == d("2.000000")
    assert report.source_diversity_gap_count == d("2.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_count == d("1.000000")
    assert report.average_settlement_price_mwh == d("-21.666667")
    assert report.average_price_drop_mwh == d("40.000000")
    assert report.max_negative_price_abs == d("75.000000")
    assert report.max_price_drop_mwh == d("90.000000")

    assert tuple((row.condition_id, row.spike_id) for row in report.rows) == (
        ("condition_beta", "ercot_negative_spike"),
        ("condition_gamma", "caiso_negative_spike"),
        ("condition_alpha", "pjm_ready_interval"),
    )

    blocked = report.rows[0]
    assert blocked.spike_status == "blocked"
    assert blocked.observation_age_seconds == d("2400.000000")
    assert blocked.negative_price_abs == d("75.000000")
    assert blocked.price_drop_mwh == d("90.000000")
    assert blocked.reason_codes == (
        "market_research_energy_power_price_negative_spike_digest_negative_price_spike",
        "market_research_energy_power_price_negative_spike_digest_sharp_price_drop",
        "market_research_energy_power_price_negative_spike_digest_high_renewable_share",
        "market_research_energy_power_price_negative_spike_digest_source_diversity_gap",
        "market_research_energy_power_price_negative_spike_digest_stale_observation",
        "market_research_energy_power_price_negative_spike_digest_confidence_gap",
    )
    assert report.reason_codes == (
        "market_research_energy_power_price_negative_spike_digest_negative_price_spike",
        "market_research_energy_power_price_negative_spike_digest_sharp_price_drop",
        "market_research_energy_power_price_negative_spike_digest_high_renewable_share",
        "market_research_energy_power_price_negative_spike_digest_source_diversity_gap",
        "market_research_energy_power_price_negative_spike_digest_stale_observation",
        "market_research_energy_power_price_negative_spike_digest_confidence_gap",
    )
    assert report.reason_code_counts == (
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_price_negative_spike_digest_negative_price_spike"
            ),
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_price_negative_spike_digest_sharp_price_drop"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_price_negative_spike_digest_high_renewable_share"
            ),
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_price_negative_spike_digest_source_diversity_gap"
            ),
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_price_negative_spike_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_price_negative_spike_digest_confidence_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code="market_research_energy_power_price_negative_spike_digest_ready",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )


def test_empty_input_is_blocked_report_only_digest() -> None:
    report = _report(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))

    assert report.generated_at == GENERATED_AT
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "hold_report_only_market_research_energy_power_price_negative_spike_digest"
    )
    assert report.observation_count == ZERO
    assert report.ready_observation_count == ZERO
    assert report.watch_observation_count == ZERO
    assert report.blocked_observation_count == ZERO
    assert report.reason_codes == (
        "market_research_energy_power_price_negative_spike_digest_no_inputs",
    )
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_serializes_decimals_to_six_strings_and_rejects_time_tampering() -> None:
    report = _report(
        _observation(
            observed_at=datetime(2026, 7, 6, 13, 30, tzinfo=timezone(timedelta(hours=2))),
            settlement_price_mwh=d("-12.3456789"),
            prior_price_mwh=d("10.0000001"),
            day_ahead_price_mwh=d("12.0000001"),
            renewable_share=d("0.7500001"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    payload = market_research_energy_power_price_negative_spike_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_settlement_price_mwh"] == "-12.345679"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["settlement_price_mwh"] == "-12.345679"
    assert payload["rows"][0]["negative_price_abs"] == "12.345679"
    assert payload["rows"][0]["price_drop_mwh"] == "22.345679"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"
    _assert_no_float_or_decimal_payload(payload)

    object.__setattr__(
        report,
        "generated_at",
        datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="normalized to UTC"):
        market_research_energy_power_price_negative_spike_digest_payload(report)

    report = _report(_observation())
    object.__setattr__(
        report.rows[0],
        "observed_at",
        datetime(2026, 7, 6, 13, 0, tzinfo=timezone(timedelta(hours=1))),
    )
    with pytest.raises(ValueError, match="normalized to UTC"):
        market_research_energy_power_price_negative_spike_digest_payload(report)


def test_payload_recursively_revalidates_nested_public_dataclasses() -> None:
    report = _report(_observation(settlement_price_mwh=d("-15.000000")))

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_energy_power_price_negative_spike_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "count", ZERO)
    with pytest.raises(ValueError, match="constructor-valid"):
        market_research_energy_power_price_negative_spike_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "count", d("1.000000"))

    object.__setattr__(report.rows[0], "negative_price_abs", d("0.000001"))
    with pytest.raises(ValueError, match="constructor-valid"):
        market_research_energy_power_price_negative_spike_digest_payload(report)


def test_public_constructors_reject_noncanonical_public_collections_and_counts() -> None:
    good_row = _report(_observation()).rows[0]
    good_count = MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
        reason_code="market_research_energy_power_price_negative_spike_digest_ready",
        count=d("1.000000"),
        observation_ratio=d("1.000000"),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(good_row, reason_codes=["market_research_energy_power_price_negative_spike_digest_ready"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="count"):
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code="market_research_energy_power_price_negative_spike_digest_ready",
            count=ZERO,
            observation_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code="market_research_energy_power_price_negative_spike_digest_ready",
            count=d("1.500000"),
            observation_ratio=d("1.000000"),
        )

    report = _report(
        _observation("condition_b", "spike_b", settlement_price_mwh=d("-15.000000")),
        _observation("condition_a", "spike_a"),
    )
    same_spike_report = _report(
        _observation(
            "condition_a",
            "shared_spike",
            source_config_version="energy-source-a",
        ),
        _observation(
            "condition_b",
            "shared_spike",
            settlement_price_mwh=d("-15.000000"),
            source_config_version="energy-source-b",
        ),
    )
    assert same_spike_report.source_config_versions == (
        ("shared_spike", "condition_a", "energy-source-a"),
        ("shared_spike", "condition_b", "energy-source-b"),
    )

    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=list(report.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(good_count,))
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(report, source_config_versions=list(report.source_config_versions))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(
            report,
            source_config_versions=tuple(reversed(report.source_config_versions)),
        )


def test_payload_revalidates_negative_price_threshold_status_tampering() -> None:
    report = _report(
        _observation(
            settlement_price_mwh=d("-55.000000"),
            prior_price_mwh=d("-50.000000"),
        ),
    )
    assert report.rows[0].spike_status == "blocked"
    assert report.rows[0].reason_codes == (
        "market_research_energy_power_price_negative_spike_digest_negative_price_spike",
    )

    object.__setattr__(report.rows[0], "spike_status", "watch")
    with pytest.raises(ValueError, match="constructor-valid"):
        market_research_energy_power_price_negative_spike_digest_payload(report)


def test_public_values_are_frozen_exact_decimal_and_type_safe() -> None:
    public_values = (
        _config(),
        _observation(),
        *_report(_observation()).rows,
        *_report(_observation(settlement_price_mwh=d("-15.000000"))).reason_code_counts,
        _report(_observation()),
    )
    for value in public_values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False

    with pytest.raises(ValueError, match="config_version"):
        _config(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="watch_negative_price_mwh"):
        _config(watch_negative_price_mwh=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="settlement_price_mwh"):
        _observation(settlement_price_mwh=-15.0)
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        _observation(paper_only=False)

    public_type_kwargs = (
        (MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig, {}),
        (
            MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
            _observation_kwargs(),
        ),
    )
    for public_type, kwargs in public_type_kwargs:
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})
        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)

    forbidden_public_field_names = {"market_slug", "question", "payload_json"}
    for value in public_values:
        assert forbidden_public_field_names.isdisjoint(field.name for field in fields(value))

    numeric_names = {
        field.name
        for value in public_values
        for field in fields(value)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_share")
            or field.name.endswith("_price_mwh")
            or field.name.endswith("_price_abs")
            or field.name.endswith("_drop_mwh")
            or field.name.endswith("_mw")
            or field.name.endswith("_seconds")
            or field.name == "confidence"
            or field.name == "min_confidence"
        )
    }
    assert numeric_names
    for value in public_values:
        for field in fields(value):
            if field.name in numeric_names:
                public_value = getattr(value, field.name)
                assert public_value is None or type(public_value) is Decimal


def test_module_excludes_io_asdict_and_live_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_energy_power_price_negative_spike_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered_source = source.lower()
    tree = ast.parse(source)

    assert "asdict" not in lowered_source
    forbidden_literals = (
        "buy",
        "sell",
        "trade",
        "wallet",
        "order",
        "position",
        "auth",
        "cancel",
        "exchange",
        "mutation",
        "replace",
        "secret",
        "private_key",
        "api_key",
        "payload_json",
        "market_slug",
        "question",
    )
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _observation_kwargs(**overrides: object) -> dict[str, object]:
    values = {
        "condition_id": "condition_alpha",
        "spike_id": "pjm_ready_interval",
        "grid_region": "PJM-West",
        "observed_at": GENERATED_AT - timedelta(seconds=120),
        "source_count": d("3.000000"),
        "settlement_price_mwh": d("25.000000"),
        "prior_price_mwh": d("30.000000"),
        "day_ahead_price_mwh": d("28.000000"),
        "renewable_share": d("0.300000"),
        "load_mw": d("40000.000000"),
        "confidence": d("0.900000"),
        "source_config_version": "energy-source-v0",
    }
    values.update(overrides)
    return values


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]


def _assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_float_or_decimal_payload(child)
