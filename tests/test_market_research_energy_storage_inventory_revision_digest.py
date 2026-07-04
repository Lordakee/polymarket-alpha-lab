from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest

from polymarket_alpha_lab.market_research_energy_storage_inventory_revision_digest import (
    DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION,
    MarketResearchEnergyStorageInventoryRevisionDigestConfig,
    MarketResearchEnergyStorageInventoryRevisionDigestInputRow,
    MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount,
    MarketResearchEnergyStorageInventoryRevisionDigestReport,
    MarketResearchEnergyStorageInventoryRevisionDigestRow,
    build_market_research_energy_storage_inventory_revision_digest,
    market_research_energy_storage_inventory_revision_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_energy_storage_inventory_revision_digest.py"
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEnergyStorageInventoryRevisionDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "watch_revision_ratio": d("0.050000"),
        "blocked_revision_ratio": d("0.150000"),
        "watch_surprise_ratio": d("0.050000"),
        "blocked_surprise_ratio": d("0.150000"),
        "cluster_min_report_count": d("2.000000"),
        "probability_repricing_threshold": d("0.070000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchEnergyStorageInventoryRevisionDigestConfig(**values)


def input_row(
    research_key: str = "research.energy.oil.eia",
    *,
    condition_id: str = "condition_energy_oil_inventory",
    market_slug: str = "oil-weekly-inventory",
    inventory_report_key: str = "eia.oil.weekly",
    commodity_family: str = "oil",
    inventory_report_reference: str = "public-eia-energy-calendar",
    released_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    initial_inventory_level: Decimal = d("1000.000000"),
    revised_inventory_level: Decimal = d("1030.000000"),
    expected_inventory_level: Decimal = d("1000.000000"),
    market_probability_before: Decimal = d("0.470000"),
    market_probability_after: Decimal = d("0.530000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEnergyStorageInventoryRevisionDigestInputRow:
    return MarketResearchEnergyStorageInventoryRevisionDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        inventory_report_key=inventory_report_key,
        commodity_family=commodity_family,
        inventory_report_reference=inventory_report_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=40),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=35)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        initial_inventory_level=initial_inventory_level,
        revised_inventory_level=revised_inventory_level,
        expected_inventory_level=expected_inventory_level,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchEnergyStorageInventoryRevisionDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEnergyStorageInventoryRevisionDigestReport:
    return build_market_research_energy_storage_inventory_revision_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_energy_storage_inventory_revision_digest_reduces_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.energy.storage.iso",
                condition_id="condition_storage_inventory",
                market_slug="battery-storage-inventory",
                inventory_report_key="iso.storage.daily",
                commodity_family="storage",
                initial_inventory_level=d("1000.000000"),
                revised_inventory_level=d("1010.000000"),
                expected_inventory_level=d("1005.000000"),
                source_count=d("4.000000"),
                market_probability_before=d("0.500000"),
                market_probability_after=d("0.510000"),
            ),
            input_row(
                "research.energy.oil.primary",
                condition_id="condition_oil_inventory_primary",
                market_slug="oil-weekly-inventory",
                inventory_report_key="eia.oil.primary",
                commodity_family="oil",
                inventory_report_reference="https://vendor.example/oil?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=80),
                source_count=d("1.000000"),
                initial_inventory_level=d("1000.000000"),
                revised_inventory_level=d("1070.000000"),
                expected_inventory_level=d("1000.000000"),
                market_probability_before=d("0.470000"),
                market_probability_after=d("0.530000"),
            ),
            input_row(
                "research.energy.oil.secondary",
                condition_id="condition_oil_inventory_secondary",
                market_slug="oil-refined-products",
                inventory_report_key="eia.oil.secondary",
                commodity_family="oil",
                inventory_report_reference="private-oil-feed",
                source_count=d("3.000000"),
                initial_inventory_level=d("1000.000000"),
                revised_inventory_level=d("1060.000000"),
                expected_inventory_level=d("1000.000000"),
                market_probability_before=d("0.520000"),
                market_probability_after=d("0.570000"),
            ),
            input_row(
                "research.energy.gas.eia",
                condition_id="condition_gas_inventory",
                market_slug="gas-weekly-storage",
                inventory_report_key="eia.gas.weekly",
                commodity_family="gas",
                inventory_report_reference="public-gas-storage-calendar",
                released_at=datetime(
                    2026,
                    7,
                    4,
                    5,
                    0,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                acknowledged_at=None,
                source_count=d("1.000000"),
                initial_inventory_level=d("1000.000000"),
                revised_inventory_level=d("1220.000000"),
                expected_inventory_level=d("1000.000000"),
                market_probability_before=d("0.410000"),
                market_probability_after=d("0.590000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert type(summary) is MarketResearchEnergyStorageInventoryRevisionDigestReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        "market-research-energy-storage-inventory-revision-digest-v0"
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_storage_inventory_revision_digest"
    )
    assert summary.inventory_report_count == d("4.000000")
    assert summary.pass_report_count == d("1.000000")
    assert summary.watch_report_count == d("2.000000")
    assert summary.blocked_report_count == d("1.000000")
    assert summary.material_revision_count == d("3.000000")
    assert summary.material_surprise_count == d("3.000000")
    assert summary.surprise_cluster_count == d("2.000000")
    assert summary.stale_release_count == d("2.000000")
    assert summary.thin_source_count == d("2.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.average_revision_abs_ratio == d("0.090000")
    assert summary.max_revision_abs_ratio == d("0.220000")
    assert summary.max_surprise_abs_ratio == d("0.220000")
    assert summary.max_release_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.250000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.revision_status, row.commodity_family) for row in summary.rows) == (
        ("blocked", "gas"),
        ("watch", "oil"),
        ("watch", "oil"),
        ("pass", "storage"),
    )

    gas = summary.rows[0]
    assert type(gas) is MarketResearchEnergyStorageInventoryRevisionDigestRow
    assert gas.released_at == datetime(2026, 7, 4, 9, 0, tzinfo=UTC)
    assert gas.acknowledged_at is None
    assert gas.release_age_seconds == d("10800.000000")
    assert gas.acknowledgement_lag_seconds is None
    assert gas.revision_delta == d("220.000000")
    assert gas.revision_abs == d("220.000000")
    assert gas.revision_abs_ratio == d("0.220000")
    assert gas.inventory_surprise == d("220.000000")
    assert gas.surprise_abs_ratio == d("0.220000")
    assert gas.probability_delta == d("0.180000")
    assert gas.revision_status == "blocked"
    assert gas.reason_codes == (
        "market_research_energy_storage_inventory_revision_digest_material_revision",
        "market_research_energy_storage_inventory_revision_digest_material_surprise",
        "market_research_energy_storage_inventory_revision_digest_probability_repricing",
        "market_research_energy_storage_inventory_revision_digest_missing_acknowledgement",
        "market_research_energy_storage_inventory_revision_digest_stale_release",
        "market_research_energy_storage_inventory_revision_digest_thin_sources",
    )

    primary_oil = summary.rows[1]
    assert primary_oil.revision_status == "watch"
    assert primary_oil.acknowledgement_lag_seconds == d("6000.000000")
    assert primary_oil.reason_codes == (
        "market_research_energy_storage_inventory_revision_digest_material_revision",
        "market_research_energy_storage_inventory_revision_digest_material_surprise",
        "market_research_energy_storage_inventory_revision_digest_surprise_cluster",
        "market_research_energy_storage_inventory_revision_digest_slow_acknowledgement",
        "market_research_energy_storage_inventory_revision_digest_stale_release",
        "market_research_energy_storage_inventory_revision_digest_thin_sources",
    )
    assert primary_oil.redacted_inventory_report_reference.startswith("sha256:")

    storage = summary.rows[3]
    assert storage.revision_status == "pass"
    assert storage.reason_codes == (
        "market_research_energy_storage_inventory_revision_digest_pass",
    )

    assert summary.reason_code_counts == (
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "material_revision"
            ),
            count=d("3.000000"),
            report_ratio=d("0.750000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "material_surprise"
            ),
            count=d("3.000000"),
            report_ratio=d("0.750000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "surprise_cluster"
            ),
            count=d("2.000000"),
            report_ratio=d("0.500000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "probability_repricing"
            ),
            count=d("1.000000"),
            report_ratio=d("0.250000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            report_ratio=d("0.250000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code="market_research_energy_storage_inventory_revision_digest_pass",
            count=d("1.000000"),
            report_ratio=d("0.250000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            report_ratio=d("0.250000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "stale_release"
            ),
            count=d("2.000000"),
            report_ratio=d("0.500000"),
        ),
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_storage_inventory_revision_digest_"
                "thin_sources"
            ),
            count=d("2.000000"),
            report_ratio=d("0.500000"),
        ),
    )
    assert summary.reason_codes == tuple(row.reason_code for row in summary.reason_code_counts)

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-oil-feed",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_empty_energy_storage_inventory_revision_digest_is_blocked_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_storage_inventory_revision_digest"
    )
    assert summary.inventory_report_count == ZERO
    assert summary.pass_report_count == ZERO
    assert summary.watch_report_count == ZERO
    assert summary.blocked_report_count == ZERO
    assert summary.average_revision_abs_ratio == ZERO
    assert summary.max_revision_abs_ratio == ZERO
    assert summary.max_surprise_abs_ratio == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code="market_research_energy_storage_inventory_revision_digest_no_inputs",
            count=d("1.000000"),
            report_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_energy_storage_inventory_revision_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_uses_six_decimal_strings_and_no_public_floats() -> None:
    summary = report((input_row(),))
    payload = market_research_energy_storage_inventory_revision_digest_payload(summary)

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload == market_research_energy_storage_inventory_revision_digest_payload(summary)
    assert _float_paths(payload) == ()
    assert _decimal_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["inventory_report_count"] == "1.000000"
    assert payload["average_revision_abs_ratio"] == "0.030000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["revision_delta"] == "30.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert all(item["paper_only"] is True for item in payload["rows"])
    assert all(item["report_only"] is True for item in payload["rows"])
    assert all(item["readonly"] is True for item in payload["rows"])
    assert all(item["paper_only"] is True for item in payload["reason_code_counts"])
    assert all(item["report_only"] is True for item in payload["reason_code_counts"])
    assert all(item["readonly"] is True for item in payload["reason_code_counts"])

    for value in _walk_dataclasses(summary):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float(hint)
        for field in fields(value):
            field_value = getattr(value, field.name)
            if _is_public_numeric(field.name):
                assert field_value is None or type(field_value) is Decimal, field.name


def test_validates_inputs_staleness_flags_and_manual_consistency() -> None:
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="revised_inventory_level"):
        input_row(revised_inventory_level=_DecimalSubclass("1000.000000"))
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            acknowledged_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="commodity_family"):
        input_row(commodity_family="power")
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="watch_revision_ratio"):
        config(watch_revision_ratio=d("0.000000"))
    with pytest.raises(ValueError, match="blocked_revision_ratio"):
        config(blocked_revision_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="cluster_min_report_count"):
        config(cluster_min_report_count=d("1.500000"))
    with pytest.raises(ValueError, match="config"):
        build_market_research_energy_storage_inventory_revision_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="released_at"):
        report((input_row(released_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="acknowledged_at"):
        report((input_row(acknowledged_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="acknowledged_at"):
        report(
            (
                input_row(
                    released_at=GENERATED_AT - timedelta(minutes=10),
                    acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                ),
            ),
        )
    with pytest.raises(ValueError, match="unique research condition report keys"):
        report((input_row(), input_row()))
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))

    summary = report(
        (
            input_row("research.energy.oil.z", inventory_report_key="z.report"),
            input_row(),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="revision_status"):
        replace(summary.rows[0], revision_status="blocked")
    with pytest.raises(ValueError, match="revision_delta"):
        replace(summary.rows[0], revision_delta=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            summary.rows[0],
            reason_codes=(
                "market_research_energy_storage_inventory_revision_digest_pass",
                "market_research_energy_storage_inventory_revision_digest_material_revision",
            ),
        )
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())


def test_static_source_has_no_live_io_or_secret_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "token",
        "requests",
        "http",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_or_attribute_names = {
        "cancel_order",
        "connect",
        "create_order",
        "delete",
        "execute",
        "fetch",
        "mkdir",
        "open",
        "place_order",
        "post",
        "put",
        "read",
        "rename",
        "replace_order",
        "request",
        "submit_order",
        "unlink",
        "urlopen",
        "wallet",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_or_attribute_names
                assert call.id != "float"
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_or_attribute_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_call_or_attribute_names


def _walk_dataclasses(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if is_dataclass(value) and not isinstance(value, type):
        found.append(value)
        for field in fields(value):
            found.extend(_walk_dataclasses(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            found.extend(_walk_dataclasses(item))
    return tuple(found)


def _is_public_numeric(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_seconds")
        or field_name.endswith("_level")
        or field_name.endswith("_delta")
        or field_name.endswith("_abs")
        or field_name.startswith("market_probability_")
    )


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _decimal_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) is Decimal:
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_decimal_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_decimal_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
