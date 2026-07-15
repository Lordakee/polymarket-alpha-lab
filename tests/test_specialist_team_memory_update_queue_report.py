from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_memory_update_queue_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_memory_update_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def queue_input(
    *,
    settled_feedback_ready: bool = True,
    postmortem_ready: bool = True,
    source_family_feedback_ready: bool = True,
    calibration_note_ready: bool = True,
    supabase_persistence_ready: bool = True,
    playbook_ready: bool = True,
    domain_risk_register_ready: bool = True,
) -> Any:
    module = api()
    return module.SpecialistTeamMemoryUpdateQueueInput(
        settled_feedback_ready=settled_feedback_ready,
        postmortem_ready=postmortem_ready,
        source_family_feedback_ready=source_family_feedback_ready,
        calibration_note_ready=calibration_note_ready,
        supabase_persistence_ready=supabase_persistence_ready,
        playbook_ready=playbook_ready,
        domain_risk_register_ready=domain_risk_register_ready,
    )


def build_report(**kwargs: bool) -> Any:
    module = api()
    return module.build_specialist_team_memory_update_queue_report(
        queue_input(**kwargs),
    )


def test_exports_defaults_and_paper_only_flags() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_CONFIG_VERSION",
        "SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_PRIORITY_BANDS",
        "SpecialistTeamMemoryUpdateQueueInput",
        "SpecialistTeamMemoryUpdateQueueReport",
        "build_specialist_team_memory_update_queue_report",
        "specialist_team_memory_update_queue_report_digest",
        "specialist_team_memory_update_queue_report_payload",
    )
    assert module.DEFAULT_SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_CONFIG_VERSION == (
        "specialist-team-memory-update-queue-report-v0"
    )
    assert module.SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_PRIORITY_BANDS == (
        "ready",
        "attention",
        "blocked",
    )

    readiness = queue_input()
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.SpecialistTeamMemoryUpdateQueueInput(
            settled_feedback_ready=True,
            postmortem_ready=True,
            source_family_feedback_ready=True,
            calibration_note_ready=True,
            supabase_persistence_ready=True,
            playbook_ready=True,
            domain_risk_register_ready=True,
            paper_only=False,
        )


def test_ready_report_has_public_payload_and_stable_digest() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.config_version == "specialist-team-memory-update-queue-report-v0"
    assert report.settled_feedback_ready is True
    assert report.postmortem_ready is True
    assert report.source_family_feedback_ready is True
    assert report.calibration_note_ready is True
    assert report.supabase_persistence_ready is True
    assert report.playbook_ready is True
    assert report.domain_risk_register_ready is True
    assert report.memory_update_queue_ready is True
    assert report.update_priority_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.ready_signal_count == d("7.000000")
    assert report.required_signal_count == d("7.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == api().specialist_team_memory_update_queue_report_payload(report)
    assert payload["ready_ratio"] == "1.000000"
    assert payload["ready_signal_count"] == "7.000000"
    assert payload["blocked_reason_codes"] == []
    assert "Decimal" not in repr(payload)
    json.dumps(payload, sort_keys=True)

    assert len(report.digest) == 64
    assert report.digest == api().specialist_team_memory_update_queue_report_digest(report)


def test_blocked_report_prioritizes_hard_queue_dependencies() -> None:
    report = build_report(
        settled_feedback_ready=False,
        postmortem_ready=False,
        supabase_persistence_ready=False,
        playbook_ready=False,
    )

    assert report.memory_update_queue_ready is False
    assert report.update_priority_band == "blocked"
    assert report.blocked_reason_codes == (
        "settled_feedback_not_ready",
        "postmortem_not_ready",
        "supabase_persistence_not_ready",
        "playbook_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.ready_signal_count == d("3.000000")
    assert report.ready_ratio == d("0.428571")


def test_attention_report_tracks_soft_memory_learning_inputs() -> None:
    report = build_report(
        source_family_feedback_ready=False,
        calibration_note_ready=False,
        domain_risk_register_ready=False,
    )

    assert report.memory_update_queue_ready is False
    assert report.update_priority_band == "attention"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "source_family_feedback_not_ready",
        "calibration_note_not_ready",
        "domain_risk_register_not_ready",
    )
    assert report.ready_signal_count == d("4.000000")
    assert report.ready_ratio == d("0.571429")


def test_validation_is_frozen_decimal_only_and_self_consistent() -> None:
    module = api()

    with pytest.raises(ValueError, match="settled_feedback_ready must be a bool"):
        module.SpecialistTeamMemoryUpdateQueueInput(
            settled_feedback_ready=1,  # type: ignore[arg-type]
            postmortem_ready=True,
            source_family_feedback_ready=True,
            calibration_note_ready=True,
            supabase_persistence_ready=True,
            playbook_ready=True,
            domain_risk_register_ready=True,
        )

    readiness = queue_input()
    with pytest.raises(FrozenInstanceError):
        readiness.postmortem_ready = False  # type: ignore[misc]

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.ready_ratio = d("0.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio="1.000000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="ready_ratio must match readiness components"):
        replace(report, ready_ratio=d("0.500000"))

    with pytest.raises(ValueError, match="blocked_reason_codes must match readiness components"):
        replace(report, blocked_reason_codes=("settled_feedback_not_ready",))

    with pytest.raises(ValueError, match="digest must match report payload"):
        replace(report, digest="0" * 64)


def test_module_source_is_read_only_report_only_and_side_effect_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "insert",
        "update ",
        "delete(",
        "post(",
        "put(",
    ):
        assert forbidden not in lowered
    for forbidden in (
        "wallet",
        "order",
        "trade",
        "sizing",
        "auth",
        "token",
        "dsn",
        "live",
    ):
        assert forbidden not in lowered
