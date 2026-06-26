"""Pure row codec for persisted action-gated queue history reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history import (
    PaperActionGatedStrategyRecommendationQueueHistoryReport,
)
from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueHistoryDbRow",
    "paper_action_gated_strategy_recommendation_queue_history_report_from_db_row",
    "paper_action_gated_strategy_recommendation_queue_history_report_to_db_row",
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


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    research_ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    status_transition_count: int
    ready_notional_delta: Decimal
    latest_reason_code_counts_json: dict[str, int]
    payload_json: dict[str, object]
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
            "first_source_generated_at",
            _as_optional_utc(
                "first_source_generated_at",
                self.first_source_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "last_source_generated_at",
            _as_optional_utc("last_source_generated_at", self.last_source_generated_at),
        )
        for field_name in (
            "source_report_count",
            "research_ready_count",
            "watch_count",
            "blocked_count",
            "status_transition_count",
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
        _require_optional_action_status(
            "latest_action_status",
            self.latest_action_status,
        )
        _require_optional_queue_next_step(
            "latest_recommended_next_step",
            self.latest_recommended_next_step,
        )
        _validate_optional_next_step_pair(
            self.latest_action_status,
            self.latest_recommended_next_step,
        )
        object.__setattr__(
            self,
            "ready_notional_delta",
            _require_decimal("ready_notional_delta", self.ready_notional_delta),
        )
        object.__setattr__(
            self,
            "latest_reason_code_counts_json",
            _normalize_reason_code_counts_json(
                "latest_reason_code_counts_json",
                self.latest_reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_payload_json_contract(self)
        _validate_history_row(self)
        _validate_payload_recovers_to_canonical_report(self.payload_json)
        _require_hard_flags("DB row", self)


def paper_action_gated_strategy_recommendation_queue_history_report_to_db_row(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> PaperActionGatedStrategyRecommendationQueueHistoryDbRow:
    if type(report) is not PaperActionGatedStrategyRecommendationQueueHistoryReport:
        raise ValueError(
            "report must be a "
            "PaperActionGatedStrategyRecommendationQueueHistoryReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperActionGatedStrategyRecommendationQueueHistoryDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        source_report_count=report.source_report_count,
        first_source_generated_at=report.first_source_generated_at,
        last_source_generated_at=report.last_source_generated_at,
        research_ready_count=report.research_ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        total_ready_notional=report.total_ready_notional,
        latest_action_status=report.latest_action_status,
        latest_recommended_next_step=report.latest_recommended_next_step,
        status_transition_count=report.status_transition_count,
        ready_notional_delta=report.ready_notional_delta,
        latest_reason_code_counts_json={
            item.reason_code: item.count for item in report.latest_reason_code_counts
        },
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_action_gated_strategy_recommendation_queue_history_report_from_db_row(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
) -> PaperActionGatedStrategyRecommendationQueueHistoryReport:
    if type(row) is not PaperActionGatedStrategyRecommendationQueueHistoryDbRow:
        raise ValueError(
            "row must be a PaperActionGatedStrategyRecommendationQueueHistoryDbRow",
        )
    _reject_json_floats(row.payload_json)
    _validate_payload_json_contract(row)
    _validate_payload_recovers_to_canonical_report(row.payload_json)
    try:
        report = from_jsonable(
            PaperActionGatedStrategyRecommendationQueueHistoryReport,
            row.payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid action-gated queue history report: "
            f"{exc}",
        ) from exc
    if type(report) is not PaperActionGatedStrategyRecommendationQueueHistoryReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperActionGatedStrategyRecommendationQueueHistoryReport",
        )
    _validate_report_tree(report)
    expected_row = (
        paper_action_gated_strategy_recommendation_queue_history_report_to_db_row(
            report,
        )
    )
    _validate_row_matches_payload(row, expected_row)
    return report


def _validate_report_tree(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    _validate_hard_flags_tree(report, "report")
    _validate_unique_latest_reason_code_counts(report)


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


def _validate_unique_latest_reason_code_counts(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    seen: set[str] = set()
    for item in report.latest_reason_code_counts:
        if item.reason_code in seen:
            raise ValueError(
                "latest_reason_code_counts must not contain duplicate reason codes",
            )
        seen.add(item.reason_code)


def _validate_row_matches_payload(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
    expected: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "source_report_count",
        "first_source_generated_at",
        "last_source_generated_at",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "total_ready_notional",
        "latest_action_status",
        "latest_recommended_next_step",
        "status_transition_count",
        "ready_notional_delta",
        "latest_reason_code_counts_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if not _json_values_match(
            _json_ready(getattr(row, field_name)),
            _json_ready(getattr(expected, field_name)),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_history_row(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
) -> None:
    if (
        row.research_ready_count + row.watch_count + row.blocked_count
        != row.source_report_count
    ):
        raise ValueError("action status counts must match source_report_count")
    if row.source_report_count == 0:
        _validate_empty_history_row(row)
        return
    _validate_nonempty_history_row(row)


def _validate_empty_history_row(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
) -> None:
    if row.first_source_generated_at is not None:
        raise ValueError("first_source_generated_at must be None for empty history")
    if row.last_source_generated_at is not None:
        raise ValueError("last_source_generated_at must be None for empty history")
    if row.latest_action_status is not None:
        raise ValueError("latest_action_status must be None for empty history")
    if row.latest_recommended_next_step is not None:
        raise ValueError(
            "latest_recommended_next_step must be None for empty history",
        )
    if row.status_transition_count != 0:
        raise ValueError("status_transition_count must be zero for empty history")
    if row.total_ready_notional != Decimal("0.000000"):
        raise ValueError("total_ready_notional must be zero for empty history")
    if row.ready_notional_delta != Decimal("0.000000"):
        raise ValueError("ready_notional_delta must be zero for empty history")
    if row.latest_reason_code_counts_json:
        raise ValueError(
            "latest_reason_code_counts_json must be empty for empty history",
        )


def _validate_nonempty_history_row(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
) -> None:
    if row.first_source_generated_at is None:
        raise ValueError("first_source_generated_at is required")
    if row.last_source_generated_at is None:
        raise ValueError("last_source_generated_at is required")
    if row.last_source_generated_at < row.first_source_generated_at:
        raise ValueError("last_source_generated_at must not precede first_source_generated_at")
    if row.latest_action_status is None:
        raise ValueError("latest_action_status is required")
    if row.latest_recommended_next_step is None:
        raise ValueError("latest_recommended_next_step is required")
    if row.status_transition_count >= row.source_report_count:
        raise ValueError("status_transition_count must be below source_report_count")


def _validate_payload_json_contract(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
) -> None:
    _validate_json_hard_flags(row.payload_json, "payload_json")
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    for field_name in (
        "generated_at",
        "source_report_count",
        "first_source_generated_at",
        "last_source_generated_at",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "total_ready_notional",
        "latest_action_status",
        "latest_recommended_next_step",
        "status_transition_count",
        "ready_notional_delta",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _validate_payload_field_matches_row(row, field_name)
    if not _json_values_match(
        _normalize_payload_reason_code_counts(
            "payload_json latest_reason_code_counts",
            row.payload_json.get("latest_reason_code_counts"),
        ),
        row.latest_reason_code_counts_json,
    ):
        raise ValueError("latest_reason_code_counts_json must match payload_json")


def _validate_payload_recovers_to_canonical_report(
    payload_json: dict[str, object],
) -> None:
    try:
        report = from_jsonable(
            PaperActionGatedStrategyRecommendationQueueHistoryReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid action-gated queue history report: "
            f"{exc}",
        ) from exc
    if type(report) is not PaperActionGatedStrategyRecommendationQueueHistoryReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperActionGatedStrategyRecommendationQueueHistoryReport",
        )
    _validate_report_tree(report)
    if payload_json != _json_ready(asdict(report)):
        raise ValueError("payload_json must match canonical recovered report payload")


def _validate_payload_field_matches_row(
    row: PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
    field_name: str,
) -> None:
    if not _json_values_match(
        row.payload_json.get(field_name),
        _json_ready(getattr(row, field_name)),
    ):
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


def _report_sha256(payload_json: dict[str, object]) -> str:
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
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError(
        "action-gated queue history DB row values must be JSON serializable",
    )


def _normalize_json_object(field_name: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


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
    if any(
        flag_name in value for flag_name in ("paper_only", "report_only", "readonly")
    ):
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


def _require_canonical_token(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a canonical token")


def _require_optional_action_status(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_optional_queue_next_step(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in QUEUE_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known recommended next step")


def _validate_optional_next_step_pair(
    latest_action_status: str | None,
    latest_recommended_next_step: str | None,
) -> None:
    if latest_action_status is None:
        if latest_recommended_next_step is not None:
            raise ValueError(
                "latest_recommended_next_step requires latest_action_status",
            )
        return
    if latest_recommended_next_step is None:
        raise ValueError("latest_recommended_next_step is required")
    if (
        latest_recommended_next_step
        != NEXT_STEP_BY_ACTION_STATUS[latest_action_status]
    ):
        raise ValueError("latest_recommended_next_step must match latest_action_status")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
