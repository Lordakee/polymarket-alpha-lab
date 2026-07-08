from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_evidence_refresh_sla_report import (
    ResearchResolutionEvidenceRefreshSlaConfig,
    ResearchResolutionEvidenceRefreshSlaInput,
    ResearchResolutionEvidenceRefreshSlaReasonCodeCount,
    ResearchResolutionEvidenceRefreshSlaReport,
    ResearchResolutionEvidenceRefreshSlaRow,
    build_research_resolution_evidence_refresh_sla_report,
    research_resolution_evidence_refresh_sla_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedRefreshShape:
    public_bucket_id: str
    aggregate_evidence_age_hours: Decimal
    hours_until_resolution_deadline: Decimal
    oracle_lag_hours: Decimal
    aggregate_source_reliability: Decimal
    contradiction_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionEvidenceRefreshSlaConfig:
    values = {
        "watch_aggregate_evidence_age_hours": d("12.000000"),
        "block_aggregate_evidence_age_hours": d("48.000000"),
        "watch_deadline_proximity_hours": d("24.000000"),
        "block_deadline_proximity_hours": d("2.000000"),
        "watch_oracle_lag_hours": d("6.000000"),
        "block_oracle_lag_hours": d("48.000000"),
        "watch_risk_threshold": d("0.350000"),
        "block_risk_threshold": d("0.700000"),
        "aggregate_evidence_age_weight": d("0.250000"),
        "deadline_proximity_weight": d("0.200000"),
        "oracle_lag_weight": d("0.200000"),
        "source_reliability_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchResolutionEvidenceRefreshSlaConfig(**values)


def refresh_item(
    public_bucket_id: str = "bucket-a",
    *,
    aggregate_evidence_age_hours: Decimal = d("4.000000"),
    hours_until_resolution_deadline: Decimal = d("72.000000"),
    oracle_lag_hours: Decimal = d("1.000000"),
    aggregate_source_reliability: Decimal = d("0.950000"),
    contradiction_pressure: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionEvidenceRefreshSlaInput:
    return ResearchResolutionEvidenceRefreshSlaInput(
        public_bucket_id=public_bucket_id,
        aggregate_evidence_age_hours=aggregate_evidence_age_hours,
        hours_until_resolution_deadline=hours_until_resolution_deadline,
        oracle_lag_hours=oracle_lag_hours,
        aggregate_source_reliability=aggregate_source_reliability,
        contradiction_pressure=contradiction_pressure,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionEvidenceRefreshSlaConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionEvidenceRefreshSlaReport:
    return build_research_resolution_evidence_refresh_sla_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    refresh_report = report(())

    assert type(refresh_report) is ResearchResolutionEvidenceRefreshSlaReport
    assert refresh_report.generated_at == GENERATED_AT
    assert refresh_report.config_version == "research-resolution-evidence-refresh-sla-v0"
    assert refresh_report.bucket_count == d("0")
    assert refresh_report.pass_count == d("0")
    assert refresh_report.watch_count == d("0")
    assert refresh_report.block_count == d("0")
    assert refresh_report.average_refresh_sla_risk_score is None
    assert refresh_report.average_aggregate_evidence_age_hours is None
    assert refresh_report.max_aggregate_evidence_age_hours == d("0.000000")
    assert refresh_report.min_hours_until_resolution_deadline is None
    assert refresh_report.max_oracle_lag_hours == d("0.000000")
    assert refresh_report.status == "pass"
    assert refresh_report.reason_codes == ("no_refresh_sla_items",)
    assert refresh_report.reason_code_counts == (
        ResearchResolutionEvidenceRefreshSlaReasonCodeCount(
            reason_code="no_refresh_sla_items",
            count=d("1"),
        ),
    )
    assert refresh_report.rows == ()
    assert len(refresh_report.derived_validation_digest) == 64
    assert refresh_report.paper_only is True
    assert refresh_report.report_only is True
    assert refresh_report.readonly is True


def test_risk_uses_evidence_age_deadline_oracle_lag_reliability_and_contradiction() -> None:
    refresh_report = report(
        (
            refresh_item(
                "bucket-c",
                aggregate_evidence_age_hours=d("72.000000"),
                hours_until_resolution_deadline=d("1.000000"),
                oracle_lag_hours=d("60.000000"),
                aggregate_source_reliability=d("0.350000"),
                contradiction_pressure=d("0.800000"),
                reason_codes=("manual_public_review",),
            ),
            refresh_item("bucket-a"),
            refresh_item(
                "bucket-b",
                aggregate_evidence_age_hours=d("30.000000"),
                hours_until_resolution_deadline=d("13.000000"),
                oracle_lag_hours=d("27.000000"),
                aggregate_source_reliability=d("0.750000"),
                contradiction_pressure=d("0.400000"),
            ),
        ),
    )

    assert tuple(row.public_bucket_id for row in refresh_report.rows) == (
        "bucket-a",
        "bucket-b",
        "bucket-c",
    )
    assert refresh_report.status == "block"
    assert refresh_report.bucket_count == d("3")
    assert refresh_report.pass_count == d("1")
    assert refresh_report.watch_count == d("1")
    assert refresh_report.block_count == d("1")
    assert refresh_report.average_refresh_sla_risk_score == d("0.450833")
    assert refresh_report.average_aggregate_evidence_age_hours == d("35.333333")
    assert refresh_report.max_aggregate_evidence_age_hours == d("72.000000")
    assert refresh_report.min_hours_until_resolution_deadline == d("1.000000")
    assert refresh_report.max_oracle_lag_hours == d("60.000000")

    pass_row, watch_row, block_row = refresh_report.rows
    assert type(pass_row) is ResearchResolutionEvidenceRefreshSlaRow
    assert pass_row.aggregate_evidence_age_pressure == d("0.000000")
    assert pass_row.deadline_proximity_pressure == d("0.000000")
    assert pass_row.oracle_lag_pressure == d("0.000000")
    assert pass_row.source_reliability_gap == d("0.050000")
    assert pass_row.refresh_sla_risk_score == d("0.017500")
    assert pass_row.status == "pass"
    assert watch_row.aggregate_evidence_age_pressure == d("0.500000")
    assert watch_row.deadline_proximity_pressure == d("0.500000")
    assert watch_row.oracle_lag_pressure == d("0.500000")
    assert watch_row.source_reliability_gap == d("0.250000")
    assert watch_row.refresh_sla_risk_score == d("0.435000")
    assert watch_row.status == "watch"
    assert block_row.aggregate_evidence_age_pressure == d("1.000000")
    assert block_row.deadline_proximity_pressure == d("1.000000")
    assert block_row.oracle_lag_pressure == d("1.000000")
    assert block_row.source_reliability_gap == d("0.650000")
    assert block_row.refresh_sla_risk_score == d("0.900000")
    assert block_row.status == "block"
    assert "input_manual_public_review" in block_row.reason_codes
    assert refresh_report.reason_code_counts == tuple(
        sorted(refresh_report.reason_code_counts, key=lambda item: item.reason_code),
    )
    assert {row.status for row in refresh_report.rows} == {"pass", "watch", "block"}


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedRefreshShape(
            public_bucket_id="bucket-b",
            aggregate_evidence_age_hours=d("30.000000"),
            hours_until_resolution_deadline=d("13.000000"),
            oracle_lag_hours=d("27.000000"),
            aggregate_source_reliability=d("0.750000"),
            contradiction_pressure=d("0.400000"),
            reason_codes=("manual_review",),
        ),
        refresh_item("bucket-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_evidence_refresh_sla_report_payload(
        first_report,
    )
    second_payload = research_resolution_evidence_refresh_sla_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["refresh_sla_risk_score"] == "0.017500"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "http://",
            "https://",
            "source_url",
            "source_text",
            "source_ref",
            "raw_url",
            "raw_text",
            "raw_ref",
            "market_id",
            "market_slug",
            "condition_id",
            "market_identifier",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="source_reliability_weight"):
        config(source_reliability_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_risk_threshold"):
        config(block_risk_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="block_aggregate_evidence_age_hours"):
        config(block_aggregate_evidence_age_hours=d("12.000000"))
    with pytest.raises(ValueError, match="watch_oracle_lag_hours"):
        config(watch_oracle_lag_hours=6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_proximity_weight"):
        config(deadline_proximity_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((refresh_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (refresh_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_bucket_id"):
        refresh_item(public_bucket_id="bucket url")
    with pytest.raises(ValueError, match="public_bucket_id"):
        refresh_item(public_bucket_id="market-alpha")
    with pytest.raises(ValueError, match="aggregate_evidence_age_hours"):
        refresh_item(aggregate_evidence_age_hours=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="hours_until_resolution_deadline"):
        refresh_item(hours_until_resolution_deadline=d("-1"))
    with pytest.raises(ValueError, match="aggregate_source_reliability"):
        refresh_item(aggregate_source_reliability=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        refresh_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(refresh_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    refresh_report = report((refresh_item(),))

    with pytest.raises(FrozenInstanceError):
        refresh_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        refresh_report.rows[0].refresh_sla_risk_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type("BadInput", (ResearchResolutionEvidenceRefreshSlaInput,), {})
    with pytest.raises(ValueError, match="status"):
        replace(refresh_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(refresh_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="bucket_count"):
        replace(refresh_report, bucket_count=d("2"))


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_evidence_refresh_sla_report.py"
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
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
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
