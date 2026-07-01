from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import importlib
import json
import sys
import types
from typing import Any

import pytest

from polymarket_alpha_lab.team_diagnostics_snapshot import TeamDiagnosticsSnapshotReport


DB_ROW_MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot_db_row"


@pytest.fixture()
def db_row_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    sys.modules.pop(DB_ROW_MODULE_NAME, None)
    return importlib.import_module(DB_ROW_MODULE_NAME)


def _report(**overrides: Any) -> TeamDiagnosticsSnapshotReport:
    values: dict[str, Any] = {
        "generated_at": datetime(2026, 7, 1, 12, 30, tzinfo=timezone(timedelta(hours=-4))),
        "config_version": "team-diagnostics-snapshot-test-v0",
        "source_config_version": "team-diagnostics-bundle-v0",
        "filters": (
            ("team_id", "crypto_btc"),
            ("market_slug", "bitcoin-above-120k"),
            ("forecast_id", "forecast-btc-1"),
        ),
        "forecast_row_count": 3,
        "evidence_row_count": 5,
        "outcome_row_count": 1,
        "memory_eligible_reference_count": 1,
        "calibration_status": "calibration_watch",
        "calibration_settled_count": 3,
        "calibration_group_count": 2,
        "event_template_row_count": 4,
        "event_template_status": "event_template_pass",
        "source_reliability_row_count": 6,
        "source_reliability_missing_source_evidence_count": 1,
        "evidence_quality_status": "evidence_quality_watch",
        "evidence_quality_pass_count": 3,
        "evidence_quality_watch_count": 2,
        "evidence_quality_blocked_count": 0,
        "evidence_quality_average_quality_score": Decimal("0.740000"),
        "reason_codes": ("calibration_watch", "evidence_quality_watch"),
    }
    values.update(overrides)
    return TeamDiagnosticsSnapshotReport(**values)


def _expected_payload(report: TeamDiagnosticsSnapshotReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.astimezone(UTC).isoformat(),
        "config_version": report.config_version,
        "source_config_version": report.source_config_version,
        "filters": [list(item) for item in report.filters],
        "forecast_row_count": report.forecast_row_count,
        "evidence_row_count": report.evidence_row_count,
        "outcome_row_count": report.outcome_row_count,
        "memory_eligible_reference_count": report.memory_eligible_reference_count,
        "calibration_status": report.calibration_status,
        "calibration_settled_count": report.calibration_settled_count,
        "calibration_group_count": report.calibration_group_count,
        "event_template_row_count": report.event_template_row_count,
        "event_template_status": report.event_template_status,
        "source_reliability_row_count": report.source_reliability_row_count,
        "source_reliability_missing_source_evidence_count": (
            report.source_reliability_missing_source_evidence_count
        ),
        "evidence_quality_status": report.evidence_quality_status,
        "evidence_quality_pass_count": report.evidence_quality_pass_count,
        "evidence_quality_watch_count": report.evidence_quality_watch_count,
        "evidence_quality_blocked_count": report.evidence_quality_blocked_count,
        "evidence_quality_average_quality_score": str(
            report.evidence_quality_average_quality_score,
        ),
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
    report: TeamDiagnosticsSnapshotReport,
) -> dict[str, Any]:
    row = db_row_module.team_diagnostics_snapshot_report_to_db_row(report)
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "source_config_version": row.source_config_version,
        "team_id": row.team_id,
        "market_slug": row.market_slug,
        "forecast_id": row.forecast_id,
        "forecast_row_count": row.forecast_row_count,
        "evidence_row_count": row.evidence_row_count,
        "outcome_row_count": row.outcome_row_count,
        "memory_eligible_reference_count": row.memory_eligible_reference_count,
        "calibration_status": row.calibration_status,
        "calibration_settled_count": row.calibration_settled_count,
        "calibration_group_count": row.calibration_group_count,
        "event_template_row_count": row.event_template_row_count,
        "event_template_status": row.event_template_status,
        "source_reliability_row_count": row.source_reliability_row_count,
        "source_reliability_missing_source_evidence_count": (
            row.source_reliability_missing_source_evidence_count
        ),
        "evidence_quality_status": row.evidence_quality_status,
        "evidence_quality_pass_count": row.evidence_quality_pass_count,
        "evidence_quality_watch_count": row.evidence_quality_watch_count,
        "evidence_quality_blocked_count": row.evidence_quality_blocked_count,
        "evidence_quality_average_quality_score": (
            row.evidence_quality_average_quality_score
        ),
        "reason_codes_json": row.reason_codes_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def test_snapshot_report_to_db_row_hash_round_trips_and_payload_is_canonical(
    db_row_module: types.ModuleType,
) -> None:
    report = _report()

    row = db_row_module.team_diagnostics_snapshot_report_to_db_row(report)

    expected_payload = _expected_payload(report)
    assert row.report_sha256 == _sha256(expected_payload)
    assert row.generated_at == datetime(2026, 7, 1, 16, 30, tzinfo=UTC)
    assert row.config_version == "team-diagnostics-snapshot-test-v0"
    assert row.source_config_version == "team-diagnostics-bundle-v0"
    assert row.team_id == "crypto_btc"
    assert row.market_slug == "bitcoin-above-120k"
    assert row.forecast_id == "forecast-btc-1"
    assert row.forecast_row_count == 3
    assert row.evidence_quality_average_quality_score == Decimal("0.740000")
    assert row.reason_codes_json == ["calibration_watch", "evidence_quality_watch"]
    assert row.payload_json == expected_payload

    recovered = db_row_module.team_diagnostics_snapshot_report_from_db_row(row)

    assert recovered == replace(report, generated_at=datetime(2026, 7, 1, 16, 30, tzinfo=UTC))


def test_snapshot_db_row_accepts_empty_reason_codes(
    db_row_module: types.ModuleType,
) -> None:
    report = _report(reason_codes=())

    row = db_row_module.team_diagnostics_snapshot_report_to_db_row(report)

    assert row.reason_codes_json == []
    assert row.payload_json["reason_codes"] == []
    assert db_row_module.team_diagnostics_snapshot_report_from_db_row(row) == replace(
        report,
        generated_at=datetime(2026, 7, 1, 16, 30, tzinfo=UTC),
    )


def test_db_row_copies_json_inputs_without_retaining_mutable_references(
    db_row_module: types.ModuleType,
) -> None:
    report = _report()
    kwargs = _row_kwargs_from_report(db_row_module, report)
    payload = dict(kwargs["payload_json"])
    payload["filters"] = [list(item) for item in payload["filters"]]
    payload["reason_codes"] = list(payload["reason_codes"])
    reason_codes_json = list(kwargs["reason_codes_json"])

    row = db_row_module.TeamDiagnosticsSnapshotDbRow(
        **{
            **kwargs,
            "reason_codes_json": reason_codes_json,
            "payload_json": payload,
        },
    )
    payload["filters"][0][1] = "late_mutation"
    payload["reason_codes"].append("late_mutation")
    reason_codes_json.append("late_mutation")

    assert row.payload_json["filters"] == [
        ["team_id", "crypto_btc"],
        ["market_slug", "bitcoin-above-120k"],
        ["forecast_id", "forecast-btc-1"],
    ]
    assert row.payload_json["reason_codes"] == [
        "calibration_watch",
        "evidence_quality_watch",
    ]
    assert row.reason_codes_json == [
        "calibration_watch",
        "evidence_quality_watch",
    ]


def test_db_row_rejects_false_hard_flags_in_report_and_payload(
    db_row_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="readonly"):
        db_row_module.team_diagnostics_snapshot_report_to_db_row(
            _report(readonly=False),
        )

    kwargs = _row_kwargs_from_report(db_row_module, _report())
    bad_payload = dict(kwargs["payload_json"])
    bad_payload["report_only"] = False

    with pytest.raises(ValueError, match="report_only"):
        db_row_module.TeamDiagnosticsSnapshotDbRow(
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
    changed_payload["forecast_row_count"] = kwargs["forecast_row_count"] + 1

    with pytest.raises(ValueError, match="forecast_row_count"):
        db_row_module.TeamDiagnosticsSnapshotDbRow(
            **{
                **kwargs,
                "report_sha256": _sha256(changed_payload),
                "payload_json": changed_payload,
            },
        )
