"""Report-only external catalyst calendar for event research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any, Mapping, Sequence

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EXTERNAL_CATALYST_CALENDAR_CONFIG_VERSION = (
    "research-external-catalyst-calendar-report-v0"
)

EVENT_TYPES = (
    "publication_time",
    "data_event",
    "sports_node",
    "policy_node",
    "settlement_window",
)
STATUSES = ("pass", "watch", "block")

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_MINUTE = Decimal("60")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_TEXT_MAX_LENGTH = 256
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw",
    "source_url",
    "sourceurl",
    "url",
    "source_text",
    "sourcetext",
    "market_question",
    "marketquestion",
    "dsn",
    "table",
    "token",
    "auth",
    "account",
    "balance",
    "order",
    "trade",
    "private",
    "secret",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "raw source",
    "raw-source",
    "market question",
    "will this market",
    "dsn",
    "private",
    "secret",
)


@dataclass(frozen=True)
class ResearchExternalCatalystCalendarConfig:
    config_version: str = DEFAULT_RESEARCH_EXTERNAL_CATALYST_CALENDAR_CONFIG_VERSION
    min_pass_source_count: Decimal = Decimal("2.000000")
    min_watch_source_count: Decimal = Decimal("1.000000")
    min_pass_source_family_count: Decimal = Decimal("2.000000")
    min_watch_source_family_count: Decimal = Decimal("1.000000")
    min_pass_confidence_score: Decimal = Decimal("0.700000")
    min_watch_confidence_score: Decimal = Decimal("0.450000")
    max_publication_lead_minutes: Decimal = Decimal("10080.000000")
    max_data_event_lead_minutes: Decimal = Decimal("43200.000000")
    max_sports_node_lead_minutes: Decimal = Decimal("43200.000000")
    max_policy_node_lead_minutes: Decimal = Decimal("129600.000000")
    max_settlement_window_lead_minutes: Decimal = Decimal("43200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchExternalCatalystCalendarConfig:
            raise TypeError(
                "ResearchExternalCatalystCalendarConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchExternalCatalystCalendarConfig)
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EXTERNAL_CATALYST_CALENDAR_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_source_count",
            "min_watch_source_count",
            "min_pass_source_family_count",
            "min_watch_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_confidence_score",
            "min_watch_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_publication_lead_minutes",
            "max_data_event_lead_minutes",
            "max_sports_node_lead_minutes",
            "max_policy_node_lead_minutes",
            "max_settlement_window_lead_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchExternalCatalystCalendarEvent:
    event_id: str
    event_type: str
    event_label: str
    scheduled_at: datetime
    source_count: Decimal
    source_family_count: Decimal
    confidence_score: Decimal
    settlement_window_start_at: datetime | None = None
    settlement_window_end_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchExternalCatalystCalendarEvent:
            raise TypeError(
                "ResearchExternalCatalystCalendarEvent does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("event", self, ResearchExternalCatalystCalendarEvent)
        _require_public_identifier("event_id", self.event_id)
        _require_member("event_type", self.event_type, EVENT_TYPES)
        object.__setattr__(
            self,
            "event_label",
            _require_public_text("event_label", self.event_label),
        )
        object.__setattr__(self, "scheduled_at", _as_utc("scheduled_at", self.scheduled_at))
        for field_name in ("source_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _probability_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "settlement_window_start_at",
            _optional_utc("settlement_window_start_at", self.settlement_window_start_at),
        )
        object.__setattr__(
            self,
            "settlement_window_end_at",
            _optional_utc("settlement_window_end_at", self.settlement_window_end_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_event_shape(self)
        _require_hard_flags("event", self)
        _reject_unsafe_public_payload("event", self)


@dataclass(frozen=True)
class ResearchExternalCatalystCalendarPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchExternalCatalystCalendarPublicPayloadItem:
            raise TypeError(
                "ResearchExternalCatalystCalendarPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "public_payload",
            self,
            ResearchExternalCatalystCalendarPublicPayloadItem,
        )
        object.__setattr__(
            self,
            "key",
            _require_public_identifier("public_payload.key", self.key),
        )
        object.__setattr__(
            self,
            "value",
            _require_public_text("public_payload.value", self.value),
        )
        _require_hard_flags("public_payload", self)
        _reject_unsafe_public_payload("public_payload", self)


@dataclass(frozen=True)
class ResearchExternalCatalystCalendarRow:
    event_id: str
    event_type: str
    event_label: str
    scheduled_at: datetime
    source_count: Decimal
    source_family_count: Decimal
    confidence_score: Decimal
    lead_time_minutes: Decimal
    settlement_window_start_at: datetime | None
    settlement_window_end_at: datetime | None
    settlement_window_minutes: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchExternalCatalystCalendarRow:
            raise TypeError(
                "ResearchExternalCatalystCalendarRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchExternalCatalystCalendarRow)
        _require_public_identifier("event_id", self.event_id)
        _require_member("event_type", self.event_type, EVENT_TYPES)
        object.__setattr__(
            self,
            "event_label",
            _require_public_text("event_label", self.event_label),
        )
        object.__setattr__(self, "scheduled_at", _as_utc("scheduled_at", self.scheduled_at))
        for field_name in ("source_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _probability_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "lead_time_minutes",
            _nonnegative_decimal("lead_time_minutes", self.lead_time_minutes),
        )
        object.__setattr__(
            self,
            "settlement_window_start_at",
            _optional_utc("settlement_window_start_at", self.settlement_window_start_at),
        )
        object.__setattr__(
            self,
            "settlement_window_end_at",
            _optional_utc("settlement_window_end_at", self.settlement_window_end_at),
        )
        object.__setattr__(
            self,
            "settlement_window_minutes",
            _optional_nonnegative_decimal(
                "settlement_window_minutes",
                self.settlement_window_minutes,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_shape(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchExternalCatalystCalendarReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    covered_event_type_count: Decimal
    missing_event_type_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_event_types: tuple[str, ...]
    rows: tuple[ResearchExternalCatalystCalendarRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchExternalCatalystCalendarPublicPayloadItem, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchExternalCatalystCalendarReport:
            raise TypeError(
                "ResearchExternalCatalystCalendarReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchExternalCatalystCalendarReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EXTERNAL_CATALYST_CALENDAR_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "event_count",
            "covered_event_type_count",
            "missing_event_type_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_event_types",
            _normalize_event_types("missing_event_types", self.missing_event_types),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_shape(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_external_catalyst_calendar_report_payload(self)


def build_research_external_catalyst_calendar_report(
    events: Sequence[ResearchExternalCatalystCalendarEvent],
    *,
    generated_at: datetime,
    config: ResearchExternalCatalystCalendarConfig | None = None,
    public_payload: Sequence[ResearchExternalCatalystCalendarPublicPayloadItem] = (),
) -> ResearchExternalCatalystCalendarReport:
    if config is None:
        config = ResearchExternalCatalystCalendarConfig()
    _require_exact_type("config", config, ResearchExternalCatalystCalendarConfig)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events)
    payload_items = _normalize_public_payload(public_payload)
    rows = tuple(_row_from_event(item, generated_at, config) for item in normalized_events)
    missing_event_types = _missing_event_types(rows)
    status = _report_status(rows, missing_event_types)
    return ResearchExternalCatalystCalendarReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        event_count=_decimal_count(len(rows)),
        covered_event_type_count=_decimal_count(len({row.event_type for row in rows})),
        missing_event_type_count=_decimal_count(len(missing_event_types)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "block")),
        missing_event_types=missing_event_types,
        rows=rows,
        reason_codes=_report_reason_codes(
            rows,
            missing_event_types=missing_event_types,
            status=status,
        ),
        public_payload=payload_items,
    )


def research_external_catalyst_calendar_report_payload(
    report: ResearchExternalCatalystCalendarReport,
) -> dict[str, Any]:
    _require_exact_type("report", report, ResearchExternalCatalystCalendarReport)
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = json_ready_no_floats(asdict(report))
    _reject_unsafe_json_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_event(
    event: ResearchExternalCatalystCalendarEvent,
    generated_at: datetime,
    config: ResearchExternalCatalystCalendarConfig,
) -> ResearchExternalCatalystCalendarRow:
    scheduled_before_generated = event.scheduled_at < generated_at
    lead_time = (
        _ZERO
        if scheduled_before_generated
        else _minutes_between(generated_at, event.scheduled_at)
    )
    settlement_window_minutes = None
    if event.event_type == "settlement_window":
        if event.settlement_window_start_at is None or event.settlement_window_end_at is None:
            raise ValueError("settlement_window rows require settlement bounds")
        settlement_window_minutes = _minutes_between(
            event.settlement_window_start_at,
            event.settlement_window_end_at,
        )
    reason_codes = _row_reason_codes(
        event,
        lead_time=lead_time,
        scheduled_before_generated=scheduled_before_generated,
        config=config,
    )
    return ResearchExternalCatalystCalendarRow(
        event_id=event.event_id,
        event_type=event.event_type,
        event_label=event.event_label,
        scheduled_at=event.scheduled_at,
        source_count=event.source_count,
        source_family_count=event.source_family_count,
        confidence_score=event.confidence_score,
        lead_time_minutes=lead_time,
        settlement_window_start_at=event.settlement_window_start_at,
        settlement_window_end_at=event.settlement_window_end_at,
        settlement_window_minutes=settlement_window_minutes,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    event: ResearchExternalCatalystCalendarEvent,
    *,
    lead_time: Decimal,
    scheduled_before_generated: bool,
    config: ResearchExternalCatalystCalendarConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if scheduled_before_generated:
        block_reasons.append("event_time_before_generated_at")
    if event.source_count == _ZERO:
        block_reasons.append("no_source_confirmation")
    if event.source_family_count == _ZERO:
        block_reasons.append("no_source_family_confirmation")
    if event.confidence_score < config.min_watch_confidence_score:
        block_reasons.append("confidence_below_watch_threshold")
    if lead_time > _max_lead_minutes(event.event_type, config):
        block_reasons.append(f"{event.event_type}_lead_time_too_long")
    if event.source_count < config.min_watch_source_count:
        block_reasons.append("source_count_below_watch_threshold")
    elif event.source_count < config.min_pass_source_count:
        watch_reasons.append("low_source_confirmation")
    if event.source_family_count < config.min_watch_source_family_count:
        block_reasons.append("source_family_count_below_watch_threshold")
    elif event.source_family_count < config.min_pass_source_family_count:
        watch_reasons.append("single_source_family_confirmation")
    if not watch_reasons and event.confidence_score < config.min_pass_confidence_score:
        watch_reasons.append("low_confidence_score")
    return _normalize_reason_codes(
        "reason_codes",
        (*block_reasons, *watch_reasons, *event.reason_codes),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(_is_block_reason(reason_code) for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _is_block_reason(reason_code: str) -> bool:
    return reason_code in {
        "event_time_before_generated_at",
        "no_source_confirmation",
        "no_source_family_confirmation",
        "confidence_below_watch_threshold",
        "source_count_below_watch_threshold",
        "source_family_count_below_watch_threshold",
    } or reason_code.endswith("_lead_time_too_long")


def _max_lead_minutes(
    event_type: str,
    config: ResearchExternalCatalystCalendarConfig,
) -> Decimal:
    if event_type == "publication_time":
        return config.max_publication_lead_minutes
    if event_type == "data_event":
        return config.max_data_event_lead_minutes
    if event_type == "sports_node":
        return config.max_sports_node_lead_minutes
    if event_type == "policy_node":
        return config.max_policy_node_lead_minutes
    if event_type == "settlement_window":
        return config.max_settlement_window_lead_minutes
    raise ValueError("event_type must be supported")


def _missing_event_types(
    rows: tuple[ResearchExternalCatalystCalendarRow, ...],
) -> tuple[str, ...]:
    covered = {row.event_type for row in rows}
    return tuple(sorted(event_type for event_type in EVENT_TYPES if event_type not in covered))


def _report_status(
    rows: tuple[ResearchExternalCatalystCalendarRow, ...],
    missing_event_types: tuple[str, ...],
) -> str:
    if missing_event_types:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchExternalCatalystCalendarRow, ...],
    *,
    missing_event_types: tuple[str, ...],
    status: str,
) -> tuple[str, ...]:
    if status == "pass":
        return ("external_catalyst_calendar_pass",)
    reason_codes: list[str] = []
    if missing_event_types:
        reason_codes.append("external_catalyst_calendar_missing_required_types")
        reason_codes.extend(f"missing_{event_type}" for event_type in missing_event_types)
    if any(row.status == "block" for row in rows):
        reason_codes.append("external_catalyst_calendar_blocked_rows")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("external_catalyst_calendar_watch_rows")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchExternalCatalystCalendarRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_config(config: ResearchExternalCatalystCalendarConfig) -> None:
    if config.min_watch_source_count > config.min_pass_source_count:
        raise ValueError("min_watch_source_count must not exceed min_pass_source_count")
    if config.min_watch_source_family_count > config.min_pass_source_family_count:
        raise ValueError(
            "min_watch_source_family_count must not exceed min_pass_source_family_count",
        )
    if config.min_watch_confidence_score > config.min_pass_confidence_score:
        raise ValueError(
            "min_watch_confidence_score must not exceed min_pass_confidence_score",
        )


def _validate_event_shape(event: ResearchExternalCatalystCalendarEvent) -> None:
    if event.source_family_count > event.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if event.event_type == "settlement_window":
        if event.settlement_window_start_at is None:
            raise ValueError("settlement_window_start_at is required")
        if event.settlement_window_end_at is None:
            raise ValueError("settlement_window_end_at is required")
        if event.settlement_window_end_at < event.settlement_window_start_at:
            raise ValueError(
                "settlement_window_end_at must not be before settlement_window_start_at",
            )
        return
    if event.settlement_window_start_at is not None:
        raise ValueError("settlement_window_start_at is only for settlement_window")
    if event.settlement_window_end_at is not None:
        raise ValueError("settlement_window_end_at is only for settlement_window")


def _validate_row_shape(row: ResearchExternalCatalystCalendarRow) -> None:
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if row.event_type == "settlement_window":
        if row.settlement_window_start_at is None:
            raise ValueError("settlement_window_start_at is required")
        if row.settlement_window_end_at is None:
            raise ValueError("settlement_window_end_at is required")
        if row.settlement_window_minutes is None:
            raise ValueError("settlement_window_minutes is required")
    else:
        if row.settlement_window_start_at is not None:
            raise ValueError("settlement_window_start_at is only for settlement_window")
        if row.settlement_window_end_at is not None:
            raise ValueError("settlement_window_end_at is only for settlement_window")
        if row.settlement_window_minutes is not None:
            raise ValueError("settlement_window_minutes is only for settlement_window")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report_shape(report: ResearchExternalCatalystCalendarReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.covered_event_type_count != _decimal_count(
        len({row.event_type for row in report.rows}),
    ):
        raise ValueError("covered_event_type_count must match rows")
    if report.missing_event_types != _missing_event_types(report.rows):
        raise ValueError("missing_event_types must match rows")
    if report.missing_event_type_count != _decimal_count(len(report.missing_event_types)):
        raise ValueError("missing_event_type_count must match missing_event_types")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("blocked_count must match rows")
    expected_status = _report_status(report.rows, report.missing_event_types)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(
        report.rows,
        missing_event_types=report.missing_event_types,
        status=report.status,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _normalize_events(
    events: Sequence[ResearchExternalCatalystCalendarEvent],
) -> tuple[ResearchExternalCatalystCalendarEvent, ...]:
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise ValueError("events must be a sequence")
    normalized: list[ResearchExternalCatalystCalendarEvent] = []
    for event in events:
        _require_exact_type("event", event, ResearchExternalCatalystCalendarEvent)
        normalized.append(event)
    return tuple(
        sorted(
            normalized,
            key=lambda event: (event.event_type, event.scheduled_at, event.event_id),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchExternalCatalystCalendarRow],
) -> tuple[ResearchExternalCatalystCalendarRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchExternalCatalystCalendarRow] = []
    for row in rows:
        _require_exact_type("row", row, ResearchExternalCatalystCalendarRow)
        normalized.append(row)
    return tuple(
        sorted(normalized, key=lambda row: (row.event_type, row.scheduled_at, row.event_id)),
    )


def _normalize_public_payload(
    public_payload: Sequence[ResearchExternalCatalystCalendarPublicPayloadItem],
) -> tuple[ResearchExternalCatalystCalendarPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchExternalCatalystCalendarPublicPayloadItem] = []
    for item in public_payload:
        _require_exact_type(
            "public_payload",
            item,
            ResearchExternalCatalystCalendarPublicPayloadItem,
        )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_event_types(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        _require_member(name, value, EVENT_TYPES)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier(name, value)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    reject_unsafe_surface_fields(label, value)


def _require_public_identifier(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_unsafe_public_key(name, value)
    return value


def _require_public_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be nonempty public text")
    if len(value) > _PUBLIC_TEXT_MAX_LENGTH:
        raise ValueError(f"{name} must not exceed {_PUBLIC_TEXT_MAX_LENGTH} characters")
    lowered = value.lower()
    if "?" in value or any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public value")
    return value


def _reject_unsafe_public_key(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path} has unsafe public field")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(current_path, field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(current_path, key)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_json_payload(payload: object) -> None:
    _reject_unsafe_public_payload(
        "ResearchExternalCatalystCalendarReport.payload",
        payload,
        allow_json_containers=True,
    )


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


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _positive_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_decimal(name, value)


def _nonnegative_integer_decimal(name: str, value: object) -> Decimal:
    decimal = _nonnegative_decimal(name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be an integer Decimal")
    return decimal


def _probability_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < _ZERO or decimal > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(_QUANTUM)


def _minutes_between(start: datetime, end: datetime) -> Decimal:
    start = _as_utc("start", start)
    end = _as_utc("end", end)
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return _quantize((seconds + microseconds) / _SECONDS_PER_MINUTE)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANTUM, rounding=ROUND_HALF_UP)


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined_values = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of: {joined_values}")


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_RESEARCH_EXTERNAL_CATALYST_CALENDAR_CONFIG_VERSION",
    "ResearchExternalCatalystCalendarConfig",
    "ResearchExternalCatalystCalendarEvent",
    "ResearchExternalCatalystCalendarPublicPayloadItem",
    "ResearchExternalCatalystCalendarReport",
    "ResearchExternalCatalystCalendarRow",
    "build_research_external_catalyst_calendar_report",
    "research_external_catalyst_calendar_report_payload",
)
