from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_evidence_quality_variance_report import (
    ResearchResolutionEvidenceQualityVarianceConfig,
    ResearchResolutionEvidenceQualityVarianceInput,
    ResearchResolutionEvidenceQualityVarianceReasonCodeCount,
    ResearchResolutionEvidenceQualityVarianceReport,
    ResearchResolutionEvidenceQualityVarianceRow,
    build_research_resolution_evidence_quality_variance_report,
    research_resolution_evidence_quality_variance_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedQualityVarianceShape:
    public_bucket_id: str
    evidence_group_count: Decimal
    aggregate_source_reliability: Decimal
    aggregate_freshness: Decimal
    contradiction_pressure: Decimal
    rule_clarity: Decimal
    oracle_lag_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionEvidenceQualityVarianceConfig:
    values = {
        "oracle_lag_fresh_seconds": d("3600"),
        "oracle_lag_stale_seconds": d("86400"),
        "watch_variance_threshold": d("0.350000"),
        "block_variance_threshold": d("0.700000"),
        "source_reliability_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.250000"),
        "rule_clarity_weight": d("0.150000"),
        "oracle_lag_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchResolutionEvidenceQualityVarianceConfig(**values)


def quality_item(
    public_bucket_id: str = "bucket-a",
    *,
    evidence_group_count: Decimal = d("3"),
    aggregate_source_reliability: Decimal = d("0.950000"),
    aggregate_freshness: Decimal = d("0.900000"),
    contradiction_pressure: Decimal = d("0.050000"),
    rule_clarity: Decimal = d("0.900000"),
    oracle_lag_seconds: Decimal = d("1800"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionEvidenceQualityVarianceInput:
    return ResearchResolutionEvidenceQualityVarianceInput(
        public_bucket_id=public_bucket_id,
        evidence_group_count=evidence_group_count,
        aggregate_source_reliability=aggregate_source_reliability,
        aggregate_freshness=aggregate_freshness,
        contradiction_pressure=contradiction_pressure,
        rule_clarity=rule_clarity,
        oracle_lag_seconds=oracle_lag_seconds,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionEvidenceQualityVarianceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionEvidenceQualityVarianceReport:
    return build_research_resolution_evidence_quality_variance_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    quality_report = report(())

    assert type(quality_report) is ResearchResolutionEvidenceQualityVarianceReport
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.config_version == "research-resolution-evidence-quality-variance-v0"
    assert quality_report.bucket_count == d("0")
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.average_quality_variance_pressure is None
    assert quality_report.max_oracle_lag_seconds == d("0.000000")
    assert quality_report.status == "pass"
    assert quality_report.reason_codes == ("no_quality_variance_items",)
    assert quality_report.reason_code_counts == (
        ResearchResolutionEvidenceQualityVarianceReasonCodeCount(
            reason_code="no_quality_variance_items",
            count=d("1"),
        ),
    )
    assert quality_report.rows == ()
    assert len(quality_report.derived_validation_digest) == 64
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True


def test_variance_uses_reliability_freshness_contradiction_rule_clarity_and_oracle_lag() -> None:
    quality_report = report(
        (
            quality_item(
                "bucket-c",
                aggregate_source_reliability=d("0.400000"),
                aggregate_freshness=d("0.200000"),
                contradiction_pressure=d("0.800000"),
                rule_clarity=d("0.300000"),
                oracle_lag_seconds=d("172800"),
                reason_codes=("manual_public_review",),
            ),
            quality_item("bucket-a"),
            quality_item(
                "bucket-b",
                aggregate_source_reliability=d("0.700000"),
                aggregate_freshness=d("0.650000"),
                contradiction_pressure=d("0.350000"),
                rule_clarity=d("0.700000"),
                oracle_lag_seconds=d("43200"),
            ),
        ),
    )

    assert tuple(row.public_bucket_id for row in quality_report.rows) == (
        "bucket-a",
        "bucket-b",
        "bucket-c",
    )
    assert quality_report.status == "block"
    assert quality_report.bucket_count == d("3")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("1")
    assert quality_report.block_count == d("1")
    assert quality_report.average_quality_variance_pressure == d("0.392500")
    assert quality_report.max_oracle_lag_seconds == d("172800")

    pass_row, watch_row, block_row = quality_report.rows
    assert type(pass_row) is ResearchResolutionEvidenceQualityVarianceRow
    assert pass_row.source_reliability_gap == d("0.050000")
    assert pass_row.freshness_gap == d("0.100000")
    assert pass_row.rule_clarity_gap == d("0.100000")
    assert pass_row.oracle_lag_pressure == d("0.000000")
    assert pass_row.quality_variance_pressure == d("0.060000")
    assert pass_row.status == "pass"
    assert watch_row.oracle_lag_pressure == d("0.500000")
    assert watch_row.quality_variance_pressure == d("0.352500")
    assert watch_row.status == "watch"
    assert block_row.source_reliability_gap == d("0.600000")
    assert block_row.freshness_gap == d("0.800000")
    assert block_row.rule_clarity_gap == d("0.700000")
    assert block_row.oracle_lag_pressure == d("1.000000")
    assert block_row.quality_variance_pressure == d("0.765000")
    assert block_row.status == "block"
    assert "input_manual_public_review" in block_row.reason_codes
    assert quality_report.reason_code_counts == tuple(
        sorted(quality_report.reason_code_counts, key=lambda item: item.reason_code),
    )
    assert {row.status for row in quality_report.rows} == {"pass", "watch", "block"}


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedQualityVarianceShape(
            public_bucket_id="bucket-b",
            evidence_group_count=d("2"),
            aggregate_source_reliability=d("0.700000"),
            aggregate_freshness=d("0.650000"),
            contradiction_pressure=d("0.350000"),
            rule_clarity=d("0.700000"),
            oracle_lag_seconds=d("43200"),
            reason_codes=("manual_review",),
        ),
        quality_item("bucket-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_evidence_quality_variance_report_payload(
        first_report,
    )
    second_payload = research_resolution_evidence_quality_variance_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["quality_variance_pressure"] == "0.060000"
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
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="source_reliability_weight"):
        config(source_reliability_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_variance_threshold"):
        config(block_variance_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="oracle_lag_fresh_seconds"):
        config(oracle_lag_fresh_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_weight"):
        config(freshness_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((quality_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (quality_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_bucket_id"):
        quality_item(public_bucket_id="bucket url")
    with pytest.raises(ValueError, match="public_bucket_id"):
        quality_item(public_bucket_id="market-alpha")
    with pytest.raises(ValueError, match="evidence_group_count"):
        quality_item(evidence_group_count=d("1.5"))
    with pytest.raises(ValueError, match="aggregate_freshness"):
        quality_item(aggregate_freshness=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_lag_seconds"):
        quality_item(oracle_lag_seconds=d("-1"))
    with pytest.raises(ValueError, match="reason_codes"):
        quality_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(quality_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    quality_report = report((quality_item(),))

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].quality_variance_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(quality_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="bucket_count"):
        replace(quality_report, bucket_count=d("2"))


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_evidence_quality_variance_report.py"
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
