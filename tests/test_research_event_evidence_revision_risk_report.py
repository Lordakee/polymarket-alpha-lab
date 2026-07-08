from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import ast
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_evidence_revision_risk_report import (
    ResearchEventEvidenceRevisionRiskConfig,
    ResearchEventEvidenceRevisionRiskObservation,
    ResearchEventEvidenceRevisionRiskReasonCodeCount,
    ResearchEventEvidenceRevisionRiskReport,
    ResearchEventEvidenceRevisionRiskRow,
    build_research_event_evidence_revision_risk_report,
    research_event_evidence_revision_risk_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_evidence_revision_risk_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    event_label: str
    evidence_version_label: str
    observed_at: datetime
    claim_materiality_score: Decimal
    contradiction_pressure_score: Decimal
    conflicting_update: bool = False
    unresolved_contradiction: bool = False
    manual_review_signal: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventEvidenceRevisionRiskConfig:
    values = {
        "config_version": "research-event-evidence-revision-risk-report-v0",
        "watch_stale_evidence_seconds": d("21600"),
        "watch_materiality_score": d("0.300000"),
        "block_materiality_score": d("0.700000"),
        "watch_contradiction_pressure_score": d("0.300000"),
        "block_contradiction_pressure_score": d("0.700000"),
        "watch_manual_review_urgency_score": d("0.300000"),
        "block_manual_review_urgency_score": d("0.700000"),
        "watch_revision_risk_score": d("0.300000"),
        "block_revision_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return ResearchEventEvidenceRevisionRiskConfig(**values)


def observation(
    index: int,
    *,
    event_label: str = "event-alpha",
    evidence_version_label: str | None = None,
    observed_at: datetime | None = None,
    claim_materiality_score: Decimal = d("0.100000"),
    contradiction_pressure_score: Decimal = d("0.100000"),
    conflicting_update: bool = False,
    unresolved_contradiction: bool = False,
    manual_review_signal: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventEvidenceRevisionRiskObservation:
    return ResearchEventEvidenceRevisionRiskObservation(
        event_label=event_label,
        evidence_version_label=evidence_version_label or f"revision-{index:03d}",
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        claim_materiality_score=claim_materiality_score,
        contradiction_pressure_score=contradiction_pressure_score,
        conflicting_update=conflicting_update,
        unresolved_contradiction=unresolved_contradiction,
        manual_review_signal=manual_review_signal,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventEvidenceRevisionRiskConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventEvidenceRevisionRiskReport:
    return build_research_event_evidence_revision_risk_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_stable_recent_evidence_passes_revision_risk_report() -> None:
    risk_report = report(
        (
            observation(2, observed_at=GENERATED_AT - timedelta(minutes=30)),
            observation(
                1,
                claim_materiality_score=d("0.200000"),
                contradiction_pressure_score=d("0.100000"),
                reason_codes=("reviewed",),
            ),
        ),
    )

    assert type(risk_report) is ResearchEventEvidenceRevisionRiskReport
    assert risk_report.generated_at == GENERATED_AT
    assert risk_report.config_version == "research-event-evidence-revision-risk-report-v0"
    assert risk_report.event_count == d("1")
    assert risk_report.evidence_update_count == d("2")
    assert risk_report.pass_count == d("1")
    assert risk_report.watch_count == d("0")
    assert risk_report.block_count == d("0")
    assert risk_report.conflicting_update_count == d("0")
    assert risk_report.stale_evidence_update_count == d("0")
    assert risk_report.material_change_count == d("0")
    assert risk_report.unresolved_contradiction_count == d("0")
    assert risk_report.manual_review_signal_count == d("0")
    assert risk_report.status == "pass"
    assert risk_report.reason_codes == ("evidence_revision_risk_pass",)
    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True

    row = risk_report.rows[0]
    assert type(row) is ResearchEventEvidenceRevisionRiskRow
    assert row.event_label == "event-alpha"
    assert row.evidence_update_count == d("2")
    assert row.conflicting_update_count == d("0")
    assert row.stale_evidence_update_count == d("0")
    assert row.material_change_count == d("0")
    assert row.unresolved_contradiction_count == d("0")
    assert row.manual_review_signal_count == d("0")
    assert row.latest_evidence_age_seconds == d("1800.000000")
    assert row.max_evidence_age_seconds == d("3600.000000")
    assert row.claim_materiality_score == d("0.200000")
    assert row.contradiction_pressure_score == d("0.100000")
    assert row.manual_review_urgency_score == d("0.080000")
    assert row.revision_risk_score == d("0.065000")
    assert row.status == "pass"
    assert row.evidence_version_labels == ("revision-001", "revision-002")
    assert row.reason_codes == (
        "conflicting_updates_clear",
        "contradiction_pressure_low",
        "evidence_recent",
        "evidence_revision_risk_pass",
        "input_reviewed",
        "manual_review_not_needed",
        "materiality_low",
        "revision_risk_score_low",
        "unresolved_contradiction_clear",
    )


def test_conflicting_stale_material_revisions_roll_up_to_block_report() -> None:
    risk_report = report(
        (
            observation(
                1,
                event_label="event-watch",
                claim_materiality_score=d("0.450000"),
                contradiction_pressure_score=d("0.200000"),
            ),
            observation(
                2,
                event_label="event-block",
                observed_at=GENERATED_AT - timedelta(hours=10),
                claim_materiality_score=d("0.800000"),
                contradiction_pressure_score=d("0.850000"),
                conflicting_update=True,
                unresolved_contradiction=True,
                manual_review_signal=True,
            ),
            observation(
                3,
                event_label="event-block",
                observed_at=GENERATED_AT - timedelta(hours=8),
                claim_materiality_score=d("0.300000"),
                contradiction_pressure_score=d("0.400000"),
            ),
        ),
    )

    assert risk_report.status == "block"
    assert risk_report.event_count == d("2")
    assert risk_report.evidence_update_count == d("3")
    assert risk_report.pass_count == d("0")
    assert risk_report.watch_count == d("1")
    assert risk_report.block_count == d("1")
    assert risk_report.conflicting_update_count == d("1")
    assert risk_report.stale_evidence_update_count == d("2")
    assert risk_report.material_change_count == d("2")
    assert risk_report.unresolved_contradiction_count == d("1")
    assert risk_report.manual_review_signal_count == d("1")
    assert tuple(row.status for row in risk_report.rows) == ("block", "watch")

    blocked_row = risk_report.rows[0]
    assert blocked_row.event_label == "event-block"
    assert blocked_row.conflicting_update_count == d("1")
    assert blocked_row.stale_evidence_update_count == d("2")
    assert blocked_row.material_change_count == d("1")
    assert blocked_row.unresolved_contradiction_count == d("1")
    assert blocked_row.manual_review_signal_count == d("1")
    assert blocked_row.latest_evidence_age_seconds == d("28800.000000")
    assert blocked_row.max_evidence_age_seconds == d("36000.000000")
    assert blocked_row.claim_materiality_score == d("0.800000")
    assert blocked_row.contradiction_pressure_score == d("0.850000")
    assert blocked_row.manual_review_urgency_score == d("0.700000")
    assert blocked_row.revision_risk_score == d("0.747500")
    assert blocked_row.reason_codes == (
        "conflicting_updates_present",
        "contradiction_pressure_block",
        "evidence_revision_risk_block",
        "evidence_stale",
        "manual_review_needed",
        "manual_review_urgency_block",
        "materiality_block",
        "revision_risk_score_block",
        "unresolved_contradiction_present",
    )

    watch_row = risk_report.rows[1]
    assert watch_row.event_label == "event-watch"
    assert watch_row.status == "watch"
    assert watch_row.manual_review_urgency_score == d("0.170000")
    assert watch_row.revision_risk_score == d("0.140000")
    assert watch_row.reason_codes == (
        "conflicting_updates_clear",
        "contradiction_pressure_low",
        "evidence_recent",
        "evidence_revision_risk_watch",
        "manual_review_not_needed",
        "materiality_watch",
        "revision_risk_score_low",
        "unresolved_contradiction_clear",
    )


def test_payload_is_public_decimal_only_deterministic_and_digest_checked() -> None:
    first = report((observation(2), observation(1)))
    second = report((observation(1), observation(2)))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)

    payload = research_event_evidence_revision_risk_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["revision_risk_score"] == "0.045000"
    assert payload["rows"][0]["manual_review_urgency_score"] == "0.060000"
    assert research_event_evidence_revision_risk_report_payload(payload) == payload
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    for unsafe_fragment in (
        "raw",
        "market",
        "source",
        "url",
        "wallet",
        "order",
        "trade",
        "recommend",
        "sizing",
    ):
        assert unsafe_fragment not in encoded.lower()

    tampered = json.loads(encoded)
    tampered["rows"][0]["revision_risk_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_evidence_revision_risk_report_payload(tampered)


def test_supplied_shapes_reason_counts_and_empty_report_are_deterministic() -> None:
    risk_report = report(
        (
            SuppliedObservationShape(
                event_label="event-zeta",
                evidence_version_label="revision-z",
                observed_at=GENERATED_AT - timedelta(minutes=10),
                claim_materiality_score=d("0.100000"),
                contradiction_pressure_score=d("0.100000"),
                reason_codes=("zeta", "alpha"),
            ),
            observation(1, event_label="event-alpha"),
        ),
    )

    assert tuple(row.event_label for row in risk_report.rows) == ("event-alpha", "event-zeta")
    assert tuple(
        (count.reason_code, count.count)
        for count in risk_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert type(risk_report.reason_code_counts[0]) is ResearchEventEvidenceRevisionRiskReasonCodeCount

    empty = report(())
    assert empty.status == "block"
    assert empty.reason_codes == ("no_evidence_revision_observations",)
    assert empty.reason_code_counts == (
        ResearchEventEvidenceRevisionRiskReasonCodeCount(
            reason_code="no_evidence_revision_observations",
            count=d("1"),
        ),
    )


def test_validation_rejects_bad_types_times_flags_and_unsafe_identifiers() -> None:
    with pytest.raises(ValueError, match="watch_stale_evidence_seconds"):
        config(watch_stale_evidence_seconds=d("0"))
    with pytest.raises(ValueError, match="watch_materiality_score"):
        config(watch_materiality_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_materiality_score"):
        config(block_materiality_score=d("0.200000"))
    with pytest.raises(ValueError, match="claim_materiality_score"):
        observation(1, claim_materiality_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="contradiction_pressure_score"):
        observation(1, contradiction_pressure_score=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_label"):
        observation(1, event_label="raw-market-123")
    with pytest.raises(ValueError, match="evidence_version_label"):
        observation(1, evidence_version_label="source-url-1")
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="conflicting_update"):
        replace(observation(1), conflicting_update=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("NeedsReview",))
    with pytest.raises(ValueError, match="unsafe public value"):
        observation(1, reason_codes=("wallet_token",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    risk_report = report((observation(1), observation(2)))

    with pytest.raises(FrozenInstanceError):
        risk_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(risk_report.rows[0], status="block")
    with pytest.raises(ValueError, match="manual_review_signal_count"):
        replace(risk_report, manual_review_signal_count=d("1"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(risk_report, derived_validation_digest="0" * 64)


def test_owned_module_has_no_network_database_filesystem_execution_or_advice_surface() -> None:
    module_tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(module_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(module_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    forbidden_imports = {
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "psycopg",
        "sqlalchemy",
        "asyncpg",
    }
    forbidden_calls = {"open", "connect", "cursor", "execute", "write_text", "write_bytes"}
    forbidden_advice_terms = ("buy", "sell", "trade", "recommend", "sizing")

    assert imported_roots.isdisjoint(forbidden_imports)
    for node in ast.walk(module_tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls

    lowered = MODULE_PATH.read_text(encoding="utf-8").lower()
    for term in forbidden_advice_terms:
        assert term not in lowered


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
