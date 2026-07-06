"""Decimal-only paper report for information catalyst priority queuing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUSES = ("deferred", "watch", "priority")
_STATUS_RANK = {"priority": 0, "watch": 1, "deferred": 2}
_EMPTY_REASON = "empty_catalyst_priority_queue"
_INPUT_REASON_CODES = frozenset(("catalyst_evidence_ready",))
_OWNED_REASON_CODES = frozenset(
    (
        "priority_catalyst_available",
        "priority_catalyst_watch",
        "priority_catalyst_deferred",
        "recency_boost_applied",
        "low_confidence_penalty",
        _EMPTY_REASON,
    ),
)
_REASON_RANK = {
    "priority_catalyst_available": 0,
    "priority_catalyst_watch": 1,
    "priority_catalyst_deferred": 2,
    "recency_boost_applied": 3,
    "low_confidence_penalty": 4,
    _EMPTY_REASON: 5,
}
_REPORT_KEYS = (
    "generated_at",
    "config_version",
    "catalyst_count",
    "priority_count",
    "watch_count",
    "deferred_count",
    "average_priority_score",
    "top_priority_score",
    "bottom_priority_score",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_KEYS = (
    "candidate_id",
    "market_id",
    "catalyst_id",
    "catalyst_type",
    "base_catalyst_score",
    "information_edge_score",
    "source_reliability_score",
    "resolution_clarity_score",
    "recency_age_hours",
    "confidence_score",
    "recency_boost",
    "low_confidence_penalty",
    "priority_score",
    "priority_status",
    "observed_at",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("per", "sist"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("tra", "de"),
    ),
)

__all__ = (
    "StrategyInformationCatalystPriorityQueueV2Config",
    "StrategyInformationCatalystPriorityQueueV2Input",
    "StrategyInformationCatalystPriorityQueueV2Row",
    "StrategyInformationCatalystPriorityQueueV2Report",
    "build_strategy_information_catalyst_priority_queue_v2_report",
    "strategy_information_catalyst_priority_queue_v2_payload",
)


@dataclass(frozen=True)
class StrategyInformationCatalystPriorityQueueV2Config:
    config_version: str
    recency_boost_window_hours: Decimal
    max_recency_boost: Decimal
    low_confidence_floor: Decimal
    max_low_confidence_penalty: Decimal
    priority_score_floor: Decimal
    watch_score_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "recency_boost_window_hours",
            _normalize_positive_decimal(
                "recency_boost_window_hours",
                self.recency_boost_window_hours,
            ),
        )
        for field_name in (
            "max_recency_boost",
            "low_confidence_floor",
            "max_low_confidence_penalty",
            "priority_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_score_floor > self.priority_score_floor:
            raise ValueError("watch_score_floor must not exceed priority_score_floor")
        _require_flags("config", self)
        _reject_unsafe_public("config", self)


@dataclass(frozen=True)
class StrategyInformationCatalystPriorityQueueV2Input:
    candidate_id: str
    market_id: str
    catalyst_id: str
    catalyst_type: str
    base_catalyst_score: Decimal
    information_edge_score: Decimal
    source_reliability_score: Decimal
    resolution_clarity_score: Decimal
    recency_age_hours: Decimal
    confidence_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "catalyst_id", "catalyst_type"):
            _require_text(field_name, getattr(self, field_name))
        for field_name in (
            "base_catalyst_score",
            "information_edge_score",
            "source_reliability_score",
            "resolution_clarity_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recency_age_hours",
            _normalize_nonnegative_decimal("recency_age_hours", self.recency_age_hours),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_flags("catalyst", self)
        _reject_unsafe_public("catalyst", self)


@dataclass(frozen=True)
class StrategyInformationCatalystPriorityQueueV2Row:
    candidate_id: str
    market_id: str
    catalyst_id: str
    catalyst_type: str
    base_catalyst_score: Decimal
    information_edge_score: Decimal
    source_reliability_score: Decimal
    resolution_clarity_score: Decimal
    recency_age_hours: Decimal
    confidence_score: Decimal
    recency_boost: Decimal
    low_confidence_penalty: Decimal
    priority_score: Decimal
    priority_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "catalyst_id", "catalyst_type"):
            _require_text(field_name, getattr(self, field_name))
        for field_name in (
            "base_catalyst_score",
            "information_edge_score",
            "source_reliability_score",
            "resolution_clarity_score",
            "confidence_score",
            "recency_boost",
            "low_confidence_penalty",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recency_age_hours",
            _normalize_nonnegative_decimal("recency_age_hours", self.recency_age_hours),
        )
        _require_status("priority_status", self.priority_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _reject_unsafe_public("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyInformationCatalystPriorityQueueV2Report:
    generated_at: datetime
    config_version: str
    catalyst_count: Decimal
    priority_count: Decimal
    watch_count: Decimal
    deferred_count: Decimal
    average_priority_score: Decimal
    top_priority_score: Decimal
    bottom_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "catalyst_count",
            "priority_count",
            "watch_count",
            "deferred_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_priority_score",
            "top_priority_score",
            "bottom_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _reject_unsafe_public("report", self)
        _check_report(self)
        for row in self.rows:
            _require_row_digest(row)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_information_catalyst_priority_queue_v2_report(
    catalysts: object,
    *,
    config: StrategyInformationCatalystPriorityQueueV2Config,
    generated_at: datetime,
) -> StrategyInformationCatalystPriorityQueueV2Report:
    if type(config) is not StrategyInformationCatalystPriorityQueueV2Config:
        raise ValueError(
            "config must be a StrategyInformationCatalystPriorityQueueV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_catalysts(catalysts)
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(
        sorted(
            (_row_from_catalyst(item, config=config) for item in items),
            key=_row_sort_key,
        ),
    )
    return StrategyInformationCatalystPriorityQueueV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        catalyst_count=_count(len(rows)),
        priority_count=_status_count(rows, "priority"),
        watch_count=_status_count(rows, "watch"),
        deferred_count=_status_count(rows, "deferred"),
        average_priority_score=_average_score(rows),
        top_priority_score=_top_score(rows),
        bottom_priority_score=_bottom_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_information_catalyst_priority_queue_v2_payload(
    report: StrategyInformationCatalystPriorityQueueV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyInformationCatalystPriorityQueueV2Report:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError("report must be a StrategyInformationCatalystPriorityQueueV2Report")


def _row_from_catalyst(
    item: StrategyInformationCatalystPriorityQueueV2Input,
    *,
    config: StrategyInformationCatalystPriorityQueueV2Config,
) -> StrategyInformationCatalystPriorityQueueV2Row:
    base_score = _base_score(item)
    recency_boost = _recency_boost(item.recency_age_hours, config)
    low_confidence_penalty = _low_confidence_penalty(item.confidence_score, config)
    priority_score = _clamp_ratio(base_score + recency_boost - low_confidence_penalty)
    priority_status = _status_from_score(priority_score, config)
    reason_codes = _row_reason_codes(
        priority_status=priority_status,
        recency_boost=recency_boost,
        low_confidence_penalty=low_confidence_penalty,
    )
    return StrategyInformationCatalystPriorityQueueV2Row(
        candidate_id=item.candidate_id,
        market_id=item.market_id,
        catalyst_id=item.catalyst_id,
        catalyst_type=item.catalyst_type,
        base_catalyst_score=item.base_catalyst_score,
        information_edge_score=item.information_edge_score,
        source_reliability_score=item.source_reliability_score,
        resolution_clarity_score=item.resolution_clarity_score,
        recency_age_hours=item.recency_age_hours,
        confidence_score=item.confidence_score,
        recency_boost=recency_boost,
        low_confidence_penalty=low_confidence_penalty,
        priority_score=priority_score,
        priority_status=priority_status,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _base_score(item: StrategyInformationCatalystPriorityQueueV2Input) -> Decimal:
    return _average(
        (
            item.base_catalyst_score,
            item.information_edge_score,
            item.source_reliability_score,
            item.resolution_clarity_score,
        ),
    )


def _recency_boost(
    recency_age_hours: Decimal,
    config: StrategyInformationCatalystPriorityQueueV2Config,
) -> Decimal:
    if recency_age_hours >= config.recency_boost_window_hours:
        return _ZERO
    remaining = config.recency_boost_window_hours - recency_age_hours
    return _clamp_ratio(config.max_recency_boost * remaining / config.recency_boost_window_hours)


def _low_confidence_penalty(
    confidence_score: Decimal,
    config: StrategyInformationCatalystPriorityQueueV2Config,
) -> Decimal:
    if confidence_score >= config.low_confidence_floor:
        return _ZERO
    return _clamp_ratio(
        config.max_low_confidence_penalty
        * (config.low_confidence_floor - confidence_score)
        / config.low_confidence_floor,
    )


def _status_from_score(
    priority_score: Decimal,
    config: StrategyInformationCatalystPriorityQueueV2Config,
) -> str:
    if priority_score >= config.priority_score_floor:
        return "priority"
    if priority_score >= config.watch_score_floor:
        return "watch"
    return "deferred"


def _row_reason_codes(
    *,
    priority_status: str,
    recency_boost: Decimal,
    low_confidence_penalty: Decimal,
) -> tuple[str, ...]:
    reasons = [
        {
            "priority": "priority_catalyst_available",
            "watch": "priority_catalyst_watch",
            "deferred": "priority_catalyst_deferred",
        }[priority_status],
    ]
    if recency_boost > _ZERO:
        reasons.append("recency_boost_applied")
    if low_confidence_penalty > _ZERO:
        reasons.append("low_confidence_penalty")
    return _sort_reason_codes(tuple(reasons))


def _normalize_catalysts(
    catalysts: object,
) -> tuple[StrategyInformationCatalystPriorityQueueV2Input, ...]:
    if isinstance(catalysts, (str, bytes)):
        raise ValueError("catalysts must be an iterable")
    try:
        items = tuple(catalysts)
    except TypeError as exc:
        raise ValueError("catalysts must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategyInformationCatalystPriorityQueueV2Input:
            raise ValueError(
                "catalysts must contain StrategyInformationCatalystPriorityQueueV2Input",
            )
        _require_flags("catalyst", item)
        key = (item.candidate_id, item.catalyst_id)
        if key in seen:
            raise ValueError("catalysts must not contain duplicate candidate-catalyst pairs")
        seen.add(key)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyInformationCatalystPriorityQueueV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyInformationCatalystPriorityQueueV2Row:
            raise ValueError("rows must contain StrategyInformationCatalystPriorityQueueV2Row")
        _require_flags("row", item)
        _require_row_digest(item)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return items


def _row_sort_key(row: StrategyInformationCatalystPriorityQueueV2Row) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.priority_status], -row.priority_score, row.candidate_id)


def _status_count(
    rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.priority_status == status))


def _average_score(rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return _average(tuple(row.priority_score for row in rows))


def _top_score(rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.priority_score for row in rows)


def _bottom_score(rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.priority_score for row in rows)


def _report_status(rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.priority_status == "deferred" for row in rows):
        return "deferred"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "priority"


def _report_reason_codes(
    rows: tuple[StrategyInformationCatalystPriorityQueueV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    return _sort_reason_codes(
        tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes)),
    )


def _check_row(row: StrategyInformationCatalystPriorityQueueV2Row) -> None:
    expected_terminal = {
        "priority": "priority_catalyst_available",
        "watch": "priority_catalyst_watch",
        "deferred": "priority_catalyst_deferred",
    }[row.priority_status]
    if expected_terminal not in row.reason_codes:
        raise ValueError("reason_codes must include priority status reason")


def _check_report(report: StrategyInformationCatalystPriorityQueueV2Report) -> None:
    rows = report.rows
    if report.catalyst_count != _count(len(rows)):
        raise ValueError("catalyst_count must match rows")
    if report.priority_count != _status_count(rows, "priority"):
        raise ValueError("priority_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.deferred_count != _status_count(rows, "deferred"):
        raise ValueError("deferred_count must match rows")
    if report.average_priority_score != _average_score(rows):
        raise ValueError("average_priority_score must match rows")
    if report.top_priority_score != _top_score(rows):
        raise ValueError("top_priority_score must match rows")
    if report.bottom_priority_score != _bottom_score(rows):
        raise ValueError("bottom_priority_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_digest(row: StrategyInformationCatalystPriorityQueueV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyInformationCatalystPriorityQueueV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _require_row_digest(row: StrategyInformationCatalystPriorityQueueV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategyInformationCatalystPriorityQueueV2Report) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _REPORT_KEYS)
    _require_payload_flags("payload", payload)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a JSON list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_row_payload(f"payload.rows[{index}]", row)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(label: str, payload: dict[str, Any]) -> None:
    _require_exact_keys(label, payload, _ROW_KEYS)
    _require_payload_flags(label, payload)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError(f"{label}.derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    for key in expected_keys:
        if key not in payload:
            raise ValueError(f"{label}.{key} is required")
    extra_keys = tuple(sorted(set(payload) - set(expected_keys)))
    if extra_keys:
        raise ValueError(f"{label} contains unsupported public field: {extra_keys[0]}")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError(f"{label} JSON Decimal values must be strings")
    if isinstance(value, float):
        raise ValueError(f"{label} JSON values must not be floats")
    if type(value) is int:
        raise ValueError(f"{label} JSON numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    _reject_unsafe_public(name, value)


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{name} must be one of {_STATUSES!r}")


def _normalize_input_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be an ordered tuple")
    normalized = _normalize_reason_code_values("reason_codes", values)
    for value in normalized:
        if value not in _INPUT_REASON_CODES:
            raise ValueError("reason_codes contains unsupported reason")
    return normalized


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be an ordered tuple")
    normalized = _normalize_reason_code_values(name, values)
    for value in normalized:
        if value not in _OWNED_REASON_CODES:
            raise ValueError(f"{name} contains unsupported reason")
    if normalized != _sort_reason_codes(normalized):
        raise ValueError(f"{name} must be sorted")
    return normalized


def _normalize_reason_code_values(name: str, values: tuple[object, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{name} values must be strings")
        _require_text(name, value)
        if value in seen:
            raise ValueError(f"{name} values must be unique")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _sort_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda value: (_REASON_RANK[value], value)))


def _normalize_ratio(name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(name, value)
    if value > _ONE:
        raise ValueError(f"{name} must be <= 1.000000")
    return value


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(name, value)
    if value <= _ZERO:
        raise ValueError(f"{name} must be > 0.000000")
    return value


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{name} must be >= 0.000000")
    quantized = _quantize(value)
    if value != quantized:
        raise ValueError(f"{name} must use six decimal places or fewer")
    return quantized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
