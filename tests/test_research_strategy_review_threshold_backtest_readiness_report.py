from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_review_threshold_backtest_readiness_report import (
    ResearchStrategyReviewThresholdBacktestReadinessConfig,
    ResearchStrategyReviewThresholdBacktestReadinessInput,
    ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount,
    ResearchStrategyReviewThresholdBacktestReadinessReport,
    ResearchStrategyReviewThresholdBacktestReadinessRow,
    build_research_strategy_review_threshold_backtest_readiness_report,
    research_strategy_review_threshold_backtest_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedBacktestReadinessShape:
    public_review_key: str
    evidence_coverage_score: Decimal
    cost_drag_pressure: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    calibration_sample_count: Decimal
    specialist_memory_quality_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyReviewThresholdBacktestReadinessConfig:
    values = {
        "watch_readiness_pressure_threshold": d("0.350000"),
        "block_readiness_pressure_threshold": d("0.700000"),
        "calibration_sample_target_count": d("20"),
        "evidence_coverage_weight": d("0.200000"),
        "cost_drag_weight": d("0.150000"),
        "liquidity_quality_weight": d("0.200000"),
        "resolution_clarity_weight": d("0.150000"),
        "calibration_sample_depth_weight": d("0.150000"),
        "specialist_memory_quality_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchStrategyReviewThresholdBacktestReadinessConfig(**values)


def readiness_item(
    public_review_key: str = "review-a",
    *,
    evidence_coverage_score: Decimal = d("0.950000"),
    cost_drag_pressure: Decimal = d("0.050000"),
    liquidity_quality_score: Decimal = d("0.900000"),
    resolution_clarity_score: Decimal = d("0.900000"),
    calibration_sample_count: Decimal = d("30"),
    specialist_memory_quality_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyReviewThresholdBacktestReadinessInput:
    return ResearchStrategyReviewThresholdBacktestReadinessInput(
        public_review_key=public_review_key,
        evidence_coverage_score=evidence_coverage_score,
        cost_drag_pressure=cost_drag_pressure,
        liquidity_quality_score=liquidity_quality_score,
        resolution_clarity_score=resolution_clarity_score,
        calibration_sample_count=calibration_sample_count,
        specialist_memory_quality_score=specialist_memory_quality_score,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyReviewThresholdBacktestReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyReviewThresholdBacktestReadinessReport:
    return build_research_strategy_review_threshold_backtest_readiness_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    readiness_report = report(())

    assert type(readiness_report) is ResearchStrategyReviewThresholdBacktestReadinessReport
    assert readiness_report.generated_at == GENERATED_AT
    assert (
        readiness_report.config_version
        == "research-strategy-review-threshold-backtest-readiness-v0"
    )
    assert readiness_report.review_count == d("0")
    assert readiness_report.pass_count == d("0")
    assert readiness_report.watch_count == d("0")
    assert readiness_report.block_count == d("0")
    assert readiness_report.average_backtest_readiness_pressure is None
    assert readiness_report.min_calibration_sample_count == d("0.000000")
    assert readiness_report.status == "pass"
    assert readiness_report.reason_codes == ("no_backtest_readiness_items",)
    assert readiness_report.reason_code_counts == (
        ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount(
            reason_code="no_backtest_readiness_items",
            count=d("1"),
        ),
    )
    assert readiness_report.rows == ()
    assert len(readiness_report.derived_validation_digest) == 64
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_readiness_uses_evidence_cost_liquidity_resolution_calibration_and_memory() -> None:
    readiness_report = report(
        (
            readiness_item(
                "review-c",
                evidence_coverage_score=d("0.200000"),
                cost_drag_pressure=d("0.900000"),
                liquidity_quality_score=d("0.200000"),
                resolution_clarity_score=d("0.300000"),
                calibration_sample_count=d("0"),
                specialist_memory_quality_score=d("0.200000"),
                reason_codes=("manual_review_gap",),
            ),
            readiness_item("review-a"),
            readiness_item(
                "review-b",
                evidence_coverage_score=d("0.700000"),
                cost_drag_pressure=d("0.400000"),
                liquidity_quality_score=d("0.650000"),
                resolution_clarity_score=d("0.700000"),
                calibration_sample_count=d("10"),
                specialist_memory_quality_score=d("0.700000"),
            ),
        ),
    )

    assert tuple(row.public_review_key for row in readiness_report.rows) == (
        "review-a",
        "review-b",
        "review-c",
    )
    assert readiness_report.status == "block"
    assert readiness_report.review_count == d("3")
    assert readiness_report.pass_count == d("1")
    assert readiness_report.watch_count == d("1")
    assert readiness_report.block_count == d("1")
    assert readiness_report.average_backtest_readiness_pressure == d("0.417500")
    assert readiness_report.min_calibration_sample_count == d("0")

    pass_row, watch_row, block_row = readiness_report.rows
    assert type(pass_row) is ResearchStrategyReviewThresholdBacktestReadinessRow
    assert pass_row.evidence_coverage_gap == d("0.050000")
    assert pass_row.cost_drag_pressure == d("0.050000")
    assert pass_row.liquidity_quality_gap == d("0.100000")
    assert pass_row.resolution_clarity_gap == d("0.100000")
    assert pass_row.calibration_sample_depth_score == d("1.000000")
    assert pass_row.calibration_sample_depth_gap == d("0.000000")
    assert pass_row.specialist_memory_quality_gap == d("0.100000")
    assert pass_row.backtest_readiness_pressure == d("0.067500")
    assert pass_row.status == "pass"
    assert watch_row.calibration_sample_depth_score == d("0.500000")
    assert watch_row.backtest_readiness_pressure == d("0.355000")
    assert watch_row.status == "watch"
    assert block_row.evidence_coverage_gap == d("0.800000")
    assert block_row.liquidity_quality_gap == d("0.800000")
    assert block_row.resolution_clarity_gap == d("0.700000")
    assert block_row.calibration_sample_depth_gap == d("1.000000")
    assert block_row.specialist_memory_quality_gap == d("0.800000")
    assert block_row.backtest_readiness_pressure == d("0.830000")
    assert block_row.status == "block"
    assert "input_manual_review_gap" in block_row.reason_codes
    assert readiness_report.reason_code_counts == tuple(
        sorted(readiness_report.reason_code_counts, key=lambda item: item.reason_code),
    )
    assert {row.status for row in readiness_report.rows} == {"pass", "watch", "block"}


@pytest.mark.parametrize(
    ("watch_threshold", "block_threshold", "expected_status"),
    (
        (d("0.050000"), d("0.900000"), "watch"),
        (d("0.010000"), d("0.060000"), "block"),
    ),
)
def test_configured_thresholds_control_builder_status_without_schema_changes(
    watch_threshold: Decimal,
    block_threshold: Decimal,
    expected_status: str,
) -> None:
    readiness_report = report(
        (readiness_item(),),
        cfg=config(
            watch_readiness_pressure_threshold=watch_threshold,
            block_readiness_pressure_threshold=block_threshold,
        ),
    )

    assert readiness_report.status == expected_status
    assert readiness_report.rows[0].status == expected_status
    assert (
        f"threshold_backtest_readiness_{expected_status}"
        in readiness_report.rows[0].reason_codes
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedBacktestReadinessShape(
            public_review_key="review-b",
            evidence_coverage_score=d("0.700000"),
            cost_drag_pressure=d("0.400000"),
            liquidity_quality_score=d("0.650000"),
            resolution_clarity_score=d("0.700000"),
            calibration_sample_count=d("10"),
            specialist_memory_quality_score=d("0.700000"),
            reason_codes=("manual_review",),
        ),
        readiness_item("review-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_strategy_review_threshold_backtest_readiness_report_payload(
        first_report,
    )
    second_payload = research_strategy_review_threshold_backtest_readiness_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["backtest_readiness_pressure"] == "0.067500"
    assert not any(type(value) is float for value in _walk_payload_values(first_payload))
    assert not any(type(value) is int for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "candidate_id",
            "candidate id",
            "raw_candidate",
            "market_id",
            "market_slug",
            "market_question",
            "question",
            "url",
            "http://",
            "https://",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
            "live",
            "position",
            "sizing",
            "recommendation",
        )
    )


@pytest.mark.parametrize(
    "unsafe_reason_code",
    (
        "execution_plan",
        "database_table",
        "db_connection",
        "network_route",
        "persist_path",
        "filesystem_path",
        "file_path",
        "supabase_table",
        "postgres_table",
    ),
)
def test_report_rejects_execution_and_persistence_public_leakage(
    unsafe_reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public payload"):
        report((readiness_item(reason_codes=(unsafe_reason_code,)),))


@pytest.mark.parametrize(
    "unsafe_public_review_key",
    (
        "review-db-connection",
        "review-file-path",
    ),
)
def test_report_rejects_persistence_public_review_key_leakage(
    unsafe_public_review_key: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public payload"):
        report((readiness_item(public_review_key=unsafe_public_review_key),))


def test_report_rejects_duplicate_public_review_keys() -> None:
    with pytest.raises(ValueError, match="public_review_key values must be unique"):
        report((readiness_item("review-a"), readiness_item("review-a")))


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="evidence_coverage_weight"):
        config(evidence_coverage_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_readiness_pressure_threshold"):
        config(block_readiness_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="calibration_sample_target_count"):
        config(calibration_sample_target_count=20)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_drag_weight"):
        config(cost_drag_weight=_DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((readiness_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (readiness_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_review_key"):
        readiness_item(public_review_key="candidate-alpha")
    with pytest.raises(ValueError, match="public_review_key"):
        readiness_item(public_review_key="market-alpha")
    with pytest.raises(ValueError, match="calibration_sample_count"):
        readiness_item(calibration_sample_count=d("1.5"))
    with pytest.raises(ValueError, match="liquidity_quality_score"):
        readiness_item(liquidity_quality_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_drag_pressure"):
        readiness_item(cost_drag_pressure=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        readiness_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(readiness_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    readiness_report = report((readiness_item(),))

    with pytest.raises(FrozenInstanceError):
        readiness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].backtest_readiness_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(readiness_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(readiness_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="review_count"):
        replace(readiness_report, review_count=d("2"))


def test_payload_revalidates_tampered_frozen_report_before_serializing() -> None:
    readiness_report = report((readiness_item(),))

    object.__setattr__(readiness_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_review_threshold_backtest_readiness_report_payload(
            readiness_report,
        )

    readiness_report = report((readiness_item(),))
    object.__setattr__(
        readiness_report.rows[0],
        "backtest_readiness_pressure",
        d("0.077500"),
    )
    with pytest.raises(ValueError, match="backtest_readiness_pressure"):
        research_strategy_review_threshold_backtest_readiness_report_payload(
            readiness_report,
        )

    readiness_report = report((readiness_item(),))
    object.__setattr__(readiness_report, "review_count", 1)
    with pytest.raises(ValueError, match="review_count"):
        research_strategy_review_threshold_backtest_readiness_report_payload(
            readiness_report,
        )

    readiness_report = report((readiness_item(),))
    object.__setattr__(readiness_report.rows[0], "public_review_key", "review-z")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_review_threshold_backtest_readiness_report_payload(
            readiness_report,
        )


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_review_threshold_backtest_readiness_report.py"
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
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "database",
        "network",
        "persist",
        "filesystem",
        "file_path",
        "supabase",
        "postgres",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommendation",
        "execution",
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
