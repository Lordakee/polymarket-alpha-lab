from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_outcome_learning_priority_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_outcome_learning_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def learning_task(
    *,
    team_label: str = "macro_rates",
    specialist_label: str = "inflation_research",
    learning_task_label: str = "outcome_error_review",
    aggregate_forecast_error: str = "0.900000",
    evidence_miss_rate: str = "0.750000",
    calibration_drift: str = "0.800000",
    memory_staleness_ratio: str = "0.700000",
    domain_coverage_ratio: str = "0.200000",
    aggregate_sample_count: str = "12",
) -> Any:
    module = api()
    return module.ResearchTeamOutcomeLearningPriorityInput(
        team_label=team_label,
        specialist_label=specialist_label,
        learning_task_label=learning_task_label,
        aggregate_forecast_error=d(aggregate_forecast_error),
        evidence_miss_rate=d(evidence_miss_rate),
        calibration_drift=d(calibration_drift),
        memory_staleness_ratio=d(memory_staleness_ratio),
        domain_coverage_ratio=d(domain_coverage_ratio),
        aggregate_sample_count=d(aggregate_sample_count),
    )


def build_report(*rows: Any) -> Any:
    module = api()
    return module.build_research_team_outcome_learning_priority_report(
        rows,
        config=module.ResearchTeamOutcomeLearningPriorityConfig(),
        generated_at=GENERATED_AT,
    )


def test_exports_config_and_status_contract_are_report_only() -> None:
    module = api()
    config = module.ResearchTeamOutcomeLearningPriorityConfig()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_CONFIG_VERSION",
        "RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_STATUSES",
        "ResearchTeamOutcomeLearningPriorityConfig",
        "ResearchTeamOutcomeLearningPriorityInput",
        "ResearchTeamOutcomeLearningPriorityRow",
        "ResearchTeamOutcomeLearningPriorityReport",
        "build_research_team_outcome_learning_priority_report",
        "research_team_outcome_learning_priority_report_payload",
        "validate_research_team_outcome_learning_priority_report_payload",
    )
    assert module.RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert config.config_version == "research-team-outcome-learning-priority-v0"
    assert config.forecast_error_weight == d("0.200000")
    assert config.evidence_miss_weight == d("0.200000")
    assert config.calibration_drift_weight == d("0.200000")
    assert config.memory_staleness_weight == d("0.200000")
    assert config.domain_coverage_gap_weight == d("0.200000")
    assert config.watch_priority_score == d("0.350000")
    assert config.block_priority_score == d("0.700000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert len(config.derived_validation_digest) == 64

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamOutcomeLearningPriorityConfig(paper_only=False)

    with pytest.raises(ValueError, match="forecast_error_weight must be a Decimal"):
        module.ResearchTeamOutcomeLearningPriorityConfig(
            forecast_error_weight=0.2,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="statuses must be pass, watch, or block"):
        module.ResearchTeamOutcomeLearningPriorityRow(
            team_label="macro_rates",
            specialist_label="inflation_research",
            learning_task_label="outcome_error_review",
            aggregate_sample_count=d("1"),
            aggregate_forecast_error=d("0.100000"),
            evidence_miss_rate=d("0.100000"),
            calibration_drift=d("0.100000"),
            memory_staleness_ratio=d("0.100000"),
            domain_coverage_ratio=d("0.900000"),
            domain_coverage_gap=d("0.100000"),
            priority_score=d("0.100000"),
            status="clear",
            reason_codes=("outcome_learning_priority_pass",),
            derived_validation_digest="0" * 64,
        )


def test_report_prioritizes_public_safe_outcome_learning_tasks() -> None:
    report = build_report(
        learning_task(),
        learning_task(
            team_label="weather_energy",
            specialist_label="load_research",
            learning_task_label="coverage_refresh",
            aggregate_forecast_error="0.100000",
            evidence_miss_rate="0.050000",
            calibration_drift="0.050000",
            memory_staleness_ratio="0.100000",
            domain_coverage_ratio="0.900000",
            aggregate_sample_count="5",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-outcome-learning-priority-v0"
    assert report.team_count == d("2")
    assert report.specialist_count == d("2")
    assert report.learning_task_count == d("2")
    assert report.block_count == d("1")
    assert report.watch_count == d("0")
    assert report.pass_count == d("1")
    assert report.average_priority_score == d("0.435000")
    assert report.max_priority_score == d("0.790000")
    assert report.status == "block"
    assert report.reason_codes == (
        "outcome_learning_priority_block",
        "aggregate_forecast_error",
        "evidence_miss_rate",
        "calibration_drift",
        "memory_staleness",
        "domain_coverage_gap",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.team_label for row in report.priority_rows) == (
        "macro_rates",
        "weather_energy",
    )
    assert report.priority_rows[0].priority_score == d("0.790000")
    assert report.priority_rows[0].status == "block"
    assert report.priority_rows[0].domain_coverage_gap == d("0.800000")
    assert report.priority_rows[0].reason_codes == (
        "aggregate_forecast_error",
        "evidence_miss_rate",
        "calibration_drift",
        "memory_staleness",
        "domain_coverage_gap",
    )
    assert len(report.priority_rows[0].derived_validation_digest) == 64
    assert report.priority_rows[1].priority_score == d("0.080000")
    assert report.priority_rows[1].status == "pass"
    assert report.priority_rows[1].reason_codes == ("outcome_learning_priority_pass",)

    payload = api().research_team_outcome_learning_priority_report_payload(report)
    assert payload["average_priority_score"] == "0.435000"
    assert payload["priority_rows"][0]["priority_score"] == "0.790000"
    assert payload["priority_rows"][0]["domain_coverage_gap"] == "0.800000"
    assert payload["priority_rows"][0]["derived_validation_digest"] == (
        report.priority_rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert api().validate_research_team_outcome_learning_priority_report_payload(payload)
    json.dumps(payload, sort_keys=True)


def test_payload_and_digest_are_deterministic_without_raw_external_identifiers() -> None:
    first = build_report(
        learning_task(),
        learning_task(
            team_label="weather_energy",
            specialist_label="load_research",
            learning_task_label="coverage_refresh",
            aggregate_forecast_error="0.100000",
            evidence_miss_rate="0.050000",
            calibration_drift="0.050000",
            memory_staleness_ratio="0.100000",
            domain_coverage_ratio="0.900000",
            aggregate_sample_count="5",
        ),
    )
    second = build_report(
        learning_task(
            team_label="weather_energy",
            specialist_label="load_research",
            learning_task_label="coverage_refresh",
            aggregate_forecast_error="0.100000",
            evidence_miss_rate="0.050000",
            calibration_drift="0.050000",
            memory_staleness_ratio="0.100000",
            domain_coverage_ratio="0.900000",
            aggregate_sample_count="5",
        ),
        learning_task(),
    )

    first_payload = api().research_team_outcome_learning_priority_report_payload(first)
    second_payload = api().research_team_outcome_learning_priority_report_payload(second)
    payload_text = json.dumps(first_payload, sort_keys=True).lower()

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert "decimal" not in repr(first_payload).lower()
    for forbidden in ("event_id", "market_slug", "condition_id", "source_id"):
        assert forbidden not in payload_text


def test_empty_report_and_validation_failures_are_public_safe() -> None:
    module = api()

    empty = build_report()
    assert empty.status == "pass"
    assert empty.team_count == d("0")
    assert empty.specialist_count == d("0")
    assert empty.learning_task_count == d("0")
    assert empty.average_priority_score == d("0.000000")
    assert empty.max_priority_score == d("0.000000")
    assert empty.reason_codes == ("outcome_learning_priority_pass",)
    assert empty.priority_rows == ()

    with pytest.raises(ValueError, match="aggregate_forecast_error must be a Decimal"):
        module.ResearchTeamOutcomeLearningPriorityInput(
            team_label="macro_rates",
            specialist_label="inflation_research",
            learning_task_label="outcome_error_review",
            aggregate_forecast_error=0.9,  # type: ignore[arg-type]
            evidence_miss_rate=d("0.750000"),
            calibration_drift=d("0.800000"),
            memory_staleness_ratio=d("0.700000"),
            domain_coverage_ratio=d("0.200000"),
            aggregate_sample_count=d("12"),
        )

    with pytest.raises(ValueError, match="aggregate_sample_count must be a whole Decimal"):
        learning_task(aggregate_sample_count="1.500000")

    with pytest.raises(ValueError, match="unsafe public value"):
        learning_task(team_label=f"macro_{hidden_word('77616c6c6574')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        learning_task(learning_task_label=f"review_{hidden_word('7472616465')}")

    with pytest.raises(ValueError, match="duplicate outcome learning key"):
        build_report(learning_task(), learning_task())

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(learning_task(), paper_only=False)

    with pytest.raises(FrozenInstanceError):
        learning_task().aggregate_forecast_error = d("0.100000")  # type: ignore[misc]

    report = build_report(learning_task())
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(report.priority_rows[0], priority_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(report, average_priority_score=d("0.123456"))


def test_module_source_is_report_only_and_side_effect_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "send",
        "post(",
        "put(",
        "delete(",
    ):
        assert forbidden not in lowered
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in lowered
