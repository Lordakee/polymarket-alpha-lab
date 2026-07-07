from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_probabilistic_scenario_tree_report import (
    ResearchProbabilisticScenarioEvidence,
    ResearchProbabilisticScenarioTreeConfig,
    ResearchProbabilisticScenarioTreeEventSummary,
    ResearchProbabilisticScenarioTreeReasonCodeCount,
    ResearchProbabilisticScenarioTreeReport,
    ResearchProbabilisticScenarioTreeRow,
    build_research_probabilistic_scenario_tree_report,
    research_probabilistic_scenario_tree_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchProbabilisticScenarioTreeConfig:
    values = {
        "config_version": "research-probabilistic-scenario-tree-report-v0",
        "min_scenario_count": d("2"),
        "pass_min_evidence_weight": d("0.700000"),
        "watch_min_evidence_weight": d("0.400000"),
        "pass_max_probability_interval_width": d("0.200000"),
        "watch_max_probability_interval_width": d("0.400000"),
    }
    values.update(overrides)
    return ResearchProbabilisticScenarioTreeConfig(**values)


def evidence(
    index: int,
    *,
    event_id: str = "candidate-alpha",
    scenario_id: str = "yes",
    evidence_family: str = "official",
    evidence_weight: Decimal = d("0.500000"),
    probability_low: Decimal = d("0.520000"),
    probability_high: Decimal = d("0.620000"),
    observed_at: datetime | None = None,
    blocking_condition: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchProbabilisticScenarioEvidence:
    return ResearchProbabilisticScenarioEvidence(
        event_id=event_id,
        scenario_id=scenario_id,
        evidence_id=f"evidence-{index:03d}",
        evidence_family=evidence_family,
        evidence_weight=evidence_weight,
        probability_low=probability_low,
        probability_high=probability_high,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        blocking_condition=blocking_condition,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchProbabilisticScenarioTreeConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchProbabilisticScenarioTreeReport:
    return build_research_probabilistic_scenario_tree_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_tree() -> None:
    tree = report(())

    assert type(tree) is ResearchProbabilisticScenarioTreeReport
    assert tree.generated_at == GENERATED_AT
    assert tree.config_version == "research-probabilistic-scenario-tree-report-v0"
    assert tree.event_count == d("0")
    assert tree.scenario_count == d("0")
    assert tree.evidence_count == d("0")
    assert tree.pass_count == d("0")
    assert tree.watch_count == d("0")
    assert tree.blocked_count == d("0")
    assert tree.status == "block"
    assert tree.rows == ()
    assert tree.event_summaries == ()
    assert tree.reason_codes == ("no_candidate_probability_evidence",)
    assert tree.reason_code_counts == (
        ResearchProbabilisticScenarioTreeReasonCodeCount(
            reason_code="no_candidate_probability_evidence",
            count=d("1"),
        ),
    )
    assert tree.paper_only is True
    assert tree.report_only is True
    assert tree.readonly is True


def test_mutually_exclusive_weighted_scenarios_pass_with_decimal_intervals() -> None:
    tree = report(
        (
            evidence(
                2,
                scenario_id="no",
                evidence_family="venue",
                evidence_weight=d("0.500000"),
                probability_low=d("0.380000"),
                probability_high=d("0.480000"),
            ),
            evidence(
                1,
                scenario_id="yes",
                evidence_family="official",
                evidence_weight=d("0.800000"),
                probability_low=d("0.520000"),
                probability_high=d("0.620000"),
                reason_codes=("manual_reviewed",),
            ),
            evidence(
                3,
                scenario_id="yes",
                evidence_family="analytics",
                evidence_weight=d("0.200000"),
                probability_low=d("0.500000"),
                probability_high=d("0.640000"),
            ),
            evidence(
                4,
                scenario_id="no",
                evidence_family="official",
                evidence_weight=d("0.500000"),
                probability_low=d("0.400000"),
                probability_high=d("0.500000"),
            ),
        ),
    )

    assert tree.status == "pass"
    assert tree.event_count == d("1")
    assert tree.scenario_count == d("2")
    assert tree.evidence_count == d("4")
    assert tree.pass_count == d("2")
    assert tree.watch_count == d("0")
    assert tree.blocked_count == d("0")
    assert tree.reason_codes == ("scenario_tree_pass",)

    assert tree.event_summaries == (
        ResearchProbabilisticScenarioTreeEventSummary(
            event_id="candidate-alpha",
            scenario_count=d("2"),
            evidence_count=d("4"),
            probability_low_sum=d("0.906000"),
            probability_high_sum=d("1.114000"),
            probability_midpoint_sum=d("1.010000"),
            residual_probability_midpoint=d("0.000000"),
            status="pass",
            reason_codes=("mutually_exclusive_scenarios_supported",),
        ),
    )

    yes, no = tree.rows
    assert type(yes) is ResearchProbabilisticScenarioTreeRow
    assert yes.event_id == "candidate-alpha"
    assert yes.scenario_id == "yes"
    assert yes.evidence_count == d("2")
    assert yes.evidence_weight_total == d("1.000000")
    assert yes.probability_low == d("0.516000")
    assert yes.probability_high == d("0.624000")
    assert yes.probability_midpoint == d("0.570000")
    assert yes.probability_interval_width == d("0.108000")
    assert yes.evidence_ids == ("evidence-001", "evidence-003")
    assert yes.evidence_families == ("analytics", "official")
    assert yes.status == "pass"
    assert yes.reason_codes == (
        "evidence_weight_pass",
        "input_manual_reviewed",
        "probability_interval_pass",
        "scenario_tree_pass",
    )

    assert no.scenario_id == "no"
    assert no.probability_low == d("0.390000")
    assert no.probability_high == d("0.490000")
    assert no.status == "pass"


def test_blocking_condition_and_impossible_exclusive_mass_block_tree() -> None:
    tree = report(
        (
            evidence(
                1,
                scenario_id="yes",
                probability_low=d("0.700000"),
                probability_high=d("0.800000"),
                blocking_condition=True,
            ),
            evidence(
                2,
                scenario_id="no",
                probability_low=d("0.500000"),
                probability_high=d("0.600000"),
            ),
        ),
    )

    assert tree.status == "block"
    assert tree.blocked_count == d("2")
    assert tree.event_summaries[0].status == "block"
    assert tree.event_summaries[0].reason_codes == (
        "blocking_condition_present",
        "mutual_exclusivity_probability_overlap",
    )
    assert tree.rows[0].status == "block"
    assert "blocking_condition_present" in tree.rows[0].reason_codes
    assert "mutual_exclusivity_probability_overlap" in tree.rows[1].reason_codes


def test_watch_status_for_wide_intervals_or_low_evidence_weight() -> None:
    tree = report(
        (
            evidence(
                1,
                scenario_id="yes",
                evidence_weight=d("0.500000"),
                probability_low=d("0.300000"),
                probability_high=d("0.650000"),
            ),
            evidence(
                2,
                scenario_id="no",
                evidence_weight=d("0.500000"),
                probability_low=d("0.350000"),
                probability_high=d("0.700000"),
            ),
        ),
    )

    assert tree.status == "watch"
    assert tree.watch_count == d("2")
    assert tuple(row.status for row in tree.rows) == ("watch", "watch")
    assert tree.reason_codes == ("scenario_tree_watch",)
    assert all("probability_interval_watch" in row.reason_codes for row in tree.rows)


def test_payload_is_decimal_string_only_and_excludes_raw_private_terms() -> None:
    tree = report(
        (
            evidence(1, scenario_id="yes"),
            evidence(
                2,
                scenario_id="no",
                probability_low=d("0.380000"),
                probability_high=d("0.480000"),
            ),
        ),
    )

    payload = research_probabilistic_scenario_tree_report_payload(tree)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["probability_midpoint"] == "0.570000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert all(
        private_fragment not in encoded.lower()
        for private_fragment in (
            "raw_market",
            "raw_source",
            "raw_question",
            "market",
            "source",
            "question",
            "dsn",
            "table",
            "token",
            "trade",
            "order",
            "recommendation",
        )
    )
    assert ": 0.5" not in encoded


def test_validation_rejects_floats_bad_dates_bad_flags_and_tampered_reports() -> None:
    with pytest.raises(ValueError, match="pass_min_evidence_weight"):
        config(pass_min_evidence_weight=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_evidence_weight"):
        config(watch_min_evidence_weight=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" research-probabilistic-scenario-tree-report-v0")
    with pytest.raises(ValueError, match="min_scenario_count"):
        config(min_scenario_count=d("0"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_id"):
        evidence(1, event_id="candidate alpha")
    with pytest.raises(ValueError, match="evidence_weight"):
        evidence(1, evidence_weight=d("0"))
    with pytest.raises(ValueError, match="probability_low"):
        evidence(1, probability_low=d("-0.100000"))
    with pytest.raises(ValueError, match="probability_high"):
        evidence(1, probability_low=d("0.700000"), probability_high=d("0.600000"))
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="blocking_condition"):
        replace(evidence(1), blocking_condition=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("token_secret",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)

    tree = report((evidence(1, scenario_id="yes"), evidence(2, scenario_id="no")))
    with pytest.raises(ValueError, match="scenario_count"):
        replace(tree, scenario_count=d("3"))
    with pytest.raises(ValueError, match="status"):
        replace(tree, status="pass")


def test_public_dataclasses_are_frozen() -> None:
    tree = report((evidence(1, scenario_id="yes"), evidence(2, scenario_id="no")))

    with pytest.raises(FrozenInstanceError):
        tree.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        tree.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        tree.event_summaries[0].status = "watch"  # type: ignore[misc]


def test_owned_module_has_no_db_network_write_or_trading_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_probabilistic_scenario_tree_report.py"
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
        "insert ",
        "update ",
        "delete ",
        "trade",
        "order",
        "recommendation",
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
