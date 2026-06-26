"""Pure row codec for paper autonomous allocation proposal reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "PaperAutonomousAllocationProposalDbRow",
    "from_db_row",
    "paper_autonomous_allocation_proposal_from_db_row",
    "paper_autonomous_allocation_proposal_report_from_db_row",
    "paper_autonomous_allocation_proposal_report_to_db_row",
    "paper_autonomous_allocation_proposal_to_db_row",
    "to_db_row",
)


_REPORT_MODULE_NAME = "polymarket_alpha_lab.paper_autonomous_allocation_proposal"
_REPORT_TYPE_NAME = "PaperAutonomousAllocationProposalReport"
_STATUSES = ("pass", "watch", "blocked")
_NEXT_STEP_BY_STATUS = {
    "pass": "review_paper_autonomous_allocation_proposal",
    "watch": "hold_paper_autonomous_allocation_proposal",
    "blocked": "block_paper_autonomous_allocation_proposal",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    proposal_status: str
    recommended_next_step: str
    reason_codes_json: list[str]
    reason_code_counts_json: list[dict[str, Any]]
    screening_gate_generated_at: datetime
    screening_gate_config_version: str
    screening_gate_status: str
    screening_gate_recommended_next_step: str
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    source_queue_report_count: int
    source_queue_ready_count: int
    source_queue_watch_count: int
    source_queue_blocked_count: int
    allocation_config_version: str
    allocation_generated_at: datetime
    allocation_input_count: int
    allocation_row_count: int
    allocation_allocated_count: int
    allocation_capped_count: int
    allocation_no_budget_count: int
    allocation_non_recommend_count: int
    allocation_skipped_count: int
    allocation_total_requested_paper_notional: Decimal
    allocation_total_allocated_paper_notional: Decimal
    allocation_remaining_paper_budget: Decimal
    allocation_total_paper_budget: Decimal
    allocation_max_paper_notional_per_market: Decimal
    allocation_max_paper_notional_per_event: Decimal
    allocation_max_paper_notional_per_theme: Decimal
    allocation_max_paper_notional_per_correlation_group: Decimal
    allocation_rows_json: list[dict[str, Any]]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        for field_name in (
            "generated_at",
            "screening_gate_generated_at",
            "queue_risk_generated_at",
            "allocation_generated_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "config_version",
            "recommended_next_step",
            "screening_gate_config_version",
            "screening_gate_recommended_next_step",
            "queue_risk_config_version",
            "queue_risk_recommended_next_step",
            "allocation_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "proposal_status",
            "screening_gate_status",
            "queue_risk_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        _require_status_next_step(self.proposal_status, self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_json_object_array(
                "reason_code_counts_json",
                self.reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "allocation_rows_json",
            _normalize_json_object_array(
                "allocation_rows_json",
                self.allocation_rows_json,
            ),
        )
        for field_name in (
            "source_queue_report_count",
            "source_queue_ready_count",
            "source_queue_watch_count",
            "source_queue_blocked_count",
            "allocation_input_count",
            "allocation_row_count",
            "allocation_allocated_count",
            "allocation_capped_count",
            "allocation_no_budget_count",
            "allocation_non_recommend_count",
            "allocation_skipped_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "allocation_total_requested_paper_notional",
            "allocation_total_allocated_paper_notional",
            "allocation_remaining_paper_budget",
            "allocation_total_paper_budget",
            "allocation_max_paper_notional_per_market",
            "allocation_max_paper_notional_per_event",
            "allocation_max_paper_notional_per_theme",
            "allocation_max_paper_notional_per_correlation_group",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def paper_autonomous_allocation_proposal_to_db_row(
    report: Any,
) -> PaperAutonomousAllocationProposalDbRow:
    report_type = _report_type()
    if type(report) is not report_type:
        raise ValueError("report must be a PaperAutonomousAllocationProposalReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_codes_json = payload_json.get("reason_codes")
    reason_code_counts_json = payload_json.get("reason_code_counts")
    allocation_report_json = payload_json.get("allocation_report")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    if not isinstance(reason_code_counts_json, list):
        raise ValueError("payload_json reason_code_counts must be a JSON array")
    if not isinstance(allocation_report_json, dict):
        raise ValueError("payload_json allocation_report must be a JSON object")
    allocation_rows_json = allocation_report_json.get("rows")
    if not isinstance(allocation_rows_json, list):
        raise ValueError("payload_json allocation_report rows must be a JSON array")
    allocation_report = report.allocation_report
    return PaperAutonomousAllocationProposalDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        proposal_status=report.proposal_status,
        recommended_next_step=report.recommended_next_step,
        reason_codes_json=reason_codes_json,
        reason_code_counts_json=reason_code_counts_json,
        screening_gate_generated_at=report.screening_gate_generated_at,
        screening_gate_config_version=report.screening_gate_config_version,
        screening_gate_status=report.screening_gate_status,
        screening_gate_recommended_next_step=report.screening_gate_recommended_next_step,
        queue_risk_generated_at=report.queue_risk_generated_at,
        queue_risk_config_version=report.queue_risk_config_version,
        queue_risk_status=report.queue_risk_status,
        queue_risk_recommended_next_step=report.queue_risk_recommended_next_step,
        source_queue_report_count=_source_queue_report_count(report),
        source_queue_ready_count=_source_queue_status_count(report, "ready_count"),
        source_queue_watch_count=_source_queue_status_count(report, "watch_count"),
        source_queue_blocked_count=_source_queue_status_count(report, "blocked_count"),
        allocation_config_version=allocation_report.config_version,
        allocation_generated_at=allocation_report.generated_at,
        allocation_input_count=allocation_report.input_count,
        allocation_row_count=allocation_report.row_count,
        allocation_allocated_count=allocation_report.allocated_count,
        allocation_capped_count=allocation_report.capped_count,
        allocation_no_budget_count=allocation_report.no_budget_count,
        allocation_non_recommend_count=allocation_report.non_recommend_count,
        allocation_skipped_count=allocation_report.skipped_count,
        allocation_total_requested_paper_notional=(
            allocation_report.total_requested_paper_notional
        ),
        allocation_total_allocated_paper_notional=(
            allocation_report.total_allocated_paper_notional
        ),
        allocation_remaining_paper_budget=allocation_report.remaining_paper_budget,
        allocation_total_paper_budget=allocation_report.total_paper_budget,
        allocation_max_paper_notional_per_market=(
            allocation_report.max_paper_notional_per_market
        ),
        allocation_max_paper_notional_per_event=(
            allocation_report.max_paper_notional_per_event
        ),
        allocation_max_paper_notional_per_theme=(
            allocation_report.max_paper_notional_per_theme
        ),
        allocation_max_paper_notional_per_correlation_group=(
            allocation_report.max_paper_notional_per_correlation_group
        ),
        allocation_rows_json=allocation_rows_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_allocation_proposal_from_db_row(
    row: PaperAutonomousAllocationProposalDbRow,
) -> Any:
    if type(row) is not PaperAutonomousAllocationProposalDbRow:
        raise ValueError("row must be a PaperAutonomousAllocationProposalDbRow")
    _validate_row_payload_consistency(row)

    report_type = _report_type()
    try:
        report = from_jsonable(report_type, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid allocation proposal report: {exc}",
        ) from exc
    if type(report) is not report_type:
        raise ValueError(
            "payload_json must recover a PaperAutonomousAllocationProposalReport",
        )
    _validate_report_tree(report)
    expected_row = paper_autonomous_allocation_proposal_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(report: Any) -> PaperAutonomousAllocationProposalDbRow:
    return paper_autonomous_allocation_proposal_to_db_row(report)


def from_db_row(row: PaperAutonomousAllocationProposalDbRow) -> Any:
    return paper_autonomous_allocation_proposal_from_db_row(row)


def _report_type() -> type:
    try:
        module = importlib.import_module(_REPORT_MODULE_NAME)
    except ImportError as exc:
        raise ValueError(
            f"{_REPORT_MODULE_NAME}.{_REPORT_TYPE_NAME} is required",
        ) from exc
    try:
        report_type = getattr(module, _REPORT_TYPE_NAME)
    except AttributeError as exc:
        raise ValueError(
            f"{_REPORT_MODULE_NAME}.{_REPORT_TYPE_NAME} is required",
        ) from exc
    if not isinstance(report_type, type):
        raise ValueError(f"{_REPORT_TYPE_NAME} must be a type")
    return report_type


def _source_queue_report_count(report: Any) -> int:
    if hasattr(report, "source_queue_report_count"):
        return report.source_queue_report_count
    return report.source_queue_count


def _source_queue_status_count(report: Any, field_name: str) -> int:
    attr_name = f"source_queue_{field_name.removesuffix('_count')}_count"
    if hasattr(report, attr_name):
        return getattr(report, attr_name)
    return sum(getattr(summary, field_name) for summary in report.source_queue_summaries)


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_report_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_report_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_report_tree(item, f"{field_name}.{index}")


def _validate_row_matches_payload(
    row: PaperAutonomousAllocationProposalDbRow,
    expected: PaperAutonomousAllocationProposalDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_payload_consistency(
    row: PaperAutonomousAllocationProposalDbRow,
) -> None:
    _reject_json_floats(row.reason_code_counts_json)
    _reject_json_floats(row.allocation_rows_json)
    _reject_json_floats(row.payload_json)
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_required_json_hard_flags_array(
        "reason_code_counts_json",
        row.reason_code_counts_json,
    )
    _validate_required_json_hard_flags_array(
        "allocation_rows_json",
        row.allocation_rows_json,
    )
    _validate_row_flags_match_payload(row)

    allocation_report_json = row.payload_json.get("allocation_report")
    if not isinstance(allocation_report_json, dict):
        raise ValueError("payload_json allocation_report must be a JSON object")
    _require_json_hard_flags("payload_json allocation_report", allocation_report_json)
    _validate_optional_required_json_hard_flags_array(
        "payload_json source_queue_summaries",
        row.payload_json,
        "source_queue_summaries",
    )

    _validate_row_field_matches_payload(
        "reason_codes_json",
        row.reason_codes_json,
        row.payload_json.get("reason_codes"),
    )
    _validate_row_field_matches_payload(
        "reason_code_counts_json",
        row.reason_code_counts_json,
        row.payload_json.get("reason_code_counts"),
    )
    _validate_row_field_matches_payload(
        "allocation_rows_json",
        row.allocation_rows_json,
        allocation_report_json.get("rows"),
    )
    for row_field_name, payload_field_name in _ROOT_PAYLOAD_FIELD_MAP:
        _validate_row_field_matches_payload(
            row_field_name,
            getattr(row, row_field_name),
            row.payload_json.get(payload_field_name),
        )
    _validate_source_queue_count_matches_payload(row)
    for row_field_name, payload_field_name in _ALLOCATION_REPORT_FIELD_MAP:
        _validate_row_field_matches_payload(
            row_field_name,
            getattr(row, row_field_name),
            allocation_report_json.get(payload_field_name),
        )


def _validate_row_flags_match_payload(
    row: PaperAutonomousAllocationProposalDbRow,
) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        _validate_row_field_matches_payload(
            field_name,
            getattr(row, field_name),
            row.payload_json.get(field_name),
        )


def _validate_source_queue_count_matches_payload(
    row: PaperAutonomousAllocationProposalDbRow,
) -> None:
    if "source_queue_report_count" in row.payload_json:
        source_queue_report_count = row.payload_json.get("source_queue_report_count")
    else:
        source_queue_report_count = row.payload_json.get("source_queue_count")
    _validate_row_field_matches_payload(
        "source_queue_report_count",
        row.source_queue_report_count,
        source_queue_report_count,
    )

    for row_field_name in (
        "source_queue_ready_count",
        "source_queue_watch_count",
        "source_queue_blocked_count",
    ):
        if row_field_name in row.payload_json:
            expected_value = row.payload_json.get(row_field_name)
        else:
            expected_value = _source_queue_summary_count(
                row.payload_json,
                row_field_name.removeprefix("source_queue_"),
            )
        _validate_row_field_matches_payload(
            row_field_name,
            getattr(row, row_field_name),
            expected_value,
        )


def _source_queue_summary_count(
    payload_json: dict[str, Any],
    summary_field_name: str,
) -> int | None:
    summaries = payload_json.get("source_queue_summaries")
    if not isinstance(summaries, list):
        return None
    total = 0
    for summary in summaries:
        if not isinstance(summary, dict):
            return None
        value = summary.get(summary_field_name)
        if type(value) is not int:
            return None
        total += value
    return total


def _validate_row_field_matches_payload(
    field_name: str,
    row_value: Any,
    payload_value: Any,
) -> None:
    if _json_ready(row_value) != payload_value:
        raise ValueError(f"{field_name} must match payload_json")


def _validate_optional_required_json_hard_flags_array(
    field_name: str,
    payload_json: dict[str, Any],
    payload_key: str,
) -> None:
    if payload_key not in payload_json:
        return
    _validate_required_json_hard_flags_array(field_name, payload_json[payload_key])


def _validate_required_json_hard_flags_array(
    field_name: str,
    value: object,
) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for index, item in enumerate(value):
        _require_json_hard_flags(f"{field_name} {index}", item)


def _require_json_hard_flags(field_name: str, value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("allocation proposal DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return normalized


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    previous: str | None = None
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        normalized.append(item)
        seen.add(item)
        previous = item
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
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
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_status_next_step(status: str, next_step: str) -> None:
    expected = _NEXT_STEP_BY_STATUS[status]
    if next_step != expected:
        raise ValueError("recommended_next_step must match proposal_status")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value


_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "proposal_status",
    "recommended_next_step",
    "reason_codes_json",
    "reason_code_counts_json",
    "screening_gate_generated_at",
    "screening_gate_config_version",
    "screening_gate_status",
    "screening_gate_recommended_next_step",
    "queue_risk_generated_at",
    "queue_risk_config_version",
    "queue_risk_status",
    "queue_risk_recommended_next_step",
    "source_queue_report_count",
    "source_queue_ready_count",
    "source_queue_watch_count",
    "source_queue_blocked_count",
    "allocation_config_version",
    "allocation_generated_at",
    "allocation_input_count",
    "allocation_row_count",
    "allocation_allocated_count",
    "allocation_capped_count",
    "allocation_no_budget_count",
    "allocation_non_recommend_count",
    "allocation_skipped_count",
    "allocation_total_requested_paper_notional",
    "allocation_total_allocated_paper_notional",
    "allocation_remaining_paper_budget",
    "allocation_total_paper_budget",
    "allocation_max_paper_notional_per_market",
    "allocation_max_paper_notional_per_event",
    "allocation_max_paper_notional_per_theme",
    "allocation_max_paper_notional_per_correlation_group",
    "allocation_rows_json",
    "paper_only",
    "report_only",
    "readonly",
)


_ROOT_PAYLOAD_FIELD_MAP = (
    ("generated_at", "generated_at"),
    ("config_version", "config_version"),
    ("proposal_status", "proposal_status"),
    ("recommended_next_step", "recommended_next_step"),
    ("screening_gate_generated_at", "screening_gate_generated_at"),
    ("screening_gate_config_version", "screening_gate_config_version"),
    ("screening_gate_status", "screening_gate_status"),
    ("screening_gate_recommended_next_step", "screening_gate_recommended_next_step"),
    ("queue_risk_generated_at", "queue_risk_generated_at"),
    ("queue_risk_config_version", "queue_risk_config_version"),
    ("queue_risk_status", "queue_risk_status"),
    ("queue_risk_recommended_next_step", "queue_risk_recommended_next_step"),
)


_ALLOCATION_REPORT_FIELD_MAP = (
    ("allocation_config_version", "config_version"),
    ("allocation_generated_at", "generated_at"),
    ("allocation_input_count", "input_count"),
    ("allocation_row_count", "row_count"),
    ("allocation_allocated_count", "allocated_count"),
    ("allocation_capped_count", "capped_count"),
    ("allocation_no_budget_count", "no_budget_count"),
    ("allocation_non_recommend_count", "non_recommend_count"),
    ("allocation_skipped_count", "skipped_count"),
    ("allocation_total_requested_paper_notional", "total_requested_paper_notional"),
    ("allocation_total_allocated_paper_notional", "total_allocated_paper_notional"),
    ("allocation_remaining_paper_budget", "remaining_paper_budget"),
    ("allocation_total_paper_budget", "total_paper_budget"),
    ("allocation_max_paper_notional_per_market", "max_paper_notional_per_market"),
    ("allocation_max_paper_notional_per_event", "max_paper_notional_per_event"),
    ("allocation_max_paper_notional_per_theme", "max_paper_notional_per_theme"),
    (
        "allocation_max_paper_notional_per_correlation_group",
        "max_paper_notional_per_correlation_group",
    ),
)


paper_autonomous_allocation_proposal_report_to_db_row = (
    paper_autonomous_allocation_proposal_to_db_row
)
paper_autonomous_allocation_proposal_report_from_db_row = (
    paper_autonomous_allocation_proposal_from_db_row
)
