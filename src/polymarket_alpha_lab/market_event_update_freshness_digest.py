"""Pure in-memory freshness digest for supplied market event update rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_MARKET_EVENT_UPDATE_FRESHNESS_CONFIG_VERSION = (
    "market-event-update-freshness-digest-v0"
)
FRESHNESS_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "no_market_event_updates",
    "missing_update_family",
    "missing_event_update_at",
    "missing_source_acknowledgement_at",
    "missing_probability_context",
    "stale_event_update_age",
    "stale_source_acknowledgement_age",
    "stale_probability_context",
    "close_time_pressure",
    "market_event_updates_fresh",
)
ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")


__all__ = (
    "DEFAULT_MARKET_EVENT_UPDATE_FRESHNESS_CONFIG_VERSION",
    "MarketEventUpdateFreshnessConfig",
    "MarketEventUpdateFreshnessEventInput",
    "MarketEventUpdateFreshnessReasonCodeCount",
    "MarketEventUpdateFreshnessReport",
    "MarketEventUpdateFreshnessRow",
    "MarketEventUpdateFreshnessStatusCount",
    "build_market_event_update_freshness_digest",
    "market_event_update_freshness_payload",
)


@dataclass(frozen=True)
class MarketEventUpdateFreshnessConfig:
    config_version: str = DEFAULT_MARKET_EVENT_UPDATE_FRESHNESS_CONFIG_VERSION
    max_event_update_age_seconds: Decimal = Decimal("3600")
    max_source_acknowledgement_age_seconds: Decimal = Decimal("7200")
    max_probability_context_age_seconds: Decimal = Decimal("1800")
    close_pressure_window_seconds: Decimal = Decimal("900")
    required_update_families: tuple[str, ...] = (
        "metadata",
        "probability",
        "resolution",
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_event_update_age_seconds",
            "max_source_acknowledgement_age_seconds",
            "max_probability_context_age_seconds",
            "close_pressure_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_update_families",
            _normalize_required_update_families(self.required_update_families),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventUpdateFreshnessEventInput:
    event_slug: str
    category: str
    update_family: str | None
    event_updated_at: datetime | None
    source_acknowledged_at: datetime | None
    probability_captured_at: datetime | None
    close_time: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_slug", self.event_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "update_family",
            _normalize_optional_canonical_string("update_family", self.update_family),
        )
        for field_name in (
            "event_updated_at",
            "source_acknowledged_at",
            "probability_captured_at",
            "close_time",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class MarketEventUpdateFreshnessRow:
    event_slug: str
    category: str
    update_family: str | None
    event_updated_at: datetime | None
    source_acknowledged_at: datetime | None
    probability_captured_at: datetime | None
    close_time: datetime | None
    event_update_age_seconds: Decimal | None
    source_acknowledgement_age_seconds: Decimal | None
    probability_context_age_seconds: Decimal | None
    close_time_pressure_seconds: Decimal | None
    close_time_pressure: bool
    missing_required_update_families: tuple[str, ...]
    freshness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_slug", self.event_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "update_family",
            _normalize_optional_canonical_string("update_family", self.update_family),
        )
        for field_name in (
            "event_updated_at",
            "source_acknowledged_at",
            "probability_captured_at",
            "close_time",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "event_update_age_seconds",
            "source_acknowledgement_age_seconds",
            "probability_context_age_seconds",
            "close_time_pressure_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if type(self.close_time_pressure) is not bool:
            raise ValueError("close_time_pressure must be a bool")
        object.__setattr__(
            self,
            "missing_required_update_families",
            _normalize_string_tuple(
                "missing_required_update_families",
                self.missing_required_update_families,
                allow_empty=True,
            ),
        )
        _require_freshness_status("freshness_status", self.freshness_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketEventUpdateFreshnessStatusCount:
    category: str
    freshness_status: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        _require_freshness_status("freshness_status", self.freshness_status)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("status_count", self)


@dataclass(frozen=True)
class MarketEventUpdateFreshnessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEventUpdateFreshnessReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    close_pressure_count: Decimal
    missing_update_family_count: Decimal
    stale_probability_context_count: Decimal
    average_event_update_age_seconds: Decimal | None
    average_source_acknowledgement_age_seconds: Decimal | None
    max_event_update_age_seconds: Decimal
    max_source_acknowledgement_age_seconds: Decimal
    max_probability_context_age_seconds: Decimal
    close_pressure_window_seconds: Decimal
    required_update_families: tuple[str, ...]
    freshness_status: str
    rows: tuple[MarketEventUpdateFreshnessRow, ...]
    category_status_counts: tuple[MarketEventUpdateFreshnessStatusCount, ...]
    reason_code_counts: tuple[MarketEventUpdateFreshnessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: tuple[tuple[str, str], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "close_pressure_count",
            "missing_update_family_count",
            "stale_probability_context_count",
            "max_event_update_age_seconds",
            "max_source_acknowledgement_age_seconds",
            "max_probability_context_age_seconds",
            "close_pressure_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_event_update_age_seconds",
            "average_source_acknowledgement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "required_update_families",
            _normalize_required_update_families(self.required_update_families),
        )
        _require_freshness_status("freshness_status", self.freshness_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "category_status_counts",
            _normalize_status_counts(self.category_status_counts),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _normalize_validation_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_market_event_update_freshness_digest(
    events: Iterable[object],
    *,
    config: MarketEventUpdateFreshnessConfig,
    generated_at: datetime,
) -> MarketEventUpdateFreshnessReport:
    if type(config) is not MarketEventUpdateFreshnessConfig:
        raise ValueError("config must be a MarketEventUpdateFreshnessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    event_inputs = _normalize_event_inputs(events)
    rows = tuple(
        sorted(
            (
                _row_from_event(event, config=config, generated_at=generated_at_utc)
                for event in event_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    category_status_counts = _category_status_counts(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    event_count = _decimal_count(len(rows))
    pass_count = _decimal_count(_row_status_count(rows, "pass"))
    watch_count = _decimal_count(_row_status_count(rows, "watch"))
    blocked_count = _decimal_count(_row_status_count(rows, "blocked"))
    close_pressure_count = _decimal_count(
        sum(1 for row in rows if row.close_time_pressure),
    )
    missing_update_family_count = _decimal_count(
        sum(1 for row in rows if "missing_update_family" in row.reason_codes),
    )
    stale_probability_context_count = _decimal_count(
        sum(1 for row in rows if "stale_probability_context" in row.reason_codes),
    )

    return MarketEventUpdateFreshnessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        close_pressure_count=close_pressure_count,
        missing_update_family_count=missing_update_family_count,
        stale_probability_context_count=stale_probability_context_count,
        average_event_update_age_seconds=_average_optional_decimal(
            row.event_update_age_seconds for row in rows
        ),
        average_source_acknowledgement_age_seconds=_average_optional_decimal(
            row.source_acknowledgement_age_seconds for row in rows
        ),
        max_event_update_age_seconds=config.max_event_update_age_seconds,
        max_source_acknowledgement_age_seconds=(
            config.max_source_acknowledgement_age_seconds
        ),
        max_probability_context_age_seconds=config.max_probability_context_age_seconds,
        close_pressure_window_seconds=config.close_pressure_window_seconds,
        required_update_families=config.required_update_families,
        freshness_status=_summary_status(reason_codes),
        rows=rows,
        category_status_counts=category_status_counts,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        derived_validation_digest=_derived_validation_digest(
            event_count=event_count,
            pass_count=pass_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
            close_pressure_count=close_pressure_count,
            rows=rows,
            category_status_counts=category_status_counts,
            reason_code_counts=reason_code_counts,
        ),
    )


def market_event_update_freshness_payload(
    report: MarketEventUpdateFreshnessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketEventUpdateFreshnessReport:
        _require_hard_flags("report", report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a MarketEventUpdateFreshnessReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_from_event(
    event: MarketEventUpdateFreshnessEventInput,
    *,
    config: MarketEventUpdateFreshnessConfig,
    generated_at: datetime,
) -> MarketEventUpdateFreshnessRow:
    _reject_future_times(event, generated_at)
    event_age = _age_seconds(generated_at, event.event_updated_at)
    source_age = _age_seconds(generated_at, event.source_acknowledged_at)
    context_age = _age_seconds(generated_at, event.probability_captured_at)
    pressure_seconds = _close_pressure_seconds(generated_at, event.close_time)
    close_pressure = (
        pressure_seconds is not None
        and pressure_seconds <= config.close_pressure_window_seconds
    )
    missing_families = _missing_required_update_families(
        event.update_family,
        config.required_update_families,
    )
    reason_codes = _row_reason_codes(
        event_age=event_age,
        source_age=source_age,
        context_age=context_age,
        close_pressure=close_pressure,
        missing_families=missing_families,
        config=config,
    )
    return MarketEventUpdateFreshnessRow(
        event_slug=event.event_slug,
        category=event.category,
        update_family=event.update_family,
        event_updated_at=event.event_updated_at,
        source_acknowledged_at=event.source_acknowledged_at,
        probability_captured_at=event.probability_captured_at,
        close_time=event.close_time,
        event_update_age_seconds=event_age,
        source_acknowledgement_age_seconds=source_age,
        probability_context_age_seconds=context_age,
        close_time_pressure_seconds=pressure_seconds,
        close_time_pressure=close_pressure,
        missing_required_update_families=missing_families,
        freshness_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_event_inputs(events: Iterable[object]) -> tuple[MarketEventUpdateFreshnessEventInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    return tuple(_coerce_event_input(value) for value in values)


def _coerce_event_input(value: object) -> MarketEventUpdateFreshnessEventInput:
    if type(value) is MarketEventUpdateFreshnessEventInput:
        _require_hard_flags("event", value)
        return value
    _require_hard_flags("event", value)
    return MarketEventUpdateFreshnessEventInput(
        event_slug=_field_value(value, "event_slug"),
        category=_field_value(value, "category"),
        update_family=_field_value(value, "update_family", default=None),
        event_updated_at=_field_value(value, "event_updated_at", default=None),
        source_acknowledged_at=_field_value(
            value,
            "source_acknowledged_at",
            default=None,
        ),
        probability_captured_at=_field_value(
            value,
            "probability_captured_at",
            default=None,
        ),
        close_time=_field_value(value, "close_time", default=None),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_reason_codes(
    *,
    event_age: Decimal | None,
    source_age: Decimal | None,
    context_age: Decimal | None,
    close_pressure: bool,
    missing_families: tuple[str, ...],
    config: MarketEventUpdateFreshnessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_families:
        reason_codes.append("missing_update_family")
    if event_age is None:
        reason_codes.append("missing_event_update_at")
    elif event_age > config.max_event_update_age_seconds:
        reason_codes.append("stale_event_update_age")
    if source_age is None:
        reason_codes.append("missing_source_acknowledgement_at")
    elif source_age > config.max_source_acknowledgement_age_seconds:
        reason_codes.append("stale_source_acknowledgement_age")
    if context_age is None:
        reason_codes.append("missing_probability_context")
    elif context_age > config.max_probability_context_age_seconds:
        reason_codes.append("stale_probability_context")
    if close_pressure:
        reason_codes.append("close_time_pressure")
    return _canonical_reason_codes(reason_codes)


def _summary_reason_codes(
    rows: tuple[MarketEventUpdateFreshnessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_market_event_updates",)
    reason_codes = tuple(
        reason_code
        for reason_code in REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )
    if not reason_codes:
        return ("market_event_updates_fresh",)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return "blocked"
    if reason_codes:
        return "watch"
    return "pass"


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return "blocked"
    if reason_codes == ("market_event_updates_fresh",):
        return "pass"
    return "watch"


def _is_blocking_reason(reason_code: str) -> bool:
    return reason_code in {
        "no_market_event_updates",
        "missing_update_family",
        "missing_event_update_at",
        "missing_source_acknowledgement_at",
        "missing_probability_context",
    }


def _missing_required_update_families(
    update_family: str | None,
    required_update_families: tuple[str, ...],
) -> tuple[str, ...]:
    if update_family is not None and update_family in required_update_families:
        return ()
    if update_family is None:
        return tuple(
            family
            for family in required_update_families
            if family != "metadata"
        ) + tuple(
            family
            for family in required_update_families
            if family == "metadata"
        )
    return required_update_families


def _category_status_counts(
    rows: tuple[MarketEventUpdateFreshnessRow, ...],
) -> tuple[MarketEventUpdateFreshnessStatusCount, ...]:
    status_counts: Counter[tuple[str, str]] = Counter(
        (row.category, row.freshness_status) for row in rows
    )
    return tuple(
        MarketEventUpdateFreshnessStatusCount(
            category=category,
            freshness_status=freshness_status,
            count=_decimal_count(count),
        )
        for (category, freshness_status), count in sorted(status_counts.items())
    )


def _reason_code_counts(
    rows: tuple[MarketEventUpdateFreshnessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketEventUpdateFreshnessReasonCodeCount, ...]:
    if not rows or reason_codes == ("market_event_updates_fresh",):
        return (
            MarketEventUpdateFreshnessReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _row_status_count(rows: tuple[MarketEventUpdateFreshnessRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.freshness_status == status)


def _average_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return None
    return _quantize(sum(present_values, ZERO) / Decimal(len(present_values)))


def _age_seconds(generated_at: datetime, captured_at: datetime | None) -> Decimal | None:
    if captured_at is None:
        return None
    delta = generated_at - captured_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _close_pressure_seconds(
    generated_at: datetime,
    close_time: datetime | None,
) -> Decimal | None:
    if close_time is None:
        return None
    delta = close_time - generated_at
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    if seconds < ZERO:
        return ZERO
    return seconds


def _reject_future_times(
    event: MarketEventUpdateFreshnessEventInput,
    generated_at: datetime,
) -> None:
    for field_name in (
        "event_updated_at",
        "source_acknowledged_at",
        "probability_captured_at",
    ):
        value = getattr(event, field_name)
        if value is not None and value > generated_at:
            raise ValueError(f"{field_name} must not be after generated_at")


def _row_sort_key(
    row: MarketEventUpdateFreshnessRow,
) -> tuple[int, str, str, str, str, str, str, str]:
    rank = {"blocked": 0, "watch": 1, "pass": 2}[row.freshness_status]
    return (
        rank,
        row.category,
        row.event_slug,
        row.update_family or "",
        _datetime_sort_value(row.event_updated_at),
        _datetime_sort_value(row.source_acknowledged_at),
        _datetime_sort_value(row.probability_captured_at),
        _datetime_sort_value(row.close_time),
    )


def _datetime_sort_value(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _normalize_rows(
    rows: Iterable[MarketEventUpdateFreshnessRow],
) -> tuple[MarketEventUpdateFreshnessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventUpdateFreshnessRow:
            raise ValueError("rows must contain MarketEventUpdateFreshnessRow values")
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_status_counts(
    rows: Iterable[MarketEventUpdateFreshnessStatusCount],
) -> tuple[MarketEventUpdateFreshnessStatusCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("category_status_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("category_status_counts must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventUpdateFreshnessStatusCount:
            raise ValueError(
                "category_status_counts must contain status count values",
            )
        _require_hard_flags("status_count", row)
    if values != tuple(
        sorted(values, key=lambda row: (row.category, row.freshness_status)),
    ):
        raise ValueError("category_status_counts must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[MarketEventUpdateFreshnessReasonCodeCount],
) -> tuple[MarketEventUpdateFreshnessReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventUpdateFreshnessReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", row)
    if values != tuple(sorted(values, key=lambda row: (-row.count, row.reason_code))):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
    sorted_values = tuple(sorted(values, key=REASON_CODES.index))
    if values and values != sorted_values:
        raise ValueError("reason_codes must be deterministically sorted")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    return values


def _canonical_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    values = tuple(reason_codes)
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(values, key=REASON_CODES.index))


def _validate_row_consistency(row: MarketEventUpdateFreshnessRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.freshness_status != expected_status:
        raise ValueError("freshness_status must match reason_codes")
    if row.close_time_pressure and "close_time_pressure" not in row.reason_codes:
        raise ValueError("close_time_pressure must match reason_codes")
    if (
        row.missing_required_update_families
        and "missing_update_family" not in row.reason_codes
    ):
        raise ValueError("missing_required_update_families must match reason_codes")


def _validate_report_consistency(report: MarketEventUpdateFreshnessReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_row_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_row_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_row_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.close_pressure_count != _decimal_count(
        sum(1 for row in report.rows if row.close_time_pressure),
    ):
        raise ValueError("close_pressure_count must match rows")
    if report.missing_update_family_count != _decimal_count(
        sum(1 for row in report.rows if "missing_update_family" in row.reason_codes),
    ):
        raise ValueError("missing_update_family_count must match rows")
    if report.stale_probability_context_count != _decimal_count(
        sum(1 for row in report.rows if "stale_probability_context" in row.reason_codes),
    ):
        raise ValueError("stale_probability_context_count must match rows")
    if report.average_event_update_age_seconds != _average_optional_decimal(
        row.event_update_age_seconds for row in report.rows
    ):
        raise ValueError("average_event_update_age_seconds must match rows")
    if report.average_source_acknowledgement_age_seconds != _average_optional_decimal(
        row.source_acknowledgement_age_seconds for row in report.rows
    ):
        raise ValueError("average_source_acknowledgement_age_seconds must match rows")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must summarize reason_codes")
    if report.category_status_counts != _category_status_counts(report.rows):
        raise ValueError("category_status_counts must summarize rows")
    if report.freshness_status != _summary_status(report.reason_codes):
        raise ValueError("freshness_status must match reason_codes")
    expected_digest = _derived_validation_digest(
        event_count=report.event_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        close_pressure_count=report.close_pressure_count,
        rows=report.rows,
        category_status_counts=report.category_status_counts,
        reason_code_counts=report.reason_code_counts,
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match derived report checks")


class _Missing:
    pass


_MISSING = _Missing()


def _field_value(value: object, field_name: str, default: object = _MISSING) -> object:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


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


def _normalize_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_required_update_families(value: object) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "required_update_families",
        value,
        allow_empty=False,
    )


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in values:
        _require_canonical_string(field_name, item)
    return values


def _require_freshness_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in FRESHNESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _derived_validation_digest(
    *,
    event_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    close_pressure_count: Decimal,
    rows: tuple[MarketEventUpdateFreshnessRow, ...],
    category_status_counts: tuple[MarketEventUpdateFreshnessStatusCount, ...],
    reason_code_counts: tuple[MarketEventUpdateFreshnessReasonCodeCount, ...],
) -> tuple[tuple[str, str], ...]:
    status_total = pass_count + watch_count + blocked_count
    category_status_total = sum(
        (row.count for row in category_status_counts),
        ZERO,
    )
    reason_code_total = sum((row.count for row in reason_code_counts), ZERO)
    return (
        ("blocked_count", _validation_decimal(blocked_count)),
        ("category_status_total", _validation_decimal(category_status_total)),
        ("close_pressure_count", _validation_decimal(close_pressure_count)),
        ("event_count", _validation_decimal(event_count)),
        ("hard_flags", "paper_only/report_only/readonly"),
        ("reason_code_total", _validation_decimal(reason_code_total)),
        ("row_count", _validation_decimal(_decimal_count(len(rows)))),
        ("status_total", _validation_decimal(status_total)),
    )


def _normalize_validation_digest(
    field_name: str,
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if type(item) not in (list, tuple):
            raise ValueError(f"{field_name} must contain key value pairs")
        pair = tuple(item)
        if len(pair) != 2:
            raise ValueError(f"{field_name} must contain key value pairs")
        key, item_value = pair
        _require_canonical_string(field_name, key)
        _require_canonical_string(field_name, item_value)
        pairs.append((key, item_value))
    normalized = tuple(pairs)
    if len({key for key, _ in normalized}) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicate keys")
    if normalized != tuple(sorted(normalized, key=lambda pair: pair[0])):
        raise ValueError(f"{field_name} must be deterministically sorted")
    return normalized


def _validation_decimal(value: Decimal) -> str:
    _normalize_nonnegative_decimal("derived_validation_digest value", value)
    return str(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if _field_value(value, "paper_only", default=None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if _field_value(value, "report_only", default=None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if _field_value(value, "readonly", default=None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


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


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} contains unsafe public payload key")
            if _has_unsafe_fragment(key):
                raise ValueError(f"{context} contains unsafe public payload key")
            _reject_unsafe_public_payload(context, item)
    elif type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(context, item)
    elif type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"{context} contains unsafe public payload value")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _unsafe_fragments())


def _unsafe_fragments() -> tuple[str, ...]:
    return tuple(
        "".join(parts)
        for parts in (
            ("li", "ve"),
            ("au", "th"),
            ("wal", "let"),
            ("or", "der"),
            ("net", "work"),
            ("data", "base"),
            ("per", "sist"),
        )
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is dict:
        return {
            key: _payload_value(item)
            for key, item in value.items()
        }
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: _payload_value(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        }
    return value
