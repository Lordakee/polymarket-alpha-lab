from __future__ import annotations

from datetime import datetime


def format_team_research_assignment_history_cli_stdout(report: object) -> str:
    return (
        "team-research-assignment-history: "
        f"config_version={_string_value(getattr(report, 'config_version'))} "
        f"history_status={_string_value(getattr(report, 'history_status'))} "
        f"report_count={_string_value(getattr(report, 'report_count'))} "
        f"required_report_count={_string_value(getattr(report, 'required_report_count'))} "
        "first_report_generated_at="
        f"{_string_value(getattr(report, 'first_report_generated_at'))} "
        "latest_report_generated_at="
        f"{_string_value(getattr(report, 'latest_report_generated_at'))} "
        f"status_rows={_status_rows_value(getattr(report, 'status_rows'))} "
        "latest_assignment_status="
        f"{_string_value(getattr(report, 'latest_assignment_status'))} "
        f"latest_assignment_count={_string_value(getattr(report, 'latest_assignment_count'))} "
        f"latest_assigned_count={_string_value(getattr(report, 'latest_assigned_count'))} "
        f"latest_watch_count={_string_value(getattr(report, 'latest_watch_count'))} "
        f"latest_blocked_count={_string_value(getattr(report, 'latest_blocked_count'))} "
        f"assignment_count_delta={_string_value(getattr(report, 'assignment_count_delta'))} "
        f"assigned_count_delta={_string_value(getattr(report, 'assigned_count_delta'))} "
        f"watch_count_delta={_string_value(getattr(report, 'watch_count_delta'))} "
        f"blocked_count_delta={_string_value(getattr(report, 'blocked_count_delta'))} "
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


def _status_rows_value(status_rows: object) -> str:
    if status_rows is None:
        return "none"
    values = tuple(status_rows)
    if not values:
        return "none"
    return ",".join(_status_row_value(row) for row in values)


def _status_row_value(row: object) -> str:
    if isinstance(row, tuple) and len(row) >= 2:
        return f"{_string_value(row[0])}:{_string_value(row[1])}"
    return (
        f"{_field_value(row, 'assignment_status', 'none')}:"
        f"{_field_value(row, 'report_count', 'none')}"
    )


def _reason_codes_value(reason_codes: object) -> str:
    if reason_codes is None:
        return "none"
    values = tuple(reason_codes)
    if not values:
        return "none"
    return ",".join(str(reason_code) for reason_code in values)


def _field_value(container: object, name: str, default: object) -> str:
    if isinstance(container, dict):
        return _string_value(container.get(name, default))
    return _string_value(getattr(container, name, default))


__all__ = ("format_team_research_assignment_history_cli_stdout",)
