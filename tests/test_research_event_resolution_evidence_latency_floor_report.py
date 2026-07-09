from __future__ import annotations

import ast
import dataclasses
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_evidence_latency_floor_report import (
    EventResolutionEvidenceLatencyFloorConfig,
    EventResolutionEvidenceLatencyFloorInput,
    EventResolutionEvidenceLatencyFloorReport,
    build_research_event_resolution_evidence_latency_floor_report,
    research_event_resolution_evidence_latency_floor_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
RESOLVED_AT = GENERATED_AT - timedelta(hours=3)


def evidence(
    private_candidate_ref: str = "candidate-a",
    *,
    resolved_at: datetime = RESOLVED_AT,
    first_evidence_at: datetime = RESOLVED_AT + timedelta(minutes=30),
    independent_source_count: Decimal = Decimal("3"),
    official_source_count: Decimal = Decimal("2"),
    corroborating_source_count: Decimal = Decimal("2"),
    conflicting_source_count: Decimal = Decimal("0"),
    evidence_confidence: Decimal = Decimal("0.9500"),
    reason_codes: tuple[str, ...] = ("official_evidence",),
) -> EventResolutionEvidenceLatencyFloorInput:
    return EventResolutionEvidenceLatencyFloorInput(
        private_candidate_ref=private_candidate_ref,
        resolved_at=resolved_at,
        first_evidence_at=first_evidence_at,
        independent_source_count=independent_source_count,
        official_source_count=official_source_count,
        corroborating_source_count=corroborating_source_count,
        conflicting_source_count=conflicting_source_count,
        evidence_confidence=evidence_confidence,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_empty_digest() -> None:
    report = build_research_event_resolution_evidence_latency_floor_report(
        (),
        generated_at=GENERATED_AT,
        config=EventResolutionEvidenceLatencyFloorConfig(),
    )

    assert report == EventResolutionEvidenceLatencyFloorReport(
        generated_at=GENERATED_AT,
        config_version="research_event_resolution_evidence_latency_floor_report_v1",
        row_count=Decimal("0.0000"),
        pass_count=Decimal("0.0000"),
        watch_count=Decimal("0.0000"),
        block_count=Decimal("0.0000"),
        median_latency_seconds=None,
        floor_latency_seconds=None,
        strongest_evidence_score=Decimal("0.0000"),
        weakest_evidence_score=Decimal("0.0000"),
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_latency_floor_scores_pass_watch_and_block_with_decimal_only_outputs() -> None:
    report = build_research_event_resolution_evidence_latency_floor_report(
        (
            evidence("pass-candidate", first_evidence_at=RESOLVED_AT + timedelta(minutes=45)),
            evidence(
                "watch-candidate",
                first_evidence_at=RESOLVED_AT + timedelta(minutes=5),
                independent_source_count=Decimal("2"),
                official_source_count=Decimal("1"),
                evidence_confidence=Decimal("0.7600"),
                reason_codes=("fast_resolution_evidence",),
            ),
            evidence(
                "block-candidate",
                first_evidence_at=RESOLVED_AT - timedelta(minutes=2),
                independent_source_count=Decimal("1"),
                official_source_count=Decimal("0"),
                corroborating_source_count=Decimal("0"),
                conflicting_source_count=Decimal("2"),
                evidence_confidence=Decimal("0.4000"),
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=EventResolutionEvidenceLatencyFloorConfig(),
    )

    assert [row.public_row_id for row in report.rows] == [
        "candidate:134fe9db4e72",
        "candidate:21c12590e5fb",
        "candidate:874f8817b816",
    ]
    assert [row.status for row in report.rows] == ["block", "pass", "watch"]
    block_row, pass_row, watch_row = report.rows
    assert pass_row.latency_seconds == Decimal("2700.0000")
    assert pass_row.latency_floor_score == Decimal("1.0000")
    assert pass_row.evidence_score == Decimal("0.9875")
    assert pass_row.reason_codes == ("official_evidence", "pass")
    assert watch_row.latency_seconds == Decimal("300.0000")
    assert watch_row.latency_floor_score == Decimal("0.2500")
    assert watch_row.status == "watch"
    assert block_row.latency_seconds == Decimal("-120.0000")
    assert block_row.latency_floor_score == Decimal("0.0000")
    assert block_row.status == "block"
    assert "pre_resolution_evidence" in block_row.reason_codes
    assert report.pass_count == Decimal("1.0000")
    assert report.watch_count == Decimal("1.0000")
    assert report.block_count == Decimal("1.0000")
    assert report.median_latency_seconds == Decimal("300.0000")
    assert report.floor_latency_seconds == Decimal("-120.0000")
    assert report.strongest_evidence_score == Decimal("0.9875")
    assert report.weakest_evidence_score == Decimal("0.1000")


def test_rows_reason_counts_and_digest_are_deterministic_without_raw_candidate_leakage() -> None:
    config = EventResolutionEvidenceLatencyFloorConfig()
    inputs = (
        evidence("z-secret-market-id", reason_codes=("zeta", "alpha")),
        evidence("a-secret-market-id", reason_codes=("alpha",)),
        evidence(
            "m-secret-market-id",
            first_evidence_at=RESOLVED_AT + timedelta(minutes=8),
            evidence_confidence=Decimal("0.7000"),
            reason_codes=("beta",),
        ),
    )

    report = build_research_event_resolution_evidence_latency_floor_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_resolution_evidence_latency_floor_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.public_row_id for row in report.rows] == sorted(
        row.public_row_id for row in report.rows
    )
    assert report.reason_code_counts == (
        ("alpha", Decimal("2.0000")),
        ("beta", Decimal("1.0000")),
        ("pass", Decimal("2.0000")),
        ("watch", Decimal("1.0000")),
        ("zeta", Decimal("1.0000")),
    )
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest

    payload = research_event_resolution_evidence_latency_floor_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    assert "secret-market-id" not in encoded
    assert "candidate_id" not in encoded


def test_payload_helper_uses_decimal_strings_and_revalidates_digest() -> None:
    report = build_research_event_resolution_evidence_latency_floor_report(
        (evidence(),),
        generated_at=GENERATED_AT,
        config=EventResolutionEvidenceLatencyFloorConfig(),
    )

    payload = research_event_resolution_evidence_latency_floor_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["evidence_score"] == "0.9875"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_evidence_latency_floor_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_ref"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_evidence_latency_floor_payload(unsafe_key_payload)


def test_validation_rejects_invalid_decimals_datetimes_statuses_and_flags() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_resolution_evidence_latency_floor_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=EventResolutionEvidenceLatencyFloorConfig(),
        )
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        evidence(resolved_at=datetime(2026, 7, 9, 9, 0))
    with pytest.raises(ValueError, match="first_evidence_at must be timezone-aware"):
        evidence(first_evidence_at=datetime(2026, 7, 9, 9, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="resolved_at must be a datetime"):
        evidence(resolved_at=DatetimeSubclass(2026, 7, 9, 9, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="independent_source_count"):
        evidence(independent_source_count=Decimal("-1"))
    with pytest.raises(ValueError, match="official_source_count"):
        evidence(official_source_count=Decimal("4"))
    with pytest.raises(ValueError, match="conflicting_source_count"):
        evidence(conflicting_source_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="evidence_confidence"):
        evidence(evidence_confidence=Decimal("1.1"))
    with pytest.raises(ValueError, match="minimum_latency_floor_seconds"):
        EventResolutionEvidenceLatencyFloorConfig(
            minimum_latency_floor_seconds=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="pass_evidence_score_threshold"):
        EventResolutionEvidenceLatencyFloorConfig(
            pass_evidence_score_threshold=Decimal("0.5000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(EventResolutionEvidenceLatencyFloorConfig(), paper_only=False)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = EventResolutionEvidenceLatencyFloorConfig()
    input_row = evidence()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.private_candidate_ref = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(EventResolutionEvidenceLatencyFloorConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(EventResolutionEvidenceLatencyFloorInput):
            pass


def test_static_module_has_no_forbidden_side_effect_or_leakage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_evidence_latency_floor_report.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "network",
        "database",
        "persist",
        "private_key",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )

    assert not [term for term in forbidden_terms if term in source.lower()]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)
