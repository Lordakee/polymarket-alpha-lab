from __future__ import annotations

from datetime import datetime


_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "market_id",
    "candidate_id",
    "normalized_market_question",
    "market_slug",
    "question",
    "payload",
    "hash",
    "digest",
    "dsn",
    "host",
    "table",
    "source_ref",
    "source_report_ref",
    "trade",
    "trading",
    "authentication",
    "authorization",
    "oauth",
    "api_key",
    "wallet",
    "account",
    "order",
    "signing",
    "cancel",
    "replace",
    "exchange",
)


def format_candidate_decision_score_history_cli_stdout(report: object) -> str:
    _require_hard_flags(report)
    return (
        "candidate-decision-score-history: "
        f"generated_at={_string_value(_field_value(report, 'generated_at', None))} "
        f"status={_string_value(_field_value(report, 'status', None))} "
        f"report_count={_string_value(_field_value(report, 'report_count', None))} "
        "latest_generated_at="
        f"{_string_value(_field_value(report, 'latest_generated_at', None))} "
        "action_counts="
        f"{_count_rows_value(_field_value(report, 'action_counts', None), ('action', 'name'))} "
        "reason_counts="
        f"{_count_rows_value(_field_value(report, 'reason_counts', None), ('reason_code', 'reason', 'name'))} "
        "primary_team_counts="
        f"{_count_rows_value(_field_value(report, 'primary_team_counts', None), ('primary_team_id', 'team_id', 'team', 'name'))} "
        f"paper_only={_string_value(_field_value(report, 'paper_only', None))} "
        f"report_only={_string_value(_field_value(report, 'report_only', None))} "
        f"readonly={_string_value(_field_value(report, 'readonly', None))}\n"
    )


def _require_hard_flags(report: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if _field_value(report, flag_name, None) is not True:
            raise ValueError(f"report must be {flag_name}")


def _string_value(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, datetime):
        text = value.isoformat()
    else:
        text = str(value)
    _reject_unsafe_public_value(text)
    return text


def _count_rows_value(rows: object, label_fields: tuple[str, ...]) -> str:
    if rows is None:
        return "none"
    values = tuple(rows.items()) if isinstance(rows, dict) else tuple(rows)
    if not values:
        return "none"
    return ",".join(_count_row_value(row, label_fields) for row in values)


def _count_row_value(row: object, label_fields: tuple[str, ...]) -> str:
    label, count = _count_row_parts(row, label_fields)
    return f"{_string_value(label)}:{_string_value(count)}"


def _count_row_parts(row: object, label_fields: tuple[str, ...]) -> tuple[object, object]:
    if isinstance(row, tuple) and len(row) >= 2:
        return row[0], row[1]
    if isinstance(row, list) and len(row) >= 2:
        return row[0], row[1]

    label = _first_present_field(row, label_fields)
    count = _first_present_field(row, ("count", "report_count", "total"))
    if label is None or count is None:
        raise ValueError("count row must include label and count")
    return label, count


def _first_present_field(container: object, names: tuple[str, ...]) -> object:
    for name in names:
        value = _field_value(container, name, None)
        if value is not None:
            return value
    return None


def _field_value(container: object, name: str, default: object) -> object:
    if isinstance(container, dict):
        return container.get(name, default)
    return getattr(container, name, default)


def _reject_unsafe_public_value(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError("unsafe public summary value")


__all__ = ("format_candidate_decision_score_history_cli_stdout",)
