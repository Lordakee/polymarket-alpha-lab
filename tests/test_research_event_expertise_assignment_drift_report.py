from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_expertise_assignment_drift_report import (
    ResearchEventExpertiseAssignmentDriftConfig,
    ResearchEventExpertiseAssignmentDriftReasonCodeCount,
    ResearchEventExpertiseAssignmentDriftReport,
    ResearchEventExpertiseAssignmentDriftRow,
    ResearchEventExpertiseAssignmentDriftSignal,
    build_research_event_expertise_assignment_drift_report,
    research_event_expertise_assignment_drift_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSignalShape:
    domain_bucket: str
    team_bucket: str
    need_count: Decimal
    assigned_count: Decimal
    expertise_fit_score: Decimal
    capacity_buffer_score: Decimal
    memory_freshness_score: Decimal
    calibration_score: Decimal
    catalyst_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventExpertiseAssignmentDriftConfig:
    values = {
        "config_version": "research-event-expertise-assignment-drift-report-v0",
        "pass_drift_score": d("0.750000"),
        "watch_drift_score": d("0.500000"),
        "min_expertise_fit_score": d("0.700000"),
        "min_capacity_buffer_score": d("0.250000"),
        "min_memory_freshness_score": d("0.600000"),
        "min_calibration_score": d("0.650000"),
        "max_catalyst_pressure_score": d("0.700000"),
        "expertise_weight": d("0.300000"),
        "capacity_weight": d("0.200000"),
        "memory_weight": d("0.200000"),
        "calibration_weight": d("0.200000"),
        "catalyst_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchEventExpertiseAssignmentDriftConfig(**values)


def signal(
    *,
    domain_bucket: str = "macro-policy",
    team_bucket: str = "policy-specialists",
    need_count: Decimal = d("8"),
    assigned_count: Decimal = d("8"),
    expertise_fit_score: Decimal = d("0.850000"),
    capacity_buffer_score: Decimal = d("0.550000"),
    memory_freshness_score: Decimal = d("0.800000"),
    calibration_score: Decimal = d("0.780000"),
    catalyst_pressure_score: Decimal = d("0.300000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventExpertiseAssignmentDriftSignal:
    return ResearchEventExpertiseAssignmentDriftSignal(
        domain_bucket=domain_bucket,
        team_bucket=team_bucket,
        need_count=need_count,
        assigned_count=assigned_count,
        expertise_fit_score=expertise_fit_score,
        capacity_buffer_score=capacity_buffer_score,
        memory_freshness_score=memory_freshness_score,
        calibration_score=calibration_score,
        catalyst_pressure_score=catalyst_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventExpertiseAssignmentDriftConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventExpertiseAssignmentDriftReport:
    return build_research_event_expertise_assignment_drift_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_zero_counts_and_deterministic_digest() -> None:
    drift_report = report(())
    payload = research_event_expertise_assignment_drift_report_payload(drift_report)

    assert type(drift_report) is ResearchEventExpertiseAssignmentDriftReport
    assert drift_report.generated_at == GENERATED_AT
    assert drift_report.config_version == (
        "research-event-expertise-assignment-drift-report-v0"
    )
    assert drift_report.domain_count == d("0")
    assert drift_report.team_count == d("0")
    assert drift_report.total_need_count == d("0")
    assert drift_report.total_assigned_count == d("0")
    assert drift_report.pass_count == d("0")
    assert drift_report.watch_count == d("0")
    assert drift_report.block_count == d("0")
    assert drift_report.average_drift_score is None
    assert drift_report.status == "block"
    assert drift_report.rows == ()
    assert drift_report.reason_codes == ("no_assignment_signals",)
    assert drift_report.reason_code_counts == (
        ResearchEventExpertiseAssignmentDriftReasonCodeCount(
            reason_code="no_assignment_signals",
            count=d("1"),
        ),
    )
    assert drift_report.paper_only is True
    assert drift_report.report_only is True
    assert drift_report.readonly is True
    assert payload["payload_digest"] == drift_report.payload_digest
    assert payload == research_event_expertise_assignment_drift_report_payload(
        drift_report,
    )


def test_pass_watch_and_block_rows_score_assignment_drift_metrics() -> None:
    drift_report = report(
        (
            signal(
                domain_bucket="tech-policy",
                team_bucket="policy-specialists",
                need_count=d("10"),
                assigned_count=d("10"),
                expertise_fit_score=d("0.850000"),
                capacity_buffer_score=d("0.550000"),
                memory_freshness_score=d("0.800000"),
                calibration_score=d("0.780000"),
                catalyst_pressure_score=d("0.300000"),
            ),
            signal(
                domain_bucket="weather-risk",
                team_bucket="climate-specialists",
                need_count=d("12"),
                assigned_count=d("9"),
                expertise_fit_score=d("0.680000"),
                capacity_buffer_score=d("0.250000"),
                memory_freshness_score=d("0.620000"),
                calibration_score=d("0.660000"),
                catalyst_pressure_score=d("0.650000"),
            ),
            signal(
                domain_bucket="macro-policy",
                team_bucket="generalist-queue",
                need_count=d("8"),
                assigned_count=d("3"),
                expertise_fit_score=d("0.420000"),
                capacity_buffer_score=d("0.100000"),
                memory_freshness_score=d("0.400000"),
                calibration_score=d("0.500000"),
                catalyst_pressure_score=d("0.900000"),
            ),
        ),
    )

    assert drift_report.status == "block"
    assert drift_report.domain_count == d("3")
    assert drift_report.team_count == d("3")
    assert drift_report.total_need_count == d("30")
    assert drift_report.total_assigned_count == d("22")
    assert drift_report.pass_count == d("1")
    assert drift_report.watch_count == d("1")
    assert drift_report.block_count == d("1")
    assert drift_report.average_drift_score == d("0.544000")
    assert tuple(row.domain_bucket for row in drift_report.rows) == (
        "macro-policy",
        "tech-policy",
        "weather-risk",
    )

    block_row, pass_row, watch_row = drift_report.rows
    assert type(block_row) is ResearchEventExpertiseAssignmentDriftRow
    assert block_row.assignment_coverage_score == d("0.375000")
    assert block_row.drift_score == d("0.336000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "assignment_coverage_low",
        "calibration_drift",
        "capacity_buffer_low",
        "catalyst_pressure_high",
        "expertise_fit_low",
        "memory_freshness_low",
    )
    assert pass_row.drift_score == d("0.751000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("assignment_fit_aligned",)
    assert watch_row.assignment_coverage_score == d("0.750000")
    assert watch_row.drift_score == d("0.545000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "assignment_coverage_watch",
        "catalyst_pressure_watch",
        "expertise_fit_watch",
    )


def test_payload_is_decimal_only_public_safe_and_digest_is_canonical() -> None:
    drift_report = report(
        (
            SuppliedSignalShape(
                domain_bucket="z-domain",
                team_bucket="z-team",
                need_count=d("4"),
                assigned_count=d("2"),
                expertise_fit_score=d("0.600000"),
                capacity_buffer_score=d("0.250000"),
                memory_freshness_score=d("0.600000"),
                calibration_score=d("0.650000"),
                catalyst_pressure_score=d("0.700000"),
            ),
            signal(domain_bucket="a-domain", team_bucket="a-team"),
        ),
    )

    payload = research_event_expertise_assignment_drift_report_payload(drift_report)
    digest_payload = dict(payload)
    digest_payload.pop("payload_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert tuple(row.domain_bucket for row in drift_report.rows) == (
        "a-domain",
        "z-domain",
    )
    assert payload["rows"][0]["drift_score"] == str(
        drift_report.rows[0].drift_score,
    )
    assert drift_report.payload_digest == hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()
    assert payload["payload_digest"] == drift_report.payload_digest
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert "market-alpha" not in encoded
    assert "event-12345" not in encoded
    assert "source-001" not in encoded
    assert "order" not in encoded
    assert "trade" not in encoded


def test_validation_rejects_bad_types_flags_statuses_and_raw_identifiers() -> None:
    with pytest.raises(ValueError, match="pass_drift_score"):
        config(pass_drift_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="capacity_weight"):
        config(capacity_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="weights"):
        config(expertise_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal(),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="need_count"):
        signal(need_count=d("0"))
    with pytest.raises(ValueError, match="assigned_count"):
        signal(assigned_count=d("9"))
    with pytest.raises(ValueError, match="expertise_fit_score"):
        signal(expertise_fit_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="domain_bucket"):
        signal(domain_bucket="event-12345")
    with pytest.raises(ValueError, match="team_bucket"):
        signal(team_bucket=" market-alpha")
    with pytest.raises(ValueError, match="status"):
        replace(report((signal(),)).rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    drift_report = report((signal(),))

    with pytest.raises(FrozenInstanceError):
        drift_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        drift_report.rows[0].drift_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="drift_score"):
        replace(drift_report.rows[0], drift_score=d("0.100000"))
    with pytest.raises(ValueError, match="payload_digest"):
        replace(drift_report, payload_digest="bad-digest")
    with pytest.raises(ValueError, match="status"):
        replace(drift_report, status="watch")


def test_owned_module_has_no_network_storage_or_live_surface_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_expertise_assignment_drift_report.py"
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
        "psycopg",
        "sqlite",
        "wallet",
        "auth",
        "order",
        "trade",
        "execution",
        "recommend",
        "sizing",
        "buy",
        "sell",
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
