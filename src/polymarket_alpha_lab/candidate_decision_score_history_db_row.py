"""Pure row codec for candidate decision score history reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.candidate_decision_score import ACTION_STATES
from polymarket_alpha_lab.candidate_decision_score_history import (
    HISTORY_STATUSES,
    CandidateDecisionScoreHistoryReport,
)
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    reject_unsafe_surface_fields,
)


__all__ = (
    "CandidateDecisionScoreHistoryDbRow",
    "candidate_decision_score_history_report_from_db_row",
    "candidate_decision_score_history_report_to_db_row",
    "from_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_TOP_LEVEL_DECIMAL_FIELDS = (
    "source_report_count",
    "report_count",
    "candidate_count",
    "action_reject_count",
    "action_watch_count",
    "action_research_more_count",
    "action_paper_recommend_count",
    "hard_blocked_count",
    "blocked_total",
    "watch_total",
    "paper_recommend_total",
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "status",
        *_TOP_LEVEL_DECIMAL_FIELDS,
        "first_source_generated_at",
        "latest_generated_at",
        "rows",
        "action_counts",
        "hard_blocker_code_counts",
        "reason_code_counts",
        "reason_counts",
        "primary_team_counts",
        *_HARD_FLAG_NAMES,
    ),
)
_PUBLIC_SUMMARY_FIELD_ORDER = (
    "generated_at",
    "status",
    *_TOP_LEVEL_DECIMAL_FIELDS,
    "first_source_generated_at",
    "latest_generated_at",
    "action_counts",
    "hard_blocker_code_counts",
    "reason_code_counts",
    "reason_counts",
    "primary_team_counts",
    *_HARD_FLAG_NAMES,
)
_PUBLIC_SUMMARY_FIELDS = frozenset(_PUBLIC_SUMMARY_FIELD_ORDER)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "source_generated_at",
        "config_version",
        "candidate_id",
        "market_id",
        "primary_team_id",
        "action",
        "decision_score",
        "hard_blocker_count",
        "hard_blocker_codes",
        "reason_codes",
        *_HARD_FLAG_NAMES,
    ),
)
_ACTION_COUNT_PAYLOAD_FIELDS = frozenset(("action", "count", *_HARD_FLAG_NAMES))
_REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    ("reason_code", "count", *_HARD_FLAG_NAMES),
)
_TEAM_COUNT_PAYLOAD_FIELDS = frozenset(("team_id", "count", *_HARD_FLAG_NAMES))


@dataclass(frozen=True)
class CandidateDecisionScoreHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    status: str
    source_report_count: Decimal
    report_count: Decimal
    first_source_generated_at: datetime | None
    latest_generated_at: datetime | None
    candidate_count: Decimal
    action_reject_count: Decimal
    action_watch_count: Decimal
    action_research_more_count: Decimal
    action_paper_recommend_count: Decimal
    hard_blocked_count: Decimal
    blocked_total: Decimal
    watch_total: Decimal
    paper_recommend_total: Decimal
    action_counts_json: list[dict[str, Any]]
    hard_blocker_code_counts_json: list[dict[str, Any]]
    reason_code_counts_json: list[dict[str, Any]]
    reason_counts_json: list[dict[str, Any]]
    primary_team_counts_json: list[dict[str, Any]]
    public_summary_json: dict[str, Any]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_member("status", self.status, HISTORY_STATUSES)
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
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        for field_name in _TOP_LEVEL_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "action_counts_json",
            "hard_blocker_code_counts_json",
            "reason_code_counts_json",
            "reason_counts_json",
            "primary_team_counts_json",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_json_object_array(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_summary_json",
            _normalize_json_object("public_summary_json", self.public_summary_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("history DB row", self)
        _validate_json_hard_flags(self.public_summary_json, "public_summary_json")
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_public_summary_schema(self.public_summary_json)
        _validate_payload_schema(self.payload_json)
        _validate_materialized_fields_match_payload(self)
        _validate_public_summary_matches_payload(self.public_summary_json, self.payload_json)
        _validate_payload_recovers_to_report(self.payload_json)


def candidate_decision_score_history_report_to_db_row(
    report: CandidateDecisionScoreHistoryReport,
) -> CandidateDecisionScoreHistoryDbRow:
    if type(report) is not CandidateDecisionScoreHistoryReport:
        raise ValueError("report must be a CandidateDecisionScoreHistoryReport")
    _validate_report_tree(report)
    payload_json = _history_report_payload(report)
    public_summary_json = _public_summary_payload(payload_json)
    return CandidateDecisionScoreHistoryDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        status=report.status,
        source_report_count=report.source_report_count,
        report_count=report.report_count,
        first_source_generated_at=report.first_source_generated_at,
        latest_generated_at=report.latest_generated_at,
        candidate_count=report.candidate_count,
        action_reject_count=report.action_reject_count,
        action_watch_count=report.action_watch_count,
        action_research_more_count=report.action_research_more_count,
        action_paper_recommend_count=report.action_paper_recommend_count,
        hard_blocked_count=report.hard_blocked_count,
        blocked_total=report.blocked_total,
        watch_total=report.watch_total,
        paper_recommend_total=report.paper_recommend_total,
        action_counts_json=payload_json["action_counts"],
        hard_blocker_code_counts_json=payload_json["hard_blocker_code_counts"],
        reason_code_counts_json=payload_json["reason_code_counts"],
        reason_counts_json=payload_json["reason_counts"],
        primary_team_counts_json=payload_json["primary_team_counts"],
        public_summary_json=public_summary_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def candidate_decision_score_history_report_from_db_row(
    row: CandidateDecisionScoreHistoryDbRow,
) -> CandidateDecisionScoreHistoryReport:
    if type(row) is not CandidateDecisionScoreHistoryDbRow:
        raise ValueError("row must be a CandidateDecisionScoreHistoryDbRow")
    validated = CandidateDecisionScoreHistoryDbRow(**_row_values(row))
    return _validate_payload_recovers_to_report(validated.payload_json)


def to_db_row(
    report: CandidateDecisionScoreHistoryReport,
) -> CandidateDecisionScoreHistoryDbRow:
    return candidate_decision_score_history_report_to_db_row(report)


def from_db_row(
    row: CandidateDecisionScoreHistoryDbRow,
) -> CandidateDecisionScoreHistoryReport:
    return candidate_decision_score_history_report_from_db_row(row)


def _row_values(row: CandidateDecisionScoreHistoryDbRow) -> dict[str, Any]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "status": row.status,
        "source_report_count": row.source_report_count,
        "report_count": row.report_count,
        "first_source_generated_at": row.first_source_generated_at,
        "latest_generated_at": row.latest_generated_at,
        "candidate_count": row.candidate_count,
        "action_reject_count": row.action_reject_count,
        "action_watch_count": row.action_watch_count,
        "action_research_more_count": row.action_research_more_count,
        "action_paper_recommend_count": row.action_paper_recommend_count,
        "hard_blocked_count": row.hard_blocked_count,
        "blocked_total": row.blocked_total,
        "watch_total": row.watch_total,
        "paper_recommend_total": row.paper_recommend_total,
        "action_counts_json": row.action_counts_json,
        "hard_blocker_code_counts_json": row.hard_blocker_code_counts_json,
        "reason_code_counts_json": row.reason_code_counts_json,
        "reason_counts_json": row.reason_counts_json,
        "primary_team_counts_json": row.primary_team_counts_json,
        "public_summary_json": row.public_summary_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _history_report_payload(report: CandidateDecisionScoreHistoryReport) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload_json must be a JSON object")
    _reject_unsafe_public_payload("payload_json", payload)
    return payload


def _public_summary_payload(payload_json: dict[str, Any]) -> dict[str, Any]:
    return {field_name: payload_json[field_name] for field_name in _PUBLIC_SUMMARY_FIELD_ORDER}


def _validate_payload_recovers_to_report(
    payload_json: dict[str, Any],
) -> CandidateDecisionScoreHistoryReport:
    try:
        report = from_jsonable(CandidateDecisionScoreHistoryReport, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid candidate decision score history report: "
            f"{exc}",
        ) from exc
    if type(report) is not CandidateDecisionScoreHistoryReport:
        raise ValueError("payload_json must recover a CandidateDecisionScoreHistoryReport")
    _validate_report_tree(report)
    expected_payload_json = _history_report_payload(report)
    _validate_json_compatible(payload_json, expected_payload_json)
    return report


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


def _has_hard_flag(value: Any) -> bool:
    return any(hasattr(value, flag_name) for flag_name in _HARD_FLAG_NAMES)


def _validate_materialized_fields_match_payload(
    row: CandidateDecisionScoreHistoryDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at"),
        "status": payload_json.get("status"),
        "source_report_count": payload_json.get("source_report_count"),
        "report_count": payload_json.get("report_count"),
        "first_source_generated_at": payload_json.get("first_source_generated_at"),
        "latest_generated_at": payload_json.get("latest_generated_at"),
        "candidate_count": payload_json.get("candidate_count"),
        "action_reject_count": payload_json.get("action_reject_count"),
        "action_watch_count": payload_json.get("action_watch_count"),
        "action_research_more_count": payload_json.get("action_research_more_count"),
        "action_paper_recommend_count": payload_json.get(
            "action_paper_recommend_count",
        ),
        "hard_blocked_count": payload_json.get("hard_blocked_count"),
        "blocked_total": payload_json.get("blocked_total"),
        "watch_total": payload_json.get("watch_total"),
        "paper_recommend_total": payload_json.get("paper_recommend_total"),
        "action_counts_json": payload_json.get("action_counts"),
        "hard_blocker_code_counts_json": payload_json.get("hard_blocker_code_counts"),
        "reason_code_counts_json": payload_json.get("reason_code_counts"),
        "reason_counts_json": payload_json.get("reason_counts"),
        "primary_team_counts_json": payload_json.get("primary_team_counts"),
        "paper_only": payload_json.get("paper_only"),
        "report_only": payload_json.get("report_only"),
        "readonly": payload_json.get("readonly"),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "status": row.status,
        "source_report_count": _decimal_json_value(row.source_report_count),
        "report_count": _decimal_json_value(row.report_count),
        "first_source_generated_at": _datetime_json_value(row.first_source_generated_at),
        "latest_generated_at": _datetime_json_value(row.latest_generated_at),
        "candidate_count": _decimal_json_value(row.candidate_count),
        "action_reject_count": _decimal_json_value(row.action_reject_count),
        "action_watch_count": _decimal_json_value(row.action_watch_count),
        "action_research_more_count": _decimal_json_value(
            row.action_research_more_count,
        ),
        "action_paper_recommend_count": _decimal_json_value(
            row.action_paper_recommend_count,
        ),
        "hard_blocked_count": _decimal_json_value(row.hard_blocked_count),
        "blocked_total": _decimal_json_value(row.blocked_total),
        "watch_total": _decimal_json_value(row.watch_total),
        "paper_recommend_total": _decimal_json_value(row.paper_recommend_total),
        "action_counts_json": row.action_counts_json,
        "hard_blocker_code_counts_json": row.hard_blocker_code_counts_json,
        "reason_code_counts_json": row.reason_code_counts_json,
        "reason_counts_json": row.reason_counts_json,
        "primary_team_counts_json": row.primary_team_counts_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if actual_value != expected_values[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_public_summary_matches_payload(
    public_summary_json: dict[str, Any],
    payload_json: dict[str, Any],
) -> None:
    expected = _public_summary_payload(payload_json)
    if public_summary_json != expected:
        raise ValueError("public_summary_json must match aggregate payload_json fields")


def _validate_payload_schema(payload_json: dict[str, Any]) -> None:
    _require_exact_keys("payload_json", payload_json, _REPORT_PAYLOAD_FIELDS)
    _validate_top_level_summary_fields("payload_json", payload_json)
    _validate_rows_payload(payload_json["rows"])
    _validate_action_counts_payload("payload_json action_counts", payload_json["action_counts"])
    for field_name in (
        "hard_blocker_code_counts",
        "reason_code_counts",
        "reason_counts",
    ):
        _validate_reason_counts_payload(
            f"payload_json {field_name}",
            payload_json[field_name],
        )
    _validate_team_counts_payload(
        "payload_json primary_team_counts",
        payload_json["primary_team_counts"],
    )


def _validate_public_summary_schema(public_summary_json: dict[str, Any]) -> None:
    _require_exact_keys("public_summary_json", public_summary_json, _PUBLIC_SUMMARY_FIELDS)
    _validate_top_level_summary_fields("public_summary_json", public_summary_json)
    _validate_action_counts_payload(
        "public_summary_json action_counts",
        public_summary_json["action_counts"],
    )
    for field_name in (
        "hard_blocker_code_counts",
        "reason_code_counts",
        "reason_counts",
    ):
        _validate_reason_counts_payload(
            f"public_summary_json {field_name}",
            public_summary_json[field_name],
        )
    _validate_team_counts_payload(
        "public_summary_json primary_team_counts",
        public_summary_json["primary_team_counts"],
    )


def _validate_top_level_summary_fields(
    field_name: str,
    value: dict[str, Any],
) -> None:
    _validate_datetime_json_string(f"{field_name} generated_at", value["generated_at"])
    _require_member(f"{field_name} status", value["status"], HISTORY_STATUSES)
    _validate_optional_datetime_json_string(
        f"{field_name} first_source_generated_at",
        value["first_source_generated_at"],
    )
    _validate_optional_datetime_json_string(
        f"{field_name} latest_generated_at",
        value["latest_generated_at"],
    )
    for decimal_field_name in _TOP_LEVEL_DECIMAL_FIELDS:
        _fixed_six_decimal_json_string(
            f"{field_name} {decimal_field_name}",
            value[decimal_field_name],
        )
    _validate_json_hard_flags(value, field_name)


def _validate_rows_payload(value: Any) -> None:
    if type(value) is not list:
        raise ValueError("payload_json rows must be a JSON array")
    for index, item in enumerate(value):
        field_name = f"payload_json rows {index}"
        if type(item) is not dict:
            raise ValueError(f"{field_name} must be a JSON object")
        _require_exact_keys(field_name, item, _ROW_PAYLOAD_FIELDS)
        _validate_datetime_json_string(
            f"{field_name} source_generated_at",
            item["source_generated_at"],
        )
        for string_field_name in (
            "config_version",
            "candidate_id",
            "market_id",
            "primary_team_id",
        ):
            _require_canonical_string(
                f"{field_name} {string_field_name}",
                item[string_field_name],
            )
        _require_member(f"{field_name} action", item["action"], ACTION_STATES)
        _normalize_score_decimal(
            f"{field_name} decision_score",
            _fixed_six_decimal_json_string(
                f"{field_name} decision_score",
                item["decision_score"],
            ),
        )
        _normalize_count_decimal(
            f"{field_name} hard_blocker_count",
            _fixed_six_decimal_json_string(
                f"{field_name} hard_blocker_count",
                item["hard_blocker_count"],
            ),
        )
        _normalize_string_json_array(
            f"{field_name} hard_blocker_codes",
            item["hard_blocker_codes"],
            allow_empty=True,
        )
        _normalize_string_json_array(
            f"{field_name} reason_codes",
            item["reason_codes"],
        )
        _validate_json_hard_flags(item, field_name)


def _validate_action_counts_payload(field_name: str, value: Any) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    for index, item in enumerate(value):
        child_name = f"{field_name} {index}"
        if type(item) is not dict:
            raise ValueError(f"{child_name} must be a JSON object")
        _require_exact_keys(child_name, item, _ACTION_COUNT_PAYLOAD_FIELDS)
        _require_member(f"{child_name} action", item["action"], ACTION_STATES)
        _normalize_count_decimal(
            f"{child_name} count",
            _fixed_six_decimal_json_string(f"{child_name} count", item["count"]),
        )
        _validate_json_hard_flags(item, child_name)


def _validate_reason_counts_payload(field_name: str, value: Any) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    for index, item in enumerate(value):
        child_name = f"{field_name} {index}"
        if type(item) is not dict:
            raise ValueError(f"{child_name} must be a JSON object")
        _require_exact_keys(child_name, item, _REASON_COUNT_PAYLOAD_FIELDS)
        _require_canonical_string(f"{child_name} reason_code", item["reason_code"])
        _normalize_count_decimal(
            f"{child_name} count",
            _fixed_six_decimal_json_string(f"{child_name} count", item["count"]),
        )
        _validate_json_hard_flags(item, child_name)


def _validate_team_counts_payload(field_name: str, value: Any) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    for index, item in enumerate(value):
        child_name = f"{field_name} {index}"
        if type(item) is not dict:
            raise ValueError(f"{child_name} must be a JSON object")
        _require_exact_keys(child_name, item, _TEAM_COUNT_PAYLOAD_FIELDS)
        _require_canonical_string(f"{child_name} team_id", item["team_id"])
        _normalize_count_decimal(
            f"{child_name} count",
            _fixed_six_decimal_json_string(f"{child_name} count", item["count"]),
        )
        _validate_json_hard_flags(item, child_name)


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_value(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if type(normalized) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        normalized = _copy_json_value(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if type(normalized) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    for item in normalized:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain JSON objects")
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _copy_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal values")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain datetime values")
    if type(value) in (str, int, bool):
        return value
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    raise ValueError("JSON value must be an object, array, string, int, bool, or null")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return _decimal_json_value(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if type(value) in (str, int, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("history row value is not JSON serializable")


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


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    reject_unsafe_surface_fields(field_name, value)
    _reject_unsafe_public_values(field_name, value)


def _reject_unsafe_public_values(field_name: str, value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public payload value in {field_name}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_values(f"{field_name} {key}", item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_values(f"{field_name} {index}", item)


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _decimal_json_value(value: Decimal) -> str:
    return _fixed_six_decimal_string("Decimal value", value)


def _fixed_six_decimal_json_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    decimal_string = _fixed_six_decimal_string(field_name, decimal_value)
    if value != decimal_string:
        raise ValueError(f"{field_name} must be a fixed six-place Decimal string")
    return decimal_value


def _fixed_six_decimal_string(field_name: str, value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext() as context:
            integer_digits = max(value.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            quantized = value.quantize(_DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must not exceed six decimal places") from exc
    if quantized != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    if quantized.is_zero():
        quantized = _ZERO
    return format(quantized, "f")


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    decimal_string = _fixed_six_decimal_string(field_name, value)
    normalized = Decimal(decimal_string)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_DECIMAL_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_score_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    decimal_string = _fixed_six_decimal_string(field_name, value)
    normalized = Decimal(decimal_string)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_string_json_array(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> list[str]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(f"{field_name} item", item)
        if item not in normalized:
            normalized.append(item)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _validate_datetime_json_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    _as_utc(field_name, parsed)
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")


def _validate_optional_datetime_json_string(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_datetime_json_string(field_name, value)


def _datetime_json_value(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
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


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_exact_keys(
    field_name: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = set(value)
    if actual_keys == expected_keys:
        return
    missing = sorted(expected_keys - actual_keys)
    if missing:
        raise ValueError(f"{field_name} {missing[0]} is required")
    extra = sorted(actual_keys - expected_keys)
    raise ValueError(f"{field_name} {extra[0]} is not allowed")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
