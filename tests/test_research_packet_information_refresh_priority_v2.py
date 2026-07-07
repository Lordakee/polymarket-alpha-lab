from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_information_refresh_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def stamp() -> datetime:
    return datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-packet-information-refresh-priority-v2",
        "stale_source_hours": d("24.000000"),
        "resolution_horizon_hours": d("72.000000"),
        "high_priority_threshold": d("0.700000"),
        "medium_priority_threshold": d("0.400000"),
        "source_age_weight": d("0.200000"),
        "event_velocity_weight": d("0.150000"),
        "contradiction_severity_weight": d("0.200000"),
        "resolution_horizon_weight": d("0.150000"),
        "official_source_gap_weight": d("0.150000"),
        "team_uncertainty_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchPacketInformationRefreshPriorityV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "event_title": "Will Alpha resolve by July?",
        "source_age_hours": d("36.000000"),
        "event_velocity": d("0.900000"),
        "contradiction_severity": d("0.800000"),
        "hours_to_resolution": d("12.000000"),
        "official_source_gap": d("0.700000"),
        "team_uncertainty": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchPacketInformationRefreshPriorityV2Candidate(**values)


def build_report(*rows: object):
    module = api()
    source_rows = rows or (
        candidate(packet_id="packet-alpha", source_age_hours=d("36.000000")),
        candidate(
            packet_id="packet-beta",
            event_title="Will Beta resolve by July?",
            source_age_hours=d("4.000000"),
            event_velocity=d("0.100000"),
            contradiction_severity=d("0.100000"),
            hours_to_resolution=d("120.000000"),
            official_source_gap=d("0.000000"),
            team_uncertainty=d("0.100000"),
        ),
    )
    return module.build_research_packet_information_refresh_priority_v2(
        source_rows,
        config=config(),
        generated_at=stamp(),
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk(item))
        return tuple(values)
    return (value,)


def unsafe_value() -> str:
    return "requires " + "wal" + "let"


def unsafe_key() -> str:
    return "net" + "work" + "_hint"


def test_prioritizes_packets_with_decimal_only_readonly_payload() -> None:
    module = api()

    report = build_report()

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.candidate_count == d("2")
    assert report.high_priority_count == d("1")
    assert report.medium_priority_count == d("0")
    assert report.low_priority_count == d("1")
    assert report.average_priority_score == d("0.449166")
    assert report.max_priority_score == d("0.815000")
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-alpha",
        "packet-beta",
    )
    high_row = report.rows[0]
    assert high_row.rank == d("1")
    assert high_row.priority_score == d("0.815000")
    assert high_row.priority_band == "high"
    assert high_row.refresh_action == "collect_now"
    assert high_row.reason_codes == (
        "source_age_high",
        "event_velocity_high",
        "contradiction_severity_high",
        "resolution_horizon_near",
        "official_source_gap_high",
        "team_uncertainty_elevated",
        "priority_high",
    )
    assert high_row.source_age_score == d("1.000000")
    assert high_row.resolution_horizon_score == d("0.833333")

    payload = report.payload
    assert payload == module.research_packet_information_refresh_priority_v2_payload(
        report,
    )
    assert payload["config_version"] == "research-packet-information-refresh-priority-v2"
    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["candidate_count"] == "2"
    assert payload["average_priority_score"] == "0.449166"
    assert payload["max_priority_score"] == "0.815000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["priority_score"] == "0.815000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert not any(type(value) is Decimal for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_validation_requires_decimal_inputs_flags_and_frozen_dataclasses() -> None:
    module = api()
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.high_priority_count = d("2")  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_band = "low"  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_age_hours must be a Decimal"):
        candidate(source_age_hours=36)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_velocity must be a Decimal"):
        candidate(event_velocity=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_uncertainty must be a Decimal"):
        candidate(team_uncertainty=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="source_age_hours must be finite"):
        candidate(source_age_hours=Decimal("NaN"))

    with pytest.raises(ValueError, match="event_velocity must be between 0 and 1"):
        candidate(event_velocity=d("1.000001"))

    with pytest.raises(ValueError, match="input must be readonly"):
        candidate(readonly=False)

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="medium_priority_threshold must not exceed"):
        config(high_priority_threshold=d("0.399999"))

    with pytest.raises(ValueError, match="candidate rows"):
        module.build_research_packet_information_refresh_priority_v2(
            [object()],
            config=config(),
            generated_at=stamp(),
        )


def test_derived_validation_digest_rejects_row_and_payload_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, high_priority_count=d("0"))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(
            report,
            rows=(
                replace(
                    report.rows[0],
                    priority_score=d("0.840000"),
                    priority_band="high",
                    refresh_action="collect_now",
                ),
                report.rows[1],
            ),
        )

    payload = report.payload
    tampered_payload = {
        **payload,
        "rows": [
            {**payload["rows"][0], "priority_score": "0.840000"},
            payload["rows"][1],
        ],
    }
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_packet_information_refresh_priority_v2_payload(tampered_payload)

    refreshed_payload = {
        **tampered_payload,
        "derived_validation_digest": module.derive_research_packet_information_refresh_priority_v2_digest(
            tampered_payload,
        ),
    }
    assert (
        module.research_packet_information_refresh_priority_v2_payload(
            refreshed_payload,
        )["rows"][0]["priority_score"]
        == "0.840000"
    )


def test_public_payload_rejects_unsafe_keys_values_and_numeric_values() -> None:
    module = api()
    payload = build_report().payload

    with pytest.raises(ValueError, match="unsafe public payload key"):
        module.research_packet_information_refresh_priority_v2_payload(
            {**payload, unsafe_key(): "blocked"},
        )

    with pytest.raises(ValueError, match="unsafe public payload value"):
        module.research_packet_information_refresh_priority_v2_payload(
            {**payload, "operator_note": unsafe_value()},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_packet_information_refresh_priority_v2_payload(
            {**payload, "average_priority_score": 0.5},
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.research_packet_information_refresh_priority_v2_payload(
            {**payload, "candidate_count": 2},
        )

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.research_packet_information_refresh_priority_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.research_packet_information_refresh_priority_v2_payload(
            {**payload, "extra_field": "not supported"},
        )


def test_module_scope_is_readonly_report_without_external_side_effects() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_information_refresh_priority_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "connect",
        "post",
        "put",
        "delete",
        "patch",
        "request",
        "send",
        "submit",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "float",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
