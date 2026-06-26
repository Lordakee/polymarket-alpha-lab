"""Pure row codec for persisted strategy candidate research queue reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
)


__all__ = (
    "PaperStrategyCandidateResearchQueueDbRow",
    "paper_strategy_candidate_research_queue_report_from_db_row",
    "paper_strategy_candidate_research_queue_report_to_db_row",
)


ACTION_STATUSES = ("research_ready", "watch", "blocked")
RESEARCH_STATUSES = ("ready", "watch", "blocked")
QUEUE_NEXT_STEPS = (
    "review_candidate_research_queue",
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
RESEARCH_QUEUE_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "research_rank",
        "queue_rank",
        "market_slug",
        "question",
        "selected_side",
        "scoring_side",
        "source_action",
        "decision",
        "queue_status",
        "research_status",
        "research_bucket",
        "assessment_status",
        "source_status",
        "readiness_status",
        "recommendation_score",
        "readiness_score",
        "screening_score",
        "net_edge_per_share",
        "total_cost_per_share",
        "confidence",
        "spread",
        "resolution_risk",
        "suggested_notional",
        "selected_position_notional",
        "primary_reason_code",
        "research_priority_score",
        "evidence_gap_codes",
        "reason_codes",
        "explanation",
    ),
)
RESEARCH_QUEUE_ROW_PAYLOAD_ALL_FIELDS = RESEARCH_QUEUE_ROW_PAYLOAD_FIELDS | frozenset(
    HARD_FLAG_NAMES,
)
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "source_config_version",
        "action_status",
        "recommended_next_step",
        "source_reason_code_counts",
        "research_status",
        "candidate_count",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "selected_count",
        "skipped_count",
        "not_selected_count",
        "total_ready_notional",
        "total_selected_notional",
        "total_suggested_notional",
        "top_research_priority_score",
        "average_research_ready_score",
        "primary_reason_code_counts",
        "rows",
        "reason_codes",
        *HARD_FLAG_NAMES,
    ),
)
NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperStrategyCandidateResearchQueueDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    research_status: str
    candidate_count: int
    research_ready_count: int
    watch_count: int
    blocked_count: int
    selected_count: int
    skipped_count: int
    not_selected_count: int
    total_ready_notional: Decimal
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    top_research_priority_score: Decimal
    average_research_ready_score: Decimal
    source_reason_code_counts_json: dict[str, int]
    primary_reason_code_counts_json: dict[str, int]
    reason_codes_json: list[str]
    rows_json: list[dict[str, Any]]
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
        _require_research_status("research_status", self.research_status)
        for field_name in (
            "candidate_count",
            "research_ready_count",
            "watch_count",
            "blocked_count",
            "selected_count",
            "skipped_count",
            "not_selected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_ready_notional",
            "total_selected_notional",
            "total_suggested_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "top_research_priority_score",
            "average_research_ready_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_reason_code_counts_json",
            _normalize_count_json_object(
                "source_reason_code_counts_json",
                self.source_reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "primary_reason_code_counts_json",
            _normalize_count_json_object(
                "primary_reason_code_counts_json",
                self.primary_reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "rows_json",
            _normalize_rows_json("rows_json", self.rows_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_payload_rows_hard_flags(self.payload_json)
        _validate_payload_schema(self.payload_json)
        _validate_payload_duplicate_shapes(self.payload_json)
        _validate_materialized_fields_match_payload(self)
        _validate_canonical_recovered_payload(self.payload_json)


def paper_strategy_candidate_research_queue_report_to_db_row(
    report: PaperStrategyCandidateResearchQueueReport,
) -> PaperStrategyCandidateResearchQueueDbRow:
    if type(report) is not PaperStrategyCandidateResearchQueueReport:
        raise ValueError("report must be a PaperStrategyCandidateResearchQueueReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperStrategyCandidateResearchQueueDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        action_status=report.action_status,
        recommended_next_step=report.recommended_next_step,
        research_status=report.research_status,
        candidate_count=report.candidate_count,
        research_ready_count=report.research_ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        selected_count=report.selected_count,
        skipped_count=report.skipped_count,
        not_selected_count=report.not_selected_count,
        total_ready_notional=report.total_ready_notional,
        total_selected_notional=report.total_selected_notional,
        total_suggested_notional=report.total_suggested_notional,
        top_research_priority_score=report.top_research_priority_score,
        average_research_ready_score=report.average_research_ready_score,
        source_reason_code_counts_json={
            item.reason_code: item.count for item in report.source_reason_code_counts
        },
        primary_reason_code_counts_json={
            reason_code: count
            for reason_code, count in report.primary_reason_code_counts
        },
        reason_codes_json=list(report.reason_codes),
        rows_json=list(payload_json.get("rows", [])),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_strategy_candidate_research_queue_report_from_db_row(
    row: PaperStrategyCandidateResearchQueueDbRow,
) -> PaperStrategyCandidateResearchQueueReport:
    if type(row) is not PaperStrategyCandidateResearchQueueDbRow:
        raise ValueError("row must be a PaperStrategyCandidateResearchQueueDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_payload_rows_hard_flags(row.payload_json)
    _validate_payload_schema(row.payload_json)
    _validate_payload_duplicate_shapes(row.payload_json)
    _validate_materialized_fields_match_payload(row)
    report = _validate_canonical_recovered_payload(row.payload_json)
    expected_row = paper_strategy_candidate_research_queue_report_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def _validate_report_tree(report: PaperStrategyCandidateResearchQueueReport) -> None:
    _validate_hard_flags_tree(report, "report")
    _validate_unique_primary_reason_code_counts(report)
    _validate_unique_source_reason_code_counts(report)
    _validate_unique_reason_codes("reason_codes", report.reason_codes)
    for index, row in enumerate(report.rows):
        _validate_unique_reason_codes(f"rows.{index}.reason_codes", row.reason_codes)
        _validate_unique_reason_codes(
            f"rows.{index}.evidence_gap_codes",
            row.evidence_gap_codes,
        )


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


def _validate_unique_primary_reason_code_counts(
    report: PaperStrategyCandidateResearchQueueReport,
) -> None:
    seen: set[str] = set()
    for item in report.primary_reason_code_counts:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("primary_reason_code_counts must contain tuple rows")
        reason_code, count = item
        _require_canonical_string("primary_reason_code_counts reason_code", reason_code)
        if type(count) is not int or count <= 0:
            raise ValueError("primary_reason_code_counts count must be a positive int")
        if reason_code in seen:
            raise ValueError("primary_reason_code_counts must not contain duplicates")
        seen.add(reason_code)


def _validate_unique_source_reason_code_counts(
    report: PaperStrategyCandidateResearchQueueReport,
) -> None:
    seen: set[str] = set()
    for item in report.source_reason_code_counts:
        if type(item) is not PaperRecommendationCycleActionGateReasonCodeCount:
            raise ValueError(
                "source_reason_code_counts must contain "
                "PaperRecommendationCycleActionGateReasonCodeCount values",
            )
        if item.reason_code in seen:
            raise ValueError("source_reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)


def _validate_unique_reason_codes(field_name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)


def _validate_row_matches_payload(
    row: PaperStrategyCandidateResearchQueueDbRow,
    expected: PaperStrategyCandidateResearchQueueDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "source_config_version",
        "action_status",
        "recommended_next_step",
        "research_status",
        "candidate_count",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "selected_count",
        "skipped_count",
        "not_selected_count",
        "total_ready_notional",
        "total_selected_notional",
        "total_suggested_notional",
        "top_research_priority_score",
        "average_research_ready_score",
        "source_reason_code_counts_json",
        "primary_reason_code_counts_json",
        "reason_codes_json",
        "rows_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if not _strict_equal(getattr(row, field_name), getattr(expected, field_name)):
            raise ValueError(f"{field_name} must match payload_json")
    if not _strict_equal(row.payload_json, expected.payload_json):
        raise ValueError("payload_json must match recovered canonical payload")


def _validate_materialized_fields_match_payload(
    row: PaperStrategyCandidateResearchQueueDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at"),
        "config_version": payload_json.get("config_version"),
        "source_config_version": payload_json.get("source_config_version"),
        "action_status": payload_json.get("action_status"),
        "recommended_next_step": payload_json.get("recommended_next_step"),
        "research_status": payload_json.get("research_status"),
        "candidate_count": payload_json.get("candidate_count"),
        "research_ready_count": payload_json.get("research_ready_count"),
        "watch_count": payload_json.get("watch_count"),
        "blocked_count": payload_json.get("blocked_count"),
        "selected_count": payload_json.get("selected_count"),
        "skipped_count": payload_json.get("skipped_count"),
        "not_selected_count": payload_json.get("not_selected_count"),
        "total_ready_notional": payload_json.get("total_ready_notional"),
        "total_selected_notional": payload_json.get("total_selected_notional"),
        "total_suggested_notional": payload_json.get("total_suggested_notional"),
        "top_research_priority_score": payload_json.get("top_research_priority_score"),
        "average_research_ready_score": payload_json.get(
            "average_research_ready_score",
        ),
        "source_reason_code_counts_json": _source_reason_code_counts_from_payload(
            payload_json,
        ),
        "primary_reason_code_counts_json": _primary_reason_code_counts_from_payload(
            payload_json,
        ),
        "reason_codes_json": payload_json.get("reason_codes"),
        "rows_json": payload_json.get("rows"),
        "paper_only": payload_json.get("paper_only"),
        "report_only": payload_json.get("report_only"),
        "readonly": payload_json.get("readonly"),
    }
    try:
        actual_values = {
            "report_sha256": row.report_sha256,
            "generated_at": row.generated_at.isoformat(),
            "config_version": row.config_version,
            "source_config_version": row.source_config_version,
            "action_status": row.action_status,
            "recommended_next_step": row.recommended_next_step,
            "research_status": row.research_status,
            "candidate_count": row.candidate_count,
            "research_ready_count": row.research_ready_count,
            "watch_count": row.watch_count,
            "blocked_count": row.blocked_count,
            "selected_count": row.selected_count,
            "skipped_count": row.skipped_count,
            "not_selected_count": row.not_selected_count,
            "total_ready_notional": _json_ready(row.total_ready_notional),
            "total_selected_notional": _json_ready(row.total_selected_notional),
            "total_suggested_notional": _json_ready(row.total_suggested_notional),
            "top_research_priority_score": _json_ready(row.top_research_priority_score),
            "average_research_ready_score": _json_ready(
                row.average_research_ready_score,
            ),
            "source_reason_code_counts_json": row.source_reason_code_counts_json,
            "primary_reason_code_counts_json": row.primary_reason_code_counts_json,
            "reason_codes_json": row.reason_codes_json,
            "rows_json": row.rows_json,
            "paper_only": row.paper_only,
            "report_only": row.report_only,
            "readonly": row.readonly,
        }
    except (AttributeError, ValueError) as exc:
        raise ValueError("materialized fields must match payload_json") from exc
    for field_name, actual_value in actual_values.items():
        if not _strict_equal(actual_value, expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _source_reason_code_counts_from_payload(
    payload_json: dict[str, Any],
) -> dict[str, int] | None:
    source_reason_code_counts = payload_json.get("source_reason_code_counts")
    if not isinstance(source_reason_code_counts, list):
        return None
    counts: dict[str, int] = {}
    for item in source_reason_code_counts:
        if not isinstance(item, dict):
            return None
        reason_code = item.get("reason_code")
        count = item.get("count")
        if not isinstance(reason_code, str) or type(count) is not int:
            return None
        counts[reason_code] = count
    return counts


def _primary_reason_code_counts_from_payload(
    payload_json: dict[str, Any],
) -> dict[str, int] | None:
    primary_reason_code_counts = payload_json.get("primary_reason_code_counts")
    if not isinstance(primary_reason_code_counts, list):
        return None
    counts: dict[str, int] = {}
    for item in primary_reason_code_counts:
        if not isinstance(item, list) or len(item) != 2:
            return None
        reason_code, count = item
        if not isinstance(reason_code, str) or type(count) is not int:
            return None
        counts[reason_code] = count
    return counts


def _validate_canonical_recovered_payload(
    payload_json: dict[str, Any],
) -> PaperStrategyCandidateResearchQueueReport:
    payload_for_recovery = _payload_for_recovery(payload_json)
    try:
        report = from_jsonable(
            PaperStrategyCandidateResearchQueueReport,
            payload_for_recovery,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid strategy candidate research queue report: {exc}",
        ) from exc
    if type(report) is not PaperStrategyCandidateResearchQueueReport:
        raise ValueError(
            "payload_json must recover a PaperStrategyCandidateResearchQueueReport",
        )
    _validate_report_tree(report)
    canonical_payload = _json_ready(asdict(report))
    if not _strict_equal(payload_json, canonical_payload):
        raise ValueError("payload_json must match recovered canonical payload")
    return report


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_for_recovery(payload_json: dict[str, Any]) -> dict[str, Any]:
    payload = _json_ready(payload_json)
    if "source_reason_code_counts" in payload:
        value = payload["source_reason_code_counts"]
        if type(value) is not list:
            raise ValueError("source_reason_code_counts must be a JSON array")
        payload["source_reason_code_counts"] = [
            _source_reason_count_from_json(item) for item in value
        ]
    return payload


def _source_reason_count_from_json(
    value: object,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    reason_code, count = _source_reason_count_values_from_json(value)
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _source_reason_count_values_from_json(value: object) -> tuple[str, int]:
    if type(value) is not dict:
        raise ValueError("source_reason_code_counts rows must be JSON objects")
    if set(value) != {"reason_code", "count"}:
        raise ValueError("source_reason_code_counts rows must contain reason_code/count")
    reason_code = value["reason_code"]
    count = value["count"]
    _require_canonical_token("source_reason_code_counts reason_code", reason_code)
    if type(count) is not int or count <= 0:
        raise ValueError("source_reason_code_counts count must be a positive int")
    return reason_code, count


def _validate_payload_duplicate_shapes(
    value: Any,
    field_name: str = "payload_json",
) -> None:
    if isinstance(value, dict):
        if "primary_reason_code_counts" in value:
            _validate_payload_primary_reason_counts(
                value["primary_reason_code_counts"],
            )
        if "source_reason_code_counts" in value:
            _validate_payload_source_reason_counts(value["source_reason_code_counts"])
        if "reason_codes" in value:
            _validate_payload_reason_codes(f"{field_name} reason_codes", value["reason_codes"])
        if "evidence_gap_codes" in value:
            _validate_payload_reason_codes(
                f"{field_name} evidence_gap_codes",
                value["evidence_gap_codes"],
            )
        for key, item in value.items():
            _validate_payload_duplicate_shapes(item, f"{field_name} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_duplicate_shapes(item, f"{field_name} {index}")


def _validate_payload_primary_reason_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("primary_reason_code_counts must be a JSON array")
    seen: set[str] = set()
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("primary_reason_code_counts rows must be JSON arrays")
        reason_code, count = item
        _require_canonical_string("primary_reason_code_counts reason_code", reason_code)
        if type(count) is not int or count <= 0:
            raise ValueError("primary_reason_code_counts count must be a positive int")
        if reason_code in seen:
            raise ValueError("primary_reason_code_counts must not contain duplicates")
        seen.add(reason_code)


def _validate_payload_source_reason_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("source_reason_code_counts must be a JSON array")
    seen: set[str] = set()
    for item in value:
        reason_code, _ = _source_reason_count_values_from_json(item)
        if reason_code in seen:
            raise ValueError("source_reason_code_counts must not contain duplicates")
        seen.add(reason_code)


def _validate_payload_reason_codes(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)


def _validate_payload_schema(payload_json: dict[str, Any]) -> None:
    if set(payload_json) != REPORT_PAYLOAD_FIELDS:
        raise ValueError("payload_json must contain the canonical report fields")
    _validate_payload_decimal_strings(payload_json)
    rows = payload_json.get("rows")
    if type(rows) is not list:
        raise ValueError("payload_json rows must be a JSON array")
    for index, item in enumerate(rows):
        if type(item) is not dict:
            raise ValueError(f"payload_json rows {index} must be a JSON object")
        if set(item) != RESEARCH_QUEUE_ROW_PAYLOAD_ALL_FIELDS:
            missing = sorted(RESEARCH_QUEUE_ROW_PAYLOAD_ALL_FIELDS - set(item))
            if missing:
                raise ValueError(f"payload_json rows {index} {missing[0]} is required")
            extra = sorted(set(item) - RESEARCH_QUEUE_ROW_PAYLOAD_ALL_FIELDS)
            raise ValueError(f"payload_json rows {index} {extra[0]} is not allowed")
        _validate_payload_decimal_strings(item, f"payload_json rows {index}")


def _validate_payload_decimal_strings(
    value: dict[str, Any],
    field_name: str = "payload_json",
) -> None:
    for key, item in value.items():
        if key in _DECIMAL_PAYLOAD_KEYS and item is not None and type(item) is not str:
            raise ValueError(f"{field_name} {key} must be a canonical decimal string")


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
    raise ValueError("strategy candidate research queue DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
        _reject_json_decimals(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must contain stored JSON values: {exc}") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _normalize_count_json_object(field_name: str, value: object) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    for key, item in normalized.items():
        _require_canonical_token(f"{field_name} key", key)
        if type(item) is not int or item <= 0:
            raise ValueError(f"{field_name} {key} must be a positive int")
    return normalized


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
    return normalized


def _normalize_rows_json(field_name: str, value: object) -> list[dict[str, Any]]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[dict[str, Any]] = []
    for item in value:
        normalized.append(_normalize_json_object(f"{field_name} row", item))
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in HARD_FLAG_NAMES):
        for flag_name in HARD_FLAG_NAMES:
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _validate_payload_rows_hard_flags(payload_json: dict[str, Any]) -> None:
    _validate_research_queue_row_hard_flags(payload_json, "payload_json")


def _validate_research_queue_row_hard_flags(
    value: Any,
    field_name: str,
) -> None:
    if isinstance(value, dict):
        if _is_research_queue_row_payload(value):
            for flag_name in HARD_FLAG_NAMES:
                if value.get(flag_name) is not True:
                    raise ValueError(
                        f"{field_name} {flag_name} must be present and true",
                    )
        for key, item in value.items():
            _validate_research_queue_row_hard_flags(item, f"{field_name} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_research_queue_row_hard_flags(item, f"{field_name} {index}")


def _is_research_queue_row_payload(value: dict[str, Any]) -> bool:
    return RESEARCH_QUEUE_ROW_PAYLOAD_FIELDS.issubset(value)


_DECIMAL_PAYLOAD_KEYS = frozenset(
    (
        "total_ready_notional",
        "total_selected_notional",
        "total_suggested_notional",
        "top_research_priority_score",
        "average_research_ready_score",
        "recommendation_score",
        "readiness_score",
        "screening_score",
        "net_edge_per_share",
        "total_cost_per_share",
        "confidence",
        "spread",
        "resolution_risk",
        "suggested_notional",
        "selected_position_notional",
        "research_priority_score",
    ),
)


def _strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if set(left) != set(right):
            return False
        return all(_strict_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        if len(left) != len(right):
            return False
        return all(
            _strict_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _reject_json_decimals(value: Any, field_name: str = "JSON value") -> None:
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not be a Decimal")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_json_decimals(item, f"{field_name} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_json_decimals(item, f"{field_name} {index}")


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


def _require_research_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


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


def _require_score_decimal(field_name: str, value: object) -> Decimal:
    score = _require_nonnegative_decimal(field_name, value)
    if score > Decimal("1"):
        raise ValueError(f"{field_name} must be at most 1")
    return score


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
