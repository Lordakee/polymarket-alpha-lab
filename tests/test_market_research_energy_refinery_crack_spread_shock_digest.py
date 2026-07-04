from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_energy_refinery_crack_spread_shock_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_energy_refinery_crack_spread_shock_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


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
            module.DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION
        ),
        "fresh_observation_max_age_seconds": d("3600.000000"),
        "max_acknowledgement_lag_seconds": d("900.000000"),
        "min_source_count": d("2.000000"),
        "material_crack_spread_move_usd_per_bbl": d("5.000000"),
        "material_crack_spread_move_ratio": d("0.080000"),
        "high_utilization_rate": d("0.920000"),
        "max_feedstock_dislocation_score": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchEnergyRefineryCrackSpreadShockDigestConfig(**values)


def input_row(
    module: Any,
    research_key: str = "energy.refinery.crack.ready",
    *,
    condition_id: str = "condition_gulf_321",
    market_slug: str = "gulf-coast-321-crack-stable",
    refinery_region: str = "us-gulf",
    product_group: str = "gasoline-distillate",
    public_crack_spread_reference: str = "eia-public-crack-spread-note",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    baseline_crack_spread_usd_per_bbl: Decimal = d("25.000000"),
    observed_crack_spread_usd_per_bbl: Decimal = d("26.000000"),
    intraday_crack_spread_move_ratio: Decimal = d("0.020000"),
    refinery_utilization_rate: Decimal = d("0.850000"),
    feedstock_dislocation_score: Decimal = d("0.200000"),
    source_config_version: str = "energy-refinery-crack-spread-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        refinery_region=refinery_region,
        product_group=product_group,
        public_crack_spread_reference=public_crack_spread_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=5)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        baseline_crack_spread_usd_per_bbl=baseline_crack_spread_usd_per_bbl,
        observed_crack_spread_usd_per_bbl=observed_crack_spread_usd_per_bbl,
        intraday_crack_spread_move_ratio=intraday_crack_spread_move_ratio,
        refinery_utilization_rate=refinery_utilization_rate,
        feedstock_dislocation_score=feedstock_dislocation_score,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    module: Any,
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_market_research_energy_refinery_crack_spread_shock_digest(
        rows,
        config=cfg or config(module),
        generated_at=generated_at,
    )


def redacted(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def test_refinery_crack_spread_shock_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_refinery_crack_spread_shock_digest_reduces_rows_deterministically() -> None:
    module = api()

    summary = report(
        module,
        (
            input_row(
                module,
                "energy.refinery.crack.watch",
                condition_id="condition_brent_crack",
                market_slug="brent-gasoline-crack-spike",
                refinery_region="europe",
                product_group="gasoline",
                public_crack_spread_reference="operator-internal-crack-feed",
                observed_at=GENERATED_AT - timedelta(minutes=50),
                acknowledged_at=GENERATED_AT - timedelta(minutes=25),
                source_count=d("2.000000"),
                baseline_crack_spread_usd_per_bbl=d("20.000000"),
                observed_crack_spread_usd_per_bbl=d("26.000000"),
                intraday_crack_spread_move_ratio=d("0.100000"),
                refinery_utilization_rate=d("0.930000"),
                feedstock_dislocation_score=d("0.720000"),
                source_config_version="energy-refinery-crack-spread-source-v1",
            ),
            input_row(module),
            input_row(
                module,
                "energy.refinery.crack.blocked",
                condition_id="condition_heat_crack",
                market_slug="heating-oil-crack-compression",
                refinery_region="us-midcon",
                product_group="distillate",
                public_crack_spread_reference=(
                    "https://vendor.example/crack?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("1.000000"),
                baseline_crack_spread_usd_per_bbl=d("30.000000"),
                observed_crack_spread_usd_per_bbl=d("21.000000"),
                intraday_crack_spread_move_ratio=d("-0.120000"),
                refinery_utilization_rate=d("0.950000"),
                feedstock_dislocation_score=d("0.800000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_refinery_crack_spread_shock_digest"
    )
    assert summary.crack_spread_shock_count == d("3.000000")
    assert summary.ready_shock_count == d("1.000000")
    assert summary.watch_shock_count == d("1.000000")
    assert summary.blocked_shock_count == d("1.000000")
    assert summary.material_crack_spread_move_count == d("2.000000")
    assert summary.margin_compression_count == d("1.000000")
    assert summary.margin_expansion_count == d("1.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.high_utilization_count == d("2.000000")
    assert summary.feedstock_dislocation_count == d("2.000000")
    assert summary.average_abs_crack_spread_change_usd_per_bbl == d("5.333333")
    assert summary.max_abs_crack_spread_change_usd_per_bbl == d("9.000000")
    assert summary.average_abs_crack_spread_move_ratio == d("0.213333")
    assert summary.max_observation_age_seconds == d("14400.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.market_slug for row in summary.rows) == (
        "heating-oil-crack-compression",
        "brent-gasoline-crack-spike",
        "gulf-coast-321-crack-stable",
    )

    blocked = summary.rows[0]
    assert blocked.shock_status == "blocked"
    assert blocked.observation_age_seconds == d("14400.000000")
    assert blocked.acknowledgement_lag_seconds is None
    assert blocked.source_gap_count == d("1.000000")
    assert blocked.crack_spread_change_usd_per_bbl == d("-9.000000")
    assert blocked.crack_spread_move_ratio == d("-0.300000")
    assert blocked.redacted_public_crack_spread_reference == redacted(
        "https://vendor.example/crack?token=secret-123",
    )
    assert blocked.reason_codes == (
        "market_research_energy_refinery_crack_spread_shock_digest_material_crack_spread_move",
        "market_research_energy_refinery_crack_spread_shock_digest_margin_compression",
        "market_research_energy_refinery_crack_spread_shock_digest_high_utilization",
        "market_research_energy_refinery_crack_spread_shock_digest_feedstock_dislocation",
        "market_research_energy_refinery_crack_spread_shock_digest_missing_acknowledgement",
        "market_research_energy_refinery_crack_spread_shock_digest_stale_observation",
        "market_research_energy_refinery_crack_spread_shock_digest_thin_sources",
    )

    watched = summary.rows[1]
    assert watched.shock_status == "watch"
    assert watched.observation_age_seconds == d("3000.000000")
    assert watched.acknowledgement_lag_seconds == d("1500.000000")
    assert watched.source_gap_count == ZERO
    assert watched.crack_spread_change_usd_per_bbl == d("6.000000")
    assert watched.crack_spread_move_ratio == d("0.300000")
    assert watched.redacted_public_crack_spread_reference == redacted(
        "operator-internal-crack-feed",
    )
    assert watched.reason_codes == (
        "market_research_energy_refinery_crack_spread_shock_digest_material_crack_spread_move",
        "market_research_energy_refinery_crack_spread_shock_digest_margin_expansion",
        "market_research_energy_refinery_crack_spread_shock_digest_high_utilization",
        "market_research_energy_refinery_crack_spread_shock_digest_feedstock_dislocation",
        "market_research_energy_refinery_crack_spread_shock_digest_slow_acknowledgement",
    )

    ready = summary.rows[2]
    assert ready.shock_status == "ready"
    assert ready.observation_age_seconds == d("1200.000000")
    assert ready.acknowledgement_lag_seconds == d("900.000000")
    assert ready.crack_spread_change_usd_per_bbl == d("1.000000")
    assert ready.crack_spread_move_ratio == d("0.040000")
    assert ready.redacted_public_crack_spread_reference == (
        "eia-public-crack-spread-note"
    )
    assert ready.reason_codes == (
        "market_research_energy_refinery_crack_spread_shock_digest_ready",
    )

    assert summary.reason_code_counts == (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "material_crack_spread_move"
            ),
            count=d("2.000000"),
            shock_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "margin_compression"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "margin_expansion"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "high_utilization"
            ),
            count=d("2.000000"),
            shock_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "feedstock_dislocation"
            ),
            count=d("2.000000"),
            shock_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "stale_observation"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_"
                "thin_sources"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_ready"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.source_config_versions == (
        (
            "brent-gasoline-crack-spike",
            "energy-refinery-crack-spread-source-v1",
        ),
        (
            "gulf-coast-321-crack-stable",
            "energy-refinery-crack-spread-source-v0",
        ),
        (
            "heating-oil-crack-compression",
            "energy-refinery-crack-spread-source-v0",
        ),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "operator-internal-crack-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
        "order",
    ):
        assert token not in public


def test_empty_refinery_crack_spread_shock_digest_is_blocked_report_only() -> None:
    module = api()
    summary = report(module, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_refinery_crack_spread_shock_digest"
    )
    assert summary.crack_spread_shock_count == ZERO
    assert summary.ready_shock_count == ZERO
    assert summary.watch_shock_count == ZERO
    assert summary.blocked_shock_count == ZERO
    assert summary.average_abs_crack_spread_change_usd_per_bbl == ZERO
    assert summary.max_abs_crack_spread_change_usd_per_bbl == ZERO
    assert summary.average_abs_crack_spread_move_ratio == ZERO
    assert summary.max_observation_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.source_config_versions == ()
    assert summary.reason_code_counts == (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_crack_spread_shock_digest_no_inputs"
            ),
            count=d("1.000000"),
            shock_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_energy_refinery_crack_spread_shock_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_refinery_crack_spread_shock_accepts_above_one_move_ratio() -> None:
    module = api()

    summary = report(
        module,
        (
            input_row(
                module,
                "energy.refinery.crack.above-one",
                condition_id="condition_above_one",
                market_slug="gulf-crack-spread-doubles",
                baseline_crack_spread_usd_per_bbl=d("10.000000"),
                observed_crack_spread_usd_per_bbl=d("25.000000"),
                intraday_crack_spread_move_ratio=d("0.500000"),
            ),
        ),
    )

    assert summary.digest_status == "watch"
    assert summary.average_abs_crack_spread_move_ratio == d("1.500000")
    assert summary.rows[0].crack_spread_change_usd_per_bbl == d("15.000000")
    assert summary.rows[0].crack_spread_move_ratio == d("1.500000")
    assert (
        "market_research_energy_refinery_crack_spread_shock_digest_material_crack_spread_move"
        in summary.rows[0].reason_codes
    )


def test_refinery_crack_spread_shock_payload_uses_decimal_strings() -> None:
    module = api()
    summary = report(module, (input_row(module),))
    payload = module.market_research_energy_refinery_crack_spread_shock_digest_payload(
        summary,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T16:00:00+00:00"
    assert payload["crack_spread_shock_count"] == "1.000000"
    assert payload["average_abs_crack_spread_move_ratio"] == "0.040000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["crack_spread_change_usd_per_bbl"] == "1.000000"
    assert payload["rows"][0]["crack_spread_move_ratio"] == "0.040000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_crack_spread_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_refinery_crack_spread_shock_validates_contracts_and_flags() -> None:
    module = api()

    assert (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestConfig
        .__dataclass_params__
        .frozen
    )
    assert (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow
        .__dataclass_params__
        .frozen
    )
    assert (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestRow
        .__dataclass_params__
        .frozen
    )
    assert (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert (
        module.MarketResearchEnergyRefineryCrackSpreadShockDigestReport
        .__dataclass_params__
        .frozen
    )

    summary = report(module, (input_row(module),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].source_count = d("4.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(module, config_version=_StringSubclass("crack-spread-v0"))
    with pytest.raises(ValueError, match="fresh_observation_max_age_seconds"):
        config(
            module,
            fresh_observation_max_age_seconds=_DecimalSubclass("3600.000000"),
        )
    with pytest.raises(ValueError, match="min_source_count"):
        config(module, min_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="material_crack_spread_move_ratio"):
        config(module, material_crack_spread_move_ratio=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(module, _StringSubclass("energy.bad"))
    with pytest.raises(ValueError, match="market_slug"):
        input_row(module, market_slug="Energy Crack Spread Shock")
    with pytest.raises(ValueError, match="refinery_region"):
        input_row(module, refinery_region="broker-feed")
    with pytest.raises(ValueError, match="public_crack_spread_reference"):
        input_row(module, public_crack_spread_reference=" ")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(module, observed_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            module,
            acknowledged_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_count"):
        input_row(module, source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline_crack_spread_usd_per_bbl"):
        input_row(module, baseline_crack_spread_usd_per_bbl=d("0.000000"))
    with pytest.raises(ValueError, match="observed_crack_spread_usd_per_bbl"):
        input_row(module, observed_crack_spread_usd_per_bbl=Decimal("NaN"))
    with pytest.raises(ValueError, match="intraday_crack_spread_move_ratio"):
        input_row(module, intraday_crack_spread_move_ratio=d("-1.000001"))
    with pytest.raises(ValueError, match="refinery_utilization_rate"):
        input_row(module, refinery_utilization_rate=d("1.000001"))
    with pytest.raises(ValueError, match="feedstock_dislocation_score"):
        input_row(
            module,
            feedstock_dislocation_score=_DecimalSubclass("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        input_row(module, paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            module,
            (),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report(module, (object(),))
    with pytest.raises(ValueError, match="future"):
        report(
            module,
            (
                input_row(
                    module,
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="acknowledged_at"):
        report(
            module,
            (
                input_row(
                    module,
                    observed_at=GENERATED_AT - timedelta(minutes=5),
                    acknowledged_at=GENERATED_AT - timedelta(minutes=6),
                ),
            ),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_energy_refinery_crack_spread_shock_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (
                module.MarketResearchEnergyRefineryCrackSpreadShockDigestConfig,
            ),
            {},
        )


def test_refinery_crack_spread_shock_rejects_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_slug"):
        report(
            module,
            (
                input_row(module, market_slug="duplicate-crack-market"),
                input_row(
                    module,
                    "energy.refinery.crack.duplicate",
                    condition_id="condition_duplicate",
                    market_slug="duplicate-crack-market",
                ),
            ),
        )

    ready = report(module, (input_row(module),)).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_energy_refinery_crack_spread_shock_digest_ready",
                "market_research_energy_refinery_crack_spread_shock_digest_material_crack_spread_move",
            ),
        )
    with pytest.raises(ValueError, match="shock_status"):
        replace(ready, shock_status="blocked")
    with pytest.raises(ValueError, match="crack_spread_change_usd_per_bbl"):
        replace(ready, crack_spread_change_usd_per_bbl=d("9.000000"))
    with pytest.raises(ValueError, match="redacted_public_crack_spread_reference"):
        replace(
            ready,
            redacted_public_crack_spread_reference="https://host?token=secret",
        )

    with pytest.raises(ValueError, match="ready_shock_count"):
        replace(report(module, (input_row(module),)), ready_shock_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            module,
            (
                input_row(
                    module,
                    "energy.refinery.crack.z",
                    condition_id="condition_z",
                    market_slug="z-crack-market",
                ),
                input_row(module),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    module = api()
    summary = report(module, (input_row(module),))

    for value in (
        config(module),
        input_row(module),
        summary,
        summary.rows[0],
        summary.reason_code_counts[0],
    ):
        assert_decimal_public_numeric_fields(value)


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
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
        "db",
        "env",
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
        "subprocess",
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
        "auth",
        "sign",
        "session",
        "commit",
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
    if field_name.endswith("_at"):
        return False
    if field_name in {"reason_code_counts", "source_config_versions"}:
        return False
    return any(
        token in field_name
        for token in (
            "count",
            "ratio",
            "score",
            "seconds",
            "rate",
            "usd_per_bbl",
        )
    )
