"""Readonly event resolution disagreement memory scorecard report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_DISAGREEMENT_MEMORY_SCORECARD_CONFIG_VERSION = (
    "event-resolution-disagreement-memory-scorecard-v0"
)

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": ZERO,
    "watch": ONE,
    "pass": Decimal("2.000000"),
}

PASS_REASON = "event_resolution_disagreement_memory_pass"
EMPTY_REASON = "event_resolution_disagreement_memory_empty"
WATCH_DISAGREEMENT_REASON = "resolution_disagreement_watch"
BLOCK_DISAGREEMENT_REASON = "resolution_disagreement_block"
WATCH_MEMORY_REASON = "disagreement_memory_watch"
BLOCK_MEMORY_REASON = "disagreement_memory_block"
LOW_CONFIRMATION_REASON = "resolution_confirmation_low"

ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_DISAGREEMENT_REASON,
    BLOCK_DISAGREEMENT_REASON,
    WATCH_MEMORY_REASON,
    BLOCK_MEMORY_REASON,
    LOW_CONFIRMATION_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_DISAGREEMENT_REASON,
    BLOCK_DISAGREEMENT_REASON,
    WATCH_MEMORY_REASON,
    BLOCK_MEMORY_REASON,
    LOW_CONFIRMATION_REASON,
)

TOP_LEVEL_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "watch_disagreement_score",
        "block_disagreement_score",
        "watch_memory_score",
        "block_memory_score",
        "min_resolution_confirmation_score",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_current_resolution_disagreement_score",
        "max_memory_score",
        "average_memory_score",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "event_reference",
        "event_type",
        "observed_at",
        "resolved_at",
        "current_resolution_disagreement_score",
        "previous_resolution_disagreement_score",
        "disagreement_memory_decay_score",
        "resolution_confirmation_score",
        "evidence_family_count",
        "conflicting_family_count",
        "memory_score",
        "disagreement_delta",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
TOP_LEVEL_DECIMAL_FIELDS = frozenset(
    (
        "watch_disagreement_score",
        "block_disagreement_score",
        "watch_memory_score",
        "block_memory_score",
        "min_resolution_confirmation_score",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_current_resolution_disagreement_score",
        "max_memory_score",
        "average_memory_score",
    ),
)
ROW_DECIMAL_FIELDS = frozenset(
    (
        "current_resolution_disagreement_score",
        "previous_resolution_disagreement_score",
        "disagreement_memory_decay_score",
        "resolution_confirmation_score",
        "evidence_family_count",
        "conflicting_family_count",
        "memory_score",
        "disagreement_delta",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "://",
        "candidate",
        "dsn",
        "https://",
        "http://",
        "market",
        "network",
        "order",
        "postgres://",
        "question",
        "raw_candidate_text",
        "raw_text",
        "recommendation",
        "secret",
        "sizing",
        "slug",
        "source_url",
        "table",
        "token",
        "trade",
        "trading",
        "url",
        "wallet",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_DISAGREEMENT_MEMORY_SCORECARD_CONFIG_VERSION",
    "EventResolutionDisagreementMemoryScorecardConfig",
    "EventResolutionDisagreementMemoryInput",
    "EventResolutionDisagreementMemoryScorecardRow",
    "EventResolutionDisagreementMemoryScorecardReport",
    "build_research_event_resolution_disagreement_memory_scorecard_report",
    "research_event_resolution_disagreement_memory_scorecard_report_payload",
    "validate_research_event_resolution_disagreement_memory_scorecard_public_payload",
)


@dataclass(frozen=True)
class EventResolutionDisagreementMemoryScorecardConfig:
    watch_disagreement_score: Decimal = Decimal("0.300000")
    block_disagreement_score: Decimal = Decimal("0.700000")
    watch_memory_score: Decimal = Decimal("0.300000")
    block_memory_score: Decimal = Decimal("0.700000")
    min_resolution_confirmation_score: Decimal = Decimal("0.500000")
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_DISAGREEMENT_MEMORY_SCORECARD_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "watch_disagreement_score",
            "block_disagreement_score",
            "watch_memory_score",
            "block_memory_score",
            "min_resolution_confirmation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_disagreement_score <= self.watch_disagreement_score:
            raise ValueError(
                "block_disagreement_score must exceed watch_disagreement_score",
            )
        if self.block_memory_score <= self.watch_memory_score:
            raise ValueError("block_memory_score must exceed watch_memory_score")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class EventResolutionDisagreementMemoryInput:
    event_id: str
    event_type: str
    observed_at: datetime
    resolved_at: datetime
    current_resolution_disagreement_score: Decimal
    previous_resolution_disagreement_score: Decimal
    disagreement_memory_decay_score: Decimal
    resolution_confirmation_score: Decimal
    evidence_family_count: Decimal
    conflicting_family_count: Decimal
    raw_candidate_text: str = ""
    source_url: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_id", "event_type"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "current_resolution_disagreement_score",
            "previous_resolution_disagreement_score",
            "disagreement_memory_decay_score",
            "resolution_confirmation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_family_count", "conflicting_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        if self.conflicting_family_count > self.evidence_family_count:
            raise ValueError("conflicting_family_count must not exceed evidence_family_count")
        _require_raw_string("raw_candidate_text", self.raw_candidate_text)
        _require_raw_string("source_url", self.source_url)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class EventResolutionDisagreementMemoryScorecardRow:
    event_reference: str
    event_type: str
    observed_at: datetime
    resolved_at: datetime
    current_resolution_disagreement_score: Decimal
    previous_resolution_disagreement_score: Decimal
    disagreement_memory_decay_score: Decimal
    resolution_confirmation_score: Decimal
    evidence_family_count: Decimal
    conflicting_family_count: Decimal
    memory_score: Decimal
    disagreement_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_reference",
            _require_digest("event_reference", self.event_reference),
        )
        object.__setattr__(
            self,
            "event_type",
            _require_public_identifier("event_type", self.event_type),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "current_resolution_disagreement_score",
            "previous_resolution_disagreement_score",
            "disagreement_memory_decay_score",
            "resolution_confirmation_score",
            "memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_family_count", "conflicting_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "disagreement_delta",
            _require_decimal("disagreement_delta", self.disagreement_delta),
        )
        _require_known_value("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class EventResolutionDisagreementMemoryScorecardReport:
    generated_at: datetime
    config_version: str
    watch_disagreement_score: Decimal
    block_disagreement_score: Decimal
    watch_memory_score: Decimal
    block_memory_score: Decimal
    min_resolution_confirmation_score: Decimal
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_current_resolution_disagreement_score: Decimal
    max_memory_score: Decimal
    average_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[EventResolutionDisagreementMemoryScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "watch_disagreement_score",
            "block_disagreement_score",
            "watch_memory_score",
            "block_memory_score",
            "min_resolution_confirmation_score",
            "max_current_resolution_disagreement_score",
            "max_memory_score",
            "average_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        _require_known_value("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_event_resolution_disagreement_memory_scorecard_report(
    events: tuple[EventResolutionDisagreementMemoryInput, ...]
    | list[EventResolutionDisagreementMemoryInput],
    *,
    config: EventResolutionDisagreementMemoryScorecardConfig,
    generated_at: datetime,
) -> EventResolutionDisagreementMemoryScorecardReport:
    if type(config) is not EventResolutionDisagreementMemoryScorecardConfig:
        raise ValueError(
            "config must be an EventResolutionDisagreementMemoryScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    event,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for event in _normalize_inputs(events)
            ),
            key=_row_sort_key,
        ),
    )
    event_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    return EventResolutionDisagreementMemoryScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        watch_disagreement_score=config.watch_disagreement_score,
        block_disagreement_score=config.block_disagreement_score,
        watch_memory_score=config.watch_memory_score,
        block_memory_score=config.block_memory_score,
        min_resolution_confirmation_score=config.min_resolution_confirmation_score,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_current_resolution_disagreement_score=_max_decimal(
            row.current_resolution_disagreement_score for row in rows
        ),
        max_memory_score=_max_decimal(row.memory_score for row in rows),
        average_memory_score=_average_decimal(row.memory_score for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_resolution_disagreement_memory_scorecard_report_payload(
    report: EventResolutionDisagreementMemoryScorecardReport,
) -> dict[str, Any]:
    if type(report) is not EventResolutionDisagreementMemoryScorecardReport:
        raise ValueError(
            "report must be an EventResolutionDisagreementMemoryScorecardReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
        payload,
    )
    return payload


def validate_research_event_resolution_disagreement_memory_scorecard_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics(payload)
    _reject_unknown_keys("public payload", payload, TOP_LEVEL_PAYLOAD_KEYS)
    _require_required_keys("public payload", payload, TOP_LEVEL_PAYLOAD_KEYS)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _require_public_identifier("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    for field_name in TOP_LEVEL_DECIMAL_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_known_value("status", payload["status"], STATUSES)
    _normalize_reason_codes(
        "reason_codes",
        _require_list("reason_codes", payload["reason_codes"]),
        REPORT_REASON_CODES,
    )
    rows = _require_list("rows", payload["rows"])
    for row in rows:
        _validate_public_row_payload(row)
    digest = payload["derived_validation_digest"]
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_input(
    event: EventResolutionDisagreementMemoryInput,
    *,
    config: EventResolutionDisagreementMemoryScorecardConfig,
    generated_at: datetime,
) -> EventResolutionDisagreementMemoryScorecardRow:
    if type(event) is not EventResolutionDisagreementMemoryInput:
        raise ValueError("event must be an EventResolutionDisagreementMemoryInput")
    _require_hard_flags("event", event)
    _validate_not_after("observed_at", event.observed_at, generated_at)
    _validate_not_after("resolved_at", event.resolved_at, generated_at)
    memory_score = _memory_score(
        current_resolution_disagreement_score=event.current_resolution_disagreement_score,
        previous_resolution_disagreement_score=event.previous_resolution_disagreement_score,
        disagreement_memory_decay_score=event.disagreement_memory_decay_score,
    )
    disagreement_delta = _decimal_delta(
        event.current_resolution_disagreement_score,
        event.previous_resolution_disagreement_score,
    )
    reason_codes = _row_reason_codes(
        event,
        memory_score=memory_score,
        config=config,
    )
    return EventResolutionDisagreementMemoryScorecardRow(
        event_reference=_public_reference(event.event_id),
        event_type=event.event_type,
        observed_at=event.observed_at,
        resolved_at=event.resolved_at,
        current_resolution_disagreement_score=event.current_resolution_disagreement_score,
        previous_resolution_disagreement_score=event.previous_resolution_disagreement_score,
        disagreement_memory_decay_score=event.disagreement_memory_decay_score,
        resolution_confirmation_score=event.resolution_confirmation_score,
        evidence_family_count=event.evidence_family_count,
        conflicting_family_count=event.conflicting_family_count,
        memory_score=memory_score,
        disagreement_delta=disagreement_delta,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _memory_score(
    *,
    current_resolution_disagreement_score: Decimal,
    previous_resolution_disagreement_score: Decimal,
    disagreement_memory_decay_score: Decimal,
) -> Decimal:
    retained_memory = previous_resolution_disagreement_score * (
        ONE - disagreement_memory_decay_score
    )
    return max(current_resolution_disagreement_score, retained_memory).quantize(
        DECIMAL_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _decimal_delta(current_value: Decimal, previous_value: Decimal) -> Decimal:
    return (current_value - previous_value).quantize(
        DECIMAL_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _public_reference(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def _row_reason_codes(
    event: EventResolutionDisagreementMemoryInput,
    *,
    memory_score: Decimal,
    config: EventResolutionDisagreementMemoryScorecardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if event.current_resolution_disagreement_score >= config.block_disagreement_score:
        reasons.append(BLOCK_DISAGREEMENT_REASON)
    elif event.current_resolution_disagreement_score >= config.watch_disagreement_score:
        reasons.append(WATCH_DISAGREEMENT_REASON)
    if memory_score >= config.block_memory_score:
        reasons.append(BLOCK_MEMORY_REASON)
    elif memory_score >= config.watch_memory_score:
        reasons.append(WATCH_MEMORY_REASON)
    if event.resolution_confirmation_score < config.min_resolution_confirmation_score:
        reasons.append(LOW_CONFIRMATION_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        BLOCK_DISAGREEMENT_REASON in reason_codes
        or BLOCK_MEMORY_REASON in reason_codes
        or LOW_CONFIRMATION_REASON in reason_codes
    ):
        return "block"
    if (
        WATCH_DISAGREEMENT_REASON in reason_codes
        or WATCH_MEMORY_REASON in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[EventResolutionDisagreementMemoryScorecardRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[EventResolutionDisagreementMemoryScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not found:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _row_sort_key(
    row: EventResolutionDisagreementMemoryScorecardRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.memory_score,
        -row.current_resolution_disagreement_score,
        row.event_reference,
    )


def _normalize_inputs(
    events: tuple[EventResolutionDisagreementMemoryInput, ...]
    | list[EventResolutionDisagreementMemoryInput],
) -> tuple[EventResolutionDisagreementMemoryInput, ...]:
    if type(events) not in (list, tuple):
        raise ValueError("events must be a list or tuple")
    normalized: list[EventResolutionDisagreementMemoryInput] = []
    seen_event_ids: set[str] = set()
    for event in events:
        if type(event) is not EventResolutionDisagreementMemoryInput:
            raise ValueError("event must be an EventResolutionDisagreementMemoryInput")
        _require_hard_flags("event", event)
        if event.event_id in seen_event_ids:
            raise ValueError("duplicate event_id")
        seen_event_ids.add(event.event_id)
        normalized.append(event)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[EventResolutionDisagreementMemoryScorecardRow, ...],
) -> tuple[EventResolutionDisagreementMemoryScorecardRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[EventResolutionDisagreementMemoryScorecardRow] = []
    seen_event_references: set[str] = set()
    for row in rows:
        if type(row) is not EventResolutionDisagreementMemoryScorecardRow:
            raise ValueError("row must be an EventResolutionDisagreementMemoryScorecardRow")
        _require_hard_flags("row", row)
        if row.event_reference in seen_event_references:
            raise ValueError("duplicate row event_reference")
        seen_event_references.add(row.event_reference)
        normalized.append(row)
    return tuple(normalized)


def _validate_report_consistency(
    report: EventResolutionDisagreementMemoryScorecardReport,
) -> None:
    rows = report.rows
    expected_values = {
        "event_count": _count(len(rows)),
        "pass_count": _count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": _count(sum(1 for row in rows if row.status == "watch")),
        "block_count": _count(sum(1 for row in rows if row.status == "block")),
        "max_current_resolution_disagreement_score": _max_decimal(
            row.current_resolution_disagreement_score for row in rows
        ),
        "max_memory_score": _max_decimal(row.memory_score for row in rows),
        "average_memory_score": _average_decimal(row.memory_score for row in rows),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows entries must be JSON objects")
    _reject_unknown_keys("row payload", value, ROW_PAYLOAD_KEYS)
    _require_required_keys("row payload", value, ROW_PAYLOAD_KEYS)
    _require_hard_flags("row payload", _PayloadFlags(value))
    _require_digest("event_reference", value["event_reference"])
    _require_public_identifier("event_type", value["event_type"])
    _require_datetime_payload_string("observed_at", value["observed_at"])
    _require_datetime_payload_string("resolved_at", value["resolved_at"])
    for field_name in ROW_DECIMAL_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    _require_known_value("status", value["status"], STATUSES)
    _normalize_reason_codes(
        "reason_codes",
        _require_list("reason_codes", value["reason_codes"]),
        ROW_REASON_CODES,
    )


def _derived_validation_digest(
    report: EventResolutionDisagreementMemoryScorecardReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: EventResolutionDisagreementMemoryScorecardReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _PayloadFlags:
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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_raw_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...] | list[Any],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        _require_known_value(field_name, reason_code, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        normalized = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if str(normalized.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_datetime_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: Any) -> Decimal:
    maximum = ZERO
    for value in values:
        if value > maximum:
            maximum = value
    return maximum


def _average_decimal(values: Any) -> Decimal:
    total = ZERO
    count = ZERO
    for value in values:
        total += value
        count += ONE
    if count == ZERO:
        return ZERO
    return (total / count).quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_not_after(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _reject_unknown_keys(
    label: str,
    value: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    for key in value:
        if key not in allowed_keys:
            raise ValueError(f"unsafe public payload field in {label}: {key}")


def _require_required_keys(
    label: str,
    value: dict[str, Any],
    required_keys: frozenset[str],
) -> None:
    for key in required_keys:
        if key not in value:
            raise ValueError(f"missing public field in {label}: {key}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
