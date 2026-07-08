from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_domain_team_consensus_report import (
    ResearchStrategyDomainTeamConsensusConfig,
    ResearchStrategyDomainTeamConsensusInput,
    ResearchStrategyDomainTeamConsensusReasonCodeCount,
    ResearchStrategyDomainTeamConsensusReport,
    ResearchStrategyDomainTeamConsensusRow,
    build_research_strategy_domain_team_consensus_report,
    research_strategy_domain_team_consensus_report_digest,
    research_strategy_domain_team_consensus_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyDomainTeamConsensusConfig:
    values = {
        "config_version": "research-strategy-domain-team-consensus-report-v0",
        "pass_dimension_score": d("0.700000"),
        "watch_dimension_score": d("0.400000"),
        "pass_consensus_quality_score": d("0.750000"),
        "watch_consensus_quality_score": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategyDomainTeamConsensusConfig(**values)


def input_row(
    domain_team_label: str,
    *,
    specialist_agreement: Decimal = d("0.910000"),
    memory_freshness: Decimal = d("0.860000"),
    evidence_coverage: Decimal = d("0.890000"),
    unresolved_dissent: Decimal = d("0.080000"),
    escalation_urgency: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyDomainTeamConsensusInput:
    return ResearchStrategyDomainTeamConsensusInput(
        domain_team_label=domain_team_label,
        specialist_agreement=specialist_agreement,
        memory_freshness=memory_freshness,
        evidence_coverage=evidence_coverage,
        unresolved_dissent=unresolved_dissent,
        escalation_urgency=escalation_urgency,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyDomainTeamConsensusConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyDomainTeamConsensusReport:
    return build_research_strategy_domain_team_consensus_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_for_manual_review() -> None:
    consensus_report = report(())

    assert type(consensus_report) is ResearchStrategyDomainTeamConsensusReport
    assert consensus_report.generated_at == GENERATED_AT
    assert consensus_report.config_version == (
        "research-strategy-domain-team-consensus-report-v0"
    )
    assert consensus_report.team_count == d("0")
    assert consensus_report.pass_count == d("0")
    assert consensus_report.watch_count == d("0")
    assert consensus_report.block_count == d("0")
    assert consensus_report.average_consensus_quality_score is None
    assert consensus_report.min_specialist_agreement is None
    assert consensus_report.min_memory_freshness is None
    assert consensus_report.min_evidence_coverage is None
    assert consensus_report.max_unresolved_dissent is None
    assert consensus_report.max_escalation_urgency is None
    assert consensus_report.status == "block"
    assert consensus_report.reason_codes == ("no_domain_team_consensus_inputs",)
    assert consensus_report.reason_code_counts == (
        ResearchStrategyDomainTeamConsensusReasonCodeCount(
            reason_code="no_domain_team_consensus_inputs",
            count=d("1"),
        ),
    )
    assert consensus_report.rows == ()
    assert len(consensus_report.derived_validation_digest) == 64
    assert consensus_report.paper_only is True
    assert consensus_report.report_only is True
    assert consensus_report.readonly is True


def test_public_safe_inputs_pass_with_aggregate_consensus_quality() -> None:
    consensus_report = report(
        (
            input_row(
                "domain-team-alpha",
                reason_codes=("manual_consensus_review",),
            ),
        ),
    )

    row = consensus_report.rows[0]
    assert type(row) is ResearchStrategyDomainTeamConsensusRow
    assert consensus_report.status == "pass"
    assert consensus_report.team_count == d("1")
    assert consensus_report.pass_count == d("1")
    assert consensus_report.watch_count == d("0")
    assert consensus_report.block_count == d("0")
    assert consensus_report.average_consensus_quality_score == d("0.906000")
    assert consensus_report.min_specialist_agreement == d("0.910000")
    assert consensus_report.min_memory_freshness == d("0.860000")
    assert consensus_report.min_evidence_coverage == d("0.890000")
    assert consensus_report.max_unresolved_dissent == d("0.080000")
    assert consensus_report.max_escalation_urgency == d("0.050000")
    assert consensus_report.reason_codes == ("domain_team_consensus_quality_pass",)
    assert row.domain_team_label == "domain-team-alpha"
    assert row.specialist_agreement_score == d("0.910000")
    assert row.memory_freshness_score == d("0.860000")
    assert row.evidence_coverage_score == d("0.890000")
    assert row.dissent_resolution_score == d("0.920000")
    assert row.escalation_stability_score == d("0.950000")
    assert row.consensus_quality_score == d("0.906000")
    assert row.lowest_dimension_score == d("0.860000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "domain_team_consensus_quality_pass",
        "evidence_coverage_pass",
        "escalation_urgency_pass",
        "input_manual_consensus_review",
        "memory_freshness_pass",
        "report_only_domain_team_consensus_pass",
        "specialist_agreement_pass",
        "unresolved_dissent_pass",
    )


def test_watch_and_block_statuses_reflect_consensus_quality_dimensions() -> None:
    consensus_report = report(
        (
            input_row(
                "domain-team-watch",
                specialist_agreement=d("0.750000"),
                memory_freshness=d("0.620000"),
                evidence_coverage=d("0.680000"),
                unresolved_dissent=d("0.200000"),
                escalation_urgency=d("0.250000"),
            ),
            input_row(
                "domain-team-block",
                specialist_agreement=d("0.390000"),
                memory_freshness=d("0.360000"),
                evidence_coverage=d("0.500000"),
                unresolved_dissent=d("0.620000"),
                escalation_urgency=d("0.550000"),
                reason_codes=("dissent_review_needed",),
            ),
        ),
    )

    block_row, watch_row = consensus_report.rows
    assert consensus_report.status == "block"
    assert consensus_report.pass_count == d("0")
    assert consensus_report.watch_count == d("1")
    assert consensus_report.block_count == d("1")
    assert consensus_report.average_consensus_quality_score == d("0.568000")
    assert consensus_report.min_specialist_agreement == d("0.390000")
    assert consensus_report.min_memory_freshness == d("0.360000")
    assert consensus_report.min_evidence_coverage == d("0.500000")
    assert consensus_report.max_unresolved_dissent == d("0.620000")
    assert consensus_report.max_escalation_urgency == d("0.550000")
    assert block_row.domain_team_label == "domain-team-block"
    assert block_row.consensus_quality_score == d("0.416000")
    assert block_row.lowest_dimension_score == d("0.360000")
    assert block_row.status == "block"
    assert "specialist_agreement_block" in block_row.reason_codes
    assert "memory_freshness_block" in block_row.reason_codes
    assert "unresolved_dissent_block" in block_row.reason_codes
    assert "input_dissent_review_needed" in block_row.reason_codes
    assert watch_row.domain_team_label == "domain-team-watch"
    assert watch_row.consensus_quality_score == d("0.720000")
    assert watch_row.lowest_dimension_score == d("0.620000")
    assert watch_row.status == "watch"
    assert "memory_freshness_watch" in watch_row.reason_codes
    assert "evidence_coverage_watch" in watch_row.reason_codes


def test_payload_digest_are_deterministic_and_digest_validates() -> None:
    first_report = report(
        (
            input_row("z-domain-team", reason_codes=("zeta", "alpha")),
            input_row("a-domain-team"),
        ),
    )
    second_report = report(
        (
            input_row("a-domain-team"),
            input_row("z-domain-team", reason_codes=("alpha", "zeta")),
        ),
    )

    first_payload = research_strategy_domain_team_consensus_report_payload(first_report)
    second_payload = research_strategy_domain_team_consensus_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert tuple(row.domain_team_label for row in first_report.rows) == (
        "a-domain-team",
        "z-domain-team",
    )
    assert first_payload == second_payload
    assert research_strategy_domain_team_consensus_report_digest(first_report) == (
        first_report.derived_validation_digest
    )
    assert research_strategy_domain_team_consensus_report_digest(first_report) == (
        research_strategy_domain_team_consensus_report_digest(second_report)
    )
    assert len(research_strategy_domain_team_consensus_report_digest(first_report)) == 64
    assert first_payload["rows"][0]["consensus_quality_score"] == "0.906000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.9" not in encoded
    assert not any(_has_forbidden_identifier_key(key) for key in _walk_payload_keys(first_payload))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first_report, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_values_bad_flags_and_raw_labels() -> None:
    with pytest.raises(ValueError, match="pass_dimension_score"):
        config(pass_dimension_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_consensus_quality_score"):
        config(watch_consensus_quality_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="pass_consensus_quality_score"):
        config(pass_consensus_quality_score=d("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((input_row("domain-team-alpha"),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (input_row("domain-team-alpha"),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="domain_team_label"):
        input_row(" domain-team-alpha")
    with pytest.raises(ValueError, match="domain_team_label"):
        input_row("raw-market-alpha")
    with pytest.raises(ValueError, match="specialist_agreement"):
        input_row("domain-team-alpha", specialist_agreement=0.91)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_freshness"):
        input_row("domain-team-alpha", memory_freshness=d("1.1"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row("domain-team-alpha", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row("domain-team-alpha"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    consensus_report = report((input_row("domain-team-alpha"),))

    with pytest.raises(FrozenInstanceError):
        consensus_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        consensus_report.rows[0].consensus_quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="consensus_quality_score"):
        replace(consensus_report.rows[0], consensus_quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(consensus_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="status"):
        replace(consensus_report, status="watch")


def test_owned_module_has_no_execution_or_recommendation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_domain_team_consensus_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "buy",
        "sell",
        "recommend",
        "position sizing",
        "database",
    )

    assert all(term not in text for term in forbidden_terms)


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


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_identifier_key(key: str) -> bool:
    return key in {
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_id",
        "source_url",
        "source_reference",
        "raw_identifier",
    }
