"""Pure row codec for action-gated queue decision-support snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)
from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow",
    "paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row",
    "paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row",
)


RISK_STATUSES = ("pass", "watch", "blocked")
RISK_NEXT_STEP_BY_STATUS = {
    "pass": "allocate_paper_research_queue",
    "watch": "throttle_paper_research_queue",
    "blocked": "block_paper_research_queue",
}
RISK_REASON_CODES = {
    "empty_queue_reports",
    "source_queue_blocked",
    "total_ready_notional_cap_exceeded",
    "single_queue_ready_notional_cap_exceeded",
    "ready_candidate_count_cap_exceeded",
    "candidate_count_cap_exceeded",
    "source_queue_watch",
    "near_total_ready_notional_cap",
    "near_single_queue_ready_notional_cap",
    "near_ready_candidate_count_cap",
    "near_candidate_count_cap",
    "queue_risk_passed",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow:
    snapshot_sha256: str
    generated_at: datetime
    priority_source_report_count: int
    priority_research_ready_count: int
    priority_watch_count: int
    priority_blocked_count: int
    priority_total_ready_notional: Decimal
    top_research_priority_score: Decimal
    average_research_priority_score: Decimal
    risk_config_version: str
    risk_status: str
    risk_recommended_next_step: str
    risk_source_queue_count: int
    risk_candidate_count: int
    risk_ready_count: int
    risk_total_ready_notional: Decimal
    risk_largest_queue_ready_notional: Decimal
    risk_reason_codes_json: list[str]
    priority_payload_json: dict[str, Any]
    risk_payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("snapshot_sha256", self.snapshot_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "priority_source_report_count",
            "priority_research_ready_count",
            "priority_watch_count",
            "priority_blocked_count",
            "risk_source_queue_count",
            "risk_candidate_count",
            "risk_ready_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "priority_total_ready_notional",
            "top_research_priority_score",
            "average_research_priority_score",
            "risk_total_ready_notional",
            "risk_largest_queue_ready_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_canonical_string("risk_config_version", self.risk_config_version)
        _require_risk_status("risk_status", self.risk_status)
        _require_risk_next_step(
            "risk_recommended_next_step",
            self.risk_recommended_next_step,
        )
        if self.risk_recommended_next_step != RISK_NEXT_STEP_BY_STATUS[self.risk_status]:
            raise ValueError("risk_recommended_next_step must match risk_status")
        object.__setattr__(
            self,
            "risk_reason_codes_json",
            _normalize_risk_reason_codes_json(
                "risk_reason_codes_json",
                self.risk_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "priority_payload_json",
            _normalize_json_object("priority_payload_json", self.priority_payload_json),
        )
        object.__setattr__(
            self,
            "risk_payload_json",
            _normalize_json_object("risk_payload_json", self.risk_payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow:
    if type(priority_report) is not PaperActionGatedStrategyRecommendationQueuePriorityReport:
        raise ValueError(
            "priority_report must be a "
            "PaperActionGatedStrategyRecommendationQueuePriorityReport",
        )
    if type(risk_report) is not PaperActionGatedStrategyRecommendationQueueRiskReport:
        raise ValueError(
            "risk_report must be a "
            "PaperActionGatedStrategyRecommendationQueueRiskReport",
        )
    if _as_utc("priority_report.generated_at", priority_report.generated_at) != _as_utc(
        "risk_report.generated_at",
        risk_report.generated_at,
    ):
        raise ValueError("priority_report generated_at must match risk_report generated_at")

    _validate_hard_flags_tree(priority_report, "priority_report")
    _validate_hard_flags_tree(risk_report, "risk_report")
    _validate_unique_risk_reason_codes(risk_report.reason_codes)
    _validate_priority_and_risk_snapshot_consistency(priority_report, risk_report)

    priority_payload_json = _json_ready(asdict(priority_report))
    risk_payload_json = _json_ready(asdict(risk_report))
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
        snapshot_sha256=_snapshot_sha256(priority_payload_json, risk_payload_json),
        generated_at=priority_report.generated_at,
        priority_source_report_count=priority_report.source_report_count,
        priority_research_ready_count=priority_report.research_ready_count,
        priority_watch_count=priority_report.watch_count,
        priority_blocked_count=priority_report.blocked_count,
        priority_total_ready_notional=priority_report.total_ready_notional,
        top_research_priority_score=priority_report.top_research_priority_score,
        average_research_priority_score=priority_report.average_research_priority_score,
        risk_config_version=risk_report.config_version,
        risk_status=risk_report.status,
        risk_recommended_next_step=risk_report.recommended_next_step,
        risk_source_queue_count=risk_report.source_queue_count,
        risk_candidate_count=risk_report.candidate_count,
        risk_ready_count=risk_report.ready_count,
        risk_total_ready_notional=risk_report.total_ready_notional,
        risk_largest_queue_ready_notional=risk_report.largest_queue_ready_notional,
        risk_reason_codes_json=list(risk_report.reason_codes),
        priority_payload_json=priority_payload_json,
        risk_payload_json=risk_payload_json,
        paper_only=priority_report.paper_only,
        report_only=priority_report.report_only,
        readonly=priority_report.readonly,
    )


def paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
) -> tuple[
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
]:
    if type(row) is not PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow:
        raise ValueError(
            "row must be a "
            "PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow",
        )
    return _validate_row_payload_consistency(row)


def _validate_row_payload_consistency(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
) -> tuple[
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
]:
    _validate_row_shape(row)
    priority_payload_json = _normalize_json_object(
        "priority_payload_json",
        row.priority_payload_json,
    )
    risk_payload_json = _normalize_json_object(
        "risk_payload_json",
        row.risk_payload_json,
    )
    _validate_json_hard_flags(
        priority_payload_json,
        "priority_payload_json",
        require_hard_flags=True,
    )
    _validate_json_hard_flags(
        risk_payload_json,
        "risk_payload_json",
        require_hard_flags=True,
    )
    _require_payload_flags_match_row(
        priority_payload_json,
        "priority_payload_json",
        row,
    )
    _require_payload_flags_match_row(risk_payload_json, "risk_payload_json", row)
    if row.snapshot_sha256 != _snapshot_sha256(
        priority_payload_json,
        risk_payload_json,
    ):
        raise ValueError("snapshot_sha256 must match payload_json")
    try:
        priority_report = from_jsonable(
            PaperActionGatedStrategyRecommendationQueuePriorityReport,
            priority_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"priority_payload_json is not a valid priority report: {exc}",
        ) from exc
    try:
        risk_report = from_jsonable(
            PaperActionGatedStrategyRecommendationQueueRiskReport,
            risk_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"risk_payload_json is not a valid risk report: {exc}") from exc

    if type(priority_report) is not PaperActionGatedStrategyRecommendationQueuePriorityReport:
        raise ValueError("priority_payload_json must recover a priority report")
    if type(risk_report) is not PaperActionGatedStrategyRecommendationQueueRiskReport:
        raise ValueError("risk_payload_json must recover a risk report")
    _validate_hard_flags_tree(priority_report, "priority_report")
    _validate_hard_flags_tree(risk_report, "risk_report")
    _validate_unique_risk_reason_codes(risk_report.reason_codes)
    _validate_priority_and_risk_snapshot_consistency(priority_report, risk_report)
    _validate_row_matches_payload(row, priority_report, risk_report)
    return priority_report, risk_report


def _validate_row_shape(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
) -> None:
    _require_sha256("snapshot_sha256", row.snapshot_sha256)
    _as_utc("generated_at", row.generated_at)
    for field_name in (
        "priority_source_report_count",
        "priority_research_ready_count",
        "priority_watch_count",
        "priority_blocked_count",
        "risk_source_queue_count",
        "risk_candidate_count",
        "risk_ready_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    for field_name in (
        "priority_total_ready_notional",
        "top_research_priority_score",
        "average_research_priority_score",
        "risk_total_ready_notional",
        "risk_largest_queue_ready_notional",
    ):
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    _require_canonical_string("risk_config_version", row.risk_config_version)
    _require_risk_status("risk_status", row.risk_status)
    _require_risk_next_step("risk_recommended_next_step", row.risk_recommended_next_step)
    if row.risk_recommended_next_step != RISK_NEXT_STEP_BY_STATUS[row.risk_status]:
        raise ValueError("risk_recommended_next_step must match risk_status")
    _normalize_risk_reason_codes_json(
        "risk_reason_codes_json",
        row.risk_reason_codes_json,
    )
    _require_hard_flags("DB row", row)


def _require_payload_flags_match_row(
    payload_json: dict[str, Any],
    field_name: str,
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if flag_name not in payload_json:
            raise ValueError(f"{field_name} {flag_name} must match DB row")
        if payload_json[flag_name] is not getattr(row, flag_name):
            raise ValueError(f"{field_name} {flag_name} must match DB row")


def _validate_priority_and_risk_snapshot_consistency(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> None:
    _require_matching_value(
        "priority_report.generated_at",
        _as_utc("priority_report.generated_at", priority_report.generated_at),
        "risk_report.generated_at",
        _as_utc("risk_report.generated_at", risk_report.generated_at),
    )
    _require_matching_value(
        "priority_report.source_report_count",
        priority_report.source_report_count,
        "risk_report.source_queue_count",
        risk_report.source_queue_count,
    )
    _require_matching_value(
        "priority_rows.config_version",
        _priority_source_config_versions(priority_report),
        "risk_report.source_config_versions",
        _risk_source_config_versions(risk_report),
    )
    _require_matching_value(
        "priority_report.research_ready_count",
        priority_report.research_ready_count,
        "risk_report.research_ready_source_count",
        risk_report.research_ready_source_count,
    )
    _require_matching_value(
        "priority_report.watch_count",
        priority_report.watch_count,
        "risk_report.watch_source_count",
        risk_report.watch_source_count,
    )
    _require_matching_value(
        "priority_report.blocked_count",
        priority_report.blocked_count,
        "risk_report.blocked_source_count",
        risk_report.blocked_source_count,
    )
    _require_matching_value(
        "priority_report.total_ready_notional",
        priority_report.total_ready_notional,
        "risk_report.total_ready_notional",
        risk_report.total_ready_notional,
    )
    _require_matching_value(
        "sum(priority_rows.candidate_count)",
        _priority_row_sum(priority_report, "candidate_count"),
        "risk_report.candidate_count",
        risk_report.candidate_count,
    )
    _require_matching_value(
        "sum(priority_rows.ready_count)",
        _priority_row_sum(priority_report, "ready_count"),
        "risk_report.ready_count",
        risk_report.ready_count,
    )
    _require_matching_value(
        "sum(priority_rows.watch_count)",
        _priority_row_sum(priority_report, "watch_count"),
        "risk_report.watch_count",
        risk_report.watch_count,
    )
    _require_matching_value(
        "sum(priority_rows.blocked_count)",
        _priority_row_sum(priority_report, "blocked_count"),
        "risk_report.blocked_count",
        risk_report.blocked_count,
    )


def _priority_source_config_versions(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> tuple[str, ...]:
    return tuple(sorted({row.config_version for row in priority_report.priority_rows}))


def _risk_source_config_versions(
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> tuple[str, ...]:
    return tuple(sorted(risk_report.source_config_versions))


def _priority_row_sum(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    field_name: str,
) -> int:
    return sum(getattr(row, field_name) for row in priority_report.priority_rows)


def _require_matching_value(
    left_field_name: str,
    left_value: object,
    right_field_name: str,
    right_value: object,
) -> None:
    if left_value != right_value:
        raise ValueError(f"{left_field_name} must match {right_field_name}")


def _validate_row_matches_payload(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> None:
    expected_values = {
        "snapshot_sha256": _snapshot_sha256(
            _json_ready(asdict(priority_report)),
            _json_ready(asdict(risk_report)),
        ),
        "generated_at": priority_report.generated_at,
        "priority_source_report_count": priority_report.source_report_count,
        "priority_research_ready_count": priority_report.research_ready_count,
        "priority_watch_count": priority_report.watch_count,
        "priority_blocked_count": priority_report.blocked_count,
        "priority_total_ready_notional": priority_report.total_ready_notional,
        "top_research_priority_score": priority_report.top_research_priority_score,
        "average_research_priority_score": priority_report.average_research_priority_score,
        "risk_config_version": risk_report.config_version,
        "risk_status": risk_report.status,
        "risk_recommended_next_step": risk_report.recommended_next_step,
        "risk_source_queue_count": risk_report.source_queue_count,
        "risk_candidate_count": risk_report.candidate_count,
        "risk_ready_count": risk_report.ready_count,
        "risk_total_ready_notional": risk_report.total_ready_notional,
        "risk_largest_queue_ready_notional": risk_report.largest_queue_ready_notional,
        "risk_reason_codes_json": risk_report.reason_codes,
        "paper_only": priority_report.paper_only,
        "report_only": priority_report.report_only,
        "readonly": priority_report.readonly,
    }
    for field_name, expected_value in expected_values.items():
        if not _json_equal_strict(
            _json_ready(getattr(row, field_name)),
            _json_ready(expected_value),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _snapshot_sha256(
    priority_payload_json: dict[str, Any],
    risk_payload_json: dict[str, Any],
) -> str:
    encoded = json.dumps(
        {
            "priority_payload_json": priority_payload_json,
            "risk_payload_json": risk_payload_json,
        },
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
        return format(value.quantize(Decimal("0.000001")), "f")
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
    raise ValueError("decision-support row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
        _reject_json_decimals(value)
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_risk_reason_codes_json(field_name: str, value: object) -> list[str]:
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc

    if isinstance(value, dict):
        for item in value.values():
            if item is not True and not (type(item) is int and item > 0):
                raise ValueError(f"{field_name} object values must be true or positive ints")
        return _normalize_risk_reason_code_sequence(field_name, value.keys())
    if isinstance(value, (list, tuple)):
        return _normalize_risk_reason_code_sequence(field_name, value)
    raise ValueError(f"{field_name} must be a JSON list or object")


def _normalize_risk_reason_code_sequence(
    field_name: str,
    value: object,
) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be iterable") from exc
    _validate_unique_risk_reason_codes(reason_codes, field_name)
    return list(reason_codes)


def _validate_unique_risk_reason_codes(
    reason_codes: object,
    field_name: str = "risk_reason_codes_json",
) -> None:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        items = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for item in items:
        if type(item) is not str or item not in RISK_REASON_CODES:
            raise ValueError(f"{field_name} must contain known risk reason codes")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(item)


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


def _validate_json_hard_flags(
    value: Any,
    field_name: str,
    *,
    require_hard_flags: bool = False,
) -> None:
    if not isinstance(value, dict):
        return
    if require_hard_flags or any(
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
                require_hard_flags=require_hard_flags,
            )
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(
                    element,
                    f"{child_name} {index}",
                    require_hard_flags=require_hard_flags or key == "priority_rows",
                )


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _reject_json_decimals(value: Any) -> None:
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not be a Decimal")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not be a datetime")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_decimals(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_decimals(item)


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


def _require_risk_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_risk_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in set(RISK_NEXT_STEP_BY_STATUS.values()):
        raise ValueError(f"{field_name} must be a known risk next step")


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
