from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_calibration_sample_quality_report import (
    ResearchCalibrationSampleQualityConfig,
    ResearchCalibrationSampleQualityDomainInput,
    ResearchCalibrationSampleQualityReasonCodeCount,
    ResearchCalibrationSampleQualityReport,
    ResearchCalibrationSampleQualityRow,
    build_research_calibration_sample_quality_report,
    research_calibration_sample_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCalibrationSampleQualityConfig:
    values = {
        "config_version": "research-calibration-sample-quality-v0",
        "min_pass_sample_count": d("100"),
        "min_watch_sample_count": d("50"),
        "min_pass_domain_count": d("3"),
        "min_watch_domain_count": d("2"),
        "min_pass_settlement_label_completeness": d("0.950000"),
        "min_watch_settlement_label_completeness": d("0.800000"),
        "max_pass_bias_delta": d("0.050000"),
        "max_watch_bias_delta": d("0.100000"),
        "min_pass_review_quality_score": d("0.900000"),
        "min_watch_review_quality_score": d("0.700000"),
        "pass_quality_score": d("0.800000"),
        "watch_quality_score": d("0.600000"),
        "sample_size_weight": d("0.200000"),
        "domain_coverage_weight": d("0.200000"),
        "settlement_label_weight": d("0.200000"),
        "bias_stability_weight": d("0.200000"),
        "review_quality_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchCalibrationSampleQualityConfig(**values)


def domain_input(
    domain: str,
    *,
    sample_count: str,
    settled_label_count: str,
    positive_label_count: str,
    current_bias: str,
    previous_bias: str | None,
    reviewed_count: str,
    high_quality_review_count: str,
    reason_codes: tuple[str, ...] = (),
) -> ResearchCalibrationSampleQualityDomainInput:
    return ResearchCalibrationSampleQualityDomainInput(
        domain=domain,
        sample_count=d(sample_count),
        settled_label_count=d(settled_label_count),
        positive_label_count=d(positive_label_count),
        current_bias=d(current_bias),
        previous_bias=None if previous_bias is None else d(previous_bias),
        reviewed_count=d(reviewed_count),
        high_quality_review_count=d(high_quality_review_count),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchCalibrationSampleQualityConfig | None = None,
) -> ResearchCalibrationSampleQualityReport:
    return build_research_calibration_sample_quality_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_pass_report_scores_all_sample_quality_dimensions_without_raw_rows() -> None:
    quality_report = report(
        (
            domain_input(
                "crypto",
                sample_count="40",
                settled_label_count="40",
                positive_label_count="18",
                current_bias="0.020000",
                previous_bias="0.010000",
                reviewed_count="40",
                high_quality_review_count="38",
                reason_codes=("manual_reviewed",),
            ),
            domain_input(
                "macro",
                sample_count="40",
                settled_label_count="40",
                positive_label_count="22",
                current_bias="-0.010000",
                previous_bias="-0.020000",
                reviewed_count="40",
                high_quality_review_count="38",
            ),
            domain_input(
                "sports",
                sample_count="40",
                settled_label_count="40",
                positive_label_count="20",
                current_bias="0.030000",
                previous_bias="0.000000",
                reviewed_count="40",
                high_quality_review_count="38",
            ),
        ),
    )

    assert type(quality_report) is ResearchCalibrationSampleQualityReport
    assert quality_report.status == "pass"
    assert quality_report.sample_count == d("120")
    assert quality_report.domain_count == d("3")
    assert quality_report.settled_label_count == d("120")
    assert quality_report.missing_label_count == d("0")
    assert quality_report.reviewed_count == d("120")
    assert quality_report.pass_count == d("3")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.sample_size_score == d("1.000000")
    assert quality_report.domain_coverage_score == d("1.000000")
    assert quality_report.settlement_label_completeness_score == d("1.000000")
    assert quality_report.bias_stability_score == d("0.833333")
    assert quality_report.review_quality_score == d("0.950000")
    assert quality_report.quality_score == d("0.956667")
    assert quality_report.reason_codes == ("calibration_sample_quality_pass",)
    assert quality_report.reason_code_counts == (
        ResearchCalibrationSampleQualityReasonCodeCount(
            reason_code="calibration_sample_quality_pass",
            count=d("1"),
        ),
    )

    assert tuple(row.domain for row in quality_report.rows) == (
        "crypto",
        "macro",
        "sports",
    )
    row = quality_report.rows[0]
    assert type(row) is ResearchCalibrationSampleQualityRow
    assert row.domain == "crypto"
    assert row.sample_count == d("40")
    assert row.missing_label_count == d("0")
    assert row.settlement_label_completeness_score == d("1.000000")
    assert row.bias_stability_delta == d("0.010000")
    assert row.bias_stability_score == d("0.900000")
    assert row.review_quality_score == d("0.950000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "input_manual_reviewed",
        "sample_quality_pass",
    )


def test_watch_and_block_statuses_reflect_threshold_severity() -> None:
    watch_report = report(
        (
            domain_input(
                "crypto",
                sample_count="30",
                settled_label_count="25",
                positive_label_count="12",
                current_bias="0.070000",
                previous_bias="0.000000",
                reviewed_count="30",
                high_quality_review_count="23",
            ),
            domain_input(
                "macro",
                sample_count="30",
                settled_label_count="25",
                positive_label_count="12",
                current_bias="-0.070000",
                previous_bias="-0.010000",
                reviewed_count="30",
                high_quality_review_count="22",
            ),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.sample_count == d("60")
    assert watch_report.domain_count == d("2")
    assert watch_report.watch_count == d("2")
    assert watch_report.reason_codes == (
        "bias_stability_watch",
        "calibration_sample_quality_watch",
        "domain_coverage_watch",
        "review_quality_watch",
        "sample_size_watch",
        "settlement_label_completeness_watch",
    )

    block_report = report(
        (
            domain_input(
                "macro",
                sample_count="20",
                settled_label_count="10",
                positive_label_count="4",
                current_bias="0.200000",
                previous_bias="0.000000",
                reviewed_count="20",
                high_quality_review_count="5",
            ),
        ),
    )

    assert block_report.status == "block"
    assert block_report.block_count == d("1")
    assert block_report.reason_codes == (
        "bias_stability_block",
        "calibration_sample_quality_block",
        "domain_coverage_block",
        "review_quality_block",
        "sample_size_block",
        "settlement_label_completeness_block",
    )


def test_payload_is_decimal_string_only_and_omits_sensitive_public_surface() -> None:
    quality_report = report(
        (
            domain_input(
                "crypto",
                sample_count="60",
                settled_label_count="60",
                positive_label_count="30",
                current_bias="0.010000",
                previous_bias="0.000000",
                reviewed_count="60",
                high_quality_review_count="58",
            ),
            domain_input(
                "macro",
                sample_count="60",
                settled_label_count="60",
                positive_label_count="29",
                current_bias="-0.010000",
                previous_bias="0.000000",
                reviewed_count="60",
                high_quality_review_count="58",
            ),
            domain_input(
                "sports",
                sample_count="60",
                settled_label_count="60",
                positive_label_count="31",
                current_bias="0.000000",
                previous_bias="0.000000",
                reviewed_count="60",
                high_quality_review_count="58",
            ),
        ),
    )

    payload = research_calibration_sample_quality_report_payload(quality_report)
    encoded = json.dumps(payload, sort_keys=True)
    lowered = encoded.lower()

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["sample_count"] == "180"
    assert payload["rows"][0]["current_bias"] == "0.010000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert all(
        forbidden not in lowered
        for forbidden in (
            "candidate",
            "market",
            "source",
            "url",
            "dsn",
            "table",
            "token",
            "buy",
            "sell",
        )
    )


def test_validation_rejects_bad_types_counts_consistency_and_public_unsafe_text() -> None:
    with pytest.raises(ValueError, match="min_pass_sample_count"):
        config(min_pass_sample_count=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_bias_delta"):
        config(max_watch_bias_delta=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_calibration_sample_quality_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_calibration_sample_quality_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="domain"):
        domain_input(
            "raw market slug",
            sample_count="10",
            settled_label_count="10",
            positive_label_count="5",
            current_bias="0.000000",
            previous_bias="0.000000",
            reviewed_count="10",
            high_quality_review_count="10",
        )
    with pytest.raises(ValueError, match="sample_count"):
        domain_input(
            "macro",
            sample_count="10.5",
            settled_label_count="10",
            positive_label_count="5",
            current_bias="0.000000",
            previous_bias="0.000000",
            reviewed_count="10",
            high_quality_review_count="10",
        )
    with pytest.raises(ValueError, match="settled_label_count"):
        domain_input(
            "macro",
            sample_count="10",
            settled_label_count="11",
            positive_label_count="5",
            current_bias="0.000000",
            previous_bias="0.000000",
            reviewed_count="10",
            high_quality_review_count="10",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            domain_input(
                "macro",
                sample_count="10",
                settled_label_count="10",
                positive_label_count="5",
                current_bias="0.000000",
                previous_bias="0.000000",
                reviewed_count="10",
                high_quality_review_count="10",
            ),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    quality_report = report(
        (
            domain_input(
                "macro",
                sample_count="100",
                settled_label_count="100",
                positive_label_count="50",
                current_bias="0.010000",
                previous_bias="0.000000",
                reviewed_count="100",
                high_quality_review_count="95",
            ),
            domain_input(
                "sports",
                sample_count="100",
                settled_label_count="100",
                positive_label_count="50",
                current_bias="0.010000",
                previous_bias="0.000000",
                reviewed_count="100",
                high_quality_review_count="95",
            ),
            domain_input(
                "crypto",
                sample_count="100",
                settled_label_count="100",
                positive_label_count="50",
                current_bias="0.010000",
                previous_bias="0.000000",
                reviewed_count="100",
                high_quality_review_count="95",
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].sample_count = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="quality_score"):
        replace(quality_report.rows[0], quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(quality_report, status="block")


def test_owned_module_has_no_network_filesystem_db_or_trading_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_calibration_sample_quality_report.py"
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
        "insert ",
        "update ",
        "delete ",
        "buy ",
        "sell ",
        "trade ",
        "position ",
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
