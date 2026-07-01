from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.team_diagnostics_snapshot as snapshot_module
from polymarket_alpha_lab.team_diagnostics_bundle import (
    TeamDiagnosticsBundleConfig,
    build_team_diagnostics_bundle_report,
)
from polymarket_alpha_lab.team_diagnostics_snapshot import (
    DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_CONFIG_VERSION,
    TeamDiagnosticsSnapshotConfig,
    TeamDiagnosticsSnapshotReport,
    build_team_diagnostics_snapshot_report,
)
from polymarket_alpha_lab.team_event_template_performance import (
    TeamEventTemplatePerformanceConfig,
)
from polymarket_alpha_lab.team_evidence_quality import TeamEvidenceQualityConfig
from polymarket_alpha_lab.team_forecast_calibration import TeamForecastCalibrationConfig
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_evidence_to_db_row,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)
from polymarket_alpha_lab.team_memory_synthesis import TeamMemorySynthesisConfig
from polymarket_alpha_lab.team_source_reliability import TeamSourceReliabilityConfig


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 58, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _forecast_row(
    forecast_id: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    event_template: str = "btc_hit_price",
    market_slug: str | None = None,
    probability: Decimal = d("0.800000"),
    confidence: Decimal = d("0.700000"),
    generated_at: datetime = GENERATED_AT,
) -> TeamForecastDbRow:
    return team_forecast_to_db_row(
        TeamForecastPacket(
            forecast_id=forecast_id,
            team_id=team_id,
            condition_id=f"condition-{forecast_id}",
            market_slug=market_slug or f"market-{forecast_id}",
            question=f"Will {forecast_id} resolve yes?",
            category_id=category_id,
            event_template=event_template,
            selected_side="yes",
            forecast_probability=probability,
            confidence=confidence,
            evidence_quality=d("0.800000"),
            data_freshness_score=d("0.900000"),
            resolution_risk=d("0.100000"),
            base_rate=d("0.540000"),
            market_implied_probability_observed=d("0.570000"),
            reason_codes=("team_diagnostics_snapshot_test",),
            memory_references=("memory-test",),
            source_references=("source-test",),
            known_failure_modes=("test_failure_mode",),
            config_version="team-forecast-v0",
            prompt_version="team-prompt-v0",
            generated_at=generated_at,
        ),
    )


def _evidence_row(
    forecast: TeamForecastDbRow,
    *,
    evidence_id: str | None = None,
    source_id: str = "source-etf-flow-dashboard",
    generated_at: datetime = GENERATED_AT,
    weight: Decimal = d("0.600000"),
) -> TeamForecastEvidenceDbRow:
    return team_forecast_evidence_to_db_row(
        TeamForecastEvidencePacket(
            evidence_id=evidence_id or f"evidence-{forecast.forecast_id}",
            team_id=forecast.team_id,
            market_slug=forecast.market_slug,
            source_id=source_id,
            source_type="market_data",
            data_timestamp=DATA_TIMESTAMP,
            data_freshness_seconds=120,
            evidence_type="snapshot_test_evidence",
            evidence_text="Complete supplied evidence for the diagnostics snapshot.",
            weight=weight,
            reason_codes=("team_diagnostics_snapshot_test",),
        ),
        forecast_id=forecast.forecast_id,
        config_version="team-forecast-evidence-v0",
        generated_at=generated_at,
    )


def _outcome_row(
    forecast: TeamForecastDbRow,
    *,
    outcome_id: str | None = None,
    actual_outcome: str = "yes",
    resolved_at: datetime | None = None,
    generated_at: datetime | None = None,
    paper_pnl: Decimal = d("0.010000"),
    profitable_after_cost: bool = True,
    resolution_dispute_flag: bool = False,
    directionally_correct: bool | None = None,
) -> TeamForecastOutcomeDbRow:
    resolved = resolved_at or GENERATED_AT + timedelta(days=1)
    generated = generated_at or resolved + timedelta(minutes=5)
    actual_value = d("1.000000") if actual_outcome == "yes" else d("0.000000")
    forecast_error = abs(forecast.forecast_probability - actual_value)
    if directionally_correct is None:
        directionally_correct = (
            forecast.forecast_probability >= d("0.500000")
            if actual_outcome == "yes"
            else forecast.forecast_probability < d("0.500000")
        )
    return team_forecast_outcome_to_db_row(
        TeamForecastOutcome(
            outcome_id=outcome_id or f"outcome-{forecast.forecast_id}",
            forecast_id=forecast.forecast_id,
            team_id=forecast.team_id,
            market_slug=forecast.market_slug,
            actual_outcome=actual_outcome,
            resolved_at=resolved,
            settlement_source="polymarket_public_resolution",
            forecast_error=forecast_error,
            brier_score=forecast_error * forecast_error,
            paper_pnl=paper_pnl,
            cost_adjusted_return=d("0.010000" if profitable_after_cost else "-0.010000"),
            directionally_correct=directionally_correct,
            profitable_after_cost=profitable_after_cost,
            resolution_dispute_flag=resolution_dispute_flag,
            reason_codes=(f"settled_{actual_outcome}",),
        ),
        config_version="team-forecast-outcome-v0",
        generated_at=generated,
    )


def _bundle_config() -> TeamDiagnosticsBundleConfig:
    return TeamDiagnosticsBundleConfig(
        config_version="team-diagnostics-bundle-snapshot-test-v0",
        memory_synthesis_config=TeamMemorySynthesisConfig(
            config_version="team-memory-synthesis-snapshot-test-v0",
            min_category_settled_forecasts=2,
            min_event_template_settled_forecasts=2,
        ),
        forecast_calibration_config=TeamForecastCalibrationConfig(
            config_version="team-forecast-calibration-snapshot-test-v0",
            bucket_count=2,
            min_settled_forecasts=2,
            min_group_settled_forecasts=1,
        ),
        event_template_performance_config=TeamEventTemplatePerformanceConfig(
            config_version="team-event-template-performance-snapshot-test-v0",
            min_settled_forecasts=2,
            max_dispute_rate=d("1.000000"),
            min_profitable_after_cost_rate=d("0.000000"),
        ),
        source_reliability_config=TeamSourceReliabilityConfig(
            config_version="team-source-reliability-snapshot-test-v0",
            min_settled_evidence_count=2,
            max_dispute_rate=d("1.000000"),
            min_profitable_rate=d("0.000000"),
        ),
        evidence_quality_config=TeamEvidenceQualityConfig(
            config_version="team-evidence-quality-snapshot-test-v0",
            stale_after_seconds=3600,
        ),
    )


def _bundle_report():
    btc_first = _forecast_row("forecast-btc-1", probability=d("0.800000"))
    btc_second = _forecast_row(
        "forecast-btc-2",
        probability=d("0.400000"),
        confidence=d("0.600000"),
        generated_at=GENERATED_AT + timedelta(minutes=1),
    )
    eth = _forecast_row(
        "forecast-eth-1",
        team_id="crypto_eth",
        category_id="finance.crypto.eth",
        event_template="eth_hit_price",
        market_slug="market-forecast-eth-1",
        probability=d("0.300000"),
        generated_at=GENERATED_AT + timedelta(minutes=2),
    )

    return build_team_diagnostics_bundle_report(
        [btc_second, eth, btc_first],
        [
            _evidence_row(btc_first, evidence_id="evidence-btc-1"),
            _evidence_row(btc_second, evidence_id="evidence-btc-2"),
            _evidence_row(
                eth,
                evidence_id="evidence-eth-1",
                source_id="source-onchain-dashboard",
            ),
        ],
        [
            _outcome_row(btc_first, actual_outcome="yes", paper_pnl=d("0.150000")),
            _outcome_row(
                btc_second,
                actual_outcome="yes",
                paper_pnl=d("-0.070000"),
                profitable_after_cost=False,
                resolution_dispute_flag=True,
                directionally_correct=False,
            ),
            _outcome_row(eth, actual_outcome="no", paper_pnl=d("0.030000")),
        ],
        config=_bundle_config(),
        generated_at=GENERATED_AT,
    )


def _snapshot_report(**overrides: Any) -> TeamDiagnosticsSnapshotReport:
    values: dict[str, Any] = {
        "generated_at": GENERATED_AT,
        "config_version": DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_CONFIG_VERSION,
        "source_config_version": "team-diagnostics-bundle-snapshot-test-v0",
        "filters": (),
        "forecast_row_count": 3,
        "evidence_row_count": 3,
        "outcome_row_count": 3,
        "memory_eligible_reference_count": 2,
        "calibration_status": "validated",
        "calibration_settled_count": 3,
        "calibration_group_count": 6,
        "event_template_row_count": 2,
        "event_template_status": "validated",
        "source_reliability_row_count": 2,
        "source_reliability_missing_source_evidence_count": 0,
        "evidence_quality_status": "evidence_quality_pass",
        "evidence_quality_pass_count": 3,
        "evidence_quality_watch_count": 0,
        "evidence_quality_blocked_count": 0,
        "evidence_quality_average_quality_score": d("0.900000"),
        "reason_codes": ("evidence_quality_complete", "min_settled_forecasts_met"),
    }
    values.update(overrides)
    return TeamDiagnosticsSnapshotReport(**values)


def _assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("diagnostics snapshot output must not contain float values")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_float_values(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float_values(key)
            _assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float_values(item)


def test_config_and_report_are_frozen_and_validate_hard_flags() -> None:
    config = TeamDiagnosticsSnapshotConfig()

    assert config.config_version == "team-diagnostics-snapshot-v0"
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    with pytest.raises(FrozenInstanceError):
        config.config_version = "mutated"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        TeamDiagnosticsSnapshotConfig(config_version=" team-diagnostics-snapshot-v0 ")
    with pytest.raises(ValueError, match="paper_only"):
        TeamDiagnosticsSnapshotConfig(paper_only=False)

    report = _snapshot_report()
    with pytest.raises(FrozenInstanceError):
        report.config_version = "mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        _snapshot_report(readonly=False)


def test_snapshot_report_normalizes_generated_at_to_utc() -> None:
    generated_at = datetime(2026, 7, 1, 8, 0, tzinfo=timezone(timedelta(hours=-4)))

    report = _snapshot_report(generated_at=generated_at)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


def test_build_snapshot_rejects_invalid_filters_and_non_exact_inputs() -> None:
    bundle_report = _bundle_report()

    with pytest.raises(ValueError, match="config"):
        build_team_diagnostics_snapshot_report(
            bundle_report,
            config="not-a-config",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="bundle_report"):
        build_team_diagnostics_snapshot_report(
            object(),  # type: ignore[arg-type]
            config=TeamDiagnosticsSnapshotConfig(),
        )
    with pytest.raises(ValueError, match="team_id"):
        build_team_diagnostics_snapshot_report(
            bundle_report,
            config=TeamDiagnosticsSnapshotConfig(),
            team_id=" crypto_btc ",
        )
    with pytest.raises(ValueError, match="market_slug"):
        build_team_diagnostics_snapshot_report(
            bundle_report,
            config=TeamDiagnosticsSnapshotConfig(),
            market_slug="",
        )
    with pytest.raises(ValueError, match="forecast_id"):
        build_team_diagnostics_snapshot_report(
            bundle_report,
            config=TeamDiagnosticsSnapshotConfig(),
            forecast_id=123,  # type: ignore[arg-type]
        )

    object.__setattr__(bundle_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        build_team_diagnostics_snapshot_report(
            bundle_report,
            config=TeamDiagnosticsSnapshotConfig(),
        )


def test_snapshot_module_remains_pure_report_only_import_surface() -> None:
    tree = ast.parse(inspect.getsource(snapshot_module))
    forbidden_roots = {
        "dotenv",
        "http",
        "httpx",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(forbidden_roots)


def test_build_team_diagnostics_snapshot_report_reduces_bundle_summary_fields() -> None:
    report = build_team_diagnostics_snapshot_report(
        _bundle_report(),
        config=TeamDiagnosticsSnapshotConfig(config_version="snapshot-test-v0"),
        team_id="crypto_btc",
        market_slug="market-forecast-btc-1",
    )

    assert type(report) is TeamDiagnosticsSnapshotReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "snapshot-test-v0"
    assert report.source_config_version == "team-diagnostics-bundle-snapshot-test-v0"
    assert report.filters == (
        ("team_id", "crypto_btc"),
        ("market_slug", "market-forecast-btc-1"),
    )
    assert report.forecast_row_count == 3
    assert report.evidence_row_count == 3
    assert report.outcome_row_count == 3
    assert report.memory_eligible_reference_count == 2
    assert report.calibration_status == "validated"
    assert report.calibration_settled_count == 3
    assert report.calibration_group_count == 6
    assert report.event_template_row_count == 2
    assert report.event_template_status == "validated"
    assert report.source_reliability_row_count == 2
    assert report.source_reliability_missing_source_evidence_count == 0
    assert report.evidence_quality_status == "evidence_quality_pass"
    assert report.evidence_quality_pass_count == 3
    assert report.evidence_quality_watch_count == 0
    assert report.evidence_quality_blocked_count == 0
    assert report.evidence_quality_average_quality_score == d("0.900000")
    assert report.reason_codes == (
        "evidence_quality_complete",
        "min_settled_forecasts_met",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_no_float_values(report)
