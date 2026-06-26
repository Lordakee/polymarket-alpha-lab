"""Pure row codec for persisted paper allocation metrics evaluation reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
)


__all__ = (
    "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow",
    "paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row",
    "paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row",
)


STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    evaluation_status: str
    recommended_next_step: str
    source_report_count: int
    latest_report_generated_at: datetime | None
    reason_code_counts_json: dict[str, int]
    reason_codes: tuple[str, ...]
    diagnostics_json: dict[str, Any]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("evaluation_status", self.evaluation_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_reason_code_counts_json(
                "reason_code_counts_json",
                self.reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "diagnostics_json",
            _normalize_json_object("diagnostics_json", self.diagnostics_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_json_hard_flags(self.diagnostics_json, "diagnostics_json")
        _require_json_hard_flags("diagnostics_json", self.diagnostics_json)
        _validate_row_json_shape(self)
        _validate_row_matches_payload_json(self)
        _validate_payload_json_recoverable(self.payload_json)


def paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
    report: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow:
    if (
        type(report)
        is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport
    ):
        raise ValueError(
            "report must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    diagnostics_json = _normalize_json_object(
        "diagnostics_json",
        payload_json["diagnostics"],
    )
    return PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        evaluation_status=report.evaluation_status,
        recommended_next_step=report.recommended_next_step,
        source_report_count=report.source_report_count,
        latest_report_generated_at=report.latest_report_generated_at,
        reason_code_counts_json={
            count.reason_code: count.report_count
            for count in report.reason_code_counts
        },
        reason_codes=report.reason_codes,
        diagnostics_json=diagnostics_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
    row: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    if type(row) is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow:
        raise ValueError(
            "row must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow",
        )
    _reject_json_floats(row.payload_json)
    _reject_json_floats(row.diagnostics_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_json_hard_flags(row.diagnostics_json, "diagnostics_json")
    _validate_row_matches_payload_json(row)
    _validate_payload_json_recoverable(row.payload_json)
    try:
        report = from_jsonable(
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
            row.payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid paper autonomous allocation proposal "
            f"metrics evaluation report: {exc}",
        ) from exc
    if (
        type(report)
        is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport
    ):
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport",
        )
    _validate_report_tree(report)
    expected_row = (
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
            report,
        )
    )
    if row.report_sha256 != expected_row.report_sha256:
        raise ValueError("report_sha256 must match payload_json")
    if _summary_values(row) != _summary_values(expected_row):
        raise ValueError("summary columns must match payload_json")
    if row.diagnostics_json != expected_row.diagnostics_json:
        raise ValueError("diagnostics_json must match payload_json")
    return report


def _summary_values(
    row: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
) -> tuple[Any, ...]:
    return (
        row.generated_at,
        row.config_version,
        row.evaluation_status,
        row.recommended_next_step,
        row.source_report_count,
        row.latest_report_generated_at,
        row.reason_code_counts_json,
        row.reason_codes,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _validate_report_tree(
    report: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
) -> None:
    _require_hard_flags("report", report)
    _require_hard_flags("diagnostics", report.diagnostics)
    for index, count in enumerate(report.reason_code_counts):
        _require_hard_flags(f"reason_code_counts {index}", count)


def _validate_payload_json_recoverable(payload_json: dict[str, Any]) -> None:
    try:
        report = from_jsonable(
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid paper autonomous allocation proposal "
            f"metrics evaluation report: {exc}",
        ) from exc
    if (
        type(report)
        is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport
    ):
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport",
        )
    _validate_report_tree(report)
    if _json_ready(asdict(report)) != payload_json:
        raise ValueError("payload_json must be canonical")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_row_json_shape(
    row: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
) -> None:
    top_reason_codes = row.diagnostics_json.get("top_reason_codes")
    if top_reason_codes is not None and not isinstance(top_reason_codes, list):
        raise ValueError("diagnostics_json top_reason_codes must be an array")
    if set(row.reason_code_counts_json) != set(row.reason_codes):
        raise ValueError("reason_code_counts_json keys must match reason_codes")
    payload_diagnostics = row.payload_json.get("diagnostics")
    if payload_diagnostics is not None:
        normalized_payload_diagnostics = _normalize_json_object(
            "payload_json diagnostics",
            payload_diagnostics,
        )
        _require_json_hard_flags(
            "payload_json diagnostics",
            normalized_payload_diagnostics,
        )
        if row.diagnostics_json != normalized_payload_diagnostics:
            raise ValueError("diagnostics_json must match payload_json")


def _validate_row_matches_payload_json(
    row: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
) -> None:
    try:
        payload_sha256 = _report_sha256(row.payload_json)
    except (TypeError, ValueError) as exc:
        raise ValueError("payload_json must be canonical JSON") from exc
    if row.report_sha256 != payload_sha256:
        raise ValueError("report_sha256 must match payload_json")
    _validate_summary_columns_match_payload(row)
    if row.diagnostics_json != row.payload_json.get("diagnostics"):
        raise ValueError("diagnostics_json must match payload_json")
    if row.payload_json.get("paper_only") is not True:
        raise ValueError("paper_only must match payload_json")
    if row.payload_json.get("report_only") is not True:
        raise ValueError("report_only must match payload_json")
    if row.payload_json.get("readonly") is not True:
        raise ValueError("readonly must match payload_json")
    if row.paper_only != row.payload_json.get("paper_only"):
        raise ValueError("paper_only must match payload_json")
    if row.report_only != row.payload_json.get("report_only"):
        raise ValueError("report_only must match payload_json")
    if row.readonly != row.payload_json.get("readonly"):
        raise ValueError("readonly must match payload_json")


def _validate_summary_columns_match_payload(
    row: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
) -> None:
    payload_values = _payload_summary_values(row.payload_json)
    row_values = _row_summary_values_json(row)
    if payload_values[6] != row_values[6]:
        raise ValueError("reason_code_counts_json must match payload_json")
    if payload_values[7] != row_values[7]:
        raise ValueError("reason_codes must match payload_json")
    if payload_values != row_values:
        raise ValueError("summary columns must match payload_json")


def _payload_summary_values(payload_json: dict[str, Any]) -> tuple[Any, ...]:
    return (
        payload_json.get("generated_at"),
        payload_json.get("config_version"),
        payload_json.get("evaluation_status"),
        payload_json.get("recommended_next_step"),
        payload_json.get("source_report_count"),
        payload_json.get("latest_report_generated_at"),
        _payload_reason_code_counts_json(payload_json.get("reason_code_counts")),
        tuple(payload_json.get("reason_codes", ())),
        payload_json.get("paper_only"),
        payload_json.get("report_only"),
        payload_json.get("readonly"),
    )


def _payload_reason_code_counts_json(value: object) -> dict[str, int]:
    if not isinstance(value, list):
        raise ValueError("payload_json reason_code_counts must be an array")
    counts: dict[str, int] = {}
    expected_keys = {
        "reason_code",
        "report_count",
        "paper_only",
        "report_only",
        "readonly",
    }
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError("payload_json reason_code_counts must contain objects")
        if set(item) != expected_keys:
            raise ValueError(
                f"payload_json reason_code_counts {index} must contain exact keys",
            )
        for flag_name in ("paper_only", "report_only", "readonly"):
            if item.get(flag_name) is not True:
                raise ValueError(
                    f"payload_json reason_code_counts {index} "
                    f"{flag_name} must be present and true",
                )
        reason_code = _require_reason_code(item.get("reason_code"))
        report_count = item.get("report_count")
        if type(report_count) is not int or report_count <= 0:
            raise ValueError(
                f"payload_json reason_code_counts {index} "
                "report_count must be a positive int",
            )
        if reason_code in counts:
            raise ValueError("payload_json reason_code_counts must be unique")
        counts[reason_code] = report_count
    return counts


def _row_summary_values_json(
    row: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
) -> tuple[Any, ...]:
    return (
        _json_ready(row.generated_at),
        row.config_version,
        row.evaluation_status,
        row.recommended_next_step,
        row.source_report_count,
        _json_ready(row.latest_report_generated_at),
        row.reason_code_counts_json,
        row.reason_codes,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


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
    raise ValueError("metrics evaluation DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    for key, item in normalized.items():
        _require_reason_code(key)
        if type(item) is not int or item <= 0:
            raise ValueError(f"{field_name} {key} must be a positive int")
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


def _require_json_hard_flags(value_name: str, value: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{value_name} {flag_name} must be present and true")


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


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


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
