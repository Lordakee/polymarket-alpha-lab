"""Pure row codec for persisted action-gated strategy queue reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
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
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(
            PaperActionGatedStrategyRecommendationQueueReport,
            row.payload_json,
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
    expected_row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        report,
    )
    _validate_row_matches_payload(row, expected_row)
    return report


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
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "source_config_version",
        "action_status",
        "recommended_next_step",
        "candidate_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "total_ready_notional",
        "reason_code_counts_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


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
