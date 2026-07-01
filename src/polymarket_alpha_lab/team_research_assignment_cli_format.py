from __future__ import annotations


def format_team_research_assignment_cli_stdout(report: object) -> str:
    return (
        "team-research-assignment: "
        f"assignment_status={_string_value(getattr(report, 'assignment_status'))} "
        "recommended_next_step="
        f"{_string_value(getattr(report, 'recommended_next_step'))} "
        f"assignment_count={_string_value(getattr(report, 'assignment_count'))} "
        f"assigned_count={_string_value(getattr(report, 'assigned_count'))} "
        f"watch_count={_string_value(getattr(report, 'watch_count'))} "
        f"blocked_count={_string_value(getattr(report, 'blocked_count'))} "
        f"team_summaries={_team_summaries_value(getattr(report, 'team_summaries'))} "
        f"rows={_rows_value(getattr(report, 'rows'))} "
        f"reason_codes={_reason_codes_value(getattr(report, 'reason_codes'))} "
        f"paper_only={_string_value(getattr(report, 'paper_only'))} "
        f"report_only={_string_value(getattr(report, 'report_only'))} "
        f"readonly={_string_value(getattr(report, 'readonly'))}\n"
    )


def _string_value(value: object) -> str:
    if value is None:
        return "none"
    return str(value)


def _team_summaries_value(team_summaries: object) -> str:
    if team_summaries is None:
        return "none"
    values = tuple(team_summaries)
    if not values:
        return "none"
    return ",".join(_team_summary_value(row) for row in values)


def _team_summary_value(row: object) -> str:
    if isinstance(row, tuple) and len(row) >= 7:
        return (
            f"{_string_value(row[0])}:"
            f"{_string_value(row[1])}:"
            f"{_string_value(row[2])}/{_string_value(row[3])}/{_string_value(row[4])}:"
            f"{_string_value(row[5])}:"
            f"{_string_value(row[6])}"
        )
    return (
        f"{_field_value(row, 'team_id', 'none')}:"
        f"{_field_value(row, 'assignment_count', 'none')}:"
        f"{_field_value(row, 'assigned_count', 'none')}/"
        f"{_field_value(row, 'watch_count', 'none')}/"
        f"{_field_value(row, 'blocked_count', 'none')}:"
        f"{_field_value(row, 'memory_readiness_status', 'none')}:"
        f"{_field_value(row, 'memory_use_policy', 'none')}"
    )


def _rows_value(rows: object) -> str:
    if rows is None:
        return "none"
    values = tuple(rows)
    if not values:
        return "none"
    return ",".join(_row_value(row) for row in values)


def _row_value(row: object) -> str:
    if isinstance(row, tuple) and len(row) >= 6:
        return (
            f"{_string_value(row[0])}:"
            f"{_string_value(row[1])}:"
            f"{_string_value(row[2])}:"
            f"{_string_value(row[3])}:"
            f"{_string_value(row[4])}:"
            f"{_string_value(row[5])}"
        )
    return (
        f"{_field_value(row, 'research_rank', 'none')}:"
        f"{_field_value(row, 'market_slug', 'none')}:"
        f"{_field_value(row, 'team_id', 'none')}:"
        f"{_field_value(row, 'category_id', 'none')}:"
        f"{_field_value(row, 'assignment_status', 'none')}:"
        f"{_field_value(row, 'memory_use_policy', 'none')}"
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


__all__ = ("format_team_research_assignment_cli_stdout",)
