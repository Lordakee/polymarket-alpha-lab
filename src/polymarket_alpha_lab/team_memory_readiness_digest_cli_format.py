from __future__ import annotations


def format_team_memory_readiness_digest_cli_stdout(report: object) -> str:
    return (
        "team-memory-readiness-digest: "
        f"digest_status={_string_value(getattr(report, 'digest_status'))} "
        f"recommended_next_step={_string_value(getattr(report, 'recommended_next_step'))} "
        f"team_count={_string_value(getattr(report, 'team_count'))} "
        f"pass_count={_string_value(getattr(report, 'pass_count'))} "
        f"watch_count={_string_value(getattr(report, 'watch_count'))} "
        f"blocked_count={_string_value(getattr(report, 'blocked_count'))} "
        f"source_statuses={_source_statuses_value(getattr(report, 'source_statuses'))} "
        "source_config_versions="
        f"{_source_config_versions_value(getattr(report, 'source_config_versions'))} "
        f"reason_code_counts={_reason_code_counts_value(getattr(report, 'reason_code_counts'))} "
        f"reason_codes={_reason_codes_value(getattr(report, 'reason_codes'))} "
        f"paper_only={_string_value(getattr(report, 'paper_only'))} "
        f"report_only={_string_value(getattr(report, 'report_only'))} "
        f"readonly={_string_value(getattr(report, 'readonly'))}\n"
    )


def _string_value(value: object) -> str:
    if value is None:
        return "none"
    return str(value)


def _source_statuses_value(source_statuses: object) -> str:
    if source_statuses is None:
        return "none"
    values = tuple(source_statuses)
    if not values:
        return "none"
    return ",".join(_source_status_value(row) for row in values)


def _source_status_value(row: object) -> str:
    return (
        f"{_field_value(row, 'team_id', 'none')}:"
        f"{_field_value(row, 'gate_status', 'none')}:"
        f"{_field_value(row, 'latest_snapshot_age_seconds', 'none')}:"
        f"{_field_value(row, 'source_snapshot_count', 'none')}/"
        f"{_field_value(row, 'source_required_snapshot_count', 'none')}"
    )


def _source_config_versions_value(source_config_versions: object) -> str:
    if source_config_versions is None:
        return "none"
    values = tuple(source_config_versions)
    if not values:
        return "none"
    return ",".join(_source_config_version_value(row) for row in values)


def _source_config_version_value(row: object) -> str:
    if isinstance(row, tuple) and len(row) >= 2:
        return f"{_string_value(row[0])}:{_string_value(row[1])}"
    return (
        f"{_field_value(row, 'team_id', 'none')}:"
        f"{_field_value(row, 'source_config_version', 'none')}"
    )


def _reason_code_counts_value(reason_code_counts: object) -> str:
    if reason_code_counts is None:
        return "none"
    values = tuple(reason_code_counts)
    if not values:
        return "none"
    return ",".join(_reason_code_count_value(row) for row in values)


def _reason_code_count_value(row: object) -> str:
    if isinstance(row, tuple) and len(row) >= 2:
        return f"{_string_value(row[0])}:{_string_value(row[1])}"
    return (
        f"{_field_value(row, 'reason_code', 'none')}:"
        f"{_field_value(row, 'count', 'none')}"
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


__all__ = ("format_team_memory_readiness_digest_cli_stdout",)
