from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_energy_refinery_outage_restart_digest"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-6))
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_energy_refinery_outage_restart_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("10800.000000"),
        "watch_restart_probability": d("0.650000"),
        "blocked_restart_probability": d("0.350000"),
        "watch_outage_duration_hours": d("12.000000"),
        "blocked_outage_duration_hours": d("48.000000"),
        "watch_capacity_offline_bpd": d("150000.000000"),
        "blocked_capacity_offline_bpd": d("400000.000000"),
        "watch_product_spread_impact_pressure": d("0.500000"),
        "blocked_product_spread_impact_pressure": d("0.800000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return module.MarketResearchEnergyRefineryOutageRestartDigestConfig(**values)


def input_row(
    module: Any,
    event_id: str = "energy.refinery.restart.gulf",
    *,
    refinery_id: str = "gulf-refinery-a",
    region: str = "us-gulf",
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    outage_started_at: datetime = GENERATED_AT - timedelta(hours=6),
    restart_probability: Decimal = d("0.820000"),
    offline_capacity_bpd: Decimal = d("50000.000000"),
    total_capacity_bpd: Decimal = d("500000.000000"),
    product_spread_impact_pressure: Decimal = d("0.150000"),
    source_count: Decimal = d("3.000000"),
    public_source_ref: str = "eia-public-refinery-restart-board",
    event_config_version: str = "refinery-restart-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.MarketResearchEnergyRefineryOutageRestartDigestInputRow(
        event_id=event_id,
        refinery_id=refinery_id,
        region=region,
        observed_at=observed_at,
        outage_started_at=outage_started_at,
        restart_probability=restart_probability,
        offline_capacity_bpd=offline_capacity_bpd,
        total_capacity_bpd=total_capacity_bpd,
        product_spread_impact_pressure=product_spread_impact_pressure,
        source_count=source_count,
        public_source_ref=public_source_ref,
        event_config_version=event_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_market_research_energy_refinery_outage_restart_digest(
        rows,
        config=cfg or config(module),
        generated_at=generated_at,
    )


def redacted(value: str) -> str:
    return (
        "redacted-source:"
        f"{__import__('hashlib').sha256(value.encode()).hexdigest()[:16]}"
    )


def test_refinery_outage_restart_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_refinery_outage_restart_digest_reduces_events_deterministically() -> None:
    module = api()

    summary = report(
        module,
        (
            input_row(
                module,
                "energy.refinery.restart.rotterdam",
                refinery_id="rotterdam-hydrocracker",
                region="europe",
                observed_at=GENERATED_AT - timedelta(hours=4),
                outage_started_at=GENERATED_AT - timedelta(hours=60),
                restart_probability=d("0.250000"),
                offline_capacity_bpd=d("425000.000000"),
                total_capacity_bpd=d("500000.000000"),
                product_spread_impact_pressure=d("0.900000"),
                source_count=d("1.000000"),
                public_source_ref="operator-feed-sensitive-123",
                event_config_version="refinery-restart-v2",
            ),
            input_row(
                module,
                "energy.refinery.restart.midcon",
                refinery_id="midcon-cdu",
                region="us-midcon",
                observed_at=GENERATED_AT - timedelta(hours=2),
                outage_started_at=GENERATED_AT - timedelta(hours=18),
                restart_probability=d("0.500000"),
                offline_capacity_bpd=d("200000.000000"),
                total_capacity_bpd=d("500000.000000"),
                product_spread_impact_pressure=d("0.600000"),
                public_source_ref="desk-feed-sensitive",
                event_config_version="refinery-restart-v1",
            ),
            input_row(module),
        ),
        generated_at=GENERATED_AT.astimezone(SOURCE_TZ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_refinery_outage_restart_digest"
    )
    assert summary.event_count == d("3.000000")
    assert summary.pass_event_count == d("1.000000")
    assert summary.watch_event_count == d("1.000000")
    assert summary.blocked_event_count == d("1.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.prolonged_outage_duration_count == d("2.000000")
    assert summary.low_restart_probability_count == d("2.000000")
    assert summary.material_capacity_offline_count == d("2.000000")
    assert summary.product_spread_pressure_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.total_offline_capacity_bpd == d("675000.000000")
    assert summary.max_offline_capacity_bpd == d("425000.000000")
    assert summary.average_outage_duration_hours == d("28.000000")
    assert summary.average_restart_probability == d("0.523333")
    assert summary.max_utilization_capacity_offline_ratio == d("0.850000")
    assert summary.max_product_spread_impact_pressure == d("0.900000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.restart_status, row.refinery_id) for row in summary.rows) == (
        ("blocked", "rotterdam-hydrocracker"),
        ("watch", "midcon-cdu"),
        ("pass", "gulf-refinery-a"),
    )

    blocked = summary.rows[0]
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=4)
    assert blocked.observation_age_seconds == d("14400.000000")
    assert blocked.outage_duration_hours == d("60.000000")
    assert blocked.utilization_capacity_offline_ratio == d("0.850000")
    assert blocked.redacted_public_source_ref == redacted("operator-feed-sensitive-123")
    assert blocked.reason_codes == (
        "market_research_energy_refinery_outage_restart_digest_stale_observation",
        "market_research_energy_refinery_outage_restart_digest_prolonged_outage_duration",
        "market_research_energy_refinery_outage_restart_digest_low_restart_probability",
        "market_research_energy_refinery_outage_restart_digest_material_capacity_offline",
        "market_research_energy_refinery_outage_restart_digest_product_spread_pressure",
        "market_research_energy_refinery_outage_restart_digest_thin_sources",
    )

    watch = summary.rows[1]
    assert watch.restart_status == "watch"
    assert watch.outage_duration_hours == d("18.000000")
    assert watch.restart_probability == d("0.500000")
    assert watch.redacted_public_source_ref == redacted("desk-feed-sensitive")
    assert watch.reason_codes == (
        "market_research_energy_refinery_outage_restart_digest_prolonged_outage_duration",
        "market_research_energy_refinery_outage_restart_digest_low_restart_probability",
        "market_research_energy_refinery_outage_restart_digest_material_capacity_offline",
        "market_research_energy_refinery_outage_restart_digest_product_spread_pressure",
    )

    passed = summary.rows[2]
    assert passed.restart_status == "pass"
    assert passed.outage_duration_hours == d("6.000000")
    assert passed.restart_probability == d("0.820000")
    assert passed.utilization_capacity_offline_ratio == d("0.100000")
    assert passed.redacted_public_source_ref == "eia-public-refinery-restart-board"
    assert passed.reason_codes == (
        "market_research_energy_refinery_outage_restart_digest_passed",
    )

    assert summary.reason_codes == (
        "market_research_energy_refinery_outage_restart_digest_stale_observation",
        "market_research_energy_refinery_outage_restart_digest_prolonged_outage_duration",
        "market_research_energy_refinery_outage_restart_digest_low_restart_probability",
        "market_research_energy_refinery_outage_restart_digest_material_capacity_offline",
        "market_research_energy_refinery_outage_restart_digest_product_spread_pressure",
        "market_research_energy_refinery_outage_restart_digest_thin_sources",
    )
    assert summary.reason_code_counts == (
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_restart_digest_"
                "stale_observation"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_restart_digest_"
                "prolonged_outage_duration"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_restart_digest_"
                "low_restart_probability"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_restart_digest_"
                "material_capacity_offline"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_restart_digest_"
                "product_spread_pressure"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_restart_digest_thin_sources"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.event_config_versions == (
        ("energy.refinery.restart.gulf", "refinery-restart-v0"),
        ("energy.refinery.restart.midcon", "refinery-restart-v1"),
        ("energy.refinery.restart.rotterdam", "refinery-restart-v2"),
    )


def test_refinery_outage_restart_digest_passes_clean_fresh_events() -> None:
    module = api()
    summary = report(
        module,
        (
            input_row(module, "energy.refinery.restart.alpha", refinery_id="alpha"),
            input_row(
                module,
                "energy.refinery.restart.beta",
                refinery_id="beta",
                restart_probability=d("0.900000"),
            ),
        ),
    )

    assert summary.digest_status == "pass"
    assert summary.recommended_next_step == (
        "allow_report_only_market_research_energy_refinery_outage_restart_digest"
    )
    assert summary.reason_codes == (
        "market_research_energy_refinery_outage_restart_digest_passed",
    )
    assert summary.reason_code_counts == (
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_restart_digest_passed",
            count=d("2.000000"),
            event_ratio=d("1.000000"),
        ),
    )


def test_empty_refinery_outage_restart_digest_is_blocked_report_only() -> None:
    module = api()
    summary = report(module, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_refinery_outage_restart_digest"
    )
    assert summary.event_count == ZERO
    assert summary.pass_event_count == ZERO
    assert summary.watch_event_count == ZERO
    assert summary.blocked_event_count == ZERO
    assert summary.total_offline_capacity_bpd == ZERO
    assert summary.average_outage_duration_hours == ZERO
    assert summary.average_restart_probability == ZERO
    assert summary.max_utilization_capacity_offline_ratio == ZERO
    assert summary.max_product_spread_impact_pressure == ZERO
    assert summary.rows == ()
    assert summary.event_config_versions == ()
    assert summary.reason_codes == (
        "market_research_energy_refinery_outage_restart_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_restart_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=ZERO,
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_refinery_outage_restart_payload_uses_six_decimal_strings() -> None:
    module = api()
    summary = report(module, (input_row(module),))
    payload = module.market_research_energy_refinery_outage_restart_digest_payload(
        summary,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T16:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["average_restart_probability"] == "0.820000"
    assert payload["rows"][0]["outage_duration_hours"] == "6.000000"
    assert payload["rows"][0]["restart_probability"] == "0.820000"
    assert payload["rows"][0]["utilization_capacity_offline_ratio"] == "0.100000"
    assert payload["rows"][0]["product_spread_impact_pressure"] == "0.150000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_source_ref':" not in repr(payload)
    assert "sensitive" not in repr(payload).lower()


def test_refinery_outage_restart_validates_contracts_and_flags() -> None:
    module = api()

    for dataclass_type in (
        module.MarketResearchEnergyRefineryOutageRestartDigestConfig,
        module.MarketResearchEnergyRefineryOutageRestartDigestInputRow,
        module.MarketResearchEnergyRefineryOutageRestartDigestRow,
        module.MarketResearchEnergyRefineryOutageRestartDigestReport,
        module.MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount,
    ):
        assert dataclass_type.__dataclass_params__.frozen

    summary = report(module, (input_row(module),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].restart_probability = d("0.100000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (module.MarketResearchEnergyRefineryOutageRestartDigestConfig,),
            {},
        )
    with pytest.raises(ValueError, match="config_version"):
        config(module, config_version=_StringSubclass("bad-version"))
    with pytest.raises(ValueError, match="max_observation_age_seconds"):
        config(module, max_observation_age_seconds=_DecimalSubclass("10800.000000"))
    with pytest.raises(ValueError, match="blocked_restart_probability"):
        config(
            module,
            watch_restart_probability=d("0.300000"),
            blocked_restart_probability=d("0.400000"),
        )
    with pytest.raises(ValueError, match="event_id"):
        input_row(module, event_id=" bad")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(module, observed_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="restart_probability"):
        input_row(module, restart_probability=d("1.000001"))
    with pytest.raises(ValueError, match="source_count"):
        input_row(module, source_count=d("1.500000"))
    with pytest.raises(ValueError, match="offline_capacity_bpd"):
        input_row(
            module,
            offline_capacity_bpd=d("600000.000000"),
            total_capacity_bpd=d("500000.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        input_row(module, paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            module,
            (input_row(module),),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            module,
            (input_row(module, outage_started_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_energy_refinery_outage_restart_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    for value in (
        config(module),
        input_row(module),
        summary,
        summary.rows[0],
        summary.reason_code_counts[0],
    ):
        assert_decimal_public_numeric_fields(value)


def test_refinery_outage_restart_module_has_no_forbidden_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "keys",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "db",
        "database",
        "file",
        "network",
        "subprocess",
        "socket",
        "http",
        "psycopg",
        "supabase",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "pathlib",
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
        "subprocess",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
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
        "trade",
    )

    for imported in imported_modules:
        assert not any(fragment in imported for fragment in forbidden_import_fragments)
    for name in call_names + attribute_names:
        assert name not in forbidden_call_or_attribute_names


def walk_values(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_values(item)
        return
    yield value


def assert_decimal_public_numeric_fields(value: Any) -> None:
    assert is_dataclass(value)
    for hint in get_type_hints(type(value)).values():
        assert not type_uses_float(hint)
    for field in fields(value):
        if is_public_numeric(field.name):
            field_value = getattr(value, field.name)
            assert field_value is None or type(field_value) is Decimal


def type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(type_uses_float(arg) for arg in getattr(hint, "__args__", ()))


def is_public_numeric(field_name: str) -> bool:
    if field_name in {"reason_code_counts", "event_config_versions"}:
        return False
    return any(
        token in field_name
        for token in (
            "count",
            "ratio",
            "pressure",
            "probability",
            "seconds",
            "hours",
            "bpd",
        )
    )
