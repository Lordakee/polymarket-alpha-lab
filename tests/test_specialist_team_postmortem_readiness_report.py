from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_postmortem_readiness_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_postmortem_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(
    *,
    settled_market_count: str = "3",
    outcome_evidence_ready: bool = True,
    forecast_error_bucket_ready: bool = True,
    source_family_feedback_ready: bool = True,
    team_memory_update_ready: bool = True,
    calibration_note_ready: bool = True,
    supabase_persistence_ready: bool = True,
) -> Any:
    module = api()
    return module.SpecialistTeamPostmortemReadinessInput(
        settled_market_count=d(settled_market_count),
        outcome_evidence_ready=outcome_evidence_ready,
        forecast_error_bucket_ready=forecast_error_bucket_ready,
        source_family_feedback_ready=source_family_feedback_ready,
        team_memory_update_ready=team_memory_update_ready,
        calibration_note_ready=calibration_note_ready,
        supabase_persistence_ready=supabase_persistence_ready,
    )


def build_report(row: Any | None = None) -> Any:
    module = api()
    return module.build_specialist_team_postmortem_readiness_report(
        row if row is not None else readiness_input(),
    )


def test_ready_report_exposes_public_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_POSTMORTEM_READINESS_CONFIG_VERSION",
        "SPECIALIST_TEAM_POSTMORTEM_REQUIRED_UPDATE_COUNT",
        "SpecialistTeamPostmortemReadinessInput",
        "SpecialistTeamPostmortemReadinessReport",
        "build_specialist_team_postmortem_readiness_report",
        "specialist_team_postmortem_readiness_report_payload",
        "specialist_team_postmortem_readiness_report_digest",
    )
    assert module.DEFAULT_SPECIALIST_TEAM_POSTMORTEM_READINESS_CONFIG_VERSION == (
        "specialist-team-postmortem-readiness-v0"
    )
    assert module.SPECIALIST_TEAM_POSTMORTEM_REQUIRED_UPDATE_COUNT == d("6.000000")
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.config_version == "specialist-team-postmortem-readiness-v0"
    assert report.settled_market_count == d("3.000000")
    assert report.postmortem_ready is True
    assert report.learning_update_count == d("6.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.specialist_team_postmortem_readiness_report_payload(report)
    assert payload["settled_market_count"] == "3.000000"
    assert payload["learning_update_count"] == "6.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["postmortem_ready"] is True
    assert payload["blocked_reason_codes"] == []
    assert payload["attention_reason_codes"] == []
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    expected_digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert report.digest == expected_digest
    assert module.specialist_team_postmortem_readiness_report_digest(report) == expected_digest


def test_blockers_and_attention_reasons_drive_readiness() -> None:
    report = build_report(
        readiness_input(
            settled_market_count="2",
            outcome_evidence_ready=False,
            forecast_error_bucket_ready=False,
            source_family_feedback_ready=True,
            team_memory_update_ready=False,
            calibration_note_ready=True,
            supabase_persistence_ready=False,
        ),
    )

    assert report.postmortem_ready is False
    assert report.learning_update_count == d("2.000000")
    assert report.ready_ratio == d("0.333333")
    assert report.blocked_reason_codes == ("supabase_persistence_not_ready",)
    assert report.attention_reason_codes == (
        "outcome_evidence_not_ready",
        "forecast_error_bucket_not_ready",
        "team_memory_update_not_ready",
    )
    assert report.public_payload["blocked_reason_codes"] == [
        "supabase_persistence_not_ready",
    ]
    assert report.public_payload["attention_reason_codes"] == [
        "outcome_evidence_not_ready",
        "forecast_error_bucket_not_ready",
        "team_memory_update_not_ready",
    ]


def test_no_settled_paper_events_blocks_postmortem() -> None:
    report = build_report(readiness_input(settled_market_count="0"))

    assert report.postmortem_ready is False
    assert report.learning_update_count == d("6.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ("no_settled_paper_events",)
    assert report.attention_reason_codes == ()


def test_frozen_decimal_only_and_hard_flags() -> None:
    module = api()
    report = build_report()

    for value in (readiness_input(), report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.ready_ratio = d("0.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="settled_market_count must be a Decimal"):
        module.SpecialistTeamPostmortemReadinessInput(
            settled_market_count=1,  # type: ignore[arg-type]
            outcome_evidence_ready=True,
            forecast_error_bucket_ready=True,
            source_family_feedback_ready=True,
            team_memory_update_ready=True,
            calibration_note_ready=True,
            supabase_persistence_ready=True,
        )

    with pytest.raises(ValueError, match="settled_market_count must be a whole Decimal"):
        readiness_input(settled_market_count="1.500000")

    with pytest.raises(ValueError, match="outcome_evidence_ready must be a bool"):
        readiness_input(outcome_evidence_ready=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(readiness_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="ready_ratio must match"):
        replace(report, ready_ratio=d("0.500000"))


def test_module_source_is_report_only_and_side_effect_free() -> None:
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
        "upsert",
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
        "trading",
        "auth",
        "token",
        "dsn",
        "secret",
        "private_key",
    ):
        assert forbidden not in lowered


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
