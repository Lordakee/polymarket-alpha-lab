"""Report-only guard for manual execution boundary leakage in research packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import re
from typing import Any


STATUS_VALUES = frozenset(("pass", "watch", "block"))

_CLEAR_REASON = "boundary_clear"
_WATCH_REASON = "human_boundary_watch"
_CREDENTIAL_REASON = "credential_leak_block"
_INTENT_REASON = "intent_language_block"
_RAW_CONTEXT_REASON = "raw_context_block"

_BLOCK_REASON_ORDER = (
    _CREDENTIAL_REASON,
    _INTENT_REASON,
    _RAW_CONTEXT_REASON,
)

_CREDENTIAL_KEY_FRAGMENTS = frozenset(
    (
        "api_key",
        "auth",
        "bearer",
        "private_key",
        "secret",
        "token",
        "wallet",
    ),
)

_EXECUTION_KEY_FRAGMENTS = frozenset(
    (
        "buy",
        "contract",
        "fill",
        "order",
        "position",
        "recommend",
        "sell",
        "share",
        "side",
        "size",
        "ticket",
        "trade",
    ),
)

_RAW_CONTEXT_KEY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "database",
        "dsn",
        "market_id",
        "market_slug",
        "question",
        "raw_candidate",
        "raw_market",
        "slug",
        "source",
        "table",
        "url",
    ),
)

_WATCH_KEY_FRAGMENTS = frozenset(
    (
        "approval",
        "handoff",
        "human",
        "manual",
        "operator",
        "review_request",
        "review_requested",
    ),
)

_CREDENTIAL_VALUE_PATTERNS = (
    re.compile(r"\b0x[a-f0-9]{40}\b", re.IGNORECASE),
    re.compile(r"\b(?:api[_ -]?key|auth|bearer|private[_ -]?key|secret|token|wallet)\b", re.IGNORECASE),
)

_EXECUTION_VALUE_PATTERNS = (
    re.compile(r"\b(?:buy|sell|recommend|recommendation|order|trade|position|shares?|contracts?)\b", re.IGNORECASE),
)

_RAW_CONTEXT_VALUE_PATTERNS = (
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"\b(?:candidate|market[_ -]?id|market[_ -]?slug|question|source|dsn|table)\b", re.IGNORECASE),
    re.compile(r"\b(?:postgres|postgresql|mysql|sqlite)://", re.IGNORECASE),
)

_WATCH_VALUE_PATTERNS = (
    re.compile(r"\b(?:manual review|human review|operator review|handoff|approval requested)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ResearchManualExecutionBoundaryGuardPacket:
    packet_key: str
    body: object
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualExecutionBoundaryGuardPacket, "packet")
        _require_canonical_string("packet_key", self.packet_key)
        object.__setattr__(self, "body", _json_ready_no_floats(self.body))
        _require_hard_flags("packet", self)


@dataclass(frozen=True)
class ResearchManualExecutionBoundaryGuardRow:
    item_key: str
    status: str
    finding_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualExecutionBoundaryGuardRow, "row")
        _require_public_item_key("item_key", self.item_key)
        _require_status("status", self.status)
        object.__setattr__(self, "finding_count", _require_nonnegative_int("finding_count", self.finding_count))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchManualExecutionBoundaryGuardReport:
    generated_at: datetime
    item_count: int
    pass_count: int
    watch_count: int
    block_count: int
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchManualExecutionBoundaryGuardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualExecutionBoundaryGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_int(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_manual_execution_boundary_guard_payload(self)


def build_research_manual_execution_boundary_guard_report(
    packets: tuple[ResearchManualExecutionBoundaryGuardPacket, ...],
    *,
    generated_at: datetime,
) -> ResearchManualExecutionBoundaryGuardReport:
    if type(packets) is not tuple:
        raise ValueError("packets must be a tuple")
    rows = tuple(sorted((_row_from_packet(packet) for packet in packets), key=_row_sort_key))
    block_count = sum(1 for row in rows if row.status == "block")
    watch_count = sum(1 for row in rows if row.status == "watch")
    pass_count = sum(1 for row in rows if row.status == "pass")
    status = _report_status(block_count, watch_count)
    reason_codes = _report_reason_codes(rows, status)
    return ResearchManualExecutionBoundaryGuardReport(
        generated_at=generated_at,
        item_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
    )


def research_manual_execution_boundary_guard_payload(
    report: ResearchManualExecutionBoundaryGuardReport | dict[str, Any],
) -> dict[str, object]:
    if type(report) is ResearchManualExecutionBoundaryGuardReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report)
        _reject_unsafe_public_payload("report", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError("report must be a ResearchManualExecutionBoundaryGuardReport")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_packet(
    packet: ResearchManualExecutionBoundaryGuardPacket,
) -> ResearchManualExecutionBoundaryGuardRow:
    if type(packet) is not ResearchManualExecutionBoundaryGuardPacket:
        raise ValueError("packets must contain ResearchManualExecutionBoundaryGuardPacket values")
    _require_hard_flags("packet", packet)
    reason_codes = _scan_reason_codes(packet.body)
    status = _status_from_reason_codes(reason_codes)
    return ResearchManualExecutionBoundaryGuardRow(
        item_key=_redacted_item_key(packet.packet_key),
        status=status,
        finding_count=0 if reason_codes == (_CLEAR_REASON,) else len(reason_codes),
        reason_codes=reason_codes,
    )


def _scan_reason_codes(value: object) -> tuple[str, ...]:
    reasons: set[str] = set()
    watch = False
    for key, item in _walk(value):
        if key is not None:
            normalized_key = key.lower()
            if _has_fragment(normalized_key, _CREDENTIAL_KEY_FRAGMENTS):
                reasons.add(_CREDENTIAL_REASON)
            if _has_fragment(normalized_key, _EXECUTION_KEY_FRAGMENTS):
                reasons.add(_INTENT_REASON)
            if _has_fragment(normalized_key, _RAW_CONTEXT_KEY_FRAGMENTS):
                reasons.add(_RAW_CONTEXT_REASON)
            if _has_fragment(normalized_key, _WATCH_KEY_FRAGMENTS):
                watch = True
        if type(item) is str:
            if _matches_any(item, _CREDENTIAL_VALUE_PATTERNS):
                reasons.add(_CREDENTIAL_REASON)
            if _matches_any(item, _EXECUTION_VALUE_PATTERNS):
                reasons.add(_INTENT_REASON)
            if _matches_any(item, _RAW_CONTEXT_VALUE_PATTERNS):
                reasons.add(_RAW_CONTEXT_REASON)
            if _matches_any(item, _WATCH_VALUE_PATTERNS):
                watch = True
    if reasons:
        return tuple(reason for reason in _BLOCK_REASON_ORDER if reason in reasons)
    if watch:
        return (_WATCH_REASON,)
    return (_CLEAR_REASON,)


def _walk(value: object, key: str | None = None) -> tuple[tuple[str | None, object], ...]:
    if isinstance(value, dict):
        rows: list[tuple[str | None, object]] = []
        for item_key in sorted(value):
            item = value[item_key]
            rows.append((item_key, item))
            rows.extend(_walk(item, item_key))
        return tuple(rows)
    if isinstance(value, list):
        rows = []
        for item in value:
            rows.extend(_walk(item, key))
        return tuple(rows)
    return ((key, value),)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (_WATCH_REASON,):
        return "watch"
    return "pass"


def _report_status(block_count: int, watch_count: int) -> str:
    if block_count:
        return "block"
    if watch_count:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchManualExecutionBoundaryGuardRow, ...],
    status: str,
) -> tuple[str, ...]:
    if status == "pass":
        return (_CLEAR_REASON,)
    reasons = sorted(
        {
            reason
            for row in rows
            for reason in row.reason_codes
            if reason != _CLEAR_REASON
        },
    )
    if not reasons:
        raise ValueError("non-pass report must include non-clear reason codes")
    return tuple(reasons)


def _report_payload(report: ResearchManualExecutionBoundaryGuardReport) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "item_count": report.item_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchManualExecutionBoundaryGuardRow) -> dict[str, object]:
    return {
        "item_key": row.item_key,
        "status": row.status,
        "finding_count": row.finding_count,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _redacted_item_key(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"item_{digest}"


def _row_sort_key(row: ResearchManualExecutionBoundaryGuardRow) -> tuple[str, str]:
    return (row.item_key, row.status)


def _normalize_rows(
    rows: tuple[ResearchManualExecutionBoundaryGuardRow, ...],
) -> tuple[ResearchManualExecutionBoundaryGuardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchManualExecutionBoundaryGuardRow] = []
    for row in rows:
        if type(row) is not ResearchManualExecutionBoundaryGuardRow:
            raise ValueError("rows must contain ResearchManualExecutionBoundaryGuardRow values")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_row_consistency(row: ResearchManualExecutionBoundaryGuardRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("row status does not match reason_codes")
    expected_finding_count = 0 if row.reason_codes == (_CLEAR_REASON,) else len(row.reason_codes)
    if row.finding_count != expected_finding_count:
        raise ValueError("row finding_count does not match reason_codes")


def _validate_report_consistency(report: ResearchManualExecutionBoundaryGuardReport) -> None:
    if report.item_count != len(report.rows):
        raise ValueError("item_count does not match rows")
    if report.pass_count != sum(1 for row in report.rows if row.status == "pass"):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != sum(1 for row in report.rows if row.status == "watch"):
        raise ValueError("watch_count does not match rows")
    if report.block_count != sum(1 for row in report.rows if row.status == "block"):
        raise ValueError("block_count does not match rows")
    if report.status != _report_status(report.block_count, report.watch_count):
        raise ValueError("report status does not match row counts")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("report reason_codes do not match rows")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must be nonempty")
    codes: list[str] = []
    for item in value:
        _require_reason_code(item)
        codes.append(item)
    return tuple(sorted(set(codes)))


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError("reason_code must be canonical")
    if not re.fullmatch(r"[a-z0-9_]+", value):
        raise ValueError("reason_code must be snake_case")
    _reject_unsafe_string("reason_code", value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_item_key(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not re.fullmatch(r"item_[a-f0-9]{16}", value):
        raise ValueError(f"{field_name} must be a redacted item key")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _json_ready_no_floats(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_floats(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_floats(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_floats(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_string(label, key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_string(label, value)


def _reject_unsafe_string(label: str, value: str) -> None:
    normalized = value.lower()
    if _has_fragment(normalized, _CREDENTIAL_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public credential surface in {label}")
    if _has_fragment(normalized, _EXECUTION_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public execution surface in {label}")
    if _has_fragment(normalized, _RAW_CONTEXT_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public raw context surface in {label}")
    if _matches_any(value, _CREDENTIAL_VALUE_PATTERNS):
        raise ValueError(f"unsafe public credential value in {label}")
    if _matches_any(value, _EXECUTION_VALUE_PATTERNS):
        raise ValueError(f"unsafe public execution value in {label}")
    if _matches_any(value, _RAW_CONTEXT_VALUE_PATTERNS):
        raise ValueError(f"unsafe public raw context value in {label}")


def _has_fragment(value: str, fragments: frozenset[str]) -> bool:
    return any(fragment in value for fragment in fragments)


def _matches_any(value: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(value) is not None for pattern in patterns)


__all__ = (
    "ResearchManualExecutionBoundaryGuardPacket",
    "ResearchManualExecutionBoundaryGuardReport",
    "ResearchManualExecutionBoundaryGuardRow",
    "build_research_manual_execution_boundary_guard_report",
    "research_manual_execution_boundary_guard_payload",
)
