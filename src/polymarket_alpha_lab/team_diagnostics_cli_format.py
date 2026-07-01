from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


_ROW_COUNT_KEYS = (
    "calibration",
    "event_template_rows",
    "source_reliability_rows",
    "evidence_quality_rows",
    "memory_eligible_references",
)


def format_team_diagnostics_cli_stdout(bundle: object) -> str:
    return "\n".join(format_team_diagnostics_cli_lines(bundle)) + "\n"


def format_team_diagnostics_cli_lines(bundle: object) -> tuple[str, ...]:
    row_counts = _row_counts(bundle)
    memory_references = _memory_reference_rows(bundle)
    event_template_rows = _event_template_rows(bundle)
    source_reliability_rows = _source_reliability_rows(bundle)
    evidence_quality_rows = _evidence_quality_rows(bundle)

    lines = [
        (
            "team-diagnostics: "
            f"paper_only={_value(bundle, 'paper_only', True)} "
            f"report_only={_value(bundle, 'report_only', True)} "
            f"readonly={_value(bundle, 'readonly', True)}"
        ),
        (
            "row-counts: "
            f"calibration={row_counts['calibration']} "
            f"event_template_rows={row_counts['event_template_rows']} "
            f"source_reliability_rows={row_counts['source_reliability_rows']} "
            f"evidence_quality_rows={row_counts['evidence_quality_rows']} "
            f"memory_eligible_references={row_counts['memory_eligible_references']}"
        ),
    ]

    lines.extend(_memory_reference_lines(memory_references))
    lines.append(_calibration_summary_line(_calibration_summary(bundle)))
    lines.extend(_event_template_lines(event_template_rows))
    lines.extend(_source_reliability_lines(source_reliability_rows))
    lines.extend(_evidence_quality_lines(evidence_quality_rows))
    return tuple(lines)


def _row_counts(bundle: object) -> dict[str, int]:
    explicit = _value(bundle, "row_counts", {})
    counts = {key: _int_value(explicit, key) for key in _ROW_COUNT_KEYS}
    counts["memory_eligible_references"] = counts[
        "memory_eligible_references"
    ] or len(_memory_reference_rows(bundle))
    counts["event_template_rows"] = counts["event_template_rows"] or len(
        _event_template_rows(bundle),
    )
    counts["source_reliability_rows"] = counts["source_reliability_rows"] or len(
        _source_reliability_rows(bundle),
    )
    counts["evidence_quality_rows"] = counts["evidence_quality_rows"] or len(
        _evidence_quality_rows(bundle),
    )
    counts["calibration"] = counts["calibration"] or len(
        _rows(_value(bundle, "forecast_calibration_report", None), "groups"),
    )
    return counts


def _memory_reference_rows(bundle: object) -> tuple[object, ...]:
    explicit = _rows(bundle, "memory_eligible_references")
    if explicit:
        return explicit
    memory_report = _value(bundle, "memory_synthesis_report", None)
    return tuple(
        {
            "condition_id": _text_value(row, "team_id"),
            "market_slug": _text_value(row, "event_template"),
            "reason": _text_value(row, "gate_status"),
            "score": _display_value(row, "average_brier_score"),
        }
        for row in _rows(memory_report, "rows")
        if _text_value(row, "gate_status") == "eligible"
    )


def _event_template_rows(bundle: object) -> tuple[object, ...]:
    explicit = _rows(bundle, "event_template_rows")
    if explicit:
        return explicit
    template_report = _value(bundle, "event_template_performance_report", None)
    return tuple(
        {
            "event_type": _text_value(row, "category_id"),
            "template_id": _text_value(row, "event_template"),
            "row_count": _display_value(row, "settled_count"),
        }
        for row in _rows(template_report, "rows")
    )


def _source_reliability_rows(bundle: object) -> tuple[object, ...]:
    explicit = _rows(bundle, "source_reliability_rows")
    if explicit:
        return explicit
    source_report = _value(bundle, "source_reliability_report", None)
    return tuple(
        {
            "source": _text_value(row, "source_id"),
            "resolved_count": _display_value(row, "settled_evidence_count"),
            "mean_error": _display_value(row, "average_brier_score"),
        }
        for row in _rows(source_report, "rows")
    )


def _evidence_quality_rows(bundle: object) -> tuple[object, ...]:
    explicit = _rows(bundle, "evidence_quality_rows")
    if explicit:
        return explicit
    quality_report = _value(bundle, "evidence_quality_report", None)
    return tuple(
        {
            "label": _text_value(row, "source_id"),
            "rows": _display_value(row, "status"),
            "memory_eligible": _display_value(row, "quality_score"),
        }
        for row in _rows(quality_report, "rows")
    )


def _calibration_summary(bundle: object) -> object:
    explicit = _value(bundle, "calibration_summary", None)
    if explicit is not None:
        return explicit
    calibration_report = _value(bundle, "forecast_calibration_report", None)
    groups = _rows(calibration_report, "groups")
    if not groups:
        return {}
    first_group = groups[0]
    return {
        "bucket_count": len(groups),
        "observation_count": _display_value(first_group, "settled_count"),
        "brier_mean": _display_value(first_group, "average_brier_score"),
        "ece": _display_value(first_group, "calibration_error"),
    }


def _memory_reference_lines(rows: tuple[object, ...]) -> tuple[str, ...]:
    lines = [f"memory-eligible-references: count={len(rows)}"]
    for row in sorted(rows, key=lambda item: _sort_key(item, "condition_id", "market_slug")):
        lines.append(
            "memory-eligible-reference: "
            f"condition_id={_text_value(row, 'condition_id')} "
            f"market_slug={_text_value(row, 'market_slug')} "
            f"reason={_text_value(row, 'reason')} "
            f"score={_metric_value(row, 'score')}",
        )
    return tuple(lines)


def _calibration_summary_line(summary: object) -> str:
    return (
        "calibration-summary: "
        f"bucket_count={_count_value(summary, 'bucket_count')} "
        f"observation_count={_count_value(summary, 'observation_count')} "
        f"brier_mean={_display_value(summary, 'brier_mean')} "
        f"ece={_display_value(summary, 'ece')}"
    )


def _event_template_lines(rows: tuple[object, ...]) -> tuple[str, ...]:
    lines = [f"event-template-rows: count={len(rows)}"]
    for row in sorted(rows, key=lambda item: _sort_key(item, "event_type", "template_id")):
        lines.append(
            "event-template-row: "
            f"event_type={_text_value(row, 'event_type')} "
            f"template_id={_text_value(row, 'template_id')} "
            f"row_count={_display_value(row, 'row_count')}",
        )
    return tuple(lines)


def _source_reliability_lines(rows: tuple[object, ...]) -> tuple[str, ...]:
    lines = [f"source-reliability-rows: count={len(rows)}"]
    for row in sorted(rows, key=lambda item: _sort_key(item, "source")):
        lines.append(
            "source-reliability-row: "
            f"source={_text_value(row, 'source')} "
            f"resolved_count={_display_value(row, 'resolved_count')} "
            f"mean_error={_display_value(row, 'mean_error')}",
        )
    return tuple(lines)


def _evidence_quality_lines(rows: tuple[object, ...]) -> tuple[str, ...]:
    lines = [f"evidence-quality-rows: count={len(rows)}"]
    for row in sorted(rows, key=lambda item: _sort_key(item, "label")):
        lines.append(
            "evidence-quality-row: "
            f"label={_text_value(row, 'label')} "
            f"rows={_display_value(row, 'rows')} "
            f"memory_eligible={_display_value(row, 'memory_eligible')}",
        )
    return tuple(lines)


def _rows(bundle: object, name: str) -> tuple[object, ...]:
    value = _value(bundle, name, ())
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(value)
    return (value,)


def _int_value(container: object, name: str) -> int:
    value = _value(container, name, 0)
    if type(value) is bool:
        return int(value)
    if type(value) is int:
        return value
    return 0


def _display_value(container: object, name: str) -> str:
    value = _value(container, name, "n/a")
    if value is None:
        return "n/a"
    if type(value) is float:
        return str(value)
    return str(value)


def _count_value(container: object, name: str) -> str:
    value = _value(container, name, 0)
    if value is None:
        return "0"
    return str(value)


def _metric_value(container: object, name: str) -> str:
    value = _value(container, name, "n/a")
    if value is None:
        return "n/a"
    return str(value)


def _text_value(container: object, name: str) -> str:
    value = _value(container, name, "")
    if value is None:
        return ""
    return str(value)


def _sort_key(container: object, *names: str) -> tuple[str, ...]:
    return tuple(_text_value(container, name) for name in names)


def _value(container: object, name: str, default: Any) -> Any:
    if isinstance(container, Mapping):
        return container.get(name, default)
    return getattr(container, name, default)


__all__ = (
    "format_team_diagnostics_cli_lines",
    "format_team_diagnostics_cli_stdout",
)
