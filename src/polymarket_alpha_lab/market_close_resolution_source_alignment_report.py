"""Phase 1 market close and resolution source alignment report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "market-close-resolution-source-alignment-report-v0"
)

EMPTY_INPUT_REASON = "empty_market_close_resolution_source_alignment_input"
PASS_REASON = "market_close_resolution_source_alignment_passed"
MISSING_CLOSE_TIME_REASON = "market_close_time_missing"
STALE_SOURCE_REFRESH_REASON = "official_resolution_source_refresh_stale"
SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON = (
    "official_resolution_source_timestamp_before_close"
)
MISSING_TEAM_ACKNOWLEDGEMENT_REASON = "team_resolution_acknowledgement_missing"
AMBIGUOUS_RESOLUTION_CRITERIA_REASON = "resolution_criteria_ambiguous"

REASON_CODES = (
    EMPTY_INPUT_REASON,
    MISSING_CLOSE_TIME_REASON,
    SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON,
    MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
    STALE_SOURCE_REFRESH_REASON,
    AMBIGUOUS_RESOLUTION_CRITERIA_REASON,
    PASS_REASON,
)
BLOCKING_REASON_CODES = (
    MISSING_CLOSE_TIME_REASON,
    SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON,
    MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
)
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("empty", "pass", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
REASON_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("tra", "ding"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
    ),
)


@dataclass(frozen=True)
class MarketCloseResolutionSourceAlignmentConfig:
    config_version: str = (
        DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    expected_source_refresh_window_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "expected_source_refresh_window_seconds",
            _require_positive_decimal(
                "expected_source_refresh_window_seconds",
                self.expected_source_refresh_window_seconds,
            ),
        )
        require_paper_only_flags(
            "market close resolution source alignment config",
            self,
        )


@dataclass(frozen=True)
class MarketCloseResolutionSourceAlignmentInputRow:
    team_id: str
    market_id: str
    source_id: str
    market_close_at: datetime | None
    resolution_source_refreshed_at: datetime | None
    resolution_source_timestamp_at: datetime | None
    team_acknowledged_at: datetime | None
    resolution_criteria_ambiguous: bool
    expected_source_refresh_window_seconds: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_public_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "market_id",
            _require_public_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "source_id",
            _require_public_string("source_id", self.source_id),
        )
        for field_name in (
            "market_close_at",
            "resolution_source_refreshed_at",
            "resolution_source_timestamp_at",
            "team_acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        if type(self.resolution_criteria_ambiguous) is not bool:
            raise ValueError("resolution_criteria_ambiguous must be a bool")
        object.__setattr__(
            self,
            "expected_source_refresh_window_seconds",
            _normalize_optional_positive_decimal(
                "expected_source_refresh_window_seconds",
                self.expected_source_refresh_window_seconds,
            ),
        )
        require_paper_only_flags(
            "market close resolution source alignment input row",
            self,
        )


@dataclass(frozen=True)
class MarketCloseResolutionSourceAlignmentRow:
    team_id: str
    market_id: str
    source_id: str
    market_close_at: datetime | None
    resolution_source_refreshed_at: datetime | None
    resolution_source_timestamp_at: datetime | None
    team_acknowledged_at: datetime | None
    resolution_criteria_ambiguous: bool
    expected_source_refresh_window_seconds: Decimal
    market_close_age_seconds: Decimal | None
    source_refresh_age_seconds: Decimal | None
    source_refresh_delay_seconds: Decimal | None
    source_timestamp_before_close_seconds: Decimal | None
    team_acknowledgement_delay_seconds: Decimal | None
    alignment_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_public_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "market_id",
            _require_public_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "source_id",
            _require_public_string("source_id", self.source_id),
        )
        for field_name in (
            "market_close_at",
            "resolution_source_refreshed_at",
            "resolution_source_timestamp_at",
            "team_acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        if type(self.resolution_criteria_ambiguous) is not bool:
            raise ValueError("resolution_criteria_ambiguous must be a bool")
        object.__setattr__(
            self,
            "expected_source_refresh_window_seconds",
            _require_positive_decimal(
                "expected_source_refresh_window_seconds",
                self.expected_source_refresh_window_seconds,
            ),
        )
        for field_name in (
            "market_close_age_seconds",
            "source_refresh_age_seconds",
            "source_refresh_delay_seconds",
            "source_timestamp_before_close_seconds",
            "team_acknowledgement_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("alignment_status", self.alignment_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags(
            "market close resolution source alignment row",
            self,
        )


@dataclass(frozen=True)
class MarketCloseResolutionSourceAlignmentReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    missing_close_time_count: Decimal
    stale_source_refresh_count: Decimal
    source_timestamp_before_close_count: Decimal
    missing_team_acknowledgement_count: Decimal
    ambiguous_resolution_criteria_count: Decimal
    issue_ratio: Decimal
    max_market_close_age_seconds: Decimal | None
    max_source_refresh_age_seconds: Decimal | None
    rows: tuple[MarketCloseResolutionSourceAlignmentRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "pass_market_count",
            "watch_market_count",
            "blocked_market_count",
            "missing_close_time_count",
            "stale_source_refresh_count",
            "source_timestamp_before_close_count",
            "missing_team_acknowledgement_count",
            "ambiguous_resolution_criteria_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_ratio_decimal("issue_ratio", self.issue_ratio),
        )
        object.__setattr__(
            self,
            "max_market_close_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_market_close_age_seconds",
                self.max_market_close_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_source_refresh_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_source_refresh_age_seconds",
                self.max_source_refresh_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)
        require_paper_only_flags(
            "market close resolution source alignment report",
            self,
        )


def build_market_close_resolution_source_alignment_report(
    input_rows: list[MarketCloseResolutionSourceAlignmentInputRow]
    | tuple[MarketCloseResolutionSourceAlignmentInputRow, ...],
    *,
    config: MarketCloseResolutionSourceAlignmentConfig,
    generated_at: datetime,
) -> MarketCloseResolutionSourceAlignmentReport:
    if type(config) is not MarketCloseResolutionSourceAlignmentConfig:
        raise ValueError(
            "config must be a MarketCloseResolutionSourceAlignmentConfig",
        )
    require_paper_only_flags(
        "market close resolution source alignment config",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)

    return MarketCloseResolutionSourceAlignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        reason_codes=reason_codes,
        market_count=_decimal_count(len(rows)),
        pass_market_count=_status_count(rows, "pass"),
        watch_market_count=_status_count(rows, "watch"),
        blocked_market_count=_status_count(rows, "blocked"),
        missing_close_time_count=_reason_count(rows, MISSING_CLOSE_TIME_REASON),
        stale_source_refresh_count=_reason_count(rows, STALE_SOURCE_REFRESH_REASON),
        source_timestamp_before_close_count=_reason_count(
            rows,
            SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON,
        ),
        missing_team_acknowledgement_count=_reason_count(
            rows,
            MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
        ),
        ambiguous_resolution_criteria_count=_reason_count(
            rows,
            AMBIGUOUS_RESOLUTION_CRITERIA_REASON,
        ),
        issue_ratio=_ratio(
            _status_count(rows, "watch") + _status_count(rows, "blocked"),
            _decimal_count(len(rows)),
        ),
        max_market_close_age_seconds=_max_optional(
            tuple(row.market_close_age_seconds for row in rows),
        ),
        max_source_refresh_age_seconds=_max_optional(
            tuple(row.source_refresh_age_seconds for row in rows),
        ),
        rows=rows,
    )


def market_close_resolution_source_alignment_report_payload(
    report: MarketCloseResolutionSourceAlignmentReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseResolutionSourceAlignmentReport:
        raise ValueError("report must be a MarketCloseResolutionSourceAlignmentReport")
    require_paper_only_flags(
        "market close resolution source alignment report",
        report,
    )
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    _reject_unsafe_public_json_fields(
        "market close resolution source alignment report",
        ready,
    )
    reject_unsafe_surface_fields(
        "market close resolution source alignment report",
        ready,
    )
    return ready


def _normalize_input_rows(
    input_rows: object,
    *,
    generated_at: datetime,
) -> tuple[MarketCloseResolutionSourceAlignmentInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketCloseResolutionSourceAlignmentInputRow:
            raise ValueError(
                "input_rows must contain MarketCloseResolutionSourceAlignmentInputRow",
            )
        require_paper_only_flags(
            "market close resolution source alignment input row",
            row,
        )
        for field_name in (
            "market_close_at",
            "resolution_source_refreshed_at",
            "resolution_source_timestamp_at",
            "team_acknowledged_at",
        ):
            value = getattr(row, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")
        key = (row.team_id, row.market_id)
        if key in seen_keys:
            raise ValueError("input_rows must be unique by team_id and market_id")
        seen_keys.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_id, row.market_id, row.source_id)))


def _row_from_input(
    input_row: MarketCloseResolutionSourceAlignmentInputRow,
    *,
    config: MarketCloseResolutionSourceAlignmentConfig,
    generated_at: datetime,
) -> MarketCloseResolutionSourceAlignmentRow:
    expected_window = (
        input_row.expected_source_refresh_window_seconds
        if input_row.expected_source_refresh_window_seconds is not None
        else config.expected_source_refresh_window_seconds
    )
    market_close_age_seconds = (
        None
        if input_row.market_close_at is None
        else _age_seconds(
            generated_at,
            input_row.market_close_at,
            earlier_field_name="market_close_at",
        )
    )
    source_refresh_age_seconds = (
        None
        if input_row.resolution_source_refreshed_at is None
        else _age_seconds(
            generated_at,
            input_row.resolution_source_refreshed_at,
            earlier_field_name="resolution_source_refreshed_at",
        )
    )
    source_refresh_delay_seconds = _source_refresh_delay_seconds(input_row)
    source_timestamp_before_close_seconds = _source_timestamp_before_close_seconds(
        input_row,
    )
    team_acknowledgement_delay_seconds = _team_acknowledgement_delay_seconds(input_row)
    reason_codes = _input_reason_codes(
        input_row,
        expected_source_refresh_window_seconds=expected_window,
        source_refresh_age_seconds=source_refresh_age_seconds,
        source_timestamp_before_close_seconds=source_timestamp_before_close_seconds,
    )

    return MarketCloseResolutionSourceAlignmentRow(
        team_id=input_row.team_id,
        market_id=input_row.market_id,
        source_id=input_row.source_id,
        market_close_at=input_row.market_close_at,
        resolution_source_refreshed_at=input_row.resolution_source_refreshed_at,
        resolution_source_timestamp_at=input_row.resolution_source_timestamp_at,
        team_acknowledged_at=input_row.team_acknowledged_at,
        resolution_criteria_ambiguous=input_row.resolution_criteria_ambiguous,
        expected_source_refresh_window_seconds=expected_window,
        market_close_age_seconds=market_close_age_seconds,
        source_refresh_age_seconds=source_refresh_age_seconds,
        source_refresh_delay_seconds=source_refresh_delay_seconds,
        source_timestamp_before_close_seconds=source_timestamp_before_close_seconds,
        team_acknowledgement_delay_seconds=team_acknowledgement_delay_seconds,
        alignment_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _input_reason_codes(
    input_row: MarketCloseResolutionSourceAlignmentInputRow,
    *,
    expected_source_refresh_window_seconds: Decimal,
    source_refresh_age_seconds: Decimal | None,
    source_timestamp_before_close_seconds: Decimal | None,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if input_row.market_close_at is None:
        reasons.add(MISSING_CLOSE_TIME_REASON)
    if (
        source_refresh_age_seconds is None
        or source_refresh_age_seconds > expected_source_refresh_window_seconds
    ):
        reasons.add(STALE_SOURCE_REFRESH_REASON)
    if (
        source_timestamp_before_close_seconds is not None
        and source_timestamp_before_close_seconds > ZERO
    ):
        reasons.add(SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON)
    if input_row.market_close_at is not None and input_row.team_acknowledged_at is None:
        reasons.add(MISSING_TEAM_ACKNOWLEDGEMENT_REASON)
    if input_row.resolution_criteria_ambiguous:
        reasons.add(AMBIGUOUS_RESOLUTION_CRITERIA_REASON)
    if not reasons:
        reasons.add(PASS_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _source_refresh_delay_seconds(
    input_row: MarketCloseResolutionSourceAlignmentInputRow,
) -> Decimal | None:
    if (
        input_row.market_close_at is None
        or input_row.resolution_source_refreshed_at is None
    ):
        return None
    if input_row.resolution_source_refreshed_at <= input_row.market_close_at:
        return ZERO
    return _elapsed_seconds(
        input_row.market_close_at,
        input_row.resolution_source_refreshed_at,
    )


def _source_timestamp_before_close_seconds(
    input_row: MarketCloseResolutionSourceAlignmentInputRow,
) -> Decimal | None:
    if (
        input_row.market_close_at is None
        or input_row.resolution_source_timestamp_at is None
    ):
        return None
    if input_row.resolution_source_timestamp_at >= input_row.market_close_at:
        return ZERO
    return _elapsed_seconds(
        input_row.resolution_source_timestamp_at,
        input_row.market_close_at,
    )


def _team_acknowledgement_delay_seconds(
    input_row: MarketCloseResolutionSourceAlignmentInputRow,
) -> Decimal | None:
    if input_row.market_close_at is None or input_row.team_acknowledged_at is None:
        return None
    if input_row.team_acknowledged_at < input_row.market_close_at:
        raise ValueError("team_acknowledged_at must not be before market_close_at")
    return _elapsed_seconds(input_row.market_close_at, input_row.team_acknowledged_at)


def _validate_row(row: MarketCloseResolutionSourceAlignmentRow) -> None:
    if row.market_close_at is None and row.market_close_age_seconds is not None:
        raise ValueError("market_close_age_seconds requires market_close_at")
    if row.market_close_at is not None and row.market_close_age_seconds is None:
        raise ValueError("market_close_age_seconds is required for market_close_at")
    if (
        row.resolution_source_refreshed_at is None
        and row.source_refresh_age_seconds is not None
    ):
        raise ValueError("source_refresh_age_seconds requires source refresh time")
    if (
        row.resolution_source_refreshed_at is not None
        and row.source_refresh_age_seconds is None
    ):
        raise ValueError("source_refresh_age_seconds is required for source refresh time")
    if row.source_refresh_delay_seconds != _expected_source_refresh_delay_seconds(row):
        raise ValueError("source_refresh_delay_seconds must match source refresh time")
    if (
        row.source_timestamp_before_close_seconds
        != _expected_source_timestamp_before_close_seconds(row)
    ):
        raise ValueError("source_timestamp_before_close_seconds must match source time")
    if (
        row.team_acknowledgement_delay_seconds
        != _expected_team_acknowledgement_delay_seconds(row)
    ):
        raise ValueError(
            "team_acknowledgement_delay_seconds must match acknowledgement time",
        )
    expected_reasons = _expected_reason_codes_from_row(row)
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row state")
    if row.alignment_status != _row_status(row.reason_codes):
        raise ValueError("alignment_status must match reason_codes")


def _expected_source_refresh_delay_seconds(
    row: MarketCloseResolutionSourceAlignmentRow,
) -> Decimal | None:
    if row.market_close_at is None or row.resolution_source_refreshed_at is None:
        return None
    if row.resolution_source_refreshed_at <= row.market_close_at:
        return ZERO
    return _elapsed_seconds(row.market_close_at, row.resolution_source_refreshed_at)


def _expected_source_timestamp_before_close_seconds(
    row: MarketCloseResolutionSourceAlignmentRow,
) -> Decimal | None:
    if row.market_close_at is None or row.resolution_source_timestamp_at is None:
        return None
    if row.resolution_source_timestamp_at >= row.market_close_at:
        return ZERO
    return _elapsed_seconds(row.resolution_source_timestamp_at, row.market_close_at)


def _expected_team_acknowledgement_delay_seconds(
    row: MarketCloseResolutionSourceAlignmentRow,
) -> Decimal | None:
    if row.market_close_at is None or row.team_acknowledged_at is None:
        return None
    if row.team_acknowledged_at < row.market_close_at:
        raise ValueError("team_acknowledged_at must not be before market_close_at")
    return _elapsed_seconds(row.market_close_at, row.team_acknowledged_at)


def _expected_reason_codes_from_row(
    row: MarketCloseResolutionSourceAlignmentRow,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if row.market_close_at is None:
        reasons.add(MISSING_CLOSE_TIME_REASON)
    if (
        row.source_refresh_age_seconds is None
        or row.source_refresh_age_seconds > row.expected_source_refresh_window_seconds
    ):
        reasons.add(STALE_SOURCE_REFRESH_REASON)
    if (
        row.source_timestamp_before_close_seconds is not None
        and row.source_timestamp_before_close_seconds > ZERO
    ):
        reasons.add(SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON)
    if row.market_close_at is not None and row.team_acknowledged_at is None:
        reasons.add(MISSING_TEAM_ACKNOWLEDGEMENT_REASON)
    if row.resolution_criteria_ambiguous:
        reasons.add(AMBIGUOUS_RESOLUTION_CRITERIA_REASON)
    if not reasons:
        reasons.add(PASS_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _validate_report(report: MarketCloseResolutionSourceAlignmentReport) -> None:
    rows = report.rows
    for row in rows:
        _validate_report_row_times(report.generated_at, row)
    if report.market_count != _decimal_count(len(rows)):
        raise ValueError("market_count must match rows")
    if report.pass_market_count != _status_count(rows, "pass"):
        raise ValueError("pass_market_count must match rows")
    if report.watch_market_count != _status_count(rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if (
        report.pass_market_count + report.watch_market_count + report.blocked_market_count
        != report.market_count
    ):
        raise ValueError("status counts must match market_count")
    expected_reason_counts = (
        (MISSING_CLOSE_TIME_REASON, report.missing_close_time_count),
        (STALE_SOURCE_REFRESH_REASON, report.stale_source_refresh_count),
        (
            SOURCE_TIMESTAMP_BEFORE_CLOSE_REASON,
            report.source_timestamp_before_close_count,
        ),
        (
            MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
            report.missing_team_acknowledgement_count,
        ),
        (
            AMBIGUOUS_RESOLUTION_CRITERIA_REASON,
            report.ambiguous_resolution_criteria_count,
        ),
    )
    for reason_code, expected_count in expected_reason_counts:
        if expected_count != _reason_count(rows, reason_code):
            raise ValueError("reason counts must match rows")
    expected_issue_ratio = _ratio(
        report.watch_market_count + report.blocked_market_count,
        report.market_count,
    )
    if report.issue_ratio != expected_issue_ratio:
        raise ValueError("issue_ratio must match rows")
    if report.max_market_close_age_seconds != _max_optional(
        tuple(row.market_close_age_seconds for row in rows),
    ):
        raise ValueError("max_market_close_age_seconds must match rows")
    if report.max_source_refresh_age_seconds != _max_optional(
        tuple(row.source_refresh_age_seconds for row in rows),
    ):
        raise ValueError("max_source_refresh_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")


def _validate_report_row_times(
    generated_at: datetime,
    row: MarketCloseResolutionSourceAlignmentRow,
) -> None:
    if row.market_close_at is not None:
        expected_market_age = _age_seconds(
            generated_at,
            row.market_close_at,
            earlier_field_name="market_close_at",
        )
        if row.market_close_age_seconds != expected_market_age:
            raise ValueError("market_close_age_seconds must match generated_at")
    if row.resolution_source_refreshed_at is not None:
        expected_source_age = _age_seconds(
            generated_at,
            row.resolution_source_refreshed_at,
            earlier_field_name="resolution_source_refreshed_at",
        )
        if row.source_refresh_age_seconds != expected_source_age:
            raise ValueError("source_refresh_age_seconds must match generated_at")
    for field_name in (
        "resolution_source_timestamp_at",
        "team_acknowledged_at",
    ):
        value = getattr(row, field_name)
        if value is not None and value > generated_at:
            raise ValueError(f"{field_name} must not be after generated_at")


def _normalize_rows(
    value: object,
) -> tuple[MarketCloseResolutionSourceAlignmentRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketCloseResolutionSourceAlignmentRow:
            raise ValueError(
                "rows must contain MarketCloseResolutionSourceAlignmentRow",
            )
        require_paper_only_flags(
            "market close resolution source alignment row",
            row,
        )
        key = (row.team_id, row.market_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team_id and market_id")
        seen_keys.add(key)
    expected_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected_rows:
        raise ValueError("rows must be deterministic")
    return rows


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
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _row_sort_key(
    row: MarketCloseResolutionSourceAlignmentRow,
) -> tuple[int, int, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.alignment_status],
        REASON_RANK[row.reason_codes[0]],
        -_row_issue_age_seconds(row),
        row.team_id,
        row.market_id,
        row.source_id,
    )


def _row_issue_age_seconds(row: MarketCloseResolutionSourceAlignmentRow) -> Decimal:
    return max(
        tuple(
            value
            for value in (
                row.market_close_age_seconds,
                row.source_refresh_age_seconds,
                row.source_timestamp_before_close_seconds,
                row.team_acknowledgement_delay_seconds,
            )
            if value is not None
        ),
        default=ZERO,
    )


def _report_reason_codes(
    rows: tuple[MarketCloseResolutionSourceAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not reasons:
        reasons.add(PASS_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _report_status(rows: tuple[MarketCloseResolutionSourceAlignmentRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.alignment_status == "blocked" for row in rows):
        return "blocked"
    if any(row.alignment_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _status_count(
    rows: tuple[MarketCloseResolutionSourceAlignmentRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.alignment_status == status))


def _reason_count(
    rows: tuple[MarketCloseResolutionSourceAlignmentRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_optional(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return None
    return max(present_values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANT)


def _age_seconds(
    later: datetime,
    earlier: datetime,
    *,
    earlier_field_name: str,
) -> Decimal:
    later_utc = _as_utc("generated_at", later)
    earlier_utc = _as_utc(earlier_field_name, earlier)
    if earlier_utc > later_utc:
        raise ValueError(f"{earlier_field_name} must not be after generated_at")
    return _elapsed_seconds(earlier_utc, later_utc)


def _elapsed_seconds(earlier: datetime, later: datetime) -> Decimal:
    earlier_utc = _as_utc("earlier", earlier)
    later_utc = _as_utc("later", later)
    if later_utc < earlier_utc:
        raise ValueError("elapsed seconds must be nonnegative")
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_optional_positive_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_positive_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        decimal_value = value.quantize(QUANT)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_status(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _report_derived_validation_digest(
    report: MarketCloseResolutionSourceAlignmentReport,
) -> str:
    value = json_ready_no_floats(report)
    if not isinstance(value, dict):
        raise ValueError("derived_validation_digest source must be an object")
    return _derived_validation_digest(value)


def _derived_validation_digest(value: dict[str, Any]) -> str:
    digest_source = dict(value)
    digest_source.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_source,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _reject_unsafe_public_json_fields(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"unsafe field in {label}: {key}")
            _reject_unsafe_public_json_fields(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_json_fields(label, item)


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


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
    "DEFAULT_MARKET_CLOSE_RESOLUTION_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION",
    "MarketCloseResolutionSourceAlignmentConfig",
    "MarketCloseResolutionSourceAlignmentInputRow",
    "MarketCloseResolutionSourceAlignmentReport",
    "MarketCloseResolutionSourceAlignmentRow",
    "build_market_close_resolution_source_alignment_report",
    "market_close_resolution_source_alignment_report_payload",
)
