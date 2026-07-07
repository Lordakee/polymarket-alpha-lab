from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_learning_priority_report_v2.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_learning_priority_report_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def input_row(
    *,
    team_id: str = "macro_rates",
    specialist_id: str = "inflation_researcher",
    memory_key: str = "memory-cpi-surprise",
    observed_at: datetime = GENERATED_AT - timedelta(days=1),
    playbook_last_reviewed_at: datetime = GENERATED_AT - timedelta(days=5),
    forecast_error_ratio: str = "0.500000",
    source_family_count: str = "3",
    sample_count: str = "5",
    unresolved_postmortem_action_count: str = "0",
    public_memory_refs: tuple[str, ...] = ("public:macro-learning-note",),
) -> Any:
    module = api()
    return module.TeamSpecialistLearningPriorityInputV2(
        team_id=team_id,
        specialist_id=specialist_id,
        memory_key=memory_key,
        observed_at=observed_at,
        playbook_last_reviewed_at=playbook_last_reviewed_at,
        forecast_error_ratio=d(forecast_error_ratio),
        source_family_count=d(source_family_count),
        sample_count=d(sample_count),
        unresolved_postmortem_action_count=d(unresolved_postmortem_action_count),
        public_memory_refs=public_memory_refs,
    )


def build_report(*rows: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_specialist_learning_priority_report_v2(
        rows,
        config=module.TeamSpecialistLearningPriorityReportV2Config(),
        generated_at=generated_at,
    )


def test_exports_and_default_config_are_readonly_phase_1_contract() -> None:
    module = api()
    config = module.TeamSpecialistLearningPriorityReportV2Config()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_CONFIG_VERSION",
        "TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_STATUSES",
        "TeamSpecialistLearningPriorityReportV2Config",
        "TeamSpecialistLearningPriorityInputV2",
        "TeamSpecialistLearningPriorityRowV2",
        "TeamSpecialistLearningPriorityReportV2",
        "build_team_specialist_learning_priority_report_v2",
        "team_specialist_learning_priority_report_v2_payload",
    )
    assert config.config_version == "team-specialist-learning-priority-report-v2-phase-1"
    assert config.recent_error_weight == d("0.350000")
    assert config.stale_playbook_weight == d("0.200000")
    assert config.source_diversity_weight == d("0.150000")
    assert config.sample_size_weight == d("0.150000")
    assert config.postmortem_action_weight == d("0.150000")
    assert config.max_recent_error_age_seconds == d("604800.000000")
    assert config.max_playbook_age_seconds == d("1209600.000000")
    assert config.min_source_family_count == d("3")
    assert config.min_sample_count == d("5")
    assert config.watch_priority_score == d("0.300000")
    assert config.critical_priority_score == d("0.700000")
    assert config.unresolved_postmortem_action_block_count == d("3")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistLearningPriorityReportV2Config(paper_only=False)


def test_report_prioritizes_recent_error_stale_playbooks_sources_samples_and_actions() -> None:
    report = build_report(
        input_row(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            memory_key="memory-cpi-surprise",
            observed_at=GENERATED_AT - timedelta(days=1),
            playbook_last_reviewed_at=GENERATED_AT - timedelta(days=30),
            forecast_error_ratio="0.900000",
            source_family_count="1",
            sample_count="2",
            unresolved_postmortem_action_count="2",
            public_memory_refs=("public:macro-learning-note",),
        ),
        input_row(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            memory_key="memory-jobs-revision",
            observed_at=GENERATED_AT - timedelta(days=2),
            playbook_last_reviewed_at=GENERATED_AT - timedelta(days=20),
            forecast_error_ratio="0.600000",
            source_family_count="2",
            sample_count="4",
            unresolved_postmortem_action_count="1",
            public_memory_refs=("memory:jobs-revision-retro",),
        ),
        input_row(
            team_id="weather_energy",
            specialist_id="grid_forecaster",
            memory_key="memory-heat-load",
            observed_at=GENERATED_AT - timedelta(days=6),
            playbook_last_reviewed_at=GENERATED_AT - timedelta(days=8),
            forecast_error_ratio="0.300000",
            source_family_count="3",
            sample_count="5",
            unresolved_postmortem_action_count="0",
            public_memory_refs=("public:grid-load-review",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-specialist-learning-priority-report-v2-phase-1"
    assert report.team_count == d("2")
    assert report.specialist_team_count == d("2")
    assert report.memory_count == d("3")
    assert report.critical_count == d("1")
    assert report.watch_count == d("0")
    assert report.clear_count == d("1")
    assert report.average_priority_score == d("0.412500")
    assert report.status == "critical"
    assert report.reason_codes == (
        "team_specialist_learning_priority_critical",
        "recent_forecast_error",
        "stale_playbook",
        "low_source_diversity",
        "low_sample_size",
        "unresolved_postmortem_actions",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple((row.team_id, row.specialist_id) for row in report.priority_rows) == (
        ("macro_rates", "inflation_researcher"),
        ("weather_energy", "grid_forecaster"),
    )
    assert report.priority_rows[0].priority_score == d("0.810000")
    assert report.priority_rows[0].row_status == "critical"
    assert report.priority_rows[0].recent_forecast_error_component == d("0.771429")
    assert report.priority_rows[0].stale_playbook_component == d("1.000000")
    assert report.priority_rows[0].source_diversity_gap == d("0.666667")
    assert report.priority_rows[0].sample_size_gap == d("0.600000")
    assert report.priority_rows[0].postmortem_action_component == d("1.000000")
    assert report.priority_rows[0].reason_codes == (
        "recent_forecast_error",
        "stale_playbook",
        "low_source_diversity",
        "low_sample_size",
        "unresolved_postmortem_actions",
    )
    assert len(report.priority_rows[0].derived_validation_digest) == 64

    assert report.priority_rows[1].priority_score == d("0.015000")
    assert report.priority_rows[1].row_status == "clear"
    assert report.priority_rows[1].reason_codes == ("learning_priority_clear",)

    payload = api().team_specialist_learning_priority_report_v2_payload(report)
    payload_text = repr(payload).lower()
    assert payload["average_priority_score"] == "0.412500"
    assert payload["priority_rows"][0]["priority_score"] == "0.810000"
    assert payload["priority_rows"][0]["source_diversity_gap"] == "0.666667"
    assert payload["priority_rows"][0]["derived_validation_digest"] == (
        report.priority_rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "Decimal" not in payload_text
    json.dumps(payload)


def test_empty_report_is_watch_with_decimal_zero_public_numbers() -> None:
    report = build_report(generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=EASTERN))

    assert report.generated_at == GENERATED_AT
    assert report.team_count == d("0")
    assert report.specialist_team_count == d("0")
    assert report.memory_count == d("0")
    assert report.critical_count == d("0")
    assert report.watch_count == d("0")
    assert report.clear_count == d("0")
    assert report.average_priority_score == d("0.000000")
    assert report.status == "watch"
    assert report.reason_codes == ("team_specialist_learning_priority_empty_sources",)
    assert report.priority_rows == ()


def test_decimal_datetime_flag_public_safety_and_tamper_validations() -> None:
    module = api()

    with pytest.raises(ValueError, match="forecast_error_ratio must be a Decimal"):
        module.TeamSpecialistLearningPriorityInputV2(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            memory_key="memory-cpi-surprise",
            observed_at=GENERATED_AT,
            playbook_last_reviewed_at=GENERATED_AT,
            forecast_error_ratio=0.5,
            source_family_count=d("3"),
            sample_count=d("5"),
            unresolved_postmortem_action_count=d("0"),
            public_memory_refs=("public:macro-learning-note",),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(input_row(), generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be on or before generated_at"):
        build_report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="playbook_last_reviewed_at must be on or before generated_at"):
        build_report(
            input_row(playbook_last_reviewed_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(ValueError, match="public_memory_refs must not be empty"):
        input_row(public_memory_refs=())

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(team_id=f"macro_{hidden_word('77616c6c6574')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(public_memory_refs=(f"public:{hidden_word('627579')}-path",))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(input_row(), paper_only=False)

    with pytest.raises(FrozenInstanceError):
        input_row().forecast_error_ratio = d("0.100000")  # type: ignore[misc]

    report = build_report(input_row())
    with pytest.raises(FrozenInstanceError):
        report.status = "clear"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.priority_rows[0], priority_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_priority_score=d("0.123456"))


def test_source_scope_has_no_io_or_external_execution_surface() -> None:
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
