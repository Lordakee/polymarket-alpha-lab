from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_counterevidence_quorum_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


def packet(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "event_slug": "event-alpha",
        "category": "macro",
        "supporting_source_count": d("4"),
        "counterevidence_source_count": d("2"),
        "independent_counterevidence_family_count": d("2"),
        "contradiction_severity_score": d("0.100000"),
        "reviewer_count": d("2"),
    }
    values.update(overrides)
    return module.ResearchPacketCounterevidenceQuorumGateV2Input(**values)


def build_report(*rows: object):
    module = api()
    source_rows = rows or (
        packet(
            packet_id="packet-gamma",
            event_slug="event-gamma",
            category="sports",
            supporting_source_count=d("3"),
            counterevidence_source_count=d("0"),
            independent_counterevidence_family_count=d("0"),
            contradiction_severity_score=d("0.850000"),
            reviewer_count=d("2"),
        ),
        packet(
            packet_id="packet-alpha",
            event_slug="event-alpha",
            category="macro",
            supporting_source_count=d("4"),
            counterevidence_source_count=d("2"),
            independent_counterevidence_family_count=d("2"),
            contradiction_severity_score=d("0.100000"),
            reviewer_count=d("2"),
        ),
        packet(
            packet_id="packet-beta",
            event_slug="event-beta",
            category="crypto",
            supporting_source_count=d("4"),
            counterevidence_source_count=d("1"),
            independent_counterevidence_family_count=d("1"),
            contradiction_severity_score=d("0.300000"),
            reviewer_count=d("1"),
        ),
    )
    return module.build_research_packet_counterevidence_quorum_gate_v2(
        source_rows,
        generated_at=GENERATED_AT,
    )


def test_builds_counterevidence_quorum_report_with_rollups() -> None:
    module = api()

    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == module.DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION
    )
    assert report.report_status == "block"
    assert report.packet_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.missing_counterevidence_count == d("1.000000")
    assert report.severe_contradiction_count == d("1.000000")
    assert report.insufficient_reviewer_count == d("1.000000")
    assert report.min_quorum_ratio == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-alpha",
        "packet-beta",
        "packet-gamma",
    )

    by_id = {row.packet_id: row for row in report.rows}
    assert by_id["packet-alpha"].counterevidence_quorum_ratio == d("0.500000")
    assert by_id["packet-alpha"].status == "pass"
    assert by_id["packet-alpha"].reason_codes == ("counterevidence_quorum_met",)

    assert by_id["packet-beta"].counterevidence_quorum_ratio == d("0.250000")
    assert by_id["packet-beta"].status == "watch"
    assert by_id["packet-beta"].reason_codes == (
        "counterevidence_quorum_below_minimum",
        "insufficient_independent_counterevidence_families",
        "insufficient_reviewers",
    )

    assert by_id["packet-gamma"].counterevidence_quorum_ratio == d("0.000000")
    assert by_id["packet-gamma"].status == "block"
    assert by_id["packet-gamma"].reason_codes == (
        "missing_counterevidence",
        "severe_contradiction",
    )

    assert report.reason_code_counts == (
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code="counterevidence_quorum_met",
            count=d("1.000000"),
        ),
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code="counterevidence_quorum_below_minimum",
            count=d("1.000000"),
        ),
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code="insufficient_independent_counterevidence_families",
            count=d("1.000000"),
        ),
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code="insufficient_reviewers",
            count=d("1.000000"),
        ),
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code="missing_counterevidence",
            count=d("1.000000"),
        ),
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code="severe_contradiction",
            count=d("1.000000"),
        ),
    )


def test_empty_input_returns_empty_status_and_zero_decimals() -> None:
    module = api()

    report = module.build_research_packet_counterevidence_quorum_gate_v2(
        (),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "empty"
    assert report.packet_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.missing_counterevidence_count == d("0.000000")
    assert report.severe_contradiction_count == d("0.000000")
    assert report.insufficient_reviewer_count == d("0.000000")
    assert report.min_quorum_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()


def test_payload_is_json_safe_and_derived_digest_rejects_tampering() -> None:
    module = api()
    report = build_report()

    assert len(report.derived_validation_digest) == 64
    payload = report.payload
    assert payload == module.research_packet_counterevidence_quorum_gate_v2_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-07T12:00:00Z"
    assert payload["packet_count"] == "3.000000"
    assert payload["min_quorum_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["counterevidence_quorum_ratio"] == "0.500000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert not any(type(value) is Decimal for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))

    tampered_payload = {
        **payload,
        "min_quorum_ratio": "0.250000",
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_counterevidence_quorum_gate_v2_payload(tampered_payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, pass_count=d("0.000000"))


def test_decimal_only_frozen_dataclasses_and_flag_validation() -> None:
    module = api()
    report = build_report()

    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])
    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="supporting_source_count must be a Decimal"):
        packet(supporting_source_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="counterevidence_source_count must be a Decimal"):
        packet(counterevidence_source_count=_DecimalSubclass("2"))
    with pytest.raises(ValueError, match="contradiction_severity_score must be a Decimal"):
        packet(contradiction_severity_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reviewer_count must be nonnegative"):
        packet(reviewer_count=d("-1"))
    with pytest.raises(ValueError, match="input must be readonly"):
        packet(readonly=False)
    with pytest.raises(ValueError, match="config must be paper_only"):
        module.ResearchPacketCounterevidenceQuorumGateV2Config(paper_only=False)


def test_safe_public_payload_rejects_unsafe_surface_and_static_writes() -> None:
    module = api()
    payload = build_report().payload

    for fragment in unsafe_fragments():
        with pytest.raises(ValueError, match="unsafe public payload key"):
            module.research_packet_counterevidence_quorum_gate_v2_payload(
                {**payload, f"{fragment}_hint": "blocked"},
            )
        with pytest.raises(ValueError, match="unsafe public payload value"):
            module.research_packet_counterevidence_quorum_gate_v2_payload(
                {**payload, "operator_note": f"requires {fragment}"},
            )
        with pytest.raises(ValueError, match="unsafe public value"):
            packet(event_slug=f"event-{fragment}")

    source = Path(
        "src/polymarket_alpha_lab/research_packet_counterevidence_quorum_gate_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "psycopg",
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

    unsafe_terms = unsafe_fragments()
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in unsafe_terms)
    for cls in (
        module.ResearchPacketCounterevidenceQuorumGateV2Config,
        module.ResearchPacketCounterevidenceQuorumGateV2Input,
        module.ResearchPacketCounterevidenceQuorumGateV2Row,
        module.ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount,
        module.ResearchPacketCounterevidenceQuorumGateV2Report,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in unsafe_terms)


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


def unsafe_fragments() -> tuple[str, ...]:
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
