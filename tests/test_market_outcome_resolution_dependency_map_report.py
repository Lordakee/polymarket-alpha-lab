from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import ast
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_outcome_resolution_dependency_map_report import (
    DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION,
    MarketOutcomeResolutionDependencyMapConfig,
    MarketOutcomeResolutionDependencyMapInput,
    MarketOutcomeResolutionDependencyMapReport,
    MarketOutcomeResolutionDependencyMapRow,
    build_market_outcome_resolution_dependency_map_report,
    market_outcome_resolution_dependency_map_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_resolution_dependency_map_report.py"
)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def market(
    market_ref: str,
    *,
    resolution_source_refs: tuple[str, ...] = ("official-source",),
    dependency_count: Decimal = d("1.000000"),
    official_source_present: bool = True,
    ambiguous_dependency_count: Decimal = ZERO,
    refresh_age_hours: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketOutcomeResolutionDependencyMapInput:
    return MarketOutcomeResolutionDependencyMapInput(
        market_ref=market_ref,
        resolution_source_refs=resolution_source_refs,
        dependency_count=dependency_count,
        official_source_present=official_source_present,
        ambiguous_dependency_count=ambiguous_dependency_count,
        refresh_age_hours=refresh_age_hours,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: MarketOutcomeResolutionDependencyMapInput,
    config: MarketOutcomeResolutionDependencyMapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketOutcomeResolutionDependencyMapReport:
    return build_market_outcome_resolution_dependency_map_report(
        rows,
        generated_at=generated_at,
        config=MarketOutcomeResolutionDependencyMapConfig() if config is None else config,
    )


def test_report_maps_dependency_statuses_reasons_and_manual_next_steps() -> None:
    dependency_report = report(
        market("market-pass", dependency_count=ZERO, resolution_source_refs=()),
        market(
            "market-watch",
            resolution_source_refs=("official-source", "secondary-source"),
            dependency_count=d("2.000000"),
            ambiguous_dependency_count=d("1.000000"),
            refresh_age_hours=d("5.500000"),
        ),
        market(
            "market-block",
            resolution_source_refs=("secondary-source",),
            dependency_count=d("4.000000"),
            official_source_present=False,
            ambiguous_dependency_count=d("2.000000"),
            refresh_age_hours=d("30.000000"),
        ),
    )

    assert dependency_report.config_version == (
        DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION
    )
    assert dependency_report.market_count == d("3.000000")
    assert dependency_report.pass_count == d("1.000000")
    assert dependency_report.watch_count == d("1.000000")
    assert dependency_report.block_count == d("1.000000")
    assert dependency_report.official_source_present_count == d("2.000000")
    assert dependency_report.ambiguous_dependency_count == d("3.000000")
    assert dependency_report.status == "block"
    assert dependency_report.reason_codes == (
        "outcome_resolution_dependency_map_report_block",
        "missing_official_resolution_source",
        "stale_resolution_dependency_map",
        "dependency_count_block",
        "ambiguous_dependency_count_block",
        "dependency_count_watch",
        "ambiguous_dependency_count_watch",
        "no_resolution_dependencies",
        "official_resolution_source_present",
        "resolution_dependency_map_fresh",
    )

    pass_row, watch_row, block_row = dependency_report.rows
    assert pass_row.market_ref == "market-pass"
    assert pass_row.dependency_status == "pass"
    assert pass_row.resolution_source_refs == ()
    assert pass_row.manual_next_step == "monitor_standard_resolution_path"
    assert pass_row.reason_codes == (
        "no_resolution_dependencies",
        "official_resolution_source_present",
        "resolution_dependency_map_fresh",
    )

    assert watch_row.market_ref == "market-watch"
    assert watch_row.dependency_status == "watch"
    assert watch_row.manual_next_step == "review_ambiguous_resolution_dependencies"
    assert watch_row.reason_codes == (
        "dependency_count_watch",
        "ambiguous_dependency_count_watch",
        "official_resolution_source_present",
        "resolution_dependency_map_fresh",
    )

    assert block_row.market_ref == "market-block"
    assert block_row.dependency_status == "block"
    assert block_row.manual_next_step == "escalate_missing_official_resolution_source"
    assert block_row.reason_codes == (
        "missing_official_resolution_source",
        "stale_resolution_dependency_map",
        "dependency_count_block",
        "ambiguous_dependency_count_block",
    )


def test_payload_is_public_readonly_decimal_only_and_deterministic() -> None:
    dependency_report = report(
        market(
            "market-z",
            resolution_source_refs=("source-beta", "source-alpha", "source-alpha"),
            dependency_count=d("2.000000"),
        ),
        market("market-a", dependency_count=ZERO, resolution_source_refs=()),
    )
    payload = market_outcome_resolution_dependency_map_report_payload(dependency_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.market_ref for row in dependency_report.rows) == (
        "market-a",
        "market-z",
    )
    assert dependency_report.rows[1].resolution_source_refs == (
        "source-alpha",
        "source-beta",
    )
    assert payload["market_count"] == "2.000000"
    assert payload["rows"][0]["dependency_count"] == "0.000000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in encoded.lower()
    assert "order" not in encoded.lower()
    assert "trade" not in encoded.lower()
    assert "recommend" not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_values(payload))


def test_empty_report_blocks_for_manual_mapping_seed() -> None:
    dependency_report = report()

    assert dependency_report.status == "block"
    assert dependency_report.market_count == ZERO
    assert dependency_report.pass_count == ZERO
    assert dependency_report.watch_count == ZERO
    assert dependency_report.block_count == ZERO
    assert dependency_report.rows == ()
    assert dependency_report.reason_codes == ("no_market_resolution_dependency_inputs",)


def test_validation_rejects_bad_types_statuses_flags_and_inconsistent_rows() -> None:
    with pytest.raises(ValueError, match="watch_dependency_count"):
        MarketOutcomeResolutionDependencyMapConfig(
            watch_dependency_count=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="block_dependency_count"):
        MarketOutcomeResolutionDependencyMapConfig(
            watch_dependency_count=d("4.000000"),
            block_dependency_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="watch_refresh_age_hours"):
        MarketOutcomeResolutionDependencyMapConfig(
            watch_refresh_age_hours=DecimalSubclass("12.000000"),
        )
    with pytest.raises(ValueError, match="market_ref"):
        market("bad market ref")
    with pytest.raises(ValueError, match="resolution_source_refs"):
        market("market-bad-source", resolution_source_refs=("bad source",))
    with pytest.raises(ValueError, match="dependency_count"):
        market("market-bad-count", dependency_count=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="official_source_present"):
        market("market-bad-bool", official_source_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ambiguous_dependency_count"):
        market("market-bad-ambiguous", dependency_count=ZERO, ambiguous_dependency_count=d("1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        market("market-bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_market_outcome_resolution_dependency_map_report(
            (),
            generated_at=datetime(2026, 7, 12, 9, 0),
            config=MarketOutcomeResolutionDependencyMapConfig(),
        )

    dependency_report = report(market("market-consistency", dependency_count=ZERO))
    with pytest.raises(ValueError, match="dependency_status"):
        replace(dependency_report.rows[0], dependency_status="watch")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(dependency_report.rows[0], manual_next_step="submit_order")


def test_public_dataclasses_are_frozen_and_payload_revalidates_flags() -> None:
    dependency_report = report(market("market-frozen", dependency_count=ZERO))
    payload = market_outcome_resolution_dependency_map_report_payload(dependency_report)

    assert type(dependency_report) is MarketOutcomeResolutionDependencyMapReport
    assert type(dependency_report.rows[0]) is MarketOutcomeResolutionDependencyMapRow
    with pytest.raises(FrozenInstanceError):
        dependency_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        dependency_report.rows[0].dependency_status = "block"  # type: ignore[misc]

    bad_payload = dict(payload)
    bad_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        market_outcome_resolution_dependency_map_report_payload(bad_payload)


def test_owned_module_has_no_persistence_network_wallet_order_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "wallet",
        "private_key",
        "auth",
        "live",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "recommend",
        "open(",
        "connect(",
        "write_text",
        "write_bytes",
    )

    assert all(term not in lowered for term in forbidden_terms)

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_values(item))
    else:
        values.append(value)
    return tuple(values)
