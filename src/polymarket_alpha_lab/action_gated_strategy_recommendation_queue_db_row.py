"""Pure row codec for persisted action-gated strategy queue reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueDbRow",
    "paper_action_gated_strategy_recommendation_queue_report_from_db_row",
    "paper_action_gated_strategy_recommendation_queue_report_to_db_row",
)


ACTION_STATUSES = ("research_ready", "watch", "blocked")
QUEUE_NEXT_STEPS = (
    "review_candidate_research_queue",
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_MISSING = object()
_DECIMAL_PAYLOAD_PATTERNS = frozenset(
    {
        ("total_ready_notional",),
        (
            "candidate_assessment_report",
            "assessment_rows",
            "*",
            "screening_score",
        ),
        (
            "candidate_assessment_report",
            "assessment_rows",
            "*",
            "net_edge_per_share",
        ),
        (
            "candidate_assessment_report",
            "assessment_rows",
            "*",
            "total_cost_per_share",
        ),
        ("candidate_assessment_report", "assessment_rows", "*", "confidence"),
        ("candidate_assessment_report", "assessment_rows", "*", "spread"),
        ("candidate_assessment_report", "assessment_rows", "*", "resolution_risk"),
        ("candidate_assessment_report", "assessment_rows", "*", "readiness_score"),
        ("bundle_report", "total_selected_notional"),
        (
            "bundle_report",
            "recommendation_report",
            "recommendation_rows",
            "*",
            "recommendation_score",
        ),
        ("bundle_report", "selection_policy_report", "total_selected_notional"),
        (
            "bundle_report",
            "selection_policy_report",
            "selection_rows",
            "*",
            "recommendation_score",
        ),
        (
            "bundle_report",
            "selection_policy_report",
            "selection_rows",
            "*",
            "suggested_position_notional",
        ),
        (
            "bundle_report",
            "selection_policy_report",
            "selection_rows",
            "*",
            "selected_position_notional",
        ),
        ("bundle_report", "selection_policy_report", "total_suggested_notional"),
        ("bundle_report", "selection_policy_report", "skipped_suggested_notional"),
        ("bundle_report", "selection_policy_report", "remaining_total_notional"),
        ("bundle_report", "selection_policy_report", "total_notional_utilization"),
        (
            "bundle_report",
            "explanation_report",
            "explanation_rows",
            "*",
            "recommendation_score",
        ),
        ("bundle_report", "total_suggested_notional"),
        ("bundle_report", "skipped_suggested_notional"),
        ("bundle_report", "remaining_total_notional"),
        ("queue_summary_report", "total_ready_notional"),
        ("queue_summary_report", "top_score"),
        ("queue_summary_report", "average_ready_score"),
        (
            "queue_summary_report",
            "queue_rows",
            "*",
            "recommendation_score",
        ),
        ("queue_summary_report", "queue_rows", "*", "suggested_notional"),
    },
)


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    reason_code_counts_json: dict[str, int]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_action_status("action_status", self.action_status)
        _require_recommended_next_step("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_ACTION_STATUS[self.action_status]:
            raise ValueError("recommended_next_step must match action_status")
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _require_nonnegative_decimal(
                "total_ready_notional",
                self.total_ready_notional,
            ),
        )
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
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_payload_json_contract(self)
        _validate_payload_recovers_to_canonical_report(self.payload_json)
        _require_hard_flags("DB row", self)


def paper_action_gated_strategy_recommendation_queue_report_to_db_row(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> PaperActionGatedStrategyRecommendationQueueDbRow:
    if type(report) is not PaperActionGatedStrategyRecommendationQueueReport:
        raise ValueError(
            "report must be a PaperActionGatedStrategyRecommendationQueueReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperActionGatedStrategyRecommendationQueueDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        action_status=report.action_status,
        recommended_next_step=report.recommended_next_step,
        candidate_count=report.candidate_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        total_ready_notional=report.total_ready_notional,
        reason_code_counts_json={
            item.reason_code: item.count for item in report.reason_code_counts
        },
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_action_gated_strategy_recommendation_queue_report_from_db_row(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    if type(row) is not PaperActionGatedStrategyRecommendationQueueDbRow:
        raise ValueError("row must be a PaperActionGatedStrategyRecommendationQueueDbRow")
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_payload_json_contract(row, payload_json)
    report = _validate_payload_recovers_to_compatible_report(payload_json)
    expected_row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        report,
    )
    _validate_row_matches_payload(row, expected_row, payload_json)
    return report


def _validate_row_core_fields(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    _require_canonical_string("source_config_version", row.source_config_version)
    _require_action_status("action_status", row.action_status)
    _require_recommended_next_step("recommended_next_step", row.recommended_next_step)
    if row.recommended_next_step != NEXT_STEP_BY_ACTION_STATUS[row.action_status]:
        raise ValueError("recommended_next_step must match action_status")
    for field_name in (
        "candidate_count",
        "ready_count",
        "watch_count",
        "blocked_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    _require_nonnegative_decimal("total_ready_notional", row.total_ready_notional)
    _normalize_reason_code_counts_json(
        "reason_code_counts_json",
        row.reason_code_counts_json,
    )
    _require_hard_flags("DB row", row)


def _validate_report_tree(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> None:
    _validate_hard_flags_tree(report, "report")
    _validate_unique_reason_code_counts(report)


def _validate_hard_flags_tree(value: Any, field_name: str) -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_hard_flags_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_hard_flags_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_hard_flags_tree(item, f"{field_name}.{index}")


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _validate_unique_reason_code_counts(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> None:
    seen: set[str] = set()
    for item in report.reason_code_counts:
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(item.reason_code)


def _validate_row_matches_payload(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
    expected: PaperActionGatedStrategyRecommendationQueueDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    for field_name in (
        "generated_at",
        "config_version",
        "source_config_version",
        "action_status",
        "recommended_next_step",
        "candidate_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "reason_code_counts_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if not _json_values_match(
            _json_ready(getattr(row, field_name)),
            _json_ready(getattr(expected, field_name)),
        ):
            raise ValueError(f"{field_name} must match payload_json")
    _require_materialized_decimal_match(
        "total_ready_notional",
        row.total_ready_notional,
        payload_json.get("total_ready_notional", _MISSING),
    )


def _validate_payload_json_contract(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    _validate_json_hard_flags(payload_json, "payload_json")
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    for field_name in (
        "generated_at",
        "config_version",
        "source_config_version",
        "action_status",
        "recommended_next_step",
        "candidate_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _validate_payload_field_matches_row(row, field_name, payload_json)
    _require_materialized_decimal_match(
        "total_ready_notional",
        row.total_ready_notional,
        payload_json.get("total_ready_notional", _MISSING),
    )
    if not _json_values_match(
        _normalize_payload_reason_code_counts(
            "payload_json reason_code_counts",
            payload_json.get("reason_code_counts"),
        ),
        row.reason_code_counts_json,
    ):
        raise ValueError("reason_code_counts_json must match payload_json")


def _validate_payload_recovers_to_compatible_report(
    payload_json: dict[str, Any],
) -> PaperActionGatedStrategyRecommendationQueueReport:
    try:
        report = from_jsonable(
            PaperActionGatedStrategyRecommendationQueueReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid action-gated queue report: {exc}",
        ) from exc
    if type(report) is not PaperActionGatedStrategyRecommendationQueueReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperActionGatedStrategyRecommendationQueueReport",
        )
    _validate_report_tree(report)
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        _canonical_report_payload(report),
    )
    return report


def _validate_payload_recovers_to_canonical_report(
    payload_json: dict[str, Any],
) -> None:
    _validate_payload_recovers_to_compatible_report(payload_json)


def _canonical_report_payload(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload_json must recover a JSON object")
    return payload


def _validate_payload_field_matches_row(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
    field_name: str,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    if not _json_values_match(
        payload_json.get(field_name),
        _json_ready(getattr(row, field_name)),
    ):
        raise ValueError(f"{field_name} must match payload_json")


def _require_materialized_decimal_match(
    field_name: str,
    row_value: Decimal,
    payload_value: object,
) -> None:
    if type(payload_value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    try:
        payload_decimal = Decimal(payload_value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must match payload_json") from exc
    if not payload_decimal.is_finite() or payload_decimal != row_value:
        raise ValueError(f"{field_name} must match payload_json")


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


def _validate_payload_compatible_with_canonical_payload(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    try:
        _validate_json_compatible((), payload_json, expected_payload_json)
    except ValueError as exc:
        raise ValueError(
            "payload_json must match canonical action-gated queue report: "
            f"{exc}",
        ) from exc


def _validate_json_compatible(
    path: tuple[str, ...],
    actual: object,
    expected: object,
) -> None:
    if _is_decimal_payload_path(path):
        _validate_compatible_decimal_path(".".join(path), actual, expected)
        return
    if type(actual) is not type(expected):
        raise ValueError(f"{'.'.join(path) or 'payload_json'} has wrong JSON type")
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():  # type: ignore[union-attr]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} keys differ")
        for key in actual:
            _validate_json_compatible(
                (*path, key),
                actual[key],
                expected[key],  # type: ignore[index]
            )
        return
    if isinstance(actual, list):
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} length differs")
        for index, item in enumerate(actual):
            _validate_json_compatible(
                (*path, str(index)),
                item,
                expected[index],  # type: ignore[index]
            )
        return
    if actual != expected:
        raise ValueError(f"{'.'.join(path) or 'payload_json'} differs")


def _is_decimal_payload_path(path: tuple[str, ...]) -> bool:
    for pattern in _DECIMAL_PAYLOAD_PATTERNS:
        if len(path) != len(pattern):
            continue
        if all(
            pattern_part == "*" or pattern_part == path_part
            for pattern_part, path_part in zip(pattern, path, strict=True)
        ):
            return True
    return False


def _validate_compatible_decimal_path(
    field_name: str,
    actual: object,
    expected: object,
) -> None:
    if actual is None or expected is None:
        if actual is not expected:
            raise ValueError(f"{field_name} differs")
        return
    if type(actual) is not str or type(expected) is not str:
        raise ValueError(f"{field_name} has wrong JSON type")
    try:
        actual_decimal = Decimal(actual)
        expected_decimal = Decimal(expected)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is not a Decimal string") from exc
    if (
        not actual_decimal.is_finite()
        or not expected_decimal.is_finite()
        or actual_decimal != expected_decimal
    ):
        raise ValueError(f"{field_name} differs")


def _normalize_payload_reason_code_counts(
    field_name: str,
    value: object,
) -> dict[str, int]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: dict[str, int] = {}
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} {index} must be a JSON object")
        if set(item) != {"reason_code", "count"}:
            raise ValueError(
                f"{field_name} {index} must contain reason_code and count",
            )
        reason_code = item["reason_code"]
        count = item["count"]
        _require_canonical_token(f"{field_name} {index} reason_code", reason_code)
        if type(count) is not int or count <= 0:
            raise ValueError(f"{field_name} {index} count must be a positive int")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        normalized[reason_code] = count
    return normalized


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
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("action-gated queue DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


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
        raise ValueError("JSON Decimal value must be quantized to six decimal places")
    return format(quantized, "f")


def _copy_json_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
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


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    for key, item in normalized.items():
        _require_canonical_token(f"{field_name} key", key)
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


def _require_canonical_token(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a canonical token")


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_recommended_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known recommended next step")


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


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
