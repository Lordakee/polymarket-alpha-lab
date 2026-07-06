from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType

import pytest


GENERATED_AT = datetime(2026, 7, 5, 14, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_energy_gas_storage_weather_beta_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    region_id: str = "us-gulf",
    storage_hub_id: str = "henry-hub",
    storage_draw_bcf: str | Decimal = "92.000000",
    normal_draw_bcf: str | Decimal = "38.000000",
    hdd_anomaly: str | Decimal = "14.000000",
    weather_confidence: str | Decimal = "0.840000",
    pipeline_freeze_risk: str | Decimal = "0.700000",
    source_timestamp: datetime = datetime(2026, 7, 5, 13, 15, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("gas_storage_weather_beta_storage_reported",),
):
    module = digest()
    return module.EnergyGasStorageWeatherBetaObservation(
        source_id=source_id,
        region_id=region_id,
        storage_hub_id=storage_hub_id,
        storage_draw_bcf=(
            storage_draw_bcf
            if isinstance(storage_draw_bcf, Decimal)
            else d(storage_draw_bcf)
        ),
        normal_draw_bcf=(
            normal_draw_bcf if isinstance(normal_draw_bcf, Decimal) else d(normal_draw_bcf)
        ),
        hdd_anomaly=hdd_anomaly if isinstance(hdd_anomaly, Decimal) else d(hdd_anomaly),
        weather_confidence=(
            weather_confidence
            if isinstance(weather_confidence, Decimal)
            else d(weather_confidence)
        ),
        pipeline_freeze_risk=(
            pipeline_freeze_risk
            if isinstance(pipeline_freeze_risk, Decimal)
            else d(pipeline_freeze_risk)
        ),
        source_timestamp=source_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = digest()
    return module.build_market_research_energy_gas_storage_weather_beta_digest(
        rows,
        config=cfg or module.EnergyGasStorageWeatherBetaDigestConfig(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_blocked_report_only_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.EnergyGasStorageWeatherBetaDigestReport)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-energy-gas-storage-weather-beta-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_energy_gas_storage_weather_beta_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.max_draw_surprise_bcf == d("0.000000")
    assert digest_report.average_draw_surprise_bcf == d("0.000000")
    assert digest_report.max_hdd_anomaly == d("0.000000")
    assert digest_report.max_pipeline_freeze_risk == d("0.000000")
    assert digest_report.weather_beta_pressure_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("gas_storage_weather_beta_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.EnergyGasStorageWeatherBetaReasonCodeCount(
            reason_code="gas_storage_weather_beta_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_storage_weather_pressure_reduces_rows_and_reasons_deterministically() -> None:
    blocked = observation(
        "source-freeze",
        region_id="permian",
        storage_hub_id="waha",
        storage_draw_bcf="108.000000",
        normal_draw_bcf="40.000000",
        hdd_anomaly="18.000000",
        pipeline_freeze_risk="0.820000",
        upstream_reason_codes=(
            "gas_storage_weather_beta_storage_reported",
            "gas_storage_weather_beta_weather_revision",
        ),
    )
    watch = observation(
        "source-watch",
        region_id="appalachia",
        storage_hub_id="dominion-south",
        storage_draw_bcf="58.000000",
        normal_draw_bcf="31.000000",
        hdd_anomaly="7.500000",
        pipeline_freeze_risk="0.420000",
    )
    passed = observation(
        "source-clear",
        region_id="rockies",
        storage_hub_id="opal",
        storage_draw_bcf="22.000000",
        normal_draw_bcf="25.000000",
        hdd_anomaly="1.250000",
        pipeline_freeze_risk="0.120000",
    )

    forward = report(watch, passed, blocked)
    reverse = report(blocked, passed, watch)

    assert forward == reverse
    assert forward.digest_status == "blocked"
    assert forward.reason_codes == (
        "gas_storage_weather_beta_blocked_present",
        "gas_storage_weather_beta_watch_present",
        "gas_storage_weather_beta_draw_pressure_present",
        "gas_storage_weather_beta_weather_pressure_present",
        "gas_storage_weather_beta_freeze_risk_present",
        "gas_storage_weather_beta_revision_present",
    )
    assert tuple(row.region_id for row in forward.rows) == (
        "permian",
        "appalachia",
        "rockies",
    )
    assert tuple(row.storage_status for row in forward.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert forward.rows[0].draw_surprise_bcf == d("68.000000")
    assert forward.rows[0].source_timestamp == datetime(2026, 7, 5, 13, 15, tzinfo=UTC)
    assert forward.rows[0].reason_codes == (
        "gas_storage_weather_beta_draw_blocked",
        "gas_storage_weather_beta_hdd_blocked",
        "gas_storage_weather_beta_freeze_blocked",
        "gas_storage_weather_beta_revision_present",
    )
    assert forward.rows[1].reason_codes == (
        "gas_storage_weather_beta_draw_watch",
        "gas_storage_weather_beta_hdd_watch",
    )
    assert forward.rows[2].reason_codes == ("gas_storage_weather_beta_inline",)
    assert tuple(item.reason_code for item in forward.reason_code_counts) == forward.reason_codes
    assert forward.reason_code_counts[0].count == d("1.000000")
    assert forward.reason_code_counts[0].row_ratio == d("0.333333")


def test_validation_rejects_subclasses_lists_future_time_and_noncanonical_decimals() -> None:
    module = digest()

    public_types = (
        module.EnergyGasStorageWeatherBetaDigestConfig,
        module.EnergyGasStorageWeatherBetaObservation,
        module.EnergyGasStorageWeatherBetaDigestRow,
        module.EnergyGasStorageWeatherBetaReasonCodeCount,
        module.EnergyGasStorageWeatherBetaDigestReport,
    )
    for public_type in public_types:
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{public_type.__name__}", (public_type,), {})
    with pytest.raises(ValueError, match="storage_draw_bcf must be a Decimal"):
        observation(storage_draw_bcf=_DecimalSubclass("42.000000"))
    with pytest.raises(ValueError, match="hdd_anomaly must use exactly six decimal places"):
        observation(hdd_anomaly=d("6.50000"))
    with pytest.raises(ValueError, match="source_timestamp must be a datetime"):
        observation(
            source_timestamp=_DateTimeSubclass(2026, 7, 5, 13, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_timestamp must be timezone-aware"):
        observation(source_timestamp=datetime(2026, 7, 5, 13, 15))
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["gas_storage_weather_beta_storage_reported"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="upstream_reason_codes must use deterministic sequence"):
        observation(
            upstream_reason_codes=(
                "gas_storage_weather_beta_weather_revision",
                "gas_storage_weather_beta_storage_reported",
            ),
        )
    with pytest.raises(ValueError, match="observations must be a tuple"):
        module.build_market_research_energy_gas_storage_weather_beta_digest(
            [observation("source-list")],
            config=module.EnergyGasStorageWeatherBetaDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source_timestamp must not be after generated_at"):
        report(
            observation(
                "source-future",
                source_timestamp=datetime(2026, 7, 5, 15, 0, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="observations must not contain duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    tampered_observation = observation("source-tampered")
    object.__setattr__(
        tampered_observation,
        "upstream_reason_codes",
        ["gas_storage_weather_beta_storage_reported"],
    )
    with pytest.raises(ValueError, match="upstream_reason_codes has unsupported payload value"):
        report(tampered_observation)


def test_non_default_thresholds_can_downgrade_weather_pressure() -> None:
    module = digest()
    cfg = module.EnergyGasStorageWeatherBetaDigestConfig(
        watch_draw_surprise_bcf=d("80.000000"),
        blocked_draw_surprise_bcf=d("120.000000"),
        watch_hdd_anomaly=d("10.000000"),
        blocked_hdd_anomaly=d("20.000000"),
        watch_pipeline_freeze_risk=d("0.900000"),
        blocked_pipeline_freeze_risk=d("0.950000"),
    )

    digest_report = report(
        observation(
            "source-threshold",
            storage_draw_bcf="58.000000",
            normal_draw_bcf="31.000000",
            hdd_anomaly="7.500000",
            pipeline_freeze_risk="0.420000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_energy_gas_storage_weather_beta_screening"
    )
    assert digest_report.rows[0].storage_status == "pass"
    assert digest_report.rows[0].reason_codes == ("gas_storage_weather_beta_inline",)
    assert digest_report.reason_codes == ("gas_storage_weather_beta_clear",)
    assert digest_report.weather_beta_pressure_score == d("0.420000")


def test_public_records_are_frozen_exact_type_and_enforce_hard_flags() -> None:
    module = digest()
    digest_report = report(observation("source-frozen"))

    public_records = (
        module.EnergyGasStorageWeatherBetaDigestConfig(),
        observation("source-record"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )
    for public_record in public_records:
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal
                assert field_value.as_tuple().exponent == -6

    frozen_observation = observation("source-immutable")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.EnergyGasStorageWeatherBetaDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-hard-flag"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_reason_counts_reject_zero_and_reconcile_with_report_rows() -> None:
    module = digest()
    digest_report = report(observation("source-reason"))

    with pytest.raises(ValueError, match="count must be positive"):
        module.EnergyGasStorageWeatherBetaReasonCodeCount(
            reason_code="gas_storage_weather_beta_blocked_present",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="count must be an integer count"):
        module.EnergyGasStorageWeatherBetaReasonCodeCount(
            reason_code="gas_storage_weather_beta_blocked_present",
            count=d("1.500000"),
            row_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(
            digest_report.rows[0],
            reason_codes=(
                "gas_storage_weather_beta_hdd_blocked",
                "gas_storage_weather_beta_draw_blocked",
                "gas_storage_weather_beta_freeze_blocked",
            ),
        )
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(digest_report, reason_code_counts=())
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(
            digest_report,
            reason_code_counts=(
                module.EnergyGasStorageWeatherBetaReasonCodeCount(
                    reason_code="gas_storage_weather_beta_blocked_present",
                    count=d("2.000000"),
                    row_ratio=d("1.000000"),
                ),
            ),
        )


def test_payload_is_immutable_utc_enforced_and_recursively_revalidated() -> None:
    module = digest()
    digest_report = report(
        observation(
            "source-payload",
            source_timestamp=datetime(2026, 7, 5, 9, 15, tzinfo=timezone(timedelta(hours=-4))),
        ),
    )

    payload = module.market_research_energy_gas_storage_weather_beta_digest_payload(
        digest_report,
    )

    assert type(payload) is MappingProxyType
    assert payload["generated_at"] == "2026-07-05T14:00:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert type(payload["rows"]) is tuple
    assert payload["rows"][0]["source_timestamp"] == "2026-07-05T13:15:00+00:00"
    assert payload["rows"][0]["draw_surprise_bcf"] == "54.000000"
    with pytest.raises(TypeError):
        payload["digest_status"] = "pass"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["region_id"] = "changed"  # type: ignore[index]

    object.__setattr__(
        digest_report.rows[0],
        "source_timestamp",
        datetime(2026, 7, 5, 9, 15, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="source_timestamp must already be UTC"):
        module.market_research_energy_gas_storage_weather_beta_digest_payload(
            digest_report,
        )

    clean_report = report(observation("source-revalidate"))
    object.__setattr__(clean_report.rows[0], "draw_surprise_bcf", d("999.000000"))
    with pytest.raises(ValueError, match="draw_surprise_bcf must match"):
        module.market_research_energy_gas_storage_weather_beta_digest_payload(
            clean_report,
        )


def test_module_has_no_io_live_surfaces_or_forbidden_public_payload_names() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_energy_gas_storage_weather_beta_digest.py",
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
        if isinstance(node, ast.Attribute):
            assert node.attr != "asdict"

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "market_slug",
        "payload_json",
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()
