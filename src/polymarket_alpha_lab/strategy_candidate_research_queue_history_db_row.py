"""Pure row codec for persisted strategy candidate research queue history reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.strategy_candidate_research_queue_history import (
    PaperStrategyCandidateResearchQueueHistoryReport,
)


__all__ = (
    "PaperStrategyCandidateResearchQueueHistoryDbRow",
    "paper_strategy_candidate_research_queue_history_report_from_db_row",
    "paper_strategy_candidate_research_queue_history_report_to_db_row",
)


ACTION_STATUSES = ("research_ready", "watch", "blocked")
RESEARCH_STATUSES = ("ready", "watch", "blocked")
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
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_TOP_LEVEL_DECIMAL_PAYLOAD_FIELDS = (
    "total_ready_notional",
    "total_selected_notional",
    "total_suggested_notional",
    "latest_top_research_priority_score",
    "latest_average_research_ready_score",
    "ready_notional_delta",
    "selected_notional_delta",
)


@dataclass(frozen=True)
class PaperStrategyCandidateResearchQueueHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    action_status_research_ready_count: int
    action_status_watch_count: int
    action_status_blocked_count: int
    research_status_ready_count: int
    research_status_watch_count: int
    research_status_blocked_count: int
    total_ready_notional: Decimal
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    latest_research_status: str | None
    latest_top_research_priority_score: Decimal | None
    latest_average_research_ready_score: Decimal | None
    status_transition_count: int
    ready_notional_delta: Decimal
    selected_notional_delta: Decimal
    latest_selected_count: int
    latest_skipped_count: int
    latest_not_selected_count: int
    latest_primary_reason_code_counts_json: dict[str, int]
    latest_reason_codes_json: list[str]
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
            "action_status_research_ready_count",
            "action_status_watch_count",
            "action_status_blocked_count",
            "research_status_ready_count",
            "research_status_watch_count",
            "research_status_blocked_count",
            "status_transition_count",
            "latest_selected_count",
            "latest_skipped_count",
            "latest_not_selected_count",
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
                _require_nonnegative_fixed_six_decimal(
                    field_name,
                    getattr(self, field_name),
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
        _require_optional_research_status(
            "latest_research_status",
            self.latest_research_status,
        )
        object.__setattr__(
            self,
            "latest_top_research_priority_score",
            _require_optional_score_fixed_six_decimal(
                "latest_top_research_priority_score",
                self.latest_top_research_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "latest_average_research_ready_score",
            _require_optional_score_fixed_six_decimal(
                "latest_average_research_ready_score",
                self.latest_average_research_ready_score,
            ),
        )
        object.__setattr__(
            self,
            "ready_notional_delta",
            _require_fixed_six_decimal(
                "ready_notional_delta",
                self.ready_notional_delta,
            ),
        )
        object.__setattr__(
            self,
            "selected_notional_delta",
            _require_fixed_six_decimal(
                "selected_notional_delta",
                self.selected_notional_delta,
            ),
        )
        object.__setattr__(
            self,
            "latest_primary_reason_code_counts_json",
            _normalize_count_json_object(
                "latest_primary_reason_code_counts_json",
                self.latest_primary_reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "latest_reason_codes_json",
            _normalize_reason_codes_json(
                "latest_reason_codes_json",
                self.latest_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(
            self.payload_json,
            "payload_json",
            require_hard_flags=True,
        )
        _validate_row_matches_payload_json(self)
        _validate_payload_recovers_to_canonical_report(self.payload_json)


def paper_strategy_candidate_research_queue_history_report_to_db_row(
    report: PaperStrategyCandidateResearchQueueHistoryReport,
) -> PaperStrategyCandidateResearchQueueHistoryDbRow:
    if type(report) is not PaperStrategyCandidateResearchQueueHistoryReport:
        raise ValueError(
            "report must be a PaperStrategyCandidateResearchQueueHistoryReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperStrategyCandidateResearchQueueHistoryDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        source_report_count=report.source_report_count,
        first_source_generated_at=report.first_source_generated_at,
        last_source_generated_at=report.last_source_generated_at,
        action_status_research_ready_count=(
            report.action_status_research_ready_count
        ),
        action_status_watch_count=report.action_status_watch_count,
        action_status_blocked_count=report.action_status_blocked_count,
        research_status_ready_count=report.research_status_ready_count,
        research_status_watch_count=report.research_status_watch_count,
        research_status_blocked_count=report.research_status_blocked_count,
        total_ready_notional=report.total_ready_notional,
        total_selected_notional=report.total_selected_notional,
        total_suggested_notional=report.total_suggested_notional,
        latest_action_status=report.latest_action_status,
        latest_recommended_next_step=report.latest_recommended_next_step,
        latest_research_status=report.latest_research_status,
        latest_top_research_priority_score=report.latest_top_research_priority_score,
        latest_average_research_ready_score=(
            report.latest_average_research_ready_score
        ),
        status_transition_count=report.status_transition_count,
        ready_notional_delta=report.ready_notional_delta,
        selected_notional_delta=report.selected_notional_delta,
        latest_selected_count=report.latest_selected_count,
        latest_skipped_count=report.latest_skipped_count,
        latest_not_selected_count=report.latest_not_selected_count,
        latest_primary_reason_code_counts_json={
            reason_code: count
            for reason_code, count in report.latest_primary_reason_code_counts
        },
        latest_reason_codes_json=list(report.latest_reason_codes),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_strategy_candidate_research_queue_history_report_from_db_row(
    row: PaperStrategyCandidateResearchQueueHistoryDbRow,
) -> PaperStrategyCandidateResearchQueueHistoryReport:
    if type(row) is not PaperStrategyCandidateResearchQueueHistoryDbRow:
        raise ValueError(
            "row must be a PaperStrategyCandidateResearchQueueHistoryDbRow",
        )
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(
        row.payload_json,
        "payload_json",
        require_hard_flags=True,
    )
    _validate_row_matches_payload_json(row)
    _validate_payload_recovers_to_canonical_report(row.payload_json)
    canonical_payload_json = _normalize_legacy_decimal_payload_json(row.payload_json)
    try:
        report = from_jsonable(
            PaperStrategyCandidateResearchQueueHistoryReport,
            canonical_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid strategy candidate research queue "
            f"history report: {exc}",
        ) from exc
    if type(report) is not PaperStrategyCandidateResearchQueueHistoryReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperStrategyCandidateResearchQueueHistoryReport",
        )
    _validate_report_tree(report)
    expected_row = paper_strategy_candidate_research_queue_history_report_to_db_row(
        report,
    )
    _validate_row_matches_payload(row, expected_row, require_report_sha256=False)
    return report


def _validate_report_tree(
    report: PaperStrategyCandidateResearchQueueHistoryReport,
) -> None:
    _validate_hard_flags_tree(report, "report")
    _validate_unique_count_pairs(
        "latest_primary_reason_code_counts",
        report.latest_primary_reason_code_counts,
    )
    _validate_unique_strings("latest_reason_codes", report.latest_reason_codes)


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
    return any(hasattr(value, flag_name) for flag_name in HARD_FLAG_NAMES)


def _validate_unique_count_pairs(
    field_name: str,
    rows: tuple[tuple[str, int], ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f"{field_name} must contain (reason_code, count) rows")
        reason_code, count = row
        _require_canonical_token(f"{field_name} reason_code", reason_code)
        if type(count) is not int or count <= 0:
            raise ValueError(f"{field_name} count must be positive")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)


def _validate_unique_strings(field_name: str, values: tuple[str, ...]) -> None:
    seen: set[str] = set()
    for value in values:
        _require_canonical_token(f"{field_name} item", value)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)


def _validate_row_matches_payload(
    row: PaperStrategyCandidateResearchQueueHistoryDbRow,
    expected: PaperStrategyCandidateResearchQueueHistoryDbRow,
    *,
    require_report_sha256: bool = True,
) -> None:
    field_names = (
        "report_sha256",
        "generated_at",
        "source_report_count",
        "first_source_generated_at",
        "last_source_generated_at",
        "action_status_research_ready_count",
        "action_status_watch_count",
        "action_status_blocked_count",
        "research_status_ready_count",
        "research_status_watch_count",
        "research_status_blocked_count",
        "total_ready_notional",
        "total_selected_notional",
        "total_suggested_notional",
        "latest_action_status",
        "latest_recommended_next_step",
        "latest_research_status",
        "latest_top_research_priority_score",
        "latest_average_research_ready_score",
        "status_transition_count",
        "ready_notional_delta",
        "selected_notional_delta",
        "latest_selected_count",
        "latest_skipped_count",
        "latest_not_selected_count",
        "latest_primary_reason_code_counts_json",
        "latest_reason_codes_json",
        "paper_only",
        "report_only",
        "readonly",
    )
    for field_name in field_names:
        if field_name == "report_sha256" and not require_report_sha256:
            continue
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_matches_payload_json(
    row: PaperStrategyCandidateResearchQueueHistoryDbRow,
) -> None:
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    canonical_payload_json = _normalize_legacy_decimal_payload_json(payload_json)
    _validate_row_scalars_match_payload(row, canonical_payload_json)
    if (
        row.latest_primary_reason_code_counts_json
        != _latest_primary_reason_code_counts_json_from_payload(canonical_payload_json)
    ):
        raise ValueError(
            "latest_primary_reason_code_counts_json must match payload_json",
        )
    if (
        row.latest_reason_codes_json
        != _latest_reason_codes_json_from_payload(canonical_payload_json)
    ):
        raise ValueError("latest_reason_codes_json must match payload_json")
    for flag_name in HARD_FLAG_NAMES:
        if flag_name not in canonical_payload_json:
            raise ValueError(f"{flag_name} must match payload_json")
        expected_value = canonical_payload_json[flag_name]
        actual_value = getattr(row, flag_name)
        if (
            type(expected_value) is not type(_json_ready(actual_value))
            or actual_value != expected_value
        ):
            raise ValueError(f"{flag_name} must match payload_json")


def _validate_row_scalars_match_payload(
    row: PaperStrategyCandidateResearchQueueHistoryDbRow,
    payload_json: dict[str, Any],
) -> None:
    for field_name in (
        "generated_at",
        "source_report_count",
        "first_source_generated_at",
        "last_source_generated_at",
        "action_status_research_ready_count",
        "action_status_watch_count",
        "action_status_blocked_count",
        "research_status_ready_count",
        "research_status_watch_count",
        "research_status_blocked_count",
        "total_ready_notional",
        "total_selected_notional",
        "total_suggested_notional",
        "latest_action_status",
        "latest_recommended_next_step",
        "latest_research_status",
        "latest_top_research_priority_score",
        "latest_average_research_ready_score",
        "status_transition_count",
        "ready_notional_delta",
        "selected_notional_delta",
        "latest_selected_count",
        "latest_skipped_count",
        "latest_not_selected_count",
    ):
        if field_name not in payload_json:
            raise ValueError(f"{field_name} must match payload_json")
        expected_value = payload_json[field_name]
        actual_value = _json_ready(getattr(row, field_name))
        if (
            type(expected_value) is not type(actual_value)
            or expected_value != actual_value
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_payload_recovers_to_canonical_report(
    payload_json: dict[str, Any],
) -> None:
    canonical_payload_json = _normalize_legacy_decimal_payload_json(payload_json)
    try:
        report = from_jsonable(
            PaperStrategyCandidateResearchQueueHistoryReport,
            canonical_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid strategy candidate research queue "
            f"history report: {exc}",
        ) from exc
    if type(report) is not PaperStrategyCandidateResearchQueueHistoryReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperStrategyCandidateResearchQueueHistoryReport",
        )
    _validate_report_tree(report)
    if canonical_payload_json != _json_ready(asdict(report)):
        raise ValueError("payload_json must match canonical recovered report payload")


def _latest_primary_reason_code_counts_json_from_payload(
    payload_json: dict[str, Any],
) -> dict[str, int]:
    rows = payload_json.get("latest_primary_reason_code_counts")
    if not isinstance(rows, list):
        raise ValueError(
            "latest_primary_reason_code_counts_json must match payload_json",
        )
    result: dict[str, int] = {}
    for item in rows:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(
                "latest_primary_reason_code_counts_json must match payload_json",
            )
        reason_code, count = item
        _require_canonical_token(
            "payload_json latest_primary_reason_code_counts reason_code",
            reason_code,
        )
        if type(count) is not int or count <= 0:
            raise ValueError(
                "payload_json latest_primary_reason_code_counts count must be positive",
            )
        if reason_code in result:
            raise ValueError(
                "payload_json latest_primary_reason_code_counts "
                "must not contain duplicate reason codes",
            )
        result[reason_code] = count
    return result


def _latest_reason_codes_json_from_payload(
    payload_json: dict[str, Any],
) -> list[str]:
    values = payload_json.get("latest_reason_codes")
    if not isinstance(values, list):
        raise ValueError("latest_reason_codes_json must match payload_json")
    seen: set[str] = set()
    result: list[str] = []
    for item in values:
        _require_canonical_token("payload_json latest_reason_codes item", item)
        if item in seen:
            raise ValueError(
                "payload_json latest_reason_codes must not contain duplicates",
            )
        seen.add(item)
        result.append(item)
    return result


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
        return _fixed_six_decimal_string("JSON Decimal value", value)
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
    raise ValueError("strategy candidate research queue history values must be JSON")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    _validate_raw_json_value(field_name, value)
    normalized = _copy_json_value(value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _validate_raw_json_value(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) in (str, int, bool):
        return
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not contain float values")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not contain Decimal values")
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must not contain datetime values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} JSON object keys must be strings")
            _validate_raw_json_value(f"{field_name}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_raw_json_value(f"{field_name}.{index}", item)
        return
    raise ValueError(f"{field_name} must contain only JSON values")


def _copy_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    return value


def _normalize_legacy_decimal_payload_json(
    payload_json: dict[str, Any],
) -> dict[str, Any]:
    normalized = _copy_json_value(payload_json)
    if not isinstance(normalized, dict):
        raise ValueError("payload_json must be a JSON object")
    for field_name in _TOP_LEVEL_DECIMAL_PAYLOAD_FIELDS:
        if field_name not in normalized or normalized[field_name] is None:
            continue
        normalized[field_name] = _fixed_six_decimal_json_string(
            field_name,
            normalized[field_name],
        )
    return normalized


def _normalize_count_json_object(
    field_name: str,
    value: object,
) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    seen: set[str] = set()
    for key, item in normalized.items():
        _require_canonical_token(f"{field_name} key", key)
        if type(item) is not int or item <= 0:
            raise ValueError(f"{field_name} {key} must be a positive int")
        if key in seen:
            raise ValueError(f"{field_name} must not contain duplicate keys")
        seen.add(key)
    return normalized


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON list")
    _validate_raw_json_value(field_name, value)
    normalized = _copy_json_value(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON list")
    seen: set[str] = set()
    result: list[str] = []
    for item in normalized:
        _require_canonical_token(f"{field_name} item", item)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
        result.append(item)
    return result


def _validate_json_hard_flags(
    value: Any,
    field_name: str,
    *,
    require_hard_flags: bool = False,
) -> None:
    if isinstance(value, list):
        for index, element in enumerate(value):
            _validate_json_hard_flags(element, f"{field_name} {index}")
        return
    if not isinstance(value, dict):
        return
    if require_hard_flags or any(flag_name in value for flag_name in HARD_FLAG_NAMES):
        missing_flags = [
            flag_name for flag_name in HARD_FLAG_NAMES if flag_name not in value
        ]
        if missing_flags:
            raise ValueError(
                f"{field_name} hard flags must include "
                "paper_only, report_only, and readonly",
            )
        for flag_name in HARD_FLAG_NAMES:
            if value[flag_name] is not True:
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


def _require_optional_research_status(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in RESEARCH_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


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


def _require_fixed_six_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    try:
        with localcontext() as context:
            integer_digits = max(decimal_value.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            fixed_value = decimal_value.quantize(_SIX_PLACE_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must not exceed six decimal places") from exc
    if decimal_value != fixed_value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return fixed_value


def _require_nonnegative_fixed_six_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    decimal_value = _require_fixed_six_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_score_fixed_six_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    decimal_value = _require_fixed_six_decimal(field_name, value)
    if decimal_value < Decimal("0") or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _fixed_six_decimal_string(field_name: str, value: object) -> str:
    return format(_require_fixed_six_decimal(field_name, value), "f")


def _fixed_six_decimal_json_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string in payload_json")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string in payload_json") from exc
    return _fixed_six_decimal_string(field_name, decimal_value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
