from __future__ import annotations

from datetime import datetime


def format_team_diagnostics_snapshot_history_gate_cli_stdout(report: object) -> str:
    return (
        "team-diagnostics-snapshot-history-gate: "
        f"gate_status={_string_value(getattr(report, 'gate_status'))} "
        f"recommended_next_step={_string_value(getattr(report, 'recommended_next_step'))} "
        f"source_config_version={_string_value(getattr(report, 'source_config_version'))} "
        f"source_generated_at={_string_value(getattr(report, 'source_generated_at'))} "
        f"source_snapshot_count={_string_value(getattr(report, 'source_snapshot_count'))} "
        "source_required_snapshot_count="
        f"{_string_value(getattr(report, 'source_required_snapshot_count'))} "
        f"source_status={_string_value(getattr(report, 'source_status'))} "
        f"source_span_seconds={_string_value(getattr(report, 'source_span_seconds'))} "
        f"source_status_counts={_status_counts_value(getattr(report, 'source_status_counts'))} "
        f"source_reason_codes={_reason_codes_value(getattr(report, 'source_reason_codes'))} "
        f"latest_snapshot_age_seconds={_string_value(getattr(report, 'latest_snapshot_age_seconds'))} "
        f"reason_code_counts={_reason_code_counts_value(getattr(report, 'reason_code_counts'))} "
        "evidence_quality_average_delta="
        f"{_string_value(getattr(report, 'evidence_quality_average_delta'))} "
        f"memory_eligible_delta={_string_value(getattr(report, 'memory_eligible_delta'))} "
        f"settled_calibration_delta={_string_value(getattr(report, 'settled_calibration_delta'))} "
        "duplicate_latest_generated_at="
        f"{_string_value(getattr(report, 'duplicate_latest_generated_at'))} "
        f"reason_codes={_reason_codes_value(getattr(report, 'reason_codes'))} "
        f"paper_only={_string_value(getattr(report, 'paper_only'))} "
        f"report_only={_string_value(getattr(report, 'report_only'))} "
        f"readonly={_string_value(getattr(report, 'readonly'))}\n"
    )


def _string_value(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _status_counts_value(status_counts: object) -> str:
    if status_counts is None:
        return "none"
    values = tuple(status_counts)
    if not values:
        return "none"
    return ",".join(f"{status}:{count}" for status, count in values)


def _reason_code_counts_value(reason_code_counts: object) -> str:
    if reason_code_counts is None:
        return "none"
    values = tuple(reason_code_counts)
    if not values:
        return "none"
    return ",".join(
        f"{_reason_code_value(row)}:{_reason_count_value(row)}" for row in values
    )


def _reason_code_value(row: object) -> str:
    if isinstance(row, dict):
        return str(row.get("reason_code", row.get("reason", "none")))
    if isinstance(row, tuple) and len(row) >= 2:
        return str(row[0])
    return str(getattr(row, "reason_code", getattr(row, "reason", "none")))


def _reason_count_value(row: object) -> str:
    if isinstance(row, dict):
        return str(row.get("report_count", row.get("count", "none")))
    if isinstance(row, tuple) and len(row) >= 2:
        return str(row[1])
    return str(getattr(row, "report_count", getattr(row, "count", "none")))


def _reason_codes_value(reason_codes: object) -> str:
    if reason_codes is None:
        return "none"
    values = tuple(reason_codes)
    if not values:
        return "none"
    return ",".join(str(reason_code) for reason_code in values)


__all__ = ("format_team_diagnostics_snapshot_history_gate_cli_stdout",)
