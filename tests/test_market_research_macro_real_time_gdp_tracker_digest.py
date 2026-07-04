from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_macro_real_time_gdp_tracker_digest import (
    DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION,
    MarketResearchMacroRealTimeGdpTrackerDigestConfig,
    MarketResearchMacroRealTimeGdpTrackerDigestInputRow,
    MarketResearchMacroRealTimeGdpTrackerDigestReport,
    build_market_research_macro_real_time_gdp_tracker_digest,
    market_research_macro_real_time_gdp_tracker_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchMacroRealTimeGdpTrackerDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION
        ),
        "fresh_tracker_max_age_seconds": d("7200.000000"),
        "material_growth_gap_threshold": d("0.400000"),
        "material_revision_threshold": d("0.300000"),
        "probability_repricing_threshold": d("0.100000"),
        "min_source_count": d("2.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchMacroRealTimeGdpTrackerDigestConfig(**values)


def input_row(
    research_key: str = "research.gdp.tracker",
    *,
    condition_id: str = "condition_gdp_growth",
    tracker_key: str = "real_gdp.q2.tracker",
    tracker_reference: str = "public-real-time-gdp-tracker",
    observed_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    annualized_real_gdp_growth: Decimal = d("2.100000"),
    consensus_real_gdp_growth: Decimal = d("2.000000"),
    prior_tracker_growth: Decimal = d("2.050000"),
    market_probability_before: Decimal = d("0.500000"),
    market_probability_after: Decimal = d("0.530000"),
) -> MarketResearchMacroRealTimeGdpTrackerDigestInputRow:
    observed = observed_at or GENERATED_AT - timedelta(minutes=30)
    return MarketResearchMacroRealTimeGdpTrackerDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        tracker_key=tracker_key,
        tracker_reference=tracker_reference,
        observed_at=observed,
        acknowledged_at=(
            acknowledged_at
            if acknowledged_at is not None
            else observed + timedelta(minutes=10)
        ),
        source_count=source_count,
        annualized_real_gdp_growth=annualized_real_gdp_growth,
        consensus_real_gdp_growth=consensus_real_gdp_growth,
        prior_tracker_growth=prior_tracker_growth,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_macro_real_time_gdp_tracker_digest_is_phase1_report_only() -> None:
    report = build_market_research_macro_real_time_gdp_tracker_digest(
        (
            input_row(
                "research.gdp.q3.atlanta",
                condition_id="condition_gdp_q3_growth",
                tracker_key="real_gdp.q3.tracker",
                tracker_reference="vendor-real-time-gdp-tracker-reference",
                observed_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=100),
                source_count=d("1.000000"),
                annualized_real_gdp_growth=d("1.700000"),
                consensus_real_gdp_growth=d("2.300000"),
                prior_tracker_growth=d("2.200000"),
                market_probability_before=d("0.420000"),
                market_probability_after=d("0.560000"),
            ),
            input_row(),
        ),
        config=config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, MarketResearchMacroRealTimeGdpTrackerDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.digest_status == "watch"
    assert (
        report.recommended_next_step
        == "watch_report_only_market_research_macro_real_time_gdp_tracker_digest"
    )
    assert report.tracker_count == d("2.000000")
    assert report.watch_tracker_count == d("1.000000")
    assert report.ready_tracker_count == d("1.000000")
    assert report.blocked_tracker_count == d("0.000000")
    assert report.material_growth_gap_count == d("1.000000")
    assert report.material_revision_count == d("1.000000")
    assert report.probability_repricing_count == d("1.000000")
    assert report.slow_acknowledgement_count == d("1.000000")
    assert report.stale_tracker_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.average_tracker_gap_abs == d("0.350000")
    assert report.max_tracker_age_seconds == d("10800.000000")
    assert report.average_source_count == d("2.000000")
    assert tuple(row.tracker_key for row in report.rows) == (
        "real_gdp.q3.tracker",
        "real_gdp.q2.tracker",
    )
    assert report.rows[0].reason_codes == (
        "market_research_macro_real_time_gdp_tracker_digest_material_growth_gap",
        "market_research_macro_real_time_gdp_tracker_digest_material_revision",
        "market_research_macro_real_time_gdp_tracker_digest_probability_repricing",
        "market_research_macro_real_time_gdp_tracker_digest_slow_acknowledgement",
        "market_research_macro_real_time_gdp_tracker_digest_stale_tracker",
        "market_research_macro_real_time_gdp_tracker_digest_thin_sources",
    )
    assert report.reason_codes == report.rows[0].reason_codes
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert all(type(row.tracker_gap_abs) is Decimal for row in report.rows)
    assert report.rows[0].redacted_tracker_reference.startswith("sha256:")

    with pytest.raises(FrozenInstanceError):
        report.tracker_count = d("3.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 3, 13, 30))

    payload = market_research_macro_real_time_gdp_tracker_digest_payload(report)
    json.dumps(payload, sort_keys=True)
    assert payload == market_research_macro_real_time_gdp_tracker_digest_payload(report)
    assert payload["generated_at"] == "2026-07-03T14:00:00+00:00"
    assert payload["tracker_count"] == "2.000000"
    assert payload["average_tracker_gap_abs"] == "0.350000"
    assert payload["max_tracker_age_seconds"] == "10800.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_count"] == "1.000000"
    assert payload["rows"][0]["tracker_gap_abs"] == "0.600000"
    assert payload["rows"][0]["market_probability_after"] == "0.560000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T11:00:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["tracker_ratio"] == "0.500000"
    assert all(row["paper_only"] is True for row in payload["rows"])
    assert all(row["report_only"] is True for row in payload["rows"])
    assert all(row["readonly"] is True for row in payload["rows"])
    assert all(item["paper_only"] is True for item in payload["reason_code_counts"])
    assert all(item["report_only"] is True for item in payload["reason_code_counts"])
    assert all(item["readonly"] is True for item in payload["reason_code_counts"])
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert "'tracker_reference':" not in repr(payload)
    assert "vendor-real-time-gdp-tracker-reference" not in repr(payload)

    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_macro_real_time_gdp_tracker_digest_payload(unsafe_report)
    with pytest.raises(ValueError, match="redacted"):
        replace(
            report.rows[0],
            redacted_tracker_reference="https://vendor.example/gdp",
        )


def test_macro_real_time_gdp_tracker_empty_digest_is_deterministic() -> None:
    report = build_market_research_macro_real_time_gdp_tracker_digest(
        (),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "ready"
    assert report.tracker_count == d("0.000000")
    assert report.reason_codes == (
        "market_research_macro_real_time_gdp_tracker_digest_no_inputs",
    )
    assert report.reason_code_counts == ()
    payload = market_research_macro_real_time_gdp_tracker_digest_payload(report)
    assert payload["tracker_count"] == "0.000000"
    assert payload["reason_codes"] == [
        "market_research_macro_real_time_gdp_tracker_digest_no_inputs",
    ]


def test_macro_real_time_gdp_tracker_digest_has_no_live_or_durable_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_macro_real_time_gdp_tracker_digest.py"
    )
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
        "wallet",
        "private_key",
        "sqlite",
        "postgres",
        "redis",
    ):
        assert token not in source

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
