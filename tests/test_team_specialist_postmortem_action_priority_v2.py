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
    / "team_specialist_postmortem_action_priority_v2.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_postmortem_action_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def action_item(
    *,
    team_id: str = "macro_rates",
    specialist_id: str = "inflation_researcher",
    action_item_id: str = "action-cpi-source-review",
    postmortem_id: str = "postmortem-cpi-surprise",
    action_opened_at: datetime = GENERATED_AT - timedelta(days=30),
    latest_evidence_at: datetime = GENERATED_AT - timedelta(days=21),
    calibration_error_ratio: str = "0.900000",
    forecast_miss_severity_ratio: str = "0.800000",
    source_failure_type: str = "resolution_source_missing",
    resolution_rule_missed: bool = True,
    upcoming_event_count: str = "7",
    public_memory_refs: tuple[str, ...] = ("public:cpi-postmortem-action",),
) -> Any:
    module = api()
    return module.TeamSpecialistPostmortemActionPriorityInputV2(
        team_id=team_id,
        specialist_id=specialist_id,
        action_item_id=action_item_id,
        postmortem_id=postmortem_id,
        action_opened_at=action_opened_at,
        latest_evidence_at=latest_evidence_at,
        calibration_error_ratio=d(calibration_error_ratio),
        forecast_miss_severity_ratio=d(forecast_miss_severity_ratio),
        source_failure_type=source_failure_type,
        resolution_rule_missed=resolution_rule_missed,
        upcoming_event_count=d(upcoming_event_count),
        public_memory_refs=public_memory_refs,
    )


def build_report(*rows: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_specialist_postmortem_action_priority_report_v2(
        rows,
        config=module.TeamSpecialistPostmortemActionPriorityReportV2Config(),
        generated_at=generated_at,
    )


def test_exports_and_default_config_are_readonly_phase_1_contract() -> None:
    module = api()
    config = module.TeamSpecialistPostmortemActionPriorityReportV2Config()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_CONFIG_VERSION",
        "TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_STATUSES",
        "TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_SOURCE_FAILURE_TYPES",
        "TeamSpecialistPostmortemActionPriorityReportV2Config",
        "TeamSpecialistPostmortemActionPriorityInputV2",
        "TeamSpecialistPostmortemActionPriorityRowV2",
        "TeamSpecialistPostmortemActionPriorityReportV2",
        "build_team_specialist_postmortem_action_priority_report_v2",
        "team_specialist_postmortem_action_priority_report_v2_payload",
    )
    assert config.config_version == "team-specialist-postmortem-action-priority-v2-phase-1"
    assert config.calibration_error_weight == d("0.200000")
    assert config.forecast_miss_severity_weight == d("0.200000")
    assert config.source_failure_weight == d("0.150000")
    assert config.resolution_rule_miss_weight == d("0.150000")
    assert config.evidence_staleness_weight == d("0.100000")
    assert config.unresolved_action_age_weight == d("0.100000")
    assert config.upcoming_event_load_weight == d("0.100000")
    assert config.stale_evidence_after_seconds == d("604800.000000")
    assert config.max_unresolved_action_age_seconds == d("2592000.000000")
    assert config.upcoming_event_load_block_count == d("5")
    assert config.watch_priority_score == d("0.350000")
    assert config.critical_priority_score == d("0.700000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistPostmortemActionPriorityReportV2Config(paper_only=False)


def test_report_prioritizes_postmortem_actions_across_all_risk_drivers() -> None:
    report = build_report(
        action_item(),
        action_item(
            team_id="weather_energy",
            specialist_id="grid_forecaster",
            action_item_id="action-heat-load-note",
            postmortem_id="postmortem-heat-load",
            action_opened_at=GENERATED_AT - timedelta(days=3),
            latest_evidence_at=GENERATED_AT - timedelta(days=1),
            calibration_error_ratio="0.200000",
            forecast_miss_severity_ratio="0.100000",
            source_failure_type="none",
            resolution_rule_missed=False,
            upcoming_event_count="1",
            public_memory_refs=("memory:heat-load-postmortem",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-specialist-postmortem-action-priority-v2-phase-1"
    assert report.team_count == d("2")
    assert report.specialist_team_count == d("2")
    assert report.action_item_count == d("2")
    assert report.critical_count == d("1")
    assert report.watch_count == d("0")
    assert report.clear_count == d("1")
    assert report.average_priority_score == d("0.515000")
    assert report.status == "critical"
    assert report.reason_codes == (
        "team_specialist_postmortem_action_priority_critical",
        "calibration_error",
        "forecast_miss_severity",
        "source_failure_resolution_source_missing",
        "resolution_rule_miss",
        "stale_evidence",
        "unresolved_action_age",
        "upcoming_event_load",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple((row.team_id, row.specialist_id, row.action_item_id) for row in report.priority_rows) == (
        ("macro_rates", "inflation_researcher", "action-cpi-source-review"),
        ("weather_energy", "grid_forecaster", "action-heat-load-note"),
    )
    assert report.priority_rows[0].priority_score == d("0.940000")
    assert report.priority_rows[0].row_status == "critical"
    assert report.priority_rows[0].evidence_age_seconds == d("1814400.000000")
    assert report.priority_rows[0].unresolved_action_age_seconds == d("2592000.000000")
    assert report.priority_rows[0].source_failure_component == d("1.000000")
    assert report.priority_rows[0].resolution_rule_miss_component == d("1.000000")
    assert report.priority_rows[0].evidence_staleness_component == d("1.000000")
    assert report.priority_rows[0].unresolved_action_age_component == d("1.000000")
    assert report.priority_rows[0].upcoming_event_load_component == d("1.000000")
    assert report.priority_rows[0].reason_codes == (
        "calibration_error",
        "forecast_miss_severity",
        "source_failure_resolution_source_missing",
        "resolution_rule_miss",
        "stale_evidence",
        "unresolved_action_age",
        "upcoming_event_load",
    )
    assert len(report.priority_rows[0].derived_validation_digest) == 64

    assert report.priority_rows[1].priority_score == d("0.090000")
    assert report.priority_rows[1].row_status == "clear"
    assert report.priority_rows[1].reason_codes == ("postmortem_action_priority_clear",)

    payload = api().team_specialist_postmortem_action_priority_report_v2_payload(report)
    payload_text = repr(payload).lower()
    assert payload["average_priority_score"] == "0.515000"
    assert payload["priority_rows"][0]["priority_score"] == "0.940000"
    assert payload["priority_rows"][0]["evidence_age_seconds"] == "1814400.000000"
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
    assert report.action_item_count == d("0")
    assert report.critical_count == d("0")
    assert report.watch_count == d("0")
    assert report.clear_count == d("0")
    assert report.average_priority_score == d("0.000000")
    assert report.status == "watch"
    assert report.reason_codes == ("team_specialist_postmortem_action_priority_empty_sources",)
    assert report.priority_rows == ()


def test_decimal_datetime_flag_public_safety_and_tamper_validations() -> None:
    module = api()

    with pytest.raises(ValueError, match="calibration_error_ratio must be a Decimal"):
        module.TeamSpecialistPostmortemActionPriorityInputV2(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            action_item_id="action-cpi-source-review",
            postmortem_id="postmortem-cpi-surprise",
            action_opened_at=GENERATED_AT,
            latest_evidence_at=GENERATED_AT,
            calibration_error_ratio=0.9,
            forecast_miss_severity_ratio=d("0.800000"),
            source_failure_type="resolution_source_missing",
            resolution_rule_missed=True,
            upcoming_event_count=d("7"),
            public_memory_refs=("public:cpi-postmortem-action",),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(action_item(), generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="action_opened_at must be timezone-aware"):
        action_item(action_opened_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="action_opened_at must be on or before generated_at"):
        build_report(action_item(action_opened_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="latest_evidence_at must be on or before generated_at"):
        build_report(action_item(latest_evidence_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="public_memory_refs must not be empty"):
        action_item(public_memory_refs=())

    with pytest.raises(ValueError, match="unsafe public value"):
        action_item(team_id=f"macro_{hidden_word('77616c6c6574')}")

    with pytest.raises(ValueError, match="unsafe public key"):
        module._reject_public_payload(  # noqa: SLF001
            "payload",
            {hidden_word("61757468"): "public-safe"},
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        action_item(public_memory_refs=(f"public:{hidden_word('7472616465')}-path",))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(action_item(), paper_only=False)

    with pytest.raises(FrozenInstanceError):
        action_item().calibration_error_ratio = d("0.100000")  # type: ignore[misc]

    report = build_report(action_item())
    with pytest.raises(FrozenInstanceError):
        report.status = "clear"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.priority_rows[0], priority_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_priority_score=d("0.123456"))


def test_source_scope_has_no_io_external_execution_or_unsafe_public_terms() -> None:
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
    ):
        assert forbidden not in lowered
