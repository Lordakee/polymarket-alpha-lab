from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.probability_event_research_confidence_decay_report import (
    ProbabilityEventResearchConfidenceDecayReport,
    build_probability_event_research_confidence_decay_report,
    probability_event_research_confidence_decay_report_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def test_builds_readonly_decay_report_with_market_move_and_age_reasons() -> None:
    report = build_probability_event_research_confidence_decay_report(
        initial_confidence_probability=d("0.820000"),
        research_age_hours=d("30.000000"),
        source_staleness_hours=d("12.000000"),
        market_move_probability=d("0.080000"),
        decay_threshold_probability=d("0.100000"),
    )

    assert isinstance(report, ProbabilityEventResearchConfidenceDecayReport)
    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.decay_status == "decayed"
    assert report.decayed_confidence_probability == d("0.520000")
    assert report.reason_codes == (
        "research_age_confidence_decay",
        "source_staleness_confidence_decay",
        "market_move_confidence_decay",
        "confidence_decay_threshold_breached",
    )
    assert report.manual_next_step == "manual_research_refresh_required"
    assert len(report.payload_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.decay_status = "current"  # type: ignore[misc]


def test_builds_current_report_when_decay_is_inside_threshold() -> None:
    report = build_probability_event_research_confidence_decay_report(
        initial_confidence_probability=d("0.820000"),
        research_age_hours=d("2.000000"),
        source_staleness_hours=d("1.000000"),
        market_move_probability=d("0.010000"),
        decay_threshold_probability=d("0.100000"),
    )

    assert report.decay_status == "current"
    assert report.decayed_confidence_probability == d("0.790000")
    assert report.reason_codes == ("research_confidence_current",)
    assert report.manual_next_step == "manual_review_optional"


def test_public_payload_is_digest_guarded_and_uses_decimal_strings_only() -> None:
    report = build_probability_event_research_confidence_decay_report(
        initial_confidence_probability=d("0.730000"),
        research_age_hours=d("4.000000"),
        source_staleness_hours=d("3.000000"),
        market_move_probability=d("0.020000"),
        decay_threshold_probability=d("0.100000"),
    )

    payload = probability_event_research_confidence_decay_report_payload(report)
    assert payload == report.public_payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["initial_confidence_probability"] == "0.730000"
    assert payload["research_age_hours"] == "4.000000"
    assert payload["source_staleness_hours"] == "3.000000"
    assert payload["market_move_probability"] == "0.020000"
    assert payload["decayed_confidence_probability"] == "0.660000"
    assert payload["payload_digest"] == report.payload_digest
    assert not any(type(value) in (Decimal, int, float) for value in _walk_payload_values(payload))

    encoded = json.dumps(payload, sort_keys=True).lower()
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "key",
        "signature",
        "order",
        "trade",
        "execute",
        "database",
        "network",
        "persist",
    )
    assert all(fragment not in encoded for fragment in forbidden_fragments)

    tampered_payload = json.loads(json.dumps(payload))
    tampered_payload["decayed_confidence_probability"] = "0.999999"
    with pytest.raises(ValueError, match="payload_digest"):
        probability_event_research_confidence_decay_report_payload(tampered_payload)


def test_rejects_non_decimal_inputs_flags_and_manual_tampering() -> None:
    with pytest.raises(ValueError, match="initial_confidence_probability"):
        build_probability_event_research_confidence_decay_report(
            initial_confidence_probability=0.7,  # type: ignore[arg-type]
            research_age_hours=d("1.000000"),
            source_staleness_hours=d("1.000000"),
            market_move_probability=d("0.010000"),
            decay_threshold_probability=d("0.100000"),
        )
    with pytest.raises(ValueError, match="research_age_hours"):
        build_probability_event_research_confidence_decay_report(
            initial_confidence_probability=d("0.700000"),
            research_age_hours=d("-1.000000"),
            source_staleness_hours=d("1.000000"),
            market_move_probability=d("0.010000"),
            decay_threshold_probability=d("0.100000"),
        )
    with pytest.raises(ValueError, match="market_move_probability"):
        build_probability_event_research_confidence_decay_report(
            initial_confidence_probability=d("0.700000"),
            research_age_hours=d("1.000000"),
            source_staleness_hours=d("1.000000"),
            market_move_probability=d("1.010000"),
            decay_threshold_probability=d("0.100000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ProbabilityEventResearchConfidenceDecayReport(
            initial_confidence_probability=d("0.700000"),
            research_age_hours=d("1.000000"),
            source_staleness_hours=d("1.000000"),
            market_move_probability=d("0.010000"),
            decay_threshold_probability=d("0.100000"),
            decay_status="current",
            decayed_confidence_probability=d("0.680000"),
            reason_codes=("research_confidence_current",),
            manual_next_step="manual_review_optional",
            public_payload={},
            payload_digest="0" * 64,
            paper_only=False,
        )

    report = build_probability_event_research_confidence_decay_report(
        initial_confidence_probability=d("0.700000"),
        research_age_hours=d("1.000000"),
        source_staleness_hours=d("1.000000"),
        market_move_probability=d("0.010000"),
        decay_threshold_probability=d("0.100000"),
    )
    with pytest.raises(ValueError, match="payload_digest"):
        replace(
            report,
            decayed_confidence_probability=d("0.100000"),
            payload_digest=report.payload_digest,
        )


def test_module_has_no_forbidden_execution_or_io_surfaces() -> None:
    import polymarket_alpha_lab.probability_event_research_confidence_decay_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    forbidden_source_terms = (
        "live",
        "auth",
        "wallet",
        "keys",
        "signature",
        "auto_execute",
        "order",
        "trade",
        "database",
        "network",
        "persist",
        "request",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "write_text",
        "write_bytes",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
