from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_dispute_history_report import (
    ResearchResolutionDisputeHistoryConfig,
    ResearchResolutionDisputeHistoryIncident,
    ResearchResolutionDisputeHistoryReport,
    ResearchResolutionDisputeHistoryRow,
    build_research_resolution_dispute_history_report,
    research_resolution_dispute_history_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def incident(
    index: int,
    *,
    condition_id: str | None = None,
    incident_id: str | None = None,
    observed_at: datetime = GENERATED_AT,
    settlement_count: Decimal = d("20"),
    dispute_count: Decimal = d("1"),
    ambiguous_rule_count: Decimal = d("0"),
    evidence_family_count: Decimal = d("4"),
    independent_evidence_family_count: Decimal = d("4"),
    official_evidence_count: Decimal = d("1"),
    retrospective_outcome: str = "clean",
) -> ResearchResolutionDisputeHistoryIncident:
    return ResearchResolutionDisputeHistoryIncident(
        condition_id=condition_id or f"condition-{index:03d}",
        incident_id=incident_id or f"incident-{index:03d}",
        observed_at=observed_at,
        settlement_count=settlement_count,
        dispute_count=dispute_count,
        ambiguous_rule_count=ambiguous_rule_count,
        evidence_family_count=evidence_family_count,
        independent_evidence_family_count=independent_evidence_family_count,
        official_evidence_count=official_evidence_count,
        retrospective_outcome=retrospective_outcome,
    )


def report(
    items: tuple[ResearchResolutionDisputeHistoryIncident, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config: ResearchResolutionDisputeHistoryConfig | None = None,
) -> ResearchResolutionDisputeHistoryReport:
    return build_research_resolution_dispute_history_report(
        items,
        generated_at=generated_at,
        config=config,
    )


def test_empty_input_returns_block_report_without_rows() -> None:
    dispute_report = report(())

    assert type(dispute_report) is ResearchResolutionDisputeHistoryReport
    assert dispute_report.generated_at == GENERATED_AT
    assert dispute_report.incident_count == d("0")
    assert dispute_report.pass_count == d("0")
    assert dispute_report.watch_count == d("0")
    assert dispute_report.block_count == d("0")
    assert dispute_report.high_risk_layer_count == d("0")
    assert dispute_report.average_dispute_frequency == d("0.000000")
    assert dispute_report.average_rule_ambiguity_ratio == d("0.000000")
    assert dispute_report.average_evidence_dependency_score == d("0.000000")
    assert dispute_report.average_retrospective_risk_score == d("0.000000")
    assert dispute_report.average_risk_score == d("0.000000")
    assert dispute_report.status == "block"
    assert dispute_report.reason_codes == ("no_disputes_to_assess",)
    assert dispute_report.rows == ()
    assert dispute_report.paper_only is True
    assert dispute_report.report_only is True
    assert dispute_report.readonly is True


def test_clean_low_frequency_history_passes() -> None:
    dispute_report = report((incident(1),))

    assert dispute_report.status == "pass"
    assert dispute_report.pass_count == d("1")
    assert dispute_report.watch_count == d("0")
    assert dispute_report.block_count == d("0")
    assert dispute_report.average_dispute_frequency == d("0.050000")
    assert dispute_report.average_rule_ambiguity_ratio == d("0.000000")
    assert dispute_report.average_evidence_dependency_score == d("0.000000")
    assert dispute_report.average_retrospective_risk_score == d("0.000000")
    assert dispute_report.average_risk_score == d("0.015000")
    assert dispute_report.reason_codes == ("resolution_dispute_history_pass",)

    row = dispute_report.rows[0]
    assert type(row) is ResearchResolutionDisputeHistoryRow
    assert row.dispute_frequency == d("0.050000")
    assert row.rule_ambiguity_ratio == d("0.000000")
    assert row.evidence_dependency_score == d("0.000000")
    assert row.retrospective_outcome == "clean"
    assert row.retrospective_risk_score == d("0.000000")
    assert row.risk_score == d("0.015000")
    assert row.risk_layer == "low"
    assert row.status == "pass"
    assert row.reason_codes == (
        "dispute_frequency_low",
        "retrospective_clean",
        "risk_layer_low",
        "resolution_dispute_history_pass",
    )


def test_rule_ambiguity_and_dependency_history_is_watch() -> None:
    dispute_report = report(
        (
            incident(
                1,
                settlement_count=d("20"),
                dispute_count=d("4"),
                ambiguous_rule_count=d("1"),
                evidence_family_count=d("4"),
                independent_evidence_family_count=d("2"),
                official_evidence_count=d("1"),
                retrospective_outcome="contained",
            ),
        ),
    )

    row = dispute_report.rows[0]
    assert dispute_report.status == "watch"
    assert dispute_report.watch_count == d("1")
    assert dispute_report.average_dispute_frequency == d("0.200000")
    assert dispute_report.average_rule_ambiguity_ratio == d("0.250000")
    assert dispute_report.average_evidence_dependency_score == d("0.250000")
    assert dispute_report.average_retrospective_risk_score == d("0.250000")
    assert dispute_report.average_risk_score == d("0.235000")
    assert row.status == "watch"
    assert row.risk_layer == "low"
    assert row.reason_codes == (
        "dispute_frequency_watch",
        "rule_ambiguity_present",
        "retrospective_contained",
        "risk_layer_low",
        "resolution_dispute_history_watch",
    )


def test_high_frequency_severe_ambiguity_and_single_family_dependency_blocks() -> None:
    dispute_report = report(
        (
            incident(
                1,
                settlement_count=d("10"),
                dispute_count=d("4"),
                ambiguous_rule_count=d("3"),
                evidence_family_count=d("1"),
                independent_evidence_family_count=d("0"),
                official_evidence_count=d("0"),
                retrospective_outcome="reversed",
            ),
        ),
    )

    row = dispute_report.rows[0]
    assert dispute_report.status == "block"
    assert dispute_report.block_count == d("1")
    assert dispute_report.high_risk_layer_count == d("1")
    assert dispute_report.average_dispute_frequency == d("0.400000")
    assert dispute_report.average_rule_ambiguity_ratio == d("0.750000")
    assert dispute_report.average_evidence_dependency_score == d("1.000000")
    assert dispute_report.average_retrospective_risk_score == d("1.000000")
    assert dispute_report.average_risk_score == d("0.757500")
    assert row.status == "block"
    assert row.risk_layer == "high"
    assert row.reason_codes == (
        "dispute_frequency_block",
        "rule_ambiguity_severe",
        "evidence_dependency_block",
        "retrospective_reversed",
        "risk_layer_high",
        "resolution_dispute_history_block",
    )


def test_rows_are_sorted_counts_are_deterministic_and_payload_uses_no_float_values() -> None:
    dispute_report = report(
        (
            incident(2, condition_id="z-condition", incident_id="z-incident"),
            incident(
                1,
                condition_id="a-condition",
                incident_id="a-incident",
                settlement_count=d("20"),
                dispute_count=d("4"),
                ambiguous_rule_count=d("1"),
                evidence_family_count=d("4"),
                independent_evidence_family_count=d("2"),
                official_evidence_count=d("1"),
                retrospective_outcome="contained",
            ),
        ),
    )
    payload = research_resolution_dispute_history_report_payload(dispute_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.condition_id for row in dispute_report.rows) == (
        "a-condition",
        "z-condition",
    )
    assert dispute_report.status == "watch"
    assert dispute_report.pass_count == d("1")
    assert dispute_report.watch_count == d("1")
    assert dispute_report.block_count == d("0")
    assert dispute_report.average_risk_score == d("0.125000")
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["risk_score"] == "0.235000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_public_payload_omits_raw_locator_material_and_rejects_unsafe_identifiers() -> None:
    dispute_report = report((incident(1),))
    payload = research_resolution_dispute_history_report_payload(dispute_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    for unsafe_fragment in (
        "raw",
        "market",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "https://",
    ):
        assert unsafe_fragment not in encoded
    with pytest.raises(ValueError, match="unsafe public value"):
        incident(2, condition_id="market-123")
    with pytest.raises(ValueError, match="unsafe public value"):
        incident(3, incident_id="https://private.example/path?token=abc")
    with pytest.raises(ValueError, match="unsafe public field"):
        research_resolution_dispute_history_report_payload(
            {
                "raw_market_question": "private",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_bad_types_enums_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_dispute_frequency"):
        ResearchResolutionDisputeHistoryConfig(
            watch_dispute_frequency=d("0.300000"),
            block_dispute_frequency=d("0.300000"),
        )
    with pytest.raises(ValueError, match="pass_risk_score_ceiling"):
        ResearchResolutionDisputeHistoryConfig(pass_risk_score_ceiling=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="retrospective_weight"):
        ResearchResolutionDisputeHistoryConfig(retrospective_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((incident(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((incident(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="incidents"):
        build_research_resolution_dispute_history_report(
            "not-a-list",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="incidents"):
        report(("not-an-incident",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        report((incident(1), incident(1)))
    with pytest.raises(ValueError, match="observed_at"):
        incident(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        incident(1, observed_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="settlement_count"):
        incident(1, settlement_count=20)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_count"):
        incident(1, settlement_count=_DecimalSubclass("20"))
    with pytest.raises(ValueError, match="dispute_count"):
        incident(1, settlement_count=d("1"), dispute_count=d("2"))
    with pytest.raises(ValueError, match="ambiguous_rule_count"):
        incident(1, dispute_count=d("1"), ambiguous_rule_count=d("2"))
    with pytest.raises(ValueError, match="independent_evidence_family_count"):
        incident(
            1,
            evidence_family_count=d("1"),
            independent_evidence_family_count=d("2"),
        )
    with pytest.raises(ValueError, match="retrospective_outcome"):
        incident(1, retrospective_outcome="unknown")
    with pytest.raises(ValueError, match="paper_only"):
        replace(incident(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    dispute_report = report((incident(1),))

    with pytest.raises(FrozenInstanceError):
        dispute_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        dispute_report.rows[0].risk_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="pass_count"):
        replace(dispute_report, pass_count=d("0"))
    with pytest.raises(ValueError, match="rows"):
        replace(dispute_report, rows=(dispute_report.rows[0], dispute_report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(dispute_report.rows[0], risk_score=d("0.100000"))
    with pytest.raises(ValueError, match="dispute_frequency"):
        replace(dispute_report.rows[0], dispute_frequency=d("0.500000"), derived_validation_digest="")


def test_owned_module_has_no_trading_collection_or_write_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_dispute_history_report.py"
    )
    module_code = module_path.read_text(encoding="utf-8").lower()
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
        ".get(",
        ".post(",
        "insert",
        "update ",
        "delete ",
        "commit(",
        "execute(",
        "cursor(",
        "trade",
        "order",
        "buy",
        "sell",
    )

    assert all(term not in module_code for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
