from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_outcome_label_quality_report import (
    ResearchOutcomeLabelQualityConfig,
    ResearchOutcomeLabelQualityMemoryWritePlan,
    ResearchOutcomeLabelQualityObservation,
    ResearchOutcomeLabelQualityReasonCodeCount,
    ResearchOutcomeLabelQualityReport,
    ResearchOutcomeLabelQualityRow,
    build_research_outcome_label_quality_report,
    research_outcome_label_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    event_id: str
    outcome_id: str
    observation_id: str
    origin_fingerprint: str | None
    origin_kind: str
    observed_at: datetime
    label_digest: str | None
    settlement_label_digest: str | None
    settled: bool = True
    dispute_flag: bool = False
    dispute_status: str = "none"
    review_usability_score: Decimal = Decimal("0.800000")
    memory_write_eligible: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchOutcomeLabelQualityConfig:
    values = {
        "config_version": "research-outcome-label-quality-report-v0",
        "min_origin_count": d("2"),
        "pass_consistency_ratio": d("1.000000"),
        "watch_consistency_ratio": d("0.500000"),
        "min_review_usability_score": d("0.700000"),
        "memory_plan_version": "local-memory-plan-v0",
    }
    values.update(overrides)
    return ResearchOutcomeLabelQualityConfig(**values)


def observation(
    index: int,
    *,
    event_id: str = "event-alpha",
    outcome_id: str = "outcome-yes",
    origin_fingerprint: str | None = None,
    origin_kind: str = "official_resolution",
    label_digest: str | None = "label-digest-yes",
    settlement_label_digest: str | None = "label-digest-yes",
    settled: bool = True,
    dispute_flag: bool = False,
    dispute_status: str = "none",
    review_usability_score: Decimal = d("0.900000"),
    memory_write_eligible: bool = True,
    reason_codes: tuple[str, ...] = (),
    observed_at: datetime | None = None,
) -> ResearchOutcomeLabelQualityObservation:
    return ResearchOutcomeLabelQualityObservation(
        event_id=event_id,
        outcome_id=outcome_id,
        observation_id=f"observation-{index:03d}",
        origin_fingerprint=(
            f"origin-fingerprint-{index:03d}"
            if origin_fingerprint is None
            else origin_fingerprint
        ),
        origin_kind=origin_kind,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=1)
        ),
        label_digest=label_digest,
        settlement_label_digest=settlement_label_digest,
        settled=settled,
        dispute_flag=dispute_flag,
        dispute_status=dispute_status,
        review_usability_score=review_usability_score,
        memory_write_eligible=memory_write_eligible,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchOutcomeLabelQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchOutcomeLabelQualityReport:
    return build_research_outcome_label_quality_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_consistent_settled_label_origins_pass_with_memory_write_plan() -> None:
    quality_report = report(
        (
            observation(
                2,
                origin_kind="venue_notice",
                review_usability_score=d("0.800000"),
                reason_codes=("manual_reconciled",),
            ),
            observation(1, origin_kind="official_resolution"),
        ),
    )

    assert type(quality_report) is ResearchOutcomeLabelQualityReport
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.config_version == "research-outcome-label-quality-report-v0"
    assert quality_report.event_outcome_count == d("1")
    assert quality_report.observation_count == d("2")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.memory_write_planned_count == d("1")
    assert quality_report.status == "pass"
    assert quality_report.reason_codes == ("outcome_label_quality_pass",)
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True

    row = quality_report.rows[0]
    assert type(row) is ResearchOutcomeLabelQualityRow
    assert row.event_id == "event-alpha"
    assert row.outcome_id == "outcome-yes"
    assert row.observation_count == d("2")
    assert row.origin_count == d("2")
    assert row.matching_label_count == d("2")
    assert row.mismatching_label_count == d("0")
    assert row.missing_label_count == d("0")
    assert row.dispute_flag_count == d("0")
    assert row.open_dispute_count == d("0")
    assert row.review_usable_observation_count == d("2")
    assert row.label_consistency_ratio == d("1.000000")
    assert row.review_usability_score == d("0.850000")
    assert row.memory_write_planned_count == d("1")
    assert row.status == "pass"
    assert row.reason_codes == (
        "input_manual_reconciled",
        "label_origin_coverage_pass",
        "memory_write_plan_ready",
        "outcome_label_quality_pass",
        "review_usable",
        "settlement_label_consistent",
    )

    plan = row.memory_write_plans[0]
    assert type(plan) is ResearchOutcomeLabelQualityMemoryWritePlan
    assert plan.backend == "local_supabase_postgres"
    assert plan.operation == "queue_outcome_label_memory_upsert"
    assert plan.dry_run_only is True
    assert plan.eligible is True
    assert plan.reason_codes == ("memory_write_plan_ready",)


def test_watch_and_block_rows_roll_up_to_block_report() -> None:
    quality_report = report(
        (
            observation(
                1,
                event_id="event-watch",
                outcome_id="outcome-a",
                origin_fingerprint="one-origin",
                review_usability_score=d("0.750000"),
            ),
            observation(
                2,
                event_id="event-block",
                outcome_id="outcome-b",
                origin_fingerprint="origin-a",
                label_digest="label-digest-no",
                settlement_label_digest="label-digest-yes",
                dispute_flag=True,
                dispute_status="open",
                review_usability_score=d("0.600000"),
                memory_write_eligible=False,
            ),
            observation(
                3,
                event_id="event-block",
                outcome_id="outcome-b",
                origin_fingerprint="origin-b",
                label_digest=None,
                settlement_label_digest="label-digest-yes",
                dispute_flag=True,
                dispute_status="resolved",
                review_usability_score=d("0.800000"),
                memory_write_eligible=False,
            ),
        ),
    )

    assert quality_report.status == "block"
    assert quality_report.event_outcome_count == d("2")
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("1")
    assert quality_report.block_count == d("1")
    assert quality_report.memory_write_planned_count == d("0")
    assert tuple(row.status for row in quality_report.rows) == ("block", "watch")

    blocked_row = quality_report.rows[0]
    assert blocked_row.event_id == "event-block"
    assert blocked_row.label_consistency_ratio == d("0.000000")
    assert blocked_row.review_usability_score == d("0.700000")
    assert blocked_row.mismatching_label_count == d("1")
    assert blocked_row.missing_label_count == d("1")
    assert blocked_row.dispute_flag_count == d("2")
    assert blocked_row.open_dispute_count == d("1")
    assert blocked_row.memory_write_planned_count == d("0")
    assert blocked_row.reason_codes == (
        "dispute_flags_present",
        "label_digest_missing",
        "label_origin_coverage_pass",
        "memory_write_plan_block",
        "open_dispute_present",
        "outcome_label_quality_block",
        "review_usable",
        "settlement_label_mismatch",
    )

    watch_row = quality_report.rows[1]
    assert watch_row.event_id == "event-watch"
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "memory_write_plan_block",
        "not_enough_label_origin_coverage",
        "outcome_label_quality_watch",
        "review_usable",
        "settlement_label_consistent",
    )


def test_payload_is_public_decimal_only_and_excludes_raw_surfaces() -> None:
    quality_report = report(
        (
            observation(2, origin_kind="venue_notice"),
            observation(1, origin_kind="official_resolution"),
        ),
    )

    payload = research_outcome_label_quality_report_payload(quality_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["observation_count"] == "2"
    assert payload["rows"][0]["label_consistency_ratio"] == "1.000000"
    assert payload["rows"][0]["memory_write_plans"][0]["backend"] == (
        "local_supabase_postgres"
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    for unsafe_fragment in ("raw", "market", "source", "url", "text", "dsn", "table", "token"):
        assert unsafe_fragment not in encoded.lower()


def test_supplied_shapes_are_normalized_and_reason_counts_are_deterministic() -> None:
    quality_report = report(
        (
            SuppliedObservationShape(
                event_id="z-event",
                outcome_id="outcome-b",
                observation_id="obs-z",
                origin_fingerprint="origin-z",
                origin_kind="curator_review",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                label_digest="label-digest-yes",
                settlement_label_digest="label-digest-yes",
                reason_codes=("zeta", "alpha"),
            ),
            observation(1, event_id="a-event", outcome_id="outcome-a"),
            observation(2, event_id="a-event", outcome_id="outcome-a"),
        ),
    )

    assert tuple((row.event_id, row.outcome_id) for row in quality_report.rows) == (
        ("a-event", "outcome-a"),
        ("z-event", "outcome-b"),
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in quality_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert type(quality_report.reason_code_counts[0]) is ResearchOutcomeLabelQualityReasonCodeCount


def test_validation_rejects_bad_types_unknown_enums_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="min_origin_count"):
        config(min_origin_count=d("1.5"))
    with pytest.raises(ValueError, match="pass_consistency_ratio"):
        config(pass_consistency_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_consistency_ratio"):
        config(watch_consistency_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_id"):
        observation(1, event_id=" event-alpha")
    with pytest.raises(ValueError, match="origin_kind"):
        observation(1, origin_kind="blog_post")
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="settled"):
        replace(observation(1), settled=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dispute_status"):
        observation(1, dispute_status="contested")
    with pytest.raises(ValueError, match="review_usability_score"):
        observation(1, review_usability_score=d("1.1"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    quality_report = report((observation(1), observation(2)))

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(quality_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="memory_write_planned_count"):
        replace(quality_report, memory_write_planned_count=d("0"))


def test_owned_module_has_no_network_database_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_outcome_label_quality_report.py"
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
        "cursor(",
        ".execute(",
        "psycopg",
        "sqlalchemy",
        "asyncpg",
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
