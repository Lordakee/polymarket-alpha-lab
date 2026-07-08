from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

import polymarket_alpha_lab.research_event_signal_conflict_priority_report as module
from polymarket_alpha_lab.research_event_signal_conflict_priority_report import (
    STATUSES,
    ResearchEventSignalConflictPriorityConfig,
    ResearchEventSignalConflictPriorityObservation,
    build_research_event_signal_conflict_priority_report,
    research_event_signal_conflict_priority_report_digest,
    research_event_signal_conflict_priority_report_payload,
)


GENERATED_AT = datetime(2026, 1, 15, 12, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    event_domain: str,
    contradiction_pressure: Decimal,
    evidence_freshness: Decimal,
    source_reliability: Decimal,
    catalyst_pressure: Decimal,
    team_confidence_dispersion: Decimal,
    observed_at: datetime | None = None,
) -> ResearchEventSignalConflictPriorityObservation:
    return ResearchEventSignalConflictPriorityObservation(
        event_domain=event_domain,
        contradiction_pressure=contradiction_pressure,
        evidence_freshness=evidence_freshness,
        source_reliability=source_reliability,
        catalyst_pressure=catalyst_pressure,
        team_confidence_dispersion=team_confidence_dispersion,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
    )


def test_prioritizes_signal_conflicts_by_public_event_domain() -> None:
    report = build_research_event_signal_conflict_priority_report(
        (
            observation(
                event_domain="sports",
                contradiction_pressure=d("0.200000"),
                evidence_freshness=d("0.900000"),
                source_reliability=d("0.950000"),
                catalyst_pressure=d("0.100000"),
                team_confidence_dispersion=d("0.100000"),
            ),
            observation(
                event_domain="macro",
                contradiction_pressure=d("0.450000"),
                evidence_freshness=d("0.600000"),
                source_reliability=d("0.750000"),
                catalyst_pressure=d("0.550000"),
                team_confidence_dispersion=d("0.350000"),
            ),
            observation(
                event_domain="politics",
                contradiction_pressure=d("0.900000"),
                evidence_freshness=d("0.100000"),
                source_reliability=d("0.300000"),
                catalyst_pressure=d("0.800000"),
                team_confidence_dispersion=d("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT,
    )

    assert STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.domain_count == d("3")
    assert report.observation_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.rows[0].event_domain == "politics"
    assert report.rows[0].priority_score == d("0.815000")
    assert report.rows[0].status == "block"
    assert report.rows[0].reason_codes == (
        "priority_score_block",
        "contradiction_pressure_elevated",
        "evidence_freshness_stale",
        "source_reliability_weak",
        "catalyst_pressure_elevated",
        "team_confidence_dispersion_elevated",
    )
    assert report.rows[1].event_domain == "macro"
    assert report.rows[1].status == "watch"
    assert report.rows[2].event_domain == "sports"
    assert report.rows[2].status == "pass"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_and_digest_are_deterministic_json_ready_and_sanitized() -> None:
    rows = (
        observation(
            event_domain="macro",
            contradiction_pressure=d("0.450000"),
            evidence_freshness=d("0.600000"),
            source_reliability=d("0.750000"),
            catalyst_pressure=d("0.550000"),
            team_confidence_dispersion=d("0.350000"),
        ),
        observation(
            event_domain="sports",
            contradiction_pressure=d("0.200000"),
            evidence_freshness=d("0.900000"),
            source_reliability=d("0.950000"),
            catalyst_pressure=d("0.100000"),
            team_confidence_dispersion=d("0.100000"),
        ),
    )
    left = build_research_event_signal_conflict_priority_report(
        rows,
        generated_at=GENERATED_AT,
    )
    right = build_research_event_signal_conflict_priority_report(
        tuple(reversed(rows)),
        generated_at=GENERATED_AT,
    )

    left_payload = research_event_signal_conflict_priority_report_payload(left)
    right_payload = research_event_signal_conflict_priority_report_payload(right)

    assert left_payload == right_payload
    assert json.loads(json.dumps(left_payload, sort_keys=True)) == left_payload
    assert research_event_signal_conflict_priority_report_digest(
        left,
    ) == research_event_signal_conflict_priority_report_digest(right)
    assert left_payload["paper_only"] is True
    assert left_payload["report_only"] is True
    assert left_payload["readonly"] is True
    assert left_payload["rows"][0]["paper_only"] is True
    assert "0.345000" in json.dumps(left_payload, sort_keys=True)

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            nested = set(value)
            for item in value.values():
                nested.update(keys(item))
            return nested
        if isinstance(value, list):
            nested: set[str] = set()
            for item in value:
                nested.update(keys(item))
            return nested
        return set()

    assert {
        "event_id",
        "market_id",
        "source_id",
        "source_name",
        "raw_event_id",
        "raw_market_id",
    }.isdisjoint(keys(left_payload))


def test_dataclasses_are_frozen_strict_and_require_decimal_inputs() -> None:
    config = ResearchEventSignalConflictPriorityConfig()
    with pytest.raises(FrozenInstanceError):
        config.watch_priority_score = d("0.100000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        observation(
            event_domain="macro",
            contradiction_pressure=0.4,  # type: ignore[arg-type]
            evidence_freshness=d("0.600000"),
            source_reliability=d("0.750000"),
            catalyst_pressure=d("0.550000"),
            team_confidence_dispersion=d("0.350000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventSignalConflictPriorityObservation(
            event_domain="macro",
            contradiction_pressure=d("0.450000"),
            evidence_freshness=d("0.600000"),
            source_reliability=d("0.750000"),
            catalyst_pressure=d("0.550000"),
            team_confidence_dispersion=d("0.350000"),
            observed_at=GENERATED_AT - timedelta(hours=1),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="future"):
        build_research_event_signal_conflict_priority_report(
            (
                observation(
                    event_domain="macro",
                    contradiction_pressure=d("0.450000"),
                    evidence_freshness=d("0.600000"),
                    source_reliability=d("0.750000"),
                    catalyst_pressure=d("0.550000"),
                    team_confidence_dispersion=d("0.350000"),
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            generated_at=GENERATED_AT,
        )


def test_empty_report_is_pass_and_module_has_no_mutation_surfaces() -> None:
    report = build_research_event_signal_conflict_priority_report(
        (),
        generated_at=GENERATED_AT,
    )

    assert report.status == "pass"
    assert report.domain_count == d("0")
    assert report.observation_count == d("0")
    assert report.max_priority_score is None
    assert report.rows == ()
    assert report.reason_codes == ("no_signal_conflicts",)

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "wallet",
        "private_key",
        "auth",
        "order",
        "trade",
        "execution",
        "live",
    ):
        assert forbidden not in source
