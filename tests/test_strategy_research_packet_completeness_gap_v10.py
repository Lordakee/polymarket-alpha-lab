from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_research_packet_completeness_gap_v10 import (
    StrategyResearchPacketCompletenessGapV10Config,
    StrategyResearchPacketCompletenessGapV10Packet,
    StrategyResearchPacketCompletenessGapV10Report,
    StrategyResearchPacketCompletenessGapV10Result,
    build_strategy_research_packet_completeness_gap_v10_report,
    strategy_research_packet_completeness_gap_v10_payload,
    validate_strategy_research_packet_completeness_gap_v10_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_research_packet_completeness_gap_v10.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
REQUIRED_SOURCE_FAMILIES = (
    "forecast_rationale",
    "market_rules",
    "price_history",
    "primary_resolution_source",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyResearchPacketCompletenessGapV10Config:
    values: dict[str, object] = {
        "config_version": "strategy-research-packet-completeness-gap-v10-test",
        "required_source_families": REQUIRED_SOURCE_FAMILIES,
        "max_forecast_age_seconds": d("86400"),
        "missing_source_family_weight": d("0.100000"),
        "missing_resolution_criteria_weight": d("0.200000"),
        "stale_forecast_weight": d("0.250000"),
        "absent_cost_estimate_weight": d("0.150000"),
        "missing_risk_notes_weight": d("0.300000"),
        "blocked_gap_score": d("0.500000"),
    }
    values.update(overrides)
    return StrategyResearchPacketCompletenessGapV10Config(**values)


def packet(
    packet_id: str,
    *,
    market_slug: str | None = None,
    source_families: tuple[str, ...] = REQUIRED_SOURCE_FAMILIES,
    has_resolution_criteria: bool = True,
    forecasted_at: datetime | None = GENERATED_AT - timedelta(hours=2),
    has_cost_estimate: bool = True,
    risk_notes: tuple[str, ...] = ("risk notes reviewed",),
) -> StrategyResearchPacketCompletenessGapV10Packet:
    return StrategyResearchPacketCompletenessGapV10Packet(
        packet_id=packet_id,
        market_slug=market_slug or packet_id,
        source_families=source_families,
        has_resolution_criteria=has_resolution_criteria,
        forecasted_at=forecasted_at,
        has_cost_estimate=has_cost_estimate,
        risk_notes=risk_notes,
    )


def build_report(
    *packets: StrategyResearchPacketCompletenessGapV10Packet,
) -> StrategyResearchPacketCompletenessGapV10Report:
    return build_strategy_research_packet_completeness_gap_v10_report(
        packets,
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_scores_packet_completeness_gap_from_missing_research_dimensions() -> None:
    stale_forecast = GENERATED_AT - timedelta(days=3)
    report = build_report(
        packet(
            "alpha-gap",
            source_families=("market_rules", "price_history"),
            has_resolution_criteria=False,
            forecasted_at=stale_forecast,
            has_cost_estimate=False,
            risk_notes=(),
        ),
        packet("complete-packet"),
    )

    assert isinstance(report, StrategyResearchPacketCompletenessGapV10Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-research-packet-completeness-gap-v10-test"
    assert report.packet_count == d("2")
    assert report.complete_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("1")
    assert report.max_gap_score == d("1.100000")
    assert report.average_gap_score == d("0.550000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.packet_id for row in report.results) == (
        "alpha-gap",
        "complete-packet",
    )

    gap = report.results[0]
    assert isinstance(gap, StrategyResearchPacketCompletenessGapV10Result)
    assert gap.missing_source_families == (
        "forecast_rationale",
        "primary_resolution_source",
    )
    assert gap.missing_source_family_count == d("2")
    assert gap.forecast_age_seconds == d("259200")
    assert gap.forecast_status == "stale"
    assert gap.source_family_gap_score == d("0.200000")
    assert gap.resolution_criteria_gap_score == d("0.200000")
    assert gap.forecast_gap_score == d("0.250000")
    assert gap.cost_estimate_gap_score == d("0.150000")
    assert gap.risk_notes_gap_score == d("0.300000")
    assert gap.max_possible_gap_score == d("1.300000")
    assert gap.total_gap_score == d("1.100000")
    assert gap.completeness_score == d("0.153846")
    assert gap.gap_status == "blocked"
    assert gap.reason_codes == (
        "missing_source_families",
        "missing_resolution_criteria",
        "forecast_stale",
        "missing_cost_estimate",
        "missing_risk_notes",
        "packet_gap_blocked",
    )

    complete = report.results[1]
    assert complete.total_gap_score == d("0.000000")
    assert complete.completeness_score == d("1.000000")
    assert complete.gap_status == "complete"
    assert complete.reason_codes == (
        "source_families_complete",
        "resolution_criteria_present",
        "forecast_fresh",
        "cost_estimate_present",
        "risk_notes_present",
        "packet_complete",
    )


def test_payload_is_json_ready_report_only_and_tamper_evident() -> None:
    report = build_report(
        packet(
            "alpha-gap",
            source_families=("market_rules",),
            has_resolution_criteria=False,
            forecasted_at=None,
            has_cost_estimate=False,
            risk_notes=(),
        ),
    )

    validated = validate_strategy_research_packet_completeness_gap_v10_report(report)
    payload = strategy_research_packet_completeness_gap_v10_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).lower()

    assert validated is report
    assert len(report.report_sha256) == 64
    assert len(report.results[0].result_sha256) == 64
    assert payload["report_sha256"] == report.report_sha256
    assert payload["packet_count"] == "1"
    assert payload["results"][0]["total_gap_score"] == "1.200000"
    assert payload["results"][0]["forecast_age_seconds"] is None
    assert '"1.200000"' in encoded
    assert "action" not in rendered
    assert "auth" not in rendered
    assert "order" not in rendered
    assert "trade" not in rendered
    assert "wallet" not in rendered
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_payload_rejects_unsafe_public_payload_keys() -> None:
    with pytest.raises(ValueError, match="unsafe live surface field"):
        strategy_research_packet_completeness_gap_v10_payload(
            {"wallet_reference": "0xunsafe"}  # type: ignore[arg-type]
        )


def test_result_and_report_validation_recompute_derived_fields() -> None:
    report = build_report(
        packet(
            "alpha-gap",
            source_families=("market_rules", "price_history"),
            has_resolution_criteria=False,
            forecasted_at=GENERATED_AT - timedelta(days=3),
            has_cost_estimate=False,
            risk_notes=(),
        ),
    )
    row = report.results[0]

    with pytest.raises(ValueError, match="total_gap_score"):
        replace(row, total_gap_score=d("0.000000"))
    with pytest.raises(ValueError, match="result_sha256"):
        replace(row, packet_id="tampered-alpha-gap")
    with pytest.raises(ValueError, match="average_gap_score"):
        replace(report, average_gap_score=d("0.000000"))
    with pytest.raises(ValueError, match="report_sha256"):
        replace(report, config_version="tampered-config")


def test_public_dataclasses_are_frozen_decimal_only_and_enforce_flags() -> None:
    report = build_report(packet("complete-packet"))
    row = report.results[0]

    with pytest.raises(FrozenInstanceError):
        row.total_gap_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="max_forecast_age_seconds"):
        config(max_forecast_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_families"):
        packet("empty-sources", source_families=())
    with pytest.raises(ValueError, match="timezone-aware"):
        build_strategy_research_packet_completeness_gap_v10_report(
            (packet("naive-generated-at"),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    numeric_suffixes = (
        "_count",
        "_seconds",
        "_weight",
        "_score",
    )
    for value in (config(), row, report):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(numeric_suffixes):
                assert type(item_value) is Decimal


def test_empty_packet_iterable_produces_zero_report_counts() -> None:
    report = build_strategy_research_packet_completeness_gap_v10_report(
        (),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert report.packet_count == d("0")
    assert report.complete_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.max_gap_score == d("0.000000")
    assert report.average_gap_score == d("0.000000")
    assert report.results == ()
    assert validate_strategy_research_packet_completeness_gap_v10_report(report) is report


def test_module_scope_has_no_live_trading_network_or_persistence_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "trade",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "persist",
        "request",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    assert ".action" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
