from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_domain_calibration_benchmark_report import (
    DEFAULT_DOMAIN_IDS,
    ResearchDomainCalibrationBenchmarkConfig,
    ResearchDomainCalibrationBenchmarkReasonCodeCount,
    ResearchDomainCalibrationBenchmarkReport,
    ResearchDomainCalibrationBenchmarkRow,
    ResearchDomainCalibrationBenchmarkSource,
    build_research_domain_calibration_benchmark_report,
    research_domain_calibration_benchmark_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDomainCalibrationBenchmarkConfig:
    values = {
        "config_version": "research-domain-calibration-benchmark-report-v0",
        "domain_ids": DEFAULT_DOMAIN_IDS,
        "pass_min_sample_size": d("3"),
        "watch_min_sample_size": d("2"),
        "pass_max_historical_error": d("0.050000"),
        "watch_max_historical_error": d("0.120000"),
        "pass_min_postmortem_quality": d("0.850000"),
        "watch_min_postmortem_quality": d("0.600000"),
        "confidence_interval_z_score": d("1.960000"),
    }
    values.update(overrides)
    return ResearchDomainCalibrationBenchmarkConfig(**values)


def source(
    index: int,
    *,
    domain_id: str = "btc",
    forecast_probability: str = "0.600000",
    resolved_outcome: str = "1.000000",
    postmortem_quality_score: str = "0.900000",
    resolved_at: datetime | None = None,
    reviewed_at: datetime | None = None,
) -> ResearchDomainCalibrationBenchmarkSource:
    return ResearchDomainCalibrationBenchmarkSource(
        domain_id=domain_id,
        forecast_id=f"{domain_id}-forecast-{index:03d}",
        forecast_probability=d(forecast_probability),
        resolved_outcome=d(resolved_outcome),
        postmortem_quality_score=d(postmortem_quality_score),
        resolved_at=resolved_at or GENERATED_AT - timedelta(days=1),
        reviewed_at=reviewed_at or GENERATED_AT - timedelta(hours=2),
    )


def report(
    rows: tuple[ResearchDomainCalibrationBenchmarkSource, ...],
    *,
    cfg: ResearchDomainCalibrationBenchmarkConfig | None = None,
) -> ResearchDomainCalibrationBenchmarkReport:
    return build_research_domain_calibration_benchmark_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_default_domains_without_sources_block_as_report_only_benchmark() -> None:
    benchmark_report = report(())

    assert type(benchmark_report) is ResearchDomainCalibrationBenchmarkReport
    assert benchmark_report.generated_at == GENERATED_AT
    assert benchmark_report.config_version == (
        "research-domain-calibration-benchmark-report-v0"
    )
    assert benchmark_report.domain_count == d("6.000000")
    assert benchmark_report.source_count == d("0.000000")
    assert benchmark_report.pass_count == d("0.000000")
    assert benchmark_report.watch_count == d("0.000000")
    assert benchmark_report.block_count == d("6.000000")
    assert benchmark_report.status == "block"
    assert benchmark_report.reason_codes == (
        "research_domain_calibration_benchmark_no_resolved_samples",
    )
    assert tuple(row.domain_id for row in benchmark_report.rows) == DEFAULT_DOMAIN_IDS
    assert all(row.status == "block" for row in benchmark_report.rows)
    assert all(row.sample_size == d("0.000000") for row in benchmark_report.rows)
    assert benchmark_report.paper_only is True
    assert benchmark_report.report_only is True
    assert benchmark_report.readonly is True


def test_six_domain_benchmark_outputs_pass_watch_and_block_rows() -> None:
    cfg = config()
    benchmark_report = report(
        (
            source(1, domain_id="basketball", forecast_probability="0.600000"),
            source(
                2,
                domain_id="basketball",
                forecast_probability="0.600000",
                resolved_outcome="0.000000",
            ),
            source(1, domain_id="btc", forecast_probability="1.000000"),
            source(2, domain_id="btc", forecast_probability="1.000000"),
            source(3, domain_id="btc", forecast_probability="1.000000"),
            source(
                1,
                domain_id="football",
                forecast_probability="1.000000",
                postmortem_quality_score="0.500000",
            ),
            source(
                2,
                domain_id="football",
                forecast_probability="1.000000",
                postmortem_quality_score="0.500000",
            ),
            source(1, domain_id="gold", forecast_probability="0.666667"),
            source(2, domain_id="gold", forecast_probability="0.666667"),
            source(
                3,
                domain_id="gold",
                forecast_probability="0.666666",
                resolved_outcome="0.000000",
            ),
            source(1, domain_id="politics", forecast_probability="0.650000"),
            source(2, domain_id="politics", forecast_probability="0.650000"),
            source(
                3,
                domain_id="politics",
                forecast_probability="0.650000",
                resolved_outcome="0.000000",
            ),
            source(1, domain_id="stock_index", forecast_probability="0.500000"),
            source(2, domain_id="stock_index", forecast_probability="0.500000"),
            source(3, domain_id="stock_index", forecast_probability="0.500000"),
        ),
        cfg=cfg,
    )

    assert benchmark_report.status == "block"
    assert benchmark_report.domain_count == d("6.000000")
    assert benchmark_report.source_count == d("16.000000")
    assert benchmark_report.pass_count == d("3.000000")
    assert benchmark_report.watch_count == d("1.000000")
    assert benchmark_report.block_count == d("2.000000")

    by_domain = {row.domain_id: row for row in benchmark_report.rows}
    assert by_domain["btc"].status == "pass"
    assert by_domain["btc"].sample_size == d("3.000000")
    assert by_domain["btc"].average_forecast_probability == d("1.000000")
    assert by_domain["btc"].observed_probability == d("1.000000")
    assert by_domain["btc"].historical_error == d("0.000000")
    assert by_domain["btc"].mean_brier_score == d("0.000000")
    assert by_domain["btc"].postmortem_quality_score == d("0.900000")
    assert by_domain["btc"].confidence_interval_lower == d("1.000000")
    assert by_domain["btc"].confidence_interval_upper == d("1.000000")
    assert by_domain["btc"].confidence_interval_width == d("0.000000")
    assert by_domain["btc"].reason_codes == (
        "research_domain_calibration_benchmark_pass",
    )

    assert by_domain["basketball"].status == "watch"
    assert by_domain["basketball"].sample_size == d("2.000000")
    assert by_domain["basketball"].average_forecast_probability == d("0.600000")
    assert by_domain["basketball"].observed_probability == d("0.500000")
    assert by_domain["basketball"].historical_error == d("0.100000")
    assert by_domain["basketball"].reason_codes == (
        "research_domain_calibration_benchmark_sample_size_watch",
        "research_domain_calibration_benchmark_historical_error_watch",
    )

    assert by_domain["football"].status == "block"
    assert by_domain["football"].postmortem_quality_score == d("0.500000")
    assert by_domain["football"].reason_codes == (
        "research_domain_calibration_benchmark_postmortem_quality_block",
        "research_domain_calibration_benchmark_sample_size_watch",
    )
    assert by_domain["gold"].status == "pass"
    assert by_domain["politics"].status == "pass"
    assert by_domain["stock_index"].status == "block"
    assert by_domain["stock_index"].reason_codes == (
        "research_domain_calibration_benchmark_historical_error_block",
        "research_domain_calibration_benchmark_forecast_outside_confidence_interval",
    )


def test_payload_is_json_ready_decimal_only_and_public_safe() -> None:
    benchmark_report = report(
        (
            source(3, domain_id="btc", forecast_probability="1.000000"),
            source(1, domain_id="btc", forecast_probability="1.000000"),
            source(2, domain_id="btc", forecast_probability="1.000000"),
        ),
        cfg=config(domain_ids=("btc",)),
    )

    payload = research_domain_calibration_benchmark_report_payload(benchmark_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["source_count"] == "3.000000"
    assert payload["rows"][0]["forecast_ids"] == [
        "btc-forecast-001",
        "btc-forecast-002",
        "btc-forecast-003",
    ]
    assert payload["rows"][0]["historical_error"] == "0.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded

    with pytest.raises(ValueError, match="unsafe public value"):
        research_domain_calibration_benchmark_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "token": "abc"},
        )


def test_validation_rejects_bad_types_future_times_flags_and_inconsistent_rows() -> None:
    with pytest.raises(ValueError, match="domain_ids"):
        config(domain_ids=("btc", "basketball"))
    with pytest.raises(ValueError, match="pass_min_sample_size"):
        config(pass_min_sample_size=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_max_historical_error"):
        config(watch_max_historical_error=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_domain_calibration_benchmark_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_domain_calibration_benchmark_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="forecast_probability"):
        source(1, forecast_probability="1.100000")
    with pytest.raises(ValueError, match="forecast_probability"):
        replace(source(1), forecast_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="resolved_outcome"):
        source(1, resolved_outcome="0.500000")
    with pytest.raises(ValueError, match="reviewed_at"):
        source(1, reviewed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="resolved_at"):
        report((source(1, resolved_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="domain_id"):
        report((source(1, domain_id="tennis"),))
    with pytest.raises(ValueError, match="forecast_id values must be unique"):
        report((source(1, domain_id="btc"), source(1, domain_id="btc")))
    with pytest.raises(ValueError, match="paper_only"):
        replace(source(1), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report((source(1),), cfg=config(domain_ids=("btc",))).rows[0], status="hold")


def test_public_dataclasses_are_frozen_and_manual_consistency_is_checked() -> None:
    benchmark_report = report(
        (
            source(1, domain_id="btc", forecast_probability="1.000000"),
            source(2, domain_id="btc", forecast_probability="1.000000"),
            source(3, domain_id="btc", forecast_probability="1.000000"),
        ),
        cfg=config(domain_ids=("btc",)),
    )

    with pytest.raises(FrozenInstanceError):
        benchmark_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        benchmark_report.rows[0].historical_error = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="confidence_interval_width"):
        replace(benchmark_report.rows[0], confidence_interval_width=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(benchmark_report, status="block")
    with pytest.raises(ValueError, match="count"):
        ResearchDomainCalibrationBenchmarkReasonCodeCount(
            reason_code="research_domain_calibration_benchmark_pass",
            count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="sample_size"):
        ResearchDomainCalibrationBenchmarkRow(
            domain_id="btc",
            sample_size=d("2.000000"),
            average_forecast_probability=d("1.000000"),
            observed_probability=d("1.000000"),
            historical_error=d("0.000000"),
            mean_brier_score=d("0.000000"),
            postmortem_quality_score=d("0.900000"),
            confidence_interval_lower=d("1.000000"),
            confidence_interval_upper=d("1.000000"),
            confidence_interval_width=d("0.000000"),
            status="pass",
            forecast_ids=("forecast-001",),
            reason_codes=("research_domain_calibration_benchmark_pass",),
        )


def test_owned_module_has_no_network_filesystem_or_action_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_domain_calibration_benchmark_report.py"
    )
    source_text = module_path.read_text(encoding="utf-8").lower()
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
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "order",
        "position",
        "buy",
        "sell",
        "investment_advice",
    )

    assert all(term not in source_text for term in forbidden_terms)


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
