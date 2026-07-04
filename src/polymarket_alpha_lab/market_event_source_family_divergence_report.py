"""Pure Phase 1 market event source family divergence report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_EVENT_SOURCE_FAMILY_DIVERGENCE_REPORT_CONFIG_VERSION = (
    "market-event-source-family-divergence-report-v0"
)

SOURCE_FAMILIES = ("official", "primary", "proxy", "team_acknowledged")
SOURCE_FAMILY_RANK = {
    "official": 0,
    "primary": 1,
    "proxy": 2,
    "team_acknowledged": 3,
}
REPORT_STATUSES = ("clear", "watch", "blocked")
PRESSURE_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

SOURCE_DIVERGENCE_REASON = "market_event_source_family_state_divergence"
STALE_SOURCE_REASON = "market_event_source_family_stale"
MISSING_ACKNOWLEDGEMENT_REASON = (
    "market_event_source_family_acknowledgement_missing"
)
CLEAR_REASON = "market_event_source_family_divergence_clear"
REASON_CODES = (
    SOURCE_DIVERGENCE_REASON,
    STALE_SOURCE_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketEventSourceFamilyDivergenceConfig:
    config_version: str = (
        DEFAULT_MARKET_EVENT_SOURCE_FAMILY_DIVERGENCE_REPORT_CONFIG_VERSION
    )
    stale_source_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_source_seconds",
            _require_positive_decimal(
                "stale_source_seconds",
                self.stale_source_seconds,
            ),
        )
        require_paper_only_flags("market event source family divergence config", self)


@dataclass(frozen=True)
class MarketEventSourceFamilyDivergenceInputRow:
    event_id: str
    source_family: str
    event_state: str
    source_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_source_family("source_family", self.source_family)
        _require_public_string("event_state", self.event_state)
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        require_paper_only_flags(
            "market event source family divergence input row",
            self,
        )


@dataclass(frozen=True)
class MarketEventSourceFamilyDivergenceRow:
    event_id: str
    official_state: str | None
    primary_state: str | None
    proxy_state: str | None
    team_acknowledged_state: str | None
    source_family_count: Decimal
    divergent_source_family_count: Decimal
    stale_source_family_count: Decimal
    missing_acknowledgement_count: Decimal
    max_source_age_seconds: Decimal
    divergence_ratio: Decimal
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        for field_name in (
            "official_state",
            "primary_state",
            "proxy_state",
            "team_acknowledged_state",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_count",
            "divergent_source_family_count",
            "stale_source_family_count",
            "missing_acknowledgement_count",
            "max_source_age_seconds",
            "divergence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_pressure_status("pressure_status", self.pressure_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_event_row(self)
        require_paper_only_flags("market event source family divergence row", self)


@dataclass(frozen=True)
class MarketEventSourceFamilyDivergenceReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    event_count: Decimal
    source_family_count: Decimal
    clear_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    pressure_event_count: Decimal
    divergent_event_count: Decimal
    stale_event_count: Decimal
    missing_acknowledgement_event_count: Decimal
    stale_source_family_count: Decimal
    divergence_ratio: Decimal
    stale_source_ratio: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketEventSourceFamilyDivergenceRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "event_count",
            "source_family_count",
            "clear_event_count",
            "watch_event_count",
            "blocked_event_count",
            "pressure_event_count",
            "divergent_event_count",
            "stale_event_count",
            "missing_acknowledgement_event_count",
            "stale_source_family_count",
            "divergence_ratio",
            "stale_source_ratio",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("market event source family divergence report", self)


def build_market_event_source_family_divergence_report(
    input_rows: list[MarketEventSourceFamilyDivergenceInputRow]
    | tuple[MarketEventSourceFamilyDivergenceInputRow, ...],
    *,
    config: MarketEventSourceFamilyDivergenceConfig,
    generated_at: datetime,
) -> MarketEventSourceFamilyDivergenceReport:
    if type(config) is not MarketEventSourceFamilyDivergenceConfig:
        raise ValueError("config must be a MarketEventSourceFamilyDivergenceConfig")
    require_paper_only_flags("market event source family divergence config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)

    by_event: dict[str, list[MarketEventSourceFamilyDivergenceInputRow]] = {}
    for row in rows:
        by_event.setdefault(row.event_id, []).append(row)

    report_rows = _sort_rows(
        tuple(
            _event_row(
                event_id,
                tuple(event_rows),
                config=config,
                generated_at=generated_at_utc,
            )
            for event_id, event_rows in sorted(by_event.items())
        ),
    )
    reason_codes = _report_reason_codes(report_rows)

    return MarketEventSourceFamilyDivergenceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        event_count=_decimal_count(len(report_rows)),
        source_family_count=_sum_decimal(row.source_family_count for row in report_rows),
        clear_event_count=_status_count(report_rows, "clear"),
        watch_event_count=_status_count(report_rows, "watch"),
        blocked_event_count=_status_count(report_rows, "blocked"),
        pressure_event_count=_pressure_count(report_rows),
        divergent_event_count=_positive_metric_count(
            report_rows,
            "divergent_source_family_count",
        ),
        stale_event_count=_positive_metric_count(
            report_rows,
            "stale_source_family_count",
        ),
        missing_acknowledgement_event_count=_positive_metric_count(
            report_rows,
            "missing_acknowledgement_count",
        ),
        stale_source_family_count=_sum_decimal(
            row.stale_source_family_count for row in report_rows
        ),
        divergence_ratio=_ratio(
            _positive_metric_count(report_rows, "divergent_source_family_count"),
            _decimal_count(len(report_rows)),
        ),
        stale_source_ratio=_ratio(
            _sum_decimal(row.stale_source_family_count for row in report_rows),
            _sum_decimal(row.source_family_count for row in report_rows),
        ),
        max_source_age_seconds=_max_source_age_seconds(report_rows),
        rows=report_rows,
    )


def market_event_source_family_divergence_report_to_payload(
    report: MarketEventSourceFamilyDivergenceReport,
) -> dict[str, Any]:
    if type(report) is not MarketEventSourceFamilyDivergenceReport:
        raise ValueError("report must be a MarketEventSourceFamilyDivergenceReport")
    require_paper_only_flags("market event source family divergence report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields(
        "market event source family divergence report value",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketEventSourceFamilyDivergenceInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketEventSourceFamilyDivergenceInputRow:
            raise ValueError("input rows must contain divergence input rows")
        require_paper_only_flags(
            "market event source family divergence input row",
            row,
        )
        if row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be in the future")
        key = (row.event_id, row.source_family)
        if key in seen:
            raise ValueError("source_family values must be unique per event_id")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.event_id,
                SOURCE_FAMILY_RANK[row.source_family],
                row.event_state,
                row.source_observed_at,
            ),
        ),
    )


def _event_row(
    event_id: str,
    rows: tuple[MarketEventSourceFamilyDivergenceInputRow, ...],
    *,
    config: MarketEventSourceFamilyDivergenceConfig,
    generated_at: datetime,
) -> MarketEventSourceFamilyDivergenceRow:
    by_family = {row.source_family: row for row in rows}
    reference_state = _reference_state(rows)
    divergent_source_family_count = _decimal_count(
        sum(1 for row in rows if row.event_state != reference_state),
    )
    stale_source_family_count = _decimal_count(
        sum(
            1
            for row in rows
            if _age_seconds(generated_at, row.source_observed_at)
            > config.stale_source_seconds
        ),
    )
    missing_acknowledgement_count = (
        ZERO if "team_acknowledged" in by_family else ONE
    )
    max_source_age_seconds = max(
        (_age_seconds(generated_at, row.source_observed_at) for row in rows),
        default=ZERO,
    )
    source_family_count = _decimal_count(len(rows))
    reason_codes = _row_reason_codes(
        divergent_source_family_count=divergent_source_family_count,
        stale_source_family_count=stale_source_family_count,
        missing_acknowledgement_count=missing_acknowledgement_count,
    )

    return MarketEventSourceFamilyDivergenceRow(
        event_id=event_id,
        official_state=_state_for_family(by_family, "official"),
        primary_state=_state_for_family(by_family, "primary"),
        proxy_state=_state_for_family(by_family, "proxy"),
        team_acknowledged_state=_state_for_family(by_family, "team_acknowledged"),
        source_family_count=source_family_count,
        divergent_source_family_count=divergent_source_family_count,
        stale_source_family_count=stale_source_family_count,
        missing_acknowledgement_count=missing_acknowledgement_count,
        max_source_age_seconds=max_source_age_seconds,
        divergence_ratio=_ratio(divergent_source_family_count, source_family_count),
        pressure_status=_row_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _reference_state(
    rows: tuple[MarketEventSourceFamilyDivergenceInputRow, ...],
) -> str:
    official = next((row.event_state for row in rows if row.source_family == "official"), None)
    if official is not None:
        return official
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.event_state] = counts.get(row.event_state, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _state_for_family(
    rows_by_family: dict[str, MarketEventSourceFamilyDivergenceInputRow],
    source_family: str,
) -> str | None:
    row = rows_by_family.get(source_family)
    return None if row is None else row.event_state


def _row_reason_codes(
    *,
    divergent_source_family_count: Decimal,
    stale_source_family_count: Decimal,
    missing_acknowledgement_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if divergent_source_family_count > ZERO:
        reason_codes.append(SOURCE_DIVERGENCE_REASON)
    if stale_source_family_count > ZERO:
        reason_codes.append(STALE_SOURCE_REASON)
    if missing_acknowledgement_count > ZERO:
        reason_codes.append(MISSING_ACKNOWLEDGEMENT_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[MarketEventSourceFamilyDivergenceRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return "blocked"
    if (
        SOURCE_DIVERGENCE_REASON in reason_codes
        or STALE_SOURCE_REASON in reason_codes
    ):
        return "watch"
    return "clear"


def _report_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return "blocked"
    if (
        SOURCE_DIVERGENCE_REASON in reason_codes
        or STALE_SOURCE_REASON in reason_codes
    ):
        return "watch"
    return "clear"


def _normalize_rows(
    value: object,
) -> tuple[MarketEventSourceFamilyDivergenceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketEventSourceFamilyDivergenceRow:
            raise ValueError("rows must contain divergence rows")
        require_paper_only_flags("market event source family divergence row", row)
        if row.event_id in seen:
            raise ValueError("rows must be unique per event_id")
        seen.add(row.event_id)
    expected = _sort_rows(rows)
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _sort_rows(
    rows: tuple[MarketEventSourceFamilyDivergenceRow, ...],
) -> tuple[MarketEventSourceFamilyDivergenceRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.pressure_status],
                -row.missing_acknowledgement_count,
                -row.divergent_source_family_count,
                -row.stale_source_family_count,
                -row.max_source_age_seconds,
                row.event_id,
            ),
        ),
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_event_row(row: MarketEventSourceFamilyDivergenceRow) -> None:
    present_source_family_count = _decimal_count(
        sum(
            1
            for value in (
                row.official_state,
                row.primary_state,
                row.proxy_state,
                row.team_acknowledged_state,
            )
            if value is not None
        ),
    )
    if row.source_family_count != present_source_family_count:
        raise ValueError("source_family_count must match populated source families")
    if row.divergent_source_family_count > row.source_family_count:
        raise ValueError("divergent_source_family_count must not exceed source_family_count")
    if row.stale_source_family_count > row.source_family_count:
        raise ValueError("stale_source_family_count must not exceed source_family_count")
    expected_missing = ZERO if row.team_acknowledged_state is not None else ONE
    if row.missing_acknowledgement_count != expected_missing:
        raise ValueError(
            "missing_acknowledgement_count must match team acknowledgement state",
        )
    if row.divergence_ratio != _ratio(
        row.divergent_source_family_count,
        row.source_family_count,
    ):
        raise ValueError("divergence_ratio must match source family counts")
    expected_reason_codes = _row_reason_codes(
        divergent_source_family_count=row.divergent_source_family_count,
        stale_source_family_count=row.stale_source_family_count,
        missing_acknowledgement_count=row.missing_acknowledgement_count,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match event row metrics")
    if row.pressure_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("pressure_status must match reason_codes")


def _validate_report(report: MarketEventSourceFamilyDivergenceReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.source_family_count != _sum_decimal(
        row.source_family_count for row in report.rows
    ):
        raise ValueError("source_family_count must match rows")
    if report.clear_event_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_event_count must match rows")
    if report.watch_event_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_event_count must match rows")
    if report.blocked_event_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_event_count must match rows")
    if (
        report.clear_event_count
        + report.watch_event_count
        + report.blocked_event_count
        != report.event_count
    ):
        raise ValueError("event status counts must sum to event_count")
    if report.pressure_event_count != _pressure_count(report.rows):
        raise ValueError("pressure_event_count must match rows")
    if report.divergent_event_count != _positive_metric_count(
        report.rows,
        "divergent_source_family_count",
    ):
        raise ValueError("divergent_event_count must match rows")
    if report.stale_event_count != _positive_metric_count(
        report.rows,
        "stale_source_family_count",
    ):
        raise ValueError("stale_event_count must match rows")
    if report.missing_acknowledgement_event_count != _positive_metric_count(
        report.rows,
        "missing_acknowledgement_count",
    ):
        raise ValueError("missing_acknowledgement_event_count must match rows")
    if report.stale_source_family_count != _sum_decimal(
        row.stale_source_family_count for row in report.rows
    ):
        raise ValueError("stale_source_family_count must match rows")
    if report.divergence_ratio != _ratio(
        report.divergent_event_count,
        report.event_count,
    ):
        raise ValueError("divergence_ratio must match event counts")
    if report.stale_source_ratio != _ratio(
        report.stale_source_family_count,
        report.source_family_count,
    ):
        raise ValueError("stale_source_ratio must match source family counts")
    if report.max_source_age_seconds != _max_source_age_seconds(report.rows):
        raise ValueError("max_source_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _status_count(
    rows: tuple[MarketEventSourceFamilyDivergenceRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.pressure_status == status))


def _pressure_count(rows: tuple[MarketEventSourceFamilyDivergenceRow, ...]) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.pressure_status != "clear"))


def _positive_metric_count(
    rows: tuple[MarketEventSourceFamilyDivergenceRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) > ZERO))


def _max_source_age_seconds(
    rows: tuple[MarketEventSourceFamilyDivergenceRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.max_source_age_seconds for row in rows)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a concrete UTC offset")
    return value.astimezone(UTC)


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_pressure_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PRESSURE_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_source_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILIES:
        raise ValueError(f"{field_name} must be official, primary, proxy, or team_acknowledged")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_EVENT_SOURCE_FAMILY_DIVERGENCE_REPORT_CONFIG_VERSION",
    "MarketEventSourceFamilyDivergenceConfig",
    "MarketEventSourceFamilyDivergenceInputRow",
    "MarketEventSourceFamilyDivergenceReport",
    "MarketEventSourceFamilyDivergenceRow",
    "build_market_event_source_family_divergence_report",
    "market_event_source_family_divergence_report_to_payload",
)
