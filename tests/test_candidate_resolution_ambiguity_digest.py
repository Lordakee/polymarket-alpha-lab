from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.candidate_resolution_ambiguity_digest import (
    CandidateResolutionAmbiguityDigestConfig,
    CandidateResolutionAmbiguityDigestReasonCodeCount,
    CandidateResolutionAmbiguityDigestReport,
    CandidateResolutionAmbiguityFacts,
    build_candidate_resolution_ambiguity_digest,
    candidate_resolution_ambiguity_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


@dataclass(frozen=True)
class SuppliedFactsShape:
    redacted_public_reference: str
    outcome_criteria_clarity: Decimal
    source_hierarchy_strength: Decimal
    dispute_risk: Decimal
    revision_risk: Decimal
    adjudication_dependency: Decimal
    close_resolution_timing_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> CandidateResolutionAmbiguityDigestConfig:
    values = {
        "config_version": "candidate-resolution-ambiguity-digest-v0",
        "min_pass_outcome_criteria_clarity": d("0.800000"),
        "min_watch_outcome_criteria_clarity": d("0.600000"),
        "min_pass_source_hierarchy_strength": d("0.700000"),
        "min_watch_source_hierarchy_strength": d("0.500000"),
        "max_pass_dispute_risk": d("0.250000"),
        "max_watch_dispute_risk": d("0.500000"),
        "max_pass_revision_risk": d("0.250000"),
        "max_watch_revision_risk": d("0.500000"),
        "max_pass_adjudication_dependency": d("0.200000"),
        "max_watch_adjudication_dependency": d("0.450000"),
        "max_pass_close_resolution_timing_risk": d("0.300000"),
        "max_watch_close_resolution_timing_risk": d("0.600000"),
    }
    values.update(overrides)
    return CandidateResolutionAmbiguityDigestConfig(**values)


def facts(
    redacted_public_reference: str = "candidate_ref_aaaaaaaaaaaaaaaa",
    *,
    outcome_criteria_clarity: Decimal = d("0.910000"),
    source_hierarchy_strength: Decimal = d("0.840000"),
    dispute_risk: Decimal = d("0.050000"),
    revision_risk: Decimal = d("0.060000"),
    adjudication_dependency: Decimal = d("0.030000"),
    close_resolution_timing_risk: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CandidateResolutionAmbiguityFacts:
    return CandidateResolutionAmbiguityFacts(
        redacted_public_reference=redacted_public_reference,
        outcome_criteria_clarity=outcome_criteria_clarity,
        source_hierarchy_strength=source_hierarchy_strength,
        dispute_risk=dispute_risk,
        revision_risk=revision_risk,
        adjudication_dependency=adjudication_dependency,
        close_resolution_timing_risk=close_resolution_timing_risk,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: CandidateResolutionAmbiguityDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CandidateResolutionAmbiguityDigestReport:
    return build_candidate_resolution_ambiguity_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_clear_resolution_facts_pass_and_public_payload_is_redacted() -> None:
    summary = report((facts(),))

    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == "candidate-resolution-ambiguity-digest-v0"
    assert summary.ambiguity_status == "pass"
    assert summary.candidate_count == d("1")
    assert summary.pass_count == d("1")
    assert summary.watch_count == ZERO
    assert summary.blocked_count == ZERO
    assert summary.reason_codes == ("resolution_ambiguity_clear",)
    assert summary.reason_code_counts == (
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="resolution_ambiguity_clear",
            count=d("1"),
        ),
    )

    row = summary.rows[0]
    assert row.redacted_public_reference == "candidate_ref_aaaaaaaaaaaaaaaa"
    assert row.ambiguity_status == "pass"
    assert row.reason_codes == ("resolution_ambiguity_clear",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = candidate_resolution_ambiguity_digest_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["redacted_public_reference"] == (
        "candidate_ref_aaaaaaaaaaaaaaaa"
    )
    assert "market_id" not in encoded
    assert "question" not in encoded
    assert "slug" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_ambiguous_outcome_criteria_watch_and_block_statuses() -> None:
    summary = report(
        (
            facts(
                "candidate_ref_bbbbbbbbbbbbbbbb",
                outcome_criteria_clarity=d("0.720000"),
            ),
            facts(
                "candidate_ref_cccccccccccccccc",
                outcome_criteria_clarity=d("0.400000"),
                source_hierarchy_strength=d("0.420000"),
            ),
        ),
    )

    assert summary.ambiguity_status == "blocked"
    assert summary.watch_count == d("1")
    assert summary.blocked_count == d("1")
    assert tuple(row.redacted_public_reference for row in summary.rows) == (
        "candidate_ref_cccccccccccccccc",
        "candidate_ref_bbbbbbbbbbbbbbbb",
    )
    assert summary.rows[0].ambiguity_status == "blocked"
    assert summary.rows[0].reason_codes == (
        "outcome_criteria_unclear",
        "source_hierarchy_weak",
    )
    assert summary.rows[1].ambiguity_status == "watch"
    assert summary.rows[1].reason_codes == ("outcome_criteria_unclear",)


def test_dispute_revision_adjudication_and_timing_risks_are_counted() -> None:
    summary = report(
        (
            facts(
                "candidate_ref_dddddddddddddddd",
                dispute_risk=d("0.300000"),
                revision_risk=d("0.550000"),
                adjudication_dependency=d("0.470000"),
                close_resolution_timing_risk=d("0.700000"),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.ambiguity_status == "blocked"
    assert row.reason_codes == (
        "dispute_risk_elevated",
        "revision_risk_elevated",
        "adjudication_dependency_present",
        "close_resolution_timing_risk",
    )
    assert summary.dispute_risk_count == d("1")
    assert summary.revision_risk_count == d("1")
    assert summary.adjudication_dependency_count == d("1")
    assert summary.close_resolution_timing_risk_count == d("1")


def test_rows_reason_counts_and_summary_reasons_are_deterministic() -> None:
    summary = report(
        (
            facts("candidate_ref_ffffffffffffffff"),
            facts(
                "candidate_ref_eeeeeeeeeeeeeeee",
                dispute_risk=d("0.300000"),
                revision_risk=d("0.300000"),
            ),
            facts(
                "candidate_ref_bbbbbbbbbbbbbbbb",
                outcome_criteria_clarity=d("0.300000"),
            ),
            facts(
                "candidate_ref_aaaaaaaaaaaaaaaa",
                source_hierarchy_strength=d("0.300000"),
            ),
        ),
    )

    assert tuple(row.redacted_public_reference for row in summary.rows) == (
        "candidate_ref_aaaaaaaaaaaaaaaa",
        "candidate_ref_bbbbbbbbbbbbbbbb",
        "candidate_ref_eeeeeeeeeeeeeeee",
        "candidate_ref_ffffffffffffffff",
    )
    assert summary.reason_codes == (
        "outcome_criteria_unclear",
        "source_hierarchy_weak",
        "dispute_risk_elevated",
        "revision_risk_elevated",
        "resolution_ambiguity_clear",
    )
    assert summary.reason_code_counts == (
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="dispute_risk_elevated",
            count=d("1"),
        ),
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="outcome_criteria_unclear",
            count=d("1"),
        ),
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="resolution_ambiguity_clear",
            count=d("1"),
        ),
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="revision_risk_elevated",
            count=d("1"),
        ),
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="source_hierarchy_weak",
            count=d("1"),
        ),
    )


def test_decimal_normalization_and_supplied_shape_coercion() -> None:
    summary = report(
        (
            SuppliedFactsShape(
                redacted_public_reference="candidate_ref_1111111111111111",
                outcome_criteria_clarity=d("0.8234561"),
                source_hierarchy_strength=d("0.7654321"),
                dispute_risk=d("0.1111111"),
                revision_risk=d("0.2222222"),
                adjudication_dependency=d("0.1234567"),
                close_resolution_timing_risk=d("0.2345678"),
            ),
        ),
        generated_at=datetime(2026, 7, 7, 7, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    row = summary.rows[0]
    assert summary.generated_at == GENERATED_AT
    assert row.outcome_criteria_clarity == d("0.823456")
    assert row.source_hierarchy_strength == d("0.765432")
    assert row.dispute_risk == d("0.111111")
    assert row.revision_risk == d("0.222222")
    assert row.adjudication_dependency == d("0.123457")
    assert row.close_resolution_timing_risk == d("0.234568")

    payload = candidate_resolution_ambiguity_digest_payload(summary)
    assert payload["rows"][0]["outcome_criteria_clarity"] == "0.823456"
    assert payload["rows"][0]["adjudication_dependency"] == "0.123457"


def test_empty_input_blocks_with_zero_counts() -> None:
    summary = report(())

    assert summary.ambiguity_status == "blocked"
    assert summary.candidate_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.blocked_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == ("no_candidate_resolution_facts",)
    assert summary.reason_code_counts == (
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code="no_candidate_resolution_facts",
            count=d("1"),
        ),
    )


def test_hard_flags_freezing_and_validation_errors() -> None:
    summary = report((facts(),))

    with pytest.raises(FrozenInstanceError):
        summary.ambiguity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].ambiguity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        facts(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        report((facts(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        report((facts(readonly=False),))
    with pytest.raises(ValueError, match="config"):
        report((facts(),), cfg=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        facts(outcome_criteria_clarity=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((facts(),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="min_watch_outcome_criteria_clarity"):
        config(min_watch_outcome_criteria_clarity=d("0.900000"))


def test_unsafe_raw_references_and_public_payloads_are_rejected() -> None:
    with pytest.raises(ValueError, match="redacted_public_reference"):
        facts(redacted_public_reference="market-123")
    with pytest.raises(ValueError, match="redacted_public_reference"):
        facts(redacted_public_reference="candidate_ref_nothex000000")

    payload = candidate_resolution_ambiguity_digest_payload(report((facts(),)))
    unsafe_payloads = (
        payload | {"raw_market_id": "market-123"},
        payload | {"market_question": "Will this resolve yes?"},
        payload | {"market_slug": "will-event-happen"},
        payload | {"condition_id": "0x123"},
        payload | {"source_url": "https://example.test/raw-market"},
        payload | {"rows": [payload["rows"][0] | {"raw_reference": "market-123"}]},
        payload | {"paper_only": False},
    )

    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe|must be True"):
            candidate_resolution_ambiguity_digest_payload(unsafe_payload)


def test_static_pure_boundary_has_no_persistence_network_or_live_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "candidate_resolution_ambiguity_digest.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "psycopg",
        "postgres",
        "supabase",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "wallet",
        "account",
        "auth",
        "order",
        "signing",
        "cancel",
        "replace",
        "exchange",
        "broker",
        "trade",
        "private_key",
        "private-key",
        "open(",
        "os.environ",
        "argparse",
        "click",
        "typer",
    )

    assert all(term not in source for term in forbidden_terms)


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
