"""Pure row codec for persisted probability selection/scorer agreement reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementReport,
)


__all__ = (
    "ProbabilitySelectionScorerAgreementDbRow",
    "from_db_row",
    "probability_selection_scorer_agreement_from_db_row",
    "probability_selection_scorer_agreement_report_from_db_row",
    "probability_selection_scorer_agreement_report_to_db_row",
    "probability_selection_scorer_agreement_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "selection_generated_at",
    "scorer_generated_at",
    "selected_count",
    "scorer_candidate_count",
    "selected_market_overlap_count",
    "selected_condition_overlap_count",
    "rejected_but_scored_count",
    "scored_but_unselected_count",
    "scorer_gate_status",
    "agreement_status",
    "recommended_next_step",
    "reason_codes_json",
    "reason_code_divergence_counts_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    selection_generated_at: datetime | None
    scorer_generated_at: datetime | None
    selected_count: int
    scorer_candidate_count: int
    selected_market_overlap_count: int
    selected_condition_overlap_count: int
    rejected_but_scored_count: int
    scored_but_unselected_count: int
    scorer_gate_status: str
    agreement_status: str
    recommended_next_step: str
    reason_codes_json: list[str]
    reason_code_divergence_counts_json: list[list[Any]]
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
            "selection_generated_at",
            _optional_utc("selection_generated_at", self.selection_generated_at),
        )
        object.__setattr__(
            self,
            "scorer_generated_at",
            _optional_utc("scorer_generated_at", self.scorer_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "selected_count",
            "scorer_candidate_count",
            "selected_market_overlap_count",
            "selected_condition_overlap_count",
            "rejected_but_scored_count",
            "scored_but_unselected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_canonical_string("scorer_gate_status", self.scorer_gate_status)
        _require_canonical_string("agreement_status", self.agreement_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "reason_code_divergence_counts_json",
            _normalize_divergence_counts_json(
                self.reason_code_divergence_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def probability_selection_scorer_agreement_to_db_row(
    report: ProbabilitySelectionScorerAgreementReport,
) -> ProbabilitySelectionScorerAgreementDbRow:
    if type(report) is not ProbabilitySelectionScorerAgreementReport:
        raise ValueError("report must be a ProbabilitySelectionScorerAgreementReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_codes_json = _require_payload_array(payload_json, "reason_codes")
    divergence_counts_json = _require_payload_array(
        payload_json,
        "reason_code_divergence_counts",
    )
    return ProbabilitySelectionScorerAgreementDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        selection_generated_at=report.selection_generated_at,
        scorer_generated_at=report.scorer_generated_at,
        selected_count=report.selected_count,
        scorer_candidate_count=report.scorer_candidate_count,
        selected_market_overlap_count=report.selected_market_overlap_count,
        selected_condition_overlap_count=report.selected_condition_overlap_count,
        rejected_but_scored_count=report.rejected_but_scored_count,
        scored_but_unselected_count=report.scored_but_unselected_count,
        scorer_gate_status=report.scorer_gate_status,
        agreement_status=report.agreement_status,
        recommended_next_step=report.recommended_next_step,
        reason_codes_json=reason_codes_json,
        reason_code_divergence_counts_json=divergence_counts_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def probability_selection_scorer_agreement_from_db_row(
    row: ProbabilitySelectionScorerAgreementDbRow,
) -> ProbabilitySelectionScorerAgreementReport:
    if type(row) is not ProbabilitySelectionScorerAgreementDbRow:
        raise ValueError("row must be a ProbabilitySelectionScorerAgreementDbRow")
    return _validate_row_payload_consistency(row)


def to_db_row(
    report: ProbabilitySelectionScorerAgreementReport,
) -> ProbabilitySelectionScorerAgreementDbRow:
    return probability_selection_scorer_agreement_to_db_row(report)


def from_db_row(
    row: ProbabilitySelectionScorerAgreementDbRow,
) -> ProbabilitySelectionScorerAgreementReport:
    return probability_selection_scorer_agreement_from_db_row(row)


def _validate_row_payload_consistency(
    row: ProbabilitySelectionScorerAgreementDbRow,
) -> ProbabilitySelectionScorerAgreementReport:
    _validate_row_shape(row)
    raw_payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(raw_payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(raw_payload_json, "payload_json")
    _require_payload_flags_match_row(raw_payload_json, "payload_json", row)
    try:
        report = from_jsonable(
            ProbabilitySelectionScorerAgreementReport,
            raw_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid probability selection scorer "
            f"agreement report: {exc}",
        ) from exc
    if type(report) is not ProbabilitySelectionScorerAgreementReport:
        raise ValueError(
            "payload_json must recover a ProbabilitySelectionScorerAgreementReport",
        )
    _validate_report_tree(report)
    _validate_row_matches_payload(row, report, payload_json=raw_payload_json)
    return report


def _validate_row_shape(row: ProbabilitySelectionScorerAgreementDbRow) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _optional_utc("selection_generated_at", row.selection_generated_at)
    _optional_utc("scorer_generated_at", row.scorer_generated_at)
    _require_canonical_string("config_version", row.config_version)
    for field_name in (
        "selected_count",
        "scorer_candidate_count",
        "selected_market_overlap_count",
        "selected_condition_overlap_count",
        "rejected_but_scored_count",
        "scored_but_unselected_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    _require_canonical_string("scorer_gate_status", row.scorer_gate_status)
    _require_canonical_string("agreement_status", row.agreement_status)
    _require_canonical_string("recommended_next_step", row.recommended_next_step)
    _normalize_string_list("reason_codes_json", row.reason_codes_json)
    _normalize_divergence_counts_json(row.reason_code_divergence_counts_json)
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
    row: ProbabilitySelectionScorerAgreementDbRow,
    report: ProbabilitySelectionScorerAgreementReport,
    *,
    payload_json: dict[str, Any],
) -> None:
    canonical_payload_json = _json_ready(asdict(report))
    expected_values = {
        "report_sha256": row.report_sha256,
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "selection_generated_at": report.selection_generated_at,
        "scorer_generated_at": report.scorer_generated_at,
        "selected_count": report.selected_count,
        "scorer_candidate_count": report.scorer_candidate_count,
        "selected_market_overlap_count": report.selected_market_overlap_count,
        "selected_condition_overlap_count": report.selected_condition_overlap_count,
        "rejected_but_scored_count": report.rejected_but_scored_count,
        "scored_but_unselected_count": report.scored_but_unselected_count,
        "scorer_gate_status": report.scorer_gate_status,
        "agreement_status": report.agreement_status,
        "recommended_next_step": report.recommended_next_step,
        "reason_codes_json": report.reason_codes,
        "reason_code_divergence_counts_json": canonical_payload_json.get(
            "reason_code_divergence_counts",
        ),
        "payload_json": canonical_payload_json,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "selection_generated_at": row.selection_generated_at,
        "scorer_generated_at": row.scorer_generated_at,
        "selected_count": row.selected_count,
        "scorer_candidate_count": row.scorer_candidate_count,
        "selected_market_overlap_count": row.selected_market_overlap_count,
        "selected_condition_overlap_count": row.selected_condition_overlap_count,
        "rejected_but_scored_count": row.rejected_but_scored_count,
        "scored_but_unselected_count": row.scored_but_unselected_count,
        "scorer_gate_status": row.scorer_gate_status,
        "agreement_status": row.agreement_status,
        "recommended_next_step": row.recommended_next_step,
        "reason_codes_json": row.reason_codes_json,
        "reason_code_divergence_counts_json": row.reason_code_divergence_counts_json,
        "payload_json": payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _MATERIALIZED_FIELDS:
        if not _json_equal_strict(
            _json_ready(actual_values[field_name]),
            _json_ready(expected_values[field_name]),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _require_payload_flags_match_row(
    payload_json: dict[str, Any],
    field_name: str,
    row: ProbabilitySelectionScorerAgreementDbRow,
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


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
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
    raise ValueError("agreement DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
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
    return normalized


def _normalize_divergence_counts_json(value: object) -> list[list[Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_divergence_counts_json must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_code_divergence_counts_json must be a JSON array")
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
            raise ValueError(
                "reason_code_divergence_counts_json entries must be reason/count pairs",
            )
        reason_code, count = item
        _require_canonical_string("reason_code_divergence_counts_json", reason_code)
        _require_nonnegative_int("reason_code_divergence_counts_json", count)
        if count == 0:
            raise ValueError("reason_code_divergence_counts_json counts must be positive")
        if reason_code in seen:
            raise ValueError("reason_code_divergence_counts_json must be unique")
        if previous_code is not None and previous_code > reason_code:
            raise ValueError("reason_code_divergence_counts_json must be sorted")
        normalized.append([reason_code, count])
        previous_code = reason_code
        seen.add(reason_code)
    return normalized


def _require_payload_array(payload_json: dict[str, Any], field_name: str) -> list[Any]:
    value = payload_json.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"payload_json {field_name} must be a JSON array")
    return list(value)


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


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not be a datetime")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


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


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


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


probability_selection_scorer_agreement_report_to_db_row = (
    probability_selection_scorer_agreement_to_db_row
)
probability_selection_scorer_agreement_report_from_db_row = (
    probability_selection_scorer_agreement_from_db_row
)
