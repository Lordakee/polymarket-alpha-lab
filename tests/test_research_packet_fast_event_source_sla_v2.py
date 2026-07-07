from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_fast_event_source_sla_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values: dict[str, object] = {
        "max_refresh_sla_seconds": d("900.000000"),
        "min_refresh_sla_seconds": d("60.000000"),
        "high_event_velocity_per_hour": d("12.000000"),
        "high_probability_movement": d("0.080000"),
        "official_lag_sla_seconds": d("300.000000"),
        "near_resolution_minutes": d("120.000000"),
        "critical_resolution_minutes": d("30.000000"),
    }
    values.update(overrides)
    return api().ResearchPacketFastEventSourceSlaV2Config(**values)


def source_row(
    packet_id: str,
    event_source_id: str,
    *,
    observed_refresh_age_seconds: Decimal = d("60.000000"),
    event_velocity_per_hour: Decimal = d("1.000000"),
    market_probability_movement: Decimal = d("0.005000"),
    official_source_lag_seconds: Decimal = d("30.000000"),
    contradiction_severity: str = "none",
    resolution_horizon_minutes: Decimal = d("720.000000"),
    specialist_uncertainty: Decimal = d("0.100000"),
):
    return api().ResearchPacketFastEventSourceSlaV2InputRow(
        packet_id=packet_id,
        event_source_id=event_source_id,
        observed_refresh_age_seconds=observed_refresh_age_seconds,
        event_velocity_per_hour=event_velocity_per_hour,
        market_probability_movement=market_probability_movement,
        official_source_lag_seconds=official_source_lag_seconds,
        contradiction_severity=contradiction_severity,
        resolution_horizon_minutes=resolution_horizon_minutes,
        specialist_uncertainty=specialist_uncertainty,
    )


def report(*rows: object, **config_overrides: object):
    return api().build_research_packet_fast_event_source_sla_v2_report(
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


def test_fast_event_source_sla_scores_blocked_watch_and_pass_rows_deterministically() -> None:
    module = api()

    sla_report = report(
        source_row(
            "packet-pass",
            "official-scoreboard",
        ),
        source_row(
            "packet-watch",
            "specialist-desk",
            observed_refresh_age_seconds=d("700.000000"),
            event_velocity_per_hour=d("4.000000"),
            market_probability_movement=d("0.030000"),
            official_source_lag_seconds=d("100.000000"),
            contradiction_severity="moderate",
            resolution_horizon_minutes=d("90.000000"),
            specialist_uncertainty=d("0.500000"),
        ),
        source_row(
            "packet-blocked",
            "official-ruling",
            observed_refresh_age_seconds=d("600.000000"),
            event_velocity_per_hour=d("15.000000"),
            market_probability_movement=d("0.120000"),
            official_source_lag_seconds=d("900.000000"),
            contradiction_severity="high",
            resolution_horizon_minutes=d("20.000000"),
            specialist_uncertainty=d("0.800000"),
        ),
    )
    payload = module.research_packet_fast_event_source_sla_v2_report_to_payload(
        sla_report,
    )

    assert is_dataclass(sla_report)
    assert type(sla_report) is module.ResearchPacketFastEventSourceSlaV2Report
    assert sla_report.generated_at == GENERATED_AT
    assert sla_report.config_version == "research-packet-fast-event-source-sla-v2"
    assert sla_report.report_status == "blocked"
    assert sla_report.source_row_count == d("3.000000")
    assert sla_report.pass_row_count == d("1.000000")
    assert sla_report.watch_row_count == d("1.000000")
    assert sla_report.blocked_row_count == d("1.000000")
    assert sla_report.issue_row_count == d("2.000000")
    assert sla_report.issue_ratio == d("0.666667")
    assert sla_report.max_observed_refresh_age_seconds == d("700.000000")
    assert sla_report.max_urgency_score == d("0.925000")
    assert sla_report.min_source_refresh_cadence_adequacy_score == d("0.112500")
    assert sla_report.reason_codes == (
        "fast_event_source_sla_blocked",
        "source_refresh_over_sla",
        "event_velocity_high",
        "market_probability_movement_high",
        "official_source_lag_high",
        "contradiction_severity_high",
        "resolution_horizon_near",
        "specialist_uncertainty_high",
    )
    assert sla_report.paper_only is True
    assert sla_report.report_only is True
    assert sla_report.readonly is True
    assert len(sla_report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in sla_report.derived_validation_digest)

    assert tuple(row.packet_id for row in sla_report.rows) == (
        "packet-blocked",
        "packet-watch",
        "packet-pass",
    )
    blocked = sla_report.rows[0]
    assert type(blocked) is module.ResearchPacketFastEventSourceSlaV2Row
    assert blocked.row_status == "blocked"
    assert blocked.urgency_score == d("0.925000")
    assert blocked.required_refresh_sla_seconds == d("67.500000")
    assert blocked.seconds_over_required_refresh_sla == d("532.500000")
    assert blocked.source_refresh_cadence_adequacy_score == d("0.112500")
    assert blocked.reason_codes == (
        "source_refresh_over_sla",
        "event_velocity_high",
        "market_probability_movement_high",
        "official_source_lag_high",
        "contradiction_severity_high",
        "resolution_horizon_near",
        "specialist_uncertainty_high",
    )

    watch = sla_report.rows[1]
    assert watch.row_status == "watch"
    assert watch.urgency_score == d("0.395833")
    assert watch.required_refresh_sla_seconds == d("543.750300")
    assert watch.source_refresh_cadence_adequacy_score == d("0.776786")
    assert watch.reason_codes == (
        "source_refresh_over_sla",
        "resolution_horizon_near",
    )

    passed = sla_report.rows[2]
    assert passed.row_status == "pass"
    assert passed.reason_codes == ("fast_event_source_sla_pass",)

    assert payload["source_row_count"] == "3.000000"
    assert payload["issue_ratio"] == "0.666667"
    assert payload["max_urgency_score"] == "0.925000"
    assert payload["rows"][0]["urgency_score"] == "0.925000"
    assert payload["rows"][0]["required_refresh_sla_seconds"] == "67.500000"
    assert payload["derived_validation_digest"] == sla_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload_values(payload)
    json.dumps(payload)


def test_empty_report_is_pass_with_decimal_zero_metrics() -> None:
    sla_report = report()

    assert sla_report.report_status == "pass"
    assert sla_report.source_row_count == d("0.000000")
    assert sla_report.pass_row_count == d("0.000000")
    assert sla_report.watch_row_count == d("0.000000")
    assert sla_report.blocked_row_count == d("0.000000")
    assert sla_report.issue_row_count == d("0.000000")
    assert sla_report.issue_ratio == d("0.000000")
    assert sla_report.max_observed_refresh_age_seconds == d("0.000000")
    assert sla_report.max_urgency_score == d("0.000000")
    assert sla_report.min_source_refresh_cadence_adequacy_score == d("0.000000")
    assert sla_report.rows == ()
    assert sla_report.reason_codes == ("fast_event_source_sla_pass",)


def test_inputs_validate_decimal_only_times_duplicates_frozen_and_hard_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="observed_refresh_age_seconds must be a Decimal"):
        source_row("packet-int", "source-int", observed_refresh_age_seconds=60)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_fast_event_source_sla_v2_report(
            (source_row("packet-naive", "source-naive"),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="event source pairs must be unique"):
        report(
            source_row("packet-dup", "source-dup"),
            source_row("packet-dup", "source-dup"),
        )

    item = source_row("packet-frozen", "source-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.ResearchPacketFastEventSourceSlaV2Config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(source_row("packet-flag", "source-flag")), readonly=False)

    for field in fields(report(source_row("packet-decimal", "source-decimal"))):
        field_value = getattr(report(source_row("packet-decimal-2", "source-decimal-2")), field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_score")
        ):
            assert type(field_value) is Decimal


def test_public_payload_is_digest_bound_and_rejects_unsafe_keys_and_values() -> None:
    module = api()
    sla_report = report(source_row("packet-json", "source-json"))
    payload = module.research_packet_fast_event_source_sla_v2_report_to_payload(
        sla_report,
    )

    tampered_payload = dict(payload)
    tampered_payload["source_row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_fast_event_source_sla_v2_report_to_payload(tampered_payload)

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_fast_event_source_sla_v2_report_to_payload(
            missing_digest_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_hint"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_packet_fast_event_source_sla_v2_report_to_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [
        {
            **payload["rows"][0],
            "event_source_id": "connect_wallet",
        },
    ]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_packet_fast_event_source_sla_v2_report_to_payload(
            unsafe_value_payload,
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        source_row("packet-live", "source-safe")

    tampered_report = report(source_row("packet-tamper", "source-tamper"))
    object.__setattr__(tampered_report.rows[0], "urgency_score", d("0.500000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_fast_event_source_sla_v2_report_to_payload(tampered_report)


def test_module_scope_exposes_no_external_action_surface_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_fast_event_source_sla_v2.py",
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
        "read_text",
        "write_text",
    }.isdisjoint(called_names)
