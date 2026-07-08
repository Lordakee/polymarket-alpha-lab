from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_uncertainty_decomposition_report import (
    ResearchStrategyEventForecast,
    ResearchStrategyUncertaintyComponentRow,
    ResearchStrategyUncertaintyConfig,
    ResearchStrategyUncertaintyDecompositionReport,
    ResearchStrategyUncertaintyEventRow,
    ResearchStrategyUncertaintyReasonCodeCount,
    build_research_strategy_uncertainty_decomposition_report,
    research_strategy_uncertainty_decomposition_report_digest,
    research_strategy_uncertainty_decomposition_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedForecastShape:
    event_id: str
    forecast_id: str
    market_slug: str
    public_question: str
    forecasted_at: datetime
    expected_resolution_at: datetime
    evidence_quality_score: Decimal
    model_disagreement_score: Decimal
    market_mechanics_score: Decimal
    resolution_ambiguity_score: Decimal
    timing_risk_score: Decimal
    evidence_count: Decimal
    model_count: Decimal
    public_notes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyUncertaintyConfig:
    values = {
        "config_version": "research-strategy-uncertainty-decomposition-v0",
        "pass_uncertainty_threshold": d("0.350000"),
        "block_uncertainty_threshold": d("0.650000"),
        "component_watch_threshold": d("0.500000"),
        "component_block_threshold": d("0.800000"),
        "evidence_quality_weight": d("0.250000"),
        "model_disagreement_weight": d("0.200000"),
        "market_mechanics_weight": d("0.200000"),
        "resolution_ambiguity_weight": d("0.200000"),
        "timing_risk_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchStrategyUncertaintyConfig(**values)


def forecast(
    index: int,
    *,
    event_id: str = "event-alpha",
    forecast_id: str | None = None,
    market_slug: str = "market-alpha",
    public_question: str = "Will the event resolve under published public criteria?",
    forecasted_at: datetime | None = None,
    expected_resolution_at: datetime | None = None,
    evidence_quality_score: Decimal = d("0.900000"),
    model_disagreement_score: Decimal = d("0.100000"),
    market_mechanics_score: Decimal = d("0.050000"),
    resolution_ambiguity_score: Decimal = d("0.100000"),
    timing_risk_score: Decimal = d("0.100000"),
    evidence_count: Decimal = d("3"),
    model_count: Decimal = d("3"),
    public_notes: tuple[str, ...] = (),
) -> ResearchStrategyEventForecast:
    observed = (
        forecasted_at if forecasted_at is not None else GENERATED_AT - timedelta(hours=1)
    )
    return ResearchStrategyEventForecast(
        event_id=event_id,
        forecast_id=forecast_id or f"forecast-{index:03d}",
        market_slug=market_slug,
        public_question=public_question,
        forecasted_at=observed,
        expected_resolution_at=(
            expected_resolution_at
            if expected_resolution_at is not None
            else observed + timedelta(days=10)
        ),
        evidence_quality_score=evidence_quality_score,
        model_disagreement_score=model_disagreement_score,
        market_mechanics_score=market_mechanics_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        timing_risk_score=timing_risk_score,
        evidence_count=evidence_count,
        model_count=model_count,
        public_notes=public_notes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyUncertaintyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyUncertaintyDecompositionReport:
    return build_research_strategy_uncertainty_decomposition_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_block_report_with_hard_flags() -> None:
    uncertainty_report = report(())

    assert type(uncertainty_report) is ResearchStrategyUncertaintyDecompositionReport
    assert uncertainty_report.generated_at == GENERATED_AT
    assert uncertainty_report.config_version == "research-strategy-uncertainty-decomposition-v0"
    assert uncertainty_report.event_count == d("0")
    assert uncertainty_report.pass_count == d("0")
    assert uncertainty_report.watch_count == d("0")
    assert uncertainty_report.block_count == d("0")
    assert uncertainty_report.average_uncertainty_score is None
    assert uncertainty_report.status == "block"
    assert uncertainty_report.reason_codes == ("no_public_forecast_inputs",)
    assert uncertainty_report.reason_code_counts == (
        ResearchStrategyUncertaintyReasonCodeCount(
            reason_code="no_public_forecast_inputs",
            count=d("1"),
        ),
    )
    assert uncertainty_report.rows == ()
    assert uncertainty_report.paper_only is True
    assert uncertainty_report.report_only is True
    assert uncertainty_report.readonly is True

    payload = research_strategy_uncertainty_decomposition_report_payload(
        uncertainty_report,
    )
    assert payload["status"] == "block"
    assert (
        research_strategy_uncertainty_decomposition_report_digest(uncertainty_report)
        == "fb769db372f1b99b96785ecbe8ca2a46912c90e886615d992fc742232cc1a71c"
    )


def test_decomposes_five_uncertainty_sources_and_statuses_deterministically() -> None:
    uncertainty_report = report(
        (
            forecast(
                3,
                event_id="event-block",
                forecast_id="forecast-block",
                market_slug="market-block",
                evidence_quality_score=d("0.200000"),
                model_disagreement_score=d("0.750000"),
                market_mechanics_score=d("0.600000"),
                resolution_ambiguity_score=d("0.500000"),
                timing_risk_score=d("0.400000"),
            ),
            SuppliedForecastShape(
                event_id="event-watch",
                forecast_id="forecast-watch",
                market_slug="market-watch",
                public_question="Will the event resolve under published public criteria?",
                forecasted_at=GENERATED_AT - timedelta(hours=1),
                expected_resolution_at=GENERATED_AT + timedelta(days=9, hours=23),
                evidence_quality_score=d("0.550000"),
                model_disagreement_score=d("0.550000"),
                market_mechanics_score=d("0.300000"),
                resolution_ambiguity_score=d("0.250000"),
                timing_risk_score=d("0.200000"),
                evidence_count=d("2"),
                model_count=d("2"),
                public_notes=("public-method-review",),
            ),
            forecast(
                1,
                event_id="event-pass",
                forecast_id="forecast-pass",
                market_slug="market-pass",
            ),
        ),
    )

    assert tuple(row.status for row in uncertainty_report.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert uncertainty_report.status == "block"
    assert uncertainty_report.pass_count == d("1")
    assert uncertainty_report.watch_count == d("1")
    assert uncertainty_report.block_count == d("1")
    assert uncertainty_report.average_uncertainty_score == d("0.360833")
    assert set(uncertainty_report.reason_codes) == {
        "evidence_quality_block",
        "model_disagreement_watch",
        "uncertainty_block",
        "uncertainty_pass",
        "uncertainty_watch",
    }

    block_row, pass_row, watch_row = uncertainty_report.rows
    assert pass_row.status == "pass"
    assert pass_row.uncertainty_score == d("0.090000")
    assert pass_row.days_to_resolution == d("10.000000")
    assert pass_row.dominant_components == ("evidence_quality",)
    assert pass_row.component_rows == (
        ResearchStrategyUncertaintyComponentRow(
            component="evidence_quality",
            raw_score=d("0.900000"),
            uncertainty_score=d("0.100000"),
            weight=d("0.250000"),
            weighted_contribution=d("0.025000"),
            status="pass",
            reason_codes=("evidence_quality_pass",),
        ),
        ResearchStrategyUncertaintyComponentRow(
            component="model_disagreement",
            raw_score=d("0.100000"),
            uncertainty_score=d("0.100000"),
            weight=d("0.200000"),
            weighted_contribution=d("0.020000"),
            status="pass",
            reason_codes=("model_disagreement_pass",),
        ),
        ResearchStrategyUncertaintyComponentRow(
            component="market_mechanics",
            raw_score=d("0.050000"),
            uncertainty_score=d("0.050000"),
            weight=d("0.200000"),
            weighted_contribution=d("0.010000"),
            status="pass",
            reason_codes=("market_mechanics_pass",),
        ),
        ResearchStrategyUncertaintyComponentRow(
            component="resolution_ambiguity",
            raw_score=d("0.100000"),
            uncertainty_score=d("0.100000"),
            weight=d("0.200000"),
            weighted_contribution=d("0.020000"),
            status="pass",
            reason_codes=("resolution_ambiguity_pass",),
        ),
        ResearchStrategyUncertaintyComponentRow(
            component="timing_risk",
            raw_score=d("0.100000"),
            uncertainty_score=d("0.100000"),
            weight=d("0.150000"),
            weighted_contribution=d("0.015000"),
            status="pass",
            reason_codes=("timing_risk_pass",),
        ),
    )

    assert watch_row.status == "watch"
    assert watch_row.uncertainty_score == d("0.362500")
    assert watch_row.dominant_components == ("evidence_quality", "model_disagreement")
    assert "model_disagreement_watch" in watch_row.reason_codes
    assert block_row.status == "block"
    assert block_row.uncertainty_score == d("0.630000")
    assert block_row.dominant_components == ("evidence_quality",)
    assert "evidence_quality_block" in block_row.reason_codes


def test_all_zero_uncertainty_keeps_dominant_components_nonempty() -> None:
    uncertainty_report = report(
        (
            forecast(
                1,
                evidence_quality_score=d("1.000000"),
                model_disagreement_score=d("0.000000"),
                market_mechanics_score=d("0.000000"),
                resolution_ambiguity_score=d("0.000000"),
                timing_risk_score=d("0.000000"),
            ),
        ),
    )

    zero_row = uncertainty_report.rows[0]

    assert zero_row.status == "pass"
    assert zero_row.uncertainty_score == d("0.000000")
    assert zero_row.dominant_components == tuple(
        component.component for component in zero_row.component_rows
    )
    assert zero_row.reason_codes == ("uncertainty_pass",)


def test_payload_and_digest_are_stable_json_safe_and_public_only() -> None:
    first = report(
        (
            forecast(
                2,
                event_id="raw-event-z",
                forecast_id="raw-forecast-z",
                market_slug="raw-market-z",
                public_question="Raw public question z?",
                evidence_quality_score=d("0.200000"),
                model_disagreement_score=d("0.750000"),
                market_mechanics_score=d("0.600000"),
                resolution_ambiguity_score=d("0.500000"),
                timing_risk_score=d("0.400000"),
            ),
            forecast(
                1,
                event_id="raw-event-a",
                forecast_id="raw-forecast-a",
                market_slug="raw-market-a",
                public_question="Raw public question a?",
            ),
        ),
    )
    second = report(
        (
            forecast(
                1,
                event_id="raw-event-a",
                forecast_id="raw-forecast-a",
                market_slug="raw-market-a",
                public_question="Raw public question a?",
            ),
            forecast(
                2,
                event_id="raw-event-z",
                forecast_id="raw-forecast-z",
                market_slug="raw-market-z",
                public_question="Raw public question z?",
                evidence_quality_score=d("0.200000"),
                model_disagreement_score=d("0.750000"),
                market_mechanics_score=d("0.600000"),
                resolution_ambiguity_score=d("0.500000"),
                timing_risk_score=d("0.400000"),
            ),
        ),
    )
    renamed = report(
        (
            forecast(
                3,
                event_id="renamed-event-z",
                forecast_id="renamed-forecast-z",
                market_slug="renamed-market-z",
                public_question="Renamed public question z?",
                evidence_quality_score=d("0.200000"),
                model_disagreement_score=d("0.750000"),
                market_mechanics_score=d("0.600000"),
                resolution_ambiguity_score=d("0.500000"),
                timing_risk_score=d("0.400000"),
            ),
            forecast(
                4,
                event_id="renamed-event-a",
                forecast_id="renamed-forecast-a",
                market_slug="renamed-market-a",
                public_question="Renamed public question a?",
            ),
        ),
    )

    first_payload = research_strategy_uncertainty_decomposition_report_payload(first)
    second_payload = research_strategy_uncertainty_decomposition_report_payload(second)
    renamed_payload = research_strategy_uncertainty_decomposition_report_payload(renamed)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload == renamed_payload
    assert research_strategy_uncertainty_decomposition_report_digest(
        first,
    ) == research_strategy_uncertainty_decomposition_report_digest(second)
    assert research_strategy_uncertainty_decomposition_report_digest(
        first,
    ) == research_strategy_uncertainty_decomposition_report_digest(renamed)
    assert tuple(row["status"] for row in first_payload["rows"]) == (
        "block",
        "pass",
    )
    assert tuple(row["uncertainty_score"] for row in first_payload["rows"]) == (
        "0.630000",
        "0.090000",
    )
    for row in first_payload["rows"]:
        for raw_field in (
            "event_id",
            "forecast_id",
            "market_slug",
            "public_question",
        ):
            assert raw_field not in row
    for raw_value in (
        "raw-event-z",
        "raw-forecast-z",
        "raw-market-z",
        "Raw public question z?",
        "raw-event-a",
        "raw-forecast-a",
        "raw-market-a",
        "Raw public question a?",
    ):
        assert raw_value.lower() not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    for forbidden in (
        "wallet",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "live-execution",
    ):
        assert forbidden not in encoded.lower()


def test_validation_rejects_non_decimal_numbers_sensitive_text_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="evidence_quality_weight"):
        config(evidence_quality_weight=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="model_count"):
        forecast(1, model_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timing_risk_score"):
        forecast(1, timing_risk_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((forecast(1),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((forecast(1),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecasted_at"):
        forecast(1, forecasted_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="expected_resolution_at"):
        forecast(
            1,
            forecasted_at=GENERATED_AT,
            expected_resolution_at=GENERATED_AT - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="public_question"):
        forecast(1, public_question="Public summary mentions wallet telemetry")
    with pytest.raises(ValueError, match="market_slug"):
        forecast(1, market_slug="order-flow-review")
    with pytest.raises(ValueError, match="public_notes"):
        forecast(1, public_notes=("contains live-execution detail",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(forecast(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    uncertainty_report = report((forecast(1),))

    with pytest.raises(FrozenInstanceError):
        uncertainty_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        uncertainty_report.rows[0].uncertainty_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(uncertainty_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="uncertainty_score"):
        replace(uncertainty_report.rows[0], uncertainty_score=d("0.500000"))
    with pytest.raises(ValueError, match="weighted_contribution"):
        replace(
            uncertainty_report.rows[0].component_rows[0],
            weighted_contribution=d("0.500000"),
        )


def test_owned_module_has_no_network_db_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_uncertainty_decomposition_report.py"
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
        "sqlite",
        "psycopg",
        "supabase",
        "insert(",
        "update(",
        "delete(",
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
