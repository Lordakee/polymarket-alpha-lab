from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_packet_source_recency_confidence_gate_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_recency_confidence_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def generated_at() -> datetime:
    return datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def config(**overrides: object):
    module = api()
    values = {
        "official_source_age_max_seconds": d("1000.000000"),
        "independent_source_family_age_max_seconds": d("1000.000000"),
        "contradiction_age_max_seconds": d("1000.000000"),
        "probability_move_attribution_age_max_seconds": d("1000.000000"),
        "event_velocity_soft_cap_per_day": d("10.000000"),
        "resolution_horizon_max_seconds": d("1000.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketSourceRecencyConfidenceGateV2Config(**values)


def packet(**overrides: object):
    module = api()
    now = generated_at()
    values = {
        "packet_id": "packet-alpha",
        "event_id": "event-alpha",
        "official_source_last_seen_at": now - timedelta(seconds=100),
        "independent_source_family_last_seen_at": now - timedelta(seconds=200),
        "contradiction_last_seen_at": now - timedelta(seconds=900),
        "probability_move_attributed_at": now - timedelta(seconds=300),
        "event_velocity_per_day": d("2.000000"),
        "resolution_at": now + timedelta(seconds=600),
        "specialist_uncertainty": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchPacketSourceRecencyConfidenceGateV2Packet(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    report_config = overrides.pop("config", config())
    report_generated_at = overrides.pop("generated_at", generated_at())
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items:
        items = (
            packet(packet_id="packet-alpha", event_id="event-alpha"),
            packet(
                packet_id="packet-beta",
                event_id="event-beta",
                official_source_last_seen_at=report_generated_at
                - timedelta(seconds=900),
                independent_source_family_last_seen_at=report_generated_at
                - timedelta(seconds=900),
                contradiction_last_seen_at=report_generated_at
                - timedelta(seconds=100),
                probability_move_attributed_at=None,
                event_velocity_per_day=d("10.000000"),
                resolution_at=report_generated_at + timedelta(seconds=100),
                specialist_uncertainty=d("0.900000"),
            ),
        )
    return module.build_research_packet_source_recency_confidence_gate_v2(
        items,
        config=report_config,
        generated_at=report_generated_at,
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


def test_builds_decimal_source_recency_confidence_gate_and_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.gate_status == "blocked"
    assert report.packet_count == d("2")
    assert report.pass_packet_count == d("1")
    assert report.watch_packet_count == d("0")
    assert report.blocked_packet_count == d("1")
    assert report.average_source_recency_confidence_score == d("0.443500")
    assert report.minimum_source_recency_confidence_score == d("0.075000")
    assert report.reason_codes == ("source_recency_confidence_gate_blocked_rows",)

    rows = report.rows
    assert tuple(row.packet_id for row in rows) == ("packet-alpha", "packet-beta")
    assert rows[0].official_source_age_seconds == d("100.000000")
    assert rows[0].independent_source_family_age_seconds == d("200.000000")
    assert rows[0].contradiction_age_seconds == d("900.000000")
    assert rows[0].probability_move_attribution_age_seconds == d("300.000000")
    assert rows[0].resolution_horizon_seconds == d("600.000000")
    assert rows[0].source_recency_confidence_score == d("0.812000")
    assert rows[0].gate_status == "pass"
    assert rows[1].source_recency_confidence_score == d("0.075000")
    assert rows[1].gate_status == "blocked"

    payload = report.payload
    assert payload["packet_count"] == "2"
    assert payload["average_source_recency_confidence_score"] == "0.443500"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_recency_confidence_score"] == "0.812000"
    assert payload["rows"][1]["probability_move_attribution_age_seconds"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_gate_is_report_only_and_digest_backed() -> None:
    module = api()

    report = module.build_research_packet_source_recency_confidence_gate_v2(
        (),
        config=config(),
        generated_at=generated_at(),
    )

    assert report.gate_status == "blocked"
    assert report.packet_count == d("0")
    assert report.rows == ()
    assert report.average_source_recency_confidence_score == d("0.000000")
    assert report.minimum_source_recency_confidence_score == d("0.000000")
    assert report.reason_codes == ("source_recency_confidence_gate_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    report_config = config()
    sample = packet()
    report = build_report(sample, config=report_config)
    row = report.rows[0]

    for item in (report_config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "official_source_age_max_seconds",
                "independent_source_family_age_max_seconds",
                "contradiction_age_max_seconds",
                "probability_move_attribution_age_max_seconds",
                "event_velocity_soft_cap_per_day",
                "resolution_horizon_max_seconds",
                "official_source_age_weight",
                "independent_source_family_freshness_weight",
                "contradiction_age_weight",
                "probability_move_attribution_age_weight",
                "event_velocity_weight",
                "resolution_horizon_weight",
                "specialist_uncertainty_weight",
                "pass_score_floor",
                "watch_score_floor",
                "event_velocity_per_day",
                "specialist_uncertainty",
                "official_source_age_seconds",
                "official_source_recency_score",
                "independent_source_family_age_seconds",
                "independent_source_family_freshness_score",
                "contradiction_age_seconds",
                "contradiction_age_score",
                "probability_move_attribution_age_seconds",
                "probability_move_attribution_score",
                "event_velocity_score",
                "resolution_horizon_seconds",
                "resolution_horizon_score",
                "specialist_uncertainty_score",
                "source_recency_confidence_score",
                "packet_count",
                "pass_packet_count",
                "watch_packet_count",
                "blocked_packet_count",
                "average_source_recency_confidence_score",
                "minimum_source_recency_confidence_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "event_velocity_per_day",
            _DecimalSubclass("2.000000"),
            "event_velocity_per_day must be exactly Decimal",
        ),
        (
            "specialist_uncertainty",
            d("1.000001"),
            "specialist_uncertainty must be <= 1.000000",
        ),
        (
            "event_velocity_per_day",
            d("2.0000004"),
            "event_velocity_per_day must use six decimal places or fewer",
        ),
        (
            "specialist_uncertainty",
            Decimal("NaN"),
            "specialist_uncertainty must be finite",
        ),
    ),
)
def test_packet_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        packet(**{field_name: bad_value})


def test_config_and_build_validation_reject_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="official_source_age_max_seconds must be exactly Decimal"):
        module.ResearchPacketSourceRecencyConfidenceGateV2Config(
            official_source_age_max_seconds=1000,
        )
    with pytest.raises(ValueError, match="gate weights must sum to 1.000000"):
        module.ResearchPacketSourceRecencyConfidenceGateV2Config(
            official_source_age_weight=d("0.240000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed pass_score_floor"):
        module.ResearchPacketSourceRecencyConfidenceGateV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchPacketSourceRecencyConfidenceGateV2Config(paper_only=False)
    with pytest.raises(ValueError, match="packets must be an iterable"):
        module.build_research_packet_source_recency_confidence_gate_v2(
            object(),
            config=config(),
            generated_at=generated_at(),
        )
    with pytest.raises(
        ValueError,
        match="packet items must be ResearchPacketSourceRecencyConfidenceGateV2Packet",
    ):
        module.build_research_packet_source_recency_confidence_gate_v2(
            [object()],
            config=config(),
            generated_at=generated_at(),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_source_recency_confidence_gate_v2(
            [packet()],
            config=config(),
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="resolution_at must be >= generated_at"):
        build_report(
            packet(resolution_at=generated_at() - timedelta(seconds=1)),
            config=config(),
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_source_recency_confidence_score=d("0.500000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_packet",
        "auth_packet",
        "wallet_packet",
        "order_packet",
        "network_packet",
        "database_packet",
        "persist_packet",
        "signing_packet",
        "mutation_packet",
        "buy_packet",
        "sell_packet",
        "trade_packet",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            packet(packet_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_reason_codes_and_scores() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by confidence and packet"):
        replace(report, rows=(report.rows[1], report.rows[0]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_packet_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match gate_status"):
        replace(report, reason_codes=("source_recency_confidence_gate_passed",))
    values = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "packet_count": report.packet_count,
        "pass_packet_count": report.pass_packet_count,
        "watch_packet_count": report.watch_packet_count,
        "blocked_packet_count": report.blocked_packet_count,
        "average_source_recency_confidence_score": d("0.443501"),
        "minimum_source_recency_confidence_score": report.minimum_source_recency_confidence_score,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = module._derived_validation_digest(values)
    with pytest.raises(ValueError, match="average_source_recency_confidence_score must match rows"):
        replace(
            report,
            average_source_recency_confidence_score=values[
                "average_source_recency_confidence_score"
            ],
            derived_validation_digest=values["derived_validation_digest"],
        )


def test_public_api_and_module_scope_stay_pure_readonly_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_RECENCY_CONFIDENCE_GATE_V2_CONFIG_VERSION",
        "ResearchPacketSourceRecencyConfidenceGateV2Config",
        "ResearchPacketSourceRecencyConfidenceGateV2Packet",
        "ResearchPacketSourceRecencyConfidenceGateV2Row",
        "ResearchPacketSourceRecencyConfidenceGateV2Report",
        "build_research_packet_source_recency_confidence_gate_v2",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden_fragment in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden_fragment not in lowered_source

    tree = ast.parse(source)
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "place_order",
        "rollback",
        "send",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
