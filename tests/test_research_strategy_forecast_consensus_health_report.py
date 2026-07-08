from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_forecast_consensus_health_report import (
    ResearchStrategyForecastConsensusHealthConfig,
    ResearchStrategyForecastConsensusHealthInput,
    ResearchStrategyForecastConsensusHealthReasonCodeCount,
    ResearchStrategyForecastConsensusHealthReport,
    ResearchStrategyForecastConsensusHealthRow,
    build_research_strategy_forecast_consensus_health_report,
    research_strategy_forecast_consensus_health_report_digest,
    research_strategy_forecast_consensus_health_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyForecastConsensusHealthConfig:
    values = {
        "config_version": "research-strategy-forecast-consensus-health-report-v0",
        "pass_dimension_score": d("0.700000"),
        "watch_dimension_score": d("0.400000"),
        "pass_health_score": d("0.750000"),
        "watch_health_score": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategyForecastConsensusHealthConfig(**values)


def input_row(
    consensus_scope_label: str,
    *,
    team_confidence_dispersion: Decimal = d("0.080000"),
    calibration_drift: Decimal = d("0.040000"),
    evidence_freshness: Decimal = d("0.870000"),
    contradiction_pressure: Decimal = d("0.060000"),
    cost_input_quality: Decimal = d("0.880000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyForecastConsensusHealthInput:
    return ResearchStrategyForecastConsensusHealthInput(
        consensus_scope_label=consensus_scope_label,
        team_confidence_dispersion=team_confidence_dispersion,
        calibration_drift=calibration_drift,
        evidence_freshness=evidence_freshness,
        contradiction_pressure=contradiction_pressure,
        cost_input_quality=cost_input_quality,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyForecastConsensusHealthConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyForecastConsensusHealthReport:
    return build_research_strategy_forecast_consensus_health_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_for_manual_review() -> None:
    health_report = report(())

    assert type(health_report) is ResearchStrategyForecastConsensusHealthReport
    assert health_report.generated_at == GENERATED_AT
    assert health_report.config_version == (
        "research-strategy-forecast-consensus-health-report-v0"
    )
    assert health_report.scope_count == d("0")
    assert health_report.pass_count == d("0")
    assert health_report.watch_count == d("0")
    assert health_report.block_count == d("0")
    assert health_report.average_consensus_health_score is None
    assert health_report.max_team_confidence_dispersion is None
    assert health_report.max_calibration_drift is None
    assert health_report.min_evidence_freshness is None
    assert health_report.max_contradiction_pressure is None
    assert health_report.min_cost_input_quality is None
    assert health_report.status == "block"
    assert health_report.reason_codes == ("no_forecast_consensus_health_inputs",)
    assert health_report.reason_code_counts == (
        ResearchStrategyForecastConsensusHealthReasonCodeCount(
            reason_code="no_forecast_consensus_health_inputs",
            count=d("1"),
        ),
    )
    assert health_report.rows == ()
    assert health_report.paper_only is True
    assert health_report.report_only is True
    assert health_report.readonly is True


def test_public_safe_consensus_inputs_pass_with_aggregate_decimal_score() -> None:
    health_report = report(
        (
            input_row(
                "consensus-case-alpha",
                reason_codes=("manual_consensus_review",),
            ),
        ),
    )

    row = health_report.rows[0]
    assert type(row) is ResearchStrategyForecastConsensusHealthRow
    assert health_report.status == "pass"
    assert health_report.scope_count == d("1")
    assert health_report.pass_count == d("1")
    assert health_report.watch_count == d("0")
    assert health_report.block_count == d("0")
    assert health_report.average_consensus_health_score == d("0.914000")
    assert health_report.max_team_confidence_dispersion == d("0.080000")
    assert health_report.max_calibration_drift == d("0.040000")
    assert health_report.min_evidence_freshness == d("0.870000")
    assert health_report.max_contradiction_pressure == d("0.060000")
    assert health_report.min_cost_input_quality == d("0.880000")
    assert health_report.reason_codes == ("forecast_consensus_health_pass",)
    assert row.consensus_scope_label == "consensus-case-alpha"
    assert row.team_confidence_dispersion == d("0.080000")
    assert row.confidence_alignment_score == d("0.920000")
    assert row.calibration_stability_score == d("0.960000")
    assert row.evidence_freshness_score == d("0.870000")
    assert row.contradiction_resistance_score == d("0.940000")
    assert row.cost_input_quality_score == d("0.880000")
    assert row.consensus_health_score == d("0.914000")
    assert row.lowest_dimension_score == d("0.870000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "calibration_drift_pass",
        "confidence_dispersion_pass",
        "contradiction_pressure_pass",
        "cost_input_quality_pass",
        "evidence_freshness_pass",
        "forecast_consensus_health_pass",
        "input_manual_consensus_review",
        "report_only_consensus_health_pass",
    )


def test_watch_and_block_statuses_reflect_health_pressure_dimensions() -> None:
    health_report = report(
        (
            input_row(
                "consensus-case-watch",
                team_confidence_dispersion=d("0.180000"),
                calibration_drift=d("0.120000"),
                evidence_freshness=d("0.620000"),
                contradiction_pressure=d("0.180000"),
                cost_input_quality=d("0.660000"),
            ),
            input_row(
                "consensus-case-block",
                team_confidence_dispersion=d("0.410000"),
                calibration_drift=d("0.260000"),
                evidence_freshness=d("0.350000"),
                contradiction_pressure=d("0.450000"),
                cost_input_quality=d("0.390000"),
                reason_codes=("cost_review_needed",),
            ),
        ),
    )

    block_row, watch_row = health_report.rows
    assert health_report.status == "block"
    assert health_report.pass_count == d("0")
    assert health_report.watch_count == d("1")
    assert health_report.block_count == d("1")
    assert health_report.average_consensus_health_score == d("0.642000")
    assert health_report.max_team_confidence_dispersion == d("0.410000")
    assert health_report.max_calibration_drift == d("0.260000")
    assert health_report.min_evidence_freshness == d("0.350000")
    assert health_report.max_contradiction_pressure == d("0.450000")
    assert health_report.min_cost_input_quality == d("0.390000")
    assert block_row.consensus_scope_label == "consensus-case-block"
    assert block_row.consensus_health_score == d("0.524000")
    assert block_row.lowest_dimension_score == d("0.350000")
    assert block_row.status == "block"
    assert "confidence_dispersion_block" in block_row.reason_codes
    assert "evidence_freshness_block" in block_row.reason_codes
    assert "cost_input_quality_block" in block_row.reason_codes
    assert "input_cost_review_needed" in block_row.reason_codes
    assert watch_row.consensus_scope_label == "consensus-case-watch"
    assert watch_row.consensus_health_score == d("0.760000")
    assert watch_row.lowest_dimension_score == d("0.620000")
    assert watch_row.status == "watch"
    assert "evidence_freshness_watch" in watch_row.reason_codes
    assert "cost_input_quality_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_without_raw_identifiers_or_floats() -> None:
    first_report = report(
        (
            input_row("z-consensus", reason_codes=("zeta", "alpha")),
            input_row("a-consensus"),
        ),
    )
    second_report = report(
        (
            input_row("a-consensus"),
            input_row("z-consensus", reason_codes=("alpha", "zeta")),
        ),
    )

    first_payload = research_strategy_forecast_consensus_health_report_payload(first_report)
    second_payload = research_strategy_forecast_consensus_health_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert tuple(row.consensus_scope_label for row in first_report.rows) == (
        "a-consensus",
        "z-consensus",
    )
    assert first_payload == second_payload
    assert research_strategy_forecast_consensus_health_report_digest(first_report) == (
        research_strategy_forecast_consensus_health_report_digest(second_report)
    )
    assert len(research_strategy_forecast_consensus_health_report_digest(first_report)) == 64
    assert first_payload["rows"][0]["consensus_health_score"] == "0.914000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.9" not in encoded
    assert not any(_has_forbidden_identifier_key(key) for key in _walk_payload_keys(first_payload))


def test_validation_rejects_non_decimal_values_bad_flags_and_raw_labels() -> None:
    with pytest.raises(ValueError, match="pass_dimension_score"):
        config(pass_dimension_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_health_score"):
        config(watch_health_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="pass_health_score"):
        config(pass_health_score=d("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((input_row("consensus-case-alpha"),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (input_row("consensus-case-alpha"),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="consensus_scope_label"):
        input_row(" consensus-case-alpha")
    with pytest.raises(ValueError, match="consensus_scope_label"):
        input_row("raw-event-alpha")
    with pytest.raises(ValueError, match="team_confidence_dispersion"):
        input_row("consensus-case-alpha", team_confidence_dispersion=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="calibration_drift"):
        input_row("consensus-case-alpha", calibration_drift=d("1.1"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row("consensus-case-alpha", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row("consensus-case-alpha"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    health_report = report((input_row("consensus-case-alpha"),))

    with pytest.raises(FrozenInstanceError):
        health_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        health_report.rows[0].consensus_health_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="consensus_health_score"):
        replace(health_report.rows[0], consensus_health_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(health_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="status"):
        replace(health_report, status="watch")


def test_owned_module_has_no_execution_surface_or_action_language() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_forecast_consensus_health_report.py"
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
        "position sizing",
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
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_id",
        "source_url",
        "source_reference",
    }
