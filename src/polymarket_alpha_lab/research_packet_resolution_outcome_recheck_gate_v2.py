"""Phase 1 outcome-source recheck readiness gate for closed research packets."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_RECHECK_GATE_V2_CONFIG_VERSION = (
    "research-packet-resolution-outcome-recheck-gate-v2-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_EMPTY = "empty"
ROW_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
REPORT_STATUSES = (STATUS_EMPTY, *ROW_STATUSES)
STATUS_SORT_RANK = {
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "outcome_recheck_gate_pass"
WATCH_REASON = "outcome_recheck_gate_watch"
BLOCK_REASON = "outcome_recheck_gate_block"
EMPTY_REASON = "outcome_recheck_gate_empty"
MISSING_CHECK_REASON = "missing_outcome_source_check"
MISSING_OFFICIAL_REASON = "missing_official_outcome_source"
CONFLICT_REASON = "conflicting_outcome_sources_present"
DISPUTE_REASON = "unresolved_disputes_present"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    MISSING_CHECK_REASON,
    MISSING_OFFICIAL_REASON,
    CONFLICT_REASON,
    DISPUTE_REASON,
)
REPORT_REASON_CODES = (*ROW_REASON_CODES, EMPTY_REASON)
REASON_CODE_SET = frozenset(REPORT_REASON_CODES)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_RECHECK_GATE_V2_CONFIG_VERSION",
    "ResearchPacketResolutionOutcomeRecheckGateV2Input",
    "ResearchPacketResolutionOutcomeRecheckGateV2Row",
    "ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount",
    "ResearchPacketResolutionOutcomeRecheckGateV2Report",
    "build_research_packet_resolution_outcome_recheck_gate_v2_report",
    "research_packet_resolution_outcome_recheck_gate_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeRecheckGateV2Input:
    packet_id: str
    market_id: str
    event_slug: str
    category: str
    market_closed_at: datetime
    outcome_source_checked_at: datetime | None
    official_outcome_source_count: Decimal
    conflicting_outcome_source_count: Decimal
    unresolved_dispute_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketResolutionOutcomeRecheckGateV2Input,
            "input",
        )
        for field_name in ("packet_id", "market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "outcome_source_checked_at",
            _optional_utc(
                "outcome_source_checked_at",
                self.outcome_source_checked_at,
            ),
        )
        for field_name in (
            "official_outcome_source_count",
            "conflicting_outcome_source_count",
            "unresolved_dispute_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)
        reject_unsafe_surface_fields("input", self)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeRecheckGateV2Row:
    packet_id: str
    market_id: str
    event_slug: str
    category: str
    market_closed_at: datetime
    outcome_source_checked_at: datetime | None
    official_outcome_source_count: Decimal
    conflicting_outcome_source_count: Decimal
    unresolved_dispute_count: Decimal
    close_age_seconds: Decimal
    outcome_check_age_seconds: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketResolutionOutcomeRecheckGateV2Row,
            "row",
        )
        for field_name in ("packet_id", "market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "outcome_source_checked_at",
            _optional_utc(
                "outcome_source_checked_at",
                self.outcome_source_checked_at,
            ),
        )
        for field_name in (
            "official_outcome_source_count",
            "conflicting_outcome_source_count",
            "unresolved_dispute_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "close_age_seconds",
            _nonnegative_seconds("close_age_seconds", self.close_age_seconds),
        )
        object.__setattr__(
            self,
            "outcome_check_age_seconds",
            _optional_nonnegative_seconds(
                "outcome_check_age_seconds",
                self.outcome_check_age_seconds,
            ),
        )
        _require_choice("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)
        reject_unsafe_surface_fields("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        require_paper_only_flags("reason code count", self)
        reject_unsafe_surface_fields("reason code count", self)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeRecheckGateV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_outcome_check_count: Decimal
    conflict_count: Decimal
    unresolved_dispute_count: Decimal
    max_close_age_seconds: Decimal
    rows: tuple[ResearchPacketResolutionOutcomeRecheckGateV2Row, ...]
    reason_code_counts: tuple[
        ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketResolutionOutcomeRecheckGateV2Report,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_RECHECK_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_outcome_check_count",
            "conflict_count",
            "unresolved_dispute_count",
            "max_close_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)
        _set_or_validate_digest(self, "report")


def build_research_packet_resolution_outcome_recheck_gate_v2_report(
    rows: Iterable[ResearchPacketResolutionOutcomeRecheckGateV2Input],
    *,
    generated_at: datetime,
) -> ResearchPacketResolutionOutcomeRecheckGateV2Report:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (
                _row_from_input(row, generated_at=generated_at_utc)
                for row in normalized_rows
            ),
            key=_row_sort_key,
        ),
    )
    packet_count = _decimal_from_int(len(report_rows))
    return ResearchPacketResolutionOutcomeRecheckGateV2Report(
        generated_at=generated_at_utc,
        config_version=(
            DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_RECHECK_GATE_V2_CONFIG_VERSION
        ),
        report_status=_report_status(report_rows),
        packet_count=packet_count,
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        missing_outcome_check_count=_reason_count(
            report_rows,
            MISSING_CHECK_REASON,
        ),
        conflict_count=_positive_source_count(
            row.conflicting_outcome_source_count for row in report_rows
        ),
        unresolved_dispute_count=_positive_source_count(
            row.unresolved_dispute_count for row in report_rows
        ),
        max_close_age_seconds=max(
            (row.close_age_seconds for row in report_rows),
            default=ZERO,
        ),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, packet_count),
    )


def research_packet_resolution_outcome_recheck_gate_v2_payload(
    report: ResearchPacketResolutionOutcomeRecheckGateV2Report,
) -> "FrozenJsonObject":
    if type(report) is not ResearchPacketResolutionOutcomeRecheckGateV2Report:
        raise ValueError(
            "report must be exactly ResearchPacketResolutionOutcomeRecheckGateV2Report",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("payload", payload)
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_from_input(
    row: ResearchPacketResolutionOutcomeRecheckGateV2Input,
    *,
    generated_at: datetime,
) -> ResearchPacketResolutionOutcomeRecheckGateV2Row:
    if row.market_closed_at > generated_at:
        raise ValueError("market_closed_at must not be after generated_at")
    if row.outcome_source_checked_at is not None:
        if row.outcome_source_checked_at > generated_at:
            raise ValueError("outcome_source_checked_at must not be after generated_at")
        if row.outcome_source_checked_at < row.market_closed_at:
            raise ValueError(
                "outcome_source_checked_at must not be before market_closed_at",
            )
    reason_codes = _row_reason_codes(row)
    return ResearchPacketResolutionOutcomeRecheckGateV2Row(
        packet_id=row.packet_id,
        market_id=row.market_id,
        event_slug=row.event_slug,
        category=row.category,
        market_closed_at=row.market_closed_at,
        outcome_source_checked_at=row.outcome_source_checked_at,
        official_outcome_source_count=row.official_outcome_source_count,
        conflicting_outcome_source_count=row.conflicting_outcome_source_count,
        unresolved_dispute_count=row.unresolved_dispute_count,
        close_age_seconds=_duration_seconds(row.market_closed_at, generated_at),
        outcome_check_age_seconds=(
            None
            if row.outcome_source_checked_at is None
            else _duration_seconds(row.outcome_source_checked_at, generated_at)
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchPacketResolutionOutcomeRecheckGateV2Input,
) -> tuple[str, ...]:
    return _reason_codes_for_values(
        outcome_source_checked_at=row.outcome_source_checked_at,
        official_outcome_source_count=row.official_outcome_source_count,
        conflicting_outcome_source_count=row.conflicting_outcome_source_count,
        unresolved_dispute_count=row.unresolved_dispute_count,
    )


def _reason_codes_for_values(
    *,
    outcome_source_checked_at: datetime | None,
    official_outcome_source_count: Decimal,
    conflicting_outcome_source_count: Decimal,
    unresolved_dispute_count: Decimal,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    has_block_reason = False
    if outcome_source_checked_at is None:
        detail_reasons.append(MISSING_CHECK_REASON)
        has_block_reason = True
    if official_outcome_source_count == ZERO:
        detail_reasons.append(MISSING_OFFICIAL_REASON)
        has_block_reason = True
    if conflicting_outcome_source_count > ZERO:
        detail_reasons.append(CONFLICT_REASON)
    if unresolved_dispute_count > ZERO:
        detail_reasons.append(DISPUTE_REASON)
        has_block_reason = True

    if has_block_reason:
        return (BLOCK_REASON, *detail_reasons)
    if detail_reasons:
        return (WATCH_REASON, *detail_reasons)
    return (PASS_REASON,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchPacketResolutionOutcomeRecheckGateV2Row, ...],
) -> str:
    if not rows:
        return STATUS_EMPTY
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_inputs(
    rows: Iterable[ResearchPacketResolutionOutcomeRecheckGateV2Input],
) -> tuple[ResearchPacketResolutionOutcomeRecheckGateV2Input, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be an iterable of inputs")
    normalized = tuple(rows)
    seen_packet_ids: set[str] = set()
    seen_market_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketResolutionOutcomeRecheckGateV2Input:
            raise ValueError(
                "rows must contain ResearchPacketResolutionOutcomeRecheckGateV2Input",
            )
        require_paper_only_flags("input", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("packet_id values must be unique")
        if row.market_id in seen_market_ids:
            raise ValueError("market_id values must be unique")
        seen_packet_ids.add(row.packet_id)
        seen_market_ids.add(row.market_id)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketResolutionOutcomeRecheckGateV2Row, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_packet_ids: set[str] = set()
    seen_market_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketResolutionOutcomeRecheckGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketResolutionOutcomeRecheckGateV2Row",
            )
        require_paper_only_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows packet_id values must be unique")
        if row.market_id in seen_market_ids:
            raise ValueError("rows market_id values must be unique")
        seen_packet_ids.add(row.packet_id)
        seen_market_ids.add(row.market_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchPacketResolutionOutcomeRecheckGateV2Row,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.close_age_seconds,
        row.event_slug,
        row.category,
        row.packet_id,
        row.market_id,
    )


def _reason_code_counts(
    rows: tuple[ResearchPacketResolutionOutcomeRecheckGateV2Row, ...],
    packet_count: Decimal,
) -> tuple[ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
                reason_code=EMPTY_REASON,
                row_count=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchPacketResolutionOutcomeRecheckGateV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchPacketResolutionOutcomeRecheckGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_from_int(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _positive_source_count(values: Iterable[Decimal]) -> Decimal:
    return _decimal_from_int(sum(1 for value in values if value > ZERO))


def _validate_row_consistency(
    row: ResearchPacketResolutionOutcomeRecheckGateV2Row,
) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if (row.outcome_source_checked_at is None) != (
        row.outcome_check_age_seconds is None
    ):
        raise ValueError(
            "outcome_check_age_seconds must match outcome_source_checked_at",
        )
    if row.outcome_source_checked_at is not None:
        if row.outcome_source_checked_at < row.market_closed_at:
            raise ValueError(
                "outcome_source_checked_at must not be before market_closed_at",
            )
    expected_reason_codes = _reason_codes_for_values(
        outcome_source_checked_at=row.outcome_source_checked_at,
        official_outcome_source_count=row.official_outcome_source_count,
        conflicting_outcome_source_count=row.conflicting_outcome_source_count,
        unresolved_dispute_count=row.unresolved_dispute_count,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row outcome source fields")


def _validate_report_consistency(
    report: ResearchPacketResolutionOutcomeRecheckGateV2Report,
) -> None:
    expected_packet_count = _decimal_from_int(len(report.rows))
    expected_values = {
        "packet_count": expected_packet_count,
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "missing_outcome_check_count": _reason_count(report.rows, MISSING_CHECK_REASON),
        "conflict_count": _positive_source_count(
            row.conflicting_outcome_source_count for row in report.rows
        ),
        "unresolved_dispute_count": _positive_source_count(
            row.unresolved_dispute_count for row in report.rows
        ),
        "max_close_age_seconds": max(
            (row.close_age_seconds for row in report.rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    expected_reason_code_counts = _reason_code_counts(
        report.rows,
        expected_packet_count,
    )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        if allow_empty:
            return ()
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and len(reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    if reason_codes[0] == WATCH_REASON and any(
        reason in (MISSING_CHECK_REASON, MISSING_OFFICIAL_REASON, DISPUTE_REASON)
        for reason in reason_codes[1:]
    ):
        raise ValueError("watch reason_codes must not contain block reasons")
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    reject_unsafe_surface_fields(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _nonnegative_seconds(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _optional_nonnegative_seconds(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_seconds(name, value)


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")
