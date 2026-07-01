"""Pure row codec for paper autonomous screening gate transition trend reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend import (
    PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport,
)


__all__ = (
    "PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow",
    "from_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_trend_from_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_trend_report_from_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_trend_report_to_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_trend_to_db_row",
    "to_db_row",
)


_GATE_STATUSES = ("pass", "watch", "blocked")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_MISSING = object()


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    transition_report_count: int
    first_transition_generated_at: datetime | None
    latest_transition_generated_at: datetime | None
    latest_from_gate_status: str | None
    latest_to_gate_status: str | None
    latest_introduced_reason_code_count: int
    latest_cleared_reason_code_count: int
    latest_persistent_reason_code_count: int
    latest_transition_count: int
    latest_instability_ratio: Decimal | None
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
            "first_transition_generated_at",
            _as_optional_utc(
                "first_transition_generated_at",
                self.first_transition_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_transition_generated_at",
            _as_optional_utc(
                "latest_transition_generated_at",
                self.latest_transition_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "transition_report_count",
            self.transition_report_count,
        )
        _require_optional_gate_status(
            "latest_from_gate_status",
            self.latest_from_gate_status,
        )
        _require_optional_gate_status(
            "latest_to_gate_status",
            self.latest_to_gate_status,
        )
        for field_name in (
            "latest_introduced_reason_code_count",
            "latest_cleared_reason_code_count",
            "latest_persistent_reason_code_count",
            "latest_transition_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_instability_ratio",
            _normalize_optional_ratio_decimal(
                "latest_instability_ratio",
                self.latest_instability_ratio,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_count_nullability_consistency(self)
        _validate_materialized_fields_match_payload(self)
        _validate_payload_recovers_to_compatible_report(self.payload_json)


def paper_autonomous_screening_decision_support_gate_transition_trend_to_db_row(
    report: Any,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow:
    if (
        type(report)
        is not PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport
    ):
        raise ValueError(
            "report must be a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport",
        )
    _require_hard_flags("report", report)
    payload_json = _json_ready(asdict(report))
    return PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        transition_report_count=report.transition_report_count,
        first_transition_generated_at=report.first_transition_generated_at,
        latest_transition_generated_at=report.latest_transition_generated_at,
        latest_from_gate_status=report.latest_from_gate_status,
        latest_to_gate_status=report.latest_to_gate_status,
        latest_introduced_reason_code_count=(
            report.latest_introduced_reason_code_count
        ),
        latest_cleared_reason_code_count=report.latest_cleared_reason_code_count,
        latest_persistent_reason_code_count=(
            report.latest_persistent_reason_code_count
        ),
        latest_transition_count=report.latest_transition_count,
        latest_instability_ratio=report.latest_instability_ratio,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_screening_decision_support_gate_transition_trend_from_db_row(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    if (
        type(row)
        is not PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow
    ):
        raise ValueError(
            "row must be a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow",
        )
    _reject_json_noncanonical_values(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row)
    report = _validate_payload_recovers_to_compatible_report(row.payload_json)
    expected_row = (
        paper_autonomous_screening_decision_support_gate_transition_trend_to_db_row(
            report,
        )
    )
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: Any,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow:
    return paper_autonomous_screening_decision_support_gate_transition_trend_to_db_row(
        report,
    )


def from_db_row(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    return paper_autonomous_screening_decision_support_gate_transition_trend_from_db_row(
        row,
    )


def _validate_payload_recovers_to_compatible_report(
    payload_json: dict[str, Any],
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    try:
        report = from_jsonable(
            PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport,
            payload_json,
        )
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid autonomous screening gate transition "
            f"trend report: {exc}",
        ) from exc
    if (
        type(report)
        is not PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport
    ):
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport",
        )
    _require_hard_flags("report", report)
    expected_payload_json = _json_ready(asdict(report))
    _validate_json_compatible(payload_json, expected_payload_json)
    return report


def _validate_materialized_fields_match_payload(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    for field_name in _SCALAR_PAYLOAD_FIELDS:
        expected_values[field_name] = payload_json.get(field_name, _MISSING)
    actual_values = {
        "report_sha256": row.report_sha256,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _SCALAR_PAYLOAD_FIELDS:
        actual_values[field_name] = _json_ready(getattr(row, field_name))
    for field_name in _MATERIALIZED_FIELDS:
        if actual_values[field_name] != expected_values[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_matches_payload(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
    expected: PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_count_nullability_consistency(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionTrendDbRow,
) -> None:
    has_transition_bounds = (
        row.first_transition_generated_at is not None
        and row.latest_transition_generated_at is not None
    )
    if row.transition_report_count == 0:
        if row.first_transition_generated_at is not None:
            raise ValueError(
                "transition_report_count must be positive when "
                "first_transition_generated_at is present",
            )
        if row.latest_transition_generated_at is not None:
            raise ValueError(
                "transition_report_count must be positive when "
                "latest_transition_generated_at is present",
            )
    elif not has_transition_bounds:
        raise ValueError(
            "transition_report_count must have first and latest transition "
            "generated timestamps when positive",
        )

    has_latest_status_pair = (
        row.latest_from_gate_status is not None
        and row.latest_to_gate_status is not None
    )
    if row.latest_transition_count == 0:
        if row.latest_from_gate_status is not None:
            raise ValueError(
                "latest_transition_count must be positive when "
                "latest_from_gate_status is present",
            )
        if row.latest_to_gate_status is not None:
            raise ValueError(
                "latest_transition_count must be positive when "
                "latest_to_gate_status is present",
            )
    elif not has_latest_status_pair:
        raise ValueError(
            "latest_transition_count must have latest from/to gate statuses "
            "when positive",
        )


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
        return _decimal_to_json(value)
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
    raise ValueError(
        "autonomous screening gate transition trend row values must be JSON "
        "serializable",
    )


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    return normalized


def _copy_json_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain datetime")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_payload(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_payload(item) for item in value]
    raise ValueError("JSON value must be a dict, list, string, int, bool, or null")


def _decimal_to_json(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("JSON Decimal value must be finite")
    with localcontext() as context:
        context.prec = max(
            28,
            len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 6,
        )
        quantized = value.quantize(_DECIMAL_QUANTUM)
    if value != quantized:
        raise ValueError("JSON Decimal value must have at most six decimal places")
    if quantized.is_zero():
        quantized = Decimal("0.000000")
    return format(quantized, "f")


def _validate_json_compatible(
    actual: object,
    expected: object,
    path: tuple[str, ...] = (),
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{'.'.join(path) or 'payload_json'} has wrong JSON type")
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():  # type: ignore[union-attr]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} keys differ")
        for key in actual:
            _validate_json_compatible(
                actual[key],
                expected[key],  # type: ignore[index]
                (*path, key),
            )
        return
    if isinstance(actual, list):
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} length differs")
        for index, item in enumerate(actual):
            _validate_json_compatible(
                item,
                expected[index],  # type: ignore[index]
                (*path, str(index)),
            )
        return
    if actual != expected:
        raise ValueError(f"{'.'.join(path) or 'payload_json'} differs")


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


def _reject_json_noncanonical_values(value: Any) -> None:
    if isinstance(value, (Decimal, datetime, float)):
        raise ValueError("JSON value must not contain raw non-JSON values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_noncanonical_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_noncanonical_values(item)


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


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
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


def _require_optional_gate_status(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = max(
            28,
            len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 6,
        )
        quantized = value.quantize(_DECIMAL_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if value < Decimal("0.000000") or value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    if quantized.is_zero():
        quantized = Decimal("0.000000")
    return quantized


_SCALAR_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "transition_report_count",
    "first_transition_generated_at",
    "latest_transition_generated_at",
    "latest_from_gate_status",
    "latest_to_gate_status",
    "latest_introduced_reason_code_count",
    "latest_cleared_reason_code_count",
    "latest_persistent_reason_code_count",
    "latest_transition_count",
    "latest_instability_ratio",
)
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "paper_only",
    "report_only",
    "readonly",
    *_SCALAR_PAYLOAD_FIELDS,
)


paper_autonomous_screening_decision_support_gate_transition_trend_report_to_db_row = (
    paper_autonomous_screening_decision_support_gate_transition_trend_to_db_row
)
paper_autonomous_screening_decision_support_gate_transition_trend_report_from_db_row = (
    paper_autonomous_screening_decision_support_gate_transition_trend_from_db_row
)
