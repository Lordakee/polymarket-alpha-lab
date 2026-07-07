from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_probability_move_source_attribution_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def stamp() -> datetime:
    return datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-packet-probability-move-source-attribution-v2",
        "high_attribution_threshold": d("0.700000"),
        "medium_attribution_threshold": d("0.400000"),
        "source_update_weight": d("0.200000"),
        "official_source_event_weight": d("0.200000"),
        "contradiction_change_weight": d("0.200000"),
        "liquidity_movement_weight": d("0.150000"),
        "event_velocity_weight": d("0.150000"),
        "specialist_uncertainty_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchPacketProbabilityMoveSourceAttributionV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "event_title": "Alpha resolution update",
        "source_id": "source-alpha",
        "previous_probability": d("0.400000"),
        "current_probability": d("0.650000"),
        "source_update_score": d("0.900000"),
        "official_source_event_score": d("0.800000"),
        "contradiction_change_score": d("0.700000"),
        "liquidity_movement_score": d("0.600000"),
        "event_velocity_score": d("0.900000"),
        "specialist_uncertainty_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchPacketProbabilityMoveSourceAttributionV2Candidate(**values)


def build_report(*rows: object):
    module = api()
    source_rows = rows or (
        candidate(),
        candidate(
            packet_id="packet-beta",
            event_title="Beta resolution update",
            source_id="source-beta",
            previous_probability=d("0.500000"),
            current_probability=d("0.470000"),
            source_update_score=d("0.100000"),
            official_source_event_score=d("0.000000"),
            contradiction_change_score=d("0.100000"),
            liquidity_movement_score=d("0.100000"),
            event_velocity_score=d("0.200000"),
            specialist_uncertainty_score=d("0.800000"),
        ),
    )
    return module.build_research_packet_probability_move_source_attribution_v2(
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


def unsafe_terms() -> tuple[str, ...]:
    return (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "muta" + "tion",
        "b" + "uy",
        "se" + "ll",
        "tra" + "de",
    )


def test_builds_decimal_only_readonly_probability_move_source_attribution_report() -> None:
    module = api()

    report = build_report()

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.candidate_count == d("2")
    assert report.high_attribution_count == d("1")
    assert report.medium_attribution_count == d("0")
    assert report.low_attribution_count == d("1")
    assert report.average_probability_move == d("0.140000")
    assert report.max_probability_move == d("0.250000")
    assert report.average_total_attribution_score == d("0.460000")
    assert report.max_total_attribution_score == d("0.755000")
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-alpha",
        "packet-beta",
    )
    high_row = report.rows[0]
    assert high_row.rank == d("1")
    assert high_row.probability_move == d("0.250000")
    assert high_row.source_update_contribution == d("0.180000")
    assert high_row.official_source_event_contribution == d("0.160000")
    assert high_row.contradiction_change_contribution == d("0.140000")
    assert high_row.liquidity_movement_contribution == d("0.090000")
    assert high_row.event_velocity_contribution == d("0.135000")
    assert high_row.specialist_uncertainty_contribution == d("0.050000")
    assert high_row.total_attribution_score == d("0.755000")
    assert high_row.primary_attribution == "source_update"
    assert high_row.attribution_band == "high"
    assert high_row.research_action == "explain_source_move"
    assert high_row.reason_codes == (
        "source_update_primary",
        "official_source_event_high",
        "contradiction_change_elevated",
        "liquidity_movement_watch",
        "event_velocity_high",
        "specialist_uncertainty_normal",
        "attribution_high",
    )

    payload = report.payload
    assert payload == module.research_packet_probability_move_source_attribution_v2_payload(
        report,
    )
    assert (
        payload["config_version"]
        == "research-packet-probability-move-source-attribution-v2"
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["candidate_count"] == "2"
    assert payload["average_probability_move"] == "0.140000"
    assert payload["max_total_attribution_score"] == "0.755000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["total_attribution_score"] == "0.755000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is Decimal for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))
    json.dumps(payload, sort_keys=True)


def test_validation_requires_decimal_inputs_flags_and_frozen_dataclasses() -> None:
    module = api()
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.high_attribution_count = d("2")  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.rows[0].attribution_band = "low"  # type: ignore[misc]

    with pytest.raises(ValueError, match="previous_probability must be a Decimal"):
        candidate(previous_probability=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_update_score must be a Decimal"):
        candidate(source_update_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="specialist_uncertainty_score must be a Decimal"):
        candidate(specialist_uncertainty_score=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="source_update_score must be finite"):
        candidate(source_update_score=Decimal("NaN"))

    with pytest.raises(ValueError, match="event_velocity_score must be between 0 and 1"):
        candidate(event_velocity_score=d("1.000001"))

    with pytest.raises(ValueError, match="candidate must be readonly"):
        candidate(readonly=False)

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="attribution weights must total 1"):
        config(specialist_uncertainty_weight=d("0.200000"))

    with pytest.raises(ValueError, match="config_version must be supported"):
        config(config_version="research-packet-probability-move-source-attribution-v1")

    with pytest.raises(ValueError, match="candidate rows"):
        module.build_research_packet_probability_move_source_attribution_v2(
            [object()],
            config=config(),
            generated_at=stamp(),
        )


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, average_probability_move=d("0.150000"))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(
            report,
            rows=(
                replace(report.rows[0], event_title="Alpha resolution change"),
                report.rows[1],
            ),
        )

    payload = report.payload
    tampered_payload = {
        **payload,
        "rows": [
            {**payload["rows"][0], "event_title": "Alpha resolution change"},
            payload["rows"][1],
        ],
    }
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_packet_probability_move_source_attribution_v2_payload(
            tampered_payload,
        )

    refreshed_payload = {
        **tampered_payload,
        "derived_validation_digest": module.derive_research_packet_probability_move_source_attribution_v2_digest(
            tampered_payload,
        ),
    }
    assert (
        module.research_packet_probability_move_source_attribution_v2_payload(
            refreshed_payload,
        )["rows"][0]["event_title"]
        == "Alpha resolution change"
    )


def test_public_payload_rejects_all_unsafe_keys_values_and_numeric_scalars() -> None:
    module = api()
    payload = build_report().payload

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public payload key"):
            module.research_packet_probability_move_source_attribution_v2_payload(
                {**payload, f"{term}_hint": "blocked"},
            )

        with pytest.raises(ValueError, match="unsafe public payload value"):
            module.research_packet_probability_move_source_attribution_v2_payload(
                {**payload, "public_note": f"mentions {term}"},
            )

        with pytest.raises(ValueError, match="packet_id contains unsafe text"):
            candidate(packet_id=f"packet-{term}")

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_packet_probability_move_source_attribution_v2_payload(
            {**payload, "average_total_attribution_score": 0.5},
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.research_packet_probability_move_source_attribution_v2_payload(
            {**payload, "candidate_count": 2},
        )

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.research_packet_probability_move_source_attribution_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.research_packet_probability_move_source_attribution_v2_payload(
            {**payload, "extra_field": "not supported"},
        )


def test_public_api_and_module_scope_stay_pure_in_memory_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_ATTRIBUTION_V2_CONFIG_VERSION",
        "ResearchPacketProbabilityMoveSourceAttributionV2Candidate",
        "ResearchPacketProbabilityMoveSourceAttributionV2Config",
        "ResearchPacketProbabilityMoveSourceAttributionV2Report",
        "ResearchPacketProbabilityMoveSourceAttributionV2Row",
        "build_research_packet_probability_move_source_attribution_v2",
        "derive_research_packet_probability_move_source_attribution_v2_digest",
        "research_packet_probability_move_source_attribution_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = Path(
        "src/polymarket_alpha_lab/research_packet_probability_move_source_attribution_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
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
