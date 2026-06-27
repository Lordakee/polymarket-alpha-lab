"""Pure row codec for paper autonomous screening decision-support gate reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import importlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "PaperAutonomousScreeningDecisionSupportGateDbRow",
    "from_db_row",
    "paper_autonomous_screening_decision_support_gate_from_db_row",
    "paper_autonomous_screening_decision_support_gate_report_from_db_row",
    "paper_autonomous_screening_decision_support_gate_report_to_db_row",
    "paper_autonomous_screening_decision_support_gate_to_db_row",
    "to_db_row",
)


_REPORT_MODULE_NAME = (
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate"
)
_REPORT_TYPE_NAME = "PaperAutonomousScreeningDecisionSupportGateReport"
_GATE_STATUSES = ("pass", "watch", "blocked")
_RANK_STABILITY_STATUSES = ("stable", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_DECIMAL_PAYLOAD_FIELDS = frozenset(
    (
        "queue_total_ready_notional",
        "queue_largest_ready_notional",
        "queue_top_research_priority_score",
        "queue_average_research_priority_score",
    ),
)
_DECIMAL_PAYLOAD_PATHS = frozenset(
    (field_name,) for field_name in _DECIMAL_PAYLOAD_FIELDS
)
_MISSING = object()


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    reason_codes_json: list[str]
    reason_code_counts_json: list[dict[str, Any]]
    operator_flow_gate_config_version: str
    operator_flow_gate_generated_at: datetime
    operator_flow_gate_status: str
    operator_flow_recommended_next_step: str
    queue_priority_generated_at: datetime
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    queue_source_report_count: int
    queue_research_ready_count: int
    queue_watch_count: int
    queue_blocked_count: int
    queue_candidate_count: int
    queue_ready_count: int
    queue_candidate_watch_count: int
    queue_candidate_blocked_count: int
    queue_total_ready_notional: Decimal
    queue_largest_ready_notional: Decimal
    queue_top_research_priority_score: Decimal
    queue_average_research_priority_score: Decimal
    trend_source_snapshot_count: int | None
    trend_latest_risk_status: str | None
    trend_consecutive_latest_watch_count: int | None
    trend_consecutive_latest_blocked_count: int | None
    trend_duplicate_generated_at_count: int | None
    rank_stability_status: str | None
    rank_stable_ready_count: int | None
    rank_unstable_ready_count: int | None
    rank_blocked_count: int | None
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        for field_name in (
            "generated_at",
            "operator_flow_gate_generated_at",
            "queue_priority_generated_at",
            "queue_risk_generated_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "config_version",
            "recommended_next_step",
            "operator_flow_gate_config_version",
            "operator_flow_recommended_next_step",
            "queue_risk_config_version",
            "queue_risk_recommended_next_step",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "gate_status",
            "operator_flow_gate_status",
            "queue_risk_status",
        ):
            _require_gate_status(field_name, getattr(self, field_name))
        if self.trend_latest_risk_status is not None:
            _require_gate_status(
                "trend_latest_risk_status",
                self.trend_latest_risk_status,
            )
        if self.rank_stability_status is not None:
            _require_rank_stability_status(
                "rank_stability_status",
                self.rank_stability_status,
            )
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
        for field_name in (
            "queue_source_report_count",
            "queue_research_ready_count",
            "queue_watch_count",
            "queue_blocked_count",
            "queue_candidate_count",
            "queue_ready_count",
            "queue_candidate_watch_count",
            "queue_candidate_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "trend_source_snapshot_count",
            "trend_consecutive_latest_watch_count",
            "trend_consecutive_latest_blocked_count",
            "trend_duplicate_generated_at_count",
            "rank_stable_ready_count",
            "rank_unstable_ready_count",
            "rank_blocked_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "queue_total_ready_notional",
            "queue_largest_ready_notional",
            "queue_top_research_priority_score",
            "queue_average_research_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_payload_json(
                "payload_json",
                self.report_sha256,
                self.payload_json,
            ),
        )
        object.__setattr__(self, "report_sha256", _report_sha256(self.payload_json))
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_materialized_fields_match_payload(self)
        _validate_payload_recovers_to_canonical_report(self.payload_json)


def paper_autonomous_screening_decision_support_gate_to_db_row(
    report: Any,
) -> PaperAutonomousScreeningDecisionSupportGateDbRow:
    report_type = _report_type()
    if type(report) is not report_type:
        raise ValueError(
            "report must be a PaperAutonomousScreeningDecisionSupportGateReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_codes_json = payload_json.get("reason_codes")
    reason_code_counts_json = payload_json.get("reason_code_counts")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    if not isinstance(reason_code_counts_json, list):
        raise ValueError("payload_json reason_code_counts must be a JSON array")
    return PaperAutonomousScreeningDecisionSupportGateDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_status=report.gate_status,
        recommended_next_step=report.recommended_next_step,
        reason_codes_json=reason_codes_json,
        reason_code_counts_json=reason_code_counts_json,
        operator_flow_gate_config_version=report.operator_flow_gate_config_version,
        operator_flow_gate_generated_at=report.operator_flow_gate_generated_at,
        operator_flow_gate_status=report.operator_flow_gate_status,
        operator_flow_recommended_next_step=report.operator_flow_recommended_next_step,
        queue_priority_generated_at=report.queue_priority_generated_at,
        queue_risk_generated_at=report.queue_risk_generated_at,
        queue_risk_config_version=report.queue_risk_config_version,
        queue_risk_status=report.queue_risk_status,
        queue_risk_recommended_next_step=report.queue_risk_recommended_next_step,
        queue_source_report_count=report.queue_source_report_count,
        queue_research_ready_count=report.queue_research_ready_count,
        queue_watch_count=report.queue_watch_count,
        queue_blocked_count=report.queue_blocked_count,
        queue_candidate_count=report.queue_candidate_count,
        queue_ready_count=report.queue_ready_count,
        queue_candidate_watch_count=report.queue_candidate_watch_count,
        queue_candidate_blocked_count=report.queue_candidate_blocked_count,
        queue_total_ready_notional=report.queue_total_ready_notional,
        queue_largest_ready_notional=report.queue_largest_ready_notional,
        queue_top_research_priority_score=report.queue_top_research_priority_score,
        queue_average_research_priority_score=(
            report.queue_average_research_priority_score
        ),
        trend_source_snapshot_count=report.trend_source_snapshot_count,
        trend_latest_risk_status=report.trend_latest_risk_status,
        trend_consecutive_latest_watch_count=(
            report.trend_consecutive_latest_watch_count
        ),
        trend_consecutive_latest_blocked_count=(
            report.trend_consecutive_latest_blocked_count
        ),
        trend_duplicate_generated_at_count=report.trend_duplicate_generated_at_count,
        rank_stability_status=report.rank_stability_status,
        rank_stable_ready_count=report.rank_stable_ready_count,
        rank_unstable_ready_count=report.rank_unstable_ready_count,
        rank_blocked_count=report.rank_blocked_count,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_screening_decision_support_gate_from_db_row(
    row: PaperAutonomousScreeningDecisionSupportGateDbRow,
) -> Any:
    if type(row) is not PaperAutonomousScreeningDecisionSupportGateDbRow:
        raise ValueError(
            "row must be a PaperAutonomousScreeningDecisionSupportGateDbRow",
        )
    _require_sha256("report_sha256", row.report_sha256)
    reason_code_counts_json = _copy_raw_json_array(
        "reason_code_counts_json",
        row.reason_code_counts_json,
    )
    payload_json = _copy_raw_json_object("payload_json", row.payload_json)
    _validate_raw_payload_hash(row.report_sha256, payload_json)
    payload_json = _normalize_legacy_decimal_payload(payload_json)
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_materialized_fields_match_payload(
        row,
        payload_json=payload_json,
        compare_report_sha256=False,
    )
    if not _json_values_match(
        row.reason_codes_json,
        payload_json.get("reason_codes", _MISSING),
    ):
        raise ValueError("reason_codes_json must match payload_json")
    if not _json_values_match(
        reason_code_counts_json,
        payload_json.get("reason_code_counts", _MISSING),
    ):
        raise ValueError("reason_code_counts_json must match payload_json")
    _validate_row_scalars_match_payload(row, payload_json=payload_json)
    _validate_payload_recovers_to_canonical_report(payload_json)

    report_type = _report_type()
    try:
        report = from_jsonable(report_type, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid autonomous screening gate report: {exc}",
        ) from exc
    if type(report) is not report_type:
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousScreeningDecisionSupportGateReport",
        )
    _validate_report_tree(report)
    expected_row = paper_autonomous_screening_decision_support_gate_to_db_row(report)
    _validate_row_matches_payload(row, expected_row, compare_report_sha256=False)
    return report


def to_db_row(report: Any) -> PaperAutonomousScreeningDecisionSupportGateDbRow:
    return paper_autonomous_screening_decision_support_gate_to_db_row(report)


def from_db_row(row: PaperAutonomousScreeningDecisionSupportGateDbRow) -> Any:
    return paper_autonomous_screening_decision_support_gate_from_db_row(row)


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
    row: PaperAutonomousScreeningDecisionSupportGateDbRow,
    expected: PaperAutonomousScreeningDecisionSupportGateDbRow,
    *,
    compare_report_sha256: bool = True,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if field_name == "report_sha256" and not compare_report_sha256:
            continue
        if not _json_values_match(
            _json_ready(getattr(row, field_name), (field_name,)),
            _json_ready(getattr(expected, field_name), (field_name,)),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_scalars_match_payload(
    row: PaperAutonomousScreeningDecisionSupportGateDbRow,
    *,
    payload_json: dict[str, Any] | None = None,
) -> None:
    payload = row.payload_json if payload_json is None else payload_json
    for field_name in _SCALAR_PAYLOAD_FIELDS:
        if not _json_values_match(
            payload.get(field_name, _MISSING),
            _json_ready(getattr(row, field_name), (field_name,)),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperAutonomousScreeningDecisionSupportGateDbRow,
    *,
    payload_json: dict[str, Any] | None = None,
    compare_report_sha256: bool = True,
) -> None:
    payload_json = row.payload_json if payload_json is None else payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "reason_codes_json": payload_json.get("reason_codes", _MISSING),
        "reason_code_counts_json": payload_json.get("reason_code_counts", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    for field_name in _SCALAR_PAYLOAD_FIELDS:
        expected_values[field_name] = payload_json.get(field_name, _MISSING)
    actual_values = {
        "report_sha256": row.report_sha256,
        "reason_codes_json": row.reason_codes_json,
        "reason_code_counts_json": row.reason_code_counts_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _SCALAR_PAYLOAD_FIELDS:
        actual_values[field_name] = _json_ready(getattr(row, field_name), (field_name,))
    for field_name in ("paper_only", "report_only", "readonly"):
        if not _json_values_match(actual_values[field_name], expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")
    for field_name in _MATERIALIZED_FIELDS:
        if field_name == "report_sha256" and not compare_report_sha256:
            continue
        if field_name in {"paper_only", "report_only", "readonly"}:
            continue
        if not _json_values_match(actual_values[field_name], expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_payload_recovers_to_canonical_report(payload_json: dict[str, Any]) -> None:
    report_type = _report_type()
    try:
        report = from_jsonable(report_type, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid autonomous screening gate report: {exc}",
        ) from exc
    if type(report) is not report_type:
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousScreeningDecisionSupportGateReport",
        )
    _validate_report_tree(report)
    if not _json_values_match(payload_json, _json_ready(asdict(report))):
        raise ValueError("payload_json must match canonical recovered report payload")


def _json_values_match(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if set(left) != set(right):
            return False
        return all(_json_values_match(left[key], right[key]) for key in left)
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(
            _json_values_match(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_raw_payload_hash(report_sha256: str, payload_json: dict[str, Any]) -> None:
    if report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")


def _json_ready(value: Any, path: tuple[object, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), path)
    if isinstance(value, Decimal):
        if not _is_decimal_payload_path(path):
            raise ValueError(f"{_payload_path_name(path)} is not an allowed Decimal path")
        return _fixed_six_decimal_string(_payload_path_name(path), value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, str):
        if _is_decimal_like_string(value) and not _is_decimal_payload_path(path):
            raise ValueError(f"{_payload_path_name(path)} is not an allowed Decimal path")
        return value
    if isinstance(value, (int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item, (*path, key)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item, (*path, index)) for index, item in enumerate(value)]
    raise ValueError("autonomous screening gate row values must be JSON serializable")


def _fixed_six_decimal_string(field_name: str, value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    try:
        with localcontext() as context:
            integer_digits = max(value.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            quantized = value.quantize(_DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must not exceed six decimal places") from exc
    if quantized != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return format(quantized, "f")


def _fixed_six_decimal_json_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _fixed_six_decimal_string(field_name, decimal_value)


def _normalize_payload_json(
    field_name: str,
    report_sha256: str,
    value: object,
) -> dict[str, Any]:
    normalized = _copy_raw_json_object(field_name, value)
    _validate_raw_payload_hash(report_sha256, normalized)
    return _normalize_legacy_decimal_payload(normalized)


def _copy_raw_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    normalized = _copy_raw_json_value(field_name, value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _copy_raw_json_array(field_name: str, value: object) -> list[Any]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized = _copy_raw_json_value(field_name, value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return normalized


def _copy_raw_json_value(field_name: str, value: object) -> Any:
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not be a raw Decimal")
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must not be a raw datetime")
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} JSON object keys must be strings")
            copied[key] = _copy_raw_json_value(f"{field_name}.{key}", item)
        return copied
    if isinstance(value, (list, tuple)):
        return [
            _copy_raw_json_value(f"{field_name}[{index}]", item)
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{field_name} must contain only JSON-safe values")


def _normalize_legacy_decimal_payload(
    value: Any,
    path: tuple[object, ...] = (),
) -> Any:
    if _is_decimal_payload_path(path):
        return _fixed_six_decimal_json_string(_payload_path_name(path), value)
    if isinstance(value, str) and _is_decimal_like_string(value):
        raise ValueError(f"{_payload_path_name(path)} is not an allowed Decimal path")
    if isinstance(value, dict):
        return {
            key: _normalize_legacy_decimal_payload(item, (*path, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _normalize_legacy_decimal_payload(item, (*path, index))
            for index, item in enumerate(value)
        ]
    return value


def _is_decimal_payload_path(path: tuple[object, ...]) -> bool:
    return path in _DECIMAL_PAYLOAD_PATHS


def _is_decimal_like_string(value: str) -> bool:
    try:
        Decimal(value)
    except (InvalidOperation, ValueError):
        return False
    return True


def _payload_path_name(path: tuple[object, ...]) -> str:
    if not path:
        return "payload_json"
    name = "payload_json"
    for item in path:
        if type(item) is int:
            name = f"{name}[{item}]"
        else:
            name = f"{name}.{item}"
    return name


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_raw_json_object(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must contain only JSON-safe values") from exc
    return normalized


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    normalized = _copy_raw_json_array(field_name, value)
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


def _validate_json_hard_flags(
    value: Any,
    field_name: str,
    *,
    hard_flags_required: bool = False,
) -> None:
    if not isinstance(value, dict):
        return
    if hard_flags_required or any(
        flag_name in value for flag_name in ("paper_only", "report_only", "readonly")
    ):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(
                item,
                child_name,
                hard_flags_required=key == "reason_code_counts",
            )
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(
                    element,
                    f"{child_name} {index}",
                    hard_flags_required=key == "reason_code_counts",
                )


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain raw Decimals")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain raw datetimes")
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


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_rank_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _RANK_STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return Decimal(_fixed_six_decimal_string(field_name, value))


_SCALAR_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_next_step",
    "operator_flow_gate_config_version",
    "operator_flow_gate_generated_at",
    "operator_flow_gate_status",
    "operator_flow_recommended_next_step",
    "queue_priority_generated_at",
    "queue_risk_generated_at",
    "queue_risk_config_version",
    "queue_risk_status",
    "queue_risk_recommended_next_step",
    "queue_source_report_count",
    "queue_research_ready_count",
    "queue_watch_count",
    "queue_blocked_count",
    "queue_candidate_count",
    "queue_ready_count",
    "queue_candidate_watch_count",
    "queue_candidate_blocked_count",
    "queue_total_ready_notional",
    "queue_largest_ready_notional",
    "queue_top_research_priority_score",
    "queue_average_research_priority_score",
    "trend_source_snapshot_count",
    "trend_latest_risk_status",
    "trend_consecutive_latest_watch_count",
    "trend_consecutive_latest_blocked_count",
    "trend_duplicate_generated_at_count",
    "rank_stability_status",
    "rank_stable_ready_count",
    "rank_unstable_ready_count",
    "rank_blocked_count",
)
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "reason_codes_json",
    "reason_code_counts_json",
    "paper_only",
    "report_only",
    "readonly",
    *_SCALAR_PAYLOAD_FIELDS,
)


paper_autonomous_screening_decision_support_gate_report_to_db_row = (
    paper_autonomous_screening_decision_support_gate_to_db_row
)
paper_autonomous_screening_decision_support_gate_report_from_db_row = (
    paper_autonomous_screening_decision_support_gate_from_db_row
)
