"""Pure row codec for persisted paper recommendation cycle snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
)


__all__ = (
    "PaperRecommendationCycleSnapshotDbRow",
    "paper_recommendation_cycle_snapshot_from_db_row",
    "paper_recommendation_cycle_snapshot_to_db_row",
)


STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class PaperRecommendationCycleSnapshotDbRow:
    snapshot_sha256: str
    generated_at: datetime
    config_version: str
    final_status: str
    stage_count: int
    artifact_count: int
    blocked_artifact_count: int
    watch_artifact_count: int
    reason_codes: tuple[str, ...]
    stage_counts_json: dict[str, int]
    artifact_counts_json: dict[str, int]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("snapshot_sha256", self.snapshot_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("final_status", self.final_status)
        for field_name in (
            "stage_count",
            "artifact_count",
            "blocked_artifact_count",
            "watch_artifact_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "stage_counts_json",
            _normalize_int_json_object("stage_counts_json", self.stage_counts_json),
        )
        object.__setattr__(
            self,
            "artifact_counts_json",
            _normalize_int_json_object(
                "artifact_counts_json",
                self.artifact_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_count_objects(self)


def paper_recommendation_cycle_snapshot_to_db_row(
    report: PaperRecommendationCycleSnapshotReport,
) -> PaperRecommendationCycleSnapshotDbRow:
    if type(report) is not PaperRecommendationCycleSnapshotReport:
        raise ValueError("report must be a PaperRecommendationCycleSnapshotReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    snapshot_sha256 = _snapshot_sha256(payload_json)
    return PaperRecommendationCycleSnapshotDbRow(
        snapshot_sha256=snapshot_sha256,
        generated_at=report.generated_at,
        config_version=report.config_version,
        final_status=report.final_status,
        stage_count=report.stage_count,
        artifact_count=report.artifact_count,
        blocked_artifact_count=report.blocked_artifact_count,
        watch_artifact_count=report.watch_artifact_count,
        reason_codes=report.reason_codes,
        stage_counts_json={
            "stage_count": report.pipeline_report.stage_count,
            "pass_count": report.pipeline_report.pass_count,
            "watch_count": report.pipeline_report.watch_count,
            "blocked_count": report.pipeline_report.blocked_count,
        },
        artifact_counts_json={
            "artifact_count": report.artifact_index_report.row_count,
            "pass_count": report.artifact_index_report.pass_count,
            "watch_count": report.artifact_index_report.watch_count,
            "blocked_count": report.artifact_index_report.blocked_count,
        },
        payload_json=payload_json,
    )


def paper_recommendation_cycle_snapshot_from_db_row(
    row: PaperRecommendationCycleSnapshotDbRow,
) -> PaperRecommendationCycleSnapshotReport:
    if type(row) is not PaperRecommendationCycleSnapshotDbRow:
        raise ValueError("row must be a PaperRecommendationCycleSnapshotDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperRecommendationCycleSnapshotReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid snapshot report: {exc}") from exc
    if type(report) is not PaperRecommendationCycleSnapshotReport:
        raise ValueError("payload_json must recover a PaperRecommendationCycleSnapshotReport")
    _validate_report_tree(report)
    expected_row = paper_recommendation_cycle_snapshot_to_db_row(report)
    if row.snapshot_sha256 != expected_row.snapshot_sha256:
        raise ValueError("snapshot_sha256 must match payload_json")
    return report


def _validate_report_tree(
    report: PaperRecommendationCycleSnapshotReport,
) -> None:
    _require_hard_flags("report", report)
    _require_hard_flags("pipeline_report", report.pipeline_report)
    for index, stage in enumerate(report.pipeline_report.stages):
        _require_hard_flags(f"pipeline_report stages {index}", stage)
    _require_hard_flags("artifact_index_report", report.artifact_index_report)


def _snapshot_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_count_objects(row: PaperRecommendationCycleSnapshotDbRow) -> None:
    expected_stage_counts = {
        "stage_count": row.stage_count,
        "pass_count": row.stage_counts_json.get("pass_count"),
        "watch_count": row.stage_counts_json.get("watch_count"),
        "blocked_count": row.stage_counts_json.get("blocked_count"),
    }
    if row.stage_counts_json.get("stage_count") != row.stage_count:
        raise ValueError("stage_counts_json stage_count must match stage_count")
    if not all(type(value) is int and value >= 0 for value in expected_stage_counts.values()):
        raise ValueError("stage_counts_json must contain nonnegative int counts")

    expected_artifact_counts = {
        "artifact_count": row.artifact_count,
        "pass_count": row.artifact_counts_json.get("pass_count"),
        "watch_count": row.artifact_counts_json.get("watch_count"),
        "blocked_count": row.artifact_counts_json.get("blocked_count"),
    }
    if row.artifact_counts_json.get("artifact_count") != row.artifact_count:
        raise ValueError("artifact_counts_json artifact_count must match artifact_count")
    if not all(type(value) is int and value >= 0 for value in expected_artifact_counts.values()):
        raise ValueError("artifact_counts_json must contain nonnegative int counts")


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
        return _as_utc("datetime", value).isoformat()
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
    raise ValueError("cycle snapshot DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _normalize_int_json_object(field_name: str, value: object) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    for key, item in normalized.items():
        if type(item) is not int or item < 0:
            raise ValueError(f"{field_name} {key} must be a nonnegative int")
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly")):
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


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    return tuple(_require_reason_code(value) for value in normalized)


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if _TOKEN_PATTERN.sub("_", value.strip().lower()).strip("_") != value:
        raise ValueError("reason_codes must contain canonical tokens")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
