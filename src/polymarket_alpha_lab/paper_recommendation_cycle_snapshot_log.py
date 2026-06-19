"""Append-only JSONL helpers for paper recommendation cycle snapshots."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
)


__all__ = (
    "append_paper_recommendation_cycle_snapshot_log",
    "read_paper_recommendation_cycle_snapshot_log",
)


LOG_NAME = "paper recommendation cycle snapshot log"


def append_paper_recommendation_cycle_snapshot_log(
    path: Path | str,
    report: PaperRecommendationCycleSnapshotReport,
) -> None:
    """Append one paper-only recommendation cycle snapshot to a local JSONL log."""

    if type(report) is not PaperRecommendationCycleSnapshotReport:
        raise ValueError("report must be a PaperRecommendationCycleSnapshotReport")
    _validate_report_tree(report)
    path = _normalize_log_path(path)
    line = (
        json.dumps(
            _json_ready(asdict(report)),
            allow_nan=False,
            sort_keys=True,
        )
        + "\n"
    )
    _validate_log_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def read_paper_recommendation_cycle_snapshot_log(
    path: Path | str,
) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
    """Read local snapshot JSONL reports back into typed dataclasses."""

    target = Path(path)
    records: list[PaperRecommendationCycleSnapshotReport] = []
    for line_number, raw_line in enumerate(
        target.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
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
    report: PaperRecommendationCycleSnapshotReport,
) -> PaperRecommendationCycleSnapshotReport:
    _validate_hard_flags(report, "report")
    _validate_hard_flags(report.pipeline_report, "pipeline_report")
    for index, stage in enumerate(report.pipeline_report.stages):
        _validate_hard_flags(stage, f"pipeline_report stages {index}")
    _validate_hard_flags(report.artifact_index_report, "artifact_index_report")
    return _report_from_jsonable(_json_ready(asdict(report)))


def _report_from_jsonable(row: Any) -> PaperRecommendationCycleSnapshotReport:
    if not isinstance(row, dict):
        raise ValueError("report row must be a JSON object")
    _reject_json_floats(row)
    _validate_json_hard_flags(row, "report")
    report = from_jsonable(PaperRecommendationCycleSnapshotReport, row)
    if type(report) is not PaperRecommendationCycleSnapshotReport:
        raise ValueError("report must be a PaperRecommendationCycleSnapshotReport")
    return report


def _validate_hard_flags(value: Any, field_name: str) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if _looks_report_like(value):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _looks_report_like(value: dict[str, Any]) -> bool:
    return any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly"))


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
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
    raise ValueError("paper recommendation cycle snapshot log values must be JSON serializable")


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
