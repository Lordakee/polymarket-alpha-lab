"""Append-only JSONL helpers for paper strategy recommendation bundle reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
)


__all__ = (
    "append_paper_strategy_recommendation_bundle_log",
    "read_paper_strategy_recommendation_bundle_log",
)


LOG_NAME = "strategy recommendation bundle log"


def append_paper_strategy_recommendation_bundle_log(
    path: Path | str,
    report: PaperStrategyRecommendationBundleReport,
) -> None:
    """Append one paper-only recommendation bundle report to a local JSONL log."""

    if type(report) is not PaperStrategyRecommendationBundleReport:
        raise ValueError("report must be a PaperStrategyRecommendationBundleReport")
    _validate_report_flags(report)
    path = _normalize_log_path(path)
    line = (
        json.dumps(
            _json_ready(asdict(_validate_report_tree(report))),
            allow_nan=False,
            sort_keys=True,
        )
        + "\n"
    )
    _validate_log_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def read_paper_strategy_recommendation_bundle_log(
    path: Path | str,
) -> tuple[PaperStrategyRecommendationBundleReport, ...]:
    """Read recommendation bundle JSONL reports back into typed dataclasses."""

    target = Path(path)
    records: list[PaperStrategyRecommendationBundleReport] = []
    with target.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{LOG_NAME} line {line_number} is not valid JSON: {exc}",
                ) from exc
            try:
                records.append(_report_from_jsonable(row))
            except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"{LOG_NAME} line {line_number} is not a valid report: {exc}",
                ) from exc
    return tuple(records)


def _validate_report_tree(
    report: PaperStrategyRecommendationBundleReport,
) -> PaperStrategyRecommendationBundleReport:
    _validate_nested_report(
        "recommendation_report",
        report.recommendation_report,
        PaperStrategyCandidateRecommendationReport,
    )
    _validate_nested_report(
        "selection_policy_report",
        report.selection_policy_report,
        PaperStrategySelectionPolicyReport,
    )
    _validate_nested_report(
        "explanation_report",
        report.explanation_report,
        PaperStrategyRecommendationExplanationReport,
    )
    row = _json_ready(asdict(report))
    return _report_from_jsonable(row)


def _report_from_jsonable(row: Any) -> PaperStrategyRecommendationBundleReport:
    if not isinstance(row, dict):
        raise ValueError("report row must be a JSON object")
    _validate_json_report_shape(row)
    report = from_jsonable(PaperStrategyRecommendationBundleReport, row)
    if type(report) is not PaperStrategyRecommendationBundleReport:
        raise ValueError("report must be a PaperStrategyRecommendationBundleReport")
    return report


def _validate_json_report_shape(row: dict[str, Any]) -> None:
    _require_json_hard_flags(row, "report")
    recommendation_report = _required_json_object(row, "recommendation_report")
    selection_policy_report = _required_json_object(row, "selection_policy_report")
    explanation_report = _required_json_object(row, "explanation_report")

    _require_json_hard_flags(recommendation_report, "recommendation_report")
    _require_json_hard_flags(selection_policy_report, "selection_policy_report")
    _require_json_hard_flags(explanation_report, "explanation_report")

    for recommendation_row in _require_json_array(
        recommendation_report,
        "recommendation_rows",
    ):
        _require_json_array(_require_json_object_value(recommendation_row), "reason_codes")
    for selection_row in _require_json_array(
        selection_policy_report,
        "selection_rows",
    ):
        _require_json_array(_require_json_object_value(selection_row), "reason_codes")
    for explanation_row in _require_json_array(
        explanation_report,
        "explanation_rows",
    ):
        _require_json_array(_require_json_object_value(explanation_row), "reason_codes")


def _require_json_hard_flags(row: dict[str, Any], field_name: str) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if row.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


def _required_json_object(row: dict[str, Any], field_name: str) -> dict[str, Any]:
    value = row[field_name]
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _require_json_object_value(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("JSON array items must be objects")
    return value


def _require_json_array(row: dict[str, Any], field_name: str) -> list[Any]:
    value = row[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _validate_nested_report(field_name: str, report: Any, expected_type: type[Any]) -> None:
    if type(report) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _validate_report_flags(report, field_name=field_name)


def _validate_report_flags(report: Any, *, field_name: str = "report") -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(report, flag_name, None) is not True:
            if field_name == "report":
                raise ValueError(f"{flag_name} must be True")
            raise ValueError(f"{field_name} {flag_name} must be True")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("strategy recommendation bundle log values must be JSON serializable")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return
