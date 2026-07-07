from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_risk_concentration_report import (
    DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION,
    ResearchRiskConcentrationCandidate,
    ResearchRiskConcentrationConfig,
    ResearchRiskConcentrationDimension,
    ResearchRiskConcentrationReport,
    build_research_risk_concentration_report,
    research_risk_concentration_report_payload,
    validate_research_risk_concentration_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def candidate(
    candidate_id: str,
    *,
    domain_key: str = "macro",
    source_family: str = "official_family",
    rule_family: str = "resolution_rule",
    timeline_bucket: str = "seven_day_plus",
    risk_weight: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchRiskConcentrationCandidate:
    return ResearchRiskConcentrationCandidate(
        candidate_id=candidate_id,
        domain_key=domain_key,
        source_family=source_family,
        rule_family=rule_family,
        timeline_bucket=timeline_bucket,
        risk_weight=risk_weight,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *items: ResearchRiskConcentrationCandidate,
    config: ResearchRiskConcentrationConfig | None = None,
) -> ResearchRiskConcentrationReport:
    return build_research_risk_concentration_report(
        items,
        config=config or ResearchRiskConcentrationConfig(),
        generated_at=GENERATED_AT,
    )


def test_pass_report_balances_domain_source_rule_and_timeline_concentration() -> None:
    report = build_report(
        candidate(
            "raw-candidate-alpha",
            domain_key="macro",
            source_family="official_family",
            rule_family="resolution_rule",
            timeline_bucket="seven_day_plus",
        ),
        candidate(
            "raw-candidate-beta",
            domain_key="sports",
            source_family="expert_family",
            rule_family="volume_rule",
            timeline_bucket="three_to_seven_days",
        ),
        candidate(
            "raw-candidate-gamma",
            domain_key="crypto",
            source_family="aggregator_family",
            rule_family="dispute_rule",
            timeline_bucket="one_to_three_days",
        ),
        candidate(
            "raw-candidate-delta",
            domain_key="politics",
            source_family="calendar_family",
            rule_family="settlement_rule",
            timeline_bucket="same_day",
        ),
    )

    assert report.config_version == DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION
    assert report.report_status == "pass"
    assert report.item_count == d("4.000000")
    assert report.pass_dimension_count == d("4.000000")
    assert report.watch_dimension_count == d("0.000000")
    assert report.block_dimension_count == d("0.000000")
    assert report.max_concentration_ratio == d("0.250000")
    assert report.reason_codes == ("research_risk_concentration_passed",)
    assert tuple(row.dimension for row in report.dimensions) == (
        "domain",
        "source",
        "rule",
        "timeline",
    )
    assert all(row.dimension_status == "pass" for row in report.dimensions)
    assert all(row.top_group_item_ratio == d("0.250000") for row in report.dimensions)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = research_risk_concentration_report_payload(report)
    assert payload["item_count"] == "4.000000"
    assert payload["max_concentration_ratio"] == "0.250000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert validate_research_risk_concentration_public_payload(payload)
    json.dumps(payload, sort_keys=True)

    serialized = json.dumps(payload, sort_keys=True).lower()
    assert "raw-candidate-alpha" not in serialized
    assert "raw-candidate-beta" not in serialized


def test_watch_report_flags_moderate_domain_concentration() -> None:
    report = build_report(
        candidate(
            "raw-a",
            domain_key="macro",
            source_family="official_family",
            rule_family="resolution_rule",
            timeline_bucket="same_day",
        ),
        candidate(
            "raw-b",
            domain_key="macro",
            source_family="expert_family",
            rule_family="volume_rule",
            timeline_bucket="one_to_three_days",
        ),
        candidate(
            "raw-c",
            domain_key="sports",
            source_family="aggregator_family",
            rule_family="dispute_rule",
            timeline_bucket="seven_day_plus",
        ),
    )

    assert report.report_status == "watch"
    assert report.pass_dimension_count == d("3.000000")
    assert report.watch_dimension_count == d("1.000000")
    assert report.block_dimension_count == d("0.000000")
    assert report.max_concentration_ratio == d("0.666667")
    assert report.reason_codes == ("research_risk_concentration_domain_watch",)
    domain = report.dimensions[0]
    assert domain == ResearchRiskConcentrationDimension(
        dimension="domain",
        top_group_label="macro",
        top_group_item_count=d("2.000000"),
        top_group_item_ratio=d("0.666667"),
        top_group_risk_weight=d("2.000000"),
        top_group_risk_weight_ratio=d("0.666667"),
        dimension_status="watch",
        reason_codes=("research_risk_concentration_domain_watch",),
        derived_validation_digest=domain.derived_validation_digest,
    )


def test_block_report_flags_high_source_rule_and_timeline_concentration() -> None:
    report = build_report(
        candidate(
            "raw-a",
            domain_key="macro",
            source_family="official_family",
            rule_family="resolution_rule",
            timeline_bucket="same_day",
        ),
        candidate(
            "raw-b",
            domain_key="sports",
            source_family="official_family",
            rule_family="resolution_rule",
            timeline_bucket="same_day",
        ),
        candidate(
            "raw-c",
            domain_key="crypto",
            source_family="official_family",
            rule_family="resolution_rule",
            timeline_bucket="same_day",
        ),
        candidate(
            "raw-d",
            domain_key="politics",
            source_family="expert_family",
            rule_family="volume_rule",
            timeline_bucket="seven_day_plus",
        ),
    )

    assert report.report_status == "block"
    assert report.pass_dimension_count == d("1.000000")
    assert report.watch_dimension_count == d("0.000000")
    assert report.block_dimension_count == d("3.000000")
    assert report.max_concentration_ratio == d("0.750000")
    assert report.reason_codes == (
        "research_risk_concentration_source_block",
        "research_risk_concentration_rule_block",
        "research_risk_concentration_timeline_block",
    )
    assert tuple((row.dimension, row.dimension_status) for row in report.dimensions) == (
        ("domain", "pass"),
        ("source", "block"),
        ("rule", "block"),
        ("timeline", "block"),
    )


def test_decimal_only_exact_type_validation_and_frozen_dataclasses() -> None:
    with pytest.raises(ValueError, match="domain_watch_ratio"):
        ResearchRiskConcentrationConfig(domain_watch_ratio=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_block_ratio"):
        ResearchRiskConcentrationConfig(source_block_ratio=_DecimalSubclass("0.75"))
    with pytest.raises(ValueError, match="risk_weight"):
        candidate("raw-a", risk_weight=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="risk_weight"):
        candidate("raw-a", risk_weight=d("0.000000"))

    report = build_report(candidate("raw-a"), candidate("raw-b", domain_key="sports"))
    with pytest.raises(FrozenInstanceError):
        report.report_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.dimensions[0].top_group_item_ratio = d("1.000000")  # type: ignore[misc]


def test_rejects_public_payload_leaks_and_unsafe_research_surfaces() -> None:
    report = build_report(candidate("raw-candidate-secret"))
    payload = research_risk_concentration_report_payload(report)
    serialized = json.dumps(payload, sort_keys=True).lower()

    forbidden_public_terms = (
        "raw-candidate-secret",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommendation",
        _unsafe("b", "uy"),
        _unsafe("s", "ell"),
    )
    for term in forbidden_public_terms:
        assert term not in serialized

    unsafe_cases = (
        {"market_id": "pm-123"},
        {"market_slug": "event-slug"},
        {"question": "Will this resolve?"},
        {"source_ref": "ref-1"},
        {"source_url": "https://example.test/detail"},
        {"source_text": "quoted source details"},
        {"dsn": "postgres://example"},
        {"table_name": "research_queue"},
        {"note": "api token is present"},
        {"note": "wallet review"},
        {"note": "auth required"},
        {"note": "order ticket"},
        {"note": "trade review"},
        {"note": "position sizing"},
        {"note": "buy this"},
        {"note": "sell this"},
        {"note": "recommendation ready"},
    )
    for unsafe in unsafe_cases:
        tampered = dict(payload)
        tampered.update(unsafe)
        with pytest.raises(ValueError, match="unsafe|public"):
            research_risk_concentration_report_payload(tampered)

    with pytest.raises(ValueError, match="source_family"):
        candidate(
            "raw-a",
            source_family="https://example.test/source",
        )


def test_hard_flags_are_required_on_inputs_reports_dimensions_and_payloads() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchRiskConcentrationConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate("raw-a", report_only=False)

    report = build_report(candidate("raw-a"), candidate("raw-b", domain_key="sports"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.dimensions)

    with pytest.raises(ValueError, match="readonly"):
        replace(report.dimensions[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    payload = research_risk_concentration_report_payload(report)
    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_risk_concentration_report_payload(downgraded)


def test_output_is_deterministic_for_input_order_and_payload_round_trip() -> None:
    items = (
        candidate(
            "raw-a",
            domain_key="macro",
            source_family="official_family",
            rule_family="resolution_rule",
            timeline_bucket="same_day",
            risk_weight=d("2.000000"),
        ),
        candidate(
            "raw-b",
            domain_key="sports",
            source_family="expert_family",
            rule_family="volume_rule",
            timeline_bucket="seven_day_plus",
            risk_weight=d("1.000000"),
        ),
        candidate(
            "raw-c",
            domain_key="sports",
            source_family="aggregator_family",
            rule_family="dispute_rule",
            timeline_bucket="one_to_three_days",
            risk_weight=d("1.000000"),
        ),
    )
    first = build_report(*items)
    second = build_report(*reversed(items))

    first_payload = research_risk_concentration_report_payload(first)
    second_payload = research_risk_concentration_report_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert research_risk_concentration_report_payload(first_payload) == first_payload
    assert first.derived_validation_digest == second.derived_validation_digest
