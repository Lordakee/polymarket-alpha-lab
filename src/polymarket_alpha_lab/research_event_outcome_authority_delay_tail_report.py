"""Report-only reducer for event outcome authority delay tails."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_OUTCOME_AUTHORITY_DELAY_TAIL_CONFIG_VERSION = (
    "research-event-outcome-authority-delay-tail-report-v0"
)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_CODES = (
    "authority_missing",
    "authority_delay_watch",
    "authority_delay_block",
    "unresolved_tail_watch",
    "unresolved_tail_block",
)
_REPORT_REASON_CODES = (
    "event_outcome_authority_delay_tail_empty",
    "event_outcome_authority_delay_tail_clear",
    "authority_missing_present",
    "authority_delay_watch_present",
    "authority_delay_block_present",
    "unresolved_tail_watch_present",
    "unresolved_tail_block_present",
)


def _term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "candidate_id",
        "raw_candidate_id",
        "market",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "live",
        "network",
        _term("au", "th_token"),
        _term("authori", "zation"),
        _term("bear", "er"),
    ),
)

_REPORT_DECIMAL_FIELDS = (
    "event_count",
    "tail_event_count",
    "authority_missing_count",
    "authority_delay_watch_count",
    "authority_delay_block_count",
    "unresolved_tail_watch_count",
    "unresolved_tail_block_count",
    "max_authority_delay_seconds",
    "max_unresolved_tail_probability",
)
_ROW_DECIMAL_FIELDS = (
    "row_sequence",
    "authority_delay_seconds",
    "unresolved_tail_probability",
    "flag_count",
)
_ROW_BOOL_FIELDS = (
    "authority_available",
    "authority_missing",
    "authority_delay_watch",
    "authority_delay_block",
    "unresolved_tail_watch",
    "unresolved_tail_block",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *_REPORT_DECIMAL_FIELDS,
    "status",
    "reason_codes",
    "tail_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "row_sequence",
    "status",
    "authority_delay_seconds",
    "unresolved_tail_probability",
    *_ROW_BOOL_FIELDS,
    "flag_count",
    "reason_codes",
)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityDelayTailConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_OUTCOME_AUTHORITY_DELAY_TAIL_CONFIG_VERSION
    watch_authority_delay_seconds_threshold: Decimal = Decimal("86400.000000")
    block_authority_delay_seconds_threshold: Decimal = Decimal("604800.000000")
    watch_unresolved_tail_probability_threshold: Decimal = Decimal("0.050000")
    block_unresolved_tail_probability_threshold: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityDelayTailConfig:
            raise ValueError("config must be exact")
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_OUTCOME_AUTHORITY_DELAY_TAIL_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_authority_delay_seconds_threshold",
            "block_authority_delay_seconds_threshold",
        ):
            normalized = _normalize_positive_decimal(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, normalized)
        for field_name in (
            "watch_unresolved_tail_probability_threshold",
            "block_unresolved_tail_probability_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.block_authority_delay_seconds_threshold
            < self.watch_authority_delay_seconds_threshold
        ):
            raise ValueError("block authority delay threshold must be at least watch threshold")
        if (
            self.block_unresolved_tail_probability_threshold
            < self.watch_unresolved_tail_probability_threshold
        ):
            raise ValueError("block unresolved tail threshold must be at least watch threshold")
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityDelayTailInput:
    event_reference: str
    event_ended_at: datetime
    authority_last_checked_at: datetime
    outcome_authority_available: bool
    unresolved_tail_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityDelayTailInput:
            raise ValueError("input must be exact")
        _require_private_text("event_reference", self.event_reference)
        object.__setattr__(self, "event_ended_at", _as_utc("event_ended_at", self.event_ended_at))
        object.__setattr__(
            self,
            "authority_last_checked_at",
            _as_utc("authority_last_checked_at", self.authority_last_checked_at),
        )
        if type(self.outcome_authority_available) is not bool:
            raise ValueError("outcome_authority_available must be a bool")
        object.__setattr__(
            self,
            "unresolved_tail_probability",
            _normalize_ratio(
                "unresolved_tail_probability",
                self.unresolved_tail_probability,
            ),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityDelayTailRow:
    row_sequence: Decimal
    status: str
    authority_delay_seconds: Decimal
    unresolved_tail_probability: Decimal
    authority_available: bool
    authority_missing: bool
    authority_delay_watch: bool
    authority_delay_block: bool
    unresolved_tail_watch: bool
    unresolved_tail_block: bool
    flag_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityDelayTailRow:
            raise ValueError("row must be exact")
        object.__setattr__(self, "row_sequence", _normalize_positive_decimal("row_sequence", self.row_sequence))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "authority_delay_seconds",
            _normalize_nonnegative_decimal(
                "authority_delay_seconds",
                self.authority_delay_seconds,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_tail_probability",
            _normalize_ratio("unresolved_tail_probability", self.unresolved_tail_probability),
        )
        for field_name in (
            "authority_available",
            "authority_missing",
            "authority_delay_watch",
            "authority_delay_block",
            "unresolved_tail_watch",
            "unresolved_tail_block",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(self, "flag_count", _normalize_nonnegative_decimal("flag_count", self.flag_count))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _require_flags("row", self)
        _check_row(self)


@dataclass(frozen=True)
class ResearchEventOutcomeAuthorityDelayTailReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    tail_event_count: Decimal
    authority_missing_count: Decimal
    authority_delay_watch_count: Decimal
    authority_delay_block_count: Decimal
    unresolved_tail_watch_count: Decimal
    unresolved_tail_block_count: Decimal
    max_authority_delay_seconds: Decimal
    max_unresolved_tail_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    tail_rows: tuple[ResearchEventOutcomeAuthorityDelayTailRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeAuthorityDelayTailReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_OUTCOME_AUTHORITY_DELAY_TAIL_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in _REPORT_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        object.__setattr__(self, "tail_rows", _normalize_rows(self.tail_rows))
        _require_flags("report", self)
        _check_report(self)
        _reject_unsafe_public("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_event_outcome_authority_delay_tail_report(
    events: object,
    *,
    config: ResearchEventOutcomeAuthorityDelayTailConfig,
    generated_at: datetime,
) -> ResearchEventOutcomeAuthorityDelayTailReport:
    if type(config) is not ResearchEventOutcomeAuthorityDelayTailConfig:
        raise ValueError("config must be a ResearchEventOutcomeAuthorityDelayTailConfig")
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events, generated_at)
    row_inputs = tuple(
        sorted(
            (
                candidate
                for candidate in (
                    _tail_candidate(
                        index,
                        item,
                        config=config,
                        generated_at=generated_at,
                    )
                    for index, item in enumerate(normalized_events)
                )
                if candidate["flag_count"] > _ZERO
            ),
            key=_candidate_sort_key,
        ),
    )
    tail_rows = tuple(
        _row_from_candidate(sequence, candidate)
        for sequence, candidate in enumerate(row_inputs, start=1)
    )
    return ResearchEventOutcomeAuthorityDelayTailReport(
        generated_at=generated_at,
        config_version=config.config_version,
        event_count=_count(len(normalized_events)),
        tail_event_count=_count(len(tail_rows)),
        authority_missing_count=_flag_total(tail_rows, "authority_missing"),
        authority_delay_watch_count=_flag_total(tail_rows, "authority_delay_watch"),
        authority_delay_block_count=_flag_total(tail_rows, "authority_delay_block"),
        unresolved_tail_watch_count=_flag_total(tail_rows, "unresolved_tail_watch"),
        unresolved_tail_block_count=_flag_total(tail_rows, "unresolved_tail_block"),
        max_authority_delay_seconds=_max_decimal(
            row.authority_delay_seconds for row in tail_rows
        ),
        max_unresolved_tail_probability=_max_decimal(
            row.unresolved_tail_probability for row in tail_rows
        ),
        status=_report_status(tail_rows),
        reason_codes=_report_reason_codes(tail_rows, len(normalized_events)),
        tail_rows=tail_rows,
    )


def research_event_outcome_authority_delay_tail_payload(
    report: ResearchEventOutcomeAuthorityDelayTailReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventOutcomeAuthorityDelayTailReport:
        _require_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchEventOutcomeAuthorityDelayTailReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_flags("payload", _PayloadFlags(payload))
    _reject_flag_downgrades("payload", payload)
    _validate_public_payload(payload)
    _reject_unsafe_public("payload", payload)
    return payload


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


def _normalize_events(
    events: object,
    generated_at: datetime,
) -> tuple[ResearchEventOutcomeAuthorityDelayTailInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        items = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchEventOutcomeAuthorityDelayTailInput:
            raise ValueError(
                "events must contain ResearchEventOutcomeAuthorityDelayTailInput",
            )
        _require_flags("input", item)
        if item.event_reference in seen:
            raise ValueError("duplicate event_reference values are not allowed")
        if item.event_ended_at > generated_at:
            raise ValueError("event_ended_at must not be after generated_at")
        if item.authority_last_checked_at > generated_at:
            raise ValueError("authority_last_checked_at must not be after generated_at")
        if item.authority_last_checked_at < item.event_ended_at:
            raise ValueError("authority_last_checked_at must not precede event_ended_at")
        seen.add(item.event_reference)
    return items


def _tail_candidate(
    index: int,
    item: ResearchEventOutcomeAuthorityDelayTailInput,
    *,
    config: ResearchEventOutcomeAuthorityDelayTailConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    authority_reference_at = (
        item.authority_last_checked_at if item.outcome_authority_available else generated_at
    )
    authority_delay_seconds = _duration_seconds(item.event_ended_at, authority_reference_at)
    authority_missing = not item.outcome_authority_available
    authority_delay_block = (
        authority_delay_seconds >= config.block_authority_delay_seconds_threshold
    )
    authority_delay_watch = (
        not authority_delay_block
        and authority_delay_seconds >= config.watch_authority_delay_seconds_threshold
    )
    unresolved_tail_block = (
        item.unresolved_tail_probability
        >= config.block_unresolved_tail_probability_threshold
    )
    unresolved_tail_watch = (
        not unresolved_tail_block
        and item.unresolved_tail_probability
        >= config.watch_unresolved_tail_probability_threshold
    )
    flag_count = _count(
        sum(
            1
            for flag in (
                authority_missing,
                authority_delay_watch,
                authority_delay_block,
                unresolved_tail_watch,
                unresolved_tail_block,
            )
            if flag
        ),
    )
    return {
        "index": index,
        "status": _row_status(
            authority_missing=authority_missing,
            authority_delay_watch=authority_delay_watch,
            authority_delay_block=authority_delay_block,
            unresolved_tail_watch=unresolved_tail_watch,
            unresolved_tail_block=unresolved_tail_block,
        ),
        "authority_delay_seconds": authority_delay_seconds,
        "unresolved_tail_probability": item.unresolved_tail_probability,
        "authority_available": item.outcome_authority_available,
        "authority_missing": authority_missing,
        "authority_delay_watch": authority_delay_watch,
        "authority_delay_block": authority_delay_block,
        "unresolved_tail_watch": unresolved_tail_watch,
        "unresolved_tail_block": unresolved_tail_block,
        "flag_count": flag_count,
        "reason_codes": _row_reason_codes(
            authority_missing=authority_missing,
            authority_delay_watch=authority_delay_watch,
            authority_delay_block=authority_delay_block,
            unresolved_tail_watch=unresolved_tail_watch,
            unresolved_tail_block=unresolved_tail_block,
        ),
    }


def _row_from_candidate(
    sequence: int,
    candidate: dict[str, Any],
) -> ResearchEventOutcomeAuthorityDelayTailRow:
    return ResearchEventOutcomeAuthorityDelayTailRow(
        row_sequence=_count(sequence),
        status=candidate["status"],
        authority_delay_seconds=candidate["authority_delay_seconds"],
        unresolved_tail_probability=candidate["unresolved_tail_probability"],
        authority_available=candidate["authority_available"],
        authority_missing=candidate["authority_missing"],
        authority_delay_watch=candidate["authority_delay_watch"],
        authority_delay_block=candidate["authority_delay_block"],
        unresolved_tail_watch=candidate["unresolved_tail_watch"],
        unresolved_tail_block=candidate["unresolved_tail_block"],
        flag_count=candidate["flag_count"],
        reason_codes=candidate["reason_codes"],
    )


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, Decimal, Decimal, Decimal, int]:
    return (
        _STATUS_RANK[candidate["status"]],
        -candidate["flag_count"],
        -candidate["authority_delay_seconds"],
        -candidate["unresolved_tail_probability"],
        candidate["index"],
    )


def _row_sort_key(
    row: ResearchEventOutcomeAuthorityDelayTailRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal]:
    return (
        _STATUS_RANK[row.status],
        -row.flag_count,
        -row.authority_delay_seconds,
        -row.unresolved_tail_probability,
        row.row_sequence,
    )


def _row_status(
    *,
    authority_missing: bool,
    authority_delay_watch: bool,
    authority_delay_block: bool,
    unresolved_tail_watch: bool,
    unresolved_tail_block: bool,
) -> str:
    if authority_missing or authority_delay_block or unresolved_tail_block:
        return "block"
    if authority_delay_watch or unresolved_tail_watch:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    authority_missing: bool,
    authority_delay_watch: bool,
    authority_delay_block: bool,
    unresolved_tail_watch: bool,
    unresolved_tail_block: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if authority_missing:
        reason_codes.append("authority_missing")
    if authority_delay_watch:
        reason_codes.append("authority_delay_watch")
    if authority_delay_block:
        reason_codes.append("authority_delay_block")
    if unresolved_tail_watch:
        reason_codes.append("unresolved_tail_watch")
    if unresolved_tail_block:
        reason_codes.append("unresolved_tail_block")
    return tuple(reason_codes)


def _report_status(rows: tuple[ResearchEventOutcomeAuthorityDelayTailRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventOutcomeAuthorityDelayTailRow, ...],
    event_count: int,
) -> tuple[str, ...]:
    if event_count == 0:
        return ("event_outcome_authority_delay_tail_empty",)
    if not rows:
        return ("event_outcome_authority_delay_tail_clear",)
    reason_codes: list[str] = []
    if any(row.authority_missing for row in rows):
        reason_codes.append("authority_missing_present")
    if any(row.authority_delay_watch for row in rows):
        reason_codes.append("authority_delay_watch_present")
    if any(row.authority_delay_block for row in rows):
        reason_codes.append("authority_delay_block_present")
    if any(row.unresolved_tail_watch for row in rows):
        reason_codes.append("unresolved_tail_watch_present")
    if any(row.unresolved_tail_block for row in rows):
        reason_codes.append("unresolved_tail_block_present")
    return tuple(reason_codes)


def _check_row(row: ResearchEventOutcomeAuthorityDelayTailRow) -> None:
    expected_missing = not row.authority_available
    if row.authority_missing is not expected_missing:
        raise ValueError("authority_missing must match authority_available")
    expected_flag_count = _count(
        sum(
            1
            for flag in (
                row.authority_missing,
                row.authority_delay_watch,
                row.authority_delay_block,
                row.unresolved_tail_watch,
                row.unresolved_tail_block,
            )
            if flag
        ),
    )
    if row.flag_count != expected_flag_count:
        raise ValueError("flag_count must match row flags")
    if row.flag_count == _ZERO:
        raise ValueError("tail row must contain at least one flag")
    expected_status = _row_status(
        authority_missing=row.authority_missing,
        authority_delay_watch=row.authority_delay_watch,
        authority_delay_block=row.authority_delay_block,
        unresolved_tail_watch=row.unresolved_tail_watch,
        unresolved_tail_block=row.unresolved_tail_block,
    )
    if row.status != expected_status:
        raise ValueError("status must match row flags")
    expected_reasons = _row_reason_codes(
        authority_missing=row.authority_missing,
        authority_delay_watch=row.authority_delay_watch,
        authority_delay_block=row.authority_delay_block,
        unresolved_tail_watch=row.unresolved_tail_watch,
        unresolved_tail_block=row.unresolved_tail_block,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row flags")


def _check_report(report: ResearchEventOutcomeAuthorityDelayTailReport) -> None:
    rows = report.tail_rows
    if report.event_count < report.tail_event_count:
        raise ValueError("tail_event_count must not exceed event_count")
    if report.tail_event_count != _count(len(rows)):
        raise ValueError("tail_event_count must match tail_rows")
    for field_name, flag_name in (
        ("authority_missing_count", "authority_missing"),
        ("authority_delay_watch_count", "authority_delay_watch"),
        ("authority_delay_block_count", "authority_delay_block"),
        ("unresolved_tail_watch_count", "unresolved_tail_watch"),
        ("unresolved_tail_block_count", "unresolved_tail_block"),
    ):
        if getattr(report, field_name) != _flag_total(rows, flag_name):
            raise ValueError(f"{field_name} must match tail_rows")
    if report.max_authority_delay_seconds != _max_decimal(
        row.authority_delay_seconds for row in rows
    ):
        raise ValueError("max_authority_delay_seconds must match tail_rows")
    if report.max_unresolved_tail_probability != _max_decimal(
        row.unresolved_tail_probability for row in rows
    ):
        raise ValueError("max_unresolved_tail_probability must match tail_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match tail_rows")
    if report.reason_codes != _report_reason_codes(rows, int(report.event_count)):
        raise ValueError("reason_codes must match tail_rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("tail_rows must use deterministic sequence")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventOutcomeAuthorityDelayTailRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("tail_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("tail_rows must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchEventOutcomeAuthorityDelayTailRow:
            raise ValueError(
                "tail_rows must contain ResearchEventOutcomeAuthorityDelayTailRow",
            )
        _require_flags("row", item)
    return items


def _flag_total(
    rows: tuple[ResearchEventOutcomeAuthorityDelayTailRow, ...],
    flag_name: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, flag_name)))


def _max_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at < started_at:
        raise ValueError("finished_at must not precede started_at")
    delta = finished_at - started_at
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + fractional_seconds)


def _report_digest(report: ResearchEventOutcomeAuthorityDelayTailReport) -> str:
    payload = asdict(report)
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_public_text("generated_at", payload["generated_at"])
    _require_public_text("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_RESEARCH_EVENT_OUTCOME_AUTHORITY_DELAY_TAIL_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in _REPORT_DECIMAL_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _normalize_reason_codes("reason_codes", payload["reason_codes"], _REPORT_REASON_CODES)
    if type(payload["tail_rows"]) is not list:
        raise ValueError("tail_rows must be a list")
    for row in payload["tail_rows"]:
        _validate_public_row_payload(row)
    _verify_payload_digest(payload)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("tail_rows must contain JSON objects")
    _reject_unknown_payload_keys("tail row payload", value, _ROW_PAYLOAD_KEYS)
    _require_status("status", value["status"])
    for field_name in _ROW_DECIMAL_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in _ROW_BOOL_FIELDS:
        if type(value[field_name]) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_reason_codes("reason_codes", value["reason_codes"], _ROW_REASON_CODES)


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if set(payload.keys()) != set(allowed_keys):
        raise ValueError(f"{label} must use the public readonly schema")


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


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
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
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
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


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return _quantize(Decimal(value))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _require_private_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe public value in {name}")


def _require_status(name: str, value: object) -> None:
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _normalize_reason_codes(
    name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{name} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{name} must not contain duplicates")
    for item in items:
        _require_public_text(name, item)
        if item not in allowed:
            raise ValueError(f"{name} must contain known values")
    if tuple(reason for reason in allowed if reason in items) != items:
        raise ValueError(f"{name} must use deterministic order")
    return items


def _require_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    if str(_quantize(decimal_value)) != value:
        raise ValueError(f"{name} must use canonical Decimal-derived string values")
    return decimal_value


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_OUTCOME_AUTHORITY_DELAY_TAIL_CONFIG_VERSION",
    "ResearchEventOutcomeAuthorityDelayTailConfig",
    "ResearchEventOutcomeAuthorityDelayTailInput",
    "ResearchEventOutcomeAuthorityDelayTailReport",
    "ResearchEventOutcomeAuthorityDelayTailRow",
    "build_research_event_outcome_authority_delay_tail_report",
    "research_event_outcome_authority_delay_tail_payload",
)
