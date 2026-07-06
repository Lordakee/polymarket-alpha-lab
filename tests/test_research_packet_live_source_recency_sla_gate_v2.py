from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_live_source_recency_sla_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values: dict[str, object] = {
        "near_resolution_seconds": d("7200.000000"),
        "critical_resolution_seconds": d("900.000000"),
        "minimum_effective_recency_seconds": d("60.000000"),
        "blocked_age_multiplier": d("2.000000"),
        "source_age_weight": d("0.700000"),
        "market_time_to_resolution_weight": d("0.200000"),
        "source_tier_weight": d("0.100000"),
        "pass_score_floor": d("0.800000"),
        "warn_score_floor": d("0.350000"),
    }
    values.update(overrides)
    return api().ResearchPacketLiveSourceRecencySlaGateV2Config(**values)


def source_row(
    packet_id: str,
    market_id: str,
    source_id: str,
    *,
    source_tier: str = "official",
    observed_age_seconds: Decimal = d("120.000000"),
    resolution_horizon_seconds: Decimal = d("21600.000000"),
    required_recency_seconds: Decimal = d("600.000000"),
):
    return api().ResearchPacketLiveSourceRecencySlaGateV2InputRow(
        packet_id=packet_id,
        market_id=market_id,
        source_id=source_id,
        source_tier=source_tier,
        observed_at=GENERATED_AT - timedelta(seconds=float(observed_age_seconds)),
        market_resolution_at=GENERATED_AT
        + timedelta(seconds=float(resolution_horizon_seconds)),
        required_recency_seconds=required_recency_seconds,
    )


def report(*rows: object, **config_overrides: object):
    return api().build_research_packet_live_source_recency_sla_gate_v2_report(
        rows,
        config=config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)


def assert_no_float_or_decimal_payload_values(value: object) -> None:
    values = walk_payload_values(value)
    assert not any(type(item) is float for item in values)
    assert not any(type(item) is Decimal for item in values)


def test_live_source_recency_sla_scores_blocked_warn_and_pass_rows() -> None:
    module = api()

    sla_report = report(
        source_row("packet-pass", "market-alpha", "official-ruling"),
        source_row(
            "packet-warn",
            "market-alpha",
            "primary-analysis",
            source_tier="primary",
            observed_age_seconds=d("200.000000"),
            resolution_horizon_seconds=d("3600.000000"),
        ),
        source_row(
            "packet-blocked",
            "market-beta",
            "live-feed",
            source_tier="live",
            observed_age_seconds=d("1500.000000"),
            resolution_horizon_seconds=d("600.000000"),
        ),
        source_row(
            "packet-secondary",
            "market-gamma",
            "secondary-reference",
            source_tier="secondary",
            observed_age_seconds=d("30.000000"),
            resolution_horizon_seconds=d("21600.000000"),
            required_recency_seconds=d("300.000000"),
        ),
    )
    payload = module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
        sla_report,
    )

    assert is_dataclass(sla_report)
    assert type(sla_report) is module.ResearchPacketLiveSourceRecencySlaGateV2Report
    assert sla_report.generated_at == GENERATED_AT
    assert sla_report.config_version == "research-packet-live-source-recency-sla-gate-v2"
    assert sla_report.report_status == "blocked"
    assert sla_report.source_row_count == d("4.000000")
    assert sla_report.pass_row_count == d("2.000000")
    assert sla_report.warn_row_count == d("1.000000")
    assert sla_report.blocked_row_count == d("1.000000")
    assert sla_report.issue_row_count == d("2.000000")
    assert sla_report.issue_ratio == d("0.500000")
    assert sla_report.max_source_age_seconds == d("1500.000000")
    assert sla_report.max_seconds_over_effective_sla == d("1200.000000")
    assert sla_report.min_information_freshness_score == d("0.101667")
    assert sla_report.reason_codes == (
        "live_source_recency_sla_blocked",
        "source_age_stale",
        "required_recency_missed",
        "market_resolution_near",
    )
    assert sla_report.paper_only is True
    assert sla_report.report_only is True
    assert sla_report.readonly is True
    assert len(sla_report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in sla_report.derived_validation_digest)

    assert tuple(row.packet_id for row in sla_report.rows) == (
        "packet-blocked",
        "packet-warn",
        "packet-pass",
        "packet-secondary",
    )
    blocked = sla_report.rows[0]
    assert blocked.row_status == "blocked"
    assert blocked.source_tier == "live"
    assert blocked.source_age_seconds == d("1500.000000")
    assert blocked.market_time_to_resolution_seconds == d("600.000000")
    assert blocked.required_recency_seconds == d("600.000000")
    assert blocked.effective_recency_sla_seconds == d("300.000000")
    assert blocked.seconds_over_effective_sla == d("1200.000000")
    assert blocked.source_age_score == d("0.000000")
    assert blocked.market_time_to_resolution_score == d("0.083333")
    assert blocked.source_tier_score == d("0.850000")
    assert blocked.information_freshness_score == d("0.101667")
    assert blocked.reason_codes == (
        "live_source_recency_sla_blocked",
        "source_age_stale",
        "required_recency_missed",
        "market_resolution_near",
        "live_source_tier",
    )

    warned = sla_report.rows[1]
    assert warned.row_status == "warn"
    assert warned.effective_recency_sla_seconds == d("300.000000")
    assert warned.seconds_over_effective_sla == d("0.000000")
    assert warned.source_age_score == d("0.333333")
    assert warned.market_time_to_resolution_score == d("0.500000")
    assert warned.source_tier_score == d("0.900000")
    assert warned.information_freshness_score == d("0.423333")
    assert warned.reason_codes == (
        "live_source_recency_sla_warn",
        "source_age_fresh",
        "required_recency_met",
        "market_resolution_buffer_clear",
        "primary_source_tier",
    )

    passed = sla_report.rows[2]
    assert passed.row_status == "pass"
    assert passed.source_tier == "official"
    assert passed.information_freshness_score == d("0.860000")

    secondary = sla_report.rows[3]
    assert secondary.row_status == "pass"
    assert secondary.source_tier_score == d("0.750000")
    assert secondary.information_freshness_score == d("0.905000")

    assert payload["source_row_count"] == "4.000000"
    assert payload["issue_ratio"] == "0.500000"
    assert payload["rows"][0]["information_freshness_score"] == "0.101667"
    assert payload["derived_validation_digest"] == sla_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload_values(payload)
    json.dumps(payload)


def test_empty_report_blocks_as_missing_freshness_evidence() -> None:
    sla_report = report()

    assert sla_report.report_status == "blocked"
    assert sla_report.source_row_count == d("0.000000")
    assert sla_report.pass_row_count == d("0.000000")
    assert sla_report.warn_row_count == d("0.000000")
    assert sla_report.blocked_row_count == d("0.000000")
    assert sla_report.issue_row_count == d("0.000000")
    assert sla_report.issue_ratio == d("0.000000")
    assert sla_report.max_source_age_seconds == d("0.000000")
    assert sla_report.max_seconds_over_effective_sla == d("0.000000")
    assert sla_report.min_information_freshness_score == d("0.000000")
    assert sla_report.rows == ()
    assert sla_report.reason_codes == (
        "live_source_recency_sla_blocked",
        "live_source_recency_sla_gate_empty",
    )


def test_inputs_validate_decimal_only_time_order_duplicates_frozen_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="required_recency_seconds must be a Decimal"):
        source_row(
            "packet-int",
            "market-int",
            "source-int",
            required_recency_seconds=600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_live_source_recency_sla_gate_v2_report(
            (source_row("packet-naive", "market-naive", "source-naive"),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    future_observation = module.ResearchPacketLiveSourceRecencySlaGateV2InputRow(
        packet_id="packet-future",
        market_id="market-future",
        source_id="source-future",
        source_tier="official",
        observed_at=GENERATED_AT + timedelta(seconds=1),
        market_resolution_at=GENERATED_AT + timedelta(hours=1),
        required_recency_seconds=d("600.000000"),
    )
    with pytest.raises(ValueError, match="observed_at must be <= generated_at"):
        module.build_research_packet_live_source_recency_sla_gate_v2_report(
            (future_observation,),
            config=config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="source rows must have unique"):
        report(
            source_row("packet-dup", "market-dup", "source-dup"),
            source_row("packet-dup", "market-dup", "source-dup"),
        )

    item = source_row("packet-frozen", "market-frozen", "source-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.ResearchPacketLiveSourceRecencySlaGateV2Config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(source_row("packet-flag", "market-flag", "source-flag")), readonly=False)

    checked_report = report(source_row("packet-decimal", "market-decimal", "source-decimal"))
    for field in fields(checked_report):
        field_value = getattr(checked_report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_score")
        ):
            assert type(field_value) is Decimal


def test_payload_digest_is_deterministic_and_tamper_evident() -> None:
    module = api()
    sla_report = report(source_row("packet-json", "market-json", "source-json"))
    payload = module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
        sla_report,
    )
    same_report = report(source_row("packet-json", "market-json", "source-json"))

    assert same_report.derived_validation_digest == sla_report.derived_validation_digest
    assert same_report.payload == payload

    tampered_payload = dict(payload)
    tampered_payload["source_row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
            tampered_payload,
        )

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
            missing_digest_payload,
        )

    forbidden_key_payload = dict(payload)
    forbidden_key_payload["wallet_hint"] = "redacted"
    with pytest.raises(ValueError, match="forbidden public field"):
        module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
            forbidden_key_payload,
        )

    forbidden_value_payload = dict(payload)
    forbidden_value_payload["rows"] = [
        {
            **payload["rows"][0],
            "source_id": "connect-wallet",
        },
    ]
    with pytest.raises(ValueError, match="forbidden public value"):
        module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
            forbidden_value_payload,
        )

    tampered_report = report(source_row("packet-tamper", "market-tamper", "source-tamper"))
    object.__setattr__(
        tampered_report.rows[0],
        "information_freshness_score",
        d("0.500000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_live_source_recency_sla_gate_v2_report_to_payload(
            tampered_report,
        )


def test_module_scope_is_readonly_and_has_no_external_action_surface_or_floats() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_live_source_recency_sla_gate_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "web3",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "write_text",
    }.isdisjoint(called_names)
