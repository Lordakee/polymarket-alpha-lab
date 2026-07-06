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
        "polymarket_alpha_lab.research_packet_disconfirming_evidence_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def stamp() -> datetime:
    return datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-packet-disconfirming-evidence-gate-v2",
        "minimum_disconfirming_sources": d("2"),
        "minimum_opposition_sources": d("1"),
        "coverage_weight": d("0.400000"),
        "opposition_source_weight": d("0.300000"),
        "contradiction_penalty_weight": d("0.300000"),
        "pass_threshold": d("0.800000"),
        "review_threshold": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchPacketDisconfirmingEvidenceGateV2Config(**values)


def packet(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "market_question": "Will Alpha pass review?",
        "thesis_summary": "Independent checks support the packet thesis.",
        "disconfirming_source_count": d("2"),
        "opposition_source_count": d("1"),
        "supporting_source_count": d("3"),
        "contradiction_severity": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchPacketDisconfirmingEvidenceGateV2Packet(**values)


def build_report(*rows: object):
    module = api()
    source_rows = rows or (
        packet(packet_id="packet-alpha"),
        packet(
            packet_id="packet-beta",
            market_question="Will Beta pass review?",
            contradiction_severity=d("0.900000"),
        ),
        packet(
            packet_id="packet-gamma",
            market_question="Will Gamma pass review?",
            opposition_source_count=d("0"),
        ),
        packet(
            packet_id="packet-delta",
            market_question="Will Delta pass review?",
            disconfirming_source_count=d("0"),
            opposition_source_count=d("0"),
            supporting_source_count=d("1"),
            contradiction_severity=d("0.500000"),
        ),
    )
    return module.build_research_packet_disconfirming_evidence_gate_v2(
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


def test_builds_disconfirming_evidence_gate_with_expected_flags() -> None:
    module = api()

    report = build_report()

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.packet_count == d("4")
    assert report.pass_count == d("1")
    assert report.review_count == d("2")
    assert report.fail_count == d("1")
    assert report.average_gate_score == d("0.630000")
    assert report.min_gate_score == d("0.150000")
    assert report.max_contradiction_penalty_ratio == d("0.900000")
    assert len(report.derived_validation_digest) == 64

    by_id = {row.packet_id: row for row in report.rows}
    assert by_id["packet-alpha"].disconfirming_coverage_ratio == d("1.000000")
    assert by_id["packet-alpha"].opposition_coverage_ratio == d("1.000000")
    assert by_id["packet-alpha"].contradiction_penalty_ratio == d("0.100000")
    assert by_id["packet-alpha"].gate_score == d("0.970000")
    assert by_id["packet-alpha"].gate_status == "pass"
    assert "disconfirming_coverage_complete" in by_id["packet-alpha"].reason_codes
    assert "opposition_source_present" in by_id["packet-alpha"].reason_codes

    assert by_id["packet-beta"].gate_score == d("0.730000")
    assert by_id["packet-beta"].gate_status == "review"
    assert "contradiction_penalty_high" in by_id["packet-beta"].reason_codes

    assert by_id["packet-gamma"].opposition_coverage_ratio == d("0.000000")
    assert by_id["packet-gamma"].gate_status == "review"
    assert "missing_opposition_source" in by_id["packet-gamma"].reason_codes

    assert by_id["packet-delta"].disconfirming_coverage_ratio == d("0.000000")
    assert by_id["packet-delta"].gate_status == "fail"
    assert "disconfirming_coverage_missing" in by_id["packet-delta"].reason_codes

    payload = report.payload
    assert payload == module.research_packet_disconfirming_evidence_gate_v2_payload(
        report,
    )
    assert payload["config_version"] == "research-packet-disconfirming-evidence-gate-v2"
    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["packet_count"] == "4"
    assert payload["average_gate_score"] == "0.630000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["gate_score"] == "0.150000"
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
        report.pass_count = d("2")  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="disconfirming_source_count must be a Decimal"):
        packet(disconfirming_source_count=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="contradiction_severity must be a Decimal"):
        packet(contradiction_severity=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="opposition_source_count must be a Decimal"):
        packet(opposition_source_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="contradiction_severity must be finite"):
        packet(contradiction_severity=Decimal("NaN"))

    with pytest.raises(ValueError, match="contradiction_severity must be between 0 and 1"):
        packet(contradiction_severity=d("1.000001"))

    with pytest.raises(ValueError, match="packet must be readonly"):
        packet(readonly=False)

    with pytest.raises(ValueError, match="config must be report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="review_threshold must not exceed pass_threshold"):
        config(review_threshold=d("0.900000"))

    with pytest.raises(ValueError, match="packets must contain disconfirming evidence packet"):
        module.build_research_packet_disconfirming_evidence_gate_v2(
            [object()],
            config=config(),
            generated_at=stamp(),
        )


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, pass_count=d("0"))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(
            report,
            rows=(
                replace(
                    report.rows[0],
                    gate_score=d("0.250000"),
                    gate_status="fail",
                ),
                *report.rows[1:],
            ),
        )

    payload = report.payload
    tampered_payload = {
        **payload,
        "rows": [
            {**payload["rows"][0], "gate_score": "0.250000"},
            *payload["rows"][1:],
        ],
    }
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_packet_disconfirming_evidence_gate_v2_payload(tampered_payload)


def test_public_payload_rejects_unsafe_keys_values_and_numeric_values() -> None:
    module = api()
    payload = build_report().payload

    for fragment in unsafe_fragments():
        with pytest.raises(ValueError, match="unsafe public payload key"):
            module.research_packet_disconfirming_evidence_gate_v2_payload(
                {**payload, f"{fragment}_hint": "blocked"},
            )

        with pytest.raises(ValueError, match="unsafe public payload value"):
            module.research_packet_disconfirming_evidence_gate_v2_payload(
                {**payload, "operator_note": f"requires {fragment}"},
            )

    with pytest.raises(ValueError, match="unsafe public payload value"):
        module.research_packet_disconfirming_evidence_gate_v2_payload(
            {**payload, "operator_note": unsafe_value()},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_packet_disconfirming_evidence_gate_v2_payload(
            {**payload, "average_gate_score": 0.5},
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.research_packet_disconfirming_evidence_gate_v2_payload(
            {**payload, "packet_count": 4},
        )

    with pytest.raises(ValueError, match="payload must be paper_only"):
        module.research_packet_disconfirming_evidence_gate_v2_payload(
            {**payload, "paper_only": False},
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.research_packet_disconfirming_evidence_gate_v2_payload(
            {**payload, "extra_field": "not supported"},
        )


def test_module_scope_is_readonly_report_without_unsafe_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_disconfirming_evidence_gate_v2.py",
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
