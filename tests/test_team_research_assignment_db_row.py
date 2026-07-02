from __future__ import annotations

from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import importlib
import json
import sys
import types
from typing import Any

import pytest

from polymarket_alpha_lab.team_research_assignment import (
    NEXT_STEPS,
    READY_REPORT_REASON_CODE,
    TeamResearchAssignmentReport,
    TeamResearchAssignmentRow,
    TeamResearchAssignmentTeamSummary,
)


DB_ROW_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_db_row"


@pytest.fixture()
def db_row_module() -> types.ModuleType:
    sys.modules.pop(DB_ROW_MODULE_NAME, None)
    return importlib.import_module(DB_ROW_MODULE_NAME)


def _assignment_row(**overrides: Any) -> TeamResearchAssignmentRow:
    values: dict[str, Any] = {
        "research_rank": 1,
        "market_slug": "btc-alpha",
        "question": "Will Bitcoin trade above alpha by resolution?",
        "selected_side": "yes",
        "scoring_side": "yes",
        "team_id": "crypto_btc",
        "category_id": "crypto",
        "routing_confidence": Decimal("0.920000"),
        "secondary_team_ids": ("crypto_macro",),
        "queue_research_status": "ready",
        "queue_research_bucket": "crypto",
        "queue_readiness_status": "ready",
        "memory_readiness_status": "pass",
        "memory_use_policy": "allow",
        "assignment_status": "assigned",
        "assignment_reason_codes": ("team_research_assignment_assigned",),
        "evidence_gap_codes": ("needs_resolution_context",),
        "source_reason_codes": ("source_queue_ready",),
    }
    values.update(overrides)
    return TeamResearchAssignmentRow(**values)


def _team_summary(**overrides: Any) -> TeamResearchAssignmentTeamSummary:
    values: dict[str, Any] = {
        "team_id": "crypto_btc",
        "assignment_count": 1,
        "assigned_count": 1,
        "watch_count": 0,
        "blocked_count": 0,
        "memory_readiness_status": "pass",
        "memory_use_policy": "allow",
    }
    values.update(overrides)
    return TeamResearchAssignmentTeamSummary(**values)


def _report(**overrides: Any) -> TeamResearchAssignmentReport:
    row = overrides.pop("row", _assignment_row())
    values: dict[str, Any] = {
        "generated_at": datetime(2026, 7, 1, 12, 30, tzinfo=timezone(timedelta(hours=-4))),
        "config_version": "team-research-assignment-test-v0",
        "source_queue_config_version": "queue-source-test-v0",
        "source_route_config_version": "route-source-test-v0",
        "source_memory_config_version": "memory-source-test-v0",
        "assignment_status": "ready",
        "recommended_next_step": NEXT_STEPS["ready"],
        "assignment_count": 1,
        "assigned_count": 1,
        "watch_count": 0,
        "blocked_count": 0,
        "team_summaries": (_team_summary(),),
        "rows": (row,),
        "reason_codes": (READY_REPORT_REASON_CODE,),
    }
    values.update(overrides)
    return TeamResearchAssignmentReport(**values)


def _expected_payload(report: TeamResearchAssignmentReport) -> dict[str, Any]:
    row = report.rows[0]
    summary = report.team_summaries[0]
    return {
        "generated_at": report.generated_at.astimezone(UTC).isoformat(),
        "config_version": report.config_version,
        "source_queue_config_version": report.source_queue_config_version,
        "source_route_config_version": report.source_route_config_version,
        "source_memory_config_version": report.source_memory_config_version,
        "assignment_status": report.assignment_status,
        "recommended_next_step": report.recommended_next_step,
        "assignment_count": report.assignment_count,
        "assigned_count": report.assigned_count,
        "watch_count": report.watch_count,
        "blocked_count": report.blocked_count,
        "team_summaries": [
            {
                "team_id": summary.team_id,
                "assignment_count": summary.assignment_count,
                "assigned_count": summary.assigned_count,
                "watch_count": summary.watch_count,
                "blocked_count": summary.blocked_count,
                "memory_readiness_status": summary.memory_readiness_status,
                "memory_use_policy": summary.memory_use_policy,
                "paper_only": summary.paper_only,
                "report_only": summary.report_only,
                "readonly": summary.readonly,
            },
        ],
        "rows": [
            {
                "research_rank": row.research_rank,
                "market_slug": row.market_slug,
                "question": row.question,
                "selected_side": row.selected_side,
                "scoring_side": row.scoring_side,
                "team_id": row.team_id,
                "category_id": row.category_id,
                "routing_confidence": str(row.routing_confidence),
                "secondary_team_ids": list(row.secondary_team_ids),
                "queue_research_status": row.queue_research_status,
                "queue_research_bucket": row.queue_research_bucket,
                "queue_readiness_status": row.queue_readiness_status,
                "memory_readiness_status": row.memory_readiness_status,
                "memory_use_policy": row.memory_use_policy,
                "assignment_status": row.assignment_status,
                "assignment_reason_codes": list(row.assignment_reason_codes),
                "evidence_gap_codes": list(row.evidence_gap_codes),
                "source_reason_codes": list(row.source_reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            },
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _sha256(payload_json: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload_json,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _row_kwargs_from_report(
    db_row_module: types.ModuleType,
    report: TeamResearchAssignmentReport,
) -> dict[str, Any]:
    row = db_row_module.team_research_assignment_report_to_db_row(report)
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "source_queue_config_version": row.source_queue_config_version,
        "source_route_config_version": row.source_route_config_version,
        "source_memory_config_version": row.source_memory_config_version,
        "assignment_status": row.assignment_status,
        "assignment_count": row.assignment_count,
        "assigned_count": row.assigned_count,
        "watch_count": row.watch_count,
        "blocked_count": row.blocked_count,
        "reason_codes_json": row.reason_codes_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def test_assignment_report_to_db_row_hash_round_trips_and_payload_is_canonical(
    db_row_module: types.ModuleType,
) -> None:
    report = _report()

    row = db_row_module.team_research_assignment_report_to_db_row(report)

    expected_payload = _expected_payload(report)
    assert row.report_sha256 == _sha256(expected_payload)
    assert row.generated_at == datetime(2026, 7, 1, 16, 30, tzinfo=UTC)
    assert row.config_version == "team-research-assignment-test-v0"
    assert row.source_queue_config_version == "queue-source-test-v0"
    assert row.source_route_config_version == "route-source-test-v0"
    assert row.source_memory_config_version == "memory-source-test-v0"
    assert row.assignment_status == "ready"
    assert row.assignment_count == 1
    assert row.assigned_count == 1
    assert row.watch_count == 0
    assert row.blocked_count == 0
    assert row.reason_codes_json == ["team_research_assignment_ready"]
    assert row.payload_json == expected_payload
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    recovered = db_row_module.team_research_assignment_report_from_db_row(row)

    assert recovered == report
    assert db_row_module.to_db_row(report) == row
    assert db_row_module.from_db_row(row) == report


def test_db_row_copies_json_inputs_without_retaining_mutable_references(
    db_row_module: types.ModuleType,
) -> None:
    kwargs = _row_kwargs_from_report(db_row_module, _report())
    payload = dict(kwargs["payload_json"])
    payload["reason_codes"] = list(payload["reason_codes"])
    payload["rows"] = [dict(payload["rows"][0])]
    payload["rows"][0]["assignment_reason_codes"] = list(
        payload["rows"][0]["assignment_reason_codes"],
    )
    payload["team_summaries"] = [dict(payload["team_summaries"][0])]
    reason_codes_json = list(kwargs["reason_codes_json"])

    row = db_row_module.TeamResearchAssignmentDbRow(
        **{
            **kwargs,
            "reason_codes_json": reason_codes_json,
            "payload_json": payload,
        },
    )
    payload["reason_codes"].append("late_mutation")
    payload["rows"][0]["assignment_reason_codes"].append("late_mutation")
    payload["team_summaries"][0]["team_id"] = "late_mutation"
    reason_codes_json.append("late_mutation")

    assert row.payload_json["reason_codes"] == ["team_research_assignment_ready"]
    assert row.payload_json["rows"][0]["assignment_reason_codes"] == [
        "team_research_assignment_assigned",
    ]
    assert row.payload_json["team_summaries"][0]["team_id"] == "crypto_btc"
    assert row.reason_codes_json == ["team_research_assignment_ready"]


def test_db_row_rejects_false_hard_flags_in_report_row_and_payload(
    db_row_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="readonly"):
        db_row_module.team_research_assignment_report_to_db_row(
            _report(readonly=False),
        )

    kwargs = _row_kwargs_from_report(db_row_module, _report())
    with pytest.raises(ValueError, match="paper_only"):
        db_row_module.TeamResearchAssignmentDbRow(
            **{
                **kwargs,
                "paper_only": False,
            },
        )

    bad_payload = dict(kwargs["payload_json"])
    bad_payload["rows"] = [dict(bad_payload["rows"][0])]
    bad_payload["rows"][0]["report_only"] = False

    with pytest.raises(ValueError, match="report_only"):
        db_row_module.TeamResearchAssignmentDbRow(
            **{
                **kwargs,
                "report_sha256": _sha256(bad_payload),
                "payload_json": bad_payload,
            },
        )


def test_db_row_rejects_payload_that_changes_materialized_values(
    db_row_module: types.ModuleType,
) -> None:
    kwargs = _row_kwargs_from_report(db_row_module, _report())
    changed_payload = dict(kwargs["payload_json"])
    changed_payload["assignment_count"] = kwargs["assignment_count"] + 1

    with pytest.raises(ValueError, match="assignment_count"):
        db_row_module.TeamResearchAssignmentDbRow(
            **{
                **kwargs,
                "report_sha256": _sha256(changed_payload),
                "payload_json": changed_payload,
            },
        )


def test_db_row_rejects_naive_generated_at(
    db_row_module: types.ModuleType,
) -> None:
    kwargs = _row_kwargs_from_report(db_row_module, _report())

    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        db_row_module.TeamResearchAssignmentDbRow(
            **{
                **kwargs,
                "generated_at": datetime(2026, 7, 1, 16, 30),
            },
        )


def test_db_row_rejects_float_and_decimal_json_payload_inputs(
    db_row_module: types.ModuleType,
) -> None:
    kwargs = _row_kwargs_from_report(db_row_module, _report())
    assert kwargs["payload_json"]["rows"][0]["routing_confidence"] == "0.920000"

    decimal_payload = dict(kwargs["payload_json"])
    decimal_payload["rows"] = [dict(decimal_payload["rows"][0])]
    decimal_payload["rows"][0]["routing_confidence"] = Decimal("0.920000")

    with pytest.raises(ValueError, match="Decimal"):
        db_row_module.TeamResearchAssignmentDbRow(
            **{
                **kwargs,
                "payload_json": decimal_payload,
            },
        )

    float_payload = dict(kwargs["payload_json"])
    float_payload["rows"] = [dict(float_payload["rows"][0])]
    float_payload["rows"][0]["routing_confidence"] = 0.92

    with pytest.raises(ValueError, match="float"):
        db_row_module.TeamResearchAssignmentDbRow(
            **{
                **kwargs,
                "payload_json": float_payload,
            },
        )
