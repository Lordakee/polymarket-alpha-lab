from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_resolution_rule_source_alignment_report import (
    DEFAULT_RESEARCH_RESOLUTION_RULE_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION,
    ResearchResolutionRuleSourceAlignmentAggregate,
    ResearchResolutionRuleSourceAlignmentConfig,
    ResearchResolutionRuleSourceAlignmentReport,
    ResearchResolutionRuleSourceAlignmentRow,
    build_research_resolution_rule_source_alignment_report,
    research_resolution_rule_source_alignment_report_payload,
    validate_research_resolution_rule_source_alignment_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_resolution_rule_source_alignment_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionRuleSourceAlignmentConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_RESOLUTION_RULE_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
        ),
        "min_rule_citation_completeness_ratio": d("1.000000"),
        "block_rule_citation_completeness_ratio": d("0.500000"),
        "min_official_source_agreement_ratio": d("0.800000"),
        "block_official_source_agreement_ratio": d("0.500000"),
        "watch_ambiguity_pressure_ratio": d("0.250000"),
        "block_ambiguity_pressure_ratio": d("0.600000"),
        "watch_stale_rule_memory_ratio": d("0.250000"),
        "block_stale_rule_memory_ratio": d("0.500000"),
        "watch_recheck_urgency_ratio": d("0.250000"),
        "block_recheck_urgency_ratio": d("0.600000"),
    }
    values.update(overrides)
    return ResearchResolutionRuleSourceAlignmentConfig(**values)


def alignment_group(
    name: str,
    *,
    rules: str,
    cited: str,
    evidence: str,
    official_agreement: str,
    ambiguous: str = "0.000000",
    stale_memory: str = "0.000000",
    pending_recheck: str = "0.000000",
) -> ResearchResolutionRuleSourceAlignmentAggregate:
    return ResearchResolutionRuleSourceAlignmentAggregate(
        rule_group=name,
        rule_count=d(rules),
        cited_rule_count=d(cited),
        evidence_source_count=d(evidence),
        official_source_agreement_count=d(official_agreement),
        ambiguous_rule_count=d(ambiguous),
        stale_rule_memory_count=d(stale_memory),
        pending_recheck_count=d(pending_recheck),
    )


def report(
    rows: tuple[ResearchResolutionRuleSourceAlignmentAggregate, ...],
    *,
    cfg: ResearchResolutionRuleSourceAlignmentConfig | None = None,
) -> ResearchResolutionRuleSourceAlignmentReport:
    return build_research_resolution_rule_source_alignment_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_with_zero_aggregate_pressure_and_hard_flags() -> None:
    alignment_report = report(())

    assert type(alignment_report) is ResearchResolutionRuleSourceAlignmentReport
    assert is_dataclass(alignment_report)
    assert alignment_report.__dataclass_params__.frozen is True
    assert alignment_report.generated_at == GENERATED_AT
    assert alignment_report.config_version == (
        DEFAULT_RESEARCH_RESOLUTION_RULE_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    assert alignment_report.rule_group_count == ZERO
    assert alignment_report.rule_count == ZERO
    assert alignment_report.cited_rule_count == ZERO
    assert alignment_report.evidence_source_count == ZERO
    assert alignment_report.official_source_agreement_count == ZERO
    assert alignment_report.ambiguous_rule_count == ZERO
    assert alignment_report.stale_rule_memory_count == ZERO
    assert alignment_report.pending_recheck_count == ZERO
    assert alignment_report.pass_count == ZERO
    assert alignment_report.watch_count == ZERO
    assert alignment_report.block_count == ZERO
    assert alignment_report.rule_citation_completeness_ratio == ZERO
    assert alignment_report.official_source_agreement_ratio == ZERO
    assert alignment_report.ambiguity_pressure_ratio == ZERO
    assert alignment_report.stale_rule_memory_ratio == ZERO
    assert alignment_report.recheck_urgency_ratio == ZERO
    assert alignment_report.status == "block"
    assert alignment_report.reason_codes == ("no_rule_source_alignment_groups",)
    assert alignment_report.rows == ()
    assert alignment_report.paper_only is True
    assert alignment_report.report_only is True
    assert alignment_report.readonly is True
    assert len(alignment_report.derived_validation_digest) == 64


def test_complete_rule_citations_and_official_source_agreement_pass_deterministically() -> None:
    alignment_report = report(
        (
            alignment_group(
                "primary-rulebook",
                rules="4.000000",
                cited="4.000000",
                evidence="4.000000",
                official_agreement="4.000000",
            ),
            alignment_group(
                "settlement-notes",
                rules="2.000000",
                cited="2.000000",
                evidence="2.000000",
                official_agreement="2.000000",
            ),
        ),
    )

    payload = research_resolution_rule_source_alignment_report_payload(alignment_report)
    repeat_payload = research_resolution_rule_source_alignment_report_payload(
        alignment_report,
    )

    assert alignment_report.status == "pass"
    assert alignment_report.rule_group_count == d("2.000000")
    assert alignment_report.rule_count == d("6.000000")
    assert alignment_report.cited_rule_count == d("6.000000")
    assert alignment_report.evidence_source_count == d("6.000000")
    assert alignment_report.official_source_agreement_count == d("6.000000")
    assert alignment_report.pass_count == d("2.000000")
    assert alignment_report.watch_count == ZERO
    assert alignment_report.block_count == ZERO
    assert alignment_report.rule_citation_completeness_ratio == ONE
    assert alignment_report.official_source_agreement_ratio == ONE
    assert alignment_report.reason_codes == ("rule_source_alignment_pass",)
    assert tuple(row.rule_group for row in alignment_report.rows) == (
        "primary-rulebook",
        "settlement-notes",
    )
    assert all(type(row) is ResearchResolutionRuleSourceAlignmentRow for row in alignment_report.rows)
    assert all(row.status == "pass" for row in alignment_report.rows)
    assert payload == repeat_payload
    assert payload["derived_validation_digest"] == (
        alignment_report.derived_validation_digest
    )
    assert payload["rows"][0]["rule_citation_completeness_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _has_forbidden_public_key(payload)
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert validate_research_resolution_rule_source_alignment_report_payload(payload)


def test_citation_agreement_ambiguity_memory_and_recheck_pressure_roll_up() -> None:
    alignment_report = report(
        (
            alignment_group(
                "event-rules",
                rules="4.000000",
                cited="3.000000",
                evidence="4.000000",
                official_agreement="3.000000",
                ambiguous="1.000000",
                stale_memory="1.000000",
                pending_recheck="1.000000",
            ),
            alignment_group(
                "settlement-rules",
                rules="5.000000",
                cited="2.000000",
                evidence="5.000000",
                official_agreement="2.000000",
                ambiguous="4.000000",
                stale_memory="3.000000",
                pending_recheck="4.000000",
            ),
        ),
    )

    assert alignment_report.status == "block"
    assert alignment_report.rule_group_count == d("2.000000")
    assert alignment_report.rule_count == d("9.000000")
    assert alignment_report.cited_rule_count == d("5.000000")
    assert alignment_report.evidence_source_count == d("9.000000")
    assert alignment_report.official_source_agreement_count == d("5.000000")
    assert alignment_report.ambiguous_rule_count == d("5.000000")
    assert alignment_report.stale_rule_memory_count == d("4.000000")
    assert alignment_report.pending_recheck_count == d("5.000000")
    assert alignment_report.pass_count == ZERO
    assert alignment_report.watch_count == ONE
    assert alignment_report.block_count == ONE
    assert alignment_report.rule_citation_completeness_ratio == d("0.555556")
    assert alignment_report.official_source_agreement_ratio == d("0.555556")
    assert alignment_report.ambiguity_pressure_ratio == d("0.555556")
    assert alignment_report.stale_rule_memory_ratio == d("0.444444")
    assert alignment_report.recheck_urgency_ratio == d("0.555556")
    assert alignment_report.reason_codes == (
        "rule_citation_completeness_watch",
        "official_source_agreement_watch",
        "ambiguity_pressure_watch",
        "stale_rule_memory_watch",
        "recheck_urgency_watch",
        "rule_source_alignment_group_block",
    )

    event_rules, settlement_rules = alignment_report.rows
    assert (event_rules.rule_group, event_rules.status) == ("event-rules", "watch")
    assert (settlement_rules.rule_group, settlement_rules.status) == (
        "settlement-rules",
        "block",
    )
    assert event_rules.reason_codes == (
        "rule_citation_completeness_watch",
        "official_source_agreement_watch",
        "ambiguity_pressure_watch",
        "stale_rule_memory_watch",
        "recheck_urgency_watch",
    )
    assert settlement_rules.reason_codes == (
        "rule_citation_completeness_block",
        "official_source_agreement_block",
        "ambiguity_pressure_block",
        "stale_rule_memory_block",
        "recheck_urgency_block",
    )


def test_validation_rejects_bad_numerics_inconsistent_counts_flags_and_payloads() -> None:
    with pytest.raises(ValueError, match="min_rule_citation_completeness_ratio"):
        config(min_rule_citation_completeness_ratio=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_ambiguity_pressure_ratio"):
        config(watch_ambiguity_pressure_ratio=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="block_rule_citation_completeness_ratio"):
        config(block_rule_citation_completeness_ratio=d("1.000000"))
    with pytest.raises(ValueError, match="rule_group"):
        alignment_group(
            "market-slug-leak",
            rules="1.000000",
            cited="1.000000",
            evidence="1.000000",
            official_agreement="1.000000",
        )
    with pytest.raises(ValueError, match="rule_count"):
        alignment_group(
            "official",
            rules="0.000000",
            cited="0.000000",
            evidence="0.000000",
            official_agreement="0.000000",
        )
    with pytest.raises(ValueError, match="cited_rule_count"):
        alignment_group(
            "official",
            rules="1.000000",
            cited="2.000000",
            evidence="2.000000",
            official_agreement="1.000000",
        )
    with pytest.raises(ValueError, match="official_source_agreement_count"):
        alignment_group(
            "official",
            rules="1.000000",
            cited="1.000000",
            evidence="1.000000",
            official_agreement="2.000000",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            alignment_group(
                "official",
                rules="1.000000",
                cited="1.000000",
                evidence="1.000000",
                official_agreement="1.000000",
            ),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        validate_research_resolution_rule_source_alignment_report_payload(
            {
                "raw_" + "url": "blocked",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_public_dataclasses_are_frozen_exact_and_source_has_no_unsafe_surfaces() -> None:
    alignment_report = report(
        (
            alignment_group(
                "official",
                rules="1.000000",
                cited="1.000000",
                evidence="1.000000",
                official_agreement="1.000000",
            ),
        ),
    )

    public_classes = (
        ResearchResolutionRuleSourceAlignmentConfig,
        ResearchResolutionRuleSourceAlignmentAggregate,
        ResearchResolutionRuleSourceAlignmentRow,
        ResearchResolutionRuleSourceAlignmentReport,
    )
    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if field.name.endswith("_count") or field.name.endswith("_ratio"):
                assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        alignment_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        alignment_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(alignment_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="pass_count"):
        replace(alignment_report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(alignment_report, derived_validation_digest="0" * 64)

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "raw_" + "url",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "ques" + "tion",
        "database",
        "network",
        "wallet",
        "order",
        "live",
        "trade",
        "trading",
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


def _has_forbidden_public_key(value: object) -> bool:
    forbidden = (
        "raw_" + "url",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "ques" + "tion",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in forbidden):
                return True
            if _has_forbidden_public_key(item):
                return True
    if isinstance(value, list):
        return any(_has_forbidden_public_key(item) for item in value)
    return False
