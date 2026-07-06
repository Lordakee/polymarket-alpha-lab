from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_packet_resolution_rule_change_watch_v2 import (
    ResearchPacketResolutionRuleChangeWatchV2Config,
    ResearchPacketResolutionRuleChangeWatchV2Observation,
    build_research_packet_resolution_rule_change_watch_v2,
    research_packet_resolution_rule_change_watch_v2_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_packet_resolution_rule_change_watch_v2.py"
)


def _observation(
    *,
    packet_reference: str = "packet-alpha",
    event_title: str = "Will the rule settle from the agency memo?",
    source_label: str = "agency-memo",
    generated_at: datetime,
    checked_delta: timedelta = timedelta(minutes=5),
    rule_change_risk_score: Decimal = Decimal("0.050000"),
    ambiguity_score: Decimal = Decimal("0.050000"),
    source_reliability_score: Decimal = Decimal("0.900000"),
    rule_change_evidence_present: bool = False,
    ambiguous_resolution_terms: bool = False,
    conflicting_source_terms: bool = False,
    public_evidence_fields: tuple[tuple[str, str], ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchPacketResolutionRuleChangeWatchV2Observation:
    return ResearchPacketResolutionRuleChangeWatchV2Observation(
        packet_reference=packet_reference,
        event_title=event_title,
        source_label=source_label,
        resolution_rule_text="Settles from the final agency memo.",
        source_published_at=generated_at - checked_delta - timedelta(minutes=10),
        source_checked_at=generated_at - checked_delta,
        rule_change_risk_score=rule_change_risk_score,
        ambiguity_score=ambiguity_score,
        source_reliability_score=source_reliability_score,
        rule_change_evidence_present=rule_change_evidence_present,
        ambiguous_resolution_terms=ambiguous_resolution_terms,
        conflicting_source_terms=conflicting_source_terms,
        public_evidence_fields=public_evidence_fields,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build_report(
    observations: tuple[ResearchPacketResolutionRuleChangeWatchV2Observation, ...],
    *,
    generated_at: datetime,
    config: ResearchPacketResolutionRuleChangeWatchV2Config | None = None,
):
    return build_research_packet_resolution_rule_change_watch_v2(
        observations,
        generated_at=generated_at,
        config=config or ResearchPacketResolutionRuleChangeWatchV2Config(),
    )


def test_rule_change_risk_blocks_high_score_and_evidence() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    report = _build_report(
        (
            _observation(
                generated_at=generated_at,
                rule_change_risk_score=Decimal("0.850000"),
                rule_change_evidence_present=True,
            ),
        ),
        generated_at=generated_at,
    )

    assert report.status == "blocked"
    assert report.blocked_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.rows[0].rule_change_status == "rule_change_blocked"
    assert report.rows[0].rule_change_watch is True
    assert "resolution_rule_change_blocked" in report.rows[0].reason_codes


def test_source_freshness_blocks_stale_sources() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    report = _build_report(
        (
            _observation(
                generated_at=generated_at,
                checked_delta=timedelta(hours=3),
            ),
        ),
        generated_at=generated_at,
        config=ResearchPacketResolutionRuleChangeWatchV2Config(
            max_source_age_seconds=Decimal("3600.000000"),
            watch_source_age_seconds=Decimal("1800.000000"),
        ),
    )

    assert report.status == "blocked"
    assert report.rows[0].source_age_seconds == Decimal("10800.000000")
    assert report.rows[0].source_freshness_status == "source_freshness_blocked"
    assert report.rows[0].source_freshness_watch is True
    assert "source_freshness_blocked" in report.reason_codes


def test_ambiguity_flags_watch_when_scores_and_flags_are_present() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    report = _build_report(
        (
            _observation(
                generated_at=generated_at,
                ambiguity_score=Decimal("0.500000"),
                ambiguous_resolution_terms=True,
                conflicting_source_terms=True,
            ),
        ),
        generated_at=generated_at,
    )

    assert report.status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert report.rows[0].ambiguity_status == "ambiguity_watch"
    assert report.rows[0].ambiguity_watch is True
    assert "resolution_rule_ambiguity_watch" in report.rows[0].reason_codes


def test_payload_serializes_decimals_as_strings_and_keeps_hard_flags() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    report = _build_report((_observation(generated_at=generated_at),), generated_at=generated_at)
    payload = research_packet_resolution_rule_change_watch_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["source_count"], str)
    assert payload["source_count"] == "1.000000"
    assert isinstance(payload["rows"][0]["source_age_seconds"], str)
    assert payload["rows"][0]["source_age_seconds"] == "300.000000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimals() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    observation = _observation(generated_at=generated_at)
    report = _build_report((observation,), generated_at=generated_at)

    with pytest.raises(FrozenInstanceError):
        observation.source_label = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].watch_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketResolutionRuleChangeWatchV2Config(
            max_source_age_seconds=3600,  # type: ignore[arg-type]
        )

    for value in (report, *report.rows):
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name.endswith("_count") or field.name.endswith("_seconds"):
                assert type(item) is Decimal
            if field.name.endswith("_score"):
                assert type(item) is Decimal


def test_hard_flags_are_rejected_for_config_observations_and_report() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketResolutionRuleChangeWatchV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _observation(generated_at=generated_at, report_only=False)  # type: ignore[call-arg]

    report = _build_report((_observation(generated_at=generated_at),), generated_at=generated_at)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    report = _build_report((_observation(generated_at=generated_at),), generated_at=generated_at)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, config_version="tampered-v1")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    generated_at = datetime(2026, 1, 1, 12, tzinfo=UTC)
    with pytest.raises(ValueError, match="unsafe public"):
        _observation(
            generated_at=generated_at,
            public_evidence_fields=(("wallet_hint", "redacted"),),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        _observation(
            generated_at=generated_at,
            public_evidence_fields=(("memo", "contains live handling"),),
        )


def test_module_exposes_no_unsafe_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "db",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    forbidden_import_fragments = unsafe_terms
    forbidden_call_names = {
        "open",
        "requests",
        "urlopen",
        "socket",
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
    }
    public_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(term in alias.name.lower() for term in forbidden_import_fragments)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert not any(
                term in (node.module or "").lower()
                for term in forbidden_import_fragments
            )
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                public_names.append(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if not node.target.id.startswith("_"):
                public_names.append(node.target.id)

    assert public_names
    for public_name in public_names:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)
