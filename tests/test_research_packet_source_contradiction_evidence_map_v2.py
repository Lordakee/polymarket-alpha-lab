from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect
import json

import pytest

from polymarket_alpha_lab import research_packet_source_contradiction_evidence_map_v2 as module
from polymarket_alpha_lab.research_packet_source_contradiction_evidence_map_v2 import (
    ResearchPacketSourceContradictionEvidence,
    ResearchPacketSourceContradictionEvidenceMapConfig,
    build_research_packet_source_contradiction_evidence_map_v2_report,
    research_packet_source_contradiction_evidence_map_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    evidence_id: str,
    *,
    source_family: str,
    source_id: str,
    source_role: str,
    hours_ago: int,
    independence_group: str,
    claimed_outcome: str,
    official_source_rank_score: str,
    resolution_rule_relevance_score: str,
) -> ResearchPacketSourceContradictionEvidence:
    return ResearchPacketSourceContradictionEvidence(
        packet_id="packet-fed-rate-cut",
        event_id="event-fed-rate-cut",
        evidence_id=evidence_id,
        source_family=source_family,
        source_id=source_id,
        source_role=source_role,
        observed_at=GENERATED_AT - timedelta(hours=hours_ago),
        independence_group=independence_group,
        claimed_outcome=claimed_outcome,
        official_source_rank_score=d(official_source_rank_score),
        resolution_rule_relevance_score=d(resolution_rule_relevance_score),
    )


def config() -> ResearchPacketSourceContradictionEvidenceMapConfig:
    return ResearchPacketSourceContradictionEvidenceMapConfig(
        config_version="research-packet-source-contradiction-evidence-map-v2-test",
        recency_window_hours=d("24.000000"),
        severe_contradiction_threshold=d("0.600000"),
    )


def report():
    return build_research_packet_source_contradiction_evidence_map_v2_report(
        (
            evidence(
                "evidence-official",
                source_family="official-release",
                source_id="fomc-release",
                source_role="official",
                hours_ago=1,
                independence_group="federal-reserve",
                claimed_outcome="rate-cut-yes",
                official_source_rank_score="0.950000",
                resolution_rule_relevance_score="1.000000",
            ),
            evidence(
                "evidence-wire-a",
                source_family="newswire",
                source_id="wire-a",
                source_role="supporting",
                hours_ago=2,
                independence_group="wire-a",
                claimed_outcome="rate-cut-no",
                official_source_rank_score="0.200000",
                resolution_rule_relevance_score="0.800000",
            ),
            evidence(
                "evidence-wire-b",
                source_family="newswire",
                source_id="wire-b",
                source_role="supporting",
                hours_ago=3,
                independence_group="wire-b",
                claimed_outcome="rate-cut-no",
                official_source_rank_score="0.100000",
                resolution_rule_relevance_score="0.700000",
            ),
            evidence(
                "evidence-social",
                source_family="social",
                source_id="social-a",
                source_role="proxy",
                hours_ago=12,
                independence_group="social-a",
                claimed_outcome="rate-cut-yes",
                official_source_rank_score="0.050000",
                resolution_rule_relevance_score="0.300000",
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )


def test_maps_contradictory_evidence_by_family_rank_recency_independence_and_rule_relevance() -> None:
    mapped = report()

    assert mapped.packet_count == d("1.000000")
    assert mapped.evidence_count == d("4.000000")
    assert mapped.source_family_count == d("3.000000")
    assert mapped.contradiction_count == d("2.000000")
    assert mapped.official_source_contradiction_count == d("2.000000")
    assert mapped.status == "blocked"
    assert mapped.reason_codes == (
        "source_contradiction_present",
        "official_source_ranked_contradiction_present",
        "severe_contradiction_present",
        "source_contradiction_blocked",
    )

    wire_a = next(row for row in mapped.evidence_rows if row.evidence_id == "evidence-wire-a")
    assert wire_a.source_family == "newswire"
    assert wire_a.reference_outcome == "rate-cut-yes"
    assert wire_a.contradicts_reference is True
    assert wire_a.reference_official_source_rank_score == d("0.950000")
    assert wire_a.evidence_age_hours == d("2.000000")
    assert wire_a.recency_weight == d("0.916667")
    assert wire_a.independent_source_family_count == d("3.000000")
    assert wire_a.independent_evidence_count == d("4.000000")
    assert wire_a.resolution_rule_relevance_score == d("0.800000")
    assert wire_a.contradiction_severity_score == d("0.696667")
    assert wire_a.status == "blocked"

    official = next(row for row in mapped.evidence_rows if row.evidence_id == "evidence-official")
    assert official.contradicts_reference is False
    assert official.contradiction_severity_score == d("0.000000")
    assert official.status == "clear"

    family = next(row for row in mapped.source_family_rows if row.source_family == "newswire")
    assert family.evidence_count == d("2.000000")
    assert family.contradicted_evidence_count == d("2.000000")
    assert family.max_official_source_rank_score == d("0.200000")
    assert family.max_reference_official_source_rank_score == d("0.950000")
    assert family.max_contradiction_severity_score == d("0.696667")
    assert family.status == "blocked"


def test_payload_uses_decimal_strings_flags_digest_and_no_numeric_scalars() -> None:
    mapped = report()

    payload = research_packet_source_contradiction_evidence_map_v2_payload(mapped)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["evidence_count"] == "4.000000"
    assert payload["contradiction_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == mapped.derived_validation_digest
    assert len(mapped.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in mapped.derived_validation_digest)
    payload_wire_a = next(
        row for row in payload["evidence_rows"] if row["evidence_id"] == "evidence-wire-a"
    )
    assert payload_wire_a["contradiction_severity_score"] == "0.696667"
    assert_no_float_or_public_numeric_scalars(payload)
    json.dumps(payload, sort_keys=True)


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    mapped = report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(mapped, contradiction_count=d("3.000000"))

    payload = research_packet_source_contradiction_evidence_map_v2_payload(mapped)
    tampered = dict(payload)
    tampered["status"] = "clear"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_packet_source_contradiction_evidence_map_v2_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_source_contradiction_evidence_map_v2_payload(missing_digest)


def test_rejects_unsafe_public_keys_and_values_for_execution_surfaces() -> None:
    payload = research_packet_source_contradiction_evidence_map_v2_payload(report())

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
        "signing_key",
        "mutation_endpoint",
        "buy_flag",
        "sell_flag",
        "trade_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            research_packet_source_contradiction_evidence_map_v2_payload(unsafe_payload)

    unsafe_values = (
        "live mode enabled",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
        "signing key configured",
        "mutation request configured",
        "buy action configured",
        "sell action configured",
        "trade action configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_rows = [dict(row) for row in payload["evidence_rows"]]
        unsafe_rows[0]["source_id"] = unsafe_value
        unsafe_payload["evidence_rows"] = unsafe_rows
        with pytest.raises(ValueError, match="unsafe"):
            research_packet_source_contradiction_evidence_map_v2_payload(unsafe_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    mapped = report()

    assert is_dataclass(ResearchPacketSourceContradictionEvidence)
    with pytest.raises(FrozenInstanceError):
        mapped.evidence_rows[0].packet_id = "other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(mapped, paper_only=False)

    class TaggedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="official_source_rank_score must be a Decimal"):
        evidence(
            "evidence-tagged",
            source_family="official-release",
            source_id="fomc-tagged",
            source_role="official",
            hours_ago=1,
            independence_group="federal-reserve",
            claimed_outcome="rate-cut-yes",
            official_source_rank_score="0.950000",
            resolution_rule_relevance_score="1.000000",
        ).__class__(
            packet_id="packet-fed-rate-cut",
            event_id="event-fed-rate-cut",
            evidence_id="evidence-tagged",
            source_family="official-release",
            source_id="fomc-tagged",
            source_role="official",
            observed_at=GENERATED_AT,
            independence_group="federal-reserve",
            claimed_outcome="rate-cut-yes",
            official_source_rank_score=TaggedDecimal("0.950000"),
            resolution_rule_relevance_score=d("1.000000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_packet_source_contradiction_evidence_map_v2_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )


def test_module_is_readonly_report_only_and_has_no_live_io_surface() -> None:
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "eval", "exec", "compile"}

    assert "paper_only" in source
    assert "report_only" in source
    assert "readonly" in source


def assert_no_float_or_public_numeric_scalars(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float found in payload: {value!r}")
    if type(value) is int:
        raise AssertionError(f"integer found in payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_public_numeric_scalars(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_public_numeric_scalars(child)
