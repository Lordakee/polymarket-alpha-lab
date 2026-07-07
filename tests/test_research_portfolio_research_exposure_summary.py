from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_portfolio_research_exposure_summary import (
    DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION,
    ResearchPortfolioResearchExposureBucket,
    ResearchPortfolioResearchExposureInputRow,
    ResearchPortfolioResearchExposurePublicPayloadItem,
    ResearchPortfolioResearchExposureReasonCodeCount,
    ResearchPortfolioResearchExposureSummaryConfig,
    ResearchPortfolioResearchExposureSummaryReport,
    build_research_portfolio_research_exposure_summary,
    research_portfolio_research_exposure_summary_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def research_row(
    index: int,
    *,
    domain: str = "politics",
    settlement_window: str = "2026-08",
    source_dependency_keys: tuple[str, ...] = ("official-results",),
    model_dependency_keys: tuple[str, ...] = ("calibration-v1",),
) -> ResearchPortfolioResearchExposureInputRow:
    return ResearchPortfolioResearchExposureInputRow(
        research_item_id=f"research-{index:03d}",
        domain=domain,
        settlement_window=settlement_window,
        source_dependency_keys=source_dependency_keys,
        model_dependency_keys=model_dependency_keys,
    )


def report(
    rows: tuple[ResearchPortfolioResearchExposureInputRow, ...],
    *,
    config: ResearchPortfolioResearchExposureSummaryConfig | None = None,
    public_payload: tuple[ResearchPortfolioResearchExposurePublicPayloadItem, ...] = (),
    generated_at: datetime = GENERATED_AT,
) -> ResearchPortfolioResearchExposureSummaryReport:
    return build_research_portfolio_research_exposure_summary(
        rows,
        config=config,
        generated_at=generated_at,
        public_payload=public_payload,
    )


def test_empty_research_queue_returns_blocked_zero_exposure_report() -> None:
    exposure_report = report(())

    assert type(exposure_report) is ResearchPortfolioResearchExposureSummaryReport
    assert exposure_report.generated_at == GENERATED_AT
    assert (
        exposure_report.config_version
        == DEFAULT_RESEARCH_PORTFOLIO_RESEARCH_EXPOSURE_SUMMARY_CONFIG_VERSION
    )
    assert exposure_report.research_item_count == d("0.000000")
    assert exposure_report.domain_count == d("0.000000")
    assert exposure_report.settlement_window_count == d("0.000000")
    assert exposure_report.source_dependency_count == d("0.000000")
    assert exposure_report.model_dependency_count == d("0.000000")
    assert exposure_report.pass_count == d("0.000000")
    assert exposure_report.watch_count == d("0.000000")
    assert exposure_report.blocked_count == d("0.000000")
    assert exposure_report.max_domain_share == d("0.000000")
    assert exposure_report.max_settlement_window_share == d("0.000000")
    assert exposure_report.max_source_dependency_share == d("0.000000")
    assert exposure_report.max_model_dependency_share == d("0.000000")
    assert exposure_report.status == "blocked"
    assert exposure_report.reason_codes == ("no_research_queue_items",)
    assert exposure_report.reason_code_counts == (
        ResearchPortfolioResearchExposureReasonCodeCount(
            reason_code="no_research_queue_items",
            count=d("1.000000"),
        ),
    )
    assert exposure_report.rows == ()
    assert exposure_report.paper_only is True
    assert exposure_report.report_only is True
    assert exposure_report.readonly is True


def test_balanced_research_queue_exposure_passes_with_deterministic_buckets() -> None:
    exposure_report = report(
        (
            research_row(
                4,
                domain="weather",
                settlement_window="2026-11",
                source_dependency_keys=("satellite-data",),
                model_dependency_keys=("scenario-model",),
            ),
            research_row(
                2,
                domain="economics",
                settlement_window="2026-09",
                source_dependency_keys=("survey-panel",),
                model_dependency_keys=("calibration-v1", "text-ranker"),
            ),
            research_row(
                1,
                domain="politics",
                settlement_window="2026-08",
                source_dependency_keys=("official-results", "venue-feed"),
                model_dependency_keys=("calibration-v1",),
            ),
            research_row(
                3,
                domain="sports",
                settlement_window="2026-10",
                source_dependency_keys=("odds-feed",),
                model_dependency_keys=("text-ranker",),
            ),
        ),
    )

    assert exposure_report.status == "pass"
    assert exposure_report.research_item_count == d("4.000000")
    assert exposure_report.domain_count == d("4.000000")
    assert exposure_report.settlement_window_count == d("4.000000")
    assert exposure_report.source_dependency_count == d("5.000000")
    assert exposure_report.model_dependency_count == d("3.000000")
    assert exposure_report.pass_count == d("16.000000")
    assert exposure_report.watch_count == d("0.000000")
    assert exposure_report.blocked_count == d("0.000000")
    assert exposure_report.max_domain_share == d("0.250000")
    assert exposure_report.max_settlement_window_share == d("0.250000")
    assert exposure_report.max_source_dependency_share == d("0.250000")
    assert exposure_report.max_model_dependency_share == d("0.500000")
    assert exposure_report.reason_codes == ("research_exposure_summary_pass",)

    assert tuple(
        (
            row.exposure_dimension,
            row.exposure_key,
            row.research_item_count,
            row.exposure_share,
            row.status,
            row.reason_codes,
        )
        for row in exposure_report.rows
    ) == (
        (
            "domain",
            "economics",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("domain_exposure_pass",),
        ),
        (
            "domain",
            "politics",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("domain_exposure_pass",),
        ),
        (
            "domain",
            "sports",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("domain_exposure_pass",),
        ),
        (
            "domain",
            "weather",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("domain_exposure_pass",),
        ),
        (
            "model_dependency",
            "calibration-v1",
            d("2.000000"),
            d("0.500000"),
            "pass",
            ("model_dependency_exposure_pass",),
        ),
        (
            "model_dependency",
            "scenario-model",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("model_dependency_exposure_pass",),
        ),
        (
            "model_dependency",
            "text-ranker",
            d("2.000000"),
            d("0.500000"),
            "pass",
            ("model_dependency_exposure_pass",),
        ),
        (
            "settlement_window",
            "2026-08",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("settlement_window_exposure_pass",),
        ),
        (
            "settlement_window",
            "2026-09",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("settlement_window_exposure_pass",),
        ),
        (
            "settlement_window",
            "2026-10",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("settlement_window_exposure_pass",),
        ),
        (
            "settlement_window",
            "2026-11",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("settlement_window_exposure_pass",),
        ),
        (
            "source_dependency",
            "odds-feed",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("source_dependency_exposure_pass",),
        ),
        (
            "source_dependency",
            "official-results",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("source_dependency_exposure_pass",),
        ),
        (
            "source_dependency",
            "satellite-data",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("source_dependency_exposure_pass",),
        ),
        (
            "source_dependency",
            "survey-panel",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("source_dependency_exposure_pass",),
        ),
        (
            "source_dependency",
            "venue-feed",
            d("1.000000"),
            d("0.250000"),
            "pass",
            ("source_dependency_exposure_pass",),
        ),
    )


def test_concentrated_research_queue_exposure_yields_watch_and_block() -> None:
    watch_report = report(
        (
            research_row(1, domain="politics", settlement_window="2026-08"),
            research_row(2, domain="politics", settlement_window="2026-09"),
            research_row(3, domain="economics", settlement_window="2026-10"),
            research_row(4, domain="sports", settlement_window="2026-11"),
        ),
        config=ResearchPortfolioResearchExposureSummaryConfig(
            watch_domain_share=d("0.490000"),
            block_domain_share=d("0.750000"),
            block_source_dependency_share=d("1.000000"),
            block_model_dependency_share=d("1.000000"),
        ),
    )
    blocked_report = report(
        (
            research_row(1, domain="politics", settlement_window="2026-08"),
            research_row(2, domain="politics", settlement_window="2026-09"),
            research_row(3, domain="politics", settlement_window="2026-10"),
            research_row(4, domain="sports", settlement_window="2026-11"),
        ),
        config=ResearchPortfolioResearchExposureSummaryConfig(
            block_source_dependency_share=d("1.000000"),
            block_model_dependency_share=d("1.000000"),
        ),
    )

    assert watch_report.status == "watch"
    assert any(
        row.exposure_dimension == "domain"
        and row.exposure_key == "politics"
        and row.exposure_share == d("0.500000")
        and row.status == "watch"
        for row in watch_report.rows
    )
    assert "domain_exposure_watch" in watch_report.reason_codes
    assert "research_exposure_summary_watch" in watch_report.reason_codes

    assert blocked_report.status == "blocked"
    assert any(
        row.exposure_dimension == "domain"
        and row.exposure_key == "politics"
        and row.exposure_share == d("0.750000")
        and row.status == "blocked"
        for row in blocked_report.rows
    )
    assert "domain_exposure_blocked" in blocked_report.reason_codes
    assert "research_exposure_summary_blocked" in blocked_report.reason_codes


def test_missing_dependency_keys_are_blocked_without_other_inputs() -> None:
    exposure_report = report(
        (
            research_row(
                1,
                source_dependency_keys=(),
                model_dependency_keys=(),
            ),
        ),
    )

    assert exposure_report.status == "blocked"
    assert exposure_report.blocked_count == d("4.000000")
    assert any(
        row.exposure_dimension == "source_dependency"
        and row.exposure_key == "unmapped_source_dependency"
        and row.status == "blocked"
        and row.reason_codes
        == ("source_dependency_exposure_blocked", "missing_source_dependency")
        for row in exposure_report.rows
    )
    assert any(
        row.exposure_dimension == "model_dependency"
        and row.exposure_key == "unmapped_model_dependency"
        and row.status == "blocked"
        and row.reason_codes
        == ("model_dependency_exposure_blocked", "missing_model_dependency")
        for row in exposure_report.rows
    )


def test_payload_is_public_safe_deterministic_and_decimal_only() -> None:
    exposure_report = report(
        (research_row(1),),
        public_payload=(
            ResearchPortfolioResearchExposurePublicPayloadItem(
                key="run_label",
                value="research exposure dry run",
            ),
        ),
    )
    payload = research_portfolio_research_exposure_summary_payload(exposure_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == exposure_report.payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["research_item_count"] == "1.000000"
    assert payload["rows"][0]["exposure_share"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 1.0" not in encoded

    with pytest.raises(ValueError, match="unsafe public value"):
        ResearchPortfolioResearchExposurePublicPayloadItem(
            key="unsafe_value",
            value="please " + "b" + "uy",
        )


def test_validation_rejects_bad_types_subclasses_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_domain_share"):
        ResearchPortfolioResearchExposureSummaryConfig(
            watch_domain_share=0.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="block share"):
        ResearchPortfolioResearchExposureSummaryConfig(
            watch_domain_share=d("0.700000"),
            block_domain_share=d("0.600000"),
        )
    with pytest.raises(ValueError, match="block_domain_share"):
        ResearchPortfolioResearchExposureSummaryConfig(
            block_domain_share=_DecimalSubclass("0.666667"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((research_row(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (research_row(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_item_id"):
        research_row(1, domain="politics").__class__(
            research_item_id=" bad-id",
            domain="politics",
            settlement_window="2026-08",
            source_dependency_keys=("official-results",),
            model_dependency_keys=("calibration-v1",),
        )
    with pytest.raises(ValueError, match="source_dependency_keys"):
        ResearchPortfolioResearchExposureInputRow(
            research_item_id="research-001",
            domain="politics",
            settlement_window="2026-08",
            source_dependency_keys=["official-results"],  # type: ignore[arg-type]
            model_dependency_keys=("calibration-v1",),
        )
    with pytest.raises(ValueError, match="research_item_id"):
        report((research_row(1), research_row(1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(research_row(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_consistency_is_enforced() -> None:
    exposure_report = report((research_row(1), research_row(2, domain="sports")))

    with pytest.raises(FrozenInstanceError):
        exposure_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        exposure_report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="bucket status reason"):
        replace(exposure_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(exposure_report, status="pass")
    with pytest.raises(ValueError, match="exposure_share"):
        replace(
            exposure_report,
            rows=(
                replace(exposure_report.rows[0], exposure_share=d("0.100000")),
                *exposure_report.rows[1:],
            ),
        )


def test_owned_module_has_no_io_execution_or_unrequested_business_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_portfolio_research_exposure_summary.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "pathlib",
        "open(",
        "connect(",
        "write(",
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
