from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_expected_value_input_quality_report import (
    ResearchStrategyExpectedValueInput,
    ResearchStrategyExpectedValueInputQualityConfig,
    ResearchStrategyExpectedValueInputQualityReasonCodeCount,
    ResearchStrategyExpectedValueInputQualityReport,
    ResearchStrategyExpectedValueInputQualityRow,
    build_research_strategy_expected_value_input_quality_report,
    research_strategy_expected_value_input_quality_report_digest,
    research_strategy_expected_value_input_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyExpectedValueInputQualityConfig:
    values = {
        "config_version": "research-strategy-expected-value-input-quality-report-v0",
        "pass_component_quality": d("0.700000"),
        "watch_component_quality": d("0.400000"),
        "pass_quality_score": d("0.750000"),
        "watch_quality_score": d("0.500000"),
        "forecast_confidence_weight": d("0.200000"),
        "cost_estimate_quality_weight": d("0.200000"),
        "liquidity_quality_weight": d("0.200000"),
        "resolution_clarity_weight": d("0.200000"),
        "evidence_freshness_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategyExpectedValueInputQualityConfig(**values)


def input_row(
    research_key: str,
    *,
    evidence_set_label: str = "packet-alpha",
    forecast_confidence: Decimal = d("0.820000"),
    cost_estimate_quality: Decimal = d("0.880000"),
    liquidity_quality: Decimal = d("0.760000"),
    resolution_clarity: Decimal = d("0.900000"),
    evidence_freshness: Decimal = d("0.840000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyExpectedValueInput:
    return ResearchStrategyExpectedValueInput(
        research_key=research_key,
        evidence_set_label=evidence_set_label,
        forecast_confidence=forecast_confidence,
        cost_estimate_quality=cost_estimate_quality,
        liquidity_quality=liquidity_quality,
        resolution_clarity=resolution_clarity,
        evidence_freshness=evidence_freshness,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyExpectedValueInputQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyExpectedValueInputQualityReport:
    return build_research_strategy_expected_value_input_quality_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_for_manual_review() -> None:
    quality_report = report(())

    assert type(quality_report) is ResearchStrategyExpectedValueInputQualityReport
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.config_version == (
        "research-strategy-expected-value-input-quality-report-v0"
    )
    assert quality_report.input_count == d("0")
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.average_input_quality_score is None
    assert quality_report.status == "block"
    assert quality_report.reason_codes == ("no_expected_value_research_inputs",)
    assert quality_report.reason_code_counts == (
        ResearchStrategyExpectedValueInputQualityReasonCodeCount(
            reason_code="no_expected_value_research_inputs",
            count=d("1"),
        ),
    )
    assert quality_report.rows == ()
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True


def test_complete_ev_inputs_pass_with_weighted_decimal_score() -> None:
    quality_report = report(
        (
            input_row(
                "ev-case-alpha",
                reason_codes=("manually_checked",),
            ),
        ),
    )

    row = quality_report.rows[0]
    assert type(row) is ResearchStrategyExpectedValueInputQualityRow
    assert quality_report.status == "pass"
    assert quality_report.input_count == d("1")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.average_input_quality_score == d("0.840000")
    assert quality_report.reason_codes == ("expected_value_input_quality_pass",)
    assert row.research_key == "ev-case-alpha"
    assert row.evidence_set_label == "packet-alpha"
    assert row.forecast_confidence == d("0.820000")
    assert row.cost_estimate_quality == d("0.880000")
    assert row.liquidity_quality == d("0.760000")
    assert row.resolution_clarity == d("0.900000")
    assert row.evidence_freshness == d("0.840000")
    assert row.input_quality_score == d("0.840000")
    assert row.lowest_component_quality == d("0.760000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "component_cost_estimate_quality_pass",
        "component_evidence_freshness_pass",
        "component_forecast_confidence_pass",
        "component_liquidity_quality_pass",
        "component_resolution_clarity_pass",
        "expected_value_input_quality_pass",
        "input_manually_checked",
        "manual_review_input_quality_pass",
    )


def test_watch_and_block_statuses_reflect_incomplete_review_inputs() -> None:
    quality_report = report(
        (
            input_row(
                "ev-case-watch",
                forecast_confidence=d("0.760000"),
                cost_estimate_quality=d("0.520000"),
                liquidity_quality=d("0.620000"),
                resolution_clarity=d("0.840000"),
                evidence_freshness=d("0.860000"),
            ),
            input_row(
                "ev-case-block",
                forecast_confidence=d("0.600000"),
                cost_estimate_quality=d("0.550000"),
                liquidity_quality=d("0.500000"),
                resolution_clarity=d("0.300000"),
                evidence_freshness=d("0.380000"),
                reason_codes=("resolution_needs_review",),
            ),
        ),
    )

    block_row, watch_row = quality_report.rows
    assert quality_report.status == "block"
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("1")
    assert quality_report.block_count == d("1")
    assert quality_report.average_input_quality_score == d("0.593000")
    assert block_row.research_key == "ev-case-block"
    assert block_row.input_quality_score == d("0.466000")
    assert block_row.lowest_component_quality == d("0.300000")
    assert block_row.status == "block"
    assert "component_resolution_clarity_block" in block_row.reason_codes
    assert "component_evidence_freshness_block" in block_row.reason_codes
    assert "input_resolution_needs_review" in block_row.reason_codes
    assert watch_row.research_key == "ev-case-watch"
    assert watch_row.input_quality_score == d("0.720000")
    assert watch_row.lowest_component_quality == d("0.520000")
    assert watch_row.status == "watch"
    assert "component_cost_estimate_quality_watch" in watch_row.reason_codes
    assert "component_liquidity_quality_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_without_raw_identifiers_or_floats() -> None:
    first_report = report(
        (
            input_row("z-case", reason_codes=("zeta", "alpha")),
            input_row("a-case", evidence_set_label="packet-beta"),
        ),
    )
    second_report = report(
        (
            input_row("a-case", evidence_set_label="packet-beta"),
            input_row("z-case", reason_codes=("alpha", "zeta")),
        ),
    )

    first_payload = research_strategy_expected_value_input_quality_report_payload(
        first_report,
    )
    second_payload = research_strategy_expected_value_input_quality_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert tuple(row.research_key for row in first_report.rows) == ("a-case", "z-case")
    assert first_payload == second_payload
    assert research_strategy_expected_value_input_quality_report_digest(first_report) == (
        research_strategy_expected_value_input_quality_report_digest(second_report)
    )
    assert len(research_strategy_expected_value_input_quality_report_digest(first_report)) == 64
    assert first_payload["rows"][0]["input_quality_score"] == "0.840000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.8" not in encoded
    assert not any(_has_forbidden_identifier_key(key) for key in _walk_payload_keys(first_payload))


def test_validation_rejects_non_decimal_values_bad_flags_and_raw_labels() -> None:
    with pytest.raises(ValueError, match="forecast_confidence_weight"):
        config(forecast_confidence_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_quality_score"):
        config(pass_quality_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_component_quality"):
        config(watch_component_quality=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((input_row("ev-case-alpha"),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (input_row("ev-case-alpha"),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(" ev-case-alpha")
    with pytest.raises(ValueError, match="research_key"):
        input_row("raw-alpha")
    with pytest.raises(ValueError, match="forecast_confidence"):
        input_row("ev-case-alpha", forecast_confidence=0.82)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_quality"):
        input_row("ev-case-alpha", liquidity_quality=d("1.1"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row("ev-case-alpha", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row("ev-case-alpha"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    quality_report = report((input_row("ev-case-alpha"),))

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].input_quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="input_quality_score"):
        replace(quality_report.rows[0], input_quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(quality_report, status="watch")


def test_owned_module_has_no_execution_surface_or_action_language() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_expected_value_input_quality_report.py"
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
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "buy",
        "sell",
        "recommend",
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


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_identifier_key(key: str) -> bool:
    return key in {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_id",
        "source_url",
        "source_reference",
    }
