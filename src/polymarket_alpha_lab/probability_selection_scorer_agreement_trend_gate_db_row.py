"""Pure row codec for persisted probability selection/scorer agreement trend gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
    ProbabilitySelectionScorerAgreementTrendGateReport,
)


__all__ = (
    "ProbabilitySelectionScorerAgreementTrendGateDbRow",
    "from_db_row",
    "probability_selection_scorer_agreement_trend_gate_from_db_row",
    "probability_selection_scorer_agreement_trend_gate_report_from_db_row",
    "probability_selection_scorer_agreement_trend_gate_report_to_db_row",
    "probability_selection_scorer_agreement_trend_gate_to_db_row",
    "to_db_row",
)


ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_LIKE_STRING_PATTERN = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)$")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_REPORT_DECIMAL_FIELDS = (
    "average_selected_count",
    "average_scorer_candidate_count",
)
_GATE_STATUSES = ("pass", "watch", "blocked")
_TREND_STATUSES = ("insufficient_history", "blocked", "watch", "stable")
_AGREEMENT_STATUSES = (
    "aligned",
    "gate_blocked",
    "insufficient_identifiers",
    "low_overlap",
    "missing_inputs",
)
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "source_generated_at",
    "trend_report_age_seconds",
    "gate_status",
    "recommended_next_step",
    "reason_code_counts_json",
    "source_report_count",
    "source_trend_status",
    "source_recommended_next_step",
    "latest_agreement_status",
    "latest_agreement_status_streak",
    "aligned_report_count",
    "low_overlap_report_count",
    "gate_blocked_report_count",
    "missing_inputs_report_count",
    "insufficient_identifiers_report_count",
    "average_selected_count",
    "average_scorer_candidate_count",
    "latest_source_reason_codes_json",
    "recurring_source_reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendGateDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    trend_report_age_seconds: int
    gate_status: str
    recommended_next_step: str
    reason_code_counts_json: list[dict[str, Any]]
    source_report_count: int
    source_trend_status: str
    source_recommended_next_step: str
    latest_agreement_status: str
    latest_agreement_status_streak: int
    aligned_report_count: int
    low_overlap_report_count: int
    gate_blocked_report_count: int
    missing_inputs_report_count: int
    insufficient_identifiers_report_count: int
    average_selected_count: Decimal
    average_scorer_candidate_count: Decimal
    latest_source_reason_codes_json: list[str]
    recurring_source_reason_code_counts_json: list[list[Any]]
    reason_codes_json: list[str]
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
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_nonnegative_int(
            "trend_report_age_seconds",
            self.trend_report_age_seconds,
        )
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_reason_code_counts_json(
                "reason_code_counts_json",
                self.reason_code_counts_json,
            ),
        )
        _require_nonnegative_int("source_report_count", self.source_report_count)
        _require_trend_status("source_trend_status", self.source_trend_status)
        _require_canonical_string(
            "source_recommended_next_step",
            self.source_recommended_next_step,
        )
        _require_agreement_status(
            "latest_agreement_status",
            self.latest_agreement_status,
        )
        for field_name in (
            "latest_agreement_status_streak",
            "aligned_report_count",
            "low_overlap_report_count",
            "gate_blocked_report_count",
            "missing_inputs_report_count",
            "insufficient_identifiers_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in _REPORT_DECIMAL_FIELDS:
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_source_reason_codes_json",
            _normalize_string_list(
                "latest_source_reason_codes_json",
                self.latest_source_reason_codes_json,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "recurring_source_reason_code_counts_json",
            _normalize_count_pairs_json(
                "recurring_source_reason_code_counts_json",
                self.recurring_source_reason_code_counts_json,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list(
                "reason_codes_json",
                self.reason_codes_json,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def probability_selection_scorer_agreement_trend_gate_to_db_row(
    report: ProbabilitySelectionScorerAgreementTrendGateReport,
) -> ProbabilitySelectionScorerAgreementTrendGateDbRow:
    if type(report) is not ProbabilitySelectionScorerAgreementTrendGateReport:
        raise ValueError(
            "report must be a ProbabilitySelectionScorerAgreementTrendGateReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_code_counts_json = _require_payload_array(
        payload_json,
        "reason_code_counts",
    )
    latest_source_reason_codes_json = _require_payload_array(
        payload_json,
        "latest_source_reason_codes",
    )
    recurring_counts_json = _require_payload_array(
        payload_json,
        "recurring_source_reason_code_counts",
    )
    reason_codes_json = _require_payload_array(payload_json, "reason_codes")
    return ProbabilitySelectionScorerAgreementTrendGateDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        source_generated_at=report.source_generated_at,
        trend_report_age_seconds=report.trend_report_age_seconds,
        gate_status=report.gate_status,
        recommended_next_step=report.recommended_next_step,
        reason_code_counts_json=_require_json_object_items(
            "reason_code_counts",
            reason_code_counts_json,
        ),
        source_report_count=report.source_report_count,
        source_trend_status=report.source_trend_status,
        source_recommended_next_step=report.source_recommended_next_step,
        latest_agreement_status=report.latest_agreement_status,
        latest_agreement_status_streak=report.latest_agreement_status_streak,
        aligned_report_count=report.aligned_report_count,
        low_overlap_report_count=report.low_overlap_report_count,
        gate_blocked_report_count=report.gate_blocked_report_count,
        missing_inputs_report_count=report.missing_inputs_report_count,
        insufficient_identifiers_report_count=(
            report.insufficient_identifiers_report_count
        ),
        average_selected_count=report.average_selected_count,
        average_scorer_candidate_count=report.average_scorer_candidate_count,
        latest_source_reason_codes_json=_require_string_items(
            "latest_source_reason_codes",
            latest_source_reason_codes_json,
        ),
        recurring_source_reason_code_counts_json=list(recurring_counts_json),
        reason_codes_json=_require_string_items("reason_codes", reason_codes_json),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def probability_selection_scorer_agreement_trend_gate_from_db_row(
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
) -> ProbabilitySelectionScorerAgreementTrendGateReport:
    if type(row) is not ProbabilitySelectionScorerAgreementTrendGateDbRow:
        raise ValueError(
            "row must be a ProbabilitySelectionScorerAgreementTrendGateDbRow",
        )
    return _validate_row_payload_consistency(row)


def to_db_row(
    report: ProbabilitySelectionScorerAgreementTrendGateReport,
) -> ProbabilitySelectionScorerAgreementTrendGateDbRow:
    return probability_selection_scorer_agreement_trend_gate_to_db_row(report)


def from_db_row(
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
) -> ProbabilitySelectionScorerAgreementTrendGateReport:
    return probability_selection_scorer_agreement_trend_gate_from_db_row(row)


def _validate_row_payload_consistency(
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
) -> ProbabilitySelectionScorerAgreementTrendGateReport:
    _validate_row_shape(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_payload_decimal_strings(payload_json)
    _require_payload_flags_match_row(payload_json, "payload_json", row)
    try:
        report = from_jsonable(
            ProbabilitySelectionScorerAgreementTrendGateReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid probability selection scorer agreement "
            f"trend-gate report: {exc}",
        ) from exc
    if type(report) is not ProbabilitySelectionScorerAgreementTrendGateReport:
        raise ValueError(
            "payload_json must recover a "
            "ProbabilitySelectionScorerAgreementTrendGateReport",
        )
    _validate_report_tree(report)
    _validate_row_matches_payload(row, report, payload_json=payload_json)
    return report


def _validate_row_shape(
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    _require_canonical_string("source_config_version", row.source_config_version)
    _as_utc("source_generated_at", row.source_generated_at)
    _require_nonnegative_int(
        "trend_report_age_seconds",
        row.trend_report_age_seconds,
    )
    _require_gate_status("gate_status", row.gate_status)
    _require_canonical_string("recommended_next_step", row.recommended_next_step)
    _normalize_reason_code_counts_json(
        "reason_code_counts_json",
        row.reason_code_counts_json,
    )
    _require_nonnegative_int("source_report_count", row.source_report_count)
    _require_trend_status("source_trend_status", row.source_trend_status)
    _require_canonical_string(
        "source_recommended_next_step",
        row.source_recommended_next_step,
    )
    _require_agreement_status(
        "latest_agreement_status",
        row.latest_agreement_status,
    )
    for field_name in (
        "latest_agreement_status_streak",
        "aligned_report_count",
        "low_overlap_report_count",
        "gate_blocked_report_count",
        "missing_inputs_report_count",
        "insufficient_identifiers_report_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    for field_name in _REPORT_DECIMAL_FIELDS:
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    _normalize_string_list(
        "latest_source_reason_codes_json",
        row.latest_source_reason_codes_json,
        allow_empty=False,
    )
    _normalize_count_pairs_json(
        "recurring_source_reason_code_counts_json",
        row.recurring_source_reason_code_counts_json,
        allow_empty=True,
    )
    _normalize_string_list(
        "reason_codes_json",
        row.reason_codes_json,
        allow_empty=False,
    )
    _normalize_json_object("payload_json", row.payload_json)
    _require_hard_flags("DB row", row)


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
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
    report: ProbabilitySelectionScorerAgreementTrendGateReport,
    *,
    payload_json: dict[str, Any],
) -> None:
    canonical_payload_json = _json_ready(asdict(report))
    expected_values = {
        "report_sha256": row.report_sha256,
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "source_config_version": report.source_config_version,
        "source_generated_at": report.source_generated_at,
        "trend_report_age_seconds": report.trend_report_age_seconds,
        "gate_status": report.gate_status,
        "recommended_next_step": report.recommended_next_step,
        "reason_code_counts_json": canonical_payload_json.get("reason_code_counts"),
        "source_report_count": report.source_report_count,
        "source_trend_status": report.source_trend_status,
        "source_recommended_next_step": report.source_recommended_next_step,
        "latest_agreement_status": report.latest_agreement_status,
        "latest_agreement_status_streak": report.latest_agreement_status_streak,
        "aligned_report_count": report.aligned_report_count,
        "low_overlap_report_count": report.low_overlap_report_count,
        "gate_blocked_report_count": report.gate_blocked_report_count,
        "missing_inputs_report_count": report.missing_inputs_report_count,
        "insufficient_identifiers_report_count": (
            report.insufficient_identifiers_report_count
        ),
        "average_selected_count": report.average_selected_count,
        "average_scorer_candidate_count": report.average_scorer_candidate_count,
        "latest_source_reason_codes_json": report.latest_source_reason_codes,
        "recurring_source_reason_code_counts_json": (
            canonical_payload_json.get("recurring_source_reason_code_counts")
        ),
        "reason_codes_json": report.reason_codes,
        "payload_json": canonical_payload_json,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "source_config_version": row.source_config_version,
        "source_generated_at": row.source_generated_at,
        "trend_report_age_seconds": row.trend_report_age_seconds,
        "gate_status": row.gate_status,
        "recommended_next_step": row.recommended_next_step,
        "reason_code_counts_json": row.reason_code_counts_json,
        "source_report_count": row.source_report_count,
        "source_trend_status": row.source_trend_status,
        "source_recommended_next_step": row.source_recommended_next_step,
        "latest_agreement_status": row.latest_agreement_status,
        "latest_agreement_status_streak": row.latest_agreement_status_streak,
        "aligned_report_count": row.aligned_report_count,
        "low_overlap_report_count": row.low_overlap_report_count,
        "gate_blocked_report_count": row.gate_blocked_report_count,
        "missing_inputs_report_count": row.missing_inputs_report_count,
        "insufficient_identifiers_report_count": (
            row.insufficient_identifiers_report_count
        ),
        "average_selected_count": row.average_selected_count,
        "average_scorer_candidate_count": row.average_scorer_candidate_count,
        "latest_source_reason_codes_json": row.latest_source_reason_codes_json,
        "recurring_source_reason_code_counts_json": (
            row.recurring_source_reason_code_counts_json
        ),
        "reason_codes_json": row.reason_codes_json,
        "payload_json": payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _MATERIALIZED_FIELDS:
        if not _json_equal_strict(
            _json_ready_materialized_field(field_name, actual_values[field_name]),
            _json_ready_materialized_field(field_name, expected_values[field_name]),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _require_payload_flags_match_row(
    payload_json: dict[str, Any],
    field_name: str,
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if flag_name not in payload_json:
            raise ValueError(f"{field_name} {flag_name} must match DB row")
        if payload_json[flag_name] is not getattr(row, flag_name):
            raise ValueError(f"{field_name} {flag_name} must match DB row")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any, field_path: tuple[str | int, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), field_path)
    if isinstance(value, Decimal):
        if not _is_decimal_payload_path(field_path):
            raise ValueError(
                f"{_format_payload_path(field_path)} is not an allowed Decimal path",
            )
        return _fixed_six_decimal_string(_format_payload_path(field_path), value)
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
        return {
            key: _json_ready(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    raise ValueError("trend-gate DB row values must be JSON serializable")


def _json_ready_materialized_field(field_name: str, value: Any) -> Any:
    if field_name in _REPORT_DECIMAL_FIELDS:
        return _json_ready(value, (field_name,))
    if field_name == "payload_json":
        return _normalize_legacy_decimal_payload(value)
    return _json_ready(value)


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_raw_json_values(value)
        normalized = _json_ready(value)
        normalized = _normalize_legacy_decimal_payload(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} entries must be JSON objects")
        if set(item) != {
            "reason_code",
            "report_count",
            "paper_only",
            "report_only",
            "readonly",
        }:
            raise ValueError(f"{field_name} entries must have canonical keys")
        reason_code = item["reason_code"]
        report_count = item["report_count"]
        _require_canonical_string(f"{field_name} reason_code", reason_code)
        _require_positive_int(f"{field_name} report_count", report_count)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        for flag_name in _HARD_FLAG_NAMES:
            if item[flag_name] is not True:
                raise ValueError(f"{field_name} {flag_name} must be True")
        normalized.append(
            {
                "paper_only": True,
                "readonly": True,
                "reason_code": reason_code,
                "report_count": report_count,
                "report_only": True,
            },
        )
    return normalized


def _normalize_string_list(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(item)
        seen.add(item)
    return normalized


def _normalize_count_pairs_json(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> list[list[Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[list[Any]] = []
    previous_code: str | None = None
    seen: set[str] = set()
    for item in value:
        if (
            not isinstance(item, (list, tuple))
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not int
        ):
            raise ValueError(f"{field_name} entries must be reason/count pairs")
        reason_code, count = item
        _require_canonical_string(field_name, reason_code)
        _require_positive_int(field_name, count)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous_code is not None and previous_code > reason_code:
            raise ValueError(f"{field_name} must use canonical sequence")
        normalized.append([reason_code, count])
        previous_code = reason_code
        seen.add(reason_code)
    return normalized


def _require_payload_array(payload_json: dict[str, Any], field_name: str) -> list[Any]:
    value = payload_json.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"payload_json {field_name} must be a JSON array")
    return list(value)


def _require_json_object_items(
    field_name: str,
    value: list[Any],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"payload_json {field_name} must contain JSON objects")
        normalized.append(dict(item))
    return normalized


def _require_string_items(field_name: str, value: list[Any]) -> list[str]:
    normalized: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"payload_json {field_name} must contain strings")
        normalized.append(item)
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in _HARD_FLAG_NAMES):
        for flag_name in _HARD_FLAG_NAMES:
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _validate_payload_decimal_strings(payload_json: dict[str, Any]) -> None:
    for field_name in _REPORT_DECIMAL_FIELDS:
        _require_json_decimal_string(
            f"payload_json {field_name}",
            payload_json.get(field_name),
        )


def _normalize_legacy_decimal_payload(
    value: Any,
    field_path: tuple[str | int, ...] = (),
) -> Any:
    if _is_decimal_payload_path(field_path):
        field_name = _format_payload_path(field_path)
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal string")
        return _fixed_six_decimal_string(
            field_name,
            _decimal_from_string(field_name, value),
        )
    if type(value) is str and _DECIMAL_LIKE_STRING_PATTERN.fullmatch(value) is not None:
        raise ValueError(
            f"{_format_payload_path(field_path)} is not an allowed Decimal path",
        )
    if isinstance(value, dict):
        return {
            key: _normalize_legacy_decimal_payload(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _normalize_legacy_decimal_payload(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    return value


def _is_decimal_payload_path(field_path: tuple[str | int, ...]) -> bool:
    return len(field_path) == 1 and field_path[0] in _REPORT_DECIMAL_FIELDS


def _fixed_six_decimal_string(field_name: str, value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    value_tuple = value.as_tuple()
    excess_decimal_places = -value_tuple.exponent - 6
    if excess_decimal_places > 0 and any(
        digit != 0 for digit in value_tuple.digits[-excess_decimal_places:]
    ):
        raise ValueError(f"{field_name} must not exceed six decimal places")
    if value == ZERO:
        return "0.000000"
    return f"{value:.6f}"


def _decimal_from_string(field_name: str, value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _format_payload_path(field_path: tuple[str | int, ...]) -> str:
    if not field_path:
        return "payload_json"
    formatted = "payload_json"
    for item in field_path:
        if isinstance(item, int):
            formatted = f"{formatted}[{item}]"
        else:
            formatted = f"{formatted}.{item}"
    return formatted


def _require_json_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    try:
        decimal = Decimal(value)
        canonical = decimal.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical decimal string") from exc
    if not decimal.is_finite() or decimal < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative finite decimal string")
    if decimal == ZERO:
        canonical = ZERO.quantize(QUANTUM)
    if value != str(canonical):
        raise ValueError(f"{field_name} must be a canonical decimal string")


def _reject_raw_json_values(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not be a Decimal")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not be a datetime")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_json_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_json_values(item)


def _json_equal_strict(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return False
        return all(_json_equal_strict(left[key], right[key]) for key in left)
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(
            _json_equal_strict(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _has_hard_flag(value: Any) -> bool:
    return any(hasattr(value, flag_name) for flag_name in _HARD_FLAG_NAMES)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_trend_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _TREND_STATUSES:
        raise ValueError(f"{field_name} must be a known trend status")


def _require_agreement_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _AGREEMENT_STATUSES:
        raise ValueError(f"{field_name} must be a known agreement status")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


probability_selection_scorer_agreement_trend_gate_report_to_db_row = (
    probability_selection_scorer_agreement_trend_gate_to_db_row
)
probability_selection_scorer_agreement_trend_gate_report_from_db_row = (
    probability_selection_scorer_agreement_trend_gate_from_db_row
)
