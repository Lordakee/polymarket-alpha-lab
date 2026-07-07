from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_arbitration_risk_screen_report import (
    ResearchArbitrationRiskScreenConfig,
    ResearchArbitrationRiskScreenEvent,
    ResearchArbitrationRiskScreenReasonCodeCount,
    ResearchArbitrationRiskScreenReport,
    ResearchArbitrationRiskScreenRow,
    build_research_arbitration_risk_screen_report,
    research_arbitration_risk_screen_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEventShape:
    event_id: str
    market_slug: str
    rule_clarity_score: Decimal
    source_dependency_score: Decimal
    human_adjudication_score: Decimal
    dispute_history_score: Decimal
    resolution_source_count: Decimal = Decimal("1")
    prior_dispute_count: Decimal = Decimal("0")
    human_adjudication_required: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class UnsafeSuppliedEventShape:
    event_id: str
    market_slug: str
    rule_clarity_score: Decimal
    source_dependency_score: Decimal
    human_adjudication_score: Decimal
    dispute_history_score: Decimal
    wallet_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchArbitrationRiskScreenConfig:
    values = {
        "config_version": "research-arbitration-risk-screen-report-v0",
        "pass_max_risk_score": d("0.300000"),
        "watch_max_risk_score": d("0.600000"),
        "min_rule_clarity_score": d("0.250000"),
        "max_source_dependency_score": d("0.850000"),
        "max_human_adjudication_score": d("0.850000"),
        "max_dispute_history_score": d("0.850000"),
        "component_watch_score": d("0.500000"),
        "rule_clear_score": d("0.750000"),
        "rule_clarity_weight": d("0.350000"),
        "source_dependency_weight": d("0.250000"),
        "human_adjudication_weight": d("0.200000"),
        "dispute_history_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchArbitrationRiskScreenConfig(**values)


def event(
    index: int,
    *,
    event_id: str | None = None,
    market_slug: str | None = None,
    rule_clarity_score: Decimal = Decimal("0.950000"),
    source_dependency_score: Decimal = Decimal("0.100000"),
    human_adjudication_score: Decimal = Decimal("0.100000"),
    dispute_history_score: Decimal = Decimal("0.000000"),
    resolution_source_count: Decimal = Decimal("3"),
    prior_dispute_count: Decimal = Decimal("0"),
    human_adjudication_required: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchArbitrationRiskScreenEvent:
    return ResearchArbitrationRiskScreenEvent(
        event_id=event_id or f"event-{index:03d}",
        market_slug=market_slug or f"market-{index:03d}",
        rule_clarity_score=rule_clarity_score,
        source_dependency_score=source_dependency_score,
        human_adjudication_score=human_adjudication_score,
        dispute_history_score=dispute_history_score,
        resolution_source_count=resolution_source_count,
        prior_dispute_count=prior_dispute_count,
        human_adjudication_required=human_adjudication_required,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchArbitrationRiskScreenConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchArbitrationRiskScreenReport:
    return build_research_arbitration_risk_screen_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report() -> None:
    risk_report = report(())

    assert type(risk_report) is ResearchArbitrationRiskScreenReport
    assert risk_report.generated_at == GENERATED_AT
    assert risk_report.config_version == "research-arbitration-risk-screen-report-v0"
    assert risk_report.event_count == d("0")
    assert risk_report.pass_count == d("0")
    assert risk_report.watch_count == d("0")
    assert risk_report.block_count == d("0")
    assert risk_report.average_arbitration_risk_score is None
    assert risk_report.status == "block"
    assert risk_report.reason_codes == ("no_arbitration_risk_events",)
    assert risk_report.reason_code_counts == (
        ResearchArbitrationRiskScreenReasonCodeCount(
            reason_code="no_arbitration_risk_events",
            count=d("1"),
        ),
    )
    assert risk_report.rows == ()
    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True


def test_clear_rules_multiple_sources_low_human_review_and_no_disputes_pass() -> None:
    risk_report = report((event(1, reason_codes=("rules_checked",)),))

    assert risk_report.status == "pass"
    assert risk_report.event_count == d("1")
    assert risk_report.pass_count == d("1")
    assert risk_report.watch_count == d("0")
    assert risk_report.block_count == d("0")
    assert risk_report.average_arbitration_risk_score == d("0.062500")
    assert risk_report.reason_codes == ("research_arbitration_risk_pass",)

    row = risk_report.rows[0]
    assert type(row) is ResearchArbitrationRiskScreenRow
    assert row.event_id == "event-001"
    assert row.market_slug == "market-001"
    assert row.rule_clarity_score == d("0.950000")
    assert row.rule_ambiguity_score == d("0.050000")
    assert row.source_dependency_score == d("0.100000")
    assert row.human_adjudication_score == d("0.100000")
    assert row.dispute_history_score == d("0.000000")
    assert row.resolution_source_count == d("3")
    assert row.prior_dispute_count == d("0")
    assert row.human_adjudication_required is False
    assert row.arbitration_risk_score == d("0.062500")
    assert row.status == "pass"
    assert row.reason_codes == (
        "dispute_history_low",
        "human_adjudication_low",
        "input_rules_checked",
        "multiple_resolution_sources",
        "research_arbitration_risk_pass",
        "rules_clear",
        "source_dependency_low",
    )


def test_ambiguous_single_source_human_review_and_disputes_block() -> None:
    risk_report = report(
        (
            event(
                1,
                event_id="contested-event",
                market_slug="resolution-risk",
                rule_clarity_score=d("0.200000"),
                source_dependency_score=d("0.900000"),
                human_adjudication_score=d("0.850000"),
                dispute_history_score=d("0.800000"),
                resolution_source_count=d("1"),
                prior_dispute_count=d("2"),
                human_adjudication_required=True,
                reason_codes=("committee_needed",),
            ),
        ),
    )

    row = risk_report.rows[0]
    assert risk_report.status == "block"
    assert risk_report.block_count == d("1")
    assert risk_report.average_arbitration_risk_score == d("0.835000")
    assert row.event_id == "contested-event"
    assert row.rule_ambiguity_score == d("0.800000")
    assert row.arbitration_risk_score == d("0.835000")
    assert row.status == "block"
    assert row.reason_codes == (
        "aggregate_risk_above_watch_threshold",
        "dispute_history_elevated",
        "hard_component_block",
        "high_rule_ambiguity",
        "human_adjudication_elevated",
        "human_adjudication_required",
        "input_committee_needed",
        "prior_disputes_present",
        "research_arbitration_risk_block",
        "rules_ambiguous",
        "single_resolution_source",
        "source_dependency_elevated",
    )


def test_rows_reason_counts_and_payload_are_deterministic_without_float_values() -> None:
    supplied = SuppliedEventShape(
        event_id="a-event",
        market_slug="a-market",
        rule_clarity_score=d("0.700000"),
        source_dependency_score=d("0.200000"),
        human_adjudication_score=d("0.100000"),
        dispute_history_score=d("0.000000"),
        resolution_source_count=d("2"),
        reason_codes=("manual_reviewed",),
    )
    risk_report = report((event(2, event_id="z-event"), supplied))

    payload = research_arbitration_risk_screen_report_payload(risk_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.event_id for row in risk_report.rows) == ("a-event", "z-event")
    assert risk_report.rows[0].status == "watch"
    assert risk_report.rows[0].arbitration_risk_score == d("0.175000")
    assert tuple(
        (count.reason_code, count.count)
        for count in risk_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_manual_reviewed", d("1")),)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["arbitration_risk_score"] == "0.175000"
    assert payload["rows"][1]["rule_clarity_score"] == "0.950000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_unknown_status_times_flags_and_unsafe_payload() -> None:
    with pytest.raises(ValueError, match="weights"):
        config(rule_clarity_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_max_risk_score"):
        config(pass_max_risk_score=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_dependency_weight"):
        config(source_dependency_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_id"):
        event(1, event_id=" event-1")
    with pytest.raises(ValueError, match="rule_clarity_score"):
        event(1, rule_clarity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_source_count"):
        event(1, resolution_source_count=d("1.5"))
    with pytest.raises(ValueError, match="human_adjudication_required"):
        replace(event(1), human_adjudication_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        event(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe"):
        event(1, market_slug="wallet-risk")
    with pytest.raises(ValueError, match="unsafe"):
        report(
            (
                UnsafeSuppliedEventShape(
                    event_id="unsafe-event",
                    market_slug="unsafe-market",
                    rule_clarity_score=d("0.900000"),
                    source_dependency_score=d("0.100000"),
                    human_adjudication_score=d("0.100000"),
                    dispute_history_score=d("0.000000"),
                    wallet_reference="redacted",
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    risk_report = report((event(1),))

    with pytest.raises(FrozenInstanceError):
        risk_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.rows[0].arbitration_risk_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="rule_ambiguity_score"):
        replace(risk_report.rows[0], rule_ambiguity_score=d("0.900000"))
    with pytest.raises(ValueError, match="status"):
        replace(risk_report, status="watch")


def test_owned_module_has_no_network_filesystem_execution_or_write_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_arbitration_risk_screen_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
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
        "sqlite",
        "sqlalchemy",
        "supabase",
    )
    forbidden_field_terms = (
        "wallet_id",
        "wallet_address",
        "auth_token",
        "order_id",
        "order_size",
    )

    assert all(term not in source for term in forbidden_terms)
    assert all(term not in source for term in forbidden_field_terms)


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
