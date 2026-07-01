from __future__ import annotations

from datetime import datetime


def format_team_diagnostics_snapshot_history_cli_stdout(report: object) -> str:
    return (
        "team-diagnostics-snapshot-history: "
        f"status={_string_value(getattr(report, 'status'))} "
        f"snapshot_count={_string_value(getattr(report, 'snapshot_count'))} "
        f"required_snapshot_count={_string_value(getattr(report, 'required_snapshot_count'))} "
        f"earliest_generated_at={_string_value(getattr(report, 'earliest_generated_at'))} "
        f"latest_generated_at={_string_value(getattr(report, 'latest_generated_at'))} "
        f"span_seconds={_string_value(getattr(report, 'span_seconds'))} "
        f"status_counts={_status_counts_value(getattr(report, 'status_counts'))} "
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


def _reason_codes_value(reason_codes: object) -> str:
    if reason_codes is None:
        return "none"
    values = tuple(reason_codes)
    if not values:
        return "none"
    return ",".join(str(reason_code) for reason_code in values)


__all__ = ("format_team_diagnostics_snapshot_history_cli_stdout",)
