from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_source_evidence_freshness_matrix import (
    ResearchEventSourceEvidenceFreshnessMatrixConfig,
    ResearchEventSourceEvidenceFreshnessMatrixObservation,
    ResearchEventSourceEvidenceFreshnessMatrixReport,
    ResearchEventSourceEvidenceFreshnessMatrixRow,
    build_research_event_source_evidence_freshness_matrix_report,
    research_event_source_evidence_freshness_matrix_public_digest,
    research_event_source_evidence_freshness_matrix_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchEventSourceEvidenceFreshnessMatrixConfig:
    values = {
        "config_version": "research-event-source-evidence-freshness-matrix-v0",
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("86400.000000"),
        "min_evidence_count": d("3"),
        "min_source_family_count": d("2"),
        "min_required_role_count": d("2"),
        "pass_coverage_score": d("0.800000"),
        "watch_coverage_score": d("0.500000"),
    }
    values.update(overrides)
    return ResearchEventSourceEvidenceFreshnessMatrixConfig(**values)


def observation(
    index: int,
    *,
    event_key: str = "raw-candidate-id:market-42",
    evidence_key: str | None = None,
    source_family: str = "official",
    evidence_role: str = "official_event_notice",
    observed_at: datetime | None = None,
    conflict_signal: bool = False,
    hard_block_flag: bool = False,
) -> ResearchEventSourceEvidenceFreshnessMatrixObservation:
    return ResearchEventSourceEvidenceFreshnessMatrixObservation(
        event_key=event_key,
        evidence_key=(
            evidence_key
            if evidence_key is not None
            else f"https://sources.invalid/source-ref/{index:03d}"
        ),
        source_family=source_family,
        evidence_role=evidence_role,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        conflict_signal=conflict_signal,
        hard_block_flag=hard_block_flag,
    )


def report(
    rows: tuple[ResearchEventSourceEvidenceFreshnessMatrixObservation, ...],
    *,
    cfg: ResearchEventSourceEvidenceFreshnessMatrixConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventSourceEvidenceFreshnessMatrixReport:
    return build_research_event_source_evidence_freshness_matrix_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_fresh_covered_unconflicted_event_passes_without_leaking_raw_ids() -> None:
    freshness_report = report(
        (
            observation(
                3,
                source_family="analysis",
                evidence_role="independent_confirmation",
            ),
            observation(
                1,
                source_family="official",
                evidence_role="official_event_notice",
            ),
            observation(
                2,
                source_family="rules",
                evidence_role="market_rules",
            ),
        ),
    )

    payload = research_event_source_evidence_freshness_matrix_public_payload(
        freshness_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert freshness_report.status == "pass"
    assert freshness_report.event_count == d("1")
    assert freshness_report.pass_count == d("1")
    assert freshness_report.watch_count == d("0")
    assert freshness_report.block_count == d("0")
    assert freshness_report.average_freshness_score == d("1.000000")
    assert freshness_report.average_coverage_score == d("1.000000")
    assert freshness_report.average_conflict_risk_score == d("0.000000")
    assert freshness_report.reason_codes == ("freshness_matrix_pass",)

    row = freshness_report.rows[0]
    assert type(row) is ResearchEventSourceEvidenceFreshnessMatrixRow
    assert row.event_public_id == "event-001"
    assert row.evidence_count == d("3")
    assert row.source_family_count == d("3")
    assert row.required_role_count == d("3")
    assert row.fresh_evidence_count == d("3")
    assert row.stale_evidence_count == d("0")
    assert row.conflict_signal_count == d("0")
    assert row.hard_flag_count == d("0")
    assert row.latest_observed_at == GENERATED_AT - timedelta(minutes=30)
    assert row.latest_evidence_age_seconds == d("1800.000000")
    assert row.oldest_evidence_age_seconds == d("1800.000000")
    assert row.freshness_score == d("1.000000")
    assert row.coverage_score == d("1.000000")
    assert row.conflict_risk_score == d("0.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("freshness_matrix_pass",)

    assert payload["public_digest"] == freshness_report.public_digest
    assert "raw-candidate-id" not in encoded
    assert "market-42" not in encoded
    assert "source-ref" not in encoded
    assert "sources.invalid" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_stale_or_thin_coverage_event_is_watch() -> None:
    freshness_report = report(
        (
            observation(
                2,
                event_key="watch-event",
                source_family="analysis",
                evidence_role="independent_confirmation",
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
            observation(
                1,
                event_key="watch-event",
                source_family="official",
                evidence_role="official_event_notice",
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
    )

    row = freshness_report.rows[0]
    assert freshness_report.status == "watch"
    assert freshness_report.pass_count == d("0")
    assert freshness_report.watch_count == d("1")
    assert freshness_report.block_count == d("0")
    assert row.status == "watch"
    assert row.evidence_count == d("2")
    assert row.source_family_count == d("2")
    assert row.required_role_count == d("2")
    assert row.fresh_evidence_count == d("0")
    assert row.stale_evidence_count == d("0")
    assert row.freshness_score == d("0.916667")
    assert row.coverage_score == d("0.888889")
    assert row.reason_codes == (
        "freshness_refresh_needed",
        "freshness_matrix_watch",
    )


def test_missing_fresh_evidence_and_hard_flags_block_event() -> None:
    freshness_report = report(
        (
            observation(
                1,
                event_key="block-event",
                source_family="official",
                evidence_role="official_event_notice",
                observed_at=GENERATED_AT - timedelta(days=3),
                conflict_signal=True,
                hard_block_flag=True,
            ),
        ),
    )

    row = freshness_report.rows[0]
    assert freshness_report.status == "block"
    assert freshness_report.block_count == d("1")
    assert freshness_report.average_conflict_risk_score == d("1.000000")
    assert row.status == "block"
    assert row.evidence_count == d("1")
    assert row.source_family_count == d("1")
    assert row.required_role_count == d("1")
    assert row.fresh_evidence_count == d("0")
    assert row.stale_evidence_count == d("1")
    assert row.conflict_signal_count == d("1")
    assert row.hard_flag_count == d("1")
    assert row.freshness_score == d("0.000000")
    assert row.coverage_score == d("0.444444")
    assert row.conflict_risk_score == d("1.000000")
    assert row.reason_codes == (
        "coverage_below_watch_floor",
        "freshness_matrix_block",
        "hard_collection_flag_present",
        "no_fresh_evidence",
        "stale_evidence_present",
    )


def test_decimal_type_rejection_and_datetime_validation() -> None:
    with pytest.raises(ValueError, match="fresh_age_seconds"):
        config(fresh_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pass_coverage_score"):
        config(pass_coverage_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_coverage_score"):
        config(watch_coverage_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="stale_age_seconds"):
        config(stale_age_seconds=d("3599.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=_DatetimeSubclass(2026, 7, 6, 11, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="conflict_signal"):
        replace(observation(1), conflict_signal=1)  # type: ignore[arg-type]


def test_public_payload_rejects_leaky_keys_values_and_numeric_types() -> None:
    freshness_report = report((observation(1), observation(2), observation(3)))
    payload = research_event_source_evidence_freshness_matrix_public_payload(
        freshness_report,
    )

    leaky_payload = dict(payload)
    leaky_payload["market_id"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe public payload key"):
        research_event_source_evidence_freshness_matrix_public_payload(leaky_payload)

    leaky_payload = dict(payload)
    leaky_payload["status"] = "recommend_buy"
    with pytest.raises(ValueError, match="unsafe public payload value"):
        research_event_source_evidence_freshness_matrix_public_payload(leaky_payload)

    numeric_payload = dict(payload)
    numeric_payload["event_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        research_event_source_evidence_freshness_matrix_public_payload(numeric_payload)


def test_hard_flags_are_required_and_public_dataclasses_are_frozen() -> None:
    freshness_report = report((observation(1), observation(2), observation(3)))

    with pytest.raises(FrozenInstanceError):
        freshness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        freshness_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(freshness_report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(freshness_report, readonly=False)


def test_payload_and_digest_are_deterministic_and_consistent() -> None:
    rows = (
        observation(
            4,
            event_key="z-event",
            source_family="analysis",
            evidence_role="independent_confirmation",
        ),
        observation(
            2,
            event_key="a-event",
            source_family="official",
            evidence_role="official_event_notice",
        ),
        observation(
            3,
            event_key="z-event",
            source_family="rules",
            evidence_role="market_rules",
            conflict_signal=True,
        ),
        observation(
            1,
            event_key="a-event",
            source_family="analysis",
            evidence_role="independent_confirmation",
        ),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_event_source_evidence_freshness_matrix_public_payload(
        first_report,
    )
    second_payload = research_event_source_evidence_freshness_matrix_public_payload(
        second_report,
    )

    assert first_payload == second_payload
    assert tuple(row.event_public_id for row in first_report.rows) == (
        "event-001",
        "event-002",
    )
    assert first_report.rows[0].status == "watch"
    assert first_report.rows[1].status == "watch"
    assert first_report.status == "watch"
    assert first_report.public_digest == second_report.public_digest
    assert first_report.public_digest == research_event_source_evidence_freshness_matrix_public_digest(
        first_report,
    )
    assert first_report.public_digest == research_event_source_evidence_freshness_matrix_public_digest(
        first_payload,
    )
    assert len(first_report.public_digest) == 64

    tampered_payload = dict(first_payload)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="public_digest"):
        research_event_source_evidence_freshness_matrix_public_payload(tampered_payload)


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_source_evidence_freshness_matrix.py"
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
        "wallet",
        "order",
        "trade",
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
